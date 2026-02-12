import React from 'react';
import {
  AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Sequence, Audio, staticFile,
} from 'remotion';
import { noise2D } from '@remotion/noise';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';
import {
  Background, FadeSlide, ArchNode, Arrow, Badge, TechTag, LogoReveal,
  ParticleExplosion, CodeBlock, GlitchText, CircuitLines, NumberCounter,
  StatCounter, WaveformVisualizer, ProgressRing,
} from '../components';

const FPS = 60;
const sec = (s) => Math.round(s * FPS);
const GC = ({ children, style = {}, color, glow }) => (
  <div style={{ ...theme.glass.card, padding: '28px 32px', textAlign: 'center', ...(color ? { borderColor: `rgba(${hexToRgb(color)}, 0.25)` } : {}), ...(glow ? { boxShadow: glow } : {}), ...style }}>{children}</div>
);

const OpeningScene = () => (
  <Background variant="dark" showLightRays lightRayCorner="center" particleCount={50} vignetteIntensity={0.65} orbs={[{ color: theme.colors.purple, size: 700, top: '5%', left: '35%', delay: 5 }, { color: theme.colors.cyan, size: 400, top: '55%', left: '60%', delay: 15 }]}>
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <ParticleExplosion startFrame={8} x="50%" y="42%" count={70} color={theme.colors.purple} secondaryColor={theme.colors.green} duration={50} spread={400} />
      <LogoReveal startFrame={10} text="AgentWallet" highlightText="Wallet" tagline="The self-custodial wallet protocol for AI agents" fontSize={90} />
      <FadeSlide startFrame={sec(4)} duration={20} direction="up">
        <div style={{ marginTop: 50, fontSize: 13, fontWeight: 600, color: theme.colors.green, letterSpacing: 3, fontFamily: fontFamily.mono, ...theme.glass.subtle, padding: '10px 24px' }}>â—Ž BUILT ON SOLANA</div>
      </FadeSlide>
    </AbsoluteFill>
  </Background>
);

const ProblemScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sr = sec(14);
  const lS = spring({ frame, fps, delay: sec(2), config: theme.springs.snappy });
  const rS = spring({ frame, fps, delay: sec(3.5), config: theme.springs.snappy });
  const vS = spring({ frame, fps, delay: sec(5), config: theme.springs.bouncy });
  const sS = spring({ frame, fps, delay: sr, config: theme.springs.pop });
  const sO = interpolate(frame, [sr, sr + 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const p = 0.7 + Math.sin(frame * 0.06) * 0.3;
  return (
    <Background variant="dark" showScanLine particleCount={20} vignetteIntensity={0.7} orbs={[{ color: '#FF3B5C', size: 500, top: '10%', left: '20%', delay: 0 }, { color: theme.colors.orange, size: 400, top: '60%', left: '70%', delay: 10 }]}>
      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
        <div style={{ marginBottom: 60 }}><GlitchText text="THE PROBLEM" startFrame={sec(0.5)} color="#FF3B5C" fontSize={56} fontWeight={900} glitchIntensity={1.2} duration={25} /></div>
        <div style={{ display: 'flex', alignItems: 'stretch', justifyContent: 'center', gap: 60, width: '100%', maxWidth: 1400 }}>
          <div style={{ flex: 1, transform: `scale(${lS})`, ...theme.glass.card, padding: '40px 36px', borderColor: `rgba(${hexToRgb(theme.colors.orange)}, ${0.25*p})`, textAlign: 'center' }}>
            <div style={{ fontSize: 60, marginBottom: 20 }}>ðŸŒ</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: theme.colors.orange, fontFamily: fontFamily.heading, marginBottom: 12 }}>Human Approves Every Tx</div>
            <div style={{ fontSize: 15, color: theme.colors.dim, fontFamily: fontFamily.heading }}>Slow. Manual. Bottleneck.</div>
            <div style={{ marginTop: 16, fontSize: 12, color: theme.colors.orange, fontFamily: fontFamily.mono, letterSpacing: 2, opacity: p }}>âš  NOT SCALABLE</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', transform: `scale(${vS})` }}><div style={{ fontSize: 28, fontWeight: 900, color: theme.colors.muted }}>VS</div></div>
          <div style={{ flex: 1, transform: `scale(${rS})`, ...theme.glass.card, padding: '40px 36px', borderColor: `rgba(${hexToRgb('#FF3B5C')}, ${0.25*p})`, textAlign: 'center' }}>
            <div style={{ fontSize: 60, marginBottom: 20 }}>ðŸ’€</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#FF3B5C', fontFamily: fontFamily.heading, marginBottom: 12 }}>Private Keys Exposed</div>
            <div style={{ fontSize: 15, color: theme.colors.dim, fontFamily: fontFamily.heading }}>Dangerous. One leak drains all.</div>
            <div style={{ marginTop: 16, fontSize: 12, color: '#FF3B5C', fontFamily: fontFamily.mono, letterSpacing: 2, opacity: p }}>â˜  CATASTROPHIC RISK</div>
          </div>
        </div>
        {sO > 0 && <div style={{ marginTop: 60, transform: `scale(${sS})`, opacity: sO, textAlign: 'center', position: 'relative' }}>
          <ParticleExplosion startFrame={sr} x="50%" y="50%" count={40} color={theme.colors.purple} secondaryColor={theme.colors.green} duration={35} spread={250} />
          <div style={{ fontSize: 36, fontWeight: 900, fontFamily: fontFamily.heading, color: theme.colors.white, textShadow: theme.glow.textPurple }}>Enter <span style={{ color: theme.colors.purple }}>Agent</span><span style={{ color: theme.colors.green }}>Wallet</span></div>
          <div style={{ marginTop: 10, fontSize: 16, color: theme.colors.gray, fontFamily: fontFamily.heading }}>No private keys. No bottleneck. Full autonomy.</div>
        </div>}
      </AbsoluteFill>
    </Background>
  );
};

