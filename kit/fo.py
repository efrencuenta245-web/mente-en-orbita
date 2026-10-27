import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
import nc
from nc import proj, P2, vis, shade, box_polys, cyl_polys
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of,
                  VIOLET, BLUE, CYAN, ORANGE, COPPER, STARS)

FPS = 24
DUR = 67.6
NF = int(DUR * FPS)

PHR = [
    (0.4, 4.6, "¿Cómo viaja un video por medio mundo en un instante...", {9}),
    (4.7, 8.8, "dentro de un hilo de vidrio tan delgado como un cabello?", {10}),
    (9.6, 12.9, "La fibra óptica no manda electricidad: manda luz.", {7}),
    (13.7, 16.3, "Tu internet empieza como señales eléctricas.", {4}),
    (16.5, 22.0, "Un láser las convierte en destellos: encendido, apagado, miles de millones de veces por segundo.", {1}),
    (22.8, 26.8, "Pero la luz no se escapa: el hilo tiene un núcleo", {10}),
    (26.9, 32.9, "y una capa de otro vidrio, y la luz rebota en la frontera como en un espejo.", {2}),
    (33.6, 36.2, "Se llama reflexión total interna.", {2}),
    (37.2, 41.5, "Por dentro hay también una cubierta protectora y hebras de refuerzo.", {6}),
    (42.3, 46.3, "La luz recorre decenas de kilómetros perdiendo muy poca fuerza,", {5}),
    (46.4, 52.1, "y se pueden enviar varios colores a la vez, cada uno con sus propios datos.", {5}),
    (52.9, 59.4, "Al llegar a tu casa, un aparato convierte la luz en señal eléctrica... y tu video aparece.", {6}),
    (60.2, 64.0, "Tu internet no viaja por el aire: viaja como luz.", {9}),
    (64.6, 66.6, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)

CUTS = (13.4, 22.6, 42.0, 52.6)
T_OUT = 64.2

# ---------------- cámara ----------------
KEYS = [
    (0.0, 1450, 7, -22, 1090, 150, 380, 200),
    (4.7, 1350, 7, -14, 1090, 250, 450, 450),
    (9.6, 1250, 8, -8, 1090, 100, 480, 650),
    (13.2, 800, 10, -30, 1090, -40, 480, 800),
    (13.4, 1000, 10, -22, 1100, 0, 500, 150),
    (22.4, 720, 8, 10, 1100, 0, 520, 150),
    (22.6, 640, 6, -8, 1100, 0, 480, 0),
    (36.0, 600, 6, -14, 1100, 0, 480, 0),
    (36.4, 580, 10, -28, 1080, 0, 480, 0),
    (41.8, 520, 14, -58, 1080, 0, 480, 0),
    (42.0, 1300, 14, -25, 1100, 0, 90, 0),
    (46.2, 1100, 16, -5, 1100, 0, 120, 0),
    (52.4, 800, 18, 12, 1100, 0, 150, 0),
    (52.6, 1500, 18, -8, 1100, 0, 300, 500),
    (55.0, 1050, 16, -12, 1100, -450, 300, 700),
    (57.5, 1100, 16, 6, 1100, 150, 330, 700),
    (67.6, 1550, 14, 0, 1100, 50, 300, 600),
]


def cam_at(t):
    v = None
    for i in range(len(KEYS) - 1):
        a, b = KEYS[i], KEYS[i + 1]
        if a[0] <= t <= b[0]:
            e = ease((t - a[0]) / max(1e-6, b[0] - a[0]))
            v = [lerp(a[j], b[j], e) for j in range(1, 8)]
            break
    if v is None:
        v = list(KEYS[-1][1:])
    D, phi, yaw, cy, fx, fy, fz = v
    pr, yr = math.radians(phi), math.radians(yaw)
    c = dict(D=D, cy=cy, cp=math.cos(pr), sp=math.sin(pr), ca=math.cos(yr), sa=math.sin(yr), f=(fx, fy, fz))
    c['pos'] = (fx + D * c['cp'] * c['sa'], fy + D * c['sp'], fz - D * c['cp'] * c['ca'])
    return c


# ---------------- utilidades ----------------
def clip_near(pts3, c, near=40.0):
    out = []
    n = len(pts3)
    deps = [proj(*p, c)[2] for p in pts3]
    for i in range(n):
        a, b = pts3[i], pts3[(i + 1) % n]
        da, db = deps[i], deps[(i + 1) % n]
        if da >= near:
            out.append(a)
        if (da >= near) != (db >= near):
            f = (near - da) / (db - da)
            out.append(tuple(lerp(a[k], b[k], f) for k in range(3)))
    return out


def poly(d, c, pts3, col, dim=1.0):
    q = clip_near(pts3, c)
    if len(q) >= 3:
        d.polygon([P2(*p, c) for p in q], fill=tuple(max(0, min(255, int(v * dim))) for v in col))


def line3(d, c, p0, p1, col, w=1, near=40.0):
    da, db = proj(*p0, c)[2], proj(*p1, c)[2]
    if da < near and db < near:
        return
    if da < near:
        f = (near - da) / (db - da)
        p0 = tuple(lerp(p0[k], p1[k], f) for k in range(3))
    elif db < near:
        f = (near - da) / (db - da)
        p1 = tuple(lerp(p0[k], p1[k], f) for k in range(3))
    d.line([P2(*p0, c), P2(*p1, c)], fill=col, width=w)


def qy(x0, x1, z0, z1, y=0.0):
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]


