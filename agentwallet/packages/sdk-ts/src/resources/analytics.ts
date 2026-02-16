import type { AgentWallet } from '../client';
import type { AnalyticsSummary } from '../types';

export class AnalyticsResource {
  constructor(private client: AgentWallet) {}

  /** Get analytics summary */
  async summary(days = 30): Promise<AnalyticsSummary> {
    return this.client.get<AnalyticsSummary>('/analytics/summary', { days });
  }

  /** Get daily analytics breakdown */
  async daily(options?: { days?: number; agent_id?: string }): Promise<Record<string, unknown>[]> {
    return this.client.get<Record<string, unknown>[]>('/analytics/daily', {
      days: options?.days ?? 30,
      agent_id: options?.agent_id,
    });
  }

  /** Get analytics grouped by agent */
  async byAgent(days = 30): Promise<Record<string, unknown>[]> {
    return this.client.get<Record<string, unknown>[]>('/analytics/agents', { days });
  }
}
