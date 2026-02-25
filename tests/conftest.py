"""
Jyotish AI — Test Fixtures

Common fixtures: sample chart data, test database, mock objects.
"""

import pytest
from datetime import date, time, datetime
from jyotish_ai.domain.types import (
    Planet, Sign, EventType, BirthTimeTier, LagnaMode, DashaLevel, Dignity,
    ARCSEC_PER_SIGN, ARCSEC_PER_NAKSHATRA,
)
from jyotish_ai.domain.models import (
    PlanetPosition, HouseCusp, DashaPeriod, BoundaryFlags, QualityFlags,
    AshtakavargaTable, BirthChart, GateResult,
)


@pytest.fixture
def sample_planets():
    """9 planet positions for a test chart (Delhi, Jan 15 1990, 09:30 AM)."""
    return [
        PlanetPosition(planet=Planet.SUN, longitude_arcsec=270000, sign=Sign.CAPRICORN,
                       sign_degrees=18.33, nakshatra="Shravana", nakshatra_pada=3,
                       house=10, dignity=Dignity.ENEMY, dignity_score=0.125, is_retrograde=False),
        PlanetPosition(planet=Planet.MOON, longitude_arcsec=96000, sign=Sign.ARIES,
                       sign_degrees=24.0, nakshatra="Bharani", nakshatra_pada=4,
                       house=1, dignity=Dignity.NEUTRAL, dignity_score=0.25, is_retrograde=False),
        PlanetPosition(planet=Planet.MARS, longitude_arcsec=324000, sign=Sign.PISCES,
                       sign_degrees=0.0, nakshatra="Purva_Bhadrapada", nakshatra_pada=4,
                       house=12, dignity=Dignity.NEUTRAL, dignity_score=0.25, is_retrograde=False),
        PlanetPosition(planet=Planet.MERCURY, longitude_arcsec=252000, sign=Sign.SAGITTARIUS,
                       sign_degrees=24.0, nakshatra="Purva_Ashadha", nakshatra_pada=3,
                       house=9, dignity=Dignity.ENEMY, dignity_score=0.125, is_retrograde=False),
        PlanetPosition(planet=Planet.JUPITER, longitude_arcsec=192000, sign=Sign.GEMINI,
                       sign_degrees=24.0, nakshatra="Punarvasu", nakshatra_pada=2,
                       house=3, dignity=Dignity.ENEMY, dignity_score=0.125, is_retrograde=False),
        PlanetPosition(planet=Planet.VENUS, longitude_arcsec=288000, sign=Sign.AQUARIUS,
                       sign_degrees=0.0, nakshatra="Dhanishta", nakshatra_pada=3,
                       house=11, dignity=Dignity.NEUTRAL, dignity_score=0.25, is_retrograde=False),
        PlanetPosition(planet=Planet.SATURN, longitude_arcsec=288000, sign=Sign.AQUARIUS,
                       sign_degrees=0.0, nakshatra="Dhanishta", nakshatra_pada=3,
                       house=11, dignity=Dignity.OWN, dignity_score=0.75, is_retrograde=False),
        PlanetPosition(planet=Planet.RAHU, longitude_arcsec=180000, sign=Sign.CANCER,
                       sign_degrees=12.0, nakshatra="Pushya", nakshatra_pada=2,
                       house=4, dignity=Dignity.NEUTRAL, dignity_score=0.25, is_retrograde=False),
        PlanetPosition(planet=Planet.KETU, longitude_arcsec=828000, sign=Sign.CAPRICORN,
                       sign_degrees=12.0, nakshatra="Shravana", nakshatra_pada=1,
                       house=10, dignity=Dignity.NEUTRAL, dignity_score=0.25, is_retrograde=False),
    ]


@pytest.fixture
def sample_houses():
    """12 house cusps for the test chart."""
    cusps = []
    asc_arcsec = 72000  # Aries at ~20 degrees
    for i in range(12):
        cusp = (asc_arcsec + i * ARCSEC_PER_SIGN) % 1296000
        sign = Sign((cusp // ARCSEC_PER_SIGN) + 1)
        cusps.append(HouseCusp(
            house_number=i + 1,
            cusp_arcsec=cusp,
            sign=sign,
            sign_degrees=round((cusp % ARCSEC_PER_SIGN) / 3600, 2),
            span_degrees=30.0,
        ))
    return cusps


@pytest.fixture
def sample_dasha_tree():
    """Simple dasha tree for testing."""
    md = DashaPeriod(
        level=DashaLevel.MAHADASHA,
        planet=Planet.VENUS,
        start_date=date(1988, 1, 1),
        end_date=date(2008, 1, 1),
        duration_days=7305.0,
        sub_periods=[
            DashaPeriod(
                level=DashaLevel.ANTARDASHA,
                planet=Planet.SUN,
                start_date=date(1988, 1, 1),
                end_date=date(1989, 1, 1),
                duration_days=365.25,
            ),
            DashaPeriod(
                level=DashaLevel.ANTARDASHA,
                planet=Planet.MOON,
                start_date=date(1989, 1, 1),
                end_date=date(1990, 9, 1),
                duration_days=609.0,
            ),
            DashaPeriod(
                level=DashaLevel.ANTARDASHA,
                planet=Planet.MARS,
                start_date=date(1990, 9, 1),
                end_date=date(1991, 11, 1),
                duration_days=426.0,
            ),
        ],
    )
    return [md]


@pytest.fixture
def sample_ashtakavarga():
    """Sample ashtakavarga table."""
    bav = {}
    sav = {}
    sav_reduced = {}
    for planet in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                   Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
        bav[planet.value] = {s.name: 4 for s in Sign}
    for s in Sign:
        sav[s.name] = 28
        sav_reduced[s.name] = 20
    return AshtakavargaTable(bav=bav, sav=sav, sav_trikona_reduced=sav_reduced)


@pytest.fixture
def sample_chart(sample_planets, sample_houses, sample_dasha_tree, sample_ashtakavarga):
    """Complete birth chart fixture."""
    return BirthChart(
        ascendant_sign=Sign.ARIES,
        ascendant_arcsec=72000,
        lagna_mode=LagnaMode.STANDARD,
        planets=sample_planets,
        houses=sample_houses,
        dasha_tree=sample_dasha_tree,
        dasha_tree_alt=None,
        ashtakavarga=sample_ashtakavarga,
        navamsha_planets=sample_planets,  # simplified for tests
        boundary_flags=BoundaryFlags(),
        quality_flags=QualityFlags(birth_time_tier=BirthTimeTier.TIER_2),
        computed_at=datetime(2024, 1, 1, 12, 0),
    )
