# Project Research Summary

**Project:** Trade Critical Dependencies Dashboard
**Domain:** Trade dependency analytics (international economics)
**Researched:** 2026-03-17
**Confidence:** HIGH

## Executive Summary

This project is an analytical dashboard that combines bilateral trade data (CEPII BACI), geopolitical risk indices, and product essentiality classifications to surface import vulnerabilities at HS6 product granularity across ~200 countries over ~20 years. No existing tool occupies this niche — WITS and OEC show trade flows without risk framing, EU RMIS does supply-risk assessment but only for ~70 critical raw materials, and resourcetrade.earth covers only natural resources. The composite scoring approach (HHI concentration + geopolitical risk + product essentiality) is the core differentiator and the foundation everything else rests on.

The recommended approach uses a strict pipeline/serve split: Polars processes multi-GB BACI CSVs into pre-computed Parquet metrics, DuckDB stores and serves those metrics as an in-process analytical database, and Dash 4.0 with Plotly 6 renders interactive visualizations. This architecture keeps each tool in its strength zone — Polars for heavy ETL, DuckDB for fast filtered queries, pandas only as a thin serving layer inside callbacks. The stack is Python end-to-end, with all packages verified on PyPI as of March 2026.

The dominant risks are data-layer: HS code revision breaks across the 20-year time series (15-20% of codes change per revision), re-export hubs inflating supplier counts, and the inherent subjectivity of geopolitical risk scores and essentiality classifications. On the dashboard side, the main risk is callback chain latency — multiple linked views must all respond in <1 second, which demands aggressive pre-computation. All of these are solvable with disciplined pipeline design and explicit data contracts between layers.

## Key Findings

### Recommended Stack

The stack targets Python ≥3.12 with Dash 4.0 (Feb 2026) as the dashboard framework and Plotly 6.6 for visualization. Dash 4.0's Pages feature enables multi-view routing (country→products, product→countries) with background callbacks for any slow operations.

**Core technologies:**
- **Polars 1.36** (ETL pipeline): Rust-based, lazy evaluation keeps memory bounded on 5-10GB BACI CSVs. 5-10× faster than pandas for groupby/join workloads
- **DuckDB 1.5** (analytical storage): In-process columnar DB, queries pre-computed metrics in <50ms. Zero-config deployment — single file. Direct Parquet ingestion
- **Dash 4.0 + Plotly 6.6** (dashboard): Native choropleth maps, Sankey diagrams, animated charts. Pages for multi-view routing. AG Grid for tables replacing deprecated dash-table
- **dash-cytoscape 1.0** (network graphs): Force-directed trade dependency networks. Official Plotly wrapper, mature API
- **dash-ag-grid 33.3** (data tables): Sorting, filtering, pagination, conditional formatting. Free AG Grid Community tier is sufficient
- **uv 0.10** (package management): 10-100× faster than pip, lockfile support, integrated venv management

**Data volume context:** Raw BACI is ~100-200M rows (~5-10GB CSV). Pre-computed metrics compress to ~500MB-1GB Parquet → ~300-600MB DuckDB file. Per-callback queries return ~5,000 rows in <50ms.

### Expected Features

**Must have (table stakes):**
- Country/product selectors with search and HS hierarchy browsing (T1, T2)
- Ranked vulnerability tables sortable by composite score and sub-scores (T3, T4)
- Time series charts showing score evolution over ~20 years (T5)
- Choropleth world map colored by dependency score (T6)
- Composite score display with decomposition into sub-scores (T7)
- Supplier breakdown for any product-country pair (T9)
- Methodology explanation page for analytical credibility (T8)

**Should have (differentiators for v1):**
- Composite vulnerability scoring combining HHI + geo risk + essentiality — the core differentiator (D1)
- Geopolitical risk layer on trade flows turning raw data into intelligence (D2)
- Dual entry points: Country→Products AND Product→Countries with cross-linking (D5)
- Sankey diagrams showing risk-colored supplier flows — visual showpiece (D3)
- Score decomposition radar/spider charts distinguishing concentration vs. risk vs. essentiality (D7)
- Product essentiality classification drawing from EU CRM + USGS lists (D6)

