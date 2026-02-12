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
  FadeSlide,
  ArchNode,
  Arrow,
  Badge,
  TechTag,
  LogoReveal,
  ParticleExplosion,
  CodeBlock,
  GlitchText,
  CircuitLines,
  NumberCounter,
  StatCounter,
} from '../components';

// ═══════════════════════════════════════════════════════════
// Scene 1: Logo Reveal (0-5s)
// ═══════════════════════════════════════════════════════════
const LogoScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <Background
      variant="dark"
      showLightRays
      lightRayCorner="center"
      particleCount={40}
      vignetteIntensity={0.65}
      orbs={[
        { color: theme.colors.purple, size: 600, top: '10%', left: '40%', delay: 5 },
        { color: theme.colors.cyan, size: 350, top: '60%', left: '60%', delay: 15 },
      ]}
    >
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Particle explosion at start */}
        <ParticleExplosion
          startFrame={5}
          x="50%"
          y="45%"
          count={50}
          color={theme.colors.purple}
          secondaryColor={theme.colors.green}
          duration={40}
          spread={350}
        />

        {/* Logo reveal */}
        <LogoReveal
          startFrame={8}
          text="AgentWallet"
          highlightText="Wallet"
          tagline="Autonomous Wallet Infrastructure for AI Agents"
          fontSize={80}
        />

        {/* Solana badge */}
        <FadeSlide startFrame={70} duration={15} direction="up">
          <div
            style={{
              marginTop: 40,
              fontSize: 12,
              fontWeight: 600,
              color: theme.colors.green,
              letterSpacing: 3,
              fontFamily: fontFamily.mono,
              ...theme.glass.subtle,
              padding: '8px 20px',
            }}
          >
            ◎ BUILT ON SOLANA
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 2: Architecture Diagram (5-15s)
// ═══════════════════════════════════════════════════════════
const ArchitectureScene = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  // Circuit line paths connecting nodes
  const circuitPaths = [
    {
      points: [
        { x: 100, y: 180 }, { x: 200, y: 180 }, { x: 200, y: 300 },
        { x: 350, y: 300 },
      ],
      color: theme.colors.purple,
      delay: 30,
    },
    {
      points: [
        { x: width - 100, y: 200 }, { x: width - 200, y: 200 },
        { x: width - 200, y: 350 }, { x: width - 380, y: 350 },
      ],
      color: theme.colors.cyan,
      delay: 40,
    },
    {
      points: [
        { x: 120, y: height - 200 }, { x: 280, y: height - 200 },
        { x: 280, y: height - 320 },
      ],
      color: theme.colors.green,
      delay: 50,
    },
  ];

  return (
    <Background
      variant="default"
      showLightRays
      lightRayCorner="topRight"
      particleCount={25}
      orbs={[
        { color: theme.colors.purple, size: 500, top: '-10%', left: '60%', delay: 0 },
        { color: theme.colors.cyan, size: 350, top: '65%', left: '10%', delay: 10 },
      ]}
    >
      {/* Circuit traces in background */}
      <CircuitLines
        paths={circuitPaths}
        width={width}
        height={height}
        startFrame={25}
      />

      <AbsoluteFill style={{ padding: isVertical ? '50px 30px' : '50px 60px' }}>
        {/* Header */}
        <FadeSlide startFrame={0} duration={12}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 24,
            }}
          >
            <GlitchText
              text="Architecture"
              startFrame={2}
              color={theme.colors.purple}
              fontSize={14}
              fontWeight={700}
              mono
              duration={12}
            />
            <Badge text="Protocol v2.0" startFrame={5} color={theme.colors.cyan} />
          </div>
        </FadeSlide>

        {/* Title */}
        <FadeSlide startFrame={8} duration={15} scale={0.97}>
          <div
            style={{
              fontSize: isVertical ? 32 : 40,
              fontWeight: 800,
              color: theme.colors.white,
              letterSpacing: -1.5,
              marginBottom: 6,
              fontFamily: fontFamily.heading,
              textShadow: theme.glow.textSubtle,
            }}
          >
            How <span style={{ color: theme.colors.purple }}>AgentWallet</span> Works
          </div>
          <div
            style={{
              fontSize: 15,
              color: theme.colors.dim,
              marginBottom: isVertical ? 40 : 48,
              fontFamily: fontFamily.heading,
            }}
          >
            End-to-end autonomous infrastructure on Solana
          </div>
        </FadeSlide>

        {/* Architecture flow */}
        <div
          style={{
            display: 'flex',
            alignItems: isVertical ? 'flex-start' : 'center',
            justifyContent: 'center',
            flexDirection: isVertical ? 'column' : 'row',
            gap: isVertical ? 10 : 0,
            flexWrap: 'nowrap',
          }}
        >
          <ArchNode
            label="Agent"
            name="AI Agent"
            desc="Claude / GPT"
            icon="🤖"
            color={theme.colors.cyan}
            startFrame={20}
          />
          <Arrow startFrame={28} color={theme.colors.cyan} direction={isVertical ? 'down' : 'right'} />
          <ArchNode
            label="Interface"
            name="MCP Server"
            desc="27 tools"
            icon="⚡"
            color={theme.colors.purple}
            startFrame={32}
          />
          <Arrow startFrame={40} color={theme.colors.purple} direction={isVertical ? 'down' : 'right'} />
          <ArchNode
            label="Protocol"
            name="AgentWallet"
            desc="PDA · Escrow · x402"
            icon="🔐"
            color={theme.colors.purple}
            startFrame={44}
            size="large"
          />
          <Arrow startFrame={52} color={theme.colors.green} direction={isVertical ? 'down' : 'right'} />
          <ArchNode
            label="Chain"
            name="Solana"
            desc="SOL · USDC"
            icon="◎"
            color={theme.colors.green}
            startFrame={56}
          />
          {!isVertical && (
            <>
              <Arrow startFrame={64} color={theme.colors.orange} />
              <ArchNode
                label="Commerce"
                name="A2A Market"
                desc="Jobs · Rep"
                icon="🏪"
                color={theme.colors.orange}
                startFrame={68}
              />
            </>
          )}
        </div>

        {/* Tech tags */}
        <FadeSlide startFrame={80} duration={15}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 14,
              marginTop: isVertical ? 30 : 48,
              flexWrap: 'wrap',
            }}
          >
            {['Solana', 'MCP', 'x402', 'PDA', 'SPL', 'USDC', 'A2A'].map(
              (tag, i) => (
                <TechTag key={tag} text={tag} startFrame={80} delay={i * 4} />
              )
            )}
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 3: Code Demo (15-25s)
// ═══════════════════════════════════════════════════════════
const CodeScene = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  const codeText = `# Create an agent wallet
wallet = await mcp.call("create_wallet", {
    "agent_id": "claude-prod-01",
    "network": "mainnet-beta"
})

# Response: PDA wallet created
# address: "7xKXt...9mPq"
# balance: 0.0 SOL`;

  // Response card appears after code is typed
  const responseDelay = 80;

  return (
    <Background
      variant="default"
      showScanLine
      showLightRays
      lightRayCorner="topLeft"
      particleCount={15}
      orbs={[
        { color: theme.colors.green, size: 450, top: '-5%', left: '65%', delay: 0 },
        { color: theme.colors.purple, size: 300, top: '70%', left: '15%', delay: 10 },
      ]}
    >
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: isVertical ? '50px 30px' : '50px 80px',
        }}
      >
        {/* Section label */}
        <FadeSlide startFrame={0} duration={10}>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: theme.colors.green,
              letterSpacing: 3,
              textTransform: 'uppercase',
              marginBottom: 24,
              fontFamily: fontFamily.mono,
            }}
          >
            ⚡ LIVE CODE DEMO
          </div>
        </FadeSlide>

        {/* Code block with typing */}
        <CodeBlock
          code={codeText}
          startFrame={8}
          typingSpeed={1.8}
          title="create_wallet.py"
          accentColor={theme.colors.green}
          maxWidth={isVertical ? 500 : 650}
          fontSize={isVertical ? 13 : 14}
        />

        {/* Response card */}
        <FadeSlide startFrame={responseDelay} duration={15} direction="up" scale={0.95}>
          <div
            style={{
              marginTop: 24,
              ...theme.glass.card,
              padding: '20px 28px',
              maxWidth: isVertical ? 500 : 650,
              width: '100%',
            }}
          >
            <div
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: theme.colors.green,
                letterSpacing: 2,
                marginBottom: 10,
                fontFamily: fontFamily.mono,
              }}
            >
              ✓ RESPONSE
            </div>
            <div
              style={{
                fontSize: 13,
                color: theme.colors.offWhite,
                fontFamily: fontFamily.mono,
                lineHeight: 1.8,
              }}
            >
              <span style={{ color: theme.colors.dim }}>address:</span>{' '}
              <span style={{ color: theme.colors.green }}>7xKXtQ...9mPqW</span>
              <br />
              <span style={{ color: theme.colors.dim }}>network:</span>{' '}
              <span style={{ color: theme.colors.cyan }}>mainnet-beta</span>
              <br />
              <span style={{ color: theme.colors.dim }}>status:</span>{' '}
              <span style={{ color: theme.colors.green }}>active ✓</span>
            </div>
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 4: Transaction Flow (25-35s)
// ═══════════════════════════════════════════════════════════
const TransactionScene = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  // SOL token moving along path
  const pathProgress = interpolate(frame, [30, 120], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const pathEased = easing.easeInOutCubic(pathProgress);

  // Policy gate open/close
  const gateOpen = spring({
    frame,
    fps,
    delay: 60,
    config: theme.springs.snappy,
  });

  const rgb = hexToRgb(theme.colors.green);

  return (
    <Background
      variant="default"
      showLightRays
      particleCount={20}
      orbs={[
        { color: theme.colors.orange, size: 500, top: '-10%', left: '30%', delay: 0 },
        { color: theme.colors.green, size: 400, top: '55%', left: '65%', delay: 8 },
      ]}
    >
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: isVertical ? '50px 30px' : '50px 60px',
        }}
      >
        {/* Title */}
        <FadeSlide startFrame={0} duration={12}>
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <div
              style={{
                fontSize: 12,
                fontWeight: 700,
                color: theme.colors.orange,
                letterSpacing: 3,
                textTransform: 'uppercase',
                marginBottom: 12,
                fontFamily: fontFamily.mono,
              }}
            >
              TRANSACTION FLOW
            </div>
            <div
              style={{
                fontSize: isVertical ? 30 : 36,
                fontWeight: 800,
                color: theme.colors.white,
                fontFamily: fontFamily.heading,
                letterSpacing: -1,
                textShadow: theme.glow.textSubtle,
              }}
            >
              Policy-Validated Transfers
            </div>
          </div>
        </FadeSlide>

        {/* Flow diagram */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 0,
            position: 'relative',
            flexDirection: isVertical ? 'column' : 'row',
          }}
        >
          <ArchNode
            label="Agent"
            name="Transfer Req"
            icon="🤖"
            color={theme.colors.cyan}
            startFrame={15}
          />
          <Arrow startFrame={25} color={theme.colors.cyan} direction={isVertical ? 'down' : 'right'} length={60} />

          {/* Policy Gate */}
          <div style={{ position: 'relative' }}>
            <ArchNode
              label="Validate"
              name="Policy Check"
              icon={gateOpen > 0.5 ? '✅' : '🔒'}
              color={theme.colors.orange}
              startFrame={35}
              size="large"
            />
            {/* Gate indicator */}
            <div
              style={{
                position: 'absolute',
                bottom: -20,
                left: '50%',
                transform: 'translateX(-50%)',
                fontSize: 10,
                fontWeight: 700,
                color: gateOpen > 0.5 ? theme.colors.green : theme.colors.orange,
                fontFamily: fontFamily.mono,
                letterSpacing: 2,
                opacity: interpolate(frame, [50, 60], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
              }}
            >
              {gateOpen > 0.5 ? 'APPROVED' : 'CHECKING...'}
            </div>
          </div>

          <Arrow startFrame={70} color={theme.colors.green} direction={isVertical ? 'down' : 'right'} length={60} />

          <ArchNode
            label="Execute"
            name="SOL Transfer"
            icon="◎"
            color={theme.colors.green}
            startFrame={80}
          />
        </div>

        {/* SOL token icon moving along path */}
        {pathProgress > 0 && pathProgress < 1 && !isVertical && (
          <div
            style={{
              position: 'absolute',
              top: '48%',
              left: `${20 + pathEased * 60}%`,
              fontSize: 24,
              filter: `drop-shadow(0 0 12px rgba(${rgb}, 0.8))`,
              transform: 'translate(-50%, -50%)',
              zIndex: 10,
            }}
          >
            ◎
          </div>
        )}

        {/* Transaction details */}
        <FadeSlide startFrame={100} duration={15}>
          <div
            style={{
              marginTop: 40,
              ...theme.glass.card,
              padding: '16px 28px',
              display: 'flex',
              gap: 40,
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            {[
              { label: 'Amount', value: '2.5 SOL', color: theme.colors.green },
              { label: 'Fee', value: '0.000005 SOL', color: theme.colors.dim },
              { label: 'Status', value: 'Confirmed ✓', color: theme.colors.green },
              { label: 'Block', value: '#298,441,203', color: theme.colors.cyan },
            ].map((item) => (
              <div key={item.label} style={{ textAlign: 'center' }}>
                <div
                  style={{
                    fontSize: 10,
                    color: theme.colors.muted,
                    fontFamily: fontFamily.mono,
                    letterSpacing: 1.5,
                    textTransform: 'uppercase',
                  }}
                >
                  {item.label}
                </div>
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: 700,
                    color: item.color,
                    fontFamily: fontFamily.mono,
                    marginTop: 4,
                  }}
                >
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// Scene 5: Stats CTA (35-40s)
// ═══════════════════════════════════════════════════════════
const StatsCTAScene = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  return (
    <Background
      variant="energy"
      showLightRays
      lightRayCorner="center"
      particleCount={35}
      vignetteIntensity={0.5}
      orbs={[
        { color: theme.colors.purple, size: 700, top: '-15%', left: '35%', delay: 0 },
        { color: theme.colors.green, size: 500, top: '50%', left: '55%', delay: 5 },
        { color: theme.colors.cyan, size: 300, top: '10%', left: '75%', delay: 10 },
      ]}
    >
      <ParticleExplosion
        startFrame={5}
        x="50%"
        y="40%"
        count={35}
        color={theme.colors.purple}
        secondaryColor={theme.colors.green}
        duration={30}
        spread={200}
      />

      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: isVertical ? '60px 30px' : '40px 60px',
        }}
      >
        {/* Stats fly in */}
        <div
          style={{
            display: 'flex',
            gap: isVertical ? 20 : 30,
            marginBottom: 40,
            flexDirection: isVertical ? 'column' : 'row',
            alignItems: 'center',
          }}
        >
          <StatCounter
            value="27"
            label="MCP Tools"
            color={theme.colors.purple}
            startFrame={10}
            size="large"
          />
          <StatCounter
            value="0"
            label="Private Keys"
            color={theme.colors.green}
            startFrame={18}
            size="large"
          />
          <StatCounter
            value="100"
            suffix="%"
            label="On-Chain"
            color={theme.colors.cyan}
            startFrame={26}
            size="large"
          />
        </div>

        {/* CTA */}
        <FadeSlide startFrame={40} duration={15} scale={0.95}>
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                fontSize: isVertical ? 48 : 52,
                fontWeight: 900,
                color: theme.colors.white,
                fontFamily: fontFamily.heading,
                letterSpacing: -2,
                textShadow: theme.glow.textPurple,
                marginBottom: 16,
              }}
            >
              agent<span style={{ color: theme.colors.purple }}>wallet</span>.fun
            </div>

            <FadeSlide startFrame={55} duration={12}>
              <div
                style={{
                  fontSize: 14,
                  color: theme.colors.gray,
                  fontFamily: fontFamily.mono,
                  ...theme.glass.subtle,
                  padding: '10px 28px',
                  display: 'inline-block',
                }}
              >
                pip install agentwallet-mcp
              </div>
            </FadeSlide>
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

// ═══════════════════════════════════════════════════════════
// MAIN COMPOSITION
// ═══════════════════════════════════════════════════════════
export const ArchExplainer = ({ voiceoverSrc }) => {
  const { fps } = useVideoConfig();
  const sec = (s) => Math.round(s * fps);

  return (
    <AbsoluteFill>
      {voiceoverSrc && <Audio src={voiceoverSrc} volume={1} />}

      {/* Scene 1: Logo Reveal (0-5s) */}
      <Sequence from={0} durationInFrames={sec(5)}>
        <LogoScene />
      </Sequence>

      {/* Scene 2: Architecture (5-15s) */}
      <Sequence from={sec(5)} durationInFrames={sec(10)}>
        <ArchitectureScene />
      </Sequence>

      {/* Scene 3: Code Demo (15-25s) */}
      <Sequence from={sec(15)} durationInFrames={sec(10)}>
        <CodeScene />
      </Sequence>

      {/* Scene 4: Transaction Flow (25-35s) */}
      <Sequence from={sec(25)} durationInFrames={sec(10)}>
        <TransactionScene />
      </Sequence>

      {/* Scene 5: Stats CTA (35-40s) */}
      <Sequence from={sec(35)} durationInFrames={sec(5)}>
        <StatsCTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};
