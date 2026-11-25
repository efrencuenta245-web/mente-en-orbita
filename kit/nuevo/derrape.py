"""Reel diario vie 27-nov-2026 10:00 (propuesto) — «Tu derrape no es descontrol.»
Física del drift: una llanta que rueda agarra más que una que se arrastra (fricción estática > dinámica; demo «Locked
Brakes» de Harvard: con las de adelante trabadas el carro se va derecho, con las de atrás trabadas da trompo; por eso
existe el ABS). El piloto suelta las de atrás a propósito con el acelerador, apunta el carro con el contravolante y con el
pie decide el ángulo (PopSci, 2023: «the car's direction of travel is controlled by counter-steering» y el acelerador
mantiene la línea). Error (segundo gancho): jalar el freno de mano en la calle (traba las de atrás) y apagar el control
de estabilidad con lluvia (el agarre baja de ~0.7 a ~0.4: HyperPhysics). NHTSA (DOT HS 810 794, 2007): el ESC bajó 36 %
los choques mortales de un solo vehículo en autos (63 % en camionetas). Cierre: el drift se aprende en pista.
Comunidad: drift y tuning. Inicio tipo 9 (giro 360° con destellos): el carro da un trompo completo con 3 cortes de
destello y humo, y queda de frente al título («CONTROL» de cristal detrás).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Datos y fuentes: guiones/2026-11-27_derrape.txt. Sin fotos reales (todo es esquema sin marca).
"""
import json, math, os, sys
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
import electrico as EL
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


TEMA = 'derrape'
TXT = ['Tu derrape no es descontrol.',
       'Una llanta que rueda agarra más',
       'que una que se arrastra.',
       'Mira: si se traban las de adelante,',
       'el carro se va derecho… y ya no da vuelta.',
       'Si se traban las de atrás,',
       'la cola se adelanta… y das trompo.',
       'Por eso existe el ABS:',
       'suelta y aprieta el freno',
       'para que la llanta siga rodando y puedas girar.',
       'El piloto de drift suelta las de atrás a propósito,',
       'con el acelerador, y las de adelante siguen rodando.',
       'Con el contravolante apunta el carro,',
       'y con el pie derecho decide qué tanto se abre la cola.',
       'Y aquí está el error:',
       'jalar el freno de mano en la calle.',
       'Traba las de atrás, la cola se suelta…',
       'y en la calle no hay muro de llantas: hay postes, banquetas y gente.',
       'Y apagar el control de estabilidad con lluvia es peor:',
       'el agarre baja casi a la mitad.',
       'Ese control frena una llanta por ti antes del trompo:',
       'en EE. UU. bajó más de un tercio los choques mortales de un solo carro.',
       'El drift se aprende en pista, con casco y con permiso.',
       'Mándaselo a tu compa que se siente piloto en la glorieta.',
       'Porque tu derrape no es descontrol.']
VOZ = ['Tu derrape no es descontrol.',
       'Una llanta que rueda agarra más',
       'que una que se arrastra.',
       'Mira: si se traban las de adelante,',
       'el carro se va derecho... y ya no da vuelta.',
       'Si se traban las de atrás,',
       'la cola se adelanta... y das trompo.',
       'Por eso existe el ABS:',
       'suelta y aprieta el freno',
       'para que la llanta siga rodando y puedas girar.',
       'El piloto de drift suelta las de atrás a propósito,',
       'con el acelerador, y las de adelante siguen rodando.',
       'Con el contravolante apunta el carro,',
       'y con el pie derecho decide qué tanto se abre la cola.',
       'Y aquí está el error:',
       'jalar el freno de mano en la calle.',
       'Traba las de atrás, la cola se suelta...',
       'y en la calle no hay muro de llantas: hay postes, banquetas y gente.',
       'Y apagar el control de estabilidad con lluvia es peor:',
       'el agarre baja casi a la mitad.',
       'Ese control frena una llanta por ti antes del trompo:',
       'en Estados Unidos bajó más de un tercio los choques mortales de un solo carro.',
       'El drift se aprende en pista, con casco y con permiso.',
       'Mándaselo a tu compa que se siente piloto en la glorieta.',
       'Porque tu derrape no es descontrol.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_derrape.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-27_derrape_words.json')

AMARILLO = (255, 236, 160)
AMBAR = (255, 176, 40)
NARANJA = (255, 130, 50)
ROJO = (240, 50, 42)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (90, 220, 140)
CARRO = (236, 236, 240)          # el carro de drift: blanco con franja roja
FRANJA = (214, 30, 36)
HUMO = (178, 180, 188)
LLANTA = (24, 24, 27)
CROMO = (205, 208, 215)
ASFALTO = (60, 60, 64)
CONO = (255, 110, 30)

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


# ------------------------------------------------------------------ el carro de drift (frente hacia +x)
RUEDAS = {'fi': (1.0, 0.6), 'fd': (1.0, -0.68), 'ti': (-1.0, 0.6), 'td': (-1.0, -0.68)}   # +z = lado derecho
R_LL = 0.33


def auto(giro=0.0, steer=0.0, traba_f=0.0, traba_t=0.0, frena=None, col=CARRO, giro_t=None):
    """Coupé de drift sin marca: blanco con franja roja, alerón chico. steer: grados de las llantas de adelante
    (+ = a la izquierda). traba_f/t 0–1: llantas trabadas (se pintan de rojo). frena: rueda que frena el ESC ('fi'…)."""
    ms = []
    ms.append(named(M3.rbox(3.0, 0.48, 1.25, 0.22, col, n=5, shadow=0, gloss=0.85).tf(t=(0, 0.32, 0)), 'cuerpo', rim=0.8, gloss=0.85))
    ms.append(named(M3.rbox(1.45, 0.42, 1.08, 0.24, (26, 30, 38), n=5, shadow=0, gloss=0.95).tf(t=(-0.25, 0.76, 0)), 'vidrio', rim=0.9, gloss=0.95))
    ms.append(named(M3.rbox(1.2, 0.06, 0.98, 0.2, col, n=4, shadow=0, gloss=0.85).tf(t=(-0.3, 1.0, 0)), 'cuerpo', rim=0.8))
    _B(ms, 3.02, 0.08, 0.18, FRANJA, 0.0, 0.5, 0.0, name='franja', gloss=0.7, base=False)
    _B(ms, 0.9, 0.04, 0.2, FRANJA, 0.55, 0.57, 0.0, name='franja', gloss=0.7, base=False)
    _B(ms, 0.12, 0.2, 0.06, (40, 40, 44), -1.4, 0.68, 0.45, name='aleron', gloss=0.4)
    _B(ms, 0.12, 0.2, 0.06, (40, 40, 44), -1.4, 0.68, -0.45, name='aleron', gloss=0.4)
    _B(ms, 0.34, 0.04, 1.2, (30, 30, 34), -1.42, 0.8, 0.0, name='aleron', gloss=0.5, base=False)
    for z in (-0.45, 0.45):
        _B(ms, 0.04, 0.1, 0.28, (255, 248, 230), 1.5, 0.5, z, glow=(160, 150, 120))
        _B(ms, 0.04, 0.09, 0.28, (210, 30, 30), -1.5, 0.52, z, glow=(120, 20, 20))
    gt = giro if giro_t is None else giro_t
    for k_, (x, z) in RUEDAS.items():
        adel = k_[0] == 'f'
        tb = traba_f if adel else traba_t
        g = (giro if adel else gt) * (1 - clamp(tb))
        w = V.rueda(R_LL, (0, 0, 0), g)
        w = P.tfk(w, ry=steer if adel else 0.0, t=(x, R_LL, z + 0.1))
        glow = None
        if tb > 0.02:
            glow = M.scale_c(ROJO, 0.85 * clamp(tb))
        if frena == k_:
            glow = M.scale_c(NARANJA, 0.95)
        if glow is not None:
            for m in w:
                if getattr(m, 'name', '') == 'llanta':
                    m.glow = glow
        ms += w
    return ms


