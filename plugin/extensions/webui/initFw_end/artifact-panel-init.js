/**
 * Artifact Panel — DOM injection and Alpine registration
 * =======================================================
 * Hook: initFw_end  (fires after Alpine is initialized and running)
 *
 * Inserts #artifact-panel as a flex sibling of #right-panel so it appears
 * as a collapsible right strip. Loads the CSS and registers the Alpine
 * component defined in artifact-panel.js.
 *
 * The panel is always present in the DOM — collapsed to 28px when empty,
 * expanding to the persisted width when an artifact arrives.
 *
 * artifact-handler.js (get_message_handler) routes type="artifact" messages
 * to window.artifactPanel.update() rather than rendering inline in the chat.
 */

const BASE = "/usr/plugins/exocortex/webui";

export default async function initArtifactPanel() {

    // ── Load CSS ────────────────────────────────────────────────────────────
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${BASE}/artifact-panel.css`;
    document.head.appendChild(link);

    // ── Load JS (registers Alpine.data('artifactPanel', ...)) ───────────────
    await import(`${BASE}/artifact-panel.js`);

    // ── Inject panel HTML ───────────────────────────────────────────────────
    const rightPanel = document.getElementById("right-panel");
    if (!rightPanel || document.getElementById("artifact-panel")) return;

    const panelEl = document.createElement("div");
    panelEl.id = "artifact-panel";
    panelEl.setAttribute("x-data", "artifactPanel");
    // Insert after #right-panel so it sits to the right of the chat area
    rightPanel.insertAdjacentElement("afterend", panelEl);

    // ── Panel HTML structure ─────────────────────────────────────────────────
    panelEl.innerHTML = `
    <div class="artifact-sash"></div>

    <!-- Toggle tab strip (always-visible 28px strip) -->
    <div class="artifact-tab" @click="toggle()" title="Toggle artifact panel">
        <span class="material-symbols-outlined artifact-tab-icon">widgets</span>
        <span class="artifact-tab-label" x-text="hasContent ? title : 'Artifacts'"></span>
        <div class="artifact-dot" :class="hasContent ? 'visible' : ''"></div>
    </div>

    <!-- Panel content (only rendered when open) -->
    <div class="artifact-content" x-show="open" x-cloak>

        <!-- Multi-tab bar -->
        <div class="artifact-tabs-bar" x-show="tabs.length > 1">
            <template x-for="(tab, idx) in tabs" :key="tab.id">
                <div class="artifact-tab-item" :class="activeTab === idx ? 'active' : ''"
                    @click="switchTab(idx)">
                    <span class="artifact-tab-type-icon">description</span>
                    <span class="artifact-tab-title" x-text="tab.title"></span>
                    <button class="artifact-tab-close" @click.stop="closeTab(idx)">close</button>
                </div>
            </template>
        </div>

        <!-- Header -->
        <div class="artifact-header">
            <span class="artifact-header-title" x-text="title || 'Artifact'"></span>
            <span class="artifact-header-type" x-text="type"></span>
            <div class="artifact-header-actions">
                <div class="artifact-zoom-controls" style="display:flex;gap:0;">
                    <button class="artifact-header-btn" @click="zoomIn()" title="Zoom in">zoom_in</button>
                    <button class="artifact-header-btn" @click="zoomOut()" title="Zoom out">zoom_out</button>
                    <button class="artifact-header-btn" @click="zoomReset()" title="Reset zoom">zoom_out_map</button>
                    <button class="artifact-header-btn" @click="togglePan()"
                        :class="panMode ? 'artifact-btn-active' : ''"
                        title="Pan mode">pan_tool</button>
                </div>
                <div class="artifact-service-links" style="display:flex;gap:0;">
                    <template x-for="svc in serviceLinks" :key="svc.label">
                        <button class="artifact-header-btn"
                            @click="window.open(svc.url,'_blank')"
                            :title="svc.label"
                            x-text="svc.icon"></button>
                    </template>
                </div>
                <button class="artifact-header-btn" @click="reopenLastTab()"
                    :disabled="closedTabs.length === 0"
                    title="Reopen last closed tab">tab_unselected</button>
                <button class="artifact-header-btn" @click="openInNewTab()" title="Open in new tab">open_in_new</button>
                <button class="artifact-header-btn" @click="closeActiveTab()" title="Close tab">close</button>
            </div>
        </div>

        <!-- Frame wrapper: skeleton + iframe -->
        <div class="artifact-frame-wrapper">
            <div id="artifact-skeleton">
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-block"></div>
            </div>
            <iframe id="artifact-frame" sandbox="allow-scripts allow-same-origin allow-forms"
                title="Artifact"></iframe>
        </div>
    </div>`;

    // ── Boot Alpine on the injected subtree ──────────────────────────────────
    if (globalThis.Alpine?.initTree) {
        globalThis.Alpine.initTree(panelEl);
    }
}
