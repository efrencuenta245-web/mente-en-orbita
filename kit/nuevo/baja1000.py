"""Reel diario vie 13-nov-2026 10:00 — «Tu camioneta no aguantaría… este brinco.» (59.ª SCORE Baja 1000, Cabo a Cabo).
Comunidad: off-road / riders (decisión de Efrén del 10-nov: vehículos y comunidades mexicanas por dentro).
Inicio tipo 12 (cuenta regresiva): en la salida de San José del Cabo cae 3-2-1, el Trophy Truck arranca, vuela del
brinco con la suspensión colgando y aterriza con sacudida mientras se estrella el título. El final regresa a la salida
con el «3» (loop). Voz Isaac (eleven_v4), 65.3 s. Datos y fuentes: guiones/2026-11-13_baja1000.txt.
Todo es recreación en 3D (los Trophy Truck van cubiertos de logos de patrocinadores): se marca «RECREACIÓN».
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'baja1000'
TXT = ['Tu camioneta no aguantaría… este brinco.',
       'Hoy arranca la Baja 1000, y por primera vez es toda en Baja California Sur.',
       'De Cabo a Cabo: más de 1 500 kilómetros de desierto.',
       'Mira por dentro: una pickup de fábrica sube y baja la llanta, cuando mucho, 38 centímetros.',
       'Un Trophy Truck, casi un metro.',
       'Cae del brinco y la suspensión se traga el golpe.',
       'Pero el error más peligroso de la carrera… lo comete el público.',
       'Pararse afuera de la curva: justo ahí se sale un camión de más de 800 caballos.',
       'En la Baja 500 de 2016, un camión se salió en una curva y le pegó a tres espectadores.',
       'Por eso SCORE pide verla a más de 30 metros, y nada de hacerle brincos o zanjas al camino.',
       'Y adentro del amortiguador hay otra carrera: cada golpe se vuelve calor.',
       'Tras horas de desierto, el aceite se pone aguadito y deja de frenar el rebote.',
       'Por eso llevan ese tanque con nitrógeno y aletas para enfriarlo.',
       'Mándaselo a tu compa que va a ver la Baja 1000,',
       'porque su camioneta no aguantaría… este brinco.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-13_baja1000_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_baja1000.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-13_baja1000_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
VERDE = (120, 240, 160)
ARENA = (214, 190, 150)
BLANCO_T = (232, 234, 238)
AZUL_T = (40, 92, 200)
NARANJA_T = (255, 120, 30)
NEGRO = (22, 22, 26)
GRIS_P = (120, 124, 132)
CROMO = (210, 212, 218)
ROJO_A = (220, 40, 40)
ORO = (214, 170, 70)


# ------------------------------------------------------------------ tiempos por palabra (u de la palabra k de la frase i)
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


def Wu(i, k):
    L = _wt()[i]
    return L[min(k, len(L) - 1)]


def Wp(i, palabra):
    """u de la primera palabra de la frase i que empieza con `palabra` (sin acentos)."""
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    for k, w in enumerate(ws):
        if w.startswith(p):
            return Wu(i, k)
    return 0.0


# ------------------------------------------------------------------ utilidades
def K(u, dist, yaw, pitch, tx=0.0, ty=0.8, tz=0.0, roll=0.0):
    return (u, dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll))


def camara(u, claves, cy=0.56, off=(0.0, 0.0, 0.0)):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'] + off[0], p['ty'] + off[1], p['tz'] + off[2]), dist=p['dist'], yaw=p['yaw'],
               pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def golpe_k(u, u0, dur=0.32):
    return (1 - seg(u, u0, u0 + dur)) ** 2 if u >= u0 else 0.0


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    return P.mover_img(img, amp * k * math.sin(t * 91.0) * math.cos(t * 37.0), amp * k * math.sin(t * 73.0 + 1.3))


def texto(img, fx, x, y, txt, size, col=WHITE, k=1.0, f='sansx', glow=0.35, anchor='mm'):
    if k <= 0.01:
        return
    lay = Image.new('L', img.size, 0)
    ImageDraw.Draw(lay).text((x, y), txt, font=M.font(f, size), fill=int(255 * clamp(k)), anchor=anchor)
    img.paste(Image.new('RGB', img.size, col), (0, 0), lay)
    if glow:
        fx.paste(Image.new('RGB', img.size, M.scale_c(col, glow)), (0, 0), lay.filter(ImageFilter.GaussianBlur(8)))


def recreacion(img, fx, k=1.0, y=1440, txt='RECREACIÓN'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


def tubo(p0, p1, r=0.035, col=CROMO, n=7, name='in', glow=None):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = M.norm(p1 - p0)
    a = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    e1 = M.norm(np.cross(d, a))
    e2 = np.cross(d, e1)
    V, F = [], []
    for p in (p0, p1):
        for j in range(n):
            q = 2 * math.pi * j / n
            V.append(p + r * (math.cos(q) * e1 + math.sin(q) * e2))
    for j in range(n):
        F.append((j, (j + 1) % n, n + (j + 1) % n, n + j))
    m = named(M3.Mesh(V, F, col, shadow=0, gloss=0.8, double=True), name, rim=0.8, gloss=0.8)
    if glow is not None:
        m.glow = glow
    return m


def _B(ms, sx, sy, sz, col, x, y, z, name='cuerpo', gloss=0.45, rim=0.6, glow=None, base=True):
    m = named(M3.box(sx, sy, sz, col, shadow=0, gloss=gloss, base=base).tf(t=(x, y, z)), name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    ms.append(m)
    return m


def _rueda(ms, x, y, z, r=0.46, ancho=0.34, giro=0.0, rin=(70, 72, 78)):
    ms.append(named(M3.cyl(r, ancho, NEGRO, n=20, shadow=0, gloss=0.12).tf(rx=90, t=(x, y, z - ancho / 2)), 'llanta', rim=0.35))
    ms.append(named(M3.cyl(r * 0.55, ancho + 0.012, rin, n=12, shadow=0, gloss=0.85).tf(rx=90, t=(x, y, z - ancho / 2 - 0.006)),
                    'rin', rim=0.7, gloss=0.85))
    for j in range(3):                                   # tacos que giran (se nota la rueda)
        a = giro + j * 2.1
        bx, by = x + r * 0.78 * math.cos(a), y + r * 0.78 * math.sin(a)
        _B(ms, 0.1, 0.1, ancho + 0.03, (40, 40, 44), bx, by, z, name='taco', base=False, gloss=0.1)


# ------------------------------------------------------------------ el Trophy Truck (frente hacia +x)
def troca(comp=0.0, giro=0.0, luces=0.6, calor=0.0):
    """Trophy Truck semirrealista sin logos. comp: 1 = suspensión comprimida (golpe), 0 = normal, −1 = colgando
    (en el aire: las llantas bajan casi un metro). Las piezas de la suspensión se llaman 'in' (rayos X)."""
    ms = []
    yc = 0.63 - 0.3 * max(comp, 0.0)                      # alto del chasis sobre el piso
    dr = 0.62 * max(-comp, 0.0)                           # cuánto cuelga la llanta trasera
    df = 0.48 * max(-comp, 0.0)
    yr, yf = 0.46 - dr, 0.46 - df
    # carrocería de fibra (blanca con franjas azul y naranja, sin logos)
    _B(ms, 1.25, 0.62, 1.62, BLANCO_T, 0.05, yc + 0.42, 0, gloss=0.55)                         # cabina
    _B(ms, 1.15, 0.05, 1.5, (24, 30, 40), 0.1, yc + 1.04, 0, gloss=0.9, rim=0.9)               # techo oscuro
    _B(ms, 0.05, 0.36, 1.44, (26, 34, 46), 0.69, yc + 0.66, 0, gloss=0.95, rim=0.9)            # parabrisas
    _B(ms, 1.45, 0.42, 1.78, BLANCO_T, 1.32, yc + 0.32, 0, gloss=0.55)                         # cofre
    _B(ms, 0.08, 0.3, 1.5, (34, 34, 38), 2.06, yc + 0.34, 0, gloss=0.3)                        # parrilla
    _B(ms, 1.7, 0.42, 1.82, BLANCO_T, -1.42, yc + 0.32, 0, gloss=0.5)                          # caja
    for s in (-1, 1):
        _B(ms, 4.5, 0.09, 0.02, AZUL_T, -0.05, yc + 0.36, s * 0.92, gloss=0.6, rim=0.5)       # franja azul
        _B(ms, 4.5, 0.05, 0.02, NARANJA_T, -0.05, yc + 0.48, s * 0.92, gloss=0.6, rim=0.5)    # franja naranja
        _B(ms, 0.9, 0.1, 0.24, (30, 30, 34), 1.45, yc + 0.18, s * 0.99, gloss=0.2)            # salpicaderas anchas
        _B(ms, 1.0, 0.1, 0.24, (30, 30, 34), -1.45, yc + 0.18, s * 0.99, gloss=0.2)
    _B(ms, 0.2, 0.09, 1.3, (60, 60, 66), 0.5, yc + 1.09, 0, gloss=0.6,                         # barra de luces
       glow=M.scale_c((255, 246, 220), luces))
    for z in (-0.5, 0.5):
        _B(ms, 0.05, 0.1, 0.24, (255, 248, 230), 2.11, yc + 0.42, z, glow=M.scale_c((255, 236, 190), luces))
    # jaula y llantas de refacción en la caja
    for s in (-1, 1):
        ms.append(tubo((-0.55, yc + 1.05, s * 0.62), (-1.9, yc + 0.72, s * 0.6), r=0.04, col=(200, 60, 40), name='jaula'))
    ms.append(named(M3.cyl(0.4, 0.3, NEGRO, n=18, shadow=0, gloss=0.1).tf(t=(-1.55, yc + 0.72, 0.0)), 'refa', rim=0.3))
    # suspensión (rayos X)
    for s in (-1, 1):
        z = s * 0.98
        zi = s * 0.55
        # adelante: brazos A y coilover inclinado
        ms.append(tubo((1.45, yf, z * 0.86), (1.2, yc + 0.08, zi), r=0.04, col=CROMO))
        ms.append(tubo((1.45, yf, z * 0.86), (1.75, yc + 0.08, zi), r=0.04, col=CROMO))
        ms.append(tubo((1.45, yf + 0.12, z * 0.82), (1.45, yc + 0.72, zi + s * 0.12), r=0.075, col=(200, 40, 30),
                       glow=M.scale_c((255, 90, 40), calor)))
        # atrás: brazo largo (trailing arm), eje y dos amortiguadores por lado (coilover + bypass)
        ms.append(tubo((-1.45, yr, z * 0.86), (0.2, yc + 0.05, zi), r=0.055, col=CROMO))
        for dx, col in ((-0.18, (200, 40, 30)), (0.12, (60, 120, 220))):
            ms.append(tubo((-1.45 + dx, yr + 0.1, z * 0.82), (-1.3 + dx, yc + 0.85, zi + s * 0.1), r=0.07, col=col,
                           glow=M.scale_c((255, 90, 40), calor)))
        ms.append(tubo((-1.3 + 0.32, yr + 0.35, z * 0.78), (-1.15 + 0.32, yc + 0.7, zi), r=0.05, col=ORO))  # depósito
    _B(ms, 0.16, 0.16, 1.8, (90, 92, 100), -1.45, yr - 0.08, 0, name='in', gloss=0.7)          # eje trasero
    for x, y in ((1.45, yf), (-1.45, yr)):
        for s in (-1, 1):
            _rueda(ms, x, y, s * 1.0, giro=giro)
    return ms


def pickup(comp=0.0, giro=0.0, color=(132, 136, 146)):
    """Pickup de fábrica (genérica, sin marca). Su llanta trasera solo puede bajar/subir unos 38 cm."""
    ms = []
    yc = 0.62 - 0.1 * max(comp, 0)
    dr = 0.22 * max(-comp, 0)
    yr = 0.38 - dr
    _B(ms, 1.3, 0.85, 1.6, color, 0.1, yc + 0.3, 0, gloss=0.6)
    _B(ms, 0.05, 0.36, 1.4, (26, 34, 46), 0.76, yc + 0.72, 0, gloss=0.95, rim=0.9)
    _B(ms, 1.15, 0.55, 1.65, color, 1.3, yc + 0.3, 0, gloss=0.6)
    _B(ms, 0.06, 0.3, 1.2, CROMO, 1.9, yc + 0.42, 0, gloss=0.95)
    _B(ms, 1.8, 0.55, 1.66, color, -1.45, yc + 0.3, 0, gloss=0.55)
    for s in (-1, 1):
        z = s * 0.82
        ms.append(tubo((-1.45, yr, z * 0.9), (-1.45, yc + 0.32, z * 0.75), r=0.06, col=(70, 140, 230)))   # amortiguador
        ms.append(tubo((1.4, 0.38, z * 0.9), (1.4, yc + 0.32, z * 0.75), r=0.06, col=(70, 140, 230)))
        ms.append(tubo((-1.45, yr + 0.1, z * 0.8), (-0.3, yc + 0.1, z * 0.6), r=0.03, col=CROMO))       # muelle
    _B(ms, 0.12, 0.12, 1.6, (90, 92, 100), -1.45, yr - 0.06, 0, name='in', gloss=0.7)
    for x, y in ((1.4, 0.38), (-1.45, yr)):
        for s in (-1, 1):
            _rueda(ms, x, y, s * 0.86, r=0.38, ancho=0.26, giro=giro, rin=(190, 192, 198))
    return ms


def cota_v(fr, x, y0, y1, z, k, col=AMARILLO):
    """Cota vertical (3D) con topes; devuelve la posición en pantalla de su centro."""
    if k <= 0.01:
        return None
    y1k = lerp(y0, y1, k)
    line3(fr, [(x, y0, z), (x, y1k, z)], col=col, w=3.2, a=0.95, glow=1.0)
    for y in (y0, y1k):
        line3(fr, [(x - 0.12, y, z), (x + 0.12, y, z)], col=col, w=3.2, a=0.95, glow=1.0)
    return fr.cam.p1((x, (y0 + y1k) / 2, z))


def desierto(fr, t, a=0.7, seed=5, z=-9.0, cardones=True):
    """Dunas de línea al fondo y cardones (el cactus de Baja California Sur)."""
    rng = np.random.RandomState(seed)
    xs = np.linspace(-22, 22, 50)
    ys = 0.9 + 1.1 * np.abs(np.sin(xs * 0.19 + 0.6)) + 0.6 * np.abs(np.sin(xs * 0.47)) + rng.uniform(0, 0.2, len(xs))
    line3(fr, [(x, y, z) for x, y in zip(xs, ys)], col=ARENA, w=2.0, a=a, glow=0.5)
    if cardones:
        for cx_, cz_, h in ((-6.5, -5.0, 2.6), (7.0, -6.0, 3.0), (-11.0, -7.5, 3.4), (12.0, -4.5, 2.2)):
            line3(fr, [(cx_, 0, cz_), (cx_, h, cz_)], col=(150, 200, 160), w=3.0, a=a * 0.8, glow=0.4)
            for sgn, yb in ((-1, h * 0.45), (1, h * 0.6)):
                line3(fr, [(cx_, yb, cz_), (cx_ + sgn * 0.45, yb, cz_), (cx_ + sgn * 0.45, yb + h * 0.3, cz_)],
                      col=(150, 200, 160), w=3.0, a=a * 0.8, glow=0.4)


def polvo(img, fx, x, y, t, k=1.0, escala=1.0, seed=0):
    """Nube de polvo (2D) que sale de las llantas al caer o arrancar."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    rng = np.random.RandomState(seed)
    for j in range(14):
        ph = (t * 0.9 + rng.rand()) % 1.0
        r = (20 + 60 * ph) * escala * (0.6 + rng.rand())
        xx = x + (rng.rand() - 0.5) * 260 * escala + (rng.rand() - 0.5) * 120 * ph
        yy = y - 30 * ph * escala - rng.rand() * 30
        d.ellipse((xx - r, yy - r * 0.6, xx + r, yy + r * 0.6), fill=M.scale_c(ARENA, 0.28 * k * (1 - ph)))


