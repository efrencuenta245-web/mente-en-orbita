"""Video largo de YouTube: ¿Por qué GTA 6 tardó tanto en salir? (y sus reels).
Estilo: fondo blanco con piso de puntos, objetos 3D a color, tarjetas en blanco y negro entre razones.
Uso:
  GTA_FMT=h GTA_MODE=full  python3 gta6.py preview T salida.png
  GTA_FMT=h GTA_MODE=full  python3 gta6.py chunk A B salida.mp4
GTA_MODE: full | reelA | reelB  (los reels se renderizan con GTA_FMT=v)."""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
import gta_eng as E
from gta_eng import (Cam, cam_path, box, rbox, cyl, sphere, extrude, torus, merge, decal, tex, grad_tex, Frame,
                     line3, ring3, dot3, headline, pill, label, counter, draw_text, font, ease, eout, eback, lerp, mix,
                     clamp, win, fmt_int, W, H, VERT, SS, INK)

MODE = os.environ.get('GTA_MODE', 'full')
TL = json.load(open(f'/home/claude/tl_gta_{MODE}.json'))
DUR = TL['dur']
FPS = 24
NF = int(round(DUR * FPS))
P = {(p['c'], p['i']): p for p in TL['phrases']}
CHAPS = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6']


def PA(c, i):
    p = P.get((c, i))
    return p['a'] if p else None


def PB(c, i):
    p = P.get((c, i))
    return p['b'] if p else None


def WS(c, i, k):
    """Inicio de la palabra k (índice de pantalla) de la frase; k puede ser texto (primera coincidencia)."""
    p = P.get((c, i))
    if not p:
        return None
    if isinstance(k, str):
        for w, a, b in p['words']:
            if w.strip('.,:;…?!¿¡').lower().startswith(k.lower()):
                return a
        return p['a']
    k = max(0, min(k, len(p['words']) - 1))
    return p['words'][k][1]


def T(*opts, default=0.0):
    """Primer tiempo disponible de varias opciones (frases que pueden faltar en los reels)."""
    for o in opts:
        v = WS(*o) if len(o) == 3 else PA(*o)
        if v is not None:
            return v
    return default


# ------------------------------------------------------------------ colores
TEAL = (34, 138, 126)
TEAL2 = (20, 86, 92)
PINK = (240, 88, 138)
ORANGE = (255, 166, 77)
RED = (186, 44, 36)
GOLD = (230, 178, 58)
BLUE = (66, 124, 214)
GREEN = (70, 160, 90)
BROWN = (128, 84, 48)
BLACK = (34, 34, 38)
WHITE = (236, 236, 238)
SLATE = (96, 112, 136)
PAPER = (246, 244, 238)


# ------------------------------------------------------------------ texturas
_TX = {}


def cover_tex(kind):
    if kind in _TX:
        return _TX[kind]
    w, h = 270, 340
    if kind == 'V':
        img = grad_tex(w, h, (24, 120, 112), (12, 52, 66))
        txt, sub = 'V', 'GRAND THEFT AUTO'
    elif kind == 'VI':
        img = grad_tex(w, h, (255, 120, 150), (255, 176, 84))
        txt, sub = 'VI', 'GRAND THEFT AUTO'
    else:
        img = grad_tex(w, h, (160, 34, 30), (70, 18, 16))
        txt, sub = '2', 'RED DEAD REDEMPTION'
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 34), fill=(245, 245, 245, 255))
    d.text((w / 2, 17), 'JUEGO', font=font('sb', 16), fill=(60, 60, 60), anchor='mm')
    d.text((w / 2, 70), sub, font=font('b', 17 if kind != 'RDR' else 14), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 196), txt, font=font('xb', 150 if len(txt) < 2 else 128), fill=(255, 255, 255), anchor='mm')
    if kind == 'VI':
        for i in range(5):  # palmeras/olas simples
            y = 290 + i * 8
            d.line([(20, y), (w - 20, y)], fill=(255, 230, 200, 120), width=2)
    _TX[kind] = img
    return img


def screen_tex(kind, w=320, h=180):
    key = ('scr', kind, w, h)
    if key in _TX:
        return _TX[key]
    if kind == 'term':
        img = Image.new('RGBA', (w, h), (10, 14, 12, 255))
        d = ImageDraw.Draw(img)
        f = font('monor', 13)
        lines = ['> conectando...', '> acceso: slack', '> descargando clips', '> 90 archivos', '> subiendo...', '█']
        for i, ln in enumerate(lines):
            d.text((12, 12 + i * 22), ln, font=f, fill=(80, 255, 140))
    elif kind == 'play':
        img = grad_tex(w, h, (40, 44, 60), (16, 18, 26))
        d = ImageDraw.Draw(img)
        cx, cy = w / 2, h / 2
        d.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), fill=(255, 255, 255, 235))
        d.polygon([(cx - 10, cy - 16), (cx - 10, cy + 16), (cx + 18, cy)], fill=(30, 30, 40))
        d.rectangle((16, h - 20, w - 16, h - 16), fill=(90, 90, 100))
        d.rectangle((16, h - 20, w * 0.62, h - 16), fill=(255, 90, 130))
    elif kind == 'vc':  # cuadro de video filtrado (gráficos a medio hacer)
        img = grad_tex(w, h, (255, 140, 170), (60, 170, 190))
        d = ImageDraw.Draw(img)
        rng = np.random.RandomState(w + h)
        for i in range(14):
            x, y, s = rng.randint(0, w), rng.randint(h // 3, h), rng.randint(10, 40)
            d.rectangle((x, y, x + s, y + s * 2), fill=(40, 40, 60, 180))
        d.text((10, 8), 'WIP', font=font('mono', 22), fill=(255, 255, 255))
        d.polygon([(w / 2 - 12, h / 2 - 18), (w / 2 - 12, h / 2 + 18), (w / 2 + 18, h / 2)], fill=(255, 255, 255))
    elif kind == 'phone':
        img = grad_tex(w, h, (30, 34, 46), (14, 16, 22))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((w * .12, h * .12, w * .88, h * .45), 10, fill=(255, 120, 150))
        d.polygon([(w * .45, h * .22), (w * .45, h * .35), (w * .58, h * .285)], fill=(255, 255, 255))
        for i in range(4):
            d.rounded_rectangle((w * .12, h * (.52 + i * .1), w * (.88 - .15 * (i % 2)), h * (.57 + i * .1)), 4, fill=(70, 74, 90))
    elif kind == 'house':
        img = grad_tex(w, h, (40, 60, 110), (20, 30, 60))
        d = ImageDraw.Draw(img)
        for i in range(5):
            d.rectangle((12, 14 + i * 26, w - 12 - (i % 3) * 30, 26 + i * 26), fill=(120, 200, 255))
    else:
        img = Image.new('RGBA', (w, h), (20, 20, 24, 255))
    _TX[key] = img
    return img


def windows_tex(w=360, h=200, lit=0.0):
    key = ('win', w, h, round(lit, 2))
    if key in _TX:
        return _TX[key]
    img = Image.new('RGBA', (w, h), (225, 222, 214, 255))
    d = ImageDraw.Draw(img)
    for r in range(4):
        for c in range(7):
            x0, y0 = 14 + c * 49, 16 + r * 46
            d.rectangle((x0, y0, x0 + 36, y0 + 30), fill=(120, 170, 210) if (r + c) % 3 else (150, 196, 230))
    _TX[key] = img
    return img


def cal_tex(top, big, sub, col=(220, 60, 60), cross=0.0):
    key = ('cal', top, big, sub, col, round(cross, 2))
    if key in _TX:
        return _TX[key]
    w, h = 300, 340
    img = Image.new('RGBA', (w, h), PAPER + (255,))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 78), fill=col)
    d.text((w / 2, 40), top, font=font('xb', 34), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 190), big, font=font('xb', 120 if len(big) <= 2 else 74), fill=(30, 30, 34), anchor='mm')
    d.text((w / 2, 296), sub, font=font('sb', 30), fill=(90, 90, 96), anchor='mm')
    if cross > 0:
        k = clamp(cross)
        d.line([(30, 100), (30 + (w - 60) * k, 100 + (h - 140) * k)], fill=(220, 40, 40), width=14)
        if k > 0.5:
            k2 = (k - 0.5) * 2
            d.line([(w - 30, 100), (w - 30 - (w - 60) * k2, 100 + (h - 140) * k2)], fill=(220, 40, 40), width=14)
    _TX[key] = img
    return img


def text_tex(txt, w=300, h=120, bg=(255, 255, 255), fg=(30, 30, 34), size=60, fk='xb'):
    key = ('txt', txt, w, h, bg, fg, size)
    if key in _TX:
        return _TX[key]
    img = Image.new('RGBA', (w, h), tuple(bg) + (255,))
    d = ImageDraw.Draw(img)
    d.text((w / 2, h / 2), txt, font=font(fk, size), fill=fg, anchor='mm')
    _TX[key] = img
    return img


# ------------------------------------------------------------------ objetos
def game_case(kind, s=1.0):
    m = box(1.3 * s, 1.66 * s, 0.13 * s, (230, 230, 232), shadow=0.45)
    m.C[m.FACE['front']] = (240, 240, 240)
    decal(m, m.FACE['front'], cover_tex(kind))
    m.flat = False
    return m


def case_at(kind, x=0.0, y=0.0, z=0.0, ry=0.0, s=1.0, rx=0.0, rz=0.0):
    return game_case(kind, s).tf(ry=ry, rx=rx, rz=rz, t=(x, y, z))


def person(h=1.0, col=SLATE, x=0.0, z=0.0, ry=0.0, walk=0.0):
    body = cyl(0.17 * h, 0.62 * h, col, n=18, r2=0.13 * h, y0=0.34 * h, shadow=0.4)
    head = sphere(0.15 * h, (232, 196, 170), nu=16, nv=10, gloss=0.2).tf(t=(0, 1.1 * h, 0))
    lw = math.sin(walk) * 0.18 * h
    legs = [cyl(0.06 * h, 0.36 * h, (60, 66, 80), n=10, y0=0.0).tf(t=(-0.07 * h, 0, lw)),
            cyl(0.06 * h, 0.36 * h, (60, 66, 80), n=10, y0=0.0).tf(t=(0.07 * h, 0, -lw))]
    ms = [body] + legs + [head]
    return [m.tf(ry=ry, t=(x, 0, z)) for m in ms]


