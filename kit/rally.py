"""Mente en órbita — Autos de rally por dentro (serie "Lo que no ves") · extra pedido por Efrén.
Escenas: salto de 50 m en un camino de tierra (cámara lenta, contadores) · escáner de rayos X (sello) y jaula que
aguanta una volcadura · tracción 4x4 derrapando en grava · aterrizaje: amortiguador con aceite · 5 G sobre el piloto ·
antilag: flamazos en el escape · turbina que no deja de girar · copiloto cantando notas desde la cabina · Guanajuato a
2,700 m · aire delgado: 20 % menos fuerza · regreso al salto (loop) con Sí/No."""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
import vasec as VS
from nc import proj, P2, vis
from fo import clip_near, line3
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of, VIOLET, BLUE, CYAN, ORANGE)
from gps_geo import (norm, cam_from, cam_keys, polyline3, glow_dot)
import gps_earth as ge
import moto_model as mm
from vasec import draw_faces, bg_studio, vnoise, tube, catmull
import rcar as RC

FPS = 24
RED = (255, 90, 90)
GREEN = (90, 255, 150)
GOLD = (255, 205, 100)
SCAN = (120, 235, 255)
FLAME = (255, 150, 50)

PHR = [
    (0.3, 5.6, "Vas a 170 km/h en un camino de tierra... y tu auto vuela 50 metros.", {2, 13}),
    (6.1, 7.4, "Así se ve por dentro.", {4}),
    (7.9, 11.6, "Te rodea una jaula de tubos de acero: si vuelcas, ella aguanta el golpe.", {3}),
    (12.1, 15.4, "Las cuatro ruedas empujan a la vez, por eso agarra en la grava.", {2}),
    (15.9, 19.4, "Al caer, cada amortiguador frena el golpe con aceite, como un pistón.", {3, 8}),
    (19.9, 22.2, "Y tu cuerpo siente hasta 5 veces su peso.", {5}),
    (22.7, 25.6, "¿Y esas explosiones en el escape? Se llama antilag.", {2, 8}),
    (26.1, 29.6, "Quema gasolina en el escape para que el turbo nunca deje de girar.", {1, 8}),
    (30.1, 34.4, "A tu lado, el copiloto te canta cada curva y cada salto antes de que los veas.", {4}),
    (34.9, 39.6, "En el Rally de México, en Guanajuato, los tramos suben a casi 2,700 metros.", {6, 12}),
    (40.1, 44.4, "Ahí el aire es tan delgado que el motor pierde hasta 20 % de fuerza.", {4, 11}),
    (44.9, 49.9, "Mándaselo a quien maneja como piloto de rally. ¿Te subirías? Sí o no.", {0, 9}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)
_ST = [list(ph['starts']) for ph in anim.PH]


def WT(i, w):
    return _ST[i][w]


CUTS = (5.85, 11.85, 15.65, 19.65, 22.45, 25.85, 29.85, 34.65, 39.85, 44.65)
ENVS = ('hook', 'xray', 'awd', 'land', 'gforce', 'flames', 'turbo', 'cockpit', 'sierra', 'air', 'road2')
T_OUT = 50.3
DUR = 52.6
NF = int(DUR * FPS)


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


# =====================================================================
# Terreno del tramo (m): camino de tierra a lo largo de x, rampa del salto en x∈[-RL, 0]
# =====================================================================
V0 = 47.2            # 170 km/h en m/s
RL = 60.0
G = 9.81


def _land_x(hr):
    s = 2 * hr / RL
    vy = V0 * s / math.sqrt(1 + s * s)
    vx = V0 / math.sqrt(1 + s * s)
    tl = (vy + math.sqrt(vy * vy + 2 * G * hr)) / G
    return vx * tl


_lo, _hi = 0.5, 4.0
for _ in range(40):
    _m = (_lo + _hi) / 2
    if _land_x(_m) < 50.0:
        _lo = _m
    else:
        _hi = _m
HR = _lo
SLOPE = 2 * HR / RL
VX = V0 / math.sqrt(1 + SLOPE ** 2)
VY = V0 * SLOPE / math.sqrt(1 + SLOPE ** 2)
TAU_LAND = (VY + math.sqrt(VY * VY + 2 * G * HR)) / G
X_LAND = VX * TAU_LAND


def h_road(x):
    x = np.asarray(x, np.float64)
    up = HR * np.clip((x + RL) / RL, 0, 1) ** 2
    down = HR * np.clip(1 - x / 7.0, 0, 1) ** 2
    return np.where(x <= 0, up, down)


def h_ter(x, z):
    """altura del terreno: rampa en el camino y terraplén que baja a los lados"""
    az = np.abs(z)
    k = np.clip(1 - (az - 4.2) / 9.0, 0, 1)
    k = k * k * (3 - 2 * k)
    hill = 1.2 * vnoise(np.asarray(x, np.float64) + 300.0, np.asarray(z, np.float64), 38.0, 4) * np.clip((az - 6.0) / 12.0, 0, 1)
    return h_road(x) * k + hill


L_SUN = norm(np.array([0.35, 0.80, -0.48]))


def sky(dx, dy, dz, dusk=0.0):
    e = np.clip(dy, -0.2, 1.0).astype(np.float32)
    top = np.array([62, 120, 200], np.float32) * (1 - dusk) + np.array([40, 46, 92], np.float32) * dusk
    hz = np.array([206, 220, 232], np.float32) * (1 - dusk) + np.array([250, 150, 90], np.float32) * dusk
    k = np.clip(e / 0.45, 0, 1)[..., None] ** 0.7
    out = hz * (1 - k) + top * k
    cosang = np.clip(dx * L_SUN[0] + dy * L_SUN[1] + dz * L_SUN[2], -1, 1)
    out += (np.clip(cosang, 0, 1) ** 40 * 120)[..., None] * np.array([1.0, 0.9, 0.7], np.float32)
    return out


def ground(c, dusk=0.0, blur=0.0):
    dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
    out = sky(dx, dy, dz, dusk)
    cam = np.asarray(c['pos'], np.float64)
    m = dy < -0.002
    rx, ry, rz = dx[m], dy[m], dz[m]
    t = (0.0 - cam[1]) / ry
    t = np.minimum(t, 3000.0)
    for _ in range(4):
        x, z = cam[0] + t * rx, cam[2] + t * rz
        t = np.clip((h_ter(x, z) - cam[1]) / ry, 0.05, 3000.0)
    x, z = cam[0] + t * rx, cam[2] + t * rz
    az = np.abs(z)
    n1 = vnoise(x, z, 3.0, 1)
    n2 = vnoise(x, z, 0.45, 2)
    n3 = vnoise(x, z, 18.0, 3)
    det = np.clip(12.0 / (t + 1.0), 0, 1)
    grass = np.array([150, 140, 88], np.float32) * (1 - n3[:, None]) + np.array([112, 118, 70], np.float32) * n3[:, None]
    grass = grass * (0.82 + 0.3 * (n1[:, None] - 0.5) + 0.25 * det[:, None] * (n2[:, None] - 0.5))
    road = np.array([184, 156, 120], np.float32) * (0.9 + 0.22 * (n1[:, None] - 0.5) + 0.35 * det[:, None] * (n2[:, None] - 0.5))
    rut = np.exp(-((az - 0.85) / 0.28) ** 2)[:, None]
    road = road * (1 - 0.16 * rut)
    kr = np.clip((4.0 - az) / 0.8, 0, 1)[:, None]
    shoulder = np.clip((5.2 - az) / 1.0, 0, 1)[:, None] * (1 - kr)
    col = grass * (1 - kr) + road * kr
    col = col * (1 - 0.3 * shoulder) + np.array([196, 176, 140], np.float32) * 0.3 * shoulder
    # sombreado por la pendiente
    e = 0.15
    hx = (h_ter(x + e, z) - h_ter(x - e, z)) / (2 * e)
    hz_ = (h_ter(x, z + e) - h_ter(x, z - e)) / (2 * e)
    nn = np.stack([-hx, np.ones_like(hx), -hz_], 1)
    nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    lam = np.clip(nn @ L_SUN, 0, 1)
    col = col * (0.55 + 0.55 * lam)[:, None] * (1 - 0.35 * dusk)
    fog = (1 - np.exp(-t / 520.0))[:, None].astype(np.float32)
    fogc = np.array([200, 212, 222], np.float32) * (1 - dusk) + np.array([200, 140, 110], np.float32) * dusk
    col = col * (1 - 0.8 * fog) + fogc * 0.8 * fog
    out[m] = col
    if blur > 0.5:
        k = int(blur)
        acc = out.copy()
        for s in range(1, k + 1):
            acc[:, s:] += out[:, :-s]
            acc[:, :-s] += out[:, s:]
        gm = m.astype(np.float32)[..., None]
        out = out * (1 - gm) + acc / (2 * k + 1) * gm
    return out


# ---------- árboles, cerros lejanos, público ----------
def pine(m, x, z, h, seed):
    rs = np.random.RandomState(seed)
    y0 = float(h_ter(x, z))
    m.cyl((x, y0 + h * 0.15, z), (0, 1, 0), 0.18 * h / 9, h * 0.3, (92, 70, 52), 6, 'tree')
    g = [(46, 78, 46), (56, 88, 50), (40, 70, 44)][rs.randint(3)]
    for (y1, r, hh) in ((0.25, 0.32, 0.5), (0.5, 0.24, 0.42), (0.72, 0.15, 0.3)):
        base = y0 + h * y1
        apex = (x, base + h * hh, z)
        n = 7
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            p0 = (x + h * r * math.cos(a0), base, z + h * r * math.sin(a0))
            p1 = (x + h * r * math.cos(a1), base, z + h * r * math.sin(a1))
            am = (a0 + a1) / 2
            nrm = norm(np.array([math.cos(am), r / hh * 0.9, math.sin(am)]))
            m.face([p0, apex, p1], nrm, g, 'tree')


def build_trees():
    m = mm.Model()
    rs = np.random.RandomState(5)
    for k in range(150):
        x = rs.uniform(-700, 160)
        side = 1 if rs.rand() < 0.6 else -1
        z = side * (9 + rs.uniform(0, 1) ** 1.4 * 90)
        if abs(x) < 70 and abs(z) < 16:
            continue
        pine(m, x, z, rs.uniform(7, 13), k)
    return m


TREES = build_trees()


def build_fans():
    m = mm.Model()
    rs = np.random.RandomState(9)
    cols = [(220, 60, 50), (240, 240, 240), (40, 90, 200), (60, 150, 80), (240, 190, 40), (30, 30, 34)]
    for k in range(34):
        x = rs.uniform(20, 75)
        z = rs.uniform(15, 19)
        y = float(h_ter(x, z))
        cc = cols[rs.randint(len(cols))]
        m.box((x - 0.22, y, z - 0.15), (x + 0.22, y + 0.85, z + 0.15), (50, 54, 70), 'fan')
        m.box((x - 0.25, y + 0.85, z - 0.17), (x + 0.25, y + 1.45, z + 0.17), cc, 'fan')
        m.box((x - 0.12, y + 1.45, z - 0.12), (x + 0.12, y + 1.72, z + 0.12), (200, 160, 130), 'fan')
    # cinta de seguridad
    for k in range(8):
        x0 = 18 + k * 8
        m.beam((x0, float(h_ter(x0, 13.5)) + 0.9, 13.5), (x0 + 8, float(h_ter(x0 + 8, 13.5)) + 0.9, 13.5), 0.05, 0.08, (240, 60, 40) if k % 2 else (240, 240, 240), 'fan')
    return m


FANS = build_fans()


def far_hills(bd, c, dusk=0.0):
    rs = np.random.RandomState(3)
    for (r, colA, amp, seed) in ((1500.0, (150, 162, 176), 140, 1), (900.0, (122, 134, 120), 80, 2)):
        pts = []
        n = 180
        for k in range(n + 1):
            a = 2 * math.pi * k / n
            hh = amp * (0.5 + 0.5 * math.sin(a * 7 + seed) * math.sin(a * 3.1 + 2 * seed)) + 25
            pts.append((r * math.cos(a), hh, r * math.sin(a)))
        col = lc(colA, (170, 120, 110), dusk)
        for i in range(n):
            p0, p1 = pts[i], pts[i + 1]
            quad = [p0, p1, (p1[0], -5, p1[2]), (p0[0], -5, p0[2])]
            q = clip_near(quad, c, 1.0)
            if len(q) >= 3:
                bd.polygon([P2(*p, c) for p in q], fill=tuple(int(v) for v in col))


# =====================================================================
# Dibujo del auto
# =====================================================================
def faces_of(c, model, Rm, pos, L, styles=None, default=None, filt=None, near=0.15):
    out = []
    pos = np.asarray(pos, np.float64)
    cam = np.asarray(c['pos'])
    for (pts, n, col, tag) in model.F:
        st = (styles or {}).get(tag, default or {})
        if st.get('hide'):
            continue
        if filt is not None and not filt(pts.mean(0), tag):
            continue
        Wp = pts @ Rm.T + pos
        nw = Rm @ n
        ctr = Wp.mean(0)
        V = cam - ctr
        V = V / np.linalg.norm(V)
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
        sp = max(0.0, nw @ hh) ** 24 * st.get('spec', 0.35)
        rim = (1 - max(0.0, nw @ V)) ** 3 * 0.22
        k = (0.38 + 0.70 * d) * dim
        colr = tuple(int(min(255, cc[i] * k + 255 * sp * dim + cc[i] * rim)) for i in range(3))
        out.append((dep, [P2(*p, c) for p in q], colr, st.get('alpha'), tag))
    return out


def glass_of(la, c, model, Rm, pos, col, k=1.0, filt=None, near=0.15):
    cam = np.asarray(c['pos'])
    items = []
    for (pts, n, _, tag) in model.F:
        if filt is not None and not filt(pts.mean(0), tag):
            continue
        Wp = pts @ Rm.T + pos
        nw = Rm @ n
        ctr = Wp.mean(0)
        V = cam - ctr
        V = V / np.linalg.norm(V)
        nv = nw @ V
        if nv <= 0:
            continue
        q = clip_near([tuple(p) for p in Wp], c, near)
        if len(q) < 3:
            continue
        f = (1 - nv) ** 2.4
        items.append((proj(*ctr, c)[2], [P2(*p, c) for p in q], sc3(col, k * (0.04 + 0.9 * f))))
    items.sort(key=lambda q: -q[0])
    for dep, pts, cc in items:
        la.polygon(pts, fill=cc)


CAR_ST = {'glass': {'spec': 0.55}, 'lamp': {'spec': 0.0}, 'tail': {'spec': 0.0}}


def draw_car(bd, od, la, c, pos, Rm, L, ang=0.0, comp=0.0, xray=None, show=(), xray_k=1.0, dim=1.0, glow_lamps=0.0):
    """xray: x local del escáner (las caras con x < xray se ven en rayos X); show: etiquetas internas resaltadas"""
    pos = np.asarray(pos, np.float64)
    bpos = pos + Rm @ np.array([0.0, -comp, 0.0])
    cl = Rm.T @ (np.asarray(c['pos']) - pos)
    styles = dict(CAR_ST)
    if dim != 1.0:
        styles = {k: dict(v, dim=dim) for k, v in styles.items()}
    default = {'spec': 0.4, 'dim': dim}
    wst = {'tire': {'spec': 0.08, 'dim': dim}, 'rim': {'spec': 0.5, 'dim': dim}}
    sx = -99.0 if xray is None else xray
    for far in (True, False):
        if not far:
            if xray is not None:
                fl = faces_of(c, RC.INTERNALS, Rm, bpos, L, {}, {'spec': 0.45},
                              filt=lambda p, tag: p[0] < sx + 0.05 and (not show or tag in show or tag in ('seat', 'crew')))
                draw_faces(bd, od, fl)
            fl = faces_of(c, RC.BODY, Rm, bpos, L, styles, default, filt=lambda p, tag: p[0] >= sx)
            draw_faces(bd, od, fl)
            if xray is not None:
                glass_of(la, c, RC.BODY, Rm, bpos, SCAN, 0.9 * xray_k, filt=lambda p, tag: p[0] < sx)
                if show:
                    glass_of(la, c, RC.INTERNALS, Rm, bpos, (255, 150, 70), 0.9 * xray_k, filt=lambda p, tag: tag in show and p[0] < sx)
        for (wx, wz) in RC.WHEELS:
            if (cl[2] * wz < 0) == far:
                Rw = Rm @ RC.rot_z(-ang)
                wp = pos + Rm @ np.array([wx, RC.RW, wz])
                if xray is not None and wx < sx:
                    glass_of(la, c, RC.WHEEL, Rw, wp, SCAN, 0.6 * xray_k)
                    continue
                draw_faces(bd, od, faces_of(c, RC.WHEEL, Rw, wp, L, wst, {'spec': 0.2, 'dim': dim}))
    if glow_lamps > 0:
        for s in (-1.5, -0.5, 0.5, 1.5):
            p = bpos + Rm @ np.array([2.03, 0.82, s * 0.2])
            x, y, dep = proj(*p, c)
            if dep > 0.3 and (Rm @ np.array([1, 0, 0])) @ (np.asarray(c['pos']) - p) > 0:
                glow_dot(la, x * S, y * S, 26 * S * 6 / dep, (255, 240, 200), glow_lamps)


def shadow(img, c, pos, Rm, k=1.0):
    """sombra suave del auto proyectada sobre el terreno"""
    pos = np.asarray(pos, np.float64)
    hgt = pos[1] - float(h_ter(pos[0], pos[2]))
    a = int(150 * k * math.exp(-max(0.0, hgt) / 5.0))
    if a < 4:
        return img
    ly = L_SUN
    pts = []
    for q in np.linspace(0, 2 * math.pi, 28, endpoint=False):
        lp = np.array([2.15 * math.cos(q), 0.5, 1.02 * math.sin(q)])
        wp = pos + Rm @ lp
        t = (wp[1] - float(h_ter(wp[0], wp[2]))) / ly[1]
        gp = wp - ly * t
        gp[1] = float(h_ter(gp[0], gp[2])) + 0.03
        if proj(*gp, c)[2] < 0.3:
            return img
        pts.append(P2(*gp, c))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon(pts, fill=(20, 18, 14, a))
    from PIL import ImageFilter
    sh = sh.filter(ImageFilter.GaussianBlur(5 * S))
    return Image.alpha_composite(img.convert("RGBA"), sh).convert("RGB")


# =====================================================================
# Física del salto (tiempo físico tau; tau=0 al despegar)
# =====================================================================
TK = 3.2        # segundo del video en que despega
SLOW = 0.45     # cámara lenta en el vuelo


def tau_of(t):
    if t < TK:
        return t - TK
    return (t - TK) * SLOW


def car_state(tau):
    """posición del auto (origen bajo el centro, al nivel del piso), pitch y compresión"""
    if tau < 0:
        x = V0 * tau
        y = float(h_road(x))
        pitch = math.atan(2 * HR / RL * clamp((x + RL) / RL, 0, 1))
        return np.array([x, y, 0.0]), pitch, 0.0, True
    if tau < TAU_LAND:
        x = VX * tau
        y = HR + VY * tau - 0.5 * G * tau * tau
        pitch = math.atan(SLOPE) * (1 - tau / TAU_LAND) - 0.06 * math.sin(math.pi * tau / TAU_LAND)
        return np.array([x, y, 0.0]), pitch, 0.0, False
    a = tau - TAU_LAND
    x = X_LAND + VX * a * (1 - 0.2 * min(1.0, a))
    comp = 0.17 * math.exp(-a * 7.0) * math.sin(min(math.pi / 2, a * 40) + max(0.0, a - 0.04) * 22)
    return np.array([x, 0.0, 0.0]), 0.03 * math.sin(a * 20) * math.exp(-a * 5), max(-0.05, comp), True


def wheel_ang(tau):
    return (V0 * tau) / RC.RW


def g_load(tau):
    a = tau - TAU_LAND
    if a < 0:
        return 0.15
    return 1.0 + 4.0 * math.exp(-((a - 0.06) / 0.05) ** 2) if a < 0.4 else 1.0


# polvo: (tau de emisión, posición, velocidad, tamaño)
_rd = np.random.RandomState(4)
DUST = []
for k in range(260):
    te = -3.2 + k * 0.0125
    if -0.02 < te < TAU_LAND + 0.05:
        continue
    p, _, _, _ = car_state(te)
    for s in (1, -1):
        base = p + np.array([-RC.WB - 0.3, 0.2, s * RC.TRACK])
        v = np.array([_rd.uniform(-3, 2), _rd.uniform(0.8, 2.2), s * _rd.uniform(0.3, 1.6)])
        DUST.append((te, base, v, _rd.uniform(0.7, 1.2)))
for k in range(60):
    te = TAU_LAND + _rd.uniform(0, 0.05)
    a = _rd.uniform(0, 2 * math.pi)
    DUST.append((te, np.array([X_LAND + _rd.uniform(-2, 2), 0.2, 1.1 * math.sin(a)]),
                 np.array([_rd.uniform(-2, 6), _rd.uniform(1.5, 4.5), 4.0 * math.sin(a)]), _rd.uniform(1.0, 1.7)))


def draw_dust(od, c, tau, life=2.4, k=1.0):
    items = []
    for (te, p0, v, sz) in DUST:
        a = tau - te
        if a < 0 or a > life:
            continue
        drag = (1 - math.exp(-a * 1.6)) / 1.6
        p = p0 + v * drag + np.array([0, 0.2 * a, 0])
        x, y, dep = proj(*p, c)
        if dep < 0.5:
            continue
        rr = (0.4 + 1.5 * a) * sz * FOC_ / dep * S
        al = int(130 * k * (1 - a / life) * min(1.0, a / 0.08))
        items.append((dep, x * S, y * S, rr, al))
    items.sort(key=lambda q: -q[0])
    for dep, x, y, rr, al in items:
        od.ellipse((x - rr, y - rr * 0.8, x + rr, y + rr * 0.8), fill=(196, 172, 140, al))


FOC_ = 1200.0


def gravel_spray(od, c, pos, Rm, t, n=40, k=1.0, wheels=RC.WHEELS):
    rs = np.random.RandomState(int(t * 24) % 1000)
    for (wx, wz) in wheels:
        for j in range(n // 4):
            a = rs.uniform(0, 0.5)
            lp = np.array([wx - 0.3 - 6 * a, 0.1 + 2.4 * a - 6 * a * a, wz * (1 + 2.5 * a)])
            x, y, dep = proj(*(np.asarray(pos) + Rm @ lp), c)
            if dep < 0.5:
                continue
            r = max(1.0, 0.04 * FOC_ / dep * S)
            od.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=(120, 100, 80, int(220 * k * (1 - a * 1.6))))


# =====================================================================
# Cámaras
# =====================================================================
def cam_look(pos, target, cy=960):
    pos, target = np.asarray(pos, np.float64), np.asarray(target, np.float64)
    v = pos - target
    D = float(np.linalg.norm(v))
    phi = math.degrees(math.asin(v[1] / D))
    cp = math.cos(math.radians(phi))
    yaw = math.degrees(math.atan2(v[0] / (D * cp), -v[2] / (D * cp)))
    return cam_from(D, phi, yaw, cy, tuple(target))


def hook_cam(t):
    tau = tau_of(t)
    p, _, _, _ = car_state(tau)
    if tau < 0:
        f = p + np.array([0.0, 1.0, 0.0])
        D = 11.0 - 2.0 * ease(seg(t, 0, TK))
        yaw = -28 + 14 * ease(seg(t, 0, TK))
        return cam_from(D, 5 + 3 * ease(seg(t, 0.8, TK)), yaw, 1120, tuple(f))
    k = ease(seg(tau, 0, TAU_LAND))
    f = p + np.array([0.0, 0.7, 0.0])
    f[1] = lerp(f[1], 1.4, 0.35)
    return cam_from(9.0 + 2.0 * math.sin(math.pi * min(1.0, tau / TAU_LAND)) + 1.5 * k, 8 - 9 * ease(seg(tau, 0, 0.5)) + 4 * k, -14 + 26 * k, 1120, tuple(f))


# =====================================================================
# Escenas de estudio: piso con rejilla
# =====================================================================
def studio_floor(c, y0=0.0):
    arr = bg_studio((12, 18, 34), (4, 6, 12), (30, 44, 70))
    dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
    cam = c['pos']
    m = dy < -1e-4
    t = (y0 - cam[1]) / dy[m]
    x, z = cam[0] + t * dx[m], cam[2] + t * dz[m]
    gx = np.abs((x / 0.5) - np.round(x / 0.5))
    gz = np.abs((z / 0.5) - np.round(z / 0.5))
    line = np.clip(1 - np.minimum(gx, gz) / (0.035 + 0.004 * t), 0, 1)
    r = np.hypot(x, z)
    base = np.array([16, 22, 36], np.float32) * np.clip(1.3 - r / 9, 0.25, 1.3)[:, None]
    gl = line[:, None] * np.array([40, 70, 110], np.float32) * np.clip(1 - r / 10, 0, 1)[:, None]
    arr[m] = base + gl
    return arr


def scan_ring_x(la, od, c, pos, Rm, sx, a=1.0):
    """anillo del escáner (sello) que recorre el auto a lo largo de x"""
    if a <= 0.01:
        return
    pts = [np.asarray(pos) + Rm @ np.array([sx, 0.70 + 0.95 * math.sin(q), 1.30 * math.cos(q)]) for q in np.linspace(0, 2 * math.pi, 73)]
    polyline3(la, c, pts, sc3(SCAN, a), max(2, int(5 * S)), 0.3)
    q = [P2(*p, c) for p in pts if proj(*p, c)[2] > 0.3]
    if len(q) > 3:
        od.polygon(q, fill=(120, 235, 255, int(30 * a)))


# =====================================================================
# Turbina (esquema)
# =====================================================================
def build_turbine():
    m = mm.Model()
    m.cyl((0, 0, 0), (0, 0, 1), 0.10, 0.5, (170, 176, 186), 14, 'hub', True, (200, 204, 212))
    for k in range(11):
        a = 2 * math.pi * k / 11
        ca, sa = math.cos(a), math.sin(a)
        r0, r1 = 0.10, 0.62
        tw = 0.18
        p = [(r0 * ca, r0 * sa, -0.22), (r1 * ca, r1 * sa, -0.16), (r1 * ca - tw * sa, r1 * sa + tw * ca, 0.16), (r0 * ca - 0.08 * sa, r0 * sa + 0.08 * ca, 0.22)]
        nrm = norm(np.cross(np.subtract(p[1], p[0]), np.subtract(p[3], p[0])))
        m.face(p, nrm, (206, 160, 110), 'blade')
        m.face(p[::-1], -nrm, (186, 140, 96), 'blade')
    return m


TURB = build_turbine()
PIPE = mm.Model()
_pipe_path = catmull([np.array(p, float) for p in ((-5.5, 0.4, 0), (-3.5, 0.2, 0), (-1.6, 0.0, 0), (-0.45, 0.0, 0))], 8)
tube(PIPE, _pipe_path, 0.42, (150, 120, 96), 'pipe', sides=18, caps=False)


# =====================================================================
# Sierra de Guanajuato (relieve ilustrativo, km con altura exagerada)
# =====================================================================
def h_sierra(x, z):
    return (0.55 + 0.75 * math.exp(-((x - 1.0) ** 2 + (z - 0.5) ** 2) / 9.0) + 0.35 * math.exp(-((x + 4) ** 2 + (z - 3) ** 2) / 6.0)
            + 0.08 * math.sin(x * 1.7 + 0.5) * math.sin(z * 1.3) + 0.05 * math.sin(x * 4.1 + z * 3.3))


def build_sierra():
    m = mm.Model()
    xs = np.linspace(-9, 9, 34)
    zs = np.linspace(-7, 9, 30)
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            pts = [(xs[a], h_sierra(xs[a], zs[b]), zs[b]) for (a, b) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            hm = sum(p[1] for p in pts) / 4
            n = (0.5 + 0.5 * math.sin(xs[i] * 2.3 + zs[j] * 1.7))
            if hm > 1.15:
                col = lc((128, 116, 92), (110, 104, 86), n)
            elif hm > 0.8:
                col = lc((96, 110, 66), (120, 120, 74), n)
            else:
                col = lc((150, 138, 92), (136, 128, 84), n)
            pp = [np.asarray(q) for q in pts]
            nn = norm(np.cross(pp[2] - pp[0], pp[1] - pp[3]))
            if nn[1] < 0:
                nn = -nn
                pts = pts[::-1]
            m.face(pts, nn, col, 'ter')
    return m


SIERRA = build_sierra()
_road = []
for k in range(160):
    u = k / 159
    x = -7.5 + 8.5 * u + 0.9 * math.sin(u * 9)
    z = -5.5 + 6.0 * u + 1.1 * math.cos(u * 7)
    _road.append((x, z))
SROAD = [(x, h_sierra(x, z) + 0.015, z) for (x, z) in _road]
ALT0, ALT1 = 1900.0, 2700.0


def sierra_alt(y):
    return ALT0 + (ALT1 - ALT0) * (y - SROAD[0][1]) / (max(p[1] for p in SROAD) - SROAD[0][1])


# =====================================================================
# Render
# =====================================================================
DARK = []
T_SCAN = 6.1


def render(t):
    env = env_at(t)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    info = {}
    c = None

    if env in ('hook', 'road2'):
        if env == 'hook':
            tt = t
        else:
            tt = t - DUR + 0.02          # termina justo donde empieza el video (loop)
        tau = tau_of(tt)
        c = hook_cam(tt)
        pos, pitch, comp, on_g = car_state(tau)
        Rm = RC.car_R(0.0, pitch)
        spd = 1.0 if tau < 0 else SLOW
        arr = ground(c, blur=6 * spd if tau < 0 else 2)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        far_hills(bd, c)
        fl = faces_of(c, TREES, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.02}, near=0.5)
        fl += faces_of(c, FANS, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.05}, near=0.5)
        draw_faces(bd, od, fl)
        base = shadow(base, c, pos, Rm)
        bd = ImageDraw.Draw(base)
        draw_dust(od, c, tau, k=0.7)
        draw_car(bd, od, la, c, pos, Rm, L_SUN, ang=wheel_ang(tau), comp=comp)
        draw_dust(od, c, tau, k=0.35)
        info.update(tau=tau, pos=pos, spd=170.0 if tau < TAU_LAND else max(0.0, 170 - 40 * (tau - TAU_LAND)))
    elif env in ('xray', 'turbo', 'air'):
        if env == 'xray':
            u = ease(seg(t, 5.85, 11.85))
            c = cam_from(8.6 - 1.2 * u, 14 - 4 * u, -38 + 50 * u, 1080, (0.0, 0.85, 0.0))
            arr = studio_floor(c)
            base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            bd = ImageDraw.Draw(base)
            sx = lerp(-2.4, 2.4, ease(seg(t, T_SCAN, T_SCAN + 1.5)))
            # volcadura: el auto gira 360° alrededor de su eje
            roll = 2 * math.pi * ease(seg(t, WT(2, 9) - 0.2, WT(2, 13) + 0.4))
            lift = 0.95 * math.sin(roll / 2)
            pos = np.array([0.0, lift, 0.0])
            Rm = RC.car_R(0.0, 0.0, roll)
            show = () if t < WT(2, 3) - 0.2 else ('cage',)
            Lx = norm((0.3, 0.8, -0.5))
            draw_car(bd, od, la, c, pos, Rm, Lx, ang=0.0, xray=sx if t >= T_SCAN else -2.4, show=show)
            if T_SCAN <= t <= T_SCAN + 1.6:
                scan_ring_x(la, od, c, pos, Rm, sx)
            info['cage'] = proj(*(pos + Rm @ np.array([-0.2, 1.33, -0.6])), c)[:2]
            info['roll'] = roll
        elif env == 'turbo':
            u = ease(seg(t, 25.85, 29.85))
            c = cam_from(5.4 - 0.6 * u, 12, -30 + 22 * u, 1050, (-1.2, 0.3, 0.0))
            arr = studio_floor(c, y0=-0.8)
            base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            bd = ImageDraw.Draw(base)
            Lt = norm((0.4, 0.8, -0.5))
            spin = (t - 25.85) * 7.0 + 2.0 * ease(seg(t, WT(7, 9), WT(7, 12)))
            fl = faces_of(c, TURB, RC.rot_y(math.pi / 2) @ RC.rot_z(0) @ np.array(
                [[math.cos(spin), -math.sin(spin), 0], [math.sin(spin), math.cos(spin), 0], [0, 0, 1]]), (0.0, 0.0, 0.0), Lt, {}, {'spec': 0.5})
            draw_faces(bd, od, fl)
            fl = faces_of(c, PIPE, np.eye(3), (0, 0, 0), Lt, {'pipe': {'alpha': 70}}, {'spec': 0.3})
            draw_faces(bd, od, fl)
            glass_of(la, c, PIPE, np.eye(3), np.zeros(3), (255, 170, 110), 0.7)
            # gasolina que entra y explota en el escape
            rs = np.random.RandomState(11)
            for k in range(26):
                ph = ((t - 25.85) * 0.55 + k / 26.0) % 1.0
                s_ = ph * (len(_pipe_path) - 1)
                i0 = int(s_)
                p = _pipe_path[min(i0, len(_pipe_path) - 1)] + np.array([0, rs.uniform(-0.25, 0.25), rs.uniform(-0.25, 0.25)])
                x, y, dep = proj(*p, c)
                boom = clamp((ph - 0.35) / 0.15)
                if boom <= 0:
                    glow_dot(la, x * S, y * S, 5 * S, (255, 200, 60), 0.9)
                else:
                    fl_ = 1 - clamp((ph - 0.5) / 0.5)
                    glow_dot(la, x * S, y * S, (8 + 26 * boom) * S, (255, 120, 40), 0.85 * fl_)
                    glow_dot(la, x * S, y * S, (4 + 10 * boom) * S, (255, 230, 160), 0.8 * fl_)
            info['blade'] = proj(0.0, 0.62, 0.0, c)[:2]
            info['fuel'] = proj(*_pipe_path[6], c)[:2]
            info['spin'] = spin
        else:
            c = cam_from(9.0, 10, -8 + 6 * ease(seg(t, 39.85, 44.65)), 1000, (0.0, 1.2, 0.0))
            arr = studio_floor(c)
            base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            bd = ImageDraw.Draw(base)
            # dos cubos de aire: nivel del mar vs 2,700 m
            info['boxes'] = []
            for (cx, n, lab) in ((-1.6, 120, 0), (1.6, 88, 1)):
                corners = [(cx + a * 1.2, 1.2 + b * 1.2, d * 1.2) for a in (-1, 1) for b in (-1, 1) for d in (-1, 1)]
                ed = [(0, 1), (0, 2), (0, 4), (3, 1), (3, 2), (3, 7), (5, 1), (5, 4), (5, 7), (6, 2), (6, 4), (6, 7)]
                for (i, j) in ed:
                    line3(la, c, corners[i], corners[j], sc3(CYAN, 0.55), max(1, int(2 * S)), 0.5)
                rs = np.random.RandomState(7 + lab)
                for k in range(n):
                    p0 = rs.uniform(-1.1, 1.1, 3)
                    v = rs.normal(0, 1, 3)
                    pp = p0 + 0.25 * np.sin(v * (t - 39.85) * 2.0 + rs.uniform(0, 6, 3))
                    p = (cx + pp[0], 1.2 + pp[1], pp[2])
                    x, y, dep = proj(*p, c)
                    col = (150, 210, 255) if k % 5 else (255, 140, 140)
                    glow_dot(la, x * S, y * S, 4.5 * S * 9 / dep, col, 0.85)
                info['boxes'].append(proj(cx, 2.6, 0, c)[:2])
    elif env == 'awd':
        u = seg(t, 15.65 - 3.8, 15.65)
        x0 = -500 + V0 * 0.55 * (t - 11.85)
        yaw = 0.30 + 0.06 * math.sin(t * 1.7)
        pos = np.array([x0, float(h_ter(x0, 0.6)), 0.6])
        Rm = RC.car_R(yaw, 0.0, -0.03)
        c = cam_from(10.5, 30, -60 + 22 * ease(seg(t, 11.85, 15.65)), 1180, tuple(pos + np.array([0.0, 0.6, 0.0])))
        arr = ground(c, blur=2)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        far_hills(bd, c)
        fl = faces_of(c, TREES, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.02}, near=0.5)
        draw_faces(bd, od, fl)
        base = shadow(base, c, pos, Rm)
        bd = ImageDraw.Draw(base)
        gravel_spray(od, c, pos, Rm, t, 64)
        draw_car(bd, od, la, c, pos, Rm, L_SUN, ang=t * 30)
        # tracción: flujo de fuerza por la flecha y los semiejes (rayos X superpuestos)
        ka = ease(seg(t, WT(3, 0) - 0.2, WT(3, 2) + 0.2))
        if ka > 0:
            glass_of(la, c, RC.INTERNALS, Rm, pos, (255, 160, 70), 0.9 * ka, filt=lambda p, tag: tag in ('drive', 'engine'))
            for (wx, wz) in RC.WHEELS:
                for j in range(3):
                    ph = ((t * 1.6) + j / 3.0) % 1.0
                    a = np.array([wx * ph, 0.34, 0.0]) if True else None
                    p = np.array([wx, 0.34, 0.0]) + (np.array([wx, RC.RW, wz * 0.82]) - np.array([wx, 0.34, 0.0])) * ph
                    x, y, dep = proj(*(pos + Rm @ p), c)
                    glow_dot(la, x * S, y * S, 7 * S, (255, 220, 120), ka)
            info['wheels'] = [proj(*(pos + Rm @ np.array([wx, RC.RW, wz * 1.25])), c)[:2] for (wx, wz) in RC.WHEELS]
        info['ka'] = ka
    elif env in ('land', 'gforce'):
        if env == 'land':
            tau = TAU_LAND - 0.08 + (t - 15.65) * 0.07
            pos, pitch, comp, _ = car_state(tau)
            Rm = RC.car_R(0.0, pitch)
            fw_ = pos + Rm @ np.array([RC.WB, RC.RW, -RC.TRACK])
            c = cam_from(4.6 - 0.6 * ease(seg(t, 15.65, 19.65)), 6, -30, 1160, tuple(np.array([fw_[0] - 0.2, 0.75, 0.0])))
        else:
            tau = TAU_LAND - 0.10 + (t - 19.65) * 0.09
            pos, pitch, comp, _ = car_state(tau)
            Rm = RC.car_R(0.0, pitch)
            c = cam_from(7.4, 9, 58 - 8 * ease(seg(t, 19.65, 22.45)), 1120, tuple(pos + np.array([0.3, 0.8, 0.0])))
        arr = ground(c)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        far_hills(bd, c)
        fl = faces_of(c, TREES, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.02}, near=0.5)
        fl += faces_of(c, FANS, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.05}, near=0.5)
        draw_faces(bd, od, fl)
        base = shadow(base, c, pos, Rm)
        bd = ImageDraw.Draw(base)
        draw_dust(od, c, tau, k=0.5)
        if env == 'land':
            draw_car(bd, od, la, c, pos, Rm, L_SUN, ang=wheel_ang(tau), comp=comp)
            ka = ease(seg(t, WT(4, 3) - 0.3, WT(4, 3) + 0.2))
            if ka > 0:
                glass_of(la, c, RC.INTERNALS, Rm, pos + Rm @ np.array([0, -comp, 0]), (255, 210, 90), ka,
                         filt=lambda p, tag: tag == 'shock' and p[0] > 0)
            info['shock'] = proj(*(pos + Rm @ np.array([RC.WB, 0.7, -0.75])), c)[:2]
        else:
            draw_car(bd, od, la, c, pos, Rm, L_SUN, ang=wheel_ang(tau), comp=comp, xray=2.4, show=('crew', 'seat'), xray_k=0.8)
            info['crew'] = proj(*(pos + Rm @ np.array([-0.38, 1.1 - comp, 0.38])), c)[:2]
        info['comp'] = comp
        info['g'] = g_load(tau)
        info['tau'] = tau
    elif env == 'flames':
        x0 = -260 + 16 * (t - 22.45)
        pos = np.array([x0, float(h_ter(x0, 0.0)), 0.0])
        Rm = RC.car_R(0.05, 0.02)
        c = cam_from(6.2 - 0.8 * ease(seg(t, 22.45, 25.85)), 7, 160 - 25 * ease(seg(t, 22.45, 25.85)), 1080, tuple(pos + np.array([-1.0, 0.6, 0.0])))
        arr = ground(c, dusk=0.75)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        far_hills(bd, c, 0.75)
        fl = faces_of(c, TREES, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.02, 'dim': 0.55}, near=0.5)
        draw_faces(bd, od, fl)
        base = shadow(base, c, pos, Rm, 0.6)
        bd = ImageDraw.Draw(base)
        Ld = norm((-0.6, 0.5, -0.4))
        draw_car(bd, od, la, c, pos, Rm, Ld, ang=t * 20, dim=0.85, glow_lamps=0.0)
        # flamazos del antilag: ráfagas irregulares
        ex = pos + Rm @ np.array([-2.12, 0.36, 0.52])
        xe, ye, de = proj(*ex, c)
        rs = np.random.RandomState(int(t * 24))
        bang = 0.0
        for tb in (22.9, 23.35, 23.6, 24.2, 24.45, 24.9, 25.3, 25.55):
            bang = max(bang, math.exp(-max(0.0, t - tb) * 9) if t >= tb else 0.0)
        if bang > 0.05:
            dirv = Rm @ np.array([-1.0, 0.05, 0.1])
            for k in range(9):
                p = ex + dirv * (0.1 + 0.28 * k * bang) + rs.normal(0, 0.03 * k, 3)
                x, y, dep = proj(*p, c)
                r = (0.40 - 0.03 * k) * FOC_ / dep * S * (0.6 + 0.8 * bang)
                glow_dot(la, x * S, y * S, max(1.0, r), lc((255, 230, 160), (255, 90, 30), k / 8), bang)
            for k in range(14):
                v = dirv * rs.uniform(1, 3) + rs.normal(0, 0.6, 3)
                a = rs.uniform(0, 0.4)
                p = ex + v * a
                x, y, dep = proj(*p, c)
                glow_dot(la, x * S, y * S, 2 * S, (255, 200, 90), bang * (1 - a * 2))
            glow_dot(la, xe * S, ye * S, 90 * S * bang, (120, 50, 10), 0.6 * bang)
        info['exhaust'] = (xe, ye)
        info['bang'] = bang
    elif env == 'cockpit':
        u = t - 29.85
        x0 = -330 + 32 * u
        eye = np.array([x0 + 0.1, float(h_ter(x0, 0.38)) + 1.12, 0.38])
        sway = 0.02 * math.sin(u * 7) + 0.01 * math.sin(u * 13)
        target = eye + np.array([30.0, -1.6 + 30 * sway, -1.2 * math.sin(u * 0.8)])
        c = cam_look(eye, target, 900)
        arr = ground(c, blur=3)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        far_hills(bd, c)
        fl = faces_of(c, TREES, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.02}, near=0.5)
        fl += faces_of(c, FANS, np.eye(3), (0, 0, 0), L_SUN, {}, {'spec': 0.05}, near=0.5)
        draw_faces(bd, od, fl)
        cockpit_frame(bd, t, u)
    elif env == 'sierra':
        u = ease(seg(t, 34.65, 39.85))
        c = cam_from(17 - 3 * u, 30 + 6 * u, -24 + 26 * u, 1080, (-1.5, 0.9, 0.5))
        dx, dy, dz = ge.ray_dirs(c, 0, 0, W, H)
        arr = sky(dx, dy, dz) * 0.95
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        Ls = norm((0.5, 0.75, -0.4))
        fl = faces_of(c, SIERRA, np.eye(3), (0, 0, 0), Ls, {}, {'spec': 0.03}, near=0.5)
        draw_faces(bd, od, fl)
        kr = ease(seg(t, WT(9, 6) - 0.4, 39.6))
        n = max(2, int(len(SROAD) * kr))
        polyline3(bd, c, SROAD, (214, 196, 160), max(2, int(4 * S)), 0.5)
        polyline3(la, c, SROAD[:n], sc3(GOLD, 0.9), max(2, int(5 * S)), 0.5)
        p = SROAD[n - 1]
        x, y, dep = proj(*p, c)
        glow_dot(la, x * S, y * S, 12 * S, (255, 255, 255), 0.9)
        info['alt'] = clamp(sierra_alt(p[1]), ALT0, ALT1)
        info['car'] = (x, y)
        info['top'] = proj(*max(SROAD, key=lambda q: q[1]), c)[:2]
        info['k'] = kr

    # ---------- composición ----------
    imgA = base.convert("RGBA")
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")
    LAa = np.asarray(LA, np.float32)
    gl = glow_of(LA, 4)
    out = np.asarray(imgB, np.float32) + LAa + 1.3 * gl
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    out = out * (0.55 + 0.45 * np.clip(yy / (H * 0.26), 0, 1))
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :, None]
    out = out * (1 - 0.18 * xx ** 2)
    f = 1.0
    for ct in CUTS:
        f = min(f, clamp(abs(t - ct) / 0.18))
    flash = 0.0
    if env == 'hook':
        flash = math.exp(-max(0.0, info['tau'] - TAU_LAND) * 30) if info['tau'] >= TAU_LAND else 0.0
    out = out * (0.35 + 0.65 * f) + 60 * flash
    out = out * (1 - 0.88 * seg(t, T_OUT, T_OUT + 0.8))
    L2 = Image.new("RGB", (W, H), (0, 0, 0))
    l2 = ImageDraw.Draw(L2)
    anim.draw_caption(l2, t)
    DARK.clear()
    if env in ('hook', 'road2', 'awd', 'land', 'gforce', 'cockpit', 'sierra', 'flames'):
        DARK.append((40, 150, 1040, 430, 0.9))
    hud(l2, c, t, env, info)
    if DARK:
        mk = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mk)
        for (x0, y0, x1, y1, a) in DARK:
            md.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=int(30 * S), fill=int(255 * 0.62 * a))
        out = out * (1 - np.asarray(mk, np.float32)[..., None] / 255.0)
    out = out + np.asarray(L2, np.float32) + 1.2 * glow_of(L2, 3)
    out = out * (seg(t, 0.0, 0.12) * (1 - seg(t, DUR - 0.35, DUR)) * 0.85 + 0.15 if t < 0.12 or t > DUR - 0.35 else 1.0)
    return np.clip(out, 0, 255).astype(np.uint8)


