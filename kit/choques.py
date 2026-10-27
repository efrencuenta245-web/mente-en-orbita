"""Mente en órbita — ¿Por qué no chocan los satélites? (video 8).
Escenas: enjambre de satélites sobre la Tierra · choque Iridium 33 – Kosmos 2251 (2009) · radar y telescopio de vigilancia ·
predicción de un acercamiento · el satélite se hace a un lado · la Estación Espacial esquiva un pedazo de cohete (2025) ·
satélite tipo Starlink en rayos X (tanque de argón, propulsor eléctrico, computadora) · flota con maniobras ·
plataforma de lanzamiento · ventana de lanzamiento (la Tierra gira bajo la órbita) · etapa superior soltando satélites · cierre."""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
import lasers  # (fija anim.PHR al importarse; se sobrescribe abajo)
from nc import proj, P2, vis
from fo import clip_near, line3, pulses, resample
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of, VIOLET, BLUE, CYAN, ORANGE)
from gps_geo import (norm, cam_from, cam_keys, polyline3, glow_dot, ring_pts, splat)
import gps_earth as ge
import moto_model as mm
from lasers import draw_stars, SAT, model_faces, draw_list, proj_np_, occl_np, sat_icon, term_head, TERMS

FPS = 24
RED = (255, 80, 80)
GREEN = (90, 255, 150)
GOLD = (255, 210, 110)
HALL = (175, 120, 255)

