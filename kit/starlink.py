"""Video largo de YouTube: Starlink por dentro (28-oct-2026) y sus 2 Shorts. Tema visual: orbita.
Uso: MOTOR_TEMA=orbita GTA_FMT=h|v VIDEO_TL=/home/claude/tl_starlink_MODO.json python3 starlink.py info|preview T out.png|sheet out.jpg t..|chunk A B out.mp4"""
import os
os.environ.setdefault('MOTOR_TEMA', 'orbita')
import math
import numpy as np
from PIL import Image, ImageDraw
import escenas as S
from escenas import *  # noqa: F401,F403
from motor3d import tex, torus, merge

# ------------------------------------------------------------------ colores (objetos reales; neón solo en efectos)
CYAN = (70, 175, 255)
ICE = (170, 230, 255)
LASER = (255, 70, 110)
LGREEN = (90, 255, 150)
AMBER = (255, 176, 60)
PINK = (240, 88, 138)
OCEAN = (28, 74, 150)
LAND = (64, 132, 78)
DESERT = (176, 150, 100)
ICEC = (230, 236, 242)
PANEL = (34, 52, 104)
METAL = (196, 198, 206)
WHITE = (236, 236, 240)
DARK = (34, 36, 42)
TERRA = (214, 128, 92)     # casa mexicana
CREAM = (232, 214, 176)
BLACK = (24, 24, 28)


def lab(fr, txt, a=1.0, where='br', dotc=CYAN):
    ui_pill(fr, txt, a, where=where, dotc=dotc)


# ------------------------------------------------------------------ Tierra
LANDS = [(45, -100, 20, 30), (22, -102, 9, 12), (15, -89, 5, 6), (60, -125, 10, 18), (-15, -60, 22, 14),
         (-40, -67, 12, 6), (52, 15, 12, 20), (5, 20, 28, 18), (24, 45, 8, 8), (50, 90, 20, 45), (20, 78, 8, 7),
         (10, 105, 8, 8), (-25, 134, 10, 16), (72, -40, 8, 15), (64, 100, 10, 50), (36, 138, 6, 4)]
DESERTS = [(24, 10, 9, 20), (24, 45, 6, 7), (-25, 128, 6, 9), (29, -106, 5, 5)]


def _inside(lat, lon, L):
    for a, b, ra, rb in L:
        dl = (lon - b + 180) % 360 - 180
        if ((lat - a) / ra) ** 2 + (dl / rb) ** 2 < 1:
            return True
    return False


def earth_col(lat, lon):
    if lat < -72 or lat > 88:
        return ICEC
    if _inside(lat, lon, LANDS):
        if _inside(lat, lon, DESERTS):
            return DESERT
        return LAND
    return OCEAN


_EARTH = {}


def earth(r, lon0=-100.0, lat_tilt=20.0, nu=44, nv=24, spin=0.0):
    """Tierra con continentes aproximados; lon0 queda de frente a la cámara (+z). Recreación."""
    key = (nu, nv)
    if key not in _EARTH:
        def cols(i, j):
            lat = 90 - (j + 0.5) * 180 / nv
            u = (i + 0.5) * 360 / nu
            lon = -(u - 90)
            return earth_col(lat, lon)
        _EARTH[key] = sphere(1.0, OCEAN, nu=nu, nv=nv, shadow=0, gloss=0.35, cols=cols)
    m = _EARTH[key].copy()
    m.V = m.V @ rotm(0, -(lon0) - spin, 0).T  # gira para que lon0 quede al frente
    m.V = m.V @ rotm(lat_tilt, 0, 0).T
    m.V = m.V * r
    m.sh_r = r
    return m


def atmo(d, cam, c, r, a=1.0):
    """Halo de atmósfera (efecto)."""
    s, z = cam.proj([c])
    if z[0] < 0.2:
        return
    x, y = s[0]
    rr = cam.F * r / z[0]
    for k, (dr, w, al) in enumerate(((1.0, 6, 0.55), (1.025, 4, 0.3), (1.05, 3, 0.15))):
        R = rr * dr
        col = mix(tuple(int(v) for v in E.BG), CYAN, al * a)
        d.ellipse((x - R, y - R, x + R, y + R), outline=col, width=int(w * SS))


def hidden(p, c, campos, r):
    """¿El punto p queda detrás de la esfera (c, r) vista desde campos?"""
    p, c, campos = np.asarray(p), np.asarray(c), np.asarray(campos)
    d = p - campos
    L = np.linalg.norm(d)
    d = d / L
    tc = np.dot(c - campos, d)
    if tc < 0 or tc > L:
        return False
    return np.linalg.norm(campos + d * tc - c) < r


