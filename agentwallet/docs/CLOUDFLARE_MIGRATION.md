# Cloudflare Full-Proxy Migration — Click-Path Checklist

Move `agentwallet.fun` (currently on Vercel DNS) to Cloudflare so every request
gets a real country code (`CF-IPCountry`) and the API gets Cloudflare's edge
(WAF, caching, bot fight). No application code changes are needed — the backend
already prefers `CF-IPCountry` first (see `services/presence.py:_GEO_HEADERS`).

- **Why full zone**: Cloudflare Free does not offer CNAME/partial setup — you
  must move the whole zone's nameservers.
- **What you need**: a Cloudflare account + access to the registrar where
  `agentwallet.fun` is registered (the registrar that issued the domain — the
  nameservers currently point to Vercel, but the domain registration lives at
  the registrar).
- **Expected downtime**: dashboard keeps serving from Vercel the whole time
  (Cloudflare proxies to the same origins). Worst case ~24h propagation before
  all resolvers see the new nameservers.

---

## Step 0 — Snapshot current DNS (Vercel)

1. Go to the **Vercel dashboard** → project **landing-page** → **Settings** →
   **Domains**.
2. Click **agentwallet.fun** → **DNS records** (or Settings → Domains → DNS).
3. Export/screenshot every record. Today's set is roughly:
   | Type | Name | Value | Notes |
   |------|------|-------|-------|
   | A | `@` | `216.198.79.65` | Vercel apex — verify current IPs before migrating |
   | A | `@` | `64.29.17.1` | second Vercel apex IP |
   | CNAME | `api` | `a70gs6rx.up.railway.app` | **DEAD** — repoint to `api-production-6421a.up.railway.app` in Cloudflare |
   | TXT | `_vercel` | (verification value) | keep during migration, delete after Vercel re-verifies |
4. Note the current nameservers: `ns1.vercel-dns.com`, `ns2.vercel-dns.com` —
   keep these for rollback.

## Step 1 — Create the zone (dashboard.cloudflare.com)

1. Open **https://dash.cloudflare.com** and sign in.
2. On the account home (list of sites), click **+ Add site** (top-right, blue
   button).
3. In the **Add site** modal: type `agentwallet.fun` in the **Domain name**
   field → click **Continue**.
4. **Choose a plan** → select **Free** ($0) → click **Continue**.
   - If prompted, confirm the site is not already on Cloudflare.
