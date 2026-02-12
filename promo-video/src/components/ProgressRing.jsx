import React from 'react';
import { useCurrentFrame, interpolate, useVideoConfig, spring } from 'remotion';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';

export const ProgressRing = ({
  progress = 100, // 0-100
  startFrame = 0,
  duration = 40,
  size = 160,
  strokeWidth = 6,
  color = theme.colors.purple,
  secondaryColor = theme.colors.green,
  showValue = true,
  valuePrefix = '',
  valueSuffix = '%',
  label = '',
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const elapsed = frame - startFrame;

  const rgb = hexToRgb(color);

  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;

  // Animation progress
  const rawProgress = interpolate(elapsed, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const animProgress = easing.easeOutExpo(rawProgress);
  const currentProgress = progress * animProgress;
  const dashOffset = circumference * (1 - currentProgress / 100);

  // Scale entrance
  const scale = spring({
    frame,
    fps,
    delay: startFrame,
    config: theme.springs.pop,
  });

  // Glow pulse
  const pulse = 0.7 + Math.sin(frame * 0.04) * 0.3;

  // Opacity
  const opacity = interpolate(elapsed, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Gradient ID unique per instance
  const gradId = `ring-grad-${startFrame}-${progress}`;

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        opacity,
        position: 'relative',
        width: size,
        height: size,
        ...style,
      }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor={secondaryColor} />
          </linearGradient>
          <filter id={`ringGlow-${startFrame}`}>
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth}
        />

        {/* Progress arc glow */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`rgba(${rgb}, ${0.2 * pulse})`}
          strokeWidth={strokeWidth + 8}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          filter={`url(#ringGlow-${startFrame})`}
        />

        {/* Progress arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#${gradId})`}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />

        {/* End dot */}
        {currentProgress > 2 && (
          <circle
            cx={size / 2 + radius * Math.cos((-90 + 360 * currentProgress / 100) * Math.PI / 180)}
            cy={size / 2 + radius * Math.sin((-90 + 360 * currentProgress / 100) * Math.PI / 180)}
            r={strokeWidth * 1.2}
            fill={secondaryColor}
            filter={`url(#ringGlow-${startFrame})`}
          />
        )}
      </svg>

      {/* Center value */}
      {showValue && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              fontSize: size * 0.22,
              fontWeight: 800,
              color: theme.colors.offWhite,
              fontFamily: fontFamily.heading,
              fontVariantNumeric: 'tabular-nums',
              textShadow: `0 0 20px rgba(${rgb}, 0.3)`,
            }}
          >
            {valuePrefix}{Math.round(currentProgress)}{valueSuffix}
          </div>
          {label && (
            <div
              style={{
                fontSize: size * 0.08,
                color: theme.colors.dim,
                fontFamily: fontFamily.mono,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                marginTop: 2,
              }}
            >
              {label}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
