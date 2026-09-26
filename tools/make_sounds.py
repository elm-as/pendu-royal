"""Synthétise les effets sonores du jeu (WAV mono 22 kHz, aucun droit d'auteur).

    python tools/make_sounds.py
"""
import math
import random
import struct
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / "assets" / "sounds"


def tone(freq, dur, vol=0.5, shape="sine", attack=0.005, decay=None, freq_end=None):
    n = int(RATE * dur)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / RATE
        f = freq if freq_end is None else freq + (freq_end - freq) * i / n
        phase += 2 * math.pi * f / RATE
        if shape == "sine":
            s = math.sin(phase)
        elif shape == "tri":
            s = 2 / math.pi * math.asin(math.sin(phase))
        else:  # bruit
            s = random.uniform(-1, 1)
        env = min(1.0, t / attack) if attack else 1.0
        env *= math.exp(-t * (decay if decay is not None else 6 / dur))
        out.append(s * env * vol)
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def seq(*parts, gap=0.0):
    out = []
    for p in parts:
        out.extend(p)
        out.extend([0.0] * int(RATE * gap))
    return out


def bell(freq, dur=0.35, vol=0.35):
    return mix(tone(freq, dur, vol), tone(freq * 2, dur, vol * 0.3), tone(freq * 3.01, dur * 0.6, vol * 0.12))


def save(name, samples):
    OUT.mkdir(parents=True, exist_ok=True)
    peak = max(1e-6, max(abs(s) for s in samples))
    scale = min(1.0, 0.9 / peak)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(s * scale * 32767)) for s in samples))


def main():
    random.seed(7)
    save("click", tone(1400, 0.035, 0.35, "tri", decay=120))
    save("select", tone(900, 0.05, 0.3, "tri", decay=70))
    save("hit", seq(bell(784, 0.18), bell(1175, 0.35)))
    save("miss", mix(tone(150, 0.35, 0.8, "sine", freq_end=70), tone(0, 0.08, 0.25, "noise", decay=60)))
    save("feather", tone(700, 0.45, 0.25, "sine", freq_end=300, decay=5))
    save("win", seq(bell(523, 0.16), bell(659, 0.16), bell(784, 0.16), bell(1047, 0.7, 0.45)))
    save("lose", seq(tone(392, 0.25, 0.5, "tri"), tone(330, 0.25, 0.5, "tri"), tone(262, 0.25, 0.5, "tri"),
                     tone(196, 0.8, 0.55, "tri", decay=3)))
    save("event", mix(tone(300, 0.6, 0.35, "sine", freq_end=1200, decay=3), tone(0, 0.6, 0.08, "noise", decay=5)))
    save("coin", seq(bell(988, 0.08, 0.3), bell(1319, 0.3, 0.3)))
    save("tick", tone(1800, 0.02, 0.25, "tri", decay=200))
    save("unlock", seq(bell(659, 0.12), bell(880, 0.12), bell(1319, 0.9, 0.45)))
    print("Sons générés dans", OUT)


if __name__ == "__main__":
    main()
