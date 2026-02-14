"""Cards 1-5"""
from css import html

def card_01():
    return html(1,'''<div class="gp" style="top:-100px;left:-100px"></div><div class="gg" style="bottom:-80px;right:-80px"></div><div class="gpk" style="top:300px;right:200px;width:350px;height:350px"></div>
<div class="c" style="justify-content:center;align-items:center;text-align:center">
<div style="margin-bottom:24px"><span class="tg tg-p">DEEP DIVE THREAD</span></div>
<div class="t" style="font-size:52px;margin-bottom:16px">The Complete Guide to<br><span class="p">Solana PDAs</span></div>
<div style="width:80px;height:3px;background:linear-gradient(90deg,#6366f1,#10b981);margin:20px auto;border-radius:2px"></div>
<div style="font-size:18px;color:#94a3b8;max-width:600px;margin-bottom:32px;line-height:1.6">Program Derived Addresses explained from first principles.<br>Why they matter for AI agents, wallets, and the future of Solana.</div>
<div style="display:flex;gap:24px;margin-top:12px">
<div style="text-align:center"><div class="m" style="font-size:28px;font-weight:700;color:#6366f1">15</div><div class="m" style="font-size:11px;color:#64748b">TWEETS</div></div>
<div style="width:1px;background:rgba(99,102,241,.2)"></div>
<div style="text-align:center"><div class="m" style="font-size:28px;font-weight:700;color:#10b981">5 min</div><div class="m" style="font-size:11px;color:#64748b">READ TIME</div></div>
<div style="width:1px;background:rgba(99,102,241,.2)"></div>
<div style="text-align:center"><div class="m" style="font-size:28px;font-weight:700;color:#ec4899">100%</div><div class="m" style="font-size:11px;color:#64748b">ON-CHAIN</div></div>
</div></div>''')

def card_02():
    return html(2,'''<div class="gp" style="top:-50px;right:-50px"></div><div class="gg" style="bottom:100px;left:-80px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-p">FUNDAMENTALS</span></div>
<div class="t" style="font-size:38px;margin-bottom:24px">What is a <span class="p">PDA</span>?</div>
<div style="display:flex;gap:20px;margin-bottom:22px">
<div style="flex:1;background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);border-radius:16px;padding:22px">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;color:#f87171;margin-bottom:14px">Normal Wallet</div>
<div style="font-size:13px;color:#94a3b8;line-height:2.1"><div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Has a private key</div><div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Human signs txs</div><div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Key can be stolen</div><div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Full access or nothing</div><div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Single point of failure</div></div></div>
<div style="flex:1;background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.15);border-radius:16px;padding:22px">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;color:#34d399;margin-bottom:14px">PDA Wallet</div>
<div style="font-size:13px;color:#94a3b8;line-height:2.1"><div><span style="color:#34d399;font-weight:700">+</span> &nbsp;No private key exists</div><div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Program signs via CPI</div><div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Nothing to steal</div><div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Granular permissions</div><div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Programmatic control</div></div></div></div>
<div style="background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.12);border-radius:12px;padding:18px;text-align:center">
<div style="font-size:15px;color:#94a3b8;line-height:1.6">a PDA is an address <span class="p" style="font-weight:600">derived from a program</span> that sits off the ed25519 curve.<br>no human holds the key. <span class="g" style="font-weight:600">only code controls it.</span></div></div></div>''')

