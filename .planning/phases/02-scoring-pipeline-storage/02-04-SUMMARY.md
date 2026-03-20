---
phase: 02-scoring-pipeline-storage
plan: 04
subsystem: scoring
tags: [polars, duckdb, composite-score, star-schema, cli]

requires:
  - phase: 02-01
    provides: HHI Parquet with supplier_share per (importer, product, year, exporter)
  - phase: 02-02
    provides: geo_risk per (country, year) Parquet
  - phase: 02-03
    provides: essentiality_score per HS6 Parquet

provides:
  - composite_score per supplier tuple: 0.35*hhi + 0.35*basket_geo_risk + 0.30*essentiality_score
  - basket_geo_risk = sum(supplier_share * exporter_geo_risk) per (importer, product, year)
  - composite Parquet at data/scoring/composite/year=YYYY/data.parquet
  - DuckDB star schema at data/dashboard.duckdb (dependency_scores fact + countries + products dims)
  - Extended CLI: python -m pipeline with stages 4-7 and --skip-scoring flag
  - pipeline.yaml scoring config block with weights and paths

affects: [03-dashboard, 04-api]

tech-stack:
  added:
    - duckdb (read_parquet via glob with hive_partitioning=true, star schema DDL, indexing)
  patterns:
    - basket_geo_risk computed as weighted sum using Polars window .over() on (importer, hs6, year)
    - fill_null with meaningful defaults: geo_risk=0.5 (median), essentiality=0.1 (standard min)
    - DuckDB idempotent: DROP TABLE IF EXISTS before CREATE TABLE
    - Indexes on (importer_iso3), (hs6), (year), (importer_iso3, hs6, year) for <50ms queries

key-files:
  created:
    - pipeline/composite.py
    - pipeline/export.py
    - tests/test_pipeline/test_composite.py
    - tests/test_pipeline/test_export.py
  modified:
    - pipeline/__main__.py (stages 4-7, --skip-scoring, version 0.2.0)
    - pipeline.yaml (scoring: section with weights)
    - tests/test_pipeline/test_integration.py (added skip_scoring=True to preserve Phase 1 test isolation)

key-decisions:
  - "Default weights: hhi=0.35, geo_risk=0.35, essentiality=0.30 (configurable via pipeline.yaml)"
  - "Missing geo_risk fills with 0.5 (median), NOT 0.0 (which would incorrectly reward unknown exporters)"
  - "Missing essentiality fills with 0.1 (standard tier minimum), NOT 0.0"
  - "Composite score clamped [0,1] even though weighted sum of 0-1 values cannot normally exceed 1"
  - "DuckDB CREATE TABLE AS SELECT ... FROM read_parquet(glob, hive_partitioning=true) — no intermediate CSV"
  - "Integration tests updated to pass skip_scoring=True to preserve Phase 1 test isolation"

patterns-established:
  - "basket_geo_risk pattern: (pl.col('supplier_share') * pl.col('exporter_geo_risk')).sum().over(key)"
  - "DuckDB glob pattern: composite_dir / 'year=*' / 'data.parquet' with hive_partitioning=true"
  - "Test fixture helpers: _make_composite_df(n) with random.seed(42) for reproducible perf tests"
  - "Use 'df if df is not None else default' NOT 'df or default' for Polars DataFrames (truthiness TypeError)"

requirements-completed: [SCOR-04, DATA-05]

duration: 40min
completed: 2026-03-20
---

# Plan 02-04: Composite Scoring, DuckDB Export, and CLI Wiring

**Composite dependency score combines HHI + basket_geo_risk + essentiality via configurable weights; DuckDB star schema enables <50ms dashboard queries; CLI extended with stages 4-7 and --skip-scoring flag.**

## Performance

- **Tasks:** 3
- **Files modified:** 4 created, 3 modified

## Accomplishments
- `compute_composite()` joins all 3 sub-scores, computes basket_geo_risk via window function
- `build_duckdb()` creates star schema with 4 indexes; typical query <2ms in tests
- `run_duckdb_export()` idempotent: drops and recreates all tables on each run
- CLI now runs full 7-stage pipeline by default; `--skip-scoring` preserves Phase 1 behavior
- 12/12 new tests pass (7 composite + 5 export); full suite 93/93

## Task Commits

1. **Task 1: Composite module + tests** - `1831845` (feat, part 1)
2. **Task 2: Export module + tests** - `1831845` (feat, part 2)
3. **Task 3: CLI + YAML config** - `1831845` (feat, part 3)
