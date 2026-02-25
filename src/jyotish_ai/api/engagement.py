"""Weekly engagement endpoints."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter

from jyotish_ai.api.schemas import EngagementResponse
from jyotish_ai.engagement.weekly_transit import generate_weekly_insights
from jyotish_ai.config import settings

router = APIRouter(prefix="/engagement", tags=["engagement"])


@router.get("/weekly", response_model=EngagementResponse)
async def get_weekly_insights():
    """Get or generate weekly transit insights for all 12 Lagna signs."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    insights = await generate_weekly_insights(
        week_start=monday,
        api_key=settings.anthropic_api_key,
        ayanamsha=settings.ayanamsha,
    )

    return EngagementResponse(
        week_start=monday.isoformat(),
        insights=insights,
    )
