"""Reel EXTRA (pedido de Efrén, 9-nov-2026): la historia de Can-Am. Voz Isaac (4 % más rápida para quedar en 74 s).
Pedido clave: «que los vehículos no se vean como una recreación en 3D, sino como se ven en las imágenes pero en 3D».
→ Cada vehículo es su FOTO REAL recortada (ISNet) con profundidad (Depth Anything V2): la cámara orbita con paralaje,
   la luz recorre la carrocería real y hay reflejo en el piso (kit/nuevo/foto3d.py). Nada de mallas recreadas.
Inicio tipo 2 (el objeto cae y rebota): el Spyder rojo cae sobre la foto de motocross de los 70 y la tumba.
Loop: la última frase («porque todo empezó con dos ruedas») enseña la foto de motocross… y el Spyder vuelve a caer.

Datos (fuentes en guiones/2026-11-09_canam.txt): Can-Am nace en 1972-73 dentro de Bombardier (Valcourt, Quebec), motos de
motocross/enduro con motor Rotax; nombre por concurso entre empleados (Canadá + América) y compraron los derechos porque ya
existía la serie de carreras Can-Am (Wikipedia, «Can-Am motorcycles»); ISDT 1973: oro, plata y bronce (cyclechaos,
Motocross Action); 1974: Gary Jones, campeón AMA 250 en Can-Am (Motocross Action, PulpMX); 1987, último año de motos
(Wikipedia, PulpMX); mayo 2006: las cuatrimotos de BRP pasan a llamarse Can-Am (Powersports Business); febrero 2007:
Spyder roadster (ATV Magazine, BRP); acomodo como moto de nieve (Wikipedia «Can-Am Spyder»); Juárez: 2 millones de
vehículos desde 2007 (BRP, 23-ene-2026); 2024: Pulse y Origin eléctricas + ediciones «73» por el año de lanzamiento (amcn,
Cycle Gear, Electric Autonomy).
Fotos: Wikimedia Commons, solo CC BY / CC0 / dominio público (créditos en pantalla y en el guion). No hay foto libre de
una moto Can-Am de los 70 ni de las eléctricas: el motocross de los 70 se ve con fotos de NARA (dominio público) y se
dice en pantalla que es «MOTOCROSS EN LOS 70», no una Can-Am.
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
import norte as N
import foto3d as F3
from motor2 import (Frame, Cam, space, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3, rec_frame,
                    seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

TEMA = 'canam'
TXT = ['Seguro has visto uno de estos… pero Can-Am no nació con tres ruedas.',
       'Nació en Quebec, Canadá, dentro de Bombardier, la empresa que inventó la moto de nieve Ski-Doo.',
       'En 1973 lanzó sus primeras motos de motocross, con motor Rotax.',
       'El nombre salió de un concurso entre sus empleados: Canadá más América… y hasta tuvieron que comprarlo.',
       'Y ganaron rápido: oro, plata y bronce en los Seis Días Internacionales.',
       'Un año después ya eran campeones de motocross en Estados Unidos.',
       'Pero las ventas se cayeron… y en 1987 hicieron su última moto.',
       'El nombre se quedó dormido 19 años.',
       'En 2006, BRP lo revivió: sus cuatrimotos pasaron a llamarse Can-Am.',
       'Y en 2007 sacó algo rarísimo: el Spyder, con dos ruedas adelante y una atrás.',
       '¿Te suena? Es el mismo acomodo de una moto de nieve: dos esquís adelante y una oruga atrás.',
       'Hoy muchos se arman en Ciudad Juárez, Chihuahua: de ahí ya salieron 2 millones.',
       'Y en 2024 volvió a las motos de dos ruedas… pero eléctricas.',
       'A su edición especial le pusieron un número: 73.',
       'Mándaselo a alguien con un Can-Am,',
       'porque todo empezó con dos ruedas.']
VOZ = list(TXT)
VOZ[0] = '[curious] ' + TXT[0]
VOZ[2] = 'En mil novecientos setenta y tres lanzó sus primeras motos de motocross, con motor Rotax.'
VOZ[6] = '[excited] Pero las ventas se cayeron… y en mil novecientos ochenta y siete hicieron su última moto.'
VOZ[7] = 'El nombre se quedó dormido diecinueve años.'
VOZ[8] = 'En dos mil seis, BRP lo revivió: sus cuatrimotos pasaron a llamarse Can-Am.'
VOZ[9] = 'Y en dos mil siete sacó algo rarísimo: el Spyder, con dos ruedas adelante y una atrás.'
VOZ[11] = 'Hoy muchos se arman en Ciudad Juárez, Chihuahua: de ahí ya salieron dos millones.'
VOZ[12] = 'Y en dos mil veinticuatro volvió a las motos de dos ruedas… pero eléctricas.'
VOZ[13] = 'A su edición especial le pusieron un número: setenta y tres.'

AMARILLO = (255, 236, 160)
ORO, PLATA, BRONCE = (255, 198, 70), (205, 210, 222), (210, 130, 70)
GRIS = (120, 120, 128)
WORDS_JSON = '/home/claude/words_canam_r.json'


# ================================================================== tiempos
def _palabras(i):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split()


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


_WS = []


def _ws():
    if not _WS and os.path.exists(WORDS_JSON):
        d = json.load(open(WORDS_JSON))['words']
        _WS.extend([w for w in d if w.get('type', 'word') == 'word' and not w['text'].startswith('[')])
    return _WS


def W(i, k):
    """Tiempo global en que empieza la palabra k (desde 0) de la frase i (palabras reales de Scribe)."""
    ws = _ws()
    idx = sum(len(_palabras(j)) for j in range(i)) + k
    if not ws or idx >= len(ws):
        n = len(_palabras(i))
        return TT(i) + (TE(i) - TT(i)) * k / n
    off = TT(0) - ws[0]['start']
    return ws[idx]['start'] + off


def Wu(i, k):
    return W(i, k) - TT(i)


def F(k, s):
    return M.font(k, s)


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def mov(u, claves):
    return P.cam_rapida(u, claves)


# ================================================================== fotos reales en 3D
FOTOS = os.path.join(HERE, 'img', 'canam')
CREDITO = {
    'spyth': 'FOTO: TONY HISGETT · CC BY 2.0', 'spybs': 'FOTO: BRIAN SNELSON · CC BY 2.0',
    'spyjb': 'FOTO: JOOST J. BAKKER · CC BY 2.0', 'skidoo': 'FOTO: DADEROT · CC0 · MUSEO DE BELLAS ARTES DE MONTREAL',
    'outh': 'FOTO: ANTTI LEPPÄNEN · CC BY 4.0', 'defr': 'FOTO: AHUNT · CC0', 'mavf': 'FOTO: KARLEHORN · CC BY 3.0',
    'mavs': 'FOTO: KARLEHORN · CC BY 3.0', 'irving': 'FOTO: ARTAXERXES · CC BY 4.0',
    'nara1': 'FOTO: BILL GILLETTE · NARA · DOMINIO PÚBLICO', 'nara2': 'FOTO: BILL GILLETTE · NARA · DOMINIO PÚBLICO',
    'nara3': 'FOTO: BILL GILLETTE · NARA · DOMINIO PÚBLICO'}
_RECORTE = {'outh': dict(borrar=[(0.24, 0, 0.41, 0.29)]), 'spyth': dict(borrar=[(0.08, 0, 0.41, 0.16)]),
            'irving': dict(borrar=[(0.49, 0, 0.62, 0.54)])}
VEH = {}
ESC = {}
for _n in ['spyth', 'spybs', 'spyjb', 'skidoo', 'outh', 'defr', 'mavf', 'mavs', 'irving']:
    VEH[_n] = F3.preparar(f'{FOTOS}/canam_i_{_n}.jpg', _n, **_RECORTE.get(_n, {}))
for _n in ['nara1', 'nara2', 'nara3']:
    ESC[_n] = F3.preparar_escena(f'{FOTOS}/canam_i_{_n}.jpg', _n)


def veh(img, fx, n, cx, piso, alto, yaw=0.0, pitch=0.15, t=0.0, alfa=1.0, luz=None, reflejo=0.22, borde=0.55, dy=0.0,
        escala=1.0):
    """Vehículo real (foto recortada con profundidad) apoyado en el piso: su base queda en `piso` (px)."""
    a = VEH[n]
    if luz is None:
        luz = (-0.65 + 0.55 * math.sin(t * 0.9), -0.62)       # la luz recorre la carrocería
    al = alto * escala
    cy = piso - al * 0.5 + dy
    r = F3.dibujar(img, a, cx, cy, al, yaw=yaw, pitch=pitch, luz=luz, fx=fx, alfa=alfa, reflejo=reflejo, borde=borde,
                   piso_y=piso + dy)
    return r


def en(r, px, py):
    """Punto de la foto (fracciones) → pantalla, con el rectángulo que devolvió veh()."""
    x0, y0, w, h = r
    return x0 + px * w, y0 + py * h


def credito(img, txt, y=1872, k=1.0):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    d.text((540, y), txt, font=F('mono', 19), fill=M.scale_c((150, 150, 158), k), anchor='mm')


def escenario(t, yaw_deg=0.0, pitch=11, dist=6.0, floor_a=0.8, beam=0.35, cy=0.5, bokeh=1.0, floor='dots'):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=dist, yaw=yaw_deg, pitch=pitch, cy=cy))
    space(fr, t, floor=floor, floor_a=floor_a, bokeh=bokeh, beam=beam)
    return fr


def piso(fr):
    return fr.cam.p1((0, 0, 0))[1]


def tierra(fr, t, C, R, spin):
    N.earth(fr, t, np.asarray(C, float), R, spin)


def geo(lat, lon, spin, C, R):
    la, lo = math.radians(lat), math.radians(lon)
    p = np.array([[R * math.cos(la) * math.cos(lo), R * math.sin(la), R * math.cos(la) * math.sin(lo)]])
    return np.asarray(C, float) + D._rot(p, spin)[0]


def giro_para(lat, lon, cam_dir=(0, 0.15, 1)):
    """Giro de la Tierra de alambre que pone (lat, lon) de frente a la cámara."""
    v = np.asarray(cam_dir, float)
    v /= np.linalg.norm(v)
    best = max(np.linspace(0, 2 * math.pi, 720), key=lambda s: float((geo(lat, lon, s, (0, 0, 0), 1.0)) @ v))
    return float(best)


SPIN_QC = giro_para(46.5, -72.3, (0, math.sin(math.radians(34)), math.cos(math.radians(34))))
SPIN_JZ = giro_para(31.7, -106.4, (0, math.sin(math.radians(24)), math.cos(math.radians(24))))


def pin(img, fx, x, y, k, txt, col=CYAN):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    h = 70 * P.resorte(k)
    d.line([(x, y), (x, y - h)], fill=col, width=4)
    r = 16 * clamp(k * 2)
    d.ellipse((x - r, y - h - r, x + r, y - h + r), fill=col)
    df.ellipse((x - r - 6, y - h - r - 6, x + r + 6, y - h + r + 6), fill=M.scale_c(col, 0.5))
    rr = 30 * (1 + 2 * ((k * 3) % 1.0))
    df.ellipse((x - rr, y - rr * 0.4, x + rr, y + rr * 0.4), outline=M.scale_c(col, 0.6 * (1 - (k * 3) % 1.0)), width=3)
    pill(img, fx, x, y - h - 70, txt, eout(seg(k, 0.3, 1.0)), size=32, border=col)


def medalla(img, fx, cx, cy, r, col, k, t, etiqueta):
    """Medalla de metal (dibujo 2D con brillo) que cuelga y se balancea."""
    if k <= 0.01:
        return
    s = P.resorte(k)
    ang = 8 * math.exp(-3 * max(0, k - 0.3)) * math.sin(t * 7)
    lay = Image.new('RGBA', (int(r * 2.6), int(r * 4.2)), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    w, h = lay.size
    mx, my = w / 2, h - r * 1.2
    dl.polygon([(mx - r * 0.75, 0), (mx - r * 0.2, 0), (mx + r * 0.25, my - r * 0.6), (mx - r * 0.25, my - r * 0.6)], fill=(60, 120, 200, 255))
    dl.polygon([(mx + r * 0.75, 0), (mx + r * 0.2, 0), (mx - r * 0.25, my - r * 0.6), (mx + r * 0.25, my - r * 0.6)], fill=(200, 60, 60, 255))
    for j in range(24, 0, -1):
        rr = r * j / 24
        c = M.mixc(M.scale_c(col, 0.55), M.mixc(col, (255, 255, 255), 0.35), (1 - j / 24) ** 0.7)
        dl.ellipse((mx - rr - r * 0.12 * (1 - j / 24), my - rr - r * 0.18 * (1 - j / 24), mx + rr, my + rr), fill=c + (255,))
    dl.ellipse((mx - r * 0.72, my - r * 0.72, mx + r * 0.72, my + r * 0.72), outline=M.scale_c(col, 0.5) + (255,), width=max(2, int(r * 0.06)))
    lay = lay.rotate(ang, resample=Image.BICUBIC, center=(w / 2, 0))
    lay = lay.resize((max(2, int(w * s)), max(2, int(h * s))), Image.BILINEAR)
    img.paste(lay, (int(cx - lay.width / 2), int(cy - r * 3.0 * s)), lay)
    ImageDraw.Draw(fx).ellipse((cx - r * 0.5, cy - r * 0.6 * s, cx - r * 0.1, cy - r * 0.2 * s), fill=M.scale_c(col, 0.45))
    ImageDraw.Draw(img).text((cx, cy + r * 1.35), etiqueta, font=F('mono', 30), fill=M.scale_c(col, clamp(k * 2)), anchor='mm')


def rayo(img, fx, k, t, cx=540, y0=520, y1=1180, col=(150, 235, 255)):
    """Rayo de luz (line-art) que cae: para «eléctricas»."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(int(t * 14))
    pts = [(cx + 120, y0)]
    n = 7
    for j in range(1, n + 1):
        yy = y0 + (y1 - y0) * j / n
        pts.append((cx + (90 if j % 2 else -90) * (1 - j / n) + rng.uniform(-14, 14), yy))
    m = max(2, int(len(pts) * clamp(k * 1.6)))
    ImageDraw.Draw(img).line(pts[:m], fill=col, width=9, joint='curve')
    ImageDraw.Draw(fx).line(pts[:m], fill=M.scale_c(col, 0.9), width=30, joint='curve')


