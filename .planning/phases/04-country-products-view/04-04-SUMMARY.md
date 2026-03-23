---
phase: 04-country-products-view
plan: 04
subsystem: ui
tags: [ag-grid, duckdb, dash]

requires:
  - phase: 04-country-products-view
    provides: Country view AG Grid table and data layer

provides:
  - Fixed AG Grid tier filter (community-compatible)
  - Filtered country dropdown (only countries with data)

affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - dashboard/pages/country.py
    - dashboard/data.py

key-decisions:
  - "Use agTextColumnFilter for Tier column — agSetColumnFilter is enterprise-only"
  - "Filter country list via subquery on dependency_scores (252 → 222 countries)"

patterns-established: []

requirements-completed: [CNTV-01, CNTV-03, VIZZ-04]

duration: 3min
completed: 2026-03-23
---

# Plan 04-04: Fix AG Grid set filter and country dropdown query

**Fixed two UAT bugs: enterprise-only filter type replaced with community-compatible alternative, country dropdown filtered to only show countries with trade data.**

## Performance

- **Duration:** 3 min
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Replaced `agSetColumnFilter` (enterprise-only, silently broken) with `agTextColumnFilter` for the Tier column
- Updated `get_country_list()` SQL to filter against `dependency_scores` table, reducing dropdown from 252 to 222 countries
- Preserved all `agNumberColumnFilter` instances on score columns

## Task Commits

1. **Task 1: Fix AG Grid set filter and country dropdown query** - `d1c88e3` (fix)

## Files Created/Modified
- `dashboard/pages/country.py` - Changed Tier column filter from agSetColumnFilter to agTextColumnFilter
- `dashboard/data.py` - Updated get_country_list() to use subquery filtering against dependency_scores
