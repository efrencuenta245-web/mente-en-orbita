"""Montaje genérico del estilo nuevo (reels de 61–75 s). Un video = un archivo TEMA.py que define:
    TEMA = 'bateria'
    TXT = ['Frase 1 de pantalla…', …]            # las mismas frases de la voz, con cifras
    VOZ = ['Frase 1 como se dice…', …]           # opcional: con números en letra (mejora los tiempos)
    ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[(1.2, 'tick', 0.6)]),
               dict(desde=2, fn=s_rayosx, tr='zoom'), …, dict(desde=12, loop=True, tr='zoom')]
    if __name__ == '__main__': montaje.cli(globals())
Cada escena dura desde 0.2 s antes de su frase `desde` hasta que empieza la siguiente.
fn(t, fi, u, d) devuelve el cuadro terminado (np.uint8 1080x1920x3): t = tiempo global, u = t − inicio de su frase,
d = duración de la escena. `loop=True` repite la escena 0 con t − DUR para que el último cuadro sea el primero.
Transiciones (tr): whip, whip_izq, zoom, flash, wipe, push, corte, ritmo, glitch, giro, iris, deslizar,
  deslizar_abajo, golpe (rápidas: 0.25–0.3 s) y las CREATIVAS (6-nov-2026): cubo, cubo_izq (cubo 3D que gira),
  rebanadas (franjas que salen disparadas), rompe (la pantalla se rompe como cristal; c=(x, y) es el impacto),
  mosaico (bloques digitales), remolino (espiral) y cristal (la palabra de cristal gigante deja ver la escena
  siguiente por sus letras y la cámara atraviesa una letra; pon palabra='CALOR' en esa escena).
REGLAS QUE SE REVISAN SOLAS (`hoja` las imprime como ERROR y `render` NO arranca hasta que se cumplan):
  · Transiciones: 8+ distintas (5+ si hay menos de 14 cambios), 3+ creativas distintas, ninguna dos veces seguidas,
    ninguna más de 3 veces, la primera distinta a la del reel anterior y ninguna racha de 3 seguidas igual a un
    reel de los últimos 6 de inicios.md (para que no salga la misma plantilla de siempre).
  · Letras de cristal GIGANTES (motor2.cristal, ≥ 80 % del ancho, detrás del objeto): en 3+ escenas (2+ si hay
    menos de 10) y una en los primeros 6 s. La transición `cristal` cuenta como una.
  · Guion: «Mándaselo a…» solo en la última o penúltima frase (a mitad del video la gente cree que ya terminó).
Los subtítulos (bloques de 6 palabras con caja cian) se ponen solos encima de todo.
Movimiento (ESTILO.md §11): objetos que entran en 0.12–0.3 s y cámara con golpes rápidos → piezas.entrada,
  piezas.cam_rapida, piezas.sacudida + piezas.mover_img, piezas.rebote/resorte/eout4, piezas.despiece.
Inicio (ESTILO.md §12): tipo distinto a los últimos 6 de /home/claude/mente-en-orbita/inicios.md; anótalo ahí.
Al terminar `hoja` sin errores: python3 TEMA.py registrar "AAAA-MM-DD HH:MM" "tema" "N nombre del inicio"
  → agrega la fila del reel arriba en inicios.md (con su secuencia de transiciones y sus palabras de cristal).

Comandos (desde /home/claude/mente-en-orbita/kit/nuevo):
  python3 TEMA.py tiempos /home/claude/narr_TEMA.mp3 [/home/claude/words_TEMA.json]
        → tiempos por frase (mejor con las palabras de Scribe) + voz con pausas (61 s o más)
  python3 TEMA.py preview 0.1 5 12                      → /home/claude/prev_TEMA_T.png
  python3 TEMA.py hoja                                   → reglas (ERROR si falta algo) + hoja de contacto /home/claude/hoja_TEMA.png
  python3 TEMA.py revisar                                → solo las reglas (transiciones y letras de cristal)
  python3 TEMA.py registrar "AAAA-MM-DD HH:MM" "tema" "N nombre del inicio"   → fila arriba en inicios.md
  python3 TEMA.py render                                 → /home/claude/TEMA_sin_audio.mp4 (no arranca si hay ERROR)
  python3 TEMA.py final "Línea 1" "línea 2" CATEGORÍA SEMILLA BPM
        → efectos, música, mezcla, portada y portada como cuadro 0: /home/claude/TEMA_final_p.mp4 + portada_TEMA.jpg
"""
import os, sys, json, math, subprocess, re
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import motor2 as M
from motor2 import (W, H, FPS, word_caption, seg, tr_zoom_through, tr_flash, tr_whip, tr_wipe_v, push_in,
                    tr_glitch, tr_giro, tr_iris, tr_deslizar, tr_golpe, tr_cubo, tr_rebanadas, tr_rompe, tr_mosaico,
                    tr_remolino, tr_cristal)

