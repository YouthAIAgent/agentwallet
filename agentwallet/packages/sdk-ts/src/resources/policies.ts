import type { AgentWallet } from '../client';
import type { CreatePolicyParams, ListResponse, Policy } from '../types';

export class PoliciesResource {
  constructor(private client: AgentWallet) {}

  /** Create a spending policy */
  async create(params: CreatePolicyParams): Promise<Policy> {
    return this.client.post<Policy>('/policies', {
      name: params.name,
      rules: params.rules,
      scope_type: params.scope_type ?? 'org',
      scope_id: params.scope_id ?? null,
      priority: params.priority ?? 100,
    });
  }

  /** Get a policy by ID */
  async get(policyId: string): Promise<Policy> {
    return this.client.get<Policy>(`/policies/${policyId}`);
  }

  /** List policies */
  async list(options?: { limit?: number; offset?: number }): Promise<ListResponse<Policy>> {
    return this.client.get<ListResponse<Policy>>('/policies', {
      limit: options?.limit ?? 50,
      offset: options?.offset ?? 0,
    });
  }

  /** Update a policy */
  async update(policyId: string, params: Partial<CreatePolicyParams>): Promise<Policy> {
    return this.client.patch<Policy>(`/policies/${policyId}`, params as Record<string, unknown>);
  }

  /** Delete a policy */
  async delete(policyId: string): Promise<void> {
    await this.client.delete(`/policies/${policyId}`);
  }
}
