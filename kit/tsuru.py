"""Reel extra: por qué el Tsuru fue tan conocido en México (28-oct-2026). Tema visual: orbita.
Escenas: taxi rosa de la CDMX que llega por una calle (gancho: 0 estrellas y 2.4 millones vendidos) · escáner de rayos X
que recorre el auto · motor de 4 cilindros con llave de mecánico · línea de ensamble de CIVAC (recreación) · 1992 = 2017 y
vista explotada de refacciones · el Tsuru reemplaza al Vocho + fotos reales de taxis (Wikimedia Commons) · duelo de ventas
Tsuru vs Vocho · rayos X de lo que no tenía (bolsas de aire, ABS) · prueba de choque (recreación) · contador de muertes ·
norma y último Tsuru (Buen Camino) · cierre de la planta CIVAC · cierre Sí/No con loop (el taxi vuelve a llegar).
Uso: MOTOR_TEMA=orbita GTA_FMT=v VIDEO_TL=/home/claude/tl_tsuru.json python3 tsuru.py info|preview T out.png|sheet out.jpg t..|chunk A B out.mp4"""
import os
os.environ.setdefault('MOTOR_TEMA', 'orbita')
os.environ.setdefault('GTA_FMT', 'v')
os.environ.setdefault('VIDEO_TL', '/home/claude/tl_tsuru.json')
import math
import numpy as np
import escenas as S
from escenas import *  # noqa: F401,F403
from motor3d import tex, Mesh
from starlink import bigc, CYAN, ICE, LASER, LGREEN, AMBER, TERRA, CREAM
import tsuru_model as M

S.CREDIT = 'Fotos reales · Wikimedia Commons (CC BY-SA)'
ASPH = (58, 60, 66)
WALK = (150, 148, 142)
LINE = (232, 232, 226)
YELLOWL = (240, 200, 60)
REDX = (255, 70, 90)
FLOORF = (96, 100, 108)


def lab2(fr, txt, a=1.0, dotc=CYAN):
    """Etiqueta honesta abajo a la izquierda (no choca con contadores ni subtítulos)."""
    fr.ui.append(lambda img, d: pill(img, d, 40, H * 0.735, txt, a, anchor='l', dotc=dotc))


def star(d, x, y, r, filled, col, a=1.0):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        th = -math.pi / 2 + k * math.pi / 5
        pts.append((x + rr * math.cos(th), y + rr * math.sin(th)))
    bgc = tuple(int(v) for v in BG)
    c = mix(bgc, col, a)
    if filled:
        d.polygon(pts, fill=c, outline=c)
    else:
        d.line(pts + [pts[0]], fill=c, width=4)


def stars_ui(fr, y, a, n_on=0, txt='0 / 5', sub='ESTRELLAS DE SEGURIDAD'):
    def f(img, d):
        if a <= 0.01:
            return
        for k in range(5):
            star(d, W / 2 + (k - 2) * 120, y, 46, k < n_on, AMBER, a)
        draw_text(d, (W / 2, y + 100), txt, font('mono', 72), INK, 'mm', a=a)
        draw_text(d, (W / 2, y + 160), sub, font('sb', 28), MUTED, 'mm', a=a, spacing=3)
    fr.ui.append(f)


# ------------------------------------------------------------------ escenario: calle de la CDMX
_BT = {}


def bld_tex(col, floors, seed):
    key = (col, floors, seed)
    if key not in _BT:
        rng = np.random.RandomState(seed)

        def f(d, im):
            w, h = im.size
            fh = h / floors
            for i in range(floors):
                for j in range(4):
                    x0 = 18 + j * (w - 36) / 4
                    y0 = i * fh + fh * 0.25
                    lit = rng.rand() < 0.35
                    d.rectangle((x0 + 8, y0, x0 + (w - 36) / 4 - 8, y0 + fh * 0.5), fill=(250, 214, 140) if lit else (50, 62, 80))
            d.rectangle((0, h - fh * 0.9, w, h), fill=tuple(int(c * 0.8) for c in col))
        _BT[key] = tex(240, 60 * floors, col + (255,), f)
    return _BT[key]


BCOLS = [TERRA, CREAM, (96, 150, 190), (226, 180, 70), (190, 90, 110), (150, 170, 120), (230, 230, 225)]


