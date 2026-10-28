"""Modelo 3D del Nissan Tsuru III (B13, 1992–2017) con medidas reales (metros): largo 4.32, ancho 1.64, alto 1.39,
distancia entre ejes 2.43. Carrocería por secciones (loft), cabina con cristales y pilares, llantas, faros y torreta de taxi.
También: Vocho sencillo y piezas internas para el escáner de rayos X (motor de 4 cilindros, tanque, asientos, volante).
El frente del auto mira a +x; y hacia arriba; z a lo ancho."""
import math
import numpy as np
from motor3d import Mesh, box, rbox, cyl, sphere, decal, mix, tex, font, draw_text

PINK = (222, 42, 128)
WHITE_P = (238, 238, 236)
GOLD = (200, 170, 110)
WINE = (140, 28, 40)
BLUE_ORION = (36, 62, 120)
GLASS = (26, 40, 58)
TIRE = (24, 24, 26)
RIM = (190, 192, 196)
CHROME = (205, 208, 212)
BUMP = (60, 62, 66)
HEAD = (236, 240, 230)
TAIL = (196, 30, 36)
AMBERL = (240, 150, 40)

SCHEMES = {
    'cdmx': dict(low=WHITE_P, top=PINK, cab=PINK),          # rosa y blanco (2014–2018)
    'dorado': dict(low=WINE, top=GOLD, cab=GOLD),            # dorado y guinda (2006–2012)
    'verde': dict(low=WHITE_P, top=(40, 120, 70), cab=WHITE_P),  # ecotaxi verde (años 2000)
    'orion': dict(low=BLUE_ORION, top=BLUE_ORION, cab=BLUE_ORION),  # Buen Camino (último, 2017)
    'blanco': dict(low=WHITE_P, top=WHITE_P, cab=WHITE_P),
    'gris': dict(low=(150, 152, 156), top=(150, 152, 156), cab=(150, 152, 156)),  # lámina sin pintar (planta)
}


def _fix(V, F, center_fn):
    """Orienta cada cara hacia afuera (respecto a un eje interior)."""
    out = []
    for f in F:
        P = V[list(f)]
        n = np.cross(P[1] - P[0], P[2] - P[0])
        if np.linalg.norm(n) < 1e-12 and len(f) > 3:
            n = np.cross(P[2] - P[0], P[3] - P[0])
        c = P.mean(0)
        if n @ (c - center_fn(c)) < 0:
            f = tuple(reversed(f))
        out.append(tuple(f))
    return out


def loft(stations, colfn, caps=True, shadow=0.0, gloss=0.35, cy0=None):
    """stations: [(x, [(z, y), ...]), ...] con el mismo número de puntos (polígono cerrado).
    colfn(i_station, j_lado) -> color de la cara entre la estación i e i+1 en el lado j."""
    K = len(stations[0][1])
    V = []
    for x, sec in stations:
        V += [(x, y, z) for z, y in sec]
    V = np.array(V, float)
    F, C = [], []
    for i in range(len(stations) - 1):
        for j in range(K):
            a, b = i * K + j, i * K + (j + 1) % K
            F.append((a, b, b + K, a + K))
            C.append(colfn(i, j))
    cy = {i: np.mean([p[1] for p in stations[i][1]]) for i in range(len(stations))}
    if caps:
        for i in (0, len(stations) - 1):
            F.append(tuple(range(i * K, i * K + K)))
            C.append(colfn(min(i, len(stations) - 2), -1))
    xs = np.array([s[0] for s in stations])

    def center(c):
        k = int(np.argmin(abs(xs - c[0])))
        return np.array([c[0], cy[k], 0.0]) if abs(c[0] - xs[0]) > 1e-6 and abs(c[0] - xs[-1]) > 1e-6 else np.array([np.mean(xs), cy[k], 0.0])
    if cy0 is not None:
        center = lambda c: np.array([c[0], cy0, 0.0])
    F = _fix(V, F, center)
    m = Mesh(V, F, C, shadow=shadow, gloss=gloss)
    m.sh_r = 2.2
    return m


