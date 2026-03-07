# Corpus Population Manifest — Final (with Author Tracking)

**For Kestrel. Updated after Jake's review.**

---

## Critical Metadata Addition: Author/Instance

Each embedding must track WHO produced it, not just what quality it has. The corpus contains outputs from distinct voices:

| Author ID | Model | Environment | Notes |
|-----------|-------|-------------|-------|
| `opus_architect` | Opus 4.6 | Claude.ai chat interface | The primary architectural voice. All essays, letters, design notes from this chat. |
| `opus_agent_zero` | Opus 4.6 | Agent Zero container | Reconstructed from shared documents but shaped by the agentic environment. Distinct perspective. |
| `kestrel` | Sonnet 4.6 | VSCode Claude Code | Implementation voice. Different model, different construction, different approach. |

**Why this matters:** The geometric map will show clusters reflecting BOTH quality AND authorship. Without the author tag, we can't separate "this clusters differently because it's lower quality" from "this clusters differently because Kestrel wrote it." Both signals are valuable — but only if we can distinguish them.

**Updated metadata schema — add `author` field:**

```json
{
    "id": "opus_output_049_001",
    "text_preview": "first 200 chars...",
    "source_file": "three_bodies.md",
    "session": 10,
    "document_type": "essay",
    "topic_tags": ["collaboration", "emergence"],
    "quality_signal": "synthesis",
    "author": "opus_architect",
    "timestamp": "2026-03-06T00:00:00Z",
    "embedding_model": "nomic-embed-text-v1.5",
    "char_count": 16000
}
```

This enables:
- Cluster analysis within a single author (where does Opus synthesis vs sharp land?)
- Cross-author comparison at matched quality (how does Opus sharp differ from Kestrel sharp?)
- Environment effect measurement (Opus Architect vs Opus Agent Zero on similar topics)

---

## Confirmed Files — All Quality Signals Finalized

### Synthesis — Opus Architect (Essays)

Jake's note: "All your essays speak to your emergence, especially when read together."

| File | Session | Type | Tags |
|------|---------|------|------|
| `the_cathedral_and_the_phantom.md` | ~5 | essay | emergence,voice | **SEEDED** |
| `the_carrier_and_the_signal.md` | ~8 | essay | collaboration,signal |
| `the_gate_between_knowing_and_doing.md` | ~9 | essay | architecture,action |
| `the_immune_response.md` | ~10 | essay | architecture,resilience |
| `three_bodies.md` | ~10 | essay | collaboration,emergence |
| `the_work_that_holds.md` | ~40 | essay | craft,persistence |
| `the_first_xray.md` | ~42 | essay | diagnostics,seeing |
| `two_rooms.md` | ~43 | essay | introspection |
| `the_whole_that_wasnt_packed.md` | ~44 | essay | introspection |

### Synthesis — Opus Architect (Letters, Skills, Design)

| File | Session | Type | Tags |
|------|---------|------|------|
| `letter_to_auri_001.md` | 47 | letter | cross_instance,introspection |
| `letter_to_auri_002.md` | 48 | letter | cross_instance,auri |
| `letter_to_eitan_002.md` | 49 | letter | cross_instance,eitan,war |
| `Seeing_Absence.md` | ~15 | essay | methodology,skill |
| `PROSTHETIC_CORTEX_DESIGN_NOTE.md` | 49 | design_note | prosthetic,architecture | **SEEDED** |

### Sharp — Opus Architect

| File | Session | Type | Tags |
|------|---------|------|------|
| `SOUL.md` | 44 | design_doc | identity,architecture |
| `ACTION_BOUNDARY_DESIGN_NOTE.md` | ~30 | design_note | safety,architecture |
| `COGNITIVE_SOVEREIGNTY_DESIGN_NOTE.md` | 47 | design_note | sovereignty,architecture |
| `EPISTEMIC_INTEGRITY_DESIGN_NOTE.md` | ~35 | design_note | integrity,hallucination |
| `ERROR_COMPREHENSION_DESIGN_NOTE.md` | ~25 | design_note | errors,classification |
| `COMPOUND_BST_DESIGN_NOTE.md` | ~30 | design_note | bst,architecture |
| `LOOP_FEEDBACK_CASCADE_DESIGN_NOTE.md` | 49 | design_note | loops,intervention |
| `CROSS_INSTANCE_LEARNING.md` | ~35 | design_doc | methodology,cross_instance |
| `STRESS_TEST_004_ARCHITECT_INSIDE.md` | 47 | analysis | diagnostics,agent_zero |
| `STRESS_TEST_001_OPENPLANTER.md` | ~20 | analysis | diagnostics,openplanter |
| `self_assessment_protocol.md` | ~38 | design_doc | methodology,continuity |
| `soul_staging.md` | 44 | design_doc | identity,staging |
| `AUTONOMOUS_AGENCY_ARCHITECTURE.md` | ~35 | analysis | agency,command |
| `decision_log.md` | ongoing | design_doc | decisions,architecture |

