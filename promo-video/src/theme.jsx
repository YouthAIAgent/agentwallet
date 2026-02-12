// ═══════════════════════════════════════════════════════════════
// THEME — Cinema-Grade Design System
// ═══════════════════════════════════════════════════════════════

// ─── Easing Functions ───
// Custom cubic-bezier curves for professional motion
const cubicBezier = (p1x, p1y, p2x, p2y) => {
  // Attempt Newton's method for t given x, then evaluate y
  return (x) => {
    let t = x;
    for (let i = 0; i < 8; i++) {
      const cx = 3 * p1x * t * (1 - t) * (1 - t) + 3 * p2x * t * t * (1 - t) + t * t * t - x;
      const dx = 3 * p1x * (1 - t) * (1 - t) - 6 * p1x * t * (1 - t) + 6 * p2x * t * (1 - t) - 3 * p2x * t * t + 3 * t * t;
      if (Math.abs(dx) < 1e-6) break;
      t -= cx / dx;
    }
    t = Math.max(0, Math.min(1, t));
    return 3 * p1y * t * (1 - t) * (1 - t) + 3 * p2y * t * t * (1 - t) + t * t * t;
  };
};

export const easing = {
  // Dramatic entrances
  easeOutExpo: (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  easeOutQuart: (t) => 1 - Math.pow(1 - t, 4),
  easeOutCubic: (t) => 1 - Math.pow(1 - t, 3),
  easeOutQuint: (t) => 1 - Math.pow(1 - t, 5),
  easeOutBack: (t) => {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  },
  // Smooth transitions
  easeInOutCubic: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  easeInOutQuart: (t) => t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2,
  easeInOutQuint: (t) => t < 0.5 ? 16 * t * t * t * t * t : 1 - Math.pow(-2 * t + 2, 5) / 2,
  // Elastic / Bounce
  easeOutElastic: (t) => {
    if (t === 0 || t === 1) return t;
    return Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3) + 1;
  },
  // Apple-style smooth
  appleSmooth: cubicBezier(0.25, 0.1, 0.25, 1.0),
  // Snappy like Stripe
  stripeSnap: cubicBezier(0.22, 1, 0.36, 1),
};

