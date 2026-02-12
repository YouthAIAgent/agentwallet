import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { fontFamily } from '../fonts';
import { theme } from '../theme';

export const TechTag = ({
  text,
  startFrame = 0,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const effectiveStart = startFrame + delay;

  const opacity = interpolate(
    frame,
    [effectiveStart, effectiveStart + 12],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const y = interpolate(
    frame,
    [effectiveStart, effectiveStart + 12],
    [8, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <span
      style={{
        display: 'inline-block',
        fontSize: 11,
        color: theme.colors.dim,
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
        padding: '4px 14px',
        borderRadius: 4,
        fontFamily: fontFamily.mono,
        opacity,
        transform: `translateY(${y}px)`,
      }}
    >
      {text}
    </span>
  );
};
