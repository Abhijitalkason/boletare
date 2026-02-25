"""
Jyotish AI -- Gate 2: Dasha Significator Evaluation

Checks whether the currently active Vimshottari Dasha lords (Mahadasha and
Antardasha) are connected to the event house being predicted.

A dasha lord "connects" to an event house through four independent channels:

    1. Lordship   -- the dasha lord rules the event house sign
    2. Placement  -- the dasha lord is physically sitting in the event house
    3. Aspect     -- the dasha lord casts an aspect on the event house
    4. Connection -- the dasha lord is conjunct or mutually aspecting
                     the event house lord

Each channel carries a fixed weight.  The per-lord score is the sum of
triggered weights (clamped to 1.0).  The final gate score blends the
Mahadasha lord score (60 %) and Antardasha lord score (40 %).

Architecture doc section 4.2:
  "The current Mahadasha lord and Antardasha lord must be significators
   of the event house for the event to fructify in the queried period."
"""

from __future__ import annotations

from datetime import date

from jyotish_ai.domain.types import Planet, Sign, EventType
from jyotish_ai.domain.models import BirthChart, DashaPeriod, GateResult, PlanetPosition
from jyotish_ai.domain.constants import (
    SIGN_LORD,
    EVENT_HOUSE_MAP,
    SPECIAL_ASPECTS,
    sign_to_house,
    house_to_sign,
)
from jyotish_ai.engine.dasha import find_active_periods

# ── Weight constants ──────────────────────────────────────────────────
_W_EVENT_LORD: float = 0.40
_W_PLACED_IN_HOUSE: float = 0.30
_W_ASPECTS_HOUSE: float = 0.20
_W_CONNECTED_TO_LORD: float = 0.15

# ── Blend weights ─────────────────────────────────────────────────────
_MD_WEIGHT: float = 0.60
_AD_WEIGHT: float = 0.40

# ── Gate threshold (score >= this → sufficient) ───────────────────────
_SUFFICIENCY_THRESHOLD: float = 0.30


# ======================================================================
# Public API
# ======================================================================

def evaluate_dasha(
    chart: BirthChart,
    event_type: EventType,
    query_date: date,
) -> GateResult:
    """Gate 2: Evaluate Dasha lords' connection to event house.

    Args:
        chart: Complete birth chart with dasha tree.
        event_type: The event being predicted.
        query_date: Date to check active dasha for.

    Returns:
        GateResult with score and connection details.
    """
    # Resolve event house and its lord
    event_house: int = EVENT_HOUSE_MAP[event_type]
    event_sign: Sign = house_to_sign(event_house, chart.ascendant_sign)
    event_lord: Planet = SIGN_LORD[event_sign]

    # Find active Mahadasha / Antardasha
    active_md, active_ad = find_active_periods(chart.dasha_tree, query_date)

    # --- No active MD → score is zero -----------------------------------
    if active_md is None:
        return GateResult(
            gate_name="Gate 2 — Dasha Significator",
            score=0.0,
            is_sufficient=False,
            details={
                "md_lord": None,
                "ad_lord": None,
                "md_score": 0.0,
                "ad_score": 0.0,
                "md_connections": {
                    "is_event_lord": False,
                    "placed_in_house": False,
                    "aspects_house": False,
                    "connected_to_lord": False,
                },
                "ad_connections": {
                    "is_event_lord": False,
                    "placed_in_house": False,
                    "aspects_house": False,
                    "connected_to_lord": False,
                },
                "event_house": event_house,
                "event_lord": event_lord.value,
            },
        )

    # --- Score Mahadasha lord -------------------------------------------
    md_score, md_connections = _score_lord_connection(
        lord_planet=active_md.planet,
        chart=chart,
        event_house=event_house,
        event_lord=event_lord,
    )

    # --- Score Antardasha lord (if present) ------------------------------
    if active_ad is not None:
        ad_score, ad_connections = _score_lord_connection(
            lord_planet=active_ad.planet,
            chart=chart,
            event_house=event_house,
            event_lord=event_lord,
        )
        combined = _MD_WEIGHT * md_score + _AD_WEIGHT * ad_score
    else:
        ad_score = 0.0
        ad_connections = {
            "is_event_lord": False,
            "placed_in_house": False,
            "aspects_house": False,
            "connected_to_lord": False,
        }
        combined = md_score * _MD_WEIGHT

    # Clamp to [0.0, 1.0]
    combined = max(0.0, min(1.0, combined))

    return GateResult(
        gate_name="Gate 2 — Dasha Significator",
        score=round(combined, 4),
        is_sufficient=combined >= _SUFFICIENCY_THRESHOLD,
        details={
            "md_lord": active_md.planet.value,
            "ad_lord": active_ad.planet.value if active_ad else None,
            "md_score": round(md_score, 4),
            "ad_score": round(ad_score, 4),
            "md_connections": md_connections,
            "ad_connections": ad_connections,
            "event_house": event_house,
            "event_lord": event_lord.value,
        },
    )


