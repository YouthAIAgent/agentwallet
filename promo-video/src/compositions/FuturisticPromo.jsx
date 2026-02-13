import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  Audio,
  Img,
  AbsoluteFill,
} from 'remotion';
import { noise2D } from '@remotion/noise';
import { theme, easing, hexToRgb } from '../theme';
import { fontFamily } from '../fonts';
import { GlitchText } from '../components/GlitchText';
import { TypeWriter } from '../components/TypeWriter';
import { CircuitLines } from '../components/CircuitLines';
import { ParticleExplosion } from '../components/ParticleExplosion';
import { CodeBlock } from '../components/CodeBlock';

// ═══════════════════════════════════════════════════════════════
// 2030-TIER FUTURISTIC PROMO — AgentWallet Protocol
// ═══════════════════════════════════════════════════════════════

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

// ─── Animated Grid Background ────────────────────────────────
const GridBackground = ({ color = theme.colors.purple, speed = 0.5 }) => {
  const frame = useCurrentFrame();
  const offset = frame * speed;

  return (
    <AbsoluteFill>
      {/* Deep space background */}
      <div style={{
        position: 'absolute', inset: 0,
        background: theme.gradients.meshDark,
      }} />

      {/* Perspective grid */}
      <div style={{
        position: 'absolute', inset: 0,
        perspective: '800px',
        perspectiveOrigin: '50% 40%',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          width: '200%', height: '200%',
          left: '-50%', top: '20%',
          transform: `rotateX(65deg) translateY(${-offset % 100}px)`,
          backgroundImage: `
            linear-gradient(rgba(${hexToRgb(color)}, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(${hexToRgb(color)}, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
        }} />
      </div>

      {/* Floating particles */}
      {Array.from({ length: 40 }).map((_, i) => {
        const x = noise2D('px' + i, frame * 0.005, i) * 100;
        const y = noise2D('py' + i, frame * 0.005, i + 100) * 100;
        const size = 1 + Math.abs(noise2D('ps' + i, 0, i)) * 3;
        const alpha = 0.1 + Math.abs(noise2D('pa' + i, frame * 0.01, i)) * 0.4;

        return (
          <div key={i} style={{
            position: 'absolute',
            left: `${50 + x * 0.5}%`,
            top: `${50 + y * 0.5}%`,
            width: size, height: size,
            borderRadius: '50%',
            background: i % 3 === 0 ? theme.colors.purple
              : i % 3 === 1 ? theme.colors.green
              : theme.colors.cyan,
            opacity: alpha,
            boxShadow: `0 0 ${size * 4}px ${i % 3 === 0 ? theme.colors.purple : theme.colors.cyan}`,
          }} />
        );
      })}

      {/* Ambient glow orbs */}
      <div style={{
        position: 'absolute',
        width: 600, height: 600,
        borderRadius: '50%',
        left: `${30 + Math.sin(frame * 0.01) * 10}%`,
        top: `${20 + Math.cos(frame * 0.008) * 10}%`,
        background: `radial-gradient(circle, rgba(${hexToRgb(theme.colors.purple)}, 0.12) 0%, transparent 70%)`,
        filter: 'blur(60px)',
      }} />
      <div style={{
        position: 'absolute',
        width: 500, height: 500,
        borderRadius: '50%',
        right: `${20 + Math.cos(frame * 0.012) * 8}%`,
        bottom: `${15 + Math.sin(frame * 0.009) * 8}%`,
        background: `radial-gradient(circle, rgba(${hexToRgb(theme.colors.cyan)}, 0.08) 0%, transparent 70%)`,
        filter: 'blur(50px)',
      }} />
    </AbsoluteFill>
  );
};

// ─── Holographic Badge ───────────────────────────────────────
const HoloBadge = ({ text, delay = 0, color = theme.colors.purple }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: theme.springs.snappy });
  const shimmer = (frame - delay) * 3;

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      padding: '6px 18px',
      borderRadius: 6,
      background: `linear-gradient(135deg, rgba(${hexToRgb(color)}, 0.15) 0%, rgba(${hexToRgb(color)}, 0.05) 100%)`,
      border: `1px solid rgba(${hexToRgb(color)}, 0.4)`,
      transform: `translateY(${(1 - progress) * 20}px)`,
      opacity: progress,
      overflow: 'hidden',
      position: 'relative',
    }}>
      {/* Shimmer effect */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)`,
        transform: `translateX(${-100 + (shimmer % 200)}%)`,
      }} />
      <div style={{
        width: 6, height: 6, borderRadius: '50%',
        background: color,
        boxShadow: `0 0 8px ${color}`,
      }} />
      <span style={{
        fontSize: 13, fontWeight: 700,
        fontFamily: fontFamily.mono,
        color: color,
        letterSpacing: '2px',
        textTransform: 'uppercase',
        position: 'relative',
      }}>
        {text}
      </span>
    </div>
  );
};

