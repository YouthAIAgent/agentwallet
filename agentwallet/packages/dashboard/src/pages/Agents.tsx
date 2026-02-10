import { useEffect, useState } from "react";
import {
  Bot,
  Plus,
  X,
  Loader2,
  Copy,
  Check,
  Pause,
  Play,
  Trash2,
} from "lucide-react";
import {
  agents,
  type Agent,
  type CreateAgentRequest,
  type CreateAgentResponse,
} from "../api";

const mockAgents: Agent[] = [
  {
    id: "ag_01",
    name: "Trading Bot Alpha",
    description: "Automated DeFi trading on Ethereum mainnet",
    status: "active",
    api_key_prefix: "aw_sk_abc1",
    policy_id: "pol_01",
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-02-11T08:00:00Z",
    metadata: { version: "2.1" },
  },
  {
    id: "ag_02",
    name: "Payment Processor",
    description: "Handles USDC disbursements to vendors",
    status: "active",
    api_key_prefix: "aw_sk_def2",
    policy_id: "pol_02",
    created_at: "2026-01-20T14:30:00Z",
    updated_at: "2026-02-10T16:00:00Z",
    metadata: {},
  },
  {
    id: "ag_03",
    name: "Staking Manager",
    description: "Auto-compounds staking rewards",
    status: "paused",
    api_key_prefix: "aw_sk_ghi3",
    policy_id: null,
    created_at: "2026-02-01T09:00:00Z",
    updated_at: "2026-02-08T12:00:00Z",
    metadata: {},
  },
  {
    id: "ag_04",
    name: "NFT Minter",
    description: "Batch minting service for collections",
    status: "revoked",
    api_key_prefix: "aw_sk_jkl4",
    policy_id: "pol_01",
    created_at: "2025-12-10T18:00:00Z",
    updated_at: "2026-01-05T20:00:00Z",
    metadata: {},
  },
  {
    id: "ag_05",
    name: "Bridge Relayer",
    description: "Cross-chain bridge message relaying",
    status: "active",
    api_key_prefix: "aw_sk_mno5",
    policy_id: "pol_03",
    created_at: "2026-02-05T11:00:00Z",
    updated_at: "2026-02-11T07:30:00Z",
    metadata: { chains: ["ethereum", "polygon", "arbitrum"] },
  },
];

const statusBadge = (status: string) => {
  switch (status) {
    case "active":
      return <span className="badge-green">Active</span>;
    case "paused":
      return <span className="badge-yellow">Paused</span>;
    case "revoked":
      return <span className="badge-red">Revoked</span>;
    default:
      return <span className="badge-gray">{status}</span>;
  }
};