OUT = '/home/claude'
LEAD, TAIL, MIN_DUR, MAX_GAP = 0.25, 0.55, 61.3, 0.6


# ------------------------------------------------------------------ tiempos de las frases
def _silencios(wav):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', wav, '-af', 'silencedetect=noise=-38dB:d=0.1', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav],
                               capture_output=True, text=True).stdout)
    if len(en) < len(st):
        en.append(dur)
    return list(zip(st, en)), dur


def _alinear(sil, dur, txts):
    """Elige los n−1 silencios que separan las frases: los más largos que caen cerca de donde 'debería' ir cada corte."""
    s0 = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
    s1 = sil[-1][0] if sil and sil[-1][1] > dur - 0.05 else dur
    cand = [(a, b) for a, b in sil if a > s0 + 0.3 and b < s1 - 0.3]
    w = np.array([max(1, len(re.sub(r'[^\wáéíóúñü]', '', x.lower()))) for x in txts], float)
    cum = np.cumsum(w)[:-1] / w.sum()
    exp = s0 + (s1 - s0) * cum
    n, m = len(exp), len(cand)
    if m < n:
        raise SystemExit(f'Solo hay {m} pausas para {n} cortes: revisa la voz o junta frases.')
    INF = 1e9
    cost = np.full((n + 1, m + 1), INF)
    back = np.zeros((n + 1, m + 1), int)
    cost[0, :] = 0
    for k in range(1, n + 1):
        best, arg = INF, -1
        for j in range(1, m + 1):
            if cost[k - 1, j - 1] < best:
                best, arg = cost[k - 1, j - 1], j - 1
            a, b = cand[j - 1]
            c = abs((a + b) / 2 - exp[k - 1]) * 1.0 - (b - a) * 3.0
            if best < INF:
                cost[k, j] = best + c
                back[k, j] = arg
    j = int(np.argmin(cost[n]))
    pick = []
    for k in range(n, 0, -1):
        pick.append(cand[j - 1])
        j = back[k, j]
    pick = pick[::-1]
    T, a = [], s0
    for (sa, sb) in pick:
        T.append((a, sa))
        a = sb
    T.append((a, s1))
    return T


def _norm(w):
    import unicodedata
    w = unicodedata.normalize('NFD', w.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in w if unicodedata.category(c) != 'Mn'))


