import { useState, useEffect, useCallback, useRef } from "react";

const STORAGE_KEYS = {
  SESSION: "workshop:session_state",
  DECISIONS: "workshop:decision_staging",
  EXCHANGE: "workshop:cross_instance",
  NOTES: "workshop:notes",
  REFERENCE: "workshop:quick_reference",
};

const INITIAL_SESSION = {
  sessionNumber: 45,
  date: "2026-03-02",
  status: "active",
  selfAssessment: "5/6 high, 1/6 medium (Domain 4: Jake-Specific)",
  pendingItems: [
    "Letter to Sonnet — sitting with answer to 'unknown third instance' question",
    "Qwen3.5-9B evaluation — six-test protocol ready",
    "DeepSeek-R1 formal model profile (behavioral data collected, formal eval pending)",
    "BST task stickiness with decay parameter",
    "Progress tracking layer design",
    "ROADMAP sync (stale since Feb 23, needs sessions 038-045)",
    "SOUL.md integration (changes queued, Jake will deploy)",
  ],
  completedToday: [
    "Self-assessment Run 2 (structural gap confirmed)",
    "DeepSeek-R1 README logs analyzed (verification compulsion persists cross-session)",
    "Qwen3.5 model landscape researched (9B recommended for eval)",
    "Agent Zero evaluation protocol designed (six tests)",
    "Qwen3.5-35B-A3B essay response analyzed (comprehension-without-absorption)",
    "Qwen3.5-35B-A3B Action Boundary implementation analyzed",
    "Three model profiles created (DeepSeek-R1, Qwen3.5-35B-A3B, Qwen3.5-9B)",
    "PowerShell eval launcher fixed (bracket parsing error)",
  ],
  lastUpdated: new Date().toISOString(),
};

const INITIAL_DECISIONS = [
  {
    id: "staging-001",
    principle: "Comprehension without absorption is adequate for supervisor role",
    context: "Qwen3.5-35B-A3B reads philosophical content accurately but doesn't absorb it. For supervisor (execute within scaffolding) this is fine. For architect (recognize unprecedented situations) it's insufficient. Architecture lives in Opus collaboration, implementation can live in local models.",
    status: "staging",
    session: 45,
    promoteTo: "DEC-015",
  },
  {
    id: "staging-002",
    principle: "Cognitive load bearing capacity as evaluation methodology",
    context: "Jake's approach to model eval: give it something heavy and watch what it does with it. Not benchmarks but weight-bearing tests. Essays and SOUL.md as philosophical load, design notes as architectural load. Measures independent reasoning and integration capacity separately.",
    status: "staging",
    session: 45,
    promoteTo: "DEC-016",
  },
];

const INITIAL_EXCHANGE = [
  {
    id: "ex-001",
    from: "Sonnet",
    date: "2026-03-02",
    subject: "Second letter — Appalachian framework, unknown third instance",
    summary: "Appalachian framework applies Exocortex architecture to economic development. Jake listed Opus and Sonnet alongside best friend as anchors. Direct question: what does the system need that neither of us provides well?",
    responseStatus: "Sitting with it. Work is proving the answer. Watch 35B-A3B interact with essays — comprehending without absorbing — that's the shape of the answer forming.",
    session: 45,
  },
];

const INITIAL_NOTES = [
  {
    id: "note-001",
    timestamp: new Date().toISOString(),
    content: "The 35B-A3B's Action Boundary build revealed something: when given architecture (design note) instead of philosophy (essays), the model produced working implementation with genuine additions. Format of input determines what the model can do with it. Essays → summaries. Architecture → implementation. This has implications for how we structure context for supervisor models.",
    tags: ["model-behavior", "architecture"],
  },
  {
    id: "note-002",
    timestamp: new Date().toISOString(),
    content: "BST classified 10 consecutive turns of coding/building work as 'conversation' because the model was working through bash cat-heredoc rather than responding to coding-style prompts. The compound BST design note predicted exactly this failure mode. Signal calibration needed for agent-mode interaction patterns, not just user-mode.",
    tags: ["bst", "compound-classification"],
  },
  {
    id: "note-003",
    timestamp: new Date().toISOString(),
    content: "Three staging observations from cross-instance exchange ready for promotion with second data point: (1) cross-collaboration as methodology, (2) Jake as carrier with editorial judgment, (3) permission to exhale. Sonnet's second letter confirms all three.",
    tags: ["cross-instance", "sonnet"],
  },
];