# carrocería baja: (x, y_piso, y_arriba, medio ancho)
LOW = [(2.16, 0.32, 0.60, 0.74), (2.10, 0.26, 0.70, 0.79), (1.95, 0.24, 0.76, 0.81), (1.55, 0.24, 0.80, 0.82),
       (1.15, 0.24, 0.83, 0.82), (0.80, 0.24, 0.86, 0.82), (0.40, 0.24, 0.87, 0.82), (0.0, 0.24, 0.87, 0.82),
       (-0.4, 0.24, 0.88, 0.82), (-0.9, 0.24, 0.89, 0.82), (-1.38, 0.24, 0.91, 0.82), (-1.75, 0.25, 0.92, 0.81),
       (-2.05, 0.27, 0.90, 0.80), (-2.16, 0.33, 0.84, 0.76)]
WHEELS_X = (1.30, -1.13)


def low_stations():
    """Estaciones de la carrocería baja con los pasos de rueda recortados (arco de radio 0.42)."""
    L = np.array(LOW)
    xs = set(np.round(L[:, 0], 3))
    for xc in WHEELS_X:
        for u in np.linspace(-0.42, 0.42, 9):
            xs.add(round(xc + u, 3))
    out = []
    for x in sorted(xs, reverse=True):
        y0 = np.interp(-x, -L[:, 0], L[:, 1])
        y1 = np.interp(-x, -L[:, 0], L[:, 2])
        hw = np.interp(-x, -L[:, 0], L[:, 3])
        for xc in WHEELS_X:
            u = x - xc
            if abs(u) < 0.42:
                y0 = max(y0, 0.30 + math.sqrt(0.42 ** 2 - u * u) * 0.86)
        out.append((x, y0, y1, hw))
    return out


# cabina: (x, y_base, y_techo, medio ancho abajo, medio ancho arriba, tipo de lado, tipo de techo)
CAB = [(0.80, 0.86, 0.875, 0.80, 0.70, 'g', 'g'), (0.0, 0.87, 1.37, 0.80, 0.64, 'b', 'r'), (-0.16, 0.87, 1.38, 0.80, 0.64, 'g', 'r'),
       (-0.30, 0.875, 1.38, 0.80, 0.64, 'g', 'r'), (-0.86, 0.89, 1.37, 0.81, 0.64, 'b', 'g'), (-1.40, 0.91, 0.92, 0.81, 0.70, 'g', 'g')]


def body(scheme='cdmx', open_=0.0):
    S = SCHEMES[scheme]
    st = []
    for x, y0, y1, hw in low_stations():
        sh = min(0.06, (y1 - y0) * 0.2)
        sec = [(-hw + 0.04, y0), (hw - 0.04, y0), (hw, y0 + 0.12), (hw, y1 - sh), (hw - 0.07, y1), (-hw + 0.07, y1), (-hw, y1 - sh), (-hw, y0 + 0.12)]
        st.append((x, sec))
    stripe = 0.66  # línea de color (CDMX: arriba rosa)

    def lowcol(i, j):
        if j == 0:
            return (30, 30, 32)
        if j in (4,):
            return S['top']
        if j in (3, 5):
            return S['top'] if scheme == 'cdmx' else S['low']
        if j == -1:
            return S['low']
        return S['low']
    lo = loft(st, lowcol, shadow=0.45, gloss=0.45)
    cs = []
    for x, yb, yt, hb, ht, _, _ in CAB:
        cs.append((x, [(-hb, yb), (hb, yb), (ht, yt), (-ht, yt)]))

    def cabcol(i, j):
        side, top = CAB[i][5], CAB[i][6]
        if j in (1, 3):
            return GLASS if side == 'g' else S['cab']
        if j == 2:
            return GLASS if top == 'g' else S['cab']
        return S['cab']
    ca = loft(cs, cabcol, caps=False, shadow=0.0, gloss=0.55, cy0=0.5)
    return [lo, ca]


def wheel(x, z, spin=0.0, r=0.30, w=0.19):
    s = 1 if z > 0 else -1
    t = cyl(r, w, TIRE, n=22, shadow=0.0, gloss=0.1, y0=-w / 2).tf(rx=90).tf(t=(x, r, z))
    rim = cyl(r * 0.62, 0.02, RIM, n=18, shadow=0.0, gloss=0.8, y0=-0.01).tf(rx=90).tf(t=(x, r, z + s * (w / 2 + 0.005)))
    hub = cyl(r * 0.16, 0.02, (120, 122, 126), n=8, shadow=0.0, gloss=0.5, y0=-0.01).tf(rx=90).tf(t=(x, r, z + s * (w / 2 + 0.02)))
    ms = [t, rim, hub]
    # rayos del rin (giran)
    for k in range(5):
        a = spin + k * 72
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        sp = box(r * 0.5, 0.035, 0.012, (150, 152, 156), shadow=0.0, base=False, edge=False).tf(rz=a).tf(
            t=(x + ca * r * 0.32, r + sa * r * 0.32, z + s * (w / 2 + 0.015)))
        ms.append(sp)
    return ms


