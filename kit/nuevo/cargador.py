"""Reel diario: «Tu cargador sin celular… ¿gasta luz?» (Mito o realidad). Lun 9-nov-2026, 19:00. Voz Isaac. Estilo rápido.
Inicio tipo 6 (pantalla dividida: arriba el cargador conectado sin celular, abajo la tele «apagada» con su lucecita roja;
las dos mitades chocan con golpe y el título cae en la unión). Datos: en la UE (Reglamento 2019/1782, desde abr-2020) un
cargador CA-CC de hasta 49 W puede gastar en vacío máximo 0.10 W; la CFE estima (82 000 diagnósticos, vía Luz Noticias y
El Imparcial, jul-2026) que en espera un cargador gasta ~2.3 kWh al año y una tele ~45.1 kWh (microondas 27, estéreo 14.5)
y que lo que se queda en espera es ~11 % del consumo de una casa; tarifa 1 de CFE, consumo básico ≈ $1.125 por kWh
(jun-2026, UnoTV) → cargador < $3 y tele ≈ $50 al año. Regleta con apagador: consejo de la CFE. Tibio = gasta (calor = energía
perdida). Cargador, tele, decodificador, micro, estéreo, regleta y monedas: RECREACIÓN sin marcas. Fuentes en
guiones/2026-11-09_cargador.txt."""
import math, os, re, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'cargador'
TXT = ['Tu cargador sin celular… ¿gasta luz?',
       'Casi nada. El que sí gasta está en tu sala.',
       'Un cargador moderno casi se apaga solo cuando no hay nada conectado.',
       'En Europa, la ley le permite máximo 0.1 watts.',
       'La CFE calcula que gasta unos 2 kWh al año: menos de $3.',
       'Ahora mira tu tele «apagada»: la lucecita roja sigue prendida.',
       'En espera, gasta unos 45 kWh al año.',
       'Unos $50: 20 veces más que tu cargador.',
       'Y aquí está el error: desconectas el cargador… y dejas todo lo demás enchufado.',
       'El decodificador, el micro con su reloj, el estéreo: todos esperando.',
       'Según la CFE, lo que se queda en espera es como el 11% de lo que gasta una casa.',
       'El truco: conéctalos a una regleta con apagador.',
       'Un clic en la noche… y se apagan de verdad.',
       '¿Y el cargador? Si está tibio sin celular, ese sí desconéctalo.',
       'Mándaselo a quien desconecta el cargador y deja la tele enchufada.',
       'Y la próxima vez que te pregunten:']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-09_cargador_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)

AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 50, 40)
ORO = (214, 170, 80)
GRIS = (150, 150, 160)


# ================================================================== utilidades
def _pal(i):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split()


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


_W = []


def _words():
    if not _W:
        f = f'/home/claude/words_{TEMA}.json'
        if os.path.exists(f):
            d = json.load(open(f))
            d = d.get('words', d) if isinstance(d, dict) else d
            _W.extend(w for w in d if w.get('type', 'word') == 'word' and not w['text'].startswith('['))
    return _W


def wt(i, k):
    n = len(_pal(i))
    k = max(0, min(k, n - 1))
    W = _words()
    if len(W) == sum(len(_pal(j)) for j in range(len(VOZ))):
        n0 = sum(len(_pal(j)) for j in range(i))
        return W[n0 + k]['start'] - W[n0]['start']
    return (TE(i) - TT(i)) * k / n


def cam(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch=8, tx=0.0, ty=0.0, tz=0.0, roll=0.0):
    return (u, dict(tx=tx, ty=ty, tz=tz, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def check(img, fx, x, y, k, txt, col=VERDE):
    pill(img, fx, x, y, '✓ ' + txt, eout(k), size=36, border=col)


def tache(img, fx, x, y, k, txt):
    pill(img, fx, x, y, '✗ ' + txt, eout(k), size=36, border=ROJO, col=(255, 200, 196))


def texto(img, fx, x, y, txt, size, col, k=1.0, glow=0.45, f='sansx', anchor='mm'):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, k), anchor=anchor)
    ImageDraw.Draw(fx).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, glow * k), anchor=anchor)


def flat(m, glow=None):
    m.flat = True
    if glow is not None:
        m.glow = glow
    return m


# ================================================================== objetos (RECREACIÓN, sin marcas)
_IM = {}


def _decal_img(key, w, h, dib):
    if key not in _IM:
        im = Image.new('RGB', (w, h), (0, 0, 0))
        dib(ImageDraw.Draw(im), im)
        _IM[key] = im.convert('RGBA')
    return _IM[key]


def pared(t=(0, 0, 0), w=3.2, h=2.4, contacto=(0, 0.9)):
    """Pared clara (plano vertical en z=0, viendo a +z) con un contacto doble."""
    ms = [named(M3.box(w, h, 0.06, (54, 54, 58), shadow=0, base=True, gloss=0.05).tf(t=(0, 0, -0.03)), 'pared', rim=0.2, gloss=0.05)]
    cx, cy = contacto
    ms.append(named(M3.rbox(0.42, 0.03, 0.62, 0.04, (232, 230, 224), n=3, shadow=0, gloss=0.3).tf(rx=90, t=(cx, cy, 0.0)), 'placa',
                    rim=0.4))
    for dy in (0.14, -0.14):
        for dx in (-0.045, 0.045):
            ms.append(flat(named(M3.box(0.025, 0.08, 0.01, (20, 20, 22), shadow=0, base=False).tf(t=(cx + dx, cy + dy, 0.035)), 'ranura')))
    return P.tfk(ms, t=t)


