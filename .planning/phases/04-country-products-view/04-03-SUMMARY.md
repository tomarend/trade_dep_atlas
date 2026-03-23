---
phase: 04-country-products-view
plan: 03
subsystem: ui

requires: [04-01, 04-02]
provides:
  - Product drill-down panel triggered by AG Grid row selection
  - Supplier breakdown table (country, share%, value USD, geo risk, region)
  - Choropleth world map of suppliers colored by geo risk (RdYlGn_r scale, natural earth projection)
  - Per-product radar/spider chart showing HHI, Geo Risk, Essentiality score decomposition
  - Supplier share bar chart (top 10 suppliers, colored by geo risk)
  - Country-level overview radar chart in summary cards area

affects: [phases 5-6]

tech-stack:
  added: []
  patterns:
    - plotly.express.choropleth with RdYlGn_r colorscale for geo risk maps
    - plotly.graph_objects.Scatterpolar for radar/spider charts
    - All charts use template="plotly_white" and font_family="Inter"
    - All dcc.Graph components use config={"displayModeBar": False}

key-files:
  modified:
    - dashboard/pages/country.py
    - dashboard/assets/custom.css

key-decisions:
  - "Drill-down renders all 4 visualizations in a single callback (render_drilldown) — simpler than separate callbacks"
  - "Top 10 suppliers shown in bar chart to prevent chart overcrowding"
  - "Country overview radar in summary cards shows avg HHI/geo/essentiality at a glance"
  - "drilldown-header has blue left border (#2563eb) as visual accent"

component-ids:
  - supplier-choropleth (Graph — rendered inside drill-down)
  - product-radar (Graph — rendered inside drill-down)
  - supplier-bar (Graph — rendered inside drill-down)
  - country-overview-radar (Graph — rendered inside summary cards)

patterns-established:
  - "Drill-down pattern: AG Grid selectedRows → callback → query supplier data → render panel"
  - "Chart color convention: RdYlGn_r for risk (red=high, green=low), #2563eb blue for neutral accents"
  - "Radar fillcolor: rgba(37, 99, 235, 0.15) with #2563eb line"
---
