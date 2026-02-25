"""
Jyotish AI — Authentication Utilities

Password hashing (bcrypt direct) and JWT token management.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
import bcrypt

from jyotish_ai.config import settings

# ── Password Hashing ────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]  # bcrypt max 72 bytes
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    pw_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hashed_bytes)


# ── JWT Tokens ──────────────────────────────────────────────

def create_access_token(
    user_id: int,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None
