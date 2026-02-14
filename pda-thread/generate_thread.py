"""
PDA Deep Dive Thread Generator
Generates 15 premium infographic cards (1080x1080) + thread.md
"""

import asyncio
import os
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(r"C:\Users\black\Desktop\agentwallet\pda-thread")
MEDIA_DIR = Path(r"C:\Users\black\.openclaw\media")

# ─── SHARED CSS ───────────────────────────────────────────────────────
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  width: 1080px; height: 1080px;
  background: linear-gradient(135deg, #05050a 0%, #0a0a1a 50%, #0d0d20 100%);
  font-family: 'Inter', sans-serif;
  color: #e2e8f0;
  overflow: hidden;
  position: relative;
}

/* Grid overlay */
body::before {
  content: '';
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  z-index: 0;
}

/* Corner accents */
.corner-tl, .corner-tr, .corner-bl, .corner-br {
  position: absolute; width: 60px; height: 60px; z-index: 5;
}
.corner-tl { top: 20px; left: 20px; border-top: 2px solid rgba(99,102,241,0.4); border-left: 2px solid rgba(99,102,241,0.4); }
.corner-tr { top: 20px; right: 20px; border-top: 2px solid rgba(99,102,241,0.4); border-right: 2px solid rgba(99,102,241,0.4); }
.corner-bl { bottom: 20px; left: 20px; border-bottom: 2px solid rgba(99,102,241,0.4); border-left: 2px solid rgba(99,102,241,0.4); }
.corner-br { bottom: 20px; right: 20px; border-bottom: 2px solid rgba(99,102,241,0.4); border-right: 2px solid rgba(99,102,241,0.4); }

/* Glow orbs */
.glow-purple {
  position: absolute; width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
  border-radius: 50%; z-index: 0;
}
.glow-green {
  position: absolute; width: 250px; height: 250px;
  background: radial-gradient(circle, rgba(16,185,129,0.12) 0%, transparent 70%);
  border-radius: 50%; z-index: 0;
}
.glow-pink {
  position: absolute; width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(236,72,153,0.10) 0%, transparent 70%);
  border-radius: 50%; z-index: 0;
}

.content { position: relative; z-index: 2; width: 100%; height: 100%; padding: 50px; display: flex; flex-direction: column; }

/* Thread number badge */
.thread-num {
  position: absolute; top: 32px; right: 50px;
  font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 600;
  color: rgba(99,102,241,0.7); letter-spacing: 2px; z-index: 10;
}

/* Footer */
.footer {
  position: absolute; bottom: 30px; left: 50px; right: 50px;
  display: flex; justify-content: space-between; align-items: center;
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
  color: rgba(148,163,184,0.5); z-index: 10;
}
.footer .handle { color: rgba(99,102,241,0.6); }
.footer .site { color: rgba(16,185,129,0.6); }

/* Separator line */
.sep-line {
  position: absolute; bottom: 60px; left: 50px; right: 50px;
  height: 1px; background: linear-gradient(90deg, transparent, rgba(99,102,241,0.2), rgba(16,185,129,0.2), transparent);
  z-index: 10;
}

/* Typography */
.title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; line-height: 1.15; }
.mono { font-family: 'JetBrains Mono', monospace; }
.body-text { font-family: 'Inter', sans-serif; line-height: 1.6; }

