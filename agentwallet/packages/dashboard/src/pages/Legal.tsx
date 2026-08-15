import { Link } from "react-router-dom";

const shell = "border border-ink-800 bg-ink-900/60 rounded-lg p-6";
const h2 = "text-lg font-semibold text-ink-100 mt-6 mb-2";
const p = "text-sm text-ink-400 leading-relaxed mb-3";
const li = "text-sm text-ink-400 leading-relaxed mb-1.5 list-disc ml-5";

function PageShell({
  title,
  updated,
  children,
}: {
  title: string;
  updated: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-ink-950 text-ink-200 relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(0,255,65,0.06),transparent_60%)]" />
      <div className="relative max-w-3xl mx-auto px-6 py-16">
        <div className="mb-10 flex items-center justify-between">
          <Link
            to="/"
            className="text-brand-400 hover:text-brand-300 text-sm font-semibold transition-colors"
          >
            ← Back to agentwallet
          </Link>
          <span className="text-[10px] text-ink-600 uppercase tracking-widest">
            Updated {updated}
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-ink-50 mb-2">
          {title}
        </h1>
        <p className="text-sm text-ink-500 mb-10">
          agentwallet · Solana devnet playground
        </p>
        <div className={shell}>{children}</div>
        <div className="mt-10 flex items-center gap-6 text-xs text-ink-600">
          <Link to="/terms" className="hover:text-ink-300 transition-colors">
            Terms
          </Link>
          <Link to="/privacy" className="hover:text-ink-300 transition-colors">
            Privacy
          </Link>
          <Link to="/support" className="hover:text-ink-300 transition-colors">
            Support
          </Link>
        </div>
      </div>
    </div>
  );
}

export function Terms() {
  return (
    <PageShell title="Terms of Service" updated="August 15, 2026">
      <p className={p}>
        agentwallet is a developer playground running on the{" "}
        <span className="text-ink-200 font-medium">Solana devnet</span>. All
        assets you receive here are testnet tokens with no monetary value.
      </p>
      <h2 className={h2}>1. Devnet only</h2>
      <p className={p}>
        Every transaction you run in the playground uses devnet — a public test
        network. SOL and dUSDC granted here are fake, free, and reset. Nothing
        on this site involves real money or real assets.
      </p>
      <h2 className={h2}>2. Acceptable use</h2>
      <ul className={li}>
        <li>
          You may use the playground to learn, demo, and build against the
          AgentWallet protocol.
        </li>
        <li>
          Do not attempt to drain, spam, or abuse the funded platform wallet.
          Daily faucet limits apply per account.
        </li>
        <li>
          Do not use the service for any illegal activity or to send
          unsolicited transactions.
        </li>
      </ul>
      <h2 className={h2}>3. No warranties</h2>
      <p className={p}>
        The service is provided “as is” without warranty of any kind. We do not
        guarantee availability, and devnet transactions can fail or be reverted
        at any time. Use it for testing, not for anything you depend on.
      </p>
      <h2 className={h2}>4. Limitation of liability</h2>
      <p className={p}>
        To the maximum extent permitted by law, agentwallet and its operators
        are not liable for any loss arising from your use of this testnet
        playground. There are no real funds involved — there is nothing to
        lose.
      </p>
      <h2 className={h2}>5. Changes</h2>
      <p className={p}>
        We may update these terms as the playground evolves. Continued use after
        changes means you accept the updated terms.
      </p>
    </PageShell>
  );
}

export function Privacy() {
  return (
    <PageShell title="Privacy Policy" updated="August 15, 2026">
      <p className={p}>
        We collect the minimum needed to run the devnet playground and keep it
        safe. There is no real money, but your data still matters.
      </p>
      <h2 className={h2}>What we collect</h2>
      <ul className={li}>
        <li>
          <span className="text-ink-200 font-medium">Account info</span> — email
          and a password hash (we never store plaintext passwords) so you can
          sign in.
        </li>
        <li>
          <span className="text-ink-200 font-medium">Wallet addresses</span> —
          the devnet public keys used for your playground demos.
        </li>
        <li>
          <span className="text-ink-200 font-medium">Usage analytics</span> —
          anonymized page views via Google Analytics to understand what people
          use.
        </li>
      </ul>
      <h2 className={h2}>What we do NOT collect</h2>
      <ul className={li}>
        <li>No private keys — wallets are generated server-side and never leave the platform.</li>
        <li>No payment information — there is no billing on devnet.</li>
      </ul>
      <h2 className={h2}>How we use it</h2>
      <p className={p}>
        To authenticate you, to run your playground transactions, to enforce
        rate limits and prevent abuse, and to improve the product.
      </p>
      <h2 className={h2}>Your rights</h2>
      <p className={p}>
        You can delete your account and its data at any time by contacting{" "}
        <a
          href="mailto:support@agentwallet.fun"
          className="text-brand-400 hover:text-brand-300"
        >
          support@agentwallet.fun
        </a>
        . We’ll remove your data within 30 days.
      </p>
      <h2 className={h2}>Contact</h2>
      <p className={p}>
        Questions about privacy? Email{" "}
        <a
          href="mailto:support@agentwallet.fun"
          className="text-brand-400 hover:text-brand-300"
        >
          support@agentwallet.fun
        </a>
        .
      </p>
    </PageShell>
  );
}

export function Support() {
  return (
    <PageShell title="Support" updated="August 15, 2026">
      <p className={p}>
        Stuck on the playground? Here’s how to get help fast.
      </p>
      <h2 className={h2}>Common fixes</h2>
      <ul className={li}>
        <li>
          <span className="text-ink-200 font-medium">Funds not arriving</span> —
          devnet confirmations can take a few seconds. Refresh the playground
          status and check the explorer link on your last transaction.
        </li>
        <li>
          <span className="text-ink-200 font-medium">Rate limited</span> —
          faucet grants are capped (0.01 SOL every 60s, 20/day). Wait for the
          window or use your existing balance for the other demos.
        </li>
        <li>
          <span className="text-ink-200 font-medium">Platform out of funds</span>{" "}
          — if the custody wallet runs dry we refill it, but it may take a few
          hours. Check back later.
        </li>
      </ul>
      <h2 className={h2}>Contact channels</h2>
      <ul className={li}>
        <li>
          Email:{" "}
          <a
            href="mailto:support@agentwallet.fun"
            className="text-brand-400 hover:text-brand-300"
          >
            support@agentwallet.fun
          </a>
        </li>
        <li>
          GitHub issues:{" "}
          <a
            href="https://github.com/ChiranjibAI/agent-genesis/issues"
            target="_blank"
            rel="noreferrer"
            className="text-brand-400 hover:text-brand-300"
          >
            ChiranjibAI/agent-genesis
          </a>
        </li>
        <li>
          Discord: join the Agent Wallet community server (link published on
          the landing page).
        </li>
      </ul>
      <h2 className={h2}>What we can’t help with</h2>
      <p className={p}>
        Recovering real funds, mainnet support, or anything involving real
        money — this playground is devnet-only by design.
      </p>
    </PageShell>
  );
}
