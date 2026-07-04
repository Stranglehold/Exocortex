"""
TLA+ Model Checker Tool
=======================
Allows the agent to write a TLA+ specification and run TLC to check
invariants and liveness properties before building.

Workflow:
    1. Write a .tla spec and optional .cfg model config
    2. Call this tool with the spec content
    3. TLC checks all reachable states against your invariants
    4. If invariant violations or deadlocks are found, TLC returns the
       exact execution trace — fix the spec and re-run

Tool arguments:
    spec        (required) — TLA+ spec content (full module text)
    cfg         (optional) — Model config content. Defaults to checking
                             the Spec specification with no invariants.
    module_name (optional) — Module name to use. Default: "spec"
    deadlock    (optional) — "false" to suppress deadlock checking. Default: "true"

Returns structured output:
    - result: "ok" | "invariant_violated" | "deadlock" | "parse_error" | "error"
    - states_checked: integer
    - trace: execution trace on violation (list of state strings)
    - raw_output: full TLC output for debugging

Example spec (Loop Feedback Cascade tier invariant):
    ---- MODULE loop_tiers ----
    EXTENDS Naturals
    VARIABLES tier
    Tiers == {"none", "warn", "summarize", "reset"}
    TypeOK == tier \\in Tiers
    Init == tier = "none"
    Next == \\/ (tier = "none" /\\ tier' = "warn")
            \\/ (tier = "warn" /\\ tier' = "summarize")
            \\/ (tier = "summarize" /\\ tier' = "reset")
    TierMonotone == tier /= "reset" => tier' /= "none"
    Spec == Init /\\ [][Next]_tier
    ====

Example cfg:
    SPECIFICATION Spec
    INVARIANT TypeOK TierMonotone
"""

import json
import os
import re
import subprocess
import tempfile
from typing import Any

from helpers.tool import Tool, Response

TLC_JAR = "/usr/local/bin/tla2tools.jar"


class TlaCheck(Tool):
    """Run TLC model checker on a TLA+ specification."""

    async def execute(self, **kwargs) -> Response:
        spec_content = kwargs.get("spec", "").strip()
        cfg_content = kwargs.get("cfg", "").strip()
        module_name = kwargs.get("module_name", "spec").strip()
        check_deadlock = kwargs.get("deadlock", "true").lower() != "false"

        if not spec_content:
            return Response(
                message=json.dumps({"result": "error", "message": "spec argument is required"}),
                break_loop=False,
            )

        if not os.path.exists(TLC_JAR):
            return Response(
                message=json.dumps({"result": "error", "message": f"TLC not found at {TLC_JAR}. Install with: apt-get install default-jre-headless && curl -L -o {TLC_JAR} https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar"}),
                break_loop=False,
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tla_path = os.path.join(tmpdir, f"{module_name}.tla")
            cfg_path = os.path.join(tmpdir, f"{module_name}.cfg")

            with open(tla_path, "w") as f:
                f.write(spec_content)

            # Default config if none provided: just check the Spec
            if not cfg_content:
                cfg_content = "SPECIFICATION Spec\n"
            with open(cfg_path, "w") as f:
                f.write(cfg_content)

            cmd = [
                "java", "-XX:+UseParallelGC",
                "-jar", TLC_JAR,
                "-config", cfg_path,
                "-nowarning",
            ]
            if not check_deadlock:
                cmd.append("-deadlock")
            cmd.append(tla_path)

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=tmpdir,
                )
                output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                return Response(
                    message=json.dumps({"result": "error", "message": "TLC timed out after 60 seconds (state space too large)"}),
                    break_loop=False,
                )

        return Response(
            message=_parse_tlc_output(output),
            break_loop=False,
        )


# ── Output Parser ─────────────────────────────────────────────────────────────

def _parse_tlc_output(output: str) -> str:
    """Parse TLC output into structured result dict."""
    result = {
        "result": "ok",
        "states_checked": 0,
        "message": "",
        "trace": [],
        "raw_output": output,
    }

    # Extract states generated
    m = re.search(r"(\d+) states generated", output)
    if m:
        result["states_checked"] = int(m.group(1))

    # Detect outcomes
    if "Parsing or semantic analysis failed" in output or "Errors:" in output:
        result["result"] = "parse_error"
        # Extract error lines
        errors = re.findall(r"^.*[Ee]rror.*$", output, re.MULTILINE)
        result["message"] = "\n".join(errors[:10])

    elif "Invariant" in output and "violated" in output:
        result["result"] = "invariant_violated"
        # Extract the invariant name
        m = re.search(r"Invariant (\S+) is violated", output)
        if m:
            result["message"] = f"Invariant {m.group(1)} is violated"
        result["trace"] = _extract_trace(output)

    elif "Deadlock reached" in output:
        result["result"] = "deadlock"
        result["message"] = "Deadlock: no valid next state from current state"
        result["trace"] = _extract_trace(output)

    elif "Error" in output and result["result"] == "ok":
        result["result"] = "error"
        result["message"] = output[:500]

    else:
        result["message"] = f"No errors detected. {result['states_checked']} states checked."

    return json.dumps(result, indent=2)


def _extract_trace(output: str) -> list:
    """Extract execution trace from TLC violation output."""
    lines = output.split("\n")
    trace = []
    in_trace = False
    for line in lines:
        if "The behavior up to this point" in line or "State " in line:
            in_trace = True
        if in_trace and line.strip():
            trace.append(line)
        if len(trace) > 50:  # cap trace length
            trace.append("... (trace truncated)")
            break
    return trace
