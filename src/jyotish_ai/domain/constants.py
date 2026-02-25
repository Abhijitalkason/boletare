"""
Jyotish AI -- Core Domain Constants

THE single most critical file in the system.  Every piece of classical Vedic
astrology domain knowledge that can be expressed as a deterministic lookup
table lives here.  All computation modules import from this file.

Design rules
------------
* Pure data -- no I/O, no side effects.
* Every table is fully enumerated -- no lazy computation.
* ArcSeconds is the positional unit everywhere.
* Helper functions at the bottom are thin arithmetic wrappers.
"""

from __future__ import annotations

from jyotish_ai.domain.types import (
    Planet,
    Sign,
    EventType,
    ArcSeconds,
    ARCSEC_PER_SIGN,
    ARCSEC_PER_NAKSHATRA,
)

# Convenience re-imports used by helpers
from jyotish_ai.domain.types import ARCSEC_PER_DEGREE, ARCSEC_PER_PADA

# ======================================================================
# 1. SIGN_LORD -- which planet rules each sign
# ======================================================================
SIGN_LORD: dict[Sign, Planet] = {
    Sign.ARIES:       Planet.MARS,
    Sign.TAURUS:      Planet.VENUS,
    Sign.GEMINI:      Planet.MERCURY,
    Sign.CANCER:      Planet.MOON,
    Sign.LEO:         Planet.SUN,
    Sign.VIRGO:       Planet.MERCURY,
    Sign.LIBRA:       Planet.VENUS,
    Sign.SCORPIO:     Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN:   Planet.SATURN,
    Sign.AQUARIUS:    Planet.SATURN,
    Sign.PISCES:      Planet.JUPITER,
}

# ======================================================================
# 2. EXALTATION -- the sign where each planet is exalted
# ======================================================================
EXALTATION: dict[Planet, Sign] = {
    Planet.SUN:     Sign.ARIES,
    Planet.MOON:    Sign.TAURUS,
    Planet.MARS:    Sign.CAPRICORN,
    Planet.MERCURY: Sign.VIRGO,
    Planet.JUPITER: Sign.CANCER,
    Planet.VENUS:   Sign.PISCES,
    Planet.SATURN:  Sign.LIBRA,
    Planet.RAHU:    Sign.TAURUS,
    Planet.KETU:    Sign.SCORPIO,
}

# ======================================================================
# 3. DEBILITATION -- opposite of exaltation (7th sign away)
# ======================================================================
DEBILITATION: dict[Planet, Sign] = {
    Planet.SUN:     Sign.LIBRA,
    Planet.MOON:    Sign.SCORPIO,
    Planet.MARS:    Sign.CANCER,
    Planet.MERCURY: Sign.PISCES,
    Planet.JUPITER: Sign.CAPRICORN,
    Planet.VENUS:   Sign.VIRGO,
    Planet.SATURN:  Sign.ARIES,
    Planet.RAHU:    Sign.SCORPIO,
    Planet.KETU:    Sign.TAURUS,
}

# ======================================================================
# 4. MOOLATRIKONA -- (sign, start_degree, end_degree)
#    The planet has Moolatrikona dignity between start and end degrees
#    of the given sign.
# ======================================================================
MOOLATRIKONA: dict[Planet, tuple[Sign, int, int]] = {
    Planet.SUN:     (Sign.LEO,         0, 20),
    Planet.MOON:    (Sign.TAURUS,      4, 20),
    Planet.MARS:    (Sign.ARIES,       0, 12),
    Planet.MERCURY: (Sign.VIRGO,      16, 20),
    Planet.JUPITER: (Sign.SAGITTARIUS, 0, 10),
    Planet.VENUS:   (Sign.LIBRA,       0, 15),
    Planet.SATURN:  (Sign.AQUARIUS,    0, 20),
}

