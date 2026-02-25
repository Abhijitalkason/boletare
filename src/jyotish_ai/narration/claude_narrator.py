"""
Jyotish AI — Layer 3: Claude API Narrator

Real narration using Claude Sonnet. Activated when ANTHROPIC_API_KEY is present.
Falls back to MockNarrator on API failure.

LLM QUARANTINE: Receives ONLY pre-computed numbers. Never computes astrology.
Cost: ~$0.005/prediction.
"""

from __future__ import annotations

import logging
from typing import Optional

from jyotish_ai.domain.types import EventType, ConfidenceLevel
from jyotish_ai.domain.models import GateResult, QualityFlags
from jyotish_ai.narration.base import NarratorBase

logger = logging.getLogger(__name__)


class ClaudeNarrator(NarratorBase):
    """Narrator using Claude Sonnet API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._api_key = api_key
        self._model = model

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
        """Generate narrative using Claude API.

        Falls back to MockNarrator on any API error.
        """
        prompt = self._build_prompt(
            event_type, confidence_level, convergence_score,
            gate1, gate2, gate3, quality_flags, peak_month, language,
        )

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self._api_key)
            response = await client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.warning("Claude API narration failed (%s), falling back to mock", e)
            from jyotish_ai.narration.mock_narrator import MockNarrator
            fallback = MockNarrator()
            return await fallback.narrate(
                event_type, confidence_level, convergence_score,
                gate1, gate2, gate3, quality_flags, peak_month, language,
            )

    def _build_prompt(
        self,
        event_type: EventType,
        confidence_level: ConfidenceLevel,
        convergence_score: float,
        gate1: GateResult,
        gate2: GateResult,
        gate3: GateResult,
        quality_flags: QualityFlags,
        peak_month: Optional[str],
        language: str,
    ) -> str:
        lang_instruction = "Respond in Hindi." if language == "hi" else "Respond in English."

        return f"""You are a Vedic astrology narrator. Your job is to explain pre-computed
prediction results in clear, empathetic language.

CRITICAL: You must NEVER compute any astrological values. All numbers below are
pre-computed by the deterministic engine. Simply narrate them.

{lang_instruction}

## Prediction Data

Event Type: {event_type.value}
Confidence Level: {confidence_level.value}
Convergence Score: {convergence_score:.2f} / 3.00

### Gate 1 — Birth Chart Promise
Score: {gate1.score:.2f}
House Lord Dignity: {gate1.details.get('lord_dignity', 'N/A')}
Event Lord: {gate1.details.get('event_lord', 'N/A')}
SAV Score: {gate1.details.get('sav_raw', 'N/A')}

### Gate 2 — Dasha Period
Score: {gate2.score:.2f}
Mahadasha Lord: {gate2.details.get('md_lord', 'N/A')}
Antardasha Lord: {gate2.details.get('ad_lord', 'N/A')}

### Gate 3 — Double Transit
Score: {gate3.score:.2f}
Active Transit Months: {gate3.details.get('active_months_count', 0)}
Peak Month: {peak_month or 'None identified'}

### Quality Notes
Birth Time Tier: {quality_flags.birth_time_tier.value}
Lagna Mode: {quality_flags.lagna_mode.value}
Retrospective: {quality_flags.is_retrospective}

## Instructions
Write 2-3 paragraphs:
1. Summarize the birth chart promise (Gate 1) — is the chart favorable for this event?
2. Describe the timing assessment (Gates 2 & 3) — are current planetary periods supportive?
3. If there are transit windows, mention when conditions are most favorable.

Use a warm, professional tone. Mention confidence level. If quality flags indicate
uncertainty (Tier 3, Chandra lagna), add a brief caveat.
Do NOT use technical jargon without explanation. Keep it accessible."""
