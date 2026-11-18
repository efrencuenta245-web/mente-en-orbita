"""Piezas y escenas del video «¿Qué pasaría si México tuviera tren bala?» (YouTube, 18-nov-2026).
Sirve en horizontal (largo, MOTOR_FORMATO=h) y en vertical (Shorts): el acomodo cambia con M.HORIZONTAL.
Objetos nuevos: tren bala con nariz de pato (loft), camión, tren maglev sobre su viga, tren de pasajeros mexicano,
mapa de México en línea de luz, corte sísmico con ondas P y S, sismógrafo, velocímetro, reloj, barra de avance.
Cada escena es mk(**cfg) -> fn(t, fi, u, d) para montaje.py."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motor2 as M
from motor2 import (Frame, Cam, space, draw_objects, finish, title, kicker, pill, line3, dot3, seg, ease, eout, clamp,
                    lerp, named, WHITE, CYAN, RED, INK, MUTED, doodle_circle, doodle_arrow, rec_frame)
import piezas as P

M3 = M.M3
HZ = M.HORIZONTAL
W, H = M.W, M.H
S = M.SS

# ------------------------------------------------------------------ acomodo según formato
OBJ_CX = 0.67 if HZ else 0.5
OBJ_CY = 0.58 if HZ else 0.53
TX = 520 if HZ else 540              # centro del texto (título y kicker)
TY = 112 if HZ else 250              # y del título
TSZ = 58 if HZ else 72
CAP_Y = 905 if HZ else 1560          # subtítulos (montaje)

AZUL = (40, 92, 210)
BLANCO = (238, 240, 244)
OSCURO = (22, 26, 34)
GRISB = (90, 96, 108)
AMARILLO = (255, 226, 120)
VERDE = (120, 240, 160)
GUINDA = (150, 30, 50)
NARANJA = (255, 150, 60)
ROJO = (255, 70, 60)
CONCRETO = (128, 126, 120)


def fx_(x):
    """fracción horizontal -> px"""
    return x * W


def fy_(y):
    return y * H


# ------------------------------------------------------------------ utilidades de texto y UI
def texto(img, fx, x, y, txt, size, col=WHITE, k=1.0, f='sansx', glow=0.35, anchor='mm'):
    if k <= 0.01:
        return
    lay = Image.new('L', img.size, 0)
    ImageDraw.Draw(lay).text((x, y), txt, font=M.font(f, size), fill=int(255 * clamp(k)), anchor=anchor)
    img.paste(Image.new('RGB', img.size, col), (0, 0), lay)
    if glow:
        fx.paste(Image.new('RGB', img.size, M.scale_c(col, glow)), (0, 0), lay.filter(ImageFilter.GaussianBlur(8)))


def titulo(img, fx, l1, l2, u, u0=0.1, y=None, cx=None, size=None):
    """Título de 2 líneas (sans + serif) en el lado del texto."""
    title(img, fx, [(l1, 'sans'), (l2, 'serif')] if l2 else [(l1, 'sans')], TY if y is None else y,
          seg(u, u0, u0 + 0.45), size=size or TSZ, cx=TX if cx is None else cx)


def kick(img, txt, u, u0=0.0, y=None, cx=None):
    kicker(img, txt, (TY - 54) if y is None else y, seg(u, u0, u0 + 0.3), cx=TX if cx is None else cx, size=24)


def num(img, fx, txt, x, y, size, k, col=WHITE, glow=0.6):
    """Número que golpea (llega desde x2.6 desenfocado y se clava)."""
    if k <= 0.01:
        return
    f = M.font('sansx', size)
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    bx = d0.textbbox((0, 0), txt, font=f)
    w0, h0 = bx[2] - bx[0] + 40, bx[3] - bx[1] + 40
    lay = Image.new('L', (w0, h0), 0)
    ImageDraw.Draw(lay).text((20 - bx[0], 20 - bx[1]), txt, font=f, fill=255)
    kk = P.eout4(k)
    s = 2.6 - 1.6 * kk
    lay = lay.resize((max(1, int(w0 * s)), max(1, int(h0 * s))), Image.BILINEAR)
    if kk < 0.98:
        lay = lay.filter(ImageFilter.GaussianBlur(12 * (1 - kk)))
    a = lay.point(lambda v: int(v * min(1.0, k * 2.0)))
    xx, yy = int(x - lay.size[0] / 2), int(y - lay.size[1] / 2)
    img.paste(Image.new('RGB', lay.size, col), (xx, yy), a)
    fx.paste(Image.new('RGB', lay.size, M.scale_c(col, glow)), (xx, yy), a.filter(ImageFilter.GaussianBlur(10)))


def contador(u, u0, u1, v0, v1):
    return lerp(v0, v1, P.eout4(seg(u, u0, u1)))


def velocimetro(img, fx, x, y, r, val, vmax, k=1.0, label='KM/H', col=WHITE, warn=None):
    """Velocímetro de línea de luz (arco de 240°, marcas, aguja y número)."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    rr = r * (0.85 + 0.15 * P.resorte(k))
    a0, a1 = 150, 390
    d.arc((x - rr, y - rr, x + rr, y + rr), a0, a1, fill=M.scale_c((90, 92, 100), k), width=6)
    fr_ = clamp(val / vmax)
    c = col if warn is None or val < warn else ROJO
    if fr_ > 0.001:
        d.arc((x - rr, y - rr, x + rr, y + rr), a0, a0 + (a1 - a0) * fr_, fill=M.scale_c(c, k), width=10)
        df.arc((x - rr, y - rr, x + rr, y + rr), a0, a0 + (a1 - a0) * fr_, fill=M.scale_c(c, 0.6 * k), width=18)
    for j in range(13):
        a = math.radians(a0 + (a1 - a0) * j / 12)
        r0 = rr * (0.80 if j % 2 == 0 else 0.86)
        d.line((x + r0 * math.cos(a), y + r0 * math.sin(a), x + rr * 0.93 * math.cos(a), y + rr * 0.93 * math.sin(a)),
               fill=M.scale_c(INK, 0.7 * k), width=3)
    a = math.radians(a0 + (a1 - a0) * fr_)
    d.line((x, y, x + rr * 0.74 * math.cos(a), y + rr * 0.74 * math.sin(a)), fill=M.scale_c(c, k), width=6)
    df.line((x, y, x + rr * 0.74 * math.cos(a), y + rr * 0.74 * math.sin(a)), fill=M.scale_c(c, 0.5 * k), width=12)
    d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=M.scale_c(c, k))
    texto(img, fx, x, y + rr * 0.42, f'{val:.0f}', int(rr * 0.42), c, k, f='mono', glow=0.4)
    texto(img, fx, x, y + rr * 0.72, label, int(rr * 0.13), MUTED, k, f='mono', glow=0)


