import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { noise2D } from '@remotion/noise';
import { theme, hexToRgb, easing } from '../theme';

// ─── Animated PCB-style circuit traces ───
const CircuitPath = ({ points, color, startFrame, frame, index, glowing = true }) => {
  const elapsed = frame - startFrame;
  const rgb = hexToRgb(color);

  // Build SVG path
  let pathD = '';
  points.forEach((p, i) => {
    pathD += i === 0 ? `M ${p.x} ${p.y}` : ` L ${p.x} ${p.y}`;
  });

  // Calculate total path length (approximate)
  let totalLength = 0;
  for (let i = 1; i < points.length; i++) {
    const dx = points[i].x - points[i - 1].x;
    const dy = points[i].y - points[i - 1].y;
    totalLength += Math.sqrt(dx * dx + dy * dy);
  }

  // Draw progress
  const rawProgress = interpolate(elapsed, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const drawProgress = easing.easeOutCubic(rawProgress);
  const dashOffset = totalLength * (1 - drawProgress);

  // Flowing particle along path
  const particleProgress = ((elapsed * 2) % (totalLength + 20)) / totalLength;

  // Pulse
  const pulse = 0.6 + Math.sin(frame * 0.04 + index) * 0.2;

  return (
    <g>
      {/* Glow line behind */}
      {glowing && (
        <path
          d={pathD}
          fill="none"
          stroke={`rgba(${rgb}, ${0.15 * pulse})`}
          strokeWidth={6}
          strokeDasharray={totalLength}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#circuitGlow)"
        />
      )}

      {/* Main line */}
      <path
        d={pathD}
        fill="none"
        stroke={`rgba(${rgb}, ${0.5 * pulse})`}
        strokeWidth={1.5}
        strokeDasharray={totalLength}
        strokeDashoffset={dashOffset}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Junction dots */}
      {points.map((p, i) => {
        const dotDelay = i * 5;
        const dotOpacity = interpolate(elapsed, [dotDelay, dotDelay + 8], [0, 0.8], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        return (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={i === 0 || i === points.length - 1 ? 4 : 2.5}
            fill={`rgba(${rgb}, ${dotOpacity * pulse})`}
            filter={glowing ? 'url(#circuitGlow)' : undefined}
          />
        );
      })}
    </g>
  );
};

export const CircuitLines = ({
  paths = [],
  width = 1920,
  height = 1080,
  startFrame = 0,
  color = theme.colors.purple,
  secondaryColor = theme.colors.cyan,
  style = {},
}) => {
  const frame = useCurrentFrame();

  // If no paths provided, generate decorative ones
  const circuitPaths = useMemo(() => {
    if (paths.length > 0) return paths;
    // Auto-generate some circuit traces
    return [
      {
        points: [
          { x: 100, y: 200 }, { x: 200, y: 200 }, { x: 200, y: 350 },
          { x: 400, y: 350 }, { x: 400, y: 500 },
        ],
        color,
        delay: 0,
      },
      {
        points: [
          { x: width - 100, y: 150 }, { x: width - 250, y: 150 },
          { x: width - 250, y: 300 }, { x: width - 450, y: 300 },
        ],
        color: secondaryColor,
        delay: 10,
      },
      {
        points: [
          { x: 150, y: height - 200 }, { x: 350, y: height - 200 },
          { x: 350, y: height - 350 }, { x: 550, y: height - 350 },
          { x: 550, y: height - 250 },
        ],
        color,
        delay: 20,
      },
      {
        points: [
          { x: width - 150, y: height - 150 }, { x: width - 300, y: height - 150 },
          { x: width - 300, y: height - 300 },
        ],
        color: secondaryColor,
        delay: 15,
      },
    ];
  }, [paths, width, height, color, secondaryColor]);

  return (
    <svg
      width={width}
      height={height}
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        ...style,
      }}
    >
      <defs>
        <filter id="circuitGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {circuitPaths.map((path, i) => (
        <CircuitPath
          key={i}
          points={path.points}
          color={path.color || color}
          startFrame={startFrame + (path.delay || 0)}
          frame={frame}
          index={i}
        />
      ))}
    </svg>
  );
};
