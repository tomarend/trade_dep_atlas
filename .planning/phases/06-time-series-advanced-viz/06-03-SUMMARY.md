---
phase: 06-time-series-advanced-viz
plan: 03
subsystem: dashboard
tags: [plotly, sankey, go.Sankey, dash-cytoscape, network-graph, trade-flows]

requires:
  - phase: 06-time-series-advanced-viz
    provides: get_trade_flows query, year-store

provides:
  - Sankey flow diagram on product page (supplier->importer trade flows)
  - Network graph on product page (force-directed trade network)
  - Top-10 aggregation with "Other" grouping for both visualizations

affects: []

tech-stack:
  added: [dash-cytoscape (cose layout)]
  patterns: [Sankey with go.Sankey, Cytoscape with pre-computed node sizes/colors]

key-files:
  created: []
  modified:
    - dashboard/pages/product.py

key-decisions:
  - "Pre-compute node sizes and colors in Python rather than using Cytoscape mapData for more control"
  - "Top-10 aggregation for both exporters and importers with 'Other' grouping to keep charts readable"
  - "Link colors encode exporter geo risk using red/amber/green gradient"
  - "Used cose layout for network graph (force-directed, no animation for fast render)"

requirements-completed: [VIZZ-02, VIZZ-06]

duration: 3min
completed: 2026-03-26
---

# Phase 06 Plan 03: Sankey & Network Graph Summary

**Sankey flow diagram and force-directed network graph added to Product Risk page, visualizing supplier-to-importer trade structure with geo-risk coloring and top-10 aggregation.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T15:12:30Z
- **Completed:** 2026-03-26T15:14:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Sankey diagram shows top-10 exporters (left) -> top-10 importers (right) with "Other" aggregation
- Link widths proportional to trade value, colors encode exporter geo risk
- Network graph shows countries as force-directed nodes with directed edges
- Node sizes scale with trade volume (20-60px), colors indicate geo risk tier
- Both visualizations update reactively on year slider or product selection change

## Task Commits

1. **Task 1: Add Sankey flow diagram** - `fe4ce38` (feat)
2. **Task 2: Add network graph** - `fe4ce38` (feat, combined commit)

## Files Created/Modified
- `dashboard/pages/product.py` - Sankey container, network container, two new callbacks

## Decisions Made
- Pre-computed node sizes/colors in Python (Cytoscape mapData requires knowing max values at stylesheet definition time)
- Used cose layout with animate=False for instant rendering on product/year change

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Plan Readiness

Phase 06 complete — all 3 plans executed across 3 waves. Ready for phase verification.
