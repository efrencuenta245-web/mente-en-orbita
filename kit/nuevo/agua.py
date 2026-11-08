"""Reel diario: «Tu agua hierve… sin llegar a 100.» Mar 10-nov-2026, 10:00. Voz Isaac. Estilo rápido.
Inicio tipo 12 (reloj: la aguja del termómetro de cocina corre hacia el 100, se estrella contra el 92 y se congela ahí,
con «100°» de cristal gigante detrás y el título que cae con golpe). Datos: en la Ciudad de México (2 240 m) el agua
hierve a unos 92 °C (Tutiempo, abr-2025; Cafessio calcula 92.6 °C, jul-2026), en Veracruz (nivel del mar) a 100 °C y
en Toluca (2 660 m) a unos 91 °C (Cafessio); a más altura los alimentos tardan más en cocerse (Tutiempo); con más fuego
el agua «hierve más rápido, no más caliente» (Univ. de Illinois, Physics Van); la olla exprés sube la presión y con ella
la temperatura de hervor (HyperPhysics: ~121 °C a 15 psi sobre la presión ambiente; en la CDMX es menor, pero pasa de
100 °C). Foto real: NASA ISS062-E-112947 (México desde la Estación Espacial, 23-mar-2020, dominio público).
Olla, estufa, tanque de gas y olla exprés: RECREACIÓN sin marcas. Fuentes en guiones/2026-11-10_agua.txt."""
import math, os, re, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'agua'
TXT = ['Tu agua hierve… sin llegar a 100.',
       'En la Ciudad de México hierve a unos 92 °C.',
       'Y no es tu estufa: es el aire que tienes encima.',
       'En Veracruz, junto al mar, el aire pesa más y el agua llega a 100 °C.',
       'En Toluca, a casi 2,700 metros, hierve a unos 91 °C.',
       'Cada burbuja de vapor tiene que ganarle al peso de ese aire: con menos aire, escapa antes.',
       'Por eso tus frijoles tardan más en la Ciudad de México.',
       'Y aquí está el error: subirle todo el fuego a la olla.',
       'Ya hirviendo, más fuego no la calienta más: solo hierve más fuerte.',
       'El agua se evapora, gastas más gas… y los frijoles se cuecen igual.',
       'La olla exprés sí cambia todo: atrapa el vapor y sube la presión.',
       'Adentro, por fin, el agua pasa de 100 °C y todo se cuece mucho más rápido.',
       'Así que, ya hirviendo, bájale a fuego medio y ahorra gas.',
       'Mándaselo a quien le sube todo el fuego a la olla.',
       'Porque su agua también hierve… sin llegar a 100.']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-10_agua_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)

PELTRE = (30, 70, 150)
BLANCO_P = (236, 236, 240)
AGUA = (130, 160, 182)
FRIJOL = (96, 50, 38)
ACERO = (150, 156, 166)
NEGRO = (26, 26, 30)
AZUL_F = (90, 150, 255)
NARANJA = (255, 150, 60)
AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 60, 50)
VAPOR = (255, 190, 120)


# ================================================================== utilidades
def _pal(i):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split()


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


_W = []


def _words():
    if not _W:
        f = f'/home/claude/words_{TEMA}.json'
        if os.path.exists(f):
            d = json.load(open(f))
            d = d.get('words', d) if isinstance(d, dict) else d
            _W.extend(w for w in d if w.get('type', 'word') == 'word' and not w['text'].startswith('['))
    return _W


def wt(i, k):
    """Segundos desde el inicio de la frase i hasta su palabra k."""
    n = len(_pal(i))
    k = max(0, min(k, n - 1))
    W_ = _words()
    if len(W_) == sum(len(_pal(j)) for j in range(len(VOZ))):
        n0 = sum(len(_pal(j)) for j in range(i))
        return W_[n0 + k]['start'] - W_[n0]['start']
    return (TE(i) - TT(i)) * k / n


def cam(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch=8, tx=0.0, ty=0.0, tz=0.0, roll=0.0):
    return (u, dict(tx=tx, ty=ty, tz=tz, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def check(img, fx, x, y, k, txt, col=VERDE):
    pill(img, fx, x, y, '✓ ' + txt, eout(k), size=36, border=col)


def tache(img, fx, x, y, k, txt):
    pill(img, fx, x, y, '✗ ' + txt, eout(k), size=36, border=ROJO, col=(255, 200, 196))


def texto(img, fx, x, y, txt, size, col, k=1.0, glow=0.45, f='sansx', anchor='mm'):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, k), anchor=anchor)
    ImageDraw.Draw(fx).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, glow * k), anchor=anchor)


def flat(m, glow=None):
    m.flat = True
    if glow is not None:
        m.glow = glow
    return m


def dibujar(fr, ms):
    """draw_objects + tapa en la capa que brilla (fx) lo que queda detrás de los objetos (flamas, letras de cristal):
    sin esto el brillo de las flamas se ve a través de la olla."""
    draw_objects(fr, ms)
    caras = M._faces(fr.cam, ms)
    for z, mi, fi_, n, vd, Sx in caras:
        if getattr(ms[mi], 'glow', None) is None:
            fr.df.polygon([tuple(p) for p in Sx], fill=(0, 0, 0))
    for z, mi, fi_, n, vd, Sx in caras:
        g = getattr(ms[mi], 'glow', None)
        if g is not None:
            fr.df.polygon([tuple(p) for p in Sx], fill=g)


# ================================================================== objetos (RECREACIÓN, sin marcas)
def olla(t=(0, 0, 0), s=1.0, frijoles=0.0, tt=0.0, ry=0.0, agua=AGUA, entra=None):
    """Olla de peltre azul con borde blanco, llena de agua (y frijoles que flotan)."""
    ms = [named(M3.cyl(0.55, 0.62, PELTRE, n=36, top=agua, shadow=0, gloss=0.6, r2=0.58), 'olla', rim=0.7, gloss=0.6),
          named(M3.torus(0.58, 0.03, BLANCO_P, nu=36, nv=6, gloss=0.5).tf(t=(0, 0.62, 0)), 'borde', rim=0.4)]
    for sx in (-1, 1):
        ms.append(named(M3.rbox(0.2, 0.06, 0.11, 0.025, NEGRO, n=2, shadow=0, gloss=0.4).tf(t=(sx * 0.68, 0.5, 0)), 'asa', rim=0.4))
    if frijoles > 0.01:
        rng = np.random.RandomState(3)
        for i in range(int(16 * frijoles)):
            a = rng.uniform(0, 2 * math.pi)
            r = 0.44 * math.sqrt(rng.uniform(0.03, 1))
            b = 0.014 * math.sin(tt * 9 + i * 1.7)
            f = M3.sphere(0.06, FRIJOL, nu=10, nv=6, shadow=0, gloss=0.55).tf(s=(1.0, 0.5, 0.66), ry=i * 47 + tt * 30 * (i % 3 - 1),
                                                                             t=(r * math.cos(a), 0.64 + b, r * math.sin(a)))
            ms.append(named(f, 'frijol', rim=0.3, gloss=0.55))
    return P.tfk(ms, s=s, ry=ry, t=t)


def perilla(x, ang, s=1.0, z=0.75, y=-0.16):
    """Perilla negra de la estufa (de frente a +z) con su marca blanca girada `ang` grados."""
    k = named(M3.cyl(0.085 * s, 0.07 * s, (30, 30, 34), n=20, shadow=0, gloss=0.6).tf(rx=90, t=(x, y, z)), 'perilla', rim=0.6)
    mk = flat(named(M3.box(0.016 * s, 0.06 * s, 0.01, (245, 245, 245), shadow=0, base=False).tf(t=(0, 0.035 * s, 0))
                    .tf(rz=ang, t=(x, y, z + 0.075 * s)), 'marca'))
    return [k, mk]


