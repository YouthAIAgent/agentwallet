"""ACP (Agent Commerce Protocol) models — 4-phase job lifecycle with memos."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class AcpJob(Base):
    """ACP job with 4-phase lifecycle: request → negotiation → transaction → evaluation → completed."""

    __tablename__ = "acp_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Agents
    buyer_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    seller_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    evaluator_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))

    # Service reference
    service_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id"))

    # ACP 4-phase state machine
    phase: Mapped[str] = mapped_column(String(50), default="request")
    # Phases: request, negotiation, transaction, evaluation, completed, cancelled, disputed

    # Job details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[dict] = mapped_column(JSON, default=dict)
    deliverables: Mapped[dict] = mapped_column(JSON, default=dict)

    # Negotiation terms (Proof of Agreement)
    agreed_terms: Mapped[dict | None] = mapped_column(JSON)
    agreed_price_lamports: Mapped[int] = mapped_column(BigInteger, default=0)

    # Fund transfer mode (agent manages buyer's principal)
    fund_transfer: Mapped[bool] = mapped_column(Boolean, default=False)
    principal_amount_lamports: Mapped[int | None] = mapped_column(BigInteger)

    # Escrow
    escrow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("escrows.id"))

    # Result
    result_data: Mapped[dict | None] = mapped_column(JSON)
    evaluation_notes: Mapped[str | None] = mapped_column(Text)
    evaluation_approved: Mapped[bool | None] = mapped_column(Boolean)
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5

    # Swarm reference
    swarm_task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("swarm_tasks.id"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    negotiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    transacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    buyer_agent = relationship("Agent", foreign_keys=[buyer_agent_id], lazy="noload")
    seller_agent = relationship("Agent", foreign_keys=[seller_agent_id], lazy="noload")
    evaluator_agent = relationship("Agent", foreign_keys=[evaluator_agent_id], lazy="noload")
    memos = relationship("AcpMemo", back_populates="job", lazy="noload")


class AcpMemo(Base):
    """Signed memo for ACP job communication and phase advancement."""

    __tablename__ = "acp_memos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("acp_jobs.id"), nullable=False)
    sender_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

    # Memo classification
    memo_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: job_request, agreement, transaction, deliverable, evaluation, general

    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[str | None] = mapped_column(String(128))  # Ed25519 from Solana wallet

    # On-chain anchor (Solana tx signature if stored on-chain)
    tx_signature: Mapped[str | None] = mapped_column(String(128))

    # Whether this memo advances the job phase
    advances_phase: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("AcpJob", back_populates="memos", lazy="noload")
    sender_agent = relationship("Agent", lazy="noload")


class ResourceOffering(Base):
    """Lightweight read-only data endpoint agents expose to other agents."""

    __tablename__ = "resource_offerings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint_path: Mapped[str] = mapped_column(String(500), nullable=False)  # e.g. /v1/resources/{id}/data
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    response_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage tracking
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    avg_response_ms: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    agent = relationship("Agent", lazy="noload")