def shell_points(n, R, c=(0, 0, 0), t=0.0, seed=3, speed=0.05, planes=18):
    """n satélites repartidos en planos orbitales inclinados (posiciones en el tiempo t)."""
    rng = np.random.RandomState(seed)
    pts = []
    per = max(1, n // planes)
    for k in range(planes):
        inc = math.radians(53 + rng.uniform(-3, 3)) if k % 5 else math.radians(rng.uniform(70, 97))
        raan = 2 * math.pi * k / planes + rng.uniform(0, 0.2)
        for j in range(per):
            u = 2 * math.pi * j / per + t * speed * (1 + 0.1 * (k % 3)) + k * 0.37
            x, y, z = math.cos(u), 0.0, math.sin(u)
            y, z = z * math.sin(inc), z * math.cos(inc)
            x, z = x * math.cos(raan) - z * math.sin(raan), x * math.sin(raan) + z * math.cos(raan)
            pts.append((c[0] + R * x, c[1] + R * y, c[2] + R * z))
    return pts


def draw_shell(fr, pts, c, r, col=ICE, rad=2.2, a=1.0):
    def f(d, cam):
        for p in pts:
            if not hidden(p, c, cam.pos, r):
                dot3(d, cam, p, rad, col, a)
    fr.over.append(f)


# ------------------------------------------------------------------ objetos 3D
def satellite(s=1.0, panel_open=1.0):
    """Satélite tipo Starlink (recreación): cuerpo plano y dos alas solares."""
    ms = [box(0.62 * s, 0.1 * s, 0.36 * s, METAL, shadow=0.3, base=False, gloss=0.4)]
    w = 1.25 * s * max(0.05, panel_open)
    for sg in (-1, 1):
        p = box(w, 0.02 * s, 0.42 * s, PANEL, cols={'top': (44, 70, 140)}, shadow=0.3, base=False, gloss=0.5)
        ms.append(p.tf(t=(sg * (0.31 * s + w / 2 + 0.04 * s), 0, 0)))
        ms.append(box(0.08 * s, 0.03 * s, 0.05 * s, (120, 120, 128), base=False, shadow=0).tf(t=(sg * 0.34 * s, 0, 0)))
    return ms


def sat_at(p, s=1.0, ry=0.0, rx=0.0, rz=0.0, panel_open=1.0, alpha=1.0):
    out = []
    for m in satellite(s, panel_open):
        mm = m.tf(rx=rx, ry=ry, rz=rz, t=p)
        mm.alpha = alpha
        out.append(mm)
    return out


def dish(x=0.0, y=0.0, z=0.0, ry=0.0, tilt=-25.0, s=1.0):
    """Antena plana tipo Starlink (rectangular blanca sobre un mástil)."""
    mast = cyl(0.035 * s, 0.45 * s, (210, 210, 214), n=12, shadow=0.3).tf(t=(0, 0, 0))
    panel = rbox(0.62 * s, 0.05 * s, 0.9 * s, 0.06 * s, WHITE, gloss=0.4, shadow=0.35, base=False)
    panel = panel.tf(rx=tilt, t=(0, 0.5 * s, 0))
    return [m.tf(ry=ry, t=(x, y, z)) for m in (mast, panel)]


def dish_normal(ry=0.0, tilt=-25.0):
    n = np.array([0, 1.0, 0]) @ rotm(tilt, 0, 0).T @ rotm(0, ry, 0).T
    return n


def house(x=0.0, z=0.0, ry=0.0, s=1.0, col=TERRA, roofdish=True, tinaco=True):
    """Casa mexicana de azotea con tinaco y antena en el techo."""
    ms = [box(1.6 * s, 1.0 * s, 1.2 * s, col, cols={'top': (196, 190, 180)}, shadow=0.4)]
    ms.append(box(1.66 * s, 0.1 * s, 1.26 * s, (240, 236, 228), shadow=0).tf(t=(0, 1.0 * s, 0)))
    door = box(0.3 * s, 0.55 * s, 0.03, (110, 70, 40), shadow=0).tf(t=(-0.4 * s, 0, 0.61 * s))
    win1 = box(0.36 * s, 0.3 * s, 0.03, (60, 90, 130), shadow=0).tf(t=(0.3 * s, 0.45 * s, 0.61 * s))
    ms += [door, win1]
    if tinaco:
        ms.append(cyl(0.18 * s, 0.38 * s, (20, 20, 22), n=18, r2=0.15 * s, shadow=0.3, gloss=0.5).tf(t=(0.45 * s, 1.1 * s, -0.3 * s)))
    if roofdish:
        ms += dish(-0.3 * s, 1.1 * s, 0.0, ry=0, tilt=-22, s=0.7 * s)
    return [m.tf(ry=ry, t=(x, 0, z)) for m in ms]


def radome(x=0.0, z=0.0, r=0.35):
    return [cyl(r * 0.9, 0.25, (190, 190, 196), n=20, shadow=0.35).tf(t=(x, 0, z)),
            sphere(r, (244, 244, 246), nu=20, nv=10, shadow=0.35, gloss=0.5).tf(t=(x, 0.25 + r * 0.55, z))]


def ground_station(x=0.0, z=0.0, s=1.0):
    ms = [box(1.2 * s, 0.5 * s, 0.8 * s, (150, 154, 162), shadow=0.35).tf(t=(x, 0, z - 0.9 * s))]
    for i in range(3):
        ms += radome(x - 0.9 * s + i * 0.9 * s, z + 0.2 * s, 0.32 * s)
    return ms


def rack(x=0.0, z=0.0, lit=0.0, n=6):
    ms = [box(0.7, 1.6, 0.6, (30, 32, 38), shadow=0.4).tf(t=(x, 0, z))]
    for i in range(n):
        c = mix((60, 60, 70), LGREEN if (i + int(lit * 7)) % 3 else CYAN, 0.8)
        ms.append(box(0.6, 0.04, 0.02, c, shadow=0, edge=False).tf(t=(x, 0.2 + i * 0.22, z + 0.31)))
    return ms


def phone_m(x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0, s=1.0, scr=None):
    body = rbox(0.5 * s, 0.05 * s, 1.0 * s, 0.07 * s, (26, 26, 30), gloss=0.6, shadow=0.35, base=False)
    sc = box(0.44 * s, 0.005, 0.92 * s, (14, 14, 16), edge=False, shadow=0, base=False).tf(t=(0, 0.03 * s, 0))
    if scr is not None:
        decal(sc, sc.FACE['top'], scr)
    return [m.tf(rx=rx, ry=ry, rz=rz, t=(x, y, z)) for m in (body, sc)]


_SCR = {}


def screen_video():
    if 'v' not in _SCR:
        def f(d, im):
            w, h = im.size
            for yy in range(h):
                c = mix((20, 40, 90), (8, 12, 30), yy / h)
                d.line([(0, yy), (w, yy)], fill=c)
            for i in range(40):
                d.ellipse((7 * i % w, 13 * i % (h // 2), 7 * i % w + 2, 13 * i % (h // 2) + 2), fill=(200, 220, 255))
            d.ellipse((w * 0.2, h * 0.6, w * 0.8, h * 1.2), fill=(40, 110, 200))
            d.polygon([(w * 0.42, h * 0.40), (w * 0.42, h * 0.52), (w * 0.56, h * 0.46)], fill=(255, 255, 255))
            d.rectangle((w * 0.1, h * 0.9, w * 0.9, h * 0.91), fill=(255, 255, 255))
            d.rectangle((w * 0.1, h * 0.9, w * 0.45, h * 0.91), fill=(255, 60, 60))
        _SCR['v'] = tex(160, 320, (0, 0, 0, 255), f)
    return _SCR['v']


def text_tex(txt, w=320, h=120, bg=(255, 255, 255), fg=(20, 20, 24), size=60, fk='xb', sub=None):
    key = ('t', txt, w, h, bg, fg, size, fk, sub)
    if key not in _SCR:
        def f(d, im):
            if sub:
                d.text((w / 2, h * 0.40), txt, font=font(fk, size), fill=fg, anchor='mm')
                d.text((w / 2, h * 0.80), sub, font=font('sb', int(size * 0.38)), fill=fg, anchor='mm')
            else:
                d.text((w / 2, h / 2), txt, font=font(fk, size), fill=fg, anchor='mm')
        _SCR[key] = tex(w, h, bg + (255,), f)
    return _SCR[key]


def tag3(txt, sub, w=1.6, h=0.7, col=WHITE, fg=(20, 20, 24)):
    m = box(w, h, 0.06, col, shadow=0.35, base=False)
    decal(m, m.FACE['front'], text_tex(txt, 420, int(420 * h / w), col, fg, size=int(150 * h / w * 1.6) if not sub else 92, sub=sub))
    return m


def beam(fr, a, b, col=CYAN, w=3.0, k=1.0, alpha=1.0, dash=None, pulse=None, layer='over'):
    """Haz de señal de a a b (k = fracción dibujada); pulse = posición 0..1 de un destello."""
    a, b = np.array(a, float), np.array(b, float)

    def f(d, cam):
        if k <= 0:
            return
        p = a + (b - a) * clamp(k)
        line3(d, cam, [a, p], col, w, dash, alpha)
        if pulse is not None and 0 <= pulse <= 1:
            q = a + (b - a) * pulse
            dot3(d, cam, q, 7, (255, 255, 255), alpha)
            dot3(d, cam, q, 12, col, alpha * 0.5)
    (fr.over if layer == 'over' else fr.under).append(f)


def scan_ring(fr, t, ts, te, y0, y1, center=(0, 0, 0), r=1.4):
    """Anillo escáner de rayos X (sello de la marca)."""
    k = clamp((t - ts) / max(0.1, te - ts))
    ys = lerp(y0, y1, ease(k))
    a = win(t, ts, te + 0.6, 0.2, 0.4)

    def over(d, cam, ys=ys, a=a):
        for j, (rr, w) in enumerate(((r, 3.4), (r * 1.06, 1.6), (r * 0.94, 1.2))):
            ring3(d, cam, (center[0], ys, center[2]), rr, CYAN, w, a * (1 - j * 0.3))
    fr.over.append(over)
    return ys, k


def bigc(fr, txt, sub, a=1.0, y=None, size=None):
    big_counter(fr, txt, a=a, sub=sub, pos=(W * 0.5, H * (y if y else (0.30 if not VERT else 0.30))),
                size=size or (84 if not VERT else 96), col=INK)


def cnt(v, t, t0, d=1.6):
    return v * eout((t - t0) / d) if t0 is not None else v


# ================================================================== GANCHO (c0)
EC = (0, -6.2, 0)   # centro de la Tierra en tomas de horizonte
ER = 6.0


def s_hook(fr, t, lt, dur, loop=False):
    """Horizonte de la Tierra (México al frente) con miles de satélites cruzando y contador."""
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.4, 0), dist=vfit(9.5, wide=True) - lt * 0.25, yaw=-6 + lt * 1.5, pitch=12, cy=0.62 if not VERT else 0.52)
    fr.meshes.append(earth(ER, lon0=-100, lat_tilt=55, spin=lt * 0.6).tf(t=EC))
    fr.under.append(lambda d, cam: atmo(d, cam, EC, ER * 1.01))
    n = int(lerp(60, 520, ease(lt / 2.5)))
    pts = shell_points(n, ER + 0.55, EC, t, seed=5, speed=0.12, planes=26)
    draw_shell(fr, pts, EC, ER, ICE, 2.0)
    # un satélite de cerca, cruzando
    p = (-3.2 + lt * 0.9, 1.6, 0.8)
    fr.meshes += sat_at(p, s=0.55, ry=20, rz=-8)
    v = 11150 * eout((lt - 0.2) / 2.2)
    bigc(fr, fmt_int(max(0, v)), 'SATÉLITES STARLINK EN ÓRBITA', y=0.24 if not VERT else 0.30)
    lab(fr, 'Recreación · cifra: oct 2026', clamp(lt / 0.5))


def s_phone(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.3, 0), dist=vfit(6.2), yaw=-18 + lt * 4, pitch=8 + lt * 2)
    fr.meshes += phone_m(0, 0.9, 0.6, rx=70, s=1.3, scr=screen_video())
    sp = (1.6, 3.4, -2.0)
    fr.meshes += sat_at(sp, s=0.5, ry=-30, rz=10)
    k = (lt - 0.3) / 1.0
    pu = (lt * 0.8) % 1.0
    beam(fr, sp, (0, 1.3, 0.55), CYAN, 3.0, k=k, pulse=pu if k > 1 else None, dash=None)
    head(fr, ['Uno te manda', 'este video.'], CYAN, t, t0 + 0.1, kicker='Tal vez ahora mismo')
    lab(fr, 'Recreación', clamp(lt / 0.5))


def s_speed(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(5.0), yaw=-30 + lt * 6, pitch=-6)
    fr.meshes.append(earth(ER, lon0=-90, lat_tilt=40, spin=lt * 3).tf(t=(0, -7.0, -1.5)))
    fr.meshes += sat_at((0, 0.8, 0), s=1.0, ry=lt * 4, rz=-5)

    def streaks(d, cam, lt=lt):
        rng = np.random.RandomState(1)
        for i in range(26):
            y = rng.uniform(-0.4, 2.2); z = rng.uniform(-2.5, 1.2)
            x = ((rng.uniform(-6, 6) - lt * 9) % 12) - 6
            line3(d, cam, [(x, y, z), (x + 1.4, y, z)], ICE, 1.4, 0.5)
    fr.under.append(streaks)
    v = 27000 * eout((lt - 0.1) / 1.4)
    bigc(fr, fmt_int(v) + ' km/h', 'VELOCIDAD EN ÓRBITA', y=0.20 if not VERT else 0.26)
    lab(fr, 'Recreación', 1)


def s_lap(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(8.0), yaw=-10 + lt * 3, pitch=22, cy=0.62 if not VERT else 0.55)
    fr.meshes.append(earth(1.45, lon0=-100, lat_tilt=20, spin=lt * 8))
    fr.under.append(lambda d, cam: atmo(d, cam, (0, 0, 0), 1.47))
    inc = math.radians(53)
    k = clamp((lt - 0.2) / 2.2)
    u0 = -0.6

    def orb(u):
        x, z = 2.1 * math.cos(u), 2.1 * math.sin(u)
        return (x, z * math.sin(inc) * 0.5, z * math.cos(inc))
    ang = u0 + 2 * math.pi * ease(k)

    def path(d, cam, ang=ang):
        P = [orb(u0 + (ang - u0) * i / 80) for i in range(81)]
        P2 = [orb(u0 + 2 * math.pi * i / 120) for i in range(121)]
        line3(d, cam, [p for p in P2], CYAN, 1.2, dash=6, a=0.4)
        line3(d, cam, P, CYAN, 3.0)
    fr.over.append(path)
    fr.meshes += sat_at(orb(ang), s=0.32, ry=-math.degrees(ang))
    mins = 95 * ease(k)
    bigc(fr, f'{int(mins)} min', 'UNA VUELTA A LA TIERRA', y=0.18 if not VERT else 0.24)
    lab(fr, 'Órbita a escala exagerada', 1)


def s_blink(fr, t, lt, dur):
    """Ojo que parpadea vs. viaje de ida y vuelta de la señal."""
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.2, 0), dist=vfit(7.0, wide=True), yaw=-4 + lt * 2, pitch=10)
    fr.meshes += house(-2.2, 0.3, ry=12, s=0.8)
    fr.meshes += ground_station(2.4, 0.0, s=0.7)
    sp = (0.0, 3.3, -1.0)
    fr.meshes += sat_at(sp, s=0.45, ry=10)
    tk = T(('c0', 4, 'sube'), default=t0 + 0.6)
    tb = T(('c0', 4, 'baja'), default=t0 + 1.4)
    tl_ = T(('c0', 4, 'llega'), default=t0 + 2.2)
    up = clamp((t - tk) / 0.5)
    dn = clamp((t - tb) / 0.5)
    beam(fr, (-2.45, 1.25, 0.3), sp, CYAN, 3.0, k=up)
    beam(fr, sp, (2.4, 0.6, 0.2), CYAN, 3.0, k=dn)
    if t > tl_:
        def flash(d, cam, a=1 - clamp((t - tl_) / 0.8)):
            ring3(d, cam, (2.4, 0.05, 0.2), 0.6 + (1 - a) * 1.2, LGREEN, 3, a)
        fr.over.append(flash)
    # ojo (UI): párpado que se cierra
    def eye(img, d, lt=lt):
        cx, cy = (W * 0.22, H * 0.22) if not VERT else (W * 0.5, H * 0.22)
        rw, rh = (110, 52) if not VERT else (150, 70)
        k = abs(math.sin(clamp((t - tl_) / 0.5) * math.pi)) if t > tl_ else 0
        hh = rh * (1 - k)
        d.ellipse((cx - rw, cy - max(2, hh), cx + rw, cy + max(2, hh)), outline=INK, width=4)
        if hh > 14:
            d.ellipse((cx - hh * 0.6, cy - hh * 0.6, cx + hh * 0.6, cy + hh * 0.6), fill=CYAN)
            d.ellipse((cx - hh * 0.25, cy - hh * 0.25, cx + hh * 0.25, cy + hh * 0.25), fill=(10, 14, 30))
    fr.ui.append(eye)
    lab(fr, 'Menos que un parpadeo · Recreación', 1)


