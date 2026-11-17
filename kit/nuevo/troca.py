"""Reel diario jue 19-nov-2026 18:00 — «Tu troca 4x4… no siempre es 4x4.» (4x4 de tiempo parcial: en 2H solo empujan
las de atrás y las de adelante van libres; al meter la palanca la caja de transferencia amarra los dos ejes y jalan
parejo; prueba en el lodo; error: traerla metida en el pavimento: en una curva las de adelante recorren más camino,
amarradas tienen que girar igual, en el lodo la llanta resbala tantito y en seco no: brinca, rechina, dirección dura y
castiga la caja de transferencia, las crucetas y los ejes; 4x4 solo en tierra, lodo, arena o nieve; en 4L no pasar de 40).
Comunidad: troqueros del norte y del campo. Inicio tipo 6 (pantalla dividida que choca): arriba la troca atascada en
el lodo en 2H («4x2» de cristal), abajo la misma saliendo en 4H («4x4» de cristal); las dos mitades chocan con
sacudida y el título cae en la costura. El final («porque su troca 4x4… no siempre es 4x4») regresa a él (loop).
Voz Isaac (eleven_v4) del 17-nov, 70.2 s. Datos y fuentes: guiones/2026-11-19_troca.txt.
Foto real: «Transfer case 4wd.jpg» (Gnangarra, CC BY 2.5 AU, Wikimedia Commons; caja de transferencia de una Pajero).
La troca, los ejes, la caja y las trayectorias son esquemas sin marca marcados «ESQUEMA».
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
from gasolina import tubo, _B, texto, esquema, golpe_k, sacudir, K, camara

M3 = M.M3
TEMA = 'troca'
TXT = ['Tu troca 4x4… no siempre es 4x4.',
       'Si es de tiempo parcial, casi siempre anda en dos:',
       'solo empujan las de atrás.',
       'Las de adelante van de paseo, girando libres.',
       'Al meter la palanca o el botón,',
       'la caja de transferencia amarra los dos ejes.',
       'Y las cuatro jalan parejo, a la misma velocidad.',
       'La prueba en el lodo: en dos, las de atrás patinan y se entierran.',
       'En cuatro, las de adelante la jalan… y sale.',
       'Pero aquí está el error: traerla metida en el pavimento.',
       'En una curva, las llantas de adelante recorren más camino que las de atrás.',
       'Pero amarradas tienen que girar igual…',
       'y algo tiene que ceder.',
       'En el lodo, la llanta resbala tantito y no pasa nada.',
       'En pavimento seco no resbala:',
       'la troca brinca, rechina y la dirección se pone dura.',
       'Esa tensión castiga la caja de transferencia, las crucetas y los ejes.',
       'Por eso el manual dice:',
       '4x4 solo en tierra, lodo, arena o nieve.',
       'Y en 4 baja, muchos manuales piden no pasar de 40 km/h.',
       'Mándaselo a quien trae la 4x4 metida en la ciudad,',
       'porque su troca 4x4… no siempre es 4x4.']
VOZ = ['[curious] Tu troca cuatro por cuatro… no siempre es cuatro por cuatro.',
       'Si es de tiempo parcial, casi siempre anda en dos:',
       'solo empujan las de atrás.',
       'Las de adelante van de paseo, girando libres.',
       'Al meter la palanca o el botón,',
       'la caja de transferencia amarra los dos ejes.',
       'Y las cuatro jalan parejo, a la misma velocidad.',
       'La prueba en el lodo: en dos, las de atrás patinan y se entierran.',
       'En cuatro, las de adelante la jalan… y sale.',
       '[excited] Pero aquí está el error: traerla metida en el pavimento.',
       'En una curva, las llantas de adelante recorren más camino que las de atrás.',
       'Pero amarradas tienen que girar igual…',
       'y algo tiene que ceder.',
       'En el lodo, la llanta resbala tantito y no pasa nada.',
       'En pavimento seco no resbala:',
       'la troca brinca, rechina y la dirección se pone dura.',
       'Esa tensión castiga la caja de transferencia, las crucetas y los ejes.',
       'Por eso el manual dice:',
       'cuatro por cuatro solo en tierra, lodo, arena o nieve.',
       'Y en cuatro baja, muchos manuales piden no pasar de cuarenta por hora.',
       'Mándaselo a quien trae la cuatro por cuatro metida en la ciudad,',
       'porque su troca cuatro por cuatro… no siempre es cuatro por cuatro.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_troca.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-19_troca_words.json')
IMG = os.path.join(HERE, 'img', 'troca')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
VERDE = (40, 205, 110)
GRIS = (150, 150, 160)
ROJO_T = (172, 34, 38)
NEGRO = (24, 24, 28)
CROMO = (210, 212, 218)
LODO = (92, 64, 40)
LODO_C = (130, 96, 62)
ASFALTO = (44, 45, 50)
ACTIVO = (255, 160, 60)
LIBRE = (120, 124, 134)

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
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


_F = {}


def foto():
    if 'c' not in _F:
        im = Image.open(os.path.join(IMG, 'troca_i_transfer.jpg')).convert('RGB')
        w, h = im.size
        _F['c'] = im.crop((int(w * 0.12), int(h * 0.1), int(w * 0.9), int(h * 0.9)))
    return _F['c']


# ------------------------------------------------------------------ la troca (frente hacia +x)
XF, XR, ZW, RW, WW = 1.3, -1.2, 0.68, 0.38, 0.3      # ejes, vía, radio y ancho de llanta
X_TC = 0.05                                          # caja de transferencia


def rueda(x, z, ang, steer=0.0, col_rin=CROMO, glow=None, hund=0.0):
    """Llanta con rin y 3 rayos (se nota cuando gira). ang en grados (rz), steer en grados (ry)."""
    ms = [named(M3.cyl(RW, WW, (26, 26, 28), n=26, shadow=0, gloss=0.15, y0=-WW / 2).tf(rx=90), 'llanta', rim=0.35),
          named(M3.cyl(RW * 0.6, WW + 0.02, col_rin, n=18, shadow=0, gloss=0.85, y0=-(WW + 0.02) / 2).tf(rx=90), 'rin', rim=0.8)]
    sgn = 1 if z > 0 else -1
    for j in range(3):
        b = named(M3.box(0.06, RW * 1.1, 0.03, (90, 92, 98), shadow=0, base=False, gloss=0.6).tf(rz=ang + 60 * j)
                  .tf(t=(0, 0, sgn * (WW / 2 + 0.03))), 'rayo', rim=0.6)
        ms.append(b)
    if glow is not None:
        for m in ms[:2]:
            m.glow = glow
    out = []
    for m in ms:
        mm = m.tf(ry=steer).tf(t=(x, RW - hund, z))
        for a in P.ATTRS:
            if hasattr(m, a):
                setattr(mm, a, getattr(m, a))
        out.append(mm)
    return out


def carroceria(col=ROJO_T):
    ms = []
    ms.append(named(M3.rbox(2.45, 0.5, 1.36, 0.14, col, n=4, shadow=0, gloss=0.8).tf(t=(0.75, 0.62, 0)), 'cuerpo', rim=0.8, gloss=0.8))
    ms.append(named(M3.rbox(1.25, 0.52, 1.28, 0.16, col, n=4, shadow=0, gloss=0.8).tf(t=(0.12, 1.12, 0)), 'cuerpo', rim=0.8, gloss=0.8))
    ms.append(named(M3.rbox(1.0, 0.34, 1.3, 0.12, (24, 30, 40), n=4, shadow=0, gloss=0.95).tf(t=(0.16, 1.2, 0)), 'vidrio', rim=0.9))
    _B(ms, 1.6, 0.08, 1.36, M.mixc(col, NEGRO, 0.4), -1.25, 0.62, 0, name='cuerpo', gloss=0.5)
    for z in (0.645, -0.645):
        _B(ms, 1.6, 0.48, 0.07, col, -1.25, 0.62, z, name='cuerpo', gloss=0.8)
    _B(ms, 0.07, 0.48, 1.36, col, -2.03, 0.62, 0, name='cuerpo', gloss=0.8)
    _B(ms, 0.07, 0.48, 1.36, col, -0.47, 0.62, 0, name='cuerpo', gloss=0.8)
    _B(ms, 0.12, 0.18, 1.42, CROMO, 2.0, 0.5, 0, name='cuerpo', gloss=0.95)
    _B(ms, 0.12, 0.16, 1.42, CROMO, -2.1, 0.5, 0, name='cuerpo', gloss=0.95)
    _B(ms, 0.03, 0.24, 0.8, (18, 18, 22), 1.985, 0.74, 0, name='cuerpo', gloss=0.6)
    for z in (0.5, -0.5):
        _B(ms, 0.03, 0.1, 0.26, (255, 248, 230), 1.99, 0.95, z, name='faro', glow=(160, 150, 120))
        _B(ms, 0.03, 0.18, 0.12, (210, 30, 30), -2.08, 0.82, z * 1.2, name='faro', glow=(120, 20, 20))
    for x in (-2.0, 1.95):                                             # el chasis (largueros)
        pass
    for z in (0.38, -0.38):
        _B(ms, 3.4, 0.12, 0.12, (54, 56, 62), -0.1, 0.4, z, name='chasis', gloss=0.4)
    return ms


def tren(act_f=0.0, act_r=1.0, lock=0.0, rojo=0.0):
    """Motor, transmisión, caja de transferencia, flechas, diferenciales y ejes (nombre 'in': se ve con rayos X)."""
    cf = M.mixc(M.mixc(LIBRE, ACTIVO, act_f), (255, 70, 50), rojo)
    cr = M.mixc(M.mixc(LIBRE, ACTIVO, act_r), (255, 70, 50), rojo)
    ctc = M.mixc(M.mixc((150, 154, 164), (255, 190, 90), lock), (255, 80, 60), rojo)
    ms = []
    _B(ms, 0.75, 0.42, 0.55, (110, 114, 124), 1.35, 0.42, 0, name='in', gloss=0.6)
    ms.append(named(M3.cyl(0.16, 0.9, (130, 134, 144), n=16, shadow=0, gloss=0.7, r2=0.12).tf(rz=90).tf(t=(0.98, 0.58, 0)), 'in', rim=0.7))
    tc = _B(ms, 0.32, 0.34, 0.42, ctc, X_TC, 0.38, 0.05, name='in', gloss=0.7,
            glow=M.scale_c((255, 160, 60), 0.6 * lock) if lock > 0.02 or rojo > 0.02 else None)
    if rojo > 0.02:
        tc.glow = M.scale_c((255, 70, 50), 0.7 * rojo)
    ms.append(tubo((X_TC - 0.16, 0.5, 0.0), (XR + 0.15, RW, 0.0), r=0.045, col=cr, name='in', gloss=0.8))
    ms.append(tubo((X_TC + 0.16, 0.5, 0.2), (XF - 0.15, RW, 0.2), r=0.045, col=cf, name='in', gloss=0.8))
    for x, c in ((XR, cr), (XF, cf)):
        ms.append(named(M3.sphere(0.17, c, nu=18, nv=10, shadow=0, gloss=0.7).tf(t=(x, RW, 0.05)), 'in', rim=0.8))
        ms.append(tubo((x, RW, -ZW + 0.12), (x, RW, ZW - 0.12), r=0.045, col=c, name='in', gloss=0.8))
    return ms


def flujo(fr, t, act_f, act_r, k=1.0, col=ACTIVO):
    """La fuerza que corre por las flechas (puntitos que viajan)."""
    rutas = [((X_TC - 0.16, 0.5, 0.0), (XR + 0.15, RW, 0.0), act_r), ((X_TC + 0.16, 0.5, 0.2), (XF - 0.15, RW, 0.2), act_f)]
    for p0, p1, a in rutas:
        if a * k < 0.02:
            continue
        p0, p1 = np.array(p0), np.array(p1)
        for j in range(5):
            ph = (t * 1.6 + j / 5) % 1.0
            dot3(fr, p0 + (p1 - p0) * ph, r=5, col=col, a=a * k, glow=1.6)


def troca(ang=(0, 0, 0, 0), steer=0.0, col=ROJO_T, interior=False, act_f=0.0, act_r=1.0, lock=0.0, rojo=0.0, hund=0.0,
          glow_f=0.0, glow_r=0.0):
    ms = carroceria(col)
    gf = M.scale_c(ACTIVO, 0.5 * glow_f) if glow_f > 0.02 else None
    gr = M.scale_c(ACTIVO, 0.5 * glow_r) if glow_r > 0.02 else None
    ms += rueda(XF, ZW, ang[0], steer, glow=gf, hund=hund) + rueda(XF, -ZW, ang[1], steer, glow=gf, hund=hund)
    ms += rueda(XR, ZW, ang[2], glow=gr, hund=hund) + rueda(XR, -ZW, ang[3], glow=gr, hund=hund)
    if interior:
        ms += tren(act_f, act_r, lock, rojo)
    return ms


def colocar(ms, x=0.0, y=0.0, z=0.0, ry=0.0, rz=0.0, s=1.0):
    return P.tfk(P.tfk(ms, rz=rz), s=s, ry=ry, t=(x, y, z))


def piso_lodo(ms, w=9.0, d=6.0, x=0.0):
    _B(ms, w, 0.06, d, LODO, x, -0.06, 0, name='lodo', gloss=0.7)


def piso_asfalto(fr, ms, w=12.0, d=5.0, x=0.0, t=0.0, vel=0.0):
    _B(ms, w, 0.04, d, ASFALTO, x, -0.04, 0, name='asfalto', gloss=0.3)
    for j in range(8):                                                   # raya central punteada
        x0 = x - w / 2 + ((j * 1.5 - t * vel) % w)
        line3(fr, [(x0, 0.01, -1.2), (x0 + 0.7, 0.01, -1.2)], col=(240, 200, 80), w=5, a=0.8, glow=0.5)


def salpica(fr, t, x, z, k=1.0, n=14, seed=1, sentido=-1, col=LODO_C):
    """Lodo que sale disparado de una llanta que patina (hacia atrás y arriba)."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    for j in range(n):
        ph = (t * 2.2 + j / n) % 1.0
        v = 0.8 + rng.rand()
        p = (x + sentido * (0.3 + 1.6 * ph * v), 0.15 + 1.6 * ph * v - 2.4 * ph * ph, z + (rng.rand() - 0.5) * 0.5)
        dot3(fr, p, r=5 + 4 * rng.rand(), col=col, a=k * (1 - ph * 0.6), glow=0.2)


