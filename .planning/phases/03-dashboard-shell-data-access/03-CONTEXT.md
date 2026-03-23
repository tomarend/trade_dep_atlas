# Phase 3: Dashboard Shell & Data Access - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up the Dash multi-page application shell with left-sidebar navigation, shared data access layer querying DuckDB, methodology page with full content, and appropriate loading/error states. Requirements: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05.

</domain>

<decisions>
## Implementation Decisions

### Visual Theme & Information Density
- **DBC theme:** Light theme — use `dash-bootstrap-components` LUX or Flatly (light, clean, report-style)
- **Risk color convention:** Red = high risk (conventional; applies to choropleth color scales, score badges, conditional table formatting in later phases)
- **Information density:** Comfortable spacing — adequate whitespace, readable typography; not Bloomberg-dense
- **Chart integration:** Charts embedded — Plotly chart backgrounds match the page background; no visible card border/shadow around chart containers. Use `plotly_white` template aligned to the light theme.

### Navigation Layout
- **Structure:** Left collapsible sidebar (not top navbar) — allows for future pages in Phases 4–6 without overflow
- **Page labels:**
  - Country Exposure (`/country`)
  - Product Risk (`/product`)
  - About (`/about`)
- **Active page:** Highlighted link in sidebar
- **Brand/title:** "DependencyAtlas" in sidebar header
- **Data freshness indicator:** Footer element — shows latest data year and year range (e.g. "Data: BACI 1995–2022"). Pulled live from DuckDB on app startup, displayed on all pages.

### Methodology Page (About)
- **Content depth:** Full content now — not stubs. Write actual explanations for each section.
- **Formula rendering:** MathJax via `dash-mdown` or `dcc.Markdown` with MathJax CDN injection. Render:
  - HHI: $HHI = \sum_{i=1}^{n} s_i^2$ where $s_i$ is supplier $i$'s share of import value
  - Composite: $\text{score} = w_1 \cdot HHI + w_2 \cdot \text{geo\_risk} + w_3 \cdot \text{essentiality}$
- **Layout:** Tabbed sections using `dbc.Tabs`:
  1. **HHI Concentration** — formula, interpretation, normalization (0–1 scale), why HHI vs alternatives
  2. **Geopolitical Risk** — WGI 6 dimensions, Freedom House fallback for gaps (Taiwan/Kosovo/Palestine), GSDB sanctions multiplier, formula `geo_risk = governance_risk × (1 + sanctions_intensity)`
  3. **Essentiality** — three-tier structure (Critical 0.85–1.0 / Important 0.45–0.7 / Standard 0.1–0.3), within-tier gradient via global export HHI, EU CRM 2023 + USGS 2022 sources
  4. **Data Sources** — BACI trade data (CEPII), WGI (World Bank), Freedom House, GSDB (Drexel/Stanford), EU CRM list, USGS Critical Minerals list. Year range and latest year pulled live from DuckDB.

### Data Access Layer
- **DuckDB path:** `data/dashboard.duckdb` (relative to project root, configurable via `pipeline.yaml`)
- **Connection strategy:** Single read-only DuckDB connection opened at app startup, stored in a module-level singleton (`dashboard/data.py`). Not per-request connections — DuckDB read-only connections are thread-safe.
- **Freshness query:** On startup, query `SELECT MIN(year), MAX(year) FROM dependency_scores` — store result in module-level cache, expose as `get_year_range() -> tuple[int, int]`.
- **Country list query:** `SELECT iso3, name FROM countries ORDER BY name` — cached at startup for sidebar/dropdowns in later phases.
- **Error handling:** If `dashboard.duckdb` not found at startup → render error page with message: "No data found. Run `python -m pipeline` to build the database, then restart the dashboard."

### Empty / Loading States
- **Default landing state:** Pre-load a default selection on first visit. Country Exposure page auto-loads the country with the highest mean composite score across all products (i.e. most exposed country overall). Product Risk page auto-loads the product with the highest mean composite score (most critical product globally). This is computed once at startup and cached.
- **Loading indicator:** Component-level `dcc.Loading` spinners — each chart/table/map has its own `dcc.Loading` wrapper with `type="circle"`. No page-level loading takeover.
- **No-data error:** Error page (not traceback) — clean `dbc.Alert` with instructions to run pipeline. App must NOT crash with Python exception visible to user.
- **Layout during loading:** Component placeholders visible (empty containers with correct dimensions) while spinner is shown — prevents layout shift.

### App Structure
- **Entry point:** `dashboard/app.py` — creates Dash app instance, registers pages, injects MathJax CDN
- **Pages:** `dashboard/pages/country.py`, `dashboard/pages/product.py`, `dashboard/pages/about.py`
- **Shared layout:** `dashboard/layout.py` — sidebar + content area + footer
- **Data layer:** `dashboard/data.py` — DuckDB connection singleton, cached queries
- **Assets:** `dashboard/assets/` — custom CSS if needed for sidebar styling
- **Deployment:** `gunicorn dashboard.app:server` — `server = app.server` exposed in `app.py`
- **Docker:** `Dockerfile` at project root — Python 3.12, installs project, exposes port 8050, CMD gunicorn

### Claude's Discretion
- Specific DBC theme choice between LUX and Flatly (pick whichever renders cleaner with sidebar layout)
- Sidebar collapse behaviour on narrow screens
- Exact MathJax CDN injection method (external_scripts in Dash app constructor)
- Default country/product selection query optimisation (can be a simple pre-computed scalar at startup)

</decisions>

<deferred_ideas>
## Deferred Ideas

*(Captured during discussion — not in scope for Phase 3)*

- None surfaced during discussion.

</deferred_ideas>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Prior Phase Context
- `.planning/phases/02-scoring-pipeline-storage/02-CONTEXT.md` — DuckDB schema (dependency_scores fact table, countries dim, products dim), column names, star schema structure
- `.planning/phases/01-data-pipeline-ingestion/01-CONTEXT.md` — pipeline.yaml config structure, data directory layout

### Project Context
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — DASH-01 through DASH-05 (this phase's requirements)

### Key Dependencies (already installed in pyproject.toml)
- `dash>=4.0.0` — multi-page app support via `dash.register_page()`
- `dash-bootstrap-components>=2.0.4` — sidebar layout, DBC theme
- `plotly>=6.6.0` — `plotly_white` template
- `duckdb>=1.5.0` — read-only connection
- `gunicorn>=25.1.0` — production server

</canonical_refs>

<code_context>
## Existing Code Insights

### DuckDB Schema (from pipeline/export.py)
Tables available in `data/dashboard.duckdb`:
- **`dependency_scores`** (fact): `importer_iso3, hs6, year, exporter_iso3, value_usd, supplier_share, hhi, exporter_geo_risk, basket_geo_risk, essentiality_score, essentiality_tier, crm_listed_since, composite_score`
- **`countries`** (dim): `iso3, name, region, continent, is_reexport_hub`
- **`products`** (dim): built from essentiality Parquet — hs6, description, hierarchy, tier, score, global HHI

### Existing Pipeline Modules (do NOT modify in this phase)
- `pipeline/countries.py` — `CountryRecord`, `load_country_mapping()` — reusable for country name lookups
- `pipeline/export.py` — `build_duckdb()` / `run_duckdb_export()` — already complete
- `pipeline/__main__.py` — CLI orchestrator — already complete

### No Existing Dashboard Code
The `dashboard/` package does not yet exist. Phase 3 creates it from scratch.

</code_context>
