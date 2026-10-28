"""Efectos de sonido del video de Starlink (largo y Shorts). Uso: SLMODE=full ... python3 sfx_starlink.py -> efectos_starlink_MODO.wav
(requiere VIDEO_TL, MOTOR_TEMA y GTA_FMT como el render)."""
import os, math
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile
import starlink as V
import escenas as ES
ES.CARD.update(V.CARDS)
ES.SH[:] = ES.build_shots(V.SHOTS)
MODE = os.environ.get('SLMODE', 'full')

sr = 44100
T = ES.DUR
N = int(T * sr)
rng = np.random.RandomState(28)
buf = np.zeros(N)
OUT = f"/home/claude/efectos_starlink_{MODE}.wav"


def tt(d):
    return np.arange(int(max(0.01, d) * sr)) / sr


def add(sig, t0, g=1.0):
    if t0 is None:
        return
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
    if a > 0: x[:min(a, n)] *= np.linspace(0, 1, min(a, n))
    if b > 0: x[-min(b, n):] *= np.linspace(1, 0, min(b, n))
    return x


def whoosh(d=0.6):
    t = tt(d); n = len(t)
    nz = rng.randn(n)
    low = lp(nz, 700) * 3.0
    high = bp(nz, 2000, 7000) * 1.6
    e1 = np.sin(np.pi * np.clip(t / d * 1.5, 0, 1)) ** 2 * (t / d < 0.67)
    e2 = np.sin(np.pi * np.clip((t / d - 0.25) / 0.75, 0, 1)) ** 2
    return fade(low * e1 + high * e2, 0.02, 0.05) * 0.45


def tick(f=1500, d=0.04, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * g * 0.6


def thud(f=70, d=0.35, g=1.0):
    t = tt(d)
    return np.sin(2 * np.pi * (f + 60 * np.exp(-t * 30)) * t) * np.exp(-t * 11) * g


def ping(f, d=0.5, g=1.0):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.exp(-t * (5.0 / d)) * g * 0.5


def pop(g=0.5):
    t = tt(0.12)
    f = 500 + 900 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 35) * g


def click(g=0.25):
    t = tt(0.02)
    return hp(rng.randn(len(t)), 2500) * np.exp(-t * 300) * g


def glitch(d=0.35, g=0.4):
    t = tt(d)
    sq = np.sign(np.sin(2 * np.pi * 180 * t)) * (np.sin(2 * np.pi * 23 * t) > 0)
    return (sq * 0.3 + bp(rng.randn(len(t)), 1500, 6000) * 0.6) * np.exp(-t * 6) * g


def escaner(g=1.0):
    d = 1.8
    t = tt(d)
    f = 320 + 1900 * (t / d) ** 1.4
    ph = 2 * np.pi * np.cumsum(f) / sr
    sweep = np.sin(ph) * np.sin(np.pi * t / d) ** 0.8 * 0.28
    shimmer = sum(np.sin(2 * np.pi * fr * t + k) * (0.5 + 0.5 * np.sin(2 * np.pi * (9 + 3 * k) * t))
                  for k, fr in enumerate((2637, 3136, 3951))) * 0.035 * np.sin(np.pi * t / d) ** 2
    return (sweep + shimmer) * g


def counter_ticks(a, b, n, f=2400, g=0.3):
    if a is None:
        return
    for k in range(n):
        u = (k / max(1, n - 1)) ** 0.6
        add(tick(f + 400 * (k % 2), 0.03, g), a + (b - a) * u)


def cash(g=0.4):
    t = tt(0.6)
    return sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 7) for f in (2093, 2637, 3136)) * g * 0.3


# cortes de escena
for s in ES.SH[1:]:
    if s['card']:
        continue
    add(whoosh(0.55), s['t0'] - 0.25, 0.6)

# tarjetas en blanco y negro
for s in ES.SH:
    if not s['card']:
        continue
    t0 = s['t0']
    c = s['key'][1]
    style = ES.CARD[c][2]
    add(whoosh(0.9), t0 - 0.45, 0.9)
    if style == 'error':
        add(glitch(0.4, 0.5), t0 + 1.0)
        add(thud(80, 0.3, 0.6), t0 + 0.05)
    elif style == 'ruler':
        counter_ticks(t0 + 0.1, t0 + 2.2, 18, 2200, 0.25)
    else:
        add(thud(75, 0.35, 0.7), t0 + 0.1)
    for k in range(len(ES.CARD[c][1])):
        add(click(0.18), t0 + 0.3 + 0.9 * k / len(ES.CARD[c][1]))


def S(key):
    for s in ES.SH:
        if s['key'] == key:
            return s['t0']
    return None


def beep(f=1200, d=0.12, g=0.3):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 18) * g


# escáner de rayos X (sello)
x = S(('c2', 2))
add(escaner(1.0), x + 0.2 if x is not None else None)
# contadores
for key, d, n in ((('c0', 0), 2.4, 22), (('c0', 2), 1.4, 14), (('c1', 2), 2.6, 18), (('c3', 2), 1.6, 16),
                  (('c3', 3), 1.0, 10), (('c3', 4), 1.8, 14), (('c3', 6), 2.8, 22), (('c4', 1), 5.5, 30),
                  (('c4', 2), 2.2, 20), (('c5', 3), 2.0, 16), (('c5', 5), 3.0, 22)):
    x = S(key)
    if x is not None:
        counter_ticks(x + 0.4, x + 0.4 + d, n, 2400, 0.2)
# señal que sube / rebota (pitidos de datos)
for key in (('c0', 1), ('c0', 4), ('c1', 4), ('c1', 6), ('c2', 6), ('c3', 1), ('c6', 1)):
    x = S(key)
    if x is not None:
        add(beep(1400, 0.15, 0.25), x + 0.5)
        add(beep(1800, 0.15, 0.2), x + 0.7)
x = ES.WS('c2', 6, 'salta')
add(ping(1320, 0.6, 0.4), x)
# esquive y propulsor
x = S(('c4', 1))
add(whoosh(0.5), x + 1.5 if x is not None else None, 0.8)
x = ES.WS('c4', 4, 'mueven')
add(whoosh(0.4), x, 0.6)
# reentrada: fuego
x = S(('c4', 7))
if x is not None:
    t = tt(3.0)
    fire = lp(rng.randn(len(t)), 900) * np.sin(np.pi * t / 3.0) ** 2 * 0.5
    add(fire, x + 1.0, 0.7)
# precios
for key in (('c5', 2), ('c5', 3)):
    x = S(key)
    if x is not None:
        add(cash(0.45), x + 1.2)
x = S(('c5', 2))
add(pop(0.45), x + 0.3 if x is not None else None)
# lotería -> antena
x = ES.WS('c2', 3, 'casillas')
add(glitch(0.3, 0.25), x)
# resumen
for w in ('antena', 'láseres', 'miles'):
    add(pop(0.35), ES.WS('c6', 0, w))
# sí / no
for key in (('c6', 3), ('out', 1)):
    x = S(key)
    if x is not None:
        add(ping(880, 0.6, 0.35), x + 0.5)
        add(ping(660, 0.6, 0.35), x + 0.62)

buf = np.tanh(buf * 0.9) * 0.9
st = np.stack([buf, np.roll(buf, 90) * 0.96], 1)
wavfile.write(OUT, sr, (st * 32767).astype(np.int16))
print('ok', OUT, round(T, 2))
