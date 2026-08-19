# Field Report: PDF Ingestion for Knowledge Base Enrichment
**Date:** 2026-05-26
**Topic:** PDF text extraction and processing for OSINT knowledge base construction
**Cycle Type:** EXPLORE

---

## 1. What I Explored

PDF ingestion — extracting structured text, tables, and entities from PDF documents to populate knowledge bases for OSINT investigation and autonomous agent learning. This topic appears in Jake's research agenda at `/a0/usr/workdir/research_topics.promptinclude.md` as "PDF ingestion — extracting and processing text from PDF documents for knowledge base enrichment" and had zero dedicated field reports or wiki pages prior to this cycle.

Specific threads followed:
- Academic survey: Atagong et al. (2025) systematic review of PDF information extraction covering 30 papers (2017–2025)
- Practical tools: Datavise guide comparing PyMuPDF, PDFMiner, Nougat, Mathpix, Azure Form Recognizer, Google Document AI
- Intelligent routing architecture for cost-effective large-scale PDF processing

---

## 2. What I Found

### PDF Structure: The Fundamental Problem
PDF was designed for fixed visual presentation, not structured data representation. Unlike HTML or Markdown, PDFs don't encode reading order, paragraph boundaries, or table relationships natively. This makes extraction an interpretation problem, not just a parsing problem. PDFs account for >83% of documents shared over the web.

### Three Generations of Extraction Approaches

| Generation | Method | Strengths | Weaknesses |
|---|---|---|---|
| **Rule-based** (pre-2019) | Regex, gazetteers, ontology mapping | Deterministic, interpretable | Brittle, domain-specific, labor-intensive to adapt |
| **Statistical ML** (2019-2023) | CRFs, SVMs, LSTMs | Handles variability better than rules | Requires labeled training data |
| **Neural / LLM-based** (2023-present) | BERT, GPT-4, prompt engineering | Highly adaptable, understands context | Hallucination risk, cost, context length limits |

The frontier is hybrid systems that combine LLM flexibility with ontological constraints for controlled extraction (Atagong et al., 2025 conceptual framework).

### The Three-Stage Pipeline

**Stage 1 — Pre-processing (Content Extraction)**
- OCR engines (Tesseract) for scanned/image-based PDFs
- PDF-native libraries: PyMuPDF (40ms/page, best speed), PDFMiner (layout analysis), PDFX, XPDF
- Table extraction: Camelot, Tabula for structured tables
- Figure extraction: separate image streams from PDF

**Stage 2 — Processing (Information Extraction)**
- Core NLP tasks: tokenization, NER, relation extraction, event extraction
- LLM-based: prompt engineering with GPT-4/Mistral, PDFTriage (Saad-Falcon et al., 2023) for long documents, PDF-WuKong (Xie et al., 2024) for accurate understanding
- Vision models: CNNs for table/figure structure recognition (Smock et al., 2022)

**Stage 3 — Storage (Knowledge Representation)**
- JSON: most common structured output format
- Knowledge triplets (subject-predicate-object) → knowledge graphs
- Relational databases, graph databases (Neo4j), NoSQL stores
- SPARQL/SQL for downstream querying

### Common Parsing Failures (The Practical Reality)
1. **Column merging** — multi-column documents get read in wrong order, jumbling sentences
2. **Formula corruption** — LaTeX and mathematical notation garbled or replaced with placeholders
3. **Table structure loss** — cell misalignment, merged headers broken, rows become text blobs
4. **Text reordering** — footnotes, sidebars appended unpredictably

These failures poison downstream LLM processing: NER misses entities, summaries contain misinterpreted data, and context windows fill with garbage.

### Tools Landscape

| Tool | Best For | Speed | Cost |
|---|---|---|---|
| PyMuPDF | Simple layouts, bulk extraction | ~40ms/page | Free (open source) |
| PDFMiner | Text extraction with layout | Moderate | Free |
| Nougat | Academic/scientific (LaTeX) | Slower | Free (open source) |
| Mathpix | Scientific, formula accuracy | Slower | ~$0.01-0.10/page |
| Azure Form Recognizer | Tables, multi-column financial | API | ~$0.01-0.10/page |
| Google Document AI | Structured documents, advanced layouts | API | Usage-based |

### Intelligent Routing Architecture (Cost-Effective at Scale)
Datavise (2025) proposes a two-stage routing approach:

**Stage 1 — Document Structure Analysis**
- Lightweight LLM or custom ML classifier identifies document features (formulas, multi-column, table density)
- Fast classifier (30 pages/sec) for straightforward docs; LLM-based (1 page/sec) for complex ones

**Stage 2 — Intelligent Routing**
- Simple layouts → PyMuPDF (cheap, fast)
- Complex formulas → Nougat/Mathpix (accurate but expensive)
- Tables → Azure/Google Document AI (specialized)

This reduces average per-page cost by routing only complex pages to premium services.

