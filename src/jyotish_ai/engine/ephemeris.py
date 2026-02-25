"""
Jyotish AI — Layer 1: Swiss Ephemeris Adapter

THE critical boundary between pyswisseph (C extension) and the rest of the system.
Every planetary position, house cusp, and ayanamsha value flows through this module.

INVARIANT: All positional values exit this module as integer arc-seconds.
The single float→int conversion point is deg_to_arcsec().

Thread safety: pyswisseph is NOT thread-safe. All calls go through a module-level lock.
"""

from __future__ import annotations

import threading
from datetime import date, time, datetime
from typing import Optional

import swisseph as swe

from jyotish_ai.domain.types import (
    ArcSeconds,
    Planet,
    Sign,
    ARCSEC_PER_DEGREE,
    ARCSEC_PER_SIGN,
    ARCSEC_PER_NAKSHATRA,
    ARCSEC_FULL_CIRCLE,
)

# Module-level lock for thread safety
_swe_lock = threading.Lock()

# pyswisseph planet ID mapping
_PLANET_SWE_ID: dict[Planet, int] = {
    Planet.SUN: swe.SUN,
    Planet.MOON: swe.MOON,
    Planet.MERCURY: swe.MERCURY,
    Planet.VENUS: swe.VENUS,
    Planet.MARS: swe.MARS,
    Planet.JUPITER: swe.JUPITER,
    Planet.SATURN: swe.SATURN,
    Planet.RAHU: swe.TRUE_NODE,  # True Node (Rahu)
    # Ketu is derived as Rahu + 180°
}

# Ayanamsha method mapping
_AYANAMSHA_MAP: dict[str, int] = {
    "lahiri": swe.SIDM_LAHIRI,
    "kp": swe.SIDM_KRISHNAMURTI,
}


# ──────────────────────────────────────────────────────────────────
# Core conversion — THE single point where float becomes integer
# ──────────────────────────────────────────────────────────────────

def deg_to_arcsec(degrees: float) -> ArcSeconds:
    """Convert floating-point degrees to integer arc-seconds.

    This is the ONLY place in the entire codebase where a floating-point
    positional value is converted to an integer. All downstream math
    uses integer arithmetic exclusively.

    1° = 3,600 arc-seconds. One Nakshatra = 48,000 arc-seconds exactly.
    """
    raw = int(round(degrees * ARCSEC_PER_DEGREE))
    # Normalize to [0, 1_296_000) — full circle
    return ArcSeconds(raw % ARCSEC_FULL_CIRCLE)


def arcsec_to_deg(arcsec: int) -> float:
    """Convert integer arc-seconds back to degrees (for display only)."""
    return arcsec / ARCSEC_PER_DEGREE


def arcsec_to_sign(arcsec: int) -> Sign:
    """Determine zodiac sign from arc-second position."""
    index = (arcsec % ARCSEC_FULL_CIRCLE) // ARCSEC_PER_SIGN
    return Sign(index + 1)


def arcsec_in_sign(arcsec: int) -> int:
    """Arc-seconds elapsed within the current sign (0 to 107999)."""
    return arcsec % ARCSEC_PER_SIGN


def arcsec_to_nakshatra_index(arcsec: int) -> int:
    """Nakshatra index (0-26) from arc-second position."""
    return (arcsec % ARCSEC_FULL_CIRCLE) // ARCSEC_PER_NAKSHATRA


# ──────────────────────────────────────────────────────────────────
# Julian Day conversion
# ──────────────────────────────────────────────────────────────────

def date_to_jd(
    birth_date: date,
    birth_time: Optional[time] = None,
    tz_offset: float = 5.5,  # IST default
) -> float:
    """Convert birth date/time to Julian Day number (UT).

    Args:
        birth_date: The date of birth
        birth_time: Time of birth (if None, defaults to 6:00 AM — sunrise approx)
        tz_offset: Timezone offset from UTC in hours (IST = +5.5)

    Returns:
        Julian Day number in Universal Time
    """
    if birth_time is None:
        hour_ut = 6.0 - tz_offset  # Approximate sunrise in UT
    else:
        hour_decimal = birth_time.hour + birth_time.minute / 60.0 + birth_time.second / 3600.0
        hour_ut = hour_decimal - tz_offset

    with _swe_lock:
        jd = swe.julday(
            birth_date.year,
            birth_date.month,
            birth_date.day,
            hour_ut,
        )
    return jd


# ──────────────────────────────────────────────────────────────────
# Ayanamsha
# ──────────────────────────────────────────────────────────────────

