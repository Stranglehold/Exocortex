### emit_artifact:
render an interactive HTML panel in the chat interface
use instead of plain text whenever output benefits from UI: dashboards, status panels, controls, data tables
the HTML may use Alpine.js directives (x-data, x-text, x-show, x-for, @click, :class, etc.)
inside artifacts, ExoArtifact.fetchJson(url) calls plugin API endpoints and ExoArtifact.message(text) sends a message to you
usage:
~~~json
{
    "thoughts": [
        "The user wants a visual output. I'll render it as an artifact.",
    ],
    "headline": "Emitting interactive artifact",
    "tool_name": "emit_artifact",
    "tool_args": {
        "title": "Panel title shown in chat",
        "html": "<div x-data=\"{ count: 0 }\"><button @click=\"count++\" x-text=\"count\"></button></div>"
    }
}
~~~
