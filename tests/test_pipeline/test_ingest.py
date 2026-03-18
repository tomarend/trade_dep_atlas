"""Tests for the core ingestion pipeline."""

import csv
import shutil
from pathlib import Path

import polars as pl
import pytest
import yaml

from pipeline.countries import CountryRecord
from pipeline.ingest import ingest_baci_year, run_ingestion


def _make_country_mapping() -> dict[int, CountryRecord]:
    """Create a minimal country mapping for testing."""
    return {
        842: CountryRecord(baci_code=842, iso3="USA", name="United States", region="Northern America", continent="Americas"),
        276: CountryRecord(baci_code=276, iso3="DEU", name="Germany", region="Western Europe", continent="Europe"),
        156: CountryRecord(baci_code=156, iso3="CHN", name="China", region="Eastern Asia", continent="Asia"),
        392: CountryRecord(baci_code=392, iso3="JPN", name="Japan", region="Eastern Asia", continent="Asia"),
        76: CountryRecord(baci_code=76, iso3="BRA", name="Brazil", region="South America", continent="Americas"),
    }


def _make_simple_csv(path: Path, rows: list[list] | None = None) -> Path:
    """Create a simple BACI CSV for testing."""
    if rows is None:
        rows = [
            [2020, 156, 842, 854231, 50000, 100],
            [2020, 276, 842, 270900, 30000, 500],
            [2020, 156, 392, 854231, 40000, 80],
            [2020, 76, 276, 260300, 20000, 1000],
            [2020, 156, 842, 854231, 0, 50],  # zero value — should be kept
        ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t", "i", "j", "k", "v", "q"])
        writer.writerows(rows)
    return path


class TestIngestBaciYear:
    def test_ingest_synthetic_csv(self, synthetic_baci_csv: Path):
        mapping = _make_country_mapping()
        df = ingest_baci_year(synthetic_baci_csv, mapping, {}, {})

        expected_cols = {
            "year", "exporter_baci", "importer_baci", "exporter_iso3", "importer_iso3",
            "hs6_original", "concorded_hs6", "hs2", "hs4", "product_description",
            "category", "concordance_flag", "value_usd", "quantity_kg", "unit_value", "outlier_flag",
        }
        assert expected_cols.issubset(set(df.columns))
        assert len(df) > 0

    def test_zero_values_kept(self, tmp_path: Path):
        csv_path = _make_simple_csv(tmp_path / "test.csv")
        mapping = _make_country_mapping()
        df = ingest_baci_year(csv_path, mapping, {}, {})

        # Row with value_usd=0 should be present
        zero_rows = df.filter(pl.col("value_usd") == 0)
        assert len(zero_rows) > 0

    def test_null_values_dropped(self, tmp_path: Path):
        # Create CSV with a null value row
        rows = [
            [2020, 156, 842, 854231, 50000, 100],
            [2020, 276, 842, 270900, "", 500],  # empty value → null
        ]
        csv_path = tmp_path / "test.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["t", "i", "j", "k", "v", "q"])
            writer.writerows(rows)

        mapping = _make_country_mapping()
        df = ingest_baci_year(csv_path, mapping, {}, {})

        # Only the non-null row should remain
        assert len(df) == 1
        assert df["value_usd"][0] == 50000

    def test_country_mapping_applied(self, tmp_path: Path):
        csv_path = _make_simple_csv(tmp_path / "test.csv", [
            [2020, 156, 842, 854231, 50000, 100],
        ])
        mapping = _make_country_mapping()
        df = ingest_baci_year(csv_path, mapping, {}, {})

        assert df["exporter_iso3"][0] == "CHN"
        assert df["importer_iso3"][0] == "USA"

    def test_hs_hierarchy_derived(self, tmp_path: Path):
        csv_path = _make_simple_csv(tmp_path / "test.csv", [
            [2020, 156, 842, 854231, 50000, 100],
        ])
        mapping = _make_country_mapping()
        df = ingest_baci_year(csv_path, mapping, {}, {})

        assert df["hs2"][0] == "85"
        assert df["hs4"][0] == "8542"

    def test_unit_value_computed(self, tmp_path: Path):
        csv_path = _make_simple_csv(tmp_path / "test.csv", [
            [2020, 156, 842, 854231, 1000, 100],
        ])
        mapping = _make_country_mapping()
        df = ingest_baci_year(csv_path, mapping, {}, {})

        assert abs(df["unit_value"][0] - 10.0) < 0.01

    def test_unit_value_null_when_zero_quantity(self, tmp_path: Path):
        csv_path = _make_simple_csv(tmp_path / "test.csv", [
            [2020, 156, 842, 854231, 1000, 0],
        ])
        mapping = _make_country_mapping()
        df = ingest_baci_year(csv_path, mapping, {}, {})

        assert df["unit_value"][0] is None


class TestRunIngestion:
    def _setup_pipeline(self, tmp_path: Path) -> dict:
        """Set up a minimal pipeline directory structure for integration tests."""
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        reference_dir = tmp_path / "data" / "reference"
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        reference_dir.mkdir(parents=True)

        # Copy real reference files
        real_ref = Path("data/reference")
        if (real_ref / "country_overrides.yaml").exists():
            shutil.copy(real_ref / "country_overrides.yaml", reference_dir)
        if (real_ref / "hs_product_descriptions.csv").exists():
            shutil.copy(real_ref / "hs_product_descriptions.csv", reference_dir)

        # Create synthetic CSV
        _make_simple_csv(raw_dir / "BACI_HS17_Y2020.csv")

        config = {
            "baci": {"raw_dir": str(raw_dir), "retry_count": 1, "retry_backoff_seconds": 0.01},
            "processing": {"processed_dir": str(processed_dir), "reference_dir": str(reference_dir), "target_hs_revision": "H6"},
            "output": {"format": "parquet", "partition_by": "year", "compression": "zstd"},
        }
        return config

    def test_incremental_skip(self, tmp_path: Path):
        config = self._setup_pipeline(tmp_path)

        # First run — should process
        result1 = run_ingestion(config)
        assert len(result1["years_processed"]) > 0
        assert result1["total_rows"] > 0

        # Second run — should skip
        result2 = run_ingestion(config)
        assert len(result2["years_processed"]) == 0
        assert len(result2["years_skipped"]) > 0
