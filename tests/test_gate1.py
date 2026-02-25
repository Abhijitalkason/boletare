"""
Jyotish AI — Test Gate 1: Birth Chart Promise Analysis

Validates the promise evaluation for life events, including score range,
sufficiency thresholds, and expected detail keys.
"""

from datetime import date, datetime

from jyotish_ai.domain.types import (
    Planet, Sign, EventType, BirthTimeTier, LagnaMode, Dignity, DashaLevel,
    ARCSEC_PER_SIGN,
)
from jyotish_ai.domain.models import (
    PlanetPosition, HouseCusp, DashaPeriod, BoundaryFlags, QualityFlags,
    AshtakavargaTable, BirthChart,
)
from jyotish_ai.prediction.gate1_promise import evaluate_promise


def test_evaluate_promise_marriage(sample_chart):
    """Gate 1 returns a valid GateResult for marriage (house 7) prediction."""
    result = evaluate_promise(sample_chart, EventType.MARRIAGE)
    assert result.gate_name == "gate1_promise"
    assert 0.0 <= result.score <= 1.0
    assert isinstance(result.is_sufficient, bool)


def test_promise_score_in_range(sample_chart):
    """Gate 1 score should always be normalized to [0.0, 1.0] for any event type."""
    for event_type in EventType:
        result = evaluate_promise(sample_chart, event_type)
        assert 0.0 <= result.score <= 1.0, (
            f"Score {result.score} out of range for {event_type.value}"
        )


def test_insufficient_promise_with_low_scores():
    """A chart with very low dignity and SAV scores should produce low/insufficient promise."""
    # Build a deliberately weak chart: all planets debilitated, low SAV
    weak_planets = []
    for i, planet in enumerate(Planet):
        weak_planets.append(PlanetPosition(
            planet=planet,
            longitude_arcsec=i * 108000 % 1296000,
            sign=Sign((i % 12) + 1),
            sign_degrees=0.0,
            nakshatra="Ashwini",
            nakshatra_pada=1,
            house=(i % 12) + 1,
            dignity=Dignity.DEBILITATED,
            dignity_score=0.0,
            is_retrograde=False,
        ))

    weak_houses = []
    for i in range(12):
        cusp = i * ARCSEC_PER_SIGN
        weak_houses.append(HouseCusp(
            house_number=i + 1,
            cusp_arcsec=cusp,
            sign=Sign(i + 1),
            sign_degrees=0.0,
            span_degrees=30.0,
        ))

    # Very low SAV values
    bav = {}
    for p in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
              Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
        bav[p.value] = {s.name: 1 for s in Sign}
    sav = {s.name: 7 for s in Sign}
    sav_reduced = {s.name: 3 for s in Sign}

    weak_chart = BirthChart(
        ascendant_sign=Sign.ARIES,
        ascendant_arcsec=0,
        lagna_mode=LagnaMode.STANDARD,
        planets=weak_planets,
        houses=weak_houses,
        dasha_tree=[DashaPeriod(
            level=DashaLevel.MAHADASHA,
            planet=Planet.KETU,
            start_date=date(1990, 1, 1),
            end_date=date(1997, 1, 1),
            duration_days=2556.75,
        )],
        dasha_tree_alt=None,
        ashtakavarga=AshtakavargaTable(bav=bav, sav=sav, sav_trikona_reduced=sav_reduced),
        navamsha_planets=weak_planets,
        boundary_flags=BoundaryFlags(),
        quality_flags=QualityFlags(birth_time_tier=BirthTimeTier.TIER_3),
        computed_at=datetime(2024, 1, 1, 12, 0),
    )

    result = evaluate_promise(weak_chart, EventType.MARRIAGE)
    # With all dignity=0.0 and very low SAV, score should be low
    assert result.score < 0.3


def test_promise_details_contain_expected_keys(sample_chart):
    """Gate 1 details dict should contain all expected sub-score keys."""
    result = evaluate_promise(sample_chart, EventType.CAREER)
    expected_keys = {
        "event_house", "event_sign", "event_lord",
        "lord_dignity", "occupant_score", "navamsha_score",
        "sav_raw", "sav_normalized",
        "benefics_in_house", "malefics_in_house",
    }
    assert expected_keys.issubset(result.details.keys()), (
        f"Missing keys: {expected_keys - result.details.keys()}"
    )