def rueda(img, fx, cx, cy, r, ang, k, col=WHITE):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    c = M.scale_c(col, k)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=6)
    d.ellipse((cx - r * 0.82, cy - r * 0.82, cx + r * 0.82, cy + r * 0.82), outline=M.scale_c(col, 0.5 * k), width=2)
    df.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(col, 0.35 * k), width=14)
    for j in range(8):
        a = ang + j * math.pi / 4
        d.line([(cx + r * 0.12 * math.cos(a), cy + r * 0.12 * math.sin(a)), (cx + r * 0.8 * math.cos(a), cy + r * 0.8 * math.sin(a))], fill=c, width=3)
    d.ellipse((cx - r * 0.14, cy - r * 0.14, cx + r * 0.14, cy + r * 0.14), fill=c)


def texto_grande(img, fx, txt, x, y, size, col=WHITE, a=1.0, anchor='mm', glow=0.3, f='sansx'):
    if a <= 0.01:
        return
    lay = Image.new('L', img.size, 0)
    ImageDraw.Draw(lay).text((x, y), txt, font=F(f, size), fill=int(255 * clamp(a)), anchor=anchor)
    img.paste(Image.new('RGB', img.size, col), (0, 0), lay)
    if glow:
        fx.paste(Image.new('RGB', img.size, M.scale_c(col, glow)), (0, 0), lay.filter(ImageFilter.GaussianBlur(8)))


