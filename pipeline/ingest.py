"""Core ingestion pipeline: raw BACI CSV → cleaned, concorded, country-mapped Parquet."""

import re
import time
from pathlib import Path

import polars as pl
from loguru import logger

from pipeline.concordance import (
    Concordance,
    build_concordance_polars_map,
    load_concordance,
    load_product_descriptions,
)
from pipeline.countries import CountryRecord, load_country_mapping


def ingest_baci_year(
    csv_path: Path,
    country_mapping: dict[int, CountryRecord],
    concordance_map: dict[str, str],
    descriptions: dict[str, tuple[str, str]],
) -> pl.DataFrame:
    """Ingest a single BACI CSV file using Polars lazy evaluation.

    Args:
        csv_path: Path to raw BACI CSV (columns: t, i, j, k, v, q).
        country_mapping: BACI numeric code → CountryRecord.
        concordance_map: Flat HS6 source → target mapping.
        descriptions: HS6 → (description, category).

    Returns:
        Polars DataFrame with enriched columns.
    """
    # Build lookup functions
    def _resolve_iso3(baci_code: int) -> str:
        record = country_mapping.get(baci_code)
        return record.iso3 if record else "UNK"

    def _get_description(hs6: str) -> str:
        info = descriptions.get(hs6)
        return info[0] if info else "Unknown product"

    def _get_category(hs6: str) -> str:
        info = descriptions.get(hs6)
        return info[1] if info else "unknown"

    # Read CSV lazily
    lf = pl.scan_csv(csv_path, infer_schema_length=10000)

    df = (
        lf
        .rename({"t": "year", "i": "exporter_baci", "j": "importer_baci", "k": "hs6_original", "v": "value_usd", "q": "quantity_kg"})
        # Cast hs6 to string, zero-pad to 6 digits
        .with_columns(
            pl.col("hs6_original").cast(pl.Utf8).str.zfill(6).alias("hs6_original")
        )
        # Drop rows where value_usd is null (keep zeros)
        .filter(pl.col("value_usd").is_not_null())
        .collect()
    )

    # Apply country mapping (vectorized via map_elements)
    df = df.with_columns(
        pl.col("exporter_baci").map_elements(_resolve_iso3, return_dtype=pl.Utf8).alias("exporter_iso3"),
        pl.col("importer_baci").map_elements(_resolve_iso3, return_dtype=pl.Utf8).alias("importer_iso3"),
    )

    # Apply HS concordance
    if concordance_map:
        df = df.with_columns(
            pl.col("hs6_original").replace_strict(concordance_map, default=pl.col("hs6_original")).alias("concorded_hs6")
        )
    else:
        df = df.with_columns(
            pl.col("hs6_original").alias("concorded_hs6")
        )

    # Derive HS hierarchy
    df = df.with_columns(
        pl.col("concorded_hs6").str.slice(0, 2).alias("hs2"),
        pl.col("concorded_hs6").str.slice(0, 4).alias("hs4"),
    )

    # Map descriptions and categories
    df = df.with_columns(
        pl.col("concorded_hs6").map_elements(_get_description, return_dtype=pl.Utf8).alias("product_description"),
        pl.col("concorded_hs6").map_elements(_get_category, return_dtype=pl.Utf8).alias("category"),
    )

    # Concordance flag
    df = df.with_columns(
        pl.when(pl.col("hs6_original") != pl.col("concorded_hs6"))
        .then(pl.lit("mapped"))
        .otherwise(pl.lit("unchanged"))
        .alias("concordance_flag")
    )

    # Compute unit value ($/kg) — null if quantity is 0 or null
    df = df.with_columns(
        pl.when(pl.col("quantity_kg").is_not_null() & (pl.col("quantity_kg") > 0))
        .then(pl.col("value_usd") / pl.col("quantity_kg"))
        .otherwise(None)
        .alias("unit_value")
    )

    # Outlier flag: value_usd > mean + 3*std within each concorded_hs6 group
    df = df.with_columns(
        (
            pl.col("value_usd")
            > (pl.col("value_usd").mean().over("concorded_hs6") + 3 * pl.col("value_usd").std().over("concorded_hs6"))
        ).alias("outlier_flag")
    )

    return df


