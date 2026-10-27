import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of,
                  VIOLET, BLUE, CYAN, ORANGE, COPPER)

FPS = 24
DUR = 49.8
NF = int(DUR * FPS)
FOC = 1200.0

PHR = [
    (0.4, 4.4, "¿Cómo puede un audífono apagar el ruido... usando más ruido?", {9}),
    (5.0, 7.8, "Todo sonido es una onda de presión", {4}),
    (7.9, 10.6, "que viaja por el aire hasta tu oído.", {4}),
    (11.2, 14.0, "Los micrófonos exteriores captan ese ruido,", {1}),
    (14.1, 18.0, "y un chip calcula, en menos de un milisegundo, su onda contraria.", {2}),
    (18.6, 21.2, "Es la misma onda, pero invertida.", {5}),
    (21.3, 25.0, "Cuando se encuentran, una empuja y la otra jala, y se cancelan.", {11}),
    (25.8, 28.6, "Por dentro hay micrófonos, un procesador", {3}),
    (28.7, 32.6, "y una bocina que reproduce tu música junto con el anti-ruido.", {2}),
    (33.3, 36.2, "Funciona mejor con zumbidos constantes,", {3}),
    (36.3, 38.8, "como el motor de un avión.", {5}),
    (39.2, 42.4, "Las voces y los golpes son más difíciles de cancelar.", {1}),
    (43.0, 46.4, "Tus audífonos no bloquean el ruido: lo cancelan con más ruido.", {7}),
    (47.0, 49.0, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)

T6A, T6B = 33.2, 42.9      # escena de comparación (pantalla 2D)
T_OUT = 46.5

# colores de objetos "reales"
HP_BLACK = (28, 29, 35)
HP_PAD = (20, 20, 24)
HP_SILVER = (196, 200, 212)
WOOD = (150, 98, 58)
LIGHT = np.array([-0.55, 0.75, -0.35])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

# ---------------- cámara ----------------
KEYS = [
    (0.0, 1300, 14, -24, 1110, 0, 170, 0),
    (5.0, 1300, 14, -14, 1110, -40, 170, 0),
    (5.7, 1250, 15, 6, 1080, -260, 140, 0),
    (11.0, 1250, 15, 10, 1080, -250, 140, 0),
    (11.9, 800, 12, -38, 1100, -150, 110, 0),
    (18.3, 820, 12, -34, 1100, -150, 110, 0),
    (19.1, 1000, 8, 4, 1100, 0, 300, -60),
    (25.4, 1000, 8, 8, 1100, 0, 300, -60),
    (26.3, 430, 12, -78, 1000, -160, 105, 0),
    (32.8, 470, 20, -48, 1000, -160, 105, 0),
    (43.2, 1250, 16, -24, 1110, 0, 170, 0),
    (49.8, 1350, 16, -8, 1110, 0, 170, 0),
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


def proj(x, y, z, c):
    x -= c['f'][0]
    y -= c['f'][1]
    z -= c['f'][2]
    x1 = x * c['ca'] + z * c['sa']
    z1 = -x * c['sa'] + z * c['ca']
    y2 = y * c['cp'] + z1 * c['sp']
    z2 = z1 * c['cp'] - y * c['sp']
    dep = z2 + c['D']
    k = FOC / dep
    return (540 + x1 * k, c['cy'] - y2 * k, dep)


def P2(x, y, z, c):
    sx, sy, _ = proj(x, y, z, c)
    return (sx * S, sy * S)


def vis(c, ctr, n):
    p = c['pos']
    return n[0] * (p[0] - ctr[0]) + n[1] * (p[1] - ctr[1]) + n[2] * (p[2] - ctr[2]) > 0


def shade(col, n, dim=1.0, amb=0.40, dif=0.85):
    d = max(0.0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])
    k = (amb + dif * d) * dim
    return (min(255, int(col[0] * k)), min(255, int(col[1] * k)), min(255, int(col[2] * k)))


def box_polys(c, x0, x1, y0, y1, z0, z1, col, dim=1.0, amb=0.40):
    faces = [((0, 1, 0), [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]),
             ((0, 0, -1), [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]),
             ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
             ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
             ((1, 0, 0), [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)])]
    out = []
    for n, pts in faces:
        ctr = tuple(sum(p[i] for p in pts) / 4 for i in range(3))
        if vis(c, ctr, n):
            out.append((proj(*ctr, c)[2], [P2(*p, c) for p in pts], shade(col, n, dim, amb)))
    return out


