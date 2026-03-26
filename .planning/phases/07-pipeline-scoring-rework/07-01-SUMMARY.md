---
plan: 07-01
phase: 07-pipeline-scoring-rework
status: complete
completed: 2026-03-26
---

## Summary

Slimmed BACI download to HS92 + HS22 revisions only, and made HS22 the authoritative source for years 2022–2024. Wired BACI-bundled product codes CSV as the authoritative description source.

## What Was Built

- **pipeline/download.py**: Added one-line filter after `discover_baci_urls()` dedup step — only H92 and H22 entries proceed. Reduces download footprint from ~45GB to ~17GB.
- **pipeline/concordance.py**: Updated `load_product_descriptions()` to accept `raw_dir: Path | None = None`. When provided, reads `product_codes_HS22_V*.csv` first (fallback to any `product_codes_HS*_V*.csv`); returns `(description, "")` tuples. Falls through to legacy `hs_product_descriptions.csv` when no BACI file is found.
- **pipeline/ingest.py**: Added `import re`; HS22 files sorted first; non-trade CSVs (`country_codes*`, `product_codes*`) skipped; HS revision detected per file; HS92 skipped for 2022/2023/2024 when `hs22_years` set already contains that year; HS22 years tracked after each successful write.
- **pipeline/export.py**: `load_product_descriptions()` call updated to pass `raw_dir=raw_dir`.

## Verification

- All three module imports: ✓
- `H92.*H22` filter pattern in download.py: 1 match ✓
- `hs22_years` references in ingest.py: 3 matches ✓
- `raw_dir` references in concordance.py: 5 matches ✓

## Key Files Modified

- pipeline/download.py
- pipeline/concordance.py
- pipeline/ingest.py
- pipeline/export.py

## Commit

ac5ddb4 — feat(07-01): slim BACI download to HS92+HS22, HS22 authority for 2022-2024
