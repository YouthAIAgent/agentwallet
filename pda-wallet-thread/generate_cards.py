# -*- coding: utf-8 -*-
"""Generate all 10 PDA Wallet Thread cards"""
import sys, os, io, json

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\black\Desktop\agentwallet\scripts")
from banger_card import (
    generate_statement_card, generate_code_card, generate_stats_card,
    generate_vs_card, generate_quote_card, generate_announce_card
)

OUT = r"C:\Users\black\Desktop\agentwallet\pda-wallet-thread"

print("=" * 60)
print("PDA WALLET THREAD - Generating 10 Cards")
print("=" * 60)

# Card 1: Hook - Statement (crimson for urgency)
print("\n[1/10] Hook card...")
generate_statement_card(
    "Your AI agent is moving real money with zero guardrails",
    "No spending limits. No revocation. No audit trail. Just a raw private key in an env variable.",
    os.path.join(OUT, "card_01.png"),
    "crimson"
)

# Card 2: The Problem - VS card
print("\n[2/10] Problem VS card...")
generate_vs_card(
    "Private Key Wallets",
    json.dumps(["Key in .env = one leak away", "No spending limits at all", "Can't revoke without moving funds", "Zero audit trail", "Agent has god-mode access"]),
    "PDA Wallets",
    json.dumps(["No private key exists", "On-chain spend policies", "Instant 1-click revocation", "Full on-chain audit trail", "Granular per-agent permissions"]),
    os.path.join(OUT, "card_02.png"),
    "arctic"
)

# Card 3: What Changes - Statement (obsidian)
print("\n[3/10] What changes card...")
generate_statement_card(
    "Don't give your agent keys. Give it permissions.",
    "PDA wallets have no private key. The program controls access. The agent operates within boundaries you define.",
    os.path.join(OUT, "card_03.png"),
    "obsidian"
)

# Card 4: Spend Policies - Code card
print("\n[4/10] Spend policies code card...")
code_text = """<span style="color:#c084fc;">AgentPolicy</span> {
  <span style="color:#94a3b8;">max_per_tx:</span>    <span style="color:#fbbf24;">5 SOL</span>
  <span style="color:#94a3b8;">daily_limit:</span>   <span style="color:#fbbf24;">20 SOL</span>
  <span style="color:#94a3b8;">allowed_tokens:</span> <span style="color:#34d399;">[SOL, USDC, BONK]</span>
  <span style="color:#94a3b8;">destinations:</span>  <span style="color:#34d399;">[jupiter, raydium]</span>
  <span style="color:#94a3b8;">cooldown:</span>      <span style="color:#fbbf24;">30 seconds</span>
  <span style="color:#94a3b8;">emergency:</span>     <span style="color:#f43f5e;">owner_freeze()</span>
}

<span style="color:#64748b;">// Enforced by Solana VM</span>
<span style="color:#64748b;">// Not by your agent. Not by a server.</span>
<span style="color:#64748b;">// By the runtime itself.</span>"""
generate_code_card(
    "On-Chain Spend Policies",
    code_text,
    os.path.join(OUT, "card_04.png"),
    "neon",
    "agent_policy.rs"
)

# Card 5: Multi-Agent - Announce card
print("\n[5/10] Multi-agent announce card...")
generate_announce_card(
    "MULTI-AGENT ISOLATION",
    "Each agent. Own PDA. Own permissions.",
    json.dumps([
        "Agent A: Trading bot -- 10 SOL/day, Jupiter only",
        "Agent B: NFT bidder -- 2 SOL/tx, Tensor only",
        "Agent C: Treasury -- read-only, reports only",
        "One compromised agent can't touch the others"
    ]),
    os.path.join(OUT, "card_05.png"),
    "solar"
)

# Card 6: Speed + Cost - Stats card
print("\n[6/10] Speed + cost stats card...")
generate_stats_card(
    json.dumps([
        {"value": "400ms", "label": "CONFIRMATION"},
        {"value": "$0.0002", "label": "PER TRANSACTION"},
        {"value": "12ms", "label": "API RESPONSE"},
        {"value": "30x", "label": "FASTER THAN ETH"}
    ]),
    "Performance that matches AI agent speed",
    os.path.join(OUT, "card_06.png"),
    "ember"
)

# Card 7: Revocation - Quote card
print("\n[7/10] Revocation quote card...")
generate_quote_card(
    "If you can't revoke your AI agent's access in under 1 second, you don't have security. You have hope.",
    "@Web3__Youth",
    os.path.join(OUT, "card_07.png"),
    "crimson"
)

# Card 8: Composability - Code card
print("\n[8/10] Composability code card...")
code_text2 = """<span style="color:#64748b;">// Single atomic transaction</span>
<span style="color:#64748b;">// Zero private keys needed</span>

<span style="color:#38bdf8;">invoke_signed</span>([
  <span style="color:#34d399;">jupiter</span>::<span style="color:#c084fc;">swap</span>(SOL -> USDC),
  <span style="color:#34d399;">raydium</span>::<span style="color:#c084fc;">add_liquidity</span>(USDC-SOL),
  <span style="color:#34d399;">marinade</span>::<span style="color:#c084fc;">stake</span>(remaining_SOL),
], <span style="color:#fbbf24;">pda_seeds</span>);

<span style="color:#64748b;">// If ANY step fails -> everything reverts</span>
<span style="color:#64748b;">// No partial states. No stuck funds.</span>"""
generate_code_card(
    "CPI Composability",
    code_text2,
    os.path.join(OUT, "card_08.png"),
    "arctic",
    "atomic_swap.rs"
)

# Card 9: What We Shipped - Stats card
print("\n[9/10] What we shipped stats card...")
generate_stats_card(
    json.dumps([
        {"value": "33", "label": "MCP TOOLS"},
        {"value": "PDA", "label": "NATIVE WALLETS"},
        {"value": "100%", "label": "ON-CHAIN POLICIES"},
        {"value": "12ms", "label": "RESPONSE TIME"}
    ]),
    "Shipped code. Not pitch decks.",
    os.path.join(OUT, "card_09.png"),
    "neon"
)

# Card 10: CTA - Statement card
print("\n[10/10] CTA card...")
generate_statement_card(
    "The future of AI agents is on-chain",
    "PDA wallets are the guardrails. We built AgentWallet so you don't have to figure this out alone. agentwallet.fun",
    os.path.join(OUT, "card_10.png"),
    "obsidian"
)

print("\n" + "=" * 60)
print("ALL 10 CARDS GENERATED!")
print("=" * 60)

# Verify
import glob
cards = sorted(glob.glob(os.path.join(OUT, "card_*.png")))
print(f"\nFound {len(cards)} cards:")
for c in cards:
    size = os.path.getsize(c)
    print(f"  {os.path.basename(c)} - {size // 1024}KB")