PHR = [
    (0.3, 6.2, "Sobre tu cabeza giran casi 16 mil satélites, muchos a 27 mil kilómetros por hora... sin semáforos.", {16}),
    (6.7, 8.2, "¿Cómo es que no chocan?", {4}),
    (8.7, 14.6, "Bueno... a veces sí: en 2009, dos satélites chocaron sobre Siberia y dejaron más de dos mil pedazos.", {8}),
    (15.1, 19.4, "Por eso, radares y telescopios vigilan unos 47 mil objetos, día y noche.", {7}),
    (19.9, 25.0, "Computadoras predicen sus caminos días antes y avisan si dos van a pasar muy cerca.", {1}),
    (25.5, 29.2, "Entonces, el satélite enciende su propulsor y se hace a un lado.", {3}),
    (29.7, 34.2, "Hasta la Estación Espacial lo hace: en 2025 esquivó un pedazo de cohete viejo.", {8}),
    (34.7, 38.7, "Los Starlink lo deciden solos, con un motor eléctrico que dispara argón.", {4}),
    (39.2, 44.1, "En seis meses hicieron más de 200 mil maniobras: más de mil al día.", {11}),
    (44.6, 48.8, "¿Y dónde los sueltan? Su órbita se planea desde antes del despegue.", {3}),
    (49.3, 56.0, "Como la Tierra gira, el cohete sale justo cuando esa órbita pasa sobre la base: la ventana de lanzamiento.", {16}),
    (56.5, 61.4, "Y su computadora los suelta a la altura y velocidad exactas, uno tras otro.", {10}),
    (62.0, 64.0, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)
_ST = [list(ph['starts']) for ph in anim.PH]


def WT(i, w):
    """inicio de la palabra w de la frase i (línea de tiempo original)"""
    return _ST[i][w]


DUR = 65.2
NF = int(DUR * FPS)
CUTS = (8.45, 14.85, 19.65, 25.25, 29.45, 34.45, 38.95, 44.35, 49.05, 56.25)
ENVS = ('hook', 'crash', 'radar', 'predict', 'dodge', 'iss', 'xray', 'fleet', 'pad', 'window', 'deploy')
T_OUT = 61.7


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


# =====================================================================
# Órbitas (km). Sentido de giro de la Tierra al DISMINUIR spin (= hacia el este)
# =====================================================================
RE = 6371.0
MU = 398600.0
_s0 = np.array(ge.surf_point((0, 0, 0), 1.0, 0.0, 0.0, 0.0))
_s1 = np.array(ge.surf_point((0, 0, 0), 1.0, 0.0, 0.0, -1.0))
SPIN_AX = norm(np.cross(_s0, _s1 - _s0))
NORTH = np.array([0.0, 1.0, 0.0])
TL = 150.0  # factor de tiempo acelerado de las órbitas


def plane_basis(inc_deg, raan_deg):
    O = math.radians(raan_deg)
    e1 = np.array([math.cos(O), 0.0, math.sin(O)])
    e2q = norm(np.cross(SPIN_AX, e1))
    i = math.radians(inc_deg)
    e2 = norm(math.cos(i) * e2q + math.sin(i) * NORTH)
    return e1, e2


def make_sats(specs, seed):
    """specs: (n, inc, alt, raan_mode) → arrays e1, e2, r, u0, w"""
    rs = np.random.RandomState(seed)
    E1, E2, Rr, U0, Wv = [], [], [], [], []
    for (n, inc, alt, nplanes) in specs:
        for k in range(n):
            if nplanes:
                pl = k % nplanes
                raan = 360.0 * pl / nplanes + rs.uniform(-0.6, 0.6)
                u0 = 2 * math.pi * (k // nplanes) / max(1, n // nplanes) + pl * 0.37
            else:
                raan = rs.uniform(0, 360)
                u0 = rs.uniform(0, 2 * math.pi)
            ii = inc if inc is not None else rs.uniform(0, 100)
            aa = alt if alt is not None else rs.uniform(400, 1500)
            e1, e2 = plane_basis(ii, raan)
            r = RE + aa + rs.uniform(-6, 6)
            E1.append(e1)
            E2.append(e2)
            Rr.append(r)
            U0.append(u0)
            Wv.append(math.sqrt(MU / r ** 3))
    return np.array(E1), np.array(E2), np.array(Rr), np.array(U0), np.array(Wv)


def sat_pos(SS, t, tl=TL):
    E1, E2, Rr, U0, Wv = SS
    u = U0 + Wv * t * tl
    return Rr[:, None] * (np.cos(u)[:, None] * E1 + np.sin(u)[:, None] * E2)


ALL_SATS = make_sats([(2400, 53.0, 550, 72), (1600, 43.0, 530, 40), (800, 70.0, 570, 36), (700, 97.6, 560, 10),
                      (1800, 53.2, 540, 72), (650, 87.9, 1200, 18), (3800, None, None, 0), (180, 55.0, 20200, 6),
                      (120, 56.0, 23200, 3), (700, 0.05, 35786, 0), (450, 98.0, 700, 0)], 11)
STARLINK = make_sats([(2400, 53.0, 550, 72), (1800, 53.2, 540, 72), (2600, 43.0, 530, 52), (900, 70.0, 570, 36),
                      (600, 97.6, 560, 10), (1700, 53.0, 480, 60)], 23)
_rs = np.random.RandomState(5)
ALL_COL = np.where((ALL_SATS[2] > 30000)[:, None], np.array([[1.0, 0.86, 0.55]]), np.array([[0.78, 0.88, 1.0]]))
ALL_INT = _rs.uniform(0.45, 1.0, len(ALL_SATS[2]))


def draw_sat_cloud(buf, c, P_, col, inten, size=2):
    occ = occl_np(c, P_, (0, 0, 0), RE)
    keep = ~occ
    sx, sy, dep = proj_np_(P_[keep], c)
    ok = (dep > 50) & (sx * S >= 1) & (sx * S < W - 3) & (sy * S >= 1) & (sy * S < H - 3)
    xs, ys = (sx[ok] * S).astype(np.int32), (sy[ok] * S).astype(np.int32)
    w = (inten[keep][ok] if not np.isscalar(inten) else np.full(xs.shape, inten)).astype(np.float32)
    cv = col[keep][ok] if (not isinstance(col, tuple) and col.ndim == 2) else np.tile(np.asarray(col, np.float32), (len(xs), 1))
    for dx_ in range(size):
        for dy_ in range(size):
            for ch in range(3):
                np.add.at(buf[..., ch], (ys + dy_, xs + dx_), w * cv[:, ch] * 255.0)


def earth(arr, c, spin, sun, ctr=(0, 0, 0), R=RE, **kw):
    draw_stars(arr, c)
    ge.render_earth(arr, c, ctr, R, spin, sun, **kw)


# ---------- par de satélites que se cruzan en el gancho ----------
def _camdir(phi, yaw):
    p, y = math.radians(phi), math.radians(yaw)
    return np.array([math.cos(p) * math.sin(y), math.sin(p), -math.cos(p) * math.cos(y)])


def planes_x(sdir, inc):
    """las dos normales de plano de inclinación inc que contienen la dirección sdir"""
    k = SPIN_AX
    s = norm(sdir)
    sk = s @ k
    sh = s - sk * k
    u1 = norm(sh)
    u2 = np.cross(k, u1)
    A = math.cos(math.radians(inc))
    Bc = -A * sk / np.linalg.norm(sh)
    C = math.sqrt(max(0.0, 1 - A * A - Bc * Bc))
    return [norm(A * k + Bc * u1 + sg * C * u2) for sg in (1, -1)]


def cross_pair(xdir, incA, incB):
    """dos órbitas que se cruzan en xdir (u=0 en el cruce), casi en ángulo recto"""
    X = norm(xdir)
    nA = max(planes_x(X, incA), key=lambda n: np.cross(n, X) @ NORTH)
    vA = norm(np.cross(nA, X))
    nB = min(planes_x(X, incB), key=lambda n: abs(norm(np.cross(n, X)) @ vA))
    out = []
    for n in (nA, nB):
        out.append((X, norm(np.cross(n, X))))
    return out


_X = norm(_camdir(24, -6) + np.array([0.12, 0.10, 0.0]))
PA, PB = cross_pair(_X, 53.0, 97.6)
RS_X = RE + 552.0
X_HOOK = _X * RS_X
T_MEET = 8.75


def pair_pos(t):
    out = []
    for (e1, e2) in (PA, PB):
        w = math.sqrt(MU / RS_X ** 3) * TL
        u = -w * (T_MEET - t)
        out.append(RS_X * (math.cos(u) * e1 + math.sin(u) * e2))
    return out


# =====================================================================
# Modelos (metros)
# =====================================================================
def build_iridium():
    m = mm.Model()
    R_ = 0.62
    tri = [(R_ * math.cos(a), R_ * math.sin(a)) for a in (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3)]
    m.ext(tri, -2.0, 2.0, (196, 160, 82), 'body', (205, 168, 86))
    for i in range(3):
        a, b = np.array(tri[i]), np.array(tri[(i + 1) % 3])
        mid = (a + b) / 2
        nn = norm(np.array([mid[0], mid[1], 0.0]))
        tv = norm(np.array([b[0] - a[0], b[1] - a[1], 0.0]))
        ctr = np.array([mid[0], mid[1], 0.3]) + nn * 0.04
        pts = [ctr + tv * sx * 0.46 + np.array([0, 0, 1.0]) * sz * 1.45 for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        m.face(pts, nn, (214, 216, 222), 'mma')
        m.face(pts[::-1], -nn, (120, 122, 130), 'mma')
    for s in (-1, 1):
        m.beam((0, 0, -1.7), (s * 1.4, 0, -1.7), 0.08, 0.08, (170, 172, 178))
        x0, x1 = (1.4, 4.4) if s > 0 else (-4.4, -1.4)
        m.box((x0, -0.02, -2.4), (x1, 0.02, -1.0), (32, 52, 120), 'panel')
    return m


def build_kosmos():
    m = mm.Model()
    m.cyl((0, 0, 0), (0, 0, 1), 1.0, 2.8, (44, 56, 104), 18, 'body', True, (176, 178, 186))
    for z in (-1.0, 0.0, 1.0):
        m.cyl((0, 0, z), (0, 0, 1), 1.02, 0.12, (170, 172, 180), 18, 'body', False)
    m.beam((0, 0, 1.4), (0, 0, 8.0), 0.07, 0.07, (186, 188, 196))
    m.box((-0.18, -0.18, 8.0), (0.18, 0.18, 8.36), (150, 152, 160))
    return m


IRI = build_iridium()
KOS = build_kosmos()


def starlink_faces(c, pos, Rm, L, xr=0.0, dim=1.0):
    fl = model_faces(c, SAT, pos, Rm, L, dim, xr, ('body',))
    for tp in TERMS:
        hp = np.asarray(pos) + Rm @ (tp + np.array([0, 0.24, 0]))
        hm = term_head(hp, Rm @ np.array([0.3, 1.0, 0.0]) / np.linalg.norm([0.3, 1.0, 0.0]))
        fl += model_faces(c, hm, hp, np.eye(3), L, dim, xr, ('head',))
    st = mm.Model()
    st.cyl((0.6, 0.18, -0.5), (0, 1, 0), 0.06, 0.12, (40, 42, 50), 12, 'body', True, (20, 20, 26))
    fl += model_faces(c, st, pos, Rm, L, dim, xr, ('body',))
    return fl


def sl_panel_lines(bd, c, pos, Rm):
    w1 = max(1, int(1.5 * S))
    for sx in (-1, 1):
        x0, x1 = (2.1, 8.3) if sx > 0 else (-8.3, -2.1)
        for k in range(1, 8):
            x = x0 + (x1 - x0) * k / 8
            line3(bd, c, tuple(np.asarray(pos) + Rm @ np.array([x, 0.025, -1.2])), tuple(np.asarray(pos) + Rm @ np.array([x, 0.025, 1.2])), (70, 96, 170), w1, 0.05)


def build_iss():
    m = mm.Model()
    m.beam((-55, 0, 0), (55, 0, 0), 3.0, 3.0, (170, 172, 180), side=(0, 1, 0))
    for x in (-50, -38, 38, 50):
        for s in (-1, 1):
            m.box((x - 5.5, -0.1, s * 3), (x + 5.5, 0.1, s * 36), (178, 118, 56), 'panel')
            m.beam((x, 0, s * 1.5), (x, 0, s * 3.2), 0.6, 0.6, (150, 152, 160), side=(1, 0, 0))
    for (z0, z1) in ((-14, -4), (-4, 6), (6, 16)):
        m.cyl((0, -3, (z0 + z1) / 2), (0, 0, 1), 2.2, z1 - z0 - 0.4, (226, 228, 234), 16)
    m.cyl((-7, -3, 2), (1, 0, 0), 2.0, 9, (222, 224, 230), 14)
    m.cyl((7, -3, -6), (1, 0, 0), 2.0, 9, (222, 224, 230), 14)
    for x in (-22, 22):
        m.box((x - 7, -0.08, -1.2), (x + 7, 0.08, -13), (236, 238, 242))
    # módulo de servicio + nave de carga acoplada atrás
    m.cyl((0, -3, -19), (0, 0, 1), 2.0, 9.6, (214, 216, 222), 16)
    m.cyl((0, -3, -27.2), (0, 0, 1), 1.35, 6.8, (210, 212, 216), 14, 'body', True, (120, 122, 128))
    for s in (-1, 1):
        m.box((s * 1.4, -3.05, -29.5), (s * 6.2, -2.95, -28.0), (40, 58, 120), 'panel')
        m.box((s * 2.0, -3.05, -18.0), (s * 9.5, -2.95, -16.2), (40, 58, 120), 'panel')
    return m


ISS = build_iss()
ISS_AFT = [np.array([x, -3 + y, -30.65]) for (x, y) in ((0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7))]


def build_rocket():
    m = mm.Model()
    white, black, gray = (232, 234, 238), (32, 33, 38), (120, 122, 128)
    m.cyl((0, 1.0, 0), (0, 1, 0), 1.9, 2.0, black, 24)
    m.cyl((0, 22.0, 0), (0, 1, 0), 1.85, 40.0, white, 24)
    m.cyl((0, 45.0, 0), (0, 1, 0), 1.86, 6.0, black, 24)
    m.cyl((0, 55.0, 0), (0, 1, 0), 1.85, 14.0, white, 24)
    m.cyl((0, 65.0, 0), (0, 1, 0), 2.6, 6.0, white, 24, 'body', True, white)
    # punta (cono por anillos)
    prev = None
    for k in range(7):
        y0, y1 = 68.0 + k * 1.3, 68.0 + (k + 1) * 1.3
        r0 = 2.6 * math.cos(0.5 * math.pi * k / 7) ** 0.8
        r1 = 2.6 * math.cos(0.5 * math.pi * (k + 1) / 7) ** 0.8
        n = 24
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            pts = [(r0 * math.cos(a0), y0, r0 * math.sin(a0)), (r0 * math.cos(a1), y0, r0 * math.sin(a1)),
                   (r1 * math.cos(a1), y1, r1 * math.sin(a1)), (r1 * math.cos(a0), y1, r1 * math.sin(a0))]
            am = (a0 + a1) / 2
            slope = (r0 - r1) / 1.3
            m.face(pts, norm((math.cos(am), slope, math.sin(am))), white)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        d = np.array([math.cos(a), 0, math.sin(a)])
        m.beam(d * 1.9 + np.array([0, 1.2, 0]), d * 1.95 + np.array([0, 9.0, 0]), 0.5, 0.25, black, side=(0, 1, 0))
        m.box(tuple(d * 1.9 + np.array([-0.4, 40.5, -0.4])), tuple(d * 1.9 + np.array([0.4, 41.6, 0.4])), gray)
    return m


def build_tower():
    m = mm.Model()
    g, dg = (150, 150, 154), (92, 92, 98)
    x0, x1, z0, z1 = 8.0, 15.0, -3.5, 3.5
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        m.beam((x, 0, z), (x, 82, z), 0.7, 0.7, g)
    for k in range(0, 9):
        y = 4 + k * 9.6
        for (p0, p1) in (((x0, y, z0), (x1, y, z0)), ((x0, y, z1), (x1, y, z1)), ((x0, y, z0), (x0, y, z1)), ((x1, y, z0), (x1, y, z1))):
            m.beam(p0, p1, 0.45, 0.45, dg, side=(0, 1, 0))
        yn = y + 9.6
        m.beam((x0, y, z0), (x1, yn, z0), 0.3, 0.3, dg)
        m.beam((x0, y, z1), (x1, yn, z1), 0.3, 0.3, dg)
    m.box((2.7, 64.0, -1.3), (8.0, 66.0, 1.3), (110, 110, 116))
    m.box((-40, 0, -40), (40, 0.6, 40), (148, 146, 140))
    m.box((-8, 0.6, -4), (8, 1.6, 4), (120, 118, 114))
    for (x, z) in ((-45, -30), (45, -32), (2, 52)):
        m.beam((x, 0, z), (x, 108, z), 1.0, 1.0, (170, 170, 176))
    return m


ROCKET = build_rocket()
TOWER = build_tower()


def build_radar():
    m = mm.Model()
    concrete = (178, 176, 170)
    prof = [(0, 0), (11.6, 32.0), (30.0, 32.0), (30.0, 0)]
    loc = mm.Model()
    loc.ext(prof, -17.0, 17.0, concrete, 'body', (168, 166, 160))
    Rb = mm.rot(math.radians(90))
    for (pts, n, col, tag) in loc.F:
        m.face(pts @ Rb.T, Rb @ n, col, tag)
    # cara del arreglo: círculo de antenas sobre la cara inclinada
    nf = Rb @ norm(np.array([-32.0, 11.6, 0.0]) * np.array([1, 1, 1]))
    nf = Rb @ norm(np.array([-math.cos(math.radians(20)), math.sin(math.radians(20)), 0.0]))
    cu = Rb @ np.array([5.8, 16.0, 0.0])
    up = Rb @ norm(np.array([11.6, 32.0, 0.0]))
    side = norm(np.cross(up, nf))
    ctr = cu + nf * 0.15
    pts = [ctr + 14.5 * (math.cos(a) * side + math.sin(a) * up) for a in np.linspace(0, 2 * math.pi, 33)[:-1]]
    m.face(pts, nf, (70, 74, 84), 'array')
    m.box((-26, 0, 34), (-17, 6, 50), (190, 188, 182))
    return m, ctr, nf, up, side


RADAR, ARR_C, ARR_N, ARR_UP, ARR_SIDE = build_radar()
DOME_C = np.array([-62.0, 0.0, 70.0])


def build_dome():
    m = mm.Model()
    white = (226, 228, 232)
    m.cyl(DOME_C + np.array([0, 3.5, 0]), (0, 1, 0), 7.0, 7.0, (206, 206, 210), 24)
    nb, ns = 7, 24
    for i in range(nb):
        e0, e1 = 0.5 * math.pi * i / nb, 0.5 * math.pi * (i + 1) / nb
        for j in range(ns):
            a0, a1 = 2 * math.pi * j / ns, 2 * math.pi * (j + 1) / ns
            p = lambda e, a: DOME_C + np.array([0, 7.0, 0]) + 7.1 * np.array([math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a)])
            pts = [p(e0, a0), p(e0, a1), p(e1, a1), p(e1, a0)]
            am, em = (a0 + a1) / 2, (e0 + e1) / 2
            nn = np.array([math.cos(em) * math.cos(am), math.sin(em), math.cos(em) * math.sin(am)])
            slit = (abs(((am - 4.25) + math.pi) % (2 * math.pi) - math.pi) < 0.2) and i >= 2
            m.face(pts, nn, (34, 36, 44) if slit else white)
    return m


DOME = build_dome()


def build_stage():
    m = mm.Model()
    m.cyl((0, 0, 0), (1, 0, 0), 1.85, 10.0, (206, 208, 212), 24, 'body', True, (150, 152, 158))
    m.cyl((-3.5, 0, 0), (1, 0, 0), 1.87, 1.0, (40, 40, 46), 24, 'body', False)
    for k in range(6):
        x0, x1 = -5.0 - k * 0.45, -5.0 - (k + 1) * 0.45
        r0, r1 = 0.45 + k * 0.17, 0.45 + (k + 1) * 0.17
        n = 20
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            pts = [(x0, r0 * math.cos(a0), r0 * math.sin(a0)), (x0, r0 * math.cos(a1), r0 * math.sin(a1)),
                   (x1, r1 * math.cos(a1), r1 * math.sin(a1)), (x1, r1 * math.cos(a0), r1 * math.sin(a0))]
            am = (a0 + a1) / 2
            m.face(pts, norm((0.38, math.cos(am), math.sin(am))), (52, 50, 54))
    m.cyl((5.3, 0, 0), (1, 0, 0), 1.3, 0.6, (60, 62, 70), 20)
    m.cyl((5.75, 0, 0), (1, 0, 0), 1.65, 0.3, (176, 178, 186), 24)
    return m


STAGE = build_stage()
PAY_COLS = [(206, 168, 80), (190, 192, 200), (44, 46, 54), (210, 170, 90), (176, 178, 186), (60, 64, 110)]
PAY_OFF = [np.array([6.2, 0.95 * math.cos(a), 0.95 * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
PAY_T0 = None  # se fija tras definir tiempos


def pay_model(k):
    m = mm.Model()
    col = PAY_COLS[k % len(PAY_COLS)]
    m.box((0, -0.34, -0.3), (0.62, 0.34, 0.3), col)
    m.face([(0.63, -0.3, -0.26), (0.63, 0.3, -0.26), (0.63, 0.3, 0.26), (0.63, -0.3, 0.26)], (1, 0, 0), (36, 50, 110))
    return m


PAYS = [pay_model(k) for k in range(6)]


# =====================================================================
# Cielo y suelo por píxel (escenas en tierra, metros)
# =====================================================================
def _hash(i, j, seed):
    n = (i * 374761393 + j * 668265263 + seed * 1013904223) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF).astype(np.float32) / 65535.0


def vnoise(x, z, sc, seed=0):
    X, Z = x / sc, z / sc
    xi, zi = np.floor(X).astype(np.int64), np.floor(Z).astype(np.int64)
    fx, fz = (X - xi).astype(np.float32), (Z - zi).astype(np.float32)
    ux, uz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b = _hash(xi, zi, seed), _hash(xi + 1, zi, seed)
    c_, d = _hash(xi, zi + 1, seed), _hash(xi + 1, zi + 1, seed)
    return (a + (b - a) * ux) * (1 - uz) + (c_ + (d - c_) * ux) * uz


def sky_col(dy, dx, dz, kind):
    e = np.clip(dy, -0.2, 1.0).astype(np.float32)
    if kind == 'dusk':
        hz = np.array([236, 128, 78], np.float32)
        mid = np.array([92, 80, 140], np.float32)
        top = np.array([10, 14, 38], np.float32)
        warm = np.clip(0.55 + 0.45 * (-dx * 0.8 + dz * 0.2), 0, 1).astype(np.float32)[..., None]
    else:  # dawn
        hz = np.array([252, 186, 120], np.float32)
        mid = np.array([128, 150, 196], np.float32)
        top = np.array([40, 66, 128], np.float32)
        warm = np.clip(0.5 + 0.5 * (dx * 0.7 + dz * 0.3), 0, 1).astype(np.float32)[..., None]
    k1 = np.clip(e / 0.12, 0, 1)[..., None]
    k2 = np.clip((e - 0.12) / 0.5, 0, 1)[..., None]
    hzc = hz * (0.55 + 0.45 * warm)
    return (hzc * (1 - k1) + mid * k1) * (1 - k2) + top * k2


def ground_scene(c, kind, coast=None):
    dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
    out = sky_col(dy, dx, dz, kind)
    cam = c['pos']
    m = dy < -2e-4
    tt = (0.0 - cam[1]) / np.where(m, dy, -1.0)
    gx, gz = cam[0] + tt * dx, cam[2] + tt * dz
    x, z, d = gx[m], gz[m], tt[m]
    n1 = vnoise(x, z, 2.5, 1)
    n2 = vnoise(x, z, 14.0, 2)
    n3 = vnoise(x, z, 60.0, 3)
    a1 = np.clip(2.5 * 260.0 / d, 0, 1).astype(np.float32)
    a2 = np.clip(14.0 * 260.0 / d, 0, 1).astype(np.float32)
    if kind == 'dusk':
        base = np.array([118, 98, 74], np.float32)
        alt = np.array([86, 88, 60], np.float32)
        lit = 0.42
        fogc = np.array([150, 96, 86], np.float32)
    else:
        base = np.array([196, 182, 150], np.float32)
        alt = np.array([110, 128, 78], np.float32)
        lit = 0.85
        fogc = np.array([210, 180, 160], np.float32)
    mix = np.clip((n3 - 0.35) * 2.2, 0, 1)[:, None]
    col = base * (1 - mix) + alt * mix
    col = col * (0.82 + 0.18 * ((n1 - 0.5) * a1 + 0.5)[:, None] * 2 * 0.5 + 0.14 * ((n2 - 0.5) * a2)[:, None])
    col = col * lit
    if coast is not None:
        water = z > coast + 6.0 * (vnoise(x, np.zeros_like(x), 40.0, 7) - 0.5)
        beach = (z > coast - 18.0) & ~water
        col[beach] = np.array([214, 200, 168], np.float32) * lit
        if water.any():
            rx, ry, rz = dx[m][water], -dy[m][water], dz[m][water]
            refl = sky_col(ry, rx, rz, kind) * 0.62 + np.array([10, 32, 52], np.float32) * 0.6
            sp = vnoise(x[water] * 1.0, z[water] * 3.0, 1.2, 9)
            refl = refl * (0.9 + 0.2 * sp[:, None] * np.clip(40.0 / d[water], 0, 1)[:, None])
            col[water] = refl
    f = np.clip((d - 300.0) / 6000.0, 0, 0.9)[:, None].astype(np.float32)
    col = col * (1 - f) + fogc * f
    out[m] = col
    return out.astype(np.float32), dy


def mountains(bd, c, z0, col, seed, amp=220.0, base=0.0):
    rs = np.random.RandomState(seed)
    xs = np.linspace(-12000, 12000, 90)
    hs = base + amp * (0.5 + 0.5 * np.sin(xs / 1700.0 + seed)) * (0.6 + 0.4 * rs.rand(len(xs)))
    pts = [(xs[0], -200.0, z0)] + [(x, h, z0 + 400 * math.sin(x / 3000.0)) for x, h in zip(xs, hs)] + [(xs[-1], -200.0, z0)]
    q = clip_near(pts, c, 10.0)
    if len(q) >= 3:
        bd.polygon([P2(*p, c) for p in q], fill=col)


# =====================================================================
# Choque 2009 (metros, cámara lenta)
# =====================================================================
DIR_A = norm(np.array([1.0, 0.0, 0.35]))
DIR_B = norm(np.array([-0.32, 0.0, 1.0]))
V_SLOW = 5.5
T_IMP = WT(2, 8) + 0.15
CR_CTR = (0.0, -(6.371e6 + 789e3), 0.0)
CR_SUN = norm((-0.45, 0.62, 0.55))
SAT_SUN = norm((-0.6, 0.55, 0.55))


def _make_debris(seed):
    rs = np.random.RandomState(seed)
    out = []
    for k in range(560):
        src = k % 2
        dv = DIR_A if src == 0 else DIR_B
        v = dv * V_SLOW * rs.uniform(0.45, 0.85) + rs.normal(0, 1.9, 3)
        sz = rs.uniform(0.08, 0.42) if k > 24 else rs.uniform(0.7, 1.5)
        verts = rs.normal(0, 1, (3, 3)) * sz
        ax = norm(rs.normal(0, 1, 3))
        if src == 0:
            col = [(196, 160, 82), (214, 216, 222), (32, 52, 120), (170, 172, 178)][rs.randint(0, 4)]
        else:
            col = [(44, 56, 104), (176, 178, 186), (60, 70, 110)][rs.randint(0, 3)]
        out.append((v, verts, ax, rs.uniform(1.5, 7.0), col, rs.normal(0, 0.25, 3)))
    return out


DEBRIS = _make_debris(9)
_rsp = np.random.RandomState(12)
SPARK_V = _rsp.normal(0, 1, (700, 3))
SPARK_V = SPARK_V / np.linalg.norm(SPARK_V, axis=1, keepdims=True) * _rsp.uniform(2, 16, (700, 1))
SPARK_V += (DIR_A + DIR_B)[None, :] * 2.0


def rodrigues(ax, ang):
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def draw_crash(base, bd, od, la, buf, c, t, info):
    if t < T_IMP:
        pa = -DIR_A * V_SLOW * (T_IMP - t)
        pb = -DIR_B * V_SLOW * (T_IMP - t)
        up = np.array([0, 1.0, 0])
        Ra = np.column_stack([DIR_A, np.cross(up, DIR_A), up]) @ rodrigues(np.array([0, 0, 1.0]), 0.5)
        Rb = np.column_stack([DIR_B, np.cross(up, DIR_B), up]) @ rodrigues(np.array([1.0, 0, 0]), 0.35 + 0.08 * t)
        fl = model_faces(c, IRI, pa, Ra, SAT_SUN, 1.0, near=0.3)
        fl += model_faces(c, KOS, pb, Rb, SAT_SUN, 1.0, near=0.3)
        draw_list(bd, od, fl)
        info['A'], info['B'] = pa, pb
    else:
        dt = t - T_IMP
        polys = []
        for (v, verts, ax, wv, col, p0) in DEBRIS:
            p = p0 + v * dt
            Rm = rodrigues(ax, wv * dt)
            Wp = verts @ Rm.T + p
            q = clip_near([tuple(x) for x in Wp], c, 0.3)
            if len(q) < 3:
                continue
            nn = norm(np.cross(Wp[1] - Wp[0], Wp[2] - Wp[0]))
            k = 0.4 + 0.75 * abs(nn @ SAT_SUN)
            dep = proj(*p, c)[2]
            polys.append((dep, [P2(*x, c) for x in q], tuple(int(min(255, cc * k)) for cc in col)))
        polys.sort(key=lambda q: -q[0])
        for dep, pts, col in polys:
            bd.polygon(pts, fill=col)
        # chispas
        fa = clamp(1 - dt / 1.1)
        if fa > 0.01:
            Pp = SPARK_V * dt
            for ch, cv in enumerate((255, 190, 110)):
                pass
            splat(buf, c, Pp[:, 0], Pp[:, 1], Pp[:, 2], (255, 200, 120), 1.0 * fa, near=0.3, size=2)
        fl_ = clamp(1 - dt / 0.45)
        if fl_ > 0.01:
            x, y, dep = proj(0, 0, 0, c)
            glow_dot(la, x * S, y * S, (60 + 160 * dt) * S, (255, 230, 190), fl_)
            glow_dot(la, x * S, y * S, 26 * S, (255, 255, 255), fl_)
        info['dt'] = dt


# =====================================================================
# Radar (metros, atardecer)
# =====================================================================
SKY_OBJ = [(norm(np.array([math.cos(a0) * 0.9, 0.35 + 0.5 * e0, 0.9 + 0.3 * math.sin(a0)])), norm(np.array([1.0, 0.25 * (k % 3 - 1), -0.2 + 0.1 * k % 0.4])), 0.03 + 0.012 * (k % 4))
           for k, (a0, e0) in enumerate(zip(np.linspace(-1.2, 1.3, 14), (np.sin(np.arange(14) * 2.3) * 0.5 + 0.5)))]


def sky_obj_pos(k, t):
    d0, v, w = SKY_OBJ[k]
    ang = w * (t - 14.0) * 1.8
    ax = norm(np.cross(d0, v))
    d = rodrigues(ax, ang) @ d0
    return d


def draw_radar_scene(c, t, la, od, info):
    arr, dy = ground_scene(c, 'dusk')
    tmp = np.zeros_like(arr)
    draw_stars(tmp, c, 0.7)
    arr += tmp * np.clip((dy - 0.12) / 0.3, 0, 1)[..., None].astype(np.float32)
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    bd = ImageDraw.Draw(base)
    mountains(bd, c, 5200.0, (58, 48, 74), 3, 380.0)
    mountains(bd, c, 3200.0, (44, 38, 56), 6, 220.0)
    L = norm((-0.75, 0.35, -0.3))
    fl = model_faces(c, RADAR, (0, 0, 0), np.eye(3), L, 0.72, near=1.0)
    fl += model_faces(c, DOME, (0, 0, 0), np.eye(3), L, 0.78, near=1.0)
    draw_list(bd, od, fl)
    # retícula del arreglo
    w1 = max(1, int(1.2 * S))
    for k in range(-13, 14, 2):
        hh = math.sqrt(max(0.0, 14.5 ** 2 - k * k))
        p0 = ARR_C + ARR_N * 0.05 + ARR_SIDE * k - ARR_UP * hh
        p1 = ARR_C + ARR_N * 0.05 + ARR_SIDE * k + ARR_UP * hh
        line3(bd, c, tuple(p0), tuple(p1), (96, 100, 112), w1, 1.0)
        p0 = ARR_C + ARR_N * 0.05 + ARR_UP * k - ARR_SIDE * hh
        p1 = ARR_C + ARR_N * 0.05 + ARR_UP * k + ARR_SIDE * hh
        line3(bd, c, tuple(p0), tuple(p1), (96, 100, 112), w1, 1.0)
    # luces del sitio
    for (x, y, z) in ((-30, 6.5, 33.5), (-17, 6.5, 33.5), (20, 2.5, -2), (-62, 7.4, 62.8), (36, 4, 10)):
        xx, yy, dep = proj(x, y, z, c)
        if dep > 1:
            glow_dot(la, xx * S, yy * S, 4 * S, (255, 200, 130), 0.9)
    # haz del radar: abanico que barre
    ph = (t - 14.9) * 0.55
    el = math.radians(18 + 50 * (0.5 + 0.5 * math.sin(ph * 2.2)))
    az0 = math.atan2(-ARR_N[0], -ARR_N[2]) if False else 0.0
    fan = [tuple(ARR_C + ARR_N * 0.3)]
    for az in np.linspace(-0.55, 0.55, 15):
        d = norm(np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)]))
        fan.append(tuple(ARR_C + d * 900.0))
    q = clip_near(fan, c, 1.0)
    a_f = ease(seg(t, 15.0, 15.6))
    if len(q) >= 3 and a_f > 0:
        la.polygon([P2(*p, c) for p in q], fill=sc3((8, 22, 16), a_f))
        polyline3(la, c, fan[1:], sc3(GREEN, 0.55 * a_f), max(1, int(2 * S)), 1.0)
    # objetos en el cielo
    trk = []
    for k in range(len(SKY_OBJ)):
        d = sky_obj_pos(k, t)
        if d[1] < 0.05:
            continue
        p = ARR_C + d * 60000.0
        xx, yy, dep = proj(*p, c)
        if dep < 10:
            continue
        el_k = math.asin(d[1])
        hit = abs(el_k - el) < 0.12 and abs(math.atan2(d[0], d[2])) < 0.6
        glow_dot(la, xx * S, yy * S, 3.4 * S, (230, 236, 255), 0.95)
        trk.append((xx, yy, hit, k))
    info['trk'] = trk
    info['el'] = el
    return base, bd


# =====================================================================
# Predicción (km)
# =====================================================================
_XP = norm(_camdir(34, 14) + np.array([0.0, 0.16, 0.0]))
PRA, PRB = cross_pair(_XP, 53.0, 97.6)
RP = RE + 555.0
X_PRED = _XP * RP


def pred_u(pl, t):
    e1, e2 = pl
    uX = math.atan2(_XP @ e2, _XP @ e1)
    w = math.sqrt(MU / RP ** 3) * 60.0
    return uX - 2.1 + w * 0.0 * t, uX


# =====================================================================
# Ventana de lanzamiento (km)
# =====================================================================
CAPE = (28.5, -80.6)
W_INC = 53.0
W_RATE = 15.0  # grados por segundo (tiempo acelerado)
T_LAUNCH = WT(10, 11) + 0.1
W_CAM = (21000, 24, 2)


def _site(spin, r=RE):
    return np.array(ge.surf_point((0, 0, 0), r, CAPE[0], CAPE[1], spin))


def _pick_spin():
    cd = _camdir(W_CAM[1], W_CAM[2])
    best = None
    for s in np.arange(-180, 180, 0.25):
        v = norm(_site(s)) @ cd
        if best is None or v > best[0]:
            best = (v, s)
    return best[1] - 14.0


SPIN_L = _pick_spin()


def _plane_through(sdir, inc):
    k = SPIN_AX
    s = norm(sdir)
    sk = s @ k
    sh = s - sk * k
    u1 = norm(sh)
    u2 = np.cross(k, u1)
    A = math.cos(math.radians(inc))
    Bc = -A * sk / np.linalg.norm(sh)
    C = math.sqrt(max(0.0, 1 - A * A - Bc * Bc))
    best = None
    for sg in (1, -1):
        n = A * k + Bc * u1 + sg * C * u2
        v = np.cross(n, s)
        if best is None or v @ NORTH > best[0]:
            best = (v @ NORTH, n)
    return norm(best[1])


W_N = _plane_through(_site(SPIN_L), W_INC)
W_A = norm(_site(SPIN_L))
W_B = norm(np.cross(W_N, W_A))


def w_spin(t):
    return SPIN_L + W_RATE * (T_LAUNCH - t)


# =====================================================================
# Cámaras
# =====================================================================
XH = tuple(X_HOOK * 0.94)
KEYS = {
    'hook': [(0.0, 27000, 16, -26, 1000, 0, 0, 0), (6.4, 21000, 22, -10, 1000, 0, 0, 0), (8.45, 9000, 24, -6, 980, *XH)],
    'crash': [(8.45, 30, 9, 30, 940, 0, 0, 0), (T_IMP, 20, 9, 40, 940, 0, 0, 0), (T_IMP + 1.2, 36, 11, 50, 940, 0, 0, 0), (14.85, 64, 14, 66, 940, 0, 0, 0)],
    'radar': [(14.85, 160, -5, -12, 980, -6, 28, 50), (19.65, 140, -6, -2, 980, -8, 30, 50)],
    'predict': [(19.65, 17500, 32, 8, 1000, 0, 0, 0), (25.25, 15500, 36, 20, 1000, 0, 0, 0)],
    'dodge': [(25.25, 21, 34, 24, 980, 0, 0, 0), (29.45, 23, 38, 36, 980, 0, 0, 2)],
    'iss': [(29.45, 170, 18, 28, 900, 0, -3, -8), (34.45, 150, 22, 48, 900, 0, -3, -8)],
    'xray': [(34.45, 6.0, 44, -36, 1000, -0.2, 0, -0.1), (38.95, 5.0, 50, -18, 1000, -0.3, 0, -0.15)],
    'fleet': [(38.95, 25000, 28, -6, 1000, 0, 0, 0), (44.35, 21500, 34, 18, 1000, 0, 0, 0)],
    'pad': [(44.35, 112, -8, 18, 880, 0, 40, 0), (49.05, 96, -10, 28, 880, 0, 42, 0)],
    'window': [(49.05, 21000, 24, 2, 980, 0, 0, 0), (56.25, 19800, 26, 8, 980, 0, 0, 0)],
    'deploy': [(56.25, 15, 18, 124, 940, 4.0, 0.3, 0), (65.2, 18, 22, 150, 940, 5.0, 0.3, 0)],
}
LOGD = {'hook': True, 'crash': True}


def cam_for(env, t):
    return cam_keys(t, KEYS[env], LOGD.get(env, False))


# =====================================================================
# Tiempos de eventos (línea original)
# =====================================================================
T_BURN = WT(5, 3) + 0.05
T_PASS = T_BURN + 2.0
T_ISSB = WT(6, 0) + 0.3
T_XR = WT(7, 0) + 0.3
T_SEP0 = WT(11, 4)
T_SEPS = [T_SEP0 + 0.62 * k for k in range(6)]
LEO_CTR = (0.0, -6.921e6, 0.0)
LEO_SUN = norm((0.85, 0.2, 0.5))
ISS_CTR = (0.0, -6.791e6, 0.0)


def debris_chunk():
    m = mm.Model()
    rs = np.random.RandomState(4)
    pts = rs.normal(0, 1, (8, 3)) * np.array([0.7, 0.35, 0.45])
    tris = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4), (6, 0, 1), (7, 3, 5)]
    for (a, b, c_) in tris:
        n = norm(np.cross(pts[b] - pts[a], pts[c_] - pts[a]))
        ctr = (pts[a] + pts[b] + pts[c_]) / 3
        if n @ ctr < 0:
            n = -n
            m.face([pts[a], pts[c_], pts[b]], n, (98, 96, 92))
        else:
            m.face([pts[a], pts[b], pts[c_]], n, (98, 96, 92))
    return m