def pose(ms, x=0.0, z=0.0, yaw=0.0):
    return P.tfk(ms, ry=yaw, t=(x, 0, z))


def rueda_mundo(k_, x, z, yaw):
    """Posición en el mundo del centro de la llanta k_ del carro puesto en (x, z, yaw)."""
    rx, rz = RUEDAS[k_]
    rz += 0.1
    a = math.radians(yaw)
    return (x + rx * math.cos(a) + rz * math.sin(a), R_LL, z - rx * math.sin(a) + rz * math.cos(a))


def humo(fr, t, fuentes, k=1.0, viento=(0.0, 0.0), n=9, seed=0, s=1.0):
    """Humo de llanta: nubes claras en la capa que brilla (se suman a la imagen, como humo iluminado por el foco)."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    for q, (px, py, pz) in enumerate(fuentes):
        for j in range(n):
            ph = (t * 1.4 + j / n + q * 0.37) % 1.0
            jx, jz = rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)
            p = (px + (viento[0] + jx) * ph * 1.4 * s, py - 0.1 + ph * 0.8 * s, pz + (viento[1] + jz) * ph * 1.4 * s)
            sc, z = fr.cam.proj([p])
            if z[0] < 0.2:
                continue
            x, y = sc[0]
            rr = (12 + 46 * ph) * s * M.SS * 3.4 / max(1.0, z[0])
            a = k * 0.34 * (1 - ph) ** 1.2
            fr.df.ellipse((x - rr, y - rr, x + rr, y + rr), fill=M.scale_c(HUMO, a))
            fr.df.ellipse((x - rr * 0.6, y - rr * 0.6, x + rr * 0.6, y + rr * 0.6), fill=M.scale_c(HUMO, a * 1.3))


def marcas(fr, pts, a=0.6, w=5):
    line3(fr, pts, col=(110, 110, 118), w=w, a=a, glow=0.0)


def circulo(R, n=48, a0=0.0, a1=360.0, cx=0.0, cz=0.0, y=0.01):
    return [(cx + R * math.cos(math.radians(a)), y, cz - R * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


def drift_pose(phi, R=2.2, beta=35.0, cx=0.0, cz=0.0):
    """Carro en un círculo (antihorario visto desde arriba) con la cola afuera: (x, z, yaw)."""
    x = cx + R * math.cos(math.radians(phi))
    z = cz - R * math.sin(math.radians(phi))
    return x, z, phi + 90 + beta


def ruedas_atras(x, z, yaw):
    return [rueda_mundo('ti', x, z, yaw), rueda_mundo('td', x, z, yaw)]


def lluvia(img, fx, t, k=1.0, n=70, seed=3):
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    d = ImageDraw.Draw(img)
    for j in range(n):
        x0 = rng.uniform(0, 1080)
        ph = (t * 2.2 + rng.rand()) % 1.0
        y0 = -100 + ph * 2100
        d.line([(x0, y0), (x0 - 14, y0 + 60)], fill=M.scale_c(AZULC, 0.55 * k), width=2)


def volante(ang=0.0):
    ms = [named(M3.torus(0.5, 0.06, (30, 30, 34), nu=40, nv=10).tf(rx=90), 'aro', rim=0.7, gloss=0.4)]
    for a in (90, 210, 330):
        b = M3.box(0.46, 0.07, 0.05, (60, 62, 68), shadow=0, base=False, gloss=0.5).tf(t=(0.23, 0, 0)).tf(rz=a)
        ms.append(named(b, 'rayo', rim=0.7))
    ms.append(named(M3.cyl(0.14, 0.08, (44, 46, 52), n=22, shadow=0, gloss=0.5, y0=-0.04).tf(rx=90), 'centro', rim=0.8))
    ms.append(named(M3.box(0.06, 0.1, 0.04, FRANJA, shadow=0, base=False).tf(t=(0, 0.5, 0.03)), 'marca', glow=M.scale_c(FRANJA, 0.4)))
    return P.tfk(ms, rz=ang)


def palanca(ang=0.0):
    """Freno de mano: base, palanca que sube (ang grados) y botón."""
    ms = []
    _B(ms, 0.9, 0.12, 0.3, (34, 34, 38), 0.0, 0.0, 0.0, name='base', gloss=0.3)
    lev = [tubo((0, 0, 0), (0.85, 0, 0), r=0.06, col=(50, 52, 58), name='palanca', gloss=0.5),
           named(M3.cyl(0.085, 0.32, (24, 24, 26), n=18, shadow=0, gloss=0.3).tf(rz=-90, t=(0.55, 0, 0)), 'mango', rim=0.6),
           named(M3.cyl(0.05, 0.08, (210, 40, 36), n=14, shadow=0, gloss=0.6).tf(rz=-90, t=(0.9, 0, 0)), 'boton', rim=0.8)]
    lev = P.tfk(lev, rz=ang, t=(-0.4, 0.12, 0))
    return ms + lev


def poste(x, z, h=2.6):
    return [named(M3.cyl(0.07, h, (150, 152, 160), n=14, shadow=0, gloss=0.7).tf(t=(x, 0, z)), 'poste', rim=0.8),
            named(M3.box(0.5, 0.06, 0.12, (150, 152, 160), shadow=0, base=False).tf(t=(x + 0.22, h, z)), 'poste', rim=0.8),
            named(M3.box(0.22, 0.05, 0.14, (255, 240, 200), shadow=0, base=False).tf(t=(x + 0.42, h - 0.04, z)), 'foco', glow=(150, 140, 110))]


def pila_llantas(x, z, n=3):
    return [named(M3.torus(0.3, 0.12, LLANTA, nu=22, nv=8).tf(t=(x, 0.12 + 0.24 * j, z)), 'llanta', rim=0.4) for j in range(n)]


def cono(x, z, s=1.0):
    return [named(M3.cyl(0.16 * s, 0.5 * s, CONO, n=18, shadow=0, gloss=0.5, r2=0.02 * s).tf(t=(x, 0.03, z)), 'cono', rim=0.7),
            named(M3.box(0.36 * s, 0.04, 0.36 * s, CONO, shadow=0, base=False).tf(t=(x, 0.02, z)), 'cono', rim=0.6),
            named(M3.cyl(0.11 * s, 0.07 * s, (240, 240, 244), n=18, shadow=0, gloss=0.5, r2=0.09 * s).tf(t=(x, 0.22 * s, z)), 'franja', rim=0.7)]


def icono_esc(img, fx, cx, cy, s, k=1.0, off=True, col=AMBAR):
    """Testigo del control de estabilidad (2D genérico): carrito con 2 rayitas en S y la palabra OFF."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    c = M.scale_c(col, k)
    d.rounded_rectangle((cx - 1.0 * s, cy - 0.75 * s, cx + 1.0 * s, cy + 0.05 * s), radius=int(0.25 * s), outline=c, width=max(3, int(s * 0.09)))
    df.rounded_rectangle((cx - 1.0 * s, cy - 0.75 * s, cx + 1.0 * s, cy + 0.05 * s), radius=int(0.25 * s), outline=M.scale_c(col, 0.5 * k), width=max(6, int(s * 0.2)))
    for x0 in (-0.55, 0.35):
        pts = [(cx + (x0 + 0.18 * math.sin(q * 6.3)) * s, cy + (0.2 + 0.7 * q) * s) for q in np.linspace(0, 1, 14)]
        d.line(pts, fill=c, width=max(3, int(s * 0.08)))
        df.line(pts, fill=M.scale_c(col, 0.5 * k), width=max(6, int(s * 0.18)))
    if off:
        d.text((cx, cy + 1.25 * s), 'OFF', font=M.font('sansx', int(0.6 * s)), fill=c, anchor='mm')
        df.text((cx, cy + 1.25 * s), 'OFF', font=M.font('sansx', int(0.6 * s)), fill=M.scale_c(col, 0.5 * k), anchor='mm')


