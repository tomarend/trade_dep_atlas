# Trade Critical Dependencies Dashboard

## What This Is

A state-of-the-art Python dashboard for exploring critical trade dependencies at the product level (HS6) across all countries over time. Built on CEPII BACI bilateral trade data, it surfaces where countries are dangerously reliant on concentrated or geopolitically risky suppliers — combining HHI concentration, geopolitical risk scores, and supply substitutability into a composite dependency metric. A portfolio project designed to showcase analytical depth and visualization craft.

## Core Value

Instantly reveal which products make a country vulnerable due to concentrated, geopolitically risky import sources — and how that exposure has evolved over time.

## Current Milestone: v2.0 Dashboard Redesign

**Goal:** Rebuild the pipeline to use correct HS revision data, replace the deterministic tier-based scoring with a fully empirical model, and redesign **Goal:** Rebuild the pipeline to use correct HS revision data, replace the deterministic tier-bade**Goal:** Rebuild the pipeline to use ata**Goal:** Rebuloa**Goal:** Rebuild the pipeline to use correct HS revision data, replace the deterministic tier-based scoring with a fully empirical model, and redesign **Goal:** Rebuild the pipeline to use correct HS revision data, replace the deterministic tier-bade**Goal:** Rebuild the pipeline to use ata**Goal:** Rebuloa**Goal:** Rebuild the pipeline to use correct HS revision data, replace the deterministic tier-based scoring with a fully empirical model, and redesign **Goal:** Rebuild the pitra**Goal:** Reankey flow diagrams, flag badges, "why it matters" context
- Time series with HS92 data for cross-year comparability, trend lines, sparklines in tables

## Requirements

### Validated (v1.0)

- [x] Automated BACI data download and ingestion pipeline (HS6, all countries, all years)
- [x] Pre-computed dependency metrics: HHI concentration, geopolitical risk, product essentiality, composite score
- [x] Country → Products view: select an importer, see its most vulnerable products ranked by dependency score
- [x] Product → Countries view: select an HS6 product, see which importers are most exposed
- [x] Geographic heatmaps (choropleths) showing dependency intensity across countries
- [x] Interactive charts (bar, line) and sortable ranked AG Grid tables
- [x] Dashboard built with Dash/Plotly with multi-page routing
- [x] Methodology page explaining scoring approach and data sources

### Active (v2.0)

- [ ] Pipeline downloads only HS92 + HS22 revisions from BACI (not all 7)
- [ ] Pipeline uses BACI metadata files (product_codes_HS*.csv, country_codes_V*.csv) instead of hand-built reference files
- [ ] Scoring uses fully empirical formula: HHI + geo-risk + global export HHI (substitutability proxy)
- [ ] Categorical flags (EU_CRM, USGS_Critical, Energy, Food, Pharma_API) as labels, not score drivers
- [ ] Country page: hero stat cards, scatter plot (HHI vs substitutability), top bilateral risk relationships, choropleth, restyled AG Grid
- [ ] Product page: concentration bars/donut, Sankey flow diagram, flag badges, choropleth, restyled AG Grid
- [ ] Time series: year slider, trend line charts, sparklines in table rows, HS92 with explanatory footnote
- [ ] Weight adjustment controls for the 3 empirical score components

### Out of Scope

- Export-side dependency analysis (focus is on import vulnerability)
- Real-time or live trade data feeds — BACI is retrospective annual data
- Mobile-optimized layout — desktop-first portfolio piece
- User authentication or multi-tenancy — single-user tool
- Product-level forecasting or predictive modeling — descriptive analytics only
- Force-directed network graph — dropped in v2 (low insight density for bilateral focus)
- Animated temporal evolution with play/pause — deferred

## Context

- **Data source:** CEPII BACI — reconciled bilateral trade data derived from UN COMTRADE. ~200 countries, ~5,000 HS6 products, 1995-2024. Requires CEPII registration for download.
- **HS revision strategy:**- **HS revision strategy:**- **HS revision strategy:**- **HS revision strategy:**- **HS revision stfor time series with cross-year comparability footnote.
- **Dependency scoring (v2):** Fully empirical composite of three dimensions:
  - **HHI (Herfindahl-Hirschman Index):** Concentration of import sources for a given product-importer pair
  - **Geopolitical risk:** Composite of governance indices (WGI) and sanctions data
  - **Global export HHI (substitutability):** How many countries produce this product worldwide — fewer producers = harder to substitute
- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIs, Semi- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIs, Semi-- - **Categorical flags:** EU CRM, USGS Critical Mineraletrics- **Catega p- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIs, Semi- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIs, Semi-- -nt- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIs, Semi- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIs, Semi-h lea- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Foolotly — - **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIs, Semi- **Categorical frd)- **Categorical flags:** EU CRM, USGS Critical Minerals, Energy, Food, Pharma APIscisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Dash/Plotly over Streamlit/Panel | Best visualization flexibility for maps, Sankey, and complex interactivity | Validated in v1 |
| Pre-compute metrics in pipeline | Dashboard can't query 200x5000x30 raw rows in real-time | Validated in v1 |
| BACI over raw COMTRADE | BACI is reconciled (fixes reporter/partner discrepancies), cleaner for analysis | Validated in v1 |
| HS92 for time series, HS22 for snapshots | BACI converts all years to each revision; HS92 covers 1995-2024 for comparability, HS22 has finest modern granularity | v2.0 |
| Download only HS92 + HS22 | Other 5 revisions unused — saves ~37GB of download and storage | v2.0 |
| Empirical score replacing tier system | v1 tiers predetermined risk by category (critical/important/standard) — circular, not empirical. v2 uses HHI + geo-risk + global export HHI, all data-derived | v2.0 |
| Flags replace tiers as labels | EU CRM, Energy, etc. as informational badges for filtering — don't distort the empirical score | Flags replace tiers as labels |s | Flags replace tiers as labels | EU CRM, Energy, etc. as informational badges for filtering — don't distort the empirical scorev2.0 |
| Drop network graph | Low insight density with 200+ nodes; scatter plot + Sankey serve bilateral analysis better | v2.0 |

---
*Last updated: 2026-03-26 — v2.0 milestone started*