def qz(x0, x1, y0, y1, z):
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


def qx(y0, y1, z0, z1, x):
    return [(x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0)]


def draw_solids(d, polys):
    polys.sort(key=lambda q: -q[0])
    for dep, pts, col in polys:
        d.polygon(pts, fill=col)


def sag_path(p0, p1, sag, n):
    return [(lerp(p0[0], p1[0], i / n), lerp(p0[1], p1[1], i / n) - sag * 4 * (i / n) * (1 - i / n), lerp(p0[2], p1[2], i / n)) for i in range(n + 1)]


def crom(pts, per=10):
    out = []
    P_ = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for k in range(per):
            u = k / per
            out.append(tuple(0.5 * ((2 * p1[m]) + (-p0[m] + p2[m]) * u + (2 * p0[m] - 5 * p1[m] + 4 * p2[m] - p3[m]) * u * u + (-p0[m] + 3 * p1[m] - 3 * p2[m] + p3[m]) * u ** 3) for m in range(3)))
    out.append(tuple(pts[-1]))
    return out


def resample(pts, ds):
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.dist(pts[i], pts[i - 1]))
    tot = L[-1]
    n = max(2, int(tot / ds))
    out, ss = [], []
    j = 0
    for k in range(n + 1):
        s = tot * k / n
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        f = (s - L[j]) / max(1e-9, L[j + 1] - L[j])
        out.append(tuple(lerp(pts[j][m], pts[j + 1][m], f) for m in range(3)))
        ss.append(s)
    return out, ss


def pulses(la, c, path, ss, t, speed, bits, a, col, bl=48.0, width=None, fade_fn=None):
    w = width or max(2, int(5 * S))
    nb = len(bits)
    pp = [P2(*p, c) for p in path]
    for i in range(len(path) - 1):
        s = (ss[i] + ss[i + 1]) / 2
        ph = (s - t * speed) / bl
        if bits[int(math.floor(ph)) % nb]:
            aa = a * (fade_fn(path[i]) if fade_fn else 1.0)
            if aa > 0.02:
                la.line([pp[i], pp[i + 1]], fill=sc3(col, aa), width=w)


def led(la, c, p, col, a, r=5):
    x, y = P2(*p, c)
    rr = r * S
    la.ellipse((x - rr, y - rr, x + rr, y + rr), fill=sc3(col, a))


# ---------------- ESCENARIO 1: calle ----------------
POLES_Z = [-600, 100, 800, 1500, 2200, 2900]
MAIN = []
for _a, _b in zip(POLES_Z[:-1], POLES_Z[1:]):
    _s = sag_path((330, 650, _a), (330, 650, _b), 45, 14)
    MAIN += _s if not MAIN else _s[1:]
DROP = sag_path((312, 600, 800), (-420, 300, 800), 35, 30)
MAIN_R, MAIN_S = resample(MAIN, 14)
DROP_R, DROP_S = resample(DROP, 10)
rs = np.random.RandomState(5)
SKY = [(-3000 + i * 430, 330 + rs.randint(0, 700), 300 + rs.randint(0, 120)) for i in range(14)]
SKY_WIN = [(i, rs.randint(0, 3), rs.randint(0, 6)) for i in range(14) for _ in range(5)]


