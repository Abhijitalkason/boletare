"""
Jyotish AI — Configuration Management

Single source of truth for all configurable parameters.
Uses pydantic-settings for environment variable loading.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Environment(str, Enum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class Settings(BaseSettings):
    """Application settings loaded from environment variables with JYOTISH_ prefix."""

    environment: Environment = Environment.DEV
    database_url: str = "sqlite+aiosqlite:///./data/jyotish_ai.db"

    # --- Claude API ---
    anthropic_api_key: Optional[str] = None
    narration_model: str = "claude-sonnet-4-20250514"
    narration_max_tokens: int = 1024
    engagement_model: str = "claude-haiku-4-5-20251001"
    engagement_max_tokens: int = 512

    # --- Ayanamsha ---
    ayanamsha: str = "lahiri"  # "lahiri" or "kp"

    # --- Prediction Engine ---
    promise_gate_threshold: float = 0.3
    transit_scan_months: int = 24

    # Convergence weights (Phase 1: hand-coded from expert guidance)
    w1_promise: float = 1.0
    w2_dasha: float = 1.0
    w3_transit: float = 1.0

    # Confidence thresholds (out of max 3.0 for Phase 1)
    threshold_high: float = 2.5
    threshold_medium: float = 1.5
    threshold_low: float = 0.5

    # --- Auth / JWT ---
    jwt_secret_key: str = "jyotish-ai-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # --- OpenClaw WhatsApp ---
    openclaw_api_key: Optional[str] = None
    openclaw_phone_id: Optional[str] = None
    openclaw_webhook_verify_token: Optional[str] = Field(
        default="jyotish-verify-token",
        description="Verification token for WhatsApp webhook handshake",
    )

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "JYOTISH_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