5. Cloudflare scans the existing DNS (from the registrar's current NS — it will
   import whatever it can). **Review the imported records** — fix any obvious
   errors now (you'll re-add them cleanly in Step 2 anyway).
6. Click **Continue**.
7. Cloudflare shows **two nameservers** for the zone, e.g.:
   - `ada.ns.cloudflare.com`
   - `bob.ns.cloudflare.com`
   - **Copy both.** You can click **I'll do this later** and change NS later;
     the zone stays in *Pending Nameserver* state until then.
8. Click **Done** (or **Check nameservers now** — it will show "pending" until
   Step 4 completes).

## Step 2 — Add DNS records (DNS → Records)

1. From the zone overview, click **DNS** in the left sidebar, then **Records**.
2. Click the blue **Add record** button. Add these one by one:

   **Apex A record (dashboard):**
   - **Type**: `A`
   - **Name**: `@`
   - **IPv4 address**: `216.198.79.65` (current Vercel apex IP)
   - **Proxy status**: toggle **Proxied** (orange cloud) → **Save**
   - Repeat for the second apex IP `64.29.17.1` (same name `@`).

   **API CNAME (fixes the dead subdomain):**
   - **Type**: `CNAME`
   - **Name**: `api`
   - **Target**: `api-production-6421a.up.railway.app`
   - **Proxy status**: **Proxied** (orange cloud) → **Save**
   - Now `api.agentwallet.fun` serves the live API and every direct call gets
     `CF-IPCountry` automatically.

   **www (optional):**
   - **Type**: `CNAME` · **Name**: `www` · **Target**: `cname.vercel-dns.com`
   - **Proxy status**: **Proxied** → **Save** (skip if `www` is unused).

   **Vercel verification TXT (temporary):**
   - **Type**: `TXT` · **Name**: `_vercel` · **Content**: (value from Step 0)
   - **Proxy status**: not applicable for TXT (always grey) → **Save**.
   - Delete after Vercel confirms the domain is still verified.

3. Click **Save** after each record. Final list should look like:
   | Type | Name | Target | Proxy |
   |------|------|--------|-------|
   | A | `@` | `216.198.79.65` | 🟠 |
   | A | `@` | `64.29.17.1` | 🟠 |
   | CNAME | `api` | `api-production-6421a.up.railway.app` | 🟠 |
   | CNAME | `www` | `cname.vercel-dns.com` | 🟠 (optional) |
   | TXT | `_vercel` | (from Vercel) | ⚪ (temporary) |

## Step 3 — Enable TLS/edge settings (optional but recommended)

1. **SSL/TLS** → **Overview** → set mode to **Full (strict)** (Cloudflare
   verifies Railway's origin cert).
2. **SSL/TLS** → **Edge Certificates** → enable **Always Use HTTPS**.
3. **Caching** → **Configuration** → **Caching level**: Standard is fine;
   add a **Cache Rule** to bypass `/api/*` (API responses must not be cached):
   - Hostname: `agentwallet.fun` · Path: `/api/*` → **Bypass cache**.

## Step 4 — Change nameservers at the registrar

The exact clicks depend on the registrar (the company that sold/registered
`agentwallet.fun`). The flow is the same everywhere:

1. Log in to the **registrar account**.
2. Open **My Domains / Domain List** → select `agentwallet.fun`.
3. Find **Nameservers / DNS settings** (often under *Advanced*, *DNS*, or
   *Manage DNS*).
4. Switch from **Vercel nameservers** to **Custom nameservers** and enter the
   two Cloudflare NS values from Step 1.7.
5. **Save / Apply**. Keep the old Vercel NS values handy (rollback = restore
   them here).

## Step 5 — Verify (after propagation, minutes → 24h)

```bash
# nameservers now point at Cloudflare
dig +short agentwallet.fun NS          # expect *.ns.cloudflare.com
dig +short agentwallet.fun A           # expect Cloudflare proxy IPs (104.x/172.x)
dig +short api.agentwallet.fun CNAME   # expect api-production-6421a.up.railway.app

# dashboard still serves
curl -s -o /dev/null -w "%{http_code}\n" https://agentwallet.fun/          # 200
curl -s -o /dev/null -w "%{http_code}\n" https://agentwallet.fun/playground  # 200

# presence records a real country (NOT xx)
curl -s -X POST https://agentwallet.fun/api/v1/public/presence \
  -H "Content-Type: application/json" \
  -d '{"visitor_id":"cf-migrate-check-0001"}'
# → {"online":N,"countries":[{"code":"IN","count":1},...]}   <- your country, not xx

# direct API subdomain now works (was dead)
curl -s https://api.agentwallet.fun/health   # {"status":"ok","version":"0.4.0"}
```

1. Landing page badge shows flag emojis + real country counts.
2. Cloudflare dashboard zone status shows **Active** (nameservers verified).

## Step 6 — Post-migration cleanup (optional)

- Delete the `_vercel` TXT record after Vercel confirms the domain is verified.
- The Vercel middleware (`packages/dashboard/proxy.ts`) is now redundant for
  geo (CF adds `CF-IPCountry` directly) but harmless — keep as a fallback, or
  remove it and set `VITE_API_URL` back to the absolute Railway URL.

## Rollback

1. At the **registrar**, restore nameservers to `ns1.vercel-dns.com` /
   `ns2.vercel-dns.com`.
2. DNS propagation reverses over the next 24h; the Vercel middleware still
   proxies `/api/*` so nothing breaks in the meantime.
3. The Cloudflare zone config stays — re-activating later is one NS change.

---

## Security & operations notes

- Cloudflare terminates TLS at its edge (free universal SSL, auto-issued).
  Railway keeps its own TLS for the origin; with **Full (strict)** both hops
  are encrypted.
- Cloudflare sees unauthenticated API traffic in cleartext at the edge — do
  NOT add auth secrets to URLs. JWT/API-key auth stays in headers.
- Our per-IP rate limiting reads `X-Forwarded-For`, which Cloudflare sets —
  unchanged behavior.
- If you later point `api.agentwallet.fun` at Railway and the browser calls it
  directly (instead of via `/api` on the dashboard), CORS still allows
  `https://agentwallet.fun` (already configured on Railway).
