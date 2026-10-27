"""Sincronización automática video <-> narración (sin MAP manual).

Uso típico (archivo MODULO_sync.py):
    import sys; sys.path.insert(0, '/home/claude')
    import autosync as A
    A.setup('popo', '/home/claude/narr_popo.mp3', SPOKEN={'72': 'setentaydos'})
    fw, bw, NEWDUR, NF = A.fw, A.bw, A.NEWDUR, A.NF
    if __name__ == '__main__':
        A.main(sys.argv)

Pasos:
1. silencedetect encuentra los tramos de voz (SEG).
2. Programación dinámica reparte los tramos entre las frases del guion (MAP),
   comparando la duración de cada grupo con la longitud hablada de la frase
   y premiando las pausas largas como fronteras de frase.
3. Dentro de cada frase, cada tramo extra empieza en la palabra más cercana
   a su fracción de tiempo (preferencia por palabras tras coma/puntos).
4. Se recortan pausas (GAP_IN dentro de frase, GAP_OUT entre frases) y se
   construye la deformación de tiempo OLD->NEW igual que en tiempo_sync.py.
"""
import sys, os, re, subprocess, importlib
import numpy as np
from PIL import Image
from scipy.io import wavfile

BASE = '/home/claude'
if BASE not in sys.path:
    sys.path.insert(0, BASE)

PUNCT = '.,:;…?!¿¡«»"'
CFG = {}
V = anim = None
SEG = MAP = NSEG = SEGN = PIECES = None
OLD = NEW = None
NEWDUR = NF = VOICE_LEN = 0.0
CUR = [0.0]


def silences(src, db=-38, d=0.18):
    """Tramos con voz [(ini, fin)] según silencedetect."""
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", src, "-af", f"silencedetect=noise={db}dB:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                               capture_output=True, text=True).stdout.strip())
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    segs, t = [], 0.0
    for s, e in zip(st, en + [dur] * (len(st) - len(en))):
        if s - t > 0.06:
            segs.append((round(t, 3), round(s, 3)))
        t = e
    if dur - t > 0.06:
        segs.append((round(t, 3), round(dur, 3)))
    return segs


def wlen(w, spoken):
    k = w.strip(PUNCT)
    return len(spoken.get(k, k)) + 2


def auto_map(seg, phrases_words, spoken):
    """phrases_words: lista de listas de palabras. Devuelve MAP [[(w0, s), ...], ...]."""
    K, N = len(seg), len(phrases_words)
    assert K >= N, f"hay {K} tramos de voz y {N} frases: baja el umbral de silencio"
    L = np.array([sum(wlen(w, spoken) for w in ws) for ws in phrases_words], float)
    dseg = np.array([b - a for a, b in seg])
    rate = dseg.sum() / L.sum()
    gap = np.array([0.0] + [seg[i][0] - seg[i - 1][1] for i in range(1, K)])
    csum = np.concatenate([[0.0], np.cumsum(dseg)])
    INF = 1e18
    dp = np.full((N + 1, K + 1), INF)
    bk = np.zeros((N + 1, K + 1), int)
    dp[0, 0] = 0.0
    for j in range(1, N + 1):
        e = L[j - 1] * rate
        for b in range(j, K - (N - j) + 1):
            best, arg = INF, -1
            for a in range(j - 1, b):
                if dp[j - 1, a] >= INF:
                    continue
                s = csum[b] - csum[a]
                c = 10.0 * ((s - e) / max(e, 0.6)) ** 2
                if j > 1:
                    c -= 1.6 * min(gap[a], 0.9)
                v = dp[j - 1, a] + c
                if v < best:
                    best, arg = v, a
            dp[j, b], bk[j, b] = best, arg
    cuts, b = [], K
    for j in range(N, 0, -1):
        a = bk[j, b]
        cuts.append((a, b))
        b = a
    cuts.reverse()
    MAPx = []
    for (a, b), ws in zip(cuts, phrases_words):
        n = len(ws)
        wt = np.array([wlen(w, spoken) for w in ws], float)
        cw = np.concatenate([[0.0], np.cumsum(wt)]) / wt.sum()
        ds = dseg[a:b]
        cf = np.concatenate([[0.0], np.cumsum(ds)]) / ds.sum()
        m = [(0, a)]
        prev = 0
        for k in range(1, b - a):
            hi = n - (b - a - k)
            cands = range(prev + 1, hi + 1)
            if not cands:
                break
            best = min(cands, key=lambda i: abs(cw[i] - cf[k]) - (0.10 if ws[i - 1][-1:] in PUNCT or ws[i - 1].endswith('...') else 0.0))
            m.append((best, a + k))
            prev = best
        if len(m) < b - a:  # más tramos que palabras: une los sobrantes al último
            m = m[:len(m)]
        MAPx.append(m)
    return MAPx, cuts