export const theme = {
  colors: {
    // Core
    bg: '#0a0a1a',
    bgAlt: '#12122a',
    bgDeep: '#050510',
    surface: '#1a1a35',
    surfaceLight: '#22224a',

    // Solana palette (extended with depth)
    purple: '#9945FF',
    purpleLight: '#B77FFF',
    purpleDark: '#6B1FCC',
    purpleMuted: '#5A2D99',
    green: '#14F195',
    greenLight: '#5BFBB9',
    greenDark: '#0BBF73',

    // Accent spectrum
    cyan: '#00D4FF',
    cyanDark: '#0099BB',
    orange: '#FF6B35',
    orangeLight: '#FF9B6B',
    pink: '#E040FB',
    pinkDark: '#A020B0',
    blue: '#4F8FFF',
    yellow: '#FBBF24',
    red: '#FF3B5C',

    // Neutral
    white: '#FFFFFF',
    offWhite: '#E2E8F0',
    gray: '#94A3B8',
    dim: '#64748B',
    muted: '#475569',
    dark: '#1E293B',
  },

  fonts: {
    heading: 'Inter',
    mono: 'JetBrains Mono',
  },

  // Spring configs for remotion spring()
  springs: {
    // Organic entrances
    gentle: { damping: 18, mass: 1, stiffness: 80 },
    // Quick but smooth
    snappy: { damping: 14, mass: 0.7, stiffness: 220 },
    // Playful overshoot
    bouncy: { damping: 8, mass: 0.8, stiffness: 180 },
    // Slow cinematic reveal
    slow: { damping: 24, mass: 1.5, stiffness: 50 },
    // Hard slam (feature cards)
    slam: { damping: 20, mass: 0.5, stiffness: 350 },
    // Soft float
    float: { damping: 30, mass: 2, stiffness: 40 },
    // Scale pop
    pop: { damping: 10, mass: 0.6, stiffness: 280 },
  },

  // ─── Timing presets (in seconds, multiply by fps for frames) ───
  timing: {
    sceneGap: 0.1,        // gap between scenes
    staggerSmall: 0.05,   // between list items
    staggerMedium: 0.12,  // between cards
    staggerLarge: 0.25,   // between major elements
    fadeIn: 0.3,           // standard fade
    fadeInSlow: 0.6,       // cinematic fade
    holdMin: 0.8,          // minimum hold time
    holdStandard: 2.0,     // standard read time
    transitionDuration: 0.4, // transition between scenes
  },

  // ─── Glow / Shadow presets ───
  glow: {
    // Text glows
    textPurple: '0 0 40px rgba(153, 69, 255, 0.6), 0 0 80px rgba(153, 69, 255, 0.3), 0 0 120px rgba(153, 69, 255, 0.1)',
    textGreen: '0 0 40px rgba(20, 241, 149, 0.6), 0 0 80px rgba(20, 241, 149, 0.3), 0 0 120px rgba(20, 241, 149, 0.1)',
    textCyan: '0 0 40px rgba(0, 212, 255, 0.6), 0 0 80px rgba(0, 212, 255, 0.3)',
    textWhite: '0 0 20px rgba(255, 255, 255, 0.5), 0 0 60px rgba(255, 255, 255, 0.2)',
    // Subtle text shadow for readability
    textSubtle: '0 2px 20px rgba(0, 0, 0, 0.8)',
    // Box glows
    boxPurple: '0 0 30px rgba(153, 69, 255, 0.3), inset 0 0 30px rgba(153, 69, 255, 0.05)',
    boxGreen: '0 0 30px rgba(20, 241, 149, 0.3), inset 0 0 30px rgba(20, 241, 149, 0.05)',
    boxCyan: '0 0 30px rgba(0, 212, 255, 0.3), inset 0 0 30px rgba(0, 212, 255, 0.05)',
    // Neon line glow
    neonPurple: '0 0 8px rgba(153, 69, 255, 0.8), 0 0 20px rgba(153, 69, 255, 0.4)',
    neonGreen: '0 0 8px rgba(20, 241, 149, 0.8), 0 0 20px rgba(20, 241, 149, 0.4)',
    neonCyan: '0 0 8px rgba(0, 212, 255, 0.8), 0 0 20px rgba(0, 212, 255, 0.4)',
  },

  // ─── Gradient presets ───
  gradients: {
    // Mesh-like backgrounds (multi-stop radials composed via CSS)
    meshDark: `
      radial-gradient(ellipse at 20% 20%, rgba(153, 69, 255, 0.08) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 30%, rgba(0, 212, 255, 0.06) 0%, transparent 50%),
      radial-gradient(ellipse at 40% 80%, rgba(20, 241, 149, 0.05) 0%, transparent 50%),
      linear-gradient(180deg, #0a0a1a 0%, #050510 100%)
    `,
    meshPurple: `
      radial-gradient(ellipse at 30% 20%, rgba(153, 69, 255, 0.15) 0%, transparent 50%),
      radial-gradient(ellipse at 70% 70%, rgba(107, 31, 204, 0.1) 0%, transparent 50%),
      linear-gradient(135deg, #0a0a1a 0%, #12122a 100%)
    `,
    meshGreen: `
      radial-gradient(ellipse at 60% 30%, rgba(20, 241, 149, 0.1) 0%, transparent 50%),
      radial-gradient(ellipse at 20% 80%, rgba(0, 212, 255, 0.06) 0%, transparent 50%),
      linear-gradient(135deg, #0a0a1a 0%, #0d1a15 100%)
    `,
    // Glass card backgrounds
    glassDark: 'rgba(15, 15, 35, 0.6)',
    glassLight: 'rgba(255, 255, 255, 0.03)',
    // Gradient strokes
    strokePurpleGreen: 'linear-gradient(135deg, #9945FF, #14F195)',
    strokePurpleCyan: 'linear-gradient(135deg, #9945FF, #00D4FF)',
    strokeCyanGreen: 'linear-gradient(90deg, #00D4FF, #14F195)',
    // Accent bars
    accentBar: 'linear-gradient(90deg, #9945FF 0%, #14F195 50%, #00D4FF 100%)',
  },

  // ─── Glass effect styles ───
  glass: {
    card: {
      background: 'rgba(15, 15, 40, 0.55)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: 16,
    },
    cardHover: {
      background: 'rgba(20, 20, 50, 0.65)',
      backdropFilter: 'blur(24px)',
      WebkitBackdropFilter: 'blur(24px)',
      border: '1px solid rgba(255, 255, 255, 0.12)',
      borderRadius: 16,
    },
    subtle: {
      background: 'rgba(255, 255, 255, 0.02)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.04)',
      borderRadius: 12,
    },
  },
};

// ─── Utility: hex to rgb string ───
export function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `${r},${g},${b}`;
}

// ─── Utility: apply easing to a 0-1 progress value ───
export function applyEasing(progress, easingFn) {
  return easingFn(Math.max(0, Math.min(1, progress)));
}
