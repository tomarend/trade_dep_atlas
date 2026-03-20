---
phase: 02-scoring-pipeline-storage
plan: 02
subsystem: scoring
tags: [polars, parquet, wgi, freedom-house, sanctions, geopolitical-risk]

requires: []
provides:
  - geo_risk score 0-1 per (country, year): governance_risk * (1 + sanctions_intensity), clamped
  - georisk_by_country_year.parquet at data/scoring/georisk/

affects: [03-dashboard, composite-scoring, duckdb-export]

tech-stack:
  added: []
  patterns:
    - WGI → governance_risk = (2.5 - mean(WGI)) / 5.0, clamped [0,1]
    - Freedom House fallback: governance_risk = 1 - fh_score/100
    - sanctions_intensity = active_senders / 10.0, clamped [0,1]
    - geo_risk = min(1.0, governance_risk * (1 + sanctions_intensity))

key-files:
  created:
    - pipeline/georisk.py
    - tests/test_pipeline/test_georisk.py
    - data/reference/governance/README.md

key-decisions:
  - "WGI data REQUIRED (hard FileNotFoundError with setup instructions if missing)"
  - "Freedom House used as fallback ONLY when WGI missing for a country-year"
  - "GSDB sanctions: count distinct sending countries per year, normalise by 10"
  - "sanctions_intensity clamped [0,1] — 10+ senders = max severity"

patterns-established:
  - "Hard FileNotFoundError with actionable setup instructions for required reference data"
  - "Fallback data loaded lazily (only merged if WGI coverage gap exists)"

requirements-completed: [SCOR-02]

duration: 15min
completed: 2026-03-20
---

# Plan 02-02: Geopolitical Risk Scoring

**Country-year geo_risk scores derived from World Governance Indicators with Freedom House fallback and GSDB sanctions overlay; formula: geo_risk = min(1.0, governance_risk * (1 + sanctions_intensity)).**

## Performance

- **Tasks:** 1
- **Files modified:** 3 created

## Accomplishments
- `compute_governance_risk()` merges WGI + FH data, WGI takes precedence
- `compute_sanctions_intensity()` counts active senders per year, normalises to [0,1]
- `compute_geo_risk()` joins both, applies formula, writes single Parquet file
- 13/13 unit tests cover safe/risky countries, clamping, fallback precedence, sanctions logic

## Task Commits

1. **Task 1: Geo-risk scoring module** - `6fce82a` (feat)
