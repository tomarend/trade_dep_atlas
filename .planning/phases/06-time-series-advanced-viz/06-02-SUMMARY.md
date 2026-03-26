---
phase: 06-time-series-advanced-viz
plan: 02
subsystem: dashboard
tags: [plotly, trend-charts, time-series, go.Scatter, go.Figure]

requires:
  - phase: 06-time-series-advanced-viz
    provides: get_score_trend, get_product_trend, year-store

provides:
  - Country drill-down trend chart (30-year score evolution)
  - Product page trend chart (global dependency evolution)
  - Toggleable sub-score overlays on both trend charts
  - Vertical reference line at selected year

affects: [06-03]

tech-stack:
  added: []
  patterns: [trend chart pattern with go.Scatter, legendonly visibility, add_vline reference]

key-files:
  created: []
  modified:
    - dashboard/pages/country.py
    - dashboard/pages/product.py
    - dashboard/data.py

key-decisions:
  - "get_product_trend aggregates via AVG across all importers per year for product-level view"
  - "Sub-scores default to legendonly (hidden) to keep chart clean, toggled via legend clicks"
  - "Missing years render as None gaps with connectgaps=False"

requirements-completed: [TIME-02, TIME-03]

duration: 3min
completed: 2026-03-26
---

# Phase 06 Plan 02: Trend Line Charts Summary

**30-year score trend charts added to both Country Exposure drill-down and Product Risk page with toggleable sub-score overlays, vertical year reference line, and gap handling.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T15:04:00Z
- **Completed:** 2026-03-26T15:12:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Country drill-down trend chart shows composite + 3 sub-scores for specific importer-product pair
- Product page trend chart shows global averages across all importers over time
- Both charts: blue composite line always visible, purple HHI / red geo risk / green essentiality toggleable
- Vertical dashed reference line marks currently selected year
- Missing data years render as gaps (no misleading interpolation)

## Task Commits

1. **Task 1: Add trend chart to country page drill-down** - `af86874` (feat)
2. **Task 2: Add trend chart section to product page** - `eb2a78f` (feat)

## Files Created/Modified
- `dashboard/pages/country.py` - Trend chart in render_drilldown after radar+bar row
- `dashboard/pages/product.py` - Trend chart section below choropleth + new callback
- `dashboard/data.py` - get_product_trend() aggregation query

## Decisions Made
- Product trend uses AVG aggregation across importers (not a specific importer's view)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Plan Readiness

Ready for 06-03 (Sankey + Network Graph) — trend infrastructure complete, get_trade_flows() available.