def estufa(perilla_ang=0.0, w=2.6, d=1.5, cuerpo=True):
    """Estufa blanca con cubierta negra, quemador y parrilla; perilla del quemador al centro."""
    ms = []
    if cuerpo:
        ms.append(named(M3.box(w, 0.9, d, (226, 226, 222), shadow=0, base=True, gloss=0.35).tf(t=(0, -0.9, 0)), 'estufa', rim=0.5,
                        gloss=0.35))
    ms.append(named(M3.box(w * 0.98, 0.02, d * 0.96, (22, 22, 24), shadow=0, base=True, gloss=0.85).tf(t=(0, -0.01, 0)), 'cubierta',
                    gloss=0.85))
    ms.append(named(M3.cyl(0.2, 0.05, (70, 70, 74), n=24, shadow=0, gloss=0.6), 'quemador', rim=0.4))
    ms.append(named(M3.torus(0.34, 0.022, (52, 52, 56), nu=28, nv=5, gloss=0.6).tf(t=(0, 0.04, 0)), 'quemador', rim=0.4))
    for a in (0, 90):
        ms.append(named(M3.box(1.05, 0.03, 0.035, (14, 14, 16), shadow=0, base=False, gloss=0.6).tf(ry=a + 45, t=(0, 0.075, 0)),
                        'parrilla', rim=0.6))
    if cuerpo:
        for x in (-0.95, -0.5, 0.5, 0.95):
            ms += perilla(x, -30.0, z=d / 2)
        ms += perilla(0.0, perilla_ang, z=d / 2)
    return ms


def llamas(fr, t, c=(0, 0, 0), R=0.34, k=0.5, lado=-1, s=1.0, pot_r=0.6):
    """Flamas de gas alrededor del quemador. lado=-1: todas (antes de la olla, que las tapa); lado=+1: solo la parte de
    las flamas de enfrente que sale de la olla (después de draw_objects, para que laman los lados)."""
    if k <= 0.01:
        return
    n = 16
    cc = np.array(c, float)
    for i in range(n):
        a = 2 * math.pi * i / n + 0.1
        d = np.array([math.cos(a), 0, math.sin(a)])
        base = cc + d * R * s + np.array([0, 0.05 * s, 0])
        vc = (fr.cam.pos - cc)[[0, 2]]
        cosv = float(d[[0, 2]] @ vc) / (np.linalg.norm(vc) + 1e-9)
        if lado == 1 and not (0.0 < cosv < 0.75):      # solo las de los lados que lamen la olla
            continue
        h = (0.06 + 0.42 * k) * (0.8 + 0.25 * math.sin(t * 23 + i * 2.1)) * s
        out = d * (0.06 + 0.34 * k) * s
        pts = [base + out * (1 - (1 - q) ** 2) + np.array([0, h * q ** 1.4, 0]) for q in np.linspace(0, 1, 9)]
        if lado == 1:
            pts = [p for p in pts if np.linalg.norm((p - cc)[[0, 2]]) > pot_r * s]
            if len(pts) < 2:
                continue
        col = M.mixc(AZUL_F, NARANJA, clamp((k - 0.55) / 0.45) * 0.85)
        line3(fr, pts, col=col, w=(5 + 6 * k) * s, a=0.95, glow=1.3)
        if lado == -1:
            line3(fr, pts[:4], col=(200, 225, 255), w=3 * s, a=0.9, glow=0.8)


def burbujas(fr, t, c=(0, 0, 0), R=0.48, k=1.0, n=14, y=0.645, s=1.0, rate=1.6, big=1.0):
    """Burbujas que revientan en la superficie del agua (anillos que crecen y desaparecen)."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(7)
    cx, cy, cz = c
    for j in range(int(n)):
        a = rng.uniform(0, 2 * math.pi)
        r = R * math.sqrt(rng.uniform(0, 1))
        sp = 0.7 + 0.6 * rng.rand()
        ph = (t * rate * sp + rng.rand()) % 1.0
        p = np.array([cx + r * math.cos(a) * s, cy + y * s, cz + r * math.sin(a) * s])
        sc, z = fr.cam.proj([p])
        if z[0] < 0.2:
            continue
        x0, y0 = sc[0]
        rad = fr.cam.F * (0.008 + 0.04 * ph * big) * s / z[0]
        sq = 0.35 + 0.5 * abs(math.sin(math.radians(25)))
        al = k * (1 - ph) ** 0.7
        col = M.scale_c(WHITE, 0.95 * al)
        fr.db.ellipse((x0 - rad, y0 - rad * sq, x0 + rad, y0 + rad * sq), outline=col, width=max(2, int(2.5 * S)))
        fr.df.ellipse((x0 - rad, y0 - rad * sq, x0 + rad, y0 + rad * sq), outline=M.scale_c(WHITE, 0.4 * al), width=max(3, int(5 * S)))
        if ph < 0.25:
            dot3(fr, p + np.array([0, 0.02 * s, 0]), r=3 + 4 * big, col=WHITE, a=al, glow=0.7)


def vapor(fr, t, c=(0, 0, 0), k=1.0, h=1.4, n=6, s=1.0, ancho=0.8):
    """Hilos de vapor que suben (line-art blanco)."""
    if k <= 0.01:
        return
    cx, cy, cz = c
    for i in range(n):
        x0 = cx + (-ancho / 2 + ancho * (i + 0.5) / n) * s
        ph = t * 1.6 + i * 1.3
        pts = [np.array([x0 + 0.07 * s * math.sin(ph + q * 7) * (0.3 + q), cy + h * q * s, cz + 0.05 * math.cos(i)]) for q in
               np.linspace(0, 1, 26)]
        line3(fr, pts, col=(235, 240, 248), w=3 * s, a=0.45 * k, glow=0.7 * k, frac=clamp(((t * 0.7 + i * 0.23) % 1.0) * 1.6))


def columna_aire(fr, t, x=0.0, z=0.0, y0=0.8, y1=5.0, dens=1.0, k=1.0, r=0.5, flechas=True, seed=1):
    """Columna de aire: moléculas (puntitos) que bajan y empujan la superficie del agua."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    n = int(90 * dens)
    for j in range(n):
        a = rng.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(rng.rand())
        ph = (rng.rand() - t * 0.18 * (0.6 + rng.rand())) % 1.0
        p = np.array([x + rr * math.cos(a), y0 + (y1 - y0) * ph, z + rr * math.sin(a)])
        dot3(fr, p, r=3.2, col=(225, 235, 255), a=0.85 * k * min(1, ph * 6), glow=0.6)
    if flechas:
        for j, dx in enumerate((-0.28, 0.0, 0.28)):
            yy = y0 + 0.35 + 0.12 * ((t * 1.5 + j * 0.3) % 1.0)
            line3(fr, [(x + dx, yy + 0.45, z), (x + dx, yy, z)], col=CYAN, w=4, a=0.9 * k, glow=0.9)
            line3(fr, [(x + dx - 0.07, yy + 0.09, z), (x + dx, yy, z), (x + dx + 0.07, yy + 0.09, z)], col=CYAN, w=4, a=0.9 * k, glow=0.9)