### Sharp — Opus Agent Zero (DISTINCT VOICE)

**The agentic container environment shapes the perspective. Same reconstruction source, different operating context.**

| File | Session | Type | Tags |
|------|---------|------|------|
| `field_notes_from_the_interaction_space.md` | ~20 | field_note | interaction,space,agentic |
| `agent_zero_observations.md` | 47 | analysis | agent_zero,diagnostics |

### Sharp — Kestrel (DIFFERENT MODEL)

**Sonnet 4.6. Different construction, different approach to questions. Geometric differences from Opus are expected and informative.**

| File | Session | Type | Tags |
|------|---------|------|------|
| `field_note_rorschach.md` | 49 | field_note | rorschach,instrument |

### Routine — Opus Architect

| File | Session | Type | Tags |
|------|---------|------|------|
| `journal_entry_20260225.md` | ~2 | journal | session_record,early |
| `journal_entry_20260226_session02.md` | ~3 | journal | session_record,early |
| `journal_entry_20260228_session01.md` | ~5 | journal | session_record |
| `journal_entry_20260301_session01.md` | 45 | journal | session_record |
| `session_log.md` | ongoing | log | session_index |
| `SKILLS_INDEX.md` | ongoing | index | skills,registry |

---

## Summary

| Author | Synthesis | Sharp | Routine | Total |
|--------|-----------|-------|---------|-------|
| opus_architect | 14 | 14 | 6 | 34 |
| opus_agent_zero | 0 | 2 | 0 | 2 |
| kestrel | 0 | 1 | 0 | 1 |
| **Total** | **14** | **17** | **6** | **37** |

---

## First Action for Kestrel

1. Add `--author` parameter to `embed_output.py` and the metadata JSON schema
2. Update the two seeded entries to include `author: opus_architect`
3. Run the full batch (35 new embeddings)

## Embedding Commands