def draw_street(d, c, t, dim):
    ZF = 6000
    for i in range(10):
        y0 = -300 + i * 240
        poly(d, c, qz(-12000, 12000, y0, y0 + 240, ZF), lc((74, 48, 88), (6, 8, 26), i / 9), dim)
    poly(d, c, [(-1700 + 170 * math.cos(a), 1900 + 170 * math.sin(a), ZF - 10) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)], (236, 236, 214), dim)
    sol = []
    for (x0, h, w) in SKY:
        sol += box_polys(c, x0, x0 + w, 0, h, 4300, 4300 + w, (14, 16, 36), dim)
    for (i, a, b) in SKY_WIN:
        x0, h, w = SKY[i]
        poly(d, c, qz(x0 + 40 + a * 90, x0 + 56 + a * 90, 100 + b * 90 + 20, 100 + b * 90 + 38, 4299), (255, 214, 130), dim) if 100 + b * 90 + 38 < h else None
    draw_solids(d, sol)
    poly(d, c, qy(-12000, 12000, -3000, 6000), (22, 38, 30), dim)
    poly(d, c, qy(-250, 250, -3000, 6000), (38, 40, 48), dim)
    poly(d, c, qy(250, 520, -3000, 6000), (98, 100, 108), dim)
    poly(d, c, qy(-520, -250, -3000, 6000), (98, 100, 108), dim)
    for z in range(-2600, 5000, 420):
        poly(d, c, qy(-8, 8, z, z + 200, 0.5), (240, 220, 140), dim)
    sol = []
    for z in POLES_Z:
        sol += cyl_polys(c, 1, (330, 350, z), 14, 700, (112, 82, 56), 12, dim)
        sol += box_polys(c, 250, 410, 650, 672, z - 9, z + 9, (96, 70, 46), dim)
    sol += box_polys(c, 276, 316, 420, 520, 770, 830, (150, 156, 162), dim)
    # casa
    sol += box_polys(c, -900, -420, 0, 330, 450, 1050, (206, 190, 160), dim)
    for (pts, n_) in (([(-930, 330, 430), (-930, 330, 1070), (-660, 480, 1070), (-660, 480, 430)], (-0.47, 0.88, 0)),
                      ([(-390, 330, 430), (-390, 330, 1070), (-660, 480, 1070), (-660, 480, 430)], (0.47, 0.88, 0))):
        ctr = tuple(sum(p[k] for p in pts) / 4 for k in range(3))
        if vis(c, ctr, n_):
            sol.append((proj(*ctr, c)[2], [P2(*p, c) for p in pts], shade((158, 72, 52), n_, dim)))
    for z_ in (430, 1070):
        pts = [(-910, 330, z_), (-410, 330, z_), (-660, 480, z_)]
        n_ = (0, 0, -1 if z_ == 430 else 1)
        if vis(c, (-660, 380, z_), n_):
            sol.append((proj(-660, 380, z_, c)[2], [P2(*p, c) for p in pts], shade((206, 190, 160), n_, dim)))
    sol += box_polys(c, -426, -420, 0, 220, 700, 790, (92, 60, 40), dim)
    draw_solids(d, sol)
    for (z0, z1) in ((520, 620), (880, 980)):
        poly(d, c, qx(120, 250, z0, z1, -419), (255, 214, 130), dim)
    # cables (negros)
    lw = max(2, int(4 * S))
    d.line([P2(*p, c) for p in MAIN], fill=(16, 16, 20), width=lw)
    d.line([P2(*p, c) for p in DROP], fill=(16, 16, 20), width=lw)


# ---------------- ESCENARIO 2: centro de datos ----------------
CORD_A = crom([(-80, 480, 148), (-80, 480, 100), (-80, 430, 30), (-70, 240, -40), (40, 40, -110), (400, 8, -150), (900, 8, -120), (1500, 8, -100)], 8)
CORD_B = crom([(-20, 480, 148), (-20, 480, 100), (-20, 440, 40), (-10, 250, -20), (120, 40, -60), (500, 8, -40), (1000, 8, -30), (1500, 8, 0)], 8)
CORD_AR, CORD_AS = resample(CORD_A, 8)


def draw_rack(d, c, t, dim):
    poly(d, c, qy(-1600, 1600, -700, 1600), (24, 26, 34), dim)
    for k in range(-8, 9):
        line3(d, c, (k * 200, 0.3, -700), (k * 200, 0.3, 1600), (40, 44, 58))
    for z in range(-600, 1600, 200):
        line3(d, c, (-1600, 0.3, z), (1600, 0.3, z), (40, 44, 58))
    poly(d, c, qz(-1600, 1600, 0, 1200, 1100), (34, 38, 52), dim)
    sol = []
    sol += box_polys(c, -1300, 1300, 990, 1010, 380, 520, (54, 56, 66), dim)
    for (x0, x1) in ((-280, -262), (262, 280)):
        sol += box_polys(c, x0, x1, 0, 900, 150, 650, (22, 22, 26), dim)
    sol += box_polys(c, -280, 280, 900, 918, 150, 650, (22, 22, 26), dim)
    for k in range(9):
        col = (74, 78, 94) if k == 4 else (50, 52, 62)
        sol += box_polys(c, -255, 255, 60 + k * 95, 60 + k * 95 + 80, 150, 190, col, dim)
    for (xa, xb) in ((-780, -480), (480, 780)):
        sol += box_polys(c, xa, xb, 0, 900, 200, 600, (24, 24, 30), dim)
        for k in range(8):
            sol += box_polys(c, xa + 10, xb - 10, 40 + k * 105, 40 + k * 105 + 85, 200, 214, (48, 50, 60), dim)
    draw_solids(d, sol)
    for (px, py) in ((-80, 480), (-20, 480), (40, 480), (100, 480)):
        poly(d, c, qz(px - 12, px + 12, py - 8, py + 8, 149), (8, 8, 10), dim)
    for cp in (CORD_A, CORD_B):
        d.line([P2(*p, c) for p in cp], fill=(236, 196, 40), width=max(3, int(6 * S)), joint="curve")


