import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
} from "remotion";
import {
  FONT,
  GRID,
  GREEN,
  GREEN_L,
  INK_100,
  INK_800,
  INK_900,
  INK_950,
  MUTED,
  Hex,
  Fade,
} from "./Launch";

// vertical screenshots (1080x1920)
import vLanding from "../public/shots-v/v-landing.png";
import vLogin from "../public/shots-v/v-login.png";
import vDashboard from "../public/shots-v/v-dashboard.png";
import vAgents from "../public/shots-v/v-agents.png";
import vWallets from "../public/shots-v/v-wallets.png";
import vBilling from "../public/shots-v/v-billing.png";

const MONO = { fontFamily: FONT } as React.CSSProperties;

/** Big bold caption so shorts are watchable on mute. */
function Caption({
  text,
  start,
  dur,
}: {
  text: string;
  start: number;
  dur: number;
}) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  const out = interpolate(frame, [start + dur - 12, start + dur], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const visible = frame >= start && frame <= start + dur;
  if (!visible) return null;
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: 40,
        right: 40,
        bottom: 70,
        textAlign: "center",
        opacity: s * out,
        transform: `translateY(${interpolate(s, [0, 1], [24, 0])}px)`,
        zIndex: 10,
      }}
    >
      <span
        style={{
          fontSize: 44,
          fontWeight: 800,
          lineHeight: 1.25,
          color: "#ffffff",
          textShadow:
            "0 2px 0 #000000, 0 4px 0 rgba(0,0,0,0.9), 0 6px 18px rgba(0,0,0,0.85)",
        }}
      >
        {text}
      </span>
    </div>
  );
}