def get_ayanamsha_value(jd: float, method: str = "lahiri") -> float:
    """Get the ayanamsha (sidereal correction) value in degrees.

    Args:
        jd: Julian Day number
        method: "lahiri" or "kp"

    Returns:
        Ayanamsha in degrees (~24° for current era)
    """
    sid_mode = _AYANAMSHA_MAP.get(method, swe.SIDM_LAHIRI)
    with _swe_lock:
        swe.set_sid_mode(sid_mode)
        aya = swe.get_ayanamsa_ut(jd)
    return aya


# ──────────────────────────────────────────────────────────────────
# Planet position computation
# ──────────────────────────────────────────────────────────────────

def get_planet_longitude(
    jd: float,
    planet: Planet,
    ayanamsha: str = "lahiri",
) -> tuple[ArcSeconds, bool]:
    """Compute sidereal longitude for a single planet.

    Args:
        jd: Julian Day number
        planet: The planet to compute
        ayanamsha: "lahiri" or "kp"

    Returns:
        (longitude_arcsec, is_retrograde)
    """
    if planet == Planet.KETU:
        # Ketu = Rahu + 180°
        rahu_arcsec, _ = get_planet_longitude(jd, Planet.RAHU, ayanamsha)
        ketu_arcsec = (rahu_arcsec + ARCSEC_FULL_CIRCLE // 2) % ARCSEC_FULL_CIRCLE
        return ArcSeconds(ketu_arcsec), False  # Ketu retrograde is implicit

    swe_id = _PLANET_SWE_ID[planet]
    sid_mode = _AYANAMSHA_MAP.get(ayanamsha, swe.SIDM_LAHIRI)

    with _swe_lock:
        swe.set_sid_mode(sid_mode)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        result = swe.calc_ut(jd, swe_id, flags)

    longitude_deg = result[0][0]  # Sidereal longitude in degrees
    speed = result[0][3]  # Daily speed (negative = retrograde)
    is_retrograde = speed < 0

    # Ensure positive longitude
    if longitude_deg < 0:
        longitude_deg += 360.0

    arcsec = deg_to_arcsec(longitude_deg)
    return arcsec, is_retrograde


def get_all_planet_longitudes(
    jd: float,
    ayanamsha: str = "lahiri",
) -> dict[Planet, tuple[ArcSeconds, bool]]:
    """Compute sidereal longitudes for all 9 Vedic planets.

    Returns:
        Dict mapping Planet -> (longitude_arcsec, is_retrograde)
    """
    result: dict[Planet, tuple[ArcSeconds, bool]] = {}
    for planet in Planet:
        result[planet] = get_planet_longitude(jd, planet, ayanamsha)
    return result


# ──────────────────────────────────────────────────────────────────
# House cusp computation
# ──────────────────────────────────────────────────────────────────

def get_house_cusps_placidus(
    jd: float,
    latitude: float,
    longitude: float,
    ayanamsha: str = "lahiri",
) -> tuple[list[ArcSeconds], ArcSeconds]:
    """Compute Placidus house cusps (sidereal).

    pyswisseph's swe.houses() returns TROPICAL cusps even when sidereal mode
    is set. We must manually subtract the ayanamsha.

    Args:
        jd: Julian Day number
        latitude: Birth latitude
        longitude: Birth longitude
        ayanamsha: "lahiri" or "kp"

    Returns:
        (list of 12 cusp positions in arc-seconds, ascendant_arcsec)
        cusps[0] = 1st house cusp (Ascendant), cusps[1] = 2nd, etc.
    """
    with _swe_lock:
        cusps_tropical, ascmc = swe.houses(jd, latitude, longitude, b'P')  # P = Placidus

    aya_deg = get_ayanamsha_value(jd, ayanamsha)

    cusp_arcsecs: list[ArcSeconds] = []
    for i in range(12):
        tropical_deg = cusps_tropical[i]
        sidereal_deg = tropical_deg - aya_deg
        if sidereal_deg < 0:
            sidereal_deg += 360.0
        cusp_arcsecs.append(deg_to_arcsec(sidereal_deg))

    # Ascendant (from ascmc array, index 0)
    asc_sidereal = ascmc[0] - aya_deg
    if asc_sidereal < 0:
        asc_sidereal += 360.0
    ascendant_arcsec = deg_to_arcsec(asc_sidereal)

    return cusp_arcsecs, ascendant_arcsec


def get_house_cusps_equal(
    ascendant_arcsec: ArcSeconds,
) -> list[ArcSeconds]:
    """Compute Equal House cusps (each house = 30° from Ascendant).

    Used as fallback when Placidus is distorted (near equator).

    Returns:
        List of 12 cusp positions in arc-seconds.
    """
    cusps: list[ArcSeconds] = []
    for i in range(12):
        cusp = (ascendant_arcsec + i * ARCSEC_PER_SIGN) % ARCSEC_FULL_CIRCLE
        cusps.append(ArcSeconds(cusp))
    return cusps
