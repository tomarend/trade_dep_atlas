"""Tests for geopolitical risk scoring module."""

from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

from pipeline.georisk import (
    compute_geo_risk,
    compute_governance_risk,
    compute_sanctions_intensity,
    load_freedom_house_fallback,
    load_sanctions,
    load_wgi,
    run_georisk_scoring,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _wgi_df(rows: list[dict]) -> pl.DataFrame:
    schema = {
        "iso3": pl.Utf8, "year": pl.Int64,
        "va": pl.Float64, "ps": pl.Float64, "ge": pl.Float64,
        "rq": pl.Float64, "rl": pl.Float64, "cc": pl.Float64,
    }
    return pl.DataFrame(rows, schema=schema)


def _fh_df(rows: list[dict]) -> pl.DataFrame:
    schema = {"iso3": pl.Utf8, "year": pl.Int64, "fh_score": pl.Float64}
    return pl.DataFrame(rows, schema=schema)


def _sanctions_df(rows: list[dict]) -> pl.DataFrame:
    schema = {
        "sender_iso3": pl.Utf8, "target_iso3": pl.Utf8,
        "start_year": pl.Int64, "end_year": pl.Int64,
    }
    return pl.DataFrame(rows, schema=schema)


def _safe_country(iso3: str, year: int) -> dict:
    """WGI all = +2.0 → governance_risk = (2.5-2.0)/5.0 = 0.1"""
    return {"iso3": iso3, "year": year, "va": 2.0, "ps": 2.0, "ge": 2.0, "rq": 2.0, "rl": 2.0, "cc": 2.0}


def _risky_country(iso3: str, year: int) -> dict:
    """WGI all = -2.0 → governance_risk = (2.5+2.0)/5.0 = 0.9"""
    return {"iso3": iso3, "year": year, "va": -2.0, "ps": -2.0, "ge": -2.0, "rq": -2.0, "rl": -2.0, "cc": -2.0}


# ── governance risk tests ─────────────────────────────────────────────────────

def test_governance_risk_safe_country():
    wgi = _wgi_df([_safe_country("DEU", 2022)])
    result = compute_governance_risk(wgi, _fh_df([]))
    row = result.filter(pl.col("iso3") == "DEU")["governance_risk"][0]
    assert row == pytest.approx(0.1, abs=1e-9)


def test_governance_risk_risky_country():
    wgi = _wgi_df([_risky_country("SOM", 2022)])
    result = compute_governance_risk(wgi, _fh_df([]))
    row = result.filter(pl.col("iso3") == "SOM")["governance_risk"][0]
    assert row == pytest.approx(0.9, abs=1e-9)


def test_governance_risk_clamps():
    # WGI above +2.5 range → clamp to 0
    wgi = _wgi_df([{"iso3": "TEST", "year": 2022,
                    "va": 10.0, "ps": 10.0, "ge": 10.0, "rq": 10.0, "rl": 10.0, "cc": 10.0}])
    result = compute_governance_risk(wgi, _fh_df([]))
    row = result.filter(pl.col("iso3") == "TEST")["governance_risk"][0]
    assert row == pytest.approx(0.0, abs=1e-9)  # (2.5 - 10) / 5 = -1.5 → clamped to 0

    # WGI below -2.5 range → clamp to 1
    wgi2 = _wgi_df([{"iso3": "TEST2", "year": 2022,
                     "va": -10.0, "ps": -10.0, "ge": -10.0, "rq": -10.0, "rl": -10.0, "cc": -10.0}])
    result2 = compute_governance_risk(wgi2, _fh_df([]))
    row2 = result2.filter(pl.col("iso3") == "TEST2")["governance_risk"][0]
    assert row2 == pytest.approx(1.0, abs=1e-9)


def test_freedom_house_fallback_fills_gaps():
    """TWN not in WGI → gets FH-derived governance_risk = 1 - 94/100 = 0.06"""
    wgi = _wgi_df([_safe_country("DEU", 2022)])  # no TWN in WGI
    fh = _fh_df([{"iso3": "TWN", "year": 2022, "fh_score": 94.0}])
    result = compute_governance_risk(wgi, fh)
    twn = result.filter(pl.col("iso3") == "TWN")["governance_risk"][0]
    assert twn == pytest.approx(1.0 - 94.0 / 100.0, abs=1e-9)


def test_freedom_house_does_not_override_wgi():
    """Country in both WGI and FH → WGI value kept."""
    wgi = _wgi_df([_safe_country("DEU", 2022)])  # governance_risk = 0.1
    fh = _fh_df([{"iso3": "DEU", "year": 2022, "fh_score": 10.0}])  # would give 0.9 if applied
    result = compute_governance_risk(wgi, fh)
    deu_rows = result.filter(pl.col("iso3") == "DEU")
    assert len(deu_rows) == 1  # no duplicate
    assert deu_rows["governance_risk"][0] == pytest.approx(0.1, abs=1e-9)


# ── sanctions tests ───────────────────────────────────────────────────────────

def test_sanctions_active_sanction_counts():
    """start_year <= year AND end_year null → active."""
    sanctions = _sanctions_df([
        {"sender_iso3": "USA", "target_iso3": "IRN", "start_year": 1979, "end_year": None}
    ])
    result = compute_sanctions_intensity(sanctions, [2022])
    irn = result.filter(pl.col("iso3") == "IRN")["sanctions_intensity"][0]
    assert irn == pytest.approx(1 / 10.0, abs=1e-9)


def test_sanctions_ended_not_counted():
    """end_year < year → not active."""
    sanctions = _sanctions_df([
        {"sender_iso3": "USA", "target_iso3": "TGT", "start_year": 2000, "end_year": 2010}
    ])
    result = compute_sanctions_intensity(sanctions, [2022])
    # TGT not in result → 0 active sanctions
    if len(result.filter(pl.col("iso3") == "TGT")) > 0:
        assert result.filter(pl.col("iso3") == "TGT")["sanctions_intensity"][0] == 0.0
    # If not present, that's correct too (no active sanctions)


def test_sanctions_intensity_normalization():
    """10 active sanctions → intensity = 1.0; 5 → 0.5."""
    # Create 10 senders sanctioning same target
    rows = [
        {"sender_iso3": f"S{i:02d}", "target_iso3": "TGT", "start_year": 2000, "end_year": None}
        for i in range(10)
    ]
    sanctions = _sanctions_df(rows)
    result = compute_sanctions_intensity(sanctions, [2022])
    tgt = result.filter(pl.col("iso3") == "TGT")["sanctions_intensity"][0]
    assert tgt == pytest.approx(1.0, abs=1e-9)

    # 5 senders
    rows5 = rows[:5]
    result5 = compute_sanctions_intensity(_sanctions_df(rows5), [2022])
    tgt5 = result5.filter(pl.col("iso3") == "TGT")["sanctions_intensity"][0]
    assert tgt5 == pytest.approx(0.5, abs=1e-9)


# ── geo_risk formula tests ────────────────────────────────────────────────────

def test_geo_risk_formula():
    """governance_risk=0.5, sanctions_intensity=0.5 → geo_risk = min(1.0, 0.5×1.5) = 0.75"""
    gov = pl.DataFrame({"iso3": ["TGT"], "year": [2022], "governance_risk": [0.5]})
    si = pl.DataFrame({"iso3": ["TGT"], "year": [2022], "sanctions_intensity": [0.5]})
    result = compute_geo_risk(gov, si)
    assert result["geo_risk"][0] == pytest.approx(0.75, abs=1e-9)


def test_geo_risk_clamps_to_one():
    """governance=1.0, sanctions=1.0 → geo_risk clamped to 1.0."""
    gov = pl.DataFrame({"iso3": ["TGT"], "year": [2022], "governance_risk": [1.0]})
    si = pl.DataFrame({"iso3": ["TGT"], "year": [2022], "sanctions_intensity": [1.0]})
    result = compute_geo_risk(gov, si)
    assert result["geo_risk"][0] == pytest.approx(1.0, abs=1e-9)


def test_geo_risk_no_sanctions():
    """sanctions_intensity=0 → geo_risk == governance_risk."""
    gov = pl.DataFrame({"iso3": ["TGT"], "year": [2022], "governance_risk": [0.6]})
    si = pl.DataFrame({"iso3": ["TGT"], "year": [2022], "sanctions_intensity": [0.0]})
    result = compute_geo_risk(gov, si)
    assert result["geo_risk"][0] == pytest.approx(0.6, abs=1e-9)


# ── integration tests ─────────────────────────────────────────────────────────

def test_run_georisk_scoring_missing_wgi_raises(tmp_path):
    """When wgi.csv is absent and auto-download fails, the error propagates."""
    (tmp_path / "governance").mkdir()
    (tmp_path / "processed").mkdir()
    config = {
        "processing": {
            "reference_dir": str(tmp_path),
            "processed_dir": str(tmp_path / "processed"),
        },
        "scoring": {"output_dir": str(tmp_path / "scoring")},
    }
    with patch("pipeline.georisk._download_wgi", side_effect=OSError("no network")):
        with pytest.raises(OSError, match="no network"):
            run_georisk_scoring(config)


def test_run_georisk_scoring_writes_parquet(tmp_path):
    """Integration test: run_georisk_scoring writes output Parquet with expected columns."""
    gov_dir = tmp_path / "governance"
    gov_dir.mkdir()

    # Write synthetic wgi.csv
    wgi_rows = [
        _safe_country("DEU", 2020),
        _safe_country("DEU", 2021),
        _risky_country("RUS", 2020),
        _risky_country("RUS", 2021),
    ]
    wgi_df = _wgi_df(wgi_rows)
    wgi_path = gov_dir / "wgi.csv"
    wgi_df.write_csv(str(wgi_path))

    # Write synthetic sanctions (RUS sanctioned by USA)
    sanctions_rows = [
        {"sender_iso3": "USA", "target_iso3": "RUS", "start_year": 2014, "end_year": None}
    ]
    _sanctions_df(sanctions_rows).write_csv(str(gov_dir / "gsdb_sanctions.csv"))

    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    config = {
        "processing": {
            "reference_dir": str(tmp_path),
            "processed_dir": str(processed_dir),
        },
        "scoring": {"output_dir": str(tmp_path / "scoring")},
    }
    result = run_georisk_scoring(config)

    assert result["countries_scored"] == 2
    assert sorted(result["years_covered"]) == [2020, 2021]

    out_path = tmp_path / "scoring" / "georisk" / "georisk_by_country_year.parquet"
    assert out_path.exists()

    df = pl.read_parquet(out_path)
    expected_cols = {"iso3", "year", "governance_risk", "sanctions_intensity", "geo_risk"}
    assert expected_cols.issubset(set(df.columns))

    # RUS should have higher geo_risk than DEU
    rus_2021 = df.filter((pl.col("iso3") == "RUS") & (pl.col("year") == 2021))["geo_risk"][0]
    deu_2021 = df.filter((pl.col("iso3") == "DEU") & (pl.col("year") == 2021))["geo_risk"][0]
    assert rus_2021 > deu_2021
