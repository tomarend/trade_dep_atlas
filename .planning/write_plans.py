"""Write all 4 Phase 7 PLAN.md files."""
import pathlib

phase_dir = pathlib.Path(".planning/phases/07-pipeline-scoring-rework")
phase_dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# Plan 07-01
# ============================================================
plan_01 = """\
---
phase: 07-pipeline-scoring-rework
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - pipeline/download.py
  - pipeline/concordance.py
  - pipeline/ingest.py
autonomous: true
requirements:
  - DATA-06
  - DATA-07
must_haves:
  truths:
    - "discover_baci_urls() returns only HS92 and HS22 entries (no HS17, HS10, HS96, etc.)"
    - "run_ingestion() skips HS92 CSVs for years 2022, 2023, 2024 when HS22 version exists"
    - "load_product_descriptions() uses product_codes_HS22_V*.csv from data/raw/ when present"
    - "country_codes_V*.csv extracted from ZIPs is the authoritative source (already wired in countries.py)"
  artifacts:
    - path: "pipeline/download.py"
      provides: "HS revision filter after discover_baci_urls dedup step"
      contains: "H92.*H22|H22.*H92"
    - path: "pipeline/ingest.py"
      provides: "HS22-priority ingest for 2022-2024"
      contains: "hs22_years"
    - path: "pipeline/concordance.py"
      provides: "BACI product codes as authoritative description source"
      contains: "product_codes_HS"
  key_links:
    - from: "pipeline/download.py"
      to: "discover_baci_urls return value"
      via: "hs_revision filter set {H92, H22}"
      pattern: "H92.*H22|{.H92., .H22.}"
    - from: "pipeline/ingest.py"
      to: "year parquet skipping"
      via: "hs22_years set tracks processed overlap years"
      pattern: "hs22_years"
---

<objective>
Slim BACI download to HS92 + HS22 revisions only, and make HS22 the authoritative source 
for 2022-2024 trade rows. Use BACI's own bundled mapping files for product descriptions.

Purpose: Reduces download from ~45GB to ~17GB. HS22 replaces HS92 for years 2022-2024
(the more current revision). BACI-bundled product_codes_HS*.csv replaces the separate
hs_product_descriptions.csv for descriptions.
Output: Modified download.py, ingest.py, concordance.py ready for pipeline run.
</objective>

<execution_context>
@$HOME/.copilot/get-shit-done/workflows/execute-plan.md
@$HOME/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/07-pipeline-scoring-rework/07-CONTEXT.md
</context>

<interfaces>
<!-- Key signatures the executor must know. Read these files before touching them. -->

From pipeline/download.py (discover_baci_urls):
  - Returns list[dict] with keys: url, filename, hs_revision
  - hs_revision format: "H92" for HS92, "H22" for HS22, "H17" for HS2017, etc.
    (derived as f"H{hs_match.group(1)}" where hs_match extracts digits from filename)
  - Dedup step: latest_by_revision dict → urls list comprehension
  - ADD FILTER after the urls list comprehension, before the logger.info() call:
    urls = [u for u in urls if u["hs_revision"] in {"H92", "H22"}]

From pipeline/concordance.py (load_product_descriptions):
  - Current signature: load_product_descriptions(reference_dir: Path) -> dict[str, tuple[str, str]]
  - Returns: hs6 -> (description, category)
  - NEW signature: load_product_descriptions(reference_dir: Path, raw_dir: Path | None = None)
  - When raw_dir provided: look for product_codes_HS22_V*.csv first, then product_codes_HS*_V*.csv
  - BACI product codes file columns: "code" (or "product_code"), "description" — no category column
  - Return (description, "") when sourced from BACI file (empty category string is fine)

From pipeline/ingest.py (run_ingestion):
  - Loops sorted(raw_dir.glob("*.csv")) — currently ALL csv files
  - Country code CSVs (country_codes_V*.csv) and product code CSVs (product_codes_HS*.csv)
    sit in the same raw_dir — must skip them (they are not trade data CSVs)
  - HS revision detection from filename: re.search(r"BACI_(HS\\d+)_", csv_path.name)
    BACI_HS22_V202401_Y2022.csv → "HS22"
    BACI_HS92_V202401_Y2020.csv → "HS92"
  - HS22 priority: process HS22 CSVs BEFORE HS92 (sort key puts HS22 first)
  - Skip HS92 for years 2022/2023/2024 if that year already in hs22_years set
  - Update load_product_descriptions call to pass raw_dir
</interfaces>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Filter download to HS92 + HS22 only</name>
  <files>pipeline/download.py</files>
  <read_first>
    - pipeline/download.py (MANDATORY — read current discover_baci_urls() in full before editing)
  </read_first>
  <action>
In discover_baci_urls(), locate the list comprehension that builds the final `urls` list
from latest_by_revision.values() (currently around line 192):

    urls = [
        {"url": e["url"], "filename": e["filename"], "hs_revision": e["hs_revision"]}
        for e in latest_by_revision.values()
    ]

IMMEDIATELY AFTER this block (before the logger.info call), add ONE line:

    urls = [u for u in urls if u["hs_revision"] in {"H92", "H22"}]

That's the entire change. No other modifications to this file.

Why {"H92", "H22"}: hs_revision is built as f"H{hs_match.group(1)}" where the regex
extracts digits from the filename (e.g. "BACI_HS92_V202401..." → match group = "92" → "H92").
  </action>
  <verify>
    <automated>grep -n 'H92.*H22\|H22.*H92' pipeline/download.py | grep -v '#'</automated>
  </verify>
  <done>grep confirms the filter line exists. discover_baci_urls returns at most 2 entries.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: BACI product codes as authoritative description source</name>
  <files>pipeline/concordance.py</files>
  <read_first>
    - pipeline/concordance.py (MANDATORY — read load_product_descriptions() fully before editing)
    - pipeline/ingest.py (read run_ingestion() to find the load_product_descriptions call to update)
    - pipeline/export.py (read build_duckdb() to find the load_product_descriptions call to update)
  </read_first>
  <action>
1. Update load_product_descriptions() signature:
   OLD: def load_product_descriptions(reference_dir: Path) -> dict[str, tuple[str, str]]:
   NEW: def load_product_descriptions(reference_dir: Path, raw_dir: Path | None = None) -> dict[str, tuple[str, str]]:

2. At the START of the function body (before the existing desc_path logic), add:
   if raw_dir is not None:
       # Try HS22 first (most current), then any HS revision
       baci_files = sorted(raw_dir.glob("product_codes_HS22_V*.csv"))
       if not baci_files:
           baci_files = sorted(raw_dir.glob("product_codes_HS*_V*.csv"))
       if baci_files:
           baci_path = baci_files[-1]  # latest version
           descriptions: dict[str, tuple[str, str]] = {}
           with open(baci_path, newline="", encoding="utf-8-sig") as f:
               reader = csv.DictReader(f)
               for row in reader:
                   # BACI columns: "code" or "product_code", "description"
                   raw_code = row.get("code", row.get("product_code", "")).strip()
                   if not raw_code:
                       continue
                   code = str(raw_code).zfill(6)
                   desc = row.get("description", "").strip()
                   descriptions[code] = (desc, "")
           logger.info(f"Loaded {len(descriptions)} product descriptions from {baci_path.name}")
           return descriptions
   # Fall through to existing hs_product_descriptions.csv logic below

3. Update run_ingestion() in pipeline/ingest.py:
   Find: descriptions = load_product_descriptions(reference_dir)
   Change to: descriptions = load_product_descriptions(reference_dir, raw_dir=raw_dir)

4. Update build_duckdb() in pipeline/export.py:
   Find: descriptions = load_product_descriptions(reference_dir)
   Change to: descriptions = load_product_descriptions(reference_dir, raw_dir=raw_dir)
   (raw_dir is already a parameter of build_duckdb())
  </action>
  <verify>
    <automated>grep -n "raw_dir" pipeline/concordance.py | head -5</automated>
  </verify>
  <done>
    - load_product_descriptions has raw_dir parameter
    - pipeline/ingest.py passes raw_dir to load_product_descriptions
    - pipeline/export.py passes raw_dir to load_product_descriptions
    - python -c "from pipeline.concordance import load_product_descriptions; print('OK')" exits 0
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: HS22 wins for years 2022-2024 in ingest</name>
  <files>pipeline/ingest.py</files>
  <read_first>
    - pipeline/ingest.py (MANDATORY — read run_ingestion() in full before editing)
  </read_first>
  <action>
In run_ingestion(), make the following changes:

1. Add import at top of file (if not already present):
   import re

2. Before the csv_files loop, initialize:
   hs22_years: set[int] = set()

3. Change the csv_files sort to put HS22 files first:
   OLD: csv_files = sorted(raw_dir.glob("*.csv"))
   NEW: csv_files = sorted(
       raw_dir.glob("*.csv"),
       key=lambda p: (0 if re.search(r"BACI_HS22_", p.name, re.IGNORECASE) else 1, p.name)
   )

4. At the START of the csv loop body (before the year extraction try block), add a skip
   for non-trade CSVs (country/product mapping files):
   if csv_path.name.startswith(("country_codes", "product_codes")):
       continue

5. After the year extraction (after the "year = int(sample["t"][0])" line), add:
   # Detect HS revision from filename
   hs_rev_match = re.search(r"BACI_(HS\\d+)_", csv_path.name, re.IGNORECASE)
   hs_revision = hs_rev_match.group(1).upper() if hs_rev_match else "HS92"

   # HS22 wins for 2022-2024: skip non-HS22 if HS22 already processed this year
   if year in {2022, 2023, 2024} and hs_revision != "HS22" and year in hs22_years:
       logger.info(f"Skipping {csv_path.name} — HS22 already covers year {year}")
       years_skipped.append(year)
       continue

6. After the "df.write_parquet(parquet_path ...)" line (successful ingest), add:
   if hs_revision == "HS22" and year in {2022, 2023, 2024}:
       hs22_years.add(year)
  </action>
  <verify>
    <automated>grep -n "hs22_years\|hs_revision\|HS22" pipeline/ingest.py | head -15</automated>
  </verify>
  <done>
    - ingest.py contains hs22_years set and hs_revision detection
    - Non-trade CSVs (country_codes, product_codes) are skipped in the loop
    - python -c "from pipeline.ingest import run_ingestion; print('OK')" exits 0
  </done>
</task>

</tasks>

<verification>
python -c "
from pipeline.download import discover_baci_urls
from pipeline.concordance import load_product_descriptions
from pipeline.ingest import run_ingestion
print('All imports OK')
"

grep -c 'H92.*H22\|H22.*H92' pipeline/download.py
grep -c 'hs22_years' pipeline/ingest.py
grep -c 'raw_dir' pipeline/concordance.py
</verification>

<success_criteria>
- discover_baci_urls returns only HS92 and HS22 entries when run
- run_ingestion skips HS92 CSVs for years 2022, 2023, 2024 when HS22 was processed first
- load_product_descriptions uses BACI product codes CSV when raw_dir is provided
- All three modules import cleanly with no Python errors
</success_criteria>

<output>
After completion, create .planning/phases/07-pipeline-scoring-rework/07-01-SUMMARY.md
</output>
"""

