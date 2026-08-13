#!/usr/bin/env bash
# AgentWallet Protocol — One-command smoke test
#
# Verifies, in a single run:#   1. API       — /health, register, API key, agent + wallet creation,
#                   devnet-funded escrow (create/release) + SOL transfer,
#                   and transactions list
#   2. Python SDK — agent + wallet + balance via aw-protocol-sdk
#   3. CLI        — `agentwallet_cli.main status` and `agents`
#   4. MCP server — initialize handshake + tools/list
#   5. Dashboard  — live dev server, or a production build as fallback
#
# Usage:
#   bash smoke_test.sh
#   API_URL=http://localhost:8000 bash smoke_test.sh
#   SKIP_DASHBOARD=1 bash smoke_test.sh        # skip the dashboard check
#   VALIDATOR_MODE=1 bash smoke_test.sh         # run on-chain checks against a
#                                               # local solana-test-validator (Docker)
#
# Requires a running API (see setup.sh / make start) and, for the
# dashboard fallback build, Node.js >= 18.

set -u

API_URL="${API_URL:-http://localhost:8000}"
API_BASE="${API_BASE:-$API_URL/v1}"
DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:5173}"
SKIP_DASHBOARD="${SKIP_DASHBOARD:-0}"
SOLANA_RPC="${SOLANA_RPC:-https://api.devnet.solana.com}"
VALIDATOR_MODE="${VALIDATOR_MODE:-0}"
VALIDATOR_IMAGE="${VALIDATOR_IMAGE:-solanalabs/solana:stable}"
VALIDATOR_CONTAINER="aw-solana-test-validator"
VALIDATOR_RPC="http://localhost:8899"
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
VENV_PY=""

# Locate the venv python: bin/ on Linux/macOS, Scripts/ on Windows.
# The venv may not exist yet on first run — re-detect after creation.
detect_venv_py() {
  if [ -x "$VENV/bin/python" ]; then
    VENV_PY="$VENV/bin/python"
  elif [ -x "$VENV/Scripts/python.exe" ]; then
    VENV_PY="$VENV/Scripts/python.exe"
  fi
}
detect_venv_py

json_get() {  # json_get <field> <json>
  "$PYTHON" -c "import sys,json;print(json.load(sys.stdin)['$1'])" <<< "$2"
}

# Request devnet SOL (best effort — faucets are externally rate-limited).
# Retries with smaller amounts, then polls on-chain balance. Echoes lamports.
airdrop_devnet_sol() {
  local addr="$1"
  for amount in 500000000 200000000 100000000 100000000; do
    curl -sf --max-time 20 -X POST "$SOLANA_RPC" -H "Content-Type: application/json" \
      -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"requestAirdrop\",\"params\":[\"$addr\",$amount]}" \
      >/dev/null 2>&1 || true
    for i in $(seq 1 10); do
      local resp bal
      resp="$(curl -sf --max-time 10 -X POST "$SOLANA_RPC" -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getBalance\",\"params\":[\"$addr\"]}" 2>/dev/null)" || resp=""
      bal="$(echo "$resp" | "$PYTHON" -c "import sys,json;print(json.load(sys.stdin).get('result',{}).get('value',0))" 2>/dev/null || echo 0)"
      if [ "${bal:-0}" -gt 0 ] 2>/dev/null; then
        echo "$bal"
        return 0
      fi
      sleep 5
    done
  done
  return 1
}

# ── Validator mode ──────────────────────────────────────────────────────────
# Starts a local solana-test-validator (Docker) on the compose network and
# points the API container at it, so the on-chain checks (escrow fund/release,
# SOL transfer) run deterministically without the rate-limited devnet faucet.
start_validator() {
  local api_cid net
  api_cid="$(docker compose -f "$ROOT/docker-compose.yml" ps -q api 2>/dev/null | head -1)"
  net="$(docker inspect "$api_cid" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null)"
  if [ -z "$api_cid" ] || [ -z "$net" ]; then
    fail "validator mode needs the API running via docker compose"
    return 1
  fi
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${VALIDATOR_CONTAINER}$"; then
    docker rm -f "$VALIDATOR_CONTAINER" >/dev/null 2>&1 || true
    docker run -d --name "$VALIDATOR_CONTAINER" --network "$net" -p 8899:8899 \
      "$VALIDATOR_IMAGE" solana-test-validator >/dev/null 2>&1 || {
      fail "could not start $VALIDATOR_CONTAINER (first run pulls the image — may take a while)"
      return 1
    }
  fi
  local ready=""
  for i in $(seq 1 30); do
    if curl -sf --max-time 5 -X POST "$VALIDATOR_RPC" -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' 2>/dev/null | grep -q '"ok"'; then
      ready=1
      break
    fi
    sleep 5
  done
  if [ -z "$ready" ]; then
    fail "solana-test-validator did not become ready"
    return 1
  fi
  # Point the API container at the validator. The override file uses compose
  # 'environment' (higher precedence than env_file) and container-name DNS on
  # the compose network — works on Linux CI and Docker Desktop alike.
  cat > "$ROOT/.smoke-validator-compose.yml" <<YAML
services:
  api:
    environment:
      SOLANA_RPC_URL: http://${VALIDATOR_CONTAINER}:8899
YAML
  docker compose -f "$ROOT/docker-compose.yml" -f "$ROOT/.smoke-validator-compose.yml" \
    up -d api >/dev/null 2>&1 || true
  for i in $(seq 1 20); do
    curl -sf --max-time 5 "$API_URL/health" >/dev/null 2>&1 && break
    sleep 2
  done
  SOLANA_RPC="$VALIDATOR_RPC"
  pass "API pointed at local validator (http://${VALIDATOR_CONTAINER}:8899)"
}

