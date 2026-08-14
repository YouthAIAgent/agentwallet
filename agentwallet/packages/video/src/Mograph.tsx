import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
} from "remotion";

import { VoiceMograph } from "./VoiceMograph";
import {
  DIM,
  FONT,
  GRID,
  GREEN,
  GREEN_L,
  Hex,
  INK_100,
  INK_800,
  INK_900,
  INK_950,
  MUTED,
} from "./Launch";

const MONO = { fontFamily: FONT } as React.CSSProperties;

// ============================================================
// shared background layers (full motion-graphics feel)
// ============================================================

function Orbs() {
  const frame = useCurrentFrame();
  const t = frame / 30;
  return (
    <>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 55% 42% at 50% 28%, rgba(0,187,127,0.13), transparent 70%)",
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle 420px at ${50 + 14 * Math.sin(t * 0.35)}% ${32 + 8 * Math.cos(t * 0.28)}%, rgba(0,187,127,0.10), transparent 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle 340px at ${78 + 10 * Math.cos(t * 0.22)}% ${68 + 10 * Math.sin(t * 0.3)}%, rgba(59,130,246,0.07), transparent 70%)`,
        }}
      />
    </>
  );
}

const PARTICLES = Array.from({ length: 44 }, (_, i) => ({
  x: (i * 97 + 11) % 100,
  y: (i * 53 + 7) % 100,
  size: 1.5 + (i % 3),
  speed: 0.25 + (i % 5) * 0.09,
  delay: (i * 13) % 120,
  green: i % 2 === 0,
}));

function Particles() {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      {PARTICLES.map((p, i) => {
        const y = (p.y + (frame + p.delay * 3) / 30 * p.speed * 6) % 100;
        const tw =
          0.25 + 0.75 * Math.abs(Math.sin((frame + p.delay * 4) / 30 * 2.2));
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${p.x}%`,
              top: `${y}%`,
              width: p.size,
              height: p.size,
              borderRadius: 999,
              background: p.green ? GREEN : GREEN_L,
              opacity: tw * 0.45,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
}

function Scanline() {
  const frame = useCurrentFrame();
  const y = ((frame % 300) / 300) * 1080;
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: y,
        height: 120,
        background:
          "linear-gradient(to bottom, transparent, rgba(0,187,127,0.05), transparent)",
        zIndex: 5,
      }}
    />
  );
}

function Base({ children }: { children: React.ReactNode }) {
  return (
    <AbsoluteFill style={{ background: INK_950 }}>
      <AbsoluteFill style={GRID} />
      <Orbs />
      <Particles />
      <Scanline />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.5) 100%)",
        }}
      />
      {children}
    </AbsoluteFill>
  );
}

/** Spring in from below. */
function Rise({
  children,
  start = 0,
  delay = 0,
  fromY = 46,
}: {
  children: React.ReactNode;
  start?: number;
  delay?: number;
  fromY?: number;
}) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start - delay, fps: 30, config: { damping: 200 } });
  return (
    <div
      style={{
        opacity: s,
        transform: `translateY(${interpolate(s, [0, 1], [fromY, 0])}px)`,
      }}
    >
      {children}
    </div>
  );
}

function H({ text, x, start = 0, size = 64 }: { text: React.ReactNode; x: number; start?: number; size?: number }) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: x,
        top: 110,
        color: INK_100,
        fontSize: size,
        fontWeight: 700,
        letterSpacing: 1,
        opacity: s,
        transform: `translateY(${interpolate(s, [0, 1], [30, 0])}px)`,
        whiteSpace: "pre",
      }}
    >
      {text}
    </div>
  );
}

function Kicker({ text, x, start = 0 }: { text: string; x: number; start?: number }) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: x,
        top: 66,
        color: GREEN,
        fontSize: 26,
        letterSpacing: 8,
        textTransform: "uppercase",
        opacity: s,
      }}
    >
      {text}
    </div>
  );
}

