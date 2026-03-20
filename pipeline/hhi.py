"""HHI (Herfindahl-Hirschman Index) concentration scoring module.

Computes per-(importer_iso3, concorded_hs6, year) HHI on the 0–1 academic scale
(sum of squared supplier shares). Retains supplier-level rows so downstream phases
can access individual shares for drill-down analysis and Sankey diagrams.

Scale: 0–1 (sum of squared fractional shares). Monopoly → 1.0; 4 equal → 0.25.
NEVER use the 10,000-point DOJ scale — all thresholds elsewhere assume 0–1 scale.
"""

from pathlib import Path

import polars as pl
from loguru import logger


def compute_hhi(df: pl.DataFrame) -> pl.DataFrame:
    """Compute HHI per (importer_iso3, concorded_hs6, year) group.

    Returns a supplier-level DataFrame: one row per (importer, product, year, exporter)
    with the per-group HHI repeated across all rows in the group. This preserves
    individual supplier_share values needed for drill-down and Sankey.

    Args:
        df: DataFrame with columns [importer_iso3, exporter_iso3, concorded_hs6,
            year, value_usd]. Rows with value_usd <= 0 will be excluded.

    Returns:
        DataFrame with original columns plus: supplier_share (float, 0–1),
        hhi (float, 0–1, group-level scalar repeated per row), supplier_count (int).
    """
    key = ["importer_iso3", "concorded_hs6", "year"]

    return (
        df.filter(pl.col("value_usd") > 0)
        .with_columns(
            pl.col("value_usd").sum().over(key).alias("_total_import_value")
        )
        .with_columns(
            (pl.col("value_usd") / pl.col("_total_import_value")).alias("supplier_share")
        )
        .with_columns(
            (pl.col("supplier_share").pow(2).sum().over(key)).alias("hhi"),
            pl.len().over(key).cast(pl.Int32).alias("supplier_count"),
        )
        .drop("_total_import_value")
    )


def run_hhi_scoring(config: dict) -> dict:
    """Compute HHI for all years in processed_dir, write partitioned Parquet.

    Reads data/processed/year=YYYY/data.parquet year-by-year (memory-efficient).
    Writes to data/scoring/hhi/year=YYYY/data.parquet with zstd compression.

    Args:
        config: Pipeline config dict. Reads:
            config["processing"]["processed_dir"]  — input Parquet root
            config.get("scoring", {}).get("output_dir", "data/scoring")  — output root

    Returns:
        dict with years_processed (list[int]), rows_written (int).
    """
    processed_dir = Path(config["processing"]["processed_dir"])
    scoring_dir = Path(config.get("scoring", {}).get("output_dir", "data/scoring"))
    hhi_dir = scoring_dir / "hhi"

    year_dirs = sorted(processed_dir.glob("year=*"))
    if not year_dirs:
        logger.warning(f"No year partitions found in {processed_dir}. Run ingestion first.")
        return {"years_processed": [], "rows_written": 0}

    years_processed = []
    total_rows = 0

    for year_dir in year_dirs:
        parquet_path = year_dir / "data.parquet"
        if not parquet_path.exists():
            logger.warning(f"Skipping {year_dir}: data.parquet not found")
            continue

        year_val = int(year_dir.name.split("=")[1])
        out_path = hhi_dir / f"year={year_val}" / "data.parquet"

        if out_path.exists():
            logger.info(f"HHI year={year_val}: skipping (already exists)")
            years_processed.append(year_val)
            continue

        logger.info(f"HHI year={year_val}: computing...")
        df = pl.read_parquet(
            parquet_path,
            columns=["year", "importer_iso3", "exporter_iso3", "concorded_hs6", "value_usd"],
        )
        result = compute_hhi(df)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        result.write_parquet(out_path, compression="zstd")

        years_processed.append(year_val)
        total_rows += len(result)
        logger.info(f"HHI year={year_val}: {len(result):,} supplier rows written")

    logger.info(f"HHI scoring complete: {len(years_processed)} years, {total_rows:,} total rows")
    return {"years_processed": years_processed, "rows_written": total_rows}
