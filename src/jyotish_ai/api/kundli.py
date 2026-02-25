"""
Jyotish AI — Free Kundli API

Anonymous kundli computation endpoint. No user account required.
Calls compute_birth_chart() directly (pure function, no DB I/O),
then runs yoga and dosha detection on the result.
"""

from __future__ import annotations

import logging
from datetime import time as dt_time

from fastapi import APIRouter, HTTPException

from jyotish_ai.api.schemas import (
    KundliRequest,
    KundliResponse,
    YogaSchema,
    DoshaSchema,
)
from jyotish_ai.domain.types import BirthTimeTier
from jyotish_ai.engine.chart_computer import compute_birth_chart
from jyotish_ai.engine.yogas import detect_all_yogas
from jyotish_ai.engine.doshas import detect_all_doshas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kundli", tags=["kundli"])


def _parse_birth_time(time_str: str | None) -> dt_time | None:
    """Parse HH:MM or HH:MM:SS string into a datetime.time object."""
    if not time_str:
        return None
    parts = time_str.split(":")
    if len(parts) == 2:
        return dt_time(int(parts[0]), int(parts[1]))
    elif len(parts) == 3:
        return dt_time(int(parts[0]), int(parts[1]), int(parts[2]))
    return None


@router.post("/compute", response_model=KundliResponse)
async def compute_kundli(request: KundliRequest):
    """Compute a full kundli analysis anonymously.

    No user creation, no database persistence. Computes the birth chart
    in-process, then detects yogas and doshas.
    """
    try:
        birth_time = _parse_birth_time(request.birth_time)
        tier = BirthTimeTier(request.birth_time_tier)

        # Call the pure-functional chart computer directly
        chart = compute_birth_chart(
            birth_date=request.birth_date,
            birth_time=birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            tz_offset=request.timezone_offset,
            birth_time_tier=tier,
            ayanamsha=request.ayanamsha,
        )

        # Detect yogas and doshas
        yogas = detect_all_yogas(chart)
        doshas = detect_all_doshas(chart)

        # Serialize chart data (same pattern as charts.py)
        return KundliResponse(
            name=request.name,
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            birth_place=request.birth_place,
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
            yogas=[
                YogaSchema(
                    name=y.name,
                    yoga_type=y.yoga_type,
                    is_present=y.is_present,
                    strength=y.strength,
                    involved_planets=y.involved_planets,
                    description=y.description,
                )
                for y in yogas
            ],
            doshas=[
                DoshaSchema(
                    name=d.name,
                    is_present=d.is_present,
                    severity=d.severity,
                    involved_planets=d.involved_planets,
                    affected_houses=d.affected_houses,
                    description=d.description,
                    cancellation_factors=d.cancellation_factors,
                )
                for d in doshas
            ],
        )
    except Exception as e:
        logger.exception("Kundli computation failed")
        raise HTTPException(status_code=500, detail=f"Chart computation failed: {e}")
