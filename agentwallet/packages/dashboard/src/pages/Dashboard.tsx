import { useEffect, useState } from "react";
import {
  Bot,
  Wallet,
  ArrowLeftRight,
  DollarSign,
  TrendingUp,
  Loader2,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { dashboard, type DashboardOverview } from "../api";

// Mock data for preview when API is unavailable
const mockData: DashboardOverview = {
  total_agents: 12,
  total_wallets: 34,
  total_transactions: 1847,
  total_spend_usd: 42_690.55,
  recent_transactions: [
    {
      id: "tx_001",
      wallet_id: "w_01",
      agent_id: "ag_01",
      type: "transfer",
      status: "confirmed",
      chain: "ethereum",
      from_address: "0x1a2b...3c4d",
      to_address: "0x5e6f...7a8b",
      amount: "1.25",
      token: "ETH",
      tx_hash: "0xabc...def",
      gas_used: "21000",
      created_at: "2026-02-11T08:30:00Z",
      confirmed_at: "2026-02-11T08:31:00Z",
      signatures: ["sig1"],
    },
    {
      id: "tx_002",
      wallet_id: "w_02",
      agent_id: "ag_02",
      type: "swap",
      status: "pending",
      chain: "polygon",
      from_address: "0x9c0d...1e2f",
      to_address: "0x3a4b...5c6d",
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
      from_address: "0x7e8f...9a0b",
      to_address: "0x1c2d...3e4f",
      amount: "0.05",
      token: "ETH",
      tx_hash: "0x123...456",
      gas_used: "85000",
      created_at: "2026-02-11T07:45:00Z",
      confirmed_at: null,
      signatures: ["sig1", "sig2"],
    },
    {
      id: "tx_004",
      wallet_id: "w_03",
      agent_id: "ag_01",
      type: "transfer",
      status: "confirmed",
      chain: "solana",
      from_address: "7xKX...9mNp",
      to_address: "3yLM...4oQr",
      amount: "250.00",
      token: "USDC",
      tx_hash: "5abc...xyz",
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
      from_address: "0x5f6a...7b8c",
      to_address: "0x9d0e...1f2a",
      amount: "32.00",
      token: "ETH",
      tx_hash: "0xdef...ghi",
      gas_used: "120000",
      created_at: "2026-02-10T22:00:00Z",
      confirmed_at: "2026-02-10T22:02:00Z",
      signatures: ["sig1", "sig2", "sig3"],
    },
  ],
  daily_spend: Array.from({ length: 14 }, (_, i) => ({
    date: new Date(Date.now() - (13 - i) * 86400000)
      .toISOString()
      .split("T")[0],
    total_usd: Math.round((800 + Math.random() * 2500) * 100) / 100,
    tx_count: Math.floor(20 + Math.random() * 80),
  })),
};

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

function formatUSD(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboard
      .overview()
      .then(setData)
      .catch(() => setData(mockData))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  const d = data!;

  // Real deltas from daily_spend: last 7d vs prior 7d
  const spend = d.daily_spend ?? [];
  const sum = (arr: { total_usd: number; tx_count: number }[]) =>
    arr.reduce((s, x) => s + x.total_usd, 0);
  const txSum = (arr: { total_usd: number; tx_count: number }[]) =>
    arr.reduce((s, x) => s + (x.tx_count ?? 0), 0);
  const recent7 = spend.slice(-7);
  const prior7 = spend.slice(-14, -7);
  const spendDelta =
    sum(prior7) > 0
      ? Math.round(((sum(recent7) - sum(prior7)) / sum(prior7)) * 100)
      : null;
  const txDelta =
    txSum(prior7) > 0
      ? Math.round(((txSum(recent7) - txSum(prior7)) / txSum(prior7)) * 100)
      : null;

  const statCards = [
    {
      label: "agents",
      value: formatNumber(d.total_agents),
      icon: Bot,
      delta: null as number | null,
      suffix: "live · devnet",
    },
    {
      label: "wallets",
      value: formatNumber(d.total_wallets),
      icon: Wallet,
      delta: null as number | null,
      suffix: "live · devnet",
    },
    {
      label: "transactions",
      value: formatNumber(d.total_transactions),
      icon: ArrowLeftRight,
      delta: txDelta,
      suffix: "vs prev 7d",
    },
    {
      label: "total spend",
      value: formatUSD(d.total_spend_usd),
      icon: DollarSign,
      delta: spendDelta,
      suffix: "vs prev 7d",
    },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-heading">Dashboard</h1>
        <p className="text-ink-400 mt-1 text-sm">
          Overview of your AgentWallet Protocol activity
        </p>
      </div>

      {/* Stats Grid — terminal style */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => (
          <div
            key={card.label}
            className="card !p-5 hover:border-brand-500/40 transition-colors relative overflow-hidden"
          >
            {/* corner accent */}
            <div className="absolute top-0 right-0 w-10 h-10 border-t border-r border-brand-500/30" />
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] uppercase tracking-[0.2em] text-ink-500 font-medium">
                {card.label}
              </span>
              <card.icon className="w-4 h-4 text-brand-500/60" />
            </div>
            <p className="text-3xl font-bold text-ink-100 tracking-tight">
              {card.value}
            </p>
            <div className="mt-3 flex items-center gap-1.5">
              {card.delta !== null ? (
                <>
                  <TrendingUp className="w-3.5 h-3.5 text-brand-400" />
                  <span className="text-xs font-semibold text-brand-400">
                    {card.delta >= 0 ? "+" : ""}
                    {card.delta}%
                  </span>
                  <span className="text-[11px] text-ink-600">
                    {card.suffix}
                  </span>
                </>
              ) : card.suffix.includes("live") ? (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />
                  <span className="text-[11px] text-ink-500 uppercase tracking-wider">
                    {card.suffix}
                  </span>
                </>
              ) : (
                <span className="text-[11px] text-ink-600">{card.suffix}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Chart and Recent Transactions */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Spend Chart */}
        <div className="xl:col-span-2 card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-semibold text-ink-100">
                Daily Spend
              </h2>
              <p className="text-xs text-ink-500 mt-0.5">Last 14 days</p>
            </div>
            <div className="flex items-center gap-1.5 text-emerald-400 text-sm font-medium">
              <TrendingUp className="w-4 h-4" />
              Active
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={d.daily_spend}>
                <defs>
                  <linearGradient
                    id="spendGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="rgb(0,187,127)"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="100%"
                      stopColor="rgb(0,187,127)"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#272522"
                  vertical={false}
                />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#8a867e", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) =>
                    new Date(v).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })
                  }
                />
                <YAxis
                  tick={{ fill: "#8a867e", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#161513",
                    border: "1px solid #272522",
                    borderRadius: "2px",
                    fontSize: "12px",
                    fontFamily: "Geist Mono, monospace",
                  }}
                  labelStyle={{ color: "#c9c5bd" }}
                  itemStyle={{ color: "#00bb7f" }}
                  formatter={(value: number) => [formatUSD(value), "Spend"]}
                  labelFormatter={(label) =>
                    new Date(label).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })
                  }
                />
                <Area
                  type="monotone"
                  dataKey="total_usd"
                  stroke="#00bb7f"
                  strokeWidth={2}
                  fill="url(#spendGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="card">
          <h2 className="text-base font-semibold text-ink-100 mb-4">
            Recent Transactions
          </h2>
          <div className="space-y-3">
            {d.recent_transactions.slice(0, 5).map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between py-2.5 border-b border-ink-800/60 last:border-0"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-ink-200 truncate">
                      {tx.amount} {tx.token}
                    </span>
                    {statusBadge(tx.status)}
                  </div>
                  <p className="text-xs text-ink-500 mt-0.5 truncate">
                    {tx.type} on {tx.chain} &middot; {formatTime(tx.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
