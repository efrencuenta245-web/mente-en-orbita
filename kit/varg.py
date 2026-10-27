"""Mente en órbita — Stark Varg vs una 450 de gasolina (video 5). Formato de duelo por rounds.
Escenas: pista (gancho) · salto · partidor (VS) · dinamómetro · cambios en rayos X · teléfono del manubrio ·
rayos X de la eléctrica · arena de SuperEnduro · báscula (punto débil) · cierre."""
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
import moto_model as mm

FPS = 24
DUR = 48.0
NF = int(DUR * FPS)
ECOL = (60, 200, 255)
GCOL = (255, 130, 50)
RED = (255, 80, 80)
GREEN = (90, 255, 150)

PHR = [
    (0.3, 2.2, "Esta moto casi no hace ruido,", {4}),
    (2.4, 4.8, "no tiene palanca de cambios ni clutch...", {6}),
    (5.0, 8.8, "y es capaz de humillar a las mejores motos de gasolina del planeta.", {4}),
    (9.3, 12.6, "Stark Varg contra una 450 de gasolina. Que empiece la pelea.", {9}),
    (13.1, 17.6, "Round uno, potencia: una 450 ronda los sesenta caballos. La Varg, hasta ochenta.", {12}),
    (18.1, 22.6, "Round dos, cambios: cinco velocidades y clutch contra... una sola. Aceleras y ya.", {9}),
    (23.1, 28.4, "Round tres: desde el teléfono del manubrio le cambias la potencia de diez a ochenta caballos.", {4}),
    (28.9, 34.3, "Por dentro: una batería de 7.2 kilowatts hora y un motor eléctrico. Sin pistones ni filtros.", {4}),
    (34.8, 39.9, "Y en 2026 ganó el mundial de constructores de SuperEnduro, por encima de Husqvarna y Triumph.", {4}),
    (40.4, 44.2, "¿Su punto débil? Pesa 118 kilos, más que muchas de gasolina.", {2}),
    (44.8, 46.8, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)

CUTS = (4.9, 9.0, 12.8, 17.9, 22.9, 28.7, 34.6, 40.2)
ENVS = ('track1', 'jump', 'gate', 'dyno', 'gears', 'phone', 'xray', 'arena', 'scale')
T_OUT = 44.4
SCORE = [(13.1, 0, 0), (17.3, 1, 0), (22.5, 2, 0), (28.2, 3, 0), (43.1, 3, 1)]


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


# =====================================================================
# Fondo de cielo por gradiente según la línea del horizonte
# =====================================================================
def sky(c, top, mid, hor, sun_dir=None, sun_col=(255, 200, 140)):
    hy = (c['cy'] - 1200.0 * math.tan(math.asin(max(-0.99, min(0.99, c['sp'])))) ) * S
    ys = np.arange(H, dtype=np.float32)[:, None]
    u = np.clip((hy - ys) / (H * 0.55), 0, 1)
    top, mid, hor = (np.array(v, np.float32) for v in (top, mid, hor))
    a = np.clip(u * 2, 0, 1)
    b = np.clip(u * 2 - 1, 0, 1)
    col = hor * (1 - a[..., None]) + mid * a[..., None]
    col = col * (1 - b[..., None]) + top * b[..., None]
    arr = np.repeat(col, W, axis=1)
    if sun_dir is not None:
        d = norm(sun_dir)
        far = np.asarray(c['pos']) + d * 1e7
        sx, sy, dep = proj(*far, c)
        if dep > 0:
            yy, xx = np.mgrid[0:H, 0:W]
            r = np.hypot(xx - sx * S, yy - sy * S) / (W * 0.5)
            g = np.exp(-r * r * 6)[..., None] * np.array(sun_col, np.float32) * 0.9
            g += (r < 0.05)[..., None] * np.array([255, 240, 220], np.float32) * 0.8
            arr = arr + g
    return arr


# =====================================================================
# Pista de motocross (cm)
# =====================================================================
SUN = norm((-0.45, 0.55, 0.7))
DIRT = (138, 100, 68)
_rt = np.random.RandomState(5)
TREES = [(x, 9000 + _rt.uniform(0, 3000), _rt.uniform(600, 1200)) for x in np.arange(-30000, 30000, 900.0)]
TREES += [(x, -9000 - _rt.uniform(0, 3000), _rt.uniform(600, 1200)) for x in np.arange(-30000, 30000, 1100.0)]
BANNER_COLS = [VIOLET, BLUE, (240, 240, 245), CYAN, ORANGE, (240, 240, 245)]
CROWD = []
for row in range(6):
    for k in range(260):
        CROWD.append((-6000 + k * 46 + _rt.uniform(-8, 8), 140 + row * 70 + 40, 2300 + row * 90, _rt.randint(0, 5)))
CROWD = np.array(CROWD)
CROWD_COLS = [(230, 80, 80), (80, 170, 255), (250, 220, 90), (240, 240, 240), (120, 230, 140)]


def ground_y(x):
    if x < 2400 or x > 4400:
        return 0.0
    if x < 3000:
        return 160.0 * (x - 2400) / 600
    if x < 3700:
        return 160.0
    return 160.0 * (4400 - x) / 700


def draw_track(bd, la, buf, c, t, gate=False, dim=1.0):
    L = SUN
    # colinas lejanas
    for k in range(9):
        x0 = -400000 + k * 100000
        poly(bd, c, [(x0, -100, 600000), (x0 + 120000, -100, 600000), (x0 + 70000, 26000 + 9000 * math.sin(k * 1.7), 600000)],
             (86, 70, 104), dim)
    poly(bd, c, [(-900000, -10, -900000), (900000, -10, -900000), (900000, -10, 900000), (-900000, -10, 900000)], (84, 118, 62), dim)
    # pista
    poly(bd, c, [(-40000, 0, -700), (40000, 0, -700), (40000, 0, 700), (-40000, 0, 700)], DIRT, dim)
    for zz in (-420, -150, 160, 430):
        line3(bd, c, (-40000, 0.5, zz), (40000, 0.5, zz), sc3(DIRT, 0.82 * dim), max(1, int(3 * S)), 20.0)
    sol = []
    # salto (mesa)
    prof = [(2400, 0), (3000, 160), (3700, 160), (4400, 0)]
    for i in range(3):
        (xa, ya), (xb, yb) = prof[i], prof[i + 1]
        n = norm((-(yb - ya), (xb - xa), 0))
        f = face(c, [(xa, ya, -700), (xb, yb, -700), (xb, yb, 700), (xa, ya, 700)], n, (150, 110, 76), dim, L, 0.5, near=20.0)
        if f:
            sol.append(f)
    for zz, nz in ((-700, -1), (700, 1)):
        f = face(c, [(2400, 0, zz), (3000, 160, zz), (3700, 160, zz), (4400, 0, zz)], (0, 0, nz), (120, 86, 58), dim, L, 0.5, near=20.0)
        if f:
            sol.append(f)
    # barreras, vallas y lonas
    for side in (-1, 1):
        zb = side * 760
        for k in range(-40, 60):
            x0 = k * 300
            col = (230, 232, 238) if k % 2 else (60, 120, 220)
            sol += cbox(c, x0, x0 + 290, 0, 70, zb - 40, zb + 40, col, dim, L, 0.5, near=20.0)
        zf = side * 1100
        for k in range(-30, 45):
            x0 = k * 400
            col = BANNER_COLS[(k + (3 if side > 0 else 0)) % len(BANNER_COLS)]
            f = face(c, [(x0, 40, zf), (x0 + 390, 40, zf), (x0 + 390, 190, zf), (x0, 190, zf)], (0, 0, -side), col, dim * 0.95, L, 0.6, near=20.0)
            if f:
                sol.append(f)
    # tribuna
    sol += cbox(c, -6200, 6000, 0, 140, 2200, 2900, (92, 94, 104), dim, L, 0.5, near=20.0)
    for row in range(6):
        sol += cbox(c, -6200, 6000, 140 + row * 70, 140 + row * 70 + 70, 2240 + row * 90, 2900, (108, 110, 120), dim, L, 0.5, near=20.0)
    sol += cbox(c, -6200, 6000, 640, 660, 2200, 3000, (60, 62, 72), dim, L, 0.5, near=20.0)
    # árboles
    for (x, z, h) in TREES:
        sx, sy, dep = proj(x, h / 2, z, c)
        if dep < 100 or sx < -600 or sx > 1700:
            continue
        sol += cbox(c, x - 260, x + 260, 0, h, z - 260, z + 260, (50, 88, 56), dim, L, 0.55, near=20.0)
    if gate:
        for k in range(-6, 7):
            z0 = k * 120
            sol += cbox(c, -110, -100, 0, 70, z0 - 55, z0 + 55, (150, 154, 162), dim, L, 0.5)
            sol += cbox(c, -140, -100, 0, 6, z0 - 58, z0 + 58, (90, 92, 98), dim, L, 0.5)
        poly(bd, c, [(-300, 0.6, -800), (60, 0.6, -800), (60, 0.6, 800), (-300, 0.6, 800)], (150, 146, 140), dim)
    fo.draw_solids(bd, sol)
    # público
    cc = CROWD
    for ci, col in enumerate(CROWD_COLS):
        m = cc[:, 3] == ci
        splat(buf, c, cc[m, 0], cc[m, 1], cc[m, 2], col, 0.55, near=50.0, size=2)


def shadow(od, c, pos, yaw, a=110, rx=120, rz=34):
    gy = ground_y(pos[0]) + 1.0
    pts = [(pos[0] + rx * math.cos(q) * math.cos(yaw) - rz * math.sin(q) * math.sin(yaw), gy,
            pos[2] + rx * math.cos(q) * math.sin(yaw) + rz * math.sin(q) * math.cos(yaw)) for q in np.linspace(0, 2 * math.pi, 20, endpoint=False)]
    q = clip_near(pts, c, 20.0)
    if len(q) > 2:
        h = max(0.0, pos[1] - gy)
        od.polygon([P2(*p, c) for p in q], fill=(20, 14, 10, int(a * clamp(1 - h / 500))))


def draw_bikes(bd, od, c, bikes, L=SUN, dim=1.0, xr=0.0):
    """bikes: lista de dict(kind, pos, yaw, pitch, rider, wheel)"""
    allf = []
    for bk in bikes:
        allf += mm.faces(c, bk['kind'], bk['pos'], bk.get('yaw', 0.0), bk.get('pitch', 0.0), L, dim, bk.get('rider', True),
                         bk.get('xr', xr), 20.0, bk.get('hide', ()), bk.get('wheel', 0.0))
    allf.sort(key=lambda q: -q[0])
    for dep, pts, col, al, tag in allf:
        if al is None:
            bd.polygon(pts, fill=col)
        else:
            od.polygon(pts, fill=(*col, al))


# =====================================================================
# Garaje (cm)
# =====================================================================
GL = norm((-0.25, 0.9, -0.35))
SCALE_X = (-175.0, 175.0)


def draw_garage(bd, la, c, t, dim=1.0, dyno=False, scales=False):
    L = GL
    poly(bd, c, [(-3000, 0, -1500), (3000, 0, -1500), (3000, 0, 700), (-3000, 0, 700)], (74, 76, 86), dim)
    for k in range(-15, 16):
        line3(bd, c, (k * 200, 0.3, -1500), (k * 200, 0.3, 700), sc3((64, 66, 76), dim), max(1, int(2 * S)), 20.0)
    poly(bd, c, [(-3000, 0, 700), (3000, 0, 700), (3000, 700, 700), (-3000, 700, 700)], (44, 46, 58), dim)
    poly(bd, c, [(-3000, 700, 700), (3000, 700, 700), (3000, 700, -1500), (-3000, 700, -1500)], (30, 32, 40), dim)
    # tablero de herramientas y franja de color
    poly(bd, c, [(-900, 160, 699), (900, 160, 699), (900, 420, 699), (-900, 420, 699)], (58, 62, 76), dim)
    poly(bd, c, [(-3000, 80, 698), (3000, 80, 698), (3000, 100, 698), (-3000, 100, 698)], (60, 140, 220), dim)
    sol = []
    sol += cbox(c, -1400, -1000, 0, 95, 520, 690, (70, 74, 84), dim, L)
    sol += cbox(c, -1420, -980, 95, 105, 500, 695, (110, 80, 54), dim, L)
    sol += cbox(c, 1000, 1200, 0, 140, 540, 690, (200, 60, 50), dim, L)
    for k in range(4):
        sol += [f for f in nc.cyl_polys(c, 1, (-1700, 18 + k * 30, 500), 42, 26, (26, 26, 28), 20, dim)]
    if dyno:
        for zz in (-130, 130):
            sol += cbox(c, -140, -10, -1, 4, zz - 40, zz + 40, (40, 42, 48), dim, L)
    if scales:
        for xx in SCALE_X:
            sol += cbox(c, xx - 115, xx + 115, 0, 8, -45, 45, (120, 124, 132), dim, L)
            sol += cbox(c, xx - 4, xx + 4, 0, 60, -86, -78, (60, 62, 70), dim, L)
            sol += cbox(c, xx - 26, xx + 26, 60, 96, -92, -76, (34, 36, 42), dim, L)
    fo.draw_solids(bd, sol)
    # barras de luz en la pared del fondo
    for k in range(-3, 4):
        x0 = k * 600
        line3(la, c, (x0 - 220, 470, 696), (x0 + 220, 470, 696), sc3((220, 230, 255), 0.7), max(2, int(5 * S)), 20.0)
    for (x, y) in ((-700, 300), (-300, 240), (200, 330), (600, 260)):
        line3(la, c, (x, y, 698), (x + 120, y, 698), sc3((140, 150, 180), 0.25), max(1, int(3 * S)), 20.0)


# =====================================================================
# Arena de SuperEnduro (cm)
# =====================================================================
LOGS = [(-400, 30), (-250, 30), (-325, 80), (900, 30), (1050, 30)]
ROCKS = [(300 + k * 60, (k * 37) % 50 + 20) for k in range(8)]


def arena_y(x):
    if -520 < x < -130:
        return 110.0 * math.sin(math.pi * (x + 520) / 390)
    return 0.0


def draw_arena(bd, la, buf, c, t, dim=1.0):
    L = norm((0.2, 0.9, -0.3))
    poly(bd, c, [(-20000, 0, -20000), (20000, 0, -20000), (20000, 0, 20000), (-20000, 0, 20000)], (64, 48, 38), dim)
    sol = []
    for row in range(10):
        sol += cbox(c, -9000, 9000, row * 90, row * 90 + 90, 2600 + row * 110, 5000, (40, 42, 54), dim, L, 0.6)
    for zz in (-3800,):
        for row in range(6):
            sol += cbox(c, -9000, 9000, row * 90, row * 90 + 90, -5000, zz - row * 110, (40, 42, 54), dim, L, 0.6)
    sol += cbox(c, -9000, 9000, 0, 90, 900, 1000, (230, 230, 236), dim, L, 0.5)
    for (x, r) in LOGS:
        sol += [f for f in nc.cyl_polys(c, 2, (x, r, 0), r if r < 60 else 30, 700, (112, 78, 50), 14, dim)]
    for (x, h) in ROCKS:
        sol += cbox(c, x - 28, x + 28, 0, h, -300, 300, (120, 118, 116), dim, L, 0.5)
    for k in range(6):
        sol += [f for f in nc.cyl_polys(c, 1, (1500 + k * 70, 20, -150 + (k % 2) * 300), 34, 40, (26, 26, 28), 16, dim)]
    fo.draw_solids(bd, sol)
    rs = np.random.RandomState(9)
    X = rs.uniform(-9000, 9000, 4000)
    row = rs.randint(0, 10, 4000)
    Y = row * 90 + 130.0
    Z = 2620 + row * 110.0
    flick = 0.5 + 0.5 * np.sin(t * 6 + X * 0.01)
    splat(buf, c, X, Y, Z, (200, 200, 230), 0.35 + 0.3 * flick, near=50.0, size=2)
    # focos
    for k in range(-4, 5):
        p = (k * 1800, 2600, 2400)
        sx, sy, dep = proj(*p, c)
        if dep > 100 and sy > 560:
            glow_dot(la, sx * S, sy * S, max(3, 160000 / dep) * S, (255, 250, 230), 0.9)


# =====================================================================
# Movimiento de las motos
# =====================================================================
def jump_state(x, base_y=0.0):
    """altura y cabeceo sobre la mesa"""
    if x < 3000:
        y = ground_y(x)
        pitch = math.atan2(160, 600) * 0.9 if x > 2400 else 0.0
        return y, pitch
    if x > 4200:
        return ground_y(x), -math.atan2(160, 700) * 0.6 if x < 4400 else 0.0
    u = (x - 3000) / 1200.0
    y = lerp(160, ground_y(4200), u) + 4 * 230 * u * (1 - u)
    dy = (ground_y(4200) - 160) / 1200 + 4 * 230 * (1 - 2 * u) / 1200
    return y, math.atan(dy) * 0.8


def tau_jump(t):
    a = t - 4.9
    if a < 1.1:
        return a
    if a < 3.1:
        return 1.1 + 0.35 * (a - 1.1)
    return 1.8 + (a - 3.1)


def bikes_jump(t):
    tau = tau_jump(t)
    out = []
    for kind, x0, v, z in (('gas', 1500, 1250, 300), ('elec', 1100, 1500, -170)):
        x = x0 + v * tau
        y, pitch = jump_state(x)
        out.append(dict(kind=kind, pos=(x, y, z), yaw=0.0, pitch=pitch, rider=True, wheel=-x / 35.0))
    return out


def x_track1(t):
    return -1200 + 700 * t


def arena_bike(t):
    x = -1100 + 520 * (t - 34.6)
    y = arena_y(x)
    if -520 < x < -130:
        pitch = math.atan(110 * math.pi / 390 * math.cos(math.pi * (x + 520) / 390)) * 0.6
    else:
        pitch = 0.0
    return dict(kind='elec', pos=(x, y, 0), yaw=0.0, pitch=pitch, rider=True, wheel=-x / 35.0)


# =====================================================================
# Cámaras
# =====================================================================
def cam_for(env, t):
    if env == 'track1':
        x = x_track1(t)
        keys = [(0.0, 430, 5, 140, 1080, 60, 90, 0), (2.2, 400, 6, 150, 1080, 60, 90, 0), (3.0, 240, 12, 168, 1040, 10, 85, 20), (4.9, 220, 14, 172, 1040, 5, 80, 20)]
        c = cam_keys(t, keys)
        f = (c['f'][0] + x, c['f'][1], c['f'][2])
        return cam_from(c['D'], math.degrees(math.asin(c['sp'])), math.degrees(math.atan2(c['sa'], c['ca'])), c['cy'], f)
    if env == 'jump':
        bs = bikes_jump(t)
        fx = (bs[0]['pos'][0] + bs[1]['pos'][0]) / 2 + 80
        keys = [(4.9, 1000, 13, -14, 1150, 0, 200, 0), (9.0, 900, 12, 8, 1150, 0, 220, 0)]
        c = cam_keys(t, keys)
        return cam_from(c['D'], math.degrees(math.asin(c['sp'])), math.degrees(math.atan2(c['sa'], c['ca'])), c['cy'], (fx, 230, 0))
    keys = {
        'gate': [(9.0, 620, 7, 82, 1060, 0, 100, 0), (12.8, 470, 8, 96, 1060, 0, 100, 0)],
        'dyno': [(12.8, 520, 12, 64, 1060, -30, 75, 0), (17.9, 450, 11, 76, 1060, -30, 75, 0)],
        'gears': [(17.9, 210, 8, 188, 960, 10, 70, 0), (20.6, 200, 8, 182, 960, 10, 70, 0), (21.15, 200, 8, 180, 960, -330, 66, 0),
                  (22.9, 190, 9, 174, 960, -330, 66, 0)],
        'phone': [(22.9, 40, 26, -90, 1010, *(mm.HB + (-2, 9, 0))), (27.4, 48, 24, -84, 1010, *(mm.HB + (-2, 9, 0))),
                  (28.7, 420, 10, -40, 1020, 0, 80, 0)],
        'xray': [(28.7, 300, 4, -4, 1000, -5, 75, 0), (34.6, 270, 5, 6, 1000, -5, 75, 0)],
        'arena': [(34.6, 620, 5, -16, 1100, -700, 140, 0), (40.2, 700, 6, 14, 1100, 400, 130, 0)],
        'scale': [(40.2, 760, 9, -8, 1000, 0, 75, 0), (48.0, 700, 10, 4, 1000, 0, 75, 0)],
    }[env]
    c = cam_keys(t, keys)
    if env == 'arena':
        b = arena_bike(t)
        fx = b['pos'][0] + 120
        c = cam_from(c['D'], math.degrees(math.asin(c['sp'])), math.degrees(math.atan2(c['sa'], c['ca'])), c['cy'], (fx, 130, 0))
    return c


# =====================================================================
# Render
# =====================================================================
BITS = [1, 1, 0, 1, 0, 1, 1, 0]


def render(t):
    env = env_at(t)
    c = cam_for(env, t)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    buf = np.zeros((H, W, 3), np.float32)
    info = {}

    if env in ('track1', 'jump', 'gate', 'phone'):
        arr = sky(c, (40, 46, 96), (190, 110, 120), (255, 176, 110), SUN, (255, 190, 120))
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        draw_track(bd, la, buf, c, t, gate=(env == 'gate'))
    elif env in ('dyno', 'gears', 'xray', 'scale'):
        base = Image.new("RGB", (W, H), (30, 32, 40))
        bd = ImageDraw.Draw(base)
        draw_garage(bd, la, c, t, 0.55 if env == 'xray' else 1.0, dyno=(env == 'dyno'), scales=(env == 'scale'))
    else:
        base = Image.new("RGB", (W, H), (10, 10, 18))
        bd = ImageDraw.Draw(base)
        draw_arena(bd, la, buf, c, t)

    # ---------- motos ----------
    if env == 'track1':
        x = x_track1(t)
        b = dict(kind='elec', pos=(x, 0, 0), yaw=0.0, rider=True, wheel=-x / 35.0)
        shadow(od, c, b['pos'], 0.0)
        draw_bikes(bd, od, c, [b])
        info['bike'] = b
        # polvo
        for k in range(14):
            age = ((t * 2.2 + k / 14.0) % 1.0)
            px = x - 80 - age * 260
            py = 10 + age * 60
            pz = (k % 3 - 1) * 20 + age * 40 * math.sin(k)
            sx, sy, dep = proj(px, py, pz, c)
            if dep > 30:
                rr = (8 + age * 50) * 1200 / dep * S
                od.ellipse((sx * S - rr, sy * S - rr, sx * S + rr, sy * S + rr), fill=(190, 150, 110, int(90 * (1 - age))))
    elif env == 'jump':
        bs = bikes_jump(t)
        for b in bs:
            shadow(od, c, b['pos'], 0.0)
        draw_bikes(bd, od, c, bs)
        info['bikes'] = bs
        for b in bs:
            for k in range(10):
                age = ((t * 2.0 + k / 10.0) % 1.0)
                px = b['pos'][0] - 100 - age * 400
                py = ground_y(px) + 10 + age * 80
                sx, sy, dep = proj(px, py, b['pos'][2], c)
                if dep > 30 and b['pos'][1] - ground_y(b['pos'][0]) < 30:
                    rr = (10 + age * 70) * 1200 / dep * S
                    od.ellipse((sx * S - rr, sy * S - rr, sx * S + rr, sy * S + rr), fill=(190, 150, 110, int(80 * (1 - age))))
        # estela de la eléctrica
        e = bs[1]
        pts = [mm.world(e['pos'], 0.0, e['pitch'], (-110 - 40 * k, 90, 0)) for k in range(8)]
        polyline3(la, c, pts, sc3(ECOL, 0.35), max(2, int(6 * S)), 20.0)
    elif env == 'gate':
        bs = [dict(kind='elec', pos=(0, 0, -130), rider=True), dict(kind='gas', pos=(0, 0, 130), rider=True)]
        for b in bs:
            shadow(od, c, b['pos'], 0.0)
        draw_bikes(bd, od, c, bs)
        info['bikes'] = bs
    elif env == 'dyno':
        sp = ease(seg(t, 13.6, 15.0))
        bs = [dict(kind='elec', pos=(0, 6, -130), rider=False, wheel=-t * 25 * sp),
              dict(kind='gas', pos=(0, 6, 130), rider=False, wheel=-t * 20 * sp)]
        draw_bikes(bd, od, c, bs, GL)
        info['bikes'] = bs
        for zz, col, kk in ((-130, ECOL, 1.0), (130, GCOL, 0.75)):
            a = ease(seg(t, 14.4, 15.4)) * kk
            for q in range(6):
                ang = -t * 9 + q * math.pi / 3
                p0 = (-74 + 34 * math.cos(ang), 40 + 34 * math.sin(ang), zz - 7)
                p1 = (-74 + 34 * math.cos(ang + 0.4), 40 + 34 * math.sin(ang + 0.4), zz - 7)
                line3(la, c, p0, p1, sc3(col, 0.6 * a), max(2, int(4 * S)), 20.0)
    elif env == 'gears':
        xg = ease(seg(t, 18.2, 18.9)) * (1 - ease(seg(t, 22.6, 22.9)))
        bs = [dict(kind='gas', pos=(0, 0, 0), rider=False, xr=xg * (1 - ease(seg(t, 20.8, 21.2)))),
              dict(kind='elec', pos=(-330, 0, 0), rider=False, xr=xg * ease(seg(t, 20.8, 21.2)))]
        draw_bikes(bd, od, c, bs, GL)
        info['bikes'] = bs
        ga = xg * (1 - ease(seg(t, 20.8, 21.2)))
        if ga > 0.01:
            for i, (r1, r2) in enumerate(((7.5, 3.4), (6.6, 4.3), (5.8, 5.1), (5.1, 5.8), (4.4, 6.5))):
                zz = -7 + i * 3.5
                spin = t * (3 + i)
                for (cx_, cy_, r, s) in ((2, 46, r1, 1), (2 + r1 + r2 + 0.6, 46 - 2, r2, -1)):
                    pts = [(cx_ + r * math.cos(q + s * spin), cy_ + r * math.sin(q + s * spin), zz) for q in np.linspace(0, 2 * math.pi, 31)]
                    polyline3(la, c, pts, sc3(lc(GCOL, (255, 220, 120), i / 4), ga), max(2, int(3 * S)), 10.0)
                    for k in range(10):
                        q = s * spin + k * 2 * math.pi / 10
                        line3(la, c, (cx_ + r * math.cos(q), cy_ + r * math.sin(q), zz), (cx_ + (r + 1.2) * math.cos(q), cy_ + (r + 1.2) * math.sin(q), zz),
                              sc3(GCOL, ga), max(1, int(3 * S)), 10.0)
            pts = [(6 + 10 * math.cos(q), 46 + 10 * math.sin(q), -13) for q in np.linspace(0, 2 * math.pi, 31)]
            polyline3(la, c, pts, sc3(BLUE, ga * 0.9), max(2, int(4 * S)), 10.0)
            for tag_p in ((mm.HB + (14, -4, 38)), (mm.SP + (22, 2, 16))):
                glow_dot(la, P2(*tag_p, c)[0], P2(*tag_p, c)[1], 10 * S, RED, ga * (0.6 + 0.4 * math.sin(t * 8)))
        ea = xg * ease(seg(t, 20.8, 21.2))
        if ea > 0.01:
            ox = -330
            for (cx_, cy_, r, s) in ((ox - 2, 40, 5, 1), (ox - 2 + 5 + 11 + 0.6, 40, 11, -1)):
                spin = t * 4 * (2.2 if r < 6 else 1)
                pts = [(cx_ + r * math.cos(q + s * spin), cy_ + r * math.sin(q + s * spin), 12) for q in np.linspace(0, 2 * math.pi, 31)]
                polyline3(la, c, pts, sc3(ECOL, ea), max(2, int(4 * S)), 10.0)
                for k in range(12):
                    q = s * spin + k * 2 * math.pi / 12
                    line3(la, c, (cx_ + r * math.cos(q), cy_ + r * math.sin(q), 12), (cx_ + (r + 1.4) * math.cos(q), cy_ + (r + 1.4) * math.sin(q), 12),
                          sc3(ECOL, ea), max(1, int(3 * S)), 10.0)
    elif env == 'phone':
        sp = ease(seg(t, 26.6, 28.2))
        b = dict(kind='elec', pos=(0, 0, 0), rider=False, wheel=-t * 30 * sp)
        shadow(od, c, b['pos'], 0.0)
        draw_bikes(bd, od, c, [b])
        info['bike'] = b
        draw_phone_ui(bd, la, c, t)
    elif env == 'xray':
        xo = ease(seg(t, 29.2, 30.0))
        b = dict(kind='elec', pos=(0, 0, 0), rider=False, xr=xo, wheel=-t * 4)
        draw_bikes(bd, od, c, [b], GL)
        info['bike'] = b
        xray_fx(la, c, t, xo)
    elif env == 'arena':
        b = arena_bike(t)
        draw_bikes(bd, od, c, [b], norm((0.2, 0.9, -0.3)))
        info['bike'] = b
    elif env == 'scale':
        bs = [dict(kind='elec', pos=(SCALE_X[0], 8, 0), rider=False), dict(kind='gas', pos=(SCALE_X[1], 8, 0), rider=False)]
        draw_bikes(bd, od, c, bs, GL)
        info['bikes'] = bs
        for xx, col in ((SCALE_X[0], RED), (SCALE_X[1], (120, 200, 255))):
            q = [P2(xx - 22, 64, -92.5, c), P2(xx + 22, 64, -92.5, c), P2(xx + 22, 92, -92.5, c), P2(xx - 22, 92, -92.5, c)]
            la.polygon(q, fill=sc3(col, 0.45 + 0.15 * math.sin(t * 6)))

    # ---------- composición ----------
    arr = np.asarray(base, np.float32)
    imgA = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")
    LAa = np.asarray(LA, np.float32) + buf
    gl = glow_of(Image.fromarray(np.clip(LAa, 0, 255).astype(np.uint8)), 4)
    out = np.asarray(imgB, np.float32) + LAa + 1.5 * gl
    # degradado oscuro arriba (legibilidad de subtítulos)
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    out = out * (0.42 + 0.58 * np.clip(yy / (H * 0.30), 0, 1))
    f = 1.0
    for ct in CUTS:
        f = min(f, clamp(abs(t - ct) / 0.22))
    out = out * f
    # destello en cada cambio de marcador
    for (ts, _, _) in SCORE[1:]:
        if 0 <= t - ts < 0.35:
            out = out + 60 * (1 - (t - ts) / 0.35)
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


# ---------- teléfono del manubrio ----------
PH_C = mm.HB + np.array([-3.2, 9.0, 0.0])


def scr(u, v, off=0.0):
    return (PH_C[0] - off, PH_C[1] + v * 5.8, PH_C[2] - u * 4.6)


def draw_phone_ui(bd, la, c, t):
    k = ease(seg(t, 27.0, 27.95))
    hp = 10 + 70 * k
    q = [P2(*scr(-1, -1), c), P2(*scr(1, -1), c), P2(*scr(1, 1), c), P2(*scr(-1, 1), c)]
    bd.polygon(q, fill=(10, 14, 24))
    # arco de potencia
    a0, a1 = math.radians(210), math.radians(-30)
    pts = [P2(*scr(0.78 * math.cos(lerp(a0, a1, i / 40)), 0.15 + 0.62 * math.sin(lerp(a0, a1, i / 40)) * 0.8, 0.05), c) for i in range(41)]
    la.line(pts, fill=(30, 40, 60), width=max(3, int(16 * S)))
    n = int(40 * (hp - 10) / 70) + 1
    la.line(pts[:max(2, n)], fill=sc3(lc(ECOL, (255, 255, 255), k * 0.3), 1.0), width=max(3, int(16 * S)))
    # curva de potencia
    cur = [P2(*scr(-0.8 + 1.6 * i / 30, -0.75 + 0.45 * (1 - math.exp(-3 * i / 30)) * (hp / 80), 0.05), c) for i in range(31)]
    la.line(cur, fill=sc3(VIOLET, 0.9), width=max(2, int(6 * S)))
    # botones de modo
    for i in range(4):
        u0 = -0.8 + i * 0.42
        on = i == min(3, int(k * 4))
        bq = [P2(*scr(u0, -0.95, 0.05), c), P2(*scr(u0 + 0.34, -0.95, 0.05), c), P2(*scr(u0 + 0.34, -0.85, 0.05), c), P2(*scr(u0, -0.85, 0.05), c)]
        la.polygon(bq, fill=sc3(ECOL, 0.8 if on else 0.15))


def xray_fx(la, c, t, xo):
    if xo <= 0.01:
        return
    # celdas de la batería
    for i in range(9):
        x = -20 + i * 6.4
        line3(la, c, (x, 48, 12.5), (x, 90, 12.5), sc3(CYAN, 0.45 * xo), max(1, int(2 * S)), 10.0)
    for j in range(7):
        y = 50 + j * 6.5
        line3(la, c, (-20, y, 12.5), (34, y, 12.5), sc3(CYAN, 0.45 * xo), max(1, int(2 * S)), 10.0)
    pul = 0.6 + 0.4 * math.sin(t * 5)
    corners = [(-22, 46, 12.6), (36, 46, 12.6), (36, 92, 12.6), (-22, 92, 12.6), (-22, 46, 12.6)]
    polyline3(la, c, corners, sc3(ECOL, xo * pul), max(2, int(4 * S)), 10.0)
    # bobinas del motor
    for r in (12, 8.5, 5):
        pts = [(-2 + r * math.cos(q), 40 + r * math.sin(q), 11.5) for q in np.linspace(0, 2 * math.pi, 33)]
        polyline3(la, c, pts, sc3(VIOLET, xo), max(2, int(3 * S)), 10.0)
    for k in range(6):
        q = t * 6 + k * math.pi / 3
        line3(la, c, (-2, 40, 11.5), (-2 + 11 * math.cos(q), 40 + 11 * math.sin(q), 11.5), sc3(VIOLET, 0.7 * xo), max(1, int(2 * S)), 10.0)
    # controlador
    glow_dot(la, *P2(23, 88, 10, c), 9 * S, ORANGE, xo * 0.8)
    # cables de alto voltaje y flujo de energía
    path1 = [(30, 88, 10), (30, 70, 10), (14, 52, 10), (4, 44, 10)]
    pr, ss = resample(fo.crom(path1, 8), 2.0)
    line_ = [P2(*p, c) for p in pr]
    la.line(line_, fill=sc3(ORANGE, 0.6 * xo), width=max(2, int(4 * S)))
    pulses(la, c, pr, ss, t, 60, BITS, xo, (255, 255, 255), 6.0, max(2, int(4 * S)))
    # cadena
    chain = [(-2 + 5 * math.cos(q), 40 + 5 * math.sin(q), 13) for q in np.linspace(-1.4, 1.4, 8)]
    chain += [(-74 + 12 * math.cos(q), 34 + 12 * math.sin(q), 13) for q in np.linspace(1.6, 4.7, 10)]
    chain.append(chain[0])
    prc, ssc = resample(chain, 2.0)
    pulses(la, c, prc, ssc, t, 80, [1, 0], xo * 0.8, ECOL, 4.0, max(1, int(3 * S)))
    # escáner
    xs = -110 + ((t * 0.35) % 1.0) * 230
    sq = [(xs, 0, 30), (xs, 140, 30), (xs, 140, -30), (xs, 0, -30), (xs, 0, 30)]
    polyline3(la, c, sq, sc3(BLUE, 0.8 * xo), max(2, int(3 * S)), 10.0)


# =====================================================================
# HUD
# =====================================================================
DARK = []


def score_at(t):
    e, g = 0, 0
    for (ts, a, b) in SCORE:
        if t >= ts:
            e, g = a, b
    return e, g


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

    def xmark(x, y, a, r=18):
        if a <= 0:
            return
        rr = r * S
        px, py = P(x, y)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), outline=sc3(RED, a), width=max(2, int(4 * S)))
        l2.line([(px - rr * 0.6, py - rr * 0.6), (px + rr * 0.6, py + rr * 0.6)], fill=sc3(RED, a), width=max(2, int(4 * S)))

    def pill(txt, y, a, col=BLUE, w=560, size=36):
        if a <= 0:
            return
        DARK.append((540 - w / 2, y - 42, 540 + w / 2, y + 42, a))
        l2.rounded_rectangle((*P(540 - w / 2, y - 42), *P(540 + w / 2, y + 42)), radius=int(42 * S), outline=sc3(col, a), width=max(2, int(3 * S)))
        l2.text(P(540, y), txt, font=F(B, size), fill=sc3((235, 240, 255), a), anchor="mm")

    def win(a, b, e=0.4):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def round_card(num, name, t0, t1, col):
        a = win(t0, t1, 0.25)
        if a <= 0:
            return
        k = ease(seg(t, t0, t0 + 0.3))
        size = int(lerp(150, 104, k))
        DARK.append((150, 470, 930, 700, a))
        l2.text(P(540, 545), f"ROUND {num}", font=F(B, size), fill=sc3((255, 255, 255), a), anchor="mm")
        l2.text(P(540, 645), name, font=F(B, 44), fill=sc3(col, a), anchor="mm")

    def P3(p):
        sx, sy, _ = proj(*p, c)
        return (sx, sy)

    # marcador
    ma = ease(seg(t, 9.6, 10.2)) * (1 - ease(seg(t, T_OUT + 0.4, T_OUT + 1.0)))
    if ma > 0:
        e, g = score_at(t)
        DARK.append((70, 1740, 1010, 1850, ma))
        l2.rounded_rectangle((*P(70, 1740), *P(1010, 1850)), radius=int(30 * S), outline=sc3((150, 150, 200), ma * 0.8), width=max(1, int(2 * S)))
        l2.text(P(110, 1795), "ELÉCTRICA", font=F(B, 38), fill=sc3(ECOL, ma), anchor="lm")
        l2.text(P(970, 1795), "GASOLINA", font=F(B, 38), fill=sc3(GCOL, ma), anchor="rm")
        l2.text(P(540, 1795), f"{e}  –  {g}", font=F(M, 64), fill=sc3((255, 255, 255), ma), anchor="mm")

    for ct in CUTS:
        if abs(t - ct) < 0.25:
            return
    if env == 'track1':
        a = win(0.5, 2.4)
        if a > 0:
            DARK.append((180, 1480, 900, 1640, a))
            l2.text(P(540, 1515), "RUIDO DEL MOTOR", font=F(B, 30), fill=sc3((200, 200, 230), a), anchor="mm")
            for i in range(24):
                h = 6 + 8 * abs(math.sin(t * 9 + i * 0.7)) * 0.4
                x = 240 + i * 25
                l2.rectangle((*P(x, 1595 - h), *P(x + 14, 1595 + h)), fill=sc3(GREEN if i < 3 else (70, 80, 100), a))
        b = info.get('bike')
        if b:
            a = win(2.9, 4.85)
            lever = mm.world(b['pos'], 0.0, 0.0, mm.HB + (8, -2, 34))
            shifter = mm.world(b['pos'], 0.0, 0.0, mm.SP + (12, 0, 18))
            if a > 0:
                q1, q2 = P3(lever), P3(shifter)
                ac = ease(seg(t, 4.0, 4.3)) * a
                xmark(q2[0], q2[1], a)
                xmark(q1[0], q1[1], ac)
                label("SIN PALANCA DE CAMBIOS", (q2[0], q2[1] + 18), (60, 1560), "lm", a, (255, 200, 200))
                label("SIN CLUTCH", (q1[0], q1[1] - 18), (1020, 520), "rm", ac, (255, 200, 200))
    if env == 'jump':
        bs = info.get('bikes', [])
        if bs:
            a = win(5.2, 8.9)
            g = P3(mm.world(bs[0]['pos'], 0, bs[0]['pitch'], (0, 200, 0)))
            e = P3(mm.world(bs[1]['pos'], 0, bs[1]['pitch'], (0, 200, 0)))
            if a > 0:
                label("450 DE GASOLINA", g, (1020, 520), "rm", a, (255, 210, 170))
                label("ELÉCTRICA", e, (60, 1500), "lm", a, (190, 240, 255))
    if env == 'gate':
        a = win(9.4, 12.8)
        if a > 0:
            k = ease(seg(t, 9.4, 9.9))
            DARK.append((380, 820, 700, 1000, a * 0.7))
            l2.text(P(540, 910), "VS", font=F(B, int(lerp(220, 140, k))), fill=sc3((255, 255, 255), a), anchor="mm")
            l2.text(P(270, 1560), "ELÉCTRICA", font=F(B, 50), fill=sc3(ECOL, a), anchor="mm")
            l2.text(P(270, 1620), "80 HP · 118 kg", font=F(M, 30), fill=sc3((200, 220, 240), a * ease(seg(t, 10.4, 10.8))), anchor="mm")
            l2.text(P(810, 1560), "GASOLINA 450", font=F(B, 50), fill=sc3(GCOL, a), anchor="mm")
            l2.text(P(810, 1620), "≈60 HP · ≈105-111 kg", font=F(M, 30), fill=sc3((240, 210, 190), a * ease(seg(t, 10.4, 10.8))), anchor="mm")
    if env == 'dyno':
        round_card(1, "POTENCIA", 13.1, 14.6, CYAN)
        a = win(14.2, 17.8)
        if a > 0:
            k1 = ease(seg(t, 14.3, 15.7))
            k2 = ease(seg(t, 16.3, 17.2))
            DARK.append((80, 440, 1000, 700, a))
            for i, (name, val, col, kk) in enumerate((("450 GASOLINA", 60, GCOL, k1), ("STARK VARG", 80, ECOL, k2))):
                y = 500 + i * 120
                l2.text(P(110, y), name, font=F(B, 32), fill=sc3((230, 230, 245), a), anchor="lm")
                l2.rectangle((*P(110, y + 25), *P(970, y + 55)), outline=sc3((90, 90, 130), a), width=max(1, int(2 * S)))
                l2.rectangle((*P(110, y + 25), *P(110 + 860 * val / 80 * kk, y + 55)), fill=sc3(col, a))
                l2.text(P(970, y), f"{int(val * kk)} HP", font=F(M, 40), fill=sc3(col, a), anchor="rm")
    if env == 'gears':
        round_card(2, "CAMBIOS", 18.1, 19.4, VIOLET)
        a = win(19.2, 20.8)
        if a > 0:
            label("5 VELOCIDADES", P3((8, 46, 0)), (60, 1500), "lm", a, (255, 210, 170))
            label("CLUTCH", P3(mm.HB + (14, -4, 38)), (1020, 560), "rm", a, (255, 210, 170))
        a = win(21.15, 22.8)
        if a > 0:
            label("1 SOLA VELOCIDAD", P3((-330 + 4, 40, 12)), (60, 1500), "lm", a, (190, 240, 255))
        pill("ACELERAS Y YA", 1600, win(21.75, 22.8), ECOL, 560, 38)
    if env == 'phone':
        round_card(3, "TU CELULAR", 23.1, 24.4, BLUE)
        a = win(24.5, 28.5)
        if a > 0:
            k = ease(seg(t, 27.0, 27.95))
            hp = int(10 + 70 * k)
            DARK.append((260, 1450, 820, 1640, a))
            l2.text(P(540, 1490), "POTENCIA", font=F(B, 30), fill=sc3((200, 210, 240), a), anchor="mm")
            l2.text(P(540, 1570), f"{hp} HP", font=F(M, 90), fill=sc3(lc(ECOL, (255, 255, 255), k * 0.4), a), anchor="mm")
        a = win(24.3, 26.6)
        if a > 0:
            label("TELÉFONO ANDROID", P3(scr(0.0, 1.0)), (1020, 700), "rm", a)
    if env == 'xray':
        a = win(29.8, 34.5)
        if a > 0:
            label("BATERÍA 7.2 kWh", P3((8, 70, 13)), (60, 560), "lm", ease(seg(t, 29.85, 30.2)) * a, (190, 240, 255))
            label("MOTOR ELÉCTRICO", P3((-2, 40, 12)), (60, 1480), "lm", ease(seg(t, 31.9, 32.25)) * a, (220, 200, 255))
            label("CONTROLADOR", P3((23, 88, 10)), (1020, 680), "rm", ease(seg(t, 31.0, 31.4)) * a, (255, 210, 170))
        pill("SIN PISTONES", 1600, win(32.9, 34.5), RED, 520, 36)
        pill("SIN FILTROS", 1700, win(33.75, 34.5, 0.3), RED, 520, 36)
    if env == 'arena':
        a = win(35.2, 40.1)
        if a > 0:
            DARK.append((120, 450, 960, 720, a))
            l2.text(P(540, 510), "MUNDIAL SUPERENDURO 2026", font=F(B, 36), fill=sc3((220, 220, 240), a), anchor="mm")
            l2.text(P(540, 580), "CAMPEÓN DE CONSTRUCTORES", font=F(B, 50), fill=sc3((255, 215, 90), a), anchor="mm")
            l2.text(P(540, 660), "1.ª MARCA ELÉCTRICA EN LOGRARLO", font=F(B, 30), fill=sc3(ECOL, a * ease(seg(t, 36.4, 36.8))), anchor="mm")
        for i, name in enumerate(("HUSQVARNA", "TRIUMPH")):
            a = win(38.75 + 0.65 * i, 40.1)
            if a > 0:
                x = 320 + 440 * i
                DARK.append((x - 190, 1560, x + 190, 1640, a))
                l2.rounded_rectangle((*P(x - 190, 1560), *P(x + 190, 1640)), radius=int(40 * S), outline=sc3((150, 150, 170), a), width=max(2, int(3 * S)))
                l2.text(P(x, 1600), name, font=F(B, 34), fill=sc3((190, 190, 205), a), anchor="mm")
    if env == 'scale':
        a = win(41.4, T_OUT + 0.4)
        if a > 0:
            bs = info.get('bikes')
            q1 = P3((SCALE_X[0], 78, -93))
            q2 = P3((SCALE_X[1], 78, -93))
            label("118 kg", q1, (60, 1440), "lm", a, (255, 170, 170))
            label("≈105-111 kg", q2, (1020, 1440), "rm", ease(seg(t, 42.45, 42.85)) * a, (200, 230, 255))
        pill("PUNTO DÉBIL: EL PESO", 1620, win(41.0, T_OUT + 0.3), RED, 680, 36)
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
        os.makedirs("/home/claude/varg_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/varg_prev/t_{ts}.png")
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
