# GitHub Actions CI/CD Pipeline

This repository includes comprehensive CI/CD pipelines for the AgentWallet project using GitHub Actions.

## 🚀 Workflows Overview

### 1. Main CI/CD Pipeline (`ci.yml`)

**Triggers:**
- Push to `master`/`main` branches
- Pull requests to `master`/`main` branches  
- Release creation

**Jobs:**
- **Lint**: Code quality checks using `ruff` on the API package
- **Test**: Run test suite across Python 3.11 and 3.12 with PostgreSQL and Redis services
- **Build**: Build SDK and MCP server packages
- **Security**: Vulnerability scanning with Trivy
- **Deploy**: Publish packages to PyPI (only on releases)

### 2. Solana Program Pipeline (`solana.yml`)

**Triggers:**
- Push/PR when Solana program files change
- Changes to `Anchor.toml` or the workflow file

**Jobs:**
- **Build Program**: Compile Anchor/Rust program with linting
- **Security Audit**: Run `cargo audit` for security vulnerabilities
- **Test Program**: Run Anchor tests with local validator
- **Verify Deployment**: Check program size and deployment readiness

## 📋 Required GitHub Secrets

To enable full functionality, add these secrets in your repository settings (`Settings > Secrets and variables > Actions`):

### Required for PyPI Publishing
- `PYPI_TOKEN`: Your PyPI API token for publishing packages
  - Generate at: https://pypi.org/manage/account/token/
  - Scope: Entire account or specific projects

### Optional Secrets
- `CODECOV_TOKEN`: For code coverage reporting
  - Get from: https://codecov.io/ after connecting your repository

## 🔧 Pipeline Features

### Code Quality
- **Linting**: `ruff check` for code style and errors
- **Formatting**: `ruff format --check` for consistent formatting
- **Security**: Trivy vulnerability scanning
- **Rust**: `cargo clippy` and `cargo fmt` for Solana programs

### Testing
- **Matrix Testing**: Python 3.11 and 3.12
- **Services**: PostgreSQL and Redis for integration tests
- **Coverage**: Code coverage reporting with Codecov integration
- **Solana**: Local validator testing for smart contracts

### Build & Deploy
- **Package Building**: SDK and MCP server packages
- **Artifact Upload**: Build artifacts stored for each run
- **PyPI Publishing**: Automated package publishing on releases
- **Program Verification**: Solana program size and deployment checks

## 📦 Package Structure

The CI/CD pipeline handles these packages:

1. **API Package** (`packages/api/`)
   - FastAPI-based backend
   - PostgreSQL + Redis integration
   - Comprehensive test suite

2. **SDK Package** (`packages/sdk-python/`)
   - Python SDK for AgentWallet Protocol
   - Published to PyPI as `aw-protocol-sdk`

3. **MCP Server Package** (`packages/mcp-server/`)
   - Model Context Protocol server
   - Published to PyPI as `agentwallet-mcp`

4. **Solana Program** (`packages/programs/agentwallet/`)
   - Anchor/Rust smart contract
   - Deployed to Solana blockchain

## 🚦 Workflow Status

You can monitor workflow status in the Actions tab of your repository. Each workflow provides detailed logs and summaries.

### Status Badges

Add these to your README.md to show build status:

```markdown
![CI/CD](https://github.com/YouthAIAgent/agentwallet/workflows/CI/CD%20Pipeline/badge.svg)
![Solana](https://github.com/YouthAIAgent/agentwallet/workflows/Solana%20Program%20CI/badge.svg)
```

## 🔄 Release Process

To trigger a new release deployment:

1. Create a new release in GitHub (`Releases > Create a new release`)
2. Add a version tag (e.g., `v0.2.0`)
3. The CI/CD pipeline will automatically:
   - Run all tests
   - Build packages
   - Publish to PyPI
   - Create deployment summary

## 🛠️ Local Development

To run the same checks locally:

```bash
# Python linting and formatting
ruff check packages/api/
ruff format packages/api/

# Run tests
pytest packages/api/tests/ -v

# Build packages
cd packages/sdk-python && python -m build
cd packages/mcp-server && python -m build

# Solana program
anchor build
anchor test
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Anchor Framework](https://github.com/coral-xyz/anchor)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Solana CLI Guide](https://docs.solana.com/cli)