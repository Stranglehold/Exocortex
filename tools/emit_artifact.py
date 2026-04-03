"""
emit_artifact — Exocortex Artifact Emission Tool
=================================================

Renders an interactive HTML panel ("artifact") directly in the Agent Zero
chat interface. The panel supports Alpine.js directives and the ExoArtifact
runtime for live data fetching and agent callbacks.

When to use:
  - Displaying a dashboard or control panel (stack status, OSS summary, etc.)
  - Showing live-updating data that the user can interact with
  - Any output that benefits from structured UI rather than plain text

The HTML content may use:
  - Alpine.js: x-data, x-text, x-show, x-for, @click, :class, etc.
  - ExoArtifact.fetchJson(url)  — calls a plugin API endpoint, returns JSON
  - ExoArtifact.action(url, payload) — POSTs to a plugin API endpoint
  - ExoArtifact.message(text) — sends a chat message to the agent

Example:
  emit_artifact(
    title="Stack Status",
    html='<div x-data="{ ok: false }" x-init="ExoArtifact.fetchJson(...).then(d => ok = d.ok)">...</div>'
  )
"""

from helpers.tool import Tool, Response


class EmitArtifact(Tool):
    """Emit an interactive HTML artifact panel into the chat."""

    async def execute(
        self,
        title: str = "Artifact",
        html: str = "",
        **kwargs,
    ) -> Response:
        if not html or not html.strip():
            return Response(message="emit_artifact: no HTML content provided.", break_loop=False)

        # Emit the artifact as a special log entry.
        # type="artifact" is handled by artifact-handler.js on the frontend.
        # The Literal type hint in log.py is not runtime-enforced (dataclass).
        self.agent.context.log.log(
            type="artifact",   # type: ignore[arg-type]
            heading=title,
            content=html,
        )

        return Response(
            message=f"Artifact '{title}' emitted to chat.",
            break_loop=False,
        )