def cyl_polys(c, axis, ctr, r, h, col, n=24, dim=1.0, caps=True):
    a = axis
    u = (a + 1) % 3
    v = (a + 2) % 3
    out = []

    def pt(side, th):
        p = [0.0, 0.0, 0.0]
        p[a] = ctr[a] + side * h / 2
        p[u] = ctr[u] + r * math.cos(th)
        p[v] = ctr[v] + r * math.sin(th)
        return tuple(p)

    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        tm = (t0 + t1) / 2
        nv = [0.0, 0.0, 0.0]
        nv[u] = math.cos(tm)
        nv[v] = math.sin(tm)
        pts = [pt(-1, t0), pt(-1, t1), pt(1, t1), pt(1, t0)]
        cc = tuple(sum(p[k] for p in pts) / 4 for k in range(3))
        if vis(c, cc, nv):
            out.append((proj(*cc, c)[2], [P2(*p, c) for p in pts], shade(col, nv, dim)))
    if caps:
        for side in (-1, 1):
            nv = [0.0, 0.0, 0.0]
            nv[a] = side
            cc = list(ctr)
            cc[a] = ctr[a] + side * h / 2
            if vis(c, tuple(cc), nv):
                pts = [pt(side, 2 * math.pi * i / n) for i in range(n)]
                out.append((proj(*cc, c)[2] - 0.5, [P2(*p, c) for p in pts], shade(col, nv, dim)))
    return out


# ---------------- entorno: cuarto ----------------
BUILDINGS = [(-540, -482, 170), (-482, -420, 255), (-420, -352, 150), (-352, -288, 300), (-288, -222, 205), (-222, -160, 250)]
WIN = (-560, -160, 170, 560)  # x0,x1,y0,y1 en el plano z=420
WZ = 420


def wall_quad(x0, x1, y0, y1):
    return [(x0, y0, WZ), (x1, y0, WZ), (x1, y1, WZ), (x0, y1, WZ)]


def draw_room(d, c, t, dim):
    def poly(pts3, col):
        d.polygon([P2(*p, c) for p in pts3], fill=tuple(max(0, min(255, int(v * dim))) for v in col))

    poly([(-1800, -420, -1000), (1800, -420, -1000), (1800, -420, 1000), (-1800, -420, 1000)], (14, 14, 20))
    # pared con degradado
    n = 12
    for i in range(n):
        y0 = -420 + i * 1500 / n
        y1 = y0 + 1500 / n
        g = 1 - abs(((y0 + y1) / 2 - 300) / 900) * 0.55
        poly(wall_quad(-1800, 1800, y0, y1), (int(40 * g), int(48 * g), int(78 * g)))
    # ventana
    x0, x1, y0, y1 = WIN
    poly(wall_quad(x0 - 16, x1 + 16, y0 - 16, y1 + 16), (206, 206, 212))
    ns = 9
    for i in range(ns):
        ya = y0 + (y1 - y0) * i / ns
        yb = y0 + (y1 - y0) * (i + 1) / ns
        f = i / (ns - 1)
        poly(wall_quad(x0, x1, ya, yb), lc((78, 52, 84), (12, 16, 40), f))
    for (bx0, bx1, h) in BUILDINGS:
        poly(wall_quad(bx0, bx1, 205, 205 + h), (11, 13, 28))
        ry = 225
        while ry < 205 + h - 20:
            cx = bx0 + 10
            while cx < bx1 - 14:
                if ((int(cx) * 7 + int(ry) * 13) % 5) < 2:
                    poly(wall_quad(cx, cx + 9, ry, ry + 13), (255, 214, 120))
                cx += 21
            ry += 32
    poly(wall_quad(x0, x1, y0, 205), (30, 30, 38))
    for i in range(4):
        xc = x0 + ((t * 70 + i * 105) % (x1 - x0 - 40))
        poly(wall_quad(xc, xc + 34, 178, 192), (22, 22, 30))
        poly(wall_quad(xc + 29, xc + 35, 182, 188), (255, 236, 160))
        poly(wall_quad(xc - 1, xc + 4, 182, 188), (255, 60, 50))
    # travesaños
    poly(wall_quad(x0 - 4, x1 + 4, (y0 + y1) / 2 - 4, (y0 + y1) / 2 + 4), (206, 206, 212))
    poly(wall_quad((x0 + x1) / 2 - 4, (x0 + x1) / 2 + 4, y0, y1), (206, 206, 212))

    # escritorio
    polys = []
    for lx in (-740, 690):
        for lz in (-330, 250):
            polys += box_polys(c, lx, lx + 50, -420, -40, lz, lz + 50, (96, 62, 36), dim)
    polys.sort(key=lambda q: -q[0])
    for dep, pts, col in polys:
        d.polygon(pts, fill=col)
    polys = box_polys(c, -800, 800, -40, 0, -380, 300, WOOD, dim, 0.55)
    for dep, pts, col in polys:
        d.polygon(pts, fill=col)
    # objetos sobre el escritorio
    objs = box_polys(c, -470, -300, 0, 14, -210, -80, (60, 92, 130), dim)
    objs += cyl_polys(c, 1, (390, 35, -110), 34, 70, (196, 62, 56), 24, dim)
    objs.sort(key=lambda q: -q[0])
    for dep, pts, col in objs:
        d.polygon(pts, fill=col)


