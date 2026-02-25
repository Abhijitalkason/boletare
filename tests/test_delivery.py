"""
Tests for the WhatsApp delivery pipeline (Layer 4).

Tests cover:
- WhatsApp message formatting
- Delivery channel selection logic
- DeliveryService channel routing
- API delivery passthrough
- Delivery log persistence
- Phone number validation in schemas
- Delivery API endpoints
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import date

from jyotish_ai.delivery.base import DeliveryResult
from jyotish_ai.delivery.whatsapp import WhatsAppDelivery
from jyotish_ai.delivery.api_delivery import ApiDelivery


# ── WhatsApp Delivery Tests ──────────────────────────────────────

class TestWhatsAppDelivery:
    """Tests for WhatsAppDelivery channel."""

    def setup_method(self):
        self.wa = WhatsAppDelivery(
            api_key="test-key",
            phone_id="test-phone-id",
        )

    def test_format_message_basic(self):
        """Message should include header, content, and footer."""
        formatted = self.wa._format_message("Hello world", 42)
        assert "Jyotish AI Prediction #42" in formatted
        assert "Hello world" in formatted
        assert "Powered by Jyotish AI" in formatted

    def test_format_message_truncation(self):
        """Long messages should be truncated to ~4000 chars."""
        long_content = "x" * 5000
        formatted = self.wa._format_message(long_content, 1)
        assert len(formatted) <= 4100
        assert "[Message truncated]" in formatted

    @pytest.mark.asyncio
    async def test_deliver_without_phone_number(self):
        """Should fail gracefully when no phone number provided."""
        result = await self.wa.deliver(
            user_id=1,
            prediction_id=1,
            content="Test",
            phone_number=None,
        )
        assert not result.success
        assert result.channel == "whatsapp"
        assert "No phone number" in result.error

    @pytest.mark.asyncio
    async def test_deliver_with_phone_number(self):
        """Should attempt HTTP POST to OpenClaw API."""
        from unittest.mock import MagicMock

        with patch("jyotish_ai.delivery.whatsapp.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "messages": [{"id": "wamid.test123"}]
            }
            mock_response.raise_for_status = MagicMock()  # sync method in httpx

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            result = await self.wa.deliver(
                user_id=1,
                prediction_id=1,
                content="Your prediction results are ready.",
                phone_number="+919876543210",
            )

            assert result.success
            assert result.channel == "whatsapp"
            assert result.message_id == "wamid.test123"
            mock_instance.post.assert_called_once()

            # Verify the payload structure
            call_args = mock_instance.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert payload["messaging_product"] == "whatsapp"
            assert payload["to"] == "+919876543210"
            assert payload["type"] == "text"

    @pytest.mark.asyncio
    async def test_deliver_handles_http_error(self):
        """Should return failure result on HTTP errors."""
        import httpx
        from unittest.mock import MagicMock

        with patch("jyotish_ai.delivery.whatsapp.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401", request=MagicMock(), response=mock_response,
            )

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            result = await self.wa.deliver(
                user_id=1,
                prediction_id=1,
                content="Test",
                phone_number="+919876543210",
            )

            assert not result.success
            assert "401" in result.error


# ── API Delivery Tests ───────────────────────────────────────────

class TestApiDelivery:
    """Tests for ApiDelivery channel."""

    @pytest.mark.asyncio
    async def test_api_delivery_always_succeeds(self):
        """API delivery is implicit — always returns success."""
        api = ApiDelivery()
        result = await api.deliver(
            user_id=1,
            prediction_id=42,
            content="Test content",
        )
        assert result.success
        assert result.channel == "api"
        assert result.message_id == "42"
        assert "/api/v1/predictions/42" in result.metadata["fetch_url"]


# ── Schema Validation Tests ──────────────────────────────────────

class TestPhoneValidation:
    """Tests for phone number validation in schemas."""

    def test_valid_e164_phone(self):
        from jyotish_ai.api.schemas import UserPhoneUpdate
        update = UserPhoneUpdate(phone_number="+919876543210")
        assert update.phone_number == "+919876543210"

    def test_valid_phone_without_plus(self):
        from jyotish_ai.api.schemas import UserPhoneUpdate
        update = UserPhoneUpdate(phone_number="919876543210")
        assert update.phone_number == "919876543210"

    def test_invalid_phone_rejected(self):
        from pydantic import ValidationError
        from jyotish_ai.api.schemas import UserPhoneUpdate
        with pytest.raises(ValidationError):
            UserPhoneUpdate(phone_number="invalid")

    def test_delivery_preference_valid(self):
        from jyotish_ai.api.schemas import UserCreate
        user = UserCreate(
            name="Test",
            birth_date=date(1990, 1, 1),
            delivery_preference="whatsapp",
        )
        assert user.delivery_preference == "whatsapp"

    def test_delivery_preference_invalid(self):
        from pydantic import ValidationError
        from jyotish_ai.api.schemas import UserCreate
        with pytest.raises(ValidationError):
            UserCreate(
                name="Test",
                birth_date=date(1990, 1, 1),
                delivery_preference="sms",
            )


# ── Delivery API Endpoint Tests ──────────────────────────────────

@pytest.mark.asyncio
async def test_delivery_endpoints_exist():
    """Verify that delivery router has the expected routes."""
    from jyotish_ai.api.delivery import router
    paths = [route.path for route in router.routes]
    assert "/delivery/predictions/{prediction_id}/send" in paths
    assert "/delivery/predictions/{prediction_id}/status" in paths
    assert "/delivery/users/{user_id}/history" in paths


@pytest.mark.asyncio
async def test_onboarding_endpoint_exists():
    """Verify that onboarding router has the expected route."""
    from jyotish_ai.api.onboarding import router
    paths = [route.path for route in router.routes]
    assert "/onboarding/whatsapp" in paths


# ── Integration: Full App Endpoint Test ──────────────────────────

@pytest.mark.asyncio
async def test_user_phone_update_endpoint():
    """Test the PUT /users/{id}/phone endpoint via TestClient."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Create user without phone
        resp = await client.post("/api/v1/users", json={
            "name": "Phone Test User",
            "birth_date": "1990-05-15",
        })
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Set phone number
        resp = await client.put(f"/api/v1/users/{user_id}/phone", json={
            "phone_number": "+919876543210",
            "opt_in_whatsapp": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone_number"] == "+919876543210"
        assert data["whatsapp_opted_in"] is True
        assert data["delivery_preference"] == "whatsapp"

        # Remove phone
        resp = await client.delete(f"/api/v1/users/{user_id}/phone")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone_number"] is None
        assert data["whatsapp_opted_in"] is False
        assert data["delivery_preference"] == "api"
