"""
PDA Deep Dive Thread Generator - Complete
Generates 15 premium infographic cards (1080x1080) + thread.md
"""

import asyncio
import os
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(r"C:\Users\black\Desktop\agentwallet\pda-thread")
MEDIA_DIR = Path(r"C:\Users\black\.openclaw\media")

# ─── SHARED CSS ───
BASE_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1080px;background:linear-gradient(135deg,#05050a 0%,#0a0a1a 50%,#0d0d20 100%);font-family:'Inter',sans-serif;color:#e2e8f0;overflow:hidden;position:relative}
body::before{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(99,102,241,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(99,102,241,0.03) 1px,transparent 1px);background-size:40px 40px;z-index:0}
.corner-tl,.corner-tr,.corner-bl,.corner-br{position:absolute;width:60px;height:60px;z-index:5}
.corner-tl{top:20px;left:20px;border-top:2px solid rgba(99,102,241,0.4);border-left:2px solid rgba(99,102,241,0.4)}
.corner-tr{top:20px;right:20px;border-top:2px solid rgba(99,102,241,0.4);border-right:2px solid rgba(99,102,241,0.4)}
.corner-bl{bottom:20px;left:20px;border-bottom:2px solid rgba(99,102,241,0.4);border-left:2px solid rgba(99,102,241,0.4)}
.corner-br{bottom:20px;right:20px;border-bottom:2px solid rgba(99,102,241,0.4);border-right:2px solid rgba(99,102,241,0.4)}
.glow-purple{position:absolute;width:300px;height:300px;background:radial-gradient(circle,rgba(99,102,241,0.15) 0%,transparent 70%);border-radius:50%;z-index:0}
.glow-green{position:absolute;width:250px;height:250px;background:radial-gradient(circle,rgba(16,185,129,0.12) 0%,transparent 70%);border-radius:50%;z-index:0}
.glow-pink{position:absolute;width:200px;height:200px;background:radial-gradient(circle,rgba(236,72,153,0.10) 0%,transparent 70%);border-radius:50%;z-index:0}
.content{position:relative;z-index:2;width:100%;height:100%;padding:50px;display:flex;flex-direction:column}
.thread-num{position:absolute;top:32px;right:50px;font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600;color:rgba(99,102,241,0.7);letter-spacing:2px;z-index:10}
.footer{position:absolute;bottom:30px;left:50px;right:50px;display:flex;justify-content:space-between;align-items:center;font-family:'JetBrains Mono',monospace;font-size:13px;color:rgba(148,163,184,0.5);z-index:10}
.footer .handle{color:rgba(99,102,241,0.6)}
.footer .site{color:rgba(16,185,129,0.6)}
.sep-line{position:absolute;bottom:60px;left:50px;right:50px;height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,0.2),rgba(16,185,129,0.2),transparent);z-index:10}
.title{font-family:'Space Grotesk',sans-serif;font-weight:700;line-height:1.15}
.mono{font-family:'JetBrains Mono',monospace}
.body-text{font-family:'Inter',sans-serif;line-height:1.6}
.purple{color:#6366f1}.green{color:#10b981}.pink{color:#ec4899}.orange{color:#f59e0b}.dim{color:#64748b}.bright{color:#f1f5f9}
.tag{display:inline-block;padding:4px 12px;border-radius:20px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:500}
.tag-purple{background:rgba(99,102,241,0.15);color:#818cf8;border:1px solid rgba(99,102,241,0.2)}
.tag-green{background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.2)}
.tag-pink{background:rgba(236,72,153,0.15);color:#f472b6;border:1px solid rgba(236,72,153,0.2)}
.tag-orange{background:rgba(245,158,11,0.15);color:#fbbf24;border:1px solid rgba(245,158,11,0.2)}
.tag-red{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.2)}
.code-block{background:rgba(0,0,0,0.5);border:1px solid rgba(99,102,241,0.15);border-radius:12px;padding:20px 24px;font-family:'JetBrains Mono',monospace;font-size:14px;line-height:1.7;color:#94a3b8}
.code-block .kw{color:#c084fc}.code-block .str{color:#34d399}.code-block .fn{color:#60a5fa}.code-block .cm{color:#475569}.code-block .ty{color:#f59e0b}.code-block .num{color:#ec4899}
.list-item{display:flex;align-items:flex-start;gap:14px;margin-bottom:14px}
.li-icon{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0;margin-top:2px}
.li-red{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.2)}
.li-green{background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.2)}
.li-purple{background:rgba(99,102,241,0.15);color:#818cf8;border:1px solid rgba(99,102,241,0.2)}
.li-orange{background:rgba(245,158,11,0.15);color:#fbbf24;border:1px solid rgba(245,158,11,0.2)}
.stat-box{background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);border-radius:12px;padding:20px;text-align:center}
.stat-val{font-family:'Space Grotesk',sans-serif;font-size:36px;font-weight:700}
.stat-lbl{font-family:'Inter',sans-serif;font-size:13px;color:#64748b;margin-top:4px}
"""

FRAME = """<div class="corner-tl"></div><div class="corner-tr"></div><div class="corner-bl"></div><div class="corner-br"></div>
<div class="thread-num">{num:02d}/15</div>
<div class="sep-line"></div>
<div class="footer"><span class="handle">@Web3__Youth</span><span class="site">agentwallet.fun</span></div>"""

def html(num, body, extra_css=""):
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}\n{extra_css}</style></head><body>{FRAME.format(num=num)}{body}</body></html>'

# ─── CARD 01: TITLE ───
CARD_01 = html(1, """
<div class="glow-purple" style="top:-100px;left:-100px"></div>
<div class="glow-green" style="bottom:-80px;right:-80px"></div>
<div class="glow-pink" style="top:300px;right:200px;width:350px;height:350px"></div>
<div class="content" style="justify-content:center;align-items:center;text-align:center">
  <div style="margin-bottom:24px"><span class="tag tag-purple">DEEP DIVE THREAD</span></div>
  <div class="title" style="font-size:52px;margin-bottom:16px">The Complete Guide to<br><span class="purple">Solana PDAs</span></div>
  <div style="width:80px;height:3px;background:linear-gradient(90deg,#6366f1,#10b981);margin:20px auto;border-radius:2px"></div>
  <div class="body-text" style="font-size:18px;color:#94a3b8;max-width:600px;margin-bottom:32px">Program Derived Addresses explained from first principles.<br>Why they matter for AI agents, wallets, and the future of Solana.</div>
  <div style="display:flex;gap:24px;margin-top:12px">
    <div style="text-align:center"><div class="mono" style="font-size:28px;font-weight:700;color:#6366f1">15</div><div class="mono" style="font-size:11px;color:#64748b">TWEETS</div></div>
    <div style="width:1px;background:rgba(99,102,241,0.2)"></div>
    <div style="text-align:center"><div class="mono" style="font-size:28px;font-weight:700;color:#10b981">5 min</div><div class="mono" style="font-size:11px;color:#64748b">READ TIME</div></div>
    <div style="width:1px;background:rgba(99,102,241,0.2)"></div>
    <div style="text-align:center"><div class="mono" style="font-size:28px;font-weight:700;color:#ec4899">100%</div><div class="mono" style="font-size:11px;color:#64748b">ON-CHAIN</div></div>
  </div>
</div>""")

# ─── CARD 02: WHAT IS A PDA ───
CARD_02 = html(2, """
<div class="glow-purple" style="top:-50px;right:-50px"></div>
<div class="glow-green" style="bottom:100px;left:-80px"></div>
<div class="content">
  <div style="margin-bottom:8px"><span class="tag tag-purple">FUNDAMENTALS</span></div>
  <div class="title" style="font-size:38px;margin-bottom:24px">What is a <span class="purple">PDA</span>?</div>
  <div style="display:flex;gap:20px;margin-bottom:24px">
    <div style="flex:1;background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.15);border-radius:16px;padding:22px">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;color:#f87171;margin-bottom:14px">Normal Wallet</div>
      <div style="font-size:13px;color:#94a3b8;line-height:2">
        <div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Has a private key</div>
        <div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Human signs txs</div>
        <div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Key can be stolen</div>
        <div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Full access or nothing</div>
        <div><span style="color:#f87171;font-weight:700">x</span> &nbsp;Single point of failure</div>
      </div>
    </div>
    <div style="flex:1;background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.15);border-radius:16px;padding:22px">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;color:#34d399;margin-bottom:14px">PDA Wallet</div>
      <div style="font-size:13px;color:#94a3b8;line-height:2">
        <div><span style="color:#34d399;font-weight:700">+</span> &nbsp;No private key exists</div>
        <div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Program signs via CPI</div>
        <div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Nothing to steal</div>
        <div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Granular permissions</div>
        <div><span style="color:#34d399;font-weight:700">+</span> &nbsp;Programmatic control</div>
      </div>
    </div>
  </div>
  <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);border-radius:12px;padding:18px;text-align:center">
    <div class="body-text" style="font-size:15px;color:#94a3b8">a PDA is an address <span class="purple" style="font-weight:600">derived from a program</span> that sits off the ed25519 curve.<br>no human holds the key. <span class="green" style="font-weight:600">only code controls it.</span></div>
  </div>
</div>""")

# ─── CARD 03: HOW PDAS DERIVED ───
CARD_03 = html(3, """
<div class="glow-purple" style="top:200px;left:-100px"></div>
<div class="glow-green" style="bottom:-50px;right:100px"></div>
<div class="content">
  <div style="margin-bottom:8px"><span class="tag tag-green">TECHNICAL</span></div>
  <div class="title" style="font-size:36px;margin-bottom:20px">How PDAs Are <span class="green">Derived</span></div>
  <div class="code-block" style="margin-bottom:20px;font-size:13.5px">
    <div><span class="cm">// Deriving a PDA in Rust (Anchor)</span></div>
    <div style="margin-top:6px"><span class="kw">let</span> (pda, bump) = <span class="fn">Pubkey::find_program_address</span>(</div>
    <div style="padding-left:24px">&amp;[</div>
    <div style="padding-left:48px"><span class="str">b"agent_wallet"</span>,</div>
    <div style="padding-left:48px">owner.<span class="fn">key</span>().<span class="fn">as_ref</span>(),</div>
    <div style="padding-left:24px">],</div>
    <div style="padding-left:24px">program_id,</div>
    <div>);</div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;justify-content:center;margin-bottom:20px">
    <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);border-radius:10px;padding:14px 16px;text-align:center">
      <div class="mono" style="font-size:10px;color:#64748b">SEEDS</div>
      <div class="mono" style="font-size:12px;color:#818cf8;margin-top:4px">"agent_wallet"<br>+ owner_key</div>
    </div>
    <div class="mono" style="font-size:18px;color:#475569">+</div>
    <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.2);border-radius:10px;padding:14px 16px;text-align:center">
      <div class="mono" style="font-size:10px;color:#64748b">PROGRAM ID</div>
      <div class="mono" style="font-size:12px;color:#fbbf24;margin-top:4px">AgentWallet<br>Program</div>
    </div>
    <div class="mono" style="font-size:18px;color:#475569">=</div>
    <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);border-radius:10px;padding:14px 16px;text-align:center">
      <div class="mono" style="font-size:10px;color:#64748b">OUTPUT</div>
      <div class="mono" style="font-size:12px;color:#34d399;margin-top:4px">PDA Address<br>+ bump seed</div>
    </div>
  </div>
  <div style="background:rgba(0,0,0,0.3);border-radius:10px;padding:14px 18px;text-align:center">
    <div class="mono" style="font-size:12px;color:#64748b">sha256(seeds + program_id + "ProgramDerivedAddress") <span class="pink">--&gt;</span> must NOT be on ed25519 curve</div>
  </div>
