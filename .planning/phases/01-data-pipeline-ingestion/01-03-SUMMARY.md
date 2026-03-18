---
phase: 01-data-pipeline-ingestion
plan: 03
subsystem: pipeline
tags: [polars, parquet, etl, cli, argparse, ingestion]

requires:
  - phase: 01-01
    provides: Project scaffolding, download module, conftest fixtures
  - phase: 01-02
    provides: Country mapping (load_country_mapping), HS concordance (build_concordance_polars_map)
provides:
  - Core Polars lazy ETL pipeline (BACI CSV → enriched DataFrame)
  - Hive-partitioned Parquet output (data/processed/year=YYYY/)
  - Pipeline CLI orchestrator (python -m pipeline)
  - Pipeline manifest JSON with run metadata
affects: [scoring-pipeline, dashboard]

tech-stack:
  added: []
  patterns: [Polars lazy evaluation, hive partitioning, JSON manifest, argparse CLI]

key-files:
  created:
    - pipeline/ingest.py
    - pipeline/__main__.py
    - tests/test_pipeline/test_ingest.py
    - tests/test_pipeline/test_integration.py
  modified: []

key-decisions:
  - "Polars scan_csv → collect for lazy evaluation (memory-efficient for multi-GB files)"
  - "map_elements for country mapping (vectorized replace not feasible with complex lookups)"
  - "replace_strict for concordance mapping (flat dict → vectorized)"
  - "outlier_flag via window function over concorded_hs6 groups (3σ threshold)"
  - "Incremental processing: skip if Parquet mtime >= CSV mtime"
  - "Manifest captures years_processed, years_skipped, total_rows, concordance_warnings"

patterns-established:
  - "Pipeline invoked via `python -m pipeline [--skip-download] [--config path]`"
  - "4-stage pipeline: download → validate concordance → ingest → manifest"
  - "Parquet output at data/processed/year={year}/data.parquet with zstd compression"
  - "Output schema: year, exporter_baci, importer_baci, exporter_iso3, importer_iso3, hs6_original, concorded_hs6, hs2, hs4, product_description, category, concordance_flag, value_usd, quantity_kg, unit_value, outlier_flag"

requirements-completed: [DATA-02]

duration: 5min
completed: 2026-03-18
---

# Plan 01-03: Core Ingestion Pipeline + CLI Orchestrator

**End-to-end BACI ETL pipeline that reads raw CSVs, applies country mapping and HS concordance, computes unit values and outlier flags, and writes hive-partitioned Parquet — invokable via `python -m pipeline`.**

## What Was Built

1. **Ingestion module** (`pipeline/ingest.py`):
   - `ingest_baci_year()` — Polars lazy ETL: scan CSV → rename → filter nulls → map countries → apply concordance → derive HS hierarchy → compute unit values → flag outliers → collect
   - `run_ingestion()` — processes all CSVs in raw_dir, writes Parquet per year, incremental skip

2. **CLI orchestrator** (`pipeline/__main__.py`):
   - `main()` — 4-stage pipeline: download → validate concordance → ingest → manifest
   - `python -m pipeline --help` prints usage
   - `--skip-download` flag for development (skip CEPII download)
   - `--config` flag for custom config path
   - `write_manifest()` — JSON with run_timestamp, years, rows, warnings

## Test Results

39 tests total across all modules — all passing:
- 9 download tests
- 8 country tests
- 10 concordance tests
- 8 ingestion tests
- 4 integration tests

## Output Schema

| Column | Type | Source |
|--------|------|--------|
| year | int | BACI t column |
| exporter_iso3 | str | Country mapping |
| importer_iso3 | str | Country mapping |
| concorded_hs6 | str | HS concordance |
| hs2, hs4 | str | Derived from concorded_hs6 |
| value_usd | float | BACI v column |
| quantity_kg | float | BACI q column |
| unit_value | float | value_usd / quantity_kg |
| outlier_flag | bool | 3σ from product-level mean |