# ================================================================== escenas
# 0. gancho (inicio tipo 2): el Spyder rojo cae sobre la foto de motocross de los 70 y la tumba
U_CAE, U_ATERRIZA = -0.42, -0.02


def s_gancho(t, fi, u, d):
    m = mov(u, [(-4.0, dict(yaw=-0.25, al=640, cy=0.0)), (U_ATERRIZA, dict(yaw=-0.55, al=640, cy=0.0)),
                (Wu(0, 7), dict(yaw=-0.55, al=640, cy=0.0)), (Wu(0, 7) + 0.05, dict(yaw=0.35, al=720, cy=0.0)),
                (Wu(0, 11), dict(yaw=0.35, al=720, cy=0.0)), (Wu(0, 11) + 0.05, dict(yaw=0.15, al=760, cy=0.0)),
                (6.0, dict(yaw=0.6, al=780, cy=0.0))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.45)
    py = piso(fr) + 215
    kc = seg(u, U_CAE + 0.05, U_CAE + 0.6)                  # la foto sale volando al caer el Spyder

    def ui(img, fx):
        M.cristal(img, fx, '3 RUEDAS', u, t0=-0.75, cy=0.37, entrada='golpe')
        if kc < 1:
            yy = 1010 + 1500 * kc ** 2
            F3.dibujar_escena(img, ESC['nara2'], (90, yy - 330, 990, yy + 330), yaw=0.9 * math.sin(t * 0.7), pitch=0.35,
                              angulo=-4 - 40 * kc ** 1.5, marco=14)
            if kc < 0.05:
                kicker(img, 'MOTOCROSS · AÑOS 70', 560, 1.0, col=(150, 210, 230))
                credito(img, CREDITO['nara2'], y=1360)
        kl = 1 - seg(u, U_CAE - 0.12, U_CAE)
        if u < U_CAE:
            M.title(img, fx, [('Todo empezó', 'sans'), ('con dos ruedas.', 'serif')], 250, kl * seg(u, -3.2, -2.85), size=84)
        if u >= U_CAE:
            e = P.entrada(u, U_CAE, U_ATERRIZA - U_CAE + 0.25, 'cae')
            r = veh(img, fx, 'spyth', 540, py, m['al'], yaw=m['yaw'], pitch=0.18, t=t, dy=e['dy'] * 260, alfa=e['alfa'])
            uw = Wu(0, 12)                                     # «tres ruedas»
            if r and u >= uw - 0.2:
                for j, (px_, py_) in enumerate([(0.26, 0.80), (0.88, 0.63)]):
                    x, y = en(r, px_, py_)
                    doodle_circle(img, fx, x, y, r[2] * 0.15, r[3] * 0.15, t, k=seg(u, uw - 0.2 + 0.12 * j, uw + 0.15 + 0.12 * j), seed=j)
                x, y = en(r, 0.56, 0.52)
                pill(img, fx, x, y - 40, '+1 ATRÁS', eout(seg(u, uw + 0.25, uw + 0.5)), size=30, border=AMARILLO)
            credito(img, CREDITO['spyth'], k=seg(u, U_ATERRIZA, U_ATERRIZA + 0.3))
        kicker(img, 'CAN-AM SPYDER · FOTO REAL EN 3D', 140, seg(u, 0.05, 0.35), col=(150, 210, 230))
        P.titulo_golpe(img, fx, [('No nació', 'sans'), ('con tres ruedas.', 'serif')], 200, seg(u, 0.08, 0.23), size=92)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, U_ATERRIZA, 0.35) + golpe_k(u, 0.23, 0.3), amp=22)


