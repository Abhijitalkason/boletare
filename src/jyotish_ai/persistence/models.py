"""
Jyotish AI — SQLAlchemy 2.0 ORM Models

Persistence layer for users, birth charts, predictions, life events,
and weekly engagement records.

All JSON columns store pre-serialised dicts/lists produced by the domain
layer so that the DB acts as a dumb store — no ORM-level parsing.
"""

from __future__ import annotations

from datetime import date, time, datetime
from typing import Optional, Any

from sqlalchemy import (
    String,
    Float,
    Integer,
    Date,
    Time,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ──────────────────────────────────────────────────────────────────
# Declarative Base
# ──────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Shared declarative base for every Jyotish-AI table."""
    pass


# ──────────────────────────────────────────────────────────────────
# User
# ──────────────────────────────────────────────────────────────────

class User(Base):
    """A person whose horoscope is being analysed.

    Stores immutable birth data alongside optional demographic fields
    collected during onboarding.
    """

    __tablename__ = "users"

    # --- Primary key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Auth credentials ---
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True,
        comment="Login email address (unique)"
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="bcrypt-hashed password"
    )

    # --- Birth data (immutable after creation) ---
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    birth_place: Mapped[str] = mapped_column(String(300), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timezone_offset: Mapped[float] = mapped_column(Float, nullable=False)
    birth_time_tier: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1=hospital cert, 2=family memory, 3=rough estimate"
    )

    # --- Optional demographics ---
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    education: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    income_bracket: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # --- Delivery / WhatsApp ---
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="E.164 format, e.g. +919876543210"
    )
    delivery_preference: Mapped[str] = mapped_column(
        String(20), nullable=False, default="api",
        comment="api or whatsapp",
    )
    whatsapp_opted_in: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="User has explicitly opted in for WhatsApp delivery",
    )

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    birth_charts: Mapped[list[BirthChartRecord]] = relationship(
        "BirthChartRecord", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    predictions: Mapped[list[Prediction]] = relationship(
        "Prediction", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    events: Mapped[list[Event]] = relationship(
        "Event", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r}>"


# ──────────────────────────────────────────────────────────────────
# Birth Chart Record
# ──────────────────────────────────────────────────────────────────

class BirthChartRecord(Base):
    """Snapshot of a computed birth chart persisted for audit and reuse.

    All positional data is stored as JSON blobs so the schema does not
    need to change when we add new computed fields.
    """

    __tablename__ = "birth_charts"

    # --- Primary key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Foreign key ---
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Chart metadata ---
    ayanamsha_type: Mapped[str] = mapped_column(String(20), nullable=False)
    ascendant_sign: Mapped[str] = mapped_column(String(20), nullable=False)
    ascendant_arcsec: Mapped[int] = mapped_column(Integer, nullable=False)
    lagna_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="standard or chandra"
    )

    # --- Serialised chart data ---
    planets_json: Mapped[Any] = mapped_column(
        JSON, nullable=False, comment="List of planet position dicts"
    )
    houses_json: Mapped[Any] = mapped_column(
        JSON, nullable=False, comment="List of house cusp dicts"
    )
    dasha_json: Mapped[Any] = mapped_column(
        JSON, nullable=False, comment="Dasha tree serialised"
    )
    ashtakavarga_json: Mapped[Any] = mapped_column(
        JSON, nullable=False, comment="Ashtakavarga points"
    )
    navamsha_json: Mapped[Any] = mapped_column(
        JSON, nullable=False, comment="Navamsha divisional chart"
    )
    quality_flags_json: Mapped[Any] = mapped_column(
        JSON, nullable=False, comment="Combustion, retrogression, etc."
    )

    # --- Timestamp ---
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # --- Relationship ---
    user: Mapped[User] = relationship("User", back_populates="birth_charts")

    def __repr__(self) -> str:
        return (
            f"<BirthChartRecord id={self.id} user_id={self.user_id} "
            f"asc={self.ascendant_sign}>"
        )


# ──────────────────────────────────────────────────────────────────
# Prediction
# ──────────────────────────────────────────────────────────────────

class Prediction(Base):
    """Result of running the three-gate convergence engine for one
    (user, event_type, query_date) tuple.

    Stores the individual gate scores, combined convergence, and
    optional detail blobs that the narration layer can consume.
    """

    __tablename__ = "predictions"

    # --- Primary key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Foreign key ---
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Core prediction fields ---
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    query_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Gate scores ---
    gate1_score: Mapped[float] = mapped_column(Float, nullable=False)
    gate2_score: Mapped[float] = mapped_column(Float, nullable=False)
    gate3_score: Mapped[float] = mapped_column(Float, nullable=False)
    convergence_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)

    # --- Optional detail blobs ---
    quality_flags_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    feature_vector_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    timeline_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    narration_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gate1_details_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    gate2_details_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    gate3_details_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # --- Flags ---
    is_retrospective: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Timestamp ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # --- Relationship ---
    user: Mapped[User] = relationship("User", back_populates="predictions")

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} user={self.user_id} "
            f"event={self.event_type} confidence={self.confidence_level}>"
        )


# ──────────────────────────────────────────────────────────────────
# Event (ground-truth label)
# ──────────────────────────────────────────────────────────────────

class Event(Base):
    """A real-world life event reported by the user.

    Used as ground-truth labels for calibration and retrospective
    validation of predictions.
    """

    __tablename__ = "events"

    # --- Primary key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Foreign key ---
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Event data ---
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    reported_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    is_retrospective: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    label_smoothed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # --- Relationship ---
    user: Mapped[User] = relationship("User", back_populates="events")

    def __repr__(self) -> str:
        return (
            f"<Event id={self.id} user={self.user_id} "
            f"type={self.event_type} date={self.event_date}>"
        )


# ──────────────────────────────────────────────────────────────────
# Engagement Record
# ──────────────────────────────────────────────────────────────────

class EngagementRecord(Base):
    """Weekly lagna-based engagement insight generated by the LLM.

    One row per (lagna_sign, week_start) pair.  ``delivery_count``
    tracks how many users have been sent this insight so far.
    """

    __tablename__ = "engagements"

    # --- Primary key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Content fields ---
    lagna_sign: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    insight_text: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Timestamp ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<EngagementRecord id={self.id} sign={self.lagna_sign} "
            f"week={self.week_start}>"
        )


# ──────────────────────────────────────────────────────────────────
# Delivery Log
# ──────────────────────────────────────────────────────────────────

class DeliveryLog(Base):
    """Tracks every delivery attempt (WhatsApp, API, etc.).

    One row per delivery attempt. If retried, a new row is created.
    """

    __tablename__ = "delivery_logs"

    # --- Primary key ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Foreign keys ---
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prediction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    engagement_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("engagements.id", ondelete="SET NULL"), nullable=True
    )

    # --- Delivery data ---
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="api, whatsapp"
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    message_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="External message ID from delivery provider"
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_preview: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="First 200 chars of delivered content"
    )

    # --- Timestamp ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DeliveryLog id={self.id} user={self.user_id} "
            f"channel={self.channel} success={self.success}>"
        )
