"""PDA wallet table for on-chain policy-enforced wallets.

Revision ID: 004_pda_wallets
Revises: 003_marketplace
Create Date: 2026-02-14 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_pda_wallets"
down_revision: Union[str, None] = "003_marketplace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pda_wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("pda_address", sa.String(64), unique=True, nullable=False),
        sa.Column("authority_wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wallets.id"), nullable=False),
        sa.Column("org_pubkey", sa.String(64), nullable=False),
        sa.Column("agent_id_seed", sa.String(64), nullable=False),
        sa.Column("spending_limit_per_tx", sa.Integer, nullable=False),
        sa.Column("daily_limit", sa.Integer, nullable=False),
        sa.Column("bump", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("tx_signature", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_pda_wallets_org_id", "pda_wallets", ["org_id"])
    op.create_index("ix_pda_wallets_authority_wallet_id", "pda_wallets", ["authority_wallet_id"])


def downgrade() -> None:
    op.drop_table("pda_wallets")