def candado(img, fx, x, y, s, k=1.0, col=ROJO):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    c = M.scale_c(col, k)
    d.arc((x - 0.5 * s, y - 1.25 * s, x + 0.5 * s, y - 0.25 * s), 180, 360, fill=c, width=max(3, int(s * 0.18)))
    d.rounded_rectangle((x - 0.7 * s, y - 0.75 * s, x + 0.7 * s, y + 0.55 * s), radius=int(0.15 * s), fill=c)
    df.rounded_rectangle((x - 0.8 * s, y - 0.85 * s, x + 0.8 * s, y + 0.65 * s), radius=int(0.2 * s), fill=M.scale_c(col, 0.5 * k))
    d.ellipse((x - 0.14 * s, y - 0.35 * s, x + 0.14 * s, y - 0.07 * s), fill=(20, 20, 22))


def tache(img, fx, x, y, r, k, col=ROJO, w=14):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    kk = eout(k)
    for s_ in (-1, 1):
        d.line([(x - r * kk, y - s_ * r * kk), (x + r * kk, y + s_ * r * kk)], fill=col, width=w)
        df.line([(x - r * kk, y - s_ * r * kk), (x + r * kk, y + s_ * r * kk)], fill=M.scale_c(col, 0.6), width=w * 3)


def flecha_curva(img, fx, cx, cy, r, a0, a1, col, k=1.0, w=10):
    """Flecha en arco (2D) de a0 a a1 grados (0 = derecha, antihorario)."""
    if k <= 0.01:
        return
    a1 = a0 + (a1 - a0) * clamp(k)
    pts = [(cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 24)]
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.line(pts, fill=col, width=w, joint='curve')
    df.line(pts, fill=M.scale_c(col, 0.6), width=w * 3, joint='curve')
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    ang = math.atan2(yb - ya, xb - xa)
    for s_ in (-1, 1):
        d.line([(xb, yb), (xb - 34 * math.cos(ang + s_ * 0.5), yb - 34 * math.sin(ang + s_ * 0.5))], fill=col, width=w)


GIRO = lambda t, v=1.0: -t * 6.0 * v / R_LL

# ================================================================== escenas
UG = 0.85          # el trompo termina y cae el título


def _hook_cam(u):
    """Inicio 9: 3 cortes rítmicos con destello mientras el carro da la vuelta, y luego se asienta."""
    if u < 0.0:
        return camara(u, [K(-3.0, 8.8, 0, 50, ty=0.5), K(0.0, 8.4, 10, 46, ty=0.5)], cy=0.62)
    if u < 0.22:
        return camara(u, [K(0.0, 5.0, 40, 28, ty=0.5), K(0.22, 4.8, 44, 28, ty=0.5)], cy=0.62)
    if u < 0.48:
        return camara(u, [K(0.22, 5.4, -50, 20, ty=0.5), K(0.48, 5.2, -54, 20, ty=0.5)], cy=0.62)
    if u < 0.72:
        return camara(u, [K(0.48, 6.4, 160, 58, ty=0.5), K(0.72, 6.2, 166, 58, ty=0.5)], cy=0.62)
    return camara(u, [K(0.72, 5.4, 20, 18, ty=0.55), K(UG + 0.4, 5.0, 30, 16, ty=0.55), K(4.0, 4.9, 34, 16, ty=0.55)], cy=0.66)


def _hook_pose(u):
    if u < 0.0:     # loop: entra derrapando en un círculo que se cierra hacia el centro
        R = 1.5 * clamp(-u / 2.6)
        phi = u * 140
        x, z, yaw = drift_pose(phi, R=R, beta=40 * clamp(-u * 2))
        return x, z, yaw, 1.0
    k = P.eout4(seg(u, 0.0, UG))
    return 0.0, 0.0, 90 + 570 * k, 1.0 - seg(u, UG, UG + 1.0) * 0.7


def s_gancho(t, fi, u, d):
    fr = Frame(_hook_cam(u))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'CONTROL', u, t0=-2.6, cy=0.32, entrada='golpe')
    x, z, yaw, kh = _hook_pose(u)
    for R in (1.55, 1.75):
        marcas(fr, circulo(R, a0=0, a1=360 * clamp(0.3 + seg(u, -1.0, UG))), a=0.55)
    humo(fr, t, ruedas_atras(x, z, yaw), k=kh, viento=(0.0, 0.3), seed=1)
    draw_objects(fr, pose(auto(giro=GIRO(t), giro_t=GIRO(t, 2.5), steer=-18), x, z, yaw))

    def ui(img, fx):
        kicker(img, 'DRIFT · FRICCIÓN ESTÁTICA VS DINÁMICA', 140, seg(u, UG - 0.1, UG + 0.2), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu derrape no es', 'sans'), ('descontrol.', 'serif')], 190, seg(u, UG, UG + 0.15), size=84)
    fr.ui.append(ui)
    fl = max(golpe_k(u, 0.0, 0.14), golpe_k(u, 0.22, 0.14), golpe_k(u, 0.48, 0.14), golpe_k(u, 0.72, 0.14))
    img = finish(fr, fi, flash=0.55 * fl)
    return sacudir(img, t, max(golpe_k(u, UG + 0.15, 0.35), 0.5 * fl), amp=24)


# 1. una llanta que rueda agarra más («AGARRE» de cristal; la huella en verde)
def s_rueda(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 60, 8, ty=0.85), K(0.3, 4.2, 30, 6, ty=0.85), K(5, 4.15, 26, 6, ty=0.85)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'AGARRE', u, t0=Wp(1, 'agarra') - 0.3, cy=0.3, entrada='zoom')
    e = P.entrada(u, -0.25, 0.3, 'desliza')
    w, _ = LL.llanta_m(giro=math.degrees(GIRO(t, 0.5)), x=e['dy'])
    draw_objects(fr, w)
    for j in range(8):
        xm = -2.5 + ((j * 0.7 - t * 1.6) % 5.6)
        line3(fr, [(xm, 0.01, 0.4), (xm + 0.3, 0.01, 0.4)], col=WHITE, w=2.5, a=0.5, glow=0.3)

    def ui(img, fx):
        ka = seg(u, Wp(1, 'agarra') - 0.2, Wp(1, 'agarra') + 0.1)
        xa, ya, _ = fr.cam.p1((0, 0.0, 0.0))
        ImageDraw.Draw(img).ellipse((xa - 150 * ka, ya - 16, xa + 150 * ka, ya + 16), outline=VERDE, width=5)
        ImageDraw.Draw(fx).ellipse((xa - 150 * ka, ya - 16, xa + 150 * ka, ya + 16), outline=M.scale_c(VERDE, 0.6), width=14)
        pill(img, fx, 540, 1330, 'RUEDA = AGARRA', eout(seg(u, Wp(1, 'rueda') - 0.1, Wp(1, 'rueda') + 0.15)), size=34, border=VERDE, dot=False)
        kicker(img, 'FRICCIÓN ESTÁTICA', 300, seg(u, 0.0, 0.3), col=VERDE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. que una que se arrastra (la misma llanta trabada patina con humo y raya el piso)
def s_arrastra(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 20, 8, ty=0.85), K(0.3, 4.2, -10, 6, ty=0.85), K(5, 4.15, -14, 6, ty=0.85)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    xw = 0.4 * math.sin(u * 3)
    humo(fr, t, [(xw - 0.5, 0.25, 0.0)], k=1.0, viento=(-1.0, 0.0), seed=2, s=1.3)
    marcas(fr, [(xw - 3.0, 0.01, 0.0), (xw, 0.01, 0.0)], a=0.8, w=26)
    draw_objects(fr, LL.llanta_m(giro=20.0, x=xw)[0])

    def ui(img, fx):
        candado(img, fx, 540, 620, 60, seg(u, 0.0, 0.25))
        pill(img, fx, 540, 1330, 'SE ARRASTRA = RESBALA', eout(seg(u, Wp(2, 'arrastra') - 0.2, Wp(2, 'arrastra'))), size=34, border=ROJO, dot=False)
        kicker(img, 'FRICCIÓN DINÁMICA · AGARRA MENOS', 300, seg(u, 0.0, 0.3), col=ROJO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.25, amp=8)


# 3. si se traban las de adelante (vista de arriba: las de adelante en rojo con candado)
def s_adelante(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.2, -10, 50, ty=0.3), K(0.3, 6.2, 30, 40, ty=0.3), K(5, 6.1, 34, 40, ty=0.3)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.3)
    kt = seg(u, Wp(3, 'traban') - 0.1, Wp(3, 'traban') + 0.15)
    draw_objects(fr, auto(giro=GIRO(t), traba_f=kt))

    def ui(img, fx):
        for k_ in ('fi', 'fd'):
            x, y, _ = fr.cam.p1(rueda_mundo(k_, 0, 0, 0))
            candado(img, fx, x, y - 10, 26, kt)
        pill(img, fx, 540, 1330, 'ADELANTE: TRABADAS', eout(seg(u, Wp(3, 'adelante') - 0.2, Wp(3, 'adelante'))), size=32, border=ROJO, dot=False)
        kicker(img, 'CASO 1', 300, seg(u, 0.0, 0.25), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(3, 'traban') + 0.1, 0.25), amp=12)


