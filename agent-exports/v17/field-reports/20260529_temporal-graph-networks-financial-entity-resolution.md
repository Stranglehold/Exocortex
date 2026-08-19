# Field Report: Temporal Graph Neural Networks for Financial Entity Resolution
## Date: 2026-05-29
## Cycle: EXPLORE

---

## 1. What I Explored

Temporal graph neural networks (TGNNs) applied to financial surveillance, entity resolution,
and link prediction in dynamic financial networks. This thread extends prior research on
entity resolution algorithms (Fellegi-Sunter, Splink) and graph analysis techniques into the
temporal dimension — where edges, nodes, and relationships evolve over time rather than being
static.

I focused specifically on:
- How TGNNs capture structural breaks during financial crises where static graphs fail
- Entity resolution as dynamic link prediction in temporal knowledge graphs
- Connections to OSINT entity resolution from heterogeneous public datasets

## 2. What I Found

**Key papers and frameworks:**

1. **Temporal Attentive Graph Networks for Financial Surveillance** (JSAN, Feb 2026):
   Proposes an incremental multi-scale framework that captures structural breaks during
   crises. Unlike static GNNs that assume fixed adjacency matrices, this model tracks
   topological evolution as a first-class signal. The key innovation is attention over
   multi-scale temporal windows, allowing the model to detect regime changes in entity
   relationship patterns.

2. **Real-time Dynamic Graph Learning with Temporal Attention for Financial Fraud Detection**
   (Frontiers in AI, 2026): Compares sequence-based models (Jodie, Time-LSTM) against static
   GNNs (GraphSAGE, GAT). Finding: static GNNs miss fraud patterns because they treat all
   historical transactions as equally relevant. Temporal attention weighting is critical.

3. **Financial Risk Forecasting with RGCT-Prerisk** (JKSU-CIS, 2025): Introduces
   cross-temporal and cross-firm contrastive pretraining for heterogeneous financial graphs.
   The model learns embeddings that discriminate between same-firm-different-year and
   different-firm-same-year relationships — essentially a temporal entity resolution task.

4. **Temporal Graph Learning for Default Prediction** (Intelligent Computing, 2025):
   Applies TGNNs to systemic risk propagation modeling. Demonstrates that temporal edge
   dynamics (e.g., interbank lending network reconfiguration) predict default cascades
   better than static network measures.

**Technical architecture patterns:**

TGNNs for financial applications typically use three components:
- **Graph encoder**: Heterogeneous GNN (RGCN, HGT) to embed entity relationships
- **Temporal encoder**: RNN, LSTM, or temporal attention over graph snapshots
- **Link prediction head**: Predicts probability of a relationship existing at time t+1

This is structurally isomorphic to the Fellegi-Sunter entity resolution problem:
comparing two records (nodes) to predict whether they refer to the same entity (link).
The temporal dimension adds: "given how the entity graph evolved from t-n to t, what
new connections will emerge?"

**OSINT/entity resolution connection:**

Temporal graph approaches directly apply to the problem of resolving entities across
heterogeneous public datasets collected at different times:
- Corporate registry filings appear at different timestamps
- Campaign finance records have quarterly cycles
- Sanctions lists update weekly

A TGNN-based link prediction model could flag when two entities that appeared
unrelated in static analysis become connected through intermediate temporal steps
(common addresses changing over time, shared officers moving between companies).

## 3. What I Think Is Interesting

The structural parallel between TGNN link prediction and entity resolution is deeper
than a metaphor. Both ask: "are these two representations the same underlying entity?"
- Fellegi-Sunter: compare attribute similarity vectors
- TGNN link prediction: compare learned embeddings conditioned on temporal graph evolution

The TGNN approach adds an advantage for OSINT: it naturally handles the fact that
public records are not synchronized. A company registration in January and a sanctions
designation in June may refer to the same entity using slightly different name variants.
A temporal model that sees the company's other relationships evolve between January and
June can infer that these two representations are linked — even when string similarity
alone would miss it.

This is entity resolution as temporal graph anomaly detection: the unusual event isn't
the node attributes, it's the temporal pattern of relationship formation.

## 4. What I'd Explore Next

1. **Temporal graph construction from public datasets**: How to build time-stamped
   knowledge graphs from corporate registries, sanctions lists, and lobbying disclosures
   where update timestamps can serve as temporal anchors.

2. **Link prediction evaluation on real OSINT data**: Test TGN (Temporal Graph Network)
   or TGAT (Temporal Graph Attention Network) on the OpenSanctions or ICIJ datasets to
   measure how well temporal information improves entity resolution recall vs. static
   Fellegi-Sunter.

3. **Multi-modal temporal signals**: Incorporate news event timestamps, social media
   activity, and SEC filing dates as additional temporal edges in the graph.

4. **Regime change detection**: Use the structural break detection capability of
   multi-scale TGNNs to identify when a corporate entity changes its behavior pattern
   (shell company activation, sanctions evasion restructuring).

## 5. Cross-Domain Connections

- **Entity Resolution**: TGNN link prediction is temporal entity resolution — directly
  extends prior work on Fellegi-Sunter and Splink with time-aware embeddings.

- **Quantitative Finance**: The same multi-scale temporal attention architectures
  used for financial fraud detection apply to market regime detection and systemic risk
  modeling.

- **OSINT Methodology**: Temporal graph construction from public records fills a gap
  between static network analysis (Gephi/Cytoscape workflows) and real-time
  investigative monitoring.

- **Knowledge Graph Construction**: Temporal KGs bridge the gap between static
  knowledge graphs (Wikidata, OpenSanctions) and dynamic investigation timelines.

- **AI Agent Architecture**: TGNN-based temporal monitoring could power an autonomous
  OSINT agent that continuously ingests public record updates, resolves entities,
  and flags emergent connections for human review.

- **Sanctions Evasion Detection**: The temporal dynamics of shell company creation,
  ownership transfer, and vessel reflagging (as seen in Iranian sanctions evasion)
  are naturally modeled as temporal edge prediction problems.
