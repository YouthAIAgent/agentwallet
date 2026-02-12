import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';

export const StatCounter = ({
  value,
  label,
  suffix = '',
  prefix = '',
  color = theme.colors.purple,
  startFrame = 0,
  isNumeric = true,
  size = 'default', // 'default' | 'large' | 'hero'
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    delay: startFrame,
    config: theme.springs.pop,
  });

  const rawProgress = interpolate(
    frame,
    [startFrame, startFrame + 30],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
  const countProgress = easing.easeOutExpo(rawProgress);

  const numVal = parseInt(value, 10);
  const displayValue = isNumeric && !isNaN(numVal)
    ? Math.round(numVal * countProgress)
    : value;

  const rgb = hexToRgb(color);
  const pulse = 0.85 + Math.sin(frame * 0.04 + startFrame) * 0.15;

  const sizes = {
    default: { num: 48, label: 11, pad: '20px 32px', min: 150, radius: 14 },
    large: { num: 64, label: 13, pad: '28px 40px', min: 180, radius: 16 },
    hero: { num: 96, label: 15, pad: '36px 48px', min: 220, radius: 20 },
  };
  const s = sizes[size] || sizes.default;

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        position: 'relative',
      }}
    >
      {/* Outer glow */}
      <div
        style={{
          position: 'absolute',
          inset: -6,
          borderRadius: s.radius + 6,
          background: `radial-gradient(ellipse, rgba(${rgb}, ${0.08 * pulse}) 0%, transparent 70%)`,
          filter: 'blur(12px)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'relative',
          background: `linear-gradient(135deg, rgba(${rgb}, 0.06) 0%, rgba(${rgb}, 0.02) 100%)`,
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: `1px solid rgba(${rgb}, 0.18)`,
          borderRadius: s.radius,
          padding: s.pad,
          textAlign: 'center',
          minWidth: s.min,
          overflow: 'hidden',
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

        <div
          style={{
            fontSize: s.num,
            fontWeight: 800,
            color,
            fontFamily: fontFamily.heading,
            textShadow: `0 0 30px rgba(${rgb}, 0.4)`,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {prefix}{displayValue}{suffix}
        </div>
        <div
          style={{
            fontSize: s.label,
            color: theme.colors.dim,
            marginTop: 8,
            letterSpacing: 2.5,
            textTransform: 'uppercase',
            fontFamily: fontFamily.mono,
          }}
        >
          {label}
        </div>
      </div>
    </div>
  );
};
