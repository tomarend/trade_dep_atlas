---
phase: 05-product-countries-view
plan: 02
subsystem: ui

requires:
  - phase: 05-product-countries-view
    plan: 01
    provides: product-data-store, importer-table-container, product-map-container placeholders, get_importer_scores query

provides:
  - AG Grid importer table (id="importer-table") with 7 columns, sorting, filtering, conditional formatting
  - Choropleth world map (id="product-choropleth") with YlOrRd color scale showing dependency score by country
  - Callbacks to populate table and map from product-data-store

affects: [05-03]

tech-stack:
  added: []
  patterns:
    - AG Grid pattern mirrors country page's product-table for consistency
    - Choropleth uses YlOrRd (not RdYlGn_r) to distinguish dependency magnitude from geo risk direction

key-files:
  modified:
    - dashboard/pages/product.py

key-decisions:
  - "YlOrRd colorscale for dependency score (distinct from country page's RdYlGn_r for geo risk)"
  - "AG Grid uses same defaultColDef and dashGridOptions as country page for consistency"
  - "Choropleth title includes product description for context"

component-ids:
  - importer-table (AgGrid)
  - product-choropleth (Graph)
  - product-map-container (Div, now populated by callback)

patterns-established:
  - "Importer table callback simply passes store data through (pre-sorted by query)"

requirements-completed: [PRDV-02, PRDV-03, PRDV-05]

duration: 3min
completed: 2026-03-23
---

# Plan 05-02: AG Grid Importer Table & Choropleth Map

**Product page now shows ranked importer table with conditional formatting and choropleth world map colored by dependency score, completing the main analytical visualizations.**
