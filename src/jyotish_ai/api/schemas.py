"""
Jyotish AI — API Schemas (Request/Response)

Pydantic v2 models for API serialization. These are separate from
domain models to decouple the API contract from internal representation.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional, Union

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """User registration via email/password."""
    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Valid email address",
    )
    password: str = Field(min_length=6, max_length=128, description="At least 6 characters")
    name: str = Field(min_length=1, max_length=200)
    birth_date: date
    birth_time: Optional[str] = Field(
        default=None,
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Birth time in HH:MM or HH:MM:SS format",
    )
    birth_place: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    timezone_offset: Optional[float] = Field(default=5.5)
    birth_time_tier: int = Field(default=2, ge=1, le=3)
    phone_number: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[1-9]\d{1,14}$",
    )
    delivery_preference: str = Field(default="api", pattern=r"^(api|whatsapp)$")


class LoginRequest(BaseModel):
    """User login via email/password."""
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    name: str


class AuthUserResponse(BaseModel):
    """Authenticated user profile (returned by /me)."""
    id: int
    email: Optional[str] = None
    name: str
    birth_date: date
    birth_time: Optional[Union[str, time]] = None
    birth_place: Optional[str] = None
    phone_number: Optional[str] = None
    delivery_preference: Optional[str] = None
    whatsapp_opted_in: Optional[bool] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── User ─────────────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    birth_date: date
    birth_time: Optional[str] = Field(
        default=None,
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Birth time in HH:MM or HH:MM:SS format",
    )
    birth_place: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    timezone_offset: Optional[float] = Field(default=5.5, description="UTC offset in hours")
    birth_time_tier: int = Field(default=2, ge=1, le=3, description="1=hospital, 2=family, 3=estimate")
    gender: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=150)
    education: Optional[str] = None
    income: Optional[str] = None
    marital_status: Optional[str] = None
    phone_number: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[1-9]\d{1,14}$",
        description="E.164 phone number, e.g. +919876543210",
    )
    delivery_preference: str = Field(
        default="api",
        pattern=r"^(api|whatsapp)$",
        description="Delivery channel: api or whatsapp",
    )


class UserResponse(BaseModel):
    id: int
    name: str
    birth_date: date
    birth_time: Optional[Union[str, time]] = None
    birth_place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone_offset: Optional[float] = None
    birth_time_tier: Optional[int] = None
    phone_number: Optional[str] = None
    delivery_preference: Optional[str] = None
    whatsapp_opted_in: Optional[bool] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserPhoneUpdate(BaseModel):
    """Update phone number and opt into WhatsApp delivery."""
    phone_number: str = Field(
        pattern=r"^\+?[1-9]\d{1,14}$",
        description="E.164 phone number, e.g. +919876543210",
    )
    opt_in_whatsapp: bool = Field(default=True)


# ── Prediction ───────────────────────────────────────────────
class PredictionRequest(BaseModel):
    user_id: int
    event_type: str = Field(description="One of: marriage, career, child, property, health")
    query_date: Optional[date] = Field(default=None, description="Default: today")
    is_retrospective: bool = False
    ayanamsha: str = Field(default="lahiri", description="lahiri or kp")


class GateScoreSchema(BaseModel):
    gate_name: str
    score: float
    is_sufficient: bool
    details: dict = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    id: Optional[int] = None
    user_id: int
    event_type: str
    query_date: date
    gate1: GateScoreSchema
    gate2: GateScoreSchema
    gate3: GateScoreSchema
    convergence_score: float
    confidence_level: str
    quality_flags: dict = Field(default_factory=dict)
    peak_month: Optional[str] = None
    feature_vector: list[float] = Field(default_factory=list)
    narration_text: Optional[str] = None
    is_retrospective: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PredictionListItem(BaseModel):
    id: int
    event_type: str
    query_date: date
    convergence_score: float
    confidence_level: str
    is_retrospective: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Event ────────────────────────────────────────────────────
class EventCreate(BaseModel):
    user_id: int
    event_type: str = Field(description="One of: marriage, career, child, property, health")
    event_date: date
    is_retrospective: bool = True


class EventResponse(BaseModel):
    id: int
    user_id: int
    event_type: str
    event_date: date
    reported_date: Optional[date] = None
    is_retrospective: bool
    label_smoothed: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Chart ────────────────────────────────────────────────────
class ChartResponse(BaseModel):
    ascendant_sign: str
    ascendant_arcsec: int
    lagna_mode: str
    planets: list[dict]
    houses: list[dict]
    dasha_tree: list[dict]
    ashtakavarga: dict
    navamsha_planets: list[dict]
    quality_flags: dict
    computed_at: datetime


# ── Health ───────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    environment: str = "dev"
    database: str = "connected"


# ── Engagement ───────────────────────────────────────────────
class EngagementResponse(BaseModel):
    week_start: str
    insights: dict[str, str] = Field(description="sign_name -> insight_text")


# ── Delivery ────────────────────────────────────────────────
class DeliverPredictionRequest(BaseModel):
    """Manually trigger delivery of a prediction to the user."""
    channel: Optional[str] = Field(
        default=None,
        description="Override channel (api or whatsapp). Default: user's preference.",
    )


class DeliveryLogResponse(BaseModel):
    id: int
    user_id: int
    prediction_id: Optional[int] = None
    engagement_id: Optional[int] = None
    channel: str
    phone_number: Optional[str] = None
    message_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeliveryStatusResponse(BaseModel):
    prediction_id: int
    deliveries: list[DeliveryLogResponse]
    latest_success: bool


# ── WhatsApp Onboarding ──────────────────────────────────────
class WhatsAppOnboardingEvent(BaseModel):
    """A retrospective life event reported during WhatsApp onboarding."""
    event_type: str = Field(description="marriage, career, child, property, health")
    event_date: date = Field(description="Approximate month/year of the event")


class WhatsAppOnboardingRequest(BaseModel):
    """WhatsApp onboarding payload — batch of retrospective events."""
    user_id: int
    events: list[WhatsAppOnboardingEvent] = Field(
        min_length=0,
        max_length=10,
        description="Past life events from the last 5 years",
    )


# ── Kundli (Free Chart Analysis) ─────────────────────────────────
class KundliRequest(BaseModel):
    """Anonymous kundli computation — no user account needed."""
    name: str = Field(min_length=1, max_length=200)
    birth_date: date
    birth_time: Optional[str] = Field(
        default=None,
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Birth time in HH:MM or HH:MM:SS format",
    )
    birth_place: Optional[str] = None
    latitude: float = Field(default=28.6, ge=-90, le=90)
    longitude: float = Field(default=77.2, ge=-180, le=180)
    timezone_offset: float = Field(default=5.5)
    birth_time_tier: int = Field(default=2, ge=1, le=3)
    ayanamsha: str = Field(default="lahiri", pattern=r"^(lahiri|kp)$")


class YogaSchema(BaseModel):
    """A yoga (planetary combination) in the kundli response."""
    name: str
    yoga_type: str
    is_present: bool
    strength: float
    involved_planets: list[str]
    description: str


class DoshaSchema(BaseModel):
    """A dosha (affliction) in the kundli response."""
    name: str
    is_present: bool
    severity: str
    involved_planets: list[str]
    affected_houses: list[int]
    description: str
    cancellation_factors: list[str]


class KundliResponse(BaseModel):
    """Complete kundli analysis — chart + yogas + doshas."""
    name: str
    birth_date: date
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None
    ascendant_sign: str
    ascendant_arcsec: int
    lagna_mode: str
    planets: list[dict]
    houses: list[dict]
    dasha_tree: list[dict]
    ashtakavarga: dict
    navamsha_planets: list[dict]
    quality_flags: dict
    computed_at: datetime
    yogas: list[YogaSchema]
    doshas: list[DoshaSchema]