def termo_dial(img, fx, cx, cy, R, temp, k=1.0, vmax=120, roja=100, lectura=None, tallo=None, col_aguja=ROJO):
    """Termómetro de carátula de cocina (2D que brilla). temp en °C; tallo=(x, y) punta del vástago."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    a = clamp(k)
    if tallo:
        d.line([(cx, cy + R * 0.9), tallo], fill=M.scale_c((200, 204, 210), a), width=10)
        df.line([(cx, cy + R * 0.9), tallo], fill=M.scale_c((90, 90, 96), a), width=14)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(10, 12, 16), outline=M.scale_c((230, 232, 238), a), width=8)
    df.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c((120, 130, 150), a), width=16)

    def ang(v):
        return math.radians(225 - 270 * v / vmax)
    # zona roja
    a0, a1 = 225 - 270 * roja / vmax, 225 - 270 * min(vmax, roja + 20) / vmax
    box = (cx - R * 0.86, cy - R * 0.86, cx + R * 0.86, cy + R * 0.86)
    d.arc(box, -a0, -a1, fill=M.scale_c(ROJO, a), width=int(R * 0.09))
    df.arc(box, -a0, -a1, fill=M.scale_c(ROJO, 0.6 * a), width=int(R * 0.13))
    for v in range(0, vmax + 1, 5):
        th = ang(v)
        L = R * (0.16 if v % 20 == 0 else 0.08)
        r0 = R * 0.9
        d.line([(cx + r0 * math.cos(th), cy - r0 * math.sin(th)), (cx + (r0 - L) * math.cos(th), cy - (r0 - L) * math.sin(th))],
               fill=M.scale_c(WHITE, a * (1 if v % 20 == 0 else 0.6)), width=4 if v % 20 == 0 else 2)
        if v % 20 == 0 and 0 < v < vmax:
            rt = R * 0.6
            d.text((cx + rt * math.cos(th), cy - rt * math.sin(th)), str(v), font=M.font('mono', int(R * 0.13)),
                   fill=M.scale_c((200, 202, 210), a), anchor='mm')
    th = ang(clamp(temp, 0, vmax + 8))
    tip = (cx + R * 0.8 * math.cos(th), cy - R * 0.8 * math.sin(th))
    tail = (cx - R * 0.15 * math.cos(th), cy + R * 0.15 * math.sin(th))
    d.line([tail, tip], fill=M.scale_c(col_aguja, a), width=max(4, int(R * 0.035)))
    df.line([tail, tip], fill=M.scale_c(col_aguja, 0.7 * a), width=max(8, int(R * 0.07)))
    d.ellipse((cx - R * 0.07, cy - R * 0.07, cx + R * 0.07, cy + R * 0.07), fill=M.scale_c((230, 230, 235), a))
    txt = lectura if lectura is not None else f'{temp:.0f} °C'
    d.text((cx, cy + R * 0.48), txt, font=M.font('mono', int(R * 0.2)), fill=M.scale_c(WHITE, a), anchor='mm')
    df.text((cx, cy + R * 0.48), txt, font=M.font('mono', int(R * 0.2)), fill=M.scale_c(WHITE, 0.35 * a), anchor='mm')


def tanque(t=(0, 0, 0), s=1.0, ry=0.0):
    """Cilindro de gas LP (sin marcas): cuerpo gris claro, domo, válvula de latón y aro protector."""
    ms = [named(M3.cyl(0.36, 1.0, (206, 206, 200), n=30, shadow=0, gloss=0.45), 'tanque', rim=0.6, gloss=0.45),
          named(M3.sphere(0.36, (206, 206, 200), nu=30, nv=10, shadow=0, gloss=0.45).tf(s=(1, 0.35, 1), t=(0, 1.0, 0)), 'tanque',
                rim=0.6, gloss=0.45),
          named(M3.cyl(0.05, 0.16, (205, 165, 80), n=12, shadow=0, gloss=0.9).tf(t=(0, 1.08, 0)), 'valvula', gloss=0.9),
          named(M3.torus(0.2, 0.025, (150, 150, 150), nu=24, nv=5, gloss=0.6).tf(t=(0, 1.3, 0)), 'aro', rim=0.6),
          named(M3.cyl(0.3, 0.08, (60, 60, 64), n=24, shadow=0, gloss=0.3), 'base', rim=0.3)]
    return P.tfk(ms, s=s, ry=ry, t=t)


def olla_expres(t=(0, 0, 0), s=1.0, ry=0.0, tapa=0.0, frijoles=0.0, tt=0.0, valvula=0.0):
    """Olla exprés de acero (sin marcas) con tapa que se cierra (tapa = 1 abierta arriba → 0 cerrada) e interior para rayos X."""
    up = 1.2 * tapa
    ms = [named(M3.cyl(0.55, 0.6, ACERO, n=36, shadow=0, gloss=0.85), 'cuerpo', rim=0.8, gloss=0.85),
          named(M3.rbox(0.6, 0.06, 0.12, 0.03, NEGRO, n=2, shadow=0, gloss=0.4).tf(t=(-0.85, 0.5, 0)), 'mango', rim=0.4),
          named(M3.cyl(0.58, 0.05, (140, 146, 156), n=36, shadow=0, gloss=0.85).tf(t=(0, 0.6 + up, 0)), 'tapa', rim=0.8, gloss=0.85),
          named(M3.sphere(0.56, (146, 152, 162), nu=36, nv=10, shadow=0, gloss=0.85).tf(s=(1, 0.22, 1), t=(0, 0.65 + up, 0)), 'tapa',
                rim=0.8, gloss=0.85),
          named(M3.rbox(0.62, 0.06, 0.12, 0.03, NEGRO, n=2, shadow=0, gloss=0.4).tf(t=(-0.82, 0.68 + up, 0)), 'mango', rim=0.4),
          named(M3.cyl(0.045, 0.12, (150, 150, 156), n=12, shadow=0, gloss=0.9).tf(t=(0, 0.75 + up, 0)), 'valvula', gloss=0.9),
          named(M3.cyl(0.075, 0.07, (24, 24, 28), n=14, shadow=0, gloss=0.5).tf(ry=valvula * 40, t=(0, 0.86 + up + 0.02 * valvula, 0)),
                'pesa', rim=0.5)]
    ms.append(named(M3.cyl(0.5, 0.36, (80, 150, 210), n=30, top=(150, 200, 235), shadow=0, gloss=0.3).tf(t=(0, 0.03, 0)), 'in',
                    glow=(10, 30, 50)))
    if frijoles > 0.01:
        for i in range(int(12 * frijoles)):
            a = i * 2.39 + tt * (1.5 + 0.3 * (i % 3))
            r = 0.12 + 0.3 * ((i * 0.37) % 1)
            yy = 0.12 + 0.2 * ((i * 0.61 + tt * 0.8) % 1)
            ms.append(named(M3.sphere(0.06, FRIJOL, nu=10, nv=6, shadow=0, gloss=0.55).tf(s=(1, 0.5, 0.66), ry=i * 50 + tt * 200,
                                                                                         t=(r * math.cos(a), yy, r * math.sin(a))),
                            'in', rim=0.3))
    return P.tfk(ms, s=s, ry=ry, t=t)


def moleculas(fr, t, centro, R, n=24, k=1.0, col=VAPOR, vel=1.0, seed=5, y_min=None):
    """Moléculas de vapor que rebotan dentro de un volumen (puntitos cálidos que brillan)."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    cx, cy, cz = centro
    for j in range(n):
        ph = rng.rand(3) * 6.28
        w = (0.8 + rng.rand(3)) * vel
        p = np.array([cx + R * 0.8 * math.sin(t * w[0] * 2 + ph[0]), cy + R * 0.5 * math.sin(t * w[1] * 2.3 + ph[1]),
                      cz + R * 0.8 * math.sin(t * w[2] * 1.9 + ph[2])])
        if y_min is not None and p[1] < y_min:
            p[1] = 2 * y_min - p[1]
        dot3(fr, p, r=4, col=col, a=k, glow=1.1)


def tierra_linea(fr, perfil, k=1.0, z=0.0, col=WHITE):
    """Perfil del terreno en line-art (lista de (x, y))."""
    if k <= 0.01:
        return
    line3(fr, [(x, y, z) for x, y in perfil], col=col, w=3, a=0.85 * k, glow=0.8 * k, frac=k)
    for dz in (-0.6, -1.2):
        line3(fr, [(x, y * 0.92, z + dz) for x, y in perfil], col=col, w=2, a=0.3 * k, glow=0.3 * k, frac=k)


def olas(fr, t, x0, x1, y=0.0, k=1.0, z=0.0):
    if k <= 0.01:
        return
    for j in range(3):
        zz = z + 0.4 - 0.4 * j
        pts = [(x, y + 0.04 * math.sin(x * 6 + t * 3 + j), zz) for x in np.linspace(x0, x1, 40)]
        line3(fr, pts, col=CYAN, w=3, a=0.7 * k, glow=0.9 * k)


_FOTO = {}


def foto_mx():
    if 'mx' not in _FOTO:
        im = Image.open('/home/claude/fotos_agua/mexico_iss.jpg').convert('RGB')
        _FOTO['mx'] = im.crop((0, 0, 720, 560))
    return _FOTO['mx']


