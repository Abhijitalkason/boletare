"""
Step 2b: Parse horoscope blocks from technique books (Cluster B).

Handles three files:
  - How to Judge a Horoscope (Santhanam translation)
  - How to Judge a Horoscope Vol 1 (Raman)
  - How to Judge a Horoscope Vol 2 (Raman)

Block format:
  "Chart No. 1.—Born on 12-2-1856 at 12-21 p.m. (L.T.) Lat. 18° N., Long. 84° E"

These are technique books: charts illustrate astrological principles.
Events are scattered in surrounding prose, not in structured sections.
Filters for Indian-only charts. Deduplicates by (date, time, lat, lon).
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
    extract_latlon,
    extract_events,
    extract_gender,
    determine_reliability,
    is_indian_chart,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# Source configurations
SOURCES = [
    {
        "ocr_file": DATA_DIR / "training" / "raw" / "judge_horoscope_santhanam_ocr.txt",
        "output_file": DATA_DIR / "training" / "judge_horoscope_santhanam.json",
        "source_name": "judge_horoscope_santhanam",
        "book_url": "https://archive.org/details/how-to-judge-a-horoscope-r.-santhanam",
        "id_prefix": "JHS",
    },
    {
        "ocr_file": DATA_DIR / "training" / "raw" / "judge_horoscope_v1_raman_ocr.txt",
        "output_file": DATA_DIR / "training" / "judge_horoscope_v1_raman.json",
        "source_name": "judge_horoscope_v1_raman",
        "book_url": "https://archive.org/details/raman-how-to-judge-horoscope-2",
        "id_prefix": "JH1",
    },
    {
        "ocr_file": DATA_DIR / "training" / "raw" / "judge_horoscope_v2_raman_ocr.txt",
        "output_file": DATA_DIR / "training" / "judge_horoscope_v2_raman.json",
        "source_name": "judge_horoscope_v2_raman",
        "book_url": "https://archive.org/details/raman-how-to-judge-horoscope-2",
        "id_prefix": "JH2",
    },
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Block delimiter: "Chart No. 1.—Born on 12-2-1856 at 12-21 p.m. (L.T.) Lat. 18° N., Long. 84° E"
# Also handles OCR: "Bom" for "Born", missing periods, varied separators
BLOCK_PATTERN = re.compile(
    r"Chart\s+No\.\s*(\d+)\s*[.\-—]+\s*(?:Born|Bom|Boni)\s+(?:on\s+)?",
    re.IGNORECASE,
)

# Theoretical/general statements to filter out (not biographical)
THEORY_INDICATORS = re.compile(
    r"\bgenerally\b|\busually\b|\bthis yoga\b|\bthe combination\b|\bif the\b|\bwhen the\b|\bthe rule\b",
    re.IGNORECASE,
)

# Biographical indicators (event tied to a specific person)
BIO_INDICATORS = re.compile(
    r"\bthe native\b|\bnative\'s\b|\bhis\b|\bher\b|\bhe\b|\bshe\b|\bthe person\b|\bthe subject\b",
    re.IGNORECASE,
)


def find_chart_blocks(text: str) -> list[tuple[int, str, str]]:
    """Find chart definition blocks (Chart No. X—Born on ...).

    Returns list of (line_number, chart_num, block_text).
    Only returns blocks that have birth data (the definition, not references).
    """
    lines = text.split("\n")
    block_starts: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        match = BLOCK_PATTERN.search(line)
        if match:
            chart_num = match.group(1)
            block_starts.append((i, chart_num))

    blocks: list[tuple[int, str, str]] = []
    for idx, (start_line, chart_num) in enumerate(block_starts):
        # Block extends until next Chart No. definition or 200 lines, whichever comes first
        end_line = block_starts[idx + 1][0] if idx + 1 < len(block_starts) else min(start_line + 200, len(lines))
        block_text = "\n".join(lines[start_line:end_line])
        blocks.append((start_line, chart_num, block_text))

    return blocks


def extract_bio_events(text: str, birth_date, existing_events: list[dict]) -> list[dict]:
    """Extract events only from biographical statements, filtering out theory.

    Uses the standard extract_events() then filters for biographical context
    and adds bare-year events near biographical keywords.
    """
    from datetime import date as _date

    # Standard extraction
    events = extract_events(text, birth_date)

    # Additional: find bare years near event keywords in biographical sentences
    existing_keys = {(e["event_type"], e["event_date"]) for e in events}
    existing_keys.update((e["event_type"], e["event_date"]) for e in existing_events)

    sentences = re.split(r"[.;]", text)
    for sentence in sentences:
        sent_lower = sentence.lower()

        # Skip theoretical statements
        if THEORY_INDICATORS.search(sentence) and not BIO_INDICATORS.search(sentence):
            continue

        # Only process sentences with biographical indicators
        if not BIO_INDICATORS.search(sentence):
            continue

        for event_type, keywords in EVENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword not in sent_lower:
                    continue

                # Find bare years: "died in 1946", "married in 1930", "separated in June 1974"
                for year_match in re.finditer(r"\b(1[89]\d{2})\b", sentence):
                    try:
                        year = int(year_match.group(1))
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

    return events


def parse_source(source: dict, city_lookup: dict[str, tuple[float, float]]) -> dict:
    """Parse a single source file and return the output dict."""
    ocr_file = source["ocr_file"]
    id_prefix = source["id_prefix"]

    if not ocr_file.exists():
        logger.error("OCR file not found: %s", ocr_file)
        return {"source": source["source_name"], "book_url": source["book_url"], "charts": []}

    text = ocr_file.read_text(encoding="utf-8", errors="replace")
    # Clean OCR line breaks
    clean_text = re.sub(r"¬\s*\n\s*", "", text)

    logger.info("Loaded %s: %d chars", ocr_file.name, len(clean_text))

    # Find chart blocks
    blocks = find_chart_blocks(clean_text)
    logger.info("Found %d chart definition blocks in %s", len(blocks), ocr_file.name)

    charts: list[dict] = []
    seen_signatures: set[tuple] = set()  # (birth_date, birth_time, lat, lon) for dedup
    chart_index = 1
    skipped_non_indian = 0
    skipped_duplicate = 0
    skipped_parse_fail = 0

    for line_num, chart_num, block_text in blocks:
        warnings: list[str] = []

        # Extract birth date from the block (DD-MM-YYYY format common in these books)
        birth_date, _is_bc, date_warnings = extract_birth_date(block_text, use_birth_details_section=False)
        warnings.extend(date_warnings)

        if birth_date is None:
            skipped_parse_fail += 1
            continue

        # Extract birth time
        birth_time, time_warnings = extract_birth_time(block_text, use_birth_details_section=False)
        warnings.extend(time_warnings)

        if birth_time is None:
            skipped_parse_fail += 1
            continue

        # Extract coordinates
        lat, lon = extract_latlon(block_text)

        # Indian-only filter
        indian = is_indian_chart(lat, lon, None, block_text, city_lookup)
        if indian is False:
            skipped_non_indian += 1
            continue

        # Deduplication by signature
        sig = (birth_date.isoformat(), birth_time.isoformat(), round(lat or 0, 1), round(lon or 0, 1))
        if sig in seen_signatures:
            skipped_duplicate += 1
            continue
        seen_signatures.add(sig)

        # Try place name from city lookup
        place = None
        if lat is not None and lon is not None:
            # Find closest known city
            for city_name, (clat, clon) in city_lookup.items():
                if abs(clat - lat) < 0.5 and abs(clon - lon) < 0.5:
                    place = city_name.title()
                    break

        # Gender from pronouns in surrounding text
        gender = extract_gender(block_text)

        # Birth time tier
        if lat is not None and lon is not None:
            tier = 1 if place else 2
        else:
            tier = 3

        # Extract events (biographical only, filter out theory)
        events = extract_bio_events(block_text, birth_date, [])

        needs_review = (lat is None or lon is None) or not events

        # Default coordinates
        if lat is None:
            lat = 20.5937
        if lon is None:
            lon = 78.9629

        reliability = determine_reliability("", birth_date, warnings)

        chart_id = f"{id_prefix}_{chart_index:03d}"
        excerpt = block_text[:200].replace("\n", " ")

        charts.append({
            "id": chart_id,
            "person_name": "",
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
        })
        chart_index += 1

    # Summary
    total_events = sum(len(c["events"]) for c in charts)
    event_dist: dict[str, int] = {}
    for c in charts:
        for e in c["events"]:
            event_dist[e["event_type"]] = event_dist.get(e["event_type"], 0) + 1

    print(f"\n{'='*60}")
    print(f"  {source['source_name']}")
    print(f"{'='*60}")
    print(f"  Blocks found:        {len(blocks)}")
    print(f"  Parsed (Indian):     {len(charts)}")
    print(f"  Skipped non-Indian:  {skipped_non_indian}")
    print(f"  Skipped duplicates:  {skipped_duplicate}")
    print(f"  Skipped parse fail:  {skipped_parse_fail}")
    print(f"  Total events:        {total_events}")
    if event_dist:
        print(f"  Event distribution:  {event_dist}")
    print(f"{'='*60}")

    return {
        "source": source["source_name"],
        "book_url": source["book_url"],
        "charts": charts,
    }


def main() -> int:
    city_lookup = load_cities()
    print(f"Loaded {len(city_lookup)} city entries for geocoding.")

    total_charts = 0
    total_events = 0

    for source in SOURCES:
        result = parse_source(source, city_lookup)

        # Write output
        output_file = source["output_file"]
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  Output saved to {output_file}")

        total_charts += len(result["charts"])
        total_events += sum(len(c["events"]) for c in result["charts"])

    print(f"\n{'='*60}")
    print(f"GRAND TOTAL — All Technique Books")
    print(f"{'='*60}")
    print(f"  Total Indian charts: {total_charts}")
    print(f"  Total events:        {total_events}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
