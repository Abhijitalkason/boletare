"""
Jyotish AI — Delivery Service

Orchestrates delivery of predictions and engagement insights to users
via the appropriate channel (API or WhatsApp).

Channel selection logic:
  - If user.delivery_preference == "whatsapp" AND user.whatsapp_opted_in
    AND user.phone_number is set AND OpenClaw config present → WhatsApp
  - Otherwise → API (implicit, prediction available via GET endpoint)
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.config import settings
from jyotish_ai.delivery.base import DeliveryChannel, DeliveryResult
from jyotish_ai.delivery.api_delivery import ApiDelivery
from jyotish_ai.delivery.whatsapp import WhatsAppDelivery
from jyotish_ai.persistence.models import User, DeliveryLog
from jyotish_ai.persistence.repositories import DeliveryLogRepository

logger = logging.getLogger(__name__)


class DeliveryService:
    """Selects the right delivery channel and logs every attempt."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._log_repo = DeliveryLogRepository(session)
        self._whatsapp: Optional[WhatsAppDelivery] = None
        self._api = ApiDelivery()

        # Initialise WhatsApp channel if configured
        if settings.openclaw_api_key and settings.openclaw_phone_id:
            self._whatsapp = WhatsAppDelivery(
                api_key=settings.openclaw_api_key,
                phone_id=settings.openclaw_phone_id,
            )

    def _select_channel(
        self,
        user: User,
        override_channel: Optional[str] = None,
    ) -> tuple[DeliveryChannel, str]:
        """Pick the right channel for a user.

        Returns (channel_instance, channel_name).
        """
        channel_name = override_channel or user.delivery_preference

        if (
            channel_name == "whatsapp"
            and user.whatsapp_opted_in
            and user.phone_number
            and self._whatsapp is not None
        ):
            return self._whatsapp, "whatsapp"

        return self._api, "api"

    async def deliver_prediction(
        self,
        user: User,
        prediction_id: int,
        content: str,
        override_channel: Optional[str] = None,
    ) -> DeliveryResult:
        """Deliver a prediction result to a user.

        Selects channel, sends, logs the attempt, returns result.
        """
        channel, channel_name = self._select_channel(user, override_channel)

        logger.info(
            "Delivering prediction %d to user %d via %s",
            prediction_id, user.id, channel_name,
        )

        result = await channel.deliver(
            user_id=user.id,
            prediction_id=prediction_id,
            content=content,
            phone_number=user.phone_number,
        )

        # Log the delivery attempt
        await self._log_delivery(
            user_id=user.id,
            prediction_id=prediction_id,
            engagement_id=None,
            channel=channel_name,
            phone_number=user.phone_number if channel_name == "whatsapp" else None,
            result=result,
            content_preview=content[:200] if content else None,
        )

        if not result.success:
            logger.warning(
                "Delivery failed for prediction %d via %s: %s",
                prediction_id, channel_name, result.error,
            )

        return result

    async def deliver_engagement(
        self,
        user: User,
        engagement_id: int,
        content: str,
    ) -> DeliveryResult:
        """Deliver a weekly engagement insight to a user."""
        channel, channel_name = self._select_channel(user)

        result = await channel.deliver(
            user_id=user.id,
            prediction_id=0,  # Not a prediction
            content=content,
            phone_number=user.phone_number,
        )

        await self._log_delivery(
            user_id=user.id,
            prediction_id=None,
            engagement_id=engagement_id,
            channel=channel_name,
            phone_number=user.phone_number if channel_name == "whatsapp" else None,
            result=result,
            content_preview=content[:200] if content else None,
        )

        return result

    async def _log_delivery(
        self,
        user_id: int,
        prediction_id: Optional[int],
        engagement_id: Optional[int],
        channel: str,
        phone_number: Optional[str],
        result: DeliveryResult,
        content_preview: Optional[str],
    ) -> None:
        """Persist a delivery log record."""
        try:
            log = DeliveryLog(
                user_id=user_id,
                prediction_id=prediction_id,
                engagement_id=engagement_id,
                channel=channel,
                phone_number=phone_number,
                message_id=result.message_id,
                success=result.success,
                error_message=result.error,
                content_preview=content_preview,
            )
            await self._log_repo.create(log)
        except Exception:
            logger.exception("Failed to log delivery (non-fatal)")