def console(kind, x=0.0, z=0.0, ry=0.0):
    if kind == 'ps3':
        a = rbox(1.15, 0.24, 1.0, 0.08, (28, 28, 32), gloss=0.7)
        b = box(1.0, 0.02, 0.02, (120, 120, 126), edge=False, shadow=0).tf(t=(0, 0.11, 0.51))
        ms = [a, b]
    elif kind == 'ps4':
        a = box(1.25, 0.11, 1.0, (30, 30, 34), shadow=0.4, gloss=0.4)
        b = box(1.2, 0.11, 0.94, (44, 44, 50), shadow=0, gloss=0.6).tf(t=(0.03, 0.12, 0.02))
        c = box(0.9, 0.012, 0.02, (90, 140, 255), edge=False, shadow=0).tf(t=(0, 0.115, 0.51))
        ms = [a, b, c]
    elif kind == 'pc':
        a = box(0.5, 1.25, 1.0, (40, 40, 46), shadow=0.45, gloss=0.3)
        b = box(0.02, 1.0, 0.04, (90, 200, 255), edge=False, shadow=0).tf(t=(0.0, 0.12, 0.5))
        ms = [a, b]
    else:  # ps5
        core = box(0.36, 1.45, 0.95, (24, 24, 28), shadow=0.45)
        w1 = box(0.12, 1.55, 1.02, (240, 240, 242), shadow=0, gloss=0.5).tf(t=(-0.24, 0, 0))
        w2 = box(0.12, 1.55, 1.02, (240, 240, 242), shadow=0, gloss=0.5).tf(t=(0.24, 0, 0))
        st = cyl(0.3, 0.05, (30, 30, 34), shadow=0).tf(t=(0, 0, 0))
        ms = [st, core.tf(t=(0, 0.05, 0)), w1.tf(t=(0, 0.02, 0)), w2.tf(t=(0, 0.02, 0))]
    return [m.tf(ry=ry, t=(x, 0, z)) for m in ms]


def building(w=3.0, h=1.6, d=1.6, col=(214, 208, 196)):
    m = box(w, h, d, col, shadow=0.4)
    decal(m, m.FACE['front'], windows_tex())
    decal(m, m.FACE['right'], windows_tex(220, 200))
    decal(m, m.FACE['left'], windows_tex(220, 200))
    roof = box(w + 0.1, 0.08, d + 0.1, (180, 176, 168), shadow=0).tf(t=(0, h, 0))
    return [m, roof]


def tv(x=0.0, z=0.0, ry=0.0, w=1.9, h=1.07, kind='term', y=0.55):
    scr = box(w, h, 0.07, (22, 22, 26), shadow=0.3, base=False)
    scr.C[scr.FACE['front']] = (10, 10, 12)
    decal(scr, scr.FACE['front'], screen_tex(kind))
    scr = scr.tf(t=(0, y + h / 2, 0))
    stand = box(0.5, y, 0.25, (60, 60, 66), shadow=0.35)
    return [stand.tf(ry=ry, t=(x, 0, z)), scr.tf(ry=ry, t=(x, 0, z))]


def phone(x=0.0, y=0.0, z=0.0, ry=0.0, rx=0.0, s=1.0, kind='phone'):
    m = rbox(0.5 * s, 0.05 * s, 1.0 * s, 0.07 * s, (26, 26, 30), gloss=0.6, shadow=0.35)
    # pantalla: un cuadro delgado encima
    sc = box(0.44 * s, 0.005, 0.92 * s, (14, 14, 16), edge=False, shadow=0).tf(t=(0, 0.05 * s, 0))
    decal(sc, sc.FACE['top'], screen_tex(kind, 160, 320))
    return [mm.tf(rx=rx, ry=ry, t=(x, y, z)) for mm in (m, sc)]


def coins(n, x=0.0, z=0.0, r=0.32):
    ms = []
    for i in range(n):
        ms.append(cyl(r, 0.07, GOLD, n=20, top=(246, 206, 90), gloss=0.5, shadow=0.35 if i == 0 else 0).tf(
            t=(x + 0.015 * math.sin(i * 1.7), i * 0.075, z + 0.015 * math.cos(i * 2.3))))
    return ms


def hat(x=0.0, y=0.0, z=0.0, s=1.0, ry=0.0):
    brim = cyl(0.62 * s, 0.05 * s, BROWN, n=26, top=(146, 98, 58), shadow=0.3)
    crown = cyl(0.32 * s, 0.42 * s, (112, 72, 40), n=22, r2=0.27 * s, y0=0.05 * s, top=(120, 78, 44), shadow=0)
    band = cyl(0.325 * s, 0.07 * s, (50, 30, 20), n=22, y0=0.08 * s, shadow=0)
    return [m.tf(ry=ry, t=(x, y, z)) for m in (brim, crown, band)]


def gear(r, teeth, th, col, x=0.0, y=0.0, z=0.0, rot=0.0, upright=True):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4) + math.radians(rot)
        rr = r if (i % 4) in (1, 2) else r * 0.82
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    m = extrude(pts, th, col, top=tuple(min(255, int(c * 1.08)) for c in col), shadow=0.35, gloss=0.3)
    hole = cyl(r * 0.22, th + 0.02, (220, 220, 224), n=16, shadow=0, y0=-0.01)
    ms = [m, hole]
    if upright:
        return [mm.tf(rx=90, t=(x, y, z)) for mm in ms]
    return [mm.tf(t=(x, y, z)) for mm in ms]


def heart_pts(s=1.0, n=40):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        X = 16 * math.sin(t) ** 3
        Y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((X * s / 17, Y * s / 17))
    return pts


def hourglass(x=0.0, z=0.0, s=1.0, k=0.0):
    top = cyl(0.42 * s, 0.07 * s, BROWN, n=22, shadow=0.35)
    bot = cyl(0.42 * s, 0.07 * s, BROWN, n=22, shadow=0).tf(t=(0, 1.33 * s, 0))
    g1 = cyl(0.32 * s, 0.6 * s, (200, 225, 240), n=22, r2=0.04 * s, y0=0.07 * s, shadow=0, gloss=0.8)
    g2 = cyl(0.04 * s, 0.6 * s, (200, 225, 240), n=22, r2=0.32 * s, y0=0.67 * s, shadow=0, gloss=0.8)
    sand_b = cyl(0.28 * s * (0.3 + 0.7 * k), 0.4 * s * k + 0.01, (232, 196, 120), n=18, r2=0.04 * s, y0=0.07 * s, shadow=0)
    ms = [top, g1, sand_b, g2, bot]
    posts = [box(0.04 * s, 1.33 * s, 0.04 * s, BROWN, shadow=0).tf(t=(0.38 * s * math.cos(a), 0.0, 0.38 * s * math.sin(a)))
             for a in (0.6, 2.7, 4.8)]
    return [m.tf(t=(x, 0, z)) for m in ms + posts]


def bills(n, x=0.0, z=0.0):
    ms = []
    for i in range(n):
        ms.append(box(0.95, 0.06, 0.45, (120, 170, 110), cols={'top': (150, 196, 132)}, shadow=0.35 if i == 0 else 0).tf(
            ry=(i * 7) % 5 - 2, t=(x, i * 0.062, z)))
    return ms


def calendar(top, big, sub, x=0.0, z=0.0, ry=0.0, col=(220, 60, 60), cross=0.0, s=1.0, y=0.0):
    m = box(1.2 * s, 1.36 * s, 0.08 * s, PAPER, shadow=0.4)
    decal(m, m.FACE['front'], cal_tex(top, big, sub, col, cross))
    return m.tf(ry=ry, t=(x, y, z))


# ------------------------------------------------------------------ ayudas de escena
def orbit(lt, base_yaw, rate=4.0, **kw):
    kw = dict(kw)
    kw['yaw'] = base_yaw + lt * rate
    return Cam(**kw)


def vfit(d, wide=False):
    """En vertical la cámara se aleja para que quepa el ancho (más en escenas anchas)."""
    if not VERT:
        return d * 0.96
    return d * (1.3 if wide else 1.0)


def appear(t, t0, d=0.45):
    return eback((t - t0) / d) if t0 is not None else 0.0


def ui_label3(fr, p, txt, sub=None, a=1.0, side=1, length=90, up=40):
    def f(img, d, p=p):
        x, y, z = fr.cam.p1(p)
        if z > 0.2:
            label(img, d, x, y, txt, sub, a, side, length, up)
    fr.ui.append(f)


def ui_text3(fr, p, txt, size=30, a=1.0, col=INK, fk='b', dy=0):
    def f(img, d, p=p):
        x, y, z = fr.cam.p1(p)
        if z > 0.2:
            draw_text(d, (x, y + dy), txt, font(fk, size * (1.3 if VERT else 1.0)), col, 'mm', a=a)
    fr.ui.append(f)


def ui_pill(fr, txt, a=1.0, where='br', dotc=None):
    def f(img, d):
        if where == 'br':
            x, y = (W - 40, H - 150) if not VERT else (W - 40, H * 0.66)
            pill(img, d, x, y, txt, a, anchor='r', dotc=dotc)
        else:
            x, y = (40, H - 150) if not VERT else (40, H * 0.66)
            pill(img, d, x, y, txt, a, anchor='l', dotc=dotc)
    fr.ui.append(f)


def head(fr, lines, accent, t, t0, kicker=None):
    k = clamp((t - t0) / 0.55) if t0 is not None else 0
    fr.ui.append(lambda img, d: headline(img, d, lines, accent, ease(k), kicker))


def big_counter(fr, txt, a=1.0, sub=None, pos=None, size=None, col=INK):
    def f(img, d):
        x, y = pos or ((W * 0.5, H * 0.30) if not VERT else (W * 0.5, H * 0.30))
        counter(img, d, x, y, txt, size, a, col, sub)
    fr.ui.append(f)


# ------------------------------------------------------------------ tarjetas en blanco y negro
CARD = {
    'c1': ('RAZÓN 1', 'GTA 5 NUNCA SE FUE', 'bounce'),
    'c2': ('RAZÓN 2', 'OTRO GIGANTE EN LA MESA', 'line'),
    'c3': ('RAZÓN 3', 'UN ESTUDIO NUEVO', 'rings'),
    'c4': ('RAZÓN 4', 'EL HACKEO', 'error'),
    'c5': ('RAZÓN 5', 'LO QUE TÚ ESPERAS', 'ruler'),
}


