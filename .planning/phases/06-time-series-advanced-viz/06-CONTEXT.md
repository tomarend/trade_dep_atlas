# Phase 6: Time Series & Advanced Visualizations - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Temporal analysis and advanced visualizations: global year slider, trend line charts in drill-downs, Sankey flow diagrams, and force-directed network graph. Requirements: TIME-01, TIME-02, TIME-03, VIZZ-02, VIZZ-06.

</domain>

<decisions>
## Implementation Decisions

### Year Selection & Page Integration
- **Global sidebar year slider:** One `dcc.Slider` placed in the sidebar below the nav links, above the footer. Affects all pages — changing year re-queries all data.
- **Simple continuous slider:** Range 1995–2024, tick marks at 5-year intervals, defaults to latest year (max_year). No play/pause animation (deferred to v2/TEMP-01).
- **Update on slider release:** Fire query only when user releases the handle, not while dragging. Use Dash slider's default `mouseup` behavior (not `updatemode="drag"`).
- **Active year label:** Display "Viewing: YYYY" near the slider for clarity.
- **Selected year preserved across navigation:** When user cross-links from country→product or vice versa, the selected year carries over via the sidebar state.

### Trend Charts
- **Embedded in existing drill-downs:** No separate Trends page. Trend chart appears in the drill-down panel on both Country Exposure and Product Risk pages.
- **Composite line by default, toggleable sub-score overlays:** Starts with one composite score line, user can check/uncheck HHI, geo risk, essentiality overlays via `dcc.Checklist`.
- **Gap handling:** Missing data shown as gaps in the line via `None` values in Plotly. No interpolation — honest representation.
- **Selected year as vertical reference line:** "You are here" dashed vertical line on the trend chart at the currently selected year.

### Sankey Diagram
- **Product-focused:** Sankey on the Product Risk page. Shows supplier→importer trade flows for the selected product and year.
- **Top 10 suppliers with "Other" aggregation:** Always predictable, readable count. Suppliers ranked by `supplier_share`, the rest summed into "Other".
- **Always visible on Product Risk page:** Positioned after the choropleth map. Not collapsed, not in drill-down. A standalone visualization section.

### Network Graph
- **Product-focused:** On the Product Risk page alongside the Sankey. Nodes = countries (both importers and exporters), edges = trade flows for the selected product.
- **Top-N filtering:** Same approach as Sankey — top 10 suppliers shown, keeping the graph readable and performant.
- **Force-directed layout:** Use Plotly `go.Scatter` with spring layout positions computed via networkx. Nodes sized by trade volume, colored by geo risk.

### Claude's Discretion
- Trend chart height and exact placement within drill-down panel
- Network graph exact layout algorithm parameters (spring constant, iterations)
- Sankey color encoding specifics (geo risk gradient vs categorical)
- How "Other" aggregation node is styled in Sankey/network
- Exact tick mark positions on year slider

</decisions>

<deferred>
## Deferred Ideas

- **Country-focused Sankey:** Supplier→product flows for a selected country (beyond Phase 6 scope)
- **Play/pause animation:** TEMP-01, already captured in v2 requirements
- **Interactive network pruning slider:** Dynamic edge threshold control (overkill for v1)

</deferred>

<specifics>
## Specific Ideas

- Year slider in sidebar means it's always visible, acts as a global filter — conceptually similar to how BI tools handle time dimension
- Trend charts provide the "how did we get here" narrative when a user drills into a specific product
- Sankey diagram reveals the flow structure that the numbers in the table can't show — where the trade actually moves
- Network graph shows the structural position of countries in the trade graph for a product — hub/spoke patterns become visible
- All new visualizations respect existing patterns: `plotly_white` template, Inter font, consistent color coding

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Prior Phase Context
- `.planning/phases/04-country-products-view/04-CONTEXT.md` — Drill-down pattern, weight sliders, AG Grid, score color coding
- `.planning/phases/03-dashboard-shell-data-access/03-CONTEXT.md` — LUX theme, sidebar layout, data access layer patterns

### Key Existing Files
- `dashboard/layout.py` — Sidebar structure (year slider goes here)
- `dashboard/data.py` — DuckDB singleton, all query functions accept `year` parameter
- `dashboard/pages/country.py` — Country page with drill-down panel (trend chart goes in drill-down)
- `dashboard/pages/product.py` — Product page with choropleth (Sankey + network go after map)

### Key Dependencies (already installed)
- `dash>=4.0.0` — multi-page app, callbacks, dcc.Slider
- `plotly>=6.6.0` — Sankey (`go.Sankey`), network (`go.Scatter`), line charts
- `networkx` — May need to install for force-directed layout computation

</canonical_refs>

<code_context>
## Relevant Code Patterns

### Data Layer
All query functions in `dashboard/data.py` already accept `year` parameter with default to latest year. The year slider just needs to pass the selected year to these functions.

### Sidebar Layout
`dashboard/layout.py` — `_build_sidebar()` returns a `dbc.Col` with brand, nav links. Year slider inserts between nav and footer area.

### Callback Pattern
Both pages use `dcc.Store` as intermediary: selector change → load data to store → downstream callbacks consume store. Year slider becomes an additional Input to the store-loading callbacks.

### Cross-Link Pattern
URL query params (`?iso3=XXX`, `?hs6=XXXXXX`) for cross-page navigation. Year state lives in sidebar dcc.Store (not URL) since it's persistent across all pages.

</code_context>
