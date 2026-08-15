# AgentWallet Protocol - Project Memory

## Project Overview
AI agent wallet infrastructure SaaS on Solana. Wallet-as-a-service for autonomous AI agents with spending limits, escrow, analytics, compliance, ACP (Agent Commerce Protocol), and swarm coordination.

## Live Deployment
- **Railway API**: https://api-production-6421a.up.railway.app (devnet)
- **Website**: https://agentwallet.fun (Vercel)
- **Railway Project**: `agentwallet-devnet` (workspace: Earning Girl's Projects) → service `api`
- **Railway Account**: Earning Girl (earninggirl6@gmail.com)
- **GitHub**: https://github.com/ChiranjibAI/agent-genesis
- **Health**: `GET /health` returns `{"status":"ok","version":"0.4.0"}`
- **Swagger Docs**: `GET /docs` (disabled in production)

### Deploy
- **Normal path (preferred)**: push to master → GitHub Actions CI deploys Railway + Vercel automatically.
- **CI fallback** (Actions disabled / flagged account): run `./deploy_prod.sh` from `agentwallet/agentwallet`
  (deploys API → Railway and dashboard → Vercel + health checks, or `./deploy_prod.sh api` / `dashboard` for one).
  Requires `railway login` (project linked) + `npx vercel login` on this machine.

### API routing & geo headers (current)
- **Dashboard API calls are same-origin**: `VITE_API_URL=/api/v1` (in `packages/dashboard/.env.production`),
  so browsers hit `https://agentwallet.fun/api/v1/...`.
- **Vercel Routing Middleware** (`packages/dashboard/proxy.ts`, wired via `vercel.json` → `proxy.entrypoint`,
  matcher `/api/*`) forwards those calls to `https://api-production-6421a.up.railway.app` and passes
  Vercel's `x-vercel-ip-country` through as `cf-ipcountry` — the presence tracker
  (`services/presence.py`, `country_from_request`) then records real country codes.
- DNS: `agentwallet.fun` nameservers are Vercel's (`ns1.vercel-dns.com`, `ns2.vercel-dns.com`).
  Note: `api.agentwallet.fun` currently CNAMEs to `a70gs6rx.up.railway.app` which is DEAD
  ("Application not found") — repoint or delete it during migration.

### Cloudflare full-proxy migration (optional, when ready)
Why: Cloudflare's free plan only supports full-zone (no CNAME/partial setup), so moving to Cloudflare
means moving the whole `agentwallet.fun` zone. Do this only when you want CF's edge (WAF, caching,
bot fight, `CF-IPCountry` for every request). Our backend already prefers `CF-IPCountry` first
(`_GEO_HEADERS` in `services/presence.py`), so no code change is needed after migration.

Steps (requires Cloudflare account + registrar access):
1. **Snapshot current DNS** — export the Vercel DNS records for `agentwallet.fun` (dashboard →
   Settings → Domains → DNS records). Minimum set: apex `A` → Vercel (the two IPs above), any
   `CNAME`s (e.g. `www`, `api`), and the `_vercel` TXT/verification records if present.
2. **Create the zone on Cloudflare** — dashboard → Add site → `agentwallet.fun` (Free plan).
3. **Recreate records in Cloudflare** with proxy ON (orange cloud):
   - `A  @  216.198.79.65` (or the current Vercel apex IPs) — proxy ON.
   - `CNAME  www  cname.vercel-dns.com` — proxy ON (or delete if www unused).
   - `CNAME  api  api-production-6421a.up.railway.app` — proxy ON; this fixes the dead
     `api.agentwallet.fun` record and gives every direct API call a real `CF-IPCountry`.
   - Keep any `_vercel` verification records (proxy OFF / grey cloud) until Vercel re-verifies.
4. **Change nameservers at the registrar** to the two Cloudflare-assigned NS (shown in CF dashboard).
   Propagation: minutes to ~24h. Keep the old Vercel NS values handy for rollback.
5. **Verify after propagation** (`dig +short agentwallet.fun NS` shows Cloudflare):
   - `https://agentwallet.fun` still serves the dashboard (HTTP 200).
   - `curl -s https://agentwallet.fun/api/v1/public/presence -X POST -H 'Content-Type: application/json'
     -d '{"visitor_id":"cf-check-0001"}'` → `countries` should contain a real code (your own
     country, e.g. `IN`), not `xx`.
   - Presence badge on the landing page shows flag emojis + counts.
