"""Cards 11-15"""
from css import html

def card_11():
    return html(11,'''<div class="gp" style="top:-80px;left:-80px;width:350px;height:350px"></div><div class="gpk" style="bottom:100px;right:-50px;width:300px;height:300px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">SECURITY</span></div>
<div class="t" style="font-size:36px;margin-bottom:24px">Why PDAs Are <span class="g">Unhackable</span></div>
<div style="display:flex;flex-direction:column;gap:14px">
<div style="background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.1);border-radius:12px;padding:18px;display:flex;gap:14px;align-items:flex-start">
<div style="width:40px;height:40px;background:rgba(16,185,129,.15);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0"><div class="m" style="font-size:16px;color:#34d399;font-weight:700">1</div></div>
<div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:15px;color:#f1f5f9;margin-bottom:4px">No Private Key to Steal</div><div style="font-size:13px;color:#94a3b8;line-height:1.5">the address is mathematically off the ed25519 curve. no key exists -- not in memory, not in a file, not anywhere.</div></div></div>
<div style="background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.1);border-radius:12px;padding:18px;display:flex;gap:14px;align-items:flex-start">
<div style="width:40px;height:40px;background:rgba(16,185,129,.15);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0"><div class="m" style="font-size:16px;color:#34d399;font-weight:700">2</div></div>
<div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:15px;color:#f1f5f9;margin-bottom:4px">Program-Only Signing</div><div style="font-size:13px;color:#94a3b8;line-height:1.5">only the owning program can invoke_signed for its PDAs. the Solana runtime itself enforces this -- not application code.</div></div></div>
<div style="background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.1);border-radius:12px;padding:18px;display:flex;gap:14px;align-items:flex-start">
<div style="width:40px;height:40px;background:rgba(16,185,129,.15);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0"><div class="m" style="font-size:16px;color:#34d399;font-weight:700">3</div></div>
<div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:15px;color:#f1f5f9;margin-bottom:4px">Deterministic Derivation</div><div style="font-size:13px;color:#94a3b8;line-height:1.5">same seeds always derive the same PDA. no randomness, no surprises. verifiable by anyone, anytime.</div></div></div>
<div style="background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.1);border-radius:12px;padding:18px;display:flex;gap:14px;align-items:flex-start">
<div style="width:40px;height:40px;background:rgba(16,185,129,.15);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0"><div class="m" style="font-size:16px;color:#34d399;font-weight:700">4</div></div>
<div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:15px;color:#f1f5f9;margin-bottom:4px">Immutable On-Chain Logic</div><div style="font-size:13px;color:#94a3b8;line-height:1.5">the program's rules can't be changed by the agent. code is law, enforced by 1000+ validators.</div></div></div>
</div></div>''')

def card_12():
    return html(12,'''<div class="gp" style="top:50px;right:-100px;width:400px;height:400px"></div><div class="gg" style="bottom:-50px;left:50px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-p">COMPOSABILITY</span></div>
<div class="t" style="font-size:34px;margin-bottom:20px">Cross-Program <span class="p">Invocation</span></div>
<div style="font-size:15px;color:#94a3b8;line-height:1.6;margin-bottom:20px">CPIs let PDAs interact with any Solana program in a single atomic transaction. this is the secret sauce that makes agent wallets composable.</div>
<div class="cb" style="margin-bottom:20px;font-size:12px"><div><span class="cm">// Agent swaps USDC->SOL via Jupiter in one tx</span></div><div style="margin-top:4px"><span class="fn">invoke_signed</span>(</div><div style="padding-left:20px">&amp;<span class="fn">jupiter_swap_ix</span>(</div><div style="padding-left:40px">agent_pda,&nbsp;&nbsp;&nbsp;&nbsp;<span class="cm">// source (PDA)</span></div><div style="padding-left:40px">usdc_mint,&nbsp;&nbsp;&nbsp;&nbsp;<span class="cm">// input token</span></div><div style="padding-left:40px">sol_mint,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="cm">// output token</span></div><div style="padding-left:40px">amount,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="cm">// within policy limit</span></div><div style="padding-left:20px">),</div><div style="padding-left:20px">&amp;[&amp;agent_pda_seeds],&nbsp;<span class="cm">// PDA signs</span></div><div>);</div></div>
<div style="display:flex;gap:12px;text-align:center">
<div style="flex:1;background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.1);border-radius:10px;padding:14px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:28px;color:#818cf8">1</div><div style="font-size:12px;color:#64748b;margin-top:4px">single transaction</div></div>
<div style="flex:1;background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.1);border-radius:10px;padding:14px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:28px;color:#34d399">0</div><div style="font-size:12px;color:#64748b;margin-top:4px">private keys needed</div></div>
<div style="flex:1;background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.1);border-radius:10px;padding:14px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:28px;color:#fbbf24">ANY</div><div style="font-size:12px;color:#64748b;margin-top:4px">program composable</div></div>
</div></div>''')

