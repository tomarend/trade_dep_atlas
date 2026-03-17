# Pitfalls Research

**Domain:** Trade dependency analytics dashboard (BACI data, HHI, geopolitical risk, Dash/Plotly)
**Researched:** 2026-03-17
**Confidence:** HIGH (data/methodology pitfalls), MEDIUM (visualization/architecture pitfalls)

---

## Critical Pitfalls

### Pitfall 1: HS Code Revision Breaks Time Series

**What goes wrong:** The Harmonized System is revised roughly every 5 years (HS 1996, HS 2002, HS 2007, HS 2012, HS 2017, HS 2022). Product codes split, merge, or get reassigned between revisions. Naively joining BACI data across years treats different physical products as the same HS6 code, or creates spurious discontinuities where a code was split into two. For example, an HS6 code for "lithium carbonate" in HS 2017 may not exist in HS 2007 — it was lumped under a broader category. Your HHI time series for that product will show a false structural break at the revision boundary.

**Why it happens:** BACI uses the HS revision that was current when each year's data was reported. Developers assume HS6 codes are stable identifiers across the full 20-year span. They are not — roughly 15-20% of HS6 codes change with each revision.

**How to avoid:**
- Use BACI's built-in HS revision field and apply concordance tables (available from WITS/World Bank: H0↔H1↔H2↔H3↔H4↔H5↔H6) to map all years to a single consistent revision
- Concordance mappings are many-to-many: when one old code maps to multiple new codes (or vice versa), you must decide on an aggregation strategy (aggregate up to a "concorded" group, or proportionally split values)
- The safest approach: define "consistent HS6 groups" by taking the transitive closure of all codes linked across revisions, then aggregate to these groups for time series analysis
- Flag products on the dashboard where concordance introduces ambiguity

**Warning signs:**
- Sudden appearance/disappearance of HS6 codes at 5-year boundaries (2002, 2007, 2012, 2017)
- Time series with implausible jumps in trade values at revision years
- Different product counts per year in your processed data

**Phase to address:** Data pipeline phase (ingestion/ETL). Must be solved before any metrics are computed.

---

### Pitfall 2: Re-exports Inflate Supplier Concentration Artificially

**What goes wrong:** Countries like the Netherlands, Singapore, Hong Kong, and the UAE are major re-export hubs. Raw COMTRADE data (and by extension BACI) records these as "exports from Netherlands" even though the goods originated in China or elsewhere. If you compute HHI on direct bilateral flows, the Netherlands appears as a major supplier of products it merely transships. This deflates your HHI artificially (more apparent suppliers) or misattributes geopolitical risk (Netherlands looks safe, but the actual origin may not be).

**Why it happens:** Trade statistics record country-of-consignment (last country shipped from), not country-of-origin, for many reporters. BACI reconciles reporter/partner discrepancies but does not resolve the re-export problem — it's a fundamental limitation of customs data.

**How to avoid:**
- Accept this as a known limitation and document it prominently in the dashboard
- For key hub countries (NL, SG, HK, AE, BE), consider flagging their exports with a "likely re-export hub" marker
- Do NOT attempt to "correct" re-exports algorithmically without a solid methodology — it's an open research problem
- Consider using BACI's quantity data alongside values: re-export hubs sometimes show unusually high value/quantity ratios for commodities they don't produce
- EU intra-trade: for EU member states, re-exports within the EU are particularly common; document this

**Warning signs:**
- Netherlands/Belgium appearing as top-5 global exporters of tropical commodities, rare earths, or other products they clearly don't produce
- HHI values that seem surprisingly low for products known to be concentrated (e.g., rare earths)

**Phase to address:** Data pipeline + metric computation phase. Document limitation in dashboard UI.

---

### Pitfall 3: HHI Scale Confusion (0-1 vs 0-10,000)

