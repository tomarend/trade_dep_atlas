"""Tests for DuckDB export module (DATA-05)."""

import time
from pathlib import Path

import duckdb
import polars as pl
import pytest

from pipeline.export import build_duckdb


# ── Fixtures ──────────────────────────────────────────────────────────────────

_COMPOSITE_SCHEMA = {
    "importer_iso3": pl.Utf8,
    "concorded_hs6": pl.Utf8,
    "year": pl.Int64,
    "exporter_iso3": pl.Utf8,
    "value_usd": pl.Float64,
    "supplier_share": pl.Float64,
    "hhi": pl.Float64,
    "exporter_geo_risk": pl.Float64,
    "basket_geo_risk": pl.Float64,
    "essentiality_score": pl.Float64,
    "essentiality_tier": pl.Utf8,
    "crm_listed_since": pl.Int64,
    "composite_score": pl.Float64,
}

_ESS_SCHEMA = {
    "hs6": pl.Utf8,
    "category": pl.Utf8,
    "essentiality_tier": pl.Utf8,
    "essentiality_score": pl.Float64,
    "global_export_hhi": pl.Float64,
    "crm_listed_since": pl.Int64,
}

_IMPORTERS = ["DEU", "FRA", "USA", "JPN", "GBR"]
_EXPORTERS = ["CHN", "AUS", "ZAF", "CHL", "CAN"]
_HS6_CODES = ["260111", "260112", "280450", "310210", "290110"]


def _make_composite_df(n: int = 1000) -> pl.DataFrame:
    """Generate synthetic composite rows for testing."""
    import random

    random.seed(42)
    rows = []
    for i in range(n):
        imp = _IMPORTERS[i % len(_IMPORTERS)]
        hs6 = _HS6_CODES[i % len(_HS6_CODES)]
        exp = _EXPORTERS[i % len(_EXPORTERS)]
        share = round(random.uniform(0.1, 1.0), 4)
        geo = round(random.uniform(0.0, 1.0), 4)
        hhi = round(random.uniform(0.1, 1.0), 4)
        ess = round(random.uniform(0.1, 1.0), 4)
        composite = round(0.35 * hhi + 0.35 * geo + 0.30 * ess, 6)
        rows.append({
            "importer_iso3": imp,
            "concorded_hs6": hs6,
            "year": 2022,
            "exporter_iso3": exp,
            "value_usd": float(random.randint(100, 100_000)),
            "supplier_share": share,
            "hhi": hhi,
            "exporter_geo_risk": geo,
            "basket_geo_risk": geo * share,
            "essentiality_score": ess,
            "essentiality_tier": "standard",
            "crm_listed_since": None,
            "composite_score": composite,
        })
    return pl.DataFrame(rows, schema=_COMPOSITE_SCHEMA)


def _write_composite_parquet(tmp_path: Path, df: pl.DataFrame | None = None) -> Path:
    composite_dir = tmp_path / "composite"
    year_dir = composite_dir / "year=2022"
    year_dir.mkdir(parents=True)
    parquet_path = year_dir / "data.parquet"
    out_df = df if df is not None else _make_composite_df()
    out_df.write_parquet(year_dir / "data.parquet")
    return composite_dir


def _write_essentiality_parquet(tmp_path: Path) -> Path:
    ess_path = tmp_path / "essentiality_scores.parquet"
    rows = [
        {"hs6": hs6, "category": "other", "essentiality_tier": "standard",
         "essentiality_score": 0.2, "global_export_hhi": 0.3, "crm_listed_since": None}
        for hs6 in _HS6_CODES
    ]
    pl.DataFrame(rows, schema=_ESS_SCHEMA).write_parquet(ess_path)
    return ess_path


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_duckdb_creates_fact_table(tmp_path):
    """build_duckdb creates dependency_scores table with correct row count."""
    n = 50
    df = _make_composite_df(n)
    composite_dir = _write_composite_parquet(tmp_path, df)
    ess_path = _write_essentiality_parquet(tmp_path)
    db_path = tmp_path / "test.duckdb"

    build_duckdb(db_path, composite_dir, tmp_path / "georisk.parquet", ess_path, tmp_path)

    with duckdb.connect(str(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM dependency_scores").fetchone()[0]
    assert count == n


def test_duckdb_creates_dimension_tables(tmp_path):
    """build_duckdb creates both countries and products dimension tables."""
    composite_dir = _write_composite_parquet(tmp_path)
    ess_path = _write_essentiality_parquet(tmp_path)
    db_path = tmp_path / "test.duckdb"

    build_duckdb(db_path, composite_dir, tmp_path / "georisk.parquet", ess_path, tmp_path)

    with duckdb.connect(str(db_path)) as conn:
        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        assert "countries" in tables
        assert "products" in tables
        products_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert products_count == len(_HS6_CODES)


def test_duckdb_expected_columns(tmp_path):
    """dependency_scores has all expected columns including composite_score."""
    composite_dir = _write_composite_parquet(tmp_path)
    ess_path = _write_essentiality_parquet(tmp_path)
    db_path = tmp_path / "test.duckdb"

    build_duckdb(db_path, composite_dir, tmp_path / "georisk.parquet", ess_path, tmp_path)

    with duckdb.connect(str(db_path)) as conn:
        cols = {r[0] for r in conn.execute("DESCRIBE dependency_scores").fetchall()}

    expected = {
        "importer_iso3", "hs6", "year", "exporter_iso3",
        "supplier_share", "hhi", "exporter_geo_risk",
        "basket_geo_risk", "essentiality_score", "composite_score",
    }
    assert expected.issubset(cols)


def test_duckdb_idempotent(tmp_path):
    """Calling build_duckdb twice does not raise; row counts are consistent."""
    composite_dir = _write_composite_parquet(tmp_path)
    ess_path = _write_essentiality_parquet(tmp_path)
    db_path = tmp_path / "test.duckdb"

    build_duckdb(db_path, composite_dir, tmp_path / "georisk.parquet", ess_path, tmp_path)
    build_duckdb(db_path, composite_dir, tmp_path / "georisk.parquet", ess_path, tmp_path)

    with duckdb.connect(str(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM dependency_scores").fetchone()[0]
    assert count == 1000  # default _make_composite_df size


def test_duckdb_query_performance(tmp_path):
    """Dashboard query WHERE importer_iso3='DEU' completes within 50ms."""
    composite_dir = _write_composite_parquet(tmp_path, _make_composite_df(1000))
    ess_path = _write_essentiality_parquet(tmp_path)
    db_path = tmp_path / "test.duckdb"

    build_duckdb(db_path, composite_dir, tmp_path / "georisk.parquet", ess_path, tmp_path)

    with duckdb.connect(str(db_path)) as conn:
        start = time.perf_counter()
        rows = conn.execute(
            "SELECT hs6, composite_score FROM dependency_scores "
            "WHERE importer_iso3='DEU' ORDER BY composite_score DESC LIMIT 100"
        ).fetchall()
        elapsed_ms = (time.perf_counter() - start) * 1000

    assert len(rows) > 0, "Query returned no rows — check test data has DEU importers"
    assert elapsed_ms < 50, f"Query took {elapsed_ms:.1f}ms (threshold: 50ms)"