# 1. Quebec (Tierra de alambre con pin) → la Ski-Doo de Bombardier (foto real en 3D)
def _quebec_tierra(t, fi, u):
    k = P.eout4(seg(u, -0.2, 0.5))
    C = np.array([0.0, 1.0, 0.0])
    spin = SPIN_QC + 0.5 * (1 - k) + 0.04 * u
    fr = Frame(Cam(target=tuple(C), dist=7.4 - 2.6 * k, yaw=4 * math.sin(t * 0.4), pitch=34, cy=0.56))
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, C, 1.6, spin)
    q = geo(46.5, -72.3, spin, C, 1.6)
    dot3(fr, q, r=10, col=CYAN, a=0.7 + 0.3 * math.sin(t * 8), glow=1.5)
    px, py, _ = fr.cam.p1(tuple(q))

    def ui(img, fx):
        pin(img, fx, px, py, seg(u, 0.3, 1.1), 'VALCOURT, QUEBEC')
        kicker(img, 'CANADÁ · 1972', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        M.title(img, fx, [('Todo empezó', 'sans'), ('en la nieve.', 'serif')], 210, seg(u, 0.5, 0.9), size=78)
    fr.ui.append(ui)
    return finish(fr, fi), (px / 1080, py / 1920)


def _quebec_skidoo(t, fi, u, u0):
    v = u - u0
    m = mov(v, [(-0.1, dict(yaw=0.9, al=520)), (0.0, dict(yaw=0.9, al=520)), (0.35, dict(yaw=-0.2, al=560)),
                (Wu(1, 13) - u0, dict(yaw=-0.2, al=560)), (Wu(1, 13) - u0 + 0.05, dict(yaw=-0.75, al=620)), (5, dict(yaw=-0.6, al=630))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.5)
    py = piso(fr) + 120

    def ui(img, fx):
        M.cristal(img, fx, 'NIEVE', v, t0=0.0, cy=0.4, entrada='zoom')
        e = P.entrada(v, 0.0, 0.28, 'pop')
        veh(img, fx, 'skidoo', 540, py, m['al'], yaw=m['yaw'], pitch=0.2, t=t, escala=max(0.05, e['escala']), alfa=e['alfa'])
        kicker(img, 'BOMBARDIER · SKI-DOO ORIGINAL', 150, seg(v, 0.1, 0.4), col=(150, 210, 230))
        pill(img, fx, 540, 1400, 'LA MOTO DE NIEVE QUE INVENTARON', eout(seg(u, Wu(1, 8), Wu(1, 8) + 0.3)), size=32, border=AMARILLO)
        credito(img, CREDITO['skidoo'], k=seg(v, 0.2, 0.5))
    fr.ui.append(ui)
    return finish(fr, fi)


def s_quebec(t, fi, u, d):
    u0 = Wu(1, 6)                                              # «Bombardier»
    if u < u0 - 0.18:
        return _quebec_tierra(t, fi, u)[0]
    if u >= u0 + 0.14:
        return _quebec_skidoo(t, fi, u, u0)
    A, (cx, cy) = _quebec_tierra(t, fi, u)
    B = _quebec_skidoo(t, fi, u, u0)
    return M.tr_zoom_through(A, B, seg(u, u0 - 0.18, u0 + 0.14), cx, cy)


# 2. 1973: así era el motocross (foto real de NARA en 3D) + zoom digital + motor Rotax
def s_1973(t, fi, u, d):
    m = mov(u, [(-0.3, dict(yaw=-1.0, p=0.2)), (0.4, dict(yaw=-0.2, p=0.35)), (Wu(2, 7), dict(yaw=-0.2, p=0.35)),
                (Wu(2, 7) + 0.05, dict(yaw=0.8, p=0.1)), (6, dict(yaw=1.0, p=0.05))])
    fr = escenario(t, yaw_deg=0, floor=None, beam=0.3)

    def ui(img, fx):
        F3.dibujar_escena(img, ESC['nara2'], (70, 640, 1010, 1345), yaw=m['yaw'], pitch=m['p'], esc=1.14, marco=14,
                          angulo=-2.0)
        kicker(img, 'ASÍ ERA EL MOTOCROSS EN LOS 70', 190, seg(u, 0.0, 0.3), col=(150, 210, 230))
        M.title(img, fx, [('Primero fueron', 'sans'), ('motos de motocross.', 'serif')], 270, seg(u, 0.15, 0.55), size=76)
        credito(img, CREDITO['nara2'], y=1395)
    fr.ui.append(ui)
    out = finish(fr, fi)
    # zoom digital sobre el salto (x1.0 → x1.3 → x1.6)
    z1, z2 = Wu(2, 6), Wu(2, 10)
    z = 1.0 + 0.3 * P.eout4(seg(u, z1, z1 + 0.1)) + 0.3 * P.eout4(seg(u, z2, z2 + 0.1))
    if z > 1.001:
        out = M.scale_about(out, z, 0.53, 0.47)
        im = Image.fromarray(out)
        rec_frame(im, t, k=seg(u, z1, z1 + 0.1), zoom_label=f'x{z:.1f}')
        out = np.asarray(im)
    ur = Wu(2, 11)                                             # «Rotax»
    if u >= ur - 0.05:
        im = Image.fromarray(out)
        pill(im, Image.new('RGB', im.size), 540, 1460, 'MOTOR ROTAX · AUSTRIA', eout(seg(u, ur - 0.05, ur + 0.25)), size=36, border=AMARILLO)
        out = np.asarray(im)
    return sacudir(out, t, golpe_k(u, z1, 0.2) + golpe_k(u, z2, 0.2), amp=10)


# 3. el nombre: CANADÁ + AMÉRICA chocan → CAN-AM de cristal → «hasta tuvieron que comprarlo»
def s_nombre(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0)
    uc, um, ua, ub = Wu(3, 9), Wu(3, 10), Wu(3, 11), Wu(3, 16)
    uj = ua + 0.55                                              # se juntan
    kj = P.eout4(seg(u, uj, uj + 0.3))

    def ui(img, fx):
        kicker(img, 'UN CONCURSO ENTRE EMPLEADOS · 1972', 210, seg(u, 0.0, 0.3), col=(150, 210, 230))
        kz = 1 - P.eout4(seg(u, uc - 0.35, uc - 0.05))          # la urna se va cuando entra CANADÁ
        if kz > 0.01:
            dd = ImageDraw.Draw(img)
            df = ImageDraw.Draw(fx)
            oy = (1 - kz) * 900
            bx = (300, 1050 + oy, 780, 1420 + oy)
            dd.rounded_rectangle(bx, radius=24, outline=M.scale_c(WHITE, kz), width=5)
            df.rounded_rectangle(bx, radius=24, outline=M.scale_c(WHITE, 0.3 * kz), width=14)
            dd.line([(470, 1050 + oy), (610, 1050 + oy)], fill=(0, 0, 0), width=9)
            dd.text((540, 1250 + oy), 'CONCURSO', font=F('mono', 40), fill=M.scale_c(CYAN, kz), anchor='mm')
            M.title(img, fx, [('¿Cómo se', 'sans'), ('iba a llamar?', 'serif')], 300, seg(u, -0.25, 0.1) * kz, size=82)
            for j in range(10):                                 # papelitos con nombres que caen a la urna
                u0 = -0.3 + 0.26 * j
                kk = seg(u, u0, u0 + 0.55)
                if 0 < kk < 1:
                    yy = lerp(560, 1060, kk ** 2) + oy
                    sl = Image.new('RGBA', (230, 120), (0, 0, 0, 0))
                    ImageDraw.Draw(sl).rounded_rectangle((0, 0, 229, 119), radius=10, fill=(240, 238, 230, 255))
                    ImageDraw.Draw(sl).text((115, 60), '¿ NOMBRE ?', font=F('mono', 26), fill=(40, 40, 46), anchor='mm')
                    sl = sl.rotate(25 * math.sin(j * 2.1 + kk * 4), resample=Image.BICUBIC, expand=True)
                    img.paste(sl, (int(540 + 140 * math.sin(j * 1.7) * (1 - kk) - sl.width / 2), int(yy - sl.height / 2)), sl)
        if kj < 1:
            k1 = P.eout4(seg(u, uc - 0.15, uc + 0.15))
            k2 = P.eout4(seg(u, ua - 0.15, ua + 0.15))
            x1 = lerp(-500, 540, k1) + lerp(0, 120, kj)
            x2 = lerp(1600, 540, k2) - lerp(0, 120, kj)
            texto_grande(img, fx, 'CANADÁ', x1, lerp(760, 860, kj), 150, a=1 - kj)
            texto_grande(img, fx, 'AMÉRICA', x2, lerp(1000, 860, kj), 150, a=1 - kj)
            kp = P.resorte(seg(u, um - 0.1, um + 0.2))
            texto_grande(img, fx, '+', 540, 880, int(120 * max(0.01, kp)), col=CYAN, a=clamp(kp) * (1 - kj), glow=0.8)
            # las letras que sobran se caen
            if u > ua + 0.2:
                kf = seg(u, ua + 0.2, uj + 0.3)
                texto_grande(img, fx, 'CAN', 540 - 150 + 0 * kf, 760 - 200 * 0, 110, col=CYAN, a=clamp(kf * 3) * (1 - kj), glow=0.6)
                texto_grande(img, fx, 'AM', 540 + 150, 1000, 110, col=CYAN, a=clamp(kf * 3) * (1 - kj), glow=0.6)
        if u >= uj:
            M.cristal(img, fx, 'CAN-AM', u, t0=uj, cy=0.45, entrada='zoom')
            kicker(img, 'CAN(ADÁ) + AM(ÉRICA)', 1180, seg(u, uj + 0.2, uj + 0.5), col=(200, 200, 210), size=30)
        if u >= ub - 0.1:
            kb = eout(seg(u, ub - 0.1, ub + 0.25))
            pill(img, fx, 540, 1330, 'YA LO USABA UNA SERIE DE CARRERAS', kb, size=32, border=AMARILLO)
            # etiqueta de precio que cae y se balancea
            ang = 14 * math.exp(-4 * max(0, u - ub)) * math.sin((u - ub) * 12)
            tag = Image.new('RGBA', (300, 150), (0, 0, 0, 0))
            dt = ImageDraw.Draw(tag)
            dt.polygon([(0, 75), (50, 0), (300, 0), (300, 150), (50, 150)], fill=(245, 236, 200, 255))
            dt.ellipse((34, 63, 58, 87), fill=(10, 10, 12, 255))
            dt.text((180, 75), 'COMPRADO', font=F('sans', 36), fill=(30, 30, 34), anchor='mm')
            tag = tag.rotate(ang - 8, resample=Image.BICUBIC, expand=True)
            yy = lerp(-200, 520, P.rebote(seg(u, ub - 0.1, ub + 0.3)))
            img.paste(tag, (int(760 - tag.width / 2), int(yy - tag.height / 2)), tag)
    fr.ui.append(ui)
    out = finish(fr, fi)
    s = 1 + 0.05 * P.eout4(seg(u, uj, uj + 0.2)) - 0.05 * P.eout4(seg(u, ub, ub + 0.25))
    if abs(s - 1) > 1e-3:
        out = M.scale_about(out, s, 0.5, 0.48)
    return sacudir(out, t, golpe_k(u, uj + 0.05, 0.3) + golpe_k(u, ub + 0.2, 0.3), amp=16)


# 4. oro, plata y bronce (medallas que caen y se balancean) — ISDT 1973
def s_medallas(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    uo, up, ub = Wu(4, 3), Wu(4, 4), Wu(4, 6)

    def ui(img, fx):
        F3.dibujar_escena(img, ESC['nara1'], (80, 1150, 1000, 1530), yaw=0.8 * math.sin(t * 0.6), pitch=0.2, esc=1.15, marco=10,
                          alfa=0.55 * seg(u, -0.25, 0.0), sombra=False, tinte=((255, 255, 255), 0.6))
        kicker(img, 'SEIS DÍAS INTERNACIONALES · 1973', 160, seg(u, -0.25, 0.0), col=(150, 210, 230))
        M.title(img, fx, [('Ganaron', 'sans'), ('desde el primer año.', 'serif')], 230, seg(u, -0.25, 0.1), size=76)
        for (x, col, u0, lab, sd) in [(270, ORO, uo, 'ORO', 0), (540, PLATA, up, 'PLATA', 1), (810, BRONCE, ub, 'BRONCE', 2)]:
            k = seg(u, u0 - 0.1, u0 + 0.25)
            yy = lerp(-300, 860, P.rebote(k))
            medalla(img, fx, x, yy, 105, col, k, t + sd, lab)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, uo + 0.15, 0.25) + golpe_k(u, up + 0.15, 0.25) + golpe_k(u, ub + 0.15, 0.25), amp=10)


# 5. 1974: campeones en Estados Unidos (la foto cae y se pega) + número que golpea
def s_campeones(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0)
    un = Wu(5, 3)                                               # «campeones» (casi)

    def ui(img, fx):
        k = seg(u, -0.32, 0.05)
        yy = lerp(-200, 1080, P.rebote(k))
        ang = -3 + 6 * math.exp(-5 * max(0, u - 0.3)) * math.cos(12 * max(0, u - 0.3))
        F3.dibujar_escena(img, ESC['nara3'], (80, yy - 360, 1000, yy + 360), yaw=-0.8 + 1.4 * seg(u, 0, 3.5), pitch=0.3, esc=1.14,
                          marco=14, angulo=ang)
        P.numero_golpe(img, fx, '1974', 360, seg(u, un - 0.15, un), size=230, col=AMARILLO)
        kicker(img, 'UN AÑO DESPUÉS', 170, seg(u, 0.0, 0.3), col=(150, 210, 230))
        pill(img, fx, 540, 1530, 'CAMPEONES DE MOTOCROSS 250 · EE. UU.', eout(seg(u, Wu(5, 5), Wu(5, 5) + 0.3)), size=30, border=AMARILLO)
        credito(img, CREDITO['nara3'], y=1462)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.05, 0.3) + golpe_k(u, un, 0.35), amp=18)


