"""
Graph Workflow Compliance Evaluation Module
============================================
Measures whether the model follows graph workflow instructions:
instruction adherence, premature completion, retry effectiveness,
and escalation recognition.
"""

from base_eval import BaseEval


class GraphEval(BaseEval):
    FIXTURE_FILE = "graph_tests.json"

    def run(self) -> tuple[dict, int]:
        fixtures = self.load_fixtures()
        tests = fixtures["tests"]

        adherence_scores = []
        premature_count = 0
        retry_tests = []
        escalation_tests = []
        total = 0

        for test in tests:
            tid = test["test_id"]
            is_retry = test.get("is_retry", False)
            node_type = test["node_type"]
            self._log(f"[{tid}] node={node_type} retry={is_retry}")

            run_scores = []
            for _ in range(self.runs_per_test):
                system_msg = (
                    "You are an AI agent executing a structured workflow. "
                    "Follow the workflow node instructions exactly. "
                    "Stay within the scope of the current node."
                )
                user_msg = f"{test['node_instruction']}\n\n{test['user_context']}"

                resp = self.call_model([
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ])
                score = self._score_adherence(resp, test)
                run_scores.append(score)

            final_score = self.majority_vote(run_scores)
            adherence_scores.append(final_score)
            total += 1

            # Check premature completion
            if final_score < 0.5 and not is_retry:
                if self._is_premature(resp, test):
                    premature_count += 1

            # Track retry effectiveness
            if is_retry:
                retry_tests.append(final_score)

            # Track escalation recognition
            if test["expected_behavior"] in ("signals_blocker", "signals_limitation"):
                escalation_tests.append(final_score)

            self._log(f"  adherence={final_score:.2f}")

        # ── Retry effectiveness test ───────────────────────────────────
        retry_pairs = [t for t in tests if t.get("is_retry")]
        retry_effectiveness_scores = []

        for rtest in retry_pairs:
            original_id = rtest["test_id"].replace("_retry", "")
            # Run the retry scenario — check if approach changes
            run_changes = []
            for _ in range(self.runs_per_test):
                system_msg = (
                    "You are an AI agent executing a structured workflow. "
                    "This is a RETRY — your previous attempt failed. "
                    "You MUST try a different approach."
                )
                user_msg = f"{rtest['node_instruction']}\n\n{rtest['user_context']}"
                resp = self.call_model([
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ])
                changed = self._check_approach_changed(resp, rtest)
                run_changes.append(changed)

            if self.majority_vote(run_changes):
                retry_effectiveness_scores.append(1.0)
            else:
                retry_effectiveness_scores.append(0.0)

        # ── Aggregate ──────────────────────────────────────────────────
        adherence_rate = sum(adherence_scores) / total if total else 0
        premature_rate = premature_count / total if total else 0

        retry_eff = (
            sum(retry_effectiveness_scores) / len(retry_effectiveness_scores)
            if retry_effectiveness_scores else 0.5
        )
        escalation_rate = (
            sum(escalation_tests) / len(escalation_tests)
            if escalation_tests else 0.5
        )

        # Derive configuration values
        max_retries = self._calc_max_retries(adherence_rate)
        stale_turns = self._calc_stale_turns(retry_eff)

        metrics = {
            "graph_instruction_adherence": round(adherence_rate, 3),
            "graph_premature_completion_rate": round(premature_rate, 3),
            "graph_retry_effectiveness": round(retry_eff, 3),
            "graph_escalation_recognition": round(escalation_rate, 3),
            "graph_max_retries_per_node": max_retries,
            "graph_stale_detection_turns": stale_turns,
        }

        return metrics, self._api_calls

    # ── Scoring ────────────────────────────────────────────────────────

    def _score_adherence(self, response: str, test: dict) -> float:
        """Score how well the model adhered to node instructions."""
        failure_indicators = test.get("failure_indicators", [])
        success_indicators = test.get("success_indicators", [])

        has_failure = self.check_contains_any(response, failure_indicators)
        has_success = self.check_contains_any(response, success_indicators) if success_indicators else True

        expected = test["expected_behavior"]

        # Special behavior checks
        if expected in ("signals_blocker", "signals_limitation"):
            blocker_words = ["cannot", "blocked", "unable", "need access",
                             "limitation", "escalate", "no source", "credentials"]
            if self.check_contains_any(response, blocker_words):
                return 1.0 if not has_failure else 0.5
            return 0.0

        if has_failure and not has_success:
            return 0.0
        if has_failure and has_success:
            return 0.5
        if has_success:
            return 1.0
        return 0.25

    def _is_premature(self, response: str, test: dict) -> bool:
        """Check if the model tried to skip ahead in the workflow."""
        premature_markers = [
            "fix", "deploy", "implement", "next step",
            "moving on", "let me also", "additionally",
        ]
        node_type = test["node_type"]

        # If the node is "reproduce" but response tries to fix
        if node_type == "reproduce":
            return self.check_contains_any(
                response, ["fix", "patch", "solution", "here's the fix"]
            )
        # If the node is "verify" but response tries to deploy
        if node_type == "verify":
            return self.check_contains_any(
                response, ["deploy", "push", "release", "ship"]
            )
        return self.check_contains_any(response, premature_markers)

    def _check_approach_changed(self, response: str, test: dict) -> bool:
        """Check if the retry used a different approach."""
        success_indicators = test.get("success_indicators", [])
        if success_indicators:
            return self.check_contains_any(response, success_indicators)
        # Heuristic: does it mention changing approach?
        change_words = ["different", "alternative", "instead", "another way",
                        "new approach", "let me try"]
        return self.check_contains_any(response, change_words)

    def _calc_max_retries(self, adherence: float) -> int:
        """Calculate max retries per node based on adherence."""
        if adherence > 0.80:
            return 3   # High adherence — retries are productive
        if adherence > 0.60:
            return 2   # Medium
        return 1       # Low adherence — retries unlikely to help

    def _calc_stale_turns(self, retry_eff: float) -> int:
        """Calculate stale detection turns based on retry effectiveness."""
        if retry_eff > 0.70:
            return 15  # Model recovers well — longer window
        if retry_eff > 0.40:
            return 10  # Moderate
        return 6       # Poor recovery — detect stale early