def ang_rueda(dist):
    return -math.degrees(dist / RW)


# ================================================================== escenas
# 0. gancho (inicio 6: pantalla dividida que choca). Arriba: atascada en el lodo en 2H (las de atrás patinan, «4x2»
#    de cristal). Abajo: la misma saliendo en 4H («4x4» de cristal). Las mitades llegan separadas y chocan en u = 0.05
#    con sacudida; antes del loop se vuelven a separar, así el último cuadro es igual al primero.
U_CHOQUE = 0.05


def _mitad(t, u, arriba):
    if arriba:
        fr = Frame(camara(u, [K(-3.5, 9.0, 40, 10, ty=0.8), K(U_CHOQUE, 8.2, 28, 8, ty=0.8), K(3.0, 7.8, 20, 8, ty=0.8)], cy=0.5))
    else:
        fr = Frame(camara(u, [K(-3.5, 9.0, -40, 10, ty=0.8, tx=0.6), K(U_CHOQUE, 8.2, -28, 8, ty=0.8, tx=0.6),
                              K(3.0, 7.8, -20, 8, ty=0.8, tx=0.9)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, '4x2' if arriba else '4x4', u, t0=-3.0, cy=0.47, entrada='golpe')
    ms = []
    piso_lodo(ms)
    if arriba:
        a = ang_rueda(t * 6.0)
        tr_ = troca(ang=(0, 0, a, a), hund=0.1, glow_r=1.0)
        ms += colocar(tr_, y=-0.02 * abs(math.sin(t * 20)))
        draw_objects(fr, ms)
        salpica(fr, t, XR, ZW, k=1.0, seed=1)
        salpica(fr, t, XR, -ZW, k=1.0, seed=2)
    else:
        xm = 0.25 * ((t * 0.5) % 1.0)
        a = ang_rueda(t * 2.0)
        tr_ = troca(ang=(a, a, a, a), glow_f=1.0, glow_r=1.0)
        ms += colocar(tr_, x=xm)
        draw_objects(fr, ms)
        salpica(fr, t, XF + xm, ZW, k=0.4, seed=3, n=6)
        salpica(fr, t, XR + xm, ZW, k=0.4, seed=4, n=6)
    return fr


def s_gancho(t, fi, u, d):
    uns = Wp(0, 'siempre') - 0.15
    if u < -0.25:
        gap = 230 * seg(u, -0.9, -0.25)
    else:
        gap = 230 * (1 - P.eout4(seg(u, -0.25, U_CHOQUE)))
    A = _mitad(t, u, True)
    B = _mitad(t, u, False)

    def ui_a(img, fx):
        pill(img, fx, 540, 1180, '2H · SOLO ATRÁS', 1.0, size=30, border=RED)
        if u > uns:
            dl = ImageDraw.Draw(img)
            e = seg(u, uns, uns + 0.25)
            dl.line([(360, 1180 - 40 * e), (360 + 360 * e, 1180 + 40 * e)], fill=RED, width=10)

    def ui_b(img, fx):
        pill(img, fx, 540, 700, '4H · LAS CUATRO', 1.0, size=30, border=VERDE)
    A.ui.append(ui_a)
    B.ui.append(ui_b)
    ia = finish(A, fi)
    ib = finish(B, fi)
    out = np.zeros_like(ia)
    g = int(gap)
    top = ia[480 + g:1440, :, :] if g < 960 else ia[:0]
    out[0:960 - g] = top[:960 - g]
    bot = ib[480:1440 - g]
    out[960 + g:1920] = bot[:960 - g]
    img = Image.fromarray(out)
    fx = Image.new('RGB', img.size, (0, 0, 0))
    dl = ImageDraw.Draw(img)
    kc = 1 - seg(u, U_CHOQUE + 0.05, U_CHOQUE + 0.5) if u >= U_CHOQUE else 0.5
    dl.line([(0, 960 - g), (1080, 960 - g)], fill=M.scale_c(WHITE, 0.6 + 0.4 * kc), width=4)
    dl.line([(0, 960 + g), (1080, 960 + g)], fill=M.scale_c(WHITE, 0.6 + 0.4 * kc), width=4)
    P.titulo_golpe(img, fx, [('Tu troca 4x4…', 'sans'), ('no siempre es 4x4.', 'serif')], 850, seg(u, 0.15, 0.3), size=74)
    kicker(img, 'TIEMPO PARCIAL', 120, seg(u, 0.3, 0.5), col=AZULC)
    a = np.asarray(img, np.float32) + np.asarray(fx.filter(ImageFilter.GaussianBlur(6)), np.float32) * 0.8
    if U_CHOQUE <= u < U_CHOQUE + 0.14:
        a += 120 * (1 - seg(u, U_CHOQUE, U_CHOQUE + 0.14))
    out = a.clip(0, 255).astype(np.uint8)
    return sacudir(out, t, max(golpe_k(u, U_CHOQUE, 0.4), golpe_k(u, 0.3, 0.25)), amp=28)


# 1. si es de tiempo parcial, casi siempre anda en dos: rayos X del chasis; solo la flecha de atrás lleva fuerza
def s_parcial(t, fi, u, d):
    ud = Wp(1, 'dos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.2, 70, 14, ty=0.7), K(0.35, 6.0, 30, 18, ty=0.6), K(ud, 5.4, 18, 22, ty=0.5),
                          K(d, 5.3, 14, 22, ty=0.5)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.4)
    a = ang_rueda(t * 2.0)
    draw_objects(fr, troca(ang=(a, a, a, a), interior=True, act_f=0.0, act_r=1.0, glow_r=0.8),
                 xray=seg(u, -0.2, 0.25), keep=('in', 'llanta', 'rin', 'rayo'))
    flujo(fr, t, 0.0, 1.0, k=seg(u, 0.2, 0.5))
    pt = fr.cam.p1((X_TC, 0.3, 0.05))

    def ui(img, fx):
        kicker(img, '4x4 DE TIEMPO PARCIAL · RAYOS X', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pt[0], pt[1] + 110, 'CAJA DE TRANSFERENCIA', eout(seg(u, 0.5, 0.75)), size=22, border=(200, 200, 210))
        P.numero_golpe(img, fx, '2H', 330, seg(u, ud, ud + 0.15), size=160, col=ACTIVO)
        esquema(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ud + 0.15, 0.3), amp=16)


# 2. solo empujan las de atrás: close a las llantas traseras con flechas de empuje
def s_atras(t, fi, u, d):
    ue = Wp(2, 'empujan') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, 120, 8, tx=-1.2, ty=0.5), K(0.3, 3.2, 150, 6, tx=-1.2, ty=0.45),
                          K(d, 3.1, 156, 6, tx=-1.2, ty=0.45)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.3)
    a = ang_rueda(t * 3.0)
    draw_objects(fr, troca(ang=(a, a, a, a), interior=True, act_r=1.0, glow_r=1.0), xray=0.7, keep=('in', 'llanta', 'rin', 'rayo'))
    flujo(fr, t, 0.0, 1.0)
    pr = fr.cam.p1((XR, RW, -ZW - 0.3))
    for j in range(3):                                                    # flechas de empuje (hacia +x)
        ph = (t * 1.5 + j / 3) % 1.0
        line3(fr, [(XR + 0.2 + 0.8 * ph, 0.25 + 0.15 * j, -ZW - 0.35), (XR + 0.6 + 0.8 * ph, 0.25 + 0.15 * j, -ZW - 0.35)],
              col=ACTIVO, w=5, a=seg(u, ue, ue + 0.2) * (1 - ph), glow=1.2)

    def ui(img, fx):
        texto(img, fx, 540, 300, 'empujan', 90, ACTIVO, eout(seg(u, ue, ue + 0.2)), f='serif', glow=0.5)
        pill(img, fx, pr[0], pr[1] + 170, 'LAS DE ATRÁS', eout(seg(u, -0.2, 0.1)), size=30, border=ACTIVO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. las de adelante van de paseo, girando libres («LIBRES» de cristal; las delanteras grises, sin fuerza)
def s_paseo(t, fi, u, d):
    ul = Wp(3, 'libres') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, 20, 6, tx=1.3, ty=0.5, tz=0.4), K(0.3, 3.8, 50, 4, tx=1.3, ty=0.45, tz=0.4),
                          K(ul, 3.4, 64, 4, tx=1.3, ty=0.45, tz=0.4), K(d, 3.35, 68, 4, tx=1.3, ty=0.45, tz=0.4)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.3)
    M.cristal(fr.base, fr.fx, 'LIBRES', u, t0=ul - 0.05, cy=0.3, entrada='sube')
    a = ang_rueda(t * 3.0)
    draw_objects(fr, troca(ang=(a, a, a, a), interior=True, act_r=1.0), xray=0.7, keep=('in', 'llanta', 'rin', 'rayo'))
    flujo(fr, t, 0.0, 1.0)
    pf = fr.cam.p1((XF, RW + 0.6, ZW))

    def ui(img, fx):
        kicker(img, 'LAS DE ADELANTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pf[0], pf[1] - 40, 'SIN FUERZA', eout(seg(u, 0.3, 0.55)), size=28, border=LIBRE)
        doodle_circle(img, fx, pf[0], pf[1] + 150, 150, 150, t, k=seg(u, 0.5, 0.8), col=WHITE, seed=2)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. al meter la palanca o el botón: la segunda palanca pasa de 2H a 4H (y el botón gira)
def s_palanca(t, fi, u, d):
    up = Wp(4, 'palanca') - 0.1
    ub = Wp(4, 'boton') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.0, 40, 30, ty=0.5), K(0.3, 2.4, 14, 26, ty=0.5), K(d, 2.35, 10, 26, ty=0.5)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9, beam=0.6)
    e = P.entrada(u, -0.25, 0.3, 'pop')
    sc = max(0.05, e['escala'])
    k = P.resorte(seg(u, up, up + 0.35))
    ms = []
    _B(ms, 1.4, 0.08, 0.7, (34, 34, 38), 0, 0, 0, name='consola', gloss=0.4)
    ms.append(named(M3.cyl(0.13, 0.14, (20, 20, 22), n=16, shadow=0, gloss=0.2, r2=0.07).tf(t=(-0.2 + 0.35 * k, 0.08, 0)), 'bota', rim=0.4))
    pal = [named(M3.cyl(0.03, 0.55, CROMO, n=10, shadow=0, gloss=0.9).tf(t=(0, 0, 0)), 'palanca', rim=0.9),
           named(M3.sphere(0.09, (30, 30, 34), nu=18, nv=10, shadow=0, gloss=0.6).tf(t=(0, 0.6, 0)), 'pomo', rim=0.8)]
    ms += P.tfk(pal, rz=-14 * (1 - 2 * k), t=(-0.2 + 0.35 * k, 0.1, 0))
    draw_objects(fr, P.tfk(ms, s=sc))
    p2 = fr.cam.p1((-0.2, 0.05, 0.38))
    p4 = fr.cam.p1((0.15, 0.05, 0.38))

    def ui(img, fx):
        kicker(img, 'LA SEGUNDA PALANCA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, p2[0] - 30, p2[1] + 60, '2H', 1.0, size=30, border=ACTIVO if k < 0.5 else LIBRE, dot=False)
        pill(img, fx, p4[0] + 50, p4[1] + 60, '4H', 1.0, size=30, border=VERDE if k > 0.5 else LIBRE, dot=False)
        kb = eout(seg(u, ub, ub + 0.25))
        if kb > 0.01:                                                    # o el botón (perilla)
            cx, cy, r = 540, 1280, 90
            dl = ImageDraw.Draw(img)
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(WHITE, kb), width=6)
            ag = math.radians(-120 + 80 * P.resorte(seg(u, ub + 0.15, ub + 0.5)))
            dl.line([(cx, cy), (cx + r * 0.8 * math.cos(ag), cy + r * 0.8 * math.sin(ag))], fill=M.scale_c(VERDE, kb), width=8)
            texto(img, fx, cx, cy + r + 50, 'O EL BOTÓN', 32, WHITE, kb, f='mono', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.2, 0.25), amp=12)


