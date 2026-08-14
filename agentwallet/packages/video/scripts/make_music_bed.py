# Generates the subtle background-music bed for the launch videos.
# A gentle 16s loop: Am -> F -> C -> G, warm detuned pad + soft plucky
# arpeggio + a soft kick on each chord change. Written to assets/music-bed.wav
# (44.1kHz, 16-bit stereo, ~1.4MB) and intended to sit ~-18dB under the
# voiceover with sidechain ducking applied at mix time.
#
#   pip install numpy        # then:  python scripts/make_music_bed.py
import numpy as np, pathlib, wave

SR = 44100
CHORD_SECS = 4.0
ROOT = pathlib.Path(__file__).resolve().parent.parent / "assets"

# (root, third, fifth) for the pad; arpeggio uses higher voicings
CHORDS = [
    {"pad": [220.00, 261.63, 329.63], "arp": [440.00, 523.25, 659.25, 880.00]},  # Am
    {"pad": [174.61, 220.00, 261.63], "arp": [349.23, 440.00, 523.25, 698.46]},  # F
    {"pad": [196.00, 246.94, 329.63], "arp": [392.00, 493.88, 659.25, 783.99]},  # G
    {"pad": [130.81, 164.81, 196.00], "arp": [261.63, 329.63, 392.00, 523.25]},  # C
]


def env(n, attack, release, hold=None):
    """Attack/release amplitude envelope over n samples."""
    e = np.ones(n)
    a = int(attack * SR)
    r = int(release * SR)
    e[:a] = np.linspace(0, 1, a)
    if hold is not None:
        e[hold:] = np.linspace(1, 0, n - hold)
    else:
        e[-r:] = np.linspace(1, 0, r)
    return e


def chord_block(freqs, n):
    """Warm pad: each note a few detuned partials with slow vibrato."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.15, 0.0, 0.15):
            vib = 1.0 + 0.002 * np.sin(2 * np.pi * 4.5 * t + f)
            partial = (
                0.55 * np.sin(2 * np.pi * f * vib * t + det)
                + 0.22 * np.sin(2 * np.pi * 2 * f * t)  # octave shimmer
                + 0.08 * np.sin(2 * np.pi * 3 * f * t)
            )
            out += partial * (1 / 3.0)
    return out * env(n, 0.8, 0.8)


def arp_block(freqs, n, chord_i):
    """Plucky up-down arpeggio, one note per 8th note."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    step = int(SR * 0.5)  # 8th notes at ~120bpm
    pattern = [0, 1, 2, 3, 2, 1]  # up-down
    for s, idx in enumerate(pattern):
        s0 = s * step
        if s0 >= n:
            break
        seg = min(step, n - s0)
        tt = t[:seg]
        f = freqs[idx % len(freqs)]
        note = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 4.5)
        out[s0 : s0 + seg] += note
    return out * env(n, 0.02, 0.4)


def kick(n, chord_i):
    """Soft kick on each chord change: 55Hz -> 40Hz sine sweep."""
    t = np.arange(n) / SR
    f = 55.0 * np.exp(-t * 3.5) + 38.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 7.0)
    click = np.sin(2 * np.pi * 300 * t) * np.exp(-t * 60.0) * 0.3
    return (body + click) * env(n, 0.002, 0.35)


def main():
    ROOT.mkdir(exist_ok=True)
    n_chord = int(CHORD_SECS * SR)
    blocks = []
    for ci, ch in enumerate(CHORDS):
        pad = chord_block(ch["pad"], n_chord) * 0.5
        arp = arp_block(ch["arp"], n_chord, ci) * 0.30
        kc = kick(n_chord, ci) * 0.28
        blocks.append(pad + arp + kc)

    mono = np.concatenate(blocks)
    # gentle overall fade at loop edges so it loops seamlessly
    fade = int(0.35 * SR)
    mono[:fade] *= np.linspace(0, 1, fade)
    mono[-fade:] *= np.linspace(1, 0, fade)
    # normalize to ~ -14 dBFS peak so the mix has headroom
    mono = mono / (np.max(np.abs(mono)) + 1e-9) * 0.20
    # very light stereo: duplicate with a tiny haas delay
    delay = int(0.012 * SR)
    left = mono
    right = np.concatenate([np.zeros(delay), mono[:-delay]])
    stereo = np.stack([left, right], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

    out = ROOT / "music-bed.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {out}  ({out.stat().st_size / 1e6:.2f} MB, "
          f"{len(mono) / SR:.1f}s, peak {np.max(np.abs(mono)):.3f})")


if __name__ == "__main__":
    main()
