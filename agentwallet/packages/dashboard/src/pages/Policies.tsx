import { useEffect, useState } from "react";
import {
  ShieldCheck,
  Plus,
  X,
  Loader2,
  ChevronDown,
  ChevronRight,
  Trash2,
  Edit3,
} from "lucide-react";
import { policies, type Policy, type CreatePolicyRequest, type PolicyRule } from "../api";

const mockPolicies: Policy[] = [
  {
    id: "pol_01",
    name: "Conservative Trading",
    description: "Low-risk policy for automated trading agents",
    rules: [
      {
        type: "spending_limit",
        params: { max_per_tx: 1000, max_daily: 5000, currency: "USD" },
      },
      {
        type: "whitelist",
        params: {
          addresses: [
            "0x1a2b3c4d5e6f7890abcdef1234567890abcdef12",
            "0x9876543210fedcba9876543210fedcba98765432",
          ],
        },
      },
      {
        type: "time_window",
        params: { allowed_hours: { start: 8, end: 22 }, timezone: "UTC" },
      },
    ],
    created_at: "2026-01-10T10:00:00Z",
    updated_at: "2026-02-05T14:00:00Z",
  },
  {
    id: "pol_02",
    name: "Payment Processing",
    description: "Policy for USDC disbursements with approval thresholds",
    rules: [
      {
        type: "spending_limit",
        params: { max_per_tx: 10000, max_daily: 50000, currency: "USD" },
      },
      {
        type: "approval_required",
        params: { threshold_usd: 5000, approvers: 2 },
      },
      {
        type: "chain_restriction",
        params: { allowed_chains: ["ethereum", "polygon"] },
      },
    ],
    created_at: "2026-01-15T12:00:00Z",
    updated_at: "2026-02-01T09:30:00Z",
  },
  {
    id: "pol_03",
    name: "Bridge Operations",
    description: "Cross-chain bridge relayer with multi-chain access",
    rules: [
      {
        type: "spending_limit",
        params: { max_per_tx: 50000, max_daily: 200000, currency: "USD" },
      },
      {
        type: "chain_restriction",
        params: {
          allowed_chains: ["ethereum", "polygon", "arbitrum", "base"],
        },
      },
    ],
    created_at: "2026-02-05T11:00:00Z",
    updated_at: "2026-02-10T16:45:00Z",
  },
];

const ruleTypeLabels: Record<string, { label: string; color: string }> = {
  spending_limit: { label: "Spending Limit", color: "badge-yellow" },
  whitelist: { label: "Address Whitelist", color: "badge-green" },
  time_window: { label: "Time Window", color: "badge-blue" },
  approval_required: { label: "Approval Required", color: "badge-red" },
  chain_restriction: { label: "Chain Restriction", color: "badge bg-purple-500/10 text-purple-400 border border-purple-500/20" },
};

const defaultRules = `[
  {
    "type": "spending_limit",
    "params": {
      "max_per_tx": 1000,
      "max_daily": 5000,
      "currency": "USD"
    }
  }
]`;

