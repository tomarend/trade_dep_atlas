# Requirements: Trade Critical Dependencies Dashboard

**Defined:** 2026-03-17
**Core Value:** Instantly reveal which products make a country vulnerable due to concentrated, geopolitically risky import sources — and how that exposure has evolved over time.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Pipeline

- [ ] **DATA-01**: System can automatically download BACI bilateral trade data files from CEPII
- [ ] **DATA-02**: System ingests BACI CSV files (all countries, all HS6 products, all available years) into a processing pipeline
- [ ] **DATA-03**: System applies HS code revision concordance tables to maintain consistent product codes across years
- [ ] **DATA-04**: System normalizes country identifiers to ISO3 codes, handling name variants and edge cases (e.g., "Korea, Rep." → KOR)
- [ ] **DATA-05**: Pipeline stores all pre-computed metrics in DuckDB for fast dashboard serving

### Scoring

- [ ] **SCOR-01**: System computes HHI concentration index per product-importer pair across all supplier countries
- [ ] **SCOR-02**: System computes geopolitical risk score per country as a composite of trade sanctions exposure and governance indices (WGI or similar)
- [ ] **SCOR-03**: System classifies product essentiality tier (critical/important/standard) using EU CRM lists, USGS critical minerals, and sector categorization (energy, pharma, food, semiconductors)
- [ ] **SCOR-04**: System computes composite dependency score as a weighted combination of HHI concentration, geopolitical risk, and product essentiality
- [ ] **SCOR-05**: User can adjust sub-score weights (HHI, geo risk, essentiality) via interactive controls in the dashboard and see results update

### Country View

- [ ] **CNTV-01**: User can select an importing country via searchable dropdown with ~200 countries
- [ ] **CNTV-02**: User can see a ranked table of products sorted by composite dependency score for the selected country
- [ ] **CNTV-03**: User can sort the product vulnerability table by composite score, HHI, geo risk, or essentiality
- [ ] **CNTV-04**: User can see score summary cards showing top-level dependency statistics for the selected country
- [ ] **CNTV-05**: User can drill into any product row to see supplier breakdown (top supplier countries, their share %, individual risk scores)
- [ ] **CNTV-06**: User can view a choropleth world map showing supplier countries colored by geopolitical risk for a selected product
- [ ] **CNTV-07**: User can click through from the country view to the product view for any product (cross-linking)

### Product View

- [ ] **PRDV-01**: User can select an HS6 product via searchable selector with HS hierarchy browsing (HS2→HS4→HS6)
- [ ] **PRDV-02**: User can see a ranked table of importing countries sorted by exposure/dependency for the selected product
- [ ] **PRDV-03**: User can sort the country exposure table by composite score, HHI, geo risk, or essentiality
- [ ] **PRDV-04**: User can see score summary cards showing top-level statistics for the selected product
- [ ] **PRDV-05**: User can view a choropleth world map with importers colored by dependency score for the selected product
- [ ] **PRDV-06**: User can click through from the product view to the country view for any country (cross-linking)

### Time Series

- [x] **TIME-01**: User can select a year via slider or dropdown to view dependency scores for that year
- [x] **TIME-02**: User can see line charts showing how dependency scores evolve over ~20 years for a country-product pair
- [x] **TIME-03**: Time series handles missing data gracefully (gaps in BACI coverage)

### Visualizations

- [ ] **VIZZ-01**: Dashboard renders a choropleth world map colored by dependency metric (score, HHI, risk)
- [ ] **VIZZ-02**: Dashboard renders Sankey diagrams showing supplier→importer trade flows, width proportional to trade share, color encoding geopolitical risk
- [ ] **VIZZ-03**: Dashboard renders bar and line charts for score decomposition and trends
- [ ] **VIZZ-04**: Dashboard renders sortable data tables with AG Grid (sorting, filtering, pagination, conditional formatting)
- [ ] **VIZZ-05**: Dashboard renders radar/spider chart showing score decomposition (HHI vs geo risk vs essentiality) for a product-country pair
- [ ] **VIZZ-06**: Dashboard renders force-directed network graph of trade dependency relationships (nodes = countries, edges = flows, color/size = risk/volume)