# ---------------- audífonos ----------------
def hp_polys(c, dim=1.0):
    out = []
    for sgn in (-1, 1):
        cx = 150 * sgn
        out += cyl_polys(c, 0, (cx, 95, 0), 88, 52, HP_BLACK, 28, dim)
        out += cyl_polys(c, 0, (cx - sgn * 37, 95, 0), 80, 22, HP_PAD, 28, dim)
        out += box_polys(c, cx - 9, cx + 9, 176, 214, -13, 13, HP_SILVER, dim, 0.5)
    N = 30

    def Q(a, r, z):
        return (r * math.cos(a), 183 + r * math.sin(a), z)

    for i in range(N):
        a0 = math.pi * (1 - i / N)
        a1 = math.pi * (1 - (i + 1) / N)
        am = (a0 + a1) / 2
        rad = (math.cos(am), math.sin(am), 0.0)
        col = (44, 45, 54) if 9 <= i <= 20 else (34, 35, 42)
        faces = [([Q(a0, 160, -15), Q(a1, 160, -15), Q(a1, 160, 15), Q(a0, 160, 15)], rad),
                 ([Q(a0, 150, -15), Q(a1, 150, -15), Q(a1, 160, -15), Q(a0, 160, -15)], (0, 0, -1)),
                 ([Q(a0, 150, -15), Q(a1, 150, -15), Q(a1, 150, 15), Q(a0, 150, 15)], (-rad[0], -rad[1], 0))]
        for pts, nv in faces:
            cc = tuple(sum(p[k] for p in pts) / 4 for k in range(3))
            if vis(c, cc, nv):
                out.append((proj(*cc, c)[2], [P2(*p, c) for p in pts], shade(col, nv, dim)))
    out.sort(key=lambda q: -q[0])
    return out


