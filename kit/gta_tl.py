"""Línea de tiempo: arma la voz editada y los tiempos por frase/palabra a partir de una lista de edición.
Uso: python3 gta_tl.py MODO   (MODO = full | reelA | reelB)  -> narr_gta_MODO.wav y tl_gta_MODO.json"""
import sys, json, re, subprocess
import numpy as np
from scipy.io import wavfile
import gta_guion as G
from gta_words import WORDS

SR = 48000
CH = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6']
PH = {c: G.CAPS[i][1] for i, c in enumerate(CH)}
PH['out'] = G.REEL_OUT

EDITS = {
    'full': [('gap', 0.25), ('c0', 0, 6), ('gap', 1.5), ('c1', 0, 8), ('gap', 1.5), ('c2', 0, 6), ('gap', 1.5),
             ('c3', 0, 6), ('gap', 1.5), ('c4', 0, 8), ('gap', 1.5), ('c5', 0, 8), ('gap', 1.2), ('c6', 0, 4), ('gap', 2.2)],
    'reelA': [('gap', 0.15), ('c0', 0, 4), ('c0', 6, 6), ('gap', 0.45), ('c1', 1, 7), ('gap', 0.6), ('out', 0, 1), ('gap', 1.6)],
    'reelB': [('gap', 0.15), ('c4', 1, 8), ('gap', 0.45), ('c5', 2, 3), ('gap', 0.6), ('out', 0, 1), ('gap', 1.6)],
}
GAP_MAX = 0.55   # pausa máxima entre frases dentro de un tramo
PAD_A, PAD_B = 0.05, 0.14

UNI = ['cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'once', 'doce', 'trece',
       'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve', 'veinte', 'veintiuno', 'veintidós',
       'veintitrés', 'veinticuatro', 'veinticinco', 'veintiséis', 'veintisiete', 'veintiocho', 'veintinueve']
DEC = {30: 'treinta', 40: 'cuarenta', 50: 'cincuenta', 60: 'sesenta', 70: 'setenta', 80: 'ochenta', 90: 'noventa'}
CEN = {100: 'cien', 200: 'doscientos', 300: 'trescientos', 400: 'cuatrocientos', 500: 'quinientos', 600: 'seiscientos',
       700: 'setecientos', 800: 'ochocientos', 900: 'novecientos'}


def n2w(n):
    if n < 30:
        return UNI[n]
    if n < 100:
        d, u = n // 10 * 10, n % 10
        return DEC[d] + ('' if u == 0 else ' y ' + UNI[u])
    if n < 1000:
        c, r = n // 100 * 100, n % 100
        if r == 0:
            return CEN[c]
        return ('ciento' if c == 100 else CEN[c]) + ' ' + n2w(r)
    m, r = n // 1000, n % 1000
    s = 'mil' if m == 1 else n2w(m) + ' mil'
    return s if r == 0 else s + ' ' + n2w(r)


SPOK = {'GTA': 3, 'PS3': 2, 'PS4': 2, 'PS5': 2, 'PC': 1, 'km': 1, 'Fire': 1}


def spoken_count(w):
    k = w.strip('.,:;…?!¿¡«»"')
    if not k:
        return 0
    if k in SPOK:
        return SPOK[k]
    if re.fullmatch(r'[\d,]+', k):
        return len(n2w(int(k.replace(',', ''))).split())
    return 1


def phrase_words(c, i):
    """Devuelve [(palabra_pantalla, t0, t1)] en tiempo local del mp3 del capítulo."""
    voice_counts = [len(p[1].split()) for p in PH[c]]
    off = sum(voice_counts[:i])
    vw = WORDS[c][off:off + voice_counts[i]]
    disp = PH[c][i][0].split()
    cnt = [spoken_count(w) for w in disp]
    out = []
    if sum(cnt) == len(vw):
        k = 0
        for w, n in zip(disp, cnt):
            if n == 0:
                t0 = out[-1][2] if out else vw[0][0]
                out.append((w, t0, t0))
                continue
            out.append((w, vw[k][0], vw[k + n - 1][1]))
            k += n
    else:
        print('aviso: reparto proporcional en', c, i, sum(cnt), len(vw), file=sys.stderr)
        a, b = vw[0][0], vw[-1][1]
        L = [len(w) + 2 for w in disp]
        tot = sum(L); acc = a
        for w, l in zip(disp, L):
            d = (b - a) * l / tot
            out.append((w, acc, acc + d)); acc += d
    return out, vw[0][0], vw[-1][1]


def load(c):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'/home/claude/narr_gta_{c}.mp3', '-ac', '1', '-ar', str(SR),
                          '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768


def build(mode):
    audio = []
    t = 0.0
    phrases = []
    cache = {}
    for it in EDITS[mode]:
        if it[0] == 'gap':
            audio.append(np.zeros(int(it[1] * SR), np.float32)); t += it[1]
            continue
        c, i0, i1 = it
        if c not in cache:
            cache[c] = load(c)
        x = cache[c]
        for i in range(i0, i1 + 1):
            words, a, b = phrase_words(c, i)
            a0, b0 = max(0.0, a - PAD_A), min(len(x) / SR, b + PAD_B)
            seg = x[int(a0 * SR):int(b0 * SR)].copy()
            n = len(seg)
            f = int(0.012 * SR)
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
            off = t - a0
            phrases.append({'c': c, 'i': i, 'a': a + off, 'b': b + off,
                            'words': [(w, w0 + off, w1 + off) for w, w0, w1 in words], 'text': PH[c][i][0]})
            audio.append(seg); t += n / SR
            if i < i1:
                # pausa original entre frases, con tope
                _, na, _ = phrase_words(c, i + 1)
                g = min(GAP_MAX, max(0.12, (na - PAD_A) - b0))
                audio.append(np.zeros(int(g * SR), np.float32)); t += g
    y = np.concatenate(audio)
    wavfile.write(f'/home/claude/narr_gta_{mode}.wav', SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
    voice_end = phrases[-1]['b']
    json.dump({'dur': len(y) / SR, 'voice_end': voice_end, 'phrases': phrases}, open(f'/home/claude/tl_gta_{mode}.json', 'w'),
              ensure_ascii=False, indent=0)
    print(mode, 'duración', round(len(y) / SR, 2), 's; fin de voz', round(voice_end, 2))


if __name__ == '__main__':
    for m in (sys.argv[1:] or ['full', 'reelA', 'reelB']):
        build(m)
