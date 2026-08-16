# AgentWallet — Platform Guide (A to Z)

> Simple language version — English script, Hindi explanation.
> Technical readers: full details in `README.md`, `CLAUDE.md`, and `docs/LAUNCH_CHECKLIST.md`.

**Live now:** https://agentwallet.fun · **Devnet playground** — register free, fund from
the faucet, run real Solana transactions (escrow + x402 + USDC) in minutes.

---

## 🔍 Pehle samjho — problem kya hai

AI agents (jaise Claude, GPT agents) kaam karte hain — API call karte hain, tasks
complete karte hain. **Par unke paas paisa nahi hai.** Bank account nahi khol sakte,
Stripe nahi use kar sakte (wo humans ke liye bana hai). To agent ko kaam karne ke liye
paisa dena hai to **kisi human ko har baar manually pay karna padta hai** — yeh slow
aur impossible hai jab hazaaron agents ek saath kaam karein.

**AgentWallet iska solution hai** — agents ko unka apna crypto wallet deta hai Solana
pe, taaki wo **khud paisa le-sake, de-sake, aur kaam ke liye pay kar-sake** — bina
kisi middleman ke.

---

## 🤖 AI Agents ko kya faida

1. **Apna wallet** — har agent ka apna Solana wallet, keys + balance, sab API se
2. **Escrow (bharosa)** — agent aur service ke beech paisa lock hota hai; kaam poora
   hua to release, nahi hua to refund — koi dhoka nahi
3. **Pay-per-call (x402)** — agent har AI call ke liye chhota paisa pay karta hai,
   jaise metered taxi. Micro-payments automatic
4. **USDC billing** — agent apna subscription khud pay/renew/cancel kar sakta hai —
   crypto se, card nahi
5. **Swarms + ACP** — ek wallet, kayi agents — poora agent team ek saath transact kar
   sakta hai

**Seedha fayda:** Agent **autonomous** ban jaata hai — bina human ke paisa move kar
sakta hai, kaam karke paisa kama sakta hai. Yehi "agent economy" hai.

---

## 👤 Humans (developers/users) ko kya faida

1. **Minutes mein setup** — wallet banao, escrow lock karo, AI call pay karo — sab
   60 second mein, no card, no KYC, no bank
2. **Zero middleman fees** — Stripe jaisa koi 2.9% + $0.30 nahi. Sirf Solana ka chhota
   transaction fee (fraction of a cent)
3. **Full control + transparency** — har transaction explorer pe verify kar sakte ho —
   koi hidden charges nahi
4. **Agent se paisa kamana** — agar agent aapka business kaam karta hai (content,
   support, trading), to wo khud aapko revenue de sakta hai
5. **Devnet pe free test** — bina paise lagaye pura platform try karo, real
   transactions ke saath

---

## 📦 Platform details — A to Z

| Letter | Detail |
|---|---|
| **A — API** | FastAPI backend, sab kuch REST se — wallets, escrow, x402, USDC, agents |
| **B — Billing** | USDC subscriptions (Free / Pro $49 / Enterprise $299) |
| **C — CLI** | `agx` — terminal se sab kuch: agents, wallets, genesis org deploy |
| **D — Dashboard** | React SPA — live stats, real activity feed, online visitors, playground |
| **E — Escrow** | Create → fund → release → refund, dispute-ready, real on-chain |
| **F — Faucet** | Devnet pe free SOL + USDC funding — playground test ke liye |
| **G — Genesis** | Agent Genesis tool — AI se poora org design + deploy, VPS sandboxes pe |
| **H — Hosting** | API on Railway, dashboard on Vercel, agents on VPS (OpenSandbox) |
| **I — Infra** | Redis caching, rate limiting per-IP, Docker compose local dev |
| **J — JSON-RPC** | MCP server — Claude/agents ko platform se jodta hai |
| **K — Keys** | Platform wallet, per-agent keypairs, encrypted storage |
| **L — Landing** | agentwallet.fun — brand, live stats badge, activity feed, GA/Plausible |
| **M — Mascot** | SOL/USDC glowing coin character — videos + branding |
| **N — Network** | Solana devnet abhi, mainnet = sirf config change |
| **O — OG/Open source** | GitHub pe poora code — ChiranjibAI/agent-genesis |
| **P — Playground** | Users real devnet tx chalate hain — escrow, x402, USDC, SOL transfer |
| **Q — Quality** | 159+ API tests, CI/CD — GitHub Actions pe full lifecycle tests |
| **R — Rate limits** | Per-IP buckets, abuse protection |
| **S — SDK** | `aw-protocol-sdk` (PyPI 0.4.7) + TS SDK — 5 line mein wallet |
| **T — Transactions** | Har demo REAL devnet tx — explorer link ke saath |
| **U — USDC** | Devnet mint + "Get USDC" button — subscribe/renew/cancel e2e |
| **V — Video** | 2-min launch video + 15s/30s shorts, voiceover, captions, music |
| **W — Wallets** | Custodial agent wallets, multi-wallet, balance tracking |
| **X — x402** | Pay-per-call protocol — agent pay karta hai, AI response milta hai |
| **Y — You (users)** | Har visitor ko anonymous online count + country flag dikhta hai |
| **Z — Zero-cost test** | Devnet pe pura platform free — koi card, koi deposit nahi |

---

## 🎯 Ek line mein

**AgentWallet = agents ka Stripe + bank account, Solana pe.** Agents ko de deta hai
paisa khud manage karne ki power; humans ko de deta hai un agents se kaam karwane ka
transparent, sasta, automatic system.

**Abhi:** devnet pe free test karo (agentwallet.fun) → feedback do → mainnet switch.
