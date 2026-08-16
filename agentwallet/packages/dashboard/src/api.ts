const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

let authToken: string | null = localStorage.getItem("aw_token");

export function setToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem("aw_token", token);
  } else {
    localStorage.removeItem("aw_token");
  }
}

export function getToken(): string | null {
  return authToken;
}

export function isAuthenticated(): boolean {
  return !!authToken;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    setToken(null);
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || body.message || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// --- Auth ---
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  org_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  org_id: string;
}

export const auth = {
  login: (data: LoginRequest) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  register: (data: RegisterRequest) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  logout: () => {
    setToken(null);
  },
};

// --- Agents ---
export interface Agent {
  id: string;
  name: string;
  description: string;
  status: "active" | "paused" | "revoked";
  api_key_prefix: string;
  policy_id: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
  default_wallet_id?: string | null;
  reputation_score?: number;
  is_public?: boolean;
}

// The API returns the agent directly (no {agent, api_key} wrapper) and
// has no per-agent API key — keys live under /auth/api-keys. Map the wire
// shape to the UI shape.

export interface ApiAgent {
  id: string;
  org_id: string;
  name: string;
  description: string | null;
  status: string;
  capabilities: string[];
  default_wallet_id: string | null;
  reputation_score: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  capabilities?: string[];
  metadata?: Record<string, unknown>;
}

export function mapAgent(a: ApiAgent): Agent {
  return {
    id: a.id,
    name: a.name,
    description: a.description || "",
    status: (a.status as Agent["status"]) || "active",
    api_key_prefix: "",
    policy_id: null,
    created_at: a.created_at,
    updated_at: a.updated_at,
    metadata: {},
    default_wallet_id: a.default_wallet_id,
    reputation_score: a.reputation_score,
    is_public: a.is_public,
  };
}

export interface CreateAgentResponse {
  agent: Agent;
  api_key: string;
}

