#!/usr/bin/env node
/**
 * X402 Gate Proxy — wraps any OpenAI-compatible LLM endpoint with a
 * pay-per-request on-chain gate.
 *
 *   POST /v1/chat/completions
 *     no X-PAYMENT      -> 402 { x402Version, accepts: [{token:"SOL", payTo, amount}] }
 *     X-PAYMENT present -> verify on-chain via AgentWallet /v1/x402/verify,
 *                          then stream the upstream LLM response.
 *
 * Usage:
 *   UPSTREAM_BASE=http://127.0.0.1:20128/v1 node x402-proxy.mjs
 *   AGX_API_BASE=http://127.0.0.1:23131/v1 AGX_PAY_PER_USE=1 node agx.mjs
 */
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const UPSTREAM = (process.env.UPSTREAM_BASE || "http://127.0.0.1:20128/v1").replace(/\/$/, "");
const AGW_URL = (process.env.AGW_URL || "http://localhost:8000").replace(/\/$/, "");
const PORT = parseInt(process.env.PORT || "23131", 10);
const PAY_TO = process.env.PAY_TO || "BTcvExhix1pfVX25imKzkHquGJrncZjijxEJq1RkKK5";
const AMOUNT_LAMPORTS = parseInt(process.env.AMOUNT_LAMPORTS || "100000", 10); // 0.0001 SOL/request
const NETWORK = process.env.NETWORK || "solana-devnet";

function agwKey() {
  try {
    const id = JSON.parse(fs.readFileSync(path.join(os.homedir(), ".agx", "identity.json"), "utf8"));
    if (id.apiKey) return id.apiKey;
  } catch {}
  return process.env.AGW_API_KEY || "";
}

function accepts() {
  return {
    x402Version: "1.0",
    accepts: [{ token: "SOL", payTo: PAY_TO, amount: AMOUNT_LAMPORTS, minAmount: AMOUNT_LAMPORTS }],
  };
}

const server = http.createServer(async (req, res) => {
  if (req.method === "POST" && req.url === "/v1/chat/completions") {
    let body = "";
    for await (const chunk of req) body += chunk;

    const payment = req.headers["x-payment"];
    if (!payment) {
      res.writeHead(402, { "Content-Type": "application/json" });
      res.end(JSON.stringify(accepts()));
      return;
    }

    // Verify the on-chain payment through AgentWallet
    try {
      const vr = await fetch(`${AGW_URL}/v1/x402/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": agwKey() },
        body: JSON.stringify({
          payment_header: payment,
          expected_pay_to: PAY_TO,
          expected_amount_lamports: AMOUNT_LAMPORTS,
          network: NETWORK,
        }),
      });
      const v = await vr.json();
      if (!v.valid) {
        res.writeHead(402, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: `payment invalid: ${v.error}`, ...accepts() }));
        return;
      }
    } catch (e) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: `verify failed: ${e.message}` }));
      return;
    }

    // Stream the upstream LLM response
    try {
      const up = await fetch(`${UPSTREAM}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: req.headers["authorization"] || `Bearer ${process.env.UPSTREAM_KEY || ""}`,
        },
        body,
      });
      const ct = up.headers.get("content-type") || "application/json";
      console.log(`[gate] verified -> upstream ${up.status} ct=${ct}`);
      const chunks = [];
      for await (const chunk of up.body) chunks.push(chunk);
      const buf = Buffer.concat(chunks);
      console.log(`[gate] upstream body ${buf.length}b first=${buf.subarray(0, 80).toString().slice(0, 80)}`);
      res.writeHead(up.status, { "Content-Type": ct });
      res.end(buf);
    } catch (e) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: `upstream failed: ${e.message}` }));
    }
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "not found" }));
});

server.listen(PORT, () => {
  console.log(`[x402-gate] :${PORT} -> ${UPSTREAM}`);
  console.log(`[x402-gate] price ${AMOUNT_LAMPORTS / 1e9} SOL/request -> ${PAY_TO} (${NETWORK})`);
  console.log(`[x402-gate] verify via ${AGW_URL}/v1/x402/verify`);
});
