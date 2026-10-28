"""Motor 3D de Mente en órbita, con TEMAS visuales (MOTOR_TEMA=estudio|espacio|medico|plano|neon|noir|naturaleza|micro|mapa).
Nació con el video largo de GTA 6 (tema estudio).
Fondo blanco con piso de puntos en perspectiva, objetos 3D con color y sombra suave,
líneas y anillos en blanco y negro como efectos. Sirve en horizontal (YouTube) y vertical (reels):
GTA_FMT=h -> 1920x1080, GTA_FMT=v -> 1080x1920."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FMT = os.environ.get('GTA_FMT', 'h')
W, H = (1920, 1080) if FMT == 'h' else (1080, 1920)
VERT = FMT == 'v'
SS = 2
SW, SH = W * SS, H * SS
FPS = 24

# ---------------------------------------------------------------- temas visuales
# Cada video elige el tema que mejor cuenta su historia (ver .claude/skills/animador/temas.md).
THEMES = {
    # fondo blanco, piso de puntos, objetos a color (tecnología, productos, videojuegos explicados, comparaciones)
    'estudio': dict(top=(250, 250, 248), bot=(244, 244, 242), floor='dots', fcol=(130, 130, 134), ink=(20, 20, 22),
                    muted=(150, 150, 154), pill=(255, 255, 255), pborder=(210, 210, 212), shadow=(175, 175, 178), vig=0.07),
    # negro azulado con estrellas (espacio, satélites, astronomía)
    'espacio': dict(top=(6, 10, 24), bot=(14, 20, 42), floor='stars', fcol=(200, 210, 255), ink=(240, 244, 255),
                    muted=(140, 150, 180), pill=(24, 32, 60), pborder=(70, 84, 130), shadow=(4, 6, 14), vig=0.25),
    # clínico claro con retícula (cuerpo humano, salud, anatomía)
    'medico': dict(top=(236, 244, 249), bot=(218, 231, 240), floor='grid', fcol=(150, 180, 200), ink=(16, 40, 64),
                   muted=(110, 140, 165), pill=(255, 255, 255), pborder=(180, 205, 220), shadow=(170, 190, 205), vig=0.06),
    # plano técnico azul (ingeniería, máquinas, cómo funciona por dentro)
    'plano': dict(top=(22, 66, 128), bot=(14, 48, 100), floor='grid', fcol=(140, 190, 255), ink=(240, 248, 255),
                  muted=(150, 190, 235), pill=(18, 56, 112), pborder=(120, 170, 235), shadow=(8, 34, 74), vig=0.18),
    # retro neón con malla synthwave (videojuegos, cultura pop, internet)
    'neon': dict(top=(22, 8, 44), bot=(70, 14, 82), floor='synth', fcol=(255, 70, 200), ink=(255, 244, 255),
                 muted=(200, 150, 220), pill=(40, 14, 66), pborder=(255, 90, 210), shadow=(14, 4, 26), vig=0.22),
    # documental oscuro con foco (historias reales, crimen, hackeos, misterios)
    'noir': dict(top=(26, 27, 31), bot=(14, 15, 18), floor='dots', fcol=(110, 110, 118), ink=(238, 236, 230),
                 muted=(140, 140, 146), pill=(36, 37, 42), pborder=(80, 80, 88), shadow=(6, 6, 8), vig=0.35),
    # cielo y tierra (clima, volcanes, sismos, animales, planeta)
    'naturaleza': dict(top=(176, 214, 240), bot=(236, 226, 200), floor='grid', fcol=(150, 140, 110), ink=(30, 36, 30),
                       muted=(100, 110, 96), pill=(252, 250, 244), pborder=(200, 192, 170), shadow=(150, 140, 115), vig=0.05),
    # microscopio: verde azulado oscuro con partículas (células, química, materiales, virus)
    'micro': dict(top=(6, 34, 40), bot=(4, 18, 26), floor='bokeh', fcol=(90, 220, 200), ink=(230, 255, 250),
                  muted=(120, 190, 180), pill=(10, 46, 52), pborder=(60, 160, 150), shadow=(2, 10, 14), vig=0.3),
    # papel con curvas de nivel (geografía, mapas, datos, historia de países)
    'mapa': dict(top=(244, 239, 228), bot=(236, 229, 214), floor='contour', fcol=(180, 160, 120), ink=(52, 40, 28),
                 muted=(140, 120, 96), pill=(250, 246, 236), pborder=(210, 196, 170), shadow=(190, 175, 150), vig=0.08),
}
TEMA = os.environ.get('MOTOR_TEMA', 'estudio')
TH = THEMES[TEMA]
DARK = sum(TH['top']) < 300
BG = np.array(TH['bot'], float)
INK = TH['ink']
MUTED = TH['muted']
GRAY = (150, 150, 152)
LIGHTG = (205, 205, 207)

FONTS = {
    'xb': '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf',
    'b': '/usr/share/fonts/opentype/inter/Inter-Bold.otf',
    'sb': '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf',
    'm': '/usr/share/fonts/opentype/inter/Inter-Medium.otf',
    'mono': '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf',
    'monor': '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf',
}
_FC = {}


def font(k, size):
    key = (k, int(size))
    if key not in _FC:
        p = FONTS[k]
        if not os.path.exists(p):
            p = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        _FC[key] = ImageFont.truetype(p, int(size))
    return _FC[key]


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eback(x):
    x = clamp(x)
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(round(lerp(a, b, k))) for a, b in zip(c1, c2))


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def win(t, a, b, fi=0.3, fo=0.3):
    """Ventana suave: 0 antes de a, 1 entre a+fi y b-fo, 0 después de b."""
    if t < a or t > b:
        return 0.0
    k = 1.0
    if fi > 0:
        k = min(k, (t - a) / fi)
    if fo > 0:
        k = min(k, (b - t) / fo)
    return ease(k)


# ---------------------------------------------------------------- cámara
class Cam:
    def __init__(self, target=(0, 0.6, 0), dist=7.0, yaw=25.0, pitch=18.0, fk=1.45, cx=0.5, cy=None, roll=0.0):
        self.target = np.array(target, float)
        if cy is None:
            cy = 0.60 if not VERT else 0.46
        y, p = math.radians(yaw), math.radians(pitch)
        off = np.array([math.cos(p) * math.sin(y), math.sin(p), math.cos(p) * math.cos(y)])
        self.pos = self.target + off * dist
        f = self.target - self.pos
        f /= np.linalg.norm(f)
        r = np.cross(f, np.array([0, 1.0, 0]))
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        if roll:
            a = math.radians(roll)
            r, u = r * math.cos(a) + u * math.sin(a), u * math.cos(a) - r * math.sin(a)
        self.f, self.r, self.u = f, r, u
        self.F = fk * min(W, H) * SS
        self.cx, self.cy = cx * SW, cy * SH
        self.dist = dist

    def proj(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        d = P - self.pos
        x = d @ self.r
        y = d @ self.u
        z = d @ self.f
        zz = np.maximum(z, 1e-3)
        sx = self.cx + self.F * x / zz
        sy = self.cy - self.F * y / zz
        return np.stack([sx, sy], 1), z

    def p1(self, p):
        """Proyección de un punto a coordenadas de la imagen final (1x)."""
        s, z = self.proj(p)
        return s[0, 0] / SS, s[0, 1] / SS, z[0]


def cam_lerp(a, b, k):
    """Interpola dos dicts de parámetros de cámara."""
    out = {}
    for key in a:
        va, vb = a[key], b.get(key, a[key])
        if isinstance(va, (tuple, list)):
            out[key] = tuple(lerp(x, y, k) for x, y in zip(va, vb))
        else:
            out[key] = lerp(va, vb, k)
    return out


def cam_path(t, keys):
    """keys: [(t, dict)] -> Cam interpolada con ease."""
    if t <= keys[0][0]:
        return Cam(**keys[0][1])
    for (ta, a), (tb, b) in zip(keys[:-1], keys[1:]):
        if ta <= t <= tb:
            return Cam(**cam_lerp(a, b, ease((t - ta) / max(1e-6, tb - ta))))
    return Cam(**keys[-1][1])


# ---------------------------------------------------------------- mallas
class Mesh:
    def __init__(self, V, F, C, edge=None, shadow=0.0, double=False, gloss=0.0, flat=False, alpha=1.0):
        self.V = np.asarray(V, float)
        self.F = [tuple(f) for f in F]
        self.C = C if isinstance(C, list) else [C] * len(self.F)
        self.edge = edge
        self.shadow = shadow
        self.double = double
        self.gloss = gloss
        self.flat = flat
        self.decals = []  # (idx4 vértices, imagen)
        self.alpha = alpha
        self.sh_r = None

    def copy(self):
        m = Mesh(self.V.copy(), list(self.F), list(self.C), self.edge, self.shadow, self.double, self.gloss, self.flat, self.alpha)
        m.decals = list(self.decals)
        m.sh_r = self.sh_r
        if hasattr(self, 'ORD'):
            m.ORD = self.ORD; m.FACE = self.FACE
        return m

    def tf(self, s=1.0, ry=0.0, rx=0.0, rz=0.0, t=(0, 0, 0)):
        V = self.V * (np.array(s, float) if not np.isscalar(s) else s)
        V = V @ rotm(rx, ry, rz).T
        m = self.copy()
        m.V = V + np.array(t, float)
        return m


def rotm(rx=0.0, ry=0.0, rz=0.0):
    ax, ay, az = math.radians(rx), math.radians(ry), math.radians(rz)
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


def box(sx, sy, sz, col, cols=None, edge=True, shadow=0.35, base=True, gloss=0.0):
    """Caja con base en y=0 (si base) centrada en x,z. cols: dict cara->color (top,bottom,front,back,left,right)."""
    x, z = sx / 2, sz / 2
    y0, y1 = (0, sy) if base else (-sy / 2, sy / 2)
    V = [(-x, y0, -z), (x, y0, -z), (x, y1, -z), (-x, y1, -z), (-x, y0, z), (x, y0, z), (x, y1, z), (-x, y1, z)]
    F = {'back': (0, 3, 2, 1), 'front': (4, 5, 6, 7), 'left': (0, 4, 7, 3), 'right': (1, 2, 6, 5),
         'top': (3, 7, 6, 2), 'bottom': (0, 1, 5, 4)}
    cols = cols or {}
    order = ['back', 'front', 'left', 'right', 'top', 'bottom']
    m = Mesh(V, [F[k] for k in order], [cols.get(k, col) for k in order], edge=edge, shadow=shadow, gloss=gloss)
    m.sh_r = 0.55 * math.hypot(sx, sz)
    m.FACE = {k: i for i, k in enumerate(order)}
    m.ORD = {m.FACE['front']: (3, 2, 1, 0), m.FACE['right']: (2, 1, 0, 3), m.FACE['left']: (3, 2, 1, 0),
             m.FACE['top']: (0, 3, 2, 1), m.FACE['back']: (2, 1, 0, 3), m.FACE['bottom']: (0, 1, 2, 3)}
    return m


def rbox(sx, sy, sz, r, col, n=4, shadow=0.35, edge=False, gloss=0.25, base=True):
    """Caja con esquinas redondeadas en planta (x,z): extrusión de rectángulo redondeado."""
    pts = []
    for cx, cz, a0 in ((sx / 2 - r, sz / 2 - r, 0), (-sx / 2 + r, sz / 2 - r, 90), (-sx / 2 + r, -sz / 2 + r, 180), (sx / 2 - r, -sz / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    m = extrude(pts, sy, col, shadow=shadow, edge=edge, gloss=gloss)
    if not base:
        m.V[:, 1] -= sy / 2
    return m


def extrude(pts, h, col, top=None, side=None, shadow=0.35, edge=False, gloss=0.0, y0=0.0):
    """Extruye un polígono (x,z) en planta hacia arriba h."""
    pts = list(pts)
    a = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i]; x2, z2 = pts[(i + 1) % len(pts)]
        a += x1 * z2 - x2 * z1
    if a < 0:
        pts = pts[::-1]
    n = len(pts)
    V = [(x, y0, z) for x, z in pts] + [(x, y0 + h, z) for x, z in pts]
    F, C = [], []
    for i in range(n):
        j = (i + 1) % n
        F.append((i, n + i, n + j, j)); C.append(side or col)
    F.append(tuple(range(2 * n - 1, n - 1, -1))); C.append(top or col)
    F.append(tuple(range(n))); C.append(col)
    m = Mesh(V, F, C, edge=edge, shadow=shadow, gloss=gloss)
    P = np.array(pts)
    m.sh_r = 0.5 * float(np.max(P.max(0) - P.min(0)))
    m.TOP = len(F) - 2
    return m


def cyl(r, h, col, n=28, top=None, shadow=0.35, gloss=0.2, r2=None, y0=0.0, edge=False):
    r2 = r if r2 is None else r2
    V = [(r * math.cos(2 * math.pi * i / n), y0, r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    V += [(r2 * math.cos(2 * math.pi * i / n), y0 + h, r2 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    F, C = [], []
    for i in range(n):
        j = (i + 1) % n
        F.append((i, n + i, n + j, j)); C.append(col)
    F.append(tuple(range(2 * n - 1, n - 1, -1))); C.append(top or col)
    F.append(tuple(range(n))); C.append(col)
    m = Mesh(V, F, C, shadow=shadow, gloss=gloss, edge=edge)
    m.sh_r = max(r, r2)
    m.TOP = n
    return m


def sphere(r, col, nu=28, nv=16, shadow=0.4, gloss=0.6, cols=None):
    V = []
    for j in range(nv + 1):
        v = math.pi * j / nv
        for i in range(nu):
            u = 2 * math.pi * i / nu
            V.append((r * math.sin(v) * math.cos(u), r * math.cos(v), r * math.sin(v) * math.sin(u)))
    F, C = [], []
    for j in range(nv):
        for i in range(nu):
            a = j * nu + i; b = j * nu + (i + 1) % nu
            F.append((a, b, b + nu, a + nu))
            C.append(cols(i, j) if cols else col)
    m = Mesh(V, F, C, shadow=shadow, gloss=gloss)
    m.sh_r = r
    return m


def torus(R, r, col, nu=36, nv=10, shadow=0.0, gloss=0.3):
    V = []
    for i in range(nu):
        u = 2 * math.pi * i / nu
        for j in range(nv):
            v = 2 * math.pi * j / nv
            V.append(((R + r * math.cos(v)) * math.cos(u), r * math.sin(v), (R + r * math.cos(v)) * math.sin(u)))
    F = []
    for i in range(nu):
        for j in range(nv):
            a = i * nv + j; b = ((i + 1) % nu) * nv + j
            F.append((a, a - j + (j + 1) % nv, b - j + (j + 1) % nv, b))
    m = Mesh(V, F, col, shadow=shadow, gloss=gloss)
    m.sh_r = R
    return m


def merge(ms):
    V, F, C = [], [], []
    off = 0
    for m in ms:
        V.append(m.V)
        F += [tuple(i + off for i in f) for f in m.F]
        C += m.C
        off += len(m.V)
    out = Mesh(np.concatenate(V), F, C, edge=ms[0].edge, shadow=ms[0].shadow, gloss=ms[0].gloss)
    out.sh_r = ms[0].sh_r
    return out


# ---------------------------------------------------------------- texturas (calcas sobre caras)
def _persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def paste_quad(canvas, quad, img, alpha=1.0):
    """Pega img (RGBA) deformada en el cuadrilátero quad [(x,y)x4] (orden: sup-izq, sup-der, inf-der, inf-izq)."""
    q = np.array(quad)
    x0, y0 = np.floor(q.min(0)).astype(int)
    x1, y1 = np.ceil(q.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, canvas.width), min(y1, canvas.height)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    w, h = img.size
    try:
        co = _persp_coeffs([(px - x0, py - y0) for px, py in quad], [(0, 0), (w, 0), (w, h), (0, h)])
    except np.linalg.LinAlgError:
        return
    out = img.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(co), Image.BILINEAR)
    m = out.getchannel('A')
    if alpha < 1:
        m = m.point(lambda v: int(v * alpha))
    canvas.paste(out.convert('RGB'), (x0, y0), m)


def decal(m, face_idx, img, flip=False):
    """Asocia una imagen a una cara de 4 vértices de la malla (orden sup-izq, sup-der, inf-der, inf-izq)."""
    order = getattr(m, 'ORD', {}).get(face_idx, (0, 1, 2, 3))
    m.decals.append((face_idx, img, order))
    return m


# ---------------------------------------------------------------- escena
LIGHT = np.array([-0.45, 0.85, 0.55]); LIGHT /= np.linalg.norm(LIGHT)


class Frame:
    def __init__(self):
        self.cam = Cam()
        self.meshes = []
        self.under = []   # funciones (draw, cam) sobre el lienzo grande antes de las mallas
        self.over = []    # después de las mallas
        self.ui = []      # funciones (img1x, draw1x) tras reducir
        self.floor = 1.0
        self.floor_r = 7.0
        self.floor_g = 0.32
        self.gray = 0.0
        self.mono = False  # todo en blanco y negro (tarjetas de transición)
        self.head = None
        self.kicker = None
        self.head_k = 1.0
        self.pill = None
        self.fade_white = 0.0


def shade(col, n, gloss=0.0, view=None):
    d = max(0.0, float(n @ LIGHT))
    k = 0.60 + 0.48 * d
    c = np.array(col[:3], float) * k
    if gloss and view is not None:
        h = LIGHT - view
        h /= (np.linalg.norm(h) + 1e-9)
        s = max(0.0, float(n @ h)) ** 24 * gloss
        c = c + (255 - c) * s
    if n[1] < -0.5:
        c *= 0.8
    return tuple(int(clamp(v, 0, 255)) for v in c)


def draw_floor(d, cam, fr):
    if fr.floor <= 0:
        return
    st = TH['floor']
    if st in ('stars', 'bokeh'):
        return  # van en el fondo
    g = fr.floor_g
    R = fr.floor_r
    tx, tz = cam.target[0], cam.target[2]
    bgc = np.array(TH['bot'], float)
    fc = np.array(TH['fcol'], float)
    if st in ('grid', 'synth', 'contour'):
        step = g * (2.5 if st == 'grid' else 3.0)
        lines = []
        if st == 'contour':
            for k in range(1, int(R / step) + 1):
                th = np.linspace(0, 2 * math.pi, 90)
                r = k * step
                lines.append((np.stack([tx + r * np.cos(th) * (1 + 0.08 * np.sin(3 * th + k)), np.zeros_like(th),
                                        tz + r * np.sin(th) * (1 + 0.08 * np.cos(2 * th + k))], 1), r / R))
        else:
            x0 = math.floor((tx - R) / step) * step
            z0 = math.floor((tz - R) / step) * step
            n = int(2 * R / step) + 2
            for i in range(n):
                x = x0 + i * step
                zs = np.linspace(tz - R, tz + R, 40)
                lines.append((np.stack([np.full_like(zs, x), np.zeros_like(zs), zs], 1), abs(x - tx) / R))
                z = z0 + i * step
                xs = np.linspace(tx - R, tx + R, 40)
                lines.append((np.stack([xs, np.zeros_like(xs), np.full_like(xs, z)], 1), abs(z - tz) / R))
        for P, dist in lines:
            if dist >= 1:
                continue
            s_, z_ = cam.proj(P)
            ok = z_ > 0.3
            dd = np.hypot(P[:, 0] - tx, P[:, 2] - tz)
            pts = [tuple(p) for p, o, q in zip(s_, ok, dd) if o and q < R]
            if len(pts) < 2:
                continue
            a = (1 - dist ** 2) * fr.floor * (0.55 if st == 'grid' else 0.9)
            c = tuple(int(v) for v in bgc + (fc - bgc) * a)
            d.line(pts, fill=c, width=max(1, int(SS * (1.4 if st == 'synth' else 1.0))))
        return
    ix = np.arange(math.floor((tx - R) / g), math.ceil((tx + R) / g) + 1) * g
    iz = np.arange(math.floor((tz - R) / g), math.ceil((tz + R) / g) + 1) * g
    X, Z = np.meshgrid(ix, iz)
    X, Z = X.ravel(), Z.ravel()
    dd = np.hypot(X - tx, Z - tz)
    keep = dd < R
    X, Z, dd = X[keep], Z[keep], dd[keep]
    P = np.stack([X, np.zeros_like(X), Z], 1)
    s, z = cam.proj(P)
    ok = (z > 0.3) & (s[:, 0] > -20) & (s[:, 0] < SW + 20) & (s[:, 1] > -20) & (s[:, 1] < SH + 20)
    a = (1 - (dd / R) ** 2) * fr.floor
    rad = np.clip(0.020 * cam.F / np.maximum(z, 0.3), 0.6, 7)
    for (x, y), aa, rr, o in zip(s, a, rad, ok):
        if not o or aa <= 0.02:
            continue
        c = tuple(int(v) for v in bgc + (fc - bgc) * aa)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=c)


def draw_shadows(canvas, cam, meshes):
    sc = 8
    lay = Image.new('L', (SW // sc, SH // sc), 0)
    ld = ImageDraw.Draw(lay)
    anyy = False
    for m in meshes:
        if not m.shadow or m.sh_r is None:
            continue
        ymin = m.V[:, 1].min()
        if ymin > 1.2:
            k = max(0.0, 1 - (ymin - 1.2) / 3.0)
        else:
            k = 1.0
        if k <= 0:
            continue
        cx, cz = m.V[:, 0].mean(), m.V[:, 2].mean()
        r = m.sh_r * (1.05 + 0.15 * max(0, ymin))
        pts = [(cx + r * math.cos(a) + 0.08, 0.0, cz + r * 0.9 * math.sin(a) - 0.05) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
        s, z = cam.proj(pts)
        if (z < 0.2).any():
            continue
        ld.polygon([(x / sc, y / sc) for x, y in s], fill=int(110 * m.shadow * k * (1 if m.alpha >= 1 else m.alpha)))
        anyy = True
    if not anyy:
        return
    lay = lay.filter(ImageFilter.GaussianBlur(5)).resize((SW, SH), Image.BILINEAR)
    dark = Image.new('RGB', (SW, SH), TH['shadow'])
    canvas.paste(dark, (0, 0), lay)


def draw_meshes(canvas, d, cam, meshes, mono=False):
    items = []
    for mi, m in enumerate(meshes):
        if m.alpha <= 0.01:
            continue
        S, Z = cam.proj(m.V)
        V = m.V
        for fi, f in enumerate(m.F):
            zf = Z[list(f)]
            if (zf < 0.15).any():
                continue
            p0, p1, p2 = V[f[0]], V[f[1]], V[f[2]]
            if len(f) > 4:  # Newell: normal robusta para polígonos no convexos
                Q = V[list(f)]
                Qn = np.roll(Q, -1, 0)
                n = np.array([np.sum((Q[:, 1] - Qn[:, 1]) * (Q[:, 2] + Qn[:, 2])),
                              np.sum((Q[:, 2] - Qn[:, 2]) * (Q[:, 0] + Qn[:, 0])),
                              np.sum((Q[:, 0] - Qn[:, 0]) * (Q[:, 1] + Qn[:, 1]))])
                pass
            else:
                n = np.cross(p1 - p0, p2 - p0)
            nn = np.linalg.norm(n)
            if nn < 1e-12:
                if len(f) > 3:
                    n = np.cross(V[f[2]] - p0, V[f[3]] - p0); nn = np.linalg.norm(n)
                if nn < 1e-12:
                    continue
            n = n / nn
            cen = V[list(f)].mean(0)
            view = cen - cam.pos
            vd = view / (np.linalg.norm(view) + 1e-9)
            if n @ vd > 0:
                if not m.double:
                    continue
                n = -n
            items.append((float(zf.mean()), mi, fi, n, vd))
    items.sort(key=lambda it: -it[0])
    for z, mi, fi, n, vd in items:
        m = meshes[mi]
        f = m.F[fi]
        S, _ = cam.proj(m.V[list(f)])
        col = m.C[fi]
        if m.flat:
            c = tuple(int(v) for v in col[:3])
        else:
            c = shade(col, n, m.gloss, vd)
        if mono:
            g = int(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
            c = (g, g, g)
        if m.alpha < 1:
            c = mix(tuple(int(v) for v in BG), c, m.alpha)
        pts = [tuple(p) for p in S]
        if m.edge:
            ec = m.edge if isinstance(m.edge, tuple) else tuple(int(v * 0.78) for v in c)
            d.polygon(pts, fill=c, outline=ec)
        else:
            d.polygon(pts, fill=c, outline=c)
        for (dfi, img, order) in m.decals:
            if dfi == fi:
                paste_quad(canvas, [pts[k] for k in order], img, m.alpha)


def line3(d, cam, pts, col=INK, w=2.0, dash=None, a=1.0):
    P = np.asarray(pts, float)
    s, z = cam.proj(P)
    c = mix(tuple(int(v) for v in BG), col, a)
    if dash:
        # puntos/rayitas a lo largo de la curva en pantalla
        seg = np.hypot(*(np.diff(s, axis=0).T))
        L = np.concatenate([[0], np.cumsum(seg)])
        step = dash * SS
        for ds in np.arange(0, L[-1], step):
            i = min(np.searchsorted(L, ds) - 1, len(s) - 2)
            i = max(i, 0)
            k = (ds - L[i]) / max(1e-6, L[i + 1] - L[i])
            x, y = s[i] + (s[i + 1] - s[i]) * k
            if z[i] < 0.2:
                continue
            r = w * SS * 0.6
            d.ellipse((x - r, y - r, x + r, y + r), fill=c)
        return
    ok = z > 0.2
    pts2 = [tuple(p) for p, o in zip(s, ok) if o]
    if len(pts2) >= 2:
        d.line(pts2, fill=c, width=max(1, int(w * SS)), joint='curve')


def ring3(d, cam, center, r, col=INK, w=2.0, a=1.0, n=72, y=None, dash=None, axis='y', frac=1.0):
    cx, cy, cz = center
    th = np.linspace(0, 2 * math.pi * frac, max(3, int(n * frac)) + 1)
    if axis == 'y':
        P = np.stack([cx + r * np.cos(th), np.full_like(th, cy), cz + r * np.sin(th)], 1)
    else:  # anillo vertical, de frente a z
        P = np.stack([cx + r * np.cos(th), cy + r * np.sin(th), np.full_like(th, cz)], 1)
    line3(d, cam, P, col, w, dash, a)


def dot3(d, cam, p, r=6, col=INK, a=1.0):
    s, z = cam.proj([p])
    if z[0] < 0.2:
        return
    x, y = s[0]
    rr = r * SS
    d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=mix(tuple(int(v) for v in BG), col, a))


# ---------------------------------------------------------------- fondo
_BG = {}


def bg_img():
    if 'b' not in _BG:
        h, w = SH // 4, SW // 4
        y, x = np.mgrid[0:h, 0:w]
        top, bot = np.array(TH['top'], float), np.array(TH['bot'], float)
        k = (y / h)[..., None]
        img = top * (1 - k) + bot * k
        r = np.hypot((x - w / 2) / w, (y - h * 0.45) / h)
        v = 1 - TH['vig'] * np.clip(r - 0.2, 0, 1) ** 1.2 * 2
        img = img * v[..., None]
        if TEMA == 'noir':  # foco de luz al centro
            img += 26 * np.exp(-((x - w / 2) ** 2 / (w * 0.25) ** 2 + (y - h * 0.55) ** 2 / (h * 0.35) ** 2))[..., None]
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((SW, SH), Image.BILINEAR)
        rng = np.random.RandomState(7)
        dd = ImageDraw.Draw(im)
        if TH['floor'] == 'stars':
            for _ in range(900):
                sx, sy = rng.rand() * SW, rng.rand() * SH
                rr = rng.choice([0.6, 0.9, 1.3, 2.0], p=[0.5, 0.3, 0.15, 0.05]) * SS
                b = rng.uniform(0.35, 1.0)
                c = tuple(int(a + (bb - a) * b) for a, bb in zip(TH['bot'], TH['fcol']))
                dd.ellipse((sx - rr, sy - rr, sx + rr, sy + rr), fill=c)
        if TH['floor'] == 'bokeh':
            lay = Image.new('RGB', (SW // 4, SH // 4), (0, 0, 0))
            ld = ImageDraw.Draw(lay)
            for _ in range(70):
                sx, sy, rr = rng.rand() * SW / 4, rng.rand() * SH / 4, rng.uniform(4, 26)
                b = rng.uniform(0.15, 0.5)
                ld.ellipse((sx - rr, sy - rr, sx + rr, sy + rr), fill=tuple(int(c * b) for c in TH['fcol']))
            lay = lay.filter(ImageFilter.GaussianBlur(5)).resize((SW, SH), Image.BILINEAR)
            from PIL import ImageChops
            im = ImageChops.add(im, lay)
        _BG['b'] = im
    return _BG['b'].copy()


def render_frame(fr):
    canvas = bg_img()
    d = ImageDraw.Draw(canvas)
    cam = fr.cam
    draw_floor(d, cam, fr)
    draw_shadows(canvas, cam, fr.meshes)
    d = ImageDraw.Draw(canvas)
    for fn in fr.under:
        fn(d, cam)
    draw_meshes(canvas, d, cam, fr.meshes, fr.mono)
    for fn in fr.over:
        fn(d, cam)
    img = canvas.resize((W, H), Image.LANCZOS)
    if fr.gray > 0 or fr.mono:
        g = img.convert('L').convert('RGB')
        img = Image.blend(img, g, 1.0 if fr.mono else clamp(fr.gray))
    if fr.fade_white > 0:
        img = Image.blend(img, Image.new('RGB', (W, H), tuple(int(v) for v in BG)), clamp(fr.fade_white))
    d1 = ImageDraw.Draw(img)
    for fn in fr.ui:
        fn(img, d1)
    return img


# ---------------------------------------------------------------- texto e interfaz
def text_w(txt, f):
    return f.getbbox(txt)[2] - f.getbbox(txt)[0] if txt else 0


def draw_text(d, xy, txt, f, col, anchor='la', a=1.0, spacing=0):
    if a <= 0.01:
        return
    c = mix(tuple(int(v) for v in BG), col, a) if a < 1 else col
    if spacing:
        x, y = xy
        tw = sum(text_w(ch, f) + spacing for ch in txt) - spacing
        if anchor[0] == 'm':
            x -= tw / 2
        elif anchor[0] == 'r':
            x -= tw
        for ch in txt:
            d.text((x, y), ch, font=f, fill=c, anchor='l' + anchor[1])
            x += text_w(ch, f) + spacing if ch != ' ' else f.size * 0.3 + spacing
        return
    d.text(xy, txt, font=f, fill=c, anchor=anchor)


def headline(img, d, lines, accent, k=1.0, kicker=None, y=None):
    """Título grande estilo 'El vidrio / se rompe.' con punto de color. k: 0..1 aparición."""
    if k <= 0.01:
        return
    size = 64 if not VERT else 84
    f = font('xb', size)
    y0 = (78 if not VERT else 210) if y is None else y
    if kicker:
        fk = font('sb', 17 if not VERT else 24)
        draw_text(d, (W / 2, y0 - (34 if not VERT else 50)), '•  ' + kicker.upper(), fk, MUTED, 'mm', a=k, spacing=3)
    lh = size * 1.02
    for i, ln in enumerate(lines):
        kk = ease((k - i * 0.15) / 0.85)
        if kk <= 0:
            continue
        yy = y0 + i * lh + (1 - kk) * 26
        last = i == len(lines) - 1
        txt = ln
        dot = ''
        if last and txt and txt[-1] in '.?!':
            dot = txt[-1]; txt = txt[:-1]
        tw = text_w(txt + dot, f)
        x = W / 2 - tw / 2
        draw_text(d, (x, yy), txt, f, INK, 'lm', a=kk)
        if dot:
            draw_text(d, (x + text_w(txt, f) + 2, yy), dot, f, accent, 'lm', a=kk)


def pill(img, d, x, y, txt, a=1.0, fill=None, col=None, size=None, border=None, anchor='m', fnt='sb', dotc=None):
    fill = TH['pill'] if fill is None else fill
    col = INK if col is None else col
    border = TH['pborder'] if border is None else border
    if a <= 0.01:
        return
    size = size or (19 if not VERT else 26)
    f = font(fnt, size)
    tw = text_w(txt, f)
    pad = size * 0.75
    extra = size * 0.9 if dotc else 0
    w = tw + 2 * pad + extra
    h = size * 1.9
    if anchor == 'm':
        x0 = x - w / 2
    elif anchor == 'l':
        x0 = x
    else:
        x0 = x - w
    y0 = y - h / 2
    bgc = tuple(int(v) for v in BG)
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=h / 2, fill=mix(bgc, fill, a), outline=mix(bgc, border, a), width=2)
    if dotc:
        r = size * 0.28
        d.ellipse((x0 + pad - r + r, y - r, x0 + pad + r + r, y + r), fill=mix(bgc, dotc, a))
    draw_text(d, (x0 + pad + extra, y + 1), txt, f, col, 'lm', a=a)


def label(img, d, px, py, txt, sub=None, a=1.0, side=1, length=90, up=40, col=INK):
    """Etiqueta con línea guía (como 'Vidrio común' en la referencia)."""
    if a <= 0.01:
        return
    bgc = tuple(int(v) for v in BG)
    c = mix(bgc, col, a)
    ex, ey = px + side * length * ease(a), py - up * ease(a)
    d.line([(px, py), (px + side * 14, ey), (ex, ey)], fill=c, width=2)
    d.ellipse((px - 4, py - 4, px + 4, py + 4), fill=c)
    f = font('sb', 20 if not VERT else 27)
    anc = 'ls' if side > 0 else 'rs'
    draw_text(d, (ex + side * 4, ey - 8), txt, f, col, anc, a=a)
    if sub:
        draw_text(d, (ex + side * 4, ey + 20 if not VERT else ey + 26), sub, font('m', 15 if not VERT else 20), MUTED, anc, a=a)


def counter(img, d, x, y, txt, size=None, a=1.0, col=INK, sub=None, fnt='mono'):
    if a <= 0.01:
        return
    size = size or (72 if not VERT else 96)
    draw_text(d, (x, y), txt, font(fnt, size), col, 'mm', a=a)
    if sub:
        draw_text(d, (x, y + size * 0.78), sub, font('sb', size * 0.28), MUTED, 'mm', a=a, spacing=2)


def fmt_int(n):
    return f"{int(round(n)):,}"


# ---------------------------------------------------------------- imágenes para calcas
def tex(w, h, bg, draw_fn):
    img = Image.new('RGBA', (w, h), bg)
    draw_fn(ImageDraw.Draw(img), img)
    return img


def grad_tex(w, h, c1, c2, vertical=True):
    a = np.linspace(0, 1, h if vertical else w)
    c = np.array(c1)[None, :] * (1 - a[:, None]) + np.array(c2)[None, :] * a[:, None]
    if vertical:
        arr = np.repeat(c[:, None, :], w, 1)
    else:
        arr = np.repeat(c[None, :, :], h, 0)
    rgba = np.concatenate([arr, np.full(arr.shape[:2] + (1,), 255)], 2).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')