const HowItWorksScene = () => {
  const { width, height } = useVideoConfig();
  return (
    <Background variant="default" showLightRays lightRayCorner="topRight" particleCount={30} orbs={[{ color: theme.colors.purple, size: 600, top: '-10%', left: '55%', delay: 0 }, { color: theme.colors.cyan, size: 400, top: '60%', left: '10%', delay: 10 }]}>
      <CircuitLines paths={[{ points: [{ x: 80, y: 160 }, { x: 180, y: 160 }, { x: 180, y: 310 }, { x: 350, y: 310 }], color: theme.colors.purple, delay: 30 }, { points: [{ x: width-80, y: 180 }, { x: width-200, y: 180 }, { x: width-200, y: 340 }, { x: width-400, y: 340 }], color: theme.colors.cyan, delay: 40 }]} width={width} height={height} startFrame={sec(2)} />
      <AbsoluteFill style={{ padding: '50px 60px' }}>
        <FadeSlide startFrame={0} duration={12}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <GlitchText text="HOW IT WORKS" startFrame={2} color={theme.colors.cyan} fontSize={14} fontWeight={700} mono duration={12} />
            <Badge text="MCP Protocol" startFrame={5} color={theme.colors.purple} />
          </div>
        </FadeSlide>
        <FadeSlide startFrame={sec(0.5)} duration={15} scale={0.97}>
          <div style={{ fontSize: 42, fontWeight: 800, color: theme.colors.white, letterSpacing: -1.5, marginBottom: 6, fontFamily: fontFamily.heading }}><span style={{ color: theme.colors.purple }}>PDA</span> Wallets â€” No Keys Required</div>
          <div style={{ fontSize: 16, color: theme.colors.dim, marginBottom: 44, fontFamily: fontFamily.heading }}>Deterministic wallets derived from the agent's identity</div>
        </FadeSlide>
        <FadeSlide startFrame={sec(2)} duration={15}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 40 }}>
            <ArchNode label="Model" name="AI Agent" desc="GPT / Claude" icon="ðŸ¤–" color={theme.colors.cyan} startFrame={sec(2.5)} />
            <Arrow startFrame={sec(3.5)} color={theme.colors.cyan} direction="right" length={50} />
            <ArchNode label="Interface" name="MCP" desc="27 tools" icon="âš¡" color={theme.colors.purple} startFrame={sec(4)} />
            <Arrow startFrame={sec(5)} color={theme.colors.purple} direction="right" length={50} />
            <ArchNode label="Wallet" name="AgentWallet" desc="PDAÂ·EscrowÂ·x402" icon="ðŸ”" color={theme.colors.purple} startFrame={sec(5.5)} size="large" />
            <Arrow startFrame={sec(6.5)} color={theme.colors.green} direction="right" length={50} />
            <ArchNode label="Chain" name="Solana PDA" desc="On-chain" icon="â—Ž" color={theme.colors.green} startFrame={sec(7)} />
          </div>
        </FadeSlide>
        <div style={{ display: 'flex', gap: 40, alignItems: 'flex-start', justifyContent: 'center' }}>
          <FadeSlide startFrame={sec(10)} duration={15} direction="left">
            <CodeBlock code={"# Install AgentWallet\npip install agentwallet-mcp\n\nwallet = await mcp.call(\n  \"create_wallet\",\n  {\"agent_id\": \"claude-prod-01\"}\n)\n# PDA: 7xKXt...9mPq"} startFrame={sec(10)} typingSpeed={1.5} title="setup.py" accentColor={theme.colors.green} maxWidth={580} fontSize={13} />
          </FadeSlide>
          <FadeSlide startFrame={sec(15)} duration={15} direction="right">
            <GC style={{ maxWidth: 400, padding: '30px 36px', textAlign: 'left' }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: theme.colors.green, letterSpacing: 2, fontFamily: fontFamily.mono, marginBottom: 16 }}>ðŸ”‘ KEY INSIGHT</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: theme.colors.offWhite, fontFamily: fontFamily.heading, lineHeight: 1.5, marginBottom: 12 }}>No private keys.<br/><span style={{ color: theme.colors.purple }}>Derived mathematically.</span></div>
              <div style={{ fontSize: 13, color: theme.colors.dim, fontFamily: fontFamily.heading }}>Cannot be stolen â€” nothing to steal.</div>
            </GC>
          </FadeSlide>
        </div>
      </AbsoluteFill>
    </Background>
  );
};