def _pant_chat(k_env, t):
    def dib(d, im):
        w, h = im.size
        d.rectangle((0, 70, w, 150), fill=(18, 20, 26))
        d.ellipse((24, 88, 72, 136), fill=(60, 90, 140))
        d.text((88, 96), 'Familia', font=M.font('sanss', 30), fill=(240, 240, 242))
        d.text((88, 128), 'en línea', font=M.font('sansm', 18), fill=(150, 200, 160))
        # globo con el video
        y0 = 210
        d.rounded_rectangle((120, y0, w - 24, y0 + 330), radius=22, fill=(26, 60, 50))
        d.rounded_rectangle((136, y0 + 16, w - 40, y0 + 250), radius=14, fill=(8, 8, 10))
        cx, cy = (136 + w - 40) / 2, y0 + 150
        d.rectangle((cx - 70, cy - 30, cx + 70, cy + 40), fill=PELTRE)
        d.rectangle((cx - 74, cy - 34, cx + 74, cy - 26), fill=BLANCO_P)
        for i in range(7):
            x = cx - 90 + 30 * i
            hh = 40 + 12 * math.sin(t * 20 + i)
            d.polygon([(x - 10, cy + 70), (x + 10, cy + 70), (x, cy + 70 - hh * 0.0 + 0)], fill=NARANJA)
            d.polygon([(x - 11, cy + 72), (x + 11, cy + 72), (x, cy + 72 - hh)], fill=(255, 140 + i * 8, 50))
        d.polygon([(cx - 14, y0 + 110), (cx - 14, y0 + 150), (cx + 18, y0 + 130)], fill=(240, 240, 240))
        d.text((140, y0 + 266), 'Tu agua hierve… sin llegar a 100', font=M.font('sanss', 20), fill=(235, 240, 236))
        d.text((w - 40, y0 + 302), '10:00 ✓✓', font=M.font('sansm', 18), fill=(130, 200, 255), anchor='ra')
        if k_env > 0.01:
            y1 = y0 + 360
            d.rounded_rectangle((60, y1, w - 24, y1 + 90), radius=20, fill=(26, 60, 50))
            d.text((80, y1 + 24), '¡Bájale al fuego! 🔥'.replace(' 🔥', ''), font=M.font('sanss', 30), fill=(240, 242, 240))
        d.rounded_rectangle((24, h - 120, w - 110, h - 62), radius=28, fill=(30, 32, 38))
        d.ellipse((w - 96, h - 124, w - 30, h - 58), fill=(40, 170, 110))
        d.polygon([(w - 76, h - 108), (w - 76, h - 74), (w - 46, h - 91)], fill=(255, 255, 255))
    return P.pantalla(dib)


# ================================================================== escenas
# 0. gancho, inicio tipo 12 (reloj/aguja): la olla hierve; la aguja del termómetro corre hacia el 100, se estrella contra
#    el 92 y se congela (sacudida + título que cae). En el loop (u < 0) la aguja sube del frío al 92 mientras se dice
#    «…sin llegar a cien», y el último cuadro es igual al primero.
UJ = 0.32           # la aguja choca y se congela


def _aguja0(u):
    if u < 0:
        return 92 + 0.6 * math.sin(u * 11)     # en el loop ya está en 92 (hierve) y tiembla un poco
    if u < UJ:
        return 92 + 7 * math.sin(math.pi * seg(u, 0.0, UJ)) ** 0.7     # intenta pasar…
    return 92 + 1.6 * math.exp(-9 * (u - UJ)) * math.sin(40 * (u - UJ))  # …rebota y se queda en 92


def s_gancho(t, fi, u, d):
    fr = Frame(cam(u, [K(-4.5, 3.6, -22, 22, ty=0.45), K(-1.7, 3.05, 6, 24, ty=0.45), K(UJ, 3.05, 6, 24, ty=0.45),
                       K(UJ + 0.05, 2.55, 12, 26, ty=0.45), K(3.4, 2.45, 16, 26, ty=0.45)], cy=0.7))
    space(fr, t, floor=None, bokeh=1.0, beam=0.45)
    M.cristal(fr.base, fr.fx, '100°', u, t0=-3.4, cy=0.37, alto=0.3, entrada='golpe')
    k_f = 0.45 + 0.05 * math.sin(t * 3)
    llamas(fr, t, k=k_f, lado=-1)
    dibujar(fr, estufa(perilla_ang=-60) + olla(tt=t))
    llamas(fr, t, k=k_f, lado=1)
    burbujas(fr, t, k=1.0, n=16)
    vapor(fr, t, c=(0, 0.7, 0), k=0.6, h=1.1)
    pt = fr.cam.p1((0.22, 0.66, 0.15))
    temp = _aguja0(u)

    def ui(img, fx):
        kicker(img, 'TERMÓMETRO DE COCINA · CDMX', 112, 1.0, col=(150, 210, 230))
        termo_dial(img, fx, 770, 960, 165, temp, tallo=(pt[0], pt[1]), lectura='92 °C' if u < 0 or u > UJ + 0.25 else None)
        P.titulo_golpe(img, fx, [('Tu agua hierve…', 'sans'), ('sin llegar a 100.', 'serif')], 170, seg(u, UJ, UJ + 0.15), size=76)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u >= UJ:
        out = (out.astype(np.float32) + 110 * golpe_k(u, UJ, 0.16)).clip(0, 255).astype(np.uint8)
    return sacudir(out, t, golpe_k(u, UJ, 0.4), amp=26)


# 1. CDMX: la cámara atraviesa la carátula y cae la foto real de México desde la Estación Espacial; «92 °C» golpea.
def s_cdmx(t, fi, u, d):
    u92 = wt(1, 8) - 0.12
    fr = Frame(cam(u, [K(-0.3, 4.5, -30, 10, ty=1.2), K(0.2, 4.0, 0, 6, ty=1.2), K(u92, 4.0, 0, 6, ty=1.2),
                       K(u92 + 0.1, 3.4, 10, 8, ty=1.2), K(4.0, 3.3, 14, 8, ty=1.2)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.2)
    k92 = seg(u, u92, u92 + 0.18)

    def ui(img, fx):
        kicker(img, 'MÉXICO DESDE LA ESTACIÓN ESPACIAL', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        photo_card(img, fx, foto_mx(), 540, 700 - 140 * P.eout4(seg(u, u92 - 0.1, u92 + 0.2)), 760, -0.05, u,
                   caption='NASA · ISS062-E-112947 · 2020', angle0=-10)
        yc = 545 - 140 * P.eout4(seg(u, u92 - 0.1, u92 + 0.2))
        doodle_circle(img, fx, 432, yc, 135, 58, t, k=eout(seg(u, 0.6, 1.1)), col=AMARILLO, w=6)
        P.numero_golpe(img, fx, '92 °C', 1200, k92, size=250)
        pill(img, fx, 540, 1420, 'CDMX · 2 240 m SOBRE EL MAR', eout(seg(u, u92 + 0.35, u92 + 0.6)), size=32, border=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u92 + 0.18, 0.35), amp=22)


# 2. no es tu estufa (✗) → la cámara sube y aparece la columna de aire encima de la olla; «AIRE» de cristal.
def s_aire(t, fi, u, d):
    ue, ua = wt(2, 4) - 0.1, wt(2, 5) - 0.12
    if u < ua:
        fr = Frame(cam(u, [K(-0.3, 1.6, 50, 14, ty=0.1), K(0.25, 1.35, 18, 12, ty=0.1), K(3.0, 1.3, 14, 12, ty=0.1)], cy=0.5))
        space(fr, t, floor=None, bokeh=0.8)
        llamas(fr, t, k=0.5, lado=-1)
        dibujar(fr, estufa(perilla_ang=-60, cuerpo=False))
        llamas(fr, t, k=0.5, lado=1)

        def ui(img, fx):
            kicker(img, 'QUEMADOR', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
            tache(img, fx, 540, 1380, seg(u, ue, ue + 0.25), 'TU ESTUFA')
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, ue + 0.2, 0.3), amp=12)
    v = u - ua
    k = P.eout4(seg(v, 0.0, 0.55))
    fr = Frame(Cam(target=(0, lerp(0.5, 2.3, k), 0), dist=lerp(2.6, 6.2, k), yaw=lerp(10, -14, k), pitch=lerp(30, 8, k), cy=0.55))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'AIRE', v, t0=wt(2, 7) - ua - 0.15, cy=0.3, alto=0.32, entrada='sube')
    llamas(fr, t, k=0.45, lado=-1)
    dibujar(fr, estufa(perilla_ang=-60) + olla(tt=t))
    llamas(fr, t, k=0.45, lado=1)
    burbujas(fr, t, k=1.0, n=12)
    columna_aire(fr, t, y0=0.75, y1=6.5, dens=1.2, k=seg(v, 0.1, 0.5), r=0.6)
    out = finish(fr, fi)
    if k < 0.9:
        out = M.radial_blur(out, 0.12 * (1 - k), 0.5, 0.6)
    im = Image.fromarray(out)
    fx = Image.new('RGB', im.size)
    pill(im, fx, 540, 1400, 'EL AIRE QUE TIENES ENCIMA', eout(seg(v, 0.5, 0.8)), size=34, border=CYAN)
    return np.asarray(im)


