/**
 * Exocortex Artifact Message Handler
 * ====================================
 * Registered via the get_message_handler JS extension hook.
 * Handles log messages with type="artifact" — renders HTML content
 * as an interactive block in the chat, with Alpine.js support.
 *
 * The agent emits artifacts via the emit_artifact tool:
 *   emit_artifact(title="Dashboard", html="<div x-data...>...</div>")
 *
 * Module-level setup (runs once on first load):
 *   - Registers the DOMPurify hook to allow Alpine.js directives through sanitization
 *   - Loads the ExoArtifact runtime (sets window.ExoArtifact for use inside artifacts)
 *
 * NOTE: This file is loaded via direct import(), NOT via importComponent.
 * That means module-level side effects are safe — no loading indicator, no DOM disruption.
 * This is why the DOMPurify setup and ExoArtifact import live here instead of page-head.
 */

import { drawMessageDefault } from "/js/messages.js";
import DOMPurify from "/vendor/dompurify/purify.es.mjs";

// Allow Alpine.js directives through DOMPurify sanitization.
// x-*, @*, :* attributes would be stripped by default.
// This runs once when the module is first imported.
DOMPurify.addHook("uponSanitizeAttribute", (node, evt) => {
    const attr = evt.attrName;
    if (attr.startsWith("x-") || attr.startsWith("@") || attr.startsWith(":")) {
        evt.forceKeepAttr = true;
    }
});

// Load the ExoArtifact runtime so artifacts can call ExoArtifact.message() etc.
// exo-artifact.js sets window.ExoArtifact at module load time.
import "/usr/plugins/exocortex/webui/exo-artifact.js";

export default async function registerArtifactHandler(extData) {
    if (extData?.type === "artifact") {
        extData.handler = drawMessageArtifact;
    }
}

function drawMessageArtifact({ id, heading, content, kvps, ...args }) {
    // Build the standard message container with heading — pass empty content
    // so drawMessageDefault doesn't escape our HTML into a <pre> element.
    const { element } = drawMessageDefault({
        id,
        heading: heading || "Artifact",
        content: "",
        kvps,
        ...args,
    });

    if (!content?.trim()) return { element };

    // Find the .message-body created by drawMessageDefault
    const body = element.querySelector(".message-body");
    if (!body) return { element };

    // Inject DOMPurify-sanitized HTML (Alpine.js directives allowed via
    // the hook registered above at module load time).
    const artifactDiv = document.createElement("div");
    artifactDiv.className = "msg-content artifact-content";
    artifactDiv.innerHTML = DOMPurify.sanitize(content);
    body.appendChild(artifactDiv);

    // Boot Alpine.js on the new subtree so x-data etc. activate.
    if (globalThis.Alpine?.initTree) {
        globalThis.Alpine.initTree(artifactDiv);
    }

    return { element };
}
