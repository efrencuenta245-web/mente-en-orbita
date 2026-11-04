"""Piezas reutilizables del estilo nuevo: celular con pantalla propia, transformar mallas sin perder su material,
pantallas de celular, almohada, pila de celular, termómetro, pastillas tachadas, etc."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motor2 as M
import demo_estilo as D
import norte as N
from motor2 import named, line3, dot3, pill, doodle_circle, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE

M3 = M.M3
S = M.SS
PH_Y = D.PH_Y
ATTRS = ('rim', 'gloss', 'glow', 'double', 'name', 'flat', 'alpha')


def tfk(meshes, s=1.0, rx=0.0, ry=0.0, rz=0.0, t=(0, 0, 0)):
    """Transforma mallas conservando nombre y material."""
    out = []
    for m in meshes:
        mm = m.tf(s=s, rx=rx, ry=ry, rz=rz, t=t)
        for a in ATTRS:
            if hasattr(m, a):
                setattr(mm, a, getattr(m, a))
        out.append(mm)
    return out


def pantalla(dibujar, t=0.0):
    """Pantalla de celular 420x900: barra de estado, lo que dibuje `dibujar(d, im)` y reflejo del cristal."""
    w, h = 420, 900
    im = Image.new('RGB', (w, h), (6, 7, 10))
    d = ImageDraw.Draw(im)
    d.text((34, 26), '9:41', font=M.font('sanss', 26), fill=(230, 230, 232))
    d.rounded_rectangle((w - 80, 32, w - 34, 52), radius=6, outline=(200, 200, 200), width=2)
    dibujar(d, im)
    d.rounded_rectangle((w / 2 - 70, h - 34, w / 2 + 70, h - 26), radius=4, fill=(200, 200, 204))
    gl = Image.new('L', (w, h), 0)
    ImageDraw.Draw(gl).polygon([(w * 0.55, 0), (w * 0.85, 0), (w * 0.15, h), (-w * 0.15, h)], fill=20)
    im.paste((255, 255, 255), (0, 0), gl)
    return im


def celular(scr, ry=0.0, rz=0.0, off=(0, 0, 0), acostado=False, interior=False):
    """Celular semirrealista con la pantalla `scr`. acostado=True: boca arriba sobre el piso (centro en off)."""
    ph = N.phone_with(scr)
    if not interior:
        ph = [m for m in ph if m.name != 'in']
    if acostado:
        ph = tfk(ph, t=(0, -PH_Y, 0))
        ph = tfk(ph, rx=-90)
        ph = tfk(ph, ry=ry, t=(off[0], 0.04 + off[1], off[2]))
        return ph
    return tfk(tfk(ph, t=(0, -PH_Y, 0)), rz=rz, ry=ry, t=(off[0], PH_Y + off[1], off[2]))


def almohada(x=0.0, z=0.0, col=(218, 214, 206)):
    m = M3.rbox(1.9, 0.34, 1.15, 0.16, col, n=6, shadow=0, gloss=0.15)
    m = named(m, 'almohada', rim=0.35, gloss=0.15)
    return tfk([m], t=(x, 0, z))


def pila(nivel, x=0.0, y=0.0, z=0.0, col_fill=(120, 225, 255), ancho=0.6, alto=1.0, glow=0.8, caliente=0.0):
    """Pila de celular de pie (cara grande hacia +z) con su nivel de carga que brilla."""
    body_col = M.mixc((52, 54, 60), (120, 40, 30), caliente)
    b = named(M3.rbox(ancho, alto, 0.09, 0.03, body_col, n=4, shadow=0, gloss=0.5), 'pila', rim=0.6, gloss=0.5)
    tab = named(M3.box(ancho * 0.35, 0.05, 0.05, (190, 160, 90), shadow=0, base=True, gloss=0.8).tf(t=(0, alto, 0)), 'tab')
    out = [b, tab]
    lv = clamp(nivel)
    if lv > 0.01:
        f = M3.box(ancho * 0.78, (alto - 0.12) * lv, 0.01, col_fill, shadow=0, base=True, gloss=0.2).tf(t=(0, 0.06, 0.05))
        f = named(f, 'fill', glow=M.scale_c(col_fill, glow), rim=0.1)
        f.flat = True
        out.append(f)
    return tfk(out, t=(x, y, z))


def pill_tachada(img, fx, x, y, txt, k, kx, t, size=34, col=(255, 236, 160)):
    """Pastilla que aparece (k) y luego se tacha con una X garabateada (kx)."""
    pill(img, fx, x, y, txt, eout(k), size=size, border=(200, 200, 210), dot=False)
    if kx > 0.01:
        d = ImageDraw.Draw(img)
        f = M.font('sanss', size)
        w = d.textlength(txt, font=f) + 70
        N.doodle_arrow_free(img, fx, x - w / 2, y + 6, x + w / 2, y - 6, t, clamp(kx), RED, seed=7)


def termometro(img, fx, x, y, h, nivel, txt, k=1.0, col=(255, 90, 70)):
    """Termómetro de línea que brilla (2D), nivel 0–1."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    c = M.scale_c(WHITE, 0.85 * k)
    d.rounded_rectangle((x - 22, y - h, x + 22, y), radius=22, outline=c, width=4)
    d.ellipse((x - 40, y - 10, x + 40, y + 70), outline=c, width=4)
    fill_h = (h - 30) * clamp(nivel)
    d.rounded_rectangle((x - 11, y - fill_h, x + 11, y + 20), radius=11, fill=M.scale_c(col, k))
    d.ellipse((x - 28, y + 2, x + 28, y + 58), fill=M.scale_c(col, k))
    df.rounded_rectangle((x - 16, y - fill_h, x + 16, y + 30), radius=16, fill=M.scale_c(col, 0.6 * k))
    df.ellipse((x - 34, y - 4, x + 34, y + 64), fill=M.scale_c(col, 0.6 * k))
    for i in range(5):
        yy = y - 30 - i * (h - 60) / 4
        d.line([(x + 26, yy), (x + 44, yy)], fill=c, width=3)
    d.text((x + 60, y - fill_h - 20), txt, font=M.font('sans', 56), fill=M.scale_c(col, k))


def ondas_calor(fr, t, cx, y0, y1, ancho, k=1.0, col=(255, 140, 80), n=5):
    """Ondas de calor que suben (line-art en 3D, plano z=0.1)."""
    if k <= 0.01:
        return
    for i in range(n):
        x0 = cx - ancho / 2 + ancho * (i + 0.5) / n
        ph = t * 3 + i
        P = [np.array([x0 + 0.05 * math.sin(ph + s * 9), y0 + (y1 - y0) * s, 0.12]) for s in np.linspace(0, 1, 30)]
        line3(fr, P, col=col, w=2.2, a=0.7 * k, glow=0.9 * k, frac=clamp((t * 0.8 + i * 0.2) % 1.0 * 1.5))


def kicker_c(img, txt, y, k, col=(150, 210, 230)):
    M.kicker(img, txt, y, k, col=col)