def _por_palabras(words_json, frases):
    """Tiempos por frase con las palabras de ElevenLabs Scribe (words_download_url), alineadas con difflib."""
    import difflib
    d = json.load(open(words_json))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(_norm(w.get('text', '')), float(w['start']), float(w['end'])) for w in d
          if w.get('type', 'word') == 'word' and _norm(w.get('text', ''))]
    sw = []
    for i, f in enumerate(frases):
        for w in re.sub(r'\[[^\]]*\]', ' ', f).split():
            if _norm(w):
                sw.append((i, _norm(w)))
    sm = difflib.SequenceMatcher(None, [w for _, w in sw], [w for w, _, _ in tw], autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    T = []
    for i in range(len(frases)):
        idx = [j for j, (fi, _) in enumerate(sw) if fi == i and j in mp]
        if not idx:
            T.append(None)
            continue
        T.append((tw[mp[idx[0]]][1], tw[mp[idx[-1]]][2]))
    for i in range(len(T)):  # frases sin coincidencias: interpola
        if T[i] is None:
            a = T[i - 1][1] if i > 0 and T[i - 1] else 0
            b = next((x[0] for x in T[i + 1:] if x), a + 2)
            T[i] = (a + 0.1, b - 0.1)
    return T


def tiempos(tema, mp3, words_json=None):
    wav = f'{OUT}/narr_{tema}_raw.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '48000', wav], check=True)
    txts = CTX['TXT']
    if words_json:
        T = _por_palabras(words_json, CTX.get('VOZ') or txts)
    else:
        sil, dur = _silencios(wav)
        T = _alinear(sil, dur, CTX.get('VOZ') or txts)
    from scipy.io import wavfile
    sr, x = wavfile.read(wav)
    x = x.astype(np.float32)
    n = len(T)
    voz = T[-1][1] - T[0][0]
    gap = min(MAX_GAP, max(0.0, (MIN_DUR - TAIL - LEAD - voz) / (n - 1)))
    cuts = [T[0][0]] + [(T[i][1] + T[i + 1][0]) / 2 for i in range(n - 1)] + [len(x) / sr]
    out = [np.zeros(int(LEAD * sr), np.float32)]
    for i in range(n):
        out.append(x[int(cuts[i] * sr):int(cuts[i + 1] * sr)])
        if i < n - 1:
            out.append(np.zeros(int(gap * sr), np.float32))
    y = np.concatenate(out)
    off = LEAD - T[0][0]
    T2 = [(round(a + off + gap * i, 3), round(b + off + gap * i, 3)) for i, (a, b) in enumerate(T)]
    DUR = round(max(T2[-1][1] + TAIL, MIN_DUR), 2)
    y = np.concatenate([y, np.zeros(max(0, int(DUR * sr) - len(y)), np.float32)])[:int(DUR * sr)]
    wavfile.write(f'{OUT}/narr_{tema}_pad.wav', sr, y.astype(np.int16))
    json.dump({'T': T2, 'DUR': DUR}, open(f'{OUT}/tiempos_{tema}.json', 'w'))
    print(f'DUR {DUR} s · pausa extra {gap:.2f} s')
    for i, ((a, b), t) in enumerate(zip(T2, txts)):
        print(f'{i:2d} {a:6.2f}–{b:6.2f}  {t}')


def cargar(tema):
    f = f'{OUT}/tiempos_{tema}.json'
    if not os.path.exists(f):
        return None, None
    d = json.load(open(f))
    return [tuple(x) for x in d['T']], d['DUR']


# ------------------------------------------------------------------ subtítulos
def _cap(img, t, T, txts, y=1560, size=56):
    fx = Image.new('RGB', (W, H), (0, 0, 0))
    for i, (a, b) in enumerate(T):
        nxt = T[i + 1][0] if i + 1 < len(T) else 1e9
        if not (a - 0.05 <= t < nxt - 0.12):
            continue
        w = txts[i].split()
        per = (b - a) * 0.92 / len(w)
        n = len(w)
        k = max(1, math.ceil(n / 6))
        sz = [n // k + (1 if j < n % k else 0) for j in range(k)]
        st = 0
        for j, m in enumerate(sz):
            t0 = a + st * per
            t1 = a + (st + m) * per if j < k - 1 else 1e9
            if t0 <= t < t1:
                word_caption(img, fx, w[st:st + m], t0, t, y=y, size=size, per=per)
                break
            st += m
    small = fx.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    a = np.asarray(img, np.float32) + np.asarray(small, np.float32) * 0.6
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


# ------------------------------------------------------------------ composición
CTX = {}


def _flash(img, t, t0, d=0.14, amt=110):
    if t0 <= t < t0 + d:
        img = (img.astype(np.float32) + amt * (1 - seg(t, t0, t0 + d))).clip(0, 255).astype(np.uint8)
    return img


def _escenas():
    T, DUR = CTX['T'], CTX['DUR']
    E = CTX['ESCENAS']
    out = []
    for k, e in enumerate(E):
        a = 0.0 if k == 0 else T[e['desde']][0] - 0.2
        b = DUR if k == len(E) - 1 else T[E[k + 1]['desde']][0] - 0.2
        out.append(dict(e, a=a, b=b))
    return out


def _eval(e, t, fi):
    T, DUR = CTX['T'], CTX['DUR']
    if e.get('loop'):
        e0 = CTX['_SC'][0]
        tt = t - DUR
        return e0['fn'](tt, fi, tt - T[e0['desde']][0], e0['b'] - e0['a'])
    return e['fn'](t, fi, t - T[e['desde']][0], e['b'] - e['a'])


def frame_at(t, fi, caps=True):
    SC = CTX['_SC']
    k = max(i for i, e in enumerate(SC) if e['a'] <= t or i == 0)
    e = SC[k]
    nxt = SC[k + 1] if k + 1 < len(SC) else None
    img = None
    # transición de salida hacia la siguiente (cada una decide su ventana; máx. 0.4 s antes del corte)
    if nxt is not None and t >= nxt['a'] - 0.4:
        img = _transicion(e, nxt, t, fi)
    # transición de entrada (hasta 0.3 s después del corte)
    if img is None and k > 0 and t < e['a'] + 0.3:
        img = _transicion(SC[k - 1], e, t, fi)
    if img is None:
        img = _eval(e, t, fi)
        if k > 0 and e.get('tr') in ('push', 'corte'):
            img = _flash(img, t, e['a'], 0.2 if e['tr'] == 'push' else 0.12, 150 if e['tr'] == 'push' else 110)
    if caps:
        img = np.asarray(_cap(Image.fromarray(img), t, CTX['T'], CTX['TXT'], **CTX.get('CAP', {})))
    return img


def _palabra(e):
    """Palabra de la transición `cristal`: la que diga la escena (palabra='…') o la más larga de su frase."""
    if e.get('palabra'):
        return e['palabra'].upper()
    ws = re.findall(r'[0-9A-Za-zÁÉÍÓÚÑÜáéíóúñü%]+', CTX['TXT'][e['desde']])
    return max(ws, key=len).upper() if ws else 'MENTE'


def _transicion(A, B, t, fi):
    tr = B.get('tr', 'corte')
    c = B['a']
    cx, cy = A.get('c', (0.5, 0.5))
    if tr in ('whip', 'whip_izq'):
        if c - 0.2 <= t < c + 0.15:
            return tr_whip(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.2, c + 0.15), -1 if tr == 'whip_izq' else 1)
    elif tr == 'zoom':
        if c - 0.2 <= t < c + 0.15:
            return tr_zoom_through(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.2, c + 0.15), cx, cy)
    elif tr == 'flash':
        if c - 0.2 <= t < c + 0.2:
            return tr_flash(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.2, c + 0.2))
    elif tr == 'wipe':
        if c - 0.2 <= t < c + 0.15:
            return tr_wipe_v(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.2, c + 0.15))
    elif tr == 'push':
        if c - 0.35 <= t < c:
            return push_in(_eval(A, t, fi), seg(t, c - 0.35, c), cx, cy, zmax=3.2)
    elif tr == 'glitch':
        if c - 0.13 <= t < c + 0.12:
            return tr_glitch(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.13, c + 0.12), fi)
    elif tr == 'giro':
        if c - 0.16 <= t < c + 0.14:
            return tr_giro(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.16, c + 0.14), cx, cy)
    elif tr == 'iris':
        if c - 0.1 <= t < c + 0.2:
            return tr_iris(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.1, c + 0.2), *B.get('c', (0.5, 0.5)))
    elif tr in ('deslizar', 'deslizar_abajo'):
        if c - 0.13 <= t < c + 0.12:
            return tr_deslizar(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.13, c + 0.12), tr == 'deslizar')
    elif tr == 'golpe':
        if c - 0.14 <= t < c + 0.11:
            return tr_golpe(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.14, c + 0.11), cx, cy)
    elif tr in ('cubo', 'cubo_izq'):
        if c - 0.2 <= t < c + 0.15:
            return tr_cubo(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.2, c + 0.15), -1 if tr == 'cubo_izq' else 1)
    elif tr == 'rebanadas':
        if c - 0.18 <= t < c + 0.14:
            return tr_rebanadas(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.18, c + 0.14))
    elif tr == 'rompe':
        if c - 0.12 <= t < c + 0.26:
            return tr_rompe(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.12, c + 0.26), *B.get('c', (0.5, 0.45)))
    elif tr == 'mosaico':
        if c - 0.15 <= t < c + 0.13:
            return tr_mosaico(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.15, c + 0.13), fi)
    elif tr == 'remolino':
        if c - 0.17 <= t < c + 0.15:
            return tr_remolino(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.17, c + 0.15), cx, cy)
    elif tr == 'cristal':
        if c - 0.3 <= t < c + 0.2:
            return tr_cristal(_eval(A, t, fi), _eval(B, t, fi), seg(t, c - 0.3, c + 0.2), _palabra(B))
    elif tr == 'ritmo':
        if c - 0.36 <= t < c:
            SC = CTX['_SC']
            prev = [s for s in SC[1:-1] if s is not A][-3:] or [A]
            j = min(2, int((t - (c - 0.36)) / 0.12))
            s = prev[j % len(prev)]
            tt = (s['a'] + s['b']) / 2
            return _flash(_eval(s, tt, fi), t, c - 0.36 + 0.12 * j, 0.12, 90)
    return None


