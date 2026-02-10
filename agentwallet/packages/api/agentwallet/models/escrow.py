"""Escrow model -- locked funds with conditional release."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Escrow(Base):
    __tablename__ = "escrows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    funder_wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    recipient_address: Mapped[str] = mapped_column(String(64), nullable=False)
    arbiter_address: Mapped[str | None] = mapped_column(String(64))
    escrow_address: Mapped[str | None] = mapped_column(String(64))  # PDA address on-chain

    amount_lamports: Mapped[int] = mapped_column(BigInteger, nullable=False)
    token_mint: Mapped[str | None] = mapped_column(String(64))  # None for SOL

    status: Mapped[str] = mapped_column(String(50), default="created")
    # States: created -> funded -> released | refunded | disputed -> resolved | expired

    conditions: Mapped[dict] = mapped_column(JSONB, default=dict)
    # e.g. {"task_description": "...", "completion_criteria": "..."}

    fund_signature: Mapped[str | None] = mapped_column(String(128))
    release_signature: Mapped[str | None] = mapped_column(String(128))
    refund_signature: Mapped[str | None] = mapped_column(String(128))

    dispute_reason: Mapped[str | None] = mapped_column(Text)
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
