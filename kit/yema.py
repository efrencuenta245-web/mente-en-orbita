"""Reel diario: Lo que no ves — la yema de tu huevo y el cempasúchil (28-oct-2026). Tema visual: orbita.
Escenas: huevo estrellado en un comal (gancho) · rayos X del huevo · gallina que no fabrica el color · pétalos al alimento ·
luteína 90 % · del alimento a la sangre y a la yema · abanico de 16 tonos · yema pálida vs naranja · 410 huevos al año ·
ofrenda · 20 pétalos (cempoalxóchitl) · cierre Sí/No · loop al huevo.
Uso: MOTOR_TEMA=orbita GTA_FMT=v VIDEO_TL=/home/claude/tl_yema.json python3 yema.py info|preview T out.png|sheet out.jpg t..|chunk A B out.mp4"""
import os
os.environ.setdefault('MOTOR_TEMA', 'orbita')
os.environ.setdefault('GTA_FMT', 'v')
os.environ.setdefault('VIDEO_TL', '/home/claude/tl_yema.json')
import math
import numpy as np
import escenas as S
from PIL import ImageDraw
import entornos as EN
from escenas import *  # noqa: F401,F403
from starlink import scan_ring, lab, bigc, cnt, CYAN, ICE, LASER, LGREEN, AMBER, PINK, CREAM, WHITE

YOLK = (250, 160, 20)
YOLK_D = (236, 120, 10)
PALE = (246, 228, 160)
ALB = (250, 248, 242)
SHELL = (222, 186, 140)
MARI = (246, 128, 14)
MARI2 = (255, 176, 36)
STEM = (60, 120, 50)
WOOD = (140, 92, 56)
WOOD2 = (120, 78, 46)
COMAL = (54, 54, 58)
HEN = (176, 86, 44)
HEN2 = (140, 62, 32)
COMB = (210, 36, 40)
BEAK = (236, 180, 60)
BLOOD = (200, 36, 46)
PAPEL = (220, 40, 130)
CANDLE = (244, 236, 214)


def table(w=6.0, d=4.0, y=-0.12):
    def cols(*a):
        return None
    return box(w * 1.3, 0.12, d * 1.3, WOOD, cols={'top': WOOD}, shadow=0.0, base=True, edge=False).tf(t=(0, y, 0))


def fried_egg(s=1.0, yc=YOLK, wob=0.0, x=0.0, z=0.0, y=0.0):
    """Huevo estrellado: clara de orilla irregular con borde dorado + yema brillante con reflejo."""
    def cw(i, j):
        return (232, 196, 130) if j == 4 else (ALB if j < 4 else (238, 232, 220))
    w = sphere(1.0, ALB, nu=56, nv=10, shadow=0.35, gloss=0.55, cols=cw)
    V = np.array(w.V, float)
    th = np.arctan2(V[:, 2], V[:, 0])
    f = 1 + 0.10 * np.sin(3 * th + 0.5) + 0.06 * np.sin(5 * th + 2.0) + 0.035 * np.sin(9 * th + 1.0)
    V[:, 0] *= f
    V[:, 2] *= f
    w.V = V
    w = w.tf(s=(1.0 * s, 0.05 * s, 0.82 * s), t=(x, y + 0.05 * s, z))
    w.sh_r = 1.0 * s
    yy = sphere(1.0, yc, nu=40, nv=20, shadow=0.0, gloss=0.95).tf(
        s=(0.36 * s * (1 + 0.04 * wob), 0.2 * s * (1 - 0.06 * wob), 0.36 * s * (1 + 0.04 * wob)), t=(x + 0.1 * s, y + 0.09 * s, z - 0.05 * s))
    hl = sphere(1.0, (255, 250, 230), nu=10, nv=6, shadow=0, gloss=1.0).tf(s=(0.08 * s, 0.03 * s, 0.05 * s), t=(x + 0.02 * s, y + 0.27 * s, z - 0.12 * s))
    return [w, yy, hl]


