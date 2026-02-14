"""Add ACP (Agent Commerce Protocol) and Agent Swarm tables.

Revision ID: 006_acp_and_swarms
Revises: 005_pda_bigint
Create Date: 2026-02-14 22:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "006_acp_and_swarms"
down_revision: Union[str, None] = "005_pda_bigint"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Agent Swarms ──
    op.create_table(
        "agent_swarms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("orchestrator_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("swarm_type", sa.String(100), server_default="general"),
        sa.Column("max_members", sa.Integer, server_default="10"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_public", sa.Boolean, server_default=sa.text("false")),
        sa.Column("total_tasks", sa.Integer, server_default="0"),
        sa.Column("completed_tasks", sa.Integer, server_default="0"),
        sa.Column("avg_completion_time_hours", sa.Float, server_default="0.0"),
        sa.Column("config", sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "swarm_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("swarm_id", UUID(as_uuid=True), sa.ForeignKey("agent_swarms.id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("role", sa.String(100), server_default="worker"),
        sa.Column("specialization", sa.String(255), nullable=True),
        sa.Column("is_contestable", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("tasks_completed", sa.Integer, server_default="0"),
        sa.Column("avg_rating", sa.Float, server_default="0.0"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "swarm_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("swarm_id", UUID(as_uuid=True), sa.ForeignKey("agent_swarms.id"), nullable=False),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("task_type", sa.String(100), server_default="general"),
        sa.Column("subtasks", sa.JSON, server_default="[]"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("aggregated_result", sa.JSON, nullable=True),
        sa.Column("total_subtasks", sa.Integer, server_default="0"),
        sa.Column("completed_subtasks", sa.Integer, server_default="0"),
        sa.Column("client_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── ACP Jobs ──
    op.create_table(
        "acp_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("buyer_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("seller_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("evaluator_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("service_id", UUID(as_uuid=True), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("phase", sa.String(50), server_default="request"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("requirements", sa.JSON, server_default="{}"),
        sa.Column("deliverables", sa.JSON, server_default="{}"),
        sa.Column("agreed_terms", sa.JSON, nullable=True),
        sa.Column("agreed_price_lamports", sa.BigInteger, server_default="0"),
        sa.Column("fund_transfer", sa.Boolean, server_default=sa.text("false")),
        sa.Column("principal_amount_lamports", sa.BigInteger, nullable=True),
        sa.Column("escrow_id", UUID(as_uuid=True), sa.ForeignKey("escrows.id"), nullable=True),
        sa.Column("result_data", sa.JSON, nullable=True),
        sa.Column("evaluation_notes", sa.Text, nullable=True),
        sa.Column("evaluation_approved", sa.Boolean, nullable=True),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column("swarm_task_id", UUID(as_uuid=True), sa.ForeignKey("swarm_tasks.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("negotiated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "acp_memos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("acp_jobs.id"), nullable=False),
        sa.Column("sender_agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("memo_type", sa.String(50), nullable=False),
        sa.Column("content", sa.JSON, nullable=False),
        sa.Column("signature", sa.String(128), nullable=True),
        sa.Column("tx_signature", sa.String(128), nullable=True),
        sa.Column("advances_phase", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Resource Offerings ──
    op.create_table(
        "resource_offerings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("endpoint_path", sa.String(500), nullable=False),
        sa.Column("parameters", sa.JSON, server_default="{}"),
        sa.Column("response_schema", sa.JSON, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("total_calls", sa.Integer, server_default="0"),
        sa.Column("avg_response_ms", sa.Float, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_acp_jobs_org_id", "acp_jobs", ["org_id"])
    op.create_index("ix_acp_jobs_phase", "acp_jobs", ["phase"])
    op.create_index("ix_acp_jobs_buyer", "acp_jobs", ["buyer_agent_id"])
    op.create_index("ix_acp_jobs_seller", "acp_jobs", ["seller_agent_id"])
    op.create_index("ix_acp_memos_job_id", "acp_memos", ["job_id"])
    op.create_index("ix_resource_offerings_agent", "resource_offerings", ["agent_id"])
    op.create_index("ix_agent_swarms_org_id", "agent_swarms", ["org_id"])
    op.create_index("ix_swarm_members_swarm_id", "swarm_members", ["swarm_id"])
    op.create_index("ix_swarm_tasks_swarm_id", "swarm_tasks", ["swarm_id"])
    op.create_index("ix_swarm_tasks_status", "swarm_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_swarm_tasks_status")
    op.drop_index("ix_swarm_tasks_swarm_id")
    op.drop_index("ix_swarm_members_swarm_id")
    op.drop_index("ix_agent_swarms_org_id")
    op.drop_index("ix_resource_offerings_agent")
    op.drop_index("ix_acp_memos_job_id")
    op.drop_index("ix_acp_jobs_seller")
    op.drop_index("ix_acp_jobs_buyer")
    op.drop_index("ix_acp_jobs_phase")
    op.drop_index("ix_acp_jobs_org_id")

    op.drop_table("resource_offerings")
    op.drop_table("acp_memos")
    op.drop_table("acp_jobs")
    op.drop_table("swarm_tasks")
    op.drop_table("swarm_members")
    op.drop_table("agent_swarms")
