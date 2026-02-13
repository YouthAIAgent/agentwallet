import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  Audio,
  AbsoluteFill,
  staticFile,
} from 'remotion';
import { noise2D } from '@remotion/noise';
import { theme, easing, hexToRgb } from '../theme';
import { fontFamily } from '../fonts';
import { GlitchText } from '../components/GlitchText';
import { CircuitLines } from '../components/CircuitLines';

// ═══════════════════════════════════════════════════════════════
// TOKEN DETAILS VIDEO — AgentWallet $AW
// Voiceover-synced, organic presentation
// ═══════════════════════════════════════════════════════════════

const FPS = 30;

// ─── Shared Background ──────────────────────────────────────
const GridBg = ({ color = theme.colors.purple, speed = 0.4 }) => {
  const frame = useCurrentFrame();
  const offset = frame * speed;

  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', inset: 0, background: theme.gradients.meshDark }} />
      <div style={{
        position: 'absolute', inset: 0,
        perspective: '800px', perspectiveOrigin: '50% 40%', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', width: '200%', height: '200%',
          left: '-50%', top: '20%',
          transform: `rotateX(65deg) translateY(${-offset % 100}px)`,
          backgroundImage: `
            linear-gradient(rgba(${hexToRgb(color)}, 0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(${hexToRgb(color)}, 0.06) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
        }} />
      </div>
      {Array.from({ length: 25 }).map((_, i) => {
        const x = noise2D('px' + i, frame * 0.004, i) * 100;
        const y = noise2D('py' + i, frame * 0.004, i + 50) * 100;
        const size = 1 + Math.abs(noise2D('ps' + i, 0, i)) * 2.5;
        const alpha = 0.08 + Math.abs(noise2D('pa' + i, frame * 0.008, i)) * 0.3;
        return (
          <div key={i} style={{
            position: 'absolute',
            left: `${50 + x * 0.5}%`, top: `${50 + y * 0.5}%`,
            width: size, height: size, borderRadius: '50%',
            background: i % 3 === 0 ? theme.colors.purple : i % 3 === 1 ? theme.colors.green : theme.colors.cyan,
            opacity: alpha,
            boxShadow: `0 0 ${size * 3}px ${i % 3 === 0 ? theme.colors.purple : theme.colors.cyan}`,
          }} />
        );
      })}
      <div style={{
        position: 'absolute', width: 500, height: 500, borderRadius: '50%',
        left: `${25 + Math.sin(frame * 0.008) * 8}%`,
        top: `${15 + Math.cos(frame * 0.006) * 8}%`,
        background: `radial-gradient(circle, rgba(${hexToRgb(theme.colors.purple)}, 0.1) 0%, transparent 70%)`,
        filter: 'blur(50px)',
      }} />
    </AbsoluteFill>
  );
};

// ─── Badge ──────────────────────────────────────────────────
const Badge = ({ text, delay = 0, color = theme.colors.purple }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: theme.springs.snappy });
  const shimmer = (frame - delay) * 3;

  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      padding: '6px 16px', borderRadius: 6,
      background: `linear-gradient(135deg, rgba(${hexToRgb(color)}, 0.15), rgba(${hexToRgb(color)}, 0.05))`,
      border: `1px solid rgba(${hexToRgb(color)}, 0.4)`,
      transform: `translateY(${(1 - progress) * 15}px)`, opacity: progress,
      overflow: 'hidden', position: 'relative',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.06) 50%, transparent 70%)`,
        transform: `translateX(${-100 + (shimmer % 200)}%)`,
      }} />
      <div style={{
        width: 5, height: 5, borderRadius: '50%',
        background: color, boxShadow: `0 0 6px ${color}`,
      }} />
      <span style={{
        fontSize: 11, fontWeight: 700, fontFamily: fontFamily.mono,
        color, letterSpacing: '2px', textTransform: 'uppercase', position: 'relative',
      }}>{text}</span>
    </div>
  );
};

// ─── Neon Line ──────────────────────────────────────────────
const NeonLine = ({ delay = 0, width = '50%' }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: theme.springs.snappy });
  return (
    <div style={{
      width, height: 2, margin: '16px auto',
      background: theme.gradients.accentBar,
      boxShadow: `0 0 8px ${theme.colors.purple}, 0 0 16px ${theme.colors.cyan}`,
      transform: `scaleX(${progress})`, opacity: progress,
    }} />
  );
};

