"""Pipeline CLI orchestrator: python -m pipeline."""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from loguru import logger

from pipeline.concordance import load_concordance, validate_concordance
from pipeline.download import download_baci
from pipeline.ingest import run_ingestion


def load_config(config_path: Path = Path("pipeline.yaml")) -> dict:
    """Read pipeline.yaml configuration."""
    if not config_path.exists():
        raise FileNotFoundError(f"Pipeline config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def write_manifest(output_dir: Path, report: dict) -> Path:
    """Write pipeline manifest JSON with run metadata."""
    manifest_path = output_dir / "pipeline_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "0.1.0",
        "years_processed": report.get("years_processed", []),
        "years_skipped": report.get("years_skipped", []),
        "years_failed": report.get("years_failed", []),
        "total_rows": report.get("total_rows", 0),
        "duration_seconds": report.get("duration_seconds", 0),
        "baci_download": report.get("baci_download", {}),
        "concordance_warnings": report.get("concordance_warnings", []),
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest_path


def main(config_path: Path | None = None, skip_download: bool = False) -> None:
    """Full pipeline orchestration: download → validate → ingest → manifest."""
    start_time = time.time()

    # Stage 0: Load config
    config = load_config(config_path or Path("pipeline.yaml"))

    raw_dir = Path(config["baci"]["raw_dir"])
    processed_dir = Path(config["processing"]["processed_dir"])
    reference_dir = Path(config["processing"]["reference_dir"])

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Pipeline starting...")

    combined_report: dict = {
        "years_processed": [],
        "years_skipped": [],
        "years_failed": [],
        "total_rows": 0,
        "duration_seconds": 0,
        "baci_download": {},
        "concordance_warnings": [],
    }

    # Stage 1: Download
    if not skip_download:
        logger.info("Stage 1: Downloading BACI data...")
        download_report = download_baci(config)
        combined_report["baci_download"] = {
            "downloaded": len(download_report.downloaded),
            "skipped": len(download_report.skipped),
            "failed": len(download_report.failed),
        }
        logger.info(
            f"Download: {len(download_report.downloaded)} downloaded, "
            f"{len(download_report.skipped)} skipped, "
            f"{len(download_report.failed)} failed"
        )
    else:
        logger.info("Stage 1: Skipping download (--skip-download)")

    # Stage 2: Validate concordance
    logger.info("Stage 2: Validating concordance...")
    concordance = load_concordance(reference_dir)
    warnings = validate_concordance(concordance)
    combined_report["concordance_warnings"] = warnings
    for w in warnings:
        logger.warning(f"Concordance: {w}")

    # Stage 3: Ingest
    logger.info("Stage 3: Ingesting BACI data...")
    ingestion_result = run_ingestion(config)
    combined_report["years_processed"] = ingestion_result["years_processed"]
    combined_report["years_skipped"] = ingestion_result["years_skipped"]
    combined_report["total_rows"] = ingestion_result["total_rows"]
    logger.info(
        f"Ingestion: {len(ingestion_result['years_processed'])} years processed, "
        f"{ingestion_result['total_rows']:,} total rows"
    )

    # Stage 4: Write manifest
    duration = round(time.time() - start_time, 2)
    combined_report["duration_seconds"] = duration
    manifest_path = write_manifest(processed_dir, combined_report)
    logger.info(f"Manifest written to {manifest_path}")

    logger.info(f"Pipeline complete in {duration}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BACI Trade Data Pipeline")
    parser.add_argument("--config", type=Path, default=Path("pipeline.yaml"), help="Path to pipeline config YAML")
    parser.add_argument("--skip-download", action="store_true", help="Skip BACI data download stage")
    args = parser.parse_args()
    main(config_path=args.config, skip_download=args.skip_download)
