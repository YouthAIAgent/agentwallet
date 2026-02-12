import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';

// ─── Single Digit Column (Odometer) ───
const DigitColumn = ({ targetDigit, progress, fontSize, color, rgb }) => {
  // Each digit column scrolls independently
  const digits = '0123456789';
  const offset = targetDigit * progress;
  const columnHeight = fontSize * 1.2;

  return (
    <div
      style={{
        display: 'inline-block',
        height: columnHeight,
        overflow: 'hidden',
        position: 'relative',
        width: fontSize * 0.65,
      }}
    >
      <div
        style={{
          transform: `translateY(${-offset * columnHeight}px)`,
          transition: 'none',
        }}
      >
        {digits.split('').map((d, i) => (
          <div
            key={i}
            style={{
              height: columnHeight,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize,
              fontWeight: 900,
              color,
              fontFamily: fontFamily.heading,
              fontVariantNumeric: 'tabular-nums',
              textShadow: `0 0 30px rgba(${rgb}, 0.4)`,
            }}
          >
            {d}
          </div>
        ))}
      </div>
    </div>
  );
};

export const NumberCounter = ({
  value, // string like "27" or "100"
  startFrame = 0,
  duration = 40,
  color = theme.colors.purple,
  fontSize = 120,
  suffix = '',
  prefix = '',
  style = {},
}) => {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;
  if (elapsed < 0) return <div style={{ opacity: 0 }} />;

  const rgb = hexToRgb(color);

  const rawProgress = interpolate(elapsed, [0, duration], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const progress = easing.easeOutExpo(rawProgress);

  const digits = String(value).split('');

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        ...style,
      }}
    >
      {/* Prefix */}
      {prefix && (
        <span
          style={{
            fontSize: fontSize * 0.6,
            fontWeight: 800,
            color,
            fontFamily: fontFamily.heading,
            marginRight: 4,
            opacity: interpolate(elapsed, [0, 10], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          {prefix}
        </span>
      )}

      {/* Digit columns */}
      {digits.map((digit, i) => {
        const digitNum = parseInt(digit, 10);
        if (isNaN(digitNum)) {
          // Non-numeric character (like %)
          return (
            <span
              key={i}
              style={{
                fontSize,
                fontWeight: 900,
                color,
                fontFamily: fontFamily.heading,
              }}
            >
              {digit}
            </span>
          );
        }
        // Stagger each digit slightly
        const staggeredProgress = interpolate(
          elapsed,
          [i * 3, i * 3 + duration],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        return (
          <DigitColumn
            key={i}
            targetDigit={digitNum}
            progress={easing.easeOutExpo(staggeredProgress)}
            fontSize={fontSize}
            color={color}
            rgb={rgb}
          />
        );
      })}

      {/* Suffix */}
      {suffix && (
        <span
          style={{
            fontSize: fontSize * 0.5,
            fontWeight: 800,
            color,
            fontFamily: fontFamily.heading,
            marginLeft: 4,
            opacity: interpolate(elapsed, [duration * 0.5, duration * 0.7], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          {suffix}
        </span>
      )}
    </div>
  );
};
