"""
Jyotish AI — Test Dosha Detection Engine

Validates that classical Vedic doshas are correctly detected from
constructed BirthChart objects with known planet placements.
"""

from datetime import date, datetime

from jyotish_ai.domain.types import (
    Planet, Sign, Dignity, BirthTimeTier, LagnaMode, DashaLevel,
)
from jyotish_ai.domain.models import (
    BirthChart, PlanetPosition, HouseCusp, DashaPeriod,
    BoundaryFlags, QualityFlags, AshtakavargaTable,
)
from jyotish_ai.engine.doshas import detect_all_doshas


# ── Test Helpers ─────────────────────────────────────────────────────

def _make_planet(
    planet: Planet,
    sign: Sign,
    house: int,
    dignity: Dignity = Dignity.NEUTRAL,
    dignity_score: float = 0.35,
    longitude_arcsec: int | None = None,
) -> PlanetPosition:
    """Create a minimal PlanetPosition for testing."""
    if longitude_arcsec is None:
        longitude_arcsec = (int(sign) - 1) * 108_000 + 54_000  # mid-sign
    return PlanetPosition(
        planet=planet,
        longitude_arcsec=longitude_arcsec,
        sign=sign,
        sign_degrees=15.0,
        nakshatra="Ashwini",
        nakshatra_pada=1,
        house=house,
        dignity=dignity,
        dignity_score=dignity_score,
        is_retrograde=False,
    )


def _make_chart(
    planets: list[PlanetPosition],
    ascendant_sign: Sign = Sign.ARIES,
) -> BirthChart:
    """Create a minimal BirthChart for testing dosha detection."""
    planet_set = {p.planet for p in planets}
    for req_planet in Planet:
        if req_planet not in planet_set:
            planets.append(_make_planet(req_planet, Sign.VIRGO, 6))

    houses = [
        HouseCusp(
            house_number=h,
            cusp_arcsec=(int(ascendant_sign) - 1 + h - 1) % 12 * 108_000,
            sign=Sign((int(ascendant_sign) - 1 + h - 1) % 12 + 1),
            sign_degrees=0.0,
            span_degrees=30.0,
        )
        for h in range(1, 13)
    ]

    return BirthChart(
        ascendant_sign=ascendant_sign,
        ascendant_arcsec=(int(ascendant_sign) - 1) * 108_000,
        lagna_mode=LagnaMode.STANDARD,
        planets=planets,
        houses=houses,
        dasha_tree=[
            DashaPeriod(
                level=DashaLevel.MAHADASHA,
                planet=Planet.SUN,
                start_date=date(2020, 1, 1),
                end_date=date(2026, 1, 1),
                duration_days=2192,
            ),
        ],
        dasha_tree_alt=None,
        ashtakavarga=AshtakavargaTable(
            bav={}, sav={}, sav_trikona_reduced={},
        ),
        navamsha_planets=[],
        boundary_flags=BoundaryFlags(),
        quality_flags=QualityFlags(birth_time_tier=BirthTimeTier.TIER_2),
        computed_at=datetime(2025, 1, 1),
    )


def _find_dosha(results, name: str):
    """Find a dosha result by name."""
    for d in results:
        if d.name == name:
            return d
    return None


# ── Mangal Dosha ─────────────────────────────────────────────────────