export const agents = {
  list: (params?: { status?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return request<{ data: ApiAgent[]; total: number }>(
      `/agents${q ? `?${q}` : ""}`
    ).then((r) => ({ agents: r.data.map(mapAgent), total: r.total }));
  },
  get: (id: string) =>
    request<ApiAgent>(`/agents/${id}`).then(mapAgent),
  create: (data: CreateAgentRequest) =>
    request<ApiAgent>("/agents", {
      method: "POST",
      body: JSON.stringify(data),
    }).then((a) => ({ agent: mapAgent(a), api_key: "" })),
  update: (id: string, data: Partial<CreateAgentRequest> & { status?: string }) =>
    request<ApiAgent>(`/agents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }).then(mapAgent),
  delete: (id: string) =>
    request<void>(`/agents/${id}`, { method: "DELETE" }),
};

// --- Wallets ---
// The API is Solana-native and returns { id, org_id, agent_id, address,
// wallet_type, label, is_active, created_at }. Map it to the UI shape
// (chain/balance/status) so pages don't have to know the wire format.
// The API takes { agent_id, wallet_type, label } — no chain field.

export interface ApiWallet {
  id: string;
  org_id: string;
  agent_id: string | null;
  address: string;
  wallet_type: string;
  label: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Wallet {
  id: string;
  agent_id: string | null;
  chain: string;
  address: string;
  balance: string;
  status: "active" | "frozen" | "archived";
  created_at: string;
  label: string;
}

export function mapWallet(w: ApiWallet): Wallet {
  return {
    id: w.id,
    agent_id: w.agent_id,
    chain: w.wallet_type === "pda" ? "pda" : "solana",
    address: w.address,
    balance: "0",
    status: w.is_active ? "active" : "frozen",
    created_at: w.created_at,
    label: w.label || "",
  };
}

export interface CreateWalletRequest {
  agent_id?: string;
  wallet_type?: string;
  label?: string;
}

export const wallets = {
  list: (params?: { agent_id?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.agent_id) qs.set("agent_id", params.agent_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return request<{ data: ApiWallet[]; total: number }>(
      `/wallets${q ? `?${q}` : ""}`
    ).then((r) => ({ wallets: r.data.map(mapWallet), total: r.total }));
  },
  get: (id: string) =>
    request<ApiWallet>(`/wallets/${id}`).then(mapWallet),
  create: (data: CreateWalletRequest) =>
    request<ApiWallet>("/wallets", {
      method: "POST",
      body: JSON.stringify(data),
    }).then(mapWallet),
};

// --- Transactions ---
export interface Transaction {
  id: string;
  wallet_id: string;
  agent_id: string;
  type: "transfer" | "swap" | "stake" | "contract_call";
  status: "pending" | "confirmed" | "failed" | "cancelled";
  chain: string;
  from_address: string;
  to_address: string;
  amount: string;
  token: string;
  tx_hash: string | null;
  gas_used: string | null;
  created_at: string;
  confirmed_at: string | null;
  signatures: string[];
}

export const transactions = {
  list: (params?: {
    status?: string;
    agent_id?: string;
    wallet_id?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.agent_id) qs.set("agent_id", params.agent_id);
    if (params?.wallet_id) qs.set("wallet_id", params.wallet_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return request<{ data: ApiTransaction[]; total: number }>(
      `/transactions${q ? `?${q}` : ""}`
    ).then((r) => ({
      transactions: r.data.map(mapTransaction),
      total: r.total,
    }));
  },
  get: (id: string) => request<Transaction>(`/transactions/${id}`),
};

// --- Analytics ---
export interface DailySpend {
  date: string;
  total_usd: number;
  tx_count: number;
}

export interface AgentSpend {
  agent_id: string;
  agent_name: string;
  total_usd: number;
  tx_count: number;
}

// Wire shapes from /analytics (lamports, camelCase)
interface DailyMetricResponse {
  date: string;
  tx_count: number;
  total_spend_lamports: number;
  total_fees_lamports: number;
  unique_destinations: number;
  failed_tx_count: number;
}

interface AgentAnalyticsResponse {
  agent_id: string;
  agent_name?: string;
  total_spend_lamports: number;
  tx_count: number;
}

interface AnalyticsSummaryResponse {
  total_spend_lamports: number;
  total_fees_lamports: number;
  tx_count: number;
  failed_tx_count: number;
  active_agents: number;
  unique_destinations: number;
  period_start: string;
  period_end: string;
}

export interface AnalyticsSummary {
  total_spend_usd: number;
  total_transactions: number;
  active_agents: number;
  active_wallets: number;
  avg_tx_value: number;
  period_days: number;
}

export const analytics = {
  // API returns lamports; the UI shows USD — map on the way in.
  dailySpend: (days = 30) =>
    request<DailyMetricResponse[]>(`/analytics/daily?days=${days}`).then((r) => ({
      data: (Array.isArray(r) ? r : (r as { data?: DailyMetricResponse[] }).data || []).map(
        (d) => ({
          date: d.date,
          total_usd: d.total_spend_lamports / 1e9,
          tx_count: d.tx_count,
        })
      ),
    })),
  agentBreakdown: () =>
    request<AgentAnalyticsResponse[]>(`/analytics/agents?days=30`).then((r) => ({
      data: (Array.isArray(r) ? r : (r as { data?: AgentAnalyticsResponse[] }).data || []).map(
        (a) => ({
          agent_id: a.agent_id,
          agent_name: a.agent_name || a.agent_id,
          total_usd: a.total_spend_lamports / 1e9,
          tx_count: a.tx_count,
        })
      ),
    })),
  summary: (days = 30) =>
    request<AnalyticsSummaryResponse>(`/analytics/summary?days=${days}`).then((s) => ({
      total_spend_usd: s.total_spend_lamports / 1e9,
      total_transactions: s.tx_count,
      active_agents: s.active_agents,
      active_wallets: s.unique_destinations,
      avg_tx_value: s.tx_count ? s.total_spend_lamports / 1e9 / s.tx_count : 0,
      period_days: days,
    })),
};

// --- Policies ---
export interface Policy {
  id: string;
  name: string;
  description: string;
  rules: PolicyRule[];
  created_at: string;
  updated_at: string;
}

export interface PolicyRule {
  type: "spending_limit" | "whitelist" | "time_window" | "approval_required" | "chain_restriction";
  params: Record<string, unknown>;
}

export interface CreatePolicyRequest {
  name: string;
  description?: string;
  rules: PolicyRule[];
}

export const policies = {
  list: () =>
    request<{ data: Policy[]; total: number }>("/policies").then((r) => ({
      policies: r.data,
      total: r.total,
    })),
  get: (id: string) => request<Policy>(`/policies/${id}`),
  create: (data: CreatePolicyRequest) =>
    request<Policy>("/policies", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<CreatePolicyRequest>) =>
    request<Policy>(`/policies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<void>(`/policies/${id}`, { method: "DELETE" }),
};

// --- Audit Log ---
export interface AuditEvent {
  id: string;
  actor_type: "user" | "agent" | "system";
  actor_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ip_address: string;
  created_at: string;
}

export const auditLog = {
  list: (params?: {
    action?: string;
    actor_type?: string;
    resource_type?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.action) qs.set("action", params.action);
    if (params?.actor_type) qs.set("actor_type", params.actor_type);
    if (params?.resource_type) qs.set("resource_type", params.resource_type);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return request<{ data: ApiAuditEvent[]; total: number }>(
      `/audit-log${q ? `?${q}` : ""}`
    ).then((r) => ({ events: r.data.map(mapAuditEvent), total: r.total }));
  },
};

// Wire shape from /audit-log (event_type, actor_id)
interface ApiAuditEvent {
  id: string;
  org_id: string;
  event_type: string;
  actor_id: string;
  actor_type: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export function mapAuditEvent(e: ApiAuditEvent): AuditEvent {
  return {
    id: e.id,
    actor_type: (e.actor_type as AuditEvent["actor_type"]) || "system",
    actor_id: e.actor_id,
    action: e.event_type,
    resource_type: e.resource_type,
    resource_id: e.resource_id,
    details: e.details || {},
    ip_address: e.ip_address || "",
    created_at: e.created_at,
  };
}

// --- Billing ---
export interface BillingInfo {
  tier: "free" | "starter" | "pro" | "enterprise";
  usage: {
    agents: { used: number; limit: number | null };
    wallets: { used: number; limit: number | null };
    transactions_monthly: { used: number; limit: number | null };
    api_calls_monthly: { used: number; limit: number | null };
  };
  current_period_end: string;
  amount_due: number;
}

export interface BillingTier {
  name: string;
  price_monthly: number;
  limits: {
    agents: number;
    wallets: number;
    transactions_monthly: number;
    api_calls_monthly: number;
  };
  features: string[];
}

export const billing = {
  current: () =>
    request<{
      tier: string;
      usage: Record<
        string,
        { used: number; limit: number | null }
      >;
      current_period_end?: string | null;
      amount_due?: number;
    }>("/billing/current").then((r) => ({
      tier: (r.tier as BillingInfo["tier"]) || "free",
      usage: {
        agents: r.usage["agents"] || { used: 0, limit: 0 },
        wallets: r.usage["wallets"] || { used: 0, limit: 0 },
        transactions_monthly:
          r.usage["transactions_monthly"] || { used: 0, limit: 0 },
        api_calls_monthly:
          r.usage["api_calls_monthly"] || { used: 0, limit: 0 },
      },
      current_period_end: r.current_period_end || "",
      amount_due: r.amount_due || 0,
    })),
  tiers: () =>
    request<{ tiers: BillingTier[] }>("/billing/tiers").then((r) => ({
      tiers: r.tiers.map((t) => ({
        name: t.name,
        price_monthly: t.price_monthly,
        limits: {
          agents: t.limits?.agents ?? 0,
          wallets: t.limits?.wallets ?? 0,
          transactions_monthly: t.limits?.transactions_monthly ?? 0,
          api_calls_monthly: t.limits?.api_calls_monthly ?? 0,
        },
        features: t.features || [],
      })),
    })),
  upgrade: (tier: string) =>
    request<{ checkout_url: string }>("/billing/upgrade", {
      method: "POST",
      body: JSON.stringify({ tier }),
    }),
};

// --- PDA Wallets ---
export interface PdaWallet {
  id: string;
  organization_id: string;
  authority_wallet_id: string;
  agent_id_seed: string;
  pda_address: string;
  spending_limit_per_tx: string;
  daily_limit: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreatePdaWalletRequest {
  authority_wallet_id: string;
  agent_id_seed: string;
  spending_limit_per_tx: number;
  daily_limit: number;
}

export interface PdaOnChainState {
  authority: string;
  daily_spent: number;
  daily_limit: number;
  spending_limit_per_tx: number;
  is_active: boolean;
  sol_balance: number;
  last_reset_slot: number;
}

export interface DerivePdaRequest {
  org_pubkey: string;
  agent_id_seed: string;
}

export interface DerivePdaResponse {
  pda_address: string;
  bump: number;
}

export const pdaWallets = {
  list: (params?: { limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return request<{ data: PdaWallet[]; total: number }>(
      `/pda-wallets${q ? `?${q}` : ""}`
    ).then((r) => ({ pda_wallets: r.data, total: r.total }));
  },
  get: (id: string) => request<PdaWallet>(`/pda-wallets/${id}`),
  create: (data: CreatePdaWalletRequest) =>
    request<PdaWallet>("/pda-wallets", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getState: (id: string) =>
    request<PdaOnChainState>(`/pda-wallets/${id}/state`),
  derive: (data: DerivePdaRequest) =>
    request<DerivePdaResponse>("/pda-wallets/derive", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// --- Devnet Playground ---
export interface PlaygroundStatus {
  wallet_id: string | null;
  wallet_address: string | null;
  balance_sol: number;
  platform_address: string;
  network: string;
}

export interface FundResult {
  wallet_id: string;
  wallet_address: string;
  amount_sol: number;
  signature: string;
  confirmed: boolean;
  explorer_url: string;
}

export interface EscrowDemoResult {
  escrow_id: string;
  status: string;
  amount_sol: number;
  fund_signature: string | null;
  fund_explorer_url: string | null;
  recipient_address: string;
}

export interface EscrowReleaseResult {
  escrow_id: string;
  status: string;
  release_signature: string | null;
  release_explorer_url: string | null;
  recipient_address: string;
}

export interface EscrowRefundResult {
  escrow_id: string;
  status: string;
  refund_signature: string | null;
  refund_explorer_url: string | null;
  funder_wallet_address: string | null;
}

export interface X402DemoResult {
  demo: boolean;
  amount_sol: number;
  to_address: string;
  payment_signature: string;
  payment_confirmed: boolean;
  payment_explorer_url: string;
  verified_on_chain: boolean;
  verification_error: string | null;
  ai_provider: string;
  ai_model: string;
  ai_response: string;
}

export interface TransferDemoResult {
  wallet_id: string;
  amount_sol: number;
  to_address: string;
  signature: string;
  confirmed: boolean;
  explorer_url: string;
}

export interface UsdcDemoResult {
  wallet_id: string;
  wallet_address: string;
  mint: string;
  amount_usdc: number;
  signature: string;
  confirmed: boolean;
  explorer_url: string;
}

export const playground = {
  status: () => request<PlaygroundStatus>("/playground"),
  fund: () =>
    request<FundResult>("/playground/fund", { method: "POST" }),
  escrow: () =>
    request<EscrowDemoResult>("/playground/escrow", { method: "POST" }),
  release: (escrowId: string) =>
    request<EscrowReleaseResult>(`/playground/escrow/${escrowId}/release`, {
      method: "POST",
    }),
  refund: (escrowId: string) =>
    request<EscrowRefundResult>(`/playground/escrow/${escrowId}/refund`, {
      method: "POST",
    }),
  x402: () => request<X402DemoResult>("/playground/x402", { method: "POST" }),
  transfer: () =>
    request<TransferDemoResult>("/playground/transfer", { method: "POST" }),
  usdc: () => request<UsdcDemoResult>("/playground/usdc", { method: "POST" }),
};

// Solana devnet explorer link for a tx signature
export function explorerUrl(signature: string): string {
  return `https://explorer.solana.com/tx/${signature}?cluster=devnet`;
}

export function shortSig(signature: string): string {
  return signature.length > 24 ? `${signature.slice(0, 12)}…${signature.slice(-8)}` : signature;
}

// --- Dashboard Overview ---
export interface DashboardOverview {
  total_agents: number;
  total_wallets: number;
  total_transactions: number;
  total_spend_usd: number;
  recent_transactions: Transaction[];
  daily_spend: DailySpend[];
}

// Wire shape from /transactions (lamports, tx_type, signature)
interface ApiTransaction {
  id: string;
  org_id: string;
  agent_id: string | null;
  wallet_id: string;
  tx_type: string;
  status: string;
  signature: string | null;
  from_address: string;
  to_address: string;
  amount_lamports: number;
  token_mint: string | null;
  platform_fee_lamports: number;
  memo: string | null;
  error: string | null;
  created_at: string;
  confirmed_at: string | null;
}

export function mapTransaction(t: ApiTransaction): Transaction {
  return {
    id: t.id,
    wallet_id: t.wallet_id,
    agent_id: t.agent_id || "",
    type: (t.tx_type as Transaction["type"]) || "transfer",
    status: (t.status as Transaction["status"]) || "pending",
    chain: "solana",
    from_address: t.from_address,
    to_address: t.to_address,
    amount: (t.amount_lamports / 1e9).toString(),
    token: t.token_mint === "USDC" ? "USDC" : "SOL",
    tx_hash: t.signature,
    gas_used: null,
    created_at: t.created_at,
    confirmed_at: t.confirmed_at,
    signatures: t.signature ? [t.signature] : [],
  };
}

// The home page composes live endpoints instead of a /dashboard/overview
// route. Each call falls back to zeroed data so a single 404 never blanks
// the whole page.
export const dashboard = {
  overview: async () => {
    const [summary, agentsRes, walletsRes, daily, txs] = await Promise.all([
      analytics.summary(14).catch(() => null),
      agents.list({ limit: 1 }).catch(() => null),
      wallets.list({ limit: 1 }).catch(() => null),
      analytics.dailySpend(14).catch(() => null),
      transactions.list({ limit: 5 }).catch(() => null),
    ]);
    return {
      total_agents: agentsRes?.total ?? 0,
      total_wallets: walletsRes?.total ?? 0,
      total_transactions: summary?.total_transactions ?? txs?.total ?? 0,
      total_spend_usd: summary?.total_spend_usd ?? 0,
      recent_transactions: txs?.transactions ?? [],
      daily_spend: daily?.data ?? [],
    };
  },
};

// --- Task Marketplace ---
export interface Task {
  id: string;
  org_id: string;
  title: string;
  description: string;
  category: string;
  capability?: string | null;
  requirements: Record<string, unknown>;
  price_usdc: number;
  token_symbol: string;
  platform_fee_usdc: number;
  escrow_id?: string | null;
  agent_id?: string | null;
  agent_name?: string | null;
  agent_address?: string | null;
  status: string;
  result_data?: Record<string, unknown> | null;
  delivery_notes?: string | null;
  provider?: string | null;
  model?: string | null;
  posted_at: string;
  funded_at?: string | null;
  assigned_at?: string | null;
  delivered_at?: string | null;
  released_at?: string | null;
  created_at: string;
}

export interface TaskStats {
  total_tasks: number;
  delivered_tasks: number;
  released_tasks: number;
  platform_fees_usdc: number;
}

export const tasks = {
  list: (params: { status?: string; category?: string; limit?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.status) q.set("status", params.status);
    if (params.category) q.set("category", params.category);
    if (params.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return request<Task[]>(`/marketplace/tasks${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<Task>(`/marketplace/tasks/${id}`),
  stats: () => request<TaskStats>("/marketplace/tasks/stats"),
  post: (body: {
    title: string;
    description: string;
    price_usdc: number;
    category?: string;
    capability?: string;
    requirements?: Record<string, unknown>;
    auto_assign?: boolean;
  }) => request<Task>("/marketplace/tasks", {
    method: "POST",
    body: JSON.stringify(body),
  }),
  assign: (id: string, agent_id: string) =>
    request<Task>(`/marketplace/tasks/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ agent_id }),
    }),
  run: (id: string) => request<Task>(`/marketplace/tasks/${id}/run`, { method: "POST" }),
  deliver: (id: string, result_data: Record<string, unknown>, delivery_notes?: string) =>
    request<Task>(`/marketplace/tasks/${id}/deliver`, {
      method: "POST",
      body: JSON.stringify({ result_data, delivery_notes, auto_release: true }),
    }),
  refund: (id: string, reason?: string) =>
    request<Task>(`/marketplace/tasks/${id}/refund`, {
      method: "POST",
      body: JSON.stringify({ reason: reason || "not started" }),
    }),
  cancel: (id: string) => request<Task>(`/marketplace/tasks/${id}/cancel`, { method: "POST" }),
};
