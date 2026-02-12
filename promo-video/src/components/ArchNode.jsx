import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { noise2D } from '@remotion/noise';
import { fontFamily } from '../fonts';
import { theme, hexToRgb } from '../theme';

export const ArchNode = ({
  label,
  name,
  desc,
  color = theme.colors.purple,
  startFrame = 0,
  size = 'default',
  glowing = true,
  icon,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    delay: startFrame,
    config: theme.springs.pop,
  });

  const opacity = interpolate(frame, [startFrame, startFrame + 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const rgb = hexToRgb(color);
  const isLarge = size === 'large';

  // Subtle pulse animation
  const pulse = glowing ? 0.85 + Math.sin(frame * 0.05 + startFrame) * 0.15 : 1;

  // Shimmer effect on the border
  const shimmerPos = ((frame - startFrame) * 2) % 360;

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        opacity,
        position: 'relative',
      }}
    >
      {/* Outer glow */}
      {glowing && (
        <div
          style={{
            position: 'absolute',
            inset: -8,
            borderRadius: isLarge ? 22 : 18,
            background: `radial-gradient(ellipse at 50% 50%, rgba(${rgb}, ${0.12 * pulse}) 0%, transparent 70%)`,
            filter: 'blur(12px)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Glass card */}
      <div
        style={{
          position: 'relative',
          background: `linear-gradient(135deg, rgba(${rgb}, 0.08) 0%, rgba(${rgb}, 0.03) 100%)`,
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: `1px solid rgba(${rgb}, ${0.2 + pulse * 0.1})`,
          borderRadius: isLarge ? 16 : 12,
          padding: isLarge ? '22px 36px' : '18px 28px',
          textAlign: 'center',
          minWidth: isLarge ? 170 : 140,
          overflow: 'hidden',
        }}
      >
        {/* Shimmer sweep */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `linear-gradient(${shimmerPos}deg, transparent 0%, rgba(255,255,255,0.03) 45%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0.03) 55%, transparent 100%)`,
            pointerEvents: 'none',
          }}
        />

        {/* Inner glow at top */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: '20%',
            right: '20%',
            height: 1,
            background: `linear-gradient(90deg, transparent, rgba(${rgb}, 0.4), transparent)`,
            pointerEvents: 'none',
          }}
        />

        {/* Icon */}
        {icon && (
          <div style={{ fontSize: isLarge ? 24 : 20, marginBottom: 6 }}>
            {icon}
          </div>
        )}

        {/* Label */}
        <div
          style={{
            fontSize: isLarge ? 11 : 10,
            fontWeight: 700,
            color,
            letterSpacing: 2.5,
            textTransform: 'uppercase',
            fontFamily: fontFamily.mono,
            opacity: 0.9,
          }}
        >
          {label}
        </div>

        {/* Name */}
        <div
          style={{
            fontSize: isLarge ? 22 : 18,
            fontWeight: 700,
            color: theme.colors.offWhite,
            marginTop: 6,
            fontFamily: fontFamily.heading,
            textShadow: `0 0 20px rgba(${rgb}, 0.3)`,
          }}
        >
          {name}
        </div>

        {/* Description */}
        {desc && (
          <div
            style={{
              fontSize: isLarge ? 12 : 11,
              color: theme.colors.dim,
              marginTop: 5,
              fontFamily: fontFamily.mono,
              lineHeight: 1.4,
            }}
          >
            {desc}
          </div>
        )}
      </div>
    </div>
  );
};