CHUNK = debris_chunk()
CHUNK_BIG = mm.Model()
CHUNK2 = mm.Model()
for (_p, _n, _c, _tg) in CHUNK.F:
    CHUNK_BIG.face(_p * 3.0, _n, _c, _tg)
    CHUNK2.face(_p * 1.8, _n, (128, 124, 118), _tg)


def speed_lines(la, t, k_speed=1.3, a=0.3):
    for k in range(28):
        y0 = (k * 97) % 1100 + 300
        x0 = ((k * 0.137 - t * k_speed) % 1.0) * W
        la.line([(x0, y0 * S), (x0 + 90 * S, y0 * S)], fill=sc3((150, 170, 230), a), width=1)


def plume(la, c, p0, d, length, col, a, t, wid=1.0):
    if a <= 0.01:
        return
    for k in range(9):
        u = k / 8.0
        p = p0 + d * length * u
        x, y, dep = proj(*p, c)
        if dep <= 0.05:
            continue
        r = (0.10 + 0.25 * u) * wid * 1200.0 / dep * S
        fl = 0.85 + 0.15 * math.sin(t * 37 + k * 1.7)
        glow_dot(la, x * S, y * S, r, col, a * (1 - u) ** 1.2 * fl)
    x, y, dep = proj(*p0, c)
    if dep > 0.05:
        glow_dot(la, x * S, y * S, 0.12 * wid * 1200.0 / dep * S, lc(col, (255, 255, 255), 0.5), a)


