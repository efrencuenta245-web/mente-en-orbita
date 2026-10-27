"""Moto de motocross estilizada (genérica, sin marcas) en cm. Ejes locales: x adelante, y arriba, z = lado IZQUIERDO
(el proyector espeja la quiralidad: la cámara en -z ve el lado derecho con el frente a la derecha de la pantalla).
Dos versiones: 'elec' (batería + motor eléctrico, sin clutch ni palanca de cambios) y 'gas' (motor 450, escape, clutch).
Incluye un piloto estilizado opcional."""
import math
import numpy as np
from nc import proj, P2, vis
from fo import clip_near

RA = np.array([-74.0, 34.0, 0.0])   # eje trasero
FA = np.array([74.0, 36.0, 0.0])    # eje delantero
SP = np.array([-10.0, 46.0, 0.0])   # pivote del basculante
RAKE = math.radians(27.0)
FDIR = np.array([-math.sin(RAKE), math.cos(RAKE), 0.0])
TOP = FA + 92 * FDIR                # tija superior
HB = TOP + np.array([-6.0, 9.0, 0.0])  # manubrio


def _n(v):
    v = np.asarray(v, np.float64)
    return v / np.linalg.norm(v)


class Model:
    def __init__(self):
        self.F = []   # (pts(k,3), normal(3), color, tag)

    def face(self, pts, n, col, tag='body'):
        self.F.append((np.asarray(pts, np.float64), np.asarray(n, np.float64), col, tag))

    def box(self, lo, hi, col, tag='body'):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        self.face([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0), col, tag)
        self.face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0), col, tag)
        self.face([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], (0, 0, -1), col, tag)
        self.face([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1), col, tag)
        self.face([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0), col, tag)
        self.face([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], (1, 0, 0), col, tag)

    def ext(self, pts2, z0, z1, col, tag='body', side_col=None):
        """polígono 2D (x,y) extruido entre z0 y z1"""
        p = list(pts2)
        area = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
        if area < 0:
            p = p[::-1]
        self.face([(x, y, z1) for (x, y) in p], (0, 0, 1), col, tag)
        self.face([(x, y, z0) for (x, y) in p[::-1]], (0, 0, -1), col, tag)
        sc = side_col or col
        for i in range(len(p)):
            a, b = p[i], p[(i + 1) % len(p)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 1e-6:
                continue
            self.face([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], (dy / L, -dx / L, 0), sc, tag)

    def beam(self, p0, p1, w, h, col, tag='body', side=(0, 0, 1)):
        p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
        ax = _n(p1 - p0)
        s = _n(side)
        if abs(ax @ s) > 0.95:
            s = _n((0, 1, 0))
        up = _n(np.cross(s, ax))
        s = np.cross(ax, up)
        hw, hh = w / 2, h / 2
        corners = lambda p: [p + s * hw + up * hh, p - s * hw + up * hh, p - s * hw - up * hh, p + s * hw - up * hh]
        A, Bc = corners(p0), corners(p1)
        norms = [up, -s, -up, s]
        for i in range(4):
            j = (i + 1) % 4
            mid = (A[i] + A[j]) / 2 - p0
            self.face([A[i], A[j], Bc[j], Bc[i]], _n(mid), col, tag)
        self.face(A[::-1], -ax, col, tag)
        self.face(Bc, ax, col, tag)

    def cyl(self, ctr, axis, r, length, col, n=16, tag='body', caps=True, cap_col=None):
        ctr = np.asarray(ctr, np.float64)
        ax = _n(axis)
        a = np.array([1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.array([0, 1.0, 0])
        e1 = _n(np.cross(ax, a))
        e2 = np.cross(ax, e1)
        h = length / 2
        ring = lambda s: [ctr + ax * s * h + r * (math.cos(2 * math.pi * i / n) * e1 + math.sin(2 * math.pi * i / n) * e2) for i in range(n)]
        A, Bc = ring(-1), ring(1)
        for i in range(n):
            j = (i + 1) % n
            tm = 2 * math.pi * (i + 0.5) / n
            self.face([A[i], A[j], Bc[j], Bc[i]], math.cos(tm) * e1 + math.sin(tm) * e2, col, tag)
        if caps:
            self.face(A[::-1], -ax, cap_col or col, tag)
            self.face(Bc, ax, cap_col or col, tag)


WHITE = (232, 234, 238)
BLACK = (30, 31, 36)
DGRAY = (58, 60, 66)
SILVER = (176, 180, 188)
GOLD = (214, 170, 70)
TIRE = (28, 28, 30)


def build(kind='elec', rider=True):
    m = Model()
    accent = (60, 200, 255) if kind == 'elec' else (240, 120, 40)
    plast = WHITE if kind == 'elec' else (236, 112, 36)
    # ruedas (se dibujan aparte para girar los rayos, aquí solo llantas)
    for (axc, r, w) in ((RA, 34.0, 11.0), (FA, 36.0, 9.0)):
        m.cyl(axc, (0, 0, 1), r, w, TIRE, 22, 'tire', True, (24, 24, 26))
        m.cyl(axc, (0, 0, 1), 5, w + 6, SILVER, 8, 'body')
    # basculante
    for zz in (-8, 8):
        m.beam(SP + (0, 0, zz), RA + (0, 2, zz), 6, 8, SILVER)
    # horquilla
    for zz in (-9, 9):
        p_mid = FA + 50 * FDIR
        m.beam(FA + (0, 0, zz), p_mid + (0, 0, zz), 7.5, 7.5, BLACK)
        m.beam(p_mid + (0, 0, zz), TOP + (0, 0, zz), 6, 6, GOLD)
    m.box(TOP + (-6, -3, -13), TOP + (6, 3, 13), DGRAY)
    m.box(TOP - 22 * FDIR + (-6, -3, -13), TOP - 22 * FDIR + (6, 3, 13), DGRAY)
    # manubrio y puños
    m.beam(HB + (0, 0, -40), HB + (0, 0, 40), 3, 3, BLACK, side=(1, 0, 0))
    m.beam(TOP, HB, 4, 4, DGRAY)
    for zz in (-42, 42):
        m.beam(HB + (0, 0, zz - 6 * np.sign(zz)), HB + (0, 0, zz + 6 * np.sign(zz)), 4.5, 4.5, (20, 20, 22), side=(1, 0, 0))
    # palanca de freno (derecha) y clutch (izquierda, solo gasolina)
    m.beam(HB + (2, 0, -30), HB + (14, -4, -38), 2, 1.5, SILVER, 'brake_lever')
    if kind == 'gas':
        m.beam(HB + (2, 0, 30), HB + (14, -4, 38), 2, 1.5, SILVER, 'clutch')
    # chasis
    head_b = TOP - 30 * FDIR
    m.beam(head_b, (-12, 96, 0), 6, 6, DGRAY if kind == 'elec' else (40, 40, 46))
    for zz in (-9, 9):
        m.beam((-12, 96, zz), (-16, 52, zz), 5, 5, DGRAY)
        m.beam(head_b + (0, 0, zz * 0.4), (28, 40, zz), 5, 5, DGRAY)
        m.beam((28, 40, zz), (-12, 36, zz), 5, 5, DGRAY)
        m.beam((-12, 96, zz), (-70, 90, zz * 1.2), 3.5, 3.5, DGRAY)
    # amortiguador
    m.beam((-14, 92, 0), (-26, 52, 0), 6, 6, (226, 196, 60), 'shock')
    if kind == 'elec':
        # batería (estructural) y motor
        m.box((-22, 46, -12), (36, 92, 12), (44, 46, 54), 'battery')
        m.cyl((-2, 40, 0), (0, 0, 1), 12, 22, (90, 94, 104), 18, 'motor')
        m.box((12, 82, -9), (34, 94, 9), (70, 74, 86), 'inverter')
        # pantalla tipo teléfono en el manubrio
        m.box(HB + (-3, 3, -5), HB + (1, 15, 5), (16, 16, 20), 'phone')
    else:
        # motor de combustión: cárter, cilindro, escape
        m.box((-18, 30, -12), (26, 60, 12), (150, 154, 162), 'engine')
        m.beam((6, 56, 0), (22, 88, 0), 22, 18, (160, 164, 172), 'engine', side=(0, 0, 1))
        m.box((14, 84, -8), (30, 96, 8), (60, 62, 68), 'engine')
        pts = [(28, 80, -6), (44, 70, -12), (40, 48, -16), (20, 40, -18), (-10, 44, -18), (-30, 70, -16)]
        for i in range(len(pts) - 1):
            m.beam(pts[i], pts[i + 1], 5, 5, (170, 120, 80), 'exhaust')
        m.cyl((-62, 80, -16), (-1, 0.12, 0), 8, 62, (60, 62, 68), 14, 'exhaust', True, (130, 134, 140))
        m.beam(SP + (2, -2, 16), SP + (22, 2, 16), 2, 2, SILVER, 'shifter')
    # plásticos
    arc = [(FA[0] + 47 * math.cos(math.radians(a)), FA[1] + 47 * math.sin(math.radians(a))) for a in np.linspace(5, 120, 9)]
    arc_in = [(FA[0] + 43 * math.cos(math.radians(a)), FA[1] + 43 * math.sin(math.radians(a))) for a in np.linspace(120, 5, 9)]
    m.ext(arc + arc_in, -8, 8, plast, 'shell')
    # placa delantera
    pc = TOP - 10 * FDIR + np.array([9, 0, 0])
    m.ext([(pc[0] - 3, pc[1] - 18), (pc[0] + 6, pc[1] - 16), (pc[0] + 3, pc[1] + 14), (pc[0] - 6, pc[1] + 12)], -13, 13, plast, 'shell')
    # cubiertas laterales (radiador)
    sh = [(44, 108), (14, 106), (-8, 94), (-4, 66), (22, 56), (40, 80)]
    for (z0, z1) in ((13, 16), (-16, -13)):
        m.ext(sh, z0, z1, plast, 'shell')
    acc = [(36, 98), (12, 99), (-2, 88), (16, 76)]
    m.ext(acc, 16, 16.8, accent, 'shell')
    m.ext(acc, -16.8, -16, accent, 'shell')
    # asiento
    m.ext([(24, 106), (-10, 102), (-72, 98), (-74, 93), (-10, 95), (20, 99)], -11, 11, (24, 24, 28), 'shell')
    # guardabarros trasero y placas laterales
    m.ext([(-30, 97), (-108, 94), (-110, 89), (-30, 91)], -13, 13, plast, 'shell')
    m.ext([(-24, 95), (-72, 93), (-60, 62), (-28, 70)], 12, 14, WHITE, 'shell')
    m.ext([(-24, 95), (-72, 93), (-60, 62), (-28, 70)], -14, -12, WHITE, 'shell')
    # estribos
    for zz in (-20, 20):
        m.box((-10, 38, zz - 6), (2, 41, zz + 6), SILVER)
    if rider:
        suit = (40, 44, 56) if kind == 'elec' else (60, 40, 36)
        jersey = (40, 170, 230) if kind == 'elec' else (236, 112, 36)
        helm = WHITE if kind == 'elec' else (240, 240, 240)
        for s in (-1, 1):
            foot = np.array([-4, 44, 20 * s])
            knee = np.array([18, 86, 22 * s])
            hip = np.array([-18, 112, 11 * s])
            m.beam(foot, knee, 11, 11, suit, 'rider')
            m.beam(knee, hip, 13, 13, suit, 'rider')
            m.box(foot + (-10, -4, -5), foot + (12, 8, 5), (20, 20, 24), 'rider')
            sh_ = np.array([8, 152, 17 * s])
            elbow = np.array([18, 138, 34 * s])
            grip = HB + np.array([0, 0, 40 * s])
            m.beam(sh_, elbow, 10, 10, jersey, 'rider')
            m.beam(elbow, grip, 9, 9, jersey, 'rider')
        m.beam((-18, 112, 0), (8, 154, 0), 30, 22, jersey, 'rider', side=(0, 0, 1))
        m.box((4, 158, -13), (34, 188, 13), helm, 'rider')
        m.box((30, 160, -10), (44, 174, 10), helm, 'rider')
        m.box((26, 170, -9.5), (35, 182, 9.5), (24, 30, 44), 'rider')
        m.box((10, 186, -12), (40, 190, 12), jersey, 'rider')
    return m


MODELS = {}


def get(kind, rider):
    k = (kind, rider)
    if k not in MODELS:
        MODELS[k] = build(kind, rider)
    return MODELS[k]


def rot(yaw, pitch=0.0, roll=0.0):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, spt = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rz = np.array([[cp, -spt, 0], [spt, cp, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Ry @ Rz @ Rx


def shade(col, n, L, dim=1.0, amb=0.42, dif=0.8):
    d = max(0.0, n[0] * L[0] + n[1] * L[1] + n[2] * L[2])
    k = (amb + dif * d) * dim
    return (min(255, int(col[0] * k)), min(255, int(col[1] * k)), min(255, int(col[2] * k)))


def wheel_decals(ang):
    """rin y rayos sobre las caras laterales de las llantas (giran con ang)"""
    F = []
    for (axc, w) in ((RA, 11.0), (FA, 9.0)):
        for s in (-1, 1):
            z = s * (w / 2 + 0.4)
            n = (0, 0, s)
            for i in range(18):
                a0, a1 = 2 * math.pi * i / 18, 2 * math.pi * (i + 1) / 18
                pts = [(axc[0] + r * math.cos(a), axc[1] + r * math.sin(a), z) for (r, a) in ((21, a0), (24, a0), (24, a1), (21, a1))]
                F.append((np.array(pts), np.array(n, np.float64), SILVER, 'decal', axc[:2]))
            for k in range(12):
                a = ang + 2 * math.pi * k / 12
                ca, sa = math.cos(a), math.sin(a)
                px, py = -sa * 0.6, ca * 0.6
                pts = [(axc[0] + 5 * ca + px, axc[1] + 5 * sa + py, z), (axc[0] + 21 * ca + px, axc[1] + 21 * sa + py, z),
                       (axc[0] + 21 * ca - px, axc[1] + 21 * sa - py, z), (axc[0] + 5 * ca - px, axc[1] + 5 * sa - py, z)]
                F.append((np.array(pts), np.array(n, np.float64), (150, 154, 162), 'decal', axc[:2]))
    return F


def faces(c, kind, pos, yaw=0.0, pitch=0.0, L=(-0.4, 0.8, -0.45), dim=1.0, rider=True, xr=0.0, near=20.0, hide=(), wheel=0.0):
    """devuelve lista (dep, pts2d, color, alpha, tag) lista para ordenar; xr>0 vuelve translúcida la carrocería"""
    m = get(kind, rider)
    Rm = rot(yaw, pitch)
    pos = np.asarray(pos, np.float64)
    out = []
    L = np.asarray(L, np.float64)
    L = L / np.linalg.norm(L)
    cam = np.asarray(c['pos'])
    for (pts, n, col, tag, anc) in wheel_decals(wheel):
        W_ = pts @ Rm.T + pos
        nw = Rm @ n
        a3 = Rm @ np.array([anc[0], anc[1], pts[0][2]]) + pos
        if nw @ (cam - a3) <= 0:
            continue
        q = clip_near([tuple(p) for p in W_], c, near)
        if len(q) < 3:
            continue
        dep = proj(*a3, c)[2] - 0.6
        out.append((dep, [P2(*p, c) for p in q], shade(col, nw, L, dim), int(255 * (1 - 0.8 * xr)) if xr > 0.01 else None, tag))
    for (pts, n, col, tag) in m.F:
        if tag in hide:
            continue
        W_ = pts @ Rm.T + pos
        nw = Rm @ n
        ctr = W_.mean(0)
        if nw @ (cam - ctr) <= 0:
            continue
        q = clip_near([tuple(p) for p in W_], c, near)
        if len(q) < 3:
            continue
        dep = proj(*ctr, c)[2]
        cc = shade(col, nw, L, dim)
        alpha = None
        if xr > 0.01 and tag in ('shell', 'rider', 'engine', 'exhaust', 'tire'):
            alpha = int(255 * (1 - 0.8 * xr))
        out.append((dep, [P2(*p, c) for p in q], cc, alpha, tag))
    return out


def world(pos, yaw, pitch, p):
    return tuple(rot(yaw, pitch) @ np.asarray(p, np.float64) + np.asarray(pos, np.float64))
