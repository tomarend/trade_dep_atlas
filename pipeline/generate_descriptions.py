"""Generate comprehensive HS6 product descriptions from BACI product_codes files.

Merges all HS revision files (HS92→HS22), with later revisions taking precedence.
Preserves hand-curated entries from existing hs_product_descriptions.csv.
Derives categories from essentiality/CRM data where available, falls back to HS2 chapter mapping.
"""

from pathlib import Path

import polars as pl
from loguru import logger

# HS2 chapter → broad category mapping (UN trade classification)
_HS2_CATEGORY: dict[str, str] = {
    # Live animals, animal products (01-05)
    "01": "food", "02": "food", "03": "food", "04": "food", "05": "food",
    # Vegetable products (06-14)
    "06": "food", "07": "food", "08": "food", "09": "food", "10": "food",
    "11": "food", "12": "food", "13": "food", "14": "food",
    # Fats and oils (15)
    "15": "food",
    # Prepared foodstuffs, beverages, tobacco (16-24)
    "16": "food", "17": "food", "18": "food", "19": "food", "20": "food",
    "21": "food", "22": "food", "23": "food", "24": "food",
    # Mineral products (25-27)
    "25": "minerals", "26": "critical_minerals", "27": "energy",
    # Chemicals (28-38)
    "28": "chemicals", "29": "chemicals", "30": "pharma", "31": "chemicals",
    "32": "chemicals", "33": "chemicals", "34": "chemicals", "35": "chemicals",
    "36": "chemicals", "37": "chemicals", "38": "chemicals",
    # Plastics, rubber (39-40)
    "39": "plastics", "40": "plastics",
    # Hides, leather (41-43)
    "41": "textiles", "42": "textiles", "43": "textiles",
    # Wood, cork (44-46)
    "44": "wood", "45": "wood", "46": "wood",
    # Paper (47-49)
    "47": "paper", "48": "paper", "49": "paper",
    # Textiles (50-63)
    "50": "textiles", "51": "textiles", "52": "textiles", "53": "textiles",
    "54": "textiles", "55": "textiles", "56": "textiles", "57": "textiles",
    "58": "textiles", "59": "textiles", "60": "textiles", "61": "textiles",
    "62": "textiles", "63": "textiles",
    # Footwear, headgear (64-67)
    "64": "footwear", "65": "footwear", "66": "footwear", "67": "footwear",
    # Stone, cement, ceramics, glass (68-70)
    "68": "construction", "69": "construction", "70": "construction",
    # Precious stones, metals (71)
    "71": "precious_metals",
    # Iron, steel, base metals (72-83)
    "72": "metals", "73": "metals", "74": "metals", "75": "metals",
    "76": "metals", "78": "metals", "79": "metals", "80": "metals",
    "81": "metals", "82": "metals", "83": "metals",
    # Machinery (84)
    "84": "machinery",
    # Electrical equipment (85)
    "85": "electronics",
    # Vehicles (86-89)
    "86": "transport", "87": "transport", "88": "aerospace", "89": "transport",
    # Instruments (90-92)
    "90": "instruments", "91": "instruments", "92": "instruments",
    # Arms (93)
    "93": "arms",
    # Miscellaneous manufactured (94-96)
    "94": "manufactured", "95": "manufactured", "96": "manufactured",
    # Art, antiques (97)
    "97": "manufactured",
    # Special (99)
    "99": "other",
}

# Revision priority: later revisions take precedence
_REVISION_PRIORITY = ["HS92", "HS96", "HS02", "HS07", "HS12", "HS17", "HS22"]


def _extract_revision(filename: str) -> str:
    """Extract HS revision tag from filename like 'product_codes_HS22_V202601.csv'."""
    for rev in _REVISION_PRIORITY:
        if rev in filename:
            return rev
    return "HS92"


def generate_descriptions(
    raw_dir: Path,
    reference_dir: Path,
) -> int:
    """Generate comprehensive hs_product_descriptions.csv.

    Returns the total number of descriptions written.
    """
    desc_path = reference_dir / "hs_product_descriptions.csv"

    # 1. Load existing hand-curated entries (preserve them)
    curated: dict[str, tuple[str, str]] = {}
    if desc_path.exists():
        existing = pl.read_csv(desc_path, schema_overrides={"hs6": pl.Utf8})
        for row in existing.iter_rows(named=True):
            hs6 = str(row["hs6"]).zfill(6)
            curated[hs6] = (row.get("description", ""), row.get("category", ""))
        logger.info(f"Preserved {len(curated)} hand-curated descriptions")

    # 2. Load category sources: essentiality + CRM
    category_lookup: dict[str, str] = {}
    ess_path = reference_dir / "essentiality_hs6.csv"
    if ess_path.exists():
        ess = pl.read_csv(ess_path, schema_overrides={"hs6": pl.Utf8})
        for row in ess.iter_rows(named=True):
            hs6 = str(row["hs6"]).zfill(6)
            category_lookup[hs6] = row.get("category", "")

    crm_path = reference_dir / "crm_hs6_mapping.csv"
    if crm_path.exists():
        crm = pl.read_csv(crm_path, schema_overrides={"hs6": pl.Utf8})
        for row in crm.iter_rows(named=True):
            hs6 = str(row["hs6"]).zfill(6)
            if hs6 not in category_lookup:
                material = row.get("material", "critical_minerals")
                category_lookup[hs6] = material.lower().replace(" ", "_")

    # 3. Read all BACI product_codes files, ordered by revision priority
    product_files = sorted(raw_dir.glob("product_codes_HS*.csv"))
    if not product_files:
        logger.warning(f"No product_codes_HS*.csv files found in {raw_dir}")
        return 0

    # Group by revision, process in priority order (latest wins)
    all_products: dict[str, str] = {}  # hs6 → description
    for rev in _REVISION_PRIORITY:
        rev_files = [f for f in product_files if rev in f.name]
        for f in rev_files:
            df = pl.read_csv(f, schema_overrides={"code": pl.Utf8})
            for row in df.iter_rows(named=True):
                code = str(row["code"]).strip()
                # Filter to 6-digit numeric codes only
                if not code.isdigit():
                    continue
                code = code.zfill(6)
                if len(code) != 6:
                    continue
                desc = row.get("description", "").strip()
                if desc:
                    all_products[code] = desc

    logger.info(f"Found {len(all_products)} unique HS6 codes across all revisions")

    # 4. Build final output: curated entries take precedence, then BACI descriptions
    rows: list[dict[str, str]] = []
    all_hs6_codes = sorted(set(list(curated.keys()) + list(all_products.keys())))

    for hs6 in all_hs6_codes:
        if hs6 in curated:
            desc, cat = curated[hs6]
        else:
            desc = all_products.get(hs6, "")
            cat = ""

        # Resolve category: curated > essentiality/CRM > HS2 chapter
        if not cat:
            cat = category_lookup.get(hs6, "")
        if not cat:
            hs2 = hs6[:2]
            cat = _HS2_CATEGORY.get(hs2, "other")

        rows.append({"hs6": hs6, "description": desc, "category": cat})

    # 5. Write output
    out_df = pl.DataFrame(rows, schema={"hs6": pl.Utf8, "description": pl.Utf8, "category": pl.Utf8})
    out_df.write_csv(desc_path)
    logger.info(f"Wrote {len(out_df)} product descriptions to {desc_path}")

    return len(out_df)
