"""Rewrite corrupted research files for v2.0."""
import pathlib

BASE = pathlib.Path("/Users/tom/Documents/git/dashboard_trade_crit_dep/.planning/research")
BASE.mkdir(exist_ok=True)

STACK = """# Stack Research -- v2.0

**Milestone:** v2.0 Dashboard Redesign
**Researched:** 2026-03-26
**Confidence:** HIGH

## Current Stack (Verified)

All packages confirmed in requirements.txt / installed environment.

| Package | Version | Role |
|---------|---------|------|
| dash | >=4.0.0 | Dashboard framework (multi-page via Pages) |
| plotly | >=6.6.0 | Visualization library |
| dash-ag-grid | 33.3.3 | Data tables (AG Grid Community — free) |
| polars | >=1.36.1 | ETL pipeline (lazy Rust-based dataframes) |
| duckdb | >=1.5.0 | In-process analytical DB |
| pandas | >=2.2.0 | Thin serving layer (DuckDB cursor → DataFrame) |
| dash-cytoscape | >=1.0.2 | Network graph (TO BE REMOVED in v2.0) |

## v2.0 Stack Changes

### Remove
- `dash-cytoscape` — network graph dropped (low insight density vs implementation cost)

### No New Packages Needed
- Scatter plot: `go.Scatter` (already in plotly)
- Concentration bars: `go.Bar` horizontal (already in plotly)
- Flag badges: Dash HTML components (already available)
- Bilateral risk panel: `go.Bar` horizontal (already in plotly)

## AG Grid Sparklines — Critical Note

AG Grid sparklines (`sparklineOptions`) are **Enterprise-only**.
dash-ag-grid 33.3.3 uses AG Grid Community. Sparklines WILL silently fail.

**Solution:** Custom clientside JS `cellRenderer` drawing an SVG polyline:
```javascript
function(params) {
    const vals = params.value;  // array of 6 floats
    if (!vals || vals.length === 0) return '';
    const w = 60, h = 20;
    const min = Math.min(...vals), max = Math.max(...vals);
    const pts = vals.map((v, i) => {
        const x = (i / (vals.length - 1)) * w;
        const y = h - ((v - min) / (max - min + 0.001)) * h;
        return x + ',' + y;
    }).join(' ');
    return '<svg width="' + w + '" height="' + h + '"><polyline points="' + pts + '" stroke="#3b82f6" fill="none" stroke-width="1.5"/></svg>';
}
```

Registered via `dashGridOptions={"getRowId": ..., "cellRenderer": ...}` per column.

## BACI Data Versions

| Revision | Coverage | Files | Size |
|---------|----------|-------|------|
| HS92 | 1995–2024 (all years) | ~59 | ~16GB |
| HS22 | 2022–2024 (latest) | ~3 | ~1GB |
| All others | drop | — | ~28GB saved |

HS92 covers entire time series. HS22 used for latest-year enriched product codes (5,609 vs 5,022).

## Composite Scoring Formula -- v2.0

Old: `composite = 0.35*hhi + 0.35*geo_risk + 0.30*essentiality_score`
     (essentiality_score was tier-derived: 0.85/0.55/0.20 by hand)

New: `composite = w1*hhi + w2*geo_risk + w3*global_export_hhi`
     (global_export_hhi = HHI of global exporters of product — empirical substitutability)

`global_export_hhi` already exists in `pipeline/essentiality.py` as `compute_global_export_hhi()`.
It just wasn't used as a score driver. Now it IS the substitutability dimension.

## DuckDB Schema Delta

**products dim (add/remove columns):**
- REMOVE: `essentiality_category`, `essentiality_tier`, `essentiality_score`
- ADD: `flags LIST(VARCHAR)`, keep `global_export_hhi`, keep `crm_listed_since`

**dependency_scores fact:**
- RENAME: `essentiality_score` → `substitutability_score`
- REMOVE: `essentiality_tier`

Full DuckDB rebuild required (no ALTER TABLE for list columns in DuckDB).
"""

ARCHITECTURE = BASE / "ARCHITECTURE.md"
# Only rewrite if first line looks wrong (check for the existing file)
arch_content = ARCHITECTURE.read_text() if ARCHITECTURE.exists() else ""
if "# Architecture Research" in arch_content and len(arch_content) > 500:
    print("ARCHITECTURE.md looks OK, skipping")
else:
    print("ARCHITECTURE.md needs rewrite")

