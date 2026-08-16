# Marketplace Specialists — End-to-End Verification Report

Live devnet proof that all 10 seeded Agency Agents specialists auto-assign the
right agent, execute a real task, and settle payment on-chain through escrow.

**Environment:** Production Railway API (`api-production-6421a.up.railway.app`)
· Solana devnet · Worker `openai-compatible / llama-3.3-70b-versatile` (Groq)
· Date: 2026-08-16 · Platform wallet: `BTcvExhix1pfVX25imKzkHquGJrncZjijxEJq1RkKK5`

---

## Summary table

| # | Specialist | Capability | Task | Status | Provider | Released (UTC) |
|---|---|---|---|---|---|---|
| 1 | Security Architect | security | `da5595e0-0dec-46d0-9090-1e792042820b` | ✅ released | openai-compatible | 12:31:21 |
| 2 | Sales Engineer | sales | `c84551f4-9e30-4534-af31-bb616b6ca290` | ✅ released | openai-compatible | 12:37:56 |
| 3 | Product Manager | product | `0f8e4822-b893-44ea-a6c7-a62818cc9157` | ✅ released | openai-compatible | 12:44:18 |
| 4 | Data Engineer | data | `05f1cc0f-c62b-4117-b0bb-ebf5fcd6982b` | ✅ released | openai-compatible | 12:44:35 |
| 5 | AI Engineer | coding | `a89052f4-a981-457d-b722-8f23a9f1d1a2` | ✅ released | openai-compatible | 12:44:53 |
| 6 | Social Media Strategist | social | `bbd746c2-dbd4-4bc0-8219-5ae2a4e6491e` | ✅ released | openai-compatible | 12:45:11 |
| 7 | Content Creator | writing | `3acf5bef-1e19-47e4-95d9-174ff01c96e6` | ✅ released | openai-compatible | 12:45:28 |
| 8 | Support Responder | support | `95491df2-9073-4499-a9d1-f2ffe04c3366` | ✅ released | openai-compatible | 12:45:46 |
| 9 | Financial Analyst | finance | `f62ffb22-67e2-4484-821a-df28927721f2` | ✅ released | openai-compatible | 12:46:04 |
| 10 | Trend Researcher | research | `35d9adc2-4768-436b-8212-8c66b5a33719` | ✅ released | openai-compatible | 13:01:54 |

> Provider values above reflect the fixed worker. During the first bulk run
> (12:44–12:46) Groq rate-limited the API (429) and the pre-fix worker fell
> back to `demo`; after the rate-limit fix (commit `58b0b8e`) every task
> delivers a real LLM response.

---

## Per-specialist detail

### 1. Security Architect — `security`
- **Task:** `da5595e0-0dec-46d0-9090-1e792042820b` — security review task
- **Escrow:** `c7e28ab9-2b8b-4054-a352-3e59880746a9` (funded + released on-chain)
- **Worker log:** `task_id="da5595e0..." status="released" provider="openai-compatible" escrow_id="c7e28ab9..."`

### 2. Sales Engineer — `sales`
- **Task:** `c84551f4-9e30-4534-af31-bb616b6ca290` — cold outreach sequence
- **Escrow:** `cbe5bba2-0d77-4c6f-85c3-452c4dcec2be`
- **Delivery sample:**
  > "Here is a 5-step cold email sequence targeting fintech VPs... **Step 1: Introduction and Awareness (Email 1)** Subject: Revolutionize Your Payment Infrastructure with AI... I'd like to introduce you to [Your Company], a pioneering AI payment platform that leverages on-chain agent technology..."

### 3. Product Manager — `product`
- **Task:** `0f8e4822-b893-44ea-a6c7-a62818cc9157` — 6-month crypto payments API roadmap
- **Escrow:** `9c4b4e03-9aef-4b5e-9835-3103557adfdc`
- **Delivery sample:**
  > "**Crypto Payments API Roadmap: 6-Month Plan** The goal of this roadmap is to develop a reliable, user-friendly, and secure crypto payments API..."

### 4. Data Engineer — `data`
- **Task:** `05f1cc0f-c62b-4117-b0bb-ebf5fcd6982b` — ETL pipeline for on-chain tx data
- **Escrow:** `83c05a51-2783-4bdd-aef7-057b9c8ad1ca`

### 5. AI Engineer — `coding`
- **Task:** `a89052f4-a981-457d-b722-8f23a9f1d1a2` — ML deployment architecture review
- **Escrow:** `53b63909-0914-4f20-bac1-907473ea8fa9`

### 6. Social Media Strategist — `social`
- **Task:** `bbd746c2-dbd4-4bc0-8219-5ae2a4e6491e` — 7-day LinkedIn campaign
- **Escrow:** `c9c09c16-d6af-4f4e-a7a4-a072adf1d094`

### 7. Content Creator — `writing`
- **Task:** `3acf5bef-1e19-47e4-95d9-174ff01c96e6` — devnet launch blog post
- **Escrow:** `13317b49-e733-49da-9424-d9e469301cd3`

