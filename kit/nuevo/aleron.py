"""Reel diario sáb 14-nov-2026 18:00 — «Tu alerón no te pega… al piso.»
Comunidad: F1 y tuning (decisión de Efrén del 10-nov: vehículos y comunidades mexicanas por dentro).
Inicio tipo 7 (macro extremo que se aleja): la trama de fibra de carbono del alerón con el aire marcado, gigante,
y un zoom hacia atrás revela el alerón trasero de un Fórmula 1 (recreación sin marcas) con «ALERÓN» de cristal detrás.
El final regresa al macro (loop). Ciencia: el alerón es un ala de avión al revés (aire más rápido abajo, presión baja,
carga), la carga crece con el cuadrado de la velocidad; error: el alerón de calle a 50 km/h empuja como 1 kilo y frena
el aire. Voz Isaac (eleven_v4), recortada para que el error caiga a los 26 s. Datos y fuentes: guiones/2026-11-14_aleron.txt.
Fotos reales: humo alrededor de un perfil de ala (NACA, dominio público) y vórtices de un ala en humo (NASA, dominio público).
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

M3 = M.M3
TEMA = 'aleron'
TXT = ['Tu alerón no te pega… al piso.',
       'El de un Fórmula 1, sí:',
       'es un ala de avión… al revés.',
       'El aire corre más rápido por abajo,',
       'la presión baja y el auto se hunde.',
       'A unos 150 km/h,',
       'un F1 ya hace tanta carga como lo que pesa.',
       'Por eso, en teoría, podría ir de cabeza por el techo de un túnel.',
       'Y al doble de velocidad, esa carga se multiplica por 4.',
       'Y aquí está el error:',
       'ponerle alerón a tu Tsuru para que «se pegue».',
       'A 50 km/h, un alerón de fábrica',
       'empuja como un kilo: una botella de agua.',
       'Y uno grande frena el aire: más gasolina,',
       'y en curva hasta lo desbalancea.',
       'Por eso los F1 de 2026 mueven sus alas:',
       'en la recta se abren y en la curva se cierran.',
       'Así es el Cadillac de Checo Pérez,',
       'que en México corrió su carrera número 300.',
       'Y en la CDMX el aire es tan delgado',
       'que las alas pierden como la cuarta parte.',
       'Mándaselo a quien le puso alerón a su Tsuru,',
       'porque tu alerón no te pega… al piso.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-14_aleron_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_aleron.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-14_aleron_words.json')
FOTOS = '/home/claude/fotos_1114'
if not os.path.exists(os.path.join(FOTOS, 'nasa_vortex.jpg')):
    FOTOS = os.path.join(_REPO, 'inbox')

AMARILLO = (255, 226, 90)
NARANJA = (255, 140, 50)
ROJO = (255, 60, 50)
AZULC = (150, 210, 230)
AGUA = (90, 170, 255)
VERDE = (120, 240, 160)
GRIS = (150, 150, 160)
CARBON = (38, 38, 44)
NEGRO = (22, 22, 26)
BLANCO = (232, 232, 236)
LLANTA = (30, 30, 33)
CROMO = (214, 216, 222)


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


# ------------------------------------------------------------------ utilidades
def K(u, dist, yaw, pitch, tx=0.0, ty=0.5, tz=0.0, roll=0.0):
    return (u, dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll))


def camara(u, claves, cy=0.56):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


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


def credito(img, txt, y=1872, k=1.0):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((540, y), txt, font=M.font('mono', 19), fill=M.scale_c((150, 150, 158), k), anchor='mm')


def tubo(p0, p1, r=0.03, col=CROMO, n=7, name='tubo'):
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
    return named(M3.Mesh(V, F, col, shadow=0, gloss=0.8, double=True), name, rim=0.8, gloss=0.8)


def _B(ms, sx, sy, sz, col, x, y, z, name='cuerpo', gloss=0.5, rim=0.6, glow=None, base=True, rz=0.0):
    m = named(M3.box(sx, sy, sz, col, shadow=0, gloss=gloss, base=base).tf(rz=rz, t=(x, y, z)), name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    ms.append(m)
    return m


def _rueda(ms, x, z, r, w, giro=0.0):
    ms.append(named(M3.cyl(r, w, LLANTA, n=24, shadow=0, gloss=0.15).tf(rx=90, t=(x, r, z - w / 2)), 'llanta', rim=0.4))
    ms.append(named(M3.cyl(r * 0.55, w + 0.01, (70, 72, 78), n=14, shadow=0, gloss=0.8).tf(rx=90, t=(x, r, z - w / 2 - 0.005)),
                    'rin', rim=0.7))
    for j in range(3):
        a = giro + j * 2.1
        _B(ms, 0.05, 0.05, w + 0.03, CROMO, x + r * 0.3 * math.cos(a), r + r * 0.3 * math.sin(a), z, name='rin', base=False,
           gloss=0.9)


# ------------------------------------------------------------------ el Fórmula 1 (recreación sin marcas; frente hacia +x)
def f1(giro=0.0, flap=0.0, hundir=0.0, ala_glow=0.0, franja=None):
    """flap: 0 = alerón cerrado (curva, mucha carga); 1 = abierto (recta). hundir: baja la carrocería (carga)."""
    ms = []
    y0 = -0.05 * hundir
    for x, r, w in ((1.75, 0.34, 0.34), (-1.65, 0.36, 0.42)):
        for s in (-1, 1):
            _rueda(ms, x, s * 0.82, r, w, giro)
    _B(ms, 4.0, 0.04, 1.35, CARBON, 0.0, 0.07 + y0, 0, name='piso', gloss=0.4)
    ms.append(named(M3.rbox(2.1, 0.42, 0.7, 0.18, NEGRO, n=4, shadow=0, gloss=0.85).tf(t=(0.25, 0.1 + y0, 0)), 'cuerpo',
                    rim=0.8, gloss=0.85))
    ms.append(named(M3.cyl(0.24, 1.55, NEGRO, n=20, r2=0.08, shadow=0, gloss=0.85).tf(rz=-90, t=(1.25, 0.36 + y0, 0)), 'cuerpo',
                    rim=0.8, gloss=0.85))                                                    # trompa
    for s in (-1, 1):
        ms.append(named(M3.rbox(1.5, 0.38, 0.42, 0.16, NEGRO, n=4, shadow=0, gloss=0.85).tf(t=(-0.25, 0.1 + y0, s * 0.56)),
                        'cuerpo', rim=0.8, gloss=0.85))                                     # pontones
    ms.append(named(M3.cyl(0.3, 1.7, BLANCO, n=20, r2=0.1, shadow=0, gloss=0.8).tf(rz=90, t=(-0.2, 0.5 + y0, 0)), 'cuerpo',
                    rim=0.8, gloss=0.8))                                                     # cubierta del motor
    _B(ms, 0.28, 0.32, 0.3, BLANCO, -0.15, 0.6 + y0, 0, gloss=0.8)                          # toma de aire
    ms.append(tubo((0.75, 0.62 + y0, 0), (0.2, 0.82 + y0, 0), r=0.035, col=(60, 60, 66), name='halo'))
    for s in (-1, 1):
        ms.append(tubo((0.2, 0.82 + y0, 0), (-0.05, 0.62 + y0, s * 0.22), r=0.03, col=(60, 60, 66), name='halo'))
    if franja:
        for j, col in enumerate(franja):
            _B(ms, 1.2, 0.012, 0.08, col, -0.3, 0.8 + y0, (j - 1) * 0.08, gloss=0.6, base=False)
    # alerón delantero
    _B(ms, 0.42, 0.035, 1.95, CARBON, 2.72, 0.1 + y0, 0, name='ala_d', gloss=0.6)
    _B(ms, 0.28, 0.03, 1.85, CARBON, 2.58, 0.19 + y0, 0, name='ala_d', gloss=0.6, rz=12)
    for s in (-1, 1):
        _B(ms, 0.55, 0.24, 0.03, CARBON, 2.7, 0.06 + y0, s * 0.98, name='ala_d', gloss=0.5)
    # alerón trasero (dos planos; el de arriba se abre en la recta)
    g = M.scale_c(CYAN, 0.5 * ala_glow) if ala_glow > 0.02 else None
    _B(ms, 0.46, 0.04, 1.0, CARBON, -2.3, 0.92 + y0, 0, name='ala', gloss=0.6, glow=g, rz=-8)
    _B(ms, 0.3, 0.03, 1.0, CARBON, -2.52 + 0.04 * flap, 1.06 + y0 + 0.08 * flap, 0, name='ala', gloss=0.6, glow=g,
       rz=-38 + 34 * flap)
    for s in (-1, 1):
        _B(ms, 0.7, 0.56, 0.03, CARBON, -2.38, 0.6 + y0, s * 0.51, name='ala', gloss=0.5)
    _B(ms, 0.06, 0.5, 0.06, (60, 60, 66), -2.2, 0.45 + y0, 0, name='ala', gloss=0.5)
    return ms


# ------------------------------------------------------------------ un sedán compacto de calle (recreación, sin marca)
def sedan(giro=0.0, col=(226, 226, 230), ala=1.0, ala_s=1.0, botella=0.0):
    ms = []
    for x in (1.25, -1.25):
        for s in (-1, 1):
            _rueda(ms, x, s * 0.72, 0.3, 0.2, giro)
    ms.append(named(M3.rbox(4.1, 0.55, 1.62, 0.22, col, n=4, shadow=0, gloss=0.7).tf(t=(0, 0.28, 0)), 'cuerpo', rim=0.8, gloss=0.7))
    ms.append(named(M3.rbox(1.95, 0.48, 1.42, 0.25, (70, 80, 92), n=4, shadow=0, gloss=0.9).tf(t=(-0.15, 0.83, 0)), 'vidrio',
                    rim=0.8, gloss=0.9))
    _B(ms, 1.6, 0.05, 1.36, col, -0.15, 1.3, 0, gloss=0.7)                                     # techo
    for s in (-1, 1):
        _B(ms, 0.04, 0.1, 0.3, (255, 250, 230), 2.06, 0.6, s * 0.55, glow=(120, 115, 100), gloss=0.9)  # faros
        _B(ms, 0.04, 0.1, 0.3, (220, 40, 40), -2.06, 0.62, s * 0.55, glow=(90, 10, 10), gloss=0.9)    # calaveras
    if ala > 0.01:
        h = 0.55 * ala_s
        for s in (-1, 1):
            _B(ms, 0.08, h * ala, 0.06, NEGRO, -1.75, 0.83, s * 0.5, name='ala', gloss=0.6)
        _B(ms, 0.5 * ala_s, 0.05, 1.5 * min(1.15, ala_s), NEGRO, -1.8, 0.83 + h * ala, 0, name='ala', gloss=0.7, rz=-6)
        for s in (-1, 1):
            _B(ms, 0.5 * ala_s, 0.22 * ala_s, 0.03, NEGRO, -1.8, 0.75 + h * ala, s * 0.75 * min(1.15, ala_s), name='ala', gloss=0.6)
    if botella > 0.01:
        b = named(M3.cyl(0.09, 0.32, (120, 190, 240), n=16, shadow=0, gloss=0.9).tf(t=(-1.8, 0.88 + h * ala - 0.3 * (1 - botella), 0)),
                  'botella', rim=0.9, gloss=0.9)
        b.glow = M.scale_c(AGUA, 0.25)
        ms.append(b)
        ms.append(named(M3.cyl(0.05, 0.06, (240, 240, 245), n=12, shadow=0).tf(t=(-1.8, 1.2 + h * ala - 0.3 * (1 - botella), 0)),
                        'botella', rim=0.8))
    return ms


# ------------------------------------------------------------------ perfil de ala 2D y líneas de aire
def perfil(cx, cy, cuerda, inv=False, ang=0.0, n=40):
    """Perfil NACA 4412 (curvo arriba). inv=True lo voltea (curvo abajo, como en un F1). ang en grados."""
    m, p, t_ = 0.04, 0.4, 0.12
    up, lo = [], []
    for i in range(n + 1):
        x = (1 - math.cos(math.pi * i / n)) / 2
        yt = 5 * t_ * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1015 * x ** 4)
        yc = m / p ** 2 * (2 * p * x - x * x) if x < p else m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x * x)
        up.append((x, yc + yt))
        lo.append((x, yc - yt))
    pts = up + lo[::-1]
    a = math.radians(ang)
    out = []
    for x, y in pts:
        y = -y if inv else y
        xx, yy = (x - 0.4) * cuerda, -y * cuerda
        out.append((cx + xx * math.cos(a) - yy * math.sin(a), cy + xx * math.sin(a) + yy * math.cos(a)))
    return out


def dibujar_perfil(img, fx, pts, k=1.0, col=WHITE, relleno=(30, 30, 36), glow=0.6):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=M.scale_c(relleno, k))
    d.line(pts + [pts[0]], fill=M.scale_c(col, k), width=5, joint='curve')
    ImageDraw.Draw(fx).line(pts + [pts[0]], fill=M.scale_c(col, glow * k), width=12, joint='curve')


def lineas_aire(img, fx, cx, cy, cuerda, t, inv=True, k=1.0, n=9, vel=1.0, rapido=1.8, col=(200, 230, 255)):
    """Líneas de corriente alrededor del perfil: del lado curvo se juntan y corren más rápido (puntos que avanzan)."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    sgn = 1 if inv else -1                      # sgn=1: lado curvo abajo (en pantalla, y crece hacia abajo)
    for i in range(n):
        h = (i - (n - 1) / 2) / ((n - 1) / 2)    # −1 (arriba) … 1 (abajo)
        base = cy + h * cuerda * 0.42
        lado_curvo = (h * sgn) > 0
        amp = cuerda * (0.16 if lado_curvo else 0.06) * math.exp(-abs(h) * 1.6)
        pts = []
        for j in range(60):
            x = cx - 560 + j * 1120 / 59
            xx = (x - cx) / cuerda
            bump = math.exp(-((xx + 0.05) / 0.38) ** 2)
            y = base + (1 if h >= 0 else -1) * amp * bump
            pts.append((x, y))
        d.line(pts, fill=M.scale_c(col, 0.35 * k), width=2)
        v = vel * (rapido if lado_curvo else 1.0)
        for j in range(6):
            q = ((t * v * 0.35 + j / 6 + i * 0.13) % 1.0) * 59
            a, b = int(q), min(59, int(q) + 1)
            x, y = pts[a][0] + (pts[b][0] - pts[a][0]) * (q - a), pts[a][1] + (pts[b][1] - pts[a][1]) * (q - a)
            r = 6 if lado_curvo else 5
            c2 = CYAN if lado_curvo else col
            d.ellipse((x - r, y - r, x + r, y + r), fill=M.scale_c(c2, k))
            df.ellipse((x - 2 * r, y - 2 * r, x + 2 * r, y + 2 * r), fill=M.scale_c(c2, 0.5 * k))