def cockpit_frame(bd, t, u):
    """cabina vista desde el piloto: tablero, pilares, jaula y copiloto con su libreta"""
    sh = 6 * math.sin(u * 9) + 3 * math.sin(u * 17)
    # tablero
    bd.polygon([P(-20, 1480 + sh), P(1100, 1440 + sh), P(1100, 1940), P(-20, 1940)], fill=(26, 27, 31))
    bd.polygon([P(-20, 1480 + sh), P(1100, 1440 + sh), P(1100, 1470 + sh), P(-20, 1512 + sh)], fill=(44, 46, 52))
    # pilares A y marco del parabrisas
    bd.polygon([P(-20, 380 + sh), P(60, 380 + sh), P(190, 1490 + sh), P(-20, 1500 + sh)], fill=(20, 21, 24))
    bd.polygon([P(1020, 360 + sh), P(1100, 360 + sh), P(1100, 1450 + sh), P(890, 1450 + sh)], fill=(20, 21, 24))
    bd.rectangle((*P(-20, 0), *P(1100, 380 + sh)), fill=(30, 31, 36))
    # jaula naranja
    for (a, b) in (((40, 380), (240, 1460)), ((1040, 370), (850, 1440)), ((-20, 330), (1100, 320))):
        bd.line([P(a[0], a[1] + sh), P(b[0], b[1] + sh)], fill=(214, 86, 38), width=int(26 * S))
    # volante
    cx, cy = 300, 1700 + sh
    bd.ellipse((*P(cx - 250, cy - 250), *P(cx + 250, cy + 250)), outline=(18, 18, 20), width=int(46 * S))
    bd.rectangle((*P(cx - 40, cy - 20), *P(cx + 40, cy + 260)), fill=(18, 18, 20))
    # copiloto: casco y libreta
    hx, hy = 860, 1250 + sh * 1.2
    bd.ellipse((*P(hx - 150, hy - 170), *P(hx + 150, hy + 150)), fill=(232, 234, 238))
    bd.chord((*P(hx - 150, hy - 170), *P(hx + 150, hy + 150)), 150, 250, fill=(30, 34, 44))
    bd.line([P(hx - 20, hy - 168), P(hx + 60, hy + 140)], fill=(40, 90, 200), width=int(30 * S))
    bd.polygon([P(640, 1940), P(700, 1560 + sh), P(1060, 1520 + sh), P(1100, 1940)], fill=(40, 90, 200))
    bd.polygon([P(600, 1700 + sh), P(900, 1640 + sh), P(940, 1860 + sh), P(630, 1920 + sh)], fill=(246, 244, 236))
    for k in range(5):
        y = 1700 + 40 * k + sh
        bd.line([P(640, y + 10 - 8 * k * 0.1), P(900, y - 45 + 10)], fill=(90, 96, 110), width=max(1, int(3 * S)))


