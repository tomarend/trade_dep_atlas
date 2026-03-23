# Phase 4: Country→Products View - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Primary analytical view: user selects an importing country and explores its product vulnerabilities through interactive AG Grid tables, choropleth maps, radar/bar charts, score decomposition cards, and adjustable weight controls. Requirements: CNTV-01, CNTV-02, CNTV-03, CNTV-04, CNTV-05, CNTV-06, SCOR-05, VIZZ-01, VIZZ-03, VIZZ-04, VIZZ-05.

</domain>

<decisions>
## Implementation Decisions

### Page Layout & Information Flow
- **Layout pattern:** Top-down vertical scroll — country selector at top, summary cards, then product table, then drill-down detail below. No tabs or grid layout.
- **Above the fold:** Country selector dropdown + summary cards visible without scrolling. Product table starts just below with breathing room.
- **Summary cards:** One large "Overall Exposure Score" card with color-coded badge (red/amber/green based on score) + 3 smaller decomposition cards (Concentration/HHI, Geo Risk, Essentiality Profile). All display country-level aggregated values.
- **Product table columns (main view):** HS6 Code, Product Description, Composite Score, Essentiality Tier — keep it lean. Sub-scores (HHI, geo risk, essentiality) only on drill-down.

### Product Drill-Down Interaction
- **Drill-down content:** Full analytical panel showing:
  - Supplier table: Country name, Share %, Trade Value (USD), Geo Risk Score — sorted by share descending
  - Choropleth map: Suppliers colored by geopolitical risk score
  - Radar/spider chart: Score decomposition for that product (HHI, geo risk, essentiality)
  - Bar chart: Supplier share concentration visualization
- **Interaction pattern:** Claude's discretion — choose between inline row expansion, detail section below the table, or side panel based on what works best with AG Grid and the data density.

### Weight Adjustment Controls
- **Location:** Collapsible panel above the product table, triggered by a "Customize Weights" button. Collapsed by default — only analysts who want to customize weights see it.
- **Weight constraint:** Sum constrained to 1.0 — moving one slider proportionally adjusts the others (three sliders for HHI, geo risk, essentiality).
- **Update behavior:** Debounced — scores recalculate 300–500ms after the slider stops moving. No "Apply" button; feels immediate.

### Score Summary Cards & Charts
- **Radar chart placement:** Two levels — country-level overview radar in the summary cards area + per-product radar on drill-down. Country-level radar shows average HHI, geo risk, and essentiality across all products for that country.
- **Color scheme:** Claude's discretion — likely a cool-to-hot gradient for risk severity (green→yellow→orange→red) applied consistently across score badges, table conditional formatting, and choropleth.

### AG Grid Table Behavior
- **Row rendering:** Virtual scroll — no pagination. All rows rendered on demand via AG Grid's virtual row model. Scroll through the full product list seamlessly.
- **Filtering:** Sort by any column + column-level filters using AG Grid's built-in column filter icons. Range filtering on numeric score columns, text matching on product descriptions.

### Claude's Discretion
- Drill-down interaction pattern (inline expand vs detail section below table vs side panel) — pick what works best with AG Grid and data density
- Color scheme for risk visualization (likely cool-to-hot gradient: green→yellow→orange→red)
- Choropleth map projection and interaction behavior (zoom, tooltips)
- Weight recomputation strategy (client-side recalculation vs server-side callback) — choose based on data volume and responsiveness
- Specific AG Grid configuration (column definitions, default sort, theme integration with LUX)

</decisions>

<specifics>
## Specific Ideas

- Country-level radar chart in summary area provides at-a-glance risk profile before user scrolls to table
- Weight sliders use proportional adjustment (not independent) — when user increases HHI weight, geo risk and essentiality weights decrease proportionally to maintain sum = 1.0
- Drill-down supplier table + choropleth map + radar chart + bar chart all appear together for a selected product — comprehensive single-product analysis
- AG Grid with virtual scroll handles large product lists (~5,000+ HS6 codes per country) without pagination friction
- Column-level filters allow analysts to quickly narrow to e.g. "essentiality tier = Critical" or "composite score > 0.7"

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Prior Phase Context
- `.planning/phases/03-dashboard-shell-data-access/03-CONTEXT.md` — LUX theme, sidebar layout, data access layer, DBC patterns, `plotly_white` template
- `.planning/phases/02-scoring-pipeline-storage/02-CONTEXT.md` — DuckDB schema (dependency_scores fact table, countries dim, products dim), composite score formula, sub-score ranges

### Project Context
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — CNTV-01 through CNTV-06, SCOR-05, VIZZ-01, VIZZ-03, VIZZ-04, VIZZ-05

### Key Dependencies (already installed in pyproject.toml)
- `dash>=4.0.0` — multi-page app, callbacks
- `dash-bootstrap-components>=2.0.4` — LUX theme, cards, collapse, sliders
- `dash-ag-grid` — AG Grid component with virtual scroll, column filters
- `plotly>=6.6.0` — choropleth, radar chart, bar chart (`plotly_white` template)
- `duckdb>=1.5.0` — read-only queries via `dashboard/data.py` singleton

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard/data.py`: DuckDB singleton with `get_year_range()`, `get_country_list()`, `get_default_country()`, `get_default_product()` — country list and defaults already cached at startup
- `dashboard/layout.py`: Sidebar layout (width=2) with NavLinks — Phase 4 page slot already exists at `/country`
- `dashboard/pages/country.py`: Stub page registered at `/country` — replace entirely with full implementation

### Established Patterns
- DBC card components for content containers (`dbc.Card`, `dbc.CardBody`)
- `dcc.Loading` with `type="circle"` for component-level loading spinners
- `plotly_white` chart template for all Plotly figures
- Inter font family via Google Fonts CDN
- Module-level caching for startup queries (avoid repeated DB calls)

### Integration Points
- `dashboard/data.py` → add new query functions for product scores, supplier breakdowns, score aggregates by country
- `dashboard/pages/country.py` → full page rewrite with AG Grid table, summary cards, charts, callbacks
- `pipeline/export.py` schema → `dependency_scores` table columns: `importer_iso3, hs6, year, exporter_iso3, value_usd, supplier_share, hhi, exporter_geo_risk, basket_geo_risk, essentiality_score, essentiality_tier, crm_listed_since, composite_score`
- `countries` dimension table → `iso3, name, region, continent, is_reexport_hub`
- `products` dimension table → HS6/HS4/HS2 hierarchy, description, essentiality fields

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-country-products-view*
*Context gathered: 2026-03-23*
