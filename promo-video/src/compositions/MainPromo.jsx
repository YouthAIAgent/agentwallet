import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  Audio,
} from 'remotion';
import { noise2D } from '@remotion/noise';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';
import {
  Background,
  TypeWriter,
  FadeSlide,
  StatCounter,
  ArchNode,
  Arrow,
  Badge,
  TechTag,
  GlitchText,
  CodeBlock,
  LogoReveal,
  ParticleExplosion,
  CircuitLines,
  WaveformVisualizer,
} from '../components';

// ═══════════════════════════════════════════════════════════
// Scene 1: Cinematic Opening (0-5s)
// Single cursor blink → "pip install agentwallet-mcp" types out
// ═══════════════════════════════════════════════════════════
const CinematicOpening = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  // Just a cursor blinking for the first 30 frames
  const cursorOnly = frame < 30;
  const cursorBlink = frame % 30 < 18;

  // Typing starts at frame 30
  const typingStart = 30;

  return (
    <Background
      variant="terminal"
      showGrid={false}
      showParticles={false}
      showNoise
      showVignette
      vignetteIntensity={0.7}
    >
      <AbsoluteFill
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            maxWidth: isVertical ? 500 : 700,
            width: '100%',
            padding: '0 40px',
          }}
        >
          {/* Minimal terminal window */}
          <div
            style={{
              background: 'rgba(10, 10, 20, 0.9)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 12,
              overflow: 'hidden',
              boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
            }}
          >
            {/* Title bar */}
            <div
              style={{
                display: 'flex',
                gap: 7,
                padding: '12px 16px',
                background: 'rgba(255,255,255,0.02)',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
                alignItems: 'center',
              }}
            >
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FF5F57' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FEBC2E' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#28C840' }} />
              <span
                style={{
                  fontSize: 11,
                  color: theme.colors.muted,
                  marginLeft: 12,
                  fontFamily: fontFamily.mono,
                }}
              >
                terminal
              </span>
            </div>

            {/* Terminal content */}
            <div style={{ padding: '24px 24px' }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span
                  style={{
                    fontSize: isVertical ? 16 : 18,
                    color: theme.colors.green,
                    fontFamily: fontFamily.mono,
                    fontWeight: 500,
                    marginRight: 10,
                  }}
                >
                  $
                </span>
                {cursorOnly ? (
                  <span
                    style={{
                      fontSize: isVertical ? 16 : 18,
                      color: theme.colors.green,
                      fontFamily: fontFamily.mono,
                      opacity: cursorBlink ? 1 : 0,
                    }}
                  >
                    ▌
                  </span>
                ) : (
                  <TypeWriter
                    text="pip install agentwallet-mcp"
                    startFrame={typingStart}
                    speed={1.5}
                    color={theme.colors.offWhite}
                    fontSize={isVertical ? 16 : 18}
                    fontWeight={500}
                    cursorColor={theme.colors.green}
                    mono
                  />
                )}
              </div>

              {/* Install output after typing */}
              {frame > typingStart + 50 && (
                <div style={{ marginTop: 16 }}>
                  <FadeSlide startFrame={typingStart + 50} duration={8}>
                    <div style={{ fontSize: 13, color: theme.colors.dim, fontFamily: fontFamily.mono, lineHeight: 1.8 }}>
                      <span style={{ color: theme.colors.green }}>✓</span> Installing agentwallet-mcp v2.0.0
                      <br />
                      <span style={{ color: theme.colors.green }}>✓</span> 27 MCP tools loaded
                      <br />
                      <span style={{ color: theme.colors.green }}>✓</span> Connected to Solana mainnet
                      <br />
                      <span style={{ color: theme.colors.cyan }}>→</span>{' '}
                      <span style={{ color: theme.colors.cyan }}>Ready. Your agent deserves a wallet.</span>
                    </div>
                  </FadeSlide>
                </div>
              )}
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 2: Hero Reveal (5-10s)
// Terminal morphs into hero + architecture
// ═══════════════════════════════════════════════════════════
const HeroScene = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  const titleScale = spring({
    frame,
    fps,
    delay: 5,
    config: theme.springs.snappy,
  });

  return (
    <Background
      variant="energy"
      showLightRays
      lightRayCorner="topRight"
      particleCount={30}
      orbs={[
        { color: theme.colors.purple, size: 600, top: '-20%', left: '40%', delay: 0 },
        { color: theme.colors.green, size: 400, top: '60%', left: '-5%', delay: 10 },
      ]}
    >
      <ParticleExplosion
        startFrame={3}
        x="50%"
        y="40%"
        count={40}
        color={theme.colors.purple}
        secondaryColor={theme.colors.cyan}
        duration={35}
        spread={300}
      />

      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <FadeSlide startFrame={0} duration={15}>
          <div
            style={{
              fontSize: 13,
              color: theme.colors.purple,
              fontWeight: 700,
              letterSpacing: 4,
              textTransform: 'uppercase',
              marginBottom: 20,
              fontFamily: fontFamily.mono,
            }}
          >
            The Agentic Economy Starts Here
          </div>
        </FadeSlide>

        <div
          style={{
            textAlign: 'center',
            transform: `scale(${titleScale})`,
          }}
        >
          <GlitchText
            text="AgentWallet"
            startFrame={5}
            color={theme.colors.white}
            fontSize={isVertical ? 56 : 72}
            fontWeight={900}
            duration={20}
          />
          <div
            style={{
              fontSize: isVertical ? 56 : 72,
              fontWeight: 900,
              color: theme.colors.white,
              letterSpacing: -3,
              lineHeight: 1.05,
              fontFamily: fontFamily.heading,
              opacity: interpolate(frame, [10, 20], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
            }}
          >
            Protocol
          </div>
        </div>

        <FadeSlide startFrame={25} duration={15}>
          <div
            style={{
              fontSize: isVertical ? 18 : 20,
              color: theme.colors.gray,
              marginTop: 24,
              textAlign: 'center',
              fontFamily: fontFamily.heading,
              maxWidth: 550,
            }}
          >
            Autonomous wallet infrastructure for AI agents on Solana
          </div>
        </FadeSlide>

        <FadeSlide startFrame={40} duration={15}>
          <div
            style={{
              display: 'flex',
              gap: isVertical ? 16 : 20,
              marginTop: 48,
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}
          >
            <StatCounter value="27" label="MCP Tools" color={theme.colors.purple} startFrame={42} />
            <StatCounter value="0" label="Keys Needed" color={theme.colors.green} startFrame={47} />
            <StatCounter value="100" suffix="%" label="Trustless" color={theme.colors.cyan} startFrame={52} />
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 3: Architecture (10-16s)
// ═══════════════════════════════════════════════════════════
const ArchitectureScene = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  return (
    <Background
      variant="default"
      showLightRays
      lightRayCorner="topRight"
      particleCount={20}
      orbs={[
        { color: theme.colors.purple, size: 500, top: '-10%', left: '65%', delay: 0 },
        { color: theme.colors.cyan, size: 300, top: '70%', left: '10%', delay: 15 },
      ]}
    >
      <CircuitLines
        width={width}
        height={height}
        startFrame={15}
        color={theme.colors.purple}
        secondaryColor={theme.colors.cyan}
      />

      <AbsoluteFill style={{ padding: isVertical ? '50px 30px' : '50px 60px' }}>
        <FadeSlide startFrame={0} duration={12}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 24,
            }}
          >
            <div
              style={{
                fontSize: 14,
                fontWeight: 700,
                color: theme.colors.purple,
                fontFamily: fontFamily.mono,
              }}
            >
              ◎ AgentWallet
            </div>
            <Badge text="Architecture" startFrame={5} color={theme.colors.cyan} />
          </div>
        </FadeSlide>

        <FadeSlide startFrame={8} duration={15} scale={0.97}>
          <div
            style={{
              fontSize: isVertical ? 30 : 38,
              fontWeight: 800,
              color: theme.colors.white,
              letterSpacing: -1,
              marginBottom: 6,
              fontFamily: fontFamily.heading,
              textShadow: theme.glow.textSubtle,
            }}
          >
            How <span style={{ color: theme.colors.purple }}>It</span> Works
          </div>
          <div
            style={{
              fontSize: 15,
              color: theme.colors.dim,
              marginBottom: 48,
              fontFamily: fontFamily.heading,
            }}
          >
            End-to-end autonomous wallet infrastructure
          </div>
        </FadeSlide>

        {/* Flow */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: isVertical ? 'column' : 'row',
            gap: isVertical ? 8 : 0,
          }}
        >
          <ArchNode label="Agent" name="AI Agent" icon="🤖" color={theme.colors.cyan} startFrame={20} />
          <Arrow startFrame={28} color={theme.colors.cyan} direction={isVertical ? 'down' : 'right'} />
          <ArchNode label="Interface" name="MCP Server" icon="⚡" color={theme.colors.purple} startFrame={32} />
          <Arrow startFrame={40} color={theme.colors.purple} direction={isVertical ? 'down' : 'right'} />
          <ArchNode label="Protocol" name="AgentWallet" icon="🔐" color={theme.colors.purple} startFrame={44} size="large" />
          <Arrow startFrame={52} color={theme.colors.green} direction={isVertical ? 'down' : 'right'} />
          <ArchNode label="Chain" name="Solana" icon="◎" color={theme.colors.green} startFrame={56} />
        </div>

        <FadeSlide startFrame={70} duration={15}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 14,
              marginTop: 48,
              flexWrap: 'wrap',
            }}
          >
            {['PDA', 'Escrow', 'x402', 'Jupiter', 'SPL'].map((tag, i) => (
              <TechTag key={tag} text={tag} startFrame={70} delay={i * 4} />
            ))}
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 4: Features Montage (16-22s)
// ═══════════════════════════════════════════════════════════
const FeaturesMontage = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  const features = [
    { icon: '🔐', name: 'PDA Vaults', desc: 'No private keys needed', color: theme.colors.purple },
    { icon: '💰', name: 'Stablecoins', desc: 'USDC + USDT native', color: theme.colors.green },
    { icon: '🤝', name: 'Escrow', desc: 'Trustless A2A payments', color: theme.colors.cyan },
    { icon: '⚡', name: 'x402', desc: 'HTTP micropayments', color: theme.colors.orange },
    { icon: '📊', name: 'Policies', desc: 'Full spend control', color: theme.colors.pink },
    { icon: '🏪', name: 'Marketplace', desc: 'Agent economy', color: theme.colors.cyan },
  ];

  return (
    <Background
      variant="default"
      showLightRays
      lightRayCorner="topLeft"
      particleCount={20}
      orbs={[
        { color: theme.colors.green, size: 500, top: '-10%', left: '55%', delay: 0 },
        { color: theme.colors.purple, size: 350, top: '65%', left: '-5%', delay: 10 },
      ]}
    >
      <AbsoluteFill style={{ padding: isVertical ? '50px 30px' : '50px 60px' }}>
        <FadeSlide startFrame={0} duration={12}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: theme.colors.green,
              marginBottom: 8,
              fontFamily: fontFamily.mono,
            }}
          >
            ◎ Features
          </div>
          <div
            style={{
              fontSize: isVertical ? 30 : 38,
              fontWeight: 800,
              color: theme.colors.white,
              letterSpacing: -1,
              marginBottom: 40,
              fontFamily: fontFamily.heading,
              textShadow: theme.glow.textSubtle,
            }}
          >
            27 tools. <span style={{ color: theme.colors.green }}>One SDK.</span>
          </div>
        </FadeSlide>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: isVertical ? '1fr 1fr' : '1fr 1fr 1fr',
            gap: 16,
          }}
        >
          {features.map((f, i) => {
            const cardScale = spring({
              frame,
              fps,
              delay: 15 + i * 6,
              config: theme.springs.slam,
            });
            const rgb = hexToRgb(f.color);

            return (
              <div
                key={i}
                style={{
                  transform: `scale(${cardScale})`,
                  ...theme.glass.card,
                  padding: isVertical ? 18 : 24,
                  overflow: 'hidden',
                  position: 'relative',
                }}
              >
                {/* Top edge glow */}
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: '15%',
                    right: '15%',
                    height: 1,
                    background: `linear-gradient(90deg, transparent, rgba(${rgb}, 0.3), transparent)`,
                    pointerEvents: 'none',
                  }}
                />
                <div style={{ fontSize: isVertical ? 24 : 28, marginBottom: 8 }}>{f.icon}</div>
                <div
                  style={{
                    fontSize: isVertical ? 16 : 18,
                    fontWeight: 700,
                    color: theme.colors.offWhite,
                    marginBottom: 4,
                    fontFamily: fontFamily.heading,
                  }}
                >
                  {f.name}
                </div>
                <div
                  style={{
                    fontSize: isVertical ? 12 : 13,
                    color: theme.colors.dim,
                    lineHeight: 1.5,
                    fontFamily: fontFamily.heading,
                  }}
                >
                  {f.desc}
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 5: Testimonial / Social Proof (22-26s)
// ═══════════════════════════════════════════════════════════
const TestimonialScene = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  const quotes = [
    { text: '"The missing piece for autonomous AI agents."', attribution: '— AI Developer' },
    { text: '"Finally, agent wallets without private key nightmares."', attribution: '— Solana Builder' },
  ];

  return (
    <Background
      variant="dark"
      showLightRays
      lightRayCorner="center"
      particleCount={15}
      vignetteIntensity={0.65}
      orbs={[
        { color: theme.colors.purple, size: 500, top: '20%', left: '40%', delay: 0 },
      ]}
    >
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '60px 80px',
        }}
      >
        {quotes.map((q, i) => (
          <FadeSlide key={i} startFrame={i * 60} duration={15} scale={0.97}>
            <div
              style={{
                textAlign: 'center',
                marginBottom: 40,
                opacity: interpolate(frame, [i * 60, i * 60 + 15, i * 60 + 100, i * 60 + 115], [0, 1, 1, 0.3], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
              }}
            >
              <div
                style={{
                  fontSize: isVertical ? 28 : 32,
                  fontWeight: 600,
                  color: theme.colors.offWhite,
                  fontFamily: fontFamily.heading,
                  lineHeight: 1.4,
                  fontStyle: 'italic',
                  maxWidth: 700,
                  textShadow: theme.glow.textSubtle,
                }}
              >
                {q.text}
              </div>
              <div
                style={{
                  fontSize: 14,
                  color: theme.colors.dim,
                  marginTop: 16,
                  fontFamily: fontFamily.mono,
                }}
              >
                {q.attribution}
              </div>
            </div>
          </FadeSlide>
        ))}

        {/* Waveform visualizer for vibe */}
        <FadeSlide startFrame={20} duration={15}>
          <WaveformVisualizer
            startFrame={20}
            barCount={48}
            width={isVertical ? 400 : 500}
            height={60}
            color={theme.colors.purple}
            secondaryColor={theme.colors.cyan}
            intensity={0.6}
            style={{ marginTop: 20, opacity: 0.4 }}
          />
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 6: Epic CTA (26-30s)
// Everything converges → logo + tagline
// ═══════════════════════════════════════════════════════════
const EpicCTA = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  const pulse = Math.sin(frame * 0.1) * 0.06 + 1;

  return (
    <Background
      variant="energy"
      showLightRays
      lightRayCorner="center"
      particleCount={40}
      vignetteIntensity={0.5}
      orbs={[
        { color: theme.colors.purple, size: 700, top: '-15%', left: '35%', delay: 0 },
        { color: theme.colors.green, size: 500, top: '55%', left: '55%', delay: 5 },
      ]}
    >
      <ParticleExplosion
        startFrame={5}
        x="50%"
        y="45%"
        count={50}
        color={theme.colors.purple}
        secondaryColor={theme.colors.green}
        duration={40}
        spread={300}
      />

      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Logo reveal */}
        <LogoReveal
          startFrame={5}
          text="AgentWallet"
          highlightText="Wallet"
          tagline="Your Agent Deserves a Wallet"
          fontSize={isVertical ? 56 : 72}
        />

        {/* Install command */}
        <FadeSlide startFrame={55} duration={12}>
          <div
            style={{
              marginTop: 40,
              ...theme.glass.card,
              padding: '14px 32px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <span
              style={{
                fontSize: 14,
                color: theme.colors.green,
                fontFamily: fontFamily.mono,
              }}
            >
              $
            </span>
            <span
              style={{
                fontSize: 14,
                color: theme.colors.offWhite,
                fontFamily: fontFamily.mono,
              }}
            >
              pip install agentwallet-mcp
            </span>
          </div>
        </FadeSlide>

        {/* Links */}
        <FadeSlide startFrame={70} duration={12}>
          <div
            style={{
              display: 'flex',
              gap: 24,
              marginTop: 24,
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: 12, color: theme.colors.dim, fontFamily: fontFamily.mono }}>
              agentwallet.fun
            </span>
            <span style={{ fontSize: 12, color: theme.colors.muted }}>|</span>
            <span style={{ fontSize: 12, color: theme.colors.dim, fontFamily: fontFamily.mono }}>
              github.com/YouthAIAgent/agentwallet
            </span>
          </div>
        </FadeSlide>

        {/* Branding */}
        <FadeSlide startFrame={80} duration={12}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: theme.colors.purple,
              marginTop: 40,
              fontFamily: fontFamily.mono,
            }}
          >
            @Web3__Youth · ◎ Solana
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// MAIN COMPOSITION
// ═══════════════════════════════════════════════════════════
export const MainPromo = ({ voiceoverSrc }) => {
  const { fps } = useVideoConfig();
  const sec = (s) => Math.round(s * fps);

  return (
    <AbsoluteFill>
      {voiceoverSrc && <Audio src={voiceoverSrc} volume={1} />}

      {/* Scene 1: Cinematic Opening (0-5s) */}
      <Sequence from={0} durationInFrames={sec(5)}>
        <CinematicOpening />
      </Sequence>

      {/* Scene 2: Hero (5-10s) */}
      <Sequence from={sec(5)} durationInFrames={sec(5)}>
        <HeroScene />
      </Sequence>

      {/* Scene 3: Architecture (10-16s) */}
      <Sequence from={sec(10)} durationInFrames={sec(6)}>
        <ArchitectureScene />
      </Sequence>

      {/* Scene 4: Features Montage (16-22s) */}
      <Sequence from={sec(16)} durationInFrames={sec(6)}>
        <FeaturesMontage />
      </Sequence>

      {/* Scene 5: Testimonials (22-26s) */}
      <Sequence from={sec(22)} durationInFrames={sec(4)}>
        <TestimonialScene />
      </Sequence>

      {/* Scene 6: Epic CTA (26-30s) */}
      <Sequence from={sec(26)} durationInFrames={sec(4)}>
        <EpicCTA />
      </Sequence>
    </AbsoluteFill>
  );
};
