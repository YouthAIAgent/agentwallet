"""Audit event model -- immutable log of all state changes."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. wallet.created, transaction.submitted, policy.evaluated, escrow.funded

    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)  # user_id, agent_id, or "system"
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, agent, api_key, system

    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # wallet, transaction, escrow, ...
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)

    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_events_org_created", "org_id", "created_at"),
        Index("ix_audit_events_resource", "resource_type", "resource_id"),
        Index("ix_audit_events_event_type", "event_type"),
    )
