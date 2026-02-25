"""
Jyotish AI — Prediction Orchestrator

THE core pipeline: L1 (Compute) → L2 (Predict) → L3 (Narrate) → L4 (Deliver) → Persist.

This is the single entry point for running a prediction. All other services
and modules are wired together here.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.domain.types import EventType, ConfidenceLevel
from jyotish_ai.domain.models import (
    BirthChart, PredictionResult, GateResult, QualityFlags,
)
from jyotish_ai.prediction.gate1_promise import evaluate_promise
from jyotish_ai.prediction.gate2_dasha import evaluate_dasha
from jyotish_ai.prediction.gate3_transit import evaluate_transit
from jyotish_ai.prediction.convergence import compute_convergence
from jyotish_ai.prediction.quality_flags import compute_quality_flags
from jyotish_ai.prediction.feature_builder import build_feature_vector
from jyotish_ai.narration.base import create_narrator
from jyotish_ai.services.delivery_service import DeliveryService
from jyotish_ai.persistence.models import Prediction
from jyotish_ai.persistence.repositories import PredictionRepository
from jyotish_ai.services.chart_service import ChartService
from jyotish_ai.persistence.models import User
from jyotish_ai.config import settings

logger = logging.getLogger(__name__)


class PredictionOrchestrator:
    """Wires all layers together into a single prediction pipeline."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._chart_service = ChartService(session)
        self._prediction_repo = PredictionRepository(session)
        self._delivery_service = DeliveryService(session)

    async def run_prediction(
        self,
        user: User,
        event_type: EventType,
        query_date: Optional[date] = None,
        is_retrospective: bool = False,
        ayanamsha: str = "lahiri",
    ) -> tuple[PredictionResult, Optional[int]]:
        """Execute the full prediction pipeline.

        Steps:
        1. Compute/retrieve birth chart (Layer 1, cached)
        2. Gate 1: Promise analysis — short-circuit if insufficient
        3. Gate 2: Dasha evaluation
        4. Gate 3: Double transit window detection
        5. Compute convergence + confidence
        6. Compute quality flags
        7. Build 22-feature vector
        8. Persist prediction to DB
        9. Trigger LLM narration (non-blocking failure)
        10. Return PredictionResult

        Args:
            user: User with birth data
            event_type: Event to predict
            query_date: Date for prediction (default: today)
            is_retrospective: Whether predicting a past event
            ayanamsha: Ayanamsha system

        Returns:
            Complete PredictionResult
        """
        if query_date is None:
            query_date = date.today()

        logger.info("Running prediction: user=%d, event=%s, date=%s",
                    user.id, event_type.value, query_date)

        # ── Step 1: Birth Chart (Layer 1) ────────────────────
        chart = await self._chart_service.get_or_compute_chart(
            user=user, ayanamsha=ayanamsha,
        )

        # ── Step 2: Gate 1 — Promise ─────────────────────────
        gate1 = evaluate_promise(
            chart=chart,
            event_type=event_type,
            promise_threshold=settings.promise_gate_threshold,
        )

        # Short-circuit if insufficient promise
        if not gate1.is_sufficient:
            logger.info("Gate 1 insufficient for user %d, event %s (score=%.2f)",
                       user.id, event_type.value, gate1.score)
            insufficient_result = self._build_insufficient_result(
                user.id, event_type, query_date, gate1, chart, is_retrospective,
            )
            return insufficient_result, None

        # ── Step 3: Gate 2 — Dasha ───────────────────────────
        gate2 = evaluate_dasha(
            chart=chart,
            event_type=event_type,
            query_date=query_date,
        )

        # ── Step 4: Gate 3 — Double Transit ──────────────────
        gate3 = evaluate_transit(
            chart=chart,
            event_type=event_type,
            query_date=query_date,
            ayanamsha=ayanamsha,
        )

        # ── Step 5: Convergence + Confidence ─────────────────
        convergence_score, confidence_level = compute_convergence(
            gate1=gate1,
            gate2=gate2,
            gate3=gate3,
            w1=settings.w1_promise,
            w2=settings.w2_dasha,
            w3=settings.w3_transit,
        )

        # ── Step 6: Quality Flags ────────────────────────────
        quality_flags = compute_quality_flags(chart, is_retrospective=is_retrospective)

        # ── Step 7: Feature Vector ───────────────────────────
        feature_vector = build_feature_vector(
            gate1=gate1,
            gate2=gate2,
            gate3=gate3,
            convergence_score=convergence_score,
            quality_flags=quality_flags,
        )

        # ── Step 8: Extract timeline and peak ────────────────
        timeline = gate3.details.get("timeline", [])
        peak_month = gate3.details.get("peak_month")

        # ── Step 9: Narration (Layer 3) ──────────────────────
        narration_text = None
        try:
            narrator = create_narrator(api_key=settings.anthropic_api_key)
            narration_text = await narrator.narrate(
                event_type=event_type,
                confidence_level=confidence_level,
                convergence_score=convergence_score,
                gate1=gate1,
                gate2=gate2,
                gate3=gate3,
                quality_flags=quality_flags,
                peak_month=peak_month,
            )
        except Exception:
            logger.exception("Narration failed (non-fatal)")

        # ── Step 10: Build result ────────────────────────────
        result = PredictionResult(
            user_id=user.id,
            event_type=event_type,
            query_date=query_date,
            gate1=gate1,
            gate2=gate2,
            gate3=gate3,
            convergence_score=convergence_score,
            confidence_level=confidence_level,
            quality_flags=quality_flags,
            timeline=[],  # Serialized in details already
            peak_month=peak_month,
            feature_vector=feature_vector,
            narration_text=narration_text,
            is_retrospective=is_retrospective,
            created_at=datetime.utcnow(),
        )

        # ── Step 11: Persist ─────────────────────────────────
        prediction_db_id = await self._persist_prediction(user.id, result, timeline)

        # ── Step 12: Delivery (Layer 4) ────────────────────────
        if prediction_db_id and narration_text:
            try:
                await self._delivery_service.deliver_prediction(
                    user=user,
                    prediction_id=prediction_db_id,
                    content=narration_text,
                )
            except Exception:
                logger.exception("Delivery failed (non-fatal)")

        logger.info(
            "Prediction complete: user=%d, event=%s, confidence=%s, score=%.2f",
            user.id, event_type.value, confidence_level.value, convergence_score,
        )

        return result, prediction_db_id

    async def _persist_prediction(
        self,
        user_id: int,
        result: PredictionResult,
        timeline: list,
    ) -> Optional[int]:
        """Save prediction to database. Returns the DB record ID or None."""
        try:
            record = Prediction(
                user_id=user_id,
                event_type=result.event_type.value,
                query_date=result.query_date,
                gate1_score=result.gate1.score,
                gate2_score=result.gate2.score,
                gate3_score=result.gate3.score,
                convergence_score=result.convergence_score,
                confidence_level=result.confidence_level.value,
                quality_flags_json=result.quality_flags.model_dump(mode="json"),
                feature_vector_json=result.feature_vector,
                timeline_json=timeline,
                narration_text=result.narration_text,
                gate1_details_json=result.gate1.details,
                gate2_details_json=result.gate2.details,
                gate3_details_json={k: v for k, v in result.gate3.details.items() if k != "timeline"},
                is_retrospective=result.is_retrospective,
            )
            created = await self._prediction_repo.create(record)
            return created.id
        except Exception:
            logger.exception("Failed to persist prediction (non-fatal)")
            return None

    def _build_insufficient_result(
        self,
        user_id: int,
        event_type: EventType,
        query_date: date,
        gate1: GateResult,
        chart: BirthChart,
        is_retrospective: bool,
    ) -> PredictionResult:
        """Build a result for insufficient promise (Gate 1 fail)."""
        empty_gate = GateResult(
            gate_name="skipped",
            score=0.0,
            is_sufficient=False,
            details={"reason": "Gate 1 promise insufficient — pipeline short-circuited"},
        )
        quality_flags = compute_quality_flags(chart, is_retrospective=is_retrospective)

        return PredictionResult(
            user_id=user_id,
            event_type=event_type,
            query_date=query_date,
            gate1=gate1,
            gate2=empty_gate,
            gate3=empty_gate,
            convergence_score=0.0,
            confidence_level=ConfidenceLevel.INSUFFICIENT,
            quality_flags=quality_flags,
            timeline=[],
            peak_month=None,
            feature_vector=[0.0] * 22,
            narration_text="The birth chart does not show sufficient promise for this event type. "
                          "The analysis has been halted at Gate 1 (Promise Analysis).",
            is_retrospective=is_retrospective,
            created_at=datetime.utcnow(),
        )
