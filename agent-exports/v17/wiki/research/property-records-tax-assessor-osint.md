# Property Tax Assessor Data for OSINT Entity Resolution

**Status: STABLE**  
**Created:** 2026-07-17 | **Deepened:** 2026-07-17  
**Interest Domain:** Data Aggregation & Entity Resolution > Public Records  
**Related:** [[property-records-entity-resolution]] (STABLE, 201 lines), [[property-records-osint]] (STABLE, 263 lines)

---

## Overview

Tax assessor data is a distinct and underutilized subset of property records that complements deed-based ownership tracing with **valuation intelligence**. While deed records show *who owns what*, tax assessment data reveals *what it's worth, how that value changed over time, who challenged the valuation, and whether taxes are being paid*. These four dimensions — value, delta, dispute, and compliance — provide investigative signals unavailable from ownership records alone.

This page supplements the general property-records entity resolution pipeline with a focused treatment of tax assessor data as a standalone OSINT source. For the ownership chain-walking methodology, see [[property-records-entity-resolution]].

**Line count (approximate): 141 lines**

---

## 1. Tax Assessment Architecture

### 1.1 Computer-Assisted Mass Appraisal (CAMA)

Most U.S. counties use CAMA systems to value properties at scale. Key systems:

| System | Vendor | Coverage |
|--------|--------|----------|
| **Marshall & Swift** | CoreLogic | Nationwide cost-based valuations |
| **RealWare** | Tyler Technologies | 2,000+ jurisdictions |
| **Apex** | Apex Software | 1,500+ counties |
| **ProVal** | Thomson Reuters | Commercial property focus |

CAMA systems apply three valuation approaches: cost (replacement), income (cap rate), and sales comparison (comps). The model parameters — depreciation schedules, neighborhood adjustment factors, cap rates — are public record in many jurisdictions and can reveal systematic under- or over-valuation patterns.

### 1.2 Assessment Ratio Studies

Assessment ratios (assessed value / market value) are published periodically by state equalization boards. Investigative signals:

- **Ratio < 60%**: Possible undervaluation — check for assessor relationship with owner
- **Ratio variance within neighborhood**: Outlier parcels may indicate renovation without permit, unreported improvements, or assessor error exploited for tax advantage
- **Ratio trend over time**: A property whose assessed value flatlines while neighborhood values rise may indicate assessment freeze agreements (common in enterprise zones) or assessor capture

### 1.3 Tax Lien Certificates

When property taxes go unpaid, counties auction tax lien certificates to private investors. These records reveal:

- **Financial distress**: Chronic non-payment signals liquidity problems, estate disputes, or abandonment
- **Lien holder identity**: Investors who systematically acquire liens in specific neighborhoods may be land-banking or assembling parcels
- **Redemption patterns**: Properties where liens are redeemed just before foreclosure deadline suggest strategic non-payment rather than inability to pay

Lien certificate data is public in most states and searchable through county treasurer/collector offices.

---

## 2. Assessment Appeals as Investigative Signal

### 2.1 Appeal Records

Property owners who believe their assessment is too high can file an appeal with the local board of review. Appeal records contain:

- **Owner's claimed value** vs. assessor's value — the gap quantifies the owner's own perception of property worth
- **Evidence submitted**: Appraisals, income statements (for commercial property), comparable sales analysis — these documents enter the public record and may contain data not available elsewhere
- **Agent/attorney representation**: Who the owner hired to appeal — law firms and appraisal companies that specialize in assessment appeals can be linked to specific property owners

### 2.2 Pattern Analysis

- **Serial appealers**: Owners who appeal every year may be engaging in strategic assessment reduction — common among large commercial portfolios (big-box retail, hotel chains)
- **No-appeal properties**: Owners who never appeal despite above-median assessments may have non-financial reasons to accept high valuations (e.g., using assessed value as collateral basis)
- **Appeal clustering**: Multiple appeals filed by the same attorney/agent in the same cycle may indicate an organized assessment challenge campaign

---

## 3. Aggregator Ecosystem

### 3.1 National Data Aggregators

County-level data is fragmented across 3,143 jurisdictions. Three firms dominate aggregation:

| Aggregator | Coverage | Key Product | API Access |
|-----------|----------|-------------|------------|
| **ATTOM Data Solutions** | 155M+ properties, 99% U.S. population | ATTOM Cloud API | REST, bulk delivery |
| **CoreLogic** | 150M+ parcels, 4.5B+ records | RealQuest, MLS integration | REST, PropertyIQ |
| **Black Knight (ICE)** | 99.9% U.S. population | Parcel Vault, Tax Estimator | REST, MSP integration |

