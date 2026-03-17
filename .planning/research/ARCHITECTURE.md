# Architecture Research

**Domain:** Trade dependency analytics dashboard
**Researched:** 2026-03-17
**Confidence:** HIGH

## System Overview

```
                        ┌─────────────────────────────────────────┐
                        │           DATA ACQUISITION              │
                        │  BACI CSVs (multi-GB, ~20 year files)   │
                        │  + Governance indices + Sanctions lists  │
                        │  + Product essentiality classifications  │
                        └──────────────────┬──────────────────────┘
                                           │
                                           ▼
                        ┌─────────────────────────────────────────┐
                        │           DATA PIPELINE                 │
                        │  Polars (lazy mode) — ETL + metrics     │
                        │                                         │
                        │  ┌─────────┐ ┌─────────┐ ┌───────────┐ │
                        │  │  HHI    │ │Geo-Risk │ │Essentiality│ │
                        │  │  calc   │ │ scoring │ │ scoring    │ │
                        │  └────┬────┘ └────┬────┘ └─────┬─────┘ │
                        │       └───────────┼────────────┘        │
                        │                   ▼                     │
                        │          Composite Score                │
                        └──────────────────┬──────────────────────┘
                                           │ write Parquet
                                           ▼
                        ┌─────────────────────────────────────────┐
                        │           STORAGE LAYER                 │
                        │  DuckDB database file (.duckdb)         │
                        │  Loaded from Parquet files               │
                        │                                         │
                        │  Tables:                                │
                        │   • dependency_scores (main fact table) │
                        │   • countries (dimension)               │
                        │   • products (dimension, HS hierarchy)  │
                        │   • suppliers (bilateral breakdowns)    │
                        │   • time_series_cache (pre-aggregated)  │
                        └──────────────────┬──────────────────────┘
                                           │ SQL queries → pandas
                                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        DASH APPLICATION                                  │
│                                                                          │
│  ┌──────────────┐   ┌───────────────────────────────────────────────┐   │
│  │   app.py     │   │             pages/                            │   │
│  │   (entry     │   │  ┌──────────┐ ┌───────────┐ ┌────────────┐   │   │
│  │    point)    │──▶│  │  home    │ │ country   │ │  product   │   │   │
│  │              │   │  │          │ │ _products │ │ _countries │   │   │
│  │   Shell:     │   │  └──────────┘ └───────────┘ └────────────┘   │   │
│  │   navbar +   │   │  ┌──────────┐ ┌───────────┐                  │   │
│  │   sidebar +  │   │  │  method  │ │   not_    │                  │   │
│  │   page_      │   │  │ _ology  │ │  found_   │                  │   │
│  │   container  │   │  │          │ │   404     │                  │   │
│  │              │   │  └──────────┘ └───────────┘                  │   │
│  └──────────────┘   └───────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────┐  ┌────────────────────────┐   │
│  │         data/ (data access layer)    │  │  components/           │   │
│  │  db.py — DuckDB connection singleton │  │  navbar.py             │   │
│  │  queries.py — parametrized SQL       │  │  sidebar.py            │   │
│  │  cache.py — callback result cache    │  │  score_card.py         │   │
│  └──────────────────────────────────────┘  │  map_figure.py         │   │
│                                            │  sankey_figure.py      │   │
│  ┌──────────────────────────────────────┐  │  time_series_figure.py │   │
│  │         figures/ (chart builders)    │  │  supplier_table.py     │   │
│  │  choropleth.py                       │  │  radar_figure.py       │   │
│  │  sankey.py                           │  └────────────────────────┘   │
│  │  time_series.py                      │                                │
│  │  radar.py                            │                                │
│  │  network.py (v1.x)                  │                                │
│  └──────────────────────────────────────┘                                │
└──────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Boundary Definition

The system has three hard boundaries with clean interfaces between them. Each can be developed, tested, and run independently.

| Component | Responsibility | Inputs | Outputs | Typical Implementation |
|-----------|---------------|--------|---------|----------------------|
| **Data pipeline** | Download BACI data, compute all dependency metrics, write pre-aggregated results | Raw BACI CSVs, governance indices, sanctions lists, essentiality config | Parquet files, DuckDB database | CLI scripts run via `python -m pipeline` |
| **Storage layer** | Serve pre-computed metrics via fast analytical queries | SQL queries with country/product/year filters | Pandas DataFrames (small, filtered) | DuckDB file queried in-process |
| **Dashboard app** | Present interactive visualizations, handle user navigation and filtering | User interactions (clicks, dropdowns, sliders) | Rendered HTML/JS (Plotly figures, AG Grid tables) | Dash 4.0 multi-page app |

### Sub-Component Detail

#### Pipeline Sub-Components

| Module | Responsibility | Depends On |
|--------|---------------|------------|
| `pipeline/download.py` | Authenticate with CEPII, download BACI CSVs, verify integrity | requests, CEPII credentials |
| `pipeline/ingest.py` | Parse raw BACI CSVs into standardized Polars DataFrames | polars (lazy scan_csv) |
| `pipeline/hhi.py` | Compute HHI concentration per (importer, product, year) | Ingested trade flows |
| `pipeline/georisk.py` | Score supplier countries on geopolitical risk (sanctions + governance) | Governance data (Freedom House/V-Dem/WGI), sanctions lists |
| `pipeline/essentiality.py` | Classify HS6 products by essentiality tier (critical/important/standard) | Essentiality config (YAML/JSON mapping HS codes to tiers) |
| `pipeline/composite.py` | Combine HHI + geo-risk + essentiality into composite dependency score | HHI scores, geo-risk scores, essentiality scores |
| `pipeline/export.py` | Write computed metrics to Parquet, load into DuckDB | All computed scores |
| `pipeline/__main__.py` | CLI entry point orchestrating full pipeline run | All pipeline modules |

#### Dashboard Sub-Components

| Module | Responsibility | Depends On |
|--------|---------------|------------|
| `app.py` | Dash app instance, shell layout (navbar + sidebar + page_container), server config | Dash, dbc |
| `data/db.py` | DuckDB connection singleton (open once, share across callbacks) | duckdb |
| `data/queries.py` | Parametrized SQL functions returning pandas DataFrames | db.py |
| `pages/home.py` | Landing page with overview stats and navigation | queries.py |
| `pages/country_products.py` | Country→Products view: select importer, see vulnerable products | queries.py, figures/, components/ |
| `pages/product_countries.py` | Product→Countries view: select product, see exposed importers | queries.py, figures/, components/ |
| `pages/methodology.py` | Static methodology explanation page | None (content only) |
| `figures/*.py` | Pure functions: (DataFrame) → Plotly Figure. No side effects, no callbacks | plotly |
| `components/*.py` | Reusable Dash layout fragments (cards, tables, selectors) | dash, dbc, dag |

## Recommended Project Structure

```
dashboard_trade_crit_dep/
│
├── app.py                          # Dash entry point (use_pages=True)
├── gunicorn.conf.py                # Production server config
│
├── pipeline/                       # Data pipeline (runs independently)
│   ├── __init__.py
│   ├── __main__.py                 # CLI: python -m pipeline
│   ├── download.py                 # BACI download + authentication
│   ├── ingest.py                   # CSV → Polars lazy frames
│   ├── hhi.py                      # HHI concentration calculation
│   ├── georisk.py                  # Geopolitical risk scoring
│   ├── essentiality.py             # Product essentiality classification
│   ├── composite.py                # Composite score aggregation
│   └── export.py                   # Write Parquet → Load DuckDB
│
├── data/                           # Data access layer (shared by dashboard)
│   ├── __init__.py
│   ├── db.py                       # DuckDB connection singleton
│   ├── queries.py                  # Parametrized SQL → pandas DataFrames
│   └── cache.py                    # Optional: callback-level caching
│
├── pages/                          # Dash Pages (auto-registered)
│   ├── home.py                     # Landing / overview (path="/")
│   ├── country_products.py         # Country→Products view
│   ├── product_countries.py        # Product→Countries view
│   ├── methodology.py              # Scoring methodology explanation
│   └── not_found_404.py            # Custom 404
│
├── figures/                        # Pure figure-building functions
│   ├── __init__.py
│   ├── choropleth.py               # World map figures
│   ├── sankey.py                   # Supplier flow diagrams
│   ├── time_series.py              # Line/area charts
│   ├── radar.py                    # Score decomposition spider charts
│   ├── bar.py                      # Ranked bar charts
│   └── network.py                  # Trade network graphs (v1.x)
│
├── components/                     # Reusable Dash layout fragments
│   ├── __init__.py
│   ├── navbar.py                   # Top navigation bar
│   ├── sidebar.py                  # Filter sidebar (country/product)
│   ├── score_card.py               # Composite score display card
│   ├── selector.py                 # Country/product dropdowns with search
│   ├── supplier_table.py           # AG Grid supplier breakdown
│   └── year_slider.py              # Year range / animation slider
│
├── assets/                         # Dash auto-serves this directory
│   ├── style.css                   # Custom CSS overrides
│   ├── favicon.ico
│   └── logo.png
│
├── config/                         # Static configuration
│   ├── essentiality.yaml           # HS6 → essentiality tier mapping
│   ├── sanctions.yaml              # Sanctioned country lists by year
│   └── settings.py                 # App settings (DB path, theme, etc.)
│
├── db/                             # Generated data (gitignored except schema)
│   ├── trade_deps.duckdb           # Pre-computed metrics database
│   └── parquet/                    # Intermediate Parquet files
│       ├── hhi.parquet
│       ├── georisk.parquet
│       ├── essentiality.parquet
│       └── composite.parquet
│
├── tests/                          # Test suite
│   ├── test_pipeline/
│   │   ├── test_hhi.py
│   │   ├── test_georisk.py
│   │   ├── test_composite.py
│   │   └── test_export.py
│   ├── test_data/
│   │   └── test_queries.py
│   └── test_figures/
│       └── test_choropleth.py
│
├── pyproject.toml                  # Project metadata + dependencies (uv)
├── uv.lock                         # Locked dependencies
├── Dockerfile                      # Container for deployment
├── .gitignore
└── README.md
```

### Structure Rationale

**Why `pages/` directory pattern?** Dash 4.0 Pages auto-discovers and registers pages in the `pages/` folder. Each file defines a `layout` variable/function and its callbacks via `@callback` (imported from `dash`). No manual routing needed — Dash handles URL→page mapping automatically.

**Why separate `figures/` from `pages/`?** Figure-building functions are pure: DataFrame in, Plotly Figure out. This makes them testable without a running Dash app, reusable across pages (e.g., both views use choropleth maps), and keeps page files focused on layout + callbacks rather than chart construction.

**Why separate `data/` from `pipeline/`?** The pipeline runs offline (batch ETL). The `data/` module is the dashboard's read-only interface to pre-computed results. They share no code at runtime — the pipeline writes to DuckDB, the dashboard reads from it.

**Why `components/` separate from `pages/`?** Both the Country→Products and Product→Countries views share UI elements (score cards, year sliders, supplier tables). Extracting shared components prevents duplication and ensures visual consistency.

## Data Flow

### Pipeline Flow (Offline, Batch)

```
1. DOWNLOAD
   CEPII BACI portal ──(requests + auth)──→ raw CSVs to data/raw/

2. INGEST
   raw CSVs ──(polars.scan_csv, lazy)──→ standardized LazyFrames
   • Filter columns: reporter, partner, product (HS6), value, quantity
   • Map country codes → ISO 3166 via pycountry
   • Validate: drop rows with missing keys

3. COMPUTE HHI (per importer × product × year)
   LazyFrame
   ──(groupby [importer, product, year])──→ supplier shares
   ──(share² summed)──→ HHI score [0.0 – 1.0]
   ──(write)──→ parquet/hhi.parquet

4. COMPUTE GEO-RISK (per supplier country × year)
   governance indices (Freedom House / V-Dem / WGI) + sanctions lists
   ──(normalize each index 0–1)──→ composite risk score per country-year
   ──(write)──→ parquet/georisk.parquet

5. COMPUTE ESSENTIALITY (per HS6 product, static)
   essentiality.yaml config
   ──(map HS6 → tier)──→ essentiality score [0.0 – 1.0]
   ──(write)──→ parquet/essentiality.parquet

6. COMPUTE COMPOSITE
   join(hhi, georisk, essentiality) on importer × product × year
   ──(weighted average)──→ composite dependency score
   ──(write)──→ parquet/composite.parquet

7. LOAD INTO DUCKDB
   all parquet files ──(CREATE TABLE AS SELECT * FROM)──→ trade_deps.duckdb
   • Add indexes on (importer, year) and (product, year)
   • Compute summary statistics table for home page
```

### Dashboard Flow (Online, Per-Request)

```
User action                    Callback                         Data layer
───────────                    ────────                         ──────────

Select country "DEU"  ──→  @callback in                   ──→  queries.get_vulnerable_products(
                           country_products.py                    importer="DEU", year=2022
                                                                 )
                                                           ──→  DuckDB SQL:
                                                                 SELECT product, hhi, georisk,
                                                                        essentiality, composite
                                                                 FROM dependency_scores
                                                                 WHERE importer = ? AND year = ?
                                                                 ORDER BY composite DESC
                                                           ──→  pandas DataFrame (~5,000 rows)
                      ◀──  Return:
                           • AG Grid table (ranked products)
                           • Choropleth map figure
                           • Score summary cards

Click product "8542"  ──→  @callback: drill into           ──→  queries.get_supplier_breakdown(
                           supplier detail                        importer="DEU", product="8542",
                                                                  year=2022)
                                                           ──→  DuckDB SQL:
                                                                 SELECT partner, value, share,
                                                                        georisk_score
                                                                 FROM bilateral_flows
                                                                 WHERE importer = ? AND product = ?
                                                                   AND year = ?
                      ◀──  Return:
                           • Sankey figure (suppliers → DEU)
                           • Supplier table (AG Grid)
                           • Radar chart (score decomposition)

Slide year to 2015    ──→  @callback: re-query with         ──→  queries.get_vulnerable_products(
                           new year                               importer="DEU", year=2015)
                      ◀──  Updated table + map + cards
```

### Data Volume at Each Stage

| Stage | Rows | Size | Query Time |
|-------|------|------|------------|
| Raw BACI (all years) | ~100–200M | ~5–10 GB (CSV) | N/A (pipeline only) |
| Pre-computed scores | ~20M (200 countries × 5K products × 20 years) | ~500MB–1GB (Parquet) | N/A (pipeline only) |
| DuckDB database | ~20M rows | ~300–600MB (.duckdb) | Full scan: ~1s |
| Single callback query | ~5,000 rows (one country, one year) | ~200KB | <50ms |
| Sankey drill-down | ~50–200 rows (top suppliers) | ~10KB | <10ms |

## Build Order

The dependency graph determines what must be built first. Each layer depends only on the layer above it.

```
Phase 1: Foundation
├── Project scaffolding (pyproject.toml, directory structure, config)
├── pipeline/ingest.py (BACI CSV → Polars DataFrames)
└── pipeline/download.py (BACI acquisition, can stub initially)

Phase 2: Scoring Pipeline
├── pipeline/hhi.py (Needs: ingest)
├── pipeline/georisk.py (Needs: governance data config)
├── pipeline/essentiality.py (Needs: essentiality config)
└── pipeline/composite.py (Needs: hhi + georisk + essentiality)

Phase 3: Storage + Data Access
├── pipeline/export.py (Needs: composite pipeline output)
├── data/db.py (Needs: DuckDB file from export)
└── data/queries.py (Needs: db.py + table schema)

Phase 4: Dashboard Shell
├── app.py (Dash instance, use_pages=True, bootstrap theme)
├── components/navbar.py
├── pages/home.py (landing page with overview stats)
└── pages/methodology.py (static content)

Phase 5: Core Views
├── components/selector.py (country/product dropdowns)
├── components/year_slider.py
├── figures/bar.py (ranked bar charts)
├── figures/choropleth.py (world heat map)
├── pages/country_products.py (Needs: queries + figures + components)
└── pages/product_countries.py (Needs: queries + figures + components)

Phase 6: Advanced Visualizations
├── figures/sankey.py (supplier flow diagrams)
├── figures/radar.py (score decomposition)
├── figures/time_series.py (evolution charts)
├── components/score_card.py (composite score display)
└── components/supplier_table.py (AG Grid drill-down)

Phase 7: Polish + Deployment
├── assets/style.css (visual polish)
├── Dockerfile
├── gunicorn.conf.py
└── tests/
```

**Critical path:** Phases 1→2→3 are strictly sequential (each needs prior output). Phases 4–6 can partially overlap once Phase 3 produces a working DuckDB file with sample data.

**Recommended approach for development velocity:** Build Phase 2 with a small data sample (1 year, 10 countries) first, then expand to full dataset once the pipeline is validated.

## Architectural Patterns

### 1. Pipeline/Serve Split

**Pattern:** Strict separation between data computation (pipeline) and data serving (dashboard). The pipeline runs as a batch CLI process. The dashboard is a read-only web server.

**Why:** The pipeline processes 100M+ rows with Polars — heavy computation that takes minutes. The dashboard serves pre-computed results — lightweight queries returning in <50ms. Mixing them would make the dashboard slow and fragile.

**Interface contract:** The pipeline writes to a DuckDB file with a known schema. The dashboard reads from that file. No shared Python objects cross this boundary — only the database file.

```python
# pipeline/export.py — writes
import duckdb
con = duckdb.connect("db/trade_deps.duckdb")
con.execute("CREATE OR REPLACE TABLE dependency_scores AS SELECT * FROM 'parquet/composite.parquet'")

# data/db.py — reads
import duckdb
_con = duckdb.connect("db/trade_deps.duckdb", read_only=True)
def get_connection():
    return _con
```

### 2. DuckDB Connection Singleton

**Pattern:** One read-only DuckDB connection opened at app startup, shared across all Dash callbacks.

**Why:** DuckDB is in-process (no network). Opening/closing connections per callback adds ~10ms overhead for no benefit. A single read-only connection is thread-safe for concurrent reads (Dash serves callbacks on multiple threads).

```python
# data/db.py
import duckdb
from config.settings import DB_PATH

_connection = None

def get_connection() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is None:
        _connection = duckdb.connect(DB_PATH, read_only=True)
    return _connection
```

### 3. Parametrized Query Functions

**Pattern:** All SQL lives in `data/queries.py` as functions that accept Python arguments and return pandas DataFrames. No SQL in page files or callbacks.

**Why:** Centralizes all data access. Makes queries testable, prevents SQL injection via parametrized queries, and means page files only deal with layout/figure logic.

```python
# data/queries.py
import pandas as pd
from data.db import get_connection

def get_vulnerable_products(importer: str, year: int, limit: int = 100) -> pd.DataFrame:
    return get_connection().execute("""
        SELECT product_code, product_name, hhi, georisk, essentiality, composite_score
        FROM dependency_scores
        WHERE importer_iso3 = $1 AND year = $2
        ORDER BY composite_score DESC
        LIMIT $3
    """, [importer, year, limit]).df()
```

### 4. Pure Figure Functions

**Pattern:** Each figure type is a pure function: `(pd.DataFrame, **options) → go.Figure`. No Dash imports, no callbacks, no side effects.

**Why:** Pure functions are trivially testable (`assert isinstance(result, go.Figure)`), reusable across pages, and composable. The page's callback is responsible for fetching data and calling the figure function — separation of concerns.

```python
# figures/choropleth.py
import plotly.express as px
import pandas as pd

def create_dependency_map(df: pd.DataFrame, color_col: str = "composite_score") -> go.Figure:
    fig = px.choropleth(
        df, locations="iso3", color=color_col,
        color_continuous_scale="RdYlGn_r",
        hover_data=["country_name", "composite_score", "hhi"],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    return fig
```

### 5. Dash Pages with Shared Shell

**Pattern:** `app.py` defines the persistent shell (navbar + sidebar + page_container). Each page in `pages/` defines only its unique content. Dash Pages handles routing.

**Why:** Navbar and sidebar persist across page navigation (no flash/reload). Page files stay focused on their specific view. URL structure is clean: `/`, `/country`, `/product`, `/methodology`.

```python
# app.py
import dash
from dash import Dash, html, page_container
import dash_bootstrap_components as dbc
from components.navbar import create_navbar

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
)

app.layout = dbc.Container([
    create_navbar(),
    html.Div(page_container, className="mt-3"),
], fluid=True)

server = app.server  # For gunicorn: gunicorn app:server

if __name__ == "__main__":
    app.run(debug=True)
```

### 6. Cross-Linking Between Views

**Pattern:** Country→Products view links to Product→Countries view (and vice versa) using `dcc.Link` with query parameters or path variables. Clicking a product in the country table navigates to the product view pre-filtered.

**Why:** The two entry points (D5 in features) are the core differentiator. Seamless cross-navigation makes the dual-view concept work.

```python
# In country_products.py callback:
# Each product row in the AG Grid links to the product view
dcc.Link("View product globally", href=f"/product?code={product_code}")

# pages/product_countries.py
dash.register_page(__name__, path="/product")

def layout(code=None, **kwargs):
    # code comes from query string: /product?code=8542
    ...
```

### 7. Lazy Pipeline Processing

**Pattern:** Pipeline uses Polars lazy evaluation throughout. Data is never fully materialized until the final `.collect()` or `.sink_parquet()`.

**Why:** Raw BACI data is 5–10GB. Eager loading into memory would require 15–20GB RAM. Polars lazy mode streams data in chunks, applies predicate pushdown, and only materializes final aggregations — staying within 2–4GB RSS.

```python
# pipeline/hhi.py
import polars as pl

def compute_hhi(trade_flows: pl.LazyFrame) -> pl.LazyFrame:
    return (
        trade_flows
        .group_by(["importer", "product", "year"])
        .agg([
            (pl.col("value") / pl.col("value").sum()).pow(2).sum().alias("hhi"),
            pl.col("value").sum().alias("total_value"),
        ])
    )
    # Returns LazyFrame — no computation yet. Caller chains or collects.
```

## Performance Considerations

### Data Pipeline Performance

| Concern | Strategy | Expected Impact |
|---------|----------|-----------------|
| Multi-GB CSV reads | Polars `scan_csv` (lazy, streaming) | 2–4GB RSS vs 15–20GB with pandas |
| Year-by-year processing | Process each BACI year file sequentially, write intermediate Parquet per year | Bounded memory regardless of total data size |
| HHI group-by aggregation | Polars parallel execution on all CPU cores | ~2–5 min for full 20-year dataset |
| Parquet compression | Snappy compression (default) for balanced speed/size | 5–10× smaller than CSV |
| Pipeline idempotency | Overwrite Parquet files and re-create DuckDB tables | Safe to re-run anytime; no partial state |

### Dashboard Performance

| Concern | Strategy | Expected Impact |
|---------|----------|-----------------|
| First callback latency | DuckDB connection opened at startup; first query warms disk cache | First callback: ~200ms. Subsequent: <50ms |
| Concurrent users (future) | DuckDB read-only connection is thread-safe; gunicorn with 4 workers | Each worker handles ~10 concurrent callbacks |
| Large result sets | Pre-aggregate in pipeline; limit queries to single (country, year) or (product, year) slice | Max ~5,000 rows per callback. Pandas handles trivially |
| Plotly figure rendering | Server returns JSON figure spec; client-side Plotly.js does rendering | Network payload ~50–200KB per figure. Client rendering <100ms |
| Choropleth map performance | Use Plotly's built-in country geometries (no external GeoJSON needed for country-level) | Instant — geometries bundled in plotly.js |
| Sankey diagram scaling | Limit to top-20 suppliers per (importer, product, year) | Readable and performant. Full supplier list in AG Grid table |
| AG Grid large tables | Server-side pagination if >5,000 rows; client-side sort/filter otherwise | Smooth at 5K rows. Use `rowModelType="infinite"` if needed |
| Page transitions | Dash Pages uses client-side routing (no full page reload) | Instant navigation feel |

### DuckDB Query Optimization

| Technique | When to Use |
|-----------|-------------|
| Column indexing | Add indexes on `(importer_iso3, year)` and `(product_code, year)` — the two most common filter patterns |
| Predicate pushdown | DuckDB automatically pushes WHERE clauses into Parquet scans if querying Parquet directly |
| Materialized tables over views | Load Parquet into DuckDB tables (not views) for index support and faster repeated queries |
| Summary tables | Pre-compute `home_stats` table (country count, product count, year range, top vulnerabilities) for instant landing page |
| Avoid SELECT * | Always select only needed columns. DuckDB's columnar storage skips unused columns entirely |

## Anti-Patterns to Avoid

### Anti-Pattern 1: Querying Raw Data in Callbacks
**What:** Running analytical queries on raw BACI trade flows from within Dash callbacks.
**Why bad:** 100M+ row scans take seconds. Multiple concurrent users = dashboard freezes. Memory spikes.
**Instead:** Pre-compute everything in the pipeline. Dashboard queries only pre-aggregated results (<20M rows, filtered to <5K per query).

### Anti-Pattern 2: Global DataFrame Variables
**What:** Loading entire DataFrames into module-level variables that persist in memory across all callbacks.
**Why bad:** 20M rows × 10 columns ≈ 1.5GB in pandas. Multiplied per gunicorn worker = 6GB for 4 workers. Wastes RAM when each callback only needs ~5K rows.
**Instead:** Query DuckDB per callback. DuckDB's in-process architecture makes this nearly as fast as reading from a variable, but uses memory only when needed.

### Anti-Pattern 3: Fat Page Files
**What:** Putting SQL queries, figure-building logic, component layout, and callbacks all in one page file.
**Why bad:** Untestable, unreusable, 500+ line files. Two pages with similar charts duplicate code.
**Instead:** Page files orchestrate: call `queries.py` for data, call `figures/*.py` for charts, assemble `components/*` for layout. Page files should be <200 lines.

### Anti-Pattern 4: Circular Imports with `app` Instance
**What:** Importing the `app` instance in page files to use `@app.callback`.
**Why bad:** Dash Pages uses `dash.register_page` which triggers imports. Importing `app` back creates circular imports.
**Instead:** Use `from dash import callback` — module-level callback decorator that doesn't need the app instance.

### Anti-Pattern 5: String-Concatenated SQL
**What:** Building SQL queries with f-strings or `.format()` using user inputs.
**Why bad:** SQL injection risk. Even in a local-first app, this is bad practice that would need rewriting for deployment.
**Instead:** Always use parametrized queries (`$1`, `$2` with parameter lists) via `duckdb.execute(sql, params)`.

## Scalability Considerations

| Concern | At 1 User (Dev) | At 10 Users (Hosted) | At 100+ Users |
|---------|-----------------|----------------------|---------------|
| **Server** | `python app.py` (debug mode) | gunicorn, 4 workers | gunicorn + CDN for static assets |
| **Database** | Single DuckDB file, read/write | DuckDB read-only, works fine — in-process per worker | Consider pre-querying to Parquet/JSON; DuckDB still viable with read-only workers |
| **Memory** | ~200MB (DuckDB + Dash) | ~200MB × 4 workers = 800MB | Acceptable for most hosting (1–2GB plans) |
| **Caching** | None needed | `flask_caching` with filesystem backend for repeated queries | Redis cache for shared state across workers |
| **Data updates** | Re-run pipeline, restart app | Re-run pipeline, swap DuckDB file, restart workers | Blue/green database swap (generate new file, atomic rename) |

## Sources

- Dash 4.0 Pages documentation: https://dash.plotly.com/urls — Multi-page app architecture, auto-routing, variable paths, query strings
- Dash Background Callbacks: https://dash.plotly.com/background-callbacks — DiskCache/Celery patterns for long-running callbacks
- DuckDB Python documentation: https://duckdb.org/docs/api/python/overview — Connection management, parametrized queries, pandas integration
- Polars user guide (lazy evaluation): https://docs.pola.rs/user-guide/lazy/ — LazyFrame, collect, sink, streaming
- STACK.md (this project): Technology decisions and version compatibility
- FEATURES.md (this project): Feature dependencies and build prioritization
