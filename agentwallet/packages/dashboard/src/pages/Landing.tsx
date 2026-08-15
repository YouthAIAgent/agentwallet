import { useEffect, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import {
  Bot,
  Lock,
  Zap,
  CreditCard,
  Network,
  ScrollText,
  ArrowRight,
  Sun,
  Moon,
  Copy,
} from "lucide-react";
import Brand from "../components/Brand";
import { LogoMark } from "../components/Brand";
import { isAuthenticated } from "../api";
import { track } from "../analytics";

const features = [
  {
    icon: Bot,
    title: "Agent Wallets",
    desc: "Per-agent Solana wallets with PDA custody, programmable spend limits and full key isolation.",
  },
  {
    icon: Lock,
    title: "On-chain Escrow",
    desc: "Create, fund, release and refund escrow — dispute-ready settlements with no middleman.",
  },
  {
    icon: Zap,
    title: "x402 Pay-per-use",
    desc: "Agents pay for API calls over plain HTTP. Crypto-native monetization for model endpoints.",
  },
  {
    icon: CreditCard,
    title: "USDC Billing",
    desc: "Subscribe, renew and cancel — subscription rails that settle in USDC on-chain, no Stripe.",
  },
  {
    icon: Network,
    title: "Swarms & ACP",
    desc: "Multi-agent coordination with Agent Client Protocol out of the box. One wallet, many agents.",
  },
  {
    icon: ScrollText,
    title: "Audit Trail",
    desc: "Every move signed, logged and verifiable on-chain. Built for compliance from day one.",
  },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "devnet",
    tagline: "Try the protocol",
    cta: "Start on Devnet",
    highlight: false,
    features: [
      "3 agents",
      "5 wallets",
      "1,000 transactions / month",
      "Community support",
    ],
  },
  {
    name: "Pro",
    price: "$49",
    period: "USDC / month",
    tagline: "For growing teams",
    cta: "Upgrade with USDC",
    highlight: true,
    features: [
      "25 agents",
      "50 wallets",
      "50,000 transactions / month",
      "90-day analytics",
      "Priority support",
    ],
  },
  {
    name: "Enterprise",
    price: "$299",
    period: "USDC / month",
    tagline: "For scale",
    cta: "Talk to us",
    highlight: false,
    features: [
      "Custom agent & wallet limits",
      "Dedicated infrastructure",
      "SLA & compliance reports",
      "Dedicated support",
    ],
  },
];

const heroCmds = [
  "agentwallet escrow create --from agent --to vendor --amount 50 USDC",
  "agentwallet x402 pay --endpoint model.api --max 0.002 SOL",
  "agentwallet wallet create --type agent --label acme-bot",
  "agentwallet subscribe --plan pro --usdc 49",
];

/** Scroll-reveal wrapper — fades/slides children in when they enter view. */
function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { threshold: 0.12 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={`transition-all duration-700 ease-out ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
      } ${className}`}
    >
      {children}
    </div>
  );
}

function ThemeToggle() {
  const [light, setLight] = useState(
    () => localStorage.getItem("aw-theme") === "light"
  );
  useEffect(() => {
    document.documentElement.classList.toggle("light", light);
    localStorage.setItem("aw-theme", light ? "light" : "dark");
  }, [light]);
  return (
    <button
      onClick={() => setLight(!light)}
      className="p-2 rounded text-ink-400 hover:text-ink-200 hover:bg-ink-800/60 transition-colors"
      title="Toggle theme"
    >
      {light ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
    </button>
  );
}

function CopyCmd({ cmd }: { cmd: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(cmd);
        setCopied(true);
        setTimeout(() => setCopied(false), 1200);
      }}
      className="text-ink-500 hover:text-brand-400 transition-colors flex-shrink-0"
      title="Copy command"
    >
      {copied ? (
        <span className="text-[10px] text-brand-400">copied ✓</span>
      ) : (
        <Copy className="w-3.5 h-3.5" />
      )}
    </button>
  );
}

/** Terminal that types the demo commands, runs each with a spinner, and logs realistic success/failure output with exit codes. Loops forever. */
const runningMsgs = [
  "creating escrow account…",
  "signing x402 payment…",
  "deriving PDA + keypair…",
  "opening USDC subscription…",
];

const failMsgs = [
  "rpc rate limit exceeded — retry",
  "insufficient funds — fund the wallet first",
  "simulation failed: instruction error",
  "network timeout — retry with --retry 3",
  "signature verification failed",
];

