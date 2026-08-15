#!/usr/bin/env bash
# Production journey test — agentwallet.fun (frontend) + Railway API (backend)
# Register -> Fund SOL -> Get USDC -> Escrow -> x402 -> Transfer, all real devnet txs.
set -euo pipefail

API="https://api-production-6421a.up.railway.app/v1"
STAMP=$(date +%s)
EMAIL="prod-journey-${STAMP}@test.agentwallet.fun"
PASS="JourneyTest-${STAMP}!"
OUT=/tmp/prod_journey_${STAMP}.json
echo "=== 1. REGISTER fresh user ==="
REG=$(curl -s --max-time 30 -X POST "$API/auth/register" -H "Content-Type: application/json" \
  -d "{\"org_name\":\"Prod Journey ${STAMP}\",\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}")
echo "$REG" | python -c "import json,sys; d=json.load(sys.stdin); print('org_id:', d.get('org_id')); print('token:', (d.get('access_token') or '')[:24] + '...')"
TOKEN=$(echo "$REG" | python -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))")
[ -n "$TOKEN" ] || { echo "REGISTER FAILED"; echo "$REG"; exit 1; }

echo
echo "=== 2. FUND SOL (playground/fund) ==="
FUND=$(curl -s --max-time 60 -X POST "$API/playground/fund" -H "Authorization: Bearer $TOKEN")
echo "$FUND" | python -c "import json,sys; d=json.load(sys.stdin); print('wallet:', d.get('wallet_address')); print('amount:', d.get('amount_sol'), 'SOL'); print('confirmed:', d.get('confirmed')); print('explorer:', d.get('explorer_url'))"
FUND_SIG=$(echo "$FUND" | python -c "import json,sys; print(json.load(sys.stdin).get('signature',''))")

echo
echo "=== 3. GET USDC (playground/usdc) ==="
USDC=$(curl -s --max-time 90 -X POST "$API/playground/usdc" -H "Authorization: Bearer $TOKEN")
echo "$USDC" | python -c "import json,sys; d=json.load(sys.stdin); print('amount:', d.get('amount_usdc'), 'dUSDC'); print('mint:', d.get('mint')); print('confirmed:', d.get('confirmed')); print('explorer:', d.get('explorer_url'))"
USDC_SIG=$(echo "$USDC" | python -c "import json,sys; print(json.load(sys.stdin).get('signature',''))")

echo
echo "=== 4. ESCROW create+fund (playground/escrow) ==="
ESC=$(curl -s --max-time 90 -X POST "$API/playground/escrow" -H "Authorization: Bearer $TOKEN")
echo "$ESC" | python -c "import json,sys; d=json.load(sys.stdin); print('escrow_id:', d.get('escrow_id')); print('status:', d.get('status')); print('amount:', d.get('amount_sol'), 'SOL'); print('fund_sig:', d.get('fund_signature')); print('explorer:', d.get('fund_explorer_url'))"
ESC_ID=$(echo "$ESC" | python -c "import json,sys; print(json.load(sys.stdin).get('escrow_id',''))")
ESC_SIG=$(echo "$ESC" | python -c "import json,sys; print(json.load(sys.stdin).get('fund_signature',''))")

echo
echo "=== 5. ESCROW refund (playground/escrow/{id}/refund) ==="
[ -n "$ESC_ID" ] && {
  REF=$(curl -s --max-time 90 -X POST "$API/playground/escrow/$ESC_ID/refund" -H "Authorization: Bearer $TOKEN")
  echo "$REF" | python -c "import json,sys; d=json.load(sys.stdin); print('status:', d.get('status')); print('refund_sig:', d.get('refund_signature') or d.get('signature')); print('explorer:', d.get('explorer_url') or d.get('refund_explorer_url'))"
}

echo
echo "=== 6. X402 pay-per-call (playground/x402) ==="
X402=$(curl -s --max-time 90 -X POST "$API/playground/x402" -H "Authorization: Bearer $TOKEN")
echo "$X402" | python -c "import json,sys; d=json.load(sys.stdin); print('amount:', d.get('amount_sol'), 'SOL'); print('to:', d.get('to_address')); print('payment_confirmed:', d.get('payment_confirmed')); print('verified_on_chain:', d.get('verified_on_chain')); print('ai_provider:', d.get('ai_provider'), '/', d.get('ai_model')); print('ai_response:', (d.get('ai_response') or '')[:110]); print('explorer:', d.get('payment_explorer_url'))"
X402_SIG=$(echo "$X402" | python -c "import json,sys; print(json.load(sys.stdin).get('payment_signature',''))")

echo
echo "=== 7. TRANSFER (playground/transfer) — real SOL send ==="
TR=$(curl -s --max-time 90 -X POST "$API/playground/transfer" -H "Authorization: Bearer $TOKEN")
echo "$TR" | python -c "import json,sys; d=json.load(sys.stdin); print('amount:', d.get('amount_sol'), 'SOL'); print('to:', d.get('to_address')); print('confirmed:', d.get('confirmed')); print('explorer:', d.get('explorer_url'))"
TR_SIG=$(echo "$TR" | python -c "import json,sys; print(json.load(sys.stdin).get('signature',''))")

echo
echo "=============================================="
echo "✅ PRODUCTION JOURNEY SUMMARY — ${EMAIL}"
echo "  fund:    ${FUND_SIG:0:12}..."
echo "  usdc:    ${USDC_SIG:0:12}..."
echo "  escrow:  ${ESC_SIG:0:12}... (refund done)"
echo "  x402:    ${X402_SIG:0:12}..."
echo "  transfer:${TR_SIG:0:12}..."
echo "All explorer links above — check on Solana devnet."
echo "=============================================="
echo "$EMAIL" > /tmp/prod_journey_email.txt
