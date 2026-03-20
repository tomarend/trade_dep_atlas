---
phase: 02-scoring-pipeline-storage
plan: 03
subsystem: scoring
tags: [polars, parquet, essentiality, crm, critical-raw-materials, tiered-scoring]

requires: []
provides:
  - essentiality_score 0-1 per HS6 product, tiered: critical [0.85,1.0], important [0.45,0.7], standard [0.1,0.3]
  - within-tier gradient: score = tier_min + (tier_max - tier_min) * global_export_HHI
  - essentiality_scores.parquet at data/scoring/essentiality/
  - CRM mapping: data/reference/crm_hs6_mapping.csv (~55 entries EU+USGS)
  - HS6 overrides: data/reference/essentiality_hs6.csv (~39 entries)
  - Sector config: data/reference/essentiality_config.yaml

affects: [03-dashboard, composite-scoring, duckdb-export]

tech-stack:
  added: []
  patterns:
    - Tiered scoring with within-tier gradient using global export HHI
    - Classification priority: CRM mapping > HS6 overrides > YAML sector rules

key-files:
  created:
    - pipeline/essentiality.py
    - tests/test_pipeline/test_essentiality.py
    - data/reference/essentiality_config.yaml
    - data/reference/essentiality_hs6.csv
    - data/reference/crm_hs6_mapping.csv

key-decisions:
  - "Critical tier: [0.85, 1.0]; Important: [0.45, 0.7]; Standard: [0.1, 0.3]"
  - "Within-tier gradient uses global export HHI of each product (higher concentration = higher score)"
  - "CRM listing (EU or USGS) always maps to critical tier"
  - "Energy HS2=27 is critical EXCEPT HS4=2716 (electricity, not scarce)"

patterns-established:
  - "CRITICAL BUG FIXED: Polars infers all-numeric HS6 codes as Int64 from CSV; must cast pl.col('hs6').cast(pl.Utf8) in both load_crm_hs6_mapping() and load_essentiality_overrides()"
  - "Always cast string codes (HS6, HS4, HS2) to pl.Utf8 explicitly when loading from CSV"

requirements-completed: [SCOR-03]

duration: 20min
completed: 2026-03-20
---

# Plan 02-03: Product Essentiality Scoring

**Tiered essentiality classification for all HS6 products, with within-tier gradient using global export HHI; CRM materials always classified critical regardless of HS sector rules.**

## Performance

- **Tasks:** 1
- **Files modified:** 5 created

## Accomplishments
- `classify_hs6()` applies 3-priority classification hierarchy (CRM > overrides > YAML rules)
- `compute_essentiality_scores()` computes global HHI for each HS6, then applies tier+gradient scoring
- 15/15 unit tests cover all tier boundaries, CRM classification, energy exception, standard residual
- Fixed Polars type inference bug: HS6 codes read as Int64, cast to Utf8 in CSV loaders

## Task Commits

1. **Task 1: Essentiality scoring module** - `f1ad39a` (feat)
