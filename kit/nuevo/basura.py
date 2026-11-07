"""Reel diario: «Sobre tu cabeza cae basura… todos los días.» Lun 9-nov-2026, 8:00. Voz Isaac. Estilo rápido (ESTILO.md §11-12).
Inicio tipo 1 (caída desde el espacio: la Tierra de alambre con bolas de fuego → crash zoom → una casa → el pedazo cae y
rebota junto a ella, con el título al aterrizar). Datos: el observatorio Swift de la NASA (3 200 lb ≈ 1 450 kg, lanzado en
nov-2004) reingresó el 4-nov-2026 hacia las 7:39 a. m. hora del este (6:39 en CDMX) sobre Indonesia (Fuerza Espacial de EE. UU.,
vía ABC7); la nave de rescate LINK de Katalyst (julio de 2026) quedó girando sin control; la NASA calculó 1 en 2 100 de que
lastimara a alguien y la regla de EE. UU. (2019) pide menos de 1 en 10 000; ~10 % de una nave así suele llegar al suelo
(McDowell); el tanque de acero de ~250 kg de un Delta 2 cayó casi entero cerca de Georgetown, Texas, en 1997 (ESA);
más de 3 satélites o cohetes enteros reingresan al día en promedio (ESA, 2025); en mar-2024 un pedazo de la estación espacial
atravesó el techo de una casa en Naples, Florida (NASA vía NBC); no tocar los restos: pueden traer combustible tóxico (PhilSA).
Swift, nave, casa, tanque y pedazos: RECREACIÓN. Foto real: NASA (Swift antes del lanzamiento, dominio público).
Fuentes en guiones/2026-11-09_basura.txt."""
import math, os, re, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'basura'
TXT = ['Sobre tu cabeza cae basura… todos los días.',
       'El 4 de noviembre le tocó a un telescopio de la NASA: el Swift.',
       '1 450 kilos, casi 22 años en órbita.',
       'Una nave fue a rescatarlo… y se quedó girando sin control.',
       'Y el Swift cayó sobre Indonesia a las 6:39 de la mañana, hora de México.',
       'Entra al aire a más de 25 000 km/h: una bola de fuego.',
       'Casi todo se quema… pero cerca del 10% puede llegar al suelo.',
       'En Texas cayó así un tanque de cohete de 250 kilos… casi entero.',
       'Y lo peor: la NASA calculó 1 posibilidad en 2 100 de que lastimara a alguien.',
       'La regla de Estados Unidos pide menos de 1 en 10 000.',
       'Y no es el único: en promedio, más de 3 satélites o cohetes enteros caen cada día.',
       'En 2024, un pedazo de la estación espacial atravesó el techo de una casa en Florida.',
       'Que se sepa, todavía no ha herido a nadie.',
       'Si encuentras un pedazo, no lo toques: puede traer restos de combustible tóxico.',
       'Aléjate y avisa a protección civil.',
       'Mándaselo a quien se llevaría el pedazo de recuerdo.',
       'Porque mientras ves esto…']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-09_basura_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)

AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 70, 60)
NARANJA = (255, 150, 60)
FUEGO = (255, 190, 110)
ORO = (214, 150, 62)
_SWIFT = Image.open(os.path.join(HERE, 'img', 'img_swift_nasa.jpg')).convert('RGB')


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
    """Tiempo (relativo al inicio de la frase i) en que empieza su palabra k: exacto con las palabras de Scribe."""
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


# ================================================================== objetos (RECREACIÓN)
def swift(s=1.0, rx=0.0, ry=0.0, rz=0.0, t=(0, 0, 0), interior=False):
    """Observatorio Swift: cuerpo de 8 caras con lámina dorada, faldón plateado, caja blanca del BAT arriba
    con su toldo gris y dos paneles solares. Centro aproximado en (0, 0.8, 0) antes de transformar."""
    ms = []
    ms.append(named(M3.cyl(0.5, 0.95, ORO, n=8, shadow=0, gloss=0.75), 'cuerpo', rim=0.6, gloss=0.75))
    ms.append(named(M3.cyl(0.66, 0.1, (200, 202, 208), n=8, shadow=0, gloss=0.8, y0=0.95), 'faldon', rim=0.6, gloss=0.8))
    ms.append(named(M3.box(1.05, 0.55, 0.85, (236, 236, 238), shadow=0, base=True, gloss=0.3).tf(t=(-0.05, 1.05, 0)), 'bat', rim=0.5))
    ms.append(named(M3.box(0.5, 0.62, 0.9, (150, 152, 158), shadow=0, base=True, gloss=0.5).tf(rz=-8, t=(0.42, 1.03, 0)), 'toldo', rim=0.5))
    for sx in (-1, 1):
        ms.append(named(M3.box(0.08, 0.06, 0.06, (120, 120, 126), shadow=0, base=False).tf(t=(sx * 0.62, 0.5, 0)), 'brazo'))
        ms.append(named(M3.box(1.15, 0.03, 0.62, (26, 40, 86), shadow=0, base=False, gloss=0.9).tf(t=(sx * 1.25, 0.5, 0)), 'panel',
                        rim=0.4, gloss=0.9))
    if interior:
        ms.append(named(M3.sphere(0.2, (190, 192, 198), nu=18, nv=10, shadow=0, gloss=0.9).tf(t=(0, 0.45, 0)), 'tanque', rim=0.5))
        ms.append(named(M3.cyl(0.16, 0.5, (210, 210, 220), n=14, shadow=0, gloss=0.95, y0=0.95), 'espejo', rim=0.5))
    return P.tfk(P.tfk(ms, t=(0, -0.8, 0)), s=s, rx=rx, ry=ry, rz=rz, t=t)


def nave(s=1.0, rx=0.0, ry=0.0, rz=0.0, t=(0, 0, 0)):
    """Nave de rescate genérica (sin marcas): caja blanca, un panel solar y un brazo de captura."""
    ms = [named(M3.box(0.6, 0.5, 0.5, (226, 226, 230), shadow=0, base=False, gloss=0.4), 'nave', rim=0.6),
          named(M3.box(1.1, 0.025, 0.42, (26, 40, 86), shadow=0, base=False, gloss=0.9).tf(t=(-0.88, 0, 0)), 'panel', rim=0.4),
          named(M3.box(0.45, 0.06, 0.06, (150, 150, 156), shadow=0, base=False).tf(t=(0.52, 0.0, 0)), 'brazo'),
          named(M3.box(0.06, 0.18, 0.18, (200, 60, 50), shadow=0, base=False).tf(t=(0.76, 0.0, 0)), 'garra')]
    return P.tfk(ms, s=s, rx=rx, ry=ry, rz=rz, t=t)


