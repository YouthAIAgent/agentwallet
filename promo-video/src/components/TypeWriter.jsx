import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { fontFamily } from '../fonts';
import { theme } from '../theme';

export const TypeWriter = ({
  text,
  startFrame = 0,
  speed = 1.5,
  color = theme.colors.white,
  fontSize = 42,
  fontWeight = 800,
  cursorColor = theme.colors.purple,
  mono = false,
  showCursor = true,
}) => {
  const frame = useCurrentFrame();
  const elapsed = frame - startFrame;
  if (elapsed < 0) return null;

  const charsToShow = Math.min(Math.floor(elapsed * speed), text.length);
  const displayText = text.slice(0, charsToShow);
  const cursorVisible = elapsed % 16 < 10 && charsToShow < text.length;

  return (
    <span
      style={{
        color,
        fontSize,
        fontWeight,
        fontFamily: mono ? fontFamily.mono : fontFamily.heading,
        letterSpacing: mono ? 0 : '-0.02em',
      }}
    >
      {displayText}
      {showCursor && cursorVisible && (
        <span style={{ color: cursorColor, opacity: 0.8 }}>|</span>
      )}
    </span>
  );
};
