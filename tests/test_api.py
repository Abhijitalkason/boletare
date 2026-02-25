"""
Jyotish AI — Test API Endpoints

Tests FastAPI routes using httpx AsyncClient with ASGITransport.
Uses an in-memory SQLite database for isolation.
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from jyotish_ai.main import app
from jyotish_ai.db import engine, init_db
from jyotish_ai.persistence.models import Base


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Initialize a clean in-memory database before each test."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Provide an async HTTP client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_health_endpoint(client: AsyncClient):
    """GET /api/v1/health should return 200 with status=ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


async def test_create_user(client: AsyncClient):
    """POST /api/v1/users should create a user and return 201."""
    payload = {
        "name": "Test User",
        "birth_date": "1990-01-15",
        "birth_time": "09:30",
        "birth_place": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone_offset": 5.5,
        "birth_time_tier": 2,
    }
    response = await client.post("/api/v1/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert "id" in data


async def test_get_nonexistent_user(client: AsyncClient):
    """GET /api/v1/users/999 should return 404 when the user does not exist."""
    response = await client.get("/api/v1/users/999")
    assert response.status_code == 404


async def test_prediction_with_invalid_event_type(client: AsyncClient):
    """POST /api/v1/predictions with an invalid event type should return 422."""
    # First create a user so we can reference a valid user_id
    user_payload = {
        "name": "Prediction Test User",
        "birth_date": "1990-01-15",
        "birth_time": "09:30",
        "birth_place": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone_offset": 5.5,
        "birth_time_tier": 2,
    }
    user_response = await client.post("/api/v1/users", json=user_payload)
    user_id = user_response.json()["id"]

    pred_payload = {
        "user_id": user_id,
        "event_type": "invalid_event_type",
        "query_date": "2024-06-15",
    }
    response = await client.post("/api/v1/predictions", json=pred_payload)
    assert response.status_code == 422


async def test_create_event(client: AsyncClient):
    """POST /api/v1/events should create an event after creating a user first."""
    # First create a user
    user_payload = {
        "name": "Event Test User",
        "birth_date": "1985-06-20",
        "birth_time": "14:00",
        "birth_place": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "timezone_offset": 5.5,
        "birth_time_tier": 1,
    }
    user_response = await client.post("/api/v1/users", json=user_payload)
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    # Create an event for that user
    event_payload = {
        "user_id": user_id,
        "event_type": "marriage",
        "event_date": "2015-03-10",
        "is_retrospective": True,
    }
    response = await client.post("/api/v1/events", json=event_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user_id
    assert data["event_type"] == "marriage"


async def test_cors_headers(client: AsyncClient):
    """CORS headers should be present on responses."""
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORS middleware should respond (200 for preflight)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
