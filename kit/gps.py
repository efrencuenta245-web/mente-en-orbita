"""Mente en órbita — ¿Cómo funciona el GPS?  (video 4)
Escenas: auto de noche (celular con mapa) · la ciudad se aleja hacia el espacio · constelación GPS ·
satélite en rayos X · celular en rayos X (solo recibe) · ciudad: señales, distancias y trilateración ·
relatividad · error sin corregir y zoom a 5 m · cierre en el auto."""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
import nc
import fo
from nc import proj, P2, vis
from fo import clip_near, poly, line3, pulses, resample, led
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of,
                  VIOLET, BLUE, CYAN, ORANGE)
import gps_earth as ge
import gps_ground as gg
from gps_geo import (norm, shade_l, cam_from, cam_keys, face, cbox, rot_x, rot_y, rot_z, xf, obox, ocyl,
                     proj_np, splat, seg_clip_uv, ring_pts, polyline3, glow_dot)

FPS = 24
DUR = 68.6
NF = int(DUR * FPS)
GREEN = (90, 255, 150)
RED = (255, 80, 80)

PHR = [
    (0.4, 4.3, "¿Cómo sabe tu celular dónde estás... si nadie se lo dice?", {4}),
    (4.8, 8.2, "La respuesta está a veinte mil kilómetros sobre tu cabeza.", {6}),
    (8.8, 13.8, "Ahí giran más de treinta satélites GPS, dando dos vueltas a la Tierra al día.", {5}),
    (14.4, 18.4, "Cada uno lleva relojes atómicos, precisos a la mil millonésima de segundo.", {4}),
    (18.9, 22.9, "Y transmiten sin parar quiénes son, dónde están y la hora exacta.", {10}),
    (23.5, 26.3, "Tu celular no les manda nada: solo escucha.", {7}),
    (26.9, 32.6, "La señal viaja a la velocidad de la luz y llega en menos de una décima de segundo.", {8}),
    (33.1, 36.8, "Con ese retraso, tu celular calcula su distancia a cada satélite.", {7}),
    (37.4, 40.6, "Con tres distancias, solo hay un punto posible: tú.", {8}),
    (41.3, 46.8, "Un cuarto satélite corrige el reloj del celular: una millonésima de segundo de error son trescientos metros.", {1, 15}),
    (47.5, 52.7, "Y hasta Einstein importa: allá arriba, los relojes se adelantan treinta y ocho microsegundos al día.", {2}),
    (53.2, 56.5, "Sin corregirlo, tu ubicación fallaría más de diez kilómetros diarios.", {7}),
    (57.1, 60.6, "Ya corregido, te ubica con un margen de unos cinco metros.", {9}),
    (61.3, 65.0, "Tu celular no sabe dónde estás: lo calcula midiendo el tiempo.", {10}),
    (65.8, 67.8, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)

CUTS = (4.6, 8.6, 14.2, 23.2, 26.6, 47.2, 52.9, 60.9)
T_OUT = 65.4
ENVS = ('car', 'rise', 'orbit', 'sat', 'carx', 'city', 'rel', 'drift', 'car2')


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


# =====================================================================
# Estrellas (direcciones en una esfera, sin paralaje)
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
# ESCENARIO A: interior del auto (mm). El auto avanza en +z; el mundo se mueve hacia -z.
# =====================================================================
V_CAR = 11000.0
LOOP = 384000.0
PHONE_C = np.array([-120.0, 1125.0, 400.0])
EYE = np.array([-380.0, 1250.0, -170.0])
_n = norm(EYE - PHONE_C)
_r = norm(np.cross(_n, (0, 1, 0)))
_u = np.cross(_r, _n)
PH_R, PH_U, PH_N = _r, _u, _n
PH_ROT = np.column_stack([_r, _u, _n])
NIGHT_L = norm((-0.3, 0.8, -0.5))

_rb = np.random.RandomState(8)
SIDE_B = {}
for side in (-1, 1):
    lst, z = [], 0.0
    while z < LOOP:
        w = _rb.uniform(14000, 30000)
        h = _rb.uniform(8000, 30000)
        col = [(70, 72, 84), (84, 76, 70), (64, 70, 82), (92, 88, 84), (60, 62, 72)][_rb.randint(0, 5)]
        lit = _rb.rand(40, 12) < 0.42
        tv = _rb.rand(40, 12) < 0.15
        lst.append((z, w, h, col, lit, tv))
        z += w + _rb.uniform(1500, 6000)
    SIDE_B[side] = lst
SKYLINE = [(-60000 + i * 9000 + _rb.uniform(-2000, 2000), _rb.uniform(20000, 70000), _rb.uniform(6000, 12000)) for i in range(14)]


def zloop(z0, t, speed=V_CAR):
    return (z0 - speed * t) % LOOP - 9000.0


def car_world(bd, la, buf, c, t, dim=1.0):
    # cielo
    for i in range(9):
        y0 = i * 9000
        poly(bd, c, [(-900000, y0, 700000), (900000, y0, 700000), (900000, y0 + 9000, 700000), (-900000, y0 + 9000, 700000)],
             lc((52, 30, 70), (8, 8, 22), i / 8), dim)
    poly(bd, c, [(-900000, 81000, 700000), (900000, 81000, 700000), (900000, 600000, 700000), (-900000, 600000, 700000)], (8, 8, 22), dim)
    # skyline lejano
    for (x, h, w) in SKYLINE:
        poly(bd, c, [(x, 0, 420000), (x + w, 0, 420000), (x + w, h, 420000), (x, h, 420000)], (18, 18, 36), dim)
    # suelo
    poly(bd, c, [(-60000, 0, -4000), (60000, 0, -4000), (60000, 0, 420000), (-60000, 0, 420000)], (20, 20, 26), dim)
    poly(bd, c, [(-5600, 1, -4000), (5600, 1, -4000), (5600, 1, 420000), (-5600, 1, 420000)], (34, 35, 42), dim)
    for sx_ in (-1, 1):
        poly(bd, c, [(sx_ * 5600, 150, -4000), (sx_ * 11500, 150, -4000), (sx_ * 11500, 150, 420000), (sx_ * 5600, 150, 420000)], (52, 52, 58), dim)
    # líneas de carril
    for k in range(43):
        z0 = zloop(k * 9000.0, t)
        if z0 > 330000:
            continue
        for lx in (-1850, 1850):
            poly(bd, c, [(lx - 70, 3, z0), (lx + 70, 3, z0), (lx + 70, 3, z0 + 3000), (lx - 70, 3, z0 + 3000)], (200, 200, 190), dim)
    sol = []
    # edificios
    for side, lst in SIDE_B.items():
        for (z0, w, h, col, lit, tv) in lst:
            zs = zloop(z0, t)
            if zs > 330000 or zs + w < -9000:
                continue
            fog = clamp(1.0 - zs / 340000.0) ** 0.7
            xa, xb = (11500, 26000) if side > 0 else (-26000, -11500)
            sol += cbox(c, xa, xb, 0, h, zs, zs + w, col, dim * (0.45 + 0.55 * fog), NIGHT_L, 0.55)
            if zs < 170000:
                xf_ = 11499 if side > 0 else -11499
                nrow = int((h - 3000) // 3600)
                ncol = int((w - 2400) // 3200)
                for r_ in range(min(nrow, 12)):
                    for q in range(min(ncol, 40)):
                        if not lit[q % 40, r_ % 12]:
                            continue
                        y0 = 3000 + r_ * 3600
                        zz = zs + 1500 + q * 3200
                        wc = (150, 170, 255) if tv[q % 40, r_ % 12] else (255, 206, 130)
                        f = face(c, [(xf_, y0, zz), (xf_, y0, zz + 1500), (xf_, y0 + 1800, zz + 1500), (xf_, y0 + 1800, zz)],
                                 (-side, 0, 0), sc3(wc, 0.85 * fog), 1.0, flat=True)
                        if f:
                            sol.append((f[0] - 1.0, f[1], f[2]))
    # postes de luz
    for k in range(13):
        z0 = zloop(k * 32000.0 + 6000, t)
        if z0 > 330000:
            continue
        for sx_ in (-1, 1):
            x = sx_ * 6400
            sol += cbox(c, x - 110, x + 110, 150, 9000, z0 - 110, z0 + 110, (70, 72, 78), dim, NIGHT_L)
            sol += cbox(c, min(x, x - sx_ * 1900), max(x, x - sx_ * 1900), 8800, 9000, z0 - 80, z0 + 80, (70, 72, 78), dim, NIGHT_L)
    # auto de enfrente y autos en sentido contrario
    zl = 26000 + 2500 * math.sin(t * 0.6)
    sol += cbox(c, -950, 950, 300, 1150, zl, zl + 4400, (128, 130, 140), dim * 0.8, NIGHT_L)
    sol += cbox(c, -800, 800, 1150, 1650, zl + 1000, zl + 3300, (30, 34, 44), dim * 0.8, NIGHT_L)
    fo.draw_solids(bd, sol)
    # luces
    for k in range(13):
        z0 = zloop(k * 32000.0 + 6000, t)
        if z0 > 330000 or z0 < 200:
            continue
        for sx_ in (-1, 1):
            hx = sx_ * 6400 - sx_ * 1800
            sx2, sy2, dep = proj(hx, 8750, z0, c)
            if dep > 300:
                r_ = max(2.0, 260000.0 / dep) * S
                glow_dot(la, sx2 * S, sy2 * S, r_, (255, 190, 110), 0.95)
                pool = [(hx + 1800 * math.cos(a), 5, z0 + 3000 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
                q = clip_near(pool, c)
                if len(q) > 2:
                    la.polygon([P2(*p, c) for p in q], fill=sc3((34, 24, 12), clamp(1 - z0 / 200000)))
    for xx in (-700, 700):
        led(la, c, (xx, 950, zl - 5), RED, 0.9, max(3, 9000.0 / max(1, proj(xx, 950, zl, c)[2]) * 30))
    for k in range(4):
        z0 = (k * 70000.0 - 2.3 * V_CAR * t) % 280000.0 + 6000
        for xx in (-4400, -2950):
            sx2, sy2, dep = proj(xx, 650, z0, c)
            if dep > 300:
                glow_dot(la, sx2 * S, sy2 * S, max(2.0, 160000.0 / dep) * S, (255, 250, 230), 0.9)


def scr_pt(u, v, off=0.6):
    p = PHONE_C + (u * 33.0) * PH_R + (v * 71.0) * PH_U + off * PH_N
    return (p[0], p[1], p[2])


def scr_line(d, c, a, b, col, wuv=0.03):
    s = seg_clip_uv(a, b)
    if not s:
        return
    p0, p1 = scr_pt(*s[0]), scr_pt(*s[1])
    dep = proj(*p0, c)[2]
    w = max(1, int(wuv * 33.0 * 1200.0 / max(dep, 1.0) * S))
    d.line([P2(*p0, c), P2(*p1, c)], fill=col, width=w)


def scr_quad(d, c, u0, v0, u1, v1, col, off=0.6):
    d.polygon([P2(*scr_pt(u0, v0, off), c), P2(*scr_pt(u1, v0, off), c), P2(*scr_pt(u1, v1, off), c), P2(*scr_pt(u0, v1, off), c)], fill=col)


def scr_disc(d, c, u, v, r, col, off=0.8, k=20):
    d.polygon([P2(*scr_pt(u + r * math.cos(a) * 71 / 33, v + r * math.sin(a), off), c) for a in np.linspace(0, 2 * math.pi, k, endpoint=False)], fill=col)


ROUTE = [(0.06, -1.2), (0.06, 0.38), (0.75, 0.38), (1.3, 0.38)]


def draw_map(od, la, c, t, a):
    """mapa de navegación en la pantalla del celular (sobre la capa RGBA)"""
    if a <= 0.01:
        return
    A = int(255 * a)
    scr_quad(od, c, -1, -1, 1, 1, (30, 34, 46, A))
    off = (t * 0.16) % 0.5
    for k in range(-1, 6):
        v = -1.0 + k * 0.5 - off
        if -1 < v < 1:
            scr_line(od, c, (-1, v), (1, v), (64, 72, 92, A), 0.05)
    for u in (-0.62, 0.62):
        scr_line(od, c, (u, -1), (u, 1), (64, 72, 92, A), 0.05)
    scr_line(od, c, (0.06, -1), (0.06, 1), (98, 108, 132, A), 0.11)
    for k in range(-1, 6):
        v = -0.75 + k * 0.5 - off
        if -1 < v < 1:
            scr_quad(od, c, -0.55, v - 0.06, -0.12, v + 0.12, (40, 66, 52, A))
    # banner de instrucción
    scr_quad(od, c, -1, 0.72, 1, 1.0, (24, 112, 74, A))
    for i, (u0, u1) in enumerate(((-0.25, 0.85), (-0.25, 0.4))):
        scr_quad(od, c, u0, 0.9 - i * 0.09, u1, 0.93 - i * 0.09, (230, 245, 235, A))
    scr_quad(od, c, -0.85, 0.78, -0.75, 0.93, (255, 255, 255, A))
    scr_quad(od, c, -0.85, 0.88, -0.55, 0.93, (255, 255, 255, A))
    # ruta
    rv = [(u, v - off * 0) for (u, v) in ROUTE]
    for i in range(len(rv) - 1):
        s = seg_clip_uv(rv[i], rv[i + 1])
        if s:
            p0, p1 = scr_pt(*s[0], 1.0), scr_pt(*s[1], 1.0)
            dep = proj(*p0, c)[2]
            w = max(2, int(0.09 * 33.0 * 1200.0 / max(dep, 1.0) * S))
            la.line([P2(*p0, c), P2(*p1, c)], fill=sc3((80, 150, 255), 0.85 * a), width=w)
    # punto azul (tú)
    pu, pv = 0.06, -0.38
    pul = 0.5 + 0.5 * math.sin(t * 4.0)
    scr_disc(od, c, pu, pv, 0.07 + 0.04 * pul, (60, 120, 255, int(90 * a)))
    scr_disc(od, c, pu, pv, 0.05, (255, 255, 255, A))
    scr_disc(od, c, pu, pv, 0.037, (40, 130, 255, A))


PH_PARTS = [  # (u0, v0, u1, v1, color) — interior del celular
    (-0.92, -0.95, 0.92, 0.95, (22, 30, 40)),
    (-0.78, -0.88, 0.78, 0.22, (66, 72, 86)),
    (-0.86, 0.30, 0.86, 0.93, (34, 112, 66)),
    (0.02, 0.48, 0.42, 0.70, (24, 26, 30)),
    (-0.20, 0.36, -0.02, 0.46, (24, 26, 30)),
    (0.48, 0.38, 0.78, 0.50, (24, 26, 30)),
    (0.42, 0.72, 0.78, 0.90, (40, 40, 46)),
]
GPS_CHIP = (-0.62, 0.52, -0.30, 0.74)
ANT_A, ANT_B = (-0.88, 0.965), (0.30, 0.965)


def draw_phone(bd, la, od, c, t, xr, map_a=1.0):
    pol = obox(c, tuple(PHONE_C), PH_ROT, (-38, -79, -9), (38, 79, 0), (16, 16, 20), 1.0, NIGHT_L, 0.6)
    # soporte
    back = PHONE_C - 9 * PH_N
    line3(bd, c, tuple(back), (-120, 1010, 520), (24, 24, 28), max(3, int(16 * S)))
    fo.draw_solids(bd, pol)
    if xr > 0.01:
        k = xr
        for (u0, v0, u1, v1, col) in PH_PARTS:
            scr_quad(bd, c, u0, v0, u1, v1, sc3(col, 0.3 + 0.7 * k), 0.3)
        # celdas de la batería
        for i in range(1, 6):
            v = -0.88 + i * 0.18
            scr_line(bd, c, (-0.78, v), (0.78, v), sc3((90, 96, 110), k), 0.02)
        scr_quad(bd, c, *GPS_CHIP, sc3((30, 40, 52), k), 0.35)
    draw_map(od, la, c, t, map_a * (1 - xr))
    if xr > 0.01:
        # contorno y escáner
        corners = [scr_pt(-1, -1, 1), scr_pt(1, -1, 1), scr_pt(1, 1, 1), scr_pt(-1, 1, 1), scr_pt(-1, -1, 1)]
        la.line([P2(*p, c) for p in corners], fill=sc3(BLUE, 0.8 * xr), width=max(2, int(3 * S)))
        vs = -1 + 2 * ((t * 0.55) % 1.0)
        a_, b_ = scr_pt(-1, vs, 1.2), scr_pt(1, vs, 1.2)
        la.line([P2(*a_, c), P2(*b_, c)], fill=sc3(CYAN, 0.9 * xr), width=max(2, int(4 * S)))
        g = 0.6 + 0.4 * math.sin(t * 9)
        u0, v0, u1, v1 = GPS_CHIP
        la.polygon([P2(*scr_pt(u0, v0, 1.2), c), P2(*scr_pt(u1, v0, 1.2), c), P2(*scr_pt(u1, v1, 1.2), c), P2(*scr_pt(u0, v1, 1.2), c)],
                   fill=sc3(CYAN, 0.55 * xr * g))


def car_interior(bd, la, c, t, dim=1.0):
    L = NIGHT_L
    # cofre (afuera)
    poly(bd, c, [(-880, 1010, 730), (880, 1010, 730), (860, 870, 2300), (-860, 870, 2300)], (30, 32, 42), dim * 0.85)
    # techo y pilares
    poly(bd, c, [(-950, 1470, 250), (950, 1470, 250), (950, 1500, -900), (-950, 1500, -900)], (44, 42, 48), dim)
    poly(bd, c, [(-820, 1435, 300), (820, 1435, 300), (820, 1475, 250), (-820, 1475, 250)], (22, 22, 26), dim)
    for sx_ in (-1, 1):
        poly(bd, c, [(sx_ * 950, 1000, 730), (sx_ * 790, 1000, 730), (sx_ * 680, 1475, 250), (sx_ * 850, 1475, 250)], (26, 26, 30), dim)
        poly(bd, c, [(sx_ * 950, 300, 730), (sx_ * 950, 1500, 250), (sx_ * 980, 1500, -900), (sx_ * 980, 300, -900)], (24, 24, 28), dim)
    # tablero
    poly(bd, c, [(-950, 960, 230), (950, 960, 230), (950, 1012, 732), (-950, 1012, 732)], (38, 38, 44), dim)
    poly(bd, c, [(-950, 620, 200), (950, 620, 200), (950, 960, 230), (-950, 960, 230)], (27, 27, 32), dim)
    pol = cbox(c, -600, -150, 930, 1015, 200, 330, (32, 32, 38), dim, L)
    fo.draw_solids(bd, pol)
    # pantalla central y ventilas
    scr = [(80, 760, 212), (420, 760, 212), (420, 925, 228), (80, 925, 228)]
    poly(bd, c, scr, (14, 16, 22), dim)
    q = clip_near(scr, c)
    if len(q) > 2:
        la.polygon([P2(*p, c) for p in q], fill=(10, 18, 34))
    for vx in (-760, 520):
        poly(bd, c, [(vx, 850, 207), (vx + 200, 850, 207), (vx + 200, 920, 213), (vx, 920, 213)], (16, 16, 19), dim)
        for k in range(1, 4):
            line3(bd, c, (vx, 850 + 17 * k, 208), (vx + 200, 850 + 17 * k, 208), (40, 40, 46), max(1, int(2 * S)))
    # tablero de instrumentos (brillo)
    for cxp in (-470, -280):
        pts = ring_pts((cxp, 900, 205), (0, 0.1, -1), 70, 28)
        polyline3(la, c, pts, sc3((90, 160, 255), 0.55), max(2, int(3 * S)))
    # volante
    wc = (-390, 985, 150)
    pts = ring_pts(wc, (0, 0.35, -0.94), 185, 40)
    polyline3(bd, c, pts, (16, 16, 18), max(4, int(24 * S)))
    for a in (0.0, math.pi, -math.pi / 2):
        pass
    hub = ring_pts(wc, (0, 0.35, -0.94), 55, 20)
    q = clip_near(hub, c)
    if len(q) > 2:
        bd.polygon([P2(*p, c) for p in q], fill=(22, 22, 25))
    for (a0) in (0.0, math.pi, -math.pi / 2):
        e = ring_pts(wc, (0, 0.35, -0.94), 185, 40)
        idx = int(((a0 % (2 * math.pi)) / (2 * math.pi)) * 40)
        line3(bd, c, wc, e[idx], (20, 20, 22), max(3, int(14 * S)))


# =====================================================================
# ESCENARIO B: ciudad de noche (m)
# =====================================================================
_rc = np.random.RandomState(12)
CITY_B = []
PARKS = []
TREES = []
PARK_BLOCKS = {(2, 1), (-3, -2), (-1, 3), (3, -4), (-5, 2), (1, -2)}
ROOFS = [(70, 72, 80), (78, 72, 66), (64, 70, 76), (84, 80, 74), (60, 62, 70), (74, 76, 84)]
for i in range(-6, 6):
    for j in range(-6, 6):
        bx0, bx1 = i * 110 + 10, i * 110 + 100
        bz0, bz1 = j * 110 + 10, j * 110 + 100
        if i == 0:
            bx0 += 6
        if i == -1:
            bx1 -= 6
        if (i, j) in PARK_BLOCKS:
            PARKS.append((bx0, bx1, bz0, bz1))
            for _ in range(16):
                tx, tz = _rc.uniform(bx0 + 6, bx1 - 6), _rc.uniform(bz0 + 6, bz1 - 6)
                TREES.append((tx, tz, _rc.uniform(2.5, 4.5)))
            continue
        rr = math.hypot(i * 110 + 55, j * 110 + 55)
        hmax = 85 * math.exp(-rr / 330.0) + 14
        mx, mz = (bx0 + bx1) / 2, (bz0 + bz1) / 2
        for (xa, xb) in ((bx0, mx - 2), (mx + 2, bx1)):
            for (za, zb) in ((bz0, mz - 2), (mz + 2, bz1)):
                if _rc.rand() < 0.12:
                    continue
                h = _rc.uniform(0.3, 1.0) * hmax
                lx, lz = int(xa > mx), int(za > mz)
                hv = (((i * 73856093) ^ (j * 19349663) ^ ((lx * 2 + lz) * 83492791)) & 0xFFFF) / 65535.0
                rv = 30 + 30 * hv
                col = (int(rv / 1.18), int(rv / 1.18), int(rv * 1.12 / 1.18))
                CITY_B.append((xa + 1.5, xb - 1.5, za + 1.5, zb - 1.5, h, col))

# ventanas: tiras iluminadas por piso (una lista por muro)
WIN = []  # por edificio: lista de 4 muros -> arrays (p0, p1, col)
for (x0, x1, z0, z1, h, col) in CITY_B:
    walls = []
    for (nrm, a, b) in (((0, 0, -1), (x0, z0), (x1, z0)), ((0, 0, 1), (x0, z1), (x1, z1)),
                        ((-1, 0, 0), (x0, z0), (x0, z1)), ((1, 0, 0), (x1, z0), (x1, z1))):
        segs = []
        if h > 10:
            nf = int((h - 4) // 3.6)
            for fl in range(nf):
                y = 3.5 + fl * 3.6
                for k in range(3):
                    if _rc.rand() < 0.45:
                        u0 = 0.08 + k * 0.31
                        u1 = u0 + _rc.uniform(0.08, 0.24)
                        pa = (lerp(a[0], b[0], u0) + nrm[0] * 0.05, y, lerp(a[1], b[1], u0) + nrm[2] * 0.05)
                        pb = (lerp(a[0], b[0], u1) + nrm[0] * 0.05, y, lerp(a[1], b[1], u1) + nrm[2] * 0.05)
                        wc = (255, 206, 130) if _rc.rand() < 0.8 else (160, 190, 255)
                        segs.append((pa, pb, wc))
        walls.append((nrm, segs))
    WIN.append(walls)

# alumbrado: puntos a lo largo de las calles
_sl = []
for i in range(-6, 7):
    for z in np.arange(-660, 660, 30.0):
        for off in (-11, 11):
            _sl.append((i * 110 + off, 7.0, z + (15 if off > 0 else 0)))
            _sl.append((z + (15 if off > 0 else 0), 7.0, i * 110 + off))
SL = np.array(_sl)
# autos circulando (puntos de faros)
CARS = [(_rc.randint(-6, 7), _rc.choice([0, 1]), _rc.uniform(0, 1320), _rc.uniform(8, 15), _rc.choice([-1, 1])) for _ in range(70)]

# región exterior (luces de la ciudad hasta el horizonte)
_ln = np.arange(-145, 146) * 110.0
_ss = np.arange(-16000, 16000, 38.0)
_A, _Bv = np.meshgrid(_ln, _ss, indexing='ij')
_A, _Bv = _A.ravel(), _Bv.ravel()
_side = np.where(_rc.rand(_A.size) < 0.5, -7.0, 7.0)
_X = np.concatenate([_A + _side, _Bv])
_Z = np.concatenate([_Bv, _A + _side])
_keep = ~((np.abs(_X) < 690) & (np.abs(_Z) < 690))
_ii = np.clip(gg._tx(_Z), 0, gg.GT - 1).astype(int)
_jj = np.clip(gg._tx(_X), 0, gg.GT - 1).astype(int)
_keep &= gg.URBAN[_ii, _jj]
_dd = np.hypot(_X, _Z)
_keep &= _rc.rand(_X.size) < (0.5 * np.exp(-_dd / 9000.0) + 0.08)
OL = np.stack([_X[_keep], np.full(_keep.sum(), 3.0), _Z[_keep]], 1)
OLI = _rc.uniform(0.25, 1.0, OL.shape[0])

CITY_CAR_X = 4.0


def city_ground(bd, c, dim, outer=True):
    poly(bd, c, [(-675, 0, -675), (675, 0, -675), (675, 0, 675), (-675, 0, 675)], (40, 35, 34), dim)
    for i in range(-6, 6):
        for j in range(-6, 6):
            bx0, bx1 = i * 110 + 10, i * 110 + 100
            bz0, bz1 = j * 110 + 10, j * 110 + 100
            if i == 0:
                bx0 += 6
            if i == -1:
                bx1 -= 6
            colg = (18, 34, 24) if (i, j) in PARK_BLOCKS else (22, 22, 28)
            poly(bd, c, [(bx0, 0.2, bz0), (bx1, 0.2, bz0), (bx1, 0.2, bz1), (bx0, 0.2, bz1)], colg, dim)
    # línea central de la avenida
    for z in range(-660, 660, 24):
        poly(bd, c, [(-0.3, 0.3, z), (0.3, 0.3, z), (0.3, 0.3, z + 10), (-0.3, 0.3, z + 10)], (210, 200, 150), dim)


def city_sky(bd, c, dim):
    for i in range(10):
        y0 = -200 + i * 700
        poly(bd, c, [(-80000, y0, 25000), (80000, y0, 25000), (80000, y0 + 700, 25000), (-80000, y0 + 700, 25000)],
             lc((60, 34, 76), (8, 8, 24), i / 9), dim)
    poly(bd, c, [(-80000, 6800, 25000), (80000, 6800, 25000), (80000, 60000, 25000), (-80000, 60000, 25000)], (8, 8, 24), dim)


def city_buildings(bd, c, dim, windows=True, car_z=0.0, car_on=True, md=None):
    L = NIGHT_L
    sol = []
    for bi, (x0, x1, z0, z1, h, col) in enumerate(CITY_B):
        # descarte rápido fuera de pantalla
        sx, sy, dep = proj((x0 + x1) / 2, h / 2, (z0 + z1) / 2, c)
        if dep < 1:
            continue
        rad = max(x1 - x0, h) * 1200.0 / dep
        if sx < -rad - 60 or sx > 1140 + rad or sy < -rad - 60 or sy > 1980 + rad:
            continue
        fog = clamp(1.0 - (dep - 1200.0) / 5000.0, 0.45, 1.0) if c['sp'] < 0.6 else 1.0
        col = tuple(int(v * fog) for v in col)
        faces = [((0, 1, 0), [(x0, h, z0), (x1, h, z0), (x1, h, z1), (x0, h, z1)]),
                 ((0, 0, -1), [(x0, 0, z0), (x1, 0, z0), (x1, h, z0), (x0, h, z0)]),
                 ((0, 0, 1), [(x0, 0, z1), (x1, 0, z1), (x1, h, z1), (x0, h, z1)]),
                 ((-1, 0, 0), [(x0, 0, z0), (x0, 0, z1), (x0, h, z1), (x0, h, z0)]),
                 ((1, 0, 0), [(x1, 0, z0), (x1, 0, z1), (x1, h, z1), (x1, h, z0)])]
        for fi, (n, pts) in enumerate(faces):
            f = face(c, pts, n, col if fi == 0 else tuple(int(v * 0.78) for v in col), dim, L, 0.5, near=2.0)
            if not f:
                continue
            sol.append(f)
            if windows and fi > 0 and dep < 2600:
                nrm, segs = WIN[bi][fi - 1]
                for (pa, pb, wc) in segs:
                    a2, b2 = proj(*pa, c), proj(*pb, c)
                    if a2[2] > 2 and b2[2] > 2:
                        wv = min(5, max(1, int(1.6 * 1200.0 / a2[2] * S)))
                        sol.append((f[0] - 0.01, ('L', (a2[0] * S, a2[1] * S), (b2[0] * S, b2[1] * S), wv), sc3(wc, 0.8 * dim)))
    for (tx, tz, r_) in TREES:
        sol += cbox(c, tx - r_, tx + r_, 0, r_ * 1.6, tz - r_, tz + r_, (30, 70, 40), dim, L, near=2.0)
    if car_on:
        cx = CITY_CAR_X
        sol += cbox(c, cx - 0.95, cx + 0.95, 0.25, 0.95, car_z - 2.3, car_z + 2.3, (34, 50, 92), dim, L, near=0.5)
        sol += cbox(c, cx - 0.8, cx + 0.8, 0.95, 1.45, car_z - 1.2, car_z + 0.9, (22, 26, 36), dim, L, near=0.5)
    sol.sort(key=lambda q: -q[0])
    for dep, pts, col in sol:
        if isinstance(pts, tuple) and pts and pts[0] == 'L':
            bd.line([pts[1], pts[2]], fill=col, width=pts[3])
        else:
            bd.polygon(pts, fill=col)
            if md is not None:
                md.polygon(pts, fill=255)


def city_lights(buf, la, c, t, outer=True, car_z=0.0, car_on=True, k=1.0):
    k = k * clamp(3000.0 / c['D'], 0.1, 1.0)
    # resplandor de las calles del centro (igual que la textura exterior), solo en vista desde arriba
    sdep = max(10.0, proj(0, 0, 0, c)[2])
    ek = (0.55 + 0.35 * clamp((c['D'] - 2500.0) / 25000.0)) * clamp((c['sp'] - 0.7) / 0.25) * clamp((c['D'] - 400.0) / 1500.0)
    for i in range(-6, 7):
        if ek <= 0.01:
            break
        wv = max(1, int(20 * 1200.0 / sdep * S))
        cl = sc3((255, 168, 78), (0.55 if i % 5 == 0 else 0.17) * ek)
        line3(la, c, (i * 110, 0.4, -665), (i * 110, 0.4, 665), cl, wv, 2.0)
        line3(la, c, (-665, 0.4, i * 110), (665, 0.4, i * 110), cl, wv, 2.0)
    splat(buf, c, SL[:, 0], SL[:, 1], SL[:, 2], (255, 170, 80), 1.1, near=2.0, size=2 if c['D'] < 1500 else 1, fade_far=1400.0)
    # autos
    X, Z, I = [], [], []
    for (line, axis, s0, v, d) in CARS:
        s = ((s0 + d * v * t) % 1320.0) - 660.0
        off = 4.0 * d
        if axis == 0:
            X.append(line * 110 + off)
            Z.append(s)
        else:
            X.append(s)
            Z.append(line * 110 + off)
    X, Z = np.array(X), np.array(Z)
    splat(buf, c, X, np.full_like(X, 0.8), Z, (255, 250, 230), 1.4 * k, near=2.0, size=2)
    if outer:
        splat(buf, c, OL[:, 0], OL[:, 1], OL[:, 2], (255, 196, 120), OLI * 1.3, near=2.0, size=1, fade_far=4000.0)
    if car_on:
        cx = CITY_CAR_X
        for dx in (-0.65, 0.65):
            led(la, c, (cx + dx, 0.7, car_z + 2.32), (255, 250, 235), 1.0, 4)
            led(la, c, (cx + dx, 0.75, car_z - 2.32), RED, 0.9, 3)
        cone = [(cx - 0.8, 0.05, car_z + 2.4), (cx + 0.8, 0.05, car_z + 2.4), (cx + 6, 0.05, car_z + 28), (cx - 6, 0.05, car_z + 28)]
        q = clip_near(cone, c, 0.5)
        if len(q) > 2:
            la.polygon([P2(*p, c) for p in q], fill=sc3((80, 74, 54), 0.9))


# =====================================================================
# ESCENARIO C: espacio — Tierra y constelación (km)
# =====================================================================
RE = 6371.0
RG = 26571.0
INC = math.radians(55.0)
PLANES = []
for k in range(6):
    Om = math.radians(60.0 * k + 12)
    Ry = rot_y(Om)
    e1 = Ry @ np.array([1.0, 0, 0])
    e2 = Ry @ np.array([0.0, math.sin(INC), math.cos(INC)])
    PLANES.append((e1, e2))
SATS = []
for k in range(6):
    n_ = 6 if k == 4 else 5
    for j in range(n_):
        SATS.append((k, 2 * math.pi * j / n_ + k * 0.45))
W_ORB = 0.10  # rad/s (visual; en la realidad 1 vuelta = 12 h)


def sat_pos(k, th0, t):
    e1, e2 = PLANES[k]
    th = th0 + W_ORB * t
    return RG * (math.cos(th) * e1 + math.sin(th) * e2)


def sat_icon(la, x, y, sc, a, col=CYAN):
    if a <= 0.02:
        return
    w = max(1, int(2 * S))
    la.line([(x - 11 * sc, y), (x + 11 * sc, y)], fill=sc3((110, 150, 255), a), width=max(1, int(3 * sc)))
    glow_dot(la, x, y, 3.2 * sc, col, a)
    glow_dot(la, x, y, 1.6 * sc, (255, 255, 255), a)


def orbit_scene(arr, la, c, t, ctr=(0, 0, 0), spin=-99.0, a_orb=1.0, highlight=None, sun=(-0.7, 0.35, -0.62)):
    draw_stars(arr, c)
    ge.render_earth(arr, c, ctr, RE, spin, sun)
    lw = max(1, int(2 * S))
    for k, (e1, e2) in enumerate(PLANES):
        pts = [RG * (math.cos(th) * e1 + math.sin(th) * e2) for th in np.linspace(0, 2 * math.pi, 97)]
        prev = None
        for p in pts:
            sx, sy, dep = proj(*p, c)
            okp = dep > 500 and not ge.occluded(c, p, ctr, RE)
            if prev is not None and okp:
                la.line([prev, (sx * S, sy * S)], fill=sc3(lc(VIOLET, BLUE, k / 5), 0.42 * a_orb), width=lw)
            prev = (sx * S, sy * S) if okp else None
    pos = []
    for (k, th0) in SATS:
        p = sat_pos(k, th0, t)
        sx, sy, dep = proj(*p, c)
        if dep < 800 or ge.occluded(c, p, ctr, RE):
            pos.append(None)
            continue
        sc = clamp(120000.0 / dep, 1.0, 2.8) * S
        sat_icon(la, sx * S, sy * S, sc, a_orb)
        pos.append((sx, sy))
    return pos


# =====================================================================
# ESCENARIO D: satélite GPS de cerca (cm) con la Tierra al fondo
# =====================================================================
def rot_axis(axis, ang):
    k = norm(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


_R0 = rot_x(math.radians(-30.0))
NADIR = _R0 @ np.array([0.0, -1.0, 0.0])
SAT_ROT = rot_axis(NADIR, math.radians(-38.0)) @ _R0
E_DIST = 2.657e9
E_CTR = tuple(-NADIR * -E_DIST) if False else tuple(NADIR * E_DIST)
E_R = 6.371e8
E_TILT = 35.0
SUN_SAT = norm((-0.55, 0.55, -0.62))
SAT_O = (0.0, 0.0, 0.0)
HELIX = [(math.cos(2 * math.pi * k / 8) * 52, math.sin(2 * math.pi * k / 8) * 46) for k in range(8)] + [(-18, -16), (18, -16), (-18, 16), (18, 16)]
CLOCKS = [(-48, 28, 0), (0, 28, 0), (48, 28, 0)]


def sat_solids(c, xo, dim=1.0, panel_ang=0.0):
    L = SUN_SAT
    Rm = SAT_ROT
    ctr = SAT_O
    sol, body = [], []
    alpha = None if xo <= 0.01 else int(255 * (1 - 0.82 * xo))
    gold = (206, 156, 62)
    body += obox(c, ctr, Rm, (-95, -105, -85), (95, 105, 85), gold, dim, L, 0.45)
    if alpha is not None:
        body = [(d_, p_, (*c_, alpha)) for (d_, p_, c_) in body]
    # panel de antenas (hacia la Tierra)
    sol += obox(c, ctr, Rm, (-88, -116, -78), (88, -105, 78), (226, 228, 234), dim, L, 0.5)
    for (hx, hz) in HELIX:
        sol += ocyl(c, ctr, Rm, (hx, -116, hz), 1, 7.5, -42, (240, 240, 244), 10, dim, L)
    # mástil superior
    sol += ocyl(c, ctr, Rm, (0, 105, 0), 1, 6, 60, (190, 192, 200), 10, dim, L)
    sol += obox(c, ctr, Rm, (-22, 160, -22), (22, 172, 22), (200, 202, 210), dim, L)
    # paneles solares
    Rp = Rm @ rot_x(panel_ang)
    for sx_ in (-1, 1):
        sol += ocyl(c, ctr, Rm, (sx_ * 95, 0, 0), 0, 5, sx_ * 80, (170, 172, 180), 8, dim, L)
        for seg_i in range(3):
            xa = sx_ * (180 + seg_i * 175)
            xb = xa + sx_ * 168
            lo = (min(xa, xb), -3, -115)
            hi = (max(xa, xb), 3, 115)
            sol += obox(c, ctr, Rp, lo, hi, (34, 58, 132), dim, L, 0.55)
    if xo > 0.01:
        # interior: relojes atómicos, procesador, transmisor, baterías
        for (cx_, cy_, cz_) in CLOCKS:
            sol += ocyl(c, ctr, Rm, (cx_, cy_, cz_ - 38), 2, 19, 76, (120, 210, 240), 14, dim, L)
        sol += obox(c, ctr, Rm, (-60, -30, -55), (60, -6, 55), (50, 150, 84), dim, L)
        sol += obox(c, ctr, Rm, (20, -90, -45), (78, -50, 45), (240, 132, 48), dim, L)
        sol += obox(c, ctr, Rm, (-82, -92, -60), (-24, -46, 60), (110, 114, 124), dim, L)
    return sol, body


def sat_scene(arr, la, c, t, xo, panel_ang=0.0, spin=-98.0):
    draw_stars(arr, c)
    ge.render_earth(arr, c, E_CTR, E_R, spin, SUN_SAT, tilt_deg=E_TILT)


def sat_draw(bd, od, la, c, t, xo, panel_ang=0.0):
    sol, body = sat_solids(c, xo, 1.0, panel_ang)
    if xo <= 0.01:
        fo.draw_solids(bd, sol + body)
    else:
        fo.draw_solids(bd, sol)
        body.sort(key=lambda q: -q[0])
        for dep, pts, col in body:
            od.polygon(pts, fill=col)
    # líneas de celdas en los paneles
    Rp = SAT_ROT @ rot_x(panel_ang)
    w1 = max(1, int(1.5 * S))
    for sx_ in (-1, 1):
        for seg_i in range(3):
            xa = sx_ * (180 + seg_i * 175)
            for q in range(1, 6):
                xq = xa + sx_ * 168 * q / 6
                p0, p1 = xf(Rp, SAT_O, (xq, 3.5, -115)), xf(Rp, SAT_O, (xq, 3.5, 115))
                if vis(c, xf(Rp, SAT_O, (xq, 3.5, 0)), tuple(Rp @ np.array([0, 1.0, 0]))):
                    line3(bd, c, p0, p1, (70, 96, 170), w1)
            for q in (-1, 0, 1):
                p0 = xf(Rp, SAT_O, (xa, 3.5, q * 57))
                p1 = xf(Rp, SAT_O, (xa + sx_ * 168, 3.5, q * 57))
                if vis(c, xf(Rp, SAT_O, (xa, 3.5, 0)), tuple(Rp @ np.array([0, 1.0, 0]))):
                    line3(bd, c, p0, p1, (70, 96, 170), w1)
    # hélices de las antenas
    for (hx, hz) in HELIX:
        pts = []
        for i in range(25):
            a = i / 24 * 6 * math.pi
            pts.append(xf(SAT_ROT, SAT_O, (hx + 8.2 * math.cos(a), -118 - 40 * i / 24, hz + 8.2 * math.sin(a))))
        polyline3(bd, c, pts, (150, 150, 160), max(1, int(1.5 * S)))
    if xo > 0.01:
        # relojes que laten
        for i, (cx_, cy_, cz_) in enumerate(CLOCKS):
            beat = (0.5 + 0.5 * math.sin(2 * math.pi * (t * 2.0 - i * 0.33))) ** 3
            for zz in (-38, 0, 38):
                pts = [xf(SAT_ROT, SAT_O, (cx_ + 21 * math.cos(a), cy_ + 21 * math.sin(a), cz_ + zz)) for a in np.linspace(0, 2 * math.pi, 25)]
                polyline3(la, c, pts, sc3(CYAN, xo * (0.35 + 0.65 * beat)), max(2, int(3 * S)))
        # contorno del cuerpo y escáner
        cs = [(-95, -105, -85), (95, -105, -85), (95, 105, -85), (-95, 105, -85)]
        for zz in (-85, 85):
            pts = [xf(SAT_ROT, SAT_O, (x, y, zz)) for (x, y, _) in cs + cs[:1]]
            polyline3(la, c, pts, sc3(BLUE, 0.7 * xo), max(1, int(2 * S)))
        xs = -95 + ((t * 0.45) % 1.0) * 190
        pts = [xf(SAT_ROT, SAT_O, p) for p in ((xs, -110, -90), (xs, 110, -90), (xs, 110, 90), (xs, -110, 90), (xs, -110, -90))]
        polyline3(la, c, pts, sc3(CYAN, 0.9 * xo), max(2, int(3 * S)))


def sat_waves(la, c, t, a):
    if a <= 0.01:
        return
    base = np.array(xf(SAT_ROT, SAT_O, (0, -160, 0)))
    for j in range(6):
        s = ((t * 0.55) + j / 6.0) % 1.0
        ctr = base + NADIR * (40 + 1500 * s)
        pts = ring_pts(tuple(ctr), NADIR, 40 + 520 * s, 48)
        polyline3(la, c, pts, sc3(lc(CYAN, BLUE, s), a * (1 - s) * 0.95), max(2, int(4 * S)))


# =====================================================================
# Señales en la ciudad: satélites "en el cielo" (posiciones esquemáticas)
# =====================================================================
U = np.array([CITY_CAR_X, 1.5, 40.0])
SKY_SATS = []
for (az, el, col) in ((-30, 21, VIOLET), (4, 25, BLUE), (32, 18, CYAN), (-10, 13, ORANGE)):
    a_, e_ = math.radians(az), math.radians(el)
    SKY_SATS.append((U + 5200.0 * np.array([math.sin(a_) * math.cos(e_), math.sin(e_), math.cos(a_) * math.cos(e_)]), col))
CIRC = []
for (az, rr, col) in ((-120, 620, VIOLET), (-15, 820, BLUE), (95, 560, CYAN), (200, 700, ORANGE)):
    a_ = math.radians(az)
    ctr = (U[0] + rr * math.sin(a_), 1.0, U[2] + rr * math.cos(a_))
    CIRC.append((ctr, rr, col))
DIST_TXT = ["20,310 km", "21,470 km", "22,860 km", "23,540 km"]


def circle3(ctr, r, a0=0.0, a1=2 * math.pi, k=90):
    return [(ctr[0] + r * math.sin(a), 1.2, ctr[2] + r * math.cos(a)) for a in np.linspace(a0, a1, k)]


# =====================================================================
# Cámaras por escena
# =====================================================================
PC = tuple(PHONE_C)
K_CAR = [(0.0, 215, 3, -24, 860, *PC), (1.0, 225, 3, -24, 860, *PC), (4.6, 720, 9, -18, 1130, -95, 1150, 600)]
K_RISE = [(4.6, 85, 38, 18, 1150, CITY_CAR_X, 0, 0), (8.6, 5200, 84, 40, 960, CITY_CAR_X, 0, 40)]
K_ORBIT = [(8.6, 15500, 10, 0, 1000, 0, 0, 0), (14.2, 82000, 22, 38, 1010, 0, 0, 0)]
K_SAT = [(14.2, 1250, 22, 4, 800, 0, 0, 0), (18.6, 1050, 20, 12, 800, 0, 0, 0), (19.4, 1350, 26, 2, 900, 0, -30, 0),
         (23.2, 1500, 28, -6, 920, 0, -50, 0)]
K_CARX = [(23.2, 270, 4, -26, 900, *PC), (26.6, 230, 3, -20, 860, *PC)]
K_CITY = [(26.6, 980, 15, -4, 1360, *U), (32.6, 900, 16, 4, 1360, *U), (36.8, 840, 18, 8, 1360, *U),
          (38.2, 2700, 84, 12, 980, U[0], 0, U[2] + 120), (41.0, 2750, 86, 14, 980, U[0], 0, U[2] + 120),
          (47.2, 2950, 86, 22, 980, U[0], 0, U[2] + 100)]
K_REL = [(47.2, 2500, 36, 10, 560, 0, 0, 0), (52.9, 3100, 38, -4, 560, 0, 0, 0)]
K_DRIFT = [(52.9, 36000, 86, 0, 980, 0, 0, 1500), (57.4, 34000, 86, 4, 960, CITY_CAR_X, 0, U[2]), (60.6, 170, 72, 20, 960, CITY_CAR_X, 0, U[2])]
K_CAR2 = [(60.9, 760, 9, -18, 1130, -95, 1150, 600), (68.6, 640, 8, -22, 1110, -100, 1145, 560)]
CAMS = {'car': (K_CAR, False), 'rise': (K_RISE, True), 'orbit': (K_ORBIT, True), 'sat': (K_SAT, False), 'carx': (K_CARX, False),
        'city': (K_CITY, False), 'rel': (K_REL, False), 'drift': (K_DRIFT, True), 'car2': (K_CAR2, False)}


def cam_for(env, t):
    keys, lg = CAMS[env]
    return cam_keys(t, keys, lg)


# =====================================================================
# Render
# =====================================================================
BITS = [1, 1, 0, 1, 0, 0, 1, 0, 1, 1]


def render(t):
    env = env_at(t)
    c = cam_for(env, t)
    base = Image.new("RGB", (W, H), (8, 8, 14))
    bd = ImageDraw.Draw(base)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    buf = np.zeros((H, W, 3), np.float32)
    arr = None
    info = {}

    if env in ('car', 'carx', 'car2'):
        car_world(bd, la, buf, c, t, 0.9)
        car_interior(bd, la, c, t, 0.95)
        xr = 0.0
        if env == 'carx':
            xr = ease(seg(t, 23.4, 24.2)) * (1 - ease(seg(t, 26.1, 26.5)))
        draw_phone(bd, la, od, c, t, xr, 1.0)
        if env == 'carx':
            # señales que llegan desde arriba a la antena
            A3 = scr_pt(-0.3, 0.965, 1.5)
            a = ease(seg(t, 23.6, 24.3))
            for i, (dirv, col) in enumerate((((-0.35, 1.0, 0.25), VIOLET), ((0.05, 1.0, 0.4), BLUE), ((0.4, 1.0, 0.15), CYAN))):
                d = norm(dirv)
                p0 = tuple(np.array(A3) + d * 3000)
                path = [tuple(np.array(p0) + (np.array(A3) - np.array(p0)) * (k / 40)) for k in range(41)]
                pr, ss = resample(path, 25)
                pulses(la, c, pr, ss, t + i * 0.2, 1800, BITS, a * 0.9, col, 90.0, max(2, int(4 * S)))
            for j in range(4):
                s = ((t * 0.9) + j / 4.0) % 1.0
                rr = 8 + 90 * (1 - s)
                pts = [scr_pt(-0.3 + rr / 33.0 * math.cos(q) * 0.5, 0.965 + rr / 71.0 * math.sin(q) * 0.5, 1.5) for q in np.linspace(0, 2 * math.pi, 30)]
                polyline3(la, c, pts, sc3(CYAN, a * s * 0.9), max(2, int(3 * S)))
            la.line([P2(*scr_pt(*ANT_A, 1.3), c), P2(*scr_pt(*ANT_B, 1.3), c)], fill=sc3(BLUE, xr * (0.6 + 0.4 * math.sin(t * 12))), width=max(2, int(5 * S)))
    elif env in ('rise', 'city', 'drift'):
        if env == 'rise':
            car_z = (t - 4.6) * 11.0
        else:
            car_z = U[2]
        gnd, emg = gg.render_ground(c, em_k=0.55 + 0.35 * clamp((c['D'] - 2500.0) / 25000.0))
        base = Image.fromarray(np.clip(gnd, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        city_ground(bd, c, 1.0, True)
        MK = Image.new("L", (W, H), 0)
        city_buildings(bd, c, 1.0, windows=c['D'] < 3000, car_z=car_z, md=ImageDraw.Draw(MK))
        bufG = emg
        splat(bufG, c, OL[:, 0], OL[:, 1], OL[:, 2], (255, 196, 120), OLI * 1.2, near=2.0, size=1, fade_far=5000.0)
        buf += bufG * (1 - np.asarray(MK, np.float32)[..., None] / 255.0)
        city_lights(buf, la, c, t, False, car_z)
        info['car_z'] = car_z
    elif env == 'orbit':
        arr = np.asarray(base, np.float32).copy()
        info['sats'] = orbit_scene(arr, la, c, t, spin=-99 + (t - 8.6) * 1.5)
    elif env in ('sat', 'rel'):
        arr = np.asarray(base, np.float32).copy()
        sat_scene(arr, la, c, t, 0.0, spin=-96 + (t - 14.2) * 0.4)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        xo = 0.0
        if env == 'sat':
            xo = ease(seg(t, 15.0, 15.8)) * (1 - ease(seg(t, 18.7, 19.3)))
        sat_draw(bd, od, la, c, t, xo, 0.0)
        if env == 'sat':
            sat_waves(la, c, t, ease(seg(t, 19.0, 19.6)) * (1 - ease(seg(t, 22.9, 23.2))))

    # ---------- efectos de la ciudad ----------
    if env == 'city':
        a_s = ease(seg(t, 26.8, 27.5)) * (1 - ease(seg(t, 36.9, 37.6)))
        for i, (sp, col) in enumerate(SKY_SATS):
            if i == 3 and t < 41.3:
                continue
            sx, sy, dep = proj(*sp, c)
            if dep > 10:
                sat_icon(la, sx * S, sy * S, 3.4 * S, a_s, col)
                glow_dot(la, sx * S, sy * S, 14 * S, col, 0.25 * a_s)
            if a_s > 0.02 and (i < 3):
                path = [tuple(sp + (U - sp) * (k / 60.0)) for k in range(61)]
                pr, ss = resample(path, 40)
                pulses(la, c, pr, ss, t + i * 0.3, 1500, BITS, a_s * 0.9, col, 160.0, max(2, int(4 * S)))
        # círculos de distancia (vista desde arriba)
        lw = max(2, int(4 * S))
        err = 0.0
        if t > 41.3:
            err = 110.0 * ease(seg(t, 41.4, 42.0)) * (1 - ease(seg(t, 43.6, 44.1)))
        for i, (ctr, rr, col) in enumerate(CIRC):
            if i < 3:
                st = 37.7 + 0.8 * i
                g = ease(seg(t, st, st + 0.7))
            else:
                g = ease(seg(t, 42.0, 42.9))
            if g <= 0:
                continue
            r_ = rr + (err if i < 3 else -err * 0.0) * (1 if i != 1 else -0.7)
            if i == 3:
                r_ = rr + err * 0.4
            a0 = math.atan2(U[0] - ctr[0], U[2] - ctr[2])
            pts = circle3(ctr, r_, a0 - math.pi * g, a0 + math.pi * g, 120)
            polyline3(la, c, pts, sc3(col, 0.9), lw)
            sx, sy, dep = proj(*ctr, c)
            glow_dot(la, sx * S, sy * S, 5 * S, col, 0.8 * g)
        # puntos candidatos
        if 38.6 < t < 39.4:
            for (px_, pz_) in ((U[0], U[2]), (U[0] - 690, U[2] + 520)):
                pass
        if t > 39.9:
            pa = ease(seg(t, 39.9, 40.3))
            fl = 1.0 if t < 41.3 or t > 44.1 else 0.35
            sx, sy, dep = proj(*U, c)
            glow_dot(la, sx * S, sy * S, (9 + 6 * (1 - pa)) * S, (255, 255, 255), pa * fl)
            if 43.6 < t < 44.6:
                f2 = 1 - seg(t, 43.6, 44.6)
                glow_dot(la, sx * S, sy * S, 40 * S * (1 - f2) + 8, (180, 220, 255), f2 * 0.8)
    if env == 'drift':
        # pin real y pin que se desvía
        sxu, syu, _ = proj(*U, c)
        d_err = 11000.0 * ease(seg(t, 53.4, 56.4)) * (1 - ease(seg(t, 57.2, 57.8)))
        ang = 0.6 + 0.25 * math.sin(t * 0.7)
        Wp = (U[0] + d_err * math.cos(ang), 1.5, U[2] + d_err * math.sin(ang))
        info['wp'] = Wp
        info['derr'] = d_err
        if d_err > 5:
            n_ = 40
            pts = [(U[0] + d_err * (k / n_) * math.cos(ang + 0.15 * math.sin(k / n_ * 3)), 1.5,
                    U[2] + d_err * (k / n_) * math.sin(ang + 0.15 * math.sin(k / n_ * 3))) for k in range(n_ + 1)]
            for k in range(0, n_, 2):
                line3(la, c, pts[k], pts[k + 1], sc3(ORANGE, 0.9), max(2, int(4 * S)))
            sx, sy, dep = proj(*Wp, c)
            glow_dot(la, sx * S, sy * S, 9 * S, ORANGE, 1.0)
        # círculo de precisión de 5 m
        pa = ease(seg(t, 58.6, 59.4))
        if pa > 0:
            pts = circle3((U[0], 0, U[2]), 5.0, 0, 2 * math.pi, 60)
            q = clip_near(pts, c, 0.5)
            if len(q) > 2:
                od.polygon([P2(*p, c) for p in q], fill=(70, 150, 255, int(70 * pa)))
            polyline3(la, c, pts, sc3(BLUE, pa), max(2, int(4 * S)), near=0.5)

    # ---------- composición ----------
    if arr is None:
        arr = np.asarray(base, np.float32)
    imgA = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")
    LAa = np.asarray(LA, np.float32) + buf
    gl = glow_of(Image.fromarray(np.clip(LAa, 0, 255).astype(np.uint8)), 4)
    out = np.asarray(imgB, np.float32) + LAa + 1.5 * gl
    if env == 'rise':
        # estelas de ascenso
        u = seg(t, 7.2, 8.6)
        if u > 0:
            st = Image.new("RGB", (W, H), (0, 0, 0))
            sd = ImageDraw.Draw(st)
            rs = np.random.RandomState(int(t * 24))
            for _ in range(40):
                a = rs.uniform(0, 2 * math.pi)
                r0 = rs.uniform(200, 900) * S
                r1 = r0 + rs.uniform(80, 300) * S * u
                cx, cy = W / 2, H / 2
                sd.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))],
                        fill=sc3((170, 190, 255), 0.5 * u), width=max(1, int(2 * S)))
            out = out + np.asarray(st, np.float32)
            out = out * (1 - 0.5 * u) + np.array([10, 14, 40], np.float32) * u
    f = 1.0
    for ct in CUTS:
        f = min(f, clamp(abs(t - ct) / 0.28))
    out = out * f
    out = out * (1 - 0.9 * seg(t, T_OUT, T_OUT + 0.8))

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
    out = out * (seg(t, 0.0, 0.4) * (1 - seg(t, DUR - 0.5, DUR)))
    return np.clip(out, 0, 255).astype(np.uint8)


# =====================================================================
# HUD
# =====================================================================
DARK = []


def hud(l2, c, t, env, info):
    def label(txt, target, text_pos, anchor, a, col=(185, 185, 225)):
        if a <= 0:
            return
        f = F(B, 30)
        tw = f.getlength(txt) / S
        tx, ty = text_pos
        l2.text(P(tx, ty), txt, font=f, fill=sc3(col, a), anchor=anchor)
        ex = (tx - tw - 14) if anchor == "rm" else (tx + tw + 14)
        l2.line([P(*target), P(ex, ty)], fill=sc3((140, 140, 200), a), width=max(1, int(2 * S)))
        rr = 6 * S
        px, py = P(*target)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), outline=sc3((210, 210, 245), a), width=max(1, int(2 * S)))

    def pill(txt, y, a, col=BLUE, w=560, size=36):
        if a <= 0:
            return
        DARK.append((540 - w / 2, y - 42, 540 + w / 2, y + 42, a))
        l2.rounded_rectangle((*P(540 - w / 2, y - 42), *P(540 + w / 2, y + 42)), radius=int(42 * S), outline=sc3(col, a), width=max(2, int(3 * S)))
        l2.text(P(540, y), txt, font=F(B, size), fill=sc3((225, 235, 255), a), anchor="mm")

    def panel(lines, x0, y0, x1, a, col=(100, 90, 190), size=40, lh=60, font=M):
        if a <= 0:
            return
        y1 = y0 + 40 + lh * len(lines)
        DARK.append((x0, y0, x1, y1, a))
        l2.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=int(22 * S), outline=sc3(col, a * 0.9), width=max(1, int(2 * S)))
        for i, (txt, aa, cc) in enumerate(lines):
            if aa > 0:
                l2.text(P(x0 + 30, y0 + 20 + lh * i + lh / 2), txt, font=F(font, size), fill=sc3(cc, a * aa), anchor="lm")

    def win(a, b, e=0.5):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def pin(x, y, a, col=(60, 140, 255), drop=1.0, txt=None, side=1):
        if a <= 0:
            return
        y = y - 260 * (1 - ease(drop)) ** 2
        pts = [P(x + 26 * math.cos(q), y - 62 + 26 * math.sin(q)) for q in np.linspace(math.radians(140), math.radians(400), 24)]
        pts.append(P(x, y))
        l2.polygon(pts, fill=sc3((255, 255, 255), a))
        rr = 13 * S
        cx, cy = P(x, y - 62)
        l2.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=sc3(col, a))
        if txt:
            l2.text(P(x + side * 44, y - 62), txt, font=F(B, 40), fill=sc3((255, 255, 255), a), anchor="lm" if side > 0 else "rm")

    for ct in CUTS:
        if abs(t - ct) < 0.3:
            return
    def P3(p):
        sx, sy, _ = proj(*p, c)
        return (sx, sy)

    if env == 'car':
        a = win(1.2, 4.4)
        if a > 0:
            label("TÚ", P3(scr_pt(0.06, -0.38, 1.0)), (1010, 1480), "rm", a, (255, 255, 255))
        pill("19.4326° N   99.1332° O", 1600, win(2.2, 4.5), BLUE, 700, 34)
    if env == 'rise':
        a = win(5.0, 8.5, 0.4)
        if a > 0:
            u = ease(seg(t, 5.0, 8.3))
            alt = 0.05 * (20200 / 0.05) ** (u ** 1.15)
            txt = f"{alt:,.0f} km" if alt >= 10 else f"{alt:.2f} km"
            DARK.append((200, 470, 880, 650, a))
            l2.rounded_rectangle((*P(200, 470), *P(880, 650)), radius=int(24 * S), outline=sc3((100, 90, 190), a * 0.9), width=max(1, int(2 * S)))
            l2.text(P(540, 530), "ALTITUD", font=F(B, 32), fill=sc3((170, 160, 230), a), anchor="mm")
            l2.text(P(540, 600), txt, font=F(M, 76), fill=sc3((235, 225, 255), a), anchor="mm")
    if env == 'orbit':
        sats = info.get('sats', [])
        a = win(9.2, 13.9)
        if a > 0 and sats:
            best = None
            for s_ in sats:
                if s_ and 120 < s_[0] < 960 and 480 < s_[1] < 1400:
                    if best is None or s_[1] < best[1]:
                        best = s_
            if best:
                label("SATÉLITE GPS", best, (1020, 500) if best[0] < 600 else (60, 500), "rm" if best[0] < 600 else "lm", a)
        pill("20,200 km DE ALTURA", 1560, win(9.0, 11.4), VIOLET, 620, 34)
        pill("MÁS DE 30 SATÉLITES", 1560, win(11.5, 13.0), BLUE, 620, 34)
        pill("1 VUELTA CADA 12 HORAS", 1560, win(13.0, 14.1, 0.3), CYAN, 680, 34)
    if env == 'sat':
        if 15.2 < t < 19.2:
            specs = [(15.5, "RELOJES ATÓMICOS", (0, 28, 0), (60, 470), "lm"),
                     (16.3, "TRANSMISOR", (50, -70, 0), (1020, 470), "rm"),
                     (17.0, "ANTENAS", (60, -150, 40), (1020, 1500), "rm"),
                     (17.6, "PANELES SOLARES", (-520, 0, 0), (60, 1180), "lm")]
            for (ta, txt, p3, tp, anc) in specs:
                a = ease(seg(t, ta, ta + 0.45)) * (1 - ease(seg(t, 18.6, 19.1)))
                if a > 0:
                    label(txt, P3(xf(SAT_ROT, SAT_O, p3)), tp, anc, a)
        pill("0.000 000 001 s", 1660, win(16.6, 18.9), CYAN, 560, 40)
        a = win(19.6, 23.1)
        if a > 0:
            ns = int((t * 1e9) % 1e9)
            lines = [("SOY: GPS 07", ease(seg(t, 20.2, 20.6)), (230, 225, 255)),
                     ("ESTOY: ÓRBITA C2", ease(seg(t, 21.0, 21.4)), (230, 225, 255)),
                     (f"HORA: 12:08:{int(t) % 60:02d}.{ns:09d}", ease(seg(t, 22.0, 22.4)), (170, 235, 255))]
            panel(lines, 120, 470, 960, a, size=38, lh=62)
    if env == 'carx':
        a = win(23.8, 26.4)
        if a > 0:
            label("ANTENA GPS", P3(scr_pt(-0.3, 0.965, 1.0)), (1020, 470), "rm", a)
            label("CHIP RECEPTOR", P3(scr_pt(-0.46, 0.63, 1.0)), (60, 1480), "lm", a)
        pill("SOLO RECIBE SEÑALES", 1600, win(24.6, 26.4), GREEN, 640, 34)
        pill("NO ENVÍA NADA AL SATÉLITE", 1700, win(25.1, 26.4), RED, 760, 32)
    if env == 'city':
        a = win(28.2, 32.8)
        if a > 0:
            u = ease(seg(t, 28.4, 31.8))
            DARK.append((200, 470, 880, 650, a))
            l2.rounded_rectangle((*P(200, 470), *P(880, 650)), radius=int(24 * S), outline=sc3((100, 90, 190), a * 0.9), width=max(1, int(2 * S)))
            l2.text(P(540, 530), "TIEMPO DE VIAJE", font=F(B, 32), fill=sc3((170, 160, 230), a), anchor="mm")
            l2.text(P(540, 600), f"{0.067 * u:.3f} s", font=F(M, 76), fill=sc3((235, 225, 255), a), anchor="mm")
        pill("LUZ: 300,000 km POR SEGUNDO", 1620, win(29.0, 32.8), CYAN, 800, 32)
        if 33.0 < t < 37.2:
            for i in range(3):
                ta = 33.4 + 0.6 * i
                a = ease(seg(t, ta, ta + 0.4)) * (1 - ease(seg(t, 36.6, 37.1)))
                sp, col = SKY_SATS[i]
                mid = tuple(sp + (U - sp) * 0.62)
                tg = P3(mid)
                tp = (60, 760 + 120 * i) if tg[0] < 540 else (1020, 760 + 120 * i)
                label(DIST_TXT[i], tg, tp, "lm" if tg[0] < 540 else "rm", a, lc(col, (255, 255, 255), 0.5))
        pill("DISTANCIA = TIEMPO × VELOCIDAD", 1620, win(34.2, 37.0), BLUE, 820, 32)
        a = win(37.8, 47.0)
        if a > 0:
            l2.text(P(1040, 1860), "ESQUEMA SIMPLIFICADO", font=F(B, 24), fill=sc3((150, 150, 190), a * 0.8), anchor="rm")
        if 38.9 < t < 39.95:
            ab = (0.5 + 0.5 * math.sin((t - 38.9) * 14)) * (1 - seg(t, 39.6, 39.95))
            (c0, r0, _), (c1, r1, _) = CIRC[0][:3], CIRC[1][:3]
            dx_, dz_ = c1[0] - c0[0], c1[2] - c0[2]
            dd = math.hypot(dx_, dz_)
            aa = (r0 * r0 - r1 * r1 + dd * dd) / (2 * dd)
            hh = math.sqrt(max(0.0, r0 * r0 - aa * aa))
            mx_, mz_ = c0[0] + aa * dx_ / dd, c0[2] + aa * dz_ / dd
            for sg in (-1, 1):
                q = P3((mx_ + sg * hh * (-dz_) / dd, 1.0, mz_ + sg * hh * dx_ / dd))
                rr = 11 * S
                px, py = P(*q)
                l2.ellipse((px - rr, py - rr, px + rr, py + rr), outline=sc3((255, 255, 255), ab), width=max(2, int(3 * S)))
        a = win(40.0, 41.4)
        if a > 0:
            q = P3(U)
            pin(q[0], q[1], a, BLUE, seg(t, 40.0, 40.35), "TÚ")
        a = win(41.6, 44.0)
        if a > 0:
            l2.text(P(540, 1080), "?", font=F(B, 120), fill=sc3((255, 200, 120), a * (1 - ease(seg(t, 43.4, 43.8)))), anchor="mm")
        pill("4.º SATÉLITE: CORRIGE EL RELOJ", 1600, win(42.0, 44.2), ORANGE, 840, 32)
        a = win(44.0, 47.1)
        if a > 0:
            q = P3(U)
            pin(q[0], q[1], a, BLUE, 1.0, "TÚ")
        pill("0.000001 s DE ERROR = 300 m", 1600, win(44.3, 47.1), RED, 800, 34)
    if env == 'rel':
        a = win(47.6, 52.8)
        if a > 0:
            label("RELOJ EN ÓRBITA", P3((0, 110, 0)), (1020, 480), "rm", a, (190, 240, 255))
            mex = ge.surf_point(E_CTR, E_R, 19.4, -99.1, -96 + (t - 14.2) * 0.4, E_TILT)
            tg = P3(mex)
            if 0 < tg[0] < 1080 and 0 < tg[1] < 1920:
                label("RELOJ EN LA TIERRA", tg, (60, 1440), "lm", a)
            u = ease(seg(t, 49.5, 52.2))
            hrs = 24 * u
            lines = [("TIERRA   " + f"{int(hrs):02d}:{int(hrs * 60) % 60:02d}:00.000000", 1.0, (220, 220, 240)),
                     ("ÓRBITA   " + f"{int(hrs):02d}:{int(hrs * 60) % 60:02d}:00.{int(38 * u):06d}", 1.0, (170, 235, 255))]
            panel(lines, 90, 1530, 990, a * ease(seg(t, 48.6, 49.2)), size=34, lh=56)
        pill("+38 MICROSEGUNDOS AL DÍA", 1800, win(50.6, 52.9, 0.4), CYAN, 760, 34)
        pill("RELATIVIDAD · EINSTEIN", 1800, win(47.8, 50.5, 0.4), VIOLET, 660, 34)
    if env == 'drift':
        de = info.get('derr', 0.0)
        a = win(53.3, 57.6)
        if a > 0:
            q = P3(U)
            pin(q[0], q[1], a, BLUE)
            label("POSICIÓN REAL", (q[0], q[1] - 62), (60, 1480), "lm", a, (190, 220, 255))
            if de > 300:
                q2 = P3(info['wp'])
                pin(q2[0], q2[1], a, ORANGE)
                label("SIN CORREGIR", (q2[0], q2[1] - 62), (1020, 500), "rm", a, (255, 200, 140))
            DARK.append((230, 470, 850, 620, a))
            l2.rounded_rectangle((*P(230, 470), *P(850, 620)), radius=int(24 * S), outline=sc3((200, 130, 80), a * 0.9), width=max(1, int(2 * S)))
            l2.text(P(540, 545), f"ERROR: {de / 1000:.1f} km", font=F(M, 64), fill=sc3((255, 210, 160), a), anchor="mm")
        pill("+10 km CADA DÍA SIN CORREGIR", 1600, win(54.4, 57.4), ORANGE, 820, 32)
        pill("≈ 5 m A CIELO ABIERTO", 1600, win(58.9, 60.8, 0.4), BLUE, 640, 36)
        a = win(59.2, 60.8, 0.4)
        if a > 0:
            q = P3((U[0], 1.5, U[2]))
            pin(q[0], q[1] - 30, a, BLUE, seg(t, 59.2, 59.5), "TÚ")
    if env == 'car2':
        a = win(61.4, 65.2)
        if a > 0:
            label("TÚ", P3(scr_pt(0.06, -0.38, 1.0)), (1010, 1480), "rm", a, (255, 255, 255))
        pill("CALCULADO CON EL TIEMPO", 1600, win(62.4, 65.2), VIOLET, 700, 34)
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
        os.makedirs("/home/claude/gps_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/gps_prev/t_{ts}.png")
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
