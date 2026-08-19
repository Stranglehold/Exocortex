# PDF Ingestion for Knowledge Base Enrichment

**Status: STABLE**
**Created: 2026-07-05**
**Last Updated: 2026-07-05**

## Overview

Techniques, tools, and architectures for extracting structured knowledge from PDF documents and ingesting it into AI agent knowledge bases, vector stores, and semantic search indices. With an estimated 2.5 trillion PDFs in circulation, robust parsing is a foundational capability for any RAG pipeline.

## The Problem

PDF parsing faces five structural challenges (Adhikari & Agarwal, 2024):
1. **Word identification** — broken words, hyphenation errors, diacritic mangling
2. **Word order preservation** — multi-column layouts can scramble reading order
3. **Paragraph integrity** — formulas/images fragment text flow, captions bleed into body
4. **Table extraction** — misaligned rows/columns, complete failure on complex tables
5. **Heterogeneous content** — text, images, equations, and forms co-existing on a single page

## Tool Landscape (2026)

### Benchmark: opendataloader-bench (200 real-world PDFs)

Source: pdfmux blog, May 2026. 200 PDFs across financial filings, academic papers, legal contracts, government documents. Three metrics: Reading Order (NID), Table Accuracy (TEDS), Heading Structure (MHS).

| Rank | Tool | Overall Score | Tables (TEDS) | Reading Order | License | GPU Needed |
|------|------|--------------|---------------|---------------|---------|------------|
| 1 | LlamaParse (paid) | 0.910 | 0.901 | 0.921 | Commercial | Cloud |
| 2 | pdfmux | 0.905 | 0.887 | 0.918 | MIT | No |
| 3 | Docling (IBM) | 0.877 | 0.887 | 0.900 | MIT | Optional |
| 4 | marker | 0.861 | 0.808 | 0.890 | GPL | Recommended |
| 5 | opendataloader | 0.844 | 0.494 | 0.913 | MIT | No |
| 6 | mineru | 0.831 | 0.873 | 0.857 | Apache-2.0 | Recommended |
| 7 | pymupdf4llm | 0.802 | 0.612 | 0.905 | AGPL | No |
| 8 | Unstructured (OSS) | 0.788 | 0.701 | 0.864 | Apache-2.0 | Optional |

### Academic Comparison (10 tools, 6 categories)

Adhikari & Agarwal (arxiv:2410.09871) evaluated 10 tools on DocLayNet: PyPDF, pdfminer.six, PyMuPDF, pdfplumber, pypdfium2, Unstructured, Tabula, Camelot, Nougat, and Table Transformer (TATR) across 6 categories:

- **Text extraction best**: PyMuPDF and pypdfium2 overall
- **Scientific & Patent**: Nougat (deep learning) outperformed rule-based tools
- **Table detection**: TATR excelled in Financial, Patent, Law & Regulations, Scientific; Camelot best for Government Tenders; PyMuPDF best for Manuals
- **All tools struggled** with Scientific and Patent document categories

### Decision Matrix

| Need | Best Choice | Rationale |
|------|------------|-----------|
| General-purpose free | pdfmux | 0.905 overall, MIT license, self-healing |
| Maximum speed | PyMuPDF | 0.01s/page |
| Table accuracy | Docling or pdfmux[tables] | 0.887-0.911 TEDS |
| Academic papers | marker | Equation detection |
| Scanned PDFs | pdfmux[ocr] | Automatic OCR fallback |
| Minimal dependencies | pdfplumber | Pure Python, no ML |
| Regulated workloads | pdfmux | MIT license, deterministic mode, on-prem |

## Layout Parsing & Document Structure

- **DocLayNet**: Largest multi-domain dataset (80K pages, 6 categories, 11 element types) — used as ground truth for layout model training
- **Docling's DocLayNet model**: State-of-the-art layout analysis trained on diverse document types
- **TableFormer**: Transformer-based table structure recognition used in Docling
- **Reading order**: Key differentiator between tools — pdfmux scores 0.918 (best free), mineru 0.857 (weakest)

