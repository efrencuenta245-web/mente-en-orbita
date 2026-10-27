import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

sr = 44100
T = 49.8
N = int(T * sr)
rng = np.random.RandomState(11)
buf = np.zeros(N)


def tt(d):
    return np.arange(int(d * sr)) / sr


def add(sig, t0, g=1.0):
    i0 = int(t0 * sr)
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
    """aplica envolvente de ganancia por tramos: (tiempo, ganancia)"""
    t = np.arange(len(x)) / sr
    xs, ys = zip(*a)
    return x * np.interp(t, xs, ys)


# ---------- ambiente de calle (0-33, y breve regreso 42.9-44.6) ----------
amb = lp(rng.randn(N), 900) * 2.2
amb *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.31 * np.arange(N) / sr)
for tc in (1.2, 3.4, 6.5, 9.8, 13.0, 17.6, 21.5, 26.0, 29.5):
    n = int(2.4 * sr); t = np.arange(n) / sr
    car = bp(rng.randn(n), 180, 2200) * np.exp(-((t - 1.2) / 0.55) ** 2) * 2.6
    i0 = int(tc * sr)
    if i0 + n < N: amb[i0:i0 + n] += car
amb = span(amb, [(0, 0), (1.0, 0.5), (32.4, 0.5), (33.1, 0), (42.8, 0), (42.95, 0.5), (43.2, 0.5), (44.6, 0)])
buf += amb * 0.55

# ---------- cabina de avión (33.2-42.9) ----------
t = np.arange(N) / sr
drone = lp(np.cumsum(rng.randn(N)) / 600.0, 160) * 0.0
brown = lp(rng.randn(N), 170, 3) * 3.0
saw = sum(np.sin(2 * np.pi * 92 * k * t) / k for k in range(1, 6)) * 0.12
cab = (brown + saw) * (0.9 + 0.1 * np.sin(2 * np.pi * 0.4 * t))
cab = span(cab, [(0, 0), (33.1, 0), (33.6, 0.6), (42.4, 0.6), (42.9, 0)])
buf += cab * 0.5

# ---------- transiciones ----------
for tw in (4.75, 10.95, 18.35, 25.55, 32.85, 42.65, 46.2):
    add(whoosh(0.7), tw, 0.9)

# ---------- escena 1: golpes suaves de las ondas ----------
for th in (1.68, 2.59, 3.50, 4.41):
    add(thud(75, 0.3, 0.55), th)
# ---------- escena 2: pulso de presión ----------
pt = tt(5.4)
pulse = np.sin(2 * np.pi * 110 * pt) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.9 * pt - np.pi / 2))
add(fade(pulse, 0.5, 0.6), 5.4, 0.30)
# ---------- escena 3 ----------
add(ping(1760, 0.6, 0.8), 12.0)
for k in range(3):
    add(tick(1200 + 300 * k, 0.07, 0.9), 14.4 + 0.1 * k)
add(chirp(280, 900, 1.0, 0.7), 14.5)
add(ping(1320, 0.5, 0.7), 15.5)
# ---------- escena 4: cancelación audible ----------
add(ping(1568, 0.6, 0.6), 19.1)
add(chirp(500, 1500, 0.8, 0.6), 19.6)


def ease(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


dur = 24.6 - 19.9
tn = np.arange(int(dur * sr)) / sr
tabs = 19.9 + tn
phi = np.pi * ease((tabs - 21.4) / 3.0)
amp = np.abs(np.cos(phi / 2))
tone = (np.sin(2 * np.pi * 220 * tabs) + 0.5 * np.sin(2 * np.pi * 440 * tabs)) * amp
add(fade(tone, 0.1, 0.05), 19.9, 0.30)
add(ping(1046, 0.5, 0.8), 24.5)
add(ping(1568, 0.9, 0.8), 24.62)
# ---------- escena 5: rayos X ----------
add(chirp(180, 2400, 1.0, 0.8, 0.6), 26.0)
add(hp(rng.randn(int(1.0 * sr)), 3000) * np.sin(np.pi * np.linspace(0, 1, int(1.0 * sr))) ** 2, 26.0, 0.12)
for ta in (26.5, 27.2, 27.9, 29.0):
    add(ping(1100, 0.18, 0.7), ta)
k = 0
while 27.3 + 2.2 * k < 32.4:
    add(tick(900, 0.1, 0.5), 27.3 + 2.2 * k)
    k += 1
# ---------- escena 6 ----------
add(tick(700, 0.08, 0.9), 33.5)
add(ping(988, 0.4, 0.7), 34.85)
add(ping(1480, 0.7, 0.7), 34.97)
add(tick(700, 0.08, 0.9), 39.0)
for tb in (39.45, 39.9, 40.2, 41.0, 41.35, 41.9, 42.2):
    n = int(rng.uniform(0.08, 0.22) * sr)
    burst = bp(rng.randn(n), 300, 2800) * np.hanning(n) * rng.uniform(0.5, 1.0)
    add(burst, tb, 0.9)
add(thud(60, 0.3, 0.9), 40.6)
bz = tt(0.35)
add(np.sign(np.sin(2 * np.pi * 120 * bz)) * np.exp(-bz * 5) * 0.25, 40.5)
# ---------- escena 7: burbuja de silencio ----------
sh = tt(2.6)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.12
add(fade(shim * np.sin(np.pi * sh / 2.6) ** 1.5, 0.3, 0.8), 43.2, 0.7)
bl = tt(1.6)
add(np.sin(2 * np.pi * 130 * bl) * np.sin(np.pi * bl / 1.6) ** 2, 44.0, 0.35)
add(ping(1047, 2.2, 0.55), 46.7)
add(ping(1568, 2.2, 0.45), 46.78)
add(ping(2093, 2.2, 0.35), 46.86)

# ---------- master ----------
buf = fade(buf, 0.05, 0.8)
peak = np.abs(buf).max()
buf = buf / peak * 0.5
print("pico previo", round(float(peak), 2), "RMS global dBFS", round(float(20 * np.log10(np.sqrt((buf ** 2).mean()))), 1))
st = np.stack([buf, buf], 1)
wavfile.write("/mnt/user-data/outputs/efectos_cancelacion_de_ruido.wav", sr, (st * 32767).astype(np.int16))
# energía por segundo (verificación)
rms = [round(float(20 * np.log10(np.sqrt((buf[i * sr:(i + 1) * sr] ** 2).mean()) + 1e-6)), 0) for i in range(0, 49)]
print(rms)
