"""Billing subscription model -- on-chain USDC subscription billing."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class BillingSubscription(Base):
    """A paid tier subscription funded with USDC from the org's own wallet.

    Status lifecycle: active -> cancelled | expired.
    """

    __tablename__ = "billing_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # pro, enterprise
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, cancelled, expired
    amount_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    amount_raw: Mapped[int] = mapped_column(BigInteger, default=0)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_wallet_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payment_tx_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payment_signature: Mapped[str | None] = mapped_column(String(128))
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
