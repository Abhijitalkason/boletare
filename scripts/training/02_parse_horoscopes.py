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
from datetime import date, time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OCR_FILE = DATA_DIR / "training" / "raw" / "notable_horoscopes_ocr.txt"
OUTPUT_FILE = DATA_DIR / "training" / "notable_horoscopes.json"
CITIES_FILE = DATA_DIR / "geocoding" / "indian_cities.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Month name to number mapping
MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

# Event keywords to EventType mapping
EVENT_KEYWORDS = {
    "marriage": ["married", "marriage", "wedding", "wed"],
    "career": ["appointed", "promotion", "career", "job", "employed", "service", "office", "minister", "elected", "presidency"],
    "child": ["child", "son", "daughter", "born a son", "born a daughter", "childbirth"],
    "property": ["property", "house", "land", "purchased", "acquired"],
    "health": ["illness", "disease", "health", "accident", "death", "died", "surgery", "hospital", "passed away", "assassinated", "killed"],
}

# Historical figures with legendary/uncertain birth data
LEGENDARY_FIGURES = {
    "sri krishna", "jesus christ", "prophet mahamud", "prophet muhammad",
    "sri adi sankaracharya", "sri ramanujacharya", "guru nanak", "sri chaitanya",
}

ANCIENT_CUTOFF_YEAR = 500  # Before 500 AD = ancient/uncertain


def load_cities() -> dict[str, tuple[float, float]]:
    """Load city geocoding lookup. Returns {lowercase_name: (lat, lon)}."""
    with open(CITIES_FILE) as f:
        data = json.load(f)

    lookup: dict[str, tuple[float, float]] = {}
    for city in data["cities"]:
        coords = (city["latitude"], city["longitude"])
        lookup[city["name"].lower()] = coords
        for alias in city.get("aliases", []):
            lookup[alias.lower()] = coords
    return lookup


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


# ─── Stage 2: Field Extraction ──────────────────────────────────────────────

# Birth Details pattern for Notable Horoscopes format:
# "Birth Details. — *19th July 3228 B.C., at about midnight"
# "Birth Details.— Born on 12th February 1809 at about 2 a.m. (L.M.T.)"
BIRTH_DETAILS_PATTERN = re.compile(
    r"Birth\s+Details?\s*[.—\-]+\s*\*?\s*(?:Born\s+on\s+)?(.+?)(?:\n\n|\n(?=[A-Z]))",
    re.IGNORECASE | re.DOTALL,
)

# Date patterns
DATE_PATTERNS = [
    # "19th July 3228 B.C." or "8th August 1912"
    re.compile(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{1,4})\s*(B\.?\s*C\.?|A\.?\s*D\.?)?",
        re.IGNORECASE,
    ),
    # "July 19, 1912"
    re.compile(
        r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{1,4})\s*(B\.?\s*C\.?|A\.?\s*D\.?)?",
        re.IGNORECASE,
    ),
    # "8-8-1912"
    re.compile(
        r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})",
    ),
]

# Time patterns
TIME_PATTERNS = [
    # "at about midnight" / "at midnight"
    re.compile(r"(?:at\s+)?(?:about\s+)?midnight", re.IGNORECASE),
    # "at about 2 a.m." / "at 7-35 p.m." / "at about noon"
    re.compile(r"(?:at\s+)?(?:about\s+)?noon", re.IGNORECASE),
    # "at 7-35 p.m." / "at about 2 a.m." / "10 and 12 at night"
    re.compile(
        r"(?:at\s+)?(?:about\s+)?(\d{1,2})[-:.]\s*(\d{2})\s*(a\.?m\.?|p\.?m\.?)",
        re.IGNORECASE,
    ),
    # "at about 2 a.m." (hour only)
    re.compile(
        r"(?:at\s+)?(?:about\s+)?(\d{1,2})\s+(a\.?m\.?|p\.?m\.?)",
        re.IGNORECASE,
    ),
    # "between 10 and 12 at night"
    re.compile(
        r"between\s+(\d{1,2})\s+and\s+(\d{1,2})\s+at\s+night",
        re.IGNORECASE,
    ),
]

# ─── Coordinate Extraction (robust against OCR artifacts) ─────────────────

# Degree symbol variants: °, D, J, ~, 0 (zero adjacent to space), double-°
_DEG = r"""[°DJ~]"""  # OCR produces D, J, ~ instead of °