// ─── Info Row ───────────────────────────────────────────────
const InfoRow = ({ label, value, delay = 0, color = theme.colors.cyan, mono = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: theme.springs.snappy });

  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '12px 20px', borderRadius: 10,
      background: 'rgba(15, 15, 40, 0.5)',
      border: '1px solid rgba(255,255,255,0.06)',
      opacity: progress, transform: `translateX(${(1 - progress) * 40}px)`,
    }}>
      <span style={{
        fontSize: 14, fontWeight: 600, fontFamily: fontFamily.mono,
        color: theme.colors.gray, letterSpacing: '1px', textTransform: 'uppercase',
      }}>{label}</span>
      <span style={{
        fontSize: mono ? 13 : 16, fontWeight: 700,
        fontFamily: mono ? fontFamily.mono : fontFamily.heading,
        color, letterSpacing: mono ? '0.5px' : '0px',
      }}>{value}</span>
    </div>
  );
};

// ─── Feature Card ───────────────────────────────────────────
const FeatureCard = ({ title, desc, delay = 0, color = theme.colors.green }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: theme.springs.pop });

  return (
    <div style={{
      padding: '18px 22px', borderRadius: 14,
      ...theme.glass.card,
      borderColor: `rgba(${hexToRgb(color)}, 0.25)`,
      boxShadow: `0 0 15px rgba(${hexToRgb(color)}, 0.1), inset 0 0 15px rgba(${hexToRgb(color)}, 0.02)`,
      transform: `scale(${0.85 + progress * 0.15}) translateY(${(1 - progress) * 20}px)`,
      opacity: progress, flex: 1, minWidth: 200,
    }}>
      <div style={{
        fontSize: 16, fontWeight: 800, color,
        fontFamily: fontFamily.heading, marginBottom: 6,
      }}>{title}</div>
      <div style={{
        fontSize: 13, fontWeight: 500, color: theme.colors.gray,
        fontFamily: fontFamily.heading, lineHeight: 1.4,
      }}>{desc}</div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// SCENES — synced to voiceover timing
// ═══════════════════════════════════════════════════════════════

// Scene 1: Title Card (0-5s)
const TitleScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBg color={theme.colors.purple} />
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2 }}>
        <div style={{
          width: 90, height: 90, margin: '0 auto 25px',
          background: `linear-gradient(135deg, ${theme.colors.purple}, ${theme.colors.cyan})`,
          borderRadius: 18,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: theme.glow.boxPurple,
          transform: `scale(${spring({ frame, fps, config: theme.springs.bouncy })})`,
        }}>
          <span style={{ fontSize: 42, fontWeight: 900, color: '#FFF', fontFamily: fontFamily.heading }}>AW</span>
        </div>

        <GlitchText text="AGENTWALLET" startFrame={8} fontSize={68} color={theme.colors.white} glitchIntensity={1.2} duration={22} />
        <div style={{ marginTop: 8 }}>
          <GlitchText text="PROTOCOL" startFrame={18} fontSize={26} color={theme.colors.purple} glitchIntensity={0.4} duration={12} mono />
        </div>
        <NeonLine delay={30} width="280px" />
        <div style={{
          marginTop: 8,
          opacity: interpolate(frame, [35, 48], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
        }}>
          <span style={{ fontSize: 16, fontWeight: 600, fontFamily: fontFamily.mono, color: theme.colors.gray, letterSpacing: '3px' }}>
            TOKEN DETAILS & VERIFICATION
          </span>
        </div>
      </div>
      <CircuitLines opacity={0.1} />
    </AbsoluteFill>
  );
};

// Scene 2: Token Info (5-12s)
const TokenInfoScene = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBg color={theme.colors.cyan} speed={0.3} />
      <div style={{ position: 'relative', zIndex: 2, maxWidth: 800, width: '100%', padding: '0 60px' }}>
        <Badge text="TOKEN INFO" delay={0} color={theme.colors.cyan} />
        <div style={{ marginTop: 30, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <InfoRow label="Name" value="AgentWallet" delay={10} color={theme.colors.white} />
          <InfoRow label="Ticker" value="$AW" delay={18} color={theme.colors.green} />
          <InfoRow label="Network" value="Solana (SPL)" delay={26} color={theme.colors.purple} />
          <InfoRow label="Supply" value="1,000,000,000" delay={34} color={theme.colors.cyan} />
          <InfoRow label="DEX" value="Jupiter" delay={42} color={theme.colors.orange} />
          <InfoRow label="Mint" value="B8r3Yp5C...DGBAGS" delay={50} color={theme.colors.green} mono />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 3: Mint Address Full (12-17s)
const MintScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - 10, fps, config: theme.springs.snappy });

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBg color={theme.colors.green} speed={0.5} />
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2, maxWidth: 900 }}>
        <Badge text="VERIFIED MINT ADDRESS" delay={0} color={theme.colors.green} />
        <div style={{
          marginTop: 40, padding: '24px 32px', borderRadius: 14,
          background: 'rgba(10, 10, 30, 0.7)',
          border: `1px solid rgba(${hexToRgb(theme.colors.green)}, 0.3)`,
          boxShadow: `0 0 30px rgba(${hexToRgb(theme.colors.green)}, 0.1)`,
          opacity: progress, transform: `scale(${0.95 + progress * 0.05})`,
        }}>
          <div style={{
            fontSize: 11, fontWeight: 700, fontFamily: fontFamily.mono,
            color: theme.colors.gray, letterSpacing: '2px', marginBottom: 12,
          }}>SOLANA SPL TOKEN</div>
          <div style={{
            fontSize: 22, fontWeight: 700, fontFamily: fontFamily.mono,
            color: theme.colors.green, letterSpacing: '1px', wordBreak: 'break-all',
            textShadow: `0 0 20px rgba(${hexToRgb(theme.colors.green)}, 0.4)`,
          }}>
            B8r3Yp5C2Kx5fAyCLVMoVaGoiQkAaqzLsh69adDGBAGS
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 25 }}>
          <Badge text="SOLSCAN" delay={30} color={theme.colors.cyan} />
          <Badge text="JUPITER" delay={38} color={theme.colors.orange} />
          <Badge text="X / TWITTER" delay={46} color={theme.colors.purple} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 4: What It Does (17-28s)