def street(fr, x0=-16.0, x1=16.0, scroll=0.0, bz=-7.2, both=False):
    """Calle con carriles, banquetas y edificios de colores (recreación de una avenida de la CDMX)."""
    L = x1 - x0
    xc = (x0 + x1) / 2
    fr.meshes.append(box(L, 0.02, 7.0, ASPH, shadow=0.0, base=True, edge=False, gloss=0.1).tf(t=(xc, -0.02, 0)))
    for zs in ((-4.2,) if not both else (-4.2, 4.2)):
        fr.meshes.append(box(L, 0.16, 1.4, WALK, shadow=0.0, base=True, edge=False, cols={'top': (176, 172, 164)}).tf(t=(xc, 0, zs)))
    k0 = math.floor((x0 - scroll) / 3.0)
    for k in range(k0, k0 + int(L / 3.0) + 2):
        x = k * 3.0 + scroll
        if x0 < x < x1:
            fr.meshes.append(box(1.6, 0.012, 0.14, LINE, shadow=0.0, base=True, edge=False).tf(t=(x, 0.0, -1.0)))
    fr.meshes.append(box(L, 0.012, 0.12, YELLOWL, shadow=0.0, base=True, edge=False).tf(t=(xc, 0.0, -3.35)))
    # edificios (fachada al frente)
    x = x0
    i = 0
    while x < x1:
        w = 3.0 + (i * 7 % 5) * 0.5
        fl = 1 + (i * 3 % 3)
        h = fl * 1.5
        col = BCOLS[i % len(BCOLS)]
        b = box(w - 0.1, h, 2.4, col, shadow=0.0, base=True, edge=False, gloss=0.1)
        decal(b, b.FACE['front'], bld_tex(col, fl, i))
        fr.meshes.append(b.tf(t=(x + w / 2, 0, bz - 1.2)))
        if i % 2 == 0:  # poste de luz
            fr.meshes.append(cyl(0.05, 3.6, (80, 84, 90), n=6, shadow=0.0).tf(t=(x + 0.3, 0.16, -3.7)))
            fr.meshes.append(box(0.7, 0.08, 0.16, (80, 84, 90), shadow=0.0, base=True).tf(t=(x + 0.6, 3.7, -3.7)))
        x += w
        i += 1


# ------------------------------------------------------------------ ayudas de malla
def clip(ms, keep):
    """Deja solo las caras cuyo centro cumple keep(c)."""
    out = []
    for m in ms:
        F, C = [], []
        for f, c in zip(m.F, m.C):
            if keep(m.V[list(f)].mean(0)):
                F.append(f); C.append(c)
        if F:
            mm = m.copy(); mm.F = F; mm.C = C
            mm.decals = [dd for dd in m.decals if dd[0] < len(F)] if len(F) == len(m.F) else []
            out.append(mm)
    return out


def ghost(fr, ms, col=CYAN, a=0.7, w=1.4, every=1):
    """Silueta de rayos X: dibuja las aristas de las caras (debajo de las piezas internas)."""
    segs = []
    for m in ms:
        for fi, f in enumerate(m.F):
            if fi % every:
                continue
            P = m.V[list(f)]
            segs.append(np.vstack([P, P[:1]]))

    def g(d, cam):
        for P in segs:
            line3(d, cam, P, col, w, a=a)
    fr.under.append(g)


def xring(fr, x, r=1.15, cy=0.7, a=1.0):
    """Anillo escáner vertical que recorre el auto a lo largo."""
    def o(d, cam):
        for j, (rr, w) in enumerate(((r, 3.4), (r * 1.07, 1.6), (r * 0.93, 1.2))):
            th = np.linspace(0, 2 * math.pi, 64)
            P = np.stack([np.full_like(th, x), cy + rr * np.sin(th), rr * 1.0 * np.cos(th)], 1)
            line3(d, cam, P, CYAN, w, a=a * (1 - j * 0.3))
    fr.over.append(o)


def crush(ms, k, dx=0.0):
    """Deforma el frente (choque): comprime la parte delantera y baja el techo cerca del parabrisas."""
    out = []
    xl = 2.2 - 0.9 * k
    for m in ms:
        mm = m.copy()
        V = mm.V.copy()
        x = V[:, 0] - dx
        zone = x > xl - 0.9
        x[zone] = (xl - 0.9) + (x[zone] - (xl - 0.9)) * (0.9 / (2.25 - (xl - 0.9)))
        up = (V[:, 1] > 0.9) & (x > -0.6)
        V[up, 1] -= 0.22 * k * np.clip((x[up] + 0.6) / 1.4, 0, 1)
        V[:, 0] = x + dx
        mm.V = V
        out.append(mm)
    return out


def ui_x3(fr, p, size=90, a=1.0, col=REDX):
    """Tache rojo (X) dibujado con líneas sobre un punto 3D."""
    def f(img, d, p=p):
        x, y, z = fr.cam.p1(p)
        if z > 0.2 and a > 0.01:
            c = mix(tuple(int(v) for v in BG), col, a)
            r = size / 2
            d.line([(x - r, y - r), (x + r, y + r)], fill=c, width=int(size / 6))
            d.line([(x - r, y + r), (x + r, y - r)], fill=c, width=int(size / 6))
    fr.ui.append(f)


def person_icon(d, x, y, s, col, a):
    bgc = tuple(int(v) for v in BG)
    c = mix(bgc, col, a)
    d.ellipse((x - 7 * s, y - 22 * s, x + 7 * s, y - 8 * s), fill=c)
    d.rounded_rectangle((x - 10 * s, y - 5 * s, x + 10 * s, y + 20 * s), radius=6 * s, fill=c)


# ------------------------------------------------------------------ poses del gancho y del loop
def hook_car(lt, t_arrive=1.6):
    k = eout(clamp(lt / t_arrive))
    x = lerp(-15.0, 0.0, k)
    spin = -lerp(0, 15.0, k) * 120
    return x, spin


def hook_cam(lt):
    return Cam(target=(0.4, 0.75, 0), dist=vfit(8.4) - min(lt, 7) * 0.12, yaw=52 + lt * 2.2, pitch=9 + lt * 0.4)


