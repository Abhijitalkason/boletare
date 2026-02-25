"""
Jyotish AI — Database Engine & Session Factory

Async SQLAlchemy with SQLite (Phase A).
Migration path: change DATABASE_URL to postgresql+asyncpg:// for Phase B.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from jyotish_ai.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=(settings.environment.value == "dev"),
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create all tables. Called once at startup."""
    from jyotish_ai.persistence.models import Base  # noqa: F401 — register models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Dependency-injectable session generator."""
    async with async_session_factory() as session:
        try:
            yield session  # type: ignore[misc]
            await session.commit()
        except Exception:
            await session.rollback()
            raise
