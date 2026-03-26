"""Product flag classification module.

Replaces essentiality.py. Each HS6 product gets a list of orthogonal categorical flags
instead of a tier score. global_export_hhi is the substitutability measure.

Output schema for flags_scores.parquet:
  hs6 (Utf8), flags (List(Utf8)), global_export_hhi (Float64),
  crm_listed_since (Int64, nullable), hs22_only (Boolean)
"""

import csv
from pathlib import Path

import polars as pl
import yaml
from loguru import logger


def load_flags_config(reference_dir: Path) -> dict:
    """Load product flag configuration from flags_config.yaml."""
    config_path = reference_dir / "flags_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Flags config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_crm_hs6_mapping(reference_dir: Path) -> pl.DataFrame:
    """Load CRM material → HS6 mapping (EU CRM 2023 + USGS 2022)."""
    crm_path = reference_dir / "crm_hs6_mapping.csv"
    if not crm_path.exists():
        logger.warning(
            f"CRM HS6 mapping not found at {crm_path} "
            "— no CRM products will be flagged as crm_listed"
        )
        return pl.DataFrame(
            schema={"material": pl.Utf8, "hs6": pl.Utf8, "crm_listed_since": pl.Int64, "source": pl.Utf8}
        )
    return pl.read_csv(crm_path, null_values=["", "NA"]).with_columns(
        pl.col("hs6").cast(pl.Utf8),
        pl.col("crm_listed_since").cast(pl.Int64, strict=False),
    )


def compute_global_export_hhi(processed_dir: Path) -> pl.DataFrame:
    """Compute HHI of global exports per HS6 product (across all importers and years).

    Treats the whole world as one importer: for each product, compute what fraction
    of total world exports comes from each exporter, then compute HHI.
    Aggregated over all years for a stable static measure.

    Returns DataFrame with columns: [concorded_hs6, global_export_hhi].
    """
    parquet_glob = str(processed_dir / "year=*" / "data.parquet")
    year_dirs = list(processed_dir.glob("year=*/data.parquet"))
    if not year_dirs:
        logger.warning(
            f"No processed Parquet found in {processed_dir} "
            "— global HHI will be 0 for all products"
        )
        return pl.DataFrame(
            schema={"concorded_hs6": pl.Utf8, "global_export_hhi": pl.Float64}
        )

    # Aggregate total exports per (hs6, exporter) across all years
    df = (
        pl.scan_parquet(parquet_glob)
        .filter(pl.col("value_usd") > 0)
        .group_by(["concorded_hs6", "exporter_iso3"])
        .agg(pl.col("value_usd").sum().alias("total_export_value"))
        .collect()
    )

    if df.is_empty():
        return pl.DataFrame(
            schema={"concorded_hs6": pl.Utf8, "global_export_hhi": pl.Float64}
        )

    # Compute global HHI per product
    global_hhi = (
        df
        .with_columns(
            pl.col("total_export_value").sum().over("concorded_hs6").alias("world_total")
        )
        .with_columns(
            (pl.col("total_export_value") / pl.col("world_total")).alias("exporter_share")
        )
        .with_columns(
            pl.col("exporter_share").pow(2).sum().over("concorded_hs6").alias("global_export_hhi")
        )
        .select(["concorded_hs6", "global_export_hhi"])
        .unique("concorded_hs6")
    )
    return global_hhi


def classify_hs6(hs6: str, flags_config: dict, crm_hs6_set: set) -> list[str]:
    """Classify a single HS6 code and return a list of matching flag names.

    Returns an empty list if no flags match.
    hs22_only is NOT set here — it is set in compute_product_flags from the product code diff.
    Rule evaluation: hs6_exclude/hs4_exclude take precedence over any include rule.
    """
    result_flags = []
    hs2 = hs6[:2]
    hs4 = hs6[:4]

    for flag_name, rules in flags_config.items():
        if rules.get("set_programmatically", False):
            continue  # skip crm_listed and hs22_only (handled separately)

        # Exclusions take precedence
        if hs6 in rules.get("hs6_exclude", []):
            continue
        if hs4 in rules.get("hs4_exclude", []):
            continue

        # Inclusions
        matched = False
        if hs6 in rules.get("hs6_include", []):
            matched = True
        elif hs4 in rules.get("hs4_include", []):
            matched = True
        elif hs2 in rules.get("hs2_include", []):
            matched = True

        if matched:
            result_flags.append(flag_name)

    # CRM is managed programmatically via crm_hs6_set
    if hs6 in crm_hs6_set:
        result_flags.append("crm_listed")

    return result_flags