# 4. el carro se va derecho… y ya no da vuelta (la curva sigue y el carro se sale derecho)
def s_derecho(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.0, -20, 56, tx=0.6, ty=0.2, tz=-0.8), K(0.3, 8.6, 0, 64, tx=1.2, ty=0.2, tz=-1.2),
                          K(5, 8.7, 0, 64, tx=1.3, ty=0.2, tz=-1.3)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.2)
    for R in (1.8, 3.4):
        line3(fr, circulo(R, a0=-90, a1=0, cz=-2.6), col=WHITE, w=3, a=0.8, glow=0.5)
    line3(fr, [(-4.0, 0.01, 0.8), (-0.0, 0.01, 0.8)], col=WHITE, w=3, a=0.8, glow=0.5)
    line3(fr, [(-4.0, 0.01, -0.8), (-0.0, 0.01, -0.8)], col=WHITE, w=3, a=0.8, glow=0.5)
    kx = seg(u, 0.0, d)
    x = -1.6 + 4.2 * P.eout4(kx) ** 0.8
    marcas(fr, [(-1.6, 0.01, 0.8), (x - 1.0, 0.01, 0.8)], a=0.7, w=8)
    marcas(fr, [(-1.6, 0.01, -0.48), (x - 1.0, 0.01, -0.48)], a=0.7, w=8)
    draw_objects(fr, pose(auto(giro=0.0, steer=28, traba_f=1.0, giro_t=GIRO(t)), x, 0.0, 0))

    def ui(img, fx):
        xa, ya, _ = fr.cam.p1((x + 1.6, 0.1, 0.0))
        V.flecha(img, fx, xa, ya, xa + 260, ya, ROJO, k=seg(u, 0.1, 0.5), w=12)
        xc, yc, _ = fr.cam.p1((2.2, 0.0, -1.4))
        texto(img, fx, xc - 30, yc + 30, 'LA CURVA', 34, AZULC, seg(u, 0.0, 0.3), f='mono', glow=0.3)
        tache(img, fx, 540, 470, 70, seg(u, Wp(4, 'vuelta') - 0.15, Wp(4, 'vuelta')))
        pill(img, fx, 540, 1330, 'VOLANTE GIRADO… Y SE VA DERECHO', eout(seg(u, Wp(4, 'derecho') - 0.2, Wp(4, 'derecho'))), size=28, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. si se traban las de atrás (ahora las de atrás en rojo; cámara gira de golpe)
def s_atras(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.0, 190, 50, ty=0.3), K(0.3, 6.2, 150, 40, ty=0.3), K(5, 6.1, 146, 40, ty=0.3)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.3)
    kt = seg(u, Wp(5, 'traban') - 0.1, Wp(5, 'traban') + 0.15)
    draw_objects(fr, auto(giro=GIRO(t), traba_t=kt))

    def ui(img, fx):
        for k_ in ('ti', 'td'):
            x, y, _ = fr.cam.p1(rueda_mundo(k_, 0, 0, 0))
            candado(img, fx, x, y - 10, 26, kt)
        pill(img, fx, 540, 1330, 'ATRÁS: TRABADAS', eout(seg(u, Wp(5, 'atras') - 0.2, Wp(5, 'atras'))), size=32, border=ROJO, dot=False)
        kicker(img, 'CASO 2', 300, seg(u, 0.0, 0.25), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(5, 'traban') + 0.1, 0.25), amp=12)


# 6. la cola se adelanta… y das trompo («TROMPO» de cristal; el carro gira 200° con humo)
def s_trompo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.6, 10, 58, ty=0.3), K(0.3, 7.0, 40, 54, ty=0.3), K(5, 6.9, 46, 54, ty=0.3)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, 'TROMPO', u, t0=Wp(6, 'trompo') - 0.3, cy=0.27, entrada='golpe')
    kr = P.eout4(seg(u, Wp(6, 'cola') - 0.1, Wp(6, 'trompo') + 0.4))
    yaw = 220 * kr
    x = 1.2 * P.eout4(seg(u, -0.2, d))
    humo(fr, t, ruedas_atras(x, 0, yaw), k=kr * (1 - seg(u, d - 0.5, d)), seed=3)
    marcas(fr, circulo(1.0, a0=0, a1=yaw, cx=x, cz=0.0), a=0.6, w=6)
    draw_objects(fr, pose(auto(giro=0.0, traba_t=1.0), x, 0, yaw))

    def ui(img, fx):
        flecha_curva(img, fx, 540, 1060, 330, 200, 200 + 160 * kr, ROJO, k=seg(u, Wp(6, 'cola') - 0.2, Wp(6, 'cola') + 0.3), w=12)
        pill(img, fx, 540, 1380, 'LA COLA SE ADELANTA', eout(seg(u, Wp(6, 'adelanta') - 0.2, Wp(6, 'adelanta'))), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(6, 'trompo'), 0.35), amp=20)


