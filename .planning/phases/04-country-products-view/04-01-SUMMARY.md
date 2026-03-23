---
phase: 04-country-products-view
plan: 01
subsystem: ui, data

requires: [03-01]
provides:
  - Three parameterized query functions in dashboard/data.py (get_product_scores, get_country_summary, get_supplier_breakdown)
  - Full Country Exposure page layout at dashboard/pages/country.py with searchable country dropdown, 4 summary cards, collapsible weight sliders, dcc.Store, placeholder divs for AG Grid and drill-down
  - Callbacks for toggle_weights, clientside proportional weight adjustment, load_country_data, update_summary_cards
  - CSS classes for score styling (.score-high, .score-medium, .score-low, .score-value, .drilldown-panel, .drilldown-header)

affects: [04-02, 04-03]

tech-stack:
  added: []
  patterns:
    - Parameterized queries (no lru_cache) with ? placeholders and try/except guards
    - clientside_callback for instant weight proportional adjustment
    - dcc.Store(id="country-data-store") as intermediary between country selector and downstream consumers

key-files:
  modified:
    - dashboard/data.py
    - dashboard/pages/country.py
    - dashboard/assets/custom.css

key-decisions:
  - "Weight sliders default to HHI=0.35, Geo=0.35, Ess=0.30 — collapsed by default"
  - "clientside_callback for proportional adjustment — instant response, no server round-trip"
  - "Product data stored in dcc.Store for consumption by AG Grid (Plan 02) and drill-down (Plan 03)"
  - "Summary cards recalculate weighted composite inline to reflect current weight settings"

component-ids:
  - country-selector (Dropdown)
  - country-summary-cards (Div)
  - weights-toggle (Button)
  - weights-collapse (Collapse)
  - weight-hhi, weight-geo, weight-ess (Slider)
  - country-data-store (Store)
  - product-table-container (Div placeholder for Plan 02)
  - product-drilldown-container (Div placeholder for Plan 03)

patterns-established:
  - "Parameterized query pattern: if _conn is None guard, ? placeholders, try/except with logger.error"
  - "Weight-driven recalculation: weighted_composite = w_hhi * hhi + w_geo * basket_geo_risk + w_ess * essentiality_score"
  - "Score color coding: >0.7 red (#dc2626), >0.4 amber (#d97706), else green (#16a34a)"
---
