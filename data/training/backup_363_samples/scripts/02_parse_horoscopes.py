"""
Step 2: Parse horoscope blocks from "Notable Horoscopes" OCR text into structured JSON.

Book URL: https://archive.org/details/NotableHoroscopesBVR

Two-stage hybrid parsing:
  Stage 1 — Block identification (find horoscope boundaries via "No. X.— NAME")
  Stage 2 — Field extraction within each block (regex-based)

Outputs structured JSON matching the Pydantic schema in 03_validate_data.py.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

# Shared parsing utilities (extracted to enable reuse across Cluster A/B/C parsers)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_utils import (
    load_cities,
    extract_birth_date,
    extract_birth_time,
    extract_place,
    extract_gender,
    extract_events,
    determine_reliability,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OCR_FILE = DATA_DIR / "training" / "raw" / "notable_horoscopes_ocr.txt"
OUTPUT_FILE = DATA_DIR / "training" / "notable_horoscopes.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ─── Stage 1: Block Identification ─────────────────────────────────────────

# Pattern for "No. 1.— SRI KRISHNA" or "No. 76.— BANGALORE VENKATA RAMAN"
BLOCK_PATTERN = re.compile(
    r"No\.\s*(\d+)\.\s*[-—]+\s*(.+?)(?:\n|$)",
    re.IGNORECASE,
)


def find_blocks(text: str) -> list[tuple[int, str, str, str]]:
    """Find horoscope block boundaries in OCR text.

    Returns list of (line_number, block_id, person_name, block_text).
    """
    lines = text.split("\n")
    block_starts: list[tuple[int, str, str]] = []

    for i, line in enumerate(lines):
        match = BLOCK_PATTERN.search(line)
        if match:
            num = match.group(1)
            name = match.group(2).strip()
            block_id = f"No. {num}"
            block_starts.append((i, block_id, name))

    blocks: list[tuple[int, str, str, str]] = []
    for idx, (start_line, block_id, name) in enumerate(block_starts):
        end_line = block_starts[idx + 1][0] if idx + 1 < len(block_starts) else len(lines)
        block_text = "\n".join(lines[start_line:end_line])
        blocks.append((start_line, block_id, name, block_text))

    return blocks


# ─── Stage 2: Field Extraction (imported from parse_utils.py) ──────────────


def parse_block(
    line_num: int,
    block_id: str,
    person_name: str,
    block_text: str,
    city_lookup: dict[str, tuple[float, float]],
    chart_index: int,
) -> dict | None:
    """Parse a single horoscope block into a chart entry dict."""
    warnings: list[str] = []

    birth_date, is_bc, date_warnings = extract_birth_date(block_text)
    warnings.extend(date_warnings)

    if birth_date is None and not is_bc:
        logger.warning("Block line %d (%s - %s): No birth date found. Skipping.", line_num, block_id, person_name)
        return None

    if birth_date is None and is_bc:
        # B.C. dates — can't be processed by the engine, skip
        logger.info("Block line %d (%s - %s): B.C. date, skipping.", line_num, block_id, person_name)
        return None

    birth_time, time_warnings = extract_birth_time(block_text)
    warnings.extend(time_warnings)

    if birth_time is None:
        logger.warning("Block line %d (%s - %s): No birth time found. Skipping.", line_num, block_id, person_name)
        return None

    place, lat, lon, tier, place_warnings = extract_place(block_text, city_lookup)
    warnings.extend(place_warnings)

    gender = extract_gender(block_text)
    events = extract_events(block_text, birth_date)

    needs_review = lat is None or lon is None or not events

    if needs_review:
        warnings.append("Flagged for manual review")

    # Default coordinates for unknown places
    if lat is None:
        lat = 20.5937
    if lon is None:
        lon = 78.9629

    reliability = determine_reliability(person_name, birth_date, warnings)

    chart_id = f"NH_{chart_index:03d}"
    excerpt = block_text[:200].replace("\n", " ")

    return {
        "id": chart_id,
        "person_name": person_name,
        "birth_date": birth_date.isoformat(),
        "birth_time": birth_time.isoformat(),
        "birth_place": place or "Unknown",
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "timezone_offset": 5.5,
        "birth_time_tier": tier,
        "gender": gender,
        "birth_data_reliability": reliability,
        "events": events,
        "raw_text_excerpt": excerpt,
        "needs_manual_review": needs_review,
        "parse_warnings": warnings,
    }


def main() -> int:
    if not OCR_FILE.exists():
        print(f"ERROR: OCR file not found: {OCR_FILE}")
        print("Run 01_download_ocr.py first.")
        return 1

    city_lookup = load_cities()
    print(f"Loaded {len(city_lookup)} city entries for geocoding.")

    text = OCR_FILE.read_text(encoding="utf-8", errors="replace")
    print(f"Loaded OCR text: {len(text):,} characters")

    # Stage 1: Find blocks
    blocks = find_blocks(text)
    print(f"\nStage 1: Found {len(blocks)} horoscope blocks")

    # Stage 2: Parse each block
    charts: list[dict] = []
    parsed_ok = 0
    parsed_fail = 0
    flagged = 0
    chart_index = 1

    for line_num, block_id, person_name, block_text in blocks:
        result = parse_block(line_num, block_id, person_name, block_text, city_lookup, chart_index)
        if result:
            charts.append(result)
            parsed_ok += 1
            chart_index += 1
            if result["needs_manual_review"]:
                flagged += 1
            logger.info(
                "Block line %d (%s - %s) -> %s: %d events, reliability=%s, review=%s",
                line_num, block_id, person_name, result["id"],
                len(result["events"]), result["birth_data_reliability"],
                result["needs_manual_review"],
            )
        else:
            parsed_fail += 1

    # Reliability distribution
    reliability_dist: dict[str, int] = {}
    for c in charts:
        r = c["birth_data_reliability"]
        reliability_dist[r] = reliability_dist.get(r, 0) + 1

    # Summary
    print(f"\n{'='*60}")
    print(f"PARSING SUMMARY")
    print(f"{'='*60}")
    print(f"Blocks found:          {len(blocks)}")
    print(f"Parsed successfully:   {parsed_ok}")
    print(f"Parse failures:        {parsed_fail}")
    print(f"Flagged for review:    {flagged}")
    total_events = sum(len(c["events"]) for c in charts)
    print(f"Total events extracted:{total_events}")
    print(f"\nReliability distribution:")
    for level, count in sorted(reliability_dist.items()):
        print(f"  {level}: {count}")
    print(f"{'='*60}")

    # Write output
    output = {
        "source": "notable_horoscopes_bv_raman",
        "book_url": "https://archive.org/details/NotableHoroscopesBVR",
        "charts": charts,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput saved to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