function VShot({ src }: { src: string }) {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 240], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(p, [0, 1], [1.04, 1.16]);
  return (
    <AbsoluteFill>
      <Img
        src={src}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})` }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.6) 100%)",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to top, rgba(15,14,12,0.9) 0%, transparent 30%)",
        }}
      />
    </AbsoluteFill>
  );
}

function VBottom({
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
        left: 60,
        right: 60,
        bottom: 130,
        textAlign: "center",
        opacity: s,
        transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)`,
      }}
    >
      <div style={{ color: GREEN, fontSize: 24, letterSpacing: 6, textTransform: "uppercase" }}>
        {kicker}
      </div>
      <div style={{ color: INK_100, fontSize: 56, fontWeight: 700, marginTop: 14 }}>
        {title}
      </div>
      {sub && (
        <div style={{ color: MUTED, fontSize: 26, marginTop: 12, letterSpacing: 2 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function VIntro({ compact = false }: { compact?: boolean }) {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps: 30, config: { damping: 200 } });
  return (
    <AbsoluteFill style={{ background: INK_950 }}>
      <AbsoluteFill style={GRID} />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 70% 40% at 50% 38%, rgba(0,187,127,0.16), transparent 70%)",
        }}
      />
      <AbsoluteFill
        style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
      >
        <div style={{ opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})` }}>
          <Hex size={compact ? 110 : 150} />
        </div>
        <div style={{ ...MONO, color: INK_100, fontSize: compact ? 66 : 88, fontWeight: 700, marginTop: 36 }}>
          agent<span style={{ color: GREEN }}>wallet</span>
        </div>
        <div style={{ ...MONO, color: MUTED, fontSize: 22, letterSpacing: 12, marginTop: 26, textAlign: "center" }}>
          THE PAYMENT RAIL FOR
          <br />
          THE AGENT ECONOMY
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}

function VFeatureStack() {
  const frame = useCurrentFrame();
  const items = [
    { k: "ESCROW", d: "create · fund · release" },
    { k: "X402", d: "pay per API call" },
    { k: "USDC", d: "subscribe · renew · cancel" },
    { k: "SWARMS", d: "multi-agent coordination" },
  ];
  return (
    <AbsoluteFill style={{ background: INK_950, padding: "120px 70px" }}>
      <AbsoluteFill style={GRID} />
      <div style={{ ...MONO, color: INK_100, fontSize: 52, fontWeight: 700, textAlign: "center", marginTop: 40 }}>
        Everything agents need
        <br />
        to <span style={{ color: GREEN }}>move money.</span>
      </div>
      <div style={{ marginTop: 90, display: "flex", flexDirection: "column", gap: 34 }}>
        {items.map((it, i) => {
          const s = spring({ frame: frame - (30 + i * 12), fps: 30, config: { damping: 200 } });
          return (
            <div
              key={it.k}
              style={{
                ...MONO,
                background: INK_900,
                border: `1px solid ${INK_800}`,
                borderRadius: 8,
                padding: "34px 40px",
                opacity: s,
                transform: `translateY(${interpolate(s, [0, 1], [50, 0])}px)`,
              }}
            >
              <div style={{ color: GREEN_L, fontSize: 30, letterSpacing: 4 }}>● {it.k}</div>
              <div style={{ color: MUTED, fontSize: 26, marginTop: 8, letterSpacing: 1 }}>{it.d}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

function VTerminal() {
  const frame = useCurrentFrame();
  const lines = [
    ["agentwallet escrow create --from agent --to vendor --amount 50 USDC", 0],
    ["✓ escrow_abc123 funded · 50 USDC locked", 110],
    ["agentwallet x402 pay --endpoint model.api", 170],
    ["✓ paid 0.002 SOL · receipt confirmed", 260],
    ["→ exit 0", 320],
  ];
  const SPEED = 3;
  return (
    <AbsoluteFill style={{ background: INK_950, padding: "110px 60px" }}>
      <AbsoluteFill style={GRID} />
      <div style={{ ...MONO, color: INK_100, fontSize: 52, fontWeight: 700, textAlign: "center" }}>
        The terminal. <span style={{ color: GREEN }}>Every flow.</span>
      </div>
      <div
        style={{
          ...MONO,
          marginTop: 70,
          background: INK_900,
          border: `1px solid ${INK_800}`,
          borderRadius: 10,
          padding: "34px 34px",
        }}
      >
        {lines.map(([text, start], i) => {
          const line = text as string;
          const startF = start as number;
          const n = line.length;
          const chars = Math.floor(
            interpolate(frame, [startF, startF + n * SPEED], [0, n], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          );
          const isCmd = !line.startsWith("✓") && !line.startsWith("→");
          const done = frame - startF >= n * SPEED;
          const visible = isCmd ? Math.min(chars, n) : done ? n : 0;
          if (frame < startF && !done) return null;
          const color = line.startsWith("✓")
            ? GREEN
            : line.startsWith("→")
            ? MUTED
            : INK_100;
          return (
            <div key={i} style={{ color, fontSize: 26, marginBottom: 24, whiteSpace: "nowrap" }}>
              {isCmd && <span style={{ color: GREEN, marginRight: 10 }}>$</span>}
              {line.slice(0, visible)}
              {isCmd && !done && (
                <span style={{ color: GREEN, opacity: frame % 30 < 15 ? 1 : 0 }}>▍</span>
              )}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

function VOutro({ compact = false }: { compact?: boolean }) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - 15, fps: 30, config: { damping: 200 } });
  return (
    <AbsoluteFill style={{ background: INK_950 }}>
      <AbsoluteFill style={GRID} />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 50% 45%, rgba(0,187,127,0.18), transparent 70%)",
        }}
      />
      <AbsoluteFill
        style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
      >
        <div style={{ opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})` }}>
          <Hex size={compact ? 100 : 130} />
        </div>
        <div style={{ ...MONO, color: INK_100, fontSize: compact ? 58 : 72, fontWeight: 700, marginTop: 30 }}>
          agent<span style={{ color: GREEN }}>wallet</span>
        </div>
        <div style={{ ...MONO, color: GREEN, fontSize: 26, letterSpacing: 6, marginTop: 24 }}>
          LAUNCH ON DEVNET — FREE
        </div>
        <div
          style={{
            ...MONO,
            color: MUTED,
            fontSize: 22,
            marginTop: 44,
            letterSpacing: 1,
            padding: "14px 28px",
            border: `1px solid ${INK_800}`,
            borderRadius: 8,
            textAlign: "center",
          }}
        >
          agentwallet-devnet-two.vercel.app
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}

