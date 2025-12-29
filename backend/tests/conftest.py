"""
Pytest fixtures for backend tests.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings


@pytest_asyncio.fixture
async def db_session():
    """
    Create a fresh database session for each test.
    Uses the configured database URL from settings.
    """
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False  # Set to True for SQL debugging
    )

    # Create tables (if they don't exist)
    async with engine.begin() as conn:
        # Note: We don't drop tables to preserve seed data
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create and yield session
    async with async_session() as session:
        yield session

    # Cleanup
    await engine.dispose()
