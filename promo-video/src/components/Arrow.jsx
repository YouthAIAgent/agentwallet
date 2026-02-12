import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { theme, hexToRgb } from '../theme';

export const Arrow = ({
  startFrame = 0,
  color = theme.colors.purple,
  direction = 'right',
  length = 50,
  animated = true,
  showParticles = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [startFrame, startFrame + 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const lineProgress = animated
    ? spring({
        frame,
        fps,
        delay: startFrame,
        config: { damping: 16, mass: 1, stiffness: 140 },
      })
    : opacity;

  const rgb = hexToRgb(color);
  const isVertical = direction === 'down' || direction === 'up';

  // Flowing dash offset animation
  const dashOffset = (frame - startFrame) * 1.5;

  // Particle positions along the line
  const particlePos = ((frame - startFrame) * 3) % (length + 20);

  if (isVertical) {
    const actualLength = length * lineProgress;
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '4px 0',
          opacity,
          position: 'relative',
        }}
      >
        {/* Glow line */}
        <div
          style={{
            position: 'relative',
            width: 2,
            height: actualLength,
            overflow: 'visible',
          }}
        >
          {/* Base glow */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: `rgba(${rgb}, 0.15)`,
              filter: 'blur(4px)',
            }}
          />
          {/* Dashed line */}
          <svg
            width="2"
            height={actualLength}
            style={{ position: 'absolute', inset: 0 }}
          >
            <line
              x1="1" y1="0" x2="1" y2={actualLength}
              stroke={color}
              strokeWidth="1.5"
              strokeDasharray="6 4"
              strokeDashoffset={direction === 'down' ? -dashOffset : dashOffset}
              opacity="0.6"
            />
          </svg>
          {/* Flowing particle */}
          {showParticles && opacity > 0.5 && (
            <div
              style={{
                position: 'absolute',
                left: -2,
                top: direction === 'down' ? particlePos % actualLength : actualLength - (particlePos % actualLength),
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: color,
                boxShadow: `0 0 8px ${color}, 0 0 16px rgba(${rgb}, 0.5)`,
                opacity: 0.9,
              }}
            />
          )}
        </div>
        {/* Arrow head with glow */}
        <div style={{ position: 'relative' }}>
          <div
            style={{
              width: 0,
              height: 0,
              borderLeft: '6px solid transparent',
              borderRight: '6px solid transparent',
              borderTop: direction === 'down' ? `10px solid ${color}` : 'none',
              borderBottom: direction === 'up' ? `10px solid ${color}` : 'none',
              filter: `drop-shadow(0 0 4px rgba(${rgb}, 0.5))`,
              opacity: 0.8,
            }}
          />
        </div>
      </div>
    );
  }

  // Horizontal
  const actualLength = length * lineProgress;
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0 4px',
        opacity,
        position: 'relative',
      }}
    >
      <div
        style={{
          position: 'relative',
          width: actualLength,
          height: 2,
          overflow: 'visible',
        }}
      >
        {/* Base glow */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `rgba(${rgb}, 0.15)`,
            filter: 'blur(4px)',
          }}
        />
        {/* Dashed line */}
        <svg
          width={actualLength}
          height="2"
          style={{ position: 'absolute', inset: 0 }}
        >
          <line
            x1="0" y1="1" x2={actualLength} y2="1"
            stroke={color}
            strokeWidth="1.5"
            strokeDasharray="6 4"
            strokeDashoffset={-dashOffset}
            opacity="0.6"
          />
        </svg>
        {/* Flowing particle */}
        {showParticles && opacity > 0.5 && (
          <div
            style={{
              position: 'absolute',
              top: -2,
              left: particlePos % actualLength,
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: color,
              boxShadow: `0 0 8px ${color}, 0 0 16px rgba(${rgb}, 0.5)`,
              opacity: 0.9,
            }}
          />
        )}
      </div>
      {/* Arrow head with glow */}
      <div
        style={{
          width: 0,
          height: 0,
          borderTop: '6px solid transparent',
          borderBottom: '6px solid transparent',
          borderLeft: `10px solid ${color}`,
          filter: `drop-shadow(0 0 4px rgba(${rgb}, 0.5))`,
          opacity: 0.8,
        }}
      />
    </div>
  );
};