# 7. por eso existe el ABS (rayos X: sensores en las 4 llantas y el módulo; entra con la transición `cristal`)
def s_abs(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.6, 50, 34, ty=0.4), K(0.3, 5.0, 24, 30, ty=0.4), K(5, 4.9, 20, 30, ty=0.4)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    ms = auto(giro=GIRO(t))
    _B(ms, 0.3, 0.16, 0.24, (60, 64, 72), 0.9, 0.48, -0.25, name='modulo', gloss=0.6, glow=M.scale_c(CYAN, 0.5))
    draw_objects(fr, ms, xray=0.85, keep=('modulo', 'llanta', 'rin'))
    for k_ in RUEDAS:
        p = rueda_mundo(k_, 0, 0, 0)
        line3(fr, [(0.9, 0.48, -0.25), (p[0], 0.45, p[2])], col=CYAN, w=2.5, a=0.9, glow=0.9, frac=seg(u, 0.0, 0.4))
        dot3(fr, (p[0], 0.45, p[2]), r=7, col=CYAN, a=seg(u, 0.2, 0.4), glow=1.2)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0.9, 0.48, -0.25))
        pill(img, fx, x, y - 150, 'MÓDULO ABS', eout(seg(u, 0.1, 0.35)), size=30, border=CYAN)
        pill(img, fx, 540, 1380, 'UN SENSOR EN CADA LLANTA', eout(seg(u, 0.3, 0.55)), size=30, border=CYAN, dot=False)
        P.titulo_golpe(img, fx, [('ABS', 'sans')], 260, seg(u, Wp(7, 'abs') - 0.1, Wp(7, 'abs') + 0.05), size=120, col=AMBAR)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(7, 'abs') + 0.05, 0.25), amp=12)


# 8. suelta y aprieta el freno (el disco de cerca: el caliper pulsa y la gráfica hace dientes)
def s_pulsa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, -40, 10, ty=0.0), K(0.3, 2.7, -14, 6, ty=0.0), K(5, 2.65, -10, 6, ty=0.0)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    pulso = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 6)
    ms = EL.disco(calor=0.15 * pulso, giro=-t * 180 * (0.4 + 0.6 * pulso))
    draw_objects(fr, P.tfk(ms, s=0.95, t=(-0.1, -0.1, 0)))

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        x0, y0, w, h = 140, 1250, 800, 120
        kq = seg(u, 0.0, 0.8)
        pts = []
        for q in np.linspace(0, kq, 160):
            tt = q * 3.0
            v = 1.0 if (tt * 6) % 1.0 < 0.5 else 0.25
            pts.append((x0 + w * q, y0 + h * (1 - v)))
        if len(pts) > 1:
            d_.line(pts, fill=AMBAR, width=5)
            df.line(pts, fill=M.scale_c(AMBAR, 0.6), width=14)
        texto(img, fx, x0, y0 - 40, 'PRESIÓN DEL FRENO (ESQUEMA)', 26, GRIS, seg(u, 0.0, 0.3), f='mono', glow=0.0, anchor='lm')
        on = (t * 6) % 1.0 < 0.5
        texto(img, fx, 540, 420, 'APRIETA' if on else 'SUELTA', 88, ROJO if on else VERDE, seg(u, Wp(8, 'suelta') - 0.1, Wp(8, 'suelta') + 0.05), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. para que la llanta siga rodando y puedas girar (frena en la curva y sí da vuelta)
def s_girar(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 9.0, 0, 70, ty=0.2), K(0.3, 8.4, -20, 66, ty=0.2), K(5, 8.3, -24, 66, ty=0.2)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.2)
    for R in (1.4, 3.0):
        line3(fr, circulo(R, a0=-90, a1=0, cx=0.0, cz=-2.2), col=WHITE, w=3, a=0.8, glow=0.5)
    ka = seg(u, -0.2, d)
    phi = -90 + 90 * P.eout4(ka) ** 0.9
    x, z, yaw = drift_pose(phi, R=2.2, beta=0.0, cz=-2.2)
    draw_objects(fr, pose(auto(giro=GIRO(t, 0.6), steer=20), x, z, yaw))

    def ui(img, fx):
        xa, ya, _ = fr.cam.p1((x, 0.6, z))
        texto(img, fx, xa, ya - 150, '✓', 110, VERDE, seg(u, Wp(9, 'girar') - 0.15, Wp(9, 'girar')), f='sansx', glow=0.6)
        pill(img, fx, 540, 1330, 'RUEDA · AGARRA · GIRA', eout(seg(u, Wp(9, 'rodando') - 0.2, Wp(9, 'rodando'))), size=32, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. el piloto de drift suelta las de atrás a propósito (drift en círculo, de lado, con humo)
def _drift_escena(t, u, claves, beta=38.0, cy=0.6, floor='lines', R=2.3, vel=70.0, steer=-22):
    fr = Frame(camara(u, claves, cy=cy))
    space(fr, t, floor=floor, floor_a=0.7, bokeh=1.0, beam=0.35)
    phi = 30 + vel * t
    x, z, yaw = drift_pose(phi, R=R, beta=beta)
    marcas(fr, circulo(R + 0.45, a0=phi - 160, a1=phi - 10), a=0.5, w=6)
    marcas(fr, circulo(R - 0.35, a0=phi - 160, a1=phi - 10), a=0.5, w=6)
    humo(fr, t, ruedas_atras(x, z, yaw), k=1.0, seed=4)
    ms = pose(auto(giro=GIRO(t), giro_t=GIRO(t, 3.0), steer=steer), x, z, yaw)
    return fr, ms, (x, z, yaw)


def s_piloto(t, fi, u, d):
    fr, ms, (x, z, yaw) = _drift_escena(t, u, [K(-0.3, 11.0, -30, 50, ty=0.3), K(0.3, 9.6, 0, 58, ty=0.3), K(5, 9.5, 4, 58, ty=0.3)])
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'DRIFT · A PROPÓSITO', 300, seg(u, 0.0, 0.3), col=AMARILLO)
        for k_, txt, col in (('ti', 'RESBALAN', ROJO), ('fi', 'RUEDAN', VERDE)):
            xw, yw, _ = fr.cam.p1(rueda_mundo(k_, x, z, yaw))
            pill(img, fx, xw, yw - 90, txt, eout(seg(u, Wp(10, 'atras') - 0.2 if col == ROJO else Wp(10, 'proposito'), Wp(10, 'atras') + 0.1 if col == ROJO else Wp(10, 'proposito') + 0.3)), size=26, border=col)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. con el acelerador, y las de adelante siguen rodando (el pedal a fondo; la cámara entra con `push` desde el carro)
def s_acelerador(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, -60, 10, ty=-0.4), K(0.3, 3.0, -30, 8, ty=-0.4), K(5, 2.95, -26, 8, ty=-0.4)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    kp = P.resorte(seg(u, Wp(11, 'acelerador') - 0.25, Wp(11, 'acelerador') + 0.2))
    draw_objects(fr, EL.pedal(ang=-24 * kp))

    def ui(img, fx):
        d_ = ImageDraw.Draw(img)
        x0, y0, w, h = 860, 560, 60, 600
        d_.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=14, outline=M.scale_c(WHITE, 0.7), width=4)
        hh = h * (0.15 + 0.8 * clamp(kp))
        d_.rounded_rectangle((x0 + 8, y0 + h - hh + 8, x0 + w - 8, y0 + h - 8), radius=10, fill=AMBAR)
        texto(img, fx, x0 + w / 2, y0 - 40, 'GAS', 30, AMBAR, 1.0, f='mono', glow=0.4)
        pill(img, fx, 540, 1330, 'ACELERADOR = LAS DE ATRÁS PATINAN', eout(seg(u, Wp(11, 'acelerador') - 0.2, Wp(11, 'acelerador'))), size=26, border=AMBAR, dot=False)
        pill(img, fx, 540, 1400, 'LAS DE ADELANTE SIGUEN RODANDO', eout(seg(u, Wp(11, 'adelante') - 0.2, Wp(11, 'adelante'))), size=26, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(11, 'acelerador') + 0.2, 0.3), amp=10)


