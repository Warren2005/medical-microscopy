"""
PostgreSQL async connection manager using SQLAlchemy.

Provides:
- Async engine with connection pooling
- Session factory for request-scoped sessions
- Health check via SELECT 1
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.core.config import settings
from app.core.logging_config import logger


class DatabaseService:
    def __init__(self, database_url: str):
        # Convert postgresql:// to postgresql+asyncpg:// for async driver
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        self._url = database_url
        self._engine = None
        self._session_factory = None

    async def connect(self):
        self._engine = create_async_engine(
            self._url,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Connected to PostgreSQL", extra={"url": self._url.split("@")[-1]})

    async def disconnect(self):
        if self._engine:
            await self._engine.dispose()
            logger.info("Disconnected from PostgreSQL")

    async def health_check(self) -> bool:
        async with self._session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


db_service = DatabaseService(settings.database_url)
