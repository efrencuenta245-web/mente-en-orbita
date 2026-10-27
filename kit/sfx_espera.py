"""Efectos de sonido del video extra: la espera tras la vasectomía. Tiempos por fw() (si existe espera_sync.py, los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile
import espera as V

try:
    import espera_sync
    fw = espera_sync.fw
    T = espera_sync.NEWDUR
    OUT = "/home/claude/efectos_espera_sync.wav"
except ImportError:
    fw = lambda x: x
    T = V.DUR
    OUT = "/home/claude/efectos_espera.wav"

sr = 44100
N = int(T * sr)
rng = np.random.RandomState(21)
buf = np.zeros(N)
t_all = np.arange(N) / sr
WT = V.WT


def tt(d):
    return np.arange(int(max(0.01, d) * sr)) / sr


def add(sig, t0, g=1.0):
    i0 = int(fw(t0) * sr)
    if i0 >= N or i0 < 0:
        return
    i1 = min(N, i0 + len(sig))
    buf[i0:i1] += sig[:i1 - i0] * g


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


def beep(f, d=0.09, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.minimum(1, np.minimum(t / 0.005, (d - t) / 0.01)).clip(0, 1) * g * 0.45


def tick(f=1500, d=0.04, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * g * 0.6


def thud(f=70, d=0.3, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * (f + 50 * np.exp(-t * 30)) * t) * np.exp(-t * 12) * g


def chord(fs, t0, d=2.0, g=0.5):
    for k, f in enumerate(fs):
        add(ping(f, d, g / (1 + 0.15 * k)), t0 + 0.06 * k)


def counter_ticks(a, b, n, f=2400, g=0.35):
    for k in range(n):
        u = (k / max(1, n - 1)) ** 0.6
        add(tick(f + 400 * (k % 2), 0.03, g), a + (b - a) * u)


def hiss(d, f0=800, f1=6000, g=1.0):
    return bp(rng.randn(int(d * sr)), f0, f1) * g


def rumble(d, f=160, g=1.0):
    return lp(rng.randn(int(d * sr)), f, 2) * 3.0 * g


def riser(d, f0=200, f1=900, g=0.4):
    t = tt(d)
    f = f0 + (f1 - f0) * (t / d) ** 2
    ph = 2 * np.pi * np.cumsum(f) / sr
    return np.sin(ph) * (t / d) ** 1.5 * g + hp(rng.randn(len(t)), 3000) * (t / d) ** 3 * 0.15


CUTS = V.CUTS


def snip(g=1.0):
    t = tt(0.18)
    click = hp(rng.randn(len(t)), 2500) * np.exp(-t * 60) * 0.9
    ring = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (18 + f / 400)) for f in (2900, 4300, 6100)) * 0.25
    return (click + ring) * g


def clink(f=3200, g=1.0):
    t = tt(0.5)
    return sum(np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (8 + 5 * k)) / k for k in (1, 2.76, 5.4)) * 0.3 * g


def drop(f=900, g=1.0):
    t = tt(0.22)
    fr = f * (1 + 1.4 * np.exp(-t * 30))
    return np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.exp(-t * 18) * 0.5 * g


def sizzle(d=0.8, g=1.0):
    n = int(d * sr)
    x = hp(rng.randn(n), 3500) * (0.5 + 0.5 * (rng.rand(n) > 0.97)) * np.exp(-np.arange(n) / sr * 2.5)
    return x * 0.35 * g


def page(g=1.0):
    t = tt(0.25)
    return bp(rng.randn(len(t)), 1500, 6000) * np.sin(np.pi * t / 0.25) ** 2 * 0.35 * g


def escaner(g=1.0):
    """sonido de marca del escáner de rayos X: barrido ascendente + brillo digital"""
    d = 1.6
    t = tt(d)
    f = 320 + 1900 * (t / d) ** 1.4
    ph = 2 * np.pi * np.cumsum(f) / sr
    sweep = np.sin(ph) * np.sin(np.pi * t / d) ** 0.8 * 0.28
    sweep += np.sin(2 * ph + 0.3) * np.sin(np.pi * t / d) ** 2 * 0.08
    shimmer = sum(np.sin(2 * np.pi * fr * t + k) * (0.5 + 0.5 * np.sin(2 * np.pi * (9 + 3 * k) * t)) for k, fr in enumerate((2637, 3136, 3951))) * 0.035
    shimmer *= np.sin(np.pi * t / d) ** 2
    tick_ = np.zeros_like(t)
    for k in range(12):
        i0 = int((0.08 + k * 0.12) * sr)
        tq = tt(0.02)
        tick_[i0:i0 + len(tq)] += np.sin(2 * np.pi * 5200 * tq) * np.exp(-tq * 220) * 0.12
    return (sweep + shimmer + tick_ + hp(rng.randn(len(t)), 5000) * np.sin(np.pi * t / d) ** 3 * 0.03) * g



CUTS = V.CUTS
ANAT = [(5.25, 33.45)]
pad_ = (np.sin(2 * np.pi * 110 * t_all) + 0.6 * np.sin(2 * np.pi * 164.8 * t_all + 0.4) + 0.4 * np.sin(2 * np.pi * 220.4 * t_all)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t_all))
pad_ += lp(rng.randn(N), 400, 2) * 0.8
pad_ = span(pad_, [(0, 0), (5.2, 0), (5.3, 0.3), (33.4, 0.3), (33.5, 0.0), (V.DUR, 0.0)])
buf += pad_ * 0.22
room = lp(rng.randn(N), 380) * 0.9 + np.sin(2 * np.pi * 120 * t_all) * 0.05
room = span(room, [(0, 0.28), (5.2, 0.28), (5.25, 0), (33.45, 0), (33.5, 0.3), (52.1, 0.3), (52.15, 0.25), (V.DUR, 0.25)])
buf += room * 0.4

# ================= gancho =================
add(clink(3000, 0.5), 0.15)
add(snip(1.2), V.T_SNIP)
add(thud(90, 0.25, 0.5), V.T_SNIP + 0.02)
add(escaner(0.55), WT(0, 5) - 0.8)
for k in range(2):
    add(beep(660 if k == 0 else 520, 0.16, 0.6), WT(0, 6) + k * 0.2)

# ================= escáner =================
add(escaner(1.0), V.T_SCAN)

# ================= comentario =================
add(ping(1320, 0.5, 0.6), 7.45)
add(ping(1760, 0.4, 0.4), 7.6)
for k in range(12):
    add(tick(2200 + 40 * k, 0.04, 0.5), WT(2, 6) - 0.1 + k * (WT(2, 8) + 0.6 - WT(2, 6)) / 12)

# ================= corte =================
add(thud(70, 0.35, 0.6), 11.5)
for k in range(5):
    add(tick(1300, 0.05, 0.35), 12.2 + k * 0.7)

# ================= del otro lado =================
add(riser(1.6, 220, 1000, 0.3), WT(4, 7) - 1.2)
add(thud(60, 0.5, 0.8), WT(4, 9) - 0.25)
add(ping(1046, 0.9, 0.4), WT(4, 9) - 0.2)

# ================= reserva =================
for w_ in ((5, 3), (5, 8), (5, 10)):
    add(tick(2600, 0.05, 0.45), WT(*w_) - 0.1)
counter_ticks(WT(6, 2) - 0.2, 27.2, 20, 2400, 0.3)

# ================= vaciado =================
t0, t1 = WT(7, 2) - 0.2, 33.0
for k in range(1, 23):
    tk = t0 + (t1 - t0) * k / 22.0
    add(tick(2800 - 60 * k, 0.05, 0.45), tk)
    if k % 3 == 1:
        add(whoosh(0.4), tk - 0.05, 0.25)

# ================= laboratorio =================
add(clink(2400, 0.5), 33.8)
counter_ticks(WT(8, 2) - 0.3, WT(8, 4) + 0.4, 7, 2000, 0.3)
chord((784, 1046, 1318), WT(9, 13), 1.0, 0.45)
for k in range(2):
    add(beep(600, 0.12, 0.5), WT(10, 1) + k * 0.18)
counter_ticks(WT(10, 6) - 0.2, WT(10, 9) + 0.3, 4, 2000, 0.3)
chord((784, 1046, 1568), WT(10, 10), 1.2, 0.45)

# ================= mientras =================
add(ping(880, 0.6, 0.5), 47.7)
for k in range(2):
    add(beep(560, 0.16, 0.55), WT(11, 7) + k * 0.2)

# ================= cierre =================
add(ping(1318, 0.5, 0.5), 52.7)
for k in range(2):
    add(ping(1568 if k == 0 else 1175, 0.35, 0.45), WT(12, 12) + k * 0.15)
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), V.T_OUT, 0.6)
chord((1047, 1568, 2093), V.T_OUT + 0.3, 2.4, 0.5)
for ct in CUTS:
    add(whoosh(0.6), ct - 0.3, 0.7)

# ================= MASTER =================
buf = fade(buf, 0.05, 0.4)
peak = np.abs(buf).max()
ref = np.percentile(np.abs(buf), 99.9)
buf = np.tanh(buf / ref * 0.8)
buf = buf / np.abs(buf).max() * 0.6
print("pico previo", round(float(peak), 2), "RMS dBFS", round(float(20 * np.log10(np.sqrt((buf ** 2).mean()))), 1))
st = np.stack([buf, buf], 1)
wavfile.write(OUT, sr, (st * 32767).astype(np.int16))
print("->", OUT)
