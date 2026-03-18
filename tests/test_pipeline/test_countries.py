"""Tests for the country code mapping module."""

from pathlib import Path

from pipeline.countries import (
    CountryRecord,
    load_country_mapping,
    load_historical_entities,
    resolve_country,
)


class TestCountryMapping:
    def test_usa_resolves(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        mapping = load_country_mapping(tmp_path)
        record = mapping.get(840)  # USA numeric code in ISO 3166
        assert record is not None
        assert record.iso3 == "USA"

    def test_china_resolves(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        mapping = load_country_mapping(tmp_path)
        record = mapping.get(156)
        assert record is not None
        assert record.iso3 == "CHN"

    def test_taiwan_override(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        mapping = load_country_mapping(tmp_path)
        record = mapping.get(158)
        assert record is not None
        assert record.iso3 == "TWN"
        assert record.name == "Taiwan"

    def test_kosovo_override(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        mapping = load_country_mapping(tmp_path)
        record = mapping.get(983)
        assert record is not None
        assert record.iso3 == "XKX"

    def test_reexport_hub_flag(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        mapping = load_country_mapping(tmp_path)
        # Netherlands (528) should be a re-export hub
        nld = mapping.get(528)
        assert nld is not None
        assert nld.iso3 == "NLD"
        assert nld.is_reexport_hub is True

        # USA should NOT be a re-export hub
        usa = mapping.get(840)
        assert usa is not None
        assert usa.is_reexport_hub is False

    def test_historical_czechoslovakia(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        historical = load_historical_entities(tmp_path)
        entity = historical.get(200)
        assert entity is not None
        assert "CZE" in entity.successors
        assert "SVK" in entity.successors
        assert entity.dissolved_year == 1993

    def test_unknown_code_returns_none(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        mapping = load_country_mapping(tmp_path)
        result = resolve_country(99999, mapping)
        assert result is None

    def test_region_populated(self, tmp_path: Path):
        self._write_overrides(tmp_path)
        mapping = load_country_mapping(tmp_path)
        usa = mapping.get(840)
        assert usa is not None
        assert usa.region != ""
        assert usa.continent != ""

    @staticmethod
    def _write_overrides(tmp_path: Path):
        """Copy the real overrides file to tmp_path for testing."""
        import shutil
        src = Path("data/reference/country_overrides.yaml")
        if src.exists():
            shutil.copy(src, tmp_path / "country_overrides.yaml")
