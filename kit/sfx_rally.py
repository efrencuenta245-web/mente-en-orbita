"""Efectos de sonido del video de autos de rally. Tiempos por fw() (si existe rally_sync.py, los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile
import rally as V

try:
    import rally_sync
    fw = rally_sync.fw
    T = rally_sync.NEWDUR
    OUT = "/home/claude/efectos_rally_sync.wav"
except ImportError:
    fw = lambda x: x
    T = V.DUR
    OUT = "/home/claude/efectos_rally.wav"

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




def engine(rpm_pts, d, g=1.0, lpf=5000):
    """motor 4 cilindros turbo: armónicos del encendido + ruido modulado"""
    t = tt(d)
    rpm = np.interp(t, [a for a, _ in rpm_pts], [b for _, b in rpm_pts])
    f = rpm / 30.0
    ph = 2 * np.pi * np.cumsum(f) / sr
    s = sum(np.sin(k * ph + 0.3 * k) / k ** 0.9 for k in range(1, 9))
    s += 0.5 * np.sin(0.5 * ph)
    nz = bp(rng.randn(len(t)), 300, 4000) * (0.5 + 0.5 * np.sin(ph)) * 0.8
    return lp(s * 0.35 + nz * 0.3, lpf) * g


def crunch(d, g=1.0):
    n = bp(rng.randn(int(d * sr)), 1500, 7000)
    m = (rng.rand(int(d * sr)) < 0.004).astype(float)
    m = lp(m, 900) * 25
    return (n * 0.25 + hp(m * rng.randn(len(m)), 800)) * g


def bang(g=1.0):
    d = 0.35
    t = tt(d)
    return (lp(rng.randn(len(t)), 900) * 3.0 * np.exp(-t * 22) + hp(rng.randn(len(t)), 2000) * np.exp(-t * 60) * 0.6 + thud(60, d, 0.6)[:len(t)]) * g


TK, SL, TL = V.TK, V.SLOW, V.TAU_LAND
T_LAND = TK + TL / SL

# ================= gancho: acercamiento, despegue y vuelo en cámara lenta =================
add(fade(engine([(0, 6900), (TK - 0.3, 7300), (TK, 7600)], TK + 0.1, 1.0), 0.05, 0.1), 0.0)
add(fade(crunch(TK, 0.6), 0.05, 0.1), 0.0)
fly = engine([(0, 7600 * 0.55), (0.5, 8200 * 0.5), (T_LAND - TK, 8400 * 0.5)], T_LAND - TK + 0.2, 0.9, 1400)
add(fade(fly, 0.05, 0.1), TK)
add(whoosh(T_LAND - TK + 0.3), TK - 0.1, 1.0)
add(riser(T_LAND - TK, 80, 300, 0.25), TK)
add(thud(38, 1.4, 1.8), T_LAND)
add(lp(rng.randn(int(1.6 * sr)), 300) * 4 * np.exp(-tt(1.6) * 3), T_LAND, 0.8)
add(fade(crunch(1.0, 0.9), 0.0, 0.5), T_LAND)
add(fade(engine([(0, 4000), (0.4, 3600)], 0.8, 0.8, 1400), 0.05, 0.4), T_LAND)
for k in range(10):
    add(tick(2400 + 300 * (k % 2), 0.025, 0.16), TK + 0.1 + k * (T_LAND - TK) / 10)

# ================= escáner (sello) y volcadura =================
add(escaner(1.0), V.T_SCAN - 0.05)
add(thud(45, 0.9, 0.6), V.T_SCAN)
chord((392, 523, 659), V.WT(2, 3), 1.4, 0.28)
add(whoosh(1.4), V.WT(2, 9) - 0.2, 0.8)
add(thud(50, 0.6, 0.9), V.WT(2, 13) + 0.4)
add(ping(1175, 0.8, 0.35), V.WT(2, 13) + 0.45)

# ================= 4x4 en grava =================
add(fade(engine([(0, 6200), (1.2, 6800), (1.5, 5200), (2.4, 6600), (3.8, 7000)], 3.8, 0.9), 0.1, 0.2), 11.85)
add(fade(crunch(3.8, 1.0), 0.1, 0.2), 11.85)
chord((523, 659, 784), V.WT(3, 2), 1.2, 0.22)

# ================= aterrizaje: amortiguador =================
add(fade(lp(rng.randn(int(4 * sr)), 200) * 1.2, 0.2, 0.3), 15.65)
add(thud(36, 1.6, 1.4), 15.65 + (V.TAU_LAND - (V.TAU_LAND - 0.08)) / 0.07)
for k in range(8):
    add(np.sin(2 * np.pi * rng.uniform(180, 380) * tt(0.08)) * np.exp(-tt(0.08) * 40) * 0.25, V.WT(4, 8) + k * 0.12)
add(ping(784, 0.6, 0.3), V.WT(4, 3))

# ================= 5 G =================
add(thud(34, 1.4, 1.3), 19.65 + 0.10 / 0.09)
counter_ticks(19.9, 21.6, 14, 2600, 0.2)
add(riser(1.6, 120, 600, 0.22), 19.8)

# ================= antilag =================
add(fade(engine([(0, 5200), (0.4, 3000), (3.4, 3200)], 3.4, 0.6, 2500), 0.1, 0.2), 22.45)
for tb in (22.9, 23.35, 23.6, 24.2, 24.45, 24.9, 25.3, 25.55):
    add(bang(1.0), tb)

# ================= turbo =================
tw = tt(4.0)
fwh = 1800 + 2600 * np.clip(tw / 2.5, 0, 1)
whistle = np.sin(2 * np.pi * np.cumsum(fwh) / sr) * 0.12 + bp(rng.randn(len(tw)), 2500, 6000) * 0.25
add(fade(whistle, 0.3, 0.4), 25.85)
for k in range(8):
    add(bang(0.35), 26.3 + k * 0.45)
add(ping(1046, 0.7, 0.3), V.WT(7, 9))

# ================= cabina y copiloto =================
add(fade(engine([(0, 6400), (1.5, 7200), (1.7, 5600), (3.2, 7000), (3.4, 5800), (4.8, 6900)], 4.8, 0.55, 2200), 0.1, 0.2), 29.85)
add(fade(crunch(4.8, 0.5), 0.1, 0.2), 29.85)
for ta in (30.3, 31.4, 32.5, 33.4):
    add(beep(1500, 0.06, 0.3), ta)

# ================= Guanajuato =================
wind = lp(rng.randn(int(5.2 * sr)), 600) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * tt(5.2)))
add(fade(wind * 0.8, 0.3, 0.3), 34.65)
add(riser(4.6, 150, 700, 0.18), 34.9)
counter_ticks(V.WT(9, 6), 39.6, 26, 2400, 0.18)
add(ping(1175, 0.9, 0.4), 39.5)

# ================= aire delgado =================
pad = sum(np.sin(2 * np.pi * f * tt(4.8)) for f in (220, 277, 330)) * 0.05
add(fade(pad, 0.4, 0.4), 39.85)
for k in range(6):
    add(beep(1200 - k * 80, 0.07, 0.3), V.WT(10, 9) - 0.4 + k * 0.18)

# ================= cierre (loop al salto) =================
add(fade(engine([(0, 6600), (5.6, 7300)], 5.6, 0.8), 0.6, 0.6), 44.65)
add(fade(crunch(5.6, 0.5), 0.6, 0.6), 44.65)
for k, ti in enumerate((V.WT(11, 10), V.WT(11, 12))):
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