function Box({ x, y, w, h, label, accent = GREEN, start = 0 }: { x: number; y: number; w: number; h: number; label: string; accent?: string; start?: number }) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  const pulse = 0.5 + 0.5 * Math.sin(frame / 30 * 3);
  return (
    <div
      style={{
        ...MONO,
        position: "absolute",
        left: x,
        top: y,
        width: w,
        height: h,
        borderRadius: 12,
        background: INK_900,
        border: `1px solid ${accent}`,
        boxShadow: `0 0 ${30 + 20 * pulse}px rgba(0,187,127,0.18)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: s,
        transform: `scale(${interpolate(s, [0, 1], [0.8, 1])})`,
      }}
    >
      <div style={{ color: accent, fontSize: 34, letterSpacing: 4, fontWeight: 700 }}>{label}</div>
    </div>
  );
}

// ============================================================
// scene 1 — intro (0..150)
// ============================================================
function SIntro() {
  const frame = useCurrentFrame();
  const inS = spring({ frame, fps: 30, config: { damping: 200 } });
  const ringRot = interpolate(frame, [0, 70], [0, 360]);
  const ringO = interpolate(frame, [0, 55, 90], [0, 0.9, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const word = "agentwallet";
  return (
    <Base>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        {/* rotating dashed ring */}
        <div
          style={{
            position: "absolute",
            width: 380,
            height: 380,
            borderRadius: 999,
            border: "2px dashed rgba(0,187,127,0.5)",
            opacity: ringO,
            transform: `rotate(${ringRot}deg)`,
          }}
        />
        <div style={{ opacity: inS, transform: `scale(${interpolate(inS, [0, 1], [0.55, 1])}) rotate(${interpolate(inS, [0, 1], [-14, 0])}deg)` }}>
          <Hex size={190} />
        </div>
        <div style={{ display: "flex", marginTop: 52, fontSize: 118, fontWeight: 700 }}>
          {word.split("").map((ch, i) => {
            const s = spring({ frame: frame - 25 - i * 4, fps: 30, config: { damping: 200 } });
            const green = i >= 5;
            return (
              <span
                key={i}
                style={{
                  ...MONO,
                  color: green ? GREEN : INK_100,
                  opacity: s,
                  transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`,
                  display: "inline-block",
                }}
              >
                {ch}
              </span>
            );
          })}
        </div>
        <Rise start={55}>
          <div style={{ ...MONO, color: MUTED, fontSize: 30, letterSpacing: 20, marginTop: 34 }}>
            THE PAYMENT RAIL
          </div>
        </Rise>
      </AbsoluteFill>
    </Base>
  );
}

