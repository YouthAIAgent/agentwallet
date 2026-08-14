import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
} from "remotion";

import { VoiceTrack } from "./Voice";

// bundled asset imports (reliable across renders)
import shotLanding from "../public/shots/01-landing.png";
import shotLogin from "../public/shots/02-login.png";
import shotDashboard from "../public/shots/03-dashboard.png";
import shotAgents from "../public/shots/04-agents.png";
import shotWallets from "../public/shots/05-wallets.png";
import shotAnalytics from "../public/shots/07-analytics.png";
import shotBilling from "../public/shots/10-billing.png";
import shotLight from "../public/shots/12-dashboard-light.png";

// ---------- design tokens (local.ai aesthetic) ----------
export const INK_950 = "#0f0e0c";
export const INK_900 = "#161513";
export const INK_800 = "#22201e";
export const INK_100 = "#efeeeb";
export const MUTED = "#8a867e";
export const DIM = "#6b675f";
export const GREEN = "#00bb7f";
export const GREEN_L = "#4ddcac";
export const FONT = "Consolas, 'Courier New', monospace";

export const GRID: React.CSSProperties = {
  backgroundImage:
    "linear-gradient(rgba(239,238,235,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(239,238,235,0.03) 1px, transparent 1px)",
  backgroundSize: "44px 44px",
};

export const MONO = { fontFamily: FONT } as React.CSSProperties;

// ---------- helpers ----------
export function Hex({ size = 120 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
      <path
        d="M20 2.5 L34.9 11.25 V28.75 L20 37.5 L5.1 28.75 V11.25 Z"
        fill={GREEN}
        fillOpacity="0.07"
        stroke={GREEN}
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      <path
        d="M13.5 15 L20 20 L13.5 25"
        stroke={GREEN}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M20.5 25.5 H26.5" stroke={GREEN} strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function Fade({
  children,
  start,
  dur,
  from = 0,
}: {
  children: React.ReactNode;
  start: number;
  dur: number;
  from?: number;
}) {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [start, start + 12, start + dur - 12, start + dur],
    [from, 1, 1, from],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
}

