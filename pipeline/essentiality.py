"""Product essentiality classification and scoring module.

Classifies every HS6 product into:
  - Critical (0.85–1.0): EU CRM, USGS critical minerals, energy, fertilizers, pharma APIs, semiconductor materials
  - Important (0.45–0.7): food staples (HS01-24), finished pharma (HS30), industrial chemicals (HS28)
  - Standard (0.1–0.3): everything else

Within-tier score gradient:
    score = tier_min + (tier_max - tier_min) × global_export_hhi
    global_export_hhi = HHI of worldwide exports of this product across all importers/years
    More concentrated global supply → higher score within tier

Classification is static (today's assessment applied to all years).
crm_listed_since: integer year when each material first appeared on EU CRM or USGS list.
"""

from pathlib import Path

import polars as pl
import yaml
from loguru import logger


def load_essentiality_config(reference_dir: Path) -> dict:
    """Load essentiality tier configuration from YAML."""
    config_path = reference_dir / "essentiality_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Essentiality config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_crm_hs6_mapping(reference_dir: Path) -> pl.DataFrame:
    """Load CRM material → HS6 mapping (EU CRM 2023 + USGS 2022)."""
    crm_path = reference_dir / "crm_hs6_mapping.csv"
    if not crm_path.exists():
        logger.warning(
            f"CRM HS6 mapping not found at {crm_path} "
            "— no CRM products will be classified as critical"
        )
        return pl.DataFrame(
            schema={"material": pl.Utf8, "hs6": pl.Utf8, "crm_listed_since": pl.Int64, "source": pl.Utf8}
        )
    return pl.read_csv(crm_path, null_values=["", "NA"]).with_columns(
        pl.col("hs6").cast(pl.Utf8),
        pl.col("crm_listed_since").cast(pl.Int64, strict=False),
    )


