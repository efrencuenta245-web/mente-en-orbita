"""Reel diario jue 26-nov-2026 18:00 (propuesto) — «Tu parabrisas no es vidrio… es sándwich.»
El parabrisas es vidrio laminado: dos vidrios con una capa de plástico (PVB) en medio, pegados con calor y presión; por eso
una piedra deja una estrellita y no se cae en pedazos (Jalopnik; Motor.es). Las ventanas de los lados son de vidrio
templado: con un golpe se hacen cubitos sin filo, a propósito, para cortar menos y poder salir en una emergencia (Jalopnik).
El laminado retiene los pedazos y evita que salgas disparado (NHTSA, carta de interpretación sobre vidrios). Orgullo
mexicano: Vitro (Nuevo León) hace vidrio automotriz laminado y templado y vende en México, EE. UU., Canadá, Europa y
Sudamérica (vitro.com). Error (segundo gancho): echarle agua caliente al parabrisas congelado (choque térmico: por fuera se
calienta y se estira y por dentro sigue helado → se rompe; Motor1); una estrellita sin reparar se vuelve grieta de lado a
lado en una noche de frío y la calefacción a todo directo al vidrio frío hace lo mismo (Safelite, 2-abr-2026). Mejor:
calefacción suave y quitar el hielo con calma; daños de menos de 6 pulgadas (~15 cm) se pueden reparar (Safelite).
Comunidad: automovilistas (heladas). Inicio tipo 2 (cae y rebota): la piedrita cae, rebota en el parabrisas, deja la
estrellita con sacudida y el título se estrella («SÁNDWICH» de cristal detrás).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Datos y fuentes: guiones/2026-11-26_parabrisas.txt. Sin fotos reales (todo es esquema sin marca).
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import texto, esquema, golpe_k, sacudir, K, camara, _B, tubo
import velocimetro as V
import vin as VI
import llanta as LL

M3 = M.M3
_NF = [0]


def finish(fr, fi=0, **kw):
    """motor2.finish + rompe el ciclo fr → ui → fr (si no, cada cuadro se queda en memoria y el render se cae)."""
    import gc
    out = M.finish(fr, fi, **kw)
    fr.ui.clear()
    _NF[0] += 1
    if _NF[0] % 40 == 0:
        gc.collect()
    return out


TEMA = 'parabrisas'
TXT = ['Tu parabrisas no es vidrio… es sándwich.',
       'Son dos vidrios con una capa de plástico transparente en medio,',
       'el PVB, pegados con calor y presión.',
       'Por eso, cuando le pega una piedra, queda una estrellita…',
       'pero no se cae en pedazos.',
       'Ahora mira la ventana de un lado:',
       'esa es de vidrio templado, y con un golpe se hace cubitos.',
       'Y es a propósito: cubitos sin filo que cortan menos,',
       'y por ahí puedes salir en una emergencia.',
       'El parabrisas, en cambio, aguanta:',
       'el plástico agarra los pedazos y te mantiene adentro en un choque.',
       'Y aquí está el error:',
       'echarle agua caliente al parabrisas congelado.',
       'Por fuera el vidrio se calienta y se estira de golpe,',
       'pero por dentro sigue helado… y truena.',
       'Si ya tenía una estrellita,',
       'el frío de una noche la puede volver una grieta de lado a lado.',
       'Y la calefacción a todo, directo al vidrio helado, hace lo mismo.',
       'Mejor prende el carro, calefacción suave, y quita el hielo despacio.',
       'Y la estrellita, repárala pronto:',
       'un daño de menos de 15 cm todavía se puede reparar sin cambiar el parabrisas.',
       'Y uno de los que los fabrica es mexicano:',
       'Vitro, de Nuevo León, los vende en México, Estados Unidos, Canadá y Europa.',
       'Mándaselo a quien le echa agua caliente al parabrisas congelado.',
       'Porque tu parabrisas no es vidrio… es sándwich.']
VOZ = ['Tu parabrisas no es vidrio... es sándwich.',
       'Son dos vidrios con una capa de plástico transparente en medio,',
       'el PVB, pegados con calor y presión.',
       'Por eso, cuando le pega una piedra, queda una estrellita...',
       'pero no se cae en pedazos.',
       'Ahora mira la ventana de un lado:',
       'esa es de vidrio templado, y con un golpe se hace cubitos.',
       'Y es a propósito: cubitos sin filo que cortan menos,',
       'y por ahí puedes salir en una emergencia.',
       'El parabrisas, en cambio, aguanta:',
       'el plástico agarra los pedazos y te mantiene adentro en un choque.',
       'Y aquí está el error:',
       'echarle agua caliente al parabrisas congelado.',
       'Por fuera el vidrio se calienta y se estira de golpe,',
       'pero por dentro sigue helado... y truena.',
       'Si ya tenía una estrellita,',
       'el frío de una noche la puede volver una grieta de lado a lado.',
       'Y la calefacción a todo, directo al vidrio helado, hace lo mismo.',
       'Mejor prende el carro, calefacción suave, y quita el hielo despacio.',
       'Y la estrellita, repárala pronto:',
       'un daño de menos de quince centímetros todavía se puede reparar sin cambiar el parabrisas.',
       'Y uno de los que los fabrica es mexicano:',
       'Vitro, de Nuevo León, los vende en México, Estados Unidos, Canadá y Europa.',
       'Mándaselo a quien le echa agua caliente al parabrisas congelado.',
       'Porque tu parabrisas no es vidrio... es sándwich.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_parabrisas.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-26_parabrisas_words.json')

AMARILLO = (255, 236, 160)
AMBAR = (255, 190, 90)
NARANJA = (255, 130, 50)
ROJO = (240, 50, 42)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (90, 220, 140)
CARRO = (150, 26, 32)
VIDRIO = (120, 160, 182)
VID_OSC = (16, 24, 34)
PVB_C = (236, 196, 110)
HIELO = (210, 238, 255)
CROMO = (205, 208, 215)
CONCRETO = (110, 110, 112)

# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    if not os.path.exists(WORDS):
        for i, f in enumerate(VOZ):
            _WT[i] = [0.3 * k for k in range(len(f.split()))]
        return _WT
    import difflib
    d = json.load(open(WORDS))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(montaje._norm(w.get('text', '')), float(w['start'])) for w in d
          if w.get('type', 'word') == 'word' and montaje._norm(w.get('text', ''))]
    sw = []
    for i, f in enumerate(VOZ):
        for w in f.split():
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
    ws_ = [montaje._norm(w) for w in VOZ[i].split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws_) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ el frente del carro con su parabrisas (mira hacia +z)
TILT = 32.0
_T = math.radians(TILT)
C_WS = np.array([0.0, 1.0, 0.0])
EX = np.array([1.0, 0, 0])
EY = np.array([0, math.cos(_T), -math.sin(_T)])
EN = np.array([0, math.sin(_T), math.cos(_T)])
WW, WH = 0.95, 0.52
STAR = (0.28, 0.12)            # dónde pega la piedra (coordenadas del parabrisas, −1 a 1)


def ws(uu, vv, off=0.0):
    return tuple(C_WS + EX * uu * WW + EY * vv * WH + EN * off)


def _placa(th, col, off, name, gloss=0.95, rim=0.9, s=1.0):
    m = M3.box(2 * WW * s, 2 * WH * s, th, col, shadow=0, gloss=gloss, base=False).tf(rx=-TILT)
    return named(m.tf(t=tuple(C_WS + EN * off)), name, rim=rim, gloss=gloss)


def capas(sep=0.0, caliente=0.0, frio=0.0, oscuro=False):
    """Las 3 capas del parabrisas: vidrio de afuera, PVB y vidrio de adentro (sep las separa en vista explotada)."""
    vid = VID_OSC if oscuro else VIDRIO
    c_out = M.mixc(M.mixc(vid, (230, 80, 50), caliente), (62, 80, 94) if oscuro else HIELO, frio)
    out = _placa(0.035, c_out, 0.03 + sep, 'vidrio', gloss=0.18 if oscuro else 0.95)
    if caliente > 0.05:
        out.glow = M.scale_c((255, 90, 40), 0.5 * caliente)
    pv = _placa(0.012, PVB_C, 0.0, 'pvb', gloss=0.4, rim=0.6)
    if sep > 0.01 or not oscuro:
        pv.glow = M.scale_c(PVB_C, 0.15 + 0.35 * clamp(sep * 3))
    inn = _placa(0.035, M.mixc(vid, (120, 170, 255), 0.0 if oscuro else frio), -0.03 - sep, 'vidrio', gloss=0.18 if oscuro else 0.95)
    return [out, pv, inn]


def frente(sep=0.0, col=CARRO, caliente=0.0, frio=0.0, carro=True):
    ms = capas(sep, caliente, frio, oscuro=carro)
    if not carro:
        return ms
    yb = C_WS[1] - WH * math.cos(_T)
    zb = WH * math.sin(_T)
    ms.append(named(M3.rbox(2.3, 0.1, 0.95, 0.05, col, n=4, shadow=0, gloss=0.8).tf(rx=7, t=(0, yb - 0.1, zb + 0.45)), 'cofre', rim=0.8, gloss=0.8))
    ms.append(named(M3.rbox(2.2, 0.07, 1.2, 0.04, col, n=4, shadow=0, gloss=0.8).tf(t=(0, C_WS[1] + WH * math.cos(_T) + 0.01, -zb - 0.6)), 'techo', rim=0.8, gloss=0.8))
    for s_ in (-1, 1):
        ms.append(tubo(ws(s_ * 1.04, -1.04, 0.0), ws(s_ * 1.04, 1.04, 0.0), r=0.055, col=col, name='poste', gloss=0.8))
    ms.append(tubo(ws(-1.05, -1.06), ws(1.05, -1.06), r=0.04, col=(30, 30, 34), name='base', gloss=0.3))
    for x0 in (-0.85, 0.05):
        ms.append(tubo(ws(x0, -0.92, 0.06), ws(x0 + 0.75, -0.62, 0.06), r=0.012, col=(20, 20, 22), name='limpia', gloss=0.4))
    for s_ in (-1, 1):
        _B(ms, 0.36, 0.1, 0.06, (255, 246, 226), s_ * 0.8, yb - 0.2, zb + 0.93, name='faro', glow=(140, 130, 110))
    return ms


def piedra(p, s=1.0, rot=0.0):
    m = M3.sphere(0.07 * s, (130, 124, 116), nu=14, nv=9, shadow=0, gloss=0.3)
    v = np.asarray(m.V, float)
    rng = np.random.RandomState(3)
    v = v * (1 + 0.22 * rng.rand(len(v), 1))
    m.V = v
    return named(m.tf(ry=rot, rz=rot * 0.7, t=tuple(p)), 'piedra', rim=0.5)


def estrella(img, fx, x, y, R, k, seed=1, col=WHITE):
    """Estrellita de piedra (2D): grietas radiales con quiebres y 2 anillos rotos."""
    if k <= 0.01 or R < 2:
        return
    rng = np.random.RandomState(seed)
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    kk = eout(k)
    c = M.scale_c(col, 0.95)
    for j in range(11):
        a = j * 2 * math.pi / 11 + rng.uniform(-0.2, 0.2)
        L = R * rng.uniform(0.45, 1.0) * kk
        pts = [(x, y)]
        for s in np.linspace(0.25, 1, 4):
            aa = a + rng.uniform(-0.18, 0.18)
            pts.append((x + L * s * math.cos(aa), y + L * s * math.sin(aa)))
        d.line(pts, fill=c, width=3)
        df.line(pts, fill=M.scale_c(AZULC, 0.5), width=7)
    for rr in (0.32, 0.6):
        for j in range(5):
            a0 = rng.uniform(0, 360)
            r = R * rr * kk
            d.arc((x - r, y - r, x + r, y + r), a0, a0 + rng.uniform(25, 55), fill=c, width=2)
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=WHITE)
    df.ellipse((x - 26, y - 26, x + 26, y + 26), fill=M.scale_c(WHITE, 0.6))


def _ruta_grieta(seed=5):
    rng = np.random.RandomState(seed)
    izq, der = [STAR], [STAR]
    for s in np.linspace(0.08, 1, 16):
        izq.append((STAR[0] + (-0.99 - STAR[0]) * s, STAR[1] + 0.12 * s + rng.uniform(-0.05, 0.05)))
        der.append((STAR[0] + (0.99 - STAR[0]) * s, STAR[1] - 0.2 * s + rng.uniform(-0.05, 0.05)))
    return izq, der


GRIETA = _ruta_grieta()


def grieta(img, fx, fr, k, off=0.04, col=WHITE):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    for ruta in GRIETA:
        n = max(2, int(len(ruta) * clamp(k)))
        pts = [fr.cam.p1(ws(a, b, off))[:2] for a, b in ruta[:n]]
        d.line(pts, fill=col, width=4)
        df.line(pts, fill=M.scale_c(AZULC, 0.6), width=10)


def escarcha(img, fx, fr, k, seed=2, n=70, off=0.05):
    """Escarcha sobre el parabrisas: velo blanco + cristalitos (2D)."""
    if k <= 0.01:
        return
    poly = [fr.cam.p1(ws(a, b, off))[:2] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lay = Image.new('L', img.size, 0)
    ImageDraw.Draw(lay).polygon(poly, fill=int(55 * clamp(k)))
    img.paste(Image.new('RGB', img.size, HIELO), (0, 0), lay)
    rng = np.random.RandomState(seed)
    d = ImageDraw.Draw(img)
    for j in range(n):
        a, b = rng.uniform(-0.95, 0.95), rng.uniform(-0.92, 0.92)
        x, y, _ = fr.cam.p1(ws(a, b, off))
        r = rng.uniform(5, 13) * clamp(k * 1.5 - j / n * 0.5)
        if r < 1.5:
            continue
        for q in range(3):
            ang = q * math.pi / 3 + j
            d.line([(x - r * math.cos(ang), y - r * math.sin(ang)), (x + r * math.cos(ang), y + r * math.sin(ang))], fill=WHITE, width=2)


def p_star(fr, off=0.04):
    return fr.cam.p1(ws(STAR[0], STAR[1], off))


# ------------------------------------------------------------------ ventana de lado (templada) y sus cubitos
def puerta(cubos=0.0, sin_vidrio=False, col=CARRO, seed=4):
    ms = []
    ms.append(named(M3.rbox(1.6, 0.75, 0.1, 0.05, col, n=4, shadow=0, gloss=0.8).tf(t=(0, 0.0, 0)), 'puerta', rim=0.8, gloss=0.8))
    ms.append(tubo((0.45, 0.5, 0.07), (0.7, 0.5, 0.07), r=0.025, col=CROMO, name='manija'))
    for a, b in (((-0.78, 0.75, 0), (-0.55, 1.35, 0)), ((-0.55, 1.35, 0), (0.78, 1.35, 0)), ((0.78, 1.35, 0), (0.78, 0.75, 0))):
        ms.append(tubo(a, b, r=0.035, col=(30, 30, 34), name='marco', gloss=0.4))
    if sin_vidrio:
        return ms
    if cubos <= 0.001:
        v = M3.box(1.45, 0.58, 0.02, VID_OSC, shadow=0, gloss=0.18, base=False)
        ms.append(named(v.tf(t=(0.08, 1.05, 0.0)), 'ventana', rim=0.9, gloss=0.95))
        return ms
    rng = np.random.RandomState(seed)
    k = cubos
    for i in range(16):
        for j in range(7):
            x = -0.62 + 1.4 * (i + 0.5) / 16
            y = 0.78 + 0.55 * (j + 0.5) / 7
            if x < -0.62 + (y - 0.78) * 0.35:
                continue
            vz = rng.uniform(0.6, 1.8)
            vx = (x - 0.08) * rng.uniform(0.4, 1.2)
            p = (x + vx * k, y + rng.uniform(-0.2, 0.6) * k - 2.4 * k * k, vz * k)
            c = M.mixc(VIDRIO, (200, 230, 240), rng.rand() * 0.5)
            b = M3.box(0.075, 0.07, 0.03, c, shadow=0, gloss=0.95, base=False).tf(rx=rng.uniform(-400, 400) * k, ry=rng.uniform(-400, 400) * k, t=p)
            ms.append(named(b, 'cubito', rim=0.9, gloss=0.95))
    return ms


def martillo(k=1.0):
    ms = []
    _B(ms, 0.07, 0.45, 0.07, (30, 30, 34), 0, -0.45, 0, name='mango', gloss=0.3)
    _B(ms, 0.36, 0.09, 0.09, (210, 40, 36), 0, 0.0, 0, name='cabeza', gloss=0.6, base=False)
    for s_ in (-1, 1):
        ms.append(named(M3.cyl(0.035, 0.08, CROMO, n=10, shadow=0, gloss=0.9, r2=0.004).tf(rz=-90 * s_, t=(0.18 * s_, 0, 0)), 'punta', rim=0.9))
    return P.tfk(ms, s=P.resorte(k))


def tetera(incl=0.0):
    ms = []
    ms.append(named(M3.cyl(0.24, 0.32, CROMO, n=28, shadow=0, gloss=0.9, r2=0.2), 'tetera', rim=0.9, gloss=0.9))
    ms.append(named(M3.cyl(0.1, 0.06, (40, 40, 44), n=18, shadow=0, gloss=0.5).tf(t=(0, 0.32, 0)), 'tapa', rim=0.6))
    ms.append(tubo((0.2, 0.08, 0), (0.42, 0.3, 0), r=0.035, col=CROMO, name='pico', gloss=0.9))
    ms.append(named(M3.torus(0.13, 0.025, (40, 40, 44), nu=20, nv=6).tf(t=(-0.26, 0.18, 0)), 'asa', rim=0.6))
    return P.tfk(ms, rz=-incl)


def ventila(fuerte=1.0):
    ms = []
    _B(ms, 1.8, 0.12, 0.5, (32, 32, 36), 0, 0.0, 0, name='tablero', gloss=0.4)
    for j in range(7):
        _B(ms, 0.9, 0.012, 0.03, (90, 90, 96), 0, 0.13, -0.15 + j * 0.05, name='rejilla', gloss=0.6)
    return ms


def corte(caliente=0.0, frio=1.0, estira=0.0, roto=False):
    """Corte del parabrisas (de canto): vidrio de afuera arriba, PVB y vidrio de adentro abajo."""
    ms = []
    s = 1 + 0.07 * estira
    c_out = M.mixc(VIDRIO, (235, 70, 40), caliente)
    m = named(M3.box(3.0 * s, 0.26, 0.6, c_out, shadow=0, gloss=0.9, base=False).tf(t=(0, 1.45, 0)), 'afuera', rim=0.9, gloss=0.9)
    if caliente > 0.05:
        m.glow = M.scale_c((255, 80, 30), 0.45 * caliente)
    ms.append(m)
    ms.append(named(M3.box(3.0, 0.06, 0.6, PVB_C, shadow=0, gloss=0.4, base=False).tf(t=(0, 1.29, 0)), 'pvb', rim=0.6))
    mi = named(M3.box(3.0, 0.26, 0.6, M.mixc(VIDRIO, (110, 170, 255), frio), shadow=0, gloss=0.9, base=False).tf(t=(0, 1.13, 0)), 'adentro', rim=0.9, gloss=0.9)
    mi.glow = M.scale_c((90, 150, 255), 0.25 * frio)
    ms.append(mi)
    return ms


# ================================================================== escenas
UG = 0.3
ZP = np.array([0.0, 0.0, 0.0])


def _p_piedra(u):
    """Trayectoria de la piedra: cae al punto STAR (llega en UG) y rebota hacia la cámara."""
    hit = np.array(ws(STAR[0], STAR[1], 0.1))
    if u < UG:
        k = seg(u, UG - 0.32, UG)
        return hit + np.array([0.3, 3.2, 0.4]) * (1 - k * k), u * 900
    k = u - UG
    return hit + np.array([0.6 * k, 2.4 * k - 4.0 * k * k, 2.2 * k]), u * 900


def s_gancho(t, fi, u, d):
    fr = Frame(camara(u, [K(-4.0, 4.6, -16, 24, ty=0.95), K(UG, 4.3, -10, 22, ty=0.95), K(UG + 0.5, 3.7, 14, 26, ty=1.0),
                          K(3.2, 3.65, 18, 26, ty=1.0)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.6)
    M.cristal(fr.base, fr.fx, 'SÁNDWICH', u, t0=-2.6, cy=0.33, entrada='golpe')
    ms = frente()
    pp, rot = _p_piedra(u)
    if pp[1] < 4.0 and u < UG + 0.7:
        ms.append(piedra(pp, rot=rot))
    draw_objects(fr, ms)

    def ui(img, fx):
        x, y, _ = p_star(fr)
        estrella(img, fx, x, y, 120, seg(u, UG, UG + 0.25), seed=1)
        kicker(img, 'VIDRIO LAMINADO · 3 CAPAS', 140, seg(u, UG, UG + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu parabrisas no es vidrio…', 'sans'), ('es sándwich.', 'serif')], 190, seg(u, UG + 0.05, UG + 0.2), size=64)
    fr.ui.append(ui)
    img = finish(fr, fi, flash=0.35 * golpe_k(u, UG, 0.18))
    return sacudir(img, t, golpe_k(u, UG, 0.4), amp=26)


# 1. son dos vidrios con una capa de plástico en medio (vista explotada: las 3 capas se separan)
def s_capas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.0, 70, 6, ty=1.0), K(0.3, 3.4, 58, 10, ty=1.0), K(5, 3.45, 54, 10, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    k = P.eout4(seg(u, 0.0, 0.5))
    draw_objects(fr, frente(sep=0.35 * k, carro=False))

    def ui(img, fx):
        for j, (off, txt, col, w) in enumerate(((0.03 + 0.35 * k, 'VIDRIO', AZULC, 'vidrios'), (0.0, 'PLÁSTICO', AMBAR, 'plastico'),
                                                (-0.03 - 0.35 * k, 'VIDRIO', AZULC, 'vidrios'))):
            x, y, _ = fr.cam.p1(ws(-1.0, 0.95, off))
            uw = Wp(1, w) - 0.15 + (0.25 if j == 2 else 0)
            pill(img, fx, x, y - 60, txt, eout(seg(u, uw, uw + 0.25)), size=30, border=col)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. el PVB, pegados con calor y presión (se juntan con un golpe; ondas de calor y flechas de presión; «PVB» de cristal)
def s_pvb(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 40, 10, ty=1.0), K(0.3, 3.2, 16, 8, ty=1.0), K(5, 3.15, 12, 8, ty=1.0)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'PVB', u, t0=-0.1, cy=0.3, entrada='zoom')
    up = Wp(2, 'presion') - 0.1
    k = 1 - P.eout4(seg(u, up - 0.2, up + 0.1))
    draw_objects(fr, frente(sep=0.3 * k, carro=False, caliente=0.4 * seg(u, Wp(2, 'calor') - 0.2, Wp(2, 'calor') + 0.3) * k))
    P.ondas_calor(fr, t, 0.0, 0.4, 1.7, 1.6, k=seg(u, Wp(2, 'calor') - 0.2, Wp(2, 'calor')) * (1 - seg(u, up + 0.3, up + 0.8)), col=NARANJA, n=6)

    def ui(img, fx):
        kp = seg(u, up - 0.3, up)
        V.flecha(img, fx, 540, 640, 540, 820, AMARILLO, k=kp, w=10)
        V.flecha(img, fx, 540, 1420, 540, 1240, AMARILLO, k=kp, w=10)
        texto(img, fx, 540, 590, 'PRESIÓN', 40, AMARILLO, kp, f='mono', glow=0.4)
        pill(img, fx, 220, 1080, 'CALOR', eout(seg(u, Wp(2, 'calor') - 0.2, Wp(2, 'calor'))), size=30, border=NARANJA)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.1, 0.3), amp=14)


# 3. por eso, cuando le pega una piedra, queda una estrellita (macro de la estrellita que se abre)
def s_piedra(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.0, 20, 24, tx=0.25, ty=1.1), K(0.3, 2.3, 4, 20, tx=0.27, ty=1.08), K(5, 2.25, 0, 20, tx=0.27, ty=1.08)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.4)
    ui0 = Wp(3, 'piedra') - 0.1
    ms = frente()
    if u < ui0 + 0.4:
        hit = np.array(ws(STAR[0], STAR[1], 0.1))
        k = seg(u, ui0 - 0.35, ui0)
        pp = hit + np.array([0.0, 1.6, 1.2]) * (1 - k) if u < ui0 else hit + np.array([0.3, 0.8, 1.4]) * (u - ui0)
        ms.append(piedra(pp, rot=u * 800))
    draw_objects(fr, ms)

    def ui(img, fx):
        x, y, _ = p_star(fr)
        estrella(img, fx, x, y, 260, seg(u, ui0, ui0 + 0.3), seed=1)
        pill(img, fx, x, y + 330, 'ESTRELLITA', eout(seg(u, Wp(3, 'estrellita') - 0.2, Wp(3, 'estrellita'))), size=32, border=WHITE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=0.3 * golpe_k(u, ui0, 0.15)), t, golpe_k(u, ui0, 0.3), amp=18)


# 4. pero no se cae en pedazos (de canto: los pedazos del vidrio se quedan pegados al plástico)
def s_nocae(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, -30, 20, ty=1.3), K(0.3, 3.0, -6, 16, ty=1.3), K(5, 2.95, -2, 16, ty=1.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    vib = 0.02 * math.sin(t * 50) * (1 - seg(u, 0.2, 1.0))
    draw_objects(fr, P.tfk(corte(caliente=0.0, frio=0.0), t=(0, vib, 0)))

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        rng = np.random.RandomState(8)
        kk = seg(u, -0.1, 0.25)
        for j in range(9):
            x3 = -1.3 + 2.6 * (j + 0.5) / 9
            for yy in (1.45, 1.13):
                a = fr.cam.p1((x3 + rng.uniform(-0.1, 0.1), yy + 0.13, 0.31))
                b = fr.cam.p1((x3 + rng.uniform(-0.1, 0.1), yy - 0.13, 0.31))
                if kk > 0:
                    d_.line([a[:2], b[:2]], fill=M.scale_c(WHITE, kk), width=3)
                    df.line([a[:2], b[:2]], fill=M.scale_c(AZULC, 0.5 * kk), width=8)
        x, y, _ = fr.cam.p1((0, 1.29, 0.31))
        pill(img, fx, x, y + 260, 'EL PLÁSTICO LOS AGARRA', eout(seg(u, 0.2, 0.5)), size=30, border=AMBAR)
        P.titulo_golpe(img, fx, [('✓ No se cae.', 'sans')], 330, seg(u, Wp(4, 'cae') - 0.1, Wp(4, 'cae') + 0.05), size=80, col=VERDE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(4, 'cae') + 0.05, 0.25), amp=12)


# 5. ahora mira la ventana de un lado (la puerta llega girando)
def s_lado(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.2, 50, 10, ty=0.75), K(0.3, 3.6, 12, 6, ty=0.75), K(5, 3.55, 8, 6, ty=0.75)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'gira')
    draw_objects(fr, P.tfk(puerta(), ry=math.degrees(e['giro']) * 0.25))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0.08, 1.05, 0))
        doodle_circle(img, fx, x, y, 330, 170, t, k=seg(u, Wp(5, 'ventana') - 0.1, Wp(5, 'ventana') + 0.3), col=AMARILLO, seed=2)
        pill(img, fx, x, y - 240, 'VENTANA DE LADO', eout(seg(u, Wp(5, 'lado') - 0.2, Wp(5, 'lado'))), size=32, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. esa es de vidrio templado, y con un golpe se hace cubitos («CUBITOS» de cristal; la ventana estalla)
def s_templado(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, -20, 8, ty=0.8), K(0.3, 3.8, -4, 6, ty=0.8), K(5, 3.75, 0, 6, ty=0.8)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    ug = Wp(6, 'golpe') - 0.05
    M.cristal(fr.base, fr.fx, 'CUBITOS', u, t0=Wp(6, 'cubitos') - 0.3, cy=0.3, entrada='golpe')
    k = clamp((u - ug) / 1.3)
    draw_objects(fr, puerta(cubos=k))

    def ui(img, fx):
        pill(img, fx, 540, 1380, 'VIDRIO TEMPLADO', eout(seg(u, Wp(6, 'templado') - 0.2, Wp(6, 'templado'))), size=32, border=AZULC, dot=False)
        if 0 < u - ug < 0.15:
            x, y, _ = fr.cam.p1((0.1, 1.05, 0))
            estrella(img, fx, x, y, 200, 1.0, seed=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=0.4 * golpe_k(u, ug, 0.15)), t, golpe_k(u, ug, 0.4), amp=24)


# 7. y es a propósito: cubitos sin filo que cortan menos (la cámara entra a los cubitos; uno gira de cerca)
def s_sinfilo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.2, 30, 30, ty=0.1), K(0.3, 1.6, 10, 22, ty=0.1), K(5, 1.55, 6, 22, ty=0.1)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.6)
    rng = np.random.RandomState(11)
    ms = []
    for j in range(18):
        p = (rng.uniform(-1.0, 1.0), 0.03, rng.uniform(-0.8, 0.5))
        ms.append(named(M3.rbox(0.16, 0.12, 0.14, 0.035, M.mixc(VIDRIO, (210, 235, 245), rng.rand() * 0.5), n=3, shadow=0, gloss=0.95)
                        .tf(ry=rng.uniform(0, 90), t=p), 'cubito', rim=0.9, gloss=0.95))
    e = P.entrada(u, -0.1, 0.3, 'pop')
    ms.append(named(M3.rbox(0.36, 0.3, 0.32, 0.08, (190, 225, 240), n=4, shadow=0, gloss=0.95)
                    .tf(rx=t * 40, ry=t * 70, t=(0, 0.45, 0.3)), 'cubito', rim=0.95, gloss=0.95))
    draw_objects(fr, ms)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0, 0.6, 0.3))
        doodle_circle(img, fx, x, y, 170, 150, t, k=seg(u, Wp(7, 'filo') - 0.2, Wp(7, 'filo') + 0.2), col=VERDE, seed=3)
        pill(img, fx, x, y - 230, 'SIN FILO', eout(seg(u, Wp(7, 'filo') - 0.2, Wp(7, 'filo'))), size=34, border=VERDE)
        pill(img, fx, 540, 1380, 'A PROPÓSITO', eout(seg(u, Wp(7, 'proposito') - 0.2, Wp(7, 'proposito'))), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. y por ahí puedes salir en una emergencia (el martillo de emergencia y la flecha de salida)
def s_salida(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 40, 10, ty=0.8), K(0.3, 4.0, 18, 6, ty=0.8), K(5, 3.95, 14, 6, ty=0.8)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    km = seg(u, -0.1, 0.25)
    draw_objects(fr, puerta(sin_vidrio=True) + P.tfk(martillo(km), rz=-30 + 20 * math.sin(t * 3), t=(-0.9, 1.6, 0.3)))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0.1, 1.05, 0))
        V.flecha(img, fx, x - 220, y, x + 260, y - 60, VERDE, k=seg(u, Wp(8, 'salir') - 0.2, Wp(8, 'salir') + 0.1), w=14)
        pill(img, fx, 540, 1380, 'SALIDA DE EMERGENCIA', eout(seg(u, Wp(8, 'emergencia') - 0.2, Wp(8, 'emergencia'))), size=32, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. el parabrisas, en cambio, aguanta (la estrellita grande y el vidrio en su lugar; la cámara gira)
def s_aguanta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -50, 22, ty=1.0), K(0.3, 4.2, -18, 20, ty=1.0), K(5, 4.15, -14, 20, ty=1.0)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    draw_objects(fr, frente())

    def ui(img, fx):
        x, y, _ = p_star(fr)
        estrella(img, fx, x, y, 170, 1.0, seed=1)
        grieta(img, fx, fr, 0.35)
        P.titulo_golpe(img, fx, [('Aguanta.', 'serif')], 330, seg(u, Wp(9, 'aguanta') - 0.1, Wp(9, 'aguanta') + 0.05), size=100)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(9, 'aguanta') + 0.05, 0.25), amp=12)


# 10. el plástico agarra los pedazos y te mantiene adentro en un choque (el carro choca con el muro)
def s_choque(t, fi, u, d):
    uc = Wp(10, 'choque') - 0.25
    x = -1.6 + 1.6 * min(1.0, max(0.0, (u + 0.3) / (uc + 0.3))) ** 2
    fr = Frame(camara(u, [K(-0.3, 6.6, -30, 12, tx=x + 0.4, ty=0.8), K(0.3, 5.8, -12, 10, tx=x + 0.4, ty=0.8), K(5, 5.75, -8, 10, tx=x + 0.4, ty=0.8)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.4)
    kc = seg(u, uc, uc + 0.2)
    ms = P.tfk(V.carro(col=CARRO, giro_llanta=-x / 0.33), rz=-3 * math.sin(math.pi * kc) * (1 - seg(u, uc + 0.2, uc + 0.5)), t=(x, 0, 0))
    ms.append(named(M3.box(0.5, 2.2, 2.8, CONCRETO, shadow=0, gloss=0.1).tf(t=(1.78, 0, 0)), 'muro', rim=0.4))
    draw_objects(fr, ms)

    def ui(img, fx):
        if kc > 0:
            xw, yw, _ = fr.cam.p1((x + 0.5, 1.05, 0.3))
            estrella(img, fx, xw, yw, 110, kc, seed=9)
            V.flecha(img, fx, xw + 120, yw - 180, xw - 140, yw - 180, VERDE, k=seg(u, uc + 0.2, uc + 0.5), w=10)
            texto(img, fx, xw, yw - 250, 'TE MANTIENE ADENTRO', 36, VERDE, seg(u, uc + 0.3, uc + 0.6), f='mono', glow=0.4)
        pill(img, fx, 540, 1380, 'EL PLÁSTICO AGARRA LOS PEDAZOS', eout(seg(u, Wp(10, 'agarra') - 0.2, Wp(10, 'agarra'))), size=28, border=AMBAR, dot=False)
        esquema(img, fx, seg(u, 0, 0.3), y=1450, txt='ESQUEMA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=0.4 * golpe_k(u, uc, 0.12)), t, golpe_k(u, uc, 0.45), amp=26)


# 11–12. uno de los que los fabrica es mexicano: Vitro, de Nuevo León (la Tierra de alambre y sus mercados)
MTY = (-100.3, 25.7)


def _globo(fr, t, u, marcas, spin):
    return VI.globo(fr, t, np.array([0, 1.15, 0]), 1.35, spin, marcas=marcas)


def s_mexicano(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.8, 30, 6, ty=1.15), K(0.3, 5.4, 10, 8, ty=1.15), K(5, 5.35, 6, 8, ty=1.15)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.1)
    M.cristal(fr.base, fr.fx, 'MÉXICO', u, t0=Wp(21, 'mexicano') - 0.3, cy=0.27, entrada='sube')
    spin = math.radians(-70 + 25 * u)
    g = _globo(fr, t, u, [(MTY[0], MTY[1], VERDE, seg(u, Wp(21, 'mexicano') - 0.2, Wp(21, 'mexicano')))], spin)

    def ui(img, fx):
        (x, y, _), vis = g[0]
        if vis:
            pill(img, fx, x, y - 70, 'MONTERREY', eout(seg(u, Wp(21, 'mexicano'), Wp(21, 'mexicano') + 0.25)), size=28, border=VERDE)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_vitro(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 6, 8, ty=1.15), K(0.3, 5.6, -10, 12, ty=1.15), K(5, 5.65, -14, 12, ty=1.15)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.1)
    spin = math.radians(-55 + 22 * u)
    ks = [seg(u, Wp(22, w) - 0.15, Wp(22, w) + 0.1) for w in ('mexico', 'estados', 'canada', 'europa')]
    g = _globo(fr, t, u, [(MTY[0], MTY[1], VERDE, 1.0), (-98, 39, CYAN, ks[1]), (-106, 56, CYAN, ks[2]), (10, 50, CYAN, ks[3])], spin)

    def ui(img, fx):
        kicker(img, 'VIDRIO AUTOMOTRIZ · NUEVO LEÓN', 300, seg(u, -0.1, 0.2), col=AZULC)
        P.titulo_golpe(img, fx, [('Vitro', 'serif')], 350, seg(u, Wp(22, 'vitro') - 0.1, Wp(22, 'vitro') + 0.05), size=110)
        for j, txt in enumerate(('MÉXICO', 'EE. UU.', 'CANADÁ', 'EUROPA')):
            pill(img, fx, 190 + 233 * j, 1380, txt, eout(ks[j]), size=24, border=VERDE if j == 0 else CYAN, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(22, 'vitro') + 0.05, 0.25), amp=12)


# 13. y aquí está el error (el parabrisas congelado se pone rojo)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, 40, 26, ty=1.0), K(0.3, 4.6, 14, 20, ty=1.0), K(5, 4.65, 10, 20, ty=1.0)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    draw_objects(fr, frente(frio=1.0), xray=0.0)

    def ui(img, fx):
        escarcha(img, fx, fr, 1.0)
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 300, seg(u, 0.05, 0.2), size=92, col=WHITE)
        texto(img, fx, 540, 1330, '⚠', 140, ROJO, seg(u, 0.2, 0.35), f='sansx', glow=0.8)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.35), amp=20)


# 14. echarle agua caliente al parabrisas congelado («CALIENTE» de cristal; la tetera vacía el chorro con vapor)
def s_agua(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, -30, 24, ty=1.2), K(0.3, 4.2, -8, 22, ty=1.2), K(5, 4.15, -4, 22, ty=1.2)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'CALIENTE', u, t0=Wp(12, 'caliente') - 0.3, cy=0.27, entrada='golpe')
    ua = Wp(12, 'agua') - 0.1
    ki = P.eout4(seg(u, ua - 0.3, ua + 0.1))
    tp = np.array([0.55, 2.15, 0.6])
    draw_objects(fr, frente(frio=1.0 - 0.3 * seg(u, ua, d)) + P.tfk(tetera(incl=55 * ki), t=tuple(tp)))
    kw = seg(u, ua, ua + 0.3)
    if kw > 0:
        a = math.radians(-55 * ki)
        tip = tp + np.array([0.42 * math.cos(a) - 0.3 * math.sin(a), 0.42 * math.sin(a) + 0.3 * math.cos(a), 0])
        hit = np.array(ws(0.2, 0.25, 0.05))
        pts = [tuple(tip + (hit - tip) * s + np.array([0, 0.25 * math.sin(math.pi * s), 0])) for s in np.linspace(0, kw, 14)]
        line3(fr, pts, col=AZULC, w=6, a=0.9, glow=0.9)
        for j in range(6):
            s = (t * 2.0 + j / 6) % 1.0 * kw
            dot3(fr, tuple(tip + (hit - tip) * s + np.array([0, 0.25 * math.sin(math.pi * s), 0])), r=7, col=WHITE, a=0.9, glow=1.2)
        P.ondas_calor(fr, t, 0.2, 1.25, 2.0, 1.0, k=kw, col=WHITE, n=5)

    def ui(img, fx):
        escarcha(img, fx, fr, 1.0 - 0.4 * seg(u, ua, d))
        pill(img, fx, 540, 1380, 'PARABRISAS CONGELADO', eout(seg(u, Wp(12, 'congelado') - 0.2, Wp(12, 'congelado'))), size=30, border=AZULC, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. por fuera el vidrio se calienta y se estira de golpe (corte: la capa de afuera roja se estira)
def s_estira(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, -40, 22, ty=1.3), K(0.3, 3.6, -14, 18, ty=1.3), K(5, 3.55, -10, 18, ty=1.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    kc = seg(u, Wp(13, 'calienta') - 0.3, Wp(13, 'calienta') + 0.2)
    ke = P.resorte(seg(u, Wp(13, 'estira') - 0.1, Wp(13, 'estira') + 0.4))
    draw_objects(fr, corte(caliente=kc, frio=1.0, estira=ke))

    def ui(img, fx):
        xa, ya, _ = fr.cam.p1((-1.6, 1.45, 0.3))
        xb, yb, _ = fr.cam.p1((1.6, 1.45, 0.3))
        V.flecha(img, fx, xa + 120, ya - 120, xa - 40, ya - 120, NARANJA, k=ke, w=10)
        V.flecha(img, fx, xb - 120, yb - 120, xb + 40, yb - 120, NARANJA, k=ke, w=10)
        texto(img, fx, 540, 420, 'POR FUERA: CALIENTE', 52, NARANJA, kc, f='sansx', glow=0.5)
        x, y, _ = fr.cam.p1((0, 1.13, 0.3))
        pill(img, fx, x, y + 220, 'POR DENTRO: HELADO', eout(seg(u, 0.1, 0.4)), size=30, border=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. pero por dentro sigue helado… y truena (la grieta cruza el corte con golpe)
def s_truena(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, -10, 20, ty=1.3), K(0.3, 3.2, 10, 16, ty=1.3), K(5, 3.15, 14, 16, ty=1.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    ut = Wp(14, 'truena') - 0.1
    draw_objects(fr, corte(caliente=1.0, frio=1.0, estira=1.0))

    def ui(img, fx):
        kt = seg(u, ut, ut + 0.15)
        if kt > 0:
            rng = np.random.RandomState(4)
            pts = []
            for s in np.linspace(0, 1, 12):
                x3 = -1.5 + 3.0 * s
                pts.append(fr.cam.p1((x3, 1.45 + rng.uniform(-0.1, 0.1), 0.31))[:2])
            n = max(2, int(12 * kt))
            ImageDraw.Draw(img).line(pts[:n], fill=WHITE, width=6)
            ImageDraw.Draw(fx).line(pts[:n], fill=(255, 120, 80), width=16)
            texto(img, fx, 540, 420, '¡CRAC!', 110, WHITE, kt, f='sansx', glow=0.6)
        x, y, _ = fr.cam.p1((0, 1.13, 0.3))
        pill(img, fx, x, y + 220, 'ADENTRO: HELADO', eout(seg(u, Wp(14, 'helado') - 0.2, Wp(14, 'helado'))), size=30, border=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=0.4 * golpe_k(u, ut, 0.15)), t, golpe_k(u, ut, 0.45), amp=26)


# 17. si ya tenía una estrellita (de noche, con escarcha)
def s_estrellita(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.8, 40, 26, tx=0.2, ty=1.1), K(0.3, 2.2, 14, 20, tx=0.25, ty=1.1), K(5, 2.15, 10, 20, tx=0.25, ty=1.1)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8, beam=0.3)
    draw_objects(fr, frente(frio=1.0))

    def ui(img, fx):
        escarcha(img, fx, fr, 0.8, seed=5)
        x, y, _ = p_star(fr)
        estrella(img, fx, x, y, 170, seg(u, 0.0, 0.3), seed=1)
        doodle_circle(img, fx, x, y, 220, 200, t, k=seg(u, 0.2, 0.5), col=ROJO, seed=7)
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. el frío de una noche la puede volver una grieta de lado a lado (la luna, el reloj y la grieta que crece; «GRIETA»)
def s_noche(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, 30, 22, ty=1.0), K(0.3, 4.0, 4, 20, ty=1.0), K(5, 3.95, 0, 20, ty=1.0)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8, beam=0.2)
    M.cristal(fr.base, fr.fx, 'GRIETA', u, t0=Wp(16, 'grieta') - 0.3, cy=0.28, entrada='zoom')
    draw_objects(fr, frente(frio=1.0))
    kg = seg(u, Wp(16, 'noche') - 0.2, Wp(16, 'lado', 1) + 0.2)

    def ui(img, fx):
        escarcha(img, fx, fr, 0.7, seed=5)
        x, y, _ = p_star(fr)
        estrella(img, fx, x, y, 130, 1.0, seed=1)
        grieta(img, fx, fr, kg)
        h = int(22 + 9 * kg) % 24
        LL.reloj_txt(img, fx, 600, 1435, f'{h:02d}:00', k=seg(u, 0.0, 0.25), icono='luna')
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. y la calefacción a todo, directo al vidrio helado, hace lo mismo (desde adentro: el chorro caliente al vidrio)
def s_calefaccion(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 160, 16, ty=0.9), K(0.3, 3.2, 176, 14, ty=0.9), K(5, 3.15, 180, 14, ty=0.9)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.3)
    yb = C_WS[1] - WH * math.cos(_T)
    zb = WH * math.sin(_T)
    kf = seg(u, Wp(17, 'todo') - 0.3, Wp(17, 'todo') + 0.1)
    draw_objects(fr, frente(frio=1.0) + P.tfk(ventila(), t=(0, yb - 0.1, -zb - 0.35)))
    for j in range(7):
        x0 = -0.6 + 0.2 * j
        ph = (t * 2.5 + j * 0.3) % 1.0
        pts = [(x0 + 0.04 * math.sin(s * 9 + t * 8), yb + 0.05 + 0.6 * s, -zb - 0.35 + 0.3 * s) for s in np.linspace(0, 1, 12)]
        line3(fr, pts, col=(255, 90, 50), w=3.0, a=0.8 * kf, glow=1.0, frac=clamp(ph * 1.6))

    def ui(img, fx):
        grieta(img, fx, fr, 0.35 + 0.65 * seg(u, Wp(17, 'mismo') - 0.4, Wp(17, 'mismo') + 0.2), off=-0.05)
        pill(img, fx, 540, 380, 'CALEFACCIÓN A TODO', eout(seg(u, Wp(17, 'calefaccion') - 0.2, Wp(17, 'calefaccion'))), size=36, border=ROJO, dot=False)
        texto(img, fx, 540, 470, '✕', 90, ROJO, seg(u, Wp(17, 'mismo') - 0.2, Wp(17, 'mismo')), f='sansx', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(17, 'mismo'), 0.25), amp=12)


# 20. mejor prende el carro, calefacción suave, y quita el hielo despacio (lista con palomitas; la escarcha se va)
def s_mejor(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.8, -40, 24, ty=1.0), K(0.3, 4.4, -14, 22, ty=1.0), K(5, 4.35, -10, 22, ty=1.0)], cy=0.7))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    kq = seg(u, Wp(18, 'quita') - 0.2, d)
    draw_objects(fr, frente(frio=1.0 - kq))

    def ui(img, fx):
        escarcha(img, fx, fr, 1.0 - kq, seed=5)
        for j, (txt, w) in enumerate((('✓ PRENDE EL CARRO', 'prende'), ('✓ CALEFACCIÓN SUAVE', 'suave'), ('✓ QUITA EL HIELO DESPACIO', 'quita'))):
            k = seg(u, Wp(18, w) - 0.2, Wp(18, w))
            texto(img, fx, 120, 330 + j * 95, txt, 48, VERDE, k, f='sansx', glow=0.4, anchor='lm')
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. y la estrellita, repárala pronto (la jeringa de resina llena la estrellita)
def s_repara(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.6, -30, 28, tx=0.28, ty=1.1), K(0.3, 2.1, -8, 24, tx=0.28, ty=1.1), K(5, 2.05, -4, 24, tx=0.28, ty=1.1)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.4)
    st = np.array(ws(STAR[0], STAR[1], 0.05))
    e = P.entrada(u, -0.1, 0.3, 'cae')
    iny = [named(M3.cyl(0.06, 0.35, (230, 230, 236), n=18, shadow=0, gloss=0.9), 'jeringa', rim=0.9),
           named(M3.cyl(0.015, 0.12, CROMO, n=10, shadow=0, gloss=0.9, y0=-0.12), 'punta', rim=0.9),
           named(M3.cyl(0.075, 0.03, (40, 150, 230), n=18, shadow=0, gloss=0.6).tf(t=(0, 0.35, 0)), 'embolo', rim=0.7)]
    iny = [m.tf(rx=-TILT).tf(t=tuple(st + EN * (0.13 + max(0.0, -e['dy']) * 0.3))) for m in iny]
    draw_objects(fr, frente() + iny)

    def ui(img, fx):
        x, y, _ = p_star(fr)
        kr = seg(u, Wp(19, 'reparala') - 0.1, Wp(19, 'pronto') + 0.3)
        estrella(img, fx, x, y, 200, 1.0 - 0.75 * kr, seed=1)
        pill(img, fx, 540, 1380, 'RESINA · SE REPARA', eout(seg(u, Wp(19, 'reparala') - 0.2, Wp(19, 'reparala'))), size=32, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 22. un daño de menos de 15 cm todavía se puede reparar (cota de 15 cm junto a la grieta; «15 CM» de cristal)
def s_15(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, 30, 24, ty=1.0), K(0.3, 3.6, 8, 20, ty=1.0), K(5, 3.55, 4, 20, ty=1.0)], cy=0.64))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, '15 CM', u, t0=Wp(20, 'quince') - 0.3, cy=0.27, entrada='sube')
    draw_objects(fr, frente())

    def ui(img, fx):
        x, y, _ = p_star(fr)
        estrella(img, fx, x, y, 110, 1.0, seed=1)
        kc = seg(u, Wp(20, 'quince') - 0.1, Wp(20, 'quince') + 0.3)
        xa, ya, _ = fr.cam.p1(ws(STAR[0] - 0.4, STAR[1] - 0.45, 0.05))
        xb, yb, _ = fr.cam.p1(ws(STAR[0] + 0.4, STAR[1] - 0.45, 0.05))
        if kc > 0:
            dd = ImageDraw.Draw(img)
            xm = xa + (xb - xa) * kc
            dd.line([(xa, ya), (xm, ya + (yb - ya) * kc)], fill=AMARILLO, width=5)
            for xx, yy in ((xa, ya), (xb, yb)):
                dd.line([(xx, yy - 22), (xx, yy + 22)], fill=M.scale_c(AMARILLO, kc), width=5)
            texto(img, fx, (xa + xb) / 2, ya + 50, '15 CM', 40, AMARILLO, kc, f='mono', glow=0.4)
        pill(img, fx, 540, 1380, 'SIN CAMBIAR EL PARABRISAS', eout(seg(u, Wp(20, 'cambiar') - 0.2, Wp(20, 'cambiar'))), size=30, border=VERDE, dot=False)
        pill(img, fx, 540, 1450, 'SAFELITE: DAÑOS DE MENOS DE 6 PULGADAS', seg(u, 0.3, 0.6), size=20, border=GRIS, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. mándaselo a quien le echa agua caliente al parabrisas congelado
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 40, 22, ty=1.0), K(0.3, 4.2, 20, 20, ty=1.0), K(5, 4.15, 16, 20, ty=1.0)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    draw_objects(fr, frente(frio=0.6) + P.tfk(tetera(incl=0.0), t=(1.5, 0.0, 1.0)))

    def ui(img, fx):
        escarcha(img, fx, fr, 0.6, seed=5)
        P.titulo_golpe(img, fx, [('Mándaselo a quien le echa', 'sans'), ('agua caliente al parabrisas.', 'serif')], 250, seg(u, 0.05, 0.2), size=58)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-2.6, 'whoosh_suave', 0.4), (UG - 0.35, 'whoosh', 0.5), (UG, 'vidrio', 1.0), (UG + 0.02, 'sub', 0.9), (UG + 0.2, 'bass', 0.8)]),
           dict(desde=1, fn=s_capas, tr='zoom', c=(0.6, 0.5), sfx=[(0.1, 'whoosh_suave', 0.5)]),
           dict(desde=2, fn=s_pvb, tr='deslizar', sfx=[(-0.1, 'cristal', 0.6)]),
           dict(desde=3, fn=s_piedra, tr='golpe', sfx=[]),
           dict(desde=4, fn=s_nocae, tr='iris', c=(0.6, 0.5), sfx=[(0.2, 'scribble', 0.4)]),
           dict(desde=5, fn=s_lado, tr='cubo', sfx=[(0.0, 'whoosh', 0.5)]),
           dict(desde=6, fn=s_templado, tr='whip', sfx=[]),
           dict(desde=7, fn=s_sinfilo, tr='zoom', c=(0.5, 0.5), sfx=[(0.1, 'shimmer', 0.4)]),
           dict(desde=8, fn=s_salida, tr='deslizar_abajo', sfx=[(0.1, 'slap', 0.6)]),
           dict(desde=9, fn=s_aguanta, tr='cubo_izq', sfx=[]),
           dict(desde=10, fn=s_choque, tr='golpe', sfx=[]),
           dict(desde=11, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.15, 'sub', 0.9), (0.2, 'bass', 0.7)]),
           dict(desde=12, fn=s_agua, tr='push', c=(0.5, 0.5), sfx=[]),
           dict(desde=13, fn=s_estira, tr='zoom', c=(0.5, 0.5), sfx=[(0.1, 'whoosh_suave', 0.4)]),
           dict(desde=14, fn=s_truena, tr='glitch', sfx=[]),
           dict(desde=15, fn=s_estrellita, tr='wipe', sfx=[(0.1, 'scribble', 0.5)]),
           dict(desde=16, fn=s_noche, tr='remolino', sfx=[(0.0, 'riser', 0.3)]),
           dict(desde=17, fn=s_calefaccion, tr='deslizar', sfx=[(0.1, 'whoosh_suave', 0.5)]),
           dict(desde=18, fn=s_mejor, tr='rebanadas', sfx=[]),
           dict(desde=19, fn=s_repara, tr='giro', sfx=[]),
           dict(desde=20, fn=s_15, tr='mosaico', sfx=[]),
           dict(desde=21, fn=s_mexicano, tr='flash', sfx=[(0.1, 'whoosh_suave', 0.4)]),
           dict(desde=22, fn=s_vitro, tr='iris', c=(0.45, 0.5), sfx=[]),
           dict(desde=23, fn=s_compa, tr='whip_izq', sfx=[(0.05, 'slap', 0.7)]),
           dict(desde=24, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    add = {1: [(Wp(1, 'vidrios') - 0.15, 'tick', 0.5), (Wp(1, 'plastico') - 0.15, 'tick2', 0.5)],
           2: [(Wp(2, 'calor') - 0.2, 'burst', 0.4), (Wp(2, 'presion') - 0.1, 'thud', 0.9)],
           3: [(Wp(3, 'piedra') - 0.1, 'vidrio', 1.0), (Wp(3, 'piedra') - 0.05, 'sub', 0.7)],
           4: [(Wp(4, 'cae') - 0.1, 'bass', 0.8)],
           5: [(Wp(5, 'ventana') - 0.1, 'scribble', 0.5)],
           6: [(Wp(6, 'golpe') - 0.05, 'vidrio', 1.0), (Wp(6, 'golpe'), 'sub', 0.9), (Wp(6, 'cubitos') - 0.3, 'cristal', 0.6)],
           7: [(Wp(7, 'filo') - 0.2, 'scribble', 0.5)],
           8: [(Wp(8, 'salir') - 0.2, 'whoosh', 0.5)],
           9: [(Wp(9, 'aguanta') - 0.1, 'bass', 0.8)],
           10: [(Wp(10, 'choque') - 0.25, 'burst', 0.9), (Wp(10, 'choque') - 0.2, 'sub', 1.0), (Wp(10, 'choque'), 'vidrio', 0.6)],
           21: [(Wp(21, 'mexicano') - 0.3, 'cristal', 0.6), (Wp(21, 'mexicano'), 'chime_a', 0.5)],
           22: [(Wp(22, 'vitro'), 'bass', 0.7)] + [(Wp(22, w) - 0.1, 'tick2', 0.5) for w in ('estados', 'canada', 'europa')],
           12: [(Wp(12, 'agua') - 0.1, 'whoosh_suave', 0.5), (Wp(12, 'caliente') - 0.3, 'cristal', 0.6)],
           13: [(Wp(13, 'estira') - 0.1, 'thud', 0.8)],
           14: [(Wp(14, 'truena') - 0.1, 'vidrio', 1.0), (Wp(14, 'truena'), 'sub', 1.0)],
           16: [(Wp(16, 'grieta') - 0.3, 'cristal', 0.6), (Wp(16, 'lado', 1), 'scribble', 0.6)],
           17: [(Wp(17, 'mismo') - 0.1, 'burst', 0.6)],
           18: [(Wp(18, w) - 0.2, 'chime_b', 0.4) for w in ('prende', 'suave', 'quita')],
           19: [(Wp(19, 'reparala') - 0.1, 'click', 0.8), (Wp(19, 'pronto'), 'chime_c', 0.4)],
           20: [(Wp(20, 'quince') - 0.3, 'cristal', 0.6), (Wp(20, 'quince'), 'click', 0.6)]}
    for e in ESCENAS:
        if e.get('desde') in add and not e.get('loop'):
            e['sfx'] = list(e.get('sfx', [])) + add[e['desde']]


_sfx_dinamicos()


def tiempos_falsos():
    T = [(round(0.25 + 2.8 * i, 2), round(0.25 + 2.8 * i + 2.4, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.55, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    print('ok', T[-1])


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    else:
        montaje.cli(globals())
