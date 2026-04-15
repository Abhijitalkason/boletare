"""
Step 1b: Download ALL OCR text files from Archive.org

Downloads djvu.txt for all 15 training data sources defined in ocr_sources.py.
Idempotent — skips files that already exist.

Usage:
    python scripts/training/01b_download_all_ocr.py
    python scripts/training/01b_download_all_ocr.py --only judge_horoscope_v1_raman_ocr.txt
    python scripts/training/01b_download_all_ocr.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Allow running from repo root or scripts/training/
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ocr_sources import SOURCES

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training" / "raw"
DOCS_FILE = Path(__file__).resolve().parent.parent.parent / "docs" / "TRAINING_DATA_SOURCES.md"
MIN_SIZE_BYTES = 10 * 1024  # 10KB minimum
DELAY_SECONDS = 2


def download_via_ia(archive_id: str, ocr_file: str, output_path: Path) -> bool:
    """Try downloading using the internetarchive package."""
    try:
        import internetarchive as ia

        ia.download(archive_id, files=[ocr_file], destdir=str(OUTPUT_DIR), no_directory=True)

        downloaded = OUTPUT_DIR / ocr_file
        if downloaded.exists() and downloaded != output_path:
            downloaded.rename(output_path)

        return output_path.exists()
    except ImportError:
        return False
    except Exception as e:
        print(f"    ia download failed: {e}")
        return False


def download_via_http(archive_id: str, ocr_file: str, output_path: Path) -> bool:
    """Fallback: direct HTTP download from Archive.org."""
    encoded_name = urllib.parse.quote(ocr_file)
    url = f"https://archive.org/download/{archive_id}/{encoded_name}"
    try:
        urllib.request.urlretrieve(url, str(output_path))
        return output_path.exists()
    except Exception as e:
        print(f"    HTTP download failed: {e}")
        return False


def validate_file(output_path: Path) -> tuple[bool, str]:
    """Validate downloaded OCR file. Returns (ok, message)."""
    if not output_path.exists():
        return False, "File not found after download"

    size = output_path.stat().st_size
    if size < MIN_SIZE_BYTES:
        return False, f"Too small ({size} bytes, need >{MIN_SIZE_BYTES})"

    sample = output_path.read_text(encoding="utf-8", errors="replace")[:5000]
    english_chars = sum(1 for c in sample if c.isascii() and c.isalpha())
    total_alpha = sum(1 for c in sample if c.isalpha()) or 1
    ratio = english_chars / total_alpha

    if ratio < 0.4:
        return False, f"Low English content ({ratio:.0%} ASCII alpha)"

    return True, f"{size:,} bytes"


def update_docs(output_name: str, size_kb: int) -> None:
    """Update TRAINING_DATA_SOURCES.md status for the given source."""
    if not DOCS_FILE.exists():
        return

    content = DOCS_FILE.read_text(encoding="utf-8")

    # Find the section containing this output_name and update its status line
    # Pattern: "- **Status:** Not yet processed" after the output_name appears
    # We look for the output_name in backticks, then find the next Status line
    pattern = re.escape(f"`{output_name}`")
    match = re.search(pattern, content)
    if not match:
        return

    # Find the next "Status:" line after this match
    rest = content[match.end():]
    status_match = re.search(r"- \*\*Status:\*\* Not yet processed", rest)
    if status_match:
        start = match.end() + status_match.start()
        end = match.end() + status_match.end()
        new_status = f"- **Status:** Downloaded ({size_kb} KB)"
        content = content[:start] + new_status + content[end:]
        DOCS_FILE.write_text(content, encoding="utf-8")


def download_one(source: dict, index: int, total: int, dry_run: bool = False) -> dict:
    """Download a single OCR source. Returns result dict."""
    output_path = OUTPUT_DIR / source["output_name"]
    result = {
        "name": source["output_name"],
        "title": source["title"],
        "status": "unknown",
        "size": 0,
        "error": None,
    }

    # Skip if already exists
    if output_path.exists() and output_path.stat().st_size >= MIN_SIZE_BYTES:
        size = output_path.stat().st_size
        result["status"] = "exists"
        result["size"] = size
        print(f"  [{index}/{total}] {source['output_name']} — SKIP (already exists, {size:,} bytes)")
        return result

    if dry_run:
        result["status"] = "dry_run"
        print(f"  [{index}/{total}] {source['output_name']} — WOULD DOWNLOAD from {source['id']}")
        return result

    print(f"  [{index}/{total}] Downloading {source['output_name']}...", end=" ", flush=True)

    # Try ia package first, then HTTP fallback
    success = download_via_ia(source["id"], source["ocr_file"], output_path)
    if not success:
        print("(ia failed, trying HTTP)...", end=" ", flush=True)
        success = download_via_http(source["id"], source["ocr_file"], output_path)

    if not success:
        result["status"] = "failed"
        result["error"] = "All download methods failed"
        print("FAILED")
        return result

    # Validate
    ok, message = validate_file(output_path)
    if not ok:
        result["status"] = "invalid"
        result["error"] = message
        print(f"INVALID ({message})")
        return result

    size = output_path.stat().st_size
    result["status"] = "downloaded"
    result["size"] = size
    print(f"OK ({size:,} bytes)")

    # Update docs
    update_docs(source["output_name"], size // 1024)

    return result


def print_summary(results: list[dict]) -> None:
    """Print a summary table of all downloads."""
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"{'#':<4} {'File':<40} {'Status':<12} {'Size':<12}")
    print("-" * 70)

    downloaded = 0
    existed = 0
    failed = 0

    for i, r in enumerate(results, 1):
        size_str = f"{r['size']:,} B" if r["size"] else ""
        status = r["status"].upper()
        print(f"{i:<4} {r['name']:<40} {status:<12} {size_str:<12}")
        if r["status"] == "downloaded":
            downloaded += 1
        elif r["status"] == "exists":
            existed += 1
        elif r["status"] in ("failed", "invalid"):
            failed += 1

    print("-" * 70)
    print(f"New downloads: {downloaded}  |  Already existed: {existed}  |  Failed: {failed}  |  Total: {len(results)}")
    print("=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download all OCR training data from Archive.org")
    parser.add_argument("--only", help="Download only this specific file (output_name)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sources = SOURCES
    if args.only:
        sources = [s for s in SOURCES if s["output_name"] == args.only]
        if not sources:
            print(f"ERROR: No source found with output_name '{args.only}'")
            print("Available:", ", ".join(s["output_name"] for s in SOURCES))
            return 1

    total = len(sources)
    print(f"\nArchive.org OCR Bulk Download — {total} sources")
    print(f"Output directory: {OUTPUT_DIR}\n")

    results = []
    for i, source in enumerate(sources, 1):
        result = download_one(source, i, total, dry_run=args.dry_run)
        results.append(result)

        # Rate limit between downloads (skip for existing/dry-run)
        if result["status"] == "downloaded" and i < total:
            time.sleep(DELAY_SECONDS)

    print_summary(results)

    failed = [r for r in results if r["status"] in ("failed", "invalid")]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
