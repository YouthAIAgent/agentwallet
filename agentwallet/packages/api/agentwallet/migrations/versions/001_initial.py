"""Initial schema -- all tables for AgentWallet Protocol.

Revision ID: 001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("tier", sa.String(50), server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("settings", postgresql.JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="admin"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("permissions", postgresql.JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Wallets (create before agents since agents reference wallets)
    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True)),  # FK added after agents table
        sa.Column("address", sa.String(64), unique=True, nullable=False),
        sa.Column("wallet_type", sa.String(50), server_default="agent"),
        sa.Column("encrypted_key", sa.String(1024), nullable=False),
        sa.Column("label", sa.String(255)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Agents
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("capabilities", postgresql.JSONB, server_default="[]"),
        sa.Column("default_wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wallets.id")),
        sa.Column("reputation_score", sa.Float, server_default="0"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("is_public", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Add agent FK to wallets
    op.create_foreign_key("fk_wallets_agent_id_agents", "wallets", "agents", ["agent_id"], ["id"])

    # Transactions
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wallets.id"), nullable=False),
        sa.Column("tx_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("signature", sa.String(128)),
        sa.Column("from_address", sa.String(64), nullable=False),
        sa.Column("to_address", sa.String(64), nullable=False),
        sa.Column("amount_lamports", sa.BigInteger, nullable=False),
        sa.Column("token_mint", sa.String(64)),
        sa.Column("platform_fee_lamports", sa.BigInteger, server_default="0"),
        sa.Column("idempotency_key", sa.String(255), unique=True),
        sa.Column("memo", sa.Text),
        sa.Column("error", sa.Text),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_transactions_org_created", "transactions", ["org_id", "created_at"])
    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_agent", "transactions", ["agent_id"])

    # Escrows
    op.create_table(
        "escrows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("funder_wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wallets.id"), nullable=False),
        sa.Column("recipient_address", sa.String(64), nullable=False),
        sa.Column("arbiter_address", sa.String(64)),
        sa.Column("escrow_address", sa.String(64)),
        sa.Column("amount_lamports", sa.BigInteger, nullable=False),
        sa.Column("token_mint", sa.String(64)),
        sa.Column("status", sa.String(50), server_default="created"),
        sa.Column("conditions", postgresql.JSONB, server_default="{}"),
        sa.Column("fund_signature", sa.String(128)),
        sa.Column("release_signature", sa.String(128)),
        sa.Column("refund_signature", sa.String(128)),
        sa.Column("dispute_reason", sa.Text),
        sa.Column("resolution_notes", sa.Text),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("funded_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Policies
    op.create_table(
        "policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rules", postgresql.JSONB, nullable=False),
        sa.Column("scope_type", sa.String(50), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True)),
        sa.Column("priority", sa.Integer, server_default="100"),
        sa.Column("enabled", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Approval Requests
    op.create_table(
        "approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("transaction_request", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("required_approvals", sa.Integer, server_default="1"),
        sa.Column("decisions", postgresql.JSONB, server_default="[]"),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("policies.id")),
        sa.Column("reason", sa.String(1024)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Audit Events
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=False),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_org_created", "audit_events", ["org_id", "created_at"])
    op.create_index("ix_audit_events_resource", "audit_events", ["resource_type", "resource_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])

    # Analytics Daily
    op.create_table(
        "analytics_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id")),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("tx_count", sa.Integer, server_default="0"),
        sa.Column("total_spend_lamports", sa.BigInteger, server_default="0"),
        sa.Column("total_fees_lamports", sa.BigInteger, server_default="0"),
        sa.Column("unique_destinations", sa.Integer, server_default="0"),
        sa.Column("failed_tx_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_analytics_daily_org_date", "analytics_daily", ["org_id", "date"])
    op.create_index("ix_analytics_daily_agent_date", "analytics_daily", ["agent_id", "date"])

    # Webhooks
    op.create_table(
        "webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("events", postgresql.JSONB, server_default="[]"),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Webhook Deliveries
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("webhook_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("webhooks.id"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("status_code", sa.Integer),
        sa.Column("response_body", sa.Text),
        sa.Column("attempts", sa.Integer, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Usage Meters
    op.create_table(
        "usage_meters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tx_count", sa.Integer, server_default="0"),
        sa.Column("tx_volume_lamports", sa.BigInteger, server_default="0"),
        sa.Column("api_calls", sa.Integer, server_default="0"),
        sa.Column("escrow_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("usage_meters")
    op.drop_table("webhook_deliveries")
    op.drop_table("webhooks")
    op.drop_table("analytics_daily")
    op.drop_table("audit_events")
    op.drop_table("approval_requests")
    op.drop_table("policies")
    op.drop_table("escrows")
    op.drop_table("transactions")
    op.drop_table("agents")
    op.drop_table("wallets")
    op.drop_table("api_keys")
    op.drop_table("users")
    op.drop_table("organizations")