export default function Agents() {
  const [agentList, setAgentList] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [createResult, setCreateResult] = useState<CreateAgentResponse | null>(
    null
  );
  const [copied, setCopied] = useState(false);
  const [formData, setFormData] = useState<CreateAgentRequest>({
    name: "",
    description: "",
    policy_id: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    agents
      .list()
      .then((res) => setAgentList(res.agents))
      .catch(() => setAgentList(mockAgents))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload: CreateAgentRequest = {
        name: formData.name,
        description: formData.description || undefined,
        policy_id: formData.policy_id || undefined,
      };
      const res = await agents.create(payload);
      setCreateResult(res);
      setAgentList((prev) => [res.agent, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create agent");
    } finally {
      setSubmitting(false);
    }
  };

  const copyApiKey = async () => {
    if (createResult?.api_key) {
      await navigator.clipboard.writeText(createResult.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleStatusToggle = async (agent: Agent) => {
    const newStatus = agent.status === "active" ? "paused" : "active";
    try {
      const updated = await agents.update(agent.id, { status: newStatus });
      setAgentList((prev) =>
        prev.map((a) => (a.id === agent.id ? updated : a))
      );
    } catch {
      // Update locally for demo
      setAgentList((prev) =>
        prev.map((a) =>
          a.id === agent.id ? { ...a, status: newStatus as Agent["status"] } : a
        )
      );
    }
  };

  const closeModal = () => {
    setShowCreate(false);
    setCreateResult(null);
    setCopied(false);
    setFormData({ name: "", description: "", policy_id: "" });
    setError("");
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Agents</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Manage your autonomous agents and their API keys
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Create Agent
        </button>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        ) : agentList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500">
            <Bot className="w-10 h-10 mb-3" />
            <p className="text-sm font-medium">No agents yet</p>
            <p className="text-xs mt-1">Create your first agent to get started</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="table-header">Name</th>
                <th className="table-header">Status</th>
                <th className="table-header">API Key</th>
                <th className="table-header">Policy</th>
                <th className="table-header">Created</th>
                <th className="table-header text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {agentList.map((agent) => (
                <tr
                  key={agent.id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="table-cell">
                    <div>
                      <p className="font-medium text-slate-100">
                        {agent.name}
                      </p>
                      {agent.description && (
                        <p className="text-xs text-slate-500 mt-0.5 max-w-xs truncate">
                          {agent.description}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="table-cell">{statusBadge(agent.status)}</td>
                  <td className="table-cell">
                    <code className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-1 rounded">
                      {agent.api_key_prefix}...
                    </code>
                  </td>
                  <td className="table-cell">
                    {agent.policy_id ? (
                      <span className="text-xs text-brand-400 font-mono">
                        {agent.policy_id}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-600">None</span>
                    )}
                  </td>
                  <td className="table-cell text-slate-500 text-xs">
                    {new Date(agent.created_at).toLocaleDateString()}
                  </td>
                  <td className="table-cell text-right">
                    <div className="flex items-center justify-end gap-1">
                      {agent.status !== "revoked" && (
                        <button
                          onClick={() => handleStatusToggle(agent)}
                          className="p-1.5 rounded-md text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors"
                          title={
                            agent.status === "active" ? "Pause" : "Resume"
                          }
                        >
                          {agent.status === "active" ? (
                            <Pause className="w-3.5 h-3.5" />
                          ) : (
                            <Play className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}
                      <button
                        className="p-1.5 rounded-md text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
              <h2 className="text-lg font-semibold text-white">
                {createResult ? "Agent Created" : "Create New Agent"}
              </h2>
              <button
                onClick={closeModal}
                className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {createResult ? (
              <div className="p-6 space-y-4">
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
                  <p className="text-sm text-emerald-400 font-medium">
                    Agent "{createResult.agent.name}" created successfully!
                  </p>
                </div>
                <div>
                  <label className="label">
                    API Key (save this - it won't be shown again)
                  </label>
                  <div className="flex gap-2">
                    <code className="flex-1 input font-mono text-xs break-all">
                      {createResult.api_key}
                    </code>
                    <button
                      onClick={copyApiKey}
                      className="btn-secondary flex-shrink-0"
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
                <button onClick={closeModal} className="btn-primary w-full">
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreate} className="p-6 space-y-5">
                <div>
                  <label htmlFor="agentName" className="label">
                    Agent Name
                  </label>
                  <input
                    id="agentName"
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className="input"
                    placeholder="Trading Bot Alpha"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="agentDesc" className="label">
                    Description
                  </label>
                  <input
                    id="agentDesc"
                    type="text"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    className="input"
                    placeholder="Automated DeFi trading on Ethereum"
                  />
                </div>
                <div>
                  <label htmlFor="agentPolicy" className="label">
                    Policy ID (optional)
                  </label>
                  <input
                    id="agentPolicy"
                    type="text"
                    value={formData.policy_id || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, policy_id: e.target.value })
                    }
                    className="input"
                    placeholder="pol_..."
                  />
                </div>

                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
                    <p className="text-sm text-red-400">{error}</p>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="btn-primary flex-1"
                  >
                    {submitting && (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    )}
                    Create Agent
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
