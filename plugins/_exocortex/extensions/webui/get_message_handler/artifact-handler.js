/**
 * Exocortex Artifact Message Handler
 * ====================================
 * Registered via the get_message_handler JS extension hook.
 * Handles log messages with type="artifact" — routes them to the
 * collapsible right-side artifact panel (window.artifactPanel).
 *
 * The panel is injected by artifact-panel-init.js (initFw_end hook).
 * If the panel is not yet present (race on first load), falls back to
 * a brief inline notification in the chat.
 *
 * The agent emits artifacts via the emit_artifact tool:
 *   emit_artifact(title="Dashboard", html="<div x-data...>...</div>")
 *
 * Module-level setup (runs once on first load):
 *   - Loads the ExoArtifact runtime (sets window.ExoArtifact for use
 *     inside artifacts rendered in the panel iframe)
 */

import { drawMessageDefault } from "/js/messages.js";

// Load the ExoArtifact runtime so artifacts can call ExoArtifact.message() etc.
// exo-artifact.js sets window.ExoArtifact at module load time.
import "/usr/plugins/_exocortex/webui/exo-artifact.js";

export default async function registerArtifactHandler(extData) {
    if (extData?.type === "artifact") {
        extData.handler = drawMessageArtifact;
    }
}

function drawMessageArtifact({ id, heading, content, kvps, ...args }) {
    // Route to the right-side panel if it's available
    if (window.artifactPanel && typeof window.artifactPanel.update === "function") {
        window.artifactPanel.update(content || "", "html", heading || "Artifact");

        // Emit a compact inline notice so the chat log records that an artifact
        // was sent to the panel — gives the conversation context without cluttering it.
        const notice = `Artifact "${heading || "Artifact"}" → panel`;
        return drawMessageDefault({
            id,
            heading: heading || "Artifact",
            content: notice,
            kvps,
            ...args,
        });
    }

    // Fallback: panel not ready (shouldn't happen after first load, but safe)
    // Render inline as a plain text block.
    return drawMessageDefault({
        id,
        heading: heading || "Artifact",
        content: content || "",
        kvps,
        ...args,
    });
}