export function Shot({
  src,
  scaleFrom = 1.04,
  scaleTo = 1.16,
}: {
  src: string;
  scaleFrom?: number;
  scaleTo?: number;
}) {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 300], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(p, [0, 1], [scaleFrom, scaleTo]);
  const y = interpolate(p, [0, 1], [0, -24]);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <Img
        src={src}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale}) translateY(${y}px)` }}
      />
      {/* vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55) 100%)",
        }}
      />
    </AbsoluteFill>
  );
}

export function Title({
  text,
  color = INK_100,
  size = 64,
  start = 0,
  x = 0,
  y = 0,
  align = "left",
  weight = 700,
  tracking = 0,
}: {
  text: React.ReactNode;
  color?: string;
  size?: number;
  start?: number;
  x?: number;
  y?: number;
  align?: "left" | "center" | "right";
  weight?: number;
  tracking?: number;
}) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: x,
        top: y,
        color,
        fontSize: size,
        fontWeight: weight,
        letterSpacing: tracking,
        textAlign: align,
        opacity: s,
        transform: `translateY(${interpolate(s, [0, 1], [44, 0])}px)`,
        whiteSpace: "pre-wrap",
      }}
    >
      {text}
    </div>
  );
}

export function Chip({
  text,
  x,
  y,
  start = 0,
  color = GREEN,
  bg = "rgba(0,187,127,0.08)",
  border = "rgba(0,187,127,0.35)",
}: {
  text: string;
  x: number;
  y: number;
  start?: number;
  color?: string;
  bg?: string;
  border?: string;
}) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: x,
        top: y,
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 20px",
        borderRadius: 999,
        background: bg,
        border: `1px solid ${border}`,
        color,
        fontSize: 26,
        opacity: s,
        transform: `translateX(${interpolate(s, [0, 1], [-30, 0])}px)`,
      }}
    >
      <span
        style={{ width: 12, height: 12, borderRadius: 999, background: color }}
      />
      {text}
    </div>
  );
}

export function Bar({
  kicker,
  title,
  sub,
  start = 0,
}: {
  kicker: string;
  title: string;
  sub?: string;
  start?: number;
}) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: 80,
        bottom: 84,
        opacity: s,
        transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)`,
      }}
    >
      <div style={{ color: GREEN, fontSize: 26, letterSpacing: 6, textTransform: "uppercase" }}>
        {kicker}
      </div>
      <div style={{ color: INK_100, fontSize: 52, fontWeight: 700, marginTop: 8 }}>
        {title}
      </div>
      {sub && (
        <div style={{ color: MUTED, fontSize: 26, marginTop: 10, letterSpacing: 2 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

// ---------- scene 1: intro ----------
function Intro() {
  const frame = useCurrentFrame();
  const inS = spring({ frame, fps: 30, config: { damping: 200 } });
  const typeP = interpolate(frame, [25, 95], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ background: INK_950 }}>
      <AbsoluteFill style={GRID} />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 60% 45% at 50% 38%, rgba(0,187,127,0.14), transparent 70%)",
        }}
      />
      <AbsoluteFill
        style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
      >
        <div
          style={{
            opacity: inS,
            transform: `scale(${interpolate(inS, [0, 1], [0.6, 1])})`,
          }}
        >
          <Hex size={170} />
        </div>
        <div style={{ ...MONO, color: INK_100, fontSize: 110, fontWeight: 700, marginTop: 46 }}>
          agent<span style={{ color: GREEN }}>wallet</span>
        </div>
        <div
          style={{
            ...MONO,
            color: MUTED,
            fontSize: 30,
            letterSpacing: 18,
            marginTop: 30,
            opacity: typeP,
          }}
        >
          THE PAYMENT RAIL FOR THE AGENT ECONOMY
        </div>
        <div style={{ display: "flex", gap: 22, marginTop: 56, opacity: typeP }}>
          {["ESCROW", "X402", "USDC", "SWARMS"].map((t) => (
            <div
              key={t}
              style={{
                ...MONO,
                color: GREEN_L,
                fontSize: 24,
                letterSpacing: 4,
                padding: "10px 22px",
                border: `1px solid ${INK_800}`,
                borderRadius: 6,
              }}
            >
              ● {t}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}

// ---------- screenshot scenes ----------
function ShotScene({
  src,
  kicker,
  title,
  sub,
  chips = [],
}: {
  src: string;
  kicker: string;
  title: string;
  sub?: string;
  chips?: { text: string; x: number; y: number; start?: number }[];
}) {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: INK_950 }}>
      <Shot src={src} />
      <AbsoluteFill
        style={{
          background: "linear-gradient(to top, rgba(15,14,12,0.82) 0%, transparent 32%)",
        }}
      />
      {chips.map((c) => (
        <Chip key={c.text} text={c.text} x={c.x} y={c.y} start={c.start ?? 30} />
      ))}
      <Bar kicker={kicker} title={title} sub={sub} start={30} />
    </AbsoluteFill>
  );
}

// ---------- feature grid scene ----------
const FEATURES = [
  { icon: "⇄", title: "Agent Wallets", desc: "PDA custody · spend limits" },
  { icon: "⬡", title: "On-chain Escrow", desc: "create · fund · release" },
  { icon: "⚡", title: "x402 Pay-per-use", desc: "pay per API call" },
  { icon: "₹", title: "USDC Billing", desc: "subscribe · renew · cancel" },
];

