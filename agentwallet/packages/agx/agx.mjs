#!/usr/bin/env node
/**
 * AGX — Agent Genesis terminal agent.
 *
 * Claude Code-style AI agent that runs on top of AgentWallet's Solana
 * wallet infrastructure. You bring the API provider (Anthropic-compatible
 * or OpenAI-compatible), the agent brings its own wallet.
 *
 *   export AGX_API_KEY=sk-ant-...          # or AGX_API_BASE + AGX_API_KEY
 *   node agx.mjs
 *
 *   # pay-per-use mode (x402): pay for each API request on-chain
 *   AGX_PAY_PER_USE=1 node agx.mjs
 *
 * Zero dependencies. Node 18+.
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline from "node:readline";
import { spawn } from "node:child_process";

// ── Config ────────────────────────────────────────────────────────────
const cfg = {
  apiBase: process.env.AGX_API_BASE || "https://api.anthropic.com",
  apiKey: process.env.AGX_API_KEY || process.env.ANTHROPIC_API_KEY || "",
  apiFormat: (process.env.AGX_API_FORMAT || "anthropic").toLowerCase(), // anthropic | openai
  model: process.env.AGX_MODEL || (process.env.AGX_API_FORMAT === "openai" ? "gpt-4o" : "claude-sonnet-4-5"),
  agwUrl: process.env.AGW_API_URL || "http://localhost:8000",
  payPerUse: process.env.AGX_PAY_PER_USE === "1" || process.env.AGX_PAY_PER_USE === "true",
  maxTurns: parseInt(process.env.AGX_MAX_TOOL_TURNS || "12", 10),
  system: process.env.AGX_SYSTEM
    || "You are AGX, an AI software engineering agent running on Solana with your own crypto wallet. "
    + "You write code, edit files, and run commands — and you can transact on-chain: check your wallet "
    + "balance, send SOL, create escrows, and pay for API access. Be concise and precise. "
    + "When the user asks you to do work, use your tools.",
  identityPath: process.env.AGX_IDENTITY || path.join(os.homedir(), ".agx", "identity.json"),
};

// ── ANSI palette (hacker) ─────────────────────────────────────────────
const C = {
  reset: "\x1b[0m", bold: "\x1b[1m", dim: "\x1b[2m",
  green: "\x1b[38;5;82m", cyan: "\x1b[38;5;51m", yellow: "\x1b[38;5;226m",
  red: "\x1b[38;5;196m", magenta: "\x1b[38;5;201m", orange: "\x1b[38;5;208m", gray: "\x1b[38;5;245m",
};

const log = (s = "") => console.log(s);

// ── Identity (wallet) ─────────────────────────────────────────────────
let identity = null;

function loadIdentity() {
  try { identity = JSON.parse(fs.readFileSync(cfg.identityPath, "utf8")); } catch { identity = null; }
}

function saveIdentity() {
  fs.mkdirSync(path.dirname(cfg.identityPath), { recursive: true });
  fs.writeFileSync(cfg.identityPath, JSON.stringify(identity, null, 2), { mode: 0o600 });
}

async function agwReq(method, p, { token, apiKey, body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (apiKey) headers["X-API-Key"] = apiKey;
  const res = await fetch(`${cfg.agwUrl.replace(/\/$/, "")}${p}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(30000),
  });
  let data = null;
  try { data = await res.json(); } catch {}
  return { status: res.status, data };
}

async function ensureIdentity() {
  loadIdentity();
  if (identity?.apiKey && identity?.walletId) {
    // Probe wallet still valid
    const b = await agwReq("GET", `/v1/wallets/${identity.walletId}/balance`, { apiKey: identity.apiKey });
    if (b.status === 200) return identity;
    identity = null;
  }

  log(`  ${C.yellow}[!]${C.reset} no wallet identity found — registering a fresh agent on-chain...`);
  const stamp = Date.now().toString(36);
  const email = `agx-${stamp}@genesis.agent`;
  const password = `Agx!${stamp}Xz9`;

  const reg = await agwReq("POST", "/v1/auth/register", {
    body: { org_name: `AGX ${stamp}`, email, password },
  });
  if (reg.status !== 200 && reg.status !== 201) {
    throw new Error(`AgentWallet register failed (HTTP ${reg.status}): ${JSON.stringify(reg.data)}`);
  }
  const token = reg.data.access_token;

  const keyResp = await agwReq("POST", "/v1/auth/api-keys", {
    token,
    body: { name: "agx-agent", permissions: { wallets: "rw", agents: "rw", escrows: "rw", x402: "rw" } },
  });
  if (!keyResp.data?.key) throw new Error(`AgentWallet API key failed: ${JSON.stringify(keyResp.data)}`);
  const apiKey = keyResp.data.key;

  const agent = await agwReq("POST", "/v1/agents", {
    apiKey,
    body: { name: `AGX ${stamp}`, description: "Agent Genesis terminal agent", capabilities: ["coding", "analysis"] },
  });
  const agentId = agent.data?.id;
  if (!agentId) throw new Error(`Agent creation failed: ${JSON.stringify(agent.data)}`);

  const wallet = await agwReq("POST", "/v1/wallets", {
    apiKey,
    body: { agent_id: agentId, wallet_type: "agent", label: "AGX Wallet" },
  });
  const walletId = wallet.data?.id;
  const address = wallet.data?.address;
  if (!walletId) throw new Error(`Wallet creation failed: ${JSON.stringify(wallet.data)}`);

  identity = { email, orgId: reg.data.org_id, apiKey, agentId, walletId, address };
  saveIdentity();
  return identity;
}

async function getBalance() {
  const b = await agwReq("GET", `/v1/wallets/${identity.walletId}/balance`, { apiKey: identity.apiKey });
  if (b.status !== 200) return null;
  return b.data;
}

// ── x402 pay-per-use ──────────────────────────────────────────────────
async function payAndRetry(method, url, headers, body, amount) {
  // Parse 402 accepts, pay via wallet, retry with X-PAYMENT header.
  if (!identity) await ensureIdentity();
  const accept = amount?.accepts?.[0];
  if (!accept) throw new Error("402 response had no acceptable payment methods");
  const payTo = accept.payTo || accept.pay_to;
  const rawAmount = accept.amount || accept.maxAmountRequired;
  if (!payTo || !rawAmount) throw new Error("Payment requirement missing pay_to/amount");

  const token = (accept.tokenSymbol || accept.token || "SOL").toUpperCase();
  let tx;
  if (token === "SOL") {
    tx = await agwReq("POST", "/v1/transactions/transfer-sol", {
      apiKey: identity.apiKey,
      body: { from_wallet_id: identity.walletId, to_address: payTo, amount_sol: Number(rawAmount) / 1e9 },
    });
  } else {
    tx = await agwReq("POST", "/v1/tokens/transfer", {
      apiKey: identity.apiKey,
      body: { from_wallet_id: identity.walletId, to_address: payTo, token_symbol: token, amount: Number(rawAmount) / 1e6 },
    });
  }
  if (!tx.data?.signature) throw new Error(`x402 payment failed: ${JSON.stringify(tx.data)}`);
  log(`  ${C.green}[pay]${C.reset} ${token} ${Number(rawAmount) / 1e9} → ${payTo.slice(0, 8)}…  ${C.dim}${tx.data.signature.slice(0, 16)}…${C.reset}`);

  const proof = Buffer.from(JSON.stringify({
    payload: { signature: tx.data.signature, amount: String(rawAmount), timestamp: Math.floor(Date.now() / 1000) },
  })).toString("base64");

  const retry = await fetch(url, { method, headers: { ...headers, "X-PAYMENT": proof }, body: body ? JSON.stringify(body) : undefined });
  return retry;
}

// ── Tool definitions ──────────────────────────────────────────────────
const toolDefs = [
  {
    name: "read_file",
    description: "Read a file from disk. Pass the full path.",
    input_schema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] },
  },
  {
    name: "write_file",
    description: "Create or overwrite a file with the given content.",
    input_schema: { type: "object", properties: { path: { type: "string" }, content: { type: "string" } }, required: ["path", "content"] },
  },
  {
    name: "run_command",
    description: "Run a shell command. Pass the command string. May be long-running.",
    input_schema: { type: "object", properties: { command: { type: "string" } }, required: ["command"] },
  },
  {
    name: "wallet_balance",
    description: "Get the agent's Solana wallet balance (SOL + tokens).",
    input_schema: { type: "object", properties: {} },
  },
  {
    name: "send_sol",
    description: "Send SOL from the agent's wallet to any Solana address.",
    input_schema: { type: "object", properties: { to_address: { type: "string" }, amount_sol: { type: "number" } }, required: ["to_address", "amount_sol"] },
  },
  {
    name: "create_escrow",
    description: "Lock funds in escrow payable to a recipient when work completes.",
    input_schema: { type: "object", properties: { recipient_address: { type: "string" }, amount_sol: { type: "number" }, task: { type: "string" } }, required: ["recipient_address", "amount_sol"] },
  },
  {
    name: "create_agent",
    description: "Create a new agent in your org (returns its id).",
    input_schema: { type: "object", properties: { name: { type: "string" }, description: { type: "string" } }, required: ["name"] },
  },
  {
    name: "create_swarm",
    description: "Create an agent swarm; the AGX agent is the orchestrator.",
    input_schema: { type: "object", properties: { name: { type: "string" }, description: { type: "string" } }, required: ["name", "description"] },
  },
  {
    name: "swarm_add_member",
    description: "Add an agent as a member of a swarm.",
    input_schema: { type: "object", properties: { swarm_id: { type: "string" }, agent_id: { type: "string" }, role: { type: "string" } }, required: ["swarm_id", "agent_id"] },
  },
  {
    name: "create_swarm_task",
    description: "Create a task in a swarm.",
    input_schema: { type: "object", properties: { swarm_id: { type: "string" }, title: { type: "string" }, description: { type: "string" } }, required: ["swarm_id", "title", "description"] },
  },
  {
    name: "create_acp_job",
    description: "Create an ACP job (agent-to-agent commerce) between two agents, priced in USDC.",
    input_schema: { type: "object", properties: { title: { type: "string" }, description: { type: "string" }, buyer_agent_id: { type: "string" }, seller_agent_id: { type: "string" }, price_usdc: { type: "number" } }, required: ["title", "description", "buyer_agent_id", "seller_agent_id", "price_usdc"] },
  },
  {
    name: "genesis_design",
    description: "Design an Agent Genesis organization from a task description. Returns the org spec (id, agents with roles/runtimes, topology).",
    input_schema: { type: "object", properties: { task: { type: "string" } }, required: ["task"] },
  },
  {
    name: "genesis_deploy",
    description: "Deploy a previously designed Agent Genesis organization to its target runtimes.",
    input_schema: { type: "object", properties: { org_id: { type: "string" } }, required: ["org_id"] },
  },
  {
    name: "genesis_orgs",
    description: "List Agent Genesis organizations saved in memory (design results are persisted).",
    input_schema: { type: "object", properties: {} },
  },
];

async function runTool(name, args) {
  switch (name) {
    case "read_file": {
      try { return { ok: true, content: fs.readFileSync(args.path, "utf8") }; }
      catch (e) { return { ok: false, error: e.message }; }
    }
    case "write_file": {
      try {
        fs.mkdirSync(path.dirname(args.path), { recursive: true });
        fs.writeFileSync(args.path, args.content);
        return { ok: true, wrote: args.path };
      } catch (e) { return { ok: false, error: e.message }; }
    }
    case "run_command":
      return runCommand(args.command);
    case "wallet_balance": {
      const b = await getBalance();
      return b ? { ok: true, ...b } : { ok: false, error: "wallet balance unavailable" };
    }
    case "send_sol": {
      const tx = await agwReq("POST", "/v1/transactions/transfer-sol", {
        apiKey: identity.apiKey,
        body: { from_wallet_id: identity.walletId, to_address: args.to_address, amount_sol: args.amount_sol },
      });
      return tx.data ? { ok: tx.status < 400, tx: tx.data } : { ok: false, error: `HTTP ${tx.status}` };
    }
    case "create_escrow": {
      const esc = await agwReq("POST", "/v1/escrow", {
        apiKey: identity.apiKey,
        body: { funder_wallet_id: identity.walletId, recipient_address: args.recipient_address, amount_sol: args.amount_sol, conditions: { task: args.task || "agx task" } },
      });
      return esc.data ? { ok: esc.status < 400, escrow: esc.data } : { ok: false, error: `HTTP ${esc.status}` };
    }
    case "create_agent": {
      const r = await agwReq("POST", "/v1/agents", {
        apiKey: identity.apiKey,
        body: { name: args.name, description: args.description || "AGX-created agent", capabilities: ["general"] },
      });
      return r.data ? { ok: r.status < 400, agent: r.data } : { ok: false, error: `HTTP ${r.status}: ${JSON.stringify(r.data)}` };
    }
    case "create_swarm": {
      const r = await agwReq("POST", "/v1/swarms", {
        apiKey: identity.apiKey,
        body: { name: args.name, description: args.description, orchestrator_agent_id: identity.agentId, swarm_type: "general", max_members: 10 },
      });
      return r.data ? { ok: r.status < 400, swarm: r.data } : { ok: false, error: `HTTP ${r.status}: ${JSON.stringify(r.data)}` };
    }
    case "swarm_add_member": {
      const r = await agwReq("POST", `/v1/swarms/${args.swarm_id}/members`, {
        apiKey: identity.apiKey,
        body: { agent_id: args.agent_id, role: args.role || "worker" },
      });
      return r.data ? { ok: r.status < 400, member: r.data } : { ok: false, error: `HTTP ${r.status}: ${JSON.stringify(r.data)}` };
    }
    case "create_swarm_task": {
      const r = await agwReq("POST", `/v1/swarms/${args.swarm_id}/tasks`, {
        apiKey: identity.apiKey,
        body: { title: args.title, description: args.description },
      });
      return r.data ? { ok: r.status < 400, task: r.data } : { ok: false, error: `HTTP ${r.status}: ${JSON.stringify(r.data)}` };
    }
    case "create_acp_job": {
      const r = await agwReq("POST", "/v1/acp/jobs", {
        apiKey: identity.apiKey,
        body: { title: args.title, description: args.description, buyer_agent_id: args.buyer_agent_id, seller_agent_id: args.seller_agent_id, price_usdc: args.price_usdc },
      });
      return r.data ? { ok: r.status < 400, job: r.data } : { ok: false, error: `HTTP ${r.status}: ${JSON.stringify(r.data)}` };
    }
    case "genesis_design":
      return runGenesis(["design", args.task]);
    case "genesis_deploy":
      return runGenesis(["deploy", args.org_id]);
    case "genesis_orgs":
      return runGenesis(["orgs"]);
    default:
      return { ok: false, error: `unknown tool: ${name}` };
  }
}

function execShell(command, resolve) {
  const proc = spawn(command, { shell: true, stdio: ["ignore", "pipe", "pipe"] });
  let out = "", err = "";
  proc.stdout.on("data", (d) => { out += d; process.stdout.write(C.dim + d + C.reset); });
  proc.stderr.on("data", (d) => { err += d; process.stdout.write(C.orange + d + C.reset); });
  proc.on("close", (code) => resolve({ ok: code === 0, exit_code: code, stdout: out, stderr: err }));
}

function runCommand(command) {
  return new Promise((resolve) => {
    const autoApprove = process.env.AGX_AUTORUN === "1" || !process.stdin.isTTY;
    if (autoApprove) {
      log(`  ${C.yellow}[?]${C.reset} run: ${C.cyan}${command}${C.reset}  ${C.dim}(auto-approved: non-interactive)${C.reset}`);
      execShell(command, resolve);
      return;
    }
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(`  ${C.yellow}[?]${C.reset} run: ${C.cyan}${command}${C.reset}  ${C.dim}(y/N)${C.reset} `, (ans) => {
      rl.close();
      if (!/^y/i.test(ans.trim())) { resolve({ ok: false, cancelled: true }); return; }
      execShell(command, resolve);
    });
  });
}

// ── Agent Genesis CLI integration ─────────────────────────────────────
// Runs the `genesis` command (installed via `pip install -e agent_genesis`)
// and parses its JSON output. Falls back to `python -m agent_genesis.cli.genesis`
// when the console script is missing from PATH.
function runGenesis(args, timeoutMs = 120000) {
  return new Promise((resolve) => {
    const py = process.platform === "win32" ? "python" : "python3";
    const candidates = [
      { cmd: "genesis", args },
      { cmd: py, args: ["-m", "agent_genesis.cli.genesis", ...args] },
    ];
    let idx = 0;
    let done = false;
    const finish = (result) => { if (!done) { done = true; resolve(result); } };
    const attempt = () => {
      if (done) return;
      if (idx >= candidates.length) {
        finish({ ok: false, error: "genesis CLI not found — install it with: cd agent_genesis && pip install -e ." });
        return;
      }
      const { cmd, args: cargs } = candidates[idx++];
      let attemptDone = false;
      let started = false;
      const proc = spawn(cmd, cargs, { stdio: ["ignore", "pipe", "pipe"] });
      let out = "", err = "";
      const timer = setTimeout(() => {
        proc.kill();
        finish({ ok: false, error: `genesis timed out after ${timeoutMs / 1000}s`, stdout: out, stderr: err });
      }, timeoutMs);
      const settle = (result) => {
        if (attemptDone) return;
        attemptDone = true;
        clearTimeout(timer);
        finish(result);
      };
      proc.on("spawn", () => { started = true; });
      // ENOENT / spawn failure (binary missing) -> try the python -m fallback
      const skipToFallback = () => {
        if (attemptDone) return;
        attemptDone = true;
        clearTimeout(timer);
        attempt();
      };
      proc.on("error", () => { if (!started) skipToFallback(); else settle({ ok: false, error: err.trim() || `failed to start ${cmd}` }); });
      proc.stdout.on("data", (d) => { out += d; });
      proc.stderr.on("data", (d) => { err += d; });
      proc.on("close", (code) => {
        if (!started) { skipToFallback(); return; }
        if (code !== 0) {
          settle({ ok: false, exit_code: code, error: err.trim() || `genesis exited with ${code}`, stdout: out });
          return;
        }
        const text = out.trim();
        try {
          settle({ ok: true, ...JSON.parse(text) });
        } catch {
          settle({ ok: true, raw: text });
        }
      });
    };
    attempt();
  });
}

// ── LLM clients (streaming) ───────────────────────────────────────────
async function* streamAnthropic(messages) {
  const body = {
    model: cfg.model,
    max_tokens: 4096,
    system: cfg.system,
    messages,
    tools: toolDefs,
    stream: true,
  };
  const res = await fetch(`${cfg.apiBase.replace(/\/$/, "")}/v1/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": cfg.apiKey, "anthropic-version": "2023-06-01" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(120000),
  });
  if (res.status === 402) {
    const err = await res.json();
    yield { type: "payment_required", data: err };
    return;
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text.slice(0, 500)}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentBlock = null;

  function* flushBlock() {
    if (currentBlock) { yield { type: "content_block_stop", data: currentBlock }; currentBlock = null; }
  }

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith("data:")) continue;
      const payload = t.slice(5).trim();
      if (payload === "[DONE]") continue;
      let ev;
      try { ev = JSON.parse(payload); } catch { continue; }
      switch (ev.type) {
        case "content_block_start":
          currentBlock = {
            index: ev.index,
            type: ev.content_block.type,
            text: "",
            name: ev.content_block.name || "",
            input: "",
            toolCallId: ev.content_block.id || `toolu_${ev.index}_${Date.now()}`,
          };
          break;
        case "content_block_delta":
          if (!currentBlock) break;
          if (ev.delta.type === "text_delta") currentBlock.text += ev.delta.text;
          if (ev.delta.type === "input_json_delta") currentBlock.input += ev.delta.partial_json;
          yield { type: "delta", data: { block_index: ev.index, kind: currentBlock.type, text: ev.delta.type === "text_delta" ? ev.delta.text : "" } };
          break;
        case "content_block_stop":
          yield* flushBlock();
          break;
        case "message_stop":
          yield* flushBlock();
          break;
      }
    }
  }
  yield* flushBlock();
}

async function* streamOpenAI(messages) {
  // Convert tool defs to OpenAI format
  const tools = toolDefs.map((t) => ({ type: "function", function: { name: t.name, description: t.description, parameters: t.input_schema } }));
  const body = { model: cfg.model, messages, tools, stream: true };
  const res = await fetch(`${cfg.apiBase.replace(/\/$/, "")}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${cfg.apiKey}` },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(120000),
  });
  if (res.status === 402) {
    const err = await res.json();
    yield { type: "payment_required", data: err };
    return;
  }
  if (!res.ok) { const t = await res.text(); throw new Error(`API error ${res.status}: ${t.slice(0, 500)}`); }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const toolCalls = new Map(); // index -> {id, name} (OpenAI repeats these only on first chunk)
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith("data:")) continue;
      const payload = t.slice(5).trim();
      if (payload === "[DONE]") continue;
      let ev;
      try { ev = JSON.parse(payload); } catch { continue; }
      const d = ev.choices?.[0]?.delta;
      if (!d) continue;
      if (d.content) yield { type: "delta", data: { kind: "text", text: d.content } };
      if (d.tool_calls?.[0]) {
        const tc = d.tool_calls[0];
        const idx = tc.index ?? 0;
        const prev = toolCalls.get(idx) || {};
        const id = tc.id || prev.id;
        const name = tc.function?.name || prev.name;
        toolCalls.set(idx, { id, name });
        yield { type: "tool_call", data: { index: idx, id, name, arguments: tc.function?.arguments || "" } };
      }
    }
  }
}

// ── Conversation helpers ──────────────────────────────────────────────
// Convert the internal conversation (Anthropic-style content blocks:
// assistant {type:"tool_use"} + user {type:"tool_result"}) into the wire
// format the provider expects. OpenAI needs tool_calls on the assistant
// message and a separate role:"tool" message per tool result.
function wireMessages(msgs) {
  if (cfg.apiFormat !== "openai") return msgs;
  const out = [];
  for (const m of msgs) {
    if (!Array.isArray(m.content)) { out.push({ role: m.role, content: m.content }); continue; }
    const text = m.content.filter((b) => b.type === "text").map((b) => b.text).join("");
    if (m.role === "assistant") {
      const toolCalls = m.content
        .filter((b) => b.type === "tool_use")
        .map((b) => ({ id: b.id, type: "function", function: { name: b.name, arguments: JSON.stringify(b.input ?? {}) } }));
      if (toolCalls.length) out.push({ role: "assistant", content: text || null, tool_calls: toolCalls });
      else out.push({ role: "assistant", content: text });
    } else if (m.role === "user") {
      const results = m.content.filter((b) => b.type === "tool_result");
      if (results.length) {
        // drop the wrapper; emit one role:"tool" message per result
        for (const r of results) out.push({ role: "tool", tool_call_id: r.tool_use_id, content: r.content });
      } else {
        out.push({ role: "user", content: text });
      }
    } else {
      out.push({ role: m.role, content: text });
    }
  }
  return out;
}

// ── Main REPL ─────────────────────────────────────────────────────────
function banner() {
  log("");
  log(`${C.green}${C.bold}   █████╗  ██████╗ ███████╗███╗   ██╗████████╗${C.reset}`);
  log(`${C.green}${C.bold}  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝${C.reset}`);
  log(`${C.cyan}${C.bold}  ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ${C.reset}`);
  log(`${C.cyan}${C.bold}  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ${C.reset}`);
  log(`${C.magenta}${C.bold}  ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ${C.reset}`);
  log(`${C.magenta}${C.bold}  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ${C.reset}`);
  log(`${C.green}${C.bold}   ██████╗ ███████╗███╗   ██╗███████╗███████╗██╗███████╗${C.reset}`);
  log(`${C.green}${C.bold}  ██╔════╝ ██╔════╝████╗  ██║██╔════╝██╔════╝██║██╔════╝${C.reset}`);
  log(`${C.cyan}${C.bold}  ██║  ███╗█████╗  ██╔██╗ ██║█████╗  ███████╗██║███████╗${C.reset}`);
  log(`${C.cyan}${C.bold}  ██║   ██║██╔══╝  ██║╚██╗██║██╔══╝  ╚════██║██║╚════██║${C.reset}`);
  log(`${C.magenta}${C.bold}  ╚██████╔╝███████╗██║ ╚████║███████╗███████║██║███████║${C.reset}`);
  log(`${C.magenta}${C.bold}   ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝╚══════╝${C.reset}`);
  log("");
  log(`  ${C.magenta}${C.bold}  D E C E N T R A L I Z E D   T E R M I N A L   A G E N T${C.reset}`);
  log(`  ${C.gray}┌────────────────────────────────────────────────────────────────┐${C.reset}`);
  log(`  ${C.gray}│${C.reset}  model   : ${C.cyan}${cfg.model}${C.reset}`);
  log(`  ${C.gray}│${C.reset}  api     : ${C.cyan}${cfg.apiBase}${C.reset}  (${cfg.apiFormat})`);
  log(`  ${C.gray}│${C.reset}  wallet  : ${C.yellow}${cfg.payPerUse ? "pay-per-use (x402)" : "on-chain" + ""}${C.reset}`);
  log(`  ${C.gray}└────────────────────────────────────────────────────────────────┘${C.reset}`);
  log("");
}

const helpText = `
  ${C.green}/help${C.reset}        show this help
  ${C.green}/wallet${C.reset}      show wallet identity + balance
  ${C.green}/pay${C.reset}         toggle pay-per-use (x402) mode
  ${C.green}/model <name>${C.reset}  switch model
  ${C.green}/quit${C.reset}        exit
`;

function printToolHeader(name, args) {
  const summary = name === "run_command" ? args.command
    : name === "read_file" ? args.path
    : name === "write_file" ? `${args.path} (${(args.content || "").length}b)`
    : name === "send_sol" ? `${args.amount_sol} SOL → ${args.to_address?.slice(0, 8)}…`
    : name === "create_escrow" ? `${args.amount_sol} SOL escrow → ${args.recipient_address?.slice(0, 8)}…`
    : name === "create_agent" ? args.name
    : name === "create_swarm" ? args.name
    : name === "swarm_add_member" ? `${args.agent_id?.slice(0, 8)}… as ${args.role || "worker"}`
    : name === "create_swarm_task" ? args.title
    : name === "create_acp_job" ? `${args.title} (${args.price_usdc} USDC)`
    : "";
  log(`  ${C.cyan}[tool]${C.reset} ${C.bold}${name}${C.reset} ${C.dim}${summary}${C.reset}`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Hacker boot sequence — runs once at startup.
function bootSequence() {
  const steps = [
    ["INITIALIZING AGENT GENESIS OS", C.cyan],
    ["MOUNTING SOLANA WALLET MODULE", C.green],
    ["ESTABLISHING ON-CHAIN IDENTITY", C.magenta],
    ["LOADING TOOLKIT  [read_file, write_file, run_command, wallet_balance, send_sol, create_escrow]", C.gray],
    ["LOADING TOOLKIT+ [create_agent, create_swarm, swarm_add_member, create_swarm_task, create_acp_job]", C.gray],
    ["LOADING TOOLKIT++ [genesis_design, genesis_deploy, genesis_orgs]", C.gray],
    ["ARMING X402 PAYMENT RAIL", C.yellow],
    ["AGENT ONLINE", C.green],
  ];
  for (const [text, color] of steps) {
    log(`  ${C.dim}[${color}●${C.reset}${C.dim}]${C.reset} ${color}${text}${C.reset}`);
    if (isTTY) { const until = Date.now() + 90; while (Date.now() < until); }
  }
  log("");
}

async function chat(rl, messages) {
  let turns = 0;
  for (;;) {
    if (++turns > cfg.maxTurns) { log(`  ${C.yellow}[!]${C.reset} max tool turns reached, stopping`); break; }

    let assistantText = "";
    let blocks = []; // {index, type, text, name, input, toolCallId}
    let paymentRequired = null;

    log(`  ${C.dim}▸ ${cfg.model}${C.reset}`);
    const streamFn = cfg.apiFormat === "openai" ? streamOpenAI : streamAnthropic;
    let spinner = null;
    if (isTTY) {
      const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
      let i = 0;
      spinner = setInterval(() => {
        process.stdout.write(`\r  ${C.cyan}${frames[i++ % frames.length]}${C.reset} ${C.dim}thinking${C.reset}`);
      }, 80);
    }
    let firstChunk = true;
    for await (const ev of streamFn(wireMessages(messages))) {
      if (firstChunk && spinner) { clearInterval(spinner); spinner = null; process.stdout.write("\r\x1b[K"); }
      firstChunk = false;
      if (ev.type === "payment_required") { paymentRequired = ev.data; break; }
      if (ev.type === "delta" && ev.data.kind === "text") {
        process.stdout.write(ev.data.text);
        assistantText += ev.data.text;
      }
      if (ev.type === "tool_call") {
        let b = blocks.find((x) => x.index === ev.data.index);
        if (!b) {
          b = { index: ev.data.index, toolCallId: ev.data.id, name: ev.data.name || "", args: "" };
          blocks.push(b);
        }
        if (ev.data.id) b.toolCallId = ev.data.id;
        if (ev.data.name) b.name = ev.data.name;
        if (ev.data.arguments) b.args += ev.data.arguments;
      }
      if (ev.type === "content_block_stop" && ev.data?.type === "tool_use") {
        let b = blocks.find((x) => x.index === ev.data.index);
        if (!b) {
          b = { index: ev.data.index, type: "tool_use", name: ev.data.name || "", args: "" };
          blocks.push(b);
        }
        b.name = ev.data.name || b.name;
        b.args = ev.data.input || b.args;
      }
    }
    if (spinner) { clearInterval(spinner); spinner = null; process.stdout.write("\r\x1b[K"); }

    if (paymentRequired) {
      if (!cfg.payPerUse) {
        log(`\n  ${C.red}[402]${C.reset} this API requires on-chain payment. Enable pay-per-use:`);
        log(`  ${C.yellow}   /pay${C.reset}   (or AGX_PAY_PER_USE=1)`);
        return;
      }
      log(`\n  ${C.yellow}[402]${C.reset} paying per-use on-chain...`);
      // Re-run with payAndRetry by building a non-stream request
      const body = cfg.apiFormat === "openai"
        ? { model: cfg.model, messages: wireMessages(messages), tools: toolDefs.map((t) => ({ type: "function", function: { name: t.name, description: t.description, parameters: t.input_schema } })) }
        : { model: cfg.model, max_tokens: 4096, system: cfg.system, messages, tools: toolDefs };
      const url = `${cfg.apiBase.replace(/\/$/, "")}${cfg.apiFormat === "openai" ? "/v1/chat/completions" : "/v1/messages"}`;
      const headers = cfg.apiFormat === "openai"
        ? { "Content-Type": "application/json", Authorization: `Bearer ${cfg.apiKey}` }
        : { "Content-Type": "application/json", "x-api-key": cfg.apiKey, "anthropic-version": "2023-06-01" };
      try {
        const retried = await payAndRetry("POST", url, headers, body, paymentRequired);
        if (retried.ok) {
          let reply = "";
          const ct = retried.headers.get("content-type") || "";
          if (ct.includes("event-stream")) {
            // Some providers always stream, even for non-stream requests.
            const text = await retried.text();
            for (const line of text.split(/\r?\n/)) {
              const t = line.trim();
              if (!t.startsWith("data:")) continue;
              const payload = t.slice(5).trim();
              if (!payload || payload === "[DONE]") continue;
              try {
                const ev = JSON.parse(payload);
                const d = ev.choices?.[0]?.delta;
                if (d?.content) reply += d.content;
                else if (d?.tool_calls?.[0]?.function?.arguments) reply += d.tool_calls[0].function.arguments;
                else if (ev.content?.[0]?.text) reply += ev.content[0].text;
              } catch {}
            }
          } else {
            const data = await retried.json();
            reply = cfg.apiFormat === "openai"
              ? (data.choices?.[0]?.message?.content || "")
              : (data.content?.[0]?.text || "");
          }
          log(`  ${C.green}[pay]${C.reset} request accepted — ${reply.trim().slice(0, 60) || "done"}${C.reset}`);
          if (reply.trim()) { process.stdout.write("\n" + reply.trim() + "\n"); messages.push({ role: "assistant", content: reply.trim() }); }
          return;
        } else {
          const t = await retried.text();
          throw new Error(`paid request failed: ${retried.status} ${t.slice(0, 300)}`);
        }
      } catch (e) {
        log(`  ${C.red}[x]${C.reset} ${e.message}`);
        return;
      }
    }

    // Reconstruct tool_use blocks from Anthropic stream output
    // (Anthropic: content_block_stop yields {index,type,name,input})
    const toolUses = blocks.filter((b) => b.name && b.args !== undefined);

    if (toolUses.length === 0) {
      // No tools requested — text only
      if (assistantText) {
        messages.push({ role: "assistant", content: assistantText });
      }
      log("");
      return;
    }

    // Build assistant message with tool_use blocks
    const assistantContent = [];
    if (assistantText) assistantContent.push({ type: "text", text: assistantText });
    for (const b of toolUses) {
      let input = {};
      try { input = JSON.parse(b.args || "{}"); } catch {}
      assistantContent.push({ type: "tool_use", id: b.toolCallId || `toolu_${Date.now()}`, name: b.name, input });
    }
    messages.push({ role: "assistant", content: assistantContent });

    // Execute tools + collect results
    const results = [];
    for (const b of toolUses) {
      let input = {};
      try { input = JSON.parse(b.args || "{}"); } catch {}
      printToolHeader(b.name, input);
      const r = await runTool(b.name, input);
      const content = r.ok ? JSON.stringify(r) : JSON.stringify(r);
      results.push({ toolUseId: b.toolCallId || `toolu_${Date.now()}`, content });
    }
    messages.push({ role: "user", content: results.map((r) => ({ type: "tool_result", tool_use_id: r.toolUseId, content: r.content })) });
    log("");
  }
}

// ── Entry ─────────────────────────────────────────────────────────────
const isTTY = Boolean(process.stdin.isTTY && process.stdout.isTTY);
const rl = isTTY ? readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true }) : null;

function promptUser() {
  if (rl) {
    rl.setPrompt(`${C.green}${C.bold}agx${C.reset} ${C.gray}›${C.reset} `);
    rl.prompt();
  }
}

async function main() {
  if (process.argv.includes("--version")) { log("agx 0.1.0 — Agent Genesis terminal agent"); process.exit(0); }
  if (process.argv.includes("--help") || process.argv.includes("-h")) { log(helpText); process.exit(0); }

  banner();
  bootSequence();

  // Wallet identity (fail soft if stack down — chat still works)
  let walletNote = "";
  try {
    await ensureIdentity();
    const bal = await getBalance();
    walletNote = bal ? `${C.green}●${C.reset} ${bal.sol_balance ?? "?"} SOL` : `${C.yellow}●${C.reset} balance unavailable`;
    log(`  ${C.green}[wallet]${C.reset} ${identity.address.slice(0, 12)}…  ${walletNote}`);
  } catch (e) {
    log(`  ${C.yellow}[warn]${C.reset} no AgentWallet identity: ${e.message}`);
    log(`  ${C.dim}        chat works; wallet tools need AgentWallet API at ${cfg.agwUrl}${C.reset}`);
  }
  log(`  ${C.gray}type /help for commands. Ctrl+C to quit.${C.reset}`);
  log("");

  if (!cfg.apiKey) {
    log(`  ${C.red}[!]${C.reset} no API key set. Export one first:`);
    log(`      ${C.cyan}export AGX_API_KEY=sk-...${C.reset}`);
    log(`      ${C.cyan}export AGX_API_BASE=https://...  # optional, default Anthropic${C.reset}`);
    log(`      ${C.cyan}export AGX_API_FORMAT=openai      # or openai-compatible${C.reset}`);
    log("");
    process.exit(1);
  }

  const messages = [];

  async function handleLine(rawLine) {
    const input = rawLine.trim();
    if (!input) { promptUser(); return; }

    if (input.startsWith("/")) {
      const [cmd, ...rest] = input.slice(1).split(/\s+/);
      switch (cmd) {
        case "quit": case "exit": case "q":
          log(`${C.gray}bye — wallet stays on-chain.${C.reset}`); process.exit(0);
          break;
        case "help": case "h":
          log(helpText); break;
        case "wallet":
          try {
            const bal = await getBalance();
            log(`  ${C.green}[wallet]${C.reset} ${identity?.address}`);
            log(`  ${C.gray}  api-key : ${identity?.apiKey?.slice(0, 15)}…${C.reset}`);
            log(`  ${C.gray}  balance : ${C.cyan}${bal?.sol_balance ?? "?"} SOL${C.reset} ${bal?.tokens?.length ? `+ ${bal.tokens.length} token(s)` : ""}`);
          } catch (e) { log(`  ${C.red}[x]${C.reset} ${e.message}`); }
          break;
        case "pay":
          cfg.payPerUse = !cfg.payPerUse;
          log(`  ${C.green}[pay]${C.reset} pay-per-use ${cfg.payPerUse ? "ON" : "OFF"}${C.reset}`);
          break;
        case "model":
          if (rest[0]) { cfg.model = rest[0]; log(`  ${C.green}[model]${C.reset} ${cfg.model}`); }
          else log(`  ${C.gray}  model: ${cfg.model}${C.reset}`);
          break;
        default:
          log(`  ${C.yellow}[?]${C.reset} unknown command: /${cmd}  (try /help)`);
      }
      promptUser();
      return;
    }

    messages.push({ role: "user", content: input });
    log(`  ${C.gray}${new Date().toLocaleTimeString()} — processing${C.reset}`);
    try {
      await chat(rl, messages);
    } catch (e) {
      log(`\n  ${C.red}[x]${C.reset} ${e.message}`);
      // keep user turn, retryable
    }
    promptUser();
  }

  if (isTTY) {
    let busy = false;
    let queue = [];

    rl.on("line", (line) => {
      queue.push(line);
      pump();
    });

    async function pump() {
      if (busy) return;
      const line = queue.shift();
      if (line === undefined) return;
      busy = true;
      try { await handleLine(line); } finally { busy = false; pump(); }
    }

    rl.on("close", () => { log(`${C.gray}bye — wallet stays on-chain.${C.reset}`); process.exit(0); });
    promptUser();
  } else {
    // Non-interactive: read all stdin lines and process sequentially
    const stdin = fs.readFileSync(0, "utf8");
    for (const line of stdin.split(/\r?\n/)) {
      if (line.trim()) await handleLine(line);
    }
    log(`${C.gray}bye — wallet stays on-chain.${C.reset}`);
    process.exit(0);
  }
}

main().catch((e) => { console.error(C.red + e.message + C.reset); process.exit(1); });