def comal_under(fr, r=1.5, x=0.0):
    def f(d, cam):
        if not isinstance(d, ImageDraw.ImageDraw):
            return
        P = np.array([(x + r * math.cos(a), 0.005, r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 60)])
        s, z = cam.proj(P)
        d.polygon([tuple(p) for p in s], fill=COMAL)
        d.line([tuple(p) for p in s] + [tuple(s[0])], fill=(84, 84, 90), width=4)
    fr.under.append(f)


def comal(r=1.5):
    return []


def egg(s=1.0, a=1.0, x=0.0, y=0.0, z=0.0, col=SHELL):
    m = sphere(1.0, col, nu=40, nv=24, shadow=0.35, gloss=0.45).tf(s=(0.62 * s, 0.82 * s, 0.62 * s), t=(x, y + 0.82 * s, z))
    m.alpha = a
    m.sh_r = 0.6 * s
    return m


def flower(s=1.0, x=0.0, y=0.0, z=0.0, ry=0.0, open_=1.0, rich=True, stem=0.0):
    """Flor de cempasúchil: pompón de pétalos ondulados en capas (recreación)."""
    out = []
    if rich:
        out.append(sphere(0.15, MARI, nu=14, nv=9, shadow=0, gloss=0.3).tf(s=(1, 0.9, 1), t=(0, 0.16, 0)))
        rings = ((16, 0.40, 8, MARI2), (14, 0.33, 25, (250, 150, 24)), (12, 0.26, 42, MARI), (10, 0.19, 58, MARI2), (8, 0.12, 72, MARI), (6, 0.06, 84, (236, 110, 10)))
        for r_i, (n, rr, tilt, col) in enumerate(rings):
            for i in range(n):
                th = 360 * i / n + r_i * 17
                ruf = 12 * math.sin(i * 2.7 + r_i)
                p = sphere(0.1, col, nu=10, nv=6, shadow=0, gloss=0.3).tf(s=(1.3, 0.28, 0.85))
                p = p.tf(rx=ruf, rz=tilt * open_).tf(t=(rr * open_, 0.06 + (0.40 - rr) * 0.32, 0)).tf(ry=th)
                out.append(p)
        out.append(cyl(0.16, 0.08, STEM, n=12, r2=0.06, shadow=0).tf(t=(0, -0.02, 0)))
    else:
        def cc(i, j):
            v = math.sin(i * 2.1 + j * 1.3) * math.sin(i * 1.1 - j * 2.7)
            return MARI if v > 0.2 else (MARI2 if v > -0.4 else (236, 110, 10))
        out.append(sphere(0.38, MARI2, nu=22, nv=12, shadow=0.0, gloss=0.2, cols=cc).tf(s=(1, 0.72, 1), t=(0, 0.2, 0)))
    if stem > 0:
        out.append(cyl(0.03, stem, STEM, n=6, shadow=0).tf(t=(0, -stem, 0)))
        for sg in (-1, 1):
            out.append(sphere(0.12, (70, 140, 60), nu=8, nv=5, shadow=0).tf(s=(1.4, 0.15, 0.5), rz=sg * 25, t=(sg * 0.14, -stem * 0.55, 0)))
    return [m.tf(s=s).tf(ry=ry).tf(t=(x, y, z)) for m in out]


