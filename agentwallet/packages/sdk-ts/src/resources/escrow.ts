import type { AgentWallet } from '../client';
import type { CreateEscrowParams, Escrow, ListResponse } from '../types';

export class EscrowResource {
  constructor(private client: AgentWallet) {}

  /** Create an escrow contract */
  async create(params: CreateEscrowParams): Promise<Escrow> {
    return this.client.post<Escrow>('/escrow', {
      funder_wallet_id: params.funder_wallet_id,
      recipient_address: params.recipient_address,
      amount_sol: params.amount_sol,
      token_mint: params.token_mint ?? null,
      arbiter_address: params.arbiter_address ?? null,
      conditions: params.conditions ?? {},
      expires_in_hours: params.expires_in_hours ?? 24,
    });
  }

  /** Get an escrow by ID */
  async get(escrowId: string): Promise<Escrow> {
    return this.client.get<Escrow>(`/escrow/${escrowId}`);
  }

  /** List escrows */
  async list(options?: { status?: string; limit?: number; offset?: number }): Promise<ListResponse<Escrow>> {
    return this.client.get<ListResponse<Escrow>>('/escrow', {
      status: options?.status,
      limit: options?.limit ?? 50,
      offset: options?.offset ?? 0,
    });
  }

  /** Release escrow funds to recipient */
  async release(escrowId: string): Promise<Escrow> {
    return this.client.post<Escrow>(`/escrow/${escrowId}/action`, { action: 'release' });
  }

  /** Refund escrow funds to funder */
  async refund(escrowId: string): Promise<Escrow> {
    return this.client.post<Escrow>(`/escrow/${escrowId}/action`, { action: 'refund' });
  }

  /** Dispute an escrow */
  async dispute(escrowId: string, reason: string): Promise<Escrow> {
    return this.client.post<Escrow>(`/escrow/${escrowId}/action`, { action: 'dispute', reason });
  }
}