def test_mangal_dosha_present_house_7():
    """Mars in house 7 -> Mangal Dosha (severe before cancellations)."""
    planets = [
        _make_planet(Planet.MARS, Sign.LIBRA, 7),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_doshas(chart)
    md = _find_dosha(results, "Mangal Dosha")
    assert md is not None
    assert md.is_present is True
    assert md.severity in {"severe", "moderate", "mild"}


def test_mangal_dosha_absent():
    """Mars in house 3 -> no Mangal Dosha."""
    planets = [
        _make_planet(Planet.MARS, Sign.GEMINI, 3),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_doshas(chart)
    md = _find_dosha(results, "Mangal Dosha")
    assert md is not None
    assert md.is_present is False
    assert md.severity == "none"


def test_mangal_dosha_cancelled_by_own_sign():
    """Mars in house 8 but in Scorpio (own sign) -> cancellation reduces severity."""
    planets = [
        _make_planet(Planet.MARS, Sign.SCORPIO, 8,
                     dignity=Dignity.OWN, dignity_score=0.75),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_doshas(chart)
    md = _find_dosha(results, "Mangal Dosha")
    assert md is not None
    # Should have cancellation factor
    assert len(md.cancellation_factors) > 0
    assert any("own sign" in f.lower() for f in md.cancellation_factors)


# ── Kaal Sarp Dosha ─────────────────────────────────────────────────

def test_kaal_sarp_present():
    """All 7 planets between Rahu and Ketu -> Kaal Sarp detected.

    Place Rahu at 0 deg Aries, Ketu at 0 deg Libra (180 apart).
    All other planets in signs between Aries and Libra (forward arc).
    """
    planets = [
        _make_planet(Planet.RAHU, Sign.ARIES, 1, longitude_arcsec=10_000),
        _make_planet(Planet.KETU, Sign.LIBRA, 7, longitude_arcsec=658_000),
        # All 7 planets between Rahu (10000) and Ketu (658000) going forward
        _make_planet(Planet.SUN, Sign.TAURUS, 2, longitude_arcsec=150_000),
        _make_planet(Planet.MOON, Sign.GEMINI, 3, longitude_arcsec=260_000),
        _make_planet(Planet.MARS, Sign.CANCER, 4, longitude_arcsec=370_000),
        _make_planet(Planet.MERCURY, Sign.TAURUS, 2, longitude_arcsec=160_000),
        _make_planet(Planet.JUPITER, Sign.LEO, 5, longitude_arcsec=480_000),
        _make_planet(Planet.VENUS, Sign.GEMINI, 3, longitude_arcsec=270_000),
        _make_planet(Planet.SATURN, Sign.CANCER, 4, longitude_arcsec=380_000),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_doshas(chart)
    ks = _find_dosha(results, "Kaal Sarp Dosha")
    assert ks is not None
    assert ks.is_present is True


def test_kaal_sarp_absent():
    """Planets on BOTH sides of Rahu-Ketu -> no Kaal Sarp."""
    planets = [
        _make_planet(Planet.RAHU, Sign.ARIES, 1, longitude_arcsec=10_000),
        _make_planet(Planet.KETU, Sign.LIBRA, 7, longitude_arcsec=658_000),
        # Some planets on one side, some on the other
        _make_planet(Planet.SUN, Sign.TAURUS, 2, longitude_arcsec=150_000),
        _make_planet(Planet.MOON, Sign.SCORPIO, 8, longitude_arcsec=800_000),  # other side
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_doshas(chart)
    ks = _find_dosha(results, "Kaal Sarp Dosha")
    assert ks is not None
    assert ks.is_present is False


# ── Pitra Dosha ──────────────────────────────────────────────────────

def test_pitra_dosha_sun_rahu_conjunct():
    """Sun and Rahu in same sign -> Pitra Dosha detected."""
    planets = [
        _make_planet(Planet.SUN, Sign.LEO, 5),
        _make_planet(Planet.RAHU, Sign.LEO, 5),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_doshas(chart)
    pd = _find_dosha(results, "Pitra Dosha")
    assert pd is not None
    assert pd.is_present is True


def test_pitra_dosha_absent():
    """Sun and Rahu in different signs, Sun not in 9th -> no Pitra Dosha."""
    planets = [
        _make_planet(Planet.SUN, Sign.LEO, 5),
        _make_planet(Planet.RAHU, Sign.SCORPIO, 8),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_doshas(chart)
    pd = _find_dosha(results, "Pitra Dosha")
    assert pd is not None
    assert pd.is_present is False


# ── All doshas returned ─────────────────────────────────────────────

def test_detect_all_returns_3_doshas():
    """detect_all_doshas should always return exactly 3 results."""
    chart = _make_chart([], Sign.ARIES)
    results = detect_all_doshas(chart)
    assert len(results) == 3
    names = {d.name for d in results}
    assert "Mangal Dosha" in names
    assert "Kaal Sarp Dosha" in names
    assert "Pitra Dosha" in names
