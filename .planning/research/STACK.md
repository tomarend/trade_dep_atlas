# Stack Research

**Domain:** Trade dependency analytics dashboard
**Researched:** 2026-03-17
**Confidence:** HIGH

All versions verified against PyPI on 2026-03-17.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | ≥3.12 | Runtime | 3.12 has significant performance improvements and is the stable target for all listed packages. 3.13 is available but 3.12 maximizes compatibility. |
| Dash | 4.0.0 | Dashboard framework | Project requirement. v4.0 (Feb 2026) adds Pages for multi-view routing, background callbacks, improved pattern-matching callbacks — all critical for country/product/time views. |
| Plotly | 6.6.0 | Charting library | v6 (Mar 2026) is current. Native support for choropleth maps, Sankey diagrams, animated scatter/line, treemaps. Tight Dash integration. |
| DuckDB | 1.5.0 | Analytical storage | In-process columnar database. Queries pre-computed metrics 10-100× faster than SQLite for analytical GROUP BY/filter workloads. Direct Parquet/CSV ingestion. Zero-config deployment — just a file. |
| Polars | 1.36.1 | Data pipeline (ETL) | Rust-based DataFrame library. 5-10× faster than pandas for the multi-GB CSV reads, groupbys, and joins in the pipeline. Lazy evaluation keeps memory bounded. |
| PyArrow | 23.0.1 | Parquet I/O + interchange | Industry-standard columnar format. Bridge between Polars, DuckDB, and pandas. Parquet files are 5-10× smaller than CSV with column-level compression. |

### Dashboard Components

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| dash-bootstrap-components | 2.0.4 | Layout & theming | Bootstrap 5 grid system for responsive multi-panel layouts. Professional themes (Darkly, Flatly) out of the box. Far better than raw html.Div positioning. |
| dash-cytoscape | 1.0.2 | Network/flow graphs | Official Plotly wrapper for Cytoscape.js. Purpose-built for interactive network visualization in Dash. Supports force-directed layouts, styling, zoom/pan, node selection callbacks. Use for trade concentration network diagrams. |
| dash-ag-grid | 33.3.3 | Data tables | Replaces deprecated dash-table. AG Grid Community (free) provides sorting, filtering, pagination, conditional formatting, column pinning. Ideal for ranked product/country tables. |
| kaleido | 1.2.0 | Static image export | Export Plotly figures to PNG/SVG/PDF for portfolio screenshots. v1.0+ requires Chrome (auto-installable). Used by `fig.write_image()`. |
| plotly-geo | 1.0.0 | Geographic shapes | Extended geo support for choropleth maps — county/region boundaries. Small add-on package. |

### Data Processing & Analytics

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | 3.0.1 | DataFrame interop | Dash/Plotly callbacks expect pandas DataFrames. Use as the *serving* layer, not the *pipeline* layer. v3.0 uses PyArrow backend by default — faster than legacy pandas. |
| numpy | 2.4.3 | Numerical computation | HHI calculation (sum of squared shares), score normalization, weighted composites. No reason to avoid — it's a transitive dependency anyway. |
| scipy | 1.17.1 | Statistical functions | Min-max scaling, percentile calculations for score normalization. Only if needed — numpy covers most cases. |
| networkx | 3.6.1 | Graph analytics | Compute network metrics (centrality, clustering) for trade flow graphs if needed. Feed results into dash-cytoscape for visualization. |

### Data Acquisition & Reference

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | 2.32.5 | HTTP client | BACI download from CEPII (authenticated). Simple, reliable, well-understood. |
| pycountry | 26.2.16 | Country code mapping | ISO 3166 country codes, names, alpha-2/alpha-3 lookups. BACI uses numeric codes — pycountry maps them to human-readable names. |
| tqdm | 4.67.3 | Progress bars | Pipeline processing feedback for multi-year BACI ingestion. Cheap dependency, high UX value during long ETL runs. |
| loguru | 0.7.3 | Logging | Structured logging for pipeline stages. Simpler API than stdlib logging. One-liner setup. |

### Deployment

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| gunicorn | 25.1.0 | WSGI server | Production server for Dash (which is Flask underneath). Multi-worker process model handles concurrent dashboard users. Use with `--workers 4 --timeout 120`. |
| Docker | latest | Containerization | Optional but recommended for hosting on Render/Railway. Single `Dockerfile` bundles Python + DuckDB data file. |

### Development Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| uv | 0.10.11 | Package management | 10-100× faster than pip. Handles venv creation, dependency resolution, lockfiles. Use `uv init`, `uv add`, `uv sync`. The standard Python package manager in 2026. |
| ruff | 0.15.6 | Linting + formatting | Replaces both flake8 and black. Rust-based, near-instant. Single tool for linting and formatting. |
| pytest | 9.0.2 | Testing | Pipeline validation tests, metric sanity checks. Standard choice. |

## Architecture: How These Fit Together