# ================================================================== escenas
def s_hook(fr, t, lt, dur, loop=False):
    """Un Tsuru taxi rosa llega por una avenida; 0 estrellas; luego se multiplica en una flota y el contador sube."""
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = hook_cam(lt)
    x, spin = hook_car(lt)
    street(fr, scroll=0.0)
    fr.meshes += M.place(M.tsuru('cdmx', spin=spin, lights=1.0), x=x)
    ts = T(('c0', 0, 'sacó'), default=1.4)
    ta = T(('c0', 0, 'aun'), default=3.9)
    a1 = ease(clamp((t - ts) / 0.4)) * (1 - ease(clamp((t - ta + 0.2) / 0.4)))
    stars_ui(fr, H * 0.27, a1)
    if t > ta - 0.3:
        k = clamp((t - ta + 0.3) / 2.6)
        n = int(2 + 22 * ease(k))
        for i in range(n):
            r, c = divmod(i, 6)
            fr.meshes += M.place(M.tsuru(['cdmx', 'dorado', 'verde', 'blanco'][(i * 7) % 4], taxi=i % 3 != 2, parts=False),
                                 x=-5.5 - r * 5.0 + (c % 2) * 1.6, z=-2.2 + (c % 3) * 1.5 - (c // 3) * 0.2, s=0.98)
        v = 2400000 * eout(clamp((t - ta) / 2.4))
        bigc(fr, fmt_int(max(0, v)), 'TSURUS VENDIDOS EN MÉXICO', a=ease(clamp((t - ta) / 0.3)), y=0.29, size=110)
    if not loop:
        head(fr, ['Mira', 'este coche.'], CYAN, t, t0 + 0.05, kicker='Lo que no ves')
    lab2(fr, 'Recreación 3D · Nissan Tsuru (1984–2017)', clamp(lt / 0.5), dotc=(222, 42, 128))


def xray_parts(lt):
    ms = M.interior()
    ms += M.engine(lt)
    for x in M.WHEELS_X:
        for z in (0.73, -0.73):
            ms += M.wheel(x, z, 0)
            ms += M.brake(x, z)
    return ms


def s_xray(fr, t, lt, dur):
    """Escáner de rayos X: el anillo recorre el auto; detrás de él la carrocería se vuelve silueta y se ven las piezas."""
    t0 = t - lt
    fr.floor = 0.5
    fr.cam = Cam(target=(0, 0.6, 0), dist=vfit(7.6), yaw=38 + lt * 6, pitch=16)
    k = ease(clamp((lt - 0.1) / 1.5))
    xr = lerp(2.5, -2.5, k)
    car = M.tsuru('cdmx')
    body = car[:2]
    fr.meshes += clip(car, lambda c: c[0] < xr)
    ghost(fr, clip(body, lambda c: c[0] >= xr), CYAN, 0.55, 1.2)
    fr.meshes += clip(xray_parts(lt), lambda c: c[0] >= xr)
    if 0.02 < k < 0.99:
        xring(fr, xr)
    a = clamp((lt - 1.0) / 0.4)
    ui_label3(fr, (1.45, 1.0, 0), 'Motor', sub='1.6 L · 4 cilindros', a=a, side=1, length=70, up=140)
    ui_label3(fr, (-1.3, 0.55, 0), 'Tanque', a=clamp((lt - 1.3) / 0.4), side=-1, length=70, up=160)
    ui_label3(fr, (0.05, 0.9, 0.36), 'Asientos', a=clamp((lt - 1.5) / 0.4), side=-1, length=60, up=230)
    head(fr, ['Así se ve', 'por dentro.'], CYAN, t, t0 + 0.1, kicker='Rayos X')
    lab2(fr, 'Recreación · esquema simplificado', clamp(lt / 0.4))


def wrench(t):
    """Llave española (de mecánico)."""
    ms = [box(0.9, 0.05, 0.1, (196, 200, 206), shadow=0.0, base=False, gloss=0.8)]
    for sgn in (-1, 1):
        ms.append(box(0.12, 0.05, 0.06, (196, 200, 206), shadow=0.0, base=False, gloss=0.8).tf(t=(0.5, 0, sgn * 0.08)))
    return ms


def s_engine(fr, t, lt, dur):
    """Motor de cerca con los 4 pistones; una llave aprieta un tornillo: lo arregla cualquier mecánico."""
    t0 = t - lt
    fr.floor = 0.5
    fr.cam = Cam(target=(1.45, 0.75, 0), dist=vfit(3.4) - lt * 0.1, yaw=60 + lt * 7, pitch=26)
    car = M.tsuru('cdmx')
    ghost(fr, car[:2], CYAN, 0.35, 1.0, every=1)
    eng = M.engine(lt * 1.4, s=1.25)
    fr.meshes += eng
    # llave que gira sobre un tornillo de la cabeza
    ang = 25 * math.sin(lt * 5)
    fr.meshes += [m.tf(s=0.5).tf(ry=ang + 30).tf(t=(1.45 + 0.22, 1.12, 0.1)) for m in wrench(t)]
    fr.meshes.append(cyl(0.04, 0.08, (220, 200, 120), n=6, shadow=0.0, gloss=0.8).tf(t=(1.45, 1.08, 0.1)))
    a = clamp((lt - 0.5) / 0.4)
    ui_label3(fr, (1.45, 1.05, -0.28), '4 cilindros', sub='1.6 litros', a=a, side=-1, length=60, up=180)
    ui_label3(fr, (1.9, 1.15, 0.1), 'Una llave', sub='y listo', a=clamp((lt - 1.4) / 0.4), side=1, length=50, up=200)
    head(fr, ['Tan sencillo que', 'lo arregla cualquiera.'], CYAN, t, t0 + 0.1, kicker='Mecánico de colonia')
    lab2(fr, 'Recreación', clamp(lt / 0.4))


def robot(x, z, ph, reach=0.0):
    ms = [cyl(0.25, 0.3, (240, 150, 40), n=12, shadow=0.0, gloss=0.4)]
    a1 = -40 + 25 * math.sin(ph)
    ms.append(box(0.16, 1.3, 0.16, (240, 150, 40), shadow=0.0, base=True, gloss=0.4).tf(rz=a1).tf(t=(0, 0.3, 0)))
    ex = -math.sin(math.radians(a1)) * 1.3
    ey = 0.3 + math.cos(math.radians(a1)) * 1.3
    ms.append(box(1.0, 0.12, 0.12, (240, 150, 40), shadow=0.0, base=False, gloss=0.4).tf(rz=-20 + 15 * math.sin(ph * 1.3)).tf(t=(ex + 0.45, ey, 0)))
    tip = (ex + 0.95, ey - 0.15, 0)
    return [m.tf(ry=90 if z > 0 else -90).tf(t=(x, 0, z)) for m in ms], (x + (tip[2] if z > 0 else -tip[2]), tip[1], z - (tip[0] if z > 0 else -tip[0]))


def s_plant(fr, t, lt, dur):
    """Línea de ensamble (recreación): carrocerías en lámina, pintadas y terminadas avanzan; robots soldando; contador 1984→2017."""
    t0 = t - lt
    fr.floor = 0.0
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(14.5) - lt * 0.3, yaw=28 + lt * 3, pitch=18)
    fr.meshes.append(box(30, 0.02, 9, FLOORF, shadow=0.0, base=True, edge=False, gloss=0.2).tf(t=(0, -0.02, 0)))
    for z in (-1.4, 1.4):
        fr.meshes.append(box(30, 0.012, 0.1, YELLOWL, shadow=0.0, base=True, edge=False).tf(t=(0, 0.0, z)))
    fr.meshes.append(box(30, 0.18, 1.3, (44, 46, 52), shadow=0.0, base=True, edge=False, gloss=0.3))
    # nave: columnas y vigas
    for x in np.arange(-12, 13, 4.0):
        for z in (-4.0, 4.0):
            fr.meshes.append(box(0.25, 5.0, 0.25, (140, 146, 156), shadow=0.0, base=True))
    sp = 0.9
    for i in range(6):
        x = ((lt * sp + i * 4.4) % 26.4) - 15.0
        if x < -4.5:
            sch, parts, tx = 'gris', False, False
        elif x < 2.5:
            sch, parts, tx = 'blanco', False, False
        else:
            sch, parts, tx = 'blanco', True, False
        fr.meshes += M.place(M.tsuru(sch, taxi=tx, parts=parts), x=x, y=0.18, s=1.0)
    sparks = []
    for j, (rx, rz) in enumerate(((-6.5, 1.9), (-6.5, -1.9), (-1.0, 1.9), (-1.0, -1.9))):
        ms, tip = robot(rx, rz, lt * 3 + j)
        fr.meshes += ms
        if j < 2:
            sparks.append(tip)
    rng = np.random.RandomState(int(lt * 24) % 997)

    def spk(d, cam):
        for p in sparks:
            for _ in range(10):
                q = np.array(p) + rng.uniform(-0.25, 0.25, 3)
                dot3(d, cam, q, rng.uniform(1.5, 3.5), AMBER, 0.9)
    fr.over.append(spk)
    v = int(lerp(1984, 2017, eout(clamp((lt - 0.4) / 2.6))))
    bigc(fr, str(v), '33 AÑOS EN CIVAC, MORELOS', a=ease(clamp(lt / 0.4)), y=0.34, size=120)
    head(fr, ['Lo armaron', 'en CIVAC.'], CYAN, t, t0 + 0.1, kicker='Morelos · 1984–2017')
    lab2(fr, 'Recreación de la línea de ensamble', clamp(lt / 0.4))


def s_parts(fr, t, lt, dur):
    """Tsuru 1992 y Tsuru 2017 casi iguales; luego vista explotada: refacciones por todos lados."""
    t0 = t - lt
    fr.floor = 0.5
    th = T(('c0', 4, 'hay'), default=t0 + 2.4)
    if t < th - 0.15:
        fr.cam = Cam(target=(0, 0.7, 0), dist=vfit(10.5), yaw=20 + lt * 3, pitch=14)
        fr.meshes += M.place(M.tsuru('blanco', taxi=False), z=1.6)
        fr.meshes += M.place(M.tsuru('blanco', taxi=False), z=-1.6)
        ui_text3(fr, (0, 1.9, 1.6), '1992', 46, a=1, col=AMBER, fk='mono')
        ui_text3(fr, (0, 1.9, -1.6), '2017', 46, a=1, col=AMBER, fk='mono')
        ui_text3(fr, (0, 2.6, 0), '=', 80, a=clamp((lt - 0.6) / 0.3), col=LGREEN, fk='mono')
        head(fr, ['25 años', 'casi igual.'], CYAN, t, t0 + 0.1, kicker='Sin cambios de modelo')
    else:
        lt2 = t - th
        fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(9.0), yaw=35 + lt2 * 10, pitch=20)
        k = eout(clamp(lt2 / 1.2))
        car = M.tsuru('cdmx', taxi=False)
        fr.meshes += car[:2]
        for m in car[2:]:
            c = m.V.mean(0)
            v = c - np.array([0, 0.6, 0])
            v[1] *= 2.0
            n = v / (np.linalg.norm(v) + 1e-6)
            fr.meshes.append(m.tf(t=tuple(n * 0.8 * k + np.array([0, 0.3 * k, 0]))))
        for i, (p, txt) in enumerate((((2.6, 0.9, 0.7), 'Faros'), ((1.4, 0.7, 1.5), 'Llantas'), ((2.9, 0.6, -0.4), 'Defensa'), ((-2.8, 0.9, -0.8), 'Calaveras'))):
            ui_label3(fr, p, txt, a=clamp((lt2 - 0.6 - i * 0.15) / 0.3), side=1 if i % 2 == 0 else -1, length=50, up=60)
        head(fr, ['Refacciones', 'en cada esquina.'], CYAN, t, th, kicker='Baratas y fáciles de hallar')
    lab2(fr, 'Recreación', clamp(lt / 0.4))


