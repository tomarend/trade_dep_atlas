"""DuckDB singleton and cached startup queries for the DependencyAtlas dashboard."""

import os
from functools import lru_cache
from pathlib import Path

import duckdb
from loguru import logger

# ---------------------------------------------------------------------------
# DB path resolution
# ---------------------------------------------------------------------------
_db_path: Path = Path(
    os.environ.get(
        "DASHBOARD_DB",
        str(Path(__file__).parent.parent / "data" / "dashboard.duckdb"),
    )
)

# ---------------------------------------------------------------------------
# Connection singleton — opened once at startup, read-only
# ---------------------------------------------------------------------------
_conn: duckdb.DuckDBPyConnection | None = None

if _db_path.exists():
    try:
        _conn = duckdb.connect(str(_db_path), read_only=True)
        logger.info("DuckDB connected: {}", _db_path)
    except Exception as exc:
        logger.error("DuckDB connection failed for {}: {}", _db_path, exc)
        _conn = None
else:
    logger.warning("DuckDB not found at {} — running in offline mode", _db_path)

#: True when the database is available and the connection succeeded.
db_available: bool = _conn is not None


# ---------------------------------------------------------------------------
# Cached startup queries
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_year_range() -> tuple[int, int]:
    """Return (min_year, max_year) from dependency_scores table."""
    if _conn is None:
        return (1995, 2022)
    try:
        row = _conn.execute("SELECT MIN(year), MAX(year) FROM dependency_scores").fetchone()
        if row and row[0] is not None:
            return (int(row[0]), int(row[1]))
    except Exception as exc:
        logger.error("get_year_range query failed: {}", exc)
    return (1995, 2022)


@lru_cache(maxsize=1)
def get_country_list() -> list[tuple[str, str]]:
    """Return list of (iso3, name) ordered by name."""
    if _conn is None:
        return []
    try:
        rows = _conn.execute(
            "SELECT c.iso3, c.name FROM countries c "
            "WHERE c.iso3 IN (SELECT DISTINCT importer_iso3 FROM dependency_scores) "
            "ORDER BY c.name"
        ).fetchall()
        return [(str(r[0]), str(r[1])) for r in rows]
    except Exception as exc:
        logger.error("get_country_list query failed: {}", exc)
    return []


@lru_cache(maxsize=1)
def get_default_country() -> str:
    """Return iso3 of the country with highest mean composite_score."""
    if _conn is None:
        return "USA"
    try:
        row = _conn.execute(
            "SELECT importer_iso3 FROM dependency_scores "
            "GROUP BY importer_iso3 ORDER BY AVG(composite_score) DESC LIMIT 1"
        ).fetchone()
        if row:
            return str(row[0])
    except Exception as exc:
        logger.error("get_default_country query failed: {}", exc)
    return "USA"


@lru_cache(maxsize=1)
def get_default_product() -> str:
    """Return hs6 of the product with highest mean composite_score."""
    if _conn is None:
        return "271019"
    try:
        row = _conn.execute(
            "SELECT hs6 FROM dependency_scores "
            "GROUP BY hs6 ORDER BY AVG(composite_score) DESC LIMIT 1"
        ).fetchone()
        if row:
            return str(row[0])
    except Exception as exc:
        logger.error("get_default_product query failed: {}", exc)
    return "271019"



# ---------------------------------------------------------------------------
# Parameterized queries for Phase 4: Country→Products View
# ---------------------------------------------------------------------------


def get_product_scores(importer_iso3: str, year: int | None = None) -> list[dict]:
    """Return per-product scores for the given importer and year."""
    if _conn is None:
        return []
    yr = year or get_year_range()[1]
    try:
        rows = _conn.execute(
            """
            SELECT DISTINCT
                ds.hs6,
                COALESCE(p.description, '') AS description,
                ds.essentiality_tier,
                ds.hhi,
                ds.basket_geo_risk,
                ds.essentiality_score,
                ds.composite_score
            FROM dependency_scores ds
            LEFT JOIN products p ON ds.hs6 = p.hs6
            WHERE ds.importer_iso3 = ? AND ds.year = ?
            ORDER BY ds.composite_score DESC
            """,
            [importer_iso3, yr],
        ).fetchall()
        cols = ["hs6", "description", "essentiality_tier", "hhi",
                "basket_geo_risk", "essentiality_score", "composite_score"]
        return [
            {
                c: (round(v, 4) if isinstance(v, float) else v)
                for c, v in zip(cols, row)
            }
            for row in rows
        ]
    except Exception as exc:
        logger.error("get_product_scores query failed: {}", exc)
    return []