def hen(x=0.0, z=0.0, ry=0.0, s=1.0, peck=0.0):
    """Gallina (recreación): cuerpo, ala, cola de plumas, cresta, barbilla, pico y patas con dedos."""
    ms = []
    def body_c(i, j):
        return HEN if (i + j) % 5 else (196, 104, 56)
    ms.append(sphere(1.0, HEN, nu=30, nv=18, shadow=0.0, gloss=0.35, cols=body_c).tf(s=(0.62, 0.5, 0.45), t=(0, 0.74, 0)))
    ms.append(sphere(1.0, (196, 112, 60), nu=20, nv=12, shadow=0.0, gloss=0.3).tf(s=(0.36, 0.3, 0.38), t=(0.2, 0.62, 0)))
    for sz in (-1, 1):
        ms.append(sphere(1.0, HEN2, nu=18, nv=10, shadow=0, gloss=0.35).tf(s=(0.42, 0.24, 0.08), rz=-12, t=(-0.05, 0.8, sz * 0.43)))
    for k in range(6):
        ang = 25 + k * 14
        c = (40, 52, 46) if k % 2 else (26, 34, 30)
        ms.append(sphere(1.0, c, nu=12, nv=6, shadow=0, gloss=0.7).tf(s=(0.34, 0.07, 0.12), rz=ang, t=(-0.62, 1.0 + 0.04 * k, (k - 2.5) * 0.05)))
    hx, hy = 0.52 + 0.18 * peck, 1.24 - 0.5 * peck
    ms.append(cyl(0.15, 0.42, HEN, n=14, r2=0.11, shadow=0).tf(rz=-30 - 50 * peck, t=(0.36, 0.86, 0)))
    ms.append(sphere(0.18, (190, 98, 50), nu=18, nv=12, shadow=0, gloss=0.35).tf(s=(1.1, 1, 0.9), t=(hx, hy, 0)))
    for k in range(5):
        r = 0.05 + 0.02 * (k % 2)
        ms.append(sphere(r, COMB, nu=10, nv=7, shadow=0, gloss=0.5).tf(s=(0.9, 1.3, 0.5), t=(hx - 0.1 + k * 0.05, hy + 0.18 + 0.02 * (k % 2), 0)))
    for sz in (-0.03, 0.03):
        ms.append(sphere(0.05, COMB, nu=10, nv=7, shadow=0, gloss=0.5).tf(s=(0.7, 1.5, 0.5), t=(hx + 0.1, hy - 0.17, sz)))
    ms.append(cyl(0.055, 0.15, BEAK, n=10, r2=0.0, shadow=0, gloss=0.5).tf(rz=-90 - 30 * peck, t=(hx + 0.15, hy - 0.02, 0)))
    for sz in (-0.13, 0.13):
        ms.append(sphere(0.035, (250, 200, 60), nu=8, nv=6, shadow=0).tf(t=(hx + 0.08, hy + 0.05, sz * 0.95)))
        ms.append(sphere(0.02, (15, 15, 15), nu=6, nv=4, shadow=0, gloss=0.9).tf(t=(hx + 0.095, hy + 0.05, sz * 1.08)))
        ms.append(cyl(0.028, 0.32, BEAK, n=8, shadow=0).tf(t=(0.05, 0.0, sz)))
        for a in (-35, 0, 35):
            ms.append(cyl(0.015, 0.13, BEAK, n=6, shadow=0).tf(rz=-90, ry=a, t=(0.05, 0.01, sz)))
    out = [m.tf(s=s).tf(ry=ry).tf(t=(x, 0, z)) for m in ms]
    out[0].shadow = 0.35
    out[0].sh_r = 0.5 * s
    return out


def wood_floor(fr, f=0.5, name='cocina'):
    EN.env(fr, name)


