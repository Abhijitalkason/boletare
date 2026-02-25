"""
Jyotish AI -- Layer 1: Navamsha (D-9) Divisional Chart Computation

The Navamsha is the most important divisional chart in Vedic astrology.
It divides each sign into 9 equal parts of 3 deg 20 min (12,000 arc-seconds),
yielding 108 navamsha divisions across the full zodiac.

Algorithm
---------
The navamsha sign for a planet depends on its rasi sign's element:

    Fire  signs (Aries, Leo, Sagittarius)    -> navamshas start from Aries
    Earth signs (Taurus, Virgo, Capricorn)   -> navamshas start from Capricorn
    Air   signs (Gemini, Libra, Aquarius)    -> navamshas start from Libra
    Water signs (Cancer, Scorpio, Pisces)    -> navamshas start from Cancer

Within its rasi sign the planet occupies one of 9 divisions (0-8).
The navamsha sign = (element_start - 1 + division_index) % 12 + 1.
"""

from __future__ import annotations

from jyotish_ai.domain.types import (
    Planet,
    Sign,
    ArcSeconds,
    Dignity,
    ARCSEC_PER_SIGN,
    ARCSEC_PER_PADA,
    ARCSEC_FULL_CIRCLE,
)
from jyotish_ai.domain.models import PlanetPosition
from jyotish_ai.domain.constants import (
    get_sign_from_arcsec,
    get_nakshatra_name,
    get_pada,
    SIGN_LORD,
)

# ──────────────────────────────────────────────────────────────────
# Internal constants
# ──────────────────────────────────────────────────────────────────

_NAVAMSHA_START: dict[str, int] = {
    "fire": 1,    # Aries
    "earth": 10,  # Capricorn
    "air": 7,     # Libra
    "water": 4,   # Cancer
}


# ──────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────

def _element_of_sign(sign: Sign) -> str:
    """Return the element category for a zodiac sign.

    Args:
        sign: A zodiac sign (1-12).

    Returns:
        One of 'fire', 'earth', 'air', 'water'.
    """
    if sign in (Sign.ARIES, Sign.LEO, Sign.SAGITTARIUS):
        return "fire"
    if sign in (Sign.TAURUS, Sign.VIRGO, Sign.CAPRICORN):
        return "earth"
    if sign in (Sign.GEMINI, Sign.LIBRA, Sign.AQUARIUS):
        return "air"
    return "water"


# ──────────────────────────────────────────────────────────────────
# Core computation
# ──────────────────────────────────────────────────────────────────

def _navamsha_sign(rasi_arcsec: int) -> Sign:
    """Determine the navamsha sign for a given rasi longitude.

    Args:
        rasi_arcsec: Absolute sidereal longitude in arc-seconds (0 to 1,295,999).

    Returns:
        The navamsha Sign (1-12).
    """
    # 1. Which rasi sign is the planet in?
    rasi_sign = get_sign_from_arcsec(rasi_arcsec)

    # 2. Position within the sign (0 to 107,999)
    pos_in_sign = rasi_arcsec % ARCSEC_PER_SIGN

    # 3. Which of the 9 navamsha divisions (0-8)?
    nav_div = pos_in_sign // ARCSEC_PER_PADA

    # 4. Starting sign based on element
    element = _element_of_sign(rasi_sign)
    start = _NAVAMSHA_START[element]

    # 5. Navamsha sign
    nav_sign_value = (start - 1 + nav_div) % 12 + 1
    return Sign(nav_sign_value)


def compute_navamsha(
    planets: list[PlanetPosition],
) -> list[PlanetPosition]:
    """Compute Navamsha (D-9) positions for all planets.

    For each planet in the rasi chart, determines its navamsha sign and
    computes a synthetic longitude within that sign.  The position within
    the navamsha division (a 12,000 arc-second span) is scaled
    proportionally to fill the full 108,000 arc-second sign.

    Args:
        planets: Rasi chart planet positions.

    Returns:
        List of PlanetPosition with navamsha sign/house data.
        House in navamsha is set to the navamsha sign number (1-12)
        since navamsha does not use separate house cusps.
        Dignity and dignity_score are set to Dignity.NEUTRAL and 0.25
        as placeholders -- the dignity module will recalculate.
    """
    navamsha_positions: list[PlanetPosition] = []

    for pp in planets:
        rasi_arcsec = pp.longitude_arcsec

        # Determine navamsha sign
        nav_sign = _navamsha_sign(rasi_arcsec)

        # Compute synthetic longitude within the navamsha sign.
        # pos_in_pada: position within the current navamsha division (0 to 11,999)
        # Scale to full sign (0 to 107,999).
        pos_in_pada = rasi_arcsec % ARCSEC_PER_PADA
        sign_internal = (pos_in_pada * ARCSEC_PER_SIGN) // ARCSEC_PER_PADA

        # Absolute navamsha longitude (0 to 1,295,999)
        navamsha_longitude = (nav_sign - 1) * ARCSEC_PER_SIGN + sign_internal

        # Degrees within the navamsha sign (for display)
        sign_degrees = round(sign_internal / 3600.0, 4)

        # Nakshatra and pada from navamsha longitude
        nakshatra = get_nakshatra_name(navamsha_longitude)
        nakshatra_pada = get_pada(navamsha_longitude)

        navamsha_positions.append(PlanetPosition(
            planet=pp.planet,
            longitude_arcsec=navamsha_longitude,
            sign=nav_sign,
            sign_degrees=sign_degrees,
            nakshatra=nakshatra,
            nakshatra_pada=nakshatra_pada,
            house=int(nav_sign),  # navamsha house = sign number
            dignity=Dignity.NEUTRAL,
            dignity_score=0.25,
            is_retrograde=pp.is_retrograde,
        ))

    return navamsha_positions