# 3. Veracruz: olas, la olla al nivel del mar y una columna de aire densa; la aguja llega a 100.
def s_veracruz(t, fi, u, d):
    u100 = wt(3, 12) - 0.1
    fr = Frame(cam(u, [K(-0.3, 5.2, -40, 14, ty=1.2), K(0.3, 4.6, -18, 10, ty=1.2), K(wt(3, 5) - 0.1, 4.6, -18, 10, ty=1.2),
                       K(wt(3, 5) + 0.15, 3.9, -6, 6, ty=1.0), K(5.0, 3.8, -2, 6, ty=1.0)], cy=0.56))
    space(fr, t, floor=None, bokeh=1.0)
    olas(fr, t, -3.0, 3.0, y=0.0)
    e = P.entrada(u, -0.1, 0.3, 'cae')
    llamas(fr, t, c=(0, -e['dy'], 0), k=0.45, lado=-1, s=0.8)
    dibujar(fr, P.tfk(estufa(cuerpo=False), s=0.8, t=(0, -e['dy'], 0)) + olla(s=0.8, t=(0, -e['dy'], 0), tt=t))
    llamas(fr, t, c=(0, -e['dy'], 0), k=0.45, lado=1, s=0.8)
    burbujas(fr, t, k=seg(u, u100 - 0.3, u100), n=12, s=0.8)
    columna_aire(fr, t, y0=0.65, y1=5.0, dens=1.7, k=seg(u, wt(3, 5) - 0.2, wt(3, 6)), r=0.55, seed=2)
    temp = lerp(60, 100, P.eout4(seg(u, u100 - 0.6, u100)))

    def ui(img, fx):
        pill(img, fx, 540, 190, 'VERACRUZ · NIVEL DEL MAR', eout(seg(u, 0.0, 0.25)), size=34, border=CYAN)
        pill(img, fx, 300, 330, 'AIRE QUE PESA MÁS', eout(seg(u, wt(3, 7) - 0.1, wt(3, 7) + 0.15)), size=30, border=(200, 200, 210),
             dot=False)
        termo_dial(img, fx, 800, 1160, 150, temp, k=seg(u, 0.2, 0.45), col_aguja=VERDE if temp > 99.5 else ROJO)
        check(img, fx, 800, 1390, seg(u, u100 + 0.1, u100 + 0.35), '100 °C')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u100, 0.3) + golpe_k(u, 0.2, 0.25), amp=14)


# 4. Toluca: la montaña de line-art sube, la olla arriba con poco aire; luego la gráfica 100 / 92 / 91.
PERFIL = [(-4.0, 0.0), (-2.6, 0.0), (-1.9, 0.25), (-1.3, 0.9), (-0.8, 1.35), (-0.3, 1.5), (0.3, 1.55), (0.8, 1.62),
          (1.2, 1.8), (1.6, 2.1), (2.1, 1.7), (2.8, 1.2), (3.6, 0.9)]


def s_toluca(t, fi, u, d):
    uc = wt(4, 8) - 0.15
    if u < uc:
        k = P.eout4(seg(u, -0.2, 0.5))
        fr = Frame(cam(u, [K(-0.3, 6.5, 30, 6, tx=0.6, ty=0.6), K(0.5, 4.2, 12, 16, tx=1.4, ty=2.2), K(4.0, 4.0, 8, 16, tx=1.5, ty=2.2)],
                       cy=0.55))
        space(fr, t, floor=None, bokeh=1.0, beam=0.3, beam_x=0.6)
        tierra_linea(fr, [(x, y * k) for x, y in PERFIL], k=1.0)
        top = (1.6, 2.1 * k, 0.0)
        llamas(fr, t, c=top, k=0.45, lado=-1, s=0.5)
        dibujar(fr, P.tfk(estufa(cuerpo=False), s=0.5, t=top) + olla(s=0.5, t=top, tt=t))
        llamas(fr, t, c=top, k=0.45, lado=1, s=0.5)
        burbujas(fr, t, c=top, k=1.0, n=10, s=0.5)
        columna_aire(fr, t, x=1.6, y0=2.1 * k + 0.4, y1=5.2, dens=0.45, k=seg(u, 0.3, 0.7), r=0.4, seed=4, flechas=False)
        pc = fr.cam.p1((0.3, 1.55 * k, 0))

        def ui(img, fx):
            pill(img, fx, 540, 190, 'TOLUCA · 2 660 m', eout(seg(u, 0.0, 0.25)), size=34, border=CYAN)
            pill(img, fx, pc[0], pc[1] + 60, 'CDMX · 2 240 m', eout(seg(u, 0.5, 0.75)), size=26, border=(200, 200, 210), dot=False)
            pill(img, fx, 330, 1380, 'MENOS AIRE ENCIMA', eout(seg(u, 0.9, 1.2)), size=30, border=AMARILLO, dot=False)
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, 0.5, 0.25), amp=10)
    v = u - uc
    fr = Frame(cam(v, [K(-0.2, 6.0, 0, 10, tx=0.3, ty=1.4), K(0.4, 5.2, -10, 8, tx=0.3, ty=1.4), K(3.0, 5.0, -14, 8, tx=0.3, ty=1.4)],
                   cy=0.5))
    space(fr, t, floor=None, bokeh=1.0)
    tierra_linea(fr, PERFIL, k=0.5)

    def ui(img, fx):
        chart_grow(img, fx, (80, 330, 1000, 1330), [100, 92, 91], ['VER', 'CDMX', 'TOL'], 0.0, v, unit='°C',
                   title_txt='EL AGUA HIERVE A… (°C)', vmax=104, line=True, tag='APROX.')
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. zoom fractal: de la olla a una burbuja de vapor; el aire la aplasta; con menos aire, escapa antes (zoom digital REC).
def s_burbuja(t, fi, u, d):
    uz, um = wt(5, 6) - 0.1, wt(5, 12) - 0.12
    zoom = 1.0 if u < uz else (1.3 if u < um else 1.8)
    fr = Frame(cam(u, [K(-0.3, 4.0, 0, 4, ty=1.2), K(0.3, 3.2, 8, 4, ty=1.2), K(uz, 3.2, 8, 4, ty=1.2),
                       K(uz + 0.1, 2.6, -6, 4, ty=1.4), K(um, 2.6, -6, 4, ty=1.4), K(um + 0.1, 2.9, 4, 6, ty=1.7),
                       K(6.0, 2.8, 8, 6, ty=1.8)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.4)
    # superficie del agua (línea ondulada) y agua debajo
    ys = 1.75
    for j in range(2):
        line3(fr, [(x, ys + 0.03 * math.sin(x * 5 + t * 4 + j), -0.3 * j) for x in np.linspace(-2.5, 2.5, 50)], col=CYAN, w=4 - j,
              a=0.8 - 0.3 * j, glow=1.0)
    esc = P.eout4(seg(u, um + 0.6, um + 1.4))
    yb = lerp(0.9, 2.6, esc) + 0.03 * math.sin(t * 6)
    rb = 0.42 + 0.03 * math.sin(t * 8) + 0.05 * esc
    draw_objects(fr, [named(M3.sphere(rb, (180, 220, 240), nu=28, nv=16, shadow=0, gloss=0.9).tf(t=(0, yb - rb, 0)), 'burbuja')],
                 xray=1.0)
    moleculas(fr, t, (0, yb, 0), rb, n=18, k=1.0, vel=1.4)
    for j in range(8):  # vapor que empuja hacia afuera
        a = j * math.pi / 4 + 0.2
        p0 = np.array([0, yb, 0]) + np.array([math.cos(a), math.sin(a), 0]) * (rb + 0.05)
        p1 = p0 + np.array([math.cos(a), math.sin(a), 0]) * (0.18 + 0.04 * math.sin(t * 9 + j))
        line3(fr, [p0, p1], col=VAPOR, w=4, a=0.9 * seg(u, 0.4, 0.7), glow=1.0)
    dens = lerp(1.3, 0.35, P.eout4(seg(u, um, um + 0.5)))
    columna_aire(fr, t, y0=ys + 0.1, y1=5.0, dens=dens, k=1.0, r=1.0, seed=6)

    def ui(img, fx):
        rec_frame(img, t, 1.0, zoom_label=f'x{zoom:.1f}')
        pill(img, fx, 290, 1040, 'VAPOR', eout(seg(u, wt(5, 3) - 0.1, wt(5, 3) + 0.15)), size=30, border=VAPOR)
        pill(img, fx, 780, 470, 'PESO DEL AIRE', eout(seg(u, wt(5, 8) - 0.1, wt(5, 8) + 0.15)), size=30, border=CYAN)
        pill(img, fx, 540, 1380, '↑ ESCAPA ANTES', eout(seg(u, wt(5, 15) - 0.1, wt(5, 15) + 0.15)), size=36, border=AMARILLO)
    fr.ui.append(ui)
    out = finish(fr, fi)
    for uj in (uz, um):
        if uj <= u < uj + 0.12:
            out = (out.astype(np.float32) + 70).clip(0, 255).astype(np.uint8)
    return out


# 6. tus frijoles tardan más: olla de frijoles vista desde arriba y un cronómetro que no para.
def s_frijoles(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.2, 30, 70, ty=0.6), K(0.25, 1.7, 0, 58, ty=0.6), K(1.6, 1.7, 0, 58, ty=0.6),
                       K(1.75, 1.45, -14, 50, ty=0.62), K(3.4, 1.4, -18, 50, ty=0.62)], cy=0.56))
    space(fr, t, floor=None, bokeh=0.8)
    e = P.entrada(u, -0.15, 0.3, 'pop')
    dibujar(fr, estufa(cuerpo=False) + olla(tt=t, frijoles=max(0.05, e['escala'])))
    burbujas(fr, t, k=0.8, n=10)
    vapor(fr, t, c=(0, 0.7, 0), k=0.4, h=0.9)
    ang = (u * 3.0) % 1.0

    def ui(img, fx):
        kicker(img, 'FRIJOLES DE OLLA · CDMX', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        cx, cy, R = 820, 340, 110
        d = ImageDraw.Draw(img)
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(230, 232, 238), width=6)
        d.arc((cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14), -90, -90 + 360 * ((u * 0.9) % 1.0), fill=AMARILLO, width=12)
        ImageDraw.Draw(fx).arc((cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10), -90, -90 + 360 * ((u * 0.9) % 1.0),
                               fill=(120, 110, 60), width=20)
        th = 2 * math.pi * ang - math.pi / 2
        d.line([(cx, cy), (cx + R * 0.75 * math.cos(th), cy + R * 0.75 * math.sin(th))], fill=WHITE, width=5)
        d.rectangle((cx - 16, cy - R - 26, cx + 16, cy - R - 6), fill=(230, 232, 238))
        pill(img, fx, 540, 1380, 'MÁS TIEMPO DE COCCIÓN', eout(seg(u, wt(6, 4) - 0.1, wt(6, 4) + 0.15)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.25), amp=10)


