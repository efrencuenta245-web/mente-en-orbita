"""Efectos de sonido del video de relatividad. Tiempos por fw() (si existe tiempo_sync.py se usan los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

try:
    import tiempo_sync
    fw = tiempo_sync.fw
    T = tiempo_sync.NEWDUR
    OUT = "/home/claude/efectos_tiempo_sync.wav"
except ImportError:
    fw = lambda x: x
    T = 65.8
    OUT = "/home/claude/efectos_tiempo.wav"

sr = 44100
N = int(T * sr)
rng = np.random.RandomState(17)
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


def add_abs(sig, t_new, g=1.0):
    i0 = int(t_new * sr)
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


def tick(f=1500, d=0.04, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * g * 0.6


def clock_tick(f=2200, g=1.0):
    t = tt(0.05)
    s = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.51 * t)) * np.exp(-t * 120)
    return s * g * 0.5 + hp(rng.randn(len(t)), 3000) * np.exp(-t * 200) * 0.15 * g


def thud(f=70, d=0.3, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * (f + 50 * np.exp(-t * 30)) * t) * np.exp(-t * 12) * g


def chord(fs, t0, d=2.0, g=0.5):
    for k, f in enumerate(fs):
        add(ping(f, d, g / (1 + 0.15 * k)), t0 + 0.06 * k)


def ticks(a, b, rate, f, g=1.0, phase=0.0):
    """tic-tac en tiempo nuevo entre a y b (tiempo viejo), a 'rate' tics por segundo"""
    ta, tb = fw(a), fw(b)
    k = 0
    tc = ta + phase
    while tc < tb:
        add_abs(clock_tick(f if k % 2 == 0 else f * 0.8, g), tc)
        tc += 1.0 / rate
        k += 1


CUTS = (7.25, 12.65, 24.75, 38.45, 52.25, 57.95)

# ================= AMBIENTES =================
dr = (np.sin(2 * np.pi * 55 * t_all) + 0.7 * np.sin(2 * np.pi * 82.6 * t_all + 0.4) + 0.4 * np.sin(2 * np.pi * 110.3 * t_all)) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.11 * t_all))
dr += lp(rng.randn(N), 300, 2) * 1.2
dr = span(dr, [(0, 0), (0.3, 0.4), (52.1, 0.4), (52.3, 0)])
buf += dr * 0.3
room = lp(rng.randn(N), 420) * 0.9 + np.sin(2 * np.pi * 60 * t_all) * 0.04
room = span(room, [(0, 0), (52.2, 0), (52.5, 0.3), (57.8, 0.3), (58.0, 0.35), (65.8, 0.25)])
buf += room * 0.45
fan = bp(rng.randn(N), 200, 1500) * 0.8 + np.sin(2 * np.pi * 120 * t_all) * 0.08
fan = span(fan, [(0, 0), (57.9, 0), (58.2, 0.3), (65.8, 0.25)])
buf += fan * 0.35

# ================= gancho: dos relojes que se desfasan =================
ticks(0.4, 7.1, 1.0, 1300, 0.55)
ticks(0.4, 7.1, 1.06, 2100, 0.45, 0.02)
add(ping(523, 1.5, 0.6), 4.75)
add(ping(784, 1.5, 0.5), 4.85)
add(thud(50, 0.8, 0.6), 4.7)

# ================= malla =================
t1 = tt(2.0)
add(np.sin(2 * np.pi * (60 + 30 * t1) * t1) * np.sin(np.pi * t1 / 2.0) * 0.5, 7.6)
add(whoosh(0.8), 10.3, 0.7)
t2 = tt(1.2)
add(np.sin(2 * np.pi * (140 - 70 * t2 / 1.2) * t2) * np.exp(-t2 * 2) * 0.6, 11.3)
add(tick(1500, 0.05, 0.7), 11.05)

# ================= reloj de luz =================
for (period, f, g) in ((1.0, 1760, 0.45), (1.0 * np.sqrt(1 + (1.6 / 6.4) ** 2) * 1.6, 1175, 0.45)):
    tc = 12.9 + period / 2
    while tc < 17.6:
        add(ping(f, 0.25, g), tc)
        tc += period / 2
# GPS a 14,000 km/h
add(whoosh(1.4), 17.8, 1.0)
add(lp(rng.randn(int(2.0 * sr)), 400) * np.sin(np.pi * tt(2.0) / 2.0) * 0.5, 18.0)
add(tick(1500, 0.05, 0.8), 18.45)
add(ping(330, 0.8, 0.7), 21.45)
add(ping(262, 0.8, 0.5), 21.6)

# ================= gravedad =================
add(np.sin(2 * np.pi * 45 * tt(3.0)) * np.sin(np.pi * tt(3.0) / 3.0) * 0.5, 25.0)
ticks(25.4, 34.4, 0.8, 1100, 0.35)
ticks(29.4, 34.4, 1.25, 2300, 0.35, 0.1)
add(ping(988, 0.8, 0.7), 31.65)
add(ping(1318, 0.8, 0.5), 31.8)
add(thud(60, 0.4, 0.7), 34.95)
add(thud(60, 0.4, 0.7), 35.45)
chord((784, 988, 1175, 1568), 35.95, 1.8, 0.55)

# ================= Estación Espacial =================
add(whoosh(1.3), 38.5, 0.9)
add(lp(rng.randn(int(seglen := 4.0 * sr)), 300) * 0.0, 38.5)
add(tick(1500, 0.05, 0.8), 39.25)
add(thud(48, 0.7, 0.9), 42.25)
add(ping(392, 0.9, 0.5), 42.3)
ticks(44.7, 52.1, 1.0, 1500, 0.4)
ticks(44.7, 52.1, 1.0, 2000, 0.35, 0.08)
add(ping(1568, 0.8, 0.6), 48.65)

# ================= sala: cabeza vs pies =================
ticks(52.6, 57.8, 1.0, 900, 0.3)
ticks(53.0, 57.8, 1.02, 2400, 0.3)
add(ping(1046, 0.6, 0.5), 55.45)

# ================= laboratorio =================
t3 = tt(1.0)
add(np.sin(2 * np.pi * (180 + 2200 * t3) * t3) * np.sin(np.pi * t3) ** 0.6 * 0.35, 59.0)
add(hp(rng.randn(len(t3)), 3000) * np.sin(np.pi * t3) ** 2 * 0.1, 59.0)
sp = np.zeros(int(3.0 * sr))
for k in range(60):
    i0 = rng.randint(0, len(sp) - 2000)
    tq = tt(0.04)
    sp[i0:i0 + len(tq)] += np.sin(2 * np.pi * rng.uniform(3000, 6000) * tq) * np.exp(-tq * 80) * 0.15
add(sp, 59.3)
add(ping(1318, 0.5, 0.6), 59.35)
add(ping(1175, 0.5, 0.5), 59.95)
add(tick(1500, 0.05, 0.8), 60.65)

# ================= cierre y cortes =================
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), 62.3, 0.6)
chord((1047, 1568, 2093), 62.6, 2.4, 0.5)
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
