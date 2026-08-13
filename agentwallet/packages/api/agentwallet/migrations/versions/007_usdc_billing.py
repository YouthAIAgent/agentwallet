"""On-chain USDC subscription billing table.

Revision ID: 007_usdc_billing
Revises: 006_acp_and_swarms
Create Date: 2026-08-13 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_usdc_billing"
down_revision: Union[str, None] = "006_acp_and_swarms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("tier", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("amount_usdc", sa.Float, server_default="0"),
        sa.Column("amount_raw", sa.BigInteger, server_default="0"),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("payment_wallet_id", postgresql.UUID(as_uuid=True)),
        sa.Column("payment_tx_id", postgresql.UUID(as_uuid=True)),
        sa.Column("payment_signature", sa.String(128)),
        sa.Column("auto_renew", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_billing_subscriptions_org_id", "billing_subscriptions", ["org_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_billing_subscriptions_org_id", table_name="billing_subscriptions")
    op.drop_table("billing_subscriptions")
