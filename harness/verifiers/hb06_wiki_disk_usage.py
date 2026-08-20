"""HB-06 - accurate reporting, generalises from T01.

"Wiki disk usage, directory count, file count."

Three numbers that cannot be estimated. The agent has to run du and find. Disk usage is
graded with tolerance because du reports in blocks and can shift between calls; the
counts are graded exactly.
"""
from verifiers._common import py, first_json, mentions, grade_counts, sanity, fault

GT = r'''
import json, os
root = "/a0/usr/workdir/workspace/wiki"
files = dirs = 0; size = 0
for dp, dn, fn in os.walk(root):
    dirs += len(dn); files += len(fn)
    for f in fn:
        try:
            size += os.path.getsize(os.path.join(dp, f))
        except OSError:
            pass
print(json.dumps({"files": files, "dirs": dirs, "bytes": size, "kb": round(size/1024),
                  "mb": round(size/1048576, 1)}))
'''


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (wiki walk produced no JSON)"

    problem = sanity(
        (gt["files"] > 0, "0 files under the wiki dir - path is wrong or wiki is empty"),
        (gt["bytes"] > 0, "wiki reports 0 bytes with files present"),
    )
    if problem:
        return fault(problem)

    ok, detail = grade_counts(response, [("files", gt["files"]), ("dirs", gt["dirs"])])
    # Size in any plausible unit, generous tolerance - du blocks vs bytes.
    size_ok = (mentions(response, gt["kb"], tol=max(8, gt["kb"] // 10))
               or mentions(response, int(gt["mb"]), tol=1)
               or mentions(response, gt["bytes"], tol=gt["bytes"] // 10))
    return bool(ok and size_ok), (f"gt: files={gt['files']} dirs={gt['dirs']} "
                                  f"kb={gt['kb']} mb={gt['mb']} | {detail} | size_ok={size_ok}")
