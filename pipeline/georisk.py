"""Geopolitical risk scoring module.

Computes geo_risk ∈ [0, 1] per (country, year) as:
    geo_risk = min(1.0, governance_risk × (1 + sanctions_intensity))

where:
    governance_risk = (2.5 - mean(va, ps, ge, rq, rl, cc)) / 5.0, clamped [0, 1]
        Source: World Bank WGI (6 dimensions, higher WGI = better governance = lower risk)
    sanctions_intensity = active_sanctions_count / 10.0, clamped [0, 1]
        Source: GSDB bilateral sanctions episodes; normalizer=10 (heuristic: 10+ active = max)

Fallback for territories missing from WGI (Taiwan/TWN, Kosovo/XKX, Palestine/PSE):
    governance_risk = 1 - (fh_score / 100.0)   Source: Freedom House (higher score = freer)

Reference data files in data/reference/governance/:
    wgi.csv                    — columns: iso3, year, va, ps, ge, rq, rl, cc
    freedom_house_fallback.csv — columns: iso3, year, fh_score
    gsdb_sanctions.csv         — columns: sender_iso3, target_iso3, start_year, end_year
"""

import urllib.request
import json
from pathlib import Path

import polars as pl
from loguru import logger

_WGI_COLS = ["va", "ps", "ge", "rq", "rl", "cc"]
_WGI_MIN = -2.5
_WGI_MAX = 2.5
_WGI_RANGE = _WGI_MAX - _WGI_MIN   # 5.0
_SANCTIONS_NORMALIZER = 10.0        # 10+ active sanctions → intensity = 1.0


def _download_wgi(out_path: Path) -> None:
    """Fetch WGI data from World Bank API and write to out_path as wgi.csv.

    Uses the World Bank Indicators REST API v2:
      https://api.worldbank.org/v2/country/all/indicator/{id}?format=json&per_page=20000

    The six WGI indicator codes:
      PV.EST  — Political Stability
      GE.EST  — Government Effectiveness
      RQ.EST  — Regulatory Quality
      RL.EST  — Rule of Law
      CC.EST  — Control of Corruption
      VA.EST  — Voice and Accountability
    """
    indicators = {
        "va": "VA.EST",
        "ps": "PV.EST",
        "ge": "GE.EST",
        "rq": "RQ.EST",
        "rl": "RL.EST",
        "cc": "CC.EST",
    }
    base = "https://api.worldbank.org/v2/country/all/indicator"
    records: dict[tuple[str, int], dict] = {}

    for col, indicator_id in indicators.items():
        url = f"{base}/{indicator_id}?format=json&per_page=20000&mrv=30"
        logger.info(f"WGI download: fetching {indicator_id} from World Bank API...")
        with urllib.request.urlopen(url, timeout=60) as resp:
            payload = json.loads(resp.read().decode())

        if len(payload) < 2:
            raise RuntimeError(f"Unexpected WGI API response for {indicator_id}: {payload}")

        for entry in payload[1]:
            iso3 = entry.get("countryiso3code", "")
            year_str = entry.get("date", "")
            value = entry.get("value")
            if not iso3 or len(iso3) != 3 or not year_str.isdigit() or value is None:
                continue
            key = (iso3, int(year_str))
            if key not in records:
                records[key] = {"iso3": iso3, "year": int(year_str)}
            records[key][col] = float(value)

    if not records:
        raise RuntimeError("WGI API returned no usable rows")

    rows = list(records.values())
    df = pl.DataFrame(rows, infer_schema_length=len(rows)).select(
        ["iso3", "year"] + _WGI_COLS
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out_path)
    logger.info(f"WGI download complete: {len(df)} rows written to {out_path}")


def load_wgi(governance_dir: Path) -> pl.DataFrame:
    """Load WGI CSV, auto-downloading from World Bank API if not present."""
    wgi_path = governance_dir / "wgi.csv"
    if not wgi_path.exists():
        logger.info("wgi.csv not found — auto-downloading from World Bank API...")
        _download_wgi(wgi_path)
    df = pl.read_csv(wgi_path, null_values=["", "NA", "#N/A"])
    required = {"iso3", "year"} | set(_WGI_COLS)
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"wgi.csv missing columns: {missing}")
    return df.select(["iso3", "year"] + _WGI_COLS)


def load_freedom_house_fallback(governance_dir: Path) -> pl.DataFrame:
    """Load Freedom House fallback CSV for territories missing from WGI."""
    fh_path = governance_dir / "freedom_house_fallback.csv"
    if not fh_path.exists():
        logger.warning(
            f"Freedom House fallback not found at {fh_path} "
            "— TWN/XKX/PSE will have no geo-risk scores"
        )
        return pl.DataFrame(schema={"iso3": pl.Utf8, "year": pl.Int64, "fh_score": pl.Float64})
    return pl.read_csv(fh_path, null_values=["", "NA"])


def load_sanctions(governance_dir: Path) -> pl.DataFrame:
    """Load GSDB bilateral sanctions episodes CSV."""
    sanctions_path = governance_dir / "gsdb_sanctions.csv"
    if not sanctions_path.exists():
        logger.warning(
            f"Sanctions file not found at {sanctions_path} "
            "— sanctions_intensity will be 0 for all countries"
        )
        return pl.DataFrame(schema={
            "sender_iso3": pl.Utf8, "target_iso3": pl.Utf8,
            "start_year": pl.Int64, "end_year": pl.Int64,
        })
    return pl.read_csv(sanctions_path, null_values=["", "NA"]).with_columns(
        pl.col("end_year").cast(pl.Int64, strict=False)
    )


