import { useEffect, useState } from "react";
import { ArrowLeftRight, Loader2, Filter, ChevronLeft, ChevronRight } from "lucide-react";
import { transactions, type Transaction } from "../api";

const mockTransactions: Transaction[] = [
  {
    id: "tx_001",
    wallet_id: "w_01",
    agent_id: "ag_01",
    type: "transfer",
    status: "confirmed",
    chain: "ethereum",
    from_address: "0x1a2b3c4d5e6f7890abcdef1234567890abcdef12",
    to_address: "0x5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f",
    amount: "1.2500",
    token: "ETH",
    tx_hash: "0xabc123def456789012345678901234567890abcdef",
    gas_used: "21000",
    created_at: "2026-02-11T08:30:00Z",
    confirmed_at: "2026-02-11T08:31:00Z",
    signatures: ["0xsig1..."],
  },
  {
    id: "tx_002",
    wallet_id: "w_02",
    agent_id: "ag_02",
    type: "swap",
    status: "pending",
    chain: "polygon",
    from_address: "0x9876543210fedcba9876543210fedcba98765432",
    to_address: "0x3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
    amount: "500.00",
    token: "USDC",
    tx_hash: null,
    gas_used: null,
    created_at: "2026-02-11T09:15:00Z",
    confirmed_at: null,
    signatures: [],
  },
  {
    id: "tx_003",
    wallet_id: "w_01",
    agent_id: "ag_03",
    type: "contract_call",
    status: "failed",
    chain: "ethereum",
    from_address: "0x7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f",
    to_address: "0x1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d",
    amount: "0.0500",
    token: "ETH",
    tx_hash: "0x123456789abcdef0123456789abcdef0123456789",
    gas_used: "85000",
    created_at: "2026-02-11T07:45:00Z",
    confirmed_at: null,
    signatures: ["0xsig1...", "0xsig2..."],
  },
  {
    id: "tx_004",
    wallet_id: "w_03",
    agent_id: "ag_01",
    type: "transfer",
    status: "confirmed",
    chain: "solana",
    from_address: "7xKXqv9mNpL3yR5tU2wE8sD4fGhJ6kBnC1aZoYiO",
    to_address: "3yLM4oQrS5tU6vW7xY8zA9bC0dE1fG2hI3jK4lM5n",
    amount: "250.00",
    token: "USDC",
    tx_hash: "5abcxyzdefghijklmnopqrstuvwxyz1234567890",
    gas_used: "5000",
    created_at: "2026-02-11T06:20:00Z",
    confirmed_at: "2026-02-11T06:20:05Z",
    signatures: ["sig1"],
  },
  {
    id: "tx_005",
    wallet_id: "w_02",
    agent_id: "ag_04",
    type: "stake",
    status: "confirmed",
    chain: "ethereum",
    from_address: "0x5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a",
    to_address: "0x9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e",
    amount: "32.0000",
    token: "ETH",
    tx_hash: "0xdef0123456789abcdef0123456789abcdef012345",
    gas_used: "120000",
    created_at: "2026-02-10T22:00:00Z",
    confirmed_at: "2026-02-10T22:02:00Z",
    signatures: ["0xsig1...", "0xsig2...", "0xsig3..."],
  },
  {
    id: "tx_006",
    wallet_id: "w_05",
    agent_id: "ag_05",
    type: "transfer",
    status: "confirmed",
    chain: "arbitrum",
    from_address: "0x1122334455667788990011223344556677889900",
    to_address: "0xaabbccddeeff00112233445566778899aabbccdd",
    amount: "1200.00",
    token: "USDC",
    tx_hash: "0x789abcdef0123456789abcdef0123456789abcdef",
    gas_used: "65000",
    created_at: "2026-02-10T18:30:00Z",
    confirmed_at: "2026-02-10T18:30:02Z",
    signatures: ["0xsig1..."],
  },
  {
    id: "tx_007",
    wallet_id: "w_01",
    agent_id: "ag_01",
    type: "swap",
    status: "cancelled",
    chain: "ethereum",
    from_address: "0x1a2b3c4d5e6f7890abcdef1234567890abcdef12",
    to_address: "0x0000000000000000000000000000000000000000",
    amount: "5.0000",
    token: "ETH",
    tx_hash: null,
    gas_used: null,
    created_at: "2026-02-10T15:00:00Z",
    confirmed_at: null,
    signatures: [],
  },
  {
    id: "tx_008",
    wallet_id: "w_03",
    agent_id: "ag_01",
    type: "transfer",
    status: "confirmed",
    chain: "solana",
    from_address: "7xKXqv9mNpL3yR5tU2wE8sD4fGhJ6kBnC1aZoYiO",
    to_address: "9aPbQcRdSeTfUgVhWiXjYkZlAmBnCoDpEqFrGsHtIu",
    amount: "75.00",
    token: "USDC",
    tx_hash: "2mnopqrstuvwxyz1234567890abcdefghijklm",
    gas_used: "5000",
    created_at: "2026-02-10T12:00:00Z",
    confirmed_at: "2026-02-10T12:00:03Z",
    signatures: ["sig1"],
  },
];