# Standard Lat/Lon: "Lat. 27° 25' N., Long. 77° 41' E."
# Also handles: Lat,  Let.  Lang.  reversed order  curly quotes  missing symbols
LATLON_PATTERN = re.compile(
    r"L[ae]t[.,]?\s*"                          # "Lat." "Lat," "Lat" "Let."
    r"(\d[\d ]*)\s*" + _DEG + r"+\s*"          # degrees (may have spaces: "1 3°")
    r"(?:(\d[\d ]*)\s*['\u2019\u201A]?\s*)?"   # optional minutes (curly quotes)
    r"([NS])"                                   # direction
    r"[^A-Za-z]*?"                              # separator (punctuation, spaces)
    r"L[oa]ng[.,]?\s*"                          # "Long." "Long," "Lang."
    r"(\d[\d ]*)\s*" + _DEG + r"+\s*"          # degrees
    r"(?:(\d[\d ]*)\s*['\u2019\u201A]?\s*)?"   # optional minutes
    r"([EWS])",                                 # direction (S=typo for E sometimes)
    re.IGNORECASE,
)

# Reversed order: "Long. 88° 25' E., Lat. 23° 23' N."
LATLON_REVERSED_PATTERN = re.compile(
    r"L[oa]ng[.,]?\s*"
    r"(\d[\d ]*)\s*" + _DEG + r"+\s*"
    r"(?:(\d[\d ]*)\s*['\u2019\u201A]?\s*)?"
    r"([EW])"
    r"[^A-Za-z]*?"
    r"L[ae]t[.,]?\s*"
    r"(\d[\d ]*)\s*" + _DEG + r"+\s*"
    r"(?:(\d[\d ]*)\s*['\u2019\u201A]?\s*)?"
    r"([NS])",
    re.IGNORECASE,
)

# Time-based longitude: "5h. 10m. 20s. E." → h×15 + m×0.25 + s×(1/240)
LATLON_TIME_PATTERN = re.compile(
    r"L[ae]t[.,]?\s*"
    r"(\d[\d ]*)\s*" + _DEG + r"+\s*"
    r"(?:(\d[\d ]*)\s*['\u2019\u201A]?\s*)?"
    r"([NS])"
    r"[^A-Za-z]*?"
    r"L[oa]ng[.,]?\s*"
    r"(\d+)\s*h\.?\s*(\d+)\s*m\.?\s*(?:(\d+)\s*s\.?)?\s*"
    r"([EW])?\s*",
    re.IGNORECASE,
)

# OCR artifact pattern: "0°3CT" → "0°30'" (common OCR misread)
_OCR_ARTIFACT = re.compile(r"(\d+)[°](\d+)CT", re.IGNORECASE)


def _clean_coord_number(s: str) -> float:
    """Strip internal spaces from OCR numbers: '1 3' → 13, '5 1' → 51."""
    return float(s.replace(" ", ""))


def _extract_latlon(text: str) -> tuple[float | None, float | None]:
    """Extract latitude and longitude from text, handling all OCR variations.

    Returns (latitude, longitude) or (None, None).
    """
    # Pre-clean OCR artifacts like "3CT" → "30"
    cleaned = _OCR_ARTIFACT.sub(lambda m: f"{m.group(1)}°{m.group(2)}0'", text)

    # Try time-based longitude first (more specific pattern)
    match = LATLON_TIME_PATTERN.search(cleaned)
    if match:
        g = match.groups()
        lat = _clean_coord_number(g[0]) + _clean_coord_number(g[1] or "0") / 60.0
        if g[2].upper() == "S":
            lat = -lat
        # Convert hours/minutes/seconds to degrees
        lon = int(g[3]) * 15.0 + int(g[4]) * 0.25
        if g[5]:
            lon += int(g[5]) / 240.0
        if g[6] and g[6].upper() == "W":
            lon = -lon
        return lat, lon

    # Try standard Lat...Long order
    match = LATLON_PATTERN.search(cleaned)
    if match:
        g = match.groups()
        lat = _clean_coord_number(g[0]) + _clean_coord_number(g[1] or "0") / 60.0
        if g[2].upper() == "S":
            lat = -lat
        lon = _clean_coord_number(g[3]) + _clean_coord_number(g[4] or "0") / 60.0
        if g[5].upper() == "W":
            lon = -lon
        return lat, lon

    # Try reversed Long...Lat order
    match = LATLON_REVERSED_PATTERN.search(cleaned)
    if match:
        g = match.groups()
        lon = _clean_coord_number(g[0]) + _clean_coord_number(g[1] or "0") / 60.0
        if g[2].upper() == "W":
            lon = -lon
        lat = _clean_coord_number(g[3]) + _clean_coord_number(g[4] or "0") / 60.0
        if g[5].upper() == "S":
            lat = -lat
        return lat, lon

    return None, None

