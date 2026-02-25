"""
Jyotish AI — Layer 5: Weekly Engagement Scheduler

APScheduler-based weekly trigger (Sunday 9 AM IST).
Fetches all active users grouped by Lagna sign,
generates weekly insights, delivers via configured channel.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class WeeklyEngagementScheduler:
    """Manages the weekly engagement loop lifecycle."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        ayanamsha: str = "lahiri",
    ):
        self._api_key = api_key
        self._ayanamsha = ayanamsha
        self._scheduler = None

    def start(self) -> None:
        """Start the weekly scheduler (Sunday 9 AM IST = 3:30 AM UTC)."""
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger

            self._scheduler = AsyncIOScheduler()
            self._scheduler.add_job(
                self._run_weekly_engagement,
                trigger=CronTrigger(day_of_week="sun", hour=3, minute=30),
                id="weekly_engagement",
                name="Weekly Transit Engagement",
                replace_existing=True,
            )
            self._scheduler.start()
            logger.info("Weekly engagement scheduler started (Sunday 9 AM IST)")
        except ImportError:
            logger.warning("APScheduler not installed — weekly engagement disabled")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            logger.info("Weekly engagement scheduler stopped")

    async def _run_weekly_engagement(self) -> None:
        """Execute the weekly engagement pipeline."""
        from jyotish_ai.engagement.weekly_transit import generate_weekly_insights

        # Compute the Monday of this week
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        logger.info("Running weekly engagement for week of %s", monday.isoformat())

        try:
            insights = await generate_weekly_insights(
                week_start=monday,
                api_key=self._api_key,
                ayanamsha=self._ayanamsha,
            )

            logger.info(
                "Generated %d sign insights for week of %s",
                len(insights),
                monday.isoformat(),
            )

            # Deliver insights to users grouped by Lagna sign
            await self._deliver_insights(insights)

        except Exception:
            logger.exception("Weekly engagement pipeline failed")

    async def _deliver_insights(self, insights: dict[str, str]) -> None:
        """Deliver generated insights to all WhatsApp-opted-in users by Lagna sign."""
        from jyotish_ai.db import async_session_factory
        from jyotish_ai.persistence.repositories import (
            UserRepository, EngagementRepository,
        )
        from jyotish_ai.persistence.models import EngagementRecord
        from jyotish_ai.services.delivery_service import DeliveryService

        today = date.today()
        monday = today - timedelta(days=today.weekday())

        async with async_session_factory() as session:
            user_repo = UserRepository(session)
            eng_repo = EngagementRepository(session)
            delivery_svc = DeliveryService(session)

            for sign_name, insight_text in insights.items():
                # Persist the engagement record
                eng_record = EngagementRecord(
                    lagna_sign=sign_name,
                    week_start=monday,
                    insight_text=insight_text,
                    delivery_count=0,
                )
                created = await eng_repo.create(eng_record)

                # Load users with this Lagna sign who opted in for WhatsApp
                users = await user_repo.get_all_by_lagna_sign(sign_name)
                delivered = 0
                for user in users:
                    if user.whatsapp_opted_in and user.phone_number:
                        try:
                            result = await delivery_svc.deliver_engagement(
                                user=user,
                                engagement_id=created.id,
                                content=insight_text,
                            )
                            if result.success:
                                delivered += 1
                        except Exception:
                            logger.exception(
                                "Engagement delivery failed for user %d", user.id,
                            )

                created.delivery_count = delivered
                await session.flush()

                logger.info(
                    "Engagement delivered: sign=%s, users=%d, delivered=%d",
                    sign_name, len(users), delivered,
                )

            await session.commit()

    async def run_now(self) -> dict[str, str]:
        """Trigger weekly engagement immediately (for testing/API endpoint).

        Returns:
            Dict of sign_name -> insight_text
        """
        from jyotish_ai.engagement.weekly_transit import generate_weekly_insights

        today = date.today()
        monday = today - timedelta(days=today.weekday())

        return await generate_weekly_insights(
            week_start=monday,
            api_key=self._api_key,
            ayanamsha=self._ayanamsha,
        )
