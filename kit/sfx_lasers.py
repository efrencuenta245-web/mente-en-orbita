"""Efectos de sonido del video de láseres entre satélites. Tiempos por fw() (si existe lasers_sync.py se usan los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

try:
    import lasers_sync
    fw = lasers_sync.fw
    T = lasers_sync.NEWDUR
    OUT = "/home/claude/efectos_lasers_sync.wav"
except ImportError:
    fw = lambda x: x
    T = 64.6
    OUT = "/home/claude/efectos_lasers.wav"

sr = 44100
N = int(T * sr)
rng = np.random.RandomState(91)
buf = np.zeros(N)
t_all = np.arange(N) / sr


def tt(d):
    return np.arange(int(max(0.01, d) * sr)) / sr


def add(sig, t0, g=1.0):
    i0 = int(fw(t0) * sr)
    if i0 >= N or i0 < 0:
        return
    i1 = min(N, i0 + len(sig))
    buf[i0:i1] += sig[:i1 - i0] * g


def seglen(a, b):
    return max(0.05, fw(b) - fw(a))


def lp(x, f, o=2):
    b, a = butter(o, f / (sr / 2), 'low'); return lfilter(b, a, x)


def hp(x, f, o=2):
    b, a = butter(o, f / (sr / 2), 'high'); return lfilter(b, a, x)


def bp(x, f0, f1, o=2):
    b, a = butter(o, [f0 / (sr / 2), f1 / (sr / 2)], 'band'); return lfilter(b, a, x)


def fade(x, fi, fo):
    x = x.copy(); n = len(x)
    a, b = int(fi * sr), int(fo * sr)
    if a > 0: x[:min(a, n)] *= np.linspace(0, 1, min(a, n))
    if b > 0: x[-min(b, n):] *= np.linspace(1, 0, min(b, n))
    return x


def span(x, pts):
    xs = [fw(a) for a, _ in pts]
    ys = [b for _, b in pts]
    return x * np.interp(t_all[:len(x)], xs, ys)


def whoosh(d=0.7):
    t = tt(d); n = len(t)
    nz = rng.randn(n)
    low = lp(nz, 700) * 3.0
    high = bp(nz, 2000, 7000) * 1.6
    e1 = np.sin(np.pi * np.clip(t / d * 1.5, 0, 1)) ** 2 * (t / d < 0.67)
    e2 = np.sin(np.pi * np.clip((t / d - 0.25) / 0.75, 0, 1)) ** 2
    return fade(low * e1 + high * e2, 0.02, 0.05) * 0.5


def ping(f, d=0.5, g=1.0):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * np.sin(2 * np.pi * 3.01 * f * t)
    return s * np.exp(-t * (5.0 / d)) * g * 0.5


def tick(f=1500, d=0.04, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * g * 0.6


def thud(f=70, d=0.3, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * (f + 50 * np.exp(-t * 30)) * t) * np.exp(-t * 12) * g


def chirp(f0, f1, d, g=1.0, shape=1.0):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / sr
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** shape
    return np.sin(ph) * e * g * 0.5


def chord(fs, t0, d=2.0, g=0.5):
    for k, f in enumerate(fs):
        add(ping(f, d, g / (1 + 0.15 * k)), t0 + 0.06 * k)


def zap(t0, g=1.0):
    """carga y disparo del láser"""
    t = tt(0.45)
    up = np.sin(2 * np.pi * np.cumsum(300 * (1 + 6 * (t / 0.45) ** 2)) / sr) * (t / 0.45) * 0.35
    add(up, t0 - 0.45, g)
    t = tt(0.6)
    f = 2400 * np.exp(-t * 6) + 300
    s = np.sin(2 * np.pi * np.cumsum(f) / sr) + 0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(f * 0.5) / sr))
    add(lp(s, 5000) * np.exp(-t * 5) * 0.4, t0, g)


def beam_hum(a, b, g=1.0, f=220):
    d = seglen(a, b)
    t = tt(d)
    s = (2 * ((f * t) % 1.0) - 1) * 0.5 + np.sin(2 * np.pi * f * 2 * t) * 0.3
    s = lp(s, 1400) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * t))
    add(fade(s, 0.1, 0.25) * 0.18, a, g)


def crickets(a, b, g=1.0):
    d = seglen(a, b)
    out = np.zeros(int(d * sr))
    k = 0
    tc = 0.2
    while tc < d - 0.2:
        for j in range(3):
            tq = tt(0.05)
            i0 = int((tc + j * 0.07) * sr)
            if i0 + len(tq) < len(out):
                out[i0:i0 + len(tq)] += np.sin(2 * np.pi * (4300 + 120 * (k % 3)) * tq) * np.hanning(len(tq)) * 0.22
        tc += 0.32 + rng.uniform(0, 0.08)
        k += 1
    out += lp(rng.randn(len(out)), 600) * 1.0
    add(fade(out, 0.2, 0.3), a, g)


CUTS = (8.55, 13.25, 28.15, 33.55, 41.05, 46.75, 56.45)

# ================= AMBIENTES =================
dr = (np.sin(2 * np.pi * 55 * t_all) + 0.7 * np.sin(2 * np.pi * 82.6 * t_all + 0.4) + 0.4 * np.sin(2 * np.pi * 110.3 * t_all)) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.11 * t_all))
dr += lp(rng.randn(N), 300, 2) * 1.2
dr = span(dr, [(0, 0), (0.3, 0.45), (41.0, 0.45), (41.1, 0), (46.7, 0), (46.9, 0.4), (56.4, 0.4), (56.5, 0)])
buf += dr * 0.33
crickets(41.05, 46.75, 0.55)
crickets(56.45, 64.6, 0.55)

# ================= 1: disparo =================
add(chirp(400, 900, 0.8, 0.25, 1.0), 1.0)
add(tick(1800, 0.05, 0.7), 1.25)
zap(4.85, 1.0)
beam_hum(4.9, 8.5, 1.0)
for k in range(10):
    add(tick(2600 + 90 * (k % 4), 0.025, 0.35), 6.3 + 0.2 * k)
add(tick(1500, 0.05, 0.7), 5.45)

# ================= 2: malla =================
for k in range(28):
    add(ping(1800 + 140 * (k % 7), 0.25, 0.22), 9.0 + k * 0.09 + rng.uniform(0, 0.04))
sh = tt(3.0)
add(sum(np.sin(2 * np.pi * f * sh + q) for q, f in enumerate((1320, 1760, 2217))) * np.sin(np.pi * sh / 3.0) * 0.06, 9.6)
add(tick(1500, 0.05, 0.8), 10.25)

# ================= 3: radio vs láser =================
d = seglen(13.6, 17.3)
t = tt(d)
wub = np.sin(2 * np.pi * (180 + 60 * np.sin(2 * np.pi * 1.0 * t)) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 2.0 * t)) + lp(rng.randn(len(t)), 900) * 0.6
add(fade(wub, 0.2, 0.4) * 0.3, 13.6)
add(tick(1500, 0.05, 0.7), 13.85)
zap(17.85, 0.8)
beam_hum(17.9, 27.9, 0.9, 247)
tc = 20.4
while tc < 22.4:
    add(tick(1200 + 900 * (tc - 20.4) / 2.0, 0.025, 0.4), tc)
    tc += 0.07
add(ping(1760, 0.8, 0.7), 22.45)
add(ping(2349, 0.8, 0.4), 22.6)
sh = tt(2.0)
add(sum(np.sin(2 * np.pi * f * sh + q) * (0.6 + 0.4 * np.sin(2 * np.pi * (4 + q) * sh)) for q, f in enumerate((2093, 2637, 3136))) * np.sin(np.pi * sh / 2.0) * 0.06, 24.3)
add(tick(1500, 0.05, 0.7), 24.65)

# ================= 4: rayos X del terminal =================
t1 = tt(1.0)
add(np.sin(2 * np.pi * (180 + 2200 * t1) * t1) * np.sin(np.pi * t1) ** 0.6 * 0.35, 28.6)
add(hp(rng.randn(len(t1)), 3000) * np.sin(np.pi * t1) ** 2 * 0.1, 28.6)
for ta in (29.6, 30.2, 30.6, 31.6):
    add(ping(1100, 0.2, 0.7), ta)
for k in range(5):
    t_ = tt(0.35)
    add(np.sin(2 * np.pi * (320 + 140 * np.sin(np.pi * t_ / 0.35)) * t_) * np.hanning(len(t_)) * 0.12, 30.7 + 0.5 * k)
beam_hum(28.2, 33.5, 0.6, 262)

# ================= 5: persecución =================
add(whoosh(1.2), 33.7, 0.9)
add(lp(rng.randn(int(seglen(33.6, 41.0) * sr)), 160) * 0.5, 33.6)
beam_hum(33.6, 41.0, 0.8, 233)
tc = 34.3
while tc < 36.8:
    add(np.sin(2 * np.pi * 1900 * tt(0.05)) * np.hanning(int(0.05 * sr)) * 0.16, tc)
    tc += 0.16
chord((1318, 1760), 36.85, 0.9, 0.45)
add(tick(1500, 0.05, 0.8), 34.45)
add(tick(1500, 0.05, 0.8), 37.3)

# ================= 6: la moneda =================
add(tick(900, 0.06, 0.9), 41.4)
add(np.sin(2 * np.pi * 1400 * tt(1.2)) * np.exp(-tt(1.2) * 2.5) * 0.06, 41.45)
t_ = tt(1.0)
add((np.sin(2 * np.pi * 3520 * t_) + 0.5 * np.sin(2 * np.pi * 5280 * t_) + 0.3 * np.sin(2 * np.pi * 7040 * t_)) * np.exp(-t_ * 4) * 0.2, 42.1)
add(tick(1500, 0.05, 0.8), 43.85)

# ================= 7: carrera =================
for k in range(3):
    add(np.sin(2 * np.pi * 880 * tt(0.12)) * 0.18, 46.9 + 0.17 * k)
add(np.sin(2 * np.pi * 1760 * tt(0.25)) * np.exp(-tt(0.25) * 6) * 0.25, 47.4)
add(chirp(500, 2600, seglen(47.4, 50.6), 0.35, 0.8), 47.4)
add(chirp(300, 900, seglen(47.4, 52.3), 0.3, 0.8), 47.4)
chord((1047, 1318, 1568, 2093), 50.65, 1.8, 0.55)
add(ping(330, 1.0, 0.7), 52.3)
add(ping(262, 1.0, 0.5), 52.45)

# ================= 8: nubes y radio =================
add(hp(rng.randn(int(0.9 * sr)), 2500) * np.exp(-tt(0.9) * 3) * 0.25, 57.0)
beam_hum(56.9, 59.9, 0.5, 220)
d = seglen(58.3, 60.9)
t = tt(d)
add(fade(np.sin(2 * np.pi * (520 + 80 * np.sin(2 * np.pi * 3 * t)) * t) * 0.12, 0.2, 0.3), 58.3)
add(ping(1318, 0.5, 0.6), 58.95)
add(ping(1760, 0.6, 0.5), 59.1)

# ================= cierre y cortes =================
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), 61.1, 0.6)
chord((1047, 1568, 2093), 61.4, 2.4, 0.5)
for ct in CUTS:
    add(whoosh(0.6), ct - 0.3, 0.8)

# ================= MASTER =================
buf = fade(buf, 0.05, 1.0)
peak = np.abs(buf).max()
buf = buf / peak * 0.6
print("pico previo", round(float(peak), 2), "RMS dBFS", round(float(20 * np.log10(np.sqrt((buf ** 2).mean()))), 1))
st = np.stack([buf, buf], 1)
wavfile.write(OUT, sr, (st * 32767).astype(np.int16))
rms = [int(20 * np.log10(np.sqrt((buf[i * sr:(i + 1) * sr] ** 2).mean()) + 1e-6)) for i in range(0, int(T))]
print(rms)
print("->", OUT)
