---
phase: 03-dashboard-shell-data-access
plan: 01
subsystem: ui
tags: [dash, duckdb, dash-bootstrap-components, gunicorn, sidebar]

requires: []
provides:
  - DuckDB read-only singleton at dashboard/data.py with lru_cache startup queries
  - Dash multi-page app instance with LUX theme at dashboard/app.py
  - Left sidebar layout with 3 NavLinks + live footer at dashboard/layout.py
  - Offline-safe error page when dashboard.duckdb is absent

affects: [03-02, 03-03, phases 4-6 that add page content]

tech-stack:
  added: [dash>=4.0.0, dash-bootstrap-components>=2.0.4, duckdb>=1.5.0, loguru, gunicorn]
  patterns:
    - Module-level DuckDB singleton (read_only=True), opened once at app startup
    - lru_cache(maxsize=1) on all startup queries for zero-cost repeat calls
    - Offline guard in create_layout() — returns error container when db_available=False

key-files:
  created:
    - dashboard/__init__.py
    - dashboard/data.py
    - dashboard/app.py
    - dashboard/layout.py
    - dashboard/assets/custom.css

key-decisions:
  - "LUX theme chosen (clean, report-style, light — matches CONTEXT.md decision)"
  - "DASHBOARD_DB env var overrides default data/dashboard.duckdb path"
  - "db_available module-level bool exposed so layout.py can branch without re-checking"
  - "dcc.Location placed in both layouts (online + offline) so routing doesn't break"

patterns-established:
  - "data.py singleton pattern: _conn at module level, db_available bool, lru_cache queries"
  - "Offline guard: create_layout() returns _build_error_layout() when not data.db_available"
  - "gunicorn entry point: server = app.server in app.py"

requirements-completed: [DASH-01, DASH-03]

duration: 6min
completed: 2026-03-23
---

# Phase 03 Plan 01 Summary

**DuckDB data access singleton + Dash app shell with LUX sidebar layout — offline-safe foundation for all dashboard pages.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-23T10:42:32Z
- **Completed:** 2026-03-23T10:49:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Module-level DuckDB read-only singleton with `db_available` flag and 4 lru_cached startup queries (`get_year_range`, `get_country_list`, `get_default_country`, `get_default_product`)
- Multi-page Dash app with DBC LUX theme, left sidebar (width=2) with pills navigation, and live data freshness footer (`"Data: BACI {min_year}–{max_year} · CEPII"`)
- Offline-safe: absent `data/dashboard.duckdb` shows error alert with pipeline instructions — no Python traceback visible

## Task Commits

1. **Task 1: data access layer** - `744b285` (feat)
2. **Task 2: Dash app shell** - `c3b9c02` (feat)

## Files Created/Modified
- `dashboard/__init__.py` — package marker
- `dashboard/data.py` — DuckDB singleton + cached startup queries
- `dashboard/app.py` — Dash app + `server` export for gunicorn
- `dashboard/layout.py` — `create_layout()` with sidebar + footer (or error layout)
- `dashboard/assets/custom.css` — brand-title, footer-text, sidebar styles