def dashed(la, c, p0, p1, col, a, n=24, near=0.05, w=3, phase=0.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    for k in range(n):
        u0 = (k + phase % 1.0) / n
        u1 = u0 + 0.5 / n
        if u1 > 1:
            continue
        line3(la, c, tuple(p0 + (p1 - p0) * u0), tuple(p0 + (p1 - p0) * u1), sc3(col, a), max(1, int(w * S)), near)


# =====================================================================
# Render
# =====================================================================
DARK = []


def render(t):
    env = env_at(t)
    c = cam_for(env, t)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    buf = np.zeros((H, W, 3), np.float32)
    info = {}
    arr = None
    base = None

    if env == 'hook':
        arr = np.full((H, W, 3), 5.0, np.float32)
        earth(arr, c, -96.0 - 0.62 * t, norm((0.7, 0.3, -0.62)), atmo=1.1)
        Pp = sat_pos(ALL_SATS, t)
        a_s = ease(seg(t, 0.15, 1.4))
        draw_sat_cloud(buf, c, Pp, ALL_COL, ALL_INT * 0.95 * a_s, 2)
        if t > 6.3:
            a = ease(seg(t, 6.5, 7.0))
            pr = pair_pos(t)
            info['pair'] = []
            for p, ph in zip(pr, (0.0, 0.5)):
                x, y, dep = proj(*p, c)
                glow_dot(la, x * S, y * S, (7 + 3 * math.sin(t * 9 + ph * 6)) * S, RED, a)
                dashed(la, c, p, X_HOOK, RED, 0.8 * a, 16, 50.0, 3, t * 2)
                info['pair'].append((x, y))
            x, y, dep = proj(*X_HOOK, c)
            glow_dot(la, x * S, y * S, (12 + 6 * math.sin(t * 10)) * S, (255, 120, 120), 0.6 * a)
            info['X'] = (x, y)
    elif env == 'crash':
        arr = np.full((H, W, 3), 5.0, np.float32)
        draw_stars(arr, c)
        ge.render_earth(arr, c, CR_CTR, 6.371e6, 98.0 - 0.05 * t, CR_SUN, atmo=1.2, lights_k=1.0, tilt_deg=35.0, smooth=True)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        draw_crash(base, bd, od, la, buf, c, t, info)
        if t < T_IMP:
            speed_lines(la, t, 0.9, 0.22)
    elif env == 'radar':
        base, bd = draw_radar_scene(c, t, la, od, info)
    elif env == 'predict':
        arr = np.full((H, W, 3), 5.0, np.float32)
        earth(arr, c, -40.0 - 0.6 * (t - 19.65), norm((0.6, 0.45, -0.66)), atmo=1.0)
        Pp = sat_pos(ALL_SATS, t)
        draw_sat_cloud(buf, c, Pp, ALL_COL, ALL_INT * 0.35, 1)
        lw = max(1, int(2 * S))
        info['now'] = []
        for pl, col, off in ((PRA, CYAN, 0.0), (PRB, ORANGE, 0.35)):
            e1, e2 = pl
            uX = 0.0
            ring = RP * (np.cos(np.linspace(0, 2 * math.pi, 181))[:, None] * e1 + np.sin(np.linspace(0, 2 * math.pi, 181))[:, None] * e2)
            occ = occl_np(c, ring)
            sx, sy, dep = proj_np_(ring, c)
            for i in range(180):
                if not (occ[i] or occ[i + 1]):
                    la.line([(sx[i] * S, sy[i] * S), (sx[i + 1] * S, sy[i + 1] * S)], fill=sc3(col, 0.28), width=lw)
            u_now = uX - 0.78 - off * 0.25 + 0.03 * (t - 19.65)
            p_now = RP * (math.cos(u_now) * e1 + math.sin(u_now) * e2)
            # camino predicho (raya a raya hasta el cruce)
            us = np.linspace(u_now, uX, 40)
            pts = RP * (np.cos(us)[:, None] * e1 + np.sin(us)[:, None] * e2)
            gk = ease(seg(t, 20.6, 22.0))
            for i in range(0, 39, 2):
                if i / 39 > gk:
                    break
                line3(la, c, tuple(pts[i]), tuple(pts[i + 1]), sc3(col, 0.95), max(2, int(4 * S)), 50.0)
            # "fantasma": la computadora adelanta el tiempo
            ph = ((t - 21.0) / 1.6) % 1.0 if t > 21.0 else 0.0
            if t > 21.0:
                ug = u_now + (uX - u_now) * ease(ph)
                pg = RP * (math.cos(ug) * e1 + math.sin(ug) * e2)
                x, y, dep = proj(*pg, c)
                glow_dot(la, x * S, y * S, 7 * S, col, 0.55 * (1 - ph * 0.5))
            x, y, dep = proj(*p_now, c)
            sat_icon(la, x * S, y * S, 3.2 * S, 1.0, col)
            info['now'].append((x, y))
        x, y, dep = proj(*X_PRED, c)
        aa = ease(seg(t, 22.0, 22.4))
        if aa > 0:
            pul = 0.5 + 0.5 * math.sin(t * 9)
            glow_dot(la, x * S, y * S, (14 + 10 * pul) * S, RED, 0.75 * aa)
            la.ellipse((x * S - 36 * S, y * S - 36 * S, x * S + 36 * S, y * S + 36 * S), outline=sc3(RED, aa), width=max(2, int(3 * S)))
        info['X'] = (x, y)
    elif env == 'dodge':
        arr = np.full((H, W, 3), 5.0, np.float32)
        draw_stars(arr, c)
        ge.render_earth(arr, c, LEO_CTR, 6.371e6, -60.0 - 0.15 * t, LEO_SUN, atmo=1.2, tilt_deg=48.0, smooth=True)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        dz = 4.2 * ease(seg(t, T_BURN + 0.2, T_BURN + 1.6))
        pos = np.array([0.0, 0.0, dz])
        Rm = np.eye(3)
        xd = 44.0 - 22.0 * (t - (T_PASS - 2.0))
        pd = np.array([xd, 0.0, 0.0])
        fl = starlink_faces(c, pos, Rm, SAT_SUN)
        fl += model_faces(c, CHUNK2, pd, rodrigues(norm(np.array([0.3, 1.0, 0.4])), t * 3.0), SAT_SUN, 1.0, near=0.3)
        draw_list(bd, od, fl)
        sl_panel_lines(bd, c, pos, Rm)
        # camino del pedazo y posición original
        a_p = ease(seg(t, 25.5, 26.0))
        dashed(la, c, (40.0, 0, 0), (-40.0, 0, 0), RED, 0.7 * a_p, 40, 0.3, 3, -t * 1.5)
        ghost = 1 - ease(seg(t, T_BURN + 0.3, T_BURN + 1.4))
        if ghost < 0.98 and a_p > 0:
            pts = [(-1.6, 0, -0.7), (1.6, 0, -0.7), (1.6, 0, 0.7), (-1.6, 0, 0.7), (-1.6, 0, -0.7)]
            polyline3(la, c, pts, sc3(RED, 0.8 * a_p), max(2, int(3 * S)), 0.3)
        burn = ease(seg(t, T_BURN, T_BURN + 0.2)) * (1 - ease(seg(t, T_BURN + 1.4, T_BURN + 1.8)))
        plume(la, c, pos + np.array([-1.0, 0.0, -0.72]), np.array([0, 0, -1.0]), 2.6, HALL, burn, t, 1.4)
        if t > T_BURN + 1.0:
            g = ease(seg(t, T_BURN + 1.0, T_BURN + 1.5))
            dashed(la, c, (30.0, 0, dz), (-30.0, 0, dz), GREEN, 0.6 * g, 30, 0.3, 3, t * 1.5)
        info['pos'], info['pd'] = pos, pd
        speed_lines(la, t, 0.6, 0.18)
    elif env == 'iss':
        arr = np.full((H, W, 3), 5.0, np.float32)
        draw_stars(arr, c)
        ge.render_earth(arr, c, ISS_CTR, 6.371e6, -110.0 - 1.6 * (t - 29.45), norm((-0.5, 0.6, -0.55)), atmo=1.1, tilt_deg=60.0, smooth=True)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        L = norm((-0.5, 0.6, -0.55))
        Rm = mm.rot(math.radians(12))
        rise = 1.2 * ease(seg(t, T_ISSB, T_ISSB + 4.0))
        pos = np.array([0.0, rise, 0.0])
        fl = model_faces(c, ISS, pos, Rm, L, 1.0, near=1.0)
        pdx = np.array([-150.0 + 60.0 * (t - 29.45), -60.0, 70.0])
        fl += model_faces(c, CHUNK_BIG, pdx, rodrigues(norm(np.array([0.2, 1.0, 0.5])), t * 2.2), L, 1.0, near=1.0)
        draw_list(bd, od, fl)
        for x in (-50, -38, 38, 50):
            for s in (-1, 1):
                for k in range(1, 6):
                    zz = s * (3 + 33 * k / 6)
                    line3(bd, c, tuple(pos + Rm @ np.array([x - 5.5, 0.12, zz])), tuple(pos + Rm @ np.array([x + 5.5, 0.12, zz])), (120, 80, 40), max(1, int(1.5 * S)), 0.5)
        burn = ease(seg(t, T_ISSB, T_ISSB + 0.3)) * (1 - ease(seg(t, 34.1, 34.4)))
        for pa in ISS_AFT:
            plume(la, c, pos + Rm @ pa, Rm @ np.array([0, 0, -1.0]), 16.0, (255, 196, 140), burn * 0.8, t, 11.0)
        info['pdx'] = pdx
        info['aft'] = pos + Rm @ np.array([0, -3, -30.6])
        speed_lines(la, t, 1.2, 0.2)
    elif env == 'xray':
        arr = np.full((H, W, 3), 5.0, np.float32)
        draw_stars(arr, c)
        ge.render_earth(arr, c, LEO_CTR, 6.371e6, -70.0 - 0.15 * t, LEO_SUN, atmo=1.2, tilt_deg=48.0, smooth=True)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        xr = ease(seg(t, T_XR, T_XR + 0.8))
        fl = starlink_faces(c, (0, 0, 0), np.eye(3), SAT_SUN, xr)
        draw_list(bd, od, fl)
        sl_panel_lines(bd, c, (0, 0, 0), np.eye(3))
        xray_starlink(la, c, t, xr)
        info['xr'] = xr
    elif env == 'fleet':
        arr = np.full((H, W, 3), 5.0, np.float32)
        earth(arr, c, -20.0 - 0.6 * (t - 38.95), norm((0.55, 0.35, -0.75)), atmo=1.0)
        Pp = sat_pos(STARLINK, t)
        n = len(Pp)
        draw_sat_cloud(buf, c, Pp, (0.78, 0.86, 1.0), 0.8, 2)
        a_m = ease(seg(t, 39.6, 40.2))
        occ = occl_np(c, Pp)
        for kk in range(-6, 1):
            bin_ = int(t * 10) + kk
            age = (t * 10 - bin_) / 7.0
            rs = np.random.RandomState(bin_ % 100000)
            idx = rs.randint(0, n, 14)
            for i in idx:
                if occ[i]:
                    continue
                x, y, dep = proj(*Pp[i], c)
                if dep < 100:
                    continue
                rr = (8 + 44 * age) * S
                la.ellipse((x * S - rr, y * S - rr, x * S + rr, y * S + rr), outline=sc3(HALL, a_m * (1 - age)), width=max(2, int(3 * S)))
                glow_dot(la, x * S, y * S, 6 * S, (255, 255, 255), a_m * (1 - age))
    elif env == 'pad':
        arr, dy = ground_scene(c, 'dawn', coast=380.0)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        L = norm((-0.55, 0.45, -0.7))
        fl = model_faces(c, TOWER, (0, 0, 0), np.eye(3), L, 1.0, near=1.0)
        fl += model_faces(c, ROCKET, (0, 0.6, 0), mm.rot(math.radians(10)), L, 1.0, near=1.0)
        draw_list(bd, od, fl)
        # cables de pararrayos
        for (p0, p1) in (((-45, 108, -30), (45, 108, -32)), ((-45, 108, -30), (2, 108, 52)), ((45, 108, -32), (2, 108, 52))):
            pts = [(lerp(p0[0], p1[0], u), p0[1] - 18 * 4 * u * (1 - u), lerp(p0[2], p1[2], u)) for u in np.linspace(0, 1, 20)]
            polyline3(bd, c, pts, (90, 92, 100), max(1, int(1.2 * S)), 1.0)
        # vapor de oxígeno líquido
        for k in range(10):
            ph = ((t * 0.35 + k * 0.1) % 1.0)
            p = np.array([2.2 + 6 * ph, 47.0 - 2 + 4 * math.sin(k), -0.5 + k * 0.1])
            x, y, dep = proj(*p, c)
            if dep > 1:
                rr = (1.2 + 5 * ph) * 1200 / dep * S
                od.ellipse((x * S - rr, y * S - rr, x * S + rr, y * S + rr), fill=(240, 240, 245, int(90 * (1 - ph))))
        for k in range(8):
            ph = ((t * 0.25 + k * 0.125) % 1.0)
            p = np.array([-6 + 12 * (k / 8.0), 1.5 + 4 * ph, -9 - 10 * ph])
            x, y, dep = proj(*p, c)
            if dep > 1:
                rr = (3 + 9 * ph) * 1200 / dep * S
                od.ellipse((x * S - rr, y * S - rr * 0.7, x * S + rr, y * S + rr * 0.7), fill=(236, 236, 240, int(70 * (1 - ph))))
        info['rocket_top'] = (0, 74, 0)
    elif env == 'window':
        arr = np.full((H, W, 3), 5.0, np.float32)
        spin = w_spin(t)
        earth(arr, c, spin, norm((0.5, 0.5, -0.7)), atmo=1.0)
        rp = RE + 550.0
        qs = np.linspace(0, 2 * math.pi, 241)
        ring = rp * (np.cos(qs)[:, None] * W_A + np.sin(qs)[:, None] * W_B)
        occ = occl_np(c, ring)
        sx, sy, dep = proj_np_(ring, c)
        a_r = ease(seg(t, 49.3, 50.0))
        lw = max(2, int(4 * S))
        for i in range(240):
            if not (occ[i] or occ[i + 1]):
                la.line([(sx[i] * S, sy[i] * S), (sx[i + 1] * S, sy[i + 1] * S)], fill=sc3(CYAN, 0.75 * a_r), width=lw)
        s_now = _site(spin, RE + 5)
        if not occl_np(c, s_now[None, :])[0]:
            x, y, dep = proj(*s_now, c)
            pul = 0.5 + 0.5 * math.sin(t * 8)
            glow_dot(la, x * S, y * S, (8 + 4 * pul) * S, ORANGE, 1.0)
            glow_dot(la, x * S, y * S, 3.5 * S, (255, 255, 255), 1.0)
            info['site'] = (x, y)
        if t > T_LAUNCH:
            u = clamp((t - T_LAUNCH) / 2.4)
            pts = []
            for v in np.linspace(0, u, 40):
                th = 0.42 * v
                d = math.cos(th) * W_A + math.sin(th) * W_B
                r = RE + 8 + 545.0 * (1 - (1 - v) ** 2)
                pts.append(d * r)
            Pt = np.array(pts)
            occ2 = occl_np(c, Pt)
            sx2, sy2, _ = proj_np_(Pt, c)
            for i in range(len(pts) - 1):
                if not (occ2[i] or occ2[i + 1]):
                    la.line([(sx2[i] * S, sy2[i] * S), (sx2[i + 1] * S, sy2[i + 1] * S)], fill=sc3((255, 230, 190), 1.0), width=max(2, int(5 * S)))
            if u < 1 and not occ2[-1]:
                glow_dot(la, sx2[-1] * S, sy2[-1] * S, 10 * S, (255, 240, 210), 1.0)
            if u >= 1:
                sat_icon(la, sx2[-1] * S, sy2[-1] * S, 2.4 * S, 1.0, GREEN)
        th_l = 0.42 * 0.6
        info['ring_lbl'] = proj(*(rp * (math.cos(-0.9) * W_A + math.sin(-0.9) * W_B)), c)[:2]
    else:  # deploy
        arr = np.full((H, W, 3), 5.0, np.float32)
        draw_stars(arr, c)
        ge.render_earth(arr, c, LEO_CTR, 6.371e6, -150.0 - 0.15 * t, LEO_SUN, atmo=1.2, tilt_deg=55.0, smooth=True)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        L = SAT_SUN
        Rs = mm.rot(0, math.radians(4), 0)
        fl = model_faces(c, STAGE, (0, 0, 0), Rs, L, 1.0, near=0.3)
        info['pays'] = []
        for k in range(6):
            off = PAY_OFF[k]
            radial = norm(np.array([0.0, off[1], off[2]]))
            Rk = mm.rot(0, 0, math.atan2(off[2], off[1]))
            if t < T_SEPS[k]:
                p = Rs @ off
                Rp = Rs @ Rk
            else:
                dt = t - T_SEPS[k]
                p = Rs @ (off + np.array([0.95, 0, 0]) * dt + radial * 0.55 * dt)
                Rp = Rs @ Rk @ rodrigues(norm(np.array([0.3, 0.6, 0.7]) + 0.2 * k), 0.35 * dt * (1 + 0.3 * k))
                if dt < 0.5:
                    x, y, dep = proj(*(Rs @ (off + radial * 0.1)), c)
                    if dep > 0.3:
                        glow_dot(la, x * S, y * S, (8 + 30 * dt) * S, (230, 236, 255), 0.5 * (1 - dt / 0.5))
            fl += model_faces(c, PAYS[k], p, Rp, L, 1.0, near=0.3)
            info['pays'].append(p)
        draw_list(bd, od, fl)
        info['stage'] = Rs @ np.array([0.0, 1.9, 0.0])
        info['eng'] = Rs @ np.array([-7.2, 0.0, 0.0])

    # ---------- composición ----------
    if arr is None:
        arr = np.asarray(base, np.float32)
    imgA = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")
    LAa = np.asarray(LA, np.float32) + buf
    gl = glow_of(Image.fromarray(np.clip(LAa, 0, 255).astype(np.uint8)), 4)
    out = np.asarray(imgB, np.float32) + LAa + 1.5 * gl
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
    hud(l2, c, t, env, info)
    if DARK:
        mk = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mk)
        for (x0, y0, x1, y1, a) in DARK:
            md.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=int(30 * S), fill=int(255 * 0.62 * a))
        out = out * (1 - np.asarray(mk, np.float32)[..., None] / 255.0)
    out = out + np.asarray(L2, np.float32) + 1.2 * glow_of(L2, 3)
    out = out * (seg(t, 0.0, 0.3) * (1 - seg(t, DUR - 0.5, DUR)))
    return np.clip(out, 0, 255).astype(np.uint8)