def reloj(img, fx, x, y, r, horas, k=1.0, label='', col=WHITE):
    """Reloj de manecillas: `horas` (float) desde las 12; la manecilla grande da una vuelta por hora."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    rr = r * (0.85 + 0.15 * P.resorte(k))
    d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=M.scale_c(col, k), width=5)
    df.ellipse((x - rr, y - rr, x + rr, y + rr), outline=M.scale_c(col, 0.4 * k), width=10)
    for j in range(12):
        a = j / 12 * 2 * math.pi
        d.line((x + rr * 0.84 * math.sin(a), y - rr * 0.84 * math.cos(a), x + rr * 0.95 * math.sin(a),
                y - rr * 0.95 * math.cos(a)), fill=M.scale_c(INK, k), width=4)
    am = (horas % 1.0) * 2 * math.pi
    ah = (horas / 12.0) * 2 * math.pi
    d.line((x, y, x + rr * 0.78 * math.sin(am), y - rr * 0.78 * math.cos(am)), fill=M.scale_c(CYAN, k), width=6)
    df.line((x, y, x + rr * 0.78 * math.sin(am), y - rr * 0.78 * math.cos(am)), fill=M.scale_c(CYAN, 0.6 * k), width=12)
    d.line((x, y, x + rr * 0.5 * math.sin(ah), y - rr * 0.5 * math.cos(ah)), fill=M.scale_c(col, k), width=9)
    d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=M.scale_c(col, k))
    if label:
        texto(img, fx, x, y + rr + 52, label, int(r * 0.32), col, k, f='mono', glow=0.3)


def barra(img, fx, x, y, w, frac, k=1.0, label='', col=CYAN, h=34):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.rounded_rectangle((x, y, x + w, y + h), radius=h / 2, outline=M.scale_c(INK, 0.7 * k), width=3)
    ww = max(h, w * clamp(frac))
    if frac > 0.002:
        d.rounded_rectangle((x + 5, y + 5, x + ww - 5, y + h - 5), radius=(h - 10) / 2, fill=M.scale_c(col, k))
        df.rounded_rectangle((x + 5, y + 5, x + ww - 5, y + h - 5), radius=(h - 10) / 2, fill=M.scale_c(col, 0.5 * k))
    if label:
        texto(img, fx, x + w / 2, y + h + 44, label, 30, MUTED, k, f='mono', glow=0)


def tarjeta_dato(img, fx, x, y, big, small, k, col=WHITE, size=None):
    """Número grande con etiqueta mono debajo (para comparar dos cosas)."""
    if k <= 0.01:
        return
    size = size or (110 if HZ else 120)
    num(img, fx, big, x, y, size, k, col)
    texto(img, fx, x, y + size * 0.78, small, 26, MUTED, seg(k, 0.5, 1.0), f='mono', glow=0)


def etiqueta(img, fx, txt, u, u0=0.3, x=None, y=None):
    """Etiqueta honesta: RECREACIÓN, ESTIMACIÓN, ESCALA EXAGERADA…"""
    pill(img, fx, (W - 40 if HZ else W / 2) if x is None else x, (70 if HZ else 1420) if y is None else y, txt,
         seg(u, u0, u0 + 0.3), size=20, border=(150, 150, 160), dot=False, anchor='r' if (HZ and x is None) else 'm')


def credito(img, txt, k=1.0):
    d = ImageDraw.Draw(img)
    d.text((40 if HZ else 40, (H - 40) if HZ else 1700), txt, font=M.font('mono', 20), fill=M.scale_c((170, 170, 176), k),
           anchor='ls')


# ------------------------------------------------------------------ cámara
def pose(dist, yaw, pitch, tx=0.0, ty=0.8, tz=0.0, roll=0.0):
    return dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll)


def camara(u, claves, cx=None, cy=None, fk=1.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'],
               cx=OBJ_CX if cx is None else cx, cy=OBJ_CY if cy is None else cy, roll=p.get('roll', 0.0), fk=fk)


def golpe_k(u, u0, dur=0.32):
    return (1 - seg(u, u0, u0 + dur)) ** 2 if u >= u0 else 0.0


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    return P.mover_img(img, amp * k * math.sin(t * 91.0) * math.cos(t * 37.0), amp * k * math.sin(t * 73.0 + 1.3))


# ------------------------------------------------------------------ mallas
def loft(secs, n=24, cols=None, name='cuerpo', gloss=0.7, rim=0.75, cap0=True, cap1=True):
    """Superficie por secciones: secs = [(x, hw, bot, top, e)] (e = exponente de superelipse; 2 = elipse, 5 = caja).
    cols(x, y, z, nz, ny) -> color de cada cara."""
    V, F, C = [], [], []
    for (x, hw, bot, top, e) in secs:
        c, hh = (top + bot) / 2, (top - bot) / 2
        for j in range(n):
            th = 2 * math.pi * j / n
            cz, sy = math.cos(th), math.sin(th)
            z = hw * math.copysign(abs(cz) ** (2 / e), cz)
            y = c + hh * math.copysign(abs(sy) ** (2 / e), sy)
            V.append((x, y, z))
    V = np.array(V, float)
    for i in range(len(secs) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            f = (a, b, b + n, a + n)
            F.append(f)
            q = V[list(f)].mean(0)
            th = 2 * math.pi * (j + 0.5) / n
            C.append(cols(q[0], q[1], q[2], math.cos(th), math.sin(th)) if cols else BLANCO)
    if cap0:
        F.append(tuple(range(n - 1, -1, -1)))
        C.append(cols(V[0, 0], 0, 0, 0, 0) if cols else BLANCO)
    if cap1:
        k = (len(secs) - 1) * n
        F.append(tuple(range(k, k + n)))
        C.append(cols(V[k, 0], 0, 0, 0, 0) if cols else BLANCO)
    m = M3.Mesh(V, F, C, shadow=0, gloss=gloss)
    return named(m, name, rim=rim, gloss=gloss)


def _col_bala(nariz_x0):
    def f(x, y, z, cz, sy):
        if sy < -0.55:
            return (70, 74, 84)
        if x > nariz_x0 + 0.55 and x < nariz_x0 + 1.25 and sy > 0.35:     # parabrisas
            return (16, 20, 28)
        if x <= nariz_x0 and 0.86 < y < 1.02 and abs(cz) > 0.45:          # banda de ventanas
            return (20, 24, 32)
        if 0.6 < y < 0.74 and abs(cz) > 0.3 and x < nariz_x0 + 1.9:       # franja azul
            return AZUL
        return BLANCO
    return f


def tren_bala(x=0.0, carros=2, nariz=3.2, largo=5.0, aletas=0.0, xray=False):
    """Shinkansen genérico (blanco con franja azul, sin logos). La nariz apunta a +x y termina en x.
    carros: cuántos carros detrás de la nariz (cada uno `largo`)."""
    ms = []
    x_n0 = x - nariz                                       # donde empieza la nariz
    secs = []
    for j in range(13):
        f = j / 12
        top = 0.40 + 1.0 * (1 - f ** 1.35) ** 1.1
        hw = 0.5 * (1 - 0.62 * f ** 2.2)
        bot = 0.30 + 0.07 * f ** 2
        e = 4.2 - 1.6 * f
        secs.append((x_n0 + nariz * f, hw, bot, max(top, bot + 0.04), e))
    body = [(x_n0 - largo, 0.5, 0.30, 1.40, 4.2), (x_n0, 0.5, 0.30, 1.40, 4.2)]
    ms.append(loft(body + secs, n=26, cols=_col_bala(x_n0), cap0=True, cap1=False))
    for c in range(1, carros):                             # carros de atrás (cajas redondeadas con su banda)
        x1 = x_n0 - largo * c - 0.12 * c
        ms.append(loft([(x1 - largo, 0.5, 0.30, 1.40, 4.2), (x1, 0.5, 0.30, 1.40, 4.2)], n=26, cols=_col_bala(x1 + 99)))
    # carretones (bogies) oscuros con ruedas
    for c in range(carros):
        xa = x_n0 - largo * c - 0.12 * c
        for xb in (xa - 0.7, xa - largo + 0.7) if c else (xa - 0.6, xa - largo + 0.7):
            ms.append(named(M3.box(1.2, 0.2, 0.86, (40, 42, 48), shadow=0, gloss=0.3).tf(t=(xb, 0.16, 0)), 'bajo', gloss=0.3))
            for dx in (-0.38, 0.38):
                for zz in (-0.36, 0.36):
                    w = M3.cyl(0.13, 0.06, (60, 62, 70), n=14, shadow=0, gloss=0.6).tf(rx=90, t=(xb + dx, 0.13, zz))
                    ms.append(named(w, 'rueda', gloss=0.6))
    # pantógrafo (barras) y aletas «orejas de gato»
    xp = x_n0 - largo * 0.55
    ms.append(named(M3.box(0.5, 0.05, 0.5, (90, 94, 104), shadow=0, gloss=0.6).tf(t=(xp, 1.43, 0)), 'panto'))
    if aletas > 0.01:
        a = 80 * clamp(aletas)
        for xa in (x_n0 - 1.2, x_n0 - 3.4):
            pl = M3.box(0.05, 0.42, 0.34, (236, 238, 244), shadow=0, gloss=0.5)
            for zs in (-0.2, 0.2):
                m = named(pl.tf(rz=(90 - a), t=(xa, 1.40, zs)), 'aleta', rim=0.9)
                m.glow = M.scale_c(ROJO, 0.25 * clamp(aletas))
                ms.append(m)
    return ms


def tren_mx(x=0.0, carros=2, largo=5.0):
    """Tren de pasajeros (no de alta velocidad): nariz corta, blanco con franja guinda. Genérico, sin logos."""
    secs = []
    x_n0 = x - 1.1
    for j in range(7):
        f = j / 6
        top = 1.42 - 0.35 * f ** 2.5
        hw = 0.52 * (1 - 0.18 * f ** 3)
        secs.append((x_n0 + 1.1 * f, hw, 0.32 + 0.1 * f ** 3, top, 5.0 - 1.4 * f))

    def cols(xx, y, z, cz, sy):
        if sy < -0.55:
            return (70, 74, 84)
        if xx > x_n0 + 0.3 and sy > 0.1 and cz > 0.2 and y > 0.95:
            return (16, 20, 28)
        if xx <= x_n0 and 0.88 < y < 1.12 and abs(cz) > 0.45:
            return (20, 24, 32)
        if 0.55 < y < 0.70 and abs(cz) > 0.3:
            return GUINDA
        return BLANCO
    ms = [loft([(x_n0 - largo, 0.52, 0.32, 1.42, 5.0), (x_n0, 0.52, 0.32, 1.42, 5.0)] + secs, n=26, cols=cols, cap1=False)]
    for c in range(1, carros):
        x1 = x_n0 - largo * c - 0.12 * c
        ms.append(loft([(x1 - largo, 0.52, 0.32, 1.42, 5.0), (x1, 0.52, 0.32, 1.42, 5.0)], n=26, cols=cols))
    for c in range(carros):
        xa = x_n0 - largo * c
        for xb in (xa - 0.8, xa - largo + 0.8):
            ms.append(named(M3.box(1.2, 0.22, 0.86, (40, 42, 48), shadow=0).tf(t=(xb, 0.17, 0)), 'bajo'))
    return ms


def maglev(x=0.0, flota=1.0, largo=5.0, xray=False):
    """Tren maglev genérico: nariz redonda, envuelve la viga en T; flota `flota`·(escala exagerada)."""
    dy = 0.04 + 0.14 * clamp(flota)
    x_n0 = x - 2.4
    secs = []
    for j in range(10):
        f = j / 9
        top = 0.62 + 0.86 * (1 - f ** 1.8) ** 0.8
        hw = 0.55 * (1 - 0.5 * f ** 2.6)
        secs.append((x_n0 + 2.4 * f, hw, 0.36 + 0.10 * f ** 2, max(top, 0.5), 3.4 - 1.0 * f))

    def cols(xx, y, z, cz, sy):
        if sy < -0.5:
            return (60, 64, 74)
        if xx > x_n0 + 0.6 and xx < x_n0 + 1.5 and sy > 0.35:
            return (16, 20, 28)
        if xx <= x_n0 and 0.98 < y < 1.18 and abs(cz) > 0.45:
            return (20, 24, 32)
        if 0.66 < y < 0.80 and abs(cz) > 0.3:
            return (60, 150, 230)
        return (226, 228, 234)
    ms = [P.tfk([loft([(x_n0 - largo, 0.55, 0.36, 1.48, 3.4), (x_n0, 0.55, 0.36, 1.48, 3.4)] + secs, n=26, cols=cols,
                       cap1=False)], t=(0, dy, 0))]
    ms = ms[0]
    # faldones que abrazan la viga (con imanes que brillan)
    for zs in (-1, 1):
        ms.append(named(M3.box(largo + 1.6, 0.70, 0.08, (52, 56, 66), shadow=0, gloss=0.4).tf(t=(x_n0 - largo / 2 + 0.6, -0.30 + dy, zs * 0.5)), 'falda'))
        mg = named(M3.box(largo + 1.4, 0.08, 0.14, (30, 40, 60), shadow=0, gloss=0.4).tf(t=(x_n0 - largo / 2 + 0.6, -0.20 + dy, zs * 0.38)), 'iman')
        mg.glow = M.scale_c(CYAN, 0.55 * clamp(flota))
        ms.append(mg)
    return ms


def viga(x0=-12, x1=12):
    """Viga guía del maglev (concreto) con su riel de acero arriba."""
    L = x1 - x0
    ms = [named(M3.box(L, 0.42, 0.62, CONCRETO, shadow=0, gloss=0.15).tf(t=((x0 + x1) / 2, -0.42, 0)), 'viga', gloss=0.15)]
    for zs in (-1, 1):
        ms.append(named(M3.box(L, 0.06, 0.12, (150, 154, 164), shadow=0, gloss=0.8).tf(t=((x0 + x1) / 2, 0.0, zs * 0.25)), 'riel', gloss=0.8))
    for j in range(int(L / 4) + 1):
        ms.append(named(M3.box(0.5, 1.6, 0.42, (110, 108, 104), shadow=0, gloss=0.1).tf(t=(x0 + 4 * j, -2.0, 0)), 'pilar', gloss=0.1))
    return ms


def camion(x=0.0, z=0.0, largo=4.4):
    """Autobús foráneo genérico (gris claro, ventanas oscuras, franja roja), sin logos. Frente hacia +x."""
    def cols(xx, y, zz, cz, sy):
        if sy < -0.6:
            return (40, 42, 48)
        if 0.98 < y < 1.38 and abs(cz) > 0.4:
            return (24, 28, 36)
        if 0.52 < y < 0.62 and abs(cz) > 0.4:
            return (200, 44, 44)
        return (196, 198, 204)
    ms = [P.tfk([loft([(x - largo, 0.48, 0.25, 1.55, 8.0), (x, 0.48, 0.25, 1.55, 8.0)], n=28, cols=cols, gloss=0.5, rim=0.7)],
                t=(0, 0, z))[0]]
    ms.append(named(M3.box(0.05, 0.62, 0.84, (20, 24, 32), shadow=0, gloss=0.95).tf(t=(x + 0.03, 0.82, z)), 'vidrio', gloss=0.95))
    for xw in (x - 0.75, x - largo + 0.9, x - largo + 1.5):
        for zz in (-0.47, 0.47):
            ms.append(named(M3.cyl(0.21, 0.12, (24, 24, 28), n=16, shadow=0, gloss=0.2).tf(rx=90, t=(xw, 0.21, z + zz)), 'rueda'))
    for zz in (-0.3, 0.3):
        f = named(M3.box(0.04, 0.08, 0.16, (255, 240, 200), shadow=0).tf(t=(x + 0.03, 0.42, z + zz)), 'faro')
        f.glow = (200, 190, 150)
        ms.append(f)
    return ms


def via(fr, x0=-14, x1=14, a=1.0, mov=0.0, cat=0.0, cat_col=(255, 236, 160), postes=True, soldado=True):
    """Vía en línea de luz: 2 rieles, durmientes que corren (mov), postes y catenaria (cat = brillo de la corriente)."""
    for zs in (-0.36, 0.36):
        line3(fr, [(x0, 0.03, zs), (x1, 0.03, zs)], col=(210, 214, 222), w=2.4, a=0.9 * a, glow=0.4)
    L = x1 - x0
    for j in range(int(L / 0.5) + 1):
        xx = x0 + ((j * 0.5 - mov) % L)
        line3(fr, [(xx, 0.0, -0.62), (xx, 0.0, 0.62)], col=WHITE, w=1.4, a=0.28 * a, glow=0.1)
    if postes:
        for j in range(int(L / 5) + 1):
            xx = x0 + ((j * 5 - mov) % L)
            line3(fr, [(xx, 0, -0.95), (xx, 2.3, -0.95), (xx, 2.3, 0.1)], col=(170, 174, 184), w=2.0, a=0.6 * a, glow=0.15)
        cc = M.mixc((150, 154, 164), cat_col, clamp(cat))
        line3(fr, [(x0, 2.05, 0), (x1, 2.05, 0)], col=cc, w=1.8 + 1.4 * cat, a=0.8 * a, glow=0.3 + 0.9 * cat)
        line3(fr, [(x0, 2.3, 0), (x1, 2.3, 0)], col=(140, 144, 154), w=1.2, a=0.5 * a, glow=0.1)


def rachas(fr, t, a=1.0, n=26, vel=18.0, y0=0.2, y1=2.4, x0=-14, x1=14, seed=4):
    """Rayas de velocidad (viento) que pasan."""
    rng = np.random.RandomState(seed)
    for j in range(n):
        y, z, L, ph = rng.uniform(y0, y1), rng.uniform(-2.5, 2.5), rng.uniform(0.8, 2.6), rng.rand()
        xx = x1 - ((t * vel + ph * (x1 - x0)) % (x1 - x0))
        line3(fr, [(xx, y, z), (xx + L, y, z)], col=(220, 230, 255), w=1.2, a=0.35 * a, glow=0.5)


def chispas(fr, t, x, a=1.0, n=14):
    rng = np.random.RandomState(int(t * 24) % 97)
    for j in range(n):
        p0 = np.array([x + rng.uniform(-0.6, 0.6), 0.08, rng.choice([-0.36, 0.36])])
        v = np.array([-rng.uniform(0.3, 1.0), rng.uniform(0.1, 0.5), rng.uniform(-0.2, 0.2)])
        line3(fr, [p0, p0 + v * 0.6], col=(255, 200, 120), w=1.6, a=a, glow=1.0)


# ------------------------------------------------------------------ mapa de México (línea de luz)
MX = [(32.53, -117.12), (32.6, -114.8), (31.3, -111.0), (31.33, -108.2), (31.78, -106.5), (30.6, -104.9),
      (29.56, -104.4), (29.0, -103.2), (29.8, -101.4), (28.7, -100.5), (27.5, -99.5), (26.1, -98.3), (25.9, -97.15),
      (24.0, -97.7), (22.2, -97.8), (21.0, -97.3), (19.2, -96.1), (18.15, -94.4), (18.5, -92.6), (18.65, -91.8),
      (19.85, -90.5), (20.9, -90.4), (21.35, -89.6), (21.55, -87.1), (21.1, -86.8), (20.2, -87.4), (18.5, -88.3),
      (17.82, -89.15), (17.82, -90.98), (16.08, -90.45), (15.25, -92.2), (14.53, -92.22), (15.7, -93.9),
      (16.2, -95.2), (15.85, -97.07), (16.85, -99.9), (17.95, -102.2), (19.05, -104.3), (20.6, -105.25),
      (21.5, -105.3), (23.2, -106.4), (25.6, -109.05), (27.9, -110.9), (28.8, -111.95), (30.6, -113.1),
      (31.3, -113.5), (31.8, -114.8), (31.0, -114.85), (28.95, -113.55), (27.3, -112.27), (26.0, -111.35),
      (24.15, -110.3), (22.9, -109.9), (23.45, -110.2), (24.6, -112.1), (26.7, -113.6), (27.85, -115.08),
      (28.0, -114.1), (30.06, -115.73), (31.85, -116.6), (32.53, -117.12)]
CIU = {'CDMX': (19.43, -99.13), 'Querétaro': (20.59, -100.39), 'Irapuato': (20.67, -101.35),
       'León': (21.12, -101.68), 'Guadalajara': (20.67, -103.35), 'Huehuetoca': (19.83, -99.2),
       'Tula': (20.05, -99.34), 'San Juan del Río': (20.39, -99.99)}
RUTA = ['CDMX', 'Querétaro', 'Irapuato', 'León', 'Guadalajara']
MK = 0.42                                  # unidades de escena por grado


def geo(lat, lon, y=0.0):
    return np.array([(lon + 102.0) * MK, y, -(lat - 23.0) * MK])


def ruta_pts(nombres, n=24):
    """Puntos de la ruta (suavizada) por las ciudades."""
    P0 = [geo(*CIU[c]) for c in nombres]
    out = []
    for a, b in zip(P0[:-1], P0[1:]):
        for j in range(n):
            out.append(a + (b - a) * j / n)
    out.append(P0[-1])
    return np.array(out)


def largo_pts(Pp):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pp, axis=0), axis=1))]
    return d / d[-1]


def en_ruta(Pp, f):
    d = largo_pts(Pp)
    f = clamp(f)
    i = min(len(Pp) - 2, int(np.searchsorted(d, f, side='right') - 1))
    k = (f - d[i]) / max(1e-9, d[i + 1] - d[i])
    return Pp[i] + (Pp[i + 1] - Pp[i]) * k


def mapa(fr, a=1.0, dibuja=1.0, glow=0.5):
    pts = [geo(la, lo) for la, lo in MX]
    line3(fr, pts, col=(200, 210, 225), w=2.2, a=0.85 * a, glow=glow, frac=dibuja)
    # retícula tenue de lat/lon
    for la in range(16, 34, 4):
        line3(fr, [geo(la, -118), geo(la, -86)], col=WHITE, w=1, a=0.07 * a, glow=0)
    for lo in range(-116, -86, 4):
        line3(fr, [geo(14, lo), geo(33, lo)], col=WHITE, w=1, a=0.07 * a, glow=0)


def ruta(fr, nombres, frac, col=CYAN, w=4.0, a=1.0, punteada=False, t=0.0):
    Pp = ruta_pts(nombres)
    if punteada:
        n = len(Pp)
        m = int(n * clamp(frac))
        for j in range(0, m - 1, 2):
            line3(fr, [Pp[j], Pp[j + 1]], col=col, w=w * 0.7, a=a * (0.55 + 0.45 * math.sin(t * 6 + j)), glow=0.6)
        return Pp
    line3(fr, Pp, col=col, w=w, a=a, glow=1.0, frac=frac)
    return Pp


def ciudad_ui(img, fx, cam, nombre, k=1.0, lado=1, col=WHITE, dy=0, size=None):
    """Punto y nombre de una ciudad (en la capa 1x)."""
    if k <= 0.01:
        return
    x, y, z = cam.p1(geo(*CIU[nombre]))
    if z < 0.2:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    r = 9 * P.resorte(k)
    d.ellipse((x - r, y - r, x + r, y + r), fill=M.scale_c(col, k))
    df.ellipse((x - 2 * r, y - 2 * r, x + 2 * r, y + 2 * r), fill=M.scale_c(col, 0.4 * k))
    sz = size or (28 if HZ else 30)
    texto(img, fx, x + lado * 22, y + dy, nombre.upper(), sz, col, k, f='mono', glow=0.25, anchor='lm' if lado > 0 else 'rm')


def marcador(img, fx, cam, p, txt, k=1.0, col=CYAN, size=None):
    """Ficha que va sobre la ruta (tren / camión)."""
    if k <= 0.01:
        return
    x, y, z = cam.p1(p)
    if z < 0.2:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    r = 15
    d.ellipse((x - r, y - r, x + r, y + r), fill=(8, 10, 14), outline=M.scale_c(col, k), width=4)
    d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=M.scale_c(col, k))
    df.ellipse((x - 30, y - 30, x + 30, y + 30), fill=M.scale_c(col, 0.35 * k))
    pill(img, fx, x, y - 48, txt, k, size=size or 22, border=col)


# ------------------------------------------------------------------ corte sísmico (2D)
def corte_sismico(img, fx, box, u, kP=0.0, kS=0.0, tren_x=0.72, sensores=True, k=1.0, corriente=1.0):
    """Corte de la tierra: superficie con la vía, epicentro en la costa, onda P (cian, rápida, débil) y S (roja, fuerte)."""
    if k <= 0.01:
        return
    x0, y0, x1, y1 = box
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    ys = y0 + (y1 - y0) * 0.30
    sh = 0.0
    if kS > 0.55:
        sh = 6 * math.sin(u * 60) * clamp((kS - 0.55) * 3)
    # capas
    for j in range(5):
        yy = ys + (y1 - ys) * (j + 1) / 6
        d.line([(x0, yy + sh * 0.3), (x1, yy - sh * 0.3)], fill=M.scale_c((90, 90, 100), 0.5 * k), width=2)
    d.line([(x0, ys + sh), (x1, ys - sh)], fill=M.scale_c(INK, k), width=4)
    df.line([(x0, ys + sh), (x1, ys - sh)], fill=M.scale_c(INK, 0.3 * k), width=8)
    ex, ey = x0 + (x1 - x0) * 0.12, ys + (y1 - ys) * 0.62
    # ondas (se emiten sin parar mientras dura la onda: la P rápida y delgada, la S lenta y gruesa)
    R = (x1 - x0) * 1.05
    from PIL import ImageChops
    cl = Image.new('L', img.size, 0)
    ImageDraw.Draw(cl).rectangle((x0, y0, x1, y1), fill=255)
    for kk, col, w, vel_, gap in ((kP, CYAN, 3, 900.0, 140.0), (kS, ROJO, 9, 380.0, 190.0)):
        if kk <= 0.01:
            continue
        mask = Image.new('L', img.size, 0)
        dm = ImageDraw.Draw(mask)
        frente = R * min(1.0, kk * 1.4)
        for j in range(12):
            rr = (u * vel_ + j * gap) % (R * 1.0)
            if rr < 6 or rr > frente:
                continue
            a = int(255 * (1 - rr / R) ** 0.6)
            dm.arc((ex - rr, ey - rr, ex + rr, ey + rr), 180, 360, fill=a, width=w)
        mask = ImageChops.multiply(mask, cl)
        img.paste(Image.new('RGB', img.size, M.scale_c(col, k)), (0, 0), mask)
        fx.paste(Image.new('RGB', img.size, M.scale_c(col, 0.6 * k)), (0, 0), mask.filter(ImageFilter.GaussianBlur(6)))
    # epicentro
    r = 12 + 4 * math.sin(u * 12)
    d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=M.scale_c(ROJO, k))
    df.ellipse((ex - 2.5 * r, ey - 2.5 * r, ex + 2.5 * r, ey + 2.5 * r), fill=M.scale_c(ROJO, 0.4 * k))
    texto(img, fx, ex, ey + 44, 'EPICENTRO', 22, MUTED, k, f='mono', glow=0)
    # sensores (costa y vía)
    if sensores:
        for sx in (x0 + (x1 - x0) * 0.22, x0 + (x1 - x0) * 0.55, x0 + (x1 - x0) * 0.86):
            on = kP * (x1 - x0) * 1.15 > math.hypot(sx - ex, ys - ey)
            c = CYAN if on else (150, 150, 160)
            d.rectangle((sx - 12, ys - 30, sx + 12, ys - 6), outline=M.scale_c(c, k), width=3)
            if on:
                df.ellipse((sx - 26, ys - 44, sx + 26, ys + 8), fill=M.scale_c(CYAN, 0.5 * k))
    # tren en la superficie
    tx = x0 + (x1 - x0) * tren_x
    d.rounded_rectangle((tx - 90, ys - 30, tx + 70, ys - 8), radius=10, fill=M.scale_c(BLANCO, k))
    d.polygon([(tx + 70, ys - 30), (tx + 120, ys - 8), (tx + 70, ys - 8)], fill=M.scale_c(BLANCO, k))
    d.line([(tx - 90, ys - 22), (tx + 90, ys - 22)], fill=M.scale_c(AZUL, k), width=4)
    # catenaria
    cc = M.mixc((90, 90, 100), AMARILLO, corriente)
    d.line([(x0 + (x1 - x0) * 0.45, ys - 64), (x1, ys - 64)], fill=M.scale_c(cc, k), width=3)
    if corriente > 0.05:
        df.line([(x0 + (x1 - x0) * 0.45, ys - 64), (x1, ys - 64)], fill=M.scale_c(AMARILLO, 0.6 * corriente * k), width=10)


def sismograma(img, fx, box, u, kP=0.0, kS=0.0, k=1.0, frac=1.0):
    """Tira de sismógrafo que se dibuja: ruido, onda P chica y onda S grande."""
    if k <= 0.01:
        return
    x0, y0, x1, y1 = box
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(over).rounded_rectangle(box, radius=22, fill=(12, 13, 17, int(220 * k)), outline=(255, 255, 255, int(60 * k)), width=2)
    img.paste(over, (0, 0), over)
    cy = (y0 + y1) / 2
    n = 260
    xs = np.linspace(x0 + 24, x1 - 24, n)
    m = int(n * clamp(frac))
    rng = np.random.RandomState(2)
    noise = rng.normal(size=n)
    pts = []
    for i in range(m):
        f = i / n
        amp = 2.0 + 14 * kP * math.exp(-((f - 0.35) / 0.08) ** 2) * (f > 0.27) + \
            62 * kS * math.exp(-((f - 0.72) / 0.12) ** 2) * (f > 0.6)
        pts.append((xs[i], cy + amp * math.sin(i * 1.7 + noise[i]) * (0.6 + 0.4 * abs(noise[i]))))
    if len(pts) > 1:
        d.line(pts, fill=M.scale_c(WHITE, k), width=3)
        df.line(pts, fill=M.scale_c(WHITE, 0.4 * k), width=6)
    if kP > 0.3:
        xp = xs[int(n * 0.30)]
        texto(img, fx, xp, y0 + 26, 'P', 26, CYAN, kP * k, f='mono', glow=0.5)
    if kS > 0.3:
        xp = xs[int(n * 0.66)]
        texto(img, fx, xp, y0 + 26, 'S', 26, ROJO, kS * k, f='mono', glow=0.5)


# ------------------------------------------------------------------ escenario 3D genérico del tren
def escena_tren(t, fi, u, claves, quien='bala', vel=1.0, frena=0.0, chisp=0.0, aletas=0.0, cat=0.0, xray=0.0,
                palabra=None, pal_t0=-0.3, pal_cy=0.36, pal_entrada='golpe', ui=None, floor='dots', tunel=0.0,
                extra=None, xpos=None, bokeh=1.0, cx=None, cy=None, beam=0.3, dof=0.0):
    """Tren sobre su vía con cámara de golpes. vel: velocidad aparente (durmientes y viento)."""
    fr = Frame(camara(u, claves, cx=cx, cy=cy))
    space(fr, t, floor=floor, floor_a=0.5, bokeh=bokeh, beam=beam, beam_x=OBJ_CX)
    if palabra:
        M.cristal(fr.base, fr.fx, palabra, u, t0=pal_t0, cy=pal_cy, entrada=pal_entrada)
    mov = t * 9.0 * vel
    via(fr, mov=mov, cat=cat)
    if vel > 0.3:
        rachas(fr, t, a=min(1.0, vel), vel=16 * vel)
    xp = 0.0 if xpos is None else xpos
    if quien == 'bala':
        ms = tren_bala(x=xp + 1.6, carros=2, aletas=aletas)
    elif quien == 'mx':
        ms = tren_mx(x=xp + 1.6, carros=2)
    else:
        ms = []
    if extra:
        ms = ms + extra(u)
    draw_objects(fr, ms, xray=xray, keep=('bajo', 'rueda'))
    if quien == 'bala':                                   # brazo del pantógrafo hasta la catenaria
        xp_ = xp + 1.6 - 3.2 - 5.0 * 0.55
        cc = M.mixc((150, 154, 164), (255, 236, 160), clamp(cat))
        line3(fr, [(xp_, 1.47, 0), (xp_ + 0.35, 1.78, 0), (xp_, 2.05, 0)], col=cc, w=2.4, a=0.95, glow=0.3 + 0.9 * cat)
        if cat > 0.3:
            dot3(fr, (xp_, 2.05, 0), r=6, col=(255, 236, 160), a=cat, glow=1.4)
    if chisp > 0.01:
        chispas(fr, t, xp + 1.6 - 3.2 - 0.6, a=chisp)
        chispas(fr, t + 0.5, xp + 1.6 - 3.2 - 4.3, a=chisp)
    if tunel > 0.01:
        _tunel(fr, tunel)
    if ui:
        fr.ui.append(ui)
    return finish(fr, fi, grain=0.025 if HZ else 0.04, dof=dof)


def _tunel(fr, k):
    """Boca de túnel (anillos) adelante del tren."""
    for j in range(6):
        xx = 4.2 + j * 0.5
        th = np.linspace(0, math.pi, 30)
        pts = [(xx, 0.0 + 2.1 * math.sin(a) * 1.0, 1.6 * math.cos(a)) for a in th]
        line3(fr, pts, col=(200, 205, 215), w=2.4 - j * 0.3, a=k * (1 - j * 0.14), glow=0.4)
