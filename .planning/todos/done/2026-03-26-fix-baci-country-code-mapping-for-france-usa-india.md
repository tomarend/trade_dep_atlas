---
created: 2026-03-26T15:40:31.141Z
title: Fix BACI country code mapping for France, USA, India
area: pipeline
files:
  - pipeline/countries.py
  - pipeline/ingest.py
  - data/raw/BACI_HS02_Y2002_V202601.csv
---

## Problem

France (ISO 250/FRA), USA (ISO 840/USA), and India (ISO 356/IND) are completely missing from the dashboard — they don't appear in the Country Exposure page or as options anywhere.

Investigation during Phase 6 UAT revealed:
- The `countries` table has FRA, USA entries (populated via pycountry)
- The `dependency_scores` table has 222 unique importers, but FRA/USA/IND are NOT among them
- The raw BACI CSV files themselves don't contain numeric codes 250, 840, or 356
- BACI uses non-standard codes: 251 (near France's 250), 842 (near USA's 840) — these are likely BACI-specific composite codes
- The `pipeline/countries.py` `_baci_code_to_iso3()` function uses standard pycountry numeric lookup which fails for these non-standard BACI codes
- The `country_overrides.yaml` reference file may need entries for these BACI-specific codes

Root cause: BACI dataset uses custom numeric country codes that don't align 1:1 with ISO 3166-1 numeric for some major economies. The pipeline's country resolution assumes standard ISO numeric codes.

## Solution

1. Check BACI's `country_codes_*.csv` reference file (should be in `data/raw/`) for the official BACI-to-ISO mapping
2. Update `country_overrides.yaml` or the resolution logic in `pipeline/countries.py` to handle BACI-specific codes (251→FRA, 842→USA, etc.)
3. Re-run the pipeline to regenerate `dependency_scores` with correct country mappings
4. Verify France, USA, India appear in the dashboard after re-ingestion
