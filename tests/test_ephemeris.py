"""
Jyotish AI — Test Ephemeris Module

Validates the core conversion functions and Swiss Ephemeris adapter
from jyotish_ai.engine.ephemeris.
"""

from datetime import date, time

from jyotish_ai.domain.types import (
    Planet, Sign,
    ARCSEC_PER_SIGN, ARCSEC_FULL_CIRCLE,
)
from jyotish_ai.engine.ephemeris import (
    deg_to_arcsec,
    arcsec_to_sign,
    arcsec_in_sign,
    date_to_jd,
    get_planet_longitude,
)


def test_deg_to_arcsec_basic_conversions():
    """deg_to_arcsec converts degrees to arc-seconds correctly."""
    # 0 degrees -> 0 arcsec
    assert deg_to_arcsec(0.0) == 0
    # 30 degrees -> 108000 arcsec (one sign)
    assert deg_to_arcsec(30.0) == ARCSEC_PER_SIGN
    # 360 degrees wraps to 0 (full circle mod)
    assert deg_to_arcsec(360.0) == 0
    # 1 degree -> 3600 arcsec
    assert deg_to_arcsec(1.0) == 3600


def test_arcsec_to_sign_mapping():
    """arcsec_to_sign returns the correct zodiac sign for arc-second positions."""
    # Start of Aries
    assert arcsec_to_sign(0) == Sign.ARIES
    # Start of Taurus
    assert arcsec_to_sign(108000) == Sign.TAURUS
    # End of Aries (just before Taurus)
    assert arcsec_to_sign(107999) == Sign.ARIES
    # Start of Pisces
    assert arcsec_to_sign(1188000) == Sign.PISCES
    # End of zodiac
    assert arcsec_to_sign(1295999) == Sign.PISCES


def test_arcsec_in_sign_offset():
    """arcsec_in_sign returns arc-seconds elapsed within the current sign."""
    # Start of a sign -> 0
    assert arcsec_in_sign(0) == 0
    assert arcsec_in_sign(108000) == 0
    # One arcsec into the second sign
    assert arcsec_in_sign(108001) == 1
    # Mid-sign
    assert arcsec_in_sign(54000) == 54000  # 15 degrees into Aries


def test_date_to_jd_produces_valid_julian_day():
    """date_to_jd returns a Julian Day number in the expected range for modern dates."""
    # Jan 15, 1990 should produce a JD > 2440000 (modern era)
    jd = date_to_jd(date(1990, 1, 15), time(9, 30), tz_offset=5.5)
    assert jd > 2440000
    # A known reference: J2000.0 = Jan 1, 2000, 12:00 UT = JD 2451545.0
    jd_2000 = date_to_jd(date(2000, 1, 1), time(17, 30), tz_offset=5.5)
    # 17:30 IST = 12:00 UT
    assert abs(jd_2000 - 2451545.0) < 0.01


def test_get_planet_longitude_valid_range():
    """get_planet_longitude returns arc-seconds in [0, 1296000) and a boolean retrograde flag."""
    jd = date_to_jd(date(1990, 1, 15), time(9, 30), tz_offset=5.5)
    arcsec, is_retro = get_planet_longitude(jd, Planet.SUN)
    assert 0 <= arcsec < ARCSEC_FULL_CIRCLE
    assert isinstance(is_retro, bool)
    # Sun is never retrograde
    assert is_retro is False