// ============================================================
// scene 2 — kinetic headline (150..330)
// ============================================================
function SHeadline() {
  const frame = useCurrentFrame();
  const l1 = "THE PAYMENT RAIL";
  const l2 = ["FOR THE ", "AGENT", " ECONOMY"];
  return (
    <Base>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", maxWidth: 1700 }}>
          {l1.split("").map((ch, i) => {
            const s = spring({ frame: frame - i * 3.2, fps: 30, config: { damping: 200 } });
            return (
              <span
                key={i}
                style={{
                  ...MONO,
                  color: INK_100,
                  fontSize: 108,
                  fontWeight: 800,
                  opacity: s,
                  transform: `translateY(${interpolate(s, [0, 1], [70, 0])}px) rotate(${interpolate(s, [0, 1], [6, 0])}deg)`,
                  display: "inline-block",
                }}
              >
                {ch === " " ? "\u00A0" : ch}
              </span>
            );
          })}
        </div>
        <div style={{ display: "flex", marginTop: 40 }}>
          {l2.map((seg, si) =>
            seg.split("").map((ch, ci) => {
              const i = ci + (si === 0 ? 0 : si === 1 ? 9 : 14);
              const s = spring({ frame: frame - 55 - i * 3.2, fps: 30, config: { damping: 200 } });
              return (
                <span
                  key={`${si}-${ci}`}
                  style={{
                    ...MONO,
                    color: si === 1 ? GREEN : MUTED,
                    fontSize: 64,
                    fontWeight: 700,
                    opacity: s,
                    transform: `translateX(${interpolate(s, [0, 1], [40, 0])}px)`,
                    display: "inline-block",
                  }}
                >
                  {ch === " " ? "\u00A0" : ch}
                </span>
              );
            })
          )}
        </div>
        {/* underline sweep */}
        <div
          style={{
            position: "absolute",
            bottom: 250,
            height: 6,
            borderRadius: 999,
            background: `linear-gradient(90deg, transparent, ${GREEN})`,
            width: interpolate(frame, [120, 210], [0, 620], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          }}
        />
      </AbsoluteFill>
    </Base>
  );
}

// ============================================================
// scene 3 — wallet (330..540)
// ============================================================
const ADDR = "7xKp3Zx9Qm4vR2Lt8sNw4Yq";
const COINS = [
  { x: 300, y: 250, d: 0 },
  { x: 420, y: 160, d: 8 },
  { x: 520, y: 220, d: 16 },
];

function SWallet() {
  const frame = useCurrentFrame();
  const pulse = 0.5 + 0.5 * Math.sin(frame / 30 * 2.4);
  const addrN = Math.floor(
    interpolate(frame, [80, 80 + ADDR.length * 2.5], [0, ADDR.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  return (
    <Base>
      <Kicker text="agent wallets" x={140} start={10} />
      <H text={<>Every agent gets its own <span style={{ color: GREEN }}>Solana wallet.</span></>} x={140} start={20} />
      <div
        style={{
          position: "absolute",
          left: 560,
          top: 320,
          width: 800,
          height: 470,
          borderRadius: 20,
          background: "linear-gradient(160deg, #171613, #100f0d)",
          border: `1px solid rgba(0,187,127,${0.35 + 0.35 * pulse})`,
          boxShadow: `0 50px 140px rgba(0,0,0,0.6), 0 0 ${40 + 30 * pulse}px rgba(0,187,127,0.16)`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "34px 40px", borderBottom: `1px solid ${INK_800}` }}>
          <div style={{ ...MONO, color: GREEN_L, fontSize: 30, letterSpacing: 6 }}>AGENT WALLET</div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <span style={{ ...MONO, color: MUTED, fontSize: 22 }}>PDA</span>
            <Hex size={34} />
          </div>
        </div>
        <div style={{ padding: "36px 40px" }}>
          <div style={{ ...MONO, color: DIM, fontSize: 22, letterSpacing: 2 }}>ADDRESS</div>
          <div style={{ ...MONO, color: INK_100, fontSize: 34, marginTop: 10 }}>
            {ADDR.slice(0, addrN)}
            <span style={{ color: GREEN, opacity: frame % 30 < 15 ? 1 : 0 }}>▍</span>
          </div>
          <div style={{ ...MONO, color: DIM, fontSize: 22, letterSpacing: 2, marginTop: 42 }}>BALANCE</div>
          <div style={{ ...MONO, color: INK_100, fontSize: 78, fontWeight: 800, marginTop: 6 }}>
            $
            {Math.floor(interpolate(frame, [110, 190], [0, 1250], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            }))
              .toLocaleString("en-US")}
            .42 <span style={{ color: GREEN, fontSize: 44, fontWeight: 700 }}>SOL</span>
          </div>
        </div>
      </div>
      {/* falling coins */}
      {COINS.map((c, i) => {
        const s = spring({ frame: frame - 40 - c.d, fps: 30, config: { damping: 12 } });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 560 + c.x,
              top: 280 + c.y + interpolate(s, [0, 1], [-80, 0]),
              width: 34,
              height: 34,
              borderRadius: 999,
              background: GREEN,
              boxShadow: "0 0 26px rgba(0,187,127,0.85)",
              opacity: s,
            }}
          />
        );
      })}
      {/* chips */}
      {[
        { t: "ISOLATED", x: 320, y: 620, d: 90 },
        { t: "ON-CHAIN", x: 560, y: 680, d: 105 },
        { t: "PROGRAM-OWNED", x: 1120, y: 600, d: 120 },
      ].map((c) => (
        <Rise key={c.t} start={330} delay={c.d - 330}>
          <div
            style={{
              ...MONO,
              position: "absolute",
              left: c.x,
              top: c.y,
              color: GREEN_L,
              fontSize: 26,
              letterSpacing: 4,
              padding: "12px 24px",
              border: `1px solid rgba(0,187,127,0.4)`,
              borderRadius: 999,
              background: "rgba(0,187,127,0.07)",
            }}
          >
            {c.t}
          </div>
        </Rise>
      ))}
    </Base>
  );
}

