"""Approval request model -- human approval workflow for high-value transactions."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    transaction_request: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Stores the full transaction parameters so it can be executed on approval

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, approved, rejected, expired
    required_approvals: Mapped[int] = mapped_column(Integer, default=1)

    decisions: Mapped[list] = mapped_column(JSONB, default=list)
    # e.g. [{"user_id": "...", "decision": "approved", "at": "..."}]

    policy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("policies.id"))
    reason: Mapped[str | None] = mapped_column(String(1024))

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