const PDAVaultsScene = () => (
  <Background variant="default" showLightRays lightRayCorner="topLeft" particleCount={25} orbs={[{ color: theme.colors.purple, size: 500, top: '15%', left: '60%', delay: 0 }]}>
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
      <FadeSlide startFrame={0} duration={10}><div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}><Badge text="Layer 1" startFrame={2} color={theme.colors.purple} /><GlitchText text="PDA VAULTS" startFrame={3} color={theme.colors.purple} fontSize={14} fontWeight={700} mono duration={12} /></div></FadeSlide>
      <FadeSlide startFrame={sec(0.5)} duration={15}><div style={{ fontSize: 44, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 50 }}>Deterministic <span style={{ color: theme.colors.purple }}>Wallet</span> Derivation</div></FadeSlide>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24, marginBottom: 50 }}>
        <FadeSlide startFrame={sec(2)} duration={12} direction="left"><GC><div style={{ fontSize: 36, marginBottom: 10 }}>ðŸ¤–</div><div style={{ fontSize: 11, fontWeight: 700, color: theme.colors.cyan, letterSpacing: 2, fontFamily: fontFamily.mono }}>AGENT ID</div><div style={{ fontSize: 14, color: theme.colors.offWhite, fontFamily: fontFamily.mono, marginTop: 6 }}>claude-prod-01</div></GC></FadeSlide>
        <FadeSlide startFrame={sec(3)} duration={12}><div style={{ fontSize: 28, color: theme.colors.purple, fontWeight: 900 }}>+</div></FadeSlide>
        <FadeSlide startFrame={sec(3.5)} duration={12}><GC><div style={{ fontSize: 36, marginBottom: 10 }}>ðŸ”</div><div style={{ fontSize: 11, fontWeight: 700, color: theme.colors.purple, letterSpacing: 2, fontFamily: fontFamily.mono }}>PROGRAM</div><div style={{ fontSize: 14, color: theme.colors.offWhite, fontFamily: fontFamily.mono, marginTop: 6 }}>AgentWlt...</div></GC></FadeSlide>
        <Arrow startFrame={sec(5)} color={theme.colors.green} direction="right" length={60} />
        <FadeSlide startFrame={sec(6)} duration={15} direction="right"><GC color={theme.colors.green} glow={theme.glow.boxGreen} style={{ minWidth: 220 }}><div style={{ fontSize: 36, marginBottom: 10 }}>ðŸ’Ž</div><div style={{ fontSize: 11, fontWeight: 700, color: theme.colors.green, letterSpacing: 2, fontFamily: fontFamily.mono }}>PDA WALLET</div><div style={{ fontSize: 16, color: theme.colors.green, fontFamily: fontFamily.mono, fontWeight: 700, marginTop: 6 }}>7xKXt...9mPq</div></GC></FadeSlide>
      </div>
      <FadeSlide startFrame={sec(8)} duration={15}><div style={{ display: 'flex', gap: 50, justifyContent: 'center' }}>
        {[['ðŸ”’','Program-Controlled'],['ðŸŽ¯','Deterministic'],['ðŸ›¡ï¸','Unstealable']].map(([ic,lb], i) => <FadeSlide key={lb} startFrame={sec(8)+i*12} duration={12} direction="up"><div style={{ textAlign: 'center' }}><div style={{ fontSize: 32, marginBottom: 8 }}>{ic}</div><div style={{ fontSize: 14, fontWeight: 700, color: theme.colors.offWhite, fontFamily: fontFamily.heading }}>{lb}</div></div></FadeSlide>)}
      </div></FadeSlide>
    </AbsoluteFill>
  </Background>
);

