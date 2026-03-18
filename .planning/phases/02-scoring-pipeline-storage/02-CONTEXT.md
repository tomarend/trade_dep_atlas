# Phase 2: Scoring Pipeline & Storage - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Compute HHI concentration, geopolitical risk scores, product essentiality tiers, and a composite dependency score for every (importer, product, year) tuple. Store all pre-computed metrics in DuckDB for fast dashboard serving. Requirements: SCOR-01, SCOR-02, SCOR-03, SCOR-04, DATA-05.

</domain>

<decisions>
## Implementation Decisions

### HHI Concentration
- Per (importer, product, year) tuple: HHI = Σ(supplier_share²) on 0–1 scale (academic convention)
- Supplier share = exporter's value / total import value for that product-importer-year
- Computed in Polars from Phase 1 Parquet output
- Store both HHI and individual supplier shares (needed for drill-down and Sankey in later phases)

### Geopolitical Risk Data Sources
- **Primary governance index:** World Bank Worldwide Governance Indicators (WGI) — 6 dimensions, 200+ countries, 1996–present
- **Fallback for gaps:** Freedom House scores (Taiwan, Kosovo, Palestine, and any other territories missing from WGI)
- **Sanctions data:** Global Sanctions Data Base (GSDB) from Drexel/Stanford — bilateral country-level sanctions episodes with temporal data
- **Combination formula:** geo_risk = governance_risk × (1 + sanctions_intensity) — sanctions act as a multiplier on governance risk
- **Time-varying:** Geo-risk scores computed per year, matching WGI year to trade data year. Captures regime changes and new sanctions episodes (e.g., Russia before/after 2014/2022)
- **Score range:** 0–1 (inverted from WGI — higher = riskier)

### Product Essentiality Classification
- **Three-tier structure with within-tier gradient:**
  - **Critical (0.85–1.0):** EU CRM list materials, USGS critical minerals, energy commodities (crude oil, natural gas, LNG), fertilizers (potash, phosphates, nitrogen), pharmaceutical APIs/bulk inputs, semiconductor materials
  - **Important (0.45–0.7):** Food staples (HS 01–24), finished pharmaceutical products, industrial chemicals (non-CRM)
  - **Standard (0.1–0.3):** Everything else — consumer goods, manufactured articles, etc.
- **Within-tier gradient:** Global export HHI (how concentrated are worldwide exporters of this product) determines where a product falls within its tier range. More concentrated global supply → higher score within tier
- **Authoritative sources:** EU CRM 2023 list + USGS Critical Minerals List 2022 + sector categorization rules
- **Highest tier wins:** If a product qualifies for multiple categories, it gets the highest applicable tier
- **Configuration format:** YAML config defining sector→tier+score_range mapping, plus a companion CSV mapping individual HS6 codes to categories. Both in `data/reference/`
- **CRM→HS6 mapping:** Curated static mapping file built from EU CRM + USGS lists, stored in `data/reference/`
- **Static scores:** Essentiality doesn't change over time (today's strategic assessment applied to all years)
- **Metadata:** Include `crm_listed_since` field showing when each material first appeared on a CRM list

### Composite Dependency Score
- **Formula:** Weighted linear sum: composite = w₁×HHI + w₂×geo_risk + w₃×essentiality
- **No normalization needed:** All three sub-scores already on 0–1 scale with sufficient range spread
- **Default weights:** Claude's discretion — optimize for producing meaningful rankings that surface dangerous dependencies
- **User-adjustable:** Weight controls added in Phase 4 (SCOR-05), not in this phase
- **Output range:** 0–1

### DuckDB Storage
- **Pipeline flow:** Polars computes metrics → writes Parquet intermediates → final step loads all Parquet into DuckDB tables
- **Parquet intermediates:** Serve as backup, inspection artifacts, and testable pipeline stage outputs
- **DuckDB file:** Single file at `data/dashboard.duckdb`
- **Schema:** Star schema with:
  - **Fact table:** All sub-scores and composite per (importer, product, year, exporter) — full supplier-level detail including individual shares, values, and per-supplier geo-risk
  - **Country dimension table:** ISO3, name, region, continent, reexport_hub flag, geo-risk scores per year
  - **Product dimension table:** HS6 code, description, HS2/HS4 hierarchy, category, essentiality tier, essentiality score, global export HHI, crm_listed_since
- **Query target:** <50ms for typical dashboard queries (country→products ranked, product→countries ranked)