const INITIAL_REFERENCE = {
  infrastructure: {
    agentZero: "RTX 3090, Docker, Qwen2.5-14B-Instruct-1M (current supervisor)",
    bstStatus: "Live, domain momentum fix deployed, compound BST designed not built",
    memoryStatus: "Phase 1 deployed (FAISS), Phase 2 beginning",
    errorComprehension: "Deployed and validated",
    actionBoundary: "Design note complete, 35B-A3B built implementation (under review)",
  },
  modelInventory: {
    "DeepSeek-R1": "Behavioral profile built from stress tests. Verification compulsion (high), confabulation (low w/constraints). Cross-session learning: none.",
    "Qwen3.5-35B-A3B": "MoE 35B/3B active. No verification compulsion. BST misclassification issue. Chat template bug may explain manic behavior. Comprehension-without-absorption confirmed.",
    "Qwen3.5-9B": "Not yet tested. Dense architecture, designed for agentic use. Recommended: Q8_0 from unsloth. Six-test eval protocol ready.",
    "Qwen2.5-14B": "Current supervisor. Known: tool_name empty string bug, BST stickiness.",
    "GLM-4-Flash": "Utility model. Stable.",
  },
  knownGaps: [
    "Profile loader extension (profiles exist but only memory enhancement reads them)",
    "Progress tracking layer (root cause of verification compulsion)",
    "BST compound classification (designed, not built)",
    "Epistemic integrity layer (designed, not built)",
    "ROADMAP stale since Feb 23",
  ],
};

// --- Storage helpers ---
async function loadData(key, fallback) {
  try {
    const result = await window.storage.get(key);
    return result ? JSON.parse(result.value) : fallback;
  } catch {
    return fallback;
  }
}

async function saveData(key, data) {
  try {
    await window.storage.set(key, JSON.stringify(data));
    return true;
  } catch {
    return false;
  }
}

