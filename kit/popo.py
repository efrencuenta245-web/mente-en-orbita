"""Mente en órbita — El Popocatépetl por dentro (serie "Lo que no ves") · video 10.
Escenas: azotea de la CDMX al amanecer con el Popo y el Izta (exhalaciones, zoom de 72 km) · bloque geológico con el
escáner de rayos X (sello) · glifo náhuatl · magma y gases · tomografía UNAM con IA (columna de Torres Latinoamericanas) ·
bolsas de magma · explosión y ceniza · aeropuerto cerrado (2023) · mapa: 25 millones a menos de 100 km · estación de
monitoreo y semáforo amarillo fase 2 · regreso a la azotea (loop) con llamado a compartir."""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
import vasec as VS  # reutiliza sombreado, tubos, blobs, fondos (fija anim.PHR al importarse; se sobrescribe abajo)
from nc import proj, P2, vis
from fo import clip_near, line3
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of, VIOLET, BLUE, CYAN, ORANGE)
from gps_geo import (norm, cam_from, cam_keys, polyline3, glow_dot)
import gps_earth as ge
import moto_model as mm
from vasec import org_faces, draw_faces, glass, blob, tube, catmull, arclen, at_s, bg_studio, vnoise, rot_x, rot_y, rot_z

FPS = 24
RED = (255, 90, 90)
GREEN = (90, 255, 150)
GOLD = (255, 205, 100)
MAGMA = (240, 96, 30)
SCAN = (120, 235, 255)

PHR = [
    (0.3, 5.8, "A 72 kilómetros de la Ciudad de México, un volcán exhaló 42 veces en un solo día.", {12}),
    (6.3, 7.8, "Así se ve por dentro.", {4}),
    (8.3, 11.0, "Popocatépetl, en náhuatl: «el monte que humea».", {4, 6}),
    (11.5, 14.8, "Debajo hay magma: roca derretida que suelta vapor y gases.", {2}),
    (15.3, 18.2, "Cada exhalación es ese gas escapando por el cráter.", {4}),
    (18.7, 23.6, "La UNAM le hizo una tomografía con inteligencia artificial... hasta 18 kilómetros de profundidad: como 100 Torres Latinoamericanas.", {4, 14}),
    (24.1, 26.6, "Y encontró bolsas de magma a distintas profundidades.", {2, 3, 4}),
    (27.1, 32.2, "Si el cráter se tapa, el gas se acumula y explota: la ceniza viaja con el viento.", {10}),
    (32.7, 37.1, "En 2023, la ceniza cerró el aeropuerto de la Ciudad de México casi seis horas.", {4}),
    (37.6, 41.4, "Unos 25 millones de personas viven a menos de 100 kilómetros.", {1, 2}),
    (41.9, 46.2, "Por eso lo vigilan día y noche. Hoy sigue en amarillo, fase 2.", {10}),
    (46.7, 51.9, "Mándaselo a alguien que vive cerca del Popo. ¿Lo has visto echar fumarola? Sí o no.", {0, 15}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)
_ST = [list(ph['starts']) for ph in anim.PH]


def WT(i, w):
    return _ST[i][w]


CUTS = (6.05, 11.25, 18.45, 23.85, 26.85, 32.45, 37.35, 41.65, 46.45)
ENVS = ('roof', 'block', 'magma', 'tomo', 'pockets', 'blast', 'airport', 'map', 'station', 'roof2')
T_OUT = 52.25
DUR = 54.6
NF = int(DUR * FPS)


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


# =====================================================================
# Relieve (km). x = este, z = norte, y = altura sobre el fondo del valle
# =====================================================================
def h_popo(x, z):
    r = math.hypot(x, z)
    th = math.atan2(z, x)
    base = 3.25 * math.exp(-(r / 5.2) ** 1.35)
    crater = 0.30 * max(0.0, 1 - (r / 0.45) ** 2)
    gul = -0.05 * (0.5 + 0.5 * math.sin(11 * th + 2.0 * r)) * min(1.0, r / 1.0) * math.exp(-r / 6.0)
    lump = 0.03 * math.sin(3 * th + 1.3) * math.exp(-((r - 6) / 3) ** 2)
    return base - crater + gul + lump


IZTA_C = np.array([-2.0, 0.0, 17.8])


def h_izta(x, z):
    u, v = x - IZTA_C[0], z - IZTA_C[2]
    bumps = max(0.92 * math.exp(-((v - 5.2) / 1.4) ** 2), 1.0 * math.exp(-((v - 0.6) / 2.0) ** 2), 0.9 * math.exp(-((v + 4.0) / 1.8) ** 2))
    ridge = 2.95 * bumps * math.exp(-(u / (2.3 + 0.3 * math.sin(v))) ** 2)
    saddle = 1.1 * math.exp(-(u / 5.0) ** 2) * math.exp(-(v / 8.0) ** 2)
    return max(ridge, saddle)


def _rnd(x, z):
    v = math.sin(x * 12.9898 + z * 78.233) * 43758.5453
    return v - math.floor(v)


def terr_col(h, x, z, kind='popo'):
    n = 0.5 + 0.5 * math.sin(x * 3.1 + z * 2.3) * math.sin(x * 1.7 - z * 2.9)
    rn = _rnd(x, z)
    snow_line = 2.9 if kind == 'popo' else 2.45
    if h > snow_line and (rn > 0.45 or h > 3.05) and kind == 'izta' or (kind == 'popo' and h > snow_line and rn > 0.55):
        return lc((226, 230, 236), (240, 242, 246), rn)
    if h > 2.2:
        return lc(lc((96, 90, 88), (122, 106, 96), n), (80, 76, 74), rn * 0.5)
    if h > 2.2:
        return lc((96, 90, 88), (122, 106, 96), n)
    if h > 1.6:
        return lc((126, 114, 80), (106, 98, 72), n)
    return lc((46, 74, 44), (62, 86, 52), n)


def _quad(m, pts, col, tag):
    p = [np.asarray(q, np.float64) for q in pts]
    nn = np.cross(p[2] - p[0], p[1] - p[3]) if len(p) == 4 else np.cross(p[1] - p[0], p[2] - p[0])
    nn = norm(nn)
    if nn[1] < 0:
        nn = -nn
        p = p[::-1]
    m.face(p, nn, col, tag)


RINGS = [0.0, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0, 1.3, 1.7, 2.2, 2.8, 3.5, 4.3, 5.2, 6.2, 7.4, 8.8, 10.4, 12.2, 14.2]


def build_popo(nsec=64, rmax=None, tag_fn=None):
    m = mm.Model()
    rings = [r for r in RINGS if rmax is None or r <= rmax + 1e-9]
    for i in range(len(rings) - 1):
        for j in range(nsec):
            a0, a1 = 2 * math.pi * j / nsec, 2 * math.pi * (j + 1) / nsec
            pts = []
            for (r, a) in ((rings[i], a0), (rings[i], a1), (rings[i + 1], a1), (rings[i + 1], a0)):
                x, z = r * math.cos(a), r * math.sin(a)
                pts.append((x, h_popo(x, z), z))
            if rings[i] == 0.0:
                pts = [pts[0], pts[2], pts[3]]
            cx = sum(p[0] for p in pts) / len(pts)
            cz = sum(p[2] for p in pts) / len(pts)
            ch = sum(p[1] for p in pts) / len(pts)
            _quad(m, pts, terr_col(ch, cx, cz), tag_fn(cx, ch, cz) if tag_fn else 'popo')
    return m


def build_izta():
    m = mm.Model()
    us = np.linspace(-6.5, 6.5, 18)
    vs = np.linspace(-9.5, 9.5, 30)
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            pts = []
            for (u, v) in ((us[i], vs[j]), (us[i + 1], vs[j]), (us[i + 1], vs[j + 1]), (us[i], vs[j + 1])):
                x, z = IZTA_C[0] + u, IZTA_C[2] + v
                pts.append((x, h_izta(x, z), z))
            ch = sum(p[1] for p in pts) / 4
            _quad(m, pts, terr_col(ch, pts[0][0], pts[0][2], 'izta'), 'izta')
    return m


POPO = build_popo()
RINGS_HI = [0.0, 0.08, 0.16, 0.24, 0.32, 0.40, 0.45, 0.5, 0.58, 0.68, 0.8, 0.95, 1.12, 1.32, 1.55, 1.85, 2.2, 2.65, 3.2, 3.9, 4.8, 6.0, 7.5, 9.5, 12.0, 14.2]


def build_popo_hi(nsec=120):
    global RINGS
    old = RINGS
    RINGS = RINGS_HI
    m = build_popo(nsec)
    RINGS = old
    return m


POPO_HI = build_popo_hi()
IZTA = build_izta()
CRATER = np.array([0.0, h_popo(0, 0), 0.0])
CRATER_TOP = np.array([0.0, 3.14, 0.0])

# =====================================================================
# Cielo y suelo del valle (km) por píxel
# =====================================================================
CDMX = np.array([-53.6, 0.0, 45.5])
PUEBLA = np.array([44.0, 0.0, 2.0])
SUN_D = norm(np.array([math.sin(math.radians(108)) * math.cos(math.radians(2.5)), math.sin(math.radians(2.5)),
                       math.cos(math.radians(108)) * math.cos(math.radians(2.5))]))
L_DAWN = norm(np.array([0.85, 0.32, -0.3]))


def _h2(i, j, seed):
    n = (i * 374761393 + j * 668265263 + seed * 1013904223) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF).astype(np.float32) / 65535.0


