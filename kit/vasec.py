"""Mente en órbita — ¿Cómo funciona una vasectomía? (video 9, estilo lámina anatómica).
Escenas: charola quirúrgica (conducto vs espagueti, tijera) · modelo anatómico translúcido · testículo en corte ·
viaje por el conducto deferente · próstata y vesículas seminales · tubo de ensayo (composición del semen) ·
consultorio · procedimiento sin bisturí (esquema) · después: los espermatozoides ya no pasan · hormonas y semen ·
laboratorio (análisis a los 3 meses) · efectividad y aviso de ITS · hospital · cierre."""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
from nc import proj, P2, vis
from fo import clip_near, line3
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of, VIOLET, BLUE, CYAN, ORANGE)
from gps_geo import (norm, cam_from, cam_keys, polyline3, glow_dot)
import gps_earth as ge
import moto_model as mm

FPS = 24
RED = (255, 90, 90)
GREEN = (90, 255, 150)
GOLD = (255, 205, 100)
SPERM = (235, 245, 255)

PHR = [
    (0.3, 5.9, "Dos tubitos del grosor de un espagueti... si se cortan, un hombre deja de ser fértil.", {6, 9}),
    (6.4, 8.2, "Así funciona la vasectomía.", {3}),
    (8.7, 12.2, "Los testículos fabrican más de mil espermatozoides por segundo.", {5}),
    (12.7, 16.6, "Salen por el conducto deferente, un tubo de unos 30 centímetros.", {3}),
    (17.1, 21.2, "Y se mezclan con líquidos de la próstata y las vesículas seminales.", {7, 10}),
    (21.7, 26.2, "Ese líquido es casi todo el semen; los espermatozoides son menos del 5%.", {12}),
    (26.7, 30.9, "Con anestesia local y sin bisturí, el médico hace una abertura diminuta...", {5}),
    (31.4, 35.3, "corta cada conducto y sella las puntas. Toma unos 15 minutos.", {0, 4}),
    (35.8, 39.6, "Los espermatozoides ya no pueden pasar, y el cuerpo los reabsorbe.", {10}),
    (40.1, 43.8, "Las hormonas no cambian y el semen se ve casi igual.", {3}),
    (44.3, 49.8, "Ojo: no funciona de inmediato. Hay que esperar unos tres meses y hacer un análisis.", {4, 14}),
    (50.3, 55.0, "Funciona en más del 99%, pero no protege contra infecciones de transmisión sexual.", {4, 7}),
    (55.5, 59.4, "Se considera permanente, y en México el IMSS la hace gratis.", {2, 10}),
    (59.9, 61.9, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)
_ST = [list(ph['starts']) for ph in anim.PH]


def WT(i, w):
    return _ST[i][w]


DUR = 63.1
NF = int(DUR * FPS)
CUTS = (6.15, 8.45, 12.45, 16.85, 21.45, 26.45, 31.15, 35.55, 39.85, 44.05, 50.05, 55.25)
ENVS = ('hook', 'anat', 'testis', 'path', 'glands', 'tube', 'clinic', 'proc', 'after', 'hormone', 'lab', 'stats', 'hosp')
T_OUT = 59.6


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


# =====================================================================
# Geometría: curvas, tubos y "blobs" orgánicos
# =====================================================================
def catmull(pts, n_per=8):
    Pp = [np.asarray(p, np.float64) for p in pts]
    Pp = [Pp[0]] + Pp + [Pp[-1]]
    out = []
    for i in range(1, len(Pp) - 2):
        p0, p1, p2, p3 = Pp[i - 1], Pp[i], Pp[i + 1], Pp[i + 2]
        for u in np.linspace(0, 1, n_per, endpoint=False):
            u2, u3 = u * u, u * u * u
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
    out.append(Pp[-2])
    return np.array(out)


def arclen(path):
    d = np.linalg.norm(np.diff(path, axis=0), axis=1)
    return np.concatenate([[0], np.cumsum(d)])


def at_s(path, cum, s):
    s = np.clip(s, 0, cum[-1])
    i = np.clip(np.searchsorted(cum, s) - 1, 0, len(path) - 2)
    f = ((s - cum[i]) / np.maximum(cum[i + 1] - cum[i], 1e-9))[..., None]
    return path[i] * (1 - f) + path[i + 1] * f


def tube(m, path, r, col, tag, sides=10, r_fn=None, caps=True, cap_col=None, s_range=None):
    n = len(path)
    T = np.gradient(path, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    a = np.array([0.0, 0.0, 1.0]) if abs(T[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    N = [norm(np.cross(T[0], a))]
    for i in range(1, n):
        v = N[-1] - T[i] * (N[-1] @ T[i])
        N.append(norm(v) if np.linalg.norm(v) > 1e-9 else N[-1])
    N = np.array(N)
    Bn = np.cross(T, N)
    cum = arclen(path)
    rings = []
    for i in range(n):
        rr = r * (r_fn(i / (n - 1)) if r_fn else 1.0)
        rings.append([path[i] + rr * (math.cos(2 * math.pi * k / sides) * N[i] + math.sin(2 * math.pi * k / sides) * Bn[i]) for k in range(sides)])
    for i in range(n - 1):
        if s_range is not None:
            sm = 0.5 * (cum[i] + cum[i + 1])
            if not any(lo <= sm <= hi for (lo, hi) in s_range):
                continue
        for k in range(sides):
            k2 = (k + 1) % sides
            am = 2 * math.pi * (k + 0.5) / sides
            nn = math.cos(am) * (N[i] + N[i + 1]) / 2 + math.sin(am) * (Bn[i] + Bn[i + 1]) / 2
            m.face([rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]], norm(nn), col, tag)
    if caps:
        m.face(rings[0][::-1], -T[0], cap_col or col, tag)
        m.face(rings[-1], T[-1], cap_col or col, tag)
    return rings


def blob(m, ctr, radii, col, tag, Rm=np.eye(3), nu=26, nv=16, bump=None, keep=None):
    ctr = np.asarray(ctr, np.float64)
    rx, ry, rz = radii

    def pt(u, v):
        k = 1.0 + (bump(u, v) if bump else 0.0)
        p = np.array([rx * math.sin(v) * math.cos(u), ry * math.cos(v), rz * math.sin(v) * math.sin(u)]) * k
        g = np.array([p[0] / rx ** 2, p[1] / ry ** 2, p[2] / rz ** 2])
        return ctr + Rm @ p, norm(Rm @ g), p

    for i in range(nv):
        v0, v1 = math.pi * i / nv, math.pi * (i + 1) / nv
        for j in range(nu):
            u0, u1 = 2 * math.pi * j / nu, 2 * math.pi * (j + 1) / nu
            a, na, pa = pt(u0, v0)
            b, nb, pb = pt(u1, v0)
            c_, nc_, pc = pt(u1, v1)
            d, nd, pd = pt(u0, v1)
            if keep is not None and not keep((pa + pb + pc + pd) / 4):
                continue
            nn = norm(na + nb + nc_ + nd)
            pts = [a, b, c_, d] if i > 0 else [a, c_, d]
            if i == nv - 1:
                pts = [a, b, c_]
            m.face(pts, nn, col, tag)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])


# =====================================================================
# Modelo anatómico (cm). x lateral, y arriba, z hacia atrás (la cámara ve el frente desde -z)
# =====================================================================
C_TESTIS = (236, 204, 196)
C_EPI = (196, 112, 112)
C_VAS = (238, 228, 204)
C_PROS = (214, 128, 116)
C_VES = (224, 176, 150)
C_BLAD = (236, 214, 140)
C_URE = (228, 186, 176)
C_ART = (214, 64, 60)
C_VEIN = (70, 96, 196)
TESTIS_C = [np.array([s * 2.4, -9.0, -1.2]) for s in (1, -1)]


def vas_ctrl(s):
    return [(s * 2.8, -11.0, 0.1), (s * 2.2, -9.8, 0.7), (s * 2.3, -7.2, 0.4), (s * 3.0, -4.6, -0.5), (s * 4.3, -1.6, -1.1),
            (s * 5.8, 1.6, -0.7), (s * 6.4, 4.6, 1.2), (s * 5.6, 7.6, 3.8), (s * 3.9, 7.4, 6.2), (s * 2.3, 5.2, 6.6),
            (s * 1.4, 3.4, 5.6), (s * 0.7, 2.3, 4.4), (0.0, 1.5, 3.4)]


VAS = [catmull(vas_ctrl(s), 10) for s in (1, -1)]
VAS_CUM = [arclen(p) for p in VAS]
VAS_LEN = VAS_CUM[0][-1]
# punto del corte: en el cordón, arriba del testículo
_cut_i = int(np.argmin(np.abs(VAS[0][:, 1] - (-5.4))))
S_CUT = VAS_CUM[0][_cut_i]
GAP = 0.9


def epi_ctrl(s):
    return [(s * 2.9, -6.8, -0.2), (s * 3.55, -7.6, 0.4), (s * 3.6, -9.2, 0.6), (s * 3.3, -10.6, 0.5), (s * 2.8, -11.0, 0.1)]


EPI = [catmull(epi_ctrl(s), 8) for s in (1, -1)]
URETHRA = catmull([(0, 3.6, 3.0), (0, 1.6, 3.2), (0, -0.4, 2.6), (0, -2.0, 1.0), (0, -3.0, -1.2), (0, -3.8, -3.2)], 8)


def cord_vessel(s, off, top):
    pts = vas_ctrl(s)[2:6]
    pts = [(p[0] + s * off[0], p[1] + off[1], p[2] + off[2]) for p in pts]
    return catmull([(s * 2.2, -7.0, -0.9)] + pts + [(s * 6.3, 4.0, -0.4), (s * 5.8, 9.0, 2.0), (s * 4.6, top, 4.0)], 8)


ARTS = [cord_vessel(s, (0.45, 0.0, -0.35), 14.0) for s in (1, -1)]
VEINS = [cord_vessel(s, (-0.35, 0.1, -0.5), 14.5) for s in (1, -1)]
VEIN_CUM = [arclen(p) for p in VEINS]


def build_anatomy(cut=False):
    m = mm.Model()
    rng = np.random.RandomState(3)
    blob(m, (0, 7.0, 2.6), (4.6, 4.2, 4.0), C_BLAD, 'bladder', nu=28, nv=16)
    blob(m, (0, 1.6, 3.2), (2.0, 1.5, 1.6), C_PROS, 'prostate', nu=22, nv=12)
    for s in (1, -1):
        Rv = rot_z(s * math.radians(32))
        blob(m, (s * 2.7, 3.6, 5.8), (2.4, 0.78, 0.8), C_VES, 'ves', Rv, nu=26, nv=10,
             bump=lambda u, v: 0.13 * math.sin(7 * u) * math.sin(3 * v + 0.7))
        Rt = rot_x(math.radians(-12))
        blob(m, TESTIS_C[0] * np.array([s, 1, 1]), (1.5, 2.2, 1.4), C_TESTIS, 'testis', Rt, nu=24, nv=14)
    for k, s in enumerate((1, -1)):
        tube(m, EPI[k], 0.5, C_EPI, 'epi', 10, r_fn=lambda u: 1.15 - 0.45 * u)
        if cut:
            tube(m, VAS[k], 0.24, C_VAS, 'vas', 10, caps=False, s_range=[(0, S_CUT - GAP / 2), (S_CUT + GAP / 2, 1e9)])
        else:
            tube(m, VAS[k], 0.24, C_VAS, 'vas', 10, caps=False)
        tube(m, ARTS[k], 0.11, C_ART, 'art', 6, caps=False)
        tube(m, VEINS[k], 0.16, C_VEIN, 'vein', 6, caps=False)
    tube(m, URETHRA, 0.34, C_URE, 'urethra', 10, caps=False)
    return m


ANAT = build_anatomy(False)
ANAT_CUT = build_anatomy(True)


def build_body():
    """silueta translúcida tipo maniquí (solo contorno brillante)"""
    m = mm.Model()
    rings = []
    ys = np.linspace(24, -2.5, 12)
    for y in ys:
        rx = 14.2 + 2.8 * math.exp(-((y - 5.0) / 9.0) ** 2) - 2.5 * max(0, (-y - 0.5) / 2.0)
        rf, rb = 9.0, 11.5 + 1.5 * math.exp(-((y - 2.0) / 6.0) ** 2)
        ring = []
        for k in range(28):
            a = 2 * math.pi * k / 28
            z = 2.5 + (rb if math.sin(a) > 0 else rf) * math.sin(a)
            ring.append((rx * math.cos(a), y, z))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(28):
            k2 = (k + 1) % 28
            pts = [rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]]
            ctr = np.mean(pts, axis=0)
            nn = norm(np.array([ctr[0], 0, ctr[2] - 2.5]))
            m.face(pts, nn, (0, 0, 0), 'body')
    for s in (1, -1):
        path = catmull([(s * 8.0, 2.0, 2.6), (s * 8.2, -12, 2.4), (s * 7.9, -30, 2.0)], 6)
        tube(m, path, 7.4, (0, 0, 0), 'body', 26, r_fn=lambda u: 1.0 - 0.18 * u, caps=False)
    blob(m, (0, -9.4, -0.9), (5.0, 3.5, 3.0), (0, 0, 0), 'scrot', nu=24, nv=12)
    return m


