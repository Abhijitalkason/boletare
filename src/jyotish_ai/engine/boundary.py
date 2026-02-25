"""
Jyotish AI — Layer 1: Dual-Ephemeris Boundary Detection

Architecture doc section 3.6:
  "When a planet is near a boundary, birth time uncertainty might place it
   on either side. Instead of approximating with velocity math, we compute
   the exact position twice."

  pos_early = swisseph.calc_ut(birth_jd - uncertainty/1440, MOON)
  pos_late  = swisseph.calc_ut(birth_jd + uncertainty/1440, MOON)

Zero approximation. Two microsecond ephemeris calls. 100% correct.
"""

from __future__ import annotations

from jyotish_ai.domain.types import (
    BirthTimeTier,
    TIER_UNCERTAINTY_MINUTES,
    ARCSEC_PER_NAKSHATRA,
    ARCSEC_PER_SIGN,
    ARCSEC_FULL_CIRCLE,
    Planet,
)
from jyotish_ai.domain.models import BoundaryFlags
from jyotish_ai.engine.ephemeris import get_planet_longitude, get_house_cusps_placidus


def check_boundaries(
    birth_jd: float,
    birth_time_tier: BirthTimeTier,
    ayanamsha: str = "lahiri",
    latitude: float = 28.6,
    longitude: float = 77.2,
) -> BoundaryFlags:
    """Run dual-ephemeris boundary detection for Moon and Lagna.

    Computes positions at birth_jd ± uncertainty and checks if any
    critical boundary (Nakshatra, Sign, Lagna sign) is crossed.

    Args:
        birth_jd: Julian Day of birth
        birth_time_tier: Determines uncertainty window
        ayanamsha: "lahiri" or "kp"
        latitude: Birth latitude (for Lagna check)
        longitude: Birth longitude (for Lagna check)

    Returns:
        BoundaryFlags with all detected ambiguities
    """
    uncertainty_min = TIER_UNCERTAINTY_MINUTES[birth_time_tier]
    uncertainty_jd = uncertainty_min / 1440.0  # Convert minutes to Julian Day fraction

    jd_early = birth_jd - uncertainty_jd
    jd_late = birth_jd + uncertainty_jd

    # ── Moon boundary checks ──────────────────────────────────
    moon_early_arcsec, _ = get_planet_longitude(jd_early, Planet.MOON, ayanamsha)
    moon_late_arcsec, _ = get_planet_longitude(jd_late, Planet.MOON, ayanamsha)

    # Nakshatra boundary: check if Nakshatra index differs
    nak_early = moon_early_arcsec // ARCSEC_PER_NAKSHATRA
    nak_late = moon_late_arcsec // ARCSEC_PER_NAKSHATRA
    moon_nakshatra_boundary = (nak_early != nak_late)

    # Sign boundary: check if sign index differs
    sign_early = moon_early_arcsec // ARCSEC_PER_SIGN
    sign_late = moon_late_arcsec // ARCSEC_PER_SIGN
    moon_sign_boundary = (sign_early != sign_late)

    # Dasha is sensitive if Nakshatra changes (different starting lord)
    dasha_boundary_sensitive = moon_nakshatra_boundary

    # ── Lagna (Ascendant) boundary check ──────────────────────
    _, asc_early = get_house_cusps_placidus(jd_early, latitude, longitude, ayanamsha)
    _, asc_late = get_house_cusps_placidus(jd_late, latitude, longitude, ayanamsha)

    asc_sign_early = asc_early // ARCSEC_PER_SIGN
    asc_sign_late = asc_late // ARCSEC_PER_SIGN
    lagna_ambiguous = (asc_sign_early != asc_sign_late)

    return BoundaryFlags(
        lagna_ambiguous=lagna_ambiguous,
        moon_nakshatra_boundary=moon_nakshatra_boundary,
        moon_sign_boundary=moon_sign_boundary,
        dasha_boundary_sensitive=dasha_boundary_sensitive,
    )