def dawn_sky(dx, dy, dz, hazy=0.0):
    e = np.clip(dy, -0.3, 1.0).astype(np.float32)
    cosang = np.clip(dx * SUN_D[0] + dy * SUN_D[1] + dz * SUN_D[2], -1, 1)
    ang = np.arccos(cosang).astype(np.float32)
    hz = np.array([248, 176, 120], np.float32)
    mid = np.array([150, 150, 190], np.float32)
    top = np.array([46, 70, 132], np.float32)
    k1 = np.clip(e / 0.10, 0, 1)[..., None]
    k2 = np.clip((e - 0.10) / 0.55, 0, 1)[..., None]
    warm = np.clip(0.35 + 0.65 * (dx * 0.8 - dz * 0.3), 0, 1).astype(np.float32)[..., None]
    sky = (hz * (0.6 + 0.4 * warm) * (1 - k1) + mid * k1) * (1 - k2) + top * k2
    glow = (np.exp(-ang / 0.05) * 1.6 + np.exp(-ang / 0.35) * 0.55)[..., None]
    sky = sky + glow * np.array([255, 196, 130], np.float32)
    if hazy > 0:
        gray = np.array([170, 162, 152], np.float32)
        sky = sky * (1 - hazy) + gray * hazy * (0.8 + 0.3 * k1)
    return sky


def valley(c, mode='dawn', hazy=0.0, map_mode=False):
    dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
    out = dawn_sky(dx, dy, dz, hazy)
    cam = c['pos']
    m = dy < -1e-5
    tt = (0.0 - cam[1]) / np.where(m, dy, -1.0)
    gx, gz = cam[0] + tt * dx, cam[2] + tt * dz
    x, z, d = gx[m], gz[m], tt[m]
    # campo
    n1 = vnoise(x, z, 0.35, 1)
    n2 = vnoise(x, z, 2.5, 2)
    n3 = vnoise(x, z, 12.0, 3)
    a1 = np.clip(0.35 * 900.0 / d, 0, 1)
    farm = np.array([104, 114, 72], np.float32) * (1 - n3[:, None]) + np.array([140, 124, 86], np.float32) * n3[:, None]
    farm = farm * (0.85 + 0.15 * ((n1 - 0.5) * a1 + 0.5)[:, None] + 0.12 * (n2 - 0.5)[:, None])
    # ciudad (CDMX y Puebla)
    du = np.hypot(x - CDMX[0], z - CDMX[2])
    dp = np.hypot(x - PUEBLA[0], z - PUEBLA[2])
    urb = np.clip((22 - du) / 6, 0, 1) * (0.75 + 0.25 * vnoise(x, z, 3.0, 5)) + np.clip((9 - dp) / 3, 0, 1)
    urb = np.clip(urb, 0, 1)
    if urb.max() > 0:
        bs = 0.11
        bx, bz = np.floor(x / bs).astype(np.int64), np.floor(z / bs).astype(np.int64)
        fx, fz = x / bs - bx, z / bs - bz
        hsh = _h2(bx, bz, 7)
        roof = np.array([150, 146, 140], np.float32)[None, :] * (0.78 + 0.4 * hsh[:, None])
        terr = (hsh > 0.8)
        roof[terr] = np.array([152, 98, 74], np.float32) * (0.85 + 0.3 * hsh[terr, None])
        street = (fx < 0.14) | (fz < 0.14)
        roof[street] = np.array([84, 84, 88], np.float32)
        det = np.clip(bs * 1200.0 / d, 0, 1)[:, None]
        mean = np.array([128, 124, 118], np.float32)
        city = roof * det + mean * (1 - det)
        if mode == 'dawn' and not map_mode:
            lit = street & (_h2(bx * 7 + 3, bz * 5 + 1, 9) > 0.9)
            city[lit] += np.array([120, 80, 40], np.float32) * det[lit]
        col = farm * (1 - urb[:, None]) + city * urb[:, None]
    else:
        col = farm
    lightk = 0.78 if mode == 'dawn' else 1.0
    col = col * lightk
    if not map_mode:
        f = (1 - np.exp(-d / 38.0))[:, None].astype(np.float32)
        fogc = dawn_sky(dx[m] * 0 + 0.7, np.full_like(dy[m], 0.02), dz[m] * 0 - 0.6, hazy)[..., :3] if False else np.array([206, 170, 150], np.float32)
        if hazy > 0:
            fogc = np.array([160, 154, 146], np.float32)
        col = col * (1 - 0.85 * f) + fogc * 0.85 * f
    out[m] = col
    return out.astype(np.float32)


def far_ridge(bd, c, seed=2):
    rs = np.random.RandomState(seed)
    pts = []
    for k in range(121):
        a = 2 * math.pi * k / 120
        r = 115.0
        hh = 0.6 + 1.2 * (0.5 + 0.5 * math.sin(a * 5 + 1.1)) * (0.7 + 0.3 * rs.rand())
        pts.append((CDMX[0] * 0.5 + r * math.cos(a), hh, CDMX[2] * 0.5 + r * math.sin(a)))
    for i in range(120):
        p0, p1 = pts[i], pts[i + 1]
        quad = [p0, p1, (p1[0], -0.2, p1[2]), (p0[0], -0.2, p0[2])]
        q = clip_near(quad, c, 0.5)
        if len(q) >= 3:
            bd.polygon([P2(*p, c) for p in q], fill=(118, 100, 116))


# =====================================================================
# Azotea en la CDMX (objetos en metros convertidos a km)
# =====================================================================
F_ROOF = np.array([0.0, 1.7, 0.0])
EYEM = 32.0
EYE = np.array([CDMX[0], EYEM / 1000.0, CDMX[2]])
_v = EYE - F_ROOF
D0 = float(np.linalg.norm(_v))
PHI0 = math.degrees(math.asin(_v[1] / D0))
_cp = math.cos(math.radians(PHI0))
YAW0 = math.degrees(math.atan2(_v[0] / (D0 * _cp), -_v[2] / (D0 * _cp)))
FWD = norm(np.array([-_v[0], 0.0, -_v[2]]))
UP = np.array([0.0, 1.0, 0.0])
RIGHT = norm(np.cross(UP, FWD))
_c0 = cam_from(D0, PHI0, YAW0, 640, tuple(F_ROOF))
if proj(*(EYE + (FWD * 10 + RIGHT * 3) * 0.001), _c0)[0] < 540:
    RIGHT = -RIGHT
RM_ROOF = np.column_stack([RIGHT, UP, FWD])


def to_world(local_model, origin=EYE, scale=0.001):
    out = mm.Model()
    for (pts, n, col, tag) in local_model.F:
        Wp = (pts * scale) @ RM_ROOF.T + origin
        out.face(Wp, norm(RM_ROOF @ n), col, tag)
    return out


def build_roof():
    m = mm.Model()
    ry = -1.6  # nivel de la azotea respecto al ojo (m)
    g = -EYEM  # nivel del suelo
    conc, paint = (176, 170, 162), (198, 150, 112)
    m.box((-6, g, -8.0), (6, ry, 3.0), (184, 176, 166))
    m.box((-6, ry - 0.05, -8.0), (6, ry, 3.0), (150, 146, 140), 'floor')
    m.box((-6, ry, 2.9), (6, ry + 0.12, 3.0), paint)
    # tinaco
    m.box((-1.55, ry, 2.0), (-0.55, ry + 0.35, 2.9), conc)
    m.cyl((-1.05, ry + 0.95, 2.45), (0, 1, 0), 0.48, 1.2, (34, 34, 38), 18, 'body', True, (44, 44, 50))
    m.cyl((-1.05, ry + 1.6, 2.45), (0, 1, 0), 0.25, 0.14, (44, 44, 50), 14)
    # castillo con varillas
    m.box((0.45, ry, 2.55), (0.75, ry + 0.6, 2.85), (166, 160, 152))
    for (dx_, dz_) in ((-0.08, -0.08), (0.08, -0.08), (-0.08, 0.08), (0.08, 0.08)):
        m.beam((0.6 + dx_, ry + 0.6, 2.7 + dz_), (0.6 + dx_ * 1.6, ry + 1.5, 2.7 + dz_ * 1.6), 0.025, 0.025, (128, 76, 48))
    # antena de TV
    m.beam((1.2, ry, 2.8), (1.2, ry + 3.0, 2.8), 0.04, 0.04, (176, 180, 186))
    for k in range(4):
        y_ = ry + 2.0 + k * 0.28
        w = 0.6 - 0.1 * k
        m.beam((1.2 - w, y_, 2.8), (1.2 + w, y_, 2.8), 0.025, 0.025, (176, 180, 186))
    # vecino de enfrente con tendedero
    top = g + 26.0
    m.box((-4.0, g, 7.0), (3.5, top, 15.0), (200, 160, 130))
    m.box((-4.0, top, 14.8), (3.5, top + 0.8, 15.0), (210, 172, 140))
    cols = [(220, 70, 70), (70, 120, 210), (240, 220, 90), (240, 240, 240), (120, 200, 140)]
    for x_ in (-3.2, 2.6):
        m.beam((x_, top, 11.0), (x_, top + 1.7, 11.0), 0.06, 0.06, (120, 122, 128))
    for k, xc in enumerate((-2.4, -1.3, -0.2, 0.9, 1.9)):
        m.face([(xc - 0.4, top + 1.65, 11.0), (xc + 0.4, top + 1.65, 11.0), (xc + 0.4, top + 0.9, 11.0), (xc - 0.4, top + 0.9, 11.0)], (0, 0, -1), cols[k])
        m.face([(xc + 0.4, top + 1.65, 11.0), (xc - 0.4, top + 1.65, 11.0), (xc - 0.4, top + 0.9, 11.0), (xc + 0.4, top + 0.9, 11.0)], (0, 0, 1), cols[k])
    m.cyl((2.4, top + 0.65, 8.5), (0, 1, 0), 0.55, 1.3, (34, 34, 38), 14)
    # azoteas vecinas (más bajas)
    rs = np.random.RandomState(12)
    for k in range(90):
        zf = 20 + rs.uniform(0, 1) ** 1.5 * 420
        xr = rs.uniform(-1.0, 1.0) * (14 + zf * 0.55)
        top = g + rs.uniform(6, 24)
        wdt, dep = rs.uniform(8, 18), rs.uniform(8, 18)
        col = [(176, 170, 162), (200, 160, 130), (214, 196, 160), (160, 150, 170), (190, 120, 110), (226, 222, 214)][rs.randint(0, 6)]
        m.box((xr - wdt / 2, g, zf), (xr + wdt / 2, top, zf + dep), col)
        if rs.rand() < 0.7:
            tx, tz = xr + rs.uniform(-wdt / 3, wdt / 3), zf + rs.uniform(1, dep - 1)
            m.cyl((tx, top + 0.65, tz), (0, 1, 0), 0.55, 1.3, (34, 34, 38), 10)
    return m