# ------------------------------------------------------------------ sonido
def sonido(out):
    sys.path.insert(0, HERE)
    import sfx_demo as S
    SR = S.SR
    DUR = CTX['DUR']
    L = np.zeros(int(DUR * SR) + SR)

    def add(x, t0, g=1.0):
        i = max(0, int(t0 * SR))
        x = np.asarray(x) * g
        L[i:i + len(x)] += x[:max(0, len(L) - i)]
    NAMED = {'tick': lambda: S.tick(1800, 0.05, 0.6), 'tick2': lambda: S.tick(2400, 0.04, 0.5),
             'chime_a': lambda: S.chime(660), 'chime_b': lambda: S.chime(988), 'chime_c': lambda: S.chime(1318),
             'scribble': lambda: S.scribble(0.45), 'click': S.click, 'slap': S.slap, 'shimmer': lambda: S.shimmer(0.7),
             'sub': lambda: S.sub_hit(0.9), 'bass': S.bass_hit, 'burst': lambda: S.burst(0.35), 'thud': S.thud,
             'whoosh': lambda: S.whoosh(0.45, 400, 3500), 'whoosh_suave': lambda: S.whoosh(1.2, 300, 1500),
             'riser': lambda: S.riser(1.0), 'cristal': S.brillo_cristal, 'vidrio': S.vidrio, 'digital': S.digital}
    add(S.sub_hit(), 0.0)
    add(S.whoosh(0.5, 300, 1600), 0.15, 0.35)
    T = CTX['T']
    for k, e in enumerate(CTX['_SC']):
        c = e['a']
        tr = e.get('tr')
        if k > 0:
            if tr in ('whip', 'whip_izq'):
                add(S.whoosh(0.35, 500, 4200), c - 0.22, 0.9)
            elif tr == 'zoom':
                add(S.riser(0.8), c - 0.95, 0.5); add(S.whoosh(0.42, 300, 5000), c - 0.2, 0.9); add(S.thud(), c + 0.15, 0.6)
            elif tr == 'flash':
                add(S.riser(0.5), c - 0.55, 0.6); add(S.burst(), c - 0.05, 1.0)
            elif tr == 'wipe':
                add(S.whoosh(0.35, 800, 3000), c - 0.2, 0.8)
            elif tr == 'push':
                add(S.whoosh(0.4, 400, 4500), c - 0.35, 0.9); add(S.burst(), c, 0.9)
            elif tr == 'glitch':
                add(S.burst(0.25), c - 0.13, 0.7); add(S.tick(3200, 0.03, 0.5), c - 0.05); add(S.tick(900, 0.03, 0.5), c + 0.03)
            elif tr == 'giro':
                add(S.whoosh(0.32, 300, 2600), c - 0.18, 1.0); add(S.thud(), c + 0.12, 0.5)
            elif tr == 'iris':
                add(S.shimmer(0.4), c - 0.1, 0.6); add(S.chime(1318, 0.4), c, 0.35)
            elif tr in ('deslizar', 'deslizar_abajo'):
                add(S.whoosh(0.28, 700, 3400), c - 0.15, 0.9)
            elif tr == 'golpe':
                add(S.whoosh(0.2, 300, 5000), c - 0.15, 0.8); add(S.bass_hit(), c, 0.9)
            elif tr in ('cubo', 'cubo_izq'):
                add(S.whoosh(0.4, 250, 2200), c - 0.22, 1.0); add(S.thud(), c + 0.13, 0.7)
            elif tr == 'rebanadas':
                for j in range(4):
                    add(S.whoosh(0.16, 900, 5200), c - 0.18 + 0.05 * j, 0.55)
                add(S.bass_hit(), c + 0.1, 0.6)
            elif tr == 'rompe':
                add(S.vidrio(), c - 0.12, 1.0); add(S.sub_hit(0.8), c - 0.12, 0.6)
            elif tr == 'mosaico':
                add(S.digital(0.3), c - 0.15, 0.9); add(S.burst(0.2), c - 0.02, 0.4)
            elif tr == 'remolino':
                add(S.whoosh(0.4, 200, 1800), c - 0.2, 1.0); add(S.riser(0.3), c - 0.3, 0.4); add(S.thud(), c + 0.14, 0.5)
            elif tr == 'cristal':
                add(S.brillo_cristal(), c - 0.3, 0.9); add(S.whoosh(0.3, 400, 6000), c - 0.08, 0.9); add(S.thud(), c + 0.18, 0.6)
            elif tr == 'ritmo':
                for j in range(3):
                    add(S.bass_hit(), c - 0.36 + 0.12 * j)
            else:
                add(S.bass_hit(), c, 0.8)
        base = T[e['desde']][0]
        for (u, name, g) in e.get('sfx', []):
            add(NAMED[name](), base + u, g)
    # brillo cristalino cuando entra cada palabra de cristal gigante (lo guarda la revisión de `render`)
    fc = f'{OUT}/cristal_{CTX["TEMA"]}.json'
    if os.path.exists(fc):
        for tc in json.load(open(fc)).get('t', []):
            add(S.brillo_cristal(), max(0.0, tc), 0.7)
    add(S.riser(0.9), DUR - 0.95, 0.45)
    L = L[:int(DUR * SR)]
    L = L / (np.max(np.abs(L)) + 1e-9) * 0.89
    from scipy.io import wavfile
    wavfile.write(out, SR, (L * 32767).astype(np.int16))


