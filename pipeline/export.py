"""DuckDB export module: loads scored Parquet files into a star-schema DuckDB.

Star schema:
  dependency_scores (fact) — supplier-level detail per (importer, product, year, exporter)
  countries (dimension) — ISO3, name, region, continent, is_reexport_hub
  products (dimension) — HS6/HS4/HS2 hierarchy, description, essentiality, global HHI

Query target: <50ms for typical dashboard queries.
DuckDB reads directly from Parquet via glob — no intermediate CSV needed.
"""

import time
from pathlib import Path

import duckdb
import polars as pl
from loguru import logger


def build_duckdb(
    duckdb_path: str | Path,
    composite_dir: Path,
    georisk_path: Path,
    essentiality_path: Path,
    reference_dir: Path,
    raw_dir: Path | None = None,
) -> None:
    """Create star-schema DuckDB database from scored Parquet intermediates.

    Drops and recreates all tables (idempotent). Creates indexes for dashboard queries.

    Args:
        duckdb_path: Output path for .duckdb file (e.g., data/dashboard.duckdb)
        composite_dir: Root of composite Parquet output (data/scoring/composite/)
        georisk_path: Path to georisk_by_country_year.parquet (unused at table level;
                      geo_risk per exporter is embedded in the fact table via composite.py)
        essentiality_path: Path to essentiality_scores.parquet (source for products dim)
        reference_dir: Pipeline reference dir (for country mapping and product descriptions)
    """
    duckdb_path = Path(duckdb_path)
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    composite_glob = str(composite_dir / "year=*" / "data.parquet")

    with duckdb.connect(str(duckdb_path)) as conn:
        # ── Fact table: dependency_scores ──────────────────────────────────
        logger.info("DuckDB: building dependency_scores fact table...")
        conn.execute("DROP TABLE IF EXISTS dependency_scores")
        conn.execute(f"""
            CREATE TABLE dependency_scores AS
            SELECT
                importer_iso3,
                concorded_hs6  AS hs6,
                year,
                exporter_iso3,
                value_usd,
                supplier_share,
                hhi,
                exporter_geo_risk,
                basket_geo_risk,
                essentiality_score,
                essentiality_tier,
                crm_listed_since,
                composite_score
            FROM read_parquet('{composite_glob}', hive_partitioning = true)
        """)
        fact_count = conn.execute("SELECT COUNT(*) FROM dependency_scores").fetchone()[0]
        logger.info(f"DuckDB: {fact_count:,} rows in dependency_scores")

        # ── Dimension table: countries ──────────────────────────────────────
        logger.info("DuckDB: building countries dimension table...")
        from pipeline.countries import load_country_mapping

        country_mapping = load_country_mapping(reference_dir, raw_dir=raw_dir)
        country_rows = [
            {
                "iso3": rec.iso3,
                "name": rec.name,
                "region": rec.region,
                "continent": rec.continent,
                "is_reexport_hub": rec.is_reexport_hub,
            }
            for rec in country_mapping.values()
            if rec.iso3  # skip entries without a valid ISO3
        ]
        countries_df = pl.DataFrame(
            country_rows,
            schema={
                "iso3": pl.Utf8,
                "name": pl.Utf8,
                "region": pl.Utf8,
                "continent": pl.Utf8,
                "is_reexport_hub": pl.Boolean,
            },
        )
        conn.execute("DROP TABLE IF EXISTS countries")
        conn.register("_countries", countries_df.to_arrow())
        conn.execute("""
            CREATE TABLE countries AS
            SELECT iso3, name, region, continent, is_reexport_hub
            FROM _countries
        """)
        conn.unregister("_countries")
        logger.info(f"DuckDB: {len(countries_df):,} rows in countries")

        # ── Dimension table: products ───────────────────────────────────────
        logger.info("DuckDB: building products dimension table...")
        ess_df = pl.read_parquet(essentiality_path)

        from pipeline.concordance import load_product_descriptions

        descriptions = load_product_descriptions(reference_dir, raw_dir=raw_dir)
        if descriptions:
            desc_df = pl.DataFrame(
                [{"hs6": k, "description": v[0]} for k, v in descriptions.items()],
                schema={"hs6": pl.Utf8, "description": pl.Utf8},
            )
            products_df = ess_df.join(desc_df, on="hs6", how="left")
        else:
            products_df = ess_df.with_columns(pl.lit("").alias("description"))

        products_df = products_df.with_columns([
            pl.col("hs6").str.slice(0, 2).alias("hs2"),
            pl.col("hs6").str.slice(0, 4).alias("hs4"),
            pl.col("description").fill_null(""),
            pl.col("crm_listed_since").cast(pl.Int64, strict=False),
        ]).select([
            "hs6", "hs2", "hs4", "description",
            pl.col("category").alias("essentiality_category"),
            "essentiality_tier",
            "essentiality_score",
            "global_export_hhi",
            "crm_listed_since",
        ])

        conn.execute("DROP TABLE IF EXISTS products")
        conn.register("_products", products_df.to_arrow())
        conn.execute("""
            CREATE TABLE products AS
            SELECT hs6, hs2, hs4, description, essentiality_category,
                   essentiality_tier, essentiality_score, global_export_hhi, crm_listed_since
            FROM _products
        """)
        conn.unregister("_products")
        logger.info(f"DuckDB: {len(products_df):,} rows in products")

        # DuckDB's columnar storage + zone maps already gives fast analytical
        # queries without explicit B-tree indexes.  Indexes on 300M+ rows are
        # extremely slow to build and provide negligible benefit for OLAP.
        logger.info(f"DuckDB build complete: {duckdb_path}")


def run_duckdb_export(config: dict) -> dict:
    """Orchestrate DuckDB export: scored Parquet → star schema .duckdb file."""
    scoring_dir = Path(config.get("scoring", {}).get("output_dir", "data/scoring"))
    duckdb_path = config.get("scoring", {}).get("duckdb_path", "data/dashboard.duckdb")
    reference_dir = Path(config["processing"]["reference_dir"])

    composite_dir = scoring_dir / "composite"
    georisk_path = scoring_dir / "georisk" / "georisk_by_country_year.parquet"
    essentiality_path = scoring_dir / "essentiality" / "essentiality_scores.parquet"

    if not composite_dir.exists():
        raise FileNotFoundError(
            f"Composite scoring output not found: {composite_dir}. Run composite scoring first."
        )

    raw_dir = Path(config["baci"]["raw_dir"])

    start = time.time()
    build_duckdb(duckdb_path, composite_dir, georisk_path, essentiality_path, reference_dir, raw_dir=raw_dir)
    duration = round(time.time() - start, 2)
    logger.info(f"DuckDB export complete in {duration}s → {duckdb_path}")
    return {"duckdb_path": str(duckdb_path), "duration_seconds": duration}