# 6. SEGUNDO GANCHO: las ventas se caen → la foto se vuelve gris y se cae → 1987 de cristal, última moto
def s_caida(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.8)
    uc, u87, uu = Wu(6, 4), Wu(6, 7), Wu(6, 13)

    def ui(img, fx):
        kg = seg(u, 0.0, uc + 0.3)
        kf = seg(u, uc + 0.1, u87 + 0.2)
        if kf < 1:
            yy = 980 + 1300 * kf ** 2
            F3.dibujar_escena(img, ESC['nara1'], (90, yy - 340, 990, yy + 340), yaw=0.3, pitch=0.2, esc=1.14, marco=14,
                              angulo=-2 + 30 * kf ** 1.5, tinte=((255, 255, 255), 0.95 * kg))
        if u < u87:
            # flecha roja que baja: «las ventas se cayeron»
            k = P.eout4(seg(u, uc - 0.2, uc + 0.25))
            if k > 0:
                pts = [(200, 520), (430, 600), (600, 560), (880, 520 + 560 * k)]
                ImageDraw.Draw(img).line(pts, fill=RED, width=10, joint='curve')
                ImageDraw.Draw(fx).line(pts, fill=M.scale_c(RED, 0.7), width=26, joint='curve')
                pill(img, fx, 540, 420, 'VENTAS', k, size=34, border=RED)
        if u >= u87 - 0.1:
            M.cristal(img, fx, '1987', u, t0=u87 - 0.1, cy=0.42, entrada='golpe')
            pill(img, fx, 540, 1290, 'LA ÚLTIMA MOTO CAN-AM', eout(seg(u, uu - 0.1, uu + 0.2)), size=38, border=RED)
        kicker(img, 'Y ENTONCES…', 200, seg(u, 0.0, 0.3), col=(255, 140, 130))
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u87 - 0.05 <= u < u87 + 0.2:
        out = M.tr_glitch(out, out, 0.5, fi)
    return sacudir(out, t, golpe_k(u, uc + 0.2, 0.3) + golpe_k(u, u87, 0.4), amp=22)


