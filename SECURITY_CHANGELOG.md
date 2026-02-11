# Security Changelog

Security fixes applied from audit findings on 2026-02-11.

---

## Critical Fixes

### 1. ENCRYPTION_KEY made mandatory (`core/kms.py`)
- **Before:** If `ENCRYPTION_KEY` was not set, the `KeyManager` would silently generate an ephemeral Fernet key via `Fernet.generate_key()`. This meant encrypted wallet keys would become permanently undecryptable after a process restart.
- **After:** A `RuntimeError` is raised if `ENCRYPTION_KEY` is not set, with clear instructions on how to generate one. No more silent data-loss footgun.

### 2. Program ID placeholder warning (`lib.rs`)
- **Before:** The `declare_id!` used a placeholder (`AWPro111...`) with no indication it was temporary.
- **After:** Added prominent `⚠️ SECURITY` comments above the macro making it unmistakable that this MUST be replaced before mainnet deployment.

### 3. Escrow PDA closing on release/refund (`escrow.rs`)
- **Before:** After releasing or refunding escrow funds, the PDA remained open with rent-exempt lamports still locked inside — wasting SOL and leaving stale accounts on-chain.
- **After:**
  - `handler_release_escrow`: After transferring the escrowed amount to the recipient, all remaining lamports (rent) are sent to the original funder, and the account is zeroed/closed.
  - `handler_refund_escrow`: All lamports (escrowed amount + rent) are transferred to the funder in one step, and the account is zeroed/closed.
  - `ReleaseEscrow` accounts struct now includes a `funder` account (validated against `escrow_account.funder`) to receive the rent refund.

### 4. Zero-amount escrow validation (`escrow.rs`, `errors.rs`)
- **Before:** `handler_create_escrow` accepted `amount = 0`, which could create zero-value escrows wasting rent and cluttering state.
- **After:** Added `require!(amount > 0, AgentWalletError::InvalidAmount)` at the top of the handler. Added new `InvalidAmount` error variant to `errors.rs`.

---

## Medium Fixes

### 5. Rate limiting on auth routes (`api/routers/auth.py`)
- **Before:** The `/register` and `/login` endpoints had no rate limiting, making them vulnerable to credential stuffing and brute-force attacks.
- **After:** Both endpoints now call `check_rate_limit()` from the existing `rate_limit` middleware, using anonymous org IDs (`anon:register`, `anon:login`) to track unauthenticated requests. Added security documentation in the module docstring.

### 6. API key hashing upgraded to HMAC-SHA256 (`api/middleware/auth.py`)
- **Before:** `hash_api_key()` used plain `hashlib.sha256()`, meaning a database leak would allow offline brute-force of API keys.
- **After:** Changed to `hmac.new(server_secret, key, sha256)` using `settings.jwt_secret_key` as the HMAC key. An attacker with only the database cannot verify candidate keys without the server secret.
- **⚠️ Migration note:** Existing API key hashes in the database will no longer match. A data migration must be run to re-hash all active API keys, or existing keys will need to be rotated.

### 7. JWT secret minimum length validation (`core/config.py`)
- **Before:** `jwt_secret_key` defaulted to `"change-me-in-production"` (23 chars) with no validation, allowing weak secrets in production.
- **After:** Added a Pydantic `field_validator` that rejects any `jwt_secret_key` shorter than 32 characters with a clear error message and generation instructions. The app will refuse to start with a weak secret.

### 8. Fee behavior documented (`transfer_with_limit.rs`)
- **Before:** The fee deduction model (fee comes FROM the transfer amount, not on top) was implicit in the code but not documented.
- **After:** Added comprehensive docstring to `handler()` explaining the fee model with a concrete example, and added an inline comment at the fee calculation. This prevents client-side misunderstandings about recipient amounts.