def draw_internals(bd, c, t):
    def PX(x, y, z):
        return P2(x, y, z, c)

    def circ(x, cy, cz, r, n=30):
        return [PX(x, cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]

    def rect(x, y0, y1, z0, z1):
        return [PX(x, y0, z0), PX(x, y0, z1), PX(x, y1, z1), PX(x, y1, z0)]

    lwd = max(1, int(2 * S))
    # bocina (driver)
    bd.polygon(circ(-132, 95, 0, 68), fill=(112, 114, 128), outline=(172, 174, 190))
    bd.polygon(circ(-132, 95, 0, 50), fill=(44, 44, 52))
    cc = circ(-132, 95, 0, 37)
    bd.line(cc + [cc[0]], fill=COPPER, width=max(3, int(8 * S)))
    bd.polygon(circ(-132, 95, 0, 22), fill=(76, 78, 90), outline=(120, 122, 136))
    # batería
    bd.polygon(rect(-158, 52, 124, 22, 62), fill=(62, 108, 182), outline=(36, 64, 126))
    bd.polygon(rect(-158, 124, 131, 36, 48), fill=(190, 192, 202))
    bd.line([PX(-158, 62, 42), PX(-158, 114, 42)], fill=(150, 190, 240), width=lwd)
    # placa
    bd.polygon(rect(-166, 70, 128, -62, 14), fill=(30, 134, 74), outline=(16, 86, 46))
    for (ya, za, yb, zb) in ((78, -56, 78, 6), (122, -56, 96, -56), (88, 8, 120, 8)):
        bd.line([PX(-166, ya, za), PX(-166, yb, zb)], fill=(92, 190, 130), width=lwd)
    chip = rect(-166, 82, 112, -48, -16)
    bd.polygon(chip, fill=(20, 22, 26), outline=(210, 170, 70))
    for k in range(5):
        zz = -46 + k * 6.5
        bd.line([PX(-166, 79, zz), PX(-166, 82, zz)], fill=(220, 180, 80), width=lwd)
        bd.line([PX(-166, 112, zz), PX(-166, 115, zz)], fill=(220, 180, 80), width=lwd)
    for (yy_, zz_) in ((120, -52), (120, -40), (76, 2)):
        bd.polygon(rect(-166, yy_, yy_ + 6, zz_, zz_ + 6), fill=(240, 190, 70))
    # micrófono interior
    bd.polygon(circ(-124, 122, 38, 7, 16), fill=(220, 180, 80), outline=(120, 90, 30))
    # cables
    wires = [[(-176, 148, -8), (-171, 130, -20), (-166, 114, -30)],
             [(-166, 84, -30), (-150, 78, -12), (-132, 72, 0)],
             [(-124, 122, 38), (-150, 112, 10), (-166, 98, -20)]]
    for w in wires:
        bd.line([PX(*p) for p in w], fill=(225, 140, 95), width=lwd)
    return wires


def poly_pts(wire, u):
    n = len(wire) - 1
    s = clamp(u) * n
    i = min(n - 1, int(s))
    f = s - i
    a, b = wire[i], wire[i + 1]
    return tuple(lerp(a[k], b[k], f) for k in range(3))


# ---------------- ondas / efectos ----------------
SRC = (-350.0, 360.0, 420.0)
DST = (0.0, 110.0, 0.0)


def ring_basis():
    d = np.array(DST) - np.array(SRC)
    d = d / np.linalg.norm(d)
    e1 = np.cross(d, np.array([0.0, 1.0, 0.0]))
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    return d, e1, e2


RD, RE1, RE2 = ring_basis()


def draw_rings(la, c, t, amp, cancel):
    lw = max(2, int(3 * S))
    for j in range(5):
        s = (t * 0.22 + j / 5.0) % 1.0
        ctr = np.array(SRC) + s * (np.array(DST) - np.array(SRC))
        rad = 30 + 330 * s
        a = amp * math.sin(math.pi * min(1.0, s * 1.05)) ** 0.7
        if cancel:
            a *= clamp((0.80 - s) / 0.16)
        else:
            a *= clamp((0.97 - s) / 0.07)
        if a <= 0.02:
            continue
        pts = []
        for i in range(41):
            th = 2 * math.pi * i / 40
            p = ctr + rad * (math.cos(th) * RE1 + math.sin(th) * RE2)
            pts.append(P2(p[0], p[1], p[2], c))
        la.line(pts, fill=sc3(ORANGE, a), width=lw)


def draw_dome(la, c, t, on):
    if on <= 0:
        return
    R0 = 330.0
    lw = max(2, int(3 * S))
    for k, th in enumerate((18, 38, 58, 78)):
        r = R0 * math.cos(math.radians(th))
        y = R0 * math.sin(math.radians(th))
        pts = [P2(r * math.cos(2 * math.pi * i / 48), y, r * math.sin(2 * math.pi * i / 48), c) for i in range(49)]
        a = on * (0.30 + 0.35 * (0.5 + 0.5 * math.sin(2 * math.pi * (0.7 * t - k * 0.12))))
        la.line(pts, fill=sc3(CYAN, a), width=lw)
    for m in range(8):
        az = 2 * math.pi * m / 8
        pts = []
        for i in range(21):
            th = math.radians(90 * i / 20)
            r = R0 * math.cos(th)
            pts.append(P2(r * math.cos(az), R0 * math.sin(th), r * math.sin(az), c))
        la.line(pts, fill=sc3(CYAN, on * 0.28), width=max(1, int(2 * S)))
    pts = [P2(R0 * math.cos(2 * math.pi * i / 64), 0.5, R0 * math.sin(2 * math.pi * i / 64), c) for i in range(65)]
    la.line(pts, fill=sc3(CYAN, on * 0.7), width=lw)


def wave3(la, c, x0, x1, y, z, amp, k, w, t, col, a, phase=0.0, n=70, env=None, width=None):
    pts = []
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        e = 1.0 if env is None else env(i / n)
        pts.append(P2(x, y + amp * e * math.sin(k * x - w * t + phase), z, c))
    la.line(pts, fill=sc3(col, a), width=width or max(2, int(4 * S)), joint="curve")


def draw_particles(la, c, t, a):
    for row, (z, yy) in enumerate(((-40, 105), (0, 105), (40, 105))):
        for i in range(70):
            x0 = -660 + i * (480 / 70.0)
            ph = 2 * math.pi * (x0 / 150.0 - 0.9 * t)
            dx = 15 * math.sin(ph)
            dens = 0.5 + 0.5 * (-math.cos(ph))     # compresión alta cuando -cos grande
            x = x0 + dx
            px, py = P2(x, yy, z, c)
            rr = (3.2 + 2.0 * dens) * S
            col = lc((120, 190, 255), ORANGE, dens)
            la.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(col, a * (0.35 + 0.65 * dens)))
    wave3(la, c, -660, -180, 175, 0, 36, 2 * math.pi / 150.0, 2 * math.pi * 0.9, t, ORANGE, a * 0.9, phase=math.pi / 2)


# ---------------- escena 6 (2D, cabina) ----------------
def noise_fn(x, t):
    return math.sin(x / 41.0 - 6.0 * t) + 0.45 * math.sin(x / 20.0 - 12.0 * t)


def voice_fn(x, t):
    env = max(0.0, math.sin(0.021 * x - 1.7 * t)) ** 2 * 0.9 + max(0.0, math.sin(0.047 * x + 0.9 * t + 1.3)) ** 3 * 0.8
    return env * (0.6 * math.sin(0.19 * x - 3.1 * t) + 0.4 * math.sin(0.41 * x + 2.3 * t))


