"""Efectos de sonido del video de la vasectomía. Tiempos por fw() (si existe vasec_sync.py, los de la narración)."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile
import vasec as V

try:
    import vasec_sync
    fw = vasec_sync.fw
    T = vasec_sync.NEWDUR
    OUT = "/home/claude/efectos_vasec_sync.wav"
except ImportError:
    fw = lambda x: x
    T = V.DUR
    OUT = "/home/claude/efectos_vasec.wav"

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


def snip(g=1.0):
    t = tt(0.18)
    click = hp(rng.randn(len(t)), 2500) * np.exp(-t * 60) * 0.9
    ring = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (18 + f / 400)) for f in (2900, 4300, 6100)) * 0.25
    return (click + ring) * g


def clink(f=3200, g=1.0):
    t = tt(0.5)
    return sum(np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (8 + 5 * k)) / k for k in (1, 2.76, 5.4)) * 0.3 * g


def drop(f=900, g=1.0):
    t = tt(0.22)
    fr = f * (1 + 1.4 * np.exp(-t * 30))
    return np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.exp(-t * 18) * 0.5 * g


def sizzle(d=0.8, g=1.0):
    n = int(d * sr)
    x = hp(rng.randn(n), 3500) * (0.5 + 0.5 * (rng.rand(n) > 0.97)) * np.exp(-np.arange(n) / sr * 2.5)
    return x * 0.35 * g


def page(g=1.0):
    t = tt(0.25)
    return bp(rng.randn(len(t)), 1500, 6000) * np.sin(np.pi * t / 0.25) ** 2 * 0.35 * g


# ================= AMBIENTES =================
ANAT = [(6.15, 26.45), (35.55, 44.05), (50.05, 55.25)]
pad_ = (np.sin(2 * np.pi * 110 * t_all) + 0.6 * np.sin(2 * np.pi * 164.8 * t_all + 0.4) + 0.4 * np.sin(2 * np.pi * 220.4 * t_all)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t_all))
pad_ += lp(rng.randn(N), 400, 2) * 0.8
pts = [(0, 0)]
for (a, b) in ANAT:
    pts += [(a + 0.05, 0.32), (b - 0.05, 0.32), (b + 0.01, 0.0)]
pad_ = span(pad_, sorted(pts, key=lambda p: p[0]))
buf += pad_ * 0.25
room = lp(rng.randn(N), 380) * 0.9 + np.sin(2 * np.pi * 120 * t_all) * 0.05
room = span(room, [(0, 0.25), (6.1, 0.25), (6.15, 0), (26.45, 0), (26.5, 0.3), (35.5, 0.3), (35.55, 0), (44.05, 0), (44.1, 0.3), (50.0, 0.3), (50.05, 0)])
buf += room * 0.4
out_amb = lp(rng.randn(N), 900) * 0.6
out_amb = span(out_amb, [(0, 0), (55.2, 0), (55.4, 0.35), (V.DUR, 0.3)])
buf += out_amb * 0.4
for k in range(14):
    t0 = 55.6 + k * 0.5 + 0.17 * (k % 3)
    t3 = tt(0.12)
    f0 = 3800 + 600 * ((k * 5) % 3)
    add(np.sin(2 * np.pi * (f0 + 900 * np.sin(2 * np.pi * 18 * t3)) * t3) * np.exp(-t3 * 20) * 0.12, t0)

# ================= gancho =================
add(clink(2800, 0.8), 0.35)
add(whoosh(0.9), V.T_SNIP - 1.6, 0.4)
add(snip(1.2), V.T_SNIP)
add(thud(90, 0.3, 0.5), V.T_SNIP)
add(ping(220, 1.4, 0.4), WT(0, 14))
add(ping(165, 1.4, 0.3), WT(0, 14) + 0.1)

# ================= modelo anatómico =================
t1 = tt(1.6)
add(sum(np.sin(2 * np.pi * f * t1 + k) for k, f in enumerate((660, 880, 1320))) * np.sin(np.pi * t1 / 1.6) ** 2 * 0.12, 6.2)
chord((523, 784, 1046), WT(1, 3), 1.6, 0.4)

# ================= testículo =================
for k in range(40):
    tk = 8.8 + k * 0.085
    add(ping(1800 + 300 * (k % 4), 0.12, 0.12 + 0.12 * (tk > WT(2, 5))), tk)
counter_ticks(WT(2, 5) - 0.2, 12.3, 22, 2600, 0.22)

# ================= conducto =================
fl = bp(rng.randn(int(4.0 * sr)), 300, 1600) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * tt(4.0)))
add(fade(fl, 0.4, 0.5) * 0.35, 12.7)
add(whoosh(1.2), 13.0, 0.6)

# ================= glándulas =================
for k in range(10):
    add(drop(700 + 120 * (k % 5), 0.5), WT(4, 7) - 0.1 + k * 0.17)
for k in range(10):
    add(drop(520 + 90 * (k % 4), 0.5), WT(4, 10) - 0.1 + k * 0.15)

# ================= tubo de ensayo =================
for (t0, f) in ((WT(5, 1) - 0.2, 380), (WT(5, 3), 460), (WT(5, 8), 620)):
    pour = bp(rng.randn(int(0.9 * sr)), f, f * 4) * np.sin(np.pi * tt(0.9) / 0.9) * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * tt(0.9)))
    add(pour * 0.4, t0)
add(ping(1568, 0.8, 0.5), WT(5, 10))
add(ping(2093, 0.8, 0.35), WT(5, 10) + 0.08)

# ================= consultorio =================
for t0 in (26.8, WT(6, 1), WT(6, 4)):
    add(clink(3000 + 300 * ((int(t0 * 10)) % 3), 0.6), t0)
for k in range(5):
    add(beep(1000, 0.08, 0.25), 27.0 + k * 0.9)

# ================= procedimiento =================
add(clink(2400, 0.7), 31.3)
add(snip(1.0), V.T_CUTP)
add(sizzle(0.9, 1.0), V.T_SEAL)
add(sizzle(0.6, 0.8), V.T_SEAL + 0.35)
counter_ticks(WT(7, 7) - 0.2, WT(7, 10) + 0.4, 15, 2200, 0.25)

# ================= después =================
add(thud(60, 0.5, 0.8), WT(8, 4))
add(beep(330, 0.25, 0.6), WT(8, 4))
t2 = tt(1.6)
add(np.sin(2 * np.pi * (1800 - 900 * t2 / 1.6) * t2) * np.exp(-t2 * 1.5) * 0.15 + hp(rng.randn(len(t2)), 4000) * np.exp(-t2 * 2.5) * 0.05, WT(8, 9))

# ================= hormonas =================
chord((392, 494, 587), WT(9, 3), 1.6, 0.35)
add(whoosh(1.0), 40.4, 0.4)

# ================= laboratorio =================
add(clink(1800, 0.5), 44.4)
for k in range(11):
    add(page(0.8), WT(10, 7) - 0.3 + k * (WT(10, 10) + 0.9 - WT(10, 7)) / 11)
chord((784, 988, 1175), WT(10, 12) + 0.1, 1.2, 0.45)

# ================= estadísticas =================
add(riser(1.4, 300, 1200, 0.25), WT(11, 2) - 0.3)
add(ping(1760, 1.0, 0.5), WT(11, 4) + 0.3)
for k in range(2):
    t4 = tt(0.22)
    add((np.sign(np.sin(2 * np.pi * 170 * t4)) * 0.22 + np.sin(2 * np.pi * 340 * t4) * 0.2) * np.exp(-t4 * 4), WT(11, 6) + k * 0.25, 0.6)

# ================= hospital =================
chord((659, 880, 1046), WT(12, 10), 1.4, 0.4)

# ================= cierre y cortes =================
sh = tt(2.4)
shim = sum(np.sin(2 * np.pi * f * sh + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (3 + k) * sh)) for k, f in enumerate((1320, 1760, 2093, 2637))) * 0.10
add(fade(shim * np.sin(np.pi * sh / 2.4) ** 1.5, 0.3, 0.8), V.T_OUT, 0.6)
chord((1047, 1568, 2093), V.T_OUT + 0.3, 2.4, 0.5)
for ct in CUTS:
    add(whoosh(0.6), ct - 0.3, 0.7)

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
