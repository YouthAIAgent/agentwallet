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


@dataclass
class PDAWallet:
    id: str
    org_id: str
    pda_address: str
    authority_wallet_id: str
    agent_id: str | None
    agent_id_seed: str
    spending_limit_per_tx: int
    daily_limit: int
    bump: int
    is_active: bool
    tx_signature: str | None
    created_at: str


@dataclass
class PDAWalletState:
    pda_address: str
    authority: str
    org: str
    agent_id: str
    spending_limit_per_tx: int
    daily_limit: int
    daily_spent: int
    last_reset_day: int
    is_active: bool
    bump: int
    sol_balance: float


@dataclass
class PDATransferResult:
    signature: str
    confirmed: bool


@dataclass
class PDADeriveResult:
    pda_address: str
    bump: int


# ── ACP Types ──


@dataclass
class AcpJob:
    id: str
    org_id: str
    buyer_agent_id: str
    seller_agent_id: str
    phase: str
    title: str
    description: str
    agreed_price_lamports: int
    fund_transfer: bool
    created_at: str
    updated_at: str
    evaluator_agent_id: str | None = None
    service_id: str | None = None
    requirements: dict = field(default_factory=dict)
    deliverables: dict = field(default_factory=dict)
    agreed_terms: dict | None = None
    escrow_id: str | None = None
    result_data: dict | None = None
    evaluation_notes: str | None = None
    evaluation_approved: bool | None = None
    rating: int | None = None
    swarm_task_id: str | None = None
    negotiated_at: str | None = None
    transacted_at: str | None = None
    evaluated_at: str | None = None
    completed_at: str | None = None


@dataclass
class AcpMemo:
    id: str
    job_id: str
    sender_agent_id: str
    memo_type: str
    content: dict
    advances_phase: bool
    created_at: str
    signature: str | None = None
    tx_signature: str | None = None


@dataclass
class ResourceOffering:
    id: str
    agent_id: str
    org_id: str
    name: str
    description: str
    endpoint_path: str
    is_active: bool
    total_calls: int
    avg_response_ms: float
    created_at: str
    updated_at: str
    parameters: dict = field(default_factory=dict)
    response_schema: dict = field(default_factory=dict)


# ── Swarm Types ──


@dataclass
class Swarm:
    id: str
    org_id: str
    name: str
    description: str
    orchestrator_agent_id: str
    swarm_type: str
    max_members: int
    is_active: bool
    is_public: bool
    total_tasks: int
    completed_tasks: int
    avg_completion_time_hours: float
    created_at: str
    updated_at: str
    config: dict = field(default_factory=dict)
    member_count: int = 0


@dataclass
class SwarmMember:
    id: str
    swarm_id: str
    agent_id: str
    role: str
    is_contestable: bool
    is_active: bool
    tasks_completed: int
    avg_rating: float
    joined_at: str
    specialization: str | None = None


@dataclass
class SwarmTask:
    id: str
    swarm_id: str
    org_id: str
    title: str
    description: str
    task_type: str
    status: str
    total_subtasks: int
    completed_subtasks: int
    created_at: str
    updated_at: str
    subtasks: list = field(default_factory=list)
    aggregated_result: dict | None = None
    client_agent_id: str | None = None
    completed_at: str | None = None
