import type { AgentWallet } from '../client';
import type { Agent, CreateAgentParams, ListResponse } from '../types';

export class AgentsResource {
  constructor(private client: AgentWallet) {}

  /** Create a new AI agent */
  async create(params: CreateAgentParams): Promise<Agent> {
    return this.client.post<Agent>('/agents', {
      name: params.name,
      description: params.description ?? null,
      capabilities: params.capabilities ?? [],
      is_public: params.is_public ?? false,
      metadata: params.metadata ?? {},
    });
  }

  /** Get an agent by ID */
  async get(agentId: string): Promise<Agent> {
    return this.client.get<Agent>(`/agents/${agentId}`);
  }

  /** List agents */
  async list(options?: { status?: string; limit?: number; offset?: number }): Promise<ListResponse<Agent>> {
    return this.client.get<ListResponse<Agent>>('/agents', {
      status: options?.status,
      limit: options?.limit ?? 50,
      offset: options?.offset ?? 0,
    });
  }

  /** Update an agent */
  async update(agentId: string, params: Partial<CreateAgentParams>): Promise<Agent> {
    return this.client.patch<Agent>(`/agents/${agentId}`, params as Record<string, unknown>);
  }
}
