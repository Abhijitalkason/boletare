"""Birth chart endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from jyotish_ai.api.schemas import ChartResponse
from jyotish_ai.api.deps import get_chart_service, get_user_repo
from jyotish_ai.services.chart_service import ChartService
from jyotish_ai.persistence.repositories import UserRepository

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("/user/{user_id}", response_model=ChartResponse)
async def get_user_chart(
    user_id: int,
    ayanamsha: str = "lahiri",
    chart_service: ChartService = Depends(get_chart_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Get computed birth chart for a user."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chart = await chart_service.get_or_compute_chart(user=user, ayanamsha=ayanamsha)

    return ChartResponse(
        ascendant_sign=chart.ascendant_sign.name,
        ascendant_arcsec=chart.ascendant_arcsec,
        lagna_mode=chart.lagna_mode.value,
        planets=[p.model_dump(mode="json") for p in chart.planets],
        houses=[h.model_dump(mode="json") for h in chart.houses],
        dasha_tree=[d.model_dump(mode="json") for d in chart.dasha_tree],
        ashtakavarga=chart.ashtakavarga.model_dump(mode="json"),
        navamsha_planets=[p.model_dump(mode="json") for p in chart.navamsha_planets],
        quality_flags=chart.quality_flags.model_dump(mode="json"),
        computed_at=chart.computed_at,
    )
