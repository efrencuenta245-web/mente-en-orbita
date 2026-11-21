"""Reel diario lun 23-nov-2026 18:00 (propuesto) — «Tu tractor trae las llantas… llenas de agua.»
Lastre líquido: a las llantas traseras de muchos tractores se les mete agua (o solución con anticongelante o cloruro
de calcio) hasta ~75 %, con la válvula arriba (a las 12): más peso abajo = más tracción y centro de gravedad más bajo
(menos vuelcos). En una llanta grande caben más de 500 L (Trelleborg: 710/60R34 al 75 % ≈ 568 L ≈ 644 kg con CaCl2).
Error (segundo gancho): llenarla al tope: sin el colchón de aire la llanta queda rígida, no amortigua y castiga llanta,
rin y eje. Con hielo, el agua sola crece y puede botar la llanta del rin; el cloruro de calcio oxida el rin.
Comunidad: rancheros y campo. Inicio tipo 1 (caída desde el espacio): la Tierra de alambre → crash zoom a México →
la foto REAL de los campos de riego de Nuevo Casas Grandes, Chihuahua, desde la Estación Espacial (NASA, dominio
público) → el tractor que aterriza en el surco con «AGUA» de cristal detrás. El final regresa al espacio (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
El tractor es un esquema sin marca (sin logos). Datos y fuentes: guiones/2026-11-23_tractor.txt.
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
                    rec_frame, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import _B, texto, esquema, golpe_k, sacudir, K, camara, tubo
from vin import globo

M3 = M.M3
VIDRIO = (210, 214, 222)          # rayos X en blanco para que el agua azul se distinga del cristal


def draw_objects(fr, ms, xray=0.0, keep=(), xray_col=VIDRIO):
    return M.draw_objects(fr, ms, xray=xray, xray_col=xray_col, keep=keep)


TEMA = 'tractor'
TXT = ['Tu tractor trae las llantas… llenas de agua.',
       'No es una fuga:',
       'a muchos tractores les meten agua a propósito en las llantas de atrás.',
       'En una llanta grande caben más de 500 litros:',
       'más de media tonelada en cada una.',
       'Mira la prueba: el mismo tractor jalando el arado con puro aire…',
       'patina y se entierra.',
       'Con agua, ese peso aprieta la llanta contra la tierra, y agarra.',
       'Y en la ladera, el peso va abajo, pegado al suelo:',
       'así es más difícil que se voltee.',
       'Por dentro, la válvula se pone arriba, a las 12,',
       'y se llena hasta ahí: tres cuartas partes.',
       'Y aquí está el error: llenarla hasta el tope.',
       'Sin aire, la llanta se pone dura como piedra:',
       'no amortigua, rebota y castiga la llanta, el rin y el eje.',
       'Ese aire de arriba es el colchón.',
       'Y donde hiela, el agua sola se congela,',
       'crece y puede botar la llanta del rin.',
       'Por eso le echan anticongelante o cloruro de calcio…',
       'aunque el cloruro oxida el rin si no lo cuidas.',
       'Es física de rancho: más peso abajo, más agarre y menos vuelcos.',
       'Mándaselo a tu compa del rancho que jura que las llantas del tractor van con puro aire.',
       'Y dile que no… van llenas de agua.']
VOZ = ['Tu tractor trae las llantas... llenas de agua.',
       'No es una fuga:',
       'a muchos tractores les meten agua a propósito en las llantas de atrás.',
       'En una llanta grande caben más de quinientos litros:',
       'más de media tonelada en cada una.',
       'Mira la prueba: el mismo tractor jalando el arado con puro aire...',
       'patina y se entierra.',
       'Con agua, ese peso aprieta la llanta contra la tierra, y agarra.',
       'Y en la ladera, el peso va abajo, pegado al suelo:',
       'así es más difícil que se voltee.',
       'Por dentro, la válvula se pone arriba, a las doce,',
       'y se llena hasta ahí: tres cuartas partes.',
       'Y aquí está el error: llenarla hasta el tope.',
       'Sin aire, la llanta se pone dura como piedra:',
       'no amortigua, rebota y castiga la llanta, el rin y el eje.',
       'Ese aire de arriba es el colchón.',
       'Y donde hiela, el agua sola se congela,',
       'crece y puede botar la llanta del rin.',
       'Por eso le echan anticongelante o cloruro de calcio...',
       'aunque el cloruro oxida el rin si no lo cuidas.',
       'Es física de rancho: más peso abajo, más agarre y menos vuelcos.',
       'Mándaselo a tu compa del rancho que jura que las llantas del tractor van con puro aire.',
       'Y dile que no... van llenas de agua.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_tractor.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-23_tractor_words.json')
IMG = os.path.join(HERE, 'img', 'tractor')

AMARILLO = (255, 236, 160)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
ROJO = (255, 60, 45)
VERDE = (60, 210, 120)
ROJO_T = (196, 44, 32)            # el tractor de este reel es rojo (sin marca)
CREMA = (196, 184, 152)          # rines
HULE = (30, 30, 33)
AGUA = (60, 150, 255)
HIELO = (215, 238, 255)
OXIDO = (170, 82, 34)
TIERRA = (150, 108, 70)
CRED = 'FOTO: NASA · ESTACIÓN ESPACIAL · CHIHUAHUA, 2020'

# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    if not os.path.exists(WORDS):
        T, _ = montaje.cargar(TEMA)
        for i, f in enumerate(VOZ):
            ws = [w for w in f.split() if montaje._norm(w)]
            a, b = T[i] if T else (0, 2)
            L = np.cumsum([0] + [len(w) + 1 for w in ws])[:-1] / max(1, sum(len(w) + 1 for w in ws))
            _WT[i] = [float(x) * (b - a) for x in L]
        return _WT
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
        base = next((x for x in L if x is not None), 0.0)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wp(i, palabra, n=0):
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


_F = {}


def foto(nombre):
    if nombre not in _F:
        p = os.path.join(IMG, nombre)
        _F[nombre] = Image.open(p).convert('RGB') if os.path.exists(p) else None
    return _F[nombre]


def credito(img, txt=CRED, y=1470):
    texto(img, None, 540, y, txt, 20, (170, 170, 178), 1.0, f='mono', glow=0)


# ------------------------------------------------------------------ objetos
R_RIN, R_EXT, ANCHO = 0.57, 0.95, 0.62      # llanta trasera: radio del rin, radio exterior, ancho


def agua_mesh(nivel, r_in=R_RIN + 0.02, r_out=R_EXT - 0.04, w=ANCHO * 0.82, col=AGUA, n=64, glow=0.16):
    """Agua dentro de la llanta (eje en z, centro en el origen): el anillo entre r_in y r_out por debajo de y = nivel."""
    V, F = [], []
    prev = None
    for j in range(n + 1):
        th = 2 * math.pi * j / n
        s, c = math.sin(th), math.cos(th)
        rb = r_out if s <= 1e-6 else min(r_out, nivel / s)
        if rb <= r_in + 0.005:
            prev = None
            continue
        i0 = len(V)
        for r in (r_in, rb):
            for z in (-w / 2, w / 2):
                V.append((r * c, r * s, z))
        if prev is not None:
            a, b = prev, i0                                    # [rin,-z] [rin,+z] [rb,-z] [rb,+z]
            F += [(a + 1, a + 3, b + 3, b + 1), (a + 0, b + 0, b + 2, a + 2),
                  (a + 2, b + 2, b + 3, a + 3), (a + 0, a + 1, b + 1, b + 0)]
        prev = i0
    if not F:
        return None
    m = M3.Mesh(V, F, col, shadow=0, gloss=0.8, double=True)
    m = named(m, 'agua', rim=0.9, gloss=0.8)
    m.glow = M.scale_c(col, glow)
    return m


def llanta_t(giro=0.0, nivel=None, hielo=0.0, oxido=0.0, piedra=0.0, botada=0.0, agua_col=AGUA, s=1.0):
    """Llanta trasera de tractor (eje en z, centro en el origen): hule con taquetes en chevrón, rin crema con
    birlos y válvula. nivel = altura del agua (None = sin agua). botada: la ceja se zafa del rin (hielo)."""
    col = M.mixc(HULE, (120, 120, 124), piedra)
    rr = (R_EXT - R_RIN) / 2
    tire = M3.torus(R_RIN + rr, rr, col, nu=56, nv=14, gloss=0.25).tf(s=(1, 1, ANCHO / (2 * rr)))
    ms = [named(tire, 'llanta', rim=0.45, gloss=0.25)]
    for j in range(22):                                            # taquetes en chevrón
        ph = 360 * j / 22 + giro
        for sgn in (-1, 1):
            lug = M3.box(0.1, 0.07, ANCHO * 0.5, col, shadow=0, base=False, gloss=0.2).tf(ry=28 * sgn)
            lug = lug.tf(t=(0.04 * sgn, R_EXT - 0.02, ANCHO * 0.25 * sgn)).tf(rz=ph)
            ms.append(named(lug, 'llanta', rim=0.4))
    rc = M.mixc(CREMA, OXIDO, oxido)
    ms.append(named(M3.cyl(R_RIN, ANCHO * 0.7, rc, n=40, shadow=0, gloss=0.35, y0=-ANCHO * 0.35).tf(rx=90), 'rin', rim=0.5, gloss=0.35))
    ms.append(named(M3.cyl(0.2, ANCHO * 0.8, (70, 70, 74), n=20, shadow=0, gloss=0.7, y0=-ANCHO * 0.4).tf(rx=90), 'maza', rim=0.7))
    for j in range(8):
        a = math.radians(45 * j + giro)
        b = M3.cyl(0.03, 0.06, (200, 200, 206), n=8, shadow=0, gloss=0.9).tf(rx=90, t=(0.13 * math.cos(a), 0.13 * math.sin(a), ANCHO * 0.4))
        ms.append(named(b, 'maza', rim=0.9))
    if oxido > 0.05:                                               # manchas de óxido en el rin
        for j in range(7):
            a = math.radians(51 * j + 20 + giro)
            mm = M3.cyl(0.05 + 0.02 * (j % 3), 0.01, OXIDO, n=10, shadow=0).tf(rx=90, t=((R_RIN - 0.12) * math.cos(a),
                                                                                         (R_RIN - 0.12) * math.sin(a), ANCHO * 0.36))
            mm = named(mm, 'rin')
            mm.glow = M.scale_c((255, 120, 40), 0.25 * oxido)
            ms.append(mm)
    va = math.radians(90 + giro)                                   # válvula (a las 12 cuando giro = 0)
    v = M3.cyl(0.03, 0.16, (40, 40, 44), n=8, shadow=0).tf(rz=-90 + giro, t=(R_RIN * math.cos(va), R_RIN * math.sin(va) - 0.0, ANCHO * 0.3))
    ms.append(named(v, 'valvula', rim=0.7))
    if nivel is not None:
        ac = M.mixc(agua_col, HIELO, hielo)
        w = agua_mesh(nivel, col=ac, glow=0.16 * (1 - hielo) + 0.2 * hielo)
        if w is not None:
            if hielo > 0.01:
                w = w.tf(s=1 + 0.05 * hielo)
                w = named(w, 'agua', rim=0.9, gloss=0.9)
                w.glow = M.scale_c(ac, 0.3)
            ms.append(w)
    if botada > 0.01:
        ms = [m.tf(t=(0.0, 0.0, 0.18 * botada)) if getattr(m, 'name', '') == 'llanta' else m for m in ms]
    return P.tfk(ms, s=s)


def llanta_d(giro=0.0):
    """Llanta delantera (chica, con costillas)."""
    R, r, w = 0.48, 0.13, 0.3
    ms = [named(M3.torus(R - r, r, HULE, nu=40, nv=10, gloss=0.25).tf(s=(1, 1, w / (2 * r))), 'llantad', rim=0.45)]
    for dz in (-0.08, 0.0, 0.08):
        ms.append(named(M3.torus(R - 0.005, 0.018, (14, 14, 16), nu=40, nv=5).tf(t=(0, 0, dz)), 'llantad'))
    ms.append(named(M3.cyl(R - 2 * r, w * 0.8, CREMA, n=28, shadow=0, gloss=0.6, y0=-w * 0.4).tf(rx=90), 'rind', rim=0.7))
    ms.append(named(M3.cyl(0.08, w, (70, 70, 74), n=14, shadow=0, gloss=0.7, y0=-w / 2).tf(rx=90), 'rind', rim=0.7))
    return P.tfk(ms, rz=giro)


XR, XF, ZR, ZF = -0.85, 1.25, 0.9, 0.72     # ejes trasero y delantero, y medias vías


def tractor(giro=0.0, nivel=None, hielo=0.0, oxido=0.0, piedra=0.0, botada=0.0, col=ROJO_T, humo=0.0, arado=False,
            hund=0.0, agua_col=AGUA):
    """Tractor agrícola sin marca (frente hacia +x): llantas traseras grandes con taquetes, delanteras chicas, cofre
    largo, salpicaderas, asiento, volante, barra antivuelco (ROPS), escape vertical y enganche de 3 puntos."""
    ms = []
    yr = R_EXT - hund
    for zs in (-1, 1):
        ms += P.tfk(llanta_t(giro=giro if zs > 0 else -giro, nivel=nivel, hielo=hielo, oxido=oxido, piedra=piedra,
                             botada=botada, agua_col=agua_col), ry=0 if zs > 0 else 180, t=(XR, yr, ZR * zs))
        ms += P.tfk(llanta_d(giro=-giro * R_EXT / 0.48), t=(XF, 0.48 - hund * 0.3, ZF * zs))
    y0 = 0.55 - hund
    _B(ms, 1.7, 0.55, 0.56, col, 0.55, y0 + 0.25, 0, name='cofre', gloss=0.7, rim=0.8)            # cofre
    _B(ms, 0.08, 0.5, 0.5, (28, 28, 30), 1.42, y0 + 0.28, 0, name='parrilla', gloss=0.4)          # parrilla
    for j in range(5):
        _B(ms, 0.02, 0.4, 0.46, (90, 90, 96), 1.47, y0 + 0.33 + 0.0 * j, -0.2 + 0.1 * j, name='parrilla', gloss=0.8)
    _B(ms, 1.0, 0.3, 0.6, (60, 60, 64), 0.4, y0 - 0.05, 0, name='motor', gloss=0.5)              # bloque abajo
    _B(ms, 0.8, 0.5, 0.9, col, XR + 0.15, y0 + 0.1, 0, name='cuerpo', gloss=0.6, rim=0.7)        # caja / diferencial
    for zs in (-1, 1):                                                                             # salpicaderas
        _B(ms, 1.25, 0.08, 0.62, col, XR, yr + R_EXT + 0.05, ZR * zs, name='salpicadera', gloss=0.7, rim=0.8)
        _B(ms, 1.25, 0.55, 0.06, col, XR, yr + R_EXT - 0.48, (ZR - 0.33) * zs, name='salpicadera', gloss=0.6, rim=0.7)
    _B(ms, 0.36, 0.08, 0.42, (24, 24, 26), XR + 0.05, yr + 0.55, 0, name='asiento', gloss=0.3)    # asiento
    _B(ms, 0.08, 0.36, 0.42, (24, 24, 26), XR - 0.13, yr + 0.6, 0, name='asiento', gloss=0.3)
    ms.append(tubo((XR + 0.75, yr + 0.25, 0), (XR + 0.55, yr + 0.75, 0), r=0.025, col=(40, 40, 44), name='volante'))
    ms.append(named(M3.torus(0.16, 0.02, (30, 30, 32), nu=20, nv=5).tf(rz=60, t=(XR + 0.55, yr + 0.78, 0)), 'volante'))
    for zs in (-1, 1):                                                                             # barra antivuelco
        ms.append(tubo((XR - 0.3, yr + 0.5, 0.55 * zs), (XR - 0.3, yr + 1.55, 0.55 * zs), r=0.045, col=(46, 46, 50), name='rops'))
    ms.append(tubo((XR - 0.3, yr + 1.55, -0.55), (XR - 0.3, yr + 1.55, 0.55), r=0.045, col=(46, 46, 50), name='rops'))
    ms.append(named(M3.cyl(0.05, 1.0, (50, 50, 54), n=12, shadow=0, gloss=0.6, y0=0).tf(t=(1.05, y0 + 0.5, 0.18)), 'escape', rim=0.6))
    ms.append(named(M3.cyl(0.065, 0.08, (30, 30, 32), n=12, shadow=0).tf(t=(1.05, y0 + 1.5, 0.18)), 'escape'))
    ms.append(tubo((XR - 0.25, y0 + 0.2, -0.3), (XR - 0.75, y0 + 0.05, -0.3), r=0.04, col=(60, 60, 64), name='enganche'))
    ms.append(tubo((XR - 0.25, y0 + 0.2, 0.3), (XR - 0.75, y0 + 0.05, 0.3), r=0.04, col=(60, 60, 64), name='enganche'))
    if arado:
        for j in range(3):                                                                         # arado de discos
            x, z = XR - 1.0 - 0.35 * j, -0.35 + 0.35 * j
            ms.append(tubo((XR - 0.75, y0 + 0.05, z), (x, 0.45 - hund, z), r=0.035, col=(70, 70, 74), name='arado'))
            dd = M3.cyl(0.32, 0.03, (190, 192, 198), n=24, shadow=0, gloss=0.9).tf(rx=70, rz=20, t=(x, 0.3 - hund * 0.5, z))
            ms.append(named(dd, 'arado', rim=0.9, gloss=0.9))
    return ms


def surcos(fr, t, a=1.0, mov=0.0, x0=-7, x1=7, z0=-4.0, z1=4.0, rz=0.0, col=TIERRA):
    """Campo arado en line-art: surcos a lo largo de x (se mueven con mov)."""
    ca, sa = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    for j, z in enumerate(np.arange(z0, z1, 0.32)):
        off = (mov % 1.0) * 0.0
        pts = [(x * ca, x * sa, z) for x in (x0, x1)]
        line3(fr, pts, col=col, w=2.0, a=a * (0.35 + 0.3 * (j % 2)), glow=0.2)
    for j in range(int(x1 - x0) * 2):                                   # terrones que pasan
        x = x0 + ((j * 0.5 - mov) % (x1 - x0))
        dot3(fr, (x * ca, x * sa + 0.02, -3.6 + (j * 1.37) % 7.2), r=3, col=col, a=0.5 * a, glow=0.1)


def polvo(fr, t, p, k=1.0, n=18, seed=1, col=(190, 150, 110), sentido=-1):
    if k <= 0.01:
        return
    for j in range(n):
        ph = (t * 1.6 + j / n) % 1.0
        rng = np.random.RandomState(j + seed)
        dx = sentido * (0.2 + 1.4 * ph) * (0.6 + 0.6 * rng.rand())
        dy = 0.15 + 0.9 * ph * rng.rand() - 0.3 * ph * ph
        dz = (rng.rand() - 0.5) * 0.9 * ph
        dot3(fr, (p[0] + dx, p[1] + dy, p[2] + dz), r=int(4 + 10 * ph), col=col, a=k * (1 - ph) * 0.7, glow=0.15)


def cg(fr, p, col, k=1.0, r=14):
    if k > 0.01:
        dot3(fr, p, r=r, col=col, a=k, glow=1.8)


def flechas_abajo(img, fx, x, y, t, k=1.0, n=3, col=AGUA):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    for j in range(n):
        xx = x + (j - (n - 1) / 2) * 70
        yy = y + 18 * math.sin(t * 6 + j)
        d.line([(xx, yy - 60), (xx, yy + 30)], fill=M.scale_c(col, k), width=8)
        d.polygon([(xx - 22, yy + 20), (xx + 22, yy + 20), (xx, yy + 52)], fill=M.scale_c(col, k))
        df.line([(xx, yy - 60), (xx, yy + 40)], fill=M.scale_c(col, 0.5 * k), width=18)


def bascula(img, fx, cx, cy, kg, k=1.0):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.rounded_rectangle((cx - 300, cy, cx + 300, cy + 70), radius=12, fill=(40, 42, 48), outline=(200, 200, 206), width=3)
    d.rounded_rectangle((cx - 150, cy + 90, cx + 150, cy + 190), radius=12, fill=(10, 12, 14), outline=CYAN, width=3)
    df.rounded_rectangle((cx - 150, cy + 90, cx + 150, cy + 190), radius=12, outline=M.scale_c(CYAN, 0.5), width=10)
    texto(img, fx, cx, cy + 140, f'+{kg:,} kg'.replace(',', ' '), 54, CYAN, k, f='mono', glow=0.6)


def pastel(img, fx, cx, cy, R, frac, k=1.0, col=AGUA, txt=''):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c(WHITE, 0.7 * k), width=5)
    if frac > 0.001:
        d.pieslice((cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10), 90 - 360 * frac / 2 + 0, 90 + 360 * frac / 2,
                   fill=M.scale_c(col, 0.85 * k))
        df.pieslice((cx - R, cy - R, cx + R, cy + R), 90 - 180 * frac, 90 + 180 * frac, fill=M.scale_c(col, 0.35 * k))
    if txt:
        texto(img, fx, cx, cy, txt, int(R * 0.42), WHITE, k, f='sansx', glow=0.4)


def esquema_p(img, fx, k=1.0, y=1440, txt='ESQUEMA · TRACTOR SIN MARCA'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


# ================================================================== escenas
# 0. gancho (inicio 1: caída desde el espacio). Pre-roll (y loop): la Tierra de alambre gira, crash zoom a México,
#    la foto REAL de los campos de Chihuahua crece, y el tractor aterriza en el surco con «AGUA» de cristal detrás.
U_ATERRIZA = -0.55


def _espacio(t, fi, u):
    k = seg(u, -2.1, -1.35)
    fr = Frame(Cam(target=(0, 1.2, 0), dist=lerp(5.6, 1.9, P.eout4(k)), yaw=0, pitch=6, cy=0.5))
    space(fr, t, floor=None, bokeh=1.0)
    spin = math.radians(-150 + 40 * clamp((u + 4.5) / 3.0) + 70 * P.eout4(k))
    globo(fr, t, np.array([0, 1.2, 0]), 1.4, spin, marcas=[(-106.4, 30.4, AMARILLO, 1.0)])

    def ui(img, fx):
        kicker(img, 'DESDE EL ESPACIO · CHIHUAHUA, MÉXICO', 150, 1.0, col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


def _foto(t, fi, u):
    fr = Frame(Cam(target=(0, 0, 0), dist=6, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    out = finish(fr, fi)
    im = foto('campos.jpg')
    if im is None:
        return out
    img = Image.fromarray(out)
    z = 1.0 + 1.6 * P.eout4(seg(u, -1.35, U_ATERRIZA))
    W0 = 1080
    H0 = int(W0 * im.size[1] / im.size[0])
    ph = im.resize((int(W0 * z), int(H0 * z)), Image.BILINEAR)
    cx, cy = ph.size[0] // 2 + int(80 * (z - 1)), ph.size[1] // 2 + int(40 * (z - 1))
    ph = ph.crop((cx - W0 // 2, cy - min(H0, 1920) // 2, cx + W0 // 2, cy + min(H0, 1920) // 2))
    img.paste(ph, (0, 960 - ph.size[1] // 2))
    fx = Image.new('RGB', img.size, (0, 0, 0))
    kicker(img, 'FOTO REAL · CAMPOS DE RIEGO DE CHIHUAHUA', 150, 1.0, col=AZULC)
    credito(img, y=960 + ph.size[1] // 2 + 30)
    return np.asarray(img)


def _tractor_gancho(t, fi, u):
    ua = Wp(0, 'agua') - 0.15
    fr = Frame(camara(u, [K(U_ATERRIZA, 4.0, 70, 40, tx=0.0, ty=0.6), K(U_ATERRIZA + 0.45, 7.4, 44, 12, tx=0.1, ty=0.9),
                          K(ua, 6.8, 34, 9, tx=0.0, ty=0.9), K(4.0, 6.6, 30, 9, tx=0.0, ty=0.9)], cy=0.64))
    space(fr, t, floor='lines', floor_a=0.4, bokeh=0.9, beam=0.5)
    surcos(fr, t, a=1.0)
    M.cristal(fr.base, fr.fx, 'AGUA', u, t0=-0.75, cy=0.42, entrada='golpe')
    e = P.entrada(u, U_ATERRIZA - 0.05, 0.4, 'cae')
    xr = seg(u, ua, ua + 0.35)
    draw_objects(fr, P.tfk(tractor(nivel=0.5 if xr > 0.01 else None), t=(0, max(0.0, -e['dy']) * 1.2, 0)), xray=xr,
                 keep=('agua', 'rin', 'maza', 'valvula', 'llantad', 'rind', 'cofre', 'parrilla', 'salpicadera', 'cuerpo', 'motor',
                       'asiento', 'volante', 'rops', 'escape', 'enganche'))
    polvo(fr, t, (XR, 0.05, ZR), k=1 - seg(u, U_ATERRIZA + 0.6, U_ATERRIZA + 1.4), seed=3)

    def ui(img, fx):
        kicker(img, 'RANCHEROS · LO QUE NO VES', 150, seg(u, U_ATERRIZA + 0.1, U_ATERRIZA + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu tractor trae las llantas…', 'sans'), ('llenas de agua.', 'serif')], 240,
                       seg(u, -0.05, 0.1), size=70)
        esquema_p(img, fx, seg(u, 0.4, 0.7), y=1420)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, U_ATERRIZA + 0.3, 0.4), amp=26)


def s_gancho(t, fi, u, d):
    if u < -1.35:
        return _espacio(t, fi, u)
    if u < -1.15:
        return M.tr_zoom_through(_espacio(t, fi, u), _foto(t, fi, u), seg(u, -1.35, -1.15), 0.5, 0.5)
    if u < U_ATERRIZA:
        return _foto(t, fi, u)
    if u < U_ATERRIZA + 0.25:
        return M.tr_zoom_through(_foto(t, fi, u), _tractor_gancho(t, fi, u), seg(u, U_ATERRIZA, U_ATERRIZA + 0.25), 0.55, 0.5)
    return _tractor_gancho(t, fi, u)


# 1. no es una fuga: la llanta de cerca, una gota en la válvula y «¿FUGA?» que se tacha
def s_fuga(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.4, 80, 10, ty=0.95), K(0.35, 2.9, 30, 6, ty=0.95), K(d, 2.8, 24, 6, ty=0.95)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.9, beam=0.4)
    surcos(fr, t, a=0.6)
    draw_objects(fr, P.tfk(llanta_t(), t=(0, R_EXT, 0)))
    vx, vy, _ = fr.cam.p1((0, R_EXT + R_RIN, ANCHO * 0.3))

    def ui(img, fx):
        kicker(img, 'LLANTA TRASERA', 150, seg(u, -0.1, 0.2), col=AZULC)
        ph = (u * 1.5) % 1.0
        dd = ImageDraw.Draw(img)
        dd.ellipse((vx - 12, vy + 20 + 120 * ph - 12, vx + 12, vy + 20 + 120 * ph + 16), fill=AGUA)
        P.pill_tachada(img, fx, 540, 420, '¿FUGA?', seg(u, -0.2, 0.0), seg(u, 0.35, 0.7), t, size=60)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. a propósito en las de atrás: la manguera entra por la válvula y el agua sube dentro de la llanta (rayos X)
def s_llenan(t, fi, u, d):
    ua = Wp(2, 'atras') - 0.2
    lv = -R_EXT + (0.5 + R_EXT) * P.eout4(seg(u, 0.2, d - 0.3))
    fr = Frame(camara(u, [K(-0.3, 3.2, 20, 8, ty=0.95), K(0.4, 3.4, 8, 6, ty=0.95), K(ua - 0.1, 3.3, 4, 6, ty=0.95), K(ua, 7.0, 40, 14, tx=-0.4, ty=0.9),
                          K(d, 6.8, 36, 14, tx=-0.4, ty=0.9)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.9)
    if u < ua:
        draw_objects(fr, P.tfk(llanta_t(nivel=lv), t=(0, R_EXT, 0)), xray=1.0, keep=('agua', 'rin', 'maza', 'valvula'))
        p0 = (0, R_EXT + R_RIN + 0.1, ANCHO * 0.3)
        line3(fr, [p0, (0.3, R_EXT + 1.6, 0.6), (1.2, R_EXT + 2.0, 0.6)], col=(60, 200, 90), w=10, a=1.0, glow=0.3)
        for j in range(5):
            ph = (t * 2 + j / 5) % 1.0
            dot3(fr, (0.3 * (1 - ph), R_EXT + 1.6 - 0.5 * ph, 0.6 - 0.3 * ph), r=6, col=AGUA, a=0.9, glow=1.0)
    else:
        draw_objects(fr, tractor(nivel=0.5), xray=1.0, keep=('agua', 'rin', 'maza', 'valvula'))

    def ui(img, fx):
        kicker(img, 'RAYOS X · LASTRE LÍQUIDO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1380, 'SOLO LAS DE ATRÁS', eout(seg(u, ua + 0.1, ua + 0.4)), size=30, border=AGUA, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. más de 500 litros: cubetas que caen en fila y el contador que se clava; «500 L» de cristal
def s_litros(t, fi, u, d):
    u5 = Wp(3, 'quinientos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, -40, 10, ty=0.95), K(0.4, 4.3, -14, 6, ty=0.95), K(d, 4.2, -10, 6, ty=0.95)], cy=0.4))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9, beam=0.5)
    M.cristal(fr.base, fr.fx, '500 L', u, t0=u5 - 0.2, cy=0.4, entrada='zoom')
    draw_objects(fr, P.tfk(llanta_t(nivel=0.5, giro=10 * math.sin(t)), t=(0, R_EXT, 0)), xray=0.85, keep=('agua', 'rin', 'maza', 'valvula'))
    n = int(500 * P.eout4(seg(u, 0.0, u5 + 0.3)))

    def ui(img, fx):
        kicker(img, 'LLANTA GRANDE DE TRACTOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        dd = ImageDraw.Draw(img)
        nb = int(20 * P.eout4(seg(u, 0.0, u5 + 0.3)))
        for j in range(nb):                                                     # cubetas de 20 L
            x = 120 + (j % 10) * 94
            y = 1330 + (j // 10) * 96
            dd.polygon([(x - 30, y - 34), (x + 30, y - 34), (x + 22, y + 30), (x - 22, y + 30)], fill=(40, 120, 220), outline=(200, 230, 255))
        P.numero_golpe(img, fx, f'{n} L', 1180, 1.0 if u > u5 + 0.3 else 0.99, size=130, col=WHITE)
        texto(img, fx, 540, 1540, '1 CUBETA = 20 L · 25 CUBETAS', 26, GRIS, seg(u, u5 + 0.3, u5 + 0.5), f='mono', glow=0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u5 + 0.3, 0.3), amp=16)


# 4. más de media tonelada en cada una: la llanta cae en la báscula
def s_tonelada(t, fi, u, d):
    ut = Wp(4, 'tonelada') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, 30, 12, ty=0.9), K(0.4, 4.2, 10, 8, ty=0.9), K(d, 4.1, 6, 8, ty=0.9)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.6)
    M.cristal(fr.base, fr.fx, '½ TON', u, t0=ut - 0.15, cy=0.3, entrada='golpe')
    e = P.entrada(u, -0.15, 0.35, 'cae')
    draw_objects(fr, P.tfk(llanta_t(nivel=0.5), t=(0, R_EXT + 0.15 + max(0.0, -e['dy']), 0)), xray=0.6, keep=('agua', 'rin', 'maza', 'valvula'))
    kg = int(500 * P.eout4(seg(u, 0.25, ut + 0.3)))

    def ui(img, fx):
        kicker(img, 'SOLO DEL AGUA, SIN CONTAR LA LLANTA', 150, seg(u, -0.1, 0.2), col=AZULC)
        bascula(img, fx, 540, 1250, kg, k=1.0)
        texto(img, fx, 540, 1500, 'CADA LLANTA', 34, GRIS, seg(u, ut + 0.2, ut + 0.4), f='mono', glow=0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.4), amp=24)


# 5. prueba: el mismo tractor con el arado y puro aire (llantas vacías)
def s_aire(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.0, 120, 18, tx=-0.8, ty=0.8), K(0.4, 6.2, 60, 12, tx=-0.8, ty=0.8), K(d, 6.0, 54, 12, tx=-0.8, ty=0.8)], cy=0.6))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    surcos(fr, t, a=1.0, mov=t * 0.3)
    draw_objects(fr, tractor(giro=-t * 160, arado=True))
    polvo(fr, t, (XR - 0.6, 0.1, ZR), k=0.7, seed=5)

    def ui(img, fx):
        kicker(img, 'PRUEBA · CASO 1: PURO AIRE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1380, 'ARADO DE DISCOS', eout(seg(u, 0.5, 0.8)), size=28, border=AMARILLO, dot=False)
        esquema_p(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. patina y se entierra: las llantas giran en su lugar, escarban y el tractor se hunde
def s_patina(t, fi, u, d):
    hund = 0.22 * P.eout4(seg(u, 0.3, d))
    fr = Frame(camara(u, [K(-0.3, 5.2, 90, 14, tx=XR, ty=0.6, tz=0.6), K(0.4, 4.4, 52, 8, tx=XR, ty=0.5, tz=0.6),
                          K(d, 4.3, 46, 8, tx=XR, ty=0.5, tz=0.6)], cy=0.6))
    space(fr, t, floor=None, bokeh=0.8)
    surcos(fr, t, a=1.0)
    draw_objects(fr, tractor(giro=-t * 700, arado=True, hund=hund))
    polvo(fr, t * 2.2, (XR - 0.5, 0.05, ZR), k=1.0, n=28, seed=7)
    polvo(fr, t * 2.0, (XR - 0.5, 0.05, -ZR), k=0.8, n=20, seed=9)

    def ui(img, fx):
        kicker(img, 'CASO 1 · SIN PESO EXTRA', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        texto(img, fx, 540, 420, 'PATINA', 110, ROJO, P.resorte(seg(u, 0.0, 0.25)), f='sansx', glow=0.5)
        texto(img, fx, 540, 1350, f'SE HUNDE {int(hund * 100)} cm', 44, ROJO, seg(u, 0.6, 0.8), f='mono', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.35, amp=8)


# 7. con agua: el mismo tractor (rayos X con agua), flechas de peso hacia abajo y avanza jalando el arado
def s_agarra(t, fi, u, d):
    ug = Wp(7, 'agarra') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.4, 60, 12, tx=-1.0, ty=0.8), K(0.4, 7.0, 40, 10, tx=-1.0, ty=0.8), K(d, 6.8, 36, 10, tx=-1.0, ty=0.8)], cy=0.6))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    mov = t * 0.9 if u > ug else 0
    surcos(fr, t, a=1.0, mov=mov)
    draw_objects(fr, tractor(giro=-t * 160, nivel=0.5, arado=True), xray=0.75,
                 keep=('agua', 'rin', 'maza', 'valvula', 'cofre', 'parrilla', 'cuerpo', 'salpicadera', 'rops', 'escape', 'arado', 'enganche', 'llantad', 'rind'))
    px, py, _ = fr.cam.p1((XR, R_EXT * 2.0, ZR))

    def ui(img, fx):
        kicker(img, 'CASO 2 · CON AGUA', 150, seg(u, -0.1, 0.2), col=AZULC)
        flechas_abajo(img, fx, px, py - 80, t, k=seg(u, 0.2, 0.5))
        texto(img, fx, 540, 420, 'AGARRA', 110, VERDE, P.resorte(seg(u, ug, ug + 0.25)), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. en la ladera: el tractor de lado en la pendiente; el centro de gravedad baja con el agua
def s_ladera(t, fi, u, d):
    ub = Wp(8, 'abajo') - 0.1
    inc = 20
    fr = Frame(camara(u, [K(-0.3, 7.6, 110, 12, tx=-0.2, ty=0.8), K(0.4, 6.2, 64, 9, tx=-0.2, ty=0.8), K(d, 6.0, 58, 9, tx=-0.2, ty=0.8)], cy=0.56))
    space(fr, t, floor=None, bokeh=0.8, beam=0.4)
    for j in range(9):                                                       # la ladera (line-art inclinado en z)
        x = -4 + j
        line3(fr, [(x, -2.4 * math.sin(math.radians(inc)), -2.4), (x, 2.4 * math.sin(math.radians(inc)), 2.4)], col=TIERRA, w=2, a=0.5, glow=0.2)
    line3(fr, [(-5, -0.6, -2.2), (3, -0.6, -2.2)], col=TIERRA, w=1, a=0.0)
    ms = P.tfk(tractor(), rx=-inc)
    draw_objects(fr, ms)
    ka = seg(u, ub - 0.2, ub + 0.4)
    hcg = lerp(1.15, 0.78, P.eout4(ka))
    c = np.array([XR + 0.6, hcg, 0.0])
    a = math.radians(-inc)
    cr = np.array([c[0], c[1] * math.cos(a) - c[2] * math.sin(a), c[1] * math.sin(a) + c[2] * math.cos(a)])
    cg(fr, cr, M.mixc(ROJO, VERDE, ka), k=1.0)
    line3(fr, [cr, (cr[0], -0.4, cr[2])], col=M.mixc(ROJO, VERDE, ka), w=3, a=0.9, glow=0.8)

    def ui(img, fx):
        kicker(img, 'CENTRO DE GRAVEDAD', 150, seg(u, -0.1, 0.2), col=AZULC)
        x, y, _ = fr.cam.p1(tuple(cr))
        pill(img, fx, x + 220, y - 40, 'MÁS ABAJO' if ka > 0.5 else 'ALTO', 1.0, size=28, border=M.mixc(ROJO, VERDE, ka))
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. más difícil que se voltee: dos casos lado a lado (sin agua se pasa de la orilla; con agua se queda)
def s_voltea(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 0, 6, ty=1.2), K(0.4, 4.6, 0, 6, ty=1.2), K(d, 4.5, 0, 6, ty=1.2)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    k = P.eout4(seg(u, 0.1, 0.9))

    def ui(img, fx):
        kicker(img, 'DOS CASOS EN LA MISMA LADERA · DE FRENTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        for j, (cx, hc, col, txt, agua) in enumerate(((275, 430, ROJO, 'SIN AGUA', False), (805, 215, VERDE, 'CON AGUA', True))):
            base_y = 1120
            ang = math.radians(20 * k)

            def R(px, py):
                dx, dy = px - cx, py - base_y
                return (cx + dx * math.cos(ang) + dy * math.sin(ang), base_y - dx * math.sin(ang) + dy * math.cos(ang))
            d_.polygon([(cx - 270, base_y + 98), (cx + 270, base_y - 98), (cx + 270, base_y + 260), (cx - 270, base_y + 260)],
                       fill=(46, 34, 24))
            d_.line([(cx - 270, base_y + 98), (cx + 270, base_y - 98)], fill=(170, 124, 80), width=6)
            body = [R(cx - 95, base_y - 90), R(cx + 95, base_y - 90), R(cx + 85, base_y - 330), R(cx - 85, base_y - 330)]
            d_.polygon(body, fill=ROJO_T, outline=(240, 200, 190))
            rops = [R(cx - 110, base_y - 300), R(cx - 110, base_y - 470), R(cx + 110, base_y - 470), R(cx + 110, base_y - 300)]
            d_.line(rops, fill=(200, 200, 206), width=10)
            for sx in (-165, 165):
                c = R(cx + sx, base_y - 110)
                d_.rounded_rectangle((c[0] - 55, c[1] - 110, c[0] + 55, c[1] + 110), radius=30, fill=(26, 26, 28), outline=(220, 220, 226), width=4)
                if agua:
                    d_.rounded_rectangle((c[0] - 45, c[1] - 40, c[0] + 45, c[1] + 100), radius=22, fill=AGUA)
            g = R(cx, base_y - hc)
            d_.line([g, (g[0], base_y + 200)], fill=M.scale_c(col, 0.9), width=4)
            d_.ellipse((g[0] - 22, g[1] - 22, g[0] + 22, g[1] + 22), fill=col, outline=WHITE, width=3)
            df.ellipse((g[0] - 36, g[1] - 36, g[0] + 36, g[1] + 36), fill=M.scale_c(col, 0.6))
            texto(img, fx, cx, 520, txt, 44, col, 1.0, f='sansx', glow=0.3)
            fin = '¡SE VOLTEA!' if j == 0 else 'SE QUEDA'
            texto(img, fx, cx, 1460, fin, 44, col, seg(u, 0.9, 1.1), f='sansx', glow=0.4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. por dentro, la válvula arriba, a las 12: la llanta gira hasta que la válvula queda arriba (reloj y zoom REC)
def s_valvula(t, fi, u, d):
    u12 = Wp(10, 'doce') - 0.1
    g = -140 * (1 - P.eout4(seg(u, 0.1, u12)))
    fr = Frame(camara(u, [K(-0.3, 3.4, 0, 4, ty=R_EXT), K(0.4, 3.2, 0, 4, ty=R_EXT), K(u12, 2.4, 0, 4, ty=R_EXT + 0.35),
                          K(d, 2.3, 0, 4, ty=R_EXT + 0.35)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8)
    draw_objects(fr, P.tfk(llanta_t(giro=g), t=(0, R_EXT, 0)), xray=0.7, keep=('rin', 'maza', 'valvula'))
    cx, cy, _ = fr.cam.p1((0, R_EXT, 0))

    def ui(img, fx):
        kicker(img, 'ZOOM · LA VÁLVULA', 150, seg(u, -0.1, 0.2), col=AZULC)
        d_ = ImageDraw.Draw(img)
        for j in range(12):
            a = math.radians(j * 30 - 90)
            r0, r1 = 360, 390
            d_.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], fill=(200, 200, 206), width=4)
        texto(img, fx, cx, cy - 440, '12', 64, AMARILLO, seg(u, u12 - 0.1, u12 + 0.15), f='mono', glow=0.5)
        rec_frame(img, t, k=1.0, zoom_label='x1.0' if u < u12 else 'x1.6')
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. y se llena hasta ahí: 3/4 partes: el agua sube hasta la válvula y el pastel marca 75 %; «75 %» de cristal
def s_tresc(t, fi, u, d):
    ut = Wp(11, 'tres') - 0.15
    lv = -R_EXT + (0.5 + R_EXT) * P.eout4(seg(u, 0.0, ut + 0.2))
    fr = Frame(camara(u, [K(-0.3, 3.0, 20, 6, ty=R_EXT), K(0.4, 3.3, -10, 6, ty=R_EXT), K(d, 3.2, -14, 6, ty=R_EXT)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '75 %', u, t0=ut - 0.1, cy=0.3, entrada='zoom')
    draw_objects(fr, P.tfk(llanta_t(nivel=lv), t=(0, R_EXT, 0)), xray=1.0, keep=('agua', 'rin', 'maza', 'valvula'))
    lx, ly, _ = fr.cam.p1((0.95, R_EXT + 0.5, 0.35))

    def ui(img, fx):
        kicker(img, 'HASTA LA VÁLVULA', 150, seg(u, -0.1, 0.2), col=AZULC)
        d_ = ImageDraw.Draw(img)
        if lv > 0.3:
            d_.line([(80, ly), (1000, ly)], fill=M.scale_c(AMARILLO, 0.8), width=3)
        pastel(img, fx, 860, 1300, 120, 0.75 * P.eout4(seg(u, 0.0, ut + 0.2)), k=seg(u, 0.0, 0.2), txt='')
        texto(img, fx, 860, 1300, f'{int(75 * P.eout4(seg(u, 0.0, ut + 0.2)))}%', 56, WHITE, seg(u, 0.0, 0.2), f='sansx', glow=0.4)
        pill(img, fx, 330, 1300, 'ARRIBA: AIRE', eout(seg(u, ut + 0.3, ut + 0.6)), size=28, border=WHITE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 12. el error (segundo gancho): llenarla hasta el tope: el agua sigue subiendo y todo se pone rojo; «TOPE»
def s_tope(t, fi, u, d):
    ut = Wp(12, 'tope') - 0.15
    lv = 0.5 + (R_EXT - 0.5) * P.eout4(seg(u, 0.3, ut + 0.2))
    rojo = seg(u, ut, ut + 0.3)
    fr = Frame(camara(u, [K(-0.3, 2.4, -30, 8, ty=R_EXT), K(0.35, 3.0, 0, 6, ty=R_EXT), K(d, 2.9, 4, 6, ty=R_EXT)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'TOPE', u, t0=ut - 0.1, cy=0.3, entrada='golpe')
    draw_objects(fr, P.tfk(llanta_t(nivel=lv, agua_col=M.mixc(AGUA, (255, 70, 60), rojo)), t=(0, R_EXT, 0)), xray=1.0,
                 keep=('agua', 'rin', 'maza', 'valvula'))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, -0.1, 0.1), col=(255, 120, 110))
        P.titulo_golpe(img, fx, [('El error:', 'sans'), ('llenarla al 100 %.', 'serif')], 1250, seg(u, ut, ut + 0.15), size=78, col=WHITE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut + 0.15, 0.35), amp=24)


# 13. sin aire, dura como piedra: la llanta llena se vuelve gris piedra; un golpe y no se aplasta nada
def s_piedra(t, fi, u, d):
    up = Wp(13, 'piedra') - 0.15
    pk = seg(u, up, up + 0.3)
    fr = Frame(camara(u, [K(-0.3, 3.6, 40, 8, ty=R_EXT), K(0.4, 3.2, 14, 6, ty=R_EXT), K(d, 3.1, 10, 6, ty=R_EXT)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8)
    draw_objects(fr, P.tfk(llanta_t(nivel=R_EXT if pk < 0.95 else None, piedra=pk), t=(0, R_EXT, 0)), xray=0.7 * (1 - pk), keep=('agua', 'rin', 'maza', 'valvula'))

    def ui(img, fx):
        kicker(img, '100 % AGUA · 0 % AIRE', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        pill(img, fx, 540, 1380, 'DURA COMO PIEDRA', eout(seg(u, up + 0.1, up + 0.4)), size=36, border=ROJO, dot=False)
        texto(img, fx, 540, 420, 'SIN AIRE', 100, ROJO, P.resorte(seg(u, -0.15, 0.1)), f='sansx', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.2, 0.3), amp=20)


# 14. no amortigua, rebota y castiga llanta, rin y eje: el tractor pasa un bordo y brinca; garabatos rojos
def s_rebota(t, fi, u, d):
    ph = (u * 1.6) % 1.0
    brinco = 0.35 * abs(math.sin(math.pi * ph)) * (1 if u > 0.1 else 0)
    fr = Frame(camara(u, [K(-0.3, 7.0, 70, 10, tx=-0.3, ty=0.9), K(0.4, 6.4, 46, 8, tx=-0.3, ty=0.9), K(d, 6.2, 42, 8, tx=-0.3, ty=0.9)], cy=0.58))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    surcos(fr, t, a=1.0, mov=t * 0.8)
    draw_objects(fr, P.tfk(tractor(giro=-t * 200, piedra=0.6), t=(0, brinco, 0), rz=6 * math.sin(math.pi * ph) * (1 if u > 0.1 else 0)),
                 xray=0.0)
    pts = [fr.cam.p1((XR, R_EXT * 1.7 + brinco, ZR + 0.3)), fr.cam.p1((XR, R_EXT + brinco, ZR + 0.35)), fr.cam.p1((XR + 0.3, R_EXT + brinco, 0))]
    us = [Wp(14, 'llanta') - 0.1, Wp(14, 'rin') - 0.1, Wp(14, 'eje') - 0.1]

    def ui(img, fx):
        kicker(img, 'SIN COLCHÓN DE AIRE', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        for j, ((x, y, _), u0, nom) in enumerate(zip(pts, us, ('LLANTA', 'RIN', 'EJE'))):
            k = seg(u, u0, u0 + 0.3)
            if k > 0:
                doodle_circle(img, fx, x, y, 110 - 20 * j, 80 - 10 * j, t, k=k, col=ROJO, seed=j)
                pill(img, fx, 220 + 320 * j, 1360, nom, eout(k), size=30, border=ROJO, dot=False)
        texto(img, fx, 540, 400, 'REBOTA', 100, ROJO, P.resorte(seg(u, 0.0, 0.25)), f='sansx', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.6 if 0.05 < ph < 0.2 else 0.0, amp=16)


# 15. ese aire de arriba es el colchón: la llanta al 75 %; el aire de arriba brilla y se comprime como resorte
def s_colchon(t, fi, u, d):
    uc = Wp(15, 'colchon') - 0.15
    sq = 0.5 + 0.5 * math.sin(t * 7)
    fr = Frame(camara(u, [K(-0.3, 2.4, 10, 6, ty=R_EXT + 0.2), K(0.4, 2.9, -8, 6, ty=R_EXT + 0.2), K(d, 2.8, -12, 6, ty=R_EXT + 0.2)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'COLCHÓN', u, t0=uc - 0.1, cy=0.3, entrada='sube')
    draw_objects(fr, P.tfk(llanta_t(nivel=0.5 + 0.04 * sq), t=(0, R_EXT, 0)), xray=1.0, keep=('agua', 'rin', 'maza', 'valvula'))
    for j in range(16):                                                       # el aire de arriba (puntos blancos que vibran)
        a = math.radians(35 + 110 * j / 15)
        r = 0.78 + 0.08 * math.sin(t * 9 + j)
        dot3(fr, (r * math.cos(a), R_EXT + 0.62 + (r - 0.62) * math.sin(a) * 0.6 - 0.04 * sq, 0.3), r=6, col=WHITE, a=0.9, glow=1.2)

    def ui(img, fx):
        kicker(img, 'ARRIBA: AIRE · ABAJO: AGUA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1380, 'EL AIRE SE APRIETA Y AMORTIGUA', eout(seg(u, uc + 0.2, uc + 0.5)), size=28, border=WHITE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. donde hiela, el agua sola se congela: el termómetro baja a −5 °C y el agua se vuelve hielo; «HIELO»
def s_hiela(t, fi, u, d):
    uc = Wp(16, 'congela') - 0.15
    h = P.eout4(seg(u, uc, uc + 0.6))
    fr = Frame(camara(u, [K(-0.3, 3.2, -40, 10, ty=R_EXT), K(0.4, 3.0, -16, 6, ty=R_EXT), K(d, 2.9, -12, 6, ty=R_EXT)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0)
    M.cristal(fr.base, fr.fx, 'HIELO', u, t0=uc - 0.1, cy=0.3, entrada='golpe')
    draw_objects(fr, P.tfk(llanta_t(nivel=0.5, hielo=h), t=(0, R_EXT, 0)), xray=1.0, keep=('agua', 'rin', 'maza', 'valvula'))
    rng = np.random.RandomState(3)
    for j in range(30):                                                         # escarcha que cae
        ph = (t * 0.25 + rng.rand()) % 1.0
        dot3(fr, (rng.uniform(-2, 2), 3.0 - 3.2 * ph, rng.uniform(-1, 1)), r=3, col=HIELO, a=0.7 * seg(u, -0.2, 0.3), glow=0.8)

    def ui(img, fx):
        kicker(img, 'AGUA SOLA · MADRUGADA DE INVIERNO', 150, seg(u, -0.1, 0.2), col=AZULC)
        temp = 6 - 11 * P.eout4(seg(u, 0.0, uc + 0.3))
        P.termometro(img, fx, 140, 1380, 340, 0.75 - 0.6 * P.eout4(seg(u, 0.0, uc + 0.3)), f'{temp:.0f} °C', k=1.0, col=M.mixc((255, 150, 80), HIELO, h))
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. crece y puede botar la llanta del rin: el hielo empuja, la ceja se zafa con sacudida
def s_bota(t, fi, u, d):
    ub = Wp(17, 'botar') - 0.15
    b = P.eout4(seg(u, ub, ub + 0.25))
    fr = Frame(camara(u, [K(-0.3, 3.0, 50, 10, ty=R_EXT), K(0.4, 3.2, 70, 8, ty=R_EXT), K(d, 3.1, 74, 8, ty=R_EXT)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8)
    draw_objects(fr, P.tfk(llanta_t(nivel=0.5, hielo=1.0, botada=b), t=(0, R_EXT, 0)), xray=0.8, keep=('agua', 'rin', 'maza', 'valvula'))
    gx, gy, _ = fr.cam.p1((0, R_EXT + R_RIN, ANCHO * 0.4))

    def ui(img, fx):
        kicker(img, 'EL HIELO OCUPA MÁS QUE EL AGUA', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        flechas = seg(u, 0.1, 0.4)
        doodle_arrow(img, fx, 540, 900, 540, 640, t, k=flechas, col=HIELO, seed=1)
        doodle_arrow(img, fx, 540, 900, 820, 900, t, k=flechas, col=HIELO, seed=2)
        if b > 0.05:
            doodle_circle(img, fx, gx, gy, 140, 90, t, k=b, col=ROJO, seed=4)
            pill(img, fx, 540, 1380, 'SE ZAFA DEL RIN', eout(b), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.2, 0.4), amp=26)


# 18. le echan anticongelante o cloruro de calcio: el garrafón y el costal caen en fila; el agua cambia de color
def s_anticong(t, fi, u, d):
    uc = Wp(18, 'cloruro') - 0.15
    fr = Frame(camara(u, [K(-0.3, 3.8, 30, 8, ty=R_EXT), K(0.4, 3.5, 10, 6, ty=R_EXT), K(d, 3.4, 6, 6, ty=R_EXT)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.4)
    col = M.mixc(AGUA, (80, 220, 170), seg(u, 0.2, 0.6))
    draw_objects(fr, P.tfk(llanta_t(nivel=0.5, agua_col=col), t=(0, R_EXT, 0), s=0.8), xray=1.0, keep=('agua', 'rin', 'maza', 'valvula'))

    def ui(img, fx):
        kicker(img, 'PARA QUE NO SE CONGELE', 150, seg(u, -0.1, 0.2), col=AZULC)
        d_ = ImageDraw.Draw(img)
        e1 = P.entrada(u, -0.2, 0.3, 'cae')
        y1 = 420 + e1['dy'] * 160
        d_.rounded_rectangle((120, y1 - 120, 400, y1 + 120), radius=30, fill=(40, 170, 120), outline=(220, 255, 230), width=4)
        d_.rectangle((220, y1 - 160, 300, y1 - 120), fill=(220, 220, 226))
        texto(img, fx, 260, y1, 'ANTI-', 40, (10, 30, 20), 1.0, f='sansx', glow=0)
        texto(img, fx, 260, y1 + 50, 'CONGELANTE', 30, (10, 30, 20), 1.0, f='sansx', glow=0)
        if u > uc - 0.2:
            e2 = P.entrada(u, uc - 0.2, 0.3, 'cae')
            y2 = 420 + e2['dy'] * 160
            d_.polygon([(640, y2 - 140), (960, y2 - 140), (990, y2 + 130), (610, y2 + 130)], fill=(236, 232, 220), outline=(255, 255, 255))
            texto(img, fx, 800, y2 - 20, 'CLORURO', 44, (40, 40, 44), 1.0, f='sansx', glow=0)
            texto(img, fx, 800, y2 + 40, 'DE CALCIO', 40, (40, 40, 44), 1.0, f='sansx', glow=0)
        pill(img, fx, 540, 1430, 'BAJAN EL PUNTO DE CONGELACIÓN', eout(seg(u, uc + 0.4, uc + 0.7)), size=26, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. el cloruro oxida el rin: manchas de óxido que crecen en el rin crema; «ÓXIDO»
def s_oxido(t, fi, u, d):
    uo = Wp(19, 'oxida') - 0.15
    ox = P.eout4(seg(u, uo, uo + 0.6))
    fr = Frame(camara(u, [K(-0.3, 3.0, -60, 8, ty=R_EXT), K(0.4, 2.4, -24, 6, ty=R_EXT), K(d, 2.3, -20, 6, ty=R_EXT)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'ÓXIDO', u, t0=uo - 0.1, cy=0.28, entrada='zoom')
    draw_objects(fr, P.tfk(llanta_t(oxido=ox), t=(0, R_EXT, 0)))
    rx, ry, _ = fr.cam.p1((0.3, R_EXT + 0.3, ANCHO * 0.4))

    def ui(img, fx):
        kicker(img, 'EL CLORURO ES CORROSIVO', 150, seg(u, -0.1, 0.2), col=(255, 150, 90))
        doodle_circle(img, fx, rx, ry, 170, 150, t, k=seg(u, uo + 0.3, uo + 0.6), col=(255, 140, 60), seed=6)
        pill(img, fx, 540, 1380, 'LAVA Y REVISA EL RIN', eout(seg(u, uo + 0.6, uo + 0.9)), size=30, border=(255, 140, 60), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. física de rancho: más peso abajo, más agarre y menos vuelcos (lista que cae con palomitas sobre el tractor)
def s_fisica(t, fi, u, d):
    us = [Wp(20, 'peso') - 0.2, Wp(20, 'agarre') - 0.2, Wp(20, 'vuelcos') - 0.2]
    fr = Frame(camara(u, [K(-0.3, 8.0, -60, 12, tx=-0.2, ty=0.9), K(0.4, 7.0, -30, 10, tx=-0.2, ty=0.9), K(d, 6.8, -26, 10, tx=-0.2, ty=0.9)], cy=0.7))
    space(fr, t, floor=None, bokeh=0.9, beam=0.5)
    surcos(fr, t, a=1.0, mov=t * 0.6)
    draw_objects(fr, tractor(giro=-t * 160, nivel=0.5, arado=True), xray=0.6,
                 keep=('agua', 'rin', 'maza', 'valvula', 'cofre', 'cuerpo', 'salpicadera', 'rops', 'escape', 'arado', 'enganche', 'llantad', 'rind', 'parrilla'))

    def ui(img, fx):
        kicker(img, 'FÍSICA DE RANCHO', 150, seg(u, -0.1, 0.2), col=AZULC)
        for j, (txt, u0) in enumerate(zip(('MÁS PESO ABAJO', 'MÁS AGARRE', 'MENOS VUELCOS'), us)):
            k = P.eout4(seg(u, u0, u0 + 0.25))
            if k <= 0:
                continue
            y = 330 + 110 * j
            x = 540 + (1 - k) * 800
            texto(img, fx, x - 300, y, '✓', 60, VERDE, k, f='sansx', glow=0.5)
            texto(img, fx, x + 40, y, txt, 54, WHITE, k, f='sansx', glow=0.2)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. mándaselo a tu compa del rancho: el tractor al atardecer y la foto real de los campos que cae
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.0, 100, 8, tx=-0.6, ty=0.9), K(0.4, 6.6, 50, 7, tx=-0.6, ty=0.9), K(d, 6.4, 44, 7, tx=-0.6, ty=0.9)], cy=0.7))
    space(fr, t, floor=None, bokeh=0.9, beam=0.6, beam_x=0.6)
    surcos(fr, t, a=1.0, mov=t * 0.5)
    draw_objects(fr, tractor(giro=-t * 140, arado=True))
    polvo(fr, t, (XR - 1.6, 0.1, 0.0), k=0.6, seed=11)
    im = foto('campos2.jpg')

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('del rancho.', 'serif')], 220, seg(u, 0.0, 0.15), size=78)
        if im is not None:
            photo_card(img, fx, im, 540, 700, 520, 0.3, u, caption='CAMPOS DE CHIHUAHUA DESDE EL ESPACIO', angle0=-8.0)
            credito(img, y=990)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


# ------------------------------------------------------------------ escena doble (frase muy corta + la siguiente, con corte interno)
_T0, _ = montaje.cargar(TEMA)


def _off(ia, ib):
    return (_T0[ib][0] - _T0[ia][0]) if _T0 else 0.0


def combo(fa, fb, ia, ib, lead=0.15, tr=None, dur=0.25):
    def fn(t, fi, u, d):
        off = _off(ia, ib)
        cut = off - lead
        if u < cut:
            return fa(t, fi, u, cut + 0.2)
        ub, db = u - off, d - off
        if u < cut + dur:
            k = seg(u, cut, cut + dur)
            A, B = fa(t, fi, u, cut + 0.2), fb(t, fi, ub, db)
            return tr(A, B, k) if tr else M.tr_zoom_through(A, B, k, 0.5, 0.42)
        return fb(t, fi, ub, db)
    return fn


C12 = _off(1, 2) - 0.15
s_fuga_llenan = combo(s_fuga, s_llenan, 1, 2)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-4.2, 'whoosh_suave', 0.6), (-2.1, 'riser', 0.6), (-1.35, 'whoosh', 0.9), (-1.15, 'slap', 0.5),
                     (U_ATERRIZA, 'whoosh', 0.8), (U_ATERRIZA + 0.3, 'sub', 1.0), (0.1, 'bass', 0.7)]),
           dict(desde=1, fn=s_fuga_llenan, tr='glitch', sfx=[(0.0, 'slap', 0.5), (0.35, 'scribble', 0.7), (C12 - 0.2, 'whoosh', 0.9),
                                                          (C12 + 0.3, 'whoosh_suave', 0.6), (C12 + 1.0, 'riser', 0.4)]),
           dict(desde=3, fn=s_litros, tr='golpe', sfx=[(0.05 * j, 'tick', 0.25) for j in range(20)] + [(1.6, 'bass', 0.8)]),
           dict(desde=4, fn=s_tonelada, tr='deslizar_abajo', sfx=[(0.2, 'sub', 1.0), (0.25, 'thud', 0.9)] + [(0.3 + 0.08 * j, 'tick2', 0.3) for j in range(8)]),
           dict(desde=5, fn=s_aire, tr='cubo', sfx=[(0.2, 'whoosh_suave', 0.5), (0.5, 'tick', 0.5)]),
           dict(desde=6, fn=s_patina, tr='remolino', c=(0.5, 0.55), sfx=[(0.1 * j, 'thud', 0.3) for j in range(14)]),
           dict(desde=7, fn=s_agarra, tr='wipe', sfx=[(0.3, 'bass', 0.6), (1.5, 'chime_b', 0.6)]),
           dict(desde=8, fn=s_ladera, tr='giro', sfx=[(0.5, 'whoosh_suave', 0.5), (1.2, 'chime_a', 0.5)]),
           dict(desde=9, fn=s_voltea, tr='cubo_izq', sfx=[(0.3, 'whoosh_suave', 0.5), (1.0, 'thud', 0.7), (1.05, 'chime_c', 0.5)]),
           dict(desde=10, fn=s_valvula, tr='iris', c=(0.5, 0.4), sfx=[(0.2, 'click', 0.6), (1.2, 'click', 0.8), (1.3, 'click', 0.6)]),
           dict(desde=11, fn=s_tresc, tr='mosaico', sfx=[(0.1, 'whoosh_suave', 0.6), (1.5, 'chime_c', 0.6)]),
           dict(desde=12, fn=s_tope, tr='rompe', c=(0.5, 0.45), sfx=[(0.3, 'riser', 0.5), (1.4, 'sub', 1.0)]),
           dict(desde=13, fn=s_piedra, tr='golpe', sfx=[(0.0, 'bass', 0.6), (1.4, 'thud', 1.0)]),
           dict(desde=14, fn=s_rebota, tr='deslizar', sfx=[(0.1 + 0.62 * j, 'thud', 0.8) for j in range(5)] + [(1.0, 'scribble', 0.6)]),
           dict(desde=15, fn=s_colchon, tr='push', c=(0.5, 0.45), sfx=[(0.6, 'shimmer', 0.5)]),
           dict(desde=16, fn=s_hiela, tr='flash', sfx=[(0.4, 'shimmer', 0.6), (1.3, 'chime_c', 0.5)]),
           dict(desde=17, fn=s_bota, tr='whip', sfx=[(0.2, 'riser', 0.4), (1.1, 'sub', 1.0), (1.15, 'slap', 0.7)]),
           dict(desde=18, fn=s_anticong, tr='rebanadas', sfx=[(-0.1, 'thud', 0.7), (1.4, 'thud', 0.7)]),
           dict(desde=19, fn=s_oxido, tr='cubo_izq', sfx=[(0.8, 'scribble', 0.6), (1.2, 'tick', 0.5)]),
           dict(desde=20, fn=s_fisica, tr='whip_izq', sfx=[(0.6, 'chime_a', 0.5), (1.5, 'chime_b', 0.5), (2.4, 'chime_c', 0.5)]),
           dict(desde=21, fn=s_compa, tr='ritmo', sfx=[(0.05, 'slap', 0.7), (0.15, 'bass', 0.7), (0.4, 'slap', 0.6)]),
           dict(desde=22, loop=True, tr='cristal', palabra='RANCHO')]

if __name__ == '__main__':
    montaje.cli(globals())