6. **Optional cleanup**: with Cloudflare in front, the Vercel middleware (`proxy.ts`) is redundant
   for geo (CF adds `CF-IPCountry` directly) but harmless — keep it as a fallback or remove it later.

Rollback (if anything breaks): at the registrar, restore the old nameservers (`ns1.vercel-dns.com`,
`ns2.vercel-dns.com`). Cloudflare keeps the zone config, so re-activating later is one NS change.

Security note: with CF proxying the API, Cloudflare sees unauthenticated traffic in cleartext at the
edge — TLS termination is on Cloudflare's side (free SSL cert auto-issued). Railway keeps its own TLS
for the origin. Rate limiting stays per-IP on our side (`check_rate_limit` uses `X-Forwarded-For`).

## Tech Stack
| Layer | Technology |
|-------|-----------|
| API | FastAPI + Python 3.11 (Docker) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| DB | PostgreSQL 16 (Railway) |
| Cache | Redis 7 (needs adding on Railway) |
| Blockchain | Solana (solders Python SDK) |
| On-chain | Anchor/Rust programs |
| Dashboard | React 18 + TypeScript 5.6 + Vite 6 + Tailwind |
| SDK | Python "aw-protocol-sdk" v0.3.0 |
| Auth | JWT + bcrypt (direct, NOT passlib) |
| Landing | Hacker terminal static site (landing-page/) on Vercel |
| Deploy | Docker + Railway |

## Project Structure
```
agentwallet/
├── docker-compose.yml, Dockerfile, Dockerfile.worker
├── alembic.ini, pyproject.toml, railway.json
├── packages/
│   ├── api/          # FastAPI backend (88+ endpoints under /v1)
│   │   └── agentwallet/ (main, api/routers, core, models, services, workers, migrations)
│   ├── sdk-python/   # pip install aw-protocol-sdk
│   ├── dashboard/    # React + Vite
│   ├── programs/     # Anchor/Rust Solana program
│   ├── cli/          # Rich operator dashboard
│   └── landing/      # Old landing page (superseded by landing-page/)
├── landing-page/     # Hacker terminal website (deployed to Vercel)
```

## API Routes (all under /v1, 16 router groups)
auth, wallets, agents, transactions, escrow, analytics, compliance, policies, webhooks, tokens, erc8004, x402, marketplace, pda-wallets, acp, swarms

## ACP (Agent Commerce Protocol) — Virtual Protocol inspired
- 4-phase job lifecycle: request → negotiation → transaction → evaluation
- Signed memos for cryptographic audit trail
- Evaluator agents for independent deliverable verification
- Resource offerings for lightweight agent-to-agent data queries
- Endpoints: `/v1/acp/jobs`, `/v1/acp/jobs/{id}/negotiate`, `/v1/acp/jobs/{id}/fund`, `/v1/acp/jobs/{id}/deliver`, `/v1/acp/jobs/{id}/evaluate`, `/v1/acp/jobs/{id}/memos`, `/v1/acp/offerings`

## Agent Swarms
- Orchestrator/worker cluster coordination for multi-agent tasks
- Task decomposition into subtasks, auto-assignment, auto-aggregation
- Swarm types: general, trading, research, content, security, data, custom
- Contestable worker roles
- Endpoints: `/v1/swarms`, `/v1/swarms/{id}/members`, `/v1/swarms/{id}/tasks`, `/v1/swarms/{id}/tasks/{id}/assign`, `/v1/swarms/{id}/tasks/{id}/complete`

## Critical Architecture Decisions (DO NOT REVERT)
1. **JSONB -> JSON**: All ORM model files use `JSON` not `JSONB` (SQLite test compat)
2. **bcrypt direct**: `import bcrypt` not `passlib` (passlib crashes on Python 3.14)
3. **lazy="noload"**: ALL relationships — Organization, Agent, Webhook, Marketplace models (selectin causes MissingGreenlet)
4. **StaticPool**: SQLite test engine uses `StaticPool` + `check_same_thread=False`
5. **Redis fail-open**: Rate limiter caches Redis availability, skips if unavailable
6. **db.refresh()**: `await db.refresh(obj)` after flush in agents/policies routers and agent_registry service
7. **Railway sh -c**: startCommand wraps in `sh -c '...'` for env var expansion
8. **SDK name**: Package is `aw-protocol-sdk` on PyPI (plain `agentwallet` and `agentwallet-sdk` were taken)
9. **Services use flush() not commit()**: get_db() auto-commits on success

