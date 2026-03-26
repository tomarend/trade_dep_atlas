---
plan: 07-03
phase: 07-pipeline-scoring-rework
status: complete
completed: 2026-03-26
---

## Summary

Updated composite scoring formula to use `sqrt(global_export_hhi)` as substitutability, rewired export.py DuckDB builder to v2 schema, wired __main__.py to `run_flags_scoring`, updated pipeline.yaml weights key, and deleted old essentiality files.

## What Was Built

- **pipeline/composite.py**:
  - `DEFAULT_WEIGHTS` key renamed `essentiality` → `substitutability`
  - `_ESSENTIALITY_FILL` constant removed
  - `compute_composite()` parameter renamed `essentiality_df` → `flags_df`; new join block uses `global_export_hhi` + `flags` + `crm_listed_since` + `hs22_only`; `substitutability_score = sqrt(global_export_hhi)`; output columns updated to v2 schema
  - `run_composite_scoring()` reads from `flags/flags_scores.parquet` instead of `essentiality/essentiality_scores.parquet`
- **pipeline/export.py**:
  - `build_duckdb()` parameter renamed `essentiality_path` → `flags_path`
  - dependency_scores fact table: `essentiality_score`/`essentiality_tier` → `global_export_hhi`/`substitutability_score`/`flags`/`hs22_only`
  - products dimension: uses flags parquet; columns `flags`, `global_export_hhi`, `hs22_only`, `crm_listed_since` (no `essentiality_*`)
  - `run_duckdb_export()` updated to use `flags_path`
- **pipeline/__main__.py**: imports `run_flags_scoring` from `pipeline.flags`; Stage 6 key is `flags`
- **pipeline.yaml**: `scoring.weights.substitutability: 0.30`
- **Deleted**: `pipeline/essentiality.py`, `data/reference/essentiality_config.yaml`

## Verification

- `DEFAULT_WEIGHTS` has `substitutability`, not `essentiality`: ✓
- pipeline.yaml has `substitutability: 0.30`: ✓
- Zero essentiality_score/tier/category/path refs in composite.py: ✓
- Zero essentiality refs in export.py: ✓
- `__main__.py` imports `run_flags_scoring`: ✓
- essentiality.py and essentiality_config.yaml deleted: ✓
- All imports clean: ✓

## Key Files Modified

- pipeline/composite.py
- pipeline/export.py
- pipeline/__main__.py
- pipeline.yaml

## Key Files Deleted

- pipeline/essentiality.py
- data/reference/essentiality_config.yaml

## Commit

0d5bdac — feat(07-03): wire flags schema through composite, export, and pipeline orchestrator