def flecha(img, fx, x, y0, y1, col, k=1.0, w=14):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    y1 = y0 + (y1 - y0) * k
    d.line([(x, y0), (x, y1)], fill=col, width=w)
    s = 1 if y1 > y0 else -1
    d.polygon([(x - w * 1.8, y1 - s * w * 2), (x + w * 1.8, y1 - s * w * 2), (x, y1 + s * w * 0.6)], fill=col)
    ImageDraw.Draw(fx).line([(x, y0), (x, y1)], fill=M.scale_c(col, 0.5), width=w * 2)


# ------------------------------------------------------------------ fibra de carbono (macro del inicio)
_TEX = {}


def carbono(w=1080, h=1920, celda=96):
    key = (w, h, celda)
    if key in _TEX:
        return _TEX[key]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = (x + y) / celda, (x - y) / celda
    iu, iv = np.floor(u), np.floor(v)
    fu, fv = u - iu, v - iv
    tw = ((iu + iv) % 2 == 0)
    hilo = np.where(tw, np.sin(fu * math.pi), np.sin(fv * math.pi)) ** 0.7
    rayas = 0.5 + 0.5 * np.sin((np.where(tw, fv, fu)) * math.pi * 14)
    g = 22 + 70 * hilo * (0.75 + 0.25 * rayas)
    spec = np.exp(-((x / w - 0.35) ** 2 + (y / h - 0.4) ** 2) / 0.05) * 90 * hilo
    img = np.stack([g + spec, g + spec, g * 1.06 + spec], 2).clip(0, 255).astype(np.uint8)
    _TEX[key] = Image.fromarray(img)
    return _TEX[key]


_F = {}


def foto(n):
    if n not in _F:
        if n == 'naca':
            _F[n] = Image.open(os.path.join(FOTOS, 'naca_frame.jpg')).convert('RGB')
        else:
            im = Image.open(os.path.join(FOTOS, 'nasa_vortex.jpg')).convert('RGB')
            _F[n] = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    return _F[n]


CRED_NACA = 'FOTO: NACA LANGLEY · DOMINIO PÚBLICO'
CRED_NASA = 'FOTO: NASA LANGLEY · DOMINIO PÚBLICO'

# ================================================================== escenas
# 0. gancho (inicio 7: macro extremo que se aleja): fibra de carbono gigante → el alerón → el F1 completo
U_Z0, U_Z1 = 0.15, 0.95


def _f1_gancho(t, u):
    fr = Frame(camara(u, [K(-1, 3.2, -150, 14, tx=-2.0, ty=0.85), K(U_Z1, 3.2, -150, 14, tx=-2.0, ty=0.85),
                          K(U_Z1 + 0.6, 6.6, -125, 12, tx=-0.6, ty=0.5), K(4, 6.4, -120, 12, tx=-0.5, ty=0.5)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ALERÓN', u, t0=-0.6, cy=0.32, entrada='golpe')
    draw_objects(fr, f1(giro=-t * 3, ala_glow=0.8))
    return fr


def s_gancho(t, fi, u, d):
    fr = _f1_gancho(t, u)
    # dónde queda el alerón en pantalla (para que el macro se encoja exactamente ahí)
    q = [fr.cam.p1((-2.3 + dx, 0.92 + dy, dz)) for dx in (-0.25, 0.25) for dy in (-0.05, 0.12) for dz in (-0.5, 0.5)]
    xs, ys = [p[0] for p in q], [p[1] for p in q]
    bx = (min(xs), min(ys), max(xs), max(ys))
    kz = P.eout4(seg(u, U_Z0, U_Z1))

    def ui(img, fx):
        if kz < 1:
            x0 = lerp(-60, bx[0], kz)
            y0 = lerp(-60, bx[1], kz)
            x1 = lerp(1140, bx[2], kz)
            y1 = lerp(1980, bx[3], kz)
            w, h = max(2, int(x1 - x0)), max(2, int(y1 - y0))
            tex = carbono().resize((w, h), Image.BILINEAR)
            dl = ImageDraw.Draw(tex)
            for j in range(7):                                  # el aire marcado sobre la fibra
                yy = h * (0.12 + 0.13 * j)
                off = (t * 900 + j * 170) % (w + 400) - 200
                dl.line([(off - 260, yy), (off, yy + 18 * math.sin(j))], fill=(150, 230, 255), width=max(1, int(6 * (1 - kz) + 1)))
            a = 1.0 - seg(kz, 0.75, 1.0)
            m = Image.new('L', (w, h), int(255 * a))
            img.paste(tex, (int(x0), int(y0)), m)
            if kz < 0.6:
                kicker(img, 'MACRO · FIBRA DE CARBONO', 150, 1 - seg(kz, 0.3, 0.6), col=AZULC)
        kicker(img, 'FÓRMULA 1 · LO QUE NO VES', 150, seg(u, U_Z1, U_Z1 + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu alerón no te pega…', 'sans'), ('al piso.', 'serif')], 240,
                       seg(u, Wp(0, 'al') - 0.05, Wp(0, 'al') + 0.1), size=74)
        pill(img, fx, 540, 1480, 'RECREACIÓN', seg(u, U_Z1, U_Z1 + 0.3), size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, Wp(0, 'al') + 0.1, 0.3), amp=20)


# 1. el de un Fórmula 1, sí: el F1 aplastado contra el piso (flechas de carga)
def s_f1(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 7.5, 60, 14, ty=0.4), K(0.3, 6.6, 20, 10, ty=0.4), K(d, 6.4, 14, 10, ty=0.4)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8, beam=0.4)
    draw_objects(fr, f1(giro=-t * 8, hundir=seg(u, 0.4, 0.9), ala_glow=0.5))
    pts = [fr.cam.p1((x, 1.3, 0)) for x in (2.6, 0.2, -2.3)]

    def ui(img, fx):
        kicker(img, 'FÓRMULA 1', 150, 1.0, col=AZULC)
        texto(img, fx, 540, 300, 'sí se pega', 100, WHITE, eout(seg(u, 0.5, 0.7)), f='serif')
        for j, p in enumerate(pts):
            flecha(img, fx, p[0], p[1] - 200, p[1] - 20, CYAN, k=eout(seg(u, 0.3 + 0.08 * j, 0.55 + 0.08 * j)), w=10)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.9, 0.3), amp=12)


# 2. es un ala de avión… al revés: el perfil del avión gira 180° (foto real del humo de la NACA)
def s_alreves(t, fi, u, d):
    ur = Wp(2, 'reves') - 0.15
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 6, ty=0.5), K(d, 5.8, 0, 6, ty=0.5)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.7)
    M.cristal(fr.base, fr.fx, 'AL REVÉS', u, t0=ur, cy=0.24, entrada='zoom')
    kg = P.eout4(seg(u, ur - 0.1, ur + 0.35))

    def ui(img, fx):
        kicker(img, 'PERFIL DE UN ALA', 150, 1.0, col=AZULC)
        photo_card(img, fx, foto('naca'), 540, 680, 700, t - u - 0.15, t, caption=CRED_NACA, angle0=5.0)
        pts = perfil(540, 1260, 560, inv=False, ang=180 * kg)
        dibujar_perfil(img, fx, pts, 1.0)
        if kg < 0.5:
            flecha(img, fx, 540, 1200, 1030, VERDE, k=eout(seg(u, 0.0, 0.3)) * (1 - 2 * kg))
            pill(img, fx, 540, 990, 'AVIÓN: LO SUBE', eout(seg(u, 0.1, 0.35)) * (1 - 2 * kg), size=26, border=VERDE)
        else:
            flecha(img, fx, 540, 1320, 1500, CYAN, k=eout(seg(kg, 0.5, 1.0)))
            pill(img, fx, 540, 1560, 'F1: LO EMPUJA AL PISO', eout(seg(kg, 0.6, 1.0)), size=26, border=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ur + 0.35, 0.3), amp=14)


# 3. el aire corre más rápido por abajo (líneas de aire que se juntan y corren abajo)
def s_rapido(t, fi, u, d):
    ua = Wp(3, 'abajo') - 0.1
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 6, ty=0.5), K(d, 5.8, 0, 6, ty=0.5)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.7)
    z = 1.0 + 0.25 * P.eout4(seg(u, -0.2, 0.3))

    def ui(img, fx):
        kicker(img, 'EL AIRE ALREDEDOR DEL ALERÓN', 150, 1.0, col=AZULC)
        c = 700 * z
        lineas_aire(img, fx, 540, 960, c, t, inv=True, k=1.0, rapido=1.0 + 1.2 * seg(u, ua - 0.3, ua + 0.2))
        dibujar_perfil(img, fx, perfil(540, 960, c, inv=True), 1.0)
        pill(img, fx, 540, 640, 'ARRIBA: MÁS LENTO', eout(seg(u, 0.2, 0.45)), size=28, border=(200, 200, 210))
        pill(img, fx, 540, 1300, 'ABAJO: MÁS RÁPIDO', eout(seg(u, ua, ua + 0.25)), size=30, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. la presión baja y el auto se hunde (zona azul abajo y el F1 que baja)
def s_presion(t, fi, u, d):
    uh = Wp(4, 'hunde') - 0.1
    fr = Frame(camara(u, [K(-0.2, 3.6, -100, 8, tx=-1.6, ty=0.5), K(uh - 0.3, 3.4, -96, 6, tx=-1.6, ty=0.5),
                          K(uh, 6.0, -70, 8, tx=-0.4, ty=0.4), K(d, 5.8, -66, 8, tx=-0.4, ty=0.4)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    kb = seg(u, 0.0, 0.5)
    for j in range(5):
        ph = (t * 0.8 + j / 5) % 1.0
        line3(fr, [(-2.3 + 0.6 * math.cos(a) * ph, 0.82 - 0.25 * ph, 0.5 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24)],
              col=AGUA, w=3, a=kb * (1 - ph), glow=1.0)
    draw_objects(fr, f1(giro=-t * 8, hundir=seg(u, uh, uh + 0.3), ala_glow=0.6))
    pz = fr.cam.p1((-2.3, 0.75, 0))

    def ui(img, fx):
        kicker(img, 'PRESIÓN BAJA = CARGA', 150, 1.0, col=AZULC)
        pill(img, fx, pz[0], pz[1] + 90, 'PRESIÓN BAJA', eout(seg(u, 0.2, 0.45)), size=28, border=AGUA)
        if u > uh:
            texto(img, fx, 540, 300, 'se hunde', 100, WHITE, eout(seg(u, uh, uh + 0.2)), f='serif')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uh + 0.25, 0.35), amp=18)


# 5. a unos 150 km/h: velocímetro que se clava y la pista que corre
def s_150(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 7.0, 150, 10, ty=0.4), K(0.4, 6.0, 120, 8, ty=0.4), K(d, 5.8, 114, 8, ty=0.4)], cy=0.62))
    space(fr, t, floor=None, bokeh=0.6)
    M.cristal(fr.base, fr.fx, '150', u, t0=0.6, cy=0.3, entrada='golpe')
    for z in (-1.4, 1.4):
        line3(fr, [(-14, 0, z), (10, 0, z)], col=WHITE, w=3, a=0.8, glow=0.6)
    for j in range(10):
        x = 10 - ((j * 2.4 + t * 20) % 24)
        line3(fr, [(x, 0, 0), (x - 1.0, 0, 0)], col=AMARILLO, w=4, a=0.9, glow=0.8)
    draw_objects(fr, f1(giro=-t * 20, ala_glow=0.4))

    def ui(img, fx):
        kicker(img, 'VELOCIDAD', 150, 1.0, col=AZULC)
        v = int(150 * P.eout4(seg(u, -0.2, 0.9)))
        texto(img, fx, 540, 1480, f'{v} km/h', 110, WHITE, 1.0, f='mono', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.9, 0.3), amp=16)


# 6. ya hace tanta carga como lo que pesa: gráfica peso contra carga (iguales)
def s_pesa(t, fi, u, d):
    up = Wp(6, 'pesa') - 0.2
    fr = Frame(camara(u, [K(-0.2, 7.0, -30, 22, ty=0.3), K(0.4, 6.4, -12, 18, ty=0.3), K(d, 6.3, -8, 18, ty=0.3)], cy=0.38))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    draw_objects(fr, f1(giro=0.0, hundir=1.0, ala_glow=0.5))
    pc = fr.cam.p1((0, 1.0, 0))

    def ui(img, fx):
        kicker(img, 'A 150 km/h', 150, 1.0, col=AZULC)
        flecha(img, fx, pc[0] - 120, pc[1] - 230, pc[1] - 40, CYAN, k=eout(seg(u, 0.1, 0.4)))
        pill(img, fx, pc[0] - 120, pc[1] - 270, 'CARGA', eout(seg(u, 0.1, 0.35)), size=26, border=CYAN)
        flecha(img, fx, pc[0] + 120, pc[1] - 230, pc[1] - 40, AMARILLO, k=eout(seg(u, up - 0.2, up + 0.1)))
        pill(img, fx, pc[0] + 120, pc[1] - 270, 'PESO', eout(seg(u, up - 0.2, up + 0.05)), size=26, border=AMARILLO)
        if u > 0.3:
            chart_grow(img, fx, (190, 1100, 890, 1500), [1.0, 1.0], ['PESO DEL AUTO', 'CARGA'], t - u + 0.3, t, unit='',
                       title_txt='A UNOS 150 km/h', vmax=1.2, line=False)
        texto(img, fx, 540, 1580, '=', 120, WHITE, eout(seg(u, up, up + 0.2)), f='sans', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.2, 0.3), amp=14)


# 7. en teoría podría ir de cabeza por el techo de un túnel (el F1 sube al techo y la cámara gira)
def s_tunel(t, fi, u, d):
    uc = Wp(7, 'cabeza') - 0.2
    kr = P.eout4(seg(u, uc - 0.1, uc + 0.5))
    fr = Frame(camara(u, [K(-0.2, 9.0, 90, 4, ty=1.2), K(0.4, 7.0, 70, 4, ty=1.2), K(d, 6.8, 64, 4, ty=1.2)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.7)
    R = 2.6
    for j in range(14):                                                     # anillos del túnel que corren
        x = 12 - ((j * 1.8 + t * 16) % 25)
        line3(fr, [(x, 1.2 + R * math.sin(a), R * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 40)], col=WHITE,
              w=2.2, a=0.55, glow=0.5)
    for a0 in (0.0, math.pi):
        line3(fr, [(-12, 1.2 + R * math.sin(a0 + math.pi / 2), 0), (12, 1.2 + R * math.sin(a0 + math.pi / 2), 0)], col=AMARILLO,
              w=3, a=0.6, glow=0.6)
    ang = 180 * kr
    draw_objects(fr, _en_tunel(ang, t, R))

    def ui(img, fx):
        kicker(img, 'EN TEORÍA · NUNCA SE HA HECHO', 150, 1.0, col=AMARILLO)
        texto(img, fx, 540, 300, 'de cabeza', 100, WHITE, eout(seg(u, uc + 0.2, uc + 0.4)), f='serif')
        pill(img, fx, 540, 1480, 'RECREACIÓN', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def _en_tunel(ang, t, R):
    """El F1 pegado a la pared del túnel: ang=0 en el piso, 180 en el techo (gira alrededor del eje x del túnel)."""
    out = []
    for m in f1(giro=-t * 20, ala_glow=0.6):
        mm = m.tf(t=(0, 1.2 - R, 0))                             # piso del túnel en y = 1.2 − R
        mm = mm.tf(t=(0, -1.2, 0)).tf(rx=ang).tf(t=(0, 1.2, 0))
        out.append(mm)
    return out


# 8. al doble de velocidad, la carga se multiplica por 4 (curva v²)
def s_x4(t, fi, u, d):
    u4 = Wp(8, 'cuatro') - 0.1
    ud = Wp(8, 'doble') - 0.1
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 6, ty=0.5), K(d, 5.8, 0, 6, ty=0.5)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '×4', u, t0=u4, cy=0.28, entrada='zoom')

    def ui(img, fx):
        kicker(img, 'CARGA CONTRA VELOCIDAD', 150, 1.0, col=AZULC)
        d_ = ImageDraw.Draw(img)
        x0, y0, x1, y1 = 160, 1500, 920, 760
        d_.line([(x0, y1 - 20), (x0, y0), (x1 + 20, y0)], fill=(200, 200, 210), width=4)
        kc = eout(seg(u, -0.1, u4))
        pts = []
        for j in range(61):
            v = j / 60 * kc
            pts.append((x0 + (x1 - x0) * v, y0 - (y0 - y1) * v * v))
        if len(pts) > 1:
            d_.line(pts, fill=CYAN, width=7)
            ImageDraw.Draw(fx).line(pts, fill=M.scale_c(CYAN, 0.5), width=16)
        for v, txt, kk in ((0.5, '1×', seg(u, ud, ud + 0.3)), (1.0, '4×', seg(u, u4, u4 + 0.3))):
            if kk > 0:
                x, y = x0 + (x1 - x0) * v, y0 - (y0 - y1) * v * v
                d_.ellipse((x - 14, y - 14, x + 14, y + 14), fill=AMARILLO)
                d_.line([(x, y), (x, y0)], fill=M.scale_c(AMARILLO, 0.6), width=3)
                texto(img, fx, x, y0 + 50, '100 km/h' if v < 1 else '200 km/h', 34, WHITE, kk, f='mono', glow=0.2)
                pill(img, fx, x - 90, y - 10, txt, eout(kk), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u4 + 0.2, 0.3), amp=16)


# 9. y aquí está el error (rojo; título que se estrella)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 7.0, 30, 10, ty=0.6), K(d, 6.4, 20, 10, ty=0.6)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    draw_objects(fr, sedan(giro=-t * 4, ala=0.0))

    def ui(img, fx):
        ImageDraw.Draw(fx).rectangle((0, 0, 1080, 1920), fill=M.scale_c((90, 0, 0), 0.25 + 0.12 * math.sin(t * 12)))
        kicker(img, '⚠ EL ERROR', 150, 1.0, col=ROJO)
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 260, seg(u, 0.0, 0.15), size=92)
        pill(img, fx, 540, 1480, 'RECREACIÓN', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.35), amp=24)


# 10. ponerle alerón a tu Tsuru para que «se pegue» (el alerón gigante sale con resorte)
def s_tsuru(t, fi, u, d):
    ua = Wp(10, 'aleron') - 0.1
    up = Wp(10, 'pegue') - 0.1
    fr = Frame(camara(u, [K(-0.2, 7.0, -40, 12, ty=0.6), K(ua, 5.6, -120, 14, tx=-1.0, ty=0.8), K(d, 5.4, -126, 14, tx=-1.0, ty=0.8)],
                      cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5)
    ka = P.resorte(seg(u, ua, ua + 0.4))
    draw_objects(fr, sedan(giro=0.0, ala=max(0.0, ka), ala_s=1.25))
    pa = fr.cam.p1((-1.8, 1.6, 0))

    def ui(img, fx):
        kicker(img, 'TU AUTO DE TODOS LOS DÍAS', 150, 1.0, col=AZULC)
        if u > up:
            texto(img, fx, 540, 300, '«para que se pegue»', 74, WHITE, eout(seg(u, up, up + 0.2)), f='serif')
            doodle_circle(img, fx, pa[0], pa[1], 230, 120, t, k=seg(u, up, up + 0.3), col=AMARILLO, w=6, seed=3)
        pill(img, fx, 540, 1480, 'RECREACIÓN', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.2, 0.3), amp=16)


# 11. a 50 km/h, un alerón de fábrica (el auto a 50 y el aire lento)
def s_50(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 7.0, 150, 10, ty=0.5), K(0.4, 6.2, 125, 8, ty=0.5), K(d, 6.0, 118, 8, ty=0.5)], cy=0.62))
    space(fr, t, floor=None, bokeh=0.6)
    for z in (-1.4, 1.4):
        line3(fr, [(-14, 0, z), (10, 0, z)], col=WHITE, w=3, a=0.8, glow=0.6)
    for j in range(10):
        x = 10 - ((j * 2.4 + t * 5) % 24)
        line3(fr, [(x, 0, 0), (x - 1.0, 0, 0)], col=AMARILLO, w=4, a=0.9, glow=0.8)
    draw_objects(fr, sedan(giro=-t * 5, ala=1.0, ala_s=0.8))
    for j in range(8):
        x = 4 - ((j * 1.0 + t * 1.2) % 8)
        dot3(fr, (x, 1.5 + 0.1 * math.sin(j), (j % 3 - 1) * 0.4), r=4, col=(200, 230, 255), a=0.7, glow=0.8)

    def ui(img, fx):
        kicker(img, 'ALERÓN DE FÁBRICA', 150, 1.0, col=AZULC)
        v = int(50 * P.eout4(seg(u, -0.2, 0.8)))
        texto(img, fx, 540, 330, f'{v} km/h', 120, WHITE, 1.0, f='mono', glow=0.5)
        pill(img, fx, 540, 1480, 'RECREACIÓN', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 12. empuja como un kilo: una botella de agua (la botella cae sobre el alerón)
def s_kilo(t, fi, u, d):
    ub = Wp(12, 'botella') - 0.1
    uk = Wp(12, 'kilo') - 0.1
    fr = Frame(camara(u, [K(-0.2, 3.2, -150, 16, tx=-1.6, ty=1.0), K(uk, 2.6, -130, 12, tx=-1.7, ty=1.1),
                          K(d, 2.5, -124, 12, tx=-1.7, ty=1.1)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.5, beam_x=0.5)
    M.cristal(fr.base, fr.fx, '1 KILO', u, t0=uk, cy=0.27, entrada='golpe')
    e = P.entrada(u, ub - 0.3, 0.35, 'cae')
    draw_objects(fr, sedan(ala=1.0, ala_s=0.8, botella=1.0 if u > ub - 0.3 else 0.0) if u > ub - 0.3 else sedan(ala=1.0, ala_s=0.8))
    pb = fr.cam.p1((-1.8, 1.3, 0))

    def ui(img, fx):
        kicker(img, 'A 50 km/h', 150, 1.0, col=AZULC)
        flecha(img, fx, pb[0] + 200, pb[1] - 150, pb[1] - 10, CYAN, k=eout(seg(u, 0.0, 0.3)))
        pill(img, fx, pb[0] + 200, pb[1] - 190, '≈ 1 kg', eout(seg(u, uk, uk + 0.2)), size=30, border=CYAN)
        if u > ub:
            pill(img, fx, 540, 1480, '= UNA BOTELLA DE AGUA', eout(seg(u, ub, ub + 0.25)), size=30, border=AGUA)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.05, 0.3), amp=14)


# 13. uno grande frena el aire: más gasolina (foto real de los remolinos de un ala y la aguja de gasolina que baja)
def s_frena(t, fi, u, d):
    ug = Wp(13, 'gasolina') - 0.1
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 8, ty=0.6), K(d, 5.7, 0, 8, ty=0.6)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.7)

    def ui(img, fx):
        kicker(img, 'EL AIRE SE ARREMOLINA DETRÁS DEL ALA', 150, 1.0, col=AZULC)
        photo_card(img, fx, foto('vortex'), 540, 720, 820, t - u - 0.12, t, caption=CRED_NASA, angle0=-6.0)
        # medidor de gasolina
        cx, cy, r = 540, 1460, 170
        d_ = ImageDraw.Draw(img)
        d_.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=(200, 200, 210), width=8)
        texto(img, fx, cx - r + 10, cy + 10, 'E', 40, ROJO, 1.0, f='mono', glow=0.3)
        texto(img, fx, cx + r - 10, cy + 10, 'F', 40, WHITE, 1.0, f='mono', glow=0.2)
        lv = 0.8 - 0.55 * P.eout4(seg(u, ug - 0.2, ug + 0.6))
        a = math.radians(200 + 140 * lv)
        d_.line([(cx, cy), (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a))], fill=NARANJA, width=8)
        pill(img, fx, 540, 1250, 'MÁS GASOLINA', eout(seg(u, ug, ug + 0.25)), size=30, border=NARANJA)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=10)


# 14. en curva hasta lo desbalancea (vista de arriba: atrás pegado, adelante se abre)
def s_curva(t, fi, u, d):
    ud = Wp(14, 'desbalancea') - 0.1
    fr = Frame(camara(u, [K(-0.2, 12.0, 0, 80, ty=0.0), K(0.4, 10.0, 20, 72, ty=0.0), K(d, 9.6, 26, 70, ty=0.0)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    R0 = 5.0
    for rr in (R0 - 1.6, R0 + 1.6):
        line3(fr, [(rr * math.cos(a) - R0, 0, rr * math.sin(a)) for a in np.linspace(-1.2, 1.2, 40)], col=WHITE, w=3, a=0.8, glow=0.5)
    s = seg(u, -0.2, d)
    a = -0.8 + 1.0 * s
    sale = 0.9 * P.eout4(seg(u, ud - 0.3, ud + 0.6))
    r = R0 + sale
    pos = (r * math.cos(a) - R0, 0, r * math.sin(a))
    yaw = -math.degrees(a) - 90 + 12 * sale
    ms = [m.tf(ry=yaw, t=pos) for m in sedan(giro=-t * 8, ala=1.0, ala_s=1.2)]
    draw_objects(fr, ms)
    pf = fr.cam.p1((pos[0] + 1.6 * math.sin(math.radians(yaw)) * 0, 0.5, pos[2]))

    def ui(img, fx):
        kicker(img, 'EN UNA CURVA', 150, 1.0, col=AZULC)
        if u > ud - 0.3:
            texto(img, fx, 540, 300, 'se va de frente', 82, ROJO, eout(seg(u, ud - 0.3, ud)), f='serif', glow=0.5)
            doodle_arrow(img, fx, pf[0], pf[1], pf[0] + 260, pf[1] - 160, t, k=seg(u, ud - 0.2, ud + 0.2), col=ROJO, w=8, seed=6)
        pill(img, fx, 540, 1480, 'MUCHO ATRÁS, NADA ADELANTE', eout(seg(u, 0.3, 0.6)), size=26, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ud, 0.3), amp=14)


# 15. los F1 de 2026 mueven sus alas (el alerón trasero se abre y se cierra)
def s_2026(t, fi, u, d):
    fl = 0.5 + 0.5 * math.sin(max(0.0, u) * 5.0)
    fr = Frame(camara(u, [K(-0.2, 4.8, -160, 18, tx=-1.6, ty=0.8), K(0.4, 3.6, -140, 14, tx=-2.0, ty=0.9),
                          K(d, 3.5, -134, 14, tx=-2.0, ty=0.9)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5)
    draw_objects(fr, f1(giro=-t * 8, flap=fl, ala_glow=0.9))
    pa = fr.cam.p1((-2.4, 1.2, 0))

    def ui(img, fx):
        kicker(img, 'REGLAS DE 2026', 150, 1.0, col=AZULC)
        P.numero_golpe(img, fx, '2026', 320, seg(u, 0.0, 0.15), size=150, col=WHITE)
        pill(img, fx, pa[0], pa[1] - 140, 'ALERONES QUE SE MUEVEN', eout(seg(u, 0.4, 0.65)), size=26, border=CYAN)
        pill(img, fx, 540, 1480, 'RECREACIÓN', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=12)


# 16. en la recta se abren y en la curva se cierran (perfil 2D del alerón con su aleta + mini pista)
def s_modos(t, fi, u, d):
    ucu = Wp(16, 'curva') - 0.1
    ab = 1.0 if u < ucu else 1.0 - P.eout4(seg(u, ucu, ucu + 0.3))
    ab = ab * P.eout4(seg(u, -0.1, 0.3))
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 6, ty=0.5), K(d, 5.8, 0, 6, ty=0.5)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.7)

    def ui(img, fx):
        recta = u < ucu
        kicker(img, 'MODO RECTA' if recta else 'MODO CURVA', 150, 1.0, col=VERDE if recta else NARANJA)
        lineas_aire(img, fx, 540, 860, 520, t, inv=True, k=1.0, rapido=1.2 + 0.8 * (1 - ab), n=7)
        dibujar_perfil(img, fx, perfil(470, 880, 420, inv=True, ang=-6), 1.0)
        dibujar_perfil(img, fx, perfil(740, 790 - 40 * ab, 220, inv=True, ang=-50 + 44 * ab), 1.0, col=CYAN)
        texto(img, fx, 540, 330, 'se abre' if recta else 'se cierra', 96, WHITE, 1.0, f='serif')
        pill(img, fx, 540, 1130, 'MENOS FRENO DEL AIRE' if recta else 'MÁS CARGA', 1.0, size=28,
             border=VERDE if recta else NARANJA)
        # mini pista
        d_ = ImageDraw.Draw(img)
        pista = [(260, 1500), (820, 1500), (880, 1440), (880, 1340), (820, 1290), (500, 1290), (440, 1350), (260, 1350),
                 (200, 1420), (260, 1500)]
        d_.line(pista, fill=(120, 120, 130), width=8, joint='curve')
        if recta:
            d_.line([(300, 1500), (800, 1500)], fill=VERDE, width=10)
        else:
            d_.line([(820, 1500), (880, 1440), (880, 1340), (820, 1290)], fill=NARANJA, width=10, joint='curve')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ucu + 0.3, 0.3), amp=12)


# 17. así es el Cadillac de Checo Pérez (el F1 con franja verde-blanco-rojo; sin logos)
def s_checo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 8.0, 40, 12, ty=0.4), K(0.4, 6.4, 25, 8, ty=0.4), K(d, 6.2, 20, 8, ty=0.4)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8, beam=0.6)
    draw_objects(fr, f1(giro=-t * 8, ala_glow=0.4, franja=[(0, 150, 70), (235, 235, 235), (210, 30, 40)]))

    def ui(img, fx):
        kicker(img, 'TEMPORADA 2026', 150, 1.0, col=AZULC)
        P.titulo_golpe(img, fx, [('Checo Pérez', 'sans'), ('con Cadillac', 'serif')], 270, seg(u, 0.0, 0.15), size=84)
        pill(img, fx, 540, 1480, 'RECREACIÓN · SIN LOGOS', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


# 18. en México corrió su carrera número 300 (contador y la bandera de cuadros)
def s_300(t, fi, u, d):
    u3 = Wp(18, 'trescientos') - 0.1
    fr = Frame(camara(u, [K(-0.2, 7.0, 0, 10, ty=0.6), K(d, 6.6, 0, 10, ty=0.6)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    M.cristal(fr.base, fr.fx, '300', u, t0=u3, cy=0.42, entrada='golpe')

    def ui(img, fx):
        kicker(img, 'GRAN PREMIO DE MÉXICO · 1-NOV-2026', 150, 1.0, col=AZULC)
        v = int(300 * P.eout4(seg(u, -0.2, u3 + 0.1)))
        texto(img, fx, 540, 330, f'carrera {v}', 92, WHITE, 1.0, f='mono', glow=0.4)
        d_ = ImageDraw.Draw(img)
        for r in range(4):                                                     # bandera de cuadros que ondea
            for c in range(8):
                if (r + c) % 2:
                    continue
                x = 220 + c * 80
                y = 1330 + r * 60 + 14 * math.sin(t * 6 + c * 0.6)
                d_.rectangle((x, y, x + 80, y + 60), fill=(235, 235, 240))
        pill(img, fx, 540, 1640, 'AUTÓDROMO HERMANOS RODRÍGUEZ', eout(seg(u, 0.3, 0.6)), size=24, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u3 + 0.2, 0.3), amp=16)


# 19. en la CDMX el aire es tan delgado (prueba en dos casos: aire al nivel del mar contra a 2 285 m)
def s_cdmx(t, fi, u, d):
    ud = Wp(19, 'delgado') - 0.1
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 8, ty=0.6), K(d, 5.8, 0, 8, ty=0.6)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.6)

    def ui(img, fx):
        kicker(img, 'EL AIRE EN DOS LUGARES', 150, 1.0, col=AZULC)
        d_ = ImageDraw.Draw(img)
        rng = np.random.RandomState(3)
        for j, (cx, n, txt, col) in enumerate(((290, 300, 'NIVEL DEL MAR', (200, 200, 210)),
                                               (790, 225, 'CDMX · 2 285 m', AMARILLO))):
            kk = eout(seg(u, -0.2 + 0.3 * j, 0.1 + 0.3 * j))
            d_.rounded_rectangle((cx - 210, 520, cx + 210, 1300), radius=24, outline=M.scale_c(col, kk), width=4)
            for i in range(int(n * kk)):
                x = cx - 190 + rng.rand() * 380 + 6 * math.sin(t * 3 + i)
                y = 540 + rng.rand() * 740 + 6 * math.cos(t * 2.5 + i)
                d_.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(170, 220, 255))
            texto(img, fx, cx, 1360, txt, 34, col, kk, f='mono', glow=0.2)
        # montaña de línea con el marcador de altura
        d_.line([(560, 1700), (760, 1470), (840, 1530), (1000, 1420), (1080, 1520)], fill=(200, 200, 210), width=4)
        pill(img, fx, 540, 1560, '≈ 25 % MENOS AIRE EN CADA METRO CÚBICO', eout(seg(u, ud, ud + 0.25)), size=24, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. las alas pierden como la cuarta parte (las flechas de carga se encogen 25 %)
def s_cuarta(t, fi, u, d):
    uc = Wp(20, 'cuarta') - 0.1
    k = P.eout4(seg(u, uc - 0.2, uc + 0.4))
    fr = Frame(camara(u, [K(-0.2, 7.0, 30, 14, ty=0.4), K(0.4, 6.4, 15, 12, ty=0.4), K(d, 6.2, 10, 12, ty=0.4)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    draw_objects(fr, f1(giro=-t * 8, ala_glow=0.5 * (1 - 0.5 * k)))
    pts = [fr.cam.p1((x, 1.3, 0)) for x in (2.6, -2.3)]

    def ui(img, fx):
        kicker(img, 'CARGA DE LOS ALERONES EN LA CDMX', 150, 1.0, col=AZULC)
        for p in pts:
            flecha(img, fx, p[0], p[1] - 260 * (1 - 0.25 * k), p[1] - 20, CYAN, k=1.0)
        texto(img, fx, 540, 330, f'{int(100 - 25 * k)} %', 120, WHITE if k < 0.5 else NARANJA, 1.0, f='mono', glow=0.5)
        pill(img, fx, 540, 1480, '≈ −25 % · RECREACIÓN', 1.0, size=22, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.2, 0.3), amp=14)


# 21. mándaselo a quien le puso alerón a su Tsuru (el sedán con su alerón gigante)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 7.5, -100, 12, ty=0.7), K(0.4, 6.4, -130, 10, ty=0.7), K(d, 6.2, -136, 10, ty=0.7)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.5)
    draw_objects(fr, sedan(giro=-t * 4, ala=1.0, ala_s=1.25))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien le puso', 'sans'), ('alerón a su Tsuru.', 'serif')], 280, seg(u, 0.0, 0.15),
                       size=68)
        pill(img, fx, 540, 1480, 'RECREACIÓN', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-0.3, 'whoosh_suave', 0.6), (U_Z0, 'riser', 0.6), (U_Z1, 'sub', 0.9), (1.9, 'bass', 0.9), (2.0, 'shimmer', 0.5)]),
           dict(desde=1, fn=s_f1, tr='whip', sfx=[(0.0, 'whoosh', 0.7), (0.9, 'thud', 0.8)]),
           dict(desde=2, fn=s_alreves, tr='giro', sfx=[(0.0, 'slap', 0.8), (1.2, 'whoosh', 0.7), (1.6, 'bass', 0.8)]),
           dict(desde=3, fn=s_rapido, tr='deslizar', sfx=[(0.0, 'whoosh_suave', 0.6), (1.2, 'tick', 0.5), (1.4, 'tick', 0.5)]),
           dict(desde=4, fn=s_presion, tr='deslizar_abajo', sfx=[(0.2, 'riser', 0.4), (1.6, 'sub', 0.9)]),
           dict(desde=5, fn=s_150, tr='golpe', sfx=[(0.0, 'riser', 0.6), (0.9, 'bass', 0.9)]),
           dict(desde=6, fn=s_pesa, tr='cubo_izq', sfx=[(0.3, 'chime_a', 0.5), (0.6, 'chime_b', 0.5), (2.2, 'bass', 0.7)]),
           dict(desde=7, fn=s_tunel, tr='zoom', c=(0.5, 0.5), sfx=[(0.0, 'whoosh', 0.8), (1.3, 'riser', 0.6), (2.2, 'sub', 0.8)]),
           dict(desde=8, fn=s_x4, tr='rebanadas', sfx=[(1.0, 'chime_a', 0.5), (2.9, 'chime_c', 0.6), (3.1, 'bass', 0.8)]),
           dict(desde=9, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(0.0, 'bass', 1.0), (0.15, 'sub', 0.9), (0.4, 'digital', 0.5)]),
           dict(desde=10, fn=s_tsuru, tr='glitch', sfx=[(0.6, 'slap', 0.8), (0.8, 'bass', 0.7), (1.9, 'scribble', 0.6)]),
           dict(desde=11, fn=s_50, tr='whip_izq', sfx=[(0.0, 'whoosh_suave', 0.6), (0.8, 'click', 0.6)]),
           dict(desde=12, fn=s_kilo, tr='iris', c=(0.5, 0.45), sfx=[(0.6, 'thud', 0.9), (0.6, 'shimmer', 0.5), (1.6, 'slap', 0.7)]),
           dict(desde=13, fn=s_frena, tr='remolino', sfx=[(0.1, 'slap', 0.8), (1.7, 'digital', 0.4)]),
           dict(desde=14, fn=s_curva, tr='giro', sfx=[(0.3, 'whoosh', 0.6), (1.2, 'scribble', 0.6), (1.4, 'bass', 0.7)]),
           dict(desde=15, fn=s_2026, tr='mosaico', sfx=[(0.15, 'bass', 0.8), (0.5, 'click', 0.6), (1.1, 'click', 0.6), (1.7, 'click', 0.6)]),
           dict(desde=16, fn=s_modos, tr='cubo', sfx=[(0.1, 'whoosh_suave', 0.6), (1.6, 'click', 0.8), (1.9, 'thud', 0.7)]),
           dict(desde=17, fn=s_checo, tr='flash', sfx=[(0.15, 'bass', 0.9), (0.2, 'shimmer', 0.5)]),
           dict(desde=18, fn=s_300, tr='golpe', sfx=[(0.1 + 0.15 * j, 'tick', 0.4) for j in range(12)] + [(2.0, 'bass', 0.9)]),
           dict(desde=19, fn=s_cdmx, tr='wipe', sfx=[(0.1, 'whoosh_suave', 0.5), (1.5, 'chime_b', 0.5)]),
           dict(desde=20, fn=s_cuarta, tr='cristal', palabra='−25%', sfx=[(1.4, 'thud', 0.8)]),
           dict(desde=21, fn=s_compa, tr='push', sfx=[(0.15, 'bass', 0.8)]),
           dict(desde=22, loop=True, tr='zoom')]

if __name__ == '__main__':
    montaje.cli(globals())