// ─── Stat Counter with Glow ──────────────────────────────────
const GlowStat = ({ value, label, delay = 0, color = theme.colors.green, suffix = '' }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: theme.springs.snappy });
  const count = Math.floor(parseFloat(value) * progress);

  return (
    <div style={{
      textAlign: 'center',
      transform: `scale(${0.8 + progress * 0.2}) translateY(${(1 - progress) * 30}px)`,
      opacity: progress,
    }}>
      <div style={{
        fontSize: 56, fontWeight: 900,
        fontFamily: fontFamily.heading,
        color: color,
        textShadow: `0 0 30px rgba(${hexToRgb(color)}, 0.5), 0 0 60px rgba(${hexToRgb(color)}, 0.2)`,
        lineHeight: 1,
      }}>
        {count}{suffix}
      </div>
      <div style={{
        fontSize: 14, fontWeight: 600,
        fontFamily: fontFamily.mono,
        color: theme.colors.gray,
        letterSpacing: '2px',
        textTransform: 'uppercase',
        marginTop: 8,
      }}>
        {label}
      </div>
    </div>
  );
};

// ─── Neon Divider Line ───────────────────────────────────────
const NeonLine = ({ delay = 0, width = '60%' }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: theme.springs.snappy });

  return (
    <div style={{
      width, height: 2, margin: '20px auto',
      background: theme.gradients.accentBar,
      boxShadow: `0 0 10px ${theme.colors.purple}, 0 0 20px ${theme.colors.cyan}`,
      transform: `scaleX(${progress})`,
      opacity: progress,
    }} />
  );
};

// ═══════════════════════════════════════════════════════════════
// SCENES
// ═══════════════════════════════════════════════════════════════

// Scene 1: INTRO — Logo Reveal + Tagline (0-4s = 0-120f)
const IntroScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBackground color={theme.colors.purple} speed={0.8} />

      {/* Central content */}
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2 }}>
        {/* AW Logo */}
        <div style={{
          width: 100, height: 100, margin: '0 auto 30px',
          background: `linear-gradient(135deg, ${theme.colors.purple}, ${theme.colors.cyan})`,
          borderRadius: 20,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: theme.glow.boxPurple,
          transform: `scale(${spring({ frame, fps, config: theme.springs.bouncy })})`,
        }}>
          <span style={{
            fontSize: 48, fontWeight: 900,
            fontFamily: fontFamily.heading,
            color: '#FFF',
          }}>AW</span>
        </div>

        <GlitchText
          text="AGENTWALLET"
          startFrame={10}
          fontSize={72}
          color={theme.colors.white}
          glitchIntensity={1.5}
          duration={25}
        />

        <div style={{ marginTop: 15 }}>
          <GlitchText
            text="PROTOCOL"
            startFrame={20}
            fontSize={28}
            color={theme.colors.purple}
            glitchIntensity={0.5}
            duration={15}
            mono
          />
        </div>

        <NeonLine delay={35} width="300px" />

        <div style={{
          marginTop: 10,
          opacity: interpolate(frame, [40, 55], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          transform: `translateY(${interpolate(frame, [40, 55], [15, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}px)`,
        }}>
          <span style={{
            fontSize: 18, fontWeight: 500,
            fontFamily: fontFamily.mono,
            color: theme.colors.gray,
            letterSpacing: '4px',
          }}>
            AUTONOMOUS AGENT INFRASTRUCTURE
          </span>
        </div>
      </div>

      <CircuitLines opacity={0.15} />
    </AbsoluteFill>
  );
};

