"""ERC-8004 models -- on-chain identity, feedback, and EVM wallets."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class ERC8004Identity(Base):
    __tablename__ = "erc8004_identities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), unique=True, nullable=False)
    token_id: Mapped[int | None] = mapped_column(BigInteger)
    evm_address: Mapped[str] = mapped_column(String(42), nullable=False)
    chain_id: Mapped[int] = mapped_column(Integer, default=8453)
    metadata_uri: Mapped[str | None] = mapped_column(String(2048))
    tx_hash: Mapped[str | None] = mapped_column(String(66))
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, confirmed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ERC8004Feedback(Base):
    __tablename__ = "erc8004_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    from_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    to_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text)
    tx_hash: Mapped[str | None] = mapped_column(String(66))
    task_reference: Mapped[str | None] = mapped_column(String(255))  # optional escrow/tx ID
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, confirmed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EVMWallet(Base):
    __tablename__ = "evm_wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    address: Mapped[str] = mapped_column(String(42), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)  # Fernet-encrypted private key
    chain_id: Mapped[int] = mapped_column(Integer, default=8453)
    label: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