ROOF = to_world(build_roof())

# =====================================================================
# Exhalaciones (km, tiempo acelerado)
# =====================================================================
WIND = np.array([0.55, 0.0, 0.12])


def puffs(od, c, t, t0, t1, n, near=0.3, scale=1.0, alpha=1.0):
    times = np.linspace(t0, t1, n)
    out = 0
    for i, ti in enumerate(times):
        a = t - ti
        if a < 0 or a > 3.2:
            continue
        out += 1
        rise = 1.0 * (1 - math.exp(-a * 1.3)) * scale
        p = CRATER_TOP + np.array([0, 0.15 + rise, 0]) + WIND * a * scale + np.array([0.05 * math.sin(i * 1.7), 0, 0.05 * math.cos(i)])
        x, y, dep = proj(*p, c)
        if dep < near:
            continue
        rr = (0.18 + 0.32 * a) * scale * 1200.0 / dep * S
        al = int(200 * alpha * max(0.0, 1 - a / 3.2) * min(1.0, a / 0.15))
        col = lc((240, 238, 236), (196, 194, 198), min(1.0, a / 2.5))
        od.ellipse((x * S - rr, y * S - rr * 0.8, x * S + rr, y * S + rr * 0.8), fill=(*[int(v) for v in col], al))
    return out


# =====================================================================
# Bloque geológico (km) con corte en z = 0
# =====================================================================
XS = np.array([-22, -17, -13, -10, -8, -6.5, -5.2, -4.2, -3.4, -2.7, -2.1, -1.6, -1.2, -0.85, -0.55, -0.3, -0.1,
               0.1, 0.3, 0.55, 0.85, 1.2, 1.6, 2.1, 2.7, 3.4, 4.2, 5.2, 6.5, 8, 10, 13, 17, 22], float)
ZB = np.array([0, 0.15, 0.4, 0.8, 1.3, 2.0, 2.9, 4.0, 5.5, 7.3, 9.5, 12.0])
DEEP = -18.0


def build_block():
    back, front = mm.Model(), mm.Model()
    for (zs, mdl, sgn) in ((ZB, back, 1), (-ZB, front, -1)):
        for i in range(len(XS) - 1):
            for j in range(len(zs) - 1):
                pts = []
                for (x, z) in ((XS[i], zs[j]), (XS[i + 1], zs[j]), (XS[i + 1], zs[j + 1]), (XS[i], zs[j + 1])):
                    pts.append((x, h_popo(x, z), z))
                ch = sum(p[1] for p in pts) / 4
                tag = 'top' if sgn > 0 else 'f%02d' % int(clamp((ch + 20) / 0.6, 0, 99))
                _quad(mdl, pts, terr_col(ch, pts[0][0], pts[0][2]), tag)
    # caras laterales
    for (mdl, z0, z1, sgn) in ((back, 0.0, 12.0, 1), (front, -12.0, 0.0, -1)):
        for xs_ in (-22.0, 22.0):
            nx = 1.0 if xs_ > 0 else -1.0
            zs_ = np.linspace(z0, z1, 7)
            for k in range(6):
                za, zb = zs_[k], zs_[k + 1]
                for (ya, yb, col) in ((0.0, -4.0, (120, 102, 84)), (-4.0, -10.0, (100, 88, 78)), (-10.0, DEEP, (78, 72, 68))):
                    pts = [(xs_, ya, za), (xs_, ya, zb), (xs_, yb, zb), (xs_, yb, za)]
                    if nx < 0:
                        pts = pts[::-1]
                    tag = 'side' if sgn > 0 else 'f%02d' % int(clamp(((ya + yb) / 2 + 20) / 0.6, 0, 99))
                    mdl.face(pts, (nx, 0, 0), col, tag)
    # frente del bloque completo (z = -12)
    for k in range(len(XS) - 1):
        for (ya, yb, col) in ((0.0, -4.0, (124, 106, 88)), (-4.0, -10.0, (104, 92, 82)), (-10.0, DEEP, (82, 76, 72))):
            pts = [(XS[k + 1], ya, -12.0), (XS[k], ya, -12.0), (XS[k], yb, -12.0), (XS[k + 1], yb, -12.0)]
            front.face(pts, (0, 0, -1), col, 'f%02d' % int(clamp(((ya + yb) / 2 + 20) / 0.6, 0, 99)))
    return back, front


BLOCK_BACK, BLOCK_FRONT = build_block()
XPROF = np.linspace(-22, 22, 121)
HPROF = np.array([h_popo(x, 0.0) for x in XPROF])
CHAMBERS = [((0.6, -5.2), (2.2, 0.85)), ((-1.0, -9.6), (3.0, 1.15)), ((0.9, -14.6), (3.6, 1.35))]


def section_polys():
    """polígonos del corte (z = 0): capas del volcán y de la corteza"""
    out = []
    layers = [1.0, 0.78, 0.56, 0.34, 0.12]
    vcols = [(96, 88, 84), (122, 106, 94), (90, 82, 80), (116, 100, 90), (100, 92, 86)]
    for k in range(len(layers)):
        top = [(x, max(0.0, h * layers[k]), 0.0) for x, h in zip(XPROF, HPROF)]
        bot = [(x, max(0.0, h * (layers[k + 1] if k + 1 < len(layers) else 0.0)), 0.0) for x, h in zip(XPROF, HPROF)]
        out.append((top + bot[::-1], vcols[k]))
    depths = [0.0, -2.6, -6.4, -10.4, -14.2, DEEP]
    ccols = [(132, 112, 90), (114, 98, 82), (98, 88, 80), (84, 78, 74), (70, 66, 64)]
    for k in range(len(depths) - 1):
        top = [(x, depths[k] + (0.25 * math.sin(x * 0.35 + k) if k > 0 else 0.0), 0.0) for x in XPROF]
        bot = [(x, depths[k + 1] + (0.25 * math.sin(x * 0.35 + k + 1) if k + 1 < len(depths) - 1 else 0.0), 0.0) for x in XPROF]
        out.append((top + bot[::-1], ccols[k]))
    return out


SECTION = section_polys()


def conduit_poly():
    ys = np.linspace(CRATER[1], -4.5, 40)
    left, right = [], []
    for y in ys:
        wob = 0.25 * math.sin(y * 0.9)
        w = 0.22 + 0.06 * math.sin(y * 2.1)
        left.append((wob - w, y, -0.01))
        right.append((wob + w, y, -0.01))
    return left + right[::-1]


CONDUIT = conduit_poly()


def ell_pts(cx, cy, rx, ry, n=40, z=-0.02, wob=0.08, ph=0.0):
    return [(cx + rx * math.cos(a) * (1 + wob * math.sin(3 * a + ph)), cy + ry * math.sin(a) * (1 + wob * math.cos(2 * a + ph)), z)
            for a in np.linspace(0, 2 * math.pi, n + 1)[:-1]]


def draw_poly3(d, c, pts, col, near=0.5):
    q = clip_near([tuple(p) for p in pts], c, near)
    if len(q) >= 3:
        d.polygon([P2(*p, c) for p in q], fill=col)


def draw_block(base, bd, od, la, c, t, scan_y=99.0, glow=1.0, chambers_k=1.0, show_magma=True):
    L = norm((0.5, 0.75, -0.45))
    fl = org_faces(c, BLOCK_BACK, L, {}, near=0.5, default={'spec': 0.08})
    draw_faces(bd, od, fl)
    for (pts, col) in SECTION:
        draw_poly3(bd, c, pts, col)
    if show_magma:
        draw_poly3(bd, c, CONDUIT, (214, 84, 30))
        draw_poly3(la, c, CONDUIT, sc3((120, 40, 10), glow))
        for k, ((cx, cy), (rx, ry)) in enumerate(CHAMBERS):
            pul = 0.85 + 0.15 * math.sin(t * 2.0 + k)
            draw_poly3(bd, c, ell_pts(cx, cy, rx, ry, ph=k), sc3(lc((150, 60, 30), (230, 100, 36), chambers_k), 1.0))
            draw_poly3(la, c, ell_pts(cx, cy, rx * 0.8, ry * 0.7, ph=k + 1), sc3((150, 56, 14), glow * chambers_k * pul))
    # mitad delantera: opaca debajo del escáner, fantasma arriba
    st = {}
    for k in range(100):
        yc = -20 + (k + 0.5) * 0.6
        if yc > scan_y:
            st['f%02d' % k] = {'alpha': 34, 'spec': 0.0}
    flf = org_faces(c, BLOCK_FRONT, L, st, near=0.5, default={'spec': 0.08})
    draw_faces(bd, od, flf)
    # aristas del bloque
    w = max(1, int(1.5 * S))
    edges = [((-22, 0, -12), (22, 0, -12)), ((-22, DEEP, -12), (22, DEEP, -12)), ((-22, 0, -12), (-22, DEEP, -12)), ((22, 0, -12), (22, DEEP, -12)),
             ((22, 0, -12), (22, 0, 12)), ((22, DEEP, -12), (22, DEEP, 12)), ((22, 0, 12), (22, DEEP, 12)), ((-22, 0, 12), (22, 0, 12))]
    for (p0, p1) in edges:
        line3(la, c, p0, p1, sc3((120, 150, 190), 0.35), w, 0.5)