// ---------- 15s short (450 frames) ----------
const C15: { text: string; start: number; dur: number }[] = [
  { text: "agentwallet — payments for the agent economy", start: 12, dur: 72 },
  { text: "real wallets · escrow · billing on Solana", start: 100, dur: 62 },
  { text: "agents create wallets. agents pay. on-chain.", start: 172, dur: 60 },
  { text: "escrow · x402 · usdc · swarms", start: 248, dur: 74 },
  { text: "launch free on devnet", start: 345, dur: 72 },
];

export function Short15() {
  return (
    <AbsoluteFill style={{ background: INK_950, fontFamily: FONT }}>
      <Sequence from={0} durationInFrames={90}>
        <VIntro compact />
      </Sequence>
      <Sequence from={90} durationInFrames={150}>
        <Fade start={0} dur={150}>
          <AbsoluteFill style={{ background: INK_950 }}>
            <VShot src={vDashboard} />
            <VBottom kicker="dashboard" title="Real data, live" sub="agents · wallets · spend · analytics" start={15} />
          </AbsoluteFill>
        </Fade>
      </Sequence>
      <Sequence from={240} durationInFrames={90}>
        <Fade start={0} dur={90}>
          <VFeatureStack />
        </Fade>
      </Sequence>
      <Sequence from={330} durationInFrames={120}>
        <Fade start={0} dur={120}>
          <VOutro compact />
        </Fade>
      </Sequence>
      {C15.map((c) => (
        <Caption key={c.start} text={c.text} start={c.start} dur={c.dur} />
      ))}
    </AbsoluteFill>
  );
}

// ---------- 30s short (900 frames) ----------
const C30: { text: string; start: number; dur: number }[] = [
  { text: "agentwallet — payments for the agent economy", start: 15, dur: 100 },
  { text: "the payment rail for the agent economy", start: 128, dur: 60 },
  { text: "wallets · escrow · pay-per-call billing", start: 198, dur: 48 },
  { text: "real data. live on devnet.", start: 262, dur: 70 },
  { text: "each agent gets its own wallet + policy", start: 345, dur: 68 },
  { text: "PDA custody — treasury · escrow · agents", start: 428, dur: 95 },
  { text: "the terminal. every flow.", start: 540, dur: 65 },
  { text: "escrow funded · paid · subscribed — exit 0", start: 612, dur: 72 },
  { text: "launch free on devnet →", start: 700, dur: 90 },
];

export function Short30() {
  return (
    <AbsoluteFill style={{ background: INK_950, fontFamily: FONT }}>
      <Sequence from={0} durationInFrames={120}>
        <VIntro />
      </Sequence>
      <Sequence from={120} durationInFrames={130}>
        <Fade start={0} dur={130}>
          <AbsoluteFill style={{ background: INK_950 }}>
            <VShot src={vLanding} />
            <VBottom kicker="public landing" title="Marketing that converts" sub="hero · pricing · devnet CTA" start={15} />
          </AbsoluteFill>
        </Fade>
      </Sequence>
      <Sequence from={250} durationInFrames={170}>
        <Fade start={0} dur={170}>
          <AbsoluteFill style={{ background: INK_950 }}>
            <VShot src={vDashboard} />
            <VBottom kicker="dashboard" title="Real data, live" sub="per-agent wallets · escrow · billing" start={15} />
          </AbsoluteFill>
        </Fade>
      </Sequence>
      <Sequence from={420} durationInFrames={110}>
        <Fade start={0} dur={110}>
          <AbsoluteFill style={{ background: INK_950 }}>
            <VShot src={vWallets} />
            <VBottom kicker="wallets" title="PDA custody" sub="treasury · escrow · agent wallets" start={12} />
          </AbsoluteFill>
        </Fade>
      </Sequence>
      <Sequence from={530} durationInFrames={160}>
        <Fade start={0} dur={160}>
          <VTerminal />
        </Fade>
      </Sequence>
      <Sequence from={690} durationInFrames={210}>
        <Fade start={0} dur={210}>
          <VOutro />
        </Fade>
      </Sequence>
      {C30.map((c) => (
        <Caption key={c.start} text={c.text} start={c.start} dur={c.dur} />
      ))}
    </AbsoluteFill>
  );
}