def card(fr, t, lt, dur, c):
    title, sub, style = CARD[c]
    fr.mono = True
    fr.floor = 1.0
    fr.floor_g = 0.28
    ball = lambda y, s=1.0: sphere(0.32 * s, (18, 18, 20), nu=28, nv=18, gloss=0.9, shadow=0.55).tf(t=(0, y, 0))
    if style == 'bounce':
        fr.cam = Cam(target=(0, 0.4, 0), dist=vfit(6.5) - lt * 0.35, yaw=-10 + lt * 6, pitch=16 + lt * 2)
        tb = lt * 1.6
        y = abs(math.cos(min(tb, 3.6) * 1.5)) * 2.4 * math.exp(-min(tb, 3.6) * 0.75) + 0.32
        fr.meshes.append(ball(y))
        hits = [k * math.pi / 1.5 / 1.6 + math.pi / 3 / 1.6 for k in range(3)]
        def under(d, cam, lt=lt):
            for h in hits:
                if lt > h:
                    for j in range(3):
                        r = (lt - h) * 1.6 + j * 0.25
                        a = clamp(1 - (lt - h) / 1.8) * (1 - j * 0.25)
                        if a > 0:
                            ring3(d, cam, (0, 0.0, 0), r, (20, 20, 22), 1.6, a)
            ring3(d, cam, (0, 0, 0), 2.8, (20, 20, 22), 1.2, 0.5)
        fr.under.append(under)
    elif style == 'line':
        fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(7.0), yaw=30 - lt * 5, pitch=28)
        k = ease(lt / 1.3)
        a, b = np.array([-2.4, 0.0, 1.2]), np.array([2.2, 0.0, -1.4])
        p = a + (b - a) * k
        fr.meshes.append(ball(0.32, 0.7).tf(t=(p[0], 0, p[2])))
        def under(d, cam, k=k, p=p):
            line3(d, cam, [a, p], (20, 20, 22), 2.2)
            for j in range(12):
                q = a + (b - a) * j / 11
                line3(d, cam, [q + (0, 0, -0.06), q + (0, 0, 0.06)], (20, 20, 22), 1.4, a=0.7)
            ring3(d, cam, tuple(b), 0.25, (20, 20, 22), 2.0)
            ring3(d, cam, tuple(b), 0.4, (20, 20, 22), 1.4, 0.6)
        fr.under.append(under)
    elif style == 'rings':
        fr.cam = Cam(target=(0, 0.0, 0), dist=vfit(6.0), yaw=lt * 8, pitch=58 - lt * 6)
        fr.meshes.append(ball(0.25, 0.6))
        def under(d, cam, lt=lt):
            for j in range(4):
                r = 0.6 + j * 0.55 + 0.15 * math.sin(lt * 2 + j)
                ring3(d, cam, (0, 0, 0), r, (20, 20, 22), 2.2 - j * 0.3, clamp(lt * 2 - j * 0.3))
        fr.under.append(under)
    elif style == 'error':
        fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(7.0), yaw=-25 + lt * 4, pitch=24)
        k = ease(lt / 1.0)
        a, b = np.array([-2.2, 0.0, 1.0]), np.array([2.0, 0.0, -1.2])
        p = a + (b - a) * k
        fr.meshes.append(ball(0.0, 0.5).tf(t=tuple(a + (0, 0.16, 0))))
        def under(d, cam, p=p, lt=lt):
            line3(d, cam, [a, p], (20, 20, 22), 2.4)
            ring3(d, cam, tuple(b), 0.22, (20, 20, 22), 2.0)
            ring3(d, cam, tuple(b), 0.36, (20, 20, 22), 1.6)
        fr.under.append(under)
        if lt > 1.0:
            mid = (a + b) / 2 + np.array([0, 0.35, 0])
            ui_text3(fr, tuple(mid), 'error', 30, a=0.5 + 0.5 * (int(lt * 5) % 2), fk='mono')
    else:  # ruler
        fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.5), yaw=0, pitch=6)
        fr.meshes.append(ball(0.0, 0.7).tf(t=(0, 0.2, 0)))
        def under(d, cam):
            line3(d, cam, [(0, 0.2, 0), (0, 1.85, 0)], (20, 20, 22), 2.4)
            for j in range(9):
                y = 0.25 + j * 0.2
                ww = 0.12 if j % 4 == 0 else 0.06
                line3(d, cam, [(-ww, y, 0), (ww, y, 0)], (20, 20, 22), 1.6)
        fr.under.append(under)
        v = 90.4 * eout(lt / 2.2)
        ui_text3(fr, (0, 2.15, 0), f'{v:.1f}'.replace('.', ','), 44, fk='b')
        ui_text3(fr, (0.95, 2.15, 0), 'millones', 26, a=0.4, fk='m')
    # texto de la tarjeta
    def f(img, d, lt=lt):
        k = ease(lt / 0.5)
        ys = H * (0.15 if not VERT else 0.22)
        draw_text(d, (W / 2, ys), title, font('mono', 76 if not VERT else 96), INK, 'mm', a=k, spacing=6)
        n = int(len(sub) * clamp((lt - 0.3) / 0.9))
        draw_text(d, (W / 2, ys + (64 if not VERT else 86)), sub[:n], font('monor', 28 if not VERT else 38), (90, 90, 94), 'mm', a=k, spacing=3)
    fr.ui.append(f)


# ------------------------------------------------------------------ escenas: GANCHO
def s_birth(fr, t, lt, dur, loop=False):
    t1 = T(('c0', 1), default=t - lt + 4.0) if not loop else t - lt + 99
    fr.cam = Cam(target=(0, 0.75, 0), dist=vfit(6.4, wide=True) - lt * 0.12, yaw=-14 + lt * 3, pitch=12)
    fr.meshes.append(case_at('V', -1.1, 0.0, 0.0, ry=18))
    t0 = t - lt
    k = clamp((t - (t0 + 0.6)) / max(0.6, (t1 + 1.6) - (t0 + 0.6)))
    if loop:
        k = 0.0
    h = lerp(0.42, 1.55, ease(k))
    fr.meshes += person(h, (94, 120, 170), x=1.1, z=0.15, ry=-20)
    year = int(round(lerp(2013, 2026, ease(k))))
    def f(img, d, year=year):
        x, y, z = fr.cam.p1((1.1, h * 1.32 + 0.35, 0.15))
        draw_text(d, (x, y), str(year), font('mono', 40 if not VERT else 54), INK, 'mm')
        x2, y2, _ = fr.cam.p1((1.1, 0.0, 0.15))
        pill(img, d, x2, y2 + 40, 'edad: ' + str(year - 2013) + (' año' if year - 2013 == 1 else ' años'), 1.0)
    fr.ui.append(f)
    ui_label3(fr, (-1.1, 1.75, 0), 'GTA V', '17 sep 2013', a=clamp(lt / 0.6), side=-1)
    if not loop and PA('c0', 1) is not None:
        head(fr, ['13 años', 'de espera.'], PINK, t, PA('c0', 1), kicker='GTA 6')
    if loop:
        head(fr, ['Y si naciste', 'ese día…'], PINK, t, t0 + 0.2, kicker='GTA 6')


def s_bars(fr, t, lt, dur):
    data = [('III → VC', 1.0, (150, 150, 156), ('c0', 2, 'pasó')), ('SA → IV', 3.5, (120, 128, 140), ('c0', 3, 'casi')),
            ('IV → V', 5.4, TEAL, ('c0', 3, 'cuatro.')), ('V → VI', 13.2, PINK, ('c0', 4, 'trece'))]
    tlast = T(('c0', 4, 'trece'), default=t - lt + 5)
    up = ease((t - tlast) / 1.6)
    fr.cam = Cam(target=(0.2, 0.8 + up * 0.9, 0), dist=vfit(7.4, wide=True) + up * 1.6, yaw=-18 + lt * 2.5, pitch=14 + up * 4)
    for i, (lab, yrs, col, key) in enumerate(data):
        x = -2.4 + i * 1.6
        ts = T(key, default=t - lt + i)
        k = eout((t - ts) / 0.9)
        hgt = max(0.02, 0.2 * yrs * k)
        fr.meshes.append(box(0.8, hgt, 0.8, col, shadow=0.4).tf(t=(x, 0, 0)))
        if k > 0.05:
            ui_text3(fr, (x, hgt + 0.32, 0), (f'{yrs * k:.1f}'.replace('.0', '') + (' años' if i == 3 else '')), 30, a=clamp(k * 2))
            ui_text3(fr, (x, -0.0, 0.75), lab, 20, a=clamp(k * 2), col=(110, 110, 116), fk='sb')
    if PA('c0', 5) is not None and t >= PA('c0', 5):
        head(fr, ['La espera', 'más larga.'], PINK, t, PA('c0', 5), kicker='Años entre un GTA y otro')
    else:
        head(fr, ['Años entre', 'cada GTA.'], PINK, t, t - lt + 0.2)


def scan_overlay(fr, t, ts, te, y0, y1, center=(0, 0, 0), r=2.2):
    """Anillo escáner (sello de la marca) que sube; devuelve la altura actual y fracción."""
    k = clamp((t - ts) / max(0.1, te - ts))
    ys = lerp(y0, y1, ease(k))
    a = win(t, ts, te + 0.6, 0.2, 0.4)
    def over(d, cam, ys=ys, a=a):
        for j, (rr, w) in enumerate(((r, 3.2), (r * 1.06, 1.6), (r * 0.94, 1.2))):
            ring3(d, cam, (center[0], ys, center[2]), rr, (40, 160, 255), w, a * (1 - j * 0.3))
    fr.over.append(over)
    return ys, k


def s_xray(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.6), yaw=-28 + lt * 4, pitch=20)
    ts, te = t0 + 0.4, t0 + 2.6
    ys, k = scan_overlay(fr, t, ts, te, 0.0, 1.9, r=2.1)
    reveal = clamp((t - ts) / (te - ts))
    shell_a = 1 - 0.85 * ease(reveal)
    bl = building()
    for m in bl:
        m.alpha = shell_a
    cols = [TEAL, RED, ORANGE, (90, 90, 100), PINK]
    for i, c in enumerate(cols):
        kk = eback((t - (ts + 0.3 + i * 0.25)) / 0.5)
        if kk > 0:
            fr.meshes.append(box(0.42, 0.42 * kk + 0.01, 0.42, c, shadow=0.3).tf(t=(-1.1 + i * 0.55, 0.15, 0.1)))
            ui_text3(fr, (-1.1 + i * 0.55, 0.9, 0.1), str(i + 1), 30, a=clamp(kk), fk='mono')
    fr.meshes += bl if shell_a > 0.02 else []
    def wire(d, cam, a=1 - shell_a):
        if a <= 0.02:
            return
        w, h, dd = 1.5, 1.6, 0.8
        C = [(-w, 0, -dd), (w, 0, -dd), (w, 0, dd), (-w, 0, dd)]
        for yy in (0, h):
            line3(d, cam, [(x, yy, z) for x, _, z in C + C[:1]], (60, 140, 220), 1.6, a)
        for x, _, z in C:
            line3(d, cam, [(x, 0, z), (x, h, z)], (60, 140, 220), 1.6, a)
    fr.over.append(wire)
    ui_pill(fr, 'Así se ve por dentro · Recreación', clamp(lt / 0.5), dotc=(40, 160, 255))
    head(fr, ['¿Qué pasó', 'dentro?'], BLUE, t, t0 + 0.1, kicker='Rockstar Games')


# ------------------------------------------------------------------ RAZÓN 1
def s_sales(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(6.8, wide=True), yaw=-12 + lt * 3, pitch=8)
    fr.meshes.append(case_at('V', 0, 0.0, 0.6, ry=12 + 6 * math.sin(lt * 0.8)))
    years = list(range(2013, 2027))
    sold = [32.5, 45, 65, 75, 90, 100, 115, 130, 150, 170, 185, 200, 215, 230]  # millones aprox. (vendidos a tiendas)
    k = eout(lt / 2.6)
    def under(d, cam, k=k):
        pts = []
        n = 1 + (len(years) - 1) * k
        for i in range(len(years)):
            if i > n:
                break
            x = -2.6 + 5.2 * i / (len(years) - 1)
            pts.append((x, 0.25 + sold[i] / 230 * 2.0, -1.6))
        if len(pts) >= 2:
            line3(d, cam, pts, (20, 20, 22), 2.4)
        for p in pts:
            dot3(d, cam, p, 4, (20, 20, 22))
        line3(d, cam, [(-2.7, 0.2, -1.6), (2.7, 0.2, -1.6)], (150, 150, 152), 1.2)
    fr.under.append(under)
    if k > 0.95:
        ui_text3(fr, (2.6, 2.6, -1.6), '230 M', 34, fk='mono')
    ui_text3(fr, (-2.6, 0.0, -1.6), '2013', 18, col=(120, 120, 124), fk='mono')
    ui_text3(fr, (2.6, 0.0, -1.6), '2026', 18, col=(120, 120, 124), fk='mono')
    head(fr, ['Nunca dejó', 'de vender.'], TEAL, t, t0 + 0.1, kicker='Razón 1')
    ui_pill(fr, 'Copias vendidas · Take-Two', clamp(lt / 0.5))