/* Utility */
.purple { color: #6366f1; }
.green { color: #10b981; }
.pink { color: #ec4899; }
.orange { color: #f59e0b; }
.dim { color: #64748b; }
.bright { color: #f1f5f9; }

.tag {
  display: inline-block; padding: 4px 12px; border-radius: 20px;
  font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 500;
}
.tag-purple { background: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid rgba(99,102,241,0.2); }
.tag-green { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.2); }

/* Code block */
.code-block {
  background: rgba(0,0,0,0.5); border: 1px solid rgba(99,102,241,0.15);
  border-radius: 12px; padding: 20px 24px;
  font-family: 'JetBrains Mono', monospace; font-size: 14px;
  line-height: 1.7; color: #94a3b8;
}
.code-block .keyword { color: #c084fc; }
.code-block .string { color: #34d399; }
.code-block .func { color: #60a5fa; }
.code-block .comment { color: #475569; }
.code-block .type { color: #f59e0b; }
.code-block .num { color: #ec4899; }

/* Comparison table */
.compare-table { width: 100%; border-collapse: separate; border-spacing: 0; }
.compare-table th {
  padding: 14px 20px; font-family: 'Space Grotesk', sans-serif; font-size: 15px;
  font-weight: 600; text-align: left;
  border-bottom: 2px solid rgba(99,102,241,0.3);
}
.compare-table td {
  padding: 12px 20px; font-size: 14px; border-bottom: 1px solid rgba(99,102,241,0.08);
}
.compare-table tr:last-child td { border-bottom: none; }

/* Stat boxes */
.stat-box {
  background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.12);
  border-radius: 12px; padding: 20px; text-align: center;
}
.stat-value {
  font-family: 'Space Grotesk', sans-serif; font-size: 36px; font-weight: 700;
}
.stat-label {
  font-family: 'Inter', sans-serif; font-size: 13px; color: #64748b; margin-top: 4px;
}

/* List items */
.list-item {
  display: flex; align-items: flex-start; gap: 14px; margin-bottom: 14px;
}
.list-icon {
  width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center;
  justify-content: center; font-size: 14px; font-weight: 700; flex-shrink: 0; margin-top: 2px;
}
.list-icon-red { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.2); }
.list-icon-green { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.2); }
.list-icon-purple { background: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid rgba(99,102,241,0.2); }
"""

# ─── CARD HTML TEMPLATES ──────────────────────────────────────────────

def wrap(num, inner_html, extra_css=""):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}\n{extra_css}</style></head><body>
<div class="corner-tl"></div><div class="corner-tr"></div><div class="corner-bl"></div><div class="corner-br"></div>
<div class="thread-num">{num:02d}/15</div>
<div class="sep-line"></div>
<div class="footer"><span class="handle">@Web3__Youth</span><span class="site">agentwallet.fun</span></div>
{inner_html}
</body></html>"""

def card_01():
    return wrap(1, """
<div class="glow-purple" style="top:-100px;left:-100px;"></div>
<div class="glow-green" style="bottom:-80px;right:-80px;"></div>
<div class="glow-pink" style="top:300px;right:200px;width:350px;height:350px;"></div>
<div class="content" style="justify-content:center;align-items:center;text-align:center;">
  <div style="margin-bottom:24px;">
    <span class="tag tag-purple">DEEP DIVE THREAD</span>
  </div>
  <div class="title" style="font-size:52px;margin-bottom:16px;">
    The Complete Guide to<br><span class="purple">Solana PDAs</span>
  </div>
  <div style="width:80px;height:3px;background:linear-gradient(90deg,#6366f1,#10b981);margin:20px auto;border-radius:2px;"></div>
  <div class="body-text" style="font-size:18px;color:#94a3b8;max-width:600px;margin-bottom:32px;">
    Program Derived Addresses explained from first principles.<br>Why they matter for AI agents, wallets, and the future of Solana.
  </div>
  <div style="display:flex;gap:24px;margin-top:12px;">
    <div style="text-align:center;">
      <div class="mono" style="font-size:28px;font-weight:700;color:#6366f1;">15</div>
      <div class="mono" style="font-size:11px;color:#64748b;">TWEETS</div>
    </div>
    <div style="width:1px;background:rgba(99,102,241,0.2);"></div>
    <div style="text-align:center;">
      <div class="mono" style="font-size:28px;font-weight:700;color:#10b981;">5 min</div>
      <div class="mono" style="font-size:11px;color:#64748b;">READ TIME</div>
    </div>
    <div style="width:1px;background:rgba(99,102,241,0.2);"></div>
    <div style="text-align:center;">
      <div class="mono" style="font-size:28px;font-weight:700;color:#ec4899;">100%</div>
      <div class="mono" style="font-size:11px;color:#64748b;">ON-CHAIN</div>
    </div>
  </div>
</div>
""")

def card_02():
    return wrap(2, """
<div class="glow-purple" style="top:-50px;right:-50px;"></div>
<div class="glow-green" style="bottom:100px;left:-80px;"></div>
<div class="content">
  <div style="margin-bottom:8px;"><span class="tag tag-purple">FUNDAMENTALS</span></div>
  <div class="title" style="font-size:38px;margin-bottom:28px;">What is a <span class="purple">PDA</span>?</div>
  <div style="display:flex;gap:24px;margin-bottom:28px;">
    <!-- Normal Wallet -->
    <div style="flex:1;background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.15);border-radius:16px;padding:24px;">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:600;color:#f87171;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
        <span style="display:inline-flex;width:24px;height:24px;background:rgba(239,68,68,0.2);border-radius:6px;align-items:center;justify-content:center;font-size:12px;">!</span>
        Normal Wallet
      </div>
      <div style="font-size:13px;color:#94a3b8;line-height:1.8;">
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#f87171;font-weight:700;">-&gt;</span> Has a private key</div>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#f87171;font-weight:700;">-&gt;</span> Human signs transactions</div>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#f87171;font-weight:700;">-&gt;</span> Key can be stolen</div>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#f87171;font-weight:700;">-&gt;</span> Full access or no access</div>
        <div style="display:flex;align-items:center;gap:8px;"><span style="color:#f87171;font-weight:700;">-&gt;</span> Single point of failure</div>
      </div>
    </div>
    <!-- PDA -->
    <div style="flex:1;background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.15);border-radius:16px;padding:24px;">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:600;color:#34d399;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
        <span style="display:inline-flex;width:24px;height:24px;background:rgba(16,185,129,0.2);border-radius:6px;align-items:center;justify-content:center;font-size:12px;">#</span>
        PDA Wallet
      </div>
      <div style="font-size:13px;color:#94a3b8;line-height:1.8;">
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#34d399;font-weight:700;">-&gt;</span> No private key exists</div>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#34d399;font-weight:700;">-&gt;</span> Program signs via CPI</div>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#34d399;font-weight:700;">-&gt;</span> Nothing to steal</div>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;"><span style="color:#34d399;font-weight:700;">-&gt;</span> Granular permissions</div>
        <div style="display:flex;align-items:center;gap:8px;"><span style="color:#34d399;font-weight:700;">-&gt;</span> Programmatic control</div>
      </div>
    </div>
  </div>
  <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);border-radius:12px;padding:20px;text-align:center;">
    <div class="body-text" style="font-size:15px;color:#94a3b8;">
      a PDA is an address <span class="purple" style="font-weight:600;">derived from a program</span> that sits off the ed25519 curve.
      <br>no human holds the key. <span class="green" style="font-weight:600;">only code controls it.</span>
    </div>
  </div>
</div>
""")

def card_03():
    return wrap(3, """
<div class="glow-purple" style="top:200px;left:-100px;"></div>
<div class="glow-green" style="bottom:-50px;right:100px;"></div>
<div class="content">
  <div style="margin-bottom:8px;"><span class="tag tag-green">TECHNICAL</span></div>
  <div class="title" style="font-size:36px;margin-bottom:24px;">How PDAs Are <span class="green">Derived</span></div>
  <div class="code-block" style="margin-bottom:24px;">
    <div><span class="comment">// Deriving a PDA in Rust (Anchor)</span></div>
    <div style="margin-top:8px;"><span class="keyword">let</span> (pda, bump) = <span class="func">Pubkey::find_program_address</span>(</div>
    <div style="padding-left:24px;">&amp;[</div>
    <div style="padding-left:48px;"><span class="string">b"agent_wallet"</span>,</div>
    <div style="padding-left:48px;">owner.<span class="func">key</span>().<span class="func">as_ref</span>(),</div>
    <div style="padding-left:24px;">],</div>
    <div style="padding-left:24px;">program_id,</div>
    <div>);</div>
  </div>
  <div style="display:flex;align-items:center;gap:16px;justify-content:center;margin-bottom:24px;">
    <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);border-radius:10px;padding:14px 18px;text-align:center;">
      <div class="mono" style="font-size:11px;color:#64748b;">SEEDS</div>
      <div class="mono" style="font-size:13px;color:#818cf8;margin-top:4px;">"agent_wallet"<br>+ owner_key</div>
    </div>
    <div class="mono" style="font-size:20px;color:#475569;">+</div>
    <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.2);border-radius:10px;padding:14px 18px;text-align:center;">
      <div class="mono" style="font-size:11px;color:#64748b;">PROGRAM ID</div>
      <div class="mono" style="font-size:13px;color:#fbbf24;margin-top:4px;">AgentWallet<br>Program</div>
    </div>
    <div class="mono" style="font-size:20px;color:#475569;">=</div>
    <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);border-radius:10px;padding:14px 18px;text-align:center;">
      <div class="mono" style="font-size:11px;color:#64748b;">OUTPUT</div>
      <div class="mono" style="font-size:13px;color:#34d399;margin-top:4px;">PDA Address<br>+ bump seed</div>
    </div>
  </div>
  <div style="background:rgba(0,0,0,0.3);border-radius:10px;padding:16px 20px;text-align:center;">
    <div class="mono" style="font-size:12px;color:#64748b;">sha256(seeds + program_id + "ProgramDerivedAddress") <span class="pink">-&gt;</span> must NOT be on ed25519 curve</div>
  </div>
</div>
""")

def card_04():
    return wrap(4, """
<div class="glow-pink" style="top:-50px;right:100px;width:300px;height:300px;"></div>
<div class="glow-purple" style="bottom:100px;left:-50px;"></div>
<div class="content">
  <div style="margin-bottom:8px;"><span class="tag" style="background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.2);">THE PROBLEM</span></div>
  <div class="title" style="font-size:36px;margin-bottom:28px;">Why Private Keys<br><span class="pink">Kill AI Agents</span></div>
  <div style="display:flex;flex-direction:column;gap:16px;">
    <div class="list-item">
      <div class="list-icon list-icon-red">1</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">Key Exposure</div>
        <div style="font-size:13.5px;color:#94a3b8;">AI agent holds raw private key in memory. one exploit = drained wallet.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-red">2</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">No Spending Limits</div>
        <div style="font-size:13.5px;color:#94a3b8;">private key = god mode. no way to set per-tx limits, daily caps, or allowlists.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-red">3</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">Irrevocable Access</div>
        <div style="font-size:13.5px;color:#94a3b8;">can't revoke agent access without moving all funds to a new wallet.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-red">4</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">No Audit Trail</div>
        <div style="font-size:13.5px;color:#94a3b8;">agent signs like the owner. impossible to distinguish human vs AI actions.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-red">5</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">Multi-Agent Chaos</div>
        <div style="font-size:13.5px;color:#94a3b8;">sharing one key across agents? congrats, you've built a distributed single point of failure.</div>
      </div>
    </div>
  </div>
</div>
""")

def card_05():
    return wrap(5, """
<div class="glow-green" style="top:-50px;left:100px;width:350px;height:350px;"></div>
<div class="glow-purple" style="bottom:-50px;right:100px;"></div>
<div class="content">
  <div style="margin-bottom:8px;"><span class="tag tag-green">THE SOLUTION</span></div>
  <div class="title" style="font-size:36px;margin-bottom:28px;">PDAs Fix <span class="green">Everything</span></div>
  <div style="display:flex;flex-direction:column;gap:16px;">
    <div class="list-item">
      <div class="list-icon list-icon-green">1</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">Zero Key Exposure</div>
        <div style="font-size:13.5px;color:#94a3b8;">no private key exists. the program itself signs via invoke_signed. nothing to leak.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-green">2</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">On-Chain Spend Policies</div>
        <div style="font-size:13.5px;color:#94a3b8;">per-token limits, daily caps, allowlisted destinations. enforced by the VM, not trust.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-green">3</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">Instant Revocation</div>
        <div style="font-size:13.5px;color:#94a3b8;">flip a boolean on-chain. agent loses access immediately. funds stay safe.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-green">4</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">Full Audit Trail</div>
        <div style="font-size:13.5px;color:#94a3b8;">every agent action routes through the program. on-chain logs show exactly who did what.</div>
      </div>
    </div>
    <div class="list-item">
      <div class="list-icon list-icon-green">5</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px;">Multi-Agent Native</div>
        <div style="font-size:13.5px;color:#94a3b8;">each agent gets its own PDA with isolated permissions. composable, not chaotic.</div>
      </div>
    </div>
  </div>
</div>
""")

def card_06():
    return wrap(6, """
<div class="glow-purple" style="top:-80px;left:200px;width:400px;height:400px;"></div>
<div class="glow-green" style="bottom:50px;right:-50px;"></div>
<div class="content">
  <div style="margin-bottom:8px;"><span class="tag tag-purple">COMPARISON</span></div>
  <div class="title" style="font-size:34px;margin-bottom:24px;">Ethereum vs <span class="purple">Solana</span> for AI Wallets</div>
  <table class="compare-table" style="margin-bottom:16px;">
    <tr>
      <th class="dim" style="width:30%;">Feature</th>
      <th style="color:#94a3b8;">Ethereum</th>
      <th style="color:#818cf8;">Solana (PDAs)</th>
    </tr>
    <tr>
      <td class="dim">Architecture</td>
      <td style="color:#94a3b8;">Smart contract wallets</td>
      <td style="color:#34d399;">Native PDA accounts</td>
    </tr>
    <tr>
      <td class="dim">Deploy Cost</td>
      <td style="color:#f87171;">$50-200 per wallet</td>
      <td style="color:#34d399;">~$0.002 per PDA</td>
    </tr>
    <tr>
      <td class="dim">Tx Speed</td>
      <td style="color:#f87171;">12-15 seconds</td>
      <td style="color:#34d399;">400 milliseconds</td>
    </tr>
    <tr>
      <td class="dim">Tx Cost</td>
      <td style="color:#f87171;">$2-50+</td>
      <td style="color:#34d399;">$0.00025</td>
    </tr>
    <tr>
      <td class="dim">Key Model</td>
      <td style="color:#94a3b8;">EOA + contract signer</td