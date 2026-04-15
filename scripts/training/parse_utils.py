"""
Shared parsing utilities for all OCR-based horoscope parsers.

Extracted from 02_parse_horoscopes.py to enable reuse across Cluster A/B/C parsers.
Each parser imports these functions rather than duplicating them.
"""

from __future__ import annotations

import json
import re
from datetime import date, time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CITIES_FILE = DATA_DIR / "geocoding" / "indian_cities.json"

# ─── Constants ─────────────────────────────────────────────────────────────

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

EVENT_KEYWORDS = {
    "marriage": ["married", "marriage", "wedding", "wed"],
    "career": ["appointed", "promotion", "career", "job", "employed", "service", "office", "minister", "elected", "presidency"],
    "child": ["child", "son", "daughter", "born a son", "born a daughter", "childbirth"],
    "property": ["property", "house", "land", "purchased", "acquired"],
    "health": ["illness", "disease", "health", "accident", "death", "died", "surgery", "hospital", "passed away", "assassinated", "killed"],
}

LEGENDARY_FIGURES = {
    "sri krishna", "jesus christ", "prophet mahamud", "prophet muhammad",
    "sri adi sankaracharya", "sri ramanujacharya", "guru nanak", "sri chaitanya",
}

ANCIENT_CUTOFF_YEAR = 500

# India coordinate ranges for filtering
INDIA_LAT_RANGE = (6.0, 37.0)
INDIA_LON_RANGE = (67.0, 98.0)

# Western location keywords for Indian-only filtering
WESTERN_KEYWORDS = [
    "italy", "england", "france", "germany", "america", "london", "paris",
    "new york", "sweden", "switzerland", "austria", "spain", "portugal",
    "holland", "netherlands", "belgium", "scotland", "ireland", "russia",
    "egypt", "greece", "rome", "ulm", "edinburgh", "vienna",
]


# ─── City Geocoding ───────────────────────────────────────────────────────

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


# ─── Indian-Only Filter ───────────────────────────────────────────────────

def is_indian_chart(
    lat: float | None,
    lon: float | None,
    place_name: str | None,
    text_block: str,
    city_lookup: dict[str, tuple[float, float]] | None = None,
) -> bool | None:
    """Determine if a chart is Indian based on coordinates, place name, or text clues.

    Returns True (Indian), False (non-Indian), or None (uncertain).
    """
    # 1. Coordinate check (most reliable)
    if lat is not None and lon is not None:
        if INDIA_LAT_RANGE[0] <= lat <= INDIA_LAT_RANGE[1] and INDIA_LON_RANGE[0] <= lon <= INDIA_LON_RANGE[1]:
            return True
        return False

    # 2. City name check against geocoding lookup
    if place_name and city_lookup:
        if place_name.lower() in city_lookup:
            return True

    # 3. Time standard check: I.S.T. = Indian
    if re.search(r"I\.?\s*S\.?\s*T", text_block):
        return True

    # 4. G.M.T. = definitely not Indian
    if re.search(r"G\.?\s*M\.?\s*T", text_block):
        return False

    # 5. Western location keywords
    text_lower = text_block.lower()
    for kw in WESTERN_KEYWORDS:
        if kw in text_lower:
            return False

    return None  # uncertain


# ─── Birth Details Pattern ────────────────────────────────────────────────

# Notable Horoscopes format: "Birth Details. — *19th July 3228 B.C...."
BIRTH_DETAILS_PATTERN = re.compile(
    r"Birth\s+Details?\s*[.—\-]+\s*\*?\s*(?:Born\s+on\s+)?(.+?)(?:\n\n|\n(?=[A-Z]))",
    re.IGNORECASE | re.DOTALL,
)

# Date patterns (multiple formats)
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
    # "8-8-1912" or "12-2-1856"
    re.compile(
        r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})",
    ),
]

