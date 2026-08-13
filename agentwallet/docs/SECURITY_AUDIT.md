# AgentWallet — Security Audit Report

Audit date: 2026-08-13
Scope: x402 replay protection, private key storage, auth flow, rate limiting.

Summary: **4 vulnerabilities found, 4 fixed.** Private key storage was
already sound. All fixes are covered by tests (`tests/test_security.py`,
7 tests) and verified live against the running stack.

---

## 1. x402 payment replay — FIXED (High)

**Vulnerability:** After a payment proof was verified once and cached,
every subsequent request with the same `X-PAYMENT` header passed the
paywall **indefinitely** — the cache-hit path skipped the timestamp /
deadline check entirely, and never re-checked that the cached payment
matched the *current* route's payee or price. A paid signature could be
replayed forever, and a proof paid for route A (cheap) could be replayed
against route B (expensive) with a different recipient.

**Fix** (`services/x402_server.py`):
- Cache entries now store `{valid, verified_at, payee, amount, token_mint}`.
- Cache hits are still protected: the proof must be **fresh** (within
  `max_deadline_seconds`) and the cached **payee + amount must match the
  current pricing**. Violations drop the cache entry and return 402.
- Negative results are cached too, so a rejected signature stays rejected.

**Tests:** `test_replay_proof_expires_after_deadline`,
`test_replay_proof_rejected_for_different_payee`.

## 2. JWT auth: disabled / mismatched users — FIXED (High)

**Vulnerability:** The JWT verification path validated that the
*organization* was active but **never looked up the user**. A user whose
account was disabled (or deleted) could keep using their token for the
full 24 h expiry window, and nothing verified the user actually belonged
to the org claimed in the token.

**Fix** (`api/middleware/auth.py`):
- The user is now loaded from the DB; missing or inactive users get 401.
- The token's `org_id` must match the user's real `org_id`, otherwise 401.

**Tests:** `test_disabled_user_token_rejected`,
`test_user_org_mismatch_token_rejected`.

## 3. API key permissions not enforced — FIXED (High)

**Vulnerability:** API keys carry a `permissions` dict (e.g.
`{"wallets": "rw"}`) but nothing ever checked it. A read-only key could
move funds, configure x402 pricing, or alter escrows — permissions were
cosmetic.

**Fix:**
- `AuthContext` now carries the API key's permissions and exposes
  `has_permission(resource, mode)`; JWT (user) actors are full-access.
- New `require_permission(resource, mode)` FastAPI dependency factory.
- Applied to money-moving / sensitive routes: `transfer-sol`,
  `batch-transfer`, `tokens/transfer`, `escrow/{id}/action`,
  `billing/subscribe|renew|cancel`, `x402/configure`.

**Tests:** `test_api_key_without_wallet_permission_cannot_transfer`,
`test_api_key_with_wallet_permission_passes_permission_gate`,
`test_api_key_without_x402_permission_cannot_configure`.

## 4. Rate limiting missing on ACP + Swarms routers — FIXED (Medium)

**Vulnerability:** Every router except `acp.py` and `swarms.py` applied
`check_rate_limit`. Those two (agent-to-agent commerce + swarm
coordination, both state-changing) had **no rate limiting at all** — an
org could hammer them without limit.

**Fix:** Added `rate_limited_auth`, a router-level dependency that
resolves auth and enforces the org's tier rate limit. Attached to the
ACP and Swarms routers (`dependencies=[Depends(rate_limited_auth)]`).

**Note:** the rate limiter already has an in-process sliding-window
fallback when Redis is unavailable — it does *not* fail open. The
LAUNCH_CHECKLIST text about "fail open" is outdated; the code degrades
to a per-process limiter instead.

## 5. Private key storage — NO ISSUE FOUND (audited)

- Wallet keypairs are encrypted at rest with **Fernet** (`core/kms.py`),
  backed by **AWS KMS** in production when `AWS_KMS_KEY_ID` is set.
- `ENCRYPTION_KEY` is required at startup (refuses to boot without it).
- Private keys never leave the server; the API only ever sees addresses.
- API keys are stored as **HMAC-SHA256 hashes** (not plaintext), keyed by
  the server secret — offline brute-force of a leaked DB requires the
  server secret too.
- Passwords are bcrypt-hashed with a strong policy (8+ chars, upper /
  lower / digit / special) enforced by the schema.
- Account lockout (5 failures → 15 min lock) is in place on login.

**Recommendations (no code change required):**
1. Back up the platform keypair (`packages/api/.platform-keypair.json`)
   to cold storage and delete it from the workspace before launch.
2. Rotate `JWT_SECRET_KEY` / `ENCRYPTION_KEY` to fresh random values for
   production (the `.env` values are dev-only).
3. Consider per-IP rate limiting for `/auth/login` (currently per-org
   bucket, which limits distributed credential stuffing only partially).

---

## Verification

- `pytest packages/api/tests` → **138 passed** (7 new security tests).
- `ruff check` → clean.
- Live checks against the running API:
  - read-only API key → `POST /v1/transactions/transfer-sol` → **403**
  - disabled user JWT → `GET /v1/agents` → **401**
  - ACP / Swarms endpoints → rate-limited (200 under limit, 429 above)
