"""User registration and retrieval endpoints."""
from __future__ import annotations

from datetime import time as dt_time

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.api.schemas import UserCreate, UserResponse, UserPhoneUpdate
from jyotish_ai.api.deps import get_db_session, get_user_repo
from jyotish_ai.persistence.models import User
from jyotish_ai.persistence.repositories import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


def _parse_time(time_str: str | None) -> dt_time | None:
    """Convert a HH:MM or HH:MM:SS string to a Python time object."""
    if time_str is None:
        return None
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return dt_time(hour, minute, second)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Register a new user with birth data."""
    user = User(
        name=payload.name,
        birth_date=payload.birth_date,
        birth_time=_parse_time(payload.birth_time),
        birth_place=payload.birth_place or "Not specified",
        latitude=payload.latitude if payload.latitude is not None else 28.6,
        longitude=payload.longitude if payload.longitude is not None else 77.2,
        timezone_offset=payload.timezone_offset if payload.timezone_offset is not None else 5.5,
        birth_time_tier=payload.birth_time_tier,
        gender=payload.gender,
        age=payload.age,
        education=payload.education,
        income_bracket=payload.income,
        marital_status=payload.marital_status,
        phone_number=payload.phone_number,
        delivery_preference=payload.delivery_preference,
        whatsapp_opted_in=(
            payload.delivery_preference == "whatsapp" and payload.phone_number is not None
        ),
    )
    created = await user_repo.create(user)
    return created


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Get user by ID."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}/phone", response_model=UserResponse)
async def update_user_phone(
    user_id: int,
    payload: UserPhoneUpdate,
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Set or update a user's phone number and WhatsApp opt-in."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.phone_number = payload.phone_number
    user.whatsapp_opted_in = payload.opt_in_whatsapp
    if payload.opt_in_whatsapp:
        user.delivery_preference = "whatsapp"

    await session.flush()
    await session.refresh(user)
    return user


@router.delete("/{user_id}/phone", response_model=UserResponse)
async def remove_user_phone(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Remove phone number and revert to API delivery."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.phone_number = None
    user.whatsapp_opted_in = False
    user.delivery_preference = "api"

    await session.flush()
    await session.refresh(user)
    return user
