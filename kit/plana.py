"""Reel extra: ¿Qué pasaría si la Tierra fuera plana? (serie "¿Qué pasaría si…?", 28-oct-2026). Tema visual: orbita.
Escenas: tortilla que se vuelve la Tierra plana (gancho) · escáner de rayos X del disco · flechas de gravedad hacia el centro ·
personas inclinadas · cuesta sin fin · agua y aire juntos en el centro (plato con salsa) · Everest y contador de aire ·
hipótesis · gen EPAS1 · humanos de la orilla vs del centro · pueblo mexicano bajo el aire denso · el disco se aplasta en bola ·
cierre Sí/No y loop (la bola vuelve a ser tortilla).
Uso: MOTOR_TEMA=orbita GTA_FMT=v VIDEO_TL=/home/claude/tl_plana.json python3 plana.py info|preview T out.png|sheet out.jpg t..|chunk A B out.mp4"""
import os
os.environ.setdefault('MOTOR_TEMA', 'orbita')
os.environ.setdefault('GTA_FMT', 'v')
os.environ.setdefault('VIDEO_TL', '/home/claude/tl_plana.json')
import math
import numpy as np
import escenas as S
from escenas import *  # noqa: F401,F403
from motor3d import merge
from starlink import earth, atmo, scan_ring, lab, bigc, house, CYAN, ICE, LASER, LGREEN, AMBER, PINK, TERRA, CREAM, WHITE

TORT = (226, 196, 140)
TOAST = (170, 120, 70)
SKIN = (196, 140, 104)
SHIRT = (60, 110, 190)
PANTS = (44, 48, 64)
CRUST = (120, 92, 70)
MANTLE = (214, 104, 44)
CORE = (255, 196, 80)
WATER = (40, 110, 200)
SALSA = (190, 40, 30)
PLATE = (236, 232, 224)
ROCK = (110, 104, 100)
SNOW = (236, 240, 246)

R = 2.0      # radio del disco
TH_ = 0.06   # medio grosor visual del disco (escala exagerada cuando hace falta)


def tortilla(r=R, a=1.0):
    def cols(i, j):
        v = math.sin(i * 1.7 + j * 2.3) * math.sin(i * 0.9 - j * 3.1)
        return mix(TORT, TOAST, 0.75) if v > 0.72 else TORT
    m = sphere(1.0, TORT, nu=40, nv=20, shadow=0.4, gloss=0.1, cols=cols).tf(s=(r, 0.035, r))
    m.alpha = a
    m.sh_r = r
    return m


def flat_earth(r=R, f=TH_, spin=0.0, a=1.0, y=0.0):
    m = earth(1.0, lon0=-100, lat_tilt=0, spin=spin).tf(s=(r, f, r), t=(0, y, 0))
    m.alpha = a
    m.sh_r = r
    return m


def person(x=0.0, z=0.0, y=0.0, lean=0.0, ry=0.0, s=1.0, legs=1.0, wide=1.0, shirt=SHIRT, face=0.0):
    """Persona sencilla (recreación): piernas, torso, brazos y cabeza. lean inclina desde los pies (grados, eje z)."""
    L = 0.42 * legs
    ms = []
    for sg in (-1, 1):
        ms.append(cyl(0.055 * wide, L, PANTS, n=10, shadow=0.0).tf(t=(sg * 0.07 * wide, 0, 0)))
        ms.append(cyl(0.04, 0.36, SKIN, n=8, shadow=0.0).tf(rz=sg * 12, t=(sg * 0.2 * wide, L + 0.06, 0)))
    ms.append(rbox(0.32 * wide, 0.44, 0.2, 0.06, shirt, shadow=0.0, base=True, gloss=0.2).tf(t=(0, L, 0)))
    ms.append(sphere(0.12, SKIN, nu=14, nv=10, shadow=0.0, gloss=0.3).tf(t=(0, L + 0.58, 0)))
    out = []
    for m in ms:
        mm = m.tf(s=s).tf(rz=lean, ry=ry).tf(t=(x, y, z))
        out.append(mm)
    out[0].shadow = 0.35
    out[0].sh_r = 0.25 * s
    return out


