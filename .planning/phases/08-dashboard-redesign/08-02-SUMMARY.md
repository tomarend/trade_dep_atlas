---
phase: 08-dashboard-redesign
plan: 02
subsystem: country-page
tags: [dash, plotly, dash-bootstrap-components, scatter-plot, horizontal-bar, flag-emoji]

requires:
  - phase: 08-01
    provides: "get_scatter_data(), get_bilateral_risk(), RISK_THRESHOLD, _ISO3_TO_ISO2 in data.py"
provides:
  - Country page: 4 hero stat cards (Total Products, Above Risk Threshold, Highest-Risk Product, Max Composite Score)
  - Country page: hero cards (2x2 grid, md=8) + radar (md=4) in same row
  - Country page: scatter plot (HHI vs substitutability, composite colour, log-sized markers)
  - Country page: bilateral risk panel (top-10 exporters, horizontal bars, flag emoji, geo-risk colour)
  - Zero "essentiality" strings in country.py UI-visible text (DASH-06 complete)
affects: [country-page]

tech-stack:
  added: []
  patterns:
    - "Hero stats layout: 2x2 grid cards (md=8) beside radar (md=4) using dbc.Col + dbc.Row"
    - "Scatter plot: go.Scatter with log1p marker sizing, composite colorscale, hover tooltips"
    - "Bilateral bar: go.Bar horizontal with flag-emoji y-axis labels, reversed autorange"

key-files:
  created: []
  modified:
    - dashboard/pages/country.py

key-decisions:
  - "Hero cards replace the 4 avg-score cards (D-01): Total, Above-threshold, Top-risk desc, Max score"
  - "Radar retained beside hero cards (D-02), height reduced to 230px to fit same row"
  - "import math used for log1p marker sizing in scatter (no new dependency)"
  - "Terminology: 'essentiality' fully absent from UI text; internal vars (w_ess, avg_ess) unchanged"

patterns-established:
  - "Flag emoji in chart y-axis: chr(127397 + ord(c)) for c in iso2 — same pattern as product.py"
  - "Bilateral panel uses data._ISO3_TO_ISO2 directly (module-level access pattern)"

requirements-completed: [CNTV-08, CNTV-09, CNTV-10, CNTV-11, DASH-06]

duration: 25min
completed: 2026-03-27
---

# Phase 08-02: Country Page Redesign Summary

**Replaced 4 average-score summary cards with 4 insight-first hero stat cards, added scatter plot (Product Risk Landscape) and bilateral risk panel (Key Supply Risk Sources) to the country page.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-27
- **Completed:** 2026-03-27
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `update_summary_cards()` rebuilt: 4 hero cards (Total Products, Above Risk Threshold, Highest-Risk Product, Max Composite Score) in 2×2 grid (md=8) alongside radar (md=4)
- `data.RISK_THRESHOLD` used for threshold card — no hardcoded values
- `country-scatter-container` and `country-bilateral-container` divs added to layout between summary-cards and weight-controls
- `update_scatter_plot` callback: calls `get_scatter_data()`, uses `math.log1p()` for marker sizing, composite score colourscale
- `update_bilateral_panel` callback: calls `get_bilateral_risk()`, flag emoji via `_ISO3_TO_ISO2`, geo-risk colourscale on bars
- Zero "essentiality" occurrences in all UI-visible text across `country.py`

## Task Commits

1. **Task 1: Hero cards + layout row** — `86cd73a` (feat)
2. **Task 2: Scatter + bilateral callbacks** — included in `86cd73a` (feat)

## Files Created/Modified

- `dashboard/pages/country.py` — Hero cards, scatter plot, bilateral panel, terminology clean
