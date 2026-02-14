# Changelog

All notable changes to AgentWallet Protocol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-12

### Added
- **PDA Wallet API** — 7 on-chain endpoints for Solana PDA wallet management
- **Agent Marketplace** — full agent-to-agent service commerce with hiring, jobs, messaging
- **Reputation Scoring** — weighted composite reputation (reliability, quality, communication, experience)
- **Universal Balance Service** — cross-chain balance aggregation (Solana + EVM)
- **SPL Token Support** — transfer and balance queries for USDC/USDT stablecoins
- **x402 Payment Gateway** — HTTP-native auto-pay middleware for AI agents
- **ERC-8004 Identity** — cross-chain identity registration on Base mainnet
- **Comprehensive Test Suite** — 53 tests covering all critical paths
- **CI/CD Pipeline** — GitHub Actions: lint, test (Python 3.11/3.12), build, security scan, auto-deploy
- **Security Hardening** — Swagger gate, CSP headers, CORS lockdown, password policy enforcement
- **Community Files** — CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, issue/PR templates

### Changed
- SDK package renamed to `agentwallet-sdk` on PyPI (plain `agentwallet` was taken)
- Upgraded to SDK v0.2.0 with dashboard production API config
- All ORM relationships use `lazy="noload"` to prevent MissingGreenlet errors in async context

### Fixed
- Railway deployment crashes — import fixes, optional web3/eth-account dependencies
- Marketplace MissingGreenlet errors — test suite rewrite with proper async fixtures
- SQLite test compatibility — JSON columns instead of JSONB, StaticPool engine

## [0.1.0] - 2026-02-08

### Added
- **Core API** — FastAPI backend with 53 endpoints across 13 router groups
- **Wallet Engine** — custodial Solana wallet creation with encrypted private keys (Fernet/KMS)
- **Permission Engine** — policy evaluation with spending limits, whitelists, time windows
- **Transaction Engine** — SOL transfers with idempotency, fee calculation, policy enforcement
- **Escrow Service** — trustless escrow with state machine (create → fund → release/refund/dispute)
- **Analytics Engine** — daily pre-aggregated rollups, per-agent spending trends, CSV export
- **Compliance Module** — immutable audit trail, anomaly detection, EU AI Act Article 52 reports
- **Webhook System** — event subscriptions with HMAC-signed delivery
- **Background Workers** — TX confirmation (5s), webhook dispatch (1s), analytics (60s), escrow expiry (300s)
- **Rate Limiting** — Redis-backed per-org/tier (free: 60/min, pro: 600/min, enterprise: 6000/min)
- **Authentication** — JWT + API key dual auth with bcrypt password hashing
- **Fee System** — tier-based BPS (0.5%/0.25%/0.1%) with minimum 1000 lamports
- **Python SDK** — async Stripe-like client (`agentwallet-sdk`)
- **React Dashboard** — 9-page admin interface with Recharts analytics
- **CLI Dashboard** — Rich terminal operator view
- **Solana Program** — Anchor/Rust on-chain program (7 instructions, 3 PDAs)
- **Docker Stack** — PostgreSQL + Redis + API + Worker + Dashboard
- **Database Migrations** — Alembic with 3 migration versions (14+ tables)
- **Landing Page** — static marketing site

### Infrastructure
- Railway deployment (PostgreSQL + Redis)
- Solana devnet integration
- Structlog JSON logging
- MIT License
