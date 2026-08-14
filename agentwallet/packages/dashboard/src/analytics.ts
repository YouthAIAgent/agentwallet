/**
 * Env-driven web analytics:
 *   - Google Analytics 4  — set VITE_GA_ID (e.g. G-XXXXXXXXXX)
 *   - Plausible           — set VITE_PLAUSIBLE_DOMAIN (your domain)
 * Both are loaded only when configured, so builds without an ID are no-ops.
 */
declare global {
  interface Window {
    dataLayer?: unknown[][];
    gtag?: (...args: unknown[]) => void;
    plausible?: (
      event: string,
      opts?: { props?: Record<string, unknown> }
    ) => void;
  }
}

const GA_ID = import.meta.env.VITE_GA_ID as string | undefined;
const PLAUSIBLE_DOMAIN = import.meta.env
  .VITE_PLAUSIBLE_DOMAIN as string | undefined;

export function initAnalytics() {
  if (GA_ID) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function (...args: unknown[]) {
      window.dataLayer!.push(args);
    };
    window.gtag("js", new Date());
    window.gtag("config", GA_ID, { anonymize_ip: true });
    const s = document.createElement("script");
    s.async = true;
    s.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    document.head.appendChild(s);
  }
  if (PLAUSIBLE_DOMAIN) {
    const s = document.createElement("script");
    s.defer = true;
    s.src = "https://plausible.io/js/script.js";
    s.setAttribute("data-domain", PLAUSIBLE_DOMAIN);
    document.head.appendChild(s);
  }
}

/** Fire a custom event on whichever provider is configured. */
export function track(event: string, props?: Record<string, unknown>) {
  if (GA_ID) window.gtag?.("event", event, props);
  if (PLAUSIBLE_DOMAIN) window.plausible?.(event, { props });
}
