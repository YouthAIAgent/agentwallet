# Security Policy

## AgentWallet Protocol

AgentWallet is a Solana-based autonomous wallet infrastructure for AI agents. We take the security of our protocol, smart contracts, and user funds seriously. This document outlines how to report vulnerabilities, what falls within scope, and how we handle security disclosures.

---

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly through one of the following channels:

- **Email:** [security@agentwallet.fun](mailto:security@agentwallet.fun)
- **GitHub Security Advisories:** Use the "Report a vulnerability" feature under the Security tab of this repository.

**Do NOT open a public GitHub issue for security vulnerabilities.**

When submitting a report, please include:

- A clear description of the vulnerability and its potential impact.
- Detailed steps to reproduce the issue, including any tools, scripts, or payloads used.
- The affected component(s) (API, smart contract, SDK, web application, etc.).
- Any relevant logs, screenshots, or proof-of-concept code.
- Your suggested severity classification, if applicable.

---

## Scope

The following components are in scope for security reports:

- **API Endpoints** -- All endpoints across auth, wallets, agents, transactions, escrow, analytics, compliance, policies, webhooks, tokens, ERC-8004, X402, and marketplace routers.
- **Smart Contracts** -- Solana programs including PDA-derived vault logic, escrow contracts, and token operations.
- **SDK** -- The AgentWallet SDK (client libraries, signing utilities, transaction builders).
- **Authentication System** -- JWT token issuance and validation, API key generation and verification, session management.
- **Escrow System** -- Fund locking, release conditions, dispute resolution logic.
- **Web Application** -- The dashboard, landing page, and any associated frontend components.
- **Key Management** -- Encrypted key storage, derivation paths, and access controls.

---

## Out of Scope

The following are excluded from this security policy:

- **Social engineering attacks** -- Phishing, pretexting, or other attacks targeting team members or users directly.
- **Denial of Service (DoS/DDoS)** -- Volumetric or resource-exhaustion attacks against infrastructure.
- **Third-party services** -- Vulnerabilities in external dependencies, hosting providers (Railway, Solana RPC nodes), or upstream libraries unless the issue is in how AgentWallet integrates with them.
- **Self-XSS** -- Attacks that require a user to paste code into their own browser console.
- **Issues requiring physical access** to a user's device.
- **Bugs in software or protocols not maintained by the AgentWallet team.**
- **Reports from automated scanners** without a demonstrated, exploitable vulnerability.

---

## Response Timeline

We are committed to addressing security reports promptly:

| Stage | Timeline |
|---|---|
| **Acknowledgment** | Within 48 hours of receipt |
| **Triage and Initial Assessment** | Within 5 business days |
| **Fix -- Critical severity** | Target resolution within 24-48 hours |
| **Fix -- High severity** | Target resolution within 7 days |
| **Fix -- Medium severity** | Target resolution within 30 days |
| **Fix -- Low severity** | Target resolution within 90 days |

We will keep reporters informed of progress throughout the remediation process. Timelines may vary depending on complexity, but we will communicate any delays.

---

## Severity Classification

We classify vulnerabilities using the following severity levels:

### Critical

Vulnerabilities that allow an attacker to compromise user funds, extract private keys, or take full control of the protocol.

- Private key compromise or extraction from encrypted storage.
- Unauthorized fund theft from wallets or escrow accounts.
- Arbitrary Solana program instruction injection leading to fund loss.
- Complete bypass of the policy engine enabling unrestricted transactions.

### High

Vulnerabilities that allow significant unauthorized access or privilege escalation.

- Authentication bypass (JWT forgery, API key leakage through endpoints).
- Privilege escalation (agent gaining owner-level permissions, cross-tenant access).
- Escrow manipulation (unauthorized release, condition tampering).
- SQL injection or remote code execution on API servers.

### Medium

Vulnerabilities that expose sensitive data or allow limited manipulation.

- Personally identifiable information or wallet metadata leakage.
- Cross-site scripting (XSS) on the dashboard or landing page.
- Insecure direct object references exposing other users' data.
- Broken access controls on non-critical endpoints.

### Low

Vulnerabilities with minimal direct impact.

- Verbose error messages disclosing internal implementation details.
- Information disclosure through HTTP headers or server metadata.
- Missing security headers or minor configuration issues.
- Rate limiting gaps on non-sensitive endpoints.

---

## Bug Bounty

We offer rewards in $AW tokens for valid, responsibly disclosed vulnerabilities. Reward amounts are determined based on severity, impact, and quality of the report.

| Severity | Reward (up to) |
|---|---|
| **Critical** | 5,000 $AW |
| **High** | 2,000 $AW |
| **Medium** | 500 $AW |
| **Low** | 100 $AW |

### Eligibility

- The vulnerability must be in scope as defined above.
- The report must include sufficient detail to reproduce the issue.
- The vulnerability must not have been previously reported or publicly known.
- You must not have exploited the vulnerability beyond what is necessary for demonstration.
- You must comply with the responsible disclosure guidelines below.

Rewards are issued at the sole discretion of the AgentWallet team. Duplicate reports will be credited to the first submission received.

---

## Security Measures

AgentWallet employs multiple layers of security across the protocol:

- **Authentication:** Dual-layer authentication using JWT tokens and API keys. All tokens are short-lived with secure refresh flows.
- **PDA-Derived Vaults:** Agent wallets use Solana Program Derived Addresses, ensuring funds are controlled by on-chain program logic rather than externally held keys.
- **Policy Engine:** Configurable transaction policies enforce spending limits, whitelist restrictions, and approval workflows before any funds move.
- **Audit Logging:** All actions across the API are logged with full attribution for forensic review and compliance.
- **Encrypted Key Storage:** Private keys at rest are encrypted and never exposed through API responses.
- **Row-Level Security (RLS):** Database access is enforced at the row level to prevent cross-tenant data access.

---

## Responsible Disclosure

We ask that security researchers follow these guidelines:

- **Do not publish or disclose vulnerability details publicly** before a fix has been released and deployed.
- **Coordinate with the AgentWallet team** on disclosure timing. We aim to resolve issues before any public announcement.
- **Do not access, modify, or delete data** belonging to other users during your research.
- **Do not perform actions that could degrade service** for other users (load testing, spam, denial of service).
- **Use test accounts and testnets** whenever possible.

We will credit researchers in our security acknowledgments (unless anonymity is preferred) and will not pursue legal action against individuals who follow this responsible disclosure policy in good faith.

---

## Contact

- **Security reports:** [security@agentwallet.fun](mailto:security@agentwallet.fun)
- **General inquiries:** Open an issue on GitHub or reach out through our community channels.

---

This policy is effective as of February 2026 and may be updated periodically. Check this document for the latest version.
