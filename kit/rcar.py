"""Auto de rally genérico (sin marcas) en metros. Ejes locales: x adelante, y arriba, z a la izquierda.
Carrocería por secciones (loft), ruedas aparte (giran y se comprimen) e interiores para el escáner:
jaula de tubos, motor + turbo, escape, tracción 4x4, amortiguadores, asientos y tripulación."""
import math
import numpy as np
import moto_model as mm
from vasec import tube, catmull, blob

WHITE = (236, 238, 242)
NAVY = (22, 44, 112)
BLUEC = (30, 110, 220)
ORANGEC = (246, 112, 28)
BLACK = (24, 25, 28)
GLASS = (34, 44, 58)
TIRE = (26, 26, 28)
RIM = (226, 228, 232)

XR, XF = -2.05, 2.05
WB = 1.27            # medio entre ejes
TRACK = 0.80         # mitad de vía (centro de llanta)
RW = 0.34            # radio de llanta
TW = 0.24            # ancho de llanta
YB = 0.24            # fondo de la carrocería
WHEELS = [(WB, TRACK), (WB, -TRACK), (-WB, TRACK), (-WB, -TRACK)]


def _ss(a, b, x):
    k = min(1.0, max(0.0, (x - a) / (b - a)))
    return k * k * (3 - 2 * k)


def half_w(x):
    e = max(0.0, (abs(x) - 1.55) / 0.5)
    return 0.94 - 0.12 * e * e


def shoulder(x):
    if x > 0.9:
        return 0.96 - 0.22 * _ss(0.9, 2.05, x)
    return 0.98 - 0.03 * _ss(-1.2, -2.05, x)


def roof(x):
    """altura del techo; cab = 1 donde hay habitáculo"""
    ys = shoulder(x)
    if x > 0.8 or x < -1.98:
        return ys + 0.03, 0.0
    if x > 0.0:
        k = (0.8 - x) / 0.8
        return ys + (1.42 - ys) * math.sin(k * math.pi / 2) ** 0.8, k
    if x > -1.15:
        return 1.42, 1.0
    k = (x + 1.98) / 0.83
    return ys + (1.42 - ys) * math.sin(k * math.pi / 2) ** 0.6, max(0.3, k)


def section(x):
    w = half_w(x)
    ys = shoulder(x)
    yr, cab = roof(x)
    wr = w * 0.78 + (0.66 - w * 0.78) * min(1.0, cab * 1.5)
    yb = YB + 0.04 * _ss(1.6, 2.05, x) + 0.06 * _ss(-1.7, -2.05, x)
    pts = [(0.0, yb), (w - 0.10, yb), (w, yb + 0.14), (w, 0.50), (w, 0.62), (w, ys - 0.12), (w - 0.03, ys - 0.01),
           (w - 0.08, ys + 0.02), (wr + 0.02, yr - 0.05), (wr - 0.10, yr), (0.0, yr + 0.01)]
    return pts, cab


def livery(seg, x, y, cab, xm):
    if seg == 7 and cab > 0.25 and -1.70 < xm < 0.70:
        return GLASS, 'glass'
    if seg in (8, 9) and cab > 0.25 and (xm > 0.12 or xm < -1.25):
        return GLASS, 'glass'
    if seg in (8, 9) and cab > 0.25:
        return NAVY, 'body'
    if seg in (7,) and cab > 0.25:
        return BLACK, 'body'
    if y < 0.42:
        return NAVY, 'body'
    # franja diagonal naranja/azul en el costado
    if seg == 3 and -1.75 < xm < 1.85:
        return ORANGEC, 'body'
    if seg == 2 and -1.75 < xm < 1.85:
        return BLUEC, 'body'
    if seg in (8, 9) and xm > 1.0 and abs(xm - 1.5) < 0.18:
        return BLUEC, 'body'
    return WHITE, 'body'


