---
phase: 05-product-countries-view
plan: 01
subsystem: ui, data

requires:
  - phase: 04-country-products-view
    provides: Data access patterns, AG Grid patterns, summary card layout, country page as mirror template

provides:
  - Three product-centric query functions in dashboard/data.py (get_product_list, get_importer_scores, get_product_summary)
  - Full Product Risk page layout at /product with cascading HS2->HS4->HS6 dropdowns, 4 summary cards, radar chart, dcc.Store
  - Placeholder containers for AG Grid importer table and choropleth map (Plan 02)

affects: [05-02, 05-03]

tech-stack:
  added: []
  patterns:
    - Cascading dropdown pattern (HS2->HS4->HS6) with cached product list
    - Product-centric DISTINCT subquery pattern for importer scores

key-files:
  modified:
    - dashboard/data.py
    - dashboard/pages/product.py

key-decisions:
  - "get_product_list is @lru_cache(maxsize=1) since product catalog is static"
  - "get_importer_scores uses DISTINCT subquery to collapse per-exporter rows to per-importer"
  - "Summary cards show global averages across all importers for selected product"
  - "Component IDs prefixed with 'product-' to avoid conflicts with country page"

component-ids:
  - product-hs2-selector (Dropdown)
  - product-hs4-selector (Dropdown)
  - product-hs6-selector (Dropdown)
  - product-summary-cards (Div)
  - product-data-store (Store)
  - product-overview-radar (Graph)
  - importer-table-container (Div placeholder for Plan 02)
  - product-map-container (Div placeholder for Plan 02)

patterns-established:
  - "Cascading dropdown: HS2 change -> update HS4 options+value -> update HS6 options+value -> load data"
  - "Product summary uses DISTINCT aggregation to avoid double-counting across exporters"

requirements-completed: [PRDV-01, PRDV-04]

duration: 5min
completed: 2026-03-23
---

# Plan 05-01: Product Risk Page Foundation

**Product page skeleton with HS hierarchy selector and summary statistics enables users to browse and select any product for dependency analysis.**
