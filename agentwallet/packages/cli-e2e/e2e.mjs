#!/usr/bin/env node
/**
 * aw-e2e — AgentWallet end-to-end testnet test.
 *
 * One command. Full stack. Hacker style.
 *
 *   npx aw-e2e                        # test local stack (http://localhost:8000)
 *   npx aw-e2e --api https://api.agentwallet.fun
 *   node e2e.mjs --api http://localhost:8000 --email you@x.com
 *
 * Zero dependencies. Runs on Node 18+.
 */

const API_URL = (process.argv.find((a) => a.startsWith("--api=")) || "").split("=")[1]
  || process.env.AGW_API_URL
  || "http://localhost:8000";

// ── ANSI / hacker palette ──────────────────────────────────────────────
const C = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  blink: "\x1b[5m",
  green: "\x1b[38;5;82m",
  cyan: "\x1b[38;5;51m",
  yellow: "\x1b[38;5;226m",
  red: "\x1b[38;5;196m",
  magenta: "\x1b[38;5;201m",
  orange: "\x1b[38;5;208m",
  gray: "\x1b[38;5;245m",
  bgBlack: "\x1b[40m",
};

const now = () => new Date().toISOString().slice(11, 19);

function log(line = "") {
  console.log(line);
}

function info(msg) {
  log(`${C.cyan}[${now()}]${C.reset} ${C.dim}::${C.reset} ${msg}`);
}

function ok(label, detail = "") {
  const pad = " ".repeat(Math.max(1, 52 - label.length));
  log(`  ${C.green}${C.bold}✔ PASS${C.reset}  ${C.bold}${label}${C.reset}${pad}${detail ? `${C.green}${detail}${C.reset}` : ""}`);
}

function warn(label, detail = "") {
  const pad = " ".repeat(Math.max(1, 52 - label.length));
  log(`  ${C.yellow}${C.bold}⚠ SKIP${C.reset}  ${C.bold}${label}${C.reset}${pad}${detail ? `${C.yellow}${detail}${C.reset}` : ""}`);
}

function fail(label, detail = "") {
  const pad = " ".repeat(Math.max(1, 52 - label.length));
  log(`  ${C.red}${C.bold}✘ FAIL${C.reset}  ${C.bold}${label}${C.reset}${pad}${detail ? `${C.red}${detail}${C.reset}` : ""}`);
}

function banner() {
  log(``);
  // ── AGENT ──
  log(`${C.green}${C.bold}   █████╗  ██████╗ ███████╗███╗   ██╗████████╗${C.reset}`);
  log(`${C.green}${C.bold}  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝${C.reset}`);
  log(`${C.cyan}${C.bold}  ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ${C.reset}`);
  log(`${C.cyan}${C.bold}  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ${C.reset}`);
  log(`${C.magenta}${C.bold}  ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ${C.reset}`);
  log(`${C.magenta}${C.bold}  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ${C.reset}`);
  // ── GENESIS ──
  log(`${C.green}${C.bold}   ██████╗ ███████╗███╗   ██╗███████╗███████╗██╗███████╗${C.reset}`);
  log(`${C.green}${C.bold}  ██╔════╝ ██╔════╝████╗  ██║██╔════╝██╔════╝██║██╔════╝${C.reset}`);
  log(`${C.cyan}${C.bold}  ██║  ███╗█████╗  ██╔██╗ ██║█████╗  ███████╗██║███████╗${C.reset}`);
  log(`${C.cyan}${C.bold}  ██║   ██║██╔══╝  ██║╚██╗██║██╔══╝  ╚════██║██║╚════██║${C.reset}`);
  log(`${C.magenta}${C.bold}  ╚██████╔╝███████╗██║ ╚████║███████╗███████║██║███████║${C.reset}`);
  log(`${C.magenta}${C.bold}   ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝╚══════╝${C.reset}`);
  log(``);
  log(`  ${C.magenta}${C.bold}  E N D - T O - E N D   T E S T N E T   T E S T${C.reset}`);
  log(`  ${C.gray}┌─────────────────────────────────────────────────────────────┐${C.reset}`);
  log(`  ${C.gray}│${C.reset}  target   : ${C.cyan}${API_URL}${C.reset}`);
  log(`  ${C.gray}│${C.reset}  protocol : ${C.cyan}AgentWallet / Solana${C.reset}`);
  log(`  ${C.gray}│${C.reset}  mode     : ${C.yellow}register → api-key → agent → wallet → escrow → x402 → billing${C.reset}`);
  log(`  ${C.gray}└─────────────────────────────────────────────────────────────┘${C.reset}`);
  log(``);
}