# ============================================================
# Plan 07-02
# ============================================================
plan_02 = """\
---
phase: 07-pipeline-scoring-rework
plan: "02"
type: execute
wave: 1
depends_on: []
files_modified:
  - pipeline/flags.py
  - data/reference/flags_config.yaml
autonomous: true
requirements:
  - SCOR-06
  - SCOR-07
  - SCOR-08
must_haves:
  truths:
    - "pipeline/flags.py exists and exports run_flags_scoring() and classify_hs6()"
    - "classify_hs6() returns list[str] of flag names, never a (tier, category, crm_since) tuple"
    - "data/reference/flags_config.yaml exists with 8 canonical flags including fertilizer"
    - "flags_scores.parquet schema: hs6, flags (List), global_export_hhi, crm_listed_since, hs22_only"
  artifacts:
    - path: "pipeline/flags.py"
      provides: "Flag-based product classification replacing essentiality.py"
      exports: ["run_flags_scoring", "compute_product_flags", "classify_hs6", "compute_global_export_hhi", "load_crm_hs6_mapping"]
    - path: "data/reference/flags_config.yaml"
      provides: "8 canonical flag definitions with HS inclusion rules"
      contains: "fertilizer"
  key_links:
    - from: "pipeline/flags.py::run_flags_scoring()"
      to: "data/scoring/flags/flags_scores.parquet"
      via: "result.write_parquet(out_path)"
      pattern: "scoring/flags/flags_scores"
    - from: "flags_config.yaml::fertilizer"
      to: "pipeline/flags.py::classify_hs6()"
      via: "hs2_include: ['31'] rule matched against hs2 = hs6[:2]"
      pattern: "fertilizer"
---

<objective>
Create pipeline/flags.py (replacing essentiality.py) and data/reference/flags_config.yaml.
Each HS6 product gets a list of categorical flags instead of a tier score.

Purpose: Empirical classification. global_export_hhi is the substitutability measure,
not a hand-crafted tier score. Flags are orthogonal labels, not a ranking.
Output: pipeline/flags.py and data/reference/flags_config.yaml ready for composite.py to consume.
</objective>

<execution_context>
@$HOME/.copilot/get-shit-done/workflows/execute-plan.md
@$HOME/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/07-pipeline-scoring-rework/07-CONTEXT.md
@.planning/STATE.md
</context>

<interfaces>
<!-- Key signatures from essentiality.py that flags.py replaces. Read this file before writing flags.py. -->

From pipeline/essentiality.py (read this file before writing flags.py):
  compute_global_export_hhi(processed_dir: Path) -> pl.DataFrame
    Returns: [concorded_hs6, global_export_hhi]
    KEEP THIS FUNCTION VERBATIM in flags.py (it's correct).

  load_crm_hs6_mapping(reference_dir: Path) -> pl.DataFrame
    Returns DataFrame: [material, hs6, crm_listed_since, source]
    KEEP THIS FUNCTION VERBATIM in flags.py.

  OLD classify_hs6() returns (tier, category, crm_since) tuple — DELETE
  NEW classify_hs6() returns list[str] of flag names

  OLD compute_essentiality_scores() → RENAME to compute_product_flags()
  OLD run_essentiality_scoring() → RENAME to run_flags_scoring()

From data/reference/essentiality_config.yaml (read this for copying HS rules to flags_config.yaml):
  energy: hs2_include ["27"], hs4_exclude ["2716"]
  fertilizer: hs2_include ["31"] (chapter 31 = fertilizers)
  food: hs2_include ["01"-"24"] (full agriculture/food section)
  pharma: hs2_include ["29", "30"] (APIs + finished pharma — merge into one flag)
  semiconductor hs6_include: 280469, 280470, 284961, 284969, 284910, 811292, 811299, 284490, 280610, 284630
  strategic_mineral: hs4_include 2602, 2604, 2606, 2609, 2610, 2615, 2617
  crm_listed: managed via crm_hs6_mapping.csv (set_programmatically: true)
  hs22_only: set at ingest time (set_programmatically: true)

From pipeline/essentiality.py (output schema to replace):
  OLD: [hs6, category, essentiality_tier, essentiality_score, global_export_hhi, crm_listed_since]
  NEW: [hs6, flags, global_export_hhi, crm_listed_since, hs22_only]
       flags: pl.List(pl.Utf8)
       global_export_hhi: pl.Float64
       crm_listed_since: pl.Int64 (null if not CRM-listed)
       hs22_only: pl.Boolean (False by default; set True from HS22/HS92 product code diff)
</interfaces>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create flags_config.yaml with 8 canonical flags</name>
  <files>data/reference/flags_config.yaml</files>
  <read_first>
    - data/reference/essentiality_config.yaml (copy HS rules from existing tiers into new format)
  </read_first>
  <action>
Create data/reference/flags_config.yaml with this exact structure:

---
# Product classification flags — Phase 7 v2.0
# Replaces essentiality_config.yaml (deleted by Plan 07-03).
# 8 canonical flags. set_programmatically: true means the flag is not driven by YAML rules.
# Rule evaluation order: hs6_exclude/hs4_exclude take precedence over any include rule.
# Each flag is independent — a product can have multiple flags.

crm_listed:
  description: "EU CRM 2023 / USGS Critical Minerals 2022 list"
  set_programmatically: true  # driven by crm_hs6_mapping.csv, not yaml rules
  hs6_include: []
  hs6_exclude: []

energy:
  description: "Mineral fuels, oils, gas, coal (HS chapter 27 excluding electric current)"
  hs2_include: ["27"]
  hs4_exclude: ["2716"]  # 2716 = electric energy (not a physical scarce commodity)

fertilizer:
  description: "Nitrogen/phosphorus/potassium fertilizers and mineral nutrients (HS chapter 31)"
  hs2_include: ["31"]

food:
  description: "Live animals, food and agricultural products (HS chapters 01-24)"
  hs2_include:
    ["01","02","03","04","05","06","07","08","09","10","11","12",
     "13","14","15","16","17","18","19","20","21","22","23","24"]

pharma:
  description: "Pharmaceutical active ingredients (HS29) and finished medicines (HS30)"
  hs2_include: ["29", "30"]

semiconductor:
  description: "Key semiconductor fabrication materials not covered by CRM list"
  hs6_include:
    - "280469"   # Silicon (other) — semiconductor grade
    - "280470"   # Silicon (other form) — solar/semiconductor
    - "284961"   # Germanium oxides / germanium dioxide
    - "284969"   # Germanium and articles thereof
    - "284910"   # Fluorides (HF used in chip fab)
    - "811292"   # Unwrought indium (transparent displays)
    - "811299"   # Indium articles (ITO for displays)
    - "284490"   # Radioactive isotopes
    - "280610"   # Chlorine gas (semiconductor cleaning)
    - "284630"   # Europium (phosphors for displays/LEDs)

strategic_mineral:
  description: "Strategic mining ores not individually listed on CRM but geopolitically significant"
  hs4_include:
    - "2602"   # manganese ores
    - "2604"   # nickel ores
    - "2606"   # aluminium ores (bauxite)
    - "2609"   # tin ores
    - "2610"   # chromium ores
    - "2615"   # niobium, tantalum, vanadium ores
    - "2617"   # antimony ores

hs22_only:
  description: "Product code introduced in HS2022 revision — no pre-2022 time series available"
  set_programmatically: true  # set by run_flags_scoring() from HS22/HS92 product code diff
  hs6_include: []
  hs6_exclude: []
---

Verify after writing: grep "fertilizer" data/reference/flags_config.yaml
  </action>
  <verify>
    <automated>grep -c "fertilizer\|semiconductor\|strategic_mineral\|hs22_only\|crm_listed" data/reference/flags_config.yaml</automated>
  </verify>
  <done>flags_config.yaml exists with all 8 flag keys. grep count = 8.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create pipeline/flags.py replacing essentiality.py</name>
  <files>pipeline/flags.py</files>
  <read_first>
    - pipeline/essentiality.py (MANDATORY — read the entire file; copy compute_global_export_hhi and load_crm_hs6_mapping verbatim)
    - data/reference/flags_config.yaml (the config this module will read)
  </read_first>
  <action>
Create pipeline/flags.py. The file has these functions:

1. load_flags_config(reference_dir: Path) -> dict
   Loads data/reference/flags_config.yaml. Raises FileNotFoundError if missing.

2. load_crm_hs6_mapping(reference_dir: Path) -> pl.DataFrame
   COPY VERBATIM from pipeline/essentiality.py. Do not change a single line.

3. compute_global_export_hhi(processed_dir: Path) -> pl.DataFrame
   COPY VERBATIM from pipeline/essentiality.py. Do not change a single line.

4. classify_hs6(hs6: str, flags_config: dict, crm_hs6_set: set) -> list[str]
   NEW implementation (replaces old tuple-returning classify_hs6):
   - Returns list of matching flag names (empty list = no flags)
   - hs22_only is NOT set here (it's set in compute_product_flags from product code diff)
   - For each flag in flags_config:
     - Skip if rules.get("set_programmatically", False) is True (handles crm_listed, hs22_only)
     - Apply hs6_exclude / hs4_exclude — if match, skip this flag
     - Check hs6_include, then hs4_include, then hs2_include — if match, append flag name
   - After the loop, check if hs6 in crm_hs6_set → append "crm_listed"
   - Return list (may be empty, may have multiple flags)

5. compute_product_flags(flags_config: dict, reference_dir: Path, processed_dir: Path,
                         raw_dir: Path | None = None) -> pl.DataFrame
   Output schema: hs6 (Utf8), flags (List(Utf8)), global_export_hhi (Float64),
                  crm_listed_since (Int64, nullable), hs22_only (Boolean)

   Steps:
   a. Load crm_df from load_crm_hs6_mapping(reference_dir)
   b. Build crm_hs6_set: set of hs6 strings
   c. Build crm_since_lookup: dict[str, int|None] from crm_df (hs6 → crm_listed_since)
   d. Get all unique HS6 codes from processed parquet (same as essentiality.py)
   e. Compute global_hhi_df via compute_global_export_hhi(processed_dir)
   f. Build hhi_lookup: dict[str, float]
   g. Determine hs22_only_set: set of HS6 codes unique to HS22 (not in HS92)
      Logic:
        if raw_dir is not None:
            hs22_files = sorted(raw_dir.glob("product_codes_HS22_V*.csv"))
            hs92_files = sorted(raw_dir.glob("product_codes_HS92_V*.csv"))
            def load_product_codes(csv_path):
                codes = set()
                with open(csv_path, newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        code = str(row.get("code", row.get("product_code", ""))).strip().zfill(6)
                        if code: codes.add(code)
                return codes
            if hs22_files and hs92_files:
                hs22_codes = load_product_codes(hs22_files[-1])
                hs92_codes = load_product_codes(hs92_files[-1])
                hs22_only_set = hs22_codes - hs92_codes
            else:
                hs22_only_set = set()
        else:
            hs22_only_set = set()
   h. For each hs6 in all_hs6:
      - flags_list = classify_hs6(hs6, flags_config, crm_hs6_set)
      - if hs6 in hs22_only_set: flags_list.append("hs22_only")
      - global_hhi = hhi_lookup.get(hs6, 0.0)
      - crm_since_val = crm_since_lookup.get(hs6, None)  (int or None)
      - rows.append({hs6, flags: flags_list, global_export_hhi, crm_listed_since, hs22_only})
   i. Return pl.DataFrame with explicit schema

6. run_flags_scoring(config: dict) -> dict
   - reference_dir = Path(config["processing"]["reference_dir"])
   - processed_dir = Path(config["processing"]["processed_dir"])
   - raw_dir = Path(config["baci"]["raw_dir"])
   - scoring_dir = Path(config.get("scoring", {}).get("output_dir", "data/scoring"))
   - out_path = scoring_dir / "flags" / "flags_scores.parquet"
   - flags_config = load_flags_config(reference_dir)
   - result = compute_product_flags(flags_config, reference_dir, processed_dir, raw_dir)
   - out_path.parent.mkdir(parents=True, exist_ok=True)
   - result.write_parquet(out_path, compression="zstd")
   - Log: count of products per flag (explode flags column, count distinct hs6 per flag)
   - Return {"products_scored": len(result), "output_path": str(out_path)}

CRITICAL — do NOT include:
  - _tier_score() function
  - load_essentiality_overrides() function
  - Any reference to "tier", "essentiality_score", "essentiality_tier", "category"
  - Any import or use of essentiality_config.yaml
  </action>
  <verify>
    <automated>python -c "from pipeline.flags import run_flags_scoring, classify_hs6, compute_global_export_hhi, load_crm_hs6_mapping; print('OK')"</automated>
  </verify>
  <done>
    - pipeline/flags.py imports cleanly
    - classify_hs6 returns list (not tuple): python -c "import inspect; from pipeline.flags import classify_hs6; print(inspect.signature(classify_hs6))"
    - grep -c "_tier_score\|essentiality_score\|essentiality_tier" pipeline/flags.py returns 0
    - grep "flags_scores.parquet" pipeline/flags.py confirms output path
  </done>
</task>

</tasks>

<verification>
python -c "
from pipeline.flags import run_flags_scoring, classify_hs6, compute_global_export_hhi, load_crm_hs6_mapping
print('imports OK')
import yaml
with open('data/reference/flags_config.yaml') as f:
    cfg = yaml.safe_load(f)
flags = list(cfg.keys())
assert 'fertilizer' in flags, 'fertilizer missing'
assert 'crm_listed' in flags, 'crm_listed missing'
assert 'hs22_only' in flags, 'hs22_only missing'
assert len(flags) == 8, f'expected 8 flags, got {len(flags)}: {flags}'
print(f'flags OK: {flags}')
"
</verification>

<success_criteria>
- pipeline/flags.py imports cleanly with no errors
- classify_hs6() returns list[str], not a tuple
- data/reference/flags_config.yaml has exactly 8 flag keys
- flags_config.yaml contains fertilizer flag with hs2_include: ["31"]
- No references to _tier_score, essentiality_score, or essentiality_tier in flags.py
- run_flags_scoring() output path is data/scoring/flags/flags_scores.parquet
</success_criteria>

<output>
After completion, create .planning/phases/07-pipeline-scoring-rework/07-02-SUMMARY.md
</output>
"""