def s_taxi(fr, t, lt, dur):
    """El Vocho verde se va y llega el Tsuru; luego fotos reales de Tsurus taxi en las calles."""
    t0 = t - lt
    fr.floor = 0.0
    k = clamp(lt / 1.6)
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(9.5), yaw=20 + lt * 2, pitch=10)
    street(fr)
    vx = lerp(0.0, -16.0, ease(k))
    fr.meshes += M.place(M.vocho((60, 150, 80), spin=lt * 600), x=vx, z=-1.8, ry=180)
    tx = lerp(14.0, 0.0, eout(clamp((lt - 0.2) / 1.4)))
    fr.meshes += M.place(M.tsuru('cdmx', spin=-tx * 120), x=tx, z=1.0, ry=0)
    tp = 1.4
    if lt > tp:
        ph = [('tsuru_taxi_cdmx.jpg', -0.9, 2.5), ('tsuru_san_cosme.jpg', 0.0, 2.3), ('tsuru_taxi2014.jpg', 0.9, 2.6)]
        for i, (nm, off, y) in enumerate(ph):
            a = appear(t, t0 + tp + i * 0.25, 0.4)
            if a <= 0:
                continue
            fr.meshes.append(S.photo(nm, w=2.4 * a, x=off * 1.5, y=y - 0.3 * i, z=2.2 + i * 0.3, ry=20 - lt * 2, rz=(i - 1) * 4, ar=4 / 3))
        credit(fr, clamp((lt - tp) / 0.3))
    ui_text3(fr, (vx, 2.0, -1.8), 'Vocho', 34, a=clamp(1 - k * 1.5), col=MUTED)
    head(fr, ['El taxi de', 'la CDMX.'], CYAN, t, t0 + 0.1, kicker='Reemplazó al Vocho')


