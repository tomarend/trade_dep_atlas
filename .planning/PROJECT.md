# Trade Critical Dependencies Dashboard

## What This Is

A state-of-the-art Python dashboard for exploring critical trade dependencies at the product level (HS6) across all countries over time. Built on CEPII BACI bilateral trade data, it surfaces where countries are dangerously reliant on concentrated or geopolitically risky suppliers — combining HHI concentration, geopolitical risk scores, and product essentiality into a composite dependency metric. A portfolio project designed to showcase analytical depth and visualization craft.

## Core Value

Instantly reveal which products make a country vulnerable due to concentrated, geopolitically risky import sources — and how that exposure has evolved over time.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Automated BACI data download and ingestion pipeline (HS6, all countries, all years)
- [ ] Pre-computed dependency metrics: HHI concentration, geopolitical risk (sanctions + governance indices), product essentiality, composite score
- [ ] Country → Products view: select an importer, see its most vulnerable products ranked by dependency score
- [ ] Product → Countries view: select an HS6 product, see which importers are most exposed
- [ ] Time series exploration: see how dependency scores evolve over years, animated or slider-based
- [ ] Geographic heatmaps showing dependency intensity across countries
- [ ] Sankey / network flow diagrams showing trade concentration for a product or country
- [ ] Interactive charts (bar, line, scatter) and sortable ranked tables
- [ ] Dashboard built with Dash/Plotly for rich interactivity and visual polish
- [ ] Deployable architecture: runs locally, can be hosted later

### Out of Scope

- Export-side dependency analysis (focus is on import vulnerability) — keeps scope tight for v1
- Real-time or live trade data feeds — BACI is retrospective annual data
- Mobile-optimized layout — desktop-first portfolio piece
- User authentication or multi-tenancy — single-user tool
- Product-level forecasting or predictive modeling — descriptive analytics only

## Context

- **Data source:** CEPII BACI — reconciled bilateral trade data derived from UN COMTRADE. ~200 countries, ~5,000 HS6 products, ~20 years. Requires CEPII registration for download.
- **Dependency scoring:** Composite of three dimensions:
  - **HHI (Herfindahl-Hirschman Index):** Concentration of import sources for a given product-importer pair
  - **Geopolitical risk:** Composite of trade sanctions exposure and governance indices (Freedom House, V-Dem, or similar)
  - **Product essentiality:** How critical a product category is (critical raw materials, energy, pharma, food, semiconductors score higher)
- **Performance strategy:** Pre-compute all dependency metrics in a data pipeline. Dashboard serves aggregated results, not raw trade flows. This keeps the UI responsive even with full country/product coverage.
- **Target audience:** Portfolio showcase — must be visually impressive and analytically rigorous.

## Constraints

- **Data access**: BACI requires CEPII registration — automated download must handle authentication
- **Data volume**: Raw BACI data is large (multi-GB across years) — pipeline must be efficient with memory
- **Framework**: Dash/Plotly — chosen for visualization richness and interactivity
- **Language**: Python end-to-end (pipeline + dashboard)
- **Deployment**: Local-first, but architecture should support hosting (e.g., on Render, Railway, or similar)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Dash/Plotly over Streamlit/Panel | Best visualization flexibility for maps, Sankey, network graphs, and complex interactivity | — Pending |
| Pre-compute metrics in pipeline | Dashboard can't query 200×5000×20 raw rows in real-time; pre-aggregation keeps UI snappy | — Pending |
| Composite dependency score (HHI + geo risk + essentiality) | Single-dimensional measures miss the picture — high concentration from a friendly ally differs from a geopolitical rival | — Pending |
| All countries, all HS6 products | No upfront filtering — essentiality scores surface the interesting products naturally | — Pending |
| BACI over raw COMTRADE | BACI is reconciled (fixes reporter/partner discrepancies), cleaner for analysis | — Pending |

---
*Last updated: 2026-03-17 after initialization*
