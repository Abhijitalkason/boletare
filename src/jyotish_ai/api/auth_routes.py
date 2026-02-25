"""Authentication endpoints — register, login, me."""
from __future__ import annotations

from datetime import time as dt_time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.api.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    AuthUserResponse,
)
from jyotish_ai.api.deps import get_db_session, get_user_repo, get_current_user
from jyotish_ai.auth import hash_password, verify_password, create_access_token
from jyotish_ai.persistence.models import User
from jyotish_ai.persistence.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def _parse_time(time_str: str | None) -> dt_time | None:
    if time_str is None:
        return None
    parts = time_str.split(":")
    return dt_time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Register a new user with email + password. Returns JWT token."""
    existing = await user_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
        name=payload.name,
        birth_date=payload.birth_date,
        birth_time=_parse_time(payload.birth_time),
        birth_place=payload.birth_place or "Not specified",
        latitude=payload.latitude if payload.latitude is not None else 28.6,
        longitude=payload.longitude if payload.longitude is not None else 77.2,
        timezone_offset=payload.timezone_offset if payload.timezone_offset is not None else 5.5,
        birth_time_tier=payload.birth_time_tier,
        phone_number=payload.phone_number,
        delivery_preference=payload.delivery_preference,
        whatsapp_opted_in=(
            payload.delivery_preference == "whatsapp" and payload.phone_number is not None
        ),
    )
    created = await user_repo.create(user)

    token = create_access_token(user_id=created.id, email=created.email)
    return TokenResponse(
        access_token=token,
        user_id=created.id,
        email=created.email,
        name=created.name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Login with email + password. Returns JWT token."""
    user = await user_repo.get_by_email(payload.email.lower().strip())
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


@router.get("/me", response_model=AuthUserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get the authenticated user's profile."""
    return current_user
