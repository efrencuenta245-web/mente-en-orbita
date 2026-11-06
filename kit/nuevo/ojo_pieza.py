"""Ojo semirrealista procedural (2D, RGBA) para el reel «Tu ojo se apaga» (6-nov-2026).
ojo_img(apert, ancho, rojo, mirada) → Image RGBA: ojo con piel alrededor que se funde con el negro, iris café con fibras,
pupila, brillos, venitas, pestañas. apert 1 = abierto, 0 = cerrado (el párpado de arriba baja hasta el de abajo)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

_C = {}


def _ruido(h, w, escala, seed):
    rng = np.random.RandomState(seed)
    a = rng.rand(max(2, h // escala + 2), max(2, w // escala + 2)).astype(np.float32)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def _base(W, H, seed=3):
    """Capas fijas (no dependen de la apertura): piel, esclera, iris."""
    key = ('base', W, H, seed)
    if key in _C:
        return _C[key]
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * 0.5
    s = W / 1000.0
    # piel: tono cálido con poros, más oscura hacia el ojo y que se funde a negro hacia afuera
    n1 = _ruido(H, W, int(6 * s) + 1, seed)
    n2 = _ruido(H, W, int(40 * s) + 1, seed + 1)
    piel = np.zeros((H, W, 3), np.float32)
    tono = np.array([188, 138, 112], np.float32)
    piel[:] = tono * (0.82 + 0.12 * n2[..., None] + 0.06 * n1[..., None])
    r = np.sqrt(((x - cx) / (W * 0.5)) ** 2 + ((y - cy) / (H * 0.5)) ** 2)
    alfa_piel = np.clip((1.0 - r) / 0.55, 0, 1) ** 1.7
    # cuenca: más oscura alrededor del ojo; bulto del globo bajo el párpado; luz arriba-izquierda
    d_ojo = np.sqrt(((x - cx) / (W * 0.42)) ** 2 + ((y - cy) / (H * 0.36)) ** 2)
    piel *= (0.62 + 0.38 * np.clip(d_ojo - 0.55, 0, 1) ** 0.6)[..., None] * 0.92
    bulto = np.exp(-(((x - cx * 0.96) / (W * 0.26)) ** 2 + ((y - (cy - H * 0.10)) / (H * 0.17)) ** 2))
    piel *= (1 + 0.32 * bulto)[..., None]
    luz = np.clip(1 - ((x - cx * 0.7) / W + (y - cy * 0.4) / H), 0.6, 1.25)
    piel *= luz[..., None]
    # esclera: blanco cálido, más oscura en las orillas, con venitas
    esc = np.zeros((H, W, 3), np.float32)
    re = np.sqrt(((x - cx) / (W * 0.43)) ** 2 + ((y - cy) / (H * 0.30)) ** 2)
    esc[:] = np.array([238, 232, 224], np.float32)
    esc *= (1.0 - 0.5 * np.clip(re, 0, 1) ** 1.8)[..., None]
    esc *= np.array([1.0, 0.985, 0.96], np.float32)
    venas = Image.new('L', (W, H), 0)
    dv = ImageDraw.Draw(venas)
    rng = np.random.RandomState(seed + 7)
    for i in range(26):
        lado = -1 if i % 2 else 1
        px, py = cx + lado * W * rng.uniform(0.25, 0.42), cy + H * rng.uniform(-0.12, 0.12)
        pts = [(px, py)]
        ang = math.atan2(cy - py, cx - px) + rng.uniform(-0.6, 0.6)
        for k in range(10):
            ang += rng.uniform(-0.5, 0.5)
            px += math.cos(ang) * 14 * s
            py += math.sin(ang) * 14 * s
            pts.append((px, py))
        dv.line(pts, fill=int(rng.uniform(90, 200)), width=max(1, int(rng.uniform(1.2, 3.2) * s)))
    venas = np.asarray(venas.filter(ImageFilter.GaussianBlur(1.0 * s)), np.float32) / 255.0
    # iris
    R = 0.155 * W
    ang = np.arctan2(y - cy, x - cx)
    rr = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / R
    fib = np.zeros_like(rr)
    rngf = np.random.RandomState(seed + 11)
    for f, a in ((37, 0.35), (91, 0.25), (173, 0.2), (311, 0.12)):
        ph = rngf.uniform(0, 6.28)
        fib += a * np.sin(ang * f + ph + 2.0 * np.sin(rr * 6 + ang * 3))
    fib = (fib - fib.min()) / (np.ptp(fib) + 1e-6)
    cerca = np.array([196, 150, 72], np.float32)     # avellana cerca de la pupila
    lejos = np.array([96, 60, 32], np.float32)       # café hacia la orilla
    k = np.clip((rr - 0.38) / 0.6, 0, 1)[..., None]
    iris = cerca * (1 - k) + lejos * k
    iris *= (0.62 + 0.55 * fib[..., None])
    corona = np.exp(-((rr - 0.5) / 0.08) ** 2)[..., None]
    iris += np.array([60, 40, 10], np.float32) * corona * 0.6
    limbo = np.clip((rr - 0.86) / 0.14, 0, 1)[..., None]
    iris *= (1 - 0.75 * limbo)
    a_iris = np.clip((1.0 - rr) / 0.02, 0, 1)
    pup = np.clip((0.37 - rr) / 0.02, 0, 1)
    _C[key] = dict(piel=piel, alfa_piel=alfa_piel, esc=esc, venas=venas, iris=iris, a_iris=a_iris, pup=pup,
                   x=x, y=y, cx=cx, cy=cy, R=R, s=s)
    return _C[key]


def ojo_img(apert=1.0, ancho=1000, rojo=0.0, seed=3, cache=True):
    """RGBA ancho x 0.64·ancho. apert 0..1 (se cuantiza a 1/40 para el caché)."""
    apert = round(max(0.0, min(1.0, apert)) * 40) / 40
    rojo = round(max(0.0, min(1.0, rojo)) * 10) / 10
    key = ('ojo', apert, ancho, rojo, seed)
    if cache and key in _C:
        return _C[key]
    W, H = int(ancho), int(ancho * 0.64)
    B = _base(W, H, seed)
    x, y, cx, cy, s = B['x'], B['y'], B['cx'], B['cy'], B['s']
    L = W * 0.40
    xn = np.clip((x - cx) / L, -1, 1)
    f = np.clip(1 - xn ** 2, 0, 1) ** 0.85
    sesgo = 0.06 * np.sin((xn + 0.3) * math.pi)          # el ojo es un poco asimétrico (almendra)
    lo = cy + H * (0.165 * f + sesgo * f * 0.3)
    up_abierto = cy - H * (0.29 * f - sesgo * f)
    up = lo - (lo - up_abierto) * apert
    dentro = ((y > up) & (y < lo) & (np.abs(x - cx) < L)).astype(np.float32)
    dentro = gaussian_filter(dentro, 1.2 * s)
    img = B['piel'].copy()
    # esclera + iris (el iris queda medio tapado por el párpado de arriba)
    ojo = B['esc'] * (1 - B['venas'][..., None] * (0.35 + 0.5 * rojo)) + \
        np.array([200, 40, 40], np.float32) * B['venas'][..., None] * (0.35 + 0.5 * rojo)
    ojo = ojo * (1 - B['a_iris'][..., None]) + B['iris'] * B['a_iris'][..., None]
    ojo = ojo * (1 - B['pup'][..., None]) + np.array([6, 5, 5], np.float32) * B['pup'][..., None]
    sombra = np.clip((y - up) / (0.11 * H), 0, 1) ** 0.7     # sombra del párpado y las pestañas sobre el ojo
    ojo *= (0.45 + 0.55 * sombra)[..., None]
    if rojo > 0:
        ojo = ojo * (1 - 0.25 * rojo) + np.array([70, 10, 10], np.float32) * 0.25 * rojo
    # brillos (ventana de luz arriba a la izquierda)
    R = B['R']
    for (dx, dy, rx, ry, a) in ((-0.32, -0.38, 0.18, 0.12, 1.0), (0.38, 0.30, 0.07, 0.05, 0.6)):
        g = np.exp(-(((x - (cx + dx * R)) / (rx * R)) ** 2 + ((y - (cy + dy * R)) / (ry * R)) ** 2) * 3)
        ojo = ojo + 255 * a * g[..., None] * 0.9
    img = img * (1 - dentro[..., None]) + ojo * dentro[..., None]
    # pliegue y borde de los párpados
    capa = Image.new('L', (W, H), 0)
    dc = ImageDraw.Draw(capa)
    xs = np.linspace(cx - L, cx + L, 80)
    fx_ = np.clip(1 - ((xs - cx) / L) ** 2, 0, 1) ** 0.85
    sx = 0.06 * np.sin(((xs - cx) / L + 0.3) * math.pi)
    lo_l = cy + H * (0.165 * fx_ + sx * fx_ * 0.3)
    upa = cy - H * (0.29 * fx_ - sx * fx_)
    up_l = lo_l - (lo_l - upa) * apert
    plieg = upa - H * (0.13 * fx_ + 0.02) - (1 - apert) * H * 0.05
    dc.line(list(zip(xs, plieg)), fill=150, width=int(5 * s))
    oscuro = np.asarray(capa.filter(ImageFilter.GaussianBlur(5 * s)), np.float32) / 255.0
    img *= (1 - 0.45 * oscuro)[..., None]
    # pestañas (de arriba, siguen al párpado) + línea del borde
    pest = Image.new('L', (W, H), 0)
    dp = ImageDraw.Draw(pest)
    dp.line(list(zip(xs, up_l)), fill=255, width=int(6 * s))
    dp.line(list(zip(xs, lo_l)), fill=120, width=int(3 * s))
    rng = np.random.RandomState(seed + 21)
    for i in range(70):
        u = (i + rng.uniform(-0.3, 0.3)) / 70
        xx = cx - L * 0.92 + 2 * L * 0.92 * u
        j = int(u * 79)
        y0 = up_l[j]
        lado = (xx - cx) / L
        largo = (34 + 22 * (1 - abs(lado))) * s * rng.uniform(0.8, 1.15)
        a0 = -math.pi / 2 + lado * 0.9 + rng.uniform(-0.12, 0.12)
        if apert < 0.25:
            a0 = math.pi / 2 + lado * 0.6
        pts = [(xx, y0)]
        for k in range(1, 6):
            t_ = k / 5
            aa = a0 + (0.5 * t_ * (1 if lado >= 0 else -1))
            pts.append((xx + math.cos(aa) * largo * t_, y0 + math.sin(aa) * largo * t_))
        dp.line(pts, fill=255, width=max(1, int((3.2 - 1.6 * 0) * s)))
    pm = np.asarray(pest.filter(ImageFilter.GaussianBlur(0.8 * s)), np.float32) / 255.0
    img = img * (1 - 0.92 * pm[..., None]) + np.array([18, 12, 10], np.float32) * 0.92 * pm[..., None]
    a = np.clip(B['alfa_piel'] + dentro * 0.0, 0, 1)
    out = np.dstack([np.clip(img, 0, 255), a * 255]).astype(np.uint8)
    im = Image.fromarray(out, 'RGBA')
    if cache:
        _C[key] = im
    return im


def pegar(img, im, cx, cy, ancho, alfa=1.0):
    """Pega el ojo centrado en (cx, cy) con `ancho` px; recorta antes de escalar (sirve para zooms enormes)."""
    W, H = img.size
    sw, sh = im.size
    esc = ancho / sw
    x0, y0 = cx - sw * esc / 2, cy - sh * esc / 2
    # región visible en coordenadas de la fuente
    sx0, sy0 = max(0, (0 - x0) / esc), max(0, (0 - y0) / esc)
    sx1, sy1 = min(sw, (W - x0) / esc), min(sh, (H - y0) / esc)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dx0, dy0 = int(x0 + sx0 * esc), int(y0 + sy0 * esc)
    dw, dh = max(1, int((sx1 - sx0) * esc)), max(1, int((sy1 - sy0) * esc))
    part = im.resize((dw, dh), Image.BICUBIC, box=(sx0, sy0, sx1, sy1))
    if alfa < 1:
        r, g, b, a = part.split()
        a = a.point(lambda v: int(v * alfa))
        part = Image.merge('RGBA', (r, g, b, a))
    img.paste(part, (dx0, dy0), part)


if __name__ == '__main__':
    tira = Image.new('RGB', (1000 * 3, 640 * 2), (0, 0, 0))
    for i, ap in enumerate((1.0, 0.7, 0.5, 0.25, 0.08, 0.0)):
        im = ojo_img(ap, 1000, rojo=0.8 if i == 2 else 0.0)
        tira.paste(im, ((i % 3) * 1000, (i // 3) * 640), im)
    tira.resize((1500, 640)).save('/home/claude/prueba_ojo.png')
    print('ok')
