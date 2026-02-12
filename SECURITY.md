# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x (current) | Yes |
| < 0.1.0 | No |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

### Critical Vulnerabilities

For critical issues (private key exposure, fund theft, authentication bypass, escrow manipulation), email directly:

**web3youth@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Your suggested fix (if any)

We will acknowledge receipt within **24 hours** and provide an initial assessment within **72 hours**.

### Non-Critical Concerns

For lower-severity issues (rate limiting gaps, minor input validation, informational leaks), you can use the [Security Vulnerability](https://github.com/YouthAIAgent/agentwallet/issues/new?template=security_vulnerability.yml) issue template.

## Security Architecture

### Key Management
- Private keys encrypted at rest using **Fernet** (dev) / **AWS KMS** (production)
- Keys are **never** returned in API responses
- Keys are **never** logged or included in error messages

### Authentication
- **JWT tokens** for session-based auth (short-lived, signed with HS256)
- **API keys** for programmatic access (prefixed `aw_live_` / `aw_test_`)
- **bcrypt** password hashing with automatic salting

### Transaction Security
- Policy engine evaluates every transaction before chain submission
- Spending limits (per-transaction and daily rolling)
- Destination whitelist/blacklist enforcement
- Idempotency keys prevent double-spend
- All state changes recorded in immutable audit log

### Escrow Security
- Funds held in on-chain PDAs (Program Derived Addresses)
- Only funder or arbiter can release/refund
- Automatic expiry with refund on timeout
- No single party can unilaterally withdraw

### Infrastructure
- CORS restrictions on all endpoints
- Redis-backed rate limiting per authentication tier
- HMAC-signed webhook deliveries
- Input validation on all API endpoints (Pydantic)
- SQL injection prevention via SQLAlchemy parameterized queries

### On-Chain Program
- Anchor framework with built-in account validation
- Owner checks on all privileged instructions
- Signer verification for transfers and escrow operations
- Overflow-safe arithmetic

## Responsible Disclosure

We follow a **90-day disclosure policy**:

1. You report the vulnerability privately
2. We acknowledge and begin investigation
3. We develop and test a fix
4. We release the fix and notify affected users
5. After 90 days (or after the fix is deployed), you may publicly disclose

We will credit reporters in our security changelog unless you prefer to remain anonymous.

## Bug Bounty

We do not currently have a formal bug bounty program. However, we recognize and credit significant security contributions in our [Security Changelog](SECURITY_CHANGELOG.md) and project documentation.
