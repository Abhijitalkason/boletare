"""
Tests for authentication (register, login, JWT) and WhatsApp webhook registration.

Tests cover:
- User registration via email/password with DB validation
- Login with correct/incorrect credentials
- JWT token generation and validation
- /auth/me endpoint (authenticated)
- WhatsApp webhook verification handshake
- WhatsApp conversational registration flow
- DB storage validation for both registration paths
"""

import pytest
from unittest.mock import patch


# ── Auth Utility Tests ──────────────────────────────────────

class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_and_verify_password(self):
        from jyotish_ai.auth import hash_password, verify_password
        hashed = hash_password("mysecretpass")
        assert hashed != "mysecretpass"
        assert verify_password("mysecretpass", hashed)
        assert not verify_password("wrongpass", hashed)

    def test_hash_produces_different_hashes(self):
        from jyotish_ai.auth import hash_password
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salt


class TestJWTToken:
    """Tests for JWT token creation and decoding."""

    def test_create_and_decode_token(self):
        from jyotish_ai.auth import create_access_token, decode_access_token
        token = create_access_token(user_id=42, email="test@example.com")
        assert isinstance(token, str)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["email"] == "test@example.com"

    def test_decode_invalid_token_returns_none(self):
        from jyotish_ai.auth import decode_access_token
        assert decode_access_token("invalid.token.here") is None
        assert decode_access_token("") is None