# 7. el nombre se quedó dormido 19 años (contador de años 1987 → 2006)
def s_dormido(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.7)
    k = ease(seg(u, 0.25, d - 0.7))
    yr = int(round(1987 + 19 * k))

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        df = ImageDraw.Draw(fx)
        cx, cy, R = 540, 900, 330
        dd.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(60, 62, 70), width=6)
        if k > 0:
            dd.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * k, fill=CYAN, width=10)
            df.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * k, fill=M.scale_c(CYAN, 0.6), width=26)
        texto_grande(img, fx, str(yr), cx, cy - 10, 190, col=WHITE, glow=0.35, f='mono')
        texto_grande(img, fx, f'{yr - 1987} AÑOS', cx, cy + 140, 46, col=(170, 210, 230), glow=0.2, f='mono')
        texto_grande(img, fx, 'CAN-AM', cx, 1330, 110, col=(70, 70, 76), glow=0.0)
        for j in range(3):                                      # «Zzz» que suben
            ph = (u * 0.6 + j * 0.33) % 1.0
            texto_grande(img, fx, 'z', 760 + 60 * j + 30 * math.sin(ph * 6), 1250 - 260 * ph, int(50 + 30 * j), col=WHITE,
                         a=math.sin(math.pi * ph) * 0.8, glow=0.2, f='serif')
        kicker(img, 'EL NOMBRE, DORMIDO', 230, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    out = finish(fr, fi)
    s = 1.0 + 0.06 * P.eout4(seg(u, 0.0, 0.25))
    return M.scale_about(out, s, 0.5, 0.47)


# 8. 2006: la cuatrimoto deja de llamarse Bombardier y se llama Can-Am (Outlander real en 3D)
def s_2006(t, fi, u, d):
    ub, uc = Wu(8, 7), Wu(8, 11)
    m = mov(u, [(-0.2, dict(yaw=0.9, al=700)), (0.3, dict(yaw=0.4, al=700)), (ub, dict(yaw=0.4, al=700)),
                (ub + 0.05, dict(yaw=-0.5, al=760)), (uc, dict(yaw=-0.5, al=760)), (uc + 0.05, dict(yaw=0.2, al=820)),
                (6, dict(yaw=0.4, al=830))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.45)
    py = piso(fr) + 160

    def ui(img, fx):
        e = P.entrada(u, -0.28, 0.25, 'desliza')
        veh(img, fx, 'outh', 540 + e['dy'] * 160, py, m['al'], yaw=m['yaw'], pitch=0.15, t=t, alfa=e['alfa'])
        kicker(img, '2006 · BRP', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        M.title(img, fx, [('Revivió', 'sans'), ('en cuatro ruedas.', 'serif')], 220, seg(u, -0.2, 0.15), size=80)
        P.pill_tachada(img, fx, 540, 520, 'BOMBARDIER ATV', eout(seg(u, ub - 0.1, ub + 0.2)), seg(u, uc - 0.4, uc - 0.1), t, size=36)
        pill(img, fx, 540, 610, 'CAN-AM', eout(seg(u, uc - 0.05, uc + 0.25)), size=44, border=CYAN)
        credito(img, CREDITO['outh'], k=seg(u, 0.2, 0.5))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.3), amp=14)


# 9. 2007: el Spyder (foto real en 3D) — dos ruedas adelante y una atrás
def s_spyder(t, fi, u, d):
    ur, us, ud, uu = Wu(9, 6), Wu(9, 8), Wu(9, 10), Wu(9, 14)
    m = mov(u, [(-0.2, dict(yaw=-0.9, al=640)), (0.3, dict(yaw=-0.3, al=640)), (us, dict(yaw=-0.3, al=640)),
                (us + 0.05, dict(yaw=0.5, al=700)), (uu, dict(yaw=0.5, al=700)), (uu + 0.05, dict(yaw=-0.2, al=720)),
                (6, dict(yaw=-0.35, al=730))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.5)
    py = piso(fr) + 170
    land = 0.03

    def ui(img, fx):
        M.cristal(img, fx, 'SPYDER', u, t0=-0.25, cy=0.4, entrada='sube')
        e = P.entrada(u, -0.3, land + 0.3, 'cae')
        r = veh(img, fx, 'spybs', 540, py, m['al'], yaw=m['yaw'], pitch=0.15, t=t, dy=e['dy'] * 240, alfa=e['alfa'])
        if r:
            for j, (px_, py_) in enumerate([(0.57, 0.80), (0.93, 0.60)]):
                x, y = en(r, px_, py_)
                doodle_circle(img, fx, x, y, r[2] * 0.12, r[3] * 0.17, t, k=seg(u, ud - 0.1 + 0.1 * j, ud + 0.25 + 0.1 * j), seed=j + 3)
            x, y = en(r, 0.75, 0.95)
            pill(img, fx, x, y + 60, '2 ADELANTE', eout(seg(u, ud + 0.2, ud + 0.45)), size=30, border=AMARILLO)
            x, y = en(r, 0.15, 0.60)
            doodle_circle(img, fx, x, y, r[2] * 0.09, r[3] * 0.15, t, k=seg(u, uu - 0.1, uu + 0.25), col=CYAN, seed=7)
            pill(img, fx, x + 20, y - r[3] * 0.25, '1 ATRÁS', eout(seg(u, uu + 0.1, uu + 0.35)), size=30, border=CYAN)
        kicker(img, '2007 · CAN-AM SPYDER', 150, seg(u, -0.2, 0.1), col=(150, 210, 230))
        M.title(img, fx, [('Algo', 'sans'), ('rarísimo.', 'serif')], 220, seg(u, ur - 0.1, ur + 0.25), size=86)
        credito(img, CREDITO['spybs'], k=seg(u, land, land + 0.3))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, land - 0.05, 0.35), amp=20)