def card_03():
    return html(3,'''<div class="gp" style="top:200px;left:-100px"></div><div class="gg" style="bottom:-50px;right:100px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">TECHNICAL</span></div>
<div class="t" style="font-size:36px;margin-bottom:20px">How PDAs Are <span class="g">Derived</span></div>
<div class="cb" style="margin-bottom:20px"><div><span class="cm">// Deriving a PDA in Rust (Anchor)</span></div><div style="margin-top:6px"><span class="kw">let</span> (pda, bump) = <span class="fn">Pubkey::find_program_address</span>(</div><div style="padding-left:24px">&amp;[</div><div style="padding-left:48px"><span class="str">b"agent_wallet"</span>,</div><div style="padding-left:48px">owner.<span class="fn">key</span>().<span class="fn">as_ref</span>(),</div><div style="padding-left:24px">],</div><div style="padding-left:24px">program_id,</div><div>);</div></div>
<div style="display:flex;align-items:center;gap:12px;justify-content:center;margin-bottom:20px">
<div style="background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);border-radius:10px;padding:14px 16px;text-align:center"><div class="m" style="font-size:10px;color:#64748b">SEEDS</div><div class="m" style="font-size:12px;color:#818cf8;margin-top:4px">"agent_wallet"<br>+ owner_key</div></div>
<div class="m" style="font-size:18px;color:#475569">+</div>
<div style="background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);border-radius:10px;padding:14px 16px;text-align:center"><div class="m" style="font-size:10px;color:#64748b">PROGRAM ID</div><div class="m" style="font-size:12px;color:#fbbf24;margin-top:4px">AgentWallet<br>Program</div></div>
<div class="m" style="font-size:18px;color:#475569">=</div>
<div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);border-radius:10px;padding:14px 16px;text-align:center"><div class="m" style="font-size:10px;color:#64748b">OUTPUT</div><div class="m" style="font-size:12px;color:#34d399;margin-top:4px">PDA Address<br>+ bump seed</div></div></div>
<div style="background:rgba(0,0,0,.3);border-radius:10px;padding:14px 18px;text-align:center"><div class="m" style="font-size:12px;color:#64748b">sha256(seeds + program_id + "ProgramDerivedAddress") <span class="pk">--&gt;</span> must NOT be on ed25519 curve</div></div></div>''')

def card_04():
    return html(4,'''<div class="gpk" style="top:-50px;right:100px;width:300px;height:300px"></div><div class="gp" style="bottom:100px;left:-50px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-r">THE PROBLEM</span></div>
<div class="t" style="font-size:36px;margin-bottom:24px">Why Private Keys<br><span class="pk">Kill AI Agents</span></div>
<div style="display:flex;flex-direction:column;gap:12px">
<div class="li"><div class="lic lr">1</div><div><div class="lt">Key Exposure</div><div class="ld">AI agent holds raw private key in memory. one exploit = drained wallet.</div></div></div>
<div class="li"><div class="lic lr">2</div><div><div class="lt">No Spending Limits</div><div class="ld">private key = god mode. no per-tx limits, daily caps, or allowlists.</div></div></div>
<div class="li"><div class="lic lr">3</div><div><div class="lt">Irrevocable Access</div><div class="ld">can't revoke agent access without moving all funds to a new wallet.</div></div></div>
<div class="li"><div class="lic lr">4</div><div><div class="lt">No Audit Trail</div><div class="ld">agent signs like the owner. impossible to distinguish human vs AI actions.</div></div></div>
<div class="li"><div class="lic lr">5</div><div><div class="lt">Multi-Agent Chaos</div><div class="ld">sharing one key across agents = distributed single point of failure.</div></div></div>
</div></div>''')

def card_05():
    return html(5,'''<div class="gg" style="top:-50px;left:100px;width:350px;height:350px"></div><div class="gp" style="bottom:-50px;right:100px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">THE SOLUTION</span></div>
<div class="t" style="font-size:36px;margin-bottom:24px">PDAs Fix <span class="g">Everything</span></div>
<div style="display:flex;flex-direction:column;gap:12px">
<div class="li"><div class="lic lg">1</div><div><div class="lt">Zero Key Exposure</div><div class="ld">no private key exists. the program signs via invoke_signed. nothing to leak.</div></div></div>
<div class="li"><div class="lic lg">2</div><div><div class="lt">On-Chain Spend Policies</div><div class="ld">per-token limits, daily caps, allowlisted destinations. enforced by the VM.</div></div></div>
<div class="li"><div class="lic lg">3</div><div><div class="lt">Instant Revocation</div><div class="ld">flip a boolean on-chain. agent loses access immediately. funds stay safe.</div></div></div>
<div class="li"><div class="lic lg">4</div><div><div class="lt">Full Audit Trail</div><div class="ld">every agent action routes through the program. on-chain logs show who did what.</div></div></div>
<div class="li"><div class="lic lg">5</div><div><div class="lt">Multi-Agent Native</div><div class="ld">each agent gets its own PDA with isolated permissions. composable, not chaotic.</div></div></div>
</div></div>''')
