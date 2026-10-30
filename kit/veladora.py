"""Reel diario: La flama de tu veladora en el espacio (30-oct-2026). Tema visual: orbita.
Escenas: ofrenda con veladora (gancho) · veladora en órbita, flama azul · rayos X de la flama · aire caliente sube ·
aire fresco por abajo · hollín que brilla · 2º gancho: sin arriba ni abajo (estación) · oxígeno por difusión ·
Tierra vs órbita lado a lado · contador Mir 10 → 45 min · tamaño 1.5 cm y 50 W vs 5 W · cierre Sí/No · loop.
Uso: MOTOR_TEMA=orbita GTA_FMT=v VIDEO_TL=/home/claude/tl_veladora.json python3 veladora.py info|preview T out.png|sheet out.jpg t..|chunk A B out.mp4"""
import os
os.environ.setdefault('MOTOR_TEMA', 'orbita')
os.environ.setdefault('GTA_FMT', 'v')
os.environ.setdefault('VIDEO_TL', '/home/claude/tl_veladora.json')
import math
import numpy as np
import escenas as S
import entornos as EN
from escenas import *  # noqa: F401,F403
from starlink import scan_ring, lab, bigc, cnt, earth, atmo, CYAN, ICE, LASER, LGREEN, AMBER, WHITE
from yema import flower, MARI, PAPEL

WAX = (242, 236, 222)
WAX2 = (226, 214, 190)
GLASS = (196, 214, 222)
LABEL = (190, 40, 60)
WICK = (30, 26, 24)
HOTR = (255, 90, 40)
COLD = (90, 170, 255)
FY = [(255, 120, 20), (255, 170, 40), (255, 214, 90), (255, 244, 200)]
FB = [(30, 60, 170), (50, 100, 230), (90, 150, 255), (150, 200, 255)]
ISS_W = (200, 204, 212)


def veladora(x=0.0, y=0.0, z=0.0, s=1.0, rx=0.0, rz=0.0):
    """Veladora mexicana: vaso alto de vidrio, cera blanca, banda de color con estampa y pabilo."""
    ms = [
        cyl(0.36 * s, 1.5 * s, GLASS, n=36, top=WAX, shadow=0.35, gloss=0.8),
        cyl(0.37 * s, 0.7 * s, LABEL, n=36, shadow=0, gloss=0.4, y0=0.35 * s),
        cyl(0.372 * s, 0.08 * s, (250, 200, 60), n=36, shadow=0, gloss=0.5, y0=0.36 * s),
        cyl(0.372 * s, 0.08 * s, (250, 200, 60), n=36, shadow=0, gloss=0.5, y0=0.96 * s),
        torus(0.36 * s, 0.025 * s, (220, 236, 244), nu=36, nv=8, gloss=0.8).tf(t=(0, 1.5 * s, 0)),
        cyl(0.018 * s, 0.14 * s, WICK, n=8, shadow=0, y0=1.5 * s),
    ]
    return [m.tf(rx=rx, rz=rz, t=(x, y, z)) for m in ms]


def wick_top(x=0.0, y=0.0, z=0.0, s=1.0):
    return (x, y + 1.64 * s, z)


def _shape(k, n=48):
    """Contorno de la flama en coordenadas locales (unidades de alto): k=0 gota (Tierra), k=1 media burbuja (órbita)."""
    pts = []
    for i in range(n):
        u = i / (n - 1)            # 0 abajo-izq → 1 abajo-der, pasando por arriba
        th = math.pi * (1.5 - 2 * u)  # ángulo alrededor
        # gota: alta y estrecha
        v = (1 - math.cos(2 * math.pi * u)) / 2   # 0 en la base, 1 en la punta
        side = -1 if u < 0.5 else 1
        yd = -0.08 + 1.0 * v
        xd = side * 0.30 * math.sin(math.pi * min(1.0, v * 1.0)) ** 0.8 * (1 - v) ** 0.35 * 1.25
        # media burbuja: círculo un poco achatado abajo
        xs = 0.36 * math.cos(th)
        ys = 0.26 + 0.36 * math.sin(th)
        ys = max(ys, -0.04)
        pts.append((lerp(xd, xs, k), lerp(yd, ys, k)))
    return pts