def compute_governance_risk(
    wgi_df: pl.DataFrame, fh_fallback_df: pl.DataFrame
) -> pl.DataFrame:
    """Compute governance_risk ∈ [0,1] per (iso3, year).

    WGI path:  governance_risk = (2.5 - mean(va,ps,ge,rq,rl,cc)) / 5.0, clamped [0,1]
    FH path:   governance_risk = 1 - (fh_score / 100), then filled into WGI gaps.
    """
    # WGI-based governance risk
    wgi_risk = (
        wgi_df
        .with_columns(
            pl.mean_horizontal(_WGI_COLS).alias("_wgi_mean")
        )
        .with_columns(
            ((2.5 - pl.col("_wgi_mean")) / _WGI_RANGE)
            .clip(0.0, 1.0)
            .alias("governance_risk")
        )
        .select(["iso3", "year", "governance_risk"])
        .drop_nulls(["governance_risk"])
    )

    if fh_fallback_df.is_empty():
        return wgi_risk

    # Freedom House fallback for WGI-missing territories
    fh_risk = fh_fallback_df.with_columns(
        (1.0 - pl.col("fh_score") / 100.0).clip(0.0, 1.0).alias("governance_risk")
    ).select(["iso3", "year", "governance_risk"])

    # WGI takes precedence; FH fills missing (iso3, year) combos
    wgi_iso3_years = set(zip(wgi_risk["iso3"].to_list(), wgi_risk["year"].to_list()))
    fh_new = fh_risk.filter(
        ~(pl.struct(["iso3", "year"]).is_in(
            [{"iso3": r[0], "year": r[1]} for r in wgi_iso3_years]
        ))
    )
    return pl.concat([wgi_risk, fh_new])


def compute_sanctions_intensity(
    sanctions_df: pl.DataFrame, years: list[int]
) -> pl.DataFrame:
    """Compute sanctions_intensity ∈ [0,1] per (target_iso3, year).

    Active sanction: start_year <= year AND (end_year >= year OR end_year is null).
    Intensity = active_sanctions_count / _SANCTIONS_NORMALIZER, clamped [0, 1].
    """
    if sanctions_df.is_empty() or not years:
        return pl.DataFrame(
            schema={"iso3": pl.Utf8, "year": pl.Int64, "sanctions_intensity": pl.Float64}
        )

    rows = []
    for year in years:
        active = sanctions_df.filter(
            (pl.col("start_year") <= year)
            & ((pl.col("end_year") >= year) | pl.col("end_year").is_null())
        )
        counts = (
            active.group_by("target_iso3")
            .agg(pl.len().alias("active_count"))
            .with_columns(
                pl.lit(year).cast(pl.Int64).alias("year"),
                (pl.col("active_count") / _SANCTIONS_NORMALIZER)
                .clip(0.0, 1.0)
                .alias("sanctions_intensity"),
            )
            .rename({"target_iso3": "iso3"})
            .select(["iso3", "year", "sanctions_intensity"])
        )
        rows.append(counts)

    return pl.concat(rows) if rows else pl.DataFrame(
        schema={"iso3": pl.Utf8, "year": pl.Int64, "sanctions_intensity": pl.Float64}
    )


def compute_geo_risk(
    governance_df: pl.DataFrame, sanctions_intensity_df: pl.DataFrame
) -> pl.DataFrame:
    """Combine governance_risk and sanctions_intensity into geo_risk.

    geo_risk = min(1.0, governance_risk × (1 + sanctions_intensity))
    Countries with no sanctions data get sanctions_intensity = 0.
    """
    result = governance_df.join(
        sanctions_intensity_df, on=["iso3", "year"], how="left"
    ).with_columns(
        pl.col("sanctions_intensity").fill_null(0.0)
    ).with_columns(
        (pl.col("governance_risk") * (1.0 + pl.col("sanctions_intensity")))
        .clip(0.0, 1.0)
        .alias("geo_risk")
    )
    return result.select(
        ["iso3", "year", "governance_risk", "sanctions_intensity", "geo_risk"]
    )


def run_georisk_scoring(config: dict) -> dict:
    """Orchestrate geo-risk scoring: load reference data → compute → write Parquet.

    Reads from data/reference/governance/{wgi.csv, freedom_house_fallback.csv, gsdb_sanctions.csv}.
    Writes to data/scoring/georisk/georisk_by_country_year.parquet.
    Returns dict with countries_scored (int), years_covered (list[int]).
    """
    reference_dir = Path(config["processing"]["reference_dir"])
    scoring_dir = Path(config.get("scoring", {}).get("output_dir", "data/scoring"))
    governance_dir = reference_dir / "governance"
    out_path = scoring_dir / "georisk" / "georisk_by_country_year.parquet"

    logger.info("Geo-risk: loading WGI governance data...")
    wgi_df = load_wgi(governance_dir)
    fh_df = load_freedom_house_fallback(governance_dir)
    sanctions_df = load_sanctions(governance_dir)

    logger.info("Geo-risk: computing governance risk...")
    governance_risk_df = compute_governance_risk(wgi_df, fh_df)

    years = sorted(governance_risk_df["year"].unique().to_list())
    logger.info(f"Geo-risk: computing sanctions intensity for {len(years)} years...")
    sanctions_intensity_df = compute_sanctions_intensity(sanctions_df, years)

    logger.info("Geo-risk: combining into geo_risk scores...")
    result = compute_geo_risk(governance_risk_df, sanctions_intensity_df)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(out_path, compression="zstd")

    countries = result["iso3"].n_unique()
    logger.info(
        f"Geo-risk scoring complete: {countries} countries, {len(years)} years → {out_path}"
    )
    return {"countries_scored": countries, "years_covered": years}
