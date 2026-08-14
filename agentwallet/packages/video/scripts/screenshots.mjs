// Captures 1920x1080 screenshots of every agentwallet page for the launch video.
import puppeteer from "puppeteer-core";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SHOTS = path.join(ROOT, "shots");
mkdirSync(SHOTS, { recursive: true });

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const DEV = "http://127.0.0.1:3000";
const API = `${DEV}/api/v1`;

const seed = `video${Date.now() % 100000}`;
const email = `${seed}@example.com`;
const password = "VideoPass123!";
const org = "Launch Studio";

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars"],
});

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function shot(page, name) {
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await sleep(3200); // let data load + render settle
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
  console.log("shot:", name);
}

const page = await browser.newPage();
page.on("console", (m) => {
  if (m.type() === "error") console.log("  [console.error]", m.text().slice(0, 120));
});

// navigate first so fetch runs from the app origin (CORS)
await page.goto(`${DEV}/login`, { waitUntil: "networkidle2" });

// --- register via the API (through the vite proxy) ---
const reg = await page.evaluate(
  async ({ API, email, password, org }) => {
    const r = await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ org_name: org, email, password }),
    });
    return r.json();
  },
  { API, email, password, org }
);
const token = reg.access_token;
if (!token) throw new Error("register failed: " + JSON.stringify(reg));
console.log("registered:", email);

// --- seed within free-plan limits (2 agents + 3 wallets) ---
await page.evaluate(
  async ({ API, token }) => {
    const h = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
    const mk = (path, body) =>
      fetch(`${API}/${path}`, {
        method: "POST",
        headers: h,
        body: JSON.stringify(body),
      }).then((r) => r.json());
    await mk("agents", {
      name: "Trading Bot",
      description: "Executes strategy trades on devnet",
    }).catch(() => {});
    await mk("agents", {
      name: "Support Agent",
      description: "Handles user queries and refunds",
    }).catch(() => {});
    await mk("wallets", { label: "Trading Vault", wallet_type: "treasury" }).catch(
      () => {}
    );
    await mk("wallets", { label: "Escrow Pool", wallet_type: "escrow" }).catch(
      () => {}
    );
    await mk("wallets", { label: "Bot Wallet", wallet_type: "agent" }).catch(
      () => {}
    );
  },
  { API, token }
);
console.log("seeded agents + wallets");

// --- landing + login (public, no token) ---
const pub = await browser.newPage();
await pub.goto(`${DEV}/`, { waitUntil: "networkidle2" });
await shot(pub, "01-landing");
await pub.goto(`${DEV}/login`, { waitUntil: "networkidle2" });
await shot(pub, "02-login");
await pub.close();

// --- authed pages ---
await page.goto(`${DEV}/login`, { waitUntil: "networkidle2" });
await page.evaluate((token) => {
  localStorage.setItem("aw_token", token);
  localStorage.setItem("aw-theme", "dark");
}, token);
await page.goto(`${DEV}/app`, { waitUntil: "networkidle2" });
await shot(page, "03-dashboard");
await page.goto(`${DEV}/app/agents`, { waitUntil: "networkidle2" });
await shot(page, "04-agents");
await page.goto(`${DEV}/app/wallets`, { waitUntil: "networkidle2" });
await shot(page, "05-wallets");
await page.goto(`${DEV}/app/transactions`, { waitUntil: "networkidle2" });
await shot(page, "06-transactions");
await page.goto(`${DEV}/app/analytics`, { waitUntil: "networkidle2" });
await shot(page, "07-analytics");
await page.goto(`${DEV}/app/policies`, { waitUntil: "networkidle2" });
await shot(page, "08-policies");
await page.goto(`${DEV}/app/audit-log`, { waitUntil: "networkidle2" });
await shot(page, "09-audit-log");
await page.goto(`${DEV}/app/billing`, { waitUntil: "networkidle2" });
await shot(page, "10-billing");
await page.goto(`${DEV}/app/pda-wallets`, { waitUntil: "networkidle2" });
await shot(page, "11-pda-wallets");

// --- light theme dashboard for variety ---
await page.evaluate(() => localStorage.setItem("aw-theme", "light"));
await page.goto(`${DEV}/app`, { waitUntil: "networkidle2" });
await shot(page, "12-dashboard-light");

await browser.close();
console.log("done — screenshots in", SHOTS);