def xray_starlink(la, c, t, xr):
    if xr <= 0.01:
        return
    w = max(2, int(3 * S))
    # tanque de argón (cilindro a lo largo de x)
    tz = -0.3
    for x in np.linspace(-1.25, -0.15, 6):
        pts = [(x, 0.085 * math.sin(q), tz + 0.085 * math.cos(q)) for q in np.linspace(0, 2 * math.pi, 25)]
        polyline3(la, c, pts, sc3(CYAN, 0.8 * xr), max(1, int(2 * S)), 0.02)
    for q in np.linspace(0, 2 * math.pi, 9)[:-1]:
        line3(la, c, (-1.25, 0.085 * math.sin(q), tz + 0.085 * math.cos(q)), (-0.15, 0.085 * math.sin(q), tz + 0.085 * math.cos(q)), sc3(CYAN, 0.6 * xr), max(1, int(2 * S)), 0.02)
    # propulsor de efecto Hall (anillo en la cara -z)
    hc = np.array([-1.0, 0.0, -0.71])
    for r in (0.07, 0.045):
        pts = [tuple(hc + np.array([r * math.cos(q), r * math.sin(q), 0.0])) for q in np.linspace(0, 2 * math.pi, 29)]
        polyline3(la, c, pts, sc3(HALL, xr), w, 0.02)
    # tubería del tanque al propulsor con gas que fluye
    path = [(-0.7, 0.0, tz - 0.085), (-0.7, 0.0, -0.55), (-1.0, 0.0, -0.55), (-1.0, 0.0, -0.69)]
    polyline3(la, c, path, sc3((120, 200, 230), 0.7 * xr), max(1, int(2 * S)), 0.02)
    pr, ss = resample(path, 0.01)
    pulses(la, c, pr, ss, t, 0.35, [1, 0, 1, 0, 1, 1, 0], xr, (200, 240, 255), 0.03, max(2, int(3 * S)))
    plume(la, c, hc + np.array([0, 0, -0.02]), np.array([0, 0, -1.0]), 0.8, HALL, 0.6 * xr * (0.75 + 0.25 * math.sin(t * 5)), t, 0.5)
    # computadora
    x0, x1, z0, z1 = 0.25, 1.0, 0.08, 0.5
    pts = [(x0, 0.0, z0), (x1, 0.0, z0), (x1, 0.0, z1), (x0, 0.0, z1), (x0, 0.0, z0)]
    polyline3(la, c, pts, sc3(GREEN, 0.9 * xr), w, 0.02)
    for (cx, cz) in ((0.42, 0.2), (0.62, 0.36), (0.82, 0.18), (0.45, 0.4)):
        pts = [(cx - 0.05, 0.0, cz - 0.05), (cx + 0.05, 0.0, cz - 0.05), (cx + 0.05, 0.0, cz + 0.05), (cx - 0.05, 0.0, cz + 0.05), (cx - 0.05, 0.0, cz - 0.05)]
        polyline3(la, c, pts, sc3(GREEN, 0.7 * xr * (0.6 + 0.4 * math.sin(t * 7 + cx * 9))), max(1, int(2 * S)), 0.02)
    # cable de la computadora al propulsor (la orden de encender)
    path2 = [(0.25, 0.0, 0.2), (-0.05, 0.0, 0.2), (-0.05, 0.0, -0.6), (-0.95, 0.0, -0.6)]
    polyline3(la, c, path2, sc3(GREEN, 0.4 * xr), max(1, int(1.5 * S)), 0.02)
    pr2, ss2 = resample(path2, 0.01)
    pulses(la, c, pr2, ss2, t, 0.8, [1, 0, 0, 1, 0, 0], xr, (190, 255, 210), 0.025, max(2, int(2 * S)))
    # escáner
    u = -1.6 + ((t * 0.6) % 1.0) * 3.2
    pts = [(u, 0.14, -0.72), (u, 0.14, 0.72), (u, -0.14, 0.72), (u, -0.14, -0.72), (u, 0.14, -0.72)]
    polyline3(la, c, pts, sc3(BLUE, 0.9 * xr), w, 0.02)


