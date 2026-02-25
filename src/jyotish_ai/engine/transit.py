"""
Jyotish AI — Transit Position Scanner

Computes current / future sidereal positions of slow-moving planets
(Jupiter, Saturn by default) for double-transit analysis.

Two entry points:
  get_transit_positions  — single-date snapshot at noon UT
  scan_monthly_transits  — month-by-month table (15th of each month)
"""

from __future__ import annotations

from datetime import date, time, timedelta

from jyotish_ai.domain.types import (
    Planet,
    Sign,
    ArcSeconds,
    ARCSEC_PER_SIGN,
    ARCSEC_FULL_CIRCLE,
)
from jyotish_ai.engine.ephemeris import get_planet_longitude, date_to_jd, arcsec_to_sign


# Default planets for double-transit analysis
_DEFAULT_PLANETS: list[Planet] = [Planet.JUPITER, Planet.SATURN]


# ──────────────────────────────────────────────────────────────────
# Single-date transit positions
# ──────────────────────────────────────────────────────────────────

def get_transit_positions(
    query_date: date,
    planets: list[Planet] | None = None,
    ayanamsha: str = "lahiri",
) -> dict[Planet, tuple[ArcSeconds, Sign]]:
    """Get sidereal positions of planets for a given date.

    Uses mid-day (12:00 noon UT) for stable transit positions.

    Args:
        query_date: The date to compute positions for
        planets: List of planets to compute (defaults to Jupiter + Saturn
                 for double transit)
        ayanamsha: "lahiri" or "kp"

    Returns:
        Dict mapping Planet -> (longitude_arcsec, sign)
    """
    if planets is None:
        planets = _DEFAULT_PLANETS

    # Noon UT — stable mid-day position
    jd = date_to_jd(query_date, time(12, 0, 0), tz_offset=0.0)

    positions: dict[Planet, tuple[ArcSeconds, Sign]] = {}
    for planet in planets:
        arcsec, _is_retrograde = get_planet_longitude(jd, planet, ayanamsha)
        sign = arcsec_to_sign(arcsec)
        positions[planet] = (arcsec, sign)

    return positions


# ──────────────────────────────────────────────────────────────────
# Monthly transit scan
# ──────────────────────────────────────────────────────────────────

def scan_monthly_transits(
    start_date: date,
    months: int = 24,
    planets: list[Planet] | None = None,
    ayanamsha: str = "lahiri",
) -> list[dict]:
    """Scan transit positions month by month.

    Uses the 15th of each month for stability.

    Args:
        start_date: First month to scan
        months: Number of months to scan (default 24)
        planets: Planets to track (defaults to [Jupiter, Saturn])
        ayanamsha: "lahiri" or "kp"

    Returns:
        List of dicts, one per month::

            [
                {
                    "month": "2025-03",
                    "positions": {
                        Planet.JUPITER: (arcsec, Sign.ARIES),
                        Planet.SATURN: (arcsec, Sign.PISCES),
                    },
                },
                ...
            ]
    """
    if planets is None:
        planets = _DEFAULT_PLANETS

    results: list[dict] = []

    for i in range(months):
        # Month arithmetic: handle year roll-over correctly
        year = start_date.year + (start_date.month - 1 + i) // 12
        month = (start_date.month - 1 + i) % 12 + 1
        scan_date = date(year, month, 15)

        positions = get_transit_positions(scan_date, planets, ayanamsha)

        results.append({
            "month": f"{year:04d}-{month:02d}",
            "positions": positions,
        })

    return results