# Time patterns
TIME_PATTERNS = [
    # midnight
    re.compile(r"(?:at\s+)?(?:about\s+)?midnight", re.IGNORECASE),
    # noon
    re.compile(r"(?:at\s+)?(?:about\s+)?noon", re.IGNORECASE),
    # "at 7-35 p.m." (HH:MM am/pm)
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


# ─── Coordinate Extraction ────────────────────────────────────────────────

_DEG = r"""[°DJ~]"""

# Standard Lat...Long order
LATLON_PATTERN = re.compile(
    r"L[ae]t[.,]?\s*"
    r"(\d[\d ]*)\s*" + _DEG + r"+\s*"
    r"(?:(\d[\d ]*)\s*['\u2019\u201A]?\s*)?"
    r"([NS])"
    r"[^A-Za-z]*?"
    r"L[oa]ng[.,]?\s*"
    r"(\d[\d ]*)\s*" + _DEG + r"+\s*"
    r"(?:(\d[\d ]*)\s*['\u2019\u201A]?\s*)?"
    r"([EWS])",
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

# Time-based longitude: "5h. 10m. 20s. E."
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

# Inline coordinate pattern for HPA/technique books: "(12° N. and 76° 38' E.)"
INLINE_COORD_PATTERN = re.compile(
    r"\(?\s*(\d+)\s*[°]\s*(?:(\d+)\s*['\u2019]?\s*)?([NS])\s*"
    r"(?:\.?\s*(?:and|[,;])\s*)"
    r"(\d+)\s*[°]\s*(?:(\d+)\s*['\u2019]?\s*)?([EW])\s*\)?",
    re.IGNORECASE,
)

# OCR artifact pattern
_OCR_ARTIFACT = re.compile(r"(\d+)[°](\d+)CT", re.IGNORECASE)


def _clean_coord_number(s: str) -> float:
    """Strip internal spaces from OCR numbers: '1 3' → 13."""
    return float(s.replace(" ", ""))


def extract_latlon(text: str) -> tuple[float | None, float | None]:
    """Extract latitude and longitude from text, handling all OCR variations.

    Returns (latitude, longitude) or (None, None).
    """
    # Pre-clean OCR artifacts
    cleaned = _OCR_ARTIFACT.sub(lambda m: f"{m.group(1)}°{m.group(2)}0'", text)
    cleaned = re.sub(r"(\d)\s*°(\d+)°", r"\1°\2'", cleaned)

    # Try time-based longitude first (more specific)
    match = LATLON_TIME_PATTERN.search(cleaned)
    if match:
        g = match.groups()
        lat = _clean_coord_number(g[0]) + _clean_coord_number(g[1] or "0") / 60.0
        if g[2].upper() == "S":
            lat = -lat
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

    # Try inline coordinate pattern: "(12° N. and 76° 38' E.)"
    match = INLINE_COORD_PATTERN.search(cleaned)
    if match:
        g = match.groups()
        lat = float(g[0]) + float(g[1] or 0) / 60.0
        if g[2].upper() == "S":
            lat = -lat
        lon = float(g[3]) + float(g[4] or 0) / 60.0
        if g[5].upper() == "W":
            lon = -lon
        return lat, lon

    return None, None


# ─── Place Extraction ──────────────────────────────────────────────────────

PLACE_PATTERNS = [
    re.compile(r"(?:Place|Born\s+at|born\s+at|place\s+of\s+birth)\s*[:;]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", re.IGNORECASE),
    re.compile(r"at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[,.]", re.IGNORECASE),
]


# ─── Event Date Pattern ────────────────────────────────────────────────────

EVENT_DATE_PATTERN = re.compile(
    r"in\s+(\d{4})|in\s+([A-Za-z]+)\s+(\d{4})|"
    r"on\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})|"
    r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})",
    re.IGNORECASE,
)


# ─── Extraction Functions ──────────────────────────────────────────────────

def extract_birth_date(text: str, use_birth_details_section: bool = True) -> tuple[date | None, bool, list[str]]:
    """Extract birth date from block text.

    Returns (date, is_bc, warnings). B.C. dates return is_bc=True.
    If use_birth_details_section is True, searches for "Birth Details" section first.
    """
    warnings: list[str] = []

    search_text = text
    if use_birth_details_section:
        bd_match = BIRTH_DETAILS_PATTERN.search(text)
        if bd_match:
            search_text = bd_match.group(1)

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


def extract_birth_time(text: str, use_birth_details_section: bool = True) -> tuple[time | None, list[str]]:
    """Extract birth time from block text."""
    warnings: list[str] = []

    search_text = text
    if use_birth_details_section:
        bd_match = BIRTH_DETAILS_PATTERN.search(text)
        if bd_match:
            search_text = bd_match.group(1)

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

    # Check hour-only am/pm
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
            avg_hour += 12
        warnings.append(f"Approximate time: between {h1} and {h2} at night, using {avg_hour}:00")
        return time(avg_hour, 0), warnings

    # Try broader search in full text
    for pattern in TIME_PATTERNS[2:]:
        match = pattern.search(text[:500])
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3:
                    hour, minute = int(groups[0]), int(groups[1])
                    ampm = groups[2].lower().replace(".", "")
                    if "p" in ampm and hour < 12:
                        hour += 12
                    elif "a" in ampm and hour == 12:
                        hour = 0
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return time(hour, minute), warnings
                elif len(groups) == 2:
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

    explicit_lat, explicit_lon = extract_latlon(text)
    has_explicit_coords = explicit_lat is not None and explicit_lon is not None

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
    """Determine birth data reliability level."""
    name_lower = person_name.lower().strip()

    if name_lower in LEGENDARY_FIGURES:
        return "legendary"

    if birth_date is None:
        return "legendary"

    if birth_date.year < ANCIENT_CUTOFF_YEAR:
        return "low"

    has_approx_time = any("approximate" in w.lower() or "about" in w.lower() for w in warnings)
    if has_approx_time:
        return "medium"

    return "high"