def card_13():
    return html(13,'''<div class="gp" style="top:-50px;left:200px;width:400px;height:400px"></div><div class="gg" style="bottom:100px;right:-80px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">WHAT WE BUILT</span></div>
<div class="t" style="font-size:36px;margin-bottom:28px"><span class="g">AgentWallet</span> Protocol</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px">
<div class="sb"><div class="sv p">33</div><div class="sl">MCP tools</div></div>
<div class="sb"><div class="sv g">12ms</div><div class="sl">avg response</div></div>
<div class="sb"><div class="sv o">100%</div><div class="sl">on-chain</div></div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px">
<div style="background:rgba(99,102,241,.05);border:1px solid rgba(99,102,241,.1);border-radius:12px;padding:16px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#818cf8;margin-bottom:6px">PDA Wallet Engine</div><div style="font-size:12px;color:#94a3b8;line-height:1.5">create, fund, and manage agent wallets with granular spend policies</div></div>
<div style="background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.1);border-radius:12px;padding:16px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#34d399;margin-bottom:6px">DeFi Integration</div><div style="font-size:12px;color:#94a3b8;line-height:1.5">Jupiter swaps, Raydium pools, staking -- all via CPI from agent PDAs</div></div>
<div style="background:rgba(245,158,11,.05);border:1px solid rgba(245,158,11,.1);border-radius:12px;padding:16px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#fbbf24;margin-bottom:6px">Token Management</div><div style="font-size:12px;color:#94a3b8;line-height:1.5">create SPL tokens, manage supply, set metadata -- all agent-controlled</div></div>
<div style="background:rgba(236,72,153,.05);border:1px solid rgba(236,72,153,.1);border-radius:12px;padding:16px"><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#f472b6;margin-bottom:6px">MCP Server</div><div style="font-size:12px;color:#94a3b8;line-height:1.5">plug into GPT or any AI via Model Context Protocol</div></div>
</div>
<div style="text-align:center;font-size:14px;color:#64748b">the most comprehensive AI wallet toolkit on <span class="p" style="font-weight:600">Solana</span></div>
</div>''')

def card_14():
    return html(14,'''<div class="gp" style="top:-50px;right:-50px;width:350px;height:350px"></div><div class="gpk" style="bottom:200px;left:-80px;width:300px;height:300px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-p">RECOGNITION</span></div>
<div class="t" style="font-size:36px;margin-bottom:28px">Co-signed by <span class="p">toly</span></div>
<div style="display:flex;flex-direction:column;gap:20px">
<div style="background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.15);border-radius:14px;padding:24px;position:relative">
<div style="position:absolute;top:16px;right:20px;font-size:32px;color:rgba(99,102,241,.15);font-family:'Space Grotesk',sans-serif;font-weight:700">"</div>
<div style="font-size:15px;color:#94a3b8;line-height:1.6;margin-bottom:12px;font-style:italic">"this is a good explanation of PDAs"</div>
<div style="display:flex;align-items:center;gap:10px"><div style="width:36px;height:36px;background:rgba(99,102,241,.2);border-radius:50%;display:flex;align-items:center;justify-content:center"><div class="m" style="font-size:14px;color:#818cf8;font-weight:700">toly</div></div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:13px;color:#f1f5f9">@toly</div><div style="font-size:11px;color:#64748b">Co-founder, Solana Labs</div></div></div></div>
<div style="background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.15);border-radius:14px;padding:24px;position:relative">
<div style="position:absolute;top:16px;right:20px;font-size:32px;color:rgba(16,185,129,.15);font-family:'Space Grotesk',sans-serif;font-weight:700">"</div>
<div style="font-size:15px;color:#94a3b8;line-height:1.6;margin-bottom:12px;font-style:italic">"quoted twice. 44K+ impressions. the thread that caught Solana's attention."</div>
<div style="display:flex;align-items:center;gap:10px"><div style="width:36px;height:36px;background:rgba(16,185,129,.2);border-radius:50%;display:flex;align-items:center;justify-content:center"><div class="m" style="font-size:11px;color:#34d399;font-weight:700">mike</div></div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:13px;color:#f1f5f9">@mikemaccana</div><div style="font-size:11px;color:#64748b">Solana DevRel</div></div></div></div>
</div>
<div style="display:flex;gap:20px;margin-top:24px;justify-content:center">
<div class="sb"><div class="sv p">44K+</div><div class="sl">impressions</div></div>
<div class="sb"><div class="sv g">2x</div><div class="sl">toly quotes</div></div>
<div class="sb"><div class="sv o">1x</div><div class="sl">DevRel quote</div></div>
</div></div>''')

def card_15():
    return html(15,'''<div class="gp" style="top:-100px;left:-100px;width:400px;height:400px"></div><div class="gg" style="bottom:-80px;right:-80px;width:350px;height:350px"></div><div class="gpk" style="top:400px;right:100px;width:300px;height:300px"></div>
<div class="c" style="justify-content:center;align-items:center;text-align:center">
<div style="margin-bottom:20px"><span class="tg tg-g">JOIN THE REVOLUTION</span></div>
<div class="t" style="font-size:46px;margin-bottom:16px">Build With<br><span class="g">AgentWallet</span></div>
<div style="width:80px;height:3px;background:linear-gradient(90deg,#6366f1,#10b981);margin:16px auto;border-radius:2px"></div>
<div style="font-size:17px;color:#94a3b8;max-width:550px;margin-bottom:36px;line-height:1.6">the future of AI agents is on-chain.<br>PDAs make it secure. we make it easy.</div>
<div style="display:flex;gap:16px;margin-bottom:32px">
<div style="background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:12px;padding:18px 36px;text-align:center">
<div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:20px;color:#fff">agentwallet.fun</div>
<div style="font-size:12px;color:rgba(255,255,255,.6);margin-top:4px">try it now</div></div>
<div style="background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.3);border-radius:12px;padding:18px 36px;text-align:center">
<div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:20px;color:#34d399">@agentwallet_pro</div>
<div style="font-size:12px;color:rgba(52,211,153,.6);margin-top:4px">follow for updates</div></div>
</div>
<div style="display:flex;gap:20px">
<div class="sb" style="padding:14px 24px"><div class="sv" style="font-size:24px;color:#818cf8">33 MCP tools</div></div>
<div class="sb" style="padding:14px 24px"><div class="sv" style="font-size:24px;color:#34d399">PDA-native</div></div>
<div class="sb" style="padding:14px 24px"><div class="sv" style="font-size:24px;color:#fbbf24">open source</div></div>
</div>
</div>''')