def s_sales(fr, t, lt, dur):
    """Fotos reales de flotas de Tsurus; luego duelo de ventas: columna de 2.4 M (Tsuru) vs 1.7 M (Vocho)."""
    t0 = t - lt
    tb = T(('c0', 6, 'millones'), ('c0', 6, '2.4'), default=t0 + 2.6) - 0.35
    if t < tb:
        fr.floor = 0.0
        fr.cam = Cam(target=(0, 1.6, 0), dist=vfit(7.5), yaw=lt * 4, pitch=6)
        ph = [('tsuru_cancun.jpg', 0, 2.75, 2.3), ('tsuru_taxi2007.jpg', -1, 1.0, 4 / 3), ('tsuru_aztecas.jpg', 1, 1.0, 4 / 3)]
        for i, (nm, c, y, ar) in enumerate(ph):
            a = appear(t, t0 + i * 0.2, 0.4)
            fr.meshes.append(S.photo(nm, w=(3.4 if c == 0 else 2.2) * a, x=c * 1.25, y=y, z=-0.2 * abs(c), ry=-c * 8, ar=ar))
        credit(fr, clamp(lt / 0.3))
        head(fr, ['En todo', 'México.'], CYAN, t, t0 + 0.1, kicker='Taxis Tsuru reales')
    else:
        lt2 = t - tb
        fr.floor = 0.5
        fr.cam = Cam(target=(0, 1.5, 0), dist=vfit(9.0), yaw=-15 + lt2 * 5, pitch=12)
        k = eout(clamp(lt2 / 1.6))
        h1, h2 = 2.4 * 1.2 * k, 1.7 * 1.2 * k
        fr.meshes.append(box(1.6, max(0.01, h1), 1.6, (222, 42, 128), shadow=0.3, base=True, gloss=0.4).tf(t=(-1.5, 0, 0)))
        fr.meshes.append(box(1.6, max(0.01, h2), 1.6, (60, 150, 80), shadow=0.3, base=True, gloss=0.4).tf(t=(1.5, 0, 0)))
        fr.meshes += M.place(M.tsuru('cdmx', parts=True), x=-1.5, y=h1, s=0.36, ry=-30)
        fr.meshes += M.place(M.vocho((60, 150, 80)), x=1.5, y=h2, s=0.4, ry=-30)
        ui_text3(fr, (-1.5, h1 + 1.0, 0), f'{2.4 * k:.1f} M', 46, a=1, col=INK, fk='mono')
        ui_text3(fr, (1.5, h2 + 1.0, 0), f'{1.7 * k:.1f} M', 46, a=1, col=INK, fk='mono')
        ui_text3(fr, (-1.5, -0.35, 1.0), 'TSURU', 30, a=1, col=(255, 120, 180), fk='mono')
        ui_text3(fr, (1.5, -0.35, 1.0), 'VOCHO', 30, a=1, col=LGREEN, fk='mono')
        head(fr, ['Le ganó', 'al Vocho.'], CYAN, t, tb, kicker='Unidades vendidas en México')
        lab2(fr, 'Fuentes: Nissan y Motorpasión', clamp(lt2 / 0.4))