def s_consoles(fr, t, lt, dur):
    t0 = t - lt
    xs = [-3.0, -1.0, 1.0, 3.0]
    kinds = ['ps3', 'ps4', 'pc', 'ps5']
    labs = [('PS3', 'sep 2013'), ('PS4', 'nov 2014'), ('PC', 'abr 2015'), ('PS5', 'mar 2022')]
    keys = [T(('c1', 2), default=t0), T(('c1', 3, 'PS4'), default=t0 + 2), T(('c1', 3, 'PC'), default=t0 + 3),
            T(('c1', 3, 'PS5'), default=t0 + 4)]
    cur = 0
    for i, kt in enumerate(keys):
        if t >= kt:
            cur = i
    # salto del estuche entre consolas
    kt = keys[cur]
    j = clamp((t - kt) / 0.55)
    xa = xs[cur - 1] if cur > 0 else xs[0]
    xb = xs[cur]
    xx = lerp(xa, xb, ease(j))
    top = [0.24, 0.23, 1.25, 1.6][cur]
    topa = [0.24, 0.23, 1.25, 1.6][max(0, cur - 1)]
    yy = lerp(topa, top, j) + math.sin(j * math.pi) * 1.0 + 0.85
    fr.cam = Cam(target=(xx * 0.5, 0.8, 0), dist=vfit(8.2, wide=True), yaw=-8 + lt * 1.5, pitch=14)
    for x, kd in zip(xs, kinds):
        fr.meshes += console(kd, x, 0, ry=-10)
    fr.meshes.append(case_at('V', xx, yy - 0.83, 0.1, ry=10 + j * 360 * (1 if cur else 0), s=0.55))
    for i, (x, (a, b)) in enumerate(zip(xs, labs)):
        if t >= keys[i] - 0.2:
            ui_text3(fr, (x, -0.05, 0.9), a, 26, fk='b')
            ui_text3(fr, (x, -0.05, 0.9), b, 18, col=(110, 110, 116), fk='m', dy=30)
    p4 = PA('c1', 4)
    if p4 is not None and t >= p4:
        head(fr, ['3 generaciones,', 'el mismo juego.'], TEAL, t, p4, kicker='Razón 1')
    else:
        head(fr, ['Salió en', '2013.'], TEAL, t, t0 + 0.1, kicker='Razón 1')


def s_tower(fr, t, lt, dur):
    t0 = t - lt
    t6 = T(('c1', 6), default=t0 + 3)
    grow = ease((t - t6) / 3.0)
    n = 6 + int(grow * 40)
    fr.cam = Cam(target=(0, 0.9 + grow * 3.2, 0), dist=vfit(6.4) + grow * 5.5, yaw=-20 + lt * 5, pitch=10 + grow * 6)
    for i in range(n):
        fr.meshes.append(case_at('V', 0.02 * math.sin(i * 1.3), i * 0.135, 0.02 * math.cos(i * 0.7), ry=(i * 13) % 9 - 4,
                                 rx=-90, s=0.75) if i < 60 else None)
    fr.meshes = [m for m in fr.meshes if m is not None]
    v = 230e6 * eout((t - t0 - 0.2) / 2.0)
    big_counter(fr, fmt_int(v), sub='COPIAS VENDIDAS', pos=(W * 0.5, H * (0.30 if not VERT else 0.26)),
                size=64 if not VERT else 84, a=clamp(lt / 0.3) * (1 - grow))
    if grow > 0.05:
        ui_pill(fr, 'Si cada copia fuera una caja de 1.2 cm', clamp(grow * 2))
        head(fr, ['Una torre', 'de cajas.'], TEAL, t, t6, kicker='Razón 1')


def s_space(fr, t, lt, dur):
    """Del bolsillo al espacio: torre de 2,700 km junto a la Tierra y la Estación Espacial (escala real)."""
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0, 0), dist=10)
    zoom = ease(lt / 2.2)

    def over(d, cam, zoom=zoom):
        # escala: km por píxel (SS); al empezar se ve cerca del suelo, luego todo
        Hs = E.SH * (0.62 if not VERT else 0.55)
        km_top = lerp(30, 3300, zoom)
        kpx = km_top / Hs
        base_y = E.SH * (0.86 if not VERT else 0.74)
        cx = E.SW * 0.5
        R = 6371 / kpx
        # Tierra (arco)
        d.ellipse((cx - R, base_y, cx + R, base_y + 2 * R), fill=(222, 236, 246), outline=(30, 30, 34), width=3)
        # atmósfera: 100 km
        ra = (6371 + 100) / kpx
        d.ellipse((cx - ra, base_y + R - ra, cx + ra, base_y + R + ra), outline=(150, 190, 220), width=2)
        # torre de cajas
        th = 2700 / kpx
        tw = max(10, 26 * SS)
        d.rectangle((cx - tw / 2, base_y - th, cx + tw / 2, base_y), fill=TEAL, outline=TEAL2)
        # EEI a 408 km
        yi = base_y - 408 / kpx
        d.line([(cx - E.SW * 0.3, yi), (cx + E.SW * 0.3, yi)], fill=(120, 120, 124), width=2)
        ix = cx + E.SW * 0.14
        d.rectangle((ix - 22 * SS, yi - 4 * SS, ix + 22 * SS, yi + 4 * SS), fill=(70, 70, 80))
        d.rectangle((ix - 4 * SS, yi - 12 * SS, ix + 4 * SS, yi + 12 * SS), fill=(200, 160, 60))
        # Everest 8.8 km y Torre Latinoamericana
        ye = base_y - 8.8 / kpx
        d.polygon([(cx - E.SW * 0.22, base_y), (cx - E.SW * 0.2, ye), (cx - E.SW * 0.18, base_y)], fill=(130, 130, 136))
        over.marks = (yi, base_y - th, ye, base_y, cx, ix)
    fr.over.append(over)

    def f(img, d, zoom=zoom):
        Hs = E.SH * (0.62 if not VERT else 0.55)
        km_top = lerp(30, 3300, zoom)
        kpx = km_top / Hs
        base_y = E.SH * (0.86 if not VERT else 0.74)
        cx = E.SW * 0.5
        yi = (base_y - 408 / kpx) / SS
        yt = (base_y - 2700 / kpx) / SS
        fz = 22 if not VERT else 28
        if yi > 60:
            if VERT:
                draw_text(d, (cx / SS - 24, yi - 24), 'Estación Espacial · 408 km', font('sb', fz), INK, 'rm')
            else:
                draw_text(d, (cx / SS + W * 0.15, yi - 22), 'Estación Espacial · 408 km', font('sb', fz), INK, 'lm')
        if yt > 40:
            draw_text(d, (cx / SS + 26, yt), 'Torre de cajas · 2,700 km', font('b', fz + 4), TEAL2, 'lm')
        if zoom < 0.4:
            ye = (base_y - 8.8 / kpx) / SS
            draw_text(d, (cx / SS - W * 0.2, ye - 20), 'Everest · 8.8 km', font('sb', fz), INK, 'mm', a=1 - zoom * 2.5)
        pill(img, d, W - 40, (H - 150) if not VERT else H * 0.66, 'Escala real', 1.0, anchor='r', dotc=TEAL)
    fr.ui.append(f)
    head(fr, ['7 veces más alto', 'que la Estación.'], TEAL, t, t0 + 0.1, kicker='Del bolsillo al espacio')


def s_coins(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(7.0, wide=True), yaw=-6 + lt * 3, pitch=14)
    fr.meshes.append(case_at('V', -1.7, 0, 0, ry=14))
    n = 4 + int(eout(lt / 3.0) * 16)
    fr.meshes += coins(n, -0.4, 0.1)
    if n < 20:
        yy = 1.6 - (lt * 3 % 1) * 1.4
        fr.meshes.append(cyl(0.32, 0.07, GOLD, n=20, top=(246, 206, 90), gloss=0.5, shadow=0).tf(rx=30, t=(-0.4, n * 0.075 + yy, 0.1)))
    vi = case_at('VI', 1.9, 0, -0.2, ry=-14)
    vi.alpha = 0.55
    fr.meshes.append(vi)
    fr.meshes += hourglass(0.95, 0.5, 0.55, k=clamp(lt / dur))
    ui_label3(fr, (1.9, 1.7, -0.2), 'GTA VI', 'en espera', a=clamp(lt / 0.6))
    head(fr, ['El 6 podía', 'esperar.'], PINK, t, t0 + 0.1, kicker='Razón 1')


# ------------------------------------------------------------------ RAZÓN 2
def s_rdr(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0.2, 1.1, 0), dist=vfit(7.2), yaw=-16 + lt * 3, pitch=12)
    k = eback(lt / 0.7)
    big = game_case('RDR', 1.55).tf(ry=14, t=(-0.6, 0, 0))
    big.V[:, 1] *= max(0.02, k)
    fr.meshes.append(big)
    if k > 0.9:
        fr.meshes += hat(-0.6, 2.58 + 0.08 * math.sin(lt * 2), 0.0, s=0.8, ry=lt * 20)
    fr.meshes.append(case_at('VI', 1.7, 0, 0.3, ry=-12, s=0.6))
    t2 = PA('c2', 2)
    if t2 is not None:
        ui_label3(fr, (-0.6, 1.4, 0.2), 'Red Dead Redemption 2', 'oct 2018', a=clamp((t - t2) / 0.5), side=-1, length=120)
    ui_label3(fr, (1.7, 1.0, 0.3), 'GTA VI', 'esperando', a=clamp((lt - 0.6) / 0.5), length=70)
    head(fr, ['Otro gigante', 'en la mesa.'], RED, t, t0 + 0.1, kicker='Razón 2')


STUDIOS = [('Edimburgo', 55.95, -3.19), ('Nueva York', 40.7, -74.0), ('San Diego', 32.7, -117.2), ('Toronto', 43.65, -79.4),
           ('Leeds', 53.8, -1.55), ('Lincoln', 53.23, -0.54), ('Londres', 51.5, -0.13), ('Bengaluru', 12.97, 77.6),
           ('Nueva Inglaterra', 42.66, -71.14), ('Dundee', 56.46, -2.97)]


