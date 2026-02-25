"""
Jyotish AI — Test Domain Types and Constants

Validates enum completeness, conversion constants, and helper functions
from jyotish_ai.domain.types and jyotish_ai.domain.constants.
"""

from jyotish_ai.domain.types import (
    Planet, Sign, EventType, Dignity, BirthTimeTier, DashaLevel,
    ArcSeconds, ARCSEC_PER_DEGREE, ARCSEC_PER_SIGN, ARCSEC_PER_NAKSHATRA,
    ARCSEC_PER_PADA, ARCSEC_FULL_CIRCLE, DIGNITY_SCORE,
)
from jyotish_ai.domain.constants import (
    SIGN_LORD, EXALTATION, DEBILITATION, OWN_SIGNS, EVENT_HOUSE_MAP,
    NAKSHATRA_NAMES, BAV_CONTRIBUTION_RULES,
    sign_to_house, house_to_sign, get_kendras, get_trikonas,
    get_sign_from_arcsec, get_nakshatra_index, get_nakshatra_name, get_pada,
)


def test_arcsec_conversion_constants():
    """Verify fundamental arc-second conversion constants."""
    assert ARCSEC_PER_DEGREE == 3600
    assert ARCSEC_PER_SIGN == 108000
    assert ARCSEC_PER_NAKSHATRA == 48000
    assert ARCSEC_PER_PADA == 12000
    assert ARCSEC_FULL_CIRCLE == 1296000
    # Internal consistency: 12 signs fill the full circle
    assert ARCSEC_PER_SIGN * 12 == ARCSEC_FULL_CIRCLE
    # 27 nakshatras fill the full circle
    assert ARCSEC_PER_NAKSHATRA * 27 == ARCSEC_FULL_CIRCLE


def test_sign_enum_values():
    """All 12 zodiac signs have correct integer values 1-12."""
    assert len(Sign) == 12
    assert Sign.ARIES == 1
    assert Sign.TAURUS == 2
    assert Sign.GEMINI == 3
    assert Sign.CANCER == 4
    assert Sign.LEO == 5
    assert Sign.VIRGO == 6
    assert Sign.LIBRA == 7
    assert Sign.SCORPIO == 8
    assert Sign.SAGITTARIUS == 9
    assert Sign.CAPRICORN == 10
    assert Sign.AQUARIUS == 11
    assert Sign.PISCES == 12


def test_planet_enum_values():
    """All 9 Vedic planets are present."""
    assert len(Planet) == 9
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    actual = {p.value for p in Planet}
    assert actual == expected


def test_sign_lord_completeness():
    """SIGN_LORD maps all 12 signs to their ruling planet."""
    assert len(SIGN_LORD) == 12
    for sign in Sign:
        assert sign in SIGN_LORD, f"Missing lord for {sign.name}"
        assert isinstance(SIGN_LORD[sign], Planet)
    # Spot checks
    assert SIGN_LORD[Sign.ARIES] == Planet.MARS
    assert SIGN_LORD[Sign.LEO] == Planet.SUN
    assert SIGN_LORD[Sign.PISCES] == Planet.JUPITER


def test_sign_to_house_and_house_to_sign_round_trip():
    """sign_to_house and house_to_sign are inverses of each other."""
    for asc in Sign:
        for sign in Sign:
            house = sign_to_house(sign, asc)
            assert 1 <= house <= 12
            reconstructed = house_to_sign(house, asc)
            assert reconstructed == sign, (
                f"Round-trip failed: asc={asc.name}, sign={sign.name}, "
                f"house={house}, got={reconstructed.name}"
            )


def test_get_kendras_returns_four_houses():
    """get_kendras returns exactly 4 kendra houses."""
    kendras = get_kendras(1)
    assert len(kendras) == 4
    assert kendras == [1, 4, 7, 10]
    # From a non-1 base
    kendras_5 = get_kendras(5)
    assert len(kendras_5) == 4
    assert kendras_5 == [5, 8, 11, 2]


def test_get_trikonas_returns_three_houses():
    """get_trikonas returns exactly 3 trikona houses."""
    trikonas = get_trikonas(1)
    assert len(trikonas) == 3
    assert trikonas == [1, 5, 9]
    # From a non-1 base
    trikonas_3 = get_trikonas(3)
    assert len(trikonas_3) == 3
    assert trikonas_3 == [3, 7, 11]


def test_get_nakshatra_index_at_boundaries():
    """Nakshatra index correctly handles boundary values."""
    # Start of first nakshatra
    assert get_nakshatra_index(0) == 0
    # Last arcsec of first nakshatra
    assert get_nakshatra_index(47999) == 0
    # First arcsec of second nakshatra
    assert get_nakshatra_index(48000) == 1
    # Last nakshatra (index 26)
    assert get_nakshatra_index(1295999) == 26


def test_get_pada_returns_one_to_four():
    """get_pada returns pada 1-4 within each nakshatra."""
    assert get_pada(0) == 1
    assert get_pada(11999) == 1
    assert get_pada(12000) == 2
    assert get_pada(23999) == 2
    assert get_pada(24000) == 3
    assert get_pada(35999) == 3
    assert get_pada(36000) == 4
    assert get_pada(47999) == 4
