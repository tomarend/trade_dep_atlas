---
status: awaiting_human_verify
trigger: "Data ingestion issues: missing countries (US, France), incorrect chapter headings/descriptions, lots of missing data"
created: 2026-03-26T15:30:00.000Z
updated: 2026-03-26T15:31:00.000Z
---

## Current Focus

hypothesis: CONFIRMED — Two root causes found
test: Fix country mapping to use BACI CSV + re-run ingestion for descriptions
expecting: US, France, Norway, India, Switzerland appear; descriptions populated
next_action: Apply fix to countries.py

## Symptoms

expected: All countries including major ones (US, France) appear in dashboard with correct product chapter headings/descriptions and complete trade data
actual: Major countries like US and France missing, product chapter headings/descriptions incorrect, lots of data missing
errors: None — pipeline completes without errors
reproduction: Look at the dashboard output
started: Has never worked correctly

## Eliminated

## Evidence

- timestamp: 2026-03-26T15:32
  checked: Raw BACI data country codes for US/France
  found: BACI uses code 842 (US), 251 (France), 699 (India), 757 (Switzerland), 579 (Norway) — NOT ISO numeric (840, 250, etc.)
  implication: pycountry cannot resolve these codes, they map to "UNK"

- timestamp: 2026-03-26T15:34
  checked: Unresolved codes impact
  found: 6 unresolved codes affect 2,376,790 rows (20.7% of all data). US=624k, France=558k, India=441k, Switzerland=356k, Norway=206k rows.
  implication: Massive data loss — 5 major economies completely missing from dashboard

- timestamp: 2026-03-26T15:35
  checked: BACI country codes file existence
  found: data/raw/country_codes_V202601.csv exists with correct mappings (251→FRA, 842→USA, etc.) but code looks for data/reference/country_codes_baci.csv which doesn't exist. Column name mismatch too: file has "country_iso3", code expects "iso_3digit_alpha"
  implication: Fallback BACI CSV lookup is broken — wrong path AND wrong column name

- timestamp: 2026-03-26T15:38
  checked: Product descriptions in processed data
  found: ALL products show "Unknown product" in processed parquets, but descriptions file has 6,877 correct entries that match 100% of data codes
  implication: Descriptions file was likely missing/empty when ingestion first ran. Processed data is stale. Re-running ingestion will fix descriptions.

## Resolution

root_cause: |
  Two bugs in countries.py load_country_mapping():
  1. BACI CSV fallback path wrong: code looks for reference_dir/"country_codes_baci.csv" but actual file is raw_dir/"country_codes_V202601.csv" (with version suffix)
  2. BACI CSV column name wrong: code reads "iso_3digit_alpha" but file has "country_iso3"
  
  This causes 5 major countries (US, France, India, Switzerland, Norway) totaling 20.7% of all trade data to be mapped as "UNK" and effectively invisible.
  
  Additionally, all product descriptions show "Unknown product" in processed parquets — stale from initial ingestion when descriptions file was missing. Re-ingestion needed.
fix: |
  1. Added _find_baci_country_csv() to search for BACI country CSV by fixed name or versioned glob pattern (country_codes_V*.csv)
  2. Added optional raw_dir parameter to load_country_mapping() so it can find CSV in data/raw/
  3. Fixed column name lookup: now tries "country_iso3" (CEPII) then "iso_3digit_alpha" (legacy)
  4. Updated ingest.py to pass raw_dir=raw_dir when calling load_country_mapping()
verification: |
  - load_country_mapping() now resolves 268 countries (vs ~262 before)
  - All 6 previously missing codes resolve correctly: 842→USA, 251→FRA, 579→NOR, 699→IND, 757→CHE, 490→S19
  - All 91 pipeline tests pass (2 pre-existing georisk failures unrelated)
  - Processed data needs re-generation (delete data/processed/ and re-run pipeline)
files_changed:
  - pipeline/countries.py
  - pipeline/ingest.py