# =====================================================================
# HUD
# =====================================================================
def fmt_int(n):
    return f"{int(n):,}"


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
            l2.text(P(1040, y), txt, font=F(B, 22), fill=sc3((205, 205, 225), a * 0.9), anchor="rm")

    def win(a, b, e=0.3):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def counter(big, small, y, a, col=(255, 226, 190), w=700):
        if a <= 0:
            return
        DARK.append((540 - w / 2, y - 95, 540 + w / 2, y + 95, a))
        l2.text(P(540, y - 22), big, font=F(M, 96), fill=sc3((244, 246, 255), a), anchor="mm")
        l2.text(P(540, y + 60), small, font=F(B, 30), fill=sc3(col, a), anchor="mm")

    for ct in CUTS:
        if abs(t - ct) < 0.18:
            return
    if env in ('hook', 'road2'):
        tau = info['tau']
        a = win(0.1, 5.85) if env == 'hook' else win(44.8, T_OUT)
        if env == 'hook' and a > 0:
            # velocímetro y metros en el aire
            DARK.append((60, 1500, 500, 1720, a))
            l2.text(P(280, 1580), f"{info['spd']:.0f}", font=F(M, 96), fill=sc3((244, 246, 255), a), anchor="mm")
            l2.text(P(280, 1675), "km/h", font=F(B, 30), fill=sc3((255, 226, 190), a), anchor="mm")
            ka = ease(seg(tau, -0.05, 0.05))
            if ka > 0:
                d = 50.0 * clamp(info['pos'][0] / X_LAND, 0, 1)
                DARK.append((580, 1500, 1020, 1720, a * ka))
                l2.text(P(800, 1580), f"{d:.0f} m", font=F(M, 96), fill=sc3((244, 246, 255), a * ka), anchor="mm")
                l2.text(P(800, 1675), "EN EL AIRE", font=F(B, 30), fill=sc3(CYAN, a * ka), anchor="mm")
            pill("CÁMARA LENTA", 1790, a * ease(seg(tau, 0.02, 0.12)) * (1 - ease(seg(t, 5.3, 5.8))), (255, 200, 120), 420, 30)
            note("RECREACIÓN · AUTO GENÉRICO", a, 1880)
        if env == 'road2':
            pill("MÁNDASELO A QUIEN MANEJA ASÍ", 1540, win(45.0, T_OUT), (255, 200, 120), 860, 34)
            a = win(WT(11, 9) - 0.2, T_OUT)
            if a > 0:
                for (x0, txt, col) in ((300, "SÍ", GREEN), (780, "NO", RED)):
                    DARK.append((x0 - 150, 1650, x0 + 150, 1800, a))
                    l2.rounded_rectangle((*P(x0 - 130, 1665), *P(x0 + 130, 1780)), radius=int(30 * S), outline=sc3(col, a), width=max(3, int(4 * S)))
                    l2.text(P(x0, 1722), txt, font=F(B, 56), fill=sc3(col, a), anchor="mm")
                l2.text(P(540, 1850), "¿TE SUBIRÍAS? RESPONDE EN COMENTARIOS", font=F(B, 26), fill=sc3((220, 220, 240), a), anchor="mm")
    if env == 'xray':
        pill("ESCÁNER: RAYOS X", 1640, win(T_SCAN - 0.1, T_SCAN + 1.8), SCAN, 560, 34)
        a = win(WT(2, 3) - 0.2, 11.8)
        if a > 0:
            label("JAULA DE TUBOS DE ACERO", info['cage'], (1020, 560), "rm", a, (255, 190, 150))
            kr = ease(seg(t, WT(2, 9) - 0.2, WT(2, 9) + 0.2)) * a
            if kr > 0:
                deg = math.degrees(info['roll'])
                counter(f"{deg:.0f}°", "VOLCADURA · LA JAULA AGUANTA", 1620, kr, (255, 200, 160), 760)
        note("RECREACIÓN · ESQUEMA SIMPLIFICADO", win(6.0, 11.8))
    if env == 'awd':
        a = win(12.0, 15.6) * info.get('ka', 0)
        if a > 0:
            DARK.append((330, 1560, 750, 1740, a))
            l2.text(P(540, 1630), "4×4", font=F(B, 92), fill=sc3((255, 220, 140), a), anchor="mm")
            l2.text(P(540, 1710), "LAS 4 RUEDAS EMPUJAN", font=F(B, 28), fill=sc3((235, 235, 245), a), anchor="mm")
        note("GRAVA · RECREACIÓN", win(12.0, 15.6))
    if env == 'land':
        a = win(16.0, 19.6)
        if a > 0:
            label("AMORTIGUADOR", info['shock'], (60, 560), "lm", ease(seg(t, WT(4, 3) - 0.3, WT(4, 3) + 0.1)) * a, (255, 220, 140))
            damper(l2, 790, 1500, info['comp'], a * ease(seg(t, WT(4, 6) - 0.3, WT(4, 6) + 0.2)), t)
        note("CÁMARA LENTA · ESQUEMA", win(16.0, 19.6))
    if env == 'gforce':
        a = win(19.9, 22.4)
        if a > 0:
            gmax = max(1.0, max(g_load(tt) for tt in np.linspace(TAU_LAND - 0.1, info["tau"], 40)))
            label("TÚ", info['crew'], (60, 560), "lm", a, (220, 236, 255))
            DARK.append((150, 1460, 930, 1800, a))
            l2.text(P(540, 1545), f"{gmax:.1f} G", font=F(M, 104), fill=sc3((244, 246, 255), a), anchor="mm")
            n = int(round(gmax))
            for k in range(5):
                x = 540 + (k - 2) * 120
                on = k < n
                col = (255, 200, 120) if on else (90, 90, 110)
                l2.ellipse((*P(x - 18, 1640), *P(x + 18, 1676)), fill=sc3(col, a))
                l2.rounded_rectangle((*P(x - 30, 1682), *P(x + 30, 1760)), radius=int(14 * S), fill=sc3(col, a))
            l2.text(P(540, 1785), "VECES TU PESO AL ATERRIZAR", font=F(B, 26), fill=sc3((235, 235, 245), a), anchor="mm")
        note("RECREACIÓN · PICO DE HASTA 5 G", win(19.9, 22.4))
    if env == 'flames':
        a = win(22.8, 25.8)
        if a > 0:
            label("ESCAPE", info['exhaust'], (1020, 560), "rm", a, (255, 200, 150))
            pill("ANTILAG", 1660, a * ease(seg(t, WT(6, 8) - 0.2, WT(6, 8) + 0.2)), FLAME, 380, 40)
        note("RECREACIÓN", win(22.8, 25.8))
    if env == 'turbo':
        a = win(26.1, 29.8)
        if a > 0:
            label("GASOLINA QUE EXPLOTA", info['fuel'], (60, 560), "lm", ease(seg(t, WT(7, 1) - 0.2, WT(7, 1) + 0.2)) * a, (255, 200, 120))
            label("TURBO", info['blade'], (1020, 700), "rm", ease(seg(t, WT(7, 8) - 0.2, WT(7, 8) + 0.2)) * a, (220, 236, 255))
            kb = ease(seg(t, WT(7, 9) - 0.2, WT(7, 9) + 0.3)) * a
            pill("NUNCA DEJA DE GIRAR", 1660, kb, (255, 200, 120), 640, 34)
        note("ESQUEMA SIMPLIFICADO", win(26.1, 29.8))
    if env == 'cockpit':
        notes = ((30.3, "4 IZQUIERDA"), (31.4, "100 · SALTO"), (32.5, "NO CORTES"), (33.4, "6 DERECHA"))
        for i, (ta, txt) in enumerate(notes):
            tb = notes[i + 1][0] if i + 1 < len(notes) else 34.5
            a = win(ta, tb, 0.15)
            if a > 0:
                DARK.append((260, 640, 820, 760, a))
                l2.rounded_rectangle((*P(270, 650), *P(810, 750)), radius=int(20 * S), outline=sc3((255, 220, 120), a), width=max(2, int(3 * S)))
                l2.text(P(540, 700), txt, font=F(B, 54), fill=sc3((255, 240, 200), a), anchor="mm")
        pill("NOTAS DEL COPILOTO", 520, win(30.2, 34.5), (255, 220, 120), 560, 30)
        note("RECREACIÓN · NOTAS DE EJEMPLO", win(30.2, 34.5), 1420)
    if env == 'sierra':
        a = win(35.0, 39.8)
        if a > 0:
            DARK.append((150, 1460, 930, 1720, a))
            alt = info['alt'] if info['k'] > 0.01 else ALT0
            l2.text(P(540, 1545), fmt_int(round(alt, -1)) + " m", font=F(M, 96), fill=sc3((244, 246, 255), a), anchor="mm")
            l2.text(P(540, 1650), "ALTURA SOBRE EL NIVEL DEL MAR", font=F(B, 28), fill=sc3(GOLD, a), anchor="mm")
            label("GUANAJUATO", info['top'], (1020, 560), "rm", ease(seg(t, WT(9, 6) - 0.2, WT(9, 6) + 0.2)) * a, (255, 220, 160))
        note("RELIEVE ILUSTRATIVO · ESCALA EXAGERADA", win(35.0, 39.8))
    if env == 'air':
        a = win(40.0, 44.6)
        if a > 0:
            (x0, y0), (x1, y1) = info['boxes']
            for (x, y, txt, sub) in ((x0, y0, "NIVEL DEL MAR", "100 % DE AIRE"), (x1, y1, "2,700 m", "≈ 73 % DE AIRE")):
                DARK.append((x - 200, y - 110, x + 200, y - 10, a))
                l2.text(P(x, y - 80), txt, font=F(B, 32), fill=sc3((240, 244, 255), a), anchor="mm")
                l2.text(P(x, y - 38), sub, font=F(B, 26), fill=sc3(CYAN, a), anchor="mm")
            kp = ease(seg(t, WT(10, 9) - 0.4, WT(10, 12) + 0.3)) * a
            DARK.append((140, 1440, 940, 1760, a))
            l2.text(P(540, 1490), "FUERZA DEL MOTOR", font=F(B, 30), fill=sc3((235, 235, 245), a), anchor="mm")
            pct = 100 - 20 * kp
            l2.rectangle((*P(190, 1540), *P(890, 1600)), outline=sc3((150, 150, 190), a), width=max(1, int(2 * S)))
            l2.rectangle((*P(190, 1540), *P(190 + 7 * pct, 1600)), fill=sc3(lc((90, 255, 150), (255, 160, 60), kp), a))
            l2.text(P(540, 1680), f"{pct:.0f} %", font=F(M, 72), fill=sc3((244, 246, 255), a), anchor="mm")
        note("DENSIDAD APROX. · HASTA 20 % MENOS POTENCIA", win(40.0, 44.6))
    ta = ease(seg(t, T_OUT + 0.2, T_OUT + 1.0))
    if ta > 0:
        l2.text(P(540, 900), "Mente en órbita", font=F(B, 112), fill=sc3((240, 235, 255), ta), anchor="mm")
        ang = 2 * math.pi * (t - T_OUT) / 3.0
        ox, oy = 540 + 440 * math.cos(ang), 900 + 130 * math.sin(ang)
        l2.ellipse((*P(540 - 440, 900 - 130), *P(540 + 440, 900 + 130)), outline=sc3(VIOLET, 0.45 * ta), width=max(1, int(2 * S)))
        rr = 9 * S
        px, py = P(ox, oy)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, ta))