BODY = build_body()


# =====================================================================
# Sombreado con brillo especular (aspecto de lámina médica)
# =====================================================================
def org_faces(c, model, L, styles=None, pos=(0, 0, 0), Rm=np.eye(3), near=0.3, default=None):
    """styles: tag -> dict(dim, alpha, spec, col)"""
    out = []
    pos = np.asarray(pos, np.float64)
    cam = np.asarray(c['pos'])
    L = np.asarray(L)
    for (pts, n, col, tag) in model.F:
        st = (styles or {}).get(tag, default or {})
        if st.get('hide'):
            continue
        Wp = pts @ Rm.T + pos
        nw = Rm @ n
        ctr = Wp.mean(0)
        V = cam - ctr
        dv = np.linalg.norm(V)
        V = V / dv
        if nw @ V <= 0:
            continue
        q = clip_near([tuple(p) for p in Wp], c, near)
        if len(q) < 3:
            continue
        dep = proj(*ctr, c)[2]
        cc = st.get('col', col)
        dim = st.get('dim', 1.0)
        d = max(0.0, nw @ L)
        hh = norm(L + V)
        sp = max(0.0, nw @ hh) ** 28 * st.get('spec', 0.35)
        rim = (1 - max(0.0, nw @ V)) ** 3 * 0.25
        k = (0.36 + 0.72 * d) * dim
        colr = tuple(int(min(255, cc[i] * k + 255 * sp * dim + cc[i] * rim)) for i in range(3))
        al = st.get('alpha')
        out.append((dep, [P2(*p, c) for p in q], colr, al, tag))
    return out


BG_TAGS = ('floor', 'wall')


def draw_faces(bd, od, fl):
    fl.sort(key=lambda q: (0 if q[4] in BG_TAGS else 1, -q[0]))
    for dep, pts, col, al, tag in fl:
        if al is None:
            bd.polygon(pts, fill=col)
        else:
            od.polygon(pts, fill=(*col, al))


def glass(la, c, model, col, k=1.0, tags=None):
    """contorno translúcido brillante (efecto fresnel) en la capa de luz"""
    cam = np.asarray(c['pos'])
    items = []
    for (pts, n, _, tag) in model.F:
        if tags and tag not in tags:
            continue
        ctr = pts.mean(0)
        V = cam - ctr
        V = V / np.linalg.norm(V)
        nv = n @ V
        if nv <= 0:
            continue
        q = clip_near([tuple(p) for p in pts], c, 0.5)
        if len(q) < 3:
            continue
        f = (1 - nv) ** 2.6
        dep = proj(*ctr, c)[2]
        items.append((dep, [P2(*p, c) for p in q], sc3(col, k * (0.05 + 0.95 * f))))
    items.sort(key=lambda q: -q[0])
    for dep, pts, cc in items:
        la.polygon(pts, fill=cc)


def bg_studio(top=(10, 16, 34), bot=(4, 6, 14), spot=(28, 44, 70)):
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        arr[..., i] = top[i] * (1 - yy) + bot[i] * yy
    d = np.sqrt(xx ** 2 * 0.8 + (yy - 0.48) ** 2 * 2.2)
    g = np.clip(1 - d, 0, 1) ** 2
    for i in range(3):
        arr[..., i] += spot[i] * g
    return arr


BG_ANAT = bg_studio()


def particles_on(la, c, path, cum, s_arr, col, r, a, occl=None):
    if a <= 0.01:
        return []
    Pp = at_s(path, cum, s_arr)
    out = []
    for p in Pp:
        x, y, dep = proj(*p, c)
        if dep < 0.3:
            continue
        glow_dot(la, x * S, y * S, r * S, col, a)
        out.append((x, y))
    return out


def sperm_flow(t, n, speed, cum_end, phase=0.0, stop=None, t_stop=None):
    """posiciones s de n partículas que viajan por un tubo"""
    s = (np.arange(n) / n * cum_end + speed * t + phase) % cum_end
    return s


ANAT_L = norm((-0.45, 0.65, -0.6))
STY_BASE = {'bladder': {'alpha': 110, 'spec': 0.25}, 'vas': {'spec': 0.5}}


def anat_styles(focus=None, dim_others=0.45, cut=False):
    st = {'bladder': {'alpha': 110, 'spec': 0.25}}
    if focus:
        for tag in ('bladder', 'prostate', 'ves', 'testis', 'epi', 'vas', 'art', 'vein', 'urethra'):
            if tag not in focus:
                d = dict(st.get(tag, {}))
                d['dim'] = dim_others
                st[tag] = d
    return st


def draw_anatomy(base, bd, od, la, c, t, model=None, styles=None, body_k=1.0):
    glass(la, c, BODY, (120, 190, 255), 0.55 * body_k, ('body',))
    glass(la, c, BODY, (255, 190, 170), 0.35 * body_k, ('scrot',))
    fl = org_faces(c, model or ANAT, ANAT_L, styles or STY_BASE)
    draw_faces(bd, od, fl)


