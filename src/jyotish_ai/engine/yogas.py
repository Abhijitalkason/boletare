"""
Jyotish AI — Yoga Detection Engine

Detects 10 classical Vedic yogas from a computed BirthChart.
All logic is pure-functional — reads from the BirthChart object,
no I/O, no side effects.

Yogas detected:
  1. Gajakesari Yoga       — Jupiter in kendra from Moon
  2. Budh-Aditya Yoga      — Sun + Mercury conjunct
  3. Hamsa Yoga             — Jupiter in own/exalted + kendra from lagna
  4. Malavya Yoga           — Venus in own/exalted + kendra from lagna
  5. Ruchaka Yoga           — Mars in own/exalted + kendra from lagna
  6. Sasa Yoga              — Saturn in own/exalted + kendra from lagna
  7. Bhadra Yoga            — Mercury in own/exalted + kendra from lagna
  8. Chandra-Mangal Yoga    — Moon + Mars conjunct
  9. Raj Yoga (generic)     — Kendra lord + Trikona lord conjunct
 10. Viparita Raj Yoga      — Lords of 6/8/12 in each other's houses

References: Brihat Parashara Hora Shastra (BPHS).
"""

from __future__ import annotations

from jyotish_ai.domain.types import Planet, Sign, Dignity
from jyotish_ai.domain.models import BirthChart, PlanetPosition, YogaResult
from jyotish_ai.domain.constants import (
    SIGN_LORD,
    OWN_SIGNS,
    EXALTATION,
    sign_to_house,
    house_to_sign,
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


def _is_in_own_or_exalted(planet: Planet, sign: Sign) -> bool:
    """Check if a planet is in its own sign or exalted sign."""
    if EXALTATION.get(planet) == sign:
        return True
    if sign in OWN_SIGNS.get(planet, []):
        return True
    return False


def _is_kendra_house(house: int) -> bool:
    """Check if a house number is a kendra (1, 4, 7, 10)."""
    return house in {1, 4, 7, 10}


def _house_distance(from_sign: Sign, to_sign: Sign) -> int:
    """Compute the house distance (1-12) from one sign to another."""
    return (int(to_sign) - int(from_sign)) % 12 + 1


# ── Yoga Detectors ──────────────────────────────────────────────────

def _check_gajakesari(chart: BirthChart) -> YogaResult:
    """Gajakesari Yoga: Jupiter in kendra (1/4/7/10) from Moon's sign.

    Indicates wealth, intelligence, and lasting fame.
    """
    pm = _planet_map(chart)
    moon = pm[Planet.MOON]
    jupiter = pm[Planet.JUPITER]

    dist = _house_distance(moon.sign, jupiter.sign)
    is_present = dist in {1, 4, 7, 10}
    strength = jupiter.dignity_score if is_present else 0.0

    return YogaResult(
        name="Gajakesari Yoga",
        yoga_type="conjunction",
        is_present=is_present,
        strength=round(strength, 2),
        involved_planets=[Planet.JUPITER.value, Planet.MOON.value],
        description=(
            "Jupiter in kendra from Moon — bestows wisdom, wealth, and lasting reputation."
            if is_present else
            "Jupiter is not in kendra from Moon."
        ),
    )


def _check_budh_aditya(chart: BirthChart) -> YogaResult:
    """Budh-Aditya Yoga: Sun and Mercury in the same sign.

    Indicates intelligence, communication skills, and success in education.
    """
    pm = _planet_map(chart)
    sun = pm[Planet.SUN]
    mercury = pm[Planet.MERCURY]

    is_present = sun.sign == mercury.sign
    strength = round((sun.dignity_score + mercury.dignity_score) / 2, 2) if is_present else 0.0

    return YogaResult(
        name="Budh-Aditya Yoga",
        yoga_type="conjunction",
        is_present=is_present,
        strength=strength,
        involved_planets=[Planet.SUN.value, Planet.MERCURY.value],
        description=(
            "Sun and Mercury conjunct — sharp intellect, eloquence, and scholarly success."
            if is_present else
            "Sun and Mercury are not in the same sign."
        ),
    )


def _check_pancha_mahapurusha(
    chart: BirthChart,
    planet: Planet,
    yoga_name: str,
    description_present: str,
) -> YogaResult:
    """Generic checker for the 5 Pancha Mahapurusha Yogas.

    Condition: The planet must be in its own or exalted sign AND in a
    kendra house (1, 4, 7, 10) from the lagna.
    """
    pp = _get_planet(chart, planet)
    in_strong_sign = _is_in_own_or_exalted(planet, pp.sign)
    in_kendra = _is_kendra_house(pp.house)
    is_present = in_strong_sign and in_kendra
    strength = pp.dignity_score if is_present else 0.0

    return YogaResult(
        name=yoga_name,
        yoga_type="mahapurusha",
        is_present=is_present,
        strength=round(strength, 2),
        involved_planets=[planet.value],
        description=(
            description_present if is_present else
            f"{planet.value} is not in own/exalted sign in a kendra house."
        ),
    )


def _check_hamsa(chart: BirthChart) -> YogaResult:
    return _check_pancha_mahapurusha(
        chart, Planet.JUPITER, "Hamsa Yoga",
        "Jupiter in own/exalted sign in kendra — righteous, learned, and spiritually elevated.",
    )


def _check_malavya(chart: BirthChart) -> YogaResult:
    return _check_pancha_mahapurusha(
        chart, Planet.VENUS, "Malavya Yoga",
        "Venus in own/exalted sign in kendra — beauty, luxury, artistic talent, and conjugal bliss.",
    )


def _check_ruchaka(chart: BirthChart) -> YogaResult:
    return _check_pancha_mahapurusha(
        chart, Planet.MARS, "Ruchaka Yoga",
        "Mars in own/exalted sign in kendra — courage, leadership, and victory over enemies.",
    )


def _check_sasa(chart: BirthChart) -> YogaResult:
    return _check_pancha_mahapurusha(
        chart, Planet.SATURN, "Sasa Yoga",
        "Saturn in own/exalted sign in kendra — authority, discipline, and command over masses.",
    )


def _check_bhadra(chart: BirthChart) -> YogaResult:
    return _check_pancha_mahapurusha(
        chart, Planet.MERCURY, "Bhadra Yoga",
        "Mercury in own/exalted sign in kendra — intellectual brilliance, eloquence, and commerce.",
    )


def _check_chandra_mangal(chart: BirthChart) -> YogaResult:
    """Chandra-Mangal Yoga: Moon and Mars in the same sign.

    Indicates wealth through enterprise and courage.
    """
    pm = _planet_map(chart)
    moon = pm[Planet.MOON]
    mars = pm[Planet.MARS]

    is_present = moon.sign == mars.sign
    strength = round((moon.dignity_score + mars.dignity_score) / 2, 2) if is_present else 0.0

    return YogaResult(
        name="Chandra-Mangal Yoga",
        yoga_type="conjunction",
        is_present=is_present,
        strength=strength,
        involved_planets=[Planet.MOON.value, Planet.MARS.value],
        description=(
            "Moon and Mars conjunct — wealth through enterprise, courage, and practical wisdom."
            if is_present else
            "Moon and Mars are not in the same sign."
        ),
    )


def _check_raj_yoga(chart: BirthChart) -> YogaResult:
    """Raj Yoga (generic): Lord of a kendra house and lord of a trikona
    house are conjunct (in the same sign).

    Kendra houses: 1, 4, 7, 10.  Trikona houses: 5, 9 (excluding 1
    since it is both kendra and trikona).

    Per BPHS, this is the most important yoga for worldly success.
    """
    asc = chart.ascendant_sign
    pm = _planet_map(chart)

    kendra_houses = {1, 4, 7, 10}
    trikona_houses = {5, 9}  # Exclude 1 — it's both kendra & trikona

    # Find lords of kendra and trikona houses
    kendra_lords: set[Planet] = set()
    for h in kendra_houses:
        sign = house_to_sign(h, asc)
        kendra_lords.add(SIGN_LORD[sign])

    trikona_lords: set[Planet] = set()
    for h in trikona_houses:
        sign = house_to_sign(h, asc)
        trikona_lords.add(SIGN_LORD[sign])

    # Check if any kendra lord and trikona lord are conjunct (same sign)
    involved: list[str] = []
    best_strength = 0.0

    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl == tl:
                continue  # Same planet lords both — skip
            kl_pos = pm.get(kl)
            tl_pos = pm.get(tl)
            if kl_pos and tl_pos and kl_pos.sign == tl_pos.sign:
                avg = (kl_pos.dignity_score + tl_pos.dignity_score) / 2
                if avg > best_strength:
                    best_strength = avg
                    involved = [kl.value, tl.value]

    is_present = len(involved) > 0

    return YogaResult(
        name="Raj Yoga",
        yoga_type="raj",
        is_present=is_present,
        strength=round(best_strength, 2),
        involved_planets=involved,
        description=(
            f"Lord of kendra and trikona conjunct ({', '.join(involved)}) — "
            "promises power, status, and worldly success."
            if is_present else
            "No kendra lord and trikona lord conjunction found."
        ),
    )


def _check_viparita_raj_yoga(chart: BirthChart) -> YogaResult:
    """Viparita Raj Yoga: Lord of the 6th, 8th, or 12th house is placed
    in one of the other dusthana houses (6th, 8th, or 12th).

    Turns adversity into advantage — success through unusual circumstances.
    """
    asc = chart.ascendant_sign
    pm = _planet_map(chart)

    dusthana_houses = {6, 8, 12}
    dusthana_lords: dict[int, Planet] = {}
    for h in dusthana_houses:
        sign = house_to_sign(h, asc)
        dusthana_lords[h] = SIGN_LORD[sign]

    involved: list[str] = []
    for h, lord in dusthana_lords.items():
        lord_pos = pm.get(lord)
        if lord_pos and lord_pos.house in dusthana_houses and lord_pos.house != h:
            if lord.value not in involved:
                involved.append(lord.value)

    is_present = len(involved) > 0
    strength = 0.6 if is_present else 0.0  # Moderate strength by nature

    return YogaResult(
        name="Viparita Raj Yoga",
        yoga_type="viparita",
        is_present=is_present,
        strength=strength,
        involved_planets=involved,
        description=(
            f"Dusthana lords ({', '.join(involved)}) placed in other dusthana houses — "
            "success through overcoming adversity and unconventional paths."
            if is_present else
            "No dusthana lord is placed in another dusthana house."
        ),
    )


# ── Public API ──────────────────────────────────────────────────────

def detect_all_yogas(chart: BirthChart) -> list[YogaResult]:
    """Detect all 10 classical yogas from the computed birth chart.

    Returns a list of YogaResult objects — one per yoga checked.
    Each result has ``is_present`` indicating whether the yoga was found.
    """
    return [
        _check_gajakesari(chart),
        _check_budh_aditya(chart),
        _check_hamsa(chart),
        _check_malavya(chart),
        _check_ruchaka(chart),
        _check_sasa(chart),
        _check_bhadra(chart),
        _check_chandra_mangal(chart),
        _check_raj_yoga(chart),
        _check_viparita_raj_yoga(chart),
    ]