def taxi_sign(scheme='cdmx'):
    m = box(0.42, 0.12, 0.16, (245, 245, 240), shadow=0.0, base=True, gloss=0.4)
    im = tex(240, 70, (245, 245, 240), lambda d, im: draw_text(d, (120, 36), 'TAXI', font('xb', 46), (20, 20, 22), 'mm'))
    decal(m, m.FACE['front'], im)
    decal(m, m.FACE['back'], im)
    return m.tf(ry=90).tf(t=(-0.42, 1.385, 0))


def tsuru(scheme='cdmx', spin=0.0, taxi=True, lights=0.0, parts=True):
    """Lista de mallas del Tsuru completo (frente hacia +x)."""
    ms = body(scheme)
    if not parts:
        return ms
    for x in (1.30, -1.13):
        for z in (0.73, -0.73):
            ms += wheel(x, z, spin)
    # faros, parrilla, defensas, calaveras
    hl = mix(HEAD, (255, 250, 210), lights)
    for z in (0.52, -0.52):
        ms.append(box(0.04, 0.12, 0.34, hl, shadow=0.0, base=True, gloss=0.9).tf(t=(2.12, 0.58, z)))
        ms.append(box(0.04, 0.05, 0.08, AMBERL, shadow=0.0, base=True, gloss=0.6).tf(t=(2.12, 0.58, z * 1.44)))
        ms.append(box(0.04, 0.13, 0.36, TAIL, shadow=0.0, base=True, gloss=0.8).tf(t=(-2.15, 0.64, z * 1.05)))
    ms.append(box(0.04, 0.1, 0.62, (40, 42, 46), shadow=0.0, base=True, gloss=0.3).tf(t=(2.13, 0.59, 0)))
    ms.append(box(0.03, 0.05, 0.05, CHROME, shadow=0.0, base=True, gloss=0.9).tf(t=(2.155, 0.615, 0)))
    ms.append(box(0.12, 0.16, 1.56, BUMP, shadow=0.0, base=True, gloss=0.3).tf(t=(2.16, 0.30, 0)))
    ms.append(box(0.12, 0.16, 1.56, BUMP, shadow=0.0, base=True, gloss=0.3).tf(t=(-2.18, 0.34, 0)))
    pl = tex(200, 100, (250, 250, 250), lambda d, im: draw_text(d, (100, 52), 'A 2363 K', font('b', 30), (20, 20, 22), 'mm'))
    p = box(0.02, 0.11, 0.32, (250, 250, 250), shadow=0.0, base=True)
    decal(p, p.FACE['right'], pl)
    ms.append(p.tf(t=(-2.245, 0.36, 0)))
    for z in (0.83, -0.83):  # espejos y manijas
        ms.append(box(0.1, 0.1, 0.1, BUMP, shadow=0.0, base=True, gloss=0.4).tf(t=(0.68, 0.92, z)))
        for x in (0.25, -0.55):
            ms.append(box(0.14, 0.03, 0.02, (60, 60, 64), shadow=0.0, base=True).tf(t=(x, 0.76, z)))
    if taxi:
        ms.append(taxi_sign(scheme))
    return ms


def place(ms, x=0.0, z=0.0, y=0.0, ry=0.0, s=1.0):
    return [m.tf(s=s).tf(ry=ry, t=(x, y, z)) for m in ms]


# ------------------------------------------------------------------ vocho (Volkswagen Sedán) simplificado
def vocho(col=(70, 150, 90), spin=0.0, taxi=True):
    ms = []
    b = sphere(1.0, col, nu=26, nv=14, shadow=0.45, gloss=0.6).tf(s=(2.0, 0.78, 0.78), t=(0, 0.45, 0))
    b.V[:, 1] = np.maximum(b.V[:, 1], 0.32)
    ms.append(b)
    c = sphere(1.0, GLASS, nu=22, nv=12, shadow=0.0, gloss=0.7).tf(s=(1.05, 0.52, 0.68), t=(-0.15, 0.95, 0))
    c.V[:, 1] = np.maximum(c.V[:, 1], 0.95)
    ms.append(c)
    r = sphere(1.0, col, nu=22, nv=12, shadow=0.0, gloss=0.6).tf(s=(0.9, 0.5, 0.62), t=(-0.2, 1.0, 0))
    r.V[:, 1] = np.maximum(r.V[:, 1], 1.0)
    ms.append(r)
    for x in (1.2, -1.2):
        for z in (0.68, -0.68):
            ms += wheel(x, z, spin, r=0.3, w=0.17)
    for z in (0.45, -0.45):
        ms.append(sphere(0.09, HEAD, nu=10, nv=6, shadow=0.0, gloss=0.9).tf(t=(1.65, 0.72, z)))
    if taxi:
        ms.append(box(0.3, 0.1, 0.12, (245, 245, 240), shadow=0.0).tf(ry=90).tf(t=(-0.1, 1.5, 0)))
    return ms