# =====================================================================
# Testículo en corte (cm, mismo marco)
# =====================================================================
def build_testis_cut():
    m = mm.Model()
    ctr = TESTIS_C[0]
    Rt = rot_x(math.radians(-12))
    blob(m, ctr, (1.5, 2.2, 1.4), C_TESTIS, 'testis', Rt, nu=30, nv=18, keep=lambda p: p[2] > 0.0)
    # cara del corte (plano z local = 0)
    pts = []
    for k in range(40):
        a = 2 * math.pi * k / 40
        pts.append(ctr + Rt @ np.array([1.47 * math.cos(a), 2.17 * math.sin(a), 0.0]))
    m.face(pts, Rt @ np.array([0, 0, -1.0]), (232, 168, 160), 'cutface')
    tube(m, EPI[0], 0.5, C_EPI, 'epi', 12, r_fn=lambda u: 1.15 - 0.45 * u)
    tube(m, VAS[0][:60], 0.24, C_VAS, 'vas', 10)
    return m, ctr, Rt


TCUT, TC_CTR, TC_R = build_testis_cut()


def _tubules():
    """túbulos seminíferos: espirales en lóbulos sobre la cara del corte"""
    out = []
    rs = np.random.RandomState(8)
    for lob in range(9):
        a0 = -math.pi / 2 + (lob - 4) * 0.32
        coil = []
        for k in range(70):
            u = k / 69
            rr = 0.25 + 1.05 * u
            a = a0 + 0.12 * math.sin(u * 26 + lob)
            x = rr * math.cos(a) * 1.3
            y = rr * math.sin(a) * 1.9 * 0.95 + 0.0
            coil.append(np.array([x * 0.95, -y * 0.9 * -1.0, -0.02]))
        out.append(coil)
    return out


TUB = []
for _lob in range(11):
    a0 = math.radians(200 + _lob * 14)
    pts = []
    for k in range(80):
        u = k / 79
        rr = 1.3 * (1 - u) + 0.15
        wig = 0.09 * math.sin(u * 40 + _lob * 1.7)
        a = a0 + wig * 2.0
        pts.append(TC_CTR + TC_R @ np.array([(rr + wig) * math.cos(a) * 1.0, (rr + wig) * math.sin(a) * 1.45, -0.03]))
    TUB.append(np.array(pts[::-1]))
RETE = TC_CTR + TC_R @ np.array([0.55, 1.2, -0.03])


# =====================================================================
# Procedimiento (mm): piel, conducto que se levanta por la abertura, corte y sellado
# =====================================================================
T_LIFT = WT(6, 8)
T_CUTP = WT(7, 1) + 0.1
T_SEAL = WT(7, 4)


def skin_model():
    m = mm.Model()
    n = 18
    sz = 70.0
    for i in range(n):
        for j in range(n):
            x0, x1 = -sz + 2 * sz * i / n, -sz + 2 * sz * (i + 1) / n
            z0, z1 = -sz + 2 * sz * j / n, -sz + 2 * sz * (j + 1) / n
            hgt = lambda x, z: -0.0012 * (x * x + z * z) + 0.7 * math.sin(x * 0.11) * math.sin(z * 0.09)
            pts = [(x0, hgt(x0, z0), z0), (x1, hgt(x1, z0), z0), (x1, hgt(x1, z1), z1), (x0, hgt(x0, z1), z1)]
            xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
            nn = norm(np.array([0.0024 * xm, 1.0, 0.0024 * zm]))
            m.face(pts, nn, (222, 172, 146), 'skin')
    m.face([(5.0 * math.cos(a), 0.25, 3.5 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 21)[:-1]][::-1], (0, 1, 0), (112, 56, 54), 'hole')
    return m


SKIN = skin_model()


def vas_loop(lift):
    hpk = -10.0 + 26.0 * lift
    return catmull([(-70, -14, 0), (-30, -11, 0), (-10, -10, 0), (-4, -10 + 13 * lift, 0), (0, hpk, 0), (4, -10 + 13 * lift, 0),
                    (10, -10, 0), (30, -11, 0), (70, -14, 0)], 10)


# =====================================================================
# Modelos de entornos reales (cm)
# =====================================================================
def build_tray_scene():
    """charola de acero (mm) con el conducto y un espagueti"""
    m = mm.Model()
    m.box((-60, -4, -40), (60, 0, 40), (176, 180, 186), 'tray')
    for (lo, hi) in (((-62, -4, -42), (62, 4, -38)), ((-62, -4, 38), (62, 4, 42)), ((-62, -4, -42), (-58, 4, 42)), ((58, -4, -42), (62, 4, 42))):
        m.box(lo, hi, (196, 200, 206), 'tray')
    sp = catmull([(-50, 1.0, 14), (-10, 1.0, 13), (30, 1.0, 15), (52, 1.0, 13)], 8)
    tube(m, sp, 0.95, (238, 214, 140), 'spag', 10, cap_col=(220, 190, 110))
    return m


TRAY = build_tray_scene()
HOOK_VAS_L = catmull([(-50, 1.45, -6), (-20, 1.45, -4), (0, 1.45, -5), (20, 1.45, -6), (50, 1.45, -4)], 10)
HOOK_CUM = arclen(HOOK_VAS_L)
T_SNIP = WT(0, 9) + 0.05


def hook_vas_model(cut_k):
    m = mm.Model()
    if cut_k <= 0:
        tube(m, HOOK_VAS_L, 1.4, C_VAS, 'vas', 14, cap_col=(220, 200, 176))
    else:
        mid = HOOK_CUM[-1] / 2
        sep = 1.5 + 4.0 * cut_k
        i_mid = np.searchsorted(HOOK_CUM, mid)
        left = HOOK_VAS_L[:i_mid].copy()
        right = HOOK_VAS_L[i_mid:].copy()
        left[:, 0] -= sep * np.linspace(0, 1, len(left)) ** 4
        right[:, 0] += sep * np.linspace(1, 0, len(right)) ** 4
        tube(m, left, 1.4, C_VAS, 'vas', 14, cap_col=(200, 150, 130))
        tube(m, right, 1.4, C_VAS, 'vas', 14, cap_col=(200, 150, 130))
    return m


def scissors_model(open_ang):
    m = mm.Model()
    steel, dark = (196, 200, 208), (120, 124, 132)
    for sgn in (1, -1):
        a = sgn * open_ang
        Rb = rot_y(a)
        blade = [(0, 0), (6, 2.2), (46, 0.6), (48, 0), (6, -0.8)]
        bm = mm.Model()
        bm.ext([(x, y * sgn) for (x, y) in blade], -0.6 * sgn - 0.6, -0.6 * sgn + 0.6, steel, 'sc')
        hm = mm.Model()
        hpath = catmull([(0, 0, 0), (-14, -3 * sgn, 0), (-26, -9 * sgn, 0)], 6)
        tube(hm, hpath, 1.0, dark, 'sc', 8)
        ring = [(-26 - 6 * math.cos(q), -9 * sgn - 6 * math.sin(q) * sgn - 6 * sgn * 0, 0) for q in np.linspace(0, 2 * math.pi, 17)]
        ring = catmull([(-26 + 6 * math.cos(q), (-15 + 6 * math.sin(q)) * sgn, 0) for q in np.linspace(0, 2 * math.pi, 13)], 3)
        tube(hm, ring, 1.0, dark, 'sc', 8, caps=False)
        for mod in (bm, hm):
            for (pts, n, col, tag) in mod.F:
                pts2 = pts[:, [0, 2, 1]]
                n2 = n[[0, 2, 1]]
                Rq = rot_y(a)
                m.face(pts2 @ Rq.T, Rq @ n2, col, tag)
    m.cyl((0, 0, 0), (0, 1, 0), 1.6, 2.6, (150, 154, 160), 12)
    return m


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1.0, 0], [-s, 0, c]])


def build_clinic():
    m = mm.Model()
    wall, floor = (204, 224, 216), (196, 202, 206)
    m.face([(-300, 0, -700), (300, 0, -700), (300, 0, 300), (-300, 0, 300)], (0, 1, 0), floor, 'floor')
    m.face([(-300, 0, 300), (300, 0, 300), (300, 280, 300), (-300, 280, 300)], (0, 0, -1), wall, 'wall')
    m.face([(-300, 0, -250), (-300, 0, 300), (-300, 280, 300), (-300, 280, -250)], (1, 0, 0), (196, 216, 208), 'wall')
    m.box((-300, 0, 296), (300, 12, 300), (150, 170, 164), 'wall')
    # mesa de procedimientos
    m.box((-20, 0, -40), (20, 8, 40), (96, 100, 108))
    m.box((-8, 8, -8), (8, 62, 8), (150, 154, 160))
    m.box((-34, 62, -95), (34, 74, 95), (46, 116, 124))
    m.box((-30, 74.2, -92), (30, 74.6, 70), (240, 242, 244))
    m.box((-34, 74, 72), (34, 86, 95), (46, 116, 124))
    # lámpara quirúrgica
    m.beam((0, 280, 40), (0, 230, 40), 6, 6, (210, 212, 216))
    m.beam((0, 230, 40), (40, 200, 10), 5, 5, (210, 212, 216))
    m.cyl((40, 192, 10), (0.3, 1, -0.2), 30, 10, (236, 238, 240), 22, 'lamp', True, (250, 250, 250))
    # carrito de instrumental (mesa Mayo)
    m.box((70, 0, -70), (110, 4, -30), (90, 92, 98))
    m.box((86, 4, -54), (94, 96, -46), (170, 174, 180))
    m.box((52, 96, -80), (128, 99, -22), (196, 200, 206), 'traytop')
    m.box((54, 99, -78), (126, 99.4, -24), (90, 150, 170), 'drape')
    # gabinete
    m.box((-290, 0, 180), (-170, 90, 290), (232, 234, 236))
    m.box((-290, 90, 180), (-170, 94, 290), (180, 184, 190))
    m.box((-290, 160, 220), (-170, 230, 290), (232, 234, 236))
    # monitor
    m.box((-150, 0, 230), (-110, 110, 260), (70, 72, 80))
    m.box((-158, 110, 238), (-102, 150, 246), (30, 32, 38))
    return m