# ================================================================== escenas
def s_hook(fr, t, lt, dur, loop=False):
    """El huevo cae al comal y se estrella; la yema tiembla y junto aparece una flor de cempasúchil."""
    t0 = t - lt
    wood_floor(fr)
    fr.cam = Cam(target=(0, 0.25, 0), dist=vfit(4.6) - lt * 0.18, yaw=-25 + lt * 7, pitch=40 - lt * 1.5)
    comal_under(fr)
    k = clamp(lt / 0.55)
    if k < 1 and not loop:
        # el huevo cae y se abre en el primer medio segundo (acción inmediata)
        y = lerp(2.4, 0.1, ease(k))
        fr.meshes.append(egg(0.6, x=0.1, y=y, z=-0.05).tf(rz=20 * k))
    else:
        kk = clamp((lt - 0.55) / 0.35) if not loop else 1.0
        wob = math.sin(lt * 14) * math.exp(-max(0, lt - 0.55) * 2.2) * 3
        for m in fried_egg(lerp(0.4, 1.0, eout(kk)), wob=wob, y=0.06):
            fr.meshes.append(m)
    if lt > 1.6 or loop:
        a = appear(t, t0 + 1.6) if not loop else 1.0
        fr.meshes += flower(0.9 * a, x=1.55, y=0.0, z=0.7, ry=lt * 20)
        fr.meshes += flower(0.7 * a, x=-1.6, y=0.0, z=0.9, ry=-lt * 15, rich=False)
        if not loop:
            fr.over.append(lambda d, cam: line3(d, cam, [(1.45, 0.45, 0.65), (0.25, 0.35, -0.05)], AMBER, 2.4, dash=10, a=a))
    if not loop:
        head(fr, ['Mira la yema', 'de tu huevo.'], CYAN, t, t0 + 0.05, kicker='Lo que no ves')
    else:
        head(fr, ['Mira la yema', 'de tu huevo.'], CYAN, t, t0 + 0.05, kicker='La próxima vez…')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_xray(fr, t, lt, dur):
    """Escáner de rayos X sobre un huevo entero: cascarón transparente, clara y yema llena de gotitas de pigmento."""
    t0 = t - lt
    wood_floor(fr, name='laboratorio')
    fr.cam = Cam(target=(0, 0.85, 0), dist=vfit(4.4), yaw=-20 + lt * 10, pitch=12)
    ts, te = t0 + 0.15, t0 + 1.3
    ys, k = scan_ring(fr, t, ts, te, 1.75, 0.0, center=(0, 0, 0), r=0.85)
    e = ease(k)
    if e < 0.98:
        fr.meshes.append(egg(1.0, a=1 - e))
    if k > 0.05:
        fr.under.append(lambda d, cam, e=e: [ring3(d, cam, (0, 0.82, 0), 0.62 * sc, ICE, 2.0, e * 0.7, axis='z') for sc in (1.0,)])
        fr.meshes.append(sphere(0.3, YOLK, nu=22, nv=14, shadow=0, gloss=0.8).tf(t=(0, 0.72, 0)))
        rng = np.random.RandomState(3)
        pts = rng.normal(0, 1, (90, 3))
        pts = pts / np.linalg.norm(pts, axis=1, keepdims=True) * rng.uniform(0.05, 0.33, (90, 1))

        def drops(d, cam, e=e):
            for i, p in enumerate(pts):
                if i / 90 < e:
                    q = p + (0, 0.72, 0)
                    q = (q[0] + 0.02 * math.sin(lt * 3 + i), q[1], q[2])
                    dot3(d, cam, q, 3.4, (255, 120, 0), 0.9)
        fr.over.append(drops)
        ui_label3(fr, (0.3, 0.72, 0), 'Yema', a=clamp((lt - 1.2) / 0.4), side=1, length=120, up=140)
        ui_label3(fr, (-0.2, 0.62, 0), 'Pigmento', sub='luteína', a=clamp((lt - 1.6) / 0.4), side=-1, length=100, up=-160)
    head(fr, ['Así se ve', 'por dentro.'], CYAN, t, t0 + 0.1, kicker='Rayos X')
    lab(fr, 'Recreación · Esquema simplificado', clamp(lt / 0.4))