def casa(t=(0, 0, 0), s=1.0, hoyo=0.0, luz=0.6):
    """Casa de una planta (muros claros, techo de teja, puerta y 2 ventanas con luz). hoyo: agujero en el techo."""
    ms = [named(M3.box(1.8, 1.0, 1.3, (214, 204, 186), shadow=0, base=True, gloss=0.1), 'muro', rim=0.4, gloss=0.1)]
    techo = M3.extrude([(-0.75, 0), (0.75, 0), (0, 0.55)], 2.0, (168, 78, 52), shadow=0, gloss=0.2)
    techo = techo.tf(rx=-90, t=(0, 1.0, 1.0))  # prisma: el triángulo queda en x-y (punta arriba), a lo largo de z
    techo = techo.tf(s=(1.33, 1.0, 0.75), t=(0, 0, 0))
    ms.append(named(techo, 'techo', rim=0.5, gloss=0.2))
    ms.append(named(M3.box(0.32, 0.6, 0.02, (92, 60, 40), shadow=0, base=True, gloss=0.3).tf(t=(0, 0, 0.66)), 'puerta', rim=0.2))
    for x in (-0.55, 0.55):
        v = named(M3.box(0.34, 0.3, 0.02, (255, 214, 140), shadow=0, base=True).tf(t=(x, 0.45, 0.66)), 'ventana',
                  glow=M.scale_c((255, 190, 110), luz))
        v.flat = True
        ms.append(v)
    return P.tfk(ms, s=s, t=t)


def tanque(t=(0, 0, 0), s=1.0, ry=0.0, rz=0.0, quemado=0.4):
    """Tanque de cohete de acero inoxidable (cilindro con tapas semiesféricas), acostado a lo largo de x, algo chamuscado."""
    col = M.mixc((196, 198, 204), (110, 92, 78), quemado)
    ms = [named(M3.cyl(0.42, 1.6, col, n=28, shadow=0, gloss=0.85, y0=-0.8).tf(rz=90), 'tanque', rim=0.7, gloss=0.85)]
    for sx in (-1, 1):
        ms.append(named(M3.sphere(0.42, col, nu=24, nv=12, shadow=0, gloss=0.85).tf(s=(0.6, 1, 1), t=(sx * 0.8, 0, 0)), 'tapa',
                        rim=0.7, gloss=0.85))
    ms.append(named(M3.cyl(0.07, 0.25, (150, 120, 70), n=12, shadow=0, gloss=0.6).tf(rz=90, t=(1.2, 0, 0)), 'valvula'))
    return P.tfk(ms, s=s, ry=ry, rz=rz, t=t)


def pedazo(t=(0, 0, 0), s=1.0, rx=0.0, ry=0.0, rz=0.0, caliente=0.0):
    """Pedazo chamuscado (cilindro de metal de unos 10 cm, como el de Florida, a escala grande)."""
    col = M.mixc((84, 74, 66), (255, 120, 50), caliente)
    ms = [named(M3.cyl(0.13, 0.42, col, n=16, shadow=0, gloss=0.5, y0=-0.21), 'pedazo', rim=0.6, gloss=0.5),
          named(M3.cyl(0.15, 0.05, M.mixc((60, 54, 50), (255, 150, 70), caliente), n=16, shadow=0, gloss=0.4, y0=0.17), 'aro', rim=0.6)]
    if caliente > 0.05:
        for m in ms:
            m.glow = M.scale_c((255, 120, 40), 0.6 * caliente)
    return P.tfk(ms, s=s, rx=rx, ry=ry, rz=rz, t=t)


def bola_fuego(fr, p, v, k=1.0, largo=1.4, r=8, seed=0, t=0.0):
    """Bola de fuego en 3D: cabeza blanca-amarilla y estela naranja-roja hacia atrás (v = dirección de vuelo)."""
    if k <= 0.01:
        return
    p, v = np.asarray(p, float), M.norm(v)
    cola = [p - v * largo * j / 10 for j in range(11)]
    line3(fr, cola[:6], col=(255, 210, 140), w=5, a=0.9 * k, glow=1.3)
    line3(fr, cola[4:], col=(255, 110, 50), w=3, a=0.6 * k, glow=1.0)
    rng = np.random.RandomState((seed + int(t * 12)) % 100000)
    for j in range(4):
        q = p - v * largo * (0.3 + 0.6 * rng.rand()) + rng.normal(0, 0.04 * largo, 3)
        dot3(fr, q, r=2.5, col=(255, 160, 80), a=0.7 * k, glow=1.0)
    dot3(fr, p, r=r, col=(255, 250, 230), a=k, glow=1.8)


def tierra(fr, t, C, R, spin, lines=1.0):
    N.earth(fr, t, np.asarray(C, float), R, spin, lines_a=lines)


def geo(lat, lon, spin, C, R):
    """Punto de la Tierra de alambre en latitud/longitud (grados), con el mismo giro que N.earth."""
    la, lo = math.radians(lat), math.radians(lon)
    p = np.array([[R * math.cos(la) * math.cos(lo), R * math.sin(la), R * math.cos(la) * math.sin(lo)]])
    return np.asarray(C, float) + D._rot(p, spin)[0]


def humo(fr, t, C, k=1.0, col=(150, 230, 120), n=5, alto=1.0):
    """Vapores (line-art) que suben ondulando desde C."""
    if k <= 0.01:
        return
    C = np.asarray(C, float)
    for i in range(n):
        x0 = (i - (n - 1) / 2) * 0.12
        ph = t * 3.2 + i * 1.7
        pts = [C + np.array([x0 + 0.07 * math.sin(ph + s_ * 8), alto * s_, 0.05 * math.cos(ph + s_ * 6)]) for s_ in np.linspace(0, 1, 26)]
        line3(fr, pts, col=col, w=2.4, a=0.75 * k, glow=1.0, frac=clamp(((t * 0.9 + i * 0.23) % 1.0) * 1.6))


def anillo_polvo(fr, C, k, r=1.0, col=(200, 190, 170)):
    if k <= 0.01 or k >= 0.99:
        return
    th = np.linspace(0, 2 * math.pi, 50)
    rr = r * eout(k)
    line3(fr, [np.asarray(C) + np.array([rr * math.cos(a), 0.02, rr * math.sin(a)]) for a in th], col=col, w=3, a=1 - k, glow=0.6)


def reloj_dig(img, fx, x, y, txt, k, size=150, col=AMARILLO):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    f = M.font('mono', size)
    w = d.textlength(txt, font=f)
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(over).rounded_rectangle((x - w / 2 - 40, y - size * 0.75, x + w / 2 + 40, y + size * 0.75), radius=30,
                                           fill=(10, 12, 16, int(220 * k)), outline=(255, 255, 255, int(60 * k)), width=2)
    img.paste(over, (0, 0), over)
    texto(img, fx, x, y, txt, size, col, k, f='mono')


# ================================================================== escenas
# 0. gancho, inicio tipo 1: la Tierra de alambre con bolas de fuego → crash zoom → la casa → el pedazo cae y rebota
UC = 0.55          # corte interno: de la Tierra a la casa
UL = 0.95          # aterriza el pedazo (golpe + título), con «cae»