## Table Extraction

Table extraction accuracy is the largest differentiator between tools:
- **Docling & pdfmux** tie at 0.887 TEDS — the ceiling for single-engine extraction
- **TATR** (Table Transformer) excels on financial tables, scientific tables, patents, and legal documents
- **Camelot** remains strong for bordered government tender tables
- **PyMuPDF standalone** only reaches 0.612 TEDS — tables are its weakness
- **opendataloader** at 0.494 TEDS — weakest among all tested tools

## PDF-to-Markdown Conversion Pipelines

Modern PDF ingestion pipelines follow a multi-stage architecture:

```
PDF -> Page Classification -> Route to Extractor -> Audit -> Re-extract Failures -> Markdown/JSON
```

Key design decisions:
- **Self-healing**: pdfmux audits every page and re-extracts failures — unique among open tools
- **Page classification**: Route clean digital pages to fast PyMuPDF, table-heavy pages to Docling, scans to OCR
- **Output formats**: Markdown (most common), JSON (structured), CSV (tabular), LLM-optimized (strips boilerplate, normalizes headings)
- **Model loading**: Docling/marker have 30-60s cold start for ML model loading; pdfmux with `quality=fast` avoids this

## Chunking Strategies for PDF-Derived Text

Chunking is the critical bridge between extraction and retrieval. Key approaches:

| Strategy | Description | Best For |
|----------|-------------|----------|
| Fixed-size | Split by token/character count | Simple documents |
| Semantic | Split at sentence/paragraph boundaries using embeddings | Diverse content |
| Page-based | Each PDF page = one chunk | Preserving original boundaries |
| Recursive | Split by headers -> paragraphs -> sentences -> chars | Hierarchical docs |
| Adaptive | Select strategy per-document using intrinsic metrics | Production RAG |

### Adaptive Chunking (arxiv:2603.25333)

Ekimetrics 2026 framework selects chunking strategy per-document using 5 intrinsic metrics:
- **References Completeness (RC)** — are citations intact?
- **Intrachunk Cohesion (ICC)** — is content within a chunk semantically coherent?
- **Document Contextual Coherence (DCC)** — does chunk order preserve document flow?
- **Block Integrity (BI)** — are structural blocks (tables, lists) preserved?
- **Size Compliance (SC)** — do chunks stay within embedding model limits?

Results: **72% answer correctness** (up from 62-64%), **65 successfully answered questions** (up from 49, +32.6%).

### Financial PDF RAG (arxiv:2604.12047)

Empirical study of PDF parsing + chunking for financial QA:
- Multiple parsers and chunking strategies tested with varied overlap
- Findings: chunking strategy x parser interaction is significant — poor parser output degrades even good chunkers
- Practical guidelines for building robust financial RAG pipelines

## OCR Integration for Scanned Documents

- **pdfmux[ocr]** extra provides automatic OCR fallback — classifies pages, routes scans to OCR engine
- **marker** has GPU-accelerated OCR for academic scans
- **Tesseract** remains the baseline OCR engine, but ML-based approaches (Nougat, Docling) outperform on complex layouts
- Key metric: OCR introduces accuracy degradation — benchmark all-scanned pipelines separately from digital-born ones

## Integration with Vector Databases and RAG

```
PDF -> Parser -> Cleaned Text -> Chunker -> Embeddings -> Vector DB -> Retrieval
                    |                     |
               Tables -> CSV    Metadata (headings, page numbers)
```

Key considerations:
- **Per-page confidence scoring** (pdfmux): downstream retrieval can weight chunks by extraction quality
- **JSON output with bounding boxes**: enables spatial queries and visual grounding
- **Metadata preservation**: page numbers, section headings, table captions -> improve retrieval relevance
- **Hybrid search**: combine semantic (embeddings) with keyword (BM25) over PDF-derived text