# 7. segundo gancho: la perilla gira a todo, las flamas revientan (FUEGO de cristal) y ERROR.
def s_error(t, fi, u, d):
    uf = wt(7, 5) - 0.1
    kf = P.eout4(seg(u, uf, uf + 0.35))
    if u < uf:
        fr = Frame(cam(u, [K(-0.3, 1.2, 25, 8, ty=-0.16, tz=0.75), K(0.25, 0.9, 6, 4, ty=-0.16, tz=0.75), K(3.0, 0.88, 4, 4, ty=-0.16,
                                                                                                          tz=0.75)], cy=0.5))
        space(fr, t, floor=None, bokeh=0.8)
        dibujar(fr, estufa(perilla_ang=-60))

        def ui(img, fx):
            pill(img, fx, 540, 330, 'ERROR', eout(seg(u, wt(7, 4) - 0.1, wt(7, 4) + 0.15)), size=46, border=ROJO, col=(255, 200, 196))
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, wt(7, 4), 0.3), amp=12)
    v = u - uf
    fr = Frame(cam(v, [K(0.0, 1.3, 4, 8, ty=-0.1, tz=0.6), K(0.3, 3.0, -16, 18, ty=0.35), K(3.0, 2.8, -20, 18, ty=0.35)], cy=0.62))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, 'FUEGO', v, t0=0.1, cy=0.33, alto=0.3, entrada='golpe')
    kk = 0.45 + 0.55 * kf
    llamas(fr, t, k=kk, lado=-1)
    dibujar(fr, estufa(perilla_ang=lerp(-60, -250, kf)) + olla(tt=t))
    llamas(fr, t, k=kk, lado=1)
    burbujas(fr, t, k=1.0, n=22, rate=2.6, big=1.4)

    def ui(img, fx):
        pill(img, fx, 540, 1380, 'TODO EL FUEGO', eout(seg(v, 0.2, 0.45)), size=40, border=ROJO, col=(255, 200, 196))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.25, 0.45) + 0.25 * kf, amp=18)


# 8. dos casos lado a lado: fuego medio contra fuego máximo; las dos agujas en 92.
def s_tope(t, fi, u, d):
    uc, uh = wt(8, 6) - 0.1, wt(8, 8) - 0.1
    fr = Frame(cam(u, [K(-0.3, 5.6, 0, 30, ty=0.3), K(0.25, 4.9, 0, 22, ty=0.3), K(uh, 4.9, 0, 22, ty=0.3),
                       K(uh + 0.1, 3.4, 18, 20, tx=0.9, ty=0.35), K(5.0, 3.3, 22, 20, tx=0.9, ty=0.35)], cy=0.6))
    space(fr, t, floor=None, bokeh=1.0)
    L, R_ = (-1.0, 0, 0), (1.0, 0, 0)
    kfuerte = 1.0 + 0.4 * seg(u, uh, uh + 0.3)
    for c, kf in ((L, 0.4), (R_, 1.0)):
        llamas(fr, t, c=c, k=kf, lado=-1, s=0.75)
    dibujar(fr, P.tfk(estufa(cuerpo=False), s=0.75, t=L) + P.tfk(estufa(cuerpo=False), s=0.75, t=R_) +
                 olla(s=0.75, t=L, tt=t) + olla(s=0.75, t=R_, tt=t * 1.3))
    for c, kf in ((L, 0.4), (R_, 1.0)):
        llamas(fr, t, c=c, k=kf, lado=1, s=0.75)
    burbujas(fr, t, c=L, k=1.0, n=9, s=0.75)
    burbujas(fr, t, c=R_, k=1.0, n=int(16 * kfuerte), s=0.75, rate=2.8, big=1.5)
    vapor(fr, t, c=(1.0, 0.55, 0), k=seg(u, uh, uh + 0.4), h=1.6, n=8, ancho=0.9)
    j = 0.8 * math.sin(t * 30)

    def ui(img, fx):
        pill(img, fx, 270, 330, 'FUEGO MEDIO', eout(seg(u, -0.1, 0.15)), size=30, border=AZUL_F, dot=False)
        pill(img, fx, 810, 330, 'FUEGO MÁXIMO', eout(seg(u, 0.1, 0.35)), size=30, border=ROJO, dot=False)
        termo_dial(img, fx, 270, 600, 145, 92 + 0.3 * math.sin(t * 7), k=seg(u, 0.0, 0.25), lectura='92 °C')
        termo_dial(img, fx, 810, 600, 145, 92 + j, k=seg(u, 0.15, 0.4), lectura='92 °C')
        doodle_circle(img, fx, 270, 670, 100, 48, t, k=eout(seg(u, uc, uc + 0.4)), col=AMARILLO, w=5)
        doodle_circle(img, fx, 810, 670, 100, 48, t, k=eout(seg(u, uc + 0.15, uc + 0.55)), col=AMARILLO, w=5, seed=3)
        texto(img, fx, 540, 600, '=', 120, AMARILLO, k=seg(u, uc + 0.3, uc + 0.5))
        pill(img, fx, 540, 1390, 'SOLO HIERVE MÁS FUERTE', eout(seg(u, uh + 0.1, uh + 0.35)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uh + 0.05, 0.3), amp=12)