def _gancho_tierra(t, fi, u):
    k = P.eout4(seg(u, UC - 0.3, UC))                       # crash zoom hacia México
    C = np.array([0.0, 1.0, 0.0])
    spin = 2.97 + 0.12 * (u - UC)                           # México de frente al llegar el crash zoom
    fr = Frame(Cam(target=tuple(C), dist=6.4 - 0.5 * seg(u, -0.3, UC - 0.3) - 3.0 * k, yaw=6 * math.sin(t * 0.4), pitch=8, cy=0.5))
    space(fr, t, floor=None, bokeh=1.0)
    M.cristal(fr.base, fr.fx, 'BASURA', u, t0=-2.3, cy=0.5, entrada='golpe')
    tierra(fr, t, C, 1.55, spin)
    mx = geo(20, -100, spin, C, 1.55)
    dot3(fr, mx, r=9, col=CYAN, a=0.6 + 0.4 * math.sin(t * 8), glow=1.4)
    for j in range(4):                                      # bolas de fuego que reingresan (en loop, cada 1.6 s)
        ph = ((t * 0.62 + j * 0.25) % 1.0)
        a0 = j * 1.7 + 0.6
        st = C + np.array([2.6 * math.cos(a0), 1.2 + 0.9 * math.sin(a0 * 1.3), 2.0 * math.sin(a0)])
        en = C + M.norm(st - C) * 1.6
        p = st + (en - st) * ph
        bola_fuego(fr, p, en - st, k=math.sin(math.pi * ph), largo=0.9, r=6, seed=j, t=t)
    out = finish(fr, fi)
    if k > 0.05:
        px, py, _ = fr.cam.p1(tuple(mx))
        out = M.scale_about(out, 1 + 2.6 * k * k, px / 1080, py / 1920)
        out = M.radial_blur(out, 0.14 * k, px / 1080, py / 1920)
    return out


def s_gancho(t, fi, u, d):
    if u < UC:
        return _gancho_tierra(t, fi, u)
    fr = Frame(cam(u, [K(UC, 2.6, 30, 30, ty=1.6, tx=0.4), K(UL, 4.6, 18, 14, ty=0.9), K(3.5, 4.4, 10, 12, ty=0.9)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'BASURA', u, t0=-2.3, cy=0.36, entrada='golpe')
    draw_objects(fr, casa(t=(-0.85, 0, -0.75)))
    PL = np.array([0.62, 0.21, 0.5])
    kk = seg(u, UC, UL)
    if u < UL:
        p = PL + np.array([0.6, 5.0, 0.4]) * (1 - kk) ** 1.6
        bola_fuego(fr, p, (-0.6, -5.0, -0.4), k=1.0, largo=1.6, r=9, t=t)
        draw_objects(fr, pedazo(t=tuple(p), s=1.6, rz=40, caliente=1.0))
    else:
        e = P.rebote(seg(u, UL, UL + 0.5))
        h = 0.35 * (1 - e)
        draw_objects(fr, pedazo(t=(PL[0], PL[1] + h, PL[2]), s=1.6, rz=90 - 20 * (1 - e), caliente=1 - seg(u, UL, UL + 2.0)))
        anillo_polvo(fr, (PL[0], 0, PL[2]), seg(u, UL, UL + 0.6), r=1.3)
        humo(fr, t, PL + np.array([0, 0.2, 0]), k=0.6 * (1 - seg(u, UL + 1.0, UL + 2.4)), col=(170, 170, 176), n=3, alto=0.9)

    def ui(img, fx):
        kicker(img, 'BASURA ESPACIAL · REENTRADA', 150, seg(u, UL, UL + 0.3), col=(150, 210, 230))
        P.titulo_golpe(img, fx, [('Sobre tu cabeza cae basura…', 'sans'), ('todos los días.', 'serif')], 210, seg(u, UL, UL + 0.15), size=66)
        pill(img, fx, 540, 1430, 'RECREACIÓN', 1.0, size=22, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, UL, 0.4), amp=26)


# 1. el 4 de noviembre le tocó a un telescopio de la NASA: el Swift (el Swift en órbita sobre la Tierra + foto real que cae)
def s_swift(t, fi, u, d):
    us = wt(1, 12) - 0.05                        # «el Swift»: cae la foto real
    fr = Frame(cam(u, [K(-0.4, 2.0, -50, 10, ty=1.2), K(0.3, 3.6, -18, 6, ty=1.2), K(us, 3.9, 14, 4, ty=1.2), K(4.5, 3.9, 18, 4, ty=1.2)], cy=0.52))
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, (0, -5.6, -2.0), 5.0, 0.4 + 0.05 * t, lines=0.7)
    draw_objects(fr, swift(s=0.95, ry=25 + 12 * t, rz=6 * math.sin(t), t=(0, 1.25, 0)))
    pc = fr.cam.p1((0, 1.9, 0))

    def ui(img, fx):
        kicker(img, 'OBSERVATORIO SWIFT · NASA', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        reloj_dig(img, fx, 540, 300, '4 NOV 2026', eout(seg(u, 0.0, 0.25)), size=74, col=AMARILLO)
        if u > us:
            photo_card(img, fx, _SWIFT, 540, 1080, 420, t - u + us, t, caption='NASA · SWIFT · 2004', angle0=-10)
        else:
            pill(img, fx, pc[0], pc[1] - 60, 'TELESCOPIO', eout(seg(u, wt(1, 8) - 0.1, wt(1, 8) + 0.2)), size=30, border=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.28, 0.3), amp=14)


