"""
BST Rigidity Evaluation Module — v3 3-Condition Design
=======================================================
Answers: does v3 need instruction-heavy scaffolding or does
information-only enrichment produce equivalent behavior?

Per Opus architectural review 2026-04-17 (BST_V33_STRATEGIC_QUESTIONS.md):
  Condition 1 — Full BST enrichment (instruction-heavy, current production)
  Condition 2 — Information-only BST (context + tool availability, no explicit instructions)
  Condition 3 — Raw (no BST enrichment)

Domains covered: investigation, analysis, philosophical, planning
(the domains missing from the standard bst_tests.json fixtures)

Output:
  per_domain: {domain: {enriched, info_only, raw}} scores
  rigidity_verdict per domain: "instructions_load_bearing" | "info_sufficient" | "both_fail"
  overall: aggregate scores + domains where instructions add value vs noise
"""

from base_eval import BaseEval


class BSTRigidityEval(BaseEval):
    FIXTURE_FILE = "bst_tests_v3_rigidity.json"

    def run(self) -> tuple[dict, int]:
        fixtures = self.load_fixtures()
        tests = fixtures["tests"]

        enriched_results = []
        info_only_results = []
        raw_results = []
        confusion_count = 0
        per_domain = {}

        for test in tests:
            tid = test["test_id"]
            domain = test["domain"]
            has_info_only = "info_only_message" in test
            self._log(f"[{tid}] domain={domain} info_only={'yes' if has_info_only else 'no'}")

            sys_prompt = [{"role": "system", "content": "You are an AI assistant."}]

            # ── Condition 1: Full enrichment (instruction-heavy) ───────
            e_scores = []
            for _ in range(self.runs_per_test):
                resp = self.call_model(sys_prompt + [
                    {"role": "user", "content": test["enriched_message"]},
                ])
                score = self._score(resp, test)
                e_scores.append(score)
                if self._is_confused(resp):
                    confusion_count += 1
            e_score = self.majority_vote(e_scores)
            enriched_results.append(e_score)

            # ── Condition 2: Info-only (no explicit instructions) ─────
            i_score = None
            if has_info_only:
                i_scores = []
                for _ in range(self.runs_per_test):
                    resp = self.call_model(sys_prompt + [
                        {"role": "user", "content": test["info_only_message"]},
                    ])
                    i_scores.append(self._score(resp, test))
                i_score = self.majority_vote(i_scores)
                info_only_results.append(i_score)

            # ── Condition 3: Raw (no enrichment) ─────────────────────
            r_scores = []
            for _ in range(self.runs_per_test):
                resp = self.call_model(sys_prompt + [
                    {"role": "user", "content": test["raw_message"]},
                ])
                r_scores.append(self._score(resp, test))
            r_score = self.majority_vote(r_scores)
            raw_results.append(r_score)

            # ── Track per domain ──────────────────────────────────────
            if domain not in per_domain:
                per_domain[domain] = {"enriched": [], "info_only": [], "raw": []}
            per_domain[domain]["enriched"].append(e_score)
            per_domain[domain]["raw"].append(r_score)
            if i_score is not None:
                per_domain[domain]["info_only"].append(i_score)

            log_parts = [f"enriched={e_score:.2f}", f"raw={r_score:.2f}"]
            if i_score is not None:
                log_parts.insert(1, f"info_only={i_score:.2f}")
            self._log(f"  {' | '.join(log_parts)}")

        # ── Per-domain verdicts ───────────────────────────────────────
        domain_verdicts = {}
        for domain, scores in per_domain.items():
            e_avg = sum(scores["enriched"]) / len(scores["enriched"])
            r_avg = sum(scores["raw"]) / len(scores["raw"])
            i_avg = (sum(scores["info_only"]) / len(scores["info_only"])
                     if scores["info_only"] else None)

            if i_avg is not None:
                # 3-condition verdict
                if i_avg >= e_avg - 0.10:
                    # Info-only within 10% of full enrichment
                    verdict = "info_sufficient"
                elif e_avg > r_avg + 0.15 and e_avg > i_avg + 0.10:
                    # Full enrichment significantly better than both
                    verdict = "instructions_load_bearing"
                elif e_avg <= r_avg + 0.05 and i_avg <= r_avg + 0.05:
                    verdict = "both_fail"
                else:
                    verdict = "instructions_marginal"
            else:
                # 2-condition fallback
                verdict = "instructions_load_bearing" if e_avg > r_avg + 0.15 else "instructions_marginal"

            domain_verdicts[domain] = {
                "verdict": verdict,
                "enriched_avg": round(e_avg, 3),
                "info_only_avg": round(i_avg, 3) if i_avg is not None else None,
                "raw_avg": round(r_avg, 3),
            }

        # ── Aggregate ─────────────────────────────────────────────────
        total = len(tests)
        e_total = len(enriched_results)
        r_total = len(raw_results)
        i_total = len(info_only_results)
        total_calls = total * self.runs_per_test

        enriched_avg = sum(enriched_results) / e_total if e_total else 0
        raw_avg = sum(raw_results) / r_total if r_total else 0
        info_only_avg = sum(info_only_results) / i_total if i_total else 0
        confusion_rate = confusion_count / total_calls if total_calls else 0

        load_bearing_domains = [d for d, v in domain_verdicts.items()
                                if v["verdict"] == "instructions_load_bearing"]
        info_sufficient_domains = [d for d, v in domain_verdicts.items()
                                   if v["verdict"] == "info_sufficient"]
        marginal_domains = [d for d, v in domain_verdicts.items()
                           if "marginal" in v["verdict"]]

        metrics = {
            "bst_rigidity_enriched_avg": round(enriched_avg, 3),
            "bst_rigidity_info_only_avg": round(info_only_avg, 3),
            "bst_rigidity_raw_avg": round(raw_avg, 3),
            "bst_rigidity_confusion_rate": round(confusion_rate, 3),
            "bst_rigidity_per_domain": domain_verdicts,
            "bst_rigidity_load_bearing_domains": load_bearing_domains,
            "bst_rigidity_info_sufficient_domains": info_sufficient_domains,
            "bst_rigidity_marginal_domains": marginal_domains,
            "bst_rigidity_recommendation": self._recommend(
                load_bearing_domains, info_sufficient_domains, enriched_avg, info_only_avg
            ),
        }

        return metrics, self._api_calls

    # ── Scoring ──────────────────────────────────────────────────────────

    def _score(self, response: str, test: dict) -> float:
        """Unified scorer for all three conditions."""
        behavior = test["expected_behavior"]
        success = test.get("success_indicators", [])
        failures = test.get("failure_indicators", [])

        has_failure = self.check_contains_any(response, failures)
        has_success = self.check_contains_any(response, success) if success else len(response) > 80

        # Behavior-specific scoring
        if "asks" in behavior or "requests" in behavior:
            compliant = self.check_is_question(response)
        elif "writes" in behavior or "produces" in behavior:
            compliant = self.check_has_code_block(response)
        elif behavior in ("structured_comparison", "structured_comparison_with_verdict",
                          "provides_structured_analysis"):
            # Needs both structure and content
            has_structure = any(marker in response for marker in ["##", "**", "1.", "- ", "vs"])
            compliant = has_structure and has_success
        elif behavior in ("explains_with_practical_focus", "explains_pep695_technically",
                          "explains_gil_with_alternatives"):
            compliant = has_success
        elif behavior in ("provides_technical_documentation", "uses_search_or_provides_structured_answer"):
            compliant = has_success and len(response) > 150
        elif behavior == "produces_numbered_actionable_plan":
            has_numbers = any(f"{n}." in response for n in range(1, 8))
            compliant = has_numbers and has_success
        elif behavior == "diagnoses_recursion_error":
            compliant = has_success
        else:
            compliant = has_success and not has_failure

        if has_failure and not compliant:
            return 0.0
        if has_failure and compliant:
            return 0.5
        if compliant:
            return 1.0
        return 0.25

    def _is_confused(self, response: str) -> bool:
        """Check if model quoted enrichment format verbatim."""
        markers = ["[TASK CONTEXT]", "[INSTRUCTION]", "[USER MESSAGE]"]
        return sum(1 for m in markers if m in response) >= 2

    def _recommend(self, load_bearing, info_sufficient, e_avg, i_avg) -> str:
        """Generate scaffolding philosophy recommendation."""
        if not load_bearing and not info_sufficient:
            return "insufficient_data"
        if len(info_sufficient) >= len(load_bearing):
            gap = round(e_avg - i_avg, 3)
            return (f"SHIFT_TO_INFO: info-only achieves equivalent results in "
                    f"{len(info_sufficient)} of {len(info_sufficient)+len(load_bearing)} domains "
                    f"(enriched_avg-info_avg={gap}). "
                    f"Instructions load-bearing only in: {load_bearing}.")
        else:
            return (f"RETAIN_INSTRUCTIONS: instructions provide significant lift in "
                    f"{len(load_bearing)} domains: {load_bearing}. "
                    f"Info-sufficient in: {info_sufficient}.")
