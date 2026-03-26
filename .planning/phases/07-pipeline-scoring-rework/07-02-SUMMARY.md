---
plan: 07-02
phase: 07-pipeline-scoring-rework
status: complete
completed: 2026-03-26
---

## Summary

Created `pipeline/flags.py` (replacing `essentiality.py`) and `data/reference/flags_config.yaml`. Products now receive orthogonal flag lists instead of tier scores. `global_export_hhi` is the substitutability measure.

## What Was Built

- **data/reference/flags_config.yaml**: 8 canonical flags — `crm_listed`, `energy`, `fertilizer`, `food`, `pharma`, `semiconductor`, `strategic_mineral`, `hs22_only`. Two flags are `set_programmatically: true` (crm_listed, hs22_only). HS inclusion rules copied from essentiality_config.yaml.
- **pipeline/flags.py**:
  - `load_flags_config()`: loads flags_config.yaml
  - `load_crm_hs6_mapping()`: verbatim from essentiality.py
  - `compute_global_export_hhi()`: verbatim from essentiality.py
  - `classify_hs6(hs6, flags_config, crm_hs6_set) -> list[str]`: NEW — returns flag list, never a tier tuple
  - `compute_product_flags()`: builds output DataFrame with schema `[hs6, flags (List), global_export_hhi, crm_listed_since, hs22_only]`; computes hs22_only_set from HS22/HS92 product code CSV diff when raw_dir provided
  - `run_flags_scoring()`: writes to `data/scoring/flags/flags_scores.parquet`

## Verification

- All exports import cleanly: ✓
- `classify_hs6()` returns `list`: ✓
- No `_tier_score`/`essentiality_score`/`essentiality_tier` references: ✓
- Output path `flags_scores.parquet` correct: ✓
- 8 flags in config: ✓ (`crm_listed`, `energy`, `fertilizer`, `food`, `pharma`, `semiconductor`, `strategic_mineral`, `hs22_only`)

## Key Files Created

- pipeline/flags.py (new)
- data/reference/flags_config.yaml (new)

## Commit

2549932 — feat(07-02): create flags.py and flags_config.yaml