def scan_ring(la, c, ys, a=1.0):
    """anillo del escáner (sello): contorno del bloque y del cono a la altura ys"""
    if a <= 0.01:
        return
    w = max(2, int(4 * S))
    col = sc3(SCAN, a)
    if ys > 0.05:
        # radio del cono a esa altura
        lo, hi = 0.0, 14.2
        for _ in range(30):
            mid = (lo + hi) / 2
            if 3.25 * math.exp(-(mid / 5.2) ** 1.35) > ys:
                lo = mid
            else:
                hi = mid
        r = lo
        pts = [(r * math.cos(q), ys, r * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 73)]
        polyline3(la, c, pts, col, w, 0.5)
    yy = min(ys, 0.0)
    pts = [(-22, yy, -12), (22, yy, -12), (22, yy, 12), (-22, yy, 12), (-22, yy, -12)]
    polyline3(la, c, pts, col, w, 0.5)
    polyline3(la, c, [(-22, yy + 0.3, -12), (22, yy + 0.3, -12)], sc3(SCAN, 0.4 * a), max(1, int(2 * S)), 0.5)


# =====================================================================
# Tomografía
# =====================================================================
_rs = np.random.RandomState(21)
SENSORS = []
for _k in range(22):
    _r = 1.2 + 8.0 * (_k / 21.0) ** 0.8
    _a = _k * 2.4 + 0.3
    _x, _z = _r * math.cos(_a), _r * math.sin(_a)
    SENSORS.append(np.array([_x, h_popo(_x, _z) + 0.05, _z]))
QUAKES = [(18.7 + 0.42 * k, np.array([_rs.uniform(-9, 9), _rs.uniform(-16, -1.5), 0.0])) for k in range(14)]


def anomaly(x, y):
    v = 0.0
    for (cx, cy), (rx, ry) in CHAMBERS:
        v = max(v, math.exp(-(((x - cx) / (rx * 1.15)) ** 2 + ((y - cy) / (ry * 1.6)) ** 2)))
    if abs(x - 0.25 * math.sin(y * 0.9)) < 0.6 and y > -4.8:
        v = max(v, 0.8)
    return v


VOX = [(x0, y0, anomaly(x0 + 1.0, y0 - 0.75)) for x0 in np.arange(-20, 20, 2.0) for y0 in np.arange(0, DEEP, -1.5)]


def draw_tomo(od, la, c, t, t0, t1):
    prog = clamp((t - t0) / (t1 - t0))
    sweep = -20 + 40 * prog
    for (x0, y0, v) in VOX:
        if x0 > sweep:
            continue
        col = sc3(lc((40, 110, 170), (250, 110, 40), v ** 0.7), 1.0)
        pts = [(x0 + 0.08, y0 - 0.08, -0.03), (x0 + 1.92, y0 - 0.08, -0.03), (x0 + 1.92, y0 - 1.42, -0.03), (x0 + 0.08, y0 - 1.42, -0.03)]
        q = clip_near(pts, c, 0.5)
        if len(q) >= 3:
            od.polygon([P2(*p, c) for p in q], fill=(*col, 120 + int(70 * v)))
    if 0 < prog < 1:
        line3(la, c, (sweep, 0.2, -0.05), (sweep, DEEP, -0.05), sc3(SCAN, 0.9), max(2, int(3 * S)), 0.5)


def draw_quakes(la, c, t):
    w = max(1, int(2 * S))
    for (tq, p) in QUAKES:
        a = t - tq
        if a < 0 or a > 1.6:
            continue
        r = 9.0 * a
        pts = [(p[0] + r * math.cos(q), p[1] + r * math.sin(q), -0.05) for q in np.linspace(0, 2 * math.pi, 49)]
        polyline3(la, c, pts, sc3((255, 220, 140), 0.8 * (1 - a / 1.6)), w, 0.5)
        x, y, dep = proj(*p, c)
        glow_dot(la, x * S, y * S, 6 * S, (255, 230, 170), max(0.0, 1 - a / 0.6))
        for s in SENSORS[(int(tq * 10) % 5)::5]:
            k = clamp(a / 0.8)
            q_ = p + (s - p) * k
            line3(la, c, tuple(p), tuple(q_), sc3((255, 210, 140), 0.35 * (1 - a / 1.6)), max(1, int(1.5 * S)), 0.5)


def draw_sensors(la, c, a=1.0):
    for s in SENSORS:
        x, y, dep = proj(*s, c)
        if dep < 0.5:
            continue
        r = 7 * S
        la.polygon([(x * S, y * S - r), (x * S + r * 0.9, y * S + r * 0.6), (x * S - r * 0.9, y * S + r * 0.6)], fill=sc3(GREEN, a))


# =====================================================================
# Explosión (km)
# =====================================================================
T_BOOM = WT(7, 9) - 0.05
_rb = np.random.RandomState(5)
ASH = [(_rb.uniform(0, 0.5), _rb.normal(0, 0.35, 3), _rb.uniform(1.6, 2.4), _rb.uniform(0.6, 1.2)) for _ in range(150)]
BOMBS = [(_rb.normal(0, 0.9, 3) * np.array([1, 0, 1]) + np.array([0, _rb.uniform(1.2, 2.2), 0])) for _ in range(40)]
DOME = mm.Model()
blob(DOME, CRATER + np.array([0, 0.03, 0]), (0.24, 0.08, 0.24), (66, 58, 54), 'dome', nu=20, nv=8, bump=lambda u, v: 0.25 * math.sin(5 * u) * math.sin(3 * v))


def draw_blast(od, la, c, t):
    dt = t - T_BOOM
    if dt < 0:
        return
    # columna de ceniza
    items = []
    for (delay, off, vup, grow) in ASH:
        a = dt - delay
        if a <= 0:
            continue
        hgt = vup * (1 - math.exp(-a * 0.9)) * 2.2
        p = CRATER_TOP + off * np.array([1, 0.2, 1]) * (0.3 + a * 0.5) + np.array([0, hgt, 0]) + WIND * max(0.0, a - 1.2) * 1.2
        x, y, dep = proj(*p, c)
        if dep < 0.3:
            continue
        rr = (0.15 + 0.38 * a * grow) * 1200.0 / dep * S
        col = lc((82, 76, 72), (150, 144, 138), clamp(a / 3.0))
        items.append((dep, x * S, y * S, rr, col, int(235 * clamp(1.2 - a / 4.5))))
    items.sort(key=lambda q: -q[0])
    for dep, x, y, rr, col, al in items:
        od.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(*[int(v) for v in col], al))
    # fragmentos incandescentes
    for v in BOMBS:
        if dt > 2.4:
            break
        p = CRATER_TOP + v * dt + np.array([0, -0.55 * dt * dt, 0])
        x, y, dep = proj(*p, c)
        if dep > 0.3:
            glow_dot(la, x * S, y * S, 3.5 * S, (255, 150, 60), clamp(1 - dt / 2.4))
    if dt < 0.35:
        x, y, dep = proj(*CRATER_TOP, c)
        glow_dot(la, x * S, y * S, (60 + 300 * dt) * S, (255, 210, 160), 1 - dt / 0.35)


# =====================================================================
# Aeropuerto (metros)
# =====================================================================
def build_airport():
    m = mm.Model()
    glassc, wallc = (88, 116, 134), (206, 208, 210)
    m.box((-160, 0, 110), (160, 20, 150), wallc)
    m.face([(-160, 2, 109.9), (160, 2, 109.9), (160, 18, 109.9), (-160, 18, 109.9)], (0, 0, -1), glassc, 'win')
    m.box((-162, 20, 106), (162, 22, 152), (160, 162, 168))
    m.cyl((190, 32, 190), (0, 1, 0), 4, 64, (210, 210, 214), 16)
    m.cyl((190, 68, 190), (0, 1, 0), 8, 8, (70, 110, 130), 16, 'body', True, (150, 152, 158))
    # avión genérico
    fx = 0.0
    m.cyl((fx, 4.6, 40), (1, 0, 0), 2.0, 34, (236, 238, 240), 22)
    blob(m, (fx + 17, 4.6, 40), (3.2, 1.9, 1.9), (236, 238, 240), 'body', nu=18, nv=10, keep=lambda p: p[0] > 0)
    blob(m, (fx - 17, 5.0, 40), (4.0, 1.6, 1.6), (236, 238, 240), 'body', nu=18, nv=10, keep=lambda p: p[0] < 0)
    m.box((fx - 17, 3.3, 37.95), (fx + 17, 3.6, 38.0), (40, 80, 150))
    m.box((fx - 17, 3.3, 42.0), (fx + 17, 3.6, 42.05), (40, 80, 150))
    for s in (-1, 1):
        wing = [(fx + 4, 3.6, 40 + s * 1.9), (fx - 4, 3.6, 40 + s * 1.9), (fx - 10, 4.2, 40 + s * 17), (fx - 7.5, 4.2, 40 + s * 17)]
        m.face(wing if s > 0 else wing[::-1], (0, 1, 0), (214, 216, 220))
        m.face(wing[::-1] if s > 0 else wing, (0, -1, 0), (190, 192, 198))
        m.cyl((fx + 1.5, 2.4, 40 + s * 6.5), (1, 0, 0), 1.2, 4.2, (200, 202, 208), 16, 'body', True, (40, 42, 48))
        stab = [(fx - 15, 5.5, 40 + s * 1.2), (fx - 19, 5.5, 40 + s * 1.2), (fx - 21, 5.7, 40 + s * 6.5), (fx - 19.5, 5.7, 40 + s * 6.5)]
        m.face(stab if s > 0 else stab[::-1], (0, 1, 0), (214, 216, 220))
    m.face([(fx - 15, 6.4, 40), (fx - 20.5, 6.4, 40), (fx - 22, 12.5, 40), (fx - 19.5, 12.5, 40)], (0, 0, -1), (40, 80, 150))
    m.face([(fx - 20.5, 6.4, 40), (fx - 15, 6.4, 40), (fx - 19.5, 12.5, 40), (fx - 22, 12.5, 40)], (0, 0, 1), (40, 80, 150))
    for k in range(18):
        x = fx + 13 - k * 1.6
        m.face([(x, 5.3, 37.98), (x + 0.5, 5.3, 37.98), (x + 0.5, 5.9, 37.98), (x, 5.9, 37.98)], (0, 0, -1), (40, 44, 52))
    m.beam((fx + 11, 5.2, 38.6), (fx + 14, 6.0, 109), 3.0, 3.0, (176, 178, 184))
    m.box((fx + 10, 0, 100), (fx + 18, 6.5, 110), (170, 172, 178))
    return m