def s_globe(fr, t, lt, dur):
    t0 = t - lt
    R = 1.5
    cy = 1.75
    rot = -40 + lt * 6
    fr.cam = Cam(target=(0, cy, 0), dist=vfit(7.0), yaw=0, pitch=6)

    def gp(lat, lon):
        la, lo = math.radians(lat), math.radians(lon + rot)
        return (R * math.cos(la) * math.sin(lo), cy + R * math.sin(la), R * math.cos(la) * math.cos(lo))

    def under(d, cam):
        for lat in range(-60, 90, 30):
            pts = [gp(lat, lo) for lo in range(-180, 181, 6)]
            front = [p for p in pts]
            line3(d, cam, front, (60, 60, 64), 1.2, 0.35)
        for lon in range(-180, 180, 30):
            pts = [gp(la, lon) for la in range(-90, 91, 6)]
            line3(d, cam, pts, (60, 60, 64), 1.2, 0.35)
        ring3(d, cam, (0, cy, 0), R, (30, 30, 34), 2.2, axis='z')
    fr.under.append(under)
    shown = 0
    for i, (name, la, lo) in enumerate(STUDIOS):
        p = gp(la, lo)
        if p[2] < 0.1:
            continue
        a = clamp((lt - 0.3 - i * 0.18) / 0.4)
        if a <= 0:
            continue
        fr.meshes.append(sphere(0.07, RED, nu=10, nv=6, shadow=0, gloss=0.5).tf(t=p))
        if shown < 5 and name in ('Edimburgo', 'Nueva York', 'San Diego', 'Toronto', 'Londres'):
            ui_text3(fr, (p[0] + 0.05, p[1] + 0.16, p[2]), name, 17, a=a, fk='sb')
            shown += 1
    fr.floor = 0.7
    big_counter(fr, '≈ 7 años', sub='DE DESARROLLO', pos=(W * (0.2 if not VERT else 0.5), H * (0.55 if not VERT else 0.64)),
                size=56 if not VERT else 72, a=clamp((lt - 0.6) / 0.5))
    head(fr, ['Estudios en', 'varios países.'], RED, t, t0 + 0.1, kicker='Red Dead Redemption 2')
    ui_pill(fr, 'Ubicaciones de estudios Rockstar', clamp(lt / 0.5), dotc=RED)


def s_hours(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.3, 0), dist=vfit(7.4, wide=True), yaw=-14 + lt * 3, pitch=10)
    t4 = PA('c2', 4)
    k1 = eout(lt / 1.2)
    k2 = eout((t - t4) / 1.0) if t4 is not None else 0
    s = 0.026
    fr.meshes.append(cyl(0.55, max(0.02, 100 * s * k1), RED, n=30, top=(220, 80, 70), gloss=0.3).tf(t=(-1.0, 0, 0)))
    fr.meshes.append(cyl(0.55, max(0.02, 48 * s * k2), GREEN, n=30, top=(110, 196, 120), gloss=0.3).tf(t=(1.0, 0, 0)))
    ui_text3(fr, (-1.0, 100 * s * k1 + 0.35, 0), f'{int(100 * k1)} h', 40, fk='mono')
    ui_text3(fr, (-1.0, -0.1, 0.9), 'Equipo de guion, RDR2', 19, col=(110, 110, 116), fk='sb')
    if k2 > 0:
        ui_text3(fr, (1.0, 48 * s * k2 + 0.35, 0), f'{int(48 * k2)} h', 40, fk='mono')
        ui_text3(fr, (1.0, -0.1, 0.9), 'Semana máxima en México', 19, col=(110, 110, 116), fk='sb')
    head(fr, ['Semanas de', '100 horas.'], RED, t, t0 + 0.1, kicker='Razón 2')
    ui_pill(fr, 'Según Dan Houser (2018) · LFT México', clamp(lt / 0.5))


def s_desks(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(7.2, wide=True), yaw=-30 + lt * 4, pitch=42)
    tsw = T(('c2', 5, 'saliera'), default=t0 + 1.5)
    for r in range(4):
        for c in range(6):
            x, z = -2.25 + c * 0.9, -1.2 + r * 0.8
            idx = r * 6 + c
            pink = idx in (3, 10, 17, 20)
            flip = clamp((t - tsw - 0.4 - (c + r) * 0.12) / 0.3)
            col = PINK if (pink or flip >= 1) else mix(RED, PINK, flip)
            fr.meshes.append(box(0.62, 0.32, 0.42, (210, 206, 198), cols={'top': (226, 222, 214)}, shadow=0.25).tf(t=(x, 0, z)))
            fr.meshes.append(box(0.3, 0.2, 0.03, col, shadow=0).tf(t=(x, 0.32, z - 0.1)))
            fr.meshes.append(sphere(0.09, col, nu=10, nv=6, shadow=0.2).tf(t=(x, 0.18, z + 0.32)))
    fr.ui.append(lambda img, d: (pill(img, d, 40, (H - 150) if not VERT else H * 0.66, 'Red Dead 2', 1, anchor='l', dotc=RED),
                                 pill(img, d, 250 if not VERT else 300, (H - 150) if not VERT else H * 0.66, 'GTA VI', 1, anchor='l', dotc=PINK)))
    ui_pill(fr, 'Recreación', clamp(lt / 0.5))
    head(fr, ['Sin el estudio', 'completo.'], PINK, t, t0 + 0.1, kicker='Razón 2')


# ------------------------------------------------------------------ RAZÓN 3
def s_gears(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.2, 0), dist=vfit(6.6), yaw=-10 + lt * 3, pitch=8)
    a = lt * 40
    fr.meshes += gear(0.9, 14, 0.25, ORANGE, -0.75, 1.2, 0, rot=a)
    sw = clamp((lt - 1.2) / 0.8)
    fr.meshes += gear(0.6, 10, 0.25, mix(BLUE, TEAL, sw), 0.85, 1.2 + (1 - ease(sw)) * 0.0, 0, rot=-a * 1.4 + 9)
    fr.meshes += gear(0.45, 8, 0.25, (120, 120, 128), 0.6, 2.25, 0.05, rot=a * 1.9)
    head(fr, ['Se cambió', 'por dentro.'], ORANGE, t, t0 + 0.1, kicker='Razón 3')
    ui_pill(fr, 'Recreación', clamp(lt / 0.5))


def s_houser(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0.3, 0.9, 0), dist=vfit(6.6), yaw=-24 + lt * 3, pitch=10)
    # puerta
    fr.meshes.append(box(0.12, 2.0, 0.12, (150, 150, 156)).tf(t=(-0.6, 0, 0)))
    fr.meshes.append(box(0.12, 2.0, 0.12, (150, 150, 156)).tf(t=(0.6, 0, 0)))
    fr.meshes.append(box(1.32, 0.12, 0.12, (150, 150, 156)).tf(t=(0, 2.0, 0)))
    door = box(1.08, 1.94, 0.06, (196, 170, 130), shadow=0).tf(t=(0.54, 0, 0)).tf(ry=-70 * ease(lt / 0.8), t=(-0.54, 0.02, 0))
    fr.meshes.append(door)
    k = clamp((lt - 0.5) / 3.0)
    fr.meshes += person(1.35, (70, 90, 120), x=-0.0 + 2.2 * k, z=0.4 + 0.8 * k, ry=80, walk=lt * 7)
    # pluma (escritor)
    px = -1.7
    fr.meshes.append(cyl(0.07, 1.0, (40, 40, 46), n=14, r2=0.07, gloss=0.6).tf(rz=-25, t=(px, 0.5 + 0.1 * math.sin(lt * 2), 0.2)))
    fr.meshes.append(cyl(0.07, 0.25, GOLD, n=14, r2=0.0, gloss=0.6, shadow=0).tf(rz=155, t=(px + 0.03, 0.55 + 0.1 * math.sin(lt * 2), 0.2)))
    ui_label3(fr, (0.0 + 2.2 * k, 1.6, 0.4 + 0.8 * k), 'Dan Houser', 'cofundador y guionista · se fue en 2020', a=clamp((lt - 0.6) / 0.5), length=60)
    head(fr, ['Se fue', 'un fundador.'], ORANGE, t, t0 + 0.1, kicker='Razón 3 · 2020')


def s_homes(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(8.0, wide=True), yaw=-6 + lt * 2, pitch=22)
    fr.meshes += building(1.8, 1.4, 1.2)
    xs = [-3.0, -1.6, 1.6, 3.0]
    zs = [1.4, 2.0, 2.0, 1.4]
    for i, (x, z) in enumerate(zip(xs, zs)):
        k = eback((lt - 0.2 - i * 0.2) / 0.5)
        if k <= 0:
            continue
        hb = box(0.8, 0.6 * k, 0.7, (236, 226, 208), shadow=0.35)
        roof = extrude([(-0.48, 0), (0.48, 0), (0, 0.4)], 0.78, (196, 84, 64), shadow=0, y0=-0.39).tf(rx=90, t=(0, 0.6 * k + 0.0, 0))
        roof.V[:, 1] = np.maximum(roof.V[:, 1], 0.6 * k)
        mon = box(0.3, 0.2, 0.03, (20, 20, 24), shadow=0)
        decal(mon, mon.FACE['front'], screen_tex('house', 120, 80))
        for m in (hb, mon.tf(t=(0, 0.25, 0.36))):
            fr.meshes.append(m.tf(t=(x, 0, z)))
    def under(d, cam, lt=lt):
        for x, z in zip(xs, zs):
            line3(d, cam, [(x, 0.02, z - 0.4), (x * 0.3, 0.02, 0.7)], (30, 30, 34), 1.4, dash=7, a=clamp(lt - 0.8))
    fr.under.append(under)
    head(fr, ['Todos', 'a casa.'], ORANGE, t, t0 + 0.1, kicker='Razón 3 · pandemia 2020')


def s_rules(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.2, 0), dist=vfit(7.0, wide=True), yaw=-8 + lt * 2, pitch=10)
    tilt = 8 * math.exp(-lt * 1.2) * math.cos(lt * 4)
    fr.meshes.append(cyl(0.45, 0.08, (90, 90, 96), n=24).tf(t=(0, 0, 0)))
    fr.meshes.append(cyl(0.06, 1.7, (90, 90, 96), n=12, shadow=0).tf(t=(0, 0.08, 0)))
    beam = box(3.0, 0.08, 0.1, (90, 90, 96), shadow=0, base=False).tf(rz=tilt, t=(0, 1.8, 0))
    fr.meshes.append(beam)
    for sgn in (-1, 1):
        x = 1.4 * sgn
        yb = 1.8 + math.sin(math.radians(tilt)) * x
        fr.meshes.append(cyl(0.55, 0.05, (180, 180, 186), n=26, shadow=0.3).tf(t=(x, yb - 0.9, 0)))
        fr.over.append(lambda d, cam, x=x, yb=yb: [line3(d, cam, [(x, yb, 0), (x + 0.5 * math.cos(a), yb - 0.88, 0.5 * math.sin(a))], (90, 90, 96), 1.2)
                                                    for a in (0.5, 2.6, 4.7)])
        if sgn < 0:
            # reloj +1 h
            fr.meshes.append(cyl(0.34, 0.12, (240, 240, 242), n=26, top=(250, 250, 250), shadow=0).tf(rx=90, t=(x, yb - 0.85 + 0.34, 0)))
            ui_text3(fr, (x, yb - 0.5, 0.1), '+1 h', 30, fk='mono')
        else:
            fr.meshes.append(calendar('LIBRE', '1', 'día', x - 0.0, 0, ry=0, col=(70, 160, 90), s=0.55, y=yb - 0.85))
    ui_text3(fr, (0, 2.3, 0), '=', 54, fk='xb')
    head(fr, ['Horas extra =', 'días libres.'], GREEN, t, t0 + 0.1, kicker='Razón 3 · según Bloomberg')


