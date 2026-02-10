"""Policy model -- spending rules and controls for agents/wallets."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    rules: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Example rules:
    # {
    #   "spending_limit_lamports": 1000000000,  # 1 SOL per tx
    #   "daily_limit_lamports": 5000000000,     # 5 SOL per day
    #   "destination_whitelist": ["addr1", "addr2"],
    #   "destination_blacklist": ["addr3"],
    #   "token_whitelist": ["SOL", "USDC_mint"],
    #   "time_window": {"start": "09:00", "end": "17:00", "timezone": "UTC"},
    #   "require_approval_above_lamports": 500000000,
    # }

    scope_type: Mapped[str] = mapped_column(String(50), nullable=False)  # org, agent, wallet
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # agent_id or wallet_id
    priority: Mapped[int] = mapped_column(Integer, default=100)  # lower = higher priority
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
