"""Tests for composite dependency score module."""

from pathlib import Path

import polars as pl
import pytest

from pipeline.composite import (
    DEFAULT_WEIGHTS,
    _ESSENTIALITY_FILL,
    _GEO_RISK_FILL,
    compute_composite,
)


# ── helper builders ───────────────────────────────────────────────────────────

def _hhi_df(rows: list[dict]) -> pl.DataFrame:
    schema = {
        "importer_iso3": pl.Utf8, "concorded_hs6": pl.Utf8, "year": pl.Int64,
        "exporter_iso3": pl.Utf8, "value_usd": pl.Float64, "supplier_share": pl.Float64,
        "hhi": pl.Float64, "supplier_count": pl.Int32,
    }
    return pl.DataFrame(rows, schema=schema)


def _georisk_df(rows: list[dict]) -> pl.DataFrame:
    schema = {
        "iso3": pl.Utf8, "year": pl.Int64,
        "governance_risk": pl.Float64, "sanctions_intensity": pl.Float64, "geo_risk": pl.Float64,
    }
    return pl.DataFrame(rows, schema=schema)


def _ess_df(rows: list[dict]) -> pl.DataFrame:
    schema = {
        "hs6": pl.Utf8, "category": pl.Utf8, "essentiality_tier": pl.Utf8,
        "essentiality_score": pl.Float64, "global_export_hhi": pl.Float64,
        "crm_listed_since": pl.Int64,
    }
    return pl.DataFrame(rows, schema=schema)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_composite_formula_basic():
    """Verify composite = w1*hhi + w2*basket_geo + w3*essentiality."""
    hhi = _hhi_df([{"importer_iso3": "DEU", "concorded_hs6": "260111", "year": 2022,
                    "exporter_iso3": "CHN", "value_usd": 1000.0, "supplier_share": 1.0,
                    "hhi": 1.0, "supplier_count": 1}])
    georisk = _georisk_df([{"iso3": "CHN", "year": 2022, "governance_risk": 0.6,
                             "sanctions_intensity": 0.0, "geo_risk": 0.6}])
    ess = _ess_df([{"hs6": "260111", "category": "critical_raw_materials", "essentiality_tier": "critical",
                    "essentiality_score": 0.9, "global_export_hhi": 0.5, "crm_listed_since": 2020}])

    result = compute_composite(hhi, georisk, ess)
    expected = DEFAULT_WEIGHTS["hhi"] * 1.0 + DEFAULT_WEIGHTS["geo_risk"] * 0.6 + DEFAULT_WEIGHTS["essentiality"] * 0.9
    assert result["composite_score"][0] == pytest.approx(expected, abs=1e-6)


def test_basket_geo_risk_is_share_weighted():
    """basket_geo_risk = sum(share * geo_risk) with two equal suppliers."""
    hhi = _hhi_df([
        {"importer_iso3": "DEU", "concorded_hs6": "260111", "year": 2022,
         "exporter_iso3": "CHN", "value_usd": 500.0, "supplier_share": 0.5, "hhi": 0.5, "supplier_count": 2},
        {"importer_iso3": "DEU", "concorded_hs6": "260111", "year": 2022,
         "exporter_iso3": "AUS", "value_usd": 500.0, "supplier_share": 0.5, "hhi": 0.5, "supplier_count": 2},
    ])
    georisk = _georisk_df([
        {"iso3": "CHN", "year": 2022, "governance_risk": 0.6, "sanctions_intensity": 0.0, "geo_risk": 0.8},
        {"iso3": "AUS", "year": 2022, "governance_risk": 0.1, "sanctions_intensity": 0.0, "geo_risk": 0.1},
    ])
    ess = _ess_df([{"hs6": "260111", "category": "other", "essentiality_tier": "standard",
                    "essentiality_score": 0.2, "global_export_hhi": 0.5, "crm_listed_since": None}])

    result = compute_composite(hhi, georisk, ess)
    basket = result["basket_geo_risk"].unique()[0]
    assert basket == pytest.approx(0.5 * 0.8 + 0.5 * 0.1, abs=1e-6)  # 0.45