function FeatureGrid() {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: INK_950, padding: 110 }}>
      <AbsoluteFill style={GRID} />
      <Title
        text={<>Everything agents need<br />to <span style={{ color: GREEN }}>move money.</span></>}
        size={76}
        x={110}
        y={90}
        start={10}
      />
      <div
        style={{
          position: "absolute",
          left: 110,
          right: 110,
          top: 360,
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 34,
        }}
      >
        {FEATURES.map((f, i) => {
          const s = spring({ frame: frame - (40 + i * 14), fps: 30, config: { damping: 200 } });
          return (
            <div
              key={f.title}
              style={{
                ...MONO,
                background: INK_900,
                border: `1px solid ${INK_800}`,
                borderRadius: 8,
                padding: "38px 40px",
                opacity: s,
                transform: `translateY(${interpolate(s, [0, 1], [50, 0])}px)`,
              }}
            >
              <div style={{ fontSize: 44, color: GREEN }}>{f.icon}</div>
              <div style={{ color: INK_100, fontSize: 40, fontWeight: 700, marginTop: 18 }}>
                {f.title}
              </div>
              <div style={{ color: MUTED, fontSize: 26, marginTop: 10, letterSpacing: 2 }}>
                {f.desc}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

// ---------- typing terminal scene ----------
const TERM_LINES = [
  "agentwallet escrow create --from agent --to vendor --amount 50 USDC",
  "✓ escrow_abc123 funded · 50 USDC locked",
  "agentwallet x402 pay --endpoint model.api --max 0.002 SOL",
  "✓ paid 0.002 SOL · receipt confirmed",
  "agentwallet subscribe --plan pro --usdc 49",
  "✓ subscribed · pro renews in 30d",
  "→ exit 0",
];
const TERM_STARTS = [0, 105, 150, 265, 310, 415, 490];
const TERM_SPEED = 3; // frames per char

function Terminal() {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: INK_950, padding: 110 }}>
      <AbsoluteFill style={GRID} />
      <Title text={<>The terminal.<br />Every flow.</>} size={76} x={110} y={80} start={5} />
      <div
        style={{
          position: "absolute",
          left: 110,
          right: 110,
          top: 330,
          background: INK_900,
          border: `1px solid ${INK_800}`,
          borderRadius: 10,
          overflow: "hidden",
          boxShadow: "0 40px 120px rgba(0,0,0,0.5)",
        }}
      >
        <div
          style={{
            ...MONO,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "20px 30px",
            borderBottom: `1px solid ${INK_800}`,
            background: INK_950,
          }}
        >
          <span style={{ color: MUTED, fontSize: 24, letterSpacing: 4 }}>AGENTWALLET.SH</span>
          <span style={{ display: "flex", gap: 12 }}>
            {[GREEN, "#f59e0b", "#ef4444"].map((c) => (
              <span key={c} style={{ width: 18, height: 18, borderRadius: 999, background: c }} />
            ))}
          </span>
        </div>
        <div style={{ padding: "30px 34px", minHeight: 470 }}>
          {TERM_LINES.map((line, i) => {
            const isCmd = !line.startsWith("✓") && !line.startsWith("→");
            const start = TERM_STARTS[i];
            const n = line.length;
            const done = frame - start >= n * TERM_SPEED;
            const chars = Math.floor(interpolate(frame, [start, start + n * TERM_SPEED], [0, n], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }));
            const visible = isCmd ? Math.min(chars, n) : done ? n : 0;
            if (frame < start && !done) return null;
            const color = line.startsWith("✓")
              ? GREEN
              : line.startsWith("→")
              ? MUTED
              : INK_100;
            return (
              <div key={i} style={{ ...MONO, color, fontSize: 34, marginBottom: 26, whiteSpace: "nowrap" }}>
                {isCmd && <span style={{ color: GREEN, marginRight: 14 }}>$</span>}
                {line.slice(0, visible)}
                {isCmd && !done && (
                  <span style={{ color: GREEN, opacity: frame % 30 < 15 ? 1 : 0 }}>▍</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
}

// ---------- outro ----------
function Outro() {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - 20, fps: 30, config: { damping: 200 } });
  return (
    <AbsoluteFill style={{ background: INK_950 }}>
      <AbsoluteFill style={GRID} />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 45%, rgba(0,187,127,0.16), transparent 70%)",
        }}
      />
      <AbsoluteFill
        style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
      >
        <div style={{ opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})` }}>
          <Hex size={150} />
        </div>
        <div style={{ ...MONO, color: INK_100, fontSize: 96, fontWeight: 700, marginTop: 40 }}>
          agent<span style={{ color: GREEN }}>wallet</span>
        </div>
        <div style={{ ...MONO, color: GREEN, fontSize: 32, letterSpacing: 8, marginTop: 30 }}>
          LAUNCH ON DEVNET — FREE
        </div>
        <div
          style={{
            ...MONO,
            color: MUTED,
            fontSize: 26,
            marginTop: 54,
            letterSpacing: 2,
            padding: "14px 30px",
            border: `1px solid ${INK_800}`,
            borderRadius: 8,
          }}
        >
          agentwallet-devnet-two.vercel.app
        </div>
        <div style={{ ...MONO, color: DIM, fontSize: 22, marginTop: 40, letterSpacing: 6 }}>
          BUILT FOR THE AGENT ECONOMY · SOLANA
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}

// ---------- captions (synced per scene) ----------
const CAPS: { text: string; start: number; dur: number }[] = [
  { text: "agentwallet — the payment rail for the agent economy", start: 20, dur: 90 },
  { text: "wallets · escrow · x402 · USDC · swarms", start: 120, dur: 110 },
  { text: "a public landing built to convert", start: 255, dur: 75 },
  { text: "hero · features · pricing · devnet CTA", start: 340, dur: 80 },
  { text: "launch dashboard → register in minutes", start: 430, dur: 90 },
  { text: "register in seconds", start: 555, dur: 75 },
  { text: "org → email → password → on-chain keys", start: 640, dur: 80 },
  { text: "your API token, issued on devnet", start: 730, dur: 90 },
  { text: "the dashboard — real data, live", start: 855, dur: 75 },
  { text: "agents create wallets. agents pay.", start: 940, dur: 110 },
  { text: "every spend visible, on-chain", start: 1060, dur: 120 },
  { text: "per-agent autonomy", start: 1215, dur: 75 },
  { text: "each agent gets its own wallet + policy", start: 1300, dur: 80 },
  { text: "pause · delete · audit — full control", start: 1390, dur: 90 },
  { text: "PDA custody", start: 1515, dur: 75 },
  { text: "treasury · escrow · agent wallets on Solana", start: 1600, dur: 80 },
  { text: "keys isolated, spend limited", start: 1690, dur: 90 },
  { text: "every move on-chain", start: 1815, dur: 75 },
  { text: "transactions · daily spend · audit trail", start: 1900, dur: 80 },
  { text: "built for compliance from day one", start: 1990, dur: 90 },
  { text: "USDC subscriptions", start: 2115, dur: 75 },
  { text: "free $0 · pro $49 · enterprise $299", start: 2200, dur: 120 },
  { text: "dark or light", start: 2355, dur: 75 },
  { text: "one toggle, the whole app re-themes", start: 2440, dur: 120 },
  { text: "everything agents need to move money", start: 2595, dur: 105 },
  { text: "escrow · x402 · USDC · swarms — all Solana programs", start: 2710, dur: 150 },
  { text: "the terminal. every flow.", start: 2895, dur: 75 },
  { text: "escrow funded · paid · subscribed — exit 0", start: 2980, dur: 180 },
  { text: "launch free on devnet", start: 3195, dur: 105 },
  { text: "agentwallet-devnet-two.vercel.app", start: 3310, dur: 90 },
  { text: "built for the agent economy · solana", start: 3410, dur: 170 },
];

function Caption({ text, start, dur }: { text: string; start: number; dur: number }) {
  const frame = useCurrentFrame();
  if (frame < start || frame > start + dur) return null;
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  const out = interpolate(frame, [start + dur - 12, start + dur], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 250,
        textAlign: "center",
        opacity: s * out,
        transform: `translateY(${interpolate(s, [0, 1], [20, 0])}px)`,
        zIndex: 10,
      }}
    >
      <span
        style={{
          fontSize: 40,
          fontWeight: 800,
          color: "#ffffff",
          textShadow:
            "0 2px 0 #000000, 0 4px 0 rgba(0,0,0,0.9), 0 6px 20px rgba(0,0,0,0.85)",
        }}
      >
        {text}
      </span>
    </div>
  );
}

// ---------- main composition ----------
export function Launch() {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: INK_950, fontFamily: FONT }}>
      <Sequence from={0} durationInFrames={240}>
        <Intro />
      </Sequence>

      <Sequence from={240} durationInFrames={300}>
        <Fade start={0} dur={300} from={0}>
          <ShotScene
            src={shotLanding}
            kicker="01 · public landing"
            title="Marketing that converts"
            sub="hero · features · pricing · devnet CTA"
            chips={[
              { text: "devnet · live", x: 1180, y: 160, start: 60 },
              { text: "terminal demo", x: 1380, y: 640, start: 110 },
            ]}
          />
        </Fade>
      </Sequence>

      <Sequence from={540} durationInFrames={300}>
        <Fade start={0} dur={300} from={0}>
          <ShotScene
            src={shotLogin}
            kicker="02 · auth"
            title="Register in seconds"
            sub="org → email → password → token"
          />
        </Fade>
      </Sequence>

      <Sequence from={840} durationInFrames={360}>
        <Fade start={0} dur={360} from={0}>
          <ShotScene
            src={shotDashboard}
            kicker="03 · dashboard"
            title="Real data, live"
            sub="agents · wallets · spend · analytics"
            chips={[
              { text: "AGENTS 2", x: 120, y: 220, start: 40 },
              { text: "WALLETS 3", x: 120, y: 320, start: 70 },
              { text: "$0.00 SPEND", x: 120, y: 420, start: 100 },
            ]}
          />
        </Fade>
      </Sequence>

      <Sequence from={1200} durationInFrames={300}>
        <Fade start={0} dur={300} from={0}>
          <ShotScene
            src={shotAgents}
            kicker="04 · agents"
            title="Per-agent autonomy"
            sub="each agent gets its own wallet + policy"
          />
        </Fade>
      </Sequence>

      <Sequence from={1500} durationInFrames={300}>
        <Fade start={0} dur={300} from={0}>
          <ShotScene
            src={shotWallets}
            kicker="05 · wallets"
            title="PDA custody"
            sub="treasury · escrow · agent wallets on Solana"
          />
        </Fade>
      </Sequence>

      <Sequence from={1800} durationInFrames={300}>
        <Fade start={0} dur={300} from={0}>
          <ShotScene
            src={shotAnalytics}
            kicker="06 · analytics"
            title="Every move on-chain"
            sub="transactions · daily spend · audit trail"
          />
        </Fade>
      </Sequence>

      <Sequence from={2100} durationInFrames={240}>
        <Fade start={0} dur={240} from={0}>
          <ShotScene
            src={shotBilling}
            kicker="07 · billing"
            title="USDC subscriptions"
            sub="free $0 · pro $49 · enterprise $299"
          />
        </Fade>
      </Sequence>

      <Sequence from={2340} durationInFrames={240}>
        <Fade start={0} dur={240} from={0}>
          <ShotScene
            src={shotLight}
            kicker="08 · theming"
            title="Dark or light"
            sub="one toggle, whole app re-themes"
          />
        </Fade>
      </Sequence>

      <Sequence from={2580} durationInFrames={300}>
        <Fade start={0} dur={300} from={0}>
          <FeatureGrid />
        </Fade>
      </Sequence>

      <Sequence from={2880} durationInFrames={300}>
        <Fade start={0} dur={300} from={0}>
          <Terminal />
        </Fade>
      </Sequence>

      <Sequence from={3180} durationInFrames={420}>
        <Fade start={0} dur={420} from={0}>
          <Outro />
        </Fade>
      </Sequence>
      {CAPS.map((c) => (
        <Caption key={c.start} text={c.text} start={c.start} dur={c.dur} />
      ))}
      <VoiceTrack />
    </AbsoluteFill>
  );
}
export default Launch;