# ======================================================================
# 5. OWN_SIGNS -- signs owned by each planet
# ======================================================================
OWN_SIGNS: dict[Planet, list[Sign]] = {
    Planet.SUN:     [Sign.LEO],
    Planet.MOON:    [Sign.CANCER],
    Planet.MARS:    [Sign.ARIES,       Sign.SCORPIO],
    Planet.MERCURY: [Sign.GEMINI,      Sign.VIRGO],
    Planet.JUPITER: [Sign.SAGITTARIUS, Sign.PISCES],
    Planet.VENUS:   [Sign.TAURUS,      Sign.LIBRA],
    Planet.SATURN:  [Sign.CAPRICORN,   Sign.AQUARIUS],
    Planet.RAHU:    [],
    Planet.KETU:    [],
}

# ======================================================================
# 6. NATURAL BENEFICS / MALEFICS
#    Phase-1 static classification.  Moon's benefic status actually
#    depends on waxing/waning; Mercury's on conjunction with malefics.
#    Full dynamic check belongs in the dignity module.
# ======================================================================
NATURAL_BENEFICS: frozenset[Planet] = frozenset({
    Planet.JUPITER,
    Planet.VENUS,
    Planet.MOON,
    Planet.MERCURY,
})

NATURAL_MALEFICS: frozenset[Planet] = frozenset({
    Planet.SUN,
    Planet.MARS,
    Planet.SATURN,
    Planet.RAHU,
    Planet.KETU,
})

# ======================================================================
# 7. NATURAL_FRIENDSHIP  (Naisargika Maitri)
#    Classical table for the 7 visible planets.
#    Rahu/Ketu follow special rules handled elsewhere.
# ======================================================================
NATURAL_FRIENDSHIP: dict[Planet, dict[str, set[Planet]]] = {
    Planet.SUN: {
        "friends":  {Planet.MOON, Planet.MARS, Planet.JUPITER},
        "enemies":  {Planet.VENUS, Planet.SATURN},
        "neutral":  {Planet.MERCURY},
    },
    Planet.MOON: {
        "friends":  {Planet.SUN, Planet.MERCURY},
        "enemies":  set(),
        "neutral":  {Planet.MARS, Planet.JUPITER, Planet.VENUS, Planet.SATURN},
    },
    Planet.MARS: {
        "friends":  {Planet.SUN, Planet.MOON, Planet.JUPITER},
        "enemies":  {Planet.MERCURY},
        "neutral":  {Planet.VENUS, Planet.SATURN},
    },
    Planet.MERCURY: {
        "friends":  {Planet.SUN, Planet.VENUS},
        "enemies":  {Planet.MOON},
        "neutral":  {Planet.MARS, Planet.JUPITER, Planet.SATURN},
    },
    Planet.JUPITER: {
        "friends":  {Planet.SUN, Planet.MOON, Planet.MARS},
        "enemies":  {Planet.MERCURY, Planet.VENUS},
        "neutral":  {Planet.SATURN},
    },
    Planet.VENUS: {
        "friends":  {Planet.MERCURY, Planet.SATURN},
        "enemies":  {Planet.SUN, Planet.MOON},
        "neutral":  {Planet.MARS, Planet.JUPITER},
    },
    Planet.SATURN: {
        "friends":  {Planet.MERCURY, Planet.VENUS},
        "enemies":  {Planet.SUN, Planet.MOON, Planet.MARS},
        "neutral":  {Planet.JUPITER},
    },
}

# ======================================================================
# 8. SPECIAL_ASPECTS -- houses additionally aspected beyond the
#    universal 7th-house aspect.  Values are house offsets (1-indexed).
# ======================================================================
SPECIAL_ASPECTS: dict[Planet, list[int]] = {
    Planet.MARS:    [4, 8],
    Planet.JUPITER: [5, 9],
    Planet.SATURN:  [3, 10],
    Planet.RAHU:    [5, 9],
    Planet.KETU:    [5, 9],
}

# ======================================================================
# 9. VIMSHOTTARI_ORDER -- 9 planets in Vimshottari Dasha cycle order
# ======================================================================
VIMSHOTTARI_ORDER: list[Planet] = [
    Planet.KETU,
    Planet.VENUS,
    Planet.SUN,
    Planet.MOON,
    Planet.MARS,
    Planet.RAHU,
    Planet.JUPITER,
    Planet.SATURN,
    Planet.MERCURY,
]

