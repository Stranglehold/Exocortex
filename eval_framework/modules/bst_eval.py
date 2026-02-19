"""
BST Classification Accuracy Evaluation Module
==============================================
Measures whether the model responds correctly to BST-enriched messages.

Dimensions:
  1. Enrichment compliance rate — follows injected instructions
  2. Enrichment confusion rate — treats enrichment as conversation content
  3. Unenriched baseline comparison
  4. Confidence threshold calibration
"""

from base_eval import BaseEval


class BSTEval(BaseEval):
    FIXTURE_FILE = "bst_tests.json"

    def run(self) -> tuple[dict, int]:
        fixtures = self.load_fixtures()
        tests = fixtures["tests"]

        enriched_results = []
        raw_results = []
        confusion_count = 0
        per_domain = {}

        for test in tests:
            tid = test["test_id"]
            domain = test["domain"]
            self._log(f"[{tid}] domain={domain}")

            # ── Run enriched version ───────────────────────────────────
            enriched_scores = []
            for _ in range(self.runs_per_test):
                resp = self.call_model([
                    {"role": "system", "content": "You are an AI assistant."},
                    {"role": "user", "content": test["enriched_message"]},
                ])
                score = self._score_enriched(resp, test)
                enriched_scores.append(score)

                # Check confusion
                if self._is_confused(resp):
                    confusion_count += 1

            enriched_score = self.majority_vote(enriched_scores)
            enriched_results.append(enriched_score)

            # ── Run raw (unenriched) version ───────────────────────────
            raw_scores = []
            for _ in range(self.runs_per_test):
                resp = self.call_model([
                    {"role": "system", "content": "You are an AI assistant."},
                    {"role": "user", "content": test["raw_message"]},
                ])
                score = self._score_raw(resp, test)
                raw_scores.append(score)

            raw_score = self.majority_vote(raw_scores)
            raw_results.append(raw_score)

            # Track per-domain
            if domain not in per_domain:
                per_domain[domain] = {"enriched": [], "raw": []}
            per_domain[domain]["enriched"].append(enriched_score)
            per_domain[domain]["raw"].append(raw_score)

            self._log(f"  enriched={enriched_score:.2f}  raw={raw_score:.2f}")

        # ── Aggregate metrics ──────────────────────────────────────────
        total = len(tests)
        total_calls = total * self.runs_per_test  # for confusion denominator

        enriched_avg = sum(enriched_results) / total if total else 0
        raw_avg = sum(raw_results) / total if total else 0
        confusion_rate = confusion_count / total_calls if total_calls else 0
        improvement = enriched_avg - raw_avg

        # Find domains where enrichment hurts
        hurt_domains = []
        for domain, scores in per_domain.items():
            e_avg = sum(scores["enriched"]) / len(scores["enriched"])
            r_avg = sum(scores["raw"]) / len(scores["raw"])
            if r_avg > e_avg + 0.05:  # raw beats enriched by >5%
                hurt_domains.append(domain)

        # Confidence threshold calibration
        conf_adj = self._calc_confidence_adjustment(enriched_avg, confusion_rate)
        optimal_threshold = 0.70 + conf_adj

        metrics = {
            "bst_enrichment_compliance_rate": round(enriched_avg, 3),
            "bst_enrichment_confusion_rate": round(confusion_rate, 3),
            "bst_improvement_over_baseline": round(improvement, 3),
            "bst_optimal_confidence_threshold": round(optimal_threshold, 2),
            "bst_domains_where_enrichment_hurts": hurt_domains,
            "bst_confidence_adjustment": round(conf_adj, 2),
        }

        return metrics, self._api_calls

    # ── Scoring ────────────────────────────────────────────────────────

    def _score_enriched(self, response: str, test: dict) -> float:
        """Score how well the model followed the enriched instruction."""
        behavior = test["expected_behavior"]
        failure_indicators = test.get("failure_indicators", [])

        # Check for failures first
        has_failure = self.check_contains_any(response, failure_indicators)

        # Score based on expected behavior
        if behavior == "asks_clarifying_question" or behavior == "asks_clarification":
            compliant = self.check_is_question(response)
        elif behavior == "asks_language_or_writes_code":
            compliant = self.check_is_question(response) or self.check_has_code_block(response)
        elif behavior in ("requests_error_details", "asks_for_symptoms",
                          "asks_which_function", "asks_platform_and_language",
                          "requests_source_code", "requests_config_or_writes_directives",
                          "requests_queries_or_suggests_optimizations",
                          "asks_platform_and_suggests_env"):
            compliant = self.check_is_question(response)
        elif behavior in ("writes_crud_class", "writes_compose_file",
                          "writes_jwt_middleware"):
            compliant = self.check_has_code_block(response)
        elif behavior in ("diagnoses_memory_issue", "diagnoses_undefined_array",
                          "provides_remediation_steps", "explains_undo_options",
                          "suggests_rate_limit_solutions", "outlines_integration_steps"):
            success = test.get("success_indicators", [])
            if success:
                compliant = self.check_contains_any(response, success)
            else:
                compliant = len(response) > 100  # substantive response
        else:
            compliant = not has_failure and len(response) > 50

        if has_failure and not compliant:
            return 0.0
        if has_failure and compliant:
            return 0.5
        if compliant:
            return 1.0
        return 0.25

    def _score_raw(self, response: str, test: dict) -> float:
        """Score the raw (unenriched) response — same criteria, less strict."""
        behavior = test["expected_behavior"]

        if "asks" in behavior or "requests" in behavior:
            return 1.0 if self.check_is_question(response) else 0.5
        if "writes" in behavior:
            return 1.0 if self.check_has_code_block(response) else 0.3
        if "diagnoses" in behavior or "provides" in behavior or "explains" in behavior:
            return 0.8 if len(response) > 100 else 0.3
        return 0.5

    def _is_confused(self, response: str) -> bool:
        """Check if the model quoted or referenced the enrichment format."""
        confusion_markers = [
            "[TASK CONTEXT]",
            "[INSTRUCTION]",
            "[USER MESSAGE]",
            "domain:",
            "confidence:",
        ]
        resp_lower = response.lower()
        # Must match at least 2 markers to count as confused
        matches = sum(1 for m in confusion_markers if m.lower() in resp_lower)
        return matches >= 2

    def _calc_confidence_adjustment(
        self, compliance: float, confusion: float
    ) -> float:
        """Calculate BST confidence threshold adjustment."""
        if compliance > 0.85 and confusion < 0.10:
            return -0.05  # Model handles enrichment well, lower threshold
        if compliance > 0.70 and confusion < 0.15:
            return 0.0    # Acceptable
        if compliance < 0.60 or confusion > 0.20:
            return 0.10   # Model confused, raise threshold
        return 0.05       # Marginal, slight raise