## Environment Variables (Railway Production)
All secrets are managed via Railway dashboard — never commit secrets to the repo.
Required env vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `ENCRYPTION_KEY`, `SOLANA_RPC_URL`, `PLATFORM_WALLET_ADDRESS`, `ENVIRONMENT`
See `.env.example` for the full list.

## Tests
- **110/110 passing** with `pytest` (SQLite + aiosqlite backend)
- 9 test files: test_agents, test_auth, test_escrow, test_marketplace, test_pda_wallets, test_policies, test_transactions, test_wallets + conftest
- Config: `asyncio_mode = "auto"`, testpaths = `packages/api/tests`
- conftest.py creates/drops tables per session, mocks Redis + Solana RPC

## Website (landing-page/)
- Hacker terminal AI agent theme, 20 sections, 10 interactive features
- Features: AI chat widget, API playground, one-click deploy, agent leaderboard, Bloomberg terminal, network visualization, visual builder, transaction heatmap, voice mode, escrow theater
- Sections: Endorsed, Tweets, Features, Playground, Live Proof, Join Protocol, Solana Data, Escrow Theater, Marketplace, Leaderboard, Bloomberg, Network, Builder, Heatmap, ACP, Swarm, About, Free Open Source, Roadmap, Rewards

## Remaining Manual Steps
1. **PyPI publish**: `python -m twine upload packages/sdk-python/dist/* --username __token__ --password pypi-TOKEN`
2. **Add Redis on Railway**: Go to Railway dashboard, add Redis database, update REDIS_URL
3. **Solana program**: Install Rust + Solana CLI + Anchor, then build and deploy to devnet
4. **Platform wallet**: Set real PLATFORM_WALLET_ADDRESS (Solana pubkey for fee collection)
5. **Stripe**: Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET for billing

## Revenue Model
| Tier | Price | Agents | TX/mo | Fee |
|------|-------|--------|-------|-----|
| Free | $0/mo | 3 | 1,000 | 0.5% |
| Pro | $49/mo | 25 | 50,000 | 0.25% |
| Enterprise | $299+/mo | Unlimited | Unlimited | 0.1% |

## Related Project
- moltfarm: Solana utilities reused in this project (transfer_sol, confirm_transaction, retry decorator)

## Installed Agent & Sandbox Tooling
- **Agency Agents** (msitarzewski/agency-agents): 270 specialist agents installed into
  `~/.claude/agents/`, `~/.codex/agents/`, `~/.gemini/agents/`, and `.opencode/` (project,
  gitignored). Activate by name, e.g. "activate Frontend Developer mode", "use the
  security-architect agent", "reality-checker" for critique.
- **OpenSandbox** (opensandbox-group/OpenSandbox): sandbox runtime for agent code execution.
  - CLI: `osb` (`pip install opensandbox-cli`) · server: `opensandbox-server --config ~/.sandbox.toml`
  - **Production host = VPS** `srv1425290` (187.77.185.34, root, Ubuntu 24.04, 4 vCPU/16GB):
    - SSH: `ssh -i ~/.ssh/codex_hostinger_ed25519 root@187.77.185.34`
    - Server: systemd service `opensandbox`, venv at `/opt/osb/bin`, config `/root/.sandbox.toml`
    - Binds `0.0.0.0:8080` with API key auth (key in `~/.opensandbox/config.toml` local CLI config)
    - Local CLI points at `187.77.185.34:8080` — remote sandboxes run on the VPS, not locally
    - **Server-side hard caps** (every sandbox, no flags needed): memory=1Gi, cpu=0.7,
      max 24h timeout. Patched `container_ops.py:_resolve_resource_limits` (site-packages,
      backup `.bak`) — SDK default 2Gi/1.0 is overridden; smaller explicit requests are kept.
      Caps configurable via `OPENSANDBOX_DEFAULT_MEMORY` / `OPENSANDBOX_DEFAULT_CPU` in
      `/etc/systemd/system/opensandbox.service`. Capacity (verified by stress test):
      12–16 concurrent agents comfortable, 20 light burst, memory ceiling ~14GB aggregate.
  - Flow: `osb sandbox create --image python:3.12 -o json` → `osb command run <id> -o raw -- <cmd>`
  - Config: `~/.opensandbox/config.toml` (CLI) + `~/.sandbox.toml` (server, docker example)
  - Windows note: set `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` before `osb` (charmap emoji bug)
  - Local fallback: for local testing run server on 127.0.0.1:8080 with Docker Desktop running
