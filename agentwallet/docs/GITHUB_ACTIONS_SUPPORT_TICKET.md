# GitHub Support Ticket — Actions has been disabled for this user

> **How to submit:** https://support.github.com → **Contact support** → *Billing /
> Account / Abuse* → **"I need help with my account"**. Paste everything below.
> Also add a screen recording of the failing `workflow_dispatch` (shows the
> exact 422) — support replies faster with visual proof.

---

**Subject:** [Account] Actions has been disabled for this user — HTTP 422 on
workflow dispatch & push, no email notice

**Account:** `@ChiranjibAI` (Chiranjib) · created 2026-02-19 · free plan,
personal user account (no org)

**Primary repo affected:** `ChiranjibAI/agent-genesis` (public)

**Date first noticed:** 2026-08-15 (Actions stopped accepting new runs around
10:26 UTC; last successful run 10:26 UTC, nothing since)

---

## Summary

Starting 2026-08-15, GitHub Actions on my account stopped accepting **any**
new workflow runs — neither push-triggered nor `workflow_dispatch`. Every
attempt returns:

```
could not create workflow dispatch event: HTTP 422: Actions has been disabled
for this user.
(https://api.github.com/repos/ChiranjibAI/agent-genesis/actions/workflows/333241242/dispatches)
```

The same happens for push events: commits to `master` that previously
triggered workflows now produce **zero** runs (`/actions/runs` returns no entry
for the new head SHA). This is blocking my automated CI/CD entirely.

## What I already verified

1. **Repo-level Actions is enabled** — `GET /repos/ChiranjibAI/agent-genesis/actions/permissions`
   returns `{"allowed_actions": "all", "enabled": true}`.
2. **Workflows exist and are valid** — 7 workflows under `.github/workflows/`
   (CI, Devnet Lifecycle, Smoke Test, Agent Genesis, CodeQL, Docker, Vercel
   deploy). They ran fine for months; last successful run 2026-08-15 10:26 UTC.
3. **Not a repo-specific issue** — the 422 message says *"disabled for this
   user"* and occurs for **every** repo I own (tried `agent-genesis`,
   `OpenSignalAI`, `agent-eye`).
4. **Manual dispatch fails too** — `gh workflow run ci.yml --ref master`
   → HTTP 422 (so it is not a push-filter misconfiguration).
5. **Token is valid** — `gh auth status` OK; API calls succeed (only Actions
   dispatch returns 422).
6. **Billing** — personal free account; `GET /user/settings/billing/actions`
   returns 404 (no org billing object), and I have not exceeded any usage
   quota I'm aware of.

## Impact

- No CI on any of my repos: tests, lint, security scans, and deployment
  workflows all stopped on 2026-08-15.
- Production deploys (Railway + Vercel) are blocked in CI; I am manually
  deploying as a workaround.
- I have 5+ active public repos (agent-genesis, OpenSignalAI, agent-eye,
  chiranjib-xyz-react, agent-genesis-framework) and several contributors.

## What I'm asking for

1. Confirm whether this account was flagged / Actions was disabled, and why.
2. If it's a policy/abuse flag, please review — I have received **no email or
   notification** explaining the block, and to my knowledge nothing in my
   usage violates the GitHub Acceptable Use Policy (all repos are legitimate
   open-source software projects).
3. Restore Actions for `@ChiranjibAI` so push + `workflow_dispatch` trigger
   runs again, or tell me exactly what I need to do to resolve it.

## Environment

| Field | Value |
|---|---|
| Account | `@ChiranjibAI` (user, free plan) |
| Created | 2026-02-19 |
| Affected since | 2026-08-15 ~10:26 UTC |
| Last successful run | 2026-08-15 10:26 UTC (`233f651`) |
| Repo | `ChiranjibAI/agent-genesis` (public) |
| API error | HTTP 422 "Actions has been disabled for this user" |
| Repo permissions API | `{"allowed_actions":"all","enabled":true}` |
| Billing API | 404 (no org billing) |
| Email notice received | None |

---

*Timeline of last runs (all completed, then silence):*
- 2026-08-15 10:26 UTC — CI ✅ / Devnet Lifecycle ✅ / Smoke ❌ (pre-existing flake) / CodeQL ✅ — head `233f651`
- 2026-08-15 10:22 UTC — Devnet Lifecycle — head `8df710c`
- After that: every push (heads `237fd77`, `8d64fb2`, `aac61cc`, `b065441`) → **no runs created**
