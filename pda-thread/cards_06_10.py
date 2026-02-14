"""Cards 6-10"""
from css import html

def card_06():
    return html(6,'''<div class="gp" style="top:-80px;left:200px;width:400px;height:400px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-p">COMPARISON</span></div>
<div class="t" style="font-size:34px;margin-bottom:20px">Ethereum vs <span class="p">Solana</span></div>
<div style="background:rgba(0,0,0,.3);border:1px solid rgba(99,102,241,.1);border-radius:14px;overflow:hidden">
<table style="width:100%;border-collapse:collapse;font-size:14px">
<tr style="border-bottom:2px solid rgba(99,102,241,.2)"><th style="padding:14px 20px;text-align:left;color:#64748b;font-family:'Space Grotesk',sans-serif;font-size:13px;width:28%">Feature</th><th style="padding:14px 20px;text-align:left;color:#94a3b8;font-family:'Space Grotesk',sans-serif;font-size:13px">Ethereum</th><th style="padding:14px 20px;text-align:left;color:#818cf8;font-family:'Space Grotesk',sans-serif;font-size:13px">Solana (PDAs)</th></tr>
<tr style="border-bottom:1px solid rgba(99,102,241,.08)"><td style="padding:12px 20px;color:#64748b">Architecture</td><td style="padding:12px 20px;color:#94a3b8">Smart contract wallets</td><td style="padding:12px 20px;color:#34d399">Native PDA accounts</td></tr>
<tr style="border-bottom:1px solid rgba(99,102,241,.08)"><td style="padding:12px 20px;color:#64748b">Deploy Cost</td><td style="padding:12px 20px;color:#f87171">$50-200 per wallet</td><td style="padding:12px 20px;color:#34d399">~$0.002 per PDA</td></tr>
<tr style="border-bottom:1px solid rgba(99,102,241,.08)"><td style="padding:12px 20px;color:#64748b">Tx Speed</td><td style="padding:12px 20px;color:#f87171">12-15 seconds</td><td style="padding:12px 20px;color:#34d399">400 milliseconds</td></tr>
<tr style="border-bottom:1px solid rgba(99,102,241,.08)"><td style="padding:12px 20px;color:#64748b">Tx Cost</td><td style="padding:12px 20px;color:#f87171">$2-50+</td><td style="padding:12px 20px;color:#34d399">$0.00025</td></tr>
<tr style="border-bottom:1px solid rgba(99,102,241,.08)"><td style="padding:12px 20px;color:#64748b">Key Model</td><td style="padding:12px 20px;color:#94a3b8">EOA + contract</td><td style="padding:12px 20px;color:#34d399">Keyless PDA</td></tr>
<tr style="border-bottom:1px solid rgba(99,102,241,.08)"><td style="padding:12px 20px;color:#64748b">Composability</td><td style="padding:12px 20px;color:#94a3b8">External calls</td><td style="padding:12px 20px;color:#34d399">Native CPI</td></tr>
<tr><td style="padding:12px 20px;color:#64748b">AI-Ready</td><td style="padding:12px 20px;color:#f87171">Requires ERC-4337</td><td style="padding:12px 20px;color:#34d399">Native since day 1</td></tr>
</table></div>
<div style="margin-top:18px;text-align:center;font-size:14px;color:#64748b">solana had programmable wallets <span class="p" style="font-weight:600">before ethereum even started building them</span></div>
</div>''')

def card_07():
    return html(7,'''<div class="gp" style="top:100px;right:-100px;width:400px;height:400px"></div><div class="gg" style="bottom:200px;left:-50px"></div>
<div class="c" style="justify-content:center;align-items:center;text-align:center">
<div style="margin-bottom:8px"><span class="tg tg-o">PERFORMANCE</span></div>
<div class="t" style="font-size:36px;margin-bottom:36px">Speed <span class="o">Matters</span></div>
<div style="display:flex;gap:60px;align-items:flex-end;margin-bottom:40px">
<div style="text-align:center">
<div class="m" style="font-size:14px;color:#f87171;margin-bottom:8px">Ethereum</div>
<div style="width:140px;height:280px;background:linear-gradient(to top,rgba(239,68,68,.25),rgba(239,68,68,.06));border:1px solid rgba(239,68,68,.2);border-radius:12px 12px 0 0;display:flex;align-items:center;justify-content:center;flex-direction:column">
<div class="t" style="font-size:52px;color:#f87171">12s</div>
<div style="font-size:12px;color:#64748b;margin-top:4px">per block</div></div></div>
<div style="text-align:center">
<div class="m" style="font-size:14px;color:#34d399;margin-bottom:8px">Solana</div>
<div style="width:140px;height:12px;background:linear-gradient(to top,rgba(16,185,129,.4),rgba(16,185,129,.15));border:1px solid rgba(16,185,129,.3);border-radius:12px 12px 0 0"></div>
<div class="t" style="font-size:36px;color:#34d399;margin-top:12px">400ms</div>
<div style="font-size:12px;color:#64748b;margin-top:2px">per slot</div></div></div>
<div style="display:flex;gap:24px;width:100%">
<div class="sb" style="flex:1"><div class="sv o">30x</div><div class="sl">faster confirmation</div></div>
<div class="sb" style="flex:1"><div class="sv g">$0.00025</div><div class="sl">per transaction</div></div>
<div class="sb" style="flex:1"><div class="sv p">65,000</div><div class="sl">TPS theoretical</div></div>
</div></div>''')

