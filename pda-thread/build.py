"""PDA Thread Builder - All 15 cards + thread.md"""
import asyncio, shutil
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(r"C:\Users\black\Desktop\agentwallet\pda-thread")
MEDIA = Path(r"C:\Users\black\.openclaw\media")

CSS = r"""@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1080px;background:linear-gradient(135deg,#05050a,#0a0a1a,#0d0d20);font-family:'Inter',sans-serif;color:#e2e8f0;overflow:hidden;position:relative}
body::before{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(99,102,241,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(99,102,241,.03) 1px,transparent 1px);background-size:40px 40px;z-index:0}
.ctl{position:absolute;width:60px;height:60px;z-index:5}
.ctl.tl{top:20px;left:20px;border-top:2px solid rgba(99,102,241,.4);border-left:2px solid rgba(99,102,241,.4)}
.ctl.tr{top:20px;right:20px;border-top:2px solid rgba(99,102,241,.4);border-right:2px solid rgba(99,102,241,.4)}
.ctl.bl{bottom:20px;left:20px;border-bottom:2px solid rgba(99,102,241,.4);border-left:2px solid rgba(99,102,241,.4)}
.ctl.br{bottom:20px;right:20px;border-bottom:2px solid rgba(99,102,241,.4);border-right:2px solid rgba(99,102,241,.4)}
.gp{position:absolute;width:300px;height:300px;background:radial-gradient(circle,rgba(99,102,241,.15),transparent 70%);border-radius:50%;z-index:0}
.gg{position:absolute;width:250px;height:250px;background:radial-gradient(circle,rgba(16,185,129,.12),transparent 70%);border-radius:50%;z-index:0}
.gpk{position:absolute;width:200px;height:200px;background:radial-gradient(circle,rgba(236,72,153,.1),transparent 70%);border-radius:50%;z-index:0}
.c{position:relative;z-index:2;width:100%;height:100%;padding:50px;display:flex;flex-direction:column}
.tn{position:absolute;top:32px;right:50px;font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600;color:rgba(99,102,241,.7);letter-spacing:2px;z-index:10}
.ft{position:absolute;bottom:30px;left:50px;right:50px;display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:13px;z-index:10}
.ft .h{color:rgba(99,102,241,.6)}.ft .s{color:rgba(16,185,129,.6)}
.sl{position:absolute;bottom:60px;left:50px;right:50px;height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,.2),rgba(16,185,129,.2),transparent);z-index:10}
.t{font-family:'Space Grotesk',sans-serif;font-weight:700;line-height:1.15}
.m{font-family:'JetBrains Mono',monospace}
.p{color:#6366f1}.g{color:#10b981}.pk{color:#ec4899}.o{color:#f59e0b}.d{color:#64748b}
.tg{display:inline-block;padding:4px 12px;border-radius:20px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:500}
.tg-p{background:rgba(99,102,241,.15);color:#818cf8;border:1px solid rgba(99,102,241,.2)}
.tg-g{background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.2)}
.tg-r{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.2)}
.tg-o{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.2)}
.tg-pk{background:rgba(236,72,153,.15);color:#f472b6;border:1px solid rgba(236,72,153,.2)}
.cb{background:rgba(0,0,0,.5);border:1px solid rgba(99,102,241,.15);border-radius:12px;padding:18px 22px;font-family:'JetBrains Mono',monospace;font-size:13px;line-height:1.7;color:#94a3b8}
.kw{color:#c084fc}.str{color:#34d399}.fn{color:#60a5fa}.cm{color:#475569}.ty{color:#f59e0b}
.li{display:flex;align-items:flex-start;gap:14px;margin-bottom:12px}
.li-i{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0;margin-top:2px}
.li-r{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.2)}
.li-g{background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.2)}
.li-p{background:rgba(99,102,241,.15);color:#818cf8;border:1px solid rgba(99,102,241,.2)}
.li-o{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.2)}
.sb{background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.12);border-radius:12px;padding:18px;text-align:center}
.sv{font-family:'Space Grotesk',sans-serif;font-size:34px;font-weight:700}
.sl2{font-size:12px;color:#64748b;margin-top:4px}
"""