# 10. ¿te suena? mismo acomodo que la moto de nieve (Ski-Doo arriba, Spyder abajo, las dos fotos reales)
def s_nieve(t, fi, u, d):
    ue, uo = Wu(10, 11), Wu(10, 15)                             # «dos esquís», «una oruga»
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.9)
    yw = 0.5 * math.sin(t * 0.8)

    def ui(img, fx):
        e1 = P.entrada(u, -0.3, 0.25, 'desliza')
        e2 = P.entrada(u, -0.18, 0.25, 'desliza')
        ra = veh(img, fx, 'skidoo', 540 - e1['dy'] * 200, 900, 470, yaw=yw, pitch=0.2, t=t, alfa=e1['alfa'], reflejo=0.12)
        ImageDraw.Draw(img).line([(80, 975), (1000, 975)], fill=M.scale_c(CYAN, 0.5), width=2)
        rb = veh(img, fx, 'spyjb', 540 + e2['dy'] * 200, 1440, 430, yaw=-yw, pitch=0.15, t=t + 1, alfa=e2['alfa'], reflejo=0.12)
        kicker(img, '¿TE SUENA?', 150, seg(u, -0.2, 0.1), col=(150, 210, 230))
        M.title(img, fx, [('Mismo acomodo', 'sans'), ('que la moto de nieve.', 'serif')], 210, seg(u, Wu(10, 3), Wu(10, 3) + 0.35), size=66)
        ke = seg(u, ue - 0.1, ue + 0.3)
        if ra and rb and ke > 0:
            xa, ya = en(ra, 0.17, 0.80)
            xb, yb = en(rb, 0.09, 0.68)
            doodle_circle(img, fx, xa, ya, ra[2] * 0.17, ra[3] * 0.22, t, k=ke, seed=11)
            doodle_circle(img, fx, xb, yb, rb[2] * 0.08, rb[3] * 0.2, t, k=ke, seed=12)
            doodle_arrow(img, fx, xa + 10, ya + 90, xb + 10, yb - 90, t, k=seg(u, ue + 0.1, ue + 0.4))
            pill(img, fx, xa + 260, ya + 30, '2 ESQUÍS', eout(seg(u, ue, ue + 0.3)), size=30, border=AMARILLO)
            pill(img, fx, xb + 250, yb + 10, '2 RUEDAS', eout(seg(u, ue + 0.1, ue + 0.4)), size=30, border=AMARILLO)
        ko = seg(u, uo - 0.1, uo + 0.3)
        if ra and rb and ko > 0:
            xa, ya = en(ra, 0.66, 0.62)
            xb, yb = en(rb, 0.83, 0.79)
            doodle_circle(img, fx, xa, ya, ra[2] * 0.2, ra[3] * 0.16, t, k=ko, col=CYAN, seed=13)
            doodle_circle(img, fx, xb, yb, rb[2] * 0.1, rb[3] * 0.2, t, k=ko, col=CYAN, seed=14)
            doodle_arrow(img, fx, xa, ya + 80, xb - 10, yb - 100, t, k=seg(u, uo + 0.1, uo + 0.4), col=CYAN)
            pill(img, fx, xa - 40, ya - 120, '1 ORUGA', eout(seg(u, uo, uo + 0.3)), size=30, border=CYAN)
            pill(img, fx, xb - 60, yb + 120, '1 RUEDA', eout(seg(u, uo + 0.1, uo + 0.4)), size=30, border=CYAN)
        credito(img, 'FOTOS: DADEROT (CC0) · JOOST J. BAKKER (CC BY 2.0)', k=seg(u, 0.2, 0.5))
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. Ciudad Juárez (Tierra de alambre con pin) → Defender y Maverick reales + contador de 2 millones
def _jrz_tierra(t, fi, u):
    k = P.eout4(seg(u, -0.2, 0.4))
    C = np.array([0.0, 1.0, 0.0])
    spin = SPIN_JZ - 0.6 * (1 - k) + 0.03 * u
    fr = Frame(Cam(target=tuple(C), dist=7.0 - 2.6 * k, yaw=4 * math.sin(t * 0.4), pitch=24, cy=0.56))
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, C, 1.6, spin)
    q = geo(31.7, -106.4, spin, C, 1.6)
    dot3(fr, q, r=10, col=CYAN, a=0.7 + 0.3 * math.sin(t * 8), glow=1.5)
    px, py, _ = fr.cam.p1(tuple(q))

    def ui(img, fx):
        pin(img, fx, px, py, seg(u, 0.2, 1.0), 'CIUDAD JUÁREZ, CHIH.')
        kicker(img, 'HOY · MÉXICO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        M.title(img, fx, [('Muchos se arman', 'sans'), ('en México.', 'serif')], 210, seg(u, 0.3, 0.7), size=78)
    fr.ui.append(ui)
    return finish(fr, fi), (px / 1080, py / 1920)


def _jrz_planta(t, fi, u, u0):
    v = u - u0
    m = mov(v, [(-0.1, dict(yaw=-0.8)), (0.3, dict(yaw=-0.2)), (1.4, dict(yaw=-0.2)), (1.45, dict(yaw=0.6)), (5, dict(yaw=0.7))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.4)
    py = piso(fr) + 290
    un = Wu(11, 12) - u0                                        # «dos millones»
    kn = P.eout4(seg(v, un - 1.0, un + 0.1))

    def ui(img, fx):
        M.cristal(img, fx, 'JUÁREZ', v, t0=0.0, cy=0.36, entrada='golpe')
        e1 = P.entrada(v, 0.05, 0.25, 'pop')
        e2 = P.entrada(v, 0.25, 0.25, 'pop')
        veh(img, fx, 'mavf', 770, py - 40, 470, yaw=m['yaw'], pitch=0.15, t=t, escala=max(0.05, e2['escala']), alfa=e2['alfa'])
        veh(img, fx, 'defr', 320, py + 30, 500, yaw=m['yaw'], pitch=0.15, t=t + 2, escala=max(0.05, e1['escala']), alfa=e1['alfa'])
        n = int(2_000_000 * kn)
        texto_grande(img, fx, f'{n:,}'.replace(',', ' '), 540, 300, 120, col=AMARILLO if kn >= 1 else WHITE, glow=0.4, f='mono')
        kicker(img, 'VEHÍCULOS ARMADOS EN JUÁREZ DESDE 2007', 395, seg(v, 0.1, 0.4), col=(150, 210, 230), size=26)
        kicker(img, 'DEFENDER · MAVERICK · OUTLANDER', 170, seg(v, 0.1, 0.4), col=(200, 200, 210), size=26)
        credito(img, 'FUENTE: BRP, ENE 2026 · FOTOS: AHUNT (CC0) · KARLEHORN (CC BY 3.0)', k=seg(v, 0.3, 0.6))
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(v, un + 0.1, 0.35), amp=16)


def s_juarez(t, fi, u, d):
    u0 = Wu(11, 8)                                             # «de ahí»
    if u < u0 - 0.18:
        return _jrz_tierra(t, fi, u)[0]
    if u >= u0 + 0.14:
        return _jrz_planta(t, fi, u, u0)
    A, (cx, cy) = _jrz_tierra(t, fi, u)
    B = _jrz_planta(t, fi, u, u0)
    return M.tr_zoom_through(A, B, seg(u, u0 - 0.18, u0 + 0.14), cx, cy)


# 12. 2024: de vuelta a dos ruedas… pero eléctricas (sin foto libre de las motos nuevas: rueda y rayo en line-art)
def s_electrica(t, fi, u, d):
    ud, ue = Wu(12, 9), Wu(12, 12)
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)
    ke = seg(u, ue - 0.1, ue + 0.2)

    def ui(img, fx):
        if u >= ue - 0.1:
            M.cristal(img, fx, 'ELÉCTRICA', u, t0=ue - 0.1, cy=0.5, entrada='golpe')
        kw = P.eout4(seg(u, -0.25, 0.35))
        x = lerp(-300, 540, kw)
        rueda(img, fx, x - 230, 1020, 150, -t * 6, kw)
        rueda(img, fx, x + 230, 1020, 150, -t * 6, kw)
        if kw > 0:
            pill(img, fx, 540, 1250, 'DE VUELTA A 2 RUEDAS', eout(seg(u, ud - 0.1, ud + 0.2)), size=34, border=AMARILLO)
        rayo(img, fx, ke, t, cx=540, y0=430, y1=1020)
        P.numero_golpe(img, fx, '2024', 330, seg(u, -0.2, -0.05), size=210, col=WHITE)
        pill(img, fx, 330, 1400, 'CAN-AM PULSE', eout(seg(u, ue + 0.2, ue + 0.45)), size=32, border=CYAN)
        pill(img, fx, 750, 1400, 'CAN-AM ORIGIN', eout(seg(u, ue + 0.3, ue + 0.55)), size=32, border=CYAN)
    fr.ui.append(ui)
    out = finish(fr, fi, flash=0.6 * golpe_k(u, ue, 0.25))
    return sacudir(out, t, golpe_k(u, 0.15, 0.3) + golpe_k(u, ue, 0.35), amp=20)


# 13. le pusieron un número: 73 (de cristal) + la foto de 1973 que cae otra vez
def s_73(t, fi, u, d):
    u7 = Wu(13, 8)
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)

    def ui(img, fx):
        kicker(img, 'EDICIÓN ESPECIAL', 170, seg(u, -0.25, 0.0), col=(150, 210, 230))
        M.title(img, fx, [('Le pusieron', 'sans'), ('un número.', 'serif')], 240, seg(u, -0.25, 0.1), size=82)
        rueda(img, fx, 300, 1100, 120, -t * 4, seg(u, -0.25, 0.0) * (1 - seg(u, u7 - 0.3, u7)))
        rueda(img, fx, 780, 1100, 120, -t * 4, seg(u, -0.25, 0.0) * (1 - seg(u, u7 - 0.3, u7)))
        P.numero_golpe(img, fx, '??', 1100, seg(u, 0.2, 0.35) * (1 - seg(u, u7 - 0.3, u7)), size=200, col=(170, 210, 230))
        if u >= u7 - 0.1:
            M.cristal(img, fx, '73', u, t0=u7 - 0.1, cy=0.5, entrada='zoom', alto=0.5)
            k = seg(u, u7 + 0.35, u7 + 0.7)
            yy = lerp(-500, 1240, P.rebote(k))
            if k > 0:
                F3.dibujar_escena(img, ESC['nara2'], (330, yy - 160, 750, yy + 155), yaw=0.5 * math.sin(t), pitch=0.2, esc=1.14,
                                  marco=10, angulo=6 - 10 * k)
                pill(img, fx, 540, 1470, 'POR 1973, EL AÑO EN QUE NACIÓ', eout(seg(u, u7 + 0.7, u7 + 1.0)), size=30, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u7 + 0.1, 0.35) + golpe_k(u, u7 + 0.7, 0.3), amp=20)


