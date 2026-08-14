# AgentWallet Devnet Launch — Status & Handoff

Last updated: 2026-08-15

## 🎯 Goal
Fully public devnet launch (webapp ke saath) → users test → feedback → mainnet switch.

## 🌐 Live URLs
| What | URL |
|---|---|
| Dashboard (Vercel) | https://agentwallet-devnet-two.vercel.app |
| API (Railway) | https://api-production-6421a.up.railway.app |
| API docs | https://api-production-6421a.up.railway.app/docs |
| Platform devnet wallet | BTcvExhix1pfVX25imKzkHquGJrncZjijxEJq1RkKK5 |

## ✅ Done (committed + pushed to agent-genesis master)
- **Railway deploy**: Postgres + Redis + API (devnet RPC, platform secrets, encryption/JWT keys, CORS *)
- **Migrations 001→007** chale (incl. USDC billing tables)
- **Login fix**: dashboard `organization_name` → `org_name` (register 422 tha)
- **Dashboard API wiring**: agents/wallets/transactions/pda-wallets/analytics sab real API se (response shape mapping: `{data,total}` → page shapes, lamports→USD, tx_type→type, event_type→action)
- **Dashboard home**: real analytics/agents/wallets/tx composition (mock stats hata diye)
- **Naye API endpoints**: `/billing/tiers`, `/billing/current`, `/audit-log` (root)
- **Billing + Audit Log pages**: ab real data
- **142 pytest pass**, TSC clean, Devnet Lifecycle CI green (smoke+escrow+x402 on devnet)
- Browser bridge E2E verified: register → login → agent create → wallet create → saare 9 pages render

## 📝 Current git state
- master sync, sab pushed
- Uncommitted (old codex-provider task): agent_genesis/ 5 files — alag kaam, abhi chhod diya

## ⏭️ Kal kya karna hai (user ne bola)
- **Frontend design overhaul**: user design skills/tools + example websites dega → dashboard ko waise hi restyle karna hai
- Baaki pending ideas: escrow UI, USDC billing devnet test, audit trail wiring, mainnet runbook

## 🐛 Known gaps
- Audit Log empty (regular actions pe audit events nahi log hote — sirf compliance module)
- Dashboard "Starter" plan API mein nahi (PLANS: free/pro/enterprise)
- Billing upgrade button demo mode (real USDC subscribe flow `/billing/subscribe` pe hai, UI wire nahi)
- Transactions/escrow UI ke liye test SOL — public faucet dry hai, platform wallet pe 2.5 SOL hai
- Dashboard mock fallbacks: Policies/AuditLog/Billing pe abhi bhi mock data fallback hai (endpoints 404 pe)
