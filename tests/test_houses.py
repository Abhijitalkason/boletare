"""
Jyotish AI — Test House Computation

Validates house cusp computation, planet-to-house assignment,
distortion detection, and equal house fallback.
"""

from datetime import date, time

from jyotish_ai.domain.types import Sign, ARCSEC_PER_SIGN, ARCSEC_FULL_CIRCLE
from jyotish_ai.domain.models import HouseCusp
from jyotish_ai.engine.ephemeris import date_to_jd
from jyotish_ai.engine.houses import (
    compute_houses,
    compute_equal_houses_from_asc,
    assign_planet_to_house,
    _detect_distortion,
)


def test_compute_houses_returns_12_houses():
    """compute_houses produces exactly 12 house cusps."""
    jd = date_to_jd(date(1990, 1, 15), time(9, 30), tz_offset=5.5)
    # Delhi coordinates
    houses, asc_arcsec, distorted = compute_houses(jd, 28.6139, 77.2090)
    assert len(houses) == 12
    # All house numbers are present
    house_numbers = {h.house_number for h in houses}
    assert house_numbers == set(range(1, 13))
    # Ascendant is in valid range
    assert 0 <= asc_arcsec < ARCSEC_FULL_CIRCLE


def test_assign_planet_to_house_with_equal_houses():
    """assign_planet_to_house correctly places a planet given equal house cusps."""
    # Build equal houses from Aries 0 degrees
    houses = compute_equal_houses_from_asc(0)
    # Planet at 0 arcsec (start of Aries) should be in house 1
    assert assign_planet_to_house(0, houses) == 1
    # Planet at 108000 (start of Taurus) should be in house 2
    assert assign_planet_to_house(108000, houses) == 2
    # Planet at 107999 (end of Aries) should be in house 1
    assert assign_planet_to_house(107999, houses) == 1
    # Planet at 1188000 (start of Pisces) should be in house 12
    assert assign_planet_to_house(1188000, houses) == 12


def test_detect_distortion_extreme_spans():
    """_detect_distortion returns True when a house span exceeds 40 degrees or is below 20 degrees."""
    # Create a house with extreme span (50 degrees)
    distorted_houses = [
        HouseCusp(house_number=1, cusp_arcsec=0, sign=Sign.ARIES, sign_degrees=0.0, span_degrees=50.0),
        HouseCusp(house_number=2, cusp_arcsec=180000, sign=Sign.CANCER, sign_degrees=0.0, span_degrees=20.0),
    ]
    # Pad remaining houses with normal spans
    for i in range(2, 12):
        distorted_houses.append(
            HouseCusp(house_number=i + 1, cusp_arcsec=0, sign=Sign.ARIES, sign_degrees=0.0, span_degrees=30.0)
        )
    assert _detect_distortion(distorted_houses) is True

    # A house with span below 20 degrees should also be distorted
    narrow_houses = [
        HouseCusp(house_number=i + 1, cusp_arcsec=0, sign=Sign.ARIES, sign_degrees=0.0, span_degrees=15.0 if i == 0 else 30.0)
        for i in range(12)
    ]
    assert _detect_distortion(narrow_houses) is True


def test_compute_equal_houses_produces_30_degree_spans():
    """Equal houses should all have exactly 30-degree spans."""
    # Use Aries ascendant at 10 degrees (36000 arcsec)
    asc_arcsec = 36000
    houses = compute_equal_houses_from_asc(asc_arcsec)
    assert len(houses) == 12
    for house in houses:
        assert house.span_degrees == 30.0, (
            f"House {house.house_number} has span {house.span_degrees}, expected 30.0"
        )
    # First house cusp should equal the ascendant
    assert houses[0].cusp_arcsec == asc_arcsec
