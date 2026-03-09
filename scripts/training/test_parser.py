"""
Unit tests for horoscope parsing patterns (Notable Horoscopes format).

Tests regex patterns individually and the full block->extraction pipeline.
Covers easy, hard, ambiguous, and incomplete cases.
"""

from __future__ import annotations

import importlib.util
from datetime import date, time
from pathlib import Path

import pytest

# Import functions from 02_parse_horoscopes.py via importlib
_parser_path = Path(__file__).resolve().parent / "02_parse_horoscopes.py"
_spec = importlib.util.spec_from_file_location("parser", _parser_path)
_parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parser)

extract_birth_date = _parser.extract_birth_date
extract_birth_time = _parser.extract_birth_time
extract_place = _parser.extract_place
extract_gender = _parser.extract_gender
extract_events = _parser.extract_events
find_blocks = _parser.find_blocks
parse_block = _parser.parse_block
load_cities = _parser.load_cities
determine_reliability = _parser.determine_reliability

# Load city lookup once
CITY_LOOKUP = load_cities()


# ─── Birth Date Tests ───────────────────────────────────────────────────────

class TestExtractBirthDate:
    def test_day_month_year(self):
        text = "Birth Details. — *8th August 1912"
        result, is_bc, warnings = extract_birth_date(text)
        assert result == date(1912, 8, 8)
        assert is_bc is False

    def test_month_day_year(self):
        text = "Birth Details. — Born on August 8, 1912"
        result, is_bc, warnings = extract_birth_date(text)
        assert result == date(1912, 8, 8)

    def test_bc_date_returns_none(self):
        text = "Birth Details. — *19th July 3228 B.C., at about midnight"
        result, is_bc, warnings = extract_birth_date(text)
        assert result is None
        assert is_bc is True

    def test_numeric_date(self):
        text = "Born: 15/3/1940"
        result, is_bc, warnings = extract_birth_date(text)
        assert result == date(1940, 3, 15)

    def test_no_date(self):
        text = "This chart shows interesting planetary combinations."
        result, is_bc, warnings = extract_birth_date(text)
        assert result is None


# ─── Birth Time Tests ───────────────────────────────────────────────────────

class TestExtractBirthTime:
    def test_midnight(self):
        text = "Birth Details. — *19th July 1912, at about midnight"
        result, warnings = extract_birth_time(text)
        assert result == time(0, 0)

    def test_time_with_pm(self):
        text = "Birth Details. — born at 7-35 p.m."
        result, warnings = extract_birth_time(text)
        assert result == time(19, 35)

    def test_hour_only_am(self):
        text = "Birth Details. — Born on 12th February 1809 at about 2 a.m."
        result, warnings = extract_birth_time(text)
        assert result == time(2, 0)

    def test_between_at_night(self):
        text = "Birth Details. — Born on 22nd July 356 B.C. between 10 and 12 at night."
        result, warnings = extract_birth_time(text)
        assert result == time(23, 0)

    def test_no_time(self):
        text = "The person was born in Bangalore."
        result, warnings = extract_birth_time(text)
        assert result is None


# ─── Place Tests ────────────────────────────────────────────────────────────

class TestExtractPlace:
    def test_latlon(self):
        text = "Lat. 27° 25' N., Long. 77° 41' E."
        place, lat, lon, tier, _ = extract_place(text, CITY_LOOKUP)
        assert lat == pytest.approx(27.4167, abs=0.01)
        assert lon == pytest.approx(77.6833, abs=0.01)

    def test_place_colon(self):
        text = "Place: Bangalore"
        place, lat, lon, tier, _ = extract_place(text, CITY_LOOKUP)
        assert place == "Bangalore"
        assert lat == pytest.approx(12.9716, abs=0.01)
        assert tier == 1

    def test_unknown_place_with_latlon(self):
        text = "(Lat. 40° 43' N., Long. 22° 35' E.) born at Pella."
        place, lat, lon, tier, _ = extract_place(text, CITY_LOOKUP)
        assert place == "Pella"
        assert lat == pytest.approx(40.7167, abs=0.1)

    def test_no_place(self):
        text = "The planetary positions are interesting."
        place, lat, lon, tier, warnings = extract_place(text, CITY_LOOKUP)
        assert place is None


