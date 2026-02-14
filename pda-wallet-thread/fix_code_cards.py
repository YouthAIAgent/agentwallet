# -*- coding: utf-8 -*-
"""Fix code cards 4 and 8 - use plain text without HTML spans"""
import sys, os, io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\black\Desktop\agentwallet\scripts")
from banger_card import THEMES, _css, _ambient, _logo, _badge, _render

OUT = r"C:\Users\black\Desktop\agentwallet\pda-wallet-thread"

def generate_code_card_v2(title, code_html, output_path, theme="obsidian", filename="policy.rs"):
    """Code card that renders HTML spans for syntax highlighting (no escaping)"""
    t = THEMES.get(theme, THEMES["obsidian"])
    
    inner = f'''
    <div style="position:relative;z-index:5;height:100%;display:flex;flex-direction:column;padding:32px 44px;">
        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:14px;">
                {_logo(t)}
                <div style="width:1px;height:16px;background:{t['border']};"></div>
                <span style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:{t['text']};letter-spacing:-0.5px;">{title}</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:{t['accent']};background:{t['accent_dim']};border:1px solid {t['border2']};padding:4px 12px;border-radius:14px;font-weight:600;letter-spacing:1px;">{filename}</div>
                {_badge(t, "SHIPPED")}
            </div>
        </div>
        
        <!-- Editor window -->
        <div style="flex:1;background:{t['surface']};border:1px solid {t['border']};border-radius:12px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 0 1px {t['border2']};">
            <!-- Chrome bar -->
            <div style="padding:12px 18px;display:flex;align-items:center;border-bottom:1px solid rgba(255,255,255,0.04);background:rgba(255,255,255,0.015);">
                <div style="display:flex;gap:6px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#ff5f57;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#febc2e;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#28c840;"></div>
                </div>
                <div style="margin-left:16px;font-family:'JetBrains Mono',monospace;font-size:10px;color:{t['text3']};padding:3px 10px;background:rgba(255,255,255,0.04);border-radius:4px;border:1px solid rgba(255,255,255,0.04);">{filename}</div>
                <div style="margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:9px;color:{t['text3']};letter-spacing:1px;">RUST</div>
            </div>
            <!-- Code body -->
            <div style="flex:1;padding:20px 24px;font-family:'JetBrains Mono',monospace;font-size:12.5px;line-height:1.85;color:{t['text2']};white-space:pre-wrap;overflow:hidden;position:relative;">
                <div style="position:absolute;left:0;top:0;bottom:0;width:1px;background:{t['accent']};opacity:0.08;"></div>
                {code_html}
            </div>
        </div>
        
        <!-- Footer -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:{t['accent']};font-weight:700;">agentwallet.fun</span>
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:9px;color:{t['text3']};font-weight:500;letter-spacing:2px;text-transform:uppercase;">AgentWallet Protocol</span>
                <div style="width:3px;height:3px;background:{t['accent']};border-radius:50%;opacity:0.5;"></div>
                <span style="font-size:9px;color:{t['text3']};font-weight:500;letter-spacing:2px;text-transform:uppercase;">Solana</span>
            </div>
        </div>
    </div>'''

    html = f'<!DOCTYPE html><html><head><style>{_css(t)}</style></head><body>{_ambient(t)}{inner}</body></html>'
    _render(html, output_path)
    print(f"[CODE-v2] {theme} -> {output_path}")

# Card 4: Spend Policies
print("[4/10] Fixing spend policies code card...")
code4 = """<span style="color:#c084fc;font-weight:700;">AgentPolicy</span> {
  <span style="color:#94a3b8;">max_per_tx:</span>    <span style="color:#fbbf24;font-weight:600;">5 SOL</span>
  <span style="color:#94a3b8;">daily_limit:</span>   <span style="color:#fbbf24;font-weight:600;">20 SOL</span>
  <span style="color:#94a3b8;">allowed_tokens:</span> <span style="color:#34d399;">[SOL, USDC, BONK]</span>
  <span style="color:#94a3b8;">destinations:</span>  <span style="color:#34d399;">[jupiter, raydium]</span>
  <span style="color:#94a3b8;">cooldown:</span>      <span style="color:#fbbf24;font-weight:600;">30 seconds</span>
  <span style="color:#94a3b8;">emergency:</span>     <span style="color:#f43f5e;font-weight:700;">owner_freeze()</span>
}

<span style="color:#64748b;">// Enforced by Solana VM</span>
<span style="color:#64748b;">// Not by your agent. Not by a server.</span>
<span style="color:#64748b;">// By the runtime itself.</span>"""

generate_code_card_v2(
    "On-Chain Spend Policies", code4,
    os.path.join(OUT, "card_04.png"), "neon", "agent_policy.rs"
)

# Card 8: Composability
print("[8/10] Fixing composability code card...")
code8 = """<span style="color:#64748b;">// Single atomic transaction</span>
<span style="color:#64748b;">// Zero private keys needed</span>

<span style="color:#38bdf8;font-weight:700;">invoke_signed</span>([
  <span style="color:#34d399;">jupiter</span>::<span style="color:#c084fc;">swap</span>(SOL -&gt; USDC),
  <span style="color:#34d399;">raydium</span>::<span style="color:#c084fc;">add_liquidity</span>(USDC-SOL),
  <span style="color:#34d399;">marinade</span>::<span style="color:#c084fc;">stake</span>(remaining_SOL),
], <span style="color:#fbbf24;font-weight:600;">pda_seeds</span>);

<span style="color:#64748b;">// If ANY step fails -&gt; everything reverts</span>
<span style="color:#64748b;">// No partial states. No stuck funds.</span>"""

generate_code_card_v2(
    "CPI Composability", code8,
    os.path.join(OUT, "card_08.png"), "arctic", "atomic_swap.rs"
)

print("\nCode cards fixed!")

# Verify sizes
for f in ["card_04.png", "card_08.png"]:
    fp = os.path.join(OUT, f)
    print(f"  {f} - {os.path.getsize(fp) // 1024}KB")