# 12. con el contravolante apunta el carro (el volante gira al revés y el carro de arriba con las llantas contra)
def s_contra(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, 30, 6, ty=1.0), K(0.3, 2.9, 6, 4, ty=1.0), K(5, 2.85, 2, 4, ty=1.0)], cy=0.42))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    kv = P.resorte(seg(u, Wp(12, 'contravolante') - 0.2, Wp(12, 'contravolante') + 0.3))
    draw_objects(fr, P.tfk(volante(ang=-95 * kv), t=(0, 1.0, 0)))

    def ui(img, fx):
        flecha_curva(img, fx, 540, 806, 330, 120, 120 - 95 * kv, AMARILLO, k=kv, w=12)
        P.titulo_golpe(img, fx, [('Contravolante', 'serif')], 1180, seg(u, Wp(12, 'contravolante'), Wp(12, 'contravolante') + 0.15), size=86, col=AMARILLO)
        pill(img, fx, 540, 1330, 'LAS LLANTAS APUNTAN A DONDE VAS', eout(seg(u, Wp(12, 'apunta') - 0.2, Wp(12, 'apunta'))), size=28, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. y con el pie derecho decide qué tanto se abre la cola (arriba: el ángulo se abre y se cierra con el gas)
def s_angulo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.8, 0, 76, ty=0.2), K(0.3, 6.8, 0, 72, ty=0.2), K(5, 6.7, 0, 72, ty=0.2)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.2)
    g = 0.5 + 0.5 * math.sin(u * 3.2)
    beta = 18 + 30 * g
    humo(fr, t, ruedas_atras(0, 0, beta), k=0.6 + 0.4 * g, seed=5)
    draw_objects(fr, pose(auto(giro=GIRO(t), giro_t=GIRO(t, 3.0), steer=-beta * 0.6), 0, 0, beta))

    def ui(img, fx):
        cx, cy, _ = fr.cam.p1((0, 0.3, 0))
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        r = 330
        d_.line([(cx, cy), (cx - r, cy)], fill=M.scale_c(WHITE, 0.6), width=3)
        a = math.radians(180 + beta)
        d_.line([(cx, cy), (cx + r * math.cos(a), cy - r * math.sin(a))], fill=AMARILLO, width=5)
        d_.arc((cx - 200, cy - 200, cx + 200, cy + 200), 180 - beta, 180, fill=AMARILLO, width=6)
        df.arc((cx - 200, cy - 200, cx + 200, cy + 200), 180 - beta, 180, fill=M.scale_c(AMARILLO, 0.6), width=16)
        texto(img, fx, cx - 260, cy - 120, f'{beta:.0f}°', 64, AMARILLO, seg(u, 0.0, 0.3), f='mono', glow=0.5)
        x0, y0, w, h = 900, 620, 56, 520
        d_.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=14, outline=M.scale_c(WHITE, 0.7), width=4)
        hh = h * (0.2 + 0.75 * g)
        d_.rounded_rectangle((x0 + 8, y0 + h - hh + 8, x0 + w - 8, y0 + h - 8), radius=10, fill=AMBAR)
        texto(img, fx, x0 + w / 2, y0 - 40, 'GAS', 30, AMBAR, 1.0, f='mono', glow=0.4)
        pill(img, fx, 540, 1330, 'MÁS GAS = MÁS ÁNGULO', eout(seg(u, Wp(13, 'pie') - 0.2, Wp(13, 'pie'))), size=32, border=AMBAR, dot=False)
        esquema(img, fx, 1.0, y=1400, txt='EJEMPLO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. y aquí está el error (el carro en la calle de noche, rojo)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.4, 50, 24, ty=0.5), K(0.3, 5.6, 24, 20, ty=0.5), K(5, 5.55, 20, 20, ty=0.5)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    draw_objects(fr, auto(giro=GIRO(t, 0.5), col=M.mixc(CARRO, (200, 60, 50), 0.35)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 300, seg(u, 0.05, 0.2), size=92)
        texto(img, fx, 540, 1330, '⚠', 140, ROJO, seg(u, 0.2, 0.35), f='sansx', glow=0.8)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.35), amp=20)


# 15. jalar el freno de mano en la calle («CALLE» de cristal; la palanca sube de golpe)
def s_mano(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, 60, 20, ty=0.3), K(0.3, 2.8, 30, 16, ty=0.3), K(5, 2.75, 26, 16, ty=0.3)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'CALLE', u, t0=Wp(15, 'calle') - 0.3, cy=0.28, entrada='sube')
    kj = P.resorte(seg(u, Wp(15, 'jalar') - 0.1, Wp(15, 'jalar') + 0.2))
    draw_objects(fr, palanca(ang=38 * kj))

    def ui(img, fx):
        pill(img, fx, 540, 1330, 'FRENO DE MANO', eout(seg(u, Wp(15, 'freno') - 0.2, Wp(15, 'freno'))), size=34, border=ROJO, dot=False)
        texto(img, fx, 540, 1430, '¡CLAC!', 60, WHITE, seg(u, Wp(15, 'jalar') + 0.1, Wp(15, 'jalar') + 0.25) * (1 - seg(u, Wp(15, 'jalar') + 0.6, Wp(15, 'jalar') + 0.9)), f='sansx', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(15, 'jalar') + 0.2, 0.3), amp=16)


# 16. traba las de atrás, la cola se suelta (en la calle: las de atrás rojas y el carro empieza a girar)
def calle(fr, a=0.8):
    for z in (-2.2, 2.2):
        line3(fr, [(-9, 0.01, z), (9, 0.01, z)], col=WHITE, w=3, a=a, glow=0.4)
    for j in range(8):
        x = -8 + j * 2.2
        line3(fr, [(x, 0.01, 0), (x + 1.0, 0.01, 0)], col=AMARILLO, w=3, a=a, glow=0.5)


def s_traba(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.8, -120, 24, tx=-0.6, ty=0.3), K(0.3, 6.4, -150, 40, ty=0.3), K(5, 6.3, -154, 40, ty=0.3)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.3)
    calle(fr)
    kt = seg(u, Wp(16, 'traba') - 0.1, Wp(16, 'traba') + 0.1)
    ks = P.eout4(seg(u, Wp(16, 'suelta') - 0.2, d + 0.4))
    yaw = 70 * ks
    x = 1.6 * seg(u, -0.2, d)
    humo(fr, t, ruedas_atras(x, 0, yaw), k=kt, seed=6)
    draw_objects(fr, pose(auto(giro=GIRO(t), traba_t=kt), x, 0, yaw))

    def ui(img, fx):
        for k_ in ('ti', 'td'):
            xw, yw, _ = fr.cam.p1(rueda_mundo(k_, x, 0, yaw))
            candado(img, fx, xw, yw - 70, 22, kt)
        pill(img, fx, 540, 1330, 'LA COLA SE SUELTA', eout(seg(u, Wp(16, 'cola') - 0.2, Wp(16, 'cola'))), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(16, 'traba') + 0.1, 0.3), amp=14)