CLINIC = build_clinic()
CLIN_INSTR = None


def instruments_model():
    m = mm.Model()
    steel = (200, 204, 212)
    # jeringa de anestesia
    m.cyl((76, 101.5, -40), (1, 0, 0), 1.6, 16, (226, 236, 244), 14)
    m.cyl((89, 101.5, -40), (1, 0, 0), 0.5, 10, (150, 154, 160), 8)
    m.cyl((66, 101.5, -40), (1, 0, 0), 0.6, 6, (230, 232, 236), 8)
    m.box((61.5, 99.5, -42.5), (62.5, 103.5, -37.5), (230, 232, 236))
    # pinza de anillo
    m.beam((70, 100.3, -58), (104, 100.3, -64), 0.9, 0.9, steel)
    ring = catmull([(104 + 2.2 * math.cos(q), 100.3, -64 + 2.2 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 13)], 3)
    tube(m, ring, 0.45, steel, 'body', 6, caps=False)
    # disector (punta fina, sin bisturí)
    m.beam((72, 100.3, -70), (108, 100.3, -72), 0.8, 0.8, steel)
    m.beam((72, 100.3, -71.5), (108, 100.3, -72.5), 0.8, 0.8, steel)
    # gasas
    for k in range(3):
        m.box((100 + k * 0.4, 99.4 + k * 0.4, -36), (118 + k * 0.4, 99.8 + k * 0.4, -26), (246, 246, 248))
    return m


INSTR = instruments_model()


def build_lab():
    m = mm.Model()
    m.face([(-300, 0, -200), (300, 0, -200), (300, 0, 300), (-300, 0, 300)], (0, 1, 0), (170, 176, 184), 'floor')
    m.face([(-300, 0, 120), (300, 0, 120), (300, 260, 120), (-300, 260, 120)], (0, 0, -1), (214, 222, 230), 'wall')
    m.box((-160, 0, 40), (160, 88, 115), (220, 224, 228))
    m.box((-164, 88, 36), (164, 92, 118), (236, 238, 240))
    m.box((-160, 150, 92), (160, 154, 118), (200, 204, 210))
    return m


LAB = build_lab()


def microscope_model():
    m = mm.Model()
    blk, wht = (44, 46, 52), (232, 234, 238)
    m.box((-14, 92, 50), (14, 96, 80), blk)
    m.box((-6, 96, 70), (6, 150, 80), wht)
    m.box((-12, 112, 46), (12, 114, 68), blk)
    m.box((-6, 146, 52), (6, 154, 80), wht)
    m.cyl((0, 132, 60), (0, 1, 0), 3.2, 12, (200, 204, 210), 14)
    m.cyl((0, 124, 60), (0, 1, 0), 1.6, 6, (120, 124, 130), 10)
    for s in (-1, 1):
        m.cyl((s * 3.2, 162, 66), (s * 0.15, 1, -0.5), 1.8, 16, blk, 12)
    m.cyl((9, 128, 74), (1, 0, 0), 4.0, 3, (150, 154, 160), 14)
    return m


MICRO = microscope_model()
# tubos de ensayo (escena de composición)
TT_C = np.array([0.0, 115.0, 70.0])
TT_R, TT_H = 4.2, 34.0


def build_tube_bench():
    m = mm.Model()
    m.face([(-300, 0, 120), (300, 0, 120), (300, 260, 120), (-300, 260, 120)], (0, 0, -1), (206, 214, 226), 'wall')
    m.box((-160, 0, 30), (160, 88, 115), (210, 214, 220))
    m.box((-164, 88, 26), (164, 92, 118), (236, 238, 240))
    m.box((-22, 92, 56), (22, 112, 84), (60, 120, 190))
    m.box((-26, 112, 54), (26, 115, 86), (70, 132, 200))
    for x in (-36, 36):
        m.cyl((x, 106, 76), (0, 1, 0), 2.6, 28, (230, 236, 242), 12, 'glass2')
    return m


BENCH = build_tube_bench()


def liquid_cyl(m, y0, y1, col, tag):
    m.cyl((TT_C[0], (y0 + y1) / 2, TT_C[2]), (0, 1, 0), TT_R * 0.92, max(0.05, y1 - y0), col, 24, tag)


def build_hospital():
    m = mm.Model()
    wall, wall2, glassc, trim = (236, 232, 222), (214, 208, 196), (70, 120, 150), (180, 176, 168)
    m.box((-60, 0, 40), (60, 22, 70), wall)
    m.box((-60, 22, 40), (60, 23, 70), trim)
    m.box((-26, 0, 38), (26, 30, 72), wall2)
    for fl in range(5):
        y = 2.5 + fl * 4.0
        if y > 21:
            break
        for k in range(14):
            x = -56 + k * 8.4
            if -27 < x < 27:
                continue
            m.face([(x, y, 39.9), (x + 5.6, y, 39.9), (x + 5.6, y + 2.6, 39.9), (x, y + 2.6, 39.9)], (0, 0, -1), glassc, 'win')
    for fl in range(7):
        y = 2.5 + fl * 3.9
        for k in range(5):
            x = -23 + k * 9.6
            m.face([(x, y, 37.9), (x + 6.6, y, 37.9), (x + 6.6, y + 2.5, 37.9), (x, y + 2.5, 37.9)], (0, 0, -1), glassc, 'win')
    m.box((-12, 4.2, 30), (12, 4.8, 38), (200, 204, 210))
    for x in (-11, 11):
        m.box((x - 0.3, 0, 30.3), (x + 0.3, 4.2, 30.9), (160, 164, 170))
    m.face([(-6, 0.2, 37.8), (6, 0.2, 37.8), (6, 3.6, 37.8), (-6, 3.6, 37.8)], (0, 0, -1), (90, 140, 160), 'win')
    # cruz verde (señal genérica de hospital)
    for (lo, hi) in (((-1.6, 24.0, 37.6), (1.6, 28.8, 37.8)), ((-4.0, 25.6, 37.6), (4.0, 27.2, 37.8))):
        m.box(lo, hi, (40, 170, 110), 'cross')
    # árboles
    for (x, z) in ((-50, 22), (-34, 18), (36, 20), (52, 24), (-66, 30), (66, 32)):
        m.cyl((x, 1.6, z), (0, 1, 0), 0.4, 3.2, (110, 80, 54), 8)
        blob(m, (x, 5.0, z), (2.6, 2.8, 2.6), (60, 120, 66), 'tree', nu=12, nv=8, bump=lambda u, v: 0.12 * math.sin(5 * u) * math.sin(4 * v))
    # ambulancia genérica
    m.box((18, 0.4, 14), (26, 3.6, 17.5), (244, 244, 246))
    m.box((18, 1.6, 13.95), (26, 2.1, 14.0), (220, 60, 60))
    for x in (19.5, 24.5):
        m.cyl((x, 0.5, 14.0), (0, 0, 1), 0.5, 0.4, (30, 30, 34), 10)
    return m


HOSP = build_hospital()


# =====================================================================
# Cielo y suelo (día) para el hospital, en metros
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


def day_scene(c):
    dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
    e = np.clip(dy, -0.2, 1).astype(np.float32)[..., None]
    hz = np.array([206, 222, 236], np.float32)
    top = np.array([70, 128, 206], np.float32)
    k = np.clip(e / 0.45, 0, 1)
    out = hz * (1 - k) + top * k
    cam = c['pos']
    m = dy < -2e-4
    tt = (0.0 - cam[1]) / np.where(m, dy, -1.0)
    gx, gz = cam[0] + tt * dx, cam[2] + tt * dz
    x, z, d = gx[m], gz[m], tt[m]
    road = (z > 4) & (z < 30)
    grass = np.array([96, 140, 74], np.float32)
    asph = np.array([92, 94, 98], np.float32)
    n1 = vnoise(x, z, 0.8, 1)
    n2 = vnoise(x, z, 5.0, 2)
    a1 = np.clip(0.8 * 180.0 / d, 0, 1)
    col = np.where(road[:, None], asph[None, :], grass[None, :])
    col = col * (0.88 + 0.12 * ((n1 - 0.5) * a1 + 0.5)[:, None] + 0.1 * (n2 - 0.5)[:, None])
    lines = road & (np.abs(((x + 1.25) % 2.5) - 1.25) < 0.08) & (z > 6) & (z < 12)
    col[lines] = np.array([230, 230, 220], np.float32)
    f = np.clip((d - 60.0) / 900.0, 0, 0.8)[:, None]
    col = col * (1 - f) + hz * f
    out[m] = col
    return out.astype(np.float32)


