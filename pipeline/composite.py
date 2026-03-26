"""Composite dependency score module.

Combines HHI concentration, geopolitical risk, and product substitutability into a
single composite dependency score per (importer, product, year) supplier tuple.

Formula:
    basket_geo_risk = sum(supplier_share × exporter_geo_risk)  per (importer, product, year)
    substitutability_score = sqrt(global_export_hhi)  per product
    composite_score = w1×hhi + w2×basket_geo_risk + w3×substitutability_score

Default weights: w1=0.35 (HHI), w2=0.35 (geo_risk), w3=0.30 (substitutability)
These defaults optimize for surfacing dangerous dependencies where both concentration
and geopolitical risk are high, with substitutability amplifying the concern.
Weights are user-adjustable in Phase 4 (SCOR-05) — not in this module.

Output keeps supplier-level rows (one per importer+product+year+exporter) so the
fact table enables both aggregate views and drill-down analysis from the same data.
"""

from pathlib import Path

import polars as pl
from loguru import logger

DEFAULT_WEIGHTS: dict = {
    "hhi": 0.35,
    "geo_risk": 0.35,
    "substitutability": 0.30,
}
# Fill value for missing geo-risk join (avoid zeroing out the score entirely)
_GEO_RISK_FILL = 0.5    # median risk for countries with no WGI coverage


def compute_composite(
    hhi_df: pl.DataFrame,
    georisk_df: pl.DataFrame,
    flags_df: pl.DataFrame,
    weights: dict | None = None,
) -> pl.DataFrame:
    """Join HHI, geo-risk, flags, and compute composite score.

    Args:
        hhi_df: Supplier-level DataFrame from hhi.py
                Columns: importer_iso3, exporter_iso3, concorded_hs6, year, value_usd,
                         supplier_share, hhi, supplier_count
        georisk_df: Country-year DataFrame from georisk.py
                   Columns: iso3, year, governance_risk, sanctions_intensity, geo_risk
        flags_df: Product DataFrame from flags.py
                  Columns: hs6, flags, global_export_hhi, crm_listed_since, hs22_only
        weights: Override default weights. Must sum to ~1.0.

    Returns:
        Supplier-level DataFrame with composite_score added.
        Columns: importer_iso3, concorded_hs6, year, exporter_iso3, value_usd,
                 supplier_share, hhi, exporter_geo_risk, basket_geo_risk,
                 global_export_hhi, substitutability_score, flags, hs22_only,
                 crm_listed_since, composite_score
    """
    w = weights or DEFAULT_WEIGHTS
    key = ["importer_iso3", "concorded_hs6", "year"]

    # Join geo-risk on (exporter_iso3, year) → (iso3, year)
    result = hhi_df.join(
        georisk_df.select(["iso3", "year", "geo_risk"]).rename(
            {"iso3": "exporter_iso3", "geo_risk": "exporter_geo_risk"}
        ),
        on=["exporter_iso3", "year"],
        how="left",
    ).with_columns(
        pl.col("exporter_geo_risk").fill_null(_GEO_RISK_FILL)
    )

    # Compute fill value from median before join
    substitutability_fill = float((flags_df["global_export_hhi"].median() or 0.0) ** 0.5)

    # Join flags on concorded_hs6
    result = result.join(
        flags_df.select(["hs6", "global_export_hhi", "flags", "crm_listed_since", "hs22_only"])
        .rename({"hs6": "concorded_hs6"}),
        on="concorded_hs6",
        how="left",
    ).with_columns(
        pl.col("global_export_hhi").fill_null(substitutability_fill ** 2),
        pl.col("flags").fill_null(pl.lit([])),
        pl.col("hs22_only").fill_null(False),
    )

    # substitutability_score = sqrt(global_export_hhi)
    result = result.with_columns(
        pl.col("global_export_hhi").sqrt().alias("substitutability_score")
    )

    # Compute basket_geo_risk = sum(share × exporter_geo_risk) per (importer, product, year)
    result = result.with_columns(
        (pl.col("supplier_share") * pl.col("exporter_geo_risk"))
        .sum().over(key)
        .alias("basket_geo_risk")
    )

    # Composite score
    result = result.with_columns(
        (
            w["hhi"] * pl.col("hhi")
            + w["geo_risk"] * pl.col("basket_geo_risk")
            + w["substitutability"] * pl.col("substitutability_score")
        ).clip(0.0, 1.0).alias("composite_score")
    )

    return result.select([
        "importer_iso3", "concorded_hs6", "year", "exporter_iso3",
        "value_usd", "supplier_share", "hhi",
        "exporter_geo_risk", "basket_geo_risk",
        "global_export_hhi", "substitutability_score", "flags", "hs22_only",
        "crm_listed_since", "composite_score",
    ])


def run_composite_scoring(config: dict) -> dict:
    """Compute composite scores for all years, write per-year Parquet.

    Reads HHI, geo-risk, and essentiality Parquet from scoring_dir.
    Writes to data/scoring/composite/year=YYYY/data.parquet.
    """
    scoring_dir = Path(config.get("scoring", {}).get("output_dir", "data/scoring"))
    weights_cfg = config.get("scoring", {}).get("weights", DEFAULT_WEIGHTS)

    hhi_dir = scoring_dir / "hhi"
    georisk_path = scoring_dir / "georisk" / "georisk_by_country_year.parquet"
    flags_path = scoring_dir / "flags" / "flags_scores.parquet"
    composite_dir = scoring_dir / "composite"

    if not georisk_path.exists():
        raise FileNotFoundError(
            f"Geo-risk Parquet not found: {georisk_path}. Run geo-risk scoring first."
        )
    if not flags_path.exists():
        raise FileNotFoundError(
            f"Flags Parquet not found: {flags_path}. Run flags scoring first."
        )

    logger.info("Composite: loading geo-risk and flags reference data...")
    georisk_df = pl.read_parquet(georisk_path)
    flags_df = pl.read_parquet(flags_path)

    year_dirs = sorted(hhi_dir.glob("year=*"))
    if not year_dirs:
        raise FileNotFoundError(
            f"No HHI year partitions found in {hhi_dir}. Run HHI scoring first."
        )

    years_processed = []
    total_rows = 0

    for year_dir in year_dirs:
        hhi_path = year_dir / "data.parquet"
        if not hhi_path.exists():
            continue
        year_val = int(year_dir.name.split("=")[1])
        out_path = composite_dir / f"year={year_val}" / "data.parquet"

        if out_path.exists():
            logger.info(f"Composite year={year_val}: skipping (already exists)")
            years_processed.append(year_val)
            continue

        logger.info(f"Composite year={year_val}: computing...")
        hhi_df = pl.read_parquet(hhi_path)
        result = compute_composite(hhi_df, georisk_df, flags_df, weights_cfg)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        result.write_parquet(out_path, compression="zstd")

        years_processed.append(year_val)
        total_rows += len(result)
        logger.info(f"Composite year={year_val}: {len(result):,} rows written")

    logger.info(
        f"Composite scoring complete: {len(years_processed)} years, {total_rows:,} total rows"
    )
    return {"years_processed": years_processed, "rows_written": total_rows}
