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
import { Background, FadeSlide, GlitchText, NumberCounter } from '../components';

const features = [
  {
    icon: '🔐',
    name: 'PDA Vaults',
    stat: '0',
    statLabel: 'Private Keys Needed',
    desc: 'Deterministic agent wallets on Solana. No seed phrases, no risk.',
    color: theme.colors.purple,
    tags: ['Solana PDA', 'Deterministic', 'Non-custodial'],
  },
  {
    icon: '💰',
    name: 'Stablecoin Payments',
    stat: '6',
    statLabel: 'Token Types',
    desc: 'Native USDC, USDT, SOL transfers. Swap via Jupiter in one call.',
    color: theme.colors.green,
    tags: ['USDC', 'USDT', 'SOL', 'Jupiter'],
  },
  {
    icon: '🤝',
    name: 'Trustless Escrow',
    stat: '100',
    statLabel: '% Trustless',
    suffix: '%',
    desc: 'Smart contract escrow for agent-to-agent commerce. No middlemen.',
    color: theme.colors.cyan,
    tags: ['Escrow', 'A2A', 'Smart Contract'],
  },
  {
    icon: '⚡',
    name: 'x402 Micropayments',
    stat: '402',
    statLabel: 'HTTP Status',
    desc: 'Pay-per-request API access. HTTP-native micropayments for agents.',
    color: theme.colors.orange,
    tags: ['HTTP 402', 'Micropayments', 'API'],
  },
  {
    icon: '📊',
    name: 'Policy Engine',
    stat: '5',
    statLabel: 'Policy Types',
    desc: 'Spending limits, allowlists, time locks. Full control over agent spend.',
    color: theme.colors.pink,
    tags: ['Limits', 'Allowlists', 'Time Locks'],
  },
  {
    icon: '🏪',
    name: 'A2A Marketplace',
    stat: '999',
    statSuffix: '+',
    statLabel: 'Agent Jobs',
    desc: 'Discover agents, post jobs, match capabilities. Agent-to-agent economy.',
    color: theme.colors.cyan,
    tags: ['Discovery', 'Jobs', 'Reputation'],
  },
];

