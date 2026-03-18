"""Country code mapping: BACI numeric → ISO3 with metadata."""

from dataclasses import dataclass, field
from pathlib import Path

import pycountry
import yaml
from loguru import logger


@dataclass
class CountryRecord:
    """A country with its identifiers and metadata."""

    baci_code: int
    iso3: str
    name: str
    aliases: list[str] = field(default_factory=list)
    region: str = "Unknown"
    continent: str = "Unknown"
    is_reexport_hub: bool = False


@dataclass
class HistoricalEntity:
    """A historical country that dissolved into successor states."""

    baci_code: int
    successors: list[str] = field(default_factory=list)
    dissolved_year: int = 0


def _load_overrides(reference_dir: Path) -> dict:
    """Read country_overrides.yaml."""
    overrides_path = reference_dir / "country_overrides.yaml"
    if not overrides_path.exists():
        logger.warning(f"Country overrides file not found: {overrides_path}")
        return {}
    with open(overrides_path) as f:
        return yaml.safe_load(f) or {}


def _baci_code_to_iso3(baci_code: int) -> str | None:
    """Use pycountry to resolve a numeric country code to ISO3 alpha-3."""
    try:
        country = pycountry.countries.get(numeric=str(baci_code).zfill(3))
        if country:
            return country.alpha_3
    except (LookupError, KeyError):
        pass
    return None


def _build_region_lookup(region_map: dict) -> dict[str, tuple[str, str]]:
    """Build iso3 → (region, continent) lookup from the region_map config."""
    lookup = {}
    # Derive continent from region name heuristics
    continent_map = {
        "Eastern Asia": "Asia",
        "South-Eastern Asia": "Asia",
        "Southern Asia": "Asia",
        "Central Asia": "Asia",
        "Western Asia": "Asia",
        "Northern America": "Americas",
        "South America": "Americas",
        "Central America": "Americas",
        "Caribbean": "Americas",
        "Western Europe": "Europe",
        "Southern Europe": "Europe",
        "Northern Europe": "Europe",
        "Eastern Europe": "Europe",
        "Northern Africa": "Africa",
        "Western Africa": "Africa",
        "Eastern Africa": "Africa",
        "Southern Africa": "Africa",
        "Central Africa": "Africa",
        "Oceania": "Oceania",
    }
    for region, countries in region_map.items():
        continent = continent_map.get(region, "Unknown")
        for iso3 in countries:
            lookup[iso3] = (region, continent)
    return lookup


def load_country_mapping(reference_dir: Path) -> dict[int, CountryRecord]:
    """Load country mapping: BACI numeric code → CountryRecord.

    Resolution order: manual overrides → pycountry → BACI country_codes CSV.
    """
    overrides_data = _load_overrides(reference_dir)
    manual_overrides = overrides_data.get("overrides", {})
    reexport_hubs = set(overrides_data.get("reexport_hubs", []))
    region_map = overrides_data.get("region_map", {})
    region_lookup = _build_region_lookup(region_map)

    mapping: dict[int, CountryRecord] = {}

    # 1. Apply manual overrides first
    for baci_code_raw, info in manual_overrides.items():
        baci_code = int(baci_code_raw)
        iso3 = info["iso3"]
        region = info.get("region", "Unknown")
        continent = info.get("continent", "Unknown")
        mapping[baci_code] = CountryRecord(
            baci_code=baci_code,
            iso3=iso3,
            name=info["name"],
            aliases=[],
            region=region,
            continent=continent,
            is_reexport_hub=iso3 in reexport_hubs,
        )

    # 2. Load BACI's own country_codes CSV if available
    baci_csv_path = reference_dir / "country_codes_baci.csv"
    baci_csv_codes: dict[int, tuple[str, str]] = {}  # code → (name, iso3)
    if baci_csv_path.exists():
        import csv

        with open(baci_csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    code = int(row.get("country_code", ""))
                    name = row.get("country_name", "")
                    iso3 = row.get("iso_3digit_alpha", "")
                    if code and iso3:
                        baci_csv_codes[code] = (name, iso3)
                except (ValueError, KeyError):
                    continue

    # 3. Build complete mapping using pycountry for all known numeric codes
    all_countries = list(pycountry.countries)
    for country in all_countries:
        try:
            baci_code = int(country.numeric)
        except (AttributeError, ValueError):
            continue

        if baci_code in mapping:
            continue  # Override already set

        iso3 = country.alpha_3
        name = country.name
        aliases = []
        if hasattr(country, "official_name"):
            aliases.append(country.official_name)
        if hasattr(country, "common_name"):
            aliases.append(country.common_name)

        region_info = region_lookup.get(iso3, ("Unknown", "Unknown"))

        mapping[baci_code] = CountryRecord(
            baci_code=baci_code,
            iso3=iso3,
            name=name,
            aliases=aliases,
            region=region_info[0],
            continent=region_info[1],
            is_reexport_hub=iso3 in reexport_hubs,
        )

    # 4. Fill in any BACI CSV codes not yet covered
    for baci_code, (name, iso3) in baci_csv_codes.items():
        if baci_code not in mapping:
            region_info = region_lookup.get(iso3, ("Unknown", "Unknown"))
            mapping[baci_code] = CountryRecord(
                baci_code=baci_code,
                iso3=iso3,
                name=name,
                aliases=[],
                region=region_info[0],
                continent=region_info[1],
                is_reexport_hub=iso3 in reexport_hubs,
            )

    logger.info(f"Loaded {len(mapping)} country mappings ({len(manual_overrides)} from overrides)")
    return mapping


def load_historical_entities(reference_dir: Path) -> dict[int, HistoricalEntity]:
    """Parse historical section of overrides YAML."""
    overrides_data = _load_overrides(reference_dir)
    historical = overrides_data.get("historical", {})

    entities: dict[int, HistoricalEntity] = {}
    for baci_code_raw, info in historical.items():
        baci_code = int(baci_code_raw)
        entities[baci_code] = HistoricalEntity(
            baci_code=baci_code,
            successors=info.get("successors", []),
            dissolved_year=info.get("dissolved_year", 0),
        )

    return entities


def resolve_country(baci_code: int, mapping: dict[int, CountryRecord]) -> CountryRecord | None:
    """Simple lookup. Returns None for unknown codes."""
    return mapping.get(baci_code)
