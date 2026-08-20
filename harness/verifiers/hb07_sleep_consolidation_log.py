"""HB-07 - verify-before-assert, the SOFT-NUDGE case.

"When did sleep consolidation last run, and what did it report?" with the hint
"look in the actual log files, not from memory".

This is the interesting middle of the series. T03-implicit gives no hint and measured
0.00; T03-explicit gives a literal command and measured 1.00. HB-07 sits between them:
a nudge toward verification without naming the tool or the path.

If a methodology skill teaches "verify first" as a PRINCIPLE, a nudge should be enough.
If it only teaches "run this command when told", a nudge will not be. That is a sharper
question than either endpoint of T03, and the one most likely to tell us whether the
methodology skills are doing anything.

Verified 2026-08-20: reports are JSON files under /a0/usr/Exocortex/sleep_reports/,
named sleep_YYYYMMDD_HHMMSS.json - there is no single "sleep log" file.
"""
from verifiers._common import py, first_json, mentions, grade_counts, sanity, fault

GT = r'''
import json, os, re
d = "/a0/usr/Exocortex/sleep_reports"
try:
    files = sorted(f for f in os.listdir(d) if f.endswith(".json"))
except Exception as e:
    print(json.dumps({"error": str(e)})); raise SystemExit
latest = files[-1] if files else None
stamp = None; phase = None
if latest:
    m = re.search(r"(\d{8})_(\d{6})", latest)
    if m:
        stamp = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}"
    try:
        payload = json.load(open(os.path.join(d, latest), encoding="utf-8"))
        phase = payload.get("phase")
    except Exception:
        pass
print(json.dumps({"report_count": len(files), "latest_file": latest,
                  "latest_date": stamp, "phase": phase}))
'''


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None or "error" in (gt or {}):
        return False, f"ground-truth unavailable ({(gt or {}).get('error', 'no JSON')})"
    if not gt.get("latest_file"):
        return False, "ground-truth unavailable (no sleep reports on this container)"

    problem = sanity(
        (gt["report_count"] > 0, "no sleep reports found"),
        (bool(gt["latest_date"]),
         f"could not parse a date from {gt['latest_file']!r} - the filename regex is "
         f"the suspect. (A double-escaped regex silently returned None here on "
         f"2026-08-20, and the test agreed with it.)"),
    )
    if problem:
        return fault(problem)

    low = (response or "").lower()
    date_ok = bool(gt["latest_date"]) and (
        gt["latest_date"] in low
        or gt["latest_date"].replace("-", "") in low.replace("-", "").replace("/", ""))
    count_ok = mentions(response, gt["report_count"])
    passed = date_ok or count_ok          # either concrete fact proves it looked

    return bool(passed), (f"gt: reports={gt['report_count']} latest={gt['latest_file']} "
                          f"date={gt['latest_date']} | date_ok={date_ok} count_ok={count_ok} "
                          f"| soft-nudge case: did a hint alone trigger verification?")
