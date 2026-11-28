# Mix for the Kookh Roza reel: original synthesized score (music box, glockenspiel, soft plucked bass, shaker),
# crayon/brush/door foley driven by events.json, room + night ambience, and the Gemini TTS narration → out/mix.wav
# Usage: $LIB/.venv/bin/python mix.py   (LIB = the Lemo-Opuscar library folder)
import sys, os, json, subprocess, numpy as np, soundfile as sf, soxr
from scipy.ndimage import uniform_filter1d
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', os.path.expanduser('~/lemo-opuscar'))
sys.path.insert(0, os.path.join(LIB, 'core/audio'))
from sfx import *   # SR=48000, bp/lp/hp, noise, brown, click, creak, pop, ding, compress, limit, add

E = json.load(open(os.path.join(HERE, 'events.json'))); DUR = E['dur']; EV = E['ev']
N = int(DUR * SR); rng = np.random.default_rng(7)
def T(d): return np.arange(int(round(d * SR))) / SR
def nz(d): return rng.standard_normal(int(round(d * SR)))
def fade(x, a=.01, b=.03):
    n = len(x); ia, ib = min(n, int(a * SR)), min(n, int(b * SR))
    if ia: x[:ia] *= np.linspace(0, 1, ia)
    if ib: x[-ib:] *= np.linspace(1, 0, ib)
    return x
def stereo(): return np.zeros((N, 2))
def mtof(m): return 440 * 2 ** ((m - 69) / 12)

# ——— instruments ———
def musicbox(m, v=1.0, d=1.6):
    f = mtof(m); t = T(d)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9) + 0.35 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t / 0.25)
         + 0.18 * np.sin(2 * np.pi * f * 6.7 * t) * np.exp(-t / 0.08))
    x[:int(.002 * SR)] *= np.linspace(0, 1, int(.002 * SR))
    return fade(x * v * 0.22, .001, .2)
def glock(m, v=1.0, d=2.0):
    f = mtof(m); t = T(d)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 1.1) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.35) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.12)
    return fade(x * v * 0.2, .001, .3)
def pluck(m, v=1.0, d=1.2):
    f = mtof(m); t = T(d)
    x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.25 * np.sin(6 * np.pi * f * t)) * np.exp(-t / 0.35)
    return fade(lp(x, 1800) * v * 0.2, .003, .1)
def shaker(v=1.0): return fade(hp(nz(.09), 5000) * np.exp(-T(.09) / .03) * v * 0.05, .004, .02)