def s_lack(fr, t, lt, dur):
    """Rayos X de lo que no tenía: volante sin bolsa de aire y frenos sin ABS."""
    t0 = t - lt
    fr.floor = 0.4
    tf = T(('c0', 7, 'frenos'), default=t0 + 3.0) - 0.2
    car = M.tsuru('cdmx')
    ghost(fr, car[:2], CYAN, 0.45, 1.2)
    fr.meshes += M.interior()
    fr.meshes += M.engine(lt)
    abs_beat = t >= tf
    for x in M.WHEELS_X:
        for z in (0.73, -0.73):
            wm = M.wheel(x, z, lt * 200)
            if abs_beat and x > 0 and z > 0:
                ghost(fr, wm[:1], CYAN, 0.6, 1.2)
            else:
                fr.meshes += wm
            fr.meshes += M.brake(x, z)
    if lt < 1.0:
        xring(fr, lerp(2.5, -2.5, ease(lt / 1.0)))
    if t < tf:
        fr.cam = Cam(target=(0.5, 0.95, 0.36), dist=vfit(3.2), yaw=-70 + lt * 4, pitch=12)
        ka = clamp((lt - 0.8) / 0.4)

        def bag(d, cam, ka=ka):
            th = np.linspace(0, 2 * math.pi, 40)
            P = np.stack([np.full_like(th, 0.5), 0.98 + 0.3 * np.sin(th), 0.36 + 0.3 * np.cos(th)], 1)
            line3(d, cam, P, REDX, 3.0, dash=16, a=ka)
        fr.over.append(bag)
        ui_x3(fr, (0.45, 0.98, 0.36), 80, a=ka)
        ui_label3(fr, (0.5, 1.3, 0.36), 'Bolsa de aire', sub='no tenía', a=ka, side=1, length=60, up=160)
        head(fr, ['Lo que', 'no tenía.'], CYAN, t, t0 + 0.1, kicker='Rayos X')
    else:
        lt2 = t - tf
        fr.cam = Cam(target=(1.3, 0.5, 0.5), dist=vfit(3.6), yaw=35 + lt2 * 6, pitch=12)
        kb = clamp((lt2 - 0.2) / 0.4)
        ui_x3(fr, (1.3, 0.3, 0.6), 90, a=kb)
        ui_label3(fr, (1.42, 0.38, 0.62), 'Frenos ABS', sub='no tenía', a=kb, side=1, length=60, up=260)
        head(fr, ['Sin ABS.'], CYAN, t, tf, kicker='Las llantas se podían bloquear')
    lab2(fr, 'Recreación · esquema simplificado', clamp(lt / 0.4))


def s_crash(fr, t, lt, dur):
    """Prueba de choque frontal (recreación): el Tsuru pega contra la barrera y la cabina se colapsa; 0 estrellas."""
    t0 = t - lt
    fr.floor = 0.5
    ti = 0.9
    fr.cam = Cam(target=(1.2, 0.7, 0), dist=vfit(8.5) - min(lt, ti) * 0.8, yaw=22 - lt * 3, pitch=14)
    xb = 2.45
    fr.meshes.append(box(0.6, 1.0, 1.6, (240, 210, 60), shadow=0.3, base=True, gloss=0.2).tf(t=(xb + 0.3, 0, 0.35)))
    fr.meshes.append(box(1.4, 1.6, 2.6, (70, 74, 82), shadow=0.3, base=True, gloss=0.1).tf(t=(xb + 1.3, 0, -0.2)))
    if lt < ti:
        dx = lerp(-7.0, 0.3, lt / ti)
        kc = 0.0
    else:
        kc = eout(clamp((lt - ti) / 0.35))
        dx = 0.3 + 0.9 * kc  # la parte trasera sigue avanzando; el frente queda pegado a la barrera
    car = M.tsuru('cdmx', taxi=False, spin=-dx * 120)
    car = [m.tf(t=(dx, 0, 0)) for m in car]
    if kc > 0:
        car = crush(car, kc, dx)
    fr.meshes += car
    if lt > ti:
        rng = np.random.RandomState(3)
        pts = rng.uniform(-1, 1, (40, 3))
        kk = clamp((lt - ti) / 0.8)

        def deb(d, cam):
            for p in pts:
                q = np.array([xb - 0.2 + p[0] * 0.3 - kk * 1.2 * abs(p[0]), 0.7 + p[1] * 0.5 + kk * 0.6 * p[2], p[2] * 0.9])
                dot3(d, cam, q, 3.0, ICE, 1 - kk)
        fr.over.append(deb)
        if kc > 0.5:
            fr.ui.append(lambda img, d: None)
        stars_ui(fr, H * 0.235, ease(clamp((lt - ti - 0.3) / 0.3)), 0, '0 / 5', 'ADULTOS Y NIÑOS')
    head(fr, ['La cabina', 'se colapsó.'], CYAN, t, t0 + 0.1, kicker='Prueba de choque · Latin NCAP')
    lab2(fr, 'Recreación · no es video real', clamp(lt / 0.4), dotc=AMBER)


