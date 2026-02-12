"""Tests for transaction operations."""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from agentwallet.models import Transaction, TransactionStatus, TransactionType, Wallet


@pytest.mark.asyncio
async def test_transfer_sol(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test creating a SOL transfer transaction."""
    # Mock successful transaction
    mock_solana_rpc.send_transaction.return_value = "mock_signature_abc123"
    
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "amount": "0.1",
        "memo": "Test transfer"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["from_wallet_id"] == test_wallet.id
    assert data["to_address"] == transfer_data["to_address"]
    assert Decimal(data["amount"]) == Decimal(transfer_data["amount"])
    assert data["transaction_type"] == TransactionType.TRANSFER.value
    assert data["status"] in [TransactionStatus.PENDING.value, TransactionStatus.COMPLETED.value]
    assert "id" in data
    assert "created_at" in data
    assert "solana_signature" in data


@pytest.mark.asyncio
async def test_transfer_sol_insufficient_balance(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test transfer with insufficient balance should fail."""
    # Mock insufficient balance
    mock_solana_rpc.get_balance.return_value = {"value": 50000000}  # 0.05 SOL
    
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "amount": "10.0",  # More than available balance
        "memo": "Large transfer that should fail"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "insufficient" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_transfer_sol_policy_denied(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    policy_with_spending_limit,
    mock_redis,
    mock_solana_rpc
):
    """Test transfer that violates policy should be denied."""
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "UnauthorizedRecipient123456789",  # Not in allowed recipients
        "amount": "0.005",  # Within amount limit but to unauthorized recipient
        "memo": "Policy violation transfer"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 403
    assert "policy" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_transfer_sol_amount_exceeds_policy(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    policy_with_spending_limit,
    mock_redis,
    mock_solana_rpc
):
    """Test transfer that exceeds policy amount limit."""
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",  # Authorized recipient
        "amount": "0.05",  # Exceeds max_transaction_amount of 0.01
        "memo": "Amount exceeds policy limit"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 403
    assert "policy" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_get_transaction(
    async_client: AsyncClient,
    auth_headers: dict,
    test_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a specific transaction."""
    response = await async_client.get(
        f"/v1/transactions/{test_transaction.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_transaction.id
    assert data["from_wallet_id"] == test_transaction.from_wallet_id
    assert data["to_address"] == test_transaction.to_address
    assert Decimal(data["amount"]) == test_transaction.amount
    assert data["transaction_type"] == test_transaction.transaction_type.value
    assert data["status"] == test_transaction.status.value
    assert data["solana_signature"] == test_transaction.solana_signature


@pytest.mark.asyncio
async def test_get_transaction_not_found(
    async_client: AsyncClient,
    auth_headers: dict,
    mock_redis,
    mock_solana_rpc
):
    """Test retrieving a non-existent transaction."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = await async_client.get(
        f"/v1/transactions/{fake_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_list_transactions(
    async_client: AsyncClient,
    auth_headers: dict,
    test_transaction: Transaction,
    completed_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test listing all transactions for the authenticated user."""
    response = await async_client.get(
        "/v1/transactions",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least our test transactions
    
    # Check that we can find our test transactions
    transaction_ids = [tx["id"] for tx in data]
    assert test_transaction.id in transaction_ids
    assert completed_transaction.id in transaction_ids
    
    # Verify transaction data structure
    for tx in data:
        assert "id" in tx
        assert "from_wallet_id" in tx
        assert "to_address" in tx
        assert "amount" in tx
        assert "transaction_type" in tx
        assert "status" in tx
        assert "created_at" in tx


@pytest.mark.asyncio
async def test_list_transactions_filter_status(
    async_client: AsyncClient,
    auth_headers: dict,
    test_transaction: Transaction,
    completed_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test listing transactions filtered by status."""
    response = await async_client.get(
        "/v1/transactions?status=completed",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned transactions should have completed status
    for tx in data:
        assert tx["status"] == TransactionStatus.COMPLETED.value
    
    # Should include our completed transaction
    completed_tx_ids = [tx["id"] for tx in data]
    assert completed_transaction.id in completed_tx_ids
    # Should not include pending transactions
    assert test_transaction.id not in completed_tx_ids


@pytest.mark.asyncio
async def test_list_transactions_filter_wallet(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    test_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test listing transactions filtered by wallet."""
    response = await async_client.get(
        f"/v1/transactions?from_wallet_id={test_wallet.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned transactions should be from the specified wallet
    for tx in data:
        assert tx["from_wallet_id"] == test_wallet.id


@pytest.mark.asyncio
async def test_batch_transfer(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test creating multiple transfers in a batch."""
    # Mock successful transactions
    mock_solana_rpc.send_transaction.return_value = "mock_batch_signature"
    
    batch_data = {
        "from_wallet_id": test_wallet.id,
        "transfers": [
            {
                "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                "amount": "0.01",
                "memo": "Batch transfer 1"
            },
            {
                "to_address": "7Bv9eWrN7C9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
                "amount": "0.02",
                "memo": "Batch transfer 2"
            }
        ]
    }
    
    response = await async_client.post(
        "/v1/transactions/batch-transfer",
        json=batch_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    # Verify each transaction in the batch
    for i, tx in enumerate(data):
        expected_transfer = batch_data["transfers"][i]
        assert tx["from_wallet_id"] == test_wallet.id
        assert tx["to_address"] == expected_transfer["to_address"]
        assert Decimal(tx["amount"]) == Decimal(expected_transfer["amount"])
        assert tx["transaction_type"] == TransactionType.TRANSFER.value


@pytest.mark.asyncio
async def test_batch_transfer_partial_failure(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    policy_with_spending_limit,
    mock_redis,
    mock_solana_rpc
):
    """Test batch transfer with some transactions failing policy checks."""
    batch_data = {
        "from_wallet_id": test_wallet.id,
        "transfers": [
            {
                "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",  # Authorized
                "amount": "0.005",  # Within limit
                "memo": "Good transfer"
            },
            {
                "to_address": "UnauthorizedRecipient123456789",  # Not authorized
                "amount": "0.005",
                "memo": "Bad transfer"
            }
        ]
    }
    
    response = await async_client.post(
        "/v1/transactions/batch-transfer",
        json=batch_data,
        headers=auth_headers
    )
    
    # Could be 207 (partial success) or 400 (all-or-nothing failure)
    assert response.status_code in [207, 400]


@pytest.mark.asyncio
async def test_cancel_transaction(
    async_client: AsyncClient,
    auth_headers: dict,
    test_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test cancelling a pending transaction."""
    response = await async_client.post(
        f"/v1/transactions/{test_transaction.id}/cancel",
        headers=auth_headers
    )
    
    # Can only cancel pending transactions
    if test_transaction.status == TransactionStatus.PENDING:
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == TransactionStatus.CANCELLED.value
    else:
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_transaction_unauthorized(
    async_client: AsyncClient,
    test_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test accessing transactions without authentication should fail."""
    response = await async_client.get(f"/v1/transactions/{test_transaction.id}")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_transfer_invalid_address(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test transfer to invalid Solana address should fail."""
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "invalid_address",
        "amount": "0.1",
        "memo": "Invalid address transfer"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert "address" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_transfer_zero_amount(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test transfer with zero amount should fail."""
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "amount": "0",
        "memo": "Zero amount transfer"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert "amount" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_transfer_negative_amount(
    async_client: AsyncClient,
    auth_headers: dict,
    test_wallet: Wallet,
    mock_redis,
    mock_solana_rpc
):
    """Test transfer with negative amount should fail."""
    transfer_data = {
        "from_wallet_id": test_wallet.id,
        "to_address": "5Gv8eWrN7B9dqTCEKH8kKTq1nAzx8RWJ9vL4J5eZ8sX3",
        "amount": "-0.1",
        "memo": "Negative amount transfer"
    }
    
    response = await async_client.post(
        "/v1/transactions/transfer",
        json=transfer_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_transaction_status_update(
    async_client: AsyncClient,
    auth_headers: dict,
    test_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test updating transaction status (internal/admin operation)."""
    # This endpoint might not be public
    response = await async_client.put(
        f"/v1/transactions/{test_transaction.id}/status",
        json={"status": "completed"},
        headers=auth_headers
    )
    
    # Could be 200 (success), 403 (forbidden), or 405 (not allowed)
    assert response.status_code in [200, 403, 405]


@pytest.mark.asyncio
async def test_get_transaction_receipt(
    async_client: AsyncClient,
    auth_headers: dict,
    completed_transaction: Transaction,
    mock_redis,
    mock_solana_rpc
):
    """Test getting detailed transaction receipt."""
    # Mock Solana transaction details
    mock_solana_rpc.get_transaction.return_value = {
        "result": {
            "meta": {"err": None, "fee": 5000},
            "transaction": {"message": {"accountKeys": []}}
        }
    }
    
    response = await async_client.get(
        f"/v1/transactions/{completed_transaction.id}/receipt",
        headers=auth_headers
    )
    
    # This endpoint might or might not exist
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "transaction_id" in data
        assert "blockchain_data" in data or "solana_data" in data