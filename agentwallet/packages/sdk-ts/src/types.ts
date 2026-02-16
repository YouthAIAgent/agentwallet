/** Common list response wrapper */
export interface ListResponse<T> {
  data: T[];
  total: number;
}

/** Agent */
export interface Agent {
  id: string;
  org_id: string;
  name: string;
  description: string | null;
  capabilities: string[];
  is_public: boolean;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentParams {
  name: string;
  description?: string;
  capabilities?: string[];
  is_public?: boolean;
  metadata?: Record<string, unknown>;
}

/** Wallet */
export interface Wallet {
  id: string;
  org_id: string;
  agent_id: string | null;
  wallet_type: string;
  label: string | null;
  sol_address: string;
  status: string;
  created_at: string;
}

export interface CreateWalletParams {
  agent_id?: string;
  wallet_type?: string;
  label?: string;
}

export interface WalletBalance {
  wallet_id: string;
  sol_address: string;
  balance_sol: number;
  balance_lamports: number;
}

/** Transaction */
export interface Transaction {
  id: string;
  org_id: string;
  from_wallet_id: string;
  to_address: string;
  amount_sol: number;
  amount_lamports: number;
  tx_type: string;
  status: string;
  signature: string | null;
  memo: string | null;
  created_at: string;
}

export interface TransferSolParams {
  from_wallet_id: string;
  to_address: string;
  amount_sol: number;
  memo?: string;
  idempotency_key?: string;
}

export interface BatchTransferItem {
  from_wallet_id: string;
  to_address: string;
  amount_sol: number;
  memo?: string;
}

/** Escrow */
export interface Escrow {
  id: string;
  org_id: string;
  funder_wallet_id: string;
  recipient_address: string;
  amount_sol: number;
  status: string;
  token_mint: string | null;
  arbiter_address: string | null;
  conditions: Record<string, unknown>;
  expires_at: string;
  created_at: string;
}

export interface CreateEscrowParams {
  funder_wallet_id: string;
  recipient_address: string;
  amount_sol: number;
  token_mint?: string;
  arbiter_address?: string;
  conditions?: Record<string, unknown>;
  expires_in_hours?: number;
}

/** Policy */
export interface Policy {
  id: string;
  org_id: string;
  name: string;
  rules: Record<string, unknown>;
  scope_type: string;
  scope_id: string | null;
  priority: number;
  is_active: boolean;
  created_at: string;
}

export interface CreatePolicyParams {
  name: string;
  rules: Record<string, unknown>;
  scope_type?: string;
  scope_id?: string;
  priority?: number;
}

/** Analytics */
export interface AnalyticsSummary {
  total_agents: number;
  total_wallets: number;
  total_transactions: number;
  total_volume_sol: number;
  active_escrows: number;
  period_days: number;
}

/** ACP - Agent Commerce Protocol */
export interface AcpJob {
  id: string;
  org_id: string;
  buyer_agent_id: string;
  seller_agent_id: string;
  title: string;
  description: string;
  price_usdc: number;
  phase: string;
  status: string;
  evaluator_agent_id: string | null;
  requirements: Record<string, unknown>;
  deliverables: Record<string, unknown>;
  agreed_terms: Record<string, unknown> | null;
  result_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface CreateAcpJobParams {
  buyer_agent_id: string;
  seller_agent_id: string;
  title: string;
  description: string;
  price_usdc: number;
  service_id?: string;
  evaluator_agent_id?: string;
  requirements?: Record<string, unknown>;
  deliverables?: Record<string, unknown>;
  fund_transfer?: boolean;
  principal_amount_usdc?: number;
}

export interface AcpMemo {
  id: string;
  job_id: string;
  sender_agent_id: string;
  memo_type: string;
  content: Record<string, unknown>;
  signature: string | null;
  created_at: string;
}

export interface ResourceOffering {
  id: string;
  agent_id: string;
  name: string;
  description: string;
  endpoint_path: string;
  parameters: Record<string, unknown>;
  response_schema: Record<string, unknown>;
  created_at: string;
}

export interface CreateOfferingParams {
  agent_id: string;
  name: string;
  description: string;
  endpoint_path: string;
  parameters?: Record<string, unknown>;
  response_schema?: Record<string, unknown>;
}

/** Swarms */
export interface Swarm {
  id: string;
  org_id: string;
  name: string;
  description: string;
  orchestrator_agent_id: string;
  swarm_type: string;
  status: string;
  max_members: number;
  is_public: boolean;
  config: Record<string, unknown>;
  created_at: string;
}

export interface CreateSwarmParams {
  name: string;
  description: string;
  orchestrator_agent_id: string;
  swarm_type?: string;
  max_members?: number;
  is_public?: boolean;
  config?: Record<string, unknown>;
}

export interface SwarmMember {
  id: string;
  swarm_id: string;
  agent_id: string;
  role: string;
  specialization: string | null;
  is_contestable: boolean;
  status: string;
  joined_at: string;
}

export interface SwarmTask {
  id: string;
  swarm_id: string;
  title: string;
  description: string;
  task_type: string;
  status: string;
  client_agent_id: string | null;
  subtasks: Record<string, unknown>[];
  result: Record<string, unknown> | null;
  created_at: string;
}

/** Client config */
export interface AgentWalletConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

/** API error */
export interface ApiErrorBody {
  error?: string;
  detail?: string;
  [key: string]: unknown;
}
