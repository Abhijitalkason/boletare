"""
Jyotish AI — Dosha Detection Engine

Detects 3 classical Vedic doshas from a computed BirthChart.
All logic is pure-functional — reads from the BirthChart object,
no I/O, no side effects.

Doshas detected:
  1. Mangal Dosha  — Mars in houses 1/2/4/7/8/12 from lagna
  2. Kaal Sarp Dosha — All planets hemmed between Rahu-Ketu axis
  3. Pitra Dosha   — Sun conjunct Rahu / Sun afflicted in 9th house

References: Brihat Parashara Hora Shastra (BPHS), Phaladeepika.
"""

from __future__ import annotations

from jyotish_ai.domain.types import Planet, Sign, Dignity
from jyotish_ai.domain.models import BirthChart, PlanetPosition, DoshaResult
from jyotish_ai.domain.constants import (
    SIGN_LORD,
    OWN_SIGNS,
    EXALTATION,
    SPECIAL_ASPECTS,
    NATURAL_BENEFICS,
    sign_to_house,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _get_planet(chart: BirthChart, planet: Planet) -> PlanetPosition:
    """Retrieve a specific planet from the chart."""
    for p in chart.planets:
        if p.planet == planet:
            return p
    raise ValueError(f"Planet {planet} not found in chart")


def _planet_map(chart: BirthChart) -> dict[Planet, PlanetPosition]:
    """Build a quick lookup map of Planet -> PlanetPosition."""
    return {p.planet: p for p in chart.planets}


def _planet_aspects_house(planet_pos: PlanetPosition, target_house: int) -> bool:
    """Check if a planet aspects a given house (7th house + special aspects)."""
    planet = planet_pos.planet
    source_house = planet_pos.house

    # Universal 7th house aspect
    aspected_house = (source_house - 1 + 6) % 12 + 1  # 7th from source
    if aspected_house == target_house:
        return True

    # Special aspects
    special = SPECIAL_ASPECTS.get(planet, [])
    for offset in special:
        aspected = (source_house - 1 + offset - 1) % 12 + 1
        if aspected == target_house:
            return True

    return False


# ── Dosha Detectors ──────────────────────────────────────────────────

def _check_mangal_dosha(chart: BirthChart) -> DoshaResult:
    """Mangal Dosha (Kuja Dosha): Mars in houses 1, 2, 4, 7, 8, or 12
    from the lagna.

    Severity:
      - Houses 1, 7, 8: severe
      - Houses 2, 4: moderate
      - House 12: mild

    Cancellation factors:
      - Mars in own sign (Aries/Scorpio) or exalted (Capricorn)
      - Jupiter aspects the house Mars is in
      - Venus in the 7th house
      - Mars conjunct a natural benefic
    """
    pm = _planet_map(chart)
    mars = pm[Planet.MARS]

    mangal_houses = {1, 2, 4, 7, 8, 12}
    is_present = mars.house in mangal_houses

    if not is_present:
        return DoshaResult(
            name="Mangal Dosha",
            is_present=False,
            severity="none",
            involved_planets=[Planet.MARS.value],
            affected_houses=[],
            description="Mars is not in houses 1, 2, 4, 7, 8, or 12 — no Mangal Dosha.",
            cancellation_factors=[],
        )

    # Determine severity by house
    if mars.house in {1, 7, 8}:
        severity = "severe"
    elif mars.house in {2, 4}:
        severity = "moderate"
    else:
        severity = "mild"

    # Check cancellation factors
    cancellations: list[str] = []

    # Mars in own sign or exalted
    if mars.sign in OWN_SIGNS.get(Planet.MARS, []):
        cancellations.append(f"Mars is in own sign ({mars.sign.name})")
    if EXALTATION.get(Planet.MARS) == mars.sign:
        cancellations.append(f"Mars is exalted in {mars.sign.name}")

    # Jupiter aspects Mars's house
    jupiter = pm[Planet.JUPITER]
    if _planet_aspects_house(jupiter, mars.house):
        cancellations.append("Jupiter aspects the house Mars occupies")

    # Venus in 7th house
    venus = pm[Planet.VENUS]
    if venus.house == 7:
        cancellations.append("Venus is in the 7th house")

    # Mars conjunct a natural benefic (same sign)
    for benefic in NATURAL_BENEFICS:
        if benefic == Planet.MARS:
            continue
        bp = pm.get(benefic)
        if bp and bp.sign == mars.sign:
            cancellations.append(f"Mars is conjunct benefic {benefic.value}")
            break

    # Reduce severity if cancellations exist
    if cancellations:
        severity_order = ["severe", "moderate", "mild", "none"]
        idx = severity_order.index(severity)
        reduced_idx = min(idx + len(cancellations), len(severity_order) - 1)
        severity = severity_order[reduced_idx]

    return DoshaResult(
        name="Mangal Dosha",
        is_present=severity != "none",
        severity=severity,
        involved_planets=[Planet.MARS.value],
        affected_houses=[mars.house],
        description=(
            f"Mars in house {mars.house} from lagna — "
            "can cause delays or difficulties in marriage and partnerships."
            if severity != "none" else
            "Mars in house {mars.house} but cancelled by mitigating factors."
        ),
        cancellation_factors=cancellations,
    )


def _check_kaal_sarp_dosha(chart: BirthChart) -> DoshaResult:
    """Kaal Sarp Dosha: All 7 planets (Sun through Saturn) are hemmed
    between Rahu and Ketu on one side of the Rahu-Ketu axis.

    Uses arc-second longitudes to determine which hemisphere each planet
    falls in.  The arc from Rahu to Ketu (going forward through the
    zodiac) defines one hemisphere; the reverse arc defines the other.
    """
    pm = _planet_map(chart)
    rahu = pm[Planet.RAHU]
    ketu = pm[Planet.KETU]

    rahu_long = rahu.longitude_arcsec
    ketu_long = ketu.longitude_arcsec

    # The 7 planets to check (excluding Rahu and Ketu)
    check_planets = [
        Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
        Planet.JUPITER, Planet.VENUS, Planet.SATURN,
    ]

    def _is_between_forward(start: int, end: int, point: int) -> bool:
        """Check if point lies in the arc from start to end going forward
        (increasing longitude, wrapping at 1,296,000)."""
        full_circle = 1_296_000
        if start <= end:
            return start <= point <= end
        else:
            return point >= start or point <= end

    # Check hemisphere 1: Rahu -> Ketu (forward)
    all_in_rahu_to_ketu = all(
        _is_between_forward(rahu_long, ketu_long, pm[p].longitude_arcsec)
        for p in check_planets
    )

    # Check hemisphere 2: Ketu -> Rahu (forward)
    all_in_ketu_to_rahu = all(
        _is_between_forward(ketu_long, rahu_long, pm[p].longitude_arcsec)
        for p in check_planets
    )

    is_present = all_in_rahu_to_ketu or all_in_ketu_to_rahu

    if not is_present:
        return DoshaResult(
            name="Kaal Sarp Dosha",
            is_present=False,
            severity="none",
            involved_planets=[Planet.RAHU.value, Planet.KETU.value],
            affected_houses=[],
            description="Planets are not all hemmed between Rahu and Ketu — no Kaal Sarp Dosha.",
            cancellation_factors=[],
        )

    # Determine which type
    if all_in_rahu_to_ketu:
        dosha_type = "Anant" if rahu.house == 1 else "partial"
    else:
        dosha_type = "partial"

    return DoshaResult(
        name="Kaal Sarp Dosha",
        is_present=True,
        severity="moderate",
        involved_planets=[Planet.RAHU.value, Planet.KETU.value],
        affected_houses=[rahu.house, ketu.house],
        description=(
            f"All planets hemmed between Rahu (house {rahu.house}) and "
            f"Ketu (house {ketu.house}) — may cause sudden obstacles, "
            "karmic delays, and periods of struggle followed by transformation."
        ),
        cancellation_factors=[],
    )


def _check_pitra_dosha(chart: BirthChart) -> DoshaResult:
    """Pitra Dosha: Sun conjunct Rahu (in the same sign), or Sun in the
    9th house with Saturn's aspect.

    Indicates ancestral karmic debts affecting the native's fortune,
    father's health, or spiritual progress.
    """
    pm = _planet_map(chart)
    sun = pm[Planet.SUN]
    rahu = pm[Planet.RAHU]
    saturn = pm[Planet.SATURN]

    reasons: list[str] = []
    affected: list[int] = []

    # Condition 1: Sun and Rahu in the same sign
    if sun.sign == rahu.sign:
        reasons.append(f"Sun conjunct Rahu in {sun.sign.name}")
        affected.append(sun.house)

    # Condition 2: Sun in 9th house with Saturn's aspect
    if sun.house == 9 and _planet_aspects_house(saturn, 9):
        reasons.append("Sun in 9th house aspected by Saturn")
        if 9 not in affected:
            affected.append(9)

    is_present = len(reasons) > 0

    if not is_present:
        return DoshaResult(
            name="Pitra Dosha",
            is_present=False,
            severity="none",
            involved_planets=[Planet.SUN.value, Planet.RAHU.value],
            affected_houses=[],
            description="Sun is not afflicted by Rahu or Saturn in relevant houses — no Pitra Dosha.",
            cancellation_factors=[],
        )

    # Severity: Sun-Rahu conjunction is more severe
    severity = "moderate" if sun.sign == rahu.sign else "mild"

    # Check cancellation: Jupiter aspects the afflicted house
    cancellations: list[str] = []
    jupiter = pm[Planet.JUPITER]
    for h in affected:
        if _planet_aspects_house(jupiter, h):
            cancellations.append(f"Jupiter aspects house {h}")

    if cancellations:
        severity = "mild" if severity == "moderate" else "none"

    return DoshaResult(
        name="Pitra Dosha",
        is_present=severity != "none",
        severity=severity,
        involved_planets=[Planet.SUN.value, Planet.RAHU.value],
        affected_houses=affected,
        description=(
            f"Pitra Dosha detected ({'; '.join(reasons)}) — "
            "indicates ancestral karmic debts; remedies through pitru tarpan recommended."
        ),
        cancellation_factors=cancellations,
    )


# ── Public API ──────────────────────────────────────────────────────

def detect_all_doshas(chart: BirthChart) -> list[DoshaResult]:
    """Detect all 3 classical doshas from the computed birth chart.

    Returns a list of DoshaResult objects — one per dosha checked.
    Each result has ``is_present`` indicating whether the dosha was found.
    """
    return [
        _check_mangal_dosha(chart),
        _check_kaal_sarp_dosha(chart),
        _check_pitra_dosha(chart),
    ]