AIRPORT = build_airport()


def apron(c, hazy=0.55):
    dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
    out = dawn_sky(dx, dy, dz, hazy)
    cam = c['pos']
    m = dy < -1e-5
    tt = (0.0 - cam[1]) / np.where(m, dy, -1.0)
    gx, gz = cam[0] + tt * dx, cam[2] + tt * dz
    x, z, d = gx[m], gz[m], tt[m]
    n1 = vnoise(x, z, 3.0, 4)
    col = np.array([150, 150, 148], np.float32)[None, :] * (0.9 + 0.12 * n1[:, None])
    jx = (np.abs(((x + 3.75) % 7.5) - 3.75) < 0.06) | (np.abs(((z + 3.75) % 7.5) - 3.75) < 0.06)
    col[jx] *= 0.82
    yl = (np.abs(z - 20.0) < 0.25) & (x > -200)
    col[yl] = np.array([214, 184, 60], np.float32)
    ashk = vnoise(x, z, 6.0, 8)
    col = col * (1 - 0.25 * ashk[:, None]) + np.array([120, 116, 110], np.float32) * 0.25 * ashk[:, None]
    f = (1 - np.exp(-d / 500.0))[:, None].astype(np.float32)
    col = col * (1 - f) + np.array([160, 154, 146], np.float32) * f
    out[m] = col
    return out.astype(np.float32)


# =====================================================================
# Estación de monitoreo (km con objetos en metros)
# =====================================================================
ST_DIR = norm(np.array([-0.75, 0.0, -0.66]))
ST_R = 4.6
ST_P = ST_DIR * ST_R
ST_P = np.array([ST_P[0], h_popo(ST_P[0], ST_P[2]), ST_P[2]])
_up = np.array([0.0, 1.0, 0.0])
_tw = norm(-ST_DIR)
_rt = norm(np.cross(_up, _tw))
RM_ST = np.column_stack([_rt, _up, _tw])


def build_station():
    m = mm.Model()
    m.box((-0.5, 0, 6), (0.5, 0.9, 6.7), (232, 234, 236))
    m.box((-0.5, 0.9, 6), (0.5, 0.95, 6.7), (180, 184, 190))
    m.beam((1.4, 0, 6.3), (1.4, 4.2, 6.3), 0.08, 0.08, (170, 174, 180))
    m.box((1.15, 3.2, 6.15), (1.65, 3.55, 6.6), (230, 232, 236))
    m.cyl((1.4, 3.37, 6.05), (0, 0, -1), 0.12, 0.15, (40, 42, 50), 12)
    m.beam((0.8, 4.0, 6.3), (2.0, 4.0, 6.3), 0.04, 0.04, (170, 174, 180))
    for k in range(5):
        x = 0.9 + k * 0.25
        m.beam((x, 3.8, 6.3), (x, 4.2, 6.3), 0.02, 0.02, (170, 174, 180))
    pts = [(-2.2, 0.6, 5.2), (-0.9, 0.6, 5.2), (-0.9, 1.4, 6.0), (-2.2, 1.4, 6.0)]
    m.face(pts, norm(np.cross(np.array(pts[1]) - np.array(pts[0]), np.array(pts[3]) - np.array(pts[0]))) * -1, (30, 46, 92))
    m.face(pts[::-1], norm(np.cross(np.array(pts[1]) - np.array(pts[0]), np.array(pts[3]) - np.array(pts[0]))), (160, 164, 170))
    for (x, z) in ((-2.1, 5.3), (-1.0, 5.3)):
        m.beam((x, 0, z), (x, 0.6, z), 0.05, 0.05, (150, 154, 160))
    m.beam((-3.4, 0, 7.5), (-3.4, 1.8, 7.5), 0.06, 0.06, (170, 174, 180))
    blob(m, (-3.4, 1.9, 7.5), (0.22, 0.12, 0.22), (240, 242, 244), 'body', nu=14, nv=6, keep=lambda p: p[1] >= 0)
    m.box((2.6, 0, 8.0), (3.4, 0.25, 8.8), (150, 148, 144))
    return m


_eps = 0.05
_GX = (h_popo(ST_P[0] + _eps, ST_P[2]) - h_popo(ST_P[0] - _eps, ST_P[2])) / (2 * _eps)
_GZ = (h_popo(ST_P[0], ST_P[2] + _eps) - h_popo(ST_P[0], ST_P[2] - _eps)) / (2 * _eps)


def st_world(lp):
    w = ST_P + RM_ST @ (np.asarray(lp, np.float64) * 0.001)
    w = w.copy()
    w[1] += _GX * (w[0] - ST_P[0]) + _GZ * (w[2] - ST_P[2])
    return w


STATION = mm.Model()
for (_pts, _n, _col, _tag) in build_station().F:
    STATION.face(np.array([st_world(p_) for p_ in _pts]), norm(RM_ST @ _n), _col, _tag)
POPO_TOP = build_popo(64, rmax=4.3)


def slope_ground(c):
    """plano inclinado del volcán bajo la estación (arena volcánica)"""
    dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
    out = dawn_sky(dx, dy, dz, 0.0)
    eps = 0.05
    gxh = (h_popo(ST_P[0] + eps, ST_P[2]) - h_popo(ST_P[0] - eps, ST_P[2])) / (2 * eps)
    gzh = (h_popo(ST_P[0], ST_P[2] + eps) - h_popo(ST_P[0], ST_P[2] - eps)) / (2 * eps)
    n = norm(np.array([-gxh, 1.0, -gzh]))
    cam = np.asarray(c['pos'])
    den = dx * n[0] + dy * n[1] + dz * n[2]
    num = (ST_P - cam) @ n
    tt = num / np.where(np.abs(den) > 1e-9, den, 1e-9)
    m = (tt > 0) & (den < 0)
    gx, gz = cam[0] + tt * dx, cam[2] + tt * dz
    x, z, d = gx[m], gz[m], tt[m]
    n1 = vnoise(x * 1000, z * 1000, 0.6, 3)
    n2 = vnoise(x * 1000, z * 1000, 4.0, 4)
    rock = vnoise(x * 1000, z * 1000, 0.35, 6) > 0.82
    col = np.array([92, 84, 80], np.float32)[None, :] * (0.8 + 0.25 * n1[:, None] + 0.15 * n2[:, None])
    col[rock] = np.array([60, 56, 54], np.float32)
    f = np.clip(d / 6.0, 0, 0.7)[:, None]
    col = col * (1 - f) + np.array([200, 170, 156], np.float32) * f
    out[m] = col
    return out.astype(np.float32)


# =====================================================================
# Cámaras
# =====================================================================
_stc = ST_P + RM_ST @ np.array([0.0, 0.0016, 0.0])
_stv = (_stc - (CRATER_TOP + np.array([0, -0.2, 0])))
_stD = float(np.linalg.norm(_stv))
_stphi = math.degrees(math.asin(_stv[1] / _stD))
_stcp = math.cos(math.radians(_stphi))
_styaw = math.degrees(math.atan2(_stv[0] / (_stD * _stcp), -_stv[2] / (_stD * _stcp)))
_stf = tuple(CRATER_TOP + np.array([0, -0.2, 0]))
KEYS = {
    'roof': [(0.0, D0, PHI0, YAW0, 640, *F_ROOF), (0.9, D0 - 0.0015, PHI0, YAW0, 640, *F_ROOF), (6.05, 12.0, 9.0, YAW0 + 10, 900, 0, 2.4, 0)],
    'block': [(6.05, 64, 16, -22, 1060, 0, -7, 0), (11.25, 58, 20, -12, 1060, 0, -7, 0)],
    'magma': [(11.25, 19, 8, -12, 1000, 0.3, -1.5, 0), (18.45, 15, 6, -2, 980, 0.2, -0.5, 0)],
    'tomo': [(18.45, 74, 20, -28, 1040, -2.5, -8, 0), (23.85, 68, 16, -14, 1040, -2.5, -8, 0)],
    'pockets': [(23.85, 36, 6, 8, 1000, 0, -10, 0), (26.85, 32, 4, 16, 1000, 0, -10, 0)],
    'blast': [(26.85, 7.0, 9, -42, 1060, 0, 3.0, 0), (32.45, 11.0, 13, -28, 900, 0, 3.6, 0)],
    'airport': [(32.45, 95, 5, -24, 1020, 0, 9, 40), (37.35, 84, 7, -10, 1020, 0, 9, 40)],
    'map': [(37.35, 360, 78, 0, 1000, -12, 0, 10), (41.65, 330, 82, 8, 1000, -12, 0, 10)],
    'station': [(41.65, _stD, _stphi, _styaw, 1250, *_stf), (46.45, _stD - 0.0009, _stphi, _styaw, 1250, *_stf)],
    'roof2': [(46.45, D0, PHI0, YAW0, 640, *F_ROOF), (DUR, D0 - 0.002, PHI0, YAW0, 640, *F_ROOF)],
}
LOGD = {'roof': True, 'blast': True}