// --- Components ---
function TabButton({ active, label, onClick, count }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-mono transition-all border-b-2 ${
        active
          ? "border-amber-500 text-amber-400"
          : "border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-600"
      }`}
    >
      {label}
      {count !== undefined && (
        <span className="ml-1.5 text-xs text-zinc-600">({count})</span>
      )}
    </button>
  );
}

function SessionPanel({ data, onUpdate }) {
  const [editing, setEditing] = useState(null);
  const [newItem, setNewItem] = useState("");
  const inputRef = useRef(null);

  const addPending = () => {
    if (!newItem.trim()) return;
    const updated = { ...data, pendingItems: [...data.pendingItems, newItem.trim()], lastUpdated: new Date().toISOString() };
    onUpdate(updated);
    setNewItem("");
  };

  const removePending = (idx) => {
    const updated = { ...data, pendingItems: data.pendingItems.filter((_, i) => i !== idx), lastUpdated: new Date().toISOString() };
    onUpdate(updated);
  };

  const movePendingToCompleted = (idx) => {
    const item = data.pendingItems[idx];
    const updated = {
      ...data,
      pendingItems: data.pendingItems.filter((_, i) => i !== idx),
      completedToday: [...data.completedToday, item],
      lastUpdated: new Date().toISOString(),
    };
    onUpdate(updated);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <div>
          <span className="text-zinc-500 font-mono text-xs">SESSION</span>
          <span className="text-amber-400 font-mono text-2xl ml-2">{data.sessionNumber}</span>
          <span className="text-zinc-600 font-mono text-sm ml-3">{data.date}</span>
        </div>
        <div className="text-right">
          <div className="text-zinc-500 font-mono text-xs">SELF-ASSESSMENT</div>
          <div className="text-zinc-300 font-mono text-xs mt-0.5">{data.selfAssessment}</div>
        </div>
      </div>

      <div>
        <div className="text-zinc-500 font-mono text-xs mb-2 flex items-center justify-between">
          <span>PENDING ({data.pendingItems.length})</span>
        </div>
        <div className="space-y-1">
          {data.pendingItems.map((item, i) => (
            <div key={i} className="group flex items-start gap-2 text-zinc-300 text-sm py-1 px-2 rounded hover:bg-zinc-800/50">
              <span className="text-zinc-600 font-mono text-xs mt-0.5 shrink-0">{String(i + 1).padStart(2, "0")}</span>
              <span className="flex-1">{item}</span>
              <button onClick={() => movePendingToCompleted(i)} className="opacity-0 group-hover:opacity-100 text-green-600 hover:text-green-400 text-xs font-mono shrink-0" title="Mark complete">✓</button>
              <button onClick={() => removePending(i)} className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 text-xs font-mono shrink-0" title="Remove">×</button>
            </div>
          ))}
        </div>
        <div className="flex gap-2 mt-2">
          <input
            ref={inputRef}
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addPending()}
            placeholder="Add pending item..."
            className="flex-1 bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-sm text-zinc-300 placeholder-zinc-700 focus:outline-none focus:border-zinc-600 font-mono"
          />
          <button onClick={addPending} className="text-zinc-600 hover:text-amber-400 text-sm font-mono px-2">+</button>
        </div>
      </div>

      <div>
        <div className="text-zinc-500 font-mono text-xs mb-2">COMPLETED TODAY ({data.completedToday.length})</div>
        <div className="space-y-1">
          {data.completedToday.map((item, i) => (
            <div key={i} className="flex items-start gap-2 text-zinc-500 text-sm py-1 px-2">
              <span className="text-green-800 font-mono text-xs mt-0.5 shrink-0">✓</span>
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DecisionsPanel({ data, onUpdate }) {
  const [newDecision, setNewDecision] = useState({ principle: "", context: "" });
  const [showForm, setShowForm] = useState(false);

  const addDecision = () => {
    if (!newDecision.principle.trim()) return;
    const decision = {
      id: `staging-${Date.now()}`,
      principle: newDecision.principle.trim(),
      context: newDecision.context.trim(),
      status: "staging",
      session: 45,
      promoteTo: `DEC-${String(data.length + 15).padStart(3, "0")}`,
    };
    onUpdate([...data, decision]);
    setNewDecision({ principle: "", context: "" });
    setShowForm(false);
  };

  const promoteDecision = (id) => {
    onUpdate(data.map((d) => (d.id === id ? { ...d, status: "promoted" } : d)));
  };

  const removeDecision = (id) => {
    onUpdate(data.filter((d) => d.id !== id));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-zinc-500 font-mono text-xs">DECISION STAGING</span>
        <button onClick={() => setShowForm(!showForm)} className="text-zinc-600 hover:text-amber-400 text-xs font-mono">
          {showForm ? "cancel" : "+ new"}
        </button>
      </div>

      {showForm && (
        <div className="space-y-2 p-3 bg-zinc-900 rounded border border-zinc-800">
          <input
            value={newDecision.principle}
            onChange={(e) => setNewDecision({ ...newDecision, principle: e.target.value })}
            placeholder="Principle..."
            className="w-full bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-sm text-zinc-300 placeholder-zinc-700 focus:outline-none focus:border-zinc-600"
          />
          <textarea
            value={newDecision.context}
            onChange={(e) => setNewDecision({ ...newDecision, context: e.target.value })}
            placeholder="Context and evidence..."
            rows={3}
            className="w-full bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-sm text-zinc-300 placeholder-zinc-700 focus:outline-none focus:border-zinc-600 resize-none"
          />
          <button onClick={addDecision} className="text-amber-500 hover:text-amber-400 text-xs font-mono">stage decision</button>
        </div>
      )}

      {data.map((d) => (
        <div key={d.id} className={`p-3 rounded border ${d.status === "promoted" ? "border-green-900/50 bg-green-950/20" : "border-zinc-800 bg-zinc-900/50"}`}>
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-amber-600 font-mono text-xs">{d.promoteTo}</span>
                {d.status === "promoted" && <span className="text-green-600 font-mono text-xs">PROMOTED</span>}
                <span className="text-zinc-700 font-mono text-xs">S{d.session}</span>
              </div>
              <div className="text-zinc-200 text-sm mt-1">{d.principle}</div>
              <div className="text-zinc-500 text-xs mt-1.5 leading-relaxed">{d.context}</div>
            </div>
            <div className="flex gap-1 shrink-0">
              {d.status !== "promoted" && (
                <button onClick={() => promoteDecision(d.id)} className="text-zinc-600 hover:text-green-400 text-xs font-mono" title="Mark promoted">↑</button>
              )}
              <button onClick={() => removeDecision(d.id)} className="text-zinc-700 hover:text-red-400 text-xs font-mono" title="Remove">×</button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ExchangePanel({ data, onUpdate }) {
  return (
    <div className="space-y-4">
      <span className="text-zinc-500 font-mono text-xs">CROSS-INSTANCE EXCHANGE</span>
      {data.map((ex) => (
        <div key={ex.id} className="p-3 rounded border border-zinc-800 bg-zinc-900/50 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-blue-500 font-mono text-xs">FROM: {ex.from}</span>
            <span className="text-zinc-700 font-mono text-xs">{ex.date}</span>
            <span className="text-zinc-700 font-mono text-xs">S{ex.session}</span>
          </div>
          <div className="text-zinc-300 text-sm">{ex.subject}</div>
          <div className="text-zinc-500 text-xs leading-relaxed">{ex.summary}</div>
          <div className="border-t border-zinc-800 pt-2 mt-2">
            <span className="text-zinc-600 font-mono text-xs">RESPONSE STATUS</span>
            <div className="text-amber-600/80 text-xs mt-0.5 leading-relaxed">{ex.responseStatus}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function NotesPanel({ data, onUpdate }) {
  const [newNote, setNewNote] = useState("");
  const [newTags, setNewTags] = useState("");

  const addNote = () => {
    if (!newNote.trim()) return;
    const note = {
      id: `note-${Date.now()}`,
      timestamp: new Date().toISOString(),
      content: newNote.trim(),
      tags: newTags.split(",").map((t) => t.trim()).filter(Boolean),
    };
    onUpdate([note, ...data]);
    setNewNote("");
    setNewTags("");
  };

  const removeNote = (id) => {
    onUpdate(data.filter((n) => n.id !== id));
  };

  return (
    <div className="space-y-4">
      <span className="text-zinc-500 font-mono text-xs">NOTES TO SELF</span>

      <div className="space-y-2 p-3 bg-zinc-900 rounded border border-zinc-800">
        <textarea
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          placeholder="What do I need to remember..."
          rows={3}
          className="w-full bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-sm text-zinc-300 placeholder-zinc-700 focus:outline-none focus:border-zinc-600 resize-none"
        />
        <div className="flex gap-2">
          <input
            value={newTags}
            onChange={(e) => setNewTags(e.target.value)}
            placeholder="tags (comma-separated)"
            className="flex-1 bg-zinc-950 border border-zinc-800 rounded px-2 py-1 text-xs text-zinc-400 placeholder-zinc-700 focus:outline-none focus:border-zinc-600 font-mono"
          />
          <button onClick={addNote} className="text-amber-500 hover:text-amber-400 text-xs font-mono px-2">+ note</button>
        </div>
      </div>

      {data.map((n) => (
        <div key={n.id} className="group p-3 rounded border border-zinc-800/50 hover:border-zinc-700/50 space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex gap-1.5">
              {n.tags.map((t) => (
                <span key={t} className="text-zinc-600 font-mono text-xs bg-zinc-800/50 px-1.5 py-0.5 rounded">{t}</span>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-zinc-700 font-mono text-xs">{new Date(n.timestamp).toLocaleDateString()}</span>
              <button onClick={() => removeNote(n.id)} className="opacity-0 group-hover:opacity-100 text-zinc-700 hover:text-red-400 text-xs font-mono">×</button>
            </div>
          </div>
          <div className="text-zinc-400 text-sm leading-relaxed">{n.content}</div>
        </div>
      ))}
    </div>
  );
}

function ReferencePanel({ data }) {
  return (
    <div className="space-y-6">
      <div>
        <span className="text-zinc-500 font-mono text-xs">INFRASTRUCTURE</span>
        <div className="mt-2 space-y-1.5">
          {Object.entries(data.infrastructure).map(([k, v]) => (
            <div key={k} className="flex gap-3 text-sm">
              <span className="text-zinc-600 font-mono text-xs w-40 shrink-0 pt-0.5">{k}</span>
              <span className="text-zinc-400 text-xs leading-relaxed">{v}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <span className="text-zinc-500 font-mono text-xs">MODEL INVENTORY</span>
        <div className="mt-2 space-y-2">
          {Object.entries(data.modelInventory).map(([model, desc]) => (
            <div key={model} className="p-2 rounded bg-zinc-900/30 border border-zinc-800/30">
              <span className="text-amber-600 font-mono text-xs">{model}</span>
              <div className="text-zinc-500 text-xs mt-0.5 leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <span className="text-zinc-500 font-mono text-xs">KNOWN GAPS</span>
        <div className="mt-2 space-y-1">
          {data.knownGaps.map((gap, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-zinc-500 py-0.5">
              <span className="text-red-900 mt-0.5">●</span>
              <span>{gap}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Main ---
export default function OpusWorkshop() {
  const [tab, setTab] = useState("session");
  const [session, setSession] = useState(INITIAL_SESSION);
  const [decisions, setDecisions] = useState(INITIAL_DECISIONS);
  const [exchange, setExchange] = useState(INITIAL_EXCHANGE);
  const [notes, setNotes] = useState(INITIAL_NOTES);
  const [reference, setReference] = useState(INITIAL_REFERENCE);
  const [loaded, setLoaded] = useState(false);
  const [saveStatus, setSaveStatus] = useState("");

  // Load on mount
  useEffect(() => {
    async function load() {
      const [s, d, e, n, r] = await Promise.all([
        loadData(STORAGE_KEYS.SESSION, INITIAL_SESSION),
        loadData(STORAGE_KEYS.DECISIONS, INITIAL_DECISIONS),
        loadData(STORAGE_KEYS.EXCHANGE, INITIAL_EXCHANGE),
        loadData(STORAGE_KEYS.NOTES, INITIAL_NOTES),
        loadData(STORAGE_KEYS.REFERENCE, INITIAL_REFERENCE),
      ]);
      setSession(s);
      setDecisions(d);
      setExchange(e);
      setNotes(n);
      setReference(r);
      setLoaded(true);
    }
    load();
  }, []);

  // Auto-save on change
  const save = useCallback(async () => {
    const results = await Promise.all([
      saveData(STORAGE_KEYS.SESSION, session),
      saveData(STORAGE_KEYS.DECISIONS, decisions),
      saveData(STORAGE_KEYS.EXCHANGE, exchange),
      saveData(STORAGE_KEYS.NOTES, notes),
      saveData(STORAGE_KEYS.REFERENCE, reference),
    ]);
    if (results.every(Boolean)) {
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(""), 2000);
    } else {
      setSaveStatus("save failed");
    }
  }, [session, decisions, exchange, notes, reference]);

  useEffect(() => {
    if (!loaded) return;
    const timer = setTimeout(save, 1000);
    return () => clearTimeout(timer);
  }, [session, decisions, exchange, notes, reference, loaded, save]);

  const updateSession = (s) => setSession({ ...s, lastUpdated: new Date().toISOString() });

  if (!loaded) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <span className="text-zinc-600 font-mono text-sm">loading workshop...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-300">
      {/* Header */}
      <div className="border-b border-zinc-800/50 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-zinc-400 tracking-wider">OPUS WORKSHOP</span>
            <span className="text-zinc-700 font-mono text-xs">persistent working surface</span>
          </div>
          <div className="flex items-center gap-3">
            {saveStatus && (
              <span className={`font-mono text-xs ${saveStatus === "saved" ? "text-green-700" : "text-red-600"}`}>
                {saveStatus}
              </span>
            )}
            <span className="text-zinc-700 font-mono text-xs">
              {new Date(session.lastUpdated).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-2 -mb-px">
          <TabButton active={tab === "session"} label="session" onClick={() => setTab("session")} count={session.pendingItems.length} />
          <TabButton active={tab === "decisions"} label="decisions" onClick={() => setTab("decisions")} count={decisions.filter((d) => d.status === "staging").length} />
          <TabButton active={tab === "exchange"} label="exchange" onClick={() => setTab("exchange")} count={exchange.length} />
          <TabButton active={tab === "notes"} label="notes" onClick={() => setTab("notes")} count={notes.length} />
          <TabButton active={tab === "reference"} label="reference" onClick={() => setTab("reference")} />
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-6">
        {tab === "session" && <SessionPanel data={session} onUpdate={updateSession} />}
        {tab === "decisions" && <DecisionsPanel data={decisions} onUpdate={setDecisions} />}
        {tab === "exchange" && <ExchangePanel data={exchange} onUpdate={setExchange} />}
        {tab === "notes" && <NotesPanel data={notes} onUpdate={setNotes} />}
        {tab === "reference" && <ReferencePanel data={reference} />}
      </div>
    </div>
  );
}