export default function Policies() {
  const [policyList, setPolicyList] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    rules_json: defaultRules,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [jsonError, setJsonError] = useState("");

  useEffect(() => {
    policies
      .list()
      .then((res) => setPolicyList(res.policies))
      .catch(() => setPolicyList(mockPolicies))
      .finally(() => setLoading(false));
  }, []);

  const validateJson = (value: string): PolicyRule[] | null => {
    try {
      const parsed = JSON.parse(value);
      if (!Array.isArray(parsed)) {
        setJsonError("Rules must be a JSON array");
        return null;
      }
      for (const rule of parsed) {
        if (!rule.type || !rule.params) {
          setJsonError('Each rule must have "type" and "params" fields');
          return null;
        }
      }
      setJsonError("");
      return parsed;
    } catch {
      setJsonError("Invalid JSON syntax");
      return null;
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsedRules = validateJson(formData.rules_json);
    if (!parsedRules) return;

    setSubmitting(true);
    setError("");
    try {
      const payload: CreatePolicyRequest = {
        name: formData.name,
        description: formData.description || undefined,
        rules: parsedRules,
      };
      const policy = await policies.create(payload);
      setPolicyList((prev) => [policy, ...prev]);
      closeModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create policy");
    } finally {
      setSubmitting(false);
    }
  };

  const closeModal = () => {
    setShowCreate(false);
    setFormData({ name: "", description: "", rules_json: defaultRules });
    setError("");
    setJsonError("");
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Policies</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Define spending limits, whitelists, and approval rules for agents
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Create Policy
        </button>
      </div>

      {/* Policy List */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
        </div>
      ) : policyList.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-16 text-slate-500">
          <ShieldCheck className="w-10 h-10 mb-3" />
          <p className="text-sm font-medium">No policies yet</p>
          <p className="text-xs mt-1">
            Create a policy to define rules for your agents
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {policyList.map((policy) => (
            <div key={policy.id} className="card p-0 overflow-hidden">
              {/* Policy Header */}
              <button
                onClick={() => toggleExpand(policy.id)}
                className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-800/30 transition-colors text-left"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center flex-shrink-0">
                    <ShieldCheck className="w-5 h-5 text-brand-400" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-white text-sm">
                        {policy.name}
                      </h3>
                      <code className="text-[10px] font-mono text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded">
                        {policy.id}
                      </code>
                    </div>
                    {policy.description && (
                      <p className="text-xs text-slate-500 mt-0.5 truncate">
                        {policy.description}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="flex gap-1.5">
                    {policy.rules.map((rule, i) => {
                      const rt = ruleTypeLabels[rule.type];
                      return (
                        <span key={i} className={rt?.color || "badge-gray"}>
                          {rt?.label || rule.type}
                        </span>
                      );
                    })}
                  </div>
                  {expandedId === policy.id ? (
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  )}
                </div>
              </button>

              {/* Expanded Rules */}
              {expandedId === policy.id && (
                <div className="border-t border-slate-800 px-6 py-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Rules ({policy.rules.length})
                    </h4>
                    <div className="flex gap-1">
                      <button className="p-1.5 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors">
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {policy.rules.map((rule, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-800/50 rounded-lg p-4 border border-slate-800"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span
                            className={
                              ruleTypeLabels[rule.type]?.color || "badge-gray"
                            }
                          >
                            {ruleTypeLabels[rule.type]?.label || rule.type}
                          </span>
                        </div>
                        <pre className="text-xs font-mono text-slate-400 overflow-x-auto">
                          {JSON.stringify(rule.params, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 pt-3 border-t border-slate-800 flex justify-between text-xs text-slate-600">
                    <span>
                      Created{" "}
                      {new Date(policy.created_at).toLocaleDateString()}
                    </span>
                    <span>
                      Updated{" "}
                      {new Date(policy.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 sticky top-0 bg-slate-900 z-10">
              <h2 className="text-lg font-semibold text-white">
                Create New Policy
              </h2>
              <button
                onClick={closeModal}
                className="p-1 text-slate-500 hover:text-slate-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-5">
              <div>
                <label htmlFor="policyName" className="label">
                  Policy Name
                </label>
                <input
                  id="policyName"
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="input"
                  placeholder="Conservative Trading"
                  required
                />
              </div>
              <div>
                <label htmlFor="policyDesc" className="label">
                  Description
                </label>
                <input
                  id="policyDesc"
                  type="text"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className="input"
                  placeholder="Low-risk policy for trading agents"
                />
              </div>
              <div>
                <label htmlFor="policyRules" className="label">
                  Rules (JSON)
                </label>
                <textarea
                  id="policyRules"
                  value={formData.rules_json}
                  onChange={(e) => {
                    setFormData({ ...formData, rules_json: e.target.value });
                    validateJson(e.target.value);
                  }}
                  className="input font-mono text-xs min-h-[200px] resize-y"
                  spellCheck={false}
                />
                {jsonError && (
                  <p className="text-xs text-red-400 mt-1.5">{jsonError}</p>
                )}
                <div className="mt-2 text-[10px] text-slate-600 space-y-0.5">
                  <p>
                    Supported rule types: spending_limit, whitelist,
                    time_window, approval_required, chain_restriction
                  </p>
                </div>
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
                  disabled={submitting || !!jsonError}
                  className="btn-primary flex-1"
                >
                  {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  Create Policy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
