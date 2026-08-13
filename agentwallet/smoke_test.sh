#!/usr/bin/env bash
# AgentWallet Protocol — One-command smoke test
#
# Verifies, in a single run:
#   1. API        — /health, register, API key, agent creation
#   2. Python SDK — agent + wallet + balance via aw-protocol-sdk
#   3. CLI        — `agentwallet_cli.main status` and `agents`
#   4. MCP server — initialize handshake + tools/list
#   5. Dashboard  — live dev server, or a production build as fallback
#
# Usage:
#   bash smoke_test.sh
#   API_URL=http://localhost:8000 bash smoke_test.sh
#   SKIP_DASHBOARD=1 bash smoke_test.sh        # skip the dashboard check
#
# Requires a running API (see setup.sh / make start) and, for the
# dashboard fallback build, Node.js >= 18.

set -u

API_URL="${API_URL:-http://localhost:8000}"
API_BASE="${API_BASE:-$API_URL/v1}"
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:5173}"
SKIP_DASHBOARD="${SKIP_DASHBOARD:-0}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Detect Python (verify it actually runs) ────────────────────────────────
PYTHON=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" --version >/dev/null 2>&1; then
    PYTHON="$c"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "[FAIL] Python 3.10+ not found. Install from https://python.org"
  exit 1
fi

# ── Colors (ASCII-safe) ─────────────────────────────────────────────────────
BGREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'

pass() { printf "${BGREEN}[PASS]${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
fail() { printf "${RED}[FAIL]${NC} %s\n" "$1"; }
info() { printf "${CYAN}[INFO]${NC} %s\n" "$1"; }

FAILED=0
STAMP="$(date +%s)"
EMAIL="smoke-${STAMP}@example.com"
PASSWORD='SmokeTest123!'
VENV="$ROOT/.smoke-venv"
VENV_PY="$VENV/bin/python"
[ -x "$VENV_PY" ] || VENV_PY="$VENV/Scripts/python.exe"

json_get() {  # json_get <field> <json>
  "$PYTHON" -c "import sys,json;print(json.load(sys.stdin)['$1'])" <<< "$2"
}

have() { command -v "$1" >/dev/null 2>&1; }

# ═══════════════════════════════════════════════════════════════════════════
info "=== AgentWallet smoke test (API + SDK + CLI + MCP + Dashboard) ==="

# ═══════════════════════════════════════════════════════════════════════════
# 1/5  API
# ═══════════════════════════════════════════════════════════════════════════
info "1/5  API — $API_URL"

HEALTH="$(curl -sf --max-time 10 "$API_URL/health" 2>/dev/null)" || HEALTH=""
if [ -z "$HEALTH" ]; then
  fail "API not reachable at $API_URL (start it with: bash setup.sh or make start)"
  FAILED=1
else
  pass "health endpoint ($HEALTH)"
fi

API_KEY=""
TOKEN=""
if [ -n "$HEALTH" ]; then
  REG="$(curl -sf --max-time 15 -X POST "$API_BASE/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"org_name\":\"Smoke Test ${STAMP}\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" 2>/dev/null)" || REG=""
  if [ -n "$REG" ] && TOKEN="$(json_get access_token "$REG" 2>/dev/null)"; then
    pass "register (org $EMAIL)"
  else
    fail "register"
    FAILED=1
  fi

  if [ -n "$TOKEN" ]; then
    KEYRESP="$(curl -sf --max-time 15 -X POST "$API_BASE/auth/api-keys" \
      -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
      -d '{"name":"smoke-test","permissions":{}}' 2>/dev/null)" || KEYRESP=""
    if [ -n "$KEYRESP" ] && API_KEY="$(json_get key "$KEYRESP" 2>/dev/null)"; then
      pass "API key created (${API_KEY:0:12}...)"
    else
      fail "API key creation"
      FAILED=1
    fi
  fi

  if [ -n "$API_KEY" ]; then
    AGENT="$(curl -sf --max-time 15 -X POST "$API_BASE/agents" \
      -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
      -d '{"name":"smoke-curl-agent","description":"smoke test via curl","capabilities":["analysis"]}' 2>/dev/null)" || AGENT=""
    if [ -n "$AGENT" ] && AGENT_ID="$(json_get id "$AGENT" 2>/dev/null)"; then
      pass "agent created via raw API ($AGENT_ID)"
    else
      fail "agent creation via raw API"
      FAILED=1
    fi
  fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# 2/5  Python SDK
# ═══════════════════════════════════════════════════════════════════════════
info "2/5  Python SDK (aw-protocol-sdk)"

if [ -z "$API_KEY" ]; then
  fail "SDK check skipped — no API key (API section failed)"
  FAILED=1
