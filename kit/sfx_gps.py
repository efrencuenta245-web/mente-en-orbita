"""Efectos de sonido sintéticos para el video del GPS.
Todos los tiempos pasan por fw(); si existe gps_sync.py (narración) se usa su mapa de tiempos."""
import sys
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

try:
    import gps_sync
    fw = gps_sync.fw
    T = gps_sync.NEWDUR
    OUT = "/home/claude/efectos_gps_sync.wav"
except ImportError:
    fw = lambda x: x
    T = 68.6
    OUT = "/home/claude/efectos_gps.wav"

sr = 44100
N = int(T * sr)
rng = np.random.RandomState(44)
buf = np.zeros(N)
t_all = np.arange(N) / sr


def tt(d):
    return np.arange(int(d * sr)) / sr


def add(sig, t0, g=1.0, warp=True):
    t0 = fw(t0) if warp else t0
    i0 = int(t0 * sr)
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
    if a > 0: x[:a] *= np.linspace(0, 1, a)
    if b > 0: x[-b:] *= np.linspace(1, 0, b)
    return x


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


def chirp(f0, f1, d, g=1.0, shape=1.0):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / sr
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** shape
    return np.sin(ph) * e * g * 0.5


def thud(f=70, d=0.25, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * (f + 40 * np.exp(-t * 30)) * t) * np.exp(-t * 14) * g


def span(x, pts):
    xs = [fw(a) for a, _ in pts]
    ys = [b for _, b in pts]
    return x * np.interp(t_all[:len(x)], xs, ys)


def chord(fs, t0, d=2.0, g=0.5):
    for k, f in enumerate(fs):
        add(ping(f, d, g / (1 + 0.15 * k)), t0 + 0.07 * k)


def riser(d, f0=180, f1=1800, g=1.0):
    t = tt(d)
    nz = rng.randn(len(t))
    out = np.zeros(len(t))
    nseg = 24
    for k in range(nseg):
        a, b = int(len(t) * k / nseg), int(len(t) * (k + 1) / nseg)
        fc = f0 * (f1 / f0) ** (k / nseg)
        seg_ = bp(nz[max(0, a - 2000):b], fc * 0.7, min(fc * 1.5, 19000))[-(b - a):]
        out[a:b] = seg_
    tone = chirp(f0, f1, d, 0.6, 0.6)
    env = (t / d) ** 1.6
    return (out * 2.2 + tone) * env * g


# ================= AMBIENTES =================
CUT = [0, 4.6, 8.6, 14.2, 23.2, 26.6, 47.2, 52.9, 60.9, 68.6]
# interior del auto: motor y rodamiento
eng = lp(rng.randn(N), 140, 3) * 4.0 + np.sin(2 * np.pi * 46 * t_all) * 0.18 + bp(rng.randn(N), 250, 1100) * 0.7
eng *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.35 * t_all))
eng = span(eng, [(0, 0), (0.3, 0.55), (4.4, 0.55), (4.7, 0), (23.1, 0), (23.4, 0.4), (26.4, 0.4), (26.7, 0),
                 (60.8, 0), (61.1, 0.55), (65.6, 0.45), (68.6, 0)])
buf += eng * 0.5
# espacio: dron grave
dr = (np.sin(2 * np.pi * 55 * t_all) + 0.7 * np.sin(2 * np.pi * 82.6 * t_all + 0.4) + 0.4 * np.sin(2 * np.pi * 110.3 * t_all)) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.11 * t_all))
dr += lp(rng.randn(N), 300, 2) * 1.2
dr = span(dr, [(0, 0), (8.5, 0), (8.9, 0.45), (23.0, 0.45), (23.3, 0), (47.1, 0), (47.5, 0.45), (52.7, 0.45), (53.0, 0)])
buf += dr * 0.35
# ciudad de noche desde arriba: tráfico lejano + viento
city = lp(rng.randn(N), 520, 2) * 1.8 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.23 * t_all))
city = span(city, [(0, 0), (4.5, 0), (4.8, 0.5), (7.6, 0.25), (8.6, 0), (26.5, 0), (26.9, 0.45), (36.8, 0.4), (38.0, 0.3), (47.0, 0.3), (47.3, 0),
                   (52.8, 0), (53.2, 0.15), (57.5, 0.15), (60.5, 0.4), (60.9, 0)])
buf += city * 0.5
wind = bp(rng.randn(N), 300, 2500) * 1.3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * t_all))
wind = span(wind, [(0, 0), (52.8, 0), (53.2, 0.3), (57.3, 0.3), (59.0, 0.6), (60.6, 0.2), (60.9, 0)])
buf += wind * 0.4

