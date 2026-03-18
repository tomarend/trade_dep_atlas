"""Shared test fixtures for the pipeline test suite."""

import csv
import random
from pathlib import Path

import pytest
import yaml

# Synthetic test data — 5 countries, 10 products, 3 years
SYNTHETIC_COUNTRIES = {
    842: {"name": "United States", "iso3": "USA"},
    276: {"name": "Germany", "iso3": "DEU"},
    156: {"name": "China", "iso3": "CHN"},
    392: {"name": "Japan", "iso3": "JPN"},
    76: {"name": "Brazil", "iso3": "BRA"},
}

SYNTHETIC_PRODUCTS = [
    "854231",  # processors
    "270900",  # crude oil
    "300490",  # pharma
    "710812",  # gold
    "280461",  # lithium
    "260300",  # copper ore
    "100199",  # wheat
    "271111",  # natural gas
    "870323",  # vehicles
    "850440",  # converters
]

SYNTHETIC_YEARS = [2019, 2020, 2021]


@pytest.fixture
def synthetic_baci_csv(tmp_path: Path) -> Path:
    """Create a synthetic BACI CSV with ~50 rows of bilateral trade data."""
    csv_path = tmp_path / "BACI_HS17_Y2020_V202401.csv"
    rng = random.Random(42)

    country_codes = list(SYNTHETIC_COUNTRIES.keys())
    rows = []
    for year in SYNTHETIC_YEARS:
        for product in SYNTHETIC_PRODUCTS:
            # Each importer imports from 2-3 exporters per product
            for importer in country_codes:
                num_exporters = rng.randint(2, 3)
                exporters = rng.sample([c for c in country_codes if c != importer], num_exporters)
                for exporter in exporters:
                    value = rng.randint(100, 100000)
                    quantity = rng.randint(10, 10000)
                    rows.append([year, exporter, importer, product, value, quantity])

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t", "i", "j", "k", "v", "q"])
        writer.writerows(rows)

    return csv_path


@pytest.fixture
def pipeline_config(tmp_path: Path) -> dict:
    """Return a pipeline config dict with tmp_path-based directories."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    reference_dir = tmp_path / "data" / "reference"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "baci": {
            "download_page": "https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html",
            "raw_dir": str(raw_dir),
            "retry_count": 3,
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

    # Write config to a YAML file for tests that need a file path
    config_path = tmp_path / "pipeline.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config