const statusBadge = (status: string) => {
  switch (status) {
    case "confirmed":
      return <span className="badge-green">Confirmed</span>;
    case "pending":
      return <span className="badge-yellow">Pending</span>;
    case "failed":
      return <span className="badge-red">Failed</span>;
    case "cancelled":
      return <span className="badge-gray">Cancelled</span>;
    default:
      return <span className="badge-gray">{status}</span>;
  }
};

const typeBadge = (type: string) => {
  const labels: Record<string, string> = {
    transfer: "Transfer",
    swap: "Swap",
    stake: "Stake",
    contract_call: "Contract",
  };
  return (
    <span className="badge-blue">
      {labels[type] || type}
    </span>
  );
};

function truncateHash(hash: string | null): string {
  if (!hash) return "-";
  return `${hash.slice(0, 10)}...${hash.slice(-6)}`;
}

export default function Transactions() {
  const [txList, setTxList] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    const params = statusFilter !== "all" ? { status: statusFilter } : {};
    transactions
      .list({ ...params, limit: 50 })
      .then((res) => setTxList(res.transactions))
      .catch(() => setTxList(mockTransactions))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  const filteredTx =
    statusFilter === "all"
      ? txList
      : txList.filter((tx) => tx.status === statusFilter);

  const pagedTx = filteredTx.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(filteredTx.length / pageSize);

  const statusCounts = txList.reduce(
    (acc, tx) => {
      acc[tx.status] = (acc[tx.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Transactions</h1>
          <p className="text-slate-400 mt-1 text-sm">
            View and filter all transaction activity
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase font-medium">Confirmed</p>
          <p className="text-xl font-bold text-emerald-400 mt-1">
            {statusCounts["confirmed"] || 0}
          </p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase font-medium">Pending</p>
          <p className="text-xl font-bold text-amber-400 mt-1">
            {statusCounts["pending"] || 0}
          </p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase font-medium">Failed</p>
          <p className="text-xl font-bold text-red-400 mt-1">
            {statusCounts["failed"] || 0}
          </p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase font-medium">Cancelled</p>
          <p className="text-xl font-bold text-slate-400 mt-1">
            {statusCounts["cancelled"] || 0}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <Filter className="w-4 h-4 text-slate-500" />
        <div className="flex gap-2">
          {["all", "confirmed", "pending", "failed", "cancelled"].map((s) => (
            <button
              key={s}
              onClick={() => {
                setStatusFilter(s);
                setPage(0);
              }}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                statusFilter === s
                  ? "bg-brand-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700"
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        ) : pagedTx.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500">
            <ArrowLeftRight className="w-10 h-10 mb-3" />
            <p className="text-sm font-medium">No transactions found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="table-header">Type</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Amount</th>
                  <th className="table-header">Chain</th>
                  <th className="table-header">From / To</th>
                  <th className="table-header">Tx Hash</th>
                  <th className="table-header">Signatures</th>
                  <th className="table-header">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {pagedTx.map((tx) => (
                  <tr
                    key={tx.id}
                    className="hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="table-cell">{typeBadge(tx.type)}</td>
                    <td className="table-cell">{statusBadge(tx.status)}</td>
                    <td className="table-cell">
                      <span className="font-mono font-medium text-slate-100">
                        {parseFloat(tx.amount).toLocaleString()}
                      </span>
                      <span className="text-xs text-slate-500 ml-1.5">
                        {tx.token}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="text-xs text-slate-400 capitalize">
                        {tx.chain}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="text-xs font-mono">
                        <span className="text-slate-500">
                          {tx.from_address.slice(0, 8)}...
                        </span>
                        <span className="text-slate-600 mx-1">&rarr;</span>
                        <span className="text-slate-500">
                          {tx.to_address.slice(0, 8)}...
                        </span>
                      </div>
                    </td>
                    <td className="table-cell">
                      {tx.tx_hash ? (
                        <code className="text-xs font-mono text-brand-400">
                          {truncateHash(tx.tx_hash)}
                        </code>
                      ) : (
                        <span className="text-xs text-slate-600">-</span>
                      )}
                    </td>
                    <td className="table-cell">
                      <span className="text-xs text-slate-400">
                        {tx.signatures.length} sig
                        {tx.signatures.length !== 1 ? "s" : ""}
                      </span>
                    </td>
                    <td className="table-cell text-xs text-slate-500">
                      {new Date(tx.created_at).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
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
              {Math.min((page + 1) * pageSize, filteredTx.length)} of{" "}
              {filteredTx.length}
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(Math.max(0, page - 1))}
                disabled={page === 0}
                className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
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
