# Phase 7 — Pipeline & Scoring Rework: CONTEXT

**Discussed:** 2026-03-26  
**Status:** LOCKED — all gray areas resolved, ready for planning

---

## Phase Goal

Replace the tier-based essentiality scoring system with an empirical, flag-based approach using `global_export_hhi` as the substitutability signal. Slim the BACI download to HS92 + HS22 revisions only. Use BACI's own authoritative mapping files for country codes and product descriptions. Rebuild the DuckDB schema accordingly.

---

## Decisions

### A — HS22 trade data role (LOCKED)

- Ingest HS92 CSVs for **all years** (1995–2024) as the primary time series.
- Ingest HS22 CSVs for **2022–2024 only**. For those three years, HS22 rows **win** — HS92 rows for 2022–2024 are skipped (HS22 is the more current revision).
- The ~587 product codes that appear **only** in HS22 (no HS92 equivalent) get the `hs22_only` flag and a badge in the UI: *"New product code (2022+) — no time series available."*
- `ingest.py` deduplication logic: process HS22 CSVs first for 2022–2024, then skip HS92 CSVs for those years.

### B — flags.py design (LOCKED)

- **Delete** `data/reference/essentiality_config.yaml`.
- **Create** `data/reference/flags_config.yaml` — clean YAML, flags only.
  - Structure per flag: `flag_name: {hs2_include: [], hs4_include: [], hs6_include: [], hs6_exclude: []}`.
  - Include/exclude rules are union-of-hs6, with hs6_exclude taking precedence.
- **8 canonical flags:** `crm_listed`, `energy`, `fertilizer`, `food`, `pharma`, `semiconductor`, `strategic_mineral`, `hs22_only`.
  - `fertilizer` covers HS chapter 31.
  - `hs22_only` is set programmatically from ingest, not from the YAML config.
- `pipeline/essentiality.py` → **rename** to `pipeline/flags.py`.
  - Delete `_tier_score()`.
  - Rewrite `classify_hs6()` to return `list[str]` of flag names instead of `(tier, category, crm_since)` tuple.
  - Rename `compute_essentiality_scores()` → `compute_product_flags()`.
  - Output schema: `{hs6, flags: list[str], global_export_hhi: float, crm_listed_since: str|null, hs22_only: bool}`.
  - Output parquet: `data/scoring/flags/flags_scores.parquet` (was `data/scoring/essentiality/essentiality_scores.parquet`).

### C — substitutability score scaling (LOCKED)

- **Sqrt transform**: `substitutability_score = sqrt(global_export_hhi)`.
- Rationale: HHI is $\sum s_i^2$; its square root is proportional to $1/N_{eff}$ (reciprocal of effective number of exporters) — economically meaningful as a linearised concentration measure. Preserves the zero point (0 = perfectly distributed) and ceiling (1 = single-source monopoly). Spreads the 0.05–0.25 cluster enough to make the composite weight behave as users expect, without converting to a relative rank (which would be dataset-composition-dependent).
- In `composite.py`:
  - `DEFAULT_WEIGHTS` key `"essentiality"` → `"substitutability"`.
  - Formula: `w3 * sqrt(global_export_hhi)` (was `w3 * essentiality_score`).
  - Fill value: `_SUBSTITUTABILITY_FILL = sqrt(median(global_export_hhi distribution))` — computed once at startup from the flags parquet, not hardcoded.

### D — BACI country code & product description mapping (LOCKED)

- **Fold into Phase 7.** The standalone todo "Fix BACI country code mapping for France, USA, India" is closed.
- Phase 7's DATA-07 already extracts `country_codes_V*.csv` and `product_codes_HS*.csv` from the BACI ZIP files into `data/raw/`.
- `ingest.py` must use `country_codes_V*.csv` as the **authoritative** country code → ISO mapping. No hardcoded ISO lookup table. This fixes France (BACI code 251), USA (842), and India.
- Product descriptions must be sourced from `product_codes_HS*.csv` (the BACI-bundled file), not from any separate HS description CSV. This replaces whatever hardcoded or external description source is currently used.

---

## Affected Files Summary

| File | Action | Notes |
|---|---|---|
| `pipeline/essentiality.py` | **Rename → `pipeline/flags.py`** | Delete `_tier_score()`, rewrite `classify_hs6()`, rename `compute_essentiality_scores()` |
| `pipeline/composite.py` | **Modify** | Rename weight key, update formula to `w3 * sqrt(global_export_hhi)`, dynamic fill value |
| `pipeline/export.py` | **Modify** | `essentiality_path` → `flags_path`; drop `essentiality_score/tier/category` columns; add `flags LIST(VARCHAR)`, `global_export_hhi`, `hs22_only BOOLEAN` |
| `pipeline/download.py` | **Modify** | Filter `discover_baci_urls()` to `{"HS92", "HS22"}` only; extract mapping CSVs from ZIPs |
| `pipeline/ingest.py` | **Modify** | HS22 wins for 2022–2024; use BACI `country_codes_V*.csv` for mapping; use `product_codes_HS*.csv` for descriptions |
| `pipeline/__main__.py` | **Modify** | `from pipeline.essentiality import ...` → `from pipeline.flags import ...` |
| `data/reference/essentiality_config.yaml` | **Delete** | Replaced by `flags_config.yaml` |
| `data/reference/flags_config.yaml` | **Create** | 8 flags with hs inclusion rules |
| `data/reference/essentiality_hs6.csv` | **Evaluate** | May be superseded by `flags_config.yaml`; assess during planning |
| `data/scoring/essentiality/` | **Superseded** | New output path: `data/scoring/flags/` |

---

## DuckDB Schema Changes

**Products dimension** — drop: `essentiality_category`, `essentiality_tier`, `essentiality_score`; add: `flags VARCHAR[]`, `global_export_hhi DOUBLE`, `hs22_only BOOLEAN`; keep: `crm_listed_since`.

**Trade fact table** — drop: `essentiality_score`, `essentiality_tier`; add: `substitutability_score DOUBLE` (= `sqrt(global_export_hhi)` for that hs6).

Full DROP + RECREATE pattern already used in `export.py` — no ALTER TABLE needed.

---

## Folded Todo

- ~~Fix BACI country code mapping for France, USA, India~~ → resolved by Area D (authoritative BACI mapping files).

---

## Requirements Traceability

- DATA-06: slim BACI download to HS92 + HS22
- DATA-07: extract country and product code mapping files from ZIPs
- SCOR-06: replace tier scoring with `global_export_hhi`
- SCOR-07: sqrt transform on `global_export_hhi`
- SCOR-08: `flags` list replaces `essentiality_category`
- CNTV-08: `hs22_only` flag on new codes
- CNTV-09: `fertilizer` flag (HS31)