F = '<div class="ctl tl"></div><div class="ctl tr"></div><div class="ctl bl"></div><div class="ctl br"></div><div class="tn">{n:02d}/15</div><div class="sl"></div><div class="ft"><span class="h">@Web3__Youth</span><span class="s">agentwallet.fun</span></div>'

def h(n,b): return f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{F.format(n=n)}{b}</body></html>'

CARDS = {}

CARDS[1] = h(1,'''<div class="gp" style="top:-100px;left:-100px"></div><div class="gg" style="bottom:-80px;right:-80px"></div><div class="gpk" style="top:300px;right:200px;width:350px;height:350px"></div>
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

CARDS[2] = h(2,'''<div class="gp" style="top:-50px;right:-50px"></div><div class="gg" style="bottom:100px;left:-80px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-p">FUNDAMENTALS</span></div>
<div class="t" style="font-size:38px;margin-bottom:24px">What is a <span class="p">PDA</span>?</div>
<div style="display:flex;gap:20px;margin-bottom:22px">
<div style="flex:1;background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);border-radius:16px;padding:22px">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;color:#f87171;margin-bottom:14px">Normal Wallet</div>
<div style="font-size:13px;color:#94a3b8;line-height:2.1"><div><span style="color:#f87171;font-weight:700">x</span> Has a private key</div><div><span style="color:#f87171;font-weight:700">x</span> Human signs txs</div><div><span style="color:#f87171;font-weight:700">x</span> Key can be stolen</div><div><span style="color:#f87171;font-weight:700">x</span> Full access or nothing</div><div><span style="color:#f87171;font-weight:700">x</span> Single point of failure</div></div>
</div>
<div style="flex:1;background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.15);border-radius:16px;padding:22px">
<div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;color:#34d399;margin-bottom:14px">PDA Wallet</div>
<div style="font-size:13px;color:#94a3b8;line-height:2.1"><div><span style="color:#34d399;font-weight:700">+</span> No private key exists</div><div><span style="color:#34d399;font-weight:700">+</span> Program signs via CPI</div><div><span style="color:#34d399;font-weight:700">+</span> Nothing to steal</div><div><span style="color:#34d399;font-weight:700">+</span> Granular permissions</div><div><span style="color:#34d399;font-weight:700">+</span> Programmatic control</div></div>
</div></div>
<div style="background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.12);border-radius:12px;padding:18px;text-align:center">
<div style="font-size:15px;color:#94a3b8;line-height:1.6">a PDA is an address <span class="p" style="font-weight:600">derived from a program</span> that sits off the ed25519 curve.<br>no human holds the key. <span class="g" style="font-weight:600">only code controls it.</span></div>
</div></div>''')

CARDS[3] = h(3,'''<div class="gp" style="top:200px;left:-100px"></div><div class="gg" style="bottom:-50px;right:100px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">TECHNICAL</span></div>
<div class="t" style="font-size:36px;margin-bottom:20px">How PDAs Are <span class="g">Derived</span></div>
<div class="cb" style="margin-bottom:20px"><div><span class="cm">// Deriving a PDA in Rust (Anchor)</span></div><div style="margin-top:6px"><span class="kw">let</span> (pda, bump) = <span class="fn">Pubkey::find_program_address</span>(</div><div style="padding-left:24px">&amp;[</div><div style="padding-left:48px"><span class="str">b"agent_wallet"</span>,</div><div style="padding-left:48px">owner.<span class="fn">key</span>().<span class="fn">as_ref</span>(),</div><div style="padding-left:24px">],</div><div style="padding-left:24px">program_id,</div><div>);</div></div>
<div style="display:flex;align-items:center;gap:12px;justify-content:center;margin-bottom:20px">
<div style="background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);border-radius:10px;padding:14px 16px;text-align:center"><div class="m" style="font-size:10px;color:#64748b">SEEDS</div><div class="m" style="font-size:12px;color:#818cf8;margin-top:4px">"agent_wallet"<br>+ owner_key</div></div>
<div class="m" style="font-size:18px;color:#475569">+</div>
<div style="background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);border-radius:10px;padding:14px 16px;text-align:center"><div class="m" style="font-size:10px;color:#64748b">PROGRAM ID</div><div class="m" style="font-size:12px;color:#fbbf24;margin-top:4px">AgentWallet<br>Program</div></div>
<div class="m" style="font-size:18px;color:#475569">=</div>
<div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);border-radius:10px;padding:14px 16px;text-align:center"><div class="m" style="font-size:10px;color:#64748b">OUTPUT</div><div class="m" style="font-size:12px;color:#34d399;margin-top:4px">PDA Address<br>+ bump seed</div></div>
</div>
<div style="background:rgba(0,0,0,.3);border-radius:10px;padding:14px 18px;text-align:center"><div class="m" style="font-size:12px;color:#64748b">sha256(seeds + program_id + "ProgramDerivedAddress") <span class="pk">--&gt;</span> must NOT be on ed25519 curve</div></div>
</div>''')

CARDS[4] = h(4,'''<div class="gpk" style="top:-50px;right:100px;width:300px;height:300px"></div><div class="gp" style="bottom:100px;left:-50px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-r">THE PROBLEM</span></div>
<div class="t" style="font-size:36px;margin-bottom:24px">Why Private Keys<br><span class="pk">Kill AI Agents</span></div>
<div style="display:flex;flex-direction:column;gap:12px">
<div class="li"><div class="li-i li-r">1</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Key Exposure</div><div style="font-size:13px;color:#94a3b8">AI agent holds raw private key in memory. one exploit = drained wallet.</div></div></div>
<div class="li"><div class="li-i li-r">2</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">No Spending Limits</div><div style="font-size:13px;color:#94a3b8">private key = god mode. no per-tx limits, daily caps, or allowlists.</div></div></div>
<div class="li"><div class="li-i li-r">3</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Irrevocable Access</div><div style="font-size:13px;color:#94a3b8">can't revoke agent access without moving all funds to a new wallet.</div></div></div>
<div class="li"><div class="li-i li-r">4</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">No Audit Trail</div><div style="font-size:13px;color:#94a3b8">agent signs like the owner. impossible to distinguish human vs AI actions.</div></div></div>
<div class="li"><div class="li-i li-r">5</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Multi-Agent Chaos</div><div style="font-size:13px;color:#94a3b8">sharing one key across agents = distributed single point of failure.</div></div></div>
</div></div>''')

CARDS[5] = h(5,'''<div class="gg" style="top:-50px;left:100px;width:350px;height:350px"></div><div class="gp" style="bottom:-50px;right:100px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">THE SOLUTION</span></div>
<div class="t" style="font-size:36px;margin-bottom:24px">PDAs Fix <span class="g">Everything</span></div>
<div style="display:flex;flex-direction:column;gap:12px">
<div class="li"><div class="li-i li-g">1</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Zero Key Exposure</div><div style="font-size:13px;color:#94a3b8">no private key exists. the program signs via invoke_signed. nothing to leak.</div></div></div>
<div class="li"><div class="li-i li-g">2</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">On-Chain Spend Policies</div><div style="font-size:13px;color:#94a3b8">per-token limits, daily caps, allowlisted destinations. enforced by the VM.</div></div></div>
<div class="li"><div class="li-i li-g">3</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Instant Revocation</div><div style="font-size:13px;color:#94a3b8">flip a boolean on-chain. agent loses access immediately. funds stay safe.</div></div></div>
<div class="li"><div class="li-i li-g">4</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Full Audit Trail</div><div style="font-size:13px;color:#94a3b8">every agent action routes through the program. on-chain logs show who did what.</div></div></div>
<div class="li"><div class="li-i li-g">5</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Multi-Agent Native</div><div style="font-size:13px;color:#94a3b8">each agent gets its own PDA with isolated permissions. composable, not chaotic.</div></div></div>
</div></div>''')

CARDS[6] = h(6,'''<div class="gp" style="top:-80px;left:200px;width:400px;height:400px"></div>
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