def test_monopoly_basket_geo_risk_equals_exporter_geo_risk():
    """Supplier with 100% share: basket_geo_risk == exporter_geo_risk."""
    hhi = _hhi_df([{"importer_iso3": "DEU", "concorded_hs6": "260111", "year": 2022,
                    "exporter_iso3": "CHN", "value_usd": 1000.0, "supplier_share": 1.0,
                    "hhi": 1.0, "supplier_count": 1}])
    georisk = _georisk_df([{"iso3": "CHN", "year": 2022, "governance_risk": 0.7,
                             "sanctions_intensity": 0.3, "geo_risk": 0.7}])
    ess = _ess_df([{"hs6": "260111", "category": "other", "essentiality_tier": "standard",
                    "essentiality_score": 0.2, "global_export_hhi": 0.5, "crm_listed_since": None}])

    result = compute_composite(hhi, georisk, ess)
    assert result["basket_geo_risk"][0] == pytest.approx(0.7, abs=1e-6)


def test_missing_geo_risk_fills_with_median():
    """Exporter not in geo-risk data → fills with _GEO_RISK_FILL (0.5)."""
    hhi = _hhi_df([{"importer_iso3": "DEU", "concorded_hs6": "260111", "year": 2022,
                    "exporter_iso3": "XYZ", "value_usd": 100.0, "supplier_share": 1.0,
                    "hhi": 1.0, "supplier_count": 1}])
    georisk = _georisk_df([])  # no coverage for XYZ
    ess = _ess_df([{"hs6": "260111", "category": "other", "essentiality_tier": "standard",
                    "essentiality_score": 0.2, "global_export_hhi": 0.0, "crm_listed_since": None}])

    result = compute_composite(hhi, georisk, ess)
    assert result["exporter_geo_risk"][0] == pytest.approx(_GEO_RISK_FILL, abs=1e-6)


def test_missing_essentiality_fills_with_standard_min():
    """Unknown HS6 → fills with _ESSENTIALITY_FILL (0.1)."""
    hhi = _hhi_df([{"importer_iso3": "DEU", "concorded_hs6": "999999", "year": 2022,
                    "exporter_iso3": "CHN", "value_usd": 100.0, "supplier_share": 1.0,
                    "hhi": 0.5, "supplier_count": 1}])
    georisk = _georisk_df([{"iso3": "CHN", "year": 2022, "governance_risk": 0.5,
                             "sanctions_intensity": 0.0, "geo_risk": 0.5}])
    ess = _ess_df([])  # no entry for 999999

    result = compute_composite(hhi, georisk, ess)
    assert result["essentiality_score"][0] == pytest.approx(_ESSENTIALITY_FILL, abs=1e-6)


def test_composite_output_columns():
    hhi = _hhi_df([{"importer_iso3": "DEU", "concorded_hs6": "260111", "year": 2022,
                    "exporter_iso3": "CHN", "value_usd": 100.0, "supplier_share": 1.0,
                    "hhi": 1.0, "supplier_count": 1}])
    georisk = _georisk_df([{"iso3": "CHN", "year": 2022, "governance_risk": 0.5,
                             "sanctions_intensity": 0.0, "geo_risk": 0.5}])
    ess = _ess_df([{"hs6": "260111", "category": "critical_raw_materials", "essentiality_tier": "critical",
                    "essentiality_score": 0.9, "global_export_hhi": 0.5, "crm_listed_since": 2020}])

    result = compute_composite(hhi, georisk, ess)
    expected = {
        "importer_iso3", "concorded_hs6", "year", "exporter_iso3",
        "value_usd", "supplier_share", "hhi", "exporter_geo_risk",
        "basket_geo_risk", "essentiality_score", "essentiality_tier",
        "crm_listed_since", "composite_score",
    }
    assert expected.issubset(set(result.columns))


def test_composite_clamped_to_one():
    """Extreme inputs → composite_score should not exceed 1.0."""
    hhi = _hhi_df([{"importer_iso3": "DEU", "concorded_hs6": "260111", "year": 2022,
                    "exporter_iso3": "CHN", "value_usd": 100.0, "supplier_share": 1.0,
                    "hhi": 1.0, "supplier_count": 1}])
    georisk = _georisk_df([{"iso3": "CHN", "year": 2022, "governance_risk": 1.0,
                             "sanctions_intensity": 1.0, "geo_risk": 1.0}])
    ess = _ess_df([{"hs6": "260111", "category": "critical_raw_materials", "essentiality_tier": "critical",
                    "essentiality_score": 1.0, "global_export_hhi": 1.0, "crm_listed_since": 2020}])

    result = compute_composite(hhi, georisk, ess)
    assert result["composite_score"][0] <= 1.0
