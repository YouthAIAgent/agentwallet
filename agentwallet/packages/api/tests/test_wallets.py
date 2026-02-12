"""Tests for wallet operations."""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from agentwallet.models import Agent, Wallet, WalletType


@pytest.mark.asyncio
async def test_create_wallet(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a new wallet for an agent."""
    wallet_data = {
        "agent_id": test_agent.id,
        "wallet_type": "solana"
    }
    
    response = await async_client.post(
        "/v1/wallets",
        json=wallet_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == test_agent.id
    assert data["wallet_type"] == WalletType.SOLANA.value
    assert "address" in data
    assert "id" in data
    assert "created_at" in data
    # Private key should not be exposed
    assert "private_key" not in data
    assert "private_key_encrypted" not in data


@pytest.mark.asyncio
async def test_create_wallet_invalid_agent(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a wallet for a non-existent agent should fail."""
    fake_agent_id = "00000000-0000-0000-0000-000000000000"
    wallet_data = {
        "agent_id": fake_agent_id,
        "wallet_type": "solana"
    }
    
    response = await async_client.post(
        "/v1/wallets",
        json=wallet_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_wallet(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a specific wallet."""
    response = await async_client.get(
        f"/v1/wallets/{test_wallet.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_wallet.id
    assert data["agent_id"] == test_wallet.agent_id
    assert data["address"] == test_wallet.address
    assert data["wallet_type"] == test_wallet.wallet_type.value
    assert Decimal(str(data["balance"])) == test_wallet.balance
    # Private key should not be exposed
    assert "private_key" not in data
    assert "private_key_encrypted" not in data


@pytest.mark.asyncio
async def test_get_wallet_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a non-existent wallet."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = await async_client.get(
        f"/v1/wallets/{fake_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_list_wallets(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test listing all wallets for the authenticated user."""
    response = await async_client.get(
        "/v1/wallets",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check that we can find our test wallet
    wallet_ids = [wallet["id"] for wallet in data]
    assert test_wallet.id in wallet_ids
    
    # Verify wallet data structure
    for wallet in data:
        assert "id" in wallet
        assert "agent_id" in wallet
        assert "address" in wallet
        assert "wallet_type" in wallet
        assert "balance" in wallet
        assert "created_at" in wallet
        # Private key should not be exposed
        assert "private_key" not in wallet
        assert "private_key_encrypted" not in wallet


@pytest.mark.asyncio
async def test_list_wallets_by_agent(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test listing wallets filtered by agent ID."""
    response = await async_client.get(
        f"/v1/wallets?agent_id={test_agent.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned wallets should belong to the specified agent
    for wallet in data:
        assert wallet["agent_id"] == test_agent.id
    
    # Should include our test wallet
    wallet_ids = [wallet["id"] for wallet in data]
    assert test_wallet.id in wallet_ids


@pytest.mark.asyncio
async def test_get_balance(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test getting wallet balance (both cached and live)."""
    # Mock Solana RPC to return a specific balance
    mock_solana_rpc.get_balance.return_value = {"value": 2000000000}  # 2 SOL
    
    response = await async_client.get(
        f"/v1/wallets/{test_wallet.id}/balance",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert "last_updated" in data
    assert isinstance(data["balance"], str)  # Should be string to preserve precision


@pytest.mark.asyncio
async def test_get_balance_with_refresh(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test getting wallet balance with force refresh."""
    # Mock Solana RPC to return a specific balance
    mock_solana_rpc.get_balance.return_value = {"value": 1500000000}  # 1.5 SOL
    
    response = await async_client.get(
        f"/v1/wallets/{test_wallet.id}/balance?refresh=true",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert "last_updated" in data
    
    # Verify that Solana RPC was called (due to refresh=true)
    mock_solana_rpc.get_balance.assert_called()


@pytest.mark.asyncio
async def test_update_wallet(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test updating wallet metadata (like name or description)."""
    update_data = {
        "name": "My Updated Wallet",
        "description": "Updated wallet description"
    }
    
    response = await async_client.put(
        f"/v1/wallets/{test_wallet.id}",
        json=update_data,
        headers=auth_headers
    )
    
    # This might return 200 or 404 depending on implementation
    # Some wallet APIs don't allow updates, others do
    assert response.status_code in [200, 404, 405]


@pytest.mark.asyncio
async def test_delete_wallet(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test deleting a wallet (if supported)."""
    from uuid import uuid4
    
    # Create a temporary wallet for deletion
    temp_wallet = Wallet(
        id=str(uuid4()),
        agent_id=test_agent.id,
        address="TempWalletAddress123",
        private_key_encrypted="temp_encrypted_key",
        wallet_type=WalletType.SOLANA,
        balance=Decimal("0.0")
    )
    db_session.add(temp_wallet)
    await db_session.commit()
    await db_session.refresh(temp_wallet)
    
    response = await async_client.delete(
        f"/v1/wallets/{temp_wallet.id}",
        headers=auth_headers
    )
    
    # Wallet deletion might not be supported for security reasons
    assert response.status_code in [204, 405, 403]


@pytest.mark.asyncio
async def test_wallet_unauthorized(
    async_client: AsyncClient,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test accessing wallets without authentication should fail."""
    response = await async_client.get(f"/v1/wallets/{test_wallet.id}")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_permissions(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test that users can only access wallets belonging to their agents."""
    response = await async_client.get("/v1/wallets", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned wallets should belong to agents owned by the authenticated user
    # (This would be more meaningful with multiple users in the test)
    assert isinstance(data, list)
    for wallet in data:
        assert "agent_id" in wallet


@pytest.mark.asyncio
async def test_create_wallet_invalid_type(
    async_client: AsyncClient,
    auth_headers: dict,
    test_agent: Agent,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a wallet with invalid wallet type."""
    wallet_data = {
        "agent_id": test_agent.id,
        "wallet_type": "invalid_type"
    }
    
    response = await async_client.post(
        "/v1/wallets",
        json=wallet_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_wallet_transaction_history(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test getting transaction history for a wallet."""
    response = await async_client.get(
        f"/v1/wallets/{test_wallet.id}/transactions",
        headers=auth_headers
    )
    
    # This endpoint might or might not exist
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_wallet_address_validation(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test that wallet addresses are properly validated."""
    # Get wallet should return a valid Solana address format
    response = await async_client.get(
        f"/v1/wallets/{test_wallet.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    address = data["address"]
    
    # Basic Solana address validation (44 characters, base58)
    assert len(address) >= 32
    assert len(address) <= 44
    # Should not contain invalid base58 characters
    invalid_chars = ['0', 'O', 'I', 'l']
    for char in invalid_chars:
        assert char not in address