def rack_leds(la, c, t):
    for k in range(9):
        for i in range(20):
            on = ((i * 7 + k * 13 + int(t * 5)) % 5) < 2
            if on:
                led(la, c, (-235 + i * 23, 60 + k * 95 + 62, 148), (90, 255, 140) if (i + k) % 3 else (255, 190, 70), 0.8, 3.5)
    for (xa, xb) in ((-780, -480), (480, 780)):
        for k in range(8):
            for i in range(8):
                if ((i * 5 + k * 11 + int(t * 4)) % 4) < 1:
                    led(la, c, (xa + 30 + i * 35, 40 + k * 105 + 60, 198), (90, 255, 140), 0.7, 3.5)


# ---------------- ESCENARIO 3 (calle): cable ampliado, TIR y rayos X ----------------
CY, CZ = 480.0, 0.0
LP = 350.0
LAY = [(98, (50, 52, 60), 'jacket'), (66, (255, 160, 70), 'coat'), (48, (150, 200, 232), 'clad'), (22, (210, 240, 255), 'core')]


def prop_overlay(od, c, xo, ca_clad=95):
    """cilindros translúcidos del cable ampliado"""
    sides = []
    caps = []
    for (r, col, name) in LAY:
        if name in ('jacket', 'coat'):
            al = int(150 * xo)
        elif name == 'clad':
            al = ca_clad
        else:
            al = 190
        if al <= 2:
            continue
        for dep, pts, cc in cyl_polys(c, 0, (0, CY, CZ), r, 2 * LP, col, 24, 1.0, caps=False):
            sides.append((dep, pts, (*cc, al)))
        if vis(c, (-LP, CY, CZ), (-1, 0, 0)):
            pts = [P2(-LP, CY + r * math.cos(2 * math.pi * i / 28), CZ + r * math.sin(2 * math.pi * i / 28), c) for i in range(28)]
            caps.append((r, pts, (*tuple(int(v * 0.9) for v in col), min(255, al + 40))))
    sides.sort(key=lambda q: -q[0])
    for dep, pts, col in sides:
        od.polygon(pts, fill=col)
    caps.sort(key=lambda q: -q[0])
    for r, pts, col in caps:
        od.polygon(pts, fill=col)


def tri(u):
    u = u % 1.0
    return 4 * abs(u - 0.5) - 1


def prop_glow(la, c, t, a, xo):
    lw = max(2, int(4 * S))
    # zigzag de la luz dentro del núcleo (reflexión total interna)
    pts = []
    for i in range(0, 91):
        x = -LP + i * (2 * LP / 90)
        pts.append((x, CY + 17 * tri(x / 130.0), CZ))
    pp = [P2(*p, c) for p in pts]
    la.line(pp, fill=sc3(CYAN, 0.55 * a), width=lw)
    u = (t * 0.28) % 1.0
    for j in range(3):
        uu = (u + j / 3.0) % 1.0
        x = -LP + uu * 2 * LP
        y = CY + 17 * tri(x / 130.0)
        led(la, c, (x, y, CZ), (255, 255, 255), a, 8)
    # destellos en los rebotes
    for k in range(-4, 5):
        x = k * 65.0 + 65.0 * 0.0
        yk = CY + 17 * tri(x / 130.0)
        if abs(abs(tri(x / 130.0)) - 1) < 1e-6:
            f = 0.5 + 0.5 * math.sin(2 * math.pi * (t * 1.4 - k * 0.12))
            led(la, c, (x, yk, CZ), (170, 235, 255), a * f, 6 + 6 * f)
    # núcleo brillante
    ln = [P2(x, CY, CZ, c) for x in (-LP, LP)]
    la.line(ln, fill=sc3(BLUE, 0.35 * a), width=max(3, int(10 * S)))
    # hebras de refuerzo (rayos X)
    if xo > 0:
        for k in range(14):
            an = 2 * math.pi * k / 14
            ya, za = CY + 82 * math.cos(an), CZ + 82 * math.sin(an)
            la.line([P2(-LP, ya, za, c), P2(LP, ya, za, c)], fill=sc3((240, 205, 70), 0.75 * xo), width=max(1, int(3 * S)))
        for r_ in (98, 66, 48, 22):
            ring = [P2(-LP, CY + r_ * math.cos(2 * math.pi * i / 40), CZ + r_ * math.sin(2 * math.pi * i / 40), c) for i in range(41)]
            la.line(ring, fill=sc3((90, 200, 255), 0.8 * xo), width=max(1, int(3 * S)))
        xs = -LP + ((t * 0.3) % 1.0) * 2 * LP
        sq = [P2(xs, CY + 112 * math.cos(2 * math.pi * i / 40), CZ + 112 * math.sin(2 * math.pi * i / 40), c) for i in range(41)]
        la.line(sq, fill=sc3(BLUE, 0.9 * xo), width=max(2, int(4 * S)))