const sig = () =>
  Array.from({ length: 4 }, () => "0123456789abcdef"[Math.floor(Math.random() * 16)]).join(
    ""
  );

const successMsgs = [
  `escrow_abc123 funded · 50 USDC locked (sig ${sig()}…)`,
  `paid 0.002 SOL · receipt 8z${sig()}… (confirmed)`,
  `wallet created · 7xKX…9mNp (agent type)`,
  `subscribed · pro renews in 30d (USDC 49)`,
];

type CmdResult = { ok: boolean; text: string };

function TypewriterTerminal() {
  const [lineIdx, setLineIdx] = useState(0);
  const [chars, setChars] = useState(0);
  const [phase, setPhase] = useState<"typing" | "running">("typing");
  const [results, setResults] = useState<CmdResult[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // keep the active line in view as output grows
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [results, lineIdx, chars, phase]);

  useEffect(() => {
    if (lineIdx >= heroCmds.length) {
      // pause, then restart the whole demo
      const t = setTimeout(() => {
        setLineIdx(0);
        setChars(0);
        setPhase("typing");
        setResults([]);
      }, 3500);
      return () => clearTimeout(t);
    }
    if (phase === "typing") {
      const full = heroCmds[lineIdx];
      if (chars < full.length) {
        const t = setTimeout(() => setChars((c) => c + 1), 20);
        return () => clearTimeout(t);
      }
      const t = setTimeout(() => setPhase("running"), 200);
      return () => clearTimeout(t);
    }
    // running — decide the outcome (≈20% failure) after a realistic delay
    const t = setTimeout(() => {
      const ok = Math.random() > 0.2;
      const text = ok
        ? successMsgs[lineIdx]
        : failMsgs[Math.floor(Math.random() * failMsgs.length)];
      setResults((r) => [...r, { ok, text }]);
      setLineIdx((i) => i + 1);
      setChars(0);
      setPhase("typing");
    }, 700 + Math.random() * 600);
    return () => clearTimeout(t);
  }, [lineIdx, chars, phase]);

  // copy buttons appear only after the whole demo has run
  const allDone = lineIdx >= heroCmds.length;

  return (
    <div
      ref={scrollRef}
      className="p-4 h-[320px] overflow-y-auto terminal-scroll"
    >
      {/* completed commands */}
      {results.map((r, i) => (
        <div key={i} className="mb-2.5">
          <div className="flex items-center justify-between gap-3">
            <code className="text-xs text-ink-300 truncate">
              <span className="text-brand-400 select-none">$ </span>
              {heroCmds[i]}
            </code>
            {allDone && (
              <span className="aw-fade-in">
                <CopyCmd cmd={heroCmds[i]} />
              </span>
            )}
          </div>
          <p
            className={`aw-fade-in text-xs mt-1 truncate ${
              r.ok ? "text-brand-400" : "text-red-400"
            }`}
          >
            {r.ok ? "✓" : "✗"} {r.text}
          </p>
          <p className="text-[10px] mt-0.5 text-ink-500">
            → exit {r.ok ? 0 : 1}
          </p>
        </div>
      ))}

      {/* current command */}
      {lineIdx < heroCmds.length && (
        <div className="mb-2.5">
          <code className="text-xs text-ink-300">
            <span className="text-brand-400 select-none">$ </span>
            {heroCmds[lineIdx].slice(0, chars)}
            {phase === "typing" && (
              <span className="aw-cursor text-brand-400">▍</span>
            )}
          </code>
          {phase === "running" && (
            <p className="aw-fade-in text-xs mt-1 text-ink-400">
              <span className="aw-spinner text-brand-400">⟳</span>{" "}
              {runningMsgs[lineIdx]}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* LiveStats — real platform numbers from GET /v1/public/stats,        */
/* refreshed every 60s. Graceful: hides itself if the API is down,     */
/* so the landing page never breaks on a stats fetch.                  */
/* ------------------------------------------------------------------ */
interface PublicStats {
  total_agents: number;
  total_wallets: number;
  total_transactions: number;
  total_escrows: number;
  total_volume_sol: number;
}

function fmt(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(Math.round(n));
}

function useCountUp(target: number, ms = 900): number {
  const [val, setVal] = useState(0);
  useEffect(() => {
    // setInterval (not rAF) so the animation also completes when the tab
    // is backgrounded/throttled — rAF is paused there and would stick at 0.
    const start = performance.now();
    const id = setInterval(() => {
      const p = Math.min(1, (performance.now() - start) / ms);
      // ease-out cubic so it lands softly
      setVal(target * (1 - Math.pow(1 - p, 3)));
      if (p >= 1) clearInterval(id);
    }, 16);
    return () => clearInterval(id);
  }, [target, ms]);
  return val;
}

function LiveStats() {
  const [stats, setStats] = useState<PublicStats | null>(null);
  // hooks first — one per stat, unconditional (Rules of Hooks)
  const txns = useCountUp(stats?.total_transactions ?? 0);
  const wallets = useCountUp(stats?.total_wallets ?? 0);
  const agents = useCountUp(stats?.total_agents ?? 0);
  const volume = useCountUp(stats?.total_volume_sol ?? 0);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch("/api/v1/public/stats", {
          headers: { Accept: "application/json" },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: PublicStats = await res.json();
        if (alive) setStats(data);
      } catch {
        // never break the landing page on a stats failure
      }
    };
    load();
    const id = setInterval(load, 60_000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  if (!stats) return null;

  const items = [
    { label: "On-chain txns", value: fmt(txns) },
    { label: "Wallets created", value: fmt(wallets) },
    { label: "Agents running", value: fmt(agents) },
    { label: "Volume", value: volume.toFixed(3) + " SOL" },
  ];

  return (
    <div className="mt-8 inline-flex flex-wrap items-stretch gap-px rounded-lg border border-ink-800 overflow-hidden bg-ink-800">
      {items.map((it, i) => (
        <div
          key={it.label}
          className={`px-4 py-2.5 bg-ink-950/95 min-w-[110px] ${
            i > 0 ? "border-l border-ink-800" : ""
          }`}
        >
          <div className="font-mono text-sm font-bold text-brand-400 tabular-nums">
            {it.value}
          </div>
          <div className="text-[9px] uppercase tracking-widest text-ink-500 mt-0.5">
            {it.label}
          </div>
        </div>
      ))}
      <div className="px-3 py-2.5 bg-ink-950/95 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />
        <span className="font-mono text-[9px] uppercase tracking-widest text-brand-400">
          live
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* LiveFeed — anonymized recent on-chain actions from GET /v1/public/  */
/* feed, refreshed every 30s (matches the endpoint's Redis TTL).       */
/* Graceful: hides itself if the API is down.                          */
/* ------------------------------------------------------------------ */
interface FeedItem {
  type: string;
  action: string;
  address: string;
  amount: string | null;
  timestamp: string;
}

function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

/* stable identity for an item, so React can tell new vs pushed-out */
function feedUid(it: FeedItem): string {
  return `${it.type}:${it.address}:${it.action}:${it.timestamp}`;
}

interface RenderedItem extends FeedItem {
  uid: string;
  entering: boolean;
  leaving: boolean;
  delay: number;
}

function FeedRow({ it }: { it: RenderedItem }) {
  const Icon = it.type === "escrow" ? Lock : it.type === "acp" ? Zap : ArrowRight;
  const tint =
    it.type === "escrow"
      ? "bg-amber-500/10 border-amber-500/20 text-amber-500"
      : it.type === "acp"
        ? "bg-sky-500/10 border-sky-500/20 text-sky-400"
        : "bg-brand-500/10 border-brand-500/20 text-brand-400";
  return (
    <div
      className={`flex items-center gap-3 px-3.5 py-2.5 ${
        it.entering ? "aw-feed-in" : it.leaving ? "aw-feed-out" : ""
      }`}
      style={it.delay ? { animationDelay: `${it.delay}ms` } : undefined}
    >
      <span
        className={`w-6 h-6 rounded border flex items-center justify-center shrink-0 ${tint}`}
      >
        <Icon className="w-3 h-3" />
      </span>
      <span className="font-mono text-[11px] text-ink-300 truncate flex-1">
        <span className="text-ink-100">{it.address}</span>{" "}
        <span className="text-ink-500">{it.action}</span>
      </span>
      {it.amount && (
        <span className="font-mono text-[11px] text-brand-400 tabular-nums whitespace-nowrap">
          {it.amount}
        </span>
      )}
      <span className="font-mono text-[10px] text-ink-600 whitespace-nowrap">
        {timeAgo(it.timestamp)}
      </span>
    </div>
  );
}

function LiveFeed() {
  const [rendered, setRendered] = useState<RenderedItem[]>([]);
  const [online, setOnline] = useState<number | null>(null);
  const firstLoad = useRef(true);

  // presence heartbeat — anonymous visitor id in localStorage, beats every 60s
  useEffect(() => {
    let alive = true;
    let vid = localStorage.getItem("aw_visitor_id");
    if (!vid) {
      vid =
        typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `v-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
      localStorage.setItem("aw_visitor_id", vid);
    }
    const beat = async () => {
      try {
        const res = await fetch("/api/v1/public/presence", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ visitor_id: vid }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: { online?: number } = await res.json();
        if (alive && typeof data.online === "number") setOnline(data.online);
      } catch {
        // hide the badge on failure — never break the landing page
      }
    };
    beat();
    const id = setInterval(beat, 60_000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch("/api/v1/public/feed", {
          headers: { Accept: "application/json" },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: { items?: FeedItem[] } = await res.json();
        if (!alive || !Array.isArray(data.items)) return;
        const next = data.items.slice(0, 6); // 2 extra for exit detection
        const nextUids = new Set(next.map(feedUid));
        const stagger = firstLoad.current;
        firstLoad.current = false;

        setRendered((prev) => {
          const prevUids = new Set(prev.map((r) => r.uid));
          // kept rows already played their entrance — clear the flag so the
          // animation never replays if React ever recreates the element
          const kept = prev.map((r) =>
            r.leaving
              ? r
              : { ...r, entering: false, leaving: !nextUids.has(r.uid) }
          );
          const fresh = next
            .filter((n) => !prevUids.has(feedUid(n)))
            .map((n) => ({
              ...n,
              uid: feedUid(n),
              entering: true,
              leaving: false,
              delay: 0,
            }));
          // stagger the initial batch; new arrivals animate instantly
          const withDelay = stagger
            ? fresh.map((f, i) => ({ ...f, delay: i * 70 }))
            : fresh;
          return [...withDelay, ...kept].sort(
            (a, b) =>
              new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          );
        });
      } catch {
        // never break the landing page on a feed failure
      }
    };
    load();
    const id = setInterval(load, 30_000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // prune items that finished their exit animation
  useEffect(() => {
    const id = setInterval(() => {
      setRendered((prev) =>
        prev.some((r) => r.leaving)
          ? prev.filter((r) => !r.leaving)
          : prev
      );
    }, 700);
    return () => clearInterval(id);
  }, []);

  const rows = rendered
    .filter((r) => !r.leaving)
    .slice(0, 4)
    .concat(rendered.filter((r) => r.leaving))
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

  if (rows.length === 0) return null;

  return (
    <div className="mt-4 max-w-md">
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 text-[9px] uppercase tracking-widest text-ink-500">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />
          Recent on-chain activity
        </div>
        {online !== null && (
          <span
            className="inline-flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-widest text-brand-400 whitespace-nowrap"
            title="Anonymous visitors seen in the last 90 seconds"
          >
            <span className="w-1 h-1 rounded-full bg-brand-500 animate-pulse" />
            {online} online now
          </span>
        )}
      </div>
      <div className="border border-ink-800 rounded-lg overflow-hidden divide-y divide-ink-800/60 bg-ink-950/60">
        {rows.map((it) => (
          <FeedRow key={it.uid} it={it} />
        ))}
      </div>
    </div>
  );
}

export default function Landing() {
  const [light, setLight] = useState(
    () => localStorage.getItem("aw-theme") === "light"
  );
  useEffect(() => {
    document.documentElement.classList.toggle("light", light);
    localStorage.setItem("aw-theme", light ? "light" : "dark");
  }, [light]);

  if (isAuthenticated()) {
    return <Navigate to="/app" replace />;
  }

  return (
    <div className="min-h-screen bg-ink-950 text-ink-100 relative overflow-x-hidden">
      {/* backdrop */}
      <div className="absolute inset-0 grid-bg pointer-events-none" />
      {/* animated gradient glow */}
      <div className="aw-glow absolute -top-44 left-1/2 -translate-x-1/2 w-[900px] h-[520px] bg-gradient-to-br from-brand-500/10 via-brand-400/5 to-transparent blur-3xl rounded-full pointer-events-none" />

      {/* Nav */}
      <header className="relative max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
        <Brand />
        <nav className="hidden md:flex items-center gap-8 text-sm text-ink-400">
          <a href="#features" className="hover:text-ink-200 transition-colors">
            Features
          </a>
          <a href="#pricing" className="hover:text-ink-200 transition-colors">
            Pricing
          </a>
          <a href="#devnet" className="hover:text-ink-200 transition-colors">
            Devnet
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link
            to="/login"
            className="btn-primary !px-4 !py-2 text-xs"
            onClick={() => track("click_launch_app")}
          >
            Launch App
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative max-w-6xl mx-auto px-6 pt-20 pb-24 grid lg:grid-cols-2 gap-14 items-center">
        <Reveal className="min-w-0">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 border border-brand-500/30 bg-brand-500/5 rounded text-[11px] text-brand-400 mb-7">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />
              SOLANA DEVNET · LIVE
            </div>
            <h1 className="text-[clamp(2.1rem,5vw,3.75rem)] font-bold text-heading tracking-[-0.05em] leading-[1.08] text-balance">
              The Payment Rail For The{" "}
              <span className="aw-shimmer-wrap aw-underline">
                <span className="aw-shimmer">Agent Economy</span>
              </span>
              .
            </h1>
            <p className="mt-6 text-ink-300 max-w-lg leading-relaxed">
              Spin up <span className="aw-caps">Solana wallets</span>,{" "}
              <span className="aw-caps">escrow</span> and{" "}
              <span className="aw-caps">pay-per-call billing</span> for your
              agents in minutes. No Stripe, no intermediaries — just{" "}
              <span className="aw-caps">on-chain money</span> moving
              automatically when your agents work.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Link
                to="/login"
                className="btn-primary whitespace-nowrap"
                onClick={() => track("click_launch_dashboard")}
              >
                Launch Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href="#devnet"
                className="btn-secondary whitespace-nowrap"
                onClick={() => track("click_try_devnet")}
              >
                Try Devnet — Free
              </a>
            </div>
            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] text-ink-500 uppercase tracking-widest">
              <span>● Escrow</span>
              <span>● x402</span>
              <span>● USDC</span>
              <span>● Swarms</span>
            </div>
            <LiveStats />
            <LiveFeed />
          </div>
        </Reveal>

        {/* Terminal demo */}
        <Reveal delay={150} className="min-w-0">
          <div className="card !p-0 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-ink-800 bg-ink-900/80">
              <span className="text-[11px] text-ink-500 uppercase tracking-widest">
                agentwallet.sh
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-brand-500" />
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span className="w-2 h-2 rounded-full bg-red-500" />
              </span>
            </div>
            <TypewriterTerminal />
          </div>
        </Reveal>
      </section>

      {/* Features */}
      <section id="features" className="relative max-w-6xl mx-auto px-6 py-20">
        <Reveal>
          <div className="max-w-2xl mb-12">
            <p className="text-[11px] text-brand-400 uppercase tracking-[0.3em] mb-3">
              Features
            </p>
            <h2 className="text-3xl font-bold text-heading tracking-tight">
              Everything agents need to move money.
            </h2>
            <p className="mt-3 text-ink-300">
              Built for autonomous systems — every primitive is a Solana
              program, every action is on-chain.
            </p>
          </div>
        </Reveal>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <Reveal key={f.title} delay={(i % 3) * 90}>
              <div className="card h-full hover:border-brand-500/40 transition-colors">
                <div className="w-9 h-9 rounded flex items-center justify-center bg-brand-500/10 border border-brand-500/20 mb-4">
                  <f.icon className="w-4 h-4 text-brand-400" />
                </div>
                <h3 className="text-sm font-bold text-ink-100 mb-1.5">
                  {f.title}
                </h3>
                <p className="text-xs text-ink-400 leading-relaxed">{f.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="relative max-w-6xl mx-auto px-6 py-20">
        <Reveal>
          <div className="max-w-2xl mb-12">
            <p className="text-[11px] text-brand-400 uppercase tracking-[0.3em] mb-3">
              Pricing
            </p>
            <h2 className="text-3xl font-bold text-heading tracking-tight">
              Pay in USDC. Settle on-chain.
            </h2>
            <p className="mt-3 text-ink-300">
              No credit card required — subscriptions renew automatically from
              your agent wallets.
            </p>
          </div>
        </Reveal>
        <div className="grid md:grid-cols-3 gap-4 items-stretch">
          {plans.map((p, i) => (
            <Reveal key={p.name} delay={i * 120} className="h-full">
              <div
                className={`card h-full relative flex flex-col transition-all duration-300 ${
                  p.highlight
                    ? "border-brand-500/60 shadow-[0_0_0_1px_rgba(0,187,127,0.15),0_0_45px_-12px_rgba(0,187,127,0.45)]"
                    : "hover:border-ink-700"
                }`}
              >
                {p.highlight && (
                  <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-brand-500 text-ink-950 text-[10px] font-bold uppercase tracking-widest rounded whitespace-nowrap">
                    Most Popular
                  </span>
                )}
                <p className="text-[11px] text-ink-500 uppercase tracking-widest">
                  {p.name}
                </p>
                <div className="mt-3 flex items-baseline gap-2 flex-wrap">
                  <span className="text-3xl font-bold text-ink-100">
                    {p.price}
                  </span>
                  <span className="text-[11px] text-ink-500">{p.period}</span>
                </div>
                <p className="text-xs text-ink-400 mt-1">{p.tagline}</p>
                <ul className="mt-5 space-y-2.5 flex-1">
                  {p.features.map((feat) => (
                    <li
                      key={feat}
                      className="flex items-start gap-2 text-xs text-ink-300"
                    >
                      <span className="text-brand-400 mt-0.5">›</span>
                      {feat}
                    </li>
                  ))}
                </ul>
                <Link
                  to="/login"
                  className={
                    p.highlight
                      ? "btn-primary w-full mt-6"
                      : "btn-secondary w-full mt-6"
                  }
                >
                  {p.cta}
                </Link>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Devnet CTA */}
      <section id="devnet" className="relative max-w-6xl mx-auto px-6 pt-8 pb-24">
        <Reveal>
          <div className="card !p-0 overflow-hidden relative border-brand-500/25 shadow-[0_0_0_1px_rgba(0,187,127,0.12),0_0_60px_-20px_rgba(0,187,127,0.35)]">
            <div className="absolute inset-0 grid-bg opacity-60 pointer-events-none" />
            {/* centered glow behind the mark */}
            <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[420px] h-[240px] bg-brand-500/15 blur-3xl rounded-full pointer-events-none" />
            <div className="relative p-10 md:p-14 text-center">
              <div className="flex justify-center mb-7">
                <div className="w-16 h-16 rounded-full bg-brand-500/10 border border-brand-500/30 flex items-center justify-center shadow-[0_0_30px_-8px_rgba(0,187,127,0.5)]">
                  <div className="w-9 h-9">
                    <LogoMark />
                  </div>
                </div>
              </div>
              <h2 className="text-3xl font-bold text-heading tracking-tight">
                Deploy your first agent wallet today.
              </h2>
              <p className="mt-4 text-ink-300 max-w-xl mx-auto text-sm leading-relaxed">
                Register free on devnet, fund your wallet from the faucet and
                run escrow + x402 end to end — real Solana transactions, zero
                cost.
              </p>
              <div className="mt-9 flex flex-wrap justify-center gap-4">
                <Link
                  to="/login"
                  className="btn-primary whitespace-nowrap"
                  onClick={() => track("click_register_devnet")}
                >
                  Register on Devnet — Free <ArrowRight className="w-4 h-4" />
                </Link>
                <a
                  href="https://faucet.solana.com"
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary whitespace-nowrap"
                >
                  Get 0.5 Test SOL
                </a>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-ink-800">
        <div className="max-w-6xl mx-auto px-6 py-12 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex flex-col items-center md:items-start gap-4">
            <Brand size="sm" />
            <p className="text-xs text-ink-500">
              © 2026 agentwallet · Built on Solana · Devnet live
            </p>
          </div>
          <div className="flex flex-col items-center md:items-end gap-4">
            <nav className="flex items-center gap-6 text-xs">
              <a
                href="#features"
                className="text-ink-400 hover:text-ink-200 transition-colors"
              >
                Features
              </a>
              <a
                href="#pricing"
                className="text-ink-400 hover:text-ink-200 transition-colors"
              >
                Pricing
              </a>
              <a
                href="#devnet"
                className="text-ink-400 hover:text-ink-200 transition-colors"
              >
                Devnet
              </a>
              <span className="w-px h-4 bg-ink-700" />
              <Link
                to="/login"
                className="text-brand-400 hover:text-brand-300 font-semibold transition-colors"
                onClick={() => track("click_footer_dashboard")}
              >
                Dashboard →
              </Link>
              <span className="w-px h-4 bg-ink-700" />
              <Link
                to="/support"
                className="text-ink-400 hover:text-ink-200 transition-colors"
              >
                Support
              </Link>
              <Link
                to="/terms"
                className="text-ink-400 hover:text-ink-200 transition-colors"
              >
                Terms
              </Link>
              <Link
                to="/privacy"
                className="text-ink-400 hover:text-ink-200 transition-colors"
              >
                Privacy
              </Link>
            </nav>
            <p className="text-[10px] text-ink-600 uppercase tracking-widest">
              Solana devnet · 0.4.x · agent-genesis
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
