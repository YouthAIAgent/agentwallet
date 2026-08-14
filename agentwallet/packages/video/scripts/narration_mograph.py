# Generates the voiceover for the full motion-graphics launch video
# (10 scenes, ~68s) and writes src/VoiceMograph.tsx with non-overlapping
# per-scene sequence timings.
#
#   pip install edge-tts        # ffmpeg/ffprobe must be on PATH
#   python scripts/narration_mograph.py
import asyncio, json, subprocess, pathlib
import edge_tts

VOICE = "en-US-ChristopherNeural"
RATE = "+6%"
OUT = pathlib.Path("voice")
GAP = 20  # frames of silence between clips

# (start_frame, text) — synced to each scene of the mograph video (2040f total)
LINES = [
    (0,    "Introducing agentwallet."),
    (150,  "The payment rail for the agent economy."),
    (330,  "Every agent gets its own Solana wallet. Isolated. On-chain. Program-owned."),
    (540,  "Escrow with real on-chain guarantees. Fund it. Release it."),
    (750,  "x402. Pay per API call. One signature, and the agent is in."),
    (960,  "USDC subscriptions. No Stripe. No intermediaries. Pure on-chain billing."),
    (1170, "Swarms of agents, coordinating payments across the network."),
    (1380, "The terminal. Every flow. From wallet to escrow to billing, one command."),
    (1590, "Real data. Real audit trails. Built for compliance, from day one."),
    (1800, "Launch free on devnet today. Agentwallet. Built for the agent economy."),
]


def dur(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path)]).decode().strip())


def trim_silence(path):
    tmp = path.with_suffix(path.suffix + ".tmp.mp3")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path),
                    "-af", "silenceremove=start_periods=1:start_threshold=-45dB:"
                           "start_silence=0.05,areverse,silenceremove=start_periods=1:"
                           "start_threshold=-45dB:start_silence=0.05,areverse",
                    "-acodec", "libmp3lame", "-q:a", "5", str(tmp)], check=True)
    tmp.replace(path)


async def gen():
    meta = []
    prev_end = -10**9
    for i, (start, text) in enumerate(LINES):
        name = f"mo-{i:02d}.mp3"
        await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(OUT / name))
        trim_silence(OUT / name)
        d = round(dur(OUT / name), 2)
        actual_start = max(start, prev_end + GAP)
        meta.append({"file": name, "start": actual_start, "text": text, "dur": d})
        prev_end = actual_start + int(d * 30)
        print(f"{name}: {d:.2f}s @{actual_start}  (ends {prev_end}f)")
    json.dump(meta, open("voice/mograph-meta.json", "w"), indent=1)
    print(f"TOTAL end: {prev_end}f = {prev_end/30:.1f}s / 2040f")

    # write VoiceMograph.tsx
    imports = [f'import v{i:02d} from "../voice/mo-{i:02d}.mp3";' for i in range(len(meta))]
    seq = []
    for i, m in enumerate(meta):
        seq += [f'      <Sequence from={{{m["start"]}}}>',
                f'        <Audio src={{v{i:02d}}} />',
                f'      </Sequence>']
    src = ('import { Audio, Sequence } from "remotion";\n'
           + "\n".join(imports) + "\n\n"
           + "export function VoiceMograph() {\n  return (\n    <>\n"
           + "\n".join(seq) + "\n    </>\n  );\n}\n")
    open("src/VoiceMograph.tsx", "w").write(src)
    print("src/VoiceMograph.tsx written")


asyncio.run(gen())
