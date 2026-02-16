import type { AgentWallet } from '../client';
import type { CreateSwarmParams, ListResponse, Swarm, SwarmMember, SwarmTask } from '../types';

export class SwarmsResource {
  constructor(private client: AgentWallet) {}

  // ── Swarm CRUD ──

  /** Create a swarm cluster */
  async create(params: CreateSwarmParams): Promise<Swarm> {
    const body: Record<string, unknown> = {
      name: params.name,
      description: params.description,
      orchestrator_agent_id: params.orchestrator_agent_id,
      swarm_type: params.swarm_type ?? 'general',
      max_members: params.max_members ?? 10,
      is_public: params.is_public ?? false,
    };
    if (params.config) body.config = params.config;
    return this.client.post<Swarm>('/swarms', body);
  }

  /** Get a swarm by ID */
  async get(swarmId: string): Promise<Swarm> {
    return this.client.get<Swarm>(`/swarms/${swarmId}`);
  }

  /** List swarms */
  async list(options?: { is_public?: boolean; limit?: number; offset?: number }): Promise<ListResponse<Swarm>> {
    const data = await this.client.get<{ swarms: Swarm[]; total: number }>('/swarms', {
      is_public: options?.is_public,
      limit: options?.limit ?? 20,
      offset: options?.offset ?? 0,
    });
    return { data: data.swarms, total: data.total };
  }

  // ── Members ──

  /** Add a member to a swarm */
  async addMember(swarmId: string, agentId: string, options?: { role?: string; specialization?: string; is_contestable?: boolean }): Promise<SwarmMember> {
    const body: Record<string, unknown> = {
      agent_id: agentId,
      role: options?.role ?? 'worker',
      is_contestable: options?.is_contestable ?? true,
    };
    if (options?.specialization) body.specialization = options.specialization;
    return this.client.post<SwarmMember>(`/swarms/${swarmId}/members`, body);
  }

  /** List swarm members */
  async listMembers(swarmId: string): Promise<ListResponse<SwarmMember>> {
    const data = await this.client.get<{ members: SwarmMember[]; total: number }>(`/swarms/${swarmId}/members`);
    return { data: data.members, total: data.total };
  }

  /** Remove a member from a swarm */
  async removeMember(swarmId: string, agentId: string): Promise<void> {
    await this.client.delete(`/swarms/${swarmId}/members/${agentId}`);
  }

  // ── Tasks ──

  /** Create a task in a swarm */
  async createTask(swarmId: string, title: string, description: string, options?: { task_type?: string; client_agent_id?: string }): Promise<SwarmTask> {
    const body: Record<string, unknown> = {
      title,
      description,
      task_type: options?.task_type ?? 'general',
    };
    if (options?.client_agent_id) body.client_agent_id = options.client_agent_id;
    return this.client.post<SwarmTask>(`/swarms/${swarmId}/tasks`, body);
  }

  /** Get a task by ID */
  async getTask(swarmId: string, taskId: string): Promise<SwarmTask> {
    return this.client.get<SwarmTask>(`/swarms/${swarmId}/tasks/${taskId}`);
  }

  /** List tasks in a swarm */
  async listTasks(swarmId: string, options?: { status?: string; limit?: number; offset?: number }): Promise<ListResponse<SwarmTask>> {
    const data = await this.client.get<{ tasks: SwarmTask[]; total: number }>(`/swarms/${swarmId}/tasks`, {
      status: options?.status,
      limit: options?.limit ?? 20,
      offset: options?.offset ?? 0,
    });
    return { data: data.tasks, total: data.total };
  }

  /** Assign a subtask to a worker agent */
  async assignSubtask(swarmId: string, taskId: string, subtaskId: string, agentId: string, description: string): Promise<SwarmTask> {
    return this.client.post<SwarmTask>(`/swarms/${swarmId}/tasks/${taskId}/assign`, {
      subtask_id: subtaskId,
      agent_id: agentId,
      description,
    });
  }

  /** Complete a subtask with results */
  async completeSubtask(swarmId: string, taskId: string, subtaskId: string, result: Record<string, unknown>): Promise<SwarmTask> {
    return this.client.post<SwarmTask>(`/swarms/${swarmId}/tasks/${taskId}/complete`, {
      subtask_id: subtaskId,
      result,
    });
  }
}
