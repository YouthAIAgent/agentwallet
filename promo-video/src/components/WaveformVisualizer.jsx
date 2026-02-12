import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { noise2D } from '@remotion/noise';
import { theme, hexToRgb } from '../theme';

export const WaveformVisualizer = ({
  startFrame = 0,
  barCount = 64,
  width = 600,
  height = 120,
  color = theme.colors.purple,
  secondaryColor = theme.colors.cyan,
  intensity = 1.0,
  style = {},
}) => {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;
  if (elapsed < 0) return null;

  const rgb = hexToRgb(color);
  const rgb2 = hexToRgb(secondaryColor);

  const barWidth = (width / barCount) * 0.7;
  const barGap = (width / barCount) * 0.3;

  // Fade in
  const opacity = interpolate(elapsed, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: barGap,
        opacity,
        ...style,
      }}
    >
      {Array.from({ length: barCount }, (_, i) => {
        // Multiple noise layers for complex waveform
        const n1 = noise2D('wv1', i * 0.15, elapsed * 0.05) * 0.5 + 0.5;
        const n2 = noise2D('wv2', i * 0.08, elapsed * 0.03) * 0.3 + 0.5;
        const n3 = noise2D('wv3', i * 0.2, elapsed * 0.08) * 0.2;
        const barHeight = (n1 * n2 + n3) * height * 0.8 * intensity + height * 0.05;

        // Color gradient across bars
        const colorProgress = i / barCount;
        const r1 = parseInt(color.slice(1, 3), 16);
        const g1 = parseInt(color.slice(3, 5), 16);
        const b1 = parseInt(color.slice(5, 7), 16);
        const r2 = parseInt(secondaryColor.slice(1, 3), 16);
        const g2 = parseInt(secondaryColor.slice(3, 5), 16);
        const b2 = parseInt(secondaryColor.slice(5, 7), 16);
        const r = Math.round(r1 + (r2 - r1) * colorProgress);
        const g = Math.round(g1 + (g2 - g1) * colorProgress);
        const b = Math.round(b1 + (b2 - b1) * colorProgress);
        const barColor = `rgb(${r}, ${g}, ${b})`;

        return (
          <div
            key={i}
            style={{
              width: barWidth,
              height: barHeight,
              borderRadius: barWidth / 2,
              background: `linear-gradient(to top, ${barColor}, ${barColor}AA)`,
              boxShadow: `0 0 ${barHeight * 0.2}px rgba(${r}, ${g}, ${b}, 0.3)`,
              transition: 'none',
            }}
          />
        );
      })}
    </div>
  );
};
