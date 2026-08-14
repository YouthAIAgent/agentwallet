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
    <div className="p-4 h-[300px] overflow-hidden">
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
      <section className="relative max-w-6xl mx-auto px-6 pt-16 pb-20 grid lg:grid-cols-2 gap-14 items-center">
        <Reveal>
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 border border-brand-500/30 bg-brand-500/5 rounded text-[11px] text-brand-400 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse" />
              SOLANA DEVNET · LIVE
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-heading tracking-tight leading-[1.1]">
              The payment rail
              <br />
              for the <span className="text-brand-400">agent economy</span>.
            </h1>
            <p className="mt-5 text-ink-300 max-w-lg leading-relaxed">
              Spin up Solana wallets, escrow and pay-per-call billing for your
              agents in minutes. No Stripe, no intermediaries — just on-chain
              money moving automatically when your agents work.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                to="/login"
                className="btn-primary"
                onClick={() => track("click_launch_dashboard")}
              >
                Launch Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href="#devnet"
                className="btn-secondary"
                onClick={() => track("click_try_devnet")}
              >
                Try Devnet — Free
              </a>
            </div>
            <div className="mt-8 flex items-center gap-6 text-[11px] text-ink-500 uppercase tracking-widest">
              <span>● Escrow</span>
              <span>● x402</span>
              <span>● USDC</span>
              <span>● Swarms</span>
            </div>
          </div>
        </Reveal>

        {/* Terminal demo */}
        <Reveal delay={150}>
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
        <div className="grid md:grid-cols-3 gap-4">
          {plans.map((p, i) => (
            <Reveal key={p.name} delay={i * 120}>
              <div
                className={`card h-full relative flex flex-col ${
                  p.highlight
                    ? "border-brand-500/60 shadow-[0_0_40px_-12px] shadow-brand-500/20"
                    : ""
                }`}
              >
                {p.highlight && (
                  <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-brand-500 text-ink-950 text-[10px] font-bold uppercase tracking-widest rounded">
                    Most Popular
                  </span>
                )}
                <p className="text-[11px] text-ink-500 uppercase tracking-widest">
                  {p.name}
                </p>
                <div className="mt-3 flex items-baseline gap-2">
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
      <section id="devnet" className="relative max-w-6xl mx-auto px-6 py-20">
        <Reveal>
          <div className="card !p-0 overflow-hidden relative">
            <div className="absolute inset-0 grid-bg opacity-60 pointer-events-none" />
            <div className="relative p-8 md:p-12 text-center">
              <div className="flex justify-center mb-6">
                <div className="w-12 h-12">
                  <LogoMark />
                </div>
              </div>
              <h2 className="text-3xl font-bold text-heading tracking-tight">
                Deploy your first agent wallet today.
              </h2>
              <p className="mt-3 text-ink-300 max-w-xl mx-auto text-sm leading-relaxed">
                Register free on devnet, fund your wallet from the faucet and
                run escrow + x402 end to end — real Solana transactions, zero
                cost.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-4">
                <Link
                  to="/login"
                  className="btn-primary"
                  onClick={() => track("click_register_devnet")}
                >
                  Register on Devnet — Free
                </Link>
                <a
                  href="https://faucet.solana.com"
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary"
                >
                  Get 0.5 Test SOL
                </a>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-ink-800 mt-10">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7">
              <LogoMark />
            </div>
            <p className="text-xs text-ink-500">
              © 2026 agentwallet · Built on Solana · Devnet live
            </p>
          </div>
          <div className="flex items-center gap-6 text-xs text-ink-400">
            <a href="#features" className="hover:text-ink-200 transition-colors">
              Features
            </a>
            <a href="#pricing" className="hover:text-ink-200 transition-colors">
              Pricing
            </a>
            <Link to="/login" className="hover:text-brand-400 transition-colors">
              Dashboard
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
