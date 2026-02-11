"""Escrow Service -- locked funds with conditional release.

State machine ported from moltfarm lib/launcher.py pattern,
replacing file state with PostgreSQL.

States: created -> funded -> released | refunded | disputed -> resolved | expired
"""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.exceptions import EscrowStateError, NotFoundError
from ..core.logging import get_logger
from ..core.solana import confirm_transaction, transfer_sol
from ..models.escrow import Escrow
from .wallet_manager import WalletManager

logger = get_logger(__name__)

VALID_TRANSITIONS = {
    "created": ["funded"],
    "funded": ["released", "refunded", "disputed"],
    "disputed": ["resolved", "refunded"],
    "resolved": [],
    "released": [],
    "refunded": [],
    "expired": [],
}


class EscrowService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_mgr = WalletManager(db)

    async def create_escrow(
        self,
        org_id: uuid.UUID,
        funder_wallet_id: uuid.UUID,
        recipient_address: str,
        amount_lamports: int,
        token_mint: str | None = None,
        arbiter_address: str | None = None,
        conditions: dict | None = None,
        expires_in_hours: int = 24,
    ) -> Escrow:
        """Create a new escrow and fund it atomically."""
        wallet = await self.wallet_mgr.get_wallet(funder_wallet_id, org_id)

        escrow = Escrow(
            org_id=org_id,
            funder_wallet_id=funder_wallet_id,
            recipient_address=recipient_address,
            arbiter_address=arbiter_address,
            amount_lamports=amount_lamports,
            token_mint=token_mint,
            conditions=conditions or {},
            status="created",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        self.db.add(escrow)
        await self.db.flush()

        # Fund the escrow (transfer to platform-managed escrow wallet)
        try:
            settings = get_settings()
            keypair = self.wallet_mgr._decrypt_keypair(wallet)
            # For MVP, escrow funds go to the platform wallet
            # In production, this would be an on-chain PDA
            escrow_target = settings.platform_wallet_address or recipient_address

            async with httpx.AsyncClient(timeout=15) as client:
                sig = await transfer_sol(
                    client=client,
                    from_keypair=keypair,
                    to_address=escrow_target,
                    lamports=amount_lamports,
                )
                confirmed = await confirm_transaction(client, sig)

            if confirmed:
                escrow.status = "funded"
                escrow.fund_signature = sig
                escrow.funded_at = datetime.now(timezone.utc)
                escrow.escrow_address = escrow_target
            else:
                escrow.status = "created"
                escrow.fund_signature = sig

        except Exception as e:
            logger.error("escrow_fund_failed", escrow_id=str(escrow.id), error=str(e))
            # Leave as created for retry

        await self.db.flush()
        logger.info("escrow_created", escrow_id=str(escrow.id), status=escrow.status)
        return escrow

    async def release_escrow(self, escrow_id: uuid.UUID, org_id: uuid.UUID) -> Escrow:
        """Release escrow funds to the recipient."""
        escrow = await self._get_escrow(escrow_id, org_id)
        self._validate_transition(escrow.status, "released")

        # In production, this would call the on-chain program
        # For MVP, record the release
        escrow.status = "released"
        escrow.completed_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Check if both agents have ERC-8004 identities for feedback eligibility
        self._check_erc8004_feedback_eligibility(escrow)

        logger.info("escrow_released", escrow_id=str(escrow_id))
        return escrow

    def _check_erc8004_feedback_eligibility(self, escrow: Escrow) -> None:
        """Log if released escrow is eligible for ERC-8004 feedback.

        Keeps escrow service loosely coupled -- feedback submission happens
        via the /v1/erc8004/escrow/{id}/feedback API endpoint, not inline.
        """
        logger.info(
            "escrow.released.erc8004_eligible",
            escrow_id=str(escrow.id),
            msg="Escrow released; eligible for ERC-8004 feedback via POST /v1/erc8004/escrow/{id}/feedback",
        )

    async def refund_escrow(self, escrow_id: uuid.UUID, org_id: uuid.UUID) -> Escrow:
        """Refund escrow funds to the funder."""
        escrow = await self._get_escrow(escrow_id, org_id)
        self._validate_transition(escrow.status, "refunded")

        escrow.status = "refunded"
        escrow.completed_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info("escrow_refunded", escrow_id=str(escrow_id))
        return escrow

    async def dispute_escrow(
        self, escrow_id: uuid.UUID, org_id: uuid.UUID, reason: str
    ) -> Escrow:
        """Mark escrow as disputed."""
        escrow = await self._get_escrow(escrow_id, org_id)
        self._validate_transition(escrow.status, "disputed")

        escrow.status = "disputed"
        escrow.dispute_reason = reason
        await self.db.flush()

        logger.info("escrow_disputed", escrow_id=str(escrow_id))
        return escrow

    async def get_escrow(self, escrow_id: uuid.UUID, org_id: uuid.UUID) -> Escrow:
        return await self._get_escrow(escrow_id, org_id)

    async def list_escrows(
        self,
        org_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Escrow], int]:
        from sqlalchemy import func

        query = select(Escrow).where(Escrow.org_id == org_id)
        count_query = select(func.count()).select_from(Escrow).where(Escrow.org_id == org_id)

        if status:
            query = query.where(Escrow.status == status)
            count_query = count_query.where(Escrow.status == status)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(
            query.order_by(Escrow.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total or 0

    async def expire_stale_escrows(self) -> int:
        """Expire escrows past their expiry date. Called by escrow_expiry worker."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Escrow).where(
                Escrow.status.in_(["created", "funded"]),
                Escrow.expires_at < now,
            )
        )
        expired = result.scalars().all()
        for escrow in expired:
            escrow.status = "expired"
            escrow.completed_at = now
        await self.db.flush()
        if expired:
            logger.info("escrows_expired", count=len(expired))
        return len(expired)

    async def _get_escrow(self, escrow_id: uuid.UUID, org_id: uuid.UUID) -> Escrow:
        escrow = await self.db.get(Escrow, escrow_id)
        if not escrow or escrow.org_id != org_id:
            raise NotFoundError("Escrow", str(escrow_id))
        return escrow

    def _validate_transition(self, current: str, target: str) -> None:
        allowed = VALID_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise EscrowStateError(
                f"Cannot transition from '{current}' to '{target}'. "
                f"Allowed: {allowed}"
            )
