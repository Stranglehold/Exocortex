/**
 * Artifacts Sidebar Store
 * =======================
 * Alpine store for the artifact browser panel in the left sidebar.
 *
 * Polls /artifacts_list every 30s and on demand. When the user clicks an
 * artifact, fetches its content via /artifacts_get and loads it into the
 * existing artifact panel (window.artifactPanel.update).
 */

import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";

const POLL_INTERVAL_MS = 30_000;

const model = {
  artifacts: [],
  loading: false,
  error: "",
  lastRefresh: 0,

  init() {
    this.refresh();
    setInterval(() => this.refresh(), POLL_INTERVAL_MS);
  },

  async refresh() {
    try {
      this.loading = true;
      this.error = "";
      const resp = await fetchApi("/artifacts_list", { method: "GET" });
      if (!resp.ok) {
        this.error = `HTTP ${resp.status}`;
        return;
      }
      const data = await resp.json();
      this.artifacts = Array.isArray(data.artifacts) ? data.artifacts : [];
      this.lastRefresh = Date.now();
    } catch (e) {
      this.error = e?.message || "fetch error";
    } finally {
      this.loading = false;
    }
  },

  async load(name) {
    try {
      const resp = await fetchApi("/artifacts_get", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!resp.ok) {
        console.error("[artifacts-store] load failed:", resp.status);
        return;
      }
      const data = await resp.json();
      if (data.error) {
        console.error("[artifacts-store] load error:", data.error);
        return;
      }
      // Inject into the existing artifact panel
      if (window.artifactPanel?.update) {
        window.artifactPanel.update(data.content, data.type || "html", data.title || name);
      } else {
        console.warn("[artifacts-store] artifactPanel not ready");
      }
    } catch (e) {
      console.error("[artifacts-store] load exception:", e);
    }
  },

  formatSize(bytes) {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
  },

  formatDate(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso + "Z"); // treat as UTC
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return iso.slice(0, 10);
    }
  },
};

export const store = createStore("artifacts", model);
