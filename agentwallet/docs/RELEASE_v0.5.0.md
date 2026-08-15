# AgentWallet v0.5.0 — Public Devnet Launch 🚀

**Live now:** [agentwallet.fun](https://agentwallet.fun) · API: `api-production-6421a.up.railway.app` · SDK: `aw-protocol-sdk 0.4.7` on PyPI

60 commits since v0.4.5. The wallet layer for AI agents on Solana is now a public devnet product — any user can register and run real on-chain demos in minutes.

## 🚀 Devnet Playground — one-click real on-chain demos
- **`/playground`** — fund SOL, escrow create/fund/release/refund, x402 pay-per-call, USDC grant, and real SOL transfer — every action is a real devnet transaction with Explorer links
- **x402 pay-per-call demo** returns a **real AI response** (OpenAI-compatible model) after an on-chain verified micropayment
- **Escrow refund demo** — full create → fund → refund lifecycle on-chain
- Microscopic demo amounts (0.0001 SOL) so the platform fund never runs out
- Playground USDC: 200 dUSDC minted straight to the user wallet (custom mint, no faucet)

## 💳 USDC Billing (production verified)
- Subscribe → renew → cancel settles in **real on-chain USDC transfers** (dUSDC on devnet)
- Stale-balance retry + RPC hardening: all 17 RPC call sites route through `_rpc_post` with 429/5xx exponential backoff

## 🎨 Dashboard & Landing
- **Public landing page** — brand hero, features, pricing, devnet CTA (agentwallet.fun)
- Animated hero — typing terminal with spinner/outcomes/exit codes, gradient glow, scroll reveal
- Shimmer motion-graphics treatment: animated emerald gradient, glow + underline sweep on the headline; small-caps key terms; title-case continuous heading with tight tracking
- Pricing: equal-height cards with consistent glow/hover; devnet CTA + footer polished
- local.ai-inspired visual system — warm ink theme, Geist Mono, emerald accent
- Light theme toggle (white paper, red headings, blue accents), first-class logo + branding
- Login/Register page redesign, terminal-style stat cards with delta indicators
- Home dashboard composed from **live** analytics/agents/wallets/txs (no mocks)
- OG social preview image (1200×630) + env-driven analytics (GA4 or Plausible)

## 🔐 API, SDK & CLI
- Action-oriented next-step hints on every API error (rate limit → "wait 60s", insufficient SOL → "run playground fund first")
- SDK/CLI: same hints on every exception — `aw-protocol-sdk` **0.4.7 on PyPI**
- New endpoints: `/billing/tiers`, `/billing/current`, root `/audit-log`
- Escrow double-pay fix, x402 replay protection + auth hardening

## 🎬 Launch Video
- 2-min product launch video (Remotion, motion graphics, scene-synced captions, edge-tts voiceover, music bed with ducking)
- 15s/30s vertical (9:16) shorts with TikTok-style captions
- Glowing SOL/USDC coin mascot across all scenes

## 🤖 Agent Genesis
- MVP runnable — `genesis` + `genesis-bot` commands, tests, CI
- AGX CLI genesis tools (design, deploy, list orgs)
- `genesis_deploy` actually deploys — Windows spawn fix + Ollama runtime + codex custom provider (`GENESIS_CODEX_PROVIDER`)

## 🧪 CI & Testing
- GitHub Actions runs smoke + escrow + x402 lifecycles against **Solana devnet on every push**
- Smoke test extended: wallet/escrow/transactions checks, devnet funding, validator mode for deterministic on-chain runs
- `prod_journey_test.sh` — one-command full journey against production (register → fund → USDC → escrow → x402 → transfer)

## 🔧 Fixes
- Postgres URL → asyncpg driver for hosted deploys
- Dashboard dev proxy rewrite + real API shapes wiring
- MCP handshake retry (spawn race), API key write permissions for smoke checks
- Hinglish UI copy → English