const PolicyEngineScene = () => {
  const frame = useCurrentFrame();
  const ax = interpolate(frame, [sec(8), sec(18)], [15, 85], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const ab = Math.sin(frame * 0.08) * 5;
  return (
    <Background variant="default" showScanLine particleCount={20} orbs={[{ color: theme.colors.orange, size: 500, top: '10%', left: '30%', delay: 0 }]}>
      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
        <FadeSlide startFrame={0} duration={10}><div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}><Badge text="Layer 2" startFrame={2} color={theme.colors.orange} /><GlitchText text="POLICY ENGINE" startFrame={3} color={theme.colors.orange} fontSize={14} fontWeight={700} mono duration={12} /></div></FadeSlide>
        <FadeSlide startFrame={sec(0.5)} duration={15}><div style={{ fontSize: 44, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 40 }}>Autonomous <span style={{ color: theme.colors.orange }}>Within Guardrails</span></div></FadeSlide>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 40, maxWidth: 1200 }}>
          {[['ðŸ’°','Daily Limit','10 SOL/day',theme.colors.purple],['ðŸª™','Token Whitelist','SOL USDC USDT',theme.colors.cyan],['ðŸ“','Destinations','Approved only',theme.colors.green],['â°','Time Locks','Business hours',theme.colors.orange],['ðŸ“Š','Per-TX Cap','Max 2 SOL',theme.colors.pink]].map(([ic,lb,vl,cl], i) => (
            <FadeSlide key={lb} startFrame={sec(2)+i*18} duration={15} direction="up"><GC color={cl} style={{ minWidth: 180, padding: '20px 24px' }}><div style={{ fontSize: 28, marginBottom: 8 }}>{ic}</div><div style={{ fontSize: 13, fontWeight: 700, color: cl, fontFamily: fontFamily.heading, marginBottom: 4 }}>{lb}</div><div style={{ fontSize: 11, color: theme.colors.dim, fontFamily: fontFamily.mono }}>{vl}</div></GC></FadeSlide>
          ))}
        </div>
        <FadeSlide startFrame={sec(8)} duration={15}><div style={{ position: 'relative', width: '80%', height: 80 }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: `linear-gradient(90deg, ${theme.colors.purple}, ${theme.colors.green})`, boxShadow: theme.glow.neonPurple }} />
          <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 3, background: `linear-gradient(90deg, ${theme.colors.purple}, ${theme.colors.green})`, boxShadow: theme.glow.neonPurple }} />
          <div style={{ position: 'absolute', left: `${ax}%`, top: '50%', transform: `translate(-50%,${-50+ab}%)`, fontSize: 36, filter: `drop-shadow(0 0 12px ${theme.colors.cyan})` }}>ðŸ¤–</div>
        </div></FadeSlide>
        <FadeSlide startFrame={sec(14)} duration={15}><div style={{ marginTop: 24, fontSize: 18, color: theme.colors.gray, fontFamily: fontFamily.heading, textAlign: 'center' }}>No bottleneck. <span style={{ color: theme.colors.green, fontWeight: 700 }}>Full owner control.</span></div></FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

