"""
Jyotish AI — Event Service

Records retrospective life events for cold-start data.
Applies label smoothing (±1 month) for imprecise event dates.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.domain.types import EventType
from jyotish_ai.persistence.models import Event
from jyotish_ai.persistence.repositories import EventRepository

logger = logging.getLogger(__name__)


class EventService:
    """Records and manages life events for retrospective validation."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._event_repo = EventRepository(session)

    async def record_event(
        self,
        user_id: int,
        event_type: EventType,
        event_date: date,
        is_retrospective: bool = True,
    ) -> Event:
        """Record a life event.

        Args:
            user_id: The user who experienced the event
            event_type: Type of event
            event_date: When the event occurred
            is_retrospective: True if reported after the fact

        Returns:
            Created Event record
        """
        # Apply label smoothing for retrospective events
        label_smoothed = None
        if is_retrospective:
            label_smoothed = self._compute_label_smoothing(event_date)

        event = Event(
            user_id=user_id,
            event_type=event_type.value,
            event_date=event_date,
            reported_date=date.today(),
            is_retrospective=is_retrospective,
            label_smoothed=label_smoothed,
        )

        created = await self._event_repo.create(event)
        logger.info(
            "Recorded %s event for user %d on %s (retrospective=%s)",
            event_type.value, user_id, event_date, is_retrospective,
        )
        return created

    async def get_user_events(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Event]:
        """Get all events for a user."""
        return await self._event_repo.get_by_user(user_id, offset=offset, limit=limit)

    def _compute_label_smoothing(self, event_date: date) -> float:
        """Compute label smoothing score based on recency of reporting.

        Events reported closer to when they happened get a higher score.
        ±1 month window: score decreases as reporting delay increases.

        Returns:
            Score 0.0-1.0 (1.0 = reported same day, lower = more delay)
        """
        today = date.today()
        days_since = abs((today - event_date).days)

        # Within 30 days → high confidence (0.9-1.0)
        # 30-365 days → moderate (0.6-0.9)
        # > 365 days → lower confidence (0.3-0.6)
        if days_since <= 30:
            return 1.0
        elif days_since <= 365:
            return 0.9 - (days_since - 30) * 0.3 / 335
        else:
            return max(0.3, 0.6 - (days_since - 365) * 0.3 / 3650)
