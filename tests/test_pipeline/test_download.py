"""Tests for the BACI download module."""

import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.download import (
    DownloadReport,
    download_baci,
    extract_zip,
    verify_baci_csv,
)


def _make_baci_csv(path: Path, valid: bool = True) -> Path:
    """Create a minimal BACI CSV file."""
    if valid:
        path.write_text("t,i,j,k,v,q\n2020,842,156,854231,50000,100\n")
    else:
        path.write_text("col_a,col_b,col_c\n1,2,3\n")
    return path


def _make_mock_response(content: bytes = b"t,i,j,k,v,q\n2020,842,156,854231,50000,100\n", status_code: int = 200):
    """Create a mock requests response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.headers = {"content-length": str(len(content))}
    mock.iter_content = MagicMock(return_value=[content])
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        from requests.exceptions import HTTPError

        mock.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
    return mock


class TestVerifyBaciCsv:
    def test_verify_valid_csv(self, tmp_path: Path):
        csv_path = _make_baci_csv(tmp_path / "valid.csv", valid=True)
        assert verify_baci_csv(csv_path) is True

    def test_verify_invalid_csv(self, tmp_path: Path):
        csv_path = _make_baci_csv(tmp_path / "invalid.csv", valid=False)
        assert verify_baci_csv(csv_path) is False

    def test_verify_nonexistent_csv(self, tmp_path: Path):
        assert verify_baci_csv(tmp_path / "nonexistent.csv") is False


class TestExtractZip:
    def test_extract_zip(self, tmp_path: Path):
        # Create a ZIP with a CSV inside
        csv_content = "t,i,j,k,v,q\n2020,842,156,854231,50000,100\n"
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("BACI_HS17_Y2020.csv", csv_content)

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        extracted = extract_zip(zip_path, output_dir)

        assert len(extracted) == 1
        assert extracted[0].name == "BACI_HS17_Y2020.csv"
        assert extracted[0].exists()
        assert not zip_path.exists()  # ZIP deleted after extraction


class TestDownloadBaci:
    def _make_config(self, raw_dir: Path) -> dict:
        return {
            "baci": {
                "download_page": "https://example.com/baci",
                "raw_dir": str(raw_dir),
                "retry_count": 3,
                "retry_backoff_seconds": 0.001,
                "chunk_size_bytes": 65536,
                "request_timeout_seconds": 10,
            }
        }

    @patch("pipeline.download.discover_baci_urls")
    def test_skip_existing_files(self, mock_discover, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        # Pre-create a valid CSV
        csv_path = _make_baci_csv(raw_dir / "BACI_HS17_V202401.csv")

        mock_discover.return_value = [
            {"url": "https://example.com/BACI_HS17_V202401.csv", "filename": "BACI_HS17_V202401.csv", "hs_revision": "H17"}
        ]

        config = self._make_config(raw_dir)
        report = download_baci(config)

        assert len(report.skipped) == 1
        assert len(report.downloaded) == 0
        assert report.skipped[0] == csv_path

    @patch("pipeline.download.download_file")
    @patch("pipeline.download.discover_baci_urls")
    def test_retry_on_failure(self, mock_discover, mock_download, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        mock_discover.return_value = [
            {"url": "https://example.com/BACI_HS17_V202401.csv", "filename": "BACI_HS17_V202401.csv", "hs_revision": "H17"}
        ]

        # Fail twice, then succeed
        csv_content = "t,i,j,k,v,q\n2020,842,156,854231,50000,100\n"
        call_count = 0

        def side_effect(url, dest, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Connection refused")
            dest.write_text(csv_content)
            return dest

        mock_download.side_effect = side_effect

        config = self._make_config(raw_dir)
        report = download_baci(config)

        assert call_count == 3
        assert len(report.downloaded) == 1

    @patch("pipeline.download.download_file")
    @patch("pipeline.download.discover_baci_urls")
    def test_max_retries_skip(self, mock_discover, mock_download, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        mock_discover.return_value = [
            {"url": "https://example.com/BACI_HS17_V202401.csv", "filename": "BACI_HS17_V202401.csv", "hs_revision": "H17"}
        ]

        mock_download.side_effect = ConnectionError("Connection refused")

        config = self._make_config(raw_dir)
        report = download_baci(config)

        assert len(report.failed) == 1
        assert len(report.downloaded) == 0
        assert "Failed after 3 attempts" in report.failed[0][1]

    @patch("pipeline.download.discover_baci_urls")
    def test_download_report_counts(self, mock_discover, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        # 1 existing (skip), 1 missing file (will fail since no real download)
        _make_baci_csv(raw_dir / "BACI_HS17_V202401.csv")

        mock_discover.return_value = [
            {"url": "https://example.com/BACI_HS17_V202401.csv", "filename": "BACI_HS17_V202401.csv", "hs_revision": "H17"},
        ]

        config = self._make_config(raw_dir)
        report = download_baci(config)

        assert len(report.skipped) == 1
        assert isinstance(report, DownloadReport)

    @patch("pipeline.download.discover_baci_urls")
    def test_empty_url_list(self, mock_discover, tmp_path: Path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        mock_discover.return_value = []

        config = self._make_config(raw_dir)
        report = download_baci(config)

        assert len(report.downloaded) == 0
        assert len(report.skipped) == 0
        assert len(report.failed) == 0
