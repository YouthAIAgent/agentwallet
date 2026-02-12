# Contributing to AgentWallet

Thanks for your interest in contributing to AgentWallet! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/yourusername/agentwallet.git
   cd agentwallet/agentwallet
   ```
3. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
4. **Start infrastructure**:
   ```bash
   docker compose up -d postgres redis
   ```
5. **Run the API**:
   ```bash
   uvicorn agentwallet.main:app --reload --port 8000
   ```

## Development Workflow

1. Create a feature branch from `master`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests and linting:
   ```bash
   pytest packages/api/tests/ -v
   ruff check packages/api/
   ```
4. Commit using [Conventional Commits](https://conventionalcommits.org/):
   ```
   feat: add new endpoint for token transfers
   fix: correct escrow expiry calculation
   test: add wallet balance edge cases
   docs: update API reference for policies
   refactor: simplify transaction pipeline
   ```
5. Push and open a Pull Request against `master`

## Project Structure

```
agentwallet/
├── packages/
│   ├── api/            # FastAPI backend (Python)
│   ├── sdk-python/     # Python SDK (PyPI)
│   ├── mcp-server/     # MCP server (27 AI tools)
│   ├── dashboard/      # React + TypeScript frontend
│   ├── programs/       # Solana program (Anchor/Rust)
│   ├── cli/            # Operator CLI (Rich)
│   └── landing/        # Static landing page
├── scripts/            # Automation & marketing scripts
├── docs/               # Architecture documentation
└── narration/          # Explainer video scripts
```

## Code Style

| Component | Tool | Command |
|-----------|------|---------|
| Python | `ruff` | `ruff check packages/api/` |
| Python types | `mypy` | `mypy packages/api/` |
| TypeScript | `eslint` + `prettier` | `cd packages/dashboard && npm run lint` |
| Rust | `rustfmt` | `cd packages/programs/agentwallet && cargo fmt` |

## Testing

- **Framework**: pytest + pytest-asyncio
- **Database**: SQLite + aiosqlite (test environment)
- **Run all tests**: `pytest packages/api/tests/ -v`
- **Run specific test**: `pytest packages/api/tests/test_wallets.py -v`
- **Coverage**: `pytest packages/api/tests/ --cov=agentwallet`

All PRs must pass the existing test suite. New features should include tests.

## Architecture Decisions

These are established patterns — please don't change them:

- **JSON over JSONB** in ORM models (SQLite test compatibility)
- **`import bcrypt`** directly, not through passlib
- **`lazy="noload"`** on Organization/Agent/Webhook relationships
- **Redis fail-open** — rate limiter skips if Redis is unavailable
- **Fernet encryption** for dev, AWS KMS for production

See `CLAUDE.md` for the full list of architecture decisions.

## What to Work On

Check the [GitHub Issues](https://github.com/YouthAIAgent/agentwallet/issues) for open tasks. Good areas for contribution:

- **Stablecoin support** (USDC/USDT transfers)
- **Multi-chain expansion** (EVM L2 integrations)
- **Dashboard improvements** (new visualizations, UX)
- **SDK enhancements** (new language bindings)
- **Documentation** (tutorials, examples, guides)
- **Tests** (edge cases, integration tests)

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Include tests for new functionality
- Update documentation if behavior changes
- Ensure CI passes (lint + test + build)
- Write a clear PR description explaining the "why"

## Reporting Issues

- Use [GitHub Issues](https://github.com/YouthAIAgent/agentwallet/issues)
- Include steps to reproduce for bugs
- Include environment details (OS, Python version, etc.)

## Security

If you discover a security vulnerability, **do not** open a public issue. Email **web3youth@gmail.com** directly.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