def flame(fr, base, h=0.6, k=0.0, lt=0.0, a=1.0, layer='over'):
    """Flama dibujada en capas (las capas brillan con el resplandor del tema). base = punta del pabilo."""
    def f(d, cam):
        if a <= 0.02:
            return
        sp, z = cam.proj([base, (base[0], base[1] + h, base[2])])
        if z[0] < 0.2:
            return
        (bx, by), (tx, ty) = sp[0], sp[1]
        sc = math.hypot(tx - bx, ty - by)
        fl = 1 + (1 - k) * 0.06 * math.sin(lt * 17) + (1 - k) * 0.04 * math.sin(lt * 29)
        pts = _shape(k)
        cols = [mix(FY[i], FB[i], k) for i in range(4)]
        if k > 0.5:
            cols = [mix(c, (0, 0, 0), (k - 0.5) * 0.5) for c in cols[:-1]] + [mix(cols[-1], (20, 30, 80), (k - 0.5) * 1.2)]
        for j, s in enumerate((1.0, 0.78, 0.56, 0.34)):
            c = mix(tuple(int(v) for v in S.BG) if hasattr(S, 'BG') else (0, 0, 0), cols[j], a)
            poly = [(bx + sc * px * s * (1 + 0.15 * (1 - k) * (1 - s)), by - sc * fl * (py * s + (1 - s) * 0.05)) for px, py in pts]
            d.polygon(poly, fill=tuple(int(v) for v in c))
        if k < 0.6:  # base azul de la flama terrestre
            rr = sc * 0.14
            d.ellipse((bx - rr, by - rr * 0.8, bx + rr, by + rr * 0.6), fill=tuple(int(v) for v in mix(cols[0], (60, 110, 255), 0.8)))
    getattr(fr, layer).append(f)


def particles(fr, cen, n, lt, mode, col, r=5, a=1.0, seed=1, R=1.0):
    """mode 'up': suben (aire caliente); 'in': entran por abajo y suben; 'diff': llegan lento desde todas direcciones."""
    rng = np.random.RandomState(seed)
    P = rng.uniform(0, 1, (n, 3))

    def f(d, cam):
        for i in range(n):
            ph = (P[i, 0] + lt * (0.35 if mode != 'diff' else 0.12)) % 1.0
            if mode == 'up':
                x = cen[0] + (P[i, 1] - 0.5) * 0.4 * R * (1 + ph)
                y = cen[1] + ph * 2.2 * R
                z = cen[2] + (P[i, 2] - 0.5) * 0.4 * R
            elif mode == 'in':
                ang = P[i, 1] * 2 * math.pi
                if ph < 0.5:
                    q = ph / 0.5
                    rad = R * (1.4 - 1.25 * q)
                    x, y, z = cen[0] + rad * math.cos(ang), cen[1] - 0.25 * R, cen[2] + rad * math.sin(ang)
                else:
                    q = (ph - 0.5) / 0.5
                    x, y, z = cen[0] + 0.1 * math.cos(ang), cen[1] - 0.25 * R + q * 1.6 * R, cen[2] + 0.1 * math.sin(ang)
            else:
                th = P[i, 1] * 2 * math.pi
                phi = math.acos(2 * P[i, 2] - 1)
                rad = R * (1.6 - 1.25 * ph)
                x = cen[0] + rad * math.sin(phi) * math.cos(th)
                y = cen[1] + rad * math.cos(phi)
                z = cen[2] + rad * math.sin(phi) * math.sin(th)
            fade = math.sin(math.pi * ph)
            dot3(d, cam, (x, y, z), r, col, a * fade)
    fr.over.append(f)