// ============================================================
// scene 4 — escrow (540..750)
// ============================================================
function SEscrow() {
  const frame = useCurrentFrame();
  const funded = spring({ frame: frame - 70, fps: 30, config: { damping: 200 } });
  const released = spring({ frame: frame - 130, fps: 30, config: { damping: 200 } });
  const coins = [0, 14, 28, 42];
  return (
    <Base>
      <Kicker text="on-chain escrow" x={140} start={10} />
      <H text={<>Real <span style={{ color: GREEN }}>guarantees.</span> No middleman.</>} x={140} start={20} />
      <Box x={200} y={430} w={420} h={240} label="AGENT" start={30} />
      <Box x={1300} y={430} w={420} h={240} label="VENDOR" start={30} />
      {/* escrow badge center */}
      <div
        style={{
          position: "absolute",
          left: 810,
          top: 490,
          width: 300,
          height: 120,
          borderRadius: 999,
          background: INK_900,
          border: "1px solid rgba(0,187,127,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 14,
        }}
      >
        <span style={{ ...MONO, color: GREEN, fontSize: 40 }}>⬡</span>
        <span style={{ ...MONO, color: INK_100, fontSize: 30, letterSpacing: 3 }}>ESCROW</span>
      </div>
      {/* flying coins agent -> vendor */}
      {coins.map((d) => {
        const p = interpolate(frame, [60 + d, 130 + d], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.inOut(Easing.cubic),
        });
        if (p <= 0 || p >= 1) return null;
        return (
          <div
            key={d}
            style={{
              position: "absolute",
              left: 640 + (1280 - 640) * p,
              top: 540 - Math.sin(p * Math.PI) * 150,
              width: 26,
              height: 26,
              borderRadius: 999,
              background: GREEN,
              boxShadow: "0 0 26px rgba(0,187,127,0.9)",
            }}
          />
        );
      })}
      {/* status */}
      <div style={{ position: "absolute", left: 830, top: 660 }}>
        <Rise start={540} delay={70}>
          <div style={{ ...MONO, color: GREEN, fontSize: 34, letterSpacing: 3, opacity: funded }}>
            ✓ FUNDED · 50 USDC LOCKED
          </div>
        </Rise>
        <Rise start={540} delay={130}>
          <div style={{ ...MONO, color: GREEN_L, fontSize: 34, letterSpacing: 3, opacity: released, marginTop: 14 }}>
            ✓ RELEASED · ON DELIVERY
          </div>
        </Rise>
      </div>
    </Base>
  );
}

