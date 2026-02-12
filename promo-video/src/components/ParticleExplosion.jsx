import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { noise2D } from '@remotion/noise';
import { theme, hexToRgb, easing } from '../theme';

export const ParticleExplosion = ({
  startFrame = 0,
  x = '50%',
  y = '50%',
  count = 60,
  color = theme.colors.purple,
  secondaryColor = theme.colors.green,
  duration = 40,
  spread = 300,
  fadeIn = true,
}) => {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;

  const rgb1 = hexToRgb(color);
  const rgb2 = hexToRgb(secondaryColor);

  const particles = useMemo(() => {
    return Array.from({ length: count }, (_, i) => {
      const angle = (noise2D('pa' + i, i * 0.5, 0) + 1) * Math.PI;
      const speed = 0.5 + noise2D('ps' + i, i * 0.3, 1) * 0.5;
      const size = 2 + noise2D('pz' + i, i * 0.4, 2) * 3;
      const useSecondary = i % 3 === 0;
      const rotationSpeed = (noise2D('pr' + i, i, 0) - 0.5) * 2;
      return { angle, speed, size, useSecondary, rotationSpeed, id: i };
    });
  }, [count]);

  if (elapsed < 0 || elapsed > duration + 20) return null;

  // Overall explosion progress
  const rawProgress = interpolate(elapsed, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const progress = easing.easeOutQuart(rawProgress);

  // Flash at start
  const flash = interpolate(elapsed, [0, 4, 10], [0, 0.6, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: 0,
        height: 0,
        pointerEvents: 'none',
      }}
    >
      {/* Central flash */}
      {flash > 0 && (
        <div
          style={{
            position: 'absolute',
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: `radial-gradient(circle, rgba(255,255,255,${flash}) 0%, rgba(${rgb1}, ${flash * 0.5}) 40%, transparent 70%)`,
            transform: 'translate(-50%, -50%)',
            filter: 'blur(10px)',
          }}
        />
      )}

      {/* Particles */}
      {particles.map((p) => {
        const distance = p.speed * spread * progress;
        const px = Math.cos(p.angle) * distance;
        const py = Math.sin(p.angle) * distance;
        const particleOpacity = interpolate(
          elapsed,
          [0, 3, duration * 0.6, duration],
          [0, 1, 0.8, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        const particleScale = interpolate(
          elapsed,
          [0, 5, duration * 0.7, duration],
          [0, 1.2, 0.8, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        const rgb = p.useSecondary ? rgb2 : rgb1;
        const particleColor = p.useSecondary ? secondaryColor : color;

        return (
          <div
            key={p.id}
            style={{
              position: 'absolute',
              width: p.size * particleScale,
              height: p.size * particleScale,
              borderRadius: '50%',
              background: particleColor,
              boxShadow: `0 0 ${p.size * 3}px rgba(${rgb}, 0.6)`,
              transform: `translate(${px}px, ${py}px) translate(-50%, -50%)`,
              opacity: particleOpacity,
            }}
          />
        );
      })}
    </div>
  );
};