def arrow3(fr, p0, p1, col, a=1.0, w=4.0):
    def f(d, cam):
        line3(d, cam, [p0, p1], col, w, a=a)
        dx, dy, dz = (p1[i] - p0[i] for i in range(3))
        L = math.sqrt(dx * dx + dy * dy + dz * dz) or 1
        ux, uy, uz = dx / L, dy / L, dz / L
        back = (p1[0] - ux * 0.18, p1[1] - uy * 0.18, p1[2] - uz * 0.18)
        side = (-uy * 0.09, ux * 0.09, 0)
        line3(d, cam, [(back[0] + side[0], back[1] + side[1], back[2]), p1, (back[0] - side[0], back[1] - side[1], back[2])], col, w, a=a)
    fr.over.append(f)


def ofrenda(fr, lt):
    EN.env(fr, 'ofrenda')
    for i, (w, h, z) in enumerate(((4.4, 0.6, -0.6), (3.4, 0.6, -1.0), (2.4, 0.6, -1.4))):
        fr.meshes.append(box(w, h, 0.9, (236, 236, 240) if i % 2 else (120, 60, 140), shadow=0.3, base=True, edge=False).tf(t=(0, i * 0.6, z)))
    for i in range(8):
        fr.meshes += flower(0.4, x=-1.9 + i * 0.54, y=0.6, z=-0.25, ry=i * 50, rich=False)
    for i in range(4):
        fr.meshes += flower(0.34, x=-1.4 + i * 0.95, y=1.2, z=-0.65, ry=i * 70, rich=False)
    fr.meshes.append(sphere(0.32, (196, 128, 62), nu=28, nv=14, gloss=0.3).tf(s=(1, 0.6, 1), t=(-0.8, 1.86, -1.25)))
    fr.meshes.append(sphere(0.12, (176, 108, 50), nu=16, nv=8, gloss=0.3).tf(t=(-0.8, 2.08, -1.25)))

    def papel(img, d, lt=lt):
        for i in range(9):
            x = W * (0.08 + i * 0.105)
            c = (PAPEL, (250, 140, 20), (60, 150, 220), (130, 60, 180))[i % 4]
            y = H * 0.215 + 6 * math.sin(lt * 2 + i)
            d.polygon([(x - 46, y), (x + 46, y), (x + 46, y + 70), (x, y + 92), (x - 46, y + 70)], fill=c)
    fr.ui.insert(0, papel)


def space(fr, lt, earth_y=-9.0):
    """Órbita: la Tierra abajo (el fondo azul de marca va en temas del espacio)."""
    EN.reset()
    fr.floor = 0.0
    c = (0, earth_y, -4)
    fr.meshes.append(earth(7.0, spin=lt * 2).tf(t=c))
    fr.under.append(lambda d, cam: atmo(d, cam, c, 7.0, 0.8))


# ================================================================== escenas
def s_hook(fr, t, lt, dur, loop=False):
    t0 = t - lt
    ofrenda(fr, lt)
    fr.cam = Cam(target=(0.6, 1.9, 0.6), dist=vfit(3.6) - lt * 0.12, yaw=-22 + lt * 5, pitch=10)
    fr.meshes += veladora(0.6, 0, 0.6)
    on = clamp((lt - 0.25) / 0.3) if not loop else 1.0
    flame(fr, wick_top(0.6, 0, 0.6), h=0.55 * on, k=0, lt=lt, a=on)
    head(fr, ['Prende una veladora', 'de tu altar.'], CYAN, t, t0 + 0.05, kicker='Ahora sí…' if loop else 'Día de Muertos')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_space(fr, t, lt, dur):
    t0 = t - lt
    space(fr, lt)
    fr.cam = Cam(target=(0, 1.0, 0), dist=vfit(4.2) - lt * 0.2, yaw=-30 + lt * 9, pitch=8)
    fr.meshes += veladora(0, 0.2 + 0.08 * math.sin(lt * 1.3), 0, rz=6 * math.sin(lt * 0.9), rx=4)
    k = ease(clamp((lt - 0.8) / 1.6))
    flame(fr, wick_top(0, 0.2 + 0.08 * math.sin(lt * 1.3), 0), h=lerp(0.55, 0.42, k), k=k, lt=lt)
    head(fr, ['Llévala al espacio…'], CYAN, t, t0 + 0.05, kicker='En órbita')
    if k > 0.5:
        ui_pill(fr, '  ¡UNA BOLITA AZUL!  ', a=ease(clamp((k - 0.5) / 0.3)), dotc=COLD)
    lab(fr, 'Recreación · Escala exagerada', clamp(lt / 0.4), where='bl')


