"""Token Service -- SPL token transfer service for stablecoins."""

import uuid
from typing import Any, Dict

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.exceptions import (
    IdempotencyConflictError,
    InsufficientBalanceError,
    ValidationError,
)
from ..core.logging import get_logger
from ..core.solana import (
    confirm_transaction,
    get_token_accounts,
    get_token_balance,
    transfer_spl_token,
)
from ..models.transaction import Transaction
from .fee_collector import FeeCollector
from .permission_engine import PermissionEngine
from .wallet_manager import WalletManager

logger = get_logger(__name__)


class TokenService:
    """SPL Token transfer service for stablecoins."""

    SUPPORTED_TOKENS = {
        "USDC": {
            "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # devnet USDC
            "decimals": 6,
            "name": "USD Coin",
        },
        "USDT": {
            "mint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # devnet USDT
            "decimals": 6,
            "name": "Tether",
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_mgr = WalletManager(db)
        self.permission_engine = PermissionEngine(db)
        self.fee_collector = FeeCollector()

    async def transfer_token(
        self,
        org_id: uuid.UUID,
        org_tier: str,
        from_wallet_id: uuid.UUID,
        to_address: str,
        token_symbol: str,
        amount: float,
        agent_id: uuid.UUID | None = None,
        memo: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transaction:
        """Transfer SPL tokens (USDC/USDT) with policy enforcement.

        Args:
            org_id: Organization ID
            org_tier: Organization tier (for rate limits)
            from_wallet_id: Source wallet ID
            to_address: Recipient Solana address
            token_symbol: Token symbol (USDC, USDT)
            amount: Amount in human-readable format (e.g., 10.50)
            agent_id: Optional agent ID
            memo: Optional transaction memo
            idempotency_key: Optional idempotency key

        Returns:
            Transaction object

        Raises:
            ValidationError: Invalid token symbol or amount
            NotFoundError: Wallet not found
            InsufficientBalanceError: Not enough tokens
            PolicyDeniedError: Policy violation
            ApprovalRequiredError: Approval required
        """
        # Validate token
        if token_symbol not in self.SUPPORTED_TOKENS:
            raise ValidationError(f"Unsupported token: {token_symbol}")

        token_config = self.SUPPORTED_TOKENS[token_symbol]

        # Validate amount
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        # Convert to smallest unit
        amount_raw = int(amount * (10 ** token_config["decimals"]))

        # Check idempotency
        if idempotency_key:
            existing = await self._check_idempotency(org_id, idempotency_key)
            if existing:
                raise IdempotencyConflictError(
                    f"Idempotency key '{idempotency_key}' already used for transaction {existing.id}"
                )

        # Get wallet and validate ownership (get_wallet checks org_id)
        wallet = await self.wallet_mgr.get_wallet(from_wallet_id, org_id)

        # Decrypt private key
        from_keypair = self.wallet_mgr._decrypt_keypair(wallet)
        from_address = str(from_keypair.pubkey())

        # Check token balance
        async with httpx.AsyncClient() as client:
            balance_info = await get_token_balance(client, from_address, token_config["mint"])

        if balance_info["amount"] < amount_raw:
            raise InsufficientBalanceError(available=balance_info["amount"], required=amount_raw)

        # Get USD value for policy checking (simplified - use 1:1 for stablecoins)
        usd_amount = amount

        # Check policies
        await self.permission_engine.check_transfer_policy(
            org_id=org_id,
            wallet_id=from_wallet_id,
            amount_usd=usd_amount,
            agent_id=agent_id,
        )

        # Calculate platform fee
        fee_lamports = self.fee_collector.calculate_fee(usd_amount, org_tier)
        fee_recipient = get_settings().platform_fee_address

        # Create transaction record
        tx = Transaction(
            org_id=org_id,
            agent_id=agent_id,
            wallet_id=from_wallet_id,
            tx_type="token_transfer",
            status="pending",
            from_address=from_address,
            to_address=to_address,
            amount_lamports=amount_raw,  # Store raw amount
            token_mint=token_config["mint"],
            platform_fee_lamports=fee_lamports,
            memo=memo,
            idempotency_key=idempotency_key,
        )
        self.db.add(tx)
        await self.db.flush()

        try:
            # Execute transfer
            async with httpx.AsyncClient() as client:
                signature = await transfer_spl_token(
                    client=client,
                    from_keypair=from_keypair,
                    to_address=to_address,
                    mint=token_config["mint"],
                    amount=amount_raw,
                    fee_lamports=fee_lamports,
                    fee_recipient=fee_recipient,
                )

            # Update transaction with signature
            tx.signature = signature
            tx.status = "submitted"
            await self.db.flush()

            # Background confirmation (fire and forget)
            import asyncio

            asyncio.create_task(self._confirm_transaction(tx.id, signature))

            logger.info(
                "token_transfer_submitted",
                tx_id=str(tx.id),
                token=token_symbol,
                amount=amount,
                signature=signature[:24],
            )

            return tx

        except Exception as e:
            tx.status = "failed"
            tx.error = str(e)
            await self.db.flush()
            raise

    async def get_token_balance(self, wallet_address: str, token_symbol: str) -> Dict[str, Any]:
        """Get SPL token balance for a wallet.

        Args:
            wallet_address: Wallet Solana address
            token_symbol: Token symbol (USDC, USDT)

        Returns:
            Dict with balance info

        Raises:
            ValidationError: Invalid token symbol
        """
        if token_symbol not in self.SUPPORTED_TOKENS:
            raise ValidationError(f"Unsupported token: {token_symbol}")

        token_config = self.SUPPORTED_TOKENS[token_symbol]

        async with httpx.AsyncClient() as client:
            balance_info = await get_token_balance(client, wallet_address, token_config["mint"])

        return {
            "token_symbol": token_symbol,
            "mint_address": token_config["mint"],
            "amount": balance_info["ui_amount"],  # Human-readable amount
            "amount_raw": balance_info["amount"],  # Raw amount
            "decimals": balance_info["decimals"],
        }

    async def get_all_token_balances(self, wallet_address: str) -> Dict[str, Any]:
        """Get all supported token balances for a wallet.

        Args:
            wallet_address: Wallet Solana address

        Returns:
            Dict with SOL balance and all token balances
        """
        async with httpx.AsyncClient() as client:
            # Get SOL balance
            from ..core.solana import get_balance_sol

            sol_balance = await get_balance_sol(client, wallet_address)

            # Get all token accounts
            token_accounts = await get_token_accounts(client, wallet_address)

        # Map token accounts to supported tokens
        token_balances = []
        for symbol, config in self.SUPPORTED_TOKENS.items():
            balance_info = None
            for account in token_accounts:
                if account["mint"] == config["mint"]:
                    balance_info = account
                    break

            if balance_info:
                token_balances.append(
                    {
                        "token_symbol": symbol,
                        "mint_address": config["mint"],
                        "amount": balance_info["ui_amount"],
                        "amount_raw": balance_info["amount"],
                        "decimals": balance_info["decimals"],
                    }
                )
            else:
                # Token account doesn't exist - zero balance
                token_balances.append(
                    {
                        "token_symbol": symbol,
                        "mint_address": config["mint"],
                        "amount": 0.0,
                        "amount_raw": 0,
                        "decimals": config["decimals"],
                    }
                )

        return {
            "address": wallet_address,
            "sol_balance": sol_balance or 0.0,
            "tokens": token_balances,
        }

    async def _check_idempotency(self, org_id: uuid.UUID, idempotency_key: str) -> Transaction | None:
        """Check for existing transaction with same idempotency key."""
        from sqlalchemy import select

        stmt = select(Transaction).where(
            Transaction.org_id == org_id,
            Transaction.idempotency_key == idempotency_key,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _confirm_transaction(self, tx_id: uuid.UUID, signature: str):
        """Background task to confirm transaction and update status."""
        try:
            async with httpx.AsyncClient() as client:
                confirmed = await confirm_transaction(client, signature)

            # Update transaction status
            from sqlalchemy import func, update

            from ..core.database import get_session_factory

            # Create a new session for this background task
            factory = get_session_factory()
            async with factory() as session:
                if confirmed:
                    stmt = (
                        update(Transaction)
                        .where(Transaction.id == tx_id)
                        .values(
                            status="confirmed",
                            confirmed_at=func.now(),
                        )
                    )
                else:
                    stmt = (
                        update(Transaction)
                        .where(Transaction.id == tx_id)
                        .values(
                            status="timeout",
                            error="Transaction confirmation timeout",
                        )
                    )

                await session.execute(stmt)
                await session.commit()

        except Exception as e:
            logger.error(
                "token_confirmation_failed",
                tx_id=str(tx_id),
                signature=signature[:24],
                error=str(e),
            )