def card_08():
    return html(8,'''<div class="gp" style="top:-50px;left:-50px"></div><div class="gg" style="bottom:50px;right:-50px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">AGENTWALLET FEATURE</span></div>
<div class="t" style="font-size:34px;margin-bottom:18px">PDA <span class="g">Spend Policies</span></div>
<div class="cb" style="margin-bottom:16px;font-size:12px"><div><span class="cm">// On-chain spend policy enforcement</span></div><div style="margin-top:4px"><span class="kw">pub struct</span> <span class="ty">SpendPolicy</span> {</div><div style="padding-left:20px">max_per_tx: <span class="ty">u64</span>,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="cm">// max lamports per tx</span></div><div style="padding-left:20px">daily_limit: <span class="ty">u64</span>,&nbsp;&nbsp;&nbsp;<span class="cm">// 24h rolling cap</span></div><div style="padding-left:20px">allowed_tokens: <span class="ty">Vec&lt;Pubkey&gt;</span>,</div><div style="padding-left:20px">allowed_dests: <span class="ty">Vec&lt;Pubkey&gt;</span>,</div><div style="padding-left:20px">require_multisig: <span class="ty">bool</span>,</div><div style="padding-left:20px">cooldown_secs: <span class="ty">u32</span>,</div><div>}</div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
<div style="background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.12);border-radius:10px;padding:14px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#34d399;margin-bottom:4px">Per-Token Limits</div><div style="font-size:12px;color:#94a3b8">set max amounts for SOL, USDC, or any SPL token independently</div></div>
<div style="background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.12);border-radius:10px;padding:14px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#818cf8;margin-bottom:4px">Destination Allowlist</div><div style="font-size:12px;color:#94a3b8">agent can only send to pre-approved addresses</div></div>
<div style="background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.12);border-radius:10px;padding:14px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#fbbf24;margin-bottom:4px">Time-Based Cooldowns</div><div style="font-size:12px;color:#94a3b8">enforce minimum delay between consecutive transactions</div></div>
<div style="background:rgba(236,72,153,.06);border:1px solid rgba(236,72,153,.12);border-radius:10px;padding:14px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#f472b6;margin-bottom:4px">Emergency Freeze</div><div style="font-size:12px;color:#94a3b8">owner can freeze the PDA instantly. one instruction.</div></div>
</div>
<div style="text-align:center;font-size:13px;color:#64748b">all policies enforced at the <span class="g" style="font-weight:600">VM level</span> -- not by the agent, not by a server</div>
</div>''')

def card_09():
    return html(9,'''<div class="gp" style="top:-80px;right:-80px;width:350px;height:350px"></div><div class="gpk" style="bottom:100px;left:-50px;width:250px;height:250px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-o">USE CASES</span></div>
<div class="t" style="font-size:36px;margin-bottom:24px">Real-World <span class="o">Applications</span></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
<div style="background:rgba(99,102,241,.05);border:1px solid rgba(99,102,241,.12);border-radius:14px;padding:24px">
<div style="font-size:28px;margin-bottom:8px;color:#818cf8">&#x25B2;</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:18px;color:#f1f5f9;margin-bottom:8px">DeFi Agents</div>
<div style="font-size:13px;color:#94a3b8;line-height:1.6">auto-rebalance portfolios, execute DCA strategies, manage yield farming -- all with spend limits and approved protocols only</div></div>
<div style="background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.12);border-radius:14px;padding:24px">
<div style="font-size:28px;margin-bottom:8px;color:#34d399">&#x25CF;</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:18px;color:#f1f5f9;margin-bottom:8px">DAO Treasury</div>
<div style="font-size:13px;color:#94a3b8;line-height:1.6">AI agents manage DAO funds with on-chain policies. multisig approval for large transfers, auto-pay for recurring ops</div></div>
<div style="background:rgba(245,158,11,.05);border:1px solid rgba(245,158,11,.12);border-radius:14px;padding:24px">
<div style="font-size:28px;margin-bottom:8px;color:#fbbf24">&#x25C6;</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:18px;color:#f1f5f9;margin-bottom:8px">Gaming</div>
<div style="font-size:13px;color:#94a3b8;line-height:1.6">NPC wallets with PDA-controlled inventories. in-game economies with real token constraints. no exploits.</div></div>
<div style="background:rgba(236,72,153,.05);border:1px solid rgba(236,72,153,.12);border-radius:14px;padding:24px">
<div style="font-size:28px;margin-bottom:8px;color:#f472b6">&#x25A0;</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:18px;color:#f1f5f9;margin-bottom:8px">NFT Commerce</div>
<div style="font-size:13px;color:#94a3b8;line-height:1.6">agents that buy, sell, and trade NFTs autonomously. bid on drops, list at target prices, manage royalty flows</div></div>
</div></div>''')