def cam_for(env, t):
    return cam_keys(t, KEYS[env], LOGD.get(env, False))


# =====================================================================
# Render
# =====================================================================
DARK = []
T_SCAN = WT(1, 0) + 0.1
L_KM = L_DAWN


def draw_landscape(bd, od, c, near=0.0005, roof=True):
    far_ridge(bd, c)
    fl = org_faces(c, POPO, L_KM, {}, near=0.05, default={'spec': 0.05})
    fl += org_faces(c, IZTA, L_KM, {}, near=0.05, default={'spec': 0.05})
    if roof:
        fl += org_faces(c, ROOF, L_KM, {}, near=near, default={'spec': 0.15})
    draw_faces(bd, od, fl)


def render(t):
    env = env_at(t)
    c = cam_for(env, t)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    info = {}

    if env in ('roof', 'roof2'):
        arr = valley(c, 'dawn')
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        draw_landscape(bd, od, c)
        if env == 'roof':
            info['n_puffs'] = puffs(od, c, t, 0.35, 5.55, 42)
        else:
            puffs(od, c, t, 46.5, DUR, 30)
        info['popo'] = proj(*CRATER_TOP, c)[:2]
        info['dist'] = math.hypot(c['pos'][0], c['pos'][2])
    elif env in ('block', 'magma', 'tomo', 'pockets'):
        base = Image.fromarray(bg_studio((14, 20, 38), (6, 8, 16), (26, 36, 60)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        if env == 'block':
            ys = lerp(3.6, DEEP - 0.5, ease(seg(t, T_SCAN, T_SCAN + 1.5)))
            draw_block(base, bd, od, la, c, t, scan_y=ys, glow=ease(seg(t, T_SCAN + 0.3, T_SCAN + 1.2)))
            if T_SCAN <= t <= T_SCAN + 1.6:
                scan_ring(la, c, ys, 1.0)
            puffs(od, c, t, 6.2, 11.2, 8, near=0.5, scale=1.6, alpha=0.8)
            info['crater'] = proj(*CRATER_TOP, c)[:2]
        elif env == 'magma':
            draw_block(base, bd, od, la, c, t, scan_y=-99, glow=1.0)
            # convección en la cámara superior
            (cx, cy), (rx, ry) = CHAMBERS[0]
            for k in range(26):
                q = t * 0.9 + k * 0.24
                p = (cx + rx * 0.7 * math.cos(q), cy + ry * 0.55 * math.sin(q), -0.05)
                x, y, dep = proj(*p, c)
                glow_dot(la, x * S, y * S, 3.2 * S, (255, 190, 90), 0.8)
            # burbujas de gas que suben por el conducto
            ka = ease(seg(t, WT(3, 8) - 0.3, WT(3, 8) + 0.3))
            for k in range(22):
                ph = ((t - 11.25) * 0.32 + k / 22.0) % 1.0
                y = lerp(-4.4, CRATER[1], ph)
                x0 = 0.25 * math.sin(y * 0.9) + 0.12 * math.sin(k * 2.1 + t * 3)
                x, yy, dep = proj(x0, y, -0.06, c)
                glow_dot(la, x * S, yy * S, (2.5 + 2.0 * ph) * S, (240, 244, 255), ka * (0.5 + 0.5 * ph))
            n = puffs(od, c, t, 12.0, 18.4, 9, near=0.3, scale=0.9, alpha=0.85)
            info['puff_count'] = sum(1 for ti in np.linspace(12.0, 18.4, 9) if ti <= t)
            info['chamber'] = (cx, cy + 0.2, -0.05)
            info['conduit'] = (0.2, -1.6, -0.05)
            info['crater'] = tuple(CRATER_TOP)
        elif env == 'tomo':
            draw_block(base, bd, od, la, c, t, scan_y=-99, glow=0.5, chambers_k=0.0, show_magma=False)
            draw_quakes(la, c, t)
            draw_sensors(la, c)
            draw_tomo(od, la, c, t, WT(5, 4) - 0.3, 23.5)
            y0 = proj(0.0, 0.0, 0.0, c)
            y1 = proj(0.0, DEEP, 0.0, c)
            info["ruler"] = ((975.0, y0[1]), (975.0, y1[1]))
            info['sensor'] = proj(*SENSORS[6], c)[:2]
        else:
            draw_block(base, bd, od, la, c, t, scan_y=-99, glow=1.0, chambers_k=1.0)
            for (x0, y0, v) in VOX:
                if v > 0.45:
                    pts = [(x0 + 0.08, y0 - 0.08, -0.03), (x0 + 1.92, y0 - 0.08, -0.03), (x0 + 1.92, y0 - 1.42, -0.03), (x0 + 0.08, y0 - 1.42, -0.03)]
                    q = clip_near(pts, c, 0.5)
                    if len(q) >= 3:
                        od.polygon([P2(*p, c) for p in q], fill=(250, 120, 50, 70))
            info['ch'] = [proj(cx, cy, -0.05, c)[:2] for (cx, cy), _ in CHAMBERS]
    elif env == 'blast':
        arr = valley(c, 'dawn', hazy=0.15)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        fl = org_faces(c, POPO_HI, L_KM, {}, near=0.05, default={'spec': 0.05})
        fl += org_faces(c, IZTA, L_KM, {}, near=0.05, default={'spec': 0.05})
        fl += org_faces(c, DOME, L_KM, {}, near=0.05, default={'spec': 0.1})
        draw_faces(bd, od, fl)
        if t < T_BOOM:
            puffs(od, c, t, 26.9, T_BOOM - 1.0, 4, near=0.3, scale=0.5, alpha=0.6)
            # el domo "tapa" el cráter: brillo de presión
            k = ease(seg(t, WT(7, 3), T_BOOM))
            x, y, dep = proj(*(CRATER + np.array([0, 0.06, 0])), c)
            glow_dot(la, x * S, y * S, (10 + 30 * k) * S, (255, 120, 60), 0.3 + 0.6 * k * (0.7 + 0.3 * math.sin(t * 20)))
        draw_blast(od, la, c, t)
        info['crater'] = proj(*CRATER_TOP, c)[:2]
        info['press'] = ease(seg(t, WT(7, 3) - 0.2, T_BOOM))
    elif env == 'airport':
        arr = apron(c, 0.55)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.3, 0.8, -0.5))
        fl = org_faces(c, AIRPORT, L, {'win': {'spec': 0.6}}, near=1.0, default={'spec': 0.25})
        draw_faces(bd, od, fl)
        rs = np.random.RandomState(3)
        for k in range(260):
            x0 = rs.uniform(0, W)
            sp = rs.uniform(40, 90)
            y = ((rs.uniform(0, H) + t * sp * S) % H)
            x = x0 + 18 * math.sin(t * 0.8 + k) * S
            r = rs.uniform(1.0, 2.6) * S
            od.ellipse((x - r, y - r, x + r, y + r), fill=(110, 104, 98, 170))
        od.rectangle((0, 0, W, H), fill=(120, 112, 100, 46))
        info['plane'] = proj(0, 6.5, 40, c)[:2]
    elif env == 'map':
        arr = valley(c, 'day', map_mode=True)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        fl = org_faces(c, POPO, norm((0.6, 0.7, -0.3)), {}, near=1.0, default={'spec': 0.05})
        fl += org_faces(c, IZTA, norm((0.6, 0.7, -0.3)), {}, near=1.0, default={'spec': 0.05})
        draw_faces(bd, od, fl)
        k = ease(seg(t, 37.6, 39.0))
        rr = 100.0 * k
        pts = [(rr * math.cos(q), 0.05, rr * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 121)]
        if rr > 0.5:
            polyline3(la, c, pts, sc3(CYAN, 0.9), max(2, int(4 * S)), 1.0)
            ring = [P2(*p, c) for p in pts]
            od.polygon(ring, fill=(90, 200, 255, 26))
        pts = [(12.0 * math.cos(q), 0.05, 12.0 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 61)]
        polyline3(la, c, pts, sc3(RED, 0.8), max(2, int(3 * S)), 1.0)
        cities = {'CDMX': CDMX, 'PUEBLA': PUEBLA, 'CUERNAVACA': np.array([-64.0, 0, -11.0]), 'TLAXCALA': np.array([40.0, 0, 33.0]), 'TOLUCA': np.array([-109.0, 0, 30.0])}
        info['cities'] = {}
        for name, p in cities.items():
            x, y, dep = proj(*p, c)
            glow_dot(la, x * S, y * S, 6 * S, (255, 255, 255), 0.9)
            info['cities'][name] = (x, y)
        info['popo'] = proj(0, 3.2, 0, c)[:2]
    elif env == 'station':
        arr = slope_ground(c)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        fl = org_faces(c, POPO_TOP, L_KM, {}, near=0.05, default={'spec': 0.05})
        fl += org_faces(c, STATION, L_KM, {}, near=0.0003, default={'spec': 0.3})
        draw_faces(bd, od, fl)
        puffs(od, c, t, 41.7, 46.4, 5, near=0.05, scale=0.7, alpha=0.8)
        def wp(lp):
            return st_world(lp)
        info['cam'] = proj(*wp((1.4, 3.37, 6.05)), c)[:2]
        info['seis'] = proj(*wp((3.0, 0.25, 8.4)), c)[:2]
        info['gps'] = proj(*wp((-3.4, 1.9, 7.5)), c)[:2]
        info['solar'] = proj(*wp((-1.5, 1.0, 5.6)), c)[:2]

    # ---------- composición ----------
    arr = np.asarray(base, np.float32)
    imgA = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")
    LAa = np.asarray(LA, np.float32)
    gl = glow_of(LA, 4)
    out = np.asarray(imgB, np.float32) + LAa + 1.3 * gl
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    out = out * (0.5 + 0.5 * np.clip(yy / (H * 0.28), 0, 1))
    f = 1.0
    for ct in CUTS:
        f = min(f, clamp(abs(t - ct) / 0.25))
    out = out * f
    out = out * (1 - 0.88 * seg(t, T_OUT, T_OUT + 0.8))
    L2 = Image.new("RGB", (W, H), (0, 0, 0))
    l2 = ImageDraw.Draw(L2)
    anim.draw_caption(l2, t)
    DARK.clear()
    if env in ('roof', 'roof2', 'airport', 'station', 'blast'):
        DARK.append((40, 150, 1040, 420, 0.9))
    hud(l2, c, t, env, info)
    if DARK:
        mk = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mk)
        for (x0, y0, x1, y1, a) in DARK:
            md.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=int(30 * S), fill=int(255 * 0.66 * a))
        out = out * (1 - np.asarray(mk, np.float32)[..., None] / 255.0)
    out = out + np.asarray(L2, np.float32) + 1.2 * glow_of(L2, 3)
    out = out * (seg(t, 0.0, 0.3) * (1 - seg(t, DUR - 0.5, DUR)))
    return np.clip(out, 0, 255).astype(np.uint8)


