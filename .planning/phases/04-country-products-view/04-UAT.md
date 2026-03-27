---
status: testing
phase: 04-country-products-view
source:
  - .planning/phases/04-country-products-view/04-01-SUMMARY.md
  - .planning/phases/04-country-products-view/04-02-SUMMARY.md
  - .planning/phases/04-country-products-view/04-03-SUMMARY.md
started: 2026-03-23T13:58:00Z
updated: 2026-03-23T14:05:00Z
---

## Current Test

number: 3
name: Weight Sliders
expected: |
  Click "Customize Weights" button. A collapsible panel opens with 3 sliders: HHI Concentration (0.35), Geopolitical Risk (0.35), Essentiality (0.30). Dragging one slider proportionally adjusts the others so they sum to 1.0. Summary card scores update as you drag.
awaiting: user response

## Tests

### 1. Country Selector and Page Load
expected: Navigate to /country. Searchable dropdown with ~200 options, default country pre-selected. Header: "Country Exposure".
result: issue
reported: "A bunch of countries have no data, like France"
severity: major
note: "Data pipeline issue — dropdown pulls from countries table (252) but only 222 importers exist in dependency_scores. FRA, USA, IND have zero rows."

### 2. Summary Cards Display
expected: 4 summary cards: Overall Exposure, HHI, Geo Risk, Essentiality. Radar chart below.
result: issue
reported: "Geo risk is always exactly 0.500"
severity: major
note: "Data pipeline issue — 70.7M rows have exporter_geo_risk=0.5 default. Pipeline didn't populate real values."

### 3. Weight Sliders
expected: Collapsible panel with 3 sliders summing to 1.0, proportional adjustment, live card updates.
result: pending

### 4. AG Grid Product Table
expected: 7-column AG Grid with conditional coloring, sorted by composite desc.
result: issue
reported: "Most product descriptions are missing"
severity: major
note: "Data pipeline issue — 99.5% of products have empty descriptions. Only 26 CRM minerals have names."

### 5. Table Sorting and Filtering
expected: Column sort, number filters, set filter on Tier, text filters on HS6/Description.
result: pending

### 6. Weight Recalculation in Table
expected: Dragging weight sliders recalculates composite scores and re-sorts the table.
result: pending

### 7. Product Drill-Down Panel
expected: Click row -> drill-down panel with blue header, supplier table (left), choropleth (right).
result: pending

### 8. Supplier Table in Drill-Down
expected: Supplier Country, Share %, Trade Value, Geo Risk (color-coded), Region columns.
result: pending

### 9. Choropleth Map
expected: World map colored by geo risk (RdYlGn_r), hover shows name/share/risk.
result: pending

### 10. Radar and Bar Charts
expected: Radar chart (score decomposition) + bar chart (top suppliers by share).
result: pending

### 11. Country Switch Updates Everything
expected: Changing country updates cards, radar, table, drill-down. No stale data.
result: pending

## Summary

total: 11
passed: 0
issues: 3
pending: 8
skipped: 0

## Gaps

- truth: "Countries with no data should not appear or should show empty state"
  status: failed
  reason: "User reported: A bunch of countries have no data, like France"
  severity: major
  test: 1
  upstream: true
  pipeline_root_cause: "Pipeline didn't ingest FRA, USA, IND as importers"

- truth: "Geo risk values should vary reflecting real geopolitical risk"
  status: failed
  reason: "User reported: Geo risk is always exactly 0.500"
  severity: major
  test: 2
  upstream: true
  pipeline_root_cause: "Pipeline uses 0.5 default; real risk index not integrated"

- truth: "Products should have human-readable descriptions"
  status: failed
  reason: "User reported: Most product descriptions are missing"
  severity: major
  test: 4
  upstream: true
  pipeline_root_cause: "Only 26 CRM minerals have descriptions; HS Nomenclature not ingested"
