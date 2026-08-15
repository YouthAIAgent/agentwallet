import { useEffect, useState } from "react";
import {
  Zap,
  HandCoins,
  ShieldCheck,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Copy,
  CheckCircle2,
  Loader2,
  Undo2,
  Sparkles,
  Wallet as WalletIcon,
  Coins,
} from "lucide-react";
import {
  playground,
  explorerUrl,
  shortSig,
  type PlaygroundStatus,
  type FundResult,
  type EscrowDemoResult,
  type EscrowReleaseResult,
  type EscrowRefundResult,
  type X402DemoResult,
  type TransferDemoResult,
  type UsdcDemoResult,
} from "../api";

function TxLink({ sig, url, label }: { sig: string; url: string; label: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="flex items-center gap-2 mt-3 p-3 bg-ink-950 border border-ink-800 rounded-lg">
      <CheckCircle2 className="w-4 h-4 text-brand-400 flex-shrink-0" />
      <span className="text-sm text-ink-300 font-mono flex-1 min-w-0 truncate">
        {label} · {shortSig(sig)}
      </span>
      <button
        onClick={() => {
          navigator.clipboard.writeText(sig);
          setCopied(true);
          setTimeout(() => setCopied(false), 1200);
        }}
        className="text-ink-400 hover:text-ink-100 transition-colors"
        title="Copy signature"
      >
        {copied ? <CheckCircle2 className="w-4 h-4 text-brand-400" /> : <Copy className="w-4 h-4" />}
      </button>
      <a
        href={url}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1 text-brand-400 hover:text-brand-300 text-sm font-medium"
      >
        Explorer <ExternalLink className="w-3.5 h-3.5" />
      </a>
    </div>
  );
}

