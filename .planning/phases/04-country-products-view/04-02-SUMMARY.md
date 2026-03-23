---
phase: 04-country-products-view
plan: 02
subsystem: ui

requires: [04-01]
provides:
  - AG Grid product table (id="product-table") with 7 columns, sorting, filtering, conditional formatting
  - Callback update_product_table reading from country-data-store + weight sliders, recalculating weighted_composite, sorting desc
  - Replaced html.Div placeholder with dcc.Loading-wrapped dag.AgGrid

affects: [04-03]

tech-stack:
  added: [dash-ag-grid]
  patterns:
    - AG Grid with valueFormatter using d3.format for numeric columns
    - cellStyle function expressions for conditional color formatting
    - agSetColumnFilter for categorical columns (essentiality_tier)
    - rowSelection mode singleRow for drill-down integration

key-files:
  modified:
    - dashboard/pages/country.py

key-decisions:
  - "7 columns instead of 4 lean columns — sub-scores (HHI, Geo Risk, Essentiality) included for sorting per CNTV-03"
  - "ag-theme-alpine class for clean styling consistent with LUX theme"
  - "Virtual scroll via fixed 500px height, no pagination"
  - "HS6 column pinned left for readability during horizontal scroll"

component-ids:
  - product-table (AgGrid — rowData populated by update_product_table callback)

patterns-established:
  - "AG Grid conditional formatting: cellStyle function with ternary for score thresholds (>0.7 red, >0.4 amber, else green)"
  - "Weight recalculation callback: reads country-data-store + weight-* sliders, recalculates weighted_composite, sorts desc"
---