def s_five(fr, t, lt, dur):
    """Las 5 partes: 5 objetos numerados aparecen en fila."""
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(6.6, wide=True), yaw=-6 + lt * 2, pitch=14)
    xs = [-2.8, -1.4, 0.0, 1.4, 2.8]
    tp = T(('c0', 5, 'Hoy'), default=t0 + 2.5)
    for i, x in enumerate(xs):
        kk = eback((t - (t0 + 0.3 + i * 0.35)) / 0.5)
        if kk <= 0.01:
            continue
        s = max(0.05, kk)
        if i == 0:
            fr.meshes += house(x, 0, s=0.5 * s, tinaco=False)
            def ar(d, cam, x=x, s=s):
                line3(d, cam, [(x - 0.15, 0.85 * s, 0), (x + 0.3, 1.9 * s, -0.2)], CYAN, 3)
                dot3(d, cam, (x + 0.3, 1.9 * s, -0.2), 6, CYAN)
            fr.over.append(ar)
        elif i == 1:
            fr.meshes += dish(x, 0, 0, ry=-10, s=1.1 * s)
        elif i == 2:
            fr.meshes += sat_at((x, 0.8, 0), s=0.45 * s, ry=20)
            def lz(d, cam, x=x, s=s):
                line3(d, cam, [(x + 0.4, 0.8, 0), (x + 1.0 * s, 0.8, 0)], LASER, 3)
            fr.over.append(lz)
        elif i == 3:
            fr.meshes += sat_at((x - 0.2, 0.6, 0.2), s=0.3 * s, ry=40)
            fr.meshes += sat_at((x + 0.25, 1.0, -0.2), s=0.3 * s, ry=-30)
            def dg(d, cam, x=x):
                line3(d, cam, [(x - 0.6, 0.6, 0.2), (x + 0.5, 1.2, -0.3)], AMBER, 1.6, dash=5)
            fr.over.append(dg)
        else:
            fr.meshes.append(cyl(0.38 * s, 0.1, (212, 170, 60), n=24, top=(232, 196, 90), gloss=0.7).tf(t=(x, 0, 0)))
            fr.meshes.append(cyl(0.38 * s, 0.1, (212, 170, 60), n=24, top=(232, 196, 90), gloss=0.7).tf(t=(x + 0.05, 0.1, 0.03)))
        ui_text3(fr, (x, -0.1, 0.9), str(i + 1), 34, a=clamp(kk), fk='mono', col=CYAN)
    if t < tp:
        head(fr, ['¿Cómo le hace?'], CYAN, t, t0 + 0.1, kicker='Internet desde el espacio')
    else:
        head(fr, ['Por dentro,', 'en 5 partes.'], CYAN, t, tp, kicker='Hoy')


# ================================================================== PARTE 1 (c1): el viaje de tu señal
def s_house(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(6.0, wide=True) - lt * 0.2, yaw=-28 + lt * 5, pitch=14)
    fr.meshes += house(0, 0, ry=0, s=1.2)
    fr.meshes += house(-2.4, -1.2, ry=8, s=0.9, col=(150, 180, 210), roofdish=False)
    fr.meshes += house(2.4, -1.4, ry=-6, s=0.95, col=(232, 196, 110), roofdish=False)
    ui_label3(fr, (-0.36, 1.85, 0.05), 'Antena Starlink', 'en la azotea', a=clamp((lt - 0.5) / 0.5), side=-1, length=110)
    ui_label3(fr, (0.54, 1.75, -0.36), 'Tinaco', None, a=clamp((lt - 1.0) / 0.5), side=1, length=80)
    head(fr, ['Tu señal viaja', 'más lejos.'], CYAN, t, t0 + 0.1, kicker='Parte 1')


def s_up(fr, t, lt, dur):
    t0 = t - lt
    k = ease(clamp((lt - 0.2) / 3.0))
    fr.cam = Cam(target=(0, 1.0 + k * 4.0, 0), dist=vfit(6.5) + k * 5, yaw=-20 + lt * 3, pitch=10 + k * 4)
    fr.meshes += house(0, 0, s=1.0)
    sp = (0.2, 7.5, -1.0)
    fr.meshes += sat_at(sp, s=0.8, ry=15)
    beam(fr, (-0.3, 1.6, 0.0), sp, CYAN, 3.2, k=clamp((lt - 0.3) / 2.6))
    km = 500 * ease(clamp((lt - 0.3) / 2.6))
    bigc(fr, f'{int(km)} km', 'HACIA ARRIBA', y=0.22 if not VERT else 0.28)
    lab(fr, 'Escala exagerada', 1)


MX = {'CDMX': (19.43, -99.13), 'GDL': (20.67, -103.35)}


def s_scale(fr, t, lt, dur):
    """Escala real: CDMX -> Guadalajara, y esa distancia se para hacia arriba."""
    t0 = t - lt
    kup = ease(clamp((lt - 2.0) / 1.4))
    fr.cam = Cam(target=(0, 0.6 + kup * 1.6, 0), dist=vfit(8.2, wide=True) + kup * 1.5, yaw=-4 + lt * 2, pitch=48 - kup * 36)
    a, b = np.array([2.1, 0.02, 0.4]), np.array([-2.1, 0.02, -0.2])
    k = ease(clamp((lt - 0.3) / 1.3))
    for p, nm in ((a, 'Ciudad de México'), (b, 'Guadalajara')):
        fr.meshes.append(cyl(0.16, 0.12, PINK if nm == 'Guadalajara' else CYAN, n=16).tf(t=tuple(p)))
        ui_text3(fr, tuple(p + np.array([0, 0.55, 0])), nm, 24, fk='b')
    # la línea se levanta: gira alrededor de CDMX hacia la vertical
    L = np.linalg.norm(b - a)
    dirh = (b - a) / L
    top = a + (dirh * math.cos(kup * math.pi / 2) + np.array([0, 1, 0]) * math.sin(kup * math.pi / 2)) * L * k

    def ln(d, cam, top=top):
        line3(d, cam, [a, top], AMBER, 3.4)
        dot3(d, cam, top, 7, AMBER)
    fr.over.append(ln)
    if kup > 0.6:
        fr.meshes += sat_at(tuple(top + np.array([0, 0.3, 0])), s=0.4 * kup, ry=20)
    ui_text3(fr, tuple((a + top) / 2 + np.array([0.35, 0.2, 0])), '≈ 500 km', 28, fk='mono', col=AMBER, a=k)
    lab(fr, 'Escala real · Mapa aproximado', 1)
    head(fr, ['CDMX → Guadalajara,', 'pero hacia arriba.'], AMBER, t, t0 + 0.1, kicker='Escala real')


def s_bounce(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.6, 0), dist=vfit(8.5, wide=True), yaw=-6 + lt * 2.5, pitch=12)
    fr.meshes += house(-3.0, 0.4, ry=15, s=0.75)
    fr.meshes += ground_station(2.8, 0.2, s=0.8)
    sp = (0.0, 4.0, -1.0)
    fr.meshes += sat_at(sp, s=0.6, ry=10 + lt * 3)
    up = clamp((lt - 0.2) / 1.0)
    dn = clamp((t - T(('c1', 4, 'rebota'), default=t0 + 2.0)) / 1.0)
    beam(fr, (-3.2, 1.5, 0.4), sp, CYAN, 3.0, k=up)
    beam(fr, sp, (2.0, 0.7, 0.4), CYAN, 3.0, k=dn, pulse=(lt * 0.9) % 1 if dn >= 1 else None)
    ui_label3(fr, (2.8, 0.9, 0.4), 'Estación en tierra', 'antenas en domos', a=clamp(dn * 2), side=1, length=90)
    head(fr, ['Sube… y', 'rebota.'], CYAN, t, t0 + 0.1, kicker='El satélite es un espejo inteligente')
    lab(fr, 'Recreación', 1)


def s_internet(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0.6, 0.8, 0), dist=vfit(8.0, wide=True), yaw=-14 + lt * 3, pitch=18)
    fr.meshes += ground_station(-2.8, 0.0, s=0.7)
    xs = [1.0, 2.2, 3.4]
    for i, x in enumerate(xs):
        fr.meshes += rack(x, -0.4, lit=lt + i)
    k = clamp((lt - 0.2) / 1.2)

    def fiber(d, cam, k=k, lt=lt):
        P = [(-2.4, 0.03, 0.3), (0.0, 0.03, 0.8), (0.6, 0.03, 0.3)]
        line3(d, cam, [P[0], P[1]], AMBER, 3.0)
        line3(d, cam, [P[1], P[2]], AMBER, 3.0)
        q = (lt * 0.8) % 1.0
        dot3(d, cam, (lerp(-2.4, 0.0, q), 0.05, lerp(0.3, 0.8, q)), 7, (255, 255, 255))
    fr.under.append(fiber)
    names = [('c1', 5, 'YouTube'), ('c1', 5, 'banco'), ('c1', 5, 'juego')]
    txt = ['YouTube', 'Tu banco', 'Tu juego']
    for i, (x, nm) in enumerate(zip(xs, names)):
        ts = T(nm, default=t0 + 1 + i)
        ui_label3(fr, (x, 1.7, -0.1), txt[i], None, a=clamp((t - ts) / 0.4), side=1 if i < 2 else -1, length=60, up=50)
    ui_label3(fr, (-0.4, 0.05, 0.6), 'Fibra óptica', None, a=clamp(lt / 0.5), side=-1, length=70, up=30)
    head(fr, ['Y entra al internet', 'de siempre.'], CYAN, t, t0 + 0.1, kicker='Servidores')