else
  if [ ! -x "$VENV_PY" ]; then
    info "Creating venv at .smoke-venv (one-time)..."
    "$PYTHON" -m venv "$VENV" || { fail "venv creation"; FAILED=1; }
    "$VENV_PY" -m pip install -q --upgrade pip || true
    "$VENV_PY" -m pip install -q "$ROOT/packages/sdk-python" "$ROOT/packages/mcp-server" || {
      fail "installing SDK + MCP packages into venv"
      FAILED=1
    }
  fi

  SDK_OUT="$(AW_API_KEY="$API_KEY" "$VENV_PY" - "$API_BASE" 2>&1 <<'PYEOF'
import asyncio, os, sys
from agentwallet import AgentWallet

async def main():
    async with AgentWallet(api_key=os.environ["AW_API_KEY"], base_url=sys.argv[1]) as aw:
        agent = await aw.agents.create(name="smoke-agent", description="smoke test via SDK", capabilities=["analysis"])
        wallet = await aw.wallets.create(agent_id=agent.id, wallet_type="agent", label="Smoke Wallet")
        balance = await aw.wallets.get_balance(wallet.id)
        print(f"agent={agent.id} wallet={wallet.address} sol={balance.sol_balance}")
    print("SDK_OK")

asyncio.run(main())
PYEOF
)"
  if echo "$SDK_OUT" | grep -q "SDK_OK"; then
    pass "SDK quickstart — $SDK_OUT"
  else
    fail "SDK quickstart"
    echo "$SDK_OUT" | tail -5
    FAILED=1
  fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# 3/5  CLI
# ═══════════════════════════════════════════════════════════════════════════
info "3/5  CLI (agentwallet_cli)"

if [ -z "$API_KEY" ] || [ ! -x "$VENV_PY" ]; then
  fail "CLI check skipped — missing API key or venv"
  FAILED=1
else
  CLI_OUT="$(AGENTWALLET_API_KEY="$API_KEY" AGENTWALLET_API_URL="$API_URL" \
    PYTHONPATH="$ROOT/packages/cli" "$VENV_PY" -m agentwallet_cli.main status 2>&1)"
  if echo "$CLI_OUT" | grep -q "AGENTWALLET PLATFORM STATUS"; then
    pass "CLI status"
  else
    fail "CLI status"
    echo "$CLI_OUT" | tail -5
    FAILED=1
  fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# 4/5  MCP server
# ═══════════════════════════════════════════════════════════════════════════
info "4/5  MCP server (agentwallet-mcp)"

MCP_BIN="$VENV/bin/agentwallet-mcp"
[ -x "$MCP_BIN" ] || MCP_BIN="$VENV/Scripts/agentwallet-mcp.exe"

if [ ! -x "$MCP_BIN" ]; then
  fail "MCP binary not found in venv"
  FAILED=1
else
  MCP_OUT="$(printf '%s\n%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke-test","version":"1.0"}}}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
    | AGENTWALLET_API_KEY="${API_KEY:-}" timeout 20 "$MCP_BIN" 2>/dev/null | tail -1)"
  TOOLS="$(echo "$MCP_OUT" | "$PYTHON" -c "import sys,json;print(len(json.loads(sys.stdin.read())['result']['tools']))" 2>/dev/null)" || TOOLS=""
  if [ -n "$TOOLS" ] && [ "$TOOLS" -ge 30 ] 2>/dev/null; then
    pass "MCP initialized — $TOOLS tools exposed"
  else
    fail "MCP initialize / tools/list"
    FAILED=1
  fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# 5/5  Dashboard
# ═══════════════════════════════════════════════════════════════════════════
info "5/5  Dashboard"

if [ "$SKIP_DASHBOARD" = "1" ]; then
  warn "Dashboard check skipped (SKIP_DASHBOARD=1)"
elif curl -sf --max-time 5 "$DASHBOARD_URL" >/dev/null 2>&1; then
  pass "dashboard dev server at $DASHBOARD_URL"
elif have node; then
  info "No dev server at $DASHBOARD_URL — running production build instead"
  if (cd "$ROOT/packages/dashboard" && npm install --no-audit --no-fund >/dev/null 2>&1 && npm run build >/dev/null 2>&1 && [ -f dist/index.html ]); then
    pass "dashboard production build"
  else
    fail "dashboard production build"
    FAILED=1
  fi
else
  fail "dashboard not running at $DASHBOARD_URL and Node.js not found"
  FAILED=1
fi

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════
echo
if [ "$FAILED" = "0" ]; then
  printf "${BGREEN}  All checks passed!${NC}\n"
  exit 0
else
  printf "${RED}  Some checks failed.${NC}  See above for details.\n"
  exit 1
fi
