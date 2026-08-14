# Regenerates src/Voice.tsx + src/VoiceShort.tsx from the generated audio meta.
# Timings are computed so clips never overlap: each starts at its intended
# scene frame (or right after the previous clip + GAP, whichever is later).
#
#   python scripts/voice_timings.py
import json

GAP = 15  # frames of silence between clips
START = 15  # first short clip starts this many frames in


def build_sequences(meta, intended, prefix=""):
    imports, seq, prev_end = [], [], -10**9
    for i, m in enumerate(meta):
        name = (prefix + f"{i:02d}").replace("-", "_")
        imports.append(f'import v_{name} from "../voice/{m["file"]}";')
        start = max(intended[i], prev_end + GAP)
        seq.append(f"      <Sequence from={{{start}}}>")
        seq.append(f"        <Audio src={{v_{name}}} />")
        seq.append(f"      </Sequence>")
        prev_end = start + int(m["dur"] * 30)
    return imports, seq, prev_end


def main():
    meta = json.load(open("voice/meta.json"))
    imports, seq, end = build_sequences(meta, [m["start"] for m in meta])
    src = ('import { Audio, Sequence } from "remotion";\n'
           + "\n".join(imports) + "\n\n"
           + "export function VoiceTrack() {\n  return (\n    <>\n"
           + "\n".join(seq) + "\n    </>\n  );\n}\n")
    open("src/Voice.tsx", "w").write(src)
    print(f"Voice.tsx written (narration ends @{end}f = {end/30:.1f}s / 3600f)")

    shorts = json.load(open("voice/shorts-meta.json"))
    blocks = []
    for prefix in ("s15", "s30"):
        entries = shorts[prefix]
        imports, seq, end = build_sequences(entries, [START] * len(entries), prefix + "-")
        fn = "VoiceShort15" if prefix == "s15" else "VoiceShort30"
        blocks.append(
            'import { Audio, Sequence } from "remotion";\n'
            + "\n".join(imports) + "\n\n"
            + f"export function {fn}() {{\n  return (\n    <>\n"
            + "\n".join(seq) + "\n    </>\n  );\n}\n")
        limit = 450 if prefix == "s15" else 900
        print(f"{fn} ends @{end}f / {limit}f")
    open("src/VoiceShort.tsx", "w").write("\n\n".join(blocks))
    print("VoiceShort.tsx written")


if __name__ == "__main__":
    main()