### Claude's Discretion
- Default composite weight balance (w₁, w₂, w₃) — optimize for surfacing dangerous dependencies
- DuckDB indexing strategy for query performance
- Parquet partitioning scheme for intermediate scoring outputs
- Pipeline stage ordering and error handling between scoring steps

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data & Architecture
- `.planning/research/ARCHITECTURE.md` — Pipeline module structure (hhi.py, georisk.py, essentiality.py, composite.py, export.py)
- `.planning/research/STACK.md` — Polars 1.36 for ETL, DuckDB 1.5 for storage
- `.planning/research/PITFALLS.md` — HHI scale (#3), HHI aggregation level (#4), governance gaps (#5), essentiality classification (#6)

### Phase 1 Context
- `.planning/phases/01-data-pipeline-ingestion/01-CONTEXT.md` — Pipeline output format (Parquet, hive-partitioned by year), country mapping decisions, concordance approach

### Project Context
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — SCOR-01 through SCOR-04, DATA-05 (this phase's requirements)

### External Data Sources (to be ingested)
- WGI data: World Bank Worldwide Governance Indicators dataset
- Freedom House: Freedom in the World annual scores
- GSDB: Global Sanctions Data Base (Drexel/Stanford) — bilateral sanctions episodes
- EU CRM 2023 list: Critical Raw Materials Act
- USGS Critical Minerals List 2022

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/countries.py` — `CountryRecord` dataclass with ISO3, region, continent, reexport_hub flag. `load_country_mapping()` returns `dict[int, CountryRecord]`. Geo-risk scores can extend this record or build a parallel lookup.
- `pipeline/concordance.py` — `Concordance` dataclass with forward/reverse maps, descriptions. HS6→category mapping already exists in `load_product_descriptions()` returning `dict[str, tuple[str, str]]`. Essentiality can extend the category system.
- `pipeline/ingest.py` — `ingest_baci_year()` returns Polars DataFrame with columns: year, exporter_baci, importer_baci, hs6_original, value_usd, quantity_kg, exporter_iso3, importer_iso3, concorded_hs6, hs2, hs4, product_description, category, concordance_flag, unit_value, outlier_flag. HHI computation reads from this output.
- `pipeline/__main__.py` — CLI orchestrator with stage-based architecture (download → validate → ingest). Phase 2 adds scoring stages after ingestion.
- `pipeline.yaml` — Configuration file for paths and settings. Phase 2 adds scoring config section.
- `data/reference/country_overrides.yaml` — Manual country overrides with region_map and reexport_hubs. Can be extended with governance data paths.
- `data/reference/hs_product_descriptions.csv` — HS6→(description, category) mapping. Essentiality classification builds on existing categories.

### Established Patterns
- Polars lazy evaluation for large datasets (scan_csv → lazy transforms → collect)
- Reference data loaded from `data/reference/` directory
- YAML config for pipeline settings
- Loguru for logging with progress reporting
- JSON manifest for pipeline run metadata
- Incremental processing (skip already-processed years)

### Integration Points
- **Input:** Reads Parquet from `data/processed/year=YYYY/data.parquet` (Phase 1 output)
- **Output:** Writes `data/dashboard.duckdb` (consumed by Phase 3 dashboard)
- **New pipeline modules:** `pipeline/hhi.py`, `pipeline/georisk.py`, `pipeline/essentiality.py`, `pipeline/composite.py`, `pipeline/export.py`
- **New reference data:** Essentiality config YAML + HS6→category CSV, CRM→HS6 mapping, governance data files, sanctions data file
- **Updated:** `pipeline/__main__.py` gains scoring stages, `pipeline.yaml` gains scoring config

</code_context>

<specifics>
## Specific Ideas

- Sanctions as multiplier (not additive) — a well-governed but sanctioned country (e.g., Russia pre-2014 had decent WGI) still gets elevated risk via the multiplier
- Global export HHI as within-tier gradient for essentiality — this is computable from the same BACI data, so no external data source needed for this dimension
- Energy commodities (crude oil, natural gas, LNG), fertilizers, and pharma APIs elevated to critical tier alongside traditional CRM materials — justified by substitutability rather than just CRM list membership
- `crm_listed_since` metadata field for temporal context on when materials were recognized as critical
- Star schema with full supplier-level detail in the fact table — enables both aggregated rankings and drill-down supplier analysis from the same DuckDB query layer

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-scoring-pipeline-storage*
*Context gathered: 2026-03-18*
