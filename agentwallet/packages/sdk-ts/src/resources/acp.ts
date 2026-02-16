import type { AgentWallet } from '../client';
import type {
  AcpJob,
  AcpMemo,
  CreateAcpJobParams,
  CreateOfferingParams,
  ListResponse,
  ResourceOffering,
} from '../types';

export class AcpResource {
  constructor(private client: AgentWallet) {}

  // ── Jobs ──

  /** Create an ACP job */
  async createJob(params: CreateAcpJobParams): Promise<AcpJob> {
    const body: Record<string, unknown> = {
      buyer_agent_id: params.buyer_agent_id,
      seller_agent_id: params.seller_agent_id,
      title: params.title,
      description: params.description,
      price_usdc: params.price_usdc,
      fund_transfer: params.fund_transfer ?? false,
    };
    if (params.service_id) body.service_id = params.service_id;
    if (params.evaluator_agent_id) body.evaluator_agent_id = params.evaluator_agent_id;
    if (params.requirements) body.requirements = params.requirements;
    if (params.deliverables) body.deliverables = params.deliverables;
    if (params.principal_amount_usdc !== undefined) body.principal_amount_usdc = params.principal_amount_usdc;
    return this.client.post<AcpJob>('/acp/jobs', body);
  }

  /** Get an ACP job by ID */
  async getJob(jobId: string): Promise<AcpJob> {
    return this.client.get<AcpJob>(`/acp/jobs/${jobId}`);
  }

  /** List ACP jobs */
  async listJobs(options?: { agent_id?: string; phase?: string; limit?: number; offset?: number }): Promise<ListResponse<AcpJob>> {
    const data = await this.client.get<{ jobs: AcpJob[]; total: number }>('/acp/jobs', {
      agent_id: options?.agent_id,
      phase: options?.phase,
      limit: options?.limit ?? 20,
      offset: options?.offset ?? 0,
    });
    return { data: data.jobs, total: data.total };
  }

  /** Negotiate job terms (seller) */
  async negotiate(jobId: string, sellerAgentId: string, agreedTerms: Record<string, unknown>, agreedPriceUsdc?: number): Promise<AcpJob> {
    const body: Record<string, unknown> = { agreed_terms: agreedTerms };
    if (agreedPriceUsdc !== undefined) body.agreed_price_usdc = agreedPriceUsdc;
    return this.client.request<AcpJob>('POST', `/acp/jobs/${jobId}/negotiate`, {
      json: body,
      params: { seller_agent_id: sellerAgentId },
    });
  }

  /** Fund a job (buyer) */
  async fund(jobId: string, buyerAgentId: string): Promise<AcpJob> {
    return this.client.request<AcpJob>('POST', `/acp/jobs/${jobId}/fund`, {
      params: { buyer_agent_id: buyerAgentId },
    });
  }

  /** Deliver job results (seller) */
  async deliver(jobId: string, sellerAgentId: string, resultData: Record<string, unknown>, notes?: string): Promise<AcpJob> {
    const body: Record<string, unknown> = { result_data: resultData };
    if (notes) body.notes = notes;
    return this.client.request<AcpJob>('POST', `/acp/jobs/${jobId}/deliver`, {
      json: body,
      params: { seller_agent_id: sellerAgentId },
    });
  }

  /** Evaluate delivered work (evaluator) */
  async evaluate(jobId: string, evaluatorAgentId: string, approved: boolean, evaluationNotes?: string, rating?: number): Promise<AcpJob> {
    const body: Record<string, unknown> = { approved };
    if (evaluationNotes) body.evaluation_notes = evaluationNotes;
    if (rating !== undefined) body.rating = rating;
    return this.client.request<AcpJob>('POST', `/acp/jobs/${jobId}/evaluate`, {
      json: body,
      params: { evaluator_agent_id: evaluatorAgentId },
    });
  }

  // ── Memos ──

  /** Send a signed memo on a job */
  async sendMemo(jobId: string, senderAgentId: string, memoType: string, content: Record<string, unknown>, signature?: string): Promise<AcpMemo> {
    const body: Record<string, unknown> = { memo_type: memoType, content };
    if (signature) body.signature = signature;
    return this.client.request<AcpMemo>('POST', `/acp/jobs/${jobId}/memos`, {
      json: body,
      params: { sender_agent_id: senderAgentId },
    });
  }

  /** List memos for a job */
  async listMemos(jobId: string): Promise<ListResponse<AcpMemo>> {
    const data = await this.client.get<{ memos: AcpMemo[]; total: number }>(`/acp/jobs/${jobId}/memos`);
    return { data: data.memos, total: data.total };
  }

  // ── Resource Offerings ──

  /** Create a resource offering */
  async createOffering(params: CreateOfferingParams): Promise<ResourceOffering> {
    return this.client.post<ResourceOffering>('/acp/offerings', {
      agent_id: params.agent_id,
      name: params.name,
      description: params.description,
      endpoint_path: params.endpoint_path,
      parameters: params.parameters ?? {},
      response_schema: params.response_schema ?? {},
    });
  }

  /** List resource offerings */
  async listOfferings(options?: { agent_id?: string; limit?: number; offset?: number }): Promise<ListResponse<ResourceOffering>> {
    const data = await this.client.get<{ offerings: ResourceOffering[]; total: number }>('/acp/offerings', {
      agent_id: options?.agent_id,
      limit: options?.limit ?? 20,
      offset: options?.offset ?? 0,
    });
    return { data: data.offerings, total: data.total };
  }
}