def _orient(m, pts, col, tag, ref):
    p = [np.asarray(q, np.float64) for q in pts]
    n = np.cross(p[1] - p[0], p[2] - p[0])
    if np.linalg.norm(n) < 1e-9 and len(p) > 3:
        n = np.cross(p[2] - p[1], p[3] - p[1])
    nl = np.linalg.norm(n)
    if nl < 1e-9:
        return
    n = n / nl
    ctr = np.mean(p, 0)
    if n @ (ctr - ref) < 0:
        n = -n
        p = p[::-1]
    m.face(p, n, col, tag)


def build_body():
    m = mm.Model()
    xs = list(np.linspace(XR, XF, 34))
    secs = [section(x) for x in xs]
    for i in range(len(xs) - 1):
        (pa, ca), (pb, cb) = secs[i], secs[i + 1]
        xa, xb = xs[i], xs[i + 1]
        xm = (xa + xb) / 2
        cab = (ca + cb) / 2
        for s in (1, -1):
            for k in range(len(pa) - 1):
                q = [(xa, pa[k][1], s * pa[k][0]), (xa, pa[k + 1][1], s * pa[k + 1][0]),
                     (xb, pb[k + 1][1], s * pb[k + 1][0]), (xb, pb[k][1], s * pb[k][0])]
                ym = sum(v[1] for v in q) / 4
                col, tag = livery(k, xm, ym, cab, xm)
                _orient(m, q, col, tag, np.array([xm, 0.62, 0.0]))
    for (x, sgn) in ((XF, 1), (XR, -1)):
        pts, _ = section(x)
        full = [(x, y, z) for (z, y) in pts] + [(x, y, -z) for (z, y) in pts[::-1]]
        m.face(full, (sgn, 0, 0), WHITE if sgn > 0 else NAVY, 'body')
    # parrilla, faros, calaveras (calcomanías sobre las tapas)
    m.face([(XF + 0.012, 0.36, 0.55), (XF + 0.012, 0.36, -0.55), (XF + 0.012, 0.52, -0.55), (XF + 0.012, 0.52, 0.55)], (1, 0, 0), BLACK, 'body')
    for s in (1, -1):
        m.face([(XF + 0.014, 0.58, s * 0.78), (XF + 0.014, 0.58, s * 0.48), (XF + 0.014, 0.66, s * 0.46), (XF + 0.014, 0.66, s * 0.80)],
               (1, 0, 0), (250, 246, 220), 'lamp')
        m.face([(XR - 0.014, 0.80, s * 0.86), (XR - 0.014, 0.80, s * 0.56), (XR - 0.014, 0.90, s * 0.56), (XR - 0.014, 0.90, s * 0.86)],
               (-1, 0, 0), (220, 30, 30), 'tail')
    # alerón trasero
    m.box((-2.12, 1.40, -0.86), (-1.80, 1.44, 0.86), BLACK, 'wing')
    for s in (1, -1):
        m.box((-2.14, 1.26, s * 0.86 - 0.012), (-1.78, 1.50, s * 0.86 + 0.012), NAVY, 'wing')
        m.box((-1.98, 1.30, s * 0.40 - 0.02), (-1.92, 1.41, s * 0.40 + 0.02), BLACK, 'wing')
    # toma de aire del techo, espejos
    m.box((-0.55, 1.42, -0.12), (-0.15, 1.50, 0.12), NAVY, 'body')
    for s in (1, -1):
        m.box((0.62, 0.98, s * 0.92), (0.72, 1.08, s * 1.06), BLACK, 'body')
    # salpicaderas oscuras (arcos) y loderas
    for (wx, wz) in WHEELS:
        s = 1 if wz > 0 else -1
        z = s * (half_w(wx) + 0.012)
        ring_o = [(wx + 0.48 * math.cos(a), 0.34 + 0.48 * math.sin(a), z) for a in np.linspace(0, math.pi, 13)]
        ring_i = [(wx + 0.37 * math.cos(a), 0.34 + 0.37 * math.sin(a), z) for a in np.linspace(math.pi, 0, 13)]
        for j in range(12):
            q = [ring_o[j], ring_o[j + 1], ring_i[11 - j], ring_i[12 - j]]
            m.face(q, (0, 0, s), BLACK, 'arch')
        # hueco de la rueda (oscuro) para que no se vea la lámina detrás de la llanta
        hole = [(wx + 0.37 * math.cos(a), 0.34 + 0.37 * math.sin(a), z - s * 0.004) for a in np.linspace(0, math.pi, 13)]
        m.face(hole + [(wx - 0.37, YB, z - s * 0.004), (wx + 0.37, YB, z - s * 0.004)], (0, 0, s), (10, 10, 12), 'hole')
        if wx < 0:
            m.box((wx - 0.50, 0.08, s * 0.62 - 0.01 + (0 if s > 0 else -0.24)), (wx - 0.47, 0.42, s * 0.62 + 0.01 + (0.24 if s > 0 else 0)), BLACK, 'flap')
    # faros auxiliares (pod de rally nocturno) sobre el cofre
    for s in (-1.5, -0.5, 0.5, 1.5):
        m.cyl((1.98, 0.82, s * 0.2), (1, 0, 0), 0.085, 0.08, BLACK, 12, 'pod', True, (255, 250, 225))
    return m


