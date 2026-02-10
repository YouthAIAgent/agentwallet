"""Test configuration -- use SQLite for tests."""

import os

# Override database URL before importing anything
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["ENCRYPTION_KEY"] = ""

import asyncio

import pytest

from agentwallet.core.database import Base, get_engine, close_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def setup_database():
    """Create all tables before tests, drop after."""
    # Import all models so Base.metadata is populated
    import agentwallet.models  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await close_db()
    # Clean up test.db file
    if os.path.exists("test.db"):
        os.remove("test.db")
