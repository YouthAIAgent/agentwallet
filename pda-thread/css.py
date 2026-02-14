"""Shared CSS and HTML frame for all cards"""

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
.ft .fh{color:rgba(99,102,241,.6)}.ft .fs{color:rgba(16,185,129,.6)}
.spl{position:absolute;bottom:60px;left:50px;right:50px;height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,.2),rgba(16,185,129,.2),transparent);z-index:10}
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
.lic{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0;margin-top:2px}
.lr{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.2)}
.lg{background:rgba(16,185,129,.15);color:#34d399;border:1px solid rgba(16,185,129,.2)}
.lp{background:rgba(99,102,241,.15);color:#818cf8;border:1px solid rgba(99,102,241,.2)}
.lo{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.2)}
.sb{background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.12);border-radius:12px;padding:18px;text-align:center}
.sv{font-family:'Space Grotesk',sans-serif;font-size:34px;font-weight:700}
.sl{font-size:12px;color:#64748b;margin-top:4px;font-family:'Inter',sans-serif}
.lt{font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:16px;color:#f1f5f9;margin-bottom:2px}
.ld{font-size:13px;color:#94a3b8}
"""

def frame(n):
    return f'<div class="ctl tl"></div><div class="ctl tr"></div><div class="ctl bl"></div><div class="ctl br"></div><div class="tn">{n:02d}/15</div><div class="spl"></div><div class="ft"><span class="fh">@Web3__Youth</span><span class="fs">agentwallet.fun</span></div>'

def html(n, body):
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{frame(n)}{body}</body></html>'
