#!/usr/bin/env bash
# Escrow lifecycle E2E — proves release/refund disburse FROM the platform
# custody wallet (fixes the double-pay bug). Verifies both balance deltas
# AND the on-chain transaction source address.
#
# Usage:
#   bash escrow_lifecycle_test.sh                          # local validator (8899)
#   RPC=https://api.devnet.solana.com bash escrow_lifecycle_test.sh   # devnet
#   AMT1=0.02 AMT2=0.01 FUND_AMT=0.05 ...                  # smaller amounts (devnet)
set -u
API="${API:-http://localhost:8000/v1}"
RPC="${RPC:-http://localhost:8899}"
SOL=1000000000
AMT1="${AMT1:-0.3}"   # escrow #1 (release) amount in SOL
AMT2="${AMT2:-0.1}"   # escrow #2 (refund) amount in SOL
FUND_AMT="${FUND_AMT:-2}"  # devnet funding per address (SOL)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=python
AMT1_LP=$("$PY" -c "print(int($AMT1*1000000000))")
AMT2_LP=$("$PY" -c "print(int($AMT2*1000000000))")
FUND_LP=$("$PY" -c "print(int($FUND_AMT*1000000000))")

J() { python -c "import sys,json;d=json.load(sys.stdin);print(d$1)" 2>/dev/null; }
BAL() { curl -s --max-time 10 -X POST "$RPC" -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getBalance\",\"params\":[\"$1\"]}" | J "['result']['value']"; }
TX_SRC() { # TX_SRC <sig> <timeout_s> -> source pubkey of first transfer instruction (polls)
  local sig=$1 t=$2 out=""
  for i in $(seq 1 $((t/2))); do
    out=$(curl -s --max-time 10 -X POST "$RPC" -H "Content-Type: application/json" \
      -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getTransaction\",\"params\":[\"$sig\",{\"encoding\":\"jsonParsed\",\"maxSupportedTransactionVersion\":0}]}" \
      | python -c "import sys,json;d=json.load(sys.stdin);r=d.get('result');print((r.get('transaction',{}).get('message',{}).get('instructions',[{}])[0].get('parsed',{}).get('info',{}) or {}).get('source','')) if r else ''")
    [ -n "$out" ] && { echo "$out"; return 0; }
    sleep 2
  done
  echo ""
}
WAIT_BAL() { # WAIT_BAL <addr> <timeout_s>  (waits until > 0)
  local addr=$1 t=$2 b=""
  for i in $(seq 1 $((t/2))); do
    b=$(BAL "$addr")
    [ "${b:-0}" -gt 0 ] 2>/dev/null && { echo "$b"; return 0; }
    sleep 2
  done
  echo "${b:-0}"
}
STABLE_BAL() { # STABLE_BAL <addr> <timeout_s> — waits until 2 reads 2s apart agree
  local addr=$1 t=$2 a="" b=""
  for i in $(seq 1 $((t/2))); do
    a=$(BAL "$addr"); b=$(BAL "$addr")
    [ -n "$a" ] && [ "$a" = "$b" ] && { echo "$a"; return 0; }
    sleep 2
  done
  echo "${b:-0}"
}
fund() { # fund <addr> <lamports> — public airdrop, then platform-faucet fallback
  local addr=$1 lam=$2 bal=""
  bal=$(BAL "$addr")
  [ "${bal:-0}" -gt 0 ] 2>/dev/null && { echo "$bal"; return 0; }  # already funded
  curl -s --max-time 20 -X POST "$RPC" -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"requestAirdrop\",\"params\":[\"$addr\",$lam]}" >/dev/null 2>&1
  for i in $(seq 1 6); do
    bal=$(BAL "$addr")
    [ "${bal:-0}" -gt 0 ] 2>/dev/null && { echo "$bal"; return 0; }
    sleep 2
  done
  # Rate-limited public faucet -> deterministic platform faucet (real transfer)
  if [ -f "$ROOT/devnet_faucet.py" ]; then
    echo "  [fund] public airdrop rate-limited — using platform faucet for $addr" >&2
    "$PY" "$ROOT/devnet_faucet.py" "$addr" "$lam" >/dev/null 2>&1 || true
    for i in $(seq 1 10); do
      bal=$(BAL "$addr")
      [ "${bal:-0}" -gt 0 ] 2>/dev/null && { echo "$bal"; return 0; }
      sleep 3
    done
  fi
  echo "0"
}

