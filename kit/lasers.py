"""Mente en órbita — Satélites que se hablan con láseres (video 6).
Escenas: dos satélites sobre la Tierra de noche · malla de láseres alrededor del planeta · radio vs láser y "fibra sin cable" ·
terminal láser en rayos X · persecución a 27,000 km/h · la moneda a 1.6 km (calle) · carrera vacío vs cable submarino ·
casa con antena: las nubes bloquean el láser, la radio pasa · cierre."""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
import nc
import fo
from nc import proj, P2, vis
from fo import clip_near, poly, line3, pulses, resample, led
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of, VIOLET, BLUE, CYAN, ORANGE)
from gps_geo import (norm, cam_from, cam_keys, face, cbox, polyline3, glow_dot, ring_pts, splat)
import gps_earth as ge
import moto_model as mm

FPS = 24
DUR = 64.6
NF = int(DUR * FPS)
LASER = (255, 70, 120)
RED = (255, 80, 80)
GREEN = (90, 255, 150)

PHR = [
    (0.3, 4.3, "Los satélites modernos no usan antenas normales para hablar entre sí...", {5}),
    (4.7, 8.3, "¡disparan rayos láser invisibles a través del vacío del espacio!", {2}),
    (8.8, 13.0, "Los satélites de Starlink ya tienen miles de láseres conectándolos en órbita.", {6}),
    (13.5, 17.3, "¿Por qué láser? La radio se abre como un cono gigante;", {9}),
    (17.7, 23.6, "el láser es un hilo de luz que lleva muchos más datos: hasta 200 gigabits por segundo.", {4}),
    (24.1, 27.9, "Es luz infrarroja, como en la fibra óptica, pero sin cable.", {2}),
    (28.4, 33.3, "Por dentro, cada terminal tiene un telescopio, espejos que giran y un detector ultrasensible.", {6}),
    (33.8, 40.8, "El reto: vuelan a veintisiete mil kilómetros por hora y pueden estar a más de cinco mil kilómetros de distancia.", {1}),
    (41.3, 46.5, "La NASA lo compara con seguir una moneda en movimiento a un kilómetro y medio.", {7}),
    (47.0, 52.9, "Y un bonus: en el vacío la luz viaja casi 50% más rápido que en la fibra.", {12}),
    (53.4, 56.2, "En distancias largas, puede ganarle al cable submarino.", {4}),
    (56.7, 60.9, "Su enemigo: las nubes. Para bajar a la Tierra, todavía usan radio.", {3}),
    (61.5, 63.4, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)

CUTS = (8.55, 13.25, 28.15, 33.55, 41.05, 46.75, 56.45)
ENVS = ('sat', 'mesh', 'radio', 'xray', 'chase', 'street', 'race', 'house')
T_OUT = 61.1


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


# =====================================================================
# Estrellas
# =====================================================================
_rs = np.random.RandomState(31)
_sd = _rs.normal(size=(2600, 3))
STAR_D = _sd / np.linalg.norm(_sd, axis=1, keepdims=True)
STAR_B = _rs.uniform(0.15, 1.0, 2600) ** 2.2


def draw_stars(arr, c, k=1.0):
    dx, dy, dz = STAR_D[:, 0], STAR_D[:, 1], STAR_D[:, 2]
    x1 = dx * c['ca'] + dz * c['sa']
    z1 = -dx * c['sa'] + dz * c['ca']
    y2 = dy * c['cp'] + z1 * c['sp']
    z2 = z1 * c['cp'] - dy * c['sp']
    ok = z2 > 0.05
    sx = (540 + x1[ok] / z2[ok] * 1200.0) * S
    sy = (c['cy'] - y2[ok] / z2[ok] * 1200.0) * S
    b = STAR_B[ok]
    m = (sx >= 0) & (sx < W - 1) & (sy >= 0) & (sy < H - 1)
    xs, ys, b = sx[m].astype(int), sy[m].astype(int), b[m]
    for ch, cv in enumerate((215, 215, 255)):
        np.add.at(arr[..., ch], (ys, xs), cv * b * k)


# =====================================================================
# Modelo de satélite tipo "panel plano" (genérico, sin marcas) en metros
# =====================================================================
TERMS = [np.array([1.15, 0.13, 0.42]), np.array([1.15, 0.13, -0.42]), np.array([-1.15, 0.13, 0.0])]


def build_sat():
    m = mm.Model()
    m.box((-1.6, -0.12, -0.7), (1.6, 0.12, 0.7), (58, 60, 70))
    for i in range(6):
        for j in range(3):
            x0 = -1.4 + i * 0.47
            z0 = -0.6 + j * 0.42
            m.face([(x0, -0.125, z0), (x0 + 0.40, -0.125, z0), (x0 + 0.40, -0.125, z0 + 0.36), (x0, -0.125, z0 + 0.36)], (0, -1, 0), (214, 216, 222))
    for sx in (-1, 1):
        m.beam((sx * 1.6, 0.0, 0.0), (sx * 2.1, 0.0, 0.0), 0.08, 0.08, (160, 164, 172), side=(0, 1, 0))
        x0, x1 = (2.1, 8.3) if sx > 0 else (-8.3, -2.1)
        m.box((x0, -0.02, -1.2), (x1, 0.02, 1.2), (32, 54, 128), 'panel')
    for tp in TERMS:
        m.cyl(tp + np.array([0, 0.05, 0]), (0, 1, 0), 0.13, 0.1, (190, 194, 202), 14)
    return m


SAT = build_sat()


def term_head(pos, d):
    """cilindro de la cabeza del terminal orientado hacia d"""
    hm = mm.Model()
    hm.cyl((0, 0, 0), d, 0.105, 0.24, (214, 218, 226), 16, 'head', True, (20, 24, 34))
    return hm


def model_faces(c, model, pos, Rm, L, dim=1.0, xr=0.0, xr_tags=(), near=0.05):
    out = []
    pos = np.asarray(pos, np.float64)
    cam = np.asarray(c['pos'])
    for (pts, n, col, tag) in model.F:
        Wp = pts @ Rm.T + pos
        nw = Rm @ n
        ctr = Wp.mean(0)
        if nw @ (cam - ctr) <= 0:
            continue
        q = clip_near([tuple(p) for p in Wp], c, near)
        if len(q) < 3:
            continue
        dep = proj(*ctr, c)[2]
        cc = mm.shade(col, nw, L, dim)
        al = int(255 * (1 - 0.82 * xr)) if (xr > 0.01 and tag in xr_tags) else None
        out.append((dep, [P2(*p, c) for p in q], cc, al, tag))
    return out


def draw_list(bd, od, fl):
    fl.sort(key=lambda q: -q[0])
    for dep, pts, col, al, tag in fl:
        if al is None:
            bd.polygon(pts, fill=col)
        else:
            od.polygon(pts, fill=(*col, al))


def sat_faces(c, pos, Rm, L, targets, xr=0.0, dim=1.0):
    fl = model_faces(c, SAT, pos, Rm, L, dim)
    heads = []
    for i, tp in enumerate(TERMS):
        hp = np.asarray(pos) + Rm @ (tp + np.array([0, 0.24, 0]))
        tg = targets[i] if i < len(targets) and targets[i] is not None else hp + Rm @ np.array([0.3, 1.0, 0.2 * (i - 1)])
        d = norm(np.asarray(tg) - hp)
        hm = term_head(hp, d)
        fl += model_faces(c, hm, hp, np.eye(3), L, dim, xr, ('head',))
        heads.append((hp, d))
    return fl, heads


def panel_lines(bd, c, pos, Rm, L):
    w1 = max(1, int(1.5 * S))
    for sx in (-1, 1):
        x0, x1 = (2.1, 8.3) if sx > 0 else (-8.3, -2.1)
        n = Rm @ np.array([0, 1.0, 0])
        if not vis(c, tuple(np.asarray(pos) + Rm @ np.array([(x0 + x1) / 2, 0.03, 0])), tuple(n)):
            n = -n
        for k in range(1, 8):
            x = x0 + (x1 - x0) * k / 8
            line3(bd, c, tuple(np.asarray(pos) + Rm @ np.array([x, 0.025, -1.2])), tuple(np.asarray(pos) + Rm @ np.array([x, 0.025, 1.2])), (70, 96, 170), w1, 0.05)
        for z in (-0.4, 0.4):
            line3(bd, c, tuple(np.asarray(pos) + Rm @ np.array([x0, 0.025, z])), tuple(np.asarray(pos) + Rm @ np.array([x1, 0.025, z])), (70, 96, 170), w1, 0.05)


def beam(la, c, p0, p1, a, t, width=6, pulse=True, col=LASER):
    if a <= 0.01:
        return
    p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
    if np.linalg.norm(p1 - p0) < 1e-3:
        return
    n = 60
    pts = [tuple(p0 + (p1 - p0) * k / n) for k in range(n + 1)]
    polyline3(la, c, pts, sc3(col, 0.55 * a), max(2, int(width * S)), 0.05)
    polyline3(la, c, pts, sc3((255, 220, 235), 0.6 * a), max(1, int(width * 0.35 * S)), 0.05)
    if pulse:
        pr, ss = resample(pts, float(np.linalg.norm(p1 - p0)) / 120)
        pulses(la, c, pr, ss, t, float(np.linalg.norm(p1 - p0)) * 0.9, [1, 0, 1, 1, 0, 1, 0, 0], a, (255, 255, 255),
               float(np.linalg.norm(p1 - p0)) / 40, max(2, int(width * 0.6 * S)))


# Tierra vista desde la órbita baja (marco local en metros)
E_CTR = (0.0, -6.921e6, 0.0)
E_R = 6.371e6
E_TILT = 65.0
SUN_L = norm((0.85, 0.12, 0.5))
SAT_L = norm((0.7, 0.45, 0.55))
B_POS = np.array([-420.0, 6.0, 90.0])
B_RAD = np.array([-60.0, 0.0, 8.0])
B_CH = np.array([-80.0, 2.0, 10.0])


def space_bg(c, t, spin=-100.0, lights=1.0):
    base = Image.new("RGB", (W, H), (4, 4, 10))
    arr = np.asarray(base, np.float32).copy()
    draw_stars(arr, c)
    ge.render_earth(arr, c, E_CTR, E_R, spin, SUN_L, atmo=1.2, lights_k=lights, tilt_deg=E_TILT, smooth=True)
    return arr


# =====================================================================
# Malla de láseres (km)
# =====================================================================
RE, RS = 6371.0, 6921.0
NP_, NS_ = 24, 18
INC = math.radians(53.0)
_pl = []
for p in range(NP_):
    Om = math.radians(15.0 * p)
    e1 = np.array([math.cos(Om), 0, math.sin(Om)])
    e2 = np.array([-math.sin(Om) * math.cos(INC), math.sin(INC), math.cos(Om) * math.cos(INC)])
    _pl.append((e1, e2))
PLANES = _pl


def mesh_pos(t):
    P_ = np.zeros((NP_, NS_, 3))
    for p, (e1, e2) in enumerate(PLANES):
        th = 2 * math.pi * np.arange(NS_) / NS_ + p * 0.13 + 0.05 * t
        P_[p] = RS * (np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2)
    return P_


def occl_np(c, Pts, ctr=(0, 0, 0), R=RE):
    o = np.asarray(c['pos'], np.float64)
    d = Pts - o
    L = np.linalg.norm(d, axis=-1)
    d = d / L[..., None]
    oc = o - np.asarray(ctr)
    b = d @ oc
    cc = oc @ oc - R * R
    disc = b * b - cc
    t0 = -b - np.sqrt(np.maximum(disc, 0))
    return (disc > 0) & (t0 > 0) & (t0 < L)


def sat_icon(la, x, y, sc, a, col=CYAN):
    if a <= 0.02:
        return
    la.line([(x - 10 * sc, y), (x + 10 * sc, y)], fill=sc3((110, 150, 255), a), width=max(1, int(3 * sc)))
    glow_dot(la, x, y, 3.0 * sc, col, a)
    glow_dot(la, x, y, 1.5 * sc, (255, 255, 255), a)


def draw_mesh(arr, la, c, t, a=1.0):
    draw_stars(arr, c)
    ge.render_earth(arr, c, (0, 0, 0), RE, -100 + (t - 8.55) * 2.0, norm((0.75, 0.35, 0.55)), atmo=1.0)
    P_ = mesh_pos(t)
    occ = occl_np(c, P_)
    sx, sy, dep = proj_np_(P_, c)
    lw = max(1, int(2 * S))
    k = 0
    grow = ease(seg(t, 9.0, 11.5))
    for p in range(NP_):
        for s in range(NS_):
            if occ[p, s] or dep[p, s] < 500:
                continue
            for (q, r) in ((p, (s + 1) % NS_), ((p + 1) % NP_, s)):
                k += 1
                if occ[q, r] or dep[q, r] < 500:
                    continue
                if (k * 7919 % 100) / 100.0 > grow:
                    continue
                la.line([(sx[p, s] * S, sy[p, s] * S), (sx[q, r] * S, sy[q, r] * S)], fill=sc3(LASER, 0.55 * a), width=lw)
                ph = ((t * 0.9 + k * 0.37) % 1.0)
                if k % 3 == 0:
                    xx = lerp(sx[p, s], sx[q, r], ph) * S
                    yy = lerp(sy[p, s], sy[q, r], ph) * S
                    glow_dot(la, xx, yy, 2.2 * S, (255, 230, 240), a)
            sc_ = clamp(60000.0 / dep[p, s], 0.7, 2.2) * S
            sat_icon(la, sx[p, s] * S, sy[p, s] * S, sc_, a)


def proj_np_(Pts, c):
    x = Pts[..., 0] - c['f'][0]
    y = Pts[..., 1] - c['f'][1]
    z = Pts[..., 2] - c['f'][2]
    x1 = x * c['ca'] + z * c['sa']
    z1 = -x * c['sa'] + z * c['ca']
    y2 = y * c['cp'] + z1 * c['sp']
    z2 = z1 * c['cp'] - y * c['sp']
    dep = z2 + c['D']
    k = 1200.0 / np.maximum(dep, 1e-6)
    return 540 + x1 * k, c['cy'] - y2 * k, dep


# =====================================================================
# Carrera: vacío vs cable submarino (km)
# =====================================================================
def ll(lat, lon, r):
    return np.array(ge.surf_point((0, 0, 0), r, lat, lon, RACE_SPIN))


RACE_SPIN = -168.0
MEX = (19.4, -99.1)
TOK = (35.7, 139.7)


def gc_path(a, b, r, n=80, bulge=0.0):
    pa, pb = norm(ll(a[0], a[1], 1.0)), norm(ll(b[0], b[1], 1.0))
    om = math.acos(np.clip(pa @ pb, -1, 1))
    pts = []
    for i in range(n + 1):
        u = i / n
        p = (math.sin((1 - u) * om) * pa + math.sin(u * om) * pb) / math.sin(om)
        if bulge:
            nrm = norm(np.cross(pa, pb))
            p = norm(p + nrm * bulge * math.sin(math.pi * u))
        pts.append(p * r)
    return pts


CABLE = gc_path(TOK, MEX, RE + 15, 90, -0.30)
SKY = gc_path(TOK, MEX, RE * 1.10, 90, 0.0)
T_RACE0, T_LASER, T_CABLE = 47.4, 3.2, 4.9


def path_len(pts):
    return sum(np.linalg.norm(np.asarray(pts[i + 1]) - np.asarray(pts[i])) for i in range(len(pts) - 1))


def draw_race(arr, la, c, t):
    draw_stars(arr, c)
    ge.render_earth(arr, c, (0, 0, 0), RE, RACE_SPIN, norm((-0.4, 0.5, -0.75)), atmo=1.0)
    lw = max(2, int(4 * S))
    for pts, col, prog in ((CABLE, ORANGE, clamp((t - T_RACE0) / T_CABLE)), (SKY, CYAN, clamp((t - T_RACE0) / T_LASER))):
        P_ = np.array(pts)
        occ = occl_np(c, P_)
        sx, sy, dep = proj_np_(P_, c)
        for i in range(len(pts) - 1):
            if occ[i] or occ[i + 1]:
                continue
            la.line([(sx[i] * S, sy[i] * S), (sx[i + 1] * S, sy[i + 1] * S)], fill=sc3(col, 0.35), width=lw)
        nd = int(prog * (len(pts) - 1))
        for i in range(nd):
            if occ[i] or occ[i + 1]:
                continue
            la.line([(sx[i] * S, sy[i] * S), (sx[i + 1] * S, sy[i + 1] * S)], fill=sc3(col, 1.0), width=lw + 2)
        if 0 < prog < 1 and not occ[nd]:
            glow_dot(la, sx[nd] * S, sy[nd] * S, 9 * S, (255, 255, 255), 1.0)
        if col == CYAN:
            for i in range(0, len(pts), 9):
                if not occ[i]:
                    sat_icon(la, sx[i] * S, sy[i] * S, 1.4 * S, 0.9)
    for (la_, lo_) in (MEX, TOK):
        p = ll(la_, lo_, RE + 20)
        if not occl_np(c, p[None, :])[0]:
            x, y, _ = proj(*p, c)
            glow_dot(la, x * S, y * S, 7 * S, (255, 255, 255), 1.0)


# =====================================================================
# Calle (unidades de fo, cm) y casa con antena
# =====================================================================
DISH_BASE = np.array([-585.0, 452.0, 760.0])
DISH_N = norm((0.45, 0.89, 0.0))
SKY_SAT = np.array([-4200.0, 9000.0, 9000.0])
CLOUDS = [(-2600 + 900 * k + 300 * math.sin(k * 2.1), 2400 + 250 * math.sin(k * 1.3), 3200 + 700 * math.cos(k * 1.7), 700 + 200 * (k % 3)) for k in range(9)]


def draw_dish(bd, c, L):
    m = mm.Model()
    m.beam(DISH_BASE, DISH_BASE + np.array([0, 60, 0]), 5, 5, (60, 62, 70))
    ctr = DISH_BASE + np.array([0, 70, 0])
    a = norm(np.cross(DISH_N, (0, 0, 1)))
    b2 = np.cross(DISH_N, a)
    pts = [ctr + a * sa * 28 + b2 * sb * 40 for (sa, sb) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m.face(pts, DISH_N, (236, 238, 242))
    m.face(pts[::-1], -DISH_N, (200, 202, 208))
    fl = model_faces(c, m, (0, 0, 0), np.eye(3), L, 1.0, near=20.0)
    draw_list(bd, None, fl)


def clouds(od, c, a=1.0):
    for (x, y, z, r) in CLOUDS:
        for q in range(5):
            px, pz = x + (q - 2) * r * 0.45, z + 80 * math.sin(q * 1.7)
            sx, sy, dep = proj(px, y + 60 * math.cos(q), pz, c)
            if dep < 50:
                continue
            rr = r * (0.7 + 0.3 * math.sin(q * 2.3 + 1)) * 1200 / dep * S
            od.ellipse((sx * S - rr, sy * S - rr * 0.55, sx * S + rr, sy * S + rr * 0.55), fill=(150, 150, 172, int(150 * a)))


# =====================================================================
# Cámaras
# =====================================================================
T1 = tuple(TERMS[0] + np.array([0, 0.24, 0]))
KEYS = {
    'sat': [(0.0, 3.0, 9, 118, 760, *T1), (4.4, 3.6, 9, 106, 760, *T1), (6.2, 9.0, 12, 98, 880, -5, 0.2, 1.5), (8.55, 12.0, 13, 92, 900, -7, 0.2, 1.8)],
    'mesh': [(8.55, 10500, 18, -30, 980, 0, 0, 0), (13.25, 25000, 24, 8, 1000, 0, 0, 0)],
    'radio': [(13.25, 85, 28, -8, 900, -30, 0, 0), (23.6, 78, 30, 6, 900, -30, 0, 0), (24.1, 30, 22, 20, 900, -30, 0.5, 4),
              (28.15, 28, 22, 32, 900, -28, 0.5, 4)],
    'xray': [(28.15, 1.1, 16, 118, 900, *T1), (33.55, 0.9, 18, 150, 900, *T1)],
    'chase': [(33.55, 100, 28, 34, 900, -40, 0, 5), (37.0, 108, 27, 22, 900, -40, 0, 5), (41.05, 118, 26, 8, 900, -40, 0, 5)],
    'street': [(41.05, 3000, -1, 0, 960, 0, 170, 500), (46.75, 2900, -1, 2, 960, 0, 170, 500)],
    'race': [(46.75, 19500, 38, 0, 1000, 0, 0, 0), (56.45, 18500, 42, 4, 1000, 0, 0, 0)],
    'house': [(56.45, 1500, -12, 42, 1300, -660, 480, 750), (64.6, 1380, -14, 48, 1300, -660, 480, 750)],
}
LOGD = {'mesh': True, 'race': True, 'sat': True, 'chase': True}


def cam_for(env, t):
    return cam_keys(t, KEYS[env], LOGD.get(env, False))


# =====================================================================
# Render
# =====================================================================
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

    if env in ('sat', 'radio', 'xray', 'chase'):
        spin = -100.0 + (3.0 * (t - 33.55) if env == 'chase' else 0.15 * t)
        arr = space_bg(c, t, spin)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        A = np.zeros(3)
        if env == 'sat':
            Bp = B_POS
        elif env == 'radio':
            Bp = B_RAD
        else:
            Bp = B_CH
        jit = np.zeros(3)
        if env == 'chase':
            jit = np.array([0, 0.6 * math.sin(t * 7.3), 0.6 * math.cos(t * 5.1)]) * (1 - ease(seg(t, 36.0, 37.5)))
        tg = [Bp + jit, None, None]
        xr = ease(seg(t, 28.6, 29.4)) if env == 'xray' else 0.0
        fl, heads = sat_faces(c, A, np.eye(3), SAT_L, tg, xr)
        RmB = mm.rot(math.radians(8.0))
        flB, headsB = sat_faces(c, Bp, RmB, SAT_L, [A + np.array(T1) * 0 + heads[0][0]])
        draw_list(bd, od, fl + flB)
        panel_lines(bd, c, A, np.eye(3), SAT_L)
        panel_lines(bd, c, Bp, RmB, SAT_L)
        hp, d = heads[0]
        tip = hp + d * 0.13
        info['tip'] = tip
        info['B'] = Bp
        info['heads'] = heads
        if env == 'sat':
            a = ease(seg(t, 4.8, 5.3))
            ext = ease(seg(t, 4.9, 6.2))
            beam(la, c, tip, tip + (headsB[0][0] - tip) * ext, a, t, 7)
            glow_dot(la, *P2(*tip, c), 10 * S * (0.6 + 0.4 * a), LASER, 0.3 + 0.7 * a)
            if ext >= 1:
                glow_dot(la, *P2(*headsB[0][0], c), 12 * S, LASER, 0.8)
        elif env == 'radio':
            # cono de radio
            ra = ease(seg(t, 13.6, 14.2)) * (1 - ease(seg(t, 17.3, 17.8)))
            if ra > 0.01:
                axis = norm(Bp - tip)
                for j in range(7):
                    s = ((t - 13.6) * 0.5 + j / 7.0) % 1.0
                    ctr = tip + axis * (2 + 70 * s)
                    rr = 1 + 34 * s
                    pts = ring_pts(tuple(ctr), axis, rr, 40)
                    polyline3(la, c, pts, sc3(lc(BLUE, VIOLET, s), ra * (1 - s) * 0.9), max(2, int(3 * S)), 0.05)
            la_ = ease(seg(t, 17.8, 18.4))
            beam(la, c, tip, headsB[0][0], la_, t, 6)
            fg = ease(seg(t, 24.2, 24.9)) * (1 - ease(seg(t, 26.6, 27.6)))
            if fg > 0.01:
                p0, p1 = tip, headsB[0][0]
                axis = norm(p1 - p0)
                for frac in np.linspace(0.05, 0.95, 26):
                    ctr = p0 + (p1 - p0) * frac
                    pts = ring_pts(tuple(ctr), axis, 0.9, 24)
                    polyline3(la, c, pts, sc3((150, 200, 232), 0.35 * fg), max(1, int(2 * S)), 0.05)
                a_ = norm(np.cross(axis, (0, 1, 0)))
                b_ = np.cross(axis, a_)
                for (sa, sb) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    off = (a_ * sa + b_ * sb) * 0.9
                    line3(la, c, tuple(p0 + off), tuple(p1 + off), sc3((150, 200, 232), 0.5 * fg), max(1, int(2 * S)), 0.05)
        elif env == 'xray':
            beam(la, c, tip, tip + d * 30, 1.0, t, 6)
            xray_terminal(la, od, c, t, hp, d, xr)
        elif env == 'chase':
            beam(la, c, tip, headsB[0][0], 1.0, t, 6)
            # estelas de velocidad (estrellas que pasan)
            rs = np.random.RandomState(3)
            for k in range(36):
                y0 = rs.uniform(0, H * 0.55)
                x0 = ((rs.uniform(0, 1) - (t * 0.9)) % 1.0) * W
                la.line([(x0, y0), (x0 + 60 * S, y0)], fill=sc3((150, 160, 220), 0.35), width=1)
    elif env == 'mesh':
        arr = np.full((H, W, 3), 4.0, np.float32)
        draw_mesh(arr, la, c, t)
        base = None
    elif env == 'race':
        arr = np.full((H, W, 3), 4.0, np.float32)
        draw_race(arr, la, c, t)
        base = None
    else:
        base = Image.new("RGB", (W, H), (8, 8, 14))
        bd = ImageDraw.Draw(base)
        fo.draw_street(bd, c, t, 0.9)
        for (x, y, ph, r) in anim.STARS[:50]:
            a = 0.25 + 0.25 * math.sin(t * 1.4 + ph)
            px, py = P(x, y * 0.45)
            rr = r * S * 0.6
            la.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3((220, 210, 255), a))
        for (z0, z1) in ((520, 620), (880, 980)):
            la.polygon([P2(*p, c) for p in fo.qx(120, 250, z0, z1, -419)], fill=sc3((70, 50, 22), 1.0))
        if env == 'street':
            pt = np.array([35.0, 95.0, -2390.0])
            m = mm.Model()
            m.cyl(pt, (0, 0, 1), 2.2, 26, (40, 42, 48), 12)
            draw_list(bd, od, model_faces(c, m, (0, 0, 0), np.eye(3), norm((-0.3, 0.8, -0.5)), 1.0, near=5.0))
            k = ease(seg(t, 41.4, 42.2))
            p0 = pt + np.array([0, 0, 13])
            beam(la, c, p0, p0 + (np.array([0.0, 150.0, 5900.0]) - p0) * k, k, t, 4, pulse=False, col=(255, 40, 40))
            info['pt'] = pt
        else:
            draw_dish(bd, c, norm((-0.3, 0.8, -0.5)))
            sx, sy, dep = proj(*SKY_SAT, c)
            sat_icon(la, sx * S, sy * S, 3.0 * S, 1.0)
            info['sky_sat'] = (sx, sy)
            # láser que muere en las nubes
            a = ease(seg(t, 56.8, 57.4)) * (1 - ease(seg(t, 59.4, 60.0)))
            cl_hit = np.array([-1900.0, 2450.0, 3600.0])
            beam(la, c, SKY_SAT, cl_hit, a, t, 4, pulse=True)
            if a > 0.01:
                x, y, _ = proj(*cl_hit, c)
                glow_dot(la, x * S, y * S, (26 + 8 * math.sin(t * 9)) * S, LASER, 0.6 * a)
            clouds(od, c, 1.0)
            # radio que atraviesa las nubes
            ra = ease(seg(t, 58.3, 58.9))
            if ra > 0.01:
                tgt = DISH_BASE + np.array([0, 70, 0])
                axis = norm(tgt - SKY_SAT)
                L_ = np.linalg.norm(tgt - SKY_SAT)
                for j in range(8):
                    s = ((t - 58.3) * 0.45 + j / 8.0) % 1.0
                    ctr = SKY_SAT + axis * L_ * s
                    pts = ring_pts(tuple(ctr), axis, 300 + 1500 * (1 - abs(s - 0.5) * 2) * 0.4, 40)
                    polyline3(la, c, pts, sc3(BLUE, ra * 0.8 * math.sin(math.pi * s)), max(2, int(3 * S)), 20.0)
                x, y, _ = proj(*tgt, c)
                glow_dot(la, x * S, y * S, 10 * S, GREEN, ra * (0.6 + 0.4 * math.sin(t * 8)))

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


def xray_terminal(la, od, c, t, hp, d, xr):
    if xr <= 0.01:
        return
    a = norm(np.cross(d, (0, 1, 0)))
    b = np.cross(d, a)

    def at(u, x=0.0, y=0.0):
        return tuple(hp + d * u + a * x + b * y)

    w = max(2, int(3 * S))
    # espejo primario y secundario (telescopio)
    for (u, r, col) in ((-0.085, 0.085, CYAN), (0.07, 0.03, CYAN)):
        pts = [at(u, r * math.cos(q), r * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 33)]
        polyline3(la, c, pts, sc3(col, xr), w, 0.02)
    for q in np.linspace(0, 2 * math.pi, 9)[:-1]:
        line3(la, c, at(-0.085, 0.085 * math.cos(q), 0.085 * math.sin(q)), at(0.07, 0.03 * math.cos(q), 0.03 * math.sin(q)), sc3(BLUE, 0.5 * xr), max(1, int(2 * S)), 0.02)
    # espejo que apunta (gira)
    tilt = 0.4 * math.sin(t * 3.0)
    sq = [(-0.03, -0.03), (0.03, -0.03), (0.03, 0.03), (-0.03, 0.03), (-0.03, -0.03)]
    pts = [at(-0.105 + y * math.sin(tilt), x, y * math.cos(tilt) - 0.05) for (x, y) in sq]
    polyline3(la, c, pts, sc3(VIOLET, xr), w, 0.02)
    # láser (fuente) y detector
    pts = [at(-0.13, x * 0.04 + 0.04, y * 0.025 - 0.07) for (x, y) in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
    polyline3(la, c, pts, sc3(LASER, xr), w, 0.02)
    det = at(-0.12, -0.05, -0.07)
    glow_dot(la, *P2(*det, c), 7 * S, GREEN, xr * (0.6 + 0.4 * math.sin(t * 11)))
    # trayectoria interna de la luz
    path = [at(-0.13, 0.04, -0.07), at(-0.105, 0.0, -0.05), at(-0.085, 0.0, 0.0), at(0.07, 0.0, 0.0), at(0.15, 0.0, 0.0)]
    pr, ss = resample(path, 0.005)
    pulses(la, c, pr, ss, t, 0.4, [1, 0, 1, 1, 0], xr, (255, 220, 235), 0.012, max(2, int(3 * S)))
    # bobina de fibra amplificadora
    for k in range(4):
        r = 0.05 - k * 0.006
        pts = [at(-0.15, 0.05 + r * math.cos(q), 0.03 + r * math.sin(q) * 0.5) for q in np.linspace(0, 2 * math.pi, 25)]
        polyline3(la, c, pts, sc3(ORANGE, 0.7 * xr), max(1, int(2 * S)), 0.02)
    # escáner
    u = -0.13 + ((t * 0.5) % 1.0) * 0.27
    pts = [at(u, 0.13 * math.cos(q), 0.13 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 33)]
    polyline3(la, c, pts, sc3(BLUE, 0.9 * xr), w, 0.02)


# =====================================================================
# HUD
# =====================================================================
DARK = []


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

    def win(a, b, e=0.4):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def P3(p):
        sx, sy, _ = proj(*p, c)
        return (sx, sy)

    for ct in CUTS:
        if abs(t - ct) < 0.25:
            return
    if env == 'sat':
        a = win(1.2, 4.6)
        if a > 0:
            label("TERMINAL LÁSER", P3(info['tip']), (1020, 480), "rm", a)
        pill("LUZ INFRARROJA · INVISIBLE", 1600, win(5.4, 8.4), LASER, 780, 34)
        a = win(6.0, 8.4)
        if a > 0:
            l2.text(P(1040, 1700), "COLOR SIMULADO", font=F(B, 24), fill=sc3((170, 170, 200), a * 0.8), anchor="rm")
    if env == 'mesh':
        pill("MÁS DE 9,000 LÁSERES (2024)", 1600, win(10.2, 13.2), LASER, 800, 34)
    if env == 'radio':
        a = win(13.8, 17.4)
        if a > 0:
            label("RADIO: SE DISPERSA", (P3(info['tip'] + norm(info['B'] - info['tip']) * 40)[0], P3(info['tip'] + norm(info['B'] - info['tip']) * 40)[1] - 120), (60, 520), "lm", a, (190, 210, 255))
        a = win(18.2, 23.6)
        if a > 0:
            DARK.append((80, 1450, 1000, 1700, a))
            for i, (name, val, col, kk) in enumerate((("RADIO", 0.22, BLUE, ease(seg(t, 20.4, 21.2))), ("LÁSER · HASTA 200 Gb/s", 1.0, LASER, ease(seg(t, 21.0, 22.4))))):
                y = 1500 + i * 110
                l2.text(P(110, y), name, font=F(B, 32), fill=sc3((230, 230, 245), a), anchor="lm")
                l2.rectangle((*P(110, y + 25), *P(970, y + 55)), outline=sc3((90, 90, 130), a), width=max(1, int(2 * S)))
                l2.rectangle((*P(110, y + 25), *P(110 + 860 * val * kk, y + 55)), fill=sc3(col, a))
        pill("COMO FIBRA ÓPTICA... SIN CABLE", 1600, win(24.6, 27.9), (150, 200, 232), 840, 32)
    if env == 'xray':
        hp, d = info['heads'][0]
        a_ = norm(np.cross(d, (0, 1, 0)))
        b_ = np.cross(d, a_)
        at = lambda u, x=0.0, y=0.0: tuple(hp + d * u + a_ * x + b_ * y)
        a = win(29.0, 33.5)
        if a > 0:
            label("TELESCOPIO", P3(at(-0.085, 0.06, 0.06)), (1020, 500), "rm", ease(seg(t, 29.6, 30.0)) * a, (190, 240, 255))
            label("ESPEJO QUE APUNTA", P3(at(-0.105, 0.0, -0.05)), (60, 1450), "lm", ease(seg(t, 30.6, 31.0)) * a, (220, 200, 255))
            label("DETECTOR", P3(at(-0.12, -0.05, -0.07)), (1020, 1560), "rm", ease(seg(t, 31.6, 32.0)) * a, (190, 255, 210))
            label("LÁSER", P3(at(-0.13, 0.04, -0.07)), (60, 600), "lm", ease(seg(t, 30.2, 30.6)) * a, (255, 190, 210))
    if env == 'chase':
        pill("27,000 km/h", 1560, win(34.4, 38.0), CYAN, 520, 40)
        a = win(37.2, 40.9)
        if a > 0:
            p1, p2 = P3(info['tip']), P3(info['B'])
            y = max(p1[1], p2[1]) + 110
            DARK.append((min(p1[0], p2[0]) - 20, y - 70, max(p1[0], p2[0]) + 20, y + 60, a * 0.7))
            l2.line([P(p1[0], y), P(p2[0], y)], fill=sc3((220, 220, 240), a), width=max(2, int(3 * S)))
            for px in (p1[0], p2[0]):
                l2.line([P(px, y - 20), P(px, y + 20)], fill=sc3((220, 220, 240), a), width=max(2, int(3 * S)))
            l2.text(P((p1[0] + p2[0]) / 2, y - 40), "MÁS DE 5,000 km", font=F(B, 36), fill=sc3((255, 255, 255), a), anchor="mm")
            l2.text(P((p1[0] + p2[0]) / 2, y + 40), "NO A ESCALA", font=F(B, 22), fill=sc3((170, 170, 200), a * 0.8), anchor="mm")
        a = win(34.2, 37.2)
        if a > 0:
            cx, cy = 870, 560
            DARK.append((cx - 130, cy - 130, cx + 130, cy + 130, a))
            l2.ellipse((*P(cx - 100, cy - 100), *P(cx + 100, cy + 100)), outline=sc3(CYAN, a), width=max(2, int(3 * S)))
            l2.line([P(cx - 120, cy), P(cx + 120, cy)], fill=sc3(CYAN, 0.6 * a), width=1)
            l2.line([P(cx, cy - 120), P(cx, cy + 120)], fill=sc3(CYAN, 0.6 * a), width=1)
            k = 1 - ease(seg(t, 35.6, 36.8))
            dx, dy = 60 * k * math.sin(t * 7.3), 60 * k * math.cos(t * 5.1)
            rr = 10 * S
            px, py = P(cx + dx, cy + dy)
            l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(LASER, a))
            l2.text(P(cx, cy + 125), "APUNTADO" if k < 0.1 else "CORRIGIENDO", font=F(B, 24), fill=sc3(GREEN if k < 0.1 else (255, 220, 150), a), anchor="mm")
    if env == 'street':
        a = win(41.8, 46.7)
        if a > 0:
            cx, cy, r = 760, 620, 190
            DARK.append((cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10, a))
            l2.ellipse((*P(cx - r, cy - r), *P(cx + r, cy + r)), outline=sc3((230, 230, 250), a), width=max(2, int(3 * S)))
            mx = cx + 110 * math.sin(t * 1.3)
            my = cy + 30 * math.sin(t * 2.1)
            rc = 70
            l2.ellipse((*P(mx - rc, my - rc), *P(mx + rc, my + rc)), fill=sc3((96, 98, 106), a), outline=sc3((150, 152, 160), a), width=max(2, int(4 * S)))
            l2.ellipse((*P(mx - 44, my - 44), *P(mx + 44, my + 44)), fill=sc3((104, 86, 40), a))
            lag = 0.08
            dx = cx + 110 * math.sin((t - lag) * 1.3)
            dy = cy + 30 * math.sin((t - lag) * 2.1)
            rr = 12 * S
            px, py = P(dx, dy)
            l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3((255, 60, 60), a))
            l2.text(P(cx, cy + r + 40), "UNA MONEDA A 1.6 km", font=F(B, 30), fill=sc3((255, 255, 255), a), anchor="mm")
            l2.line([P(cx - r * 0.7, cy + r * 0.7), P(560, 980)], fill=sc3((170, 170, 220), a * 0.6), width=max(1, int(2 * S)))
        pill("ASÍ DE PRECISO (NASA)", 1600, win(43.8, 46.7), (255, 120, 120), 640, 34)
    if env == 'race':
        a = win(47.4, 56.3)
        if a > 0:
            for (la_, lo_), name, anc, tp in ((MEX, "MÉXICO", "rm", (1020, 1460)), (TOK, "JAPÓN", "lm", (60, 1460))):
                p = ll(la_, lo_, RE + 20)
                label(name, P3(p), tp, anc, a)
            DARK.append((80, 450, 1000, 640, a))
            l2.text(P(110, 500), "VACÍO", font=F(B, 34), fill=sc3(CYAN, a), anchor="lm")
            l2.text(P(970, 500), "≈300,000 km/s", font=F(M, 34), fill=sc3(CYAN, a), anchor="rm")
            l2.text(P(110, 590), "FIBRA", font=F(B, 34), fill=sc3(ORANGE, a), anchor="lm")
            l2.text(P(970, 590), "≈200,000 km/s", font=F(M, 34), fill=sc3(ORANGE, a), anchor="rm")
        pill("¡EL LÁSER LLEGA PRIMERO!", 1620, win(T_RACE0 + T_LASER + 0.1, 56.3), CYAN, 760, 36)
        a = win(48.0, 56.3)
        if a > 0:
            l2.text(P(1040, 1860), "TRAYECTOS SIMPLIFICADOS", font=F(B, 22), fill=sc3((160, 160, 190), a * 0.8), anchor="rm")
    if env == 'house':
        a = win(57.0, 59.6)
        if a > 0:
            q = info.get('sky_sat')
            label("LÁSER BLOQUEADO", P3(np.array([-1900.0, 2450.0, 3600.0])), (1020, 560), "rm", a, (255, 190, 210))
        a = win(58.6, 61.0)
        if a > 0:
            label("RADIO A TU ANTENA", P3(DISH_BASE + np.array([0, 70, 0])), (60, 1500), "lm", a, (190, 255, 210))
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
        os.makedirs("/home/claude/las_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/las_prev/t_{ts}.png")
            print(ts, f"{time.time() - t0:.2f}s", flush=True)
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
