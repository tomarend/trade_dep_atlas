---
phase: 01-data-pipeline-ingestion
plan: 01
subsystem: pipeline
tags: [polars, requests, baci, download, etl]

requires: []
provides:
  - Project scaffolding with pyproject.toml, directory structure, and all dependencies
  - BACI download module with retry, resume, ZIP extraction, and CSV verification
  - Synthetic BACI test fixtures (5 countries × 10 products × 3 years)
affects: [01-02, 01-03, scoring-pipeline]

tech-stack:
  added: [polars, pyarrow, duckdb, dash, plotly, requests, pycountry, tqdm, loguru, pyyaml, ruff, pytest]
  patterns: [dataclass-based reports, YAML config loading, tqdm progress bars, loguru structured logging]

key-files:
  created:
    - pyproject.toml
    - pipeline/__init__.py
    - pipeline/download.py
    - pipeline.yaml
    - .gitignore
    - tests/conftest.py
    - tests/test_pipeline/test_download.py
  modified: []

key-decisions:
  - "DownloadReport dataclass with downloaded/skipped/failed lists for structured results"
  - "discover_baci_urls parses CEPII download page HTML with regex fallback"
  - "ZIP extraction deletes ZIP after success, leaving only CSV"
  - "verify_baci_csv checks for t,i,j,k,v,q column headers"
  - "Retry uses exponential backoff (backoff_seconds * 2^attempt)"

patterns-established:
  - "Config via pipeline.yaml loaded with yaml.safe_load"
  - "Test fixtures in conftest.py with synthetic BACI data (deterministic via Random(42))"
  - "pipeline_config fixture provides tmp_path-based config dict"
  - "uv for package management, ruff for linting, pytest for testing"

requirements-completed: [DATA-01]

duration: 8min
completed: 2026-03-18
---

# Plan 01-01: Project Scaffolding + BACI Download Module

**Greenfield project established with full dependency stack and a BACI download module that handles retry, resume, ZIP extraction, and progress reporting.**

## What Was Built

1. **Project scaffolding**: pyproject.toml with all 16+ dependencies (Dash 4.0, Polars 1.36+, DuckDB 1.5+, etc.), directory skeleton (pipeline/, data/raw|processed|reference/, tests/), .gitignore for data artifacts, pipeline.yaml config.

2. **Download module** (`pipeline/download.py`):
   - `discover_baci_urls()` — fetches CEPII download page, parses for BACI file links
   - `download_file()` — stream download with tqdm progress bar
   - `extract_zip()` — extracts ZIP contents, cleans up ZIP
   - `verify_baci_csv()` — validates CSV has expected BACI columns
   - `download_baci()` — orchestrates full download with retry (exponential backoff), skip-existing, ZIP handling

3. **Test fixtures** (`tests/conftest.py`): `synthetic_baci_csv` creates ~350 rows of realistic bilateral trade data; `pipeline_config` provides a tmp_path-based config dict.

## Test Results

9 tests passing: CSV verification (valid/invalid/nonexistent), ZIP extraction, skip existing, retry on failure, max retries skip, report counts, empty URL list.

## Interface for Downstream Plans

```python
from pipeline.download import download_baci, DownloadReport

@dataclass
class DownloadReport:
    downloaded: list[Path]
    skipped: list[Path]
    failed: list[tuple[str, str]]

def download_baci(config: dict, output_dir: Path | None = None) -> DownloadReport
def verify_baci_csv(csv_path: Path) -> bool
```