def render_s6(t):
    base = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(base)
    for i in range(24):
        y0 = int(i * H / 24)
        f = i / 23
        d.rectangle((0, y0, W, y0 + int(H / 24) + 1), fill=lc((80, 88, 110), (36, 42, 64), f) and tuple(int(v) for v in lc((80, 88, 110), (36, 42, 64), f)))
    # ventanillas y asientos (colores de cabina)
    for (xa, xb) in ((110, 290), (790, 970)):
        d.rounded_rectangle((*P(xa - 14, 370), *P(xb + 14, 520)), radius=int(70 * S), fill=(214, 218, 228))
        d.rounded_rectangle((*P(xa, 384), *P(xb, 506)), radius=int(58 * S), fill=(120, 172, 232))
        d.ellipse((*P(xa + 20, 440), *P(xa + 110, 490)), fill=(236, 242, 250))
        d.ellipse((*P(xa + 70, 425), *P(xa + 150, 485)), fill=(246, 248, 252))
    d.rounded_rectangle((*P(60, 1370), *P(1020, 1990)), radius=int(90 * S), fill=(30, 44, 92))
    d.rounded_rectangle((*P(300, 1300), *P(780, 1500)), radius=int(80 * S), fill=(40, 58, 112))
    for xx in (140, 940):
        d.line([P(xx, 1450), P(xx, 1900)], fill=(24, 34, 74), width=int(8 * S))
    L = Image.new("RGB", (W, H), (0, 0, 0))
    ld = ImageDraw.Draw(L)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    lw = max(2, int(4 * S))
    panels = [(560, 880, T6A + 0.3, "ZUMBIDO CONSTANTE", "motor de avión", True),
              (960, 1280, 39.0, "VOCES Y GOLPES", "sonidos impredecibles", False)]
    for (y0, y1, ta, title, sub, good) in panels:
        a = ease(seg(t, ta, ta + 0.5))
        if a <= 0:
            continue
        od.rounded_rectangle((*P(90, y0), *P(990, y1)), radius=int(30 * S), fill=(8, 12, 28, int(205 * a)), outline=(90, 84, 170, int(220 * a)), width=max(1, int(2 * S)))
        gy = (y0 + y1) / 2 + 40
        gx0, gx1 = 140, 940
        for k in range(-2, 3):
            ld.line([P(gx0, gy + k * 36), P(gx1, gy + k * 36)], fill=sc3((70, 70, 120), 0.35 * a), width=1)
        ln, lr = [], []
        for i in range(121):
            x = gx0 + (gx1 - gx0) * i / 120
            if good:
                nv = noise_fn(x, t) * 38
                rv = nv * 0.07
            else:
                nv = voice_fn(x, t) * 70
                rv = voice_fn(x + 37, t) * 70 * 0.55
            ln.append(P(x, gy + nv))
            lr.append(P(x, gy + rv))
        ld.line(ln, fill=sc3(ORANGE, 0.85 * a), width=lw, joint="curve")
        ra = ease(seg(t, ta + 0.8, ta + 1.6))
        ld.line(lr, fill=sc3(CYAN, 0.95 * a * ra), width=lw + 1, joint="curve")
    return base, L, ov, panels


def render_s6_texts(l2, t, panels):
    for (y0, y1, ta, title, sub, good) in panels:
        a = ease(seg(t, ta, ta + 0.5))
        if a <= 0:
            continue
        l2.text(P(130, y0 + 38), title, font=F(B, 36), fill=sc3((240, 240, 255), a), anchor="lm")
        l2.text(P(130, y0 + 82), sub, font=F(R, 28), fill=sc3((170, 170, 215), a), anchor="lm")
        ra = ease(seg(t, ta + 1.2, ta + 1.9))
        if good:
            col = (110, 235, 160)
            pts = [P(850, y0 + 40), P(872, y0 + 64), P(912, y0 + 22)]
            l2.line(pts, fill=sc3(col, a * ra), width=max(3, int(8 * S)), joint="curve")
            l2.text(P(930, y0 + 100), "SE CANCELA BIEN", font=F(B, 26), fill=sc3(col, a * ra), anchor="rm")
        else:
            col = (255, 150, 90)
            l2.line([P(860, y0 + 24), P(910, y0 + 70)], fill=sc3(col, a * ra), width=max(3, int(8 * S)))
            l2.line([P(910, y0 + 24), P(860, y0 + 70)], fill=sc3(col, a * ra), width=max(3, int(8 * S)))
            l2.text(P(930, y0 + 100), "MÁS DIFÍCIL", font=F(B, 26), fill=sc3(col, a * ra), anchor="rm")


