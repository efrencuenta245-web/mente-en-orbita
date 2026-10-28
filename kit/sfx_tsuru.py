"""Efectos de sonido del reel de del Tsuru (tiempos del tl_tsuru.json, ya en la línea de tiempo editada)."""
import json
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

TL = json.load(open('/home/claude/tl_tsuru.json'))
T = TL['dur']
OUT = "/home/claude/efectos_tsuru.wav"
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




def engine_hum(d, f0=34, f1=34, g=1.0):
    """Motor de 4 cilindros: zumbido grave con armónicos (sube de f0 a f1)."""
    t = tt(d)
    f = f0 + (f1 - f0) * (t / d)
    ph = 2 * np.pi * np.cumsum(f) / sr
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(4 * ph + 0.5) + 0.12 * np.sign(np.sin(2 * ph))
    return lp(s, 900) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * t)) * g * 0.25


def crash_hit(g=1.0):
    d = 1.6
    t = tt(d)
    nz = rng.randn(len(t))
    body = lp(nz, 1800) * np.exp(-t * 6) * 1.4
    metal = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (4 + k)) for k, f in enumerate((310, 523, 787, 1190))) * 0.25
    glass = hp(nz, 5000) * np.exp(-t * 3) * (np.sin(2 * np.pi * 23 * t) > 0.3) * 0.5
    out = (body + metal + glass) * g
    th = thud(38, 1.2, 1.2 * g)
    out[:len(th)] += th
    return out


def buzz(d=0.35, g=1.0):
    t = tt(d)
    return np.sign(np.sin(2 * np.pi * 140 * t)) * 0.18 * fade(np.ones(len(t)), 0.01, 0.05) * g


def shutter(g=1.0):
    t = tt(0.12)
    return (hp(rng.randn(len(t)), 2500) * np.exp(-t * 60) + hp(rng.randn(len(t)), 2500) * np.exp(-np.maximum(0, t - 0.06) * 60) * (t > 0.06)) * 0.35 * g


def word_t(i, pre, default):
    w = [x[1] for x in TL['phrases'][i]['words'] if x[0].startswith(pre)]
    return w[0] if w else default


CUTS = [max(0.0, a - 0.2) for a in PA[1:]]
END = [CUTS[i] if i < len(CUTS) else T for i in range(len(PA))]

# ================= AMBIENTES =================
traffic = lp(rng.randn(N), 500) * 1.2 + bp(rng.randn(N), 900, 2500) * 0.25
traffic = span(traffic, [(0, 0.5), (CUTS[0], 0.5), (CUTS[0] + 0.1, 0), (CUTS[4], 0), (CUTS[4] + 0.1, 0.45), (CUTS[5], 0.45),
                         (CUTS[5] + 0.1, 0), (CUTS[11], 0), (CUTS[11] + 0.3, 0.4), (T, 0.4)])
buf += traffic * 0.3
for th, f in ((2.6, 420), (CUTS[4] + 1.0, 380), (CUTS[11] + 2.5, 440)):  # claxon lejano
    add(fade(bp(np.sign(np.sin(2 * np.pi * f * tt(0.35))), 300, 1500) * 0.06, 0.02, 0.1), th)
deep = (np.sin(2 * np.pi * 41 * t_all) + 0.6 * np.sin(2 * np.pi * 61.5 * t_all + 0.4)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * t_all))
deep = span(deep, [(0, 0), (CUTS[0], 0), (CUTS[0] + 0.2, 0.4), (CUTS[1], 0.4), (CUTS[1] + 0.1, 0), (CUTS[6], 0), (CUTS[6] + 0.2, 0.4),
                   (CUTS[7], 0.4), (CUTS[7] + 0.1, 0), (CUTS[8], 0), (CUTS[8] + 0.3, 0.55), (CUTS[9], 0.55), (CUTS[9] + 0.2, 0)])
buf += deep * 0.3
factory = bp(rng.randn(N), 150, 900) * 0.8 + np.sin(2 * np.pi * 100 * t_all) * 0.05
factory = span(factory, [(0, 0), (CUTS[2], 0), (CUTS[2] + 0.2, 0.5), (CUTS[3], 0.5), (CUTS[3] + 0.1, 0)])
buf += factory * 0.35

# ================= gancho: el taxi llega, 0 estrellas y contador =================
add(engine_hum(2.0, 70, 32, 1.6), 0.0)
add(engine_hum(END[0] - 2.0, 32, 32, 0.8), 2.0)
add(whoosh(1.4), 0.1, 0.7)
ts = word_t(0, 'sacó', 1.4)
ta = word_t(0, 'aun', 3.9)
for k in range(5):
    add(beep(880 - k * 90, 0.09, 0.35), ts + 0.05 + k * 0.1)