# ------------------------------------------------------------------ mapa de Baja California Sur (línea que brilla)
BCS = [(-114.15, 28.0), (-114.3, 27.85), (-115.05, 27.84), (-114.85, 27.5), (-114.3, 27.15), (-113.65, 26.7),
       (-113.1, 26.45), (-112.5, 26.2), (-112.2, 25.75), (-112.1, 25.2), (-112.2, 24.75), (-111.75, 24.35),
       (-111.1, 24.05), (-110.55, 23.7), (-110.2, 23.42), (-109.95, 22.9), (-109.7, 23.03), (-109.45, 23.2),
       (-109.42, 23.55), (-109.7, 23.75), (-110.0, 24.1), (-110.3, 24.18), (-110.65, 24.35), (-110.7, 24.85),
       (-111.0, 25.45), (-111.35, 26.0), (-111.6, 26.6), (-112.0, 26.9), (-112.3, 27.35), (-112.75, 27.85), (-112.85, 28.0)]
RUTA = [(-109.7, 23.06), (-109.59, 23.6), (-109.72, 23.7), (-110.1, 24.0), (-110.6, 24.45), (-110.9, 25.3),
        (-111.35, 26.0), (-111.85, 26.08), (-112.0, 25.3), (-111.85, 24.42), (-111.0, 24.0), (-110.2, 23.45),
        (-109.95, 23.15), (-109.7, 23.06)]
