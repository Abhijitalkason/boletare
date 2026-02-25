"""
Jyotish AI — Layer 1: Vimshottari Dasha Engine

The Vimshottari Dasha system divides life into 120 years of planetary periods.

Algorithm:
1. Moon's Nakshatra determines the starting Dasha lord
2. Moon's exact position within the Nakshatra determines elapsed portion
3. Build full 3-level tree: Mahadasha → Antardasha → Pratyantardasha
4. Handle dual Dasha trees when Moon is on Nakshatra boundary

Architecture doc sections 3.6, 4.2:
  "The current Mahadasha lord (6-20 year period) and Antardasha lord (months)
   must be significators of the event house."
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from jyotish_ai.domain.types import (
    Planet,
    DashaLevel,
    ARCSEC_PER_NAKSHATRA,
)
from jyotish_ai.domain.models import DashaPeriod

# Dasha order and durations (total = 120 years)
_VIMSHOTTARI_ORDER: list[Planet] = [
    Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON,
    Planet.MARS, Planet.RAHU, Planet.JUPITER, Planet.SATURN,
    Planet.MERCURY,
]

_VIMSHOTTARI_YEARS: dict[Planet, int] = {
    Planet.KETU: 7,
    Planet.VENUS: 20,
    Planet.SUN: 6,
    Planet.MOON: 10,
    Planet.MARS: 7,
    Planet.RAHU: 18,
    Planet.JUPITER: 16,
    Planet.SATURN: 19,
    Planet.MERCURY: 17,
}

_TOTAL_YEARS = 120

# Nakshatra lord mapping (repeating pattern of 9 across 27 Nakshatras)
_NAKSHATRA_LORD_BY_INDEX: list[Planet] = [
    _VIMSHOTTARI_ORDER[i % 9] for i in range(27)
]

# Days per year for Dasha calculation
_DAYS_PER_YEAR = 365.25


def compute_dasha_tree(
    moon_arcsec: int,
    birth_date: date,
    include_pratyantardasha: bool = False,
) -> list[DashaPeriod]:
    """Compute the full Vimshottari Dasha tree from Moon's position.

    Args:
        moon_arcsec: Moon's sidereal longitude in arc-seconds
        birth_date: Date of birth
        include_pratyantardasha: If True, compute 3rd level (default False for speed)

    Returns:
        List of DashaPeriod objects (Mahadashas, each containing Antardashas)
    """
    # Determine starting Nakshatra and lord
    nak_index = (moon_arcsec % (ARCSEC_PER_NAKSHATRA * 27)) // ARCSEC_PER_NAKSHATRA
    starting_lord = _NAKSHATRA_LORD_BY_INDEX[nak_index]

    # Compute elapsed fraction within the Nakshatra
    position_in_nak = moon_arcsec % ARCSEC_PER_NAKSHATRA
    elapsed_fraction = position_in_nak / ARCSEC_PER_NAKSHATRA

    # Build ordered Dasha sequence starting from this lord
    start_idx = _VIMSHOTTARI_ORDER.index(starting_lord)
    ordered = _VIMSHOTTARI_ORDER[start_idx:] + _VIMSHOTTARI_ORDER[:start_idx]

    periods: list[DashaPeriod] = []
    current_date = birth_date

    for i, md_lord in enumerate(ordered):
        md_total_years = _VIMSHOTTARI_YEARS[md_lord]
        md_total_days = md_total_years * _DAYS_PER_YEAR

        if i == 0:
            # First Dasha: subtract elapsed portion
            remaining_fraction = 1.0 - elapsed_fraction
            md_actual_days = md_total_days * remaining_fraction
        else:
            md_actual_days = md_total_days

        md_end = current_date + timedelta(days=md_actual_days)

        # Compute Antardashas within this Mahadasha
        sub_periods = _compute_sub_periods(
            md_lord=md_lord,
            md_actual_days=md_actual_days,
            md_start=current_date,
            level=DashaLevel.ANTARDASHA,
            include_next_level=include_pratyantardasha,
        )

        periods.append(DashaPeriod(
            level=DashaLevel.MAHADASHA,
            planet=md_lord,
            start_date=current_date,
            end_date=md_end,
            duration_days=round(md_actual_days, 2),
            sub_periods=sub_periods,
        ))

        current_date = md_end

    return periods


def _compute_sub_periods(
    md_lord: Planet,
    md_actual_days: float,
    md_start: date,
    level: DashaLevel,
    include_next_level: bool = False,
) -> list[DashaPeriod]:
    """Compute sub-periods within a Dasha period.

    Antardasha duration = (MD_days * AD_lord_years) / 120
    The sub-periods start from the Mahadasha lord's own period.
    """
    # Sub-period order starts from the parent lord
    start_idx = _VIMSHOTTARI_ORDER.index(md_lord)
    ad_order = _VIMSHOTTARI_ORDER[start_idx:] + _VIMSHOTTARI_ORDER[:start_idx]

    sub_periods: list[DashaPeriod] = []
    current_date = md_start

    for ad_lord in ad_order:
        ad_years = _VIMSHOTTARI_YEARS[ad_lord]
        ad_duration_days = (md_actual_days * ad_years) / _TOTAL_YEARS
        ad_end = current_date + timedelta(days=ad_duration_days)

        # Pratyantardasha (3rd level) if requested
        prat_periods: list[DashaPeriod] = []
        if include_next_level and level == DashaLevel.ANTARDASHA:
            prat_periods = _compute_sub_periods(
                md_lord=ad_lord,
                md_actual_days=ad_duration_days,
                md_start=current_date,
                level=DashaLevel.PRATYANTARDASHA,
                include_next_level=False,
            )

        sub_periods.append(DashaPeriod(
            level=level,
            planet=ad_lord,
            start_date=current_date,
            end_date=ad_end,
            duration_days=round(ad_duration_days, 2),
            sub_periods=prat_periods,
        ))

        current_date = ad_end

    return sub_periods


def find_active_periods(
    dasha_tree: list[DashaPeriod],
    query_date: date,
) -> tuple[Optional[DashaPeriod], Optional[DashaPeriod]]:
    """Find the active Mahadasha and Antardasha for a given date.

    Args:
        dasha_tree: List of Mahadasha periods (with nested Antardashas)
        query_date: The date to check

    Returns:
        (active_mahadasha, active_antardasha) — either may be None
    """
    active_md: Optional[DashaPeriod] = None
    active_ad: Optional[DashaPeriod] = None

    for md in dasha_tree:
        if md.start_date <= query_date <= md.end_date:
            active_md = md
            for ad in md.sub_periods:
                if ad.start_date <= query_date <= ad.end_date:
                    active_ad = ad
                    break
            break

    return active_md, active_ad
