"""Transaction Engine -- SOL/SPL transfers with policy enforcement and fee collection.

Ported batch/semaphore pattern from moltfarm farm.py.
"""

import asyncio
import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.exceptions import (
    ApprovalRequiredError,
    IdempotencyConflictError,
    PolicyDeniedError,
)
from ..core.logging import get_logger
from ..core.solana import confirm_transaction, transfer_sol
from ..models.transaction import Transaction
from .fee_collector import FeeCollector
from .permission_engine import PermissionEngine
from .wallet_manager import WalletManager

logger = get_logger(__name__)

# Semaphore for batch transfers (from moltfarm pattern)
BATCH_SEMAPHORE = asyncio.Semaphore(5)


class TransactionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_mgr = WalletManager(db)
        self.permission_engine = PermissionEngine(db)
        self.fee_collector = FeeCollector()

    async def transfer_sol(
        self,
        org_id: uuid.UUID,
        org_tier: str,
        wallet_id: uuid.UUID,
        to_address: str,
        amount_lamports: int,
        agent_id: uuid.UUID | None = None,
        memo: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transaction:
        """Execute a SOL transfer with full policy check and fee deduction.

        Flow: idempotency check -> permission check -> fee calc -> build TX ->
              sign -> submit -> record -> (async confirm via worker)
        """
        # Idempotency check
        if idempotency_key:
            from sqlalchemy import select
            existing = await self.db.scalar(
                select(Transaction).where(Transaction.idempotency_key == idempotency_key)
            )
            if existing:
                if existing.org_id != org_id or existing.amount_lamports != amount_lamports:
                    raise IdempotencyConflictError(
                        f"Idempotency key '{idempotency_key}' already used with different params"
                    )
                return existing

        # Get wallet
        wallet = await self.wallet_mgr.get_wallet(wallet_id, org_id)

        # Permission check
        evaluation = await self.permission_engine.evaluate(
            org_id=org_id,
            agent_id=agent_id,
            wallet_id=wallet_id,
            to_address=to_address,
            amount_lamports=amount_lamports,
        )

        if evaluation.outcome == "deny":
            raise PolicyDeniedError(evaluation.denied_by, evaluation.denial_reason)

        if evaluation.outcome == "require_approval":
            req = await self.permission_engine.create_approval_request(
                org_id=org_id,
                transaction_request={
                    "wallet_id": str(wallet_id),
                    "to_address": to_address,
                    "amount_lamports": amount_lamports,
                    "agent_id": str(agent_id) if agent_id else None,
                    "memo": memo,
                },
                policy_id=evaluation.approval_policy_id,
            )
            raise ApprovalRequiredError(str(req.id))

        # Calculate fee
        fee_lamports = self.fee_collector.calculate_fee(amount_lamports, org_tier)
        settings = get_settings()

        # Create transaction record (pending)
        tx_record = Transaction(
            org_id=org_id,
            agent_id=agent_id,
            wallet_id=wallet_id,
            tx_type="transfer_sol",
            status="pending",
            from_address=wallet.address,
            to_address=to_address,
            amount_lamports=amount_lamports,
            platform_fee_lamports=fee_lamports,
            idempotency_key=idempotency_key,
            memo=memo,
        )
        self.db.add(tx_record)
        await self.db.flush()

        # Execute on-chain
        try:
            keypair = self.wallet_mgr._decrypt_keypair(wallet)
            async with httpx.AsyncClient(timeout=15) as client:
                signature = await transfer_sol(
                    client=client,
                    from_keypair=keypair,
                    to_address=to_address,
                    lamports=amount_lamports,
                    fee_lamports=fee_lamports,
                    fee_recipient=settings.platform_wallet_address or None,
                )
            tx_record.signature = signature
            tx_record.status = "submitted"
            logger.info(
                "transaction_submitted",
                tx_id=str(tx_record.id),
                signature=signature[:24],
                amount=amount_lamports,
                fee=fee_lamports,
            )
        except Exception as e:
            tx_record.status = "failed"
            tx_record.error = str(e)
            logger.error("transaction_failed", tx_id=str(tx_record.id), error=str(e))

        await self.db.flush()
        return tx_record

    async def batch_transfer_sol(
        self,
        org_id: uuid.UUID,
        org_tier: str,
        transfers: list[dict],
    ) -> list[Transaction]:
        """Execute multiple SOL transfers with semaphore-gated concurrency.

        Pattern from moltfarm farm.py batch command.
        """
        results = []

        async def _single(t: dict):
            async with BATCH_SEMAPHORE:
                return await self.transfer_sol(
                    org_id=org_id,
                    org_tier=org_tier,
                    wallet_id=t["from_wallet_id"],
                    to_address=t["to_address"],
                    amount_lamports=int(t["amount_sol"] * 1e9),
                    agent_id=t.get("agent_id"),
                    memo=t.get("memo"),
                    idempotency_key=t.get("idempotency_key"),
                )

        tasks = [_single(t) for t in transfers]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for item in completed:
            if isinstance(item, Transaction):
                results.append(item)
            else:
                logger.error("batch_transfer_error", error=str(item))

        return results

    async def get_transaction(
        self, tx_id: uuid.UUID, org_id: uuid.UUID
    ) -> Transaction:
        from ..core.exceptions import NotFoundError

        tx = await self.db.get(Transaction, tx_id)
        if not tx or tx.org_id != org_id:
            raise NotFoundError("Transaction", str(tx_id))
        return tx

    async def list_transactions(
        self,
        org_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
        wallet_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        from sqlalchemy import func, select

        query = select(Transaction).where(Transaction.org_id == org_id)
        count_query = select(func.count()).select_from(Transaction).where(
            Transaction.org_id == org_id
        )

        if agent_id:
            query = query.where(Transaction.agent_id == agent_id)
            count_query = count_query.where(Transaction.agent_id == agent_id)
        if wallet_id:
            query = query.where(Transaction.wallet_id == wallet_id)
            count_query = count_query.where(Transaction.wallet_id == wallet_id)
        if status:
            query = query.where(Transaction.status == status)
            count_query = count_query.where(Transaction.status == status)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(
            query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total or 0
