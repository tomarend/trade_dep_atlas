# Stack Research -- v2.0

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
