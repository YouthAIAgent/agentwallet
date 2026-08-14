// Vertical 1080x1920 captures for the shorts.
import puppeteer from "puppeteer-core";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SHOTS = path.join(ROOT, "shots-v");
mkdirSync(SHOTS, { recursive: true });

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const DEV = "http://127.0.0.1:3000";
const API = `${DEV}/api/v1`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const b = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars"],
});
const p = await b.newPage();
await p.goto(`${DEV}/login`, { waitUntil: "networkidle2" });

const reg = await p.evaluate(async (API) => {
  const r = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ org_name: "Vertical", email: `vert${Date.now()}@example.com`, password: "VertPass123!" }),
  });
  return r.json();
}, API);
const token = reg.access_token;
if (!token) throw new Error("register failed");
console.log("registered");

await p.evaluate(async ({ API, token }) => {
  const h = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
  const mk = (path, body) => fetch(`${API}/${path}`, { method: "POST", headers: h, body: JSON.stringify(body) }).then(r => r.json()).catch(() => {});
  await mk("agents", { name: "Trading Bot", description: "Executes strategy trades on devnet" });
  await mk("agents", { name: "Support Agent", description: "Handles user queries and refunds" });
  await mk("wallets", { label: "Trading Vault", wallet_type: "treasury" });
  await mk("wallets", { label: "Escrow Pool", wallet_type: "escrow" });
}, { API, token });

async function shot(page, name) {
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await sleep(3200);
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
  console.log("shot:", name);
}

// public
const pub = await b.newPage();
await pub.goto(`${DEV}/`, { waitUntil: "networkidle2" });
await shot(pub, "v-landing");
await pub.goto(`${DEV}/login`, { waitUntil: "networkidle2" });
await shot(pub, "v-login");
await pub.close();

// authed
await p.goto(`${DEV}/login`, { waitUntil: "networkidle2" });
await p.evaluate((t) => { localStorage.setItem("aw_token", t); localStorage.setItem("aw-theme", "dark"); }, token);
await p.goto(`${DEV}/app`, { waitUntil: "networkidle2" });
await shot(p, "v-dashboard");
await p.goto(`${DEV}/app/agents`, { waitUntil: "networkidle2" });
await shot(p, "v-agents");
await p.goto(`${DEV}/app/wallets`, { waitUntil: "networkidle2" });
await shot(p, "v-wallets");
await p.goto(`${DEV}/app/billing`, { waitUntil: "networkidle2" });
await shot(p, "v-billing");

await b.close();
console.log("vertical shots done");
