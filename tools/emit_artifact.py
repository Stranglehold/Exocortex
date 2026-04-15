"""
emit_artifact — Exocortex Artifact Emission Tool
=================================================

Renders an interactive HTML panel ("artifact") directly in the Agent Zero
chat interface. The panel supports Alpine.js directives and the ExoArtifact
runtime for live data fetching and agent callbacks.

IMPORTANT — use dedicated panel tools first:
  - For OSS intelligence data: use oss_panel (NOT emit_artifact with custom HTML)
  - For SWARMFISH predictions: use swarmfish_panel (NOT emit_artifact with custom HTML)
  - For stack/system status: use stack_status (NOT emit_artifact with custom HTML)

Never generate static HTML that presents fabricated or estimated data as real system
output. If the data must come from an API, use the tool that already calls that API
(oss_panel, swarmfish_panel) rather than writing custom HTML with hardcoded numbers.

When emit_artifact IS appropriate:
  - Bespoke one-off visualisations not covered by any dedicated panel tool
  - The HTML must fetch live data via ExoArtifact.fetchJson() — never hardcode values

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
