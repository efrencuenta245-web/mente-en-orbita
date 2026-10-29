"""Efectos de sonido del reel de la control (tiempos del tl_control.json, ya en la línea de tiempo editada)."""
import json
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

TL = json.load(open('/home/claude/tl_control.json'))
T = TL['dur']
OUT = "/home/claude/efectos_control.wav"
fw = lambda x: x
PA = [p['a'] for p in TL['phrases']]
sr = 44100
N = int(T * sr)
rng = np.random.RandomState(33)
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


def crack(g=1.0):
    t = tt(0.12)
    return hp(rng.randn(len(t)), 1500) * np.exp(-t * 60) * g * 0.8


def cluck(t0, g=0.35):
    for k in range(3):
        d = 0.09
        t = tt(d)
        f = 520 + 260 * np.exp(-t * 30)
        s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / sr)) * 0.3 + np.sin(2 * np.pi * np.cumsum(f) / sr)
        add(bp(s, 400, 2500) * np.sin(np.pi * t / d) * g, t0 + k * 0.16)


CUTS = [max(0.0, a - 0.2) for a in PA[1:]]
END = TL['voice_end']


def click(g=0.6):
    t = tt(0.03)
    return (np.sin(2 * np.pi * 3200 * t) * 0.5 + hp(rng.randn(len(t)), 2000) * 0.5) * np.exp(-t * 200) * g


def buzz(d, f=38, g=0.15):
    t = tt(d)
    return np.sign(np.sin(2 * np.pi * f * 20 * t)) * 0.3 * np.sin(np.pi * t / d) * g


# ================= momentos =================
add(whoosh(0.5), 0.0, 0.6)
for k in range(8):                      # clics del botón en el gancho
    add(click(0.5), 0.45 + k * 1.05)
    add(beep(1800, 0.06, 0.15), 0.47 + k * 1.05)
for k in range(3):
    add(click(0.4), CUTS[0] + 0.5 + k * 1.05)
add(escaner(1.0), CUTS[1] + 0.15)       # escáner (sello)
add(thud(45, 0.9, 0.5), CUTS[1] + 0.2)
counter_ticks(CUTS[2] + 0.4, CUTS[2] + 1.8, 16, 2400, 0.22)   # 940 nm
add(riser(1.6, 200, 900, 0.25), CUTS[3] + 0.6)               # espectro
add(fade(hiss(2.0, 3000, 9000, 0.2), 0.4, 0.6), CUTS[4] + 0.4)  # sensor
add(riser(0.8, 300, 1400, 0.3), CUTS[5] - 0.8)               # 2º gancho
counter_ticks(CUTS[5] + 0.5, CUTS[5] + 2.7, 30, 2600, 0.25)
add(buzz(2.5, 38, 0.25), CUTS[5] + 0.5)
add(ping(880, 0.6, 0.3), CUTS[6] + 1.0)
for i in range(32):                      # pulsos del código
    add(beep(1500 if i % 2 else 1200, 0.04, 0.22), CUTS[7] + 0.3 + i * 0.08)
add(click(0.6), CUTS[8] + 0.9)
chord((523, 659, 784), CUTS[8] + 1.1, 1.2, 0.25)
add(ping(1046, 0.6, 0.3), CUTS[9] + 0.6)
for k in range(2):
    add(thud(120, 0.15, 0.4), CUTS[10] + 0.4 + k * 0.3)
chord((392, 523, 659), CUTS[11] + 1.2, 1.4, 0.22)
for k in range(3):
    add(click(0.5), CUTS[12] + 0.5 + k * 1.05)
for ct in CUTS:
    add(whoosh(0.6), ct - 0.3, 0.6)

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