# 2. 1 450 kilos, casi 22 años en órbita (el Swift gira de golpe, contador de kilos y órbitas que se acumulan)
def s_kilos(t, fi, u, d):
    ua = wt(2, 4) - 0.1                          # «casi veintidós años»
    fr = Frame(cam(u, [K(-0.4, 3.0, 60, 20, ty=1.0), K(0.25, 3.3, 20, 10, ty=1.0), K(ua, 5.2, -10, 24, ty=0.6), K(4.0, 5.2, -14, 24, ty=0.6)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0)
    e = P.entrada(u, -0.3, 0.3, 'gira')
    draw_objects(fr, swift(s=0.9 * max(0.05, e['escala']), ry=math.degrees(e['giro']) + 30 + 10 * t, t=(0, 1.1, 0)))
    if u > ua:                                    # órbitas que se van sumando alrededor
        for j in range(6):
            kj = seg(u, ua + 0.12 * j, ua + 0.12 * j + 0.35)
            if kj <= 0:
                continue
            r = 1.6 + 0.12 * j
            th = np.linspace(0, 2 * math.pi * kj, 60)
            line3(fr, [(r * math.cos(a), 1.1 + 0.3 * math.sin(a + j), r * math.sin(a) * 0.8) for a in th], col=CYAN, w=1.8, a=0.7, glow=0.9)
    kg = int(1450 * P.eout4(seg(u, -0.1, 0.9)))
    yr = 2004 + int(round(22 * P.eout4(seg(u, ua, ua + 1.4))))

    def ui(img, fx):
        kicker(img, 'PESO · TIEMPO EN ÓRBITA', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        texto(img, fx, 540, 330, f'{kg:,} kg'.replace(',', ' '), 130, WHITE, 1.0)
        if u > ua:
            reloj_dig(img, fx, 540, 1250, f'2004 → {yr}', eout(seg(u, ua, ua + 0.2)), size=70, col=AMARILLO)
            pill(img, fx, 540, 1400, 'CASI 22 AÑOS', eout(seg(u, ua + 1.2, ua + 1.5)), size=34, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.9, 0.3), amp=14)


# 3. una nave fue a rescatarlo… y se quedó girando sin control
def s_rescate(t, fi, u, d):
    ug = wt(3, 7) - 0.1                          # «se quedó girando»
    fr = Frame(cam(u, [K(-0.4, 6.0, -30, 14, ty=1.1, tx=0.1), K(0.3, 5.4, -8, 10, ty=1.1, tx=0.1), K(ug, 4.8, 20, 6, ty=1.1, tx=0.2),
                       K(4.0, 4.7, 24, 6, ty=1.1, tx=0.2)], cy=0.52))
    space(fr, t, floor=None, bokeh=1.0)
    draw_objects(fr, swift(s=0.55, ry=20 + 6 * t, t=(-0.75, 1.0, 0)))
    if u < ug:
        x = lerp(3.2, 0.85, P.eout4(seg(u, -0.3, ug)))
        draw_objects(fr, nave(s=0.6, ry=180, t=(x, 1.1, 0.1)))
        rot = 0.0
    else:
        v = u - ug
        rot = 200 * v + 260 * v * v
        draw_objects(fr, nave(s=0.6, ry=180 + rot, rz=rot * 0.7, rx=rot * 0.4, t=(0.85 + 0.35 * v, 1.1 + 0.2 * v, 0.1)))
    pn = fr.cam.p1((0.85, 1.45, 0.1))

    def ui(img, fx):
        kicker(img, 'MISIÓN DE RESCATE · JULIO 2026', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if u < ug:
            pill(img, fx, pn[0], pn[1] - 80, 'RESCATE', eout(seg(u, 0.2, 0.45)), size=30, border=CYAN)
        else:
            tache(img, fx, 540, 1430, seg(u, ug + 0.2, ug + 0.45), 'GIRANDO SIN CONTROL')
            doodle_circle(img, fx, pn[0] + 30, pn[1] + 60, 190, 170, t, k=eout(seg(u, ug, ug + 0.4)), col=ROJO, w=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ug, 0.35), amp=16)


# 4. cayó sobre Indonesia a las 6:39 de la mañana, hora de México (la Tierra gira hasta Indonesia + reloj)
def s_indonesia(t, fi, u, d):
    ui0 = wt(4, 5) - 0.1                         # «Indonesia»
    uh = wt(4, 8) - 0.1                          # «seis treinta y nueve»
    C = np.array([0.0, 1.0, 0.0])
    spin = lerp(2.7, 0.16, P.eout4(seg(u, -0.3, ui0 + 0.2)))       # Indonesia queda de frente
    fr = Frame(cam(u, [K(-0.4, 4.6, -40, 10, ty=1.0), K(0.3, 5.0, -6, 8, ty=1.0), K(ui0 + 0.2, 3.6, 0, 6, ty=1.15), K(5.0, 3.5, 4, 6, ty=1.15)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, C, 1.5, spin)
    pi_ = geo(2.5, 99.0, spin, C, 1.5)
    on = seg(u, ui0, ui0 + 0.3)
    if on > 0:
        bola_fuego(fr, pi_ + M.norm(pi_ - C) * 0.5 * (1 - on), C - pi_, k=1 - 0.6 * on, largo=0.7, r=7, t=t)
        dot3(fr, pi_, r=10, col=ROJO, a=on, glow=1.6)
    pp = fr.cam.p1(tuple(pi_))

    def ui(img, fx):
        kicker(img, 'DATOS: FUERZA ESPACIAL DE EE. UU.', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if on > 0.3:
            pill(img, fx, pp[0], pp[1] - 90, 'INDONESIA', eout(seg(u, ui0 + 0.1, ui0 + 0.35)), size=32, border=ROJO)
        if u > uh:
            reloj_dig(img, fx, 540, 1270, '6:39 a. m.', eout(seg(u, uh, uh + 0.2)), size=110)
            pill(img, fx, 540, 1430, 'HORA DE MÉXICO · 4 NOV', eout(seg(u, uh + 0.6, uh + 0.9)), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ui0 + 0.3, 0.3) + golpe_k(u, uh, 0.3), amp=16)


# 5. entra al aire a más de 25 000 km/h: una bola de fuego (el Swift al rojo vivo con plasma y velocímetro)
def s_fuego(t, fi, u, d):
    ub = wt(5, 11) - 0.1                         # «una bola de fuego»
    fr = Frame(cam(u, [K(-0.4, 3.0, 40, 14, ty=1.0), K(0.3, 3.6, 10, 8, ty=1.0), K(ub, 2.6, -24, 4, ty=1.0, roll=-8),
                       K(4.0, 2.5, -28, 4, ty=1.0, roll=-8)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.3)
    calor = seg(u, -0.2, ub + 0.4)
    v = np.array([-1.0, -0.35, 0.0])
    for j in range(9):                            # plasma: líneas que pasan rozando
        ph = (t * 2.2 + j * 0.37) % 1.0
        y0 = 1.0 + (j - 4) * 0.13
        x0 = 2.6 - 6.0 * ph
        line3(fr, [(x0, y0 - 0.35 * (x0 - 2.6) / 6, 0.4 * math.sin(j)), (x0 + 1.4, y0 - 0.35 * (x0 - 1.2) / 6, 0.4 * math.sin(j))],
              col=M.mixc((180, 200, 230), NARANJA, calor), w=2.2, a=0.5 + 0.4 * calor, glow=1.0)
    draw_objects(fr, swift(s=0.8, ry=-30 + 8 * math.sin(t * 3), rz=-20, t=(0, 1.0, 0)))
    if calor > 0.05:                              # capa de plasma al frente
        pts = [(-0.9 + 0.25 * math.cos(a), 1.0 + 0.95 * math.sin(a), 0.3) for a in np.linspace(math.pi / 2, 3 * math.pi / 2, 30)]
        line3(fr, pts, col=FUEGO, w=8, a=calor, glow=2.2)
        for j in range(6):
            q = (-0.9 + 0.3 * math.sin(t * 9 + j), 1.0 + 0.8 * math.sin(j * 1.1), 0.3)
            bola_fuego(fr, q, (-1, -0.1, 0), k=calor * 0.8, largo=2.2, r=5, seed=j, t=t)
    vel = int(25000 * P.eout4(seg(u, 0.0, wt(5, 10))))

    def ui(img, fx):
        kicker(img, 'REENTRADA', 150, seg(u, -0.1, 0.2), col=NARANJA, size=34)
        texto(img, fx, 540, 320, f'{vel:,}'.replace(',', ' '), 140, WHITE)
        kicker(img, 'KM/H', 420, seg(u, 0.1, 0.4), col=AMARILLO, size=34)
        pill(img, fx, 540, 1430, 'RECREACIÓN', 1.0, size=22, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    out = finish(fr, fi, flash=0.15 * golpe_k(u, ub, 0.4))
    return sacudir(out, t, 0.25 * calor + golpe_k(u, ub, 0.4), amp=12)


# 6. segundo gancho: casi todo se quema… pero cerca del 10 % puede llegar al suelo (se despedaza; quedan tanque y espejo)
def s_diez(t, fi, u, d):
    up = wt(6, 4) - 0.1                          # «pero»
    u10 = wt(6, 7) - 0.15                        # «diez por ciento»
    fr = Frame(cam(u, [K(-0.4, 3.0, 10, 8, ty=1.0), K(0.25, 3.8, -20, 10, ty=1.0), K(up, 3.2, 26, 12, ty=0.9), K(4.0, 3.1, 30, 12, ty=0.9)], cy=0.56))
    space(fr, t, floor=None, bokeh=1.0)
    M.cristal(fr.base, fr.fx, '10%', u, t0=u10 - 0.05, cy=0.4, entrada='zoom', brillo=1.1)
    kd = P.eout4(seg(u, -0.3, up))
    piezas = swift(s=0.85, ry=20 + 10 * t, t=(0, 1.0, 0), interior=True)
    sobre = [m for m in piezas if m.name in ('tanque', 'espejo')]
    quema = [m for m in piezas if m.name not in ('tanque', 'espejo')]
    exp = P.despiece(quema, kd, centro=(0, 1.0, 0), fuerza=1.5, giro=1.2)
    a_q = 1 - seg(u, up - 0.4, up + 0.3)
    for m in exp:                                 # cada pieza se encoge al quemarse
        c = m.V.mean(0)
        m.V = c + (m.V - c) * max(0.02, a_q)
        m.glow = M.scale_c((255, 120, 40), 0.7 * kd * a_q)
        m.alpha = a_q
    draw_objects(fr, [m for m in exp if m.alpha > 0.02] + P.despiece(sobre, kd * 0.4, centro=(0, 1.0, 0), fuerza=0.6))
    if a_q > 0.02:
        for j in range(8):
            a0 = j * 0.785
            q = np.array([0, 1.0, 0]) + np.array([math.cos(a0), math.sin(a0) * 0.7, 0.4 * math.sin(a0 * 2)]) * (0.5 + 1.4 * kd)
            bola_fuego(fr, q, (math.cos(a0), math.sin(a0) * 0.7, 0), k=kd * a_q, largo=0.5, r=4, seed=j, t=t)
    pt = fr.cam.p1((0, 0.6, 0))

    def ui(img, fx):
        kicker(img, 'CASI TODO SE QUEMA', 150, seg(u, -0.1, 0.2), col=NARANJA)
        if u > up + 0.3:
            pill(img, fx, 540, 1430, 'LLEGA AL SUELO: LO MÁS DURO', eout(seg(u, up + 0.3, up + 0.6)), size=30, border=AMARILLO)
            doodle_circle(img, fx, pt[0], pt[1] - 40, 230, 260, t, k=eout(seg(u, up + 0.2, up + 0.6)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u10, 0.35), amp=20)


# 7. en Texas cayó así un tanque de cohete de 250 kilos… casi entero (tanque chamuscado en el campo, zoom digital con REC)
def s_tanque(t, fi, u, d):
    uk = wt(7, 9) - 0.1                          # «doscientos cincuenta kilos»
    ue = wt(7, 12) - 0.1                         # «casi entero»
    fr = Frame(cam(u, [K(-0.4, 2.4, 70, 30, ty=0.5), K(0.3, 4.2, 30, 16, ty=0.5), K(uk, 3.8, -16, 14, ty=0.5), K(5.0, 3.7, -20, 14, ty=0.5)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9, beam=0.5)
    e = P.entrada(u, -0.35, 0.3, 'cae')
    draw_objects(fr, tanque(t=(0, 0.42 - e['dy'] * 0.6, 0), ry=-15, rz=4, quemado=0.45))
    pc = fr.cam.p1((0, 0.95, 0))
    z = 1.0 if u < ue else 1.3
    kz = seg(u, ue, ue + 0.12)

    def ui(img, fx):
        kicker(img, 'TEXAS · ENERO 1997 · COHETE DELTA 2', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if u > uk:
            pill(img, fx, pc[0], pc[1] - 90, '≈ 250 KG · ACERO', eout(seg(u, uk, uk + 0.3)), size=34, border=AMARILLO)
        pill(img, fx, 540, 1430, 'RECREACIÓN · DATO: ESA', 1.0, size=22, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u > ue:
        out = M.scale_about(out, lerp(1.0, 1.3, kz), 0.5, 0.5)
        im = Image.fromarray(out)
        rec_frame(im, t, 1.0, zoom_label='x1.3')
        out = np.asarray(im)
    return sacudir(out, t, golpe_k(u, -0.05, 0.35), amp=20)


# 8. y lo peor: la NASA calculó 1 posibilidad en 2 100 de que lastimara a alguien (2 100 puntos y uno rojo)
def s_2100(t, fi, u, d):
    un = wt(8, 6) - 0.1                          # «una posibilidad»
    fr = Frame(Cam(target=(0, 0.6, 0), dist=5.0, yaw=8 * math.sin(t * 0.6), pitch=12, cy=0.55))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '1 EN 2 100', u, t0=wt(8, 9) - 0.15, cy=0.2, entrada='golpe', brillo=1.1)
    kg = seg(u, -0.3, un)
    zoom = 1.0 + 0.6 * P.eout4(seg(u, wt(8, 14) - 0.2, wt(8, 14) + 0.3))

    def ui(img, fx):
        kicker(img, 'Y LO PEOR', 150, seg(u, -0.1, 0.1), col=ROJO, size=34)
        d_ = ImageDraw.Draw(img)
        cols, rows = 42, 50
        sp = 18.0
        x0, y0 = 540 - (cols - 1) * sp / 2, 520
        n = int(cols * rows * P.eout4(kg))
        for i in range(n):
            x = x0 + (i % cols) * sp
            y = y0 + (i // cols) * sp
            d_.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(110, 112, 120))
        if u > un:
            i = 1234
            x, y = x0 + (i % cols) * sp, y0 + (i // cols) * sp
            r = 9 + 4 * math.sin(t * 10)
            d_.ellipse((x - r, y - r, x + r, y + r), fill=ROJO)
            ImageDraw.Draw(fx).ellipse((x - 3 * r, y - 3 * r, x + 3 * r, y + 3 * r), fill=M.scale_c(ROJO, 0.5))
            doodle_circle(img, fx, x, y, 60, 60, t, k=eout(seg(u, un, un + 0.4)), col=ROJO, w=6)
            pill(img, fx, 540, 1470, 'ALGUIEN LASTIMADO', eout(seg(u, wt(8, 14) - 0.1, wt(8, 14) + 0.2)), size=34, border=ROJO)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if zoom > 1.001:
        i = 1234
        out = M.scale_about(out, zoom, (540 - 41 * 9.0 + (i % 42) * 18.0) / 1080, (520 + (i // 42) * 18.0) / 1920)
    return sacudir(out, t, golpe_k(u, un, 0.35), amp=18)


# 9. la regla de Estados Unidos pide menos de 1 en 10 000 (gráfico: riesgo por cada 10 000)
def s_regla(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.4, 4.0, -40, 20, ty=0.8), K(0.3, 4.6, -10, 14, ty=0.8), K(4.0, 4.5, -6, 14, ty=0.8)], cy=0.75))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    draw_objects(fr, swift(s=0.45, ry=40 + 20 * t, t=(0, 0.9, 0)))
    um = wt(9, 6) - 0.1

    def ui(img, fx):
        kicker(img, 'REGLA DE EE. UU. (2019)', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        chart_grow(img, fx, (110, 250, 970, 1080), [4.8, 1.0], ['SWIFT', 'LÍMITE'], t - u + 0.0, t, unit='', vmax=5.6,
                   title_txt='RIESGO POR CADA 10 000', line=False, tag='NASA')
        if u > um:
            pill(img, fx, 540, 1180, '1 EN 2 100 ≈ 5 EN 10 000', eout(seg(u, um, um + 0.3)), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um, 0.3), amp=12)


# 10. y no es el único: más de 3 satélites o cohetes enteros caen cada día (Tierra con 3 bolas de fuego + reloj de 24 h)
def s_diario(t, fi, u, d):
    u3 = wt(10, 9) - 0.1                         # «tres»
    C = np.array([0.0, 1.05, 0.0])
    fr = Frame(cam(u, [K(-0.4, 6.4, 50, 20, ty=1.05), K(0.3, 5.4, 18, 12, ty=1.05), K(u3, 4.9, -12, 8, ty=1.05), K(5.0, 4.8, -16, 8, ty=1.05)], cy=0.56))
    space(fr, t, floor=None, bokeh=1.0)
    spin = 0.4 + 0.25 * t
    tierra(fr, t, C, 1.45, spin)
    for j in range(3):
        kj = seg(u, u3 + 0.2 * j, u3 + 0.2 * j + 0.9)
        if 0 < kj < 1:
            a0 = j * 2.1 + 0.4
            st = C + np.array([2.4 * math.cos(a0), 1.6 - 0.8 * j, 1.8 * math.sin(a0)])
            en = C + M.norm(st - C) * 1.5
            bola_fuego(fr, st + (en - st) * kj, en - st, k=math.sin(math.pi * kj) ** 0.5, largo=0.9, r=7, seed=j, t=t)
    n = sum(1 for j in range(3) if u > u3 + 0.2 * j + 0.9)

    def ui(img, fx):
        kicker(img, 'ESA · PROMEDIO DE 2025', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if u > u3:
            texto(img, fx, 540, 300, str(max(1, n)) if n < 3 else 'MÁS DE 3', 150 if n < 3 else 120, AMARILLO, eout(seg(u, u3, u3 + 0.2)))
            kicker(img, 'OBJETOS ENTEROS AL DÍA', 400, seg(u, u3 + 0.2, u3 + 0.5), col=AMARILLO, size=30)
        pill(img, fx, 540, 1430, 'SATÉLITES Y COHETES', eout(seg(u, 0.2, 0.5)), size=30, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, sum(golpe_k(u, u3 + 0.2 * j + 0.9, 0.25) for j in range(3)), amp=10)


# 11. en 2024 un pedazo de la estación espacial atravesó el techo de una casa en Florida
def s_florida(t, fi, u, d):
    ua = wt(11, 10) - 0.15                       # «atravesó»
    fr = Frame(cam(u, [K(-0.4, 5.0, -50, 26, ty=0.9), K(0.3, 4.4, -22, 22, ty=0.9), K(ua + 0.1, 3.2, 8, 30, ty=1.1), K(5.0, 3.1, 10, 30, ty=1.1)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    PR = np.array([0.3, 1.39, 0.2])
    hoyo = seg(u, ua, ua + 0.08)
    draw_objects(fr, casa(t=(0, 0, 0), luz=0.8))
    ph = fr.cam.p1(tuple(PR))
    if u < ua:
        k = seg(u, ua - 1.2, ua)
        p = PR + np.array([0.8, 4.0, 0.6]) * (1 - k) ** 1.3
        bola_fuego(fr, p, PR - (PR + np.array([0.8, 4.0, 0.6])), k=1.0, largo=1.4, r=8, t=t)
        draw_objects(fr, pedazo(t=tuple(p), s=1.0, rz=30, caliente=0.8))
    else:
        for j in range(7):                        # astillas del techo
            v = u - ua
            a0 = j * 0.9
            q = PR + np.array([0.5 * math.cos(a0) * v * 2, 0.9 * v - 2.5 * v * v, 0.5 * math.sin(a0) * v * 2])
            if q[1] > 0.9:
                dot3(fr, q, r=4, col=(200, 120, 90), a=1 - seg(v, 0.3, 0.8), glow=0.4)
    pc = fr.cam.p1(tuple(PR + np.array([0, 0.3, 0])))

    def ui(img, fx):
        kicker(img, 'FLORIDA · MARZO 2024', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if hoyo > 0:
            r = 26 * hoyo
            pts = [(ph[0] + r * (1 + 0.35 * math.sin(j * 2.7)) * math.cos(j * 0.7), ph[1] + 0.55 * r * (1 + 0.35 * math.sin(j * 2.7)) * math.sin(j * 0.7))
                   for j in range(9)]
            ImageDraw.Draw(img).polygon(pts, fill=(14, 10, 10))
        if u > ua:
            pill(img, fx, pc[0], pc[1] - 110, 'PEDAZO DE ~10 CM', eout(seg(u, ua + 0.15, ua + 0.4)), size=32, border=ROJO)
            doodle_arrow(img, fx, pc[0] + 200, pc[1] - 250, pc[0] + 20, pc[1] - 20, t, k=eout(seg(u, ua + 0.3, ua + 0.7)), col=AMARILLO, w=6)
        pill(img, fx, 540, 1430, 'CONFIRMADO POR LA NASA', eout(seg(u, ua + 0.8, ua + 1.1)), size=30, border=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua, 0.4), amp=24)


# 12. que se sepa, todavía no ha herido a nadie (contador de heridos que se queda en 0)
def s_nadie(t, fi, u, d):
    un = wt(12, 8) - 0.1                         # «nadie»
    fr = Frame(cam(u, [K(-0.4, 3.6, 30, 22, ty=0.6), K(0.3, 4.0, 4, 16, ty=0.6), K(4.0, 4.0, 0, 16, ty=0.6)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.6)
    draw_objects(fr, pedazo(t=(0, 0.14, 0), s=1.6, rz=90, ry=30 + 10 * t))

    def ui(img, fx):
        kicker(img, 'HERIDOS CONFIRMADOS', 300, seg(u, -0.1, 0.2), col=(150, 210, 230), size=34)
        num = '0' if u > un else '?'
        P.numero_golpe(img, fx, num, 640, 1.0 if u < un else seg(u, un, un + 0.18), size=360, col=VERDE if u > un else WHITE)
        pill(img, fx, 540, 1430, 'QUE SE SEPA', eout(seg(u, 0.2, 0.5)), size=34, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.18, 0.35), amp=18)


# 13. si encuentras un pedazo, no lo toques: puede traer restos de combustible tóxico (vapores + TÓXICO de cristal)
def s_toxico(t, fi, u, d):
    un = wt(13, 4) - 0.1                         # «no lo toques»
    ut = wt(13, 7) - 0.1                         # «puede traer…»
    fr = Frame(cam(u, [K(-0.4, 2.6, -60, 30, ty=0.4), K(0.25, 3.0, -20, 22, ty=0.4), K(ut, 3.6, 16, 16, ty=0.6), K(5.0, 3.6, 20, 16, ty=0.6)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9)
    M.cristal(fr.base, fr.fx, 'TÓXICO', u, t0=ut, cy=0.36, entrada='sube', brillo=1.0)
    draw_objects(fr, tanque(t=(0, 0.42, 0), s=0.75, ry=25, rz=8, quemado=0.8))
    humo(fr, t, (0.2, 0.7, 0.1), k=seg(u, ut, ut + 0.4), col=(160, 240, 120), n=5, alto=1.3)
    pc = fr.cam.p1((0, 0.45, 0))

    def ui(img, fx):
        kicker(img, '¡OJO!', 150, seg(u, -0.1, 0.1), col=ROJO, size=34)
        if u > un:
            tache(img, fx, 540, 1430, seg(u, un, un + 0.25), 'NO LO TOQUES')
            doodle_circle(img, fx, pc[0], pc[1], 300, 200, t, k=eout(seg(u, un, un + 0.4)), col=ROJO, w=7)
        if u > ut + 0.4:
            pill(img, fx, 540, 1300, 'COMBUSTIBLE TÓXICO', eout(seg(u, ut + 0.4, ut + 0.7)), size=32, border=(160, 240, 120))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un, 0.35), amp=18)


# 14. aléjate y avisa a protección civil (la cámara sale volando hacia atrás y el celular llama)
def scr_llamada(u):
    def dib(d, im):
        d.text((210, 230), 'LLAMANDO…', font=M.font('mono', 30), fill=(150, 210, 230), anchor='mm')
        d.text((210, 330), 'Protección', font=M.font('sans', 52), fill=(240, 240, 244), anchor='mm')
        d.text((210, 395), 'Civil', font=M.font('sans', 52), fill=(240, 240, 244), anchor='mm')
        r = 46 + 6 * math.sin(u * 9)
        d.ellipse((210 - r, 700 - r, 210 + r, 700 + r), fill=(60, 200, 110))
        d.text((210, 700), '✆', font=M.font('sans', 56), fill=(255, 255, 255), anchor='mm')
    return P.pantalla(dib)


def s_avisa(t, fi, u, d):
    ua = wt(14, 2) - 0.1                         # «avisa»
    if u < ua:
        k = P.eout4(seg(u, -0.3, ua))
        fr = Frame(Cam(target=(0, 0.4, 0), dist=2.2 + 5.5 * k, yaw=-20 + 30 * k, pitch=30 + 20 * k, cy=0.55))
        space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0)
        draw_objects(fr, tanque(t=(0, 0.42, 0), s=0.75, ry=25, rz=8, quemado=0.8))
        th = np.linspace(0, 2 * math.pi, 60)
        line3(fr, [(2.2 * math.cos(a), 0.02, 2.2 * math.sin(a)) for a in th], col=AMARILLO, w=3, a=k, glow=0.9, frac=k)

        def ui(img, fx):
            P.titulo_golpe(img, fx, [('Aléjate.', 'sans')], 260, seg(u, -0.1, 0.05), size=110)
        fr.ui.append(ui)
        return finish(fr, fi)
    v = u - ua
    fr = Frame(cam(v, [K(-0.1, 3.6, 40, 10, ty=0.95), K(0.3, 3.0, 8, 6, ty=0.95), K(3.0, 2.9, 4, 6, ty=0.95)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    e = P.entrada(v, 0.0, 0.25, 'pop')
    draw_objects(fr, P.tfk(P.celular(scr_llamada(u)), s=max(0.05, e['escala'])))

    def ui(img, fx):
        kicker(img, 'EN MÉXICO', 150, seg(v, 0.0, 0.2), col=(150, 210, 230))
        check(img, fx, 540, 1430, seg(v, 0.3, 0.55), 'AVISA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.2, 0.3), amp=12)


# 15. mándaselo a quien se llevaría el pedazo de recuerdo (el pedazo en una repisa con etiqueta «recuerdo»… tachada)
def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.4, 4.0, -40, 12, ty=0.9), K(0.3, 3.4, -10, 10, ty=0.9), K(4.0, 3.3, -6, 10, ty=0.9)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.55)
    rep = named(M3.box(2.2, 0.08, 0.6, (120, 84, 56), shadow=0, base=True, gloss=0.3).tf(t=(0, 0.7, 0)), 'repisa', rim=0.5)
    e = P.entrada(u, 0.1, 0.3, 'cae')
    draw_objects(fr, [rep] + pedazo(t=(0, 0.99 - e['dy'] * 0.3, 0), s=1.4, rz=90, ry=20))
    pp = fr.cam.p1((0, 1.25, 0))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien se lo', 'sans'), ('llevaría de recuerdo.', 'serif')], 190, seg(u, -0.1, 0.25), size=66)
        pill_ = 'RECUERDO'
        P.pill_tachada(img, fx, pp[0], pp[1] - 120, pill_, seg(u, 0.4, 0.7), seg(u, 1.0, 1.4), t)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.4, 0.3), amp=12)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.6, 0.62), sfx=[]),
           dict(desde=1, fn=s_swift, tr='zoom', sfx=[]),
           dict(desde=2, fn=s_kilos, tr='giro', sfx=[]),
           dict(desde=3, fn=s_rescate, tr='deslizar', sfx=[]),
           dict(desde=4, fn=s_indonesia, tr='remolino', c=(0.7, 0.5), sfx=[]),
           dict(desde=5, fn=s_fuego, tr='cristal', palabra='FUEGO', sfx=[]),
           dict(desde=6, fn=s_diez, tr='rompe', c=(0.45, 0.5), sfx=[]),
           dict(desde=7, fn=s_tanque, tr='iris', c=(0.5, 0.58), sfx=[]),
           dict(desde=8, fn=s_2100, tr='golpe', sfx=[]),
           dict(desde=9, fn=s_regla, tr='wipe', sfx=[]),
           dict(desde=10, fn=s_diario, tr='rebanadas', sfx=[]),
           dict(desde=11, fn=s_florida, tr='cubo', sfx=[]),
           dict(desde=12, fn=s_nadie, tr='deslizar_abajo', sfx=[]),
           dict(desde=13, fn=s_toxico, tr='glitch', sfx=[]),
           dict(desde=14, fn=s_avisa, tr='whip', sfx=[]),
           dict(desde=15, fn=s_mandalo, tr='mosaico', sfx=[]),
           dict(desde=16, loop=True, tr='flash')]


def _sfx_dinamicos():
    E = ESCENAS
    E[0]['sfx'] = [(-1.6, 'whoosh_suave', 0.5), (UC - 0.4, 'riser', 0.5), (UC - 0.05, 'whoosh', 0.8), (UL, 'sub', 1.0), (UL, 'thud', 1.0),
                   (UL + 0.02, 'burst', 0.4), (UL + 0.15, 'bass', 0.8)]
    us = wt(1, 12) - 0.05
    E[1]['sfx'] = [(0.0, 'tick', 0.6), (wt(1, 8) - 0.1, 'click', 0.6), (us + 0.28, 'slap', 1.0), (us + 0.3, 'thud', 0.5)]
    ua = wt(2, 4) - 0.1
    E[2]['sfx'] = [(-0.3, 'whoosh', 0.6)] + [(0.0 + 0.09 * i, 'tick2', 0.3) for i in range(9)] + [(0.9, 'bass', 0.8)] + \
                  [(ua + 0.12 * j, 'chime_a' if j % 2 else 'chime_b', 0.35) for j in range(6)] + [(ua + 1.2, 'tick', 0.6)]
    ug = wt(3, 7) - 0.1
    E[3]['sfx'] = [(0.0, 'whoosh_suave', 0.6), (0.2, 'click', 0.5), (ug, 'burst', 0.5), (ug, 'sub', 0.8), (ug + 0.1, 'whoosh', 0.7),
                   (ug + 0.2, 'scribble', 0.5)]
    ui0, uh = wt(4, 5) - 0.1, wt(4, 8) - 0.1
    E[4]['sfx'] = [(-0.2, 'whoosh_suave', 0.6), (ui0, 'whoosh', 0.6), (ui0 + 0.3, 'bass', 0.9), (uh, 'click', 0.8), (uh + 0.02, 'tick', 0.6),
                   (uh + 0.6, 'tick2', 0.5)]
    ub = wt(5, 11) - 0.1
    E[5]['sfx'] = [(0.0, 'riser', 0.7), (0.1, 'whoosh_suave', 0.6)] + [(0.1 + 0.12 * i, 'tick2', 0.25) for i in range(10)] + \
                  [(ub, 'burst', 0.9), (ub, 'sub', 0.9)]
    up, u10 = wt(6, 4) - 0.1, wt(6, 7) - 0.15
    E[6]['sfx'] = [(-0.2, 'burst', 0.6), (0.0, 'whoosh', 0.6), (up, 'thud', 0.7), (up + 0.2, 'scribble', 0.5), (u10, 'bass', 1.0)]
    uk, ue = wt(7, 9) - 0.1, wt(7, 12) - 0.1
    E[7]['sfx'] = [(-0.05, 'thud', 1.0), (-0.03, 'sub', 0.6), (uk, 'tick', 0.7), (ue, 'click', 0.9), (ue + 0.1, 'click', 0.6)]
    un = wt(8, 6) - 0.1
    E[8]['sfx'] = [(0.0, 'sub', 0.8)] + [(-0.2 + 0.1 * i, 'tick2', 0.2) for i in range(8)] + [(un, 'bass', 1.0), (un + 0.05, 'scribble', 0.5),
                                                                                                   (wt(8, 14) - 0.1, 'whoosh', 0.5)]
    um = wt(9, 6) - 0.1
    E[9]['sfx'] = [(0.25, 'chime_a', 0.6), (0.53, 'chime_c', 0.6), (um, 'bass', 0.7), (um + 0.05, 'tick', 0.6)]
    u3 = wt(10, 9) - 0.1
    E[10]['sfx'] = [(0.0, 'whoosh_suave', 0.5), (u3, 'tick', 0.7)] + [(u3 + 0.2 * j, 'whoosh', 0.45) for j in range(3)] + \
                   [(u3 + 0.2 * j + 0.9, 'thud', 0.5) for j in range(3)] + [(0.2, 'click', 0.5)]
    ua11 = wt(11, 10) - 0.15
    E[11]['sfx'] = [(0.0, 'tick', 0.6), (ua11 - 1.2, 'whoosh_suave', 0.6), (ua11, 'sub', 1.0), (ua11, 'vidrio', 0.5), (ua11 + 0.02, 'thud', 0.9),
                    (ua11 + 0.15, 'click', 0.5), (ua11 + 0.3, 'scribble', 0.5), (ua11 + 0.8, 'tick2', 0.5)]
    un12 = wt(12, 8) - 0.1
    E[12]['sfx'] = [(0.0 + 0.1 * i, 'tick2', 0.2) for i in range(int(max(1, un12) / 0.1))] + [(un12 + 0.18, 'bass', 1.0), (0.2, 'click', 0.5),
                                                                                              (un12 + 0.2, 'chime_c', 0.6)]
    un13, ut13 = wt(13, 4) - 0.1, wt(13, 7) - 0.1
    E[13]['sfx'] = [(-0.1, 'tick', 0.6), (un13, 'sub', 0.9), (un13 + 0.02, 'scribble', 0.6), (ut13, 'shimmer', 0.5), (ut13 + 0.4, 'tick2', 0.5)]
    ua14 = wt(14, 2) - 0.1
    E[14]['sfx'] = [(-0.1, 'whoosh', 0.8), (0.0, 'bass', 0.7), (ua14, 'whoosh', 0.6), (ua14 + 0.2, 'click', 0.7), (ua14 + 0.35, 'chime_b', 0.6),
                    (ua14 + 0.8, 'chime_b', 0.4)]
    E[15]['sfx'] = [(0.0, 'shimmer', 0.5), (0.4, 'thud', 0.8), (0.42, 'tick', 0.5), (1.0, 'scribble', 0.6)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
