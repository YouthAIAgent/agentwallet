#!/usr/bin/env bash
# x402 pay-per-use lifecycle E2E on devnet.
#
# Proves the "decentralized paywall" flow end to end:
#   1. Configure a paid route (GET /v1/agents) via the API
#   2. Direct request without a proof  -> 402 Payment Required
#   3. /v1/x402/request pays on-chain from the org wallet, retries with
#      the X-PAYMENT proof            -> 200 + payment_made=true
#   4. /v1/x402/verify confirms the payment proof
#   5. On-chain check: payer paid the configured pay_to (platform wallet)
#
# Usage:
#   bash x402_lifecycle_test.sh                                  # local validator
#   RPC=https://api.devnet.solana.com bash x402_lifecycle_test.sh  # devnet
set -u
API="${API:-http://localhost:8000/v1}"
RPC="${RPC:-http://localhost:8899}"
PRICE_LP="${PRICE_LP:-1000000}"      # 0.001 SOL per request
FUND_LP="${FUND_LP:-10000000}"       # 0.01 SOL to fund the payer wallet
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=python

J() { python -c "import sys,json;d=json.load(sys.stdin);print(d$1)" 2>/dev/null; }
BAL() { curl -s --max-time 10 -X POST "$RPC" -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getBalance\",\"params\":[\"$1\"]}" | J "['result']['value']"; }
TX_INFO() { # TX_INFO <sig> -> "source->destination lamports" of first transfer ix (polls)
  local sig=$1 t=40 out=""
  for i in $(seq 1 $((t/2))); do
    out=$(curl -s --max-time 10 -X POST "$RPC" -H "Content-Type: application/json" \
      -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getTransaction\",\"params\":[\"$sig\",{\"encoding\":\"jsonParsed\",\"maxSupportedTransactionVersion\":0}]}" \
      | python -c "
import sys,json
d=json.load(sys.stdin); r=d.get('result')
if not r: print(''); raise SystemExit
for i in r.get('transaction',{}).get('message',{}).get('instructions',[]):
    info=(i.get('parsed',{}) or {}).get('info',{})
    if info.get('destination'):
        print(f\"{info.get('source')}->{info.get('destination')} {info.get('lamports')}\"); raise SystemExit
print('')")
    [ -n "$out" ] && { echo "$out"; return 0; }
    sleep 2
  done
  echo ""
}

PASS=0; FAIL=0
chk() { if [ "$2" = "1" ]; then echo "  PASS  $1"; PASS=$((PASS+1)); else echo "  FAIL  $1"; FAIL=$((FAIL+1)); fi; }

echo "== 1. register org + api key + payer wallet =="
STAMP=$(date +%s)
REG=$(curl -s --max-time 20 -X POST "$API/auth/register" -H "Content-Type: application/json" \
  -d "{\"org_name\":\"X402 $STAMP\",\"email\":\"x402-${STAMP}@genesis.agent\",\"password\":\"Test!${STAMP}x\"}")
TOKEN=$(echo "$REG" | J "['access_token']")
[ -n "$TOKEN" ] && chk "register (x402-$STAMP)" 1 || chk "register" 0

KEY=$(curl -s --max-time 20 -X POST "$API/auth/api-keys" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"name":"x402","permissions":{"wallets":"rw","agents":"rw","x402":"rw"}}' | J "['key']")
[ -n "$KEY" ] && chk "api key" 1 || chk "api key" 0

AGENT=$(curl -s --max-time 20 -X POST "$API/agents" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"name\":\"X402 $STAMP\",\"description\":\"x402 e2e\",\"capabilities\":[\"analysis\"]}" | J "['id']")
WALLET_ID=$(curl -s --max-time 20 -X POST "$API/wallets" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"$AGENT\",\"wallet_type\":\"agent\",\"label\":\"x402 payer\"}" | J "['id']")
PAYER=$(curl -s --max-time 20 "$API/wallets/$WALLET_ID" -H "X-API-Key: $KEY" | J "['address']")
[ -n "$PAYER" ] && chk "payer wallet ($PAYER)" 1 || chk "payer wallet" 0

echo "== 2. configure paid route (GET /agents @ $PRICE_LP lamports) =="
PLATFORM=$(grep PLATFORM_WALLET_ADDRESS .env | cut -d= -f2)
CFG=$(curl -s --max-time 20 -X POST "$API/x402/configure" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"pricing\":[{\"route_pattern\":\"/agents\",\"method\":\"GET\",\"price_lamports\":$PRICE_LP,\"description\":\"pay to list agents\",\"pay_to\":\"$PLATFORM\"}],\"enabled\":true,\"network\":\"solana-devnet\"}")
N=$(echo "$CFG" | J "['configured_routes']")
[ "${N:-0}" = "1" ] && chk "route configured (pay_to=$PLATFORM)" 1 || chk "route configured ($CFG)" 0

echo "== 3. fund payer wallet ($FUND_LP lamports) =="
bal=$(BAL "$PAYER")
if [ "${bal:-0}" -eq 0 ] 2>/dev/null; then
  curl -s --max-time 20 -X POST "$RPC" -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"requestAirdrop\",\"params\":[\"$PAYER\",$FUND_LP]}" >/dev/null 2>&1
  for i in $(seq 1 6); do
    bal=$(BAL "$PAYER"); [ "${bal:-0}" -gt 0 ] 2>/dev/null && break; sleep 2
  done
  if [ "${bal:-0}" -eq 0 ] 2>/dev/null; then
    echo "  [fund] public airdrop rate-limited — using platform faucet"
    "$PY" "$ROOT/devnet_faucet.py" "$PAYER" "$FUND_LP" >/dev/null 2>&1 || true
    for i in $(seq 1 10); do
      bal=$(BAL "$PAYER"); [ "${bal:-0}" -gt 0 ] 2>/dev/null && break; sleep 3
    done
  fi
fi
[ "${bal:-0}" -gt 0 ] 2>/dev/null && chk "payer funded ($bal lamports)" 1 || chk "payer funded ($bal)" 0

echo "== 4. direct GET without proof -> expect 402 =="
STATUS=$(curl -s -o /tmp/x402_no_proof.json -w "%{http_code}" --max-time 15 "$API/agents" -H "X-API-Key: $KEY")
[ "$STATUS" = "402" ] && chk "402 Payment Required (got $STATUS)" 1 || chk "402 Payment Required (got $STATUS)" 0
ACCEPTS=$(grep -c '"accepts"' /tmp/x402_no_proof.json 2>/dev/null || echo 0)
[ "$ACCEPTS" != "0" ] && chk "402 body has accepts[] (x402 spec)" 1 || chk "402 body has accepts[]" 0

echo "== 5. /v1/x402/request — auto-pay + retry with proof =="
RESP=$(curl -s --max-time 120 -X POST "$API/x402/request" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"$API/agents\",\"method\":\"GET\",\"headers\":{\"X-API-Key\":\"$KEY\"},\"wallet_id\":\"$WALLET_ID\",\"max_amount_lamports\":$((PRICE_LP*2))}")
STATUS2=$(echo "$RESP" | J "['status_code']")
PMADE=$(echo "$RESP" | J "['payment_made']")
PSIG=$(echo "$RESP" | J "['payment_signature']")
[ "${STATUS2:-0}" = "200" ] && chk "paid request -> 200 (got $STATUS2)" 1 || chk "paid request -> 200 (got $STATUS2: $RESP)" 0
[ "$PMADE" = "True" ] && chk "payment_made=true" 1 || chk "payment_made (got $PMADE)" 0
[ -n "${PSIG:-}" ] && chk "payment signature present (${PSIG:0:16}...)" 1 || chk "payment signature" 0

echo "== 6. /v1/x402/verify — proof validation =="
VER=$(curl -s --max-time 60 -X POST "$API/x402/verify" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"payment_header\":\"{\\\"payload\\\":{\\\"signature\\\":\\\"$PSIG\\\",\\\"payer\\\":\\\"$PAYER\\\",\\\"amount\\\":\\\"$PRICE_LP\\\",\\\"timestamp\\\":$(date +%s)}}\",\"expected_pay_to\":\"$PLATFORM\",\"expected_amount_lamports\":$PRICE_LP}")
VOK=$(echo "$VER" | J "['valid']")
[ "$VOK" = "True" ] && chk "verify valid (on-chain confirmed)" 1 || chk "verify valid ($VER)" 0

echo "== 7. on-chain: payer paid pay_to exactly $PRICE_LP lamports =="
INFO=$(TX_INFO "$PSIG")
SRC=$(echo "$INFO" | python -c "import sys; l=sys.stdin.read().strip(); print(l.split('->')[0] if l else '')")
DST=$(echo "$INFO" | python -c "import sys; l=sys.stdin.read().strip(); print(l.split('->')[1].split()[0] if l else '')")
AMT=$(echo "$INFO" | python -c "import sys; l=sys.stdin.read().strip(); print(l.split()[-1] if l else '')")
[ "$SRC" = "$PAYER" ] && chk "tx payer = org wallet" 1 || chk "tx payer = org wallet (got $SRC)" 0
[ "$DST" = "$PLATFORM" ] && chk "tx payee = platform wallet" 1 || chk "tx payee = platform wallet (got $DST)" 0
[ "${AMT:-0}" = "$PRICE_LP" ] && chk "tx amount = $PRICE_LP lamports" 1 || chk "tx amount = $PRICE_LP (got $AMT)" 0

echo ""
echo "========== SUMMARY =========="
echo "RESULT: $PASS pass, $FAIL fail"
[ "$FAIL" = "0" ]
