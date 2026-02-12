import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from 'remotion';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';
import { 
  Background, 
  GlitchText, 
  FadeSlide, 
  ParticleExplosion, 
  CodeBlock,
  NumberCounter,
  Badge,
  CircuitLines
} from '../components';

const FPS = 30;

// Scene boundaries (frames at 30fps for 60s total = 1800 frames)
const INTRO_START = 0;       // 0-5s  
const INTRO_END = 150;       // 5s * 30fps = 150 frames
const PROBLEM_START = 150;   // 5-15s
const PROBLEM_END = 450;     // 15s * 30fps = 450 frames
const SOLUTION_START = 450;  // 15-30s
const SOLUTION_END = 900;    // 30s * 30fps = 900 frames
const FEATURES_START = 900;  // 30-45s
const FEATURES_END = 1350;   // 45s * 30fps = 1350 frames
const HACKATHON_START = 1350; // 45-55s
const HACKATHON_END = 1650;  // 55s * 30fps = 1650 frames
const CTA_START = 1650;      // 55-60s
const CTA_END = 1800;        // 60s * 30fps = 1800 frames

/* ═════════════════════════════════════════════════════════════
   SCENE 1 — INTRO (0-5s)
   "AgentWallet Protocol" title with glitch effect, "Live Demo" badge
   ═════════════════════════════════════════════════════════════ */
const IntroScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lf = frame - INTRO_START;
  
  const fadeOut = interpolate(frame, [INTRO_END-30, INTRO_END], [1, 0], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });

  const titleSpring = spring({
    frame,
    fps,
    delay: INTRO_START + 10,
    config: { damping: 12, mass: 1, stiffness: 120 }
  });

  const badgeDelay = INTRO_START + 60;
  const badgeOpacity = interpolate(frame, [badgeDelay, badgeDelay + 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  return (
    <AbsoluteFill style={{ 
      justifyContent: 'center', 
      alignItems: 'center', 
      opacity: fadeOut 
    }}>
      {/* Particle explosion on title reveal */}
      {lf >= 10 && (
        <ParticleExplosion
          startFrame={INTRO_START + 10}
          x="50%"
          y="45%"
          count={25}
          color={theme.colors.purple}
          secondaryColor={theme.colors.cyan}
          duration={30}
          spread={200}
        />
      )}

      <div style={{ textAlign: 'center', position: 'relative' }}>
        {/* Main title with glitch effect */}
        <div style={{ 
          transform: `scale(${titleSpring})`,
          marginBottom: 20 
        }}>
          <GlitchText
            text="AgentWallet"
            startFrame={INTRO_START + 10}
            color={theme.colors.white}
            fontSize={84}
            fontWeight={900}
            glitchIntensity={1.2}
            duration={25}
          />
          <div style={{ marginTop: 8 }}>
            <GlitchText
              text="Protocol"
              startFrame={INTRO_START + 25}
              color={theme.colors.purple}
              fontSize={72}
              fontWeight={900}
              glitchIntensity={0.8}
              duration={20}
            />
          </div>
        </div>

        {/* Live Demo badge */}
        <div style={{ 
          opacity: badgeOpacity,
          transform: `translateY(${interpolate(frame, [badgeDelay, badgeDelay + 15], [10, 0], {
            extrapolateLeft: 'clamp', 
            extrapolateRight: 'clamp'
          })}px)`
        }}>
          <Badge 
            text="LIVE DEMO"
            color={theme.colors.green}
            glowing
            style={{ 
              fontSize: 18,
              padding: '8px 20px',
              borderRadius: 25,
              background: `linear-gradient(90deg, ${theme.colors.green}15, ${theme.colors.cyan}10)`,
              border: `2px solid ${theme.colors.green}`,
              boxShadow: theme.glow.neonGreen
            }}
          />
        </div>

        {/* Accent lines */}
        <div style={{
          position: 'absolute',
          bottom: -40,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 200,
          height: 2,
          background: theme.gradients.accentBar,
          opacity: interpolate(frame, [INTRO_START + 80, INTRO_START + 100], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp'
          })
        }} />
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 2 — PROBLEM (5-15s)
   "AI agents need wallets. Private keys = security nightmare." with visual
   ═════════════════════════════════════════════════════════════ */
const ProblemScene = () => {
  const frame = useCurrentFrame();
  const lf = frame - PROBLEM_START;
  
  const fadeIn = interpolate(lf, [0, 20], [0, 1], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });
  const fadeOut = interpolate(frame, [PROBLEM_END-30, PROBLEM_END], [1, 0], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });

  const warningPulse = 0.7 + Math.sin(lf * 0.15) * 0.3;

  return (
    <AbsoluteFill style={{ 
      justifyContent: 'center', 
      alignItems: 'center', 
      opacity: fadeIn * fadeOut,
      padding: '0 100px'
    }}>
      <div style={{ textAlign: 'center', maxWidth: 900 }}>
        {/* Problem headline */}
        <FadeSlide startFrame={PROBLEM_START + 15} duration={20} direction="up">
          <div style={{ fontSize: 20, color: theme.colors.orange, fontFamily: fontFamily.mono, 
            letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
            THE PROBLEM
          </div>
        </FadeSlide>

        <FadeSlide startFrame={PROBLEM_START + 30} duration={25} direction="up">
          <div style={{ 
            fontSize: 48, 
            fontWeight: 800, 
            color: theme.colors.white, 
            fontFamily: fontFamily.heading,
            lineHeight: 1.2,
            marginBottom: 30,
            textShadow: theme.glow.textWhite
          }}>
            AI agents need wallets.
          </div>
        </FadeSlide>

        <FadeSlide startFrame={PROBLEM_START + 60} duration={25} direction="up">
          <div style={{ 
            fontSize: 44, 
            fontWeight: 700, 
            color: theme.colors.red, 
            fontFamily: fontFamily.heading,
            lineHeight: 1.2,
            textShadow: theme.glow.textSubtle
          }}>
            Private keys = security nightmare.
          </div>
        </FadeSlide>

        {/* Visual warning elements */}
        {lf >= 90 && (
          <>
            <div style={{
              position: 'absolute',
              top: '20%',
              right: '15%',
              fontSize: 60,
              opacity: warningPulse,
              filter: `drop-shadow(0 0 20px ${theme.colors.red}80)`
            }}>
              ⚠️
            </div>
            <div style={{
              position: 'absolute',
              bottom: '25%',
              left: '10%',
              fontSize: 50,
              opacity: warningPulse * 0.8,
              filter: `drop-shadow(0 0 15px ${theme.colors.orange}60)`
            }}>
              🔓
            </div>
          </>
        )}

        {/* Circuit lines showing broken connections */}
        <CircuitLines 
          startFrame={PROBLEM_START + 120}
          variant="broken"
          color={theme.colors.red}
          intensity={0.4}
        />
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 3 — SOLUTION (15-30s)
   Show PDA wallet architecture, code snippet of creating a wallet
   ═════════════════════════════════════════════════════════════ */
const SolutionScene = () => {
  const frame = useCurrentFrame();
  const lf = frame - SOLUTION_START;
  
  const fadeIn = interpolate(lf, [0, 20], [0, 1], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });
  const fadeOut = interpolate(frame, [SOLUTION_END-30, SOLUTION_END], [1, 0], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });

  const codeSnippet = `from agentwallet import AgentWallet

# Create secure PDA wallet for your agent
wallet = AgentWallet.create(
    agent_id="claude-opus",
    budget_sol=10.0,
    policies=["no_external_transfers"]
)

print(f"🚀 Agent wallet: {wallet.address}")
# 🚀 Agent wallet: 7xKp...3mNq`;

  return (
    <AbsoluteFill style={{ 
      justifyContent: 'center', 
      alignItems: 'center', 
      opacity: fadeIn * fadeOut,
      padding: '0 60px'
    }}>
      <div style={{ width: '100%', maxWidth: 1200, display: 'flex', gap: 60 }}>
        {/* Left side: Architecture */}
        <div style={{ flex: 1 }}>
          <FadeSlide startFrame={SOLUTION_START + 15} duration={20} direction="left">
            <div style={{ fontSize: 20, color: theme.colors.green, fontFamily: fontFamily.mono, 
              letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
              THE SOLUTION
            </div>
          </FadeSlide>

          <FadeSlide startFrame={SOLUTION_START + 30} duration={25} direction="left">
            <div style={{ 
              fontSize: 42, 
              fontWeight: 800, 
              color: theme.colors.white, 
              fontFamily: fontFamily.heading,
              marginBottom: 30,
              textShadow: theme.glow.textWhite
            }}>
              PDA Wallet Architecture
            </div>
          </FadeSlide>

          <FadeSlide startFrame={SOLUTION_START + 50} duration={25} direction="left">
            <div style={{ 
              background: 'rgba(20,241,149,0.05)',
              border: `1px solid ${theme.colors.green}30`,
              borderRadius: 16,
              padding: '24px',
              marginBottom: 20
            }}>
              <div style={{ fontSize: 18, color: theme.colors.green, fontWeight: 600, marginBottom: 15 }}>
                ✅ Program Derived Addresses
              </div>
              <div style={{ fontSize: 16, color: theme.colors.offWhite, lineHeight: 1.5 }}>
                • No private key storage<br/>
                • Deterministic addresses<br/>
                • Built-in spending policies<br/>
                • Multi-signature support
              </div>
            </div>
          </FadeSlide>

          {/* Security shield visual */}
          {lf >= 100 && (
            <div style={{
              position: 'absolute',
              bottom: '15%',
              left: '5%',
              fontSize: 80,
              opacity: 0.3,
              filter: `drop-shadow(0 0 30px ${theme.colors.green}60)`
            }}>
              🛡️
            </div>
          )}
        </div>

        {/* Right side: Code */}
        <div style={{ flex: 1 }}>
          <FadeSlide startFrame={SOLUTION_START + 70} duration={25} direction="right">
            <div style={{ fontSize: 18, color: theme.colors.purple, fontFamily: fontFamily.mono, 
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 20 }}>
              Python SDK
            </div>
          </FadeSlide>

          <FadeSlide startFrame={SOLUTION_START + 90} duration={25} direction="right">
            <CodeBlock
              code={codeSnippet}
              language="python"
              theme="dark"
              fontSize={14}
              lineNumbers
              style={{
                borderRadius: 12,
                border: `1px solid ${theme.colors.purple}30`,
                boxShadow: theme.glow.boxPurple
              }}
            />
          </FadeSlide>

          {/* Rocket visual */}
          {lf >= 120 && (
            <div style={{
              position: 'absolute',
              top: '20%',
              right: '5%',
              fontSize: 60,
              opacity: 0.4,
              filter: `drop-shadow(0 0 20px ${theme.colors.purple}60)`
            }}>
              🚀
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 4 — FEATURES (30-45s)
   Quick cuts: 33 MCP Tools, x402 Payments, Agent Escrow, Spend Policies
   ═════════════════════════════════════════════════════════════ */
const FeaturesScene = () => {
  const frame = useCurrentFrame();
  const lf = frame - FEATURES_START;
  
  const fadeIn = interpolate(lf, [0, 15], [0, 1], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });
  const fadeOut = interpolate(frame, [FEATURES_END-30, FEATURES_END], [1, 0], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });

  const features = [
    { title: "33 MCP Tools", value: 33, color: theme.colors.purple, icon: "🔧", desc: "Built-in tool integrations" },
    { title: "x402 Payments", value: 402, color: theme.colors.green, icon: "💳", desc: "HTTP 402 payment protocol" },
    { title: "Agent Escrow", value: "100%", color: theme.colors.cyan, icon: "🔒", desc: "Trustless fund management" },
    { title: "Spend Policies", value: "LIVE", color: theme.colors.orange, icon: "📋", desc: "Automated compliance" }
  ];

  return (
    <AbsoluteFill style={{ 
      justifyContent: 'center', 
      alignItems: 'center', 
      opacity: fadeIn * fadeOut,
      padding: '0 60px'
    }}>
      <div style={{ width: '100%', maxWidth: 1300 }}>
        <FadeSlide startFrame={FEATURES_START + 5} duration={15} direction="up">
          <div style={{ textAlign: 'center', marginBottom: 50 }}>
            <div style={{ fontSize: 18, color: theme.colors.cyan, fontFamily: fontFamily.mono, 
              letterSpacing: 3, textTransform: 'uppercase', marginBottom: 15 }}>
              FEATURES
            </div>
            <div style={{ 
              fontSize: 48, 
              fontWeight: 800, 
              color: theme.colors.white, 
              fontFamily: fontFamily.heading,
              textShadow: theme.glow.textWhite
            }}>
              Production Ready
            </div>
          </div>
        </FadeSlide>

        <div style={{ display: 'flex', gap: 30 }}>
          {features.map((feature, i) => {
            const delay = 30 + i * 25;
            const featureOpacity = interpolate(lf, [delay, delay + 15], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp'
            });
            const featureScale = easing.easeOutBack(interpolate(lf, [delay, delay + 20], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp'
            }));

            const rgb = hexToRgb(feature.color);

            return (
              <div key={i} style={{ 
                flex: 1, 
                opacity: featureOpacity,
                transform: `scale(${featureScale})`
              }}>
                <div style={{
                  background: `rgba(${rgb}, 0.08)`,
                  border: `2px solid rgba(${rgb}, 0.3)`,
                  borderRadius: 20,
                  padding: '30px 20px',
                  textAlign: 'center',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: `0 0 30px rgba(${rgb}, 0.15)`
                }}>
                  {/* Icon */}
                  <div style={{
                    fontSize: 40,
                    marginBottom: 15,
                    filter: `drop-shadow(0 0 10px ${feature.color}60)`
                  }}>
                    {feature.icon}
                  </div>

                  {/* Value counter */}
                  <div style={{ marginBottom: 10 }}>
                    {typeof feature.value === 'number' ? (
                      <NumberCounter
                        targetValue={feature.value}
                        startFrame={FEATURES_START + delay + 10}
                        duration={30}
                        fontSize={42}
                        color={feature.color}
                        fontWeight={900}
                      />
                    ) : (
                      <div style={{
                        fontSize: 42,
                        fontWeight: 900,
                        color: feature.color,
                        fontFamily: fontFamily.heading,
                        textShadow: `0 0 20px rgba(${rgb}, 0.6)`
                      }}>
                        {feature.value}
                      </div>
                    )}
                  </div>

                  {/* Title */}
                  <div style={{
                    fontSize: 18,
                    fontWeight: 700,
                    color: theme.colors.white,
                    fontFamily: fontFamily.heading,
                    marginBottom: 8
                  }}>
                    {feature.title}
                  </div>

                  {/* Description */}
                  <div style={{
                    fontSize: 12,
                    color: theme.colors.dim,
                    fontFamily: fontFamily.mono,
                    letterSpacing: 1
                  }}>
                    {feature.desc}
                  </div>

                  {/* Glow effect */}
                  <div style={{
                    position: 'absolute',
                    top: -2,
                    left: '20%',
                    right: '20%',
                    height: 2,
                    background: `linear-gradient(90deg, transparent, ${feature.color}, transparent)`,
                    opacity: 0.6
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 5 — HACKATHON (45-55s)
   "Competing in @colosseum Agent Hackathon", "$100K in prizes", Vote CTA
   ═════════════════════════════════════════════════════════════ */
const HackathonScene = () => {
  const frame = useCurrentFrame();
  const lf = frame - HACKATHON_START;
  
  const fadeIn = interpolate(lf, [0, 15], [0, 1], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });
  const fadeOut = interpolate(frame, [HACKATHON_END-30, HACKATHON_END], [1, 0], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });

  const prizeGlow = 0.8 + Math.sin(lf * 0.1) * 0.2;

  return (
    <AbsoluteFill style={{ 
      justifyContent: 'center', 
      alignItems: 'center', 
      opacity: fadeIn * fadeOut,
      textAlign: 'center'
    }}>
      <div style={{ maxWidth: 900 }}>
        {/* Hackathon announcement */}
        <FadeSlide startFrame={HACKATHON_START + 10} duration={20} direction="up">
          <div style={{ fontSize: 20, color: theme.colors.cyan, fontFamily: fontFamily.mono, 
            letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
            HACKATHON
          </div>
        </FadeSlide>

        <FadeSlide startFrame={HACKATHON_START + 25} duration={25} direction="up">
          <div style={{ 
            fontSize: 52, 
            fontWeight: 800, 
            color: theme.colors.white, 
            fontFamily: fontFamily.heading,
            marginBottom: 20,
            textShadow: theme.glow.textWhite
          }}>
            Competing in
          </div>
        </FadeSlide>

        <FadeSlide startFrame={HACKATHON_START + 45} duration={25} direction="up">
          <div style={{ 
            fontSize: 48, 
            fontWeight: 900, 
            color: theme.colors.purple, 
            fontFamily: fontFamily.heading,
            marginBottom: 30,
            textShadow: theme.glow.textPurple
          }}>
            @colosseum Agent Hackathon
          </div>
        </FadeSlide>

        {/* Prize announcement */}
        <FadeSlide startFrame={HACKATHON_START + 70} duration={25} direction="up">
          <div style={{
            background: 'rgba(255,215,0,0.1)',
            border: '2px solid rgba(255,215,0,0.3)',
            borderRadius: 20,
            padding: '25px 40px',
            margin: '20px auto',
            maxWidth: 400,
            boxShadow: `0 0 30px rgba(255,215,0,${0.2 * prizeGlow})`
          }}>
            <div style={{ 
              fontSize: 64, 
              fontWeight: 900, 
              color: '#FFD700', 
              fontFamily: fontFamily.heading,
              marginBottom: 10,
              textShadow: `0 0 30px rgba(255,215,0,${0.6 * prizeGlow})`
            }}>
              $100K
            </div>
            <div style={{ 
              fontSize: 18, 
              color: theme.colors.offWhite, 
              fontFamily: fontFamily.mono,
              letterSpacing: 2,
              textTransform: 'uppercase'
            }}>
              IN PRIZES
            </div>
          </div>
        </FadeSlide>

        {/* Vote CTA */}
        <FadeSlide startFrame={HACKATHON_START + 110} duration={25} direction="up">
          <div style={{
            background: `linear-gradient(135deg, ${theme.colors.green}20, ${theme.colors.cyan}15)`,
            border: `2px solid ${theme.colors.green}`,
            borderRadius: 15,
            padding: '20px 50px',
            display: 'inline-block',
            boxShadow: theme.glow.boxGreen,
            cursor: 'pointer'
          }}>
            <div style={{ 
              fontSize: 28, 
              fontWeight: 800, 
              color: theme.colors.green, 
              fontFamily: fontFamily.heading,
              textShadow: theme.glow.textGreen
            }}>
              🗳️ VOTE NOW
            </div>
          </div>
        </FadeSlide>

        {/* Decorative elements */}
        {lf >= 60 && (
          <>
            <div style={{
              position: 'absolute',
              top: '15%',
              left: '10%',
              fontSize: 50,
              opacity: 0.3,
              animation: 'float 3s ease-in-out infinite'
            }}>
              🏆
            </div>
            <div style={{
              position: 'absolute',
              bottom: '20%',
              right: '15%',
              fontSize: 40,
              opacity: 0.4
            }}>
              🎯
            </div>
          </>
        )}
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 6 — CTA (55-60s)
   "agentwallet.fun" + "Vote Now" + QR or link
   ═════════════════════════════════════════════════════════════ */
const CTAScene = () => {
  const frame = useCurrentFrame();
  const lf = frame - CTA_START;
  
  const fadeIn = interpolate(lf, [0, 15], [0, 1], { 
    extrapolateLeft: 'clamp', 
    extrapolateRight: 'clamp' 
  });

  const breathe = lf > 30 ? 0.9 + Math.sin(lf * 0.08) * 0.1 : 1;

  return (
    <AbsoluteFill style={{ 
      justifyContent: 'center', 
      alignItems: 'center', 
      opacity: fadeIn,
      textAlign: 'center'
    }}>
      <div style={{ position: 'relative' }}>
        {/* Particle explosion for finale */}
        {lf >= 5 && (
          <ParticleExplosion
            startFrame={CTA_START + 5}
            x="50%"
            y="40%"
            count={40}
            color={theme.colors.purple}
            secondaryColor={theme.colors.green}
            duration={45}
            spread={300}
          />
        )}

        {/* Main CTA */}
        <FadeSlide startFrame={CTA_START + 10} duration={20} direction="up">
          <div style={{ 
            fontSize: 72, 
            fontWeight: 900, 
            color: theme.colors.white, 
            fontFamily: fontFamily.heading,
            marginBottom: 20,
            textShadow: theme.glow.textWhite,
            transform: `scale(${breathe})`
          }}>
            AgentWallet
          </div>
        </FadeSlide>

        <FadeSlide startFrame={CTA_START + 30} duration={20} direction="up">
          <div style={{ 
            fontSize: 48, 
            fontWeight: 800, 
            color: theme.colors.purple, 
            fontFamily: fontFamily.heading,
            marginBottom: 30,
            textShadow: theme.glow.textPurple
          }}>
            agentwallet.fun
          </div>
        </FadeSlide>

        {/* Accent bar */}
        <div style={{
          width: 200,
          height: 4,
          background: theme.gradients.accentBar,
          borderRadius: 2,
          margin: '20px auto',
          opacity: interpolate(lf, [40, 55], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp'
          }),
          boxShadow: `0 0 15px rgba(153,69,255,${0.4 * breathe})`
        }} />

        {/* Final vote CTA */}
        <FadeSlide startFrame={CTA_START + 60} duration={20} direction="up">
          <div style={{
            background: `linear-gradient(135deg, ${theme.colors.green}25, ${theme.colors.cyan}20)`,
            border: `3px solid ${theme.colors.green}`,
            borderRadius: 20,
            padding: '25px 60px',
            display: 'inline-block',
            boxShadow: theme.glow.boxGreen,
            transform: `scale(${breathe})`
          }}>
            <div style={{ 
              fontSize: 32, 
              fontWeight: 900, 
              color: theme.colors.green, 
              fontFamily: fontFamily.heading,
              textShadow: theme.glow.textGreen
            }}>
              🗳️ VOTE NOW
            </div>
            <div style={{ 
              fontSize: 14, 
              color: theme.colors.offWhite, 
              fontFamily: fontFamily.mono,
              marginTop: 5,
              letterSpacing: 2
            }}>
              HACKATHON VOTING OPEN
            </div>
          </div>
        </FadeSlide>

        {/* QR Code placeholder */}
        {lf >= 80 && (
          <div style={{
            position: 'absolute',
            bottom: -120,
            right: -150,
            width: 100,
            height: 100,
            background: 'rgba(255,255,255,0.9)',
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 12,
            color: '#000',
            fontFamily: fontFamily.mono,
            opacity: 0.8
          }}>
            QR CODE
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   MAIN COMPOSITION
   ═════════════════════════════════════════════════════════════ */
export const HackathonDemo = () => {
  const frame = useCurrentFrame();

  return (
    <Background
      variant="default"
      showScanLine
      showParticles
      showGrid
      showVignette
      showNoise
      particleCount={25}
      vignetteIntensity={0.4}
    >
      {/* INTRO: 0-5s */}
      {frame < INTRO_END && (
        <Sequence from={INTRO_START} durationInFrames={INTRO_END - INTRO_START}>
          <IntroScene />
        </Sequence>
      )}

      {/* PROBLEM: 5-15s */}
      {frame >= PROBLEM_START - 10 && frame < PROBLEM_END && (
        <Sequence from={PROBLEM_START} durationInFrames={PROBLEM_END - PROBLEM_START}>
          <ProblemScene />
        </Sequence>
      )}

      {/* SOLUTION: 15-30s */}
      {frame >= SOLUTION_START - 10 && frame < SOLUTION_END && (
        <Sequence from={SOLUTION_START} durationInFrames={SOLUTION_END - SOLUTION_START}>
          <SolutionScene />
        </Sequence>
      )}

      {/* FEATURES: 30-45s */}
      {frame >= FEATURES_START - 10 && frame < FEATURES_END && (
        <Sequence from={FEATURES_START} durationInFrames={FEATURES_END - FEATURES_START}>
          <FeaturesScene />
        </Sequence>
      )}

      {/* HACKATHON: 45-55s */}
      {frame >= HACKATHON_START - 10 && frame < HACKATHON_END && (
        <Sequence from={HACKATHON_START} durationInFrames={HACKATHON_END - HACKATHON_START}>
          <HackathonScene />
        </Sequence>
      )}

      {/* CTA: 55-60s */}
      {frame >= CTA_START - 10 && (
        <Sequence from={CTA_START} durationInFrames={CTA_END - CTA_START}>
          <CTAScene />
        </Sequence>
      )}
    </Background>
  );
};