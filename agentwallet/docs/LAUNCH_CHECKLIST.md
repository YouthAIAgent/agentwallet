# AgentWallet — Production Launch Checklist

Everything needed to take AgentWallet from dev environment to a live,
billing-enabled production launch. Checked items are already done in the
current workspace; unchecked items need credentials or access that only
the account owner can provide.

---

## 1. Platform Wallet (fee collection) — ✅ DONE locally

Platform fees (per-transaction % deducted atomically) are only collected
when `PLATFORM_WALLET_ADDRESS` is set. Without it, every transfer runs
with zero platform fee.

**Done in this workspace:**
- Generated a new Solana keypair (mainnet-capable).
- Set `.env`:
  ```
  PLATFORM_WALLET_ADDRESS=BTcvExhix1pfVX25imKzkHquGJrncZjijxEJq1RkKK5
  ```
- Private key saved (gitignored) to:
  `packages/api/.platform-keypair.json`

**You must do:**
1. **Back up the private key NOW** — open `packages/api/.platform-keypair.json`
   and store the `secret_key_hex` somewhere safe (password manager / cold
   storage). Anyone with this hex controls the wallet.
2. In production (Railway): set the same `PLATFORM_WALLET_ADDRESS` in the
   Railway deployment variables.
3. (Optional) Send a few lamports to the address on mainnet so the wallet
   exists on-chain before launch.
4. Keep the keypair file out of any repo (it is already covered by
   `*-keypair.json` in `.gitignore`).

**Verified:** API loads the address and `TransactionEngine` now passes
`fee_recipient=PLATFORM_WALLET_ADDRESS` on every transfer.

---

## 2. Stripe Billing — ⏳ NEEDS YOUR ACCOUNT

The codebase has a `BillingService` with tier pricing
(`free = $0`, `pro = $49/mo`, `enterprise = $299/mo`) and a usage meter,
but **Stripe keys are empty and no billing routes are exposed yet**.

**You must do:**
1. Create a Stripe account: https://stripe.com → Dashboard.
2. Get the **Secret key** (Dashboard → Developers → API keys) — use
   `sk_test_...` for testing first.
3. Create a **webhook endpoint** (Dashboard → Developers → Webhooks):
   - URL: `https://your-api-domain/v1/billing/webhook`
   - Events: `checkout.session.completed`, `invoice.paid`,
     `customer.subscription.updated`, `customer.subscription.deleted`
   - Copy the **Signing secret** (`whsec_...`).
4. Set in `.env` (and in Railway):
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

**Remaining code work** (not yet implemented):
- Add `/v1/billing` routes: `GET /v1/billing/usage`, `POST /v1/billing/checkout`
  (create Stripe Checkout Session), `POST /v1/billing/webhook` (verify
  signature, update org tier), `POST /v1/billing/portal` (Stripe Billing
  Portal).
- Wire `BillingService` into the auth/org tier logic (tier limits already
  read `org.tier`, so upgrading a tier via webhook is all that's needed).

---

## 3. Redis on Railway — ⏳ NEEDS RAILWAY ACCESS

The API requires Redis for rate limiting, the background workers
(`arq`), and caching. On Railway only Postgres is provisioned today, so
`REDIS_URL` points at nothing in production.

**You must do:**
1. In the Railway dashboard, click **+ New** → **Database** → **Redis**.
2. Copy the generated `REDIS_URL` (starts with `redis://...`).
3. Add it as a variable on the **API service** (and the worker service
   when one is added): `REDIS_URL=redis://...`.
4. The API is designed to **fail open** when Redis is unavailable (rate
   limiter skips), so the app won't crash — but billing/rate limits and
   workers need it.

Note: `railway.json` already runs `alembic upgrade head` before starting
the API (migrations are automatic on deploy).

---

## 4. PyPI — SDK is built, needs your token — ⏳ LAST STEP

The `aw-protocol-sdk` package builds cleanly and installs correctly.

**Done in this workspace:**
- Built artifacts (sdist + wheel):
  ```
  packages/sdk-python/dist/aw_protocol_sdk-0.4.0-py3-none-any.whl
  packages/sdk-python/dist/aw_protocol_sdk-0.4.0.tar.gz
  ```
- Verified: fresh venv install + `from agentwallet import AgentWallet`
  works.

**You must do:**
1. **Bump the version** to match the current release (e.g. `0.4.6`) in
   `packages/sdk-python/pyproject.toml` and rebuild:
   ```bash
   cd packages/sdk-python
   python -m build
   ```
2. Create a PyPI account: https://pypi.org → Account settings → API tokens
   → **Add API token** (scope: entire account or just the `aw-protocol-sdk`
   project).
3. Upload (twine is installed in the tools venv):
   ```bash
   cd packages/sdk-python
   python -m twine upload dist/* --username __token__ --password pypi-<YOUR-TOKEN>
   ```
4. Verify: `pip install aw-protocol-sdk` on a fresh machine.

---

## Launch-day checklist

- [ ] Platform wallet address live on mainnet (Railway var set)
- [ ] Private key backed up securely
- [ ] Stripe keys set + webhook endpoint created
- [ ] `/v1/billing` routes shipped
- [ ] Redis provisioned on Railway + `REDIS_URL` set
- [ ] SDK published to PyPI (`pip install aw-protocol-sdk` works)
- [ ] Smoke test green in CI (`VALIDATOR_MODE=1`)
- [ ] Landing page + API docs public (https://agentwallet.fun / /docs)
- [ ] Security audit passed (see SECURITY_AUDIT.md)