def run_ingestion(config: dict) -> dict:
    """Process all BACI CSVs in raw_dir → Parquet in processed_dir.

    Returns summary dict with processing stats.
    """
    raw_dir = Path(config["baci"]["raw_dir"])
    processed_dir = Path(config["processing"]["processed_dir"])
    reference_dir = Path(config["processing"]["reference_dir"])

    processed_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    # Load reference data
    country_mapping = load_country_mapping(reference_dir, raw_dir=raw_dir)
    concordance = load_concordance(reference_dir)
    concordance_map = build_concordance_polars_map(concordance)
    descriptions = load_product_descriptions(reference_dir, raw_dir=raw_dir)

    # Find all CSVs in raw_dir — HS22 processed first to enable overlap-year skipping
    csv_files = sorted(
        raw_dir.glob("*.csv"),
        key=lambda p: (0 if re.search(r"BACI_HS22_", p.name, re.IGNORECASE) else 1, p.name),
    )
    if not csv_files:
        logger.warning(f"No CSV files found in {raw_dir}")
        return {"years_processed": [], "years_skipped": [], "total_rows": 0, "duration_seconds": 0}

    years_processed = []
    years_skipped = []
    total_rows = 0
    hs22_years: set[int] = set()  # years already covered by HS22 data

    for csv_path in csv_files:
        # Skip non-trade mapping files bundled in raw_dir
        if csv_path.name.startswith(("country_codes", "product_codes")):
            continue

        # Extract year from first data row
        try:
            sample = pl.read_csv(csv_path, n_rows=1)
            if "t" in sample.columns:
                year = int(sample["t"][0])
            else:
                logger.warning(f"No 't' column in {csv_path.name}, skipping")
                continue
        except Exception as e:
            logger.warning(f"Could not read {csv_path.name}: {e}")
            continue

        # Check if already processed (incremental)
        parquet_dir = processed_dir / f"year={year}"
        parquet_path = parquet_dir / "data.parquet"
        if parquet_path.exists():
            # Skip if parquet is newer than CSV
            if parquet_path.stat().st_mtime >= csv_path.stat().st_mtime:
                logger.info(f"Skipping year {year} — already processed")
                years_skipped.append(year)
                continue

        # Detect HS revision from filename
        hs_rev_match = re.search(r"BACI_(HS\d+)_", csv_path.name, re.IGNORECASE)
        hs_revision = hs_rev_match.group(1).upper() if hs_rev_match else "HS92"

        # HS22 wins for 2022-2024: skip non-HS22 if HS22 already processed this year
        if year in {2022, 2023, 2024} and hs_revision != "HS22" and year in hs22_years:
            logger.info(f"Skipping {csv_path.name} — HS22 already covers year {year}")
            years_skipped.append(year)
            continue

        logger.info(f"Ingesting year {year} from {csv_path.name}")
        year_start = time.time()

        df = ingest_baci_year(csv_path, country_mapping, concordance_map, descriptions)
        row_count = len(df)
        total_rows += row_count

        # Write Parquet
        parquet_dir.mkdir(parents=True, exist_ok=True)
        df.write_parquet(parquet_path, compression="zstd")

        elapsed = time.time() - year_start
        logger.info(f"Year {year}: {row_count:,} rows in {elapsed:.1f}s → {parquet_path}")
        years_processed.append(year)

        if hs_revision == "HS22" and year in {2022, 2023, 2024}:
            hs22_years.add(year)

    duration = time.time() - start_time
    logger.info(f"Ingestion complete: {len(years_processed)} years, {total_rows:,} rows in {duration:.1f}s")

    return {
        "years_processed": years_processed,
        "years_skipped": years_skipped,
        "total_rows": total_rows,
        "duration_seconds": round(duration, 2),
    }