def s_badges(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.0, wide=True), yaw=-10 + lt * 3, pitch=14)
    for i in range(5):
        x = -2.2 + i * 1.1
        fl = clamp((lt - 0.4 - i * 0.25) / 0.45)
        b = box(0.7, 1.0, 0.04, (240, 240, 242), shadow=0.3, base=False)
        col = mix((160, 160, 166), BLUE, fl)
        decal(b, b.FACE['front'], text_tex('PLANTA' if fl > 0.5 else 'TEMPORAL', 220, 300, bg=(250, 250, 250), fg=col, size=34))
        fr.meshes.append(b.tf(ry=fl * 360 if fl < 1 else 0, t=(x, 1.0, 0)))
        fr.meshes.append(box(0.04, 0.5, 0.02, (120, 120, 126), shadow=0).tf(t=(x, 1.5, 0)))
    fr.meshes.append(calendar('PLAN', '✓', 'productores', 2.7, -0.6, ry=-20, col=BLUE, s=0.7))
    head(fr, ['Más gente', 'de planta.'], BLUE, t, t0 + 0.1, kicker='Razón 3 · según Bloomberg')


def s_hourglass(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(6.4), yaw=-12 + lt * 3, pitch=10)
    fr.meshes += hourglass(0.9, 0, 1.15, k=clamp(lt / max(1, dur)))
    hb = 1 + 0.06 * math.sin(lt * 6) ** 8
    hm = extrude(heart_pts(0.85 * hb), 0.3, (220, 60, 80), top=(236, 90, 106), gloss=0.4, shadow=0.35, y0=-0.15)
    fr.meshes.append(hm.tf(rx=-90, t=(-1.1, 1.0, 0)))
    head(fr, ['Más sano…', 'más lento.'], GREEN, t, t0 + 0.1, kicker='Razón 3')


# ------------------------------------------------------------------ RAZÓN 4
def hotel_room(fr, x0=0.0):
    fr.meshes.append(box(1.6, 0.45, 2.1, (240, 236, 228), cols={'top': (250, 248, 242)}, shadow=0.35).tf(t=(x0 - 1.4, 0, 0.3)))
    fr.meshes.append(box(1.6, 0.18, 0.5, (250, 250, 252), shadow=0).tf(t=(x0 - 1.4, 0.45, -0.5)))
    fr.meshes.append(box(1.62, 0.9, 0.12, (140, 100, 70), shadow=0).tf(t=(x0 - 1.4, 0, -0.78)))
    fr.meshes.append(box(0.45, 0.5, 0.45, (150, 106, 72), shadow=0.3).tf(t=(x0 - 0.25, 0, -0.6)))
    fr.meshes.append(cyl(0.12, 0.35, (230, 210, 170), n=14, r2=0.2, y0=0.5, shadow=0).tf(t=(x0 - 0.25, 0, -0.6)))
    fr.meshes += tv(x0 + 1.5, 0.0, ry=-28, kind='term')


def s_hotel(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0.2, 0.8, 0), dist=vfit(7.0, wide=True) - lt * 0.15, yaw=12 + lt * 3, pitch=16)
    hotel_room(fr)
    ui_pill(fr, 'Recreación', clamp(lt / 0.5))
    head(fr, ['Hackeado desde', 'un hotel.'], RED, t, t0 + 0.1, kicker='Razón 4 · septiembre 2022')
    big_counter(fr, '17 años', sub='EDAD DEL HACKER', pos=(W * (0.18 if not VERT else 0.5), H * (0.5 if not VERT else 0.64)),
                size=52 if not VERT else 70, a=clamp((lt - 0.8) / 0.5))


def s_nolaptop(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(5.6, wide=True), yaw=-30 + lt * 3, pitch=18)
    base = box(1.3, 0.06, 0.9, (190, 192, 198), shadow=0.35)
    scr = box(1.3, 0.86, 0.04, (60, 62, 70), shadow=0).tf(rx=-12, t=(0, 0.06, -0.45))
    fr.meshes += [base.tf(t=(-0.9, 0, 0)), scr.tf(t=(-0.9, 0, 0))]
    k = clamp((lt - 0.4) / 0.5)
    def over(d, cam, k=k):
        if k > 0:
            c = (-0.9, 0.5, 0)
            line3(d, cam, [(c[0] - 0.9, c[1] - 0.6, 0.3), (c[0] - 0.9 + 1.8 * k, c[1] - 0.6 + 1.2 * k, 0.3)], (220, 40, 40), 7)
            if k >= 1:
                line3(d, cam, [(c[0] + 0.9, c[1] - 0.6, 0.3), (c[0] - 0.9, c[1] + 0.6, 0.3)], (220, 40, 40), 7)
    fr.over.append(over)
    # cámara de vigilancia
    cb = box(0.6, 0.26, 0.26, (236, 236, 238), shadow=0.3, base=False)
    lens = cyl(0.09, 0.08, (20, 20, 24), n=14, shadow=0).tf(rx=90, t=(0, 0, 0.13))
    for m in (cb, lens):
        fr.meshes.append(m.tf(ry=-140 + 20 * math.sin(lt * 1.5), rx=15, t=(1.3, 1.7, -0.4)))
    fr.meshes.append(box(0.06, 1.55, 0.06, (150, 150, 156)).tf(t=(1.3, 0, -0.4)))
    ui_label3(fr, (1.3, 1.85, -0.4), 'Bajo vigilancia', a=clamp((lt - 0.8) / 0.5), length=70)
    ui_label3(fr, (-0.9, 0.9, 0), 'Sin computadora', a=clamp((lt - 0.6) / 0.5), side=-1, length=80)
    head(fr, ['Sin', 'computadora.'], RED, t, t0 + 0.1, kicker='Razón 4 · septiembre 2022')


def s_kit(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.7, 0), dist=vfit(7.2, wide=True), yaw=-8 + lt * 2.5, pitch=16)
    k = [T(('c4', 3, 'tele'), default=t0), T(('c4', 3, 'Fire'), default=t0 + 1), T(('c4', 3, 'celular'), default=t0 + 2)]
    a = [eback((t - x) / 0.5) for x in k]
    if a[0] > 0:
        fr.meshes += [m.tf(s=max(0.01, a[0]), t=(0, 0, 0)) for m in tv(-2.2, 0, ry=10, kind='term')]
    if a[1] > 0:
        stick = box(0.7, 0.12, 0.2, (24, 24, 28), shadow=0.35, gloss=0.5).tf(s=max(0.01, a[1]), ry=-20, t=(0, 0.0, 0.3))
        fr.meshes.append(stick)
    if a[2] > 0:
        fr.meshes += [m.tf(s=max(0.01, a[2]), t=(0, 0, 0)) for m in phone(2.2, 0.0, 0.3, ry=-20, s=1.0)]
    def under(d, cam, a=a):
        if a[1] > 0.9:
            line3(d, cam, [(-1.6, 0.05, 0.4), (-0.4, 0.05, 0.3)], (30, 30, 34), 1.5, dash=6)
        if a[2] > 0.9:
            line3(d, cam, [(0.4, 0.05, 0.3), (1.8, 0.05, 0.3)], (30, 30, 34), 1.5, dash=6)
    fr.under.append(under)
    for i, (txt, p) in enumerate((('Tele del hotel', (-2.2, 1.8, 0)), ('Fire Stick', (0, 0.25, 0.3)), ('Celular', (2.2, 0.2, 0.3)))):
        if a[i] > 0.6:
            ui_text3(fr, (p[0], p[1] + 0.35, p[2]), txt, 24, fk='b')
    head(fr, ['Tele + Fire Stick', '+ celular.'], RED, t, t0 + 0.1, kicker='Razón 4')


def s_clips(fr, t, lt, dur):
    t0 = t - lt
    t5 = PA('c4', 5)
    k5 = ease((t - t5) / 1.0) if t5 is not None else 0
    fr.cam = Cam(target=(0, 1.5, 0), dist=vfit(8.4, wide=True) - k5 * 2.2, yaw=-6 + lt * 2, pitch=8)
    fr.meshes += phone(0, 0.0, 1.4, ry=0, s=0.8)
    n = int(90 * eout((lt - 0.2) / 2.4))
    tex_vc = screen_tex('vc', 160, 90)
    for i in range(n):
        r, c = divmod(i, 15)
        fx = (c - 7) * 0.42
        fy = 0.3 + r * 0.42
        age = clamp((lt - 0.2 - i * 0.026) / 0.5)
        x = lerp(0, fx, ease(age)); y = lerp(0.2, fy, ease(age)); z = lerp(1.4, -0.4, ease(age))
        card_m = box(0.38, 0.22, 0.02, (30, 30, 34), shadow=0, base=False, edge=False)
        decal(card_m, card_m.FACE['front'], tex_vc)
        fr.meshes.append(card_m.tf(t=(x, y, z)))
    big_counter(fr, f'{n}', sub='VIDEOS FILTRADOS', pos=(W * (0.86 if not VERT else 0.5), H * (0.55 if not VERT else 0.64)),
                size=72 if not VERT else 90, a=clamp(lt / 0.4) * (1 - k5))
    if t5 is not None and t >= t5:
        head(fr, ['Gráficos a', 'medio hacer.'], PINK, t, t5, kicker='Vice City, sin terminar')
        ui_pill(fr, 'Recreación · no son imágenes reales', clamp((t - t5) / 0.4))
    else:
        head(fr, ['90 videos', 'filtrados.'], RED, t, t0 + 0.1, kicker='Razón 4')


def s_confirm(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(6.0), yaw=-10 + lt * 3, pitch=16)
    doc = box(1.5, 1.9, 0.04, PAPER, shadow=0.35)
    def dtx(dd, img):
        for i in range(9):
            dd.rectangle((30, 40 + i * 30, 30 + (220 if i % 3 else 160), 52 + i * 30), fill=(200, 200, 204))
    decal(doc, doc.FACE['front'], tex(300, 380, PAPER + (255,), dtx))
    fr.meshes.append(doc.tf(rx=-8, t=(0, 0, 0)))
    k = eback((lt - 0.5) / 0.45)
    if k > 0:
        st = cyl(0.5 * k, 0.05, (60, 170, 90), n=30, shadow=0, top=(70, 180, 100))
        fr.meshes.append(st.tf(rx=82, t=(0.25, 0.75, 0.12)))
        ui_text3(fr, (0.25, 0.75, 0.2), '✓', 64, fk='xb', col=(255, 255, 255))
    ui_text3(fr, (0, -0.05, 0.6), 'Rockstar, 19 sep 2022', 20, col=(110, 110, 116), fk='sb')
    head(fr, ['Eran', 'reales.'], GREEN, t, t0 + 0.1, kicker='Razón 4')


def s_money(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.0, wide=True), yaw=-16 + lt * 3, pitch=16)
    k = eout(lt / 2.4)
    for j, (x, z) in enumerate(((-1.2, 0), (0, -0.2), (1.2, 0), (-0.6, 0.9), (0.6, 0.9))):
        fr.meshes += bills(max(1, int(k * (14 - j * 2))), x, z)
    v = 5e6 * k
    big_counter(fr, '$' + fmt_int(v), sub='DÓLARES DE DAÑO (ESTIMADO DE ROCKSTAR)', pos=(W * 0.5, H * (0.30 if not VERT else 0.30)),
                size=60 if not VERT else 76, col=(40, 120, 60))
    ui_pill(fr, '+ miles de horas de trabajo', clamp((lt - 1.4) / 0.5), dotc=RED)
    head(fr, [], RED, t, t0)