// ============================================================
// scene 5 — x402 pay-per-call (750..960)
// ============================================================
function SX402() {
  const frame = useCurrentFrame();
  const pulses = [0, 22, 44, 66, 88];
  const receiptN = Math.floor(
    interpolate(frame, [150, 150 + 26 * 2.5], [0, 26], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  return (
    <Base>
      <Kicker text="x402 pay-per-call" x={140} start={10} />
      <H text={<>Pay per <span style={{ color: GREEN }}>API call.</span> One signature.</>} x={140} start={20} />
      {/* request chip */}
      <div
        style={{
          position: "absolute",
          left: 260,
          top: 470,
          width: 300,
          height: 130,
          borderRadius: 14,
          background: INK_900,
          border: `1px solid ${INK_800}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ ...MONO, color: INK_100, fontSize: 30, letterSpacing: 3 }}>REQUEST</div>
      </div>
      {/* model node with pulsing rings */}
      <div style={{ position: "absolute", left: 1470, top: 400 }}>
        {pulses.map((d) => {
          const p = (frame + d * 2) % 80;
          return (
            <div
              key={d}
              style={{
                position: "absolute",
                left: 90 - p * 1.4,
                top: 90 - p * 1.4,
                width: 140 + p * 2.8,
                height: 140 + p * 2.8,
                borderRadius: 999,
                border: "1px solid rgba(0,187,127,0.35)",
                opacity: 1 - p / 80,
              }}
            />
          );
        })}
        <div
          style={{
            width: 180,
            height: 180,
            borderRadius: 999,
            background: "radial-gradient(circle, rgba(0,187,127,0.22), rgba(0,187,127,0.05))",
            border: "1px solid rgba(0,187,127,0.6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div style={{ ...MONO, color: GREEN_L, fontSize: 28, letterSpacing: 2 }}>MODEL</div>
        </div>
      </div>
      {/* path + coins */}
      <div
        style={{
          position: "absolute",
          left: 580,
          top: 520,
          width: 860,
          height: 4,
          background: `linear-gradient(90deg, transparent, ${GREEN} 20%, ${GREEN} 80%, transparent)`,
          transform: "rotate(-3deg)",
        }}
      />
      {[0, 26, 52].map((d) => {
        const p = interpolate(frame, [40 + d, 120 + d], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.inOut(Easing.cubic),
        });
        if (p <= 0 || p >= 1) return null;
        return (
          <div
            key={d}
            style={{
              position: "absolute",
              left: 600 + 800 * p,
              top: 520 - Math.sin(p * Math.PI) * 60 - 2,
              width: 24,
              height: 24,
              borderRadius: 999,
              background: GREEN,
              boxShadow: "0 0 24px rgba(0,187,127,0.9)",
            }}
          />
        );
      })}
      {/* receipt */}
      <div
        style={{
          position: "absolute",
          left: 560,
          top: 660,
          ...MONO,
          color: GREEN,
          fontSize: 32,
          letterSpacing: 2,
        }}
      >
        ✓ PAID · 0.002 SOL · sig{" "}
        {"9f3a".slice(0, Math.max(0, Math.min(4, receiptN)))}
        {receiptN > 4 ? "8c2d…" : ""}
        <span style={{ opacity: frame % 30 < 15 ? 1 : 0 }}>▍</span>
      </div>
    </Base>
  );
}

// ============================================================
// scene 6 — USDC subscriptions (960..1170)
// ============================================================
function SUsdc() {
  const frame = useCurrentFrame();
  const active = spring({ frame: frame - 90, fps: 30, config: { damping: 200 } });
  const barW = interpolate(frame, [120, 210], [620, 60], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });
  const ringRot = interpolate(frame, [0, 150], [0, 360]);
  return (
    <Base>
      <Kicker text="usdc subscriptions" x={140} start={10} />
      <H text={<>No Stripe. No intermediaries. <span style={{ color: GREEN }}>On-chain billing.</span></>} x={140} start={20} size={60} />
      {/* plan card */}
      <div
        style={{
          position: "absolute",
          left: 610,
          top: 340,
          width: 700,
          height: 380,
          borderRadius: 20,
          background: "linear-gradient(160deg, #171613, #100f0d)",
          border: `1px solid rgba(0,187,127,0.4)`,
          boxShadow: "0 50px 140px rgba(0,0,0,0.6)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* USDC coin */}
        <div style={{ position: "relative", width: 96, height: 96 }}>
          <div
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: 999,
              border: "2px dashed rgba(0,187,127,0.6)",
              transform: `rotate(${ringRot}deg)`,
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 10,
              borderRadius: 999,
              background: "radial-gradient(circle at 35% 30%, rgba(0,187,127,0.9), rgba(0,120,90,0.9))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span style={{ ...MONO, color: "#04140e", fontSize: 44, fontWeight: 800 }}>$</span>
          </div>
        </div>
        <div style={{ ...MONO, color: INK_100, fontSize: 60, fontWeight: 800, marginTop: 26 }}>
          PRO <span style={{ color: GREEN, fontSize: 40 }}>· $49 / mo</span>
        </div>
        <div
          style={{
            ...MONO,
            color: GREEN_L,
            fontSize: 26,
            letterSpacing: 4,
            marginTop: 24,
            padding: "10px 26px",
            borderRadius: 999,
            border: `1px solid ${active ? "rgba(0,187,127,0.7)" : INK_800}`,
            background: active ? "rgba(0,187,127,0.12)" : "transparent",
            opacity: active ? 1 : 0.7 + 0.3 * Math.abs(Math.sin(frame / 30 * 3)),
          }}
        >
          {active ? "✓ ACTIVE · RENEWS IN 30d" : "SUBSCRIBE · USDC"}
        </div>
      </div>
      {/* countdown bar */}
      <Rise start={960} delay={120}>
        <div style={{ position: "absolute", left: 640, top: 780, width: 640 }}>
          <div style={{ ...MONO, color: DIM, fontSize: 22, letterSpacing: 3, marginBottom: 12 }}>BILLING CYCLE</div>
          <div style={{ height: 8, borderRadius: 999, background: INK_800, overflow: "hidden" }}>
            <div style={{ height: 8, width: barW, borderRadius: 999, background: `linear-gradient(90deg, ${GREEN}, ${GREEN_L})` }} />
          </div>
        </div>
      </Rise>
      {/* cancel chip */}
      <Rise start={960} delay={150}>
        <div
          style={{
            position: "absolute",
            left: 1420,
            top: 560,
            ...MONO,
            color: MUTED,
            fontSize: 24,
            letterSpacing: 3,
            padding: "10px 22px",
            border: `1px solid ${INK_800}`,
            borderRadius: 999,
          }}
        >
          CANCEL · ANYTIME
        </div>
      </Rise>
    </Base>
  );
}

// ============================================================
// scene 7 — agent swarms (1170..1380)
// ============================================================
const SATELLITES = [
  { label: "WORKER-01", ang: -90, d: 0 },
  { label: "WORKER-02", ang: -18, d: 8 },
  { label: "WORKER-03", ang: 54, d: 16 },
  { label: "WORKER-04", ang: 126, d: 24 },
  { label: "WORKER-05", ang: 198, d: 32 },
];

function SSwarms() {
  const frame = useCurrentFrame();
  const cx = 960;
  const cy = 560;
  const R = 330;
  return (
    <Base>
      <Kicker text="agent swarms" x={140} start={10} />
      <H text={<>Swarms, <span style={{ color: GREEN }}>coordinating</span> payments.</>} x={140} start={20} />
      {/* orbit ring */}
      <div
        style={{
          position: "absolute",
          left: cx - R - 40,
          top: cy - R - 40,
          width: (R + 40) * 2,
          height: (R + 40) * 2,
          borderRadius: 999,
          border: "1px dashed rgba(0,187,127,0.2)",
        }}
      />
      {/* center node */}
      <div
        style={{
          position: "absolute",
          left: cx - 90,
          top: cy - 90,
          width: 180,
          height: 180,
          borderRadius: 999,
          background: "radial-gradient(circle, rgba(0,187,127,0.25), rgba(0,187,127,0.05))",
          border: "1px solid rgba(0,187,127,0.65)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 60px rgba(0,187,127,0.3)",
        }}
      >
        <div style={{ ...MONO, color: GREEN_L, fontSize: 24, letterSpacing: 2, textAlign: "center" }}>
          ORCH-
          <br />
          ESTRATOR
        </div>
      </div>
      {/* satellites + lines + pulses */}
      {SATELLITES.map((s) => {
        const rad = (s.ang * Math.PI) / 180;
        const x = cx + R * Math.cos(rad);
        const y = cy + R * Math.sin(rad);
        const lineP = interpolate(frame, [30 + s.d, 80 + s.d], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const nodeS = spring({ frame: frame - 20 - s.d, fps: 30, config: { damping: 200 } });
        const pulseP = ((frame + s.d * 3) % 90) / 90;
        return (
          <div key={s.label}>
            {/* connecting line (draws in) */}
            <div
              style={{
                position: "absolute",
                left: cx,
                top: cy,
                width: Math.hypot(x - cx, y - cy) * lineP,
                height: 3,
                transformOrigin: "left center",
                transform: `rotate(${Math.atan2(y - cy, x - cx)}rad)`,
                background: "linear-gradient(90deg, rgba(0,187,127,0.05), rgba(0,187,127,0.5))",
              }}
            />
            {/* pulse dot along line */}
            <div
              style={{
                position: "absolute",
                left: cx + (x - cx) * pulseP - 6,
                top: cy + (y - cy) * pulseP - 6,
                width: 12,
                height: 12,
                borderRadius: 999,
                background: GREEN,
                boxShadow: "0 0 16px rgba(0,187,127,0.9)",
                opacity: pulseP < 0.9 ? 1 : 0,
              }}
            />
            {/* satellite node */}
            <div
              style={{
                position: "absolute",
                left: x - 56,
                top: y - 56,
                width: 112,
                height: 112,
                borderRadius: 16,
                background: INK_900,
                border: "1px solid rgba(0,187,127,0.45)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                opacity: nodeS,
                transform: `scale(${interpolate(nodeS, [0, 1], [0.5, 1])})`,
              }}
            >
              <div style={{ ...MONO, color: INK_100, fontSize: 20, letterSpacing: 2, textAlign: "center" }}>
                {s.label}
              </div>
            </div>
          </div>
        );
      })}
    </Base>
  );
}

// ============================================================
// scene 8 — terminal (1380..1590)
// ============================================================
const MO_LINES = [
  "agentwallet escrow create --amount 50 USDC",
  "✓ funded · 50 USDC locked",
  "agentwallet x402 pay --endpoint model.api",
  "✓ paid · receipt confirmed",
  "agentwallet subscribe --plan pro --usdc 49",
  "✓ subscribed · exit 0",
];
const MO_STARTS = [0, 100, 145, 260, 305, 415];

function STerminal() {
  const frame = useCurrentFrame();
  return (
    <Base>
      <Kicker text="the terminal" x={140} start={10} />
      <H text={<>Every flow. <span style={{ color: GREEN }}>One command.</span></>} x={140} start={20} />
      <div
        style={{
          position: "absolute",
          left: 300,
          top: 300,
          width: 1320,
          background: INK_900,
          border: `1px solid ${INK_800}`,
          borderRadius: 14,
          overflow: "hidden",
          boxShadow: "0 40px 120px rgba(0,0,0,0.55)",
        }}
      >
        <div
          style={{
            ...MONO,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "18px 28px",
            borderBottom: `1px solid ${INK_800}`,
            background: INK_950,
          }}
        >
          <span style={{ color: MUTED, fontSize: 22, letterSpacing: 4 }}>AGENTWALLET.SH</span>
          <span style={{ display: "flex", gap: 10 }}>
            {[GREEN, "#f59e0b", "#ef4444"].map((c) => (
              <span key={c} style={{ width: 15, height: 15, borderRadius: 999, background: c }} />
            ))}
          </span>
        </div>
        <div style={{ padding: "26px 30px", minHeight: 360 }}>
          {MO_LINES.map((line, i) => {
            const isCmd = !line.startsWith("✓");
            const start = MO_STARTS[i];
            const n = line.length;
            const done = frame - start >= n * 3;
            const chars = Math.floor(
              interpolate(frame, [start, start + n * 3], [0, n], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })
            );
            const visible = isCmd ? Math.min(chars, n) : done ? n : 0;
            if (frame < start && !done) return null;
            const color = line.startsWith("✓") ? GREEN : INK_100;
            return (
              <div key={i} style={{ ...MONO, color, fontSize: 32, marginBottom: 24, whiteSpace: "nowrap" }}>
                {isCmd && <span style={{ color: GREEN, marginRight: 12 }}>$</span>}
                {line.slice(0, visible)}
                {isCmd && !done && (
                  <span style={{ color: GREEN, opacity: frame % 30 < 15 ? 1 : 0 }}>▍</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Base>
  );
}

// ============================================================
// scene 9 — data / compliance (1590..1800)
// ============================================================
const STATS = [
  { label: "TRANSACTIONS", to: 1284, prefix: "", start: 40, w: "340px" },
  { label: "VOLUME (USDC)", to: 42190, prefix: "$", start: 70, w: "340px" },
  { label: "UPTIME", to: 99.98, prefix: "", decimals: 2, suffix: "%", start: 100, w: "340px" },
];

function CountUp({ to, prefix = "", suffix = "", decimals = 0, start }: { to: number; prefix?: string; suffix?: string; decimals?: number; start: number }) {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [start, start + 55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <>
      {prefix}
      {(to * p).toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </>
  );
}

function SData() {
  const frame = useCurrentFrame();
  return (
    <Base>
      <Kicker text="built for compliance" x={140} start={10} />
      <H text={<>Real data. <span style={{ color: GREEN }}>Real audit trails.</span></>} x={140} start={20} />
      {/* stat cards */}
      <div style={{ position: "absolute", left: 140, top: 360, display: "flex", gap: 44 }}>
        {STATS.map((s) => (
          <Rise key={s.label} start={1590} delay={s.start}>
            <div
              style={{
                ...MONO,
                width: s.w,
                padding: "38px 40px",
                background: INK_900,
                border: `1px solid ${INK_800}`,
                borderRadius: 12,
              }}
            >
              <div style={{ color: DIM, fontSize: 24, letterSpacing: 4 }}>{s.label}</div>
              <div style={{ color: INK_100, fontSize: 72, fontWeight: 800, marginTop: 14 }}>
                <CountUp to={s.to} prefix={s.prefix} suffix={s.suffix ?? ""} decimals={s.decimals ?? 0} start={s.start} />
              </div>
            </div>
          </Rise>
        ))}
      </div>
      {/* chain blocks */}
      <div style={{ position: "absolute", left: 140, top: 700, display: "flex", gap: 26, alignItems: "center" }}>
        {[0, 1, 2, 3].map((i) => {
          const s = spring({ frame: frame - 150 - i * 18, fps: 30, config: { damping: 200 } });
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 26 }}>
              {i > 0 && (
                <div style={{ width: 26, height: 4, background: "rgba(0,187,127,0.4)" }} />
              )}
              <div
                style={{
                  ...MONO,
                  width: 150,
                  height: 84,
                  borderRadius: 10,
                  background: INK_900,
                  border: "1px solid rgba(0,187,127,0.4)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: s,
                  transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)`,
                }}
              >
                <span style={{ color: GREEN, fontSize: 30 }}>✓</span>
              </div>
            </div>
          );
        })}
        <div style={{ ...MONO, color: DIM, fontSize: 24, marginLeft: 16 }}>EVERY MOVE ON-CHAIN</div>
      </div>
    </Base>
  );
}