def get_country_summary(importer_iso3: str, year: int | None = None) -> dict:
    """Return aggregate summary stats for the given importer and year."""
    if _conn is None:
        return {
            "avg_hhi": 0, "avg_geo_risk": 0, "avg_essentiality": 0,
            "avg_composite": 0, "product_count": 0, "critical_count": 0,
            "high_risk_count": 0,
        }
    yr = year or get_year_range()[1]
    try:
        row = _conn.execute(
            """
            SELECT
                AVG(hhi) AS avg_hhi,
                AVG(basket_geo_risk) AS avg_geo_risk,
                AVG(essentiality_score) AS avg_essentiality,
                AVG(composite_score) AS avg_composite,
                COUNT(*) AS product_count,
                SUM(CASE WHEN essentiality_tier = 'critical' THEN 1 ELSE 0 END) AS critical_count,
                SUM(CASE WHEN composite_score > 0.7 THEN 1 ELSE 0 END) AS high_risk_count
            FROM (
                SELECT DISTINCT hs6, hhi, basket_geo_risk, essentiality_score,
                       essentiality_tier, composite_score
                FROM dependency_scores
                WHERE importer_iso3 = ? AND year = ?
            ) sub
            """,
            [importer_iso3, yr],
        ).fetchone()
        if row:
            return {
                "avg_hhi": round(float(row[0] or 0), 3),
                "avg_geo_risk": round(float(row[1] or 0), 3),
                "avg_essentiality": round(float(row[2] or 0), 3),
                "avg_composite": round(float(row[3] or 0), 3),
                "product_count": int(row[4] or 0),
                "critical_count": int(row[5] or 0),
                "high_risk_count": int(row[6] or 0),
            }
    except Exception as exc:
        logger.error("get_country_summary query failed: {}", exc)
    return {
        "avg_hhi": 0, "avg_geo_risk": 0, "avg_essentiality": 0,
        "avg_composite": 0, "product_count": 0, "critical_count": 0,
        "high_risk_count": 0,
    }


def get_supplier_breakdown(importer_iso3: str, hs6: str, year: int | None = None) -> list[dict]:
    """Return supplier country breakdown for a specific product and importer."""
    if _conn is None:
        return []
    yr = year or get_year_range()[1]
    try:
        rows = _conn.execute(
            """
            SELECT
                ds.exporter_iso3,
                COALESCE(c.name, ds.exporter_iso3) AS exporter_name,
                ds.supplier_share,
                ds.value_usd,
                ds.exporter_geo_risk,
                c.region,
                c.continent
            FROM dependency_scores ds
            LEFT JOIN countries c ON ds.exporter_iso3 = c.iso3
            WHERE ds.importer_iso3 = ? AND ds.hs6 = ? AND ds.year = ?
            ORDER BY ds.supplier_share DESC
            """,
            [importer_iso3, hs6, yr],
        ).fetchall()
        cols = ["exporter_iso3", "exporter_name", "supplier_share",
                "value_usd", "exporter_geo_risk", "region", "continent"]
        return [
            {
                c: (round(v, 4) if isinstance(v, float) else v)
                for c, v in zip(cols, row)
            }
            for row in rows
        ]
    except Exception as exc:
        logger.error("get_supplier_breakdown query failed: {}", exc)
    return []


# ---------------------------------------------------------------------------
# Parameterized queries for Phase 5: Product->Countries View
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_product_list() -> list[dict]:
    """Return all products with hs2, hs4, hs6, description for hierarchical selector."""
    if _conn is None:
        return []
    try:
        rows = _conn.execute(
            "SELECT hs2, hs4, hs6, description FROM products ORDER BY hs2, hs4, hs6"
        ).fetchall()
        return [
            {"hs2": str(r[0]), "hs4": str(r[1]), "hs6": str(r[2]), "description": str(r[3])}
            for r in rows
        ]
    except Exception as exc:
        logger.error("get_product_list query failed: {}", exc)
    return []


def get_importer_scores(hs6: str, year: int | None = None) -> list[dict]:
    """Return per-importer dependency scores for the given product and year."""
    if _conn is None:
        return []
    yr = year or get_year_range()[1]
    try:
        rows = _conn.execute(
            """
            SELECT
                sub.importer_iso3,
                COALESCE(c.name, sub.importer_iso3) AS importer_name,
                sub.hhi,
                sub.basket_geo_risk,
                sub.essentiality_score,
                sub.composite_score,
                sub.essentiality_tier
            FROM (
                SELECT DISTINCT
                    importer_iso3, hhi, basket_geo_risk,
                    essentiality_score, composite_score, essentiality_tier
                FROM dependency_scores
                WHERE hs6 = ? AND year = ?
            ) sub
            LEFT JOIN countries c ON sub.importer_iso3 = c.iso3
            ORDER BY sub.composite_score DESC
            """,
            [hs6, yr],
        ).fetchall()
        cols = ["importer_iso3", "importer_name", "hhi", "basket_geo_risk",
                "essentiality_score", "composite_score", "essentiality_tier"]
        return [
            {
                c: (round(v, 4) if isinstance(v, float) else v)
                for c, v in zip(cols, row)
            }
            for row in rows
        ]
    except Exception as exc:
        logger.error("get_importer_scores query failed: {}", exc)
    return []