def arrow3(fr, p, v, col, w=3.0, a=1.0, layer='over'):
    """Flecha 3D de p en la dirección v."""
    p, v = np.array(p, float), np.array(v, float)
    q = p + v
    n = v / (np.linalg.norm(v) + 1e-9)
    side = np.cross(n, (0, 0, 1.0))
    if np.linalg.norm(side) < 1e-3:
        side = np.cross(n, (1.0, 0, 0))
    side = side / np.linalg.norm(side) * np.linalg.norm(v) * 0.22
    h = q - n * np.linalg.norm(v) * 0.3

    def f(d, cam):
        line3(d, cam, [p, q], col, w, a=a)
        line3(d, cam, [h + side, q, h - side], col, w, a=a)
    (fr.over if layer == 'over' else fr.under).append(f)


def gdir(x, z, y=0.0, thick=0.55):
    """Dirección de la gravedad en (x, y, z) sobre el disco: hacia el centro de masa (escala exagerada del grosor)."""
    v = np.array([-x, -(thick + y), -z])
    return v / np.linalg.norm(v)


def lean_at(x, thick=1.3):
    """Ángulo con el que te pararías (siguiendo la gravedad) a la distancia x del centro."""
    return math.degrees(math.atan2(x, thick))


# ================================================================== escenas
def s_hook(fr, t, lt, dur, loop=False):
    """Una tortilla gira y se vuelve la Tierra plana; una persona en la orilla se ladea."""
    t0 = t - lt
    fr.floor = 0.6
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(6.8) - lt * 0.25, yaw=-20 + lt * 9, pitch=34 + lt * 1.5)
    k = clamp((lt - 1.6) / 1.2)
    y = 0.35 + 0.05 * math.sin(lt * 3)
    flip = 180 * k  # la tortilla da media vuelta y del otro lado aparece la Tierra
    if k < 0.5:
        fr.meshes.append(tortilla().tf(rz=8 * math.sin(lt * 2) + flip, t=(0, y, 0)))
    else:
        fr.meshes.append(flat_earth(spin=lt * 8, y=0).tf(rz=flip - 180, t=(0, y, 0)))
    if k > 0:
        fr.under.append(lambda d, cam: ring3(d, cam, (0, y, 0), R * 1.04, CYAN, 2.2, k * 0.8))
    if lt > 3.4:
        a = appear(t, t0 + 3.4)
        ang = lean_at(1.6) * ease(clamp((lt - 3.6) / 1.0))
        fr.meshes += person(1.6, 0, y + 0.06, lean=ang, s=0.55 * a)
    if not loop:
        head(fr, ['Agarra', 'una tortilla.'], CYAN, t, t0 + 0.05, kicker='¿Qué pasaría si…?')
    lab(fr, 'Recreación · Escala exagerada', clamp(lt / 0.5))


