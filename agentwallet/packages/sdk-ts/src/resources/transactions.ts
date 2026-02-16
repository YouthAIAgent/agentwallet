import type { AgentWallet } from '../client';
import type { BatchTransferItem, ListResponse, Transaction, TransferSolParams } from '../types';

export class TransactionsResource {
  constructor(private client: AgentWallet) {}

  /** Transfer SOL between wallets */
  async transferSol(params: TransferSolParams): Promise<Transaction> {
    return this.client.post<Transaction>('/transactions/transfer-sol', params as unknown as Record<string, unknown>);
  }

  /** Get a transaction by ID */
  async get(txId: string): Promise<Transaction> {
    return this.client.get<Transaction>(`/transactions/${txId}`);
  }

  /** List transactions */
  async list(options?: {
    agent_id?: string;
    wallet_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ListResponse<Transaction>> {
    return this.client.get<ListResponse<Transaction>>('/transactions', {
      agent_id: options?.agent_id,
      wallet_id: options?.wallet_id,
      status: options?.status,
      limit: options?.limit ?? 50,
      offset: options?.offset ?? 0,
    });
  }

  /** Batch transfer SOL to multiple recipients */
  async batchTransfer(transfers: BatchTransferItem[]): Promise<Transaction[]> {
    return this.client.post<Transaction[]>('/transactions/batch-transfer', {
      transfers,
    } as unknown as Record<string, unknown>);
  }
}