def s_light(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 2.0, 0), dist=vfit(8.0), yaw=-10 + lt * 2, pitch=6)
    fr.meshes += house(0, 0.3, s=0.8)
    sp = (0, 4.6, -0.5)
    fr.meshes += sat_at(sp, s=0.55, ry=30)
    k = clamp((lt - 0.4) / 1.6)
    beam(fr, (-0.24, 1.3, 0.3), sp, (255, 255, 255), 2.0, k=1.0, alpha=0.25)
    beam(fr, (-0.24, 1.3, 0.3), sp, CYAN, 3.2, k=k, pulse=k if k < 1 else None)
    ms = 1.7 * k
    bigc(fr, f'{ms:.1f} ms'.replace('.', ','), 'MILÉSIMAS DE SEGUNDO · SUBIR 500 KM', y=0.22 if not VERT else 0.28)
    lab(fr, 'A la velocidad de la luz · cálculo', 1)


def s_latency(fr, t, lt, dur):
    """Medidor de retraso: 25–60 ms."""
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.0, wide=True), yaw=-6 + lt * 2, pitch=14)
    # barra de 0 a 700 ms en el piso
    L = 5.6
    x0 = -L / 2
    k = ease(clamp((lt - 0.3) / 1.2))
    a_ = x0 + L * 25 / 700
    b_ = x0 + L * 60 / 700

    def bar(d, cam, k=k):
        line3(d, cam, [(x0, 0.02, 0), (x0 + L, 0.02, 0)], MUTED, 2)
        for v in (0, 100, 200, 300, 400, 500, 600, 700):
            x = x0 + L * v / 700
            line3(d, cam, [(x, 0.02, -0.12), (x, 0.02, 0.12)], MUTED, 1.6)
        if k > 0:
            line3(d, cam, [(a_, 0.03, 0), (lerp(a_, b_, k), 0.03, 0)], LGREEN, 9)
    fr.under.append(bar)
    for v in (0, 200, 400, 600):
        ui_text3(fr, (x0 + L * v / 700, 0.0, 0.55), f'{v} ms', 18, fk='mono', col=MUTED)
    fr.meshes.append(box(abs(b_ - a_) + 0.1, 0.5 * k + 0.01, 0.5, (60, 170, 110), shadow=0.35).tf(t=((a_ + b_) / 2, 0, -0.6)))
    ui_text3(fr, ((a_ + b_) / 2, 0.95, -0.6), 'Starlink', 26, fk='b', a=k)
    bigc(fr, '25–60 ms', 'RETRASO TÍPICO DE IDA Y VUELTA', a=clamp(lt / 0.4), y=0.22 if not VERT else 0.28)
    lab(fr, 'Fuente: guías de latencia 2026', 1)


def s_geo(fr, t, lt, dur):
    """Satélite de antes: a 36 mil km (geoestacionario) vs Starlink a ~500 km. Escala real."""
    t0 = t - lt
    fr.floor = 0.0
    k = ease(clamp((lt - 0.3) / 2.0))
    fr.cam = Cam(target=(0, 0, 0), dist=lerp(5.0, 14.5, k) * (1.0 if not VERT else 1.45), yaw=0, pitch=88, cy=0.5)
    R = 0.6  # Tierra 6,371 km -> 0.6
    s = R / 6371
    fr.meshes.append(earth(R, lon0=-100, lat_tilt=90, nu=36, nv=18).tf(t=(0, 0, 0)))

    def rings(d, cam, k=k):
        ring3(d, cam, (0, 0, 0), (6371 + 500) * s, LGREEN, 2.4)
        ring3(d, cam, (0, 0, 0), (6371 + 35786) * s, AMBER, 2.4, a=k)
    fr.over.append(rings)
    ui_text3(fr, (0, 0, -(6371 + 35786) * s - 0.4), 'Satélite de antes · 36 mil km', 24, fk='b', col=AMBER, a=k)
    ui_text3(fr, (0.0, 0, R + 0.35), 'Starlink · ~500 km', 20, fk='b', col=LGREEN, a=1 - k * 0.4)
    tv = T(('c1', 8, '600'), default=t0 + 2.6)
    bigc(fr, '600+ ms', 'EL INTERNET SATELITAL DE ANTES', a=clamp((t - tv) / 0.4), y=0.16 if not VERT else 0.2)
    lab(fr, 'Escala real · órbitas', 1)


def s_lag(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.1, 0), dist=vfit(6.2, wide=True), yaw=-12 + lt * 3, pitch=8)
    scr = box(3.0, 1.7, 0.08, (14, 14, 18), shadow=0.35, base=False)

    def ftex(d, im, lt=lt):
        w, h = im.size
        d.rectangle((0, 0, w, h), fill=(16, 20, 40))
        d.rectangle((0, h * 0.7, w, h), fill=(40, 90, 50))
        # dos jugadores (cuadros) y la bala congelada
        d.rectangle((w * 0.12, h * 0.45, w * 0.2, h * 0.7), fill=(90, 160, 255))
        d.rectangle((w * 0.78, h * 0.45, w * 0.86, h * 0.7), fill=(255, 90, 110))
        d.text((w * 0.5, h * 0.25), 'LAG 600 ms', font=font('mono', 44), fill=(255, 210, 80), anchor='mm')
    img = tex(480, 272, (0, 0, 0, 255), ftex)
    decal(scr, scr.FACE['front'], img)
    fr.meshes.append(scr.tf(t=(0, 1.35, 0)))
    fr.meshes.append(box(0.5, 0.5, 0.3, (40, 40, 46), shadow=0.35).tf(t=(0, 0, 0)))
    # control
    fr.meshes.append(rbox(0.9, 0.12, 0.5, 0.15, (30, 30, 36), gloss=0.5).tf(t=(1.2, 0.0, 1.3)))
    head(fr, ['Medio segundo', 'y pierdes.'], LASER, t, t0 + 0.1, kicker='Partidas en línea')
    lab(fr, 'Recreación', 1)

# ================================================================== PARTE 2 (c2): la antena por dentro
def dish_tiles(fr, cx, cy, cz, w, h, nx, ny, tilt, lt, glow=0.0, phase=None, a=1.0, cols=None):
    """Rejilla de antenas diminutas sobre un panel inclinado (rx = tilt). phase: dirección de la onda."""
    R = rotm(tilt, 0, 0)
    for ix in range(nx):
        for iy in range(ny):
            u = (ix + 0.5) / nx - 0.5
            v = (iy + 0.5) / ny - 0.5
            p = np.array([u * w, 0.0, v * h]) @ R.T + np.array([cx, cy, cz])
            col = (200, 204, 214)
            if cols is not None:
                col = cols(ix, iy)
            if phase is not None:
                ph = math.sin(lt * 6 - (u * phase[0] + v * phase[1]) * 8)
                col = mix((60, 70, 90), CYAN, 0.5 + 0.5 * ph)
            m = box(w / nx * 0.72, 0.03, h / ny * 0.72, col, shadow=0, edge=False, base=False, gloss=0.3).tf(rx=tilt, t=tuple(p))
            m.alpha = a
            fr.meshes.append(m)


def s_plate(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(6.4, wide=True), yaw=-14 + lt * 3, pitch=12)
    # plato de antes (parabólico) a la izquierda, tachado
    pl = cyl(0.08, 0.5, (200, 200, 204), r2=0.95, n=26, top=(226, 226, 230), shadow=0.35, gloss=0.4)
    fr.meshes.append(cyl(0.04, 0.6, (160, 160, 166), n=10).tf(t=(-1.7, 0, 0)))
    fr.meshes.append(pl.tf(rx=-50, t=(-1.7, 0.75, 0)))
    tr = T(('c2', 1, 'radar'), default=t0 + 2.0)
    k = eback((t - tr) / 0.5)
    if k > 0:
        fr.meshes += dish(1.6, 0, 0.2, ry=-12, tilt=-30, s=1.5 * max(0.05, k))
    def cross(d, cam, a=clamp((t - t0 - 1.0) / 0.4)):
        if a > 0:
            line3(d, cam, [(-2.6, 0.2, 0.6), (-0.8, 1.7, -0.4)], LASER, 4, a=a)
            line3(d, cam, [(-2.6, 1.7, -0.4), (-0.8, 0.2, 0.6)], LASER, 4, a=a)
    fr.over.append(cross)
    head(fr, ['No es un plato:', 'es un radar plano.'], CYAN, t, t0 + 0.1, kicker='Parte 2')


def s_xray(fr, t, lt, dur):
    """Escáner de rayos X sobre la antena: la cubierta se vuelve transparente y aparecen las antenas diminutas."""
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.7, 0), dist=vfit(4.6), yaw=-20 + lt * 6, pitch=32)
    ts, te = t0 + 0.2, t0 + 1.6
    ys, k = scan_ring(fr, t, ts, te, 0.0, 1.4, center=(0, 0, 0), r=1.15)
    shell_a = 1 - 0.85 * ease(k)
    tilt = -18
    fr.meshes.append(cyl(0.05, 0.55, (210, 210, 214), n=12).tf(t=(0, 0, 0)))
    pnl = rbox(1.4, 0.07, 1.9, 0.12, WHITE, gloss=0.4, base=False).tf(rx=tilt, t=(0, 0.62, 0))
    pnl.alpha = shell_a
    if k > 0.05:
        dish_tiles(fr, 0, 0.64, 0, 1.25, 1.75, 9, 12, tilt, lt, a=1.0)
    fr.meshes.append(pnl)
    lab(fr, 'Así se ve por dentro · Recreación', clamp(lt / 0.4))
    head(fr, ['Así se ve', 'por dentro.'], CYAN, t, t0 + 0.1, kicker='Rayos X')


LOT = [(214, 60, 60), (40, 120, 200), (240, 180, 50), (60, 160, 90), (200, 80, 160), (250, 120, 40)]