# ---------------- ESCENARIO 4: fondo del mar ----------------
SEA_X = [-1700 + i * 50 for i in range(69)]
SEA_CABLE = [(x, 8, 40 * math.sin(x / 190.0)) for x in SEA_X]
SEA_R, SEA_S = resample(SEA_CABLE, 12)
REPEATERS = (-420, 780)
rs2 = np.random.RandomState(9)
ROCKS = [(rs2.uniform(-1500, 1500), rs2.uniform(120, 700) * rs2.choice([-1, 1]), rs2.uniform(30, 90)) for _ in range(12)]
TINT = (0.55, 0.78, 0.95)


def tint(col, k=1.0):
    return (int(col[0] * TINT[0] * k), int(col[1] * TINT[1] * k), int(col[2] * TINT[2] * k))


def draw_sea(d, c, t, dim):
    for i in range(12):
        y0 = -300 + i * 330
        poly(d, c, qz(-12000, 12000, y0, y0 + 330, 3500), lc((4, 26, 50), (22, 100, 146), 1 - i / 11), dim)
    for i in range(8):
        z0 = -1500 + i * 600
        k = 1.0 - i * 0.09
        poly(d, c, qy(-4000, 4000, z0, z0 + 600), tint((196, 172, 124), k), dim)
    sol = []
    for (x, z, s) in ROCKS:
        sol += box_polys(c, x - s, x + s, 0, s * 1.2, z - s, z + s, tint((110, 112, 120)), dim)
    for rx in REPEATERS:
        sol += cyl_polys(c, 0, (rx, 52, 30 * math.sin(rx / 190.0)), 46, 220, (176, 182, 194), 20, dim)
        for off in (-90, 90):
            sol += cyl_polys(c, 0, (rx + off, 52, 30 * math.sin(rx / 190.0)), 50, 26, (30, 66, 120), 20, dim)
    draw_solids(d, sol)
    d.line([P2(*p, c) for p in SEA_CABLE], fill=(26, 28, 34), width=max(3, int(9 * S)), joint="curve")


def sea_fade(p):
    x = p[0]
    prev, nxt = -2200.0, REPEATERS[0]
    for rx in REPEATERS:
        if x >= rx:
            prev = rx
    nxt = 2200.0
    for rx in REPEATERS:
        if rx > x:
            nxt = rx
            break
    if prev < -2000:
        return 1.0 - 0.6 * clamp((x + 1700) / (nxt + 1700))
    return 1.0 - 0.6 * clamp((x - prev) / (nxt - prev))


# ---------------- ESCENARIO 5: casa ----------------
FIB_IN = crom([(-590, 700, 790), (-590, 560, 788), (-590, 420, 776), (-590, 400, 770)], 8)
FIB_R, FIB_S = resample(FIB_IN, 8)
ETH = crom([(-590, 300, 770), (-590, 240, 772), (-575, 190, 750), (-560, 176, 735)], 8)
ETH_R, ETH_S = resample(ETH, 6)
T_ONT, T_ROUTER, T_TV = 54.0, 56.0, 58.2


def draw_home(d, c, t, dim):
    poly(d, c, qz(-2400, 2400, 0, 1600, 800), (84, 86, 112), dim)
    poly(d, c, qy(-2400, 2400, -900, 800), (150, 104, 70), dim)
    for k in range(-12, 13):
        line3(d, c, (k * 120, 0.3, -900), (k * 120, 0.3, 800), (128, 86, 56))
    poly(d, c, qx(0, 800, -900, 800, -900), (70, 72, 94), dim)
    sol = []
    # mueble de TV y TV
    sol += box_polys(c, -250, 600, 0, 170, 640, 780, (96, 66, 44), dim)
    sol += box_polys(c, -150, 500, 215, 600, 730, 750, (18, 18, 22), dim)
    # mesa lateral y router
    sol += box_polys(c, -680, -440, 0, 150, 650, 780, (96, 66, 44), dim)
    sol += box_polys(c, -660, -460, 150, 176, 690, 760, (20, 20, 24), dim)
    for ax in (-650, -470):
        sol += cyl_polys(c, 1, (ax, 220, 725), 5, 90, (24, 24, 28), 8, dim)
    # ONT en la pared
    sol += box_polys(c, -650, -530, 300, 400, 770, 800, (236, 238, 244), dim, 0.6)
    # sofá
    sol += box_polys(c, -300, 300, 0, 100, -330, -110, (36, 96, 108), dim)
    sol += box_polys(c, -300, 300, 100, 240, -130, -110, (30, 84, 96), dim)
    sol += box_polys(c, -340, -300, 0, 170, -330, -110, (30, 84, 96), dim)
    sol += box_polys(c, 300, 340, 0, 170, -330, -110, (30, 84, 96), dim)
    # lámpara
    sol += cyl_polys(c, 1, (800, 300, 650), 8, 600, (60, 60, 66), 8, dim)
    sol += cyl_polys(c, 1, (800, 640, 650), 70, 90, (240, 220, 170), 14, dim, caps=True)
    draw_solids(d, sol)
    for (pp_, col) in ((FIB_IN, (236, 196, 40)), (ETH, (60, 100, 190))):
        d.line([P2(*p, c) for p in pp_], fill=col, width=max(3, int(6 * S)), joint="curve")
    # pantalla de la TV
    on = ease(seg(t, T_TV, T_TV + 0.8))
    for i in range(10):
        x0 = -138 + i * 62.6
        col = lc((26, 74, 168), (150, 52, 172), i / 9)
        poly(d, c, qz(x0, x0 + 63, 242, 588, 729.5), tuple(int(v * on) for v in col) if on > 0 else (6, 6, 10), dim)
    if on <= 0:
        poly(d, c, qz(-138, 488, 242, 588, 729.4), (6, 6, 10), dim)
    else:
        poly(d, c, [(130, 440, 729), (130, 390, 729), (190, 415, 729)], (255, 255, 255), dim * on)
        poly(d, c, qz(-110, 90, 262, 268, 729), (240, 240, 255), dim * on)


