"""
Jyotish AI — Layer 3: Mock (Rule-Based) Narrator

Template-based text generation from gate scores + confidence level.
Works offline, zero cost, deterministic output.
Default mode when no ANTHROPIC_API_KEY is configured.
"""

from __future__ import annotations

from typing import Optional

from jyotish_ai.domain.types import EventType, ConfidenceLevel
from jyotish_ai.domain.models import GateResult, QualityFlags
from jyotish_ai.narration.base import NarratorBase


# Score-to-phrase mappings
_PROMISE_PHRASES = {
    "high": "Your birth chart shows strong indications",
    "medium": "Your birth chart shows moderate indications",
    "low": "Your birth chart shows mild indications",
    "weak": "Your birth chart shows limited indications",
}

_TIMING_PHRASES = {
    "high": "The current planetary periods are highly supportive",
    "medium": "The current planetary periods provide moderate support",
    "low": "The current planetary periods offer some support",
    "weak": "The current planetary periods do not strongly support",
}

_CONFIDENCE_PHRASES = {
    ConfidenceLevel.HIGH: "Overall, our analysis shows HIGH confidence",
    ConfidenceLevel.MEDIUM: "Overall, our analysis shows MEDIUM confidence",
    ConfidenceLevel.LOW: "Overall, our analysis shows LOW confidence",
    ConfidenceLevel.NEGATIVE: "Overall, our analysis does not find strong support",
    ConfidenceLevel.INSUFFICIENT: "The birth chart does not show sufficient promise",
}

_EVENT_NAMES = {
    EventType.MARRIAGE: "marriage",
    EventType.CAREER: "career advancement",
    EventType.CHILD: "childbirth",
    EventType.PROPERTY: "property acquisition",
    EventType.HEALTH: "health matters",
}


class MockNarrator(NarratorBase):
    """Rule-based narrator — no API calls, deterministic output."""

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
        event_name = _EVENT_NAMES.get(event_type, event_type.value)

        # Paragraph 1: Promise analysis
        promise_level = _score_to_level(gate1.score)
        promise_phrase = _PROMISE_PHRASES[promise_level]
        event_lord = gate1.details.get("event_lord", "the house lord")
        sav_raw = gate1.details.get("sav_raw", "N/A")
        para1 = (
            f"{promise_phrase} for {event_name}. "
            f"The significator planet ({event_lord}) holds a dignity score of "
            f"{gate1.score:.2f}, and the Sarvashtakavarga score for the relevant "
            f"house is {sav_raw} points."
        )

        # Paragraph 2: Timing assessment
        timing_level = _score_to_level(gate2.score)
        timing_phrase = _TIMING_PHRASES[timing_level]
        md_lord = gate2.details.get("md_lord", "unknown")
        ad_lord = gate2.details.get("ad_lord", "unknown")
        para2 = (
            f"{timing_phrase} for {event_name}. "
            f"You are currently running the {md_lord} Mahadasha and {ad_lord} "
            f"Antardasha period, with a Dasha connection score of {gate2.score:.2f}."
        )

        # Paragraph 3: Transit windows
        active_months = gate3.details.get("active_months_count", 0)
        if active_months > 0 and peak_month:
            para3 = (
                f"Jupiter and Saturn double transit analysis shows {active_months} "
                f"favorable month(s) in the next 24 months. The most favorable "
                f"period peaks around {peak_month}, with a transit score of "
                f"{gate3.score:.2f}."
            )
        else:
            para3 = (
                f"The double transit analysis of Jupiter and Saturn does not show "
                f"strongly favorable windows in the immediate 24-month period "
                f"(transit score: {gate3.score:.2f})."
            )

        # Confidence summary
        conf_phrase = _CONFIDENCE_PHRASES.get(confidence_level, "")
        summary = (
            f"{conf_phrase} in the indication for {event_name} "
            f"(convergence score: {convergence_score:.2f}/3.00)."
        )

        # Quality caveats
        caveats = []
        if quality_flags.birth_time_tier.value >= 3:
            caveats.append(
                "Note: The birth time precision is estimated (Tier 3), which may "
                "affect the accuracy of house-based calculations."
            )
        if quality_flags.lagna_mode.value == "chandra":
            caveats.append(
                "This analysis uses Chandra Lagna (Moon-based houses) due to "
                "birth time uncertainty."
            )
        if quality_flags.is_retrospective:
            caveats.append(
                "This is a retrospective analysis of a past event."
            )

        caveat_text = " ".join(caveats)

        parts = [para1, para2, para3, summary]
        if caveat_text:
            parts.append(caveat_text)

        return "\n\n".join(parts)


def _score_to_level(score: float) -> str:
    """Map a 0-1 score to a qualitative level."""
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    elif score >= 0.2:
        return "low"
    return "weak"
