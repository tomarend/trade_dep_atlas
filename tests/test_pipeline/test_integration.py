"""Integration tests for the full pipeline."""

import json
import shutil
from pathlib import Path

import polars as pl
import yaml

from pipeline.__main__ import load_config, main, write_manifest


def _setup_integration(tmp_path: Path) -> Path:
    """Set up a full pipeline directory structure for integration tests.

    Returns the config file path.
    """
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

    # Create synthetic BACI CSV
    csv_path = raw_dir / "BACI_HS17_Y2020.csv"
    csv_path.write_text(
        "t,i,j,k,v,q\n"
        "2020,156,842,854231,50000,100\n"
        "2020,276,842,270900,30000,500\n"
        "2020,156,392,854231,40000,80\n"
        "2020,76,276,260300,20000,1000\n"
        "2020,392,156,870323,60000,200\n"
    )

    config = {
        "baci": {
            "download_page": "https://example.com/baci",
            "raw_dir": str(raw_dir),
            "retry_count": 1,
            "retry_backoff_seconds": 0.01,
            "chunk_size_bytes": 65536,
            "request_timeout_seconds": 10,
        },
        "processing": {
            "processed_dir": str(processed_dir),
            "reference_dir": str(reference_dir),
            "target_hs_revision": "H6",
        },
        "output": {
            "format": "parquet",
            "partition_by": "year",
            "compression": "zstd",
        },
    }

    config_path = tmp_path / "pipeline.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


class TestFullPipeline:
    def test_full_pipeline_synthetic(self, tmp_path: Path):
        config_path = _setup_integration(tmp_path)

        main(config_path=config_path, skip_download=True, skip_scoring=True)

        processed_dir = tmp_path / "data" / "processed"

        # Check Parquet files exist
        parquet_files = list(processed_dir.rglob("*.parquet"))
        assert len(parquet_files) > 0

        # Check manifest exists and is valid
        manifest_path = processed_dir / "pipeline_manifest.json"
        assert manifest_path.exists()
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert "years_processed" in manifest
        assert len(manifest["years_processed"]) > 0
        assert "total_rows" in manifest
        assert manifest["total_rows"] > 0

        # Read Parquet and verify columns
        df = pl.read_parquet(parquet_files[0])
        expected_cols = {"year", "exporter_iso3", "importer_iso3", "concorded_hs6", "value_usd", "quantity_kg"}
        assert expected_cols.issubset(set(df.columns))

    def test_incremental_full(self, tmp_path: Path):
        config_path = _setup_integration(tmp_path)

        # First run processes data
        main(config_path=config_path, skip_download=True, skip_scoring=True)
        processed_dir = tmp_path / "data" / "processed"
        manifest_path = processed_dir / "pipeline_manifest.json"
        with open(manifest_path) as f:
            manifest1 = json.load(f)
        assert len(manifest1["years_processed"]) > 0

        # Second run skips everything
        main(config_path=config_path, skip_download=True, skip_scoring=True)
        with open(manifest_path) as f:
            manifest2 = json.load(f)
        assert len(manifest2["years_processed"]) == 0
        assert len(manifest2["years_skipped"]) > 0


class TestManifest:
    def test_manifest_structure(self, tmp_path: Path):
        report = {
            "years_processed": [2020],
            "years_skipped": [],
            "total_rows": 1000,
            "duration_seconds": 5.0,
        }
        manifest_path = write_manifest(tmp_path, report)
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "run_timestamp" in manifest
        assert "pipeline_version" in manifest
        assert manifest["years_processed"] == [2020]
        assert manifest["total_rows"] == 1000


class TestCLI:
    def test_pipeline_cli_help(self, tmp_path: Path):
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pipeline", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
        assert result.returncode == 0
        assert "BACI Trade Data Pipeline" in result.stdout