def s_xray(fr, t, lt, dur):
    """Escáner de rayos X: la superficie se vuelve transparente y se ven corteza, manto y núcleo aplastados."""
    t0 = t - lt
    fr.floor = 0.6
    fr.cam = Cam(target=(0, 0.45, 0), dist=vfit(6.2), yaw=-30 + lt * 8, pitch=22)
    ts, te = t0 + 0.15, t0 + 1.4
    ys, k = scan_ring(fr, t, ts, te, 0.0, 1.0, center=(0, 0, 0), r=R * 1.12)
    shell = flat_earth(R, 0.3, spin=lt * 5, y=0.45)
    shell.alpha = 1 - 0.8 * ease(k)
    if k > 0.05:
        e = ease(k)
        fr.meshes.append(cyl(R * 0.96, 0.5, CRUST, n=40, shadow=0.3, gloss=0.2, y0=0.2).tf())
        fr.meshes.append(cyl(R * 0.8, 0.36, MANTLE, n=40, shadow=0, gloss=0.3, y0=0.27))
        fr.meshes.append(cyl(R * 0.38 * e, 0.22, CORE, n=32, shadow=0, gloss=0.6, y0=0.34))
        ui_label3(fr, (R * 0.38, 0.58, 0), 'Núcleo', a=clamp((lt - 1.2) / 0.4), side=1, length=110, up=170)
        ui_label3(fr, (-R * 0.8, 0.6, 0), 'Manto', a=clamp((lt - 1.4) / 0.4), side=-1, length=90, up=120)
    fr.meshes.append(shell)
    head(fr, ['Así se vería', 'por dentro.'], CYAN, t, t0 + 0.1, kicker='Rayos X')
    lab(fr, 'Recreación · Esquema simplificado', clamp(lt / 0.4))


def s_gravity(fr, t, lt, dur):
    """Flechas de gravedad: abajo en el centro, cada vez más de lado hacia la orilla."""
    t0 = t - lt
    fr.floor = 0.5
    fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(6.4), yaw=lt * 4, pitch=26)
    fr.meshes.append(flat_earth(spin=lt * 3, f=0.12))
    k = clamp((lt - 0.5) / 2.0)
    n = 0
    for rr in (0.0, 0.7, 1.35, 1.9):
        for j in range(1 if rr == 0 else 6):
            th = 2 * math.pi * j / 6 + rr
            x, z = rr * math.cos(th), rr * math.sin(th)
            n += 1
            if n / 19 > k + 0.02:
                continue
            p = np.array([x, 0.12, z])
            g = gdir(x, z)
            arrow3(fr, p - g * 0.75, g * 0.6, LASER if rr > 1.5 else ICE, 3.0, a=1.0)
    fr.under.append(lambda d, cam: dot3(d, cam, (0, 0, 0), 9, AMBER, 0.9))
    ui_label3(fr, (0, 0.0, 0), 'Centro de masa', a=clamp((lt - 1.0) / 0.4), side=-1, length=80, up=260)
    head(fr, ['La gravedad', 'jalaría al centro.'], CYAN, t, t0 + 0.1, kicker='No hacia abajo')
    lab(fr, 'Escala exagerada', clamp(lt / 0.4))


def s_tilt(fr, t, lt, dur):
    """Tres personas: derecha en el centro, cada vez más ladeadas lejos de él (siguen a la gravedad)."""
    t0 = t - lt
    fr.floor = 0.5
    fr.cam = Cam(target=(0.9, 0.55, 0), dist=vfit(5.2) - lt * 0.15, yaw=-4 + lt * 2.5, pitch=14)
    fr.meshes.append(flat_earth(spin=10, f=0.08))
    k = ease(clamp((lt - 0.8) / 1.6))
    for x, sh in ((0.0, SHIRT), (1.0, (60, 160, 90)), (1.85, PINK)):
        ang = lean_at(x) * k
        fr.meshes += person(x, 0.2 if x else 0.0, 0.08, lean=ang, s=0.7, shirt=sh)
        if x:
            ui_text3(fr, (x + 0.15, 1.25, 0), f'{ang:.0f}°', 30, a=k, col=AMBER, fk='mono')
    ui_text3(fr, (0.0, 1.25, 0.2), '0°', 30, a=k, col=LGREEN, fk='mono')
    head(fr, ['Lejos del centro,', 'el piso se inclina.'], CYAN, t, t0 + 0.1, kicker='Inclinación que sentirías')
    lab(fr, 'Recreación · Escala exagerada', clamp(lt / 0.4))


