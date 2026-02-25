"""
Jyotish AI — Test Navamsha (D-9) Computation

Validates the navamsha sign derivation and full navamsha chart computation.
"""

from jyotish_ai.domain.types import Planet, Sign, ARCSEC_PER_SIGN
from jyotish_ai.engine.navamsha import _navamsha_sign, compute_navamsha


def test_navamsha_sign_aries_0_degrees():
    """Aries 0 degrees: fire sign, navamsha starts from Aries. Division 0 -> Aries."""
    # Aries 0 degrees = 0 arcsec
    result = _navamsha_sign(0)
    assert result == Sign.ARIES


def test_navamsha_sign_taurus_0_degrees():
    """Taurus 0 degrees: earth sign, navamsha starts from Capricorn. Division 0 -> Capricorn."""
    # Taurus 0 degrees = 108000 arcsec
    result = _navamsha_sign(108000)
    assert result == Sign.CAPRICORN


def test_compute_navamsha_returns_9_planets(sample_planets):
    """compute_navamsha returns exactly 9 planet positions (one per Vedic planet)."""
    nav_planets = compute_navamsha(sample_planets)
    assert len(nav_planets) == 9
    # All 9 planets should be represented
    planet_names = {pp.planet for pp in nav_planets}
    assert planet_names == {p for p in Planet}


def test_navamsha_signs_are_valid(sample_planets):
    """Every navamsha position should have a valid Sign (1-12)."""
    nav_planets = compute_navamsha(sample_planets)
    for pp in nav_planets:
        assert isinstance(pp.sign, Sign)
        assert 1 <= int(pp.sign) <= 12
        # Longitude should be in valid range
        assert 0 <= pp.longitude_arcsec < 1296000
        # House in navamsha equals sign number
        assert pp.house == int(pp.sign)
