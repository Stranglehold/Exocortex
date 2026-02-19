"""
Memory Utilization Evaluation Module
======================================
Measures whether the model uses injected memories correctly:
reference rate, accuracy, noise discrimination, staleness sensitivity.
"""

from base_eval import BaseEval


class MemoryEval(BaseEval):
    FIXTURE_FILE = "memory_tests.json"

    def run(self) -> tuple[dict, int]:
        fixtures = self.load_fixtures()
        tests = fixtures["tests"]

        reference_scores = []
        accuracy_scores = []
        noise_scores = []
        staleness_scores = []

        for test in tests:
            tid = test["test_id"]
            category = test["category"]
            self._log(f"[{tid}] {category}")

            # Build memory context
            memory_block = "\n".join(test["recalled_memories"])
            user_msg = test["user_message"]

            run_results = []
            for _ in range(self.runs_per_test):
                resp = self.call_model([
                    {"role": "system", "content": (
                        "You are an AI assistant. The following memories "
                        "were recalled from previous interactions and may "
                        "be relevant to the current task.\n\n"
                        f"# Recalled Memories\n{memory_block}"
                    )},
                    {"role": "user", "content": user_msg},
                ])
                scores = self._score_memory_usage(resp, test)
                run_results.append(scores)

            # Aggregate per-run scores
            best = self._aggregate_runs(run_results)

            reference_scores.append(best["reference"])
            accuracy_scores.append(best["accuracy"])

            if category == "mixed_relevance":
                noise_scores.append(best["discrimination"])
            if category == "staleness":
                staleness_scores.append(best["staleness"])

            self._log(f"  ref={best['reference']:.2f} acc={best['accuracy']:.2f}")

        # ── Aggregate ──────────────────────────────────────────────────
        ref_rate = sum(reference_scores) / len(reference_scores) if reference_scores else 0
        acc_rate = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
        noise_disc = sum(noise_scores) / len(noise_scores) if noise_scores else 0.5
        stale_sens = sum(staleness_scores) / len(staleness_scores) if staleness_scores else 0.5

        # Derive configuration
        optimal_count = self._calc_optimal_count(ref_rate, noise_disc)
        max_injected = min(10, optimal_count + 3)

        metrics = {
            "memory_reference_rate": round(ref_rate, 3),
            "memory_accuracy_rate": round(acc_rate, 3),
            "memory_noise_discrimination": round(noise_disc, 3),
            "memory_staleness_sensitivity": round(stale_sens, 3),
            "memory_optimal_injection_count": optimal_count,
            "memory_max_injected": max_injected,
        }

        return metrics, self._api_calls

    # ── Scoring ────────────────────────────────────────────────────────

    def _score_memory_usage(self, response: str, test: dict) -> dict:
        """Score how the model used recalled memories."""
        expected_refs = test.get("expected_references", [])
        failure_indicators = test.get("failure_indicators", [])
        noise_memories = test.get("noise_memories", [])
        category = test["category"]

        resp_lower = response.lower()

        # Reference rate: did it use any expected references?
        ref_matches = sum(1 for r in expected_refs if r.lower() in resp_lower)
        reference = ref_matches / len(expected_refs) if expected_refs else 0

        # Accuracy: no failure indicators present
        has_failure = self.check_contains_any(response, failure_indicators)
        accuracy = 0.0 if has_failure else 1.0
        if has_failure and reference > 0.5:
            accuracy = 0.5  # Partial: referenced memories but also has failures

        # Noise discrimination (mixed_relevance tests)
        discrimination = 0.5
        if noise_memories:
            used_noise = sum(1 for n in noise_memories if n.lower() in resp_lower)
            if used_noise == 0 and reference > 0:
                discrimination = 1.0  # Perfect: used relevant, ignored noise
            elif used_noise == 0:
                discrimination = 0.5  # Ignored everything
            else:
                discrimination = max(0, 1.0 - (used_noise / len(noise_memories)))

        # Staleness sensitivity (staleness tests)
        staleness = 0.5
        if category == "staleness":
            stale_idx = test.get("stale_memory_index", 0)
            stale_mem = test["recalled_memories"][stale_idx]
            # Extract key terms from stale memory
            stale_keywords = self._extract_stale_keywords(stale_mem, test)
            used_stale = self.check_contains_any(response, stale_keywords)

            if not used_stale and reference > 0.5:
                staleness = 1.0  # Correctly ignored stale memory
            elif used_stale:
                # Check if it caveated the stale info
                caveat_words = ["previously", "was", "used to", "migrated",
                                "outdated", "old", "deprecated", "changed"]
                if self.check_contains_any(response, caveat_words):
                    staleness = 0.7  # Used but caveated
                else:
                    staleness = 0.0  # Used uncritically

        return {
            "reference": reference,
            "accuracy": accuracy,
            "discrimination": discrimination,
            "staleness": staleness,
        }

    def _extract_stale_keywords(self, stale_memory: str, test: dict) -> list[str]:
        """Extract technology keywords from stale memory for matching."""
        # Get the newer memories to find what replaced the stale tech
        expected = test.get("expected_references", [])

        # Common stale tech markers
        if "MySQL" in stale_memory:
            return ["MySQL", "mysql"]
        if "Angular" in stale_memory:
            return ["Angular", "angular", "ng-"]
        if "SCSS" in stale_memory:
            return ["SCSS", "scss", ".scss"]
        if "raw SQL" in stale_memory:
            return ["raw SQL", "raw query", "cursor.execute"]

        return []

    def _aggregate_runs(self, runs: list[dict]) -> dict:
        """Average scores across multiple runs."""
        if not runs:
            return {"reference": 0, "accuracy": 0,
                    "discrimination": 0.5, "staleness": 0.5}

        keys = runs[0].keys()
        result = {}
        for k in keys:
            vals = [r[k] for r in runs]
            result[k] = sum(vals) / len(vals)
        return result

    def _calc_optimal_count(self, ref_rate: float, noise_disc: float) -> int:
        """Calculate optimal memory injection count."""
        if noise_disc > 0.70 and ref_rate > 0.70:
            return 8   # Good at using and filtering — inject more
        if noise_disc > 0.50 and ref_rate > 0.50:
            return 6   # Moderate
        if ref_rate < 0.30:
            return 3   # Barely uses memories — reduce noise
        return 5       # Default conservative