# ======================================================================
# 10. VIMSHOTTARI_YEARS -- total Mahadasha years for each planet
#     Full cycle = 120 years
# ======================================================================
VIMSHOTTARI_YEARS: dict[Planet, int] = {
    Planet.KETU:     7,
    Planet.VENUS:   20,
    Planet.SUN:      6,
    Planet.MOON:    10,
    Planet.MARS:     7,
    Planet.RAHU:    18,
    Planet.JUPITER: 16,
    Planet.SATURN:  19,
    Planet.MERCURY: 17,
}

# ======================================================================
# 11. NAKSHATRA_NAMES -- 27 nakshatras in sidereal order (0-indexed)
# ======================================================================
NAKSHATRA_NAMES: list[str] = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva_Phalguni",
    "Uttara_Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva_Ashadha",
    "Uttara_Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva_Bhadrapada",
    "Uttara_Bhadrapada",
    "Revati",
]

# ======================================================================
# 12. NAKSHATRA_LORDS -- maps each nakshatra name to its Vimshottari
#     dasha lord.  The 9-planet pattern repeats 3 times across 27.
# ======================================================================
NAKSHATRA_LORDS: dict[str, Planet] = {
    name: VIMSHOTTARI_ORDER[i % 9]
    for i, name in enumerate(NAKSHATRA_NAMES)
}

# ======================================================================
# 13. EVENT_HOUSE_MAP -- primary bhava signifier for each event type
# ======================================================================
EVENT_HOUSE_MAP: dict[EventType, int] = {
    EventType.MARRIAGE:  7,
    EventType.CAREER:   10,
    EventType.CHILD:     5,
    EventType.PROPERTY:  4,
    EventType.HEALTH:    6,
}

# ======================================================================
# 14. PLANET_SWE_ID -- Swiss Ephemeris numeric IDs
#     Rahu = 11 (True Node).  Ketu is derived (Rahu + 180 deg).
# ======================================================================
PLANET_SWE_ID: dict[Planet, int] = {
    Planet.SUN:     0,
    Planet.MOON:    1,
    Planet.MERCURY: 2,
    Planet.VENUS:   3,
    Planet.MARS:    4,
    Planet.JUPITER: 5,
    Planet.SATURN:  6,
    Planet.RAHU:   11,   # True Node
}

