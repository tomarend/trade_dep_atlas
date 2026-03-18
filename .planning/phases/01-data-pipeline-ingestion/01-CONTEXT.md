# Phase 1: Data Pipeline & Ingestion - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Download BACI bilateral trade data from CEPII, apply HS code revision concordance to create consistent product codes across all years, normalize country identifiers to ISO3, and output cleaned Parquet files ready for scoring in Phase 2. Requirements: DATA-01, DATA-02, DATA-03, DATA-04.

</domain>

<decisions>
## Implementation Decisions

### BACI Download Strategy
- No login required — BACI has public download links (https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html#download-links)
- Download all available years in one go (full dataset)
- ZIP download + automatic extraction
- Verify file integrity + skip already-downloaded files (resumable)
- Keep raw files in separate `data/raw/` directory
- Retry failed downloads 2-3 times, then skip and continue with remaining years
- Report progress to stdout (print which year is downloading, progress indicators)

### HS Concordance Approach
- Map all HS6 codes to the latest HS 2022 revision
- Use WITS concordance tables, bundled as static files in the repo
- When many-to-many mappings occur, aggregate up (sum trade values of linked codes)
- Process all available BACI years including those using older HS revisions (HS96+)
- Flag products where concordance was applied (split/merge) in a metadata column
- Store HS2, HS4, HS6 hierarchy as separate columns for dashboard browsing
- Include human-readable HS6 product descriptions alongside codes
- Validate concordance with both trade value conservation checks and spot-checks on known products (lithium, rare earths, etc.)

### Country Code Mapping
- Use BACI's own country_codes mapping file as the base, enriched with manual overrides
- Pipeline-generated artifact + manual overrides file for edge cases
- Include non-standard territories with custom ISO-like codes (TWN for Taiwan, XKX for Kosovo, etc.)
- Map historical entities to successors (Czechoslovakia → CZE + SVK, Yugoslavia → component states, etc.)
- Canonical English name + common aliases stored for dashboard search
- Include region/continent groupings per country for dashboard filtering
- ISO3 sufficient for Plotly maps — no need for lat/lon coordinates
- Flag known re-export hubs (NL, SG, HK, AE, BE) in country metadata

### Pipeline Output Format
- Parquet format for processed trade data
- Hive-partitioned by year (data/processed/year=2020/)
- Directory structure: `data/raw/`, `data/processed/`, `data/reference/` (concordance tables, country mapping)
- Keep all BACI columns (year, exporter, importer, HS6, value, quantity) + enriched columns (concorded_hs6, iso3_exporter, iso3_importer, hs2, hs4, product_description, concordance_flag)
- Incremental processing: skip years where raw data hasn't changed and processed output exists
- Write pipeline manifest JSON (run timestamp, BACI version, years processed, row counts)
- Pipeline settings via YAML config file (pipeline.yaml) for paths, year range, concordance settings
- `data/` directory in .gitignore — only code and reference tables tracked in git

### Data Quality & Cleaning
- Drop null trade values, keep explicit zeros (zero trade is meaningful)
- Trust BACI reconciliation — no deduplication step needed
- Flag extreme outliers (>3σ from product-level mean) but do not remove them
- No minimum trade value threshold — keep all flows regardless of size

### Testing Strategy
- Synthetic test fixtures (5 countries, 10 products, 3 years) for unit tests
- Real BACI data slice (1 year, all products) for integration tests
- Both unit tests (concordance logic, country mapping, cleaning) and integration tests (full pipeline: raw CSV → processed Parquet)
- pytest as test framework
- GitHub Actions CI running pytest on push

### Value & Quantity Data
- Keep both trade value (USD) and quantity (kg) from BACI
- Compute unit values ($/kg) as a derived column — useful for anomaly detection and re-export flagging

### Claude's Discretion
- Pipeline invocation method (CLI script, Makefile, or task runner)
- Aggregation strategy for concordance split logic (sum vs weighted)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Source
- `.planning/research/STACK.md` — Polars 1.36 for ETL, DuckDB 1.5 for storage, uv for packaging
- `.planning/research/PITFALLS.md` — HS concordance breaks (#1), re-exports (#2), HHI scale (#3), country mapping (#5)
- `.planning/research/ARCHITECTURE.md` — Pipeline/serve boundary, Polars lazy evaluation strategy

### Project Context
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-04 (this phase's requirements)

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- None — first phase establishes patterns for the project

### Integration Points
- Phase 2 (Scoring Pipeline) will read Parquet output from `data/processed/`
- Phase 2 will read country metadata from `data/reference/` for geo risk scoring
- Phase 2 will read HS product metadata for essentiality classification

</code_context>

<specifics>
## Specific Ideas

- BACI download page confirmed at https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html#download-links — no authentication needed
- WITS concordance tables to be bundled in repo under `data/reference/` or similar
- Re-export hub flagging (NL, SG, HK, AE, BE) is a metadata annotation, not a data correction — the re-export problem is documented as a known limitation
- Unit values ($/kg) serve dual purpose: anomaly detection in pipeline and potential re-export indicator for dashboard

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-data-pipeline-ingestion*
*Context gathered: 2026-03-17*
