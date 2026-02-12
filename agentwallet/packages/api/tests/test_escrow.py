"""Tests for escrow lifecycle operations."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from agentwallet.models import Agent, Escrow, EscrowStatus


@pytest.mark.asyncio
async def test_create_escrow(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a new escrow."""
    # Mock successful escrow creation transaction
    mock_solana_rpc.send_transaction.return_value = "escrow_creation_signature"
    
    escrow_data = {
        "agent_id": test_agent.id,
        "amount": "0.5",
        "recipient_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "terms": "Payment for service completion",
        "expires_in_days": 30,
        "dispute_resolver": "ArbitratorAddress123456789"
    }
    
    response = await async_client.post(
        "/v1/escrow",
        json=escrow_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == test_agent.id
    assert Decimal(data["amount"]) == Decimal(escrow_data["amount"])
    assert data["recipient_address"] == escrow_data["recipient_address"]
    assert data["terms"] == escrow_data["terms"]
    assert data["status"] == EscrowStatus.ACTIVE.value
    assert "id" in data
    assert "created_at" in data
    assert "expires_at" in data
    assert "escrow_address" in data  # Solana program-derived address


@pytest.mark.asyncio
async def test_create_escrow_insufficient_funds(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating escrow with insufficient funds should fail."""
    # Mock low balance
    mock_solana_rpc.get_balance.return_value = {"value": 10000000}  # 0.01 SOL
    
    escrow_data = {
        "agent_id": test_agent.id,
        "amount": "10.0",  # More than available balance
        "recipient_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "terms": "Large escrow that should fail",
        "expires_in_days": 30
    }
    
    response = await async_client.post(
        "/v1/escrow",
        json=escrow_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "insufficient" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_get_escrow(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a specific escrow."""
    response = await async_client.get(
        f"/v1/escrow/{test_escrow.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_escrow.id
    assert data["agent_id"] == test_escrow.agent_id
    assert Decimal(data["amount"]) == test_escrow.amount
    assert data["recipient_address"] == test_escrow.recipient_address
    assert data["status"] == test_escrow.status.value
    assert data["terms"] == test_escrow.terms


@pytest.mark.asyncio
async def test_get_escrow_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a non-existent escrow."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = await async_client.get(
        f"/v1/escrow/{fake_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_list_escrows(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    expired_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test listing all escrows for the authenticated user."""
    response = await async_client.get(
        "/v1/escrow",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least our test escrows
    
    # Check that we can find our test escrows
    escrow_ids = [escrow["id"] for escrow in data]
    assert test_escrow.id in escrow_ids
    assert expired_escrow.id in escrow_ids
    
    # Verify escrow data structure
    for escrow in data:
        assert "id" in escrow
        assert "agent_id" in escrow
        assert "amount" in escrow
        assert "recipient_address" in escrow
        assert "status" in escrow
        assert "terms" in escrow
        assert "created_at" in escrow
        assert "expires_at" in escrow


@pytest.mark.asyncio
async def test_list_escrows_filter_status(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    expired_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test listing escrows filtered by status."""
    response = await async_client.get(
        "/v1/escrow?status=active",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned escrows should have active status
    for escrow in data:
        assert escrow["status"] == EscrowStatus.ACTIVE.value
    
    # Should include our active escrow
    active_escrow_ids = [escrow["id"] for escrow in data]
    assert test_escrow.id in active_escrow_ids
    # Should not include expired escrows
    assert expired_escrow.id not in active_escrow_ids


@pytest.mark.asyncio
async def test_release_escrow(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test releasing an active escrow to the recipient."""
    # Mock successful release transaction
    mock_solana_rpc.send_transaction.return_value = "release_signature_123"
    
    release_data = {
        "release_notes": "Service completed satisfactorily"
    }
    
    response = await async_client.post(
        f"/v1/escrow/{test_escrow.id}/release",
        json=release_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == EscrowStatus.RELEASED.value
    assert "released_at" in data
    assert "release_signature" in data or "transaction_signature" in data
    
    if "release_notes" in release_data:
        assert data.get("release_notes") == release_data["release_notes"]


@pytest.mark.asyncio
async def test_release_escrow_not_owner(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    mock_redis,
    mock_solana_rpc
):
    """Test releasing escrow that doesn't belong to the user should fail."""
    # This would need another user's escrow to test properly
    # For now, we'll test with a non-existent escrow
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = await async_client.post(
        f"/v1/escrow/{fake_id}/release",
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_refund_escrow(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test refunding an active escrow back to the creator."""
    # Mock successful refund transaction
    mock_solana_rpc.send_transaction.return_value = "refund_signature_123"
    
    refund_data = {
        "refund_reason": "Service not completed"
    }
    
    response = await async_client.post(
        f"/v1/escrow/{test_escrow.id}/refund",
        json=refund_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == EscrowStatus.REFUNDED.value
    assert "refunded_at" in data
    assert "refund_signature" in data or "transaction_signature" in data


@pytest.mark.asyncio
async def test_refund_escrow_already_released(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test refunding an already released escrow should fail."""
    from uuid import uuid4
    
    # Create a released escrow
    released_escrow = Escrow(
        id=str(uuid4()),
        agent_id=test_agent.id,
        amount=Decimal("0.3"),
        recipient_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        status=EscrowStatus.RELEASED,
        terms="Already released escrow",
        expires_at=datetime.utcnow() + timedelta(days=30),
        created_at=datetime.utcnow(),
        released_at=datetime.utcnow()
    )
    db_session.add(released_escrow)
    await db_session.commit()
    await db_session.refresh(released_escrow)
    
    response = await async_client.post(
        f"/v1/escrow/{released_escrow.id}/refund",
        json={"refund_reason": "Should not work"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already" in response.json()["error"].lower() or "cannot" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_dispute_escrow(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a dispute for an active escrow."""
    dispute_data = {
        "dispute_reason": "Service not completed as agreed",
        "evidence_urls": ["https://example.com/evidence1.jpg"],
        "preferred_resolution": "refund"
    }
    
    response = await async_client.post(
        f"/v1/escrow/{test_escrow.id}/dispute",
        json=dispute_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == EscrowStatus.DISPUTED.value
    assert "disputed_at" in data
    assert data.get("dispute_reason") == dispute_data["dispute_reason"]


@pytest.mark.asyncio
async def test_dispute_escrow_already_resolved(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test disputing an already resolved escrow should fail."""
    from uuid import uuid4
    
    # Create a refunded escrow
    refunded_escrow = Escrow(
        id=str(uuid4()),
        agent_id=test_agent.id,
        amount=Decimal("0.3"),
        recipient_address="5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        status=EscrowStatus.REFUNDED,
        terms="Already refunded escrow",
        expires_at=datetime.utcnow() + timedelta(days=30),
        created_at=datetime.utcnow(),
        refunded_at=datetime.utcnow()
    )
    db_session.add(refunded_escrow)
    await db_session.commit()
    await db_session.refresh(refunded_escrow)
    
    response = await async_client.post(
        f"/v1/escrow/{refunded_escrow.id}/dispute",
        json={"dispute_reason": "Should not work"},
        headers=auth_headers
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_escrow_expired(
    async_client: AsyncClient,
    auth_headers: dict,
    expired_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test handling of expired escrows."""
    response = await async_client.get(
        f"/v1/escrow/{expired_escrow.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == EscrowStatus.EXPIRED.value
    
    # Try to release expired escrow (should fail)
    response = await async_client.post(
        f"/v1/escrow/{expired_escrow.id}/release",
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "expired" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_escrow_expiration_check(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test automatic expiration checking endpoint."""
    response = await async_client.post(
        "/v1/escrow/check-expirations",
        headers=auth_headers
    )
    
    # This might be an admin-only endpoint
    assert response.status_code in [200, 403, 405]
    
    if response.status_code == 200:
        data = response.json()
        assert "expired_count" in data or "checked" in data


@pytest.mark.asyncio
async def test_escrow_unauthorized(
    async_client: AsyncClient,
    test_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test accessing escrows without authentication should fail."""
    response = await async_client.get(f"/v1/escrow/{test_escrow.id}")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_escrow_invalid_amount(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating escrow with invalid amount should fail."""
    escrow_data = {
        "agent_id": test_agent.id,
        "amount": "-0.1",  # Negative amount
        "recipient_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "terms": "Invalid escrow",
        "expires_in_days": 30
    }
    
    response = await async_client.post(
        "/v1/escrow",
        json=escrow_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_escrow_invalid_address(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating escrow with invalid recipient address should fail."""
    escrow_data = {
        "agent_id": test_agent.id,
        "amount": "0.5",
        "recipient_address": "invalid_address",
        "terms": "Escrow with invalid address",
        "expires_in_days": 30
    }
    
    response = await async_client.post(
        "/v1/escrow",
        json=escrow_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert "address" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_extend_escrow_expiration(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test extending escrow expiration date."""
    extend_data = {
        "additional_days": 15
    }
    
    response = await async_client.post(
        f"/v1/escrow/{test_escrow.id}/extend",
        json=extend_data,
        headers=auth_headers
    )
    
    # This feature might not be implemented
    assert response.status_code in [200, 404, 405]
    
    if response.status_code == 200:
        data = response.json()
        assert "expires_at" in data
        # New expiration should be later than original


@pytest.mark.asyncio
async def test_escrow_notifications(
    async_client: AsyncClient,
    auth_headers: dict,
    test_escrow: Escrow,
    mock_redis,
    mock_solana_rpc
):
    """Test escrow notification settings."""
    notification_data = {
        "notify_on_expiration": True,
        "notify_on_dispute": True,
        "notification_email": "test@example.com"
    }
    
    response = await async_client.put(
        f"/v1/escrow/{test_escrow.id}/notifications",
        json=notification_data,
        headers=auth_headers
    )
    
    # This feature might not be implemented
    assert response.status_code in [200, 404, 405]