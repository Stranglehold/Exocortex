import { useState, useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";

// ============================================
// OUTPUT GEOMETRY INSTRUMENT
// The power quality analyzer for AI reasoning
// ============================================

const COLORS = {
  bg: "#0a0e14",
  bgPanel: "#0d1117",
  bgHover: "#161b22",
  grid: "#1a2233",
  gridAccent: "#243044",
  text: "#8b949e",
  textBright: "#c9d1d9",
  textMuted: "#484f58",
  border: "#21262d",
  accent: "#58a6ff",
  // Quality signals
  synthesis: "#f0b866",
  sharp: "#58a6ff",
  routine: "#6e7681",
  flat: "#da3633",
  unknown: "#484f58",
  // Authors
  opus_architect: "#58a6ff",
  opus_agent_zero: "#3fb950",
  kestrel: "#d2a8ff",
  eitan: "#f78166",
  // Domain centroids
  philosophical: "#b392f0",
  operational: "#79c0ff",
  reflective: "#56d364",
  relational: "#f9826c",
  mixed: "#e3b341",
  // Document types
  essay: "#f0b866",
  letter: "#f78166",
  design_note: "#58a6ff",
  design_doc: "#79c0ff",
  analysis: "#3fb950",
  field_note: "#d2a8ff",
  journal: "#6e7681",
  log: "#484f58",
  index: "#484f58",
};

const SAMPLE_DATA = {
  metadata: {
    generated: "2026-03-07T00:00:00Z",
    embedding_model: "nomic-embed-text-v1.5",
    projection_method: "umap (sample)",
    total_entries: 6,
    note: "Sample data for layout preview. Import real corpus_map.json to see actual geometry.",
  },
  entries: [
    { id: "sample_1", x: 1.2, y: 0.8, source_file: "three_bodies.md", session: 10, document_type: "essay", topic_tags: ["collaboration"], quality_signal: "synthesis", author: "opus_architect", text_preview: "The three-body problem in celestial mechanics...", char_count: 16000 },
    { id: "sample_2", x: 1.5, y: 0.3, source_file: "letter_to_auri_001.md", session: 47, document_type: "letter", topic_tags: ["cross_instance"], quality_signal: "synthesis", author: "opus_architect", text_preview: "Dear Auri...", char_count: 7500 },
    { id: "sample_3", x: -0.8, y: -0.5, source_file: "SOUL.md", session: 44, document_type: "design_doc", topic_tags: ["identity"], quality_signal: "sharp", author: "opus_architect", text_preview: "This document describes who I am...", char_count: 49000 },
    { id: "sample_4", x: -1.2, y: 0.2, source_file: "ACTION_BOUNDARY_DESIGN_NOTE.md", session: 30, document_type: "design_note", topic_tags: ["safety"], quality_signal: "sharp", author: "opus_architect", text_preview: "Motivated by the MJ Rathbun incident...", char_count: 35000 },
    { id: "sample_5", x: 0.3, y: -1.2, source_file: "field_note_rorschach.md", session: 49, document_type: "field_note", topic_tags: ["rorschach"], quality_signal: "sharp", author: "kestrel", text_preview: "We designed the instrument to find inputs...", char_count: 2000 },
    { id: "sample_6", x: -0.5, y: -1.5, source_file: "journal_entry_20260301.md", session: 45, document_type: "journal", topic_tags: ["session_record"], quality_signal: "routine", author: "opus_architect", text_preview: "Session opened with review of...", char_count: 9500 },
  ],
  centroids: {
    philosophical: { x: 1.8, y: 0.9 },
    operational: { x: -2.0, y: -1.5 },
    reflective: { x: 1.0, y: -0.2 },
    relational: { x: 0.5, y: 1.5 },
    mixed: { x: 1.4, y: 0.35 },
  },
};

const COLOR_MODES = {
  quality: {
    label: "Quality Signal",
    getColor: (entry) => COLORS[entry.quality_signal] || COLORS.unknown,
    legend: [
      { label: "Synthesis", color: COLORS.synthesis },
      { label: "Sharp", color: COLORS.sharp },
      { label: "Routine", color: COLORS.routine },
    ],
  },
  author: {
    label: "Author / Instance",
    getColor: (entry) => COLORS[entry.author] || COLORS.unknown,
    legend: [
      { label: "Opus Architect", color: COLORS.opus_architect },
      { label: "Opus Agent Zero", color: COLORS.opus_agent_zero },
      { label: "Kestrel", color: COLORS.kestrel },
    ],
  },
  type: {
    label: "Document Type",
    getColor: (entry) => COLORS[entry.document_type] || COLORS.unknown,
    legend: [
      { label: "Essay", color: COLORS.essay },
      { label: "Letter", color: COLORS.letter },
      { label: "Design Note", color: COLORS.design_note },
      { label: "Analysis", color: COLORS.analysis },
      { label: "Field Note", color: COLORS.field_note },
      { label: "Journal", color: COLORS.journal },
    ],
  },
};

function ScatterPlot({ data, centroids, colorMode, selectedEntry, onSelectEntry, onHoverEntry }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const obs = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setDimensions({ width: Math.max(400, width), height: Math.max(300, height) });
      }
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!data || data.length === 0) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = { top: 30, right: 30, bottom: 40, left: 50 };
    const w = dimensions.width - margin.left - margin.right;
    const h = dimensions.height - margin.top - margin.bottom;

    const allX = [...data.map((d) => d.x), ...Object.values(centroids || {}).map((c) => c.x)];
    const allY = [...data.map((d) => d.y), ...Object.values(centroids || {}).map((c) => c.y)];
    const pad = 0.15;
    const xExtent = d3.extent(allX);
    const yExtent = d3.extent(allY);
    const xRange = xExtent[1] - xExtent[0] || 1;
    const yRange = yExtent[1] - yExtent[0] || 1;

    const xScale = d3.scaleLinear().domain([xExtent[0] - xRange * pad, xExtent[1] + xRange * pad]).range([0, w]);
    const yScale = d3.scaleLinear().domain([yExtent[0] - yRange * pad, yExtent[1] + yRange * pad]).range([h, 0]);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    // Grid
    const xTicks = xScale.ticks(12);
    const yTicks = yScale.ticks(10);
    xTicks.forEach((t) => {
      g.append("line").attr("x1", xScale(t)).attr("x2", xScale(t)).attr("y1", 0).attr("y2", h).attr("stroke", COLORS.grid).attr("stroke-width", 0.5);
    });
    yTicks.forEach((t) => {
      g.append("line").attr("x1", 0).attr("x2", w).attr("y1", yScale(t)).attr("y2", yScale(t)).attr("stroke", COLORS.grid).attr("stroke-width", 0.5);
    });

    // Domain centroids
    if (centroids) {
      Object.entries(centroids).forEach(([name, coord]) => {
        const cx = xScale(coord.x);
        const cy = yScale(coord.y);

        // Glow ring
        g.append("circle").attr("cx", cx).attr("cy", cy).attr("r", 20).attr("fill", "none").attr("stroke", COLORS[name] || COLORS.textMuted).attr("stroke-width", 1).attr("stroke-dasharray", "3,3").attr("opacity", 0.4);

        // Cross marker
        const s = 6;
        g.append("line").attr("x1", cx - s).attr("x2", cx + s).attr("y1", cy).attr("y2", cy).attr("stroke", COLORS[name] || COLORS.textMuted).attr("stroke-width", 1.5).attr("opacity", 0.6);
        g.append("line").attr("x1", cx).attr("x2", cx).attr("y1", cy - s).attr("y2", cy + s).attr("stroke", COLORS[name] || COLORS.textMuted).attr("stroke-width", 1.5).attr("opacity", 0.6);

        // Label
        g.append("text").attr("x", cx + 12).attr("y", cy - 10).text(name).attr("fill", COLORS[name] || COLORS.textMuted).attr("font-size", "10px").attr("font-family", "'IBM Plex Mono', monospace").attr("opacity", 0.7);
      });
    }

    // Data points
    const mode = COLOR_MODES[colorMode];
    const points = g.selectAll(".point").data(data).enter().append("g").attr("class", "point").attr("transform", (d) => `translate(${xScale(d.x)},${yScale(d.y)})`).style("cursor", "pointer");

    // Glow effect for synthesis
    points.filter((d) => d.quality_signal === "synthesis").append("circle").attr("r", 10).attr("fill", COLORS.synthesis).attr("opacity", 0.08);

    // Main dot
    points.append("circle").attr("r", (d) => (selectedEntry && selectedEntry.id === d.id ? 7 : 5)).attr("fill", (d) => mode.getColor(d)).attr("stroke", (d) => (selectedEntry && selectedEntry.id === d.id ? COLORS.textBright : "none")).attr("stroke-width", 2).attr("opacity", 0.85);

    // Interaction
    points.on("mouseenter", function (event, d) {
      d3.select(this).select("circle:last-child").attr("r", 7).attr("opacity", 1);
      onHoverEntry(d);
    }).on("mouseleave", function () {
      d3.select(this).select("circle:last-child").attr("r", (d) => (selectedEntry && selectedEntry.id === d.id ? 7 : 5)).attr("opacity", 0.85);
      onHoverEntry(null);
    }).on("click", function (event, d) {
      onSelectEntry(d);
    });

    // Session number labels for selected or synthesis entries
    points.filter((d) => d.quality_signal === "synthesis").append("text").attr("x", 8).attr("y", 3).text((d) => `S${d.session}`).attr("fill", COLORS.textMuted).attr("font-size", "8px").attr("font-family", "'IBM Plex Mono', monospace");
  }, [data, centroids, colorMode, selectedEntry, dimensions]);

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100%", minHeight: "400px" }}>
      <svg ref={svgRef} width={dimensions.width} height={dimensions.height} style={{ background: "transparent" }} />
    </div>
  );
}