# Place patterns
PLACE_PATTERNS = [
    re.compile(r"(?:Place|Born\s+at|born\s+at|place\s+of\s+birth)\s*[:;]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", re.IGNORECASE),
    re.compile(r"at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[,.]", re.IGNORECASE),
]

# Event date patterns (year in narrative)
EVENT_DATE_PATTERN = re.compile(
    r"in\s+(\d{4})|in\s+([A-Za-z]+)\s+(\d{4})|"
    r"on\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})|"
    r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})",
    re.IGNORECASE,
)


def extract_birth_date(text: str) -> tuple[date | None, bool, list[str]]:
    """Extract birth date from block text.

    Returns (date, is_bc, warnings). B.C. dates return is_bc=True.
    """
    warnings: list[str] = []

    # Look specifically in Birth Details section first
    bd_match = BIRTH_DETAILS_PATTERN.search(text)
    search_text = bd_match.group(1) if bd_match else text

    for i, pattern in enumerate(DATE_PATTERNS):
        match = pattern.search(search_text)
        if not match:
            continue

        groups = match.groups()
        try:
            if i == 0:  # "19th July 3228 B.C."
                day, month_str, year = int(groups[0]), groups[1].lower(), int(groups[2])
                is_bc = bool(groups[3] and "b" in groups[3].lower())
                month = MONTH_MAP.get(month_str)
                if month and 1 <= day <= 31:
                    if is_bc or year < 100:
                        # For B.C. or very old dates, use a proxy year for computation
                        warnings.append(f"Ancient date: {day} {groups[1]} {year} {'B.C.' if is_bc else 'A.D.'}")
                        return None, is_bc, warnings
                    return date(year, month, day), False, warnings
            elif i == 1:  # "July 19, 1912"
                month_str, day, year = groups[0].lower(), int(groups[1]), int(groups[2])
                is_bc = bool(groups[3] and "b" in groups[3].lower())
                month = MONTH_MAP.get(month_str)
                if month and 1 <= day <= 31:
                    if is_bc or year < 100:
                        warnings.append(f"Ancient date: {groups[0]} {day} {year} {'B.C.' if is_bc else 'A.D.'}")
                        return None, is_bc, warnings
                    return date(year, month, day), False, warnings
            elif i == 2:  # "8-8-1912"
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day), False, warnings
        except (ValueError, TypeError):
            warnings.append(f"Date parse error with pattern {i}: {groups}")
            continue

    return None, False, warnings + ["Could not extract birth date"]


def extract_birth_time(text: str) -> tuple[time | None, list[str]]:
    """Extract birth time from block text."""
    warnings: list[str] = []

    # Look in Birth Details section first
    bd_match = BIRTH_DETAILS_PATTERN.search(text)
    search_text = bd_match.group(1) if bd_match else text

    # Check midnight
    if TIME_PATTERNS[0].search(search_text):
        return time(0, 0), warnings

    # Check noon
    if TIME_PATTERNS[1].search(search_text):
        return time(12, 0), warnings

    # Check HH:MM am/pm
    match = TIME_PATTERNS[2].search(search_text)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        ampm = match.group(3).lower().replace(".", "")
        if "p" in ampm and hour < 12:
            hour += 12
        elif "a" in ampm and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute), warnings

    # Check hour-only am/pm: "at about 2 a.m."
    match = TIME_PATTERNS[3].search(search_text)
    if match:
        hour = int(match.group(1))
        ampm = match.group(2).lower().replace(".", "")
        if "p" in ampm and hour < 12:
            hour += 12
        elif "a" in ampm and hour == 12:
            hour = 0
        if 0 <= hour <= 23:
            warnings.append("Approximate time (hour only, no minutes)")
            return time(hour, 0), warnings

    # Check "between X and Y at night"
    match = TIME_PATTERNS[4].search(search_text)
    if match:
        h1, h2 = int(match.group(1)), int(match.group(2))
        avg_hour = (h1 + h2) // 2
        if avg_hour < 12:
            avg_hour += 12  # "at night"
        warnings.append(f"Approximate time: between {h1} and {h2} at night, using {avg_hour}:00")
        return time(avg_hour, 0), warnings

    # Try broader search in full text
    for pattern in TIME_PATTERNS[2:]:
        match = pattern.search(text[:500])
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3:  # HH:MM am/pm
                    hour, minute = int(groups[0]), int(groups[1])
                    ampm = groups[2].lower().replace(".", "")
                    if "p" in ampm and hour < 12:
                        hour += 12
                    elif "a" in ampm and hour == 12:
                        hour = 0
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return time(hour, minute), warnings
                elif len(groups) == 2:  # hour am/pm
                    hour = int(groups[0])
                    ampm = groups[1].lower().replace(".", "")
                    if "p" in ampm and hour < 12:
                        hour += 12
                    elif "a" in ampm and hour == 12:
                        hour = 0
                    if 0 <= hour <= 23:
                        return time(hour, 0), warnings + ["Approximate time"]
            except (ValueError, TypeError):
                continue

    return None, warnings + ["Could not extract birth time"]


