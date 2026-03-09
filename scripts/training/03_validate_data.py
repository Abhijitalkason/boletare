"""
Step 3: Validate extracted horoscope data quality.

Uses Pydantic schema to validate structure, plus domain-specific checks
for dates, coordinates, ages, duplicates, and OCR digit errors.
Built FIRST (before parser) to define the data contract.
"""

from __future__ import annotations

import json
import sys
from datetime import date, time
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training"
INPUT_FILE = DATA_DIR / "notable_horoscopes.json"
REPORT_FILE = DATA_DIR / "validation_report.txt"

# Domain constants
INDIA_LAT_RANGE = (6.0, 37.0)
INDIA_LON_RANGE = (67.0, 98.0)
BIRTH_YEAR_RANGE = (500, 2000)  # Notable Horoscopes includes historical figures
AGE_RANGES = {
    "marriage": (14, 60),
    "career": (16, 70),
    "child": (18, 55),
    "property": (18, 80),
    "health": (0, 100),
}


class EventEntry(BaseModel):
    event_type: str
    event_date: date
    confidence: str = "exact"

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed = {"marriage", "career", "child", "property", "health"}
        if v.lower() not in allowed:
            raise ValueError(f"Invalid event_type: {v}. Must be one of {allowed}")
        return v.lower()

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        if v not in ("exact", "approximate"):
            raise ValueError(f"confidence must be 'exact' or 'approximate', got '{v}'")
        return v


VALID_RELIABILITY = {"high", "medium", "low", "rectified", "legendary"}


class ChartEntry(BaseModel):
    id: str
    person_name: str = ""
    birth_date: date
    birth_time: time
    birth_place: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone_offset: float
    birth_time_tier: int = Field(ge=1, le=3)
    gender: str
    birth_data_reliability: str = "medium"
    events: list[EventEntry]
    raw_text_excerpt: str = ""
    needs_manual_review: bool = False
    parse_warnings: list[str] = []

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v.lower() not in ("male", "female", "unknown"):
            raise ValueError(f"gender must be male/female/unknown, got '{v}'")
        return v.lower()

    @field_validator("birth_data_reliability")
    @classmethod
    def validate_reliability(cls, v: str) -> str:
        if v.lower() not in VALID_RELIABILITY:
            raise ValueError(f"birth_data_reliability must be one of {VALID_RELIABILITY}, got '{v}'")
        return v.lower()


class ValidationReport:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.chart_count = 0
        self.event_count = 0
        self.valid_count = 0
        self.review_count = 0

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        print(f"  ERROR: {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"  WARN:  {msg}")

    def add_info(self, msg: str) -> None:
        self.info.append(msg)

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "VALIDATION REPORT",
            "=" * 60,
            f"Charts total:        {self.chart_count}",
            f"Charts valid:        {self.valid_count}",
            f"Charts need review:  {self.review_count}",
            f"Total events:        {self.event_count}",
            f"Errors:              {len(self.errors)}",
            f"Warnings:            {len(self.warnings)}",
            "",
        ]
        if self.errors:
            lines.append("--- ERRORS ---")
            for e in self.errors:
                lines.append(f"  {e}")
            lines.append("")
        if self.warnings:
            lines.append("--- WARNINGS ---")
            for w in self.warnings:
                lines.append(f"  {w}")
            lines.append("")
        if self.info:
            lines.append("--- INFO ---")
            for i in self.info:
                lines.append(f"  {i}")
            lines.append("")

        # Event type distribution
        lines.append("--- EVENT TYPE DISTRIBUTION ---")
        for et, count in sorted(self._event_dist.items()):
            lines.append(f"  {et}: {count}")

        lines.append("=" * 60)
        return "\n".join(lines)

    _event_dist: dict[str, int] = {}


def validate_chart(chart: ChartEntry, report: ValidationReport) -> None:
    cid = chart.id

    # Birth year range
    if not (BIRTH_YEAR_RANGE[0] <= chart.birth_date.year <= BIRTH_YEAR_RANGE[1]):
        report.error(f"{cid}: birth_date year {chart.birth_date.year} outside {BIRTH_YEAR_RANGE}")

    # OCR digit sanity on birth_time
    if chart.birth_time.minute > 59:
        report.error(f"{cid}: birth_time minutes={chart.birth_time.minute} > 59 (OCR error?)")
    if chart.birth_time.hour > 23:
        report.error(f"{cid}: birth_time hour={chart.birth_time.hour} > 23 (OCR error?)")

    # Coordinate sanity (India range)
    if not (INDIA_LAT_RANGE[0] <= chart.latitude <= INDIA_LAT_RANGE[1]):
        report.warn(f"{cid}: latitude {chart.latitude} outside India range {INDIA_LAT_RANGE}")
    if not (INDIA_LON_RANGE[0] <= chart.longitude <= INDIA_LON_RANGE[1]):
        report.warn(f"{cid}: longitude {chart.longitude} outside India range {INDIA_LON_RANGE}")

    # Event validations
    for evt in chart.events:
        report.event_count += 1
        report._event_dist[evt.event_type] = report._event_dist.get(evt.event_type, 0) + 1

        # Event after birth
        if evt.event_date < chart.birth_date:
            report.error(f"{cid}: event {evt.event_type} date {evt.event_date} before birth {chart.birth_date}")

        # Event before 2025
        if evt.event_date.year > 2025:
            report.error(f"{cid}: event {evt.event_type} date {evt.event_date} in the future")

        # Age sanity
        age_at_event = (evt.event_date - chart.birth_date).days / 365.25
        age_range = AGE_RANGES.get(evt.event_type)
        if age_range and not (age_range[0] <= age_at_event <= age_range[1]):
            report.warn(
                f"{cid}: {evt.event_type} at age {age_at_event:.1f} "
                f"outside expected range {age_range}"
            )

    if chart.needs_manual_review:
        report.review_count += 1


def check_duplicates(charts: list[ChartEntry], report: ValidationReport) -> None:
    seen: dict[str, str] = {}
    for chart in charts:
        key = f"{chart.birth_date}|{chart.birth_time}|{chart.birth_place}"
        if key in seen:
            report.warn(f"Possible duplicate: {chart.id} and {seen[key]} (same birth data)")
        else:
            seen[key] = chart.id


def main() -> int:
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return 1

    with open(INPUT_FILE) as f:
        data = json.load(f)

    charts_raw = data.get("charts", [])
    report = ValidationReport()
    report.chart_count = len(charts_raw)
    report._event_dist = {}

    print(f"Validating {len(charts_raw)} charts from {INPUT_FILE.name}...\n")

    valid_charts: list[ChartEntry] = []
    for i, raw in enumerate(charts_raw):
        try:
            chart = ChartEntry(**raw)
            validate_chart(chart, report)
            valid_charts.append(chart)
            report.valid_count += 1
        except Exception as e:
            report.error(f"Chart index {i} (id={raw.get('id', '?')}): Schema error: {e}")

    check_duplicates(valid_charts, report)

    summary = report.summary()
    print(f"\n{summary}")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(summary)
    print(f"\nReport saved to {REPORT_FILE}")

    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
