import { interpolate, spring, useCurrentFrame } from "remotion";
import { FONT } from "./Launch";

export type Face = "sol" | "usdc";

/**
 * Cute glowing coin mascot — SOL face (Solana purple) / USDC face (blue).
 * Floats with a bob, blinks periodically, has a soft glow, and can do a
 * horizontal spin-flip between faces (`flipAt` = frame it flips to `face`).
 */
export function CoinMascot({
  x,
  y,
  size = 92,
  face = "sol",
  start = 0,
  flipAt,
  bob = true,
  spin = 0,
  wink = false,
  z = 15,
}: {
  x: number;
  y: number;
  size?: number;
  face?: Face;
  start?: number;
  flipAt?: number;
  bob?: boolean;
  spin?: number;
  wink?: boolean;
  z?: number;
}) {
  const frame = useCurrentFrame();
  const s = spring({ frame: frame - start, fps: 30, config: { damping: 200 } });
  const float = bob ? Math.sin((frame / 30) * 2.1) * 7 : 0;
  const glowPulse = 0.55 + 0.45 * Math.sin((frame / 30) * 3.2);

  // face flip (fake 3D spin)
  let showFace: Face = face;
  let scaleX = 1;
  if (flipAt !== undefined) {
    const fp = interpolate(frame, [flipAt, flipAt + 18], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    scaleX = Math.cos(fp * Math.PI);
    showFace = fp >= 0.5 ? face : face === "sol" ? "usdc" : "sol";
  }

  const blink = wink ? frame % 100 < 6 : frame % 150 < 5;
  const rotate = ((frame % 3600) / 3600) * spin;
  const c1 = showFace === "sol" ? "#9945FF" : "#2775CA";
  const c2 = showFace === "sol" ? "#14F195" : "#6FB7EE";
  const edge = showFace === "sol" ? "rgba(20,241,149,0.85)" : "rgba(111,183,238,0.9)";
  const glowColor =
    showFace === "sol" ? "rgba(153,69,255,0.42)" : "rgba(39,117,202,0.42)";
  const glyph = showFace === "sol" ? "S" : "$";
  const scale = interpolate(s, [0, 1], [0.4, 1]);

  return (
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        zIndex: z,
        opacity: s,
        transform: `translateY(${float}px) scale(${scale} ${scale * scaleX}) rotate(${rotate}deg)`,
        transformOrigin: "center",
      }}
    >
      {/* glow */}
      <div
        style={{
          position: "absolute",
          inset: -size * 0.45,
          borderRadius: 999,
          background: `radial-gradient(circle, ${glowColor}, transparent 70%)`,
          opacity: glowPulse,
        }}
      />
      {/* sparkles */}
      <div
        style={{
          position: "absolute",
          top: -size * 0.14,
          left: size * 0.1,
          width: size * 0.09,
          height: size * 0.09,
          borderRadius: 999,
          background: "#ffffff",
          opacity: 0.25 + 0.75 * Math.abs(Math.sin((frame / 30) * 2.6)),
        }}
      />
      <div
        style={{
          position: "absolute",
          top: size * 0.22,
          right: -size * 0.1,
          width: size * 0.06,
          height: size * 0.06,
          borderRadius: 999,
          background: "#ffffff",
          opacity: 0.2 + 0.8 * Math.abs(Math.sin((frame / 30) * 3.4 + 1.7)),
        }}
      />
      {/* coin body */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: 999,
          background: `radial-gradient(circle at 35% 28%, ${c2}, ${c1} 78%)`,
          border: `3px solid ${edge}`,
          boxShadow: `0 0 ${size * 0.32 * glowPulse}px ${glowColor}, inset 0 0 ${size * 0.2}px rgba(255,255,255,0.16)`,
        }}
      >
        {/* glyph */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: FONT,
            fontSize: size * 0.4,
            fontWeight: 800,
            color: "rgba(255,255,255,0.96)",
            textShadow: "0 2px 10px rgba(0,0,0,0.45)",
          }}
        >
          {glyph}
        </div>
        {/* eyes */}
        <div
          style={{
            position: "absolute",
            top: "36%",
            left: "24%",
            width: size * 0.1,
            height: blink ? Math.max(2, size * 0.03) : size * 0.12,
            borderRadius: 999,
            background: "#14110d",
            boxShadow: "0 0 0 2px rgba(255,255,255,0.35)",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: "36%",
            right: "24%",
            width: size * 0.1,
            height: blink ? Math.max(2, size * 0.03) : size * 0.12,
            borderRadius: 999,
            background: "#14110d",
            boxShadow: "0 0 0 2px rgba(255,255,255,0.35)",
          }}
        />
        {/* smile */}
        <div
          style={{
            position: "absolute",
            top: "52%",
            left: "36%",
            width: size * 0.28,
            height: size * 0.16,
            borderBottom: `${Math.max(2, size * 0.05)}px solid #14110d`,
            borderRadius: "0 0 999px 999px",
          }}
        />
        {/* blush */}
        <div
          style={{
            position: "absolute",
            top: "48%",
            left: "12%",
            width: size * 0.09,
            height: size * 0.05,
            borderRadius: 999,
            background: "rgba(255,255,255,0.30)",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: "48%",
            right: "12%",
            width: size * 0.09,
            height: size * 0.05,
            borderRadius: 999,
            background: "rgba(255,255,255,0.30)",
          }}
        />
      </div>
    </div>
  );
}
