import React from 'react';
import { useCurrentFrame, useVideoConfig, spring } from 'remotion';
import { fontFamily } from '../fonts';
import { theme } from '../theme';

export const Badge = ({
  text,
  color = theme.colors.purple,
  startFrame = 0,
  variant = 'outline',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    delay: startFrame,
    config: { damping: 12, mass: 0.6, stiffness: 200 },
  });

  const rgbColor = hexToRgb(color);

  const styles = {
    outline: {
      background: `rgba(${rgbColor}, 0.08)`,
      border: `1px solid rgba(${rgbColor}, 0.2)`,
      color,
    },
    solid: {
      background: `rgba(${rgbColor}, 0.2)`,
      border: `1px solid rgba(${rgbColor}, 0.3)`,
      color,
    },
    subtle: {
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.06)',
      color: theme.colors.dim,
    },
  };

  const s = styles[variant] || styles.outline;

  return (
    <span
      style={{
        display: 'inline-block',
        transform: `scale(${scale})`,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: 1.5,
        textTransform: 'uppercase',
        padding: '5px 14px',
        borderRadius: 6,
        fontFamily: fontFamily.mono,
        ...s,
      }}
    >
      {text}
    </span>
  );
};

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r},${g},${b}`;
}