def s_deaths(fr, t, lt, dur):
    """Contador de 4,102 muertes (2007–2012) con figuras; cada figura = 50 personas."""
    t0 = t - lt
    fr.floor = 0.3
    fr.cam = Cam(target=(0, 0.7, 0), dist=vfit(9.5), yaw=lt * 8, pitch=22)
    ghost(fr, M.tsuru('cdmx', parts=False), (150, 160, 190), 0.35, 1.0)
    k = eout(clamp((lt - 0.3) / 4.0))
    v = 4102 * k
    n_on = int(82 * k)

    def f(img, d, n_on=n_on, lt=lt):
        cols, s = 10, 1.45
        x0, y0 = W / 2 - 4.5 * 84, H * 0.36
        for i in range(82):
            r, c = divmod(i, cols)
            on = i < n_on
            person_icon(d, x0 + c * 84, y0 + r * 72, s, REDX if on else (60, 70, 96), 1.0 if on else 0.6)
        draw_text(d, (W / 2, y0 + 9 * 72 - 6), 'CADA FIGURA = 50 PERSONAS', font('sb', 26), MUTED, 'mm', spacing=3)
    fr.ui.append(f)
    bigc(fr, fmt_int(v), '', a=1, y=0.28, size=100)
    head(fr, ['Más de 4,000', 'muertes.'], CYAN, t, t0 + 0.1, kicker='2007–2012 · choques con un Tsuru')
    lab2(fr, 'Datos: informe citado por Motorpasión (2016)', clamp(lt / 0.4), dotc=REDX)


def nom_tex():
    def f(d, im):
        d.rectangle((0, 0, 600, 110), fill=(30, 60, 120))
        draw_text(d, (300, 56), 'NORMA MEXICANA', font('xb', 46), (255, 255, 255), 'mm')
        draw_text(d, (300, 170), 'NOM-194', font('mono', 64), (20, 20, 22), 'mm')
        for i, s in enumerate(('Bolsas de aire', 'Frenos ABS', 'Cinturones')):
            y = 270 + i * 90
            d.line([(70, y), (90, y + 22), (128, y - 20)], fill=(40, 170, 80), width=10)
            draw_text(d, (160, y), s, font('b', 46), (20, 20, 22), 'lm')
    return tex(600, 560, (250, 250, 248, 255), f)


_NOM = {}


def s_norm(fr, t, lt, dur):
    """Hoja de la norma con lo que exige; luego el último Tsuru (Buen Camino, azul Orión) sale de la línea."""
    t0 = t - lt
    fr.floor = 0.5
    tl_ = T(('c0', 10, '2017'), ('c0', 10, 'en'), default=t0 + 2.3) - 0.3
    if t < tl_:
        fr.cam = Cam(target=(0, 1.2, 0), dist=vfit(7.5), yaw=-10 + lt * 5, pitch=10)
        if 'n' not in _NOM:
            _NOM['n'] = nom_tex()
        doc = box(2.4, 2.24, 0.04, (250, 250, 248), shadow=0.2, base=False)
        decal(doc, doc.FACE['front'], _NOM['n'])
        a = appear(t, t0 + 0.1)
        fr.meshes.append(doc.tf(s=max(0.01, a)).tf(ry=-8, t=(0.9, 1.9, 0.6)))
        fr.meshes += M.place(M.tsuru('cdmx'), x=-0.6, z=-1.2, s=0.7, ry=25)
        ui_x3(fr, (-0.6, 1.5, -1.2), 110, a=clamp((lt - 0.9) / 0.3))
        head(fr, ['Una norma', 'lo dejó fuera.'], CYAN, t, t0 + 0.1, kicker='Seguridad obligatoria')
    else:
        lt2 = t - tl_
        fr.cam = Cam(target=(0, 0.7, 0), dist=vfit(8.0), yaw=40 + lt2 * 6, pitch=14)
        fr.meshes.append(box(14, 0.02, 6, FLOORF, shadow=0.0, base=True, edge=False).tf(t=(0, -0.02, 0)))
        fr.meshes.append(box(14, 0.18, 1.3, (44, 46, 52), shadow=0.0, base=True, edge=False).tf(t=(-4, 0, 0)))
        x = lerp(-5.0, 0.6, eout(clamp(lt2 / 2.0)))
        fr.meshes += M.place(M.tsuru('orion', taxi=False, spin=-x * 120, lights=1.0), x=x, y=0.0)
        bigc(fr, 'MAYO 2017', 'EL ÚLTIMO TSURU', a=ease(clamp((lt2 - 0.3) / 0.4)), y=0.29, size=100)
        ui_label3(fr, (x - 1.2, 0.9, 0.8), 'Edición Buen Camino', sub='1,000 unidades · azul Orión', a=clamp((lt2 - 0.8) / 0.4), side=-1, length=40, up=-260)
        head(fr, ['Salió', 'el último.'], CYAN, t, tl_, kicker='Fin de producción')
    lab2(fr, 'Recreación', clamp(lt / 0.4))


