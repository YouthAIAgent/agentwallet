"""Wallet model -- custodial Solana wallets managed by the platform."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    address: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    wallet_type: Mapped[str] = mapped_column(String(50), default="agent")  # agent, treasury, escrow
    encrypted_key: Mapped[str] = mapped_column(String(1024), nullable=False)  # KMS-encrypted private key
    label: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="wallets")
    agent = relationship("Agent", back_populates="wallets", foreign_keys=[agent_id])
