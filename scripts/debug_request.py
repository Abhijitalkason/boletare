"""
Trigger script for debugging the full prediction pipeline.

Usage:
  1. Start the server via VSCode "Debug Full Pipeline (Server)" config
  2. Set breakpoints in orchestrator.py, gate files, etc.
  3. Run this script in a separate terminal:
       python scripts/debug_request.py
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"


def register_test_user():
    """Register a test user with sample birth data."""
    payload = {
        "email": "debug@test.com",
        "password": "debug123",
        "full_name": "Debug User",
        "birth_date": "1990-01-15",
        "birth_time": "14:30:00",
        "birth_place": "Delhi, India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone_offset": 5.5,
    }
    resp = requests.post(f"{BASE_URL}/auth/register", json=payload)
    if resp.status_code == 200:
        print(f"Registered user: {resp.json()}")
        return resp.json()
    elif resp.status_code == 409 or "already" in resp.text.lower():
        print("User already exists, proceeding with login...")
        return None
    else:
        print(f"Register response [{resp.status_code}]: {resp.text}")
        return None


def login():
    """Login and get JWT token."""
    payload = {"email": "debug@test.com", "password": "debug123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Logged in. Token: {data.get('access_token', 'N/A')[:20]}...")
        return data
    else:
        print(f"Login failed [{resp.status_code}]: {resp.text}")
        return None


def run_prediction(user_id: int, token: str = None):
    """Fire a prediction request — this is what hits your breakpoints."""
    payload = {
        "user_id": user_id,
        "event_type": "MARRIAGE",
        "query_date": "2026-06-15",
        "is_retrospective": False,
        "ayanamsha": "lahiri",
    }

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"\nSending prediction request for user {user_id}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("Waiting for response (step through breakpoints in VSCode)...\n")

    resp = requests.post(f"{BASE_URL}/predictions", json=payload, headers=headers)

    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n--- Prediction Result ---")
        print(f"Confidence: {data.get('confidence_level', 'N/A')}")
        print(f"Convergence Score: {data.get('convergence_score', 'N/A')}")
        print(f"Gate 1 (Promise): {data.get('gate1', {}).get('score', 'N/A')}")
        print(f"Gate 2 (Dasha):   {data.get('gate2', {}).get('score', 'N/A')}")
        print(f"Gate 3 (Transit): {data.get('gate3', {}).get('score', 'N/A')}")
        print(f"Narration: {(data.get('narration_text') or 'N/A')[:200]}")
    else:
        print(f"Error: {resp.text}")


if __name__ == "__main__":
    print("=== Jyotish AI Debug Request ===\n")

    # Step 1: Register (idempotent)
    register_test_user()

    # Step 2: Login
    auth = login()
    if not auth:
        print("Cannot proceed without auth. Is the server running?")
        sys.exit(1)

    user_id = auth.get("user_id", auth.get("id", 1))
    token = auth.get("access_token")

    # Step 3: Fire prediction — this triggers the full pipeline
    run_prediction(user_id, token)
