"""
Step 2e: Parse horoscope blocks from "Crux of Vedic Astrology — Timing of Events"
by Sanjay Rath (1998).

Book URL: https://archive.org/details/sanjayrathcruxofvedicastrologytimingofevents19982

Block format variants:
  "Chart 8 : Swami Vivekanand, Born on 12th January 1863 at 6:33'AM (LMT), at 22 N 40', 88 E 30'."
  "Chart 9 Indira Gandhi (ex P.M. of India) 19th November 1917, 11;03' PM 1ST, 25N28, 81 E 52."
  "Chart 7. Male Born on 22/23 May 1955, at 30N21, 76E52."

This book focuses on EVENT TIMING — has rich biographical events with dates.
Filters for Indian-only charts.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_utils import (
    MONTH_MAP,
    EVENT_KEYWORDS,
    load_cities,
    extract_birth_date,
    extract_birth_time,
    extract_events,
    extract_gender,
    determine_reliability,
    is_indian_chart,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OCR_FILE = DATA_DIR / "training" / "raw" / "sanjay_rath_crux_ocr.txt"
OUTPUT_FILE = DATA_DIR / "training" / "sanjay_rath_crux.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Block delimiter: "Chart N" at start of line, followed by chart content
BLOCK_PATTERN = re.compile(
    r"^Chart\s+(\d+)\s*[.:]\s*",
    re.IGNORECASE | re.MULTILINE,
)

# Coordinate patterns specific to Sanjay Rath format
# "30N21, 76E52" or "22 N 40', 88 E 30'" or "25N28, 81 E 52"
SR_COORD_PATTERN = re.compile(
    r"(\d+)\s*([NS])\s*(\d+)?['\s,]*(\d+)\s*([EW])\s*(\d+)?",
    re.IGNORECASE,
)

# Name extraction: "Chart 8 : Swami Vivekanand," or "Chart 9 Indira Gandhi (ex P.M.)"
SR_NAME_PATTERN = re.compile(
    r"Chart\s+\d+\s*[.:]\s*([A-Z][a-zA-Z\s.]+?)(?:\s*[,(;]|\s+[Bb]o[rm]n|\s+\d{1,2})",
)

# Place extraction from Sanjay Rath: "at INDORE" or "at Chirakkal"
SR_PLACE_PATTERN = re.compile(
    r"(?:at|AT)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
)


def extract_sr_coords(text: str) -> tuple[float | None, float | None]:
    """Extract coordinates from Sanjay Rath format: '30N21, 76E52' or '22 N 40, 88 E 30'."""
    match = SR_COORD_PATTERN.search(text)
    if not match:
        return None, None

    g = match.groups()
    try:
        lat_deg = int(g[0])
        lat_dir = g[1].upper()
        lat_min = int(g[2]) if g[2] else 0
        lon_deg = int(g[3])
        lon_dir = g[4].upper()
        lon_min = int(g[5]) if g[5] else 0

        lat = lat_deg + lat_min / 60.0
        lon = lon_deg + lon_min / 60.0

        if lat_dir == "S":
            lat = -lat
        if lon_dir == "W":
            lon = -lon

        return lat, lon
    except (ValueError, TypeError):
        return None, None


def extract_sr_name(text: str) -> str:
    """Extract person name from chart header."""
    # Only look at the first line
    first_line = text.split("\n")[0]
    match = SR_NAME_PATTERN.search(first_line)
    if match:
        name = match.group(1).strip()
        # Filter out generic labels
        if name.lower() in ("male", "female", "chart"):
            return ""
        return name
    return ""


def find_blocks(text: str) -> list[tuple[int, str, str]]:
    """Find chart blocks in the OCR text.

    Returns list of (line_number, chart_num, block_text).
    """
    lines = text.split("\n")
    block_starts: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        match = BLOCK_PATTERN.match(line)
        if match:
            chart_num = match.group(1)
            block_starts.append((i, chart_num))

    blocks: list[tuple[int, str, str]] = []
    seen_nums: set[str] = set()

    for idx, (start_line, chart_num) in enumerate(block_starts):
        # Skip duplicate chart number references (only keep first definition)
        # But Sanjay Rath reuses chart numbers in different chapters, so
        # check if this line has birth data
        end_line = block_starts[idx + 1][0] if idx + 1 < len(block_starts) else min(start_line + 150, len(lines))
        block_text = "\n".join(lines[start_line:end_line])

        # Only keep blocks that have some birth data indicator
        has_birth = bool(re.search(r"[Bb]o[rm]n|[0-9]{4}|[0-9]+\s*[NS]", block_text[:300]))
        if has_birth:
            blocks.append((start_line, chart_num, block_text))

    return blocks


def parse_block(
    line_num: int,
    chart_num: str,
    block_text: str,
    city_lookup: dict[str, tuple[float, float]],
    chart_index: int,
) -> dict | None:
    """Parse a single Sanjay Rath chart block."""
    warnings: list[str] = []

    # Clean OCR line breaks
    clean_text = re.sub(r"¬\s*\n\s*", "", block_text)
    clean_text = re.sub(r"(?<!\n)\n(?!\n)", " ", clean_text)

    # Extract person name
    person_name = extract_sr_name(block_text)

    # Extract birth date
    birth_date, _is_bc, date_warnings = extract_birth_date(clean_text, use_birth_details_section=False)
    warnings.extend(date_warnings)

    if birth_date is None:
        return None

    # Extract birth time (handle OCR: "11;03' PM" → "11:03 PM")
    time_text = clean_text.replace(";", ":").replace("'", "")
    birth_time, time_warnings = extract_birth_time(time_text, use_birth_details_section=False)
    warnings.extend(time_warnings)

    if birth_time is None:
        return None

    # Extract coordinates (Sanjay Rath format)
    lat, lon = extract_sr_coords(clean_text)

    # Try place name
    place = None
    match = SR_PLACE_PATTERN.search(clean_text)
    if match:
        candidate = match.group(1).strip()
        if candidate.lower() not in ("the", "a", "an", "his", "her", "chart", "time"):
            place = candidate

    # Geocode place if no coords
    if lat is None and place:
        coords = city_lookup.get(place.lower())
        if coords:
            lat, lon = coords

    # Indian-only filter (OCR: "1ST" = IST)
    # Also check for IST/1ST/LMT in text
    has_ist = bool(re.search(r"1ST|IST|I\.S\.T|LMT|L\.M\.T", clean_text))
    has_gmt = bool(re.search(r"GMT|G\.M\.T|CST|EST", clean_text))

    if has_gmt and not has_ist:
        return None  # Non-Indian

    indian = is_indian_chart(lat, lon, place, clean_text, city_lookup)
    if indian is False and not has_ist:
        return None

    # Gender
    gender = extract_gender(clean_text)
    # Check explicit gender in header
    first_line_lower = block_text.split("\n")[0].lower()
    if "male" in first_line_lower and "female" not in first_line_lower:
        gender = "male"
    elif "female" in first_line_lower:
        gender = "female"

    # Birth time tier
    if lat is not None and lon is not None:
        tier = 1 if place else 2
    else:
        tier = 3

    # Extract events — this book is rich in biographical events
    events = extract_events(clean_text, birth_date)

    # Also try bare-year extraction for biographical sentences
    from datetime import date as _date
    existing_keys = {(e["event_type"], e["event_date"]) for e in events}
    sentences = re.split(r"[.;]", clean_text)
    for sentence in sentences:
        sent_lower = sentence.lower()
        # Skip theoretical text
        if re.search(r"\bgenerally\b|\busually\b|\bif the\b|\bwhen the\b", sentence, re.I):
            continue
        for event_type, keywords in EVENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword not in sent_lower:
                    continue
                for ym in re.finditer(r"\b(1[89]\d{2})\b", sentence):
                    try:
                        year = int(ym.group(1))
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
                break

    needs_review = (lat is None or lon is None) or not events

    if lat is None:
        lat = 20.5937
    if lon is None:
        lon = 78.9629

    reliability = determine_reliability(person_name, birth_date, warnings)

    chart_id = f"SRC_{chart_index:03d}"
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
        return 1

    city_lookup = load_cities()
    print(f"Loaded {len(city_lookup)} city entries for geocoding.")

    text = OCR_FILE.read_text(encoding="utf-8", errors="replace")
    print(f"Loaded OCR text: {len(text):,} characters")

    blocks = find_blocks(text)
    print(f"\nFound {len(blocks)} chart blocks with birth data")

    charts: list[dict] = []
    chart_index = 1
    seen_sigs: set[tuple] = set()

    for line_num, chart_num, block_text in blocks:
        result = parse_block(line_num, chart_num, block_text, city_lookup, chart_index)
        if result:
            # Dedup
            sig = (result["birth_date"], result["birth_time"], round(result["latitude"], 1), round(result["longitude"], 1))
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)

            charts.append(result)
            chart_index += 1
            logger.info(
                "Chart %s: %s %s, %d events, lat=%.2f lon=%.2f",
                result["id"], result["person_name"] or "(anon)",
                result["birth_date"], len(result["events"]),
                result["latitude"], result["longitude"],
            )

    total_events = sum(len(c["events"]) for c in charts)
    event_dist: dict[str, int] = {}
    for c in charts:
        for e in c["events"]:
            event_dist[e["event_type"]] = event_dist.get(e["event_type"], 0) + 1

    print(f"\n{'='*60}")
    print(f"PARSING SUMMARY — Sanjay Rath: Crux of Vedic Astrology")
    print(f"{'='*60}")
    print(f"  Blocks found:        {len(blocks)}")
    print(f"  Parsed (Indian):     {len(charts)}")
    print(f"  Total events:        {total_events}")
    if event_dist:
        print(f"  Event distribution:  {event_dist}")

    # Show named charts
    named = [c for c in charts if c["person_name"]]
    if named:
        print(f"\n  Named charts ({len(named)}):")
        for c in named[:15]:
            print(f"    {c['id']} {c['person_name']:30s} {c['birth_date']}  events={len(c['events'])}")
    print(f"{'='*60}")

    output = {
        "source": "sanjay_rath_crux_vedic_astrology",
        "book_url": "https://archive.org/details/sanjayrathcruxofvedicastrologytimingofevents19982",
        "charts": charts,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput saved to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
