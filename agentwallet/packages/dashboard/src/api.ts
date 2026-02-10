const API_BASE = "/api/v1";

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
  organization_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    organization_id: string;
  };
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
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  policy_id?: string;
  metadata?: Record<string, unknown>;
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
    return request<{ agents: Agent[]; total: number }>(
      `/agents${q ? `?${q}` : ""}`
    );
  },
  get: (id: string) => request<Agent>(`/agents/${id}`),
  create: (data: CreateAgentRequest) =>
    request<CreateAgentResponse>("/agents", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<CreateAgentRequest> & { status?: string }) =>
    request<Agent>(`/agents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<void>(`/agents/${id}`, { method: "DELETE" }),
};

// --- Wallets ---
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

export interface CreateWalletRequest {
  chain: string;
  agent_id?: string;
  label?: string;
}

export const wallets = {
  list: (params?: { chain?: string; agent_id?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.chain) qs.set("chain", params.chain);
    if (params?.agent_id) qs.set("agent_id", params.agent_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const q = qs.toString();
    return request<{ wallets: Wallet[]; total: number }>(
      `/wallets${q ? `?${q}` : ""}`
    );
  },
  get: (id: string) => request<Wallet>(`/wallets/${id}`),
  create: (data: CreateWalletRequest) =>
    request<Wallet>("/wallets", {
      method: "POST",
      body: JSON.stringify(data),
    }),
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
    return request<{ transactions: Transaction[]; total: number }>(
      `/transactions${q ? `?${q}` : ""}`
    );
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

export interface AnalyticsSummary {
  total_spend_usd: number;
  total_transactions: number;
  active_agents: number;
  active_wallets: number;
  avg_tx_value: number;
  period_days: number;
}

export const analytics = {
  dailySpend: (days = 30) =>
    request<{ data: DailySpend[] }>(`/analytics/daily-spend?days=${days}`),
  agentBreakdown: () =>
    request<{ data: AgentSpend[] }>("/analytics/agent-breakdown"),
  summary: (days = 30) =>
    request<AnalyticsSummary>(`/analytics/summary?days=${days}`),
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
  list: () => request<{ policies: Policy[]; total: number }>("/policies"),
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
    return request<{ events: AuditEvent[]; total: number }>(
      `/audit-log${q ? `?${q}` : ""}`
    );
  },
};

// --- Billing ---
export interface BillingInfo {
  tier: "free" | "starter" | "pro" | "enterprise";
  usage: {
    agents: { used: number; limit: number };
    wallets: { used: number; limit: number };
    transactions_monthly: { used: number; limit: number };
    api_calls_monthly: { used: number; limit: number };
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
  current: () => request<BillingInfo>("/billing"),
  tiers: () => request<{ tiers: BillingTier[] }>("/billing/tiers"),
  upgrade: (tier: string) =>
    request<{ checkout_url: string }>("/billing/upgrade", {
      method: "POST",
      body: JSON.stringify({ tier }),
    }),
};

// --- Dashboard Overview ---
export interface DashboardOverview {
  total_agents: number;
  total_wallets: number;
  total_transactions: number;
  total_spend_usd: number;
  recent_transactions: Transaction[];
  daily_spend: DailySpend[];
}

export const dashboard = {
  overview: () => request<DashboardOverview>("/dashboard/overview"),
};