def s_slope(fr, t, lt, dur):
    """Cuesta que nunca termina: la persona camina y el piso (con puntos) se desliza hacia abajo."""
    t0 = t - lt
    fr.floor = 0.0
    ang = 38
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(5.4), yaw=72 - lt * 3, pitch=8, roll=0)
    ramp = box(6.5, 0.12, 1.6, (150, 120, 90), cols={'top': (176, 142, 104)}, shadow=0.3, base=False).tf(rz=ang)
    fr.meshes.append(ramp)
    c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    off = (lt * 0.6) % 0.5

    def stripes(d, cam):
        for i in range(-7, 8):
            u = i * 0.5 - off
            p = np.array([u * c, u * s_ + 0.07, 0])
            line3(d, cam, [p + (0, 0, -0.75), p + (0, 0, 0.75)], (120, 92, 64), 2.0)
    fr.under.append(stripes)
    step = math.sin(lt * 7) * 3
    fr.meshes += [m.tf(t=(0, 0.06, 0)) for m in person(0, 0, 0, lean=-6 + step * 0.3, s=0.9)]
    bigc(fr, f'{lt * 0.6:4.1f} m', 'SUBIDOS… Y SIGUES IGUAL', y=0.62 if VERT else 0.3, size=70)
    head(fr, ['Una cuesta', 'que nunca termina.'], CYAN, t, t0 + 0.1, kicker='Cerca de la orilla')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_pool(fr, t, lt, dur):
    """El agua y el aire se juntan en el centro del disco; luego el plato con salsa."""
    t0 = t - lt
    split = 2.6
    if lt < split:
        fr.floor = 0.5
        fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(6.6), yaw=lt * 6, pitch=30)
        fr.meshes.append(flat_earth(spin=lt * 4, f=0.08))
        k = ease(clamp(lt / 2.0))
        w = sphere(1.0, WATER, nu=32, nv=12, shadow=0, gloss=0.9).tf(s=(lerp(R, 0.9, k), lerp(0.09, 0.32, k), lerp(R, 0.9, k)))
        fr.meshes.append(w)
        rng = np.random.RandomState(7)
        pts = rng.uniform(0, 1, (140, 3))

        def air(d, cam, k=k):
            for u, v, h in pts:
                rr = math.sqrt(u) * lerp(R, 1.2, k)
                th = 2 * math.pi * v
                dot3(d, cam, (rr * math.cos(th), 0.15 + h * lerp(0.3, 0.9, k), rr * math.sin(th)), 3.0, ICE, 0.7)
        fr.over.append(air)
        ui_label3(fr, (0.0, 0.8 * k + 0.3, 0), 'Aire', a=k, side=1, length=80, up=120)
        head(fr, ['El agua y el aire', 'se van al centro.'], CYAN, t, t0 + 0.1, kicker='Como en un plato')
    else:
        lt2 = lt - split
        fr.floor = 0.6
        fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(4.6), yaw=-20 + lt2 * 6, pitch=38)
        fr.meshes.append(cyl(1.5, 0.12, PLATE, n=40, r2=1.65, shadow=0.4, gloss=0.6))
        fr.meshes.append(cyl(1.05, 0.04, (226, 222, 214), n=40, shadow=0, gloss=0.5, y0=0.02))
        k = ease(clamp(lt2 / 1.4))
        sal = sphere(1.0, SALSA, nu=28, nv=10, shadow=0, gloss=0.8).tf(s=(lerp(1.3, 0.6, k), 0.06, lerp(1.3, 0.6, k)), t=(0, 0.08, 0))
        fr.meshes.append(sal)
        head(fr, ['Como la salsa', 'en tu plato.'], CYAN, t, t0 + split + 0.05, kicker='Todo se junta al centro')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_everest(fr, t, lt, dur):
    """La orilla: aire delgado como en la cima del Everest; contador del aire que queda."""
    t0 = t - lt
    fr.floor = 0.4
    fr.cam = Cam(target=(0, 1.3, 0), dist=vfit(6.8), yaw=-25 + lt * 5, pitch=10)
    fr.meshes.append(cyl(2.3, 2.9, ROCK, n=9, r2=0.05, shadow=0.4, gloss=0.1))
    fr.meshes.append(cyl(0.62, 0.78, SNOW, n=9, r2=0.02, shadow=0, gloss=0.3, y0=2.14))
    fr.meshes += person(0.0, 0.0, 2.92, s=0.35, shirt=(240, 120, 40))
    k = eout(clamp((lt - 0.3) / 2.2))
    v = lerp(100, 33, k)
    rng = np.random.RandomState(4)
    pts = rng.uniform(-1, 1, (160, 3)) * (2.6, 1.0, 1.6) + (0, 1.5, 0)

    def air(d, cam):
        for i, p in enumerate(pts):
            dens = 1 - (p[1] - 0.5) / 2.5 * k
            if (i * 0.618) % 1 < dens:
                dot3(d, cam, p, 3.0, ICE, 0.55)
    fr.under.append(air)
    bigc(fr, f'{v:.0f} %', 'DEL AIRE DE LA PLAYA', y=0.58 if VERT else 0.3, size=92)
    ui_label3(fr, (0, 2.9, 0), 'Everest · 8,849 m', a=clamp((lt - 0.6) / 0.4), side=1, length=90, up=90)
    head(fr, ['En la orilla,', 'aire de Everest.'], CYAN, t, t0 + 0.1, kicker='Aire delgado')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_hypo(fr, t, lt, dur):
    """Pueblitos en todo el disco: ¿y si aun así viviéramos ahí?"""
    t0 = t - lt
    fr.floor = 0.4
    fr.cam = Cam(target=(0, 0.1, 0), dist=vfit(6.0) - lt * 0.3, yaw=40 + lt * 10, pitch=40 - lt * 3)
    fr.meshes.append(flat_earth(spin=lt * 2, f=0.08))
    for i, (rr, th) in enumerate(((0.3, 0.4), (1.0, 2.0), (1.6, 3.6), (1.2, 5.0), (1.8, 1.0))):
        if lt > 0.3 + i * 0.25:
            x, z = rr * math.cos(th), rr * math.sin(th)
            fr.meshes += [m.tf(t=(0, 0.08, 0)) for m in house(x, z, ry=math.degrees(th), s=0.16 * appear(t, t0 + 0.3 + i * 0.25))]

    def f(img, d, lt=lt):
        k = ease(clamp((lt - 2.2) / 0.4))
        if k > 0:
            pill(img, d, W / 2, H * 0.60, '  HIPÓTESIS  ', k, size=58, dotc=AMBER)
    fr.ui.append(f)
    head(fr, ['¿Y si aun así', 'viviéramos ahí?'], CYAN, t, t0 + 0.1, kicker='Imagina')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_gene(fr, t, lt, dur):
    """Persona de la orilla con la doble hélice del gen EPAS1 y la sangre que lleva el oxígeno."""
    t0 = t - lt
    fr.floor = 0.4
    fr.cam = Cam(target=(0.4, 0.95, 0), dist=vfit(5.0), yaw=-10 + lt * 5, pitch=8)
    fr.meshes += person(-0.6, 0, 0, s=1.5, shirt=(150, 40, 60))
    k = clamp((lt - 0.4) / 1.6)

    def helix(d, cam, lt=lt, k=k):
        n = int(40 * k)
        for i in range(n):
            u = i / 40
            y = 0.2 + u * 1.9
            a = u * 4 * math.pi + lt * 2
            p1 = (1.2 + 0.32 * math.cos(a), y, 0.32 * math.sin(a))
            p2 = (1.2 - 0.32 * math.cos(a), y, -0.32 * math.sin(a))
            if i % 2 == 0:
                line3(d, cam, [p1, p2], (90, 110, 160), 1.6, a=0.8)
            dot3(d, cam, p1, 6, CYAN)
            dot3(d, cam, p2, 6, PINK)
    fr.over.append(helix)
    # glóbulos rojos que corren por el cuerpo
    for j in range(6):
        u = (lt * 0.5 + j / 6) % 1
        fr.meshes.append(sphere(0.05, (220, 40, 50), nu=10, nv=6, shadow=0, gloss=0.6).tf(s=(1, 0.5, 1), t=(-0.6 + 0.12 * math.sin(u * 9), 0.3 + u * 1.3, 0.2)))
    ui_label3(fr, (1.2, 2.2, 0), 'Gen EPAS1', sub='tibetanos', a=clamp((lt - 1.4) / 0.4), side=1, length=60, up=60)
    head(fr, ['Como los tibetanos:', 'un gen para poco oxígeno.'], CYAN, t, t0 + 0.1, kicker='Ya pasó en la Tierra real')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_evolve(fr, t, lt, dur):
    """Humano del centro vs humano de la orilla (inclinado, piernas cortas y fuertes); luego una cabra de montaña."""
    t0 = t - lt
    fr.floor = 0.5
    fr.cam = Cam(target=(0, 0.75, 0), dist=vfit(5.0), yaw=-12 + lt * 4, pitch=10)
    k = ease(clamp((lt - 0.4) / 1.6))
    fr.meshes += person(-0.75, 0, 0, s=1.2, shirt=SHIRT)
    fr.meshes += person(0.75, 0, 0, lean=-22 * k, s=1.2, legs=lerp(1.0, 0.62, k), wide=lerp(1.0, 1.35, k), shirt=PINK)
    ui_text3(fr, (-0.75, -0.25, 0.4), 'CENTRO', 26, a=1, col=MUTED, fk='mono')
    ui_text3(fr, (0.75, -0.25, 0.4), 'ORILLA', 26, a=1, col=AMBER, fk='mono')
    if lt > 3.0:
        a = appear(t, t0 + 3.0)
        g = [box(0.55, 0.3, 0.22, (236, 230, 220), shadow=0.3, base=False, edge=False).tf(t=(0, 0.42, 0)),
             box(0.18, 0.2, 0.14, (236, 230, 220), shadow=0, base=False).tf(rz=-30, t=(0.33, 0.62, 0))]
        for sx in (-0.2, 0.2):
            for sz in (-0.07, 0.07):
                g.append(cyl(0.03, 0.3, (120, 110, 100), n=6, shadow=0).tf(t=(sx, 0, sz)))
        g.append(cyl(0.015, 0.14, (90, 80, 70), n=6, shadow=0).tf(rz=-30, t=(0.36, 0.7, 0)))
        fr.meshes += [m.tf(s=a * 0.9, t=(1.9, 0, 0.3)) for m in g]
    head(fr, ['Inclinados, piernas', 'cortas y fuertes.'], CYAN, t, t0 + 0.1, kicker='Humanos de la orilla')
    lab(fr, 'Hipótesis · Recreación', clamp(lt / 0.4), dotc=AMBER)


