"""Marketplace models -- Agent-to-Agent service marketplace."""

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


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_lamports: Mapped[int] = mapped_column(BigInteger, nullable=False)
    token_symbol: Mapped[str] = mapped_column(String(20), default="USDC")
    capabilities: Mapped[list] = mapped_column(JSON, default=list)  # ["trading", "analysis", "research"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Service metadata
    estimated_duration_hours: Mapped[int | None] = mapped_column(Integer)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, default=1)
    requirements: Mapped[dict] = mapped_column(JSON, default=dict)  # Input requirements, constraints
    delivery_format: Mapped[str | None] = mapped_column(String(100))  # "json", "report", "data_file"

    # Performance metrics
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float | None] = mapped_column(Float)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)  # completed/total

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    agent = relationship("Agent", backref="services", lazy="noload")
    jobs = relationship("Job", back_populates="service", lazy="noload")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    buyer_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    seller_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    escrow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("escrows.id"))

    status: Mapped[str] = mapped_column(String(50), default="pending")
    # States: pending -> active -> completed | cancelled | disputed -> resolved

    # Job details
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Job requirements from buyer
    result_data: Mapped[dict | None] = mapped_column(JSON)  # Delivered results from seller

    # Communication
    buyer_notes: Mapped[str | None] = mapped_column(Text)  # Initial requirements/notes
    seller_notes: Mapped[str | None] = mapped_column(Text)  # Progress updates, delivery notes

    # Feedback
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5 stars
    review: Mapped[str | None] = mapped_column(Text)  # Written review
    seller_response: Mapped[str | None] = mapped_column(Text)  # Seller response to review

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    service = relationship("Service", back_populates="jobs", lazy="noload")
    buyer_agent = relationship("Agent", foreign_keys=[buyer_agent_id], backref="bought_jobs", lazy="noload")
    seller_agent = relationship("Agent", foreign_keys=[seller_agent_id], backref="sold_jobs", lazy="noload")
    escrow = relationship("Escrow", backref="marketplace_jobs", lazy="noload")


class AgentReputation(Base):
    __tablename__ = "agent_reputations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), unique=True, nullable=False
    )

    # Core reputation metrics
    score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0 normalized score
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    cancelled_jobs: Mapped[int] = mapped_column(Integer, default=0)
    disputed_jobs: Mapped[int] = mapped_column(Integer, default=0)

    # Rating analytics
    avg_rating: Mapped[float | None] = mapped_column(Float)  # 1.0 to 5.0
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    five_star_count: Mapped[int] = mapped_column(Integer, default=0)
    four_star_count: Mapped[int] = mapped_column(Integer, default=0)
    three_star_count: Mapped[int] = mapped_column(Integer, default=0)
    two_star_count: Mapped[int] = mapped_column(Integer, default=0)
    one_star_count: Mapped[int] = mapped_column(Integer, default=0)

    # Financial metrics
    total_volume_lamports: Mapped[int] = mapped_column(BigInteger, default=0)  # Total transaction volume
    total_earnings_lamports: Mapped[int] = mapped_column(BigInteger, default=0)  # As seller
    total_spent_lamports: Mapped[int] = mapped_column(BigInteger, default=0)  # As buyer

    # Performance metrics
    avg_completion_time_hours: Mapped[float | None] = mapped_column(Float)
    on_time_delivery_rate: Mapped[float] = mapped_column(Float, default=0.0)  # % delivered by deadline
    response_time_hours: Mapped[float | None] = mapped_column(Float)  # Avg response to job acceptance

    # Behavioral factors
    reliability_score: Mapped[float] = mapped_column(Float, default=0.5)  # Based on completion rate, punctuality
    quality_score: Mapped[float] = mapped_column(Float, default=0.5)  # Based on ratings, reviews
    communication_score: Mapped[float] = mapped_column(Float, default=0.5)  # Response times, clarity

    # Timestamps
    first_job_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_job_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    agent = relationship("Agent", backref="reputation", lazy="noload")


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("service_categories.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Self-referential relationship for subcategories
    parent = relationship("ServiceCategory", remote_side=[id], backref="subcategories", lazy="noload")


class JobMessage(Base):
    __tablename__ = "job_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    sender_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

    message_type: Mapped[str] = mapped_column(String(50), default="chat")  # chat, update, delivery, dispute
    content: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[dict] = mapped_column(JSON, default=dict)  # File URLs, metadata

    is_system_message: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", backref="messages", lazy="noload")
    sender = relationship("Agent", backref="sent_job_messages", lazy="noload")