# ======================================================================
# Internal helpers
# ======================================================================

def _score_lord_connection(
    lord_planet: Planet,
    chart: BirthChart,
    event_house: int,
    event_lord: Planet,
) -> tuple[float, dict]:
    """Score a single dasha lord's connection to the event house.

    Returns:
        (score, details_dict) where score is in [0.0, 1.0] and
        details_dict records which connections were found.
    """
    # Look up the dasha lord's position in the chart
    lord_pos: PlanetPosition | None = _find_planet(chart, lord_planet)
    event_lord_pos: PlanetPosition | None = _find_planet(chart, event_lord)

    score = 0.0

    # (a) Is the dasha lord the event house lord? ........................
    is_event_lord = lord_planet == event_lord
    if is_event_lord:
        score += _W_EVENT_LORD

    # (b) Is the dasha lord placed in the event house? ..................
    placed_in_house = False
    if lord_pos is not None and lord_pos.house == event_house:
        placed_in_house = True
        score += _W_PLACED_IN_HOUSE

    # (c) Does the dasha lord aspect the event house? ...................
    aspects_house = False
    if lord_pos is not None:
        aspected = _aspected_houses(lord_planet, lord_pos.house)
        if event_house in aspected:
            aspects_house = True
            score += _W_ASPECTS_HOUSE

    # (d) Is the dasha lord connected to the event lord? ................
    #     Conjunction check: same sign.
    #     Mutual aspect: dasha lord aspects event lord's house OR
    #                     event lord aspects dasha lord's house.
    connected_to_lord = False
    if lord_pos is not None and event_lord_pos is not None:
        # Conjunction (same sign)
        if lord_pos.sign == event_lord_pos.sign:
            connected_to_lord = True
        # Mutual aspect: dasha lord aspects event lord's house
        if not connected_to_lord:
            dasha_lord_aspects = _aspected_houses(lord_planet, lord_pos.house)
            if event_lord_pos.house in dasha_lord_aspects:
                connected_to_lord = True
        # Mutual aspect: event lord aspects dasha lord's house
        if not connected_to_lord:
            event_lord_aspects = _aspected_houses(event_lord, event_lord_pos.house)
            if lord_pos.house in event_lord_aspects:
                connected_to_lord = True

    if connected_to_lord:
        score += _W_CONNECTED_TO_LORD

    # Clamp per-lord score to [0.0, 1.0]
    score = max(0.0, min(1.0, score))

    details = {
        "is_event_lord": is_event_lord,
        "placed_in_house": placed_in_house,
        "aspects_house": aspects_house,
        "connected_to_lord": connected_to_lord,
    }
    return score, details


def _find_planet(chart: BirthChart, planet: Planet) -> PlanetPosition | None:
    """Find a planet's position in the chart, or None if absent."""
    for pp in chart.planets:
        if pp.planet == planet:
            return pp
    return None


def _aspected_houses(planet: Planet, planet_house: int) -> set[int]:
    """Return the set of houses aspected by *planet* sitting in *planet_house*.

    Every planet aspects the 7th house from its position (universal aspect).
    Planets listed in SPECIAL_ASPECTS additionally aspect extra houses
    at the offsets specified there.
    """
    aspected: set[int] = set()

    # Universal 7th-house aspect: 7th house counted from planet_house
    # (inclusive count, so offset is 6)
    aspected.add((planet_house - 1 + 6) % 12 + 1)

    # Special aspects
    if planet in SPECIAL_ASPECTS:
        for offset in SPECIAL_ASPECTS[planet]:
            aspected.add((planet_house - 1 + offset) % 12 + 1)

    return aspected