def setup(mod, src, tag=None, SPOKEN=None, TEMPO=1.0, PAD=0.04, GAP_IN=0.20, GAP_OUT=0.34, DB=-38, DMIN=0.18, MAX_LEN=70.0):
    global V, anim, SEG, MAP, NSEG, SEGN, PIECES, OLD, NEW, NEWDUR, NF, VOICE_LEN
    tag = tag or mod
    spoken = SPOKEN or {}
    CFG.update(mod=mod, src=src, tag=tag, TEMPO=TEMPO, PAD=PAD)
    V = importlib.import_module(mod)
    anim = V.anim
    words_per_phrase = [ph['words'] for ph in anim.PH]
    cache = f"{BASE}/{tag}_seg.json"
    import json
    if os.path.exists(cache) and json.load(open(cache)).get('src') == src:
        SEG = [tuple(x) for x in json.load(open(cache))['seg']]
    else:
        SEG = silences(src, DB, DMIN)
        json.dump({'src': src, 'seg': SEG}, open(cache, 'w'))
    MAP, _ = auto_map(SEG, words_per_phrase, spoken)
    first_of_phrase = {m[0][1] for m in MAP}
    used = sorted({s for m in MAP for (_, s) in m})
    # tramos que quedaron sin palabra propia se pegan al tramo anterior (mismo bloque de audio)
    NSEG, cur = {}, 0.0
    prev_s = None
    for i, (a, b) in enumerate(SEG):
        a0, b0 = max(0.0, a - PAD), b + PAD
        if prev_s is not None:
            gap = GAP_OUT if i in first_of_phrase else GAP_IN
            orig_gap = (a - PAD) - (SEG[prev_s][1] + PAD)
            cur += max(0.0, min(gap, orig_gap))
        NSEG[i] = (cur + PAD, cur + (b0 - a0) - PAD, a0, b0, cur)
        cur += b0 - a0
        prev_s = i
    VOICE_LEN = cur / TEMPO
    if VOICE_LEN > MAX_LEN and TEMPO == 1.0:
        print(f"aviso: la voz editada dura {VOICE_LEN:.1f}s (> {MAX_LEN}); usa TEMPO≈{VOICE_LEN / (MAX_LEN - 1.5):.3f}")
    SEGN = {i: (s / TEMPO, e / TEMPO) for i, (s, e, _, _, _) in NSEG.items()}
    # PIECES por frase: (palabra inicial, inicio, fin) — el fin de cada pieza llega hasta el último tramo antes de la siguiente pieza
    PIECES = []
    for j, m in enumerate(MAP):
        nxt_first = MAP[j + 1][0][1] if j + 1 < len(MAP) else len(SEG)
        pcs = []
        for k, (w0, s) in enumerate(m):
            s_end = (m[k + 1][1] - 1) if k + 1 < len(m) else nxt_first - 1
            pcs.append((w0, SEGN[s][0], SEGN[s_end][1]))
        PIECES.append(pcs)
    OLD, NEW = [0.0], [0.0]
    for i, (ph, pcs) in enumerate(zip(anim.PH, PIECES)):
        OLD.append(V.PHR[i][0]); NEW.append(pcs[0][1])
        for (w0, ta, tb) in pcs[1:]:
            OLD.append(ph['starts'][w0]); NEW.append(ta)
        OLD.append(V.PHR[i][1]); NEW.append(pcs[-1][2])
    tail = max(1.1, min(2.6, V.DUR - V.PHR[-1][1]))
    NEWDUR = round(PIECES[-1][-1][2] + tail, 2)
    OLD.append(V.DUR); NEW.append(NEWDUR)
    # limpieza de anclas no crecientes (frases muy cortas)
    o2, n2 = [OLD[0]], [NEW[0]]
    for o, n_ in zip(OLD[1:], NEW[1:]):
        if o > o2[-1] + 1e-3 and n_ > n2[-1] + 1e-3:
            o2.append(o); n2.append(n_)
    OLD, NEW = o2, n2
    NF = int(NEWDUR * 24)
    # subtítulos con los tiempos nuevos
    newp = [(pcs[0][1], pcs[-1][2] + 0.15, txt, keys) for (a0, b0, txt, keys), pcs in zip(V.PHR, PIECES)]
    anim.PHR = newp
    anim.PH = anim.build_phrases()
    for i in range(len(anim.PH) - 1):
        anim.PH[i]['b'] = min(anim.PH[i]['b'], anim.PH[i + 1]['a'] - 0.31)
    for ph, pcs in zip(anim.PH, PIECES):
        ws = ph['words']
        n = len(ws)
        starts = [0.0] * n
        for k, (w0, ta, tb) in enumerate(pcs):
            w1 = pcs[k + 1][0] if k + 1 < len(pcs) else n
            wts = [wlen(w, spoken) for w in ws[w0:w1]]
            tot = sum(wts)
            acc = ta
            for i, wt in zip(range(w0, w1), wts):
                starts[i] = acc
                acc += (tb - ta) * wt / tot
        ph['starts'] = starts
    _orig = anim.draw_caption
    anim.draw_caption = lambda l2, t: _orig(l2, CUR[0])