def extract_place(
    text: str, city_lookup: dict[str, tuple[float, float]]
) -> tuple[str | None, float | None, float | None, int, list[str]]:
    """Extract birth place and coordinates."""
    warnings: list[str] = []

    # Try explicit lat/lon first (very common in Notable Horoscopes)
    explicit_lat, explicit_lon = _extract_latlon(text)
    has_explicit_coords = explicit_lat is not None and explicit_lon is not None

    # Try place name patterns
    place_name = None
    for pattern in PLACE_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() in ("the", "a", "an", "his", "her", "this", "that", "chart", "born", "about", "details"):
                continue
            place_name = candidate
            break

    if place_name:
        coords = city_lookup.get(place_name.lower())
        if coords:
            lat_val, lon_val = coords
            if has_explicit_coords:
                return place_name, explicit_lat, explicit_lon, 1, warnings
            return place_name, lat_val, lon_val, 1, warnings
        else:
            if has_explicit_coords:
                return place_name, explicit_lat, explicit_lon, 2, warnings
            warnings.append(f"Unknown place: {place_name}")
            return place_name, None, None, 2, warnings + ["needs_manual_review: missing coordinates"]

    if has_explicit_coords:
        return "Unknown (coordinates only)", explicit_lat, explicit_lon, 2, warnings

    return None, None, None, 3, warnings + ["Could not extract birth place"]


def extract_gender(text: str) -> str:
    """Infer gender from pronouns."""
    text_lower = text.lower()
    he_count = len(re.findall(r"\bhe\b|\bhis\b|\bhim\b", text_lower))
    she_count = len(re.findall(r"\bshe\b|\bher\b|\bhers\b", text_lower))

    if he_count > she_count:
        return "male"
    elif she_count > he_count:
        return "female"
    return "unknown"


def extract_events(text: str, birth_date: date | None) -> list[dict]:
    """Extract life events from block text."""
    events: list[dict] = []
    text_lower = text.lower()

    for event_type, keywords in EVENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword not in text_lower:
                continue

            sentences = re.split(r"[.;]", text)
            for sentence in sentences:
                if keyword.lower() not in sentence.lower():
                    continue

                for match in EVENT_DATE_PATTERN.finditer(sentence):
                    g = match.groups()
                    event_date = None
                    confidence = "exact"

                    try:
                        if g[0]:  # "in 1938"
                            event_date = date(int(g[0]), 6, 15)
                            confidence = "approximate"
                        elif g[1] and g[2]:  # "in August 1938"
                            month = MONTH_MAP.get(g[1].lower())
                            if month:
                                event_date = date(int(g[2]), month, 15)
                                confidence = "approximate"
                        elif g[3] and g[4] and g[5]:  # "on 15th September 1938"
                            month = MONTH_MAP.get(g[4].lower())
                            if month:
                                event_date = date(int(g[5]), month, int(g[3]))
                        elif g[6] and g[7] and g[8]:  # "15-9-1938"
                            event_date = date(int(g[8]), int(g[7]), int(g[6]))
                    except (ValueError, TypeError):
                        continue

                    if event_date and (birth_date is None or event_date > birth_date):
                        dup = any(
                            e["event_type"] == event_type and e["event_date"] == event_date.isoformat()
                            for e in events
                        )
                        if not dup:
                            events.append({
                                "event_type": event_type,
                                "event_date": event_date.isoformat(),
                                "confidence": confidence,
                            })
                break

    return events


def determine_reliability(person_name: str, birth_date: date | None, warnings: list[str]) -> str:
    """Determine birth data reliability level.

    Returns: "high", "medium", "low", "rectified", or "legendary"
    """
    name_lower = person_name.lower().strip()

    # Legendary/mythological figures
    if name_lower in LEGENDARY_FIGURES:
        return "legendary"

    # Ancient figures (pre-500 AD) — uncertain data
    if birth_date is None:
        return "legendary"

    if birth_date.year < ANCIENT_CUTOFF_YEAR:
        return "low"

    # Check for approximate time indicators
    has_approx_time = any("approximate" in w.lower() or "about" in w.lower() for w in warnings)
    if has_approx_time:
        return "medium"

    return "high"


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