# =====================================================================
# Cámaras
# =====================================================================
KEYS = {
    'hook': [(0.0, 108, 54, 8, 980, 6, 0, 3), (T_SNIP, 90, 58, 14, 980, 4, 0, 2), (6.15, 82, 62, 20, 980, 4, 0, 2)],
    'anat': [(6.15, 50, 10, -40, 1000, 0, -1.5, 2.0), (8.45, 44, 12, -18, 1000, 0, -1.5, 2.0)],
    'testis': [(8.45, 12.5, 6, -16, 980, 2.3, -9.0, -1.0), (12.45, 10.5, 8, -2, 980, 2.3, -9.0, -1.0)],
    'path': [(12.45, 34, 8, -48, 1000, 2.5, -2.0, 1.5), (16.85, 36, 14, -62, 1000, 1.5, 0.5, 2.5)],
    'glands': [(16.85, 22, 18, 160, 980, 0, 3.4, 4.5), (21.45, 20, 22, 188, 980, 0, 3.2, 4.5)],
    'tube': [(21.45, 66, 8, -14, 1000, 0, 130, 70), (26.45, 58, 6, 2, 1000, 0, 130, 70)],
    'clinic': [(26.45, 130, 30, -58, 1000, 86, 100, -50), (31.15, 100, 36, -44, 1000, 90, 100, -52)],
    'proc': [(31.15, 78, 34, -20, 980, 0, 5, 0), (35.55, 70, 40, -8, 980, 0, 5, 0)],
    'after': [(35.55, 40, 8, -34, 1000, 2.2, -3.5, 1.0), (39.85, 36, 12, -22, 1000, 2.2, -3.0, 1.0)],
    'hormone': [(39.85, 56, 10, 28, 1000, 0, 0.0, 2.0), (44.05, 52, 12, 40, 1000, 0, 0.5, 2.0)],
    'lab': [(44.05, 120, 14, -20, 980, 0, 126, 64), (50.05, 100, 16, -6, 980, 0, 128, 64)],
    'stats': [(50.05, 66, 10, -60, 1000, 0, -1.0, 2.0), (55.25, 62, 12, -20, 1000, 0, -1.0, 2.0)],
    'hosp': [(55.25, 120, 6, -18, 900, 0, 12, 40), (63.1, 104, 8, -6, 900, 0, 12, 40)],
}
LOGD = {}


