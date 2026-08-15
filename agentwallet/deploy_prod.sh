#!/usr/bin/env bash
#
# deploy_prod.sh — Manual production deploy (CI fallback)
#
# Deploys BOTH production surfaces in one command when GitHub Actions is
# unavailable (e.g. account flagged / "Actions has been disabled for this
# user"). Mirrors what CI does:
#
#   1. API      → Railway  (agentwallet/ subdir, Docker build, alembic migrate)
#   2. Dashboard→ Vercel   (packages/dashboard, aliases agentwallet.fun)
#   3. Health checks on both, then prints URLs.
#
# Usage (from the repo root — the folder containing this script):
#   ./deploy_prod.sh            # deploy both
#   ./deploy_prod.sh api        # deploy API only
#   ./deploy_prod.sh dashboard  # deploy dashboard only
#
# Requires:
#   - railway CLI logged in (`railway login`) with project linked
#   - vercel CLI logged in (`npx vercel login`) with the prod project
#   - network access to api-production-6421a.up.railway.app
#
# NOTE: this script is a FALLBACK. Prefer normal CI deploys whenever
# GitHub Actions is healthy.

set -euo pipefail

# This script lives at the repo's agentwallet/ root (next to Dockerfile +
# railway.json), which is exactly the directory `railway up` deploys from.
AGENTWALLET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$AGENTWALLET_DIR/packages/dashboard"
API_URL="https://api-production-6421a.up.railway.app"
SITE_URL="https://agentwallet.fun"

deploy_api() {
  echo "── Deploying API → Railway ──────────────────────────"
  if ! command -v railway >/dev/null 2>&1; then
    echo "✗ railway CLI not found. Install: npm i -g @railway/cli && railway login" >&2
    exit 1
  fi
  (cd "$AGENTWALLET_DIR" && railway up --service api --detach)
  echo "✓ Railway build triggered: $API_URL"
}

deploy_dashboard() {
  echo "── Deploying Dashboard → Vercel ─────────────────────"
  if ! command -v vercel >/dev/null 2>&1 && ! npx --no-install vercel --version >/dev/null 2>&1; then
    echo "✗ vercel CLI not found. Install: npm i -g vercel && npx vercel login" >&2
    exit 1
  fi
  (cd "$DASHBOARD_DIR" && npx vercel deploy --prod --yes)
  echo "✓ Vercel deploy aliased: $SITE_URL"
}

wait_for_health() {
  local url="$1" label="$2" attempts="${3:-30}"
  echo "── Health check: $label ─────────────────────────────"
  for i in $(seq 1 "$attempts"); do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url" || true)"
    if [ "$code" = "200" ]; then
      echo "✓ $label healthy (HTTP 200, attempt $i)"
      return 0
    fi
    echo "  waiting… ($code, attempt $i/$attempts)"
    sleep 10
  done
  echo "✗ $label did not answer 200 within ${attempts}x10s" >&2
  return 1
}

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

main() {
  local target="${1:-both}"

  if [ "$target" = "api" ] || [ "$target" = "both" ]; then
    deploy_api
  fi
  if [ "$target" = "dashboard" ] || [ "$target" = "both" ]; then
    deploy_dashboard
  fi

  # Health checks only when we actually deployed something
  if [ "$target" = "api" ] || [ "$target" = "both" ]; then
    wait_for_health "$API_URL/health" "API (Railway)" 30 || exit 1
  fi
  if [ "$target" = "dashboard" ] || [ "$target" = "both" ]; then
    wait_for_health "$SITE_URL" "Dashboard (Vercel)" 12 || exit 1
  fi

  echo ""
  echo "✅ Deploy complete."
  echo "   API:       $API_URL  (swagger: /docs)"
  echo "   Dashboard: $SITE_URL  (terms /privacy /support)"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

main "$@"