def plant_building(lit, gate=0.0):
    ms = []
    ms.append(box(9.0, 3.2, 5.0, (196, 198, 204), shadow=0.0, base=True, gloss=0.2, cols={'top': (150, 154, 162)}))
    for i in range(6):  # techo de dientes de sierra
        x = -4.5 + 0.75 + i * 1.5
        ms.append(box(1.5, 0.8, 5.0, (170, 174, 182), shadow=0.0, base=True, gloss=0.3).tf(rz=-28, t=(x, 3.0, 0)))
    for i in range(10):
        on = lit[i] if i < len(lit) else 0
        ms.append(box(0.6, 0.6, 0.04, mix((40, 48, 64), (255, 214, 130), on), shadow=0.0, base=True, gloss=0.5).tf(t=(-3.9 + i * 0.86, 1.9, 2.52)))
    sign = box(3.6, 0.6, 0.06, (30, 40, 60), shadow=0.0, base=True)
    decal(sign, sign.FACE['front'], tex(480, 80, (30, 40, 60, 255), lambda d, im: draw_text(d, (240, 42), 'PLANTA CIVAC', font('xb', 48), (240, 240, 240), 'mm')))
    ms.append(sign.tf(t=(0, 2.55, 2.55)))
    ms.append(box(2.0 * (1 - gate) + 0.01, 1.6, 0.06, (90, 96, 106), shadow=0.0, base=True).tf(t=(-1.0 * gate, 0, 2.53)))
    return ms


def s_close(fr, t, lt, dur):
    """La planta CIVAC (recreación) apaga sus luces una por una; contador 1966→2026, 60 años."""
    t0 = t - lt
    fr.floor = 0.6
    fr.cam = Cam(target=(0, 1.4, 0), dist=vfit(17.0) - lt * 0.4, yaw=-25 + lt * 4, pitch=12)
    k = clamp((lt - 0.8) / 3.0)
    lit = [1.0 if (i + 1) / 10 > k else 0.0 for i in range(10)]
    fr.meshes += plant_building(lit, gate=0.0)
    fr.meshes.append(box(14, 0.02, 10, (70, 74, 82), shadow=0.0, base=True, edge=False).tf(t=(0, -0.02, 2)))
    v = int(lerp(1966, 2026, eout(clamp(lt / 2.4))))
    bigc(fr, f'1966 – {v}', '60 AÑOS · CERRÓ EL 27 DE MARZO DE 2026', a=ease(clamp(lt / 0.4)), y=0.27, size=96)
    head(fr, ['Cerró', 'CIVAC.'], CYAN, t, t0 + 0.1, kicker='La planta que lo vio nacer')
    lab2(fr, 'Recreación · dato: Expansión, 27-mar-2026', clamp(lt / 0.4))


def s_share(fr, t, lt, dur):
    """Cierre: sello, Sí/No; al final el taxi vuelve a llegar por la avenida como en el gancho (loop)."""
    t0 = t - lt
    fr.floor = 0.0
    tl = dur - 1.6  # el taxi llega igual que en el segundo 0
    if lt < tl:
        fr.cam = Cam(target=(0, 0.75, 0), dist=vfit(8.6), yaw=-30 + lt * 6, pitch=12)
        street(fr)
        fr.meshes += M.place(M.tsuru('cdmx', lights=1.0), x=0.0)
    else:
        lt2 = lt - tl
        fr.cam = hook_cam(lt2)
        x, spin = hook_car(lt2)
        street(fr)
        fr.meshes += M.place(M.tsuru('cdmx', spin=spin, lights=1.0), x=x)
    kt = clamp((lt - tl + 0.3) / 0.3)

    def f(img, d, lt=lt):
        yy = H * 0.64
        a = ease(clamp((lt - 1.4) / 0.4)) * (1 - kt)
        pill(img, d, W / 2 - 170, yy, '  SÍ  ', a, size=54, dotc=LGREEN)
        pill(img, d, W / 2 + 170, yy, '  NO  ', a, size=54, dotc=LASER)
        draw_text(d, (W / 2, H * 0.29), 'MENTE EN ÓRBITA', font('mono', 60), INK, 'mm', a=ease(clamp(lt / 0.5)) * (1 - kt), spacing=5)
    fr.ui.append(f)
    if kt < 1:
        head(fr, ['Mándaselo a quien', 'tuvo un Tsuru.'], CYAN, t, t0 + 0.1, kicker='¿Te subirías hoy a uno?')


SHOTS = [(('c0', 0), s_hook), (('c0', 1), s_xray), (('c0', 2), s_engine), (('c0', 3), s_plant), (('c0', 4), s_parts),
         (('c0', 5), s_taxi), (('c0', 6), s_sales), (('c0', 7), s_lack), (('c0', 8), s_crash), (('c0', 9), s_deaths),
         (('c0', 10), s_norm), (('c0', 11), s_close), (('c0', 12), s_share)]

if __name__ == '__main__':
    S.main(SHOTS, {})