# 5. la caja de transferencia amarra los dos ejes: cae la foto real y el esquema de la caja; el collar se corre y
#    las dos salidas se encienden («AMARRA» de cristal)
def s_transfer(t, fi, u, d):
    uc = Wp(5, 'caja') - 0.1
    ua = Wp(5, 'amarra') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.2, 40, 12, ty=0.9), K(0.3, 3.4, 18, 10, ty=0.9), K(ua, 3.0, -16, 8, ty=0.9),
                          K(d, 2.95, -20, 8, ty=0.9)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, 'AMARRA', u, t0=ua - 0.05, cy=0.28, entrada='golpe')
    lk = P.eout4(seg(u, ua, ua + 0.35))
    ms = []
    _B(ms, 1.0, 0.9, 0.7, M.mixc((140, 144, 152), (255, 190, 90), 0.4 * lk), 0, 0.45, 0, name='caja', gloss=0.6,
       glow=M.scale_c(ACTIVO, 0.3 * lk) if lk > 0.02 else None)
    ms.append(tubo((-1.8, 1.1, 0), (-0.5, 1.1, 0), r=0.07, col=CROMO, name='entrada'))
    ms.append(tubo((0.5, 1.1, 0), (1.9, 1.1, 0), r=0.07, col=M.mixc(LIBRE, ACTIVO, 1.0), name='atras'))
    ms.append(tubo((0.5, 0.3, 0.1), (1.9, 0.3, 0.1), r=0.07, col=M.mixc(LIBRE, ACTIVO, lk), name='adelante'))
    ms.append(named(M3.torus(0.13, 0.04, ACTIVO if lk > 0.5 else (200, 200, 210), nu=22, nv=6, gloss=0.8).tf(rz=90)
                    .tf(t=(0.62 + 0.3 * lk, 1.1, 0)), 'collar', rim=0.9))
    e = P.entrada(u, -0.25, 0.3, 'cae')
    draw_objects(fr, P.tfk(ms, t=(0, -e['dy'] * 0.4, 0)), xray=0.55, keep=('entrada', 'atras', 'adelante', 'collar'))
    a = t * 6
    for cy_, on in ((1.1, 1.0), (0.3, lk)):                               # engranes/cadena dentro de la caja
        q = np.linspace(0, 2 * math.pi, 30)
        line3(fr, [(0.2, cy_ + 0.18 * math.sin(x + a * on), 0.18 * math.cos(x + a * on)) for x in q], col=ACTIVO if on > 0.5 else GRIS,
              w=2.4, a=0.9, glow=1.0)
    line3(fr, [(0.2, 1.1 + 0.2, 0.0), (0.2, 0.3 + 0.2, 0.1)], col=ACTIVO if lk > 0.5 else GRIS, w=3, a=0.8, glow=0.8)
    line3(fr, [(0.2, 1.1 - 0.2, 0.0), (0.2, 0.3 - 0.2, 0.1)], col=ACTIVO if lk > 0.5 else GRIS, w=3, a=0.8, glow=0.8)
    pa = fr.cam.p1((1.9, 1.25, 0))
    pf = fr.cam.p1((1.9, 0.15, 0.1))

    def ui(img, fx):
        kicker(img, 'CAJA DE TRANSFERENCIA', 150, seg(u, uc, uc + 0.25), col=AZULC)
        if u > uc - 0.1:
            photo_card(img, fx, foto(), 800, 1180, 340, t - u + uc - 0.1, t, caption='Caja real · Gnangarra · CC BY 2.5', angle0=8.0)
        pill(img, fx, pa[0] - 60, pa[1] - 50, 'A LAS DE ATRÁS', eout(seg(u, 0.1, 0.35)), size=22, border=ACTIVO)
        pill(img, fx, pf[0] - 60, pf[1] + 60, 'A LAS DE ADELANTE', eout(seg(u, ua + 0.2, ua + 0.45)), size=22, border=ACTIVO)
        esquema(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.3, 0.3), amp=16)


