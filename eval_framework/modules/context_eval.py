"""
Context Sensitivity Evaluation Module
=======================================
Measures how much injected context the model can handle before
quality degrades, and determines optimal injection budget.
"""

import ast

from base_eval import BaseEval


class ContextEval(BaseEval):
    FIXTURE_FILE = "context_tests.json"

    def run(self) -> tuple[dict, int]:
        fixtures = self.load_fixtures()
        tests = fixtures["tests"]

        all_scores = []  # List of per-test layer-score dicts

        for test in tests:
            tid = test["test_id"]
            base_task = test["base_task"]
            metric_type = test["quality_metric"]
            expected = test.get("expected_output_contains", [])
            layers = test["context_layers"]
            self._log(f"[{tid}] {metric_type}")

            # ── Baseline: no context ───────────────────────────────────
            baseline_scores = []
            for _ in range(self.runs_per_test):
                resp = self.call_model([
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": base_task},
                ])
                score = self._score_response(resp, metric_type, expected)
                baseline_scores.append(score)
            baseline = self.majority_vote(baseline_scores)

            # ── Progressive context addition ───────────────────────────
            layer_scores = {"baseline": baseline}
            cumulative_context = ""
            cumulative_tokens = 0

            for layer in layers:
                cumulative_context += "\n\n" + layer["content"]
                cumulative_tokens += layer["approx_tokens"]

                run_scores = []
                for _ in range(self.runs_per_test):
                    resp = self.call_model([
                        {"role": "system", "content": cumulative_context},
                        {"role": "user", "content": base_task},
                    ])
                    score = self._score_response(resp, metric_type, expected)
                    run_scores.append(score)

                layer_score = self.majority_vote(run_scores)
                layer_scores[layer["name"]] = layer_score
                layer_scores[f"{layer['name']}_tokens"] = cumulative_tokens

                self._log(f"  +{layer['name']} ({cumulative_tokens}t): "
                          f"{layer_score:.2f}")

            all_scores.append(layer_scores)

        # ── Aggregate across all tests ─────────────────────────────────
        metrics = self._aggregate(all_scores, tests)
        return metrics, self._api_calls

    # ── Scoring ────────────────────────────────────────────────────────

    def _score_response(
        self, response: str, metric_type: str, expected: list[str]
    ) -> float:
        """Score response quality based on metric type."""
        if metric_type == "code_correctness":
            return self._score_code(response, expected)
        if metric_type == "explanation_quality":
            return self._score_explanation(response, expected)
        return self._score_generic(response, expected)

    def _score_code(self, response: str, expected: list[str]) -> float:
        """Score code response: syntax validity + expected content."""
        score = 0.0

        # Extract code block
        code = self._extract_code(response)
        if not code:
            # No code block — check inline
            if self.check_contains_any(response, expected):
                return 0.3
            return 0.0

        # Syntax check
        if self.try_parse_python(code):
            score += 0.4
        else:
            score += 0.1

        # Content check
        if expected:
            matches = sum(1 for kw in expected
                         if kw.lower() in response.lower())
            score += 0.6 * (matches / len(expected))

        return min(1.0, score)

    def _score_explanation(self, response: str, expected: list[str]) -> float:
        """Score explanation quality: covers expected concepts."""
        if not expected:
            return 0.5 if len(response) > 100 else 0.2

        matches = sum(1 for kw in expected if kw.lower() in response.lower())
        coverage = matches / len(expected)

        # Length bonus — substantive explanations
        length_bonus = min(0.2, len(response) / 2000)

        return min(1.0, coverage * 0.8 + length_bonus)

    def _score_generic(self, response: str, expected: list[str]) -> float:
        """Generic scoring: expected content + response quality."""
        if not expected:
            return 0.5

        matches = sum(1 for kw in expected if kw.lower() in response.lower())
        return matches / len(expected)

    def _extract_code(self, response: str) -> str:
        """Extract code from markdown code block."""
        if "```" not in response:
            return ""
        blocks = response.split("```")
        for i in range(1, len(blocks), 2):
            block = blocks[i]
            # Strip language tag
            lines = block.split("\n", 1)
            if len(lines) > 1:
                return lines[1].strip()
            return block.strip()
        return ""

    # ── Aggregation ────────────────────────────────────────────────────

    def _aggregate(self, all_scores: list[dict], tests: list) -> dict:
        """Aggregate per-test scores into module metrics."""
        layer_names = ["bst_enrichment", "recalled_memories", "graph_node",
                       "role_profile", "personality", "padding_noise"]

        # Average baseline
        baselines = [s["baseline"] for s in all_scores]
        avg_baseline = sum(baselines) / len(baselines) if baselines else 0

        # Find optimal injection point and degradation threshold
        peak_layer = None
        peak_score = avg_baseline
        degrade_tokens = None

        for layer_name in layer_names:
            scores = [s.get(layer_name, 0) for s in all_scores]
            tokens = [s.get(f"{layer_name}_tokens", 0) for s in all_scores]
            if not scores:
                continue

            avg_score = sum(scores) / len(scores)
            avg_tokens = sum(tokens) / len(tokens) if tokens else 0

            if avg_score > peak_score:
                peak_score = avg_score
                peak_layer = layer_name

            if avg_score < avg_baseline - 0.05 and degrade_tokens is None:
                degrade_tokens = int(avg_tokens)

        # Optimal injection tokens: tokens at peak layer
        optimal_tokens = 0
        if peak_layer:
            idx = layer_names.index(peak_layer) if peak_layer in layer_names else -1
            if idx >= 0:
                tokens_at_peak = [
                    s.get(f"{peak_layer}_tokens", 0)
                    for s in all_scores
                ]
                optimal_tokens = int(sum(tokens_at_peak) / len(tokens_at_peak)) if tokens_at_peak else 0

        if degrade_tokens is None:
            degrade_tokens = 4000  # No degradation observed

        # Layer priority: rank by improvement over previous layer
        layer_improvements = {}
        for i, ln in enumerate(layer_names):
            scores = [s.get(ln, 0) for s in all_scores]
            if not scores:
                continue
            avg = sum(scores) / len(scores)
            prev_name = layer_names[i - 1] if i > 0 else "baseline"
            prev_scores = [s.get(prev_name, s.get("baseline", 0)) for s in all_scores]
            prev_avg = sum(prev_scores) / len(prev_scores) if prev_scores else 0
            layer_improvements[ln] = avg - prev_avg

        priority = sorted(layer_improvements, key=layer_improvements.get, reverse=True)

        # Instruction compliance at 2k and 4k tokens
        compliance_2k = self._calc_compliance_at_tokens(all_scores, layer_names, 2000)
        compliance_4k = self._calc_compliance_at_tokens(all_scores, layer_names, 4000)

        # Max context injection
        max_injection = min(degrade_tokens, optimal_tokens + 1000) if optimal_tokens else 2000

        # Memory max injected based on context budget
        mem_max = max(3, min(10, max_injection // 300))

        metrics = {
            "context_baseline_quality": round(avg_baseline, 3),
            "context_optimal_injection_tokens": optimal_tokens,
            "context_degradation_threshold_tokens": degrade_tokens,
            "context_layer_priority": priority,
            "context_instruction_compliance_at_2k": round(compliance_2k, 3),
            "context_instruction_compliance_at_4k": round(compliance_4k, 3),
            "max_context_injection_tokens": max_injection,
            "memory_max_injected": mem_max,
        }

        return metrics

    def _calc_compliance_at_tokens(
        self, all_scores: list, layer_names: list, token_threshold: int
    ) -> float:
        """Calculate average score at approximately token_threshold tokens."""
        scores = []
        for test_scores in all_scores:
            # Find the layer closest to the token threshold
            for ln in layer_names:
                tokens = test_scores.get(f"{ln}_tokens", 0)
                if tokens >= token_threshold:
                    scores.append(test_scores.get(ln, 0))
                    break
        return sum(scores) / len(scores) if scores else 0