def load_essentiality_overrides(reference_dir: Path) -> pl.DataFrame:
    """Load explicit per-HS6 tier overrides."""
    overrides_path = reference_dir / "essentiality_hs6.csv"
    if not overrides_path.exists():
        return pl.DataFrame(
            schema={
                "hs6": pl.Utf8, "category": pl.Utf8,
                "essentiality_tier": pl.Utf8, "crm_listed_since": pl.Int64,
            }
        )
    return pl.read_csv(overrides_path, null_values=["", "NA"]).with_columns(
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


def _tier_score(tier: str, global_hhi: float, config: dict) -> float:
    """Compute final score using within-tier gradient."""
    ranges = {
        "critical":  config["tiers"]["critical"]["score_range"],
        "important": config["tiers"]["important"]["score_range"],
        "standard":  config["tiers"]["standard"]["score_range"],
    }
    lo, hi = ranges.get(tier, [0.1, 0.3])
    return round(lo + (hi - lo) * global_hhi, 6)


def classify_hs6(
    hs6: str,
    config: dict,
    crm_hs6_set: set,
    override_df: pl.DataFrame | None = None,
) -> tuple:
    """Classify a single HS6 code into (tier, category, crm_listed_since_str | None).

    Classification priority (highest tier wins):
    1. CRM mapping (critical)
    2. essentiality_hs6.csv overrides
    3. YAML sector rules (critical → important → standard)
    """
    hs2 = hs6[:2]
    hs4 = hs6[:4]

    # 1. CRM check (always critical)
    if hs6 in crm_hs6_set:
        crm_since = None
        if override_df is not None and not override_df.is_empty():
            row = override_df.filter(pl.col("hs6") == hs6)
            if not row.is_empty() and row["crm_listed_since"][0] is not None:
                crm_since = str(row["crm_listed_since"][0])
        return ("critical", "critical_raw_materials", crm_since)

    # 2. essentiality_hs6.csv override
    if override_df is not None and not override_df.is_empty():
        row = override_df.filter(pl.col("hs6") == hs6)
        if not row.is_empty():
            tier = row["essentiality_tier"][0] or "standard"
            cat = row["category"][0] or "other"
            crm_since = str(row["crm_listed_since"][0]) if row["crm_listed_since"][0] is not None else None
            return (tier, cat, crm_since)

    # 3. YAML sector rules — critical tier first
    critical_cfg = config["tiers"]["critical"]
    for sector in critical_cfg["sectors"]:
        if sector["name"] == "critical_raw_materials":
            continue  # handled via CRM set above
        hs2_inc = sector.get("hs2_include", [])
        hs4_inc = sector.get("hs4_include", [])
        hs6_inc = sector.get("hs6_include", [])
        hs4_exc = sector.get("hs4_exclude", [])
        if hs6 in hs6_inc:
            return ("critical", sector.get("label", sector["name"]), None)
        if hs4 in hs4_inc and hs4 not in hs4_exc:
            return ("critical", sector.get("label", sector["name"]), None)
        if hs2 in hs2_inc and hs4 not in hs4_exc:
            return ("critical", sector.get("label", sector["name"]), None)

    # important tier
    important_cfg = config["tiers"]["important"]
    for sector in important_cfg["sectors"]:
        hs2_inc = sector.get("hs2_include", [])
        if hs2 in hs2_inc:
            return ("important", sector.get("label", sector["name"]), None)

    return ("standard", "other", None)


def compute_essentiality_scores(
    config: dict, reference_dir: Path, processed_dir: Path
) -> pl.DataFrame:
    """Classify all HS6 products and assign essentiality scores.

    Reads all unique HS6 codes from Phase 1 Parquet.
    Returns DataFrame: [hs6, category, essentiality_tier, essentiality_score, global_export_hhi, crm_listed_since]
    """
    # Load reference data
    crm_df = load_crm_hs6_mapping(reference_dir)
    overrides_df = load_essentiality_overrides(reference_dir)
    crm_hs6_set = set(crm_df["hs6"].to_list()) if not crm_df.is_empty() else set()

    # Get all unique HS6 codes from processed Parquet
    year_paths = list(processed_dir.glob("year=*/data.parquet"))
    if not year_paths:
        logger.warning("No processed Parquet found — cannot compute essentiality scores")
        return pl.DataFrame(schema={
            "hs6": pl.Utf8, "category": pl.Utf8, "essentiality_tier": pl.Utf8,
            "essentiality_score": pl.Float64, "global_export_hhi": pl.Float64,
            "crm_listed_since": pl.Int64,
        })

    all_hs6 = (
        pl.scan_parquet(str(processed_dir / "year=*" / "data.parquet"))
        .select("concorded_hs6")
        .unique()
        .collect()["concorded_hs6"]
        .to_list()
    )

    # Compute global HHI per product
    logger.info(f"Essentiality: computing global export HHI for {len(all_hs6):,} HS6 products...")
    global_hhi_df = compute_global_export_hhi(processed_dir)
    hhi_lookup = dict(
        zip(global_hhi_df["concorded_hs6"].to_list(), global_hhi_df["global_export_hhi"].to_list())
    )

    # Classify each HS6 and compute score
    rows = []
    for hs6 in all_hs6:
        tier, category, crm_since = classify_hs6(hs6, config, crm_hs6_set, overrides_df)
        global_hhi = hhi_lookup.get(hs6, 0.0)
        score = _tier_score(tier, global_hhi, config)
        rows.append({
            "hs6": hs6,
            "category": category,
            "essentiality_tier": tier,
            "essentiality_score": score,
            "global_export_hhi": global_hhi,
            "crm_listed_since": int(crm_since) if crm_since else None,
        })

    return pl.DataFrame(rows).with_columns(
        pl.col("crm_listed_since").cast(pl.Int64, strict=False)
    )


def run_essentiality_scoring(config: dict) -> dict:
    """Orchestrate essentiality scoring: classify → score → write Parquet."""
    reference_dir = Path(config["processing"]["reference_dir"])
    processed_dir = Path(config["processing"]["processed_dir"])
    scoring_dir = Path(config.get("scoring", {}).get("output_dir", "data/scoring"))
    out_path = scoring_dir / "essentiality" / "essentiality_scores.parquet"

    logger.info("Essentiality: loading config and reference data...")
    ess_config = load_essentiality_config(reference_dir)

    logger.info("Essentiality: classifying HS6 products and computing scores...")
    result = compute_essentiality_scores(ess_config, reference_dir, processed_dir)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(out_path, compression="zstd")

    # Log tier distribution
    tier_counts = (
        result.group_by("essentiality_tier")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
    )
    for row in tier_counts.iter_rows(named=True):
        logger.info(f"  {row['essentiality_tier']}: {row['count']:,} products")
    logger.info(f"Essentiality scoring complete: {len(result):,} products → {out_path}")
    return {
        "products_scored": len(result),
        "tier_distribution": dict(
            zip(
                tier_counts["essentiality_tier"].to_list(),
                tier_counts["count"].to_list(),
            )
        ),
    }