def cargador(t=(0, 0, 0), s=1.0, ry=0.0, rx=0.0, interior=False, led=0.0):
    """Cargador de cubo blanco (sin marcas) con puerto USB-C al frente (+z) y patas atrás."""
    ms = [named(M3.rbox(0.42, 0.42, 0.36, 0.06, (236, 236, 238), n=4, shadow=0, gloss=0.35, base=False), 'cargador', rim=0.5, gloss=0.35)]
    ms[0] = ms[0].tf(rx=90)
    ms[0].name, ms[0].rim, ms[0].gloss = 'cargador', 0.5, 0.35
    ms.append(flat(named(M3.box(0.12, 0.04, 0.01, (24, 24, 26), shadow=0, base=False).tf(t=(0, -0.05, 0.215)), 'puerto')))
    for dx in (-0.06, 0.06):
        ms.append(named(M3.box(0.025, 0.07, 0.16, (200, 200, 206), shadow=0, base=False, gloss=0.9).tf(t=(dx, 0.04, -0.25)), 'pata', gloss=0.9))
    if led > 0.01:
        ms.append(flat(named(M3.box(0.03, 0.03, 0.01, (120, 255, 160), shadow=0, base=False).tf(t=(0.13, 0.12, 0.215)), 'led'),
                       glow=M.scale_c((120, 255, 160), led)))
    if interior:
        ms.append(named(M3.box(0.34, 0.02, 0.28, (30, 110, 60), shadow=0, base=False).tf(t=(0, -0.15, 0)), 'in'))
        ms.append(named(M3.box(0.14, 0.13, 0.12, (220, 190, 60), shadow=0, base=True, gloss=0.4).tf(t=(-0.06, -0.14, -0.02)), 'in'))
        for i in range(2):
            ms.append(named(M3.cyl(0.035, 0.14, (40, 60, 140), n=12, shadow=0, gloss=0.7, y0=-0.14).tf(t=(0.1, 0, -0.08 + 0.09 * i)), 'in'))
        ms.append(named(M3.box(0.07, 0.02, 0.07, (18, 18, 20), shadow=0, base=True, gloss=0.6).tf(t=(0.08, -0.14, 0.09)), 'in'))
    return P.tfk(ms, s=s, rx=rx, ry=ry, t=t)


def cable(fr, a, b, caida=0.5, col=(232, 232, 236), w=4, a_=1.0):
    a, b = np.asarray(a, float), np.asarray(b, float)
    pts = [a + (b - a) * s_ - np.array([0, caida * math.sin(math.pi * s_), 0]) for s_ in np.linspace(0, 1, 24)]
    line3(fr, pts, col=col, w=w, a=a_, glow=0.15)


def _pant_tele(estado):
    def dib(d, im):
        w, h = im.size
        if estado == 'negro':
            for i in range(h):
                v = int(30 + 22 * (i / h))
                d.line([(0, i), (w, i)], fill=(v - 4, v, v + 6))
            d.polygon([(w * 0.52, 0), (w * 0.78, 0), (w * 0.38, h), (w * 0.12, h)], fill=(70, 74, 82))
            d.rectangle((0, 0, w - 1, h - 1), outline=(120, 124, 132), width=3)
        else:
            d.rectangle((0, 0, w, h), fill=(30, 60, 90))
    return _decal_img(('tele', estado), 640, 360, dib)


def tele(t=(0, 0, 0), s=1.0, ry=0.0, led=1.0, prendida=False):
    """Pantalla plana de pie (sin marcas) con lucecita roja de espera abajo a la derecha."""
    marco = named(M3.box(2.4, 1.4, 0.08, (52, 52, 58), shadow=0, base=True, gloss=0.6).tf(t=(0, 0.42, 0)), 'tele', rim=0.9, gloss=0.6)
    M3.decal(marco, marco.FACE['front'], _pant_tele('prendida' if prendida else 'negro'))
    ms = [marco,
          named(M3.box(0.12, 0.42, 0.06, (40, 40, 44), shadow=0, base=True, gloss=0.5).tf(t=(0, 0.0, -0.04)), 'pie', rim=0.5),
          named(M3.box(0.9, 0.03, 0.4, (40, 40, 44), shadow=0, base=True, gloss=0.5), 'base', rim=0.5)]
    if led > 0.01:
        ms.append(flat(named(M3.box(0.04, 0.025, 0.01, ROJO, shadow=0, base=False).tf(t=(1.05, 0.46, 0.045)), 'led'),
                       glow=M.scale_c(ROJO, led)))
    return P.tfk(ms, s=s, ry=ry, t=t)


def deco(t=(0, 0, 0), s=1.0, ry=0.0, led=1.0):
    m = named(M3.rbox(0.9, 0.16, 0.6, 0.04, (22, 22, 24), n=3, shadow=0, gloss=0.6), 'deco', rim=0.6, gloss=0.6)
    ms = [m, flat(named(M3.box(0.22, 0.06, 0.01, (40, 10, 10), shadow=0, base=False).tf(t=(0.15, 0.08, 0.305)), 'disp'),
                  glow=M.scale_c((255, 60, 40), 0.5 * led))]
    if led > 0.01:
        ms.append(flat(named(M3.box(0.03, 0.03, 0.01, ROJO, shadow=0, base=False).tf(t=(-0.32, 0.08, 0.305)), 'led'), glow=M.scale_c(ROJO, led)))
    return P.tfk(ms, s=s, ry=ry, t=t)


def _disp_micro(on):
    def dib(d, im):
        d.rectangle((0, 0, im.size[0], im.size[1]), fill=(6, 10, 8))
        if on:
            d.text((im.size[0] / 2, im.size[1] / 2), '12:00', font=M.font('mono', 70), fill=(110, 255, 150), anchor='mm')
    return _decal_img(('micro', on), 260, 110, dib)


def micro(t=(0, 0, 0), s=1.0, ry=0.0, on=1.0):
    cuerpo = named(M3.rbox(1.2, 0.68, 0.8, 0.05, (190, 192, 196), n=3, shadow=0, gloss=0.5), 'micro', rim=0.5, gloss=0.5)
    puerta = named(M3.box(0.78, 0.5, 0.02, (16, 18, 20), shadow=0, base=True, gloss=0.9).tf(t=(-0.17, 0.09, 0.41)), 'puerta', gloss=0.9)
    disp = named(M3.box(0.26, 0.11, 0.02, (6, 10, 8), shadow=0, base=True).tf(t=(0.4, 0.45, 0.41)), 'disp')
    M3.decal(disp, disp.FACE['front'], _disp_micro(on > 0.5))
    if on > 0.5:
        disp.glow = (40, 110, 60)
    return P.tfk([cuerpo, puerta, disp], s=s, ry=ry, t=t)


def estereo(t=(0, 0, 0), s=1.0, ry=0.0, led=1.0):
    ms = [named(M3.rbox(1.0, 0.36, 0.5, 0.04, (34, 34, 38), n=3, shadow=0, gloss=0.4), 'estereo', rim=0.6)]
    for x in (-0.3, 0.3):
        ms.append(named(M3.cyl(0.13, 0.03, (70, 70, 76), n=20, shadow=0, gloss=0.3).tf(rx=90, t=(x, 0.18, 0.25)), 'bocina'))
    if led > 0.01:
        ms.append(flat(named(M3.box(0.03, 0.03, 0.01, ROJO, shadow=0, base=False).tf(t=(0.0, 0.08, 0.255)), 'led'), glow=M.scale_c(ROJO, led)))
    return P.tfk(ms, s=s, ry=ry, t=t)


