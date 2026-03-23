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
        rows = _conn.execute("SELECT iso3, name FROM countries ORDER BY name").fetchall()
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
