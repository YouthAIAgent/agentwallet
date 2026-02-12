import React from 'react';
import { useCurrentFrame, interpolate, useVideoConfig, spring } from 'remotion';
import { noise2D } from '@remotion/noise';
import { fontFamily } from '../fonts';
import { theme, hexToRgb } from '../theme';

export const GlitchText = ({
  text,
  startFrame = 0,
  color = theme.colors.white,
  fontSize = 48,
  fontWeight = 900,
  glitchIntensity = 1.0,
  duration = 20,
  settled = true, // if true, text stabilizes after duration
  mono = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const elapsed = frame - startFrame;
  if (elapsed < 0) return null;

  const rgb = hexToRgb(color);

  // Phase 1: Glitch in (0 to duration)
  const glitchProgress = interpolate(elapsed, [0, duration], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // After settling, occasional micro-glitches
  const isSettled = settled && elapsed > duration;
  const microGlitch = isSettled
    ? (noise2D('mg', elapsed * 0.05, 0) > 0.7 ? 0.15 : 0)
    : 0;

  const intensity = (glitchProgress + microGlitch) * glitchIntensity;

  // RGB split offsets
  const offsetX = noise2D('gx', elapsed * 0.3, 0) * 8 * intensity;
  const offsetY = noise2D('gy', elapsed * 0.3, 1) * 4 * intensity;

  // Character visibility (reveal effect)
  const revealProgress = interpolate(elapsed, [0, duration * 0.7], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Opacity
  const opacity = interpolate(elapsed, [0, 5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Random character scramble
  const scrambleChars = '!@#$%^&*()_+{}|:<>?ABCDEF0123456789';
  const displayText = text.split('').map((char, i) => {
    const charProgress = interpolate(
      elapsed,
      [i * 0.8, i * 0.8 + duration * 0.6],
      [0, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );
    if (charProgress >= 1 || char === ' ') return char;
    if (charProgress < 0.3) return scrambleChars[Math.floor(noise2D('sc' + i, elapsed * 0.5, i) * 18 + 18) % scrambleChars.length];
    return char;
  }).join('');

  // Scan line positions
  const scanY1 = (elapsed * 7) % 100;
  const scanY2 = (elapsed * 11 + 50) % 100;

  const baseStyle = {
    fontSize,
    fontWeight,
    fontFamily: mono ? fontFamily.mono : fontFamily.heading,
    letterSpacing: mono ? 0 : '-0.02em',
    position: 'relative',
    display: 'inline-block',
  };

  return (
    <div style={{ opacity, position: 'relative', display: 'inline-block' }}>
      {/* Red channel (offset left) */}
      {intensity > 0.01 && (
        <span
          style={{
            ...baseStyle,
            color: 'rgba(255, 0, 50, 0.6)',
            position: 'absolute',
            left: -offsetX * 1.2,
            top: offsetY * 0.5,
            opacity: intensity * 0.7,
            mixBlendMode: 'screen',
          }}
        >
          {displayText}
        </span>
      )}

      {/* Blue channel (offset right) */}
      {intensity > 0.01 && (
        <span
          style={{
            ...baseStyle,
            color: 'rgba(0, 100, 255, 0.6)',
            position: 'absolute',
            left: offsetX,
            top: -offsetY * 0.3,
            opacity: intensity * 0.7,
            mixBlendMode: 'screen',
          }}
        >
          {displayText}
        </span>
      )}

      {/* Main text */}
      <span
        style={{
          ...baseStyle,
          color,
          textShadow: intensity > 0.05
            ? `0 0 10px rgba(${rgb}, ${0.5 * intensity})`
            : `0 0 20px rgba(${rgb}, 0.2)`,
          position: 'relative',
        }}
      >
        {displayText}
      </span>

      {/* Scan lines overlay */}
      {intensity > 0.1 && (
        <div
          style={{
            position: 'absolute',
            inset: -4,
            overflow: 'hidden',
            pointerEvents: 'none',
            mixBlendMode: 'overlay',
          }}
        >
          <div
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: `${scanY1}%`,
              height: 2,
              background: `rgba(255, 255, 255, ${0.15 * intensity})`,
            }}
          />
          <div
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: `${scanY2}%`,
              height: 1,
              background: `rgba(255, 255, 255, ${0.1 * intensity})`,
            }}
          />
        </div>
      )}
    </div>
  );
};
