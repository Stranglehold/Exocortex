### swarmfish_predict:
run a prediction question through the SWARMFISH analytical committee
eight analytical profiles independently assess the question then aggregate to consensus
returns: session_id, consensus confidence, operator brief, per-profile assessments (Level 1), dissenter list
use the session_id with swarmfish_session to get full deliberation transparency (Level 2 or 3)

V2: configurable committee — pass committee list to run a subset of profiles
available profiles: "Base Rate Analyst", "Contrarian", "Historian", "Reflexivity Modeler",
  "Decomposer", "Network Analyst", "Sentiment Decoder", "Risk Manager"
usage:
~~~json
{
    "thoughts": ["The user wants a prediction. I'll run it through SWARMFISH."],
    "headline": "Running SWARMFISH prediction",
    "tool_name": "swarmfish_predict",
    "tool_args": {
        "question": "Will Iran attempt to block the Strait of Hormuz within 6 months?",
        "domain": "geopolitical",
        "context": "Optional analyst-supplied evidence and context",
        "committee": ["Base Rate Analyst", "Historian", "Contrarian"]
    }
}
~~~

### swarmfish_session:
get full session detail with configurable deliberation transparency
level 1 = confidence + one-sentence summary per profile (default in predict response)
level 2 = structured summary: reasoning, assumptions, dissent, evidence cited
level 3 = full LLM reasoning text (show me your work)
usage:
~~~json
{
    "tool_name": "swarmfish_session",
    "tool_args": {
        "session_id": "<session_id from swarmfish_predict>",
        "level": 2
    }
}
~~~

### swarmfish_sessions:
list recent prediction sessions
usage:
~~~json
{
    "tool_name": "swarmfish_sessions",
    "tool_args": {
        "limit": 10,
        "domain": "geopolitical"
    }
}
~~~

### swarmfish_calibration:
get calibration state — per-profile Brier scores by domain
shows which profiles are accurate on which question types
usage:
~~~json
{
    "tool_name": "swarmfish_calibration",
    "tool_args": {}
}
~~~

### swarmfish_outcome:
log outcome for a completed prediction session and update profile calibration
outcome: 0.0 = prediction wrong, 1.0 = prediction correct, 0.5 = partially correct
usage:
~~~json
{
    "tool_name": "swarmfish_outcome",
    "tool_args": {
        "session_id": "<session_id>",
        "outcome": 1.0,
        "outcome_date": "2026-05-01",
        "notes": "Iran did not block the strait — prediction was correct"
    }
}
~~~
