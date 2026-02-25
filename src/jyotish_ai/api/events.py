"""Retrospective event recording endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from jyotish_ai.api.schemas import EventCreate, EventResponse
from jyotish_ai.api.deps import get_event_service, get_user_repo
from jyotish_ai.domain.types import EventType
from jyotish_ai.services.event_service import EventService
from jyotish_ai.persistence.repositories import UserRepository

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    payload: EventCreate,
    event_service: EventService = Depends(get_event_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Record a retrospective life event."""
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        event_type = EventType(payload.event_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid event type: {payload.event_type}",
        )

    event = await event_service.record_event(
        user_id=payload.user_id,
        event_type=event_type,
        event_date=payload.event_date,
        is_retrospective=payload.is_retrospective,
    )
    return event
