import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { noise2D } from '@remotion/noise';
import { theme, hexToRgb } from '../theme';

// ─── Animated Mesh Gradient Background ───
const MeshGradient = ({ frame, variant }) => {
  // Subtle animated color positions that drift over time
  const t = frame * 0.003;
  const x1 = 20 + noise2D('mx1', t, 0) * 15;
  const y1 = 20 + noise2D('my1', t, 0.5) * 15;
  const x2 = 75 + noise2D('mx2', t, 1) * 15;
  const y2 = 30 + noise2D('my2', t, 1.5) * 15;
  const x3 = 40 + noise2D('mx3', t, 2) * 20;
  const y3 = 75 + noise2D('my3', t, 2.5) * 15;

  const colorSets = {
    default: [
      { color: 'rgba(153, 69, 255, 0.1)', x: x1, y: y1, size: 50 },
      { color: 'rgba(0, 212, 255, 0.07)', x: x2, y: y2, size: 45 },
      { color: 'rgba(20, 241, 149, 0.06)', x: x3, y: y3, size: 40 },
    ],
    dark: [
      { color: 'rgba(153, 69, 255, 0.06)', x: x1, y: y1, size: 55 },
      { color: 'rgba(0, 212, 255, 0.04)', x: x2, y: y2, size: 50 },
    ],
    terminal: [
      { color: 'rgba(20, 241, 149, 0.04)', x: 50, y: 50, size: 60 },
    ],
    energy: [
      { color: 'rgba(153, 69, 255, 0.14)', x: x1, y: y1, size: 50 },
      { color: 'rgba(20, 241, 149, 0.1)', x: x2, y: y2, size: 45 },
      { color: 'rgba(0, 212, 255, 0.08)', x: x3, y: y3, size: 40 },
      { color: 'rgba(255, 107, 53, 0.06)', x: 60 + noise2D('mx4', t, 3) * 10, y: 20, size: 35 },
    ],
  };

  const colors = colorSets[variant] || colorSets.default;
  const gradients = colors.map(
    (c) => `radial-gradient(ellipse ${c.size}% ${c.size}% at ${c.x}% ${c.y}%, ${c.color} 0%, transparent 100%)`
  );

  const baseBg = variant === 'terminal'
    ? '#030308'
    : variant === 'dark'
    ? '#050510'
    : '#0a0a1a';

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: `${gradients.join(', ')}, linear-gradient(180deg, ${baseBg} 0%, ${baseBg} 100%)`,
      }}
    />
  );
};

// ─── Floating Particles with Parallax Depth ───
const FloatingParticles = ({ frame, count = 40 }) => {
  const particles = useMemo(() => {
    return Array.from({ length: count }, (_, i) => {
      const depth = 0.3 + (i / count) * 0.7; // 0.3-1.0 depth factor
      const baseX = noise2D('fpx' + i, i * 0.7, 0) * 100;
      const baseY = noise2D('fpy' + i, i * 0.7, 1) * 100;
      const size = 1 + depth * 2.5;
      const colorIdx = i % 3;
      const colors = [theme.colors.purple, theme.colors.green, theme.colors.cyan];
      return { baseX, baseY, size, depth, color: colors[colorIdx], id: i };
    });
  }, [count]);

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {particles.map((p) => {
        const speed = p.depth * 0.008;
        const driftX = noise2D('pdx' + p.id, frame * speed, p.id) * 30 * p.depth;
        const driftY = noise2D('pdy' + p.id, frame * speed, p.id + 50) * 20 * p.depth;
        const twinkle = 0.15 + (noise2D('ptw' + p.id, frame * 0.02, p.id) + 1) * 0.15 * p.depth;

        return (
          <div
            key={p.id}
            style={{
              position: 'absolute',
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              background: p.color,
              left: `${p.baseX + driftX * 0.5}%`,
              top: `${p.baseY + driftY * 0.5}%`,
              opacity: twinkle,
              boxShadow: `0 0 ${p.size * 2}px ${p.color}40`,
            }}
          />
        );
      })}
    </div>
  );
};

// ─── Noise Texture Overlay (Film Grain) ───
const NoiseOverlay = ({ frame, opacity = 0.03 }) => {
  // Generate a pseudo-random seed per frame for grain
  const seed = (frame * 13.37) % 1000;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity,
        pointerEvents: 'none',
        mixBlendMode: 'overlay',
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' seed='${Math.floor(seed)}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E")`,
        backgroundSize: '256px 256px',
      }}
    />
  );
};

// ─── Cinematic Vignette ───
const Vignette = ({ intensity = 0.6 }) => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      pointerEvents: 'none',
      background: `radial-gradient(ellipse 70% 60% at 50% 50%, transparent 0%, rgba(0,0,0,${intensity}) 100%)`,
    }}
  />
);

