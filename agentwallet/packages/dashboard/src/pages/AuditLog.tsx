import { useEffect, useState } from "react";
import {
  ScrollText,
  Loader2,
  Filter,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";
import { auditLog, type AuditEvent } from "../api";

const mockEvents: AuditEvent[] = [
  {
    id: "evt_001",
    actor_type: "user",
    actor_id: "usr_01",
    action: "agent.create",
    resource_type: "agent",
    resource_id: "ag_05",
    details: { name: "Bridge Relayer" },
    ip_address: "192.168.1.100",
    created_at: "2026-02-11T09:30:00Z",
  },
  {
    id: "evt_002",
    actor_type: "agent",
    actor_id: "ag_01",
    action: "transaction.submit",
    resource_type: "transaction",
    resource_id: "tx_001",
    details: { amount: "1.25", token: "ETH", chain: "ethereum" },
    ip_address: "10.0.0.50",
    created_at: "2026-02-11T08:30:00Z",
  },
  {
    id: "evt_003",
    actor_type: "system",
    actor_id: "system",
    action: "transaction.confirm",
    resource_type: "transaction",
    resource_id: "tx_001",
    details: { tx_hash: "0xabc...def", block: 19234567 },
    ip_address: "0.0.0.0",
    created_at: "2026-02-11T08:31:00Z",
  },
  {
    id: "evt_004",
    actor_type: "user",
    actor_id: "usr_01",
    action: "policy.update",
    resource_type: "policy",
    resource_id: "pol_02",
    details: { field: "rules", change: "added chain_restriction" },
    ip_address: "192.168.1.100",
    created_at: "2026-02-11T07:15:00Z",
  },
  {
    id: "evt_005",
    actor_type: "agent",
    actor_id: "ag_02",
    action: "transaction.submit",
    resource_type: "transaction",
    resource_id: "tx_002",
    details: { amount: "500", token: "USDC", chain: "polygon" },
    ip_address: "10.0.0.51",
    created_at: "2026-02-11T09:15:00Z",
  },
  {
    id: "evt_006",
    actor_type: "system",
    actor_id: "system",
    action: "transaction.fail",
    resource_type: "transaction",
    resource_id: "tx_003",
    details: { error: "Out of gas", gas_used: "85000" },
    ip_address: "0.0.0.0",
    created_at: "2026-02-11T07:46:00Z",
  },
  {
    id: "evt_007",
    actor_type: "user",
    actor_id: "usr_01",
    action: "agent.pause",
    resource_type: "agent",
    resource_id: "ag_03",
    details: { reason: "Manual pause for maintenance" },
    ip_address: "192.168.1.100",
    created_at: "2026-02-10T22:00:00Z",
  },
  {
    id: "evt_008",
    actor_type: "user",
    actor_id: "usr_02",
    action: "wallet.create",
    resource_type: "wallet",
    resource_id: "w_05",
    details: { chain: "arbitrum", label: "Bridge Relay Fund" },
    ip_address: "192.168.1.105",
    created_at: "2026-02-10T20:30:00Z",
  },
  {
    id: "evt_009",
    actor_type: "agent",
    actor_id: "ag_01",
    action: "transaction.submit",
    resource_type: "transaction",
    resource_id: "tx_004",
    details: { amount: "250", token: "USDC", chain: "solana" },
    ip_address: "10.0.0.50",
    created_at: "2026-02-10T18:20:00Z",
  },
  {
    id: "evt_010",
    actor_type: "system",
    actor_id: "system",
    action: "policy.enforce",
    resource_type: "policy",
    resource_id: "pol_01",
    details: { result: "allowed", agent_id: "ag_01", check: "spending_limit" },
    ip_address: "0.0.0.0",
    created_at: "2026-02-10T18:20:01Z",
  },
  {
    id: "evt_011",
    actor_type: "user",
    actor_id: "usr_01",
    action: "auth.login",
    resource_type: "user",
    resource_id: "usr_01",
    details: { method: "password" },
    ip_address: "203.0.113.42",
    created_at: "2026-02-10T16:00:00Z",
  },
  {
    id: "evt_012",
    actor_type: "system",
    actor_id: "system",
    action: "agent.key_rotate",
    resource_type: "agent",
    resource_id: "ag_04",
    details: { reason: "scheduled rotation" },
    ip_address: "0.0.0.0",
    created_at: "2026-02-10T12:00:00Z",
  },
];

const actorBadge = (type: string) => {
  switch (type) {
    case "user":
      return <span className="badge-blue">User</span>;
    case "agent":
      return <span className="badge-green">Agent</span>;
    case "system":
      return <span className="badge-gray">System</span>;
    default:
      return <span className="badge-gray">{type}</span>;
  }
};

const actionColor = (action: string) => {
  if (action.includes("create") || action.includes("login"))
    return "text-emerald-400";
  if (action.includes("delete") || action.includes("fail") || action.includes("revoke"))
    return "text-red-400";
  if (action.includes("update") || action.includes("pause") || action.includes("rotate"))
    return "text-amber-400";
  return "text-slate-300";
};

export default function AuditLog() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actorFilter, setActorFilter] = useState<string>("all");
  const [resourceFilter, setResourceFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string | number> = {
      limit: 100,
      offset: 0,
    };
    if (actorFilter !== "all") params.actor_type = actorFilter;
    if (resourceFilter !== "all") params.resource_type = resourceFilter;

    auditLog
      .list(params as Parameters<typeof auditLog.list>[0])
      .then((res) => {
        setEvents(res.events);
        setTotal(res.total);
      })
      .catch(() => {
        setEvents(mockEvents);
        setTotal(mockEvents.length);
      })
      .finally(() => setLoading(false));
  }, [actorFilter, resourceFilter]);

  const filteredEvents = events.filter((evt) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      evt.action.toLowerCase().includes(term) ||
      evt.actor_id.toLowerCase().includes(term) ||
      evt.resource_id.toLowerCase().includes(term) ||
      evt.resource_type.toLowerCase().includes(term)
    );
  });

  const pagedEvents = filteredEvents.slice(
    page * pageSize,
    (page + 1) * pageSize
  );
  const totalPages = Math.ceil(filteredEvents.length / pageSize);

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Audit Log</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Complete history of all actions and system events
        </p>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0);
              }}
              className="input pl-9"
              placeholder="Search actions, actors, resources..."
            />
          </div>

          {/* Actor Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <span className="text-xs text-slate-500">Actor:</span>
            <div className="flex gap-1">
              {["all", "user", "agent", "system"].map((t) => (
                <button
                  key={t}
                  onClick={() => {
                    setActorFilter(t);
                    setPage(0);
                  }}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    actorFilter === t
                      ? "bg-brand-600 text-white"
                      : "bg-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Resource Type Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Resource:</span>
            <div className="flex gap-1">
              {["all", "agent", "wallet", "transaction", "policy", "user"].map(
                (t) => (
                  <button
                    key={t}
                    onClick={() => {
                      setResourceFilter(t);
                      setPage(0);
                    }}
                    className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                      resourceFilter === t
                        ? "bg-brand-600 text-white"
                        : "bg-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                )
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        ) : pagedEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500">
            <ScrollText className="w-10 h-10 mb-3" />
            <p className="text-sm font-medium">No events found</p>
            <p className="text-xs mt-1">
              Adjust your filters to see more results
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="table-header">Time</th>
                  <th className="table-header">Actor</th>
                  <th className="table-header">Action</th>
                  <th className="table-header">Resource</th>
                  <th className="table-header">Details</th>
                  <th className="table-header">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {pagedEvents.map((evt) => (
                  <tr
                    key={evt.id}
                    className="hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="table-cell text-xs text-slate-500 whitespace-nowrap">
                      {new Date(evt.created_at).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        {actorBadge(evt.actor_type)}
                        <code className="text-[10px] font-mono text-slate-500">
                          {evt.actor_id}
                        </code>
                      </div>
                    </td>
                    <td className="table-cell">
                      <code
                        className={`text-xs font-mono font-medium ${actionColor(
                          evt.action
                        )}`}
                      >
                        {evt.action}
                      </code>
                    </td>
                    <td className="table-cell">
                      <div className="text-xs">
                        <span className="text-slate-500">
                          {evt.resource_type}/
                        </span>
                        <code className="font-mono text-slate-300">
                          {evt.resource_id}
                        </code>
                      </div>
                    </td>
                    <td className="table-cell max-w-[200px]">
                      <code className="text-[10px] font-mono text-slate-500 truncate block">
                        {JSON.stringify(evt.details)}
                      </code>
                    </td>
                    <td className="table-cell">
                      <code className="text-xs font-mono text-slate-600">
                        {evt.ip_address}
                      </code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800">
            <p className="text-xs text-slate-500">
              Showing {page * pageSize + 1}-
              {Math.min((page + 1) * pageSize, filteredEvents.length)} of{" "}
              {filteredEvents.length} events
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-slate-500">
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