def compute_product_flags(
    flags_config: dict,
    reference_dir: Path,
    processed_dir: Path,
    raw_dir: Path | None = None,
) -> pl.DataFrame:
    """Classify all HS6 products and return a DataFrame with flag lists.

    Output schema: hs6 (Utf8), flags (List(Utf8)), global_export_hhi (Float64),
                   crm_listed_since (Int64, nullable), hs22_only (Boolean)
    """
    # Load CRM reference data
    crm_df = load_crm_hs6_mapping(reference_dir)
    crm_hs6_set = set(crm_df["hs6"].to_list()) if not crm_df.is_empty() else set()
    crm_since_lookup: dict[str, int | None] = {}
    if not crm_df.is_empty():
        for row in crm_df.iter_rows(named=True):
            crm_since_lookup[row["hs6"]] = row["crm_listed_since"]

    # Get all unique HS6 codes from processed Parquet
    year_paths = list(processed_dir.glob("year=*/data.parquet"))
    if not year_paths:
        logger.warning("No processed Parquet found — cannot compute product flags")
        return pl.DataFrame(schema={
            "hs6": pl.Utf8,
            "flags": pl.List(pl.Utf8),
            "global_export_hhi": pl.Float64,
            "crm_listed_since": pl.Int64,
            "hs22_only": pl.Boolean,
        })

    all_hs6 = (
        pl.scan_parquet(str(processed_dir / "year=*" / "data.parquet"))
        .select("concorded_hs6")
        .unique()
        .collect()["concorded_hs6"]
        .to_list()
    )

    # Compute global HHI per product
    logger.info(f"Flags: computing global export HHI for {len(all_hs6):,} HS6 products...")
    global_hhi_df = compute_global_export_hhi(processed_dir)
    hhi_lookup = dict(
        zip(global_hhi_df["concorded_hs6"].to_list(), global_hhi_df["global_export_hhi"].to_list())
    )

    # Determine hs22_only set from product code CSV diff
    hs22_only_set: set[str] = set()
    if raw_dir is not None:
        hs22_files = sorted(raw_dir.glob("product_codes_HS22_V*.csv"))
        hs92_files = sorted(raw_dir.glob("product_codes_HS92_V*.csv"))

        def _load_codes(csv_path: Path) -> set[str]:
            codes: set[str] = set()
            with open(csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_code = row.get("code", row.get("product_code", "")).strip()
                    if raw_code:
                        codes.add(str(raw_code).zfill(6))
            return codes

        if hs22_files and hs92_files:
            hs22_only_set = _load_codes(hs22_files[-1]) - _load_codes(hs92_files[-1])
            logger.info(f"Flags: {len(hs22_only_set)} HS22-only product codes identified")

    # Build rows
    rows = []
    for hs6 in all_hs6:
        flags_list = classify_hs6(hs6, flags_config, crm_hs6_set)
        if hs6 in hs22_only_set:
            flags_list.append("hs22_only")
        rows.append({
            "hs6": hs6,
            "flags": flags_list,
            "global_export_hhi": hhi_lookup.get(hs6, 0.0),
            "crm_listed_since": crm_since_lookup.get(hs6, None),
            "hs22_only": hs6 in hs22_only_set,
        })

    return pl.DataFrame(
        rows,
        schema={
            "hs6": pl.Utf8,
            "flags": pl.List(pl.Utf8),
            "global_export_hhi": pl.Float64,
            "crm_listed_since": pl.Int64,
            "hs22_only": pl.Boolean,
        },
    )


def run_flags_scoring(config: dict) -> dict:
    """Orchestrate flag scoring: classify → write Parquet."""
    reference_dir = Path(config["processing"]["reference_dir"])
    processed_dir = Path(config["processing"]["processed_dir"])
    raw_dir = Path(config["baci"]["raw_dir"])
    scoring_dir = Path(config.get("scoring", {}).get("output_dir", "data/scoring"))
    out_path = scoring_dir / "flags" / "flags_scores.parquet"

    logger.info("Flags: loading config...")
    flags_config = load_flags_config(reference_dir)

    logger.info("Flags: classifying HS6 products...")
    result = compute_product_flags(flags_config, reference_dir, processed_dir, raw_dir)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(out_path, compression="zstd")

    # Log count of products per flag
    if not result.is_empty():
        exploded = result.select("hs6", "flags").explode("flags").drop_nulls()
        per_flag = exploded.group_by("flags").agg(pl.len().alias("n")).sort("flags")
        logger.info(f"Flag counts: {per_flag.to_dicts()}")

    logger.info(f"Flags scoring complete: {len(result):,} products → {out_path}")
    return {"products_scored": len(result), "output_path": str(out_path)}
