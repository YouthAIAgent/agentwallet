import { useEffect, useState } from "react";
import {
  CreditCard,
  Loader2,
  Check,
  Zap,
  Crown,
  Building2,
  Sparkles,
} from "lucide-react";
import { billing, type BillingInfo, type BillingTier } from "../api";

const mockBilling: BillingInfo = {
  tier: "starter",
  usage: {
    agents: { used: 5, limit: 10 },
    wallets: { used: 8, limit: 25 },
    transactions_monthly: { used: 847, limit: 5000 },
    api_calls_monthly: { used: 12450, limit: 50000 },
  },
  current_period_end: "2026-03-11T00:00:00Z",
  amount_due: 49,
};

const mockTiers: BillingTier[] = [
  {
    name: "free",
    price_monthly: 0,
    limits: {
      agents: 2,
      wallets: 5,
      transactions_monthly: 500,
      api_calls_monthly: 10000,
    },
    features: [
      "2 agents",
      "5 wallets",
      "500 transactions/month",
      "Basic analytics",
      "Community support",
    ],
  },
  {
    name: "starter",
    price_monthly: 49,
    limits: {
      agents: 10,
      wallets: 25,
      transactions_monthly: 5000,
      api_calls_monthly: 50000,
    },
    features: [
      "10 agents",
      "25 wallets",
      "5,000 transactions/month",
      "Advanced analytics",
      "Policy engine",
      "Email support",
      "Audit log (30 days)",
    ],
  },
  {
    name: "pro",
    price_monthly: 199,
    limits: {
      agents: 50,
      wallets: 100,
      transactions_monthly: 50000,
      api_calls_monthly: 500000,
    },
    features: [
      "50 agents",
      "100 wallets",
      "50,000 transactions/month",
      "Full analytics suite",
      "Advanced policies",
      "Priority support",
      "Audit log (1 year)",
      "Custom webhooks",
      "Multi-sig support",
    ],
  },
  {
    name: "enterprise",
    price_monthly: -1,
    limits: {
      agents: -1,
      wallets: -1,
      transactions_monthly: -1,
      api_calls_monthly: -1,
    },
    features: [
      "Unlimited agents",
      "Unlimited wallets",
      "Unlimited transactions",
      "Dedicated infrastructure",
      "Custom SLAs",
      "24/7 support",
      "SOC 2 compliance",
      "On-premise option",
      "Custom integrations",
    ],
  },
];

const tierIcons: Record<string, typeof Zap> = {
  free: Sparkles,
  starter: Zap,
  pro: Crown,
  enterprise: Building2,
};

const tierColors: Record<string, { bg: string; border: string; text: string }> = {
  free: {
    bg: "bg-slate-800",
    border: "border-slate-700",
    text: "text-slate-300",
  },
  starter: {
    bg: "bg-brand-600/10",
    border: "border-brand-500/30",
    text: "text-brand-400",
  },
  pro: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    text: "text-amber-400",
  },
  enterprise: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
  },
};

function UsageMeter({
  label,
  used,
  limit,
}: {
  label: string;
  used: number;
  limit: number;
}) {
  const pct = limit > 0 ? (used / limit) * 100 : 0;
  const color =
    pct >= 90
      ? "bg-red-500"
      : pct >= 70
      ? "bg-amber-500"
      : "bg-brand-500";
  const textColor =
    pct >= 90
      ? "text-red-400"
      : pct >= 70
      ? "text-amber-400"
      : "text-brand-400";

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-300 font-medium">{label}</span>
        <span className={`text-sm font-mono font-medium ${textColor}`}>
          {used.toLocaleString()} / {limit.toLocaleString()}
        </span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <p className="text-[10px] text-slate-600 mt-1 text-right">
        {pct.toFixed(1)}% used
      </p>
    </div>
  );
}