def s_xray(fr, t, lt, dur):
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 1.8, 0), dist=vfit(2.4), yaw=-25 + lt * 8, pitch=10)
    ts, te = t0 + 0.05, t0 + 0.8
    ys, k = scan_ring(fr, t, ts, te, 2.5, 1.0, center=(0, 0, 0), r=0.9)
    fr.meshes += veladora(0, 0, 0)
    flame(fr, wick_top(), h=0.8, k=0, lt=lt)
    e = ease(k)
    if e > 0.3:
        ui_label3(fr, (0.0, 1.66, 0), 'Base azul', sub='entra oxígeno', a=clamp((lt - 0.5) / 0.3), side=-1, length=120, up=-80)
        ui_label3(fr, (0.06, 2.2, 0), 'Hollín que brilla', sub='amarillo', a=clamp((lt - 0.7) / 0.3), side=1, length=110, up=90)
        ui_label3(fr, (0, 1.58, 0), 'Pabilo', sub='cera en vapor', a=clamp((lt - 0.9) / 0.3), side=1, length=120, up=-170)
    head(fr, ['Así se ve', 'por dentro.'], CYAN, t, t0 + 0.1, kicker='Rayos X')
    lab(fr, 'Recreación · Esquema simplificado', clamp(lt / 0.4))


def s_rise(fr, t, lt, dur):
    t0 = t - lt
    EN.env(fr, 'ofrenda')
    fr.cam = Cam(target=(0, 2.2, 0), dist=vfit(3.4), yaw=10 + lt * 5, pitch=6)
    fr.meshes += veladora(0, 0, 0)
    flame(fr, wick_top(), h=0.65, k=0, lt=lt)
    particles(fr, (0, 2.2, 0), 46, lt, 'up', HOTR, r=6, a=0.9, R=0.9)
    for dx in (-0.35, 0.35):
        arrow3(fr, (dx, 2.5, 0), (dx * 1.3, 3.5, 0), HOTR, a=ease(clamp((lt - 0.5) / 0.4)))
    ui_pill(fr, '  AIRE CALIENTE = PESA MENOS  ', a=ease(clamp((lt - 0.8) / 0.4)), dotc=HOTR)
    head(fr, ['El aire caliente', 'sube.'], CYAN, t, t0 + 0.1, kicker='Convección')
    lab(fr, 'Recreación', clamp(lt / 0.4), where='bl')


def s_inflow(fr, t, lt, dur):
    t0 = t - lt
    EN.env(fr, 'ofrenda')
    fr.cam = Cam(target=(0, 1.9, 0), dist=vfit(3.0), yaw=-30 + lt * 6, pitch=22)
    fr.meshes += veladora(0, 0, 0)
    st = 1 + 0.35 * ease(clamp((lt - 0.8) / 1.2))
    flame(fr, wick_top(), h=0.6 * st, k=0, lt=lt)
    particles(fr, (0, 1.75, 0), 40, lt, 'in', COLD, r=5, a=0.9, R=0.8, seed=4)
    particles(fr, (0, 2.3, 0), 20, lt, 'up', HOTR, r=5, a=0.7, R=0.7, seed=9)
    a = ease(clamp((lt - 0.4) / 0.4))
    for sx in (-1, 1):
        arrow3(fr, (sx * 1.1, 1.6, 0), (sx * 0.35, 1.68, 0), COLD, a=a)
    arrow3(fr, (0, 2.6, 0), (0, 3.5, 0), HOTR, a=a)
    ui_pill(fr, '  OXÍGENO NUEVO DESDE ABAJO  ', a=ease(clamp((lt - 1.0) / 0.4)), dotc=COLD)
    head(fr, ['Por eso se estira', 'hacia arriba.'], CYAN, t, t0 + 0.1, kicker='Aire fresco')
    lab(fr, 'Recreación', clamp(lt / 0.4), where='bl')