# ------------------------------------------------------------------ piezas internas (rayos X)
ENG = (176, 180, 188)
BLOCK = (120, 126, 136)
PISTON = (210, 212, 216)
SEAT = (70, 74, 86)
TANK = (90, 96, 104)


def engine(t=0.0, x=1.45, y=0.42, s=1.0, cut=True):
    """Motor de 4 cilindros en línea (1.6 L): bloque, cabeza, 4 pistones subiendo y bajando, cárter y transmisión."""
    ms = []
    ms.append(box(0.62, 0.32, 0.42, BLOCK, shadow=0.0, base=True, gloss=0.3, edge=True).tf(t=(0, 0, 0)))
    ms.append(box(0.66, 0.1, 0.36, ENG, shadow=0.0, base=True, gloss=0.5, edge=True).tf(t=(0, 0.5, 0)))
    ms.append(box(0.58, 0.12, 0.38, (60, 64, 72), shadow=0.0, base=True, gloss=0.2).tf(t=(0, -0.12, 0)))
    for k in range(4):
        ph = t * 9 + (0, math.pi, math.pi, 0)[k]
        py = 0.3 + 0.07 * math.cos(ph)
        zc = -0.22 + k * 0.147
        ms.append(cyl(0.06, 0.08, PISTON, n=14, shadow=0.0, gloss=0.8).tf(t=(0, py, zc)))
        ms.append(box(0.03, 0.26, 0.03, (150, 150, 156), shadow=0.0, base=True).tf(t=(0, py - 0.24, zc)))
    ms.append(cyl(0.16, 0.34, (100, 104, 112), n=16, shadow=0.0, gloss=0.4, y0=0).tf(rx=90).tf(t=(-0.05, 0.12, -0.36)))
    return [m.tf(s=s).tf(ry=90, t=(x, y, 0)) for m in ms]


def interior(scheme='cdmx'):
    ms = []
    for x in (0.05, -0.75):
        for z in (0.36, -0.36):
            ms.append(box(0.46, 0.14, 0.46, SEAT, shadow=0.0, base=True, gloss=0.2).tf(t=(x, 0.42, z)))
            ms.append(box(0.12, 0.55, 0.46, SEAT, shadow=0.0, base=True, gloss=0.2).tf(rz=10).tf(t=(x - 0.24, 0.5, z)))
    ms.append(box(0.3, 0.2, 1.5, (40, 42, 48), shadow=0.0, base=True, gloss=0.2).tf(t=(0.75, 0.72, 0)))  # tablero
    sw = cyl(0.17, 0.03, (30, 30, 34), n=18, shadow=0.0, gloss=0.4, y0=-0.015).tf(rz=65).tf(t=(0.55, 0.92, 0.36))
    ms.append(sw)
    ms.append(box(0.6, 0.22, 1.0, TANK, shadow=0.0, base=True, gloss=0.3, edge=True).tf(t=(-1.3, 0.3, 0)))
    ms.append(cyl(0.035, 3.0, (110, 110, 116), n=8, shadow=0.0).tf(rz=90).tf(t=(1.5, 0.26, -0.2)))  # escape
    return ms


def brake(x, z, abs_=False):
    """Disco y caliper de freno (sin ABS: sin sensor ni anillo dentado)."""
    s = 1 if z > 0 else -1
    d = cyl(0.2, 0.025, (150, 140, 135), n=20, shadow=0.0, gloss=0.6, y0=-0.0125).tf(rx=90).tf(t=(x, 0.30, z - s * 0.12))
    c = box(0.1, 0.12, 0.06, (200, 60, 40), shadow=0.0, base=False).tf(t=(x + 0.12, 0.38, z - s * 0.12))
    return [d, c]
