"""Motor visual 2 de Mente en órbita (reset de noviembre 2026).

Espacio y transiciones al estilo de la referencia de @alyxianews (negro, line-art blanco que brilla,
bloom de 2 pasos, grano de película, viñeta, profundidad de campo, tipografía sans + serif itálica + mono)
con objetos semirrealistas como la referencia del metro (luz suave arriba, luz de borde, brillo especular,
rayos X de cristal con bordes que brillan). Ver ESTILO.md.

Todo trabaja a 1080x1920; la geometría se dibuja a 1.5x y se reduce (antialias).
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('GTA_FMT', 'v')
import motor3d as M3  # primitivas de malla (box, rbox, cyl, sphere, torus, extrude, merge, Mesh, rotm, paste_quad)

W, H = 1080, 1920
SS = 1.5
GW, GH = int(W * SS), int(H * SS)
FPS = 24

WHITE = (255, 255, 255)
INK = (236, 238, 242)
MUTED = (150, 152, 160)
CYAN = (120, 225, 255)       # único acento: rayos X, cotas y la caja del subtítulo
BLUE = (70, 140, 255)
WARM = (255, 214, 150)       # partículas cálidas (referencia del metro)
RED = (255, 72, 64)

FONT = {
    'sans': '/usr/share/fonts/opentype/inter/Inter-Bold.otf',
    'sansx': '/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf',
    'sansm': '/usr/share/fonts/opentype/inter/Inter-Medium.otf',
    'sanss': '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf',
    'serif': '/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf',
    'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
}
_FC = {}


def font(k, size):
    key = (k, int(size))
    if key not in _FC:
        f = ImageFont.truetype(FONT[k], int(size))
        if k == 'serif':
            try:
                f.set_variation_by_name('Medium Italic')
            except Exception:
                pass
        _FC[key] = f
    return _FC[key]


# ---------------------------------------------------------------- curvas
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / max(1e-9, b - a))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eout(x, p=3):
    x = clamp(x)
    return 1 - (1 - x) ** p


def ein(x, p=3):
    return clamp(x) ** p


def eexp_in(x):
    x = clamp(x)
    return 0 if x <= 0 else 2 ** (10 * x - 10)


def eback(x, s=1.6):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


def lerp(a, b, k):
    return a + (b - a) * k


def mixc(c1, c2, k):
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))


def scale_c(c, k):
    return tuple(int(clamp(v * k, 0, 255)) for v in c)


def norm(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-12)


# ---------------------------------------------------------------- cámara
class Cam:
    def __init__(self, target=(0, 0.8, 0), dist=6.0, yaw=0.0, pitch=10.0, fk=1.5, cx=0.5, cy=0.5, roll=0.0):
        self.target = np.array(target, float)
        y, p = math.radians(yaw), math.radians(pitch)
        off = np.array([math.cos(p) * math.sin(y), math.sin(p), math.cos(p) * math.cos(y)])
        self.pos = self.target + off * dist
        f = norm(self.target - self.pos)
        r = norm(np.cross(f, np.array([0, 1.0, 0])))
        u = np.cross(r, f)
        if roll:
            a = math.radians(roll)
            r, u = r * math.cos(a) + u * math.sin(a), u * math.cos(a) - r * math.sin(a)
        self.f, self.r, self.u = f, r, u
        self.F = fk * W * SS
        self.cx, self.cy = cx * GW, cy * GH

    def proj(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        d = P - self.pos
        x, y, z = d @ self.r, d @ self.u, d @ self.f
        zz = np.maximum(z, 1e-3)
        return np.stack([self.cx + self.F * x / zz, self.cy - self.F * y / zz], 1), z

    def p1(self, p):
        """Punto 3D -> coordenadas de la imagen final 1080x1920."""
        s, z = self.proj([p])
        return s[0, 0] / SS, s[0, 1] / SS, z[0]


def cam_path(t, keys):
    """keys: [(t, dict de parámetros)] -> Cam interpolada con ease."""
    if t <= keys[0][0]:
        return Cam(**keys[0][1])
    for (ta, a), (tb, b) in zip(keys[:-1], keys[1:]):
        if ta <= t <= tb:
            k = ease((t - ta) / max(1e-6, tb - ta))
            d = {}
            for key in a:
                va, vb = a[key], b.get(key, a[key])
                d[key] = tuple(lerp(x, y, k) for x, y in zip(va, vb)) if isinstance(va, (tuple, list)) else lerp(va, vb, k)
            return Cam(**d)
    return Cam(**keys[-1][1])


# ---------------------------------------------------------------- lienzo por capas
class Frame:
    """base: lo que se ve (RGB). fx: capa emisiva (lo que brilla, se suma y alimenta el bloom).
    Ambas a resolución de geometría (GW x GH) hasta finish()."""

    def __init__(self, cam=None):
        self.cam = cam or Cam()
        self.base = Image.new('RGB', (GW, GH), (0, 0, 0))
        self.fx = Image.new('RGB', (GW, GH), (0, 0, 0))
        self.db = ImageDraw.Draw(self.base)
        self.df = ImageDraw.Draw(self.fx)
        self.ui = []  # funciones (img1x, fx1x) después de reducir


# ---------------------------------------------------------------- espacio (fondo)
_CACHE = {}


def _bg_base():
    if 'bg' not in _CACHE:
        h, w = GH // 4, GW // 4
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((x - w / 2) / (w * 0.62)) ** 2 + ((y - h * 0.46) / (h * 0.55)) ** 2)
        spot = np.clip(1 - r, 0, 1) ** 1.8
        img = np.zeros((h, w, 3), np.float32) + 3.0
        img += np.array([20, 19, 18], np.float32) * spot[..., None]
        _CACHE['bg'] = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((GW, GH), Image.BILINEAR)
    return _CACHE['bg']


def space(fr, t, floor='dots', floor_a=1.0, bokeh=1.0, beam=0.0, beam_x=0.5):
    """Espacio negro con foco suave, piso en perspectiva (puntos o líneas), partículas desenfocadas y haz de luz."""
    fr.base.paste(_bg_base())
    cam = fr.cam
    if floor_a > 0 and floor:
        _floor(fr, cam, floor, floor_a)
    if bokeh > 0:
        _bokeh(fr, t, bokeh)
    if beam > 0:
        _beam(fr, beam, beam_x)


def _floor(fr, cam, style, a):
    tx, tz = cam.target[0], cam.target[2]
    R = 7.5
    if style == 'dots':
        g = 0.3
        ix = np.arange(math.floor((tx - R) / g), math.ceil((tx + R) / g) + 1) * g
        iz = np.arange(math.floor((tz - R) / g), math.ceil((tz + R) / g) + 1) * g
        X, Z = np.meshgrid(ix, iz)
        X, Z = X.ravel(), Z.ravel()
        dd = np.hypot(X - tx, Z - tz)
        keep = dd < R
        X, Z, dd = X[keep], Z[keep], dd[keep]
        s, z = cam.proj(np.stack([X, np.zeros_like(X), Z], 1))
        ok = (z > 0.3) & (s[:, 0] > -10) & (s[:, 0] < GW + 10) & (s[:, 1] > -10) & (s[:, 1] < GH + 10)
        al = (1 - (dd / R) ** 2) * a
        rad = np.clip(0.016 * cam.F / np.maximum(z, 0.3), 0.7, 5)
        for (x, y), aa, rr, o in zip(s, al, rad, ok):
            if o and aa > 0.03:
                v = int(16 + 110 * aa)
                fr.db.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(v, v, v))
    else:  # 'lines': rayas horizontales en perspectiva (como el piso de los audífonos de la referencia)
        for k in range(60):
            z = tz - R + k * 0.25
            xs = np.linspace(tx - R, tx + R, 30)
            P = np.stack([xs, np.zeros_like(xs), np.full_like(xs, z)], 1)
            s, zz = cam.proj(P)
            if (zz < 0.3).any():
                continue
            dd = abs(z - tz) / R
            v = int(14 + 90 * (1 - dd ** 2) * a)
            fr.db.line([tuple(p) for p in s], fill=(v, v, v), width=max(1, int(1.2 * SS)))


def _bokeh(fr, t, a):
    if 'bok' not in _CACHE:
        rng = np.random.RandomState(11)
        _CACHE['bok'] = [(rng.rand(), rng.rand(), rng.uniform(6, 34), rng.uniform(0.25, 1.0), rng.uniform(0.004, 0.02),
                          rng.rand() < 0.45) for _ in range(46)]
    lay = Image.new('RGB', (GW // 4, GH // 4), (0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for x, y, r, b, v, warm in _CACHE['bok']:
        yy = ((y - v * t) % 1.0) * GH / 4
        xx = (x + 0.01 * math.sin(t * 0.6 + r)) * GW / 4
        c = WARM if warm else (220, 225, 235)
        ld.ellipse((xx - r / 2, yy - r / 2, xx + r / 2, yy + r / 2), fill=scale_c(c, 0.16 * b * a))
    lay = lay.filter(ImageFilter.GaussianBlur(3)).resize((GW, GH), Image.BILINEAR)
    fr.fx.paste(Image.fromarray(np.maximum(np.asarray(fr.fx), np.asarray(lay))))


def _beam(fr, a, bx):
    """Haz de luz volumétrico que baja desde arriba (foco de escenario)."""
    lay = Image.new('L', (GW // 4, GH // 4), 0)
    ld = ImageDraw.Draw(lay)
    w4, h4 = GW // 4, GH // 4
    cx = bx * w4
    ld.polygon([(cx - w4 * 0.04, -10), (cx + w4 * 0.04, -10), (cx + w4 * 0.36, h4 * 0.78), (cx - w4 * 0.36, h4 * 0.78)], fill=int(60 * a))
    lay = lay.filter(ImageFilter.GaussianBlur(14)).resize((GW, GH), Image.BILINEAR)
    arr = np.asarray(lay, np.float32)[..., None] * np.array([1.0, 0.98, 0.94], np.float32)
    fr.fx.paste(Image.fromarray(np.clip(np.asarray(fr.fx, np.float32) + arr, 0, 255).astype(np.uint8)))


# ---------------------------------------------------------------- objetos semirrealistas
KEY = norm([-0.55, 0.9, 0.65])
FILL = norm([0.6, 0.15, 0.8])
RIMD = norm([0.4, 0.5, -1.0])


def shade(col, n, vd, gloss=0.3, rim=0.55, amb=0.30):
    col = np.array(col[:3], float)
    c = col * (amb + 0.80 * max(0.0, float(n @ KEY)) + 0.16 * max(0.0, float(n @ FILL)))
    h = norm(KEY - vd)
    s = max(0.0, float(n @ h)) ** (10 + 60 * gloss) * gloss * 1.2
    c = c + (255 - c) * s
    facing = abs(float(n @ (-vd)))
    fr_ = (1 - facing) ** 3 * rim * (0.6 + 0.4 * max(0.0, float(n @ RIMD)))
    c = c + (np.array([230, 236, 255]) - c) * min(1.0, fr_)
    if n[1] < -0.6:
        c *= 0.75  # oclusión: caras hacia abajo
    return tuple(int(clamp(v, 0, 255)) for v in c)


def _faces(cam, meshes):
    items = []
    for mi, m in enumerate(meshes):
        if getattr(m, 'alpha', 1.0) <= 0.01:
            continue
        S, Z = cam.proj(m.V)
        V = m.V
        for fi, f in enumerate(m.F):
            zf = Z[list(f)]
            if (zf < 0.15).any():
                continue
            if len(f) > 4:
                Q = V[list(f)]
                Qn = np.roll(Q, -1, 0)
                n = np.array([np.sum((Q[:, 1] - Qn[:, 1]) * (Q[:, 2] + Qn[:, 2])),
                              np.sum((Q[:, 2] - Qn[:, 2]) * (Q[:, 0] + Qn[:, 0])),
                              np.sum((Q[:, 0] - Qn[:, 0]) * (Q[:, 1] + Qn[:, 1]))])
            else:
                n = np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]])
                if np.linalg.norm(n) < 1e-12 and len(f) > 3:
                    n = np.cross(V[f[2]] - V[f[0]], V[f[3]] - V[f[0]])
            nn = np.linalg.norm(n)
            if nn < 1e-12:
                continue
            n = n / nn
            vd = norm(V[list(f)].mean(0) - cam.pos)
            if n @ vd > 0:
                if not m.double:
                    continue
                n = -n
            items.append((float(zf.mean()), mi, fi, n, vd, S[list(f)]))
    items.sort(key=lambda it: -it[0])
    return items


def draw_objects(fr, meshes, xray=0.0, xray_col=CYAN, keep=()):
    """Dibuja mallas semirrealistas. xray (0-1) vuelve cristal las mallas que no estén en keep (nombres),
    con bordes que brillan en la capa emisiva."""
    cam = fr.cam
    solid = [m for m in meshes if xray <= 0 or getattr(m, 'name', '') in keep]
    glass = [m for m in meshes if xray > 0 and getattr(m, 'name', '') not in keep]
    if xray > 0 and xray < 1:  # mientras entra el rayo X, el cuerpo se dibuja normal y se mezcla
        solid_all = meshes
    else:
        solid_all = solid
    for z, mi, fi, n, vd, S in _faces(cam, solid_all):
        m = solid_all[mi]
        c = (tuple(int(v) for v in m.C[fi][:3]) if m.flat else
             shade(m.C[fi], n, vd, getattr(m, 'gloss', 0.3), getattr(m, 'rim', 0.55)))
        pts = [tuple(p) for p in S]
        fr.db.polygon(pts, fill=c, outline=c)
        for (dfi, img, order) in m.decals:
            if dfi == fi:
                M3.paste_quad(fr.base, [pts[k] for k in order], img, 1.0)
        if getattr(m, 'glow', None) is not None:
            fr.df.polygon(pts, fill=m.glow)
    if xray > 0:
        k = ease(xray)
        if xray < 1:
            # sobre lo dibujado: oscurece (el cuerpo "se vuelve transparente") y vuelve a dibujar lo interior
            dark = Image.new('RGB', (GW, GH), (2, 3, 6))
            mask = Image.new('L', (GW, GH), 0)
            md = ImageDraw.Draw(mask)
            for z, mi, fi, n, vd, S in _faces(cam, glass):
                md.polygon([tuple(p) for p in S], fill=int(235 * k))
            fr.base.paste(dark, (0, 0), mask)
            for z, mi, fi, n, vd, S in _faces(cam, solid):
                m = solid[mi]
                c = shade(m.C[fi], n, vd, getattr(m, 'gloss', 0.3), getattr(m, 'rim', 0.55))
                fr.db.polygon([tuple(p) for p in S], fill=c, outline=c)
        else:
            mask = Image.new('L', (GW, GH), 0)
            md = ImageDraw.Draw(mask)
            for z, mi, fi, n, vd, S in _faces(cam, glass):
                md.polygon([tuple(p) for p in S], fill=235)
            fr.base.paste(Image.new('RGB', (GW, GH), (2, 3, 6)), (0, 0), mask)
            for z, mi, fi, n, vd, S in _faces(cam, solid):
                m = solid[mi]
                c = shade(m.C[fi], n, vd, getattr(m, 'gloss', 0.3), getattr(m, 'rim', 0.55))
                fr.db.polygon([tuple(p) for p in S], fill=c, outline=c)
        # cristal: tinte leve + bordes que brillan
        tint = Image.new('L', (GW, GH), 0)
        td = ImageDraw.Draw(tint)
        for z, mi, fi, n, vd, S in _faces(cam, glass):
            pts = [tuple(p) for p in S]
            facing = abs(float(n @ (-vd)))
            td.polygon(pts, fill=int(28 * k * (1.2 - facing)))
            fr.df.line(pts + [pts[0]], fill=scale_c(xray_col, 0.8 * k), width=max(1, int(2.0 * SS)))
            fr.db.line(pts + [pts[0]], fill=scale_c(xray_col, 0.35 * k), width=max(1, int(1.2 * SS)))
        fr.base.paste(Image.new('RGB', (GW, GH), xray_col), (0, 0), tint)


def named(m, name, **kw):
    m.name = name
    for k, v in kw.items():
        setattr(m, k, v)
    return m


# ---------------------------------------------------------------- line-art (brilla)
def line3(fr, pts, col=WHITE, w=2.0, a=1.0, glow=0.6, frac=1.0):
    P = np.asarray(pts, float)
    if frac < 1:
        n = max(2, int(len(P) * clamp(frac)))
        P = P[:n]
    s, z = fr.cam.proj(P)
    pts2 = [tuple(p) for p, zz in zip(s, z) if zz > 0.2]
    if len(pts2) < 2:
        return
    fr.db.line(pts2, fill=scale_c(col, a), width=max(1, int(w * SS)), joint='curve')
    if glow:
        fr.df.line(pts2, fill=scale_c(col, a * glow), width=max(1, int(w * SS * 1.6)), joint='curve')


def dot3(fr, p, r=5, col=WHITE, a=1.0, glow=0.8):
    s, z = fr.cam.proj([p])
    if z[0] < 0.2:
        return
    x, y = s[0]
    rr = r * SS
    fr.db.ellipse((x - rr, y - rr, x + rr, y + rr), fill=scale_c(col, a))
    if glow:
        rg = rr * 2.2
        fr.df.ellipse((x - rg, y - rg, x + rg, y + rg), fill=scale_c(col, a * glow * 0.6))


# ---------------------------------------------------------------- acabado (bloom, grano, viñeta)
_GRAIN = []


def _grain(i):
    if not _GRAIN:
        rng = np.random.RandomState(5)
        for _ in range(6):
            _GRAIN.append(((rng.rand(H // 2, W // 2).astype(np.float32) - 0.5)))
    g = _GRAIN[i % len(_GRAIN)]
    return np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]


def _vig():
    if 'vig' not in _CACHE:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W / 2) / (W * 0.72)) ** 2 + ((y - H * 0.47) / (H * 0.62)) ** 2)
        _CACHE['vig'] = (1 - 0.55 * np.clip(r - 0.35, 0, 1) ** 1.4)[..., None]
    return _CACHE['vig']


def finish(fr, fi=0, bloom=1.0, grain=0.045, flash=0.0, dof=0.0):
    """Reduce a 1080x1920 y aplica capa emisiva + bloom de 2 pasos + viñeta + grano. Devuelve np.uint8 HxWx3."""
    base = fr.base.resize((W, H), Image.LANCZOS)
    fx = fr.fx.resize((W, H), Image.BILINEAR)
    if dof > 0:
        base = base.filter(ImageFilter.GaussianBlur(dof))
    for fn in fr.ui:
        fn(base, fx)
    b = np.asarray(base, np.float32) / 255.0
    e = np.asarray(fx, np.float32) / 255.0
    img = b + e * 0.55
    q = (W // 4, H // 4)
    bright = np.clip(img - 0.62, 0, None) * 1.4 + e * 0.9
    sm = np.asarray(Image.fromarray(np.clip(bright * 255, 0, 255).astype(np.uint8)).resize(q, Image.BILINEAR), np.float32) / 255
    b1 = gaussian_filter(sm, (2.0, 2.0, 0))
    b2 = gaussian_filter(sm, (11.0, 11.0, 0))
    bl = b1 * 0.55 + b2 * 0.75
    bl = np.asarray(Image.fromarray(np.clip(bl * 255, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
    img = img + bl * bloom
    img = img * _vig()
    img = img / (1 + 0.12 * img)  # rolloff suave de altas luces
    img = img + _grain(fi) * grain
    if flash > 0:
        img = img + (1.15 - img) * clamp(flash)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


# ---------------------------------------------------------------- transiciones (sobre cuadros terminados)
def _pil(a):
    return Image.fromarray(a) if isinstance(a, np.ndarray) else a


def scale_about(img, s, cx=0.5, cy=0.5):
    """Zoom digital alrededor de (cx, cy) normalizados."""
    im = _pil(img)
    if abs(s - 1) < 1e-3:
        return np.asarray(im)
    if s > 1:
        w, h = W / s, H / s
        x0 = clamp(cx * W - w / 2, 0, W - w)
        y0 = clamp(cy * H - h / 2, 0, H - h)
        return np.asarray(im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)))
    small = im.resize((max(1, int(W * s)), max(1, int(H * s))), Image.BICUBIC)
    out = Image.new('RGB', (W, H), (0, 0, 0))
    out.paste(small, (int(cx * W - small.width / 2), int(cy * H - small.height / 2)))
    return np.asarray(out)


def radial_blur(img, amount, cx=0.5, cy=0.5, n=7):
    if amount <= 0.002:
        return np.asarray(_pil(img))
    acc = np.zeros((H, W, 3), np.float32)
    for i in range(n):
        acc += scale_about(img, 1 + amount * i / (n - 1), cx, cy)
    return (acc / n).astype(np.uint8)


def dir_blur(img, dx, dy, n=7):
    a = np.asarray(_pil(img)).astype(np.float32)
    if abs(dx) + abs(dy) < 1:
        return a.astype(np.uint8)
    acc = np.zeros_like(a)
    for i in range(n):
        k = i / (n - 1) - 0.5
        acc += np.roll(np.roll(a, int(dy * k), 0), int(dx * k), 1)
    return (acc / n).astype(np.uint8)


def tr_zoom_through(A, B, k, cx=0.5, cy=0.5):
    """La cámara atraviesa la escena A (zoom + desenfoque radial) y aterriza en B. 0.35 s."""
    if k < 0.5:
        u = eexp_in(k / 0.5) if k > 0.02 else 0
        s = 1 + 2.6 * ein(k / 0.5, 2)
        x = radial_blur(scale_about(A, s, cx, cy), 0.25 * (k / 0.5), cx, cy)
        return (x.astype(np.float32) * (1 - 0.35 * u) + 255 * 0.12 * u).clip(0, 255).astype(np.uint8)
    u = (k - 0.5) / 0.5
    s = 0.72 + 0.28 * eout(u)
    x = radial_blur(scale_about(B, s), 0.22 * (1 - u))
    return (x.astype(np.float32) + 255 * 0.12 * (1 - u)).clip(0, 255).astype(np.uint8)


def tr_flash(A, B, k):
    """Sobreexposición: todo se quema a blanco y se revela B. 0.4 s."""
    if k < 0.45:
        u = ein(k / 0.45, 2)
        a = np.asarray(_pil(A)).astype(np.float32)
        return (a + (255 - a) * u).clip(0, 255).astype(np.uint8)
    u = eout((k - 0.45) / 0.55, 2)
    b = np.asarray(_pil(B)).astype(np.float32)
    return (b + (255 - b) * (1 - u)).clip(0, 255).astype(np.uint8)


def tr_whip(A, B, k, dx=1):
    """Barrido rápido con desenfoque de movimiento. 0.2 s."""
    if k < 0.5:
        u = ein(k / 0.5, 2)
        return dir_blur(np.roll(np.asarray(_pil(A)), int(-dx * u * W * 0.5), 1), 260 * u, 0)
    u = eout((k - 0.5) / 0.5, 2)
    return dir_blur(np.roll(np.asarray(_pil(B)), int(dx * (1 - u) * W * 0.5), 1), 260 * (1 - u), 0)


def tr_wipe_v(A, B, k):
    """Cortinilla vertical con línea de luz. 0.3 s."""
    a = np.asarray(_pil(A)).copy()
    b = np.asarray(_pil(B))
    y = int(eout(k) * H)
    a[:y] = b[:y]
    a = a.astype(np.float32)
    lo, hi = max(0, y - 6), min(H, y + 6)
    a[lo:hi] = a[lo:hi] * 0.3 + 255 * 0.7
    return a.clip(0, 255).astype(np.uint8)


def push_in(img, k, cx=0.5, cy=0.5, zmax=2.4):
    """Acercamiento exponencial con desenfoque (para entrar a un detalle). 0.5 s."""
    s = 1 + (zmax - 1) * eexp_in(k)
    return radial_blur(scale_about(img, s, cx, cy), 0.3 * eexp_in(k), cx, cy)


# ---------------------------------------------------------------- texto
def text_layer(lines, size, gap=1.12, align='c', width=W):
    """lines: [(texto, estilo)] estilo en FONT. Devuelve imagen L con el texto y su alto."""
    fs = [font(st, size * (1.08 if st == 'serif' else 1.0)) for _, st in lines]
    hs = [f.getbbox('Ág')[3] for f in fs]
    tot = int(sum(hs) * gap) + 20
    lay = Image.new('L', (width, tot), 0)
    d = ImageDraw.Draw(lay)
    y = 0
    for (txt, st), f, h in zip(lines, fs, hs):
        w = d.textlength(txt, font=f)
        x = (width - w) / 2 if align == 'c' else 70
        d.text((x, y), txt, font=f, fill=255)
        y += h * gap
    return lay, tot


def title(img, fx, lines, y, k, size=86, col=WHITE, glow=0.35):
    """Título de 2 líneas (sans + serif itálica). Entra con desenfoque y subida."""
    if k <= 0.01:
        return
    lay, h = text_layer(lines, size)
    kk = eout(k, 3)
    if kk < 0.999:
        lay = lay.filter(ImageFilter.GaussianBlur(10 * (1 - kk)))
    yy = int(y + 34 * (1 - kk))
    a = lay.point(lambda v: int(v * clamp(k * 1.4)))
    img.paste(Image.new('RGB', lay.size, col), (0, yy), a)
    if glow:
        fx.paste(Image.new('RGB', lay.size, scale_c(col, glow)), (0, yy), a.filter(ImageFilter.GaussianBlur(6)))


def kicker(img, txt, y, k=1.0, size=26, col=MUTED, spacing=6):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    f = font('mono', size)
    widths = [d.textlength(ch, font=f) for ch in txt]
    tw = sum(widths) + spacing * (len(txt) - 1)
    x = (W - tw) / 2
    c = scale_c(col, clamp(k))
    for ch, w in zip(txt, widths):
        d.text((x, y), ch, font=f, fill=c)
        x += w + spacing


def word_caption(img, fx, words, t0, t, y=1520, size=56, per=0.22, key=None, box=CYAN):
    """Subtítulo palabra por palabra: la palabra activa en blanco con caja de selección y anclas (estilo UI)."""
    n = int(clamp((t - t0) / per, 0, len(words)))
    if t < t0:
        return
    f = font('sans', size)
    d = ImageDraw.Draw(img)
    sp = d.textlength(' ', font=f) + 14
    ws = [d.textlength(w, font=f) for w in words]
    lines, cur, cw = [], [], 0
    for i, w in enumerate(ws):
        if cur and cw + sp + w > W * 0.84:
            lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += (sp if cw else 0) + w
    lines.append(cur)
    cur_i = min(n, len(words) - 1)
    lh = size * 1.32
    df = ImageDraw.Draw(fx)
    for li, line in enumerate(lines):
        tw = sum(ws[i] for i in line) + sp * (len(line) - 1)
        x = (W - tw) / 2
        yy = y + li * lh
        for i in line:
            if i <= cur_i:
                active = (i == cur_i) if key is None else (i in key)
                col = WHITE if (i == cur_i or active) else (140, 142, 150)
                d.text((x, yy), words[i], font=f, fill=col)
                if active and i <= cur_i:
                    pad = 12
                    bx = (x - pad, yy - 4, x + ws[i] + pad, yy + size * 1.12)
                    d.rectangle(bx, outline=box, width=3)
                    df.rectangle(bx, outline=scale_c(box, 0.6), width=5)
                    s = 6
                    for cx_, cy_ in ((bx[0], bx[1]), (bx[2], bx[1]), (bx[0], bx[3]), (bx[2], bx[3])):
                        d.rectangle((cx_ - s, cy_ - s, cx_ + s, cy_ + s), fill=(8, 10, 16), outline=box, width=2)
            x += ws[i] + sp


def pill(img, fx, x, y, txt, k=1.0, size=30, col=INK, border=CYAN, anchor='m', dot=True):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    f = font('sanss', size)
    tw = d.textlength(txt, font=f)
    padx, h = 26 + (18 if dot else 0), size * 1.9
    w = tw + padx * 2
    s = eback(k) if k < 1 else 1.0
    w2, h2 = w * s, h * s
    if anchor == 'm':
        x0 = x - w2 / 2
    elif anchor == 'l':
        x0 = x
    else:
        x0 = x - w2
    y0 = y - h2 / 2
    d.rounded_rectangle((x0, y0, x0 + w2, y0 + h2), radius=h2 / 2, fill=(10, 12, 16), outline=scale_c(border, 0.9), width=2)
    ImageDraw.Draw(fx).rounded_rectangle((x0, y0, x0 + w2, y0 + h2), radius=h2 / 2, outline=scale_c(border, 0.5), width=4)
    if s > 0.8:
        a = clamp((s - 0.8) / 0.2)
        tx = x0 + padx + (10 if dot else 0)
        if dot:
            r = 7
            d.ellipse((x0 + 24 - r, y - r, x0 + 24 + r, y + r), fill=scale_c(border, a))
        d.text((tx, y), txt, font=f, fill=scale_c(col, a), anchor='lm')


# ---------------------------------------------------------------- efectos (video de referencia 2, sin persona)
def glass_type(img, fx, txt, cx, cy, size, k=1.0, fill_a=0.09, edge=0.55):
    """Letras de cristal: relleno casi transparente, bisel con borde que brilla."""
    if k <= 0.01:
        return
    f = font('sansx', size)
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    bb = d0.textbbox((0, 0), txt, font=f)
    w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).text((20 - bb[0], 20 - bb[1]), txt, font=f, fill=255)
    er = m.filter(ImageFilter.MinFilter(7))
    edge_m = Image.fromarray(np.clip(np.asarray(m, np.int16) - np.asarray(er, np.int16), 0, 255).astype(np.uint8))
    sh = Image.fromarray(np.clip(np.asarray(m, np.int16) - np.roll(np.asarray(m, np.int16), 6, 0), 0, 255).astype(np.uint8))
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    a = clamp(k)
    img.paste(Image.new('RGB', (w, h), (255, 255, 255)), (x0, y0), m.point(lambda v: int(v * fill_a * a)))
    img.paste(Image.new('RGB', (w, h), (255, 255, 255)), (x0, y0), edge_m.point(lambda v: int(v * 0.5 * a)))
    img.paste(Image.new('RGB', (w, h), (255, 255, 255)), (x0, y0), sh.point(lambda v: int(v * 0.6 * a)))
    fx.paste(Image.new('RGB', (w, h), scale_c(WHITE, edge * a)), (x0, y0), edge_m.filter(ImageFilter.GaussianBlur(3)))


def doodle_circle(img, fx, cx, cy, rx, ry, t, k=1.0, col=WHITE, w=5, fps=10, seed=0):
    """Garabato vivo: círculo a mano que 'hierve' (cambia de trazo a 10 cuadros por segundo)."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(int(t * fps) + 100 * seed)
    n = 70
    th = np.linspace(-0.4, 2 * math.pi * 1.08, n) + rng.uniform(-0.05, 0.05)
    jit = 1 + 0.035 * np.sin(th * 3 + rng.rand() * 6) + rng.normal(0, 0.012, n)
    pts = [(cx + rx * j * math.cos(a), cy + ry * j * math.sin(a)) for a, j in zip(th, jit)]
    pts = pts[:max(2, int(n * clamp(k)))]
    ImageDraw.Draw(img).line(pts, fill=col, width=w, joint='curve')
    ImageDraw.Draw(fx).line(pts, fill=scale_c(col, 0.5), width=w + 4, joint='curve')