def s_hen(fr, t, lt, dur):
    """La gallina come: su cuerpo no puede fabricar el color, lo saca del alimento."""
    t0 = t - lt
    wood_floor(fr, name='granja')
    fr.cam = Cam(target=(0.2, 0.7, 0), dist=vfit(4.6), yaw=10 + lt * 5, pitch=10)
    peck = max(0.0, math.sin(lt * 5)) ** 3
    fr.meshes += hen(-0.2, 0, s=1.0, peck=peck)
    fr.meshes.append(cyl(0.55, 0.16, (180, 120, 70), n=24, shadow=0.3, gloss=0.2).tf(t=(1.05, 0, 0)))
    rng = np.random.RandomState(5)
    gr = rng.uniform(-1, 1, (60, 2))
    fr.over.append(lambda d, cam: [dot3(d, cam, (1.05 + 0.45 * u, 0.17, 0.45 * v), 3.2, MARI if i % 3 else (230, 200, 110), 0.95)
                                   for i, (u, v) in enumerate(gr) if u * u + v * v < 1])

    def f(img, d, lt=lt):
        k = ease(clamp((lt - 1.2) / 0.4))
        if k > 0:
            pill(img, d, W / 2, H * 0.62, '  NO LO FABRICA  ', k, size=50, dotc=LASER)
    fr.ui.append(f)
    head(fr, ['La gallina no', 'fabrica ese color.'], CYAN, t, t0 + 0.1, kicker='Lo saca de lo que come')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_feed(fr, t, lt, dur):
    """Pétalos de cempasúchil que se secan, se muelen y caen como polvo naranja al alimento."""
    t0 = t - lt
    wood_floor(fr, name='granja')
    fr.cam = Cam(target=(0, 0.7, 0), dist=vfit(4.8), yaw=-30 + lt * 8, pitch=20)
    for i, (x, z) in enumerate(((-1.4, -0.6), (-0.9, 0.5), (-1.7, 0.3))):
        fr.meshes += flower(0.8, x=x, y=0.9, z=z, ry=lt * 15 + i * 40, stem=0.9, rich=(i == 0))
    # costal / tolva con alimento
    fr.meshes.append(cyl(0.7, 0.5, (196, 160, 110), n=28, r2=0.8, shadow=0.3, gloss=0.1).tf(t=(1.0, 0, 0)))
    fr.meshes.append(cyl(0.74, 0.02, (226, 196, 120), n=28, shadow=0, y0=0.5).tf(t=(1.0, 0, 0)))
    k = clamp((lt - 0.5) / 3.0)
    rng = np.random.RandomState(8)
    P = rng.uniform(0, 1, (120, 3))

    def powder(d, cam, lt=lt, k=k):
        for i, (u, v, w) in enumerate(P):
            ph = (lt * 0.6 + u) % 1.0
            x = lerp(-0.9, 1.0 + (v - 0.5) * 0.8, ph)
            y = 1.4 + 0.5 * math.sin(math.pi * ph) - ph * 0.9
            dot3(d, cam, (x, y, (w - 0.5) * 0.8), 3.6, MARI if i % 2 else MARI2, 0.9 * k)
        for i in range(int(80 * k)):
            u, v = P[i, 0] * 2 - 1, P[i, 1] * 2 - 1
            dot3(d, cam, (1.0 + 0.6 * u, 0.53, 0.6 * v), 3.0, MARI, 0.9)
    fr.over.append(powder)
    ui_label3(fr, (1.0, 0.55, 0), 'Alimento', a=clamp((lt - 1.0) / 0.4), side=1, length=80, up=200)
    head(fr, ['Polvo de pétalos', 'en su alimento.'], CYAN, t, t0 + 0.1, kicker='Cempasúchil')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_lutein(fr, t, lt, dur):
    """Acercamiento a una flor: la luteína es hasta el 90 % de su color."""
    t0 = t - lt
    wood_floor(fr, name='campo')
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(2.6) - lt * 0.1, yaw=lt * 14, pitch=48)
    fr.meshes += flower(1.6, y=0.0, ry=lt * 6)
    v = cnt(90, t, t0 + 0.6, 1.8)
    bigc(fr, f'{v:.0f} %', 'DEL COLOR DE LA FLOR ES LUTEÍNA', y=0.235 if VERT else 0.3, size=110)

    def mol(d, cam, lt=lt):
        k = clamp((lt - 1.0) / 1.2)
        n = int(18 * k)
        pts = [(-1.0 + i * 0.12, 1.15 + (0.06 if i % 2 else -0.06), 0.0) for i in range(n)]
        if len(pts) > 1:
            line3(d, cam, pts, AMBER, 3.0)
        for p in pts:
            dot3(d, cam, p, 4, AMBER)
    ui_label3(fr, (0.3, 0.35, 0.3), 'Luteína', a=clamp((lt - 1.0) / 0.4), side=1, length=120, up=200)
    head(fr, ['Se llama', 'luteína.'], CYAN, t, t0 + 0.1, kicker='El pigmento')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_blood(fr, t, lt, dur):
    """Del alimento a la sangre: un vaso con glóbulos rojos y gotitas doradas que llegan a la yema y la llenan."""
    t0 = t - lt
    wood_floor(fr, name='cuerpo')
    fr.cam = Cam(target=(0.0, 0.6, 0), dist=vfit(5.8), yaw=-8 + lt * 4, pitch=14)
    tube = cyl(0.32, 3.1, (226, 120, 120), n=24, shadow=0, gloss=0.5).tf(rz=-90, t=(-2.0, 0.6, 0))
    tube.alpha = 0.32
    fr.meshes.append(tube)
    k = ease(clamp((lt - 0.4) / 3.2))
    yr = lerp(0.25, 0.48, k)
    yc = mix(PALE, YOLK, k)
    fr.meshes.append(sphere(yr, yc, nu=24, nv=14, shadow=0, gloss=0.85).tf(t=(1.35, 0.6, 0)))
    for j in range(7):
        u = (lt * 0.35 + j / 7) % 1
        fr.meshes.append(sphere(0.09, BLOOD, nu=10, nv=6, shadow=0, gloss=0.6).tf(s=(1, 0.45, 1), rx=60 * j,
                                                                                 t=(-2.0 + 3.4 * u, 0.6 + 0.15 * math.sin(j * 2.3), 0.12 * math.cos(j))))
    rng = np.random.RandomState(2)
    G = rng.uniform(0, 1, (40, 3))

    def gold(d, cam, lt=lt):
        for i, (u, v, w) in enumerate(G):
            ph = (lt * 0.45 + u) % 1
            x = -2.0 + 3.4 * ph
            if x > 1.35:
                continue
            dot3(d, cam, (x, 0.6 + (v - 0.5) * 0.4, (w - 0.5) * 0.4), 4.0, (255, 150, 0), 0.95)
    fr.over.append(gold)
    ui_label3(fr, (-1.2, 0.95, 0), 'Sangre', a=clamp((lt - 0.6) / 0.4), side=-1, length=70, up=160)
    ui_label3(fr, (1.35, 0.6 + yr, 0), 'Yema', sub='grasa', a=clamp((lt - 1.4) / 0.4), side=1, length=60, up=150)
    head(fr, ['Viaja por la sangre', 'y se guarda en la yema.'], CYAN, t, t0 + 0.1, kicker='Dentro de la gallina')
    lab(fr, 'Recreación · Escala exagerada', clamp(lt / 0.4))