const WhatItDoesScene = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBg color={theme.colors.purple} speed={0.4} />
      <div style={{ position: 'relative', zIndex: 2, maxWidth: 950, width: '100%', padding: '0 50px' }}>
        <Badge text="CORE PROTOCOL" delay={0} color={theme.colors.purple} />
        <div style={{ marginTop: 25 }}>
          <GlitchText text="WHAT AGENTWALLET DOES" startFrame={8} fontSize={42} color={theme.colors.white} glitchIntensity={0.4} duration={15} />
        </div>
        <NeonLine delay={20} width="400px" />

        <div style={{ display: 'flex', gap: 16, marginTop: 25, flexWrap: 'wrap' }}>
          <FeatureCard title="PDA Spend Policies" desc="Programmable wallets with limits, allowlists, time locks. On-chain enforcement." delay={25} color={theme.colors.green} />
          <FeatureCard title="Trustless Escrow" desc="Agent-to-agent payments. No intermediary. Auto-release on completion." delay={35} color={theme.colors.cyan} />
          <FeatureCard title="x402 Micropayments" desc="HTTP-native pay-per-API-call. Machine-to-machine commerce." delay={45} color={theme.colors.orange} />
        </div>
        <div style={{ display: 'flex', gap: 16, marginTop: 16, flexWrap: 'wrap' }}>
          <FeatureCard title="33 MCP Tools" desc="Native Claude, GPT, Cursor integration. Plug and play." delay={55} color={theme.colors.purple} />
          <FeatureCard title="12ms Settlement" desc="Solana-native speed. Real-time agent transactions." delay={65} color={theme.colors.green} />
          <FeatureCard title="On-Chain Reputation" desc="Verifiable trust scores. Transaction history as proof." delay={75} color={theme.colors.pink} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 5: Architecture (28-38s)
const ArchScene = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBg color={theme.colors.cyan} speed={0.3} />
      <div style={{ position: 'relative', zIndex: 2, maxWidth: 850, width: '100%', padding: '0 50px' }}>
        <Badge text="TECH STACK" delay={0} color={theme.colors.cyan} />
        <div style={{ marginTop: 25 }}>
          <GlitchText text="TECHNICAL ARCHITECTURE" startFrame={8} fontSize={40} color={theme.colors.white} glitchIntensity={0.3} duration={15} />
        </div>
        <NeonLine delay={20} width="350px" />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 25 }}>
          <InfoRow label="Smart Contract" value="Solana Program (Rust/Anchor)" delay={25} color={theme.colors.green} />
          <InfoRow label="SDKs" value="Python + TypeScript + Rust" delay={33} color={theme.colors.cyan} />
          <InfoRow label="API" value="REST + MCP Server" delay={41} color={theme.colors.orange} />
          <InfoRow label="Install" value="pip install aw-protocol-sdk" delay={49} color={theme.colors.purple} mono />
          <InfoRow label="Source" value="github.com/YouthAIAgent/agentwallet" delay={57} color={theme.colors.white} mono />
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 25 }}>
          <Badge text="OPEN SOURCE" delay={65} color={theme.colors.green} />
          <Badge text="AUDITABLE" delay={70} color={theme.colors.cyan} />
          <Badge text="DEVNET LIVE" delay={75} color={theme.colors.purple} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 6: Token Utility (38-48s)
