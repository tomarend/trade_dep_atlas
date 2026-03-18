---
phase: 01-data-pipeline-ingestion
plan: 02
subsystem: pipeline
tags: [pycountry, yaml, concordance, hs6, iso3, country-mapping]

requires:
  - phase: 01-01
    provides: Project scaffolding, pyproject.toml, conftest fixtures
provides:
  - Country code mapping (BACI numeric → ISO3 with region, continent, re-export hub flag)
  - Historical entity tracking (Czechoslovakia, Yugoslavia, USSR → successor states)
  - HS concordance pipeline (any-revision HS6 → target with split/merge/unmapped flags)
  - Product descriptions with HS2/HS4/HS6 hierarchy and categories
affects: [01-03, scoring-pipeline, dashboard]

tech-stack:
  added: []
  patterns: [YAML-based manual overrides, dataclass domain models, pycountry resolution chain]

key-files:
  created:
    - pipeline/countries.py
    - pipeline/concordance.py
    - data/reference/country_overrides.yaml
    - data/reference/hs_product_descriptions.csv
    - tests/test_pipeline/test_countries.py
    - tests/test_pipeline/test_concordance.py
  modified: []

key-decisions:
  - "Resolution order: manual overrides → pycountry → BACI CSV for country mapping"
  - "Identity mapping (code→itself with unmapped flag) when no concordance tables exist"
  - "One-to-many splits resolved by picking first target alphabetically"
  - "Many-to-one merges detected via reverse_map check"
  - "Re-export hubs (NLD, SGP, HKG, ARE, BEL) flagged in country metadata"
  - "Concordance CSV parser supports multiple column naming conventions (WITS, custom)"

patterns-established:
  - "Concordance flags: unchanged | mapped | split | merged | unmapped"
  - "build_concordance_polars_map returns flat dict for vectorized Polars operations"
  - "validate_concordance spot-checks critical products (lithium, copper, semiconductors)"

requirements-completed: [DATA-03, DATA-04]

duration: 6min
completed: 2026-03-18
---

# Plan 01-02: Country Code Mapping + HS Concordance Pipeline

**Two standalone reference data modules that resolve BACI numeric country codes to ISO3 and map any-revision HS6 codes to a consistent target with split/merge tracking.**

## What Was Built

1. **Country mapping** (`pipeline/countries.py`):
   - `load_country_mapping()` — builds dict[int, CountryRecord] from pycountry + YAML overrides
   - `CountryRecord` — baci_code, iso3, name, aliases, region, continent, is_reexport_hub
   - `HistoricalEntity` — tracks dissolved countries with successor state lists
   - Handles Taiwan (TWN), Kosovo (XKX), Palestine (PSE) via manual overrides

2. **HS concordance** (`pipeline/concordance.py`):
   - `load_concordance()` — reads WITS-style concordance CSVs, builds forward/reverse maps
   - `apply_concordance()` — maps a single HS6 code with split/merge/unmapped flags
   - `build_concordance_polars_map()` — flat dict for vectorized Polars operations
   - `validate_concordance()` — spot-checks critical products, reports splits/merges

3. **Reference data**: country_overrides.yaml (overrides + historical + region map), hs_product_descriptions.csv (30 products with categories)

## Test Results

18 tests passing: 8 country tests + 10 concordance tests.

## Interface for Plan 01-03

```python
from pipeline.countries import load_country_mapping, CountryRecord
# dict[int, CountryRecord] — baci_code → record with iso3, region, etc.

from pipeline.concordance import load_concordance, build_concordance_polars_map, load_product_descriptions
# Concordance with forward_map, reverse_map, descriptions
# build_concordance_polars_map → dict[str, str] for Polars replace
```