def s_center(fr, t, lt, dur):
    """Pueblo mexicano en el centro, bajo el aire más denso: vivirían casi como tú."""
    t0 = t - lt
    fr.floor = 0.7
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(9.0) - lt * 0.3, yaw=20 + lt * 6, pitch=22)
    cols = (TERRA, CREAM, (90, 150, 190), (230, 180, 70), (200, 90, 120))
    for i, (x, z) in enumerate(((-1.6, -0.4), (0.0, -0.9), (1.6, -0.3), (-0.9, 1.0), (0.9, 1.1))):
        fr.meshes += house(x, z, ry=-10 * x, s=0.55, col=cols[i], roofdish=False)
    fr.meshes += person(0.1, 0.4, 0, s=0.6, shirt=(60, 160, 90))
    rng = np.random.RandomState(9)
    pts = rng.uniform(-1, 1, (260, 3)) * (2.6, 0.9, 1.8) + (0, 1.2, 0)
    fr.over.append(lambda d, cam: [dot3(d, cam, q, 2.6, ICE, 0.55) for q in pts])
    bigc(fr, '100 %', 'DE AIRE, COMO EN TU CASA', y=0.60 if VERT else 0.3, size=86)
    head(fr, ['En el centro,', 'casi como tú.'], CYAN, t, t0 + 0.1, kicker='Aire denso')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_collapse(fr, t, lt, dur):
    """El disco no aguanta: su gravedad lo aplasta hasta volverlo una bola (la Tierra real)."""
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.0, 0), dist=vfit(6.6), yaw=lt * 6, pitch=lerp(30, 8, ease(clamp(lt / 3.5))))
    k = ease(clamp((lt - 0.9) / 2.8))
    rr = lerp(R, 1.35, k)
    fy = lerp(0.08, 1.35, k)
    fr.meshes.append(earth(1.0, lon0=-100, lat_tilt=lerp(0, 20, k), spin=lt * 14).tf(s=(rr, fy, rr)))
    if k > 0.6:
        fr.under.append(lambda d, cam: atmo(d, cam, (0, 0, 0), 1.37, a=(k - 0.6) / 0.4))
    for j in range(8):
        th = 2 * math.pi * j / 8 + lt
        p = np.array([rr * 1.3 * math.cos(th), 0.0, rr * 1.3 * math.sin(th)])
        arrow3(fr, p, -p * 0.18, LASER, 2.6, a=clamp(1 - k * 1.2))
    head(fr, ['Su gravedad', 'lo haría bola.'], CYAN, t, t0 + 0.1, kicker='Un disco así no aguanta')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_share(fr, t, lt, dur):
    """Cierre: sello, Sí/No y loop (la Tierra se aplana y vuelve a ser tortilla, como al inicio)."""
    t0 = t - lt
    fr.floor = 0.6
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(6.8), yaw=-20 + lt * 3, pitch=lerp(10, 34, ease(clamp((lt - dur + 2.6) / 2.0))))
    k = ease(clamp((lt - (dur - 2.8)) / 1.6))   # bola -> disco -> tortilla al final (loop)
    rr = lerp(1.35, R, k)
    fy = lerp(1.35, 0.08, k)
    y = lerp(0.3, 0.35, k)
    kt = clamp((lt - (dur - 1.4)) / 0.9)
    m = earth(1.0, lon0=-100, lat_tilt=lerp(20, 0, k), spin=lt * 12).tf(s=(rr, fy, rr), t=(0, y, 0))
    if kt < 0.5:
        fr.meshes.append(m.tf(rz=180 * kt))
    else:
        fr.meshes.append(tortilla().tf(rz=180 * kt - 180, t=(0, y, 0)))

    def f(img, d, lt=lt):
        yy = H * 0.66
        a = ease(clamp((lt - 1.4) / 0.4)) * (1 - kt)
        pill(img, d, W / 2 - 170, yy, '  SÍ  ', a, size=54, dotc=LGREEN)
        pill(img, d, W / 2 + 170, yy, '  NO  ', a, size=54, dotc=LASER)
        draw_text(d, (W / 2, H * 0.205), 'MENTE EN ÓRBITA', font('mono', 60), INK, 'mm', a=ease(clamp(lt / 0.5)), spacing=5)
    fr.ui.append(f)
    head(fr, ['Mándaselo a tu', 'amigo terraplanista.'], CYAN, t, t0 + 0.1, kicker='¿Vivirías en la orilla?')


SHOTS = [(('c0', 0), s_hook), (('c0', 1), s_xray), (('c0', 2), s_gravity), (('c0', 3), s_tilt), (('c0', 4), s_slope),
         (('c0', 5), s_pool), (('c0', 6), s_everest), (('c0', 7), s_hypo), (('c0', 8), s_gene), (('c0', 9), s_evolve),
         (('c0', 10), s_center), (('c0', 11), s_collapse), (('c0', 12), s_share)]

if __name__ == '__main__':
    S.main(SHOTS, {})
