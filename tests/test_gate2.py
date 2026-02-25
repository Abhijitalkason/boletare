"""
Jyotish AI — Test Gate 2: Dasha Significator Evaluation

Validates the dasha lords' connection scoring to the event house.
"""

from datetime import date

from jyotish_ai.domain.types import EventType
from jyotish_ai.prediction.gate2_dasha import evaluate_dasha


def test_evaluate_dasha_with_sample_chart(sample_chart):
    """Gate 2 returns a valid GateResult for a date within the dasha tree."""
    # Query during Venus Mahadasha / Moon Antardasha (1989-01-01 to 1990-09-01)
    result = evaluate_dasha(sample_chart, EventType.MARRIAGE, date(1989, 6, 15))
    assert result.gate_name == "Gate 2 \u2014 Dasha Significator"
    assert isinstance(result.score, float)
    assert isinstance(result.is_sufficient, bool)


def test_dasha_score_in_range(sample_chart):
    """Gate 2 score should always be in [0.0, 1.0]."""
    result = evaluate_dasha(sample_chart, EventType.MARRIAGE, date(1989, 6, 15))
    assert 0.0 <= result.score <= 1.0


def test_dasha_details_has_lord_keys(sample_chart):
    """Gate 2 details should contain md_lord and ad_lord keys."""
    result = evaluate_dasha(sample_chart, EventType.CAREER, date(1989, 6, 15))
    assert "md_lord" in result.details
    assert "ad_lord" in result.details
    assert "md_score" in result.details
    assert "ad_score" in result.details
    assert "event_house" in result.details
    assert "event_lord" in result.details