# ================= TRANSICIONES =================
for tw in (14.0, 22.95, 26.35, 46.95, 52.65, 60.65):
    add(whoosh(0.75), tw, 0.9)
# 4.6: despegue; 8.6: llegada al espacio
add(whoosh(0.6), 4.35, 0.6)
add(riser(3.9, 160, 2200, 0.55), 4.7)
add(whoosh(1.0), 8.1, 1.0)
add(thud(48, 0.9, 0.9), 8.62)
add(np.sin(2 * np.pi * 2093 * tt(2.0)) * np.exp(-tt(2.0) * 1.6) * 0.10, 8.65)

# ================= 1: auto y mapa =================
add(ping(880, 0.35, 0.55), 0.55)
add(ping(1320, 0.6, 0.55), 0.72)
for k in range(3):
    add(np.sin(2 * np.pi * 620 * tt(0.12)) * np.hanning(int(0.12 * sr)) * 0.10, 1.2 + 1.57 * k)
add(tick(1800, 0.05, 0.8), 1.3)
add(tick(1500, 0.05, 0.8), 2.25)
# 2: altitud (tics cada vez más rápidos)
tc = 5.0
while tc < 8.3:
    add(tick(1300 + 500 * (tc - 5.0) / 3.3, 0.03, 0.45), tc)
    tc += 0.16 * (1 - 0.8 * (tc - 5.0) / 3.3)

# ================= 3: constelación =================
for ta in (9.05, 11.55, 13.05):
    add(tick(1500, 0.05, 0.8), ta)
add(tick(1800, 0.05, 0.7), 9.3)
for (tb, f) in ((10.2, 1760), (10.45, 1760), (12.2, 1568), (12.45, 1568)):
    add(np.sin(2 * np.pi * f * tt(0.09)) * np.hanning(int(0.09 * sr)) * 0.16, tb)
add(chirp(300, 900, 2.5, 0.25, 1.0), 10.8)

# ================= 4: satélite y rayos X =================
add(chirp(180, 2400, 1.0, 0.8, 0.6), 15.0)
add(hp(rng.randn(int(1.0 * sr)), 3000) * np.sin(np.pi * np.linspace(0, 1, int(1.0 * sr))) ** 2, 15.0, 0.12)
for ta in (15.5, 16.3, 17.0, 17.6):
    add(ping(1100, 0.2, 0.7), ta)
# relojes atómicos: tic preciso
tc = 15.3
while tc < 18.7:
    add(tick(2600, 0.025, 0.55), tc)
    tc += 0.5
add(ping(2637, 1.0, 0.45), 16.65)
add(chirp(2400, 300, 0.7, 0.5, 0.8), 18.8)
# transmisión: pulsos de radio hacia la Tierra
tc = 19.1
k = 0
while tc < 22.9:
    add(chirp(2200, 1300, 0.16, 0.30, 0.6), tc)
    if k % 3 == 2:
        add(np.sin(2 * np.pi * 3200 * tt(0.05)) * np.exp(-tt(0.05) * 60) * 0.12, tc + 0.08)
    tc += 1 / 3.3
    k += 1
for ta in (20.25, 21.05, 22.05):
    for j in range(6):
        add(tick(1900 + 90 * j, 0.025, 0.35), ta + 0.045 * j)

# ================= 5: celular en rayos X (solo escucha) =================
add(chirp(220, 2000, 0.8, 0.6, 0.6), 23.45)
add(hp(rng.randn(int(0.8 * sr)), 3000) * np.sin(np.pi * np.linspace(0, 1, int(0.8 * sr))) ** 2, 23.45, 0.1)
tc = 23.9
while tc < 26.3:
    add(chirp(1300, 2300, 0.12, 0.22, 0.6), tc)
    tc += 0.28
add(ping(1046, 0.25, 0.6), 24.65)
add(ping(1568, 0.5, 0.6), 24.8)
bz = tt(0.32)
add(np.sign(np.sin(2 * np.pi * 120 * bz)) * np.exp(-bz * 9) * 0.22, 25.15)

# ================= 6: ciudad — señal, distancias, trilateración =================
# rayo de señal sostenido
sig = (np.sin(2 * np.pi * 880 * t_all) * 0.5 + np.sin(2 * np.pi * 1320 * t_all) * 0.25) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * t_all)))
sig = lp(sig, 3000)
sig = span(sig, [(0, 0), (26.9, 0), (27.4, 0.10), (32.6, 0.10), (33.5, 0.05), (36.8, 0.05), (37.3, 0)])
buf += sig
tc = 28.4
while tc < 31.8:
    add(tick(2200, 0.02, 0.35), tc)
    tc += 0.06
