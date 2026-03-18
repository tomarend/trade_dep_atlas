"""BACI data download module with retry, resume, and progress reporting."""

import re
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import requests
from loguru import logger
from tqdm import tqdm


@dataclass
class DownloadReport:
    """Report of download results."""

    downloaded: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def discover_baci_urls(download_page_url: str) -> list[dict]:
    """Fetch the BACI download page and parse it for CSV/ZIP download links.

    Falls back to an empty list if the page cannot be fetched.
    """
    try:
        resp = requests.get(download_page_url, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except requests.RequestException as e:
        logger.warning(f"Could not fetch BACI download page: {e}. Returning empty URL list.")
        return []

    # Look for href links matching BACI data file patterns
    pattern = r'href=["\']([^"\']*BACI_HS\d+_V\d+[^"\']*\.(?:csv|zip))["\']'
    matches = re.findall(pattern, html, re.IGNORECASE)

    urls = []
    for match in matches:
        # Make absolute URL if relative
        if match.startswith("http"):
            url = match
        elif match.startswith("/"):
            # Extract base URL
            from urllib.parse import urlparse

            parsed = urlparse(download_page_url)
            url = f"{parsed.scheme}://{parsed.netloc}{match}"
        else:
            # Relative to page directory
            base = download_page_url.rsplit("/", 1)[0]
            url = f"{base}/{match}"

        filename = url.rsplit("/", 1)[-1]
        # Extract HS revision from filename
        hs_match = re.search(r"HS(\d+)", filename)
        hs_revision = f"H{hs_match.group(1)}" if hs_match else "unknown"

        urls.append({"url": url, "filename": filename, "hs_revision": hs_revision})

    logger.info(f"Discovered {len(urls)} BACI data file URLs")
    return urls


def download_file(url: str, dest: Path, chunk_size: int = 65536, timeout: int = 300) -> Path:
    """Stream-download a file from url to dest. Raises on HTTP error."""
    resp = requests.get(url, stream=True, timeout=timeout)
    resp.raise_for_status()

    total_size = int(resp.headers.get("content-length", 0)) or None
    with tqdm(total=total_size, unit="B", unit_scale=True, desc=dest.name) as pbar:
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                pbar.update(len(chunk))

    return dest


def extract_zip(zip_path: Path, output_dir: Path) -> list[Path]:
    """Extract ZIP contents to output_dir. Deletes ZIP after successful extraction."""
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            zf.extract(member, output_dir)
            extracted.append(output_dir / member)

    zip_path.unlink()
    logger.info(f"Extracted {len(extracted)} files from {zip_path.name}")
    return extracted


def verify_baci_csv(csv_path: Path) -> bool:
    """Check that a CSV has the expected BACI columns: t, i, j, k, v, q."""
    try:
        with open(csv_path) as f:
            header = f.readline().strip()
        columns = {col.strip().lower() for col in header.split(",")}
        expected = {"t", "i", "j", "k", "v", "q"}
        return expected.issubset(columns)
    except (OSError, UnicodeDecodeError):
        return False


def download_baci(config: dict, output_dir: Path | None = None) -> DownloadReport:
    """Download BACI CSV files from CEPII with retry and resume.

    Args:
        config: Pipeline config dict (expects baci.* keys).
        output_dir: Override output directory (defaults to config baci.raw_dir).

    Returns:
        DownloadReport with lists of downloaded, skipped, and failed files.
    """
    baci_cfg = config["baci"]
    output_dir = output_dir or Path(baci_cfg["raw_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    retry_count = baci_cfg.get("retry_count", 3)
    retry_backoff = baci_cfg.get("retry_backoff_seconds", 5)
    chunk_size = baci_cfg.get("chunk_size_bytes", 65536)
    timeout = baci_cfg.get("request_timeout_seconds", 300)

    report = DownloadReport()

    urls = discover_baci_urls(baci_cfg["download_page"])
    if not urls:
        logger.warning("No BACI download URLs discovered")
        return report

    for entry in urls:
        url = entry["url"]
        filename = entry["filename"]

        # Determine expected CSV filename (if ZIP, it's the extracted name)
        csv_name = filename.replace(".zip", ".csv")
        csv_path = output_dir / csv_name

        # Skip if already downloaded
        if csv_path.exists() and verify_baci_csv(csv_path):
            logger.info(f"Skipping {csv_name} — already exists")
            report.skipped.append(csv_path)
            continue

        # Download with retry
        dest_path = output_dir / filename
        success = False
        for attempt in range(retry_count):
            try:
                download_file(url, dest_path, chunk_size=chunk_size, timeout=timeout)
                success = True
                break
            except (requests.RequestException, OSError) as e:
                wait = retry_backoff * (2**attempt)
                logger.warning(f"Download attempt {attempt + 1}/{retry_count} failed for {filename}: {e}. Retrying in {wait}s")
                time.sleep(wait)

        if not success:
            logger.error(f"Failed to download {filename} after {retry_count} attempts")
            report.failed.append((url, f"Failed after {retry_count} attempts"))
            continue

        # Extract if ZIP
        if filename.endswith(".zip"):
            try:
                extracted = extract_zip(dest_path, output_dir)
                # Find the CSV among extracted files
                csv_files = [p for p in extracted if p.suffix.lower() == ".csv"]
                if csv_files:
                    csv_path = csv_files[0]
            except zipfile.BadZipFile as e:
                logger.error(f"Bad ZIP file {filename}: {e}")
                report.failed.append((url, f"Bad ZIP: {e}"))
                if dest_path.exists():
                    dest_path.unlink()
                continue
        else:
            csv_path = dest_path

        # Verify CSV columns
        if verify_baci_csv(csv_path):
            logger.info(f"Downloaded and verified {csv_path.name}")
            report.downloaded.append(csv_path)
        else:
            logger.warning(f"CSV verification failed for {csv_path.name} — unexpected columns")
            report.failed.append((url, "CSV column verification failed"))

    logger.info(
        f"Download complete: {len(report.downloaded)} downloaded, "
        f"{len(report.skipped)} skipped, {len(report.failed)} failed"
    )
    return report