export default function Playground() {
  const [status, setStatus] = useState<PlaygroundStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [balance, setBalance] = useState<number | null>(null);

  const [funding, setFunding] = useState(false);
  const [fundRes, setFundRes] = useState<FundResult | null>(null);

  const [escrowBusy, setEscrowBusy] = useState(false);
  const [escrowRes, setEscrowRes] = useState<EscrowDemoResult | null>(null);
  const [releasing, setReleasing] = useState(false);
  const [releaseRes, setReleaseRes] = useState<EscrowReleaseResult | null>(null);
  const [refunding, setRefunding] = useState(false);
  const [refundRes, setRefundRes] = useState<EscrowRefundResult | null>(null);

  const [x402Busy, setX402Busy] = useState(false);
  const [x402Res, setX402Res] = useState<X402DemoResult | null>(null);

  const [transferring, setTransferring] = useState(false);
  const [transferRes, setTransferRes] = useState<TransferDemoResult | null>(null);

  const [usdcBusy, setUsdcBusy] = useState(false);
  const [usdcRes, setUsdcRes] = useState<UsdcDemoResult | null>(null);

  const [error, setError] = useState<string | null>(null);

  const loadStatus = async (silent = false) => {
    if (!silent) setLoadingStatus(true);
    try {
      const s = await playground.status();
      setStatus(s);
      setBalance(s.balance_sol);
      setError(null);
    } catch (e) {
      if (!silent) setError((e as Error).message);
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const refreshBalance = async () => {
    try {
      const s = await playground.status();
      setStatus(s);
      setBalance(s.balance_sol);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const doFund = async () => {
    setFunding(true);
    setError(null);
    setFundRes(null);
    try {
      const r = await playground.fund();
      setFundRes(r);
      setBalance((b) => (b ?? 0) + r.amount_sol);
      await loadStatus(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setFunding(false);
    }
  };

  const doEscrow = async () => {
    setEscrowBusy(true);
    setError(null);
    setEscrowRes(null);
    setReleaseRes(null);
    setRefundRes(null);
    try {
      const r = await playground.escrow();
      setEscrowRes(r);
      await loadStatus(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEscrowBusy(false);
    }
  };

  const doRefund = async () => {
    if (!escrowRes) return;
    setRefunding(true);
    setError(null);
    try {
      const r = await playground.refund(escrowRes.escrow_id);
      setRefundRes(r);
      setEscrowRes((e) => (e ? { ...e, status: r.status } : e));
      await loadStatus(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRefunding(false);
    }
  };

  const doRelease = async () => {
    if (!escrowRes) return;
    setReleasing(true);
    setError(null);
    try {
      const r = await playground.release(escrowRes.escrow_id);
      setReleaseRes(r);
      setEscrowRes((e) => (e ? { ...e, status: r.status } : e));
      await loadStatus(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setReleasing(false);
    }
  };

  const doX402 = async () => {
    setX402Busy(true);
    setError(null);
    setX402Res(null);
    try {
      const r = await playground.x402();
      setX402Res(r);
      setBalance((b) => (b ?? 0) - r.amount_sol);
      await loadStatus(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setX402Busy(false);
    }
  };

  const doTransfer = async () => {
    setTransferring(true);
    setError(null);
    setTransferRes(null);
    try {
      const r = await playground.transfer();
      setTransferRes(r);
      setBalance((b) => (b ?? 0) - r.amount_sol);
      await loadStatus(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setTransferring(false);
    }
  };

  const doUsdc = async () => {
    setUsdcBusy(true);
    setError(null);
    setUsdcRes(null);
    try {
      const r = await playground.usdc();
      setUsdcRes(r);
      await loadStatus(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUsdcBusy(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-ink-100">Devnet Playground</h1>
            <span className="badge badge-green">● LIVE · REAL TX</span>
          </div>
          <p className="text-ink-400 mt-1">
            Every click runs a <span className="text-brand-400">real devnet transaction</span> —
            verify it on Solana Explorer. No fake data.
          </p>
        </div>
        <button
          onClick={() => loadStatus()}
          className="btn-secondary"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loadingStatus ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm font-mono">
          {error}
        </div>
      )}

      {/* wallet status */}
      <div className="card mb-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-brand-500/10 rounded-xl flex items-center justify-center">
              <WalletIcon className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <div className="text-sm text-ink-400">Your devnet wallet</div>
              <div className="text-ink-100 font-mono text-sm mt-0.5 break-all">
                {status?.wallet_address || "loading…"}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-ink-400">Balance</div>
            <div className="text-2xl font-bold text-brand-400">
              {balance === null ? "—" : `${balance.toFixed(4)} SOL`}
            </div>
            {usdcRes && (
              <div className="text-xs text-ink-400 mt-0.5">
                + {usdcRes.amount_usdc.toFixed(0)} USDC (devnet dUSDC)
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 1 — Get SOL */}
        <div className="card flex flex-col">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center">
              <Zap className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <div className="font-semibold text-ink-100">Get 0.01 SOL</div>
              <div className="text-xs text-ink-400 mt-0.5">Free devnet SOL from the platform wallet</div>
            </div>
          </div>
          <p className="text-sm text-ink-400 mb-4 flex-1">
            The public faucet is rate-limited — here the platform sends SOL from its own
            funded wallet. On-chain transfer, visible on the explorer.
          </p>
          <button onClick={doFund} disabled={funding} className="btn-primary w-full">
            {funding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {funding ? "Submitting…" : "Get 0.01 SOL"}
          </button>
          {fundRes && (
            <TxLink
              sig={fundRes.signature}
              url={fundRes.explorer_url}
              label={`${fundRes.amount_sol} SOL → you`}
            />
          )}
        </div>

        {/* 2 — Escrow demo */}
        <div className="card flex flex-col">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <div className="font-semibold text-ink-100">Escrow Demo</div>
              <div className="text-xs text-ink-400 mt-0.5">
                0.0001 SOL · create → fund → release / refund
              </div>
            </div>
          </div>
          <p className="text-sm text-ink-400 mb-4 flex-1">
            Creating an escrow funds it from your wallet instantly (tx 1). Then choose:
            release — pay the vendor, or refund — get your funds back (tx 2).
            All real signatures.
          </p>
          <div className="flex flex-col gap-2">
            <button onClick={doEscrow} disabled={escrowBusy} className="btn-primary w-full">
              {escrowBusy ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <HandCoins className="w-4 h-4" />
              )}
              {escrowBusy ? "Creating escrow…" : escrowRes ? "Create another escrow" : "Create + fund escrow"}
            </button>
            {escrowRes && escrowRes.status === "funded" && !releaseRes && !refundRes && (
              <div className="flex flex-col gap-2">
                <button
                  onClick={doRelease}
                  disabled={releasing || refunding}
                  className="btn-secondary w-full"
                >
                  {releasing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ArrowRight className="w-4 h-4" />
                  )}
                  {releasing ? "Releasing…" : "Release to vendor"}
                </button>
                <button
                  onClick={doRefund}
                  disabled={releasing || refunding}
                  className="btn-secondary w-full"
                >
                  {refunding ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Undo2 className="w-4 h-4" />
                  )}
                  {refunding ? "Refunding…" : "Refund to my wallet"}
                </button>
              </div>
            )}
          </div>
          {escrowRes?.fund_explorer_url && escrowRes.fund_signature && (
            <TxLink
              sig={escrowRes.fund_signature}
              url={escrowRes.fund_explorer_url}
              label={`fund ${escrowRes.amount_sol} SOL · ${escrowRes.status}`}
            />
          )}
          {releaseRes?.release_explorer_url && releaseRes.release_signature && (
            <TxLink
              sig={releaseRes.release_signature}
              url={releaseRes.release_explorer_url}
              label={`release · ${releaseRes.status}`}
            />
          )}
          {refundRes?.refund_explorer_url && refundRes.refund_signature && (
            <TxLink
              sig={refundRes.refund_signature}
              url={refundRes.refund_explorer_url}
              label={`refund · ${refundRes.status} → your wallet`}
            />
          )}
        </div>

        {/* 3 — x402 pay-per-call */}
        <div className="card flex flex-col">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <div className="font-semibold text-ink-100">x402 Pay-per-call AI</div>
              <div className="text-xs text-ink-400 mt-0.5">
                0.0001 SOL · pay → verified → AI response
              </div>
            </div>
          </div>
          <p className="text-sm text-ink-400 mb-4 flex-1">
            One click: payment from your wallet (real tx), on-chain verification, then the
            AI call unlocks. This is the x402 rail — how agents pay at HTTP 402 gates.
          </p>
          <button onClick={doX402} disabled={x402Busy} className="btn-primary w-full">
            {x402Busy ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {x402Busy ? "Paying + calling AI…" : "Pay 0.0001 SOL + call AI"}
          </button>
          {x402Res && (
            <>
              <div className="mt-3 p-3 bg-ink-950 border border-ink-800 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2
                    className={`w-4 h-4 ${x402Res.verified_on_chain ? "text-brand-400" : "text-yellow-400"}`}
                  />
                  <span className="text-xs font-mono text-ink-400">
                    {x402Res.verified_on_chain ? "payment verified on-chain" : "verify pending"} ·{" "}
                    {x402Res.ai_provider} / {x402Res.ai_model}
                    {x402Res.demo && (
                      <span className="ml-2 text-yellow-400">demo AI (no LLM key)</span>
                    )}
                  </span>
                </div>
                <div className="text-sm text-ink-200 font-mono leading-5 max-h-36 overflow-y-auto whitespace-pre-wrap">
                  {x402Res.ai_response}
                </div>
              </div>
              <TxLink
                sig={x402Res.payment_signature}
                url={x402Res.payment_explorer_url}
                label={`paid ${x402Res.amount_sol} SOL → platform`}
              />
            </>
          )}
        </div>

        {/* 4 — Send SOL */}
        <div className="card flex flex-col">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center">
              <ArrowRight className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <div className="font-semibold text-ink-100">Send 0.0001 SOL</div>
              <div className="text-xs text-ink-400 mt-0.5">From your wallet to the platform</div>
            </div>
          </div>
          <p className="text-sm text-ink-400 mb-4 flex-1">
            Simple transfer demo — agent-style payment. Signed with your wallet's encrypted
            key, submitted on devnet, verified on the explorer.
          </p>
          <button onClick={doTransfer} disabled={transferring} className="btn-primary w-full">
            {transferring ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowRight className="w-4 h-4" />
            )}
            {transferring ? "Sending…" : "Send 0.0001 SOL → platform"}
          </button>
          {transferRes && (
            <TxLink
              sig={transferRes.signature}
              url={transferRes.explorer_url}
              label={`${transferRes.amount_sol} SOL sent`}
            />
          )}
        </div>

        {/* 5 — Get USDC (billing demo) */}
        <div className="card flex flex-col">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center">
              <Coins className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <div className="font-semibold text-ink-100">Get 200 USDC</div>
              <div className="text-xs text-ink-400 mt-0.5">Devnet dUSDC for the billing demo</div>
            </div>
          </div>
          <p className="text-sm text-ink-400 mb-4 flex-1">
            Mints 200 devnet USDC straight into your wallet — enough to pay for any tier.
            Now try the Billing page: Subscribe → Renew → Cancel, each payment a real
            on-chain USDC transfer.
          </p>
          <button onClick={doUsdc} disabled={usdcBusy} className="btn-primary w-full">
            {usdcBusy ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Coins className="w-4 h-4" />
            )}
            {usdcBusy ? "Minting…" : "Get 200 USDC"}
          </button>
          {usdcRes && (
            <TxLink
              sig={usdcRes.signature}
              url={usdcRes.explorer_url}
              label={`${usdcRes.amount_usdc.toFixed(0)} USDC minted → you`}
            />
          )}
        </div>
      </div>

      {/* how it works strip */}
      <div className="mt-8 p-5 bg-ink-900 border border-ink-800 rounded-xl">
        <div className="text-sm text-ink-400 font-mono leading-6">
          <span className="text-brand-400">$</span> every demo =
          <span className="text-ink-100"> platform-funded · signed · submitted on Solana devnet</span>
          <br />
          <span className="text-brand-400">$</span> x402 flow =
          <span className="text-ink-100"> pay → proof → verify on-chain → AI call</span>
          <br />
          <span className="text-brand-400">$</span> network =
          <span className="text-ink-100"> {status?.network || "devnet"}</span> · RPC{" "}
          <span className="text-ink-100">api.devnet.solana.com</span>
          <br />
          <span className="text-brand-400">$</span> platform custody =
          <span className="text-ink-100 font-mono">{status?.platform_address ? shortSig(status.platform_address) : "…"}</span>
          <button
            onClick={refreshBalance}
            className="ml-2 text-ink-500 hover:text-ink-200 transition-colors inline-flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> refresh balance
          </button>
        </div>
      </div>
    </div>
  );
}