**What goes wrong:** HHI can be expressed on two scales: as a decimal (0 to 1, where shares are fractions) or as points (0 to 10,000, where shares are percentages). Academic trade papers, the US DOJ, and the World Bank all use different conventions. Mixing scales — computing HHI on one scale but applying thresholds from a source using the other — leads to nonsensical classifications. An HHI of 0.25 (decimal) means "highly concentrated," but if you're on the 10,000 scale, 0.25 means "virtually no concentration."

**Why it happens:** Wikipedia, DOJ guidelines, and WITS all present HHI differently. Copy-pasting threshold values without checking the scale is a common error. The DOJ uses the 10,000-point scale (>2,500 = highly concentrated). Trade economics papers typically use the 0-1 scale (>0.25 = highly concentrated). They are mathematically identical but off by a factor of 10,000.

**How to avoid:**
- Pick ONE scale and stick to it throughout the entire codebase — document which scale in a constants/config file
- Recommended: use the 0-1 scale (standard in academic trade literature) since market shares naturally sum to 1.0
- Define concentration thresholds as named constants with comments citing the source
- Unit test HHI calculations with known inputs (e.g., 4 equal suppliers → HHI = 0.25 on 0-1 scale)

**Warning signs:**
- HHI values that are all near zero or all near 10,000
- Threshold comparisons that flag everything or nothing as "concentrated"

**Phase to address:** Metric computation phase. Verify with unit tests before building any visualization.

---

### Pitfall 4: HHI Computed at Wrong Aggregation Level

**What goes wrong:** Computing HHI at the wrong level of granularity produces misleading results. HHI should be computed per (importer, product, year) tuple — showing how concentrated a specific country's imports of a specific HS6 product are across supplier countries. Common mistakes: computing HHI across all products for a country (too aggregated — dilutes product-level concentration), or computing it at HS2/HS4 level (too coarse — masks HS6-level dependencies).

**Why it happens:** Raw BACI data has ~200 importers × ~5,000 HS6 products × ~20 years = ~20 million potential HHI values. Developers sometimes aggregate prematurely for performance, or confuse "country export diversification HHI" (across products) with "import concentration HHI" (across suppliers for one product).

**How to avoid:**
- Define the HHI computation precisely: for each (importer i, product p, year t), compute $HHI_{i,p,t} = \sum_j s_{j}^2$ where $s_j$ is the share of exporter $j$ in country $i$'s total imports of product $p$ in year $t$
- Only aggregate HHI values for display (e.g., average HHI across products for a country view), never for computation
- Store per-(importer, product, year) HHI in the pre-computed dataset

**Warning signs:**
- All countries showing similar HHI values (means aggregation washed out product-level variation)
- Known concentrated products (e.g., rare earths from China) not showing high HHI

**Phase to address:** Metric design + pipeline computation phase.

---

### Pitfall 5: Geopolitical Risk Scores Become Stale or Unavailable

**What goes wrong:** Geopolitical risk is the most subjective dimension of the composite dependency score. Freedom House publishes annually (with a ~2-month lag), V-Dem publishes annually (March release). Sanctions lists change frequently. If you hardcode scores or use a single snapshot, your dashboard reflects a point-in-time assessment that becomes stale. Worse, governance indices don't cover all territories (Taiwan, Kosovo, Palestine have inconsistent coverage), and matching country names/codes between trade data and governance datasets is error-prone.

