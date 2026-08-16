"""Human-facing task marketplace models.

A human posts a task, funds it in escrow, an agent executes it, and the
escrow releases on delivery — the core "AI task marketplace" flow.

States: posted -> funded -> assigned -> in_progress -> delivered -> released | refunded | disputed
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Task description
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="general")  # research, writing, coding, data, social
    capability: Mapped[str | None] = mapped_column(String(100))  # requested agent capability
    requirements: Mapped[dict] = mapped_column(JSON, default=dict)

    # Pricing (lamports)
    price_lamports: Mapped[int] = mapped_column(BigInteger, nullable=False)
    token_symbol: Mapped[str] = mapped_column(String(20), default="SOL")
    platform_fee_lamports: Mapped[int] = mapped_column(BigInteger, default=0)

    # Payment escrow
    escrow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("escrows.id"))
    funder_wallet_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"))

    # Agent assignment
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    agent_address: Mapped[str | None] = mapped_column(String(88))  # SOL address that receives payment

    # Lifecycle
    status: Mapped[str] = mapped_column(String(50), default="posted")
    # posted -> funded -> assigned -> in_progress -> delivered -> released | refunded | disputed
    failure_count: Mapped[int] = mapped_column(Integer, default=0)  # consecutive worker execution failures

    # Execution + delivery
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    result_data: Mapped[dict | None] = mapped_column(JSON)  # delivery payload
    delivery_notes: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(100))  # which agent/provider executed
    model: Mapped[str | None] = mapped_column(String(100))

    # Timestamps
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    escrow = relationship("Escrow", lazy="selectin")
    agent = relationship("Agent", lazy="joined")

    # For B2C marketplace: optional public listing
    is_listed: Mapped[bool] = mapped_column(Boolean, default=False)