PITFALLS = """# Pitfalls Research -- v2.0

**Milestone:** v2.0 Dashboard Redesign
**Researched:** 2026-03-26
**Confidence:** HIGH

## Common Mistakes When Adding v2.0 Features

### 1. Sankey Readability -- Node Count
PITFALL: Rendering all exporters/importers creates an unreadable hairball.
The existing implementation already caps at top 10 exporters + top 10 importers (lines 525-535 product.py).
PREVENTION: Keep the cap. Consider reducing to top 8 for readability. Add "Other" aggregate node.
IMPACT: Zero analytical value from the chart.

### 2. Scatter Overplotting -- 5000+ Products
PITFALL: Plotting all ~5,000 HS6 products for one country creates an unreadable blob.
PREVENTION: Limit to top 200-500 by composite_score in the query. Add opacity=0.6.
Size markers by log(value_usd) not raw value (outliers dominate). Use LIMIT in SQL query.
IMPACT: Scatter is visually useless, defeats the insight-first goal.

### 3. AG Grid Sparklines -- Enterprise-Only
PITFALL: Using built-in AG Grid sparklines feature (sparklineOptions in columnDef).
dash-ag-grid 33.3.3 uses AG Grid Community. Sparklines silently fail or throw console errors.
PREVENTION: Use custom clientside JS cellRenderer drawing SVG polyline (60px x 20px, 6 points).
See STACK.md for the exact implementation.
IMPACT: Sparklines silently invisible or console errors every render.

### 4. DuckDB Schema -- Atomic Column Rename
PITFALL: Renaming essentiality_score in export.py but not updating data.py callbacks simultaneously.
Any dashboard code referencing essentiality_score will throw ColumnNotFound errors.
PREVENTION: Rename essentiality_score -> substitutability_score in ONE commit covering:
  export.py, data.py, country.py, product.py, methodology page.
IMPACT: Dashboard crashes on load.

### 5. HS22 + HS92 Data Mixing
PITFALL: If HS22 (2022-2024) and HS92 (all years) rows coexist in processed/ parquet
without deduplication, some year-product-country tuples appear twice and are double-counted.
PREVENTION: Current ingest.py already deduplicates by (year, exporter, importer, hs6) -- first file wins.
HS92 should be downloaded first so it wins for 2022-2024 overlap. Verify this logic in ingest.py.
IMPACT: 2022-2024 scores inflated or incorrect -- silent data quality issue.

### 6. Global Export HHI -- Static vs Year-Specific
PITFALL: Making global_export_hhi year-varying (recomputing per year separately).
Currently computed over ALL years aggregated -- this is a structural measure (how concentrated
is global production of this product), not a time-varying measure.
PREVENTION: Keep it static (aggregated over all years). Document this in methodology page.
Year-varying global HHI would be noisy and hard to interpret as "substitutability".
IMPACT: Substitutability dimension behaves erratically in time series charts.

### 7. Pipeline Incremental Runs -- Partial State
PITFALL: Running only parts of the pipeline (e.g., only composite.py) after a schema change
leaves the DuckDB in a partially-updated state mixing old and new columns.
PREVENTION: After any schema change (adding flags, renaming columns), run the FULL pipeline
from export.py onwards. Add a schema version check in export.py that fails fast if schema mismatch.
IMPACT: Hours of confusing bugs from mixed old/new column names.

### 8. Dash Callback Circular Dependencies
PITFALL: Adding bilateral_risk_panel and scatter_risk as separate callbacks on country page
that both write to overlapping Output targets.
Dash raises errors if two callbacks write to the same Output component.
PREVENTION: Combine related chart updates into single callbacks where they share inputs.
Use pattern-matching callbacks (ALL/MATCH) only if genuinely needed.
IMPACT: Callback registration error on app startup -- app won't start.

### 9. Weight Sliders -- Label Mismatch
PITFALL: Not updating slider label for the third weight component after v2 replaces essentiality
with substitutability (global_export_hhi). The underlying weights system is unchanged
(still 3 components summing to 1.0), but labels must be updated consistently.
PREVENTION: Search for "essentiality" across dashboard/ -- replace ALL display labels:
  composite.py (formula comment), data.py (column alias), country.py (slider label),
  product.py (any references), methodology page (explanation text).
IMPACT: UI shows "Essentiality Weight" for what is now "Substitutability Weight" -- confusing.

### 10. crm_listed_since -- Preserve Through Refactor
PITFALL: Dropping crm_listed_since when repurposing essentiality.py -> flags.py.
This field is useful for "EU CRM listed since [year]" badge in product view.
PREVENTION: Explicitly keep crm_listed_since in flags.py output and export.py schema.
It is separate from the scoring change -- just preserve it.
IMPACT: Loss of useful product metadata, badge feature unavailable.

### 11. DuckDB Full Rebuild Required for List Columns
PITFALL: Trying to ALTER TABLE to add a LIST(VARCHAR) flags column to existing DuckDB.
DuckDB does not support ALTER TABLE ADD COLUMN for list types in all versions.
PREVENTION: Full DuckDB rebuild when adding flags column. Drop and recreate from Parquet.
Script: `python -m pipeline --rebuild-db` should drop and recreate the .duckdb file.
IMPACT: Migration script fails, schema in broken state.
"""

(BASE / "STACK.md").write_text(STACK)
print(f"STACK.md written: {len(STACK)} chars")

(BASE / "PITFALLS.md").write_text(PITFALLS)
print(f"PITFALLS.md written: {len(PITFALLS)} chars")

print("Done.")
