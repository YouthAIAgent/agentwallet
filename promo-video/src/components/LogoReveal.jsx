import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { noise2D } from '@remotion/noise';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';

export const LogoReveal = ({
  startFrame = 0,
  text = 'AgentWallet',
  highlightText = 'Wallet',
  tagline = 'Your Agent Deserves a Wallet',
  showTagline = true,
  fontSize = 72,
  color = theme.colors.white,
  accentColor = theme.colors.purple,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const elapsed = frame - startFrame;

  const rgb = hexToRgb(accentColor);
  const rgbWhite = hexToRgb(color);

  // Phase 1: Particle convergence (0-30 frames)
  const convergeProgress = interpolate(elapsed, [0, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const converge = easing.easeOutQuart(convergeProgress);

  // Phase 2: Text reveal (20-40 frames)
  const textRevealRaw = interpolate(elapsed, [20, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const textReveal = easing.easeOutCubic(textRevealRaw);

  // Phase 3: Glow bloom (30-50 frames)
  const glowRaw = interpolate(elapsed, [30, 45, 60, 80], [0, 1, 1, 0.6], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Scale spring
  const textScale = spring({
    frame,
    fps,
    delay: startFrame + 22,
    config: { damping: 12, mass: 1, stiffness: 120 },
  });

  // Particles that converge to center
  const particles = useMemo(() => {
    return Array.from({ length: 50 }, (_, i) => {
      const startAngle = noise2D('la' + i, i * 0.5, 0) * Math.PI * 2;
      const startDist = 200 + noise2D('ld' + i, i * 0.3, 1) * 200;
      const size = 2 + noise2D('ls' + i, i * 0.4, 2) * 3;
      const isAccent = i % 3 === 0;
      return { startAngle, startDist, size, isAccent, id: i };
    });
  }, []);

  // Tagline spring
  const taglineOpacity = interpolate(elapsed, [50, 65], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const taglineY = interpolate(elapsed, [50, 65], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Breathing glow after reveal
  const breathe = elapsed > 60 ? 0.8 + Math.sin(elapsed * 0.04) * 0.2 : 1;

  if (elapsed < 0) return null;

  // Split text for highlight
  const highlightIdx = text.indexOf(highlightText);
  const beforeHighlight = highlightIdx >= 0 ? text.slice(0, highlightIdx) : text;
  const highlighted = highlightIdx >= 0 ? highlightText : '';
  const afterHighlight = highlightIdx >= 0 ? text.slice(highlightIdx + highlightText.length) : '';

  return (
    <div
      style={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Converging particles */}
      {converge < 0.95 && particles.map((p) => {
        const dist = p.startDist * (1 - converge);
        const px = Math.cos(p.startAngle) * dist;
        const py = Math.sin(p.startAngle) * dist;
        const pOpacity = interpolate(converge, [0, 0.3, 0.8, 1], [0, 0.8, 0.6, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const pColor = p.isAccent ? accentColor : theme.colors.cyan;
        const pRgb = p.isAccent ? rgb : hexToRgb(theme.colors.cyan);
        return (
          <div
            key={p.id}
            style={{
              position: 'absolute',
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              background: pColor,
              boxShadow: `0 0 ${p.size * 3}px rgba(${pRgb}, 0.6)`,
              transform: `translate(${px}px, ${py}px)`,
              opacity: pOpacity,
              pointerEvents: 'none',
            }}
          />
        );
      })}

      {/* Central glow bloom */}
      {glowRaw > 0 && (
        <div
          style={{
            position: 'absolute',
            width: 400 * glowRaw,
            height: 200 * glowRaw,
            borderRadius: '50%',
            background: `radial-gradient(circle, rgba(${rgb}, ${0.3 * glowRaw * breathe}) 0%, rgba(${rgb}, ${0.1 * glowRaw}) 40%, transparent 70%)`,
            filter: 'blur(30px)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Main text */}
      <div
        style={{
          transform: `scale(${textScale})`,
          opacity: textReveal,
          textAlign: 'center',
          position: 'relative',
        }}
      >
        <div
          style={{
            fontSize,
            fontWeight: 900,
            fontFamily: fontFamily.heading,
            letterSpacing: -3,
            lineHeight: 1.05,
            textShadow: `0 0 40px rgba(${rgb}, ${0.4 * breathe})`,
          }}
        >
          <span style={{ color }}>{beforeHighlight}</span>
          <span style={{ color: accentColor }}>{highlighted}</span>
          <span style={{ color }}>{afterHighlight}</span>
        </div>
      </div>

      {/* Tagline */}
      {showTagline && taglineOpacity > 0 && (
        <div
          style={{
            marginTop: 20,
            fontSize: fontSize * 0.25,
            color: theme.colors.gray,
            fontFamily: fontFamily.heading,
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
            letterSpacing: 1,
          }}
        >
          {tagline}
        </div>
      )}
    </div>
  );
};