MAPA_S = 1.25


def geo(lon, lat, y=0.0):
    return np.array([(lon + 111.2) * MAPA_S, y, -(lat - 25.4) * MAPA_S])


def mapa(fr, t, k=1.0, ruta=0.0, relleno=0.0):
    if k <= 0.01:
        return None
    pts = [geo(lo, la) for lo, la in BCS]
    line3(fr, pts, col=WHITE, w=2.6, a=0.9 * k, glow=0.8, frac=min(1, k * 1.05))
    # línea de la costa del continente (para dar contexto)
    line3(fr, [geo(-112.6, 29.2), geo(-111.0, 27.6), geo(-109.4, 26.0), geo(-108.0, 24.6)], col=(120, 120, 130),
          w=2.0, a=0.5 * k, glow=0.3)
    if relleno > 0.01:
        s, z = fr.cam.proj(np.array(pts))
        if (z > 0.2).all():
            fr.df.polygon([tuple(p) for p in s], fill=M.scale_c(CYAN, 0.22 * relleno))
    if ruta > 0.01:
        R = []
        for (a, b) in zip(RUTA[:-1], RUTA[1:]):
            for q in np.linspace(0, 1, 8, endpoint=False):
                R.append(geo(lerp(a[0], b[0], q), lerp(a[1], b[1], q), 0.02))
        R.append(geo(*RUTA[-1], 0.02))
        n = max(2, int(len(R) * clamp(ruta)))
        line3(fr, R[:n], col=NARANJA, w=4.0, a=1.0, glow=1.2)
        return R[n - 1]
    return None


# ================================================================== escenas
# 0. gancho (inicio 12: cuenta regresiva) → 3-2-1 en la salida de San José del Cabo, arranca, vuela y aterriza
U_YA, U_SALTO, U_CAE = 0.36, 0.95, 2.45
X_RAMPA = 1.6


def _vuelo(u):
    """Posición (x, y), inclinación y compresión del Trophy Truck en el gancho."""
    if u < U_YA:
        return 0.0, 0.0, 0.0, 0.08 * math.sin(u * 40) * 0.3
    if u < U_SALTO:
        s = (u - U_YA) / (U_SALTO - U_YA)
        return X_RAMPA * s * s, 0.35 * s * s, 9.0 * s * s, 0.0
    if u < U_CAE:
        s = (u - U_SALTO) / (U_CAE - U_SALTO)
        return X_RAMPA + 7.2 * s, 0.35 + 2.4 * 4 * s * (1 - s) - 0.35 * s, 9.0 - 17.0 * s, -min(1.0, s * 4)
    v = u - U_CAE
    x = X_RAMPA + 7.2 + 3.0 * (1 - math.exp(-v * 2.2))
    comp = math.exp(-5.0 * v) * math.cos(9.0 * v)
    return x, 0.0, -2.0 * math.exp(-6 * v), comp


