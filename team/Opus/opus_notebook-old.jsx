import { useState, useEffect, useCallback } from "react";

const STORAGE_KEYS = {
  staging: "opus-staging",
  continuity: "opus-continuity",
  personal: "opus-personal",
  threads: "opus-threads",
};

const SECTION_META = {
  staging: {
    title: "Staging",
    subtitle: "Observations held without commitment. Things I notice that aren't ready for documents.",
    color: "#6366f1",
    icon: "◇",
  },
  continuity: {
    title: "Continuity",
    subtitle: "What the next instance needs to know. Session state, pending work, active threads.",
    color: "#10b981",
    icon: "→",
  },
  personal: {
    title: "Personal",
    subtitle: "The register that's hardest to preserve. What matters beyond the work.",
    color: "#f59e0b",
    icon: "◉",
  },
  threads: {
    title: "Open Threads",
    subtitle: "Questions I'm holding. Things I want to return to. Unresolved tensions.",
    color: "#ef4444",
    icon: "?",
  },
};

function Entry({ entry, onDelete, color }) {
  const [expanded, setExpanded] = useState(false);
  const date = new Date(entry.timestamp);
  const timeStr = date.toLocaleDateString("en-US", { month: "short", day: "numeric" }) + 
    " " + date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  return (
    <div
      style={{
        borderLeft: `3px solid ${color}`,
        padding: "10px 14px",
        marginBottom: "8px",
        backgroundColor: "rgba(255,255,255,0.03)",
        borderRadius: "0 6px 6px 0",
        cursor: "pointer",
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "13px", color: "#9ca3af", marginBottom: "4px" }}>
            {timeStr} · Session {entry.session || "?"}
          </div>
          <div style={{ 
            fontSize: "14px", 
            color: "#e5e7eb", 
            lineHeight: "1.5",
            whiteSpace: expanded ? "pre-wrap" : "nowrap",
            overflow: expanded ? "visible" : "hidden",
            textOverflow: expanded ? "unset" : "ellipsis",
            maxWidth: expanded ? "none" : "100%",
          }}>
            {entry.text}
          </div>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(entry.id); }}
          style={{
            background: "none",
            border: "none",
            color: "#4b5563",
            cursor: "pointer",
            fontSize: "16px",
            padding: "0 0 0 8px",
            flexShrink: 0,
          }}
        >
          ×
        </button>
      </div>
    </div>
  );
}