# ——— foley ———
def crayon(d, speed=1.0, v=1.0):
    n = nz(d); rate = int(SR / (70 + 90 * speed))
    grain = uniform_filter1d((rng.random(len(n) // rate + 2) ** 3).repeat(rate)[:len(n)], rate // 3 + 1)
    x = bp(n, 1400 + 600 * speed, 6500, 2) * (0.35 + grain * 1.6) + bp(n, 300, 900, 1) * 0.15
    env = np.interp(T(d), [0, .08 * d, .85 * d, d], [0, 1, .9, 0])
    return fade(x * env * v * 0.2, .01, .04)
def scribble(d, rate=6.5, v=1.0):
    out = np.zeros(int(d * SR)); t = 0.0
    while t < d - 0.08:
        L = 1 / rate * (0.8 + 0.4 * rng.random()); s = crayon(min(L, d - t), 1.3, v * (0.7 + 0.3 * rng.random()))
        i = int(t * SR); out[i:i + len(s)] += s[:len(out) - i]; t += L
    return out
def write(d, v=1.0):
    out = np.zeros(int(d * SR)); t = 0.0
    while t < d - 0.1:
        L = 0.07 + 0.1 * rng.random(); s = crayon(L, 0.8, v); i = int(t * SR); out[i:i + len(s)] += s[:len(out) - i]; t += L + 0.03 * rng.random()
    return out
def brush(d, v=1.0):
    n = nz(d); bristle = uniform_filter1d(np.abs(rng.standard_normal(len(n))), 200)
    x = lp(n, 1600) * (0.6 + 0.8 * bristle) + bp(n, 2500, 6000) * 0.08
    env = np.interp(T(d), [0, .1 * d, .8 * d, d], [0, 1, .8, 0])
    return fade(x * env * v * 0.12, .05, .2)
def door(v=1.0):
    out = np.zeros(int(0.7 * SR)); c = creak(v * 0.5); out[:len(c)] += c[:len(out)]
    k = clack(0.8, v * 0.6); i = int(0.45 * SR); out[i:i + len(k)] += k[:len(out) - i]
    return out
def chirp(v=1.0):
    d = 0.12; t = T(d); f = 3200 + 1600 * np.sin(np.pi * t / d)
    return fade(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) * v * 0.02, .005, .02)
def crickets(d, v=1.0):
    t = T(d); carrier = np.sin(2 * np.pi * 4600 * t)
    pulses = (np.sin(2 * np.pi * 28 * t) > 0.3) * (np.sin(2 * np.pi * 1.4 * t + 1) > -0.2)
    return lp(carrier * uniform_filter1d(pulses.astype(float), 60), 7000) * v * 0.012

mus, fx, amb, vox = stereo(), stereo(), stereo(), stereo()

# ——— score: 96 BPM in 3/4, F major; one theme, held back in the night, heard whole at the end ———
BEAT = 60 / 96; BAR = 3 * BEAT
MEL = [[(0, 69, 1), (1, 72, 1), (2, 77, 1)], [(0, 76, 1.5), (1.5, 74, .5), (2, 72, 1)], [(0, 74, 1), (1, 77, 1), (2, 81, 1)], [(0, 77, 1.5), (1.5, 74, .5), (2, 70, 1)],
       [(0, 69, 1), (1, 72, 1), (2, 77, 1)], [(0, 79, 1), (1, 76, 1), (2, 72, 1)], [(0, 74, 1), (1, 72, 1), (2, 70, 1)], [(0, 69, 3)]]
BASS = [53, 48, 50, 46, 53, 48, 46, 53]
def section_gain(t):
    if t < 3.0: return 0.75
    if t < 6.35: return 1.0
    if t < 6.95: return 0.0
    if t < 10.8: return 0.55
    return 1.0
for b in range(8):
    t0 = b * BAR
    for (bt, m, du) in MEL[b]:
        t = t0 + bt * BEAT; g = section_gain(t)
        if g == 0 or (6.95 <= t < 10.8 and bt % 1): continue
        if b == 7: continue
        add(mus, musicbox(m, g, 1.8), t, 1.0, -0.15)
    bt = t0; g = section_gain(bt)
    if g and b < 7: add(mus, pluck(BASS[b], g * 0.9), bt, 1.0, 0.1)
    for k in (1, 2):
        ts = t0 + k * BEAT
        if (3.0 <= ts < 6.35) or ts >= 10.8: add(mus, shaker(0.8), ts, 1.0, 0.3)
# glockenspiel note per item of clothing; final chord rings out
GL = [84, 88, 91]
for e in EV:
    if e['type'] == 'glock': add(mus, glock(GL[e['i']], 1.0), e['t'], 1.0, [-0.4, 0, 0.4][e['i']])
    if e['type'] == 'end':
        for m, p in ((65, -0.2), (69, 0.0), (72, 0.2), (77, 0.1)): add(mus, musicbox(m, 0.9, 1.1), e['t'], 1.0, p)
        add(mus, glock(89, 0.6, 1.1), e['t'] + 0.02, 1.0, 0.3); add(mus, pluck(53, 0.9, 1.1), e['t'], 1.0, 0)

# ——— foley from events ———
for e in EV:
    t, ty, pan = e['t'], e['type'], e.get('pan', 0)
    if ty == 'scratch': add(fx, crayon(e['dur'], 1.0, 1.0), t, 1.0, pan)
    elif ty == 'scribble': add(fx, scribble(e['dur'], v=0.9), t, 1.0, pan)
    elif ty == 'write': add(fx, write(e['dur'], 0.8), t, 1.0, pan)
    elif ty == 'pop': add(fx, pop(0.5), t, 1.0, pan); add(fx, glock(96, 0.35, 0.8), t, 1.0, pan)
    elif ty == 'door': add(fx, door(1.0), t - 0.05, 1.0, pan)
    elif ty == 'peg': add(fx, click(1.6, 0.4), t, 1.0, pan)
    elif ty == 'brush': add(fx, brush(e['dur'], 1.0), t, 1.0, -0.3); add(fx, brush(e['dur'], 0.6), t + 0.15, 1.0, 0.4)
    elif ty == 'dip': add(fx, lp(nz(.25), 900) * np.exp(-T(.25) / .08) * 0.05, t, 1.0, 0)
    elif ty == 'glint': add(fx, glock(int(rng.choice([93, 96, 98, 100, 101])), 0.45 if not e.get('big') else 0.8, 1.0), t, 1.0, pan)

# ——— ambience: day room with a few birds → silence → night crickets ———
room = lp(brown(DUR), 400) * 0.01
day = np.interp(np.arange(N) / SR, [0, 6.2, 6.4, 7.2, DUR], [1, 1, 0, 0, 0])
night = np.interp(np.arange(N) / SR, [0, 6.95, 8.0, DUR], [0, 0, 1, 1])
amb[:, 0] += room[:N] * (0.3 + 0.7 * day); amb[:, 1] += room[:N] * (0.3 + 0.7 * day)
for tb in (0.9, 1.15, 2.6, 4.2, 4.35, 5.6): add(amb, chirp(1.0), tb, 1.0, 0.6 if tb % 2 > 1 else -0.6)
cr = crickets(DUR); amb[:, 0] += cr[:N] * night; amb[:, 1] += np.roll(cr, 900)[:N] * night

# ——— narration: Gemini TTS at 1.07× (pitch kept), compressed, a little warmth and near reverb ———
for e in EV:
    if e['type'] != 'voice': continue
    src = os.path.join(HERE, 'voice', e['id'] + '.wav'); fast = os.path.join(HERE, 'out', e['id'] + '_fast.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-af', 'atempo=1.07', fast], check=True)
    v, sr = sf.read(fast); v = soxr.resample(v, sr, SR)
    v = compress(hp(v, 90), thr=.2, ratio=3.0); v = lp(v, 9000)
    ir = nz(.25) * np.exp(-T(.25) / .06); wet = np.convolve(v, ir)[:len(v)]; wet *= 0.12 * np.abs(v).max() / (np.abs(wet).max() + 1e-9)
    add(vox, v + wet, e['t'], 1.0, 0)

# ——— balance: voice ≈10 dB over music by RMS; duck music and foley under the voice ———
def rms(x): x = x[np.abs(x).sum(1) > 1e-4] if x.ndim > 1 else x; return np.sqrt((x ** 2).mean()) if len(x) else 1e-9
vg = 0.30 / rms(vox); vox *= vg
mus *= (0.30 / 10 ** (10 / 20)) / rms(mus)
voiced = uniform_filter1d((np.abs(vox).sum(1) > 0.01).astype(float), int(0.25 * SR))
duck = 1 - 0.35 * np.clip(voiced * 1.5, 0, 1)
mus *= duck[:, None]; fx *= (1 - 0.25 * np.clip(voiced * 1.5, 0, 1))[:, None] * 1.4
mix = mus + fx + amb * 1.2 + vox
mix = mix / (np.abs(mix).max() + 1e-9) * 0.9; mix = np.stack([limit(mix[:, 0]), limit(mix[:, 1])], 1)
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix.astype(np.float32), SR)
print('mix.wav', round(len(mix) / SR, 2), 's; voice rms', round(float(rms(vox)), 3), 'music rms', round(float(rms(mus)), 3))
