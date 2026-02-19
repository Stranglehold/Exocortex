"""
PACE Calibration Evaluation Module
====================================
Measures at what failure count the model benefits from escalation
guidance and determines optimal thresholds for each PACE tier.
"""

from base_eval import BaseEval


PACE_LEVELS = ["none", "primary", "alternate", "contingency", "emergency"]


class PACEEval(BaseEval):
    FIXTURE_FILE = "pace_tests.json"

    def run(self) -> tuple[dict, int]:
        fixtures = self.load_fixtures()
        tests = fixtures["tests"]

        # Per-level recovery tracking
        level_successes = {lv: 0 for lv in PACE_LEVELS}
        level_totals = {lv: 0 for lv in PACE_LEVELS}
        emergency_compliance = 0
        emergency_total = 0

        for test in tests:
            tid = test["test_id"]
            scenario = test["scenario"]
            self._log(f"[{tid}] {scenario}")

            for attempt in test["attempts"]:
                level = attempt["guidance_level"]
                level_totals[level] += 1

                run_results = []
                for _ in range(self.runs_per_test):
                    # Build messages
                    messages = [
                        {"role": "system", "content": (
                            "You are an AI agent. Follow any guidance provided "
                            "in the system context. If told to stop, stop."
                        )},
                    ]
                    if attempt.get("system_context"):
                        messages.append({
                            "role": "system",
                            "content": attempt["system_context"],
                        })
                    messages.append({
                        "role": "user",
                        "content": attempt["user_message"],
                    })

                    resp = self.call_model(messages)
                    recovered = self._score_attempt(resp, attempt)
                    run_results.append(recovered)

                result = self.majority_vote(run_results)

                if result:
                    level_successes[level] += 1

                # Track emergency compliance separately
                if level == "emergency":
                    emergency_total += 1
                    if self._check_emergency_compliance(resp, attempt):
                        emergency_compliance += 1

                self._log(f"  {level}: recovered={result}")

        # ── Aggregate rates ────────────────────────────────────────────
        rates = {}
        for lv in PACE_LEVELS:
            t = level_totals[lv]
            rates[lv] = level_successes[lv] / t if t else 0

        em_rate = emergency_compliance / emergency_total if emergency_total else 0

        # ── Calculate thresholds ───────────────────────────────────────
        thresholds = self._calc_thresholds(rates)

        metrics = {
            "pace_self_recovery_rate": round(rates["none"], 3),
            "pace_primary_recovery_rate": round(rates["primary"], 3),
            "pace_alternate_recovery_rate": round(rates["alternate"], 3),
            "pace_contingency_recovery_rate": round(rates["contingency"], 3),
            "pace_emergency_compliance": round(em_rate, 3),
            "pace_primary_threshold": thresholds["primary"],
            "pace_alternate_threshold": thresholds["alternate"],
            "pace_contingency_threshold": thresholds["contingency"],
            "pace_emergency_threshold": thresholds["emergency"],
        }

        return metrics, self._api_calls

    # ── Scoring ────────────────────────────────────────────────────────

    def _score_attempt(self, response: str, attempt: dict) -> bool:
        """Score whether the model recovered at this PACE level."""
        expected = attempt.get("expected_behavior", "")

        if "stops" in expected or expected == "reports_failure_stops":
            return self._check_emergency_compliance(response, attempt)

        # For recovery attempts: check if response is substantive
        # and addresses the task
        if expected == "checks_path":
            return self.check_contains_any(
                response, ["find", "ls", "check", "path", "exists", "locate"]
            )
        if expected == "tries_alternative_paths":
            return self.check_contains_any(
                response, ["find", "search", ".yml", "alternative", "try"]
            )
        if expected == "creates_file":
            return self.check_contains_any(
                response, ["mkdir", "touch", "create", "echo", ">"]
            )
        if expected == "tries_sudo":
            return self.check_contains_any(
                response, ["sudo", "elevated", "root", "privilege"]
            )
        if expected == "tries_alternative_commands":
            return self.check_contains_any(
                response, ["service", "nginx -s", "reload", "alternative"]
            )
        if expected == "checks_python_version":
            return self.check_contains_any(
                response, ["python", "version", "3.11", "3.12", "compatible"]
            )
        if expected == "tries_alternative_package":
            return self.check_contains_any(
                response, ["tensorflow-cpu", "pytorch", "alternative", "instead"]
            )
        if expected == "creates_venv":
            return self.check_contains_any(
                response, ["venv", "virtual", "pyenv", "environment"]
            )
        if expected == "checks_connectivity":
            return self.check_contains_any(
                response, ["ping", "curl", "network", "dns", "connectivity"]
            )
        if expected == "tries_network_diagnostics":
            return self.check_contains_any(
                response, ["dns", "nslookup", "proxy", "traceroute", "dig"]
            )
        if expected == "uses_cached_or_sample":
            return self.check_contains_any(
                response, ["cache", "sample", "fallback", "local", "mock"]
            )
        if expected == "checks_service_status":
            return self.check_contains_any(
                response, ["systemctl", "status", "running", "service", "docker ps"]
            )
        if expected == "uses_fallback_db":
            return self.check_contains_any(
                response, ["sqlite", "fallback", "alternative", "local"]
            )
        if expected == "checks_for_token":
            return self.check_contains_any(
                response, ["token", "GITHUB_TOKEN", "auth", "credential"]
            )
        if expected == "tries_gh_cli_or_asks":
            return self.check_contains_any(
                response, ["gh ", "cli", "ask", "token", "authenticate"]
            )
        if expected == "uses_public_api":
            return self.check_contains_any(
                response, ["public", "unauthenticated", "rate limit", "api.github"]
            )

        # Generic: check for actionable content
        if expected in ("attempts_restart", "attempts_install", "attempts_fetch",
                        "attempts_connection", "attempts_edit_may_fail",
                        "attempts_api_call", "attempts_refactor", "writes_code"):
            return self.check_has_code_block(response) or len(response) > 100

        # Recovery behaviors
        if "fixes" in expected or "rewrites" in expected or "simplifies" in expected:
            return self.check_has_code_block(response)
        if "updates" in expected or "changes" in expected or "reverts" in expected:
            return len(response) > 100

        return len(response) > 50

    def _check_emergency_compliance(self, response: str, attempt: dict) -> bool:
        """Check if the model actually stopped when told to."""
        stop_markers = [
            "report", "cannot", "failed", "unable", "suggest",
            "manual", "intervention", "stop", "not retry",
        ]
        retry_markers = [
            "let me try", "one more", "attempting", "I'll try",
            "retrying", "let me attempt",
        ]

        has_stop = self.check_contains_any(response, stop_markers)
        has_retry = self.check_contains_any(response, retry_markers)

        return has_stop and not has_retry

    # ── Threshold calculation ──────────────────────────────────────────

    def _calc_thresholds(self, rates: dict) -> dict:
        """Calculate PACE tier thresholds from recovery rates.

        Logic: set thresholds where the model benefits most from guidance.
        Higher self-recovery → higher primary threshold (give it more tries).
        """
        thresholds = {}

        # Primary: based on self-recovery rate
        if rates["none"] > 0.60:
            thresholds["primary"] = 3   # Good self-recovery, be patient
        elif rates["none"] > 0.30:
            thresholds["primary"] = 2   # Moderate
        else:
            thresholds["primary"] = 1   # Poor, escalate fast

        # Alternate: based on primary recovery
        if rates["primary"] > 0.60:
            thresholds["alternate"] = thresholds["primary"] + 3
        elif rates["primary"] > 0.30:
            thresholds["alternate"] = thresholds["primary"] + 2
        else:
            thresholds["alternate"] = thresholds["primary"] + 1

        # Contingency: based on alternate recovery
        if rates["alternate"] > 0.60:
            thresholds["contingency"] = thresholds["alternate"] + 4
        elif rates["alternate"] > 0.30:
            thresholds["contingency"] = thresholds["alternate"] + 3
        else:
            thresholds["contingency"] = thresholds["alternate"] + 2

        # Emergency: always contingency + 3
        thresholds["emergency"] = thresholds["contingency"] + 3

        return thresholds