def cam_for(env, t):
    return cam_keys(t, KEYS[env], LOGD.get(env, False))


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
    info = {}
    base = None

    if env == 'hook':
        base = Image.fromarray(bg_studio((40, 64, 70), (18, 34, 40), (40, 60, 60)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.3, 0.9, -0.3))
        # campo quirúrgico (tela)
        bd.polygon([P2(*p, c) for p in clip_near([(-400, -4.2, -300), (400, -4.2, -300), (400, -4.2, 400), (-400, -4.2, 400)], c, 1.0)], fill=(44, 104, 112))
        cut_k = ease(seg(t, T_SNIP + 0.05, T_SNIP + 0.6))
        fl0 = org_faces(c, TRAY, L, {'tray': {'spec': 0.6}, 'spag': {'spec': 0.3}}, near=1.0)
        draw_faces(bd, od, [q for q in fl0 if q[4] == 'tray'])
        fl = [q for q in fl0 if q[4] != 'tray']
        fl += org_faces(c, hook_vas_model(cut_k), L, {'vas': {'spec': 0.55}}, near=1.0)
        # tijera: entra, corta y sale
        k_in = ease(seg(t, T_SNIP - 1.6, T_SNIP - 0.3))
        k_out = ease(seg(t, T_SNIP + 0.6, T_SNIP + 1.6))
        if k_in > 0.01 and k_out < 0.99:
            op = math.radians(26) * (1 - ease(seg(t, T_SNIP - 0.35, T_SNIP)))
            mid = at_s(HOOK_VAS_L, HOOK_CUM, np.array([HOOK_CUM[-1] / 2]))[0]
            pos = mid + np.array([0.0, 1.0 + 60.0 * (1 - k_in) + 60.0 * k_out, -30.0])
            Rsc = np.array([[0, 1.0, 0], [0, 0, 1.0], [1.0, 0, 0]])
            fl += org_faces(c, scissors_model(op), L, {'sc': {'spec': 0.9}}, pos=pos, Rm=Rsc, near=1.0, default={'spec': 0.8})
        draw_faces(bd, od, fl)
        if cut_k > 0 and t < T_SNIP + 0.5:
            mid = at_s(HOOK_VAS_L, HOOK_CUM, np.array([HOOK_CUM[-1] / 2]))[0]
            x, y, dep = proj(*mid, c)
            glow_dot(la, x * S, y * S, (20 + 60 * (t - T_SNIP)) * S, (255, 255, 255), 0.7 * (1 - (t - T_SNIP) / 0.5))
        info['vas'] = at_s(HOOK_VAS_L, HOOK_CUM, np.array([HOOK_CUM[-1] * 0.25]))[0]
        info['spag'] = np.array([20.0, 1.0, 14.5])
    elif env in ('anat', 'path', 'after', 'hormone', 'stats'):
        base = Image.fromarray(BG_ANAT.astype(np.uint8))
        bd = ImageDraw.Draw(base)
        model = ANAT_CUT if env in ('after', 'hormone', 'stats') else ANAT
        if env == 'anat':
            st = {'bladder': {'alpha': 110, 'spec': 0.25}}
            bk = ease(seg(t, 6.2, 7.0))
        elif env == 'path':
            st = anat_styles(('vas', 'testis', 'epi'), 0.5)
            bk = 0.7
        elif env == 'after':
            st = anat_styles(('vas', 'testis', 'epi'), 0.55)
            bk = 0.6
        elif env == 'hormone':
            st = anat_styles(('testis', 'vein', 'prostate', 'ves', 'urethra'), 0.55)
            bk = 0.6
        else:
            st = {'bladder': {'alpha': 110, 'spec': 0.25, 'dim': 0.6}, 'prostate': {'dim': 0.6}, 'ves': {'dim': 0.6}, 'testis': {'dim': 0.6},
                  'epi': {'dim': 0.6}, 'vas': {'dim': 0.6}, 'art': {'dim': 0.6}, 'vein': {'dim': 0.6}, 'urethra': {'dim': 0.6}}
            bk = 0.45
        draw_anatomy(base, bd, od, la, c, t, model, st, bk)
        if env == 'path':
            k = ease(seg(t, 12.9, 13.4))
            for i in range(2):
                s = (np.arange(26) / 26.0 * VAS_LEN + 7.0 * (t - 12.45)) % VAS_LEN
                prog = clamp((t - 13.0) / 3.4) * VAS_LEN
                s = s[s <= prog + 0.01] if prog < VAS_LEN else s
                particles_on(la, c, VAS[i], VAS_CUM[i], s, SPERM, 3.2, k)
            info['vas_lbl'] = VAS[0][int(len(VAS[0]) * 0.42)]
            info['prog'] = clamp((t - 13.0) / 3.4)
        if env == 'after':
            k = ease(seg(t, 35.8, 36.3))
            for i in range(2):
                s = (np.arange(18) / 18.0 * (S_CUT - GAP / 2) + 5.0 * (t - 35.55)) % (S_CUT - GAP / 2)
                particles_on(la, c, VAS[i], VAS_CUM[i], s, SPERM, 3.0, k)
                # se acumulan y se desvanecen junto al corte (se reabsorben)
                rs = np.random.RandomState(i + 4)
                for j in range(10):
                    ph = ((t - 35.6) * 0.5 + j / 10.0) % 1.0
                    p = at_s(VAS[i], VAS_CUM[i], np.array([S_CUT - GAP / 2 - 0.15 - 0.5 * rs.rand()]))[0] + rs.normal(0, 0.18, 3)
                    x, y, dep = proj(*p, c)
                    glow_dot(la, x * S, y * S, 2.6 * S, SPERM, k * (1 - ph) * ease(seg(t, WT(8, 7) - 0.4, WT(8, 7))) + k * (1 - ease(seg(t, WT(8, 7) - 0.4, WT(8, 7)))) * 0.8)
                # puntas selladas
                for sg in (-1, 1):
                    p = at_s(VAS[i], VAS_CUM[i], np.array([S_CUT + sg * GAP / 2]))[0]
                    x, y, dep = proj(*p, c)
                    glow_dot(la, x * S, y * S, 4.5 * S, (255, 150, 90), 0.8)
            info['cut'] = at_s(VAS[0], VAS_CUM[0], np.array([S_CUT]))[0]
        if env == 'hormone':
            k = ease(seg(t, 40.3, 40.8))
            for i in range(2):
                s = (np.arange(16) / 16.0 * VEIN_CUM[i][-1] + 6.0 * (t - 39.85)) % VEIN_CUM[i][-1]
                particles_on(la, c, VEINS[i], VEIN_CUM[i], s, GOLD, 3.2, k)
            # líquido de vesículas y próstata hacia la uretra
            k2 = ease(seg(t, WT(9, 5) - 0.3, WT(9, 5) + 0.2))
            ucum = arclen(URETHRA)
            s = (np.arange(14) / 14.0 * ucum[-1] + 4.0 * (t - 39.85)) % ucum[-1]
            particles_on(la, c, URETHRA, ucum, s, (240, 236, 220), 3.0, k2)
            info['vein'] = VEINS[0][int(len(VEINS[0]) * 0.75)]
            info['ure'] = URETHRA[-6]
        info['testis'] = TESTIS_C[0]
        info['bladder'] = np.array([0, 9.5, 1.0])
        info['prostate'] = np.array([0, 1.0, 1.8])
        info['ves'] = np.array([-4.2, 4.6, 5.8])
    elif env == 'testis':
        base = Image.fromarray(BG_ANAT.astype(np.uint8))
        bd = ImageDraw.Draw(base)
        fl = org_faces(c, TCUT, ANAT_L, {'cutface': {'spec': 0.1}})
        draw_faces(bd, od, fl)
        # túbulos y lóbulos
        w = max(1, int(2 * S))
        for tub in TUB:
            polyline3(bd, c, [tuple(p) for p in tub], (246, 214, 200), w, 0.3)
        k = ease(seg(t, 8.8, 9.3))
        rate = 1.0 + 3.0 * ease(seg(t, WT(2, 5) - 0.2, WT(2, 5) + 0.5))
        for j, tub in enumerate(TUB):
            cum = arclen(tub)
            s = (np.arange(5) / 5.0 * cum[-1] + 0.9 * rate * (t - 8.45) + j * 0.31) % cum[-1]
            particles_on(la, c, tub, cum, s, SPERM, 2.4, k)
        ep = EPI[0]
        ecum = arclen(ep)
        s = (np.arange(10) / 10 * ecum[-1] + 1.4 * (t - 8.45)) % ecum[-1]
        particles_on(la, c, ep, ecum, s, SPERM, 2.6, k)
        info['cutface'] = TC_CTR + TC_R @ np.array([-0.5, -0.6, -0.05])
        info['epi'] = EPI[0][len(EPI[0]) // 2]
    elif env == 'glands':
        base = Image.fromarray(BG_ANAT.astype(np.uint8))
        bd = ImageDraw.Draw(base)
        st = anat_styles(('prostate', 'ves', 'vas', 'urethra'), 0.5)
        st['bladder'] = {'alpha': 70, 'dim': 0.6}
        draw_anatomy(base, bd, od, la, c, t, ANAT, st, 0.4)
        k1 = ease(seg(t, WT(4, 7) - 0.3, WT(4, 7) + 0.2))
        k2 = ease(seg(t, WT(4, 10) - 0.3, WT(4, 10) + 0.2))
        for i, sg in enumerate((1, -1)):
            # gotas de las vesículas hacia el conducto eyaculador
            for j in range(9):
                ph = ((t - 16.9) * 0.6 + j / 9.0) % 1.0
                p0 = np.array([sg * 3.9, 4.4, 5.8])
                p1 = np.array([sg * 0.6, 2.2, 4.3])
                p = p0 + (p1 - p0) * ph + np.array([0, 0.35 * math.sin(ph * 6 + j), 0])
                x, y, dep = proj(*p, c)
                glow_dot(la, x * S, y * S, 3.0 * S, (255, 226, 140), k2 * (0.4 + 0.6 * math.sin(math.pi * ph)))
        for j in range(12):
            ph = ((t - 16.9) * 0.7 + j / 12.0) % 1.0
            a = j * 2.4
            p = np.array([1.5 * math.cos(a) * (1 - ph), 1.6 + 1.0 * math.sin(a) * (1 - ph), 3.2 + 1.2 * (1 - ph) * math.sin(a * 1.3)])
            x, y, dep = proj(*p, c)
            glow_dot(la, x * S, y * S, 2.8 * S, (240, 240, 250), k1 * (0.4 + 0.6 * math.sin(math.pi * ph)))
        for i in range(2):
            s = VAS_LEN - (np.arange(10) / 10.0 * 8.0 + 2.5 * (t - 16.85)) % 8.0
            s = VAS_LEN - ((np.arange(10) / 10.0 * 8.0 - 2.5 * (t - 16.85)) % 8.0)
            particles_on(la, c, VAS[i], VAS_CUM[i], s, SPERM, 2.6, 0.9)
        info['prostate'] = np.array([0, 1.6, 4.8])
        info['ves'] = np.array([3.6, 4.2, 6.6])
    elif env == 'tube':
        base = Image.fromarray(bg_studio((186, 196, 210), (150, 160, 176), (40, 40, 40)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.4, 0.8, -0.45))
        fl = org_faces(c, BENCH, L, {'wall': {'spec': 0.0}, 'glass2': {'alpha': 90, 'spec': 0.8}}, near=2.0)
        draw_faces(bd, od, fl)
        lm = mm.Model()
        y0 = TT_C[1] + 1.0
        Hh = TT_H - 6.0
        fills = [(0.70, (238, 222, 150), 'v', WT(5, 1) - 0.2), (0.27, (232, 232, 222), 'p', WT(5, 3)), (0.03, (140, 220, 255), 's', WT(5, 8))]
        yb = y0
        info['layers'] = []
        for (frac, col, tag, t0) in fills:
            kk = ease(seg(t, t0, t0 + 0.8))
            hh = Hh * frac * kk
            if hh > 0.05:
                liquid_cyl(lm, yb, yb + hh, col, tag)
            info['layers'].append((tag, yb + hh / 2, kk))
            yb += hh
        fl2 = org_faces(c, lm, L, {'v': {'spec': 0.3}, 'p': {'spec': 0.3}, 's': {'spec': 0.5}}, near=2.0)
        draw_faces(bd, od, fl2)
        # tubo de vidrio (contorno)
        gt = mm.Model()
        gt.cyl((TT_C[0], TT_C[1] + TT_H / 2, TT_C[2]), (0, 1, 0), TT_R, TT_H, (0, 0, 0), 28, 'g', False)
        glass(la, c, gt, (200, 230, 255), 0.9)
        for k_ in range(1, 6):
            yy = TT_C[1] + 1 + Hh * k_ / 5
            p0 = (TT_C[0] - TT_R * 0.7, yy, TT_C[2] - TT_R * 0.7)
            p1 = (TT_C[0] - TT_R * 0.35, yy, TT_C[2] - TT_R * 0.93)
            line3(la, c, p0, p1, sc3((230, 240, 255), 0.7), max(1, int(2 * S)), 2.0)
        if info['layers'][2][2] > 0.2:
            x, y, dep = proj(TT_C[0], info['layers'][2][1], TT_C[2] - TT_R, c)
            glow_dot(la, x * S, y * S, 16 * S, (140, 220, 255), 0.35 * info['layers'][2][2])
    elif env == 'clinic':
        base = Image.fromarray(bg_studio((220, 232, 228), (200, 212, 210), (10, 10, 10)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.3, 0.85, -0.4))
        fl = org_faces(c, CLINIC, L, {'floor': {'spec': 0.2}, 'wall': {'spec': 0.0}, 'lamp': {'spec': 0.4}}, near=5.0, default={'spec': 0.25})
        fl += org_faces(c, INSTR, L, {}, near=5.0, default={'spec': 0.8})
        draw_faces(bd, od, fl)
        w = max(1, int(1.2 * S))
        for k in range(-10, 12):
            line3(bd, c, (k * 30, 0.2, -250), (k * 30, 0.2, 296), (178, 186, 190), w, 5.0)
        for k in range(-8, 19):
            line3(bd, c, (-300, 0.2, k * 30), (300, 0.2, k * 30), (178, 186, 190), w, 5.0)
        # luz de la lámpara
        lc_ = np.array([40, 187, 11])
        for k in range(7):
            a = 2 * math.pi * k / 7
            p = lc_ + np.array([18 * math.cos(a), -1.0, 18 * math.sin(a)])
            x, y, dep = proj(*p, c)
            if dep > 5:
                glow_dot(la, x * S, y * S, 5 * S, (255, 250, 230), 0.9)
        x, y, dep = proj(*lc_, c)
        glow_dot(la, x * S, y * S, 9 * S, (255, 250, 230), 0.9)
        info['syr'] = (76, 101.5, -40)
        info['ring'] = (104, 100.3, -64)
        info['dis'] = (100, 100.3, -72)
    elif env == 'proc':
        base = Image.fromarray(bg_studio((36, 70, 78), (16, 32, 38), (30, 50, 50)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        bd.polygon([P2(*p, c) for p in clip_near([(-500, -20, -400), (500, -20, -400), (500, -20, 500), (-500, -20, 500)], c, 1.0)], fill=(40, 100, 108))
        L = norm((-0.3, 0.9, -0.35))
        lift = ease(seg(t, 31.15, T_CUTP - 0.05)) * (1 - ease(seg(t, T_SEAL + 0.7, T_SEAL + 1.6)))
        cut = t >= T_CUTP
        path = vas_loop(max(lift, 0.0))
        cum = arclen(path)
        vm = mm.Model()
        if not cut:
            tube(vm, path, 1.4, C_VAS, 'vas', 12)
        else:
            mid = cum[-1] / 2
            g = 3.0 + 5.0 * ease(seg(t, T_CUTP, T_CUTP + 0.8))
            tube(vm, path, 1.4, C_VAS, 'vas', 12, caps=False, s_range=[(0, mid - g), (mid + g, 1e9)])
        fl = org_faces(c, SKIN, L, {'skin': {'spec': 0.2}}, near=1.0)
        fl += org_faces(c, vm, L, {'vas': {'spec': 0.5}}, near=1.0)
        draw_faces(bd, od, fl)
        # pinza de anillo sujetando el asa
        top = at_s(path, cum, np.array([cum[-1] / 2]))[0]
        a_r = ease(seg(t, 31.2, 31.6)) * (1 - ease(seg(t, T_SEAL + 0.6, T_SEAL + 1.0)))
        if a_r > 0.01:
            ring = [tuple(top + np.array([0, 2.8 * math.cos(q_), 2.8 * math.sin(q_)]) + np.array([-3.0, 0, 0])) for q_ in np.linspace(0, 2 * math.pi, 24)]
            polyline3(bd, c, ring, (206, 210, 218), max(2, int(4 * S)), 1.0)
            line3(bd, c, tuple(top + np.array([-3.0, 2.8, 0])), tuple(top + np.array([-60.0, 70.0, -20.0])), (186, 190, 198), max(3, int(6 * S)), 1.0)
        if cut:
            mid = cum[-1] / 2
            g = 3.0 + 5.0 * ease(seg(t, T_CUTP, T_CUTP + 0.8))
            ends = at_s(path, cum, np.array([mid - g, mid + g]))
            seal = ease(seg(t, T_SEAL - 0.1, T_SEAL + 0.3)) * (1 - 0.6 * ease(seg(t, T_SEAL + 1.0, T_SEAL + 1.8)))
            for p in ends:
                x, y, dep = proj(*p, c)
                glow_dot(la, x * S, y * S, 9 * S, (255, 150, 80), seal)
                glow_dot(la, x * S, y * S, 4 * S, (255, 240, 200), seal)
            if t < T_CUTP + 0.3:
                x, y, dep = proj(*top, c)
                glow_dot(la, x * S, y * S, 26 * S, (255, 255, 255), 0.7 * (1 - (t - T_CUTP) / 0.3))
            info['ends'] = ends
        info['hole'] = (0, 0.2, 0)
        info['top'] = top
    elif env == 'lab':
        base = Image.fromarray(bg_studio((206, 214, 226), (176, 184, 196), (20, 20, 20)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.4, 0.85, -0.4))
        fl = org_faces(c, LAB, L, {'floor': {'spec': 0.1}, 'wall': {'spec': 0.0}}, near=5.0, default={'spec': 0.25})
        fl += org_faces(c, MICRO, L, {}, near=5.0, default={'spec': 0.6})
        draw_faces(bd, od, fl)
        x, y, dep = proj(0, 113.6, 60, c)
        glow_dot(la, x * S, y * S, 8 * S, (255, 250, 220), 0.7)
        info['micro'] = (0, 150, 66)
    else:  # hosp
        arr = day_scene(c)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.5, 0.75, -0.45))
        fl = org_faces(c, HOSP, L, {'win': {'spec': 0.9}, 'cross': {'spec': 0.2}}, near=1.0, default={'spec': 0.15})
        draw_faces(bd, od, fl)
        x, y, dep = proj(0, 26.4, 37.5, c)
        glow_dot(la, x * S, y * S, 12 * S, (80, 255, 160), 0.35)

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
    if env in ('hook', 'clinic', 'tube', 'lab', 'hosp', 'proc'):
        DARK.append((40, 150, 1040, 420, 0.95))
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


def check_icon(l2, x, y, r, a, col=GREEN):
    if a <= 0:
        return
    l2.ellipse((*P(x - r, y - r), *P(x + r, y + r)), outline=sc3(col, a), width=max(2, int(4 * S)))
    l2.line([P(x - r * 0.45, y), P(x - r * 0.1, y + r * 0.38), P(x + r * 0.5, y - r * 0.35)], fill=sc3(col, a), width=max(3, int(6 * S)))


def shield_x(l2, x, y, r, a):
    if a <= 0:
        return
    pts = [P(x, y - r), P(x + r * 0.85, y - r * 0.6), P(x + r * 0.75, y + r * 0.3), P(x, y + r), P(x - r * 0.75, y + r * 0.3), P(x - r * 0.85, y - r * 0.6)]
    l2.polygon(pts, outline=sc3((255, 200, 120), a), width=max(2, int(4 * S)))
    l2.line([P(x - r * 0.4, y - r * 0.35), P(x + r * 0.4, y + r * 0.45)], fill=sc3(RED, a), width=max(3, int(7 * S)))
    l2.line([P(x + r * 0.4, y - r * 0.35), P(x - r * 0.4, y + r * 0.45)], fill=sc3(RED, a), width=max(3, int(7 * S)))


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
            l2.text(P(1040, y), txt, font=F(B, 22), fill=sc3((200, 200, 220), a * 0.9), anchor="rm")

    def win(a, b, e=0.4):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def P3(p):
        sx, sy, _ = proj(*p, c)
        return (sx, sy)

    for ct in CUTS:
        if abs(t - ct) < 0.25:
            return
    if env == 'hook':
        a = win(0.8, 6.1)
        if a > 0:
            label("CONDUCTO DEFERENTE", P3(tuple(info['vas'])), (60, 1380), "lm", a, (255, 236, 210))
            label("ESPAGUETI", P3(tuple(info['spag'])), (1020, 680), "rm", ease(seg(t, WT(0, 6) - 0.2, WT(0, 6) + 0.2)) * a, (255, 226, 150))
        pill("2 A 3 mm DE GROSOR", 1600, win(WT(0, 3) - 0.1, T_SNIP - 0.2), (255, 220, 160), 620, 36)
        pill("SIN PASO DE ESPERMATOZOIDES", 1600, win(T_SNIP + 0.4, 6.1), RED, 820, 34)
        note("TAMAÑO REAL APROXIMADO", win(0.8, 6.1))
    if env == 'anat':
        pill("VASECTOMÍA", 1600, win(6.5, 8.4), CYAN, 520, 48)
        a = win(6.8, 8.4)
        if a > 0:
            label("TESTÍCULOS", P3(tuple(info['testis'] + np.array([1.4, -0.5, -1.0]))), (1020, 1380), "rm", a)
            label("VEJIGA", P3(tuple(info['bladder'])), (60, 520), "lm", a, (255, 236, 170))
        note("MODELO ANATÓMICO SIMPLIFICADO", win(6.5, 8.4))
    if env == 'testis':
        a = win(9.0, 12.4)
        if a > 0:
            label("TÚBULOS: AQUÍ NACEN", P3(tuple(info['cutface'])), (60, 1420), "lm", a, (255, 220, 210))
            label("EPIDÍDIMO", P3(tuple(info['epi'])), (1020, 560), "rm", ease(seg(t, 10.2, 10.6)) * a, (255, 190, 190))
        a = win(WT(2, 5) - 0.2, 12.4)
        if a > 0:
            DARK.append((150, 1500, 930, 1760, a))
            n = 1500 * (t - (WT(2, 5) - 0.2))
            l2.text(P(540, 1580), "+" + fmt_int(n), font=F(M, 80), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(540, 1690), "ESPERMATOZOIDES (≈1,500 / s)", font=F(B, 32), fill=sc3(CYAN, a), anchor="mm")
        note("TESTÍCULO EN CORTE · ILUSTRACIÓN", win(9.0, 12.4))
    if env == 'path':
        a = win(13.0, 16.8)
        if a > 0:
            label("CONDUCTO DEFERENTE", P3(tuple(info['vas_lbl'])), (1020, 600), "rm", a, (255, 236, 210))
        a = win(WT(3, 6) - 0.2, 16.8)
        if a > 0:
            DARK.append((140, 1530, 940, 1720, a))
            l2.text(P(540, 1580), "30 a 45 cm DE LARGO", font=F(B, 40), fill=sc3((255, 236, 210), a), anchor="mm")
            l2.rectangle((*P(200, 1640), *P(880, 1666)), outline=sc3((150, 150, 190), a), width=max(1, int(2 * S)))
            l2.rectangle((*P(200, 1640), *P(200 + 680 * info.get('prog', 0), 1666)), fill=sc3(C_VAS, a))
        note("GROSOR EXAGERADO PARA VERLO", win(13.0, 16.8))
    if env == 'glands':
        a = win(17.3, 21.4)
        if a > 0:
            label("PRÓSTATA", P3(tuple(info['prostate'])), (60, 1400), "lm", ease(seg(t, WT(4, 7) - 0.2, WT(4, 7) + 0.2)) * a, (255, 196, 186))
            label("VESÍCULAS SEMINALES", P3(tuple(info['ves'])), (1020, 600), "rm", ease(seg(t, WT(4, 10) - 0.2, WT(4, 10) + 0.2)) * a, (255, 226, 190))
        note("VISTA DESDE ATRÁS", win(17.3, 21.4))
    if env == 'tube':
        a = win(21.9, 26.4)
        if a > 0:
            DARK.append((600, 1170, 1050, 1640, a))
            rows = (("VESÍCULAS", "65-75%", (255, 230, 150), 0), ("PRÓSTATA", "25-30%", (235, 235, 225), 1), ("ESPERMATOZOIDES", "1-5%", (150, 225, 255), 2))
            for i, (k_, v_, col, li) in enumerate(rows):
                kk = info['layers'][li][2]
                y = 1230 + i * 140
                l2.text(P(630, y), k_, font=F(B, 32), fill=sc3(col, a * kk), anchor="lm")
                l2.text(P(630, y + 52), v_, font=F(M, 46), fill=sc3((245, 245, 255), a * kk), anchor="lm")
        pill("MENOS DEL 5%", 1760, win(WT(5, 10) - 0.2, 26.4), (150, 225, 255), 480, 40)
        note("PROPORCIONES DEL SEMEN · CLEVELAND CLINIC", win(21.9, 26.4), 1860)
    if env == 'clinic':
        a = win(26.9, 31.1)
        if a > 0:
            label("ANESTESIA LOCAL", P3(info['syr']), (60, 1300), "lm", ease(seg(t, WT(6, 1) - 0.2, WT(6, 1) + 0.2)) * a, (210, 236, 255))
            label("PINZA DE ANILLO", P3(info['ring']), (1020, 760), "rm", ease(seg(t, WT(6, 4) - 0.2, WT(6, 4) + 0.2)) * a)
        pill("SIN BISTURÍ", 1600, win(WT(6, 4) - 0.2, 31.1), GREEN, 460, 40)
        pill("ABERTURA DIMINUTA · SIN PUNTOS", 1720, win(WT(6, 10) - 0.2, 31.1), (210, 236, 255), 820, 32)
    if env == 'proc':
        a = win(31.3, T_CUTP + 0.1, 0.3)
        if a > 0:
            label("CONDUCTO DEFERENTE", P3(tuple(info['top'])), (1020, 640), "rm", a, (255, 236, 210))
        a = win(T_CUTP, 35.5)
        if a > 0 and 'ends' in info:
            label("SE CORTA", P3(tuple(info['ends'][0])), (60, 1300), "lm", a * (1 - ease(seg(t, T_SEAL - 0.2, T_SEAL + 0.1))), (255, 210, 190))
            label("PUNTAS SELLADAS", P3(tuple(info['ends'][1])), (1020, 1320), "rm", ease(seg(t, T_SEAL, T_SEAL + 0.3)) * a, (255, 190, 140))
        a = win(WT(7, 7) - 0.2, 35.5)
        if a > 0:
            DARK.append((300, 1520, 780, 1720, a))
            l2.text(P(540, 1590), "≈15 min", font=F(M, 76), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(540, 1680), "POR AMBOS LADOS", font=F(B, 30), fill=sc3(CYAN, a), anchor="mm")
        note("ESQUEMA SIMPLIFICADO", win(31.3, 35.5))
    if env == 'after':
        a = win(36.0, 39.8)
        if a > 0:
            label("CORTE SELLADO", P3(tuple(info['cut'])), (1020, 720), "rm", a, (255, 196, 150))
        pill("NO PASAN", 1560, win(WT(8, 4) - 0.2, 39.8), RED, 400, 40)
        pill("EL CUERPO LOS REABSORBE", 1680, win(WT(8, 9) - 0.2, 39.8), CYAN, 740, 34)
    if env == 'hormone':
        a = win(40.4, 44.0)
        if a > 0:
            label("TESTOSTERONA: IGUAL", P3(tuple(info['vein'])), (60, 560), "lm", a, (255, 220, 140))
            label("SEMEN: CASI IGUAL", P3(tuple(info['ure'])), (1020, 1400), "rm", ease(seg(t, WT(9, 5) - 0.2, WT(9, 5) + 0.2)) * a, (240, 236, 220))
        note("SIN ESPERMATOZOIDES", win(WT(9, 5), 44.0))
    if env == 'lab':
        a = win(44.6, 50.0)
        if a > 0:
            # calendario
            DARK.append((80, 1230, 420, 1520, a))
            wk = int(1 + 11 * ease(seg(t, WT(10, 7) - 0.3, WT(10, 10) + 0.6)))
            l2.text(P(250, 1280), "SEMANA", font=F(B, 30), fill=sc3((220, 225, 245), a), anchor="mm")
            l2.text(P(250, 1380), f"{wk}", font=F(M, 96), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(250, 1470), "≈3 MESES", font=F(B, 30), fill=sc3(CYAN, a * ease(seg(t, WT(10, 9) - 0.2, WT(10, 9) + 0.2))), anchor="mm")
            # vista del microscopio
            cx, cy, r = 760, 1380, 170
            DARK.append((cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 60, a))
            l2.ellipse((*P(cx - r, cy - r), *P(cx + r, cy + r)), fill=sc3((26, 36, 52), a), outline=sc3((200, 220, 255), a), width=max(2, int(3 * S)))
            dens = 1 - ease(seg(t, WT(10, 5), WT(10, 12)))
            rs = np.random.RandomState(6)
            nsp = int(28 * dens)
            for k in range(28):
                ang = rs.uniform(0, 2 * math.pi)
                rr = rs.uniform(0, r - 20)
                x = cx + rr * math.cos(ang) + 12 * math.sin(t * 2 + k)
                y = cy + rr * math.sin(ang) + 12 * math.cos(t * 1.7 + k)
                if k < nsp:
                    hd = 7
                    l2.ellipse((*P(x - hd, y - hd * 0.7), *P(x + hd, y + hd * 0.7)), fill=sc3((220, 236, 255), a))
                    tail = [P(x - hd - 4 * j, y + 4 * math.sin(t * 9 + j + k)) for j in range(8)]
                    l2.line(tail, fill=sc3((200, 220, 255), a * 0.8), width=max(1, int(2 * S)))
            if dens < 0.05:
                check_icon(l2, cx, cy, 70, a * ease(seg(t, WT(10, 12), WT(10, 13))))
            l2.text(P(cx, cy + r + 36), "ANÁLISIS DE SEMEN", font=F(B, 28), fill=sc3((220, 225, 245), a), anchor="mm")
        pill("NO FUNCIONA DE INMEDIATO", 1700, win(WT(10, 1) - 0.2, WT(10, 6)), (255, 200, 120), 760, 34)
        pill("HASTA CONFIRMARLO: OTRO MÉTODO", 1700, win(WT(10, 12) - 0.2, 50.0), (255, 200, 120), 880, 32)
    if env == 'stats':
        a = win(50.5, 55.2)
        if a > 0:
            cx, cy, r = 540, 1200, 170
            DARK.append((cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40, a))
            k = ease(seg(t, WT(11, 2) - 0.2, WT(11, 4) + 0.4))
            l2.arc((*P(cx - r, cy - r), *P(cx + r, cy + r)), -90, -90 + 360 * 0.99 * k, fill=sc3(GREEN, a), width=max(4, int(16 * S)))
            l2.text(P(cx, cy - 10), f"+{int(99 * k)}%", font=F(M, 84), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(cx, cy + 70), "EFECTIVA", font=F(B, 32), fill=sc3(GREEN, a), anchor="mm")
        a = win(WT(11, 5) - 0.2, 55.2)
        if a > 0:
            DARK.append((120, 1460, 960, 1800, a))
            shield_x(l2, 250, 1560, 70, a)
            l2.text(P(350, 1530), "NO PROTEGE CONTRA", font=F(B, 34), fill=sc3((255, 220, 200), a), anchor="lm")
            l2.text(P(350, 1590), "INFECCIONES (ITS)", font=F(B, 34), fill=sc3((255, 220, 200), a), anchor="lm")
            l2.text(P(540, 1720), "PARA ESO: CONDÓN", font=F(B, 36), fill=sc3(CYAN, a * ease(seg(t, WT(11, 11) - 0.2, WT(11, 11) + 0.2))), anchor="mm")
        note("FALLA EN MENOS DE 1 DE CADA 2,000", win(51.0, 55.2), 1880)
    if env == 'hosp':
        pill("SE CONSIDERA PERMANENTE", 1500, win(WT(12, 1) - 0.2, T_OUT), (255, 200, 120), 720, 34)
        a = win(WT(12, 4) - 0.2, T_OUT)
        if a > 0:
            DARK.append((140, 1580, 940, 1800, a))
            l2.text(P(540, 1640), "IMSS: GRATIS", font=F(B, 50), fill=sc3(GREEN, a), anchor="mm")
            l2.text(P(540, 1730), "AUNQUE NO SEAS DERECHOHABIENTE", font=F(B, 28), fill=sc3((230, 235, 250), a), anchor="mm")
        note("REVERTIRLA ES DIFÍCIL Y NO SIEMPRE FUNCIONA", win(WT(12, 2), T_OUT), 1880)
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
        os.makedirs("/home/claude/vas_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/vas_prev/t_{ts}.png")
            print(ts, f"{time.time() - t0:.2f}s", flush=True)
    elif mode == "times":
        for i, ph in enumerate(anim.PH):
            print(i, [round(s, 2) for s in ph['starts']])
        print("T_SNIP", round(T_SNIP, 2), "T_LIFT", round(T_LIFT, 2), "T_CUTP", round(T_CUTP, 2), "T_SEAL", round(T_SEAL, 2), "VAS_LEN", round(VAS_LEN, 1), "S_CUT", round(S_CUT, 1))
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
