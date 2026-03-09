"""
Step 1: Download OCR text from Archive.org

Downloads the djvu.txt for "Notable Horoscopes" by B.V. Raman.
Book URL: https://archive.org/details/NotableHoroscopesBVR
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ARCHIVE_ID = "NotableHoroscopesBVR"
DJVU_FILENAME = "Notable Horoscopes_djvu.txt"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "notable_horoscopes_ocr.txt"
MIN_SIZE_BYTES = 10 * 1024  # 10KB minimum


def download_via_ia() -> bool:
    """Try downloading using the internetarchive package."""
    try:
        import internetarchive as ia

        print(f"Downloading {DJVU_FILENAME} via internetarchive package...")
        ia.download(ARCHIVE_ID, files=[DJVU_FILENAME], destdir=str(OUTPUT_DIR), no_directory=True)

        downloaded = OUTPUT_DIR / DJVU_FILENAME
        if downloaded != OUTPUT_FILE:
            downloaded.rename(OUTPUT_FILE)

        return True
    except ImportError:
        print("internetarchive package not installed, trying HTTP fallback...")
        return False
    except Exception as e:
        print(f"internetarchive download failed: {e}")
        return False


def download_via_http() -> bool:
    """Fallback: direct HTTP download from Archive.org."""
    encoded_name = DJVU_FILENAME.replace(" ", "%20")
    url = f"https://archive.org/download/{ARCHIVE_ID}/{encoded_name}"
    print(f"Downloading via HTTP: {url}")
    try:
        urllib.request.urlretrieve(url, str(OUTPUT_FILE))
        return True
    except Exception as e:
        print(f"HTTP download failed: {e}")
        return False


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size >= MIN_SIZE_BYTES:
        print(f"OCR file already exists: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size:,} bytes)")
        return 0

    success = download_via_ia() or download_via_http()

    if not success:
        print("ERROR: All download methods failed.")
        return 1

    if not OUTPUT_FILE.exists():
        print(f"ERROR: Download reported success but file not found: {OUTPUT_FILE}")
        return 1

    size = OUTPUT_FILE.stat().st_size
    if size < MIN_SIZE_BYTES:
        print(f"ERROR: Downloaded file too small ({size} bytes). Expected >{MIN_SIZE_BYTES} bytes.")
        return 1

    # Verify English content
    sample = OUTPUT_FILE.read_text(encoding="utf-8", errors="replace")[:5000]
    english_chars = sum(1 for c in sample if c.isascii() and c.isalpha())
    total_alpha = sum(1 for c in sample if c.isalpha()) or 1
    if english_chars / total_alpha < 0.5:
        print(f"WARNING: Content may not be English ({english_chars}/{total_alpha} ASCII alpha)")

    print(f"SUCCESS: Downloaded OCR text ({size:,} bytes) to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
