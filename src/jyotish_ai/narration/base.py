"""
Jyotish AI — Layer 3: Narrator Base Interface

LLM QUARANTINE: The narrator NEVER computes or predicts.
It receives ONLY pre-computed numbers and generates human-readable text.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from jyotish_ai.domain.types import EventType, ConfidenceLevel
from jyotish_ai.domain.models import GateResult, QualityFlags, TransitWindow


class NarratorBase(ABC):
    """Abstract base for all narrators."""

    @abstractmethod
    async def narrate(
        self,
        event_type: EventType,
        confidence_level: ConfidenceLevel,
        convergence_score: float,
        gate1: GateResult,
        gate2: GateResult,
        gate3: GateResult,
        quality_flags: QualityFlags,
        peak_month: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """Generate narrative text from pre-computed prediction data.

        IMPORTANT: This method receives ONLY numbers and enums.
        It must NEVER compute any astrological values.
        """
        ...


def create_narrator(api_key: Optional[str] = None) -> NarratorBase:
    """Factory function: returns ClaudeNarrator if API key present, else MockNarrator."""
    if api_key:
        from jyotish_ai.narration.claude_narrator import ClaudeNarrator
        return ClaudeNarrator(api_key=api_key)
    from jyotish_ai.narration.mock_narrator import MockNarrator
    return MockNarrator()
