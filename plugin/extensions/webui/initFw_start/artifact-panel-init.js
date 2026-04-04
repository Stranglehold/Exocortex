/**
 * Artifact Panel — initFw_start hook
 * =====================================
 * Runs BEFORE Alpine is loaded, so we can:
 *   1. Load CSS
 *   2. Load artifact-panel.js (sets window.artifactPanelFactory)
 *   3. Register a named Alpine component via the alpine:init event
 *   4. Inject the panel DOM so Alpine processes it in its own initial walk
 *
 * No Alpine.initTree needed — the panel is present in the DOM when Alpine
 * starts, so it's initialized identically to any static component.
 */

const BASE = "/usr/plugins/exocortex/webui";

export default async function initArtifactPanel() {

    // ── CSS ─────────────────────────────────────────────────────────────────
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${BASE}/artifact-panel.css`;
    document.head.appendChild(link);

    // ── JS — sets window.artifactPanelFactory ────────────────────────────────
    // initFw_start is awaited before Alpine loads, so this import completes
    // before alpine:init fires.
    await import(`${BASE}/artifact-panel.js`);

    // ── Alpine component registration ────────────────────────────────────────
    // alpine:init fires just before Alpine walks the DOM — the correct moment
    // to register named components so x-data="artifactPanel" resolves.
    document.addEventListener("alpine:init", () => {
        Alpine.data("artifactPanel", window.artifactPanelFactory);
    });

    // ── Inject panel DOM ─────────────────────────────────────────────────────
    // Must insert inside .container (the flex row), not outside it.
    // afterend of #right-panel would escape the flex context.
    const container = document.querySelector(".container");
    if (!container || document.getElementById("artifact-panel")) return;

    const panelEl = document.createElement("div");
    panelEl.id = "artifact-panel";
    panelEl.setAttribute("x-data", "artifactPanel");
    panelEl.setAttribute(":class", "{ open: open }");
    container.appendChild(panelEl);

    panelEl.innerHTML = `
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
                    <button class="artifact-header-btn" @click="zoomIn()" title="Zoom in (ctrl+scroll)">zoom_in</button>
                    <button class="artifact-header-btn" @click="zoomOut()" title="Zoom out (ctrl+scroll)">zoom_out</button>
                    <button class="artifact-header-btn" @click="zoomReset()" title="Reset zoom">zoom_out_map</button>
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
}
