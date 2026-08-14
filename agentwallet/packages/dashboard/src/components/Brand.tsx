import { useId } from "react";

/**
 * AgentWallet brand mark: a rounded hexagon (Solana / network feel)
 * with a terminal prompt ">_" glyph inside — agent + wallet + crypto.
 * Colors come from theme CSS variables, so it adapts to dark/light.
 */
export function LogoMark({
  className = "w-full h-full",
}: {
  className?: string;
}) {
  const gid = useId();
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden="true">
      <defs>
        <linearGradient
          id={gid}
          x1="4"
          y1="4"
          x2="36"
          y2="36"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="var(--brand-300)" />
          <stop offset="1" stopColor="var(--brand-600)" />
        </linearGradient>
      </defs>
      {/* hexagon */}
      <path
        d="M20 2.5 L34.9 11.25 V28.75 L20 37.5 L5.1 28.75 V11.25 Z"
        fill="var(--brand-500)"
        fillOpacity="0.07"
        stroke={`url(#${gid})`}
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      {/* terminal chevron */}
      <path
        d="M13.5 15 L20 20 L13.5 25"
        stroke={`url(#${gid})`}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* underscore */}
      <path
        d="M20.5 25.5 H26.5"
        stroke={`url(#${gid})`}
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

type BrandSize = "sm" | "lg";

const sizeMap: Record<
  BrandSize,
  { box: string; word: string; tagline: string }
> = {
  sm: {
    box: "w-8 h-8",
    word: "text-sm",
    tagline: "text-[10px] tracking-[0.25em]",
  },
  lg: {
    box: "w-14 h-14",
    word: "text-2xl",
    tagline: "text-[11px] tracking-[0.3em]",
  },
};

export default function Brand({
  size = "sm",
  tagline = "protocol",
  center = false,
}: {
  size?: BrandSize;
  tagline?: string;
  center?: boolean;
}) {
  const s = sizeMap[size];
  return (
    <div
      className={`flex items-center gap-3 ${center ? "flex-col gap-4" : ""}`}
    >
      <div className={`${s.box} flex-shrink-0`}>
        <LogoMark />
      </div>
      <div className={center ? "text-center" : ""}>
        <h1 className={`${s.word} font-bold text-heading tracking-tight leading-tight`}>
          agent<span className="text-brand-400">wallet</span>
        </h1>
        <p
          className={`${s.tagline} text-ink-500 uppercase font-medium mt-0.5 tracking-widest`}
        >
          {tagline}
        </p>
      </div>
    </div>
  );
}