def damper(l2, cx, cy, comp, a, t):
    """corte del amortiguador: pistón que empuja aceite por orificios"""
    if a <= 0:
        return
    DARK.append((cx - 200, cy - 330, cx + 200, cy + 330, a))
    l2.rounded_rectangle((*P(cx - 70, cy - 230), *P(cx + 70, cy + 250)), radius=int(18 * S), outline=sc3((220, 225, 240), a), width=max(2, int(3 * S)))
    l2.rectangle((*P(cx - 64, cy - 150), *P(cx + 64, cy + 244)), fill=sc3((200, 150, 40), a * 0.85))
    py = cy - 60 + comp * 900
    l2.rectangle((*P(cx - 12, cy - 300), *P(cx + 12, py)), fill=sc3((210, 214, 222), a))
    l2.rectangle((*P(cx - 64, py - 16), *P(cx + 64, py + 16)), fill=sc3((150, 156, 170), a))
    for dx in (-36, 0, 36):
        l2.rectangle((*P(cx + dx - 5, py - 16), *P(cx + dx + 5, py + 16)), fill=sc3((200, 150, 40), a))
        k = clamp(comp * 9, 0, 1)
        if k > 0.05:
            for j in range(3):
                yy = py - 22 - j * 22 - (t * 120 % 22)
                l2.ellipse((*P(cx + dx - 5, yy - 5), *P(cx + dx + 5, yy + 5)), fill=sc3((255, 230, 140), a * k))
    l2.text(P(cx, cy + 290), "ACEITE", font=F(B, 28), fill=sc3((255, 220, 140), a), anchor="mm")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        os.makedirs("/home/claude/rally_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/rally_prev/t_{ts}.png")
            print(ts, f"{time.time() - t0:.2f}s", flush=True)
    elif mode == "times":
        for i, ph in enumerate(anim.PH):
            print(i, [round(s, 2) for s in ph['starts']])
        print("HR", round(HR, 2), "X_LAND", round(X_LAND, 1), "TAU_LAND", round(TAU_LAND, 3))
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
