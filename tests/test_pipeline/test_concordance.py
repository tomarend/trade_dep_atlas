"""Tests for the HS concordance pipeline module."""

import csv
from pathlib import Path

from pipeline.concordance import (
    Concordance,
    ConcordedProduct,
    apply_concordance,
    build_concordance_polars_map,
    load_concordance,
    load_product_descriptions,
    validate_concordance,
)


def _make_concordance_csv(concordance_dir: Path, mappings: list[tuple[str, str]]):
    """Write a concordance CSV with given (source, target) mappings."""
    concordance_dir.mkdir(parents=True, exist_ok=True)
    csv_path = concordance_dir / "test_concordance.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_hs6", "target_hs6"])
        writer.writerows(mappings)


def _make_descriptions(reference_dir: Path):
    """Create a minimal product descriptions CSV."""
    desc_path = reference_dir / "hs_product_descriptions.csv"
    with open(desc_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hs6", "description", "category"])
        writer.writerow(["854231", "Electronic integrated circuits: processors and controllers", "semiconductors"])
        writer.writerow(["270900", "Petroleum oils, crude", "energy"])
        writer.writerow(["280461", "Silicon, containing >= 99.99%", "critical_minerals"])
        writer.writerow(["260300", "Copper ores and concentrates", "critical_minerals"])
        writer.writerow(["999999", "Mapped product target", "other"])


class TestIdentityMapping:
    def test_identity_mapping_when_no_tables(self, tmp_path: Path):
        """With no concordance directory, all codes map to themselves."""
        _make_descriptions(tmp_path)
        concordance = load_concordance(tmp_path)
        assert len(concordance.forward_map) == 0
        result = apply_concordance("854231", concordance)
        assert result.concorded_hs6 == "854231"
        assert result.concordance_flag == "unmapped"


class TestApplyConcordance:
    def _make_test_concordance(self, tmp_path: Path) -> Concordance:
        """Create a concordance with various mapping types."""
        _make_descriptions(tmp_path)
        _make_concordance_csv(
            tmp_path / "concordance",
            [
                ("854231", "854231"),  # unchanged
                ("111111", "999999"),  # mapped (different target)
                ("222222", "999999"),  # also maps to 999999 → merged
                ("333333", "444444"),  # split: one source → two targets
                ("333333", "555555"),
            ],
        )
        return load_concordance(tmp_path)

    def test_apply_unchanged_code(self, tmp_path: Path):
        concordance = self._make_test_concordance(tmp_path)
        result = apply_concordance("854231", concordance)
        assert result.concorded_hs6 == "854231"
        assert result.concordance_flag == "unchanged"

    def test_apply_mapped_code(self, tmp_path: Path):
        concordance = self._make_test_concordance(tmp_path)
        result = apply_concordance("111111", concordance)
        assert result.concorded_hs6 == "999999"
        assert result.concordance_flag == "merged"  # two sources → one target

    def test_apply_split_code(self, tmp_path: Path):
        concordance = self._make_test_concordance(tmp_path)
        result = apply_concordance("333333", concordance)
        assert result.concordance_flag == "split"
        # Should pick first alphabetically
        assert result.concorded_hs6 == "444444"

    def test_apply_unmapped_code(self, tmp_path: Path):
        concordance = self._make_test_concordance(tmp_path)
        result = apply_concordance("777777", concordance)
        assert result.concordance_flag == "unmapped"
        assert result.concorded_hs6 == "777777"

    def test_hs_hierarchy_extraction(self, tmp_path: Path):
        concordance = self._make_test_concordance(tmp_path)
        result = apply_concordance("854231", concordance)
        assert result.hs2 == "85"
        assert result.hs4 == "8542"


class TestProductDescriptions:
    def test_product_descriptions_loaded(self, tmp_path: Path):
        _make_descriptions(tmp_path)
        descs = load_product_descriptions(tmp_path)
        assert "854231" in descs
        desc, cat = descs["854231"]
        assert "Electronic integrated circuits" in desc
        assert cat == "semiconductors"


class TestBuildPolarsMap:
    def test_build_polars_map_flat(self, tmp_path: Path):
        _make_descriptions(tmp_path)
        _make_concordance_csv(
            tmp_path / "concordance",
            [
                ("854231", "854231"),
                ("111111", "222222"),
                ("333333", "444444"),
                ("333333", "555555"),
            ],
        )
        concordance = load_concordance(tmp_path)
        flat = build_concordance_polars_map(concordance)
        assert isinstance(flat, dict)
        assert flat["854231"] == "854231"
        assert flat["111111"] == "222222"
        assert flat["333333"] == "444444"  # first alphabetically


class TestValidation:
    def test_validate_concordance_spot_checks(self, tmp_path: Path):
        _make_descriptions(tmp_path)
        # Create concordance WITHOUT critical products
        _make_concordance_csv(
            tmp_path / "concordance",
            [("111111", "222222")],
        )
        concordance = load_concordance(tmp_path)
        warnings = validate_concordance(concordance)
        # Should warn about missing critical products
        critical_warnings = [w for w in warnings if "Critical product" in w]
        assert len(critical_warnings) > 0

    def test_validate_empty_concordance(self, tmp_path: Path):
        _make_descriptions(tmp_path)
        concordance = load_concordance(tmp_path)  # No concordance dir
        warnings = validate_concordance(concordance)
        assert any("identity mapping" in w.lower() or "no concordance" in w.lower() for w in warnings)
