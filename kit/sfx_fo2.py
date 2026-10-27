import sys
sys.path.insert(0, '/home/claude')
import numpy as np
from fo2 import fw, NEWDUR
from scipy.signal import butter, lfilter
from scipy.io import wavfile

sr = 44100
T = NEWDUR
N = int(T * sr)
rng = np.random.RandomState(21)
buf = np.zeros(N)
t_all = np.arange(N) / sr


def tt(d):
    return np.arange(int(d * sr)) / sr


def add(sig, t0, g=1.0):
    i0 = int(fw(t0) * sr)
    if i0 >= N:
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


def span(x, a):
    xs, ys = zip(*a)
    xs = [fw(x) for x in xs]
    return x * np.interp(t_all[:len(x)], xs, ys)


def chord(fs, t0, d=2.0, g=0.5):
    for k, f in enumerate(fs):
        add(ping(f, d, g / (1 + 0.15 * k)), t0 + 0.07 * k)


# ================= AMBIENTES =================
# calle de noche (0 - 13.4)
street = lp(rng.randn(N), 800) * 1.6 * (0.75 + 0.25 * np.sin(2 * np.pi * 0.27 * t_all))
cr = np.zeros(N)
for k in range(int(13.4 * 3.2)):
    t0 = 0.3 + k * 0.31 + rng.uniform(0, 0.08)
    for j in range(3):
        d = 0.05
        tc = tt(d)
        i0 = int(fw(t0 + j * 0.07) * sr)
        if i0 + len(tc) < N:
            cr[i0:i0 + len(tc)] += np.sin(2 * np.pi * (4200 + 120 * (k % 3)) * tc) * np.hanning(len(tc)) * 0.25
street += cr
for tc_ in (2.0, 7.2, 11.0):
    n = int(2.6 * sr); tq = np.arange(n) / sr
    car = bp(rng.randn(n), 160, 2000) * np.exp(-((tq - 1.3) / 0.6) ** 2) * 2.4
    i0 = int(fw(tc_) * sr)
    if i0 + n < N: street[i0:i0 + n] += car
street = span(street, [(0, 0), (0.8, 0.5), (13.0, 0.5), (13.5, 0), (22.5, 0), (22.8, 0.28), (41.6, 0.28), (42.0, 0)])
buf += street * 0.55

# centro de datos (13.4 - 22.6)
fan = bp(rng.randn(N), 250, 1800, 2) * 2.0 + np.sin(2 * np.pi * 120 * t_all) * 0.25 + np.sin(2 * np.pi * 240 * t_all) * 0.10
fan = span(fan, [(0, 0), (13.3, 0), (13.8, 0.55), (22.3, 0.55), (22.6, 0)])
buf += fan * 0.45

# fondo del mar (42 - 52.6)
under = lp(rng.randn(N), 380, 3) * 3.4 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * t_all))
under = span(under, [(0, 0), (41.9, 0), (42.5, 0.7), (52.2, 0.7), (52.6, 0)])
buf += under * 0.5
for k in range(26):
    t0 = 42.4 + k * 0.4 + rng.uniform(0, 0.25)
    if t0 > 52.2: break
    d = 0.12
    tb = tt(d)
    f0 = rng.uniform(500, 900)
    add(np.sin(2 * np.pi * (f0 * (1 + 2.2 * tb / d)) * tb) * np.exp(-tb * 28), t0, 0.22)

# pad suave (22.6 - 41.9): zumbido tonal
pad = (np.sin(2 * np.pi * 110 * t_all) + 0.6 * np.sin(2 * np.pi * 165 * t_all + 0.7) + 0.3 * np.sin(2 * np.pi * 220 * t_all)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.18 * t_all))
pad = span(pad, [(0, 0), (22.5, 0), (23.5, 0.2), (41.5, 0.2), (42.0, 0)])
buf += pad * 0.22

# casa (52.6 - 67.6)
room = lp(rng.randn(N), 500, 2) * 1.0 + np.sin(2 * np.pi * 60 * t_all) * 0.05
room = span(room, [(0, 0), (52.5, 0), (53.2, 0.25), (66.8, 0.25), (67.6, 0)])
buf += room * 0.35

# ================= TRANSICIONES =================
for tw in (13.15, 22.3, 41.75, 52.35, 64.0):
    add(whoosh(0.75), tw, 0.9)
for tw in (4.6, 9.5, 46.2):
    add(whoosh(0.55), tw, 0.45)

# ================= ESCENA 1-2: calle =================
add(tick(1800, 0.05, 0.8), 1.0)
for k, tz in enumerate((1.3, 2.9, 4.4, 6.2, 8.0, 9.8)):
    add(chirp(900, 3400, 0.5, 0.35, 0.8), tz)