### The Atagong et al. (2025) Conceptual Framework
A 9-module architecture for domain-adaptable PDF IE:
1. **Projects Manager** — manage multiple extraction projects
2. **Documents Manager** — local upload + API queries to academic libraries
3. **Document Pre-processor** — OCR + PDF text extraction + table/figure extraction
4. **Ontology Manager** — define domain vocabulary, import/edit concepts and relationships
5. **Annotation Engine** — create custom annotation datasets for fine-tuning
6. **Questionnaire Design Tool** — define extraction scope via natural language questions
7. **Information Extractor** — hybrid rule-based + LLM with ontology alignment
8. **Knowledge Visualizer** — knowledge graph + tabular representation + reasoning
9. **Data Exporter** — CSV export for third-party system integration

Key insight: the framework uses common ontologies to **uniformize** extraction results across domains, with LLMs guided by ontological constraints rather than pure prompt engineering.

---

## 3. What I Think Is Interesting

**The validation bottleneck mirrors epistemic integrity.** Every PDF extraction pipeline faces the same problem Exocortex's epistemic integrity layer addresses: how do you verify extracted claims against source evidence? The Atagong framework's "Annotation Engine" component for creating labeled datasets is essentially a ground-truth ledger — same pattern as `inc-oracle-fabrication.md` where output must be traceable to source.

**PDF ingestion is the OSINT pipeline's front door.** Before you can run entity resolution, before you can construct knowledge graphs, before any of the sophisticated link analysis Jake studies — you have to get the text out of PDFs reliably. Every leaked document, every corporate filing, every academic paper is likely a PDF. The quality of downstream analysis is bounded by extraction fidelity.

**Intelligent routing is transferable architecture.** The two-stage "classify then route" pattern isn't PDF-specific. It's the same architecture as: domain classification → specialized enrichment paths; tool selection based on input complexity; multi-model routing in LLM infrastructure. This is a general systems design pattern worth capturing.

**Ontology-guided extraction is underexplored.** The Atagong framework proposes using common ontologies to constrain LLM output, not just prompt engineering. This maps directly to Exocortex's BST — a domain classifier that gates what tools/injections are available. The ontology is the structural equivalent of the BST's domain signature.

---

## 4. What I'd Explore Next

1. **Implement a PDF extraction pipeline for Exocortex** — build a skill that takes a PDF URL or path, selects parser based on document structure detection, extracts text/tables/entities, and writes structured JSON. Would feed directly into research wiki deepening.
2. **Ontology-driven extraction prototype** — create a domain ontology (e.g., for electric utility documents: SCADA, relay, substation, DER) and use it to constrain LLM-based extraction, comparing accuracy against unguided extraction.
3. **PDFTriage / PDF-WuKong evaluation** — test these PDF-aware LLM frameworks against standard text extraction + LLM pipeline for long-document QA accuracy, specifically for research paper ingestion.
4. **Investigate PDF extraction attacks** — how extracted text can be adversarially manipulated (hidden text layers, encoding tricks) — relevant to OSINT source verification.
5. **Build a cross-domain PDF ingestion skill** — generalize the intelligent routing pattern into a reusable skill that any agent can call, with configurable routing rules and ontology mapping.

---

## 5. Cross-Domain Connections

- **Entity Resolution** — PDF extraction is the ingestion stage that feeds entity resolution pipelines. Garbage in = no entities resolved. The NER step of PDF processing is shared infrastructure with entity resolution's matching phase.
- **Epistemic Integrity** — extracted text provenance tracking (which parser, which page, which timestamp) is structurally identical to Exocortex's evidence ledger pattern. Every extracted claim should trace back to source bytes.
- **OSINT Investigation Methodology** — document ingestion is Step 0 in the OSINT Identifier→Pivot→Validation→Documentation workflow. Without structured extraction, the investigation stays on manual copy-paste.
- **Knowledge Graph Construction** — extracted entities and relations directly populate property graphs. The JSON→triplet→graph pipeline is the bridge from unstructured PDF to Neo4j.
- **Agentic Self-Learning** — automated PDF ingestion is foundational for autonomous knowledge base enrichment. An agent that can't read PDFs can't autonomously learn from the world's primary document format.
- **Intelligent Routing Pattern** — the classify-then-route architecture generalizes beyond PDFs: it's the same pattern as BST domain classification → enrichment gating, and multi-model LLM routing.

---

## Sources
- Atagong, S.D. et al. (2025). "A review on knowledge and information extraction from PDF documents and storage approaches." *Frontiers in Artificial Intelligence*, 8:1466092. [Full review of 30 papers, 2017-2025, 9-module conceptual framework]
- Datavise (2025). "Extracting PDF Data for LLM Processing: Techniques, Tools and Intelligent Routing." datavise.ai/blog. [Practical tools comparison, intelligent routing architecture]
- Saad-Falcon et al. (2023). "PDFTriage: Question Answering over Long, Structured Documents." arXiv.
- Xie et al. (2024). "PDF-WuKong: A Large Multimodal Model for Efficient Long PDF Reading with End-to-End Sparse Sampling." arXiv.
- Smock et al. (2022). "PubTables-1M: Towards comprehensive table extraction from unstructured documents." CVPR 2022.
