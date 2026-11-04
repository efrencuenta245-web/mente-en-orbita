"""Efectos de sonido del video «el norte» (sincronizados con norte.py). Uso: python3 norte_sfx.py salida.wav"""
import sys, os
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_demo import SR, sub_hit, riser, whoosh, burst, tick, slap, scribble, click, chime, shimmer, thud, bass_hit

T = [(0.25, 3.43), (4.16, 5.98), (6.70, 10.93), (11.72, 15.57), (16.52, 21.65), (22.49, 26.62), (27.31, 33.32),
     (34.11, 38.69), (39.51, 42.21), (42.86, 48.29), (49.29, 54.81), (55.70, 57.51), (58.23, 60.92)]
DUR = 61.5


def build(out):
    L = np.zeros(int(DUR * SR) + SR)

    def add(x, t0, g=1.0):
        i = max(0, int(t0 * SR))
        x = np.asarray(x) * g
        L[i:i + len(x)] += x[:max(0, len(L) - i)]
    c = [a - 0.2 for a, _ in T]
    s = [a for a, _ in T]
    add(sub_hit(), 0.0)
    add(whoosh(0.5, 300, 1600), 0.15, 0.35)
    add(tick(1600, 0.05, 0.6), 2.5)                                  # pill SIN INTERNET
    add(whoosh(0.35, 500, 4200), c[1] - 0.22, 0.9)                   # whip
    add(tick(1800, 0.05, 0.6), s[1] + 0.05); add(tick(2000, 0.05, 0.6), s[1] + 0.4)
    add(scribble(0.3), s[1] + 0.55, 0.8); add(scribble(0.3), s[1] + 0.95, 0.8)
    add(riser(0.8), c[2] - 0.95, 0.6)
    add(whoosh(0.42, 300, 5000), c[2] - 0.2, 1.0); add(thud(), c[2] + 0.15, 0.6)
    add(shimmer(0.7), s[2], 0.9)                                     # rayos X
    add(scribble(0.5), s[2] + 1.0, 0.9)
    add(click(), s[2] + 2.0); add(click(), s[2] + 2.6)               # zoom digital
    add(tick(1600, 0.05, 0.6), s[2] + 3.15)
    add(whoosh(0.4, 400, 4500), c[3] - 0.35, 0.9); add(burst(), c[3], 0.9)
    add(slap(), s[3] + 3.5, 0.9)                                     # cae la foto
    add(riser(0.6), c[4] - 0.75, 0.5)
    add(whoosh(0.42, 300, 4000), c[4] - 0.2, 0.9)
    add(sub_hit(0.9), s[4] + 0.3, 0.55)                              # aparece el núcleo
    add(whoosh(1.6, 900, 2400), s[4] + 2.4, 0.3)                     # líneas de campo
    add(tick(1700, 0.05, 0.6), s[4] + 3.0)
    add(whoosh(0.35, 800, 3000), c[5] - 0.2, 0.8)                    # barrido
    t0 = s[5] - 0.1
    add(chime(660), t0 + 0.25, 0.8); add(chime(988), t0 + 0.53, 1.0)
    add(scribble(0.45), s[5] + 0.5, 0.9)
    add(bass_hit(), s[5] + 2.4, 0.9)
    add(whoosh(0.42, 300, 5000), c[6] - 0.2, 0.9); add(thud(), c[6] + 0.15, 0.6)
    for j in range(3):
        add(tick(1800 + 300 * j, 0.05, 0.7), s[6] + 1.6 + 0.3 * j)
    add(chime(1318), s[6] + 2.6, 0.45)
    add(whoosh(1.4, 300, 1200), s[6] + 4.2, 0.3)                     # gira el celular
    add(whoosh(0.35, 500, 4200), c[7] - 0.22, 0.9)                   # whip
    add(tick(1500, 0.05, 0.6), s[7] + 1.1)
    add(riser(1.6), s[7] + 1.0, 0.55)                                # se acerca el imán
    add(burst(0.4), s[7] + 2.7, 0.8)
    rng = np.random.RandomState(4)
    for k in range(22):                                              # brújula loca
        add(tick(900 + rng.rand() * 2600, 0.025, 0.5), s[7] + 2.75 + k * 0.07 + rng.rand() * 0.03)
    add(whoosh(0.35, 500, 4200), c[8] - 0.17, 0.8)
    add(shimmer(0.6), s[8] + 0.3, 0.7); add(tick(1500, 0.05, 0.6), s[8] + 0.4)
    add(scribble(0.5), s[8] + 1.0, 0.8)
    add(riser(0.5), c[9] - 0.55, 0.6); add(burst(), c[9] - 0.05, 1.0)  # destello
    add(whoosh(0.8, 300, 900), s[9] + 1.6, 0.35)                     # aparece el 8
    for k in range(3):
        add(whoosh(1.1, 600, 2000), s[9] + 1.45 + 1.1 * k, 0.22)     # movimiento en 8
    add(chime(988), s[9] + 4.0, 0.8); add(chime(1318), s[9] + 4.12, 0.8)  # calibrado
    add(whoosh(0.35, 800, 3000), c[10] - 0.2, 0.8)
    t0 = s[10] - 0.1
    for k, f in enumerate((660, 784, 988, 1318)):
        add(chime(f), t0 + 0.25 + 0.28 * k, 0.9)
    add(bass_hit(), c[11] - 0.36); add(bass_hit(), c[11] - 0.24); add(bass_hit(), c[11] - 0.12)
    add(riser(0.8), c[12] - 0.95, 0.5)
    add(whoosh(0.42, 300, 5000), c[12] - 0.2, 0.9); add(thud(), c[12] + 0.15, 0.5)
    add(riser(0.9), DUR - 0.95, 0.45)                                # vuelve al inicio (loop)
    L = L[:int(DUR * SR)]
    L = L / (np.max(np.abs(L)) + 1e-9) * 0.89
    wavfile.write(out, SR, (L * 32767).astype(np.int16))


if __name__ == '__main__':
    build(sys.argv[1])
