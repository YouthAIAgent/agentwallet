# AgentWallet Protocol - Project Memory

## Project Overview
AI agent wallet infrastructure SaaS on Solana. Wallet-as-a-service for autonomous AI agents with spending limits, escrow, analytics, and compliance.

## Live Deployment
- **Railway API**: https://api.agentwallet.fun (Railway: trustworthy-celebration-production-6a3e.up.railway.app)
- **Railway Project ID**: 1e142b95-97f5-49b4-aa54-38c76b369742
- **Railway Service**: trustworthy-celebration
- **Railway Account**: YouthAIAgent (web3youth@gmail.com)
- **GitHub**: https://github.com/YouthAIAgent/agentwallet
- **Health**: `GET /health` returns `{"status":"ok","version":"0.3.0"}`
- **Swagger Docs**: `GET /docs`

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
| SDK | Python "agentwallet-sdk" v0.1.0 |
| Auth | JWT + bcrypt (direct, NOT passlib) |
| Landing | Static HTML/CSS/JS (packages/landing/) |
| Deploy | Docker + Railway |

## Project Structure
```
agentwallet/
├── docker-compose.yml, Dockerfile, Dockerfile.worker
├── alembic.ini, pyproject.toml, railway.json
├── packages/
│   ├── api/          # FastAPI backend (60 endpoints under /v1)
│   │   └── agentwallet/ (main, api/routers, core, models, services, workers, migrations)
│   ├── sdk-python/   # pip install agentwallet-sdk
│   ├── dashboard/    # React + Vite
│   ├── programs/     # Anchor/Rust Solana program
│   ├── cli/          # Rich operator dashboard
│   └── landing/      # Static landing page
```

## API Routes (all under /v1, 14 router groups)
auth, wallets, agents, transactions, escrow, analytics, compliance, policies, webhooks, tokens, erc8004, x402, marketplace, pda-wallets

## Critical Architecture Decisions (DO NOT REVERT)
1. **JSONB -> JSON**: All 9 ORM model files use `JSON` not `JSONB` (SQLite test compat)
2. **bcrypt direct**: `import bcrypt` not `passlib` (passlib crashes on Python 3.14)
3. **lazy="noload"**: ALL relationships — Organization, Agent, Webhook, Marketplace models (selectin causes MissingGreenlet)
4. **StaticPool**: SQLite test engine uses `StaticPool` + `check_same_thread=False`
5. **Redis fail-open**: Rate limiter caches Redis availability, skips if unavailable
6. **db.refresh()**: `await db.refresh(obj)` after flush in agents/policies routers and agent_registry service
7. **Railway sh -c**: startCommand wraps in `sh -c '...'` for env var expansion
8. **SDK name**: Package is `agentwallet-sdk` on PyPI (plain `agentwallet` was taken)

## Environment Variables (Railway Production)
All secrets are managed via Railway dashboard — never commit secrets to the repo.
Required env vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `ENCRYPTION_KEY`, `SOLANA_RPC_URL`, `PLATFORM_WALLET_ADDRESS`, `ENVIRONMENT`
See `.env.example` for the full list.

## Tests
- **84/84 passing** with `pytest` (SQLite + aiosqlite backend)
- 9 test files: test_agents, test_auth, test_escrow, test_marketplace, test_pda_wallets, test_policies, test_transactions, test_wallets + conftest
- Config: `asyncio_mode = "auto"`, testpaths = `packages/api/tests`
- conftest.py creates/drops tables per session, mocks Redis + Solana RPC

## Remaining Manual Steps
1. **PyPI publish**: `python -m twine upload packages/sdk-python/dist/* --username __token__ --password pypi-TOKEN`
2. **Add Redis on Railway**: Go to Railway dashboard, add Redis database, update REDIS_URL
3. **Host landing page**: Deploy `packages/landing/` to Vercel/Netlify/GitHub Pages
4. **Solana program**: Install Rust + Solana CLI + Anchor, then build and deploy to devnet
5. **Platform wallet**: Set real PLATFORM_WALLET_ADDRESS (Solana pubkey for fee collection)
6. **Stripe**: Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET for billing

## Revenue Model
| Tier | Price | Agents | TX/mo | Fee |
|------|-------|--------|-------|-----|
| Free | $0/mo | 3 | 1,000 | 0.5% |
| Pro | $49/mo | 25 | 50,000 | 0.25% |
| Enterprise | $299+/mo | Unlimited | Unlimited | 0.1% |

## Git History (8 commits on master)
1. Initial commit: full architecture
2. Add comprehensive project README
3. Fix runtime issues: SQLite compat, bcrypt, session refresh, rate limiter
4. Docker stack fully operational + dashboard build fix
5. Add landing page, Railway deploy config, fix SDK build
6. Increase Railway healthcheck timeout
7. Skip alembic / fix PORT variable
8. Wrap Railway start command in sh -c + rename SDK to agentwallet-sdk

## Related Project
- moltfarm: Solana utilities reused in this project (transfer_sol, confirm_transaction, retry decorator)
