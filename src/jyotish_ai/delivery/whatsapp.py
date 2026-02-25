"""
Jyotish AI — Layer 4: WhatsApp Delivery via OpenClaw

Sends prediction narration as WhatsApp text messages.
Configurable via OPENCLAW_API_KEY and OPENCLAW_PHONE_ID in .env
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from jyotish_ai.delivery.base import DeliveryChannel, DeliveryResult

logger = logging.getLogger(__name__)


class WhatsAppDelivery(DeliveryChannel):
    """WhatsApp delivery via OpenClaw API."""

    def __init__(self, api_key: str, phone_id: str, base_url: str = "https://api.openclaw.com/v1"):
        self._api_key = api_key
        self._phone_id = phone_id
        self._base_url = base_url

    async def deliver(
        self,
        user_id: int,
        prediction_id: int,
        content: str,
        phone_number: Optional[str] = None,
    ) -> DeliveryResult:
        if not phone_number:
            return DeliveryResult(
                success=False,
                channel="whatsapp",
                error="No phone number provided",
            )

        # Format content for WhatsApp (add sections, keep within limits)
        formatted = self._format_message(content, prediction_id)

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": formatted},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._base_url}/{self._phone_id}/messages",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id", "unknown")

                logger.info("WhatsApp message sent: user=%d, prediction=%d, msg_id=%s",
                           user_id, prediction_id, message_id)

                return DeliveryResult(
                    success=True,
                    channel="whatsapp",
                    message_id=message_id,
                    metadata={"phone": phone_number},
                )

        except httpx.HTTPStatusError as e:
            logger.error("WhatsApp API error: %s", e.response.text)
            return DeliveryResult(
                success=False,
                channel="whatsapp",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error("WhatsApp delivery failed: %s", e)
            return DeliveryResult(
                success=False,
                channel="whatsapp",
                error=str(e),
            )

    def _format_message(self, content: str, prediction_id: int) -> str:
        """Format narration for WhatsApp message."""
        header = f"Jyotish AI Prediction #{prediction_id}"
        separator = "-" * 30
        footer = "Powered by Jyotish AI | Vedic Astrology Prediction Engine"

        formatted = f"{header}\n{separator}\n\n{content}\n\n{separator}\n{footer}"

        # WhatsApp message limit is ~4096 chars
        if len(formatted) > 4000:
            formatted = formatted[:3950] + "\n\n[Message truncated]"

        return formatted