def s_trailer(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.1, 0), dist=vfit(6.4), yaw=-14 + lt * 3, pitch=10)
    fr.meshes += tv(0.4, 0, ry=-6, kind='play', w=2.4, h=1.35, y=0.45)
    # gotas de "fuga"
    for i in range(4):
        ph = (lt * 0.8 + i * 0.25) % 1
        fr.meshes.append(sphere(0.06, (60, 140, 230), nu=10, nv=6, shadow=0, gloss=0.8).tf(t=(-0.4 + i * 0.5, 0.45 - ph * 0.45, 0.2)))
    fr.meshes.append(calendar('DIC', '5', '2023', -2.0, 0.2, ry=24, col=RED, s=0.75))
    ui_label3(fr, (0.4, 1.9, 0), 'Tráiler 1', 'publicado antes, tras filtrarse', a=clamp((lt - 0.5) / 0.5), length=80)
    head(fr, ['Hasta el', 'tráiler.'], RED, t, t0 + 0.1, kicker='Razón 4')


# ------------------------------------------------------------------ RAZÓN 5
def s_hype(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(6.6) - lt * 0.2, yaw=-10 + lt * 5, pitch=12)
    fr.meshes.append(cyl(0.9, 0.3, (236, 236, 240), n=36, gloss=0.3))
    fr.meshes.append(case_at('VI', 0, 0.3, 0, ry=lt * 25))
    for i in range(6):
        a = math.radians(i * 60 + 20)
        x, z = 2.3 * math.cos(a), 2.3 * math.sin(a) * 0.8
        fr.meshes += phone(x, 0.75 + 0.1 * math.sin(lt * 2 + i), z, ry=-math.degrees(a) - 90, rx=-70, s=0.55)
    def under(d, cam, lt=lt):
        for j in range(3):
            r = 1.0 + ((lt * 0.6 + j / 3) % 1) * 1.8
            ring3(d, cam, (0, 0.01, 0), r, (30, 30, 34), 1.4, 1 - ((lt * 0.6 + j / 3) % 1))
    fr.under.append(under)
    head(fr, ['Lo que tú', 'esperas.'], PINK, t, t0 + 0.1, kicker='Razón 5')


def s_views(fr, t, lt, dur):
    t0 = t - lt
    t3 = PA('c5', 3)
    k3 = ease((t - t3) / 0.45) if t3 is not None else 0
    fr.cam = Cam(target=(0 + k3 * 0.2, 1.1, 0), dist=vfit(6.8, wide=True) + k3 * 0.6, yaw=-10 + lt * 2, pitch=10)
    if k3 < 0.5:
        ms = tv(0, 0, ry=0, kind='play', w=2.6, h=1.46, y=0.35)
        for m in ms:
            m.alpha = 1 - k3
        fr.meshes += ms
        v = 90421491 * eout((t - T(('c5', 2, '90'), default=t0)) / 1.6)
        big_counter(fr, fmt_int(max(0, v)), sub='VISTAS EN 24 HORAS', pos=(W * 0.5, H * (0.30 if not VERT else 0.30)),
                    size=64 if not VERT else 80, a=1 - k3)
    if k3 > 0:
        data = [('GTA VI · tráiler 1', 90.4, PINK), ('MrBeast · récord previo', 59.4, (150, 150, 156)), ('BTS · Butter (música)', 108.2, (200, 200, 206))]
        for i, (lab, v, col) in enumerate(data):
            x = -1.4 + i * 1.6
            hh = 0.026 * v * eout((t - t3 - i * 0.2) / 0.8)
            m = box(0.8, max(0.02, hh), 0.8, col, shadow=0.35)
            if i == 2:
                m.alpha = 0.5
            fr.meshes.append(m.tf(t=(x, 0, 0)))
            ui_text3(fr, (x, hh + 0.3, 0), f'{v:.1f} M'.replace('.', ','), 28, fk='mono', a=k3)
            ui_text3(fr, (x, -0.05, 0.75), lab, 17, col=(110, 110, 116), fk='sb', a=k3)
        head(fr, ['Récord fuera', 'de la música.'], PINK, t, t3, kicker='Guinness · dic 2023')
    else:
        head(fr, ['90 millones', 'en 24 horas.'], PINK, t, t0 + 0.1, kicker='Razón 5')


def ll(lat, lon):
    """lat/lon -> plano del mapa (x, z)."""
    return ((lon + 83.5) * 0.38, -(lat - 24.5) * 0.38)


FLORIDA = [(30.7, -87.6), (30.4, -86.0), (29.9, -84.9), (30.1, -83.9), (29.2, -83.1), (28.0, -82.8), (27.0, -82.4),
           (26.1, -81.8), (25.2, -81.1), (25.3, -80.4), (25.9, -80.1), (26.8, -80.0), (27.8, -80.4), (29.0, -80.9),
           (30.4, -81.4), (30.7, -81.5), (31.0, -84.0), (31.0, -87.6)]
YUCATAN = [(21.6, -87.0), (21.5, -88.4), (21.3, -89.8), (20.9, -90.4), (19.8, -90.7), (18.6, -91.4), (18.2, -89.0),
           (17.8, -88.2), (18.5, -87.8), (19.8, -87.4), (20.6, -86.8)]
CUBA = [(21.9, -84.9), (22.8, -83.0), (23.1, -81.5), (23.2, -80.0), (22.4, -77.8), (21.0, -75.7), (20.2, -74.2),
        (19.9, -75.5), (20.0, -77.2), (20.7, -78.7), (21.6, -81.1), (22.0, -82.9)]


def s_map(fr, t, lt, dur):
    t0 = t - lt
    t5 = PA('c5', 5)
    k5 = ease((t - t5) / 1.4) if t5 is not None else 0
    fr.cam = Cam(target=(0.2, 0.0, 0.6), dist=vfit(8.0, wide=True) + k5 * 4.0, yaw=-8 + lt * 2, pitch=52 - k5 * 4)
    for poly, col, hh in ((FLORIDA, PINK, 0.14), (YUCATAN, (120, 180, 110), 0.1), (CUBA, (170, 196, 150), 0.08)):
        pts = [ll(a, b) for a, b in poly]
        kk = eback((lt - 0.2) / 0.6)
        fr.meshes.append(extrude(pts, max(0.01, hh * kk), col, top=tuple(min(255, int(c * 1.08)) for c in col), shadow=0, edge=True))
    mia, cun = ll(25.8, -80.2), ll(21.16, -86.85)
    def over(d, cam, lt=lt):
        k = clamp((lt - 0.8) / 1.2)
        P0 = np.array([cun[0], 0.12, cun[1]]); P1 = np.array([mia[0], 0.16, mia[1]])
        pts = []
        for i in range(int(40 * k) + 1):
            u = i / 40
            p = P0 + (P1 - P0) * u
            p[1] += math.sin(u * math.pi) * 1.4
            pts.append(p)
        if len(pts) > 1:
            line3(d, cam, pts, (30, 30, 34), 1.6, dash=7)
        if k5 > 0:
            # zona más grande (plan original)
            r = 2.5 + 4 * k5
            ring3(d, cam, (0.0, 0.05, 1.5), r, (30, 30, 34), 1.6, a=k5, dash=8)
    fr.over.append(over)
    dot = lambda p, c: fr.meshes.append(sphere(0.12, c, nu=12, nv=8, shadow=0, gloss=0.6).tf(t=(p[0], 0.25, p[1])))
    dot(cun, (40, 120, 200))
    ui_text3(fr, (cun[0], 0.6, cun[1]), 'Cancún', 22, fk='b')
    ui_text3(fr, (ll(28.0, -81.8)[0], 0.5, ll(28.0, -81.8)[1]), 'Leonida', 30, fk='xb', col=(200, 40, 100))
    ui_text3(fr, (ll(28.0, -81.8)[0], 0.5, ll(28.0, -81.8)[1]), '(inspirada en Florida)', 17, fk='sb', col=(110, 110, 116), dy=30)
    ui_pill(fr, 'Mapa aproximado', clamp(lt / 0.5))
    if t5 is not None and t >= t5:
        head(fr, ['Era aún', 'más grande.'], PINK, t, t5, kicker='Según Bloomberg (2022)')
    else:
        head(fr, ['Bienvenido', 'a Leonida.'], PINK, t, t0 + 0.1, kicker='Razón 5')


def s_dates(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(7.0, wide=True), yaw=-4 + lt * 2, pitch=10)
    k1 = T(('c5', 6, 'luego'), default=t0 + 2)
    k2 = T(('c5', 7, 'ahora'), default=t0 + 4)
    cr1 = clamp((t - k1) / 0.6)
    cr2 = clamp((t - k2) / 0.6)
    a3 = eback((t - k2 - 0.2) / 0.5)
    fr.meshes.append(calendar('OTOÑO', '2025', 'fecha original', -2.3, 0, ry=14, col=(150, 150, 156), cross=cr1))
    fr.meshes.append(calendar('MAYO', '26', '2026', 0, 0, col=(150, 150, 156), cross=cr2))
    if a3 > 0:
        fr.meshes.append(calendar('NOVIEMBRE', '19', '2026', 2.3, 0, ry=-14, col=PINK, s=max(0.01, a3)))
        fr.under.append(lambda d, cam: ring3(d, cam, (2.3, 0.01, 0), 1.0 + 0.1 * math.sin(lt * 4), (30, 30, 34), 2.0))
    head(fr, ['Se movió', '2 veces.'] if a3 <= 0 else ['19 de', 'noviembre.'], PINK, t, t0 + 0.1 if a3 <= 0 else k2,
         kicker='Razón 5 · fechas anunciadas')


def s_polish(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(5.8), yaw=-10 + lt * 3, pitch=10)
    fr.meshes.append(case_at('VI', 0, 0.12, 0, ry=lt * 30))
    fr.meshes.append(cyl(0.9, 0.12, (236, 236, 240), n=30))
    def over(d, cam, lt=lt):
        for i in range(6):
            ph = (lt * 0.9 + i / 6) % 1
            a = math.sin(ph * math.pi)
            p = (1.1 * math.cos(i * 1.7 + lt), 0.6 + 1.4 * ((i * 0.37) % 1), 0.6 * math.sin(i * 1.7 + lt))
            s, z = cam.proj([p])
            x, y = s[0]
            r = (8 + 10 * a) * SS
            col = mix((250, 250, 248), (240, 170, 60), a)
            d.polygon([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25), (x, y + r),
                       (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)], fill=col)
    fr.over.append(over)
    head(fr, ['Más tiempo', 'para pulirlo.'], ORANGE, t, t0 + 0.1, kicker='Razón oficial · Take-Two')


