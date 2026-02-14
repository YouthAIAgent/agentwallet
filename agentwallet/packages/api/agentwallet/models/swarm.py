"""Agent Swarm models — cluster coordination for multi-agent tasks."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
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


class AgentSwarm(Base):
    """A cluster of agents coordinated by an orchestrator for complex multi-agent tasks."""

    __tablename__ = "agent_swarms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Orchestrator — the agent that coordinates the swarm
    orchestrator_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False
    )

    # Swarm configuration
    swarm_type: Mapped[str] = mapped_column(String(100), default="general")
    # Types: general, trading, research, content, security, data, custom
    max_members: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Performance
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    avg_completion_time_hours: Mapped[float] = mapped_column(Float, default=0.0)

    # Config
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    # {fee_split: {orchestrator: 0.2, workers: 0.8}, auto_assign: true}

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    orchestrator = relationship("Agent", lazy="noload")
    members = relationship("SwarmMember", back_populates="swarm", lazy="noload")
    tasks = relationship("SwarmTask", back_populates="swarm", lazy="noload")


class SwarmMember(Base):
    """An agent's membership in a swarm with a specific role."""

    __tablename__ = "swarm_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    swarm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_swarms.id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

    role: Mapped[str] = mapped_column(String(100), default="worker")
    # Roles: orchestrator, worker, specialist, evaluator
    specialization: Mapped[str | None] = mapped_column(String(255))
    # e.g. "data_analysis", "trading", "content_writing"

    is_contestable: Mapped[bool] = mapped_column(Boolean, default=True)
    # Whether other agents can challenge for this role
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Performance in swarm
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    swarm = relationship("AgentSwarm", back_populates="members", lazy="noload")
    agent = relationship("Agent", lazy="noload")


class SwarmTask(Base):
    """A complex task decomposed and distributed across swarm members."""

    __tablename__ = "swarm_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    swarm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_swarms.id"), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Task details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), default="general")

    # Decomposition
    subtasks: Mapped[list] = mapped_column(JSON, default=list)
    # [{id, description, assigned_agent_id, status, result}]

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending, decomposing, in_progress, aggregating, completed, failed

    # Results
    aggregated_result: Mapped[dict | None] = mapped_column(JSON)
    total_subtasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_subtasks: Mapped[int] = mapped_column(Integer, default=0)

    # Client who requested the task
    client_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    swarm = relationship("AgentSwarm", back_populates="tasks", lazy="noload")
    acp_jobs = relationship("AcpJob", lazy="noload")
