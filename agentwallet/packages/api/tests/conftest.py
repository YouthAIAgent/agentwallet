"""Comprehensive test configuration with mocks and fixtures."""

import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Override environment variables for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["API_KEY_SECRET"] = "test-api-key-secret"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-bytes-long"
os.environ["SOLANA_RPC_URL"] = "https://api.devnet.solana.com"
os.environ["SOLANA_PRIVATE_KEY"] = "test-private-key"

from agentwallet.core.database import Base, get_engine, get_db_session, close_db
from agentwallet.core.redis_client import get_redis, close_redis
from agentwallet.main import app
from agentwallet.models import (
    Agent,
    AgentStatus,
    Escrow,
    EscrowStatus,
    Policy,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
    Wallet,
    WalletType,
)
from agentwallet.core.auth import create_access_token, create_api_key
from agentwallet.core.config import get_settings


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


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async with get_db_session() as session:
        yield session


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.exists = AsyncMock(return_value=False)
    mock_client.incr = AsyncMock(return_value=1)
    mock_client.expire = AsyncMock(return_value=True)
    mock_client.lpush = AsyncMock(return_value=1)
    mock_client.rpop = AsyncMock(return_value=None)
    
    with patch("agentwallet.core.redis_client.get_redis", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_solana_rpc():
    """Mock Solana RPC client."""
    mock_client = MagicMock()
    
    # Mock common responses
    mock_client.get_balance = AsyncMock(return_value={"value": 1000000000})  # 1 SOL
    mock_client.get_account_info = AsyncMock(return_value={"value": {"lamports": 1000000000}})
    mock_client.send_transaction = AsyncMock(return_value="mock_signature_123")
    mock_client.get_transaction = AsyncMock(return_value={
        "result": {
            "meta": {"err": None, "fee": 5000},
            "transaction": {"message": {"accountKeys": []}}
        }
    })
    mock_client.get_latest_blockhash = AsyncMock(return_value={"value": {"blockhash": "mock_blockhash"}})
    
    with patch("agentwallet.services.solana_service.get_solana_client", return_value=mock_client):
        yield mock_client


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        password_hash="$2b$12$test_hash",
        is_active=True,
        tier="basic",
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_agent(db_session: AsyncSession, test_user: User) -> Agent:
    """Create a test agent."""
    agent = Agent(
        id=str(uuid4()),
        name="Test Agent",
        description="A test agent for testing purposes",
        user_id=test_user.id,
        status=AgentStatus.ACTIVE,
        config={"model": "gpt-4", "temperature": 0.7},
        created_at=datetime.utcnow(),
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def test_wallet(db_session: AsyncSession, test_agent: Agent) -> Wallet:
    """Create a test wallet."""
    wallet = Wallet(
        id=str(uuid4()),
        agent_id=test_agent.id,
        address="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        private_key_encrypted="encrypted_private_key",
        wallet_type=WalletType.SOLANA,
        balance=Decimal("1.0"),
        created_at=datetime.utcnow(),
    )
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(wallet)
    return wallet


@pytest.fixture
async def test_policy(db_session: AsyncSession, test_agent: Agent) -> Policy:
    """Create a test policy."""
    policy = Policy(
        id=str(uuid4()),
        agent_id=test_agent.id,
        name="Default Policy",
        rules={"max_transaction_amount": "0.1", "allowed_recipients": ["*"]},
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    return policy


@pytest.fixture
async def test_transaction(db_session: AsyncSession, test_wallet: Wallet) -> Transaction:
    """Create a test transaction."""
    transaction = Transaction(
        id=str(uuid4()),
        from_wallet_id=test_wallet.id,
        to_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        amount=Decimal("0.1"),
        transaction_type=TransactionType.TRANSFER,
        status=TransactionStatus.PENDING,
        solana_signature="signature_123",
        created_at=datetime.utcnow(),
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


@pytest.fixture
async def test_escrow(db_session: AsyncSession, test_agent: Agent) -> Escrow:
    """Create a test escrow."""
    escrow = Escrow(
        id=str(uuid4()),
        agent_id=test_agent.id,
        amount=Decimal("0.5"),
        recipient_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        status=EscrowStatus.ACTIVE,
        terms="Test escrow terms",
        expires_at=datetime.utcnow() + timedelta(days=30),
        created_at=datetime.utcnow(),
    )
    db_session.add(escrow)
    await db_session.commit()
    await db_session.refresh(escrow)
    return escrow


@pytest.fixture
def jwt_token(test_user: User) -> str:
    """Create a JWT token for testing."""
    return create_access_token(data={"sub": test_user.id})


@pytest.fixture
def api_key(test_user: User) -> str:
    """Create an API key for testing."""
    return create_api_key(user_id=test_user.id, name="Test API Key")


@pytest.fixture
def auth_headers(jwt_token: str) -> dict:
    """Create authorization headers with JWT token."""
    return {"Authorization": f"Bearer {jwt_token}"}


@pytest.fixture
def api_key_headers(api_key: str) -> dict:
    """Create authorization headers with API key."""
    return {"X-API-Key": api_key}


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client() -> TestClient:
    """Create a sync HTTP client for testing."""
    return TestClient(app)


# Helper fixtures for common test scenarios
@pytest.fixture
async def inactive_agent(db_session: AsyncSession, test_user: User) -> Agent:
    """Create an inactive test agent."""
    agent = Agent(
        id=str(uuid4()),
        name="Inactive Agent",
        description="An inactive agent for testing",
        user_id=test_user.id,
        status=AgentStatus.INACTIVE,
        config={},
        created_at=datetime.utcnow(),
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def policy_with_spending_limit(db_session: AsyncSession, test_agent: Agent) -> Policy:
    """Create a policy with spending limits."""
    policy = Policy(
        id=str(uuid4()),
        agent_id=test_agent.id,
        name="Spending Limit Policy",
        rules={
            "max_transaction_amount": "0.01",
            "daily_spending_limit": "0.1",
            "allowed_recipients": ["5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3"]
        },
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    return policy


@pytest.fixture
async def completed_transaction(db_session: AsyncSession, test_wallet: Wallet) -> Transaction:
    """Create a completed transaction."""
    transaction = Transaction(
        id=str(uuid4()),
        from_wallet_id=test_wallet.id,
        to_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        amount=Decimal("0.05"),
        transaction_type=TransactionType.TRANSFER,
        status=TransactionStatus.COMPLETED,
        solana_signature="completed_signature_123",
        created_at=datetime.utcnow() - timedelta(hours=1),
        completed_at=datetime.utcnow(),
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


@pytest.fixture
async def expired_escrow(db_session: AsyncSession, test_agent: Agent) -> Escrow:
    """Create an expired escrow."""
    escrow = Escrow(
        id=str(uuid4()),
        agent_id=test_agent.id,
        amount=Decimal("0.2"),
        recipient_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        status=EscrowStatus.EXPIRED,
        terms="Expired escrow terms",
        expires_at=datetime.utcnow() - timedelta(days=1),
        created_at=datetime.utcnow() - timedelta(days=31),
    )
    db_session.add(escrow)
    await db_session.commit()
    await db_session.refresh(escrow)
    return escrow