**Defer to v1.x/v2+:**
- Network graph visualization (D4) — complex to make readable; add after Sankey proves value
- Sparklines in tables (D8), animated temporal evolution (D9), "what changed" alerts (D10)
- Export dependency analysis, comparison mode, sector aggregation, API (v2+)

**Anti-features (explicitly exclude):**
- Tariff simulation / policy modeling (A1) — different domain entirely
- Predictive forecasting (A2) — BACI is retrospective; extrapolation is unreliable
- User accounts / auth (A6) — use shareable URL state instead
- AI chat interface (A7) — gimmick that detracts from structured UX

### Architecture Approach

Three hard-boundaried components with a file-based contract (DuckDB database) between them: an offline batch pipeline (Polars → Parquet → DuckDB), a data access layer (parametrized SQL → pandas), and a Dash 4.0 multi-page app with pure figure functions and reusable components.

**Major components:**
1. **Data pipeline** (`pipeline/`): CLI-runnable batch ETL — download BACI, compute HHI/geo-risk/essentiality/composite, write Parquet, load DuckDB. Processes year-by-year with Polars lazy mode to keep memory bounded
2. **Storage + data access** (`data/`): DuckDB singleton connection (read-only, thread-safe), parametrized query functions returning pandas DataFrames. No SQL in page files
3. **Dashboard app** (`pages/`, `figures/`, `components/`): Dash Pages for routing, pure figure functions (DataFrame → Figure), shared components (navbar, selectors, score cards, AG Grid tables). Page files orchestrate — <200 lines each

**Key architectural patterns:**
- Pipeline/serve split: no shared runtime code between pipeline and dashboard
- DuckDB connection singleton: one read-only connection shared across all callbacks
- Pure figure functions: testable without running Dash, reusable across pages
- Parametrized SQL only: no string-concatenated queries, no SQL in callbacks
- Polars lazy evaluation: stream multi-GB data without materializing in memory

### Critical Pitfalls

1. **HS code revision breaks time series** — HS codes change every ~5 years (15-20% of codes per revision). Must apply concordance tables to map all years to a single consistent revision before computing any metrics. Address in pipeline ingestion phase
2. **Re-exports inflate supplier concentration** — Netherlands, Singapore, Hong Kong appear as major exporters of products they merely transship. Document as known limitation; flag hub countries in UI. Do not attempt algorithmic correction
3. **HHI scale confusion (0-1 vs 0-10,000)** — Pick one scale (recommend 0-1), define thresholds as named constants, unit test with known inputs. A single mixed-scale bug invalidates all scoring
4. **Callback chains freeze the dashboard** — Multiple linked views (dropdown → table → chart → map) cascade 4-5 sequential server round-trips. Pre-compute aggressively; target <50ms per callback; use clientside callbacks for formatting
5. **Product essentiality devolves into guesswork** — No universal essentiality standard exists for 5,000 HS6 products. Start with defensible categories (EU CRM list, energy, food, pharma, semiconductors) in an editable YAML file, not hardcoded. Display methodology transparently

## Implications for Roadmap

Based on combined research, the dependency graph and architectural boundaries suggest 7 phases:

