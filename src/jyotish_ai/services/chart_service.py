"""
Jyotish AI — Chart Service

Computes birth charts and caches them in the database.
If a chart already exists for a user, returns the cached version.
"""

from __future__ import annotations

import json
import logging
from datetime import time, datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.domain.types import BirthTimeTier, Sign
from jyotish_ai.domain.models import BirthChart
from jyotish_ai.engine.chart_computer import compute_birth_chart
from jyotish_ai.persistence.models import BirthChartRecord, User
from jyotish_ai.persistence.repositories import ChartRepository

logger = logging.getLogger(__name__)


class ChartService:
    """Handles birth chart computation and caching."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._chart_repo = ChartRepository(session)

    async def get_or_compute_chart(
        self,
        user: User,
        ayanamsha: str = "lahiri",
        force_recompute: bool = False,
    ) -> BirthChart:
        """Get cached chart or compute a new one.

        Args:
            user: User ORM object with birth data
            ayanamsha: Ayanamsha system
            force_recompute: If True, ignore cache

        Returns:
            Computed BirthChart
        """
        # Check cache first
        if not force_recompute:
            cached = await self._chart_repo.get_latest_for_user(user.id)
            if cached and cached.ayanamsha_type == ayanamsha:
                logger.info("Using cached chart for user %d", user.id)
                return self._deserialize_chart(cached)

        # Compute fresh chart
        logger.info("Computing chart for user %d", user.id)

        birth_time_obj = None
        if user.birth_time:
            if isinstance(user.birth_time, time):
                birth_time_obj = user.birth_time
            elif isinstance(user.birth_time, str):
                parts = user.birth_time.split(":")
                birth_time_obj = time(int(parts[0]), int(parts[1]),
                                      int(parts[2]) if len(parts) > 2 else 0)

        tier = BirthTimeTier(user.birth_time_tier) if user.birth_time_tier else BirthTimeTier.TIER_2

        chart = compute_birth_chart(
            birth_date=user.birth_date,
            birth_time=birth_time_obj,
            latitude=user.latitude or 28.6,
            longitude=user.longitude or 77.2,
            tz_offset=user.timezone_offset or 5.5,
            birth_time_tier=tier,
            ayanamsha=ayanamsha,
        )

        # Cache in DB
        await self._cache_chart(user.id, chart, ayanamsha)

        return chart

    async def _cache_chart(self, user_id: int, chart: BirthChart, ayanamsha: str) -> None:
        """Persist computed chart to database."""
        record = BirthChartRecord(
            user_id=user_id,
            ayanamsha_type=ayanamsha,
            ascendant_sign=chart.ascendant_sign.name,
            ascendant_arcsec=chart.ascendant_arcsec,
            lagna_mode=chart.lagna_mode.value,
            planets_json=[p.model_dump(mode="json") for p in chart.planets],
            houses_json=[h.model_dump(mode="json") for h in chart.houses],
            dasha_json=[d.model_dump(mode="json") for d in chart.dasha_tree],
            ashtakavarga_json=chart.ashtakavarga.model_dump(mode="json"),
            navamsha_json=[p.model_dump(mode="json") for p in chart.navamsha_planets],
            quality_flags_json=chart.quality_flags.model_dump(mode="json"),
            computed_at=chart.computed_at,
        )
        await self._chart_repo.create(record)

    def _deserialize_chart(self, record: BirthChartRecord) -> BirthChart:
        """Reconstruct BirthChart from DB record."""
        from jyotish_ai.domain.models import (
            PlanetPosition, HouseCusp, DashaPeriod,
            AshtakavargaTable, BoundaryFlags, QualityFlags,
        )
        from jyotish_ai.domain.types import LagnaMode

        planets = [PlanetPosition(**p) for p in record.planets_json]
        houses = [HouseCusp(**h) for h in record.houses_json]
        dasha_tree = [DashaPeriod(**d) for d in record.dasha_json]
        ashtakavarga = AshtakavargaTable(**record.ashtakavarga_json)
        navamsha = [PlanetPosition(**p) for p in record.navamsha_json]
        quality_flags = QualityFlags(**record.quality_flags_json)

        return BirthChart(
            ascendant_sign=Sign[record.ascendant_sign],
            ascendant_arcsec=record.ascendant_arcsec,
            lagna_mode=LagnaMode(record.lagna_mode),
            planets=planets,
            houses=houses,
            dasha_tree=dasha_tree,
            dasha_tree_alt=None,
            ashtakavarga=ashtakavarga,
            navamsha_planets=navamsha,
            boundary_flags=BoundaryFlags(),
            quality_flags=quality_flags,
            computed_at=record.computed_at,
        )
