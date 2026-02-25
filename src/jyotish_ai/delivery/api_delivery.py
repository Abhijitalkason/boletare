"""
Jyotish AI — Layer 4: API Delivery Channel

Stores prediction result for the React frontend to fetch.
Default delivery channel for web users.
"""

from __future__ import annotations

import logging
from typing import Optional

from jyotish_ai.delivery.base import DeliveryChannel, DeliveryResult

logger = logging.getLogger(__name__)


class ApiDelivery(DeliveryChannel):
    """REST API delivery — predictions are stored in DB and fetched by the frontend."""

    async def deliver(
        self,
        user_id: int,
        prediction_id: int,
        content: str,
        phone_number: Optional[str] = None,
    ) -> DeliveryResult:
        """API delivery is implicit — predictions are already persisted.

        This channel exists to satisfy the delivery interface and provide
        a consistent delivery result for logging/tracking.
        """
        logger.info("API delivery: user=%d, prediction=%d (available via GET endpoint)",
                    user_id, prediction_id)

        return DeliveryResult(
            success=True,
            channel="api",
            message_id=str(prediction_id),
            metadata={
                "user_id": user_id,
                "fetch_url": f"/api/v1/predictions/{prediction_id}",
            },
        )