def s_soot(fr, t, lt, dur):
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 2.05, 0), dist=vfit(1.5) - lt * 0.04, yaw=lt * 10, pitch=4)
    fr.meshes += veladora(0, 0, 0)
    flame(fr, wick_top(), h=0.7, k=0, lt=lt, layer='under')
    rng = np.random.RandomState(7)
    P = rng.uniform(-1, 1, (60, 3))

    def f(d, cam, lt=lt):
        for i in range(60):
            ph = (P[i, 0] * 0.5 + 0.5 + lt * 0.3) % 1
            x = P[i, 1] * 0.1 * (1 - ph)
            y = 1.85 + ph * 0.6
            glowc = mix((40, 30, 26), (255, 230, 120), clamp(math.sin(math.pi * ph) * 1.4))
            dot3(d, cam, (x, y, P[i, 2] * 0.05), 5, glowc, 0.95)
    fr.over.append(f)
    ui_label3(fr, (0.05, 2.25, 0), 'Hollín', sub='carbón que brilla', a=ease(clamp((lt - 0.8) / 0.4)), side=1, length=120, up=80)
    head(fr, ['Ese amarillo', 'es hollín.'], CYAN, t, t0 + 0.1, kicker='Pedacitos de carbón')
    lab(fr, 'Escala exagerada', clamp(lt / 0.4))


def iss(fr):
    """Módulo de la estación: piso y paredes de paneles blancos con pasamanos."""
    for sx in (-1, 1):
        fr.meshes.append(box(0.1, 3.4, 5.0, ISS_W, shadow=0, gloss=0.3, base=False).tf(t=(sx * 2.0, 0.0, -1.0)))
        for zz in (-2.5, -1.0, 0.5):
            fr.meshes.append(box(0.06, 0.06, 0.8, (236, 196, 60), shadow=0, base=False).tf(t=(sx * 1.92, 1.6, zz)))
    fr.meshes.append(box(4.1, 0.1, 5.0, (180, 184, 192), shadow=0, base=False).tf(t=(0, -0.1, -1.0)))
    fr.meshes.append(box(4.1, 0.1, 5.0, (180, 184, 192), shadow=0, base=False).tf(t=(0, 3.3, -1.0)))
    for zz in (-3.0, -1.6, -0.2):
        fr.meshes.append(box(0.6, 0.05, 0.4, (240, 244, 255), shadow=0, base=False, gloss=1.0).tf(t=(0, 3.23, zz)))


def s_noup(fr, t, lt, dur):
    """2º gancho: la cámara gira y no hay arriba ni abajo; la veladora flota en la estación."""
    t0 = t - lt
    EN.reset()
    fr.floor = 0.0
    iss(fr)
    roll = 40 * math.sin(lt * 0.8)
    fr.cam = Cam(target=(0, 1.6, 0), dist=vfit(3.2), yaw=-10 + lt * 18, pitch=6, roll=roll)
    y = 1.0 + 0.1 * math.sin(lt * 1.1)
    fr.meshes += veladora(0, y, 0, rz=lt * 25, rx=10)
    particles(fr, (0, y + 1.6, 0), 30, lt, 'diff', HOTR, r=5, a=0.6, R=0.6, seed=12)

    def f(img, d, lt=lt):
        a = ease(clamp((lt - 0.6) / 0.4))
        pill(img, d, W / 2, H * 0.58, '  SIN ARRIBA NI ABAJO  ', a, size=44, dotc=AMBER)
    fr.ui.append(f)
    head(fr, ['Pero en órbita…'], AMBER, t, t0 + 0.05, kicker='¡Ojo!')
    lab(fr, 'Recreación · Estación espacial', clamp(lt / 0.4), where='bl')