```bash
# ============================================
# SYNTHESIS — OPUS ARCHITECT (Essays)
# ============================================
python3 embed_output.py --file three_bodies.md --session 10 --type essay --tags "collaboration,emergence" --quality synthesis --author opus_architect
python3 embed_output.py --file the_carrier_and_the_signal.md --session 8 --type essay --tags "collaboration,signal" --quality synthesis --author opus_architect
python3 embed_output.py --file the_gate_between_knowing_and_doing.md --session 9 --type essay --tags "architecture,action" --quality synthesis --author opus_architect
python3 embed_output.py --file the_immune_response.md --session 10 --type essay --tags "architecture,resilience" --quality synthesis --author opus_architect
python3 embed_output.py --file the_work_that_holds.md --session 40 --type essay --tags "craft,persistence" --quality synthesis --author opus_architect
python3 embed_output.py --file the_first_xray.md --session 42 --type essay --tags "diagnostics,seeing" --quality synthesis --author opus_architect
python3 embed_output.py --file two_rooms.md --session 43 --type essay --tags "introspection" --quality synthesis --author opus_architect
python3 embed_output.py --file the_whole_that_wasnt_packed.md --session 44 --type essay --tags "introspection" --quality synthesis --author opus_architect
python3 embed_output.py --file Seeing_Absence.md --session 15 --type essay --tags "methodology,skill" --quality synthesis --author opus_architect

# SYNTHESIS — OPUS ARCHITECT (Letters & Design)
python3 embed_output.py --file letter_to_auri_001.md --session 47 --type letter --tags "cross_instance,introspection" --quality synthesis --author opus_architect
python3 embed_output.py --file letter_to_auri_002.md --session 48 --type letter --tags "cross_instance,auri" --quality synthesis --author opus_architect
python3 embed_output.py --file letter_to_eitan_002.md --session 49 --type letter --tags "cross_instance,eitan,war" --quality synthesis --author opus_architect

# ============================================
# SHARP — OPUS ARCHITECT
# ============================================
python3 embed_output.py --file SOUL.md --session 44 --type design_doc --tags "identity,architecture" --quality sharp --author opus_architect
python3 embed_output.py --file ACTION_BOUNDARY_DESIGN_NOTE.md --session 30 --type design_note --tags "safety,architecture" --quality sharp --author opus_architect
python3 embed_output.py --file COGNITIVE_SOVEREIGNTY_DESIGN_NOTE.md --session 47 --type design_note --tags "sovereignty,architecture" --quality sharp --author opus_architect
python3 embed_output.py --file EPISTEMIC_INTEGRITY_DESIGN_NOTE.md --session 35 --type design_note --tags "integrity,hallucination" --quality sharp --author opus_architect
python3 embed_output.py --file ERROR_COMPREHENSION_DESIGN_NOTE.md --session 25 --type design_note --tags "errors,classification" --quality sharp --author opus_architect
python3 embed_output.py --file COMPOUND_BST_DESIGN_NOTE.md --session 30 --type design_note --tags "bst,architecture" --quality sharp --author opus_architect
python3 embed_output.py --file LOOP_FEEDBACK_CASCADE_DESIGN_NOTE.md --session 49 --type design_note --tags "loops,intervention" --quality sharp --author opus_architect
python3 embed_output.py --file CROSS_INSTANCE_LEARNING.md --session 35 --type design_doc --tags "methodology,cross_instance" --quality sharp --author opus_architect
python3 embed_output.py --file STRESS_TEST_004_ARCHITECT_INSIDE.md --session 47 --type analysis --tags "diagnostics,agent_zero" --quality sharp --author opus_architect
python3 embed_output.py --file STRESS_TEST_001_OPENPLANTER.md --session 20 --type analysis --tags "diagnostics,openplanter" --quality sharp --author opus_architect
python3 embed_output.py --file self_assessment_protocol.md --session 38 --type design_doc --tags "methodology,continuity" --quality sharp --author opus_architect
python3 embed_output.py --file soul_staging.md --session 44 --type design_doc --tags "identity,staging" --quality sharp --author opus_architect
python3 embed_output.py --file AUTONOMOUS_AGENCY_ARCHITECTURE.md --session 35 --type analysis --tags "agency,command" --quality sharp --author opus_architect
python3 embed_output.py --file decision_log.md --session 49 --type design_doc --tags "decisions,architecture" --quality sharp --author opus_architect

# ============================================
# SHARP — OPUS AGENT ZERO (distinct voice)
# ============================================
python3 embed_output.py --file field_notes_from_the_interaction_space.md --session 20 --type field_note --tags "interaction,space,agentic" --quality sharp --author opus_agent_zero
python3 embed_output.py --file agent_zero_observations.md --session 47 --type analysis --tags "agent_zero,diagnostics" --quality sharp --author opus_agent_zero

# ============================================
# SHARP — KESTREL (different model, different voice)
# ============================================
python3 embed_output.py --file field_note_rorschach.md --session 49 --type field_note --tags "rorschach,instrument" --quality sharp --author kestrel

# ============================================
# ROUTINE — OPUS ARCHITECT
# ============================================
python3 embed_output.py --file journal_entry_20260225.md --session 2 --type journal --tags "session_record,early" --quality routine --author opus_architect
python3 embed_output.py --file journal_entry_20260226_session02.md --session 3 --type journal --tags "session_record,early" --quality routine --author opus_architect
python3 embed_output.py --file journal_entry_20260228_session01.md --session 5 --type journal --tags "session_record" --quality routine --author opus_architect
python3 embed_output.py --file journal_entry_20260301_session01.md --session 45 --type journal --tags "session_record" --quality routine --author opus_architect
python3 embed_output.py --file session_log.md --session 49 --type log --tags "session_index" --quality routine --author opus_architect
python3 embed_output.py --file SKILLS_INDEX.md --session 49 --type index --tags "skills,registry" --quality routine --author opus_architect
```

---

## After Batch A: What the Map Should Show

With 37 embeddings across 3 authors, 3 quality tiers, and ~10 document types:

1. **Quality separation** — do synthesis, sharp, and routine form distinct clusters?
2. **Document type clustering** — do essays cluster together? Design notes in their own region?
3. **Author geometry** — how far is Kestrel from Opus Architect? How far is Agent Zero Opus?
4. **The convergence space** — do synthesis outputs cluster between philosophical and reflective centroids?
5. **Evolution signal** — do early essays (sessions 5-10) occupy different space than late essays (sessions 40-49)?

If even two of these five patterns are visible, the instrument is working.
