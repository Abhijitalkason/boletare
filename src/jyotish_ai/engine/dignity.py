"""
Jyotish AI — Layer 1: Planetary Dignity Scoring Engine

Computes the classical Vedic dignity classification for each planet based
on its sidereal longitude.  Dignity determines how "comfortable" a planet
is in its current sign, which directly feeds into promise-strength scoring
in Gate 1 of the prediction pipeline.

The seven dignity tiers, in descending strength:

1. **Exalted** (1.0)      — planet in its exaltation sign
2. **Moolatrikona** (0.85) — planet in its moolatrikona sign AND degree range
3. **Own** (0.75)          — planet in a sign it rules
4. **Friendly** (0.5)      — sign lord is a natural friend
5. **Neutral** (0.25)      — sign lord is neutral
6. **Enemy** (0.125)       — sign lord is a natural enemy
7. **Debilitated** (0.0)   — planet in its debilitation sign

Classification priority: exaltation > debilitation > moolatrikona > own
sign > friendship/neutral/enemy.  Rahu and Ketu have exaltation and
debilitation entries but no moolatrikona, own signs, or friendship data;
they default to Neutral when none of the higher tiers match.
"""

from __future__ import annotations

from jyotish_ai.domain.types import (
    Planet,
    Sign,
    Dignity,
    DIGNITY_SCORE,
    ARCSEC_PER_SIGN,
    ARCSEC_PER_DEGREE,
)
from jyotish_ai.domain.constants import (
    EXALTATION,
    DEBILITATION,
    MOOLATRIKONA,
    OWN_SIGNS,
    SIGN_LORD,
    NATURAL_FRIENDSHIP,
    get_sign_from_arcsec,
)


# ──────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────

def _get_degree_in_sign(longitude_arcsec: int) -> float:
    """Get degree position within the sign (0.0 to 30.0).

    The position is computed as the remainder after dividing by one sign's
    worth of arc-seconds, then converting from arc-seconds to degrees.

    >>> _get_degree_in_sign(0)
    0.0
    >>> _get_degree_in_sign(108_000)
    0.0
    >>> _get_degree_in_sign(54_000)
    15.0
    """
    return (longitude_arcsec % ARCSEC_PER_SIGN) / ARCSEC_PER_DEGREE


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def compute_dignity(
    planet: Planet,
    longitude_arcsec: int,
) -> tuple[Dignity, float]:
    """Compute dignity classification and numeric score for a planet.

    The classification follows the classical priority order: exaltation is
    checked first, then debilitation, moolatrikona, own sign, and finally
    the friendship relationship with the sign lord.

    Args:
        planet: The planet to evaluate.
        longitude_arcsec: Sidereal longitude in arc-seconds (0 to 1,295,999).

    Returns:
        A tuple of (dignity_enum, score_float), e.g. (Dignity.EXALTED, 1.0).
    """
    sign = get_sign_from_arcsec(longitude_arcsec)

    # 1. Exaltation check
    if EXALTATION.get(planet) == sign:
        return Dignity.EXALTED, DIGNITY_SCORE[Dignity.EXALTED]

    # 2. Debilitation check
    if DEBILITATION.get(planet) == sign:
        return Dignity.DEBILITATED, DIGNITY_SCORE[Dignity.DEBILITATED]

    # 3. Moolatrikona check (Rahu/Ketu not in MOOLATRIKONA, skip for them)
    if planet in MOOLATRIKONA:
        mt_sign, mt_start_deg, mt_end_deg = MOOLATRIKONA[planet]
        if sign == mt_sign:
            degree = _get_degree_in_sign(longitude_arcsec)
            if mt_start_deg <= degree <= mt_end_deg:
                return Dignity.MOOLATRIKONA, DIGNITY_SCORE[Dignity.MOOLATRIKONA]

    # 4. Own sign check
    if sign in OWN_SIGNS.get(planet, []):
        return Dignity.OWN, DIGNITY_SCORE[Dignity.OWN]

    # 5. Friendship / Neutral / Enemy via NATURAL_FRIENDSHIP
    if planet in NATURAL_FRIENDSHIP:
        sign_lord = SIGN_LORD[sign]
        relationships = NATURAL_FRIENDSHIP[planet]

        if sign_lord in relationships["friends"]:
            return Dignity.FRIENDLY, DIGNITY_SCORE[Dignity.FRIENDLY]

        if sign_lord in relationships["neutral"]:
            return Dignity.NEUTRAL, DIGNITY_SCORE[Dignity.NEUTRAL]

        if sign_lord in relationships["enemies"]:
            return Dignity.ENEMY, DIGNITY_SCORE[Dignity.ENEMY]

    # Rahu/Ketu (not in NATURAL_FRIENDSHIP) default to Neutral
    return Dignity.NEUTRAL, DIGNITY_SCORE[Dignity.NEUTRAL]


def compute_all_dignities(
    planet_positions: dict[Planet, int],
) -> dict[Planet, tuple[Dignity, float]]:
    """Compute dignities for all planets at once.

    A convenience wrapper that calls :func:`compute_dignity` for every
    planet in the provided positions dict.

    Args:
        planet_positions: Mapping of Planet to longitude in arc-seconds.

    Returns:
        Dict mapping each Planet to its (Dignity, score) tuple.
    """
    return {
        planet: compute_dignity(planet, longitude_arcsec)
        for planet, longitude_arcsec in planet_positions.items()
    }
