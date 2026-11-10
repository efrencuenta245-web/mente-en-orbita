"""Reel diario jue 12-nov-2026 18:00 — «Tu razer no se voltea solo.» (la física del vuelco de un side by side).
Comunidad: riders (continuación del reel VIRAL del razer del 9-nov; aquel fue la historia de las marcas, este es la física).
Inicio tipo 10 (rayos X de golpe): un side by side REAL (foto CC0 en 3D) y en el primer golpe se vuelve de cristal y aparece
su centro de gravedad. El final («porque tu razer no se voltea solo») regresa a la foto (loop).
Voz Isaac (eleven_v4), 68.6 s. Datos y fuentes: guiones/2026-11-12_vuelco.txt (CPSC 2016 y 2014, manual de Polaris RZR,
ANSI/ROHVA 1-2016). La física (fuerza en la curva ∝ velocidad²) se muestra con un modelo 3D marcado «ESQUEMA».
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
                    chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'vuelco'
TXT = ['Tu razer no se voltea solo.',
       'Lo voltea la física… y tu pie en el acelerador.',
       'En Estados Unidos revisaron 428 accidentes de side by side:',
       'en el 68 % de los casos, se volteó.',
       'Mira por dentro: es alto y angosto…',
       'y su centro de gravedad va arriba.',
       'En la curva, una fuerza lo jala hacia afuera desde ese punto.',
       'Despacio, esa fuerza cae entre las llantas y sigue pegado al piso.',
       'Al doble de velocidad, la fuerza no se duplica: se multiplica por 4… y se voltea.',
       'Pero el error que más lastima viene después: sacar el brazo para detenerlo.',
       'El manual lo dice claro: nada de tu cuerpo afuera. Agárrate fuerte y aguanta.',
       'Adentro de la jaula estás protegido; lo que queda afuera, lo aplasta.',
       'Y de los que murieron al salir disparados, 9 de cada 10 no traían cinturón.',
       'Más de la mitad de esos accidentes pasó en una curva…',
       'y casi 4 de cada 10 volcaduras mortales, en terreno plano.',
       'Y atravesado en una duna, la norma solo le exige aguantar 33 grados de lado.',
       'Mándaselo a tu compa que maneja el razer sin cinturón,',
       'porque tu razer no se voltea solo.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-12_vuelco_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_vuelco.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-12_vuelco_words.json')

AMARILLO = (255, 236, 160)
ROJO = (255, 60, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
JAULA = (52, 98, 225)
CUERPO = (34, 36, 42)
LLANTA = (26, 26, 29)

# ------------------------------------------------------------------ fotos reales (Wikimedia Commons, CC0)
FOTOS = os.path.join(HERE, 'img', 'canam')
CRED = {'rzr24': 'FOTO: HJUDALL · CC0 · WIKIMEDIA COMMONS', 'rzr23': 'FOTO: HJUDALL · CC0 · WIKIMEDIA COMMONS'}
VEH = {n: F3.preparar(f'{FOTOS}/canam_i_{n}.jpg', n) for n in ('rzr24', 'rzr23')}


def veh(img, fx, n, cx, piso, alto, yaw=0.0, pitch=0.15, t=0.0, alfa=1.0, xray=0.0, dy=0.0, borde=0.55):
    a = VEH[n]
    luz = (-0.65 + 0.55 * math.sin(t * 0.9), -0.62)
    return F3.dibujar(img, a, cx, piso - alto * 0.5 + dy, alto, yaw=yaw, pitch=pitch, luz=luz, fx=fx, alfa=alfa,
                      reflejo=0.22, borde=borde, piso_y=piso + dy, xray=xray)


def credito(img, txt, y=1872, k=1.0):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((540, y), txt, font=M.font('mono', 19), fill=M.scale_c((150, 150, 158), k), anchor='mm')


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
            if L[k] is None and last is not None:
                L[k] = last + 0.25
            last = L[k] if L[k] is not None else last
        base = next(x for x in L if x is not None)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wu(i, k):
    L = _wt()[i]
    return L[min(k, len(L) - 1)]


# ------------------------------------------------------------------ utilidades
def cam(u, claves, cy=0.55):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p.get('tx', 0.0), p.get('ty', 0.8), p.get('tz', 0.0)), dist=p['dist'], yaw=p['yaw'],
               pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch, tx=0.0, ty=0.8, tz=0.0, roll=0.0):
    return (u, dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll))


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


def flecha(img, fx, x0, y0, x1, y1, col, k=1.0, w=8):
    if k <= 0.01:
        return
    x1, y1 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    df.line([(x0, y0), (x1, y1)], fill=M.scale_c(col, 0.6), width=w * 3)
    a = math.atan2(y1 - y0, x1 - x0)
    L = 28 + w
    for s in (-1, 1):
        xa, ya = x1 - L * math.cos(a + s * 0.5), y1 - L * math.sin(a + s * 0.5)
        d.line([(x1, y1), (xa, ya)], fill=col, width=w)
        df.line([(x1, y1), (xa, ya)], fill=M.scale_c(col, 0.6), width=w * 3)


def esquema(img, fx, k=1.0, y=1440):
    pill(img, fx, 540, y, 'ESQUEMA', k, size=20, border=(150, 150, 160), dot=False)


# ------------------------------------------------------------------ side by side en 3D (frente hacia +x; ancho en z)
HUELLA = 0.95      # borde exterior de las llantas (|z|)
CG = (0.0, 0.88, 0.0)


def tubo(p0, p1, r=0.035, col=JAULA, n=6, name='jaula'):
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
    m = M3.Mesh(V, F, col, shadow=0, gloss=0.8, double=True)
    return named(m, name, rim=0.8, gloss=0.8)


def sxs(giro=0.0, color_jaula=JAULA):
    ms = []

    def B(sx, sy, sz, col, x, y, z, name='cuerpo', gloss=0.5):
        ms.append(named(M3.box(sx, sy, sz, col, shadow=0, gloss=gloss).tf(t=(x, y, z)), name, rim=0.6, gloss=gloss))
    B(2.3, 0.1, 1.2, (44, 44, 50), 0, 0.36, 0, gloss=0.2)                        # piso
    for z in (-0.6, 0.6):
        B(1.4, 0.32, 0.06, CUERPO, -0.1, 0.44, z)                                 # costados
    B(0.75, 0.34, 1.15, CUERPO, 0.95, 0.42, 0)                                    # cofre
    B(0.55, 0.3, 1.1, CUERPO, -0.95, 0.46, 0)                                     # caja trasera
    for z in (-0.3, 0.3):                                                         # asientos
        B(0.4, 0.14, 0.42, (60, 62, 70), -0.05, 0.48, z, name='asiento')
        B(0.1, 0.55, 0.42, (60, 62, 70), -0.28, 0.6, z, name='asiento')
    # jaula
    P_ = {}
    for sx in (-1, 1):
        for sz in (-1, 1):
            P_[(sx, sz)] = (0.55 * sx - 0.15, 1.55, 0.55 * sz)
            ms.append(tubo((0.62 * sx - 0.12, 0.48, 0.6 * sz), P_[(sx, sz)], col=color_jaula))
    for (a, b) in (((-1, -1), (1, -1)), ((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
        ms.append(tubo(P_[a], P_[b], col=color_jaula))
    ms.append(tubo(P_[(-1, -1)], P_[(1, 1)], r=0.03, col=color_jaula))
    # llantas (taco grande)
    for x in (-0.88, 0.88):
        for sz in (-1, 1):
            zc = sz * 0.8
            ms.append(named(M3.cyl(0.36, 0.3, LLANTA, n=18, shadow=0, gloss=0.15).tf(rx=90, t=(x, 0.36, zc - 0.15)), 'llanta', rim=0.3))
            ms.append(named(M3.cyl(0.2, 0.31, (70, 72, 80), n=10, shadow=0, gloss=0.7).tf(rx=90, t=(x, 0.36, zc - 0.155)), 'rin', rim=0.6))
            bx, by = x + 0.1 * math.cos(giro), 0.36 + 0.1 * math.sin(giro)
            ms.append(named(M3.box(0.06, 0.06, 0.33, (120, 120, 128), shadow=0, base=False).tf(t=(bx, by, zc)), 'birlo'))
            ms.append(tubo((x * 0.6, 0.4, sz * 0.5), (x, 0.36, zc - sz * 0.1), r=0.03, col=(90, 92, 100), name='brazo'))
    return ms


def volcar(ms, ang, lado=1):
    """Gira el vehículo `ang` grados sobre el borde de sus llantas del lado `lado` (+1 = derecha en vista trasera)."""
    piv = np.array([0, 0, lado * HUELLA])
    ms = P.tfk(ms, t=tuple(-piv))
    ms = P.tfk(ms, rx=lado * ang)
    return P.tfk(ms, t=tuple(piv))


def cg_rot(ang, lado=1):
    piv = np.array([0, 0, lado * HUELLA])
    p = np.array(CG) - piv
    a = math.radians(lado * ang)
    y = p[1] * math.cos(a) - p[2] * math.sin(a)
    z = p[1] * math.sin(a) + p[2] * math.cos(a)
    return (p[0] + piv[0], y + piv[1], z + piv[2])


def trasera(t, u, claves, cy=0.56, floor='lines'):
    fr = Frame(cam(u, claves, cy=cy))
    space(fr, t, floor=floor, floor_a=0.8, bokeh=0.9, beam=0.35)
    return fr


def base_huella(fr, k=1.0, col=CYAN):
    line3(fr, [(0, 0.01, -HUELLA), (0, 0.01, HUELLA)], col=col, w=6, a=0.9 * k, glow=1.2)
    for s in (-1, 1):
        line3(fr, [(0, 0.01, s * HUELLA), (0, 0.01, s * (HUELLA + 0.9))], col=ROJO, w=4, a=0.6 * k, glow=0.8)


def mira_cg(img, fx, x, y, t, k=1.0, col=AMARILLO, r=34):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    rr = r * P.resorte(k)
    d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=col, width=5)
    d.pieslice((x - rr, y - rr, x + rr, y + rr), 0, 90, fill=col)
    d.pieslice((x - rr, y - rr, x + rr, y + rr), 180, 270, fill=col)
    df.ellipse((x - rr * 1.8, y - rr * 1.8, x + rr * 1.8, y + rr * 1.8), fill=M.scale_c(col, 0.35 * k))
    for s in (-1, 1):
        d.line([(x + s * rr * 1.2, y), (x + s * rr * 2.0, y)], fill=col, width=4)
        d.line([(x, y + s * rr * 1.2), (x, y + s * rr * 2.0)], fill=col, width=4)


def fuerzas(fr, img, fx, g_lat, k=1.0, ang=0.0, lado=1, escala=230):
    """Peso (abajo), fuerza de la curva (de lado, ∝ g_lat) y la resultante que pega en el piso: dentro o fuera de las llantas."""
    cg = np.array(cg_rot(ang, lado))
    x0, y0, _ = fr.cam.p1(tuple(cg))
    zg = cg[2] + cg[1] * g_lat * lado
    xg, yg, _ = fr.cam.p1((0, 0.0, zg))
    xl, yl, _ = fr.cam.p1(tuple(cg + np.array([0, 0, lado * 0.9 * g_lat])))
    flecha(img, fx, x0, y0, x0, y0 + escala, WHITE, k=eout(seg(k, 0.0, 0.5)), w=7)
    flecha(img, fx, x0, y0, xl, yl, AMARILLO, k=eout(seg(k, 0.2, 0.7)), w=8)
    afuera = abs(zg) > HUELLA
    col = ROJO if afuera else CYAN
    kk = eout(seg(k, 0.5, 1.0))
    if kk > 0.01:
        d = ImageDraw.Draw(img)
        n = 14
        for j in range(n):
            if j % 2:
                continue
            a0, a1 = j / n * kk, (j + 1) / n * kk
            d.line([(lerp(x0, xg, a0), lerp(y0, yg, a0)), (lerp(x0, xg, a1), lerp(y0, yg, a1))], fill=col, width=6)
        if kk > 0.95:
            ImageDraw.Draw(fx).ellipse((xg - 30, yg - 16, xg + 30, yg + 16), fill=M.scale_c(col, 0.7))
            d.ellipse((xg - 12, yg - 7, xg + 12, yg + 7), fill=col)
    return afuera, (xg, yg), (x0, y0)


# ================================================================== escenas
# 0. gancho, inicio tipo 10 (rayos X de golpe): el side by side real se vuelve de cristal y aparece su centro de gravedad
UX = 0.12


def s_gancho(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.85, bokeh=1.0, beam=0.55)
    pose = P.cam_rapida(u, [(-4.0, dict(yaw=-0.7, al=600, x=540)), (UX, dict(yaw=-0.2, al=640, x=540)),
                            (UX + 0.05, dict(yaw=0.35, al=700, x=540)), (3.0, dict(yaw=0.6, al=720, x=540))])
    kx = seg(u, UX, UX + 0.12)

    def ui(img, fx):
        M.cristal(img, fx, 'RAZER', u, t0=-2.3, cy=0.36, entrada='golpe')
        piso = 1260
        r = veh(img, fx, 'rzr24', pose['x'], piso, pose['al'], yaw=pose['yaw'], pitch=0.15, t=t, xray=kx, borde=0.55 + 0.6 * kx)
        if r and kx > 0:
            x0, y0, w, h = r
            cx, cy = x0 + w * 0.5, y0 + h * 0.5
            dd = ImageDraw.Draw(img)
            for j in range(12):
                yy = cy + 16 * j
                if yy < piso:
                    dd.line([(cx, yy), (cx, yy + 8)], fill=M.scale_c(AMARILLO, kx), width=3)
            mira_cg(img, fx, cx, cy, t, k=seg(u, UX + 0.05, UX + 0.35))
            pill(img, fx, cx + 190, cy - 80, 'CENTRO DE GRAVEDAD', eout(seg(u, UX + 0.25, UX + 0.5)), size=26, border=AMARILLO)
        kicker(img, 'SIDE BY SIDE · FOTO REAL · RAYOS X', 140, seg(u, UX, UX + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu razer', 'sans'), ('no se voltea solo.', 'serif')], 190, seg(u, UX, UX + 0.15), size=92)
        credito(img, CRED['rzr24'])
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, UX, 0.4), amp=24)


# 1. lo voltea la física… y tu pie en el acelerador (vista de arriba: entra a la curva y el velocímetro sube)
def s_fisica(t, fi, u, d):
    ua = Wu(1, 5) - 0.1                                    # «tu pie en el acelerador»
    vel = 0.5 + 0.9 * P.eout4(seg(u, ua, ua + 0.8))
    R = 3.2
    C = np.array([0, 0, -R])
    q0 = 0.35 * math.sin(t * vel)                          # posición sobre la curva
    pos = C + np.array([R * math.sin(q0), 0, R * math.cos(q0)])
    fr = Frame(cam(u, [K(-0.3, 7.0, 40, 55, tx=pos[0], ty=0.4, tz=pos[2]), K(0.4, 6.2, 10, 44, tx=pos[0], ty=0.4, tz=pos[2]),
                       K(ua, 5.4, -14, 32, tx=pos[0], ty=0.5, tz=pos[2]), K(5, 5.3, -18, 32, tx=pos[0], ty=0.5, tz=pos[2])], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9)
    M.cristal(fr.base, fr.fx, 'FÍSICA', u, t0=-0.2, cy=0.3, entrada='sube')
    th = np.linspace(-1.2, 1.2, 70)
    for rr, a in ((R - 0.8, 0.5), (R + 0.8, 0.5)):
        line3(fr, [C + np.array([rr * math.sin(q), 0.01, rr * math.cos(q)]) for q in th], col=WHITE, w=2.4, a=a, glow=0.5)
    line3(fr, [C + np.array([R * math.sin(q), 0.012, R * math.cos(q)]) for q in th if q < q0], col=(210, 190, 160), w=5, a=0.6, glow=0.4)
    ms = P.tfk(sxs(giro=-t * 8 * vel), s=0.8, ry=-math.degrees(q0), t=tuple(pos))
    draw_objects(fr, ms)

    def ui(img, fx):
        dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        x, y, r = 540, 1270, 120
        k0 = eout(seg(u, -0.1, 0.2))
        dd.arc((x - r, y - r, x + r, y + r), 150, 390, fill=M.scale_c(WHITE, 0.8 * k0), width=6)
        df.arc((x - r, y - r, x + r, y + r), 320, 390, fill=M.scale_c(ROJO, 0.6 * k0), width=16)
        a = math.radians(150 + 240 * (0.15 + 0.7 * P.eout4(seg(u, ua, ua + 0.6))))
        dd.line([(x, y), (x + r * 0.85 * math.cos(a), y + r * 0.85 * math.sin(a))], fill=AMARILLO, width=7)
        dd.text((x, y + 60), 'ACELERADOR', font=M.font('mono', 24), fill=M.scale_c(GRIS, k0), anchor='mm')
        esquema(img, fx, k0, y=1430)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.1, 0.3), amp=10)


# 2. revisaron 428 accidentes (cuadrícula de 428 puntos que se llena con el contador)
def _rejilla(img, fx, u, k_llena, k_rojo, t):
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    cols, n = 18, 428
    x0, y0, s = 120, 470, 47
    nrojo = int(291 * k_rojo)
    for i in range(int(n * k_llena)):
        r_, c_ = divmod(i, cols)
        x, y = x0 + c_ * s, y0 + r_ * s
        roj = i < nrojo
        if roj:
            ph = clamp((k_rojo * 291 - i) / 20)
            sx = abs(math.cos(math.pi * (1 - ph)))
            col = ROJO
            d.rounded_rectangle((x - 16 * sx, y - 16, x + 16 * sx, y + 16), radius=6, fill=col)
            df.rounded_rectangle((x - 18 * sx, y - 18, x + 18 * sx, y + 18), radius=6, fill=M.scale_c(col, 0.35))
        else:
            d.rounded_rectangle((x - 16, y - 16, x + 16, y + 16), radius=6, outline=(200, 205, 215), width=3)


def s_428(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 6.0, 30, 12), K(0.4, 5.6, 6, 8), K(4, 5.5, 2, 8)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    kl = P.eout4(seg(u, 0.0, 1.8))

    def ui(img, fx):
        kicker(img, 'ACCIDENTES DE SIDE BY SIDE · CPSC', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 320, f'{int(round(428 * kl))}', 170, WHITE, seg(u, 0.0, 0.15), f='mono', glow=0.4)
        _rejilla(img, fx, u, kl, 0.0, t)
        pill(img, fx, 540, 1430, 'REPORTES DE 2003 A 2011 · EE. UU.', eout(seg(u, 0.6, 0.9)), size=24, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. en el 68 % se volteó («68%» de cristal detrás de la cuadrícula; los cuadros se voltean a rojo)
def s_68(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 5.2, -20, 10), K(0.4, 5.6, -4, 8), K(4, 5.7, 0, 8)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    uv = Wu(3, 7) - 0.15                                   # «se volteó»
    kr = P.eout4(seg(u, uv - 0.6, uv + 0.6))

    def ui(img, fx):
        M.cristal(img, fx, '68%', u, t0=0.0, cy=0.42, entrada='zoom')
        kicker(img, 'SE VOLTEÓ EL VEHÍCULO', 150, seg(u, -0.1, 0.2), col=(255, 140, 130))
        _rejilla(img, fx, u, 1.0, kr, t)
        texto(img, fx, 540, 320, f'{int(68 * kr)} %', 150, ROJO, seg(u, uv - 0.6, uv - 0.4), f='mono', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uv + 0.6, 0.3), amp=12)


# 4. es alto y angosto (vista trasera con cotas)
def s_alto(t, fi, u, d):
    ua = Wu(4, 4) - 0.1                                    # «angosto»
    fr = trasera(t, u, [K(-0.3, 6.2, -60, 14, ty=0.8), K(0.4, 5.6, -84, 8, ty=0.8), K(ua, 5.3, -92, 6, ty=0.8),
                        K(4, 5.2, -94, 6, ty=0.8)])
    e = P.entrada(u, -0.25, 0.4, 'cae')
    ms = P.tfk(sxs(), t=(0, max(0.0, -e['dy']) * 0.5, 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'VISTA TRASERA', 150, seg(u, -0.1, 0.2), col=AZULC)
        xa, ya, _ = fr.cam.p1((0, 0, -HUELLA - 0.15))
        xb, yb, _ = fr.cam.p1((0, 1.6, -HUELLA - 0.15))
        flecha(img, fx, xa, ya, xb, yb, AMARILLO, k=eout(seg(u, 0.2, 0.6)), w=6)
        pill(img, fx, xb, yb - 50, 'ALTO', eout(seg(u, 0.4, 0.7)), size=34, border=AMARILLO, dot=False)
        x1, y1, _ = fr.cam.p1((0, -0.05, -HUELLA))
        x2, y2, _ = fr.cam.p1((0, -0.05, HUELLA))
        ka = eout(seg(u, ua, ua + 0.4))
        flecha(img, fx, (x1 + x2) / 2, y1 + 60, x1, y1 + 60, CYAN, k=ka, w=6)
        flecha(img, fx, (x1 + x2) / 2, y1 + 60, x2, y2 + 60, CYAN, k=ka, w=6)
        pill(img, fx, (x1 + x2) / 2, y1 + 130, 'ANGOSTO', ka, size=34, border=CYAN, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. su centro de gravedad va arriba (la mira aparece; «CENTRO» de cristal detrás)
def s_cg(t, fi, u, d):
    fr = trasera(t, u, [K(-0.3, 3.4, -100, 4, ty=0.9), K(0.4, 3.9, -80, 8, ty=0.9), K(4, 4.0, -76, 8, ty=0.9)])
    M.cristal(fr.base, fr.fx, 'CENTRO', u, t0=-0.1, cy=0.33, entrada='golpe')
    draw_objects(fr, sxs(), xray=0.85, keep=('llanta', 'rin'))
    x, y, _ = fr.cam.p1(CG)
    xg, yg, _ = fr.cam.p1((0, 0, 0))

    def ui(img, fx):
        mira_cg(img, fx, x, y, t, k=seg(u, 0.0, 0.35), r=40)
        dd = ImageDraw.Draw(img)
        for j in range(int((yg - y) / 18)):
            dd.line([(x, y + 50 + 18 * j), (x, y + 58 + 18 * j)], fill=AMARILLO, width=3)
        pill(img, fx, x, y - 120, 'CENTRO DE GRAVEDAD', eout(seg(u, 0.3, 0.6)), size=30, border=AMARILLO)
        pill(img, fx, x + 250, (y + yg) / 2, 'ARRIBA', eout(seg(u, 0.9, 1.2)), size=30, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. en la curva, una fuerza lo jala hacia afuera desde ese punto (vista de arriba, flecha que sale del centro)
def s_curva(t, fi, u, d):
    uf = Wu(6, 5) - 0.1                                    # «hacia afuera»
    fr = Frame(cam(u, [K(-0.3, 6.0, -30, 60, ty=0.3, tz=-0.2), K(0.4, 5.2, -10, 48, ty=0.4), K(uf, 4.6, 14, 40, ty=0.5),
                       K(5, 4.5, 18, 40, ty=0.5)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9)
    R = 3.0
    C = np.array([0, 0, -R])
    th = np.linspace(-1.1, 1.1, 60)
    for rr in (R - 0.9, R + 0.9):
        line3(fr, [C + np.array([rr * math.sin(q), 0.01, rr * math.cos(q)]) for q in th], col=WHITE, w=2.4, a=0.6, glow=0.5)
    q0 = 0.15 * math.sin(t * 1.5)
    pos = C + np.array([R * math.sin(q0), 0, R * math.cos(q0)])
    ms = P.tfk(sxs(giro=-t * 9), s=0.85, ry=-math.degrees(q0), t=tuple(pos))
    draw_objects(fr, ms)
    cg = pos + np.array([0, 0.75, 0])
    x0, y0, _ = fr.cam.p1(tuple(cg))
    x1, y1, _ = fr.cam.p1(tuple(cg + M.norm(pos - C) * 1.6))

    def ui(img, fx):
        mira_cg(img, fx, x0, y0, t, k=1.0, r=26)
        flecha(img, fx, x0, y0, x1, y1, AMARILLO, k=eout(seg(u, uf, uf + 0.35)), w=9)
        pill(img, fx, x1, y1 + 60, 'HACIA AFUERA', eout(seg(u, uf + 0.2, uf + 0.5)), size=32, border=AMARILLO, dot=False)
        kicker(img, 'EN LA CURVA', 150, seg(u, -0.1, 0.2), col=AZULC)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. caso 1, despacio: la fuerza cae entre las llantas y sigue pegado al piso
def s_despacio(t, fi, u, d):
    fr = trasera(t, u, [K(-0.3, 5.0, -70, 8, ty=0.75), K(0.4, 4.6, -88, 6, ty=0.75), K(4, 4.5, -92, 6, ty=0.75)])
    base_huella(fr, k=seg(u, 0.0, 0.4))
    draw_objects(fr, sxs(), xray=0.6, keep=('llanta', 'rin'))

    def ui(img, fx):
        texto(img, fx, 540, 250, 'DESPACIO', 96, WHITE, eout(seg(u, -0.1, 0.15)), f='sansx', glow=0.3)
        kicker(img, 'CASO 1', 360, seg(u, 0.0, 0.3), col=AZULC)
        af, (xg, yg), _ = fuerzas(fr, img, fx, 0.32, k=seg(u, 0.2, 1.6))
        pill(img, fx, xg, yg + 70, '✓ ENTRE LAS LLANTAS', eout(seg(u, 1.4, 1.7)), size=30, border=CYAN, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. caso 2: al doble de velocidad la fuerza se multiplica por 4… y se voltea («×4» de cristal; vuelco con sacudida)
def s_x4(t, fi, u, d):
    u4 = Wu(8, 10) - 0.1                                   # «se multiplica por cuatro»
    uv = Wu(8, 14) - 0.15                                  # «y se voltea»
    ang = 92 * P.rebote(seg(u, uv, uv + 0.9), n=1.5, amort=7) if u > uv else 0.0
    fr = trasera(t, u, [K(-0.3, 5.0, -92, 6, ty=0.75), K(0.4, 5.6, -76, 10, ty=0.8), K(uv, 6.6, -100, 12, ty=0.8, tz=1.0),
                        K(5, 6.7, -104, 12, ty=0.8, tz=1.0)])
    M.cristal(fr.base, fr.fx, '×4', u, t0=u4, cy=0.3, entrada='golpe')
    base_huella(fr)
    draw_objects(fr, volcar(sxs(), ang), xray=0.6 if ang < 5 else 0.0, keep=('llanta', 'rin'))

    def ui(img, fx):
        texto(img, fx, 540, 250, 'AL DOBLE DE VELOCIDAD', 62, AMARILLO, eout(seg(u, -0.1, 0.15)), f='sansx', glow=0.3)
        kicker(img, 'CASO 2 · FUERZA ×4', 340, seg(u, u4, u4 + 0.3), col=(255, 140, 130))
        g = 0.32 + (1.28 - 0.32) * P.eout4(seg(u, u4 - 0.2, u4 + 0.4))
        if ang < 40:
            af, (xg, yg), _ = fuerzas(fr, img, fx, g, k=1.0 if u > 0.4 else seg(u, -0.2, 0.4), ang=ang)
            if af:
                pill(img, fx, xg, yg + 70, '✗ AFUERA DE LAS LLANTAS', eout(seg(u, u4 + 0.4, u4 + 0.7)), size=28, border=ROJO, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uv + 0.55, 0.45), amp=26)


# 9. SEGUNDO GANCHO: el error que más lastima — sacar el brazo para detenerlo (a medio vuelco, zona roja de afuera)
def s_brazo(t, fi, u, d):
    ub = Wu(9, 9) - 0.1                                    # «sacar el brazo»
    ang = 48 + 6 * seg(u, 0.0, 4.0)
    fr = trasera(t, u, [K(-0.3, 4.2, -120, 10, ty=0.9, tz=0.6), K(0.4, 4.8, -96, 8, ty=0.9, tz=0.6), K(ub, 5.0, -84, 6, ty=0.8, tz=0.8),
                        K(5, 4.9, -80, 6, ty=0.8, tz=0.8)])
    M.cristal(fr.base, fr.fx, 'BRAZO', u, t0=0.0, cy=0.3, entrada='sube')
    draw_objects(fr, volcar(sxs(), ang))
    # zona de aplastamiento: entre la jaula y el piso del lado que cae
    za = []
    for j in range(9):
        z = HUELLA + 0.1 + 0.16 * j
        za.append(((0.5, 0.02, z), (-0.5, 0.02, z)))
    for a, b in za:
        line3(fr, [a, b], col=ROJO, w=3, a=0.8 * seg(u, ub - 0.2, ub + 0.3), glow=0.9)
    pc = fr.cam.p1(cg_rot(ang))
    pz = fr.cam.p1((0, 0.05, HUELLA + 0.75))

    def ui(img, fx):
        kicker(img, 'EL ERROR QUE MÁS LASTIMA', 150, seg(u, -0.1, 0.1), col=(255, 140, 130))
        P.titulo_golpe(img, fx, [('Sacar el brazo', 'sans'), ('para detenerlo.', 'serif')], 200, seg(u, ub, ub + 0.15), size=84)
        if u > ub:
            flecha(img, fx, pc[0], pc[1], pz[0], pz[1] - 10, ROJO, k=eout(seg(u, ub + 0.1, ub + 0.4)), w=9)
            N.doodle_arrow_free(img, fx, pz[0] - 90, pz[1] - 90, pz[0] + 90, pz[1] + 50, t, seg(u, ub + 0.4, ub + 0.6), WHITE, seed=3)
            N.doodle_arrow_free(img, fx, pz[0] + 90, pz[1] - 90, pz[0] - 90, pz[1] + 50, t, seg(u, ub + 0.5, ub + 0.7), WHITE, seed=4)
        pill(img, fx, pz[0], pz[1] + 90, 'ZONA DE APLASTAMIENTO', eout(seg(u, ub + 0.3, ub + 0.6)), size=26, border=ROJO, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.15, 0.4), amp=22)


def hoja_manual(img, fx, k, t, cx=540, cy=760, w=700):
    """Página del manual (ilustración con la advertencia traducida) que cae y se balancea."""
    if k <= 0.01:
        return
    h = int(w * 1.05)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=14, fill=(244, 242, 236, 255))
    dl.rectangle((0, 0, w, 120), fill=(250, 204, 40, 255))
    dl.polygon([(60, 95), (100, 25), (140, 95)], fill=(20, 20, 22, 255))
    dl.text((100, 80), '!', font=M.font('sansx', 50), fill=(250, 204, 40, 255), anchor='ms')
    dl.text((170, 60), 'ADVERTENCIA', font=M.font('sansx', 56), fill=(20, 20, 22, 255), anchor='lm')
    lines = ['No pongas ninguna parte', 'de tu cuerpo fuera del', 'vehículo por ninguna razón.', '',
             'Agárrate fuerte del volante', 'o de las agarraderas', 'y prepárate.']
    for j, ln in enumerate(lines):
        dl.text((50, 180 + j * 64), ln, font=M.font('sanss', 44), fill=(30, 30, 34, 255))
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


# 10. el manual lo dice claro (cae la página del manual con la advertencia traducida)
def s_manual(t, fi, u, d):
    ua = Wu(10, 9) - 0.1                                   # «agárrate fuerte»
    fr = Frame(cam(u, [K(-0.3, 6.0, -30, 30), K(0.4, 5.4, -6, 22), K(5, 5.3, -2, 22)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.6)

    def ui(img, fx):
        kicker(img, 'MANUAL DEL FABRICANTE · TRADUCCIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        hoja_manual(img, fx, seg(u, -0.15, 0.55), t)
        if u > 0.6:
            doodle_circle(img, fx, 540, 470, 330, 120, t, k=seg(u, 0.7, 1.1), col=ROJO, seed=5)
        if u > ua:
            doodle_circle(img, fx, 540, 860, 330, 120, t, k=seg(u, ua, ua + 0.4), col=CYAN, seed=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.55, 0.3), amp=12)


# 11. adentro de la jaula estás protegido; lo que queda afuera, lo aplasta (foto real con la jaula marcada)
def s_jaula(t, fi, u, d):
    uo = Wu(11, 6) - 0.1                                   # «lo que queda afuera»
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.85, bokeh=1.0, beam=0.45)
    pose = P.cam_rapida(u, [(-0.3, dict(yaw=0.8, al=640)), (0.4, dict(yaw=0.1, al=760)), (uo, dict(yaw=-0.3, al=820)),
                            (5, dict(yaw=-0.45, al=830))])

    def ui(img, fx):
        r = veh(img, fx, 'rzr24', 540, 1250, pose['al'], yaw=pose['yaw'], pitch=0.12, t=t)
        if r:
            x0, y0, w, h = r
            cx, cy = x0 + w * 0.5, y0 + h * 0.28
            doodle_circle(img, fx, cx, cy, w * 0.33, h * 0.22, t, k=seg(u, 0.2, 0.6), col=CYAN, seed=2)
            pill(img, fx, cx, y0 - 30, 'ADENTRO DE LA JAULA: PROTEGIDO', eout(seg(u, 0.3, 0.6)), size=28, border=CYAN, dot=False)
            if u > uo:
                for s_ in (-1, 1):
                    xx = cx + s_ * w * 0.48
                    for j in range(7):
                        yy = y0 + h * 0.15 + j * h * 0.1
                        ImageDraw.Draw(img).line([(xx - 50, yy), (xx + 50, yy + 40)], fill=M.scale_c(ROJO, seg(u, uo, uo + 0.3)), width=5)
                pill(img, fx, 540, y0 + h + 80, 'AFUERA: TE APLASTA', eout(seg(u, uo + 0.1, uo + 0.4)), size=32, border=ROJO, dot=False)
        credito(img, CRED['rzr24'])
    fr.ui.append(ui)
    return finish(fr, fi)


def cinturon(img, fx, x, y, k, malo, t):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    s = P.resorte(k)
    col = ROJO if malo else CYAN
    w, h = 70 * s, 44 * s
    d.rounded_rectangle((x - w, y - h, x + w * 0.2, y + h), radius=12, outline=col, width=6)
    d.rectangle((x + w * 0.2, y - h * 0.35, x + w, y + h * 0.35), outline=col, width=6)
    d.rectangle((x - w * 0.6, y - h * 0.3, x - w * 0.1, y + h * 0.3), fill=col)
    df.rounded_rectangle((x - w - 8, y - h - 8, x + w + 8, y + h + 8), radius=14, fill=M.scale_c(col, 0.18))
    if malo and k > 0.6:
        N.doodle_arrow_free(img, fx, x - 80, y - 60, x + 80, y + 60, t, seg(k, 0.6, 1.0), WHITE, seed=int(x) % 7)


# 12. de los que murieron al salir disparados, 9 de cada 10 no traían cinturón (10 hebillas: 9 rojas)
def s_cinturon(t, fi, u, d):
    u9 = Wu(12, 8) - 0.1                                   # «nueve de cada diez»
    fr = Frame(cam(u, [K(-0.3, 6.0, 40, 16), K(0.4, 5.6, 10, 10), K(5, 5.5, 4, 10)]))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0)

    def ui(img, fx):
        M.cristal(img, fx, 'CINTURÓN', u, t0=-0.1, cy=0.62, entrada='zoom')
        kicker(img, 'MUERTES AL SALIR DISPARADOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.numero_golpe(img, fx, '9 de 10', 350, seg(u, u9, u9 + 0.18), size=170, col=ROJO)
        for j in range(10):
            r_, c_ = divmod(j, 5)
            cinturon(img, fx, 150 + c_ * 195, 640 + r_ * 150, seg(u, u9 + 0.1 + 0.06 * j, u9 + 0.4 + 0.06 * j), j < 9, t)
        pill(img, fx, 540, 960, 'SIN CINTURÓN', eout(seg(u, u9 + 0.9, u9 + 1.2)), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u9 + 0.18, 0.3), amp=16)


# 13. más de la mitad de esos accidentes pasó en una curva (gráfico que crece)
def s_mitad(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 6.5, -40, 30, ty=0.2), K(0.4, 6.0, -12, 24, ty=0.2), K(5, 5.9, -8, 24, ty=0.2)]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9)
    R = 3.0
    C = np.array([0, 0, -R])
    th = np.linspace(-1.3, 1.3, 70)
    for rr in (R - 0.8, R + 0.8):
        line3(fr, [C + np.array([rr * math.sin(q), 0.01, rr * math.cos(q)]) for q in th], col=WHITE, w=2.4, a=0.45, glow=0.4)

    def ui(img, fx):
        chart_grow(img, fx, (110, 380, 970, 1260), [48, 52], ['RESTO', 'EN CURVA'], 0.0, u, unit='%',
                   title_txt='ACCIDENTES (%) · CPSC', vmax=60, line=False, tag='52 %')
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. casi 4 de cada 10 volcaduras mortales, en terreno plano (el side by side de lado sobre piso plano; «PLANO» de cristal)
def s_plano(t, fi, u, d):
    fr = trasera(t, u, [K(-0.3, 6.8, -40, 22, ty=0.5, tz=1.6), K(0.4, 6.0, -62, 14, ty=0.5, tz=1.6), K(5, 5.8, -68, 14, ty=0.5, tz=1.6)],
                 floor='dots')
    M.cristal(fr.base, fr.fx, 'PLANO', u, t0=0.0, cy=0.3, entrada='sube')
    ang = 90 * P.rebote(seg(u, -0.3, 0.5), n=1.5, amort=7)
    draw_objects(fr, volcar(sxs(), ang))
    line3(fr, [(-3, 0.01, -3), (-3, 0.01, 4)], col=CYAN, w=3, a=0.8, glow=0.8)
    line3(fr, [(3, 0.01, -3), (3, 0.01, 4)], col=CYAN, w=3, a=0.8, glow=0.8)

    def ui(img, fx):
        kicker(img, 'VOLCADURAS MORTALES', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1250, 'CASI 4 DE CADA 10', 66, WHITE, seg(u, 0.4, 0.6), f='sansx', glow=0.3)
        pill(img, fx, 540, 1340, 'TERRENO PLANO · 0°', eout(seg(u, 0.6, 0.9)), size=30, border=CYAN, dot=False)
        esquema(img, fx, 1.0, y=1430)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.35), amp=18)


# 15. atravesado en una duna, la norma solo le exige aguantar 33 grados de lado (duna inclinada + arco de 33°)
def s_duna(t, fi, u, d):
    un = Wu(15, 13) - 0.1                                  # «treinta y tres grados»
    inc = 33 * ease(seg(u, 0.2, un + 0.3))
    fr = trasera(t, u, [K(-0.3, 6.2, -70, 10, ty=0.6), K(0.4, 5.8, -88, 6, ty=0.6), K(5, 5.7, -92, 6, ty=0.6)], floor=None)
    M.cristal(fr.base, fr.fx, '33°', u, t0=un, cy=0.3, entrada='golpe')
    a = math.radians(inc)
    # duna: plano inclinado (rayas de arena)
    for j in range(-6, 7):
        x = j * 0.35
        line3(fr, [(x, 3.2 * math.sin(a), -3.2 * math.cos(a)), (x, -3.2 * math.sin(a), 3.2 * math.cos(a))],
              col=(220, 200, 160), w=1.6, a=0.45, glow=0.3)
    line3(fr, [(0, 3.2 * math.sin(a), -3.2 * math.cos(a)), (0, -3.2 * math.sin(a), 3.2 * math.cos(a))], col=(240, 220, 180), w=4, a=0.9, glow=0.8)
    line3(fr, [(0, 0, -3.2), (0, 0, 3.2)], col=WHITE, w=1.6, a=0.4, glow=0.2)
    ms = P.tfk(sxs(), rx=inc)
    draw_objects(fr, ms)
    p0 = fr.cam.p1((0, 0, 0))

    def ui(img, fx):
        kicker(img, 'ATRAVESADO EN UNA DUNA', 150, seg(u, -0.1, 0.2), col=AZULC)
        dd = ImageDraw.Draw(img)
        r = 260
        ka = seg(u, 0.2, 0.5)
        if ka > 0:
            dd.arc((p0[0] - r, p0[1] - r, p0[0] + r, p0[1] + r), 0, max(1, inc), fill=AMARILLO, width=6)
            texto(img, fx, p0[0] + r - 20, p0[1] + 90, f'{int(round(inc))}°', 70, AMARILLO, ka, f='mono', glow=0.5, anchor='lm')
        pill(img, fx, 540, 1330, 'MÍNIMO DE LA NORMA (2 PERSONAS)', eout(seg(u, un + 0.3, un + 0.6)), size=26, border=AMARILLO, dot=False)
        esquema(img, fx, 1.0, y=1430)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.3, 0.3), amp=12)


# 16. mándaselo a tu compa que maneja el razer sin cinturón (el negro entra deslizándose con su título)
def s_compa(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.85, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'desliza')
    pose = P.cam_rapida(u, [(-0.3, dict(yaw=-0.9, al=600)), (0.5, dict(yaw=0.2, al=660)), (5, dict(yaw=0.45, al=680))])

    def ui(img, fx):
        veh(img, fx, 'rzr23', 540 + e['dy'] * 260, 1250, pose['al'], yaw=pose['yaw'], pitch=0.15, t=t)
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que va sin cinturón.', 'serif')], 230, seg(u, 0.05, 0.2), size=74)
        credito(img, CRED['rzr23'])
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45), sfx=[(UX, 'sub', 0.9), (UX + 0.05, 'shimmer', 0.6), (UX + 0.3, 'tick', 0.6)]),
           dict(desde=1, fn=s_fisica, tr='giro', sfx=[(1.9, 'riser', 0.4), (2.6, 'bass', 0.6)]),
           dict(desde=2, fn=s_428, tr='mosaico', sfx=[(0.1 + 0.15 * j, 'tick2', 0.35) for j in range(12)]),
           dict(desde=3, fn=s_68, tr='deslizar', sfx=[(1.4 + 0.1 * j, 'tick', 0.35) for j in range(8)] + [(2.6, 'bass', 0.6)]),
           dict(desde=4, fn=s_alto, tr='cubo', sfx=[(0.2, 'thud', 0.7), (0.4, 'click', 0.6), (1.7, 'click', 0.6)]),
           dict(desde=5, fn=s_cg, tr='iris', c=(0.5, 0.48), sfx=[(0.1, 'chime_b', 0.5)]),
           dict(desde=6, fn=s_curva, tr='whip', sfx=[(1.6, 'whoosh', 0.6)]),
           dict(desde=7, fn=s_despacio, tr='wipe', sfx=[(1.5, 'chime_a', 0.5)]),
           dict(desde=8, fn=s_x4, tr='golpe', c=(0.5, 0.5), sfx=[(2.4, 'bass', 0.8), (4.3, 'thud', 1.0), (4.35, 'burst', 0.6)]),
           dict(desde=9, fn=s_brazo, tr='rompe', c=(0.5, 0.5), sfx=[(2.6, 'bass', 0.9), (3.0, 'scribble', 0.6)]),
           dict(desde=10, fn=s_manual, tr='deslizar_abajo', sfx=[(0.55, 'slap', 0.9), (0.8, 'scribble', 0.5), (3.2, 'scribble', 0.5)]),
           dict(desde=11, fn=s_jaula, tr='cristal', palabra='JAULA', sfx=[(0.3, 'scribble', 0.5), (2.6, 'thud', 0.6)]),
           dict(desde=12, fn=s_cinturon, tr='remolino', sfx=[(2.1, 'bass', 0.8)] + [(2.2 + 0.06 * j, 'click', 0.3) for j in range(10)]),
           dict(desde=13, fn=s_mitad, tr='push', sfx=[(0.3, 'chime_a', 0.4), (0.6, 'chime_b', 0.4)]),
           dict(desde=14, fn=s_plano, tr='cubo_izq', sfx=[(0.2, 'thud', 0.9)]),
           dict(desde=15, fn=s_duna, tr='flash', sfx=[(3.4, 'chime_c', 0.5), (3.6, 'bass', 0.6)]),
           dict(desde=16, fn=s_compa, tr='ritmo', sfx=[(0.2, 'bass', 0.7)]),
           dict(desde=17, loop=True, tr='zoom')]

if __name__ == '__main__':
    montaje.cli(globals())
