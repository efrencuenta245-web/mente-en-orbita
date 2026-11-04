"""Piezas reutilizables del estilo nuevo: celular con pantalla propia, transformar mallas sin perder su material,
pantallas de celular, almohada, pila de celular, termómetro, pastillas tachadas, etc."""
import copy, math, os, sys
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


# ================================================================== movimiento rápido (4-nov-2026)
# Reglas en ESTILO.md §11. Todo es determinista (depende solo de t y u), así funciona con el loop.
def rebote(x, n=2.5, amort=6.0):
    """0→1 con rebote al final (objeto que cae y rebota). x en 0..1."""
    x = max(0.0, min(1.0, x))
    return 1 - math.exp(-amort * x) * abs(math.cos(n * math.pi * x))


def eout4(x):
    """Ease-out cuártico: arranca muy rápido y frena suave (movimientos de cámara «de golpe»)."""
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 4


def resorte(x, f=3.0, amort=5.0):
    """0→1 pasándose un poco y regresando (overshoot): para escalas y entradas con «pop»."""
    x = max(0.0, min(1.0, x))
    return 1 - math.exp(-amort * x) * math.cos(f * math.pi * x)


def cam_rapida(u, claves):
    """Recorre poses de cámara con saltos rápidos y pausas.
    claves = [(u0, pose), (u1, pose), …] con pose = dict de números (yaw, pitch, dist, fov, x, y…).
    Entre dos claves la transición dura solo el primer 35 % del tramo (eout4) y el resto se queda quieta,
    así se siente como cortes de cámara con movimiento, no como un paneo lento."""
    if u <= claves[0][0]:
        return dict(claves[0][1])
    for (ua, pa), (ub, pb) in zip(claves, claves[1:]):
        if u <= ub:
            k = eout4((u - ua) / max(1e-6, (ub - ua) * 0.35))
            return {key: pa[key] + (pb.get(key, pa[key]) - pa[key]) * k for key in pa}
    return dict(claves[-1][1])


def sacudida(t, k=1.0, t0=None, dur=0.35, amp=18):
    """Vibración de cámara (dx, dy en px) tras un impacto en t0; sin t0 es un temblor suave continuo."""
    if t0 is not None:
        if not (t0 <= t < t0 + dur):
            return 0.0, 0.0
        k = k * (1 - (t - t0) / dur) ** 2
    return (amp * k * math.sin(t * 91.0) * math.cos(t * 37.0),
            amp * k * math.sin(t * 73.0 + 1.3))


def despiece(meshes, k, centro=(0, 0, 0), fuerza=1.6, giro=0.0):
    """Vista explotada: separa cada pieza desde `centro` (k=0 armado, k=1 separado).
    Úsalo al revés (k de 1 a 0) para un inicio donde el objeto se arma solo."""
    out = []
    cx, cy, cz = centro
    for i, m in enumerate(meshes):
        v = np.asarray(m.V, float)
        c = v.mean(0)
        d = c - np.array([cx, cy, cz])
        n = np.linalg.norm(d)
        d = d / n if n > 1e-6 else np.array([math.sin(i * 2.4), math.cos(i * 1.7), 0.3])
        mm = copy.copy(m)
        vv = v + d * fuerza * k
        if giro:
            a = giro * k * (1 if i % 2 else -1)
            cA, sA = math.cos(a), math.sin(a)
            rel = vv - (c + d * fuerza * k)
            rel = rel @ np.array([[cA, 0, sA], [0, 1, 0], [-sA, 0, cA]]).T
            vv = rel + c + d * fuerza * k
        mm.V = vv
        out.append(mm)
    return out


def entrada(u, u0=0.0, dur=0.12, modo='cae'):
    """Factores de entrada de un objeto (para multiplicar posición/escala/giro).
    Devuelve dict(dy, escala, giro, alfa). modo: 'cae' (desde arriba con rebote), 'pop' (escala con resorte),
    'gira' (llega girando 1 vuelta), 'desliza' (entra de lado, usa dy como dx)."""
    k = max(0.0, min(1.0, (u - u0) / dur))
    if modo == 'cae':
        return dict(dy=-(1 - rebote(k)) * 3.0, escala=1.0, giro=0.0, alfa=min(1, k * 4))
    if modo == 'pop':
        return dict(dy=0.0, escala=max(0.0, resorte(k)), giro=0.0, alfa=min(1, k * 4))
    if modo == 'gira':
        return dict(dy=0.0, escala=eout4(k), giro=(1 - eout4(k)) * 2 * math.pi, alfa=min(1, k * 4))
    if modo == 'desliza':
        return dict(dy=(1 - eout4(k)) * 4.0, escala=1.0, giro=0.0, alfa=min(1, k * 4))
    return dict(dy=0.0, escala=1.0, giro=0.0, alfa=1.0)


def mover_img(img, dx, dy):
    """Desplaza un cuadro (np.uint8 HxWx3) dx, dy px rellenando con negro (para aplicar sacudida)."""
    dx, dy = int(dx), int(dy)
    if not dx and not dy:
        return img
    out = np.zeros_like(img)
    h, w = img.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = img[ys, xs]
    return out


def titulo_golpe(img, fx, lineas, y, k, size=80, col=WHITE, glow=0.4):
    """Título que se estrella: entra gigante (x2.2) y transparente y cae a su tamaño en ~0.15 s.
    Úsalo con k = seg(u, u0, u0 + 0.15) y pon sacudida + 'bass' en u0 + 0.15."""
    if k <= 0.01:
        return
    lay, h = M.text_layer(lineas, size)
    kk = eout4(k)
    s = 2.2 - 1.2 * kk
    w0, h0 = lay.size
    lay = lay.resize((max(1, int(w0 * s)), max(1, int(h0 * s))), Image.BILINEAR)
    a = lay.point(lambda v: int(v * min(1.0, k * 2.5)))
    x = int((M.W - lay.size[0]) / 2)
    yy = int(y + h0 / 2 - lay.size[1] / 2)
    img.paste(Image.new('RGB', lay.size, col), (x, yy), a)
    if glow:
        from PIL import ImageFilter
        fx.paste(Image.new('RGB', lay.size, M.scale_c(col, glow * (1.6 - 0.6 * kk))), (x, yy), a.filter(ImageFilter.GaussianBlur(7)))


def numero_golpe(img, fx, txt, y, k, size=330, col=WHITE, glow=0.6):
    """Número gigante que golpea la pantalla (inicio tipo 5): llega desde x3 con desenfoque y se clava."""
    if k <= 0.01:
        return
    from PIL import ImageFilter
    f = M.font('sans', size)
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    bx = d0.textbbox((0, 0), txt, font=f)
    w0, h0 = bx[2] - bx[0] + 40, bx[3] - bx[1] + 40
    lay = Image.new('L', (w0, h0), 0)
    ImageDraw.Draw(lay).text((20 - bx[0], 20 - bx[1]), txt, font=f, fill=255)
    kk = eout4(k)
    s = 3.0 - 2.0 * kk
    lay = lay.resize((max(1, int(w0 * s)), max(1, int(h0 * s))), Image.BILINEAR)
    if kk < 0.98:
        lay = lay.filter(ImageFilter.GaussianBlur(14 * (1 - kk)))
    a = lay.point(lambda v: int(v * min(1.0, k * 2.0)))
    x = int((M.W - lay.size[0]) / 2)
    yy = int(y - lay.size[1] / 2)
    img.paste(Image.new('RGB', lay.size, col), (x, yy), a)
    fx.paste(Image.new('RGB', lay.size, M.scale_c(col, glow)), (x, yy), a.filter(ImageFilter.GaussianBlur(10)))