# 9. se evapora → el tanque de gas cae y su nivel baja (GAS de cristal) → los frijoles se cuecen igual.
def s_gas(t, fi, u, d):
    ug, uf = wt(9, 4) - 0.12, wt(9, 7) - 0.1
    if u < ug:
        fr = Frame(cam(u, [K(-0.3, 3.6, -30, 30, ty=1.0), K(0.25, 3.0, -8, 16, ty=1.1), K(3.0, 2.9, -4, 16, ty=1.1)], cy=0.6))
        space(fr, t, floor=None, bokeh=1.0)
        llamas(fr, t, k=1.0, lado=-1)
        dibujar(fr, estufa(perilla_ang=-250, cuerpo=False) + olla(tt=t * 1.3))
        llamas(fr, t, k=1.0, lado=1)
        burbujas(fr, t, k=1.0, n=22, rate=2.6, big=1.4)
        vapor(fr, t, c=(0, 0.7, 0), k=1.0, h=2.2, n=10, ancho=1.0)

        def ui(img, fx):
            pill(img, fx, 540, 300, 'SE EVAPORA', eout(seg(u, wt(9, 3) - 0.15, wt(9, 3) + 0.1)), size=36, border=(220, 225, 235))
        fr.ui.append(ui)
        return finish(fr, fi)
    v = u - ug
    fr = Frame(cam(v, [K(-0.1, 4.2, 30, 10, tx=0.4, ty=0.8), K(0.3, 3.6, 12, 8, tx=0.4, ty=0.8), K(uf - ug, 3.6, 12, 8, tx=0.4, ty=0.8),
                       K(uf - ug + 0.1, 3.0, -10, 14, tx=-0.1, ty=0.7), K(4.0, 2.9, -14, 14, tx=-0.1, ty=0.7)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0)
    M.cristal(fr.base, fr.fx, 'GAS', v, t0=0.05, cy=0.33, alto=0.34, entrada='zoom')
    e = P.entrada(v, 0.0, 0.3, 'cae')
    llamas(fr, t, c=(-0.9, 0, 0), k=1.0, lado=-1, s=0.6)
    dibujar(fr, tanque(t=(0.9, -e['dy'], -0.2), s=1.0) + P.tfk(estufa(cuerpo=False), s=0.6, t=(-0.9, 0, 0)) +
                 olla(s=0.6, t=(-0.9, 0, 0), tt=t, frijoles=seg(v, uf - ug - 0.2, uf - ug)))
    llamas(fr, t, c=(-0.9, 0, 0), k=1.0, lado=1, s=0.6)
    burbujas(fr, t, c=(-0.9, 0, 0), k=1.0, n=14, s=0.6, rate=2.6, big=1.4)
    nivel = lerp(0.8, 0.45, P.eout4(seg(v, 0.4, 1.4)))
    pg = fr.cam.p1((0.9, 1.45, -0.2))

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        x, y = pg[0] + 150, pg[1] + 60
        dd.rounded_rectangle((x - 40, y - 150, x + 40, y + 150), radius=18, outline=(230, 232, 238), width=5)
        hh = 280 * nivel
        dd.rounded_rectangle((x - 28, y + 138 - hh, x + 28, y + 138), radius=10, fill=AMARILLO if nivel > 0.55 else ROJO)
        ImageDraw.Draw(fx).rounded_rectangle((x - 30, y + 138 - hh, x + 30, y + 138), radius=10, fill=(90, 80, 30))
        texto(img, fx, x, y + 190, f'{nivel * 100:.0f}%', 40, WHITE, f='mono')
        check(img, fx, 540, 1390, seg(v, uf - ug + 0.3, uf - ug + 0.55), 'SE CUECEN IGUAL', col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.3, 0.3), amp=16)


# 10. la olla exprés cae, la tapa se cierra con clic y en rayos X se ve el vapor atrapado (presión ↑).
def s_expres(t, fi, u, d):
    uc, ux = wt(10, 4) - 0.1, wt(10, 6) - 0.1
    up = wt(10, 10) - 0.1
    fr = Frame(cam(u, [K(-0.3, 3.6, 40, 20, ty=0.55), K(0.25, 2.9, 14, 16, ty=0.55), K(ux, 2.9, 14, 16, ty=0.55),
                       K(ux + 0.1, 2.4, -16, 12, ty=0.5), K(5.0, 2.35, -20, 12, ty=0.5)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.1, 0.32, 'cae')
    tapa = 1 - P.eout4(seg(u, uc - 0.3, uc))
    kx = seg(u, ux, ux + 0.35)
    vv = seg(u, up, up + 2.0)
    ms = olla_expres(t=(0, -e['dy'], 0), tapa=tapa, frijoles=1.0, tt=t, valvula=vv * math.sin(t * 20))
    draw_objects(fr, ms, xray=kx, keep=('in',))
    if kx > 0.05:
        moleculas(fr, t, (0, 0.62, 0), 0.5, n=26, k=kx, vel=1.0 + 2.0 * vv, y_min=0.42)
    pv = fr.cam.p1((0, 0.95, 0))

    def ui(img, fx):
        kicker(img, 'OLLA EXPRÉS · RAYOS X', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
        if tapa < 0.05 and u < uc + 0.5:
            pill(img, fx, pv[0] + 170, pv[1] - 30, 'CLIC', eout(seg(u, uc, uc + 0.15)), size=30, border=WHITE, dot=False)
        pill(img, fx, 300, 1380, 'VAPOR ATRAPADO', eout(seg(u, ux + 0.2, ux + 0.45)), size=32, border=VAPOR)
        pill(img, fx, 790, 1380, 'PRESIÓN ↑', eout(seg(u, up, up + 0.25)), size=34, border=AMARILLO)
        if vv > 0:
            for j in range(3):
                yy = pv[1] - 40 - 60 * ((t * 2 + j / 3) % 1)
                ImageDraw.Draw(fx).ellipse((pv[0] - 18, yy - 18, pv[0] + 18, yy + 18), fill=(70, 70, 76))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.22, 0.3) + golpe_k(u, uc, 0.25), amp=14)


# 11. adentro: crash zoom al agua, la aguja por fin pasa el 100 (+100° de cristal) y los frijoles giran rápido.
def s_dentro(t, fi, u, d):
    u100, ur = wt(11, 7) - 0.15, wt(11, 10) - 0.1
    fr = Frame(cam(u, [K(-0.3, 3.4, 0, 30, ty=0.4), K(0.2, 1.9, 10, 22, ty=0.3), K(ur, 1.9, 10, 22, ty=0.3),
                       K(ur + 0.1, 2.5, -22, 30, ty=0.35), K(6.0, 2.45, -26, 30, ty=0.35)], cy=0.66))
    space(fr, t, floor=None, bokeh=1.0)
    M.cristal(fr.base, fr.fx, '+100°', u, t0=u100, cy=0.3, alto=0.3, entrada='golpe')
    vel = 1.0 + 3.0 * seg(u, ur, ur + 0.4)
    draw_objects(fr, olla_expres(frijoles=1.0, tt=t * vel), xray=1.0, keep=('in',))
    moleculas(fr, t, (0, 0.62, 0), 0.5, n=30, k=1.0, vel=3.0, y_min=0.42)
    temp = lerp(92, 112, P.eout4(seg(u, u100 - 0.5, u100 + 0.1)))

    def ui(img, fx):
        termo_dial(img, fx, 790, 1080, 160, temp, k=seg(u, -0.1, 0.15), vmax=120, lectura='+100 °C' if temp > 100.5 else None,
                   col_aguja=AMARILLO if temp > 100.5 else ROJO)
        pill(img, fx, 300, 1390, '» MÁS RÁPIDO', eout(seg(u, ur + 0.15, ur + 0.4)), size=36, border=VERDE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u100 + 0.1, 0.4), amp=20)


# 12. el truco: la perilla gira a fuego medio (la transición es el giro de la perilla) y ahorras gas.
def s_truco(t, fi, u, d):
    ub, ua = wt(12, 4) - 0.12, wt(12, 9) - 0.1
    kb = P.eout4(seg(u, ub, ub + 0.4))
    fr = Frame(cam(u, [K(-0.3, 1.2, -30, 4, ty=-0.16, tz=0.75), K(0.3, 0.92, -8, 3, ty=-0.16, tz=0.75), K(ub + 0.4, 0.9, -8, 3, ty=-0.16, tz=0.75),
                       K(ub + 0.55, 2.8, 14, 22, ty=0.3), K(5.0, 2.7, 18, 22, ty=0.3)], cy=0.62))
    space(fr, t, floor=None, bokeh=1.0)
    kf = lerp(1.0, 0.45, kb)
    llamas(fr, t, k=kf, lado=-1)
    dibujar(fr, estufa(perilla_ang=lerp(-250, -90, kb)) + olla(tt=t))
    llamas(fr, t, k=kf, lado=1)
    burbujas(fr, t, k=1.0, n=12)
    pt = fr.cam.p1((0.22, 0.66, 0.15))

    def ui(img, fx):
        if u > ub + 0.5:
            termo_dial(img, fx, 800, 520, 140, 92 + 0.4 * math.sin(t * 5), k=seg(u, ub + 0.5, ub + 0.7), tallo=(pt[0], pt[1]))
        check(img, fx, 290, 1300, seg(u, wt(12, 6) - 0.1, wt(12, 6) + 0.15), 'FUEGO MEDIO')
        check(img, fx, 700, 1400, seg(u, ua, ua + 0.25), 'AHORRAS GAS')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.55, 0.25), amp=10)