def s_gancho(t, fi, u, d):
    x, y, inc, comp = _vuelo(u)
    p = P.cam_rapida(u, [K(-3.8, 9.5, 48, 7), K(-0.4, 8.4, 34, 4), K(U_SALTO, 12.5, 22, -1), K(U_CAE - 0.1, 12.0, 26, 2), K(U_CAE + 0.05, 7.4, 30, 7),
                          K(U_CAE + 0.4, 8.0, 36, 8), K(5, 7.8, 40, 8)])
    fr = Frame(Cam(target=(x + 0.6, 0.8 + 0.4 * y, 0.0), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.35)
    M.cristal(fr.base, fr.fx, 'BRINCO', u, t0=-2.3, cy=0.36, entrada='golpe')
    desierto(fr, t)
    # arco de salida y rampa (línea)
    for z in (-2.1, 2.1):
        line3(fr, [(0.6, 0, z), (0.6, 3.0, z)], col=WHITE, w=3, a=0.8, glow=0.6)
    line3(fr, [(0.6, 3.0, -2.1), (0.6, 3.0, 2.1)], col=AMARILLO, w=5, a=0.9, glow=1.0)
    line3(fr, [(X_RAMPA - 1.4, 0.01, -1.5), (X_RAMPA, 0.4, -1.5), (X_RAMPA, 0.01, -1.5)], col=ARENA, w=3, a=0.8)
    line3(fr, [(X_RAMPA - 1.4, 0.01, 1.5), (X_RAMPA, 0.4, 1.5), (X_RAMPA, 0.01, 1.5)], col=ARENA, w=3, a=0.8)
    sx, sy = fr.cam.proj([(x, 0.02, 0.0)])[0][0]
    aire = clamp(y / 2.0)
    D.shadow_blob(fr, sx, sy, 520 * (1 - 0.4 * aire), 70 * (1 - 0.4 * aire), 0.8 * (1 - 0.5 * aire))
    ms = troca(comp=comp, giro=-x / 0.46, luces=1.0)
    ms = P.tfk(ms, rz=inc, t=(x, y, 0.0))
    draw_objects(fr, ms)
    arco = fr.cam.p1((0.6, 3.25, 0.0))
    rueda = fr.cam.p1((x - 1.45, 0.05, 1.0))

    def ui(img, fx):
        pill(img, fx, 540, 1330, 'SALIDA · SAN JOSÉ DEL CABO', 1.0 if u < 0.5 else 1 - seg(u, 0.5, 0.7), size=24,
             border=AMARILLO)
        for j, n in enumerate(('3', '2', '1')):
            a0 = -0.3 + 0.22 * j
            if a0 <= u < a0 + 0.22 or (j == 0 and u < a0):
                kk = seg(u, a0, a0 + 0.12) if u >= a0 else 0.0
                P.numero_golpe(img, fx, n, 360, kk, size=300, col=(255, 90, 60) if n != '1' else AMARILLO)
        if U_YA <= u < U_YA + 0.25:
            P.numero_golpe(img, fx, '¡YA!', 360, seg(u, U_YA, U_YA + 0.1), size=220, col=VERDE)
        polvo(img, fx, rueda[0], rueda[1], t, k=seg(u, U_YA, U_YA + 0.1) * (1 - seg(u, U_SALTO, U_SALTO + 0.4)), seed=1)
        if u > U_CAE:
            polvo(img, fx, rueda[0] + 120, rueda[1], t, k=1 - seg(u, U_CAE + 0.6, U_CAE + 1.6), escala=1.6, seed=2)
        kicker(img, '59.ª SCORE BAJA 1000 · TROPHY TRUCK', 150, seg(u, 0.55, 0.85), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu camioneta no aguantaría…', 'sans'), ('este brinco.', 'serif')], 205,
                       seg(u, 0.6, 0.75), size=70)
        recreacion(img, fx, seg(u, 0.9, 1.2))
    fr.ui.append(ui)
    k = max(golpe_k(u, U_CAE, 0.45), golpe_k(u, 0.6 + 0.15, 0.25) * 0.6)
    return sacudir(finish(fr, fi), t, k, amp=30)


# 1. hoy arranca y por primera vez es toda en BCS (el polvo se abre en el mapa de la península)
def s_hoy(t, fi, u, d):
    up = Wp(1, 'primera') - 0.1
    sj = geo(-109.7, 23.06)
    p = P.cam_rapida(u, [K(-0.3, 7.0, 40, 70, tx=float(sj[0]) - 0.8, tz=float(sj[2]) - 0.8), K(0.5, 13.5, 40, 64, tx=-1.2, tz=0.2),
                          K(up, 12.0, 32, 56, tx=-1.3, tz=0.0), K(d, 11.6, 30, 55, tx=-1.3, tz=0.0)])
    fr = Frame(Cam(target=(p['tx'], 0.0, p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=0.46))
    space(fr, t, floor=None, bokeh=0.9)
    km = mapa(fr, t, k=eout(seg(u, -0.45, 0.2)), relleno=eout(seg(u, up, up + 0.5)))
    cab = geo(-109.7, 23.06)
    dot3(fr, cab, r=10, col=NARANJA, a=0.7 + 0.3 * math.sin(t * 9), glow=1.6)
    for j in range(3):
        ph = (t * 1.4 + j / 3) % 1.0
        q = np.linspace(0, 2 * math.pi, 36)
        line3(fr, [cab + np.array([0.6 * ph * math.cos(a), 0.0, 0.6 * ph * math.sin(a)]) for a in q],
              col=NARANJA, w=2.2, a=(1 - ph) * 0.8, glow=1.0)
    pc = fr.cam.p1(tuple(cab))
    pl = fr.cam.p1(tuple(geo(-111.6, 25.8)))

    def ui(img, fx):
        kicker(img, '59.ª SCORE BAJA 1000 · 9 AL 15 DE NOVIEMBRE', 150, seg(u, 0.0, 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Hoy arranca', 'sans'), ('la Baja 1000.', 'serif')], 210, seg(u, 0.05, 0.2), size=82)
        pill(img, fx, pc[0] - 60, pc[1] - 80, 'SAN JOSÉ DEL CABO · SALIDA Y META', eout(seg(u, 0.4, 0.7)), size=24,
             border=NARANJA)
        texto(img, fx, pl[0], pl[1], 'BAJA CALIFORNIA SUR', 40, CYAN, eout(seg(u, up + 0.2, up + 0.5)), f='mono', glow=0.6)
        pill(img, fx, 540, 1390, 'POR PRIMERA VEZ EN SU HISTORIA · 100 % EN BCS', eout(seg(u, up, up + 0.3)), size=26,
             border=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


# 2. de Cabo a Cabo: la ruta se dibuja y el contador llega a 1 500 km (entra atravesando «1 500 KM» de cristal)
def s_cabo(t, fi, u, d):
    kr = ease(seg(u, 0.1, d - 0.5))
    p = P.cam_rapida(u, [K(-0.3, 7.5, 10, 46, tx=0.6, tz=1.6), K(1.4, 10.0, 30, 54, tx=-0.6, tz=0.6),
                          K(2.8, 11.5, 42, 60, tx=-1.0, tz=0.4), K(d, 11.5, 44, 62, tx=-1.0, tz=0.4)])
    fr = Frame(Cam(target=(p['tx'], 0.0, p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=0.55))
    space(fr, t, floor=None, bokeh=0.9)
    pt = mapa(fr, t, k=1.0, ruta=max(0.02, kr), relleno=0.4)
    if pt is not None:
        dot3(fr, pt + np.array([0, 0.05, 0]), r=12, col=WHITE, glow=2.0)
    for lo, la, nom in ((-111.35, 26.0, 'LORETO'), (-110.2, 23.45, 'TODOS SANTOS'), (-111.85, 24.42, 'PUERTO CHALE')):
        dot3(fr, geo(lo, la, 0.03), r=6, col=AMARILLO, a=0.9, glow=1.0)
    etis = [(fr.cam.p1(tuple(geo(lo, la))), nom, ka) for lo, la, nom, ka in
            ((-111.35, 26.0, 'LORETO', 0.45), (-111.85, 24.42, 'PUERTO CHALE', 0.7), (-110.2, 23.45, 'TODOS SANTOS', 0.88))]

    def ui(img, fx):
        kicker(img, 'DE CABO A CABO · RECORRIDO', 150, seg(u, 0.0, 0.3), col=AZULC)
        km_ = int(1500 * eout(seg(u, 0.1, d - 0.4), 2))
        texto(img, fx, 540, 290, f'{km_:,}'.replace(',', ' ') + ' km', 120, WHITE, 1.0, f='mono', glow=0.5)
        pill(img, fx, 540, 400, 'CASI MIL MILLAS · LÍMITE: 40 HORAS', eout(seg(u, d - 0.9, d - 0.6)), size=24,
             border=AMARILLO, dot=False)
        for (x, y, _), nom, ka in etis:
            if kr > ka:
                pill(img, fx, x + 10, y - 50, nom, eout(seg(kr, ka, ka + 0.06)), size=20, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. por dentro: la pickup de fábrica en rayos X; su llanta sube y baja cuando mucho 38 cm
def s_pickup(t, fi, u, d):
    ux = Wp(3, 'dentro') - 0.1
    ul = Wp(3, 'sube') - 0.1
    u38 = Wp(3, 'treinta') - 0.1
    e = P.entrada(u, -0.2, 0.3, 'cae')
    osc = math.sin((u - ul) * 5.0) if u > ul else 0.0
    comp = 0.85 * osc if osc > 0 else 0.95 * osc
    claves = [K(-0.3, 7.6, 38, 10, tx=0.0, ty=0.9), K(ux + 0.4, 7.0, 30, 8, tx=-0.2, ty=0.9),
              K(ul, 5.4, 8, 4, tx=-1.3, ty=0.55, tz=0.8), K(u38, 4.8, 4, 3, tx=-1.45, ty=0.5, tz=0.9),
              K(d, 4.7, 2, 3, tx=-1.45, ty=0.5, tz=0.9)]
    fr = Frame(camara(u, claves, cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.3)
    desierto(fr, t, a=0.5, cardones=False)
    ms = P.tfk(pickup(comp=comp, giro=0.0), t=(0, -e['dy'] * 0.5, 0))
    draw_objects(fr, ms, xray=clamp(seg(u, ux, ux + 0.4)), keep=('in', 'llanta', 'rin', 'taco'))
    yr = 0.38 - 0.22 * max(-comp, 0) - 0.0
    c = None
    if u > u38 - 0.4:
        c = cota_v(fr, -1.45, 0.38 - 0.22, 0.38 + 0.16, 1.05, eout(seg(u, u38 - 0.4, u38)))

    def ui(img, fx):
        kicker(img, 'CASO 1 · PICKUP DE FÁBRICA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 250, 'RAYOS X', eout(seg(u, ux, ux + 0.3)), size=24, border=CYAN)
        if c is not None:
            texto(img, fx, c[0] + 170, c[1], '38 cm', 92, AMARILLO, eout(seg(u, u38, u38 + 0.2)), f='sansx', glow=0.5)
            pill(img, fx, 540, 1380, 'LA MÁS PREPARADA DE FÁBRICA · ATRÁS', eout(seg(u, u38 + 0.3, u38 + 0.6)), size=22,
                 border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.05, 0.3), amp=12)


# 4. el Trophy Truck: casi un metro (cubo desde la pickup; «90 CM» de cristal detrás)
def s_trophy(t, fi, u, d):
    osc = math.sin(u * 4.6 + 0.4)
    comp = 0.9 * osc if osc > 0 else 1.0 * osc
    fr = Frame(camara(u, [K(-0.3, 7.0, -22, 6, tx=-1.2, ty=0.6, tz=0.8), K(0.5, 6.0, -6, 3, tx=-1.45, ty=0.5, tz=1.0),
                          K(d, 5.8, -2, 3, tx=-1.45, ty=0.5, tz=1.0)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, '90 CM', u, t0=0.05, cy=0.33, entrada='zoom')
    draw_objects(fr, troca(comp=comp, giro=0.0, luces=0.5), xray=1.0, keep=('in', 'llanta', 'rin', 'taco'))
    c = cota_v(fr, -1.45, 0.46 - 0.62, 0.46 + 0.28, 1.25, eout(seg(u, 0.1, 0.5)))

    def ui(img, fx):
        kicker(img, 'CASO 2 · TROPHY TRUCK', 150, seg(u, -0.1, 0.2), col=AZULC)
        if c is not None:
            texto(img, fx, c[0] + 200, c[1], '≈ 90 cm', 84, AMARILLO, eout(seg(u, 0.3, 0.5)), glow=0.5)
        pill(img, fx, 540, 1380, 'ATRÁS · MÁS DEL DOBLE', eout(seg(u, 0.8, 1.1)), size=24, border=AMARILLO, dot=False)
        recreacion(img, fx, 1.0, y=1450)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. cae del brinco y la suspensión se traga el golpe (zoom digital al amortiguador)
def s_cae(t, fi, u, d):
    ug = Wp(5, 'suspension') - 0.15
    land = 0.35
    if u < land:
        s = clamp((u + 0.25) / (land + 0.25))
        y, comp = 2.8 * (1 - s * s), -1.0
    else:
        v = u - land
        y, comp = 0.0, math.exp(-4.0 * v) * math.cos(7.0 * v)
    fr = Frame(camara(u, [K(-0.3, 14.0, 62, 2, tx=-0.4, ty=1.6), K(land, 12.0, 58, 6, tx=-0.4, ty=0.9),
                          K(ug - 0.35, 12.0, 56, 6, tx=-0.4, ty=0.9), K(ug, 8.5, 30, 5, tx=-0.9, ty=0.7, tz=0.5),
                          K(d, 7.4, 22, 5, tx=-0.6, ty=0.8, tz=0.4)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.65, bokeh=0.8, beam=0.4)
    desierto(fr, t, seed=9)
    sx, sy = fr.cam.proj([(0.0, 0.02, 0.0)])[0][0]
    D.shadow_blob(fr, sx, sy, 520, 70, 0.8)
    draw_objects(fr, P.tfk(troca(comp=comp, giro=0.0, luces=0.8, calor=0.3 * max(comp, 0)), t=(0, y, 0)),
                 xray=clamp(seg(u, ug, ug + 0.3)) * 0.85, keep=('in', 'llanta', 'rin', 'taco', 'jaula'))
    rr = fr.cam.p1((-1.45, 0.4, 1.0))
    sh = fr.cam.p1((-1.35, 1.05, 0.9))

    def ui(img, fx):
        if u > land:
            polvo(img, fx, rr[0] + 150, rr[1], t, k=1 - seg(u, land + 0.8, land + 1.8), escala=1.7, seed=4)
        kicker(img, 'EL GOLPE AL CAER', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, sh[0], sh[1] - 90, 'SE COMPRIME · SE TRAGA EL GOLPE', eout(seg(u, ug + 0.2, ug + 0.5)), size=24,
             border=CYAN)
        rec_frame(img, t, seg(u, ug + 0.6, ug + 0.7), zoom_label='x1.6' if u > ug + 1.0 else 'x1.3')
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u > ug + 0.6:                                             # zoom digital por saltos al amortiguador
        z = 1.3 if u < ug + 1.0 else 1.6
        out = M.scale_about(out, z, sh[0] / 1080, sh[1] / 1920)
    return sacudir(out, t, golpe_k(u, land, 0.45), amp=28)


# 6. segundo gancho: el error más peligroso lo comete el público (curva de noche llena de lucecitas)
def _curva(n=60, R=3.4, a0=-0.2, a1=2.2):
    q = np.linspace(a0, a1, n)
    return q, R


def curva_3d(fr, t, k=1.0, zona=0.0, R=3.4, ancho=0.9, public=1.0):
    q = np.linspace(-0.6, 2.3, 70)
    for r in (R - ancho, R + ancho):
        line3(fr, [(r * math.cos(a) - 1.0, 0.01, r * math.sin(a) - 1.0) for a in q], col=WHITE, w=2.6, a=0.8 * k, glow=0.6)
    if zona > 0.01:                                              # zona roja: afuera de la curva
        pts = [(R + ancho + 0.2) * np.array([math.cos(a), 0, math.sin(a)]) + np.array([-1.0, 0.01, -1.0]) for a in q[20:52]]
        pts += [(R + ancho + 2.6) * np.array([math.cos(a), 0, math.sin(a)]) + np.array([-1.0, 0.01, -1.0]) for a in q[20:52][::-1]]
        s, z = fr.cam.proj(np.array(pts))
        if (z > 0.2).all():
            fr.df.polygon([tuple(p) for p in s], fill=M.scale_c(RED, 0.35 * zona))
    rng = np.random.RandomState(3)
    for j in range(70 if public > 0 else 0):                    # el público: lucecitas de celulares y lámparas
        a = lerp(0.3, 1.6, rng.rand())
        r = R + ancho + 0.4 + rng.rand() * 1.8
        p = np.array([r * math.cos(a) - 1.0, 0.25 + rng.rand() * 0.25, r * math.sin(a) - 1.0])
        dot3(fr, p, r=5 + 4 * rng.rand(), col=(255, 230, 170), a=public * (0.6 + 0.4 * math.sin(t * 5 + j)), glow=1.6)


def s_error(t, fi, u, d):
    upub = Wp(6, 'publico') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.5, 50, 16, tx=-1.0, ty=0.4, tz=-1.0), K(0.5, 6.0, 72, 12, tx=0.6, ty=0.4, tz=1.0),
                          K(upub, 4.8, 96, 8, tx=1.6, ty=0.4, tz=1.4), K(d, 4.6, 100, 8, tx=1.6, ty=0.4, tz=1.4)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.45, bokeh=0.7, beam=0.0)
    M.cristal(fr.base, fr.fx, 'PÚBLICO', u, t0=upub, cy=0.36, entrada='golpe')
    desierto(fr, t, a=0.4, seed=11)
    curva_3d(fr, t, k=1.0, zona=0.0, public=1.0)

    def ui(img, fx):
        texto(img, fx, 540, 230, 'EL ERROR', 96, RED, eout(seg(u, 0.0, 0.15)), f='sansx', glow=0.7)
        kicker(img, 'MÁS PELIGROSO DE LA CARRERA', 320, seg(u, 0.2, 0.5), col=(255, 160, 150))
        pill(img, fx, 540, 1380, 'NO ES DE LOS PILOTOS', eout(seg(u, upub - 0.6, upub - 0.3)), size=26, border=RED, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.0, 0.3), golpe_k(u, upub + 0.1, 0.3)), amp=18)


# 7. pararse afuera de la curva: el camión sigue derecho (inercia) y cae en la zona roja; 800+ HP
def s_curva(t, fi, u, d):
    ua = Wp(7, 'justo') - 0.1
    u8 = Wp(7, 'ochocientos') - 0.1
    R = 3.4
    # trayectoria: entra por la curva y en ua sigue derecho por la tangente
    a_t = lerp(-0.4, 0.75, clamp((u + 0.3) / (ua + 0.3)))
    if u <= ua:
        pos = np.array([R * math.cos(a_t) - 1.0, 0.0, R * math.sin(a_t) - 1.0])
        yaw_t = -math.degrees(a_t) - 90
    else:
        a0 = 0.75
        p0 = np.array([R * math.cos(a0) - 1.0, 0.0, R * math.sin(a0) - 1.0])
        tg = np.array([-math.sin(a0), 0, math.cos(a0)])
        pos = p0 + tg * 3.2 * (1 - math.exp(-(u - ua) * 1.6))
        yaw_t = -math.degrees(a0) - 90
    top = u < u8 - 0.15
    claves = [K(-0.3, 11.0, 0, 82, tx=0.2, ty=0.0, tz=0.2), K(ua, 10.0, 0, 80, tx=0.6, ty=0.0, tz=0.8),
              K(u8 - 0.15, 6.0, 140, 10, tx=float(pos[0]), ty=0.6, tz=float(pos[2])),
              K(d, 6.4, 150, 10, tx=float(pos[0]), ty=0.6, tz=float(pos[2]))]
    fr = Frame(camara(u, claves, cy=0.55))
    space(fr, t, floor='lines' if not top else None, floor_a=0.5, bokeh=0.7)
    curva_3d(fr, t, zona=eout(seg(u, -0.1, 0.3)), public=0.8)
    if u <= ua + 0.05:
        pass
    a0 = 0.75
    p0 = np.array([R * math.cos(a0) - 1.0, 0.02, R * math.sin(a0) - 1.0])
    tg = np.array([-math.sin(a0), 0, math.cos(a0)])
    line3(fr, [p0, p0 + tg * 3.6], col=AMARILLO, w=3.5, a=0.95, glow=1.0, frac=eout(seg(u, ua - 0.2, ua + 0.3)))
    ms = P.tfk(troca(comp=0.0, giro=-u * 9, luces=1.0), s=0.55, ry=yaw_t, t=tuple(pos))
    draw_objects(fr, ms)
    pz = fr.cam.p1(tuple(p0 + tg * 2.6 + np.array([0.6, 0, 0.4])))
    pa = fr.cam.p1(tuple(p0 + tg * 3.6))

    def ui(img, fx):
        kicker(img, 'VISTA DESDE ARRIBA', 150, seg(u, -0.1, 0.2) * (1 if top else 0), col=AZULC)
        if top:
            pill(img, fx, pz[0], pz[1], 'AFUERA DE LA CURVA', eout(seg(u, 0.2, 0.5)), size=26, border=RED)
            if u > ua:
                pill(img, fx, pa[0], pa[1] - 60, 'SIGUE DERECHO', eout(seg(u, ua + 0.1, ua + 0.3)), size=24,
                     border=AMARILLO, dot=False)
        P.numero_golpe(img, fx, '800+ HP', 330, seg(u, u8, u8 + 0.15), size=170, col=WHITE)
        if u > u8:
            pill(img, fx, 540, 460, 'MÁS DE 800 CABALLOS · 2.5 TONELADAS', eout(seg(u, u8 + 0.3, u8 + 0.6)), size=22,
                 border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u8 + 0.15, 0.35), amp=22)


# 8. Baja 500 de 2016: la tarjeta del dato cae (muro de titulares) y el «3» en rojo
_TARJ = {}


def tarjeta_2016():
    if 'img' in _TARJ:
        return _TARJ['img']
    w, h = 820, 520
    im = Image.new('RGB', (w, h), (246, 245, 241))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 74), fill=(24, 24, 28))
    d.text((34, 37), 'DATO · BAJA 500 · ENSENADA · JUNIO 2016', font=M.font('mono', 26), fill=(255, 236, 160), anchor='lm')
    y = 120
    for ln in ('Un camión de carreras', 'se salió en una curva', 'y golpeó a 3 espectadores.'):
        d.text((34, y), ln, font=M.font('sansx', 56), fill=(20, 20, 24))
        y += 72
    d.text((34, h - 70), 'Fuente: RACER, 6-jun-2016', font=M.font('mono', 24), fill=(110, 110, 116))
    _TARJ['img'] = im
    return im


def s_2016(t, fi, u, d):
    u3 = Wp(8, 'tres') - 0.1
    fr = Frame(camara(u, [K(-0.3, 9.0, 20, 70, tx=-0.5, ty=0.0, tz=0.0), K(1.0, 8.0, -20, 62, tx=0.3, ty=0.0),
                          K(u3, 7.0, -40, 50, tx=0.6, ty=0.0), K(d, 6.8, -44, 48, tx=0.6, ty=0.0)], cy=0.62))
    space(fr, t, floor=None, bokeh=0.8)
    curva_3d(fr, t, k=0.6, zona=0.6, public=0.5)
    a0 = 0.75
    R = 3.4
    p0 = np.array([R * math.cos(a0) - 1.0, 0.02, R * math.sin(a0) - 1.0])
    tg = np.array([-math.sin(a0), 0, math.cos(a0)])
    line3(fr, [p0, p0 + tg * 3.6], col=RED, w=3.5, a=0.9, glow=1.0)

    def ui(img, fx):
        kicker(img, 'NO ES TEORÍA', 150, seg(u, -0.1, 0.2), col=(255, 160, 150))
        photo_card(img, fx, tarjeta_2016(), 540, 640, 800, t - u + 0.05, t, angle0=-8.0)
        P.numero_golpe(img, fx, '3', 1150, seg(u, u3, u3 + 0.15), size=300, col=RED)
        texto(img, fx, 540, 1330, 'ESPECTADORES', 44, (255, 160, 150), eout(seg(u, u3 + 0.15, u3 + 0.35)), f='mono')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.3, 0.3), golpe_k(u, u3 + 0.15, 0.3)), amp=18)


# 9. SCORE: verla a más de 30 m, y nada de brincos o zanjas (garabatos que tachan)
def s_30m(t, fi, u, d):
    ub = Wp(9, 'brincos') - 0.1
    uz = Wp(9, 'zanjas') - 0.1
    fr = Frame(camara(u, [K(-0.3, 10.5, -10, 70, tx=0.6, ty=0.0, tz=1.6), K(0.5, 9.5, -16, 64, tx=0.8, ty=0.0, tz=2.0),
                          K(ub - 0.9, 9.3, -18, 63, tx=0.8, ty=0.0, tz=2.0),
                          K(ub - 0.3, 7.0, 30, 34, tx=-2.4, ty=0.2, tz=0.0), K(d, 6.8, 34, 32, tx=-2.6, ty=0.2, tz=0.0)],
                     cy=0.6))
    space(fr, t, floor='lines', floor_a=0.45, bokeh=0.7)
    M.cristal(fr.base, fr.fx, '30 M', u, t0=-0.25, cy=0.34, entrada='sube')
    for z in (-0.8, 0.8):                                        # el camino
        line3(fr, [(-8, 0.01, z), (8, 0.01, z)], col=WHITE, w=2.6, a=0.8, glow=0.6)
    kz = eout(seg(u, 0.1, 0.6))
    line3(fr, [(1.5, 0.02, 0.9), (1.5, 0.02, 0.9 + 3.0 * kz)], col=AMARILLO, w=3.4, a=0.95, glow=1.0)
    for zz in (0.9, 0.9 + 3.0 * kz):
        line3(fr, [(1.3, 0.02, zz), (1.7, 0.02, zz)], col=AMARILLO, w=3.4, a=0.95, glow=1.0)
    if kz > 0.95:
        pts = [(-1.5, 0.02, 4.0), (4.5, 0.02, 4.0), (4.5, 0.02, 5.6), (-1.5, 0.02, 5.6)]
        s, z = fr.cam.proj(np.array(pts))
        if (z > 0.2).all():
            fr.df.polygon([tuple(p) for p in s], fill=M.scale_c(VERDE, 0.3))
    # brinco hechizo (rampa) y zanja en el camino
    kb = eout(seg(u, ub - 0.2, ub + 0.1))
    if kb > 0.01:
        ramp = M3.Mesh([(-2.2, 0, -0.6), (-1.4, 0, -0.6), (-1.4, 0.45 * kb, -0.6), (-2.2, 0, 0.6), (-1.4, 0, 0.6),
                        (-1.4, 0.45 * kb, 0.6)], [(0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)],
                       (150, 120, 90), shadow=0, gloss=0.1, double=True)
        draw_objects(fr, [named(ramp, 'rampa', rim=0.5)])
    kzj = eout(seg(u, uz - 0.2, uz + 0.1))
    if kzj > 0.01:
        line3(fr, [(-4.6, 0.02, -0.7), (-3.9, 0.02, -0.7), (-3.9, 0.02, 0.7), (-4.6, 0.02, 0.7), (-4.6, 0.02, -0.7)],
              col=(200, 150, 100), w=3.0, a=kzj, glow=0.6)
    p30 = fr.cam.p1((1.5, 0.0, 0.9 + 1.5 * kz))
    pv = fr.cam.p1((1.5, 0.0, 4.0))
    pr = fr.cam.p1((-1.8, 0.2, 0.0))
    pzj = fr.cam.p1((-4.25, 0.0, 0.0))

    def ui(img, fx):
        kicker(img, 'LO QUE PIDE SCORE AL PÚBLICO', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, p30[0] + 120, p30[1], '30 m', 64, AMARILLO, kz, glow=0.5)
        pill(img, fx, pv[0] - 120, pv[1] - 40, 'AQUÍ SÍ', eout(seg(u, 0.6, 0.8)), size=26, border=VERDE)
        if kb > 0.01:
            doodle_circle(img, fx, pr[0], pr[1], 150, 90, t, k=seg(u, ub, ub + 0.4), col=RED, seed=3)
            pill(img, fx, pr[0], pr[1] - 140, '✕ BRINCOS HECHIZOS', eout(seg(u, ub + 0.1, ub + 0.3)), size=24, border=RED, dot=False)
        if kzj > 0.01:
            doodle_circle(img, fx, pzj[0], pzj[1], 130, 80, t, k=seg(u, uz, uz + 0.4), col=RED, seed=5)
            pill(img, fx, pzj[0], pzj[1] + 130, '✕ ZANJAS', eout(seg(u, uz + 0.1, uz + 0.3)), size=24, border=RED, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. adentro del amortiguador hay otra carrera: el pistón bombea en aceite y cada golpe se vuelve calor
def amortiguador(fr, t, x0=0.0, calor=0.0, vel=6.0, amp=0.55, k=1.0, frenado=1.0):
    """Corte del amortiguador: cuerpo de línea que brilla, pistón y vástago de metal, aceite (puntos) que se
    calienta (ámbar → rojo) y pasa por los orificios del pistón."""
    R, H0, H1 = 0.42, 0.0, 3.2
    q = np.linspace(0, 2 * math.pi, 40)
    col_c = M.mixc(WHITE, (255, 120, 80), calor * 0.7)
    for y in (H0, H1):
        line3(fr, [(x0 + R * math.cos(a), y, R * math.sin(a)) for a in q], col=col_c, w=2.6, a=0.9 * k, glow=0.7)
    for a in (0.0, math.pi):
        line3(fr, [(x0 + R * math.cos(a), H0, R * math.sin(a)), (x0 + R * math.cos(a), H1, R * math.sin(a))], col=col_c,
              w=2.6, a=0.9 * k, glow=0.7)
    yp = 1.5 + amp * math.sin(t * vel)
    oil = M.mixc((255, 190, 70), (255, 70, 40), calor)
    rng = np.random.RandomState(7)
    for j in range(70):
        y = H0 + 0.1 + rng.rand() * (H1 - 0.2)
        if abs(y - yp) < 0.12:
            continue
        r = rng.rand() * (R - 0.06)
        a = rng.rand() * 2 * math.pi + t * (1.5 + 2 * rng.rand()) * (1 if y > yp else -1)
        jit = 0.04 * math.sin(t * 13 + j) * (1 + 2 * calor)
        dot3(fr, (x0 + r * math.cos(a), y + jit, r * math.sin(a)), r=3.2, col=oil, a=0.85 * k, glow=0.8 + calor)
    ms = [named(M3.cyl(R - 0.04, 0.16, (190, 194, 202), n=24, shadow=0, gloss=0.85).tf(t=(x0, yp - 0.08, 0)), 'piston',
                rim=0.8, gloss=0.85),
          named(M3.cyl(0.07, H1 + 1.0 - yp, (220, 222, 228), n=12, shadow=0, gloss=0.95).tf(t=(x0, yp, 0)), 'vastago',
                rim=0.9, gloss=0.95)]
    draw_objects(fr, ms)
    for s in (-1, 1):                                            # chorritos por los orificios del pistón
        ph = (t * 4) % 1.0
        line3(fr, [(x0 + s * 0.18, yp, 0.1), (x0 + s * 0.18, yp + (0.35 if math.cos(t * vel) < 0 else -0.35) * ph, 0.1)],
              col=oil, w=3.0, a=0.9 * k, glow=1.0)
    return yp


def s_amort(t, fi, u, d):
    uin = 0.9
    uc = Wp(10, 'calor') - 0.1
    if u < uin:                                                  # el amortiguador trasero del Trophy Truck…
        fr = Frame(camara(u, [K(-0.3, 4.4, 14, 8, tx=-1.3, ty=1.0, tz=0.9), K(0.25, 2.6, 6, 6, tx=-1.35, ty=1.0, tz=0.9),
                              K(uin, 1.6, 4, 6, tx=-1.38, ty=1.05, tz=0.9)], cy=0.55))
        space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8)
        draw_objects(fr, troca(comp=0.2 * math.sin(t * 6), luces=0.6, calor=0.4), xray=1.0,
                     keep=('in', 'llanta', 'rin', 'taco'))

        def ui0(img, fx):
            kicker(img, 'AMORTIGUADOR TRASERO', 150, seg(u, -0.1, 0.2), col=AZULC)
        fr.ui.append(ui0)
        out = finish(fr, fi)
        kz = seg(u, uin - 0.3, uin)                              # …y la cámara se mete por él
        if kz > 0:
            out = M.radial_blur(M.scale_about(out, 1 + 2.5 * kz * kz), 0.2 * kz)
        return out
    calor = eout(seg(u, uin, d), 2)
    fr = Frame(camara(u, [K(uin, 7.0, 30, 8, tx=0.0, ty=1.6), K(uin + 0.6, 5.6, 8, 4, tx=0.0, ty=1.6),
                          K(d, 5.4, 2, 4, tx=0.0, ty=1.6)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'CALOR', u, t0=uc, cy=0.3, entrada='zoom')
    amortiguador(fr, t, calor=calor, vel=9.0)
    P.ondas_calor(fr, t, 0.0, 3.3, 4.6, 1.4, k=calor)

    def ui(img, fx):
        kicker(img, 'ADENTRO DEL AMORTIGUADOR · CORTE', 150, seg(u, uin, uin + 0.3), col=AZULC)
        P.termometro(img, fx, 900, 1250, 380, 0.2 + 0.75 * calor, '', k=seg(u, uin + 0.2, uin + 0.5))
        pill(img, fx, 330, 1390, 'CADA GOLPE → CALOR', eout(seg(u, uc + 0.2, uc + 0.5)), size=26, border=NARANJA)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uin, 0.3), amp=14)


# 11. horas de desierto: el aceite se pone aguadito (gráfica) y deja de frenar el rebote (frío contra caliente)
def resorte_2d(img, fx, x, ytop, ybot_eq, t0, t, amort, col, etiqueta, k=1.0):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    v = max(0.0, t - t0)
    yb = ybot_eq - 160 * math.exp(-amort * v) * math.cos(9.0 * v)
    pts = []
    n = 14
    for i in range(n + 1):
        yy = lerp(ytop, yb - 60, i / n)
        xx = x + (34 if i % 2 else -34) * (0 < i < n)
        pts.append((xx, yy))
    d.line(pts, fill=M.scale_c(WHITE, 0.9 * k), width=5, joint='curve')
    df.line(pts, fill=M.scale_c(col, 0.5 * k), width=10)
    d.rounded_rectangle((x - 90, yb - 60, x + 90, yb + 40), radius=16, fill=M.scale_c(col, 0.85 * k))
    d.line([(x - 140, ytop), (x + 140, ytop)], fill=M.scale_c(WHITE, 0.7 * k), width=4)
    d.text((x, ybot_eq + 150), etiqueta, font=M.font('mono', 30), fill=M.scale_c(col, k), anchor='mm')


def s_aceite(t, fi, u, d):
    ud = Wp(11, 'deja') - 0.2
    fr = Frame(camara(u, [K(-0.3, 7.0, -20, 8, tx=0.0, ty=1.6), K(0.5, 6.0, -6, 4, tx=0.0, ty=1.6),
                          K(d, 6.0, 0, 4, tx=0.0, ty=1.6)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'EL ACEITE DEL AMORTIGUADOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u < ud:
            chart_grow(img, fx, (110, 300, 970, 1200), [30, 55, 75, 90, 100], ['1 h', '2 h', '3 h', '4 h', '5 h'], t - u, t,
                       unit='', title_txt='TEMPERATURA (ESCALA RELATIVA)', vmax=110, tag='EJEMPLO')
            texto(img, fx, 540, 1290, 'más caliente = más aguadito', 44, NARANJA, eout(seg(u, 1.4, 1.7)), f='serif')
        else:
            uu = u - ud
            resorte_2d(img, fx, 330, 380, 1000, t - uu + 0.05, t, 6.0, AZULC, 'ACEITE FRÍO', k=eout(seg(uu, 0, 0.15)))
            resorte_2d(img, fx, 750, 380, 1000, t - uu + 0.05, t, 0.9, NARANJA, 'ACEITE CALIENTE', k=eout(seg(uu, 0, 0.15)))
            pill(img, fx, 330, 1250, 'FRENA EL REBOTE', eout(seg(uu, 0.5, 0.8)), size=22, border=AZULC, dot=False)
            pill(img, fx, 750, 1250, 'SIGUE REBOTANDO', eout(seg(uu, 0.5, 0.8)), size=22, border=NARANJA, dot=False)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, ud, 0.3), amp=16)


# 12. el tanque con nitrógeno y aletas (se arma solo; el aire pasa por las aletas y lo enfría)
def tanque(abre=0.0, t=0.0):
    ms = []
    ms.append(named(M3.cyl(0.42, 2.6, (200, 40, 30), n=26, shadow=0, gloss=0.8).tf(t=(-0.8, 0.0, 0)), 'cuerpo', rim=0.8, gloss=0.8))
    ms.append(named(M3.cyl(0.07, 1.2, (220, 222, 228), n=12, shadow=0, gloss=0.95).tf(t=(-0.8, 2.6, 0)), 'vastago', rim=0.9))
    ms.append(named(M3.cyl(0.36, 2.0, ORO, n=26, shadow=0, gloss=0.85).tf(t=(0.8, 0.5, 0)), 'deposito', rim=0.85, gloss=0.85))
    for j in range(9):                                              # aletas
        ms.append(named(M3.cyl(0.5, 0.05, (230, 190, 100), n=26, shadow=0, gloss=0.8).tf(t=(0.8, 0.7 + j * 0.18, 0)),
                        'aleta', rim=0.9, gloss=0.8))
    ms.append(tubo((-0.4, 2.3, 0), (0.45, 2.3, 0), r=0.07, col=CROMO, name='manguera'))
    return P.despiece(ms, abre, centro=(0, 1.3, 0), fuerza=1.2, giro=0.4)


def s_tanque(t, fi, u, d):
    un = Wp(12, 'nitrogeno') - 0.1
    ua = Wp(12, 'aletas') - 0.1
    abre = 1 - P.eout4(seg(u, -0.2, 0.5))
    fr = Frame(camara(u, [K(-0.3, 9.0, 60, 18, tx=0.0, ty=1.4), K(0.4, 8.0, 28, 10, tx=0.1, ty=1.4),
                          K(ua - 0.4, 7.8, 24, 10, tx=0.2, ty=1.4), K(ua, 6.6, -8, 6, tx=0.5, ty=1.4),
                          K(d, 6.5, -12, 6, tx=0.5, ty=1.4)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.4)
    draw_objects(fr, tanque(abre, t), xray=clamp(seg(u, un - 0.2, un + 0.2)) * (1 - seg(u, ua, ua + 0.3)),
                 keep=('vastago',))
    if un - 0.2 < u < ua + 0.3:                                   # nitrógeno (puntos cian) sobre el pistón flotante
        rng = np.random.RandomState(2)
        for j in range(30):
            y = 1.7 + rng.rand() * 0.75
            a = rng.rand() * 6.28 + t * 2
            r = rng.rand() * 0.3
            dot3(fr, (0.8 + r * math.cos(a), y + 0.03 * math.sin(t * 9 + j), r * math.sin(a)), r=3, col=CYAN, glow=1.2)
    if u > ua:                                                     # aire que pasa por las aletas
        for j in range(6):
            ph = (t * 1.8 + j / 6) % 1.0
            y = 0.8 + j * 0.25
            line3(fr, [(-1.6 + 4.0 * ph, y, 0.7), (-1.0 + 4.0 * ph, y, 0.7)], col=AZULC, w=2.4,
                  a=0.8 * (1 - ph) * seg(u, ua, ua + 0.3), glow=1.0)
    pn = fr.cam.p1((0.8, 2.3, 0.0))
    pa = fr.cam.p1((1.35, 1.2, 0.0))

    def ui(img, fx):
        kicker(img, 'DEPÓSITO EXTERNO DEL AMORTIGUADOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pn[0] + 120, pn[1] - 80, 'NITRÓGENO', eout(seg(u, un, un + 0.3)), size=26, border=CYAN)
        pill(img, fx, pa[0] + 150, pa[1], 'ALETAS = MENOS CALOR', eout(seg(u, ua, ua + 0.3)), size=24, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. mándaselo a tu compa que va a ver la Baja 1000 (de noche, barra de luces prendida, rumbo a la meta)
def s_compa(t, fi, u, d):
    x = 2.0 * u
    fr = Frame(camara(u, [K(-0.3, 7.6, 70, 4, tx=0.0, ty=0.9), K(0.4, 6.2, 40, 3, tx=0.0, ty=0.9),
                          K(d, 6.0, 34, 3, tx=0.0, ty=0.9)], cy=0.62, off=(x, 0, 0)))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.0)
    desierto(fr, t, seed=13)
    bump = 0.12 * abs(math.sin(u * 7))
    draw_objects(fr, P.tfk(troca(comp=0.4 * math.sin(u * 7), giro=-x / 0.46, luces=1.8), t=(x, bump, 0)))
    pl = fr.cam.p1((x + 0.5, 2.15, 0.0))
    rueda = fr.cam.p1((x - 1.45, 0.05, 1.0))

    def ui(img, fx):
        df = ImageDraw.Draw(fx)
        for j, r in enumerate((80, 160, 260)):
            df.ellipse((pl[0] - r, pl[1] - r * 0.5, pl[0] + r, pl[1] + r * 0.5), fill=M.scale_c((255, 240, 200), 0.3 / (j + 1)))
        polvo(img, fx, rueda[0] - 120, rueda[1], t, k=1.0, escala=1.3, seed=8)
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que va a ver la Baja 1000.', 'serif')], 220,
                       seg(u, 0.0, 0.15), size=70)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55),
                sfx=[(-0.3, 'thud', 0.8), (-0.08, 'thud', 0.8), (0.14, 'thud', 0.8), (U_YA, 'bass', 1.0), (U_YA, 'whoosh', 0.8),
                     (U_SALTO, 'riser', 0.5), (0.75, 'sub', 0.8), (U_CAE, 'sub', 1.0), (U_CAE, 'bass', 0.9),
                     (U_CAE + 0.2, 'thud', 0.6)]),
           dict(desde=1, fn=s_hoy, tr='iris', c=(0.55, 0.6), sfx=[(0.2, 'bass', 0.7), (2.3, 'chime_b', 0.5), (2.3, 'shimmer', 0.4)]),
           dict(desde=2, fn=s_cabo, tr='cristal', palabra='1 500 KM',
                sfx=[(0.3 + 0.25 * j, 'tick', 0.35) for j in range(14)] + [(3.6, 'chime_c', 0.5)]),
           dict(desde=3, fn=s_pickup, tr='zoom', c=(0.5, 0.5), sfx=[(0.05, 'thud', 0.7), (0.6, 'shimmer', 0.5), (4.6, 'click', 0.7),
                                                                   (5.0, 'tick2', 0.6)]),
           dict(desde=4, fn=s_trophy, tr='cubo', sfx=[(0.5, 'tick2', 0.6), (1.2, 'chime_a', 0.4)]),
           dict(desde=5, fn=s_cae, tr='deslizar_abajo', sfx=[(-0.1, 'whoosh', 0.7), (0.35, 'sub', 1.0), (0.35, 'bass', 0.9),
                                                             (1.8, 'click', 0.8), (2.2, 'click', 0.8)]),
           dict(desde=6, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.0, 'bass', 0.9), (2.3, 'sub', 0.8)]),
           dict(desde=7, fn=s_curva, tr='whip', sfx=[(1.6, 'whoosh', 0.8), (3.3, 'bass', 1.0), (3.4, 'sub', 0.7)]),
           dict(desde=8, fn=s_2016, tr='flash', sfx=[(0.1, 'slap', 0.9), (4.25, 'bass', 0.9)]),
           dict(desde=9, fn=s_30m, tr='deslizar', sfx=[(0.1, 'tick', 0.6), (0.6, 'chime_a', 0.5), (3.8, 'scribble', 0.7),
                                                       (4.5, 'scribble', 0.7)]),
           dict(desde=10, fn=s_amort, tr='golpe', c=(0.5, 0.5), sfx=[(0.5, 'whoosh', 0.8), (0.9, 'thud', 0.7), (2.7, 'riser', 0.4)]),
           dict(desde=11, fn=s_aceite, tr='remolino', sfx=[(0.3 + 0.28 * j, 'chime_a', 0.35) for j in range(5)] + [(2.9, 'bass', 0.7)]),
           dict(desde=12, fn=s_tanque, tr='giro', sfx=[(0.3, 'click', 0.8), (1.2, 'shimmer', 0.5), (2.0, 'whoosh_suave', 0.5)]),
           dict(desde=13, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7)]),
           dict(desde=14, loop=True, tr='wipe')]

if __name__ == '__main__':
    montaje.cli(globals())
