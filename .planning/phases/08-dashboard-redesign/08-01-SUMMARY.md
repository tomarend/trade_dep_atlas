---
phase: 08-dashboard-redesign
plan: 01
subsystem: data, product-page
tags: [duckdb, dash, plotly, dash-bootstrap-components]

requires: []
provides:
  - RISK_THRESHOLD constant (0.7) and _ISO3_TO_ISO2 dict (~92 entries) in data.py
  - get_scatter_data() — top-200 products by composite score for scatter plots
  - get_bilateral_risk() — top-10 exporters by weighted risk contribution
  - get_product_exporters() — top-15 global exporters for a product by share
  - get_product_summary() now returns flags and crm_listed_since keys
  - Product page: dash-cytoscape import and update_network callback removed
  - Product page: concentration bar chart (update_concentration_bars) with flag-emoji labels
  - Product page: dbc.Badge flag badges rendered in update_product_summary
  - pyproject.toml: dash-cytoscape dependency removed
affects: [country-page, product-page, data-layer]

tech-stack:
  added: []
  patterns:
    - "Flag-emoji generation via chr(127397 + ord(c)) for c in iso2 — Unicode regional indicator"
    - "Graceful degradation for DB schema mismatches — try/except returning empty list"
    - "Geo-risk colour-coded horizontal bar charts using plotly go.Bar with colorscale"

key-files:
  created: []
  modified:
    - dashboard/data.py
    - dashboard/pages/product.py
    - pyproject.toml

key-decisions:
  - "RISK_THRESHOLD = 0.7 (D-13) — 0.7 composite score boundary for high-risk classification"
  - "Used _ISO3_TO_ISO2 dict (92 entries) rather than external pycountry calls in callbacks for performance"
  - "Removed dash-cytoscape entirely (network graph unused, saves ~2MB bundle, fixes install issue)"

patterns-established:
  - "ISO3->ISO2 lookup: data._ISO3_TO_ISO2.get(r['exporter_iso3'], '') — used in product.py and country.py"
  - "Flag name display: flag.replace('_', ' ').title() with CRM year override"
  - "Badge colour map: crm_listed=danger, energy=warning, pharma=info, semiconductor=secondary"

requirements-completed: [PRDV-07, PRDV-08, PRDV-09, CNTV-09, CNTV-10]

duration: 30min
completed: 2026-03-27
---

# Phase 08-01: Data Layer + Product Page Overhaul Summary

**Extended data.py with 3 new queries + constants, overhauled product page by removing network graph and adding concentration bars with flag emoji and badge rendering.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-03-27
- **Completed:** 2026-03-27
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `RISK_THRESHOLD = 0.7` and `_ISO3_TO_ISO2` (92-entry ISO3→ISO2 dict) to `data.py`
- Implemented `get_scatter_data()`, `get_bilateral_risk()`, `get_product_exporters()` — all return empty lists gracefully when DB unavailable
- Updated `get_product_summary()` to return `flags: list[str]` and `crm_listed_since: str | None`
- Removed `import dash_cytoscape`, network-container div, and entire `update_network` callback from `product.py`
- Added `product-concentration-container` div and `update_concentration_bars` callback with flag-emoji labels
- Added `dbc.Badge` flag rendering in `update_product_summary` with colour-coded badge map
- Removed `"dash-cytoscape>=1.0.2"` from `pyproject.toml`

## Task Commits

1. **Task 1: Data layer — new queries, constants, get_product_summary fix** — `c1cda8a` (feat)
2. **Task 2: Product page — remove network + add concentration bars + flag badges** — included in `c1cda8a` (feat)

## Files Created/Modified

- `dashboard/data.py` — Added RISK_THRESHOLD, _ISO3_TO_ISO2, 3 new query functions, updated get_product_summary
- `dashboard/pages/product.py` — Removed cytoscape, added concentration bars + flag badges
- `pyproject.toml` — Removed dash-cytoscape dependency