# 6. y las cuatro jalan parejo, a la misma velocidad (rayos X: todo encendido; misma cifra en las 4)
def s_parejo(t, fi, u, d):
    uv = Wp(6, 'velocidad') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, 0, 60, ty=0.4), K(0.3, 6.4, 20, 46, ty=0.4), K(d, 6.3, 24, 44, ty=0.4)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.4)
    a = ang_rueda(t * 3.0)
    draw_objects(fr, troca(ang=(a, a, a, a), interior=True, act_f=1.0, act_r=1.0, lock=1.0, glow_f=1.0, glow_r=1.0),
                 xray=0.8, keep=('in', 'llanta', 'rin', 'rayo'))
    flujo(fr, t, 1.0, 1.0)
    pts = [fr.cam.p1((x, RW, z)) for x in (XF, XR) for z in (ZW + 0.3, -ZW - 0.3)]

    def ui(img, fx):
        kicker(img, 'LAS CUATRO', 150, seg(u, -0.1, 0.2), col=AZULC)
        for j, p in enumerate(pts):
            pill(img, fx, p[0], p[1], '100 rpm', eout(seg(u, uv - 0.2 + 0.08 * j, uv + 0.05 + 0.08 * j)), size=24, border=VERDE, dot=False)
        texto(img, fx, 540, 300, 'parejo', 90, VERDE, eout(seg(u, 0.4, 0.65)), f='serif', glow=0.5)
        esquema(img, fx, 1.0, y=1450, txt='ESQUEMA · CIFRAS DE EJEMPLO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. la prueba en el lodo: en dos, las de atrás patinan y se entierran
def s_lodo2(t, fi, u, d):
    up = Wp(7, 'patinan') - 0.1
    ue = Wp(7, 'entierran') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.6, -60, 10, ty=0.6), K(0.3, 5.6, -30, 8, ty=0.6), K(ue, 4.2, -150, 8, tx=-1.0, ty=0.4),
                          K(d, 4.1, -156, 8, tx=-1.0, ty=0.4)], cy=0.58))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    hund = 0.04 + 0.12 * seg(u, up, ue + 0.4)
    a = ang_rueda(t * 7.0)
    ms = []
    piso_lodo(ms)
    ms += colocar(troca(ang=(0, 0, a, a), hund=hund, glow_r=1.0), y=-0.02 * abs(math.sin(t * 22)))
    draw_objects(fr, ms)
    for z, s_ in ((ZW, 1), (-ZW, 2)):
        salpica(fr, t, XR, z, k=seg(u, up - 0.2, up), seed=s_, n=18)

    def ui(img, fx):
        kicker(img, 'LA PRUEBA · EN EL LODO', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.numero_golpe(img, fx, '2H', 320, seg(u, 0.4, 0.55), size=150, col=ACTIVO)
        pill(img, fx, 540, 1300, 'PATINAN', eout(seg(u, up, up + 0.2)), size=34, border=RED)
        pill(img, fx, 540, 1390, 'SE ENTIERRAN', eout(seg(u, ue, ue + 0.2)), size=28, border=LODO_C)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.25 * seg(u, up, d), amp=8)