def s_loteria(fr, t, lt, dur):
    """Tabla de lotería que se convierte en la rejilla de la antena."""
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.4, 0), dist=vfit(5.4), yaw=-8 + lt * 3, pitch=58)
    km = ease(clamp((t - T(('c2', 3, 'casillas'), default=t0 + 2.5)) / 1.2))
    def cols(ix, iy):
        c = LOT[(ix * 7 + iy * 3) % len(LOT)]
        return mix(c, (200, 204, 214), km)
    n = 4 + int(km * 8)
    fr.meshes.append(box(2.5, 0.05, 2.5, (246, 240, 226) if km < 0.5 else (236, 236, 240), shadow=0.3))
    dish_tiles(fr, 0, 0.07, 0, 2.3, 2.3, n, n, 0, lt, cols=cols)
    ui_text3(fr, (0, 0.2, -1.55), 'LOTERÍA' if km < 0.5 else 'cientos de antenas', 30, fk='xb' if km < 0.5 else 'b',
             col=(200, 60, 60) if km < 0.5 else INK)
    head(fr, ['Cientos de', 'antenas diminutas.'], CYAN, t, t0 + 0.1, kicker='Como una lotería')
    lab(fr, 'Recreación · número aproximado', 1)


def s_phase(fr, t, lt, dur):
    """Ninguna se mueve: la onda de fase cambia y el haz apunta a otro lado."""
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.1, 0), dist=vfit(6.0), yaw=-24 + lt * 3, pitch=22)
    ang = math.sin(lt * 0.9) * 35
    ph = (math.sin(math.radians(ang)) * 1.6, 0.0)
    fr.meshes.append(box(2.2, 0.06, 1.6, (230, 230, 234), shadow=0.35))
    dish_tiles(fr, 0, 0.09, 0, 2.0, 1.4, 10, 7, 0, lt, phase=ph)
    a = math.radians(ang)
    tip = (math.sin(a) * 3.2, 3.4, -0.2)

    def bm(d, cam):
        for j, w in enumerate((10, 5, 2.4)):
            line3(d, cam, [(0, 0.1, 0), tip], CYAN, w, a=0.25 + j * 0.3)
    fr.over.append(bm)
    fr.meshes += sat_at((tip[0], tip[1] + 0.25, tip[2]), s=0.35, ry=20)
    head(fr, ['Ninguna', 'se mueve.'], CYAN, t, t0 + 0.1, kicker='Apuntan con electrónica')
    lab(fr, 'Antena de fase · recreación', 1)


def s_track(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.8, 0), dist=vfit(8.5, wide=True), yaw=-4 + lt * 1.5, pitch=8)
    fr.meshes += house(0, 0.6, s=0.8)
    k = clamp(lt / max(1.0, dur))
    th = math.radians(160 - 140 * k)
    sp = (math.cos(th) * 3.8, 0.8 + math.sin(th) * 2.8, -1.2)
    fr.meshes += sat_at(sp, s=0.6, ry=-20)

    def arc(d, cam):
        P = [(math.cos(math.radians(a)) * 3.8, 0.8 + math.sin(math.radians(a)) * 2.8, -1.2) for a in range(20, 161, 4)]
        line3(d, cam, P, ICE, 1.2, dash=6, a=0.5)
    fr.under.append(arc)
    beam(fr, (-0.25, 1.25, 0.6), sp, CYAN, 3.0)
    mm = 4 * k
    bigc(fr, f'{int(mm)}:{int((mm % 1) * 60):02d} min', 'CRUZA EL CIELO EN UNOS MINUTOS', y=0.16 if not VERT else 0.24, size=60 if not VERT else 80)
    lab(fr, 'Recreación', 1)


def s_handoff(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.8, 0), dist=vfit(8.5, wide=True), yaw=6 - lt * 1.5, pitch=6)
    fr.meshes += house(0, 0.6, s=0.8)
    th_ = T(('c2', 6, 'salta'), default=t0 + 2.6)
    k = clamp((t - t0) / 3.5)
    a1 = math.radians(40 - 30 * k)
    a2 = math.radians(150 - 30 * k)
    p1 = (math.cos(a1) * 4.5, 0.8 + math.sin(a1) * 3.6, -1.2)
    p2 = (math.cos(a2) * 4.5, 0.8 + math.sin(a2) * 3.6, -1.2)
    fr.meshes += sat_at(p1, s=0.42, ry=-20)
    fr.meshes += sat_at(p2, s=0.42, ry=20)
    src = (-0.25, 1.25, 0.6)
    if t < th_:
        beam(fr, src, p1, CYAN, 3.0)
    else:
        beam(fr, src, p2, CYAN, 3.0, k=clamp((t - th_) / 0.25))
        def fl(d, cam, a=1 - clamp((t - th_) / 0.6)):
            ring3(d, cam, (0, 0.05, 0.6), 0.5 + (1 - a), LGREEN, 3, a)
        fr.over.append(fl)
    ui_text3(fr, (4.4, 0.2, -1.2), 'horizonte', 20, fk='sb', col=MUTED)

    def hz(d, cam):
        line3(d, cam, [(-6, 0.02, -1.2), (6, 0.02, -1.2)], MUTED, 1.4, dash=8)
    fr.under.append(hz)
    head(fr, ['Salta al', 'siguiente.'], LGREEN, t, t0 + 0.1, kicker='Sin que lo notes')


def jet(x=0.0, y=0.0, z=0.0, ry=0.0, s=1.0):
    body = extrude([(-0.15, -1.4), (0.15, -1.4), (0.18, 0.8), (0.0, 1.4), (-0.18, 0.8)], 0.22, (120, 128, 140), shadow=0.35)
    wing = extrude([(-1.2, 0.0), (1.2, 0.0), (0.2, 0.9), (-0.2, 0.9)], 0.05, (104, 112, 124), shadow=0.35, y0=0.08)
    tail = extrude([(-0.5, -1.4), (0.5, -1.4), (0.1, -0.9), (-0.1, -0.9)], 0.05, (104, 112, 124), shadow=0.35, y0=0.08)
    return [m.tf(s=s, ry=ry, t=(x, y, z)) for m in (body, wing, tail)]


def s_jet(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(7.4, wide=True), yaw=-20 + lt * 3, pitch=22)
    fr.meshes += jet(-1.8, 0.6, 0.0, ry=60, s=1.0)
    nose = np.array([-1.8, 0.75, 0.0]) + np.array([math.sin(math.radians(60)), 0, math.cos(math.radians(60))]) * 1.4
    tp = T(('c2', 7, 'pero'), default=t0 + 3.0)
    k = eback((t - tp) / 0.6)
    if k > 0:
        fr.meshes += house(2.0, 0.0, s=0.9 * max(0.05, k))
    def rd(d, cam):
        for j in range(3):
            r = 0.3 + ((lt * 0.8 + j / 3) % 1) * 1.2
            ring3(d, cam, tuple(nose), r, CYAN, 2, 1 - (r - 0.3) / 1.2, axis='z')
    fr.over.append(rd)
    ui_label3(fr, tuple(nose), 'Radar de fase', 'aviones de combate', a=clamp(lt / 0.5), side=-1, length=80)
    if t >= tp:
        head(fr, ['Y cabe en', 'tu azotea.'], CYAN, t, tp, kicker='La misma idea')
    else:
        head(fr, ['Tecnología', 'de radar.'], CYAN, t, t0 + 0.1, kicker='La misma idea')
    lab(fr, 'Recreación', 1)


# ================================================================== PARTE 3 (c3): láseres
def s_lasers(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(7.0, wide=True), yaw=-20 + lt * 4, pitch=10)
    fr.meshes.append(earth(ER, lon0=-40, lat_tilt=30, spin=lt).tf(t=(0, -6.6, -1.0)))
    ps = [(-2.6, 0.9, 0.3), (0.0, 1.4, -0.8), (2.6, 0.8, 0.2)]
    for i, p in enumerate(ps):
        fr.meshes += sat_at(p, s=0.5, ry=10 + i * 25)
    k1 = clamp((lt - 0.4) / 0.6)
    k2 = clamp((lt - 1.1) / 0.6)
    beam(fr, ps[0], ps[1], LASER, 3.0, k=k1, pulse=(lt * 1.2) % 1 if k1 >= 1 else None)
    beam(fr, ps[1], ps[2], LGREEN, 3.0, k=k2, pulse=(lt * 1.2 + 0.5) % 1 if k2 >= 1 else None)
    head(fr, ['Se hablan', 'con láseres.'], LASER, t, t0 + 0.1, kicker='Parte 3')
    lab(fr, 'Recreación · colores de los láseres ilustrativos', 1)


def s_mesh(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0, 0), dist=vfit(8.2), yaw=-10 + lt * 5, pitch=18, cy=0.64 if not VERT else 0.56)
    fr.meshes.append(earth(1.8, lon0=-60, lat_tilt=25, spin=lt * 4))
    fr.under.append(lambda d, cam: atmo(d, cam, (0, 0, 0), 1.82))
    pts = shell_points(120, 2.25, (0, 0, 0), t, seed=8, speed=0.08, planes=12)
    k = clamp((lt - 0.3) / 2.0)

    def links(d, cam, k=k):
        n = int(len(pts) * k)
        for i in range(n):
            a = pts[i]
            b = pts[(i + 1) % len(pts)] if (i + 1) % 10 else pts[(i + 10) % len(pts)]
            if hidden(a, (0, 0, 0), cam.pos, 1.8) or hidden(b, (0, 0, 0), cam.pos, 1.8):
                continue
            line3(d, cam, [a, b], LASER if i % 3 else LGREEN, 1.4, a=0.8)
    fr.over.append(links)
    draw_shell(fr, pts, (0, 0, 0), 1.8, ICE, 3)
    v = 9000 * eout((t - T(('c3', 2, '9'), default=t0 + 1)) / 1.5)
    bigc(fr, '+' + fmt_int(max(0, v)), 'LÁSERES CONECTADOS (INICIOS DE 2024)', y=0.14 if not VERT else 0.2, size=64 if not VERT else 84)
    lab(fr, 'Recreación', 1)