def s_diff(fr, t, lt, dur):
    t0 = t - lt
    EN.reset()
    fr.floor = 0.0
    iss(fr)
    fr.cam = Cam(target=(0, 1.9, 0), dist=vfit(2.4), yaw=-20 + lt * 7, pitch=12)
    fr.meshes += veladora(0, 0.2, 0)
    k = ease(clamp((lt - 0.4) / 2.6))
    base = wick_top(0, 0.2, 0)
    flame(fr, base, h=lerp(0.6, 0.45, k), k=k, lt=lt)
    particles(fr, (base[0], base[1] + 0.15, base[2]), 70, lt, 'diff', COLD, r=5, a=0.85, R=0.75, seed=3)
    ui_pill(fr, '  OXÍGENO DESPACITO, POR TODOS LADOS  ', a=ease(clamp((lt - 0.8) / 0.4)), dotc=COLD)
    head(fr, ['Se vuelve', 'redonda.'], CYAN, t, t0 + 0.1, kicker='Como media burbuja')
    lab(fr, 'Recreación', clamp(lt / 0.4), where='bl')


def s_compare(fr, t, lt, dur):
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 1.8, 0), dist=vfit(4.0), yaw=lt * 3, pitch=6)
    for x, k in ((-0.9, 0.0), (0.9, 1.0)):
        fr.meshes += veladora(x, 0, 0)
        flame(fr, wick_top(x, 0, 0), h=0.6 if k == 0 else 0.45, k=k, lt=lt)

    def f(img, d, lt=lt):
        a = ease(clamp((lt - 0.3) / 0.4))
        pill(img, d, W * 0.3, H * 0.6, '  TIERRA  ', a, size=46, dotc=FY[1])
        pill(img, d, W * 0.7, H * 0.6, '  ÓRBITA  ', a, size=46, dotc=COLD)
        b = ease(clamp((lt - 1.2) / 0.4))
        pill(img, d, W * 0.66, H * 0.645, ' más fría · casi sin hollín ', b, size=34, dotc=COLD)
    fr.ui.append(f)
    head(fr, ['Por eso', 'se ve azul.'], CYAN, t, t0 + 0.1, kicker='Lado a lado')
    lab(fr, 'Recreación', clamp(lt / 0.4), where='bl')


def s_mir(fr, t, lt, dur):
    t0 = t - lt
    space(fr, lt, earth_y=-8.5)
    fr.cam = Cam(target=(0, 1.2, 0), dist=vfit(6.0), yaw=20 + lt * 5, pitch=10)
    # estación Mir simplificada: módulos cilíndricos y paneles
    for i, (x, l) in enumerate(((-1.4, 1.4), (0.0, 1.6), (1.5, 1.3))):
        fr.meshes.append(cyl(0.32, l, ISS_W, n=24, shadow=0, gloss=0.5).tf(rz=90, t=(x + l / 2, 1.6, -1.2)))
    for x in (-0.9, 0.9):
        fr.meshes.append(box(0.9, 0.03, 0.5, (40, 60, 120), shadow=0, gloss=0.8, base=False).tf(t=(x, 1.6, -0.5)))
        fr.meshes.append(box(0.9, 0.03, 0.5, (40, 60, 120), shadow=0, gloss=0.8, base=False).tf(t=(x, 1.6, -1.9)))
    v = cnt(45, t, t0 + 0.9, 2.4)

    def f(img, d, lt=lt, v=v):
        a = ease(clamp((lt - 0.4) / 0.4))
        x0, x1, y = W * 0.12, W * 0.88, H * 0.5
        d.rounded_rectangle((x0, y - 26, x0 + (x1 - x0) * 10 / 45, y + 26), 12, fill=FY[1])
        d.rounded_rectangle((x0, y + 50, x0 + (x1 - x0) * v / 45, y + 102), 12, fill=COLD)
        draw_text(d, (x0, y - 60), 'EN LA TIERRA: 10 min', font('sb', 40), INK, 'lm', a=a)
        draw_text(d, (x0, y + 140), f'EN LA MIR: {int(v)} min', font('sb', 40), INK, 'lm', a=a)
    fr.ui.append(f)
    bigc(fr, f'{int(v)} min', 'ardió la vela en la estación Mir', a=ease(clamp((lt - 0.6) / 0.4)), y=0.30)
    head(fr, ['La NASA', 'lo probó.'], CYAN, t, t0 + 0.1, kicker='Estación Mir · 1995')
    lab(fr, 'Recreación · Datos: NASA', clamp(lt / 0.4), where='bl')


