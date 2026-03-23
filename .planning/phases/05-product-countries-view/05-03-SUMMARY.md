---
phase: 05-product-countries-view
plan: 03
subsystem: ui

requires:
  - phase: 05-product-countries-view
    plan: 02
    provides: importer-table AG Grid with importer_name column, product-choropleth map

provides:
  - Bidirectional cross-linking between country and product views via AG Grid cellRenderer anchor tags
  - URL query parameter handling on both pages (country.py accepts ?iso3=, product.py accepts ?hs6=)
  - Country page HS6 column links to /product?hs6=XXXXXX
  - Product page importer_name column links to /country?iso3=XXX

affects: []

tech-stack:
  added: []
  patterns:
    - AG Grid cellRenderer with JS function returning <a> tags for in-app navigation
    - dangerously_allow_code=True required on AgGrid for cellRenderer JS execution
    - layout(**kwargs) pattern to receive URL query parameters from Dash page registry

key-files:
  modified:
    - dashboard/pages/country.py
    - dashboard/pages/product.py

key-decisions:
  - "cellRenderer anchor tags (Option A) chosen over dcc.Location callbacks — no server round-trip, standard web nav"
  - "importer_name column used for country links (more natural than importer_iso3)"
  - "hs6 column used for product links in country view"
  - "URL params handled via layout(**kwargs) — Dash passes query params as keyword args to layout function"
  - "Graceful fallback when URL param doesn't match valid data — defaults preserved"

component-ids:
  - product-table (AgGrid, country.py — hs6 column now clickable)
  - importer-table (AgGrid, product.py — importer_name column now clickable)

patterns-established:
  - "layout(**kwargs) for URL query parameter handling in Dash multi-page apps"
  - "cellRenderer JS function with template literal for building <a href> links between pages"
  - "dangerously_allow_code=True as standard AG Grid setting when using cellRenderer functions"

requirements-completed: [PRDV-06, CNTV-07]

duration: 8min
completed: 2026-03-23
---

# Plan 05-03: Bidirectional Cross-Linking

**Both analytical views now have clickable links enabling seamless navigation between country and product perspectives. HS6 codes in the country view link to the product page, and country names in the product view link to the country page. URL query parameters pre-select the relevant item on arrival.**
