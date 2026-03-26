# Plan 07-04 Summary — Dashboard Data Layer + Page Callbacks

**Status:** COMPLETE  
**Commit:** `f60f64d`  
**Wave:** 3

## What was done

Updated all dashboard Python files to consume the v2 DuckDB schema.
Eliminated every reference to `essentiality_score`, `essentiality_tier`, and
`essentiality_category`.

### `dashboard/data.py`

| Function | Change |
|---|---|
| `get_product_scores()` | SELECT: `essentiality_tier/score` → `COALESCE(p.flags,[]) AS flags`, `substitutability_score` |
| `get_country_summary()` | Full SQL rewrite: subquery dedupes, LEFT JOIN products, `list_contains(p.flags,...)` for `critical_count`; return key `avg_essentiality` → `avg_substitutability` |
| `get_importer_scores()` | Added LEFT JOIN products for `flags`; `essentiality_score/tier` → `substitutability_score/flags` |
| `get_product_summary()` | `AVG(essentiality_score)` → `AVG(substitutability_score)`; return key updated |
| `get_score_trend()` | Column `essentiality_score` → `substitutability_score` |
| `get_product_trend()` | Column `AVG(essentiality_score)` → `AVG(substitutability_score)` |

### `dashboard/pages/country.py`

- Weight slider label: "Essentiality" → "Substitutability"
- AG Grid column defs: replaced `essentiality_score` + `essentiality_tier` columns
  with `substitutability_score` (numeric) and `flags` (list, joined via valueFormatter)
- `update_summary_cards()`: composite formula uses `substitutability_score`;
  `critical_count` now counts `crm_listed` or `strategic_mineral` flags;
  radar theta "Essentiality" → "Substitutability"; card label updated
- `update_product_table()`: weight formula updated
- `render_drilldown()`: trend series, radar, and tier span all updated

### `dashboard/pages/product.py`

- AG Grid column defs: same replacement as country.py
- `update_product_summary()`: radar r/theta, card label, `avg_essentiality` → `avg_substitutability`
- `update_product_trend()`: `ess_vals` source column updated; trace name updated

### `dashboard/pages/about.py`

- `_tab_essentiality()` → `_tab_substitutability()`: rewrote methodology tab to
  describe the `substitutability_score = √(global_export_hhi)` formula and list
  all 8 canonical flags with descriptions
- Tab label updated from "Essentiality" to "Substitutability"

## Verification

```
grep -rn "essentiality" dashboard/ --include="*.py" | grep -v __pycache__
# exit: 1 (no matches — clean)

python3 -m py_compile dashboard/data.py dashboard/pages/country.py \
    dashboard/pages/product.py dashboard/pages/about.py
# Syntax OK
```