# =====================================================================
# HUD
# =====================================================================
def fmt_int(n):
    return f"{int(n):,}"


def traffic_light(l2, x, y, a):
    if a <= 0:
        return
    DARK.append((x - 80, y - 150, x + 80, y + 150, a))
    l2.rounded_rectangle((*P(x - 52, y - 120), *P(x + 52, y + 120)), radius=int(22 * S), fill=sc3((34, 36, 44), a), outline=sc3((150, 150, 170), a), width=max(2, int(3 * S)))
    for k, col in enumerate(((255, 70, 70), (255, 200, 60), (70, 230, 120))):
        cy_ = y - 72 + k * 72
        l2.ellipse((*P(x - 28, cy_ - 28), *P(x + 28, cy_ + 28)), fill=sc3(col, 0.25 * a), outline=sc3(col, 0.5 * a), width=max(1, int(2 * S)))
    l2.line([P(x - 90, y + 130), P(x + 90, y - 130)], fill=sc3(RED, a), width=max(4, int(10 * S)))


def warn_icon(l2, x, y, r, a, col=RED):
    if a <= 0:
        return
    l2.polygon([P(x, y - r), P(x + r * 0.95, y + r * 0.7), P(x - r * 0.95, y + r * 0.7)], outline=sc3(col, a), width=max(2, int(4 * S)))
    l2.line([P(x, y - r * 0.4), P(x, y + r * 0.2)], fill=sc3(col, a), width=max(2, int(5 * S)))
    l2.ellipse((*P(x - 4, y + 0.38 * r - 4), *P(x + 4, y + 0.38 * r + 4)), fill=sc3(col, a))


