# Phase 8: Dashboard Redesign — Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

---

<domain>
## Phase Boundary

Country page becomes insight-first: 4 hero stat cards, a scatter plot (HHI × substitutability), and a bilateral risk panel are added. Product page gains concentration bars and flag badges; the network graph is removed. All "essentiality" terminology is replaced dashboard-wide. No new pages, no new pipeline work.

</domain>

<decisions>
## Implementation Decisions

### A — Hero Cards (CNTV-08)

- **D-01:** Replace the existing 4 summary cards with 4 new hero stat cards showing:
  1. Total products (count of HS6 products for the selected importer/year)
  2. Count above risk threshold — threshold = **0.7** (hard-coded as `RISK_THRESHOLD = 0.7` in `dashboard/data.py`; not user-adjustable)
  3. Highest-risk product name (description of the HS6 with the highest composite score)
  4. Max composite score (the actual value of that top product)
- **D-02:** The existing country-level overview radar chart (avg HHI / Geo Risk / Substitutability) is **kept**. Position it alongside the 4 hero cards in the same row — e.g. 4 stat cards on the left (`md=8` split 2×2) and radar on the right (`md=4`).

### B — Scatter Plot (CNTV-09)

- **D-03:** Top 200 products by composite score, x=HHI, y=`substitutability_score` (= `sqrt(global_export_hhi)`), marker size = `log(total_import_value_usd)` (sum of `value_usd` across all exporters for that hs6/importer/year), marker color = `composite_score` using cool-to-hot gradient (green→yellow→orange→red, same as rest of dashboard).
- **D-04:** Placement: **between the hero card row and the weight controls / AG Grid** — full-width section, labelled "Product Risk Landscape".
- **D-05:** Click interaction: **tooltip only** — hovering shows product description, HS6 code, HHI, substitutability, composite score. No navigation or grid selection side-effect on click.
- **D-06:** New data query needed: `get_scatter_data(importer_iso3, year)` → returns top-200 rows with `{hs6, description, hhi, substitutability_score, composite_score, total_import_value_usd}`. `total_import_value_usd` = `SUM(value_usd)` aggregated from `dependency_scores` per hs6; `substitutability_score` joined from `products.global_export_hhi` via sqrt.

### C — Bilateral Risk Panel (CNTV-10)

- **D-07:** Placement: **below the scatter plot, above the weight controls** — keeping all country-level overview charts grouped before the product-level table.
- **D-08:** Content: top-10 source (exporter) countries ranked by `SUM(supplier_share × composite_score)` aggregated across all products for that importer/year. Displayed as horizontal bar chart — bar width = weighted risk contribution, bars colored by the exporter's mean `exporter_geo_risk`.
- **D-09:** Flag icons: **`flagcdn.com` PNG images** — `https://flagcdn.com/w20/{iso2_lower}.png` — displayed inline before country name. Requires ISO2 code; derive from ISO3 via a lookup or `countries` table if ISO2 is available there.
- **D-10:** New data query needed: `get_bilateral_risk(importer_iso3, year)` → returns top-10 rows with `{exporter_iso3, exporter_name, weighted_risk_contribution, mean_geo_risk}` sorted descending by `weighted_risk_contribution`.

### D — Product Page: Concentration Bars (PRDV-07)

- **D-11:** New horizontal bar chart showing top exporters for the selected product, bar width ∝ `supplier_share` (%), bars **colored by `exporter_geo_risk`** using the **cool-to-hot gradient** (green→yellow→orange→red) — consistent with risk color encoding used elsewhere on the dashboard.
- **D-12:** Placement: **immediately below the product summary cards / score decomposition** (near top of the detail section, before the choropleth map). This is the primary supplier concentration view.
- **D-13:** Data source: existing `get_supplier_breakdown(hs6, year)` — already returns `exporter_name`, `supplier_share`, `exporter_geo_risk`. No new query needed.

### E — Product Page: Flag Badges (PRDV-08)

- **D-14:** Display flag badges below the product name / title area. One badge per flag in the `flags` list. Active flags for this phase: `crm_listed` (show year from `crm_listed_since` if available), `energy`, `pharma`, `semiconductor`, `strategic_mineral`. `fertilizer`, `hs22_only` also renderable if present.
- **D-15:** Badge style: small `dbc.Badge` components inline, color-coded per category (e.g. `crm_listed` = danger/red, `energy` = warning/amber, `pharma` = info/blue, `semiconductor` = secondary, `strategic_mineral` = dark). Agent's discretion on exact color mapping.
- **D-16:** Data source: `flags` and `crm_listed_since` already returned by `get_product_summary()`.

### F — Network Graph Removal (PRDV-09)

- **D-17:** Remove `import dash_cytoscape as cyto` from `dashboard/pages/product.py`.
- **D-18:** Remove `html.Div(id="product-network-container", ...)` from the layout.
- **D-19:** Remove the `update_network()` callback and all associated code.
- **D-20:** Remove `dash-cytoscape` from `pyproject.toml` dependencies.
- **D-21:** Verify no import errors on startup after removal — `dash-cytoscape` is the only cytoscape reference.

### G — Terminology Replacement (DASH-06, CNTV-11)

