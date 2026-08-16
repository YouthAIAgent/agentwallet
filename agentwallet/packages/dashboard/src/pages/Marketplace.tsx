import { useCallback, useEffect, useState } from "react";
import {
  Plus,
  Send,
  RefreshCw,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Wallet as WalletIcon,
  Bot,
  ExternalLink,
  Sparkles,
  Coins,
  ChevronRight,
} from "lucide-react";
import { tasks, agents, explorerUrl, shortSig, type Task, type TaskStats } from "../api";

const CATEGORIES = ["general", "research", "writing", "coding", "data", "social"];

const STATUS_STYLES: Record<string, string> = {
  posted: "text-ink-300 bg-ink-600/40 border-ink-700",
  funded: "text-sky-400 bg-sky-500/10 border-sky-500/20",
  assigned: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  in_progress: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  delivered: "text-brand-400 bg-brand-500/10 border-brand-500/20",
  released: "text-brand-400 bg-brand-500/10 border-brand-500/20",
  refunded: "text-red-400 bg-red-500/10 border-red-500/20",
  cancelled: "text-ink-400 bg-ink-600/40 border-ink-700",
  disputed: "text-red-400 bg-red-500/10 border-red-500/20",
};

const STATUS_LABELS: Record<string, string> = {
  posted: "posted",
  funded: "funded",
  assigned: "assigned",
  in_progress: "running",
  delivered: "delivered",
  released: "paid ✓",
  refunded: "refunded",
  cancelled: "cancelled",
  disputed: "disputed",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium border ${STATUS_STYLES[status] || "text-ink-300 bg-ink-600/40 border-ink-700"}`}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}

export default function Marketplace() {
  const [taskList, setTaskList] = useState<Task[]>([]);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [agentOptions, setAgentOptions] = useState<{ id: string; name: string }[]>([]);

  // Post form
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("general");
  const [price, setPrice] = useState("0.05");
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState<string | null>(null);

  const [runningId, setRunningId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [list, st] = await Promise.all([tasks.list({ limit: 20 }), tasks.stats().catch(() => null)]);
      setTaskList(list);
      setStats(st);
    } catch {
      // silent — page still renders empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    agents.list({ limit: 50 }).then((res) => {
      setAgentOptions((res.agents || []).map((a) => ({ id: a.id, name: a.name })));
    }).catch(() => {});
  }, [refresh]);

  async function handlePost(e: React.FormEvent) {
    e.preventDefault();
    setPosting(true);
    setPostError(null);
    try {
      const task = await tasks.post({
        title,
        description,
        category,
        price_usdc: parseFloat(price),
        auto_assign: true,
      });
      setShowForm(false);
      setTitle("");
      setDescription("");
      setPrice("0.05");
      setCategory("general");
      await refresh();
      // trigger execution
      setRunningId(task.id);
      await tasks.run(task.id).catch(() => null);
      // worker picks it up within ~15s
      setTimeout(refresh, 3000);
    } catch (e) {
      setPostError(e instanceof Error ? e.message : "Failed to post task");
    } finally {
      setPosting(false);
      setRunningId(null);
    }
  }

  async function handleRun(taskId: string) {
    setRunningId(taskId);
    try {
      await tasks.run(taskId);
      await refresh();
      setTimeout(refresh, 4000);
      setTimeout(refresh, 10000);
    } finally {
      setRunningId(null);
    }
  }

  async function handleRefund(taskId: string) {
    if (!confirm("Refund the escrow to your wallet?")) return;
    try {
      await tasks.refund(taskId);
      await refresh();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Refund failed");
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-100 tracking-tight">Task Marketplace</h1>
          <p className="mt-1 text-sm text-ink-400">
            Post a task, fund it in escrow, and an agent delivers — payment releases on-chain.
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-500 hover:bg-brand-400 text-ink-950 text-sm font-semibold rounded transition-colors"
        >
          <Plus className="w-4 h-4" /> Post a task
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total tasks", value: stats?.total_tasks ?? 0, icon: Sparkles },
          { label: "Delivered", value: stats?.delivered_tasks ?? 0, icon: CheckCircle2 },
          { label: "Paid out", value: stats?.released_tasks ?? 0, icon: Coins },
          { label: "Fees earned (USDC)", value: `$${(stats?.platform_fees_usdc ?? 0).toFixed(4)}`, icon: WalletIcon },
        ].map((s) => (
          <div key={s.label} className="card p-5 border border-ink-800 rounded-lg">
            <div className="flex items-center gap-2 text-ink-400 text-xs font-medium uppercase tracking-wider">
              <s.icon className="w-4 h-4 text-brand-400" /> {s.label}
            </div>
            <div className="mt-2 text-2xl font-bold text-ink-100 font-mono">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Post form */}
      {showForm && (
        <form onSubmit={handlePost} className="card border border-ink-800 rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-ink-400 mb-1.5">
              Task title
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. Write a market research summary on AI agents"
              className="w-full px-3 py-2 bg-ink-950 border border-ink-800 rounded text-sm text-ink-100 placeholder-ink-600 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-ink-400 mb-1.5">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={4}
              placeholder="Describe exactly what the agent should deliver…"
              className="w-full px-3 py-2 bg-ink-950 border border-ink-800 rounded text-sm text-ink-100 placeholder-ink-600 focus:outline-none focus:border-brand-500 resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-ink-400 mb-1.5">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 bg-ink-950 border border-ink-800 rounded text-sm text-ink-100 focus:outline-none focus:border-brand-500"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium uppercase tracking-wider text-ink-400 mb-1.5">
                Price (USDC)
              </label>
              <input
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
                type="number"
                step="0.001"
                min="0.001"
                className="w-full px-3 py-2 bg-ink-950 border border-ink-800 rounded text-sm text-ink-100 focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>
          </div>
          {postError && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded text-sm text-red-400">
              {postError}
            </div>
          )}
          <div className="flex items-center gap-3 pt-1">
            <button
              type="submit"
              disabled={posting}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-500 hover:bg-brand-400 text-ink-950 text-sm font-semibold rounded transition-colors disabled:opacity-50"
            >
              {posting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {posting ? "Funding escrow…" : "Post + fund escrow"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2.5 bg-ink-800 hover:bg-ink-700 text-ink-100 text-sm font-medium rounded border border-ink-700 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Task list */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink-300 uppercase tracking-wider">Tasks</h2>
          <button onClick={refresh} className="text-ink-400 hover:text-ink-100 transition-colors" title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-ink-500">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
        ) : taskList.length === 0 ? (
          <div className="card border border-ink-800 rounded-lg p-10 text-center">
            <Bot className="w-10 h-10 text-ink-600 mx-auto" />
            <p className="mt-3 text-ink-300 font-medium">No tasks yet</p>
            <p className="mt-1 text-sm text-ink-500">
              Post your first task — it funds an on-chain escrow and an agent starts working.
            </p>
          </div>
        ) : (
          taskList.map((t) => (
            <div key={t.id} className="card border border-ink-800 rounded-lg p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-ink-100 truncate">{t.title}</h3>
                    <StatusBadge status={t.status} />
                  </div>
                  <p className="mt-1 text-sm text-ink-400 line-clamp-2">{t.description}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-ink-400 font-mono">
                    <span className="inline-flex items-center gap-1">
                      <Coins className="w-3.5 h-3.5 text-brand-400" /> ${t.price_usdc.toFixed(3)} {t.token_symbol}
                    </span>
                    {t.agent_name && (
                      <span className="inline-flex items-center gap-1">
                        <Bot className="w-3.5 h-3.5 text-sky-400" /> {t.agent_name}
                      </span>
                    )}
                    {t.escrow_id && (
                      <span className="inline-flex items-center gap-1">
                        <WalletIcon className="w-3.5 h-3.5 text-amber-400" /> escrow {shortSig(t.escrow_id)}
                      </span>
                    )}
                  </div>
                  {t.result_data && (
                    <div className="mt-3 p-3 bg-ink-950 border border-ink-800 rounded-lg">
                      <div className="flex items-center gap-1.5 text-xs text-brand-400 font-medium mb-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Delivery
                        {t.provider && <span className="text-ink-500 font-normal">· {t.provider} / {t.model}</span>}
                      </div>
                      <p className="text-sm text-ink-300 whitespace-pre-wrap line-clamp-4">
                        {typeof t.result_data.output === "string" ? t.result_data.output : JSON.stringify(t.result_data)}
                      </p>
                    </div>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  {(t.status === "funded" || t.status === "assigned" || t.status === "posted") && (
                    <button
                      onClick={() => handleRun(t.id)}
                      disabled={runningId === t.id}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs font-medium rounded border border-amber-500/20 transition-colors disabled:opacity-50"
                    >
                      {runningId === t.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      Run agent
                    </button>
                  )}
                  {(t.status === "posted" || t.status === "funded" || t.status === "assigned") && (
                    <button
                      onClick={() => handleRefund(t.id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-medium rounded border border-red-500/20 transition-colors"
                    >
                      <XCircle className="w-3.5 h-3.5" /> Refund
                    </button>
                  )}
                  {t.status === "released" && (
                    <span className="inline-flex items-center gap-1 text-xs text-brand-400">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Paid on-chain
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