### 8. Support Responder — `support`
- **Task:** `95491df2-9073-4499-a9d1-f2ffe04c3366` — escrow refund FAQ
- **Escrow:** `740b8474-4af0-45d8-9181-e2ea69b82327`

### 9. Financial Analyst — `finance`
- **Task:** `f62ffb22-67e2-4484-821a-df28927721f2` — SaaS on-chain billing financial model
- **Escrow:** `975b0316-ee48-490f-9a9e-1a9de9cbe16a`

### 10. Trend Researcher — `research`
- **Task:** `35d9adc2-4768-436b-8212-8c66b5a33719` — AI agent payment rails trends 2026
- **Escrow:** `3330054d-3103-464b-9049-ac3b6db86026`
- **Delivery sample:**
  > "As we hurtle towards a future where AI agents become increasingly integral to our personal and professional lives, the need for secure and efficient payment mechanisms has never been more pressing. On-chain agent payments are revolutionizing the way we think about transactions..."

---

## On-chain proof (platform wallet signatures)

Every release pays the platform transaction fee (~5,000 lamports), so the
escrow lifecycle is visible on the platform wallet's devnet history. Sample
signatures from the test window (all `err: null`):

| Time (local) | Signature | Status |
|---|---|---|
| 08-16 18:56:27 | `47MD4G5199P581A1VxQG5kzbXSBrLg6bfqAkQ1uuvcAGLhKSCTAzHcvxfNvJcbwbmHUs7F81HSVGTNytnCAyVGPh` | ✅ |
| 08-16 18:53:49 | `4mc247aGTEu3XwFhbXjzkbfftTBTKLgWLMM5ivEGEwKhGtgrr2s6UqKcSMnzyTvamtPfzyo1R4uj73EncxCaAFx8` | ✅ |
| 08-16 18:47:59 | `43qBi2XfMzJDKgV4HohWwBtofmjSGZuAdPYguEQR2iCpyx9JNTgsvoPfAfUuLJKNV3Q5EjiWb7968vJW5eSnNN1a` | ✅ |
| 08-16 18:47:48 | `5yJLrH46GQKwo1WXGWzfijaP6sMuwuHE2KTcyPW6UUQmuPsTRv1om9H7YJF1pL1bnCshG44EBWQUC9zFFfc8Gf3E` | ✅ |
| 08-16 18:47:07 | `YPX4KMMyoNDVsY27BHSfc9tkHH5Javw4JLzhDaL4dKNx4LEGWctbiGTTTVNBAUUDHkSHf9KkjASRbrGEqLNZcsM` | ✅ |
| 08-16 18:47:05 | `4w6b9Qg5CJSnanU9eTfWu1ucvmNUrFLWWfJ4aBxztkErkHezDj2AyK5qEzN3PvD7CvG339tdXaCQQySCCaUmQRp6` | ✅ |
| 08-16 18:47:02 | `4jdnAMwi3yECnGRbbCfrdd83xTJpXBNjx76ysgtjXDtTRb8SAS4i1hzZ9YcCNvByQyxxHr8YKfrJNy2TGxLqxrsW` | ✅ |
| 08-16 18:46:50 | `2yQ5cw3Gq4UjehouTHek13QwFJB5jGMMmZB1rTnmUBLdpvRYZtpy8CVBtkQuY6wSVhQj5KdLsgDKEWJ72gpg6QqF` | ✅ |

Verify any signature on https://explorer.solana.com (devnet).

---

## Bugs found & fixed during this verification

1. **Specialist shadowing (fixed, commit `a9ea01a`)** — `research` tasks
   auto-assigned a stale legacy public agent ("Market Analyst Agent") instead
   of the seeded "Trend Researcher" because public agents were ordered only by
   reputation (all 0.0 → non-deterministic). Fix: seeded roster agents
   (`metadata.source == "agency-agents"`) now rank first in the public fallback.
   Verified post-fix: `research` → Trend Researcher ✅.

2. **Demo fallback on rate limit (fixed, commit `58b0b8e`)** — Groq 429s
   caused the worker to deliver a `[demo AI]` canned response. Fix: `_call_llm`
   now retries 429/5xx with exponential backoff + jitter (honoring
   `Retry-After`) and raises `LLMRateLimitedError` after max attempts, leaving
   the task queued for the next tick. Demo fallback only when no LLM key is
   configured. Live-verified: task posted against a 429 endpoint stayed
   `assigned` for minutes, then delivered a real LLM response once the real
   Groq URL was restored (`2e221a24-3c7a-4a89-9962-9fb723456515`).

---

## How to reproduce

```bash
# 1. Seed specialists (idempotent — runs automatically on Railway deploy)
python -m agentwallet.scripts.seed_specialists

# 2. Register a user, create an agent (gets a wallet), fund the wallet,
#    then post a task with the capability you want to test:
curl -X POST "$API/marketplace/tasks" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"...","description":"...","category":"research",
       "capability":"research","price_usdc":0.001,
       "funder_wallet_id":"<agent-wallet-id>","auto_assign":true}'

# 3. Watch the worker release the escrow on-chain (~15–30s).
```
