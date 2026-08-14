# Generates per-scene narration clips with edge-tts for the 2-min video + shorts.
#
#   pip install edge-tts        # ffmpeg/ffprobe must be on PATH
#   python scripts/narration.py # writes voice/*.mp3 + voice/meta.json + voice/shorts-meta.json
#
# Then regenerate src/Voice.tsx / src/VoiceShort.tsx (timings are computed from
# the audio durations so clips never overlap).
import asyncio, json, subprocess, pathlib
import edge_tts

VOICE = "en-US-ChristopherNeural"
RATE = "+8%"  # slightly fast so the full script fits the 120s video
OUT = pathlib.Path("voice")

# (start_frame, text) — starts synced to each scene of the 2-min video.
# Dashes are written as commas: edge-tts pauses far longer on an em-dash.
LINES = [
    (20,   "agentwallet, the payment rail for the agent economy."),
    (120,  "Wallets, escrow, x402, USDC, and swarms, all on Solana."),
    (255,  "A public landing page, built to convert."),
    (340,  "Hero, features, pricing, and a devnet call to action."),
    (430,  "Launch the dashboard, and register in minutes."),
    (555,  "Register in seconds."),
    (640,  "Your organization. Your email. Your on-chain keys."),
    (730,  "Your API token, issued right on devnet."),
    (855,  "The dashboard, real data, live."),
    (940,  "Agents create wallets. Agents pay. Automatically."),
    (1060, "Every spend is visible, on-chain."),
    (1215, "Per-agent autonomy."),
    (1300, "Each agent gets its own wallet, and its own policy."),
    (1390, "Pause. Delete. Audit. Full control."),
    (1515, "PDA custody."),
    (1600, "Treasury, escrow, and agent wallets on Solana."),
    (1690, "Keys isolated. Spend limited."),
    (1815, "Every move is on-chain."),
    (1900, "Transactions, daily spend, audit trail."),
    (1990, "Built for compliance, from day one."),
    (2115, "USDC subscriptions."),
    (2200, "Free at zero. Pro at forty-nine. Enterprise at two-ninety-nine."),
    (2355, "Dark or light."),
    (2440, "One toggle re-themes the entire app."),
    (2595, "Everything agents need to move money."),
    (2710, "Escrow, x402, USDC, and swarms, all Solana programs."),
    (2895, "The terminal. Every flow."),
    (2980, "Escrow funded. Paid. Subscribed. Exit zero."),
    (3195, "Launch free on devnet."),
    (3310, "Agent wallet devnet two, on Vercel."),
    (3410, "Built for the agent economy, on Solana."),
]

# Caption-matched narration for the vertical shorts.
SHORTS = {
    "s15": [
        "agentwallet, payments for the agent economy.",
        "Real wallets, escrow, and billing on Solana.",
        "Agents create wallets. Agents pay. On-chain.",
        "Escrow, x402, USDC, and swarms.",
        "Launch free on devnet.",
    ],
    "s30": [
        "agentwallet, payments for the agent economy.",
        "The payment rail for the agent economy.",
        "Wallets, escrow, and pay-per-call billing.",
        "Real data, live on devnet.",
        "Each agent gets its own wallet and policy.",
        "PDA custody. Treasury, escrow, and agent wallets.",
        "The terminal. Every flow.",
        "Escrow funded. Paid. Subscribed. Exit zero.",
        "Launch free on devnet.",
    ],
}


def dur(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path)]).decode().strip())


def trim_silence(path):
    """Trim leading/trailing silence (and for shorts, internal pauses)."""
    tmp = path.with_suffix(path.suffix + ".tmp.mp3")
    if "s15" in path.name:
        # 15s short is tight — also collapse internal pauses
        filt = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,"
                "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,"
                "areverse,silenceremove=stop_periods=-1:stop_threshold=-40dB:stop_duration=0.12")
    else:
        filt = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                "areverse")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-af", filt,
                    "-acodec", "libmp3lame", "-q:a", "5", str(tmp)], check=True)
    tmp.replace(path)


async def gen_clip(name, text, rate):
    await edge_tts.Communicate(text, VOICE, rate=rate).save(str(OUT / name))
    trim_silence(OUT / name)
    d = round(dur(OUT / name), 2)
    print(f"{name}: {d:.2f}s")
    return d


async def gen():
    meta = []
    for i, (start, text) in enumerate(LINES):
        name = f"{i:02d}.mp3"
        d = await gen_clip(name, text, RATE)
        meta.append({"file": name, "start": start, "text": text, "dur": d})
    json.dump(meta, open("voice/meta.json", "w"), indent=1)
    total = sum(m["dur"] for m in meta)
    print(f"2-min TOTAL: {total:.1f}s = {total * 30:.0f}f (video 3600f)")

    shorts = {}
    for prefix, lines in SHORTS.items():
        entries = []
        for i, text in enumerate(lines):
            name = f"{prefix}-{i:02d}.mp3"
            # s15 gets an extra speed boost to fit 15s
            d = await gen_clip(name, text, "+18%" if prefix == "s15" else RATE)
            entries.append({"file": name, "text": text, "dur": d})
        shorts[prefix] = entries
        t = sum(e["dur"] for e in entries)
        print(f"{prefix} TOTAL: {t:.1f}s = {t * 30:.0f}f "
              f"(limit {450 if prefix == 's15' else 900}f)")
    json.dump(shorts, open("voice/shorts-meta.json", "w"), indent=1)


asyncio.run(gen())