# 17. y en la calle no hay muro de llantas: hay postes, banquetas y gente
def s_postes(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 10.4, -20, 36, tx=1.4, ty=0.3), K(0.3, 9.4, 10, 30, tx=1.8, ty=0.3), K(5, 9.3, 14, 30, tx=1.8, ty=0.3)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.3)
    calle(fr)
    ka = P.eout4(seg(u, -0.2, d))
    x, yaw = 1.0 + 1.6 * ka, 70 + 140 * ka
    zc = -0.6 * ka
    humo(fr, t, ruedas_atras(x, zc, yaw), k=1.0 - 0.5 * ka, seed=7)
    ms = pose(auto(giro=0.0, traba_t=1.0), x, zc, yaw)
    ms.append(named(M3.box(9.0, 0.16, 0.6, (120, 120, 126), shadow=0, gloss=0.2).tf(t=(1.0, 0, -2.6)), 'banqueta', rim=0.5))
    for xp in (-1.0, 2.2, 5.4):
        ms += poste(xp, -2.7)
    up = Wp(17, 'muro')
    ms += pila_llantas(-2.4, 1.0) if u < up + 0.6 else []
    draw_objects(fr, ms)
    for j in range(6):
        line3(fr, [(3.6 + j * 0.32, 0.012, -2.2), (3.6 + j * 0.32, 0.012, -0.4)], col=WHITE, w=10, a=0.8, glow=0.2)

    def ui(img, fx):
        kicker(img, 'EN LA CALLE', 300, seg(u, 0.0, 0.3), col=AZULC)
        xm, ym, _ = fr.cam.p1((-2.4, 0.5, 1.0))
        if u < up + 0.6:
            tache(img, fx, xm, ym, 80, seg(u, up - 0.05, up + 0.15))
        for j, (w, txt) in enumerate((('postes', 'POSTES'), ('banquetas', 'BANQUETAS'), ('gente', 'GENTE'))):
            pill(img, fx, 210 + 330 * j, 1330, txt, eout(seg(u, Wp(17, w) - 0.2, Wp(17, w))), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(17, 'gente'), 0.3), amp=12)


# 18. y apagar el control de estabilidad con lluvia es peor (el testigo OFF parpadea y llueve)
def s_esc(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, -40, 22, ty=0.5), K(0.3, 5.4, -16, 18, ty=0.5), K(5, 5.35, -12, 18, ty=0.5)], cy=0.7))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=1.0, beam=0.3)
    draw_objects(fr, auto(giro=GIRO(t, 0.6)))

    def ui(img, fx):
        lluvia(img, fx, t, k=seg(u, Wp(18, 'lluvia') - 0.3, Wp(18, 'lluvia')))
        on = (t * 3) % 1.0 < 0.65
        icono_esc(img, fx, 540, 420, 110, k=seg(u, Wp(18, 'apagar') - 0.1, Wp(18, 'apagar') + 0.1) * (1.0 if on else 0.35))
        pill(img, fx, 540, 1330, 'CONTROL DE ESTABILIDAD', eout(seg(u, Wp(18, 'control') - 0.2, Wp(18, 'control'))), size=30, border=AMBAR, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. el agarre baja casi a la mitad («MITAD» de cristal; barras seco 0.7 vs mojado 0.4)
def s_mitad(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.2, 50, 10, ty=0.85), K(0.3, 4.6, 30, 8, ty=0.85), K(5, 4.55, 26, 8, ty=0.85)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'MITAD', u, t0=Wp(19, 'mitad') - 0.3, cy=0.27, entrada='zoom')
    draw_objects(fr, LL.llanta_m(giro=math.degrees(GIRO(t, 0.3)))[0])

    def ui(img, fx):
        lluvia(img, fx, t, k=0.7)
        d_ = ImageDraw.Draw(img)
        for j, (lab, v, col, w) in enumerate((('SECO', 0.7, VERDE, 'agarre'), ('MOJADO', 0.4, AZULC, 'baja'))):
            kb = P.eout4(seg(u, Wp(19, w) - 0.1, Wp(19, w) + 0.3))
            x0 = 330 + 300 * j
            hh = 420 * v * kb
            d_.rectangle((x0, 1330 - hh, x0 + 120, 1330), fill=col)
            texto(img, fx, x0 + 60, 1330 - hh - 40, f'{v * kb:.1f}', 44, col, kb, f='mono', glow=0.4)
            texto(img, fx, x0 + 60, 1370, lab, 28, col, kb, f='mono', glow=0.2)
        pill(img, fx, 540, 1450, 'AGARRE APROX. · HYPERPHYSICS', seg(u, 0.2, 0.5), size=20, border=GRIS, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. ese control frena una llanta por ti antes del trompo (arriba: la de adelante de afuera frena en naranja)
def s_frena(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.4, 30, 68, ty=0.2), K(0.3, 6.8, 0, 72, ty=0.2), K(5, 6.7, -4, 72, ty=0.2)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.2)
    uf = Wp(20, 'frena') - 0.1
    yaw = 34 * seg(u, -0.2, uf) - 34 * P.eout4(seg(u, uf, uf + 0.8))
    draw_objects(fr, pose(auto(giro=GIRO(t, 0.6), frena='fi' if u > uf else None), 0, 0, yaw))

    def ui(img, fx):
        cx, cy, _ = fr.cam.p1((0, 0.3, 0))
        flecha_curva(img, fx, cx, cy, 300, 200, 160, VERDE, k=seg(u, uf + 0.1, uf + 0.6), w=12)
        xw, yw, _ = fr.cam.p1(rueda_mundo('fi', 0, 0, yaw))
        pill(img, fx, xw, yw + 110, 'FRENA ESTA', eout(seg(u, uf, uf + 0.25)), size=28, border=NARANJA)
        pill(img, fx, 540, 1330, 'ANTES DEL TROMPO', eout(seg(u, Wp(20, 'trompo') - 0.2, Wp(20, 'trompo'))), size=32, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. en EE. UU. bajó más de un tercio los choques mortales de un solo carro (−36 % golpea; NHTSA)
def s_tercio(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.0, -40, 30, ty=0.5), K(0.3, 6.4, -20, 26, ty=0.5), K(5, 6.35, -16, 26, ty=0.5)], cy=0.75))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=1.0, beam=0.4)
    draw_objects(fr, auto(giro=GIRO(t, 0.5)))
    un = Wp(21, 'tercio') - 0.15

    def ui(img, fx):
        n = 36 * P.eout4(seg(u, un - 0.5, un + 0.1))
        P.numero_golpe(img, fx, f'−{n:.0f} %', 560, seg(u, un - 0.5, un + 0.1), size=260, col=VERDE)
        kicker(img, 'NHTSA · CHOQUES MORTALES DE UN SOLO CARRO', 330, seg(u, 0.0, 0.3), col=AZULC)
        pill(img, fx, 540, 800, 'CAMIONETAS: −63 %', eout(seg(u, Wp(21, 'mortales') - 0.2, Wp(21, 'mortales'))), size=30, border=VERDE, dot=False)
        pill(img, fx, 540, 1450, 'CON CONTROL DE ESTABILIDAD · ESTUDIO 2007', seg(u, 0.4, 0.7), size=20, border=GRIS, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.1, 0.35), amp=20)