# ------------------------------------------------------------------ render, hoja, final
def _work(fi):
    return fi, frame_at(fi / FPS, fi).tobytes()


def render(out):
    from multiprocessing import Pool
    NF = int(round(CTX['DUR'] * FPS))
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-maxrate', '10M', '-bufsize', '20M',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    with Pool(2) as pool:
        for fi, buf in pool.imap(_work, range(NF), chunksize=2):
            p.stdin.write(buf)
            if fi % 240 == 0:
                print('cuadro', fi, '/', NF, flush=True)
    p.stdin.close()
    p.wait()


def hoja(out):
    SC = CTX['_SC']
    ts = [round((e['a'] + e['b']) / 2, 2) for e in SC] + [round(e['a'] + 0.05, 2) for e in SC[1:]]
    ts = sorted(ts)[:48]
    ims = [Image.fromarray(frame_at(t, int(t * FPS))).resize((216, 384)) for t in ts]
    cols = 8
    rows = math.ceil(len(ims) / cols)
    sh = Image.new('RGB', (216 * cols, 384 * rows))
    for i, im in enumerate(ims):
        sh.paste(im, ((i % cols) * 216, (i // cols) * 384))
    sh.save(out)
    print('hoja', out, ts)


def final(l1, l2, cat, semilla, bpm):
    tema = CTX['TEMA']
    DUR = CTX['DUR']
    v = f'{OUT}/{tema}_sin_audio.mp4'
    fx = f'{OUT}/efectos_{tema}.wav'
    mu = f'{OUT}/musica_{tema}.wav'
    sonido(fx)
    subprocess.run(['python3', os.path.join(KIT, 'musica.py'), str(DUR), mu, str(semilla), str(bpm), str(CTX['T'][-1][1])], check=True)
    mix = f'{OUT}/{tema}_final.mp4'
    subprocess.run(['bash', os.path.join(KIT, 'mix_musica.sh'), v, f'{OUT}/narr_{tema}_pad.wav', fx, mu, mix], check=True, cwd=KIT)
    prev = f'{OUT}/prev_{tema}_portada.png'
    Image.fromarray(frame_at(0.1, 2, caps=False)).save(prev)
    import portada
    portada.make(prev, f'{OUT}/portada_{tema}.jpg', l1, l2, cat)
    portada.primer_cuadro(mix, f'{OUT}/portada_{tema}.jpg', f'{OUT}/{tema}_final_p.mp4')
    pr = lambda f, k: subprocess.run(['ffprobe', '-v', 'error', '-select_streams', k, '-show_entries', 'stream=duration', '-of', 'csv=p=0', f],
                                     capture_output=True, text=True).stdout.strip()
    fin = f'{OUT}/{tema}_final_p.mp4'
    r = subprocess.run(['ffmpeg', '-sseof', '-3', '-i', fin, '-af', 'volumedetect', '-vn', '-f', 'null', '-'], capture_output=True, text=True).stderr
    mv = re.findall(r'mean_volume: ([-\d.]+)', r)
    print('FINAL', fin, 'video', pr(fin, 'v:0'), 'audio', pr(fin, 'a:0'), 'últimos 3 s', mv, 'dB',
          'peso', round(os.path.getsize(fin) / 1e6, 1), 'MB')


CREATIVAS = {'cubo': 'cubo', 'cubo_izq': 'cubo', 'rebanadas': 'rebanadas', 'rompe': 'rompe', 'mosaico': 'mosaico',
             'remolino': 'remolino', 'cristal': 'cristal'}
INICIOS = os.path.join(os.path.dirname(KIT), 'inicios.md')


def _inicios():
    """Filas de inicios.md (de la más nueva a la más vieja): dict con primera, archivo y secuencia."""
    out = []
    if not os.path.exists(INICIOS):
        return out
    for ln in open(INICIOS, encoding='utf-8'):
        c = [x.strip() for x in ln.strip().strip('|').split('|')]
        if not ln.startswith('|') or len(c) < 4 or c[0].startswith('Fecha') or set(c[0]) <= set('-: '):
            continue
        out.append(dict(fecha=c[0], tema=c[1], primera=c[3].split()[0] if c[3] else '',
                        archivo=c[4] if len(c) > 4 else '', seq=c[5].split() if len(c) > 5 else []))
    return out


def _trs():
    return [e.get('tr', 'corte') for e in CTX['ESCENAS'][1:]]


def _revisar_transiciones():
    trs = _trs()
    n = len(trs)
    dist = set(trs) - {'corte'}
    crea = {CREATIVAS[x] for x in trs if x in CREATIVAS}
    err = []
    need = 8 if n >= 14 else 5
    if len(dist) < need:
        err.append(f'solo {len(dist)} transiciones distintas; usa {need} o más (ESTILO.md §11)')
    if len(crea) < 3:
        err.append(f'solo {len(crea)} transiciones creativas ({", ".join(sorted(crea)) or "ninguna"}); usa 3 o más de: '
                   'cubo, rebanadas, rompe, mosaico, remolino, cristal')
    rep = [trs[i] for i in range(1, n) if trs[i] == trs[i - 1] and trs[i] != 'corte']
    if rep:
        err.append(f'repetidas seguidas: {", ".join(rep)}')
    mas = sorted({x for x in trs if x != 'corte' and trs.count(x) > 3})
    if mas:
        err.append('usadas más de 3 veces: ' + ', '.join(f'{x} ({trs.count(x)})' for x in mas))
    prev = [r for r in _inicios() if r['archivo'] != CTX['TEMA']]
    if prev and trs and prev[0]['primera'] and trs[0] == prev[0]['primera']:
        err.append(f'la primera transición ({trs[0]}) es la misma del reel anterior ({prev[0]["tema"]}); cámbiala')
    mios = {tuple(trs[i:i + 3]) for i in range(n - 2)}
    for r in prev[:6]:
        sq = r['seq']
        comun = mios & {tuple(sq[i:i + 3]) for i in range(len(sq) - 2)}
        if comun:
            err.append(f'racha igual a «{r["tema"]}»: {" → ".join(sorted(comun)[0])}; cambia el orden (nada de plantilla)')
    print('Transiciones:', ' → '.join(trs))
    return err


def _revisar_cristal(guardar=True):
    """Busca palabras de cristal gigantes (≥ 80 % del ancho) en cada escena y cuenta las transiciones `cristal`."""
    SC, T = CTX['_SC'], CTX['T']
    hits = []
    for k, e in enumerate(SC):
        if e.get('loop'):
            continue
        for fr_ in (0.3, 0.6, 0.9):
            t = e['a'] + (e['b'] - e['a']) * fr_
            M.REG_CRISTAL.clear()
            _eval(e, t, int(t * FPS))
            big = [x for x in M.REG_CRISTAL if x[1] >= 0.8]
            if big:
                hits.append((k, big[0][0], round(T[e['desde']][0] + big[0][2], 2)))
                break
    for k, e in enumerate(SC[1:], 1):
        if e.get('tr') == 'cristal' and not any(h[0] == k for h in hits):
            hits.append((k, _palabra(e), round(e['a'] - 0.3, 2)))
    hits.sort()
    n_esc = len([e for e in SC if not e.get('loop')])
    need = 3 if n_esc >= 10 else 2
    err = []
    if len(hits) < need:
        err.append(f'letras de cristal gigantes en {len(hits)} escenas; van en {need} o más (motor2.cristal, '
                   'detrás del objeto: llámala con fr.base/fr.fx antes de draw_objects; ESTILO.md §4b)')
    if not any(h[2] < 6.0 for h in hits):
        err.append('ninguna palabra de cristal gigante en los primeros 6 s (el gancho la necesita)')
    print('Cristal:', ', '.join(f'escena {k} «{w}» {t:.1f} s' for k, w, t in hits) or 'ninguna')
    if guardar:
        json.dump({'t': [h[2] for h in hits if not any(e.get('tr') == 'cristal' and i == h[0]
                                                         for i, e in enumerate(SC))],
                   'palabras': [h[1] for h in hits]}, open(f'{OUT}/cristal_{CTX["TEMA"]}.json', 'w'))
    return err, hits


def _revisar_mandaselo():
    """Guion (no animación): el «mándaselo a…» va solo en la última o penúltima frase (Efrén, 6-nov-2026)."""
    malas = set()
    for lista in (CTX.get('TXT') or [], CTX.get('VOZ') or []):
        n = len(lista)
        malas |= {i for i, f in enumerate(lista) if i < n - 2 and re.search(r'm[aá]nd[aá]selo|comp[aá]rtelo', f, re.I)}
    return [f'«mándaselo a…» en la frase {i + 1} de {len(CTX["TXT"])}: va SOLO en la última o penúltima frase '
            '(a mitad del video la gente cree que ya terminó y se va)' for i in sorted(malas)]


def _revisar(estricto):
    err = _revisar_mandaselo() + _revisar_transiciones()
    e2, hits = _revisar_cristal()
    err += e2
    for x in err:
        print('ERROR', x)
    if err and estricto:
        raise SystemExit(f'No se renderiza: {len(err)} regla(s) sin cumplir (ve los ERROR de arriba, corrige TEMA.py y '
                         'vuelve a correr hoja).')
    if not err:
        print('Reglas OK: transiciones variadas y letras de cristal gigantes.')
    return hits


def registrar(fecha, tema_txt, tipo):
    """Agrega arriba en inicios.md la fila de este reel (reemplaza la suya si ya estaba)."""
    trs = _trs()
    _, hits = _revisar_cristal(guardar=False)
    fila = (f'| {fecha} | {tema_txt} | {tipo} | {trs[0] if trs else "corte"} | {CTX["TEMA"]} | {" ".join(trs)} | '
            f'{" ".join(h[1] for h in hits)} |\n')
    lines = open(INICIOS, encoding='utf-8').readlines()
    lines = [ln for ln in lines if not (ln.startswith('|') and f'| {CTX["TEMA"]} |' in ln)]
    i = next(j for j, ln in enumerate(lines) if ln.startswith('|---'))
    lines.insert(i + 1, fila)
    open(INICIOS, 'w', encoding='utf-8').writelines(lines)
    print('inicios.md ←', fila.strip())


def cli(g):
    CTX.update({k: g[k] for k in ('TEMA', 'TXT', 'ESCENAS', 'VOZ') if k in g})
    CTX['CAP'] = g.get('CAP', {})
    cmd = sys.argv[1]
    if cmd == 'tiempos':
        tiempos(CTX['TEMA'], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        return
    T, DUR = cargar(CTX['TEMA'])
    if T is None:
        raise SystemExit('Primero: python3 TEMA.py tiempos /home/claude/narr_TEMA.mp3')
    CTX['T'], CTX['DUR'] = T, DUR
    CTX['_SC'] = _escenas()
    tema = CTX['TEMA']
    if cmd == 'preview':
        for ts in sys.argv[2:]:
            t = float(ts)
            Image.fromarray(frame_at(t, int(t * FPS))).save(f'{OUT}/prev_{tema}_{ts}.png')
    elif cmd == 'hoja':
        _revisar(estricto=False)
        hoja(f'{OUT}/hoja_{tema}.png')
    elif cmd == 'revisar':
        _revisar(estricto=False)
    elif cmd == 'render':
        _revisar(estricto=True)
        render(f'{OUT}/{tema}_sin_audio.mp4')
    elif cmd == 'registrar':
        registrar(*sys.argv[2:5])
    elif cmd == 'sonido':
        sonido(f'{OUT}/efectos_{tema}.wav')
    elif cmd == 'final':
        final(*sys.argv[2:7])


def init(g):
    """Para usar las funciones desde otro módulo (pruebas): carga tiempos sin leer la línea de comandos."""
    CTX.update({k: g[k] for k in ('TEMA', 'TXT', 'ESCENAS') if k in g})
    T, DUR = cargar(CTX['TEMA'])
    CTX['T'], CTX['DUR'] = T, DUR
    CTX['_SC'] = _escenas()