echo "== 1. register fresh org =="
STAMP=$(date +%s)
REG=$(curl -s --max-time 20 -X POST "$API/auth/register" -H "Content-Type: application/json" \
  -d "{\"org_name\":\"ESC $STAMP\",\"email\":\"esc-${STAMP}@genesis.agent\",\"password\":\"Test!${STAMP}x\"}")
TOKEN=$(echo "$REG" | J "['access_token']")
ORG=$(echo "$REG" | J "['org_id']")
echo "org=$ORG"

echo "== 2. api key + agent + funder + recipient wallets =="
KEY=$(curl -s --max-time 20 -X POST "$API/auth/api-keys" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"name":"e2e","permissions":{"wallets":"rw","agents":"rw","escrows":"rw"}}' | J "['key']")
AGENT=$(curl -s --max-time 20 -X POST "$API/agents" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"name\":\"A $STAMP\",\"description\":\"e2e\",\"capabilities\":[\"coding\"]}" | J "['id']")
FUNDER_ID=$(curl -s --max-time 20 -X POST "$API/wallets" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"$AGENT\",\"wallet_type\":\"agent\",\"label\":\"Funder\"}" | J "['id']")
FUNDER=$(curl -s --max-time 20 "$API/wallets/$FUNDER_ID" -H "X-API-Key: $KEY" | J "['address']")
RECIP=$(curl -s --max-time 20 -X POST "$API/wallets" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"$AGENT\",\"wallet_type\":\"agent\",\"label\":\"Recipient\"}" | J "['address']")
PLATFORM=$(grep PLATFORM_WALLET_ADDRESS .env | cut -d= -f2)
echo "funder=$FUNDER"
echo "recip =$RECIP"
echo "platf =$PLATFORM"

echo "== 3. funding (funder $FUND_AMT SOL, platform if needed) + wait =="
FB0=$(fund "$FUNDER" "$FUND_LP")
PB0=$(BAL "$PLATFORM")
if [ "${PB0:-0}" -eq 0 ] 2>/dev/null; then PB0=$(fund "$PLATFORM" "$FUND_LP"); fi
RB0=$(BAL "$RECIP")
echo "funder=$FB0 platform=$PB0 recip=$RB0"

echo "== 4. create escrow $AMT1 SOL, wait funded =="
ESC=$(curl -s --max-time 60 -X POST "$API/escrow" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"funder_wallet_id\":\"$FUNDER_ID\",\"recipient_address\":\"$RECIP\",\"amount_sol\":$AMT1,\"conditions\":{\"task\":\"e2e release\"}}")
ESC_ID=$(echo "$ESC" | J "['id']")
for i in $(seq 1 10); do
  S1=$(curl -s --max-time 15 "$API/escrow/$ESC_ID" -H "X-API-Key: $KEY" | J "['status']")
  [ "$S1" = "funded" ] && break; sleep 2
done
echo "escrow1=$ESC_ID status=$S1"
# wait until the fund tx has settled (funder balance drops below FB0)
for i in $(seq 1 15); do FB1=$(BAL "$FUNDER"); [ "${FB1:-0}" -lt "$FB0" ] && break; sleep 2; done
FB1=$(STABLE_BAL "$FUNDER" 20); PB1=$(STABLE_BAL "$PLATFORM" 20)
echo "after fund: funder=$FB1 (delta $((FB1-FB0))) platform=$PB1 (delta $((PB1-PB0)))"

echo "== 5. RELEASE =="
REL=$(curl -s --max-time 60 -X POST "$API/escrow/$ESC_ID/action" -H "X-API-Key: $KEY" -H "Content-Type: application/json" -d '{"action":"release"}')
REL_STAT=$(echo "$REL" | J "['status']")
REL_SIG=$(echo "$REL" | J "['release_signature']")
echo "status=$REL_STAT sig=${REL_SIG:0:16}..."
echo "RAW_REL: $REL"
SRC=$(TX_SRC "$REL_SIG" 40)
FB2=$(STABLE_BAL "$FUNDER" 20); PB2=$(STABLE_BAL "$PLATFORM" 20); RB2=$(STABLE_BAL "$RECIP" 20)
echo "after release: funder=$FB2 (delta $((FB2-FB1))) platform=$PB2 (delta $((PB2-PB1))) recip=$RB2 (delta $((RB2-RB0)))"
echo "release tx source: $SRC"