# ---------------- render principal ----------------
def render(t):
    L2 = Image.new("RGB", (W, H), (0, 0, 0))
    l2 = ImageDraw.Draw(L2)
    in6 = T6A <= t < T6B
    c = cam_at(t)

    if in6:
        base, LA, ov, panels = render_s6(t)
        imgA = Image.fromarray(np.clip(np.asarray(base, dtype=np.float32), 0, 255).astype(np.uint8)).convert("RGBA")
        imgA = Image.alpha_composite(imgA, ov).convert("RGB")
        arr = np.asarray(imgA, dtype=np.float32) + np.asarray(LA, dtype=np.float32) + 1.3 * glow_of(LA, 4)
        render_s6_texts(l2, t, panels)
    else:
        xr = ease(seg(t, 26.0, 27.0)) * (1 - ease(seg(t, 32.5, 33.0)))
        dim_env = 1 - 0.62 * xr
        base = Image.new("RGB", (W, H), (10, 10, 16))
        bd = ImageDraw.Draw(base)
        draw_room(bd, c, t, dim_env)
        LA = Image.new("RGB", (W, H), (0, 0, 0))
        la = ImageDraw.Draw(LA)
        wires = None
        if xr > 0.02:
            wires = draw_internals(bd, c, t)
        # audífonos (con transparencia en rayos X)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        alpha = int(255 * (1 - 0.86 * xr))
        for dep, pts, col in hp_polys(c, 1.0 - 0.25 * xr):
            od.polygon(pts, fill=(*col, alpha))
        for sgn in (-1, 1):
            xo = 150 * sgn + sgn * 26
            ring = [P2(xo, 95 + 66 * math.cos(2 * math.pi * i / 36), 66 * math.sin(2 * math.pi * i / 36), c) for i in range(37)]
            if vis(c, (xo, 95, 0), (sgn, 0, 0)):
                od.line(ring, fill=(*HP_SILVER, alpha), width=max(2, int(4 * S)))
        # orificio del micrófono exterior (siempre visible)
        mp = [P2(-177, 148 + 9 * math.cos(2 * math.pi * i / 16), -8 + 9 * math.sin(2 * math.pi * i / 16), c) for i in range(16)]
        if vis(c, (-177, 148, -8), (-1, 0, 0)):
            od.polygon(mp, fill=(70, 72, 84, 255))

        # luz de la ventana (resplandor)
        wx0, wx1, wy0, wy1 = WIN
        la.polygon([P2(*p, c) for p in wall_quad(wx0, wx1, wy0, wy1)], fill=sc3((60, 42, 20), 1.0 - 0.6 * xr))

        # ------- efectos por escena -------
        a_ring1 = ease(seg(t, 0.8, 1.8)) * (1 - ease(seg(t, 4.6, 5.2)))
        if a_ring1 > 0:
            draw_rings(la, c, t, a_ring1, False)
        a_part = ease(seg(t, 5.2, 6.0)) * (1 - ease(seg(t, 10.6, 11.4)))
        if a_part > 0:
            draw_particles(la, c, t, a_part)
        # escena 3: ruido que llega y anti-ruido que sale
        a3 = ease(seg(t, 11.4, 12.2)) * (1 - ease(seg(t, 18.0, 18.6)))
        if a3 > 0:
            k = 2 * math.pi / 150.0
            w = 2 * math.pi * 0.9
            wave3(la, c, -720, -180, 148, -8, 34, k, w, t, ORANGE, a3)
            ca3 = ease(seg(t, 14.4, 15.4)) * a3
            wave3(la, c, -124, 60, 95, 0, 34, k, w, t, CYAN, ca3, phase=math.pi,
                  env=lambda u: ease(u * 6) * (1 - 0.0))
            pm = 0.6 + 0.4 * math.sin(2 * math.pi * 3 * t)
            mpp = [P2(-177, 148 + 15 * math.cos(2 * math.pi * i / 24), -8 + 15 * math.sin(2 * math.pi * i / 24), c) for i in range(25)]
            la.line(mpp, fill=sc3(BLUE, a3 * pm), width=max(2, int(4 * S)))
        # escena 4: panel de cristal con las ondas
        a4 = ease(seg(t, 19.1, 19.9)) * (1 - ease(seg(t, 25.0, 25.6)))
        if a4 > 0:
            px0, px1, py0, py1, pz = -280, 280, 160, 440, -60
            quad = [P2(px0, py0, pz, c), P2(px1, py0, pz, c), P2(px1, py1, pz, c), P2(px0, py1, pz, c)]
            od.polygon(quad, fill=(8, 12, 30, int(200 * a4)))
            la.line(quad + [quad[0]], fill=sc3(VIOLET, 0.9 * a4), width=max(2, int(3 * S)))
            ymid = (py0 + py1) / 2
            for gi in range(-2, 3):
                la.line([P2(px0, ymid + gi * 55, pz, c), P2(px1, ymid + gi * 55, pz, c)], fill=sc3((70, 70, 130), 0.5 * a4), width=1)
            for gi in range(-4, 5):
                la.line([P2(gi * 62, py0, pz, c), P2(gi * 62, py1, pz, c)], fill=sc3((70, 70, 130), 0.3 * a4), width=1)
            phi = math.pi * ease(seg(t, 21.4, 24.4))
            anti_a = ease(seg(t, 19.6, 20.4))
            kk = 2 * math.pi / 220.0
            ww = 2 * math.pi * 0.8
            n = 100
            pa, pb, pc_ = [], [], []
            for i in range(n + 1):
                x = lerp(px0 + 10, px1 - 10, i / n)
                nz = 60 * math.sin(kk * x - ww * t)
                an = 60 * anti_a * math.sin(kk * x - ww * t + phi)
                pa.append(P2(x, ymid + nz, pz, c))
                pb.append(P2(x, ymid + an, pz, c))
                pc_.append(P2(x, ymid + nz + an, pz, c))
            la.line(pa, fill=sc3(ORANGE, 0.9 * a4), width=max(2, int(4 * S)), joint="curve")
            la.line(pb, fill=sc3(CYAN, 0.9 * a4), width=max(2, int(4 * S)), joint="curve")
            la.line(pc_, fill=sc3((255, 255, 255), a4), width=max(3, int(6 * S)), joint="curve")
        # escena 5: rayos X
        if xr > 0.02:
            ys = 45 + 110 * ((t * 0.45) % 1.0)
            sq = [P2(-190, ys, -100, c), P2(-100, ys, -100, c), P2(-100, ys, 100, c), P2(-190, ys, 100, c)]
            la.polygon(sq, fill=sc3(BLUE, 0.16 * xr))
            la.line(sq + [sq[0]], fill=sc3(BLUE, 0.55 * xr), width=max(1, int(2 * S)))
            for sgn in (-1, 1):
                xo = 150 * sgn + sgn * 26
                ringx = [P2(xo, 95 + 88 * math.cos(2 * math.pi * i / 48), 88 * math.sin(2 * math.pi * i / 48), c) for i in range(49)]
                la.line(ringx, fill=sc3((90, 200, 255), 0.85 * xr), width=max(2, int(3 * S)))
            band = [P2(150 * math.cos(math.pi * (1 - i / 40)), 183 + 150 * math.sin(math.pi * (1 - i / 40)), -15, c) for i in range(41)]
            la.line(band, fill=sc3((90, 200, 255), 0.85 * xr), width=max(2, int(3 * S)))
            # señales por los cables
            if wires is not None:
                sa = xr * ease(seg(t, 26.8, 27.6))
                for wi, wr in enumerate(wires):
                    for j in range(3):
                        u = (t * 0.7 + j / 3.0 + wi * 0.2) % 1.0
                        p = poly_pts(wr, u)
                        qx, qy = P2(*p, c)
                        rr = 5 * S
                        la.ellipse((qx - rr, qy - rr, qx + rr, qy + rr), fill=sc3(CYAN if wi != 1 else (255, 220, 160), sa))
                pm = 0.6 + 0.4 * math.sin(2 * math.pi * 3 * t)
                for (ctr_, rad_, col_) in (((-177, 148, -8), 16, BLUE), ((-166, 97, -32), 22, VIOLET), ((-132, 95, 0), 70, CYAN)):
                    if (col_ == BLUE and t > 26.3) or (col_ == VIOLET and t > 27.5) or (col_ == CYAN and t > 29.0):
                        r_ = [P2(ctr_[0], ctr_[1] + rad_ * math.cos(2 * math.pi * i / 28), ctr_[2] + rad_ * math.sin(2 * math.pi * i / 28), c) for i in range(29)]
                        la.line(r_, fill=sc3(col_, xr * pm), width=max(2, int(4 * S)))
        # escena 7: burbuja de silencio
        on7 = ease(seg(t, 43.2, 44.4))
        if on7 > 0 and t >= 42.9:
            draw_dome(la, c, t, on7)
            draw_rings(la, c, t, on7, True)
        if t >= 42.9 and on7 <= 0:
            pass

        arrA = np.asarray(base, dtype=np.float32)
        imgA = Image.fromarray(np.clip(arrA, 0, 255).astype(np.uint8)).convert("RGBA")
        imgB = Image.alpha_composite(imgA, ov).convert("RGB")
        arr = np.asarray(imgB, dtype=np.float32) + np.asarray(LA, dtype=np.float32) + 1.5 * glow_of(LA, 4)

    # ---------- transiciones y cierre ----------
    f = 1.0
    for cut in (T6A, T6B):
        f = min(f, clamp(abs(t - cut) / 0.28))
    arr = arr * f
    arr = arr * (1 - 0.92 * seg(t, T_OUT, T_OUT + 0.8))

    # ---------- HUD ----------
    anim.draw_caption(l2, t)
    hud(l2, c, t)
    arr = arr + np.asarray(L2, dtype=np.float32) + 1.2 * glow_of(L2, 3)
    arr = arr * (seg(t, 0.0, 0.4) * (1 - seg(t, DUR - 0.5, DUR)))
    return np.clip(arr, 0, 255).astype(np.uint8)