add(ping(1760, 0.6, 0.6), 31.85)
add(tick(1500, 0.05, 0.8), 29.05)
for j, ta in enumerate((33.4, 34.0, 34.6)):
    add(ping(988 + 200 * j, 0.45, 0.6), ta)
add(tick(1500, 0.05, 0.8), 34.25)
# círculos
for j, ta in enumerate((37.7, 38.5, 39.3)):
    add(chirp(300 + 120 * j, 1100 + 300 * j, 0.7, 0.55, 0.8), ta)
add(np.sin(2 * np.pi * 1500 * tt(0.08)) * np.hanning(int(0.08 * sr)) * 0.2, 38.95)
add(np.sin(2 * np.pi * 1500 * tt(0.08)) * np.hanning(int(0.08 * sr)) * 0.2, 39.2)
add(thud(60, 0.4, 0.9), 40.25)
chord((784, 988, 1175), 40.3, 1.4, 0.5)
# error del reloj
wob = tt(1.6)
add((np.sin(2 * np.pi * 330 * wob) + np.sin(2 * np.pi * 345 * wob)) * np.sin(np.pi * wob / 1.6) * 0.12, 41.4)
add(chirp(260, 200, 0.6, 0.35, 1.0), 41.7)
add(chirp(250, 900, 0.9, 0.55, 0.8), 42.0)
add(tick(1500, 0.05, 0.8), 42.05)
add(whoosh(0.4), 43.4, 0.5)
chord((1047, 1318, 1568, 2093), 43.65, 1.8, 0.55)
add(tick(1500, 0.05, 0.8), 44.35)
add(thud(80, 0.25, 0.5), 44.35)
for k in range(5):
    add(np.sin(2 * np.pi * 740 * tt(0.18)) * np.hanning(int(0.18 * sr)) * 0.14, 44.8 + 0.42 * k)
add(chirp(500, 1500, 1.6, 0.18, 1.0), 45.0)

# ================= 7: relatividad =================
add(ping(660, 1.2, 0.5), 47.85)
add(tick(1500, 0.05, 0.8), 47.85)
tc = 49.5
while tc < 52.2:
    r = (tc - 49.5) / 2.7
    add(tick(1500, 0.02, 0.4), tc)
    add(tick(1620, 0.02, 0.3), tc + 0.02 + 0.05 * r)
    tc += 0.22 - 0.15 * r
add(ping(1760, 0.8, 0.6), 50.65)
add(ping(2349, 0.8, 0.35), 50.8)

# ================= 8: error sin corregir y zoom a 5 m =================
wt = tt(3.0)
saw = 2 * ((140 * wt * (1 + 0.6 * wt / 3.0)) % 1.0) - 1
add(lp(saw, 1200) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * wt)) * (wt / 3.0) * 0.18, 53.4)
add(tick(1500, 0.05, 0.8), 53.35)
add(tick(1500, 0.05, 0.8), 54.45)
add(chirp(1800, 500, 0.5, 0.5, 0.8), 57.2)
chord((784, 1047, 1318), 57.6, 1.2, 0.4)
add(riser(2.6, 2200, 220, 0.35), 57.6)
add(ping(1568, 0.6, 0.55), 58.65)
add(tick(1500, 0.05, 0.8), 58.95)
add(thud(65, 0.3, 0.6), 59.45)
add(ping(1318, 0.4, 0.45), 59.5)

# ================= 9: auto y cierre =================
add(ping(880, 0.35, 0.45), 61.6)
add(ping(1320, 0.6, 0.45), 61.77)
add(tick(1500, 0.05, 0.8), 62.45)
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), 65.4, 0.6)
chord((1047, 1568, 2093), 65.7, 2.4, 0.5)

# ================= MASTER =================
buf = fade(buf, 0.05, 1.0)
peak = np.abs(buf).max()
buf = buf / peak * 0.5
print("pico previo", round(float(peak), 2), "RMS dBFS", round(float(20 * np.log10(np.sqrt((buf ** 2).mean()))), 1))
st = np.stack([buf, buf], 1)
wavfile.write(OUT, sr, (st * 32767).astype(np.int16))
rms = [int(20 * np.log10(np.sqrt((buf[i * sr:(i + 1) * sr] ** 2).mean()) + 1e-6)) for i in range(0, int(T))]
print(rms)
print("->", OUT)