# ============================================================
# Plan 07-03
# ============================================================
plan_03 = """\
---
phase: 07-pipeline-scoring-rework
plan: "03"
type: execute
wave: 2
depends_on:
  - "07-01"
  - "07-02"
files_modified:
  - pipeline/composite.py
  - pipeline/export.py
  - pipeline/__main__.py
  - pipeline.yaml
autonomous: true
requirements:
  - SCOR-06
  - SCOR-07
  - SCOR-08
must_haves:
  truths:
    - "composite.py DEFAULT_WEIGHTS has 'substitutability' key (not 'essentiality')"
    - "composite formula uses pl.col('global_export_hhi').sqrt() for the third term"
    - "composite output parquet has substitutability_score column, no essentiality_score"
    - "DuckDB products table has 'flags' VARCHAR[] column, no 'essentiality_tier'"
    - "DuckDB dependency_scores has 'substitutability_score', no 'essentiality_score'"
    - "__main__.py imports run_flags_scoring from pipeline.flags (not pipeline.essentiality)"
    - "pipeline.yaml weights section has 'substitutability: 0.30'"
    - "pipeline/essentiality.py and data/reference/essentiality_config.yaml are deleted"
  artifacts:
    - path: "pipeline/composite.py"
      provides: "Updated composite formula with sqrt(global_export_hhi)"
      contains: "substitutability"
    - path: "pipeline/export.py"
      provides: "DuckDB builder with flags/substitutability_score schema"
      contains: "flags_path"
  key_links:
    - from: "composite.py"
      to: "data/scoring/flags/flags_scores.parquet"
      via: "flags_path read in run_composite_scoring()"
      pattern: "scoring/flags/flags_scores"
    - from: "export.py::build_duckdb()"
      to: "data/scoring/flags/flags_scores.parquet"
      via: "flags_path parameter"
      pattern: "flags_path"
---

<objective>
Update composite.py and export.py to use the new flags schema. Wire __main__.py and
pipeline.yaml. Clean up old files.

Purpose: The pipeline can now run end-to-end with sqrt(global_export_hhi) as the
substitutability component. DuckDB contains the new schema with no tier columns.
Output: Working full pipeline (run without errors on existing scored Parquet).
</objective>

<execution_context>
@$HOME/.copilot/get-shit-done/workflows/execute-plan.md
@$HOME/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/07-pipeline-scoring-rework/07-CONTEXT.md
@.planning/STATE.md
</context>

<interfaces>
<!-- Target schemas the executor must implement. No interpretation needed. -->

composite.py NEW compute_composite() signature:
  compute_composite(hhi_df, georisk_df, flags_df, weights=None) -> pl.DataFrame
  (parameter rename: essentiality_df → flags_df)

composite.py input flags_df columns:
  [hs6, flags (List(Utf8)), global_export_hhi (Float64), crm_listed_since (Int64), hs22_only (Boolean)]
  (schema produced by pipeline/flags.py run_flags_scoring())

composite.py output columns (new):
  importer_iso3, concorded_hs6, year, exporter_iso3, value_usd, supplier_share, hhi,
  exporter_geo_risk, basket_geo_risk,
  global_export_hhi,          ← new (per-product, from flags join)
  substitutability_score,     ← new (= sqrt(global_export_hhi))
  flags,                      ← new (list[str], per-product)
  hs22_only,                  ← new (bool, per-product)
  crm_listed_since,           ← kept
  composite_score             ← kept (formula updated)

composite.py formula:
  substitutability_score = sqrt(global_export_hhi)
  composite_score = w["hhi"]*hhi + w["geo_risk"]*basket_geo_risk + w["substitutability"]*substitutability_score

composite.py fill value for missing global_export_hhi:
  substitutability_fill = float(flags_df["global_export_hhi"].median() ** 0.5)
  (computed once in compute_composite from the flags_df before join, not a module constant)

export.py fact table (dependency_scores) — NEW schema:
  importer_iso3, hs6, year, exporter_iso3, value_usd, supplier_share, hhi,
  exporter_geo_risk, basket_geo_risk,
  global_export_hhi,       ← new
  substitutability_score,  ← new (replaces essentiality_score)
  flags,                   ← new (VARCHAR[] / list column)
  hs22_only,               ← new (BOOLEAN)
  crm_listed_since,        ← kept
  composite_score          ← kept

export.py products dim — NEW schema:
  hs6, hs2, hs4, description, flags (VARCHAR[]), global_export_hhi (DOUBLE),
  hs22_only (BOOLEAN), crm_listed_since (INT64)
  REMOVED: essentiality_category, essentiality_tier, essentiality_score

export.py flags_df source: flags_path = scoring_dir / "flags" / "flags_scores.parquet"
  (was essentiality_path = scoring_dir / "essentiality" / "essentiality_scores.parquet")

pipeline.yaml weights section change:
  OLD: essentiality: 0.30
  NEW: substitutability: 0.30

__main__.py changes:
  OLD: from pipeline.essentiality import run_essentiality_scoring
  NEW: from pipeline.flags import run_flags_scoring
  OLD: ess_result = run_essentiality_scoring(config)
  NEW: ess_result = run_flags_scoring(config)

Files to delete (use git rm):
  pipeline/essentiality.py
  data/reference/essentiality_config.yaml
</interfaces>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Update composite.py for sqrt(global_export_hhi) formula</name>
  <files>pipeline/composite.py</files>
  <read_first>
    - pipeline/composite.py (MANDATORY — read the entire file before editing)
    - pipeline/flags.py (read to confirm the flags_df output schema)
  </read_first>
  <action>
Make these exact changes to pipeline/composite.py:

1. Module docstring: update formula line:
   OLD: "composite_score = w1×hhi + w2×basket_geo_risk + w3×essentiality_score"
   NEW: "composite_score = w1×hhi + w2×basket_geo_risk + w3×sqrt(global_export_hhi)"

2. DEFAULT_WEIGHTS dict: rename key:
   OLD: "essentiality": 0.30
   NEW: "substitutability": 0.30

3. Delete the _ESSENTIALITY_FILL constant line entirely.

4. compute_composite() function:
   a. Rename parameter: essentiality_df → flags_df
   b. Update docstring to reflect new parameter name and schema
   c. Replace the join with essentiality data:
      OLD:
        result = result.join(
            essentiality_df.select(
                ["hs6", "essentiality_score", "essentiality_tier", "crm_listed_since"]
            ).rename({"hs6": "concorded_hs6"}),
            on="concorded_hs6",
            how="left",
        ).with_columns(
            pl.col("essentiality_score").fill_null(_ESSENTIALITY_FILL),
            pl.col("essentiality_tier").fill_null("standard"),
        )
      NEW:
        # Compute fill value from median before join
        substitutability_fill = float((flags_df["global_export_hhi"].median() or 0.0) ** 0.5)
        result = result.join(
            flags_df.select(
                ["hs6", "global_export_hhi", "flags", "crm_listed_since", "hs22_only"]
            ).rename({"hs6": "concorded_hs6"}),
            on="concorded_hs6",
            how="left",
        ).with_columns(
            pl.col("global_export_hhi").fill_null(substitutability_fill ** 2),
            pl.col("flags").fill_null(pl.lit([])),
            pl.col("hs22_only").fill_null(False),
        )

   d. Add the substitutability_score derived column immediately after the join/fill:
        result = result.with_columns(
            pl.col("global_export_hhi").sqrt().alias("substitutability_score")
        )

   e. Replace basket_geo_risk computation (keep identical — no change needed there).

   f. Update composite score formula:
      OLD: w["essentiality"] * pl.col("essentiality_score")
      NEW: w["substitutability"] * pl.col("substitutability_score")

   g. Update final return SELECT statement:
      REMOVE: "essentiality_score", "essentiality_tier"
      ADD: "global_export_hhi", "substitutability_score", "flags", "hs22_only"
      KEEP: "crm_listed_since", "composite_score"
      Full column list:
        ["importer_iso3", "concorded_hs6", "year", "exporter_iso3",
         "value_usd", "supplier_share", "hhi",
         "exporter_geo_risk", "basket_geo_risk",
         "global_export_hhi", "substitutability_score", "flags", "hs22_only",
         "crm_listed_since", "composite_score"]

5. run_composite_scoring():
   a. Change essentiality_path line:
      OLD: essentiality_path = scoring_dir / "essentiality" / "essentiality_scores.parquet"
      NEW: flags_path = scoring_dir / "flags" / "flags_scores.parquet"
   b. Change existence check:
      OLD: if not essentiality_path.exists():
           raise FileNotFoundError(f"Essentiality Parquet not found: {essentiality_path}...")
      NEW: if not flags_path.exists():
           raise FileNotFoundError(f"Flags Parquet not found: {flags_path}. Run flags scoring first.")
   c. Change read:
      OLD: essentiality_df = pl.read_parquet(essentiality_path)
      NEW: flags_df = pl.read_parquet(flags_path)
   d. Update compute_composite call:
      OLD: result = compute_composite(hhi_df, georisk_df, essentiality_df, weights_cfg)
      NEW: result = compute_composite(hhi_df, georisk_df, flags_df, weights_cfg)
  </action>
  <verify>
    <automated>python -c "from pipeline.composite import compute_composite, DEFAULT_WEIGHTS; assert 'substitutability' in DEFAULT_WEIGHTS; assert 'essentiality' not in DEFAULT_WEIGHTS; print('OK')"</automated>
  </verify>
  <done>
    - DEFAULT_WEIGHTS has "substitutability" key, not "essentiality"
    - grep -c "essentiality_score\|essentiality_tier\|_ESSENTIALITY_FILL" pipeline/composite.py returns 0
    - grep "substitutability_score\|global_export_hhi" pipeline/composite.py confirms both present
    - python -c "from pipeline.composite import compute_composite, run_composite_scoring; print('OK')"
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Update export.py with new DuckDB schema</name>
  <files>pipeline/export.py</files>
  <read_first>
    - pipeline/export.py (MANDATORY — read the entire file before editing)
    - pipeline/flags.py (confirm flags_scores.parquet schema: hs6, flags, global_export_hhi, crm_listed_since, hs22_only)
  </read_first>
  <action>
Make these exact changes to pipeline/export.py:

1. build_duckdb() function signature:
   Change parameter: essentiality_path: Path → flags_path: Path
   Update docstring to reflect the rename.

2. Fact table (dependency_scores) SQL:
   Replace the CREATE TABLE AS SELECT block. The composite parquet now has these NEW columns:
   global_export_hhi, substitutability_score, flags, hs22_only.
   It still has: importer_iso3, concorded_hs6 (→ hs6), year, exporter_iso3, value_usd,
                 supplier_share, hhi, exporter_geo_risk, basket_geo_risk,
                 crm_listed_since, composite_score.
   REMOVE from SELECT: essentiality_score, essentiality_tier.
   ADD to SELECT: global_export_hhi, substitutability_score, flags, hs22_only.
   
   New CREATE TABLE statement:
   conn.execute("DROP TABLE IF EXISTS dependency_scores")
   conn.execute(f"""
       CREATE TABLE dependency_scores AS
       SELECT
           importer_iso3,
           concorded_hs6  AS hs6,
           year,
           exporter_iso3,
           value_usd,
           supplier_share,
           hhi,
           exporter_geo_risk,
           basket_geo_risk,
           global_export_hhi,
           substitutability_score,
           flags,
           hs22_only,
           crm_listed_since,
           composite_score
       FROM read_parquet('{composite_glob}', hive_partitioning = true)
   """)

3. Products dimension:
   a. Change the parquet read:
      OLD: ess_df = pl.read_parquet(essentiality_path)
      NEW: flags_df = pl.read_parquet(flags_path)
   
   b. Change the join with descriptions:
      OLD: products_df = ess_df.join(desc_df, on="hs6", how="left")
      NEW: products_df = flags_df.join(desc_df, on="hs6", how="left")
   
   c. Change products_df construction:
      OLD .with_columns / .select block that includes essentiality_category, essentiality_tier, essentiality_score.
      NEW:
        products_df = products_df.with_columns([
            pl.col("hs6").str.slice(0, 2).alias("hs2"),
            pl.col("hs6").str.slice(0, 4).alias("hs4"),
            pl.col("description").fill_null(""),
            pl.col("global_export_hhi").cast(pl.Float64),
            pl.col("crm_listed_since").cast(pl.Int64, strict=False),
            pl.col("hs22_only").fill_null(False),
        ]).select([
            "hs6", "hs2", "hs4", "description",
            "flags",
            "global_export_hhi",
            "hs22_only",
            "crm_listed_since",
        ])
   
   d. Update the conn.register and CREATE TABLE:
      OLD: conn.execute("""
               CREATE TABLE products AS
               SELECT hs6, hs2, hs4, description, essentiality_category,
                      essentiality_tier, essentiality_score, global_export_hhi, crm_listed_since
               FROM _products
           """)
      NEW: conn.execute("""
               CREATE TABLE products AS
               SELECT hs6, hs2, hs4, description, flags,
                      global_export_hhi, hs22_only, crm_listed_since
               FROM _products
           """)

4. run_duckdb_export():
   a. Change essentiality_path:
      OLD: essentiality_path = scoring_dir / "essentiality" / "essentiality_scores.parquet"
      NEW: flags_path = scoring_dir / "flags" / "flags_scores.parquet"
   b. Update build_duckdb call:
      OLD: build_duckdb(duckdb_path, composite_dir, georisk_path, essentiality_path, reference_dir, raw_dir=raw_dir)
      NEW: build_duckdb(duckdb_path, composite_dir, georisk_path, flags_path, reference_dir, raw_dir=raw_dir)
   c. Update existence check:
      OLD: essentiality_path reference
      NEW: flags_path reference (if there is such a check)
  </action>
  <verify>
    <automated>python -c "from pipeline.export import build_duckdb, run_duckdb_export; print('OK')"</automated>
  </verify>
  <done>
    - pipeline/export.py imports cleanly
    - grep -c "essentiality_score\|essentiality_tier\|essentiality_category\|essentiality_path" pipeline/export.py returns 0
    - grep "flags_path\|substitutability_score\|flags" pipeline/export.py confirms all three present
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Wire __main__.py, pipeline.yaml, and clean up old files</name>
  <files>pipeline/__main__.py, pipeline.yaml</files>
  <read_first>
    - pipeline/__main__.py (read lines 1-20 for import block, and Stage 6 section around line 135)
    - pipeline.yaml (read scoring.weights section)
  </read_first>
  <action>
1. pipeline/__main__.py:
   a. Change import line 15:
      OLD: from pipeline.essentiality import run_essentiality_scoring
      NEW: from pipeline.flags import run_flags_scoring

   b. Stage 6 comment and call (around lines 135-138):
      OLD: # Stage 6: Essentiality scoring
           logger.info("Stage 6: Computing product essentiality scores...")
           ess_result = run_essentiality_scoring(config)
           scoring_summary["essentiality"] = ess_result
      NEW: # Stage 6: Product flags and global HHI
           logger.info("Stage 6: Computing product flags and global export HHI...")
           ess_result = run_flags_scoring(config)
           scoring_summary["flags"] = ess_result

2. pipeline.yaml:
   In the scoring.weights section, change:
   OLD:   essentiality: 0.30
   NEW:   substitutability: 0.30

3. Clean up old files with git rm:
   git rm pipeline/essentiality.py
   git rm data/reference/essentiality_config.yaml
  </action>
  <verify>
    <automated>python -c "import pipeline.__main__; print('OK')" 2>&1 | head -3</automated>
  </verify>
  <done>
    - grep "run_flags_scoring" pipeline/__main__.py confirms import updated
    - grep "substitutability" pipeline.yaml confirms weights key updated
    - test ! -f pipeline/essentiality.py confirms deletion
    - test ! -f data/reference/essentiality_config.yaml confirms deletion
    - python -c "from pipeline.__main__ import main; print('OK')" exits 0
  </done>
</task>

</tasks>

<verification>
python -c "
from pipeline.composite import DEFAULT_WEIGHTS
from pipeline.export import build_duckdb
from pipeline.__main__ import main
import yaml
with open('pipeline.yaml') as f: cfg = yaml.safe_load(f)
assert 'substitutability' in cfg['scoring']['weights'], 'pipeline.yaml not updated'
assert 'essentiality' not in DEFAULT_WEIGHTS, 'DEFAULT_WEIGHTS still has essentiality key'
print('All wiring checks pass')
"
test ! -f pipeline/essentiality.py && echo 'essentiality.py deleted OK'
test ! -f data/reference/essentiality_config.yaml && echo 'essentiality_config.yaml deleted OK'
</verification>

<success_criteria>
- composite.py uses substitutability key and sqrt(global_export_hhi) formula
- export.py products table has flags, global_export_hhi, hs22_only — no essentiality_* columns
- export.py fact table has substitutability_score — no essentiality_score or essentiality_tier
- __main__.py imports from pipeline.flags not pipeline.essentiality
- pipeline.yaml has substitutability: 0.30 in weights
- pipeline/essentiality.py and data/reference/essentiality_config.yaml no longer exist
- Full pipeline.py import chain resolves without errors
</success_criteria>

<output>
After completion, create .planning/phases/07-pipeline-scoring-rework/07-03-SUMMARY.md
</output>
"""