CARDS[7] = h(7,'''<div class="gp" style="top:100px;right:-100px;width:400px;height:400px"></div><div class="gg" style="bottom:200px;left:-50px"></div>
<div class="c" style="justify-content:center;align-items:center;text-align:center">
<div style="margin-bottom:8px"><span class="tg tg-o">PERFORMANCE</span></div>
<div class="t" style="font-size:36px;margin-bottom:36px">Speed <span class="o">Matters</span></div>
<div style="display:flex;gap:60px;align-items:flex-end;margin-bottom:36px">
<div style="text-align:center"><div class="m" style="font-size:15px;color:#f87171;margin-bottom:8px">12 seconds</div><div style="width:140px;height:280px;background:linear-gradient(to top,rgba(239,68,68,.25),rgba(239,68,68,.08));border:1px solid rgba(239,68,68,.25);border-radius:12px 12px 0 0;display:flex;align-items:center;justify-content:center"><div><div class="t" style="font-size:48px;color:#f87171">12s</div><div style="font-size:12px;color:#94a3b8;margin-top:4px">Ethereum</div></div></div></div>
<div style="text-align:center"><div class="m" style="font-size:15px;color:#34d399;margin-bottom:8px">400 milliseconds</div><div style="width:140px;height:28px;background:linear-gradient(to top,rgba(16,185,129,.25),rgba(16,185,129,.08));border:1px solid rgba(16,185,129,.25);border-radius:12px 12px 0 0;display:flex;align-items:center;justify-content:center"><div class="t" style="font-size:14px;color:#34d399">0.4s</div></div></div>
</div>
<div style="display:flex;gap:24px">
<div class="sb" style="flex:1"><div class="sv o">30x</div><div class="sl2">faster confirmation</div></div>
<div class="sb" style="flex:1"><div class="sv g">$0.00025</div><div class="sl2">per transaction</div></div>
<div class="sb" style="flex:1"><div class="sv p">65,000</div><div class="sl2">TPS theoretical</div></div>
</div>
</div>''')

