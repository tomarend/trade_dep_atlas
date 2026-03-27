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
- [ ] **Phase 4.1: Data Quality Fixes** - INSERTED — Fix product descriptions, country regions, and georisk forward-fill
- [x] **Phase 5: Product→Countries View & Cross-Linking** - Second analytical entry point with HS hierarchy browsing and bidirectional cross-linking
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
- [x] 03-01-PLAN.md — Data access layer (DuckDB singleton) + Dash app shell with sidebar layout
- [x] 03-02-PLAN.md — Full methodology page (4 tabs, MathJax formulas) + stub pages with loading states
- [x] 03-03-PLAN.md — Dockerfile + human verification checkpoint

### Phase 4: Country→Products View
**Goal**: User can select any importing country and explore its product vulnerabilities through interactive tables, maps, charts, and score decomposition with adjustable weights
**Depends on**: Phase 3
**Requirements**: CNTV-01, CNTV-02, CNTV-03, CNTV-04, CNTV-05, CNTV-06, SCOR-05, VIZZ-01, VIZZ-03, VIZZ-04, VIZZ-05
**Success Criteria** (what must be TRUE):
  1. User can select an importer from ~200 countries and see a ranked AG Grid table of products sorted by composite dependency score, sortable by any sub-score
  2. User can drill into any product to see supplier breakdown with share percentages, individual risk scores, and a choropleth map of suppliers colored by geopolitical risk
  3. User can adjust HHI/geo-risk/essentiality weights via interactive controls and see all scores and rankings update dynamically
  4. Score decomposition is visible through summary cards, radar/spider chart, and bar/line charts for each product-country pair
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Data access layer queries + country page layout with selector, summary cards, weight sliders
- [x] 04-02-PLAN.md — AG Grid product table with sorting, filtering, conditional formatting, weight recalculation
- [x] 04-03-PLAN.md — Product drill-down panel with supplier table, choropleth map, radar chart, bar chart
- [x] 04-04-PLAN.md — Gap closure: AG Grid filter + country dropdown fixes

### Phase 4.1: Data Quality Fixes (INSERTED)
**Goal**: All products have human-readable descriptions, all countries have region/continent assignments, and geo-risk scores cover all BACI years including 2024
**Depends on**: Phase 4
**Requirements**: DATA-03, DATA-04, SCOR-02
**Success Criteria** (what must be TRUE):
  1. All ~5,000 HS6 products in the dashboard have real descriptions (not empty or "Unknown product")
  2. All 252 countries have real region and continent assignments (not "Unknown")
  3. Year 2024 composite scores use forward-filled geo-risk values from 2023 WGI data
**Plans**: 1 plan

Plans:
- [x] 04.1-01-PLAN.md — Fix product descriptions, country regions, georisk forward-fill, rebuild DuckDB

### Phase 5: Product→Countries View & Cross-Linking
**Goal**: User can select any HS6 product and see which importing countries are most exposed, with seamless bidirectional navigation between both analytical views
**Depends on**: Phase 4.1
**Requirements**: PRDV-01, PRDV-02, PRDV-03, PRDV-04, PRDV-05, PRDV-06, CNTV-07
**Success Criteria** (what must be TRUE):
  1. User can browse and select an HS6 product via hierarchical selector (HS2→HS4→HS6) and see a ranked, sortable table of importers by dependency score with summary statistics
  2. User can view a choropleth world map with importers colored by dependency score for the selected product
  3. User can click any product in the country view to jump to its product view, and click any country in the product view to jump to its country view
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — Data access queries + product page layout with HS hierarchy selector and summary cards
- [x] 05-02-PLAN.md — AG Grid importer table with sorting, filtering, and choropleth world map
- [x] 05-03-PLAN.md — Bidirectional cross-linking between country and product views

### Phase 6: Time Series & Advanced Visualizations
**Goal**: Dashboard provides temporal analysis and portfolio-quality Sankey and network visualizations that reveal trade flow structure and evolution over time
**Depends on**: Phase 5
**Requirements**: TIME-01, TIME-02, TIME-03, VIZZ-02, VIZZ-06
**Success Criteria** (what must be TRUE):
  1. User can select a year via slider and see all dependency scores update, with line charts showing how scores evolve over ~20 years for any country-product pair
  2. Sankey diagrams display supplier→importer trade flows with width proportional to trade share and color encoding geopolitical risk
  3. Force-directed network graph renders countries as nodes and trade flows as edges, with color/size encoding risk and volume
  4. Time series displays handle missing data gracefully where gaps exist in BACI coverage
**Plans**: 3 plans

Plans:
- [ ] 06-01-PLAN.md — Year slider in sidebar + data queries (trend, trade flows) + wire year to all page callbacks
- [ ] 06-02-PLAN.md — Trend line charts in country drill-down + product page with toggleable sub-scores
- [ ] 06-03-PLAN.md — Sankey flow diagram + force-directed network graph on product page


---

## v2.0 Milestone: Dashboard Redesign

