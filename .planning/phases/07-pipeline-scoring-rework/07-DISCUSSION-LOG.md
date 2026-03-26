# Phase 7 — Discussion Log

**Date:** 2026-03-26  
**Mode:** Interactive (all gray areas)

---

## Gray Areas Presented

Four gray areas were identified from codebase scouting and prior phase context.

---

### Area A — HS22 trade data role

**Question:** Should HS22 data be used for 2022-2024 trade rows, and how to handle the ~587 HS22-only codes with no HS92 equivalent?

**Options presented:**
1. Ignore HS22, HS92 only (lose 2022-2024 accuracy)
2. HS22 for 2022-2024, HS92 for pre-2022, HS22-only codes get `hs22_only` flag
3. Both revisions for 2022-2024 (aggregate/average — economically unsound)

**Decision:** Option 2. HS22 rows win for 2022–2024. HS22-only codes get `hs22_only` flag with UI badge "New product code (2022+) — no time series available."

---

### Area B — flags.py design

**Question:** How to structure the new flag system replacing tier-based classification? Config format? Flag vocabulary?

**Discussion:** User noted `fertilizer` was missing from the initial flag list. Updated to include `fertilizer` (HS chapter 31).

**Config format:** User chose full rebuild — new `flags_config.yaml`, old `essentiality_config.yaml` deleted.

**Decision:**
- 8 canonical flags: `crm_listed`, `energy`, `fertilizer`, `food`, `pharma`, `semiconductor`, `strategic_mineral`, `hs22_only`
- Config: `data/reference/flags_config.yaml`, flat structure per flag with hs2/hs4/hs6 include/exclude rules
- `pipeline/essentiality.py` renamed to `pipeline/flags.py`
- `classify_hs6()` returns `list[str]` instead of tuple

---

### Area C — substitutability score scaling

**Question:** Should `global_export_hhi` be used raw, normalized (min-max), or sqrt-transformed in the composite formula?

**Agent recommendation:** Sqrt — economically grounded (HHI is $\sum s_i^2$, sqrt recovers $1/N_{eff}$), preserves absolute meaning, spreads the 0.05–0.25 cluster, avoids dataset-composition artifacts of normalization.

**User:** "Lock it."

**Decision:** `substitutability_score = sqrt(global_export_hhi)`. Fill value = `sqrt(median)` computed dynamically from flags parquet.

---

### Area D — BACI country code & product description mapping

**Context:** Standalone todo existed: France (251), USA (842), India missing due to BACI non-standard codes. Fix requires `country_codes_V*.csv` from BACI ZIPs. Phase 7's DATA-07 already extracts these files.

**User:** "actually delete since we now use the authoritative mapping files that come with the zip file, both for ctry and product descr."

**Decision:**
- Fold in. Both country codes and product descriptions sourced from BACI's own bundled files.
- Standalone todo moved to `done/`.
- `ingest.py` uses `country_codes_V*.csv` as authoritative country mapping.
- `ingest.py` uses `product_codes_HS*.csv` as authoritative product description source.

---

## Summary

| Area | Decision |
|---|---|
| A | HS22 for 2022-2024, `hs22_only` flag on 587 new codes |
| B | Rebuild `flags_config.yaml`, 8 flags incl. fertilizer, rename to `flags.py` |
| C | `substitutability_score = sqrt(global_export_hhi)` |
| D | Authoritative BACI mapping files for country + product desc; todo closed |