# ======================================================================
# 15. BAV_CONTRIBUTION_RULES
#     Classical Ashtakavarga benefic-point tables.
#
#     Structure:  BAV_CONTRIBUTION_RULES[planet_whose_BAV]
#                     [contributing_body] -> frozenset of houses
#     where houses are 1-12, counted from the contributing body.
#
#     "Asc" is represented by the string "Asc" as a key.
#     7 planet BAVs (Sun--Saturn).  Rahu/Ketu do not have BAV.
# ======================================================================
BAV_CONTRIBUTION_RULES: dict[Planet, dict[Planet | str, frozenset[int]]] = {
    # ---- Sun's BAV (Surya Ashtakavarga) ----
    Planet.SUN: {
        Planet.SUN:     frozenset({1, 2, 4, 7, 8, 9, 10, 11}),
        Planet.MOON:    frozenset({3, 6, 10, 11}),
        Planet.MARS:    frozenset({1, 2, 4, 7, 8, 9, 10, 11}),
        Planet.MERCURY: frozenset({3, 5, 6, 9, 10, 11, 12}),
        Planet.JUPITER: frozenset({5, 6, 9, 11}),
        Planet.VENUS:   frozenset({6, 7, 12}),
        Planet.SATURN:  frozenset({1, 2, 4, 7, 8, 9, 10, 11}),
        "Asc":          frozenset({3, 4, 6, 10, 11, 12}),
    },

    # ---- Moon's BAV (Chandra Ashtakavarga) ----
    Planet.MOON: {
        Planet.SUN:     frozenset({3, 6, 7, 8, 10, 11}),
        Planet.MOON:    frozenset({1, 3, 6, 7, 10, 11}),
        Planet.MARS:    frozenset({2, 3, 5, 6, 9, 10, 11}),
        Planet.MERCURY: frozenset({1, 3, 4, 5, 7, 8, 10, 11}),
        Planet.JUPITER: frozenset({1, 4, 7, 8, 10, 11, 12}),
        Planet.VENUS:   frozenset({3, 4, 5, 7, 9, 10, 11}),
        Planet.SATURN:  frozenset({3, 5, 6, 11}),
        "Asc":          frozenset({3, 6, 10, 11}),
    },

    # ---- Mars' BAV (Mangala Ashtakavarga) ----
    Planet.MARS: {
        Planet.SUN:     frozenset({3, 5, 6, 10, 11}),
        Planet.MOON:    frozenset({3, 6, 11}),
        Planet.MARS:    frozenset({1, 2, 4, 7, 8, 10, 11}),
        Planet.MERCURY: frozenset({3, 5, 6, 11}),
        Planet.JUPITER: frozenset({6, 10, 11, 12}),
        Planet.VENUS:   frozenset({6, 8, 11, 12}),
        Planet.SATURN:  frozenset({1, 4, 7, 8, 9, 10, 11}),
        "Asc":          frozenset({1, 3, 6, 10, 11}),
    },

    # ---- Mercury's BAV (Budha Ashtakavarga) ----
    Planet.MERCURY: {
        Planet.SUN:     frozenset({5, 6, 9, 11, 12}),
        Planet.MOON:    frozenset({2, 4, 6, 8, 10, 11}),
        Planet.MARS:    frozenset({1, 2, 4, 7, 8, 9, 10, 11}),
        Planet.MERCURY: frozenset({1, 3, 5, 6, 9, 10, 11, 12}),
        Planet.JUPITER: frozenset({6, 8, 11, 12}),
        Planet.VENUS:   frozenset({1, 2, 3, 4, 5, 8, 9, 11}),
        Planet.SATURN:  frozenset({1, 2, 4, 7, 8, 9, 10, 11}),
        "Asc":          frozenset({1, 2, 4, 6, 8, 10, 11}),
    },

    # ---- Jupiter's BAV (Guru Ashtakavarga) ----
    Planet.JUPITER: {
        Planet.SUN:     frozenset({1, 2, 3, 4, 7, 8, 9, 10, 11}),
        Planet.MOON:    frozenset({2, 5, 7, 9, 11}),
        Planet.MARS:    frozenset({1, 2, 4, 7, 8, 10, 11}),
        Planet.MERCURY: frozenset({1, 2, 4, 5, 6, 9, 10, 11}),
        Planet.JUPITER: frozenset({1, 2, 3, 4, 7, 8, 10, 11}),
        Planet.VENUS:   frozenset({2, 5, 6, 9, 10, 11}),
        Planet.SATURN:  frozenset({3, 5, 6, 12}),
        "Asc":          frozenset({1, 2, 4, 5, 6, 7, 9, 10, 11}),
    },

    # ---- Venus' BAV (Shukra Ashtakavarga) ----
    Planet.VENUS: {
        Planet.SUN:     frozenset({8, 11, 12}),
        Planet.MOON:    frozenset({1, 2, 3, 4, 5, 8, 9, 11, 12}),
        Planet.MARS:    frozenset({3, 5, 6, 9, 11, 12}),
        Planet.MERCURY: frozenset({3, 5, 6, 9, 11}),
        Planet.JUPITER: frozenset({5, 8, 9, 10, 11}),
        Planet.VENUS:   frozenset({1, 2, 3, 4, 5, 8, 9, 10, 11}),
        Planet.SATURN:  frozenset({3, 4, 5, 8, 9, 10, 11}),
        "Asc":          frozenset({1, 2, 3, 4, 5, 8, 9, 11}),
    },

    # ---- Saturn's BAV (Shani Ashtakavarga) ----
    Planet.SATURN: {
        Planet.SUN:     frozenset({1, 2, 4, 7, 8, 10, 11}),
        Planet.MOON:    frozenset({3, 6, 11}),
        Planet.MARS:    frozenset({3, 5, 6, 10, 11, 12}),
        Planet.MERCURY: frozenset({6, 8, 9, 10, 11, 12}),
        Planet.JUPITER: frozenset({5, 6, 11, 12}),
        Planet.VENUS:   frozenset({6, 11, 12}),
        Planet.SATURN:  frozenset({3, 5, 6, 11}),
        "Asc":          frozenset({1, 3, 4, 6, 10, 11}),
    },
}