### Dashboard Shell

- [ ] **DASH-01**: Dashboard built with Dash/Plotly with multi-page routing (country view, product view, methodology)
- [ ] **DASH-02**: Dashboard includes a methodology page explaining HHI formula, risk index sources, essentiality classification, and data sources
- [ ] **DASH-03**: Dashboard shows data freshness indicator (latest data year, range of available years)
- [ ] **DASH-04**: Dashboard renders with loading states and targets sub-second view transitions
- [ ] **DASH-05**: Dashboard runs locally and has architecture supporting future deployment (e.g., gunicorn, Docker)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Tables

- **TABL-01**: Year-over-year trend sparklines embedded in table cells showing 20-year trajectory
- **TABL-02**: CSV export of visible table data

### Temporal

- **TEMP-01**: Animated temporal evolution with play/pause button animating choropleth or scatter over years
- **TEMP-02**: "What changed?" panel surfacing products where dependency score increased significantly year-over-year

### Advanced

- **ADVN-01**: Export dependency analysis (countries reliant on exporting a product)
- **ADVN-02**: Country or product comparison mode (side-by-side)
- **ADVN-03**: Sector-level aggregation (aggregate HS6 to broader sectors)
- **ADVN-04**: Public API for programmatic access to dependency scores

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Tariff simulation / trade policy modeling | Different analytical domain; months of additional complexity for questionable accuracy |
| Predictive forecasting of dependency scores | BACI is retrospective; extrapolation unreliable without deep academic methodology |
| Subnational / regional trade data | Requires different data sources; country-level is the right granularity for dependency |
| Company-level / Bill of Lading data | Proprietary data, different analytical framework |
| User accounts / authentication | Portfolio piece; use shareable URL state instead |
| AI chat interface | Distraction from structured analytical UX |
| Real-time data updates | BACI is annual retrospective with ~2 year lag |
| Multi-language support | Product names are English-standardized; portfolio targets English audience |
| Mobile-optimized layout | Desktop-first analytical tool |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| DATA-05 | Phase 2 | Pending |
| SCOR-01 | Phase 2 | Pending |
| SCOR-02 | Phase 2 | Pending |
| SCOR-03 | Phase 2 | Pending |
| SCOR-04 | Phase 2 | Pending |
| SCOR-05 | Phase 4 | Pending |
| CNTV-01 | Phase 4 | Pending |
| CNTV-02 | Phase 4 | Pending |
| CNTV-03 | Phase 4 | Pending |
| CNTV-04 | Phase 4 | Pending |
| CNTV-05 | Phase 4 | Pending |
| CNTV-06 | Phase 4 | Pending |
| CNTV-07 | Phase 5 | Pending |
| PRDV-01 | Phase 5 | Pending |
| PRDV-02 | Phase 5 | Pending |
| PRDV-03 | Phase 5 | Pending |
| PRDV-04 | Phase 5 | Pending |
| PRDV-05 | Phase 5 | Pending |
| PRDV-06 | Phase 5 | Pending |
| TIME-01 | Phase 6 | Complete |
| TIME-02 | Phase 6 | Complete |
| TIME-03 | Phase 6 | Complete |
| VIZZ-01 | Phase 4 | Pending |
| VIZZ-02 | Phase 6 | Pending |
| VIZZ-03 | Phase 4 | Pending |
| VIZZ-04 | Phase 4 | Pending |
| VIZZ-05 | Phase 4 | Pending |
| VIZZ-06 | Phase 6 | Pending |
| DASH-01 | Phase 3 | Pending |
| DASH-02 | Phase 3 | Pending |
| DASH-03 | Phase 3 | Pending |
| DASH-04 | Phase 3 | Pending |
| DASH-05 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 37 total
- Mapped to phases: 37
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-17 after roadmap creation*
