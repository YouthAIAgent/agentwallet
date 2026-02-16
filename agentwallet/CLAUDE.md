# AgentWallet Protocol - Project Memory

## Project Overview
AI agent wallet infrastructure SaaS on Solana. Wallet-as-a-service for autonomous AI agents with spending limits, escrow, analytics, compliance, ACP (Agent Commerce Protocol), and swarm coordination.

## Live Deployment
- **Railway API**: https://api.agentwallet.fun (CNAME → Railway)
- **Website**: https://agentwallet.fun (Vercel)
- **Railway Project ID**: 1e142b95-97f5-49b4-aa54-38c76b369742
- **Railway Service**: trustworthy-celebration
- **Railway Account**: YouthAIAgent (web3youth@gmail.com)
- **GitHub**: https://github.com/YouthAIAgent/agentwallet
- **Health**: `GET /health` returns `{"status":"ok","version":"0.4.0"}`
- **Swagger Docs**: `GET /docs` (disabled in production)

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