# ─── Gender Tests ───────────────────────────────────────────────────────────

class TestExtractGender:
    def test_male(self):
        text = "He was born in Bangalore. His father was a scholar."
        assert extract_gender(text) == "male"

    def test_female(self):
        text = "She was born in Delhi. Her marriage took place in 1940."
        assert extract_gender(text) == "female"

    def test_unknown(self):
        text = "The native was born in 1912."
        assert extract_gender(text) == "unknown"


# ─── Event Tests ────────────────────────────────────────────────────────────

class TestExtractEvents:
    def test_marriage_event(self):
        text = "In his 16th year, Gautama was married in 1938."
        events = extract_events(text, date(1912, 8, 8))
        types = [e["event_type"] for e in events]
        assert "marriage" in types

    def test_death_event(self):
        text = "He died in 1945 at the age of 60."
        events = extract_events(text, date(1885, 1, 1))
        types = [e["event_type"] for e in events]
        assert "health" in types

    def test_no_events(self):
        text = "The planetary positions are interesting."
        events = extract_events(text, date(1912, 1, 1))
        assert events == []


# ─── Reliability Tests ──────────────────────────────────────────────────────

class TestReliability:
    def test_legendary(self):
        assert determine_reliability("Sri Krishna", None, []) == "legendary"

    def test_ancient(self):
        assert determine_reliability("Alexander", date(356, 7, 22), []) == "low"

    def test_approximate_time(self):
        assert determine_reliability("Lincoln", date(1809, 2, 12), ["Approximate time"]) == "medium"

    def test_high(self):
        assert determine_reliability("Nehru", date(1889, 11, 14), []) == "high"


# ─── Block Identification Tests ─────────────────────────────────────────────

class TestFindBlocks:
    def test_notable_horoscopes_pattern(self):
        text = "Some text\nNo. 1.— SRI KRISHNA\nDetails here\nNo. 2.— GAUTAMA BUDDHA\nMore"
        blocks = find_blocks(text)
        assert len(blocks) == 2
        assert blocks[0][2] == "SRI KRISHNA"
        assert blocks[1][2] == "GAUTAMA BUDDHA"

    def test_no_blocks(self):
        text = "This is just regular text with no horoscope markers."
        blocks = find_blocks(text)
        assert len(blocks) == 0


# ─── Integration: Full Block Parse ──────────────────────────────────────────

class TestParseBlock:
    def test_modern_chart(self):
        """Modern chart with clear date/time/place."""
        text = """No. 59.— JAWAHARLAL NEHRU
Birth Details. — Born on 14th November 1889 at about
11-36 p.m. (Lat. 25° 26' N., Long. 81° 52' E.)
He was a great leader. He married in 1916.
He died in 1964."""
        result = parse_block(0, "No. 59", "JAWAHARLAL NEHRU", text, CITY_LOOKUP, 1)
        assert result is not None
        assert result["birth_date"] == "1889-11-14"
        assert result["birth_time"] == "23:36:00"
        assert result["gender"] == "male"
        assert result["birth_data_reliability"] == "high"
        assert result["id"] == "NH_001"

    def test_bc_date_skipped(self):
        """B.C. dates should be skipped."""
        text = """No. 1.— SRI KRISHNA
Birth Details. — *19th July 3228 B.C., at about midnight
(Lat. 27° 25' N., Long. 77° 41' E.)"""
        result = parse_block(0, "No. 1", "SRI KRISHNA", text, CITY_LOOKUP, 1)
        assert result is None

    def test_missing_time_skipped(self):
        """Block without birth time should be skipped."""
        text = """No. 99.— TEST PERSON
Birth Details. — Born on 5th March 1920"""
        result = parse_block(0, "No. 99", "TEST PERSON", text, CITY_LOOKUP, 1)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
