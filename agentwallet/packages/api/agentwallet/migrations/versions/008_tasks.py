"""Human-facing task marketplace table.

Revision ID: 008_tasks
Revises: 007_usdc_billing
Create Date: 2026-08-16 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_tasks"
down_revision: Union[str, None] = "007_usdc_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), server_default="general"),
        sa.Column("capability", sa.String(100)),
        sa.Column("requirements", sa.JSON, server_default="{}"),
        sa.Column("price_lamports", sa.BigInteger, nullable=False),
        sa.Column("token_symbol", sa.String(20), server_default="SOL"),
        sa.Column("platform_fee_lamports", sa.BigInteger, server_default="0"),
        sa.Column("escrow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("escrows.id")),
        sa.Column("funder_wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wallets.id")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("agent_address", sa.String(88)),
        sa.Column("status", sa.String(50), server_default="posted"),
        sa.Column("input_data", sa.JSON, server_default="{}"),
        sa.Column("result_data", sa.JSON),
        sa.Column("delivery_notes", sa.Text),
        sa.Column("provider", sa.String(100)),
        sa.Column("model", sa.String(100)),
        sa.Column("posted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("funded_at", sa.DateTime(timezone=True)),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_listed", sa.Boolean, server_default="false"),
    )
    op.create_index("ix_tasks_org_id", "tasks", ["org_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_escrow_id", "tasks", ["escrow_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_escrow_id", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_org_id", table_name="tasks")
    op.drop_table("tasks")
