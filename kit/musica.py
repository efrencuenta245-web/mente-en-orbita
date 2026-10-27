"""Pista musical de fondo generada 100 % por código (sin derechos de autor de terceros).
Uso: python3 musica.py DURACION_S salida.wav [semilla] [bpm] [fin_de_la_voz_s]
Estilo: electrónica suave y curiosa (pad + arpegio pluck + bajo + golpe ligero), pensada para ir
muy por debajo de la voz (la mezcla la baja aún más cuando habla el narrador)."""
import sys
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

SR = 44100


def lp(x, fc, order=2):
    b, a = butter(order, min(0.99, fc / (SR / 2)), 'low')
    return lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'high')
    return lfilter(b, a, x)


def note_hz(n):  # n = semitonos desde La4 (440)
    return 440.0 * 2 ** (n / 12)


def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n); e[:na] = np.linspace(0, 1, na)
    nd = min(nd, n - na); e[na:na + nd] = np.linspace(1, s, nd)
    nr = min(nr, n); e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def saw(f, n, ph=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + ph) % 1.0) - 1


def pluck(f, n, rng, damp=0.996):
    """Karplus-Strong."""
    p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = damp * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out


def main(dur, out, seed=3, bpm=96, outro_t=None):
    rng = np.random.RandomState(seed)
    N = int(dur * SR)
    L = np.zeros(N); R = np.zeros(N)
    beat = 60.0 / bpm
    bar = 4 * beat
    # progresiones en La menor (semitonos desde La4): Am F C G  /  Am Em F G
    progs = [[(-12, -9, -5), (-16, -12, -9), (-21, -17, -14), (-14, -10, -7)],
             [(-12, -9, -5), (-17, -14, -10), (-16, -12, -9), (-14, -10, -7)]]
    prog = progs[seed % 2]
    nbars = int(np.ceil(dur / bar)) + 1
    for bi in range(nbars):
        t0 = bi * bar
        i0 = int(t0 * SR)
        if i0 >= N:
            break
        ch = prog[bi % 4]
        n = min(int(bar * SR * 1.05), N - i0)
        # pad: sierras desafinadas, filtradas y con ataque lento
        pad = np.zeros(n)
        for k, nt in enumerate(ch):
            f = note_hz(nt)
            for dt in (-0.12, 0.0, 0.11):
                pad += saw(f * 2 ** (dt / 12), n, rng.rand())
        pad = lp(pad, 900 + 500 * np.sin(bi * 0.7) ** 2, 2) * env_adsr(n, 0.6, 0.4, 0.8, 0.5) * 0.05
        L[i0:i0 + n] += pad * 0.9; R[i0:i0 + n] += pad
        if bi == 0:
            continue  # primer compás solo pad (entrada suave)
        # bajo: nota raíz, dos golpes por compás
        root = note_hz(ch[0] - 12)
        for k in (0, 2.5):
            j0 = i0 + int(k * beat * SR)
            m = min(int(beat * 1.4 * SR), N - j0)
            if m <= 0:
                continue
            tt = np.arange(m) / SR
            b = np.sin(2 * np.pi * root * tt) * env_adsr(m, 0.01, 0.3, 0.6, 0.2) * 0.16
            L[j0:j0 + m] += b; R[j0:j0 + m] += b
        # arpegio pluck en corcheas
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12]
        for k, nt in enumerate(arp):
            j0 = i0 + int(k * beat / 2 * SR)
            m = min(int(beat * 1.2 * SR), N - j0)
            if m <= 0:
                continue
            pl = pluck(note_hz(nt), m, rng) * env_adsr(m, 0.002, 0.2, 0.5, 0.1) * 0.07
            pan = 0.5 + 0.35 * np.sin(k * 1.3)
            L[j0:j0 + m] += pl * (1 - pan) * 1.4; R[j0:j0 + m] += pl * pan * 1.4
        # golpe suave (bombo) y hi-hat
        for k in range(4):
            j0 = i0 + int(k * beat * SR)
            m = min(int(0.25 * SR), N - j0)
            if m > 0 and k in (0, 2):
                tt = np.arange(m) / SR
                kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14) * 0.22
                L[j0:j0 + m] += kick; R[j0:j0 + m] += kick
            jh = i0 + int((k + 0.5) * beat * SR)
            m = min(int(0.06 * SR), N - jh)
            if m > 0:
                hh = hp(rng.randn(m), 7000) * np.exp(-np.arange(m) / SR * 60) * 0.035
                L[jh:jh + m] += hh * 0.7; R[jh:jh + m] += hh
    # eco sencillo para dar espacio
    d = int(beat * 0.75 * SR)
    L[d:] += 0.22 * R[:-d]; R[d:] += 0.22 * L[:-d]
    # cierre: cuando la voz termina (outro_t), la música sube para que nunca quede en silencio
    if outro_t is not None and outro_t < dur:
        i0 = int(outro_t * SR)
        ramp = np.clip((np.arange(N - i0) / SR) / 0.5, 0, 1)
        g = 1.0 + 0.8 * ramp
        L[i0:] *= g; R[i0:] *= g
    # fundido de salida corto (solo el final)
    fo = int(0.5 * SR)
    L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
    st = np.stack([L, R], 1)
    rms = np.sqrt(np.mean(st ** 2)) + 1e-9
    st = st / rms * 10 ** (-20 / 20)
    st = np.tanh(st / 0.9) * 0.9
    wavfile.write(out, SR, (st * 32767).astype(np.int16))
    print('música', out, round(dur, 2), 's')


if __name__ == '__main__':
    main(float(sys.argv[1]), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3, float(sys.argv[4]) if len(sys.argv) > 4 else 96,
         float(sys.argv[5]) if len(sys.argv) > 5 else None)
