"""Reel diario vie 20-nov-2026 18:00 — «Tu casco de media calabaza… no es casco.» (un casco de verdad trae por dentro
una capa de unicel firme de ~2.5 cm que se aplasta a propósito: la cabeza frena en ~6 milésimas y no en 1; el de adorno
trae pura esponja o nada y pesa ~0.5 kg contra ~1.4 kg; segundo gancho: la correa: en el estudio europeo MAIDS casi
7 de cada 10 cascos que salieron volando iban mal abrochados; si ya se golpeó, se cambia: el unicel aplastado no
regresa; según la OMS, bien puesto baja hasta 74 % las lesiones del cerebro).
Comunidad: motos (en la CDMX casi la mitad de las muertes viales son de motociclistas). Inicio tipo 3 (se arma solo):
la cáscara, el unicel, el forro y la correa vuelan y se juntan con clic; el de media calabaza se arma… sin unicel
(«CASCO» de cristal detrás). El final («y antes de subirte, revisa el tuyo por dentro…») muestra las piezas flotando
separadas = la escena 0 en pre-roll (loop). Voz: plan B (Chatterbox) porque ElevenLabs pidió volver a iniciar sesión.
Fuentes: guiones/2026-11-20_casco.txt. Sin personas: la cabeza es una horma de prueba metálica sin cara.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import texto, esquema, golpe_k, sacudir, K, camara, tubo

M3 = M.M3
TEMA = 'casco'
TXT = ['Tu casco de media calabaza… no es casco.',
       'En la Ciudad de México, casi la mitad de los muertos del tránsito',
       'iban en moto.',
       'Uno de verdad trae por dentro una capa de unicel firme.',
       'Mide como 2.5 cm,',
       'y se aplasta a propósito.',
       'Así tu cabeza frena en 6 milésimas de segundo y no en 1:',
       'el golpe llega más suave.',
       'El de adorno trae pura esponja, o nada, y pesa medio kilo;',
       'el bueno, casi kilo y medio.',
       'Pero el error de casi todos no es el casco…',
       'es la correa.',
       'En un estudio europeo, casi 7 de cada 10 cascos que salieron volando',
       'iban mal abrochados.',
       'Floja o colgando,',
       'en el golpe el casco se va antes que tu cabeza.',
       'Y si ya se golpeó, cámbialo:',
       'el unicel aplastado no regresa, aunque se vea bien.',
       'Bien abrochado, según la OMS,',
       'baja hasta 74 % las lesiones del cerebro.',
       'Mándaselo a tu compa que anda en moto con el casco colgando.',
       'Y antes de subirte, revisa el tuyo por dentro…']
VOZ = ['Tu casco de media calabaza... no es casco.',
       'En la Ciudad de México, casi la mitad de los muertos del tránsito',
       'iban en moto.',
       'Uno de verdad trae por dentro una capa de unicel firme.',
       'Mide como dos centímetros y medio,',
       'y se aplasta a propósito.',
       'Así tu cabeza frena en seis milésimas de segundo y no en una:',
       'el golpe llega más suave.',
       'El de adorno trae pura esponja, o nada, y pesa medio kilo;',
       'el bueno, casi kilo y medio.',
       'Pero el error de casi todos no es el casco...',
       'es la correa.',
       'En un estudio europeo, casi siete de cada diez cascos que salieron volando',
       'iban mal abrochados.',
       'Floja o colgando,',
       'en el golpe el casco se va antes que tu cabeza.',
       'Y si ya se golpeó, cámbialo:',
       'el unicel aplastado no regresa, aunque se vea bien.',
       'Bien abrochado, según la OMS,',
       'baja hasta setenta y cuatro por ciento las lesiones del cerebro.',
       'Mándaselo a tu compa que anda en moto con el casco colgando.',
       'Y antes de subirte, revisa el tuyo por dentro...']
assert len(VOZ) == len(TXT)

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
VERDE = (60, 215, 120)
ROJO_C = (190, 30, 34)        # cáscara del casco certificado
NEGRO_C = (74, 76, 86)        # media calabaza (gris oscuro brillante)
EPS = (238, 236, 228)         # unicel
FORRO = (60, 62, 70)
HORMA = (168, 172, 180)
HY = 1.0                      # altura del centro del casco


def Wp(i, palabra, n=0):
    """u (desde el inicio de la frase i) de la palabra que empieza con `palabra` (reparto por letras, como el words.json)."""
    T = montaje.CTX.get('T')
    if not T:
        return 0.0
    a, b = T[i]
    ws = VOZ[i].split()
    nn = [montaje._norm(w) for w in ws]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(nn) if w.startswith(p)]
    if not hits:
        return 0.0
    k = hits[min(n, len(hits) - 1)]
    wt = [len(w) + 1 + (5 if w.endswith('...') else 3 if w[-1] in ':;' else 2 if w[-1] in ',.' else 0) for w in ws]
    return (b - a) * sum(wt[:k]) / sum(wt)


# ------------------------------------------------------------------ objetos
def domo(r, col, vf, vb, u0=0.0, u1=2 * math.pi, nu=40, nv=12, name='cascara', gloss=0.8, rim=0.8, sy=1.0, glow=None):
    """Cúpula (casco) de radio r: baja hasta vf·π al frente (+z) y vb·π atrás. u0–u1 recorta (para el corte)."""
    full = abs(u1 - u0 - 2 * math.pi) < 1e-6
    nU = nu if full else nu + 1
    V, F = [], []
    for i in range(nU):
        u = u0 + (u1 - u0) * i / nu
        b = (1 - math.sin(u)) / 2
        vmax = math.pi * (vf + (vb - vf) * b)
        for j in range(nv + 1):
            v = vmax * j / nv
            V.append((r * math.sin(v) * math.cos(u), sy * r * math.cos(v), r * math.sin(v) * math.sin(u)))
    for i in range(nu):
        i2 = (i + 1) % nU if full else i + 1
        for j in range(nv):
            a, b_ = i * (nv + 1) + j, i2 * (nv + 1) + j
            F.append((a, b_, b_ + 1, a + 1))
    m = named(M3.Mesh(V, F, col, shadow=0, gloss=gloss, double=True), name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    return m


def vmax_de(u, vf, vb):
    return math.pi * (vf + (vb - vf) * (1 - math.sin(u)) / 2)


def horma_m(x=0.0, y=HY, z=0.0, s=1.0):
    """Horma de prueba (cabeza metálica sin cara) con su cuello."""
    h = named(M3.sphere(0.4, HORMA, nu=30, nv=18, shadow=0, gloss=0.7).tf(s=(0.92, 1.22, 1.06)).tf(t=(0, -0.13, 0.0)),
              'horma', rim=0.8, gloss=0.7)
    c = named(M3.cyl(0.17, 0.45, (120, 124, 132), n=22, shadow=0, gloss=0.6).tf(t=(0, -0.95, -0.03)), 'horma', rim=0.7)
    return P.tfk([h, c], s=s, t=(x, y, z))


def correa(floja=0.0, abierta=0.0, col=(40, 40, 46)):
    """Correa de la barbilla: de oreja a oreja pasando bajo la barbilla de la horma; floja = cuelga más abajo."""
    pts = []
    for q in np.linspace(0, 1, 13):
        x = -0.38 + 0.76 * q
        y = -0.06 - 0.55 * math.sin(math.pi * q) - 0.35 * floja * math.sin(math.pi * q)
        z = 0.06 + 0.2 * math.sin(math.pi * q)
        pts.append((x, y, z))
    ms = []
    n = len(pts) - 1
    for i in range(n):
        if abierta > 0.01 and abs(i - n / 2) < 1.0:
            continue
        p0, p1 = list(pts[i]), list(pts[i + 1])
        if abierta > 0.01 and i < n / 2:
            p1[1] -= 0.0
        ms.append(tubo(tuple(p0), tuple(p1), r=0.018, col=col, name='correa', gloss=0.3))
    mid = pts[n // 2]
    dx = 0.09 * abierta
    ms.append(named(M3.box(0.07, 0.05, 0.03, (150, 152, 160), shadow=0, gloss=0.9, base=False)
                    .tf(t=(mid[0] - 0.035 - dx, mid[1], mid[2] + 0.01)), 'hebilla', rim=0.9))
    ms.append(named(M3.box(0.06, 0.04, 0.03, (190, 60, 50), shadow=0, gloss=0.8, base=False)
                    .tf(t=(mid[0] + 0.035 + dx, mid[1], mid[2] + 0.01)), 'hebilla', rim=0.9))
    return ms


def casco_m(tipo='bueno', u0=0.0, u1=2 * math.pi, partes=('cascara', 'eps', 'forro', 'correa'), floja=0.0, abierta=0.0,
            col=None):
    """Casco centrado en (0, 0, 0): certificado (cáscara + unicel + forro + correa) o de adorno (cáscara + esponja)."""
    ms = []
    if tipo == 'bueno':
        vf, vb = 0.5, 0.62
        if 'cascara' in partes:
            ms.append(domo(0.52, col or ROJO_C, vf, vb, u0, u1, name='cascara', gloss=0.9))
        if 'eps' in partes:
            ms.append(domo(0.495, EPS, vf - 0.01, vb - 0.01, u0, u1, name='eps', gloss=0.12, rim=0.4))
        if 'forro' in partes:
            ms.append(domo(0.43, FORRO, vf - 0.03, vb - 0.03, u0, u1, name='forro', gloss=0.1, rim=0.3))
    else:
        vf = vb = 0.37
        if 'cascara' in partes:
            ms.append(domo(0.47, col or NEGRO_C, vf, vb, u0, u1, name='cascara', gloss=0.95, rim=1.0))
        if 'eps' in partes:     # «esponja»: capa delgadita
            ms.append(domo(0.455, (80, 80, 86), vf - 0.01, vb - 0.01, u0, u1, name='esponja', gloss=0.05, rim=0.2))
    if 'correa' in partes:
        ms += correa(floja, abierta)
    return ms


def casco_en(tipo='bueno', x=0.0, y=HY, z=0.0, ry=0.0, rx=0.0, rz=0.0, s=1.0, **kw):
    return P.tfk(P.tfk(casco_m(tipo, **kw), s=s, rx=rx, ry=ry, rz=rz), t=(x, y, z))


def banda(fr, r0, r1, vf, vb, col, a=1.0, x=0.0, y=HY, z=0.0, s=1.0, glow=None, aplastado=0.0, puntos=False):
    """Corte transversal (plano x = 0) de una capa entre los radios r0 y r1: el frente (+z) y la espalda (−z)."""
    for lado, u in ((1, math.pi / 2), (-1, 3 * math.pi / 2)):
        vm = vmax_de(u, vf, vb)
        vs = np.linspace(0, vm, 30)
        def rin(v):
            ap = aplastado * math.exp(-((v - 0.55) / 0.22) ** 2) if lado == 1 else 0.0
            return r0 + (r1 - r0) * 0.75 * ap
        outer = [(x, y + s * r1 * math.cos(v), z + lado * s * r1 * math.sin(v)) for v in vs]
        inner = [(x, y + s * rin(v) * math.cos(v), z + lado * s * rin(v) * math.sin(v)) for v in vs[::-1]]
        S, Z = fr.cam.proj(outer + inner)
        if (Z < 0.2).any():
            continue
        fr.db.polygon([tuple(p) for p in S], fill=M.scale_c(col, a))
        if glow:
            fr.df.polygon([tuple(p) for p in S], fill=M.scale_c(glow, a))
        if puntos:                                           # textura de bolitas del unicel
            rng = np.random.RandomState(3 if lado == 1 else 4)
            for _ in range(70):
                v = rng.rand() * vm
                rr = rin(v) + (r1 - rin(v)) * rng.rand()
                p = (x, y + s * rr * math.cos(v), z + lado * s * rr * math.sin(v))
                ss, zz = fr.cam.proj([p])
                if zz[0] > 0.2:
                    px, py = ss[0]
                    q = 2.2 * M.SS * (1 - 0.6 * (aplastado * math.exp(-((v - 0.55) / 0.22) ** 2) if lado == 1 else 0))
                    fr.db.ellipse((px - q, py - q, px + q, py + q), outline=M.scale_c((150, 150, 140), a), width=1)


def corte(fr, tipo='bueno', x=0.0, y=HY, z=0.0, s=1.0, a=1.0, aplastado=0.0):
    """Las capas del casco en corte (para verlas de lado)."""
    if tipo == 'bueno':
        banda(fr, 0.495, 0.52, 0.5, 0.62, ROJO_C, a, x, y, z, s)
        banda(fr, 0.43, 0.495, 0.49, 0.61, EPS, a, x, y, z, s, glow=(30, 30, 28), aplastado=aplastado, puntos=True)
        banda(fr, 0.415, 0.43, 0.47, 0.59, FORRO, a, x, y, z, s)
    else:
        banda(fr, 0.455, 0.47, 0.37, 0.37, (70, 70, 76), a, x, y, z, s)
        banda(fr, 0.445, 0.455, 0.36, 0.36, (100, 100, 108), a, x, y, z, s)


def moto_linea(fr, x=0.0, y=0.0, z=0.0, s=1.0, k=1.0, t=0.0, col=WHITE):
    """Moto en line-art que brilla (de lado, plano z)."""
    if k <= 0.01:
        return
    q = np.linspace(0, 2 * math.pi, 40)
    for cx in (-0.62, 0.62):
        for rr in (0.3, 0.22):
            line3(fr, [(x + s * (cx + rr * math.cos(a)), y + s * (0.3 + rr * math.sin(a)), z) for a in q], col=col, w=2.6, a=k, glow=0.8)
        for j in range(6):
            a = t * 6 + j * math.pi / 3
            line3(fr, [(x + s * cx, y + s * 0.3, z), (x + s * (cx + 0.22 * math.cos(a)), y + s * (0.3 + 0.22 * math.sin(a)), z)],
                  col=col, w=1.4, a=0.6 * k, glow=0.5)
    fr_pts = [(-0.62, 0.3), (-0.1, 0.62), (0.3, 0.62), (0.62, 0.3), (0.4, 0.95), (0.3, 0.62)]
    line3(fr, [(x + s * a, y + s * b, z) for a, b in fr_pts], col=col, w=3.0, a=k, glow=0.8)
    line3(fr, [(x + s * a, y + s * b, z) for a, b in [(-0.45, 0.72), (0.15, 0.72)]], col=col, w=5.0, a=k, glow=0.8)
    line3(fr, [(x + s * a, y + s * b, z) for a, b in [(0.4, 0.95), (0.3, 1.05), (0.5, 1.08)]], col=col, w=3.0, a=k, glow=0.8)
    line3(fr, [(x + s * a, y + s * b, z) for a, b in [(-0.1, 0.62), (-0.05, 0.42), (0.2, 0.42), (0.3, 0.62)]], col=col, w=2.4,
          a=k, glow=0.7)
    for poly, ww in (([(-0.12, 0.6), (-0.12, 0.34), (0.26, 0.34), (0.3, 0.6)], 4.0),                 # motor
                     ([(-0.05, 0.72), (0.05, 0.84), (0.34, 0.86), (0.4, 0.74), (0.3, 0.68), (-0.05, 0.72)], 4.0),  # tanque
                     ([(0.0, 0.36), (-0.4, 0.32), (-0.85, 0.42)], 5.0)):                                  # escape
        line3(fr, [(x + s * a, y + s * b, z) for a, b in poly], col=col, w=ww, a=k, glow=0.8)


def bascula(fr, x, y=0.0, z=0.0, s=1.0):
    return P.tfk([named(M3.rbox(0.9, 0.12, 0.7, 0.06, (54, 56, 62), n=4, shadow=0, gloss=0.5), 'bascula', rim=0.7),
                  named(M3.box(0.86, 0.02, 0.66, (120, 124, 132), shadow=0, gloss=0.8).tf(t=(0, 0.12, 0)), 'bascula', rim=0.8)],
                 s=s, t=(x, y, z))


def display(img, fx, x, y, txt, k=1.0, col=VERDE):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.rounded_rectangle((x - 150, y - 52, x + 150, y + 52), radius=14, fill=(10, 14, 12), outline=M.scale_c(col, 0.6 * k), width=3)
    d.text((x, y), txt, font=M.font('mono', 54), fill=M.scale_c(col, k), anchor='mm')
    df.text((x, y), txt, font=M.font('mono', 54), fill=M.scale_c(col, 0.6 * k), anchor='mm')


def dona(img, fx, cx, cy, R, frac, k=1.0, col=RED, txt=None, size=110):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c((70, 72, 80), k), width=34)
    if frac > 0.002:
        d.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * frac, fill=M.scale_c(col, k), width=34)
        df.arc((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * frac, fill=M.scale_c(col, 0.6 * k), width=50)
    if txt:
        texto(img, fx, cx, cy, txt, size, col=WHITE, k=k, f='sansx', glow=0.3)


def icono_casco(d, df, x, y, w, col, glow=0.0):
    d.chord((x - w / 2, y - w / 2, x + w / 2, y + w / 2), 180, 360, fill=col)
    d.rectangle((x - w / 2, y - 4, x + w / 2 + w * 0.12, y + 6), fill=col)
    if glow:
        df.chord((x - w / 2, y - w / 2, x + w / 2, y + w / 2), 180, 360, fill=M.scale_c(col, glow))


def scr_chat(k=1.0):
    def dib(d, im):
        f = M.font
        d.text((34, 90), 'Tu compa', font=f('sanss', 30), fill=(235, 235, 240))
        d.line([(0, 140), (420, 140)], fill=(40, 42, 48), width=2)
        d.rounded_rectangle((30, 200, 340, 300), radius=26, fill=(44, 46, 54))
        d.text((54, 222), 'Nel, el casco nomás', font=f('sanss', 25), fill=(235, 235, 240))
        d.text((54, 256), 'lo traigo colgando', font=f('sanss', 25), fill=(235, 235, 240))
        if k > 0.5:
            d.rounded_rectangle((100, 340, 392, 470), radius=26, fill=(36, 120, 80))
            d.text((124, 362), 'Abróchalo, wey.', font=f('sanss', 26), fill=(245, 245, 247))
            d.text((124, 396), 'Mira por qué:', font=f('sanss', 26), fill=(245, 245, 247))
            d.text((124, 430), 'video', font=f('sanss', 22), fill=(200, 230, 210))
    return P.pantalla(dib)


# ================================================================== escenas
# 0. gancho (inicio 3: se arma solo). Pre-roll (lo que se ve al final, loop): las piezas del casco flotan separadas y
#    giran con «CASCO» de cristal detrás. En u = 0 vuelan y se juntan con clic (0.8 s) en un casco de media calabaza…
#    y el hueco del unicel queda marcado: «SIN UNICEL».
U_CLIC = 0.8


def s_gancho(t, fi, u, d):
    un = Wp(0, 'no') - 0.05
    fr = Frame(camara(u, [K(-4.0, 3.6, -70, 18, ty=HY), K(-0.5, 3.3, -50, 14, ty=HY), K(U_CLIC, 2.5, 18, 8, ty=HY - 0.05),
                          K(un, 2.3, 26, 8, ty=HY - 0.05), K(5.0, 2.2, 30, 8, ty=HY - 0.05)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'CASCO', u, t0=-3.3, cy=0.43, entrada='golpe')
    k = 1.0 if u < 0 else 1 - P.eout4(seg(u, 0.0, U_CLIC))
    flota = 0.04 * math.sin(t * 1.7) * (1 if u < 0 else 0)
    ms = casco_m('adorno', partes=('cascara', 'correa'))
    ms = P.despiece(ms, k, centro=(0, -0.25, 0), fuerza=1.1, giro=0.9)
    hy = 0.65 + flota + (2.4 * P.eout4(seg(u, 0.1, U_CLIC + 0.2)) if u > 0 else 0.0)
    hueco = P.tfk([domo(0.44, EPS, 0.36, 0.36, name='hueco', gloss=0.1)], rz=-40 * seg(u, 0.1, U_CLIC), t=(0.5 * seg(u, 0.1, U_CLIC), hy, 0))
    draw_objects(fr, P.tfk(ms, ry=12 * math.sin(t * 0.6), t=(0, HY + flota, 0)))
    if u < U_CLIC + 0.2:
        draw_objects(fr, P.tfk(hueco, t=(0, HY, 0)))
    else:                                                     # el lugar del unicel: solo una línea punteada
        q = np.linspace(0, 2 * math.pi, 60)
        for j in range(0, 60, 2):
            a0, a1 = q[j], q[min(59, j + 1)]
            line3(fr, [(0.44 * math.cos(a0), HY + 0.1, 0.44 * math.sin(a0)), (0.44 * math.cos(a1), HY + 0.1, 0.44 * math.sin(a1))],
                  col=RED, w=2.6, a=seg(u, U_CLIC, U_CLIC + 0.3), glow=0.9)
    ph = fr.cam.p1((0, HY - 0.05, 0.3))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Tu casco de media calabaza…', 'sans'), ('no es casco.', 'serif')], 190,
                       seg(u, un - 0.1, un + 0.05), size=58)
        kicker(img, 'SE ARMA SOLO', 1290, seg(u, 0.0, 0.2) * (1 - seg(u, U_CLIC + 0.4, U_CLIC + 0.6)), col=AZULC)
        pill(img, fx, ph[0], ph[1] + 260, 'SIN UNICEL', eout(seg(u, U_CLIC + 0.1, U_CLIC + 0.35)), size=34, border=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, U_CLIC, 0.3), golpe_k(u, un + 0.05, 0.3)), amp=20)


# 1. en la CDMX casi la mitad de los muertos del tránsito: la dona que se llena a la mitad («MITAD» de cristal)
def s_mitad(t, fi, u, d):
    um = Wp(1, 'mitad') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, 0, 55, ty=0.0), K(0.3, 4.2, 20, 48, ty=0.0), K(d, 4.1, 24, 48, ty=0.0)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=0.9, beam=0.3)
    M.cristal(fr.base, fr.fx, 'MITAD', u, t0=um - 0.1, cy=0.32, entrada='sube')
    rng = np.random.RandomState(2)
    for j in range(40):                                          # tráfico: luces que corren por las calles
        lane = rng.randint(-3, 4) * 0.6
        ph = (t * (0.15 + 0.1 * rng.rand()) + rng.rand()) % 1.0
        x, z = (lane, -2.5 + 5 * ph) if j % 2 else (-2.5 + 5 * ph, lane)
        dot3(fr, (x, 0.02, z), r=3.5, col=(RED if (j % 4 == 0 and u > um) else WARM), a=0.8, glow=1.0)

    def ui(img, fx):
        kicker(img, 'CIUDAD DE MÉXICO · 2025', 1060, seg(u, 0.0, 0.3), col=AZULC)
        dona(img, fx, 540, 1300, 170, 0.49 * P.eout4(seg(u, um, um + 0.8)), k=seg(u, 0.0, 0.3),
             txt=f'{49 * P.eout4(seg(u, um, um + 0.8)):.0f} %', size=84)
    fr.ui.append(ui)
    return finish(fr, fi)


WARM = (255, 214, 150)


# 2. iban en moto: la moto en line-art se dibuja y la dona queda marcada en rojo
def s_moto(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, 30, 8, ty=0.6), K(0.25, 2.8, 4, 6, ty=0.6), K(d, 2.75, 0, 6, ty=0.6)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'desliza')
    moto_linea(fr, x=-e['dy'] * 0.6, y=0.15, s=0.95, k=1.0, t=t, col=WHITE)
    for j in range(5):
        line3(fr, [(-2.0 - j * 0.3, 0.2 + 0.15 * j, 0), (-1.4 - j * 0.3, 0.2 + 0.15 * j, 0)], col=AZULC, w=2, a=0.5 * seg(u, 0.1, 0.3),
              glow=0.7)

    def ui(img, fx):
        dona(img, fx, 840, 360, 110, 0.49, k=seg(u, -0.2, 0.1), col=RED, txt='49 %', size=54)
        kicker(img, 'IBAN EN MOTO', 560, seg(u, 0.1, 0.4), col=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.3), amp=14)


# 3. uno de verdad trae por dentro una capa de unicel firme: casco rojo en la horma; rayos X y el unicel queda solo
def s_unicel(t, fi, u, d):
    uu = Wp(3, 'unicel') - 0.1
    fr = Frame(camara(u, [K(-0.3, 1.2, 10, 10, ty=HY), K(0.35, 2.6, 34, 12, ty=HY - 0.1), K(d, 2.55, 40, 12, ty=HY - 0.1)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'UNICEL', u, t0=uu - 0.15, cy=0.3, entrada='golpe')
    xr = seg(u, uu - 0.3, uu)
    draw_objects(fr, casco_en('bueno', ry=20 + 10 * t) + horma_m(), xray=xr, keep=('eps', 'horma'))
    pe = fr.cam.p1((0.0, HY + 0.52, 0.0))

    def ui(img, fx):
        kicker(img, 'CASCO CERTIFICADO', 150, seg(u, 0.0, 0.3), col=AZULC)
        pill(img, fx, pe[0], pe[1] - 120, 'UNICEL FIRME (EPS)', eout(seg(u, uu, uu + 0.25)), size=32, border=WHITE)
        esquema(img, fx, seg(u, 0.3, 0.5), y=1450)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uu, 0.3), amp=12)


# 4. mide como 2.5 cm: el casco se corta a la mitad (vista de lado) y una cota amarilla mide el unicel
def s_mide(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.0, 60, 6, ty=HY + 0.1), K(0.3, 1.6, 88, 4, ty=HY + 0.15, tz=0.15),
                          K(d, 1.55, 90, 4, ty=HY + 0.15, tz=0.15)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.9, beam=0.4)
    draw_objects(fr, casco_en('bueno', u0=math.pi / 2, u1=3 * math.pi / 2, partes=('cascara', 'eps', 'forro')))
    corte(fr, 'bueno', a=1.0)
    v = 0.25 * math.pi
    p0 = (0.001, HY + 0.43 * math.cos(v), 0.43 * math.sin(v))
    p1 = (0.001, HY + 0.495 * math.cos(v), 0.495 * math.sin(v))
    k = seg(u, 0.2, 0.5)
    line3(fr, [p0, p1], col=AMARILLO, w=3, a=k, glow=0.9)
    pa, pb = fr.cam.p1(p0), fr.cam.p1(p1)

    def ui(img, fx):
        kicker(img, 'EN CORTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        texto(img, fx, mx + 170, my - 90, '≈ 2.5 cm', 64, col=AMARILLO, k=seg(u, 0.35, 0.55), f='sansx', glow=0.5)
        doodle_arrow(img, fx, mx + 110, my - 60, mx + 20, my - 10, t, k=seg(u, 0.4, 0.6), col=AMARILLO, seed=2)
        pill(img, fx, 540, 1260, 'CÁSCARA · UNICEL · FORRO', eout(seg(u, 0.6, 0.85)), size=28, border=WHITE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. y se aplasta a propósito: un bloque de unicel bajo una prensa: las bolitas se aplastan y regresa la prensa
def s_aplasta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.6, -30, 14, ty=0.45), K(0.3, 2.1, 10, 10, ty=0.45), K(d, 2.05, 14, 10, ty=0.45)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    pr = P.eout4(seg(u, 0.25, 0.6))
    hb = 0.5 * (1 - 0.45 * pr)
    ms = [named(M3.box(0.9, hb, 0.6, (176, 174, 166), shadow=0, gloss=0.05), 'eps', rim=0.3),
          named(M3.box(1.1, 0.08, 0.8, (150, 154, 162), shadow=0, gloss=0.8).tf(t=(0, hb + 0.6 * (1 - seg(u, 0.0, 0.25)) * (1 - pr), 0)),
                'prensa', rim=0.8),
          named(M3.cyl(0.06, 1.4, (120, 124, 132), n=12, shadow=0, gloss=0.8).tf(t=(0, hb + 0.08, 0)), 'prensa', rim=0.8)]
    draw_objects(fr, ms)
    rng = np.random.RandomState(5)
    for j in range(80):                                       # bolitas de la cara frontal
        x, yy = (rng.rand() - 0.5) * 0.86, rng.rand()
        p = (x, yy * hb, 0.305)
        ss, z = fr.cam.proj([p])
        px, py = ss[0]
        rx, ry = 7 * M.SS * (1 + 0.3 * pr), 7 * M.SS * (1 - 0.55 * pr)
        fr.db.ellipse((px - rx, py - ry, px + rx, py + ry), outline=(170, 168, 160), width=2)
    pc = fr.cam.p1((0, hb + 0.1, 0.3))

    def ui(img, fx):
        kicker(img, 'UNICEL BAJO PRESIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pc[0], pc[1] - 200, 'SE APLASTA = FRENA', eout(seg(u, 0.6, 0.85)), size=32, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.6, 0.3), amp=18)


# 6. así tu cabeza frena en 6 milésimas y no en 1: prueba de caída sobre un yunque + gráfica que crece («6 ms»)
def s_frena(t, fi, u, d):
    u6 = Wp(6, 'seis') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, -24, 8, ty=1.1), K(0.3, 3.0, 12, 6, ty=1.1), K(d, 2.95, 16, 6, ty=1.1)], cy=0.42))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, '6 ms', u, t0=u6 - 0.1, cy=0.27, entrada='zoom')
    ui_ = seg(u, 0.0, 0.45)
    yy = 2.6 - 1.4 * ui_ ** 2 if u < 0.45 else 1.2 + 0.08 * math.sin(min(1.0, (u - 0.45) * 4) * math.pi) * math.exp(-(u - 0.45) * 6)
    ms = [named(M3.cyl(0.32, 0.25, (110, 112, 120), n=28, shadow=0, gloss=0.7), 'yunque', rim=0.8)]
    ms += P.tfk(casco_m('bueno') + P.tfk(horma_m(y=0.0), t=(0, 0, 0)), t=(0, yy + 0.25 - 0.62 + 0.52 + 0.05, 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'PRUEBA DE CAÍDA', 150, seg(u, -0.1, 0.2), col=AZULC)
        chart_grow(img, fx, (130, 1030, 950, 1470), [1, 6], ['SIN', 'CON'], u6, u, unit='', title_txt='MILÉSIMAS PARA FRENAR',
                   vmax=7, line=False, tag='UNICEL')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.45, 0.35), amp=22)


# 7. el golpe llega más suave: dos curvas de fuerza: pico alto y angosto (sin) contra loma baja y ancha (con)
def s_suave(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.2, 40, 10, ty=HY), K(0.3, 2.6, 70, 8, ty=HY), K(d, 2.6, 76, 8, ty=HY)], cy=0.36))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.4)
    draw_objects(fr, casco_en('bueno', ry=-30 + 8 * t) + horma_m())

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        x0, y0, w, h = 150, 1440, 780, 420
        k1, k2 = seg(u, 0.0, 0.5), seg(u, 0.4, 1.0)
        d_.line([(x0, y0), (x0 + w, y0)], fill=(80, 84, 92), width=3)
        d_.text((x0, y0 - h - 40), 'FUERZA EN TU CABEZA', font=M.font('mono', 26), fill=(160, 162, 170))
        for kk, (amp, ancho, c, lab) in ((k1, (1.0, 0.035, RED, 'SIN UNICEL')), (k2, (0.22, 0.17, VERDE, 'CON UNICEL'))):
            if kk <= 0.01:
                continue
            n = int(160 * kk)
            pts = [(x0 + w * i / 160, y0 - h * amp * math.exp(-((i / 160 - 0.35) / ancho) ** 2)) for i in range(n)]
            if len(pts) > 1:
                d_.line(pts, fill=c, width=5, joint='curve')
                df.line(pts, fill=M.scale_c(c, 0.7), width=11, joint='curve')
            d_.text((x0 + w * 0.6, y0 - h * amp * 0.9 - 10), lab, font=M.font('mono', 26), fill=c)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. el de adorno trae pura esponja, o nada, y pesa medio kilo: media calabaza en rayos X sobre la báscula (0.5 kg)
def s_adorno(t, fi, u, d):
    um = Wp(8, 'medio') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.8, -40, 16, ty=0.45), K(0.35, 2.3, -14, 12, ty=0.45), K(d, 2.25, -10, 12, ty=0.45)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    xr = seg(u, 0.4, 0.7) * (1 - seg(u, um + 0.4, um + 0.6))
    ms = bascula(fr, 0.0) + casco_en('adorno', y=0.14 + max(0.0, -e['dy']), ry=15, partes=('cascara', 'eps', 'correa'))
    draw_objects(fr, ms, xray=xr, keep=('esponja', 'bascula', 'correa', 'hebilla'))
    pc = fr.cam.p1((0, 0.5, 0.3))

    def ui(img, fx):
        kicker(img, 'CASCO DE ADORNO', 150, seg(u, -0.1, 0.2), col=RED)
        pill(img, fx, pc[0], pc[1] - 260, 'PURA ESPONJA', eout(seg(u, 0.5, 0.75)), size=32, border=RED)
        display(img, fx, 540, 1250, f'{0.45 * P.eout4(seg(u, 0.15, 0.7)):.2f} kg', k=seg(u, 0.0, 0.2), col=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.3), amp=12)


_FOTO = {}


def foto():
    if 'f' not in _FOTO:
        _FOTO['f'] = Image.open(os.path.join(HERE, 'img', 'casco', 'casco_i_real.jpg')).convert('RGB')
    return _FOTO['f']


# 9. el bueno, casi kilo y medio: el certificado cae en la báscula y marca 1.4 kg (+ foto real de un casco, CC0)
def s_bueno(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.25, 14, 12, ty=0.5), K(0.3, 2.4, 34, 12, ty=0.5), K(d, 2.35, 38, 12, ty=0.5)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.15, 0.35, 'cae')
    draw_objects(fr, bascula(fr, 0.0) + casco_en('bueno', y=0.14 + 0.36 + max(0.0, -e['dy']), ry=-20))

    def ui(img, fx):
        kicker(img, 'CASCO CERTIFICADO', 150, seg(u, -0.1, 0.2), col=VERDE)
        display(img, fx, 540, 1250, f'{1.36 * P.eout4(seg(u, 0.2, 0.9)):.2f} kg', k=1.0, col=VERDE)
        pill(img, fx, 540, 1370, 'CON UNICEL', eout(seg(u, 0.6, 0.85)), size=28, border=VERDE)
        if u > 0.5:
            M.photo_card(img, fx, foto(), 800, 470, 330, t - u + 0.5, t, caption='Casco real · CC0', angle0=8.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=16)


# 10. pero el error de casi todos no es el casco… (segundo gancho): el casco en la horma y la correa colgando en rojo
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, 0, 20, ty=HY - 0.2), K(0.3, 2.6, -24, 10, ty=HY - 0.2), K(d, 2.55, -28, 10, ty=HY - 0.2)],
                      cy=0.55))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.6, beam=0.8)
    ms = casco_en('bueno', partes=('cascara', 'eps', 'forro')) + horma_m()
    ms += P.tfk(correa(floja=0.6 + 0.08 * math.sin(t * 3), col=M.mixc((40, 40, 46), RED, 0.6 + 0.4 * math.sin(t * 6) ** 2)),
                t=(0, HY, 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, 0.0, 0.2), col=RED)
        P.titulo_golpe(img, fx, [('El error de casi todos', 'sans'), ('no es el casco…', 'serif')], 230, seg(u, 0.1, 0.25), size=70)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.3), amp=22)


# 11. es la correa: crash zoom a la hebilla abierta («CORREA» de cristal), garabato rojo
def s_correa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.6, -20, 6, ty=HY - 0.4), K(0.12, 1.75, 18, -6, ty=HY - 0.72, tz=0.15),
                          K(d, 1.7, 22, -6, ty=HY - 0.72, tz=0.15)], cy=0.42))
    space(fr, t, floor='lines', floor_a=0.4, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'CORREA', u, t0=-0.1, cy=0.68, entrada='golpe')
    ms = casco_en('bueno', partes=('cascara', 'eps', 'forro')) + horma_m() + P.tfk(correa(floja=0.5, abierta=1.0), t=(0, HY, 0))
    draw_objects(fr, ms)
    pb = fr.cam.p1((0, HY - 0.06 - 0.55 - 0.18, 0.27))

    def ui(img, fx):
        doodle_circle(img, fx, pb[0], pb[1], 200, 150, t, k=eout(seg(u, 0.1, 0.35)), col=RED, seed=8)
        pill(img, fx, pb[0], pb[1] + 230, 'DESABROCHADA', eout(seg(u, 0.25, 0.45)), size=34, border=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.12, 0.3), amp=22)


# 12. en un estudio europeo, casi 7 de cada 10 cascos que salieron volando: 10 cascos, 7 se ponen rojos («7 DE 10»)
def s_estudio(t, fi, u, d):
    u7 = Wp(12, 'siete') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, 0, 10, ty=1.0), K(0.3, 3.6, 10, 8, ty=1.0), K(d, 3.55, 14, 8, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, '7 DE 10', u, t0=u7 - 0.1, cy=0.62, entrada='sube')

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        kicker(img, 'ESTUDIO MAIDS · EUROPA', 150, seg(u, 0.0, 0.3), col=AZULC)
        texto(img, fx, 540, 300, 'CASCOS QUE SALIERON VOLANDO', 34, col=WHITE, k=seg(u, 0.2, 0.4), f='sanss', glow=0.2)
        for i in range(10):
            ki = seg(u, 0.25 + 0.06 * i, 0.4 + 0.06 * i)
            if ki <= 0.01:
                continue
            x, y = 180 + (i % 5) * 180, 470 + (i // 5) * 190 - 40 * (1 - P.rebote(ki))
            rojo = i < 7 and u > u7 + 0.08 * i
            icono_casco(d_, df, x, y, 120, RED if rojo else (120, 124, 134), glow=0.6 if rojo else 0)
        pill(img, fx, 540, 1250, '68 % · MAL ABROCHADOS O ALTERADOS', eout(seg(u, u7 + 0.6, u7 + 0.9)), size=26, border=RED)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. iban mal abrochados: la hebilla abierta, en macro, se separa
def s_abrochados(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 1.8, 40, -12, ty=HY - 0.62, tz=0.2), K(0.3, 1.35, -14, -8, ty=HY - 0.66, tz=0.2),
                          K(d, 1.3, -18, -8, ty=HY - 0.66, tz=0.2)], cy=0.42))
    space(fr, t, floor=None, bokeh=0.9, beam=0.4)
    ab = 0.3 + 0.7 * P.eout4(seg(u, 0.2, 0.6))
    ms = horma_m() + P.tfk(correa(floja=0.3, abierta=ab), t=(0, HY, 0))
    draw_objects(fr, ms)
    pb = fr.cam.p1((0, HY - 0.61, 0.27))

    def ui(img, fx):
        pill(img, fx, pb[0], pb[1] - 260, 'MAL ABROCHADO', eout(seg(u, 0.4, 0.65)), size=36, border=RED)
        texto(img, fx, pb[0], pb[1], '✕', 90, col=RED, k=seg(u, 0.6, 0.75), f='sansx', glow=0.6)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. floja o colgando: la correa columpiándose lejos de la barbilla con una cota «HUECO»
def s_floja(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.6, 60, 4, ty=HY - 0.35), K(0.3, 2.2, 80, 2, ty=HY - 0.4), K(d, 2.15, 84, 2, ty=HY - 0.4)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    sw = 0.9 + 0.12 * math.sin(t * 3.2)
    ms = casco_en('bueno', partes=('cascara', 'eps', 'forro')) + horma_m() + P.tfk(correa(floja=sw), t=(0, HY, 0))
    draw_objects(fr, ms)
    pa = fr.cam.p1((0, HY - 0.61, 0.26))
    pb = fr.cam.p1((0, HY - 0.61 - 0.35 * sw, 0.26))

    def ui(img, fx):
        d_ = ImageDraw.Draw(img)
        k = seg(u, 0.2, 0.4)
        d_.line([(pa[0] + 70, pa[1]), (pb[0] + 70, pb[1])], fill=M.scale_c(AMARILLO, k), width=4)
        texto(img, fx, pa[0] + 200, (pa[1] + pb[1]) / 2, 'HUECO', 44, col=AMARILLO, k=k, f='sansx')
        kicker(img, 'FLOJA', 150, seg(u, 0.0, 0.3), col=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. en el golpe el casco se va antes que tu cabeza: la horma frena de golpe y el casco sale volando (cámara lenta)
def s_vuela(t, fi, u, d):
    ug = Wp(15, 'golpe') - 0.05
    fr = Frame(camara(u, [K(-0.3, 3.6, 70, 8, ty=HY), K(0.3, 3.2, 90, 6, ty=HY), K(d, 3.4, 96, 6, ty=HY + 0.2)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.4)
    zh = 0.8 - 0.8 * seg(u, -0.3, ug)
    k = P.eout4(seg(u, ug, ug + 1.4))
    ms = horma_m(z=zh) + P.tfk(correa(floja=0.9), t=(0, HY, zh))
    ms += casco_en('bueno', z=zh - 1.0 * k, y=HY + 0.6 * k, rx=-80 * k, partes=('cascara', 'eps', 'forro'))
    ms.append(named(M3.box(0.2, 1.6, 1.4, (90, 94, 102), shadow=0, gloss=0.4).tf(t=(0, 0.0, -0.75)), 'muro', rim=0.6))
    draw_objects(fr, ms)
    for j in range(5):
        if k > 0.05:
            line3(fr, [(0, HY + 0.3 + 0.1 * j, zh - 0.3 - 0.6 * k), (0, HY + 0.3 + 0.1 * j, zh + 0.2 - 0.6 * k)], col=AZULC, w=2,
                  a=0.6 * (1 - k), glow=0.8)

    def ui(img, fx):
        kicker(img, 'CÁMARA LENTA · RECREACIÓN', 150, seg(u, 0.0, 0.3), col=AZULC)
        pill(img, fx, 540, 1300, 'EL CASCO SE VA PRIMERO', eout(seg(u, ug + 0.3, ug + 0.55)), size=32, border=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ug, 0.35), amp=24)


# 16. y si ya se golpeó, cámbialo: el casco cae al piso y rebota
def s_golpeo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.8, -30, 22, ty=0.4), K(0.3, 2.3, 0, 16, ty=0.4), K(d, 2.25, 4, 16, ty=0.4)], cy=0.56))
    space(fr, t, floor='lines', floor_a=1.0, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.1, 0.55, 'cae')
    draw_objects(fr, casco_en('bueno', y=0.52 + max(0.0, -e['dy']), rz=25 * math.sin(max(0, u) * 9) * math.exp(-max(0, u) * 3),
                              partes=('cascara', 'eps', 'forro')))
    pc = fr.cam.p1((0.0, 0.9, 0.3))

    def ui(img, fx):
        kicker(img, 'YA SE GOLPEÓ', 150, seg(u, -0.1, 0.2), col=AMARILLO)
        pill(img, fx, pc[0], pc[1] - 230, 'CÁMBIALO', eout(seg(u, 0.6, 0.85)), size=38, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.3), amp=20)


# 17. el unicel aplastado no regresa, aunque se vea bien: corte con la abolladura + zoom digital x1.0 → x1.8
def s_aplastado(t, fi, u, d):
    ub = Wp(17, 'bien') - 0.15
    fr = Frame(camara(u, [K(-0.3, 1.9, 70, 6, ty=HY + 0.15, tz=0.2), K(0.3, 1.5, 90, 4, ty=HY + 0.2, tz=0.25),
                          K(d, 1.45, 92, 4, ty=HY + 0.2, tz=0.25)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8, beam=0.4)
    draw_objects(fr, casco_en('bueno', u0=math.pi / 2, u1=3 * math.pi / 2, partes=('cascara', 'eps', 'forro')))
    corte(fr, 'bueno', aplastado=seg(u, 0.1, 0.5))
    img = finish(fr, fi)
    z = 1.0 if u < 0.7 else (1.4 if u < 1.4 else 1.8)
    img = M.scale_about(img, z, 0.62, 0.42)
    im = Image.fromarray(img)
    fx = Image.new('RGB', im.size, (0, 0, 0))
    rec_frame(im, t, k=1.0, zoom_label=f'x{z:.1f}')
    pill(im, fx, 540, 1250, 'POR DENTRO: APLASTADO', eout(seg(u, 0.4, 0.65)), size=30, border=RED)
    pill(im, fx, 540, 1340, 'POR FUERA: SE VE BIEN', eout(seg(u, ub, ub + 0.25)), size=30, border=VERDE)
    a = np.asarray(im, np.float32) + np.asarray(fx, np.float32) * 0.5
    return a.clip(0, 255).astype(np.uint8)


# 18. bien abrochado, según la OMS: la correa se ajusta a la barbilla y la hebilla hace clic (palomita verde)
def s_abrochado(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.4, -50, 8, ty=HY - 0.2), K(0.3, 2.0, -20, 4, ty=HY - 0.25), K(d, 1.95, -16, 4, ty=HY - 0.25)],
                      cy=0.52))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.55)
    cl = P.eout4(seg(u, 0.2, 0.5))
    ms = casco_en('bueno', partes=('cascara', 'eps', 'forro')) + horma_m() + P.tfk(correa(floja=0.5 * (1 - cl), abierta=1 - cl),
                                                                                  t=(0, HY, 0))
    draw_objects(fr, ms)
    pb = fr.cam.p1((0, HY - 0.61, 0.27))

    def ui(img, fx):
        kicker(img, 'SEGÚN LA OMS', 150, seg(u, 0.3, 0.6), col=AZULC)
        pill(img, fx, pb[0], pb[1] + 200, 'ABROCHADO Y AJUSTADO', eout(seg(u, 0.5, 0.75)), size=30, border=VERDE)
        texto(img, fx, pb[0] + 200, pb[1] - 60, '✓', 90, col=VERDE, k=seg(u, 0.5, 0.65), f='sansx', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.5, 0.25), amp=12)


# 19. baja hasta 74 % las lesiones del cerebro: la cifra golpea («74 %» de cristal) y la dona baja
def s_74(t, fi, u, d):
    u7 = Wp(19, 'setenta') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.0, 30, 10, ty=HY), K(0.3, 2.6, 10, 8, ty=HY), K(d, 2.55, 6, 8, ty=HY)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, '74 %', u, t0=u7 - 0.05, cy=0.33, entrada='golpe')
    draw_objects(fr, casco_en('bueno', ry=12 * t) + horma_m())

    def ui(img, fx):
        kicker(img, 'LESIONES DEL CEREBRO', 1360, seg(u, u7, u7 + 0.3), col=AZULC)
        texto(img, fx, 540, 1460, 'HASTA −74 %', 64, col=VERDE, k=seg(u, u7 + 0.3, u7 + 0.5), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u7 + 0.2, 0.3), amp=20)


# 20. mándaselo a tu compa que anda en moto con el casco colgando: celular con el chat y el casco colgando de la correa
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, -30, 8, tx=0.1, ty=0.95), K(0.3, 3.0, -6, 6, tx=0.1, ty=0.95),
                          K(d, 2.95, -2, 6, tx=0.1, ty=0.95)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    ms = P.celular(scr_chat(seg(u, 0.6, 0.8)), ry=-12, off=(0.65, max(0.0, -e['dy']), 0))
    sw = 12 * math.sin(t * 2.4)
    ms += casco_en('bueno', x=-0.4, y=0.85, rz=sw, s=0.7, partes=('cascara', 'eps', 'forro'))
    draw_objects(fr, ms)
    line3(fr, [(-0.4 + 0.3 * math.sin(math.radians(sw)), 0.85 + 0.0, 0.05), (-0.4, 1.65, 0.05)], col=(90, 90, 96), w=4, a=1.0,
          glow=0.1)

    def ui(img, fx):
        kicker(img, 'MÁNDASELO', 150, seg(u, 0.0, 0.3), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.25), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-3.3, 'whoosh_suave', 0.4), (-0.3, 'riser', 0.5), (0.0, 'whoosh', 0.8), (U_CLIC, 'click', 1.0),
                     (U_CLIC, 'sub', 0.9), (U_CLIC + 0.15, 'tick', 0.6), (1.6, 'bass', 0.8)]),
           dict(desde=1, fn=s_mitad, tr='golpe', sfx=[(0.4, 'tick', 0.5), (1.6, 'shimmer', 0.5), (2.0, 'chime_a', 0.5)]),
           dict(desde=2, fn=s_moto, tr='deslizar', sfx=[(0.0, 'whoosh', 0.6), (0.2, 'bass', 0.7)]),
           dict(desde=3, fn=s_unicel, tr='zoom', c=(0.5, 0.5), sfx=[(0.5, 'whoosh_suave', 0.5), (1.6, 'shimmer', 0.6), (1.8, 'slap', 0.6)]),
           dict(desde=4, fn=s_mide, tr='rebanadas', sfx=[(0.3, 'click', 0.6), (0.5, 'scribble', 0.5), (0.7, 'tick2', 0.5)]),
           dict(desde=5, fn=s_aplasta, tr='push', c=(0.5, 0.55), sfx=[(0.25, 'whoosh', 0.5), (0.6, 'thud', 0.9), (0.62, 'sub', 0.6)]),
           dict(desde=6, fn=s_frena, tr='cubo', sfx=[(0.1, 'whoosh', 0.6), (0.45, 'sub', 1.0), (0.45, 'bass', 0.8),
                                                     (2.0, 'chime_a', 0.4), (2.3, 'chime_b', 0.4)]),
           dict(desde=7, fn=s_suave, tr='deslizar_abajo', sfx=[(0.2, 'tick', 0.5), (0.7, 'chime_c', 0.5)]),
           dict(desde=8, fn=s_adorno, tr='glitch', sfx=[(0.1, 'thud', 0.7), (0.5, 'digital', 0.4), (2.5, 'tick2', 0.6)]),
           dict(desde=9, fn=s_bueno, tr='wipe', sfx=[(0.2, 'thud', 0.9), (0.9, 'tick2', 0.6), (0.6, 'chime_b', 0.5)]),
           dict(desde=10, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.25, 'sub', 1.0), (0.25, 'bass', 0.8)]),
           dict(desde=11, fn=s_correa, tr='iris', c=(0.5, 0.6), sfx=[(0.12, 'bass', 0.9), (0.2, 'scribble', 0.6)]),
           dict(desde=12, fn=s_estudio, tr='mosaico', sfx=[(0.3, 'tick', 0.4), (0.6, 'tick', 0.4), (0.9, 'tick', 0.4)]
                + [(2.0 + 0.1 * j, 'tick2', 0.4) for j in range(7)]),
           dict(desde=13, fn=s_abrochados, tr='giro', sfx=[(0.3, 'click', 0.8), (0.6, 'bass', 0.6)]),
           dict(desde=14, fn=s_floja, tr='whip', sfx=[(0.2, 'whoosh_suave', 0.4), (0.3, 'scribble', 0.4)]),
           dict(desde=15, fn=s_vuela, tr='cristal', palabra='VUELA', sfx=[(0.6, 'sub', 1.0), (0.65, 'whoosh', 0.8), (1.0, 'thud', 0.5)]),
           dict(desde=16, fn=s_golpeo, tr='flash', sfx=[(0.3, 'thud', 1.0), (0.3, 'bass', 0.7), (0.7, 'slap', 0.6)]),
           dict(desde=17, fn=s_aplastado, tr='cubo_izq', sfx=[(0.7, 'click', 0.8), (1.4, 'click', 0.8), (0.3, 'scribble', 0.4)]),
           dict(desde=18, fn=s_abrochado, tr='zoom', c=(0.5, 0.62), sfx=[(0.5, 'click', 1.0), (0.55, 'chime_c', 0.5)]),
           dict(desde=19, fn=s_74, tr='golpe', sfx=[(0.6, 'sub', 0.9), (0.9, 'shimmer', 0.5)]),
           dict(desde=20, fn=s_compa, tr='remolino', sfx=[(0.1, 'bass', 0.7), (0.7, 'click', 0.6), (0.8, 'chime_b', 0.4)]),
           dict(desde=21, loop=True, tr='whip_izq')]

if __name__ == '__main__':
    montaje.cli(globals())