- **D-22:** Weight slider label: "Essentiality" → "Substitutability" on both country and product pages. Already partially done in Phase 7 (slider uses `weight-ess` id but label may still read "Essentiality").
- **D-23:** AG Grid column formerly labelled "Essentiality Tier": rename to **"Flags"**, display the `flags` list (comma-joined strings). This applies in both the country page drill-down table and the product page importer table.
- **D-24:** About page "Essentiality" tab: **full rewrite**:
  - Rename tab to "Substitutability"
  - Replace three-tier explanation with `sqrt(global_export_hhi)` formula and economic rationale (concentration of global supply, HHI linearised via sqrt)
  - Update composite formula to: $\text{score} = w_1 \cdot HHI + w_2 \cdot \text{geo\_risk} + w_3 \cdot \sqrt{HHI_{global}}$
  - Describe the 8 canonical flags (crm_listed, energy, fertilizer, food, pharma, semiconductor, strategic_mineral, hs22_only) and their sources (EU CRM 2023, USGS 2022, HS chapter logic)
  - Remove any mention of Critical/Important/Standard tiers
- **D-25:** Grep for any remaining "essentiality" strings in UI-visible text (chart titles, card labels, tooltip text, page subtitles) and replace with "substitutability" or remove. Python variable names / internal IDs do not need to change (`weight-ess` id, `w_ess` variable are internal — only visible text matters).

### Agent's Discretion

- Exact badge color mapping per flag type (D-15)
- ISO3 → ISO2 conversion approach for flagcdn.com (lookup dict or DB column)
- Scatter plot height (recommend ~400px) and whether to show a color bar legend
- Whether to add section headings ("Key Supply Risk Sources", "Product Risk Landscape") above new chart panels

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current Dashboard Implementation
- `dashboard/pages/country.py` — existing country page (610 lines); summary cards at line 269, existing layout structure
- `dashboard/pages/product.py` — existing product page (774 lines); network graph at lines 732–773, cytoscape import at line 11
- `dashboard/data.py` — data access layer; existing queries: `get_product_scores()`, `get_country_summary()`, `get_supplier_breakdown()`, `get_product_summary()`, `get_importer_scores()`
- `dashboard/pages/about.py` — About/methodology page with Essentiality tab to be rewritten

### Schema & Data Layer
- `.planning/phases/07-pipeline-scoring-rework/07-CONTEXT.md` — authoritative source for new schema: `substitutability_score = sqrt(global_export_hhi)`, 8 flags, no tiers, BACI country mapping, products table columns
- `.planning/phases/03-dashboard-shell-data-access/03-CONTEXT.md` — LUX theme, `plotly_white`, DBC patterns, data singleton

### Project Context
- `.planning/REQUIREMENTS.md` — CNTV-08, CNTV-09, CNTV-10, CNTV-11, PRDV-07, PRDV-08, PRDV-09, DASH-06

### Current DuckDB Schema (as of Phase 7 — NOTE: DB may still be pre-Phase-7 schema)
- `dependency_scores`: `importer_iso3, hs6, year, exporter_iso3, value_usd, supplier_share, hhi, exporter_geo_risk, basket_geo_risk, essentiality_score (legacy), composite_score`
- `products`: `hs6, hs2, hs4, description, global_export_hhi, crm_listed_since` (post-Phase-7 will also have `flags VARCHAR[], hs22_only BOOLEAN`)
- `countries`: iso3, name, region, continent (ISO2 availability TBD — check before planning `flagcdn.com` approach)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `update_summary_cards()` callback in `country.py` — replace in-place with new hero card logic; radar figure generation reusable
- `get_supplier_breakdown()` in `data.py` — direct input for concentration bars (D-13), no new query
- `get_product_summary()` in `data.py` — already returns `flags` and `crm_listed_since` for badges (D-16)
- `dbc.Badge` — already used in project; use for flag badges (D-14)
- Cool-to-hot color scale already applied via `plotly` `RdYlGn_r` or inline `[[0, '#22c55e'], [0.5, '#f59e0b'], [1, '#ef4444']]` — use consistently

### New Queries Required
- `get_scatter_data(importer_iso3, year)` — join `dependency_scores` (aggregated) + `products` for top-200 rows
- `get_bilateral_risk(importer_iso3, year)` — aggregate `SUM(supplier_share × composite_score)` grouped by `exporter_iso3`

### Integration Points
- Both new queries go in `dashboard/data.py`
- Scatter and bilateral panels are new `html.Div(id=...)` slots in `country.py` layout, populated by new callbacks
- `pyproject.toml` — remove `dash-cytoscape` dependency
- `flagcdn.com` — external CDN, no install needed; just `html.Img(src=f"https://flagcdn.com/w20/{iso2}.png")`

</code_context>

<specifics>
## Specific Ideas

- Hero card row layout: 4 stat cards as a 2×2 grid (`dbc.Row` of 2 `dbc.Col md=3` pairs) + radar chart in `dbc.Col md=4` — total width = 4×3 + 4 + padding ≈ 16 cols (use `md=3` × 4 + `md=4` × 1 = bootstrap fits in 12-col by wrapping or adjust to `md=2` × 4 + `md=4`)
- Scatter tooltip should show: HS6 code, product description (truncated to 60 chars), Composite: X.XXX, HHI: X.XXX, Substitutability: X.XXX
- Bilateral panel bar labels: flag icon + country name on y-axis, weighted risk score value shown at bar end
- Concentration bars on product page: show top-15 exporters max (truncate if more), x-axis = share %, y-axis = country name with flag icon

</specifics>

<deferred>
## Deferred Ideas

### Reviewed Todos (not folded)
- **Fix HS chapter headings in product selector** (`2026-03-26-fix-hs-chapter-headings-in-product-selector.md`) — resolved by Phase 7's authoritative BACI `product_codes_HS*.csv` mapping, which provides proper chapter descriptions. Closing as superseded.

</deferred>

---

*Phase: 08-dashboard-redesign*
*Context gathered: 2026-03-27*
