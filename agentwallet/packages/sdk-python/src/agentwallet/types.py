"""Response types as dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Agent:
    id: str
    org_id: str
    name: str
    description: str | None
    status: str
    capabilities: list[str]
    default_wallet_id: str | None
    reputation_score: float
    is_public: bool
    created_at: str
    updated_at: str


@dataclass
class Wallet:
    id: str
    org_id: str
    agent_id: str | None
    address: str
    wallet_type: str
    label: str | None
    is_active: bool
    created_at: str


@dataclass
class WalletBalance:
    address: str
    sol_balance: float
    lamports: int
    tokens: list[dict] = field(default_factory=list)


@dataclass
class Transaction:
    id: str
    org_id: str
    agent_id: str | None
    wallet_id: str
    tx_type: str
    status: str
    signature: str | None
    from_address: str
    to_address: str
    amount_lamports: int
    token_mint: str | None
    platform_fee_lamports: int
    memo: str | None
    error: str | None
    created_at: str
    confirmed_at: str | None


@dataclass
class Escrow:
    id: str
    org_id: str
    funder_wallet_id: str
    recipient_address: str
    arbiter_address: str | None
    escrow_address: str | None
    amount_lamports: int
    token_mint: str | None
    status: str
    conditions: dict
    fund_signature: str | None
    release_signature: str | None
    refund_signature: str | None
    dispute_reason: str | None
    expires_at: str | None
    funded_at: str | None
    completed_at: str | None
    created_at: str


@dataclass
class Policy:
    id: str
    org_id: str
    name: str
    rules: dict
    scope_type: str
    scope_id: str | None
    priority: int
    enabled: bool
    created_at: str
    updated_at: str


@dataclass
class ListResponse:
    data: list
    total: int


@dataclass
class AnalyticsSummary:
    total_spend_lamports: int
    total_fees_lamports: int
    tx_count: int
    failed_tx_count: int
    active_agents: int
    unique_destinations: int
    period_start: str
    period_end: str
