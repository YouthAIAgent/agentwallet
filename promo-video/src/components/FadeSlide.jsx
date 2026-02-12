import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { easing } from '../theme';

export const FadeSlide = ({
  children,
  startFrame = 0,
  duration = 20,
  direction = 'up',
  distance = 30,
  style = {},
  useSpring = false,
  exitFrame,
  exitDuration = 15,
  exitDirection,
  easingFn = 'easeOutQuart',
  scale: scaleFrom,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entry animation
  let progress;
  if (useSpring) {
    progress = spring({
      frame,
      fps,
      delay: startFrame,
      config: { damping: 14, mass: 1, stiffness: 100 },
    });
  } else {
    const raw = interpolate(frame, [startFrame, startFrame + duration], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    // Apply easing
    const easeFn = easing[easingFn] || easing.easeOutQuart;
    progress = easeFn(raw);
  }

  // Exit animation
  let exitProgress = 1;
  if (exitFrame !== undefined) {
    const rawExit = interpolate(frame, [exitFrame, exitFrame + exitDuration], [1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    exitProgress = easing.easeInOutCubic(rawExit);
  }

  const finalOpacity = progress * exitProgress;

  const dirMap = {
    up: { x: 0, y: distance },
    down: { x: 0, y: -distance },
    left: { x: distance, y: 0 },
    right: { x: -distance, y: 0 },
  };

  const { x: entryX, y: entryY } = dirMap[direction] || dirMap.up;
  
  // Exit direction defaults to reverse of entry
  const exitDir = exitDirection || (direction === 'up' ? 'up' : direction === 'down' ? 'down' : direction === 'left' ? 'right' : 'left');
  const { x: exitX, y: exitY } = dirMap[exitDir] || dirMap.up;

  const translateX = entryX * (1 - progress) + (exitFrame !== undefined ? exitX * (1 - exitProgress) : 0);
  const translateY = entryY * (1 - progress) + (exitFrame !== undefined ? exitY * (1 - exitProgress) : 0);

  // Optional scale animation
  let scaleTransform = '';
  if (scaleFrom !== undefined) {
    const s = scaleFrom + (1 - scaleFrom) * progress;
    scaleTransform = ` scale(${s * (exitFrame !== undefined ? (0.95 + exitProgress * 0.05) : 1)})`;
  }

  return (
    <div
      style={{
        opacity: finalOpacity,
        transform: `translate(${translateX}px, ${translateY}px)${scaleTransform}`,
        willChange: 'transform, opacity',
        ...style,
      }}
    >
      {children}
    </div>
  );
};