// ─── Pulsing Grid Lines ───
const PulsingGrid = ({ frame, spacing = 60, color = 'rgba(255,255,255,0.025)' }) => {
  const pulse = 0.5 + Math.sin(frame * 0.03) * 0.3;
  const pulseColor = color.replace(/[\d.]+\)$/, `${parseFloat(color.match(/[\d.]+\)$/)[0]) * pulse})`);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        backgroundImage: `
          linear-gradient(${pulseColor} 1px, transparent 1px),
          linear-gradient(90deg, ${pulseColor} 1px, transparent 1px)
        `,
        backgroundSize: `${spacing}px ${spacing}px`,
        maskImage: 'radial-gradient(ellipse 80% 80% at 50% 50%, black 0%, transparent 100%)',
        WebkitMaskImage: 'radial-gradient(ellipse 80% 80% at 50% 50%, black 0%, transparent 100%)',
      }}
    />
  );
};

// ─── Volumetric Light Rays ───
const LightRays = ({ frame, fromCorner = 'topRight' }) => {
  const corners = {
    topRight: { x: '85%', y: '-10%', angle: 210 },
    topLeft: { x: '15%', y: '-10%', angle: 150 },
    center: { x: '50%', y: '-5%', angle: 180 },
  };
  const c = corners[fromCorner] || corners.topRight;
  const breathe = 0.6 + Math.sin(frame * 0.015) * 0.2;
  const shift = noise2D('lr', frame * 0.005, 0) * 3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      {[0, 1, 2].map((i) => {
        const spreadAngle = (i - 1) * 15 + shift;
        const rayOpacity = (0.04 - i * 0.01) * breathe;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: c.x,
              top: c.y,
              width: '200%',
              height: 4,
              background: `linear-gradient(90deg, rgba(153, 69, 255, ${rayOpacity}) 0%, rgba(0, 212, 255, ${rayOpacity * 0.5}) 40%, transparent 80%)`,
              transformOrigin: '0% 50%',
              transform: `rotate(${c.angle + spreadAngle}deg)`,
              filter: 'blur(8px)',
            }}
          />
        );
      })}
    </div>
  );
};

// ─── Animated Glow Orbs (upgraded) ───
const GlowOrb = ({ color, size, top, left, delay = 0, frame }) => {
  const drift = noise2D('orb' + color, frame * 0.004, 0) * 25;
  const driftY = noise2D('orby' + color, frame * 0.003, 1) * 20;
  const breathe = 0.8 + Math.sin(frame * 0.02 + delay * 0.1) * 0.2;
  const opacity = interpolate(frame, [delay, delay + 30], [0, 0.15 * breathe], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: size,
        height: size,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${color}20 0%, ${color}08 40%, transparent 70%)`,
        top,
        left,
        filter: 'blur(60px)',
        opacity,
        transform: `translate(${drift}px, ${driftY}px)`,
      }}
    />
  );
};

// ─── Scan Line (upgraded with glow) ───
const ScanLine = ({ frame }) => {
  const y = interpolate(frame % 240, [0, 240], [-2, 102]);
  const opacity = 0.15 + Math.sin(frame * 0.1) * 0.05;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: `${y}%`,
          height: 1,
          background: `linear-gradient(90deg, transparent 0%, ${theme.colors.purple}20 20%, ${theme.colors.cyan}15 50%, ${theme.colors.purple}20 80%, transparent 100%)`,
          boxShadow: `0 0 20px ${theme.colors.purple}15`,
          opacity,
        }}
      />
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// MAIN BACKGROUND COMPONENT
// ═══════════════════════════════════════════════════════════════
export const Background = ({
  children,
  variant = 'default',
  showScanLine = false,
  showParticles = true,
  showGrid = true,
  showVignette = true,
  showLightRays = false,
  showNoise = true,
  lightRayCorner = 'topRight',
  particleCount = 35,
  vignetteIntensity = 0.55,
  gridSpacing = 60,
  orbs = [],
}) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        overflow: 'hidden',
        background: '#0a0a1a',
      }}
    >
      {/* Layer 1: Mesh gradient base */}
      <MeshGradient frame={frame} variant={variant} />

      {/* Layer 2: Grid */}
      {showGrid && <PulsingGrid frame={frame} spacing={gridSpacing} />}

      {/* Layer 3: Glow orbs */}
      {orbs.map((orb, i) => (
        <GlowOrb key={i} {...orb} frame={frame} />
      ))}

      {/* Layer 4: Light rays */}
      {showLightRays && <LightRays frame={frame} fromCorner={lightRayCorner} />}

      {/* Layer 5: Floating particles */}
      {showParticles && <FloatingParticles frame={frame} count={particleCount} />}

      {/* Layer 6: Scan line */}
      {showScanLine && <ScanLine frame={frame} />}

      {/* Layer 7: Film grain */}
      {showNoise && <NoiseOverlay frame={frame} opacity={0.025} />}

      {/* Layer 8: Vignette */}
      {showVignette && <Vignette intensity={vignetteIntensity} />}

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1, width: '100%', height: '100%' }}>
        {children}
      </div>
    </AbsoluteFill>
  );
};