# ── Auth Endpoint Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_register_creates_user_in_db():
    """Register via /auth/register and verify user exists in DB."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "newuser@jyotish.ai",
            "password": "securepass123",
            "name": "Test User",
            "birth_date": "1990-05-15",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "newuser@jyotish.ai"
        assert data["name"] == "Test User"
        assert data["user_id"] > 0

        # Verify user can be fetched
        user_resp = await client.get(f"/api/v1/users/{data['user_id']}")
        assert user_resp.status_code == 200
        user_data = user_resp.json()
        assert user_data["name"] == "Test User"


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected():
    """Duplicate email registration should return 409."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        payload = {
            "email": "duplicate@jyotish.ai",
            "password": "pass123456",
            "name": "User One",
            "birth_date": "1985-01-01",
        }
        resp1 = await client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = await client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409
        assert "already registered" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_returns_token():
    """Login with valid credentials returns JWT token."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Register
        await client.post("/api/v1/auth/register", json={
            "email": "loginuser@jyotish.ai",
            "password": "mypassword",
            "name": "Login User",
            "birth_date": "1992-08-20",
        })

        # Login
        resp = await client.post("/api/v1/auth/login", json={
            "email": "loginuser@jyotish.ai",
            "password": "mypassword",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "loginuser@jyotish.ai"


@pytest.mark.asyncio
async def test_login_wrong_password_rejected():
    """Login with wrong password returns 401."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        await client.post("/api/v1/auth/register", json={
            "email": "wrongpw@jyotish.ai",
            "password": "correctpass",
            "name": "Wrong PW",
            "birth_date": "1995-03-10",
        })

        resp = await client.post("/api/v1/auth/login", json={
            "email": "wrongpw@jyotish.ai",
            "password": "incorrectpass",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_with_token():
    """/auth/me returns user profile when authenticated."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Register
        reg_resp = await client.post("/api/v1/auth/register", json={
            "email": "metest@jyotish.ai",
            "password": "testpass",
            "name": "Me Test",
            "birth_date": "1988-12-25",
        })
        token = reg_resp.json()["access_token"]

        # Get /me
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["name"] == "Me Test"
        assert data["email"] == "metest@jyotish.ai"


@pytest.mark.asyncio
async def test_me_endpoint_without_token():
    """/auth/me returns 401 when no token provided."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ── Register with WhatsApp Preference ───────────────────────

@pytest.mark.asyncio
async def test_register_with_whatsapp_preference():
    """Registration with phone + whatsapp preference enables WhatsApp delivery."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "wauser@jyotish.ai",
            "password": "whatsapp123",
            "name": "WhatsApp User",
            "birth_date": "1991-07-04",
            "phone_number": "+919876543210",
            "delivery_preference": "whatsapp",
        })
        assert resp.status_code == 201
        user_id = resp.json()["user_id"]

        # Verify user has WhatsApp enabled
        user_resp = await client.get(f"/api/v1/users/{user_id}")
        data = user_resp.json()
        assert data["phone_number"] == "+919876543210"
        assert data["delivery_preference"] == "whatsapp"
        assert data["whatsapp_opted_in"] is True


# ── WhatsApp Webhook Tests ──────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_verification_handshake():
    """GET /webhook/whatsapp with correct verify token returns challenge."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/v1/webhook/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "jyotish-verify-token",
            "hub.challenge": "1234567890",
        })
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_webhook_verification_wrong_token():
    """GET /webhook/whatsapp with wrong verify token returns 403."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/v1/webhook/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "123",
        })
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_full_registration_flow():
    """Simulate a full WhatsApp registration conversation via webhook POST."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db
    from jyotish_ai.api.whatsapp_webhook import _conversations

    await init_db()

    # Clear any stale conversation state
    _conversations.clear()

    def make_webhook_payload(phone: str, text: str) -> dict:
        return {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": phone,
                            "type": "text",
                            "text": {"body": text},
                        }]
                    }
                }]
            }]
        }

    phone = "910000000001"  # Unique number not used in other tests

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Step 1: User sends "Hi" — gets welcome + name prompt
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_webhook_payload(phone, "Hi"),
        )
        assert resp.status_code == 200

        # Step 2: User sends name
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_webhook_payload(phone, "Rahul Sharma"),
        )
        assert resp.status_code == 200

        # Step 3: User sends birth date
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_webhook_payload(phone, "15-05-1990"),
        )
        assert resp.status_code == 200

        # Step 4: User sends birth time
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_webhook_payload(phone, "09:30"),
        )
        assert resp.status_code == 200

        # Step 5: User sends birth place
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_webhook_payload(phone, "Delhi"),
        )
        assert resp.status_code == 200

        # Step 6: User confirms with "yes"
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_webhook_payload(phone, "yes"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("registration") == "complete"
        assert "user_id" in data
        user_id = data["user_id"]

        # Verify user stored in DB
        user_resp = await client.get(f"/api/v1/users/{user_id}")
        assert user_resp.status_code == 200
        user_data = user_resp.json()
        assert user_data["name"] == "Rahul Sharma"
        assert user_data["delivery_preference"] == "whatsapp"
        assert user_data["whatsapp_opted_in"] is True


@pytest.mark.asyncio
async def test_webhook_kundli_command():
    """Registered user types 'kundli' and receives their birth chart."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db
    from jyotish_ai.api.whatsapp_webhook import _conversations

    await init_db()
    _conversations.clear()

    def make_payload(phone: str, text: str) -> dict:
        return {
            "entry": [{"changes": [{"value": {"messages": [{
                "from": phone, "type": "text", "text": {"body": text},
            }]}}]}]
        }

    phone = "910000000002"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Register first: Hi -> name -> date -> time -> place -> yes
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Hi"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Kundli Test"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "10-01-1985"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "14:30"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Mumbai"))
        reg = await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "yes"))
        assert reg.json().get("registration") == "complete"
        user_id = reg.json()["user_id"]

        # Now send "kundli" command
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_payload(phone, "kundli"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "kundli_sent"
        assert data["user_id"] == user_id


@pytest.mark.asyncio
async def test_webhook_help_command():
    """Registered user types 'help' and gets menu."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db
    from jyotish_ai.api.whatsapp_webhook import _conversations

    await init_db()
    _conversations.clear()

    def make_payload(phone: str, text: str) -> dict:
        return {
            "entry": [{"changes": [{"value": {"messages": [{
                "from": phone, "type": "text", "text": {"body": text},
            }]}}]}]
        }

    phone = "910000000003"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Register
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Hi"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Help User"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "01-06-1995"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "skip"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Chennai"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "yes"))

        # Send help command
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_payload(phone, "help"),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "help"


@pytest.mark.asyncio
async def test_webhook_predict_command():
    """Registered user types 'predict marriage' and gets a prediction."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db
    from jyotish_ai.api.whatsapp_webhook import _conversations

    await init_db()
    _conversations.clear()

    def make_payload(phone: str, text: str) -> dict:
        return {
            "entry": [{"changes": [{"value": {"messages": [{
                "from": phone, "type": "text", "text": {"body": text},
            }]}}]}]
        }

    phone = "910000000004"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Register
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Hi"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Predict User"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "20-03-1992"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "10:00"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Delhi"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "yes"))

        # Send predict command
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_payload(phone, "predict marriage"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "prediction_sent"


@pytest.mark.asyncio
async def test_webhook_predict_invalid_event():
    """Invalid event type returns helpful error."""
    from httpx import ASGITransport, AsyncClient
    from jyotish_ai.main import app
    from jyotish_ai.db import init_db
    from jyotish_ai.api.whatsapp_webhook import _conversations

    await init_db()
    _conversations.clear()

    def make_payload(phone: str, text: str) -> dict:
        return {
            "entry": [{"changes": [{"value": {"messages": [{
                "from": phone, "type": "text", "text": {"body": text},
            }]}}]}]
        }

    phone = "910000000005"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Register
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Hi"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Invalid User"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "05-11-1988"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "skip"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "Pune"))
        await client.post("/api/v1/webhook/whatsapp", json=make_payload(phone, "yes"))

        # Invalid event type
        resp = await client.post(
            "/api/v1/webhook/whatsapp",
            json=make_payload(phone, "predict lottery"),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "predict_invalid"


# ── Schema Validation Tests ─────────────────────────────────

class TestAuthSchemaValidation:
    """Tests for auth schema validation."""

    def test_register_invalid_email_rejected(self):
        from pydantic import ValidationError
        from jyotish_ai.api.schemas import RegisterRequest
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="pass123",
                name="Test",
                birth_date="1990-01-01",
            )

    def test_register_short_password_rejected(self):
        from pydantic import ValidationError
        from jyotish_ai.api.schemas import RegisterRequest
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="12345",  # < 6 chars
                name="Test",
                birth_date="1990-01-01",
            )

    def test_register_valid_request(self):
        from jyotish_ai.api.schemas import RegisterRequest
        req = RegisterRequest(
            email="valid@example.com",
            password="secure123",
            name="Valid User",
            birth_date="1990-01-01",
        )
        assert req.email == "valid@example.com"


# ── Auth Router Existence ───────────────────────────────────

@pytest.mark.asyncio
async def test_auth_routes_exist():
    """Verify that auth router has the expected routes."""
    from jyotish_ai.api.auth_routes import router
    paths = [route.path for route in router.routes]
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/me" in paths


@pytest.mark.asyncio
async def test_webhook_routes_exist():
    """Verify that webhook router has the expected routes."""
    from jyotish_ai.api.whatsapp_webhook import router
    paths = [route.path for route in router.routes]
    assert "/webhook/whatsapp" in paths
