"""Mente en órbita — El tiempo no pasa igual para ti y para un satélite (Relatividad) · video 7.
Escenas: satélite GPS y dos relojes · malla del espacio-tiempo · reloj de luz (velocidad) · GPS a 14,000 km/h ·
pozo de gravedad (+45) y marcador (+38) · Estación Espacial (gana la velocidad, Scott Kelly) · sala: cabeza vs pies ·
laboratorio: reloj atómico de estroncio en rayos X · cierre."""
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
import gps

FPS = 24
DUR = 65.8
NF = int(DUR * FPS)
RED = (255, 90, 90)
GREEN = (90, 255, 150)
GOLD = (255, 210, 110)

PHR = [
    (0.3, 4.2, "El tiempo no pasa igual para ti y para un satélite.", {4}),
    (4.6, 7.0, "Y no es ciencia ficción: es relatividad.", {6}),
    (7.5, 12.4, "Einstein descubrió que el tiempo cambia con dos cosas: la velocidad y la gravedad.", {0}),
    (12.9, 17.4, "Primero, la velocidad: mientras más rápido te mueves, más lento pasa tu tiempo.", {2}),
    (17.9, 24.5, "Un satélite GPS va a casi catorce mil kilómetros por hora: su reloj se atrasa siete microsegundos al día.", {14}),
    (25.0, 28.8, "Segundo, la gravedad: mientras más fuerte, más lento pasa el tiempo.", {2}),
    (29.3, 34.2, "Allá arriba la gravedad es más débil: su reloj se adelanta cuarenta y cinco.", {10}),
    (34.7, 38.2, "Gana la gravedad: treinta y ocho microsegundos de adelanto diario.", {2}),
    (38.7, 43.9, "Pero en la Estación Espacial, que va más rápido y más bajo, gana la velocidad.", {14}),
    (44.4, 52.0, "Por eso el astronauta Scott Kelly, tras más de 500 días en órbita, envejeció 5 milésimas de segundo menos que su gemelo.", {15}),
    (52.5, 57.7, "Y sin ir al espacio: tu cabeza envejece un poquito más rápido que tus pies.", {6}),
    (58.2, 62.0, "Ya lo midieron con relojes atómicos... a un milímetro de altura.", {8}),
    (62.6, 64.6, "¿Qué quieres que explique después?", {3}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)

CUTS = (7.25, 12.65, 24.75, 38.45, 52.25, 57.95)
ENVS = ('hook', 'grid', 'speed', 'gravity', 'iss', 'home', 'lab')
T_OUT = 62.3


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


draw_stars = gps.draw_stars


# =====================================================================
# Malla del espacio-tiempo (unidades: radios terrestres ×1000)
# =====================================================================
RE_G = 1000.0
RG_G = 4170.0  # órbita GPS en la misma escala


def well(r, depth=1.0):
    return -depth * 5200.0 * 1100.0 / math.sqrt(r * r + 1100.0 ** 2)


def draw_grid(la, c, t, depth=1.0, a=1.0, ext=9000.0, n=26, col=VIOLET):
    lw = max(1, int(2 * S))
    ys = lambda x, z: -1200.0 + well(math.hypot(x, z), depth) * 1.0
    for i in range(n + 1):
        u = -ext + 2 * ext * i / n
        pts = [(u, ys(u, v), v) for v in np.linspace(-ext, ext, 80)]
        polyline3(la, c, pts, sc3(col, 0.45 * a), lw, 50.0)
        pts = [(v, ys(v, u), u) for v in np.linspace(-ext, ext, 80)]
        polyline3(la, c, pts, sc3(col, 0.45 * a), lw, 50.0)


def orbit_pts(r, y=0.0, k=120, inc=0.0):
    return [(r * math.cos(q), y + r * math.sin(q) * math.sin(inc), r * math.sin(q) * math.cos(inc)) for q in np.linspace(0, 2 * math.pi, k + 1)]


def clock_icon(l2, x, y, r, a, rate, t, col, label=None, sub=None):
    """reloj analógico en la capa HUD; rate = vueltas por segundo de la manecilla"""
    if a <= 0:
        return
    l2.ellipse((*P(x - r, y - r), *P(x + r, y + r)), outline=sc3(col, a), width=max(2, int(4 * S)))
    for k in range(12):
        q = 2 * math.pi * k / 12
        l2.line([P(x + 0.82 * r * math.sin(q), y - 0.82 * r * math.cos(q)), P(x + 0.95 * r * math.sin(q), y - 0.95 * r * math.cos(q))],
                fill=sc3(col, a * 0.8), width=max(1, int(2 * S)))
    q = 2 * math.pi * rate * t
    l2.line([P(x, y), P(x + 0.8 * r * math.sin(q), y - 0.8 * r * math.cos(q))], fill=sc3((255, 255, 255), a), width=max(2, int(4 * S)))
    q2 = q / 12
    l2.line([P(x, y), P(x + 0.5 * r * math.sin(q2), y - 0.5 * r * math.cos(q2))], fill=sc3((255, 255, 255), a), width=max(2, int(6 * S)))
    if label:
        l2.text(P(x, y + r + 34), label, font=F(B, 30), fill=sc3((230, 230, 245), a), anchor="mm")
    if sub:
        l2.text(P(x, y + r + 74), sub, font=F(M, 30), fill=sc3(col, a), anchor="mm")


# =====================================================================
# Estación Espacial (metros, genérica y estilizada)
# =====================================================================
def build_iss():
    m = mm.Model()
    m.beam((-55, 0, 0), (55, 0, 0), 3.0, 3.0, (170, 172, 180), side=(0, 1, 0))
    for x in (-50, -38, 38, 50):
        for s in (-1, 1):
            m.box((x - 5.5, -0.1, s * 3), (x + 5.5, 0.1, s * 36), (178, 118, 56), 'panel')
            m.beam((x, 0, s * 1.5), (x, 0, s * 3.2), 0.6, 0.6, (150, 152, 160), side=(1, 0, 0))
    for (z0, z1) in ((-14, -4), (-4, 6), (6, 16)):
        m.cyl((0, -3, (z0 + z1) / 2), (0, 0, 1), 2.2, z1 - z0 - 0.4, (226, 228, 234), 16)
    m.cyl((-7, -3, 2), (1, 0, 0), 2.0, 9, (222, 224, 230), 14)
    m.cyl((7, -3, -6), (1, 0, 0), 2.0, 9, (222, 224, 230), 14)
    for x in (-22, 22):
        m.box((x - 7, -0.08, -1.2), (x + 7, 0.08, -13), (236, 238, 242))
    return m


ISS = build_iss()


def iss_faces(c, pos, Rm, L, dim=1.0):
    return mm_faces(c, ISS, pos, Rm, L, dim)


def mm_faces(c, model, pos, Rm, L, dim=1.0, xr=0.0, xr_tags=(), near=0.05):
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


# =====================================================================
# Persona estilizada (cm) y laboratorio
# =====================================================================
def build_person():
    m = mm.Model()
    skin, shirt, pants = (214, 170, 140), (60, 120, 200), (40, 44, 60)
    for s in (-1, 1):
        m.beam((0, 0, 11 * s), (0, 48, 11 * s), 13, 13, pants)
        m.beam((0, 48, 11 * s), (0, 95, 10 * s), 15, 15, pants)
        m.box((-6, 0, 11 * s - 6), (16, 7, 11 * s + 6), (30, 30, 34))
        m.beam((0, 143, 24 * s), (2, 112, 28 * s), 10, 10, shirt)
        m.beam((2, 112, 28 * s), (4, 84, 27 * s), 9, 9, skin)
    m.box((-11, 92, -21), (11, 146, 21), shirt)
    m.box((-6, 146, -6), (6, 152, 6), skin)
    m.box((-11, 152, -10), (11, 178, 10), skin)
    m.box((-12, 170, -11), (12, 181, 11), (40, 30, 26))
    return m


PERSON = build_person()


def build_lab():
    m = mm.Model()
    m.box((-160, 80, -90), (160, 92, 90), (48, 50, 58))
    for x in (-140, 140):
        for z in (-70, 70):
            m.box((x - 6, 0, z - 6), (x + 6, 80, z + 6), (70, 72, 80))
    m.cyl((0, 132, 0), (0, 1, 0), 32, 80, (178, 182, 192), 20, 'chamber', True, (150, 154, 164))
    for y in (92, 172):
        m.cyl((0, y, 0), (0, 1, 0), 38, 6, (150, 154, 164), 20, 'chamber')
    for (x, z) in ((-110, -50), (-110, 50), (110, -50), (110, 50), (-60, 70), (60, -70)):
        m.cyl((x, 100, z), (0, 1, 0), 3, 16, (90, 92, 100), 8)
        m.cyl((x, 112, z), (1, 0, 1), 6, 2, (200, 210, 230), 14)
    m.box((-150, 92, 40), (-100, 120, 75), (40, 60, 120))
    return m


LAB = build_lab()


# =====================================================================
# Cámaras
# =====================================================================
KEYS = {
    'hook': [(0.0, 1250, 22, 4, 900, 0, 0, 0), (7.25, 1650, 26, 22, 920, 0, -30, 0)],
    'grid': [(7.25, 16000, 20, -20, 860, 0, -2600, 0), (12.65, 14000, 24, 12, 860, 0, -2600, 0)],
    'speed': [(12.65, 14, 8, 0, 980, 0, 0, 0), (17.6, 15, 8, 4, 980, 0, 0, 0), (17.9, 1400, 18, 30, 880, 0, 0, 0), (24.75, 1300, 22, 8, 900, 0, -30, 0)],
    'gravity': [(24.75, 16000, 18, -30, 880, 0, -2600, 0), (34.5, 13500, 24, 10, 880, 0, -2600, 0), (38.45, 13000, 24, 18, 880, 0, -2600, 0)],
    'iss': [(38.45, 160, 18, 30, 900, 0, 0, 0), (44.0, 140, 22, 54, 900, 0, 0, 0), (52.25, 175, 26, 80, 900, 0, 0, 0)],
    'home': [(52.25, 560, 6, -32, 1000, -560, 100, 200), (57.95, 500, 5, -20, 1000, -560, 100, 200)],
    'lab': [(57.95, 520, 18, 24, 1020, 0, 125, 0), (60.0, 300, 14, 34, 960, 0, 132, 0), (65.8, 280, 12, 46, 960, 0, 132, 0)],
}
LOGD = {'speed': True}


def cam_for(env, t):
    return cam_keys(t, KEYS[env], LOGD.get(env, False))


# =====================================================================
# Render
# =====================================================================
ISS_CTR = (0.0, -6.771e6, 0.0)
ISS_R = 6.371e6
SUN_ISS = norm((-0.5, 0.6, -0.55))


def light_clock(la, c, t, x0, moving, a, col):
    """reloj de luz: dos espejos y un fotón que rebota; si se mueve, el camino es diagonal"""
    hgt = 3.2
    v = 1.6 if moving else 0.0
    xs = x0 + v * ((t - 12.9) % 4.0) - (v * 2.0)
    period = 1.0 if not moving else 1.0 * math.sqrt(1 + (v / (2 * hgt)) ** 2) * 1.6
    for yy in (-hgt / 2, hgt / 2):
        line3(la, c, (xs - 0.9, yy, 0), (xs + 0.9, yy, 0), sc3((220, 230, 255), a), max(3, int(6 * S)), 0.05)
    ph = ((t - 12.9) / period) % 1.0
    y = -hgt / 2 + hgt * (1 - abs(1 - 2 * ph))
    trail = []
    for k in range(30):
        tk = t - k * 0.03
        phk = ((tk - 12.9) / period) % 1.0
        xk = x0 + v * ((tk - 12.9) % 4.0) - v * 2.0
        trail.append((xk, -hgt / 2 + hgt * (1 - abs(1 - 2 * phk)), 0))
    polyline3(la, c, trail, sc3(col, 0.5 * a), max(2, int(3 * S)), 0.05)
    x, yv, _ = proj(xs, y, 0, c)
    glow_dot(la, x * S, yv * S, 8 * S, (255, 255, 255), a)
    return xs, period


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
    base = None

    if env == 'hook' or (env == 'speed' and t >= 17.9):
        arr = np.full((H, W, 3), 6.0, np.float32)
        gps.sat_scene(arr, la, c, t, 0.0, spin=-96 + t * 0.3)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        gps.sat_draw(bd, od, la, c, t, 0.0)
        if env == 'speed':
            # estela de velocidad
            for k in range(28):
                y0 = (k * 97) % 1100 + 300
                x0 = ((k * 0.137 - t * 1.3) % 1.0) * W
                la.line([(x0, y0 * S), (x0 + 90 * S, y0 * S)], fill=sc3((150, 170, 230), 0.35), width=1)
    elif env in ('grid', 'gravity'):
        arr = np.full((H, W, 3), 6.0, np.float32)
        draw_stars(arr, c)
        yE = -1200 + well(0, 1.0) + RE_G * 0.85
        ge.render_earth(arr, c, (0, yE, 0), RE_G, -99 + t * 4, norm((-0.6, 0.4, -0.7)))
        depth = 1.0
        a = ease(seg(t, 7.6, 8.6)) if env == 'grid' else 1.0
        draw_grid(la, c, t, depth, a)
        orb = orbit_pts(RG_G, yE, 160, math.radians(8))
        polyline3(la, c, orb, sc3(BLUE, 0.55), max(1, int(2 * S)), 50.0)
        q = t * 0.5
        sp = (RG_G * math.cos(q), yE + RG_G * math.sin(q) * math.sin(math.radians(8)), RG_G * math.sin(q) * math.cos(math.radians(8)))
        x, y, dep = proj(*sp, c)
        gps.sat_icon(la, x * S, y * S, 2.4 * S, 1.0, CYAN)
        info['sat'] = sp
        info['earth'] = (0, yE + RE_G, 0)
        if env == 'grid':
            va = ease(seg(t, 10.4, 10.9))
            if va > 0:
                d = np.array([-math.sin(q), 0, math.cos(q)])
                p0 = np.array(sp)
                line3(la, c, tuple(p0), tuple(p0 + d * 1600), sc3(ORANGE, va), max(3, int(6 * S)), 50.0)
        else:
            # pozo: resalta el reloj de la superficie (más lento) y el del satélite (más rápido)
            for (p, col, rate) in ((info['earth'], RED, 0.6), (sp, GREEN, 1.0)):
                x, y, _ = proj(*p, c)
                pul = 0.5 + 0.5 * math.sin(2 * math.pi * rate * t)
                glow_dot(la, x * S, y * S, (10 + 8 * pul) * S, col, 0.8)
    elif env == 'speed':
        arr = np.full((H, W, 3), 6.0, np.float32)
        draw_stars(arr, c)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        a = ease(seg(t, 12.9, 13.5))
        info['lc0'] = light_clock(la, c, t, -3.2, False, a, CYAN)
        info['lc1'] = light_clock(la, c, t, 3.2, True, a, ORANGE)
    elif env == 'iss':
        arr = np.full((H, W, 3), 6.0, np.float32)
        draw_stars(arr, c)
        ge.render_earth(arr, c, ISS_CTR, ISS_R, -95 + (t - 38.45) * 2.2, SUN_ISS, atmo=1.1, tilt_deg=70.0, smooth=True)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        arr = None
        draw_list(bd, od, iss_faces(c, (0, 0, 0), mm.rot(math.radians(15)), SUN_ISS))
        for x in (-50, -38, 38, 50):
            for s in (-1, 1):
                for k in range(1, 6):
                    zz = s * (3 + 33 * k / 6)
                    line3(bd, c, (x - 5.5, 0.12, zz), (x + 5.5, 0.12, zz), (120, 80, 40), max(1, int(1.5 * S)), 0.5)
        for k in range(28):
            y0 = (k * 97) % 1100 + 300
            x0 = ((k * 0.137 - t * 1.8) % 1.0) * W
            la.line([(x0, y0 * S), (x0 + 110 * S, y0 * S)], fill=sc3((150, 170, 230), 0.3), width=1)
    elif env == 'home':
        base = Image.new("RGB", (W, H), (20, 20, 26))
        bd = ImageDraw.Draw(base)
        fo.draw_home(bd, c, 60.0, 1.0)
        L = norm((-0.3, 0.8, -0.5))
        draw_list(bd, od, mm_faces(c, PERSON, (-560, 0, 200), mm.rot(math.radians(-90)), L, 1.0, near=5.0))
        la.polygon([P2(*p, c) for p in fo.qz(-138, 488, 242, 588, 729.4)], fill=sc3((20, 24, 50), 1.0))
        info['head'] = (-560, 172, 200)
        info['feet'] = (-560, 4, 200)
    else:
        base = Image.new("RGB", (W, H), (16, 17, 24))
        bd = ImageDraw.Draw(base)
        poly(bd, c, [(-1500, 0, -1500), (1500, 0, -1500), (1500, 0, 800), (-1500, 0, 800)], (44, 46, 54), 1.0)
        poly(bd, c, [(-1500, 0, 800), (1500, 0, 800), (1500, 600, 800), (-1500, 600, 800)], (30, 32, 42), 1.0)
        xr = ease(seg(t, 59.0, 59.8))
        L = norm((-0.3, 0.85, -0.4))
        draw_list(bd, od, mm_faces(c, LAB, (0, 0, 0), np.eye(3), L, 1.0, xr, ('chamber',), near=5.0))
        # láseres de la mesa
        beams = [((-110, 112, -50), (-110, 112, 50)), ((-110, 112, 50), (110, 112, 50)), ((110, 112, 50), (110, 112, -50)),
                 ((110, 112, -50), (-110, 112, -50)), ((-60, 112, 70), (0, 132, 0)), ((60, 112, -70), (0, 132, 0))]
        for (p0, p1) in beams:
            line3(la, c, p0, p1, sc3((255, 60, 60), 0.8), max(2, int(3 * S)), 5.0)
        if xr > 0.01:
            # red de luz (redes ópticas) y átomos de estroncio
            for k in range(11):
                y = 124 + k * 1.6
                line3(la, c, (-26, y, 0), (26, y, 0), sc3(VIOLET, 0.6 * xr), max(1, int(2 * S)), 5.0)
            rs = np.random.RandomState(4)
            for k in range(120):
                x = rs.normal(0, 7)
                lvl = rs.randint(0, 11)
                y = 124 + lvl * 1.6 + 0.2 * math.sin(t * 6 + k)
                z = rs.normal(0, 7)
                col = lc((255, 120, 120), (120, 200, 255), lvl / 10)
                xx, yy_, dep = proj(x, y, z, c)
                if dep > 5:
                    glow_dot(la, xx * S, yy_ * S, 3.2 * S, col, xr * (0.7 + 0.3 * math.sin(t * 9 + k)))
            for yy in (92, 172):
                pts = ring_pts((0, yy, 0), (0, 1, 0), 33, 40)
                polyline3(la, c, pts, sc3(BLUE, 0.6 * xr), max(1, int(2 * S)), 5.0)
            ys = 92 + ((t * 0.5) % 1.0) * 80
            pts = ring_pts((0, ys, 0), (0, 1, 0), 36, 40)
            polyline3(la, c, pts, sc3(CYAN, 0.9 * xr), max(2, int(3 * S)), 5.0)

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


# =====================================================================
# HUD
# =====================================================================
DARK = []


def fmt_clock(sec, extra_us=0.0):
    s = sec + extra_us * 1e-6
    hh = int(s // 3600) % 24
    mm_ = int(s // 60) % 60
    ss = s % 60
    return f"{hh:02d}:{mm_:02d}:{ss:09.6f}"


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
    if env == 'hook':
        a = win(0.6, 7.2)
        if a > 0:
            DARK.append((60, 1430, 1020, 1720, a))
            el = max(0.0, t - 0.6) * 13300.0
            base_s = 12 * 3600 + el
            drift = 38.0 * el / 86400.0
            l2.text(P(110, 1490), "TU RELOJ", font=F(B, 32), fill=sc3((220, 220, 240), a), anchor="lm")
            l2.text(P(110, 1550), fmt_clock(base_s), font=F(M, 50), fill=sc3((230, 230, 245), a), anchor="lm")
            l2.text(P(110, 1620), "SATÉLITE", font=F(B, 32), fill=sc3(CYAN, a), anchor="lm")
            l2.text(P(110, 1680), fmt_clock(base_s, drift), font=F(M, 50), fill=sc3(CYAN, a), anchor="lm")
        pill("RELATIVIDAD", 560, win(4.7, 7.2), VIOLET, 520, 44)
        if a > 0:
            l2.text(P(1000, 1490), "TIEMPO ACELERADO", font=F(B, 22), fill=sc3((160, 160, 190), a * 0.8), anchor="rm")
    if env == 'grid':
        a = win(8.0, 12.6)
        if a > 0:
            label("EINSTEIN, 1905 Y 1915", P3(info['earth']), (540, 1560), "lm" if False else "rm", 0)
        a = a * ease(seg(t, 10.2, 10.6))
        if a > 0:
            DARK.append((140, 1500, 940, 1640, a))
            l2.text(P(320, 1570), "VELOCIDAD", font=F(B, 46), fill=sc3(ORANGE, a * ease(seg(t, 10.3, 10.7))), anchor="mm")
            l2.text(P(760, 1570), "GRAVEDAD", font=F(B, 46), fill=sc3(VIOLET, a * ease(seg(t, 11.3, 11.7))), anchor="mm")
            l2.text(P(540, 1570), "+", font=F(B, 46), fill=sc3((220, 220, 240), a * ease(seg(t, 11.0, 11.4))), anchor="mm")
        a = win(7.8, 12.6)
        if a > 0:
            l2.text(P(1040, 1860), "ILUSTRACIÓN DEL ESPACIO-TIEMPO", font=F(B, 22), fill=sc3((160, 160, 190), a * 0.8), anchor="rm")
    if env == 'speed':
        if t < 17.9:
            a = win(13.3, 17.6)
            if a > 0:
                lc0, lc1 = info['lc0'], info['lc1']
                p0, p1 = P3((-3.2, -2.6, 0)), P3((lc1[0], -2.6, 0))
                n0 = int((t - 12.9) / lc0[1] * 2)
                n1 = int((t - 12.9) / lc1[1] * 2)
                DARK.append((80, 1420, 1000, 1640, a))
                l2.text(P(300, 1470), "QUIETO", font=F(B, 34), fill=sc3(CYAN, a), anchor="mm")
                l2.text(P(780, 1470), "EN MOVIMIENTO", font=F(B, 34), fill=sc3(ORANGE, a), anchor="mm")
                l2.text(P(300, 1560), f"{n0} tics", font=F(M, 56), fill=sc3((240, 240, 255), a), anchor="mm")
                l2.text(P(780, 1560), f"{n1} tics", font=F(M, 56), fill=sc3((240, 240, 255), a), anchor="mm")
                l2.text(P(1040, 1860), "RELOJ DE LUZ · EFECTO EXAGERADO", font=F(B, 22), fill=sc3((160, 160, 190), a * 0.8), anchor="rm")
        else:
            pill("≈14,000 km/h", 1560, win(18.4, 24.7), ORANGE, 520, 40)
            a = win(21.4, 24.7)
            if a > 0:
                DARK.append((260, 1640, 820, 1760, a))
                l2.text(P(540, 1700), "−7 µs POR DÍA", font=F(M, 56), fill=sc3(RED, a), anchor="mm")
    if env == 'gravity':
        a = win(25.4, 38.4)
        if a > 0:
            label("EN LA TIERRA: MÁS LENTO", P3(info['earth']), (60, 1480), "lm", win(25.6, 29.2) * a, (255, 190, 190))
            label("ALLÁ ARRIBA: MÁS RÁPIDO", P3(info['sat']), (1020, 520), "rm", win(29.6, 34.4) * a, (190, 255, 210))
        a = win(31.6, 34.6)
        if a > 0:
            DARK.append((260, 1640, 820, 1760, a))
            l2.text(P(540, 1700), "+45 µs POR DÍA", font=F(M, 56), fill=sc3(GREEN, a), anchor="mm")
        a = win(34.9, 38.4)
        if a > 0:
            DARK.append((120, 1420, 960, 1780, a))
            l2.text(P(540, 1480), "−7  +  45", font=F(M, 64), fill=sc3((230, 230, 245), a), anchor="mm")
            l2.text(P(540, 1580), "= +38 µs / DÍA", font=F(M, 68), fill=sc3(GREEN, a * ease(seg(t, 35.4, 35.8))), anchor="mm")
            l2.text(P(540, 1700), "GANA LA GRAVEDAD", font=F(B, 44), fill=sc3(VIOLET, a * ease(seg(t, 35.9, 36.3))), anchor="mm")
    if env == 'iss':
        pill("ESTACIÓN ESPACIAL · ≈27,500 km/h", 1560, win(39.2, 44.0), ORANGE, 880, 32)
        pill("GANA LA VELOCIDAD", 1680, win(42.2, 44.2), RED, 600, 36)
        a = win(44.6, 52.2)
        if a > 0:
            DARK.append((90, 1380, 990, 1800, a))
            l2.text(P(540, 1440), "SCOTT KELLY · +500 DÍAS EN ÓRBITA", font=F(B, 34), fill=sc3((230, 230, 245), a), anchor="mm")
            clock_icon(l2, 300, 1600, 90, a, 1.0, t, CYAN, "SCOTT", None)
            clock_icon(l2, 780, 1600, 90, a, 1.0003, t, (255, 200, 140), "MARK (GEMELO)", None)
            l2.text(P(540, 1760), "5 MILÉSIMAS DE SEGUNDO DE DIFERENCIA", font=F(B, 28), fill=sc3(GOLD, a * ease(seg(t, 48.6, 49.0))), anchor="mm")
    if env == 'home':
        a = win(53.0, 57.9)
        if a > 0:
            label("CABEZA: UN POCO MÁS RÁPIDO", P3(info['head']), (1020, 560), "rm", a, (190, 255, 210))
            label("PIES: UN POCO MÁS LENTO", P3(info['feet']), (60, 1520), "lm", ease(seg(t, 54.0, 54.4)) * a, (255, 190, 190))
        pill("DIFERENCIA DIMINUTA", 1640, win(55.4, 57.9), VIOLET, 600, 34)
    if env == 'lab':
        a = win(59.3, 62.4)
        if a > 0:
            label("ÁTOMOS DE ESTRONCIO", P3((10, 132, 0)), (1020, 600), "rm", a, (190, 230, 255))
            label("RED DE LÁSERES", P3((-24, 128, 0)), (60, 1460), "lm", ease(seg(t, 59.9, 60.3)) * a, (220, 200, 255))
        pill("1 mm DE ALTURA: YA SE NOTA", 1640, win(60.6, 62.4), CYAN, 760, 34)
        a = win(59.6, 62.4)
        if a > 0:
            l2.text(P(1040, 1860), "JILA · 2022", font=F(B, 22), fill=sc3((160, 160, 190), a * 0.8), anchor="rm")
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
        os.makedirs("/home/claude/tie_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/tie_prev/t_{ts}.png")
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
