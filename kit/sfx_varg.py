"""Efectos de sonido del video Stark Varg vs 450. Tiempos por fw() (si existe varg_sync.py se usan los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

try:
    import varg_sync
    fw = varg_sync.fw
    T = varg_sync.NEWDUR
    OUT = "/home/claude/efectos_varg_sync.wav"
except ImportError:
    fw = lambda x: x
    T = 48.0
    OUT = "/home/claude/efectos_varg.wav"

sr = 44100
N = int(T * sr)
rng = np.random.RandomState(77)
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


def seglen(a, b):
    return max(0.05, fw(b) - fw(a))


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


def thud(f=70, d=0.3, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * (f + 50 * np.exp(-t * 30)) * t) * np.exp(-t * 12) * g


def chord(fs, t0, d=2.0, g=0.5):
    for k, f in enumerate(fs):
        add(ping(f, d, g / (1 + 0.15 * k)), t0 + 0.06 * k)


def bell(t0, g=1.0):
    t = tt(2.2)
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for (f, a, dcy) in
            ((523, 1.0, 1.6), (1247, 0.6, 2.4), (1712, 0.45, 3.0), (2361, 0.3, 4.0), (3100, 0.15, 5.0)))
    add(s * 0.32 * g, t0)
    add(s * 0.22 * g, t0 + 0.22)


def impact(t0, g=1.0):
    add(thud(48, 0.9, 1.0) * g, t0)
    n = tt(1.2)
    add(hp(rng.randn(len(n)), 2500) * np.exp(-n * 4) * 0.25 * g, t0)
    add(lp(rng.randn(len(n)), 300) * np.exp(-n * 3) * 0.8 * g, t0)


def deny(t0, g=1.0):
    t = tt(0.22)
    s = np.sign(np.sin(2 * np.pi * 180 * t)) * np.exp(-t * 10)
    add(lp(s, 1800) * 0.18 * g, t0)


def score_ping(t0, good=True):
    if good:
        add(ping(1318, 0.4, 0.7), t0)
        add(ping(1760, 0.7, 0.7), t0 + 0.09)
    else:
        add(ping(392, 0.5, 0.7), t0)
        add(ping(330, 0.7, 0.7), t0 + 0.12)


def gas_engine(d, rpm, g=1.0):
    """motor de un cilindro 4T: un encendido cada 2 vueltas; rpm = array por muestra"""
    n = int(d * sr)
    rpm = np.interp(np.arange(n), np.linspace(0, n - 1, len(rpm)), rpm)
    f = rpm / 120.0
    ph = np.cumsum(f) / sr
    fr = ph % 1.0
    pulse = np.exp(-fr * 9.0) - 0.15
    saw = 2 * ((ph * 2) % 1.0) - 1
    nz = rng.randn(n) * (0.3 + 0.7 * np.exp(-fr * 6))
    x = pulse * 1.4 + 0.35 * saw + 0.25 * nz
    x = bp(x, 50, 2600)
    x = np.tanh(x * 2.2)
    return fade(x * g, 0.05, 0.1)


def whine(d, freq, g=1.0):
    n = int(d * sr)
    f = np.interp(np.arange(n), np.linspace(0, n - 1, len(freq)), freq)
    ph = 2 * np.pi * np.cumsum(f) / sr
    x = np.sin(ph) + 0.3 * np.sin(2 * ph + 0.3) + 0.12 * np.sin(3 * ph) + 0.05 * bp(rng.randn(n), 2000, 6000)
    return fade(x * g * 0.25, 0.05, 0.1)


def span(x, pts):
    xs = [fw(a) for a, _ in pts]
    ys = [b for _, b in pts]
    return x * np.interp(t_all[:len(x)], xs, ys)


CUTS = (4.9, 9.0, 12.8, 17.9, 22.9, 28.7, 34.6, 40.2)

# ================= AMBIENTES =================
outdoor = lp(rng.randn(N), 500) * 1.4 + bp(rng.randn(N), 300, 1800) * 0.5 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.21 * t_all))
outdoor = span(outdoor, [(0, 0), (0.3, 0.5), (8.8, 0.6), (9.0, 0.7), (12.6, 0.7), (12.8, 0), (22.8, 0), (23.1, 0.45), (28.5, 0.45), (28.7, 0)])
buf += outdoor * 0.45
room = lp(rng.randn(N), 380) * 0.9 + np.sin(2 * np.pi * 120 * t_all) * 0.03
room = span(room, [(0, 0), (12.7, 0), (13.0, 0.3), (22.7, 0.3), (22.9, 0), (28.6, 0), (28.9, 0.25), (34.5, 0.25), (34.6, 0),
                   (40.1, 0), (40.4, 0.3), (48.0, 0.2)])
buf += room * 0.45
crowd = bp(rng.randn(N), 250, 2500, 2) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 0.37 * t_all)))
crowd = span(crowd, [(0, 0), (34.5, 0), (34.9, 0.6), (35.3, 0.9), (38.0, 0.7), (40.1, 0.6), (40.25, 0)])
buf += crowd * 0.5
cheer = bp(rng.randn(N), 400, 3500, 2)
cheer = span(cheer, [(0, 0), (8.0, 0), (8.4, 0.6), (9.1, 0.5), (9.5, 0.8), (11.0, 0.3), (12.7, 0.25), (12.8, 0)])
buf += cheer * 0.45

# ================= 1: pista — casi sin ruido =================
add(whine(seglen(0, 4.9), np.linspace(620, 760, 60), 0.5), 0.0)
add(lp(rng.randn(int(seglen(0, 4.9) * sr)), 900) * 0.25, 0.0)
deny(2.95)
deny(4.02)

# ================= 2: salto (la 450 ruge, la eléctrica susurra) =================
d = seglen(4.9, 9.0)
rpm = np.concatenate([np.linspace(7600, 8800, 20), np.linspace(8800, 10200, 30), np.linspace(10200, 6500, 20), np.linspace(6500, 8800, 15)])
sig = gas_engine(d, rpm, 0.55)
k = np.interp(t_all[:len(sig)], [0, fw(6.0) - fw(4.9), fw(8.0) - fw(4.9), d], [1, 0.55, 0.55, 1])
add(lp(sig, 2600) * k, 4.9)
add(whine(d, np.concatenate([np.linspace(1300, 1900, 40), np.linspace(1900, 1500, 30), np.linspace(1500, 1900, 15)]), 0.55), 4.9)
add(whoosh(1.2), 5.8, 0.8)
add(thud(40, 1.2, 0.6), 6.0)
add(thud(65, 0.4, 0.9), 8.27)
add(thud(60, 0.4, 0.8), 8.36)
add(hp(rng.randn(int(0.4 * sr)), 1500) * np.exp(-tt(0.4) * 9) * 0.3, 8.3)

# ================= 3: partidor — VS =================
impact(9.4, 1.0)
add(gas_engine(seglen(9.0, 12.8), np.full(30, 1700.0), 0.25), 9.0)
add(whine(seglen(9.0, 12.8), np.full(30, 420.0), 0.12), 9.0)
add(hp(rng.randn(int(0.5 * sr)), 3000) * np.exp(-tt(0.5) * 6) * 0.2, 12.2)

# ================= ROUNDS =================
for tb in (13.1, 18.1, 23.1):
    bell(tb)
    add(whoosh(0.5), tb - 0.15, 0.6)
    add(thud(55, 0.5, 0.7), tb + 0.05)
for (ts, good) in ((17.3, True), (22.5, True), (28.2, True), (43.1, False)):
    score_ping(ts, good)

# round 1: dinamómetro
dd = seglen(14.2, 15.9)
add(gas_engine(dd, np.concatenate([np.linspace(2500, 11500, 60), np.linspace(11500, 11000, 10)]), 0.6), 14.2)
add(gas_engine(seglen(15.9, 17.6), np.linspace(11000, 1800, 30), 0.3), 15.9)
add(whine(seglen(16.25, 17.7), np.concatenate([np.linspace(500, 2700, 60), np.linspace(2700, 2500, 10)]), 0.75), 16.25)
add(lp(rng.randn(int(seglen(14.4, 17.6) * sr)), 220) * 0.6, 14.4)

# round 2: cambios
for k in range(5):
    tk = 19.45 + 0.19 * k
    add(thud(90 + 10 * k, 0.15, 0.7), tk)
    add(tick(2400, 0.03, 0.8), tk)
add(tick(1800, 0.05, 0.7), 19.3)
add(gas_engine(seglen(19.3, 20.4), np.concatenate([np.linspace(5000, 9000, 8), np.linspace(6500, 9000, 8), np.linspace(6800, 9000, 8),
                                                   np.linspace(7000, 9000, 8), np.linspace(7200, 9200, 8)]), 0.35), 19.3)
add(whine(seglen(21.15, 22.8), np.linspace(380, 1500, 50), 0.6), 21.15)
add(whoosh(0.6), 21.75, 0.7)

# round 3: teléfono
for k in range(4):
    add(tick(2000 + 200 * k, 0.05, 0.9), 27.0 + 0.24 * k)
add(tick(1800, 0.05, 0.8), 24.35)
syn = whine(seglen(27.0, 28.0), np.linspace(220, 880, 60), 0.6)
add(lp(syn, 3000), 27.0)
add(whine(seglen(26.6, 28.6), np.linspace(300, 2400, 50), 0.6), 26.6)
add(hp(rng.randn(int(seglen(27.2, 28.6) * sr)), 1200) * 0.08, 27.2)

# ================= rayos X =================
t1 = tt(1.0)
add(np.sin(2 * np.pi * (180 + 2200 * t1 / 1.0) * t1) * np.sin(np.pi * t1) ** 0.6 * 0.4, 29.2)
add(hp(rng.randn(len(t1)), 3000) * np.sin(np.pi * t1) ** 2 * 0.12, 29.2)
hum = (np.sin(2 * np.pi * 100 * t_all) * 0.5 + np.sin(2 * np.pi * 200 * t_all) * 0.2)
hum = span(hum, [(0, 0), (29.3, 0), (29.8, 0.12), (34.4, 0.12), (34.6, 0)])
buf += hum
for ta in (29.85, 31.0, 31.9):
    add(ping(1100, 0.2, 0.7), ta)
tc = 30.2
while tc < 34.3:
    add(tick(3200, 0.02, 0.25), tc)
    tc += 0.13
deny(32.9, 1.2)
deny(33.78, 1.2)

# ================= arena =================
add(whine(seglen(34.6, 40.2), np.concatenate([np.linspace(1200, 1700, 30), np.linspace(1700, 1100, 10), np.linspace(1100, 1600, 30)]), 0.45), 34.6)
add(thud(60, 0.5, 1.0), 36.48)
chord((392, 494, 587, 784), 35.3, 2.2, 0.55)
for k, f in enumerate((587, 784, 988)):
    add(ping(f, 0.5, 0.4), 36.4 + 0.12 * k)
add(ping(1046, 0.4, 0.5), 38.78)
add(ping(1046, 0.4, 0.5), 39.43)

# ================= báscula =================
add(np.sin(2 * np.pi * 2000 * tt(0.12)) * 0.15, 40.7)
add(np.sin(2 * np.pi * 2000 * tt(0.12)) * 0.15, 40.9)
for k, (f0, f1) in enumerate(((392, 370), (370, 349), (349, 311))):
    t_ = tt(0.45 if k < 2 else 0.9)
    f = np.linspace(f0, f1, len(t_))
    s = np.sin(2 * np.pi * np.cumsum(f) / sr) * (0.6 + 0.4 * np.sin(2 * np.pi * 6 * t_)) * np.exp(-t_ * 1.5)
    add(lp(s + 0.3 * np.sign(s), 1500) * 0.22, 41.45 + 0.45 * k)

# ================= cierre =================
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), 44.4, 0.6)
chord((1047, 1568, 2093), 44.7, 2.4, 0.5)

# ================= CORTES =================
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