# ------------------------------------------------------------------ CIERRE
def s_recap(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(7.2, wide=True), yaw=-4 + lt * 2, pitch=16)
    keys = [T(('c6', 0, 'juego'), default=t0), T(('c6', 0, 'vaquero'), default=t0 + 1), T(('c6', 0, 'estudio'), default=t0 + 2),
            T(('c6', 0, 'hackeo'), default=t0 + 3), T(('c6', 0, 'ambición'), default=t0 + 4)]
    xs = [-2.6, -1.3, 0, 1.3, 2.6]
    for i, (x, kt) in enumerate(zip(xs, keys)):
        a = eback((t - kt) / 0.5)
        if a <= 0:
            continue
        s = max(0.01, a)
        if i == 0:
            fr.meshes += coins(int(8 * s), x, 0, r=0.3)
        elif i == 1:
            fr.meshes += hat(x, 0, 0, s=0.9 * s)
        elif i == 2:
            fr.meshes += gear(0.55 * s, 10, 0.2, ORANGE, x, 0.6, 0, rot=lt * 40)
        elif i == 3:
            fr.meshes += [m.tf(s=0.6 * s, t=(x, 0, 0)) for m in tv(0, 0, kind='term')]
        else:
            fr.meshes.append(extrude([ll(a2, b2) for a2, b2 in FLORIDA], 0.12, PINK, shadow=0.3).tf(s=0.5 * s, t=(x - 0.1, 0, 0.4)))
        ui_text3(fr, (x, -0.05, 0.9), str(i + 1), 26, fk='mono', a=clamp(a))
    head(fr, ['5 razones,', '13 años.'], PINK, t, t0 + 0.1, kicker='En resumen')


def s_nov19(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(5.4) - lt * 0.15, yaw=-12 + lt * 4, pitch=10)
    a = eback(lt / 0.5)
    fr.meshes.append(calendar('NOVIEMBRE', '19', '2026', 0, 0, col=PINK, s=max(0.01, 1.2 * a)))
    def under(d, cam, lt=lt):
        for j in range(3):
            ph = (lt * 0.5 + j / 3) % 1
            ring3(d, cam, (0, 0.01, 0), 0.9 + ph * 1.6, (30, 30, 34), 1.6, 1 - ph)
    fr.under.append(under)
    head(fr, ['¿Valió', 'la pena?'], PINK, t, t0 + 0.1, kicker='PS5 · Xbox Series')


def s_brand(fr, t, lt, dur, sub=None):
    t0 = t - lt
    fr.mono = False
    fr.cam = Cam(target=(0, 1.2, 0), dist=vfit(6.4), yaw=lt * 6, pitch=14)
    fr.meshes.append(sphere(0.55, (24, 24, 28), nu=32, nv=20, gloss=0.9).tf(t=(0, 1.2, 0)))
    a = lt * 1.6
    fr.meshes.append(sphere(0.1, PINK, nu=12, nv=8, shadow=0, gloss=0.5).tf(t=(1.25 * math.cos(a), 1.2 + 0.35 * math.sin(a), 1.25 * math.sin(a))))
    def under(d, cam):
        P = [(1.25 * math.cos(u), 1.2 + 0.35 * math.sin(u), 1.25 * math.sin(u)) for u in np.linspace(0, 2 * math.pi, 90)]
        line3(d, cam, P, (30, 30, 34), 1.6)
    fr.under.append(under)
    def f(img, d, lt=lt):
        k = ease(lt / 0.5)
        y = H * (0.80 if not VERT else 0.27)
        draw_text(d, (W / 2, y), 'MENTE EN ÓRBITA', font('mono', 64 if not VERT else 74), INK, 'mm', a=k, spacing=5)
        if sub:
            pill(img, d, W / 2, y + (70 if not VERT else 90), sub, k, dotc=(220, 40, 40))
    fr.ui.append(f)


def s_brand_yt(fr, t, lt, dur):
    s_brand(fr, t, lt, dur, sub='Las 5 razones completas en YouTube')


def s_question(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(6.4), yaw=-6 + lt * 2, pitch=12)
    fr.meshes.append(case_at('VI', 0, 0, 0, ry=12 * math.sin(lt)))
    def f(img, d, lt=lt):
        k = ease((lt - 0.3) / 0.5)
        y = H * (0.60 if not VERT else 0.62)
        dx = 330 if not VERT else 300
        pill(img, d, W / 2 - dx, y, '  SÍ  ', k, fill=(60, 170, 90), col=(255, 255, 255), size=40 if not VERT else 52, border=(60, 170, 90), fnt='xb')
        pill(img, d, W / 2 + dx, y, '  NO  ', k, fill=(220, 60, 60), col=(255, 255, 255), size=40 if not VERT else 52, border=(220, 60, 60), fnt='xb')
    fr.ui.append(f)
    head(fr, ['¿Valió la pena', 'la espera?'], PINK, t, t0 + 0.1, kicker='Comenta')


def s_loop(fr, t, lt, dur):
    s_birth(fr, t, lt, dur, loop=True)


# ------------------------------------------------------------------ guion de escenas
# (clave, función). clave = ('card', capítulo) o (capítulo, frase)
SHOTS = [
    (('c0', 0), s_birth), (('c0', 2), s_bars), (('c0', 6), s_xray),
    (('card', 'c1'), None), (('c1', 1), s_sales), (('c1', 2), s_consoles), (('c1', 5), s_tower), (('c1', 7), s_space),
    (('c1', 8), s_coins),
    (('card', 'c2'), None), (('c2', 1), s_rdr), (('c2', 3), s_globe), (('c2', 4), s_hours), (('c2', 6), s_desks),
    (('card', 'c3'), None), (('c3', 1), s_gears), (('c3', 2), s_houser), (('c3', 3), s_homes), (('c3', 4), s_rules),
    (('c3', 5), s_badges), (('c3', 6), s_hourglass),
    (('card', 'c4'), None), (('c4', 1), s_hotel), (('c4', 2), s_nolaptop), (('c4', 3), s_kit), (('c4', 4), s_clips),
    (('c4', 6), s_confirm), (('c4', 7), s_money), (('c4', 8), s_trailer),
    (('card', 'c5'), None), (('c5', 1), s_hype), (('c5', 2), s_views), (('c5', 4), s_map), (('c5', 6), s_dates),
    (('c5', 8), s_polish),
    (('c6', 0), s_recap), (('c6', 1), s_nov19), (('c6', 2), s_brand), (('c6', 3), s_question), (('c6', 4), s_loop),
    (('out', 0), s_brand_yt), (('out', 1), s_question),
]
LEAD = 0.2


def build_shots():
    out = []
    for key, fn in SHOTS:
        if key[0] == 'card':
            c = key[1]
            a = PA(c, 0)
            if a is None:
                continue
            start = a - 1.25
            out.append({'key': key, 'fn': (lambda fr, t, lt, dur, c=c: card(fr, t, lt, dur, c)), 't0': start, 'card': True})
        else:
            a = PA(*key)
            if a is None:
                continue
            out.append({'key': key, 'fn': fn, 't0': max(0.0, a - LEAD), 'card': False})
    out.sort(key=lambda s: s['t0'])
    out[0]['t0'] = 0.0
    for s, n in zip(out[:-1], out[1:]):
        s['t1'] = n['t0']
    out[-1]['t1'] = DUR + 0.01
    return out


SH = build_shots()
CUTS = [s['t0'] for s in SH[1:]]
XF = 0.28


def shot_at(t):
    for i, s in enumerate(SH):
        if s['t0'] <= t < s['t1']:
            return i
    return len(SH) - 1


def render_shot(i, t):
    s = SH[i]
    fr = Frame()
    lt = t - s['t0']
    s['fn'](fr, t, lt, s['t1'] - s['t0'])
    # gris hacia/desde las tarjetas en blanco y negro
    if not s['card']:
        if i + 1 < len(SH) and SH[i + 1]['card']:
            fr.gray = max(fr.gray, clamp(1 - (s['t1'] - t) / 0.6))
        if i > 0 and SH[i - 1]['card']:
            fr.gray = max(fr.gray, clamp(1 - lt / 0.6))
    return E.render_frame(fr)


_FADE = {}


def sub_band(img):
    if 'b' not in _FADE:
        h = int(H * (0.16 if not VERT else 0.2))
        a = (np.linspace(0, 1, h) ** 1.4 * 215).astype(np.uint8)
        m = Image.fromarray(np.repeat(a[:, None], W, 1), 'L')
        _FADE['b'] = (m, Image.new('RGB', (W, h), (250, 250, 248)), h)
    m, c, h = _FADE['b']
    y = H - h if not VERT else int(H * 0.86) - h
    img.paste(c, (0, y), m)
    if VERT:
        img.paste(Image.new('RGB', (W, H - int(H * 0.86)), (250, 250, 248)), (0, int(H * 0.86)),
                  Image.new('L', (W, H - int(H * 0.86)), 215))


def subtitles(img, t):
    sub_band(img)
    d = ImageDraw.Draw(img)
    cur = None
    for p in TL['phrases']:
        if p['a'] - 0.1 <= t <= p['b'] + 0.35:
            cur = p
    if cur is None:
        return
    fs = 36 if not VERT else 50
    f = font('sb', fs)
    maxw = W * (0.74 if not VERT else 0.86)
    words = cur['words']
    lines, line, lw = [], [], 0
    sp = f.getlength(' ')
    for w in words:
        ww = f.getlength(w[0])
        if line and lw + sp + ww > maxw:
            lines.append(line); line, lw = [], 0
        line.append(w); lw += (sp if lw else 0) + ww
    if line:
        lines.append(line)
    if len(lines) > 2:  # mostrar el par de líneas que contiene la palabra actual
        cur_i = 0
        for li, ln in enumerate(lines):
            if ln[0][1] <= t:
                cur_i = li
        s = min(cur_i, len(lines) - 2)
        s -= s % 2
        lines = lines[s:s + 2]
    y0 = (H - 92) if not VERT else H * 0.79
    lh = fs * 1.3
    y0 -= (len(lines) - 1) * lh
    a = clamp((t - (cur['a'] - 0.1)) / 0.15) * clamp((cur['b'] + 0.35 - t) / 0.15)
    for li, ln in enumerate(lines):
        tw = sum(f.getlength(w[0]) for w in ln) + sp * (len(ln) - 1)
        x = W / 2 - tw / 2
        for w, wa, wb in ln:
            on = t >= wa - 0.03
            col = INK if on else (196, 196, 200)
            draw_text(d, (x, y0 + li * lh), w, f, col, 'lm', a=a)
            x += f.getlength(w) + sp


def chrome(img, t):
    d = ImageDraw.Draw(img)
    fz = 16 if not VERT else 24
    draw_text(d, (34, 34) if not VERT else (40, 120), '@mente_en_orbita1', font('sb', fz), (150, 150, 154), 'lm')


def render(t):
    i = shot_at(t)
    img = render_shot(i, t)
    s = SH[i]
    if i > 0 and t - s['t0'] < XF and not s['card'] and not SH[i - 1]['card']:
        prev = render_shot(i - 1, t)
        img = Image.blend(prev, img, ease((t - s['t0']) / XF))
    elif i > 0 and t - s['t0'] < XF:
        prev = render_shot(i - 1, t)
        img = Image.blend(prev, img, ease((t - s['t0']) / XF))
    subtitles(img, t)
    chrome(img, t)
    return img


def chunk(a, b, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    for fi in range(a, b):
        p.stdin.write(render(fi / FPS).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'preview':
        render(float(sys.argv[2])).save(sys.argv[3])
    elif cmd == 'chunk':
        chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif cmd == 'info':
        print('DUR', DUR, 'NF', NF)
        for s in SH:
            print(f"{s['t0']:7.2f} {s['t1']:7.2f} {s['key']}")
