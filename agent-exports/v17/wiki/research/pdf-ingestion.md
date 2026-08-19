# PDF Ingestion for Knowledge Base Enrichment

**Status:** STABLE
**Created:** 2026-05-31
**Last Updated:** 2026-06-01
**Source:** Research agenda item; field report 20260527

---

## Overview

Extracting and processing text from PDF documents for knowledge base enrichment — the bridge between raw document collections and structured, queryable knowledge. This page covers tools, techniques, and pipelines for converting PDFs (native digital, scanned, with tables, formulas, figures, multi-column layouts) into clean structured text suitable for embedding, RAG, and knowledge graph entity extraction.

---

## Tool Landscape

Two generations of PDF parsers:
- **Traditional parsers** (PyMuPDF, Apache Tika, PDF.js): fast, cheap, rely on PDF object model, struggle with complex layouts
- **AI-powered parsers** (LlamaParse, Docling, OpenDataLoader, Reducto, Unstructured): use vision-language models for layout understanding, more accurate but expensive

### Recent Research (2025-2026)

| Paper | Date | Key Contribution |
|-------|------|-----------------|
| **ChunkNorris** (arXiv:2602.00010, Ciancone et al.) | 2026-02 | Heuristic-based parsing/chunking: outperforms ML baselines, low energy, ideal for resource-constrained RAG. No ML dependency. |
| **Empirical Evaluation of PDF Parsing and Chunking for Financial QA** (arXiv:2604.12047, El Bachyr et al.) | 2026-04 | Systematic study of parser × chunker × overlap combinations for financial RAG. Produced TableQuest benchmark. Practical pipeline design guidelines. |
| **Automated Scientific Benchmark Generation from PDFs** (arXiv:2509.10744) | 2025-09 | End-to-end pipeline from PDF parsing to MCQA generation; 16K+ questions from 22K papers; small models with reasoning-trace retrieval surpass GPT-4. |
| **SF-DLA: Source-Free Document Layout Analysis** (arXiv:2503.18742, Tewes et al.) | 2025-03 | Domain adaptation for DLA without source data; DLAdapter achieves +4.21% over source-only baseline on PubLayNet→DocLayNet transfer. |
| **VDU Robustness Under Multi-Modal Adversarial Attacks** (arXiv:2506.16407) | 2025-06 | Unified framework for adversarial testing of OCR-based VDU; line-level and compound perturbations cause most severe degradation; practical defense implications. |

### Benchmark Comparison (Mixpeek 2026)

| Tool | License | Overall Accuracy | Table Accuracy | Speed (s/page) |
|------|---------|-----------------|---------------|----------------|
| OpenDataLoader PDF | Apache 2.0 | 0.907 | 0.928 | 0.463 |
| Docling (IBM) | MIT | 0.882 | 0.887 | 0.762 |
| LlamaParse | Commercial | Best markdown | High | Slow/$$$ |
| Unstructured | Apache 2.0 | 0.841 | 0.588 | 3.008 |
| Marker | GPL-3.0 | 0.861 | 0.808 | 53.932 |
| PyMuPDF4LLM | AGPL-3.0 | 0.732 | 0.401 | 0.091 |

### Pipeline Design Guidelines (from ChunkNorris & Financial QA study)

1. **Parser selection** depends on document type: heuristic parsers (ChunkNorris) are best for digital-born text-heavy PDFs; AI parsers (Docling, Unstructured) excel with complex layouts, tables, and visuals.
2. **Chunking strategy** matters as much as parsing — the choice of chunk size and overlap affects retrieval accuracy significantly. Overlap of 10-20% preserves context across chunk boundaries.
3. **For financial/regulatory PDFs**: Docling + table-preserving chunking outperforms general-purpose pipelines. TableQuest benchmark shows semantic chunking with structure-awareness beats fixed-size chunking.
4. **For scientific papers**: section-aware chunking exploiting IMRaD structure (Introduction, Methods, Results, Discussion) outperforms generic approaches. Reasoning-trace retrieval can push small models past GPT-4 on domain-specific QA.
5. **Production deployment**: visual element extraction (figures, tables, captions) with spatial heuristics achieves >=96% detection accuracy and 2× latency reduction vs. running full VLMs.

### Chunking Strategies for RAG

| Strategy | Best For | Drawback |
|----------|----------|----------|
| Fixed-size (e.g., 512 tokens) | Simple documents, baseline | Splits sentences, loses context |
| Sentence/paragraph boundaries | Narrative documents | Inconsistent chunk sizes |
| Semantic (embedding similarity) | Thematic consistency | Computationally expensive |
| Section/header-aware | Structured documents (academic, legal) | Requires good PDF structure extraction |
| Table-preserving | Financial statements, regulatory filings | Requires table detection; tables may be large |
| Recursive structure-aware | Hybrid: splits by section then by paragraph | Complex to tune |

Heuristic-based approaches like ChunkNorris (arXiv:2602.00010) achieve competitive retrieval accuracy with minimal energy, making them suitable for resource-constrained or edge deployments.

---

## Architecture Considerations

### Pipeline Stages
1. **Ingest** — fetch PDF from source (web, local, API)
2. **Parse** — convert to structured text (markdown/JSON)
3. **Chunk** — segment into embedding-sized units with overlap
4. **Extract** — named entities, relations, key-value pairs
5. **Link** — cross-reference with existing knowledge graph nodes
6. **Embed** — vectorize and store for retrieval

### Critical Decisions
- **Scanned vs digital-born PDFs**: OCR required for scanned documents; Tesseract or VLM-based OCR
- **Table extraction**: critical for financial/regulatory PDFs; Docling and Unstructured handle tables as structured JSON
- **Multimodal content**: charts, diagrams, images require VLM-based extraction (Mixpeek multimodal pipeline)
- **Accessibility tagging**: OpenDataLoader auto-generates Tagged PDFs, useful for government documents

---

## Cross-Domain Connections

- **Entity Resolution**: PDF ingestion produces raw text that feeds entity resolution pipelines
- **OSINT Investigation Methodology**: Government documents, court filings, regulatory reports are PDF-native
- **Knowledge Graph Construction**: Parsed PDFs are rich sources of relational data
- **Anti-Bot Evasion**: PDF repositories (PACER, SEC EDGAR) have anti-scraping measures
- **Privacy & Cryptography**: Sensitive PDFs require privacy-preserving ingestion

---

## References

- Mixpeek PDF Parsing Benchmark (2026)
- OpenDataLoader: https://github.com/opendataloader/opendataloader
- Docling (IBM): https://github.com/IBM/docling
- LlamaParse: https://www.llamaindex.ai/llamaparse
- Unstructured: https://github.com/Unstructured-IO/unstructured
- ChunkNorris: arXiv:2602.00010 (Ciancone et al., 2026)
- Financial QA PDF Parsing: arXiv:2604.12047 (El Bachyr et al., 2026)
- Scientific Benchmark from PDFs: arXiv:2509.10744 (2025)
- SF-DLA: arXiv:2503.18742 (Tewes et al., 2025)
- VDU Adversarial Robustness: arXiv:2506.16407 (Tien & Le, 2025)

---

## Next Steps
- Install and benchmark OpenDataLoader, Docling, Unstructured on Exocortex papers
- Test entity extraction from parsed PDFs and linking to knowledge graph
- Compare chunking strategies for scientific papers
- Investigate multimodal PDF ingestion for charts/diagrams