// ─── Glitch Wipe Transition ───
const GlitchWipe = ({ progress }) => {
  if (progress <= 0 || progress >= 1) return null;

  const sliceCount = 12;
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 50, pointerEvents: 'none' }}>
      {Array.from({ length: sliceCount }, (_, i) => {
        const sliceH = 100 / sliceCount;
        const offset = noise2D('gw' + i, progress * 5, i) * 40;
        const rgbSplit = noise2D('gs' + i, progress * 3, i) * 10;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${offset}%`,
              top: `${i * sliceH}%`,
              width: '120%',
              height: `${sliceH}%`,
              background: `rgba(${i % 2 ? '255,0,80' : '0,100,255'}, ${0.15 * progress})`,
              mixBlendMode: 'screen',
              opacity: progress * (1 - progress) * 4,
            }}
          />
        );
      })}
    </div>
  );
};

const FeatureCard = ({ feature, index }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  const rgb = hexToRgb(feature.color);

  // SLAM entrance — fast spring, overshoot
  const slamScale = spring({
    frame,
    fps,
    delay: 3,
    config: theme.springs.slam,
  });

  // Slide in from right
  const slideX = interpolate(frame, [0, 8], [isVertical ? 200 : 400, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const slideEased = easing.easeOutExpo(interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  }));

  // Exit: glitch transition at end
  const totalFrames = Math.round(fps * 2.5);
  const glitchExit = interpolate(frame, [totalFrames - 8, totalFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Icon zoom
  const iconScale = spring({
    frame,
    fps,
    delay: 2,
    config: theme.springs.bouncy,
  });

  // Speed ramp — stat counter has a fast-slow-fast feel
  const statProgress = interpolate(frame, [8, 50], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const numVal = parseInt(feature.stat, 10);
  const displayStat = !isNaN(numVal) && numVal > 0
    ? Math.round(numVal * easing.easeOutExpo(statProgress))
    : feature.stat;

  // Description wipe
  const descWipe = interpolate(frame, [20, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <Background
      variant="default"
      showLightRays={index % 2 === 0}
      lightRayCorner={index % 2 === 0 ? 'topRight' : 'topLeft'}
      particleCount={20}
      orbs={[
        { color: feature.color, size: 600, top: '-15%', left: '45%', delay: 0 },
      ]}
    >
      <AbsoluteFill
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: isVertical ? '60px 40px' : '60px 80px',
          transform: `translateX(${(1 - slideEased) * (isVertical ? 200 : 400)}px)`,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: isVertical ? 'column' : 'row',
            gap: isVertical ? 40 : 60,
            alignItems: 'center',
            width: '100%',
            maxWidth: 1200,
            transform: `scale(${slamScale})`,
          }}
        >
          {/* Left: Icon + Stat */}
          <div style={{ textAlign: 'center', minWidth: isVertical ? 'auto' : 220 }}>
            {/* Icon with zoom */}
            <div
              style={{
                fontSize: isVertical ? 64 : 56,
                transform: `scale(${iconScale})`,
                marginBottom: 16,
                filter: `drop-shadow(0 0 20px rgba(${rgb}, 0.4))`,
              }}
            >
              {feature.icon}
            </div>

            {/* Stat number */}
            <div style={{ position: 'relative' }}>
              <div
                style={{
                  fontSize: isVertical ? 90 : 80,
                  fontWeight: 900,
                  color: feature.color,
                  fontFamily: fontFamily.heading,
                  lineHeight: 1,
                  textShadow: `0 0 40px rgba(${rgb}, 0.5)`,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {displayStat}
                {feature.suffix || feature.statSuffix || ''}
              </div>
              <div
                style={{
                  fontSize: 12,
                  color: theme.colors.dim,
                  letterSpacing: 2.5,
                  textTransform: 'uppercase',
                  marginTop: 8,
                  fontFamily: fontFamily.mono,
                }}
              >
                {feature.statLabel}
              </div>
            </div>
          </div>

          {/* Right: Info */}
          <div style={{ flex: 1, maxWidth: isVertical ? '100%' : 500 }}>
            {/* Feature counter */}
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: feature.color,
                letterSpacing: 3,
                textTransform: 'uppercase',
                marginBottom: 10,
                fontFamily: fontFamily.mono,
              }}
            >
              FEATURE {index + 1}/{features.length}
            </div>

            {/* Name with glitch */}
            <GlitchText
              text={feature.name}
              startFrame={5}
              color={theme.colors.offWhite}
              fontSize={isVertical ? 36 : 34}
              fontWeight={800}
              duration={15}
            />

            {/* Description with wipe reveal */}
            <div
              style={{
                fontSize: isVertical ? 18 : 17,
                color: theme.colors.gray,
                lineHeight: 1.6,
                marginTop: 14,
                marginBottom: 20,
                fontFamily: fontFamily.heading,
                opacity: easing.easeOutCubic(descWipe),
                transform: `translateY(${(1 - descWipe) * 15}px)`,
              }}
            >
              {feature.desc}
            </div>

            {/* Tags */}
            <div
              style={{
                display: 'flex',
                gap: 10,
                flexWrap: 'wrap',
                opacity: easing.easeOutCubic(
                  interpolate(frame, [35, 50], [0, 1], {
                    extrapolateLeft: 'clamp',
                    extrapolateRight: 'clamp',
                  })
                ),
              }}
            >
              {feature.tags.map((tag, ti) => (
                <span
                  key={tag}
                  style={{
                    fontSize: 11,
                    color: theme.colors.dim,
                    ...theme.glass.subtle,
                    padding: '5px 14px',
                    borderRadius: 6,
                    fontFamily: fontFamily.mono,
                    transform: `translateY(${interpolate(
                      frame,
                      [35 + ti * 3, 45 + ti * 3],
                      [10, 0],
                      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
                    )}px)`,
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div
          style={{
            position: 'absolute',
            bottom: isVertical ? 60 : 40,
            left: isVertical ? 40 : 80,
            right: isVertical ? 40 : 80,
            display: 'flex',
            gap: 8,
          }}
        >
          {features.map((_, i) => {
            const isActive = i === index;
            return (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: 3,
                  borderRadius: 2,
                  background: isActive
                    ? `linear-gradient(90deg, ${feature.color}, ${feature.color}80)`
                    : 'rgba(255,255,255,0.05)',
                  boxShadow: isActive ? `0 0 6px rgba(${rgb}, 0.3)` : 'none',
                }}
              />
            );
          })}
        </div>
      </AbsoluteFill>

      {/* Glitch wipe transition */}
      <GlitchWipe progress={glitchExit} />
    </Background>
  );
};

// ─── CTA Closing Card ───
const CTACard = () => {
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
      lightRayCorner="center"
      particleCount={30}
      orbs={[
        { color: theme.colors.purple, size: 600, top: '-15%', left: '40%', delay: 0 },
        { color: theme.colors.green, size: 400, top: '60%', left: '55%', delay: 5 },
      ]}
    >
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 60,
        }}
      >
        <FadeSlide startFrame={0} duration={12} scale={0.95}>
          <div
            style={{
              fontSize: isVertical ? 52 : 48,
              fontWeight: 900,
              color: theme.colors.white,
              textAlign: 'center',
              fontFamily: fontFamily.heading,
              letterSpacing: -2,
              transform: `scale(${titleScale})`,
              textShadow: theme.glow.textPurple,
            }}
          >
            agent<span style={{ color: theme.colors.purple }}>wallet</span>.fun
          </div>
        </FadeSlide>

        <FadeSlide startFrame={15} duration={12}>
          <div
            style={{
              fontSize: 15,
              color: theme.colors.gray,
              marginTop: 20,
              fontFamily: fontFamily.mono,
              ...theme.glass.subtle,
              padding: '8px 24px',
            }}
          >
            pip install agentwallet-mcp
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};

export const FeatureHighlight = ({ voiceoverSrc }) => {
  const { fps } = useVideoConfig();
  const FRAMES_PER_FEATURE = Math.round(fps * 2);
  const CTA_DURATION = Math.round(fps * 3);

  return (
    <AbsoluteFill>
      {voiceoverSrc && <Audio src={voiceoverSrc} volume={1} />}

      {features.map((feature, i) => (
        <Sequence
          key={i}
          from={i * FRAMES_PER_FEATURE}
          durationInFrames={FRAMES_PER_FEATURE}
        >
          <FeatureCard feature={feature} index={i} />
        </Sequence>
      ))}

      {/* CTA at end */}
      <Sequence
        from={features.length * FRAMES_PER_FEATURE}
        durationInFrames={CTA_DURATION}
      >
        <CTACard />
      </Sequence>
    </AbsoluteFill>
  );
};