</div>""")

# ─── CARD 04: THE PROBLEM ───
CARD_04 = html(4, """
<div class="glow-pink" style="top:-50px;right:100px;width:300px;height:300px"></div>
<div class="glow-purple" style="bottom:100px;left:-50px"></div>
<div class="content">
  <div style="margin-bottom:8px"><span class="tag tag-red">THE PROBLEM</span></div>
  <div class="title" style="font-size:36px;margin-bottom:24px">Why Private Keys<br><span class="pink">Kill AI Agents</span></div>
  <div style="display:flex;flex-direction:column;gap:14px">
    <div class="list-item"><div class="li-icon li-red">1</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Key Exposure</div><div style="font-size:13px;color:#94a3b8">AI agent holds raw private key in memory. one exploit = drained wallet.</div></div></div>
    <div class="list-item"><div class="li-icon li-red">2</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">No Spending Limits</div><div style="font-size:13px;color:#94a3b8">private key = god mode. no way to set per-tx limits, daily caps, or allowlists.</div></div></div>
    <div class="list-item"><div class="li-icon li-red">3</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Irrevocable Access</div><div style="font-size:13px;color:#94a3b8">can't revoke agent access without moving all funds to a new wallet.</div></div></div>
    <div class="list-item"><div class="li-icon li-red">4</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">No Audit Trail</div><div style="font-size:13px;color:#94a3b8">agent signs like the owner. impossible to distinguish human vs AI actions.</div></div></div>
    <div class="list-item"><div class="li-icon li-red">5</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Multi-Agent Chaos</div><div style="font-size:13px;color:#94a3b8">sharing one key across agents? congrats, you built a distributed single point of failure.</div></div></div>
  </div>