def s_size(fr, t, lt, dur):
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 1.95, 0), dist=vfit(2.1), yaw=-15 + lt * 6, pitch=8)
    fr.meshes += veladora(0, 0, 0)
    base = wick_top()
    flame(fr, base, h=0.45, k=1.0, lt=lt)
    a = ease(clamp((lt - 0.3) / 0.4))

    def ruler(d, cam, a=a):
        y = base[1] - 0.02
        line3(d, cam, [(-0.36, y - 0.18, 0.5), (0.36, y - 0.18, 0.5)], INK, 3, a=a)
        for xx in (-0.36, 0.36):
            line3(d, cam, [(xx, y - 0.24, 0.5), (xx, y - 0.12, 0.5)], INK, 3, a=a)
    fr.over.append(ruler)

    def f(img, d, lt=lt):
        b = ease(clamp((lt - 1.4) / 0.4))
        x0, y = W * 0.18, H * 0.33
        d.rounded_rectangle((x0, y, x0 + W * 0.64, y + 46), 12, fill=FY[1])
        d.rounded_rectangle((x0, y + 80, x0 + W * 0.064 * b + 4, y + 126), 12, fill=COLD)
        draw_text(d, (x0, y - 30), 'TIERRA ≈ 50 W', font('sb', 38), INK, 'lm', a=b)
        draw_text(d, (x0, y + 160), 'ÓRBITA ≈ 5 W', font('sb', 38), INK, 'lm', a=b)
    fr.ui.append(f)
    bigc(fr, '1.5 cm', 'medía la flama', a=a, y=0.215)
    head(fr, ['10 veces', 'menos calor.'], CYAN, t, t0 + 0.1, kicker='Escala real')
    lab(fr, 'Datos: NASA', clamp(lt / 0.4))


def s_share(fr, t, lt, dur):
    t0 = t - lt
    ofrenda(fr, lt)
    fr.cam = Cam(target=(0, 1.6, 0), dist=vfit(6.0) - lt * 0.15, yaw=-18 + lt * 5, pitch=10)
    for x in (-1.2, 1.2):
        fr.meshes += veladora(x, 0, 0.4, s=0.8)
        flame(fr, wick_top(x, 0, 0.4, 0.8), h=0.45, k=0, lt=lt + x)

    def f(img, d, lt=lt):
        yy = H * 0.66
        a = ease(clamp((lt - 1.2) / 0.4))
        pill(img, d, W / 2 - 170, yy, '  SÍ  ', a, size=54, dotc=LGREEN)
        pill(img, d, W / 2 + 170, yy, '  NO  ', a, size=54, dotc=LASER)
        draw_text(d, (W / 2, H * 0.29), 'MENTE EN ÓRBITA', font('mono', 60), INK, 'mm', a=ease(clamp(lt / 0.5)), spacing=5)
    fr.ui.append(f)
    head(fr, ['Mándaselo a quien', 'pone la ofrenda.'], CYAN, t, t0 + 0.1, kicker='¿Lo sabías?')


def s_loop(fr, t, lt, dur):
    s_hook(fr, t, lt, dur, loop=True)


SHOTS = [(('c0', 0), s_hook), (('c0', 1), s_space), (('c0', 2), s_xray), (('c0', 3), s_rise), (('c0', 4), s_inflow),
         (('c0', 5), s_soot), (('c0', 6), s_noup), (('c0', 7), s_diff), (('c0', 8), s_compare), (('c0', 9), s_mir),
         (('c0', 10), s_size), (('c0', 11), s_share), (('c0', 12), s_loop)]

if __name__ == '__main__':
    S.main(SHOTS, {})