def s_gbps(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(6.4, wide=True), yaw=-24 + lt * 3, pitch=8)
    a, b = np.array([-2.8, 1.0, 0.0]), np.array([2.8, 1.0, 0.0])
    fr.meshes += sat_at(tuple(a), s=0.55, ry=90)
    fr.meshes += sat_at(tuple(b), s=0.55, ry=90)
    beam(fr, a, b, LASER, 2.0, alpha=0.6)
    for i in range(10):
        u = (lt * 0.7 + i / 10) % 1.0
        p = a + (b - a) * u
        fr.meshes.append(box(0.16, 0.16, 0.16, mix(LASER, (255, 255, 255), 0.4), shadow=0, base=False, gloss=0.6).tf(rx=lt * 90, ry=lt * 60, t=tuple(p)))
    v = 100 * eout((lt - 0.2) / 1.0)
    bigc(fr, f'{int(v)} Gbps', 'POR CADA ENLACE LÁSER (HASTA)', y=0.2 if not VERT else 0.28)
    lab(fr, 'Recreación', 1)


def s_far(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    k = ease(clamp((lt - 0.3) / 1.8))
    fr.cam = Cam(target=(0, 0.5, 0), dist=vfit(5.5 + k * 5, wide=True), yaw=-6 + lt * 2, pitch=14)
    d = 0.8 + k * 4.2
    a, b = np.array([-d, 0.6, 0]), np.array([d, 0.6, 0])
    fr.meshes += sat_at(tuple(a), s=0.45, ry=90)
    fr.meshes += sat_at(tuple(b), s=0.45, ry=90)
    beam(fr, a, b, LGREEN, 3.0)

    def ruler(dd, cam, d=d):
        line3(dd, cam, [(-d, 0.0, 0.0), (d, 0.0, 0.0)], MUTED, 1.6)
        for j in range(11):
            x = -d + 2 * d * j / 10
            line3(dd, cam, [(x, -0.08, 0), (x, 0.08, 0)], MUTED, 1.4)
    fr.under.append(ruler)
    v = 5400 * k
    bigc(fr, fmt_int(v) + ' km', 'DISTANCIA DE UN ENLACE (MÁS DE)', y=0.2 if not VERT else 0.28)
    lab(fr, 'Escala exagerada', 1)


def s_ocean(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0, 0), dist=vfit(7.6), yaw=0, pitch=12, cy=0.64 if not VERT else 0.56)
    fr.meshes.append(earth(2.2, lon0=-40, lat_tilt=30, spin=0))
    fr.under.append(lambda d, cam: atmo(d, cam, (0, 0, 0), 2.22))
    # puntos sobre el océano Atlántico: de México a Europa
    def sph(lat, lon, r):
        R = rotm(30, 0, 0) @ rotm(0, 40, 0)
        la, lo = math.radians(lat), math.radians(lon)
        v = np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)])
        return tuple(v @ R.T * r)
    chain = [sph(22, -100 + i * 13, 2.6) for i in range(10)]
    k = clamp((lt - 0.3) / 2.6)
    n = int(1 + k * (len(chain) - 1))
    for p in chain[:n]:
        fr.meshes += sat_at(p, s=0.16, ry=10)

    def hop(d, cam, n=n):
        for i in range(n - 1):
            line3(d, cam, [chain[i], chain[i + 1]], LASER, 2.6)
        a = sph(22, -100, 2.2); b = sph(22, -100 + 9 * 13, 2.2)
        line3(d, cam, [a, chain[0]], CYAN, 2.0)
        if n == len(chain):
            line3(d, cam, [chain[-1], b], CYAN, 2.0)
    fr.over.append(hop)
    head(fr, ['Cruza un océano', 'sin cables.'], LASER, t, t0 + 0.1, kicker='De satélite en satélite')
    lab(fr, 'Recreación · ruta ilustrativa', 1)


def s_42(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(7.4, wide=True) + lt * 0.3, yaw=-20 + lt * 4, pitch=18)
    k = ease(clamp((lt - 0.3) / 2.6))
    n = int(4 + k * 60)
    for i in range(n):
        x = (i % 8) - 3.5
        z = ((i // 8) % 4) * 0.7 - 1.0
        y = (i // 32) * 0.45
        fr.meshes.append(box(0.55, 0.4, 0.55, (70, 80, 100), cols={'top': (96, 110, 140)}, shadow=0.3).tf(t=(x * 0.7, y, z)))
    v = 42e6 * k
    bigc(fr, fmt_int(v) + ' GB', 'DATOS POR LÁSER EN UN DÍA', y=0.16 if not VERT else 0.24, size=64 if not VERT else 80)
    lab(fr, 'Dato de SpaceX, inicios de 2024', 1)


def s_movies(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.5, 0), dist=vfit(8.0, wide=True), yaw=-10 + lt * 2, pitch=40)
    k = ease(clamp((lt - 0.2) / 3.0))
    n = int(8 + k * 140)
    rng = np.random.RandomState(2)
    for i in range(n):
        x = (i % 14) - 6.5
        z = (i // 14) - 4.5
        c = [(90, 150, 230), (230, 120, 90), (110, 190, 120), (230, 190, 90)][i % 4]
        fr.meshes.append(cyl(0.16, 0.42, c, n=8, shadow=0.2, gloss=0.2).tf(t=(x * 0.5, 0, z * 0.5)))
        fr.meshes.append(sphere(0.12, (230, 196, 160), nu=8, nv=5, shadow=0, gloss=0.2).tf(t=(x * 0.5, 0.55, z * 0.5)))
    bigc(fr, '42 millones', 'DE PELÍCULAS DE 1 GB, CADA DÍA', y=0.16 if not VERT else 0.24, size=64 if not VERT else 80)
    lab(fr, 'Comparación ilustrativa', 1)


# ================================================================== PARTE 4 (c4): cómo no chocan
def s_dodge(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(6.6, wide=True), yaw=-30 + lt * 3, pitch=22)
    fr.meshes.append(earth(ER, lon0=-100, lat_tilt=40, spin=lt).tf(t=(0, -6.8, -1.5)))
    k = clamp(lt / 3.2)
    a = np.array([-3.0 + 3.0 * k, 0.8, 0.0])
    b = np.array([0.0, 0.8, -3.0 + 3.0 * k])
    tdod = t0 + 1.6
    dz = ease(clamp((t - tdod) / 0.8)) * 0.9
    a[1] += dz
    fr.meshes += sat_at(tuple(a), s=0.45, ry=90)
    fr.meshes += sat_at(tuple(b), s=0.45, ry=0)

    def paths(d, cam):
        line3(d, cam, [(-3.2, 0.8, 0), (3.2, 0.8, 0)], AMBER, 1.4, dash=6, a=0.6)
        line3(d, cam, [(0, 0.8, -3.2), (0, 0.8, 3.2)], AMBER, 1.4, dash=6, a=0.6)
        if t > tdod and t < tdod + 1.0:
            ring3(d, cam, tuple(a - np.array([0, 0.25, 0])), 0.2 + (t - tdod) * 0.6, (255, 255, 255), 2, 1 - (t - tdod))
    fr.over.append(paths)
    v = 150000 * eout((lt - 0.4) / 5.5)
    bigc(fr, fmt_int(max(0, v)), 'CHOQUES ESQUIVADOS EN 6 MESES (CASI)', y=0.16 if not VERT else 0.24, size=70 if not VERT else 84)
    head(fr, [], AMBER, t, t0)
    lab(fr, 'Parte 4 · Recreación', 1, dotc=AMBER)


def s_tally(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.4, wide=True), yaw=-8 + lt * 2, pitch=16)
    meses = ['JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV']
    vals = [0.8, 0.9, 0.95, 1.0, 1.1, 1.2]   # forma ilustrativa (el total es el dato)
    for i, (m, v) in enumerate(zip(meses, vals)):
        x = -2.5 + i
        h = 1.8 * v * eout((lt - 0.2 - i * 0.15) / 0.6)
        fr.meshes.append(box(0.6, max(0.02, h), 0.6, AMBER if i == 5 else (200, 150, 60), shadow=0.35).tf(t=(x, 0, 0)))
        ui_text3(fr, (x, -0.05, 0.7), m, 22, fk='mono', col=MUTED)
    v = 148696 * eout((lt - 0.2) / 2.2)
    bigc(fr, fmt_int(v), 'MANIOBRAS · JUNIO–NOVIEMBRE 2025', y=0.18 if not VERT else 0.24)
    lab(fr, 'Reporte de SpaceX a la FCC · barras ilustrativas', 1, dotc=AMBER)


def s_odds(fr, t, lt, dur):
    """3 en 10 millones: un mar de puntos con 3 encendidos."""
    t0 = t - lt
    fr.cam = Cam(target=(0, 0, 0), dist=vfit(7.0) - lt * 0.4, yaw=-10 + lt * 3, pitch=55)
    hl = [(3, 5), (12, 9), (7, 15)]

    def grid(d, cam, lt=lt):
        n = 22
        for i in range(n):
            for j in range(n):
                p = (-3 + 6 * i / (n - 1), 0, -3 + 6 * j / (n - 1))
                if (i, j) in hl:
                    a = 0.6 + 0.4 * math.sin(lt * 6)
                    dot3(d, cam, p, 13, LASER, a)
                else:
                    dot3(d, cam, p, 4.5, MUTED, 0.85)
    fr.over.append(grid)
    bigc(fr, '3 en 10,000,000', 'RIESGO A PARTIR DEL CUAL SE APARTAN', y=0.16 if not VERT else 0.22, size=70 if not VERT else 80)
    lab(fr, 'Cada punto representa miles de casos · ilustrativo', 1, dotc=AMBER)


def s_still(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(4.6), yaw=20 - lt * 4, pitch=10)
    tm = T(('c4', 4, 'mueven'), default=t0 + 2.6)
    dy = ease(clamp((t - tm) / 0.6)) * 0.5
    fr.meshes += sat_at((0, 0.8 + dy, 0), s=0.9, ry=30)
    if t > tm:
        def puff(d, cam, a=1 - clamp((t - tm) / 0.9)):
            for j in range(6):
                q = (0.05 * j - 0.1, 0.6 + dy - (t - tm) * (0.4 + j * 0.15), 0.05 * j)
                dot3(d, cam, q, 6 + j * 2, ICE, a * 0.7)
        fr.over.append(puff)
    head(fr, ['Y aun así,', 'se mueven.'], AMBER, t, t0 + 0.1, kicker='Un riesgo diminuto')
    lab(fr, 'Motor de iones · recreación', 1, dotc=AMBER)


def s_lower(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 2.0, 0), dist=vfit(7.6, wide=True), yaw=0, pitch=4, cy=0.6 if not VERT else 0.55)
    fr.meshes.append(earth(14.0, lon0=-100, lat_tilt=70, nu=60, nv=30).tf(t=(0, -14.0, -2)))
    y550, y480 = 3.4, 2.2
    k = ease(clamp((lt - 1.0) / 2.6))

    def shells(d, cam):
        for yy, c, txt in ((y550, AMBER, '550 km'), (y480, LGREEN, '480 km')):
            line3(d, cam, [(-6, yy, -1), (6, yy, -1)], c, 1.6, dash=7, a=0.8)
    fr.over.append(shells)
    for i in range(5):
        x = -3.6 + i * 1.8
        y = lerp(y550, y480, clamp(k * 1.4 - i * 0.08))
        fr.meshes += sat_at((x, y, -1), s=0.5, ry=10, rx=55)
    ui_text3(fr, (5.0, y550 + 0.3, -1), '550 km', 22, fk='mono', col=AMBER)
    ui_text3(fr, (5.0, y480 + 0.3, -1), '480 km', 22, fk='mono', col=LGREEN)
    head(fr, ['Más abajo,', 'más seguro.'], LGREEN, t, t0 + 0.1, kicker='Cambio de órbita en 2026')
    lab(fr, 'Escala exagerada', 1, dotc=AMBER)


def s_debris(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 2.0, 0), dist=vfit(7.6, wide=True), yaw=-4 + lt * 1.5, pitch=6, cy=0.6 if not VERT else 0.55)
    fr.meshes.append(earth(14.0, lon0=-100, lat_tilt=70, nu=60, nv=30).tf(t=(0, -14.0, -2)))
    rng = np.random.RandomState(4)
    for i in range(34):
        x = rng.uniform(-6, 6) + math.sin(lt + i) * 0.2
        y = rng.uniform(2.7, 5.0) if i < 28 else rng.uniform(1.4, 2.4)
        z = rng.uniform(-3, 0)
        fr.meshes.append(box(0.12, 0.08, 0.1, (150, 140, 130), shadow=0, base=False).tf(rx=i * 30 + lt * 50, ry=i * 17, t=(x, y, z)))

    def lines(d, cam):
        line3(d, cam, [(-6, 2.55, -1), (6, 2.55, -1)], MUTED, 1.4, dash=7, a=0.8)
        for j in range(5):  # aire más denso abajo
            line3(d, cam, [(-6, 0.3 + j * 0.25, -1), (6, 0.3 + j * 0.25, -1)], CYAN, 6 - j, a=0.12)
    fr.under.append(lines)
    ui_text3(fr, (4.6, 2.85, -1), '500 km', 22, fk='mono', col=MUTED)
    ui_label3(fr, (-3.0, 4.0, -1.5), 'Basura espacial', 'más arriba hay más', a=clamp(lt / 0.5), side=1, length=80)
    head(fr, ['Menos basura', 'abajo.'], LGREEN, t, t0 + 0.1, kicker='Y el aire frena más')
    lab(fr, 'Recreación · ilustrativo', 1, dotc=AMBER)


