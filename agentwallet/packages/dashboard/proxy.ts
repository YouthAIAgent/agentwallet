/**
 * Vercel Routing Middleware (see vercel.json → `proxy`).
 *
 * Runs only for `/api/*` requests (matcher) and proxies them to the Railway
 * API, forwarding Vercel's geo header (`x-vercel-ip-country`) as
 * `cf-ipcountry` so the presence tracker records a real country code.
 * Everything else falls through to normal routing (SPA rewrite).
 *
 * Plain JS-compatible TS, no imports — Vercel compiles this entrypoint
 * itself, independent of the Vite/tsc build.
 */

const UPSTREAM = "https://api-production-6421a.up.railway.app";

export default async function proxy(request: Request): Promise<Response> {
  const url = new URL(request.url);

  // /api/v1/public/presence -> /v1/public/presence on the API
  const target = new URL(UPSTREAM);
  target.pathname = url.pathname.replace(/^\/api/, "");
  target.search = url.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  // forward Vercel's geo header so presence records a real country code
  const country = request.headers.get("x-vercel-ip-country");
  if (country && /^[A-Za-z]{2}$/.test(country)) {
    headers.set("cf-ipcountry", country.toUpperCase());
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(target.toString(), init);
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: upstream.headers,
  });
}
