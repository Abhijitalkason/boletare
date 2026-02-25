"""
Jyotish AI — API Dependencies

FastAPI dependency injection for database sessions and services.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from jyotish_ai.db import async_session_factory
from jyotish_ai.services.orchestrator import PredictionOrchestrator
from jyotish_ai.services.chart_service import ChartService
from jyotish_ai.services.event_service import EventService
from jyotish_ai.persistence.repositories import UserRepository
from jyotish_ai.persistence.models import User

# Optional Bearer token — allows unauthenticated access when token not provided
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session that auto-commits on success, rolls back on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Extract and validate JWT from Authorization header. Returns the User."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from jyotish_ai.auth import decode_access_token

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Optional[User]:
    """Like get_current_user, but returns None if no token provided."""
    if credentials is None:
        return None

    from jyotish_ai.auth import decode_access_token

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None

    user_id = int(payload["sub"])
    return await user_repo.get_by_id(user_id)


def get_chart_service(session: AsyncSession = Depends(get_db_session)) -> ChartService:
    return ChartService(session)


def get_event_service(session: AsyncSession = Depends(get_db_session)) -> EventService:
    return EventService(session)


def get_orchestrator(session: AsyncSession = Depends(get_db_session)) -> PredictionOrchestrator:
    return PredictionOrchestrator(session)