# ---------------- render ----------------
def prev_env(t):
    if t < CUTS[0]:
        return 'street'
    if t < CUTS[1]:
        return 'rack'
    if t < CUTS[2]:
        return 'street2'
    if t < CUTS[3]:
        return 'sea'
    return 'home'


BITS = [1, 1, 0, 1, 0, 0, 1, 1, 1, 0]
BITS2 = [1, 0, 1, 1, 0, 1, 0, 0]


def render(t):
    c = cam_at(t)
    env = prev_env(t)
    xr = ease(seg(t, 36.0, 37.0)) * (1 - ease(seg(t, 41.2, 41.8))) if env == 'street2' else 0.0
    dim_env = 1 - 0.55 * xr
    if env == 'street2':
        dim_env *= 1 - 0.5 * ease(seg(t, 22.7, 23.4))
    if env == 'sea' and t > 46.3:
        dim_env = 1 - 0.35 * ease(seg(t, 46.3, 47.2))
    base = Image.new("RGB", (W, H), (8, 8, 14))
    bd = ImageDraw.Draw(base)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)

    if env in ('street', 'street2'):
        draw_street(bd, c, t, dim_env)
        for (x, y, ph, r) in STARS[:40]:
            a = 0.25 + 0.25 * math.sin(t * 1.4 + ph)
            px, py = P(x, y * 0.5)
            rr = r * S * 0.6
            la.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3((220, 210, 255), a))
        # resplandor de las ventanas de la casa
        for (z0, z1) in ((520, 620), (880, 980)):
            la.polygon([P2(*p, c) for p in qx(120, 250, z0, z1, -419)], fill=sc3((70, 50, 22), 1.0 - 0.6 * xr))
    elif env == 'rack':
        draw_rack(bd, c, t, 1.0)
    elif env == 'sea':
        draw_sea(bd, c, t, dim_env)
    else:
        draw_home(bd, c, t, 1.0)

    # ---------- efectos por escena ----------
    if env == 'street':
        a = ease(seg(t, 0.5, 1.3))
        pulses(la, c, MAIN_R, MAIN_S, t, 520, BITS, a * 0.95, CYAN, 46.0)
        pulses(la, c, DROP_R, DROP_S, t, 420, BITS2, a * ease(seg(t, 3.0, 4.0)), (150, 255, 220), 40.0)
        if t > 9.6:
            g = ease(seg(t, 10.0, 11.0))
            pulses(la, c, DROP_R, DROP_S, t, 560, BITS2, g, (255, 255, 255), 36.0, max(3, int(7 * S)))
    elif env == 'rack':
        rack_leds(la, c, t)
        a = ease(seg(t, 14.0, 15.0))
        pm = 0.6 + 0.4 * math.sin(2 * math.pi * 3 * t)
        led(la, c, (-80, 480, 147), (255, 80, 80), a * pm, 12)
        pulses(la, c, CORD_AR, CORD_AS, t, 360, BITS2, ease(seg(t, 16.4, 17.2)), (255, 90, 90), 40.0, max(3, int(6 * S)))
        pulses(la, c, CORD_AR, CORD_AS, t, 360, BITS2, ease(seg(t, 18.0, 18.8)) * 0.6, (255, 255, 255), 40.0, max(2, int(3 * S)))
    elif env == 'street2':
        a = ease(seg(t, 22.9, 23.7)) * (1 - ease(seg(t, 41.4, 41.9)))
        xo = ease(seg(t, 36.4, 37.4)) * (1 - ease(seg(t, 41.4, 41.9)))
        cl = 95 if t < 36.4 else 95
        prop_overlay(od, c, xo, cl)
        prop_glow(la, c, t, a, xo)
    elif env == 'sea':
        a = ease(seg(t, 42.2, 43.0))
        for k in range(5):
            xx = -1400 + 500 * k + 60 * math.sin(t * 0.3 + k)
            quad = [P2(xx, 1600, 700, c), P2(xx + 80, 1600, 700, c), P2(xx + 360, 0, 500, c), P2(xx + 300, 0, 500, c)]
            la.polygon(quad, fill=sc3((14, 40, 54), 0.35))
        for k in range(40):
            px = -1500 + (k * 173 + t * 14) % 3000
            py = 40 + (k * 97 + t * 20) % 600
            pz = -300 + (k * 61) % 900
            led(la, c, (px, py, pz), (150, 210, 230), 0.4, 2.5)
        pulses(la, c, SEA_R, SEA_S, t, 700, BITS, a, CYAN, 60.0, max(2, int(5 * S)), sea_fade)
        # amplificador: destello al paso
        for rx in REPEATERS:
            pm = 0.5 + 0.5 * math.sin(2 * math.pi * 1.2 * t)
            led(la, c, (rx, 100, 30 * math.sin(rx / 190.0)), (140, 255, 200), a * pm, 10)
        # lupa: cable ampliado con colores
        if t > 46.3:
            b = ease(seg(t, 46.4, 47.4))
            CC = {'y': 120.0}
            od_cl = int(95 * b)
            prop_overlay_sea(od, la, c, t, b)
    else:
        a1 = ease(seg(t, 52.8, 53.6))
        pulses(la, c, FIB_R, FIB_S, t, -260, BITS2, a1, CYAN, 34.0, max(3, int(6 * S)))
        # LEDs del ONT
        for i in range(4):
            on = (t > T_ONT) and ((i == 0) or (t > T_ONT + 0.3 * i))
            led(la, c, (-640 + 22 * (i + 1), 322, 769), (90, 255, 140) if on else (40, 60, 44), 0.95 if on else 0.3, 4.5)
        pulses(la, c, ETH_R, ETH_S, t, -200, BITS2, ease(seg(t, T_ONT + 0.4, T_ONT + 1.2)), (255, 170, 80), 24.0, max(3, int(6 * S)))
        # wifi
        if t > T_ROUTER:
            wa = ease(seg(t, T_ROUTER, T_ROUTER + 0.8)) * (1 - 0.0)
            src = np.array([-560.0, 190.0, 725.0])
            dst = np.array([180.0, 400.0, 725.0])
            dd = dst - src
            dd /= np.linalg.norm(dd)
            e1 = np.cross(dd, np.array([0.0, 1.0, 0.0]))
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(dd, e1)
            for j in range(5):
                s = (t * 0.35 + j / 5.0) % 1.0
                ctr_ = src + s * (dst - src)
                rad = 20 + 190 * s
                pts = [P2(*(ctr_ + rad * (math.cos(2 * math.pi * i / 40) * e1 + math.sin(2 * math.pi * i / 40) * e2)), c) for i in range(41)]
                la.line(pts, fill=sc3(VIOLET, wa * math.sin(math.pi * s) * 0.9), width=max(2, int(3 * S)))
            led(la, c, (-560, 150, 715), (90, 255, 140), 0.9, 4)
        if t > T_TV:
            ta = ease(seg(t, T_TV, T_TV + 0.8))
            la.polygon([P2(*p, c) for p in qz(-138, 488, 242, 588, 729.4)], fill=sc3((20, 24, 50), ta))
        la.polygon([P2(*p, c) for p in [(780, 700, 650), (820, 700, 650), (840, 640, 650), (760, 640, 650)]], fill=sc3((90, 74, 40), 1.0))

    arrA = np.asarray(base, dtype=np.float32)
    imgA = Image.fromarray(np.clip(arrA, 0, 255).astype(np.uint8)).convert("RGBA")
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")
    arr = np.asarray(imgB, dtype=np.float32) + np.asarray(LA, dtype=np.float32) + 1.5 * glow_of(LA, 4)

    f = 1.0
    for cut in CUTS:
        f = min(f, clamp(abs(t - cut) / 0.28))
    arr = arr * f
    arr = arr * (1 - 0.92 * seg(t, T_OUT, T_OUT + 0.8))

    L2 = Image.new("RGB", (W, H), (0, 0, 0))
    l2 = ImageDraw.Draw(L2)
    anim.draw_caption(l2, t)
    hud(l2, c, t, env)
    arr = arr + np.asarray(L2, dtype=np.float32) + 1.2 * glow_of(L2, 3)
    arr = arr * (seg(t, 0.0, 0.4) * (1 - seg(t, DUR - 0.5, DUR)))
    return np.clip(arr, 0, 255).astype(np.uint8)


