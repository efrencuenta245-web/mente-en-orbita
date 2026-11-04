"""Efectos de sonido sintetizados para la prueba del estilo nuevo (todo por código, sin derechos de terceros).
Cada cambio visual lleva su sonido: golpe grave al abrir, subida antes de cada transición, whoosh al atravesar,
ráfaga de ruido en el destello, ticks por palabra, golpe de papel al caer la foto, garabato, clics del zoom
digital, campanitas al crecer las barras y golpes de bajo en los cortes rítmicos."""
import sys
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

SR = 48000


def lp(x, f, o=2):
    b, a = butter(o, min(0.99, f / (SR / 2)), 'low'); return lfilter(b, a, x)


def hp(x, f, o=2):
    b, a = butter(o, f / (SR / 2), 'high'); return lfilter(b, a, x)


def bp(x, f0, f1, o=2):
    b, a = butter(o, [f0 / (SR / 2), min(0.99, f1 / (SR / 2))], 'band'); return lfilter(b, a, x)


def env(n, a=0.005, r=0.2):
    e = np.ones(n)
    na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    e *= np.exp(-np.arange(n) / (r * SR))
    return e


rng = np.random.RandomState(4)


def noise(d):
    return rng.uniform(-1, 1, int(d * SR))


def sub_hit(d=1.1):
    n = int(d * SR); t = np.arange(n) / SR
    f = 34 + 40 * np.exp(-t * 9)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    x += 0.35 * lp(noise(d), 300) * np.exp(-t * 30)
    return x * 0.9


def riser(d=1.0):
    n = int(d * SR); t = np.arange(n) / SR
    k = (t / d) ** 2
    x = np.zeros(n)
    nz = noise(d)
    for i in range(8):
        a, b = i * n // 8, (i + 1) * n // 8
        fc = 300 + 5000 * ((i + 0.5) / 8) ** 2
        x[a:b] = bp(nz, fc * 0.6, fc * 1.4)[a:b]
    x += 0.25 * np.sin(2 * np.pi * np.cumsum(180 + 700 * k) / SR)
    return x * k * 0.5


def whoosh(d=0.45, f0=400, f1=3500):
    n = int(d * SR); t = np.arange(n) / SR
    nz = noise(d)
    x = np.zeros(n)
    for i in range(10):
        a, b = i * n // 10, (i + 1) * n // 10
        u = (i + 0.5) / 10
        fc = f0 + (f1 - f0) * np.sin(np.pi * u)
        x[a:b] = bp(nz, fc * 0.5, fc * 1.5)[a:b]
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return x * e * 0.9


def burst(d=0.35):
    t = np.arange(int(d * SR)) / SR
    return hp(noise(d), 1500) * np.exp(-t * 11) * 0.6


def tick(f=2200, d=0.03, g=0.25):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 160) * g


def slap(d=0.18):
    t = np.arange(int(d * SR)) / SR
    x = bp(noise(d), 500, 3000) * np.exp(-t * 45) * 0.8
    x += np.sin(2 * np.pi * 110 * t) * np.exp(-t * 25) * 0.5
    return x


def scribble(d=0.5):
    n = int(d * SR); t = np.arange(n) / SR
    x = bp(noise(d), 1800, 6000)
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 11 * t + 3 * np.sin(2 * np.pi * 3 * t)))
    return x * lp(am, 60) * 0.35 * np.sin(np.pi * t / d) ** 0.5


def click():
    return np.concatenate([tick(3200, 0.02, 0.5), np.zeros(int(0.05 * SR)), tick(2400, 0.03, 0.45)]) + 0


def chime(f, d=0.6):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2.01 * f * t)) * np.exp(-t * 6) * 0.22


def shimmer(d=0.6):
    t = np.arange(int(d * SR)) / SR
    x = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((2100, 2650, 3170, 3990)))
    return x * np.sin(np.pi * t / d) ** 2 * 0.06


def thud(d=0.5):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * (48 + 30 * np.exp(-t * 14)) * t) * np.exp(-t * 7) * 0.8


def bass_hit(d=0.35):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * 55 * t) + 0.3 * lp(noise(d), 200)) * np.exp(-t * 9) * 0.7


def build(dur, out):
    L = np.zeros(int(dur * SR) + SR)

    def add(x, t0, g=1.0):
        i = int(t0 * SR)
        x = np.asarray(x) * g
        L[i:i + len(x)] += x[:max(0, len(L) - i)]
    add(sub_hit(), 0.0)
    add(whoosh(0.5, 300, 1600), 0.15, 0.35)          # título entra con desenfoque
    add(riser(1.0), 1.6, 0.8)                         # sube hacia la transición
    add(whoosh(0.42, 300, 5000), 2.55, 1.0)           # atraviesa la escena
    add(thud(), 2.95, 0.7)
    for i in range(6):                                # palabra por palabra
        add(tick(2300 + 120 * i), 3.15 + 0.22 * i, 0.8)
    add(whoosh(1.0, 900, 2400), 3.2, 0.25)            # se dibujan las líneas de campo
    add(slap(), 3.88, 0.9)                            # cae la foto
    add(riser(0.45), 5.15, 0.6)
    add(burst(), 5.62, 1.0)                           # destello
    add(shimmer(0.7), 6.0, 1.0)                       # entra el rayo X
    add(tick(1600, 0.05, 0.6), 6.62)                  # aparece la etiqueta
    add(scribble(0.5), 7.0, 1.0)                      # garabato vivo
    for i in range(6):
        add(tick(2300 + 120 * i), 7.0 + 0.22 * i, 0.6)
    add(click(), 7.5); add(click(), 8.0)              # zoom digital
    add(whoosh(0.4, 400, 4500), 8.9, 0.9)             # acercamiento al chip
    add(thud(), 9.3, 0.9)
    for i, f in enumerate((660, 784, 988, 1318)):     # barras que crecen
        add(chime(f), 9.6 + 0.28 * i, 1.0)
    add(whoosh(0.6, 300, 1500), 10.7, 0.3)
    add(bass_hit(), 11.9); add(bass_hit(), 12.05)     # cortes rítmicos
    add(riser(0.7), 12.2, 0.5)                        # vuelve al inicio (loop)
    L = L[:int(dur * SR)]
    L = L / (np.max(np.abs(L)) + 1e-9) * 0.89
    wavfile.write(out, SR, (L * 32767).astype(np.int16))


if __name__ == '__main__':
    build(float(sys.argv[1]), sys.argv[2])
