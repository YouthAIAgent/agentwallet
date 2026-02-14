"""Transaction model -- all on-chain transactions initiated through the platform."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)

    tx_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # transfer_sol, transfer_spl, escrow_fund, escrow_release
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, submitted, confirmed, failed
    signature: Mapped[str | None] = mapped_column(String(128))

    from_address: Mapped[str] = mapped_column(String(64), nullable=False)
    to_address: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_lamports: Mapped[int] = mapped_column(BigInteger, nullable=False)
    token_mint: Mapped[str | None] = mapped_column(String(64))  # None for SOL

    platform_fee_lamports: Mapped[int] = mapped_column(BigInteger, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    memo: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_transactions_org_created", "org_id", "created_at"),
        Index("ix_transactions_status", "status"),
        Index("ix_transactions_agent", "agent_id"),
    )