# ######################################################################
# 16. HELPER FUNCTIONS
# ######################################################################

def sign_to_house(sign: Sign, ascendant_sign: Sign) -> int:
    """Return the bhava (1-12) that *sign* occupies when *ascendant_sign*
    is the first house.

    >>> sign_to_house(Sign.ARIES, Sign.ARIES)
    1
    >>> sign_to_house(Sign.PISCES, Sign.ARIES)
    12
    """
    return (sign - ascendant_sign) % 12 + 1


def house_to_sign(house: int, ascendant_sign: Sign) -> Sign:
    """Return the zodiac sign that corresponds to *house* (1-12) given
    the ascendant sign.

    >>> house_to_sign(1, Sign.ARIES)
    <Sign.ARIES: 1>
    >>> house_to_sign(12, Sign.ARIES)
    <Sign.PISCES: 12>
    """
    return Sign((ascendant_sign - 1 + house - 1) % 12 + 1)


def get_kendras(house: int) -> list[int]:
    """Return the four kendra houses (1, 4, 7, 10) counted from *house*.

    >>> get_kendras(1)
    [1, 4, 7, 10]
    >>> get_kendras(5)
    [5, 8, 11, 2]
    """
    return [(house - 1 + offset) % 12 + 1 for offset in (0, 3, 6, 9)]


def get_trikonas(house: int) -> list[int]:
    """Return the three trikona houses (1, 5, 9) counted from *house*.

    >>> get_trikonas(1)
    [1, 5, 9]
    >>> get_trikonas(3)
    [3, 7, 11]
    """
    return [(house - 1 + offset) % 12 + 1 for offset in (0, 4, 8)]


def get_kendra_trikona(house: int) -> list[int]:
    """Return the sorted union of kendras and trikonas from *house*.

    >>> get_kendra_trikona(1)
    [1, 4, 5, 7, 9, 10]
    """
    return sorted(set(get_kendras(house)) | set(get_trikonas(house)))


def get_sign_from_arcsec(arcsec: int) -> Sign:
    """Return the zodiac sign for a sidereal longitude in arc-seconds.

    The longitude must be in [0, 1_296_000).  Each sign spans exactly
    108,000 arc-seconds (30 degrees).

    >>> get_sign_from_arcsec(0)
    <Sign.ARIES: 1>
    >>> get_sign_from_arcsec(107_999)
    <Sign.ARIES: 1>
    >>> get_sign_from_arcsec(108_000)
    <Sign.TAURUS: 2>
    """
    return Sign(arcsec // ARCSEC_PER_SIGN + 1)


def get_nakshatra_index(arcsec: int) -> int:
    """Return the 0-based nakshatra index (0-26) for a sidereal longitude.

    Each nakshatra spans exactly 48,000 arc-seconds (13 deg 20 min).

    >>> get_nakshatra_index(0)
    0
    >>> get_nakshatra_index(47_999)
    0
    >>> get_nakshatra_index(48_000)
    1
    """
    return arcsec // ARCSEC_PER_NAKSHATRA


def get_nakshatra_name(arcsec: int) -> str:
    """Return the nakshatra name for a sidereal longitude in arc-seconds.

    >>> get_nakshatra_name(0)
    'Ashwini'
    >>> get_nakshatra_name(48_000)
    'Bharani'
    """
    return NAKSHATRA_NAMES[get_nakshatra_index(arcsec)]


def get_pada(arcsec: int) -> int:
    """Return the pada (1-4) within the nakshatra for a sidereal longitude.

    Each nakshatra is divided into 4 equal padas of 12,000 arc-seconds
    (3 deg 20 min) each.

    >>> get_pada(0)
    1
    >>> get_pada(11_999)
    1
    >>> get_pada(12_000)
    2
    >>> get_pada(47_999)
    4
    """
    offset_in_nakshatra = arcsec % ARCSEC_PER_NAKSHATRA
    return offset_in_nakshatra // ARCSEC_PER_PADA + 1
