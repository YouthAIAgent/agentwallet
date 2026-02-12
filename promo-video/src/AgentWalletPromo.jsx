import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from "remotion";

// ── STYLES ──
const bg = {
  background: "linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1f 100%)",
  fontFamily: "'Inter', sans-serif",
  overflow: "hidden",
};

const dotGrid = {
  position: "absolute",
  inset: 0,
  backgroundImage: "radial-gradient(rgba(255,255,255,0.03) 1px, transparent 1px)",
  backgroundSize: "24px 24px",
};

// ── COMPONENTS ──

const GlowOrb = ({ color, size, top, left, opacity = 0.08 }) => (
  <div
    style={{
      position: "absolute",
      width: size,
      height: size,
      borderRadius: "50%",
      background: `radial-gradient(circle, ${color}${Math.round(opacity * 255).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
      top,
      left,
      filter: "blur(80px)",
    }}
  />
);

const TypeWriter = ({ text, frame, startFrame, color = "#fff", fontSize = 42, fontWeight = 800 }) => {
  const elapsed = frame - startFrame;
  if (elapsed < 0) return null;
  const charsToShow = Math.min(Math.floor(elapsed * 1.5), text.length);
  const displayText = text.slice(0, charsToShow);
  const showCursor = elapsed % 16 < 10 && charsToShow < text.length;

  return (
    <span style={{ color, fontSize, fontWeight, letterSpacing: "-0.02em" }}>
      {displayText}
      {showCursor && <span style={{ color: "#9945FF", opacity: 0.8 }}>|</span>}
    </span>
  );
};

const FadeIn = ({ children, frame, startFrame, duration = 15 }) => {
  const opacity = interpolate(frame, [startFrame, startFrame + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [startFrame, startFrame + duration], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <div style={{ opacity, transform: `translateY(${translateY}px)` }}>{children}</div>;
};

const StatBox = ({ num, label, accent, frame, startFrame, fps }) => {
  const scale = spring({ frame, from: 0, to: 1, fps, config: { damping: 12 }, delay: startFrame });
  return (
    <div
      style={{
        transform: `scale(${scale})`,
        background: `rgba(${accent}, 0.06)`,
        border: `1px solid rgba(${accent}, 0.2)`,
        borderRadius: 12,
        padding: "20px 32px",
        textAlign: "center",
        minWidth: 160,
      }}
    >
      <div style={{ fontSize: 48, fontWeight: 800, color: `rgb(${accent})` }}>{num}</div>
      <div style={{ fontSize: 12, color: "#64748b", marginTop: 6, letterSpacing: 2, textTransform: "uppercase" }}>
        {label}
      </div>
    </div>
  );
};

const ArchNode = ({ label, name, desc, accent, frame, startFrame, fps }) => {
  const scale = spring({ frame, from: 0, to: 1, fps, config: { damping: 10 }, delay: startFrame });
  return (
    <div
      style={{
        transform: `scale(${scale})`,
        background: `rgba(${accent}, 0.06)`,
        border: `1px solid rgba(${accent}, 0.25)`,
        borderRadius: 10,
        padding: "16px 24px",
        textAlign: "center",
        minWidth: 130,
      }}
    >
      <div style={{ fontSize: 10, fontWeight: 700, color: `rgb(${accent})`, letterSpacing: 2, textTransform: "uppercase", fontFamily: "'JetBrains Mono', monospace" }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 700, color: "#e2e8f0", marginTop: 6 }}>{name}</div>
      <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>{desc}</div>
    </div>
  );
};

const Arrow = ({ frame, startFrame }) => {
  const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div style={{ display: "flex", alignItems: "center", padding: "0 6px", opacity }}>
      <div style={{ width: 30, height: 1, background: "rgba(153,69,255,0.4)" }} />
      <div
        style={{
          width: 0,
          height: 0,
          borderTop: "5px solid transparent",
          borderBottom: "5px solid transparent",
          borderLeft: "8px solid rgba(153,69,255,0.5)",
        }}
      />
    </div>
  );
};

// ── SCENES ──

const Scene1_Boot = ({ frame }) => (
  <AbsoluteFill style={{ ...bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
    <div style={dotGrid} />
    <GlowOrb color="#9945FF" size={500} top="-150px" left="60%" />
    <div style={{ position: "relative", zIndex: 1, maxWidth: 600 }}>
      {[
        { text: "[BOOT] AgentWallet Protocol v2.0.0", color: "#00D4FF", delay: 0 },
        { text: "[INIT] Connecting to Solana mainnet...", color: "#ffcc00", delay: 15 },
        { text: "[OK] Node synced. Block height: 298,441,203", color: "#00ff41", delay: 30 },
        { text: "[OK] MCP Server online. 27 tools loaded.", color: "#00ff41", delay: 45 },
        { text: "[OK] Escrow engine armed.", color: "#00ff41", delay: 60 },
        { text: "[WARN] Mainnet launch: IMMINENT", color: "#ff6600", delay: 75 },
        { text: "[SYS] Welcome, Agent.", color: "#ff0040", delay: 90 },
      ].map((line, i) => (
        <div key={i} style={{ marginBottom: 4 }}>
          <TypeWriter
            text={line.text}
            frame={frame}
            startFrame={line.delay}
            color={line.color}
            fontSize={14}
            fontWeight={500}
          />
        </div>
      ))}
    </div>
  </AbsoluteFill>
);

const Scene2_Hero = ({ frame }) => {
  const localFrame = frame;
  return (
    <AbsoluteFill style={{ ...bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <div style={dotGrid} />
      <GlowOrb color="#9945FF" size={600} top="-200px" left="50%" />
      <GlowOrb color="#14F195" size={400} top="300px" left="-100px" />
      
      <FadeIn frame={localFrame} startFrame={0} duration={20}>
        <div style={{ textAlign: "center", position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: 14, color: "#9945FF", fontWeight: 700, letterSpacing: 3, textTransform: "uppercase", marginBottom: 20 }}>
            @Web3__Youth presents
          </div>
          <div style={{ fontSize: 64, fontWeight: 900, color: "#fff", letterSpacing: -2, lineHeight: 1.1 }}>
            Agent<span style={{ color: "#9945FF" }}>Wallet</span>
          </div>
          <div style={{ fontSize: 64, fontWeight: 900, color: "#fff", letterSpacing: -2, lineHeight: 1.1 }}>
            Protocol
          </div>
        </div>
      </FadeIn>

      <FadeIn frame={localFrame} startFrame={25} duration={15}>
        <div style={{ fontSize: 20, color: "#94a3b8", marginTop: 24, textAlign: "center", position: "relative", zIndex: 1 }}>
          Autonomous wallet infrastructure for the agentic economy
        </div>
      </FadeIn>

      <FadeIn frame={localFrame} startFrame={45}>
        <div style={{ display: "flex", gap: 20, marginTop: 48, position: "relative", zIndex: 1 }}>
          <StatBox num="27" label="MCP Tools" accent="153,69,255" frame={localFrame} startFrame={50} fps={30} />
          <StatBox num="3" label="Chains" accent="20,241,149" frame={localFrame} startFrame={55} fps={30} />
          <StatBox num="100%" label="Trustless" accent="0,212,255" frame={localFrame} startFrame={60} fps={30} />
          <StatBox num="24/7" label="Autonomous" accent="255,107,53" frame={localFrame} startFrame={65} fps={30} />
        </div>
      </FadeIn>
    </AbsoluteFill>
  );
};

const Scene3_Architecture = ({ frame }) => {
  const localFrame = frame;
  return (
    <AbsoluteFill style={{ ...bg, display: "flex", flexDirection: "column", padding: 60 }}>
      <div style={dotGrid} />
      <GlowOrb color="#9945FF" size={500} top="-100px" left="70%" />

      <div style={{ position: "relative", zIndex: 1 }}>
        <FadeIn frame={localFrame} startFrame={0}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 40 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#9945FF" }}>@Web3__Youth</div>
            <div style={{ fontSize: 11, color: "#64748b", background: "rgba(153,69,255,0.08)", border: "1px solid rgba(153,69,255,0.15)", padding: "5px 14px", borderRadius: 4, letterSpacing: 1 }}>
              AGENT PROTOCOL v2.0
            </div>
          </div>
        </FadeIn>

        <FadeIn frame={localFrame} startFrame={10}>
          <div style={{ fontSize: 36, fontWeight: 800, color: "#fff", letterSpacing: -1, marginBottom: 8 }}>
            How <span style={{ color: "#9945FF" }}>AgentWallet</span> works
          </div>
          <div style={{ fontSize: 16, color: "#64748b", marginBottom: 48 }}>
            End-to-end autonomous wallet infrastructure on Solana
          </div>
        </FadeIn>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 0 }}>
          <ArchNode label="Agent" name="AI Agent" desc="Claude / GPT / Gemini" accent="0,212,255" frame={localFrame} startFrame={20} fps={30} />
          <Arrow frame={localFrame} startFrame={28} />
          <ArchNode label="Protocol" name="AgentWallet" desc="MCP · Escrow · x402" accent="153,69,255" frame={localFrame} startFrame={30} fps={30} />
          <Arrow frame={localFrame} startFrame={38} />
          <ArchNode label="Chain" name="Solana" desc="PDA · SOL · USDC" accent="20,241,149" frame={localFrame} startFrame={40} fps={30} />
          <Arrow frame={localFrame} startFrame={48} />
          <ArchNode label="Commerce" name="A2A Market" desc="Jobs · Reputation" accent="255,107,53" frame={localFrame} startFrame={50} fps={30} />
        </div>

        <FadeIn frame={localFrame} startFrame={60}>
          <div style={{ display: "flex", justifyContent: "center", gap: 40, marginTop: 48 }}>
            {["Solana", "MCP", "x402", "PDA", "SPL", "USDC"].map((tag) => (
              <div
                key={tag}
                style={{
                  fontSize: 11,
                  color: "#64748b",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  padding: "4px 14px",
                  borderRadius: 4,
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                {tag}
              </div>
            ))}
          </div>
        </FadeIn>
      </div>
    </AbsoluteFill>
  );
};

const Scene4_Features = ({ frame }) => {
  const features = [
    { icon: "🔐", name: "PDA Vaults", desc: "No private keys. Deterministic agent wallets." },
    { icon: "💰", name: "Stablecoins", desc: "USDC + USDT native transfers." },
    { icon: "🤝", name: "Escrow", desc: "Trustless agent-to-agent payments." },
    { icon: "⚡", name: "x402", desc: "HTTP-native micropayments." },
    { icon: "📊", name: "Policies", desc: "Spending limits & allowlists." },
    { icon: "🏪", name: "Marketplace", desc: "Agent discovery + job matching." },
  ];

  return (
    <AbsoluteFill style={{ ...bg, display: "flex", flexDirection: "column", padding: 60 }}>
      <div style={dotGrid} />
      <GlowOrb color="#14F195" size={500} top="-100px" left="60%" />

      <div style={{ position: "relative", zIndex: 1 }}>
        <FadeIn frame={frame} startFrame={0}>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#14F195", marginBottom: 8 }}>@Web3__Youth</div>
          <div style={{ fontSize: 36, fontWeight: 800, color: "#fff", letterSpacing: -1, marginBottom: 48 }}>
            27 tools. <span style={{ color: "#14F195" }}>One SDK.</span> Zero friction.
          </div>
        </FadeIn>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
          {features.map((f, i) => (
            <FadeIn key={i} frame={frame} startFrame={15 + i * 8}>
              <div
                style={{
                  background: "rgba(20,241,149,0.04)",
                  border: "1px solid rgba(20,241,149,0.15)",
                  borderRadius: 12,
                  padding: "24px",
                }}
              >
                <div style={{ fontSize: 28, marginBottom: 8 }}>{f.icon}</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: "#e2e8f0", marginBottom: 6 }}>{f.name}</div>
                <div style={{ fontSize: 14, color: "#64748b", lineHeight: 1.5 }}>{f.desc}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Scene5_CTA = ({ frame }) => {
  const pulse = Math.sin(frame * 0.1) * 0.15 + 1;
  return (
    <AbsoluteFill style={{ ...bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <div style={dotGrid} />
      <GlowOrb color="#9945FF" size={600} top="-100px" left="40%" />
      <GlowOrb color="#14F195" size={400} top="250px" left="60%" />

      <div style={{ position: "relative", zIndex: 1, textAlign: "center" }}>
        <FadeIn frame={frame} startFrame={0}>
          <div style={{ fontSize: 14, color: "#9945FF", fontWeight: 700, letterSpacing: 3, textTransform: "uppercase", marginBottom: 20 }}>
            Beta Whitelist Open
          </div>
        </FadeIn>

        <FadeIn frame={frame} startFrame={10}>
          <div style={{ fontSize: 56, fontWeight: 900, color: "#fff", letterSpacing: -2, marginBottom: 16 }}>
            agent<span style={{ color: "#9945FF" }}>wallet</span>.fun
          </div>
        </FadeIn>

        <FadeIn frame={frame} startFrame={25}>
          <div style={{ fontSize: 20, color: "#94a3b8", marginBottom: 40, maxWidth: 500 }}>
            First 500 agents get $AW airdrop rewards on mainnet
          </div>
        </FadeIn>

        <FadeIn frame={frame} startFrame={35}>
          <div
            style={{
              display: "inline-block",
              transform: `scale(${pulse})`,
              background: "rgba(153,69,255,0.15)",
              border: "2px solid rgba(153,69,255,0.4)",
              borderRadius: 12,
              padding: "16px 48px",
              fontSize: 18,
              fontWeight: 700,
              color: "#9945FF",
              letterSpacing: 2,
            }}
          >
            JOIN THE BETA →
          </div>
        </FadeIn>

        <FadeIn frame={frame} startFrame={50}>
          <div style={{ display: "flex", gap: 24, marginTop: 40, justifyContent: "center" }}>
            <div style={{ fontSize: 13, color: "#64748b" }}>pip install agentwallet-mcp</div>
            <div style={{ fontSize: 13, color: "#64748b" }}>|</div>
            <div style={{ fontSize: 13, color: "#64748b" }}>github.com/YouthAIAgent/agentwallet</div>
          </div>
        </FadeIn>

        <FadeIn frame={frame} startFrame={60}>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#9945FF", marginTop: 32 }}>
            @Web3__Youth · ◎ Solana
          </div>
        </FadeIn>
      </div>
    </AbsoluteFill>
  );
};

// ── MAIN COMPOSITION ──
export const AgentWalletPromo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
      
      <Sequence from={0} durationInFrames={120}>
        <Scene1_Boot frame={frame} />
      </Sequence>

      <Sequence from={120} durationInFrames={90}>
        <Scene2_Hero frame={frame - 120} />
      </Sequence>

      <Sequence from={210} durationInFrames={90}>
        <Scene3_Architecture frame={frame - 210} />
      </Sequence>

      <Sequence from={300} durationInFrames={75}>
        <Scene4_Features frame={frame - 300} />
      </Sequence>

      <Sequence from={375} durationInFrames={75}>
        <Scene5_CTA frame={frame - 375} />
      </Sequence>
    </AbsoluteFill>
  );
};