LANE_COL = [(255, 90, 90), (110, 255, 140), (110, 160, 255), (255, 225, 100)]


def prop_overlay_sea(od, la, c, t, b):
    global CY, CZ
    old = (CY, CZ)
    CY, CZ = 200.0, 0.0
    prop_overlay(od, c, 0.0, int(85 * b))
    for k, col in enumerate(LANE_COL):
        yy = CY + (-15 + 10 * k)
        pts = [(-LP + i * (2 * LP / 60), yy, CZ) for i in range(61)]
        ss = [i * (2 * LP / 60) for i in range(61)]
        pulses(la, c, pts, ss, t + k * 0.13, 320, [1, 1, 0, 1, 0, 1, 1, 0, 0][k % 3:] + [1, 0], b, col, 40.0, max(3, int(6 * S)))
    la.line([P2(-LP, CY, CZ, c), P2(LP, CY, CZ, c)], fill=sc3((60, 90, 140), 0.25 * b), width=max(3, int(14 * S)))
    CY, CZ = old


def hud(l2, c, t, env):
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
        l2.rounded_rectangle((*P(540 - w / 2, y - 42), *P(540 + w / 2, y + 42)), radius=int(42 * S), outline=sc3(col, a), width=max(2, int(3 * S)))
        l2.text(P(540, y), txt, font=F(B, size), fill=sc3((225, 235, 255), a), anchor="mm")

    def win(a, b, e=0.5):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    for cut in CUTS:
        if abs(t - cut) < 0.3:
            return
    # S1-S2
    a = win(1.0, 4.4)
    if a > 0:
        tgt = proj(*DROP[15], c)[:2]
        label("FIBRA ÓPTICA", tgt, (1030, min(1450, tgt[1] + 380)), "rm", a)
    pill("0.125 mm DE GROSOR", 1560, win(5.6, 8.8), VIOLET, 640)
    pill("SOLO LUZ, SIN ELECTRICIDAD", 1560, win(10.2, 13.0), CYAN, 760, 34)
    # S3
    a = win(14.0, 17.2)
    if a > 0:
        tgt = proj(-80, 480, 148, c)[:2]
        label("TRANSMISOR LÁSER", tgt, (1030, max(460, tgt[1] - 330)), "rm", a)
    a = win(16.8, 22.2)
    if a > 0:
        bits = "1 0 1 1 0 0 1 0 1 1 0 1"
        off = int(t * 6) % 12
        txt = bits[off:] + " " + bits[:off]
        l2.rounded_rectangle((*P(150, 420), *P(930, 540)), radius=int(24 * S), outline=sc3((100, 90, 190), a * 0.9), width=max(1, int(2 * S)))
        l2.text(P(540, 480), txt[:23], font=F(M, 58), fill=sc3((235, 225, 255), a), anchor="mm")
    pill("HASTA 10,000,000,000 / SEG", 1560, win(18.6, 22.4), BLUE, 800, 34)
    # S4
    a = win(26.0, 33.0)
    if a > 0 and env == 'street2':
        label("NÚCLEO", proj(150, CY, CZ, c)[:2], (60, 560), "lm", a, (190, 240, 255))
    a = win(28.3, 33.4)
    if a > 0 and env == 'street2':
        label("REVESTIMIENTO", proj(-250, CY + 40, CZ, c)[:2], (1030, 1480), "rm", a)
    pill("REFLEXIÓN TOTAL INTERNA", 1580, win(33.8, 36.8), CYAN, 760, 34)
    # S5
    if 36.2 <= t < 41.8 and env == 'street2':
        specs = [(37.4, "CUBIERTA PROTECTORA", (-200, CY + 98, CZ), (1030, 520), "rm"),
                 (38.4, "HEBRAS DE REFUERZO", (150, CY + 82, CZ), (60, 1520), "lm"),
                 (39.4, "RECUBRIMIENTO", (-250, CY - 66, CZ), (1030, 1500), "rm"),
                 (40.2, "NÚCLEO DE VIDRIO", (250, CY, CZ), (60, 600), "lm")]
        for (ta, txt, p3, tp, anc) in specs:
            a = ease(seg(t, ta, ta + 0.45)) * (1 - ease(seg(t, 41.2, 41.8)))
            if a > 0:
                label(txt, proj(*p3, c)[:2], tp, anc, a)
    # S6
    pill("≈ 200,000 km/s EN EL VIDRIO", 1560, win(42.6, 46.2), BLUE, 800, 32)
    a = win(43.6, 46.4)
    if a > 0:
        label("AMPLIFICADOR", proj(REPEATERS[1], 100, 30 * math.sin(REPEATERS[1] / 190.0), c)[:2], (1030, 480), "rm", a)
    pill("CADA COLOR = UN CANAL", 1560, win(47.0, 52.4), VIOLET, 700, 34)
    # S7
    a = win(53.2, 56.4)
    if a > 0 and env == 'home':
        label("CONVERTIDOR (ONT)", proj(-590, 360, 769, c)[:2], (1030, 480), "rm", a)
    a = win(55.6, 58.4)
    if a > 0 and env == 'home':
        label("ROUTER", proj(-560, 176, 735, c)[:2], (60, 1500), "lm", a)
    a = win(58.4, 63.8)
    if a > 0 and env == 'home':
        label("TU VIDEO", proj(175, 415, 729, c)[:2], (60, 480), "lm", a, (255, 255, 255))
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
        os.makedirs("/home/claude/prevfo", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render(float(ts))).save(f"/home/claude/prevfo/t_{ts}.png")
        print("ok")
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(a, b):
            pr.stdin.write(render(f / FPS).tobytes())
        pr.stdin.close()
        pr.wait()
        print("ok", a, b, "de", NF)
