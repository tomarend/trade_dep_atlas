# Roadmap: Trade Critical Dependencies Dashboard

## Overview

Build from data up: ingest and clean 20 years of BACI trade data, compute the composite dependency scoring that differentiates this project, stand up the Dash application shell, then deliver two complementary analytical views (Country→Products, Product→Countries) followed by temporal analysis and portfolio-quality advanced visualizations. Each phase produces a verifiable, standalone capability — raw data becomes queryable scores, scores become interactive exploration, exploration becomes insight.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Pipeline & Ingestion** - Download BACI data, apply HS concordance, normalize country IDs, establish pipeline architecture
- [ ] **Phase 2: Scoring Pipeline & Storage** - Compute HHI, geopolitical risk, essentiality, and composite scores; store in DuckDB
- [ ] **Phase 3: Dashboard Shell & Data Access** - Multi-page Dash app with routing, methodology page, data access layer, loading states
- [ ] **Phase 4: Country→Products View** - Primary analytical view with ranked tables, maps, charts, score decomposition, weight controls
- [ ] **Phase 5: Product→Countries View & Cross-Linking** - Second analytical entry point with HS hierarchy browsing and bidirectional cross-linking
- [ ] **Phase 6: Time Series & Advanced Visualizations** - Year slider, trend charts, Sankey flow diagrams, network graph

## Phase Details

### Phase 1: Data Pipeline & Ingestion
**Goal**: BACI trade data is downloaded, cleaned, and available for analysis with consistent product codes and country identifiers across all years
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. Running the pipeline downloads BACI data files for all available years from CEPII
  2. Pipeline ingests multi-GB BACI CSVs using Polars lazy evaluation without exceeding available memory
  3. All HS6 product codes are mapped to a single consistent revision across the full time series via concordance tables
  4. All country identifiers resolve to ISO3 codes with no unresolved or ambiguous mappings
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Project scaffolding + BACI download module with retry and resume
- [ ] 01-02-PLAN.md — Country code mapping (ISO3) + HS concordance pipeline
- [ ] 01-03-PLAN.md — Core ingestion pipeline (Polars ETL) + CLI orchestrator

### Phase 2: Scoring Pipeline & Storage
**Goal**: Every product-importer pair has HHI, geopolitical risk, essentiality, and composite dependency scores computed and stored for fast querying
**Depends on**: Phase 1
**Requirements**: SCOR-01, SCOR-02, SCOR-03, SCOR-04, DATA-05
**Success Criteria** (what must be TRUE):
  1. HHI concentration index is computed for every product-importer-year tuple with values normalized to 0–1 range
  2. Geopolitical risk scores are computed for all countries using governance indices and sanctions data
  3. Products are classified into essentiality tiers (critical/important/standard) using EU CRM lists, USGS critical minerals, and sector categorization
  4. Composite dependency score combines HHI, geo risk, and essentiality with configurable weights
  5. All pre-computed metrics are stored in DuckDB and queryable in <50ms for typical dashboard queries
**Plans**: 4 plans

Plans:
- [x] 02-01-PLAN.md — HHI concentration scoring module (pipeline/hhi.py + tests)
- [x] 02-02-PLAN.md — Geo-risk scoring module (pipeline/georisk.py + reference data + tests)
- [x] 02-03-PLAN.md — Essentiality classification (config YAML + CSV files + pipeline/essentiality.py + tests)
- [x] 02-04-PLAN.md — Composite score + DuckDB export + CLI wiring (pipeline/composite.py, export.py, __main__.py)

### Phase 3: Dashboard Shell & Data Access
**Goal**: The Dash application is running with multi-page routing, shared navigation, data access layer, and methodology documentation
**Depends on**: Phase 2
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. Dashboard launches locally with multi-page routing between country view, product view, and methodology pages
  2. Methodology page explains HHI formula, geopolitical risk sources, essentiality classification, and data provenance
  3. Dashboard displays data freshness indicator showing latest available year and year range
  4. All page transitions use loading states and respond in under one second
  5. Application runs with gunicorn and has Docker configuration for deployment
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — Data access layer (DuckDB singleton) + Dash app shell with sidebar layout
- [ ] 03-02-PLAN.md — Full methodology page (4 tabs, MathJax formulas) + stub pages with loading states
- [ ] 03-03-PLAN.md — Dockerfile + human verification checkpoint

### Phase 4: Country→Products View
**Goal**: User can select any importing country and explore its product vulnerabilities through interactive tables, maps, charts, and score decomposition with adjustable weights
**Depends on**: Phase 3
**Requirements**: CNTV-01, CNTV-02, CNTV-03, CNTV-04, CNTV-05, CNTV-06, SCOR-05, VIZZ-01, VIZZ-03, VIZZ-04, VIZZ-05
**Success Criteria** (what must be TRUE):
  1. User can select an importer from ~200 countries and see a ranked AG Grid table of products sorted by composite dependency score, sortable by any sub-score
  2. User can drill into any product to see supplier breakdown with share percentages, individual risk scores, and a choropleth map of suppliers colored by geopolitical risk
  3. User can adjust HHI/geo-risk/essentiality weights via interactive controls and see all scores and rankings update dynamically
  4. Score decomposition is visible through summary cards, radar/spider chart, and bar/line charts for each product-country pair
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD
- [ ] 04-04: TBD

### Phase 5: Product→Countries View & Cross-Linking
**Goal**: User can select any HS6 product and see which importing countries are most exposed, with seamless bidirectional navigation between both analytical views
**Depends on**: Phase 4
**Requirements**: PRDV-01, PRDV-02, PRDV-03, PRDV-04, PRDV-05, PRDV-06, CNTV-07
**Success Criteria** (what must be TRUE):
  1. User can browse and select an HS6 product via hierarchical selector (HS2→HS4→HS6) and see a ranked, sortable table of importers by dependency score with summary statistics
  2. User can view a choropleth world map with importers colored by dependency score for the selected product
  3. User can click any product in the country view to jump to its product view, and click any country in the product view to jump to its country view
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD
- [ ] 05-03: TBD

### Phase 6: Time Series & Advanced Visualizations
**Goal**: Dashboard provides temporal analysis and portfolio-quality Sankey and network visualizations that reveal trade flow structure and evolution over time
**Depends on**: Phase 5
**Requirements**: TIME-01, TIME-02, TIME-03, VIZZ-02, VIZZ-06
**Success Criteria** (what must be TRUE):
  1. User can select a year via slider and see all dependency scores update, with line charts showing how scores evolve over ~20 years for any country-product pair
  2. Sankey diagrams display supplier→importer trade flows with width proportional to trade share and color encoding geopolitical risk
  3. Force-directed network graph renders countries as nodes and trade flows as edges, with color/size encoding risk and volume
  4. Time series displays handle missing data gracefully where gaps exist in BACI coverage
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD
- [ ] 06-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Pipeline & Ingestion | 0/3 | Planned | - |
| 2. Scoring Pipeline & Storage | 0/3 | Not started | - |
| 3. Dashboard Shell & Data Access | 0/3 | Not started | - |
| 4. Country→Products View | 0/4 | Not started | - |
| 5. Product→Countries View & Cross-Linking | 0/3 | Not started | - |
| 6. Time Series & Advanced Visualizations | 0/3 | Not started | - |

---
*Roadmap created: 2026-03-17*
*Last updated: 2026-03-18*
