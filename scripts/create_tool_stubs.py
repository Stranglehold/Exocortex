"""Create individual tool stub files for multi-class tool files in the exocortex plugin."""
import os
import sys

STUBS_DIR = "/a0/usr/agents/agent0/tools"
PLUGIN_TOOLS = "/a0/usr/plugins/exocortex/tools"

os.makedirs(STUBS_DIR, exist_ok=True)

stubs = {
    # oss.py tools
    "oss_topic.py":         ("oss.py", "OssTopic"),
    "oss_drift.py":         ("oss.py", "OssDrift"),
    "oss_dynamics.py":      ("oss.py", "OssDynamics"),
    "oss_hypotheses.py":    ("oss.py", "OssHypotheses"),
    "oss_health.py":        ("oss.py", "OssHealth"),
    "oss_submit.py":        ("oss.py", "OssSubmit"),
    "oss_list_topics.py":   ("oss.py", "OssListTopics"),
    "oss_add_topic.py":     ("oss.py", "OssAddTopic"),
    "oss_ingest_pause.py":  ("oss.py", "OssIngestPause"),
    "oss_ingest_resume.py": ("oss.py", "OssIngestResume"),
    "oss_question.py":      ("oss.py", "OssQuestion"),
    "oss_synthesize.py":    ("oss.py", "OssSynthesize"),
    "oss_ingest_sprint.py": ("oss.py", "OssIngestSprint"),
    # swarmfish.py tools
    "swarmfish_predict.py":     ("swarmfish.py", "SwarmfishPredict"),
    "swarmfish_session.py":     ("swarmfish.py", "SwarmfishSession"),
    "swarmfish_sessions.py":    ("swarmfish.py", "SwarmfishSessions"),
    "swarmfish_calibration.py": ("swarmfish.py", "SwarmfishCalibration"),
    "swarmfish_outcome.py":     ("swarmfish.py", "SwarmfishOutcome"),
    # investigation_tools.py
    "ontology_search.py":       ("investigation_tools.py", "OntologySearch"),
    "source_ingest.py":         ("investigation_tools.py", "SourceIngest"),
    "entity_resolve.py":        ("investigation_tools.py", "EntityResolve"),
    "relationship_query.py":    ("investigation_tools.py", "RelationshipQuery"),
    "investigation_report.py":  ("investigation_tools.py", "InvestigationReport"),
}

TEMPLATE = """\
# Auto-generated tool stub — delegates to {source}
import sys as _sys, importlib.util as _ilu, os as _os
_src = _os.path.join("{plugin_tools}", "{source}")
_key = "exocortex_tool__{source_base}"
if _key not in _sys.modules:
    _spec = _ilu.spec_from_file_location(_key, _src)
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules[_key] = _mod
    _spec.loader.exec_module(_mod)
{class_name} = _sys.modules[_key].{class_name}
"""

created = []
for stub_name, (source, class_name) in stubs.items():
    source_base = source.replace(".", "_")
    content = TEMPLATE.format(
        source=source,
        plugin_tools=PLUGIN_TOOLS,
        source_base=source_base,
        class_name=class_name,
    )
    path = os.path.join(STUBS_DIR, stub_name)
    with open(path, "w") as f:
        f.write(content)
    created.append(stub_name)

print(f"Created {len(created)} stubs in {STUBS_DIR}")
for s in sorted(created):
    print(f"  {s}")