stop_validator() {
  if [ "${VALIDATOR_RESTORED:-0}" = "1" ]; then return; fi
  VALIDATOR_RESTORED=1
  if [ -f "$ROOT/.smoke-validator-compose.yml" ]; then
    docker compose -f "$ROOT/docker-compose.yml" up -d api >/dev/null 2>&1 || true
    rm -f "$ROOT/.smoke-validator-compose.yml"
  fi
  if [ "${KEEP_VALIDATOR:-0}" != "1" ]; then
    docker rm -f "$VALIDATOR_CONTAINER" >/dev/null 2>&1 || true
  fi
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
AGENT_ID=""
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

    # Wallets — A is the funded sender/funder, B is the recipient
    WALLET_ID=""
    WALLET_ADDR=""
    RECIPIENT_ID=""
    RECIPIENT_ADDR=""
    if [ -n "$AGENT_ID" ]; then
      WALLET_A="$(curl -sf --max-time 15 -X POST "$API_BASE/wallets" \
        -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
        -d "{\"agent_id\":\"$AGENT_ID\",\"wallet_type\":\"agent\",\"label\":\"Smoke Funder\"}" 2>/dev/null)" || WALLET_A=""
      if [ -n "$WALLET_A" ] && WALLET_ID="$(json_get id "$WALLET_A" 2>/dev/null)" && WALLET_ADDR="$(json_get address "$WALLET_A" 2>/dev/null)"; then
        pass "funder wallet created ($WALLET_ADDR)"
      else
        fail "funder wallet creation"
        FAILED=1
      fi
      WALLET_B="$(curl -sf --max-time 15 -X POST "$API_BASE/wallets" \
        -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
        -d "{\"agent_id\":\"$AGENT_ID\",\"wallet_type\":\"agent\",\"label\":\"Smoke Recipient\"}" 2>/dev/null)" || WALLET_B=""
      if [ -n "$WALLET_B" ] && RECIPIENT_ID="$(json_get id "$WALLET_B" 2>/dev/null)" && RECIPIENT_ADDR="$(json_get address "$WALLET_B" 2>/dev/null)"; then
        pass "recipient wallet created ($RECIPIENT_ADDR)"
      else
        fail "recipient wallet creation"
        FAILED=1
      fi
    fi

    # Devnet funding — public faucet (best effort), or a local
    # solana-test-validator when VALIDATOR_MODE=1 (deterministic, CI-safe)
    FUNDED=""
    if [ -n "$WALLET_ID" ] && [ -n "$RECIPIENT_ADDR" ]; then
      if [ "$VALIDATOR_MODE" = "1" ]; then
        info "Validator mode: starting local solana-test-validator..."
        start_validator
      fi
      info "Requesting devnet airdrop for $WALLET_ADDR..."
      if BAL="$(airdrop_devnet_sol "$WALLET_ADDR")"; then
        FUNDED=1
        pass "devnet airdrop received ($BAL lamports)"
      else
        warn "devnet airdrop failed ($SOLANA_RPC) — on-chain checks skipped"
      fi
    fi

    # Escrow end-to-end: create -> get -> list, and release when funded
    if [ -n "$WALLET_ID" ] && [ -n "$RECIPIENT_ADDR" ]; then
      EXPECTED="created"
      [ -n "$FUNDED" ] && EXPECTED="funded"
      ESCROW="$(curl -sf --max-time 90 -X POST "$API_BASE/escrow" \
        -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
        -d "{\"funder_wallet_id\":\"$WALLET_ID\",\"recipient_address\":\"$RECIPIENT_ADDR\",\"amount_sol\":0.001,\"conditions\":{\"task\":\"smoke test\"},\"expires_in_hours\":24}" 2>/dev/null)" || ESCROW=""
      if [ -n "$ESCROW" ] && ESCROW_ID="$(json_get id "$ESCROW" 2>/dev/null)" && [ "$(json_get status "$ESCROW" 2>/dev/null)" = "$EXPECTED" ]; then
        pass "escrow created (status=$EXPECTED)"
        if curl -sf --max-time 15 "$API_BASE/escrow/$ESCROW_ID" -H "X-API-Key: $API_KEY" 2>/dev/null | grep -q "$ESCROW_ID"; then
          pass "escrow fetched by id"
        else
          fail "escrow fetch by id"
          FAILED=1
        fi
        if curl -sf --max-time 15 "$API_BASE/escrow?status=$EXPECTED" -H "X-API-Key: $API_KEY" 2>/dev/null | grep -q "$ESCROW_ID"; then
          pass "escrow appears in escrow list"
        else
          fail "escrow list"
          FAILED=1
        fi
        if [ "$EXPECTED" = "funded" ]; then
          RELEASE="$(curl -sf --max-time 90 -X POST "$API_BASE/escrow/$ESCROW_ID/action" \
            -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
            -d '{"action":"release"}' 2>/dev/null)" || RELEASE=""
          if [ -n "$RELEASE" ] && [ "$(json_get status "$RELEASE" 2>/dev/null)" = "released" ]; then
            pass "escrow released (status=released)"
          else
            fail "escrow release"
            FAILED=1
          fi
        fi
      else
        fail "escrow creation (expected status=$EXPECTED)"
        FAILED=1
      fi
    fi

    # Real SOL transfer + tx record (only when devnet funding succeeded)
    if [ -n "$FUNDED" ] && [ -n "$WALLET_ID" ]; then
      TX="$(curl -sf --max-time 90 -X POST "$API_BASE/transactions/transfer-sol" \
        -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
        -d "{\"from_wallet_id\":\"$WALLET_ID\",\"to_address\":\"$RECIPIENT_ADDR\",\"amount_sol\":0.01,\"memo\":\"smoke test transfer\",\"idempotency_key\":\"smoke-$STAMP\"}" 2>/dev/null)" || TX=""
      TX_ID="$(echo "$TX" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d['id']) if d.get('signature') else print('')" 2>/dev/null)" || TX_ID=""
      if [ -n "$TX_ID" ]; then
        pass "SOL transfer signed (tx $TX_ID)"
        if curl -sf --max-time 15 "$API_BASE/transactions/$TX_ID" -H "X-API-Key: $API_KEY" 2>/dev/null | grep -q "$TX_ID"; then
          pass "transaction recorded and fetched by id"
        else
          fail "transaction fetch by id"
          FAILED=1
        fi
      else
        fail "SOL transfer"
        FAILED=1
      fi
    fi

    # Transactions: list endpoint (read path)
    TX_LIST="$(curl -sf --max-time 15 "$API_BASE/transactions" -H "X-API-Key: $API_KEY" 2>/dev/null)" || TX_LIST=""
    if [ -n "$TX_LIST" ] && echo "$TX_LIST" | "$PYTHON" -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
      pass "transactions list endpoint"
    else
      fail "transactions list endpoint"
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
  detect_venv_py
  if [ -z "$VENV_PY" ]; then
    info "Creating venv at .smoke-venv (one-time)..."
    if "$PYTHON" -m venv "$VENV" && detect_venv_py; then
      "$VENV_PY" -m pip install -q --upgrade pip || true
      "$VENV_PY" -m pip install -q "$ROOT/packages/sdk-python" "$ROOT/packages/mcp-server" || {
        fail "installing SDK + MCP packages into venv"
        FAILED=1
      }
    else
      fail "venv creation"
      FAILED=1
    fi
  fi

  if [ -z "$VENV_PY" ]; then
    fail "SDK quickstart skipped — venv unavailable"
    FAILED=1
  else
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
  MCP_OUT="$( { printf '%s\n%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke-test","version":"1.0"}}}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'; \
    sleep 3; } | AGENTWALLET_API_KEY="${API_KEY:-}" timeout 25 "$MCP_BIN" 2>/dev/null)"
  TOOLS="$(echo "$MCP_OUT" | "$PYTHON" -c "
import sys, json
for line in sys.stdin.read().splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        res = json.loads(line).get('result') or {}
    except Exception:
        continue
    if 'tools' in res:
        print(len(res['tools']))
        break
" 2>/dev/null)" || TOOLS=""
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
# Summary — restore the API container and remove the validator if used
# ═══════════════════════════════════════════════════════════════════════════
stop_validator

echo
if [ "$FAILED" = "0" ]; then
  printf "${BGREEN}  All checks passed!${NC}\n"
  exit 0
else
  printf "${RED}  Some checks failed.${NC}  See above for details.\n"
  exit 1
fi
