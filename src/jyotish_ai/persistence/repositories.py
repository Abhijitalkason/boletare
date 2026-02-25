"""
Jyotish AI — Async Repository Layer

Thin data-access classes over SQLAlchemy AsyncSession.  Each repository
owns queries for exactly one model; cross-model orchestration belongs
in the service layer.

Usage (inside an async with block that provides a session)::

    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(42)
"""

from __future__ import annotations

from datetime import date
from typing import TypeVar, Generic, Type, Optional, Sequence

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.persistence.models import (
    Base,
    User,
    BirthChartRecord,
    Prediction,
    Event,
    EngagementRecord,
    DeliveryLog,
)

T = TypeVar("T", bound=Base)


# ──────────────────────────────────────────────────────────────────
# Generic Base Repository
# ──────────────────────────────────────────────────────────────────

class BaseRepository(Generic[T]):
    """Generic async CRUD operations for any SQLAlchemy model.

    Subclasses set ``model`` at the class level so that base methods
    know which table to query.
    """

    model: Type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Return a single row by primary key, or ``None``."""
        return await self.session.get(self.model, entity_id)

    async def create(self, entity: T) -> T:
        """Add a new entity to the session and flush to obtain its id.

        The caller is responsible for committing the transaction
        (typically handled by the session context manager in ``db.py``).
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[T]:
        """Return a paginated list of rows ordered by primary key."""
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, entity: T) -> None:
        """Mark an entity for deletion.

        The actual DELETE fires on the next flush/commit.
        """
        await self.session.delete(entity)
        await self.session.flush()


# ──────────────────────────────────────────────────────────────────
# User Repository
# ──────────────────────────────────────────────────────────────────

class UserRepository(BaseRepository[User]):
    """Data-access methods specific to the ``users`` table."""

    model = User

    async def get_by_email(self, email: str) -> Optional[User]:
        """Lookup by email address (case-insensitive).

        Returns the user or ``None``.
        """
        stmt = select(User).where(User.email.ilike(email)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[User]:
        """Case-insensitive lookup by user name.

        Returns the first match or ``None``.
        """
        stmt = select(User).where(User.name.ilike(name)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all_by_lagna_sign(self, sign: str) -> Sequence[User]:
        """Return every user whose latest birth chart has the given
        ascendant sign.

        This performs a sub-query join against ``birth_charts`` so that
        we filter on the most recently computed chart per user.
        """
        latest_chart = (
            select(
                BirthChartRecord.user_id,
                BirthChartRecord.ascendant_sign,
            )
            .distinct(BirthChartRecord.user_id)
            .order_by(BirthChartRecord.user_id, desc(BirthChartRecord.computed_at))
            .subquery()
        )

        stmt = (
            select(User)
            .join(latest_chart, User.id == latest_chart.c.user_id)
            .where(latest_chart.c.ascendant_sign == sign)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ──────────────────────────────────────────────────────────────────
# Chart Repository
# ──────────────────────────────────────────────────────────────────

class ChartRepository(BaseRepository[BirthChartRecord]):
    """Data-access methods specific to the ``birth_charts`` table."""

    model = BirthChartRecord

    async def get_latest_for_user(self, user_id: int) -> Optional[BirthChartRecord]:
        """Return the most recently computed chart for a user, or ``None``."""
        stmt = (
            select(BirthChartRecord)
            .where(BirthChartRecord.user_id == user_id)
            .order_by(desc(BirthChartRecord.computed_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()


# ──────────────────────────────────────────────────────────────────
# Prediction Repository
# ──────────────────────────────────────────────────────────────────

class PredictionRepository(BaseRepository[Prediction]):
    """Data-access methods specific to the ``predictions`` table."""

    model = Prediction

    async def get_by_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Prediction]:
        """Return all predictions for a user, newest first."""
        stmt = (
            select(Prediction)
            .where(Prediction.user_id == user_id)
            .order_by(desc(Prediction.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user_event(
        self,
        user_id: int,
        event_type: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Prediction]:
        """Return predictions for a specific (user, event_type) pair,
        newest first.
        """
        stmt = (
            select(Prediction)
            .where(
                Prediction.user_id == user_id,
                Prediction.event_type == event_type,
            )
            .order_by(desc(Prediction.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ──────────────────────────────────────────────────────────────────
# Event Repository
# ──────────────────────────────────────────────────────────────────

class EventRepository(BaseRepository[Event]):
    """Data-access methods specific to the ``events`` table."""

    model = Event

    async def get_by_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Event]:
        """Return all events for a user, newest event date first."""
        stmt = (
            select(Event)
            .where(Event.user_id == user_id)
            .order_by(desc(Event.event_date))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_retrospective_events(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Event]:
        """Return only events flagged as retrospective (i.e. reported
        after the fact) for a user, newest first.
        """
        stmt = (
            select(Event)
            .where(
                Event.user_id == user_id,
                Event.is_retrospective.is_(True),
            )
            .order_by(desc(Event.event_date))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ──────────────────────────────────────────────────────────────────
# Engagement Repository
# ──────────────────────────────────────────────────────────────────

class EngagementRepository(BaseRepository[EngagementRecord]):
    """Data-access methods specific to the ``engagements`` table."""

    model = EngagementRecord

    async def get_latest_for_sign(self, sign: str) -> Optional[EngagementRecord]:
        """Return the most recent engagement insight for a lagna sign,
        or ``None`` if none exists.
        """
        stmt = (
            select(EngagementRecord)
            .where(EngagementRecord.lagna_sign == sign)
            .order_by(desc(EngagementRecord.week_start))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_week(
        self,
        week_start: date,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[EngagementRecord]:
        """Return all engagement records for a given ISO week start date."""
        stmt = (
            select(EngagementRecord)
            .where(EngagementRecord.week_start == week_start)
            .order_by(EngagementRecord.lagna_sign)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ──────────────────────────────────────────────────────────────────
# Delivery Log Repository
# ──────────────────────────────────────────────────────────────────

class DeliveryLogRepository(BaseRepository[DeliveryLog]):
    """Data-access methods specific to the ``delivery_logs`` table."""

    model = DeliveryLog

    async def get_by_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[DeliveryLog]:
        """Return delivery logs for a user, newest first."""
        stmt = (
            select(DeliveryLog)
            .where(DeliveryLog.user_id == user_id)
            .order_by(desc(DeliveryLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_prediction(self, prediction_id: int) -> Sequence[DeliveryLog]:
        """Return all delivery attempts for a specific prediction."""
        stmt = (
            select(DeliveryLog)
            .where(DeliveryLog.prediction_id == prediction_id)
            .order_by(desc(DeliveryLog.created_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