def card_10():
    return html(10,'''<div class="gp" style="top:100px;left:-100px;width:400px;height:400px"></div><div class="gg" style="bottom:-50px;right:100px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-p">ARCHITECTURE</span></div>
<div class="t" style="font-size:34px;margin-bottom:24px">AI Agent Wallet <span class="p">Architecture</span></div>
<div style="display:flex;flex-direction:column;gap:16px;align-items:center">
<!-- Layer 1: User -->
<div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.2);border-radius:12px;padding:16px 40px;text-align:center;width:300px">
<div class="m" style="font-size:11px;color:#64748b">LAYER 1</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#818cf8;margin-top:4px">Human Owner</div>
<div style="font-size:12px;color:#64748b;margin-top:2px">sets policies + approves agents</div></div>
<div style="color:#475569;font-size:20px">|</div>
<!-- Layer 2: Program -->
<div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:12px;padding:16px 40px;text-align:center;width:500px">
<div class="m" style="font-size:11px;color:#64748b">LAYER 2</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#34d399;margin-top:4px">AgentWallet Program (on-chain)</div>
<div style="font-size:12px;color:#64748b;margin-top:2px">enforces spend policies | signs via PDA | emits audit logs</div></div>
<div style="color:#475569;font-size:20px">|</div>
<!-- Layer 3: PDAs -->
<div style="display:flex;gap:16px">
<div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);border-radius:12px;padding:14px 20px;text-align:center">
<div class="m" style="font-size:10px;color:#64748b">PDA</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#fbbf24;margin-top:2px">Agent A Wallet</div></div>
<div style="background:rgba(236,72,153,.08);border:1px solid rgba(236,72,153,.2);border-radius:12px;padding:14px 20px;text-align:center">
<div class="m" style="font-size:10px;color:#64748b">PDA</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#f472b6;margin-top:2px">Agent B Wallet</div></div>
<div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.2);border-radius:12px;padding:14px 20px;text-align:center">
<div class="m" style="font-size:10px;color:#64748b">PDA</div>
<div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#818cf8;margin-top:2px">Agent C Wallet</div></div></div>
<div style="color:#475569;font-size:20px">|</div>
<!-- Layer 4: DeFi -->
<div style="display:flex;gap:12px">
<div style="background:rgba(0,0,0,.3);border:1px solid rgba(99,102,241,.1);border-radius:10px;padding:10px 16px;text-align:center"><div class="m" style="font-size:11px;color:#64748b">Jupiter</div></div>
<div style="background:rgba(0,0,0,.3);border:1px solid rgba(99,102,241,.1);border-radius:10px;padding:10px 16px;text-align:center"><div class="m" style="font-size:11px;color:#64748b">Raydium</div></div>
<div style="background:rgba(0,0,0,.3);border:1px solid rgba(99,102,241,.1);border-radius:10px;padding:10px 16px;text-align:center"><div class="m" style="font-size:11px;color:#64748b">Marinade</div></div>
<div style="background:rgba(0,0,0,.3);border:1px solid rgba(99,102,241,.1);border-radius:10px;padding:10px 16px;text-align:center"><div class="m" style="font-size:11px;color:#64748b">Tensor</div></div>
<div style="background:rgba(0,0,0,.3);border:1px solid rgba(99,102,241,.1);border-radius:10px;padding:10px 16px;text-align:center"><div class="m" style="font-size:11px;color:#64748b">Orca</div></div></div>
</div></div>''')