</div>""")

# ─── CARD 05: THE SOLUTION ───
CARD_05 = html(5, """
<div class="glow-green" style="top:-50px;left:100px;width:350px;height:350px"></div>
<div class="glow-purple" style="bottom:-50px;right:100px"></div>
<div class="content">
  <div style="margin-bottom:8px"><span class="tag tag-green">THE SOLUTION</span></div>
  <div class="title" style="font-size:36px;margin-bottom:24px">PDAs Fix <span class="green">Everything</span></div>
  <div style="display:flex;flex-direction:column;gap:14px">
    <div class="list-item"><div class="li-icon li-green">1</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Zero Key Exposure</div><div style="font-size:13px;color:#94a3b8">no private key exists. the program itself signs via invoke_signed. nothing to leak.</div></div></div>
    <div class="list-item"><div class="li-icon li-green">2</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">On-Chain Spend Policies</div><div style="font-size:13px;color:#94a3b8">per-token limits, daily caps, allowlisted destinations. enforced by the VM, not trust.</div></div></div>
    <div class="list-item"><div class="li-icon li-green">3</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Instant Revocation</div><div style="font-size:13px;color:#94a3b8">flip a boolean on-chain. agent loses access immediately. funds stay safe.</div></div></div>
    <div class="list-item"><div class="li-icon li-green">4</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Full Audit Trail</div><div style="font-size:13px;color:#94a3b8">every agent action routes through the program. on-chain logs show exactly who did what.</div></div></div>
    <div class="list-item"><div class="li-icon li-green">5</div><div><div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px">Multi-Agent Native</div><div style="font-size:13px;color:#94a3b8">each agent gets its own PDA with isolated permissions. composable, not chaotic.</div></div></div>
  </div>