def hud(l2, c, t, env, info):
    def label(txt, target, text_pos, anchor, a, col=(220, 220, 240)):
        if a <= 0:
            return
        f = F(B, 30)
        tw = f.getlength(txt) / S
        tx, ty = text_pos
        DARK.append(((tx - tw - 20) if anchor == "rm" else tx - 20, ty - 28, (tx + 20) if anchor == "rm" else tx + tw + 20, ty + 28, a * 0.8))
        l2.text(P(tx, ty), txt, font=f, fill=sc3(col, a), anchor=anchor)
        ex = (tx - tw - 14) if anchor == "rm" else (tx + tw + 14)
        l2.line([P(*target), P(ex, ty)], fill=sc3((170, 170, 220), a), width=max(1, int(2 * S)))
        rr = 6 * S
        px, py = P(*target)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), outline=sc3((230, 230, 250), a), width=max(1, int(2 * S)))

    def pill(txt, y, a, col=BLUE, w=560, size=36):
        if a <= 0:
            return
        DARK.append((540 - w / 2, y - 42, 540 + w / 2, y + 42, a))
        l2.rounded_rectangle((*P(540 - w / 2, y - 42), *P(540 + w / 2, y + 42)), radius=int(42 * S), outline=sc3(col, a), width=max(2, int(3 * S)))
        l2.text(P(540, y), txt, font=F(B, size), fill=sc3((235, 240, 255), a), anchor="mm")

    def note(txt, a, y=1860):
        if a > 0:
            l2.text(P(1040, y), txt, font=F(B, 22), fill=sc3((165, 165, 195), a * 0.85), anchor="rm")

    def win(a, b, e=0.4):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def P3(p):
        sx, sy, _ = proj(*p, c)
        return (sx, sy)

    for ct in CUTS:
        if abs(t - ct) < 0.25:
            return
    if env == 'hook':
        a = win(WT(0, 5) - 0.1, 6.5)
        if a > 0:
            DARK.append((150, 1440, 930, 1700, a))
            n = 15900 * ease(seg(t, WT(0, 5) - 0.1, WT(0, 7) + 0.2))
            l2.text(P(540, 1520), "≈" + fmt_int(round(n, -2)), font=F(M, 84), fill=sc3((240, 244, 255), a), anchor="mm")
            l2.text(P(540, 1620), "SATÉLITES ACTIVOS", font=F(B, 36), fill=sc3(CYAN, a), anchor="mm")
            note("ESA · OCTUBRE 2026 · TIEMPO ACELERADO", a)
        pill("27,000 km/h EN ÓRBITA BAJA", 1780, win(WT(0, 10) - 0.1, 6.5), ORANGE, 720, 34)
        traffic_light(l2, 880, 560, win(WT(0, 15) - 0.1, 6.55, 0.3))
        a = win(6.75, 8.45, 0.3)
        if a > 0 and 'pair' in info:
            for (x, y) in info['pair']:
                DARK.append((x - 40, y - 40, x + 40, y + 40, a * 0.0))
                for (sx_, sy_) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    l2.line([P(x + sx_ * 34, y + sy_ * 34), P(x + sx_ * 34, y + sy_ * 18)], fill=sc3(RED, a), width=max(2, int(3 * S)))
                    l2.line([P(x + sx_ * 34, y + sy_ * 34), P(x + sx_ * 18, y + sy_ * 34)], fill=sc3(RED, a), width=max(2, int(3 * S)))
            if 'X' in info:
                x, y = info['X']
                l2.text(P(x, y - 70), "?", font=F(B, 84), fill=sc3((255, 140, 140), a), anchor="mm")
    if env == 'crash':
        pill("10 FEB 2009 · SOBRE SIBERIA", 1560, win(8.9, 14.7), (190, 200, 255), 760, 34)
        a = win(8.9, T_IMP - 0.1, 0.3)
        if a > 0 and 'A' in info:
            label("IRIDIUM 33", P3(info['A']), (1020, 520), "rm", a, (255, 220, 160))
            label("KOSMOS 2251", P3(info['B']), (60, 1380), "lm", a, (190, 210, 255))
        pill("CHOQUE A ≈42,000 km/h", 1680, win(T_IMP - 0.6, 12.2), RED, 640, 34)
        a = win(WT(2, 14) - 0.2, 14.7)
        if a > 0:
            DARK.append((120, 1380, 960, 1500, a))
            n = 2300 * ease(seg(t, WT(2, 14) - 0.2, WT(2, 16) + 0.3))
            l2.text(P(540, 1440), "+" + fmt_int(round(n, -1)) + " PEDAZOS RASTREADOS", font=F(B, 40), fill=sc3((255, 220, 200), a), anchor="mm")
        note("RECREACIÓN · CÁMARA LENTA", win(8.9, 14.7))
    if env == 'radar':
        a = win(15.3, 19.6)
        if a > 0:
            label("RADAR", P3(tuple(ARR_C)), (1020, 1080), "rm", a, (220, 230, 245))
            label("TELESCOPIO", P3(tuple(DOME_C + np.array([0, 11, 0]))), (60, 1150), "lm", ease(seg(t, WT(3, 4) - 0.1, WT(3, 4) + 0.3)) * a, (220, 230, 245))
            for (x, y, hit, k) in info.get('trk', []):
                if hit or (k % 3 == 0 and t > 16.5):
                    col = GREEN
                    for (sx_, sy_) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                        l2.line([P(x + sx_ * 26, y + sy_ * 26), P(x + sx_ * 26, y + sy_ * 12)], fill=sc3(col, a), width=max(1, int(2 * S)))
                        l2.line([P(x + sx_ * 26, y + sy_ * 26), P(x + sx_ * 12, y + sy_ * 26)], fill=sc3(col, a), width=max(1, int(2 * S)))
        a = win(WT(3, 7) - 0.2, 19.6)
        if a > 0:
            DARK.append((150, 1460, 930, 1720, a))
            n = 47000 * ease(seg(t, WT(3, 7) - 0.2, WT(3, 9) + 0.2))
            l2.text(P(540, 1540), "≈" + fmt_int(round(n, -2)), font=F(M, 84), fill=sc3((240, 244, 255), a), anchor="mm")
            l2.text(P(540, 1640), "OBJETOS RASTREADOS", font=F(B, 36), fill=sc3(GREEN, a), anchor="mm")
        note("ESA 2026 · ILUSTRACIÓN", win(15.3, 19.6))
    if env == 'predict':
        a = win(20.2, 25.2)
        if a > 0:
            DARK.append((90, 1380, 990, 1780, a))
            l2.text(P(540, 1430), "PREDICCIÓN DE ÓRBITAS", font=F(B, 34), fill=sc3((220, 225, 245), a), anchor="mm")
            rows = (("ACERCAMIENTO EN", "3 DÍAS", ease(seg(t, 21.2, 21.6))), ("DISTANCIA MÍNIMA", "150 m", ease(seg(t, 22.0, 22.4))))
            for i, (k_, v_, aa) in enumerate(rows):
                y = 1510 + i * 70
                l2.text(P(130, y), k_, font=F(B, 32), fill=sc3((200, 200, 225), a * aa), anchor="lm")
                l2.text(P(950, y), v_, font=F(M, 40), fill=sc3((240, 240, 255), a * aa), anchor="rm")
            aw = ease(seg(t, WT(4, 9) - 0.1, WT(4, 9) + 0.3)) * a
            if aw > 0:
                blink = 0.7 + 0.3 * math.sin(t * 10)
                warn_icon(l2, 360, 1700, 34, aw * blink)
                l2.text(P(420, 1700), "ALERTA DE CHOQUE", font=F(B, 40), fill=sc3(RED, aw * blink), anchor="lm")
        if 'X' in info:
            label("CRUCE", info['X'], (1020, 560), "rm", win(22.2, 25.2), (255, 190, 190))
        note("EJEMPLO ILUSTRATIVO", win(20.2, 25.2))
    if env == 'dodge':
        a = win(25.6, T_BURN + 0.2, 0.3)
        if a > 0:
            label("RIESGO", P3((1.2, 0.0, 0.0)), (60, 1350), "lm", a, (255, 190, 190))
        pill("ENCIENDE EL PROPULSOR", 1600, win(T_BURN, T_BURN + 2.0), HALL, 700, 34)
        a = win(25.6, T_PASS - 0.3, 0.3)
        if a > 0:
            x, y = P3(tuple(info['pd']))
            for (sx_, sy_) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                l2.line([P(x + sx_ * 40, y + sy_ * 40), P(x + sx_ * 40, y + sy_ * 20)], fill=sc3(RED, a), width=max(2, int(3 * S)))
                l2.line([P(x + sx_ * 40, y + sy_ * 40), P(x + sx_ * 20, y + sy_ * 40)], fill=sc3(RED, a), width=max(2, int(3 * S)))
            label("BASURA ESPACIAL", (x, y - 40), (1020, 760), "rm", a, (255, 190, 190))
        a = win(T_PASS - 0.4, 29.4, 0.3)
        if a > 0:
            label("PASA A SALVO", P3(tuple(info['pos'] + np.array([1.2, 0, 0.0]))), (1020, 1400), "rm", a, (190, 255, 210))
        note("DISTANCIAS EXAGERADAS · CÁMARA LENTA", win(25.6, 29.4))
    if env == 'iss':
        pill("ABRIL 2025 · MOTORES 3 min 33 s", 1600, win(WT(6, 6) - 0.1, 34.4), ORANGE, 820, 34)
        a = win(WT(6, 9) - 0.1, 34.4)
        if a > 0:
            label("PEDAZO DE COHETE (2005)", P3(tuple(info['pdx'])), (60, 1380), "lm", a, (255, 200, 170))
        note("NASA · ESCENA SIMPLIFICADA", win(29.8, 34.4))
    if env == 'xray':
        xr = info.get('xr', 0.0)
        a = win(T_XR + 0.5, 38.9) * xr
        if a > 0:
            label("TANQUE DE ARGÓN", P3((-0.7, 0.0, -0.3)), (60, 560), "lm", ease(seg(t, T_XR + 0.6, T_XR + 1.0)) * a, (190, 230, 255))
            label("PROPULSOR ELÉCTRICO", P3((-1.0, 0.0, -0.72)), (60, 1420), "lm", ease(seg(t, WT(7, 8) - 0.2, WT(7, 8) + 0.2)) * a, (220, 200, 255))
            label("COMPUTADORA: DECIDE SOLA", P3((0.62, 0.0, 0.3)), (1020, 1300), "rm", ease(seg(t, WT(7, 3) - 0.1, WT(7, 3) + 0.3)) * a, (190, 255, 210))
        pill("PROPULSOR DE EFECTO HALL", 1660, win(WT(7, 11) - 0.2, 38.9), HALL, 760, 34)
        note("INTERIOR SIMPLIFICADO", win(T_XR, 38.9))
    if env == 'fleet':
        a = win(WT(8, 4) - 0.2, 44.3)
        if a > 0:
            DARK.append((120, 1400, 960, 1740, a))
            n = 207152 * ease(seg(t, WT(8, 4) - 0.2, WT(8, 8) + 0.2))
            l2.text(P(540, 1480), fmt_int(n), font=F(M, 88), fill=sc3((240, 244, 255), a), anchor="mm")
            l2.text(P(540, 1580), "MANIOBRAS PARA ESQUIVAR", font=F(B, 36), fill=sc3(HALL, a), anchor="mm")
            l2.text(P(540, 1660), "DIC 2025 – MAY 2026", font=F(B, 30), fill=sc3((200, 200, 225), a), anchor="mm")
        pill("MÁS DE 1,000 AL DÍA", 1790, win(WT(8, 9) - 0.1, 44.3), (255, 200, 120), 560, 36)
        note("STARLINK · REPORTE DE SPACEX A LA FCC", win(39.4, 44.3), 1880)
    if env == 'pad':
        a = win(WT(9, 4) - 0.2, 49.0)
        if a > 0:
            DARK.append((90, 1360, 990, 1780, a))
            l2.text(P(540, 1410), "PLAN DE VUELO", font=F(B, 34), fill=sc3((220, 225, 245), a), anchor="mm")
            rows = (("ALTURA", "550 km"), ("INCLINACIÓN", "53°"), ("DESPEGUE", "06:42:10"))
            for i, (k_, v_) in enumerate(rows):
                aa = ease(seg(t, WT(9, 6) + 0.35 * i, WT(9, 6) + 0.35 * i + 0.3))
                y = 1490 + i * 90
                l2.text(P(130, y), k_, font=F(B, 34), fill=sc3((200, 200, 225), a * aa), anchor="lm")
                l2.text(P(950, y), v_, font=F(M, 46), fill=sc3((255, 230, 190), a * aa), anchor="rm")
        note("EJEMPLO · COHETE GENÉRICO", win(45.0, 49.0))
    if env == 'window':
        a = win(49.4, 56.2)
        if a > 0:
            rl = info.get('ring_lbl')
            if rl:
                label("ÓRBITA PLANEADA (FIJA)", rl, (1020, 520), "rm", a, (190, 230, 255))
            if 'site' in info and t < T_LAUNCH + 1.6:
                label("BASE DE LANZAMIENTO", info['site'], (60, 1420), "lm", a * (1 - ease(seg(t, T_LAUNCH + 1.0, T_LAUNCH + 1.6))), (255, 210, 170))
            DARK.append((200, 1560, 880, 1700, a))
            if t < T_LAUNCH:
                rem = (T_LAUNCH - t) * W_RATE * 86164.0 / 360.0
                hh, mm_ = int(rem // 3600), int((rem % 3600) // 60)
                ss = int(rem % 60)
                l2.text(P(540, 1600), "FALTAN", font=F(B, 30), fill=sc3((200, 200, 225), a), anchor="mm")
                l2.text(P(540, 1655), f"{hh:02d}:{mm_:02d}:{ss:02d}", font=F(M, 52), fill=sc3((240, 240, 255), a), anchor="mm")
            else:
                k = 0.75 + 0.25 * math.sin(t * 10)
                l2.text(P(540, 1630), "¡DESPEGUE!", font=F(B, 60), fill=sc3((255, 220, 160), a * k), anchor="mm")
        pill("VENTANA DE LANZAMIENTO", 1800, win(WT(10, 16) - 0.2, 56.2), CYAN, 700, 36)
        note("TIEMPO ACELERADO", win(49.4, 56.2), 1240)
    if env == 'deploy':
        a = win(56.7, T_OUT)
        if a > 0:
            label("COMPUTADORA DE VUELO: GPS + SENSORES", P3(tuple(info['stage'])), (60, 1340), "lm", ease(seg(t, WT(11, 2) - 0.1, WT(11, 2) + 0.3)) * a, (220, 230, 245))
        pill("ALTURA Y VELOCIDAD EXACTAS", 1600, win(WT(11, 6) - 0.2, T_OUT), CYAN, 800, 34)
        pill("UNO TRAS OTRO", 1720, win(WT(11, 11) - 0.2, T_OUT), GREEN, 480, 34)
        note("MISIÓN COMPARTIDA · EJEMPLO", win(56.7, T_OUT))
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
        os.makedirs("/home/claude/cho_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/cho_prev/t_{ts}.png")
            print(ts, f"{time.time() - t0:.2f}s", flush=True)
    elif mode == "times":
        for i, ph in enumerate(anim.PH):
            print(i, [round(s, 2) for s in ph['starts']])
        print("T_IMP", round(T_IMP, 2), "T_BURN", round(T_BURN, 2), "T_LAUNCH", round(T_LAUNCH, 2), "T_SEPS", [round(x, 2) for x in T_SEPS])
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