def sofa(t=(0, 0, 0), s=1.0, ry=0.0):
    col = (88, 74, 66)
    ms = [named(M3.rbox(2.4, 0.45, 0.9, 0.12, col, n=4, shadow=0, gloss=0.1), 'sofa', rim=0.4, gloss=0.1),
          named(M3.rbox(2.4, 0.55, 0.25, 0.1, col, n=4, shadow=0, gloss=0.1).tf(t=(0, 0.45, -0.33)), 'sofa', rim=0.4, gloss=0.1)]
    for x in (-1.12, 1.12):
        ms.append(named(M3.rbox(0.22, 0.65, 0.9, 0.08, col, n=3, shadow=0, gloss=0.1).tf(t=(x, 0, 0)), 'sofa', rim=0.4))
    return P.tfk(ms, s=s, ry=ry, t=t)


def mueble(t=(0, 0, 0), s=1.0):
    return P.tfk([named(M3.box(3.0, 0.5, 0.7, (96, 70, 50), shadow=0, base=True, gloss=0.25), 'mueble', rim=0.4)], s=s, t=t)


def moneda(t=(0, 0, 0), s=1.0, rx=0.0):
    return [named(M3.cyl(0.2, 0.05, ORO, n=22, top=(232, 196, 110), shadow=0, gloss=0.9).tf(s=s, rx=rx, t=t), 'moneda', rim=0.6, gloss=0.9)]


def pila_monedas(n, x, k=1.0, s=1.0):
    ms = []
    for i in range(int(n * clamp(k))):
        ms += moneda(t=(x + 0.012 * math.sin(i * 2.1), i * 0.052 * s, 0.01 * math.cos(i * 1.3)), s=s)
    return ms


def regleta(t=(0, 0, 0), s=1.0, ry=0.0, on=1.0):
    ms = [named(M3.rbox(1.8, 0.14, 0.38, 0.06, (178, 178, 176), n=3, shadow=0, gloss=0.3), 'regleta', rim=0.4, gloss=0.3)]
    for i in range(4):
        x = -0.5 + 0.32 * i
        ms.append(flat(named(M3.box(0.16, 0.01, 0.2, (40, 40, 44), shadow=0, base=True).tf(t=(x, 0.14, 0)), 'toma')))
    col = (255, 60, 50) if on > 0.5 else (90, 30, 30)
    sw = named(M3.box(0.2, 0.06, 0.22, col, shadow=0, base=True, gloss=0.7).tf(rx=-12 if on > 0.5 else 12, t=(0.72, 0.14, 0)), 'switch',
               rim=0.5, gloss=0.7)
    if on > 0.5:
        sw.glow = (140, 30, 24)
    ms.append(sw)
    return P.tfk(ms, s=s, ry=ry, t=t)


def flujo(fr, t, pts, k=1.0, col=(255, 200, 90), n=10, vel=1.2):
    """Puntitos de energía que corren por un cable (lista de puntos 3D)."""
    if k <= 0.01:
        return
    A = np.asarray(pts, float)
    L = np.cumsum(np.r_[0, np.linalg.norm(np.diff(A, axis=0), axis=1)])
    for j in range(n):
        q = ((t * vel + j / n) % 1.0) * L[-1]
        i = max(0, min(np.searchsorted(L, q) - 1, len(A) - 2))
        f = (q - L[i]) / max(1e-6, L[i + 1] - L[i])
        dot3(fr, A[i] + (A[i + 1] - A[i]) * f, r=5, col=col, a=k, glow=1.3)


def _cable_pts(a, b, caida=0.5):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return [a + (b - a) * s_ - np.array([0, caida * math.sin(math.pi * s_), 0]) for s_ in np.linspace(0, 1, 24)]


def sala(fr, t, leds=1.0, flujo_k=0.0, regleta_on=None):
    """Sala con mueble, tele, decodificador, estéreo y sofá enfrente (lucecitas rojas de espera)."""
    ms = mueble(t=(0, 0, 0)) + tele(t=(0, 0.5, -0.1), led=leds) + deco(t=(-0.95, 0.5, 0.05), s=0.8, led=leds) + \
        estereo(t=(1.0, 0.5, 0.05), s=0.8, led=leds)
    if regleta_on is not None:
        ms += regleta(t=(0.2, 0.0, 0.75), s=0.7, on=regleta_on)
    draw_objects(fr, ms)
    if flujo_k > 0.01:
        for x0 in (-0.95, 0.0, 1.0):
            flujo(fr, t, _cable_pts((x0, 0.5, -0.2), (0.0, 0.05, 0.75), 0.1), k=flujo_k, n=6, vel=0.9)


# ================================================================== escenas
# 0. gancho, inicio tipo 6: pantalla dividida que choca (arriba el cargador solo, abajo la tele en espera)
UJ = 0.1            # las mitades chocan


