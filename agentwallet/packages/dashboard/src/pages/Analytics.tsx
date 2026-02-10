import { useEffect, useState } from "react";
import { Loader2, TrendingUp, TrendingDown, DollarSign, Activity, Users } from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  analytics,
  type DailySpend,
  type AgentSpend,
  type AnalyticsSummary,
} from "../api";

const mockDailySpend: DailySpend[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 86400000).toISOString().split("T")[0],
  total_usd: Math.round((500 + Math.random() * 3000) * 100) / 100,
  tx_count: Math.floor(10 + Math.random() * 90),
}));

const mockAgentBreakdown: AgentSpend[] = [
  { agent_id: "ag_01", agent_name: "Trading Bot Alpha", total_usd: 18450.0, tx_count: 620 },
  { agent_id: "ag_02", agent_name: "Payment Processor", total_usd: 12300.0, tx_count: 340 },
  { agent_id: "ag_03", agent_name: "Staking Manager", total_usd: 8200.0, tx_count: 150 },
  { agent_id: "ag_04", agent_name: "NFT Minter", total_usd: 2100.0, tx_count: 85 },
  { agent_id: "ag_05", agent_name: "Bridge Relayer", total_usd: 5640.0, tx_count: 210 },
];

const mockSummary: AnalyticsSummary = {
  total_spend_usd: 46690.0,
  total_transactions: 1405,
  active_agents: 8,
  active_wallets: 22,
  avg_tx_value: 33.23,
  period_days: 30,
};

function formatUSD(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export default function Analytics() {
  const [dailySpend, setDailySpend] = useState<DailySpend[]>([]);
  const [agentBreakdown, setAgentBreakdown] = useState<AgentSpend[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    Promise.all([
      analytics
        .dailySpend(period)
        .then((res) => setDailySpend(res.data))
        .catch(() => setDailySpend(mockDailySpend)),
      analytics
        .agentBreakdown()
        .then((res) => setAgentBreakdown(res.data))
        .catch(() => setAgentBreakdown(mockAgentBreakdown)),
      analytics
        .summary(period)
        .then(setSummary)
        .catch(() => setSummary(mockSummary)),
    ]).finally(() => setLoading(false));
  }, [period]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  const s = summary!;

  const summaryCards = [
    {
      label: "Total Spend",
      value: formatUSD(s.total_spend_usd),
      icon: DollarSign,
      color: "text-brand-400",
      bgColor: "bg-brand-500/10",
      trend: "+12.5%",
      trendUp: true,
    },
    {
      label: "Total Transactions",
      value: s.total_transactions.toLocaleString(),
      icon: Activity,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      trend: "+8.3%",
      trendUp: true,
    },
    {
      label: "Active Agents",
      value: s.active_agents.toString(),
      icon: Users,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      trend: "+2",
      trendUp: true,
    },
    {
      label: "Avg Tx Value",
      value: `$${s.avg_tx_value.toFixed(2)}`,
      icon: TrendingUp,
      color: "text-sky-400",
      bgColor: "bg-sky-500/10",
      trend: "-3.1%",
      trendUp: false,
    },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Spend analysis and agent performance metrics
          </p>
        </div>
        <div className="flex gap-2">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setPeriod(d)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                period === d
                  ? "bg-brand-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700"
              }`}
            >
              {d}D
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {summaryCards.map((card) => (
          <div key={card.label} className="card">
            <div className="flex items-center justify-between mb-3">
              <div
                className={`w-10 h-10 ${card.bgColor} rounded-xl flex items-center justify-center`}
              >
                <card.icon className={`w-5 h-5 ${card.color}`} />
              </div>
              <div
                className={`flex items-center gap-1 text-xs font-medium ${
                  card.trendUp ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {card.trendUp ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                {card.trend}
              </div>
            </div>
            <p className="text-2xl font-bold text-white">{card.value}</p>
            <p className="text-xs text-slate-500 mt-1">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Daily Spend Line Chart */}
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-1">
            Daily Spend Trend
          </h2>
          <p className="text-xs text-slate-500 mb-6">
            USD value of all transactions per day
          </p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailySpend}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#1e293b"
                  vertical={false}
                />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#64748b", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) =>
                    new Date(v).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })
                  }
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fill: "#64748b", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  labelStyle={{ color: "#94a3b8" }}
                  formatter={(value: number, name: string) => [
                    name === "total_usd"
                      ? formatUSD(value)
                      : value.toString(),
                    name === "total_usd" ? "Spend" : "Tx Count",
                  ]}
                  labelFormatter={(label) =>
                    new Date(label).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })
                  }
                />
                <Legend
                  wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
                  formatter={(value) =>
                    value === "total_usd" ? "Spend (USD)" : "Tx Count"
                  }
                />
                <Line
                  type="monotone"
                  dataKey="total_usd"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: "#6366f1" }}
                />
                <Line
                  type="monotone"
                  dataKey="tx_count"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: "#10b981" }}
                  yAxisId={0}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent Breakdown Bar Chart */}
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-1">
            Agent Spend Breakdown
          </h2>
          <p className="text-xs text-slate-500 mb-6">
            Total spend per agent over the selected period
          </p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={agentBreakdown}
                layout="vertical"
                margin={{ left: 20 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#1e293b"
                  horizontal={false}
                />
                <XAxis
                  type="number"
                  tick={{ fill: "#64748b", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <YAxis
                  type="category"
                  dataKey="agent_name"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={130}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  labelStyle={{ color: "#e2e8f0" }}
                  formatter={(value: number) => [formatUSD(value), "Total Spend"]}
                />
                <Bar
                  dataKey="total_usd"
                  fill="#6366f1"
                  radius={[0, 4, 4, 0]}
                  barSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Agent Details Table */}
      <div className="card p-0 overflow-hidden mt-6">
        <div className="px-6 py-4 border-b border-slate-800">
          <h2 className="text-base font-semibold text-white">
            Agent Performance Details
          </h2>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="table-header">Agent</th>
              <th className="table-header text-right">Total Spend</th>
              <th className="table-header text-right">Transactions</th>
              <th className="table-header text-right">Avg per Tx</th>
              <th className="table-header text-right">Share</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {agentBreakdown.map((agent) => (
              <tr
                key={agent.agent_id}
                className="hover:bg-slate-800/30 transition-colors"
              >
                <td className="table-cell font-medium text-slate-100">
                  {agent.agent_name}
                </td>
                <td className="table-cell text-right font-mono text-slate-200">
                  {formatUSD(agent.total_usd)}
                </td>
                <td className="table-cell text-right text-slate-400">
                  {agent.tx_count.toLocaleString()}
                </td>
                <td className="table-cell text-right text-slate-400">
                  ${(agent.total_usd / agent.tx_count).toFixed(2)}
                </td>
                <td className="table-cell text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-500 rounded-full"
                        style={{
                          width: `${(agent.total_usd / s.total_spend_usd) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-slate-500 w-10 text-right">
                      {((agent.total_usd / s.total_spend_usd) * 100).toFixed(1)}%
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