add(ping(1200, 0.4, 0.6), 5.6)
add(thud(70, 0.3, 0.5), 0.5)
add(tick(1500, 0.05, 0.8), 10.2)
# electricidad "cancelada": zumbido corto
bz = tt(0.35)
add(np.sign(np.sin(2 * np.pi * 110 * bz)) * np.exp(-bz * 8) * 0.25, 10.6)
add(chirp(500, 2600, 0.7, 0.55, 0.8), 11.2)
add(ping(1760, 0.8, 0.7), 11.9)
# ================= ESCENA 3: centro de datos =================
add(tick(1500, 0.05, 0.8), 14.0)
add(chirp(300, 1500, 0.8, 0.7, 0.7), 14.3)
add(ping(1480, 0.6, 0.7), 15.2)
bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1]
k = 0
tcur = 16.8
while tcur < 22.0:
    if bits[k % len(bits)]:
        add(tick(1000 + 40 * (k % 12) + 25 * (tcur - 16.8), 0.05, 0.7), tcur)
    k += 1
    tcur += 1 / 6.0
add(chirp(200, 2400, 1.9, 0.5, 1.2), 18.6)
add(ping(1568, 0.9, 0.7), 20.6)
# ================= ESCENA 4: reflexión =================
add(tick(1500, 0.05, 0.8), 26.0)
add(tick(1500, 0.05, 0.8), 28.3)
k = 0
while 23.4 + 0.7 * k < 36.0:
    add(ping(1600 + 200 * (k % 3), 0.35, 0.25), 23.4 + 0.7 * k)
    k += 1
add(chirp(400, 2200, 0.8, 0.5, 0.8), 33.7)
chord((1047, 1318, 1568), 33.9, 1.6, 0.55)
# ================= ESCENA 5: rayos X =================
add(chirp(180, 2400, 1.0, 0.8, 0.6), 36.0)
add(hp(rng.randn(int(1.0 * sr)), 3000) * np.sin(np.pi * np.linspace(0, 1, int(1.0 * sr))) ** 2, 36.0, 0.12)
for ta in (37.4, 38.4, 39.4, 40.2):
    add(ping(1100, 0.2, 0.7), ta)
k = 0
while 36.9 + 3.3 * k < 41.5:
    add(chirp(300, 1400, 0.5, 0.25, 0.8), 36.9 + 3.3 * k)
    k += 1
# ================= ESCENA 6: fondo del mar =================
add(ping(700, 2.2, 0.9), 42.5)
add(ping(700, 1.6, 0.3), 43.4)
add(tick(1300, 0.05, 0.8), 42.6)
add(tick(1300, 0.05, 0.8), 43.6)
for tb in (44.0, 46.0):
    add(chirp(400, 1400, 0.6, 0.55, 0.9), tb)
    add(ping(1568, 0.7, 0.55), tb + 0.55)
for k in range(9):
    add(tick(900, 0.04, 0.45), 42.8 + 0.34 * k)
add(whoosh(0.6), 46.3, 0.5)
add(np.sin(2 * np.pi * 1760 * tt(1.2)) * np.exp(-tt(1.2) * 3) * 0.12, 46.5)
# colores: arpegio
notes = (523, 659, 784, 988)
for rep in range(4):
    for j, f in enumerate(notes):
        add(ping(f, 0.8, 0.5), 47.0 + rep * 1.3 + 0.25 * j)
add(tick(1300, 0.05, 0.8), 47.0)
# ================= ESCENA 7: casa =================
add(tick(1300, 0.05, 0.8), 53.2)
add(chirp(1000, 3800, 0.45, 0.4, 0.8), 53.3)
add(chirp(1000, 3800, 0.45, 0.4, 0.8), 53.8)
for j, f in enumerate((900, 1200, 1500)):
    add(ping(f, 0.3, 0.6), 54.0 + 0.15 * j)
k = 0
while 54.4 + 0.12 * k < 57.5:
    if bits[k % len(bits)]:
        add(tick(1700, 0.04, 0.45), 54.4 + 0.12 * k)
    k += 1
add(tick(1300, 0.05, 0.8), 55.8)
k = 0
while 56.0 + 0.9 * k < 59.0:
    add(chirp(500, 2000, 0.4, 0.45, 0.8), 56.0 + 0.9 * k)
    k += 1
add(tick(1300, 0.05, 0.8), 58.4)
add(thud(55, 0.5, 0.9), 58.2)
add(hp(rng.randn(int(0.35 * sr)), 2500) * np.hanning(int(0.35 * sr)) * 0.5, 58.2, 0.2)
chord((523, 659, 784, 1047), 58.7, 2.2, 0.55)
add(ping(880, 0.6, 0.25), 60.2)
# ================= CIERRE =================
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), 64.2, 0.6)
chord((1047, 1568, 2093), 64.5, 2.4, 0.5)

# ================= MASTER =================
buf = fade(buf, 0.05, 1.0)
peak = np.abs(buf).max()
buf = buf / peak * 0.5
print("pico previo", round(float(peak), 2), "RMS dBFS", round(float(20 * np.log10(np.sqrt((buf ** 2).mean()))), 1))
st = np.stack([buf, buf], 1)
wavfile.write("/home/claude/efectos_fibra_sync.wav", sr, (st * 32767).astype(np.int16))
rms = [int(20 * np.log10(np.sqrt((buf[i * sr:(i + 1) * sr] ** 2).mean()) + 1e-6)) for i in range(0, 63)]
print(rms)
