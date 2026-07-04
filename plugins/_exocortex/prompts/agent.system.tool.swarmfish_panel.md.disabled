### swarmfish_panel:
emit an interactive SWARMFISH panel artifact into the chat interface
three views available — sessions browser, calibration dashboard, and prediction form

usage:
~~~json
{
    "tool_name": "swarmfish_panel",
    "tool_args": {
        "view": "sessions",
        "domain": "geopolitical",
        "session_id": "<optional — pre-expands this session>"
    }
}
~~~

views:
- `sessions`    — session browser: list recent predictions, click to expand inline detail
                  shows consensus confidence, operator brief, per-profile reasoning
                  includes outcome logging (log 0=wrong / 0.5=partial / 1=correct)
                  supports L1/L2/L3 deliberation transparency in expanded view
- `calibration` — per-profile Brier scores by domain + consensus weights
                  lower Brier = more accurate (random baseline = 0.25)
- `predict`     — interactive prediction form: question + domain + context + committee selector
                  runs the full committee (~30s), shows consensus result inline

use swarmfish_panel instead of plain text when the user wants to browse sessions,
review deliberation, log outcomes, check calibration, or submit a new prediction.
