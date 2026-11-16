#!/usr/bin/env python3
"""Compose a light, royalty-free Khaleeji wedding instrumental (oud melody in
maqam Hijaz on D, soft daf, hand claps, warm string pad) as a WAV file.

Usage: python3 compose_music.py out.wav [--seconds 40]
"""
import argparse
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
rng = np.random.default_rng(7)

D4 = 293.66
HIJAZ = {"D": 0, "Eb": 1, "F#": 4, "G": 5, "A": 7, "Bb": 8, "C": 10,
         "D'": 12, "Eb'": 13, "C,": -2, "A,": -5, "D,": -12}


def hz(name):
    return D4 * 2 ** (HIJAZ[name] / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def pluck(freq, dur, bright=0.6, decay=0.996):
    """Karplus-Strong string, vectorised per period, shaped like an oud."""
    n = int(dur * SR)
    N = max(2, int(SR / freq))
    out = np.zeros(n + N)
    out[:N] = lp(rng.uniform(-1, 1, N * 4), 1500 + 3000 * bright)[:N]
    for start in range(N, n + N, N):
        prev = out[start - N:start]
        avg = 0.5 * (prev + np.roll(prev, 1)) * decay
        end = min(start + N, n + N)
        out[start:end] = avg[: end - start]
    y = out[:n]
    y = lp(y, 2600) + 0.35 * bp(y, 150, 400)       # wooden body warmth
    env = np.minimum(1, np.linspace(0, dur, n) / 0.004)
    return y * env


def daf_dum(dur=0.5):
    t = np.arange(int(dur * SR)) / SR
    f = 55 + 45 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    skin = bp(rng.uniform(-1, 1, t.size), 200, 900) * np.exp(-t * 40) * 0.3
    return body + skin


def daf_tak(dur=0.35):
    t = np.arange(int(dur * SR)) / SR
    tone = np.sin(2 * np.pi * 330 * t) * np.exp(-t * 35) * 0.5
    jingle = bp(rng.uniform(-1, 1, t.size), 4000, 9000) * np.exp(-t * 14) * 0.35
    return tone + jingle


def clap(dur=0.25):
    t = np.arange(int(dur * SR)) / SR
    env = np.zeros_like(t)
    for d in (0, 0.008, 0.017):          # several hands, slightly apart
        env += np.exp(-np.clip(t - d, 0, None) * 45) * (t >= d)
    return bp(rng.uniform(-1, 1, t.size), 900, 3500) * env * 0.5


def pad(freqs, dur):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):   # detuned saws = string ensemble
            ph = (f * 2 ** (det / 12) * t + rng.random()) % 1
            y += 2 * ph - 1
    y = lp(y / (len(freqs) * 3), 1100, 4)
    att, rel = 0.6, 0.6
    env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / rel)
    return y * np.clip(env, 0, 1)


def place(buf, sig, at, gain):
    i = int(at * SR)
    j = min(buf.size, i + sig.size)
    if i < buf.size:
        buf[i:j] += sig[: j - i] * gain


# Melody: (note or None for rest, length in eighths)
A1 = [("A", 1), ("A", 1), ("Bb", 1), ("A", 1), ("G", 1), ("F#", 1), ("G", 1), ("A", 1),
      ("G", 1), ("F#", 1), ("Eb", 1), ("F#", 1), ("D", 4)]
B1 = [("D", 1), ("F#", 1), ("G", 1), ("A", 1), ("Bb", 1), ("C", 1), ("Bb", 1), ("A", 1),
      ("G", 1), ("A", 1), ("Bb", 1), ("A", 1), ("G", 1), ("F#", 1), ("G", 2)]
C1 = [("D'", 1), ("C", 1), ("Bb", 1), ("A", 1), ("Bb", 1), ("C", 1), ("D'", 2),
      ("C", 1), ("Bb", 1), ("A", 1), ("G", 1), ("A", 4)]
END = [("G", 1), ("F#", 1), ("Eb", 1), ("F#", 1), ("G", 1), ("F#", 1), ("Eb", 1), ("D", 1),
       ("D", 8)]
INTRO = [("D", 2), ("Eb", 1), ("F#", 1), ("G", 2), ("F#", 1), ("Eb", 1),
         ("D", 6), (None, 2)]

# 14 bars = 7 two-bar phrases: intro A B C A C ending
SONG = INTRO + A1 + B1 + C1 + A1 + C1 + END
CHORDS = ["D", "D", "D", "Gm", "D", "Cm", "D", "D", "Gm", "D", "Gm", "D", "D", "D"]
CHORD_NOTES = {"D": ["D,", "A,", "D"], "Gm": ["D,", "G", "Bb"], "Cm": ["C,", "Eb", "G"]}


def compose(seconds):
    bars = 14
    beat = seconds / (bars * 4)
    e8 = beat / 2
    mel, perc, pads = (np.zeros(int((seconds + 3) * SR)) for _ in range(3))

    # melody (oud, with a soft lower-octave double on long notes)
    t = 0.0
    for note, ln in SONG:
        if note:
            d = max(0.6, ln * e8 + 0.5)
            place(mel, pluck(hz(note), d, bright=0.55), t, 0.55)
            if ln >= 2:
                place(mel, pluck(hz(note) / 2, d, bright=0.4), t + 0.012, 0.25)
        t += ln * e8

    # pad + bass pluck per bar
    for b, ch in enumerate(CHORDS):
        fr = [hz(n) / 2 for n in CHORD_NOTES[ch]]
        place(pads, pad(fr, 4 * beat + 0.6), b * 4 * beat, 0.16)
        place(mel, pluck(fr[0] / 2, 1.2, bright=0.3), b * 4 * beat, 0.35)

    # Khaleeji groove from bar 3 to bar 12, light, with claps building in
    for b in range(2, 13):
        s = b * 4 * beat
        for k in (0, 3, 5):
            place(perc, daf_dum(), s + k * e8, 0.55)
        for k in (2, 6):
            place(perc, daf_tak(), s + k * e8, 0.35)
        if b >= 4:
            for k in (2, 6):
                place(perc, clap(), s + k * e8 + rng.normal(0, 0.004), 0.45)
        if b >= 8:
            place(perc, clap(), s + 7 * e8, 0.3)
    place(perc, daf_dum(0.9), 13 * 4 * beat, 0.6)   # final hit on the last bar

    mix = mel + 0.8 * perc + pads
    # room reverb
    ir_t = np.arange(int(1.6 * SR)) / SR
    ir = rng.normal(0, 1, ir_t.size) * np.exp(-ir_t * 4.2)
    ir = lp(ir, 5000)
    wet = fftconvolve(mix, ir)[: mix.size]
    wet *= 0.18 * np.max(np.abs(mix)) / (np.max(np.abs(wet)) + 1e-9)
    mix = mix + wet
    mix = mix[: int(seconds * SR)]
    n = mix.size
    fade = np.ones(n)
    fi, fo = int(0.8 * SR), int(2.5 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
    mix *= fade
    mix /= np.max(np.abs(mix)) + 1e-9
    mix = np.tanh(mix * 1.2) / np.tanh(1.2) * 0.89
    # gentle stereo: tiny delay on one side
    right = np.concatenate([np.zeros(int(0.011 * SR)), mix])[:n]
    return np.stack([mix, 0.7 * mix + 0.3 * right], axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=40.0)
    a = ap.parse_args()
    st = compose(a.seconds)
    wavfile.write(a.out, SR, (st * 32767).astype(np.int16))
    print(f"wrote {a.out} ({a.seconds:.1f}s)")


if __name__ == "__main__":
    main()