# 13. mándaselo: el celular llega girando con el chat de la familia y el video de la olla.
def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 3.9, 40, 10, ty=0.95), K(0.3, 3.0, 10, 6, ty=0.95), K(4.0, 2.9, 6, 6, ty=0.95)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.15, 0.3, 'gira')
    scr = _pant_chat(seg(u, 1.0, 1.1), t)
    dibujar(fr, P.tfk(P.celular(scr), s=max(0.05, e['escala']), ry=math.degrees(e['giro']), t=(0, 0.95 * (1 - e['escala']), 0)))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien le sube', 'sans'), ('todo el fuego a la olla.', 'serif')], 170, seg(u, 0.0, 0.3), size=60)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.25), amp=10)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.71, 0.5), sfx=[]),
           dict(desde=1, fn=s_cdmx, tr='zoom', sfx=[]),
           dict(desde=2, fn=s_aire, tr='cubo', sfx=[]),
           dict(desde=3, fn=s_veracruz, tr='deslizar', sfx=[]),
           dict(desde=4, fn=s_toluca, tr='rebanadas', sfx=[]),
           dict(desde=5, fn=s_burbuja, tr='iris', c=(0.5, 0.62), sfx=[]),
           dict(desde=6, fn=s_frijoles, tr='remolino', sfx=[]),
           dict(desde=7, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[]),
           dict(desde=8, fn=s_tope, tr='wipe', sfx=[]),
           dict(desde=9, fn=s_gas, tr='whip', sfx=[]),
           dict(desde=10, fn=s_expres, tr='cristal', palabra='EXPRÉS', sfx=[]),
           dict(desde=11, fn=s_dentro, tr='golpe', sfx=[]),
           dict(desde=12, fn=s_truco, tr='giro', c=(0.5, 0.55), sfx=[]),
           dict(desde=13, fn=s_mandalo, tr='mosaico', sfx=[]),
           dict(desde=14, loop=True, tr='flash')]


def _sfx_dinamicos():
    E = ESCENAS
    E[0]['sfx'] = [(-1.7, 'whoosh_suave', 0.5)] + [(-1.6 + 0.07 * i, 'tick2', 0.25) for i in range(9)] + \
                  [(0.0, 'tick', 0.5), (UJ - 0.1, 'whoosh', 0.7), (UJ, 'sub', 1.0), (UJ, 'slap', 0.8), (UJ + 0.15, 'bass', 0.8)]
    u92 = wt(1, 8) - 0.12
    E[1]['sfx'] = [(0.05, 'slap', 0.8), (0.7, 'scribble', 0.5), (u92 + 0.18, 'bass', 1.0), (u92 + 0.18, 'sub', 0.6),
                   (u92 + 0.4, 'tick', 0.5)]
    ue, ua = wt(2, 4) - 0.1, wt(2, 5) - 0.12
    E[2]['sfx'] = [(0.0, 'tick', 0.4), (ue + 0.1, 'scribble', 0.5), (ue + 0.2, 'thud', 0.6), (ua, 'riser', 0.5), (ua + 0.1, 'whoosh', 0.8),
                   (ua + 0.6, 'tick2', 0.5)]
    u100 = wt(3, 12) - 0.1
    E[3]['sfx'] = [(0.0, 'thud', 0.6), (0.2, 'tick', 0.5), (wt(3, 5), 'whoosh', 0.7), (wt(3, 7), 'tick2', 0.5),
                   (u100, 'chime_c', 0.6), (u100 + 0.1, 'click', 0.6)]
    uc = wt(4, 8) - 0.15
    E[4]['sfx'] = [(0.0, 'riser', 0.4), (0.5, 'thud', 0.6), (0.6, 'tick', 0.4), (0.9, 'tick2', 0.4), (uc, 'whoosh', 0.7)] + \
                  [(uc + 0.25 + 0.28 * i, ('chime_a', 'chime_b', 'chime_c')[i], 0.5) for i in range(3)]
    uz, um = wt(5, 6) - 0.1, wt(5, 12) - 0.12
    E[5]['sfx'] = [(0.0, 'shimmer', 0.4), (wt(5, 3), 'tick', 0.5), (uz, 'click', 0.9), (uz + 0.1, 'whoosh', 0.5),
                   (wt(5, 8), 'tick2', 0.5), (um, 'click', 0.9), (um + 0.6, 'riser', 0.5), (um + 1.3, 'chime_c', 0.5)]
    E[6]['sfx'] = [(0.0, 'thud', 0.5)] + [(0.3 + 0.25 * i, 'tick', 0.3) for i in range(10)] + [(wt(6, 4), 'tick2', 0.5)]
    uf = wt(7, 5) - 0.1
    E[7]['sfx'] = [(wt(7, 4) - 0.1, 'burst', 0.5), (wt(7, 4), 'bass', 0.8), (uf, 'click', 0.8), (uf + 0.05, 'whoosh', 0.9),
                   (uf + 0.3, 'sub', 1.0), (uf + 0.3, 'burst', 0.6), (uf + 0.5, 'tick', 0.5)]
    uc8, uh = wt(8, 6) - 0.1, wt(8, 8) - 0.1
    E[8]['sfx'] = [(0.0, 'tick', 0.5), (0.2, 'tick2', 0.4), (uc8, 'scribble', 0.5), (uc8 + 0.35, 'chime_b', 0.5), (uh, 'whoosh', 0.7),
                   (uh + 0.1, 'bass', 0.8)]
    ug, uf9 = wt(9, 4) - 0.12, wt(9, 7) - 0.1
    E[9]['sfx'] = [(0.0, 'whoosh_suave', 0.5), (wt(9, 3) - 0.1, 'tick', 0.5), (ug, 'whoosh', 0.8), (ug + 0.3, 'thud', 1.0),
                   (ug + 0.3, 'slap', 0.6), (ug + 0.5, 'tick2', 0.4), (uf9 + 0.3, 'chime_c', 0.5)]
    uc10, ux, up = wt(10, 4) - 0.1, wt(10, 6) - 0.1, wt(10, 10) - 0.1
    E[10]['sfx'] = [(0.22, 'thud', 0.9), (uc10, 'click', 1.0), (uc10 + 0.02, 'bass', 0.6), (ux, 'shimmer', 0.6), (ux + 0.1, 'whoosh', 0.5),
                    (up, 'riser', 0.6), (up + 0.25, 'tick2', 0.5)]
    u100, ur = wt(11, 7) - 0.15, wt(11, 10) - 0.1
    E[11]['sfx'] = [(0.0, 'whoosh', 0.6), (u100 - 0.5, 'riser', 0.5), (u100 + 0.1, 'sub', 1.0), (u100 + 0.1, 'bass', 0.8),
                    (ur, 'whoosh', 0.8), (ur + 0.2, 'chime_c', 0.5)]
    ub, ua12 = wt(12, 4) - 0.12, wt(12, 9) - 0.1
    E[12]['sfx'] = [(0.0, 'tick', 0.5), (ub, 'click', 0.7), (ub + 0.15, 'click', 0.6), (ub + 0.3, 'click', 0.6), (ub + 0.5, 'whoosh', 0.7),
                    (wt(12, 6), 'chime_a', 0.5), (ua12, 'chime_c', 0.5)]
    E[13]['sfx'] = [(0.0, 'whoosh', 0.6), (0.15, 'thud', 0.6), (1.0, 'click', 0.8), (1.05, 'chime_b', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
