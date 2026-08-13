#!/usr/bin/env node
/**
 * Mock Anthropic-compatible SSE provider for testing agx without a real key.
 *
 *   node mock-provider.mjs &
 *   AGX_API_BASE=http://localhost:9393 AGX_API_KEY=test AGX_MODEL=mock \
 *     node agx.mjs
 *
 * Behavior: streams a text reply, then emits a tool_use block for
 * run_command, then (on tool_result) a final text reply.
 */

import http from "node:http";

const PORT = Number(process.env.MOCK_PORT || 9393);

function sse(chunks) {
  let body = "";
  for (const c of chunks) {
    body += `data: ${JSON.stringify(c)}\n\n`;
  }
  return body;
}

const server = http.createServer((req, res) => {
  if (req.method !== "POST") { res.writeHead(405); res.end(); return; }
  let raw = "";
  req.on("data", (d) => (raw += d));
  req.on("end", () => {
    let reqBody = {};
    try { reqBody = JSON.parse(raw); } catch {}

    const lastMsg = reqBody.messages?.[reqBody.messages.length - 1]?.content;
    const lastToolResults = (Array.isArray(lastMsg) ? lastMsg : []).filter((b) => b.type === "tool_result");
    const toolResultCount = Array.isArray(reqBody.messages)
      ? reqBody.messages.filter((m) => Array.isArray(m.content) && m.content.some((b) => b.type === "tool_result")).length
      : 0;

    let body;
    if (toolResultCount >= 2) {
      // Third turn: both tools ran — final text reply
      body = sse([
        { type: "message_start", message: { role: "assistant", content: [] } },
        { type: "content_block_start", index: 0, content_block: { type: "text", text: "" } },
        { type: "content_block_delta", index: 0, delta: { type: "text_delta", text: "Done — command executed and wallet balance checked.\n" } },
        { type: "content_block_stop", index: 0 },
        { type: "message_stop" },
      ]);
    } else if (lastToolResults.length > 0) {
      // Second turn: emit wallet_balance tool
      body = sse([
        { type: "message_start", message: { role: "assistant", content: [] } },
        { type: "content_block_start", index: 0, content_block: { type: "text", text: "" } },
        { type: "content_block_delta", index: 0, delta: { type: "text_delta", text: "Let me check your wallet too.\n" } },
        { type: "content_block_stop", index: 0 },
        { type: "content_block_start", index: 1, content_block: { type: "tool_use", id: "toolu_mock_2", name: "wallet_balance", input: {} } },
        { type: "content_block_delta", index: 1, delta: { type: "input_json_delta", partial_json: "{}" } },
        { type: "content_block_stop", index: 1 },
        { type: "message_stop" },
      ]);
    } else {
      // First turn: run_command tool
      body = sse([
        { type: "message_start", message: { role: "assistant", content: [] } },
        { type: "content_block_start", index: 0, content_block: { type: "text", text: "" } },
        { type: "content_block_delta", index: 0, delta: { type: "text_delta", text: "I'll run that for you.\n" } },
        { type: "content_block_stop", index: 0 },
        { type: "content_block_start", index: 1, content_block: { type: "tool_use", id: "toolu_mock_1", name: "run_command", input: {} } },
        { type: "content_block_delta", index: 1, delta: { type: "input_json_delta", partial_json: '{"command": "echo AGENT-GENESIS-OK"}' } },
        { type: "content_block_stop", index: 1 },
        { type: "message_stop" },
      ]);
    }
    res.writeHead(200, { "Content-Type": "text/event-stream" });
    res.end(body);
  });
});

server.listen(PORT, () => console.log(`mock provider on :${PORT}`));
