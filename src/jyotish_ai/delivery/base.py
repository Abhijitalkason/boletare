"""
Jyotish AI — Layer 4: Delivery Channel Base Interface
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeliveryResult:
    """Result of a delivery attempt."""
    success: bool
    channel: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class DeliveryChannel(ABC):
    """Abstract base for all delivery channels."""

    @abstractmethod
    async def deliver(
        self,
        user_id: int,
        prediction_id: int,
        content: str,
        phone_number: Optional[str] = None,
    ) -> DeliveryResult:
        """Deliver prediction content to the user.

        Args:
            user_id: The recipient user ID
            prediction_id: Associated prediction ID
            content: The narration text to deliver
            phone_number: Phone number (for WhatsApp)
        """
        ...
