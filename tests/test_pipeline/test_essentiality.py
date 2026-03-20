"""Tests for product essentiality classification and scoring module."""

from pathlib import Path

import polars as pl
import pytest
import yaml

from pipeline.essentiality import (
    _tier_score,
    classify_hs6,
    compute_essentiality_scores,
    compute_global_export_hhi,
    load_crm_hs6_mapping,
    run_essentiality_scoring,
)

# ── fixtures / helpers ────────────────────────────────────────────────────────

REFERENCE_DIR = Path("data/reference")


@pytest.fixture(scope="module")
def real_config() -> dict:
    return yaml.safe_load(open(REFERENCE_DIR / "essentiality_config.yaml"))


@pytest.fixture(scope="module")
def real_crm_set() -> set:
    df = load_crm_hs6_mapping(REFERENCE_DIR)
    return set(df["hs6"].to_list())


@pytest.fixture(scope="module")
def real_overrides_df() -> pl.DataFrame:
    from pipeline.essentiality import load_essentiality_overrides
    return load_essentiality_overrides(REFERENCE_DIR)


def _make_parquet(tmp_path: Path, rows: list[dict], year: int = 2020) -> Path:
    """Write synthetic processed Parquet for a single year."""
    year_dir = tmp_path / f"year={year}"
    year_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(year_dir / "data.parquet")
    return tmp_path


# ── _tier_score tests ─────────────────────────────────────────────────────────

def test_tier_score_critical_monopoly(real_config):
    """Critical tier + global_hhi=1.0 → score = 1.0"""
    assert _tier_score("critical", 1.0, real_config) == pytest.approx(1.0, abs=1e-6)


def test_tier_score_critical_competitive(real_config):
    """Critical tier + global_hhi=0.0 → score = 0.85"""
    assert _tier_score("critical", 0.0, real_config) == pytest.approx(0.85, abs=1e-6)


def test_tier_score_important_midpoint(real_config):
    """Important tier + global_hhi=0.5 → score = 0.45 + (0.7-0.45)*0.5 = 0.575"""
    assert _tier_score("important", 0.5, real_config) == pytest.approx(0.575, abs=1e-6)


def test_tier_score_standard_monopoly(real_config):
    """Standard tier + global_hhi=1.0 → score = 0.3"""
    assert _tier_score("standard", 1.0, real_config) == pytest.approx(0.3, abs=1e-6)


# ── classify_hs6 tests ────────────────────────────────────────────────────────

def test_classify_crm_hs6(real_config, real_crm_set, real_overrides_df):
    """HS 280530 (rare earth metals) → critical, critical_raw_materials"""
    tier, cat, _ = classify_hs6("280530", real_config, real_crm_set, real_overrides_df)
    assert tier == "critical"
    assert cat == "critical_raw_materials"


def test_classify_energy_hs2_27(real_config, real_crm_set, real_overrides_df):
    """HS 270900 (crude oil, HS2=27) → critical, Energy"""
    tier, cat, _ = classify_hs6("270900", real_config, real_crm_set, real_overrides_df)
    assert tier == "critical"
    assert cat == "Energy"


def test_classify_energy_excludes_2716(real_config, real_crm_set, real_overrides_df):
    """HS 271600 (electric current) — HS4=2716 is in hs4_exclude → NOT critical"""
    tier, cat, _ = classify_hs6("271600", real_config, real_crm_set, real_overrides_df)
    # Should NOT be critical (excluded from energy sector)
    assert tier != "critical"


def test_classify_food_staples(real_config, real_crm_set, real_overrides_df):
    """HS 100190 (wheat, HS2=10) → important, Food"""
    tier, cat, _ = classify_hs6("100190", real_config, real_crm_set, real_overrides_df)
    assert tier == "important"
    assert cat == "Food"


def test_classify_consumer_goods(real_config, real_crm_set, real_overrides_df):
    """HS 950300 (toys) → standard, other"""
    tier, cat, _ = classify_hs6("950300", real_config, real_crm_set, real_overrides_df)
    assert tier == "standard"
    assert cat == "other"


def test_classify_fertilizer(real_config, real_crm_set, real_overrides_df):
    """HS 310210 (ammonium nitrate fertilizer, HS4=3102) → critical, Fertilizers"""
    tier, cat, _ = classify_hs6("310210", real_config, real_crm_set, real_overrides_df)
    assert tier == "critical"
    assert cat == "Fertilizers"


