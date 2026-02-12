import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from 'remotion';
import { noise2D } from '@remotion/noise';
import { fontFamily } from '../fonts';
import { theme } from '../theme';
import { Background, FadeSlide } from '../components';

export const TwitterCard = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    delay: 8,
    config: { damping: 12, mass: 1, stiffness: 120 },
  });

  const taglineOpacity = interpolate(frame, [20, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtle particle layer
  const particles = Array.from({ length: 12 }, (_, i) => {
    const x = noise2D('tx' + i, i * 0.4, 0) * 600 + 600;
    const y = noise2D('ty' + i, i * 0.4, 0) * 337 + 337;
    const drift = noise2D('td' + i, frame * 0.008, i) * 15;
    const op = interpolate(frame, [0, 20, 120, 150], [0, 0.3, 0.3, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return (
      <div
        key={i}
        style={{
          position: 'absolute',
          width: 2,
          height: 2,
          borderRadius: '50%',
          background: i % 2 === 0 ? theme.colors.purple : theme.colors.green,
          left: x + drift,
          top: y + drift * 0.5,
          opacity: op,
        }}
      />
    );
  });

  const stats = [
    { val: '27', label: 'MCP Tools' },
    { val: '◎', label: 'Solana' },
    { val: '∞', label: 'Agents' },
  ];

  return (
    <Background
      orbs={[
        { color: theme.colors.purple, size: 500, top: '-20%', left: '50%', delay: 0 },
        { color: theme.colors.green, size: 300, top: '60%', left: '0%', delay: 5 },
      ]}
    >
      {particles}
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 60,
        }}
      >
        {/* Protocol badge */}
        <FadeSlide startFrame={0} duration={10}>
          <div
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: theme.colors.purple,
              letterSpacing: 3,
              textTransform: 'uppercase',
              marginBottom: 16,
              fontFamily: fontFamily.mono,
              background: `rgba(153,69,255,0.08)`,
              border: `1px solid rgba(153,69,255,0.15)`,
              padding: '4px 16px',
              borderRadius: 4,
            }}
          >
            Agent Protocol
          </div>
        </FadeSlide>

        {/* Title */}
        <div
          style={{
            transform: `scale(${titleScale})`,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: 52,
              fontWeight: 900,
              color: theme.colors.white,
              letterSpacing: -2,
              lineHeight: 1.1,
              fontFamily: fontFamily.heading,
            }}
          >
            Agent<span style={{ color: theme.colors.purple }}>Wallet</span>
          </div>
        </div>

        {/* Tagline */}
        <div
          style={{
            opacity: taglineOpacity,
            fontSize: 16,
            color: theme.colors.gray,
            marginTop: 12,
            textAlign: 'center',
            fontFamily: fontFamily.heading,
          }}
        >
          Autonomous wallet infrastructure for AI agents
        </div>

        {/* Stats row */}
        <FadeSlide startFrame={35} duration={12}>
          <div
            style={{
              display: 'flex',
              gap: 32,
              marginTop: 28,
            }}
          >
            {stats.map((s, i) => (
              <div key={i} style={{ textAlign: 'center' }}>
                <div
                  style={{
                    fontSize: 24,
                    fontWeight: 800,
                    color: theme.colors.purple,
                    fontFamily: fontFamily.heading,
                  }}
                >
                  {s.val}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: theme.colors.dim,
                    letterSpacing: 1.5,
                    textTransform: 'uppercase',
                    fontFamily: fontFamily.mono,
                    marginTop: 2,
                  }}
                >
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </FadeSlide>

        {/* URL */}
        <FadeSlide startFrame={50} duration={12}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: theme.colors.green,
              marginTop: 20,
              fontFamily: fontFamily.mono,
              letterSpacing: 1,
            }}
          >
            agentwallet.fun
          </div>
        </FadeSlide>
      </AbsoluteFill>
    </Background>
  );
};
