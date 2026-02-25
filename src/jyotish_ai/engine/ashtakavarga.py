"""
Jyotish AI — Layer 1: Ashtakavarga Computation Engine

Computes the three Ashtakavarga tables used by the prediction engine:

1. **BAV** (Bhinnashtakavarga) — Individual planet bindus across 12 signs.
   Each of the 7 planets (Sun through Saturn) has its own 12-sign table
   with 0-8 bindus per sign, derived from the classical contribution rules.

2. **SAV** (Sarvashtakavarga) — Sum of all 7 BAV tables per sign.
   Each sign gets 0-56 points (7 planets x 8 max contributors).

3. **Trikona Shodhana** — Element-wise reduction of the BAV tables.
   Within each trikona group (fire, earth, air, water), the minimum value
   is subtracted from all three signs.  SAV is then recomputed from the
   reduced BAV values.

Architecture doc section 5.3:
  "Ashtakavarga BAV/SAV scores feed Gate 3 (Transit scan): the transit
   BAV score for Jupiter/Saturn signs determines double-transit strength."
"""

from __future__ import annotations

from jyotish_ai.domain.types import Planet, Sign
from jyotish_ai.domain.models import AshtakavargaTable, PlanetPosition
from jyotish_ai.domain.constants import BAV_CONTRIBUTION_RULES

# ──────────────────────────────────────────────────────────────────────
# The 7 planets that have BAV tables (Rahu and Ketu are excluded)
# ──────────────────────────────────────────────────────────────────────
_BAV_PLANETS: list[Planet] = [
    Planet.SUN,
    Planet.MOON,
    Planet.MARS,
    Planet.MERCURY,
    Planet.JUPITER,
    Planet.VENUS,
    Planet.SATURN,
]

# ──────────────────────────────────────────────────────────────────────
# Trikona groups — signs sharing the same element (120° apart)
# ──────────────────────────────────────────────────────────────────────
_TRIKONA_GROUPS: list[tuple[Sign, Sign, Sign]] = [
    (Sign.ARIES,  Sign.LEO,       Sign.SAGITTARIUS),   # Fire
    (Sign.TAURUS, Sign.VIRGO,     Sign.CAPRICORN),     # Earth
    (Sign.GEMINI, Sign.LIBRA,     Sign.AQUARIUS),      # Air
    (Sign.CANCER, Sign.SCORPIO,   Sign.PISCES),        # Water
]


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def compute_ashtakavarga(
    planets: list[PlanetPosition],
    ascendant_sign: Sign,
) -> AshtakavargaTable:
    """Compute BAV, SAV, and Trikona-reduced SAV.

    Args:
        planets: All 9 planet positions (only the 7 BAV planets are used
                 for contribution; Rahu and Ketu are ignored).
        ascendant_sign: The Lagna sign, used as the "Asc" contributor.

    Returns:
        AshtakavargaTable with ``bav``, ``sav``, and ``sav_trikona_reduced``
        fields keyed by string names for JSON serialisation.
    """
    bav = _compute_bav(planets, ascendant_sign)
    sav = _compute_sav(bav)

    reduced_bav = _trikona_shodhana(bav)
    sav_trikona_reduced = _compute_sav(reduced_bav)

    # Convert internal typed dicts to string-keyed dicts for the model
    bav_out: dict[str, dict[str, int]] = {}
    for planet in _BAV_PLANETS:
        bav_out[planet.value] = {
            sign.name: bav[planet][sign] for sign in Sign
        }

    sav_out: dict[str, int] = {sign.name: sav[sign] for sign in Sign}
    sav_reduced_out: dict[str, int] = {
        sign.name: sav_trikona_reduced[sign] for sign in Sign
    }

    return AshtakavargaTable(
        bav=bav_out,
        sav=sav_out,
        sav_trikona_reduced=sav_reduced_out,
    )


# ──────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────

def _compute_bav(
    planets: list[PlanetPosition],
    ascendant_sign: Sign,
) -> dict[Planet, dict[Sign, int]]:
    """Compute the Bhinnashtakavarga for all 7 BAV planets.

    For each BAV planet, for each of the 12 signs, iterate over the 8
    contributors (7 planets + Ascendant).  A bindu is awarded when the
    house offset from the contributor's sign to the evaluated sign falls
    within the classical contribution rule set.

    Args:
        planets: All planet positions (only BAV planets are used as
                 contributors; Rahu/Ketu positions are never referenced).
        ascendant_sign: The Lagna sign for the "Asc" contributor.

    Returns:
        Nested dict: planet -> sign -> bindu count (0-8).
    """
    # Build a quick lookup: Planet -> Sign
    planet_sign: dict[Planet, Sign] = {}
    for pp in planets:
        planet_sign[pp.planet] = pp.sign

    bav: dict[Planet, dict[Sign, int]] = {}

    for bav_planet in _BAV_PLANETS:
        rules = BAV_CONTRIBUTION_RULES[bav_planet]
        planet_table: dict[Sign, int] = {}

        for sign in Sign:
            points = 0

            for contributor, houses in rules.items():
                # Determine the contributor's sign
                if contributor == "Asc":
                    contributor_sign = ascendant_sign
                else:
                    contributor_sign = planet_sign[contributor]

                # House offset from contributor to the evaluated sign
                # 1-indexed: same sign = house 1
                house_offset = (int(sign) - int(contributor_sign)) % 12 + 1

                if house_offset in houses:
                    points += 1

            planet_table[sign] = points

        bav[bav_planet] = planet_table

    return bav


def _compute_sav(bav: dict[Planet, dict[Sign, int]]) -> dict[Sign, int]:
    """Compute the Sarvashtakavarga by summing all 7 BAV tables per sign.

    Args:
        bav: The BAV dict (planet -> sign -> points).

    Returns:
        Dict mapping each sign to its total SAV points (0-56).
    """
    sav: dict[Sign, int] = {}

    for sign in Sign:
        total = 0
        for planet in _BAV_PLANETS:
            total += bav[planet][sign]
        sav[sign] = total

    return sav


def _trikona_shodhana(
    bav: dict[Planet, dict[Sign, int]],
) -> dict[Planet, dict[Sign, int]]:
    """Apply Trikona Shodhana reduction to the BAV tables.

    For each of the 7 BAV planets and each of the 4 trikona groups,
    find the minimum BAV value among the 3 signs in the group and
    subtract it from all three.  This normalises each elemental triad
    so that its weakest sign becomes zero.

    Args:
        bav: The original (unreduced) BAV dict.

    Returns:
        A new BAV dict with reduced values.  The original is not mutated.
    """
    # Deep-copy the BAV structure so the original is not modified
    reduced: dict[Planet, dict[Sign, int]] = {
        planet: {sign: points for sign, points in sign_table.items()}
        for planet, sign_table in bav.items()
    }

    for planet in _BAV_PLANETS:
        for group in _TRIKONA_GROUPS:
            s1, s2, s3 = group
            v1 = reduced[planet][s1]
            v2 = reduced[planet][s2]
            v3 = reduced[planet][s3]

            min_val = min(v1, v2, v3)

            reduced[planet][s1] = v1 - min_val
            reduced[planet][s2] = v2 - min_val
            reduced[planet][s3] = v3 - min_val

    return reduced