const UtilityScene = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBg color={theme.colors.green} speed={0.5} />
      <div style={{ position: 'relative', zIndex: 2, maxWidth: 900, width: '100%', padding: '0 50px' }}>
        <Badge text="$AW UTILITY" delay={0} color={theme.colors.green} />
        <div style={{ marginTop: 25 }}>
          <GlitchText text="TOKEN UTILITY" startFrame={8} fontSize={46} color={theme.colors.green} glitchIntensity={0.5} duration={15} />
        </div>
        <NeonLine delay={20} width="300px" />

        <div style={{ display: 'flex', gap: 16, marginTop: 25, flexWrap: 'wrap' }}>
          <FeatureCard title="Protocol Fee Discounts" desc="Hold $AW, pay less on every transaction through the protocol." delay={25} color={theme.colors.green} />
          <FeatureCard title="Staking" desc="Stake for enhanced API rate limits and priority processing." delay={35} color={theme.colors.cyan} />
          <FeatureCard title="Governance" desc="Vote on protocol upgrades, fee structures, and roadmap." delay={45} color={theme.colors.purple} />
          <FeatureCard title="Marketplace Staking" desc="Reputation staking for agent marketplace. Reduced escrow fees." delay={55} color={theme.colors.orange} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 7: CTA (48-55s)
const OutroScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBg color={theme.colors.purple} speed={0.8} />
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2 }}>
        <div style={{
          width: 80, height: 80, margin: '0 auto 20px',
          background: `linear-gradient(135deg, ${theme.colors.purple}, ${theme.colors.green})`,
          borderRadius: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: theme.glow.boxPurple,
          transform: `scale(${spring({ frame, fps, config: theme.springs.bouncy })})`,
        }}>
          <span style={{ fontSize: 38, fontWeight: 900, color: '#FFF', fontFamily: fontFamily.heading }}>AW</span>
        </div>

        <GlitchText text="agentwallet.fun" startFrame={10} fontSize={52} color={theme.colors.white} glitchIntensity={0.3} duration={18} />
        <NeonLine delay={25} width="350px" />

        <div style={{
          marginTop: 12,
          opacity: interpolate(frame, [30, 42], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
        }}>
          <span style={{ fontSize: 18, fontWeight: 600, fontFamily: fontFamily.heading, color: theme.colors.gray }}>
            @Web3__Youth{'  |  '}
            <span style={{ color: theme.colors.green }}>$AW on Jupiter</span>
            {'  |  '}
            <span style={{ color: theme.colors.purple }}>Built on Solana</span>
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 25 }}>
          <Badge text="VERIFIED" delay={40} color={theme.colors.green} />
          <Badge text="LIVE ON JUPITER" delay={45} color={theme.colors.orange} />
          <Badge text="1B SUPPLY" delay={50} color={theme.colors.cyan} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ═══════════════════════════════════════════════════════════════
// MAIN COMPOSITION
// ═══════════════════════════════════════════════════════════════
export const TokenDetails = ({ voiceoverSrc }) => {
  // Scene durations in frames (30fps) — synced to 66s voiceover
  const scenes = [
    { component: TitleScene, duration: 6 * FPS },       // 0-6s
    { component: TokenInfoScene, duration: 9 * FPS },   // 6-15s
    { component: MintScene, duration: 7 * FPS },        // 15-22s
    { component: WhatItDoesScene, duration: 14 * FPS }, // 22-36s
    { component: ArchScene, duration: 12 * FPS },       // 36-48s
    { component: UtilityScene, duration: 10 * FPS },    // 48-58s
    { component: OutroScene, duration: 8 * FPS },       // 58-66s
  ];

  let offset = 0;

  return (
    <AbsoluteFill style={{ background: theme.colors.bgDeep }}>
      {/* Brand watermark */}
      <div style={{
        position: 'absolute', top: 25, left: 25, zIndex: 100,
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '6px 14px',
        background: 'rgba(10, 10, 26, 0.7)', borderRadius: 8,
        border: `1px solid rgba(${hexToRgb(theme.colors.purple)}, 0.3)`,
      }}>
        <div style={{
          width: 22, height: 22, borderRadius: 5,
          background: `linear-gradient(135deg, ${theme.colors.purple}, ${theme.colors.cyan})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 9, fontWeight: 900, color: '#FFF', fontFamily: fontFamily.heading,
        }}>AW</div>
        <span style={{
          fontSize: 12, fontWeight: 700, color: theme.colors.white,
          fontFamily: fontFamily.heading, letterSpacing: '1px',
        }}>AgentWallet Protocol</span>
      </div>

      {/* Scenes */}
      {scenes.map(({ component: Scene, duration }, i) => {
        const from = offset;
        offset += duration;
        return (
          <Sequence key={i} from={from} durationInFrames={duration}>
            <Scene />
          </Sequence>
        );
      })}

      {/* Voiceover */}
      {voiceoverSrc && (
        <Audio src={voiceoverSrc} volume={1} />
      )}
    </AbsoluteFill>
  );
};