// Scene 2: THE PROBLEM (4-8s = 120-240f)
const ProblemScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const problems = [
    { text: 'Agents leak private keys', icon: 'X' },
    { text: 'No spending controls', icon: 'X' },
    { text: 'Zero accountability on-chain', icon: 'X' },
    { text: 'Manual custody = bottleneck', icon: 'X' },
  ];

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBackground color={theme.colors.red} speed={0.3} />

      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2, maxWidth: 900 }}>
        <HoloBadge text="THE PROBLEM" delay={0} color={theme.colors.red} />

        <div style={{ marginTop: 40 }}>
          <GlitchText
            text="AI AGENTS CAN'T"
            startFrame={15}
            fontSize={56}
            color={theme.colors.white}
            glitchIntensity={0.8}
            duration={20}
          />
        </div>
        <div style={{ marginTop: 5 }}>
          <GlitchText
            text="BE TRUSTED WITH MONEY"
            startFrame={25}
            fontSize={56}
            color={theme.colors.red}
            glitchIntensity={1.2}
            duration={20}
          />
        </div>

        <div style={{
          display: 'flex', flexDirection: 'column', gap: 16,
          marginTop: 50, alignItems: 'center',
        }}>
          {problems.map((p, i) => {
            const itemDelay = 40 + i * 12;
            const progress = spring({ frame: frame - itemDelay, fps, config: theme.springs.slam });
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 16,
                opacity: progress,
                transform: `translateX(${(1 - progress) * -60}px)`,
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8,
                  background: 'rgba(255, 59, 92, 0.15)',
                  border: '1px solid rgba(255, 59, 92, 0.4)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 16, fontWeight: 900, color: theme.colors.red,
                  fontFamily: fontFamily.mono,
                }}>X</div>
                <span style={{
                  fontSize: 22, fontWeight: 600, color: theme.colors.offWhite,
                  fontFamily: fontFamily.heading,
                }}>{p.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 3: THE SOLUTION (8-13s = 240-390f)
const SolutionScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBackground color={theme.colors.green} speed={0.6} />
      <ParticleExplosion startFrame={5} color={theme.colors.green} count={50} />

      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2, maxWidth: 1000 }}>
        <HoloBadge text="THE SOLUTION" delay={0} color={theme.colors.green} />

        <div style={{ marginTop: 40 }}>
          <GlitchText
            text="PDA SPEND POLICIES"
            startFrame={10}
            fontSize={64}
            color={theme.colors.green}
            glitchIntensity={0.6}
            duration={20}
          />
        </div>

        <NeonLine delay={30} width="500px" />

        <div style={{
          fontSize: 24, color: theme.colors.offWhite, marginTop: 20,
          fontFamily: fontFamily.heading, fontWeight: 500,
          opacity: interpolate(frame, [35, 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
        }}>
          Agents get derived wallets with programmable limits.
          <br />
          <span style={{ color: theme.colors.green, fontWeight: 700 }}>
            Zero private key exposure. Ever.
          </span>
        </div>

        {/* Stats row */}
        <div style={{
          display: 'flex', justifyContent: 'center', gap: 80,
          marginTop: 50,
        }}>
          <GlowStat value="12" label="ms settlement" delay={50} color={theme.colors.cyan} suffix="ms" />
          <GlowStat value="33" label="MCP tools" delay={60} color={theme.colors.green} />
          <GlowStat value="0" label="keys exposed" delay={70} color={theme.colors.purple} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 4: CODE SHOWCASE (13-18s = 390-540f)
const CodeScene = () => {
  const frame = useCurrentFrame();

  const code = `// Define agent spend policy
const policy = await AgentWallet.createPolicy({
  agent: agentPubkey,
  maxPerTx: 5_000_000,    // 5 SOL max
  dailyLimit: 50_000_000, // 50 SOL/day
  allowedPrograms: [JUPITER_V6, RAYDIUM],
  requiresMultiSig: false,
  autoRevoke: "30d",
});

// Agent transacts autonomously
const tx = await agent.swap({
  from: "SOL", to: "USDC",
  amount: 2.5,
  // Policy enforced on-chain ✓
});`;

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBackground color={theme.colors.cyan} speed={0.4} />

      <div style={{ position: 'relative', zIndex: 2, maxWidth: 1100, width: '100%', padding: '0 60px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <HoloBadge text="SDK READY" delay={0} color={theme.colors.cyan} />
            <div style={{ marginTop: 30 }}>
              <GlitchText
                text="BUILD IN"
                startFrame={10}
                fontSize={48}
                color={theme.colors.white}
                glitchIntensity={0.4}
                duration={15}
              />
            </div>
            <GlitchText
              text="MINUTES"
              startFrame={18}
              fontSize={48}
              color={theme.colors.cyan}
              glitchIntensity={0.6}
              duration={15}
            />
            <div style={{ marginTop: 30, display: 'flex', gap: 12 }}>
              {['Rust', 'TypeScript', 'Python'].map((lang, i) => (
                <HoloBadge key={lang} text={lang} delay={30 + i * 8} color={theme.colors.purpleLight} />
              ))}
            </div>
          </div>

          <div style={{
            flex: 1.2,
            marginLeft: 40,
            opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
            transform: `translateX(${interpolate(frame, [20, 40], [40, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}px)`,
          }}>
            <CodeBlock
              code={code}
              startFrame={25}
              language="typescript"
              fontSize={13}
              lineHeight={1.6}
            />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 5: VISION — Agent Marketplace (18-23s = 540-690f)
const VisionScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const features = [
    { text: 'Agents hire agents', color: theme.colors.purple },
    { text: 'Trustless escrow', color: theme.colors.green },
    { text: 'On-chain reputation', color: theme.colors.cyan },
    { text: 'Atomic settlements', color: theme.colors.orange },
  ];

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBackground color={theme.colors.purple} speed={0.5} />

      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2 }}>
        <HoloBadge text="2030 VISION" delay={0} color={theme.colors.purple} />

        <div style={{ marginTop: 40 }}>
          <GlitchText
            text="THE AGENT"
            startFrame={10}
            fontSize={64}
            color={theme.colors.white}
            glitchIntensity={0.5}
            duration={18}
          />
        </div>
        <GlitchText
          text="MARKETPLACE"
          startFrame={20}
          fontSize={64}
          color={theme.colors.purple}
          glitchIntensity={0.8}
          duration={18}
        />

        <NeonLine delay={35} />

        <div style={{
          display: 'flex', justifyContent: 'center', gap: 30,
          marginTop: 40, flexWrap: 'wrap',
        }}>
          {features.map((f, i) => {
            const delay = 45 + i * 10;
            const progress = spring({ frame: frame - delay, fps, config: theme.springs.pop });
            return (
              <div key={i} style={{
                padding: '16px 28px',
                borderRadius: 12,
                ...theme.glass.card,
                borderColor: `rgba(${hexToRgb(f.color)}, 0.3)`,
                boxShadow: `0 0 20px rgba(${hexToRgb(f.color)}, 0.15), inset 0 0 20px rgba(${hexToRgb(f.color)}, 0.03)`,
                transform: `scale(${progress}) translateY(${(1 - progress) * 20}px)`,
                opacity: progress,
              }}>
                <span style={{
                  fontSize: 18, fontWeight: 700,
                  color: f.color,
                  fontFamily: fontFamily.heading,
                }}>{f.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Scene 6: CTA — Outro (23-28s = 690-840f)
const OutroScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <GridBackground color={theme.colors.green} speed={1.0} />
      <ParticleExplosion startFrame={10} color={theme.colors.purple} count={80} />

      <div style={{ textAlign: 'center', position: 'relative', zIndex: 2 }}>
        {/* Logo */}
        <div style={{
          width: 80, height: 80, margin: '0 auto 20px',
          background: `linear-gradient(135deg, ${theme.colors.purple}, ${theme.colors.green})`,
          borderRadius: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: theme.glow.boxPurple,
          transform: `scale(${spring({ frame, fps, config: theme.springs.bouncy })})`,
        }}>
          <span style={{
            fontSize: 38, fontWeight: 900, color: '#FFF',
            fontFamily: fontFamily.heading,
          }}>AW</span>
        </div>

        <GlitchText
          text="agentwallet.fun"
          startFrame={15}
          fontSize={56}
          color={theme.colors.white}
          glitchIntensity={0.4}
          duration={20}
        />

        <NeonLine delay={30} width="400px" />

        <div style={{
          marginTop: 15,
          opacity: interpolate(frame, [35, 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
        }}>
          <span style={{
            fontSize: 20, fontWeight: 600,
            fontFamily: fontFamily.heading,
            color: theme.colors.gray,
          }}>
            Built on{' '}
            <span style={{ color: theme.colors.green }}>Solana</span>
            {' | '}
            <span style={{ color: theme.colors.purple }}>Join the Beta</span>
          </span>
        </div>

        <div style={{
          display: 'flex', justifyContent: 'center', gap: 15, marginTop: 30,
        }}>
          <HoloBadge text="DEVNET LIVE" delay={45} color={theme.colors.green} />
          <HoloBadge text="SDK READY" delay={50} color={theme.colors.cyan} />
          <HoloBadge text="OPEN SOURCE" delay={55} color={theme.colors.purple} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ═══════════════════════════════════════════════════════════════
// MAIN COMPOSITION
// ═══════════════════════════════════════════════════════════════
export const FuturisticPromo = () => {
  const SCENE_FRAMES = FPS * 5; // 5 seconds per scene

  return (
    <AbsoluteFill style={{ background: theme.colors.bgDeep }}>
      {/* Brand watermark - always visible */}
      <div style={{
        position: 'absolute', top: 30, left: 30, zIndex: 100,
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '8px 16px',
        background: 'rgba(10, 10, 26, 0.7)',
        borderRadius: 8,
        border: `1px solid rgba(${hexToRgb(theme.colors.purple)}, 0.3)`,
      }}>
        <div style={{
          width: 24, height: 24, borderRadius: 6,
          background: `linear-gradient(135deg, ${theme.colors.purple}, ${theme.colors.cyan})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, fontWeight: 900, color: '#FFF',
          fontFamily: fontFamily.heading,
        }}>AW</div>
        <span style={{
          fontSize: 13, fontWeight: 700, color: theme.colors.white,
          fontFamily: fontFamily.heading, letterSpacing: '1px',
        }}>AgentWallet Protocol</span>
      </div>

      {/* Scene 1: Intro (0-5s) */}
      <Sequence from={0} durationInFrames={SCENE_FRAMES}>
        <IntroScene />
      </Sequence>

      {/* Scene 2: Problem (5-9s) */}
      <Sequence from={SCENE_FRAMES} durationInFrames={SCENE_FRAMES - 30}>
        <ProblemScene />
      </Sequence>

      {/* Scene 3: Solution (9-14s) */}
      <Sequence from={SCENE_FRAMES * 2 - 30} durationInFrames={SCENE_FRAMES}>
        <SolutionScene />
      </Sequence>

      {/* Scene 4: Code (14-19s) */}
      <Sequence from={SCENE_FRAMES * 3 - 30} durationInFrames={SCENE_FRAMES}>
        <CodeScene />
      </Sequence>

      {/* Scene 5: Vision (19-24s) */}
      <Sequence from={SCENE_FRAMES * 4 - 30} durationInFrames={SCENE_FRAMES}>
        <VisionScene />
      </Sequence>

      {/* Scene 6: CTA (24-28s) */}
      <Sequence from={SCENE_FRAMES * 5 - 30} durationInFrames={SCENE_FRAMES}>
        <OutroScene />
      </Sequence>
    </AbsoluteFill>
  );
};