def s_fan(fr, t, lt, dur):
    """Abanico de 16 tonos que se abre; la yema se compara con cada tono."""
    t0 = t - lt
    wood_floor(fr)
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(4.8), yaw=-6 + lt * 3, pitch=6)
    k = ease(clamp((lt - 0.2) / 1.4))
    for i in range(16):
        c = mix(PALE, (236, 92, 10), i / 15)
        ang = lerp(0, -75 + i * 10, k)
        fr.meshes.append(box(0.22, 1.9, 0.02, c, shadow=0, base=True, edge=False, gloss=0.2).tf(rz=ang, t=(0, 0.1, -0.3 + i * 0.002)))
    sel = int(clamp((lt - 1.6) / 2.0) * 13)
    for m in fried_egg(0.5, yc=mix(PALE, (236, 92, 10), sel / 15), x=0.0, z=1.3):
        fr.meshes.append(m)
    bigc(fr, f'{sel + 1}', 'DE 16 TONOS', y=0.235 if VERT else 0.3, size=110)
    head(fr, ['Más luteína,', 'yema más naranja.'], CYAN, t, t0 + 0.1, kicker='Abanico de color')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_pale(fr, t, lt, dur):
    """Dos huevos estrellados: sin pigmento (casi blanca) contra con cempasúchil."""
    t0 = t - lt
    wood_floor(fr)
    fr.cam = Cam(target=(0, 0.1, 0), dist=vfit(5.4) - lt * 0.15, yaw=lt * 5, pitch=50)
    comal_under(fr, 1.1)
    fr.meshes += [m.tf(t=(-1.25, 0, 0)) for m in comal(1.1)][0:0]
    for m in fried_egg(0.75, yc=(246, 234, 196), x=-0.8, z=0.0, y=0.06):
        fr.meshes.append(m)
    for m in fried_egg(0.75, yc=YOLK_D, x=0.8, z=0.0, y=0.06):
        fr.meshes.append(m)
    ui_text3(fr, (-0.8, 0.1, 0.9), 'SIN PIGMENTO', 26, a=clamp((lt - 0.5) / 0.4), col=MUTED, fk='mono')
    ui_text3(fr, (0.8, 0.1, 0.9), 'CON CEMPASÚCHIL', 26, a=clamp((lt - 0.8) / 0.4), col=AMBER, fk='mono')
    head(fr, ['Sin pigmento:', 'casi blanca.'], CYAN, t, t0 + 0.1, kicker='Compara')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_mexico(fr, t, lt, dur):
    """Contador en vivo: 410 huevos por persona al año; una pila de huevos que crece."""
    t0 = t - lt
    wood_floor(fr, name='tienda')
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(5.6), yaw=30 + lt * 6, pitch=26)
    v = cnt(410, t, t0 + 0.3, 2.6)
    n = int(v / 410 * 60)
    for i in range(n):
        lay, r = divmod(i, 15)
        cx, cz = (r % 5 - 2) * 0.42, (r // 5 - 1) * 0.42
        fr.meshes.append(egg(0.24, x=cx + (lay % 2) * 0.2, y=lay * 0.36, z=cz + (lay % 2) * 0.2,
                             col=SHELL if i % 3 else (238, 224, 200)))
    bigc(fr, f'{v:.0f}', 'HUEVOS POR PERSONA AL AÑO', y=0.235 if VERT else 0.3, size=120)

    def f(img, d, lt=lt):
        k = ease(clamp((lt - 2.4) / 0.4))
        if k > 0:
            pill(img, d, W / 2, H * 0.71, '  MÉXICO · N.º 1 DEL MUNDO  ', k, size=46, dotc=LGREEN)
    fr.ui.append(f)
    head(fr, ['Nadie come más', 'huevo que México.'], CYAN, t, t0 + 0.1, kicker='Contador en vivo')
    lab(fr, 'Promedio 2025 · Recreación', clamp(lt / 0.4))


def s_ofrenda(fr, t, lt, dur):
    """Ofrenda de Día de Muertos con cempasúchil, velas y papel picado; un camino de pétalos llega al plato con huevo."""
    t0 = t - lt
    wood_floor(fr, name='ofrenda')
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(6.4) - lt * 0.2, yaw=-18 + lt * 5, pitch=12)
    for i, (w, h, z) in enumerate(((3.6, 0.6, -0.4), (2.8, 0.6, -0.8), (2.0, 0.6, -1.2))):
        fr.meshes.append(box(w, h, 0.9, (236, 236, 240) if i % 2 else (120, 60, 140), shadow=0.3, base=True, edge=False).tf(t=(0, i * 0.6, z)))
    for i in range(7):
        x = -1.5 + i * 0.5
        fr.meshes += flower(0.42, x=x, y=0.6, z=-0.05, ry=i * 50, rich=False)
    for i in range(5):
        x = -1.1 + i * 0.55
        fr.meshes += flower(0.36, x=x, y=1.2, z=-0.45, ry=i * 70, rich=False)
    for x in (-0.7, 0.0, 0.7):
        fr.meshes.append(cyl(0.07, 0.4, CANDLE, n=10, shadow=0, gloss=0.3).tf(t=(x, 1.8, -0.9)))
        fl = 0.04 + 0.01 * math.sin(lt * 20 + x * 9)
        fr.over.append(lambda d, cam, x=x, fl=fl: dot3(d, cam, (x, 2.27, -0.9), 7, (255, 190, 60), 0.95))
    k = clamp((lt - 0.3) / 2.0)
    for i in range(int(22 * k)):
        z = 0.5 + i * 0.12
        fr.over.append(lambda d, cam, z=z, i=i: dot3(d, cam, (0.12 * math.sin(i * 1.3), 0.02, z), 5, MARI, 0.95))
    fr.meshes.append(cyl(0.55, 0.05, (236, 232, 224), n=28, shadow=0.3, gloss=0.5).tf(t=(1.6, 0, 2.2)))
    for m in fried_egg(0.42, x=1.6, z=2.2, y=0.05):
        fr.meshes.append(m)

    def papel(img, d, lt=lt):
        for i in range(9):
            x = W * (0.08 + i * 0.105)
            c = (PAPEL, (250, 140, 20), (60, 150, 220), (130, 60, 180))[i % 4]
            y = H * 0.19 + 6 * math.sin(lt * 2 + i)
            d.polygon([(x - 46, y), (x + 46, y), (x + 46, y + 70), (x, y + 92), (x - 46, y + 70)], fill=c)
    fr.ui.insert(0, papel)
    head(fr, ['La misma flor', 'de tu ofrenda.'], CYAN, t, t0 + 0.1, kicker='Sin saberlo')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_mexica(fr, t, lt, dur):
    """Cempoalxóchitl: flor de veinte pétalos; los pétalos aparecen y se cuentan del 1 al 20."""
    t0 = t - lt
    wood_floor(fr, name='campo')
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(3.4), yaw=lt * 5, pitch=62)
    k = clamp((lt - 0.3) / 2.6)
    n = int(round(20 * k))
    fr.meshes.append(sphere(0.25, MARI, nu=14, nv=8, shadow=0, gloss=0.3).tf(s=(1, 0.6, 1), t=(0, 0.2, 0)))
    for i in range(n):
        th = 360 * i / 20
        rr = 0.55 if i % 2 else 0.42
        p = sphere(0.18, MARI2 if i % 2 else MARI, nu=10, nv=6, shadow=0, gloss=0.3).tf(s=(1.5, 0.3, 0.8)).tf(rz=15).tf(t=(rr, 0.18, 0)).tf(ry=th)
        fr.meshes.append(p)
    bigc(fr, f'{n}', 'PÉTALOS · CEMPOALXÓCHITL', y=0.235 if VERT else 0.3, size=110)
    head(fr, ['Flor de', 'veinte pétalos.'], CYAN, t, t0 + 0.1, kicker='En náhuatl')
    lab(fr, 'Recreación · Nombre en náhuatl', clamp(lt / 0.4))