def bw(t):
    return float(np.interp(t, NEW, OLD))


def fw(t):
    return float(np.interp(t, OLD, NEW))


def render_new(tn):
    CUR[0] = tn
    return V.render(bw(tn))


def build_voice(out=None):
    tag, src, TEMPO, PAD = CFG['tag'], CFG['src'], CFG['TEMPO'], CFG['PAD']
    out = out or f"{BASE}/narr_{tag}_editada.wav"
    tmp = f"{BASE}/narr_{tag}_tmp.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ac", "1", "-ar", "44100", tmp], check=True)
    sr, x = wavfile.read(tmp)
    x = x.astype(np.float32)
    total = max(v[4] + (v[3] - v[2]) for v in NSEG.values())
    buf = np.zeros(int((total + 0.2) * sr), np.float32)
    fd = int(0.006 * sr)
    for (s, e, a0, b0, pos) in NSEG.values():
        piece = x[int(a0 * sr):int(b0 * sr)].copy()
        if len(piece) > 2 * fd:
            piece[:fd] *= np.linspace(0, 1, fd)
            piece[-fd:] *= np.linspace(1, 0, fd)
        i0 = int(pos * sr)
        buf[i0:i0 + len(piece)] += piece[:len(buf) - i0]
    cut = f"{BASE}/narr_{tag}_cortada.wav"
    wavfile.write(cut, sr, np.clip(buf, -32768, 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", cut, "-af", f"atempo={TEMPO}", out], check=True)
    return out


def main(argv):
    mode = argv[1]
    W, H, FPS = V.W, V.H, 24
    if mode == "voz":
        print("voz editada:", build_voice(), "duración", round(VOICE_LEN, 2), "video", NEWDUR)
    elif mode == "map":
        for j, (m, ph) in enumerate(zip(MAP, anim.PH)):
            ws = ph['words']
            parts = []
            for k, (w0, s) in enumerate(m):
                w1 = m[k + 1][0] if k + 1 < len(m) else len(ws)
                parts.append(f"[{SEG[s][0]:.2f}] " + ' '.join(ws[w0:w1]))
            print(f"F{j + 1:02d}: " + ' | '.join(parts))
        print("tramos:", len(SEG), "voz editada:", round(VOICE_LEN, 2), "video:", NEWDUR)
    elif mode == "anchors":
        for o, n_ in zip(OLD, NEW):
            print(f"{o:7.2f} -> {n_:7.2f}")
        for ct in tuple(V.CUTS) + (V.T_OUT,):
            print("corte", ct, "->", round(fw(ct), 2))
    elif mode == "preview":
        d = f"{BASE}/{CFG['tag']}_prev2"
        os.makedirs(d, exist_ok=True)
        for ts in argv[2:]:
            Image.fromarray(render_new(float(ts))).save(f"{d}/t_{ts}.png")
        print("ok", d)
    elif mode == "chunk":
        a, b, out = int(argv[2]), int(argv[3]), argv[4]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fr in range(a, b):
            pr.stdin.write(render_new(fr / FPS).tobytes())
        pr.stdin.close()
        pr.wait()
        print("ok", a, b, "de", NF)
