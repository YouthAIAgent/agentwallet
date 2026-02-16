import type { AgentWallet } from '../client';
import type { CreateWalletParams, ListResponse, Wallet, WalletBalance } from '../types';

export class WalletsResource {
  constructor(private client: AgentWallet) {}

  /** Create a new wallet */
  async create(params?: CreateWalletParams): Promise<Wallet> {
    return this.client.post<Wallet>('/wallets', {
      agent_id: params?.agent_id ?? null,
      wallet_type: params?.wallet_type ?? 'agent',
      label: params?.label ?? null,
    });
  }

  /** Get a wallet by ID */
  async get(walletId: string): Promise<Wallet> {
    return this.client.get<Wallet>(`/wallets/${walletId}`);
  }

  /** List wallets */
  async list(options?: { agent_id?: string; wallet_type?: string; limit?: number; offset?: number }): Promise<ListResponse<Wallet>> {
    return this.client.get<ListResponse<Wallet>>('/wallets', {
      agent_id: options?.agent_id,
      wallet_type: options?.wallet_type,
      limit: options?.limit ?? 50,
      offset: options?.offset ?? 0,
    });
  }

  /** Get wallet balance */
  async getBalance(walletId: string): Promise<WalletBalance> {
    return this.client.get<WalletBalance>(`/wallets/${walletId}/balance`);
  }
}
