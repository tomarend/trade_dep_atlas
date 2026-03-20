"""Tests for HHI concentration scoring module."""

from pathlib import Path

import polars as pl
import pytest

from pipeline.hhi import compute_hhi, run_hhi_scoring


def _make_rows(importer, hs6, year, suppliers: list[tuple[str, float]]) -> list[dict]:
    """Build synthetic rows: [(exporter_iso3, value_usd), ...]"""
    return [
        {"importer_iso3": importer, "concorded_hs6": hs6, "year": year,
         "exporter_iso3": exp, "value_usd": val}
        for exp, val in suppliers
    ]


def test_hhi_monopoly():
    df = pl.DataFrame(_make_rows("DEU", "260111", 2022, [("CHN", 1000.0)]))
    result = compute_hhi(df)
    assert result["hhi"][0] == pytest.approx(1.0, abs=1e-9)


def test_hhi_equal_four_suppliers():
    suppliers = [("CHN", 250.0), ("AUS", 250.0), ("ZAF", 250.0), ("BRA", 250.0)]
    df = pl.DataFrame(_make_rows("DEU", "260111", 2022, suppliers))
    result = compute_hhi(df)
    assert result["hhi"][0] == pytest.approx(0.25, abs=1e-9)


def test_hhi_duopoly_dominant():
    # 80% + 20%: HHI = 0.64 + 0.04 = 0.68
    df = pl.DataFrame(_make_rows("DEU", "260111", 2022, [("CHN", 800.0), ("AUS", 200.0)]))
    result = compute_hhi(df)
    assert result["hhi"][0] == pytest.approx(0.68, abs=1e-9)


def test_hhi_output_columns():
    df = pl.DataFrame(_make_rows("DEU", "260111", 2022, [("CHN", 600.0), ("AUS", 400.0)]))
    result = compute_hhi(df)
    expected = {"importer_iso3", "exporter_iso3", "concorded_hs6", "year",
                "value_usd", "supplier_share", "hhi", "supplier_count"}
    assert expected.issubset(set(result.columns))


def test_hhi_share_sums_to_one():
    suppliers = [("CHN", 300.0), ("AUS", 200.0), ("ZAF", 100.0)]
    df = pl.DataFrame(_make_rows("DEU", "260111", 2022, suppliers))
    result = compute_hhi(df)
    total_share = result["supplier_share"].sum()
    assert total_share == pytest.approx(1.0, abs=1e-6)


def test_hhi_isolates_groups():
    rows = (
        _make_rows("DEU", "260111", 2022, [("CHN", 1000.0)])  # monopoly → HHI=1.0
        + _make_rows("FRA", "260111", 2022, [("CHN", 500.0), ("AUS", 500.0)])  # equal → HHI=0.5
    )
    result = compute_hhi(pl.DataFrame(rows))
    deu = result.filter(pl.col("importer_iso3") == "DEU")["hhi"][0]
    fra = result.filter(pl.col("importer_iso3") == "FRA")["hhi"][0]
    assert deu == pytest.approx(1.0, abs=1e-9)
    assert fra == pytest.approx(0.5, abs=1e-9)


def test_hhi_filters_zero_value():
    rows = _make_rows("DEU", "260111", 2022, [("CHN", 1000.0), ("AUS", 0.0)])
    result = compute_hhi(pl.DataFrame(rows))
    # AUS filtered → only CHN remains → monopoly
    assert len(result) == 1
    assert result["hhi"][0] == pytest.approx(1.0, abs=1e-9)
    assert result["supplier_count"][0] == 1


def test_hhi_supplier_count():
    suppliers = [("CHN", 300.0), ("AUS", 200.0), ("ZAF", 100.0)]
    df = pl.DataFrame(_make_rows("DEU", "260111", 2022, suppliers))
    result = compute_hhi(df)
    assert result["supplier_count"].unique()[0] == 3


def test_run_hhi_scoring_writes_parquet(tmp_path):
    """Integration: run_hhi_scoring writes data/scoring/hhi/year=YYYY/data.parquet."""
    # Set up synthetic processed Parquet
    year = 2020
    year_dir = tmp_path / "processed" / f"year={year}"
    year_dir.mkdir(parents=True)
    rows = _make_rows("DEU", "260111", year, [("CHN", 800.0), ("RUS", 200.0)])
    pl.DataFrame(rows).write_parquet(year_dir / "data.parquet")

    config = {
        "processing": {"processed_dir": str(tmp_path / "processed")},
        "scoring": {"output_dir": str(tmp_path / "scoring")},
    }
    result = run_hhi_scoring(config)

    assert year in result["years_processed"]
    out_path = tmp_path / "scoring" / "hhi" / f"year={year}" / "data.parquet"
    assert out_path.exists()

    df = pl.read_parquet(out_path)
    assert "hhi" in df.columns
    assert "supplier_share" in df.columns
    assert df["hhi"][0] == pytest.approx(0.68, abs=1e-9)
