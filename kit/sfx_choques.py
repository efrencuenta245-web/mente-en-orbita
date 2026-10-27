"""Efectos de sonido del video '¿Por qué no chocan los satélites?'. Tiempos por fw() (si existe choques_sync.py, los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile
import choques as V

try:
    import choques_sync
    fw = choques_sync.fw
    T = choques_sync.NEWDUR
    OUT = "/home/claude/efectos_choques_sync.wav"
except ImportError:
    fw = lambda x: x
    T = V.DUR
    OUT = "/home/claude/efectos_choques.wav"

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

# ================= AMBIENTES =================
SPACE = [(0, 8.45), (8.45, 14.85), (19.65, 44.35), (49.05, V.DUR)]
dr = (np.sin(2 * np.pi * 55 * t_all) + 0.7 * np.sin(2 * np.pi * 82.6 * t_all + 0.4) + 0.4 * np.sin(2 * np.pi * 110.3 * t_all)) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.11 * t_all))
dr += lp(rng.randn(N), 300, 2) * 1.2
pts = [(0, 0)]
for (a, b) in SPACE:
    pts += [(a + 0.05, 0.38), (b - 0.05, 0.38), (b + 0.01, 0.0)]
dr = span(dr, sorted(pts, key=lambda p: p[0]))
buf += dr * 0.3
# atardecer en el radar: viento + grillos
wind = lp(rng.randn(N), 500) * 1.4 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.23 * t_all))
wind = span(wind, [(0, 0), (14.85, 0), (15.0, 0.45), (19.55, 0.45), (19.65, 0), (44.35, 0), (44.5, 0.5), (48.95, 0.5), (49.05, 0)])
buf += wind * 0.5
cr = np.zeros(N)
for k in range(60):
    tc = 14.95 + k * 0.078
    t0 = fw(tc)
    i0 = int(t0 * sr)
    tq = tt(0.03)
    if i0 + len(tq) < N:
        cr[i0:i0 + len(tq)] += np.sin(2 * np.pi * 4300 * tq) * np.exp(-tq * 60) * (0.5 + 0.5 * (k % 3 == 0))
buf += cr * 0.06

# ================= gancho =================
add(thud(45, 1.2, 0.7), 0.25)
add(whoosh(1.6), 0.2, 0.5)
counter_ticks(WT(0, 5) - 0.1, WT(0, 7) + 0.2, 18, 2600, 0.25)
add(whoosh(0.9), WT(0, 10) - 0.3, 0.5)
add(ping(330, 0.6, 0.5), WT(0, 10))
# semáforo "negado"
for k in range(2):
    t = tt(0.18)
    add((np.sign(np.sin(2 * np.pi * 180 * t)) * 0.25 + np.sin(2 * np.pi * 360 * t) * 0.2) * np.exp(-t * 4), WT(0, 15) + k * 0.22, 0.7)
# alarma del par que se cruza
for k in range(4):
    add(beep(1320 if k % 2 == 0 else 990, 0.1, 0.8), 6.8 + k * 0.28)
add(riser(1.4, 180, 800, 0.35), 7.05)

# ================= choque =================
add(rumble(3.0, 120, 0.5) * np.sin(np.pi * tt(3.0) / 3.0) ** 2, 8.5)
t2 = tt(1.6)
add(np.sin(2 * np.pi * (300 + 900 * (t2 / 1.6) ** 2) * t2) * (t2 / 1.6) ** 2 * 0.25, V.T_IMP - 1.6)
imp = rumble(2.0, 220, 1.6) * np.exp(-tt(2.0) * 2.2) + hp(rng.randn(int(2.0 * sr)), 1500) * np.exp(-tt(2.0) * 7) * 1.2
add(imp, V.T_IMP)
add(thud(40, 1.6, 1.4), V.T_IMP)
for f in (523, 698, 1046, 1480, 2217):
    t3 = tt(1.8)
    add(np.sin(2 * np.pi * f * t3) * np.exp(-t3 * (2.5 + f / 800)) * 0.12, V.T_IMP + 0.02)
crack = np.zeros(int(2.4 * sr))
for k in range(140):
    i0 = rng.randint(0, len(crack) - 3000)
    tq = tt(0.02)
    crack[i0:i0 + len(tq)] += hp(rng.randn(len(tq)), 2500) * np.exp(-tq * 200) * rng.uniform(0.2, 0.8) * np.exp(-i0 / sr * 1.2)
add(crack, V.T_IMP + 0.15, 0.8)
counter_ticks(WT(2, 14) - 0.2, WT(2, 16) + 0.3, 14, 2200, 0.28)

# ================= radar =================
for k in range(5):
    t0 = 15.15 + k * 0.95
    t4 = tt(1.0)
    add(np.sin(2 * np.pi * 980 * t4) * np.exp(-t4 * 4) * 0.35 + np.sin(2 * np.pi * 1962 * t4) * np.exp(-t4 * 6) * 0.1, t0)
for k, t0 in enumerate((16.3, 16.9, 17.6, 18.2, 18.9)):
    add(beep(2100, 0.05, 0.5), t0)
    add(beep(2800, 0.05, 0.4), t0 + 0.07)
counter_ticks(WT(3, 7) - 0.2, WT(3, 9) + 0.2, 14, 2500, 0.25)

# ================= predicción =================
for k in range(26):
    add(beep(1800 + 600 * ((k * 7) % 5), 0.035, 0.3), 20.0 + k * 0.11)
for k in range(3):
    add(whoosh(0.5), 21.0 + 1.6 * k, 0.25)
for k in range(5):
    add(beep(880, 0.16, 0.9), WT(4, 9) - 0.1 + k * 0.3)
    add(beep(660, 0.12, 0.6), WT(4, 9) + 0.05 + k * 0.3)

# ================= el satélite se hace a un lado =================
h = hiss(1.8, 1200, 7000, 0.35) * np.sin(np.pi * tt(1.8) / 1.8) ** 0.5
hum = np.sin(2 * np.pi * 220 * tt(1.8)) * 0.15 + np.sin(2 * np.pi * 330 * tt(1.8)) * 0.08
add((h + hum) * np.minimum(1, tt(1.8) / 0.05), V.T_BURN)
add(ping(1175, 0.4, 0.5), V.T_BURN)
add(whoosh(0.9), V.T_PASS - 0.5, 0.9)
add(ping(784, 0.9, 0.5), V.T_PASS + 0.3)
add(ping(1175, 0.9, 0.45), V.T_PASS + 0.42)

# ================= Estación Espacial =================
rb = rumble(4.2, 200, 0.5) * np.minimum(1, tt(4.2) / 0.3) * np.minimum(1, (4.2 - tt(4.2)) / 0.4)
add(rb, V.T_ISSB)
add(hiss(4.2, 600, 3000, 0.12) * np.minimum(1, tt(4.2) / 0.3) * np.minimum(1, (4.2 - tt(4.2)) / 0.4), V.T_ISSB)
add(whoosh(1.0), 32.4, 0.7)
add(beep(1500, 0.08, 0.5), WT(6, 6))
add(beep(1500, 0.08, 0.5), WT(6, 6) + 0.12)

# ================= rayos X =================
t5 = tt(1.0)
add(np.sin(2 * np.pi * (180 + 2200 * t5) * t5) * np.sin(np.pi * t5) ** 0.6 * 0.3, V.T_XR)
add(hp(rng.randn(len(t5)), 3000) * np.sin(np.pi * t5) ** 2 * 0.08, V.T_XR)
hm = np.sin(2 * np.pi * 110 * tt(4.0)) * 0.08 * (0.7 + 0.3 * np.sin(2 * np.pi * 6 * tt(4.0)))
add(fade(hm + hiss(4.0, 2000, 6000, 0.04), 0.3, 0.4), V.T_XR + 0.2)
for t0 in (V.T_XR + 0.6, WT(7, 3), WT(7, 8)):
    add(ping(1568, 0.4, 0.4), t0)

# ================= flota =================
for k in range(40):
    add(ping(1046 * (1.5 ** (k % 3)) / 1.5, 0.3, 0.22), 39.7 + k * 0.11 + 0.03 * (k % 4))
counter_ticks(WT(8, 4) - 0.2, WT(8, 8) + 0.2, 20, 2400, 0.25)
chord((784, 988, 1318), WT(8, 9), 1.2, 0.4)

# ================= plataforma =================
vent = hiss(4.6, 300, 4000, 0.25) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * tt(4.6)))
add(fade(vent, 0.3, 0.4), 44.4)
for i in range(3):
    add(beep(1700, 0.06, 0.5), WT(9, 6) + 0.35 * i)

# ================= ventana de lanzamiento =================
tc = 49.4
while tc < V.T_LAUNCH:
    add(tick(1300, 0.03, 0.35), tc)
    tc += 0.25 if tc < V.T_LAUNCH - 1.2 else 0.12
roar = rumble(3.0, 150, 1.0) * np.minimum(1, tt(3.0) / 0.4) * np.exp(-tt(3.0) * 0.5) + hiss(3.0, 300, 2000, 0.2) * np.exp(-tt(3.0) * 0.8)
add(roar, V.T_LAUNCH)
add(thud(50, 0.8, 0.8), V.T_LAUNCH)
chord((523, 659, 784), WT(10, 16), 1.4, 0.4)

# ================= despliegue =================
for ts in V.T_SEPS:
    add(thud(140, 0.12, 0.5), ts)
    add(tick(2600, 0.03, 0.5), ts)
    add(hiss(0.25, 2000, 8000, 0.15) * np.exp(-tt(0.25) * 12), ts)

# ================= cierre y cortes =================
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), V.T_OUT, 0.6)
chord((1047, 1568, 2093), V.T_OUT + 0.3, 2.4, 0.5)
for ct in CUTS:
    add(whoosh(0.6), ct - 0.3, 0.8)

# ================= MASTER =================
buf = fade(buf, 0.05, 1.0)
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