# 8. en cuatro, las de adelante la jalan… y sale (salta y avanza)
def s_lodo4(t, fi, u, d):
    uj = Wp(8, 'jalan') - 0.1
    us = Wp(8, 'sale') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, -40, 10, ty=0.6, tx=0.5), K(0.3, 5.4, -20, 8, ty=0.6, tx=0.8), K(us, 6.0, 10, 8, ty=0.7, tx=2.0),
                          K(d, 6.0, 14, 8, ty=0.7, tx=2.2)], cy=0.58))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    sal = P.eout4(seg(u, us - 0.1, us + 0.8))
    xm = 2.0 * sal
    a = ang_rueda(t * 4.0)
    ms = []
    piso_lodo(ms)
    ms += colocar(troca(ang=(a, a, a, a), hund=0.16 * (1 - sal), glow_f=1.0, glow_r=1.0), x=xm, y=0.25 * math.sin(math.pi * sal))
    draw_objects(fr, ms)
    for x, z, s_ in ((XF, ZW, 3), (XF, -ZW, 4), (XR, ZW, 5)):
        salpica(fr, t, x + xm, z, k=seg(u, uj - 0.2, uj) * (1 - sal), seed=s_, n=10)
    pf = fr.cam.p1((XF + xm, RW + 0.7, ZW))

    def ui(img, fx):
        P.numero_golpe(img, fx, '4H', 320, seg(u, -0.2, -0.05), size=150, col=VERDE)
        pill(img, fx, pf[0], pf[1] - 30, 'LAS DE ADELANTE JALAN', eout(seg(u, uj, uj + 0.2)), size=26, border=VERDE)
        texto(img, fx, 540, 1330, '¡y sale!', 90, VERDE, eout(seg(u, us, us + 0.2)), f='serif', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.5, 0.35), amp=18)


# 9. el error: traerla metida en el pavimento (la troca en la calle con el «4H» prendido)
def s_error(t, fi, u, d):
    up = Wp(9, 'pavimento') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.0, 60, 12, ty=0.6), K(0.3, 6.0, 40, 10, ty=0.6), K(up, 5.0, 24, 8, ty=0.6), K(d, 4.9, 20, 8, ty=0.6)],
                      cy=0.62))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8, beam=0.5)
    ms = []
    piso_asfalto(fr, ms, t=t, vel=1.5)
    a = ang_rueda(t * 3.0)
    ms += troca(ang=(a, a, a, a), glow_f=0.6, glow_r=0.6)
    draw_objects(fr, ms)

    def ui(img, fx):
        texto(img, fx, 540, 250, 'EL ERROR', 110, RED, eout(seg(u, 0.0, 0.12)), glow=0.8)
        kicker(img, '4H METIDA EN LA CALLE', 370, seg(u, 0.2, 0.45), col=(255, 160, 150))
        kp = eout(seg(u, up, up + 0.2))
        pill(img, fx, 540, 1330, 'PAVIMENTO SECO', kp, size=32, border=(200, 200, 210))
        if kp > 0.01:
            dl = ImageDraw.Draw(img)
            dl.rounded_rectangle((440, 1180, 640, 1250), radius=14, outline=M.scale_c(VERDE, kp), width=4)
            texto(img, fx, 540, 1215, '4H', 44, VERDE, kp * (0.6 + 0.4 * math.sin(t * 8) ** 2), f='mono', glow=0.8)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.0, 0.35), amp=24)


# 10. en una curva, las llantas de adelante recorren más camino que las de atrás (vista desde arriba con sus huellas)
R_GIRO = 3.2
C_GIRO = np.array([XR, 0.0, -R_GIRO])
STEER = math.degrees(math.atan((XF - XR) / R_GIRO))


def pose_curva(phi):
    """Transforma un punto local de la troca cuando va girando (phi en rad) alrededor de C_GIRO."""
    c, s = math.cos(phi), math.sin(phi)
    pr = C_GIRO + R_GIRO * np.array([s, 0, c])

    def f(p):
        x, y, z = p[0] - XR, p[1], p[2]
        return pr + np.array([x * c + z * s, y, -x * s + z * c])
    return f