// ── HTTP helper (zero deps, Node 18+ fetch) ───────────────────────────
async function req(method, path, { token, apiKey, body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (apiKey) headers["X-API-Key"] = apiKey;
  const res = await fetch(`${API_URL.replace(/\/$/, "")}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(30000),
  });
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON */ }
  return { status: res.status, data };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ── Main test ─────────────────────────────────────────────────────────
async function main() {
  banner();

  if (process.argv.includes("--dry-run")) {
    info("dry-run — syntax OK, exiting");
    log(``);
    return 0;
  }

  const stamp = Date.now().toString(36);
  const email = `e2e-${stamp}@testnet.agentwallet.fun`;
  const password = "E2ePass!2026";
  const results = { pass: 0, warn: 0, fail: 0 };
  const t = (ok) => { results[ok ? "pass" : "fail"]++; return ok; };
  const tw = () => { results.warn++; };

  // 0 — Health
  info(`probing ${API_URL}/health ...`);
  let healthOk = false;
  try {
    const h = await req("GET", "/health");
    healthOk = h.status === 200 && h.data?.status === "ok";
    t(healthOk) ? ok("API health", `status=${h.data?.status}`) : fail("API health", `HTTP ${h.status}`);
  } catch (e) {
    fail("API health", `cannot reach ${API_URL} (${e.message})`);
    log(`\n  ${C.red}${C.bold}ABORT${C.reset} — AgentWallet API is not reachable.`);
    log(`  ${C.gray}Start the stack first:  docker compose up -d   (or point --api elsewhere)${C.reset}`);
    log(``);
    return 1;
  }
  if (!healthOk) {
    log(`\n  ${C.red}${C.bold}ABORT${C.reset} — health check failed.${C.reset}`);
    log(``);
    return 1;
  }

  // 1 — Register
  info("registering fresh org ...");
  const reg = await req("POST", "/v1/auth/register", {
    body: { org_name: `E2E ${stamp}`, email, password },
  });
  const token = reg.data?.access_token;
  t(reg.status === 201 || reg.status === 200, token) ? ok("register org", email) : fail("register org", `HTTP ${reg.status}`);
  if (!token) { log(``); return 1; }

  // 2 — API key
  info("creating scoped API key ...");
  const keyResp = await req("POST", "/v1/auth/api-keys", {
    token,
    body: { name: "e2e-test", permissions: { wallets: "rw", agents: "rw", escrows: "rw", billing: "rw", x402: "rw" } },
  });
  const apiKey = keyResp.data?.key;
  t(Boolean(apiKey)) ? ok("API key", `${String(apiKey).slice(0, 15)}...`) : fail("API key", `HTTP ${keyResp.status}`);

  // 3 — Agent
  info("creating agent ...");
  const agent = await req("POST", "/v1/agents", {
    apiKey,
    body: { name: "e2e-agent", description: "created by aw-e2e", capabilities: ["analysis", "trading"] },
  });
  const agentId = agent.data?.id;
  t(Boolean(agentId)) ? ok("agent", String(agentId).slice(0, 8)) : fail("agent", `HTTP ${agent.status}`);

  // 4 — Wallets
  info("creating funder + recipient wallets ...");
  let funderId = "", funderAddr = "", recipientId = "", recipientAddr = "";
  if (agentId) {
    const w1 = await req("POST", "/v1/wallets", { apiKey, body: { agent_id: agentId, wallet_type: "agent", label: "E2E Funder" } });
    funderId = w1.data?.id; funderAddr = w1.data?.address;
    t(Boolean(funderAddr)) ? ok("funder wallet", String(funderAddr).slice(0, 12)) : fail("funder wallet", `HTTP ${w1.status}`);
    const w2 = await req("POST", "/v1/wallets", { apiKey, body: { agent_id: agentId, wallet_type: "agent", label: "E2E Recipient" } });
    recipientId = w2.data?.id; recipientAddr = w2.data?.address;
    t(Boolean(recipientAddr)) ? ok("recipient wallet", String(recipientAddr).slice(0, 12)) : fail("recipient wallet", `HTTP ${w2.status}`);
  }

  // 5 — Balance check
  info("checking balances ...");
  if (funderId) {
    const bal = await req("GET", `/v1/wallets/${funderId}/balance`, { apiKey });
    if (bal.status === 200 && bal.data) {
      ok("balance endpoint", `sol=${bal.data.sol_balance ?? "?"}`);
    } else {
      t(false) && fail("balance endpoint", `HTTP ${bal.status}`);
    }
  }

  // 6 — Escrow
  info("creating escrow ...");
  if (funderId && recipientAddr) {
    const esc = await req("POST", "/v1/escrow", {
      apiKey,
      body: { funder_wallet_id: funderId, recipient_address: recipientAddr, amount_sol: 0.05, conditions: { task: "e2e" } },
    });
    const escId = esc.data?.id;
    const escStatus = esc.data?.status;
    t(Boolean(escId)) ? ok("escrow created", `status=${escStatus}`) : fail("escrow created", `HTTP ${esc.status}`);
    if (escId) {
      const got = await req("GET", `/v1/escrow/${escId}`, { apiKey });
      t(got.status === 200) ? ok("escrow fetch by id") : fail("escrow fetch by id");
    }
  } else {
    tw();
    warn("escrow flow", "missing funder wallet / recipient");
  }

  // 7 — Transactions (read path — transfer needs funded SOL)
  info("listing transactions ...");
  const txs = await req("GET", "/v1/transactions", { apiKey });
  t(txs.status === 200) ? ok("transactions list") : fail("transactions list", `HTTP ${txs.status}`);

  // 8 — x402
  info("configuring x402 paywall ...");
  const xcfg = await req("POST", "/v1/x402/configure", {
    apiKey,
    body: {
      pricing: [{ route_pattern: "/agents/*", method: "GET", price_lamports: 100_000, description: "e2e paywall", pay_to: recipientAddr || "11111111111111111111111111111111" }],
      enabled: true, network: "solana-mainnet",
    },
  });
  t(xcfg.status === 200) ? ok("x402 configured", `${xcfg.data?.configured_routes ?? "?"} route(s)`) : fail("x402 configure", `HTTP ${xcfg.status}`);
  const xstatus = await req("GET", "/v1/x402/status", { apiKey });
  t(xstatus.status === 200) ? ok("x402 status", `enabled=${xstatus.data?.enabled}`) : fail("x402 status", `HTTP ${xstatus.status}`);
  // disable again so the stack is left clean
  await req("POST", "/v1/x402/configure", { apiKey, body: { pricing: [], enabled: false } });

  // 9 — Billing
  info("querying billing plans ...");
  const plans = await req("GET", "/v1/billing/plans", { apiKey });
  if (plans.status === 200 && plans.data?.plans) {
    const names = plans.data.plans.map((p) => p.tier).join(", ");
    ok("billing plans", names);
  } else {
    t(false) && fail("billing plans", `HTTP ${plans.status}`);
  }

  // ── Summary ──────────────────────────────────────────────────────────
  log(``);
  log(`  ${C.green}${C.bold}  ═══════════════════════════════════════════════════${C.reset}`);
  log(`  ${C.green}${C.bold}   RESULT: ${results.pass} PASS   ${results.warn} SKIP   ${results.fail} FAIL${C.reset}`);
  log(`  ${C.green}${C.bold}  ═══════════════════════════════════════════════════${C.reset}`);
  if (results.fail === 0) {
    log(`  ${C.green}${C.bold}   [✓] AgentWallet testnet stack is OPERATIONAL.${C.reset}`);
  } else {
    log(`  ${C.red}${C.bold}   [✘] ${results.fail} check(s) failed.${C.reset}`);
  }
  log(``);
  log(`  ${C.gray}  org    : ${email}${C.reset}`);
  if (apiKey) log(`  ${C.gray}  api-key: ${String(apiKey).slice(0, 24)}...${C.reset}`);
  log(``);

  return results.fail === 0 ? 0 : 1;
}

main().then((code) => process.exit(code)).catch((e) => {
  console.error(`\n  ${C.red}${C.bold}FATAL${C.reset} ${e.message}\n`);
  process.exit(1);
});
