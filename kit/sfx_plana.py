"""Efectos de sonido del reel de la Tierra plana (tiempos del tl_plana.json, ya en la línea de tiempo editada)."""
import json
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

TL = json.load(open('/home/claude/tl_plana.json'))
T = TL['dur']
OUT = "/home/claude/efectos_plana.wav"
fw = lambda x: x
PA = [p['a'] for p in TL['phrases']]
sr = 44100
N = int(T * sr)
rng = np.random.RandomState(21)
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

CUTS = [max(0.0, a - 0.2) for a in PA[1:]]
# gancho: giro de la tortilla y cambio a Tierra
add(whoosh(1.2), 0.0, 0.6)
add(riser(1.6, 200, 900, 0.22), PA[0] + 0.4)
add(ping(1046, 0.8, 0.4), PA[0] + 1.6 + 0.2)
chord((392, 523, 659), PA[0] + 2.0, 1.4, 0.25)
# escáner de rayos X (sello)
add(escaner(1.0), CUTS[0] + 0.15)
add(thud(45, 0.9, 0.6), CUTS[0] + 0.2)
# flechas de gravedad
for k in range(12):
    add(tick(1800 + 120 * k, 0.03, 0.25), CUTS[1] + 0.5 + k * 0.17)
add(thud(60, 0.5, 0.5), CUTS[1] + 2.6)
# grados de inclinación
counter_ticks(CUTS[2] + 0.8, CUTS[2] + 2.4, 16, 2400, 0.22)
# pasos en la cuesta
for k in range(int((CUTS[4] - CUTS[3]) / 0.45)):
    add(thud(90, 0.12, 0.35), CUTS[3] + 0.2 + k * 0.45)
# agua al centro
add(fade(bp(rng.randn(int(2.4 * sr)), 300, 1800) * 0.4, 0.4, 0.8), CUTS[4] + 0.2)
add(ping(784, 0.6, 0.35), CUTS[4] + 2.6)
# Everest: contador del aire
add(np.sin(2 * np.pi * 220 * tt(2.0)) * np.sin(np.pi * tt(2.0) / 2.0) * 0.15, CUTS[5] + 0.3)
counter_ticks(CUTS[5] + 0.3, CUTS[5] + 2.5, 22, 2600, 0.2)
# hipótesis
for k in range(5):
    add(tick(1500, 0.03, 0.3), CUTS[6] + 0.3 + k * 0.25)
add(beep(1320, 0.12, 0.45), CUTS[6] + 2.2)
add(beep(880, 0.12, 0.45), CUTS[6] + 2.4)
# gen
for k in range(20):
    add(beep(1600 + 300 * ((k * 3) % 4), 0.03, 0.15), CUTS[7] + 0.4 + k * 0.08)
chord((330, 415, 494), CUTS[7] + 1.6, 1.4, 0.25)
# evolución
add(riser(1.6, 120, 500, 0.2), CUTS[8] + 0.4)
add(ping(659, 0.7, 0.35), CUTS[8] + 3.0)
# centro
chord((392, 494, 587), CUTS[9] + 0.3, 2.0, 0.25)
# colapso a bola
add(riser(2.8, 50, 240, 0.35), CUTS[10] + 0.9)
add(rumble(2.8, 120, 0.4), CUTS[10] + 0.9)
add(thud(40, 1.4, 1.0), CUTS[10] + 3.7)
# cierre
for k, dt in enumerate((1.4, 1.6)):
    add(beep(1320 if k == 0 else 880, 0.12, 0.45), CUTS[11] + dt)
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), T - 2.6, 0.6)
add(whoosh(1.0), T - 1.6, 0.6)
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