echo "== 6. escrow2 $AMT2 SOL + REFUND =="
ESC2=$(curl -s --max-time 60 -X POST "$API/escrow" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"funder_wallet_id\":\"$FUNDER_ID\",\"recipient_address\":\"$RECIP\",\"amount_sol\":$AMT2,\"conditions\":{\"task\":\"e2e refund\"}}")
ESC2_ID=$(echo "$ESC2" | J "['id']")
for i in $(seq 1 10); do
  S2=$(curl -s --max-time 15 "$API/escrow/$ESC2_ID" -H "X-API-Key: $KEY" | J "['status']")
  [ "$S2" = "funded" ] && break; sleep 2
done
echo "escrow2=$ESC2_ID status=$S2"
for i in $(seq 1 15); do FB3=$(BAL "$FUNDER"); [ "${FB3:-0}" -lt "$FB1" ] && break; sleep 2; done
FB3=$(STABLE_BAL "$FUNDER" 20); PB3=$(STABLE_BAL "$PLATFORM" 20)
REF=$(curl -s --max-time 60 -X POST "$API/escrow/$ESC2_ID/action" -H "X-API-Key: $KEY" -H "Content-Type: application/json" -d '{"action":"refund"}')
REF_STAT=$(echo "$REF" | J "['status']")
REF_SIG=$(echo "$REF" | J "['refund_signature']")
echo "refund status=$REF_STAT sig=${REF_SIG:0:16}..."
echo "RAW_REF: $REF"
REF_SRC=$(TX_SRC "$REF_SIG" 40)
FB4=$(STABLE_BAL "$FUNDER" 20); PB4=$(STABLE_BAL "$PLATFORM" 20)
echo "after refund: funder=$FB4 (delta $((FB4-FB3))) platform=$PB4 (delta $((PB4-PB3)))"
echo "refund tx source: $REF_SRC"

echo ""
echo "========== SUMMARY =========="
PASS=0; FAIL=0
chk() { if [ "$2" = "1" ]; then echo "  PASS  $1"; PASS=$((PASS+1)); else echo "  FAIL  $1"; FAIL=$((FAIL+1)); fi; }
[ "$S1" = "funded" ] && chk "escrow1 funded" 1 || chk "escrow1 funded ($S1)" 0
[ "$REL_STAT" = "released" ] && chk "release -> released" 1 || chk "release -> $REL_STAT" 0
[ "$REF_STAT" = "refunded" ] && chk "refund -> refunded" 1 || chk "refund -> $REF_STAT" 0
D1=$((FB2-FB1)); D2=$((PB2-PB1)); D3=$((RB2-RB0))
[ "$D1" -ge -5000 ] && [ "$D1" -le 5000 ] && chk "release: funder NOT charged (delta $D1)" 1 || chk "release: funder NOT charged (delta $D1)" 0
MIN_RECIP=$((AMT1_LP-5000000))
[ "$D3" -ge "$MIN_RECIP" ] && chk "release: recipient +$AMT1 SOL (delta $D3)" 1 || chk "release: recipient +$AMT1 SOL (delta $D3)" 0
[ "$SRC" = "$PLATFORM" ] && chk "release tx signed by PLATFORM" 1 || chk "release tx signed by PLATFORM (got $SRC)" 0
D4=$((FB4-FB3)); D5=$((PB4-PB3))
MIN_REF=$((AMT2_LP-5000000))
[ "$D4" -ge "$MIN_REF" ] && chk "refund: funder got money back (delta $D4)" 1 || chk "refund: funder got money back (delta $D4)" 0
[ "$REF_SRC" = "$PLATFORM" ] && chk "refund tx signed by PLATFORM" 1 || chk "refund tx signed by PLATFORM (got $REF_SRC)" 0
echo "RESULT: $PASS pass, $FAIL fail"
[ "$FAIL" = "0" ]