export default function Billing() {
  const [billingInfo, setBillingInfo] = useState<BillingInfo | null>(null);
  const [tiers, setTiers] = useState<BillingTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      billing
        .current()
        .then(setBillingInfo)
        .catch(() => setBillingInfo(mockBilling)),
      billing
        .tiers()
        .then((res) => setTiers(res.tiers))
        .catch(() => setTiers(mockTiers)),
    ]).finally(() => setLoading(false));
  }, []);

  const handleUpgrade = async (tierName: string) => {
    setUpgrading(tierName);
    try {
      const res = await billing.upgrade(tierName);
      window.open(res.checkout_url, "_blank");
    } catch {
      // Demo: just show a message
      alert(`Upgrade to ${tierName} initiated (demo mode)`);
    } finally {
      setUpgrading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  const info = billingInfo!;
  const currentTierIndex = tiers.findIndex((t) => t.name === info.tier);

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Billing & Usage</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Manage your subscription and monitor resource usage
        </p>
      </div>

      {/* Current Plan */}
      <div className="card mb-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                tierColors[info.tier]?.bg || "bg-slate-800"
              }`}
            >
              {(() => {
                const Icon = tierIcons[info.tier] || CreditCard;
                return (
                  <Icon
                    className={`w-7 h-7 ${
                      tierColors[info.tier]?.text || "text-slate-400"
                    }`}
                  />
                );
              })()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white capitalize">
                  {info.tier} Plan
                </h2>
                <span
                  className={`badge ${
                    tierColors[info.tier]?.border || "border-slate-700"
                  } ${tierColors[info.tier]?.text || "text-slate-400"} ${
                    tierColors[info.tier]?.bg || "bg-slate-800"
                  }`}
                >
                  Current
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                {info.amount_due > 0 ? (
                  <>
                    ${info.amount_due}/month &middot; Renews{" "}
                    {new Date(info.current_period_end).toLocaleDateString()}
                  </>
                ) : (
                  "Free forever"
                )}
              </p>
            </div>
          </div>
          {info.tier !== "enterprise" && (
            <button
              onClick={() =>
                handleUpgrade(
                  tiers[Math.min(currentTierIndex + 1, tiers.length - 1)]?.name
                )
              }
              className="btn-primary"
            >
              <Zap className="w-4 h-4" />
              Upgrade Plan
            </button>
          )}
        </div>
      </div>

      {/* Usage Meters */}
      <div className="card mb-8">
        <h2 className="text-base font-semibold text-white mb-6">
          Current Usage
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <UsageMeter
            label="Agents"
            used={info.usage.agents.used}
            limit={info.usage.agents.limit}
          />
          <UsageMeter
            label="Wallets"
            used={info.usage.wallets.used}
            limit={info.usage.wallets.limit}
          />
          <UsageMeter
            label="Monthly Transactions"
            used={info.usage.transactions_monthly.used}
            limit={info.usage.transactions_monthly.limit}
          />
          <UsageMeter
            label="Monthly API Calls"
            used={info.usage.api_calls_monthly.used}
            limit={info.usage.api_calls_monthly.limit}
          />
        </div>
      </div>

      {/* Tier Comparison */}
      <h2 className="text-base font-semibold text-white mb-4">
        Available Plans
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        {tiers.map((tier) => {
          const isCurrent = tier.name === info.tier;
          const isPast =
            tiers.findIndex((t) => t.name === tier.name) < currentTierIndex;
          const colors = tierColors[tier.name] || tierColors.free;
          const Icon = tierIcons[tier.name] || CreditCard;

          return (
            <div
              key={tier.name}
              className={`bg-slate-900 rounded-xl border ${
                isCurrent ? colors.border : "border-slate-800"
              } p-6 flex flex-col ${
                isCurrent ? "ring-1 ring-brand-500/20" : ""
              }`}
            >
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors.bg}`}
                >
                  <Icon className={`w-5 h-5 ${colors.text}`} />
                </div>
                <h3 className="text-sm font-bold text-white capitalize">
                  {tier.name}
                </h3>
              </div>

              <div className="mb-5">
                {tier.price_monthly === 0 ? (
                  <div className="text-2xl font-bold text-white">Free</div>
                ) : tier.price_monthly < 0 ? (
                  <div className="text-2xl font-bold text-white">Custom</div>
                ) : (
                  <div>
                    <span className="text-2xl font-bold text-white">
                      ${tier.price_monthly}
                    </span>
                    <span className="text-sm text-slate-500">/month</span>
                  </div>
                )}
              </div>

              <ul className="space-y-2.5 flex-1 mb-6">
                {tier.features.map((feature, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Check
                      className={`w-4 h-4 flex-shrink-0 mt-0.5 ${colors.text}`}
                    />
                    <span className="text-slate-400">{feature}</span>
                  </li>
                ))}
              </ul>

              {isCurrent ? (
                <button
                  disabled
                  className="btn-secondary w-full opacity-60 cursor-not-allowed"
                >
                  Current Plan
                </button>
              ) : isPast ? (
                <button disabled className="btn-secondary w-full opacity-40 cursor-not-allowed">
                  Downgrade
                </button>
              ) : tier.price_monthly < 0 ? (
                <button
                  onClick={() => handleUpgrade("enterprise")}
                  className="btn-secondary w-full"
                >
                  Contact Sales
                </button>
              ) : (
                <button
                  onClick={() => handleUpgrade(tier.name)}
                  disabled={upgrading === tier.name}
                  className="btn-primary w-full"
                >
                  {upgrading === tier.name ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Zap className="w-4 h-4" />
                  )}
                  Upgrade
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