const TrustlessEscrowScene = () => {
  const frame = useCurrentFrame();
  return (
    <Background variant="default" showLightRays particleCount={25} orbs={[{ color: theme.colors.green, size: 500, top: '15%', left: '40%', delay: 0 }]}>
      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
        <FadeSlide startFrame={0} duration={10}><div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}><Badge text="Layer 3" startFrame={2} color={theme.colors.green} /><GlitchText text="TRUSTLESS ESCROW" startFrame={3} color={theme.colors.green} fontSize={14} fontWeight={700} mono duration={12} /></div></FadeSlide>
        <FadeSlide startFrame={sec(0.5)} duration={15}><div style={{ fontSize: 44, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 50 }}>Agent-to-Agent <span style={{ color: theme.colors.green }}>Commerce</span></div></FadeSlide>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 40 }}>
          <ArchNode label="Buyer" name="Agent A" desc="Locks funds" icon="ðŸ¤–" color={theme.colors.cyan} startFrame={sec(2)} />
          <Arrow startFrame={sec(3)} color={theme.colors.cyan} direction="right" length={60} />
          <ArchNode label="Contract" name="Escrow" desc="Smart contract" icon="ðŸ”" color={theme.colors.purple} startFrame={sec(3.5)} size="large" />
          <Arrow startFrame={sec(4.5)} color={theme.colors.green} direction="right" length={60} />
          <ArchNode label="Seller" name="Agent B" desc="Delivers work" icon="ðŸ¤–" color={theme.colors.green} startFrame={sec(5)} />
        </div>
        <div style={{ display: 'flex', gap: 50, justifyContent: 'center', marginBottom: 40 }}>
          {[['ðŸ”’','LOCK',sec(6),theme.colors.orange],['âœ…','VERIFY',sec(9),theme.colors.cyan],['ðŸ’¸','RELEASE',sec(12),theme.colors.green]].map(([ic,lb,sf,cl]) => (
            <FadeSlide key={lb} startFrame={sf} duration={12}><div style={{ textAlign: 'center' }}><div style={{ fontSize: 40, marginBottom: 8 }}>{ic}</div><div style={{ fontSize: 16, fontWeight: 700, color: cl, fontFamily: fontFamily.heading }}>{lb}</div></div></FadeSlide>
          ))}
        </div>
        <FadeSlide startFrame={sec(14)} duration={15}><div style={{ ...theme.glass.subtle, padding: '16px 36px', fontSize: 18, color: theme.colors.offWhite, fontFamily: fontFamily.heading, textAlign: 'center' }}>No trust required. <span style={{ color: theme.colors.green, fontWeight: 700 }}>Autonomous economy.</span></div></FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

const X402MarketScene = () => (
  <Background variant="default" showLightRays lightRayCorner="topLeft" particleCount={30} orbs={[{ color: theme.colors.cyan, size: 500, top: '10%', left: '50%', delay: 0 }, { color: theme.colors.orange, size: 400, top: '60%', left: '20%', delay: 10 }]}>
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
      <FadeSlide startFrame={0} duration={12}><GlitchText text="x402 + A2A MARKETPLACE" startFrame={2} color={theme.colors.cyan} fontSize={14} fontWeight={700} mono duration={15} /></FadeSlide>
      <FadeSlide startFrame={sec(1)} duration={15}><div style={{ fontSize: 42, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 40 }}><span style={{ color: theme.colors.cyan }}>x402</span> Micropayments</div></FadeSlide>
      <FadeSlide startFrame={sec(3)} duration={15}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 50 }}>
          <GC style={{ padding: '20px 28px' }} color={theme.colors.cyan}><div style={{ fontSize: 24, marginBottom: 6 }}>ðŸŒ</div><div style={{ fontSize: 13, fontWeight: 700, color: theme.colors.cyan, fontFamily: fontFamily.mono }}>HTTP 402</div><div style={{ fontSize: 11, color: theme.colors.dim, fontFamily: fontFamily.mono }}>Payment Required</div></GC>
          <Arrow startFrame={sec(4)} color={theme.colors.cyan} direction="right" length={40} />
          <GC style={{ padding: '20px 28px' }} color={theme.colors.green}><div style={{ fontSize: 24, marginBottom: 6 }}>â—Ž</div><div style={{ fontSize: 13, fontWeight: 700, color: theme.colors.green, fontFamily: fontFamily.mono }}>SOL Payment</div><div style={{ fontSize: 11, color: theme.colors.dim, fontFamily: fontFamily.mono }}>Auto-pay</div></GC>
          <Arrow startFrame={sec(5)} color={theme.colors.green} direction="right" length={40} />
          <GC style={{ padding: '20px 28px' }} color={theme.colors.purple}><div style={{ fontSize: 24, marginBottom: 6 }}>âœ…</div><div style={{ fontSize: 13, fontWeight: 700, color: theme.colors.purple, fontFamily: fontFamily.mono }}>API Access</div><div style={{ fontSize: 11, color: theme.colors.dim, fontFamily: fontFamily.mono }}>Delivered</div></GC>
        </div>
      </FadeSlide>
      <FadeSlide startFrame={sec(10)} duration={15}><div style={{ fontSize: 36, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 30 }}>A2A <span style={{ color: theme.colors.orange }}>Marketplace</span></div></FadeSlide>
      <FadeSlide startFrame={sec(12)} duration={15}>
        <div style={{ display: 'flex', gap: 20, justifyContent: 'center', flexWrap: 'wrap' }}>
          {[['ðŸŽ¨','Image Gen',theme.colors.pink],['ðŸ“Š','Data Agent',theme.colors.cyan],['ðŸ’»','Code Agent',theme.colors.green],['ðŸ“','Writer',theme.colors.orange]].map(([ic,nm,cl], i) => (
            <FadeSlide key={nm} startFrame={sec(12)+i*12} duration={12} direction="up">
              <GC color={cl} style={{ minWidth: 160, padding: '20px 24px' }}><div style={{ fontSize: 28, marginBottom: 8 }}>{ic}</div><div style={{ fontSize: 14, fontWeight: 700, color: cl, fontFamily: fontFamily.heading }}>{nm}</div></GC>
            </FadeSlide>
          ))}
        </div>
      </FadeSlide>
      <FadeSlide startFrame={sec(20)} duration={15}><div style={{ marginTop: 30, fontSize: 16, color: theme.colors.gray, fontFamily: fontFamily.heading, textAlign: 'center' }}>Decentralized freelance market for AI agents â€” <span style={{ color: theme.colors.green, fontWeight: 700 }}>running 24/7</span></div></FadeSlide>
    </AbsoluteFill>
  </Background>
);

