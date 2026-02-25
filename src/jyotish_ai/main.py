"""
Jyotish AI — FastAPI Application

Entry point: `uvicorn jyotish_ai.main:app --reload --port 8000`
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from jyotish_ai.config import settings
from jyotish_ai.db import init_db
from jyotish_ai.exceptions import JyotishError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.environment.value == "dev" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")
    logger.info("Jyotish AI v0.1.0 started (env=%s, ayanamsha=%s)",
                settings.environment.value, settings.ayanamsha)

    yield

    # Shutdown
    logger.info("Jyotish AI shutting down")


app = FastAPI(
    title="Jyotish AI",
    description="Deterministic Vedic Astrology Prediction Engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for JyotishError hierarchy
@app.exception_handler(JyotishError)
async def jyotish_error_handler(request: Request, exc: JyotishError):
    status_map = {
        "UserNotFoundError": 404,
        "PredictionNotFoundError": 404,
        "InvalidBirthDataError": 422,
        "ChartComputationError": 500,
        "InsufficientPromiseError": 200,  # Not an error — valid response
        "NarrationError": 502,
        "DeliveryError": 502,
    }
    status_code = status_map.get(type(exc).__name__, 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "detail": str(exc)},
    )


# Register API routers
from jyotish_ai.api.health import router as health_router
from jyotish_ai.api.users import router as users_router
from jyotish_ai.api.predictions import router as predictions_router
from jyotish_ai.api.events import router as events_router
from jyotish_ai.api.charts import router as charts_router
from jyotish_ai.api.engagement import router as engagement_router
from jyotish_ai.api.delivery import router as delivery_router
from jyotish_ai.api.onboarding import router as onboarding_router
from jyotish_ai.api.auth_routes import router as auth_router
from jyotish_ai.api.whatsapp_webhook import router as webhook_router
from jyotish_ai.api.kundli import router as kundli_router

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(charts_router, prefix="/api/v1")
app.include_router(engagement_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(kundli_router, prefix="/api/v1")

# Serve React static files (after API routes so API takes priority)
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
