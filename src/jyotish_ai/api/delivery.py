"""Delivery management endpoints — send, status, history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.api.schemas import (
    DeliverPredictionRequest,
    DeliveryLogResponse,
    DeliveryStatusResponse,
)
from jyotish_ai.api.deps import get_db_session, get_user_repo
from jyotish_ai.persistence.repositories import (
    UserRepository,
    PredictionRepository,
    DeliveryLogRepository,
)
from jyotish_ai.services.delivery_service import DeliveryService

router = APIRouter(prefix="/delivery", tags=["delivery"])


@router.post("/predictions/{prediction_id}/send", response_model=DeliveryLogResponse)
async def send_prediction(
    prediction_id: int,
    payload: DeliverPredictionRequest = DeliverPredictionRequest(),
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Manually trigger delivery of a prediction to its user."""
    pred_repo = PredictionRepository(session)
    prediction = await pred_repo.get_by_id(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    user = await user_repo.get_by_id(prediction.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    content = prediction.narration_text or (
        f"Prediction #{prediction.id}: {prediction.event_type} — "
        f"Confidence: {prediction.confidence_level}, "
        f"Score: {prediction.convergence_score:.2f}"
    )

    delivery_service = DeliveryService(session)
    result = await delivery_service.deliver_prediction(
        user=user,
        prediction_id=prediction.id,
        content=content,
        override_channel=payload.channel,
    )

    # Fetch the latest delivery log we just created
    log_repo = DeliveryLogRepository(session)
    logs = await log_repo.get_by_prediction(prediction.id)
    if logs:
        return logs[0]

    # Fallback if log wasn't persisted
    return DeliveryLogResponse(
        id=0,
        user_id=user.id,
        prediction_id=prediction.id,
        channel=result.channel,
        message_id=result.message_id,
        success=result.success,
        error_message=result.error,
    )


@router.get("/predictions/{prediction_id}/status", response_model=DeliveryStatusResponse)
async def delivery_status(
    prediction_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """Get delivery status for a prediction (all attempts)."""
    pred_repo = PredictionRepository(session)
    prediction = await pred_repo.get_by_id(prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    log_repo = DeliveryLogRepository(session)
    logs = await log_repo.get_by_prediction(prediction_id)

    return DeliveryStatusResponse(
        prediction_id=prediction_id,
        deliveries=[
            DeliveryLogResponse(
                id=log.id,
                user_id=log.user_id,
                prediction_id=log.prediction_id,
                engagement_id=log.engagement_id,
                channel=log.channel,
                phone_number=log.phone_number,
                message_id=log.message_id,
                success=log.success,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            for log in logs
        ],
        latest_success=any(log.success for log in logs),
    )


@router.get("/users/{user_id}/history", response_model=list[DeliveryLogResponse])
async def delivery_history(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Get delivery history for a user."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log_repo = DeliveryLogRepository(session)
    logs = await log_repo.get_by_user(user_id)
    return [
        DeliveryLogResponse(
            id=log.id,
            user_id=log.user_id,
            prediction_id=log.prediction_id,
            engagement_id=log.engagement_id,
            channel=log.channel,
            phone_number=log.phone_number,
            message_id=log.message_id,
            success=log.success,
            error_message=log.error_message,
            created_at=log.created_at,
        )
        for log in logs
    ]