# =====================================================================
# HUD
# =====================================================================
def fmt_int(n):
    return f"{int(n):,}"


def glyph_tepetl(l2, cx, cy, sz, a, t):
    """glifo estilizado (original): monte náhuatl con volutas de humo"""
    if a <= 0:
        return
    g, dkg = (90, 170, 90), (40, 100, 50)
    pts = []
    for k in range(25):
        u = k / 24
        x = cx - sz * 0.5 + sz * u
        y = cy + sz * 0.35 - sz * 0.62 * (math.sin(math.pi * u) ** 0.65)
        pts.append(P(x, y))
    pts += [P(cx + sz * 0.5, cy + sz * 0.42), P(cx - sz * 0.5, cy + sz * 0.42)]
    l2.polygon(pts, fill=sc3(dkg, a), outline=sc3(g, a))
    l2.rectangle((*P(cx - sz * 0.5, cy + sz * 0.3), *P(cx + sz * 0.5, cy + sz * 0.42)), fill=sc3((200, 120, 60), a))
    for k in range(5):
        x = cx - sz * 0.4 + k * sz * 0.2
        l2.ellipse((*P(x - 8, cy + sz * 0.36 - 8), *P(x + 8, cy + sz * 0.36 + 8)), outline=sc3((250, 220, 170), a), width=max(1, int(2 * S)))
    for j in range(3):
        ph = t * 1.2 + j * 2.0
        base_x = cx - sz * 0.12 + j * sz * 0.12
        pts = []
        for k in range(30):
            u = k / 29
            ang = u * 4 * math.pi + ph
            rr = sz * 0.05 * (1 + 2.5 * u)
            pts.append(P(base_x + rr * math.cos(ang) + sz * 0.05 * u, cy - sz * 0.3 - u * sz * 0.55 + rr * math.sin(ang) * 0.6))
        l2.line(pts, fill=sc3((226, 226, 232), a), width=max(2, int(4 * S)))


def semaforo(l2, x, y, a):
    if a <= 0:
        return
    DARK.append((x - 90, y - 190, x + 90, y + 190, a))
    l2.rounded_rectangle((*P(x - 60, y - 160), *P(x + 60, y + 160)), radius=int(24 * S), fill=sc3((34, 36, 44), a), outline=sc3((160, 160, 180), a), width=max(2, int(3 * S)))
    for k, col in enumerate(((70, 230, 120), (255, 205, 60), (255, 70, 70))):
        cy_ = y + 100 - k * 100
        on = k == 1
        l2.ellipse((*P(x - 38, cy_ - 38), *P(x + 38, cy_ + 38)), fill=sc3(col, a * (1.0 if on else 0.18)), outline=sc3(col, a * 0.6), width=max(1, int(2 * S)))


