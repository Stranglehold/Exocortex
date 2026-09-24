/**
 * ExoArtifact Runtime Library
 * ============================
 * Loaded globally via the page-head extension.
 * Wraps Agent Zero's own fetchApi so artifacts can communicate with the
 * agent backend — auth and CSRF handled automatically.
 *
 * Usage inside artifact HTML:
 *   await ExoArtifact.fetchJson('/api/plugins/exocortex/api_control_panel')
 *   await ExoArtifact.action('/api/plugins/oss/control', { action: 'pause' })
 *   await ExoArtifact.message('Run stack_status tool and show me the result')
 */

import { fetchApi, callJsonApi } from "/js/api.js";

const ExoArtifact = {

    /**
     * CSRF-aware fetch — same auth as the rest of the A0 frontend.
     * Drop-in for window.fetch against A0 API endpoints.
     */
    fetch: fetchApi,

    /**
     * POST JSON to an A0 API endpoint, return parsed response.
     * @param {string} url
     * @param {object} [data]
     */
    async fetchJson(url, data = {}) {
        return callJsonApi(url, data);
    },

    /**
     * Send a chat message to the agent — triggers a full agent turn.
     * @param {string} text
     */
    async message(text) {
        return callJsonApi("/api_message", { message: text });
    },

    /**
     * POST to a plugin API endpoint with a JSON payload.
     * @param {string} endpoint
     * @param {object} [payload]
     */
    async action(endpoint, payload = {}) {
        return callJsonApi(endpoint, payload);
    },
};

window.ExoArtifact = ExoArtifact;
export { ExoArtifact };
