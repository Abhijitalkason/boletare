"""Prediction endpoints — the core of the API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from jyotish_ai.api.schemas import (
    PredictionRequest, PredictionResponse, PredictionListItem, GateScoreSchema,
)
from jyotish_ai.api.deps import get_orchestrator, get_user_repo
from jyotish_ai.domain.types import EventType
from jyotish_ai.services.orchestrator import PredictionOrchestrator
from jyotish_ai.persistence.repositories import UserRepository, PredictionRepository
from jyotish_ai.api.deps import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=PredictionResponse, status_code=201)
async def run_prediction(
    payload: PredictionRequest,
    orchestrator: PredictionOrchestrator = Depends(get_orchestrator),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Run the full prediction pipeline for a user and event type."""
    # Validate user exists
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate event type
    try:
        event_type = EventType(payload.event_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid event type: {payload.event_type}. "
                   f"Must be one of: {[e.value for e in EventType]}",
        )

    # Run prediction pipeline
    result, prediction_db_id = await orchestrator.run_prediction(
        user=user,
        event_type=event_type,
        query_date=payload.query_date,
        is_retrospective=payload.is_retrospective,
        ayanamsha=payload.ayanamsha,
    )

    return PredictionResponse(
        id=prediction_db_id,
        user_id=result.user_id,
        event_type=result.event_type.value,
        query_date=result.query_date,
        gate1=GateScoreSchema(
            gate_name=result.gate1.gate_name,
            score=result.gate1.score,
            is_sufficient=result.gate1.is_sufficient,
            details=result.gate1.details,
        ),
        gate2=GateScoreSchema(
            gate_name=result.gate2.gate_name,
            score=result.gate2.score,
            is_sufficient=result.gate2.is_sufficient,
            details=result.gate2.details,
        ),
        gate3=GateScoreSchema(
            gate_name=result.gate3.gate_name,
            score=result.gate3.score,
            is_sufficient=result.gate3.is_sufficient,
            details=result.gate3.details,
        ),
        convergence_score=result.convergence_score,
        confidence_level=result.confidence_level.value,
        quality_flags=result.quality_flags.model_dump(mode="json"),
        peak_month=result.peak_month,
        feature_vector=result.feature_vector,
        narration_text=result.narration_text,
        is_retrospective=result.is_retrospective,
        created_at=result.created_at,
    )


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """Get a prediction by ID."""
    repo = PredictionRepository(session)
    pred = await repo.get_by_id(prediction_id)
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return PredictionResponse(
        id=pred.id,
        user_id=pred.user_id,
        event_type=pred.event_type,
        query_date=pred.query_date,
        gate1=GateScoreSchema(
            gate_name="gate1_promise",
            score=pred.gate1_score or 0.0,
            is_sufficient=True,
            details=pred.gate1_details_json or {},
        ),
        gate2=GateScoreSchema(
            gate_name="gate2_dasha",
            score=pred.gate2_score or 0.0,
            is_sufficient=True,
            details=pred.gate2_details_json or {},
        ),
        gate3=GateScoreSchema(
            gate_name="gate3_transit",
            score=pred.gate3_score or 0.0,
            is_sufficient=True,
            details=pred.gate3_details_json or {},
        ),
        convergence_score=pred.convergence_score or 0.0,
        confidence_level=pred.confidence_level or "INSUFFICIENT",
        quality_flags=pred.quality_flags_json or {},
        peak_month=None,
        feature_vector=pred.feature_vector_json or [],
        narration_text=pred.narration_text,
        is_retrospective=pred.is_retrospective or False,
        created_at=pred.created_at,
    )


@router.get("/user/{user_id}", response_model=list[PredictionListItem])
async def list_user_predictions(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """List all predictions for a user."""
    repo = PredictionRepository(session)
    predictions = await repo.get_by_user(user_id)
    return [
        PredictionListItem(
            id=p.id,
            event_type=p.event_type,
            query_date=p.query_date,
            convergence_score=p.convergence_score or 0.0,
            confidence_level=p.confidence_level or "INSUFFICIENT",
            is_retrospective=p.is_retrospective or False,
            created_at=p.created_at,
        )
        for p in predictions
    ]
