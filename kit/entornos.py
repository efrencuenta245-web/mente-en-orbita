"""Escenarios reales por escena (pedido de Efrén, 28-oct-2026): cada escena va en el lugar del que habla el guion
(gallina -> granja, huevo -> cocina, flor -> campo de cempasúchil, sangre -> dentro del cuerpo...). El espacio/estudio azul
solo se usa cuando el tema ES el espacio o para el escáner de rayos X.

Uso dentro de una escena (después de fijar fr.cam):
    import entornos as EN
    EN.env(fr, 'granja')            # fondo pintado + piso 3D con perspectiva (recibe las sombras de los objetos)
Nombres: cocina, granja, campo, cuerpo, ofrenda, tienda, laboratorio (y None = fondo del tema).
Para agregar uno nuevo: una función _bg_<nombre>(im, d) que pinta el fondo y una entrada en GROUND con el piso.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import motor3d as E

SW, SH = E.SW, E.SH
_ORIG_BG = E.bg_img
_CACHE = {}
_CUR = [None]


def lerpc(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


def vgrad(im, y0, y1, c0, c1):
    d = ImageDraw.Draw(im)
    for y in range(int(y0), int(y1)):
        d.line([(0, y), (SW, y)], fill=lerpc(c0, c1, (y - y0) / max(1, y1 - y0)))


def top_shade(im, frac=0.38, amax=0.66):
    """Oscurece la franja de arriba para que el titular blanco siempre se lea."""
    h = int(SH * frac)
    a = (np.linspace(1, 0, h) ** 1.3 * 255 * amax).astype(np.uint8)
    m = Image.fromarray(np.repeat(a[:, None], SW, 1), 'L')
    im.paste(Image.new('RGB', (SW, h), (6, 8, 16)), (0, 0), m)


# ---------------------------------------------------------------- fondos pintados
def _bg_cocina(im, d):
    vgrad(im, 0, SH, (236, 214, 178), (200, 168, 128))
    # ventana con luz de mañana
    x0, y0, x1, y1 = SW * 0.06, SH * 0.2, SW * 0.42, SH * 0.46
    d.rectangle((x0, y0, x1, y1), fill=(190, 222, 240))
    d.ellipse((x0 + 120, y0 + 60, x0 + 300, y0 + 240), fill=(255, 244, 210))
    for k in (0.5,):
        d.line([(x0 + (x1 - x0) * k, y0), (x0 + (x1 - x0) * k, y1)], fill=(120, 80, 50), width=18)
    d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=(120, 80, 50), width=18)
    d.rectangle((x0, y0, x1, y1), outline=(120, 80, 50), width=24)
    # repisa con jarros de barro
    d.rectangle((SW * 0.52, SH * 0.33, SW * 0.97, SH * 0.345), fill=(120, 78, 46))
    for i, x in enumerate(np.linspace(SW * 0.56, SW * 0.92, 5)):
        r = 70 + 18 * (i % 2)
        d.ellipse((x - r, SH * 0.33 - 2 * r, x + r, SH * 0.33), fill=(176, 90, 50))
        d.ellipse((x - r * 0.5, SH * 0.33 - 2 * r - 20, x + r * 0.5, SH * 0.33 - 2 * r + 20), fill=(150, 72, 40))
    # azulejo de talavera (franja)
    ty0, s = SH * 0.48, 96
    for j in range(5):
        for i in range(int(SW / s) + 1):
            x, y = i * s, ty0 + j * s
            d.rectangle((x, y, x + s - 4, y + s - 4), fill=(244, 240, 228))
            cx, cy = x + s / 2, y + s / 2
            col = (34, 74, 160) if (i + j) % 2 else (40, 120, 190)
            d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=col)
            for a in range(4):
                ang = a * math.pi / 2 + math.pi / 4
                d.ellipse((cx + 34 * math.cos(ang) - 9, cy + 34 * math.sin(ang) - 9, cx + 34 * math.cos(ang) + 9, cy + 34 * math.sin(ang) + 9),
                          fill=(230, 160, 40))


def _bg_granja(im, d):
    hz = SH * 0.5
    vgrad(im, 0, hz, (118, 170, 225), (214, 232, 244))
    d.ellipse((SW * 0.72, SH * 0.12, SW * 0.86, SH * 0.12 + SW * 0.14), fill=(255, 246, 214))
    rng = np.random.RandomState(4)
    for _ in range(5):
        cx, cy = rng.uniform(0, SW), rng.uniform(SH * 0.15, SH * 0.32)
        for k in range(5):
            r = rng.uniform(50, 110)
            d.ellipse((cx + k * 70 - r, cy - r * 0.6, cx + k * 70 + r, cy + r * 0.6), fill=(250, 250, 252))
    # cerros
    pts = [(0, hz)] + [(x, hz - 140 - 90 * math.sin(x / SW * 5) - 40 * math.sin(x / SW * 13)) for x in np.linspace(0, SW, 40)] + [(SW, hz)]
    d.polygon(pts, fill=(112, 150, 96))
    pts = [(0, hz)] + [(x, hz - 60 - 50 * math.sin(x / SW * 7 + 1)) for x in np.linspace(0, SW, 40)] + [(SW, hz)]
    d.polygon(pts, fill=(96, 136, 72))
    d.rectangle((0, hz, SW, SH), fill=(150, 120, 80))
    # granero
    bx, by, bw, bh = SW * 0.62, hz - 420, 560, 420
    d.rectangle((bx, by, bx + bw, hz), fill=(170, 40, 34))
    d.polygon([(bx - 30, by), (bx + bw / 2, by - 230), (bx + bw + 30, by)], fill=(120, 34, 30))
    d.rectangle((bx + bw / 2 - 110, hz - 260, bx + bw / 2 + 110, hz), fill=(240, 236, 226))
    d.line([(bx + bw / 2 - 110, hz - 260), (bx + bw / 2 + 110, hz)], fill=(170, 40, 34), width=16)
    d.line([(bx + bw / 2 + 110, hz - 260), (bx + bw / 2 - 110, hz)], fill=(170, 40, 34), width=16)
    # árboles
    for x in (SW * 0.12, SW * 0.3):
        d.rectangle((x - 18, hz - 220, x + 18, hz), fill=(96, 70, 44))
        d.ellipse((x - 140, hz - 460, x + 140, hz - 170), fill=(70, 120, 60))
    # cerca de madera
    fy = hz + 10
    for x in np.arange(0, SW, 150):
        d.rectangle((x, fy - 160, x + 22, fy + 20), fill=(150, 110, 70))
    for yy in (fy - 130, fy - 60):
        d.rectangle((0, yy, SW, yy + 18), fill=(166, 124, 80))


def _bg_campo(im, d):
    hz = SH * 0.5
    vgrad(im, 0, hz, (64, 70, 140), (250, 170, 100))
    d.ellipse((SW * 0.5 - 150, hz - 260, SW * 0.5 + 150, hz + 40), fill=(255, 214, 140))
    # volcanes a lo lejos (Popo e Izta)
    d.polygon([(SW * 0.05, hz), (SW * 0.3, hz - 360), (SW * 0.36, hz - 350), (SW * 0.62, hz)], fill=(110, 84, 120))
    d.polygon([(SW * 0.27, hz - 300), (SW * 0.3, hz - 360), (SW * 0.36, hz - 350), (SW * 0.39, hz - 290)], fill=(240, 230, 240))
    d.polygon([(SW * 0.55, hz), (SW * 0.78, hz - 220), (SW * 0.9, hz - 240), (SW * 1.05, hz)], fill=(124, 96, 128))
    d.rectangle((0, hz, SW, SH), fill=(70, 100, 40))
    # surcos de flores hacia el horizonte
    for k in range(40):
        y = hz + (k / 40) ** 2.2 * (SH - hz)
        h = 4 + 60 * (k / 40) ** 2
        d.rectangle((0, y, SW, y + h), fill=(240, 130, 20) if k % 2 else (74, 104, 44))


def _bg_cuerpo(im, d):
    vgrad(im, 0, SH, (70, 12, 20), (30, 4, 10))
    lay = Image.new('RGB', (SW // 4, SH // 4), (0, 0, 0))
    ld = ImageDraw.Draw(lay)
    rng = np.random.RandomState(11)
    for _ in range(60):
        x, y, r = rng.uniform(0, SW / 4), rng.uniform(0, SH / 4), rng.uniform(6, 30)
        ld.ellipse((x - r, y - r * 0.5, x + r, y + r * 0.5), fill=(int(rng.uniform(70, 150)), 14, 24))
    lay = lay.filter(ImageFilter.GaussianBlur(6)).resize((SW, SH), Image.BILINEAR)
    from PIL import ImageChops
    im.paste(ImageChops.add(im, lay))


def _bg_ofrenda(im, d):
    vgrad(im, 0, SH, (46, 22, 60), (20, 10, 26))
    lay = Image.new('RGB', (SW // 4, SH // 4), (0, 0, 0))
    ld = ImageDraw.Draw(lay)
    rng = np.random.RandomState(5)
    for _ in range(40):
        x, y, r = rng.uniform(0, SW / 4), rng.uniform(SH / 16, SH / 6), rng.uniform(5, 20)
        ld.ellipse((x - r, y - r, x + r, y + r), fill=(int(rng.uniform(80, 160)), int(rng.uniform(40, 90)), 10))
    lay = lay.filter(ImageFilter.GaussianBlur(7)).resize((SW, SH), Image.BILINEAR)
    from PIL import ImageChops
    im.paste(ImageChops.add(im, lay))


def _bg_tienda(im, d):
    vgrad(im, 0, SH, (60, 150, 140), (40, 110, 104))
    # repisas con cartones de huevo
    for j, y in enumerate((SH * 0.42, SH * 0.52, SH * 0.62)):
        d.rectangle((0, y, SW, y + 22), fill=(150, 104, 60))
        for i in range(14):
            x = 40 + i * 160
            d.rectangle((x, y - 90, x + 140, y), fill=(196, 170, 130))
            for a in range(3):
                d.ellipse((x + 10 + a * 44, y - 80, x + 46 + a * 44, y - 34), fill=(232, 210, 176) if (i + a) % 3 else (246, 238, 224))
    d.rectangle((SW * 0.25, SH * 0.30, SW * 0.75, SH * 0.36), fill=(250, 210, 40))
    f = E.font('xb', 110)
    d.text((SW * 0.5, SH * 0.33), 'HUEVO FRESCO', font=f, fill=(170, 30, 30), anchor='mm')


def _bg_laboratorio(im, d):
    im.paste(_ORIG_BG())


EXT = {'cocina': 4.5, 'granja': 7.0, 'campo': 7.0, 'ofrenda': 4.5, 'tienda': 4.5}

GROUND = {
    # tipo, color A, color B, línea, tamaño de tabla/losa
    'cocina': ('tablas', (150, 100, 62), (138, 90, 56), (112, 72, 44), 0.7),
    'granja': ('tierra', (150, 118, 76), (156, 124, 80), None, 0.8),
    'campo': ('pasto', (78, 108, 46), (84, 116, 50), None, 0.8),
    'cuerpo': (None,),
    'ofrenda': ('losas', (150, 74, 50), (136, 66, 46), (100, 50, 36), 1.0),
    'tienda': ('losas', (206, 200, 186), (190, 184, 170), (150, 146, 136), 1.0),
    'laboratorio': (None,),
}


def _backdrop(name):
    if name not in _CACHE:
        im = Image.new('RGB', (SW, SH), (0, 0, 0))
        d = ImageDraw.Draw(im)
        globals()['_bg_' + name](im, d)
        if name != 'laboratorio':
            top_shade(im)
        _CACHE[name] = im
    return _CACHE[name]


def _ground(im, cam, name):
    g = GROUND[name]
    if g[0] is None:
        return
    kind, ca, cb, cl, s = g
    d = ImageDraw.Draw(im)
    tx, tz = cam.target[0], cam.target[2]
    n = int(EXT.get(name, 6.0) / s)
    xs = np.arange(-n, n + 1) * s + round(tx / s) * s
    zs = np.arange(-n, n + 1) * s + round(tz / s) * s
    X, Z = np.meshgrid(xs, zs)
    P = np.stack([X.ravel(), np.zeros(X.size), Z.ravel()], 1)
    sp, zz = cam.proj(P)
    sp = sp.reshape(len(zs), len(xs), 2)
    zz = zz.reshape(len(zs), len(xs))
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            q = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            if min(zz[a, b] for a, b in q) < 0.25:
                continue
            pts = [tuple(sp[a, b]) for a, b in q]
            xi, zj = int(round(xs[i] / s)), int(round(zs[j] / s))
            if kind == 'tablas':
                col = ca if xi % 2 else cb
            elif kind == 'surcos':
                col = cb if xi % 3 == 0 else ca
            elif kind in ('tierra', 'pasto'):
                h = (xi * 73856093 ^ zj * 19349663) & 7
                col = lerpc(ca, cb, h / 7)
            else:
                col = ca if (xi + zj) % 2 else cb
            d.polygon(pts, fill=col, outline=cl if cl else col)
    if kind == 'pasto':  # flores de cempasúchil en el pasto
        rng = np.random.RandomState(6)
        st = rng.uniform(-n * s, n * s, (260, 2))
        A = np.stack([st[:, 0] + tx, np.full(len(st), 0.002), st[:, 1] + tz], 1)
        sa, za = cam.proj(A)
        for k in range(len(st)):
            if za[k] > 0.3:
                r = max(2, 40 / za[k])
                x, y = sa[k]
                d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=(240, 130, 20) if k % 3 else (255, 176, 36))
    if kind == 'tierra':  # paja
        rng = np.random.RandomState(2)
        st = rng.uniform(-n * s, n * s, (500, 2))
        st[:, 0] += tx
        st[:, 1] += tz
        A = np.stack([st[:, 0], np.full(len(st), 0.002), st[:, 1]], 1)
        B = A + np.stack([rng.uniform(-0.12, 0.12, len(st)), np.zeros(len(st)), rng.uniform(-0.12, 0.12, len(st))], 1)
        sa, za = cam.proj(A)
        sb, zb = cam.proj(B)
        for k in range(len(st)):
            if za[k] > 0.3 and zb[k] > 0.3:
                d.line([tuple(sa[k]), tuple(sb[k])], fill=(222, 196, 120), width=3)


def _bg_img():
    cur = _CUR[0]
    if cur is None:
        return _ORIG_BG()
    name, fr = cur
    cam = fr.cam
    im = _backdrop(name).copy()
    _ground(im, cam, name)
    return im


E.bg_img = _bg_img


def env(fr, name):
    """Pone la escena en un escenario real. Llamar después de fijar fr.cam."""
    _CUR[0] = (name, fr) if name else None
    if name and name != 'laboratorio':
        fr.floor = 0.0


def reset():
    _CUR[0] = None
