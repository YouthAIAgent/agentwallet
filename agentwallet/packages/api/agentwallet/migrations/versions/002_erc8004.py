"""ERC-8004 identity, feedback, and EVM wallet tables.

Revision ID: 002_erc8004
Revises: 001_initial
Create Date: 2025-06-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_erc8004"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ERC-8004 Identities
    op.create_table(
        "erc8004_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), unique=True, nullable=False),
        sa.Column("token_id", sa.BigInteger),
        sa.Column("evm_address", sa.String(42), nullable=False),
        sa.Column("chain_id", sa.Integer, server_default="8453"),
        sa.Column("metadata_uri", sa.String(2048)),
        sa.Column("tx_hash", sa.String(66)),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_erc8004_identities_agent_id", "erc8004_identities", ["agent_id"])
    op.create_index("ix_erc8004_identities_token_id", "erc8004_identities", ["token_id"])

    # ERC-8004 Feedback
    op.create_table(
        "erc8004_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("from_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("to_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("tx_hash", sa.String(66)),
        sa.Column("task_reference", sa.String(255)),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_erc8004_feedback_to_agent_id", "erc8004_feedback", ["to_agent_id"])
    op.create_index("ix_erc8004_feedback_from_agent_id", "erc8004_feedback", ["from_agent_id"])

    # EVM Wallets
    op.create_table(
        "evm_wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("address", sa.String(42), nullable=False),
        sa.Column("encrypted_key", sa.Text, nullable=False),
        sa.Column("chain_id", sa.Integer, server_default="8453"),
        sa.Column("label", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_evm_wallets_agent_id", "evm_wallets", ["agent_id"])

    # Add ERC-8004 columns to agents table
    op.add_column("agents", sa.Column("erc8004_token_id", sa.BigInteger))
    op.add_column("agents", sa.Column("evm_address", sa.String(42)))
    op.add_column("agents", sa.Column("erc8004_reputation", sa.Float, server_default="0"))
    op.add_column("agents", sa.Column("erc8004_feedback_count", sa.Integer, server_default="0"))


def downgrade() -> None:
    op.drop_column("agents", "erc8004_feedback_count")
    op.drop_column("agents", "erc8004_reputation")
    op.drop_column("agents", "evm_address")
    op.drop_column("agents", "erc8004_token_id")
    op.drop_table("evm_wallets")
    op.drop_table("erc8004_feedback")
    op.drop_table("erc8004_identities")