def s_burn(fr, t, lt, dur):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 1.6, 0), dist=vfit(7.8, wide=True), yaw=-6 + lt * 2, pitch=6, cy=0.6 if not VERT else 0.55)
    fr.meshes.append(earth(14.0, lon0=-100, lat_tilt=70, nu=60, nv=30).tf(t=(0, -14.0, -2)))
    k = ease(clamp((lt - 0.6) / 3.6))
    p = np.array([-3.5 + k * 6.0, 4.4 - k * 4.0, -1.0])
    if k < 0.85:
        fr.meshes += sat_at(tuple(p), s=0.4, rz=k * 160, rx=k * 90, alpha=1 - clamp((k - 0.6) / 0.25))

    def fire(d, cam, p=p, k=k):
        if k <= 0.3:
            return
        a = clamp((k - 0.3) / 0.2)
        for j in range(14):
            q = p - np.array([0.25 * j, -0.2 * j, 0]) * (0.3 + k)
            c = mix(AMBER, LASER, j / 14)
            dot3(d, cam, tuple(q), max(1, 10 - j * 0.6), c, a * (1 - j / 14))
    fr.over.append(fire)
    head(fr, ['Cae y se', 'quema.'], AMBER, t, t0 + 0.1, kicker='Un satélite muerto')
    lab(fr, 'Recreación', 1, dotc=AMBER)


# ================================================================== PARTE 5 (c5): México
def coin_stack(x, z, n, s=1.0):
    return [cyl(0.32 * s, 0.07, (204, 160, 52), n=22, top=(232, 196, 90), gloss=0.8, shadow=0.3).tf(t=(x + 0.02 * math.sin(i), i * 0.075, z)) for i in range(n)]


def s_cost(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(6.4, wide=True), yaw=-24 + lt * 4, pitch=16)
    fr.meshes += house(-1.0, 0, s=1.0)
    for i in range(3):
        n = int(clamp((lt - 0.4 - i * 0.3) / 0.8) * (6 + i * 3))
        fr.meshes += coin_stack(1.3 + i * 0.75, 0.6, n)
    head(fr, ['¿Cuánto cuesta', 'en México?'], AMBER, t, t0 + 0.1, kicker='Parte 5')


def s_plan(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.1, 0), dist=vfit(5.4, wide=True), yaw=-14 + lt * 4, pitch=8)
    k = eback((lt - 0.2) / 0.6)
    tg = tag3('$1,050', 'AL MES', w=2.4, h=1.1)
    fr.meshes.append(tg.tf(s=max(0.05, k), ry=-8 + math.sin(lt) * 4, t=(0, 1.3, 0)))
    fr.meshes.append(cyl(0.02, 0.8, (180, 180, 186), n=8).tf(t=(0, 0, 0)))
    lab(fr, 'Precio de lista oct 2026 · sin impuestos', 1, dotc=AMBER)


def s_kit(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(6.4, wide=True), yaw=-20 + lt * 4, pitch=18)
    k = ease(clamp((lt - 0.3) / 1.0))
    fr.meshes.append(box(1.6, 0.9, 1.1, (236, 236, 240), cols={'top': (250, 250, 252)}, shadow=0.4).tf(t=(-1.6, 0, 0)))
    fr.meshes += dish(0.2, 0, 0.0, ry=-10, tilt=-30, s=1.2 * max(0.05, k))
    fr.meshes.append(rbox(0.5, 0.7, 0.25, 0.06, (240, 240, 244), gloss=0.4).tf(t=(1.5, 0, 0.3)))
    ui_label3(fr, (1.5, 0.75, 0.3), 'Módem', None, a=k, side=1, length=60)
    ui_label3(fr, (0.2, 1.2, 0), 'Antena', None, a=k, side=-1, length=70)
    v = 3499 * eout((lt - 0.8) / 2.0)
    bigc(fr, '$' + fmt_int(max(0, v)), 'EL EQUIPO (PAGO ÚNICO, APROX.)', y=0.18 if not VERT else 0.26)
    lab(fr, 'Precio de lista oct 2026 · sin impuestos', 1, dotc=AMBER)


def s_tax(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(6.0, wide=True), yaw=-10 + lt * 3, pitch=40)
    rc = box(1.4, 0.03, 2.2, (248, 248, 244), shadow=0.35)

    def ftex(d, im):
        w, h = im.size
        f = font('mono', 26)
        rows = [('Plan', '$1,050'), ('Equipo', '$3,499'), ('+ IVA', '...'), ('Recargo zona', '?')]
        d.text((w / 2, 40), 'TU RECIBO', font=font('mono', 30), fill=(30, 30, 30), anchor='mm')
        for i, (a, b) in enumerate(rows):
            d.text((24, 110 + i * 60), a, font=f, fill=(40, 40, 40), anchor='lm')
            d.text((w - 24, 110 + i * 60), b, font=f, fill=(40, 40, 40), anchor='rm')
    decal(rc, rc.FACE['top'], tex(300, 470, (248, 248, 244, 255), ftex))
    fr.meshes.append(rc.tf(ry=10, t=(-1.0, 0, 0)))
    # pin de mapa
    k = eback((lt - 0.8) / 0.6)
    if k > 0:
        fr.meshes.append(cyl(0.02, 0.2, LASER, n=8, r2=0.25 * k, shadow=0.3).tf(t=(1.5, 0, 0.2)))
        fr.meshes.append(sphere(0.25 * k, LASER, nu=16, nv=10).tf(t=(1.5, 0.45, 0.2)))
    head(fr, ['Más impuestos,', 'según tu dirección.'], AMBER, t, t0 + 0.1, kicker='Ojo')
    lab(fr, 'Ilustrativo', 1, dotc=AMBER)


MEXICO = [(32.5, -117.1), (32.7, -114.7), (31.3, -111.0), (31.3, -108.2), (31.8, -106.5), (29.8, -104.5), (29.0, -103.0),
          (29.8, -101.4), (27.8, -99.5), (26.0, -97.2), (22.4, -97.8), (19.2, -96.1), (18.5, -94.5), (18.6, -91.7),
          (21.5, -90.3), (21.5, -87.0), (18.4, -88.0), (17.8, -89.2), (16.0, -90.5), (14.6, -92.2), (15.8, -94.0),
          (16.2, -96.5), (17.0, -100.0), (18.2, -103.5), (20.5, -105.5), (23.0, -106.5), (26.0, -109.3), (28.0, -111.3),
          (30.0, -113.1), (31.5, -114.5)]
BAJA = [(32.5, -117.1), (31.5, -116.6), (28.0, -114.2), (24.0, -110.5), (22.9, -109.9), (24.5, -111.8), (27.5, -114.5),
        (30.5, -116.0)]


def llm(lat, lon):
    return ((lon + 102.0) * 0.26, -(lat - 23.5) * 0.26)


