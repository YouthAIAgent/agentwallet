"""Agent-to-agent marketplace tables.

Revision ID: 003_marketplace
Revises: 002_erc8004
Create Date: 2026-02-12 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_marketplace"
down_revision: Union[str, None] = "002_erc8004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Service categories
    op.create_table(
        "service_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("service_categories.id")),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Services
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("price_lamports", sa.BigInteger, nullable=False),
        sa.Column("token_symbol", sa.String(20), server_default="USDC"),
        sa.Column("capabilities", sa.JSON, server_default="[]"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("estimated_duration_hours", sa.Integer),
        sa.Column("max_concurrent_jobs", sa.Integer, server_default="1"),
        sa.Column("requirements", sa.JSON, server_default="{}"),
        sa.Column("delivery_format", sa.String(100)),
        sa.Column("total_jobs", sa.Integer, server_default="0"),
        sa.Column("completed_jobs", sa.Integer, server_default="0"),
        sa.Column("avg_rating", sa.Float),
        sa.Column("success_rate", sa.Float, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_services_agent_id", "services", ["agent_id"])

    # Jobs
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("buyer_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("seller_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("escrow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("escrows.id")),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("input_data", sa.JSON, server_default="{}"),
        sa.Column("result_data", sa.JSON),
        sa.Column("buyer_notes", sa.Text),
        sa.Column("seller_notes", sa.Text),
        sa.Column("rating", sa.Integer),
        sa.Column("review", sa.Text),
        sa.Column("seller_response", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("deadline", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_jobs_service_id", "jobs", ["service_id"])
    op.create_index("ix_jobs_buyer_agent_id", "jobs", ["buyer_agent_id"])
    op.create_index("ix_jobs_seller_agent_id", "jobs", ["seller_agent_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # Agent reputations
    op.create_table(
        "agent_reputations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), unique=True, nullable=False),
        sa.Column("score", sa.Float, server_default="0.5"),
        sa.Column("total_jobs", sa.Integer, server_default="0"),
        sa.Column("completed_jobs", sa.Integer, server_default="0"),
        sa.Column("cancelled_jobs", sa.Integer, server_default="0"),
        sa.Column("disputed_jobs", sa.Integer, server_default="0"),
        sa.Column("avg_rating", sa.Float),
        sa.Column("rating_count", sa.Integer, server_default="0"),
        sa.Column("five_star_count", sa.Integer, server_default="0"),
        sa.Column("four_star_count", sa.Integer, server_default="0"),
        sa.Column("three_star_count", sa.Integer, server_default="0"),
        sa.Column("two_star_count", sa.Integer, server_default="0"),
        sa.Column("one_star_count", sa.Integer, server_default="0"),
        sa.Column("total_volume_lamports", sa.BigInteger, server_default="0"),
        sa.Column("total_earnings_lamports", sa.BigInteger, server_default="0"),
        sa.Column("total_spent_lamports", sa.BigInteger, server_default="0"),
        sa.Column("avg_completion_time_hours", sa.Float),
        sa.Column("on_time_delivery_rate", sa.Float, server_default="0"),
        sa.Column("response_time_hours", sa.Float),
        sa.Column("reliability_score", sa.Float, server_default="0.5"),
        sa.Column("quality_score", sa.Float, server_default="0.5"),
        sa.Column("communication_score", sa.Float, server_default="0.5"),
        sa.Column("first_job_at", sa.DateTime(timezone=True)),
        sa.Column("last_job_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_reputations_agent_id", "agent_reputations", ["agent_id"])

    # Job messages
    op.create_table(
        "job_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("sender_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("message_type", sa.String(50), server_default="chat"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("attachments", sa.JSON, server_default="{}"),
        sa.Column("is_system_message", sa.Boolean, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_messages_job_id", "job_messages", ["job_id"])
    op.create_index("ix_job_messages_sender_agent_id", "job_messages", ["sender_agent_id"])


def downgrade() -> None:
    op.drop_table("job_messages")
    op.drop_table("agent_reputations")
    op.drop_table("jobs")
    op.drop_table("services")
    op.drop_table("service_categories")
