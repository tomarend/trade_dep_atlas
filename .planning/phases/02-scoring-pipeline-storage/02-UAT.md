---
status: testing
phase: 02-scoring-pipeline-storage
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
  - 02-04-SUMMARY.md
started: 2026-03-20T00:00:00Z
updated: 2026-03-20T00:01:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 2
name: HHI Concentration Scoring
expected: |
  The HHI scoring module computes Herfindahl-Hirschman Index on the 0-1 scale.
  Run: pytest tests/test_pipeline/test_hhi.py -v
  Expected: 9/9 tests pass. Key behaviours verified: monopoly → 1.0, four-equal-suppliers → 0.25, 80/20 duopoly → ~0.68. supplier_share column is present in output. Zero-value rows are filtered before computing shares.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: |
  In the project root, the CLI entry point boots cleanly.
  Run: python -m pipeline --help
  Expected: Help text is displayed listin  Expected: Help text is displayed listin  Expected: Help text is displayed listin  Expected: Help text is displayed listin  Exp
resulresulresulresu. resulresulresulresu. resulrxpected: |
  The  The  The  The  le c  The  The  The  ThHi  The  The  The  The   The  The  The   pyt  The  The  The  The  le cst_hhi.py -v
  Expected: 9/9 tests pass  Expected: 9/rs  Expected: 9/9 tests pass  Expected: 9/rs  Expes → 0.25, 8  Expected: 9/9 tests pass plier_share colum  Expected: 9/9 tests pass  Expected: 9/rs  Expected: 9/9 tests pass  Expecte
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrrrred: safe country governance_risk is lowrrrrrry country is high; FreerrrrrrrrrrfirrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrr srrrrrrrrrrrrrrrrrrrrrrrrrrrrrr[0,rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrSarrrrrrrrrrrrrrrrrrsirrrrrrrrrexpected: |
  HS6 products are classified into tiers: critical [0.85,1.0], important [0.45,0.7], standard [0.1,0.3].
  Run: pytest tests/test_pipeline/test_essentiality.py -v
  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E  E�� standard residual. No Polars type errors (HS6 codes correctly cast to Utf8).
result: pending

### 5. Composite Scoring and DuckDB Export
expected: |
  Composite score = 0.35×HHI + 0.35×basket_geo_risk + 0.30×essentiality, clamped [0,1].
  Run: pytest tests/test_pipeline/test_composite.py tests/test_pipeline/test_export.py -v
  Expected: 12/12 tests pass. Key behaviours verified: basket_geo_risk is supplier-share-weighted sum of exporter geo_risk; missing geo_risk fills with 0.5 (not 0.0); missing essentiality fills with 0.1 (not 0.0); DuckDB creates fact table + countries + products dimensions; schema is idempotent (DROP I  Expected: 12/12 tests pass. Key behaviours verified: basket_geo_risk is supplier-share-weighted sum o I  Expected: 12/12 tests pass. Key behaviours verified: bpa  Expected: 12/12 tests pass. Key behaviours verified: basket_geo_risk is supplier-share-weighted sum of exporter geo_risk; missing geo_risk fills with 0.5 (not 0.0); missing essentiality fills with 0.1 (not 0.0); DuckDB creates fact table + countries + products dimensions; schema is idempotent (DROP Ionfirms full synthetic pipeline runs end-to-end with skip_scor  Expecteiso  Expected: 12/12 tests pass. Key behaviours verified: basket_geo_risk is supplier-share-s: 0
pending: 5
skipped: 0

## Gaps