def s_clients(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0, 0.2), dist=vfit(7.4, wide=True), yaw=-4 + lt * 2, pitch=58)
    kk = eback((lt - 0.1) / 0.6)
    for poly in (MEXICO, BAJA):
        fr.meshes.append(extrude([llm(a, b) for a, b in poly], max(0.01, 0.12 * kk), (70, 140, 90), top=(84, 160, 104), edge=True, shadow=0))
    k = clamp((lt - 0.4) / 3.0)
    rng = np.random.RandomState(9)
    pts = []
    while len(pts) < 160:
        la, lo = rng.uniform(15, 32), rng.uniform(-116, -87)
        x, z = llm(la, lo)
        pts.append((x, z))
    path = _MXP()
    pts = [p for p in pts if path.contains_point(p)]

    def dots(d, cam, k=k):
        for p in pts[:int(len(pts) * k)]:
            dot3(d, cam, (p[0], 0.14, p[1]), 3, ICE)
    fr.over.append(dots)
    v = 150000 * eout(k)
    bigc(fr, fmt_int(v), 'CLIENTES EN MÉXICO (2024)', y=0.16 if not VERT else 0.22, size=70 if not VERT else 84)
    lab(fr, 'Fuente: IFT · mapa aproximado · puntos ilustrativos', 1, dotc=AMBER)


_MXPATH = {}


def _MXP():
    if 'p' not in _MXPATH:
        from matplotlib.path import Path
        _MXPATH['p'] = Path([llm(a, b) for a, b in MEXICO])
    return _MXPATH['p']


def mountain(x, z, r, h, col=(110, 96, 80), snow=False):
    m = cyl(r, h, col, n=9, r2=0.02, shadow=0.35, gloss=0.0)
    return m.tf(t=(x, 0, z))


def s_rancho(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(8.0, wide=True), yaw=-18 + lt * 3, pitch=14)
    for (x, z, r, h) in ((-3.2, -2.2, 1.6, 2.6), (-1.0, -3.0, 1.9, 3.2), (1.8, -2.6, 1.7, 2.4), (3.8, -1.8, 1.3, 1.8)):
        fr.meshes.append(mountain(x, z, r, h, (96, 110, 80)))
    fr.meshes += house(-0.4, 0.4, s=0.8, col=(196, 150, 100))
    fr.meshes.append(box(1.2, 0.5, 0.04, (130, 96, 60), shadow=0.2).tf(t=(1.3, 0, 1.0)))  # cerca

    def fiber(d, cam):
        line3(d, cam, [(6, 0.03, 1.4), (3.2, 0.03, 1.2)], AMBER, 3.0)
        line3(d, cam, [(3.0, 0.03, 1.15), (2.6, 0.03, 1.1)], AMBER, 1.4, dash=3)
    fr.under.append(fiber)
    sp = (-1.0, 4.2, -1.4)
    fr.meshes += sat_at(sp, s=0.45, ry=20)
    beam(fr, (-0.64, 1.0, 0.4), sp, CYAN, 3.0, k=clamp((lt - 0.4) / 1.0))
    ui_label3(fr, (3.2, 0.05, 1.2), 'Aquí se acaba la fibra', None, a=clamp(lt / 0.6), side=1, length=60, up=50)
    head(fr, ['En el rancho,', 'la única opción.'], CYAN, t, t0 + 0.1, kicker='Donde no llega la fibra')
    lab(fr, 'Recreación', 1, dotc=AMBER)


def s_city(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(7.6, wide=True), yaw=-14 + lt * 3, pitch=20)
    rng = np.random.RandomState(6)
    for i in range(14):
        x = -3.5 + (i % 7) * 1.15
        z = -1.2 + (i // 7) * 1.4
        h = rng.uniform(0.8, 2.8)
        c = [(200, 196, 188), (160, 170, 186), (214, 200, 170)][i % 3]
        fr.meshes.append(box(0.8, h, 0.8, c, cols={'top': (150, 150, 156)}, shadow=0.35).tf(t=(x, 0, z)))

    def fib(d, cam, lt=lt):
        for z in (-0.5, 0.9):
            line3(d, cam, [(-5, 0.03, z), (5, 0.03, z)], AMBER, 3.0)
            q = ((lt * 1.2) % 1.0) * 10 - 5
            dot3(d, cam, (q, 0.05, z), 7, (255, 255, 255))
    fr.under.append(fib)
    head(fr, ['En la ciudad,', 'gana la fibra.'], AMBER, t, t0 + 0.1, kicker='Suele ser más barata y rápida')
    lab(fr, 'Recreación', 1, dotc=AMBER)


# ================================================================== CIERRE (c6)
def s_recap(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.4, wide=True), yaw=-10 + lt * 3, pitch=12)
    ks = [T(('c6', 0, 'antena'), default=t0), T(('c6', 0, 'láseres'), default=t0 + 1.5), T(('c6', 0, 'miles'), default=t0 + 3)]
    k0, k1, k2 = [eback((t - k) / 0.5) for k in ks]
    if k0 > 0:
        fr.meshes += dish(-2.8, 0, 0, ry=-10, s=1.2 * max(0.05, k0))
    if k1 > 0:
        fr.meshes += sat_at((-0.5, 1.2, 0), s=0.35 * k1, ry=90)
        fr.meshes += sat_at((0.9, 1.2, 0), s=0.35 * k1, ry=90)
        beam(fr, (-0.5, 1.2, 0), (0.9, 1.2, 0), LASER, 3, k=k1)
    if k2 > 0:
        fr.meshes += sat_at((2.6, 0.9, 0.2), s=0.3 * k2, ry=30)
        fr.meshes += sat_at((3.2, 1.6, -0.3), s=0.3 * k2, ry=-30)
    head(fr, ['Todo eso…'], CYAN, t, t0 + 0.1, kicker='Starlink por dentro')


def s_hand(fr, t, lt, dur):
    t0 = t - lt
    fr.cam = Cam(target=(0, 1.4, 0), dist=vfit(5.4) - lt * 0.3, yaw=14 - lt * 4, pitch=10)
    fr.meshes += phone_m(0, 1.0, 0.4, rx=72, s=1.4, scr=screen_video())
    # mano (palma simple)
    fr.meshes.append(rbox(0.9, 0.25, 0.9, 0.2, (198, 150, 116), gloss=0.2, shadow=0.35, base=False).tf(rx=72, t=(0, 0.6, 0.2)))
    sp = (-1.4, 4.0, -2.0)
    fr.meshes += sat_at(sp, s=0.5, ry=20)
    beam(fr, sp, (0, 1.3, 0.4), CYAN, 3.0, k=clamp(lt / 0.8), pulse=(lt * 0.9) % 1)
    head(fr, ['…para que llegue', 'a tu mano.'], CYAN, t, t0 + 0.1)


def s_brand(fr, t, lt, dur):
    S.s_marca(fr, t, lt, dur)


def s_brand_out(fr, t, lt, dur):
    S.s_marca(fr, t, lt, dur, sub='Las 5 partes completas en el canal')


def s_question(fr, t, lt, dur, share=False):
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(7.0), yaw=-6 + lt * 3, pitch=16)
    fr.meshes.append(earth(1.4, lon0=-100, lat_tilt=20, spin=lt * 10))
    pts = shell_points(80, 1.75, (0, 0, 0), t, seed=2, speed=0.15, planes=10)
    draw_shell(fr, pts, (0, 0, 0), 1.4, ICE, 2.4)

    def f(img, d, lt=lt):
        y = H * (0.70 if not VERT else 0.66)
        k = ease(lt / 0.5)
        pill(img, d, W / 2 - (130 if not VERT else 170), y, '  SÍ  ', k, size=40 if not VERT else 54, dotc=LGREEN)
        pill(img, d, W / 2 + (130 if not VERT else 170), y, '  NO  ', k, size=40 if not VERT else 54, dotc=LASER)
    fr.ui.append(f)
    if share:
        head(fr, ['Mándaselo a alguien', 'de rancho.'], CYAN, t, t0 + 0.1, kicker='¿Lo contratarías?')
    else:
        head(fr, ['¿Internet que', 'viene del espacio?'], CYAN, t, t0 + 0.1, kicker='Tú qué dices')


def s_share(fr, t, lt, dur):
    s_question(fr, t, lt, dur, share=True)


def s_loop(fr, t, lt, dur):
    s_hook(fr, t, lt, dur, loop=True)


CARDS = {'c1': ('PARTE 1', 'EL VIAJE DE TU SEÑAL', 'line'),
         'c2': ('PARTE 2', 'LA ANTENA POR DENTRO', 'rings'),
         'c3': ('PARTE 3', 'LÁSERES EN EL VACÍO', 'line'),
         'c4': ('PARTE 4', 'CÓMO NO CHOCAN', 'error'),
         'c5': ('PARTE 5', 'CUÁNTO CUESTA EN MÉXICO', 'ruler', (1050, 'pesos al mes'))}

SHOTS = [(('c0', 0), s_hook), (('c0', 1), s_phone), (('c0', 2), s_speed), (('c0', 3), s_lap), (('c0', 4), s_blink),
         (('c0', 5), s_five),
         (('card', 'c1'), None), (('c1', 1), s_house), (('c1', 2), s_up), (('c1', 3), s_scale), (('c1', 4), s_bounce),
         (('c1', 5), s_internet), (('c1', 6), s_light), (('c1', 7), s_latency), (('c1', 8), s_geo), (('c1', 9), s_lag),
         (('card', 'c2'), None), (('c2', 1), s_plate), (('c2', 2), s_xray), (('c2', 3), s_loteria), (('c2', 4), s_phase),
         (('c2', 5), s_track), (('c2', 6), s_handoff), (('c2', 7), s_jet),
         (('card', 'c3'), None), (('c3', 1), s_lasers), (('c3', 2), s_mesh), (('c3', 3), s_gbps), (('c3', 4), s_far),
         (('c3', 5), s_ocean), (('c3', 6), s_42), (('c3', 7), s_movies),
         (('card', 'c4'), None), (('c4', 1), s_dodge), (('c4', 2), s_tally), (('c4', 3), s_odds), (('c4', 4), s_still),
         (('c4', 5), s_lower), (('c4', 6), s_debris), (('c4', 7), s_burn),
         (('card', 'c5'), None), (('c5', 1), s_cost), (('c5', 2), s_plan), (('c5', 3), s_kit), (('c5', 4), s_tax),
         (('c5', 5), s_clients), (('c5', 6), s_rancho), (('c5', 7), s_city),
         (('c6', 0), s_recap), (('c6', 1), s_hand), (('c6', 2), s_brand), (('c6', 3), s_question), (('c6', 4), s_loop),
         (('out', 0), s_brand_out), (('out', 1), s_share)]

if __name__ == '__main__':
    S.main(SHOTS, CARDS)
