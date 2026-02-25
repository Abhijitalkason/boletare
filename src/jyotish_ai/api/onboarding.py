"""WhatsApp onboarding endpoint — batch retrospective event recording.

Per the architecture doc (Section 6.2), WhatsApp onboarding asks users
about past events from the last 5 years:
  [Marriage] [Job Change] [Child Born] [Property] [Health Event] [None]
  -> For each: 'What month and year?' -> month/year picker
  -> Run birth chart retroactively -> extract feature vector -> store
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.api.schemas import (
    WhatsAppOnboardingRequest,
    EventResponse,
    PredictionResponse,
    GateScoreSchema,
)
from jyotish_ai.api.deps import get_db_session, get_user_repo, get_orchestrator
from jyotish_ai.domain.types import EventType
from jyotish_ai.persistence.models import Event
from jyotish_ai.persistence.repositories import UserRepository, EventRepository
from jyotish_ai.services.orchestrator import PredictionOrchestrator

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/whatsapp", status_code=201)
async def whatsapp_onboarding(
    payload: WhatsAppOnboardingRequest,
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
    orchestrator: PredictionOrchestrator = Depends(get_orchestrator),
):
    """Process WhatsApp onboarding: record retrospective events and run
    retroactive predictions for each.

    This is the core data acquisition pathway described in the architecture:
    500 users × ~2.5 past events = 1,250 immediate data points.

    Returns a list of recorded events + their prediction results.
    """
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event_repo = EventRepository(session)
    results = []

    for onboarding_event in payload.events:
        # Validate event type
        try:
            event_type = EventType(onboarding_event.event_type)
        except ValueError:
            results.append({
                "event_type": onboarding_event.event_type,
                "status": "error",
                "detail": f"Invalid event type: {onboarding_event.event_type}",
            })
            continue

        # Record the retrospective event
        event = Event(
            user_id=user.id,
            event_type=event_type.value,
            event_date=onboarding_event.event_date,
            is_retrospective=True,
        )
        created_event = await event_repo.create(event)

        # Run retroactive prediction
        try:
            prediction_result, prediction_id = await orchestrator.run_prediction(
                user=user,
                event_type=event_type,
                query_date=onboarding_event.event_date,
                is_retrospective=True,
            )

            results.append({
                "event_type": event_type.value,
                "event_id": created_event.id,
                "event_date": str(onboarding_event.event_date),
                "status": "ok",
                "prediction_id": prediction_id,
                "convergence_score": prediction_result.convergence_score,
                "confidence_level": prediction_result.confidence_level.value,
            })
        except Exception as e:
            results.append({
                "event_type": event_type.value,
                "event_id": created_event.id,
                "event_date": str(onboarding_event.event_date),
                "status": "prediction_failed",
                "detail": str(e),
            })

    return {
        "user_id": user.id,
        "events_processed": len(payload.events),
        "results": results,
    }