# 22. el drift se aprende en pista, con casco y con permiso («PISTA» de cristal; conos y muro de llantas)
def s_pista(t, fi, u, d):
    fr, ms, (x, z, yaw) = _drift_escena(t, u, [K(-0.3, 12.4, 60, 40, ty=0.3), K(0.3, 11.2, 30, 44, ty=0.3), K(5, 11.1, 26, 44, ty=0.3)], cy=0.64, R=2.4, vel=80)
    M.cristal(fr.base, fr.fx, 'PISTA', u, t0=Wp(22, 'pista') - 0.3, cy=0.27, entrada='golpe')
    for a in range(0, 360, 60):
        ms += cono(0.6 * math.cos(math.radians(a)), 0.6 * math.sin(math.radians(a)), s=0.9)
    for j in range(7):
        ms += pila_llantas(-4.2 + j * 1.4, -4.2, n=2)
    draw_objects(fr, ms)

    def ui(img, fx):
        for j, (txt, w) in enumerate((('✓ PISTA', 'pista'), ('✓ CASCO', 'casco'), ('✓ PERMISO', 'permiso'))):
            texto(img, fx, 140, 1250 + 70 * j, txt, 46, VERDE, seg(u, Wp(22, w) - 0.2, Wp(22, w)), f='sansx', glow=0.4, anchor='lm')
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. mándaselo a tu compa que se siente piloto en la glorieta (la glorieta con su jardín)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 12.5, -30, 56, ty=0.2), K(0.3, 11.2, 0, 60, ty=0.2), K(5, 11.1, 4, 60, ty=0.2)], cy=0.66))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.2)
    for R in (1.4, 3.4):
        line3(fr, circulo(R, n=72), col=WHITE, w=3, a=0.8, glow=0.5)
    phi = 40 + 60 * t
    x, z, yaw = drift_pose(phi, R=2.4, beta=12)
    ms = pose(auto(giro=GIRO(t, 0.6), steer=10), x, z, yaw)
    ms.append(named(M3.cyl(1.25, 0.2, (40, 110, 60), n=40, shadow=0, gloss=0.2), 'jardin', rim=0.4))
    draw_objects(fr, ms)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que se siente piloto.', 'serif')], 250, seg(u, 0.05, 0.2), size=64)
        pill(img, fx, 540, 1380, 'LA GLORIETA NO ES PISTA', eout(seg(u, Wp(23, 'glorieta') - 0.2, Wp(23, 'glorieta'))), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55),
                sfx=[(-2.6, 'whoosh_suave', 0.4), (0.0, 'sub', 0.9), (0.0, 'burst', 0.5), (0.22, 'burst', 0.5), (0.48, 'burst', 0.5),
                     (0.72, 'burst', 0.5), (0.05, 'whoosh', 0.6), (UG + 0.15, 'bass', 0.9)]),
           dict(desde=1, fn=s_rueda, tr='remolino', c=(0.5, 0.5), sfx=[(0.0, 'whoosh_suave', 0.4)]),
           dict(desde=2, fn=s_arrastra, tr='wipe', sfx=[(0.0, 'burst', 0.5), (0.05, 'click', 0.6)]),
           dict(desde=3, fn=s_adelante, tr='cubo', sfx=[]),
           dict(desde=4, fn=s_derecho, tr='whip', sfx=[(0.1, 'whoosh', 0.5)]),
           dict(desde=5, fn=s_atras, tr='cubo_izq', sfx=[]),
           dict(desde=6, fn=s_trompo, tr='giro', sfx=[(0.0, 'burst', 0.4)]),
           dict(desde=7, fn=s_abs, tr='cristal', palabra='ABS', sfx=[(0.0, 'digital', 0.4)]),
           dict(desde=8, fn=s_pulsa, tr='mosaico', sfx=[(0.1 + 0.167 * j, 'tick', 0.35) for j in range(10)]),
           dict(desde=9, fn=s_girar, tr='deslizar', sfx=[]),
           dict(desde=10, fn=s_piloto, tr='flash', sfx=[(0.1, 'whoosh_suave', 0.5)]),
           dict(desde=11, fn=s_acelerador, tr='push', c=(0.42, 0.62), sfx=[]),
           dict(desde=12, fn=s_contra, tr='iris', c=(0.5, 0.42), sfx=[]),
           dict(desde=13, fn=s_angulo, tr='deslizar_abajo', sfx=[(0.2, 'scribble', 0.4)]),
           dict(desde=14, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.15, 'sub', 0.9), (0.2, 'bass', 0.7)]),
           dict(desde=15, fn=s_mano, tr='golpe', sfx=[]),
           dict(desde=16, fn=s_traba, tr='zoom', c=(0.45, 0.6), sfx=[]),
           dict(desde=17, fn=s_postes, tr='whip_izq', sfx=[]),
           dict(desde=18, fn=s_esc, tr='glitch', sfx=[]),
           dict(desde=19, fn=s_mitad, tr='rebanadas', sfx=[]),
           dict(desde=20, fn=s_frena, tr='giro', sfx=[]),
           dict(desde=21, fn=s_tercio, tr='golpe', sfx=[]),
           dict(desde=22, fn=s_pista, tr='flash', sfx=[(0.1, 'whoosh_suave', 0.4)]),
           dict(desde=23, fn=s_compa, tr='deslizar', sfx=[(0.05, 'slap', 0.7)]),
           dict(desde=24, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    add = {1: [(Wp(1, 'agarra') - 0.3, 'cristal', 0.6), (Wp(1, 'agarra'), 'chime_a', 0.4)],
           2: [(Wp(2, 'arrastra') - 0.1, 'burst', 0.4)],
           3: [(Wp(3, 'traban'), 'click', 0.8), (Wp(3, 'traban') + 0.05, 'thud', 0.7)],
           4: [(Wp(4, 'derecho') - 0.1, 'whoosh', 0.5), (Wp(4, 'vuelta') - 0.1, 'bass', 0.7)],
           5: [(Wp(5, 'traban'), 'click', 0.8), (Wp(5, 'traban') + 0.05, 'thud', 0.7)],
           6: [(Wp(6, 'cola') - 0.1, 'whoosh', 0.6), (Wp(6, 'trompo') - 0.3, 'cristal', 0.6), (Wp(6, 'trompo'), 'sub', 0.9)],
           7: [(Wp(7, 'abs') - 0.1, 'bass', 0.8)],
           8: [(Wp(8, 'aprieta'), 'click', 0.6)],
           9: [(Wp(9, 'girar') - 0.15, 'chime_c', 0.5)],
           10: [(Wp(10, 'atras') - 0.2, 'tick', 0.5), (Wp(10, 'proposito'), 'tick2', 0.5)],
           11: [(Wp(11, 'acelerador') - 0.2, 'riser', 0.4), (Wp(11, 'acelerador') + 0.2, 'thud', 0.8)],
           12: [(Wp(12, 'contravolante') - 0.2, 'whoosh', 0.6), (Wp(12, 'contravolante') + 0.15, 'bass', 0.6)],
           13: [(Wp(13, 'pie') - 0.2, 'tick', 0.5), (Wp(13, 'cola') - 0.2, 'whoosh_suave', 0.4)],
           15: [(Wp(15, 'jalar'), 'click', 0.9), (Wp(15, 'jalar') + 0.15, 'thud', 0.9), (Wp(15, 'calle') - 0.3, 'cristal', 0.6)],
           16: [(Wp(16, 'traba'), 'click', 0.8), (Wp(16, 'suelta') - 0.1, 'burst', 0.5)],
           17: [(Wp(17, 'muro') - 0.05, 'bass', 0.6)] + [(Wp(17, w) - 0.2, 'tick2', 0.5) for w in ('postes', 'banquetas', 'gente')],
           18: [(Wp(18, 'apagar') - 0.1, 'digital', 0.6), (Wp(18, 'lluvia') - 0.3, 'whoosh_suave', 0.4)],
           19: [(Wp(19, 'mitad') - 0.3, 'cristal', 0.6), (Wp(19, 'agarre'), 'chime_b', 0.4), (Wp(19, 'baja'), 'chime_a', 0.4)],
           20: [(Wp(20, 'frena') - 0.1, 'thud', 0.8), (Wp(20, 'trompo'), 'chime_c', 0.4)],
           21: [(Wp(21, 'tercio') - 0.65 + 0.06 * j, 'tick', 0.35) for j in range(8)] + [(Wp(21, 'tercio') - 0.05, 'sub', 0.9)],
           22: [(Wp(22, 'pista') - 0.3, 'cristal', 0.6)] + [(Wp(22, w) - 0.2, 'chime_b', 0.4) for w in ('casco', 'permiso')]}
    for e in ESCENAS:
        if e.get('desde') in add and not e.get('loop'):
            e['sfx'] = list(e.get('sfx', [])) + add[e['desde']]


_sfx_dinamicos()


def tiempos_falsos():
    T = [(round(0.25 + 2.6 * i, 2), round(0.25 + 2.6 * i + 2.2, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.55, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    print('ok', T[-1])


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    else:
        montaje.cli(globals())