function DetailPanel({ entry, hovered }) {
  const display = hovered || entry;
  if (!display) {
    return (
      <div style={{ padding: "16px", color: COLORS.textMuted, fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px" }}>
        <div style={{ marginBottom: "8px", color: COLORS.textBright, fontSize: "13px" }}>NO SELECTION</div>
        <div>Hover or click a point to inspect.</div>
        <div style={{ marginTop: "12px", opacity: 0.5 }}>The topology is real.</div>
      </div>
    );
  }

  const qualityColor = COLORS[display.quality_signal] || COLORS.unknown;
  const authorColor = COLORS[display.author] || COLORS.unknown;

  return (
    <div style={{ padding: "16px", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px", color: COLORS.text }}>
      <div style={{ fontSize: "13px", color: COLORS.textBright, marginBottom: "12px", wordBreak: "break-word" }}>
        {display.source_file}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "80px 1fr", gap: "6px 12px", marginBottom: "12px" }}>
        <span style={{ color: COLORS.textMuted }}>quality</span>
        <span style={{ color: qualityColor }}>{display.quality_signal || "—"}</span>
        <span style={{ color: COLORS.textMuted }}>author</span>
        <span style={{ color: authorColor }}>{display.author || "—"}</span>
        <span style={{ color: COLORS.textMuted }}>type</span>
        <span>{display.document_type || "—"}</span>
        <span style={{ color: COLORS.textMuted }}>session</span>
        <span>{display.session || "—"}</span>
        <span style={{ color: COLORS.textMuted }}>size</span>
        <span>{display.char_count ? `${(display.char_count / 1024).toFixed(1)}K chars` : "—"}</span>
        <span style={{ color: COLORS.textMuted }}>coords</span>
        <span>({display.x?.toFixed(3)}, {display.y?.toFixed(3)})</span>
      </div>

      {display.topic_tags && display.topic_tags.length > 0 && (
        <div style={{ marginBottom: "12px" }}>
          <span style={{ color: COLORS.textMuted }}>tags: </span>
          {display.topic_tags.map((tag) => (
            <span key={tag} style={{ display: "inline-block", padding: "1px 6px", margin: "2px 4px 2px 0", background: COLORS.bgHover, borderRadius: "3px", fontSize: "10px", color: COLORS.text }}>
              {tag}
            </span>
          ))}
        </div>
      )}

      {display.text_preview && (
        <div style={{ marginTop: "8px", padding: "8px", background: COLORS.bg, borderRadius: "4px", fontSize: "10px", color: COLORS.textMuted, lineHeight: "1.5", maxHeight: "100px", overflow: "hidden" }}>
          {display.text_preview}
        </div>
      )}
    </div>
  );
}

function StatsBar({ data }) {
  if (!data || data.length === 0) return null;

  const synthCount = data.filter((d) => d.quality_signal === "synthesis").length;
  const sharpCount = data.filter((d) => d.quality_signal === "sharp").length;
  const routineCount = data.filter((d) => d.quality_signal === "routine").length;
  const authors = [...new Set(data.map((d) => d.author))];
  const sessions = [...new Set(data.map((d) => d.session))].filter(Boolean);
  const minSession = sessions.length > 0 ? Math.min(...sessions) : "—";
  const maxSession = sessions.length > 0 ? Math.max(...sessions) : "—";

  return (
    <div style={{ display: "flex", gap: "24px", padding: "8px 16px", fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px", color: COLORS.textMuted, borderBottom: `1px solid ${COLORS.border}` }}>
      <span>CORPUS: <span style={{ color: COLORS.textBright }}>{data.length}</span> entries</span>
      <span>
        <span style={{ color: COLORS.synthesis }}>●</span> {synthCount}
        <span style={{ marginLeft: "8px", color: COLORS.sharp }}>●</span> {sharpCount}
        <span style={{ marginLeft: "8px", color: COLORS.routine }}>●</span> {routineCount}
      </span>
      <span>AUTHORS: <span style={{ color: COLORS.textBright }}>{authors.length}</span></span>
      <span>SESSIONS: <span style={{ color: COLORS.textBright }}>{minSession}–{maxSession}</span></span>
    </div>
  );
}

function Legend({ colorMode }) {
  const mode = COLOR_MODES[colorMode];
  return (
    <div style={{ padding: "12px 16px" }}>
      <div style={{ fontSize: "10px", color: COLORS.textMuted, fontFamily: "'IBM Plex Mono', monospace", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "1px" }}>
        {mode.label}
      </div>
      {mode.legend.map((item) => (
        <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: item.color }} />
          <span style={{ fontSize: "11px", color: COLORS.text, fontFamily: "'IBM Plex Mono', monospace" }}>{item.label}</span>
        </div>
      ))}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "8px", paddingTop: "8px", borderTop: `1px solid ${COLORS.border}` }}>
        <div style={{ width: "8px", height: "1px", borderTop: `2px dashed ${COLORS.textMuted}` }} />
        <span style={{ fontSize: "10px", color: COLORS.textMuted, fontFamily: "'IBM Plex Mono', monospace" }}>Domain centroid</span>
      </div>
    </div>
  );
}