Phases 7–9 continue from v1 execution order. Each phase builds on prior output.
v2.0 goal: empirical scoring, lean data pipeline, insight-first visualization.

- [x] **Phase 7: Pipeline & Scoring Rework** - Replace tier scoring with global_export_hhi, slim BACI download to HS92+HS22, rebuild DuckDB schema
- [ ] **Phase 8: Dashboard Redesign** - Country page hero/scatter/bilateral, product page concentration bars/flags, remove network graph
- [ ] **Phase 9: Time Series** - Update trend charts for substitutability, add sparklines via custom SVG cellRenderer

### Phase 7: Pipeline & Scoring Rework
**Goal**: Pipeline downloads only HS92 + HS22 data, scoring uses empirical global_export_hhi as substitutability proxy, and DuckDB schema is fully updated with no tier columns
**Depends on**: Phase 5 (completed v1 codebase)
**Requirements**: DATA-06, DATA-07, SCOR-06, SCOR-07, SCOR-08
**Success Criteria** (what must be TRUE):
  1. Running the download step fetches only HS92 and HS22 files (~17GB total, not ~45GB)
  2. pipeline/flags.py produces a `flags` list per product; no essentiality_tier or essentiality_score in any pipeline output
  3. Composite score formula uses `w3 * global_export_hhi` as third component; weights still sum to 1.0 and can be adjusted
  4. DuckDB products dim has `flags` LIST column and `global_export_hhi`; dependency_scores has `substitutability_score`; no essentiality_tier column
  5. Full pipeline run completes end-to-end and dashboard launches without ColumnNotFound errors
**Plans**: 4 plans

Plans:
- [x] 07-01-PLAN.md — Slim BACI download to HS92+HS22 only; HS22 priority ingest for 2022-2024; BACI product codes as authoritative descriptions
- [x] 07-02-PLAN.md — Create pipeline/flags.py and data/reference/flags_config.yaml with 8 canonical product flags
- [x] 07-03-PLAN.md — Wire composite.py + export.py + __main__.py for new schema; delete essentiality files
- [x] 07-04-PLAN.md — Update dashboard/data.py, country.py, product.py for v2 DuckDB schema

### Phase 8: Dashboard Redesign
**Goal**: Country page is insight-first with hero cards, scatter plot, and bilateral risk panel; product page has concentration bars and flag badges; network graph removed; all "essentiality" labels replaced
**Depends on**: Phase 7
**Requirements**: CNTV-08, CNTV-09, CNTV-10, CNTV-11, PRDV-07, PRDV-08, PRDV-09, DASH-06
**Success Criteria** (what must be TRUE):
  1. Country page: 4 hero stat cards visible above the fold with correct values from DuckDB
  2. Country page: scatter plot renders top-200 products with HHI (x) vs substitutability (y), sized by import value
  3. Country page: bilateral risk panel shows top-10 source countries as horizontal bars, ranked by weighted risk contribution
  4. Product page: concentration bar chart renders top exporters with share % bars colored by geo risk
  5. Product page: flag badges displayed for applicable products (EU CRM, energy, pharma, etc.)
  6. Network graph and dash-cytoscape removed; no import errors on startup
  7. Zero occurrences of "essentiality" in UI-visible text (slider labels, chart titles, cards)
**Plans**: TBD

Plans:
- [x] 08-01-PLAN.md — TBD

### Phase 9: Time Series
**Goal**: Score trend charts show substitutability instead of essentiality, and AG Grid product tables have year sparklines
**Depends on**: Phase 8
**Requirements**: TIME-04, TIME-05
**Success Criteria** (what must be TRUE):
  1. Score trend line chart labels and tooltip show "Substitutability" not "Essentiality"
  2. AG Grid product tables have a "Trend" column with SVG sparklines (6 data points, 60×20px)
  3. Sparklines render without AG Grid Enterprise errors in browser console
**Plans**: 2 plans

Plans:
- [ ] 09-01-PLAN.md — Sparkline data queries (data.py) + TrendSparkline SVG cellRenderer (JS)
- [ ] 09-02-PLAN.md — Wire sparklines into both AG Grid tables + TIME-04 trend chart label cleanup

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 4.1 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Pipeline & Ingestion | 0/3 | Planned | - |
| 2. Scoring Pipeline & Storage | 0/3 | Not started | - |
| 3. Dashboard Shell & Data Access | 0/3 | Not started | - |
| 4. Country→Products View | 4/4 | Complete | - |
| 4.1 Data Quality Fixes | 1/1 | Complete | - |
| 5. Product→Countries View & Cross-Linking | 0/3 | Planned | - |
| 6. Time Series & Advanced Visualizations | 0/3 | Not started | - |

| 7. Pipeline & Scoring Rework | TBD | Not started | - |
| 8. Dashboard Redesign | TBD | Not started | - |
| 9. Time Series (v2) | TBD | Not started | - |

---
*Roadmap created: 2026-03-17*
*Last updated: 2026-03-26*
