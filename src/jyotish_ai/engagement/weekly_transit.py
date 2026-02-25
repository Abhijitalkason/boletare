"""
Jyotish AI — Layer 5: Weekly Transit Insights

Batched engagement content: groups users by Lagna sign (12 groups),
generates one "energy theme" insight per group using Claude Haiku.

Anti-bias: insights are framed as "energy themes", NOT predictions.
Cost: ~Rs.1/week total (12 Haiku calls for all users).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from jyotish_ai.domain.types import Planet, Sign
from jyotish_ai.engine.transit import get_transit_positions

logger = logging.getLogger(__name__)

# Energy theme templates (fallback when no API key)
_ENERGY_THEMES: dict[str, str] = {
    "jupiter_kendra": "an expansive and growth-oriented energy",
    "jupiter_trikona": "a period of wisdom and spiritual development",
    "saturn_kendra": "a structured and disciplined energy calling for patience",
    "saturn_trikona": "a period of karmic rewards through steady effort",
    "both_favorable": "a powerful convergence of expansion and discipline",
    "neutral": "a steady period for reflection and inner work",
}


async def generate_weekly_insights(
    week_start: date,
    api_key: Optional[str] = None,
    ayanamsha: str = "lahiri",
) -> dict[str, str]:
    """Generate weekly transit insights for all 12 Lagna signs.

    Args:
        week_start: The Monday of the target week
        api_key: Anthropic API key (if None, uses rule-based templates)
        ayanamsha: Ayanamsha system

    Returns:
        Dict mapping sign name (e.g., "ARIES") to insight text
    """
    # Get current Jupiter and Saturn positions
    positions = get_transit_positions(
        query_date=week_start,
        planets=[Planet.JUPITER, Planet.SATURN],
        ayanamsha=ayanamsha,
    )

    jupiter_arcsec, jupiter_sign = positions[Planet.JUPITER]
    saturn_arcsec, saturn_sign = positions[Planet.SATURN]

    insights: dict[str, str] = {}

    for sign in Sign:
        # Compute house positions relative to this Lagna sign
        jupiter_house = (jupiter_sign - sign) % 12 + 1
        saturn_house = (saturn_sign - sign) % 12 + 1

        if api_key:
            # Use Claude Haiku for richer insights
            insight = await _generate_haiku_insight(
                api_key=api_key,
                lagna_sign=sign,
                jupiter_sign=jupiter_sign,
                jupiter_house=jupiter_house,
                saturn_sign=saturn_sign,
                saturn_house=saturn_house,
                week_start=week_start,
            )
        else:
            # Rule-based fallback
            insight = _generate_template_insight(
                lagna_sign=sign,
                jupiter_house=jupiter_house,
                saturn_house=saturn_house,
                jupiter_sign=jupiter_sign,
                saturn_sign=saturn_sign,
                week_start=week_start,
            )

        insights[sign.name] = insight

    return insights


async def _generate_haiku_insight(
    api_key: str,
    lagna_sign: Sign,
    jupiter_sign: Sign,
    jupiter_house: int,
    saturn_sign: Sign,
    saturn_house: int,
    week_start: date,
) -> str:
    """Generate insight using Claude Haiku API."""
    prompt = f"""You are a Vedic astrology engagement writer. Generate a brief,
warm weekly energy theme (2-3 sentences) for people with {lagna_sign.name} Lagna.

This week's planetary positions (pre-computed, do NOT recalculate):
- Jupiter is in {jupiter_sign.name} (House {jupiter_house} from your Lagna)
- Saturn is in {saturn_sign.name} (House {saturn_house} from your Lagna)
- Week starting: {week_start.isoformat()}

IMPORTANT: Frame this as an "energy theme" or "focus area", NOT as a prediction.
Keep it positive, actionable, and under 100 words."""

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        logger.warning("Haiku insight failed for %s: %s", lagna_sign.name, e)
        return _generate_template_insight(
            lagna_sign, jupiter_house, saturn_house,
            jupiter_sign, saturn_sign, week_start,
        )


def _generate_template_insight(
    lagna_sign: Sign,
    jupiter_house: int,
    saturn_house: int,
    jupiter_sign: Sign,
    saturn_sign: Sign,
    week_start: date,
) -> str:
    """Rule-based template insight (no API needed)."""
    kendras = {1, 4, 7, 10}
    trikonas = {1, 5, 9}
    favorable = kendras | trikonas

    jup_favorable = jupiter_house in favorable
    sat_favorable = saturn_house in favorable

    if jup_favorable and sat_favorable:
        theme = _ENERGY_THEMES["both_favorable"]
    elif jup_favorable:
        key = "jupiter_kendra" if jupiter_house in kendras else "jupiter_trikona"
        theme = _ENERGY_THEMES[key]
    elif sat_favorable:
        key = "saturn_kendra" if saturn_house in kendras else "saturn_trikona"
        theme = _ENERGY_THEMES[key]
    else:
        theme = _ENERGY_THEMES["neutral"]

    return (
        f"Weekly Energy for {lagna_sign.name} (week of {week_start.isoformat()}): "
        f"With Jupiter transiting your {_ordinal(jupiter_house)} house in "
        f"{jupiter_sign.name} and Saturn in your {_ordinal(saturn_house)} house "
        f"in {saturn_sign.name}, this week brings {theme}. "
        f"Focus on areas aligned with these energies for best results."
    )


def _ordinal(n: int) -> str:
    """Return ordinal string for a number (1st, 2nd, etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