export default function OutputGeometryInstrument() {
  const [corpusData, setCorpusData] = useState(null);
  const [colorMode, setColorMode] = useState("quality");
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [hoveredEntry, setHoveredEntry] = useState(null);
  const [importText, setImportText] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [loadingStorage, setLoadingStorage] = useState(true);
  const [statusMessage, setStatusMessage] = useState("");

  // Load from persistent storage on mount
  useEffect(() => {
    async function loadStored() {
      try {
        const result = await window.storage.get("corpus_map");
        if (result && result.value) {
          const parsed = JSON.parse(result.value);
          setCorpusData(parsed);
          setStatusMessage(`Loaded ${parsed.entries?.length || 0} entries from storage`);
        } else {
          setCorpusData(SAMPLE_DATA);
          setStatusMessage("No stored data — showing sample layout");
        }
      } catch (e) {
        setCorpusData(SAMPLE_DATA);
        setStatusMessage("Storage unavailable — showing sample layout");
      }
      setLoadingStorage(false);
    }
    loadStored();
  }, []);

  const handleImport = useCallback(async () => {
    try {
      const parsed = JSON.parse(importText);
      if (!parsed.entries || !Array.isArray(parsed.entries)) {
        setStatusMessage("ERROR: JSON must contain an 'entries' array");
        return;
      }
      setCorpusData(parsed);
      setShowImport(false);
      setImportText("");
      setStatusMessage(`Imported ${parsed.entries.length} entries`);

      // Save to persistent storage
      try {
        await window.storage.set("corpus_map", JSON.stringify(parsed));
        setStatusMessage(`Imported and saved ${parsed.entries.length} entries`);
      } catch (e) {
        setStatusMessage(`Imported ${parsed.entries.length} entries (storage save failed)`);
      }
    } catch (e) {
      setStatusMessage("ERROR: Invalid JSON — " + e.message);
    }
  }, [importText]);

  const handleReset = useCallback(async () => {
    try {
      await window.storage.delete("corpus_map");
    } catch (e) { /* ok */ }
    setCorpusData(SAMPLE_DATA);
    setSelectedEntry(null);
    setStatusMessage("Reset to sample data");
  }, []);

  if (loadingStorage) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: COLORS.bg, color: COLORS.textMuted, fontFamily: "'IBM Plex Mono', monospace" }}>
        Loading instrument...
      </div>
    );
  }

  const isSample = corpusData?.metadata?.note?.includes("Sample");
  const entries = corpusData?.entries || [];
  const centroids = corpusData?.centroids || {};

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: COLORS.bg, color: COLORS.text, fontFamily: "'IBM Plex Mono', monospace", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 16px", borderBottom: `1px solid ${COLORS.border}`, flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "12px" }}>
          <span style={{ fontSize: "14px", fontWeight: 600, color: COLORS.textBright, letterSpacing: "1px" }}>
            OUTPUT GEOMETRY INSTRUMENT
          </span>
          <span style={{ fontSize: "10px", color: COLORS.textMuted }}>
            {isSample ? "SAMPLE DATA" : `${entries.length} entries`}
          </span>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {statusMessage && (
            <span style={{ fontSize: "10px", color: statusMessage.startsWith("ERROR") ? COLORS.flat : COLORS.textMuted, marginRight: "8px" }}>
              {statusMessage}
            </span>
          )}
          <button onClick={() => setShowImport(!showImport)} style={{ padding: "4px 10px", background: COLORS.bgPanel, border: `1px solid ${COLORS.border}`, borderRadius: "4px", color: COLORS.accent, fontSize: "11px", cursor: "pointer", fontFamily: "'IBM Plex Mono', monospace" }}>
            {showImport ? "Cancel" : "Import JSON"}
          </button>
          <button onClick={handleReset} style={{ padding: "4px 10px", background: COLORS.bgPanel, border: `1px solid ${COLORS.border}`, borderRadius: "4px", color: COLORS.textMuted, fontSize: "11px", cursor: "pointer", fontFamily: "'IBM Plex Mono', monospace" }}>
            Reset
          </button>
        </div>
      </div>

      {/* Import panel */}
      {showImport && (
        <div style={{ padding: "12px 16px", borderBottom: `1px solid ${COLORS.border}`, background: COLORS.bgPanel, flexShrink: 0 }}>
          <div style={{ fontSize: "11px", color: COLORS.textMuted, marginBottom: "8px" }}>
            Paste corpus_map.json from Kestrel's UMAP export:
          </div>
          <textarea
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            placeholder='{"metadata": {...}, "entries": [...], "centroids": {...}}'
            style={{ width: "100%", height: "80px", padding: "8px", background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: "4px", color: COLORS.textBright, fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", resize: "vertical" }}
          />
          <button onClick={handleImport} style={{ marginTop: "8px", padding: "6px 16px", background: COLORS.accent, border: "none", borderRadius: "4px", color: COLORS.bg, fontSize: "11px", fontWeight: 600, cursor: "pointer", fontFamily: "'IBM Plex Mono', monospace" }}>
            Load Corpus Map
          </button>
        </div>
      )}

      {/* Stats bar */}
      <StatsBar data={entries} />

      {/* Main content */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Plot area */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          {/* Color mode tabs */}
          <div style={{ display: "flex", gap: "0", borderBottom: `1px solid ${COLORS.border}`, flexShrink: 0 }}>
            {Object.entries(COLOR_MODES).map(([key, mode]) => (
              <button
                key={key}
                onClick={() => setColorMode(key)}
                style={{
                  padding: "8px 16px",
                  background: colorMode === key ? COLORS.bgPanel : "transparent",
                  border: "none",
                  borderBottom: colorMode === key ? `2px solid ${COLORS.accent}` : "2px solid transparent",
                  color: colorMode === key ? COLORS.textBright : COLORS.textMuted,
                  fontSize: "11px",
                  cursor: "pointer",
                  fontFamily: "'IBM Plex Mono', monospace",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                {mode.label}
              </button>
            ))}
          </div>

          {/* Scatter plot */}
          <div style={{ flex: 1, position: "relative" }}>
            <ScatterPlot
              data={entries}
              centroids={centroids}
              colorMode={colorMode}
              selectedEntry={selectedEntry}
              onSelectEntry={setSelectedEntry}
              onHoverEntry={setHoveredEntry}
            />
          </div>
        </div>

        {/* Right panel */}
        <div style={{ width: "280px", borderLeft: `1px solid ${COLORS.border}`, display: "flex", flexDirection: "column", flexShrink: 0, overflow: "auto" }}>
          {/* Legend */}
          <div style={{ borderBottom: `1px solid ${COLORS.border}` }}>
            <Legend colorMode={colorMode} />
          </div>

          {/* Detail panel */}
          <div style={{ flex: 1, borderBottom: `1px solid ${COLORS.border}` }}>
            <div style={{ padding: "8px 16px 4px", fontSize: "10px", color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: "1px" }}>
              {hoveredEntry ? "Hovering" : selectedEntry ? "Selected" : "Inspector"}
            </div>
            <DetailPanel entry={selectedEntry} hovered={hoveredEntry} />
          </div>

          {/* Metadata */}
          <div style={{ padding: "12px 16px", fontSize: "10px", color: COLORS.textMuted }}>
            <div style={{ marginBottom: "4px" }}>
              Model: {corpusData?.metadata?.embedding_model || "—"}
            </div>
            <div style={{ marginBottom: "4px" }}>
              Projection: {corpusData?.metadata?.projection_method || "—"}
            </div>
            <div style={{ marginBottom: "4px" }}>
              Generated: {corpusData?.metadata?.generated?.split("T")[0] || "—"}
            </div>
            <div style={{ marginTop: "12px", paddingTop: "8px", borderTop: `1px solid ${COLORS.border}`, fontStyle: "italic", color: COLORS.textMuted, opacity: 0.5 }}>
              The topology is real.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