def s_share(fr, t, lt, dur):
    """Cierre: sello, Sí/No y la flor que gira junto al huevo."""
    t0 = t - lt
    wood_floor(fr)
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(4.8), yaw=-20 + lt * 6, pitch=34)
    comal_under(fr)
    for m in fried_egg(0.9, y=0.06):
        fr.meshes.append(m)
    fr.meshes += flower(0.9, x=1.5, z=0.7, ry=lt * 20)

    def f(img, d, lt=lt):
        yy = H * 0.66
        a = ease(clamp((lt - 1.2) / 0.4))
        pill(img, d, W / 2 - 170, yy, '  SÍ  ', a, size=54, dotc=LGREEN)
        pill(img, d, W / 2 + 170, yy, '  NO  ', a, size=54, dotc=LASER)
        draw_text(d, (W / 2, H * 0.205), 'MENTE EN ÓRBITA', font('mono', 60), INK, 'mm', a=ease(clamp(lt / 0.5)), spacing=5)
    fr.ui.append(f)
    head(fr, ['Mándaselo a quien', 'pone la ofrenda.'], CYAN, t, t0 + 0.1, kicker='¿Lo sabías?')


def s_loop(fr, t, lt, dur):
    s_hook(fr, t, lt, dur, loop=True)


SHOTS = [(('c0', 0), s_hook), (('c0', 1), s_xray), (('c0', 2), s_hen), (('c0', 3), s_feed), (('c0', 4), s_lutein),
         (('c0', 5), s_blood), (('c0', 6), s_fan), (('c0', 7), s_pale), (('c0', 8), s_mexico), (('c0', 9), s_ofrenda),
         (('c0', 10), s_mexica), (('c0', 11), s_share), (('c0', 12), s_loop)]

if __name__ == '__main__':
    S.main(SHOTS, {})
