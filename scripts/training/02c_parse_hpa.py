"""
Step 2c: Parse horoscope blocks from "Hindu Predictive Astrology" OCR text.

Book URL: https://archive.org/details/hindupredictiveastrologyofbvraman

Block format:
  "11. Birth Data : —Male, Born on 29th July 1850, at 8 p.m., Bangalore."
  "Planetary Positions :—..."
  "General Remarks :—Two wives; mark the position of Venus."

Filters for Indian-only charts based on coordinates.
Outputs structured JSON matching the Pydantic schema in 03_validate_data.py.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_utils import (
    EVENT_KEYWORDS,
    load_cities,
    extract_birth_date,
    extract_birth_time,
    extract_events,
    extract_latlon,
    determine_reliability,
    is_indian_chart,
    INLINE_COORD_PATTERN,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OCR_FILE = DATA_DIR / "training" / "raw" / "hindu_predictive_astrology_ocr.txt"
OUTPUT_FILE = DATA_DIR / "training" / "hindu_predictive_astrology.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Block delimiter for HPA format:
# "11. Birth Data : —Male, Born on 29th July 1850, at 8 p.m., Bangalore."
# "-19. Birth Data :—Female, born on 21st ..."  (OCR artifact: leading hyphen)
BLOCK_PATTERN = re.compile(
    r"^[- ]*(\d+)\.\s*Birth\s+Data\s*:?\s*[-—]+\s*(Male|Female)",
    re.IGNORECASE | re.MULTILINE,
)

# General Remarks section
REMARKS_PATTERN = re.compile(
    r"General\s+Remarks?\s*:?\s*[-—]+\s*(.+?)(?=\n\s*\d+\.\s*Birth\s+Data|\Z)",
    re.IGNORECASE | re.DOTALL,
)

# Place extraction from HPA format: "at 8 p.m., Bangalore."
# or "at 4-25 p.m. (IT 25' E. and 13° N.)" — place might be absent
HPA_PLACE_PATTERN = re.compile(
    r"(?:a\.?m\.?|p\.?m\.?|midnight|noon)[,.]?\s+(?:at\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    re.IGNORECASE,
)

# Inline coords in HPA: "(77°25'E. and 13° N.)" or "(72' E. and 23 N.)" or "(12° N. and 76° 38' E.)"
HPA_COORD_PATTERN = re.compile(
    r"\(([^)]{5,50})\)",
)


def find_blocks(text: str) -> list[tuple[int, str, str, str]]:
    """Find HPA-style horoscope blocks.

    Returns list of (line_number, block_id, gender, block_text).
    """
    lines = text.split("\n")
    block_starts: list[tuple[int, str, str]] = []

    for i, line in enumerate(lines):
        match = BLOCK_PATTERN.search(line)
        if match:
            num = match.group(1)
            gender = match.group(2).lower()
            block_id = f"HPA_{int(num):03d}"
            block_starts.append((i, block_id, gender))

    blocks: list[tuple[int, str, str, str]] = []
    for idx, (start_line, block_id, gender) in enumerate(block_starts):
        end_line = block_starts[idx + 1][0] if idx + 1 < len(block_starts) else len(lines)
        block_text = "\n".join(lines[start_line:end_line])
        blocks.append((start_line, block_id, gender, block_text))

    return blocks


def extract_hpa_coords(text: str) -> tuple[float | None, float | None]:
    """Extract coordinates from HPA inline format.

    Handles: "(77°25'E. and 13° N.)", "(12° N. and 76° 38' E.)", "(72' E. and 23 N.)"
    """
    # First try the standard lat/lon patterns from parse_utils
    lat, lon = extract_latlon(text)
    if lat is not None and lon is not None:
        return lat, lon

    # Try parenthesized coordinate blocks
    for paren_match in HPA_COORD_PATTERN.finditer(text):
        inner = paren_match.group(1)
        lat, lon = extract_latlon(inner)
        if lat is not None and lon is not None:
            return lat, lon

        # Try inline pattern: "12° N. and 76° 38' E."
        match = INLINE_COORD_PATTERN.search(inner)
        if match:
            g = match.groups()
            lat_val = float(g[0]) + float(g[1] or 0) / 60.0
            if g[2].upper() == "S":
                lat_val = -lat_val
            lon_val = float(g[3]) + float(g[4] or 0) / 60.0
            if g[5].upper() == "W":
                lon_val = -lon_val
            return lat_val, lon_val

    return None, None


def extract_hpa_place(text: str, city_lookup: dict[str, tuple[float, float]]) -> str | None:
    """Extract place name from HPA birth data line."""
    match = HPA_PLACE_PATTERN.search(text)
    if match:
        candidate = match.group(1).strip().rstrip(".")
        if candidate.lower() not in ("the", "a", "an", "his", "her", "planetary", "general"):
            return candidate

    # Try matching against known cities
    text_lower = text.lower()
    for city_name in city_lookup:
        if city_name in text_lower:
            return city_name.title()

    return None


# HPA-specific event pattern: "Earldom—1921", "death in !778", "attack...1919"
# Catches bare years near event keywords that the standard extractor misses
_HPA_YEAR_PATTERN = re.compile(r"[-—]?\s*(\d{4})\b")


def _extract_hpa_events(
    text: str, birth_date, existing_events: list[dict]
) -> list[dict]:
    """Extract events using HPA-specific patterns (em-dash + bare year).

    Only adds events not already found by the standard extract_events().
    """
    from datetime import date as _date

    events: list[dict] = []
    existing_keys = {(e["event_type"], e["event_date"]) for e in existing_events}

    sentences = re.split(r"[.;]", text)
    for sentence in sentences:
        sent_lower = sentence.lower()
        for event_type, keywords in EVENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword not in sent_lower:
                    continue

                # Find all 4-digit years in this sentence
                for year_match in _HPA_YEAR_PATTERN.finditer(sentence):
                    try:
                        year = int(year_match.group(1))
                        if year < 1000 or year > 2025:
                            continue
                        event_date = _date(year, 6, 15)
                        if birth_date and event_date <= birth_date:
                            continue
                        key = (event_type, event_date.isoformat())
                        if key not in existing_keys:
                            events.append({
                                "event_type": event_type,
                                "event_date": event_date.isoformat(),
                                "confidence": "approximate",
                            })
                            existing_keys.add(key)
                    except (ValueError, TypeError):
                        continue
                break  # Only first matching keyword per event_type

    return events


def parse_block(
    line_num: int,
    block_id: str,
    gender: str,
    block_text: str,
    city_lookup: dict[str, tuple[float, float]],
) -> dict | None:
    """Parse a single HPA horoscope block into a chart entry dict."""
    warnings: list[str] = []

    # Extract birth date (search the whole block text, not Birth Details section)
    birth_date, _is_bc, date_warnings = extract_birth_date(block_text, use_birth_details_section=False)
    warnings.extend(date_warnings)

    if birth_date is None:
        logger.warning("Block %s line %d: No birth date found. Skipping.", block_id, line_num)
        return None

    # Extract birth time
    birth_time, time_warnings = extract_birth_time(block_text, use_birth_details_section=False)
    warnings.extend(time_warnings)

    if birth_time is None:
        logger.warning("Block %s line %d: No birth time found. Skipping.", block_id, line_num)
        return None

    # Extract coordinates
    lat, lon = extract_hpa_coords(block_text)

    # Extract place name before Indian filter (needed for city-based detection)
    place = extract_hpa_place(block_text, city_lookup)

    # If no coords but known Indian city, use geocoded coords
    if lat is None and place:
        coords = city_lookup.get(place.lower())
        if coords:
            lat, lon = coords

    # Indian-only filter
    indian = is_indian_chart(lat, lon, place, block_text, city_lookup)
    if indian is False:
        logger.info("Block %s line %d: Non-Indian chart (lat=%.1f, lon=%.1f). Skipping.",
                     block_id, line_num, lat or 0, lon or 0)
        return None

    # Determine birth_time_tier
    if lat is not None and lon is not None and place:
        tier = 1
    elif lat is not None and lon is not None:
        tier = 2
    elif place:
        tier = 2
        warnings.append(f"Place '{place}' found but no coordinates")
    else:
        tier = 3
        warnings.append("No place or coordinates found")

    # Extract events from General Remarks section
    # Clean OCR line breaks that split words (e.g., "Octo¬\nber" → "October")
    clean_text = re.sub(r"¬\s*\n\s*", "", block_text)
    # Also join lines within paragraphs (OCR wraps mid-sentence)
    clean_text = re.sub(r"(?<!\n)\n(?!\n)", " ", clean_text)

    remarks_match = REMARKS_PATTERN.search(clean_text)
    remarks_text = remarks_match.group(1) if remarks_match else clean_text

    # Use standard extractor first, then HPA-specific for em-dash/bare-year patterns
    events = extract_events(remarks_text, birth_date)
    events.extend(_extract_hpa_events(remarks_text, birth_date, events))

    needs_review = (lat is None or lon is None) or not events

    # Default coordinates for unknown places
    if lat is None:
        lat = 20.5937
    if lon is None:
        lon = 78.9629

    reliability = determine_reliability("", birth_date, warnings)

    excerpt = block_text[:200].replace("\n", " ")

    return {
        "id": block_id,
        "person_name": "",  # HPA charts are mostly anonymous
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
        print("Run 01b_download_all_ocr.py first.")
        return 1

    city_lookup = load_cities()
    print(f"Loaded {len(city_lookup)} city entries for geocoding.")

    text = OCR_FILE.read_text(encoding="utf-8", errors="replace")
    print(f"Loaded OCR text: {len(text):,} characters")

    # Stage 1: Find blocks
    blocks = find_blocks(text)
    print(f"\nStage 1: Found {len(blocks)} Birth Data blocks")

    # Stage 2: Parse each block (Indian-only)
    charts: list[dict] = []
    parsed_ok = 0
    parsed_fail = 0
    flagged = 0

    for line_num, block_id, gender, block_text in blocks:
        result = parse_block(line_num, block_id, gender, block_text, city_lookup)
        if result:
            charts.append(result)
            parsed_ok += 1
            if result["needs_manual_review"]:
                flagged += 1
            logger.info(
                "Block %s: %s, %d events, lat=%.2f lon=%.2f, reliability=%s",
                block_id, result["birth_place"],
                len(result["events"]), result["latitude"], result["longitude"],
                result["birth_data_reliability"],
            )
        elif result is None:
            # Check if it was skipped due to non-Indian
            parsed_fail += 1

    # Summary
    total_events = sum(len(c["events"]) for c in charts)
    print(f"\n{'='*60}")
    print(f"PARSING SUMMARY — Hindu Predictive Astrology")
    print(f"{'='*60}")
    print(f"Blocks found:          {len(blocks)}")
    print(f"Parsed (Indian only):  {parsed_ok}")
    print(f"Skipped/failed:        {parsed_fail}")
    print(f"Flagged for review:    {flagged}")
    print(f"Total events extracted:{total_events}")

    event_dist: dict[str, int] = {}
    for c in charts:
        for e in c["events"]:
            event_dist[e["event_type"]] = event_dist.get(e["event_type"], 0) + 1
    print(f"\nEvent distribution:")
    for etype, count in sorted(event_dist.items()):
        print(f"  {etype}: {count}")
    print(f"{'='*60}")

    # Write output
    output = {
        "source": "hindu_predictive_astrology_bv_raman",
        "book_url": "https://archive.org/details/hindupredictiveastrologyofbvraman",
        "charts": charts,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput saved to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
