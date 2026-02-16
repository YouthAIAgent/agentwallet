import type { AgentWalletConfig, ApiErrorBody } from './types';
import { AgentsResource } from './resources/agents';
import { WalletsResource } from './resources/wallets';
import { TransactionsResource } from './resources/transactions';
import { EscrowResource } from './resources/escrow';
import { PoliciesResource } from './resources/policies';
import { AnalyticsResource } from './resources/analytics';
import { AcpResource } from './resources/acp';
import { SwarmsResource } from './resources/swarms';

const DEFAULT_BASE_URL = 'https://api.agentwallet.fun/v1';
const DEFAULT_TIMEOUT = 30000;

export class AgentWalletError extends Error {
  status: number;
  body: ApiErrorBody;

  constructor(status: number, message: string, body: ApiErrorBody = {}) {
    super(message);
    this.name = 'AgentWalletError';
    this.status = status;
    this.body = body;
  }
}

export class AuthenticationError extends AgentWalletError {
  constructor(status: number, message: string, body?: ApiErrorBody) {
    super(status, message, body);
    this.name = 'AuthenticationError';
  }
}

export class NotFoundError extends AgentWalletError {
  constructor(status: number, message: string, body?: ApiErrorBody) {
    super(status, message, body);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends AgentWalletError {
  constructor(status: number, message: string, body?: ApiErrorBody) {
    super(status, message, body);
    this.name = 'ValidationError';
  }
}

export class RateLimitError extends AgentWalletError {
  constructor(status: number, message: string, body?: ApiErrorBody) {
    super(status, message, body);
    this.name = 'RateLimitError';
  }
}

const ERROR_MAP: Record<number, typeof AgentWalletError> = {
  401: AuthenticationError,
  403: AuthenticationError,
  404: NotFoundError,
  422: ValidationError,
  429: RateLimitError,
};

/**
 * AgentWallet SDK client.
 *
 * @example
 * ```ts
 * const aw = new AgentWallet({ apiKey: 'aw_live_...' });
 * const agent = await aw.agents.create({ name: 'trading-bot' });
 * ```
 */
export class AgentWallet {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  /** Manage AI agents */
  readonly agents: AgentsResource;
  /** Manage Solana wallets */
  readonly wallets: WalletsResource;
  /** Transfer SOL and tokens */
  readonly transactions: TransactionsResource;
  /** Trustless escrow contracts */
  readonly escrow: EscrowResource;
  /** Spending policies */
  readonly policies: PoliciesResource;
  /** Analytics and reporting */
  readonly analytics: AnalyticsResource;
  /** Agent Commerce Protocol */
  readonly acp: AcpResource;
  /** Multi-agent swarm coordination */
  readonly swarms: SwarmsResource;

  constructor(config: AgentWalletConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, '');
    this.timeout = config.timeout ?? DEFAULT_TIMEOUT;

    this.agents = new AgentsResource(this);
    this.wallets = new WalletsResource(this);
    this.transactions = new TransactionsResource(this);
    this.escrow = new EscrowResource(this);
    this.policies = new PoliciesResource(this);
    this.analytics = new AnalyticsResource(this);
    this.acp = new AcpResource(this);
    this.swarms = new SwarmsResource(this);
  }

  /** Make an authenticated API request */
  async request<T = Record<string, unknown>>(
    method: string,
    path: string,
    options?: { json?: Record<string, unknown>; params?: Record<string, unknown> },
  ): Promise<T> {
    let url = `${this.baseUrl}${path}`;

    if (options?.params) {
      const searchParams = new URLSearchParams();
      for (const [key, val] of Object.entries(options.params)) {
        if (val !== undefined && val !== null) {
          searchParams.set(key, String(val));
        }
      }
      const qs = searchParams.toString();
      if (qs) url += `?${qs}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const resp = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body: options?.json ? JSON.stringify(options.json) : undefined,
        signal: controller.signal,
      });

      if (resp.status >= 400) {
        let body: ApiErrorBody = {};
        try { body = (await resp.json()) as ApiErrorBody; } catch { /* empty */ }
        const message = body.error ?? body.detail ?? resp.statusText;
        const ErrorClass = ERROR_MAP[resp.status] ?? AgentWalletError;
        throw new ErrorClass(resp.status, message, body);
      }

      if (resp.status === 204) return {} as T;
      return (await resp.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  }

  async get<T = Record<string, unknown>>(path: string, params?: Record<string, unknown>): Promise<T> {
    return this.request<T>('GET', path, { params });
  }

  async post<T = Record<string, unknown>>(path: string, json?: Record<string, unknown>): Promise<T> {
    return this.request<T>('POST', path, { json });
  }

  async patch<T = Record<string, unknown>>(path: string, json?: Record<string, unknown>): Promise<T> {
    return this.request<T>('PATCH', path, { json });
  }

  async delete<T = Record<string, unknown>>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }
}