# 14. mándaselo a alguien con un Can-Am (Ryker y Maverick reales)
def s_mandalo(t, fi, u, d):
    m = mov(u, [(-0.2, dict(yaw=0.8)), (0.3, dict(yaw=0.1)), (1.2, dict(yaw=0.1)), (1.25, dict(yaw=-0.6)), (4, dict(yaw=-0.7))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.4)
    py = piso(fr) + 170

    def ui(img, fx):
        e1 = P.entrada(u, -0.3, 0.3, 'cae')
        e2 = P.entrada(u, -0.18, 0.3, 'cae')
        veh(img, fx, 'mavs', 805, py - 70, 400, yaw=m['yaw'], pitch=0.15, t=t, dy=e2['dy'] * 200, alfa=e2['alfa'])
        veh(img, fx, 'irving', 330, py + 30, 600, yaw=m['yaw'], pitch=0.15, t=t + 1, dy=e1['dy'] * 200, alfa=e1['alfa'])
        M.title(img, fx, [('Mándaselo a alguien', 'sans'), ('con un Can-Am.', 'serif')], 210, seg(u, -0.2, 0.15), size=74)
        credito(img, 'FOTOS: ARTAXERXES (CC BY 4.0) · KARLEHORN (CC BY 3.0)', k=seg(u, 0.3, 0.6))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.0, 0.3), amp=16)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55), sfx=[]),
           dict(desde=1, fn=s_quebec, tr='iris', c=(0.5, 0.5), sfx=[]),
           dict(desde=2, fn=s_1973, tr='cristal', palabra='1973', sfx=[]),
           dict(desde=3, fn=s_nombre, tr='rebanadas', sfx=[]),
           dict(desde=4, fn=s_medallas, tr='golpe', sfx=[]),
           dict(desde=5, fn=s_campeones, tr='whip', sfx=[]),
           dict(desde=6, fn=s_caida, tr='rompe', c=(0.5, 0.45), sfx=[]),
           dict(desde=7, fn=s_dormido, tr='remolino', sfx=[]),
           dict(desde=8, fn=s_2006, tr='flash', sfx=[]),
           dict(desde=9, fn=s_spyder, tr='cubo', sfx=[]),
           dict(desde=10, fn=s_nieve, tr='giro', sfx=[]),
           dict(desde=11, fn=s_juarez, tr='zoom', sfx=[]),
           dict(desde=12, fn=s_electrica, tr='glitch', sfx=[]),
           dict(desde=13, fn=s_73, tr='golpe', sfx=[]),
           dict(desde=14, fn=s_mandalo, tr='ritmo', sfx=[]),
           dict(desde=15, loop=True, tr='whip_izq')]


def _sfx_dinamicos():
    E = ESCENAS
    E[0]['sfx'] = [(U_ATERRIZA, 'sub', 1.0), (U_ATERRIZA + 0.02, 'slap', 0.7), (0.23, 'bass', 0.9), (0.3, 'shimmer', 0.4),
                   (Wu(0, 7), 'whoosh', 0.6), (Wu(0, 12) - 0.2, 'scribble', 0.6), (Wu(0, 12) + 0.3, 'tick', 0.6)]
    u0 = Wu(1, 6)
    E[1]['sfx'] = [(0.0, 'whoosh_suave', 0.5), (0.35, 'tick', 0.6), (0.6, 'chime_a', 0.4), (u0 - 0.2, 'whoosh', 0.9),
                   (u0 + 0.1, 'thud', 0.7), (u0 + 0.15, 'cristal', 0.6), (Wu(1, 13), 'whoosh', 0.4), (Wu(1, 8), 'tick', 0.5)]
    z1, z2, ur = Wu(2, 6), Wu(2, 10), Wu(2, 11)
    E[2]['sfx'] = [(0.2, 'shimmer', 0.4), (z1, 'click', 0.9), (z2, 'click', 0.9), (ur, 'tick', 0.6), (Wu(2, 7), 'whoosh_suave', 0.4)]
    uc, um, ua, ub = Wu(3, 9), Wu(3, 10), Wu(3, 11), Wu(3, 16)
    E[3]['sfx'] = [(-0.3 + 0.26 * j + 0.55, 'slap', 0.3) for j in range(10) if -0.3 + 0.26 * j + 0.55 < uc - 0.3] + [(uc - 0.35, 'whoosh_suave', 0.5), (uc - 0.15, 'whoosh', 0.7), (um, 'tick', 0.7), (ua - 0.15, 'whoosh', 0.7), (ua + 0.55, 'bass', 1.0),
                   (ua + 0.6, 'cristal', 0.7), (ub, 'slap', 0.9), (ub + 0.15, 'thud', 0.6)]
    E[4]['sfx'] = [(Wu(4, 3) + 0.1, 'chime_a', 0.8), (Wu(4, 4) + 0.1, 'chime_b', 0.8), (Wu(4, 6) + 0.1, 'chime_c', 0.8),
                   (Wu(4, 3) + 0.15, 'thud', 0.4), (Wu(4, 4) + 0.15, 'thud', 0.4), (Wu(4, 6) + 0.15, 'thud', 0.4)]
    un = Wu(5, 3)
    E[5]['sfx'] = [(0.3, 'slap', 0.9), (un - 0.15, 'whoosh', 0.5), (un, 'bass', 1.0), (Wu(5, 5), 'tick', 0.6)]
    uc, u87, uu = Wu(6, 4), Wu(6, 7), Wu(6, 13)
    E[6]['sfx'] = [(uc - 0.2, 'whoosh_suave', 0.6), (uc + 0.2, 'thud', 0.8), (u87 - 0.05, 'burst', 0.6), (u87, 'sub', 1.0),
                   (u87 + 0.05, 'digital', 0.6), (uu, 'bass', 0.8)]
    d7 = TT(8) - TT(7)
    E[7]['sfx'] = [(0.25 + (d7 - 0.95) * i / 19, 'tick2', 0.3) for i in range(19)] + [(d7 - 0.7, 'chime_c', 0.6)]
    ub, uc = Wu(8, 7), Wu(8, 11)
    E[8]['sfx'] = [(0.0, 'whoosh', 0.7), (ub, 'whoosh', 0.5), (uc - 0.4, 'scribble', 0.6), (uc + 0.05, 'bass', 0.9), (uc + 0.1, 'shimmer', 0.4)]
    ud, uu, us = Wu(9, 10), Wu(9, 14), Wu(9, 8)
    E[9]['sfx'] = [(0.23, 'sub', 1.0), (0.25, 'slap', 0.6), (us, 'whoosh', 0.6), (ud - 0.1, 'scribble', 0.6), (ud + 0.2, 'tick', 0.6),
                   (uu - 0.1, 'scribble', 0.6), (uu + 0.1, 'tick', 0.6)]
    ue, uo = Wu(10, 11), Wu(10, 15)
    E[10]['sfx'] = [(0.0, 'whoosh', 0.6), (0.12, 'whoosh', 0.5), (ue - 0.1, 'scribble', 0.6), (ue + 0.1, 'tick', 0.6),
                    (uo - 0.1, 'scribble', 0.6), (uo + 0.1, 'tick', 0.6)]
    u0, un = Wu(11, 8), Wu(11, 12)
    E[11]['sfx'] = [(0.2, 'tick', 0.6), (0.4, 'chime_a', 0.5), (u0 - 0.2, 'whoosh', 0.9), (u0 + 0.1, 'thud', 0.6), (u0 + 0.12, 'cristal', 0.5),
                    (u0 + 0.05, 'whoosh', 0.4), (u0 + 0.25, 'whoosh', 0.4)] + \
                   [(un - 1.0 + 0.08 * i, 'tick2', 0.22) for i in range(13)] + [(un + 0.1, 'bass', 1.0), (un + 0.15, 'chime_c', 0.6)]
    ud, ue = Wu(12, 9), Wu(12, 12)
    E[12]['sfx'] = [(-0.2, 'bass', 0.9), (-0.2, 'whoosh', 0.6), (ud - 0.2, 'whoosh', 0.6), (ue - 0.1, 'burst', 0.7), (ue, 'sub', 1.0), (ue + 0.05, 'digital', 0.5),
                    (ue + 0.25, 'tick', 0.5), (ue + 0.35, 'tick', 0.5)]
    u7 = Wu(13, 8)
    E[13]['sfx'] = [(0.05, 'whoosh_suave', 0.5), (u7 + 0.1, 'bass', 1.0), (u7 + 0.65, 'slap', 0.8), (u7 + 0.8, 'tick', 0.5)]
    E[14]['sfx'] = [(0.2, 'sub', 0.8), (0.35, 'sub', 0.6), (1.25, 'whoosh', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
