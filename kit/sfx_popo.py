"""Efectos de sonido del video del Popocatépetl. Tiempos por fw() (si existe popo_sync.py, los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile
import popo as V

try:
    import popo_sync
    fw = popo_sync.fw
    T = popo_sync.NEWDUR
    OUT = "/home/claude/efectos_popo_sync.wav"
except ImportError:
    fw = lambda x: x
    T = V.DUR
    OUT = "/home/claude/efectos_popo.wav"

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


def exhal(g=1.0, d=0.9):
    t = tt(d)
    nz = bp(rng.randn(len(t)), 250, 1800) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return nz * 0.55 * g


# ================= AMBIENTES =================
city = lp(rng.randn(N), 600) * 0.7 + bp(rng.randn(N), 800, 2500) * 0.08
city = span(city, [(0, 0.0), (0.2, 0.35), (1.2, 0.3), (5.9, 0.12), (6.05, 0.0), (46.45, 0.0), (46.6, 0.35), (V.DUR, 0.3)])
buf += city * 0.45
for k in range(8):
    t0 = 0.4 + k * 0.62
    t3 = tt(0.14)
    add(np.sin(2 * np.pi * (3200 + 500 * (k % 3) + 700 * np.sin(2 * np.pi * 16 * t3)) * t3) * np.exp(-t3 * 18) * 0.08, t0)
for k in range(8):
    t0 = 46.8 + k * 0.7
    t3 = tt(0.14)
    add(np.sin(2 * np.pi * (3400 + 400 * (k % 3) + 700 * np.sin(2 * np.pi * 16 * t3)) * t3) * np.exp(-t3 * 18) * 0.07, t0)
deep = (np.sin(2 * np.pi * 41 * t_all) + 0.6 * np.sin(2 * np.pi * 61.5 * t_all + 0.4)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * t_all))
deep += lp(rng.randn(N), 120, 2) * 1.6
deep = span(deep, [(0, 0), (6.05, 0), (6.2, 0.45), (26.8, 0.45), (26.9, 0.0), (37.35, 0.0), (37.5, 0.3), (41.6, 0.3), (41.65, 0.0)])
buf += deep * 0.35
wind = lp(rng.randn(N), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.21 * t_all))
wind = span(wind, [(0, 0), (26.85, 0), (27.0, 0.4), (32.4, 0.4), (32.45, 0), (41.65, 0), (41.8, 0.55), (46.4, 0.55), (46.45, 0)])
buf += wind * 0.45
jet = bp(rng.randn(N), 300, 3000) * 0.4 + np.sin(2 * np.pi * 180 * t_all) * 0.03
jet = span(jet, [(0, 0), (32.45, 0), (32.6, 0.35), (37.3, 0.35), (37.35, 0)])
buf += jet * 0.4

# ================= gancho: exhalaciones y vuelo de 72 km =================
for k, ti in enumerate(np.linspace(0.35, 5.55, 42)):
    if k % 3 == 0:
        add(exhal(0.35, 0.7), ti)
    add(tick(2400 + 300 * (k % 2), 0.025, 0.16), ti)
add(whoosh(3.2), 1.0, 0.8)
add(riser(4.2, 120, 500, 0.18), 1.2)

# ================= escáner (sello) =================
add(escaner(1.0), V.T_SCAN - 0.05)
add(thud(45, 0.9, 0.6), V.T_SCAN)
chord((392, 523, 659), V.WT(2, 4), 1.4, 0.28)

# ================= magma y gases =================
bub = np.zeros(int(7.0 * sr))
for k in range(70):
    i0 = rng.randint(0, len(bub) - 3000)
    tq = tt(0.06)
    fr = rng.uniform(200, 520)
    bub[i0:i0 + len(tq)] += np.sin(2 * np.pi * fr * (1 + 2 * tq) * tq) * np.exp(-tq * 50) * 0.25
add(fade(bub, 0.4, 0.5), 11.3)
for ti in np.linspace(12.0, 18.4, 9):
    add(exhal(0.5, 0.9), ti)

# ================= tomografía =================
for (tq, p_) in V.QUAKES:
    add(thud(55 + 10 * (int(tq * 10) % 3), 0.4, 0.45), tq)
    add(ping(1568, 0.25, 0.15), tq + 0.3)
for k in range(30):
    add(beep(1800 + 400 * ((k * 3) % 4), 0.03, 0.18), V.WT(5, 4) - 0.3 + k * 0.15)
counter_ticks(V.WT(5, 15) - 0.3, V.WT(5, 17) + 0.3, 24, 2600, 0.2)

# ================= bolsas de magma =================
add(np.sin(2 * np.pi * 55 * tt(2.4)) * np.sin(np.pi * tt(2.4) / 2.4) * 0.5, 24.0)
chord((330, 415, 494), V.WT(6, 2), 1.6, 0.3)

# ================= explosión =================
add(riser(2.4, 60, 260, 0.35), V.T_BOOM - 2.4)
boom = lp(rng.randn(int(3.0 * sr)), 180, 2) * 4.0 * np.exp(-tt(3.0) * 1.4) + hp(rng.randn(int(3.0 * sr)), 1200) * np.exp(-tt(3.0) * 4) * 1.2
add(boom, V.T_BOOM)
add(thud(32, 2.0, 1.6), V.T_BOOM)
crk = np.zeros(int(2.4 * sr))
for k in range(120):
    i0 = rng.randint(0, len(crk) - 2000)
    tq = tt(0.02)
    crk[i0:i0 + len(tq)] += hp(rng.randn(len(tq)), 2500) * np.exp(-tq * 200) * rng.uniform(0.2, 0.7) * np.exp(-i0 / sr * 1.0)
add(crk, V.T_BOOM + 0.1, 0.7)
add(whoosh(1.6), V.WT(7, 14) - 0.3, 0.6)

# ================= aeropuerto =================
for (f1, f2) in ((659, 523),):
    add(ping(f1, 0.9, 0.5), 32.9)
    add(ping(f2, 1.2, 0.5), 33.3)
for i in range(4):
    add(beep(900, 0.07, 0.4), 33.4 + 0.25 * i)

# ================= mapa =================
add(riser(1.4, 200, 900, 0.2), 37.5)
add(ping(1046, 1.0, 0.45), 38.9)
counter_ticks(V.WT(9, 1) - 0.2, V.WT(9, 4) + 0.3, 18, 2400, 0.22)

# ================= estación =================
for k in range(4):
    add(beep(1300, 0.06, 0.3), 42.3 + 0.4 * k)
add(ping(880, 0.6, 0.45), V.WT(10, 7))
add(ping(1175, 0.6, 0.35), V.WT(10, 8))

# ================= cierre (azotea) =================
add(clink := None or tick(2000, 0.03, 0.3), V.WT(11, 0))
for k, ti in enumerate((V.WT(11, 14), V.WT(11, 15))):
    add(beep(1320 if k == 0 else 880, 0.12, 0.5), ti)
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
rms = [int(20 * np.log10(np.sqrt((buf[i * sr:(i + 1) * sr] ** 2).mean()) + 1e-6)) for i in range(0, int(T))]
print(rms)
print("->", OUT)