def _mitad_cargador(t, fi, u):
    fr = Frame(Cam(target=(0.0, 0.92, 0.0), dist=2.4 + 0.1 * math.sin(t * 0.7), yaw=-24 + 6 * math.sin(t * 0.5), pitch=6, cy=0.27))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'LUZ', u, t0=-2.0, cy=0.24, alto=0.3, entrada='golpe')
    draw_objects(fr, pared(contacto=(0, 0.9)) + cargador(t=(0, 0.83, 0.33), led=0.6 + 0.4 * math.sin(t * 3)))
    cable(fr, (0, 0.78, 0.52), (0.5, 0.15, 0.6), caida=0.15)

    def ui(img, fx):
        pill(img, fx, 540, 180, 'CARGADOR SIN CELULAR', 1.0, size=30, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def _mitad_tele(t, fi, u):
    fr = Frame(Cam(target=(0.2, 1.5, 0.0), dist=4.0, yaw=18 + 5 * math.sin(t * 0.6), pitch=4, cy=0.74))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    draw_objects(fr, mueble(t=(0, 0, 0)) + tele(t=(0, 0.5, 0), led=0.75 + 0.25 * math.sin(t * 4)))
    pl = fr.cam.p1((1.05, 0.96, 0.05))

    def ui(img, fx):
        r = 26 + 6 * math.sin(t * 4)
        ImageDraw.Draw(fx).ellipse((pl[0] - r, pl[1] - r, pl[0] + r, pl[1] + r), fill=(150, 20, 16))
        pill(img, fx, 540, 1470, 'TELE «APAGADA»', 1.0, size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_gancho(t, fi, u, d):
    A = _mitad_cargador(t, fi, u)
    B = _mitad_tele(t, fi, u)
    k = P.eout4(seg(u, UJ - 0.12, UJ))                       # 0 = separadas (con hueco), 1 = chocan
    gap = int(70 * (1 - k)) if u < UJ + 0.01 else 0
    out = np.zeros_like(A)
    h = 960
    out[:h - gap] = A[gap:h]
    out[h + gap:] = B[h:2 * h - gap]
    im = Image.fromarray(out)
    d = ImageDraw.Draw(im)
    fx = Image.new('RGB', im.size, (0, 0, 0))
    lw = 4 if u >= UJ else 3
    d.line([(0, h), (1080, h)], fill=(235, 240, 255), width=lw)
    ImageDraw.Draw(fx).line([(0, h), (1080, h)], fill=(120, 140, 160), width=14)
    kicker(im, 'MITO O REALIDAD', 70, 1.0, col=AMARILLO, size=30)
    P.titulo_golpe(im, fx, [('Tu cargador sin celular…', 'sans'), ('¿gasta luz?', 'serif')], 880, seg(u, UJ, UJ + 0.15), size=70)
    small = fx.resize((270, 480), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((1080, 1920), Image.BILINEAR)
    o = np.asarray(im, np.float32) + np.asarray(small, np.float32) * 0.8 + np.asarray(fx, np.float32) * 0.4
    o = o.clip(0, 255).astype(np.uint8)
    if u >= UJ:
        o = (o.astype(np.float32) + 120 * golpe_k(u, UJ, 0.18)).clip(0, 255).astype(np.uint8)
    return sacudir(o, t, golpe_k(u, UJ, 0.4), amp=28)


# 1. casi nada (medidor en el enchufe: 0.0x W) → el que sí gasta está en tu sala (la cámara sale volando a la sala)
def _pant_medidor(w):
    def dib(d, im):
        d.rectangle((0, 0, im.size[0], im.size[1]), fill=(170, 196, 160))
        d.text((im.size[0] - 20, im.size[1] / 2), f'{w:.2f} W', font=M.font('mono', 64), fill=(20, 30, 20), anchor='rm')
    return _decal_img(('med', round(w, 2)), 320, 120, dib)


def medidor(t=(0, 0, 0), w=0.05):
    b = named(M3.rbox(0.5, 0.32, 0.7, 0.06, (230, 230, 228), n=3, shadow=0, gloss=0.3, base=False).tf(rx=90), 'medidor', rim=0.5)
    lcd = named(M3.box(0.36, 0.14, 0.01, (170, 196, 160), shadow=0, base=False).tf(t=(0, 0.14, 0.165)), 'lcd')
    M3.decal(lcd, lcd.FACE['front'], _pant_medidor(w))
    lcd.glow = (30, 40, 28)
    return P.tfk([b, lcd], t=t)


def s_casinada(t, fi, u, d):
    us = wt(1, 2) - 0.15                          # «El que sí gasta…»
    if u < us:
        fr = Frame(cam(u, [K(-0.4, 1.6, 40, 10, ty=0.85), K(0.25, 2.1, 10, 4, ty=0.85), K(3.0, 2.0, 6, 4, ty=0.85)], cy=0.5))
        space(fr, t, floor=None, bokeh=1.0, beam=0.4)
        w = 0.05 + 0.01 * math.sin(t * 5)
        draw_objects(fr, pared(contacto=(0, 0.9)) + medidor(t=(0, 0.9, 0.17), w=w) +
                     cargador(t=(0, 0.83, 0.33 + 0.16 + 0.16), led=0.8))
        cable(fr, (0, 0.78, 0.84), (0.5, 0.15, 0.9), caida=0.15)

        def ui(img, fx):
            kicker(img, 'MEDIDOR DE CONSUMO · EJEMPLO', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
            check(img, fx, 540, 1430, seg(u, 0.1, 0.35), 'CASI NADA')
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.25), amp=10)
    v = u - us
    k = P.eout4(seg(v, 0.0, 0.5))
    fr = Frame(Cam(target=(0, 0.75, 0.6), dist=lerp(1.0, 5.6, k), yaw=lerp(0, 24, k), pitch=lerp(4, 18, k), cy=0.52))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    sala(fr, t, leds=1.0)
    out = finish(fr, fi)
    if k < 0.95:
        out = M.radial_blur(out, 0.15 * (1 - k), 0.5, 0.45)

    def lab():
        im = Image.fromarray(out)
        fx = Image.new('RGB', im.size, (0, 0, 0))
        pill(im, fx, 540, 1430, 'TU SALA', eout(seg(v, 0.4, 0.7)), size=36, border=ROJO)
        return np.asarray(im)
    return sacudir(lab(), t, golpe_k(v, 0.45, 0.3), amp=14)


# 2. un cargador moderno casi se apaga solo cuando no hay nada conectado (rayos X: el chip se duerme)
def s_rayosx(t, fi, u, d):
    ua = wt(2, 3) - 0.1                           # «casi se apaga solo»
    fr = Frame(cam(u, [K(-0.4, 0.9, 20, 10, ty=0.0), K(0.25, 1.35, -30, 16, ty=0.0), K(ua, 1.15, 26, 12, ty=0.0), K(4.0, 1.1, 30, 12, ty=0.0)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    xr = seg(u, -0.2, 0.15)
    dormido = seg(u, ua, ua + 0.5)
    draw_objects(fr, cargador(interior=True, led=1 - dormido, ry=10 * math.sin(t * 0.8)), xray=xr, keep=('in',))
    pc = fr.cam.p1((0.08, -0.12, 0.09))
    if dormido < 0.99:
        for j in range(8):                        # chispa de corriente que da vueltas mientras está «despierto»
            a0 = t * 6 + j * 0.8
            dot3(fr, (0.08 + 0.12 * math.cos(a0), -0.1, 0.09 + 0.12 * math.sin(a0)), r=3, col=AMARILLO, a=1 - dormido, glow=1.2)

    def ui(img, fx):
        kicker(img, 'RAYOS X · CARGADOR', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        pill(img, fx, pc[0] + 120, pc[1] - 170, 'CHIP DE CONTROL', eout(seg(u, 0.2, 0.5)), size=30, border=CYAN)
        if u > ua:
            pill(img, fx, 540, 1430, 'MODO ESPERA', eout(seg(u, ua + 0.3, ua + 0.6)), size=36, border=GRIS)
            texto(img, fx, pc[0] + 150, pc[1] - 60 - 30 * ((t * 1.2) % 1.0), 'z', 60, (180, 200, 220), dormido * (1 - (t * 1.2) % 1.0))
            texto(img, fx, pc[0] + 190, pc[1] - 110 - 30 * ((t * 1.2 + 0.5) % 1.0), 'Z', 80, (180, 200, 220), dormido * (1 - (t * 1.2 + 0.5) % 1.0))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.3, 0.25), amp=10)


# 3. en Europa, la ley le permite máximo 0.1 watts (palabra de cristal «0.1 W» y aguja que casi no se mueve)
def s_europa(t, fi, u, d):
    um = wt(3, 5) - 0.1                           # «máximo»
    fr = Frame(cam(u, [K(-0.4, 2.6, -50, 20, ty=0.3), K(0.3, 2.2, -14, 12, ty=0.3), K(um, 2.0, 16, 10, ty=0.3), K(4.0, 1.95, 20, 10, ty=0.3)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, '0.1 W', u, t0=um - 0.05, cy=0.4, entrada='zoom')
    e = P.entrada(u, -0.3, 0.3, 'pop')
    draw_objects(fr, cargador(t=(0, 0.21, 0), s=max(0.05, e['escala']) * 1.1, ry=-25 + 8 * t, led=0.0))

    def ui(img, fx):
        kicker(img, 'REGLAMENTO UE 2019/1782 · DESDE 2020', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        cx, cy, r = 540, 1300, 170
        d_ = ImageDraw.Draw(img)
        d_.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=(200, 200, 210), width=6)
        for i in range(6):
            a = math.radians(200 + 28 * i)
            d_.line([(cx + (r - 18) * math.cos(a), cy + (r - 18) * math.sin(a)), (cx + r * math.cos(a), cy + r * math.sin(a))], fill=(200, 200, 210), width=4)
        a = math.radians(203 + 2 * math.sin(t * 7))
        d_.line([(cx, cy), (cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a))], fill=ROJO, width=6)
        ImageDraw.Draw(fx).line([(cx, cy), (cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a))], fill=(120, 20, 20), width=14)
        d_.text((cx, cy + 40), 'WATTS', font=M.font('mono', 30), fill=(180, 180, 190), anchor='mm')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.25, 0.3), amp=14)


# 4. la CFE calcula que gasta unos 2 kWh al año: menos de $3 (contador de un año + 3 monedas que caen)
def s_pesos(t, fi, u, d):
    uk = wt(4, 5) - 0.1                           # «dos kilowatts-hora»
    up = wt(4, 10) - 0.1                          # «menos de tres pesos»
    fr = Frame(cam(u, [K(-0.4, 3.0, 40, 30, ty=0.2), K(0.3, 2.6, 10, 24, ty=0.2), K(up, 2.2, -16, 20, ty=0.2), K(5.0, 2.15, -20, 20, ty=0.2)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    ms = cargador(t=(-0.45, 0.17, 0), s=0.9, ry=20)
    for i in range(3):
        e = P.entrada(u, up + 0.12 * i, 0.3, 'cae')
        if u > up + 0.12 * i - 0.05:
            ms += moneda(t=(0.4 + 0.02 * i, 0.052 * i - e['dy'] * 0.5, 0.1))
    draw_objects(fr, ms)
    kwh = 2.3 * P.eout4(seg(u, uk - 0.3, uk + 0.6))
    dia = int(365 * P.eout4(seg(u, 0.0, uk + 0.6)))

    def ui(img, fx):
        kicker(img, 'CFE · CARGADOR CONECTADO TODO EL AÑO', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        texto(img, fx, 540, 330, f'{kwh:.1f} kWh', 120, WHITE)
        kicker(img, f'DÍA {max(1, dia)} DE 365', 430, 1.0, col=(180, 180, 190), size=28)
        if u > up + 0.3:
            pill(img, fx, 540, 1430, 'MENOS DE $3 AL AÑO', eout(seg(u, up + 0.3, up + 0.55)), size=36, border=VERDE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, sum(golpe_k(u, up + 0.12 * i + 0.15, 0.2) for i in range(3)), amp=10)


# 5. ahora mira tu tele «apagada»: la lucecita roja sigue prendida (crash zoom a la lucecita con REC)
def s_lucecita(t, fi, u, d):
    ul = wt(5, 6) - 0.1                           # «la lucecita roja»
    fr = Frame(cam(u, [K(-0.4, 4.4, -40, 10, ty=1.1), K(0.3, 3.6, -12, 6, ty=1.1), K(5.0, 3.5, -8, 6, ty=1.1)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    led = 0.75 + 0.25 * math.sin(t * 4)
    draw_objects(fr, mueble() + tele(t=(0, 0.5, 0), led=led))
    pl = fr.cam.p1((1.05, 0.96, 0.05))

    def ui(img, fx):
        kicker(img, 'TELE «APAGADA»', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        r = 30 + 8 * math.sin(t * 4)
        ImageDraw.Draw(fx).ellipse((pl[0] - r, pl[1] - r, pl[0] + r, pl[1] + r), fill=(170, 24, 18))
        if u > ul + 0.4:
            doodle_circle(img, fx, pl[0], pl[1], 70, 60, t, k=eout(seg(u, ul + 0.4, ul + 0.8)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    out = finish(fr, fi)
    z = 1.0 if u < ul else (1.6 if u < ul + 0.8 else 2.4)
    if z > 1.0:
        out = M.scale_about(out, z, pl[0] / 1080, pl[1] / 1920)
        im = Image.fromarray(out)
        rec_frame(im, t, 1.0, zoom_label=f'x{z:.1f}')
        fx = Image.new('RGB', im.size, (0, 0, 0))
        pill(im, fx, 540, 1430, 'SIGUE PRENDIDA', eout(seg(u, ul + 0.2, ul + 0.5)), size=36, border=ROJO)
        out = np.asarray(im)
    return sacudir(out, t, golpe_k(u, ul, 0.2) + golpe_k(u, ul + 0.8, 0.2), amp=10)


# 6. en espera, gasta unos 45 kWh al año (energía que corre del contacto a la tele + «45 kWh» de cristal)
def s_45(t, fi, u, d):
    u45 = wt(6, 4) - 0.15                         # «cuarenta y cinco»
    fr = Frame(cam(u, [K(-0.4, 2.0, 50, 20, ty=0.9, tx=1.0), K(0.3, 4.2, 20, 12, ty=0.8), K(u45, 3.8, -14, 10, ty=0.8), K(5.0, 3.7, -18, 10, ty=0.8)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    M.cristal(fr.base, fr.fx, '45 kWh', u, t0=u45, cy=0.3, entrada='golpe')
    draw_objects(fr, mueble() + tele(t=(0, 0.5, 0), led=0.8 + 0.2 * math.sin(t * 4)) + pared(t=(1.9, 0, -0.4), w=1.0, h=1.6, contacto=(0, 0.4)))
    pts = _cable_pts((1.9, 0.4, -0.32), (0.3, 0.95, -0.05), 0.35)
    line3(fr, pts, col=(70, 70, 76), w=4, a=1.0, glow=0.1)
    flujo(fr, t, pts, k=seg(u, -0.2, 0.3), n=12, vel=1.4)
    kwh = int(45 * P.eout4(seg(u, u45 - 0.6, u45 + 0.2)))

    def ui(img, fx):
        kicker(img, 'CFE · TELE EN ESPERA · AL AÑO', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if u < u45 + 0.2:
            texto(img, fx, 540, 1250, f'{kwh} kWh', 110, AMARILLO, seg(u, u45 - 0.7, u45 - 0.5))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u45 + 0.3, 0.35), amp=18)


# 7. unos $50: 20 veces más que tu cargador (duelo de pilas de monedas: 3 contra 50)
def s_20(t, fi, u, d):
    uv = wt(7, 2) - 0.15                          # «veinte veces»
    fr = Frame(cam(u, [K(-0.4, 4.2, -40, 16, ty=1.0), K(0.3, 4.6, -8, 12, ty=1.1), K(uv, 4.9, 14, 10, ty=1.2), K(4.0, 4.8, 18, 10, ty=1.2)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    kc = P.eout4(seg(u, -0.3, uv + 0.2))
    ms = pila_monedas(3, -0.9, 1.0) + pila_monedas(50, 0.9, kc) + cargador(t=(-0.9, 0.11, 0.6), s=0.6) + tele(t=(0.9, 0.0, -0.9), s=0.45, led=1.0)
    draw_objects(fr, ms)
    pa, pb = fr.cam.p1((-0.9, 0.3, 0)), fr.cam.p1((0.9, 50 * 0.052 * kc + 0.15, 0))

    def ui(img, fx):
        kicker(img, 'AL AÑO · CONSUMO BÁSICO CFE', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        pill(img, fx, pa[0], pa[1] - 160, 'CARGADOR $3', 1.0, size=30, border=VERDE, dot=False)
        pill(img, fx, pb[0], pb[1] - 60, f'TELE ${int(50 * kc)}', 1.0, size=30, border=ROJO, dot=False)
        if u > uv:
            P.numero_golpe(img, fx, '20×', 420, seg(u, uv, uv + 0.18), size=230, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uv + 0.18, 0.35), amp=22)


# 8. segundo gancho: el error → desconectas el cargador (sale volando, «✓») y dejas todo lo demás enchufado (ERROR)
def s_error(t, fi, u, d):
    ud = wt(8, 5) - 0.1                           # «desconectas»
    uy = wt(8, 8) - 0.1                           # «y dejas todo lo demás»
    if u < uy:
        fr = Frame(cam(u, [K(-0.4, 2.6, 30, 8, ty=0.85), K(0.25, 2.2, -10, 6, ty=0.85), K(uy, 2.0, -20, 6, ty=0.85)], cy=0.55))
        space(fr, t, floor=None, bokeh=1.0, beam=0.4)
        M.cristal(fr.base, fr.fx, 'ERROR', u, t0=-0.2, cy=0.33, entrada='golpe', brillo=1.2)
        k = P.eout4(seg(u, ud, ud + 0.35))
        draw_objects(fr, pared(contacto=(0, 0.9)) + cargador(t=(0.3 * k, 0.83 - 0.25 * k, 0.33 + 0.9 * k), ry=-40 * k, rx=20 * k))

        def ui(img, fx):
            kicker(img, '¡OJO!', 150, seg(u, -0.1, 0.1), col=ROJO, size=34)
            if u > ud + 0.2:
                check(img, fx, 540, 1430, seg(u, ud + 0.2, ud + 0.45), 'CARGADOR DESCONECTADO', col=GRIS)
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, -0.05, 0.35), amp=22)
    v = u - uy
    fr = Frame(cam(v, [K(-0.1, 2.0, 60, 30, ty=0.8), K(0.3, 5.2, 20, 16, ty=0.8), K(4.0, 5.1, 16, 16, ty=0.8)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    sala(fr, t, leds=1.0, flujo_k=1.0)

    def ui(img, fx):
        kicker(img, 'TODO LO DEMÁS, ENCHUFADO', 150, seg(v, 0.0, 0.2), col=ROJO)
        tache(img, fx, 540, 1430, seg(v, 0.3, 0.55), 'SIGUE GASTANDO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.3, 0.3), amp=14)


# 9. el decodificador, el micro con su reloj, el estéreo: todos esperando (aparecen uno por uno con su lucecita)
def s_lista(t, fi, u, d):
    us = [wt(9, 0) - 0.15, wt(9, 2) - 0.1, wt(9, 6) - 0.1]
    ut = wt(9, 8) - 0.1                           # «todos esperando»
    fr = Frame(cam(u, [K(-0.4, 4.0, 30, 22, ty=0.5), K(0.3, 4.4, 4, 18, ty=0.5), K(ut, 4.8, -12, 22, ty=0.5), K(4.0, 4.7, -16, 22, ty=0.5)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0)
    pos = [(-1.15, 0, 0.3), (0.0, 0, -0.1), (1.15, 0, 0.3)]
    ms = []
    for i, (fn, kw) in enumerate([(deco, dict(s=0.9)), (micro, dict(s=0.8)), (estereo, dict(s=0.85))]):
        e = P.entrada(u, us[i], 0.28, 'cae')
        if u > us[i] - 0.05:
            p = pos[i]
            ms += fn(t=(p[0], p[1] - e['dy'] * 0.5, p[2]), **kw)
    draw_objects(fr, ms)
    labs = ['DECODIFICADOR', 'MICRO · RELOJ', 'ESTÉREO']
    ys = [0.4, 0.95, 0.55]
    pp = [fr.cam.p1((p[0], y, p[2])) for p, y in zip(pos, ys)]

    def ui(img, fx):
        kicker(img, 'EN ESPERA', 150, seg(u, -0.1, 0.2), col=ROJO)
        for i in range(3):
            if u > us[i] + 0.2:
                pill(img, fx, pp[i][0], pp[i][1] - 90 - 40 * (i % 2), labs[i], eout(seg(u, us[i] + 0.2, us[i] + 0.45)), size=26, border=ROJO)
        if u > ut:
            pill(img, fx, 540, 1430, 'TODOS ESPERANDO', eout(seg(u, ut, ut + 0.3)), size=36, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, sum(golpe_k(u, us[i] + 0.28, 0.2) for i in range(3)), amp=10)


# 10. según la CFE, lo que se queda en espera es como el 11 % de lo que gasta una casa (dona del recibo + «11%» de cristal)
def s_11(t, fi, u, d):
    u11 = wt(10, 11) - 0.15                       # «once por ciento»
    fr = Frame(cam(u, [K(-0.4, 3.0, -30, 30, ty=0.4), K(0.3, 3.6, -6, 24, ty=0.4), K(u11, 3.3, 12, 20, ty=0.4), K(5.0, 3.2, 16, 20, ty=0.4)], cy=0.72))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    M.cristal(fr.base, fr.fx, '11%', u, t0=u11, cy=0.2, alto=0.24, entrada='sube')
    draw_objects(fr, deco(t=(-0.7, 0, 0.2), s=0.7, led=1.0) + micro(t=(0.6, 0, -0.1), s=0.6) + tele(t=(0, 0, -0.9), s=0.5))
    kd = seg(u, 0.0, 0.6)
    k11 = seg(u, u11, u11 + 0.4)

    def ui(img, fx):
        kicker(img, 'CFE · 82 000 DIAGNÓSTICOS EN CASAS', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        cx, cy, r = 540, 880, 170
        d_ = ImageDraw.Draw(img)
        if kd > 0.01:
            d_.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * eout(kd), fill=(90, 92, 100), width=46)
        if k11 > 0.01:
            d_.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 39.6 * eout(k11), fill=ROJO, width=56)
            ImageDraw.Draw(fx).arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 39.6 * eout(k11), fill=(140, 24, 18), width=70)
            d_.text((cx, cy - 10), 'EN ESPERA', font=M.font('mono', 30), fill=(255, 180, 170), anchor='mm')
            d_.text((cx, cy + 34), 'DE TU CONSUMO', font=M.font('mono', 24), fill=(180, 180, 190), anchor='mm')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u11 + 0.3, 0.3), amp=14)


# 11. el truco: conéctalos a una regleta con apagador (la regleta cae y los cables se conectan)
def s_regleta(t, fi, u, d):
    ur = wt(11, 5) - 0.1                          # «regleta»
    fr = Frame(cam(u, [K(-0.4, 3.0, 50, 40, ty=0.1), K(0.3, 3.6, 16, 34, ty=0.1), K(ur, 3.3, -14, 30, ty=0.1), K(4.0, 3.25, -18, 30, ty=0.1)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.25)
    e = P.entrada(u, -0.3, 0.3, 'cae')
    draw_objects(fr, regleta(t=(0, -e['dy'] * 0.4, 0), on=1.0))
    for i in range(3):
        kc = seg(u, ur + 0.15 * i, ur + 0.15 * i + 0.35)
        if kc > 0:
            x = -0.5 + 0.32 * i
            a = np.array([x + 0.4 * (i - 1), 0.2, -1.6])
            b = np.array([x, 0.16, 0.0])
            line3(fr, _cable_pts(a, a + (b - a) * eout(kc), 0.08), col=(230, 230, 234), w=4, a=1.0, glow=0.2)
    psw = fr.cam.p1((0.72, 0.2, 0))

    def ui(img, fx):
        kicker(img, 'EL TRUCO', 150, seg(u, -0.1, 0.2), col=VERDE, size=34)
        pill(img, fx, psw[0], psw[1] - 120, 'APAGADOR', eout(seg(u, ur + 0.2, ur + 0.5)), size=30, border=ROJO)
        pill(img, fx, 540, 1430, 'REGLETA CON APAGADOR', eout(seg(u, ur, ur + 0.3)), size=34, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, -0.05, 0.3), amp=14)


# 12. un clic en la noche… y se apagan de verdad (el apagador hace clic y todas las lucecitas se apagan)
def s_clic(t, fi, u, d):
    uc = wt(12, 1) - 0.05                         # «clic»
    fr = Frame(cam(u, [K(-0.4, 6.0, -30, 18, ty=0.7), K(0.3, 5.4, -6, 14, ty=0.7), K(uc + 0.3, 4.6, 14, 12, ty=0.7), K(4.0, 4.5, 18, 12, ty=0.7)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7 * (1 - 0.5 * seg(u, uc, uc + 0.3)), bokeh=1.0 - 0.6 * seg(u, uc, uc + 0.3))
    off = u > uc
    sala(fr, t, leds=0.0 if off else 1.0, flujo_k=0.0 if off else 0.8, regleta_on=0.0 if off else 1.0)

    def ui(img, fx):
        kicker(img, 'DE NOCHE', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if off:
            check(img, fx, 540, 1430, seg(u, uc + 0.5, uc + 0.75), 'APAGADOS DE VERDAD')
    fr.ui.append(ui)
    out = finish(fr, fi, flash=0.3 * golpe_k(u, uc, 0.15))
    if off:
        out = (out.astype(np.float32) * (1 - 0.35 * seg(u, uc, uc + 0.4))).astype(np.uint8)
    return sacudir(out, t, golpe_k(u, uc, 0.3), amp=12)


# 13. ¿y el cargador? si está tibio sin celular, ese sí desconéctalo (ondas de calor + termómetro + sale del contacto)
def s_tibio(t, fi, u, d):
    utb = wt(13, 5) - 0.1                         # «tibio»
    ud = wt(13, 10) - 0.1                         # «desconéctalo»
    fr = Frame(cam(u, [K(-0.4, 1.8, 50, 14, ty=0.85), K(0.3, 2.3, 16, 8, ty=0.85), K(ud, 2.6, -16, 8, ty=0.85), K(4.0, 2.55, -20, 8, ty=0.85)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    k = P.eout4(seg(u, ud, ud + 0.35))
    draw_objects(fr, pared(contacto=(0, 0.9)) + cargador(t=(0.25 * k, 0.83 - 0.2 * k, 0.33 + 0.8 * k), ry=-30 * k))
    P.ondas_calor(fr, t, 0.25 * k, 1.1 - 0.2 * k, 1.6, 0.4, k=seg(u, utb, utb + 0.3) * (1 - seg(u, ud + 0.3, ud + 0.8)))

    def ui(img, fx):
        kicker(img, '¿Y EL CARGADOR?', 150, seg(u, -0.1, 0.2), col=AMARILLO, size=34)
        if u > utb:
            P.termometro(img, fx, 170, 1350, 330, 0.25 + 0.3 * eout(seg(u, utb, utb + 0.8)), 'TIBIO', k=seg(u, utb, utb + 0.2))
        if u > ud + 0.2:
            check(img, fx, 600, 1430, seg(u, ud + 0.2, ud + 0.45), 'ESE SÍ, DESCONÉCTALO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ud + 0.1, 0.3), amp=14)


# 14. mándaselo a quien desconecta el cargador y deja la tele enchufada (el cargador en la mano… y la tele con su lucecita)
def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.4, 4.6, 40, 14, ty=0.9), K(0.3, 4.0, 12, 10, ty=0.9), K(4.0, 3.9, 8, 10, ty=0.9)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    e = P.entrada(u, 0.0, 0.3, 'gira')
    draw_objects(fr, mueble() + tele(t=(0, 0.5, 0), led=0.75 + 0.25 * math.sin(t * 4)) +
                 cargador(t=(-0.9, 0.71, 0.15), s=0.8 * max(0.05, e['escala']), ry=math.degrees(e['giro'])))
    pl = fr.cam.p1((1.05, 0.96, 0.05))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien desconecta el', 'sans'), ('cargador y deja la tele.', 'serif')], 190, seg(u, -0.1, 0.25), size=58)
        r = 28 + 6 * math.sin(t * 4)
        ImageDraw.Draw(fx).ellipse((pl[0] - r, pl[1] - r, pl[0] + r, pl[1] + r), fill=(150, 20, 16))
        doodle_circle(img, fx, pl[0], pl[1], 70, 60, t, k=eout(seg(u, 0.6, 1.0)), col=ROJO, w=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.25), amp=10)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.25), sfx=[]),
           dict(desde=1, fn=s_casinada, tr='deslizar_abajo', sfx=[]),
           dict(desde=2, fn=s_rayosx, tr='zoom', sfx=[]),
           dict(desde=3, fn=s_europa, tr='cubo', sfx=[]),
           dict(desde=4, fn=s_pesos, tr='golpe', sfx=[]),
           dict(desde=5, fn=s_lucecita, tr='whip', c=(0.7, 0.5), sfx=[]),
           dict(desde=6, fn=s_45, tr='iris', c=(0.52, 0.6), sfx=[]),
           dict(desde=7, fn=s_20, tr='wipe', sfx=[]),
           dict(desde=8, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[]),
           dict(desde=9, fn=s_lista, tr='rebanadas', sfx=[]),
           dict(desde=10, fn=s_11, tr='mosaico', sfx=[]),
           dict(desde=11, fn=s_regleta, tr='giro', c=(0.68, 0.52), sfx=[]),
           dict(desde=12, fn=s_clic, tr='push', c=(0.6, 0.6), sfx=[]),
           dict(desde=13, fn=s_tibio, tr='remolino', sfx=[]),
           dict(desde=14, fn=s_mandalo, tr='deslizar', sfx=[]),
           dict(desde=15, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    E = ESCENAS
    E[0]['sfx'] = [(-1.6, 'whoosh_suave', 0.5), (UJ - 0.12, 'whoosh', 0.8), (UJ, 'sub', 1.0), (UJ, 'slap', 0.8), (UJ + 0.15, 'bass', 0.8)]
    us = wt(1, 2) - 0.15
    E[1]['sfx'] = [(0.0, 'click', 0.6), (0.1, 'chime_c', 0.5), (us, 'whoosh', 0.9), (us + 0.45, 'thud', 0.7), (us + 0.4, 'tick', 0.6)]
    ua = wt(2, 3) - 0.1
    E[2]['sfx'] = [(-0.2, 'shimmer', 0.6), (0.2, 'tick', 0.5), (ua, 'whoosh_suave', 0.5), (ua + 0.3, 'chime_a', 0.5), (ua + 0.3, 'tick2', 0.4)]
    um = wt(3, 5) - 0.1
    E[3]['sfx'] = [(-0.3, 'whoosh', 0.5), (0.0, 'tick', 0.5), (um + 0.25, 'bass', 0.8), (um + 0.3, 'tick2', 0.5)]
    uk, up = wt(4, 5) - 0.1, wt(4, 10) - 0.1
    E[4]['sfx'] = [(0.0 + 0.1 * i, 'tick2', 0.25) for i in range(int(max(1, uk + 0.6) / 0.1))] + \
                  [(up + 0.12 * i + 0.15, 'chime_b', 0.5) for i in range(3)] + [(up + 0.3, 'click', 0.6)]
    ul = wt(5, 6) - 0.1
    E[5]['sfx'] = [(0.0, 'tick', 0.5), (ul, 'click', 0.9), (ul + 0.8, 'click', 0.9), (ul + 0.4, 'scribble', 0.5), (ul + 0.2, 'sub', 0.6)]
    u45 = wt(6, 4) - 0.15
    E[6]['sfx'] = [(0.0, 'riser', 0.4)] + [(u45 - 0.6 + 0.08 * i, 'tick2', 0.25) for i in range(9)] + [(u45 + 0.3, 'bass', 1.0)]
    uv = wt(7, 2) - 0.15
    E[7]['sfx'] = [(-0.3 + 0.07 * i, 'tick', 0.2) for i in range(10)] + [(uv + 0.18, 'bass', 1.0), (uv + 0.18, 'slap', 0.6)]
    ud, uy = wt(8, 5) - 0.1, wt(8, 8) - 0.1
    E[8]['sfx'] = [(-0.05, 'sub', 1.0), (ud, 'whoosh', 0.7), (ud + 0.2, 'click', 0.7), (uy, 'whoosh', 0.8), (uy + 0.3, 'burst', 0.5),
                   (uy + 0.3, 'bass', 0.7)]
    us9 = [wt(9, 0) - 0.15, wt(9, 2) - 0.1, wt(9, 6) - 0.1]
    E[9]['sfx'] = [(x + 0.28, 'thud', 0.7) for x in us9] + [(x + 0.2, 'tick', 0.5) for x in us9] + [(wt(9, 8) - 0.1, 'chime_c', 0.5)]
    u11 = wt(10, 11) - 0.15
    E[10]['sfx'] = [(0.0, 'whoosh_suave', 0.5), (0.1, 'scribble', 0.4), (u11 + 0.3, 'bass', 0.9), (u11 + 0.05, 'shimmer', 0.4)]
    ur = wt(11, 5) - 0.1
    E[11]['sfx'] = [(-0.05, 'thud', 0.9), (ur, 'click', 0.6), (ur + 0.15, 'click', 0.6), (ur + 0.3, 'click', 0.6), (ur + 0.2, 'tick', 0.5)]
    uc = wt(12, 1) - 0.05
    E[12]['sfx'] = [(0.0, 'whoosh_suave', 0.4), (uc, 'click', 1.0), (uc + 0.02, 'thud', 0.8), (uc + 0.5, 'chime_c', 0.6)]
    utb, ud13 = wt(13, 5) - 0.1, wt(13, 10) - 0.1
    E[13]['sfx'] = [(0.0, 'tick', 0.5), (utb, 'shimmer', 0.5), (utb + 0.1, 'riser', 0.3), (ud13 + 0.1, 'whoosh', 0.7), (ud13 + 0.2, 'click', 0.7),
                    (ud13 + 0.25, 'chime_c', 0.5)]
    E[14]['sfx'] = [(0.0, 'whoosh', 0.6), (0.3, 'thud', 0.6), (0.6, 'scribble', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