# ============================================================
# Plan 07-04
# ============================================================
plan_04 = """\
---
phase: 07-pipeline-scoring-rework
plan: "04"
type: execute
wave: 3
depends_on:
  - "07-03"
files_modified:
  - dashboard/data.py
  - dashboard/pages/country.py
  - dashboard/pages/product.py
autonomous: true
requirements:
  - SCOR-08
must_haves:
  truths:
    - "dashboard/data.py has no SQL references to essentiality_score or essentiality_tier"
    - "get_product_scores() returns dicts with 'substitutability_score' and 'flags' keys"
    - "get_country_summary() returns dict with 'avg_substitutability' and 'critical_count' keys"
    - "critical_count uses flags column (crm_listed or strategic_mineral) not a tier check"
    - "dashboard/pages/country.py has no references to p['essentiality_score'] or p['essentiality_tier']"
    - "dashboard/pages/product.py has no references to trend['essentiality_score']"
    - "Dashboard launches and serves country/product pages without DuckDB ColumnNotFound errors"
  artifacts:
    - path: "dashboard/data.py"
      provides: "DuckDB queries updated for v2 schema"
      contains: "substitutability_score"
    - path: "dashboard/pages/country.py"
      provides: "Country page callbacks using new schema"
      contains: "substitutability_score"
  key_links:
    - from: "dashboard/data.py::get_product_scores()"
      to: "dashboard/pages/country.py callback"
      via: "returns dicts with 'substitutability_score' and 'flags' keys"
      pattern: "substitutability_score"
    - from: "dashboard/data.py::get_country_summary()"
      to: "score summary cards in country.py"
      via: "returns avg_substitutability key (not avg_essentiality)"
      pattern: "avg_substitutability"
---

<objective>
Update the dashboard data layer (data.py) and page callbacks (country.py, product.py)
to use the v2 DuckDB schema. Removes all references to essentiality_score/tier.

Purpose: Meets Phase 7 success criterion 5 — "dashboard launches without ColumnNotFound errors".
This is a surgical rename pass, not a UI redesign. Flag-based critical_count replaces
the old tier-based check.
Output: Dashboard that renders country and product views correctly with v2 DuckDB.
</objective>

<execution_context>
@$HOME/.copilot/get-shit-done/workflows/execute-plan.md
@$HOME/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/07-pipeline-scoring-rework/07-CONTEXT.md
@.planning/STATE.md
</context>

<interfaces>
<!-- V2 DuckDB schema the dashboard now queries. These are the authoritative column names. -->

dependency_scores fact table (v2):
  importer_iso3, hs6, year, exporter_iso3, value_usd, supplier_share, hhi,
  exporter_geo_risk, basket_geo_risk,
  global_export_hhi DOUBLE,
  substitutability_score DOUBLE,    ← replaces essentiality_score
  flags VARCHAR[],                  ← list of flag strings
  hs22_only BOOLEAN,
  crm_listed_since INT64,
  composite_score DOUBLE

products dim (v2):
  hs6, hs2, hs4, description,
  flags VARCHAR[],                  ← list of flag strings
  global_export_hhi DOUBLE,
  hs22_only BOOLEAN,
  crm_listed_since INT64
  (REMOVED: essentiality_category, essentiality_tier, essentiality_score)

DuckDB list function for flag check:
  list_contains(flags, 'crm_listed')    ← checks if 'crm_listed' is in the flags array
  list_contains(flags, 'strategic_mineral')

Mapping for all changed function return keys:
  get_product_scores():
    OLD cols: ["hs6","description","essentiality_tier","hhi","basket_geo_risk","essentiality_score","composite_score"]
    NEW cols: ["hs6","description","flags","hhi","basket_geo_risk","substitutability_score","composite_score"]
    SQL change: SELECT ds.essentiality_tier → COALESCE(p.flags, []) AS flags (requires LEFT JOIN products p)
                SELECT ds.essentiality_score → ds.substitutability_score

  get_country_summary():
    OLD return keys: avg_hhi, avg_geo_risk, avg_essentiality, avg_composite, product_count, critical_count, high_risk_count
    NEW return keys: avg_hhi, avg_geo_risk, avg_substitutability, avg_composite, product_count, critical_count, high_risk_count
    SQL: AVG(essentiality_score) → AVG(substitutability_score)
         SUM(CASE WHEN essentiality_tier='critical' THEN 1 END) → 
           Use a JOIN to products:
           SUM(CASE WHEN list_contains(p.flags, 'crm_listed') 
                         OR list_contains(p.flags, 'strategic_mineral') 
                    THEN 1 ELSE 0 END) AS critical_count

  get_importer_scores():
    OLD cols: ["importer_iso3","importer_name","hhi","basket_geo_risk","essentiality_score","composite_score","essentiality_tier"]
    NEW cols: ["importer_iso3","importer_name","hhi","basket_geo_risk","substitutability_score","composite_score","flags"]
    SQL: rename columns accordingly, get flags via JOIN products

  get_product_summary():
    OLD return keys: avg_hhi, avg_geo_risk, avg_essentiality, avg_composite, importer_count, high_risk_count
    NEW return keys: avg_hhi, avg_geo_risk, avg_substitutability, avg_composite, importer_count, high_risk_count
    SQL: AVG(essentiality_score) → AVG(substitutability_score)

  get_score_trend():
    OLD cols: ["year","composite_score","hhi","basket_geo_risk","essentiality_score"]
    NEW cols: ["year","composite_score","hhi","basket_geo_risk","substitutability_score"]

  get_product_trend():
    OLD cols: ["year","composite_score","hhi","basket_geo_risk","essentiality_score"]
    NEW cols: ["year","composite_score","hhi","basket_geo_risk","substitutability_score"]

country.py changes:
  p["essentiality_score"]  → p["substitutability_score"]
  p["essentiality_tier"]   → p.get("flags", [])  (it's now a list)
  critical_count = sum(1 for p in products if p["essentiality_tier"] == "critical")
    → critical_count = sum(1 for p in products
                           if any(f in (p.get("flags") or [])
                                  for f in ["crm_listed", "strategic_mineral"]))
  summary["avg_essentiality"] → summary["avg_substitutability"]

product.py changes:
  trend_by_year[y]["essentiality_score"] → trend_by_year[y]["substitutability_score"]
  summary["avg_essentiality"] → summary["avg_substitutability"]
  AG Grid: "field": "essentiality_score" → "field": "substitutability_score"
           "field": "essentiality_tier"  → "field": "flags"
</interfaces>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Update dashboard/data.py SQL queries for v2 schema</name>
  <files>dashboard/data.py</files>
  <read_first>
    - dashboard/data.py (MANDATORY — read the entire file; there are 6+ functions to update)
  </read_first>
  <action>
Update every function in dashboard/data.py that references essentiality_score or essentiality_tier:

SYSTEMATIC RENAME RULES (apply throughout the file):
  - SQL column "ds.essentiality_score" or "essentiality_score" → "ds.substitutability_score" or "substitutability_score"
  - SQL column "ds.essentiality_tier" or "essentiality_tier" → drop from SELECT or replace with flags
  - Python cols list "essentiality_score" → "substitutability_score"
  - Python cols list "essentiality_tier" → "flags"
  - Return dict key "avg_essentiality" → "avg_substitutability"
  - Fallback dict "avg_essentiality": 0 → "avg_substitutability": 0

SPECIFIC FUNCTION CHANGES:

1. get_product_scores():
   - Add LEFT JOIN products p ON ds.hs6 = p.hs6 to the query
   - Change SELECT to: ds.hs6, COALESCE(p.description,'') AS description,
     COALESCE(p.flags, []) AS flags, ds.hhi, ds.basket_geo_risk,
     ds.substitutability_score, ds.composite_score
   - Update cols list accordingly

2. get_country_summary():
   - Change the inner SELECT to include flags:
     SELECT DISTINCT hs6, hhi, basket_geo_risk, substitutability_score, composite_score
     FROM dependency_scores WHERE importer_iso3 = ? AND year = ?
   - Change outer query to JOIN products for critical_count:
     Restructure as:
       SELECT
           AVG(sub.hhi) AS avg_hhi,
           AVG(sub.basket_geo_risk) AS avg_geo_risk,
           AVG(sub.substitutability_score) AS avg_substitutability,
           AVG(sub.composite_score) AS avg_composite,
           COUNT(*) AS product_count,
           SUM(CASE WHEN list_contains(p.flags, 'crm_listed')
                         OR list_contains(p.flags, 'strategic_mineral')
                    THEN 1 ELSE 0 END) AS critical_count,
           SUM(CASE WHEN sub.composite_score > 0.7 THEN 1 ELSE 0 END) AS high_risk_count
       FROM (
           SELECT DISTINCT hs6, hhi, basket_geo_risk, substitutability_score, composite_score
           FROM dependency_scores
           WHERE importer_iso3 = ? AND year = ?
       ) sub
       LEFT JOIN products p ON sub.hs6 = p.hs6
   - Update return dict keys: "avg_essentiality" → "avg_substitutability"

3. get_importer_scores():
   - Change inner SELECT: drop essentiality_tier, add flags via JOIN
   - Add LEFT JOIN countries AND LEFT JOIN products to outer query
   - Change cols list to include "flags" instead of "essentiality_tier"
   - Change "essentiality_score" → "substitutability_score"

4. get_product_summary():
   - Change "AVG(essentiality_score) AS avg_essentiality" → "AVG(substitutability_score) AS avg_substitutability"
   - Update return dict keys

5. get_score_trend():
   - "essentiality_score" → "substitutability_score" in SQL and cols list

6. get_product_trend():
   - "essentiality_score" → "substitutability_score" in SQL and cols list (x2)

VERIFY after each function: ensure no "essentiality" string remains in data.py
  </action>
  <verify>
    <automated>grep -c "essentiality" dashboard/data.py</automated>
  </verify>
  <done>
    - grep -c "essentiality" dashboard/data.py returns 0
    - grep -c "substitutability_score" dashboard/data.py returns >= 6 (one per function)
    - python -c "from dashboard.data import get_product_scores, get_country_summary; print('OK')"
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Update country.py and product.py callbacks</name>
  <files>dashboard/pages/country.py, dashboard/pages/product.py</files>
  <read_first>
    - dashboard/pages/country.py (MANDATORY — read the entire file)
    - dashboard/pages/product.py (MANDATORY — read the entire file)
  </read_first>
  <action>
Apply systematic renaming in BOTH files.

In dashboard/pages/country.py:

1. Find: p["essentiality_score"]
   Replace with: p["substitutability_score"]
   (occurs in weight recalculation callbacks and radar chart data)

2. Find: p["essentiality_tier"]
   This is used in:
     critical_count = sum(1 for p in products if p["essentiality_tier"] == "critical")
   Replace with:
     critical_count = sum(
         1 for p in products
         if any(f in (p.get("flags") or []) for f in ["crm_listed", "strategic_mineral"])
     )

3. Find: p.get("essentiality_tier", ...) or product["essentiality_tier"]
   For display strings like: f"Tier: {product.get('essentiality_tier', '—')} · "
   Replace with: f"Flags: {', '.join(product.get('flags') or []) or '—'} · "

4. Find: summary["avg_essentiality"] or similar summary key access
   Replace with: summary["avg_substitutability"]

5. Find: w_ess * p["essentiality_score"] in weight-adjusted composite calculations
   Replace with: w_ess * p["substitutability_score"]

6. Radar chart data (r=[..., product["essentiality_score"]]):
   Replace "essentiality_score" with "substitutability_score"

7. AG Grid column definitions:
   OLD: {"field": "essentiality_score", ...}
   NEW: {"field": "substitutability_score", ...}
   OLD: {"field": "essentiality_tier", ...}
   NEW: {"field": "flags", ...}

In dashboard/pages/product.py:

1. trend_by_year[y]["essentiality_score"] → trend_by_year[y]["substitutability_score"]
2. summary["avg_essentiality"] → summary["avg_substitutability"]
3. AG Grid: "essentiality_score" → "substitutability_score", "essentiality_tier" → "flags"
4. Any p["essentiality_score"] references → p["substitutability_score"]

After both files are updated:
- grep -c "essentiality" dashboard/pages/country.py should return 0
- grep -c "essentiality" dashboard/pages/product.py should return 0
  </action>
  <verify>
    <automated>grep -c "essentiality" dashboard/pages/country.py dashboard/pages/product.py</automated>
  </verify>
  <done>
    - grep returns 0 for both files
    - python -c "from dashboard.pages import country, product; print('OK')"
    - python -c "from dashboard.app import server; print('Dashboard app imports OK')"
  </done>
</task>

</tasks>

<verification>
# No essentiality references anywhere in dashboard code
grep -r "essentiality" dashboard/ --include="*.py" | grep -v __pycache__

# All imports clean
python -c "
from dashboard.data import (get_product_scores, get_country_summary,
    get_importer_scores, get_product_summary, get_score_trend, get_product_trend)
from dashboard.pages import country, product
print('All dashboard imports OK')
"

# Check return key names are correct
python -c "
from dashboard.data import get_country_summary
import inspect
src = inspect.getsource(get_country_summary)
assert 'avg_substitutability' in src
assert 'avg_essentiality' not in src
print('get_country_summary return keys OK')
"
</verification>

<success_criteria>
- Zero occurrences of "essentiality" in dashboard/data.py, country.py, product.py
- Dashboard app imports without errors
- get_country_summary() returns "avg_substitutability" key
- get_product_scores() returns "substitutability_score" and "flags" keys
- critical_count uses flags-based logic (crm_listed or strategic_mineral)
- Dashboard can be started (python -m dashboard or gunicorn) without ColumnNotFound errors
</success_criteria>

<output>
After completion, create .planning/phases/07-pipeline-scoring-rework/07-04-SUMMARY.md
</output>
"""

# Write all plans
plans = {
    "07-01-PLAN.md": plan_01,
    "07-02-PLAN.md": plan_02,
    "07-03-PLAN.md": plan_03,
    "07-04-PLAN.md": plan_04,
}

for filename, content in plans.items():
    path = phase_dir / filename
    path.write_text(content)
    print(f"Written: {path}")

print("All 4 plans written.")
