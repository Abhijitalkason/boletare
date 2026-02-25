"""
Jyotish AI — Test Narration Layer

Validates the MockNarrator template-based text generation and the
create_narrator factory function.
"""

import asyncio

from jyotish_ai.domain.types import EventType, ConfidenceLevel, BirthTimeTier
from jyotish_ai.domain.models import GateResult, QualityFlags
from jyotish_ai.narration.mock_narrator import MockNarrator
from jyotish_ai.narration.base import create_narrator


def _make_gate(score: float, details: dict) -> GateResult:
    """Helper to create a GateResult."""
    return GateResult(
        gate_name="test_gate",
        score=score,
        is_sufficient=True,
        details=details,
    )


async def test_mock_narrator_produces_non_empty_text():
    """MockNarrator.narrate should return a non-empty string."""
    narrator = MockNarrator()
    gate1 = _make_gate(0.6, {"event_lord": "Venus", "sav_raw": 28})
    gate2 = _make_gate(0.5, {"md_lord": "Venus", "ad_lord": "Moon"})
    gate3 = _make_gate(0.4, {"active_months_count": 3})
    qf = QualityFlags(birth_time_tier=BirthTimeTier.TIER_2)

    text = await narrator.narrate(
        event_type=EventType.MARRIAGE,
        confidence_level=ConfidenceLevel.MEDIUM,
        convergence_score=1.5,
        gate1=gate1,
        gate2=gate2,
        gate3=gate3,
        quality_flags=qf,
    )
    assert isinstance(text, str)
    assert len(text) > 0


async def test_mock_narrator_includes_event_type_name():
    """MockNarrator output should mention the event type (e.g. 'marriage')."""
    narrator = MockNarrator()
    gate1 = _make_gate(0.6, {"event_lord": "Venus", "sav_raw": 28})
    gate2 = _make_gate(0.5, {"md_lord": "Venus", "ad_lord": "Moon"})
    gate3 = _make_gate(0.4, {"active_months_count": 3})
    qf = QualityFlags(birth_time_tier=BirthTimeTier.TIER_2)

    text = await narrator.narrate(
        event_type=EventType.MARRIAGE,
        confidence_level=ConfidenceLevel.MEDIUM,
        convergence_score=1.5,
        gate1=gate1,
        gate2=gate2,
        gate3=gate3,
        quality_flags=qf,
    )
    assert "marriage" in text.lower()


def test_create_narrator_without_api_key_returns_mock():
    """create_narrator(None) should return a MockNarrator instance."""
    narrator = create_narrator(api_key=None)
    assert isinstance(narrator, MockNarrator)