add(thud(55, 0.5, 0.5), ts + 0.6)
counter_ticks(ta, ta + 2.4, 30, 2400, 0.25)
chord((523, 659, 784), ta + 2.4, 1.4, 0.3)
# escáner (sello) al revelar el interior
add(escaner(1.0), CUTS[0] + 0.1)
add(thud(45, 0.9, 0.5), CUTS[0] + 0.15)
# motor: pistones y llave de mecánico (matraca)
add(engine_hum(END[2] - CUTS[1], 30, 30, 1.0), CUTS[1])
for k in range(int((END[2] - CUTS[1] - 1.0) / 0.4)):
    for j in range(4):
        add(tick(1700 + 300 * j, 0.012, 0.14), CUTS[1] + 0.8 + k * 0.4 + j * 0.022)
# planta: soldadura, golpes y contador de años
for k in range(6):
    add(fade(hp(rng.randn(int(0.35 * sr)), 3000) * 0.35, 0.01, 0.1), CUTS[2] + 0.3 + k * 0.6)
    add(thud(110, 0.15, 0.4), CUTS[2] + 0.55 + k * 0.6)
counter_ticks(CUTS[2] + 0.4, CUTS[2] + 3.0, 33, 2200, 0.2)
# refacciones: "=" y explosión de piezas
add(ping(784, 0.6, 0.35), CUTS[3] + 0.8)
th = word_t(4, 'hay', CUTS[3] + 2.4)
add(whoosh(0.9), th - 0.2, 0.9)
for k in range(6):
    add(tick(900 + 200 * k, 0.04, 0.3), th + 0.3 + k * 0.09)
# taxi: el Vocho se va y llega el Tsuru; fotos
add(engine_hum(1.6, 48, 30, 0.9), CUTS[4] + 0.05)
add(whoosh(1.0), CUTS[4] + 0.3, 0.6)
for k in range(3):
    add(shutter(1.0), CUTS[4] + 1.6 + k * 0.25)
# ventas: fotos y columnas
for k in range(3):
    add(shutter(0.8), CUTS[5] + 0.1 + k * 0.2)
tb = word_t(6, '2.4', CUTS[5] + 2.95) - 0.35
add(riser(1.6, 160, 640, 0.25), tb)
counter_ticks(tb, tb + 1.6, 18, 2600, 0.2)
add(ping(1046, 0.8, 0.4), tb + 1.7)
# lo que no tenía: escáner y alarmas
add(escaner(0.8), CUTS[6] + 0.05)
add(buzz(0.4, 1.0), CUTS[6] + 0.85)
tf = word_t(7, 'frenos', CUTS[6] + 3.0) - 0.2
add(buzz(0.4, 1.0), tf + 0.25)
# choque
add(engine_hum(0.9, 40, 70, 1.2), CUTS[7])
add(whoosh(0.9), CUTS[7] + 0.1, 0.8)
add(crash_hit(1.0), CUTS[7] + 0.9)
for k in range(5):
    add(beep(660, 0.08, 0.25), CUTS[7] + 1.4 + k * 0.12)
# muertes: tictac lento y grave
for k in range(14):
    add(tick(700, 0.05, 0.3), CUTS[8] + 0.3 + k * 0.29)
add(thud(40, 1.4, 0.6), CUTS[8] + 4.3)
# norma (sello) y el último Tsuru
add(thud(80, 0.3, 0.9), CUTS[9] + 0.15)
add(buzz(0.3, 0.8), CUTS[9] + 0.95)
tl_ = word_t(10, '2017', CUTS[9] + 2.3) - 0.3
add(engine_hum(2.0, 40, 30, 0.8), tl_)
chord((392, 494, 587), tl_ + 0.5, 2.2, 0.28)
# cierre de la planta: luces que se apagan
for k in range(10):
    add(thud(160, 0.08, 0.5), CUTS[10] + 0.8 + (k + 1) * 0.3)
    add(tick(1200, 0.02, 0.3), CUTS[10] + 0.8 + (k + 1) * 0.3)
counter_ticks(CUTS[10], CUTS[10] + 2.4, 24, 2000, 0.18)
add(thud(35, 1.6, 0.8), CUTS[10] + 4.0)
# cierre Sí/No y loop (el taxi vuelve a llegar)
for k, dt in enumerate((1.4, 1.6)):
    add(beep(1320 if k == 0 else 880, 0.12, 0.45), CUTS[11] + dt)
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), T - 3.6, 0.6)
add(engine_hum(1.6, 70, 40, 1.4), T - 1.6)
add(whoosh(1.2), T - 1.5, 0.7)
for ct in CUTS:
    add(whoosh(0.6), ct - 0.3, 0.7)

# ================= MASTER =================
buf = fade(buf, 0.05, 0.05)
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