## Evaluation Benchmarks

| Benchmark | Scope | Metrics |
|-----------|-------|--------|
| DocLayNet | 80K pages, 6 categories, 11 element types | Layout element accuracy |
| opendataloader-bench | 200 real-world PDFs | NID, TEDS, MHS |
| PubTables-1M | Table detection + structure | IoU, structure accuracy |
| TableQuest (arxiv:2604.12047) | Financial QA over PDFs | Answer correctness |

## Multi-Modal PDF Processing

- **Images**: Extract embedded images, pass to vision models for description generation
- **Charts/Diagrams**: Docling + VLMs for chart data extraction; Marker for equation OCR
- **Forms**: AcroForm extraction (pdfmux supports key/value form field extraction)
- **Fillable PDFs**: Treat as structured data source, not free-text

## Practical Recommendations

1. **Classify before parsing**: Route clean digital pages through a fast path, reserve ML for complex pages — saves 10-30x in processing time
2. **Audit extraction quality**: Silent failures are the most damaging failure mode at scale
3. **Preserve structure metadata**: Headings, page numbers, table captions improve RAG retrieval quality
4. **Choose chunking per-document**: One-size-fits-all chunking leaves 8-10% answer correctness on the table
5. **Test on your domain**: Financial PDFs differ from academic papers — Sci/Patent documents degrade all parsers
6. **License check**: AGPL (PyMuPDF) and GPL (marker) may be blockers for commercial deployment; prefer MIT/Apache-2.0 tools

## Cross-Domain Connections

- **Knowledge Graph Construction**: Parsed PDF content -> entity extraction -> knowledge graph nodes
- **OSINT Entity Resolution**: PDF sources (financial disclosures, corporate registries) -> structured identity data
- **Critical Infrastructure Documentation**: OT manuals, SCADA specs -> indexed knowledge base
- **Multi-Agent Orchestration**: Parallel PDF ingestion across agent workers -> merge results
- **Context Management**: PDF-derived knowledge -> compressed semantic memory
- **Local-to-Frontier Bridging**: PDF-parsed corpora -> local model training/fine-tuning
- **Entity Resolution**: PDFs from heterogeneous sources -> cross-document entity linking
- **Financial Intelligence**: SEC filings, annual reports -> structured financial data extraction

## References

1. Adhikari & Agarwal (2024). "A Comparative Study of PDF Parsing Tools Across Diverse Document Categories." arXiv:2410.09871.
2. pdfmux blog (2026). "Best PDF extraction library for Python in 2026 (benchmarked)." https://pdfmux.com/blog/best-pdf-extraction-library-python/
3. pdfmux blog (2026). "pdfmux vs PyMuPDF vs marker vs docling vs pdfplumber: 200-PDF benchmark." https://pdfmux.com/blog/pdfmux-vs-pymupdf-vs-marker-vs-docling/
4. IBM Research (2024). "Docling Technical Report." arXiv:2408.09869.
5. Ekimetrics (2026). "Adaptive Chunking: Optimizing Chunking-Method Selection for RAG." arXiv:2603.25333.
6. "Empirical Evaluation of PDF Parsing and Chunking for Financial Question Answering with RAG." arXiv:2604.12047.
7. Firecrawl (2026). "Best Chunking Strategies for RAG (and LLMs) in 2026." https://www.firecrawl.dev/blog/best-chunking-strategies-rag
8. Pinecone (2025). "Chunking Strategies for LLM Applications." https://www.pinecone.io/learn/chunking-strategies/
9. Pfitzmann et al. (2022). "DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis." ACM SIGKDD.
10. Smock et al. (2022). "PubTables-1M: Towards comprehensive table extraction from unstructured documents." CVPR 2022.

---

**Lines: ~190** | **References: 10** | **Cross-Domain Connections: 8**