def doodle_arrow(img, fx, x0, y0, x1, y1, t, k=1.0, col=WHITE, w=5, fps=10, seed=1):
    if k <= 0.01:
        return
    rng = np.random.RandomState(int(t * fps) + 100 * seed)
    n = 24
    pts = []
    for i in range(int(n * clamp(k)) + 1):
        u = i / n
        bend = math.sin(u * math.pi) * 40
        pts.append((lerp(x0, x1, u) + rng.normal(0, 1.4) - bend * 0.3, lerp(y0, y1, u) + rng.normal(0, 1.4) + bend * 0.2))
    d = ImageDraw.Draw(img)
    if len(pts) > 1:
        d.line(pts, fill=col, width=w, joint='curve')
        ImageDraw.Draw(fx).line(pts, fill=scale_c(col, 0.5), width=w + 4)
    if k >= 0.98:
        ang = math.atan2(y1 - y0, x1 - x0)
        for da in (2.6, -2.6):
            d.line([(x1, y1), (x1 + 34 * math.cos(ang + da) + rng.normal(0, 1.5), y1 + 34 * math.sin(ang + da))], fill=col, width=w)


def rec_frame(img, t, k=1.0, zoom_label='x1.0'):
    """Marco de grabación del zoom digital: esquinas, REC parpadeando, código de tiempo."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    c = scale_c(WHITE, 0.9 * k)
    m, L = 60, 70
    for (x, y, sx, sy) in ((m, 230, 1, 1), (W - m, 230, -1, 1), (m, H - 300, 1, -1), (W - m, H - 300, -1, -1)):
        d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=c, width=4)
    if int(t * 2) % 2 == 0:
        d.ellipse((m + 10, 260, m + 34, 284), fill=scale_c(RED, k))
    f = font('mono', 30)
    d.text((m + 46, 256), 'REC', font=f, fill=c)
    tc = f'00:{int(t) // 60:02d}:{int(t) % 60:02d}:{int((t % 1) * 24):02d}'
    d.text((W - m - 10, 256), tc, font=f, fill=c, anchor='ra')
    d.text((W / 2, H - 340), zoom_label, font=font('mono', 34), fill=c, anchor='mm')


def chart_grow(img, fx, box, vals, labels, t0, t, unit='µT', title_txt='', vmax=None, line=True, tag=None):
    """Gráfico que crece: panel de cristal oscuro, barras que suben una por una y línea punteada con nodos."""
    x0, y0, x1, y1 = box
    k0 = eout(seg(t, t0, t0 + 0.35))
    if k0 <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    sc = 0.9 + 0.1 * k0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bx = (cx - (x1 - x0) / 2 * sc, cy - (y1 - y0) / 2 * sc, cx + (x1 - x0) / 2 * sc, cy + (y1 - y0) / 2 * sc)
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(over).rounded_rectangle(bx, radius=34, fill=(12, 13, 17, int(225 * k0)), outline=(255, 255, 255, int(70 * k0)), width=2)
    img.paste(over, (0, 0), over)
    if title_txt:
        d.text((bx[0] + 44, bx[1] + 40), title_txt, font=font('mono', 28), fill=scale_c(MUTED, k0))
    if tag:
        pill(img, fx, bx[2] - 40, bx[1] + 58, tag, k0, size=24, border=(200, 200, 210), anchor='r', dot=False)
    vmax = vmax or max(abs(v) for v in vals) * 1.15
    n = len(vals)
    base_y = bx[3] - 120
    top_y = bx[1] + 150
    bw = (bx[2] - bx[0] - 160) / n
    tops = []
    for i, (v, lab) in enumerate(zip(vals, labels)):
        kb = eout(seg(t, t0 + 0.25 + 0.28 * i, t0 + 0.75 + 0.28 * i), 3)
        hx0 = bx[0] + 80 + i * bw + bw * 0.18
        hx1 = hx0 + bw * 0.64
        hh = (base_y - top_y) * abs(v) / vmax * kb
        d.rounded_rectangle((hx0, base_y - hh, hx1, base_y), radius=10, fill=(236, 238, 242) if i == n - 1 else (120, 124, 134))
        df.rectangle((hx0, base_y - max(4, hh), hx1, base_y - max(4, hh) + 6), fill=(90, 90, 90))
        d.text(((hx0 + hx1) / 2, base_y + 46), lab, font=font('mono', 32), fill=scale_c(INK, k0), anchor='mm')
        if kb > 0.05:
            d.text(((hx0 + hx1) / 2, base_y - hh - 34), f'{abs(v) * kb:.0f}', font=font('mono', 30), fill=scale_c(WHITE, kb), anchor='mm')
        tops.append(((hx0 + hx1) / 2, base_y - hh, kb))
    if line:
        pts = [(x, y) for x, y, kb in tops if kb > 0.98]
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            L = math.hypot(xb - xa, yb - ya)
            for s in np.arange(0, L, 16):
                u = s / L
                xx, yy = lerp(xa, xb, u), lerp(ya, yb, u) - 70
                d.ellipse((xx - 3, yy - 3, xx + 3, yy + 3), fill=(200, 200, 205))
        for x, y in pts:
            d.ellipse((x - 9, y - 79, x + 9, y - 61), fill=WHITE)
            df.ellipse((x - 16, y - 86, x + 16, y - 54), fill=(120, 120, 120))


def photo_card(img, fx, photo, x, y, w, t0, t, caption='', angle0=-9.0, credit_y=None):
    """Muro de titulares / foto real: la tarjeta cae, rebota y se queda con balanceo amortiguado."""
    if t < t0:
        return
    u = t - t0
    drop = eout(clamp(u / 0.28), 3)
    yy = lerp(y - 420, y, drop)
    ang = angle0 * (1 - drop) + 7.0 * math.exp(-5.5 * max(0, u - 0.28)) * math.cos(14 * max(0, u - 0.28)) * (1 if u > 0.28 else 0) - 3.0
    ph = photo.copy()
    pw = int(w)
    phh = int(pw * ph.height / ph.width)
    ph = ph.resize((pw, phh), Image.LANCZOS)
    border = 16
    card = Image.new('RGBA', (pw + 2 * border, phh + 2 * border + (54 if caption else 0)), (245, 244, 240, 255))
    card.paste(ph, (border, border))
    if caption:
        ImageDraw.Draw(card).text((border, phh + border + 14), caption, font=font('mono', 22), fill=(60, 60, 64))
    card = card.rotate(ang, resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', card.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 150), (0, 0), card.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    px, py = int(x - card.width / 2), int(yy - card.height / 2)
    img.paste(sh, (px + 14, py + 22), sh)
    img.paste(card, (px, py), card)