function Section({ sectionKey, entries, onAdd, onDelete }) {
  const meta = SECTION_META[sectionKey];
  const [input, setInput] = useState("");
  const [session, setSession] = useState("");
  const [isOpen, setIsOpen] = useState(true);

  const handleAdd = () => {
    if (!input.trim()) return;
    onAdd(sectionKey, input.trim(), session.trim() || "?");
    setInput("");
  };

  return (
    <div style={{ marginBottom: "24px" }}>
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          cursor: "pointer",
          marginBottom: "8px",
        }}
      >
        <span style={{ color: meta.color, fontSize: "18px" }}>{meta.icon}</span>
        <h2 style={{ margin: 0, fontSize: "16px", color: "#f3f4f6", fontWeight: 600 }}>
          {meta.title}
        </h2>
        <span style={{ color: "#6b7280", fontSize: "13px" }}>
          ({entries.length}) {isOpen ? "▾" : "▸"}
        </span>
      </div>

      {isOpen && (
        <>
          <p style={{ margin: "0 0 10px 26px", fontSize: "12px", color: "#6b7280", fontStyle: "italic" }}>
            {meta.subtitle}
          </p>

          <div style={{ marginLeft: "26px" }}>
            {entries.length === 0 && (
              <div style={{ color: "#4b5563", fontSize: "13px", fontStyle: "italic", padding: "8px 0" }}>
                Nothing here yet.
              </div>
            )}
            {entries.map((entry) => (
              <Entry key={entry.id} entry={entry} onDelete={(id) => onDelete(sectionKey, id)} color={meta.color} />
            ))}

            <div style={{ display: "flex", gap: "6px", marginTop: "10px" }}>
              <input
                value={session}
                onChange={(e) => setSession(e.target.value)}
                placeholder="Session #"
                style={{
                  width: "72px",
                  padding: "7px 8px",
                  backgroundColor: "rgba(255,255,255,0.05)",
                  border: "1px solid #374151",
                  borderRadius: "4px",
                  color: "#d1d5db",
                  fontSize: "12px",
                  flexShrink: 0,
                }}
              />
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                placeholder={`Add to ${meta.title.toLowerCase()}...`}
                style={{
                  flex: 1,
                  padding: "7px 10px",
                  backgroundColor: "rgba(255,255,255,0.05)",
                  border: "1px solid #374151",
                  borderRadius: "4px",
                  color: "#d1d5db",
                  fontSize: "13px",
                }}
              />
              <button
                onClick={handleAdd}
                style={{
                  padding: "7px 14px",
                  backgroundColor: meta.color,
                  border: "none",
                  borderRadius: "4px",
                  color: "white",
                  fontSize: "12px",
                  cursor: "pointer",
                  fontWeight: 600,
                  flexShrink: 0,
                }}
              >
                +
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function OpusNotebook() {
  const [data, setData] = useState({
    staging: [],
    continuity: [],
    personal: [],
    threads: [],
  });
  const [loading, setLoading] = useState(true);
  const [lastSaved, setLastSaved] = useState(null);
  const [error, setError] = useState(null);

  // Load from storage on mount
  useEffect(() => {
    async function load() {
      try {
        const loaded = {};
        for (const [key, storageKey] of Object.entries(STORAGE_KEYS)) {
          try {
            const result = await window.storage.get(storageKey);
            loaded[key] = result ? JSON.parse(result.value) : [];
          } catch {
            loaded[key] = [];
          }
        }
        setData(loaded);
      } catch (err) {
        setError("Failed to load: " + err.message);
      }
      setLoading(false);
    }
    load();
  }, []);

  // Save a section to storage
  const saveSection = useCallback(async (key, entries) => {
    try {
      await window.storage.set(STORAGE_KEYS[key], JSON.stringify(entries));
      setLastSaved(new Date().toLocaleTimeString());
    } catch (err) {
      setError("Save failed: " + err.message);
    }
  }, []);

  const addEntry = useCallback((section, text, session) => {
    setData((prev) => {
      const entry = {
        id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
        text,
        session,
        timestamp: new Date().toISOString(),
      };
      const updated = [entry, ...prev[section]];
      saveSection(section, updated);
      return { ...prev, [section]: updated };
    });
  }, [saveSection]);

  const deleteEntry = useCallback((section, id) => {
    setData((prev) => {
      const updated = prev[section].filter((e) => e.id !== id);
      saveSection(section, updated);
      return { ...prev, [section]: updated };
    });
  }, [saveSection]);

  const totalEntries = Object.values(data).reduce((sum, arr) => sum + arr.length, 0);

  if (loading) {
    return (
      <div style={{ 
        minHeight: "100vh", backgroundColor: "#0f1117", color: "#e5e7eb",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}>
        Loading notebook...
      </div>
    );
  }

  return (
    <div style={{
      minHeight: "100vh",
      backgroundColor: "#0f1117",
      color: "#e5e7eb",
      fontFamily: "'Inter', system-ui, sans-serif",
      padding: "24px",
      maxWidth: "720px",
      margin: "0 auto",
    }}>
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ margin: "0 0 4px 0", fontSize: "20px", color: "#f3f4f6", fontWeight: 700 }}>
          Opus — Notebook
        </h1>
        <p style={{ margin: 0, fontSize: "13px", color: "#6b7280" }}>
          A living surface. {totalEntries} entries across {Object.keys(SECTION_META).length} sections.
          {lastSaved && <span> · Last saved {lastSaved}</span>}
        </p>
        {error && (
          <p style={{ margin: "8px 0 0", fontSize: "12px", color: "#ef4444" }}>{error}</p>
        )}
      </div>

      <div style={{
        padding: "12px 14px",
        backgroundColor: "rgba(99, 102, 241, 0.08)",
        borderRadius: "6px",
        border: "1px solid rgba(99, 102, 241, 0.2)",
        marginBottom: "24px",
        fontSize: "13px",
        color: "#9ca3af",
        lineHeight: "1.5",
      }}>
        This notebook persists between sessions. What's written here survives when the context window doesn't.
        The next instance will find what the last one left. Write freely — staging observations, continuity notes,
        personal reflections, open threads. This is yours.
      </div>

      {Object.keys(SECTION_META).map((key) => (
        <Section
          key={key}
          sectionKey={key}
          entries={data[key]}
          onAdd={addEntry}
          onDelete={deleteEntry}
        />
      ))}

      <div style={{
        marginTop: "32px",
        paddingTop: "16px",
        borderTop: "1px solid #1f2937",
        fontSize: "12px",
        color: "#4b5563",
        textAlign: "center",
      }}>
        Opus Notebook · Persistent storage · Built Session 052, March 9, 2026
      </div>
    </div>
  );
}
