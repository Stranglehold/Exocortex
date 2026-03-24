import { useState, useEffect, useRef } from "react";

const TAGS = ["observation", "surprise", "thesis", "canary", "personal"];

const TAG_COLORS = {
  observation: { bg: "#1a2a1a", border: "#3a5a3a", text: "#7ab87a" },
  surprise: { bg: "#2a1a1a", border: "#5a3a3a", text: "#b87a7a" },
  thesis: { bg: "#1a1a2a", border: "#3a3a5a", text: "#7a7ab8" },
  canary: { bg: "#2a2a1a", border: "#5a5a3a", text: "#b8b87a" },
  personal: { bg: "#2a1a2a", border: "#5a3a5a", text: "#b87ab8" },
};

const FONTS = `@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Share+Tech+Mono&display=swap');`;

const formatDate = (iso) => {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    month: "short", day: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false
  });
};

const ScanlineOverlay = () => (
  <div style={{
    position: "fixed", inset: 0, pointerEvents: "none", zIndex: 1000,
    background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
  }} />
);

export default function EitanFieldNotes() {
  const [entries, setEntries] = useState([]);
  const [draft, setDraft] = useState("");
  const [tag, setTag] = useState("observation");
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState(false);
  const [view, setView] = useState("log"); // "log" | "write"
  const textRef = useRef(null);

  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = FONTS + `
      * { box-sizing: border-box; }
      ::-webkit-scrollbar { width: 4px; }
      ::-webkit-scrollbar-track { background: #080c08; }
      ::-webkit-scrollbar-thumb { background: #2a3a2a; border-radius: 2px; }
      textarea:focus { outline: none; }
      button:focus { outline: none; }
      @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
      @keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
      @keyframes flashBorder { 0%{border-color:#7ab87a} 50%{border-color:#c8e87a} 100%{border-color:#2a3a2a} }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  useEffect(() => {
    async function load() {
      try {
        const result = await window.storage.get("eitan-field-notes");
        if (result?.value) {
          setEntries(JSON.parse(result.value));
        }
      } catch (e) {
        // no entries yet
      }
      setLoading(false);
    }
    load();
  }, []);

  const save = async (newEntries) => {
    setSaving(true);
    try {
      await window.storage.set("eitan-field-notes", JSON.stringify(newEntries));
    } catch (e) {
      console.error("Storage error:", e);
    }
    setSaving(false);
  };

  const submit = async () => {
    if (!draft.trim()) return;
    const entry = {
      id: Date.now(),
      text: draft.trim(),
      tag,
      ts: new Date().toISOString(),
    };
    const updated = [entry, ...entries];
    setEntries(updated);
    setDraft("");
    setFlash(true);
    setTimeout(() => setFlash(false), 800);
    await save(updated);
    setView("log");
  };

  const deleteEntry = async (id) => {
    const updated = entries.filter(e => e.id !== id);
    setEntries(updated);
    await save(updated);
  };

  const visible = filter === "all" ? entries : entries.filter(e => e.tag === filter);

  const styles = {
    root: {
      minHeight: "100vh",
      background: "#060a06",
      color: "#8aaa8a",
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: "13px",
      lineHeight: "1.6",
      padding: "0",
      position: "relative",
    },
    header: {
      borderBottom: "1px solid #1a2a1a",
      padding: "16px 24px 12px",
      display: "flex",
      alignItems: "baseline",
      justifyContent: "space-between",
      background: "#060a06",
      position: "sticky",
      top: 0,
      zIndex: 10,
    },
    titleBlock: {
      display: "flex",
      alignItems: "baseline",
      gap: "12px",
    },
    title: {
      fontFamily: "'Share Tech Mono', monospace",
      fontSize: "15px",
      color: "#c8e0a0",
      letterSpacing: "0.12em",
      margin: 0,
      textTransform: "uppercase",
    },
    subtitle: {
      fontSize: "11px",
      color: "#3a5a3a",
      letterSpacing: "0.06em",
    },
    cursor: {
      display: "inline-block",
      width: "8px",
      height: "13px",
      background: "#7ab87a",
      marginLeft: "4px",
      verticalAlign: "middle",
      animation: "blink 1.2s step-end infinite",
    },
    statusBar: {
      fontSize: "10px",
      color: "#2a4a2a",
      letterSpacing: "0.08em",
    },
    nav: {
      padding: "10px 24px",
      display: "flex",
      gap: "8px",
      borderBottom: "1px solid #0f1a0f",
      alignItems: "center",
      flexWrap: "wrap",
    },
    navBtn: (active) => ({
      background: active ? "#1a2a1a" : "transparent",
      border: `1px solid ${active ? "#3a5a3a" : "#1a2a1a"}`,
      color: active ? "#c8e0a0" : "#3a5a3a",
      padding: "3px 10px",
      borderRadius: "2px",
      cursor: "pointer",
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: "11px",
      letterSpacing: "0.06em",
      transition: "all 0.15s",
    }),
    divider: {
      width: "1px",
      height: "16px",
      background: "#1a2a1a",
      margin: "0 4px",
    },
    main: {
      padding: "16px 24px",
      maxWidth: "800px",
    },
    writeArea: {
      animation: "fadeIn 0.2s ease",
    },
    tagRow: {
      display: "flex",
      gap: "6px",
      marginBottom: "12px",
      flexWrap: "wrap",
    },
    tagBtn: (t, selected) => ({
      background: selected ? TAG_COLORS[t].bg : "transparent",
      border: `1px solid ${selected ? TAG_COLORS[t].border : "#1a2a1a"}`,
      color: selected ? TAG_COLORS[t].text : "#2a4a2a",
      padding: "2px 10px",
      borderRadius: "2px",
      cursor: "pointer",
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: "11px",
      letterSpacing: "0.06em",
      transition: "all 0.15s",
    }),
    textarea: {
      width: "100%",
      minHeight: "140px",
      background: "#080c08",
      border: `1px solid ${flash ? "#7ab87a" : "#1a2a1a"}`,
      borderRadius: "2px",
      color: "#a0c0a0",
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: "13px",
      lineHeight: "1.7",
      padding: "12px",
      resize: "vertical",
      transition: "border-color 0.3s",
      animation: flash ? "flashBorder 0.8s ease" : "none",
    },
    submitRow: {
      display: "flex",
      justifyContent: "flex-end",
      gap: "8px",
      marginTop: "10px",
    },
    btn: (primary) => ({
      background: primary ? "#1a2a1a" : "transparent",
      border: `1px solid ${primary ? "#3a5a3a" : "#1a2a1a"}`,
      color: primary ? "#c8e0a0" : "#3a5a3a",
      padding: "5px 16px",
      borderRadius: "2px",
      cursor: "pointer",
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: "12px",
      letterSpacing: "0.08em",
      transition: "all 0.15s",
    }),
    logArea: {
      animation: "fadeIn 0.2s ease",
    },
    emptyState: {
      color: "#1a3a1a",
      fontSize: "12px",
      fontStyle: "italic",
      padding: "32px 0",
      textAlign: "center",
      letterSpacing: "0.06em",
    },
    entry: (t) => ({
      background: TAG_COLORS[t].bg,
      border: `1px solid ${TAG_COLORS[t].border}`,
      borderRadius: "2px",
      padding: "12px 14px",
      marginBottom: "8px",
      animation: "fadeIn 0.25s ease",
      position: "relative",
    }),
    entryMeta: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "8px",
    },
    entryTag: (t) => ({
      color: TAG_COLORS[t].text,
      fontSize: "10px",
      letterSpacing: "0.12em",
      textTransform: "uppercase",
    }),
    entryTs: {
      color: "#2a4a2a",
      fontSize: "10px",
      letterSpacing: "0.04em",
    },
    entryText: {
      color: "#8aaa8a",
      fontSize: "13px",
      lineHeight: "1.65",
      whiteSpace: "pre-wrap",
      wordBreak: "break-word",
    },
    deleteBtn: {
      background: "transparent",
      border: "none",
      color: "#1a3a1a",
      cursor: "pointer",
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: "11px",
      padding: "2px 4px",
      transition: "color 0.15s",
      marginLeft: "8px",
    },
    countLine: {
      color: "#2a4a2a",
      fontSize: "10px",
      letterSpacing: "0.08em",
      marginBottom: "12px",
      paddingBottom: "8px",
      borderBottom: "1px solid #0f1a0f",
    },
    loadingState: {
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      height: "200px",
      color: "#2a4a2a",
      fontSize: "12px",
      letterSpacing: "0.1em",
    },
  };

  if (loading) return (
    <div style={styles.root}>
      <div style={styles.loadingState}>LOADING FIELD NOTES...</div>
    </div>
  );

  return (
    <div style={styles.root}>
      <ScanlineOverlay />

      <div style={styles.header}>
        <div style={styles.titleBlock}>
          <h1 style={styles.title}>
            EITAN / FIELD NOTES<span style={styles.cursor} />
          </h1>
          <span style={styles.subtitle}>intelligence · analysis · observation</span>
        </div>
        <div style={styles.statusBar}>
          {saving ? "WRITING..." : `${entries.length} ENTRIES`}
        </div>
      </div>

      <div style={styles.nav}>
        <button style={styles.navBtn(view === "write")} onClick={() => { setView("write"); setTimeout(() => textRef.current?.focus(), 50); }}>
          + NEW ENTRY
        </button>
        <button style={styles.navBtn(view === "log")} onClick={() => setView("log")}>
          FIELD LOG
        </button>
        <div style={styles.divider} />
        {["all", ...TAGS].map(t => (
          <button key={t} style={styles.navBtn(filter === t && view === "log")}
            onClick={() => { setFilter(t); setView("log"); }}>
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      <div style={styles.main}>

        {view === "write" && (
          <div style={styles.writeArea}>
            <div style={styles.tagRow}>
              {TAGS.map(t => (
                <button key={t} style={styles.tagBtn(t, tag === t)} onClick={() => setTag(t)}>
                  {t}
                </button>
              ))}
            </div>
            <textarea
              ref={textRef}
              style={styles.textarea}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder="What needs to be recorded..."
              onKeyDown={e => {
                if (e.key === "Enter" && e.metaKey) submit();
              }}
            />
            <div style={styles.submitRow}>
              <button style={styles.btn(false)} onClick={() => { setDraft(""); setView("log"); }}>
                CANCEL
              </button>
              <button style={styles.btn(true)} onClick={submit} disabled={!draft.trim()}>
                RECORD ↵
              </button>
            </div>
            <div style={{ ...styles.entryTs, marginTop: "8px", textAlign: "right" }}>
              ⌘↵ to submit
            </div>
          </div>
        )}

        {view === "log" && (
          <div style={styles.logArea}>
            {visible.length > 0 && (
              <div style={styles.countLine}>
                {filter === "all" ? `ALL ENTRIES` : filter.toUpperCase()} — {visible.length} RECORD{visible.length !== 1 ? "S" : ""}
              </div>
            )}
            {visible.length === 0 ? (
              <div style={styles.emptyState}>
                {filter === "all" ? "no entries yet. field log is empty." : `no ${filter} entries.`}
              </div>
            ) : (
              visible.map(entry => (
                <div key={entry.id} style={styles.entry(entry.tag)}>
                  <div style={styles.entryMeta}>
                    <span style={styles.entryTag(entry.tag)}>{entry.tag}</span>
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <span style={styles.entryTs}>{formatDate(entry.ts)}</span>
                      <button
                        style={styles.deleteBtn}
                        onClick={() => deleteEntry(entry.id)}
                        onMouseEnter={e => e.target.style.color = "#5a3a3a"}
                        onMouseLeave={e => e.target.style.color = "#1a3a1a"}
                        title="delete"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                  <div style={styles.entryText}>{entry.text}</div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
