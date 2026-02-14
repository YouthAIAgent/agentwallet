"""Comprehensive test configuration with fixtures for all API tests."""

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Override environment variables BEFORE importing any app code
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-32-characters-long-for-testing"
os.environ["ENCRYPTION_KEY"] = "6FaAOgDwunjVGE6f6h-MnByGs6nrV1SC8_EcwnQlSBU="
os.environ["SOLANA_RPC_URL"] = "https://api.devnet.solana.com"
os.environ["PLATFORM_WALLET_ADDRESS"] = "11111111111111111111111111111111"

from agentwallet.api.middleware.auth import create_access_token, hash_password
from agentwallet.core.database import Base, close_db, get_engine, get_session_factory
from agentwallet.main import app
from agentwallet.models import (
    Agent,
    Escrow,
    Organization,
    Policy,
    Transaction,
    User,
    Wallet,
)

# ── Event loop ───────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Database setup / teardown ────────────────────────────


@pytest.fixture(autouse=True, scope="session")
async def setup_database():
    """Create all tables before tests, drop after."""
    import agentwallet.models  # noqa: F401 — populate Base.metadata

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await close_db()
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


# ── Core entities ────────────────────────────────────────


@pytest.fixture
async def test_org(db_session: AsyncSession):
    """Create a test organization."""
    org = Organization(
        name="Test Org",
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        tier="pro",
        is_active=True,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_user(db_session: AsyncSession, test_org):
    """Create a test user inside the org."""
    user = User(
        org_id=test_org.id,
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPassword123!"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_agent(db_session: AsyncSession, test_org):
    """Create a test agent inside the org."""
    agent = Agent(
        org_id=test_org.id,
        name="Test Agent",
        description="A test agent for automated testing",
        status="active",
        capabilities=["analysis", "trading"],
        is_public=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def test_wallet(db_session: AsyncSession, test_org, test_agent):
    """Create a test wallet for the agent."""
    # Use unique address per fixture invocation to avoid UNIQUE constraint violations
    unique_addr = f"Test{uuid.uuid4().hex[:28]}Addr"  # ~32 chars, unique
    wallet = Wallet(
        org_id=test_org.id,
        agent_id=test_agent.id,
        address=unique_addr,
        wallet_type="agent",
        encrypted_key="encrypted_test_key_placeholder",
        label="Test Wallet",
        is_active=True,
    )
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(wallet)
    return wallet


@pytest.fixture
async def test_escrow(db_session: AsyncSession, test_org, test_wallet):
    """Create a test escrow."""
    escrow = Escrow(
        org_id=test_org.id,
        funder_wallet_id=test_wallet.id,
        recipient_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        amount_lamports=500_000_000,  # 0.5 SOL
        status="created",
        conditions={"task": "test escrow"},
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(escrow)
    await db_session.commit()
    await db_session.refresh(escrow)
    return escrow


@pytest.fixture
async def test_policy(db_session: AsyncSession, test_org, test_agent):
    """Create a test policy."""
    policy = Policy(
        org_id=test_org.id,
        name="Default Policy",
        scope_type="agent",
        scope_id=test_agent.id,
        rules={"spending_limit_lamports": 100_000_000, "daily_limit_lamports": 1_000_000_000},
        priority=10,
        enabled=True,
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    return policy


@pytest.fixture
async def test_transaction(db_session: AsyncSession, test_org, test_wallet):
    """Create a test transaction."""
    tx = Transaction(
        org_id=test_org.id,
        wallet_id=test_wallet.id,
        tx_type="transfer_sol",
        status="pending",
        from_address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        to_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        amount_lamports=100_000_000,  # 0.1 SOL
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)
    return tx


# ── Auth fixtures ────────────────────────────────────────


@pytest.fixture
def jwt_token(test_user, test_org) -> str:
    """Create a JWT token for the test user."""
    return create_access_token(test_user.id, test_org.id)


@pytest.fixture
def auth_headers(jwt_token: str) -> dict:
    return {"Authorization": f"Bearer {jwt_token}"}


# ── HTTP client fixtures ─────────────────────────────────


@pytest.fixture
async def client(auth_headers) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated async client for API tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=auth_headers) as ac:
        yield ac


@pytest.fixture
async def unauthed_client() -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated async client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Marketplace-specific fixtures ────────────────────────


@pytest.fixture
def created_agent(test_agent):
    """Return agent data as a dict (used by test_marketplace.py)."""
    return {
        "id": str(test_agent.id),
        "name": test_agent.name,
        "org_id": str(test_agent.org_id),
    }


# ── Mock fixtures ────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis so tests don't need a running Redis server."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.exists = AsyncMock(return_value=False)
    mock_client.incr = AsyncMock(return_value=1)
    mock_client.expire = AsyncMock(return_value=True)

    with patch("agentwallet.core.redis_client._pool", mock_client):
        with patch("agentwallet.core.redis_client.get_redis", return_value=mock_client):
            yield mock_client


@pytest.fixture
def mock_solana_rpc():
    """Mock Solana RPC calls."""
    mock_balance = AsyncMock(return_value=1_000_000_000)
    mock_tokens = AsyncMock(return_value=[])

    with (
        patch("agentwallet.services.wallet_manager.get_balance", mock_balance),
        patch("agentwallet.services.wallet_manager.get_token_accounts", mock_tokens),
    ):
        yield mock_balance