### Phase 1: Project Foundation & Data Ingestion
**Rationale:** Everything depends on having the project structure right (avoids Pitfall #10, #18) and BACI data accessible. The pipeline/serve boundary must be established from day one
**Delivers:** pyproject.toml, directory layout, BACI download script, CSV→Polars ingestion with HS code concordance, country code canonical mapping
**Addresses:** T1 setup (country reference data), Pitfall #1 (HS concordance), Pitfall #14 (country code mapping)
**Avoids:** Pitfall #10 (pipeline-dashboard coupling), Pitfall #11 (memory exhaustion — establishes year-by-year Polars lazy processing)

### Phase 2: Scoring Pipeline (HHI + Geo-Risk + Essentiality + Composite)
**Rationale:** The scoring pipeline is the critical path — no visualization works without it (D1 is the dependency root for all views). All three sub-scores must be computed before the composite
**Delivers:** HHI per (importer, product, year), geopolitical risk per (country, year), product essentiality classification, composite dependency score, all stored as Parquet + loaded into DuckDB
**Addresses:** D1 (composite scoring), D2 (geo-risk layer), D6 (essentiality)
**Avoids:** Pitfall #3 (HHI scale — unit test here), Pitfall #4 (wrong aggregation level), Pitfall #5 (stale geo scores), Pitfall #6 (subjective essentiality), Pitfall #12 (missing values), Pitfall #13 (unjustified weights)

### Phase 3: Data Access Layer & Dashboard Shell
**Rationale:** With DuckDB populated, build the query interface and app skeleton before any views. Establishes the patterns all pages will use
**Delivers:** DuckDB singleton connection, parametrized query functions, Dash app with navbar/sidebar shell, home page with overview stats, methodology page
**Addresses:** T8 (methodology), T10 (data freshness), T12 (loading states)
**Avoids:** Pitfall #7 (callback architecture established early), Pitfall #15 (no global DataFrame variables)

### Phase 4: Country→Products View (Primary Analytical View)
**Rationale:** This is the primary user entry point and showcases the core value proposition. Depends on Phase 3's query layer and establishes all reusable components
**Delivers:** Country selector with search, ranked product vulnerability table (AG Grid), choropleth supplier map, composite score card with sub-score display, supplier breakdown drill-down
**Addresses:** T1 (country selector), T3 (vulnerability table), T6 (choropleth map), T7 (score display), T9 (supplier breakdown), D7 (score decomposition radar)
**Avoids:** Pitfall #8 (top-N filtering for supplier views), Pitfall #9 (choropleth paired with table), Pitfall #17 (loading/empty states)

### Phase 5: Product→Countries View & Cross-Linking
**Rationale:** Completes the dual-entry differentiator (D5). Reuses components from Phase 4 — primarily new page layout + product selector + cross-linking logic
**Delivers:** Product selector with HS hierarchy browsing, ranked country exposure table, product-centric choropleth, cross-links between both views
**Addresses:** T2 (product selector), T4 (country exposure table), D5 (dual entry points)

### Phase 6: Advanced Visualizations (Sankey, Time Series, Animation)
**Rationale:** High-impact visual features that build on the core views. Sankey is the portfolio showpiece. Time series adds temporal depth. These require working views to integrate into
**Delivers:** Sankey flow diagrams with risk-colored links, time series charts with year slider, year-over-year trend indicators
**Addresses:** D3 (Sankey), T5 (time series), D9 (animated evolution — basic slider), D10 (what changed — basic highlighting)
**Avoids:** Pitfall #8 (top-N + "Other" for Sankey), Pitfall #16 (rolling average option for time series)

### Phase 7: Polish, Testing & Deployment
**Rationale:** Final quality pass — visual polish, comprehensive tests, deployment configuration. Must come last because it validates everything
**Delivers:** Custom CSS theme, pytest suite (pipeline validation + figure tests), Dockerfile, gunicorn config, README, performance optimization pass
**Addresses:** T11 (CSV export), T12 (sub-second performance), deployment readiness

### Phase Ordering Rationale

- **Phases 1→2→3 are strictly sequential** — each needs prior output (data → scores → queries → app shell)
- **Phases 4 and 5 could partially overlap** but Phase 4 establishes reusable components that Phase 5 needs, so sequential is cleaner
- **Phase 6 depends on Phases 4-5** for integration points (Sankey embedded in country view, time series in both views)
- **Phase 7 is a cross-cutting quality pass** that validates all prior work
- This ordering follows the critical path identified in FEATURES.md: D1 (scoring) → T3/T4 (core tables) → T5/T6 (charts/maps) → D3/D4 (advanced viz)
- Architecture research confirms pipeline→storage→shell→views as the natural build order

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** HS concordance table mechanics — many-to-many mappings require a clear aggregation strategy. CEPII documentation was returning 500 errors during research
- **Phase 2:** Geopolitical risk index selection — Freedom House vs. V-Dem vs. WGI trade-offs need resolution. Sanctions list curation methodology needs definition
- **Phase 6:** Sankey diagram UX — top-N threshold tuning, "Other" bucket behavior, and risk-color mapping need prototyping

Phases with standard patterns (skip research-phase):
- **Phase 3:** Dash 4.0 Pages + DuckDB singleton is well-documented with established patterns
- **Phase 4 & 5:** Standard Dash callback + AG Grid + Plotly choropleth — extensive docs and examples available
- **Phase 7:** Standard deployment patterns (Docker + gunicorn)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified on PyPI 2026-03-17. Dash 4.0, Plotly 6.6, DuckDB 1.5, Polars 1.36 confirmed current. Compatibility matrix validated |
| Features | HIGH | Comprehensive competitive landscape analysis. Gap (no combined HHI+risk+essentiality tool) verified across 6 existing platforms |
| Architecture | HIGH | Pipeline/serve split, DuckDB singleton, Dash Pages — all well-documented patterns with official examples. Data volume estimates grounded in BACI specifications |
| Pitfalls | HIGH (data/methodology), MEDIUM (visualization) | Data pitfalls (HS concordance, re-exports, HHI scale) verified against World Bank and academic sources. Visualization pitfalls (Sankey readability, choropleth bias) based on community consensus |

**Overall confidence:** HIGH

### Gaps to Address

- **CEPII BACI download mechanics:** CEPII site returned 500 errors during research. Authentication flow, file naming conventions, and download URLs need verification during Phase 1 implementation
- **HS concordance table source and format:** WITS provides concordance tables but exact format and completeness for HS 1996→2022 mapping needs validation during Phase 1
- **Governance index coverage gaps:** Taiwan, Kosovo, Palestine have inconsistent coverage across Freedom House/V-Dem/WGI. Country mapping edge cases need explicit decisions during Phase 2
- **Essentiality classification granularity:** EU CRM list covers ~34 materials, not HS6 codes. The CRM→HS6 mapping needs manual curation during Phase 2
- **dash-cytoscape maturity:** Last release Jul 2024 (v1.0.2). API is stable but not rapidly evolving. If issues emerge during Phase 6+, fallback is Plotly's native network trace type

## Sources

### Primary (HIGH confidence)
- PyPI package index — all version numbers and compatibility verified 2026-03-17
- Dash 4.0 official docs (dash.plotly.com) — Pages, callbacks, performance, sharing data between callbacks
- DuckDB Python docs (duckdb.org) — connection management, parametrized queries, Parquet integration
- Polars user guide (docs.pola.rs) — lazy evaluation, scan_csv, sink_parquet
- WITS/World Bank — product concordance tables, trade indicators methodology, HHI definitions
- Freedom House — Freedom in the World annual dataset
- V-Dem — Dataset v16, March 2026
- EU Commission — Critical Raw Materials 2023 list

### Secondary (MEDIUM confidence)
- CEPII BACI methodology — site returning 500 errors at time of research; characteristics from working papers and known specifications
- dash-cytoscape — last release Jul 2024; API stable but development pace uncertain
- Plotly Sankey diagram docs — rendering performance with many nodes not well-documented

### Tertiary (LOW confidence)
- Re-export correction methodologies — open research problem; no consensus approach exists

---
*Research completed: 2026-03-17*
*Ready for roadmap: yes*