def s_curva(t, fi, u, d):
    uc = Wp(10, 'curva') - 0.1
    um = Wp(10, 'mas') - 0.1
    ua = Wp(10, 'atras') - 0.1
    phi = math.radians(80) * ease(seg(u, -0.2, ua))
    fr = Frame(camara(u, [K(-0.3, 9.0, 0, 84, ty=0.0, tx=0.5, tz=-1.2), K(0.3, 8.6, 10, 80, ty=0.0, tx=0.6, tz=-1.4),
                          K(d, 8.4, 14, 78, ty=0.0, tx=0.6, tz=-1.4)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.6)
    ms = []
    _B(ms, 12, 0.04, 9, ASFALTO, 0, -0.04, -1.5, name='asfalto', gloss=0.3)
    a = ang_rueda(phi * R_GIRO)
    tr_ = troca(ang=(a, a, a, a), steer=STEER)
    ms += P.tfk(tr_, ry=math.degrees(phi), t=tuple(pose_curva(phi)(np.zeros(3))))
    draw_objects(fr, ms)
    for (x, z), col, w in (((XF, ZW), (120, 230, 255), 6), ((XF, -ZW), (120, 230, 255), 6), ((XR, ZW), ACTIVO, 5), ((XR, -ZW), ACTIVO, 5)):
        pts = [pose_curva(p)(np.array([x, 0.02, z])) for p in np.linspace(0, phi, 40)]
        if len(pts) > 1 and phi > 0.01:
            line3(fr, pts, col=col, w=w, a=seg(u, uc, uc + 0.3), glow=1.2)
    pfm = fr.cam.p1(pose_curva(phi * 0.5)(np.array([XF, 0, ZW + 0.4])))
    prm = fr.cam.p1(pose_curva(phi * 0.5)(np.array([XR, 0, ZW - 0.2])))

    def ui(img, fx):
        kicker(img, 'EN UNA CURVA · VISTA DE ARRIBA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pfm[0] + 60, pfm[1] + 40, 'ADELANTE: MÁS CAMINO', eout(seg(u, um, um + 0.25)), size=24, border=(120, 230, 255))
        pill(img, fx, prm[0] - 20, prm[1] - 40, 'ATRÁS: MENOS', eout(seg(u, ua, ua + 0.25)), size=24, border=ACTIVO)
        esquema(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11-12. pero amarradas tienen que girar igual… y algo tiene que ceder: las dos flechas amarradas se tuercen
def _flechas(fr, t, u, tw, rojo=0.0, temb=0.0):
    for y, col0 in ((1.4, (120, 230, 255)), (0.4, ACTIVO)):
        c = M.mixc(col0, (255, 70, 50), rojo)
        dy = temb * 0.03 * math.sin(t * 70 + y)
        draw_objects(fr, [tubo((-2.2, y + dy, 0), (2.2, y + dy, 0), r=0.12, col=M.mixc((160, 164, 172), c, 0.3), name='flecha', gloss=0.8)])
        n = 140
        twist = 6 + 10 * tw if y > 1 else 6                   # la de adelante se enrosca más: está forzada
        pts = [(-2.2 + 4.4 * i / n, y + dy + 0.125 * math.sin(2 * math.pi * twist * i / n + t * 4),
                0.125 * math.cos(2 * math.pi * twist * i / n + t * 4)) for i in range(n + 1)]
        line3(fr, [p for p in pts if p[2] > 0], col=c, w=3, a=0.9, glow=1.0)
    _B_ms = []
    _B(_B_ms, 0.6, 1.5, 0.6, M.mixc((150, 154, 164), (255, 80, 60), rojo), -2.5, 0.15, 0, name='caja', gloss=0.6,
       glow=M.scale_c((255, 70, 50), 0.6 * rojo) if rojo > 0.02 else None)
    draw_objects(fr, _B_ms)


def tension(img, fx, x, y, w, lv, k=1.0, txt='TENSIÓN'):
    if k <= 0.01:
        return
    dl = ImageDraw.Draw(img)
    dl.rounded_rectangle((x, y, x + w, y + 46), radius=20, outline=M.scale_c(WHITE, k), width=3)
    col = M.mixc(VERDE, (255, 60, 40), clamp(lv))
    if lv > 0.01:
        dl.rounded_rectangle((x + 6, y + 6, x + 6 + (w - 12) * clamp(lv), y + 40), radius=14, fill=M.scale_c(col, k))
    texto(img, fx, x + w / 2, y + 90, txt, 28, GRIS, k, f='mono', glow=0.2)


def s_amarradas(t, fi, u, d):
    ui_ = Wp(11, 'igual') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, 30, 10, ty=0.9), K(0.3, 5.4, 10, 6, ty=0.9), K(d, 5.3, 6, 6, ty=0.9)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    tw = seg(u, 0.0, d)
    _flechas(fr, t, u, tw)
    pc = fr.cam.p1((-2.5, 1.85, 0))

    def ui(img, fx):
        kicker(img, 'AMARRADAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 330, 'FLECHA DE ADELANTE', 1.0, size=22, border=(120, 230, 255), dot=False)
        pill(img, fx, 540, 1230, 'FLECHA DE ATRÁS', 1.0, size=22, border=ACTIVO, dot=False)
        pill(img, fx, pc[0] + 60, pc[1] - 40, 'CAJA', 1.0, size=22, border=(200, 200, 210), dot=False)
        tension(img, fx, 240, 1320, 600, 0.2 + 0.5 * tw, k=eout(seg(u, 0.2, 0.45)))
        texto(img, fx, 540, 440, 'girar igual', 70, WHITE, eout(seg(u, ui_, ui_ + 0.25)), f='serif', glow=0.35)
        esquema(img, fx, 1.0, y=1470)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_ceder(t, fi, u, d):
    uc = Wp(12, 'ceder') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, -10, 6, ty=0.9), K(0.3, 4.0, -26, 8, ty=0.9), K(d, 3.9, -30, 8, ty=0.9)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    r = seg(u, -0.2, uc + 0.2)
    _flechas(fr, t, u, 1.0 + r, rojo=r, temb=r)

    def ui(img, fx):
        tension(img, fx, 240, 1320, 600, 0.7 + 0.3 * r, k=1.0)
        texto(img, fx, 540, 300, 'algo tiene que ceder', 66, (255, 110, 80), eout(seg(u, uc - 0.3, uc)), f='serif', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.3 + 0.5 * r, amp=10)


# 13. en el lodo, la llanta resbala tantito y no pasa nada (la tensión baja a verde)
def s_resbala(t, fi, u, d):
    ur = Wp(13, 'resbala') - 0.1
    un = Wp(13, 'nada') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.6, 50, 10, tx=1.3, ty=0.4, tz=0.7), K(0.3, 2.2, 20, 8, tx=1.3, ty=0.4, tz=0.7),
                          K(d, 2.15, 16, 8, tx=1.3, ty=0.4, tz=0.7)], cy=0.58))
    space(fr, t, floor=None, bokeh=0.8)
    ms = []
    piso_lodo(ms)
    desl = 0.08 * math.sin(t * 9) * seg(u, ur, ur + 0.2)
    a = ang_rueda(t * 2.0)
    ms += P.tfk(troca(ang=(a, a, a, a), steer=20), t=(desl, 0, 0))
    draw_objects(fr, ms)
    salpica(fr, t, XF + desl, ZW, k=0.6 * seg(u, ur, ur + 0.2), seed=7, n=8, sentido=1)

    def ui(img, fx):
        kicker(img, 'EN EL LODO', 150, seg(u, -0.1, 0.2), col=LODO_C)
        pill(img, fx, 540, 330, 'RESBALA TANTITO', eout(seg(u, ur, ur + 0.2)), size=32, border=LODO_C)
        tension(img, fx, 240, 1300, 600, 0.75 - 0.6 * seg(u, ur, un + 0.2), k=1.0, txt='TENSIÓN · SE SUELTA')
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. en pavimento seco no resbala (la llanta pegada al asfalto; la tensión se queda arriba)
def s_seco(t, fi, u, d):
    un = Wp(14, 'resbala') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.4, -40, 6, tx=1.3, ty=0.4, tz=0.7), K(0.3, 2.1, -10, 4, tx=1.3, ty=0.4, tz=0.7),
                          K(d, 2.05, -6, 4, tx=1.3, ty=0.4, tz=0.7)], cy=0.58))
    space(fr, t, floor=None, bokeh=0.8)
    ms = []
    piso_asfalto(fr, ms, t=t, vel=0.0)
    ms += troca(steer=20)
    draw_objects(fr, ms)
    for j in range(5):                                                  # «agarre»: marcas que se tensan
        line3(fr, [(XF - 0.3 + 0.15 * j, 0.012, ZW - 0.15), (XF - 0.25 + 0.15 * j, 0.012, ZW + 0.15)], col=WHITE, w=3,
              a=seg(u, un, un + 0.2), glow=0.6)

    def ui(img, fx):
        kicker(img, 'PAVIMENTO SECO', 150, seg(u, -0.1, 0.2), col=(200, 200, 210))
        P.numero_golpe(img, fx, 'NO RESBALA', 330, seg(u, un, un + 0.15), size=96, col=RED)
        tension(img, fx, 240, 1300, 600, 0.6 + 0.4 * seg(u, 0.0, d), k=1.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.15, 0.3), amp=18)


# 15. la troca brinca, rechina y la dirección se pone dura («BRINCA» de cristal, saltitos, marcas de llanta y volante)
def s_brinca(t, fi, u, d):
    ub = Wp(15, 'brinca') - 0.1
    ur = Wp(15, 'rechina') - 0.1
    ud = Wp(15, 'dura') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.0, 60, 14, ty=0.6), K(0.3, 6.2, 36, 10, ty=0.6), K(ud - 0.6, 5.8, 20, 10, ty=0.7),
                          K(d, 5.7, 16, 10, ty=0.7)], cy=0.64))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, 'BRINCA', u, t0=ub - 0.1, cy=0.33, entrada='zoom')
    salto = abs(math.sin(t * 11)) * 0.12 * seg(u, ub, ub + 0.2)
    ms = []
    piso_asfalto(fr, ms, t=t, vel=0.0)
    ms += P.tfk(troca(steer=22), rz=2.5 * math.sin(t * 11) * seg(u, ub, ub + 0.2), t=(0, salto, 0))
    draw_objects(fr, ms)
    if u > ur:
        for z in (ZW, -ZW):
            line3(fr, [(XF - 0.2 - 1.2 * seg(u, ur, d) * j / 4, 0.012, z + 0.1 * math.sin(j)) for j in range(5)], col=(20, 20, 22),
                  w=10, a=0.9, glow=0.0)
            for j in range(3):                                         # el rechinido (ondas)
                r_ = 0.2 + ((t * 3 + j / 3) % 1.0) * 0.8
                q = np.linspace(-0.6, 0.6, 12)
                line3(fr, [(XF + r_ * math.cos(a), 0.05 + r_ * math.sin(a) * 0.5, z + r_ * math.sin(a) * 0.3) for a in q], col=AMARILLO,
                      w=2.4, a=0.6 * (1 - ((t * 3 + j / 3) % 1.0)), glow=1.0)

    def ui(img, fx):
        kicker(img, '4H EN SECO', 150, seg(u, -0.1, 0.2), col=(255, 160, 150))
        pill(img, fx, 330, 1250, 'RECHINA', eout(seg(u, ur, ur + 0.2)), size=28, border=AMARILLO)
        kd = eout(seg(u, ud, ud + 0.2))
        if kd > 0.01:                                                     # volante duro
            cx, cy, r = 760, 1280, 100
            dl = ImageDraw.Draw(img)
            ag = 0.25 * math.sin(t * 40) * kd
            dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(WHITE, kd), width=12)
            for b in (math.pi / 2, math.pi * 7 / 6, -math.pi / 6):
                dl.line([(cx, cy), (cx + r * math.cos(b + ag), cy + r * math.sin(b + ag))], fill=M.scale_c(WHITE, kd), width=10)
            texto(img, fx, cx, cy + r + 50, 'DURA', 40, RED, kd, f='mono', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.4 * seg(u, ub, ub + 0.2) * abs(math.sin(t * 11)), amp=14)


