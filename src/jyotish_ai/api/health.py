"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter
from jyotish_ai.api.schemas import HealthResponse
from jyotish_ai.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.environment.value,
        database="connected",
    )
