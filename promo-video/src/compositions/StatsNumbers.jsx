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
import { Background, FadeSlide, NumberCounter, GlitchText, ParticleExplosion } from '../components';

// ─── Stats Data ───
const stats = [
  {
    value: '27',
    label: 'MCP TOOLS',
    desc: 'Complete toolkit for autonomous agent operations',
    color: theme.colors.purple,
    secondaryColor: theme.colors.cyan,
  },
  {
    value: '0',
    label: 'PRIVATE KEYS',
    desc: 'PDA-based wallets eliminate key management entirely',
    color: theme.colors.green,
    secondaryColor: theme.colors.purple,
  },
  {
    value: '100',
    suffix: '%',
    label: 'ON-CHAIN',
    desc: 'Every transaction verifiable on Solana',
    color: theme.colors.cyan,
    secondaryColor: theme.colors.green,
  },
];

// ─── Screen Flash Transition ───
const ScreenFlash = ({ startFrame }) => {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;
  const flashOpacity = interpolate(elapsed, [0, 2, 5, 12], [0, 0.9, 0.5, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  if (flashOpacity <= 0) return null;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: `radial-gradient(circle, rgba(255,255,255,${flashOpacity}) 0%, rgba(255,255,255,${flashOpacity * 0.3}) 60%, transparent 100%)`,
        pointerEvents: 'none',
        zIndex: 100,
      }}
    />
  );
};

// ─── Camera Shake ───
const CameraShake = ({ children, startFrame, intensity = 8, duration = 15 }) => {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;

  if (elapsed < 0 || elapsed > duration) {
    return <div style={{ width: '100%', height: '100%' }}>{children}</div>;
  }

  const decay = 1 - elapsed / duration;
  const shakeX = noise2D('sx', elapsed * 0.8, 0) * intensity * decay;
  const shakeY = noise2D('sy', elapsed * 0.8, 1) * intensity * decay;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        transform: `translate(${shakeX}px, ${shakeY}px)`,
      }}
    >
      {children}
    </div>
  );
};

// ─── Color Explosion Behind Stat ───
const ColorExplosion = ({ color, startFrame }) => {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;
  const rgb = hexToRgb(color);

  const size = interpolate(elapsed, [0, 30], [0, 1200], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const opacity = interpolate(elapsed, [0, 5, 20, 35], [0, 0.25, 0.15, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  if (opacity <= 0) return null;

  return (
    <div
      style={{
        position: 'absolute',
        width: size,
        height: size,
        borderRadius: '50%',
        background: `radial-gradient(circle, rgba(${rgb}, ${opacity}) 0%, rgba(${rgb}, ${opacity * 0.3}) 40%, transparent 70%)`,
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        filter: 'blur(30px)',
        pointerEvents: 'none',
      }}
    />
  );
};

// ─── Stat Slide ───
const StatSlide = ({ stat, index }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  const rgb = hexToRgb(stat.color);

  // Glow pulse
  const glowPulse = 0.7 + Math.sin(frame * 0.06) * 0.3;

  const numberSize = isVertical ? 180 : 140;
  const labelSize = isVertical ? 42 : 32;
  const descSize = isVertical ? 20 : 16;

  // Number reveal with dramatic timing
  const numberRevealDelay = 8;

  return (
    <Background
      variant="dark"
      showLightRays
      lightRayCorner="topRight"
      particleCount={25}
      orbs={[
        { color: stat.color, size: isVertical ? 800 : 700, top: '-20%', left: '35%', delay: 0 },
        { color: stat.secondaryColor, size: 400, top: '65%', left: '60%', delay: 5 },
      ]}
    >
      <CameraShake startFrame={numberRevealDelay} intensity={10} duration={12}>
        <AbsoluteFill
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: isVertical ? '60px 40px' : '40px 80px',
          }}
        >
          {/* Color explosion */}
          <ColorExplosion color={stat.color} startFrame={numberRevealDelay} />

          {/* Particle burst */}
          <ParticleExplosion
            startFrame={numberRevealDelay + 2}
            x="50%"
            y="45%"
            count={40}
            color={stat.color}
            secondaryColor={stat.secondaryColor}
            duration={35}
            spread={250}
          />

          {/* Badge */}
          <FadeSlide startFrame={0} duration={10} scale={0.9}>
            <div
              style={{
                fontSize: isVertical ? 14 : 12,
                fontWeight: 700,
                color: stat.color,
                letterSpacing: 3,
                textTransform: 'uppercase',
                marginBottom: isVertical ? 50 : 30,
                fontFamily: fontFamily.mono,
                ...theme.glass.subtle,
                padding: '8px 24px',
              }}
            >
              ◎ AgentWallet
            </div>
          </FadeSlide>

          {/* Big number — odometer style */}
          <div style={{ position: 'relative', marginBottom: isVertical ? 30 : 20 }}>
            {/* Glow behind */}
            <div
              style={{
                position: 'absolute',
                width: '300%',
                height: '300%',
                top: '-100%',
                left: '-100%',
                background: `radial-gradient(circle, rgba(${rgb}, ${0.15 * glowPulse}) 0%, transparent 50%)`,
                filter: 'blur(40px)',
                pointerEvents: 'none',
              }}
            />
            <NumberCounter
              value={stat.value}
              startFrame={numberRevealDelay}
              duration={35}
              color={stat.color}
              fontSize={numberSize}
              suffix={stat.suffix || ''}
            />
          </div>

          {/* Label — glitch text */}
          <GlitchText
            text={stat.label}
            startFrame={15}
            color={theme.colors.offWhite}
            fontSize={labelSize}
            fontWeight={800}
            duration={18}
          />

          {/* Description */}
          <FadeSlide startFrame={25} duration={12}>
            <div
              style={{
                fontSize: descSize,
                color: theme.colors.gray,
                marginTop: isVertical ? 20 : 14,
                textAlign: 'center',
                maxWidth: isVertical ? 400 : 500,
                lineHeight: 1.5,
                fontFamily: fontFamily.heading,
              }}
            >
              {stat.desc}
            </div>
          </FadeSlide>

          {/* Progress dots */}
          <div
            style={{
              position: 'absolute',
              bottom: isVertical ? 80 : 40,
              display: 'flex',
              gap: 14,
            }}
          >
            {stats.map((_, i) => (
              <div
                key={i}
                style={{
                  width: i === index ? 32 : 8,
                  height: 8,
                  borderRadius: 4,
                  background: i === index
                    ? `linear-gradient(90deg, ${stat.color}, ${stat.secondaryColor})`
                    : 'rgba(255,255,255,0.08)',
                  boxShadow: i === index ? `0 0 10px rgba(${rgb}, 0.4)` : 'none',
                }}
              />
            ))}
          </div>
        </AbsoluteFill>
      </CameraShake>

      {/* Screen flash between stats */}
      <ScreenFlash startFrame={0} />
    </Background>
  );
};

export const StatsNumbers = ({ voiceoverSrc }) => {
  const { fps } = useVideoConfig();
  const FRAMES_PER_STAT = Math.round(fps * 4); // 4 seconds per stat

  return (
    <AbsoluteFill>
      {voiceoverSrc && (
        <Audio src={voiceoverSrc} volume={1} />
      )}
      {stats.map((stat, i) => (
        <Sequence
          key={i}
          from={i * FRAMES_PER_STAT}
          durationInFrames={FRAMES_PER_STAT}
        >
          <StatSlide stat={stat} index={i} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