CARDS[8] = h(8,'''<div class="gp" style="top:-50px;left:-50px"></div><div class="gg" style="bottom:50px;right:-50px"></div>
<div class="c">
<div style="margin-bottom:8px"><span class="tg tg-g">AGENTWALLET FEATURE</span></div>
<div class="t" style="font-size:34px;margin-bottom:20px">PDA <span class="g">Spend Policies</span></div>
<div class="cb" style="margin-bottom:18px;font-size:12.5px"><div><span class="cm">// On-chain spend policy enforcement</span></div><div style="margin-top:4px"><span class="kw">pub struct</span> <span class="ty">SpendPolicy</span> {</div><div style="padding-left:20px"><span class="kw">pub</span> max_per_tx: <span class="ty">u64</span>,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="cm">// max SOL per transaction</span></div><div style="padding-left:20px"><span class="kw">pub</span> daily_limit: <span class="ty">u64</span>,&nbsp;&nbsp;&nbsp;<span class="cm">// 24h rolling cap</span></div><div style="padding-left:20px"><span class="kw">pub</span> allowed_tokens: <span class="ty">Vec&lt;Pubkey&gt;</span>,</div><div style="padding-left:20px"><span class="kw">pub</span> allowed_dests: <span class="ty">Vec&lt;Pubkey&gt;</span>,</div><div style="padding-left:20px"><span class="kw">pub</span> require