```
BACI CSVs (multi-GB)
    │
    ▼
┌─────────────────────┐
│  Polars Pipeline     │  ← Lazy scan_csv, groupby, join
│  (ETL + metrics)     │  ← HHI, geo-risk, essentiality
└─────────┬───────────┘
          │ write Parquet
          ▼
┌─────────────────────┐
│  DuckDB             │  ← Load Parquet into tables
│  (analytics store)  │  ← Pre-aggregated metrics
└─────────┬───────────┘
          │ SQL queries
          ▼
┌─────────────────────┐
│  Dash Callbacks      │  ← duckdb.sql() → pandas DataFrame
│  (pandas serving)    │  ← Plotly figures from DataFrames
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Plotly / Cytoscape  │  ← Maps, Sankey, networks, charts
│  + AG Grid tables    │
└─────────────────────┘
```

**Key insight:** Polars does the heavy lifting (pipeline), DuckDB stores/queries pre-computed results, pandas is only the thin serving layer between DuckDB and Plotly. This keeps each tool in its strength zone.

## Installation

```bash
# Initialize project with uv
uv init dashboard_trade_crit_dep
cd dashboard_trade_crit_dep

# Core dashboard
uv add dash plotly dash-bootstrap-components dash-cytoscape dash-ag-grid plotly-geo

# Data pipeline
uv add polars pyarrow duckdb

# Serving layer (Dash needs pandas)
uv add pandas numpy

# Data acquisition & utilities
uv add requests pycountry tqdm loguru

# Static export (optional, for portfolio screenshots)
uv add kaleido

# Deployment
uv add gunicorn

# Dev tools
uv add --dev ruff pytest
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **Polars** (pipeline) | pandas 3.0 | If team is pandas-fluent and data fits in memory comfortably. pandas 3.0 with PyArrow backend is much better than legacy pandas but still slower than Polars for multi-GB aggregations. |
| **DuckDB** (storage) | SQLite | Never for this project. SQLite is row-oriented — disastrous for analytical GROUP BY queries over millions of rows. |
| **DuckDB** (storage) | PostgreSQL | Only if multi-user concurrent writes are needed. Massive overkill for a single-user dashboard with pre-computed read-only data. Adds deployment complexity. |
| **DuckDB** (storage) | Raw Parquet files | Viable if queries are simple full-scan. DuckDB wins when you need filtered subsets (one country, one product) — it has indexes and pushdown predicates. |
| **Dash** (framework) | Streamlit | Never for this project. Streamlit re-runs entire script on interaction, no fine-grained callbacks, limited layout control, no native Cytoscape/AG Grid support. |
| **Dash** (framework) | Panel/HoloViews | If the team prefers HoloViz ecosystem. Panel has good Bokeh integration but weaker Plotly support and smaller component ecosystem than Dash. |
| **dash-ag-grid** (tables) | dash-table | Never. dash-table is legacy/deprecated. AG Grid is faster, more feature-rich, actively maintained. |
| **dash-cytoscape** (networks) | visdcc | Never. visdcc is unmaintained. Cytoscape is official Plotly, well-documented, actively maintained. |
| **Polars** (pipeline) | Dask | If data exceeds single-machine RAM (>64GB). BACI at ~5-10GB fits comfortably in Polars lazy mode. Dask adds distributed complexity for no benefit here. |
| **uv** (packages) | pip + venv | If uv is unavailable. pip works but is 10-100× slower for resolution and has no lockfile. |
| **gunicorn** (server) | waitress | If deploying on Windows. Gunicorn is Unix-only. Waitress is cross-platform but less performant. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Streamlit** | Full script re-execution on every click. No component-level callbacks. Layout is top-to-bottom only. Cannot build complex multi-panel dashboards. | Dash 4.0 |
| **SQLite** | Row-oriented storage. Analytical queries (GROUP BY country, product aggregations) are 10-50× slower than DuckDB on this data shape. | DuckDB |
| **dash-table** | Legacy component, deprecated in favor of AG Grid. Slow with >1000 rows, limited styling, no column pinning. | dash-ag-grid |
| **Raw pandas for pipeline** | Loading 5+ GB CSVs into pandas eats 15-20GB RAM due to memory copies. No lazy evaluation = entire dataset must fit in memory at once. | Polars (lazy mode) |
| **Flask directly** | Dash *is* Flask underneath. Writing raw Flask + Jinja templates + custom JS for what Dash provides declaratively is massive wasted effort. | Dash |
| **MongoDB / Redis** | Document store and cache — neither suits analytical aggregation queries. Adds deployment dependencies for no benefit. | DuckDB (single file) |
| **Bokeh / Altair** | Neither has native Sankey diagrams, and their Dash integration is poor. Plotly covers all needed chart types natively. | Plotly |
| **pip** (for package management) | No lockfile, slow dependency resolution, no integrated venv management. | uv |
| **Jupyter notebooks** (for pipeline) | Fine for exploration, but production pipelines need reproducible CLI scripts with proper logging and error handling. | Python scripts + loguru |

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Dash 4.0 | Plotly ≥6.0 | Dash 4.0 requires Plotly 6.x. Do not pin Plotly <6. |
| Dash 4.0 | Flask 3.x | Dash bundles Flask internally. No separate Flask install needed. |
| Plotly 6.6 | kaleido ≥1.0 | Plotly 6 requires kaleido v1+ for `write_image()`. kaleido v0.x is incompatible. |
| Plotly 6.6 | pandas ≥2.0 | Plotly 6 works with pandas 2.x and 3.x. pandas 3.0 recommended for PyArrow backend. |
| Polars 1.36 | PyArrow ≥15.0 | Polars uses PyArrow for Parquet I/O. PyArrow 23 is current and compatible. |
| DuckDB 1.5 | PyArrow ≥12.0 | DuckDB can directly scan Parquet via PyArrow. Zero-copy interchange. |
| DuckDB 1.5 | Polars ≥0.20 | DuckDB can query Polars DataFrames directly via `duckdb.sql("SELECT * FROM polars_df")`. |
| DuckDB 1.5 | pandas ≥1.5 | DuckDB returns pandas DataFrames via `.df()` method. Tight integration. |
| dash-bootstrap-components 2.0 | Dash ≥2.0 | dbc 2.0 targets Bootstrap 5. Compatible with Dash 4.0. |
| dash-cytoscape 1.0 | Dash ≥2.0 | Stable on Dash 4.0. Last release Jul 2024 but API is mature/stable. |
| dash-ag-grid 33.3 | Dash ≥2.7 | Official Plotly component. Compatible with Dash 4.0. |
| Python 3.12 | All above | All listed packages have 3.12 wheels. Safest target. |

## Confidence Assessment

| Area | Confidence | Source |
|------|------------|--------|
| Dash + Plotly versions | HIGH | PyPI verified 2026-03-17. Official release dates confirmed. |
| DuckDB for analytics | HIGH | PyPI verified. Well-documented analytical DB. Standard for this workload pattern (pre-computed metrics, filtered reads). |
| Polars for ETL | HIGH | PyPI verified. Established as the performant Python DataFrame library for batch processing. |
| dash-cytoscape maturity | MEDIUM | Last release Jul 2024 (1.0.2). Not abandoned — API is stable and feature-complete — but not rapidly evolving. If issues arise, fallback is Plotly's native network trace type (less interactive). |
| dash-ag-grid free tier | HIGH | AG Grid Community features (sort, filter, paginate, style) are sufficient. Enterprise features (grouping, pivoting) not needed. |
| DuckDB + Polars interop | HIGH | DuckDB can query Polars DataFrames and Parquet files natively. Well-tested path. |
| gunicorn for deployment | HIGH | Standard WSGI server for Flask/Dash apps. v25 is current. |
| uv for package management | HIGH | De facto standard Python package manager as of 2025. Astral-backed, extremely active development. |

## Data Volume Estimates

Understanding the scale drives stack choices:

| Metric | Estimate | Implication |
|--------|----------|-------------|
| Raw BACI rows | ~100-200M (all years) | Too large for pandas in-memory. Polars lazy scan essential. |
| Raw BACI disk | ~5-10 GB (CSV) | Fits single machine. No distributed computing needed. |
| Pre-computed metrics | ~200 countries × 5,000 products × 20 years = 20M rows | DuckDB handles this trivially. Dashboard queries return in <100ms. |
| Pre-computed Parquet | ~500MB-1GB compressed | Deployable alongside app. No external database server. |
| Dashboard query result | ~5,000 rows per callback (one country's products) | pandas can serve this instantly. No performance concern. |

## Sources

- Dash 4.0.0: https://pypi.org/project/dash/ (Released Feb 3, 2026)
- Plotly 6.6.0: https://pypi.org/project/plotly/ (Released Mar 2, 2026)
- DuckDB 1.5.0: https://pypi.org/project/duckdb/ (Released Mar 9, 2026)
- Polars 1.36.1: PyPI JSON API (verified 2026-03-17)
- PyArrow 23.0.1: https://pypi.org/project/pyarrow/ (Released Feb 16, 2026)
- dash-bootstrap-components 2.0.4: https://pypi.org/project/dash-bootstrap-components/ (Released Aug 20, 2025)
- dash-cytoscape 1.0.2: https://pypi.org/project/dash-cytoscape/ (Released Jul 15, 2024)
- dash-ag-grid 33.3.3: https://pypi.org/project/dash-ag-grid/ (Released Jan 21, 2026)
- kaleido 1.2.0: https://pypi.org/project/kaleido/ (Released Nov 4, 2025)
- pycountry 26.2.16: https://pypi.org/project/pycountry/ (Released Feb 17, 2026)
- gunicorn 25.1.0: https://pypi.org/project/gunicorn/ (Released Feb 13, 2026)
- All supporting library versions verified via PyPI JSON API on 2026-03-17