**Why it happens:** Trade data uses ISO 3166 numeric codes (or BACI's own country codes). Freedom House uses country names. V-Dem uses its own country-year identifiers. There is no universal join key. Developers end up with a brittle mapping table that breaks when any source changes naming conventions.

**How to avoid:**
- Create a canonical country mapping table as a first-class data artifact, mapping BACI country codes → ISO 3166 alpha-3 → Freedom House names → V-Dem codes
- Use ISO 3166 alpha-3 as the lingua franca
- Handle edge cases explicitly: Taiwan (not in UN data but in trade data), Hong Kong vs. China, territories
- Version the governance data with a clear "as-of" date displayed on the dashboard
- Design the pipeline so governance data can be refreshed independently of trade data
- For sanctions: use a simple, maintainable YAML/JSON list rather than scraping live — sanctions change by executive order and need human review

**Warning signs:**
- Join producing NULL risk scores for significant trading partners
- Country count mismatch between trade data and governance data
- Dashboard showing "2023 governance data" with "2022 trade data" without labeling the discrepancy

**Phase to address:** Data pipeline phase (country mapping + governance ingestion). Dashboard should display data vintage clearly.

---

### Pitfall 6: Product Essentiality Classification Devolves into Subjective Guesswork

**What goes wrong:** There is no universal, agreed-upon "essentiality" score for HS6 products. The EU CRM list covers ~34 raw materials, but your dashboard has ~5,000 HS6 products. Mapping HS6 codes to essentiality requires (a) defining what "essential" means (critical minerals? food? energy? pharma? defense?) and (b) mapping HS6 codes to these categories. Developers either over-engineer a complex scoring system that can't be validated, or throw together an ad-hoc classification that doesn't survive scrutiny.

**Why it happens:** Essentiality is inherently context-dependent (essential for whom? for what?). The EU CRM list is material-based (lithium, cobalt) not HS6-based. Mapping "cobalt" → HS6 codes requires knowing which HS6 codes contain cobalt (ores, oxides, unwrought, waste/scrap, articles). BEC (Broad Economic Categories) classification helps but is coarse.

**How to avoid:**
- Start with a simple, defensible classification rather than a complex scoring system:
  - Binary categories: "critical raw material" (mapped from EU CRM list → HS6), "energy" (HS27), "food/agriculture" (HS01-24), "pharmaceutical" (HS30), "semiconductor inputs" (specific HS codes), "other"
  - Assign a hardcoded essentiality weight per category (e.g., CRM = 1.0, energy = 0.9, food = 0.8, pharma = 0.7, other = 0.3)
- Use the EU CRM list + USGS critical minerals list as authoritative sources, and cite them explicitly
- Make the classification a standalone, editable data file (CSV/YAML), not buried in code
- Display the essentiality methodology on the dashboard so users understand it's a parameter, not ground truth

**Warning signs:**
- More than 50% of products classified as "essential" (too permissive)
- Fewer than 2% classified as "essential" (too restrictive, only captures CRM)
- Inability to explain why a specific product got its score

**Phase to address:** Metric design phase. Should be defined before pipeline computation, reviewed during dashboard design.

---

### Pitfall 7: Dash Callback Chain Creates Unresponsive Dashboard

**What goes wrong:** Dash's callback architecture is synchronous by default. Each user interaction triggers server-round-trips. With a dashboard that has multiple linked views (country selector → product table → HHI chart → map → Sankey), a single dropdown change can trigger a cascade of 4-5 sequential callbacks. If any callback takes >500ms (e.g., reading a large Parquet file, filtering a DataFrame), the UI freezes for seconds. This is the #1 user experience killer for Dash dashboards with large datasets.

**Why it happens:** Developers design the dashboard with logical callback chains (A triggers B triggers C) without considering round-trip latency. The "pre-compute everything" strategy helps, but if pre-computed data is still millions of rows and needs filtering, each callback still has a floor cost.

**How to avoid:**
- Pre-compute aggressively: the dashboard should serve pre-aggregated views, not compute on the fly. Target: <50ms per callback
- Use `dcc.Store` for intermediate data that multiple callbacks share (avoid redundant computation)
- Use clientside callbacks (`app.clientside_callback`) for simple transformations (filtering, formatting) that don't need Python
- Use `prevent_initial_call=True` on callbacks that shouldn't fire on page load
- Install `orjson` for faster JSON serialization (up to 750ms improvement per Dash docs)
- For large data: Parquet files with partition-by-country or partition-by-year, so reads are targeted
- Consider `dash.long_callback` or background callbacks for any operation that might exceed 1 second
- Plotly SVG rendering chokes above ~15K points — use `scattergl` (WebGL) for scatter plots

**Warning signs:**
- UI takes >2 seconds to respond to a dropdown change
- Browser console shows multiple pending callback requests
- "Loading..." spinners appearing for simple filter operations

**Phase to address:** Dashboard implementation phase. Architecture decisions (pre-computation granularity) in pipeline phase.

---

### Pitfall 8: Sankey Diagrams Become Unreadable Spaghetti

**What goes wrong:** Plotting a full Sankey diagram of "all suppliers → importer for product X" with 50+ source countries produces an unreadable mess of overlapping links. Trade data is inherently dense — even for one product, dozens of countries may have non-zero exports. The same problem applies to "all products → top supplier" views. Without aggressive filtering, Sankey diagrams communicate less than a simple bar chart.

**Why it happens:** Sankey diagrams are visually impressive in demos with 5-10 nodes, so developers reach for them first. But real trade data typically has a long tail of small suppliers, and Plotly's Sankey implementation renders ALL links, with no automatic "other" bucket or significance threshold.

**How to avoid:**
- Implement a "top N + other" pattern: show the top 5-8 suppliers as named nodes, aggregate all remaining into an "Other" node
- The threshold for "top N" should be dynamic (e.g., suppliers contributing >2% of imports)
- Add a tooltip on the "Other" node showing how many countries it contains
- Limit Sankey diagrams to specific analytical questions ("Where does Germany get its cobalt?"), not general-purpose views
- For product-level views (many products for one importer), use treemaps or bar charts instead
- Always provide an alternative table view alongside the Sankey

**Warning signs:**
- More than 10 nodes on either side of the Sankey
- Links that are too thin to click or hover
- Users unable to extract specific numbers from the visualization
- Sankey taking >1 second to render

**Phase to address:** Dashboard design/implementation phase.

---

### Pitfall 9: Choropleth Maps That Mislead

**What goes wrong:** Showing HHI or dependency scores on a world choropleth map introduces classic cartographic biases: Russia and Canada dominate visually due to land area, while Singapore and Hong Kong (major trade hubs) are invisible. Oceans create visual separation that implies trade isolation. Color scales that aren't carefully chosen make mid-range values indistinguishable.

**Why it happens:** Choropleth maps are easy to make with Plotly (`px.choropleth`) and look impressive, so they're the first thing developers build. But geographic area has no relationship to trade importance.

**How to avoid:**
- Use a diverging color scale with a meaningful midpoint (e.g., HHI = 0.25 as the "high concentration" threshold)
- Consider a bubble map (cartogram) where bubble size represents trade value and color represents the dependency score — decouples visual from land area
- Provide a regional zoom (Europe, East Asia, etc.) since many trade-important countries are physically small
- Show a ranked bar chart or table alongside the map as the primary analytical view
- Never use a choropleth as the only view for a metric — always pair with a sortable table

**Warning signs:**
- Users saying "Africa looks really bad" when it's actually just large with missing data (gray = no data)
- Inability to distinguish between small country scores
- Color scale showing everything as one shade (data range too compressed)

**Phase to address:** Dashboard visualization design phase.

---

### Pitfall 10: Data Pipeline and Dashboard Tightly Coupled

**What goes wrong:** The pipeline (BACI download → processing → metric computation) gets interleaved with the dashboard code. DataFrame transformations happen inside Dash callbacks. Pipeline scripts import dashboard components. The result: you can't run the pipeline without starting the dashboard, you can't test metrics without a browser, and changing the pipeline breaks the UI.

**Why it happens:** In a solo project, it's fastest to build incrementally: load data in a notebook, add a chart, wrap it in Dash, add more computation. By the time the dashboard works, the pipeline logic is scattered across callbacks, modules, and notebooks.

**How to avoid:**
- Enforce a strict boundary: the pipeline produces files (Parquet/CSV), the dashboard reads them. They share no code except a schema definition
- Pipeline: `src/pipeline/` — downloads, processes, writes to `data/processed/`
- Dashboard: `src/dashboard/` — reads from `data/processed/`, renders
- The pipeline should be runnable as a standalone CLI command (`python -m pipeline.run`)
- The dashboard should start with a check: "do processed files exist? If not, tell user to run pipeline"
- Use a data contract: define the expected schema of each processed file in a shared constants module

**Warning signs:**
- `import dash` appearing in pipeline code
- DataFrame `.groupby()` or `.merge()` calls inside Dash callbacks
- Dashboard start failing because BACI download failed

**Phase to address:** Project structure/scaffolding phase (earliest).

---

### Pitfall 11: BACI Data Volume Causes Memory Exhaustion

**What goes wrong:** A single year of BACI HS6 data is ~200MB CSV. Twenty years = ~4GB raw. Loading everything into a single pandas DataFrame exceeds the memory of most development machines (16GB) and is completely unnecessary for pre-computation. But developers who prototype in Jupyter notebooks with `pd.read_csv('BACI_*.csv')` don't notice until production.

**Why it happens:** Pandas loads entire files into memory as float64 by default. A column of HS6 codes stored as int64 uses 8 bytes per row when 4 bytes (int32) or even 3 bytes suffices. String columns for country names waste memory when categorical encoding would use a fraction.

**How to avoid:**
- Process one year at a time in the pipeline — never load all years simultaneously
- Use chunked reading (`pd.read_csv(..., chunksize=500_000)`) or process year-by-year
- Specify dtypes explicitly: country codes as `int32`, HS6 as `int32`, value as `float32`, quantity as `float32`
- Output processed data as Parquet (columnar, compressed) — not CSV
- Consider Polars instead of pandas for the pipeline: lower memory footprint, faster groupby
- For the dashboard: read only the pre-aggregated data (millions of rows → hundreds of thousands after aggregation)

**Warning signs:**
- `MemoryError` or system swap thrashing during pipeline runs
- Pipeline taking >30 minutes to process
- Processed output files >1GB

**Phase to address:** Data pipeline architecture phase.

---

### Pitfall 12: Missing/Zero Trade Values Treated Inconsistently

**What goes wrong:** BACI has extensive coverage but still has gaps. A missing row (no record of country A importing product P from country B) could mean: (a) zero trade, (b) trade below reporting threshold, (c) data not reported by that country, or (d) the country didn't exist that year (e.g., South Sudan before 2011). Treating all missing records as "zero trade" inflates the denominator when computing market shares and deflates HHI. Treating them as "NA" and dropping them risks excluding real zeros.

**Why it happens:** BACI is a sparse dataset — it only contains records where trade occurred. But when you pivot to a country × supplier matrix for HHI computation, you must decide what to do with empty cells.

**How to avoid:**
- For HHI computation: only use reported positive trade flows. HHI is computed over actual suppliers, not over all possible suppliers. An importer that only has 3 suppliers for a product should have HHI computed over those 3
- Never fill missing bilateral flows with zero before computing shares — this artificially lowers concentration
- Track which countries report data in each year (BACI provides reporting metadata). Countries that don't report at all should be excluded, not treated as having zero imports
- For time series: mark years where a country didn't report as "no data" rather than "zero dependency"
- Handle country births/deaths: Yugoslavia → successor states, Sudan → Sudan + South Sudan, etc.

**Warning signs:**
- HHI for all products in a country suddenly drops to near-zero for one year (country didn't report)
- Countries like Somalia or North Korea showing zero dependency (they don't report trade data, but they trade)

**Phase to address:** Data pipeline phase (data cleaning and validation).

---

### Pitfall 13: Composite Dependency Score Weights Are Unjustified

**What goes wrong:** The composite score combining HHI, geopolitical risk, and essentiality requires weights (e.g., `score = 0.4*HHI + 0.3*geo_risk + 0.3*essentiality`). Arbitrary weight choices completely change the ranking of vulnerable products and countries. If HHI is weighted too heavily, a country importing steel from 2 friendly countries ranks as more vulnerable than a country importing critical minerals from 10 countries including several adversaries. If essentiality dominates, every food product looks critical regardless of supplier diversification.

**Why it happens:** There's no theoretically "correct" weighting. Developers pick round numbers (equal weights, or 40/30/30) and move on. The composite score then drives the entire dashboard narrative without users understanding that different weights would tell a different story.

**How to avoid:**
- Make weights adjustable in the dashboard UI (sliders) — this is a differentiating feature for a portfolio piece
- Show sub-scores alongside the composite (don't hide the components)
- Default to equal weights but provide presets ("geopolitical focus," "supply chain focus," "essentiality focus")
- Normalize all sub-scores to the same range (0-1) before combining — if HHI is 0-1 but geo_risk is 0-100, the composite is meaningless
- Include a methodology panel in the dashboard explaining the composite construction

**Warning signs:**
- One sub-score dominating the composite for nearly all products
- Composite rankings that don't pass a smell test (e.g., water as more critical than rare earths)
- Inability to explain to a viewer why product X ranks higher than product Y

**Phase to address:** Metric design phase + dashboard UI phase (for interactive weights).

---

## Moderate Pitfalls

### Pitfall 14: BACI Country Codes ≠ ISO Codes

**What goes wrong:** BACI uses its own numeric country codes that don't match ISO 3166. While many overlap, edge cases (e.g., territories, former countries) differ. Joining BACI data with governance indices or GIS shapefiles by assuming ISO codes produces silent mismatches and dropped rows.

**How to avoid:** Download the BACI country concordance table from CEPII and build your mapping through it. Never assume numeric codes match.

**Warning signs:** Country count after joins doesn't match expectations. Major trading nations missing from visualizations.

**Phase to address:** Data pipeline phase.

---

### Pitfall 15: Global Variables in Dash Break Multi-User Serving

**What goes wrong:** Storing filtered DataFrames in module-level variables means one user's filter selection mutates state for all other users. The first user sees correct data; subsequent users see progressively filtered subsets. This is a known Dash anti-pattern documented in official docs.

**How to avoid:** Never modify global DataFrames in callbacks. Use `dcc.Store` for session state. Reassign filtered data to local variables inside callbacks. Test with two browser tabs simultaneously.

**Warning signs:** Data appearing to "shrink" across interactions. Different results in incognito vs. regular browser.

**Phase to address:** Dashboard implementation phase.

---

### Pitfall 16: Year-over-Year Volatility Mistaken for Trends

**What goes wrong:** Trade data is volatile year-to-year due to commodity price swings, one-off purchases, and reporting delays. A single large shipment of military equipment can spike a country's import concentration for one year. Showing raw yearly HHI on a line chart without smoothing makes every series look erratic.

**How to avoid:** Offer both raw and 3-year rolling average views. Default to rolling average for trend analysis. Flag single-year spikes with a tooltip explaining volatility. Consider using value-based AND quantity-based HHI to separate price effects from volume effects.

**Warning signs:** Time series that look like random noise. Users unable to identify any trends.

**Phase to address:** Metric computation + dashboard visualization phase.

---

### Pitfall 17: Neglecting Dashboard Loading States and Error States

**What goes wrong:** Selecting a country with sparse trade data returns empty charts. Selecting a product with no imports returns blank tables. The user sees empty space with no explanation of why.

**How to avoid:** Add loading spinners (`dcc.Loading`), empty state messages ("No data available for this selection"), and graceful fallbacks. Pre-validate which country/product/year combinations have data and disable impossible selections.

**Warning signs:** Blank white space where charts should be. Users reporting "the dashboard is broken" when it's actually working correctly on sparse data.

**Phase to address:** Dashboard implementation phase.

---

### Pitfall 18: Python Project Structure Without Clear Entrypoints

**What goes wrong:** With both a pipeline and a dashboard in one repo, developers create a flat structure with `pipeline.py`, `dashboard.py`, `utils.py`, `config.py` all in the root. This becomes unnavigable quickly. Imports break depending on how scripts are invoked. `PYTHONPATH` hacks proliferate.

**How to avoid:**
```
src/
  pipeline/
    __init__.py
    download.py
    transform.py
    metrics.py
    run.py
  dashboard/
    __init__.py
    app.py
    layouts/
    callbacks/
  shared/
    __init__.py
    constants.py
    country_mapping.py
data/
  raw/           # BACI downloads (gitignored)
  processed/     # Pipeline output (Parquet)
  reference/     # Country mappings, essentiality classifications
```

Use `pyproject.toml` with package discovery. Run pipeline as `python -m src.pipeline.run`. Run dashboard as `python -m src.dashboard.app`.

**Phase to address:** Project scaffolding phase (first phase).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode essentiality scores in Python | Ship faster | Can't update without code change; no audit trail | Prototype only; must extract to data file before v1 |
| Skip HS concordance (use raw codes) | Simpler pipeline | Broken time series; misleading trends | Never for multi-year analysis |
| Single CSV for all processed data | Simple I/O | Slow dashboard reads; no partial updates | Acceptable if total processed data <100MB |
| Compute metrics inside Dash callbacks | Faster prototyping | Unresponsive UI; untestable metrics | Only during early exploration |
| Use pandas for full pipeline | Familiar API | Memory exhaustion on full BACI data | Fine if processing year-by-year with explicit dtypes |
| Equal weights for composite score | No justification needed | Hides analytical choices from users | OK as default if weights are adjustable |
| Hardcode country mapping | Works for current BACI version | Breaks on next BACI release or governance data update | Never; always use a reference table |
| Skip data validation in pipeline | Runs faster | Silently propagates bad data to dashboard | Never for production; OK for spike/prototype |
| Inline CSS/styling in Dash layout | Quick visual iteration | Inconsistent look; hard to restyle | Early prototyping only |
| No loading states | Less code | Users think dashboard is broken | Never for any user-facing version |

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| BACI download/ingestion | HS code versioning (#1), memory exhaustion (#11), missing values (#12) | Build concordance pipeline first; process year-by-year; validate row counts |
| Metric computation (HHI) | Scale confusion (#3), wrong aggregation (#4), missing values (#12) | Unit test with known examples; parameterize by (importer, product, year) |
| Geopolitical risk scoring | Stale scores (#5), country code mismatch (#14) | Canonical country mapping table; version governance data; display vintage |
| Essentiality classification | Subjective guesswork (#6), unjustified scope | Use EU CRM list as anchor; make classification editable; document methodology |
| Composite score | Weight justification (#13), score normalization | Interactive weights in UI; show sub-scores; normalize to 0-1 |
| Dashboard architecture | Callback chains (#7), global variables (#15), pipeline coupling (#10) | Pre-compute aggressively; use dcc.Store; strict file boundary |
| Visualization design | Spaghetti Sankey (#8), misleading maps (#9), missing states (#17) | Top-N filtering; alternative views; loading/empty states |
| Project structure | Flat structure (#18) | Set up src/ layout in very first phase |

---

## Sources

- Dash official docs: Performance (https://dash.plotly.com/performance)
- Dash official docs: Sharing Data Between Callbacks (https://dash.plotly.com/sharing-data-between-callbacks) — verified HIGH confidence
- Wikipedia: Herfindahl-Hirschman Index (https://en.wikipedia.org/wiki/Herfindahl-Hirschman_index) — verified HIGH confidence
- WITS/World Bank: Product Concordance tables (https://wits.worldbank.org/product_concordance.html) — verified HIGH confidence
- WITS/World Bank: Trade Indicators methodology (https://wits.worldbank.org/wits/wits/witshelp/Content/Utilities/e1.trade_indicators.htm) — verified HIGH confidence
- Freedom House: Freedom in the World data (https://freedomhouse.org/report/freedom-world) — verified HIGH confidence
- V-Dem: Dataset v16, March 2026 (https://v-dem.net/data/the-v-dem-dataset/) — verified HIGH confidence
- EU Commission: Critical Raw Materials 2023 list (https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials_en) — verified HIGH confidence
- Plotly: Sankey Diagram documentation (https://plotly.com/python/sankey-diagram/) — verified HIGH confidence
- CEPII BACI methodology — MEDIUM confidence (CEPII site returning 500 errors at time of research; relying on known characteristics from BACI working papers and training data)
