import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';

// Syntax highlighting color map
const syntaxColors = {
  keyword: '#C678DD',    // purple
  string: '#98C379',     // green
  function: '#61AFEF',   // blue
  number: '#D19A66',     // orange
  comment: '#5C6370',    // gray
  operator: '#56B6C2',   // cyan
  punctuation: '#ABB2BF',// light gray
  variable: '#E06C75',   // red
  default: '#ABB2BF',    // light gray
};

// Simple token colorizer
const colorize = (text) => {
  const patterns = [
    { regex: /(\/\/.*$|#.*$)/gm, type: 'comment' },
    { regex: /(".*?"|'.*?'|`.*?`)/g, type: 'string' },
    { regex: /\b(await|async|const|let|var|return|import|from|export|def|class|if|else|for|while|try|catch|new|function)\b/g, type: 'keyword' },
    { regex: /\b(\d+\.?\d*)\b/g, type: 'number' },
    { regex: /(\w+)\s*\(/g, type: 'function' },
    { regex: /(=>|===|!==|&&|\|\||[+\-*/%]=?|[<>]=?)/g, type: 'operator' },
    { regex: /([{}()\[\];,.:?])/g, type: 'punctuation' },
  ];

  // For simplicity in Remotion, return an array of {text, color} segments
  let segments = [{ text, color: syntaxColors.default }];

  for (const pattern of patterns) {
    const newSegments = [];
    for (const seg of segments) {
      if (seg.color !== syntaxColors.default) {
        newSegments.push(seg);
        continue;
      }
      let lastIdx = 0;
      const matches = [...seg.text.matchAll(pattern.regex)];
      for (const match of matches) {
        const matchText = pattern.type === 'function' ? match[1] : match[0];
        const startIdx = pattern.type === 'function'
          ? match.index
          : match.index;
        if (startIdx > lastIdx) {
          newSegments.push({ text: seg.text.slice(lastIdx, startIdx), color: syntaxColors.default });
        }
        newSegments.push({ text: matchText, color: syntaxColors[pattern.type] });
        lastIdx = startIdx + matchText.length;
      }
      if (lastIdx < seg.text.length) {
        newSegments.push({ text: seg.text.slice(lastIdx), color: syntaxColors.default });
      }
    }
    segments = newSegments;
  }
  return segments;
};

export const CodeBlock = ({
  code,
  startFrame = 0,
  typingSpeed = 1.5,
  fontSize = 14,
  showCursor = true,
  showLineNumbers = true,
  title = 'main.py',
  maxWidth = 650,
  accentColor = theme.colors.purple,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const elapsed = frame - startFrame;
  if (elapsed < 0) return null;

  const rgb = hexToRgb(accentColor);

  // Card entrance
  const cardScale = spring({
    frame,
    fps,
    delay: startFrame,
    config: theme.springs.snappy,
  });

  const cardOpacity = interpolate(elapsed, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Typing animation
  const totalChars = code.length;
  const charsVisible = Math.min(Math.floor(elapsed * typingSpeed), totalChars);
  const visibleCode = code.slice(0, charsVisible);
  const isTyping = charsVisible < totalChars;

  // Cursor blink
  const cursorVisible = showCursor && (isTyping || elapsed % 30 < 18);

  // Split into lines and colorize
  const lines = visibleCode.split('\n');

  return (
    <div
      style={{
        transform: `scale(${cardScale})`,
        opacity: cardOpacity,
        maxWidth,
        width: '100%',
      }}
    >
      <div
        style={{
          background: 'rgba(10, 10, 30, 0.8)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 12,
          overflow: 'hidden',
          boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 30px rgba(${rgb}, 0.08)`,
        }}
      >
        {/* Title bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '10px 16px',
            background: 'rgba(255,255,255,0.02)',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <div style={{ display: 'flex', gap: 7 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FF5F57' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#FEBC2E' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#28C840' }} />
          </div>
          <span
            style={{
              fontSize: 11,
              color: theme.colors.muted,
              marginLeft: 14,
              fontFamily: fontFamily.mono,
            }}
          >
            {title}
          </span>
        </div>

        {/* Code area */}
        <div style={{ padding: '16px 20px', overflowX: 'hidden' }}>
          {lines.map((line, lineIdx) => {
            const segments = colorize(line);
            return (
              <div
                key={lineIdx}
                style={{
                  display: 'flex',
                  minHeight: fontSize * 1.6,
                  alignItems: 'center',
                }}
              >
                {showLineNumbers && (
                  <span
                    style={{
                      width: 32,
                      fontSize: fontSize * 0.85,
                      color: theme.colors.muted,
                      fontFamily: fontFamily.mono,
                      textAlign: 'right',
                      marginRight: 16,
                      userSelect: 'none',
                      flexShrink: 0,
                      opacity: 0.5,
                    }}
                  >
                    {lineIdx + 1}
                  </span>
                )}
                <span
                  style={{
                    fontFamily: fontFamily.mono,
                    fontSize,
                    lineHeight: 1.6,
                    whiteSpace: 'pre',
                  }}
                >
                  {segments.map((seg, si) => (
                    <span key={si} style={{ color: seg.color }}>
                      {seg.text}
                    </span>
                  ))}
                  {/* Cursor at end of last line */}
                  {lineIdx === lines.length - 1 && cursorVisible && (
                    <span
                      style={{
                        color: accentColor,
                        opacity: 0.9,
                        fontWeight: 400,
                      }}
                    >
                      ▌
                    </span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