</div>""")

# ─── CARD 06: ETH VS SOL ───
CARD_06 = html(6, """
<div class="glow-purple" style="top:-80px;left:200px;width:400px;height:400px"></div>
<div class="content">
  <div style="margin-bottom:8px"><span class="tag tag-purple">COMPARISON</span></div>
  <div class="title" style="font-size:34px;margin-bottom:20px">Ethereum vs <span class="purple">Solana</span></div>
  <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(99,102,241,0.1);border-radius:14px;overflow:hidden">
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <tr style="border-bottom:2px solid rgba(99,102,241,0.2)">
        <th style="padding:16px 20px;text-align:left;color:#64748b;font-family:'Space Grotesk',sans-serif;font-size:13px;width:28%">Feature</th>
        <th style="padding:16px 20px;text-align:left;color:#94a3b8;font-family:'Space Grotesk',sans-serif;font-size:13px">Ethereum</th>
        <th style="padding:16px 20px;text-align:left;color:#818cf8;font-family:'Space Grotesk',sans-serif;font-size:13px">Solana (PDAs)</th>
      </tr>
      <tr style="border-bottom:1px solid rgba(99,102,241,0.08)">
        <td style="padding:13px 20px;color:#64748b">Architecture</td>
        <td style="padding:13px 20px;color:#94a3b8">Smart contract wallets</td>
        <td style="padding:13px 20px;color:#34d399">Native PDA accounts</td>
      </tr>
      <tr style="border-bottom:1px solid rgba(99,102,241,0.08)">
        <td style="padding:13px 20px;color:#64748b">Deploy Cost</td>
        <td style="padding:13px 20px;color:#f87171">$50-200 per wallet</td>
        <td style="padding:13px 20px;color:#34d399">~$0.002 per PDA</td>
      </tr>
      <tr style="border-bottom:1px solid rgba(99,102,241,0.08)">
        <td style="padding:13px 20px;color:#64748b">Tx Speed</td>
        <td style="padding:13px 20px;color:#f87171">12-15 seconds</td>
        <td style="padding:13px 20px;color:#34d399">400 milliseconds</td>
      </tr>
      <tr style="border-bottom:1px solid rgba(99,102,241,0.08)">
        <td style="padding:13px 20px;color:#64748b">Tx Cost</td>
        <td style="padding:13px 20px;color:#f87171">$2-50+</td>
        <td style="padding:13px 20px;color:#34d399">$0.00025</td>
      </tr>
      <tr style="border-bottom:1px solid rgba(99,102,241,0.08)">
        <td style="padding:13px 20px;color:#64748b">Key Model</td>
        <td style="padding:13px 20px;color:#94a3b8">EOA + contract</td>
        <td style="padding:13px 20px;color:#34d399">Keyless PDA</td>
      </tr>
      <tr style="border-bottom:1px solid rgba(99,102,241,0.08)">
        <td style="padding:13px 20px;color:#64748b">Composability</td>
        <td style="padding:13px 20px;color:#94a3b8">External calls</td>
        <td style="padding:13px 20px;color:#34d399">Native CPI</td>
      </tr>
      <tr>
        <td style="padding:13px 20px;color:#64748b">AI-Ready</td>
        <td style="padding:13px 20px;color:#f87171">Requires AA (ERC-4337)</td>
        <td style="padding:13px 20px;color:#34d399">Native since day 1</td>
      </tr>
    </table>
  </div>
  <div style="margin-top:20px;text-align:center;font-size:14px;color:#64748b">solana had programmable wallets <span class="purple" style="font-weight:600">before ethereum even started building them</span></div>
</div>""")

# ─── CARD 07: SPEED ───
CARD_07 = html(7, """
<div class="glow-purple" style="top:100px;right:-100px;width:400px;height:400px"></div>
<div class="glow-green" style="bottom:200px;left:-50px"></div>
<div class="content" style="justify-content:center;align-items:center;text-align:center">
  <div style="margin-bottom:8px"><span class="tag tag-orange">PERFORMANCE</span></div>
  <div class="title" style="font-size:36px;margin-bottom:32px">Speed <span class="orange">Matters</span></div>
  <div style="display:flex;gap:40px;align-items:flex-end;margin-bottom:40px">
    <!-- ETH bar -->
    <div style="text-align:center">
      <div class="mono" style="font-size:14px;color:#f87171;margin-bottom:8px">12s</div>
      <div style="width:120px;height:300px;background:linear-gradient(to top,rgba(239,68,68,0.3),rgba(239,68,68,0.1));border:1px solid rgba(239,68,68,0.3);border-radius: