"""Reel diario mar 24-nov-2026 10:00 (propuesto) — «Tu razer no tiene velocidades… tiene una banda.»
La CVT de los side by side: dos poleas en forma de cono y una banda que sube y baja entre sus caras; al arrancar la banda
va abajo en la polea del motor y arriba en la de las llantas (primera); al acelerar unas pesas aprietan la polea y la
banda sube sola, como rampa y no como escalera. Error (segundo gancho): andar en alta en lodo, arena o subiendo despacio:
a vuelta de rueda la banda patina contra el metal, se calienta y se quema (el manual de Polaris pide baja). Dientes de la
banda, el agua que entra a la caja y el Honda Talon, que no trae banda (doble embrague).
Comunidad: riders (la del reel VIRAL del razer). Inicio tipo 7 (macro extremo): empieza pegado a los dientes de la banda,
gigantes y calientes, y la cámara se aleja de golpe hasta la CVT completa con «BANDA» de cristal detrás. El final
(«…tiene una banda») regresa a los dientes (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Fotos reales: Polaris RZR (HJUdall, CC0) y Can-Am Maverick (KarleHorn, CC BY 3.0) en 3D con foto3d.py.
Poleas, banda, pesas, engranes y caja de doble embrague son esquemas marcados «ESQUEMA». Fuentes: guiones/2026-11-24_cvt.txt.
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import foto3d as F3
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import texto, esquema, golpe_k, sacudir, K, camara, tubo

M3 = M.M3
TEMA = 'cvt'
TXT = ['Tu razer no tiene velocidades… tiene una banda.',
       'Una bici de cambios brinca de engrane en engrane;',
       'tu razer nunca brinca.',
       'Junto al motor hay una tapa:',
       'adentro, dos poleas en forma de cono y una banda.',
       'Al arrancar, la banda va abajo en la polea del motor',
       'y arriba en la de las llantas: es tu primera.',
       'Aceleras, unas pesas aprietan la polea',
       'y la banda sube sola, como rampa y no como escalera.',
       'Y aquí está el error:',
       'andar en alta en el lodo, en la arena o subiendo despacio.',
       'A vuelta de rueda, la banda patina contra el metal,',
       'se calienta y se quema.',
       'El manual de Polaris lo dice:',
       'atascado, con remolque o subiéndolo a la troca, siempre en baja.',
       'En baja, el motor da más vueltas por cada vuelta de llanta',
       'y la banda ya no patina.',
       'De cerca, la banda tiene dientes para doblarse;',
       'el calor la deja lisa como vidrio.',
       'Si cruzas un charco hondo, el agua se mete a la caja',
       'y la banda patina hasta que la secas.',
       'Honda, en cambio, no le puso banda al Talon:',
       'usa doble embrague, como un carro de cambios.',
       'Mándaselo a tu compa que ya quemó la banda en la duna.',
       'Y que la meta en baja… porque su razer no tiene velocidades: tiene una banda.']
VOZ = [x.replace('…', '...') for x in TXT]
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_cvt.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-24_cvt_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
ROJO = (255, 60, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
ACERO = (128, 132, 140)
HULE = (38, 38, 42)
LATON = (214, 170, 84)
PLAST = (46, 48, 54)
LODO = (110, 82, 52)
AGUA = (70, 150, 230)
VERDE = (90, 220, 140)

# ------------------------------------------------------------------ fotos reales
FOTOS = os.path.join(HERE, 'img', 'canam')
CRED = {'rzr24': 'FOTO: HJUDALL · CC0 · WIKIMEDIA COMMONS', 'rzr23': 'FOTO: HJUDALL · CC0 · WIKIMEDIA COMMONS',
        'mavs': 'FOTO: KARLEHORN · CC BY 3.0 · WIKIMEDIA COMMONS'}
VEH = {n: F3.preparar(f'{FOTOS}/canam_i_{n}.jpg', n) for n in ('rzr24', 'rzr23', 'mavs')}


def veh(img, fx, n, cx, piso, alto, yaw=0.0, pitch=0.15, t=0.0, alfa=1.0, xray=0.0, dy=0.0, borde=0.55, esc=1.0):
    luz = (-0.65 + 0.55 * math.sin(t * 0.9), -0.62)
    return F3.dibujar(img, VEH[n], cx, piso - alto * 0.5 + dy, alto, yaw=yaw, pitch=pitch, luz=luz, fx=fx, alfa=alfa,
                      reflejo=0.22, borde=borde, piso_y=piso + dy, xray=xray, esc=esc)


def credito(img, txt, y=1872, k=1.0):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((540, y), txt, font=M.font('mono', 19), fill=M.scale_c((150, 150, 158), k), anchor='mm')


# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    if not os.path.exists(WORDS):                       # sin voz todavía: 0.3 s por palabra
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
    """u de la palabra de la frase i que empieza con `palabra` (la n-ésima si se repite)."""
    ws = [montaje._norm(w) for w in VOZ[i].split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


def flecha(img, fx, x0, y0, x1, y1, col, k=1.0, w=8):
    if k <= 0.01:
        return
    x1, y1 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    df.line([(x0, y0), (x1, y1)], fill=M.scale_c(col, 0.6), width=w * 3)
    a = math.atan2(y1 - y0, x1 - x0)
    L = 26 + w
    for s in (-1, 1):
        xa, ya = x1 - L * math.cos(a + s * 0.5), y1 - L * math.sin(a + s * 0.5)
        d.line([(x1, y1), (xa, ya)], fill=col, width=w)
        df.line([(x1, y1), (xa, ya)], fill=M.scale_c(col, 0.6), width=w * 3)


# ------------------------------------------------------------------ la CVT en 3D (ejes de las poleas sobre z)
C1 = np.array([-0.85, 0.95, 0.0])     # polea del motor (la de las pesas)
C2 = np.array([0.85, 0.95, 0.0])      # polea de las llantas
R1O, R2O = 0.5, 0.58                  # radio de las caras
BW = 0.16                             # ancho de la banda
SLOPE = 0.17                          # inclinación de las caras (dz por dr)


def radios(k):
    """k = 0: arranque (banda abajo en la del motor, arriba en la de las llantas); k = 1: alta."""
    return lerp(0.16, 0.44, k), lerp(0.52, 0.25, k)


def camino(r1, r2, n=220):
    """Polilínea cerrada de la banda abierta alrededor de las dos poleas (plano z = 0)."""
    d = C2[0] - C1[0]
    nx = (r1 - r2) / d
    ny = math.sqrt(max(0.0, 1 - nx * nx))
    th = math.atan2(ny, nx)
    pts = []
    a1 = np.linspace(th, 2 * math.pi - th, int(n * 0.55))
    pts += [C1[:2] + r1 * np.array([math.cos(a), math.sin(a)]) for a in a1]
    a2 = np.linspace(-th, th, int(n * 0.45))
    pts += [C2[:2] + r2 * np.array([math.cos(a), math.sin(a)]) for a in a2]
    pts.append(pts[0])
    return np.array(pts)


def _muestreo(poly, s):
    seglen = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seglen)])
    L = cum[-1]
    s = s % L
    i = int(np.searchsorted(cum, s) - 1)
    i = max(0, min(i, len(seglen) - 1))
    f = (s - cum[i]) / max(1e-9, seglen[i])
    p = poly[i] + (poly[i + 1] - poly[i]) * f
    dv = poly[i + 1] - poly[i]
    return p, math.degrees(math.atan2(dv[1], dv[0])), L


def banda(k, t, vel=1.0, calor=0.0, n=46, lisa=0.0, agua=0.0):
    """La banda dentada: n dientes que corren a lo largo del camino. calor 0–1 la pone roja; lisa 0–1 brilla como vidrio."""
    r1, r2 = radios(k)
    poly = camino(r1, r2)
    _, _, L = _muestreo(poly, 0)
    col = M.mixc(HULE, (150, 50, 24), calor)
    out = []
    for j in range(n):
        p, ang, _ = _muestreo(poly, j * L / n + t * vel)
        m = M3.box(L / n * 0.62, 0.075, BW, col, shadow=0, base=False, gloss=0.25 + 0.65 * lisa).tf(rz=ang, t=(p[0], p[1], 0))
        m = named(m, 'banda', rim=0.5 + 0.4 * lisa, gloss=0.25 + 0.65 * lisa)
        if calor > 0.05:
            m.glow = M.scale_c(NARANJA, 0.55 * calor)
        if agua > 0.05 and j % 3 == 0:
            m.glow = M.scale_c(AGUA, 0.5 * agua)
        out.append(m)
    return out


def media_polea(c, r_banda, Rout, lado, ang, col=ACERO, name='cara'):
    """Media polea (cono) de un lado (lado=+1 adelante, −1 atrás) con la banda a r_banda."""
    hz = lambda rho: BW / 2 + (rho - r_banda) * SLOPE
    z0, z1 = max(0.004, hz(0.09)), hz(Rout)
    if lado > 0:
        cone = M3.cyl(0.09, z1 - z0, col, n=30, r2=Rout, y0=z0, shadow=0, gloss=0.85)
        back = M3.cyl(Rout, 0.035, M.scale_c(col, 0.85), n=30, y0=z1, shadow=0, gloss=0.6)
        hub = M3.cyl(0.075, 0.25, (120, 122, 130), n=16, y0=z1, shadow=0, gloss=0.7)
    else:
        cone = M3.cyl(Rout, z1 - z0, col, n=30, r2=0.09, y0=-z1, shadow=0, gloss=0.85)
        back = M3.cyl(Rout, 0.035, M.scale_c(col, 0.85), n=30, y0=-z1 - 0.035, shadow=0, gloss=0.6)
        hub = M3.cyl(0.075, 0.25, (120, 122, 130), n=16, y0=-z1 - 0.25, shadow=0, gloss=0.7)
    ms = [named(m.tf(rx=90).tf(rz=ang, t=tuple(c)), name, rim=0.7, gloss=0.5) for m in (cone, back, hub)]
    for j in range(3):                                   # tornillos que dejan ver el giro
        a = ang * math.pi / 180 + j * 2 * math.pi / 3
        zz = lado * (z1 + 0.03)
        b = M3.box(0.06, 0.06, 0.04, (90, 92, 100), shadow=0, base=False).tf(t=(c[0] + 0.3 * Rout * math.cos(a), c[1] + 0.3 * Rout * math.sin(a), zz))
        ms.append(named(b, name, rim=0.6, gloss=0.7))
    return ms


def pesas(k_rpm, ang):
    """Tres pesas centrífugas en la polea del motor: salen con las vueltas (k_rpm 0–1)."""
    out = []
    rho = 0.12 + 0.2 * k_rpm
    zz = BW / 2 + (R1O - radios(k_rpm)[0]) * SLOPE + 0.09
    for j in range(3):
        a = math.radians(ang) + j * 2 * math.pi / 3
        b = M3.rbox(0.11, 0.07, 0.07, 0.025, LATON, n=3, shadow=0, gloss=0.9, base=False).tf(rz=math.degrees(a), t=(C1[0] + rho * math.cos(a), C1[1] + rho * math.sin(a), zz))
        out.append(named(b, 'pesa', rim=0.9, gloss=0.9, glow=M.scale_c(LATON, 0.25)))
    return out


def cvt(k, t, vel=1.0, calor=0.0, giro=None, lisa=0.0, agua=0.0, con_pesas=False, k_rpm=None, corte=False):
    """corte=True: sin las caras de adelante (vista en corte) para que se vea la banda sobre el cono."""
    r1, r2 = radios(k)
    a1 = (t * 220 * vel) if giro is None else giro
    a2 = a1 * r1 / r2
    ms = []
    for lado in ((-1,) if corte else (1, -1)):
        ms += media_polea(C1, r1, R1O, lado, a1, name='cara')
        ms += media_polea(C2, r2, R2O, lado, a2, name='cara')
    ms += banda(k, t, vel=vel * 1.7, calor=calor, lisa=lisa, agua=agua)
    if con_pesas:
        ms += pesas(k if k_rpm is None else k_rpm, a1)
    return ms


def tapa(alfa=1.0):
    m = named(M3.rbox(2.95, 0.62, 1.55, 0.42, (74, 76, 84), n=5, shadow=0, gloss=0.45, base=False), 'tapa', rim=0.8, gloss=0.45)
    m = m.tf(rx=90, t=(0, 0.95, 0.0))
    out = [m]
    for x in (-1.25, -0.4, 0.4, 1.25):
        for y in (0.3, 1.6):
            out.append(named(M3.cyl(0.045, 0.06, (150, 152, 160), n=10, shadow=0, gloss=0.8).tf(rx=90, t=(x, y, 0.31)), 'tapa', rim=0.6))
    return out


def base_cvt(fr, u, claves, t, floor='lines', cy=0.52, beam=0.4):
    fr2 = Frame(camara(u, claves, cy=cy))
    space(fr2, t, floor=floor, floor_a=0.7, bokeh=0.9, beam=beam)
    return fr2


def etiqueta3(img, fx, fr, p, txt, k, dx=0, dy=-120, col=AZULC, size=28):
    x, y, _ = fr.cam.p1(tuple(p))
    if k > 0.01:
        ImageDraw.Draw(img).line([(x, y), (x + dx * 0.8, y + dy * 0.8)], fill=M.scale_c(col, 0.8 * k), width=3)
    pill(img, fx, x + dx, y + dy, txt, eout(k), size=size, border=col)


# ================================================================== escenas
# 0. gancho, inicio tipo 7 (macro extremo): los dientes de la banda gigantes y calientes; la cámara se aleja de golpe
UX = 0.0


def s_gancho(t, fi, u, d):
    pose = P.cam_rapida(u, [K(-4.5, 0.42, 38, 26, tx=-0.25, ty=1.27, tz=0.0),
                            K(-2.2, 0.36, 14, 18, tx=0.05, ty=1.3, tz=0.0),
                            K(UX, 0.36, 14, 18, tx=0.05, ty=1.3, tz=0.0),
                            K(UX + 0.3, 4.4, -24, 12, tx=0.0, ty=0.95), K(3.0, 4.2, -30, 12, tx=0.0, ty=0.95)])
    fr = Frame(Cam(target=(pose['tx'], pose['ty'], pose['tz']), dist=pose['dist'], yaw=pose['yaw'], pitch=pose['pitch'], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.7 * seg(u, UX, UX + 0.3), bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'BANDA', u, t0=-2.6, cy=0.38, entrada='golpe')
    calor = 0.5 * (1 - seg(u, UX + 0.2, UX + 0.9)) + 0.2 + 0.08 * math.sin(t * 6)
    draw_objects(fr, cvt(0.35, t, vel=1.0, calor=calor, corte=True))
    fantasma(fr, 0.35, a=0.5 * seg(u, UX + 0.2, UX + 0.5))

    def ui(img, fx):
        kicker(img, 'TRANSMISIÓN CVT · POR DENTRO', 140, seg(u, UX + 0.3, UX + 0.6), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu razer no tiene velocidades…', 'sans'), ('tiene una banda.', 'serif')], 190,
                       seg(u, UX + 0.3, UX + 0.45), size=70)
        if u < UX + 0.2:
            pill(img, fx, 540, 1380, 'x12 · DIENTES DE LA BANDA', 1.0, size=24, border=NARANJA, dot=False)
        esquema(img, fx, seg(u, UX + 0.4, UX + 0.7), y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, UX + 0.45, 0.35), amp=22)


# 1. caso 1: la bici de cambios brinca de engrane en engrane (escalones)
RAD_BICI = [0.56, 0.49, 0.43, 0.37, 0.32, 0.27, 0.23]


def s_bici(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.2, 70, 14, ty=0.95), K(0.35, 2.8, 32, 8, ty=0.95), K(5, 2.7, 26, 8, ty=0.95)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)
    e = P.entrada(u, -0.25, 0.3, 'gira')
    paso = min(len(RAD_BICI) - 1, max(0, int((u - 0.2) / 0.38)))
    ang = t * 300
    ms = []
    for j, r in enumerate(RAD_BICI):
        col = ACERO if j != paso else (196, 200, 208)
        g = M3.cyl(r, 0.035, col, n=32, shadow=0, gloss=0.6, y0=-0.0175).tf(rx=90, rz=ang, t=(0, 0.95, -0.2 + j * 0.065))
        ms.append(named(g, 'engrane', rim=0.8, gloss=0.6))
    ms = P.tfk(ms, s=max(0.05, e['escala']), ry=math.degrees(e['giro']) * 0.3, t=(0, 0.95 * (1 - max(0.05, e['escala'])), 0))
    draw_objects(fr, ms)
    r = RAD_BICI[paso]
    z = -0.2 + paso * 0.065
    for j in range(16):                                   # dientes: marcas que giran
        a = math.radians(ang) + j * 2 * math.pi / 16
        p = (r * math.cos(a), 0.95 + r * math.sin(a), z + 0.02)
        dot3(fr, p, r=2.5, col=WHITE, a=0.6, glow=0.4)
    line3(fr, [(-2.2, 0.95 + r + 0.02, z), (0, 0.95 + r + 0.02, z)], col=(200, 200, 210), w=7, a=0.9, glow=0.2)
    line3(fr, [(-2.2, 0.95 - r - 0.02, z), (0, 0.95 - r - 0.02, z)], col=(200, 200, 210), w=7, a=0.9, glow=0.2)

    def ui(img, fx):
        kicker(img, 'CASO 1 · BICI DE CAMBIOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        d_ = ImageDraw.Draw(img)
        x0, y0 = 170, 1330
        n = paso + 1
        pts = [(x0, y0)]
        for j in range(n):
            pts += [(x0 + j * 105, y0 - j * 42 - 42), (x0 + (j + 1) * 105, y0 - j * 42 - 42)]
        d_.line(pts, fill=WHITE, width=7)
        ImageDraw.Draw(fx).line(pts, fill=M.scale_c(WHITE, 0.4), width=14)
        texto(img, fx, 540, 1400, f'CAMBIO {n} DE 7 · BRINCA', 34, AMARILLO, seg(u, 0.2, 0.4), f='mono', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2 + 0.38 * paso, 0.18) if paso > 0 else 0.0, amp=8)


# 2. caso 2: tu razer nunca brinca (la foto real con su línea que sube como rampa)
def s_nunca(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.85, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.28, 'desliza')
    pose = P.cam_rapida(u, [(-0.3, dict(yaw=-0.9, al=560)), (0.45, dict(yaw=0.15, al=640)), (5, dict(yaw=0.4, al=660))])

    def ui(img, fx):
        M.cristal(img, fx, 'RAMPA', u, t0=0.25, cy=0.27, entrada='sube')
        veh(img, fx, 'rzr24', 540 - e['dy'] * 240, 1180, pose['al'], yaw=pose['yaw'], pitch=0.14, t=t)
        k = eout(seg(u, 0.1, 1.3))
        d_ = ImageDraw.Draw(img)
        x0, y0, x1, y1 = 170, 1380, 170 + 740 * k, 1380 - 300 * k
        d_.line([(x0, y0), (x1, y1)], fill=CYAN, width=8)
        ImageDraw.Draw(fx).line([(x0, y0), (x1, y1)], fill=M.scale_c(CYAN, 0.6), width=20)
        texto(img, fx, 540, 1440, 'CVT · SIN SALTOS', 36, CYAN, seg(u, 0.3, 0.5), f='mono', glow=0.4)
        credito(img, CRED['rzr24'])
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. junto al motor hay una tapa (la tapa de la CVT cae y rebota; la cámara se acerca a ella)
def s_tapa(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 5.2, -40, 16), K(0.3, 4.2, -12, 8), K(5, 3.9, -6, 6)], t, floor='lines')
    e = P.entrada(u, -0.2, 0.35, 'cae')
    draw_objects(fr, P.tfk(tapa(), t=(0, max(0.0, -e['dy']) * 0.6, 0)))

    def ui(img, fx):
        kicker(img, 'A UN LADO DEL MOTOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        etiqueta3(img, fx, fr, (0.6, 1.4, 0.4), 'TAPA DE LA CVT', seg(u, 0.4, 0.7), dx=120, dy=-170)
        doodle_circle(img, fx, 540, 900, 360, 230, t, k=seg(u, 0.6, 1.0), col=WHITE, seed=3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.12, 0.3), amp=16)


# 4. adentro: dos poleas en forma de cono y una banda (la tapa se vuelve cristal; «CVT» de cristal detrás)
def s_adentro(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 3.6, -8, 6), K(0.45, 4.1, -48, 14), K(5, 4.0, -56, 14)], t, floor='lines')
    M.cristal(fr.base, fr.fx, 'CVT', u, t0=-0.2, cy=0.34, entrada='zoom')
    draw_objects(fr, tapa() + cvt(0.4, t), xray=min(1.0, 0.4 + seg(u, -0.2, 0.3)), keep=('cara', 'banda'))
    up = Wp(4, 'poleas') - 0.1
    ub = Wp(4, 'banda') - 0.1

    def ui(img, fx):
        etiqueta3(img, fx, fr, (C1[0], C1[1] + R1O, 0.1), 'POLEA DEL MOTOR', seg(u, up, up + 0.3), dx=-60, dy=-200)
        etiqueta3(img, fx, fr, (C2[0], C2[1] + R2O, 0.1), 'POLEA DE LAS LLANTAS', seg(u, up + 0.3, up + 0.6), dx=40, dy=-120)
        etiqueta3(img, fx, fr, (0.0, C1[1] - 0.4, 0.0), 'BANDA', seg(u, ub, ub + 0.3), dx=0, dy=210, col=NARANJA)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


def fantasma(fr, k, a=0.5):
    """Contorno de las caras de adelante (quitadas en el corte), en line-art."""
    r1, r2 = radios(k)
    for c, R, r in ((C1, R1O, r1), (C2, R2O, r2)):
        z = BW / 2 + (R - r) * SLOPE
        th = np.linspace(0, 2 * math.pi, 64)
        line3(fr, [(c[0] + R * math.cos(q), c[1] + R * math.sin(q), z) for q in th], col=AZULC, w=2.0, a=a, glow=0.6)
        line3(fr, [(c[0] + 0.09 * math.cos(q), c[1] + 0.09 * math.sin(q), BW / 2) for q in th], col=AZULC, w=1.6, a=a * 0.6, glow=0.4)


def vista_lado(fr, k, t, vel=1.0, calor=0.0, ver_pesas=False, k_rpm=None, lisa=0.0, agua=0.0, giro=None):
    draw_objects(fr, cvt(k, t, vel=vel, calor=calor, con_pesas=ver_pesas, k_rpm=k_rpm, lisa=lisa, agua=agua, giro=giro, corte=True))
    fantasma(fr, k)


# 5. al arrancar la banda va abajo en la polea del motor (vista de frente a la polea abierta)
def s_abajo(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 2.8, 70, 34, tx=C1[0], ty=C1[1]), K(0.4, 2.2, 28, 16, tx=C1[0] + 0.2, ty=C1[1]),
                            K(5, 2.1, 22, 14, tx=C1[0] + 0.2, ty=C1[1])], t, floor='dots')
    vista_lado(fr, 0.0, t, vel=0.6)
    r1, _ = radios(0.0)

    def ui(img, fx):
        kicker(img, 'AL ARRANCAR · POLEA DEL MOTOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        x, y, _ = fr.cam.p1(tuple(C1))
        x2, y2, _ = fr.cam.p1((C1[0], C1[1] + r1, 0))
        flecha(img, fx, x + 300, y2, x + 60, y2, AMARILLO, k=eout(seg(u, 0.3, 0.6)), w=8)
        pill(img, fx, x + 300, y2 - 70, 'ABIERTA · BANDA ABAJO', eout(seg(u, 0.4, 0.7)), size=28, border=AMARILLO, dot=False)
        doodle_circle(img, fx, x, y, 120, 120, t, k=seg(u, 0.6, 0.9), col=WHITE, seed=4)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. y arriba en la de las llantas: es tu primera («1.ª» que golpea; «PRIMERA» de cristal)
def s_primera(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 2.6, -64, 26, tx=C2[0], ty=C2[1]), K(0.35, 2.5, -26, 12, tx=C2[0] - 0.25, ty=C2[1]),
                            K(5, 2.55, -32, 12, tx=C2[0] - 0.25, ty=C2[1])], t, floor='dots')
    up = Wp(6, 'primera') - 0.1
    M.cristal(fr.base, fr.fx, 'PRIMERA', u, t0=up - 0.1, cy=0.3, entrada='golpe')
    vista_lado(fr, 0.0, t, vel=0.6)
    _, r2 = radios(0.0)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((C2[0], C2[1] + r2, 0))
        flecha(img, fx, x - 280, y - 40, x - 40, y, AMARILLO, k=eout(seg(u, 0.1, 0.4)), w=8)
        pill(img, fx, x - 280, y - 110, 'CERRADA · BANDA ARRIBA', eout(seg(u, 0.2, 0.5)), size=28, border=AMARILLO, dot=False)
        P.numero_golpe(img, fx, '1.ª', 1220, seg(u, up, up + 0.18), size=230, col=AMARILLO)
        texto(img, fx, 540, 1390, 'POCA VELOCIDAD · MUCHA FUERZA', 32, WHITE, seg(u, up + 0.2, up + 0.4), f='mono', glow=0.2)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.18, 0.3), amp=18)


# 7. aceleras: unas pesas aprietan la polea (rayos X de la polea del motor; las pesas salen con las vueltas)
def s_pesas(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 2.0, 120, 18, tx=C1[0], ty=C1[1], tz=0.1), K(0.4, 1.9, 150, 14, tx=C1[0], ty=C1[1], tz=0.1),
                            K(5, 1.85, 158, 12, tx=C1[0], ty=C1[1], tz=0.1)], t, floor='dots')
    ua = Wp(7, 'aceleras')
    kr = P.eout4(seg(u, ua + 0.2, ua + 1.8))
    M.cristal(fr.base, fr.fx, 'PESAS', u, t0=0.0, cy=0.3, entrada='sube')
    draw_objects(fr, cvt(0.25 * kr, t, vel=0.6 + 1.4 * kr, con_pesas=True, k_rpm=kr), xray=0.7, keep=('pesa', 'banda'))
    rpm = int(1500 + 6000 * kr)

    def ui(img, fx):
        kicker(img, 'RAYOS X · POLEA DEL MOTOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1280, f'{rpm:,} RPM'.replace(',', ' '), 80, WHITE, seg(u, 0.0, 0.2), f='mono', glow=0.4)
        etiqueta3(img, fx, fr, (C1[0], C1[1] + 0.3, 0.2), 'PESAS QUE SALEN CON LAS VUELTAS', seg(u, 0.5, 0.8), dx=0, dy=-260, col=LATON)
        esquema(img, fx, 1.0, y=1440, txt='ESQUEMA · RPM DE EJEMPLO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. la banda sube sola: como rampa y no como escalera (vista lateral + gráfica escalera contra rampa)
def s_rampa(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 4.4, 8, 30, ty=1.2), K(0.4, 4.6, 0, 4, ty=1.35), K(5, 4.6, -4, 4, ty=1.35)], t, floor=None, cy=0.42)
    kk = P.eout4(seg(u, 0.0, 2.2))
    vista_lado(fr, kk, t, vel=1.0 + kk)

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        x0, y0, w, h = 150, 1380, 780, 300
        d_.line([(x0, y0), (x0 + w, y0)], fill=(120, 120, 128), width=3)
        d_.line([(x0, y0), (x0, y0 - h)], fill=(120, 120, 128), width=3)
        ke = seg(u, Wp(8, 'escalera') - 0.4, Wp(8, 'escalera') + 0.6)
        if ke > 0:
            pts = [(x0, y0)]
            for j in range(5):
                pts += [(x0 + j * w / 5, y0 - (j + 1) * h / 5), (x0 + (j + 1) * w / 5, y0 - (j + 1) * h / 5)]
            n = max(2, int(len(pts) * ke))
            d_.line(pts[:n], fill=(200, 200, 210), width=5)
            texto(img, fx, x0 + w - 10, y0 - h - 30, 'ESCALERA', 28, (200, 200, 210), ke, f='mono', glow=0.1, anchor='rm')
        kr = eout(seg(u, Wp(8, 'rampa') - 0.3, Wp(8, 'rampa') + 0.5))
        if kr > 0:
            d_.line([(x0, y0), (x0 + w * kr, y0 - h * kr)], fill=CYAN, width=9)
            df.line([(x0, y0), (x0 + w * kr, y0 - h * kr)], fill=M.scale_c(CYAN, 0.6), width=22)
            texto(img, fx, x0 + 20, y0 - h - 30, 'RAMPA = CVT', 30, CYAN, kr, f='mono', glow=0.4, anchor='lm')
        kicker(img, 'LA BANDA SUBE SOLA', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. SEGUNDO GANCHO: y aquí está el error (la banda se pone roja; «ERROR» de cristal; título que se estrella)
def s_error(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 3.0, 40, 10, ty=0.95), K(0.25, 2.4, 70, 12, ty=0.95), K(5, 2.3, 76, 12, ty=0.95)], t, floor='lines')
    M.cristal(fr.base, fr.fx, 'ERROR', u, t0=-0.15, cy=0.33, entrada='golpe')
    vista_lado(fr, 0.1, t, vel=0.4, calor=0.8)

    def ui(img, fx):
        kicker(img, 'EL ERROR QUE QUEMA LA BANDA', 150, seg(u, -0.1, 0.1), col=(255, 140, 130))
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 200, seg(u, 0.05, 0.2), size=96, col=WHITE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.4), amp=24)


# 10. andar en alta en lodo, arena o subiendo despacio (el Maverick real; palanca en H y 3 pastillas)
def s_alta(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8, beam=0.4)
    pose = P.cam_rapida(u, [(-0.3, dict(yaw=0.8, al=520)), (0.4, dict(yaw=-0.1, al=600)), (5, dict(yaw=-0.3, al=610))])
    uh = Wp(10, 'alta') - 0.1
    temblor = 6 * math.sin(t * 40) * seg(u, 0.4, 0.8)

    def ui(img, fx):
        veh(img, fx, 'mavs', 540 + temblor, 1060, pose['al'], yaw=pose['yaw'], pitch=0.12, t=t)
        d_ = ImageDraw.Draw(img)
        for j in range(26):                                    # lodo y arena que salpican de las llantas
            ph = (t * 1.3 + j * 0.37) % 1.0
            x = 300 + (j * 97) % 520 + 60 * math.sin(j)
            y = 1060 - 160 * math.sin(ph * math.pi) - 10
            r = 6 + (j % 4) * 3
            c = LODO if j % 2 else (214, 190, 140)
            d_.ellipse((x - r, y - r, x + r, y + r), fill=M.scale_c(c, seg(u, 0.4, 0.7)))
        # palanca: H en rojo
        x, y = 860, 420
        kh = eout(seg(u, uh, uh + 0.25))
        if kh > 0:
            d_.rounded_rectangle((x - 80, y - 110, x + 80, y + 110), radius=22, outline=M.scale_c(WHITE, kh), width=4)
            for j, L in enumerate(('H', 'L')):
                col = ROJO if L == 'H' else (120, 120, 128)
                texto(img, fx, x, y - 50 + j * 100, L, 70, col, kh, f='sansx', glow=0.5 if L == 'H' else 0.0)
        for j, (w, cc) in enumerate((('LODO', LODO), ('ARENA', (214, 190, 140)), ('SUBIENDO DESPACIO', AMARILLO))):
            uu = Wp(10, w.split()[0].lower()) - 0.1
            pill(img, fx, 540, 1230 + j * 70, w, eout(seg(u, uu, uu + 0.25)), size=30, border=cc, dot=False)
        credito(img, CRED['mavs'])
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. a vuelta de rueda la banda patina contra el metal (polea que gira rápido, banda que casi no avanza; chispas)
def s_patina(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 1.2, -30, 20, tx=C1[0] + 0.12, ty=C1[1] + 0.12, tz=0.05),
                            K(0.35, 1.0, 20, 6, tx=C1[0] + 0.12, ty=C1[1] + 0.14, tz=0.05),
                            K(5, 0.95, 26, 6, tx=C1[0] + 0.12, ty=C1[1] + 0.14, tz=0.05)], t, floor=None)
    calor = 0.25 + 0.4 * seg(u, 0.4, 2.5)
    draw_objects(fr, cvt(0.05, t * 0.15, giro=t * 900, calor=calor, corte=True))
    for j in range(14):                                       # chispas donde se talla
        ph = (t * 2.1 + j * 0.173) % 1.0
        a = math.radians(70 + 40 * math.sin(j * 2.3))
        r0 = radios(0.05)[0]
        p0 = C1 + np.array([r0 * math.cos(a), r0 * math.sin(a), 0.09])
        p1 = p0 + np.array([0.25 * ph * math.cos(a + 0.6), 0.25 * ph * math.sin(a + 0.6) - 0.1 * ph * ph, 0.05])
        line3(fr, [p0 + (p1 - p0) * 0.7, p1], col=NARANJA, w=2.5, a=(1 - ph) * seg(u, 0.2, 0.5), glow=1.2)

    def ui(img, fx):
        rec_frame(img, t, k=seg(u, -0.1, 0.1), zoom_label='x1.8' if u > 1.0 else 'x1.3')
        kicker(img, 'A VUELTA DE RUEDA · 5 A 11 KM/H', 260, seg(u, 0.0, 0.3), col=(255, 140, 130))
        pill(img, fx, 540, 1350, 'LA POLEA GIRA · LA BANDA SE TALLA', eout(seg(u, 0.5, 0.8)), size=28, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 12. se calienta y se quema (la banda al rojo, humo y termómetro; «QUEMA» de cristal)
def s_quema(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 3.0, 20, 30, ty=1.0), K(0.3, 3.4, -30, 12, ty=1.0), K(5, 3.3, -36, 12, ty=1.0)], t, floor='lines')
    uq = Wp(12, 'quema') - 0.1
    M.cristal(fr.base, fr.fx, 'QUEMA', u, t0=uq - 0.05, cy=0.3, entrada='zoom')
    calor = 0.6 + 0.4 * seg(u, 0.0, uq)
    roto = u > uq + 0.25
    ms = cvt(0.1, t * (0.2 if roto else 0.5), calor=calor, corte=True)
    if roto:                                               # la banda se revienta: la mitad sale volando
        bb = [m for m in ms if m.name == 'banda']
        rest = [m for m in ms if m.name != 'banda']
        kk = P.eout4(seg(u, uq + 0.25, uq + 0.9))
        ms = rest + P.despiece(bb, kk, centro=(0, 0.95, 0), fuerza=0.9, giro=1.2)
    draw_objects(fr, ms)
    for j in range(10):                                    # humo
        ph = (t * 0.6 + j * 0.1) % 1.0
        x = -0.9 + j * 0.2 + 0.1 * math.sin(t * 2 + j)
        line3(fr, [(x, 1.4 + ph * 1.2, 0.0), (x + 0.08 * math.sin(t * 3 + j), 1.55 + ph * 1.3, 0.0)],
              col=(150, 150, 156), w=10 * (1 - ph) + 2, a=0.35 * (1 - ph) * seg(u, 0.1, 0.5), glow=0.0)

    def ui(img, fx):
        P.termometro(img, fx, 160, 1380, 330, 0.4 + 0.55 * eout(seg(u, 0.0, uq)), 'CALIENTE', k=seg(u, -0.1, 0.15), col=NARANJA)
        if roto:
            P.titulo_golpe(img, fx, [('¡Se truena!', 'sans')], 1220, seg(u, uq + 0.25, uq + 0.4), size=80, col=ROJO)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uq + 0.25, 0.45), amp=26)


def hoja_manual(img, fx, k, t, cx=540, cy=760, w=740):
    """Hoja del manual (ilustración con la tabla traducida) que cae y se balancea."""
    if k <= 0.01:
        return
    h = int(w * 1.08)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=14, fill=(244, 242, 236, 255))
    dl.rectangle((0, 0, w, 120), fill=(30, 30, 34, 255))
    dl.text((40, 60), 'BANDA GASTADA / QUEMADA', font=M.font('sansx', 44), fill=(250, 250, 250, 255), anchor='lm')
    filas = [('Atascado en lodo o nieve', 'BAJA'), ('Jalar o empujar despacio', 'SOLO BAJA'),
             ('Subirlo a una troca o remolque', 'BAJA'), ('Arrancar en subida', 'BAJA'),
             ('Andar a 5–11 km/h', 'MÁS RÁPIDO O BAJA'), ('Agua en la CVT', 'SECARLA')]
    for j, (a, b) in enumerate(filas):
        y = 170 + j * 100
        dl.line([(30, y + 70), (w - 30, y + 70)], fill=(200, 198, 190, 255), width=2)
        dl.text((40, y + 30), a, font=M.font('sanss', 34), fill=(30, 30, 34, 255), anchor='lm')
        dl.text((w - 40, y + 30), b, font=M.font('sansx', 32), fill=(200, 40, 30, 255), anchor='rm')
    drop = eout(clamp(k * 1.5), 3)
    tt = max(0.0, k - 0.65)
    ang = -10 * (1 - drop) + 5.0 * math.exp(-5 * tt) * math.cos(12 * tt) * (1 if k > 0.65 else 0) + 2
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    y = cy - 700 * (1 - drop)
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 160), (0, 0), lay.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    img.paste(sh, (int(cx - lay.width / 2) + 16, int(y - lay.height / 2) + 24), sh)
    img.paste(lay, (int(cx - lay.width / 2), int(y - lay.height / 2)), lay)


# 13. el manual de Polaris lo dice (cae la hoja con la tabla traducida)
def s_manual(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, -30, 30), K(0.4, 5.4, -6, 22), K(5, 5.3, -2, 22)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.6)

    def ui(img, fx):
        kicker(img, 'MANUAL DE POLARIS · TRADUCCIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        hoja_manual(img, fx, seg(u, -0.15, 0.55), t)
        if u > 0.6:
            doodle_circle(img, fx, 830, 400, 170, 70, t, k=seg(u, 0.7, 1.0), col=ROJO, seed=5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.55, 0.3), amp=12)


# 14. atascado, con remolque o subiéndolo a la troca: siempre en baja (3 íconos y la «L» que se clava; «BAJA» de cristal)
def icono(img, fx, kind, x, y, k, t):
    if k <= 0.01:
        return
    d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    c = M.scale_c(WHITE, k)
    s = P.resorte(k)
    if kind == 'lodo':
        d_.ellipse((x - 70 * s, y - 70 * s, x + 70 * s, y + 70 * s), outline=c, width=6)
        d_.chord((x - 110 * s, y + 10 * s, x + 110 * s, y + 110 * s), 180, 360, fill=M.scale_c(LODO, k))
    elif kind == 'remolque':
        d_.rectangle((x - 110 * s, y - 40 * s, x + 30 * s, y + 30 * s), outline=c, width=6)
        d_.line([(x + 30 * s, y + 10 * s), (x + 100 * s, y + 10 * s)], fill=c, width=6)
        for xx in (x - 70 * s, x - 10 * s):
            d_.ellipse((xx - 22 * s, y + 20 * s, xx + 22 * s, y + 64 * s), outline=c, width=6)
    else:  # rampa a la troca
        d_.line([(x - 120 * s, y + 60 * s), (x + 40 * s, y - 30 * s)], fill=c, width=8)
        d_.rectangle((x + 40 * s, y - 60 * s, x + 130 * s, y + 60 * s), outline=c, width=6)
    df.ellipse((x - 120, y - 90, x + 120, y + 90), fill=M.scale_c(CYAN, 0.06 * k))


def s_baja(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 20, 20), K(0.4, 5.4, 4, 14), K(5, 5.3, 0, 14)]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.4)
    ub = Wp(14, 'baja') - 0.1
    M.cristal(fr.base, fr.fx, 'BAJA', u, t0=ub - 0.05, cy=0.62, entrada='golpe')

    def ui(img, fx):
        for j, (kind, w) in enumerate((('lodo', 'atascado'), ('remolque', 'remolque'), ('troca', 'troca'))):
            uu = Wp(14, w) - 0.1
            x = 200 + j * 340
            icono(img, fx, kind, x, 470, seg(u, uu, uu + 0.25), t)
            texto(img, fx, x, 620, w.upper(), 32, WHITE, seg(u, uu + 0.1, uu + 0.3), f='mono', glow=0.2)
        kl = seg(u, ub, ub + 0.15)
        if kl > 0:
            P.numero_golpe(img, fx, 'L', 1000, kl, size=300, col=VERDE)
            texto(img, fx, 540, 1250, 'SIEMPRE EN BAJA', 52, VERDE, seg(u, ub + 0.15, ub + 0.35), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.15, 0.35), amp=20)


# 15. en baja el motor da más vueltas por cada vuelta de llanta (engrane chico contra grande, contadores)
def engrane(r, n_dientes, col, ang, c, z=0.0, h=0.12, name='engrane'):
    ms = [named(M3.cyl(r, h, col, n=40, shadow=0, gloss=0.8, y0=-h / 2).tf(rx=90, rz=ang, t=(c[0], c[1], z)), name, rim=0.8, gloss=0.8)]
    for j in range(n_dientes):
        a = math.radians(ang) + j * 2 * math.pi / n_dientes
        b = M3.box(0.08, 0.07, h, col, shadow=0, base=False).tf(rz=math.degrees(a), t=(c[0] + (r + 0.03) * math.cos(a), c[1] + (r + 0.03) * math.sin(a), z))
        ms.append(named(b, name, rim=0.7, gloss=0.8))
    m = M3.box(r * 0.9, 0.05, 0.02, ROJO, shadow=0, base=False).tf(rz=ang, t=(c[0] + r * 0.45 * math.cos(math.radians(ang)), c[1] + r * 0.45 * math.sin(math.radians(ang)), z + h / 2 + 0.012))
    ms.append(named(m, 'marca', glow=M.scale_c(ROJO, 0.5)))
    return ms


def s_vueltas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.8, 50, 20, ty=0.95), K(0.35, 3.3, 10, 6, ty=0.95), K(5, 3.25, 4, 6, ty=0.95)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.3)
    e = P.entrada(u, -0.25, 0.3, 'pop')
    a = u * 360 * 0.9
    r1, r2 = 0.32, 0.96
    ms = engrane(r1, 10, ACERO, a, (-1.0, 1.3)) + engrane(r2, 30, (150, 154, 162), -a * r1 / r2 + 6, (-1.0 + r1 + r2 + 0.06, 1.3))
    draw_objects(fr, P.tfk(ms, s=max(0.05, e['escala']), t=(0.25, 0, 0)))
    vm, vl = max(0, u) * 0.9, max(0, u) * 0.9 * r1 / r2

    def ui(img, fx):
        kicker(img, 'EN BAJA · REDUCCIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 300, 1260, f'MOTOR {vm:.1f}', 46, AMARILLO, seg(u, 0.1, 0.3), f='mono', glow=0.3)
        texto(img, fx, 790, 1260, f'LLANTA {vl:.1f}', 46, CYAN, seg(u, 0.1, 0.3), f='mono', glow=0.3)
        texto(img, fx, 540, 1330, 'VUELTAS', 28, GRIS, seg(u, 0.1, 0.3), f='mono', glow=0.0)
        esquema(img, fx, 1.0, y=1420, txt='ESQUEMA · EJEMPLO 3 A 1')
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. y la banda ya no patina (banda que agarra de lleno, cian; palomita)
def s_agarra(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 3.0, -70, 20, ty=0.95), K(0.3, 3.6, -20, 8, ty=0.95), K(5, 3.6, -14, 8, ty=0.95)], t, floor='lines')
    draw_objects(fr, cvt(0.3, t, vel=1.4, corte=True))
    fantasma(fr, 0.3, a=0.4)
    r1, r2 = radios(0.3)
    poly = camino(r1, r2, n=120)
    line3(fr, [(p[0], p[1], BW / 2 + 0.02) for p in poly], col=CYAN, w=3, a=0.9 * seg(u, 0.1, 0.5), glow=1.1, frac=seg(u, 0.1, 0.9))

    def ui(img, fx):
        pill(img, fx, 540, 1280, '✓ LA BANDA AGARRA', eout(seg(u, 0.3, 0.6)), size=40, border=VERDE, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. de cerca, la banda tiene dientes para doblarse (macro con zoom digital x1.0 → x1.3 → x1.8)
def s_dientes(t, fi, u, d):
    z = 1.0 if u < 0.6 else (1.3 if u < 1.3 else 1.8)
    fr = base_cvt(None, u, [K(-0.3, 1.5 / 1.0, -10, 6, tx=C2[0] - 0.4, ty=C2[1] + 0.4, tz=0.05),
                            K(0.6, 1.5 / 1.3, -4, 4, tx=C2[0] - 0.35, ty=C2[1] + 0.42, tz=0.05),
                            K(1.3, 1.5 / 1.8, 2, 2, tx=C2[0] - 0.3, ty=C2[1] + 0.45, tz=0.05),
                            K(5, 1.5 / 1.8, 4, 2, tx=C2[0] - 0.3, ty=C2[1] + 0.45, tz=0.05)], t, floor=None)
    draw_objects(fr, cvt(0.55, t * 0.3, corte=True))

    def ui(img, fx):
        rec_frame(img, t, k=1.0, zoom_label=f'x{z:.1f}')
        pill(img, fx, 540, 1280, 'DIENTES = SE DOBLA SIN ROMPERSE', eout(seg(u, 0.4, 0.7)), size=28, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. el calor la deja lisa como vidrio (los dientes se ponen brillosos; antes/después)
def s_vidrio(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 1.1, 30, 10, tx=C2[0] - 0.3, ty=C2[1] + 0.4, tz=0.05),
                            K(0.35, 0.95, 4, 4, tx=C2[0] - 0.3, ty=C2[1] + 0.45, tz=0.05),
                            K(5, 0.92, 0, 4, tx=C2[0] - 0.3, ty=C2[1] + 0.45, tz=0.05)], t, floor=None)
    kl = seg(u, 0.2, 1.2)
    draw_objects(fr, cvt(0.55, t * 0.3, lisa=kl, calor=0.3 * kl, corte=True))

    def ui(img, fx):
        kicker(img, 'BANDA «CRISTALIZADA»', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1280, 'LISA = YA NO AGARRA', eout(seg(u, 0.8, 1.1)), size=32, border=ROJO, dot=False)
        if kl > 0.5:
            for j in range(3):
                x, y = 380 + j * 150, 760 + 40 * j
                ph = (t * 1.5 + j * 0.3) % 1.0
                ImageDraw.Draw(fx).line([(x - 30 * ph, y - 30 * ph), (x + 30 * ph, y + 30 * ph)], fill=M.scale_c(WHITE, 0.8 * (1 - ph)), width=6)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. si cruzas un charco hondo, el agua se mete a la caja (el RZR real con el agua que sube; «AGUA» de cristal)
def s_charco(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8, beam=0.4)
    pose = P.cam_rapida(u, [(-0.3, dict(yaw=-0.7, al=560)), (0.4, dict(yaw=0.2, al=620)), (5, dict(yaw=0.35, al=640))])
    ua = Wp(19, 'agua') - 0.1
    nivel = 0.35 * eout(seg(u, 0.1, ua + 0.6))

    def ui(img, fx):
        M.cristal(img, fx, 'AGUA', u, t0=ua - 0.1, cy=0.27, entrada='zoom')
        r = veh(img, fx, 'rzr23', 540, 1180, pose['al'], yaw=pose['yaw'], pitch=0.14, t=t, dy=10 * math.sin(t * 5))
        if r:
            x0, y0, w, h = r
            yw = int(y0 + h * (1 - nivel))
            ov = Image.new('RGB', img.size, AGUA)
            m = Image.new('L', img.size, 0)
            dm = ImageDraw.Draw(m)
            pts = [(0, yw + 8 * math.sin(t * 4))] + [(x, yw + 10 * math.sin(t * 4 + x * 0.02)) for x in range(0, 1081, 40)] + [(1080, 1920), (0, 1920)]
            dm.polygon(pts, fill=120)
            img.paste(ov, (0, 0), m)
            ImageDraw.Draw(fx).line(pts[1:-2], fill=M.scale_c(AGUA, 0.7), width=6)
            etiqueta3_2d(img, fx, x0 + w * 0.42, y0 + h * 0.55, 'CAJA DE LA CVT', seg(u, ua, ua + 0.3))
        credito(img, CRED['rzr23'])
    fr.ui.append(ui)
    return finish(fr, fi)


def etiqueta3_2d(img, fx, x, y, txt, k, dy=-260, col=AZULC):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).line([(x, y), (x, y + dy * 0.8)], fill=M.scale_c(col, 0.8 * k), width=3)
    ImageDraw.Draw(img).ellipse((x - 10, y - 10, x + 10, y + 10), outline=M.scale_c(col, k), width=4)
    pill(img, fx, x, y + dy, txt, eout(k), size=28, border=col)


# 20. y la banda patina hasta que la secas (gotas en la banda; pastilla «SECAR LA CVT»)
def s_secas(t, fi, u, d):
    fr = base_cvt(None, u, [K(-0.3, 3.2, 60, 24, ty=0.95), K(0.3, 3.0, 20, 10, ty=0.95), K(5, 2.95, 14, 10, ty=0.95)], t, floor='lines')
    seco = seg(u, 1.0, 2.0)
    draw_objects(fr, cvt(0.2, t * (0.3 + 0.7 * seco), giro=t * (700 - 400 * seco), agua=1 - seco, corte=True))
    fantasma(fr, 0.2, a=0.4)
    for j in range(18):
        ph = (t * 1.6 + j * 0.13) % 1.0
        x = -1.4 + (j * 0.37) % 2.8
        dot3(fr, (x, 1.7 - ph * 1.3, 0.1), r=4, col=AGUA, a=(1 - seco) * (1 - ph), glow=0.9)

    def ui(img, fx):
        pill(img, fx, 540, 1250, 'PATINA CON AGUA', eout(seg(u, 0.1, 0.4)) * (1 - seco), size=32, border=AGUA, dot=False)
        pill(img, fx, 540, 1250, '✓ SECAR LA CVT', eout(seco), size=34, border=VERDE, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. Honda, en cambio, no le puso banda al Talon (caja de engranes sin banda)
def dct(t, k_par):
    ms = []
    for j in range(6):
        col = (120, 124, 132) if j % 2 else (84, 88, 96)
        on = (j % 2 == 0) == (k_par < 0.5)
        m = M3.cyl(0.55 - 0.03 * (j // 2), 0.06, col, n=36, shadow=0, gloss=0.8, y0=-0.03).tf(rx=90, rz=t * 180, t=(-0.6, 0.95, -0.25 + 0.09 * j))
        ms.append(named(m, 'embrague', rim=0.8, gloss=0.6, glow=M.scale_c(AMARILLO if j % 2 == 0 else CYAN, 0.12) if on else None))
    ms += engrane(0.22, 9, ACERO, t * 200, (0.55, 1.35)) + engrane(0.3, 12, (150, 154, 162), -t * 150, (0.55, 0.62))
    ms.append(tubo((-0.6, 0.95, -0.6), (-0.6, 0.95, 0.6), r=0.06, col=(110, 112, 120), name='eje'))
    return ms


def s_talon(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, -60, 16, ty=0.95), K(0.35, 3.1, -25, 10, ty=0.95), K(5, 3.0, -20, 10, ty=0.95)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'TALON', u, t0=0.0, cy=0.3, entrada='sube')
    e = P.entrada(u, -0.2, 0.3, 'cae')
    draw_objects(fr, P.tfk(dct(t, 0.0), t=(0, max(0.0, -e['dy']) * 0.5, 0)))
    ub = Wp(21, 'banda') - 0.1

    def ui(img, fx):
        kicker(img, 'HONDA TALON · SIN BANDA', 150, seg(u, 0.0, 0.3), col=AZULC)
        if u > ub:
            x, y = 540, 1270
            d_ = ImageDraw.Draw(img)
            k = seg(u, ub, ub + 0.3)
            d_.rounded_rectangle((x - 200, y - 50, x + 200, y + 50), radius=50, outline=M.scale_c(HULE if k < 0.5 else (90, 90, 96), 1), width=12)
            N.doodle_arrow_free(img, fx, x - 240, y - 80, x + 240, y + 80, t, k, ROJO, seed=8)
            texto(img, fx, x, y + 110, 'BANDA', 30, GRIS, k, f='mono', glow=0.0)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.3), amp=12)


# 22. usa doble embrague, como un carro de cambios (los dos paquetes se alternan: impares y pares)
def s_dct(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.4, 40, 30, tx=-0.6, ty=0.95), K(0.3, 2.2, 70, 12, tx=-0.6, ty=0.95), K(5, 2.15, 76, 12, tx=-0.6, ty=0.95)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.3)
    par = (int(max(0, u) / 0.55) % 2)
    draw_objects(fr, dct(t, float(par)))
    marcha = 1 + int(max(0, u) / 0.55)

    def ui(img, fx):
        kicker(img, 'DOBLE EMBRAGUE (DCT)', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 290, 1250, 'IMPARES 1·3·5', 36, AMARILLO, 1.0 if par == 0 else 0.35, f='mono', glow=0.3 if par == 0 else 0)
        texto(img, fx, 790, 1250, 'PARES 2·4·6', 36, CYAN, 1.0 if par == 1 else 0.35, f='mono', glow=0.3 if par == 1 else 0)
        P.numero_golpe(img, fx, f'{min(6, marcha)}', 1080, 1.0, size=150, col=WHITE)
        esquema(img, fx, 1.0, y=1420)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. mándaselo a tu compa que ya quemó la banda en la duna (el RZR negro entra deslizándose con su título)
def s_compa(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.85, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'desliza')
    pose = P.cam_rapida(u, [(-0.3, dict(yaw=0.9, al=600)), (0.5, dict(yaw=-0.2, al=660)), (5, dict(yaw=-0.45, al=680))])

    def ui(img, fx):
        veh(img, fx, 'rzr23', 540 + e['dy'] * 260, 1250, pose['al'], yaw=pose['yaw'], pitch=0.15, t=t)
        d_ = ImageDraw.Draw(img)
        for j in range(8):                                     # humito de banda quemada
            ph = (t * 0.7 + j * 0.12) % 1.0
            x, y = 420 + j * 25 + 20 * math.sin(t * 2 + j), 1060 - ph * 260
            r = 20 + 50 * ph
            d_.ellipse((x - r, y - r, x + r, y + r), outline=M.scale_c((140, 140, 146), 0.5 * (1 - ph)), width=4)
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que ya quemó la banda.', 'serif')], 230, seg(u, 0.05, 0.2), size=72)
        credito(img, CRED['rzr23'])
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


# 24. y que la meta en baja… (la palanca baja de golpe de H a L)
def s_metela(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -20, 14), K(0.3, 4.6, 0, 8), K(5, 4.5, 4, 8)]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    kb = P.eout4(seg(u, 0.25, 0.45))

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        x, y0, y1 = 540, 620, 1080
        d_.rounded_rectangle((x - 40, y0 - 40, x + 40, y1 + 40), radius=40, outline=(200, 200, 210), width=5)
        for j, L in enumerate(('H', 'N', 'L')):
            yy = y0 + j * (y1 - y0) / 2
            col = VERDE if (L == 'L' and kb > 0.9) else (130, 130, 138)
            texto(img, fx, x + 140, yy, L, 80, col, 1.0, f='sansx', glow=0.5 if col == VERDE else 0.0)
        yk = lerp(y0, y1, kb)
        d_.ellipse((x - 70, yk - 70, x + 70, yk + 70), fill=(30, 30, 34), outline=WHITE, width=6)
        df.ellipse((x - 90, yk - 90, x + 90, yk + 90), fill=M.scale_c(VERDE if kb > 0.9 else WHITE, 0.25))
        texto(img, fx, 540, 1300, 'BAJA', 90, VERDE, seg(u, 0.45, 0.6), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.45, 0.3), amp=18)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45),
                sfx=[(-2.6, 'cristal', 0.5), (UX, 'whoosh', 0.8), (UX + 0.45, 'bass', 0.9), (UX + 0.5, 'shimmer', 0.4)]),
           dict(desde=1, fn=s_bici, tr='whip_izq', sfx=[(0.2 + 0.38 * j, 'click', 0.7) for j in range(7)]),
           dict(desde=2, fn=s_nunca, tr='deslizar', sfx=[(0.1, 'whoosh_suave', 0.6), (0.3, 'chime_a', 0.4), (1.0, 'chime_b', 0.4)]),
           dict(desde=3, fn=s_tapa, tr='golpe', sfx=[(0.12, 'thud', 0.9), (0.4, 'tick', 0.5), (0.7, 'scribble', 0.5)]),
           dict(desde=4, fn=s_adentro, tr='zoom', c=(0.5, 0.47), sfx=[(0.3, 'shimmer', 0.5), (0.6, 'tick', 0.5), (0.9, 'tick', 0.5)]),
           dict(desde=5, fn=s_abajo, tr='giro', sfx=[(0.3, 'whoosh_suave', 0.5), (0.6, 'scribble', 0.5)]),
           dict(desde=6, fn=s_primera, tr='wipe', sfx=[(0.1, 'tick', 0.5)]),
           dict(desde=7, fn=s_pesas, tr='iris', c=(0.5, 0.5), sfx=[(0.5, 'riser', 0.5), (0.6, 'tick2', 0.4)]),
           dict(desde=8, fn=s_rampa, tr='rebanadas', sfx=[(0.4 + 0.25 * j, 'tick', 0.3) for j in range(5)] + [(1.6, 'chime_c', 0.5)]),
           dict(desde=9, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.2, 'sub', 0.9), (0.25, 'bass', 0.7)]),
           dict(desde=10, fn=s_alta, tr='deslizar_abajo', sfx=[(0.3, 'thud', 0.6), (1.0, 'slap', 0.5), (1.6, 'slap', 0.5), (2.3, 'slap', 0.5)]),
           dict(desde=11, fn=s_patina, tr='push', c=(0.42, 0.45), sfx=[(0.1, 'click', 0.5), (0.8, 'click', 0.5), (0.4, 'burst', 0.4)]),
           dict(desde=12, fn=s_quema, tr='flash', sfx=[(0.3, 'riser', 0.4), (1.2, 'burst', 0.8), (1.25, 'sub', 0.9)]),
           dict(desde=13, fn=s_manual, tr='cubo_izq', sfx=[(0.55, 'slap', 0.9), (0.8, 'scribble', 0.5)]),
           dict(desde=14, fn=s_baja, tr='rebanadas', sfx=[(0.2, 'tick', 0.5), (1.0, 'tick', 0.5), (1.8, 'tick', 0.5), (2.6, 'bass', 0.9)]),
           dict(desde=15, fn=s_vueltas, tr='remolino', sfx=[(0.3 + 0.35 * j, 'tick2', 0.3) for j in range(7)]),
           dict(desde=16, fn=s_agarra, tr='whip', sfx=[(0.3, 'chime_b', 0.5), (0.6, 'chime_c', 0.4)]),
           dict(desde=17, fn=s_dientes, tr='zoom', c=(0.62, 0.42), sfx=[(0.6, 'click', 0.8), (1.3, 'click', 0.8)]),
           dict(desde=18, fn=s_vidrio, tr='cristal', palabra='VIDRIO', sfx=[(0.8, 'tick', 0.5), (1.0, 'scribble', 0.4)]),
           dict(desde=19, fn=s_charco, tr='deslizar_abajo', sfx=[(0.2, 'whoosh_suave', 0.6), (0.6, 'burst', 0.3)]),
           dict(desde=20, fn=s_secas, tr='glitch', sfx=[(1.0, 'whoosh_suave', 0.5), (1.6, 'chime_b', 0.5)]),
           dict(desde=21, fn=s_talon, tr='cubo', sfx=[(0.1, 'thud', 0.7), (1.2, 'scribble', 0.6)]),
           dict(desde=22, fn=s_dct, tr='golpe', sfx=[(0.55 * j, 'click', 0.7) for j in range(1, 7)]),
           dict(desde=23, fn=s_compa, tr='ritmo', sfx=[(0.05, 'slap', 0.7), (0.2, 'bass', 0.7)]),
           dict(desde=24, loop=True, tr='zoom')]


def tiempos_falsos():
    T = [(round(0.25 + 2.75 * i, 2), round(0.25 + 2.75 * i + 2.4, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.55, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    print('ok', T[-1])


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    else:
        montaje.cli(globals())
