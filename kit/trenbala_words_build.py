"""Arma /home/claude/trenbala_words.py (WORDS para timeline.py): una entrada (inicio, fin) por palabra de la VOZ de cada frase.
Fuente A (ElevenLabs Scribe): /home/claude/words_trenbala_cN.json → se alinea con difflib.
Fuente B (plan B Chatterbox): /home/claude/narr_trenbala_cN.json (inbox) con 'lines' [{text,start,end}] → reparto por letras."""
import json, os, re, sys, difflib, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trenbala_guion as G

OUT = '/home/claude'


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def frases(c):
    return G.REEL_OUT if c == 'out' else G.CAPS[int(c[1:])][1]


def _audio(c):
    import subprocess
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{OUT}/narr_trenbala_{c}.mp3', '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def _recorta(x, a, b, sr=16000):
    """Inicio y fin reales de la voz dentro de [a, b] (energía por cuadros de 20 ms)."""
    import numpy as np
    i0, i1 = int(a * sr), int(b * sr)
    seg_ = x[i0:i1]
    n = 320
    if len(seg_) < n * 3:
        return a, b
    fr = seg_[:len(seg_) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-6)
    thr = max(db.max() - 38, -50)
    on = np.where(db > thr)[0]
    if not len(on):
        return a, b
    return a + on[0] * n / sr, a + (on[-1] + 1) * n / sr


def por_lineas(c):
    d = json.load(open(f'{OUT}/narr_trenbala_{c}.json'))
    L = d['lines']
    ph = frases(c)
    assert len(L) == len(ph), (c, len(L), len(ph))
    x = _audio(c)
    out = []
    for (scr, voz), ln in zip(ph, L):
        ws = voz.split()
        a, b = _recorta(x, float(ln['start']), float(ln['end']))
        a += 0.05
        b -= 0.10
        tot = sum(len(w) + 1 for w in ws)
        acc = a
        for w in ws:
            dd = (b - a) * (len(w) + 1) / tot
            out.append((round(acc, 3), round(acc + dd * 0.92, 3)))
            acc += dd
    return out


def por_scribe(c):
    d = json.load(open(f'{OUT}/words_trenbala_{c}.json'))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(norm(w.get('text', '')), float(w['start']), float(w['end'])) for w in d
          if w.get('type', 'word') == 'word' and norm(w.get('text', ''))]
    vw = [norm(w) for p in frases(c) for w in p[1].split()]
    sm = difflib.SequenceMatcher(None, vw, [w for w, _, _ in tw], autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    out = [None] * len(vw)
    for i in range(len(vw)):
        if i in mp:
            out[i] = (tw[mp[i]][1], tw[mp[i]][2])
    # huecos: interpola entre vecinos
    for i in range(len(out)):
        if out[i] is None:
            j0 = max([j for j in range(i) if out[j]] or [-1])
            j1 = min([j for j in range(i + 1, len(out)) if out[j]] or [len(out)])
            a = out[j0][1] if j0 >= 0 else 0.0
            b = out[j1][0] if j1 < len(out) else a + 0.4 * (j1 - j0)
            n = j1 - j0
            k = i - j0
            out[i] = (a + (b - a) * (k - 0.9) / n, a + (b - a) * k / n)
    return out


if __name__ == '__main__':
    W = {}
    chs = [f'c{i}' for i in range(len(G.CAPS))] + ['out']
    for c in chs:
        if os.path.exists(f'{OUT}/words_trenbala_{c}.json'):
            W[c] = por_scribe(c); src = 'scribe'
        else:
            W[c] = por_lineas(c); src = 'líneas'
        n = sum(len(p[1].split()) for p in frases(c))
        print(c, src, len(W[c]), 'palabras (voz:', n, ')')
    open(f'{OUT}/trenbala_words.py', 'w').write('WORDS = ' + json.dumps(W))
