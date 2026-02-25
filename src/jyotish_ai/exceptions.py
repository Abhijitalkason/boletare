"""
Jyotish AI — Custom Exception Hierarchy

All domain exceptions inherit from JyotishError for uniform API error handling.
"""

from __future__ import annotations


class JyotishError(Exception):
    """Base exception for all Jyotish-AI errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class UserNotFoundError(JyotishError):
    def __init__(self, user_id: int):
        super().__init__(f"User {user_id} not found", "USER_NOT_FOUND")


class ChartComputationError(JyotishError):
    def __init__(self, detail: str):
        super().__init__(f"Chart computation failed: {detail}", "CHART_ERROR")


class InsufficientPromiseError(JyotishError):
    """Not a true error — returned as a valid prediction with INSUFFICIENT level."""

    def __init__(self, score: float):
        super().__init__(
            f"Insufficient planetary promise (score={score:.4f})",
            "INSUFFICIENT_PROMISE",
        )


class PredictionNotFoundError(JyotishError):
    def __init__(self, prediction_id: int):
        super().__init__(f"Prediction {prediction_id} not found", "PREDICTION_NOT_FOUND")


class InvalidBirthDataError(JyotishError):
    def __init__(self, detail: str):
        super().__init__(f"Invalid birth data: {detail}", "INVALID_BIRTH_DATA")


class DeliveryError(JyotishError):
    def __init__(self, channel: str, detail: str):
        super().__init__(f"Delivery via {channel} failed: {detail}", "DELIVERY_ERROR")


class NarrationError(JyotishError):
    def __init__(self, detail: str):
        super().__init__(f"Narration failed: {detail}", "NARRATION_ERROR")