# 16. esa tensión castiga la caja de transferencia, las crucetas y los ejes (se ponen rojos uno por uno)
def s_castiga(t, fi, u, d):
    uc = Wp(16, 'caja') - 0.1
    ucr = Wp(16, 'crucetas') - 0.1
    ue = Wp(16, 'ejes') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.4, 30, 40, ty=0.4), K(0.3, 5.2, 10, 30, ty=0.4), K(uc, 3.4, 20, 26, ty=0.4, tx=X_TC),
                          K(ucr, 3.8, -20, 20, ty=0.4, tx=-0.4), K(ue, 5.4, -10, 30, ty=0.4), K(d, 5.3, -6, 30, ty=0.4)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.3)
    rc = seg(u, uc, uc + 0.2)
    re_ = seg(u, ue, ue + 0.2)
    ms = troca(interior=True, act_f=1.0, act_r=1.0, lock=1.0)
    for m in ms:
        if m.name == 'in' and rc > 0 and abs(np.asarray(m.V)[:, 0].mean() - X_TC) < 0.2:
            m.glow = M.scale_c((255, 70, 50), 0.8 * rc)
        if m.name == 'in' and re_ > 0 and abs(np.asarray(m.V)[:, 2]).max() > 0.4:
            m.glow = M.scale_c((255, 70, 50), 0.7 * re_)
    draw_objects(fr, ms, xray=0.85, keep=('in', 'llanta', 'rin', 'rayo'))
    kcr = seg(u, ucr, ucr + 0.2)
    for p in ((X_TC - 0.18, 0.5, 0.0), (XR + 0.17, RW, 0.0), (X_TC + 0.18, 0.5, 0.2), (XF - 0.17, RW, 0.2)):
        dot3(fr, p, r=12 + 4 * math.sin(t * 9) ** 2, col=(255, 80, 50), a=kcr, glow=2.0)
    pt = fr.cam.p1((X_TC, 0.85, 0.05))
    px = fr.cam.p1((XR + 0.17, RW + 0.3, 0.0))
    pe = fr.cam.p1((XF, RW, ZW + 0.2))

    def ui(img, fx):
        kicker(img, 'LO QUE SE DESGASTA', 150, seg(u, -0.1, 0.2), col=(255, 160, 150))
        pill(img, fx, pt[0], pt[1] - 40, 'CAJA DE TRANSFERENCIA', eout(seg(u, uc, uc + 0.2)), size=22, border=RED)
        pill(img, fx, px[0], px[1] - 60, 'CRUCETAS', eout(seg(u, ucr, ucr + 0.2)), size=24, border=RED)
        pill(img, fx, pe[0], pe[1] + 70, 'EJES', eout(seg(u, ue, ue + 0.2)), size=26, border=RED)
        esquema(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, uc, 0.25), golpe_k(u, ucr, 0.25), golpe_k(u, ue, 0.25)), amp=14)


# 17. por eso el manual dice: (el manual cae y se abre)
def s_manual(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 30, 50, ty=0.1), K(0.3, 3.0, 6, 56, ty=0.1), K(d, 2.95, 2, 56, ty=0.1)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9, beam=0.6)
    e = P.entrada(u, -0.25, 0.3, 'cae')
    ab = P.resorte(seg(u, 0.1, 0.5))
    ms = []
    _B(ms, 0.8, 0.06, 1.1, (150, 148, 142), -0.4, 0, 0, name='hoja', gloss=0.3)
    tapa = named(M3.box(0.8, 0.06, 1.1, (40, 60, 110), shadow=0, base=True, gloss=0.6).tf(t=(-0.4, 0, 0)), 'tapa', rim=0.7)
    tapa = tapa.tf(rz=-180 * (1 - ab))
    ms.append(named(tapa, 'tapa', rim=0.7, gloss=0.6))
    _B(ms, 0.8, 0.06, 1.1, (150, 148, 142), 0.4, 0, 0, name='hoja', gloss=0.3)
    draw_objects(fr, P.tfk(ms, t=(0, -e['dy'] * 0.3, 0)))
    for j in range(5):
        for x0 in (-0.7, 0.1):
            line3(fr, [(x0, 0.07, -0.4 + 0.18 * j), (x0 + 0.55 * (0.5 + 0.5 * math.sin(j * 3 + x0)), 0.07, -0.4 + 0.18 * j)], col=GRIS,
                  w=3, a=ab, glow=0.2)

    def ui(img, fx):
        texto(img, fx, 540, 300, 'el manual dice', 80, WHITE, eout(seg(u, 0.05, 0.3)), f='serif', glow=0.35)
        kicker(img, 'MANUAL DEL PROPIETARIO', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.05, 0.3), amp=12)


# 18. 4x4 solo en tierra, lodo, arena o nieve (el piso cambia con cada palabra; «TIERRA» de cristal)
SUP = [('tierra', (150, 110, 70), 'TIERRA'), ('lodo', LODO, 'LODO'), ('arena', (214, 186, 130), 'ARENA'), ('nieve', (232, 238, 246), 'NIEVE')]


def s_superficies(t, fi, u, d):
    us = [Wp(18, w) - 0.1 for w, _, _ in SUP]
    fr = Frame(camara(u, [K(-0.3, 6.6, -50, 14, ty=0.6), K(0.3, 6.0, -20, 12, ty=0.6), K(us[2], 6.0, 20, 12, ty=0.6),
                          K(d, 5.9, 26, 12, ty=0.6)], cy=0.62))
    space(fr, t, floor=None, bokeh=0.9, beam=0.4)
    M.cristal(fr.base, fr.fx, 'TIERRA', u, t0=-0.3, cy=0.33, entrada='golpe')
    cual = max([0] + [j for j, x in enumerate(us) if u >= x])
    ms = []
    _B(ms, 9, 0.06, 6, SUP[cual][1], 0, -0.06, 0, name='piso', gloss=0.5)
    a = ang_rueda(t * 2.0)
    ms += troca(ang=(a, a, a, a), glow_f=0.6, glow_r=0.6)
    draw_objects(fr, ms)
    if cual == 3:
        for j in range(30):
            ph = (t * 0.4 + j / 30) % 1.0
            dot3(fr, ((j * 0.37) % 6 - 3, 3.0 - 3.0 * ph, (j * 0.53) % 3 - 1.5), r=4, col=WHITE, a=0.8, glow=0.6)

    def ui(img, fx):
        kicker(img, 'SOLO EN', 150, 1.0, col=AZULC)
        for j, (w, col, lab) in enumerate(SUP):
            kx = eout(seg(u, us[j], us[j] + 0.15))
            pill(img, fx, 190 + 233 * j, 1290, lab, kx, size=26, border=col, dot=False)
        if u > us[3] + 0.4:
            P.pill_tachada(img, fx, 540, 1390, 'PAVIMENTO', seg(u, us[3] + 0.4, us[3] + 0.6), seg(u, us[3] + 0.7, us[3] + 1.0), t, size=28)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, us[1], 0.2), golpe_k(u, us[2], 0.2), golpe_k(u, us[3], 0.2)), amp=10)


