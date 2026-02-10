"""Analytics daily rollup model -- pre-aggregated metrics."""

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)

    tx_count: Mapped[int] = mapped_column(Integer, default=0)
    total_spend_lamports: Mapped[int] = mapped_column(BigInteger, default=0)
    total_fees_lamports: Mapped[int] = mapped_column(BigInteger, default=0)
    unique_destinations: Mapped[int] = mapped_column(Integer, default=0)
    failed_tx_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_analytics_daily_org_date", "org_id", "date"),
        Index("ix_analytics_daily_agent_date", "agent_id", "date"),
    )