def hud(l2, c, t, env, info):
    def label(txt, target, text_pos, anchor, a, col=(225, 228, 245), size=30):
        if a <= 0:
            return
        f = F(B, size)
        tw = f.getlength(txt) / S
        tx, ty = text_pos
        DARK.append(((tx - tw - 20) if anchor == "rm" else tx - 20, ty - 28, (tx + 20) if anchor == "rm" else tx + tw + 20, ty + 28, a * 0.85))
        l2.text(P(tx, ty), txt, font=f, fill=sc3(col, a), anchor=anchor)
        ex = (tx - tw - 14) if anchor == "rm" else (tx + tw + 14)
        l2.line([P(*target), P(ex, ty)], fill=sc3((190, 190, 230), a), width=max(1, int(2 * S)))
        rr = 6 * S
        px, py = P(*target)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), outline=sc3((240, 240, 255), a), width=max(1, int(2 * S)))

    def pill(txt, y, a, col=BLUE, w=560, size=36):
        if a <= 0:
            return
        DARK.append((540 - w / 2, y - 42, 540 + w / 2, y + 42, a))
        l2.rounded_rectangle((*P(540 - w / 2, y - 42), *P(540 + w / 2, y + 42)), radius=int(42 * S), outline=sc3(col, a), width=max(2, int(3 * S)))
        l2.text(P(540, y), txt, font=F(B, size), fill=sc3((240, 244, 255), a), anchor="mm")

    def note(txt, a, y=1860):
        if a > 0:
            DARK.append((1040 - F(B, 22).getlength(txt) / S - 14, y - 20, 1054, y + 20, a * 0.6))
            l2.text(P(1040, y), txt, font=F(B, 22), fill=sc3((205, 205, 225), a * 0.9), anchor="rm")

    def win(a, b, e=0.4):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def P3(p):
        sx, sy, _ = proj(*p, c)
        return (sx, sy)

    for ct in CUTS:
        if abs(t - ct) < 0.25:
            return
    if env == 'roof':
        a = win(0.4, 6.0)
        if a > 0:
            DARK.append((150, 1430, 930, 1700, a))
            n = min(42, info.get('n_puffs', 0) + sum(1 for ti in np.linspace(0.35, 5.55, 42) if ti <= t - 3.2))
            n = sum(1 for ti in np.linspace(0.35, 5.55, 42) if ti <= t)
            l2.text(P(540, 1510), f"{n}", font=F(M, 96), fill=sc3((240, 244, 255), a), anchor="mm")
            l2.text(P(540, 1620), "EXHALACIONES EN UN DÍA", font=F(B, 34), fill=sc3((255, 226, 190), a), anchor="mm")
            note("CENAPRED · 9 OCT 2026 · TIEMPO ACELERADO", a)
        a = win(WT(0, 1) - 0.1, 6.0)
        if a > 0:
            d = info.get('dist', 72.0)
            pill(f"A {d:.0f} km DE LA CDMX" if d > 15 else "POPOCATÉPETL", 1770, a, ORANGE, 620, 34)
    if env == 'block':
        a = win(T_SCAN - 0.1, T_SCAN + 1.8, 0.2)
        if a > 0:
            pill("ESCÁNER: RAYOS X", 1640, a, SCAN, 560, 34)
        a = win(WT(2, 0) - 0.2, 11.2)
        if a > 0:
            DARK.append((180, 1180, 900, 1800, a))
            glyph_tepetl(l2, 540, 1400, 300, a, t)
            l2.text(P(540, 1660), "POPOCA = HUMEAR", font=F(B, 38), fill=sc3((230, 230, 245), a * ease(seg(t, WT(2, 4) - 0.2, WT(2, 4) + 0.2))), anchor="mm")
            l2.text(P(540, 1730), "TEPETL = MONTE", font=F(B, 38), fill=sc3((150, 230, 160), a * ease(seg(t, WT(2, 6) - 0.2, WT(2, 6) + 0.2))), anchor="mm")
            note("GLIFO ESTILIZADO", a, 1860)
        note("BLOQUE GEOLÓGICO · ILUSTRACIÓN", win(6.3, WT(2, 0) - 0.2), 1860)
    if env == 'magma':
        a = win(11.6, 18.4)
        if a > 0:
            label("MAGMA: ROCA DERRETIDA", P3(info['chamber']), (60, 1380), "lm", ease(seg(t, WT(3, 2) - 0.2, WT(3, 2) + 0.2)) * a, (255, 200, 150))
            label("VAPOR Y GASES", P3(info['conduit']), (1020, 1140), "rm", ease(seg(t, WT(3, 8) - 0.2, WT(3, 8) + 0.2)) * a, (220, 236, 255))
        a = win(WT(4, 0) - 0.2, 18.4)
        if a > 0:
            label("CRÁTER", P3(info['crater']), (1020, 560), "rm", a)
            DARK.append((330, 1580, 750, 1720, a))
            l2.text(P(540, 1625), f"EXHALACIÓN #{42 + info.get('puff_count', 0)}", font=F(B, 36), fill=sc3((240, 240, 250), a), anchor="mm")
            l2.text(P(540, 1685), "GAS QUE ESCAPA", font=F(B, 28), fill=sc3(CYAN, a), anchor="mm")
        note("ESQUEMA SIMPLIFICADO", win(11.6, 18.4))
    if env == 'tomo':
        a = win(18.9, 23.8)
        if a > 0:
            label("22 SENSORES SÍSMICOS", info['sensor'], (60, 560), "lm", ease(seg(t, 19.0, 19.4)) * a, (190, 255, 210))
            pill("TOMOGRAFÍA UNAM · CON IA", 1660, ease(seg(t, WT(5, 4) - 0.2, WT(5, 4) + 0.2)) * a, SCAN, 720, 32)
            (x0, y0), (x1, y1) = info['ruler']
            ka = ease(seg(t, WT(5, 11) - 0.2, WT(5, 11) + 0.4)) * a
            if ka > 0:
                DARK.append((x0 - 200, y0 - 40, x0 + 70, y1 + 90, ka))
                l2.line([P(x0, y0), P(x0, y1)], fill=sc3((220, 230, 255), ka), width=max(2, int(3 * S)))
                for kd, lab in ((0, "0"), (6, "6"), (12, "12"), (18, "18 km")):
                    yk = y0 + (y1 - y0) * kd / 18
                    l2.line([P(x0 - 10, yk), P(x0 + 10, yk)], fill=sc3((220, 230, 255), ka), width=max(1, int(2 * S)))
                    l2.text(P(x0 + 16, yk), lab, font=F(B, 24), fill=sc3((220, 230, 255), ka), anchor="lm")
                kt = ease(seg(t, WT(5, 15) - 0.3, WT(5, 17) + 0.3)) * a
                ntow = int(100 * kt)
                hh = (y1 - y0) / 100.0
                for k in range(ntow):
                    yb = y0 + hh * (k + 1)
                    xa = x0 - 50
                    l2.polygon([P(xa, yb), P(xa + 22, yb), P(xa + 16, yb - hh * 0.85), P(xa + 6, yb - hh * 0.85)], fill=sc3((200, 210, 230), kt))
                if kt > 0.05:
                    l2.text(P(x0 - 60, y1 + 40), "≈100 TORRES", font=F(B, 26), fill=sc3(GOLD, kt), anchor="mm")
                    l2.text(P(x0 - 60, y1 + 70), "LATINOAMERICANAS", font=F(B, 20), fill=sc3(GOLD, kt), anchor="mm")
        note("UNAM · INSTITUTO DE GEOFÍSICA · 2025", win(18.9, 23.8))
    if env == 'pockets':
        a = win(24.2, 26.8)
        if a > 0:
            chs = info['ch']
            label("BOLSA DE MAGMA", chs[0], (1020, 1060), "rm", a, (255, 200, 150))
            label("BOLSA DE MAGMA", chs[1], (60, 1320), "lm", ease(seg(t, 24.6, 25.0)) * a, (255, 200, 150))
            pill("SE VIERON 2 DE 3 CÁMARAS", 1700, ease(seg(t, WT(6, 5) - 0.2, WT(6, 5) + 0.2)) * a, ORANGE, 720, 32)
        note("PROFUNDIDADES ILUSTRATIVAS", win(24.2, 26.8))
    if env == 'blast':
        a = win(27.3, T_BOOM + 0.2, 0.3)
        if a > 0:
            DARK.append((80, 1500, 520, 1660, a))
            k = info.get('press', 0.0)
            l2.text(P(110, 1540), "PRESIÓN", font=F(B, 30), fill=sc3((230, 230, 245), a), anchor="lm")
            l2.rectangle((*P(110, 1580), *P(490, 1620)), outline=sc3((150, 150, 190), a), width=max(1, int(2 * S)))
            l2.rectangle((*P(110, 1580), *P(110 + 380 * k, 1620)), fill=sc3(lc((255, 200, 80), (255, 70, 60), k), a))
            label("CRÁTER TAPADO", info['crater'], (1020, 1150), "rm", ease(seg(t, WT(7, 3) - 0.2, WT(7, 3) + 0.2)) * a, (255, 200, 170))
        pill("VIENTO  →", 1680, win(WT(7, 14) - 0.2, 32.4), (220, 220, 240), 360, 34)
        note("ESQUEMA SIMPLIFICADO", win(27.3, 32.4))
    if env == 'airport':
        a = win(32.9, 37.3)
        if a > 0:
            DARK.append((80, 1180, 1000, 1560, a))
            l2.text(P(120, 1225), "SALIDAS", font=F(B, 36), fill=sc3((255, 220, 120), a), anchor="lm")
            rows = (("MTY", "CANCELADO"), ("CUN", "CANCELADO"), ("GDL", "CANCELADO"), ("TIJ", "CANCELADO"))
            for i, (dst, st_) in enumerate(rows):
                y = 1295 + i * 64
                kk = ease(seg(t, 33.4 + 0.25 * i, 33.7 + 0.25 * i))
                l2.text(P(120, y), dst, font=F(M, 40), fill=sc3((235, 235, 245), a * kk), anchor="lm")
                l2.text(P(960, y), st_, font=F(M, 40), fill=sc3(RED, a * kk), anchor="rm")
        pill("20 MAY 2023 · CERRADO ≈ 5.5 h", 1680, win(WT(8, 1) - 0.1, 37.3), ORANGE, 780, 34)
        note("AEROPUERTO GENÉRICO · RECREACIÓN", win(32.9, 37.3))
    if env == 'map':
        a = win(37.8, 41.6)
        if a > 0:
            cs = info['cities']
            for name, anc, tp in (('CDMX', 'lm', (60, 640)), ('PUEBLA', 'rm', (1020, 900)), ('CUERNAVACA', 'lm', (60, 1260)), ('TLAXCALA', 'rm', (1020, 640))):
                label(name, cs[name], tp, anc, a)
            px, py = info['popo']
            l2.polygon([P(px, py - 30), P(px + 26, py + 14), P(px - 26, py + 14)], fill=sc3((255, 140, 80), a), outline=sc3((255, 230, 200), a))
            DARK.append((px - 120, py + 26, px + 120, py + 66, a * 0.8))
            l2.text(P(px, py + 46), "POPOCATÉPETL", font=F(B, 26), fill=sc3((255, 220, 190), a), anchor="mm")
            DARK.append((150, 1440, 930, 1720, a))
            n = 25_000_000 * ease(seg(t, WT(9, 1) - 0.2, WT(9, 4) + 0.3))
            l2.text(P(540, 1520), "≈" + fmt_int(round(n, -5)), font=F(M, 78), fill=sc3((240, 244, 255), a), anchor="mm")
            l2.text(P(540, 1620), "PERSONAS A MENOS DE 100 km", font=F(B, 32), fill=sc3(CYAN, a), anchor="mm")
        note("MAPA ILUSTRATIVO", win(37.8, 41.6))
    if env == 'station':
        a = win(42.1, 46.4)
        if a > 0:
            label("CÁMARA", info['cam'], (1020, 560), "rm", ease(seg(t, 42.3, 42.7)) * a)
            label("GPS: MIDE SI SE INFLA", info['gps'], (60, 1360), "lm", ease(seg(t, 42.7, 43.1)) * a)
            label("SISMÓGRAFO", info['seis'], (1020, 1500), "rm", ease(seg(t, 43.1, 43.5)) * a)
        a = win(WT(10, 7) - 0.2, 46.4)
        if a > 0:
            semaforo(l2, 160, 900, a)
            DARK.append((280, 1560, 1000, 1760, a))
            l2.text(P(640, 1610), "AMARILLO · FASE 2", font=F(B, 44), fill=sc3((255, 210, 80), a), anchor="mm")
            l2.text(P(640, 1700), "NO ACERCARSE A MENOS DE 12 km", font=F(B, 28), fill=sc3((235, 235, 245), a), anchor="mm")
        note("CENAPRED · OCT 2026", win(42.1, 46.4))
    if env == 'roof2':
        pill("MÁNDASELO A QUIEN VIVE CERCA", 1560, win(46.8, T_OUT), (255, 200, 120), 840, 34)
        a = win(WT(11, 9) - 0.2, T_OUT)
        if a > 0:
            for (x0, txt, col) in ((300, "SÍ", GREEN), (780, "NO", RED)):
                DARK.append((x0 - 150, 1660, x0 + 150, 1800, a))
                l2.rounded_rectangle((*P(x0 - 130, 1675), *P(x0 + 130, 1785)), radius=int(30 * S), outline=sc3(col, a), width=max(3, int(4 * S)))
                l2.text(P(x0, 1730), txt, font=F(B, 56), fill=sc3(col, a), anchor="mm")
            l2.text(P(540, 1840), "RESPONDE EN COMENTARIOS", font=F(B, 26), fill=sc3((220, 220, 240), a), anchor="mm")
    ta = ease(seg(t, T_OUT + 0.2, T_OUT + 1.0))
    if ta > 0:
        l2.text(P(540, 900), "Mente en órbita", font=F(B, 112), fill=sc3((240, 235, 255), ta), anchor="mm")
        ang = 2 * math.pi * (t - T_OUT) / 3.0
        ox, oy = 540 + 440 * math.cos(ang), 900 + 130 * math.sin(ang)
        l2.ellipse((*P(540 - 440, 900 - 130), *P(540 + 440, 900 + 130)), outline=sc3(VIOLET, 0.45 * ta), width=max(1, int(2 * S)))
        rr = 9 * S
        px, py = P(ox, oy)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, ta))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        os.makedirs("/home/claude/popo_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/popo_prev/t_{ts}.png")
            print(ts, f"{time.time() - t0:.2f}s", flush=True)
    elif mode == "times":
        for i, ph in enumerate(anim.PH):
            print(i, [round(s, 2) for s in ph['starts']])
        print("T_SCAN", round(T_SCAN, 2), "T_BOOM", round(T_BOOM, 2), "D0", round(D0, 2), "PHI0", round(PHI0, 2), "YAW0", round(YAW0, 2))
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fr in range(a, b):
            pr.stdin.write(render(fr / FPS).tobytes())
        pr.stdin.close()
        pr.wait()
        print("ok", a, b, "de", NF)
