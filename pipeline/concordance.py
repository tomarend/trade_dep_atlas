"""HS concordance: map any-revision HS6 codes to HS2022 target with hierarchy."""

import csv
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger


@dataclass
class ConcordedProduct:
    """Result of concordance lookup for a single HS6 code."""

    original_hs6: str
    concorded_hs6: str
    hs2: str
    hs4: str
    description: str
    category: str
    concordance_flag: str  # "unchanged", "mapped", "split", "merged", "unmapped"


@dataclass
class Concordance:
    """HS concordance lookup tables."""

    forward_map: dict[str, list[str]] = field(default_factory=dict)  # source → targets
    reverse_map: dict[str, list[str]] = field(default_factory=dict)  # target → sources
    descriptions: dict[str, tuple[str, str]] = field(default_factory=dict)  # hs6 → (desc, category)
    source_revision: str = "H4"
    target_revision: str = "H6"


def load_product_descriptions(reference_dir: Path) -> dict[str, tuple[str, str]]:
    """Read hs_product_descriptions.csv. Returns hs6 → (description, category)."""
    desc_path = reference_dir / "hs_product_descriptions.csv"
    descriptions: dict[str, tuple[str, str]] = {}

    if not desc_path.exists():
        logger.warning(f"Product descriptions file not found: {desc_path}")
        return descriptions

    with open(desc_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hs6 = row.get("hs6", "").strip()
            desc = row.get("description", "").strip()
            cat = row.get("category", "").strip()
            if hs6:
                descriptions[hs6] = (desc, cat)

    logger.info(f"Loaded {len(descriptions)} product descriptions")
    return descriptions


def load_concordance(
    reference_dir: Path,
    source_revision: str = "H4",
    target_revision: str = "H6",
) -> Concordance:
    """Load HS concordance tables from reference_dir.

    If concordance CSV files exist in reference_dir/concordance/, they are parsed
    to build forward and reverse maps. Otherwise, an identity mapping is used
    (every code maps to itself) — this lets the pipeline run without concordance
    tables for development/testing.
    """
    descriptions = load_product_descriptions(reference_dir)

    concordance_dir = reference_dir / "concordance"
    forward_map: dict[str, list[str]] = {}
    reverse_map: dict[str, list[str]] = {}

    if concordance_dir.exists():
        csv_files = list(concordance_dir.glob("*.csv"))
        if csv_files:
            for csv_file in csv_files:
                _parse_concordance_csv(csv_file, forward_map, reverse_map)
            logger.info(
                f"Loaded concordance from {len(csv_files)} files: "
                f"{len(forward_map)} source codes → {len(reverse_map)} target codes"
            )
        else:
            logger.warning(f"No concordance CSV files in {concordance_dir} — using identity mapping")
    else:
        logger.warning(f"Concordance directory not found: {concordance_dir} — using identity mapping")

    return Concordance(
        forward_map=forward_map,
        reverse_map=reverse_map,
        descriptions=descriptions,
        source_revision=source_revision,
        target_revision=target_revision,
    )


def _parse_concordance_csv(csv_path: Path, forward_map: dict, reverse_map: dict):
    """Parse a WITS-style concordance CSV into forward and reverse maps.

    Expected columns: source_hs6 (or HS_source), target_hs6 (or HS_target).
    Tries multiple column naming conventions.
    """
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return

        # Detect column names
        fields = [fn.strip().lower() for fn in reader.fieldnames]
        source_col = None
        target_col = None

        for fn in reader.fieldnames:
            fl = fn.strip().lower()
            if fl in ("source_hs6", "hs_source", "from_hs6", "original"):
                source_col = fn
            elif fl in ("target_hs6", "hs_target", "to_hs6", "concorded"):
                target_col = fn

        # Fall back to first two columns if no recognizable names
        if source_col is None or target_col is None:
            cols = reader.fieldnames[:2]
            if len(cols) >= 2:
                source_col, target_col = cols[0], cols[1]
            else:
                return

        for row in reader:
            source = row.get(source_col, "").strip()
            target = row.get(target_col, "").strip()
            if not source or not target:
                continue

            # Pad to 6 digits
            source = source.zfill(6)
            target = target.zfill(6)

            forward_map.setdefault(source, [])
            if target not in forward_map[source]:
                forward_map[source].append(target)

            reverse_map.setdefault(target, [])
            if source not in reverse_map[target]:
                reverse_map[target].append(source)


def apply_concordance(hs6_code: str, concordance: Concordance) -> ConcordedProduct:
    """Apply concordance to a single HS6 code.

    Returns ConcordedProduct with the target code and a concordance flag.
    """
    targets = concordance.forward_map.get(hs6_code)

    if targets is None:
        # Not in concordance table — unmapped, keep original
        concorded = hs6_code
        flag = "unmapped"
    elif len(targets) == 1:
        concorded = targets[0]
        flag = "unchanged" if concorded == hs6_code else "mapped"
    else:
        # One-to-many split: pick first alphabetically
        concorded = sorted(targets)[0]
        flag = "split"

    # Check for many-to-one merge (multiple sources → same target)
    if flag == "mapped" and concorded in concordance.reverse_map:
        sources = concordance.reverse_map[concorded]
        if len(sources) > 1:
            flag = "merged"

    hs2 = concorded[:2]
    hs4 = concorded[:4]

    desc_info = concordance.descriptions.get(concorded, ("Unknown product", "unknown"))
    description, category = desc_info

    return ConcordedProduct(
        original_hs6=hs6_code,
        concorded_hs6=concorded,
        hs2=hs2,
        hs4=hs4,
        description=description,
        category=category,
        concordance_flag=flag,
    )


def build_concordance_polars_map(concordance: Concordance) -> dict[str, str]:
    """Build a flat dict mapping every known source HS6 → single target HS6.

    For one-to-many splits, picks the first target alphabetically (same rule as apply_concordance).
    Used for vectorized Polars replace operations.
    """
    flat: dict[str, str] = {}
    for source, targets in concordance.forward_map.items():
        flat[source] = sorted(targets)[0] if len(targets) > 1 else targets[0]
    return flat


def validate_concordance(concordance: Concordance) -> list[str]:
    """Return list of warning messages about concordance quality."""
    warnings: list[str] = []

    # Count mapping types
    splits = sum(1 for targets in concordance.forward_map.values() if len(targets) > 1)
    merges = sum(1 for sources in concordance.reverse_map.values() if len(sources) > 1)

    if splits > 0:
        warnings.append(f"One-to-many splits: {splits} source codes map to multiple targets")
    if merges > 0:
        warnings.append(f"Many-to-one merges: {merges} target codes have multiple sources")

    # Spot check critical products
    critical_products = ["280461", "260300", "854231"]  # lithium, copper, semiconductors
    if concordance.forward_map:
        for hs6 in critical_products:
            if hs6 not in concordance.forward_map:
                warnings.append(f"Critical product {hs6} not found in concordance forward_map")

    # Count products in descriptions but not in concordance
    if concordance.forward_map:
        unmapped_in_desc = sum(
            1 for hs6 in concordance.descriptions if hs6 not in concordance.forward_map
        )
        if unmapped_in_desc > 0:
            warnings.append(f"Unmapped codes: {unmapped_in_desc} codes in descriptions but not in concordance")

    total_mappings = len(concordance.forward_map)
    if total_mappings == 0:
        warnings.append("No concordance mappings loaded — using identity mapping")

    logger.info(f"Concordance validation: {len(warnings)} warnings, {total_mappings} total mappings")
    return warnings
