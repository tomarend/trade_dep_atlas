"""Tests for product flag classification module (replaces test_essentiality.py)."""

from pathlib import Path

import polars as pl
import pytest
import yaml

from pipeline.flags import (
    classify_hs6,
    compute_global_export_hhi,
    compute_product_flags,
    load_crm_hs6_mapping,
    load_flags_config,
    run_flags_scoring,
)

# ── fixtures / helpers ────────────────────────────────────────────────────────

REFERENCE_DIR = Path("data/reference")


@pytest.fixture(scope="module")
def real_config() -> dict:
    return load_flags_config(REFERENCE_DIR)


@pytest.fixture(scope="module")
def real_crm_set() -> set:
    df = load_crm_hs6_mapping(REFERENCE_DIR)
    return set(df["hs6"].to_list())


def _make_parquet(tmp_path: Path, rows: list[dict], year: int = 2020) -> Path:
    """Write synthetic processed Parquet for a single year."""
    year_dir = tmp_path / f"year={year}"
    year_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(year_dir / "data.parquet")
    return tmp_path


# ── classify_hs6 tests ────────────────────────────────────────────────────────

def test_classify_crm_hs6(real_config, real_crm_set):
    """HS 280530 (rare earth metals) → contains crm_listed flag."""
    flags = classify_hs6("280530", real_config, real_crm_set)
    assert "crm_listed" in flags


def test_classify_energy_hs2_27(real_config, real_crm_set):
    """HS 270900 (crude oil, HS2=27) → contains energy flag."""
    flags = classify_hs6("270900", real_config, real_crm_set)
    assert "energy" in flags


def test_classify_energy_excludes_2716(real_config, real_crm_set):
    """HS 271600 (electric current) — HS4=2716 is excluded → NOT energy flagged."""
    flags = classify_hs6("271600", real_config, real_crm_set)
    assert "energy" not in flags


def test_classify_food_staples(real_config, real_crm_set):
    """HS 100190 (wheat, HS2=10) → contains food flag."""
    flags = classify_hs6("100190", real_config, real_crm_set)
    assert "food" in flags


def test_classify_consumer_goods_no_flags(real_config, real_crm_set):
    """HS 950300 (toys) → empty flags list (not in any category)."""
    flags = classify_hs6("950300", real_config, real_crm_set)
    assert flags == []


def test_classify_fertilizer(real_config, real_crm_set):
    """HS 310210 (ammonium nitrate, HS2=31) → contains fertilizer flag."""
    flags = classify_hs6("310210", real_config, real_crm_set)
    assert "fertilizer" in flags


def test_classify_pharma_hs2_29(real_config, real_crm_set):
    """HS 290300 (organic chemicals, HS2=29) → contains pharma flag."""
    flags = classify_hs6("290300", real_config, real_crm_set)
    assert "pharma" in flags


def test_classify_pharma_hs2_30(real_config, real_crm_set):
    """HS 300490 (mixed medicaments, HS2=30) → contains pharma flag."""
    flags = classify_hs6("300490", real_config, real_crm_set)
    assert "pharma" in flags


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


def test_compute_global_export_hhi_duopoly(tmp_path):
    """Two equal exporters → hhi = 0.5² + 0.5² = 0.5."""
    rows = [
        {"concorded_hs6": "260111", "exporter_iso3": "CHN", "value_usd": 500.0, "year": 2020},
        {"concorded_hs6": "260111", "exporter_iso3": "AUS", "value_usd": 500.0, "year": 2020},
    ]
    processed = _make_parquet(tmp_path, rows)
    result = compute_global_export_hhi(processed)
    hhi = result.filter(pl.col("concorded_hs6") == "260111")["global_export_hhi"][0]
    assert hhi == pytest.approx(0.5, abs=1e-9)


# ── integration tests ─────────────────────────────────────────────────────────

def test_run_flags_scoring_writes_parquet(tmp_path):
    """Integration: run_flags_scoring writes output with expected schema and flag values."""
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
        "baci": {"raw_dir": str(tmp_path / "raw")},
        "scoring": {"output_dir": str(tmp_path / "scoring")},
    }
    result_dict = run_flags_scoring(config)
    assert result_dict["products_scored"] == 3

    out_path = tmp_path / "scoring" / "flags" / "flags_scores.parquet"
    assert out_path.exists()

    df = pl.read_parquet(out_path)
    expected_cols = {"hs6", "flags", "global_export_hhi", "crm_listed_since", "hs22_only"}
    assert expected_cols.issubset(set(df.columns))

    # 280530 = CRM → should have crm_listed flag
    flags_280530 = df.filter(pl.col("hs6") == "280530")["flags"][0]
    assert "crm_listed" in flags_280530

    # 100190 = wheat (HS2=10 = food) → food flag
    flags_100190 = df.filter(pl.col("hs6") == "100190")["flags"][0]
    assert "food" in flags_100190

    # 950300 = toys → no special flags
    flags_950300 = df.filter(pl.col("hs6") == "950300")["flags"][0]
    assert list(flags_950300) == []


