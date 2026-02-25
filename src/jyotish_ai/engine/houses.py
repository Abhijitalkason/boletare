"""
Jyotish AI — Layer 1: House Computation

Placidus house system with distortion detection.
Equal House fallback for equatorial latitudes.

Architecture doc section 3.4:
  "Placidus is standard for KP but distorts near the equator.
   South India (8-17°N) gets houses spanning 50° while others span only 10°."

Detection: any house > 40° or < 20° → placidus_distorted = True
"""

from __future__ import annotations

from jyotish_ai.domain.types import (
    ArcSeconds,
    Sign,
    ARCSEC_PER_SIGN,
    ARCSEC_PER_DEGREE,
    ARCSEC_FULL_CIRCLE,
)
from jyotish_ai.domain.models import HouseCusp
from jyotish_ai.engine.ephemeris import (
    get_house_cusps_placidus,
    get_house_cusps_equal,
    arcsec_to_sign,
    arcsec_to_deg,
    arcsec_in_sign,
)

# Distortion thresholds in degrees
_DISTORTION_MAX_DEG = 40.0
_DISTORTION_MIN_DEG = 20.0


def compute_houses(
    jd: float,
    latitude: float,
    longitude: float,
    ayanamsha: str = "lahiri",
) -> tuple[list[HouseCusp], ArcSeconds, bool]:
    """Compute house cusps with distortion detection.

    Returns:
        (houses, ascendant_arcsec, placidus_distorted)
    """
    cusp_arcsecs, ascendant_arcsec = get_house_cusps_placidus(
        jd, latitude, longitude, ayanamsha
    )

    houses = _build_house_objects(cusp_arcsecs)
    distorted = _detect_distortion(houses)

    return houses, ascendant_arcsec, distorted


def compute_equal_houses_from_asc(
    ascendant_arcsec: ArcSeconds,
) -> list[HouseCusp]:
    """Compute Equal House cusps as fallback."""
    cusp_arcsecs = get_house_cusps_equal(ascendant_arcsec)
    return _build_house_objects(cusp_arcsecs)


def assign_planet_to_house(
    planet_arcsec: int,
    houses: list[HouseCusp],
) -> int:
    """Determine which house a planet falls in.

    Uses the cusp-based system: a planet belongs to the house whose cusp
    it has crossed but has not yet reached the next cusp.

    Args:
        planet_arcsec: Planet's sidereal longitude in arc-seconds
        houses: List of 12 HouseCusp objects (sorted by house_number)

    Returns:
        House number (1-12)
    """
    planet_pos = planet_arcsec % ARCSEC_FULL_CIRCLE

    for i in range(12):
        cusp_start = houses[i].cusp_arcsec
        cusp_end = houses[(i + 1) % 12].cusp_arcsec

        if cusp_end > cusp_start:
            # Normal case: cusp_start < planet < cusp_end
            if cusp_start <= planet_pos < cusp_end:
                return houses[i].house_number
        else:
            # Wraps around 0°/360° (Pisces→Aries boundary)
            if planet_pos >= cusp_start or planet_pos < cusp_end:
                return houses[i].house_number

    # Fallback: should not reach here with valid data
    return 1


def _build_house_objects(cusp_arcsecs: list[ArcSeconds]) -> list[HouseCusp]:
    """Build HouseCusp objects from raw cusp arc-seconds."""
    houses: list[HouseCusp] = []

    for i in range(12):
        cusp = cusp_arcsecs[i]
        next_cusp = cusp_arcsecs[(i + 1) % 12]

        # Compute span
        span_arcsec = (next_cusp - cusp) % ARCSEC_FULL_CIRCLE
        span_degrees = span_arcsec / ARCSEC_PER_DEGREE

        sign = arcsec_to_sign(cusp)
        sign_deg = arcsec_in_sign(cusp) / ARCSEC_PER_DEGREE

        houses.append(HouseCusp(
            house_number=i + 1,
            cusp_arcsec=cusp,
            sign=sign,
            sign_degrees=round(sign_deg, 4),
            span_degrees=round(span_degrees, 4),
        ))

    return houses


def _detect_distortion(houses: list[HouseCusp]) -> bool:
    """Check if any house span exceeds distortion thresholds.

    Per architecture doc: house > 40° or < 20° → distorted.
    """
    for house in houses:
        if house.span_degrees > _DISTORTION_MAX_DEG or house.span_degrees < _DISTORTION_MIN_DEG:
            return True
    return False