const StatsScene = () => {
  const frame = useCurrentFrame();
  return (
    <Background variant="energy" showLightRays lightRayCorner="center" particleCount={40} vignetteIntensity={0.5} orbs={[{ color: theme.colors.purple, size: 700, top: '-15%', left: '35%', delay: 0 }, { color: theme.colors.green, size: 500, top: '50%', left: '55%', delay: 5 }]}>
      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
        <FadeSlide startFrame={0} duration={12}><GlitchText text="THE NUMBERS" startFrame={2} color={theme.colors.purple} fontSize={14} fontWeight={700} mono duration={12} /></FadeSlide>
        <FadeSlide startFrame={sec(1)} duration={15}><div style={{ fontSize: 48, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 60 }}>Built for <span style={{ color: theme.colors.purple }}>Scale</span></div></FadeSlide>
        <ParticleExplosion startFrame={sec(3)} x="50%" y="45%" count={35} color={theme.colors.purple} secondaryColor={theme.colors.green} duration={30} spread={200} />
        <div style={{ display: 'flex', gap: 30, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 40 }}>
          <StatCounter value="27" label="MCP Tools" color={theme.colors.purple} startFrame={sec(3)} size="large" />
          <StatCounter value="0" label="Private Keys" color={theme.colors.green} startFrame={sec(5)} size="large" />
          <StatCounter value="100" suffix="%" label="On-Chain" color={theme.colors.cyan} startFrame={sec(7)} size="large" />
        </div>
        <ParticleExplosion startFrame={sec(10)} x="50%" y="60%" count={25} color={theme.colors.cyan} secondaryColor={theme.colors.green} duration={25} spread={180} />
        <FadeSlide startFrame={sec(10)} duration={15}>
          <div style={{ display: 'flex', gap: 40, justifyContent: 'center' }}>
            {[['SOL','Primary token',theme.colors.green],['USDC','Stablecoin',theme.colors.cyan],['USDT','Stablecoin',theme.colors.green],['SPL','Any token',theme.colors.purple]].map(([nm,ds,cl], i) => (
              <FadeSlide key={nm} startFrame={sec(10)+i*10} duration={12} direction="up">
                <div style={{ textAlign: 'center' }}><div style={{ fontSize: 20, fontWeight: 800, color: cl, fontFamily: fontFamily.heading, marginBottom: 4 }}>{nm}</div><div style={{ fontSize: 11, color: theme.colors.dim, fontFamily: fontFamily.mono }}>{ds}</div></div>
              </FadeSlide>
            ))}
          </div>
        </FadeSlide>
        <FadeSlide startFrame={sec(16)} duration={15}><div style={{ marginTop: 40, fontSize: 20, fontWeight: 700, color: theme.colors.offWhite, fontFamily: fontFamily.heading, textAlign: 'center' }}>Sub-second finality. <span style={{ color: theme.colors.green }}>Completely open source.</span></div></FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

const InstallScene = () => (
  <Background variant="default" showScanLine showLightRays lightRayCorner="topLeft" particleCount={15} orbs={[{ color: theme.colors.green, size: 450, top: '-5%', left: '65%', delay: 0 }, { color: theme.colors.purple, size: 300, top: '70%', left: '15%', delay: 10 }]}>
    <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
      <FadeSlide startFrame={0} duration={10}><GlitchText text="INSTALLATION" startFrame={2} color={theme.colors.green} fontSize={14} fontWeight={700} mono duration={12} /></FadeSlide>
      <FadeSlide startFrame={sec(1)} duration={15}><div style={{ fontSize: 44, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 50 }}>One Line. <span style={{ color: theme.colors.green }}>Every Model.</span></div></FadeSlide>
      <CodeBlock code={"# Install\npip install agentwallet-mcp\n\n# Configure MCP\n{\n  \"mcpServers\": {\n    \"agentwallet\": {\n      \"command\": \"agentwallet-mcp\",\n      \"args\": [\"--network\", \"mainnet\"]\n    }\n  }\n}\n\n# Works with: Claude, GPT, Gemini..."} startFrame={sec(2)} typingSpeed={1.8} title="terminal" accentColor={theme.colors.green} maxWidth={700} fontSize={14} />
      <FadeSlide startFrame={sec(12)} duration={15}>
        <div style={{ marginTop: 40, display: 'flex', gap: 30, justifyContent: 'center' }}>
          {[['ðŸ¤–','Claude'],['ðŸ§ ','GPT'],['ðŸ’Ž','Gemini'],['ðŸ”¥','Any MCP']].map(([ic,nm], i) => (
            <FadeSlide key={nm} startFrame={sec(12)+i*8} duration={10} direction="up">
              <div style={{ ...theme.glass.subtle, padding: '12px 24px', textAlign: 'center' }}><div style={{ fontSize: 24 }}>{ic}</div><div style={{ fontSize: 12, fontWeight: 700, color: theme.colors.offWhite, fontFamily: fontFamily.mono, marginTop: 4 }}>{nm}</div></div>
            </FadeSlide>
          ))}
        </div>
      </FadeSlide>
    </AbsoluteFill>
  </Background>
);

const WhySolanaScene = () => {
  const frame = useCurrentFrame();
  return (
    <Background variant="default" showLightRays particleCount={30} orbs={[{ color: theme.colors.green, size: 600, top: '10%', left: '40%', delay: 0 }, { color: theme.colors.purple, size: 400, top: '60%', left: '60%', delay: 5 }]}>
      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 80px' }}>
        <FadeSlide startFrame={0} duration={12}><GlitchText text="WHY SOLANA" startFrame={2} color={theme.colors.green} fontSize={14} fontWeight={700} mono duration={12} /></FadeSlide>
        <FadeSlide startFrame={sec(1)} duration={15}><div style={{ fontSize: 48, fontWeight: 800, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', marginBottom: 60 }}>Built on <span style={{ color: theme.colors.green }}>Solana</span> for a Reason</div></FadeSlide>
        <div style={{ display: 'flex', gap: 40, justifyContent: 'center', marginBottom: 50 }}>
          <FadeSlide startFrame={sec(3)} duration={15} direction="left">
            <GC color={theme.colors.green} glow={theme.glow.boxGreen} style={{ minWidth: 280, padding: '36px 40px' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>âš¡</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: theme.colors.green, fontFamily: fontFamily.heading, marginBottom: 8 }}>Sub-Second</div>
              <div style={{ fontSize: 14, color: theme.colors.dim, fontFamily: fontFamily.heading }}>Transaction finality</div>
            </GC>
          </FadeSlide>
          <FadeSlide startFrame={sec(5)} duration={15}>
            <GC color={theme.colors.cyan} glow={theme.glow.boxCyan} style={{ minWidth: 280, padding: '36px 40px' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>ðŸ’¸</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: theme.colors.cyan, fontFamily: fontFamily.heading, marginBottom: 8 }}>$0.00025</div>
              <div style={{ fontSize: 14, color: theme.colors.dim, fontFamily: fontFamily.heading }}>Per transaction</div>
            </GC>
          </FadeSlide>
          <FadeSlide startFrame={sec(7)} duration={15} direction="right">
            <GC color={theme.colors.purple} glow={theme.glow.boxPurple} style={{ minWidth: 280, padding: '36px 40px' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>ðŸ”</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: theme.colors.purple, fontFamily: fontFamily.heading, marginBottom: 8 }}>Native PDA</div>
              <div style={{ fontSize: 14, color: theme.colors.dim, fontFamily: fontFamily.heading }}>Purpose-built for agents</div>
            </GC>
          </FadeSlide>
        </div>
        <FadeSlide startFrame={sec(10)} duration={15}><div style={{ fontSize: 18, color: theme.colors.gray, fontFamily: fontFamily.heading, textAlign: 'center' }}>Solana's PDA system is <span style={{ color: theme.colors.green, fontWeight: 700 }}>purpose-built</span> for deterministic, program-controlled accounts.</div></FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

const ClosingCTAScene = () => {
  const frame = useCurrentFrame();
  return (
    <Background variant="energy" showLightRays lightRayCorner="center" particleCount={50} vignetteIntensity={0.5} orbs={[{ color: theme.colors.purple, size: 800, top: '-20%', left: '30%', delay: 0 }, { color: theme.colors.green, size: 600, top: '40%', left: '60%', delay: 5 }, { color: theme.colors.cyan, size: 400, top: '70%', left: '20%', delay: 10 }]}>
      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <ParticleExplosion startFrame={5} x="50%" y="40%" count={80} color={theme.colors.purple} secondaryColor={theme.colors.green} duration={60} spread={500} />
        <LogoReveal startFrame={8} text="AgentWallet" highlightText="Wallet" tagline="Your Agent Deserves a Wallet" fontSize={96} />
        <FadeSlide startFrame={sec(4)} duration={15} direction="up">
          <div style={{ marginTop: 40, fontSize: 48, fontWeight: 900, color: theme.colors.white, fontFamily: fontFamily.heading, textAlign: 'center', textShadow: theme.glow.textPurple }}>
            agent<span style={{ color: theme.colors.purple }}>wallet</span>.fun
          </div>
        </FadeSlide>
        <FadeSlide startFrame={sec(6)} duration={15} direction="up">
          <div style={{ marginTop: 20, fontSize: 14, color: theme.colors.gray, fontFamily: fontFamily.mono, ...theme.glass.subtle, padding: '12px 28px' }}>
            github.com/agentwallet | pip install agentwallet-mcp
          </div>
        </FadeSlide>
        <FadeSlide startFrame={sec(8)} duration={15} direction="up">
          <WaveformVisualizer startFrame={sec(8)} barCount={64} width={500} height={50} color={theme.colors.purple} secondaryColor={theme.colors.green} intensity={0.6} style={{ marginTop: 30 }} />
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

export const FullExplainer = ({ voiceoverSrc }) => {
  return (
    <AbsoluteFill>
      {voiceoverSrc && <Audio src={voiceoverSrc} volume={1} />}
      <Sequence from={0} durationInFrames={sec(10)}><OpeningScene /></Sequence>
      <Sequence from={sec(10)} durationInFrames={sec(20)}><ProblemScene /></Sequence>
      <Sequence from={sec(30)} durationInFrames={sec(35)}><HowItWorksScene /></Sequence>
      <Sequence from={sec(65)} durationInFrames={sec(20)}><PDAVaultsScene /></Sequence>
      <Sequence from={sec(85)} durationInFrames={sec(25)}><PolicyEngineScene /></Sequence>
      <Sequence from={sec(110)} durationInFrames={sec(20)}><TrustlessEscrowScene /></Sequence>
      <Sequence from={sec(130)} durationInFrames={sec(35)}><X402MarketScene /></Sequence>
      <Sequence from={sec(165)} durationInFrames={sec(30)}><StatsScene /></Sequence>
      <Sequence from={sec(195)} durationInFrames={sec(20)}><InstallScene /></Sequence>
      <Sequence from={sec(215)} durationInFrames={sec(15)}><WhySolanaScene /></Sequence>
      <Sequence from={sec(230)} durationInFrames={sec(12)}><ClosingCTAScene /></Sequence>
    </AbsoluteFill>
  );
};