def test_classify_pharma_api(real_config, real_crm_set, real_overrides_df):
    """HS 290300 (organic chemicals, HS2=29 = pharma APIs) → critical"""
    tier, cat, _ = classify_hs6("290300", real_config, real_crm_set, real_overrides_df)
    assert tier == "critical"
    assert cat == "Pharma APIs"


def test_classify_finished_pharma(real_config, real_crm_set, real_overrides_df):
    """HS 300490 (mixed medicaments, HS2=30) → important, Pharma"""
    tier, cat, _ = classify_hs6("300490", real_config, real_crm_set, real_overrides_df)
    assert tier == "important"
    assert cat == "Pharma"


# ── compute_global_export_hhi tests ──────────────────────────────────────────

def test_compute_global_export_hhi_monopoly(tmp_path):
    """One exporter has all exports → hhi=1.0 for that product."""
    rows = [
        {"concorded_hs6": "280530", "exporter_iso3": "CHN", "value_usd": 1000.0, "year": 2020},
    ]
    processed = _make_parquet(tmp_path, rows)
    result = compute_global_export_hhi(processed)
    hhi = result.filter(pl.col("concorded_hs6") == "280530")["global_export_hhi"][0]
    assert hhi == pytest.approx(1.0, abs=1e-9)


# ── integration tests ─────────────────────────────────────────────────────────

def test_run_essentiality_scoring_writes_parquet(tmp_path):
    """Integration: run_essentiality_scoring writes output with correct tier assignments."""
    # Write synthetic processed Parquet with 3 products
    rows = [
        {"concorded_hs6": "280530", "exporter_iso3": "CHN", "value_usd": 500.0, "year": 2020},
        {"concorded_hs6": "100190", "exporter_iso3": "RUS", "value_usd": 300.0, "year": 2020},
        {"concorded_hs6": "950300", "exporter_iso3": "CHN", "value_usd": 100.0, "year": 2020},
    ]
    processed_dir = tmp_path / "processed"
    _make_parquet(processed_dir, rows)

    config = {
        "processing": {
            "reference_dir": str(REFERENCE_DIR),
            "processed_dir": str(processed_dir),
        },
        "scoring": {"output_dir": str(tmp_path / "scoring")},
    }
    result_dict = run_essentiality_scoring(config)
    assert result_dict["products_scored"] == 3

    out_path = tmp_path / "scoring" / "essentiality" / "essentiality_scores.parquet"
    assert out_path.exists()

    df = pl.read_parquet(out_path)
    expected_cols = {"hs6", "category", "essentiality_tier", "essentiality_score", "global_export_hhi", "crm_listed_since"}
    assert expected_cols.issubset(set(df.columns))

    # 280530 = CRM → critical
    assert df.filter(pl.col("hs6") == "280530")["essentiality_tier"][0] == "critical"
    # 100190 = wheat (HS2=10) → important
    assert df.filter(pl.col("hs6") == "100190")["essentiality_tier"][0] == "important"
    # 950300 = toys → standard
    assert df.filter(pl.col("hs6") == "950300")["essentiality_tier"][0] == "standard"


def test_tier_distribution_sanity(tmp_path):
    """Standard tier should have more products than critical tier in a realistic dataset."""
    # Create a mix of products with mostly unclassified (standard) HS6 codes
    rows = [
        {"concorded_hs6": f"9503{i:02d}", "exporter_iso3": "CHN", "value_usd": 100.0, "year": 2020}
        for i in range(10)   # 10 standard products (HS2=95 = toys)
    ] + [
        {"concorded_hs6": "280530", "exporter_iso3": "CHN", "value_usd": 500.0, "year": 2020},  # critical
    ]
    processed_dir = tmp_path / "processed"
    _make_parquet(processed_dir, rows)

    config = {
        "processing": {
            "reference_dir": str(REFERENCE_DIR),
            "processed_dir": str(processed_dir),
        },
        "scoring": {"output_dir": str(tmp_path / "scoring")},
    }
    result_dict = run_essentiality_scoring(config)
    tier_dist = result_dict["tier_distribution"]

    # More standard products than critical in this synthetic set
    assert tier_dist.get("standard", 0) > tier_dist.get("critical", 0)