// ============================================================
// scene 10 — outro (1800..2040)
// ============================================================
function SOutro() {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - 20, fps: 30, config: { damping: 200 } });
  const t = frame / 30;
  return (
    <Base>
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            position: "absolute",
            width: 460,
            height: 460,
            borderRadius: 999,
            border: "2px dashed rgba(0,187,127,0.35)",
            transform: `rotate(${t * 24}deg)`,
            opacity: 0.7,
          }}
        />
        <div style={{ opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})` }}>
          <Hex size={170} />
        </div>
        <Rise start={1800} delay={20}>
          <div style={{ ...MONO, color: INK_100, fontSize: 108, fontWeight: 800, marginTop: 44 }}>
            agent<span style={{ color: GREEN }}>wallet</span>
          </div>
        </Rise>
        <Rise start={1800} delay={45}>
          <div style={{ ...MONO, color: GREEN, fontSize: 34, letterSpacing: 10, marginTop: 34 }}>
            LAUNCH ON DEVNET — FREE
          </div>
        </Rise>
        <Rise start={1800} delay={70}>
          <div
            style={{
              ...MONO,
              color: INK_100,
              fontSize: 28,
              letterSpacing: 2,
              marginTop: 54,
              padding: "16px 34px",
              border: `1px solid ${GREEN}`,
              borderRadius: 10,
              background: "rgba(0,187,127,0.08)",
            }}
          >
            agentwallet-devnet-two.vercel.app
          </div>
        </Rise>
        <Rise start={1800} delay={95}>
          <div style={{ ...MONO, color: DIM, fontSize: 22, letterSpacing: 8, marginTop: 44 }}>
            BUILT FOR THE AGENT ECONOMY · SOLANA
          </div>
        </Rise>
      </AbsoluteFill>
    </Base>
  );
}

// ============================================================
// captions (mute-friendly, synced to narration)
// ============================================================
const CAPS: { text: string; start: number; dur: number }[] = [
  { text: "introducing agentwallet", start: 4, dur: 130 },
  { text: "the payment rail for the agent economy", start: 152, dur: 170 },
  { text: "every agent gets its own Solana wallet — isolated · on-chain", start: 332, dur: 200 },
  { text: "escrow — fund it · release it", start: 542, dur: 200 },
  { text: "x402 — pay per API call", start: 752, dur: 200 },
  { text: "USDC subscriptions — no stripe", start: 962, dur: 200 },
  { text: "swarms coordinating payments", start: 1172, dur: 200 },
  { text: "the terminal — every flow", start: 1382, dur: 200 },
  { text: "real audit trails · compliance from day one", start: 1592, dur: 200 },
  { text: "launch free on devnet → agentwallet-devnet-two.vercel.app", start: 1802, dur: 230 },
];

function Caption({ text, start, dur }: { text: string; start: number; dur: number }) {
  const frame = useCurrentFrame();
  if (frame < start || frame > start + dur) return null;
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  const out = interpolate(frame, [start + dur - 14, start + dur], [1, 0], {
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
        bottom: 54,
        textAlign: "center",
        opacity: s * out,
        transform: `translateY(${interpolate(s, [0, 1], [22, 0])}px)`,
        zIndex: 20,
      }}
    >
      <span
        style={{
          fontSize: 40,
          fontWeight: 800,
          color: "#ffffff",
          textShadow:
            "0 2px 0 #000000, 0 4px 0 rgba(0,0,0,0.9), 0 6px 22px rgba(0,0,0,0.85)",
        }}
      >
        {text}
      </span>
    </div>
  );
}

// ============================================================
// main composition — 2040f (68s)
// ============================================================
export function Mograph() {
  return (
    <AbsoluteFill style={{ background: INK_950, fontFamily: FONT }}>
      <Sequence from={0} durationInFrames={150}>
        <SIntro />
      </Sequence>
      <Sequence from={150} durationInFrames={180}>
        <SHeadline />
      </Sequence>
      <Sequence from={330} durationInFrames={210}>
        <SWallet />
      </Sequence>
      <Sequence from={540} durationInFrames={210}>
        <SEscrow />
      </Sequence>
      <Sequence from={750} durationInFrames={210}>
        <SX402 />
      </Sequence>
      <Sequence from={960} durationInFrames={210}>
        <SUsdc />
      </Sequence>
      <Sequence from={1170} durationInFrames={210}>
        <SSwarms />
      </Sequence>
      <Sequence from={1380} durationInFrames={210}>
        <STerminal />
      </Sequence>
      <Sequence from={1590} durationInFrames={210}>
        <SData />
      </Sequence>
      <Sequence from={1800} durationInFrames={240}>
        <SOutro />
      </Sequence>
      {CAPS.map((c) => (
        <Caption key={c.start} text={c.text} start={c.start} dur={c.dur} />
      ))}
      <VoiceMograph />
    </AbsoluteFill>
  );
}

export default Mograph;