def hud(l2, c, t):
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

    def pill(txt, y, a, col=BLUE, w=520):
        if a <= 0:
            return
        l2.rounded_rectangle((*P(540 - w / 2, y - 42), *P(540 + w / 2, y + 42)), radius=int(42 * S), outline=sc3(col, a), width=max(2, int(3 * S)))
        l2.text(P(540, y), txt, font=F(B, 36), fill=sc3((225, 235, 255), a), anchor="mm")

    in6 = T6A <= t < T6B
    if in6:
        return
    # S1
    a = ease(seg(t, 1.2, 1.9)) * (1 - ease(seg(t, 4.6, 5.1)))
    if a > 0:
        tgt = proj(-360, 360, WZ, c)[:2]
        label("RUIDO DEL EXTERIOR", tgt, (1030, min(1500, tgt[1] + 300)), "rm", a, (255, 190, 140))
    # S2
    pill("ONDA DE PRESIÓN", 1580, ease(seg(t, 5.4, 6.0)) * (1 - ease(seg(t, 10.4, 11.0))), VIOLET)
    # S3
    a = ease(seg(t, 11.6, 12.2)) * (1 - ease(seg(t, 17.8, 18.4)))
    if a > 0:
        tgt = proj(-177, 148, -8, c)[:2]
        label("MICRÓFONO EXTERIOR", tgt, (1030, max(470, tgt[1] - 330)), "rm", a)
    a = ease(seg(t, 15.0, 15.6)) * (1 - ease(seg(t, 17.8, 18.4)))
    if a > 0:
        p = proj(-30, 95 + 34 * math.sin(0.0), 0, c)[:2]
        label("ANTI-RUIDO", p, (60, min(1500, p[1] + 330)), "lm", a, (150, 230, 255))
    a = ease(seg(t, 14.4, 15.0)) * (1 - ease(seg(t, 17.8, 18.4)))
    if a > 0:
        l2.rounded_rectangle((*P(250, 430), *P(830, 600)), radius=int(24 * S), outline=sc3((100, 90, 190), a * 0.9), width=max(1, int(2 * S)))
        l2.text(P(540, 495), "< 1 ms", font=F(M, 100), fill=sc3((235, 225, 255), a), anchor="mm")
        l2.text(P(540, 570), "TIEMPO DE CÁLCULO DEL CHIP", font=F(B, 26), fill=sc3((170, 160, 230), a), anchor="mm")
    # S4
    a4 = ease(seg(t, 19.3, 20.0)) * (1 - ease(seg(t, 25.0, 25.6)))
    if a4 > 0:
        for i, (txt, col) in enumerate((("RUIDO", ORANGE), ("ANTI-RUIDO", CYAN), ("RESULTADO", (255, 255, 255)))):
            x = 130 + i * 300
            rr = 10 * S
            px, py = P(x, 1400)
            l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(col, a4))
            l2.text(P(x + 24, 1400), txt, font=F(B, 30), fill=sc3((215, 215, 240), a4), anchor="lm")
        phi = ease(seg(t, 21.4, 24.4))
        l2.line([P(240, 1530), P(840, 1530)], fill=sc3((110, 110, 180), a4), width=max(2, int(6 * S)))
        kx = 240 + 600 * phi
        rr = 20 * S
        px, py = P(kx, 1530)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3((240, 235, 255), a4))
        l2.text(P(240, 1585), "FASE", font=F(B, 30), fill=sc3((170, 170, 225), a4), anchor="lm")
        l2.text(P(840, 1585), f"{int(180 * phi)}°", font=F(M, 40), fill=sc3((240, 235, 255), a4), anchor="rm")
        rem = abs(math.cos(math.pi * phi / 2)) * 100
        l2.text(P(540, 1660), f"RUIDO RESTANTE: {int(round(rem))}%", font=F(B, 34), fill=sc3((255, 255, 255), a4), anchor="mm")
    # S5 etiquetas
    af = (1 - ease(seg(t, 32.4, 32.9)))
    if t >= 26.3 and t < 33.0:
        specs = [(26.5, "MICRÓFONO EXTERIOR", (-177, 148, -8), (1030, -1), "rm"),
                 (27.2, "MICRÓFONO INTERIOR", (-124, 122, 38), (60, -1), "lm"),
                 (27.9, "PROCESADOR (DSP)", (-166, 97, -32), (1030, -1), "rm"),
                 (29.0, "BOCINA", (-132, 95, 0), (60, -1), "lm")]
        for (ta, txt, p3, (tx, _), anc) in specs:
            a = ease(seg(t, ta, ta + 0.5)) * af
            if a > 0:
                tgt = proj(*p3, c)[:2]
                dy = {"MICRÓFONO EXTERIOR": -330, "MICRÓFONO INTERIOR": 380, "PROCESADOR (DSP)": 300, "BOCINA": -330}[txt]
                label(txt, tgt, (tx, clamp(tgt[1] + dy, 440, 1560)), anc, a)
    # S7
    pill("BURBUJA DE SILENCIO", 1580, ease(seg(t, 43.8, 44.4)) * (1 - ease(seg(t, 46.0, 46.4))), CYAN, 600)
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
        os.makedirs("/home/claude/prevnc", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render(float(ts))).save(f"/home/claude/prevnc/t_{ts}.png")
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