def get_product_summary(hs6: str, year: int | None = None) -> dict:
    """Return aggregate summary stats for the given product across all importers."""
    if _conn is None:
        return {
            "avg_hhi": 0, "avg_geo_risk": 0, "avg_essentiality": 0,
            "avg_composite": 0, "importer_count": 0, "high_risk_count": 0,
        }
    yr = year or get_year_range()[1]
    try:
        row = _conn.execute(
            """
            SELECT
                AVG(hhi) AS avg_hhi,
                AVG(basket_geo_risk) AS avg_geo_risk,
                AVG(essentiality_score) AS avg_essentiality,
                AVG(composite_score) AS avg_composite,
                COUNT(*) AS importer_count,
                SUM(CASE WHEN composite_score > 0.7 THEN 1 ELSE 0 END) AS high_risk_count
            FROM (
                SELECT DISTINCT
                    importer_iso3, hhi, basket_geo_risk,
                    essentiality_score, composite_score
                FROM dependency_scores
                WHERE hs6 = ? AND year = ?
            ) sub
            """,
            [hs6, yr],
        ).fetchone()
        if row:
            return {
                "avg_hhi": round(float(row[0] or 0), 3),
                "avg_geo_risk": round(float(row[1] or 0), 3),
                "avg_essentiality": round(float(row[2] or 0), 3),
                "avg_composite": round(float(row[3] or 0), 3),
                "importer_count": int(row[4] or 0),
                "high_risk_count": int(row[5] or 0),
            }
    except Exception as exc:
        logger.error("get_product_summary query failed: {}", exc)
    return {
        "avg_hhi": 0, "avg_geo_risk": 0, "avg_essentiality": 0,
        "avg_composite": 0, "importer_count": 0, "high_risk_count": 0,
    }



# ---------------------------------------------------------------------------
# Parameterized queries for Phase 6: Time Series & Advanced Visualizations
# ---------------------------------------------------------------------------


def get_score_trend(importer_iso3: str, hs6: str) -> list[dict]:
    """Return time series of scores across all years for a specific importer-product pair."""
    if _conn is None:
        return []
    try:
        rows = _conn.execute(
            """
            SELECT DISTINCT year, composite_score, hhi, basket_geo_risk, essentiality_score
            FROM dependency_scores
            WHERE importer_iso3 = ? AND hs6 = ?
            ORDER BY year
            """,
            [importer_iso3, hs6],
        ).fetchall()
        cols = ["year", "composite_score", "hhi", "basket_geo_risk", "essentiality_score"]
        return [
            {
                c: (round(v, 4) if isinstance(v, float) else v)
                for c, v in zip(cols, row)
            }
            for row in rows
        ]
    except Exception as exc:
        logger.error("get_score_trend query failed: {}", exc)
    return []


def get_trade_flows(hs6: str, year: int | None = None) -> list[dict]:
    """Return exporter->importer trade flows for Sankey/network visualizations."""
    if _conn is None:
        return []
    yr = year or get_year_range()[1]
    try:
        rows = _conn.execute(
            """
            SELECT
                ds.exporter_iso3,
                COALESCE(ce.name, ds.exporter_iso3) AS exporter_name,
                ds.importer_iso3,
                COALESCE(ci.name, ds.importer_iso3) AS importer_name,
                ds.value_usd,
                ds.supplier_share,
                ds.exporter_geo_risk
            FROM dependency_scores ds
            LEFT JOIN countries ce ON ds.exporter_iso3 = ce.iso3
            LEFT JOIN countries ci ON ds.importer_iso3 = ci.iso3
            WHERE ds.hs6 = ? AND ds.year = ?
            ORDER BY ds.value_usd DESC
            """,
            [hs6, yr],
        ).fetchall()
        cols = ["exporter_iso3", "exporter_name", "importer_iso3", "importer_name",
                "value_usd", "supplier_share", "exporter_geo_risk"]
        return [
            {
                c: (round(v, 4) if isinstance(v, float) else v)
                for c, v in zip(cols, row)
            }
            for row in rows
        ]
    except Exception as exc:
        logger.error("get_trade_flows query failed: {}", exc)
    return []
