---
phase: 02-scoring-pipeline-storage
plan: 01
subsystem: scoring
tags: [polars, parquet, hhi, herfindahl-hirschman]

requires: []
provides:
  - HHI concentration score per (importer, product, year) supplier tuple
  - supplier_share column enabling basket_geo_risk computation in plan 02-04
  - per-year Parquet output at data/scoring/hhi/year=YYYY/data.parquet

affects: [03-dashboard, composite-scoring, duckdb-export]

tech-stack:
  added: []
  patterns:
    - Polars window functions (.over()) for group-level scalar aggregation
    - per-year Parquet with hive partitioning for incremental processing
    - HHI on 0-1 scale (NOT 10,000-point scale)

key-files:
  created:
    - pipeline/hhi.py
    - tests/test_pipeline/test_hhi.py

key-decisions:
  - "HHI normalized to 0-1 scale: monopoly=1.0, 4-equal-suppliers=0.25, 80/20-duopoly≈0.68"
  - "Skip Parquet files that already exist for incremental re-runs"
  - "Filter value_usd > 0 before computing supplier shares to avoid division edge cases"

patterns-established:
  - "Window function pattern: pl.col('x').sum().over(['a','b','c']) for group-level aggregation"
  - "Skip-if-exists pattern: if out_path.exists(): continue"

requirements-completed: [SCOR-01]

duration: 15min
completed: 2026-03-20
---

# Plan 02-01: HHI Concentration Scoring

**Herfindahl-Hirschman Index computed for each (importer, product, year) group, normalized to 0-1 scale, with supplier shares enabling basket geo-risk in downstream composite scoring.**

## Performance

- **Tasks:** 1
- **Files modified:** 2 created

## Accomplishments
- `compute_hhi(df)` uses Polars window functions to compute supplier shares and HHI in a single pass
- `run_hhi_scoring(config)` iterates year partitions, skips existing files (idempotent)
- 9/9 unit tests cover monopoly, equal-4, 80/20 duopoly, column schema, supplier counts

## Task Commits

1. **Task 1: HHI scoring module** - `560690d` (feat)
