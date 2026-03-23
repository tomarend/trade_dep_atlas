---
status: testing
phase: 01-data-pipeline-ingestion
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md]
started: 2026-03-18T00:00:00Z
updated: 2026-03-18T00:02:00Z
---

## Current Test

number: 3
name: Pipeline manifest written
expected: After running python -m pipeline --skip-download, a manifest JSON
  file exists. Opening it shows run_timestamp, years_processed, total_rows,
  concordance_warnings fields.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: python -m pipeline --help prints usage with --skip-download and --config options. pytest runs all 39 tests, 0 failures.
result: pass

### 2. CLI --skip-download runs and produces Parquet
expected: Run python -m pipeline --skip-download. Pipeline skips the CEPII download step. Either Parquet appears under data/processed/year=YYYY/data.parquet, or exits cleanly with no raw files message. No unhandled exceptions.
result: issue
reported: "There is an issue with the downloader in that it also downloads the archives which we do not want."
severity: major

### 3. Pipeline manifest written
expected: After running python -m pipeline --skip-download, a manifest JSON file exists. Opening it shows run_timestamp, years_processed, total_rows, concordance_warnings fields.
result: pending

### 4. Country codes mapped to ISO3
expected: In the Parquet output, columns exporter_iso3 and importer_iso3 contain 3-letter codes (e.g. USA, DEU, CHN), not raw numeric BACI codes.
result: pending

### 5. HS concordance and outlier flags present
expected: In the Parquet output, columns concorded_hs6, concordance_flag, and outlier_flag are present. concordance_flag values are one of: unchanged, mapped, split, merged, unmapped. outlier_flag is boolean.
result: pending

### 6. Re-export hub and special territory overrides
expected: from pipeline.countries import load_country_mapping - HKG record has is_reexport_hub=True. Taiwan (TWN) is also present in the mapping.
result: pending

## Summary

total: 6
passed: 1
issues: 1
pending: 4
skipped: 0

## Gaps

- truth: "Pipeline only downloads BACI CSV files, not archive files"
  status: failed
  reason: "User reported: downloader also downloads archives which we do not want"
  severity: major
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