# 19. y en 4 baja, muchos manuales piden no pasar de 40 km/h (velocímetro que se clava en 40; «40 KM/H» de cristal)
def s_cuarenta(t, fi, u, d):
    ub = Wp(19, 'baja') - 0.1
    u4 = Wp(19, 'cuarenta') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.8, 40, 10, ty=1.0), K(0.3, 6.0, 20, 8, ty=1.0), K(d, 5.9, 16, 8, ty=1.0)], cy=0.74))
    space(fr, t, floor=None, bokeh=0.9, beam=0.3)
    M.cristal(fr.base, fr.fx, '40 KM/H', u, t0=u4 - 0.1, cy=0.3, entrada='zoom')
    ms = []
    _B(ms, 9, 0.06, 6, (150, 110, 70), 0, -0.06, 0, name='piso', gloss=0.4)
    a = ang_rueda(t * 1.0)
    ms += colocar(troca(ang=(a, a, a, a), glow_f=0.5, glow_r=0.5), rz=14, y=0.3)
    draw_objects(fr, P.tfk(ms, rz=0))

    def ui(img, fx):
        kicker(img, '4L · CUATRO BAJA', 150, seg(u, ub, ub + 0.2), col=AZULC)
        cx, cy, r = 540, 1000, 160
        dl = ImageDraw.Draw(img)
        dl.arc((cx - r, cy - r, cx + r, cy + r), 150, 390, fill=(220, 220, 226), width=8)
        dl.arc((cx - r, cy - r, cx + r, cy + r), 150 + 240 * 40 / 120, 390, fill=(255, 70, 50), width=14)
        for v in range(0, 121, 20):
            ag = math.radians(150 + 240 * v / 120)
            dl.line([(cx + (r - 26) * math.cos(ag), cy + (r - 26) * math.sin(ag)), (cx + r * math.cos(ag), cy + r * math.sin(ag))],
                    fill=WHITE, width=4)
        vel = 40 * P.resorte(seg(u, u4 - 0.5, u4 + 0.2)) if u > u4 - 0.5 else 0
        ag = math.radians(150 + 240 * vel / 120)
        dl.line([(cx, cy), (cx + (r - 30) * math.cos(ag), cy + (r - 30) * math.sin(ag))], fill=AMARILLO, width=9)
        texto(img, fx, cx, cy + 70, f'{vel:.0f}', 70, WHITE, 1.0, f='mono', glow=0.4)
        texto(img, fx, cx, cy + 130, 'KM/H', 26, GRIS, 1.0, f='mono', glow=0.2)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u4 + 0.1, 0.3), amp=14)


# 20. mándaselo a quien trae la 4x4 metida en la ciudad (la troca en la calle con edificios de línea)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.0, -60, 10, ty=1.0), K(0.4, 7.0, -30, 8, ty=1.0), K(d, 6.8, -24, 8, ty=1.0)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.9, beam=0.0)
    ms = []
    piso_asfalto(fr, ms, t=t, vel=2.0)
    a = ang_rueda(t * 3.0)
    ms += troca(ang=(a, a, a, a), glow_f=0.6, glow_r=0.6)
    draw_objects(fr, ms)
    for j, (x, h) in enumerate(((-4, 3.0), (-2.4, 4.2), (-0.6, 2.6), (1.2, 3.6), (3.0, 4.6))):   # edificios de línea
        for z in (-3.0,):
            q = [(x, 0, z), (x, h, z), (x + 1.4, h, z), (x + 1.4, 0, z)]
            line3(fr, q, col=WHITE, w=2, a=0.5 * seg(u, 0.0, 0.3), glow=0.4)
            for k in range(int(h / 0.6)):
                line3(fr, [(x + 0.2, 0.4 + k * 0.6, z), (x + 1.2, 0.4 + k * 0.6, z)], col=AMARILLO, w=1.6, a=0.3 * seg(u, 0.0, 0.3), glow=0.4)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien trae', 'sans'), ('la 4x4 metida en la ciudad.', 'serif')], 230, seg(u, 0.0, 0.15), size=60)
        dl = ImageDraw.Draw(img)
        kp = eout(seg(u, 0.4, 0.6))
        dl.rounded_rectangle((440, 1250, 640, 1320), radius=14, outline=M.scale_c(VERDE, kp), width=4)
        texto(img, fx, 540, 1285, '4H', 44, VERDE, kp * (0.6 + 0.4 * math.sin(t * 8) ** 2), f='mono', glow=0.8)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-1.5, 'whoosh_suave', 0.4), (-0.2, 'whoosh', 0.8), (U_CHOQUE, 'sub', 1.0), (U_CHOQUE, 'bass', 0.9),
                     (0.3, 'bass', 0.6), (2.0, 'scribble', 0.6)]),
           dict(desde=1, fn=s_parcial, tr='cubo', sfx=[(0.1, 'shimmer', 0.5), (0.6, 'click', 0.5), (2.6, 'sub', 0.8), (2.6, 'bass', 0.6)]),
           dict(desde=2, fn=s_atras, tr='deslizar', sfx=[(0.2, 'whoosh', 0.5), (0.3, 'tick', 0.5)]),
           dict(desde=3, fn=s_paseo, tr='whip_izq', sfx=[(0.6, 'scribble', 0.5), (2.2, 'tick2', 0.5)]),
           dict(desde=4, fn=s_palanca, tr='iris', c=(0.5, 0.5), sfx=[(0.6, 'click', 1.0), (0.7, 'thud', 0.7), (1.3, 'click', 0.8)]),
           dict(desde=5, fn=s_transfer, tr='zoom', c=(0.45, 0.6), sfx=[(0.1, 'slap', 0.7), (1.3, 'click', 0.9), (1.4, 'bass', 0.7)]),
           dict(desde=6, fn=s_parejo, tr='rebanadas', sfx=[(1.4, 'chime_a', 0.4), (1.5, 'chime_b', 0.4), (1.6, 'chime_c', 0.4)]),
           dict(desde=7, fn=s_lodo2, tr='cubo_izq', sfx=[(0.5, 'bass', 0.6), (1.3, 'whoosh', 0.5), (2.6, 'thud', 0.8)]),
           dict(desde=8, fn=s_lodo4, tr='wipe', sfx=[(0.0, 'bass', 0.6), (1.6, 'whoosh', 0.8), (2.3, 'thud', 0.9)]),
           dict(desde=9, fn=s_error, tr='rompe', c=(0.5, 0.35), sfx=[(0.0, 'bass', 0.9), (0.0, 'digital', 0.5), (2.7, 'click', 0.7)]),
           dict(desde=10, fn=s_curva, tr='giro', sfx=[(0.1, 'whoosh_suave', 0.6), (1.6, 'chime_a', 0.5), (3.2, 'chime_b', 0.5)]),
           dict(desde=11, fn=s_amarradas, tr='cristal', palabra='IGUAL', sfx=[(0.4, 'riser', 0.5), (1.3, 'tick', 0.5)]),
           dict(desde=12, fn=s_ceder, tr='glitch', sfx=[(0.3, 'sub', 0.9), (0.8, 'burst', 0.6)]),
           dict(desde=13, fn=s_resbala, tr='remolino', sfx=[(0.8, 'whoosh', 0.5), (2.4, 'chime_a', 0.4)]),
           dict(desde=14, fn=s_seco, tr='golpe', sfx=[(1.0, 'sub', 0.9), (1.0, 'bass', 0.8)]),
           dict(desde=15, fn=s_brinca, tr='flash', sfx=[(0.4 + 0.29 * j, 'thud', 0.6) for j in range(8)] + [(1.1, 'scribble', 0.5),
                                                                                                         (2.8, 'bass', 0.7)]),
           dict(desde=16, fn=s_castiga, tr='push', c=(0.5, 0.55), sfx=[(1.2, 'bass', 0.8), (2.6, 'bass', 0.8), (3.4, 'bass', 0.8)]),
           dict(desde=17, fn=s_manual, tr='deslizar_abajo', sfx=[(0.05, 'slap', 0.9), (0.3, 'whoosh_suave', 0.5)]),
           dict(desde=18, fn=s_superficies, tr='mosaico', sfx=[(0.0, 'shimmer', 0.4), (1.4, 'tick', 0.6), (2.1, 'tick', 0.6),
                                                                (2.9, 'tick', 0.6), (3.4, 'tick', 0.6), (4.0, 'scribble', 0.5)]),
           dict(desde=19, fn=s_cuarenta, tr='whip', sfx=[(0.6, 'click', 0.6), (2.9, 'bass', 0.8), (3.0, 'chime_b', 0.5)]),
           dict(desde=20, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7), (0.5, 'click', 0.6)]),
           dict(desde=21, loop=True, tr='zoom')]

if __name__ == '__main__':
    montaje.cli(globals())
