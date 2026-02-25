"""
Jyotish AI -- Gate 3: Double Transit Window Detection

Scans 24 months (configurable) of Jupiter and Saturn transits to identify
periods when BOTH slow-moving planets simultaneously occupy houses that are
kendra or trikona from the event house.  This "double transit" condition is
a classical Vedic timing requirement for major life events.

Algorithm
---------
1. Derive the event house from the event type.
2. Compute favorable houses = kendras + trikonas from the event house.
3. For each scanned month, check whether Jupiter and Saturn each transit
   a sign that maps to one of the favorable houses.
4. When both are favorable ("double transit active"), compute a BAV-weighted
   transit score using the Sarva Ashtakavarga points of each transit sign.
5. Aggregate into a single gate score that blends coverage (how many months
   are active) with intensity (the peak BAV score across active months).

Score formula
~~~~~~~~~~~~~
    score = min(1.0, (active_months / total_months) * 0.5
                     + peak_bav_normalized * 0.5)

Both components are independently clamped to [0.0, 1.0].
"""

from __future__ import annotations

from datetime import date

from jyotish_ai.domain.types import Planet, Sign, EventType
from jyotish_ai.domain.models import BirthChart, GateResult, TransitWindow
from jyotish_ai.domain.constants import (
    EVENT_HOUSE_MAP,
    get_kendra_trikona,
    sign_to_house,
    house_to_sign,
)
from jyotish_ai.engine.transit import scan_monthly_transits


# ── SAV normalisation bounds (same as Gate 1) ──────────────────────
_SAV_MIN: int = 18
_SAV_MAX: int = 37

# ── Gate sufficiency threshold ──────────────────────────────────────
_DEFAULT_THRESHOLD: float = 0.3


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _normalize_sav(raw: float) -> float:
    """Normalise a raw SAV score to [0.0, 1.0].

    Uses the standard range [18, 37].
    """
    return _clamp((raw - _SAV_MIN) / (_SAV_MAX - _SAV_MIN))


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def evaluate_transit(
    chart: BirthChart,
    event_type: EventType,
    query_date: date,
    scan_months: int = 24,
    ayanamsha: str = "lahiri",
) -> GateResult:
    """Gate 3: Evaluate double transit windows for event timing.

    Scans *scan_months* months of Jupiter and Saturn transits starting
    from *query_date* and identifies periods where both planets
    simultaneously occupy kendra/trikona houses from the event house.

    Args:
        chart: Complete birth chart produced by Layer 1.
        event_type: The life event being predicted (e.g. MARRIAGE).
        query_date: Start date for the transit scan.
        scan_months: Number of months to scan (default 24).
        ayanamsha: Ayanamsha system ("lahiri" or "kp").

    Returns:
        A ``GateResult`` with the normalised gate score (0.0-1.0),
        sufficiency flag, and a ``details`` dict containing the full
        month-by-month transit timeline, peak month, and counts.
    """
    # ── 1. Resolve event house and favorable houses ────────────────
    event_house: int = EVENT_HOUSE_MAP[event_type]
    favorable_houses: list[int] = get_kendra_trikona(event_house)

    # ── 2. Scan monthly transits for Jupiter and Saturn ────────────
    raw_transits: list[dict] = scan_monthly_transits(
        start_date=query_date,
        months=scan_months,
        planets=[Planet.JUPITER, Planet.SATURN],
        ayanamsha=ayanamsha,
    )

    # ── 3. Build TransitWindow for each scanned month ──────────────
    timeline: list[TransitWindow] = []

    for entry in raw_transits:
        month_str: str = entry["month"]
        positions: dict = entry["positions"]

        # Extract Jupiter position
        _jup_arcsec, jupiter_sign = positions[Planet.JUPITER]
        jupiter_house: int = sign_to_house(jupiter_sign, chart.ascendant_sign)

        # Extract Saturn position
        _sat_arcsec, saturn_sign = positions[Planet.SATURN]
        saturn_house: int = sign_to_house(saturn_sign, chart.ascendant_sign)

        # Check favorability
        jupiter_favorable: bool = jupiter_house in favorable_houses
        saturn_favorable: bool = saturn_house in favorable_houses
        double_transit_active: bool = jupiter_favorable and saturn_favorable

        # Compute transit BAV score
        transit_bav_score: float = 0.0
        if double_transit_active:
            jupiter_sav: int = chart.ashtakavarga.sav.get(
                jupiter_sign.name, _SAV_MIN,
            )
            saturn_sav: int = chart.ashtakavarga.sav.get(
                saturn_sign.name, _SAV_MIN,
            )
            transit_bav: float = (jupiter_sav + saturn_sav) / 2.0
            transit_bav_score = _normalize_sav(transit_bav)

        # Build the TransitWindow for this month
        tw = TransitWindow(
            month=month_str,
            jupiter_sign=jupiter_sign.name,
            saturn_sign=saturn_sign.name,
            jupiter_house=jupiter_house,
            saturn_house=saturn_house,
            jupiter_in_favorable=jupiter_favorable,
            saturn_in_favorable=saturn_favorable,
            double_transit_active=double_transit_active,
            transit_bav_score=transit_bav_score,
        )
        timeline.append(tw)

    # ── 4. Compute overall Gate 3 score ────────────────────────────
    active_months: list[TransitWindow] = [
        tw for tw in timeline if tw.double_transit_active
    ]
    active_count: int = len(active_months)

    if active_count == 0:
        score: float = 0.0
        peak_month_str: str | None = None
        peak_bav: float = 0.0
    else:
        # Find the peak month (highest transit_bav_score)
        peak_tw: TransitWindow = max(
            active_months, key=lambda tw: tw.transit_bav_score,
        )
        peak_month_str = peak_tw.month
        peak_bav = peak_tw.transit_bav_score

        # Composite score: coverage (50%) + intensity (50%)
        coverage_component: float = (active_count / scan_months) * 0.5
        intensity_component: float = peak_bav * 0.5
        score = min(1.0, coverage_component + intensity_component)
        score = _clamp(score)

    # ── 5. Assemble result ─────────────────────────────────────────
    details: dict = {
        "event_house": event_house,
        "favorable_houses": favorable_houses,
        "active_months_count": active_count,
        "total_months": scan_months,
        "peak_month": peak_month_str,
        "peak_bav_score": peak_bav,
        "timeline": [tw.model_dump() for tw in timeline],
    }

    return GateResult(
        gate_name="gate3_transit",
        score=score,
        is_sufficient=score >= _DEFAULT_THRESHOLD,
        details=details,
    )
