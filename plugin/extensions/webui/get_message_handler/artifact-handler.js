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
 * The ExoArtifact runtime (loaded via page-head) provides:
 *   ExoArtifact.fetchJson(), ExoArtifact.action(), ExoArtifact.message()
 */

import { drawMessageDefault } from "/js/messages.js";
import DOMPurify from "/vendor/dompurify/purify.es.mjs";

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
    // the hook configured in exo-artifact-runtime.html).
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
