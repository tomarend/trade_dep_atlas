# Pitfalls Research -- v2.0

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
