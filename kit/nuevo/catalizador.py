"""Reel diario jue 19-nov-2026 10:00 — «Tu escape no tira humo… lo cocina.» (el convertidor catalítico: panal de
cerámica con platino, paladio y rodio que convierte CO, gasolina sin quemar y NOx en CO2, agua y nitrógeno; solo
trabaja caliente, ~260 °C; en un arranque en frío hasta el 80 % sale en el primer minuto y medio; caliente quita casi
el 90 %; error: quitarlo o vaciarlo «para que corra más»: el sensor prende el foco y la verificación lo rechaza; una
bujía que falla lo puede derretir).
Comunidad: automovilistas de la CDMX y el Edomex (verificación). Inicio tipo 10 (rayos X de golpe): el escape real se
vuelve de cristal en el primer golpe y aparece el panal brillando, con «COCINA» de cristal detrás. El final («porque
su escape no tira humo… lo cocina») regresa a él (loop).
Voz Isaac (eleven_v4) del 17-nov, 66.9 s. Datos y fuentes: guiones/2026-11-19_catalizador.txt.
Fotos reales: «Catalyticconverter.jpg» (dominio público) y «Catalytic Converter Interior.jpg» (CC0), Wikimedia Commons.
El escape, el panal, las moléculas y el sensor son esquemas marcados «ESQUEMA».
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import auto, tubo, _B, texto, esquema, gota_m, golpe_k, sacudir, K, camara

M3 = M.M3
TEMA = 'catalizador'
TXT = ['Tu escape no tira humo… lo cocina.',
       'Ese bulto en el tubo es el catalizador,',
       'y por dentro es un panal de cerámica.',
       'Miles de canalitos, cubiertos de platino, paladio y rodio.',
       'Al pasar por ahí, el gas sucio se transforma.',
       'El monóxido de carbono, que envenena, sale como dióxido de carbono.',
       'La gasolina sin quemar, como agua.',
       'Y los óxidos de nitrógeno… como el nitrógeno del aire.',
       'Pero solo cocina caliente: arriba de unos 260 °C.',
       'La prueba: con el motor frío, casi todo pasa directo.',
       'Por eso, en un arranque en frío,',
       'hasta el 80 % de lo que contamina sale en el primer minuto y medio.',
       'Ya caliente, quita casi el 90 %.',
       'Pero aquí está el error: quitarlo o vaciarlo para que corra más.',
       'Tu computadora lo nota con un sensor y prende el foco del motor.',
       'Y en la verificación te rechazan:',
       'un catalizador quitado o vaciado es una pieza alterada.',
       'Y si una bujía falla, la gasolina cruda se quema adentro…',
       'y lo puede derretir.',
       'Mándaselo a quien no pasó la verificación,',
       'porque su escape no tira humo… lo cocina.']
VOZ = ['[curious] Tu escape no tira humo… lo cocina.',
       'Ese bulto en el tubo es el catalizador,',
       'y por dentro es un panal de cerámica.',
       'Miles de canalitos, cubiertos de platino, paladio y rodio.',
       'Al pasar por ahí, el gas sucio se transforma.',
       'El monóxido de carbono, que envenena, sale como dióxido de carbono.',
       'La gasolina sin quemar, como agua.',
       'Y los óxidos de nitrógeno… como el nitrógeno del aire.',
       'Pero solo cocina caliente: arriba de unos doscientos sesenta grados.',
       'La prueba: con el motor frío, casi todo pasa directo.',
       'Por eso, en un arranque en frío,',
       'hasta el ochenta por ciento de lo que contamina sale en el primer minuto y medio.',
       'Ya caliente, quita casi el noventa por ciento.',
       '[excited] Pero aquí está el error: quitarlo o vaciarlo para que corra más.',
       'Tu computadora lo nota con un sensor y prende el foco del motor.',
       'Y en la verificación te rechazan:',
       'un catalizador quitado o vaciado es una pieza alterada.',
       'Y si una bujía falla, la gasolina cruda se quema adentro…',
       'y lo puede derretir.',
       'Mándaselo a quien no pasó la verificación,',
       'porque su escape no tira humo… lo cocina.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_catalizador.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-19_catalizador_words.json')
IMG = os.path.join(HERE, 'img', 'catalizador')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
VERDE = (40, 205, 110)
GRIS = (150, 150, 160)
ACERO = (150, 147, 142)
CROMO = (210, 212, 218)
CERAM = (224, 210, 176)
SUCIO = (170, 150, 125)
LIMPIO = (150, 235, 255)
FRIO = (120, 170, 255)
C_C, C_O, C_N, C_H = (70, 72, 80), (235, 70, 58), (90, 140, 240), (238, 238, 244)
PT, PD, RH = (236, 240, 250), (196, 200, 210), (255, 226, 170)


# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    d = json.load(open(WORDS))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(montaje._norm(w.get('text', '')), float(w['start'])) for w in d
          if w.get('type', 'word') == 'word' and montaje._norm(w.get('text', ''))]
    sw = []
    for i, f in enumerate(VOZ):
        for w in re.sub(r'\[[^\]]*\]', ' ', f).split():
            if montaje._norm(w):
                sw.append((i, montaje._norm(w)))
    sm = difflib.SequenceMatcher(None, [w for _, w in sw], [w for w, _ in tw], autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    per = {}
    for j, (i, w) in enumerate(sw):
        per.setdefault(i, []).append(tw[mp[j]][1] if j in mp else None)
    for i, L in per.items():
        last = None
        for k in range(len(L)):
            if L[k] is None:
                L[k] = (last + 0.25) if last is not None else None
            last = L[k] if L[k] is not None else last
        base = next(x for x in L if x is not None)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wp(i, palabra, n=0):
    """u de la palabra de la frase i que empieza con `palabra` (la n-ésima si se repite)."""
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ fotos reales
_F = {}


def foto(n):
    if n not in _F:
        if n == 'ext':
            im = Image.open(os.path.join(IMG, 'cat_i_exterior.jpg')).convert('RGB')
        else:
            im = Image.open(os.path.join(IMG, 'cat_i_interior.jpg')).convert('RGB')
            w, h = im.size
            im = im.crop((int(w * 0.08), int(h * 0.2), int(w * 0.92), int(h * 0.75)))
        _F[n] = im
    return _F[n]


def hay_foto(n):
    return os.path.exists(os.path.join(IMG, 'cat_i_exterior.jpg' if n == 'ext' else 'cat_i_interior.jpg'))


# ------------------------------------------------------------------ objetos
Y = 0.5          # altura del escape
X_IN, X_OUT = -0.83, 0.02   # cara de entrada y de salida del panal
RZ = 1.25        # el cuerpo es ovalado (más ancho en z)


def cil_x(r, L, col, x0, y=Y, z=0.0, r2=None, n=28, gloss=0.6, name='esc', rim=0.7, sz=RZ, glow=None):
    """Cilindro acostado a lo largo de +x desde x0 (ovalado con sz)."""
    m = M3.cyl(r, L, col, n=n, shadow=0, gloss=gloss, r2=r2).tf(rz=-90).tf(s=(1, 1, sz)).tf(t=(x0, y, z))
    m = named(m, name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    return m


def aro_x(R, r, col, x, y=Y, sz=RZ):
    m = M3.torus(R, r, col, nu=30, nv=6, gloss=0.7).tf(rz=-90).tf(s=(1, 1, sz)).tf(t=(x, y, 0))
    return named(m, 'esc', rim=0.8, gloss=0.7)


def catalizador_m(calor=0.0, frio=0.0, vacio=False, panal=True):
    """El convertidor: cono de entrada, cuerpo ovalado con aros, cono de salida y (adentro, 'in') el panal."""
    col = M.mixc(M.mixc(ACERO, (255, 120, 60), 0.5 * calor), (120, 150, 200), 0.35 * frio)
    ms = [cil_x(0.085, 0.28, col, -1.15, r2=0.3),
          cil_x(0.3, 0.95, col, -0.87),
          cil_x(0.3, 0.28, col, 0.08, r2=0.085)]
    for x in (-0.62, -0.38, -0.14):
        ms.append(aro_x(0.305, 0.018, M.mixc(col, WHITE, 0.15), x))
    if panal and not vacio:
        g = M.scale_c(NARANJA, 0.85 * calor) if calor > 0.02 else None
        ms.append(cil_x(0.26, X_OUT - X_IN, M.mixc(CERAM, (255, 170, 90), 0.5 * calor), X_IN, name='in', gloss=0.2,
                        rim=0.5, glow=g))
    return ms


def escape(calor=0.0, frio=0.0, vacio=False, sale=0.0, recto=0.0, sensores=True):
    """Escape completo a lo largo de x: tubo del motor → catalizador → tubo → mofle → cola."""
    ms = [tubo((-2.7, Y, 0), (-1.12, Y, 0), r=0.085, col=ACERO, name='esc', gloss=0.7)]
    cat = catalizador_m(calor, frio, vacio)
    if sale > 0.001:                                 # lo quitan: sube girando y se va
        cat = P.tfk(cat, rz=-25 * sale, t=(0.3 * sale, 2.6 * P.eout4(sale), 0.6 * sale))
    ms += cat
    if recto > 0.01:                                 # el «tubo recto» que ponen en su lugar
        ms.append(tubo((-1.15, Y, 0), (-1.15 + 1.55 * recto, Y, 0), r=0.085, col=(200, 120, 110), name='recto', gloss=0.8))
    ms += [tubo((0.34, Y, 0), (1.25, Y, 0), r=0.085, col=ACERO, name='esc', gloss=0.7),
           cil_x(0.27, 0.95, ACERO, 1.25, sz=1.5, gloss=0.55),
           tubo((2.18, Y, 0), (2.85, Y - 0.04, 0), r=0.07, col=ACERO, name='esc', gloss=0.7),
           cil_x(0.085, 0.14, CROMO, 2.76, y=Y - 0.04, sz=1.0, gloss=0.95)]
    if sensores:
        for x in (-1.4, 0.6):
            ms.append(named(M3.cyl(0.035, 0.2, (200, 200, 206), n=10, shadow=0, gloss=0.9).tf(t=(x, Y + 0.06, 0)), 'sensor', rim=0.9))
            ms.append(named(M3.cyl(0.065, 0.05, (170, 160, 120), n=6, shadow=0, gloss=0.8).tf(t=(x, Y + 0.1, 0)), 'sensor', rim=0.8))
    return ms


def gas(fr, t, limpia=1.0, k=1.0, n=64, x0=-2.7, x1=2.85, salida=1.0, seed=3, vel=0.5, sucio=SUCIO):
    """Partículas del gas que corren por el escape; dentro del panal cambian de color según `limpia`."""
    rng = np.random.RandomState(seed)
    for j in range(n):
        ph = (t * vel + j / n + 0.13 * rng.rand()) % 1.0
        x = x0 + (x1 + 1.3 * salida - x0) * ph
        a0, a1 = rng.rand() * 6.28, rng.rand()
        if X_IN - 0.3 < x < X_OUT + 0.3:
            r = 0.2 * a1
        elif 1.25 < x < 2.2:
            r = 0.2 * a1
        elif x > x1:
            r = 0.06 + 0.5 * (x - x1) * a1
        else:
            r = 0.055 * a1
        y = Y + r * math.sin(a0 + t * 3)
        z = r * math.cos(a0 + t * 3) * (1.3 if x < 2.2 else 1.0)
        if x < X_IN:
            c = sucio
        elif x < X_OUT:
            c = M.mixc(sucio, LIMPIO, limpia * seg(x, X_IN, X_OUT))
        else:
            c = M.mixc(sucio, LIMPIO, limpia)
        a = k * (0.9 if x < x1 else 0.9 * (1 - seg(x, x1, x1 + 1.3 * salida)))
        dot3(fr, (x, y, z), r=4.2, col=c, a=a, glow=0.7 + 0.6 * limpia * (x > X_OUT))


def rejilla(fr, x, r=0.26, sz=RZ, paso=0.052, col=CERAM, a=0.9, w=1.6, glow=0.7, caida=0.0, t=0.0):
    """La cara del panal (plano y-z en x): cuadrícula de canalitos recortada al óvalo. caida = se derrite."""
    rz = r * sz
    for v in np.arange(-r + paso, r, paso):              # líneas horizontales (y = cte)
        h = rz * math.sqrt(max(0.0, 1 - (v / r) ** 2))
        pts = [(x, Y + v - caida * (0.5 + 0.5 * math.sin(z * 9 + t)) * (1 + v / r) * 0.06, z) for z in np.linspace(-h, h, 14)]
        line3(fr, pts, col=col, w=w, a=a, glow=glow)
    for zz in np.arange(-rz + paso * sz, rz, paso * sz):  # verticales (z = cte)
        h = r * math.sqrt(max(0.0, 1 - (zz / rz) ** 2))
        pts = [(x, Y + v - caida * (0.5 + 0.5 * math.sin(zz * 9 + t)) * (1 + v / r) * 0.06, zz) for v in np.linspace(-h, h, 14)]
        line3(fr, pts, col=col, w=w, a=a, glow=glow)
    q = np.linspace(0, 2 * math.pi, 48)
    line3(fr, [(x, Y + r * math.sin(a_), rz * math.cos(a_)) for a_ in q], col=col, w=w * 1.6, a=a, glow=glow)


def esfera(r, col, p, gloss=0.75):
    return named(M3.sphere(r, col, nu=20, nv=12, shadow=0, gloss=gloss).tf(t=p), 'atomo', rim=0.85, gloss=gloss)


def enlace(p0, p1, r=0.05):
    return tubo(p0, p1, r=r, col=(200, 200, 206), name='enlace', gloss=0.6)


def molecula(atomos, rot=0.0, centro=(0, 1.0, 0), s=1.0):
    """atomos = [(pos relativa, radio, color)]; enlaces entre consecutivos. rot = giro en y (rad)."""
    c, sn = math.cos(rot), math.sin(rot)
    pts = []
    for (px, py, pz), r, col in atomos:
        x, z = px * c + pz * sn, -px * sn + pz * c
        pts.append((np.array([centro[0] + s * x, centro[1] + s * py, centro[2] + s * z]), r * s, col))
    ms = []
    for (p0, _, _), (p1, _, _) in zip(pts, pts[1:]):
        ms.append(enlace(p0, p1, 0.045 * s))
    ms += [esfera(r, col, tuple(p)) for p, r, col in pts]
    return ms


def tunel(fr, t, k=1.0, z0=0.0, vel=1.2, n=12, h=0.36, cy=0.5, col=CERAM, chispas=1.0):
    """Un canalito por dentro: anillos cuadrados que pasan junto a la cámara + chispas de metal en las paredes."""
    for j in range(n):
        ph = ((t * vel * 0.25 + j / n) % 1.0)
        z = z0 - 0.3 - 7.0 * (1 - ph)
        a = k * (0.25 + 0.75 * ph) * (1 - seg(ph, 0.93, 1.0))
        sq = [(-h, cy - h, z), (h, cy - h, z), (h, cy + h, z), (-h, cy + h, z), (-h, cy - h, z)]
        line3(fr, sq, col=col, w=2.4, a=a, glow=0.6)
    for x, y in ((-h, cy - h), (h, cy - h), (h, cy + h), (-h, cy + h)):
        line3(fr, [(x, y, z0 - 0.3), (x, y, z0 - 7.3)], col=col, w=2.0, a=0.6 * k, glow=0.5)
    rng = np.random.RandomState(11)
    for j in range(30):
        ph = ((t * vel * 0.25 + rng.rand()) % 1.0)
        z = z0 - 0.3 - 7.0 * (1 - ph)
        lado = j % 4
        s_ = rng.rand() * 2 - 1
        x, y = [(-h, cy + s_ * h), (h, cy + s_ * h), (s_ * h, cy - h), (s_ * h, cy + h)][lado]
        col_ = (PT, PD, RH)[j % 3]
        dot3(fr, (x, y, z), r=3.0 + 2 * math.sin(t * 7 + j) ** 2, col=col_, a=chispas * k * ph, glow=1.4)


def nube(fr, p, r, col, a):
    """Bolita de humo semitransparente (solo en la capa que brilla: no tapa con negro)."""
    if a <= 0.01:
        return
    s, z = fr.cam.proj([p])
    if z[0] < 0.2:
        return
    x, y = s[0]
    rr = r * M.SS
    fr.df.ellipse((x - rr, y - rr, x + rr, y + rr), fill=M.scale_c(col, 0.3 * a))
    fr.df.ellipse((x - rr * 0.6, y - rr * 0.6, x + rr * 0.6, y + rr * 0.6), fill=M.scale_c(col, 0.45 * a))


def humo(fr, t, k=1.0, x=2.9, y=Y - 0.04, col=(130, 128, 125), n=18, seed=2, dx=1.0):
    rng = np.random.RandomState(seed)
    for j in range(n):
        ph = (t * 0.6 + j / n) % 1.0
        p = (x + dx * (1.2 * ph + 0.1 * rng.rand()), y + 0.5 * ph * rng.rand() + 0.1 * ph, (rng.rand() - 0.5) * 0.8 * ph)
        nube(fr, p, 6 + 18 * ph, col, k * (1 - ph))


def sticker(img, fx, x, y, r, k, t, tache=0.0):
    """Holograma genérico (círculo tornasol) con «VERIFICACIÓN»; tache = X roja encima."""
    if k <= 0.01:
        return
    lay = Image.new('RGB', (2 * r, 2 * r), (0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(r, 0, -3):
        hue = (i / r + t * 0.2) % 1.0
        c = tuple(int(150 + 90 * math.sin(2 * math.pi * (hue + o))) for o in (0, 0.33, 0.66))
        d.ellipse((r - i, r - i, r + i, r + i), fill=c)
    d.ellipse((6, 6, 2 * r - 6, 2 * r - 6), outline=(255, 255, 255), width=5)
    d.text((r, r - 10), 'VERIFICACIÓN', font=M.font('mono', int(r * 0.2)), fill=(20, 20, 26), anchor='mm')
    d.text((r, r + int(r * 0.32)), 'VEHICULAR', font=M.font('mono', int(r * 0.15)), fill=(20, 20, 26), anchor='mm')
    m = Image.new('L', (2 * r, 2 * r), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 2 * r, 2 * r), fill=int(255 * clamp(k)))
    s = 0.6 + 0.4 * P.resorte(k)
    sz = max(2, int(2 * r * s))
    img.paste(lay.resize((sz, sz)), (int(x - sz / 2), int(y - sz / 2)), m.resize((sz, sz)))
    if tache > 0.01:
        dl, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        e = r * 0.9 * clamp(tache * 2)
        dl.line([(x - e, y - e), (x + e, y + e)], fill=RED, width=22)
        df.line([(x - e, y - e), (x + e, y + e)], fill=M.scale_c(RED, 0.6), width=30)
        e2 = r * 0.9 * clamp(tache * 2 - 1)
        if e2 > 1:
            dl.line([(x + r * 0.9, y - r * 0.9), (x + r * 0.9 - 2 * e2, y - r * 0.9 + 2 * e2)], fill=RED, width=22)
            df.line([(x + r * 0.9, y - r * 0.9), (x + r * 0.9 - 2 * e2, y - r * 0.9 + 2 * e2)], fill=M.scale_c(RED, 0.6), width=30)


def foco_motor(img, fx, x, y, s, k, col=(255, 176, 40)):
    """Icono genérico del foco del motor (silueta de un motor) encendido."""
    if k <= 0.01:
        return
    pts = [(-1.0, -0.2), (-0.75, -0.2), (-0.75, -0.45), (-0.3, -0.45), (-0.3, -0.6), (0.2, -0.6), (0.2, -0.45),
           (0.55, -0.45), (0.75, -0.25), (0.95, -0.25), (0.95, 0.35), (0.75, 0.35), (0.55, 0.55), (-0.55, 0.55),
           (-0.75, 0.3), (-1.0, 0.3)]
    pp = [(x + s * a, y + s * b) for a, b in pts]
    c = M.scale_c(col, k)
    ImageDraw.Draw(img).polygon(pp, outline=c, width=max(3, int(s * 0.09)))
    ImageDraw.Draw(fx).polygon(pp, outline=M.scale_c(col, 0.8 * k), width=max(5, int(s * 0.16)))
    ImageDraw.Draw(fx).ellipse((x - s * 1.4, y - s * 1.2, x + s * 1.4, y + s * 1.2), fill=M.scale_c(col, 0.12 * k))


def bujia_m(x, y, z=0.0, s=1.0):
    ms = [named(M3.cyl(0.11 * s, 0.5 * s, (238, 236, 230), n=20, shadow=0, gloss=0.7).tf(t=(x, y + 0.25 * s, z)), 'bujia', rim=0.8),
          named(M3.cyl(0.14 * s, 0.14 * s, (180, 180, 186), n=6, shadow=0, gloss=0.9).tf(t=(x, y + 0.1 * s, z)), 'bujia', rim=0.9),
          named(M3.cyl(0.08 * s, 0.22 * s, (170, 150, 110), n=16, shadow=0, gloss=0.8).tf(t=(x, y - 0.12 * s, z)), 'bujia', rim=0.8),
          named(M3.cyl(0.05 * s, 0.16 * s, (190, 190, 196), n=10, shadow=0, gloss=0.9).tf(t=(x, y + 0.75 * s, z)), 'bujia', rim=0.9)]
    return ms


# ================================================================== escenas
# 0. gancho (inicio 10: rayos X de golpe). En el pre-roll (lo que se ve al final, loop) el escape normal tira su gas
#    gris con «COCINA» de cristal detrás; en el primer golpe (u = 0.15) se vuelve de cristal y aparece el panal
#    brillando; con «lo cocina» se pone al rojo vivo.
U_RX = 0.15


def s_gancho(t, fi, u, d):
    uh = Wp(0, 'humo') - 0.1
    uc = Wp(0, 'cocina') - 0.1
    fr = Frame(camara(u, [K(-3.6, 5.6, 70, 14, tx=0.2, ty=Y), K(-1.2, 4.6, 44, 10, tx=-0.1, ty=Y),
                          K(U_RX, 3.4, 30, 8, tx=-0.35, ty=Y), K(uc, 2.9, 18, 6, tx=-0.4, ty=Y), K(4.0, 2.8, 12, 6, tx=-0.4, ty=Y)],
                      cy=0.5))
    space(fr, t, floor='lines', floor_a=0.55, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'COCINA', u, t0=-3.0, cy=0.43, entrada='golpe')
    xr = seg(u, U_RX, U_RX + 0.12)
    cal = 0.55 * seg(u, U_RX, U_RX + 0.3) + 0.45 * seg(u, uc, uc + 0.4)
    draw_objects(fr, escape(calor=cal), xray=xr, keep=('in', 'sensor'))
    if xr > 0.5:
        rejilla(fr, X_IN, col=M.mixc(CERAM, (255, 190, 110), cal), a=0.9 * xr, glow=0.6 + cal)
        P.ondas_calor(fr, t, -0.4, Y + 0.35, Y + 1.0, 0.8, k=seg(u, uc, uc + 0.3))
    gas(fr, t, limpia=xr, k=1.0)
    pt = fr.cam.p1((2.85, Y, 0))
    pc = fr.cam.p1((-0.4, Y - 0.35, 0))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Tu escape no tira humo…', 'sans'), ('lo cocina.', 'serif')], 190, seg(u, 0.1, 0.25), size=70)
        if u > uh - 0.1:
            P.pill_tachada(img, fx, min(900, pt[0]), pt[1] - 120, 'HUMO', seg(u, uh - 0.1, uh + 0.1), seg(u, uh + 0.3, uh + 0.6), t, size=32)
        kicker(img, 'CONVERTIDOR CATALÍTICO · RAYOS X', 1330, seg(u, U_RX, U_RX + 0.25), col=AZULC)
        if u > uc:
            pill(img, fx, pc[0], pc[1] + 70, '≈ 260–650 °C', eout(seg(u, uc, uc + 0.25)), size=26, border=NARANJA)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, U_RX, 0.35), golpe_k(u, 0.25, 0.3)), amp=24)


# 1. ese bulto en el tubo es el catalizador: el carro se vuelve de cristal y el escape queda debajo; crash zoom al bulto
def s_bulto(t, fi, u, d):
    uc = Wp(1, 'catalizador') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.2, 34, 12, ty=0.45), K(0.35, 6.2, 22, 8, ty=0.4), K(uc - 0.1, 6.0, 20, 8, ty=0.4),
                          K(uc + 0.1, 2.6, 12, 4, tx=-0.12, ty=0.2), K(d, 2.5, 8, 4, tx=-0.12, ty=0.2)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.4)
    ms = P.tfk(escape(), s=0.5, t=(0, -0.07, 0)) + auto(col=(70, 76, 90))
    draw_objects(fr, ms, xray=0.25 + 0.75 * seg(u, -0.2, 0.25), keep=('esc', 'in', 'sensor'))
    gas(fr, t * 1.0, limpia=1.0, k=0.0)
    pb = fr.cam.p1((-0.2, 0.18, 0))

    def ui(img, fx):
        kicker(img, 'DEBAJO DE TU CARRO', 150, seg(u, -0.1, 0.2), col=AZULC)
        kb = eout(seg(u, 0.3, 0.6))
        doodle_circle(img, fx, pb[0], pb[1], 150 + 120 * seg(u, uc, uc + 0.3), 70 + 70 * seg(u, uc, uc + 0.3), t, k=kb,
                      col=AMARILLO, seed=4)
        pill(img, fx, pb[0], pb[1] + 210, 'CATALIZADOR', eout(seg(u, uc + 0.1, uc + 0.35)), size=34, border=AMARILLO)
        if hay_foto('ext') and u > uc + 0.15:
            photo_card(img, fx, foto('ext'), 540, 470, 520, t - u + uc + 0.15, t, caption='Catalizador real · Dominio público',
                       angle0=-7.0)
        esquema(img, fx, seg(u, 0.2, 0.4), y=1450, txt='ESQUEMA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.3), amp=16)


# 2. y por dentro es un panal de cerámica: el cuerpo se abre en pedazos (vista explotada) y aparece el panal
def s_panal(t, fi, u, d):
    up = Wp(2, 'panal') - 0.1
    uc = Wp(2, 'ceramica') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.0, -30, 10, tx=-0.4, ty=Y), K(0.3, 2.6, -62, 8, tx=-0.4, ty=Y),
                          K(up, 2.0, -78, 4, tx=-0.6, ty=Y), K(d, 1.9, -82, 4, tx=-0.6, ty=Y)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.9, beam=0.5)
    M.cristal(fr.base, fr.fx, 'PANAL', u, t0=up - 0.1, cy=0.27, entrada='sube')
    k = P.eout4(seg(u, 0.05, 0.55))
    cat = catalizador_m()
    casco = [m for m in cat if m.name != 'in']
    adentro = [m for m in cat if m.name == 'in']
    draw_objects(fr, P.despiece(casco, k, centro=(-0.4, Y, 0), fuerza=1.3, giro=0.6) + adentro)
    rejilla(fr, X_IN - 0.002, col=CERAM, a=0.5 + 0.5 * seg(u, up, up + 0.3), glow=0.5 + 0.5 * seg(u, up, up + 0.3))

    def ui(img, fx):
        kicker(img, 'POR DENTRO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1180, 'CERÁMICA · CORDIERITA', eout(seg(u, uc, uc + 0.25)), size=28, border=CERAM)
        if hay_foto('int') and u > uc + 0.2:
            photo_card(img, fx, foto('int'), 780, 1300, 380, t - u + uc + 0.2, t, caption='Por dentro · CC0', angle0=8.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.4, 0.3), amp=14)


# 3. miles de canalitos cubiertos de platino, paladio y rodio: macro de la cara del panal (zoom digital)
def s_canales(t, fi, u, d):
    um = Wp(3, 'miles') - 0.1
    upt = Wp(3, 'platino') - 0.1
    upd = Wp(3, 'paladio') - 0.1
    urh = Wp(3, 'rodio') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, 0, 0, ty=1.0), K(0.3, 3.2, 14, 8, ty=1.0), K(upt, 2.4, -10, 6, ty=1.0, tx=0.1),
                          K(urh, 1.9, 8, 4, ty=1.0, tx=-0.1), K(d, 1.85, 10, 4, ty=1.0, tx=-0.1)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    s_ = 0.32
    n = 6
    for i in range(-n, n + 1):                               # la cuadrícula y sus paredes que se van hacia el fondo
        a = 0.9 * (1 - abs(i) / (n + 1.5))
        line3(fr, [(i * s_, 1.0 - n * s_, 0), (i * s_, 1.0 + n * s_, 0)], col=CERAM, w=3.2, a=a, glow=0.6)
        line3(fr, [(-n * s_, 1.0 + i * s_, 0), (n * s_, 1.0 + i * s_, 0)], col=CERAM, w=3.2, a=a, glow=0.6)
        for j in range(-n, n + 1, 2):
            line3(fr, [(i * s_, 1.0 + j * s_, 0), (i * s_, 1.0 + j * s_, -2.5)], col=CERAM, w=1.5, a=0.35 * a, glow=0.3)
    rng = np.random.RandomState(5)
    for j in range(120):                                       # las chispas de metal en las paredes
        cual = j % 3
        u0 = (upt, upd, urh)[cual]
        i, jj = rng.randint(-n, n), rng.randint(-n, n)
        ofs = rng.rand()
        p = (i * s_ + ofs * s_, 1.0 + jj * s_, -rng.rand() * 0.8) if j % 2 else (i * s_, 1.0 + jj * s_ + ofs * s_, -rng.rand() * 0.8)
        dot3(fr, p, r=3 + 3 * math.sin(t * 6 + j) ** 2, col=(PT, PD, RH)[cual], a=seg(u, u0, u0 + 0.25), glow=1.5)

    def ui(img, fx):
        kicker(img, 'CIENTOS DE CELDAS POR PULGADA²', 150, seg(u, um, um + 0.25), col=AZULC)
        texto(img, fx, 540, 280, 'miles de canalitos', 66, WHITE, eout(seg(u, um, um + 0.25)), f='serif', glow=0.35)
        for k_, (u0, nom, sim, col, y) in enumerate(((upt, 'PLATINO', 'Pt', PT, 1220), (upd, 'PALADIO', 'Pd', PD, 1300),
                                                     (urh, 'RODIO', 'Rh', RH, 1380))):
            pill(img, fx, 540, y, f'{sim} · {nom}', eout(seg(u, u0, u0 + 0.2)), size=28, border=col)
        rec_frame(img, t, seg(u, 0.2, 0.35), zoom_label='x40' if u < upt else 'x80')
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. al pasar por ahí, el gas sucio se transforma: la cámara viaja dentro de un canalito
def s_tunel(t, fi, u, d):
    us = Wp(4, 'sucio') - 0.1
    ut = Wp(4, 'transforma') - 0.1
    fr = Frame(camara(u, [K(-0.3, 1.0, 0, 0, ty=0.5, tz=-1.0), K(0.3, 1.0, 10, 4, ty=0.5, tz=-1.0, roll=8),
                          K(ut, 1.0, -6, -2, ty=0.5, tz=-1.0, roll=-6), K(d, 1.0, -8, -2, ty=0.5, tz=-1.0, roll=-6)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    tunel(fr, t, k=1.0, z0=0.0, vel=1.6)
    rng = np.random.RandomState(8)
    for j in range(40):                                        # el gas que entra contigo y cambia de color
        ph = ((t * 0.5 + j / 40) % 1.0)
        z = -0.2 - 6.0 * ph
        x, y = (rng.rand() - 0.5) * 0.5, 0.5 + (rng.rand() - 0.5) * 0.5
        c = M.mixc(SUCIO, LIMPIO, seg(ph, 0.25, 0.75) * seg(u, ut - 0.3, ut + 0.2) + 0.15 * seg(ph, 0.3, 0.9))
        dot3(fr, (x, y, z), r=5, col=c, a=0.9, glow=0.9)

    def ui(img, fx):
        kicker(img, 'DENTRO DE UN CANALITO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1250, 'GAS SUCIO', eout(seg(u, us, us + 0.2)), size=30, border=SUCIO)
        texto(img, fx, 540, 330, 'se transforma', 72, LIMPIO, eout(seg(u, ut, ut + 0.25)), f='serif', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. el monóxido de carbono, que envenena, sale como dióxido de carbono (CO + O → CO2)
def s_co(t, fi, u, d):
    ue = Wp(5, 'envenena') - 0.1
    us = Wp(5, 'sale') - 0.1
    ud = Wp(5, 'dioxido') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.2, -30, 8, ty=1.0), K(0.3, 3.4, 10, 6, ty=1.0), K(us, 3.0, 30, 6, ty=1.0),
                          K(d, 2.9, 34, 6, ty=1.0)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8)
    tunel(fr, t, k=0.35, z0=3.5, vel=0.6, cy=1.0, h=1.6, chispas=0.6)
    e = P.entrada(u, -0.25, 0.3, 'pop')
    sc = max(0.05, e['escala'])
    ko = P.eout4(seg(us, us, us) if False else seg(u, us, us + 0.45))
    rot = t * 0.7
    at = [((-0.28, 0, 0), 0.34, C_C), ((0.3, 0, 0), 0.3, C_O)]
    if u > us - 0.05:                                          # el oxígeno que llega del metal y se pega
        at = [((-0.9 - 1.4 * (1 - ko), 0.9 * (1 - ko), 0), 0.3, C_O)] + at
    draw_objects(fr, molecula(at, rot=rot, s=sc))
    if u > us - 0.05 and ko < 0.95:
        dot3(fr, (-1.6, 1.9, 0), r=10, col=PT, a=1 - ko, glow=2.0)
    if u > ud:
        dot3(fr, (0, 1.0, 0), r=40 + 120 * seg(u, ud, ud + 0.4), col=LIMPIO, a=0.5 * (1 - seg(u, ud, ud + 0.5)), glow=1.5)

    def ui(img, fx):
        kd = seg(u, ud, ud + 0.2)
        texto(img, fx, 540, 300, 'CO', 150, (255, 120, 100), (1 - kd) * eout(seg(u, -0.2, 0.05)), f='sansx', glow=0.6)
        texto(img, fx, 540, 300, 'CO2', 150, LIMPIO, kd, f='sansx', glow=0.6)
        pill(img, fx, 540, 430, 'MONÓXIDO DE CARBONO' if u < ud else 'DIÓXIDO DE CARBONO', 1.0, size=26,
             border=(255, 120, 100) if u < ud else LIMPIO, dot=False)
        if ue < u < ud:
            texto(img, fx, 540, 1300, 'ENVENENA', 70, RED, eout(seg(u, ue, ue + 0.15)), glow=0.8)
        esquema(img, fx, 1.0, y=1450, txt='ESQUEMA · MOLÉCULAS')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.45, 0.3), amp=12)


# 6. la gasolina sin quemar, como agua: la cadena de hidrocarburo se rompe en moléculas de agua y cae una gota
def s_agua(t, fi, u, d):
    ua = Wp(6, 'agua') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, 40, 10, ty=1.0), K(0.3, 4.0, 6, 6, ty=1.0), K(ua, 3.4, -20, 6, ty=1.0),
                          K(d, 3.3, -24, 6, ty=1.0)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8)
    tunel(fr, t, k=0.35, z0=3.5, vel=0.6, cy=1.0, h=1.6, chispas=0.6)
    k = P.eout4(seg(u, ua - 0.4, ua + 0.2))
    ms = []
    if k < 0.98:                                               # cadena: C-C-C-C con sus H
        e = P.entrada(u, -0.25, 0.3, 'gira')
        sc = max(0.05, e['escala']) * (1 - k)
        cad = []
        for i in range(4):
            x = -0.75 + 0.5 * i
            y = 0.12 if i % 2 else -0.12
            cad.append(((x, y, 0), 0.22, C_C))
        ms += molecula(cad, rot=t * 0.8 + e['giro'], s=max(0.05, sc))
        for i in range(4):
            x = -0.75 + 0.5 * i
            y = 0.45 if i % 2 else -0.45
            ms.append(esfera(0.12 * max(0.05, sc), C_H, (x * max(0.05, sc), 1.0 + y * max(0.05, sc), 0.1)))
    if k > 0.02:                                               # moléculas de agua
        for j, (x, y) in enumerate(((-0.7, 1.35), (0.6, 1.25), (0.0, 0.7))):
            s2 = max(0.05, k)
            at = [((-0.26, 0.2, 0), 0.13, C_H), ((0, 0, 0), 0.24, C_O), ((0.26, 0.2, 0), 0.13, C_H)]
            ms += molecula(at, rot=t * 0.9 + j, centro=(x * (0.4 + 0.6 * k), y, 0), s=s2)
    draw_objects(fr, ms)
    if u > ua:
        g = gota_m((120, 190, 255), 0.18)
        draw_objects(fr, P.tfk(g, t=(0.9, 1.9 - 1.6 * P.eout4(seg(u, ua, ua + 0.6)), 0.3)))

    def ui(img, fx):
        texto(img, fx, 540, 290, 'GASOLINA SIN QUEMAR', 56, AMARILLO, (1 - seg(u, ua, ua + 0.2)) * eout(seg(u, -0.2, 0.1)), glow=0.4)
        texto(img, fx, 540, 290, 'AGUA · H2O', 86, (120, 190, 255), seg(u, ua, ua + 0.2), glow=0.6)
        esquema(img, fx, 1.0, y=1450, txt='ESQUEMA · MOLÉCULAS')
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. y los óxidos de nitrógeno… como el nitrógeno del aire (NO pierde su oxígeno en el rodio → N2 que sube al aire)
def s_nitro(t, fi, u, d):
    un = Wp(7, 'nitrogeno') - 0.1
    ua = Wp(7, 'aire') - 0.1
    un2 = Wp(7, 'nitrogeno', 1) - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, -10, 4, ty=1.0), K(0.3, 3.8, -40, 10, ty=1.1), K(un2, 4.6, -20, 16, ty=1.4),
                          K(d, 4.8, -16, 16, ty=1.5)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.0)
    k = P.eout4(seg(u, un2 - 0.6, un2))
    ms = []
    for j, x in enumerate((-0.6, 0.6)):                       # 2 NO: el O se va al metal y quedan los N juntos
        xn = x * (1 - k) + (-0.17 if j == 0 else 0.17) * k
        ms.append(esfera(0.26, C_N, (xn, 1.0 + 1.2 * seg(u, ua, d), 0)))
        if k < 0.97:
            ms.append(esfera(0.23, C_O, (x * 1.6 + (x * 1.6) * 1.5 * k, 1.0 - 1.4 * k, 0.2 * j)))
    if k > 0.6:
        ms.append(enlace((-0.17, 1.0 + 1.2 * seg(u, ua, d), 0), (0.17, 1.0 + 1.2 * seg(u, ua, d), 0), 0.06))
    draw_objects(fr, ms)
    rng = np.random.RandomState(4)
    ka = seg(u, ua - 0.2, ua + 0.4)
    for j in range(26):                                         # «el aire»: muchas parejas de N2
        p = np.array([(rng.rand() - 0.5) * 5, 1.4 + rng.rand() * 2.5 + 0.2 * math.sin(t + j), -1 - rng.rand() * 2])
        dot3(fr, p, r=7, col=C_N, a=ka * 0.8, glow=0.8)
        dot3(fr, p + np.array([0.12, 0.03, 0]), r=7, col=C_N, a=ka * 0.8, glow=0.8)
    dot3(fr, (0, -0.4, 0), r=14 + 10 * math.sin(t * 9) ** 2, col=RH, a=seg(u, un2 - 0.6, un2 - 0.3), glow=2.0)

    def ui(img, fx):
        texto(img, fx, 540, 290, 'NOx' if u < un2 else 'N2', 140, (255, 140, 110) if u < un2 else (140, 175, 255), 1.0,
              glow=0.6)
        pill(img, fx, 540, 420, 'ÓXIDOS DE NITRÓGENO' if u < un2 else 'NITRÓGENO · EL 78 % DEL AIRE', eout(seg(u, -0.2, 0.1)),
             size=26, border=(255, 140, 110) if u < un2 else C_N, dot=False)
        pill(img, fx, 540, 1330, 'RODIO · Rh', seg(u, un2 - 0.6, un2 - 0.4), size=26, border=RH)
        esquema(img, fx, 1.0, y=1450, txt='ESQUEMA · MOLÉCULAS')
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. pero solo cocina caliente: arriba de unos 260 °C (termómetro que sube y el panal al rojo; «CALIENTE» de cristal)
def s_caliente(t, fi, u, d):
    uc = Wp(8, 'caliente') - 0.1
    u2 = Wp(8, 'doscientos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, -50, 14, tx=-0.4, ty=Y), K(0.3, 3.0, -30, 10, tx=-0.4, ty=Y),
                          K(u2, 2.5, -12, 6, tx=-0.4, ty=Y + 0.05), K(d, 2.45, -8, 6, tx=-0.4, ty=Y + 0.05)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, 'CALIENTE', u, t0=uc, cy=0.3, entrada='zoom')
    cal = seg(u, 0.0, u2 + 0.3)
    draw_objects(fr, catalizador_m(calor=cal), xray=0.85, keep=('in',))
    rejilla(fr, X_IN, col=M.mixc(CERAM, (255, 170, 90), cal), a=0.85, glow=0.6 + cal)
    P.ondas_calor(fr, t, -0.4, Y + 0.4, Y + 1.1, 0.9, k=cal)

    def ui(img, fx):
        kicker(img, 'SOLO TRABAJA CALIENTE', 150, seg(u, -0.1, 0.2), col=(255, 180, 140))
        P.termometro(img, fx, 160, 1380, 520, 0.12 + 0.8 * cal, f'{int(20 + 240 * cal)} °C', k=seg(u, -0.1, 0.1), col=(255, 120, 70))
        P.numero_golpe(img, fx, '260 °C', 1220, seg(u, u2, u2 + 0.15), size=150, col=NARANJA)
        pill(img, fx, 620, 1350, 'TEMPERATURA DE «ENCENDIDO»', eout(seg(u, u2 + 0.3, u2 + 0.55)), size=22, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u2 + 0.15, 0.35), amp=20)


# 9. la prueba: con el motor frío, casi todo pasa directo (el gas sale gris por la cola)
def s_frio(t, fi, u, d):
    ud = Wp(9, 'directo') - 0.1
    uf = Wp(9, 'frio') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.2, 20, 18, tx=0.4, ty=Y), K(0.3, 4.6, 4, 12, tx=0.3, ty=Y), K(ud, 3.9, -16, 10, tx=1.2, ty=Y),
                          K(d, 3.8, -20, 10, tx=1.3, ty=Y)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.3)
    draw_objects(fr, escape(frio=1.0), xray=0.8, keep=('in', 'sensor'))
    rejilla(fr, X_IN, col=FRIO, a=0.7, glow=0.5)
    gas(fr, t, limpia=0.0, k=1.0, vel=0.7)
    humo(fr, t, k=seg(u, ud - 0.3, ud + 0.2))
    pt = fr.cam.p1((2.9, Y + 0.3, 0))

    def ui(img, fx):
        kicker(img, 'LA PRUEBA · MOTOR FRÍO', 150, seg(u, -0.1, 0.2), col=FRIO)
        P.termometro(img, fx, 160, 1380, 420, 0.12, '20 °C', k=seg(u, uf, uf + 0.2), col=FRIO)
        pill(img, fx, min(860, pt[0]), pt[1] - 120, 'PASA DIRECTO', eout(seg(u, ud, ud + 0.25)), size=30, border=SUCIO)
        esquema(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. por eso, en un arranque en frío: el carro (visto desde atrás) arranca y tira su nube gris
def s_arranque(t, fi, u, d):
    ua = Wp(10, 'arranque') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.4, -120, 10, ty=0.6), K(0.3, 5.4, -100, 8, ty=0.55), K(d, 5.2, -96, 8, ty=0.55)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.4)
    temb = golpe_k(u, ua, 0.5) * 0.02 * math.sin(t * 80)
    ms = auto(col=(60, 70, 96)) + [tubo((-1.35, 0.2, 0.42), (-1.62, 0.2, 0.42), r=0.05, col=CROMO, name='cola', gloss=0.95)]
    draw_objects(fr, P.tfk(ms, t=(0, temb, 0)))
    humo(fr, t, k=seg(u, ua, ua + 0.2), x=-1.65, y=0.2, col=(150, 148, 144), n=24, dx=-1.0)
    for j in range(10):                                         # la nube: se va hacia atrás (−x)
        ph = seg(u, ua + 0.05 * j, ua + 1.4 + 0.05 * j)
        if ph > 0:
            nube(fr, (-1.7 - 1.4 * ph, 0.2 + 0.5 * ph, 0.42 + 0.4 * math.sin(j)), 10 + 34 * ph, (160, 158, 155), 1 - ph)

    def ui(img, fx):
        texto(img, fx, 540, 290, 'arranque en frío', 76, FRIO, eout(seg(u, ua, ua + 0.25)), f='serif', glow=0.4)
        kicker(img, 'LA MAÑANA · MOTOR FRÍO', 150, seg(u, -0.1, 0.2), col=FRIO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua, 0.4), amp=14)


# 11. hasta el 80 % de lo que contamina sale en el primer minuto y medio («80 %» de cristal, cronómetro y barras)
def s_ochenta(t, fi, u, d):
    u8 = Wp(11, 'ochenta') - 0.1
    um = Wp(11, 'minuto') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, 30, 6, ty=1.0), K(0.3, 5.2, 8, 4, ty=1.0), K(d, 5.0, 4, 4, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '80 %', u, t0=u8 - 0.3, cy=0.3, entrada='golpe')

    def ui(img, fx):
        kicker(img, 'ARRANQUE EN FRÍO · PRUEBA DE EMISIONES', 150, seg(u, -0.1, 0.2), col=AZULC)
        ks = 1.0
        cx, cy, r = 540, 1130, 170
        dl = ImageDraw.Draw(img)
        dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(WHITE, ks), width=6)
        dl.rectangle((cx - 22, cy - r - 40, cx + 22, cy - r - 8), fill=M.scale_c(WHITE, ks))
        seg_ = 90 * seg(u, 0.0, um + 0.6)
        a = math.radians(-90 + 360 * (seg_ % 60) / 60)
        dl.line([(cx, cy), (cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a))], fill=M.scale_c(AMARILLO, ks), width=8)
        dl.pieslice((cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14), -90, -90 + 360 * min(seg_, 60) / 60,
                    fill=M.scale_c((255, 120, 80), 0.35 * ks))
        texto(img, fx, cx, cy + r + 70, f'{int(seg_ // 60)}:{int(seg_ % 60):02d}', 70, WHITE, ks, f='mono', glow=0.4)
        texto(img, fx, 540, 1520 - 40, 'EL PRIMER MINUTO Y MEDIO', 30, AMARILLO, eout(seg(u, um, um + 0.25)), f='mono', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u8, 0.35), amp=22)


# 12. ya caliente, quita casi el 90 % (el panal brilla y el gas sale limpio; barra que se llena; «90 %» de cristal)
def s_noventa(t, fi, u, d):
    u9 = Wp(12, 'noventa') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, -24, 10, tx=0.0, ty=Y), K(0.3, 4.0, -4, 8, tx=0.2, ty=Y), K(d, 3.9, 0, 8, tx=0.2, ty=Y)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, '90 %', u, t0=u9, cy=0.29, entrada='zoom')
    draw_objects(fr, escape(calor=1.0), xray=0.85, keep=('in', 'sensor'))
    rejilla(fr, X_IN, col=(255, 190, 110), a=0.85, glow=1.4)
    gas(fr, t, limpia=1.0, k=1.0)

    def ui(img, fx):
        kicker(img, 'YA CALIENTE', 150, seg(u, -0.1, 0.2), col=(255, 180, 140))
        kb = eout(seg(u, 0.1, 0.35))
        dl = ImageDraw.Draw(img)
        x0, y0, w = 200, 1290, 680
        dl.rounded_rectangle((x0, y0, x0 + w, y0 + 50), radius=22, outline=M.scale_c(WHITE, kb), width=3)
        lv = 0.9 * P.eout4(seg(u, u9 - 0.4, u9 + 0.3))
        if lv > 0.01:
            dl.rounded_rectangle((x0 + 6, y0 + 6, x0 + 6 + (w - 12) * lv, y0 + 44), radius=16, fill=M.scale_c(LIMPIO, kb))
        texto(img, fx, 540, y0 + 100, 'CO Y NOx QUE QUITA', 28, GRIS, kb, f='mono', glow=0.2)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. el error: quitarlo o vaciarlo «para que corra más» (el catalizador sale volando y queda un tubo recto)
def s_error(t, fi, u, d):
    uq = Wp(13, 'quitarlo') - 0.1
    uc = Wp(13, 'corra') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.4, 40, 14, tx=-0.4, ty=Y + 0.3), K(0.3, 4.6, 24, 10, tx=-0.4, ty=Y + 0.4),
                          K(uq, 4.4, 10, 8, tx=-0.4, ty=Y + 0.6), K(d, 4.3, 6, 8, tx=-0.4, ty=Y + 0.6)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.5)
    sale = seg(u, uq, uq + 0.6)
    draw_objects(fr, escape(sale=sale, recto=seg(u, uq + 0.4, uq + 0.8)))
    pr = fr.cam.p1((-0.4, Y - 0.15, 0))

    def ui(img, fx):
        texto(img, fx, 540, 250, 'EL ERROR', 110, RED, eout(seg(u, 0.0, 0.12)), glow=0.8)
        kicker(img, 'QUE TE SALE CARO', 370, seg(u, 0.2, 0.45), col=(255, 160, 150))
        pill(img, fx, pr[0], pr[1] + 120, 'TUBO RECTO', eout(seg(u, uq + 0.7, uq + 0.95)), size=28, border=(255, 140, 130))
        if u > uc - 0.2:
            P.pill_tachada(img, fx, 540, 1330, '«PARA QUE CORRA MÁS»', seg(u, uc - 0.2, uc), seg(u, uc + 0.4, uc + 0.7), t, size=30)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.0, 0.35), golpe_k(u, uq + 0.1, 0.3)), amp=24)


# 14. tu computadora lo nota con un sensor y prende el foco del motor
def s_sensor(t, fi, u, d):
    us = Wp(14, 'sensor') - 0.1
    uf = Wp(14, 'foco') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.4, -30, 16, tx=0.2, ty=Y), K(0.3, 3.2, -6, 12, tx=0.5, ty=Y + 0.1),
                          K(us, 2.2, 10, 10, tx=0.6, ty=Y + 0.15), K(uf, 3.6, 20, 12, tx=0.6, ty=Y + 0.4),
                          K(d, 3.5, 22, 12, tx=0.6, ty=Y + 0.4)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.3)
    ms = escape(sale=1.0, recto=1.0)
    ms = [m for m in ms if m.name != 'in' and not (m.name == 'esc' and np.asarray(m.V)[:, 1].mean() > Y + 0.8)]
    ms.append(named(M3.cyl(0.055, 0.04, M.scale_c(CYAN, 0.3 + 0.7 * seg(u, us, us + 0.2)), n=10, shadow=0).tf(t=(0.6, Y + 0.26, 0)),
                    'sensor', glow=M.scale_c(CYAN, 0.8 * seg(u, us, us + 0.2))))
    _B(ms, 0.7, 0.18, 0.5, (40, 44, 52), 1.4, Y + 0.9, -0.2, name='ecu', gloss=0.6)
    _B(ms, 0.26, 0.04, 0.26, (30, 30, 34), 1.4, Y + 1.08, -0.2, name='chip', gloss=0.8,
       glow=M.scale_c(CYAN, 0.5 + 0.5 * math.sin(t * 8) ** 2))
    draw_objects(fr, ms)
    line3(fr, [(0.6, Y + 0.3, 0), (0.6, Y + 0.7, 0), (1.1, Y + 0.8, -0.1), (1.4, Y + 0.95, -0.2)], col=CYAN, w=2.6,
          a=seg(u, us, us + 0.2), glow=1.2, frac=seg(u, us, us + 0.5))
    pse = fr.cam.p1((0.6, Y + 0.3, 0))
    pe = fr.cam.p1((1.4, Y + 1.15, -0.2))

    def ui(img, fx):
        kicker(img, 'SENSOR DE OXÍGENO · COMPUTADORA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pse[0] - 120, pse[1] + 110, 'SENSOR', eout(seg(u, us, us + 0.25)), size=26, border=CYAN)
        pill(img, fx, pe[0], pe[1] - 70, 'COMPUTADORA', eout(seg(u, 0.1, 0.35)), size=24, border=(200, 200, 210), dot=False)
        kf = eout(seg(u, uf, uf + 0.15))
        foco_motor(img, fx, 540, 1260, 95, kf * (0.8 + 0.2 * math.sin(t * 10) ** 2))
        texto(img, fx, 540, 1420, 'P0420', 40, (255, 176, 40), kf, f='mono', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uf, 0.3), amp=14)


# 15. y en la verificación te rechazan: el holograma se tacha y cae el sello «RECHAZADO»
def s_rechazo(t, fi, u, d):
    ur = Wp(15, 'rechazan') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.0, 50, 10, ty=0.7), K(0.3, 6.2, 30, 8, ty=0.7), K(d, 6.0, 26, 8, ty=0.7)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.6)
    draw_objects(fr, auto(col=(70, 76, 90)), xray=0.6)

    def ui(img, fx):
        kicker(img, 'LA VERIFICACIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        sticker(img, fx, 540, 560, 210, eout(seg(u, -0.15, 0.15)), t, tache=seg(u, ur, ur + 0.3))
        P.numero_golpe(img, fx, 'RECHAZADO', 1240, seg(u, ur, ur + 0.15), size=130, col=RED)
        esquema(img, fx, 1.0, y=1450, txt='HOLOGRAMA DE EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ur + 0.15, 0.4), amp=26)


# 16. un catalizador quitado o vaciado es una pieza alterada (rayos X: el cuerpo está vacío por dentro)
def s_alterada(t, fi, u, d):
    uv = Wp(16, 'vaciado') - 0.1
    ua = Wp(16, 'alterada') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, 40, 12, tx=-0.4, ty=Y), K(0.3, 2.9, 14, 8, tx=-0.4, ty=Y), K(ua, 2.5, -14, 6, tx=-0.4, ty=Y),
                          K(d, 2.45, -18, 6, tx=-0.4, ty=Y)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.4)
    draw_objects(fr, catalizador_m(vacio=True), xray=seg(u, uv - 0.2, uv + 0.1), keep=())
    pc = fr.cam.p1((-0.4, Y, 0))

    def ui(img, fx):
        kicker(img, 'NOM-047 · REVISIÓN VISUAL', 150, seg(u, -0.1, 0.2), col=AZULC)
        kv = eout(seg(u, uv, uv + 0.25))
        texto(img, fx, pc[0], pc[1], 'VACÍO', 60, (255, 140, 130), kv, f='mono', glow=0.6)
        doodle_circle(img, fx, pc[0], pc[1], 260, 150, t, k=kv, col=RED, seed=6)
        pill(img, fx, 540, 1300, 'PIEZA ALTERADA = RECHAZO', eout(seg(u, ua, ua + 0.25)), size=30, border=RED)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. y si una bujía falla, la gasolina cruda se quema adentro… (la bujía sin chispa; gotas que corren al panal y prenden)
def s_bujia(t, fi, u, d):
    ub = Wp(17, 'bujia') - 0.1
    uf = Wp(17, 'falla') - 0.1
    ug = Wp(17, 'gasolina') - 0.1
    uq = Wp(17, 'quema') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, 30, 8, tx=-2.6, ty=Y + 0.6), K(0.3, 3.0, 12, 6, tx=-2.6, ty=Y + 0.6),
                          K(ug, 3.4, 20, 8, tx=-1.6, ty=Y + 0.2), K(uq - 0.2, 3.0, 10, 6, tx=-0.5, ty=Y),
                          K(d, 2.9, 6, 6, tx=-0.5, ty=Y)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    e = P.entrada(u, -0.25, 0.3, 'cae')
    ms = P.tfk(bujia_m(-3.0, Y + 0.35), t=(0, -e['dy'] * 0.4, 0)) + escape(calor=0.5 * seg(u, uq, d))
    draw_objects(fr, ms, xray=0.8, keep=('in', 'bujia', 'sensor'))
    chispa = (math.sin(t * 25) > 0.6) and u < uf
    if chispa:
        dot3(fr, (-3.0, Y + 0.25, 0), r=16, col=(200, 220, 255), a=1.0, glow=2.4)
    for j in range(14):                                          # gotas de gasolina cruda que van al panal
        ph = seg(u, ug + 0.06 * j, ug + 1.0 + 0.06 * j)
        if 0 < ph < 1:
            x = -2.7 + (X_IN + 0.3 + 2.7) * ph
            dot3(fr, (x, Y + 0.03 * math.sin(j * 3), 0.03 * math.cos(j * 2)), r=6, col=AMARILLO, a=1.0, glow=1.2)
    kq = seg(u, uq, uq + 0.4)
    if kq > 0:
        rng = np.random.RandomState(9)
        for j in range(26):
            ph = (t * 1.5 + j / 26) % 1.0
            p = (X_IN + rng.rand() * (X_OUT - X_IN), Y + (rng.rand() - 0.5) * 0.4 + 0.3 * ph, (rng.rand() - 0.5) * 0.5)
            dot3(fr, p, r=6 + 12 * ph, col=(255, 110 + int(90 * ph), 40), a=kq * (1 - ph), glow=2.0)
    pb = fr.cam.p1((-3.0, Y + 1.2, 0))

    def ui(img, fx):
        kicker(img, 'UNA BUJÍA QUE FALLA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pb[0] + 40, pb[1] - 40, 'BUJÍA', eout(seg(u, ub, ub + 0.25)), size=28, border=AMARILLO)
        if u > uf:
            texto(img, fx, 540, 330, 'SIN CHISPA', 80, RED, eout(seg(u, uf, uf + 0.15)), glow=0.7)
        pill(img, fx, 540, 1330, 'GASOLINA CRUDA', eout(seg(u, ug, ug + 0.25)), size=28, border=AMARILLO)
        esquema(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uq, 0.35), amp=16)


# 18. y lo puede derretir: la cara del panal al blanco que se escurre («DERRETIR» de cristal)
def s_derrite(t, fi, u, d):
    ud = Wp(18, 'derretir') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.6, -60, 4, tx=-0.7, ty=Y), K(0.3, 1.6, -86, 2, tx=-0.8, ty=Y), K(d, 1.5, -88, 2, tx=-0.8, ty=Y)],
                      cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'DERRETIR', u, t0=ud - 0.1, cy=0.26, entrada='golpe')
    km = seg(u, ud, ud + 1.0)
    draw_objects(fr, catalizador_m(calor=1.0), xray=0.9, keep=('in',))
    rejilla(fr, X_IN - 0.002, col=M.mixc((255, 170, 90), (255, 245, 220), km), a=0.95, glow=1.6 + km, caida=km, t=t)
    P.ondas_calor(fr, t, -0.8, Y + 0.3, Y + 0.9, 0.6, k=1.0)
    rng = np.random.RandomState(12)
    for j in range(12):                                          # gotas de cerámica fundida que escurren
        ph = (t * 0.8 + j / 12) % 1.0
        dot3(fr, (X_IN - 0.01, Y - 0.2 - 0.5 * ph * km, (rng.rand() - 0.5) * 0.5), r=5, col=(255, 200, 120), a=km * (1 - ph), glow=1.6)

    def ui(img, fx):
        kicker(img, 'SOBRECALENTAMIENTO', 150, seg(u, -0.1, 0.2), col=(255, 180, 140))
        pill(img, fx, 540, 1330, 'EL PANAL SE FUNDE', eout(seg(u, ud + 0.2, ud + 0.45)), size=30, border=NARANJA)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.2 + 0.3 * golpe_k(u, ud, 0.4), amp=10)


# 19. mándaselo a quien no pasó la verificación (el carro con su escape brillando debajo y el holograma tachado)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.4, 70, 10, ty=0.5), K(0.4, 6.4, 40, 8, ty=0.5), K(d, 6.2, 34, 8, ty=0.5)], cy=0.64))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.0)
    ms = P.tfk(escape(calor=0.6), s=0.5, t=(0, -0.07, 0)) + auto(col=(70, 76, 90))
    draw_objects(fr, ms, xray=0.7, keep=('esc', 'in', 'sensor'))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien', 'sans'), ('no pasó la verificación.', 'serif')], 230, seg(u, 0.0, 0.15), size=64)
        sticker(img, fx, 540, 1250, 120, eout(seg(u, 0.3, 0.55)), t, tache=seg(u, 0.6, 0.9))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-2.0, 'whoosh_suave', 0.4), (U_RX, 'sub', 1.0), (U_RX, 'shimmer', 0.6), (0.25, 'bass', 0.8),
                     (1.0, 'scribble', 0.5), (1.9, 'riser', 0.4)]),
           dict(desde=1, fn=s_bulto, tr='zoom', c=(0.5, 0.55), sfx=[(0.4, 'scribble', 0.6), (1.4, 'bass', 0.8), (1.6, 'slap', 0.7)]),
           dict(desde=2, fn=s_panal, tr='giro', c=(0.45, 0.55), sfx=[(0.1, 'whoosh', 0.7), (0.45, 'thud', 0.8), (1.6, 'slap', 0.6)]),
           dict(desde=3, fn=s_canales, tr='golpe', sfx=[(0.25, 'click', 0.6), (1.9, 'chime_a', 0.5), (2.6, 'chime_b', 0.5),
                                                       (3.3, 'chime_c', 0.5), (2.0, 'click', 0.5)]),
           dict(desde=4, fn=s_tunel, tr='push', c=(0.5, 0.5), sfx=[(0.0, 'whoosh_suave', 0.7), (0.9, 'tick', 0.5), (1.9, 'shimmer', 0.5)]),
           dict(desde=5, fn=s_co, tr='mosaico', sfx=[(1.3, 'burst', 0.6), (2.3, 'whoosh', 0.6), (2.8, 'click', 0.8), (2.9, 'chime_b', 0.5)]),
           dict(desde=6, fn=s_agua, tr='deslizar', sfx=[(0.1, 'whoosh', 0.5), (1.4, 'chime_a', 0.5), (1.9, 'tick2', 0.6)]),
           dict(desde=7, fn=s_nitro, tr='rebanadas', sfx=[(1.6, 'shimmer', 0.5), (2.2, 'click', 0.6), (2.8, 'whoosh_suave', 0.5)]),
           dict(desde=8, fn=s_caliente, tr='rompe', c=(0.5, 0.45), sfx=[(0.2, 'riser', 0.6), (2.7, 'sub', 1.0), (2.7, 'bass', 0.8)]),
           dict(desde=9, fn=s_frio, tr='cubo', sfx=[(0.1, 'whoosh_suave', 0.5), (1.4, 'tick', 0.5), (2.9, 'slap', 0.5)]),
           dict(desde=10, fn=s_arranque, tr='flash', sfx=[(0.5, 'thud', 0.9), (0.6, 'bass', 0.6), (0.9, 'whoosh_suave', 0.6)]),
           dict(desde=11, fn=s_ochenta, tr='whip', sfx=[(0.4, 'sub', 1.0), (0.4, 'bass', 0.8)] + [(0.2 + 0.25 * j, 'tick2', 0.35) for j in range(16)]),
           dict(desde=12, fn=s_noventa, tr='iris', c=(0.5, 0.5), sfx=[(0.6, 'riser', 0.5), (1.6, 'chime_c', 0.6), (1.7, 'shimmer', 0.5)]),
           dict(desde=13, fn=s_error, tr='rompe', c=(0.5, 0.35), sfx=[(0.0, 'bass', 0.9), (0.0, 'digital', 0.5), (1.5, 'whoosh', 0.8),
                                                                   (2.0, 'thud', 0.8), (3.1, 'scribble', 0.5)]),
           dict(desde=14, fn=s_sensor, tr='deslizar_abajo', sfx=[(1.4, 'digital', 0.6), (1.5, 'tick', 0.6), (2.5, 'bass', 0.8),
                                                                 (2.6, 'chime_a', 0.4)]),
           dict(desde=15, fn=s_rechazo, tr='golpe', sfx=[(0.1, 'shimmer', 0.4), (1.1, 'slap', 1.0), (1.2, 'sub', 0.9)]),
           dict(desde=16, fn=s_alterada, tr='cristal', palabra='ALTERADA', sfx=[(1.4, 'digital', 0.5), (1.5, 'scribble', 0.6),
                                                                                (2.7, 'bass', 0.7)]),
           dict(desde=17, fn=s_bujia, tr='wipe', sfx=[(0.0, 'thud', 0.6), (0.7, 'tick2', 0.5), (0.9, 'burst', 0.5), (2.6, 'sub', 0.8),
                                                      (2.7, 'burst', 0.6)]),
           dict(desde=18, fn=s_derrite, tr='remolino', sfx=[(0.3, 'riser', 0.5), (0.5, 'sub', 0.8), (1.0, 'burst', 0.4)]),
           dict(desde=19, fn=s_compa, tr='cubo_izq', sfx=[(0.15, 'bass', 0.7), (0.5, 'shimmer', 0.4), (0.8, 'scribble', 0.5)]),
           dict(desde=20, loop=True, tr='whip_izq')]

if __name__ == '__main__':
    montaje.cli(globals())