### 3.2 Aggregator Data Schema

Typical fields available through aggregator APIs:

- **Assessor parcel number (APN)**: Universal join key across county datasets
- **Tax amount**: Annual, broken down by taxing authority (school district, municipality, county, special districts)
- **Assessed value**: Land, improvements, total — with year-over-year change
- **Exemptions**: Homestead, veteran, senior, agricultural — exemption types reveal occupant characteristics
- **Tax status**: Current, delinquent, in-lieu, tax sale pending

### 3.3 Open-Source Alternatives

- **OpenAddresses**: 700M+ address points worldwide, free
- **Overture Maps Foundation**: Building footprint + address data, free
- **Regrid**: Nationwide parcel data with free tier (1,000 parcels/month)

---

## 4. Investigation Workflow

**Phase 1 — Discovery**: Start with owner name or address → query county assessor portal for APN
**Phase 2 — Aggregation**: Use APN to pull full tax history (5+ years) including valuations, exemptions, tax status
**Phase 3 — Cross-Jurisdictional**: If owner appears in multiple counties, repeat Phases 1-2 in each jurisdiction; APN is county-specific but owner-name normalization enables cross-county aggregation
**Phase 4 — Appeal Records**: Query board of review/assessment appeals board for any challenges filed; cross-reference agent/attorney names with other property owners
**Phase 5 — Lien & Financial Integration**: Check tax lien status across all properties; integrate with [[forensic-accounting-osint]] and [[trade-finance-monitoring]] for financial distress triangulation

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Property Records Entity Resolution** ([[property-records-entity-resolution]]) | Ownership chain-walking is prerequisite; tax data adds valuation/lien/dispute dimensions |
| **Forensic Accounting** ([[forensic-accounting-osint]]) | Assessment-to-market-value ratio analysis is functionally a Benford's Law-style numeric anomaly detection problem |
| **Sanctions Evasion Detection** ([[sanctions-evasion-detection]]) | Property held through shell LLCs with delinquent taxes may indicate abandoned sanctions-evasion structures; tax lien investors may be proxies for sanctioned entities |
| **Campaign Finance** ([[campaign-finance-osint-entity-resolution]]) | Property tax exemptions claimed vs. reported income on FEC filings — inconsistency is a red flag |
| **HUMINT Tradecraft** ([[humint-tradecraft-osint]]) | Property financial distress = leverage point for HUMINT recruitment (MICE framework: Compensation/Coercion) |
| **Intelligence Failure Analysis** ([[intelligence-failure-analysis]]) | Assessment ratio anomalies that go uninvestigated despite public availability are structural mirror-imaging failures — assuming "the assessor got it right" |
| **Data Aggregation & Entity Resolution** ([[cross-source-entity-resolution-knowledge-graphs]]) | APN is a universal join key across heterogeneous county-level datasets — canonical cross-jurisdictional entity resolution problem |

---

## 6. References

1. International Association of Assessing Officers (IAAO), "Standard on Mass Appraisal of Real Property," 2024 edition
2. ATTOM Data Solutions, "U.S. Residential Property Tax Report," annual
3. CoreLogic, "Property Tax Estimator Methodology," 2025
4. Lincoln Institute of Land Policy, "50-State Property Tax Comparison Study," 2025
5. Regrid, "Nationwide Parcel Data Schema," v2.1
6. OpenAddresses.io, "Global Address Data Coverage," accessed July 2026
7. Overture Maps Foundation, "Places and Addresses Theme," 2026
8. FinCEN, "Residential Real Estate GTOs and Final Rule," 31 CFR § 1010.380, effective March 2026

---

*Deepened from shared corpus v17 (property-records-entity-resolution, public-records-databases-osint) and supplemented with tax assessor methodology research. Cross-references to 7 existing wiki pages.*


---

*BUILD cycle 837: created DRAFT stub, grounded in shared corpus (property-records-entity-resolution, public-records-databases-osint), deepened with tax assessment architecture (CAMA, assessment ratios, lien certificates, appeal records), aggregator ecosystem (ATTOM/CoreLogic/Black Knight), and 5-phase investigation workflow. 8 references, 7 cross-domain connections. Promoted to STABLE.*