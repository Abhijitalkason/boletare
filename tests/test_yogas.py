"""
Jyotish AI — Test Yoga Detection Engine

Validates that classical Vedic yogas are correctly detected from
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
from jyotish_ai.engine.yogas import detect_all_yogas


# ── Test Helpers ─────────────────────────────────────────────────────

def _make_planet(
    planet: Planet,
    sign: Sign,
    house: int,
    dignity: Dignity = Dignity.NEUTRAL,
    dignity_score: float = 0.35,
    is_retrograde: bool = False,
) -> PlanetPosition:
    """Create a minimal PlanetPosition for testing."""
    return PlanetPosition(
        planet=planet,
        longitude_arcsec=(int(sign) - 1) * 108_000 + 54_000,  # mid-sign
        sign=sign,
        sign_degrees=15.0,
        nakshatra="Ashwini",
        nakshatra_pada=1,
        house=house,
        dignity=dignity,
        dignity_score=dignity_score,
        is_retrograde=is_retrograde,
    )


def _make_chart(
    planets: list[PlanetPosition],
    ascendant_sign: Sign = Sign.ARIES,
) -> BirthChart:
    """Create a minimal BirthChart for testing yoga detection."""
    # Ensure all 9 planets are present
    planet_set = {p.planet for p in planets}
    for req_planet in Planet:
        if req_planet not in planet_set:
            # Place missing planets in sign 6 (Virgo), house 6
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


def _find_yoga(results, name: str):
    """Find a yoga result by name."""
    for y in results:
        if y.name == name:
            return y
    return None


# ── Gajakesari Yoga ─────────────────────────────────────────────────

def test_gajakesari_present():
    """Jupiter in kendra (house 4) from Moon -> Gajakesari detected."""
    # Asc = Aries. Moon in Aries (sign 1, house 1). Jupiter in Cancer (sign 4, house 4).
    planets = [
        _make_planet(Planet.MOON, Sign.ARIES, 1),
        _make_planet(Planet.JUPITER, Sign.CANCER, 4,
                     dignity=Dignity.EXALTED, dignity_score=1.0),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    gk = _find_yoga(results, "Gajakesari Yoga")
    assert gk is not None
    assert gk.is_present is True
    assert gk.strength == 1.0


def test_gajakesari_absent():
    """Jupiter NOT in kendra from Moon -> Gajakesari not detected."""
    # Moon in Aries, Jupiter in Taurus (house 2 from Moon = not kendra)
    planets = [
        _make_planet(Planet.MOON, Sign.ARIES, 1),
        _make_planet(Planet.JUPITER, Sign.TAURUS, 2),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    gk = _find_yoga(results, "Gajakesari Yoga")
    assert gk is not None
    assert gk.is_present is False


# ── Budh-Aditya Yoga ────────────────────────────────────────────────

def test_budh_aditya_present():
    """Sun and Mercury in same sign -> Budh-Aditya detected."""
    planets = [
        _make_planet(Planet.SUN, Sign.LEO, 5,
                     dignity=Dignity.OWN, dignity_score=0.75),
        _make_planet(Planet.MERCURY, Sign.LEO, 5,
                     dignity=Dignity.FRIENDLY, dignity_score=0.5),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    ba = _find_yoga(results, "Budh-Aditya Yoga")
    assert ba is not None
    assert ba.is_present is True
    assert ba.strength == 0.62  # (0.75 + 0.5) / 2 rounded


def test_budh_aditya_absent():
    """Sun and Mercury in different signs -> Budh-Aditya not detected."""
    planets = [
        _make_planet(Planet.SUN, Sign.LEO, 5),
        _make_planet(Planet.MERCURY, Sign.VIRGO, 6),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    ba = _find_yoga(results, "Budh-Aditya Yoga")
    assert ba is not None
    assert ba.is_present is False


# ── Pancha Mahapurusha Yogas ────────────────────────────────────────

def test_hamsa_present():
    """Jupiter exalted in Cancer (kendra house 4 from Aries asc) -> Hamsa."""
    planets = [
        _make_planet(Planet.JUPITER, Sign.CANCER, 4,
                     dignity=Dignity.EXALTED, dignity_score=1.0),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    hamsa = _find_yoga(results, "Hamsa Yoga")
    assert hamsa is not None
    assert hamsa.is_present is True


def test_hamsa_absent_wrong_house():
    """Jupiter exalted but NOT in kendra -> no Hamsa."""
    planets = [
        _make_planet(Planet.JUPITER, Sign.CANCER, 5,  # house 5 = not kendra
                     dignity=Dignity.EXALTED, dignity_score=1.0),
    ]
    chart = _make_chart(planets, Sign.PISCES)  # Cancer is house 5 from Pisces
    results = detect_all_yogas(chart)
    hamsa = _find_yoga(results, "Hamsa Yoga")
    assert hamsa is not None
    assert hamsa.is_present is False


def test_ruchaka_present():
    """Mars in own sign Aries in house 1 (kendra) -> Ruchaka."""
    planets = [
        _make_planet(Planet.MARS, Sign.ARIES, 1,
                     dignity=Dignity.OWN, dignity_score=0.75),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    ruchaka = _find_yoga(results, "Ruchaka Yoga")
    assert ruchaka is not None
    assert ruchaka.is_present is True


# ── Chandra-Mangal Yoga ─────────────────────────────────────────────

def test_chandra_mangal_present():
    """Moon and Mars in same sign -> Chandra-Mangal detected."""
    planets = [
        _make_planet(Planet.MOON, Sign.SCORPIO, 8),
        _make_planet(Planet.MARS, Sign.SCORPIO, 8,
                     dignity=Dignity.OWN, dignity_score=0.75),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    cm = _find_yoga(results, "Chandra-Mangal Yoga")
    assert cm is not None
    assert cm.is_present is True


# ── Raj Yoga ─────────────────────────────────────────────────────────

def test_raj_yoga_present():
    """Lord of 10th (Saturn=Capricorn) conjunct lord of 9th (Jupiter=Sagittarius)
    in same sign -> Raj Yoga.
    Aries asc: house 10 = Capricorn (lord Saturn), house 9 = Sagittarius (lord Jupiter).
    """
    planets = [
        _make_planet(Planet.SATURN, Sign.LIBRA, 7),
        _make_planet(Planet.JUPITER, Sign.LIBRA, 7),
        # Place other kendra/trikona lords in separate signs
        _make_planet(Planet.MOON, Sign.ARIES, 1),
        _make_planet(Planet.SUN, Sign.LEO, 5),
        _make_planet(Planet.MARS, Sign.SCORPIO, 8),
        _make_planet(Planet.VENUS, Sign.TAURUS, 2),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    raj = _find_yoga(results, "Raj Yoga")
    assert raj is not None
    assert raj.is_present is True
    assert "Saturn" in raj.involved_planets or "Jupiter" in raj.involved_planets


def test_raj_yoga_absent():
    """No kendra+trikona lord conjunction -> no Raj Yoga.
    Spread all kendra/trikona lords across different signs.
    """
    planets = [
        _make_planet(Planet.MARS, Sign.ARIES, 1),
        _make_planet(Planet.MOON, Sign.CANCER, 4),
        _make_planet(Planet.VENUS, Sign.LIBRA, 7),
        _make_planet(Planet.SATURN, Sign.CAPRICORN, 10),
        _make_planet(Planet.SUN, Sign.LEO, 5),
        _make_planet(Planet.JUPITER, Sign.SAGITTARIUS, 9),
        _make_planet(Planet.MERCURY, Sign.GEMINI, 3),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    raj = _find_yoga(results, "Raj Yoga")
    assert raj is not None
    assert raj.is_present is False


# ── Viparita Raj Yoga ────────────────────────────────────────────────

def test_viparita_raj_yoga_present():
    """Lord of 6th in 8th house -> Viparita Raj Yoga.
    Aries asc: 6th house = Virgo (lord Mercury). Place Mercury in house 8.
    """
    planets = [
        _make_planet(Planet.MERCURY, Sign.SCORPIO, 8),
    ]
    chart = _make_chart(planets, Sign.ARIES)
    results = detect_all_yogas(chart)
    vry = _find_yoga(results, "Viparita Raj Yoga")
    assert vry is not None
    assert vry.is_present is True
    assert "Mercury" in vry.involved_planets


# ── All yogas returned ──────────────────────────────────────────────

def test_detect_all_returns_10_yogas():
    """detect_all_yogas should always return exactly 10 results."""
    chart = _make_chart([], Sign.ARIES)
    results = detect_all_yogas(chart)
    assert len(results) == 10
    names = {y.name for y in results}
    assert "Gajakesari Yoga" in names
    assert "Raj Yoga" in names
    assert "Viparita Raj Yoga" in names