def build_wheel():
    m = mm.Model()
    m.cyl((0, 0, 0), (0, 0, 1), RW, TW, TIRE, 22, 'tire', False)
    for s in (1, -1):
        # pared de la llanta (anillo negro) y rin blanco con 5 huecos
        ring_o = [(RW * math.cos(a), RW * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 23)]
        ring_i = [(0.22 * math.cos(a), 0.22 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 23)]
        z = s * TW / 2
        for j in range(22):
            q = [(ring_o[j][0], ring_o[j][1], z), (ring_o[j + 1][0], ring_o[j + 1][1], z), (ring_i[j + 1][0], ring_i[j + 1][1], z), (ring_i[j][0], ring_i[j][1], z)]
            _orient(m, q, (34, 34, 37), 'tire', np.array([0, 0, 0.0]))
        zr = z + s * 0.004
        disk = [(0.22 * math.cos(a), 0.22 * math.sin(a), zr) for a in np.linspace(0, 2 * math.pi, 19)[:-1]]
        _orient(m, disk, RIM, 'rim', np.array([0, 0, 0.0]))
        for k in range(5):
            a = 2 * math.pi * k / 5
            c0, s0 = math.cos(a), math.sin(a)
            hole = [((0.09 + 0.10 * u) * math.cos(a + v), (0.09 + 0.10 * u) * math.sin(a + v), zr + s * 0.004)
                    for (u, v) in ((0, -0.32), (1, -0.22), (1, 0.22), (0, 0.32))]
            _orient(m, hole, (70, 72, 78), 'rim', np.array([0, 0, 0.0]))
        hub = [(0.05 * math.cos(a), 0.05 * math.sin(a), zr + s * 0.006) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
        _orient(m, hub, (60, 62, 68), 'rim', np.array([0, 0, 0.0]))
    return m


def build_internals():
    m = mm.Model()
    # jaula de tubos (cromo-molibdeno)
    C = (232, 92, 40)
    r = 0.022
    def T(a, b, tag='cage'):
        tube(m, [np.array(a, float), np.array(b, float)], r, C if tag == 'cage' else (200, 200, 210), tag, sides=6, caps=False)
    hoop = [(-0.75, 0.30, 0.78), (-0.75, 1.30, 0.62), (-0.75, 1.36, 0.0), (-0.75, 1.30, -0.62), (-0.75, 0.30, -0.78)]
    for i in range(len(hoop) - 1):
        T(hoop[i], hoop[i + 1])
    for s in (1, -1):
        T((0.70, 0.40, s * 0.82), (0.15, 1.33, s * 0.60))       # pilar A
        T((0.15, 1.33, s * 0.60), (-0.75, 1.30, s * 0.62))      # techo
        T((-0.75, 1.30, s * 0.62), (-1.75, 0.70, s * 0.60))     # trasero
        T((0.70, 0.40, s * 0.82), (-0.75, 0.30, s * 0.78))      # piso
        T((0.70, 0.40, s * 0.82), (-0.75, 0.95, s * 0.80))      # X de puerta
        T((0.55, 0.95, s * 0.84), (-0.75, 0.35, s * 0.80))
        T((-0.75, 0.30, s * 0.78), (-1.75, 0.70, s * 0.60))
    T((0.15, 1.33, 0.60), (0.15, 1.33, -0.60))
    T((-0.75, 1.30, 0.62), (0.15, 1.33, -0.60))
    T((-0.75, 0.30, 0.78), (-0.75, 1.30, -0.62))
    T((0.62, 0.90, 0.84), (0.62, 0.90, -0.84))
    # motor, turbo, intercooler
    m.box((1.15, 0.36, -0.34), (1.80, 0.78, 0.30), (150, 154, 162), 'engine')
    m.box((1.20, 0.78, -0.30), (1.75, 0.86, 0.26), (60, 62, 68), 'engine')
    m.cyl((1.10, 0.62, 0.42), (0, 0, 1), 0.10, 0.12, (196, 120, 70), 14, 'turbo', True, (226, 150, 90))
    m.cyl((1.10, 0.62, 0.53), (0, 0, 1), 0.07, 0.10, (170, 176, 186), 12, 'turbo', True, (200, 204, 212))
    m.box((1.86, 0.36, -0.60), (1.94, 0.70, 0.60), (110, 116, 126), 'engine')
    # escape: del turbo hasta la salida trasera derecha
    path = catmull([np.array(p, float) for p in ((1.10, 0.52, 0.42), (0.95, 0.30, 0.40), (0.4, 0.22, 0.30), (-1.0, 0.22, 0.30),
                                                  (-1.7, 0.30, 0.45), (-2.08, 0.36, 0.52))], 6)
    tube(m, path, 0.045, (180, 120, 80), 'exhaust', sides=8)
    # tracción 4x4: diferenciales, flecha central y semiejes
    for x in (WB, 0.0, -WB):
        m.box((x - 0.12, 0.24, -0.12), (x + 0.12, 0.44, 0.12), (110, 112, 120), 'drive')
    tube(m, [np.array((WB, 0.34, 0.0)), np.array((-WB, 0.34, 0.0))], 0.035, (200, 204, 212), 'drive', sides=8)
    for (wx, wz) in WHEELS:
        tube(m, [np.array((wx, 0.34, 0.0)), np.array((wx, RW, wz * 0.82))], 0.03, (200, 204, 212), 'drive', sides=8)
    # amortiguadores
    for (wx, wz) in WHEELS:
        s = np.sign(wz)
        a, b = np.array((wx, RW + 0.02, wz * 0.78)), np.array((wx - 0.05 * np.sign(wx), 0.98, wz * 0.70))
        tube(m, [a, a + (b - a) * 0.55], 0.045, (230, 196, 60), 'shock', sides=8)
        tube(m, [a + (b - a) * 0.5, b], 0.028, (200, 204, 212), 'shock', sides=8)
    # asientos y tripulación
    for s, suit in ((1, (230, 230, 236)), (-1, (40, 90, 200))):
        z = s * 0.38
        m.box((-0.55, 0.30, z - 0.24), (0.05, 0.42, z + 0.24), (34, 34, 40), 'seat')
        m.box((-0.62, 0.30, z - 0.24), (-0.50, 1.20, z + 0.24), (34, 34, 40), 'seat')
        m.box((-0.50, 0.42, z - 0.16), (-0.30, 0.95, z + 0.16), suit, 'crew')
        m.box((-0.30, 0.42, z - 0.15), (0.30, 0.55, z + 0.15), suit, 'crew')
        blob(m, np.array((-0.38, 1.10, z)), (0.14, 0.15, 0.13), (250, 250, 252) if s < 0 else (230, 60, 40), 'crew', nu=12, nv=8)
    m.cyl((0.42, 0.85, -0.38), (1, -0.6, 0), 0.17, 0.04, (30, 30, 34), 14, 'crew')
    return m


BODY = build_body()
WHEEL = build_wheel()
INTERNALS = build_internals()


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def car_R(yaw, pitch=0.0, roll=0.0):
    """yaw: giro a la izquierda (+); pitch: nariz arriba (+); roll: alrededor de x"""
    c, s = math.cos(roll), math.sin(roll)
    Rx = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return rot_y(-yaw) @ rot_z(pitch) @ Rx
