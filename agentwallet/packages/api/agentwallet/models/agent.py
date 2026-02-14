"""Agent model -- registered AI agents within an organization."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, inactive, suspended
    capabilities: Mapped[list] = mapped_column(JSON, default=list)  # ["trading", "payments", ...]
    default_wallet_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"))
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    is_public: Mapped[bool] = mapped_column(default=False)

    # ERC-8004 cross-chain identity
    erc8004_token_id: Mapped[int | None] = mapped_column(BigInteger)
    evm_address: Mapped[str | None] = mapped_column(String(42))
    erc8004_reputation: Mapped[float] = mapped_column(Float, default=0.0)
    erc8004_feedback_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization = relationship("Organization", back_populates="agents")
    default_wallet = relationship("Wallet", foreign_keys=[default_wallet_id], lazy="noload")
    wallets = relationship(
        "Wallet",
        back_populates="agent",
        foreign_keys="Wallet.agent_id",
        lazy="noload",
    )
