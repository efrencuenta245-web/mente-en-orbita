"""Reel diario vie 20-nov-2026 10:00 — «Tu control no vibra… gira.» (la vibración clásica sale de un motorcito que
gira un peso chueco; trae dos: uno pesado para los golpes y uno ligero para el zumbido; el de PS5 usa actuadores
lineales con bobina e imán, como una bocina; segundo gancho: lo que descompone el control es el stick: unos contactos de
metal tallan una pista que se gasta → drift; los sticks de efecto Hall no se tocan).
Comunidad: gamers (semana de GTA 6). Inicio tipo 9 (giro 360° con destellos): el control da una vuelta completa con
3 cortes de destello, aterriza de frente, se vuelve de cristal y se ve el peso chueco girando («GIRA» de cristal detrás).
El final («y la próxima vez que tiemble en tus manos, acuérdate…») muestra el control temblando = la escena 0 en
pre-roll (loop). Voz: plan B (Chatterbox) porque ElevenLabs pidió volver a iniciar sesión. Fuentes:
guiones/2026-11-20_control.txt. El control, los motores, la bobina y el stick son ESQUEMAS sin marca.
"""
import math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import texto, esquema, golpe_k, sacudir, K, camara, tubo

M3 = M.M3
TEMA = 'control'
TXT = ['Tu control no vibra… gira.',
       'Adentro trae un motorcito con un peso chueco.',
       'Si el peso estuviera centrado,',
       'giraría liso y no sentirías nada.',
       'Chueco, en cada vuelta',
       'jala el control de un lado al otro.',
       'Por eso trae dos: uno pesado para los golpes',
       'y uno ligero para el zumbido.',
       'El de PlayStation 5 ya no gira:',
       'trae bobinas con imán, como una bocina.',
       'Mueven una pesita de ida y vuelta, y sientes hasta la lluvia.',
       'Pero lo que de verdad descompone tu control…',
       'es el palito.',
       'Debajo de cada stick, unos contactos de metal tallan una pista.',
       'Con el uso y el polvo se gasta,',
       'y el control cree que lo mueves aunque no lo toques.',
       'Eso es el drift: tu personaje camina solo…',
       'y no es culpa del juego.',
       'Los sticks con imanes, de efecto Hall,',
       'no se tocan y casi no se gastan.',
       'Mándaselo a tu compa que le echa la culpa al control.',
       'Y la próxima vez que tiemble en tus manos, acuérdate…']
VOZ = ['Tu control no vibra... gira.',
       'Adentro trae un motorcito con un peso chueco.',
       'Si el peso estuviera centrado,',
       'giraría liso y no sentirías nada.',
       'Chueco, en cada vuelta',
       'jala el control de un lado al otro.',
       'Por eso trae dos: uno pesado para los golpes',
       'y uno ligero para el zumbido.',
       'El de PlayStation cinco ya no gira:',
       'trae bobinas con imán, como una bocina.',
       'Mueven una pesita de ida y vuelta, y sientes hasta la lluvia.',
       'Pero lo que de verdad descompone tu control...',
       'es el palito.',
       'Debajo de cada stick, unos contactos de metal tallan una pista.',
       'Con el uso y el polvo se gasta,',
       'y el control cree que lo mueves aunque no lo toques.',
       'Eso es el drift: tu personaje camina solo...',
       'y no es culpa del juego.',
       'Los sticks con imanes, de efecto Hall,',
       'no se tocan y casi no se gastan.',
       'Mándaselo a tu compa que le echa la culpa al control.',
       'Y la próxima vez que tiemble en tus manos, acuérdate...']
assert len(VOZ) == len(TXT)

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
VERDE = (40, 205, 110)
CUERPO = (44, 46, 53)
CUERPO_B = (226, 228, 232)     # control blanco (el de PS5, sin marca)
NEGRO = (24, 24, 28)
COBRE = (214, 128, 64)
ACERO = (178, 180, 188)
LATON = (222, 186, 96)
IMAN_R, IMAN_A = (226, 72, 60), (70, 120, 235)
PISTA = (92, 60, 40)
CY = 1.0          # altura del centro del control
TH = 0.26         # grosor del control


def Wp(i, palabra, n=0):
    """u (desde el inicio de la frase i) de la palabra que empieza con `palabra`: reparto por letras, igual que el
    words.json del plan B."""
    T = montaje.CTX.get('T')
    if not T:
        return 0.0
    a, b = T[i]
    ws = [w for w in VOZ[i].split()]
    nn = [montaje._norm(w) for w in ws]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(nn) if w.startswith(p)]
    if not hits:
        return 0.0
    k = hits[min(n, len(hits) - 1)]
    wt = [len(w) + 1 + (5 if w.endswith('...') else 3 if w.endswith(':') else 2 if w[-1] in ',.' else 0) for w in ws]
    return (b - a) * sum(wt[:k]) / sum(wt)


# ------------------------------------------------------------------ objetos
def _chaikin(pts, n=3):
    for _ in range(n):
        q = []
        for i in range(len(pts)):
            a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
            q += [tuple(0.75 * a + 0.25 * b), tuple(0.25 * a + 0.75 * b)]
        pts = q
    return pts


_DER = [(0.0, 0.36), (0.5, 0.39), (0.78, 0.34), (0.95, 0.18), (1.03, -0.12), (1.01, -0.46), (0.93, -0.74), (0.79, -0.83),
        (0.63, -0.75), (0.5, -0.45), (0.36, -0.3), (0.0, -0.27)]
SIL = _chaikin([(x, y) for x, y in _DER] + [(-x, y) for x, y in _DER[::-1][1:-1]], 3)


def cyl_z(r, h, col, x, y, z0, n=24, r2=None, gloss=0.4, name='cuerpo', rim=0.6, glow=None):
    """Cilindro con el eje hacia la cámara (+z), de z0 a z0 + h."""
    m = named(M3.cyl(r, h, col, n=n, shadow=0, gloss=gloss, r2=r2).tf(rx=90).tf(t=(x, y, z0)), name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    return m


def placa_xy(pts, th, col, z0=0.0, name='cuerpo', gloss=0.35, rim=0.6, glow=None):
    """Polígono (x, y) extruido hacia la cámara (+z) desde z0."""
    m = M3.extrude([(x, -y) for x, y in pts], th, col, shadow=0, gloss=gloss).tf(rx=90).tf(t=(0, 0, z0))
    m = named(m, name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    return m


def peso_m(ang, r=0.085, th=0.05, x=0.0, y=0.0, z=0.0, centrado=False, col=LATON, s=1.0):
    """El peso: media luna (chueco) o disco completo (centrado), girado `ang` rad sobre el eje z."""
    r *= s
    if centrado:
        pts = [(r * 0.8 * math.cos(a), r * 0.8 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
    else:
        pts = ([(r * math.cos(a), -r * math.sin(a)) for a in np.linspace(0, math.pi, 16)] +
               [(-r * 0.22 * math.cos(a), r * 0.22 * math.sin(a)) for a in np.linspace(0, math.pi, 8)])
    m = placa_xy(pts, th * s, col, z0=0, name='peso', gloss=0.85, rim=0.9)
    return m.tf(rz=math.degrees(ang)).tf(t=(x, y, z))


def motor_m(ang, x=0.0, y=0.0, z=0.0, s=1.0, pesado=True, centrado=False):
    """Motorcito de vibración (ERM) con el eje hacia la cámara: lata, eje y peso."""
    r = 0.075 if pesado else 0.055
    L = 0.18 if pesado else 0.14
    ms = [cyl_z(r * s, L * s, ACERO, x, y, z - L * s, n=26, gloss=0.8, name='motor', rim=0.85),
          cyl_z(r * 1.02 * s, 0.025 * s, (60, 62, 70), x, y, z - L * s - 0.02 * s, n=26, gloss=0.4, name='motor'),
          cyl_z(0.012 * s, 0.05 * s, (220, 222, 228), x, y, z, n=8, gloss=0.9, name='motor')]
    ms.append(peso_m(ang, r=(0.085 if pesado else 0.055), th=(0.045 if pesado else 0.03), x=x, y=y, z=z + 0.02 * s,
                     centrado=centrado, s=s))
    return ms


def control_m(blanco=False, xs=0.0, ys=0.0, ry=0.0, rx=0.0, rz=0.0, s=1.0, stick=(0.0, 0.0), roja=0.0):
    """Control genérico (sin marca), de frente a +z, centrado en (0, CY, 0) antes de moverlo."""
    col = CUERPO_B if blanco else CUERPO
    col2 = (30, 32, 38) if blanco else (34, 35, 41)
    ms = [placa_xy(SIL, TH, col, z0=-TH / 2, gloss=0.4, rim=0.7)]
    for sx in (-1, 1):                                      # gatillos arriba
        ms.append(named(M3.rbox(0.36, 0.08, 0.16, 0.04, col2, n=3, shadow=0, gloss=0.5).tf(t=(sx * 0.58, 0.33, -0.02)),
                        'cuerpo', rim=0.7))
    for sx in (-1, 1):                                      # sticks: base, eje y tapa
        sxp, syp = sx * 0.3, -0.14
        tx, ty = (stick if sx < 0 else (0, 0))
        ms.append(cyl_z(0.13, 0.02, col2, sxp, syp, TH / 2, n=26, name='stick', gloss=0.3))
        ms.append(cyl_z(0.035, 0.07, (60, 60, 66), sxp + tx * 0.04, syp + ty * 0.04, TH / 2, n=10, name='stick'))
        cap = M.mixc((52, 54, 60), RED, roja)
        ms.append(cyl_z(0.1, 0.045, cap, sxp + tx * 0.07, syp + ty * 0.07, TH / 2 + 0.07, n=26, r2=0.11, name='stick',
                        gloss=0.3, glow=M.scale_c(RED, 0.6 * roja) if roja > 0.02 else None))
    for dx, dy in ((0, 0.075), (0, -0.075), (0.075, 0), (-0.075, 0)):   # cruceta
        ms.append(named(M3.box(0.06 if dx else 0.055, 0.055 if dx else 0.06, 0.03, col2, shadow=0, gloss=0.4, base=False)
                        .tf(t=(-0.55 + dx, 0.12 + dy, TH / 2 + 0.01)), 'cuerpo', rim=0.6))
    for (dx, dy), c in zip(((0, 0.085), (0.085, 0), (0, -0.085), (-0.085, 0)),
                           ((230, 200, 90), (220, 80, 70), (90, 200, 120), (90, 140, 230))):
        ms.append(cyl_z(0.032, 0.025, M.mixc(col2, c, 0.55), 0.55 + dx, 0.12 + dy, TH / 2, n=14, name='boton', gloss=0.6))
    out = P.tfk(ms, t=(0, 0, 0))
    out = P.tfk(out, s=s, rx=rx, ry=ry, rz=rz)
    return P.tfk(out, t=(xs, CY + ys, 0))


def motores_en(ang_p, ang_l, xs=0.0, ys=0.0, ry=0.0, rz=0.0, s=1.0, cual=(1, 1)):
    """Los dos motores dentro de los mangos (pesado a la izquierda, ligero a la derecha), en el mismo marco del control."""
    ms = []
    if cual[0]:
        ms += motor_m(ang_p, -0.74, -0.5, 0.06, pesado=True)
    if cual[1]:
        ms += motor_m(ang_l, 0.74, -0.5, 0.06, pesado=False)
    return P.tfk(P.tfk(ms, s=s, ry=ry, rz=rz), t=(xs, CY + ys, 0))


def vibra(t, amp, w=40.0, w2=None):
    """Desplazamiento (dx, dy) del control cuando lo jalan los pesos."""
    w2 = w2 or w * 1.7
    return (amp * (0.7 * math.cos(t * w) + 0.3 * math.cos(t * w2)), amp * (0.7 * math.sin(t * w) + 0.3 * math.sin(t * w2 + 1)))


def estela(fr, c, r, ang, k=1.0, col=AMARILLO, n=3, largo=2.2, w=3.0, eje='z'):
    """Arcos que brillan detrás del peso que gira (marcan la vuelta)."""
    if k <= 0.01:
        return
    for j in range(n):
        rr = r * (1.15 + 0.18 * j)
        q = np.linspace(ang - largo, ang, 24)
        pts = [(c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), c[2]) for a in q]
        line3(fr, pts, col=col, w=w - 0.6 * j, a=k * (0.9 - 0.25 * j), glow=0.9)


def onda(img, fx, x0, y0, w, h, fn, k=1.0, col=CYAN, label=None, n=180):
    """Gráfica 2D de una señal (fn(s) con s de 0 a 1 → −1..1) que se dibuja de izquierda a derecha."""
    if k <= 0.01:
        return
    m = max(2, int(n * clamp(k)))
    pts = [(x0 + w * i / n, y0 - h * fn(i / n)) for i in range(m)]
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.line([(x0, y0), (x0 + w, y0)], fill=(60, 64, 72), width=2)
    d.line(pts, fill=col, width=4, joint='curve')
    df.line(pts, fill=M.scale_c(col, 0.7), width=9, joint='curve')
    if label:
        d.text((x0, y0 - h - 46), label, font=M.font('mono', 24), fill=M.scale_c(col, 0.9))


def silueta(fr, xs, ys, z=TH / 2 + 0.002, col=WHITE, a=0.5, w=2.0, s=1.0):
    pts = [(xs + s * x, CY + ys + s * y, z) for x, y in SIL] + [(xs + s * SIL[0][0], CY + ys + s * SIL[0][1], z)]
    line3(fr, pts, col=col, w=w, a=a, glow=0.8)


def lra_m(off=0.0, x=0.0, y=0.0, z=0.0, s=1.0, ry=0.0, caja=True):
    """Actuador lineal (LRA) del control de PS5: caja, bobina de cobre, imán y la pesita que va y viene en x."""
    ms = []
    if caja:
        ms.append(named(M3.box(0.62, 0.24, 0.24, (70, 74, 84), shadow=0, gloss=0.6, base=False), 'caja', rim=0.8))
    for j in range(5):                                       # bobina: aros de cobre (eje en x)
        ms.append(named(M3.torus(0.075, 0.018, COBRE, nu=24, nv=6, gloss=0.8).tf(rz=90).tf(t=(-0.08 + 0.04 * j, 0, 0)),
                        'bobina', rim=0.8, gloss=0.8))
    ms.append(named(M3.cyl(0.045, 0.22, IMAN_R, n=18, shadow=0, gloss=0.6).tf(rz=-90).tf(t=(-0.11, 0, 0)), 'iman', rim=0.8))
    ms.append(named(M3.cyl(0.046, 0.06, IMAN_A, n=18, shadow=0, gloss=0.6).tf(rz=-90).tf(t=(0.11, 0, 0)), 'iman', rim=0.8))
    ms.append(named(M3.box(0.12, 0.17, 0.17, (196, 198, 206), shadow=0, gloss=0.85, base=False).tf(t=(0.2 + off, 0, 0)),
                    'masa', rim=0.9, gloss=0.85))
    return P.tfk(P.tfk(ms, s=s, ry=ry), t=(x, y, z))


def resortes(fr, off, x, y, z, s=1.0, k=1.0, col=AZULC):
    """Resortes de la pesita (zigzag que brilla)."""
    if k <= 0.01:
        return
    a, b = 0.26 + off, 0.31
    pts = [(x + s * (a + (b - a) * i / 10), y + s * (0.05 if i % 2 else -0.05), z) for i in range(11)]
    line3(fr, pts, col=col, w=2.2, a=k, glow=0.8)


def bocina_m(push=0.0, x=0.0, y=0.0, z=0.0, s=1.0):
    """Bocina: aro, cono (eje hacia la cámara), tapita y el imán atrás."""
    ms = [named(M3.torus(0.36, 0.035, (40, 40, 46), nu=36, nv=8, gloss=0.4).tf(rx=90).tf(t=(0, 0, 0.12)), 'bocina', rim=0.7),
          cyl_z(0.34, 0.16, (34, 34, 38), 0, 0, -0.04 + 0.04 * push, n=36, r2=0.1, gloss=0.25, name='cono', rim=0.6),
          cyl_z(0.1, 0.05, (60, 60, 66), 0, 0, 0.1 + 0.04 * push, n=24, r2=0.06, gloss=0.6, name='cono'),
          cyl_z(0.17, 0.12, (150, 152, 160), 0, 0, -0.2, n=28, gloss=0.8, name='iman', rim=0.8)]
    return P.tfk(P.tfk(ms, s=s), t=(x, y, z))


def modulo_stick(tilt=(0.0, 0.0), abre=0.0, x=0.0, y=0.0, z=0.0, s=1.0, hall=False):
    """Módulo del stick por dentro (de frente): base negra, eje que se inclina, y (si abre) la tapa que sube."""
    tx, ty = tilt
    ms = [named(M3.box(0.9, 0.12, 0.9, (30, 30, 34), shadow=0, gloss=0.4), 'base', rim=0.6)]
    ms.append(named(M3.cyl(0.06, 0.62, (70, 70, 78), n=14, shadow=0, gloss=0.6).tf(rx=-ty * 18, rz=-tx * 18).tf(t=(0, 0.1, 0)),
                    'eje', rim=0.7))
    cap = named(M3.cyl(0.26, 0.1, (54, 56, 62), n=28, shadow=0, gloss=0.3, r2=0.28)
                .tf(t=(0, 0.66 + 0.9 * P.eout4(abre), 0)), 'tapa', rim=0.7)
    ms.append(P.tfk([cap], rx=-ty * 18, rz=-tx * 18)[0])
    if hall:
        ms.append(named(M3.cyl(0.07, 0.06, IMAN_R, n=18, shadow=0, gloss=0.6).tf(t=(0, 0.14, 0)), 'iman', rim=0.8))
        ms.append(named(M3.box(0.22, 0.05, 0.22, (20, 20, 22), shadow=0, gloss=0.8).tf(t=(0, 0.12 - 0.12, 0)), 'chip', rim=0.6))
    return P.tfk(P.tfk(ms, s=s), t=(x, y, z))


def pista(fr, cx, cy, cz, r=0.32, k=1.0, gasto=0.0, s=1.0, col=PISTA, ang0=-0.5, ang1=2.2, t=0.0, eje='x'):
    """Pista resistiva (arco que brilla tenue) en el plano vertical del módulo; gasto = huecos claros."""
    if k <= 0.01:
        return
    q = np.linspace(ang0, ang1, 46)
    for j in range(len(q) - 1):
        hueco = gasto > 0.02 and math.sin(q[j] * 23 + 1.3) > 1 - 1.6 * gasto
        c = M.mixc(col, (210, 200, 180), 0.8) if hueco else col
        p0 = (cx + s * r * math.cos(q[j]), cy, cz + s * r * math.sin(q[j]))
        p1 = (cx + s * r * math.cos(q[j + 1]), cy, cz + s * r * math.sin(q[j + 1]))
        line3(fr, [p0, p1], col=c, w=9 * s, a=k, glow=0.25 if not hueco else 0.8)


def chispas(fr, t, p, k=1.0, n=10, col=AMARILLO, seed=1, r=0.12):
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    for j in range(n):
        ph = (t * 2.2 + rng.rand()) % 1.0
        a = rng.rand() * 6.28
        q = (p[0] + r * ph * math.cos(a), p[1] + 0.6 * r * ph + 0.05 * rng.rand(), p[2] + r * ph * math.sin(a))
        dot3(fr, q, r=2.2 + 1.5 * (1 - ph), col=col, a=k * (1 - ph), glow=1.2)


def polvo(fr, t, c, k=1.0, n=40, seed=4, R=0.5):
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    for j in range(n):
        a, rr, h = rng.rand() * 6.28, R * math.sqrt(rng.rand()), rng.rand()
        y = c[1] + 0.35 * h + 0.03 * math.sin(t * 2 + j)
        dot3(fr, (c[0] + rr * math.cos(a), y, c[2] + rr * math.sin(a)), r=1.6 + 1.6 * rng.rand(), col=(200, 186, 160),
             a=k * (0.35 + 0.4 * rng.rand()), glow=0.3)


def scr_chat(k=1.0):
    def dib(d, im):
        f = M.font
        d.text((34, 90), 'Tu compa', font=f('sanss', 30), fill=(235, 235, 240))
        d.line([(0, 140), (420, 140)], fill=(40, 42, 48), width=2)
        d.rounded_rectangle((30, 200, 330, 300), radius=26, fill=(44, 46, 54))
        d.text((54, 222), 'Este juego está', font=f('sanss', 26), fill=(235, 235, 240))
        d.text((54, 256), 'bien bugueado', font=f('sanss', 26), fill=(235, 235, 240))
        if k > 0.5:
            d.rounded_rectangle((110, 340, 392, 470), radius=26, fill=(36, 120, 80))
            d.text((134, 362), 'No es el juego:', font=f('sanss', 26), fill=(245, 245, 247))
            d.text((134, 396), 'es tu stick.', font=f('sanss', 26), fill=(245, 245, 247))
            d.text((134, 430), 'Mira este video', font=f('sanss', 22), fill=(200, 230, 210))
    return P.pantalla(dib)


# ================================================================== escenas
# 0. gancho (inicio 9: giro 360° con destellos). Pre-roll (lo que se ve al final, loop): el control tiembla de frente
#    con «GIRA» de cristal detrás. En u = 0 da una vuelta completa en 0.9 s con 3 cortes de destello y aterriza de
#    frente; se vuelve de cristal y aparecen los pesos chuecos girando.
U_GIRO, D_GIRO = 0.0, 0.9


def s_gancho(t, fi, u, d):
    ug = Wp(0, 'gira') - 0.05
    k_giro = P.eout4(seg(u, U_GIRO, U_GIRO + D_GIRO))
    ry = 360 * k_giro
    fr = Frame(camara(u, [K(-4.0, 4.4, 0, 6, ty=CY), K(-0.4, 3.6, 0, 4, ty=CY), K(U_GIRO + D_GIRO, 3.1, -14, 6, ty=CY),
                          K(ug, 2.7, -8, 4, ty=CY - 0.05), K(5.0, 2.6, -4, 4, ty=CY - 0.05)], cy=0.53))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'GIRA', u, t0=-3.3, cy=0.44, entrada='golpe')
    amp = 0.03 * (1 if u < U_GIRO else 0.0) + 0.012 * seg(u, ug, ug + 0.2)
    dx, dy = vibra(t, amp)
    xr = seg(u, U_GIRO + D_GIRO - 0.05, U_GIRO + D_GIRO + 0.1)
    ang = t * 9.0
    ms = control_m(xs=dx, ys=dy, ry=ry) + motores_en(ang, ang * 1.6, xs=dx, ys=dy, ry=ry)
    draw_objects(fr, ms, xray=xr, keep=('motor', 'peso'))
    if xr > 0.5:
        for xm, rm in ((-0.74, 0.085), (0.74, 0.055)):
            estela(fr, (xm + dx, CY - 0.5 + dy, 0.12), rm, ang * (1.6 if xm > 0 else 1.0), k=xr)
    if u < U_GIRO:
        silueta(fr, dx * 3, dy * 3, a=0.25)
        silueta(fr, -dx * 3, -dy * 3, a=0.18)
    fl = 0.0
    for q in (0.22, 0.45, 0.68):                              # 3 cortes de destello en el giro
        ua = U_GIRO + D_GIRO * q
        if ua <= u < ua + 0.07:
            fl = 0.75 * (1 - (u - ua) / 0.07)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Tu control no vibra…', 'sans'), ('gira.', 'serif')], 185, seg(u, ug - 0.1, ug + 0.05), size=78)
        kicker(img, 'MOTOR DE VIBRACIÓN · RAYOS X', 1300, seg(u, U_GIRO + D_GIRO, U_GIRO + D_GIRO + 0.25), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=fl), t, max(golpe_k(u, U_GIRO + D_GIRO, 0.3), golpe_k(u, ug + 0.05, 0.3),
                                                    0.25 if u < U_GIRO else 0.0), amp=22)


# 1. adentro trae un motorcito con un peso chueco: la cámara entra por el mango (rayos X) hasta el motor pesado
def s_motor(t, fi, u, d):
    up = Wp(1, 'peso') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.4, -8, 4, tx=-0.4, ty=CY - 0.3), K(0.35, 1.25, -24, 8, tx=-0.74, ty=CY - 0.5),
                          K(up, 0.95, -8, 4, tx=-0.74, ty=CY - 0.5), K(d, 0.92, -4, 4, tx=-0.74, ty=CY - 0.5)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.9, beam=0.3)
    ang = t * 5.0
    draw_objects(fr, control_m() + motores_en(ang, ang * 1.4), xray=1.0, keep=('motor', 'peso'))
    c = (-0.74, CY - 0.5, 0.11)
    estela(fr, c, 0.085, ang, k=seg(u, 0.2, 0.5))
    pc = fr.cam.p1(c)

    def ui(img, fx):
        kicker(img, 'ADENTRO DEL MANGO', 150, seg(u, -0.1, 0.2), col=AZULC)
        doodle_circle(img, fx, pc[0], pc[1], 190, 190, t, k=eout(seg(u, up, up + 0.3)), col=AMARILLO, seed=3)
        pill(img, fx, pc[0], pc[1] + 300, 'PESO CHUECO', eout(seg(u, up + 0.1, up + 0.35)), size=34, border=AMARILLO)
        texto(img, fx, 540, 1250, 'CÁMARA LENTA', 22, col=(150, 150, 160), k=seg(u, 0.4, 0.6), f='mono', glow=0)
        esquema(img, fx, seg(u, 0.2, 0.4), y=1450)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.1, 0.3), amp=14)


# 2. si el peso estuviera centrado: el motor solo, de lado, y el peso se transforma en un disco centrado
def s_centrado(t, fi, u, d):
    uc = Wp(2, 'centrado') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.2, 50, 16, ty=0.55), K(0.4, 1.5, 24, 10, ty=0.55), K(d, 1.45, 18, 10, ty=0.55)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'pop')
    ang = t * 6.0
    cen = u > uc
    draw_objects(fr, P.tfk(motor_m(ang, 0, 0.55, 0, s=2.6, centrado=cen), s=max(0.05, e['escala'])))
    if cen:
        estela(fr, (0, 0.55, 0.12), 0.18, ang, k=0.7, col=AZULC)
    pc = fr.cam.p1((0, 0.55, 0.15))

    def ui(img, fx):
        kicker(img, 'CASO A', 150, seg(u, -0.1, 0.2), col=AZULC)
        if cen:
            pill(img, fx, pc[0], pc[1] - 300, 'PESO CENTRADO', eout(seg(u, uc, uc + 0.25)), size=34, border=AZULC)
            doodle_circle(img, fx, pc[0], pc[1], 170, 170, t, k=eout(seg(u, uc + 0.1, uc + 0.4)), col=AZULC, seed=5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc, 0.25), amp=10)


# 3. giraría liso y no sentirías nada: el control quieto con el disco centrado girando y la señal plana «0»
def s_liso(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, 30, 10, ty=CY), K(0.5, 2.9, -8, 6, ty=CY), K(d, 2.85, -12, 6, ty=CY)], cy=0.47))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.4)
    ang = t * 12.0
    ms = control_m() + P.tfk(motor_m(ang, -0.74, -0.5, 0.06, centrado=True) + motor_m(ang, 0.74, -0.5, 0.06, pesado=False,
                                                                                         centrado=True), t=(0, CY, 0))
    draw_objects(fr, ms, xray=1.0, keep=('motor', 'peso'))

    def ui(img, fx):
        onda(img, fx, 180, 1300, 720, 90, lambda s: 0.02 * math.sin(s * 40), k=seg(u, 0.1, 0.9), col=AZULC, label='VIBRACIÓN')
        texto(img, fx, 960, 1300, '0', 90, col=AZULC, k=seg(u, 0.8, 1.0), f='sansx')
        kicker(img, 'GIRA PAREJO', 150, seg(u, 0.0, 0.3), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. chueco, en cada vuelta: la media luna gigante gira y una flecha la jala hacia afuera («CHUECO» de cristal)
def s_chueco(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 1.0, -40, 8, ty=0.6), K(0.3, 1.25, 10, 6, ty=0.6), K(d, 1.3, 16, 6, ty=0.6)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'CHUECO', u, t0=-0.1, cy=0.4, entrada='sube')
    ang = t * 4.0
    w = vibra(t, 0.02, w=4.0, w2=4.0)
    draw_objects(fr, motor_m(ang, w[0], 0.6 + w[1], 0, s=2.2))
    estela(fr, (w[0], 0.6 + w[1], 0.12), 0.19, ang - math.pi / 2, k=0.9, largo=2.6)
    pc = fr.cam.p1((w[0], 0.6 + w[1], 0.12))
    pe = fr.cam.p1((w[0] + 0.3 * math.cos(ang - math.pi / 2), 0.6 + w[1] + 0.3 * math.sin(ang - math.pi / 2), 0.12))

    def ui(img, fx):
        doodle_arrow(img, fx, pc[0], pc[1], pe[0], pe[1], t, k=eout(seg(u, 0.3, 0.6)), col=RED, seed=2)
        kicker(img, 'CASO B · PESO CHUECO', 150, seg(u, 0.0, 0.3), col=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. jala el control de un lado al otro: el control completo se sacude con estela y la señal se dispara
def s_jala(t, fi, u, d):
    uj = Wp(5, 'jala') - 0.05
    fr = Frame(camara(u, [K(-0.3, 3.2, 20, 8, ty=CY), K(0.25, 3.6, 0, 4, ty=CY), K(d, 3.5, -4, 4, ty=CY)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    amp = 0.07 * seg(u, uj, uj + 0.2)
    dx, dy = vibra(t, amp, w=34)
    ang = t * 34
    draw_objects(fr, control_m(xs=dx, ys=dy, rz=dx * 60) + motores_en(ang, ang * 1.5, xs=dx, ys=dy, rz=dx * 60), xray=0.0)
    if amp > 0.01:
        for j in (1, 2):
            silueta(fr, dx * (1 + j), dy * (1 + j), a=0.22 / j)
            silueta(fr, -dx * (1 + j), -dy * (1 + j), a=0.22 / j)

    def ui(img, fx):
        onda(img, fx, 160, 1310, 760, 110, lambda s: math.sin(s * 34) * (0.15 + 0.85 * seg(s, 0.15, 0.3)),
             k=seg(u, 0.0, 0.8), col=AMARILLO, label='VIBRACIÓN')
        texto(img, fx, 540, 300, '← →', 120, col=WHITE, k=seg(u, uj, uj + 0.15), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.6 * seg(u, uj, uj + 0.2), amp=26)


# 6. por eso trae dos: uno pesado para los golpes (rayos X, mango izquierdo, onda lenta y grande)
def s_pesado(t, fi, u, d):
    ug = Wp(6, 'golpes') - 0.1
    up = Wp(6, 'pesado') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.0, 0, 6, ty=CY - 0.2), K(0.4, 1.9, -22, 8, tx=-0.45, ty=CY - 0.4),
                          K(d, 1.85, -26, 8, tx=-0.45, ty=CY - 0.4)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.4)
    ang = t * 6.0
    hit = golpe_k(u, ug, 0.4)
    dx, dy = vibra(t, 0.04 * hit, w=14)
    draw_objects(fr, control_m(xs=dx, ys=dy) + motores_en(ang, 0, xs=dx, ys=dy, cual=(1, 0)), xray=1.0, keep=('motor', 'peso'))
    estela(fr, (-0.74 + dx, CY - 0.5 + dy, 0.12), 0.085, ang, k=0.9, col=NARANJA)
    pc = fr.cam.p1((-0.74, CY - 0.5, 0.12))

    def ui(img, fx):
        kicker(img, 'MOTOR 1 DE 2', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, min(820, pc[0] + 120), min(1180, pc[1] + 230), 'PESADO · GOLPES', eout(seg(u, up - 0.1, up + 0.15)), size=32,
             border=NARANJA)
        onda(img, fx, 180, 1330, 720, 100, lambda s: math.sin(s * 9) * math.exp(-2.5 * s), k=seg(u, up, up + 0.8), col=NARANJA,
             label='GRAVE')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, hit, amp=22)


# 7. y uno ligero para el zumbido (mango derecho, onda rápida y chica)
def s_ligero(t, fi, u, d):
    uz = Wp(7, 'zumbido') - 0.1
    fr = Frame(camara(u, [K(-0.3, 1.85, 26, 8, tx=0.45, ty=CY - 0.4), K(0.35, 1.5, 34, 10, tx=0.6, ty=CY - 0.45),
                          K(d, 1.45, 38, 10, tx=0.6, ty=CY - 0.45)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.4)
    ang = t * 16.0
    dx, dy = vibra(t, 0.006 * seg(u, uz, uz + 0.2), w=60)
    draw_objects(fr, control_m(xs=dx, ys=dy) + motores_en(0, ang, xs=dx, ys=dy, cual=(0, 1)), xray=1.0, keep=('motor', 'peso'))
    estela(fr, (0.74 + dx, CY - 0.5 + dy, 0.12), 0.055, ang, k=0.9, col=AZULC, largo=3.0)
    pc = fr.cam.p1((0.74, CY - 0.5, 0.12))

    def ui(img, fx):
        kicker(img, 'MOTOR 2 DE 2', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pc[0] - 40, pc[1] + 240, 'LIGERO · ZUMBIDO', eout(seg(u, uz - 0.1, uz + 0.15)), size=32, border=AZULC)
        onda(img, fx, 180, 1330, 720, 40, lambda s: math.sin(s * 70), k=seg(u, uz, uz + 0.5), col=AZULC, label='AGUDO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. el de PlayStation 5 ya no gira: llega el control blanco y, en rayos X, el peso que gira se tacha
def s_ps5(t, fi, u, d):
    un = Wp(8, 'gira') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, -30, 10, ty=CY), K(0.3, 3.0, 8, 6, ty=CY), K(d, 2.9, 12, 6, ty=CY)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.6)
    e = P.entrada(u, -0.2, 0.3, 'desliza')
    xs = e['dy']
    xr = seg(u, un - 0.3, un)
    ms = control_m(blanco=True, xs=xs)
    ms += P.tfk(lra_m(0.0, s=0.45) , t=(-0.74 + xs, CY - 0.5, 0.0)) + P.tfk(lra_m(0.0, s=0.45), t=(0.74 + xs, CY - 0.5, 0.0))
    draw_objects(fr, ms, xray=xr, keep=('bobina', 'iman', 'masa'))
    pc = fr.cam.p1((0, CY + 0.1, 0.2))

    def ui(img, fx):
        kicker(img, 'CONTROL DE PS5 · SIN MARCA', 150, seg(u, 0.0, 0.3), col=AZULC)
        P.pill_tachada(img, fx, pc[0], 330, 'PESO QUE GIRA', seg(u, un - 0.1, un + 0.1), seg(u, un + 0.3, un + 0.6), t, size=34)
        esquema(img, fx, seg(u, 0.3, 0.5), y=1450)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.3), amp=14)


# 9. trae bobinas con imán, como una bocina: el actuador abierto y una bocina que late al lado («BOCINA» de cristal)
def s_bocina(t, fi, u, d):
    ub = Wp(9, 'bocina') - 0.15
    fr = Frame(camara(u, [K(-0.3, 1.6, -20, 8, tx=-0.1, ty=0.6), K(0.4, 1.9, 6, 6, tx=0.15, ty=0.6),
                          K(ub, 2.4, 14, 6, tx=0.35, ty=0.6), K(d, 2.4, 18, 6, tx=0.35, ty=0.6)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'BOCINA', u, t0=ub, cy=0.36, entrada='zoom')
    off = 0.05 * math.sin(t * 9)
    ms = lra_m(off, x=-0.05, y=0.6, s=1.4, caja=False)
    eb = P.entrada(u, ub, 0.3, 'pop')
    if u > ub:
        ms += P.tfk(bocina_m(push=math.sin(t * 9), s=max(0.05, eb['escala'])), t=(0.95, 0.6, -0.2))
    draw_objects(fr, ms)
    resortes(fr, off, -0.05, 0.6, 0.0, s=1.4, k=0.9)
    for j in range(3):
        if u > ub:
            rr = 0.45 + 0.12 * j + 0.1 * ((t * 2) % 1)
            q = np.linspace(-0.7, 0.7, 20)
            line3(fr, [(0.95 + rr * math.cos(a) * 0.4, 0.6 + rr * math.sin(a), 0.4) for a in q], col=CYAN, w=2.4,
                  a=0.6 - 0.15 * j, glow=0.9)
    pb = fr.cam.p1((-0.15, 0.6, 0.2))

    def ui(img, fx):
        kicker(img, 'ACTUADOR LINEAL', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pb[0], pb[1] - 220, 'BOBINA', eout(seg(u, 0.2, 0.45)), size=30, border=NARANJA)
        pill(img, fx, pb[0] - 30, pb[1] + 200, 'IMÁN', eout(seg(u, 0.45, 0.7)), size=30, border=IMAN_R)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. mueven una pesita de ida y vuelta… y sientes hasta la lluvia (gotas que caen sobre el control blanco)
def s_lluvia(t, fi, u, d):
    ul = Wp(10, 'lluvia') - 0.15
    fr = Frame(camara(u, [K(-0.3, 1.4, 0, 6, tx=-0.6, ty=CY - 0.5), K(0.4, 1.2, -16, 8, tx=-0.7, ty=CY - 0.5),
                          K(ul, 3.3, 10, 18, ty=CY), K(d, 3.2, 14, 18, ty=CY)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    off = 0.06 * math.sin(t * 10)
    hits = 0.0
    lluvia = seg(u, ul - 0.2, ul + 0.2)
    ms = control_m(blanco=True) + P.tfk(lra_m(off, s=0.45), t=(-0.74, CY - 0.5, 0.0)) + P.tfk(lra_m(-off, s=0.45),
                                                                                              t=(0.74, CY - 0.5, 0.0))
    draw_objects(fr, ms, xray=1.0 - 0.6 * lluvia, keep=('bobina', 'iman', 'masa'))
    rng = np.random.RandomState(9)
    for j in range(36):
        x, z = (rng.rand() - 0.5) * 2.2, (rng.rand() - 0.5) * 0.6
        ph = (t * 1.4 + rng.rand()) % 1.0
        y = CY + 1.6 - 1.6 * ph
        if lluvia > 0.01:
            line3(fr, [(x, y, z + 0.2), (x, y + 0.12, z + 0.2)], col=AZULC, w=2.0, a=lluvia * 0.8, glow=0.8)
            if ph > 0.92:
                dot3(fr, (x, CY + 0.05, 0.2), r=6 * (ph - 0.9) * 10, col=CYAN, a=lluvia * 0.7, glow=1.0)
    pm = fr.cam.p1((-0.74 + 0.2 * 0.45 + off * 0.45, CY - 0.5, 0.1))

    def ui(img, fx):
        if u < ul:
            texto(img, fx, pm[0], pm[1] - 200, '◀  ▶', 70, col=AMARILLO, k=seg(u, 0.2, 0.4), f='sansx')
            pill(img, fx, pm[0], pm[1] + 230, 'PESITA', eout(seg(u, 0.3, 0.55)), size=30, border=AMARILLO)
        onda(img, fx, 180, 1330, 720, 70, lambda s: sum(math.exp(-((s - c) * 60) ** 2) for c in (0.1, 0.23, 0.31, 0.47, 0.6, 0.66,
                                                                                         0.79, 0.9)) * 0.9,
             k=seg(u, ul, ul + 0.7), col=CYAN, label='LLUVIA')
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. pero lo que de verdad descompone tu control… (segundo gancho): el control se pone oscuro y los sticks laten en rojo
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, 0, 30, ty=CY), K(0.3, 3.4, 18, 22, ty=CY), K(d, 3.3, 22, 22, ty=CY)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.6, beam=0.8)
    rojo = 0.5 + 0.5 * math.sin(t * 8) ** 2
    draw_objects(fr, control_m(roja=rojo * seg(u, 0.3, 0.6)))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, 0.0, 0.2), col=RED)
        P.titulo_golpe(img, fx, [('Lo que de verdad', 'sans'), ('lo descompone…', 'serif')], 230, seg(u, 0.1, 0.25), size=74)
        texto(img, fx, 540, 1250, '?', 160, col=RED, k=seg(u, 0.6, 0.8), f='sansx', glow=0.7)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.3), amp=24)


# 12. es el palito: crash zoom al stick izquierdo, garabato rojo («PALITO» de cristal detrás)
def s_palito(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.2, 20, 20, ty=CY), K(0.12, 1.2, 8, 30, tx=-0.3, ty=CY - 0.1),
                          K(d, 1.1, 4, 32, tx=-0.3, ty=CY - 0.1)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8, beam=0.6)
    M.cristal(fr.base, fr.fx, 'PALITO', u, t0=-0.1, cy=0.33, entrada='golpe')
    draw_objects(fr, control_m(roja=0.8))
    ps = fr.cam.p1((-0.3, CY - 0.14, TH / 2 + 0.1))

    def ui(img, fx):
        doodle_circle(img, fx, ps[0], ps[1], 230, 200, t, k=eout(seg(u, 0.1, 0.35)), col=RED, seed=8)
        pill(img, fx, ps[0], ps[1] + 300, 'STICK', eout(seg(u, 0.2, 0.4)), size=36, border=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.12, 0.3), amp=22)


# 13. debajo de cada stick, unos contactos de metal tallan una pista: la tapa sube y se ve la pista con su contacto
def s_pista(t, fi, u, d):
    upi = Wp(13, 'pista') - 0.1
    uc = Wp(13, 'contactos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 1.0, 10, 70, ty=0.6), K(0.4, 2.1, 30, 34, ty=0.45), K(d, 2.0, 36, 32, ty=0.45)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9, beam=0.5)
    tx = 0.6 * math.sin(t * 2.2)
    abre = seg(u, 0.0, 0.5)
    draw_objects(fr, modulo_stick((tx, 0), abre=abre, y=0.0))
    pista(fr, 0.0, 0.13, 0.0, r=0.36, k=seg(u, 0.2, 0.5), ang0=-0.6, ang1=2.0)
    a = 0.7 + 0.5 * tx
    p_w = (0.36 * math.cos(a), 0.14, 0.36 * math.sin(a))
    line3(fr, [(0, 0.14, 0), p_w], col=ACERO, w=5, a=seg(u, 0.3, 0.5), glow=0.5)
    dot3(fr, p_w, r=7, col=WHITE, a=seg(u, 0.3, 0.5), glow=1.2)
    chispas(fr, t, p_w, k=seg(u, uc, uc + 0.3) * 0.8, n=8, r=0.08)
    pp = fr.cam.p1((0.36 * math.cos(1.6), 0.13, 0.36 * math.sin(1.6)))
    pw = fr.cam.p1(p_w)

    def ui(img, fx):
        kicker(img, 'POR DENTRO DEL STICK', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pw[0] + 40, pw[1] - 170, 'CONTACTO DE METAL', eout(seg(u, uc, uc + 0.25)), size=28, border=WHITE)
        pill(img, fx, pp[0], pp[1] + 150, 'PISTA', eout(seg(u, upi, upi + 0.25)), size=30, border=NARANJA)
        esquema(img, fx, seg(u, 0.3, 0.5), y=1450)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. con el uso y el polvo se gasta: zoom digital (x1.0 → x1.8) sobre la pista que se llena de huecos y polvo
def s_gasta(t, fi, u, d):
    upo = Wp(14, 'polvo') - 0.1
    ug = Wp(14, 'gasta') - 0.1
    fr = Frame(camara(u, [K(-0.3, 1.5, 40, 40, tx=0.1, ty=0.15, tz=0.15), K(0.3, 1.2, 50, 44, tx=0.15, ty=0.15, tz=0.2),
                          K(d, 1.15, 54, 44, tx=0.15, ty=0.15, tz=0.2)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.7, beam=0.3)
    tx = 0.8 * math.sin(t * 5)
    draw_objects(fr, modulo_stick((tx, 0), abre=1.0))
    pista(fr, 0.0, 0.13, 0.0, r=0.36, k=1.0, gasto=seg(u, ug - 0.2, ug + 0.5), ang0=-0.6, ang1=2.0)
    a = 0.7 + 0.5 * tx
    p_w = (0.36 * math.cos(a), 0.14, 0.36 * math.sin(a))
    line3(fr, [(0, 0.14, 0), p_w], col=ACERO, w=5, a=1.0, glow=0.5)
    dot3(fr, p_w, r=7, col=WHITE, a=1.0, glow=1.2)
    chispas(fr, t, p_w, k=0.9, n=12, r=0.1)
    polvo(fr, t, (0.1, 0.12, 0.1), k=seg(u, upo, upo + 0.5), n=50, R=0.5)
    img = finish(fr, fi)
    z = 1.0 if u < 0.6 else (1.3 if u < 1.3 else 1.8)
    img = M.scale_about(img, z, 0.55, 0.5)
    im = Image.fromarray(img)
    fx = Image.new('RGB', im.size, (0, 0, 0))
    rec_frame(im, t, k=1.0, zoom_label=f'x{z:.1f}')
    pill(im, fx, 540, 1330, 'POLVO + ROCE = PISTA GASTADA', eout(seg(u, ug, ug + 0.25)), size=28, border=AMARILLO)
    a_ = np.asarray(im, np.float32) + np.asarray(fx, np.float32) * 0.5
    return a_.clip(0, 255).astype(np.uint8)


# 15. y el control cree que lo mueves aunque no lo toques: el stick quieto y la lectura que se va sola
def s_lectura(t, fi, u, d):
    un = Wp(15, 'aunque') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.0, -20, 30, tx=-0.3, ty=CY - 0.1), K(0.35, 1.6, -4, 34, tx=-0.3, ty=CY - 0.1),
                          K(d, 1.55, 0, 34, tx=-0.3, ty=CY - 0.1)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8, beam=0.4)
    draw_objects(fr, control_m())
    ps = fr.cam.p1((-0.3, CY - 0.14, TH / 2 + 0.1))
    dr = P.eout4(seg(u, 0.2, 2.2))

    def ui(img, fx):
        cx, cy, R = 540, 560, 220
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        k = seg(u, -0.1, 0.2)
        d_.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c(AZULC, k), width=4)
        d_.line([(cx - R, cy), (cx + R, cy)], fill=M.scale_c((80, 90, 100), k), width=2)
        d_.line([(cx, cy - R), (cx, cy + R)], fill=M.scale_c((80, 90, 100), k), width=2)
        px, py = cx + 0.42 * R * dr + 6 * math.sin(t * 7), cy - 0.25 * R * dr + 5 * math.cos(t * 9)
        d_.line([(cx, cy), (px, py)], fill=M.scale_c(RED, k * dr), width=3)
        d_.ellipse((px - 18, py - 18, px + 18, py + 18), fill=M.scale_c(RED, k))
        df.ellipse((px - 34, py - 34, px + 34, py + 34), fill=M.scale_c(RED, 0.6 * k))
        d_.text((cx - R, cy + R + 30), f'X {0.42 * dr:+.2f}   Y {0.25 * dr:+.2f}', font=M.font('mono', 34),
                fill=M.scale_c(WHITE, k))
        kicker(img, 'LO QUE LEE EL CONTROL', 260, k, col=AZULC)
        pill(img, fx, ps[0], ps[1] + 210, 'SIN TOCAR', eout(seg(u, un, un + 0.25)), size=32, border=WHITE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. eso es el drift: tu personaje camina solo… (mapa de alambre con un marcador que se va solo; entra por «DRIFT»)
def s_drift(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 0, 50, ty=0.0), K(0.4, 3.8, 24, 38, ty=0.0), K(d, 3.7, 28, 38, ty=0.0)], cy=0.5))
    space(fr, t, floor='lines', floor_a=1.0, bokeh=0.8, beam=0.3)
    for i in range(-4, 5):                                     # calles del mapa
        line3(fr, [(i * 0.5, 0.01, -2.2), (i * 0.5, 0.01, 2.2)], col=(120, 140, 170), w=2.6, a=0.85, glow=0.5)
        line3(fr, [(-2.2, 0.01, i * 0.5), (2.2, 0.01, i * 0.5)], col=(120, 140, 170), w=2.6, a=0.85, glow=0.5)
    for (bx, bz, bh) in ((-1.25, -1.25, 0.5), (0.25, -0.75, 0.8), (-0.75, 0.25, 0.35), (1.25, 0.75, 0.6), (0.75, -1.75, 0.4)):
        sq = [(bx - 0.18, 0, bz - 0.18), (bx + 0.18, 0, bz - 0.18), (bx + 0.18, 0, bz + 0.18), (bx - 0.18, 0, bz + 0.18)]
        for (x0, _, z0), (x1, _, z1) in zip(sq, sq[1:] + sq[:1]):
            line3(fr, [(x0, bh, z0), (x1, bh, z1)], col=AZULC, w=1.8, a=0.7, glow=0.6)
            line3(fr, [(x0, 0, z0), (x0, bh, z0)], col=AZULC, w=1.8, a=0.7, glow=0.6)
    s_ = seg(u, -0.3, d)
    path = lambda q: (-0.9 + 1.6 * q, 0.05, 0.9 - 1.2 * q + 0.15 * math.sin(q * 6))
    pts = [path(q * s_) for q in np.linspace(0, 1, 30)]
    line3(fr, pts, col=RED, w=3.0, a=0.8, glow=0.9)
    p = path(s_)
    for j in range(6):
        dot3(fr, path(max(0, s_ - 0.04 * j)), r=9 - j, col=RED, a=1 - 0.15 * j, glow=1.2)
    ps = fr.cam.p1(p)

    def ui(img, fx):
        kicker(img, 'EFECTO DRIFT', 150, seg(u, 0.0, 0.3), col=RED)
        pill(img, fx, ps[0], ps[1] - 140, 'CAMINA SOLO', eout(seg(u, 0.4, 0.65)), size=32, border=RED)
        texto(img, fx, 540, 1300, 'MANOS: 0', 40, col=WHITE, k=seg(u, 0.8, 1.0), f='mono', glow=0.2)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. y no es culpa del juego: «CULPA DEL JUEGO» se tacha y el marcador sigue yéndose; aparece «ES EL STICK»
def s_juego(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.7, 28, 38, ty=0.0), K(0.3, 2.6, -20, 30, ty=0.3), K(d, 2.5, -24, 30, ty=0.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=0.8, beam=0.3)
    draw_objects(fr, control_m(s=0.55, xs=0.0, ys=-0.45, rx=-30, roja=0.6))
    ps = fr.cam.p1((-0.3 * 0.55, CY - 0.45 - 0.08, 0.3))

    def ui(img, fx):
        P.pill_tachada(img, fx, 540, 330, 'CULPA DEL JUEGO', seg(u, 0.0, 0.2), seg(u, 0.4, 0.75), t, size=38)
        pill(img, fx, ps[0], ps[1] + 170, 'ES EL STICK', eout(seg(u, 0.8, 1.05)), size=36, border=RED)
        doodle_circle(img, fx, ps[0], ps[1], 110, 90, t, k=eout(seg(u, 0.85, 1.1)), col=RED, seed=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.75, 0.3), amp=16)


# 18. los sticks con imanes, de efecto Hall: el módulo Hall (imán + chip) con líneas de campo («IMANES» de cristal)
def s_hall(t, fi, u, d):
    uh = Wp(18, 'hall') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.6, -40, 20, ty=0.35), K(0.35, 2.0, -10, 14, ty=0.35), K(d, 1.95, -6, 14, ty=0.35)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'IMANES', u, t0=-0.1, cy=0.37, entrada='zoom')
    tx = 0.5 * math.sin(t * 2.0)
    draw_objects(fr, modulo_stick((tx, 0), abre=1.0, hall=True), xray=0.0)
    for j in range(5):                                         # líneas de campo del imán al chip
        a = -0.6 + 0.3 * j
        q = np.linspace(0, math.pi, 18)
        pts = [(0.06 * math.cos(a) * 3 * math.sin(s), 0.17 - 0.12 * (1 - math.cos(s)) / 2, 0.06 * math.sin(a) * 3 * math.sin(s))
               for s in q]
        line3(fr, pts, col=CYAN, w=2.2, a=0.8 * seg(u, 0.2 + 0.06 * j, 0.5 + 0.06 * j), glow=1.0)
    pc = fr.cam.p1((0, 0.05, 0.12))
    pm = fr.cam.p1((0, 0.18, 0.1))

    def ui(img, fx):
        kicker(img, 'STICK DE EFECTO HALL', 150, seg(u, uh - 0.1, uh + 0.2), col=AZULC)
        pill(img, fx, pm[0] - 230, pm[1] - 90, 'IMÁN', eout(seg(u, 0.3, 0.55)), size=30, border=IMAN_R)
        pill(img, fx, pc[0] + 220, pc[1] + 100, 'SENSOR', eout(seg(u, 0.55, 0.8)), size=30, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. no se tocan y casi no se gastan: lado a lado, el de pista echa chispas y el Hall flota sin roce
def s_comparar(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 0, 22, ty=0.3), K(0.3, 3.1, 0, 16, ty=0.3), K(d, 3.0, 4, 16, ty=0.3)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    tx = 0.6 * math.sin(t * 3)
    ms = modulo_stick((tx, 0), abre=1.0, x=-0.75, s=0.8) + modulo_stick((tx, 0), abre=1.0, x=0.75, s=0.8, hall=True)
    draw_objects(fr, ms)
    pista(fr, -0.75, 0.105, 0.0, r=0.36, s=0.8, k=1.0, gasto=0.8, ang0=-0.6, ang1=2.0)
    a = 0.7 + 0.5 * tx
    p_w = (-0.75 + 0.8 * 0.36 * math.cos(a), 0.11, 0.8 * 0.36 * math.sin(a))
    line3(fr, [(-0.75, 0.11, 0), p_w], col=ACERO, w=4, a=1.0, glow=0.5)
    chispas(fr, t, p_w, k=1.0, n=10, r=0.08)
    for j in range(4):
        a2 = -0.5 + 0.33 * j
        q = np.linspace(0, math.pi, 16)
        pts = [(0.75 + 0.8 * 0.18 * math.cos(a2) * math.sin(s), 0.8 * (0.17 - 0.12 * (1 - math.cos(s)) / 2),
                0.8 * 0.18 * math.sin(a2) * math.sin(s)) for s in q]
        line3(fr, pts, col=CYAN, w=2.0, a=0.8, glow=1.0)
    pl, pr = fr.cam.p1((-0.75, 0.0, 0.4)), fr.cam.p1((0.75, 0.0, 0.4))

    def ui(img, fx):
        pill(img, fx, pl[0], pl[1] + 150, 'ROCE · SE GASTA', eout(seg(u, 0.0, 0.25)), size=28, border=AMARILLO)
        pill(img, fx, pr[0], pr[1] + 150, 'SIN CONTACTO', eout(seg(u, 0.4, 0.65)), size=28, border=CYAN)
        texto(img, fx, 540, 330, 'VS', 90, col=WHITE, k=seg(u, 0.1, 0.3), f='sansx', glow=0.4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. mándaselo a tu compa que le echa la culpa al control: celular con el chat y el control al lado
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, 30, 8, tx=0.2, ty=0.95), K(0.3, 3.0, 4, 6, tx=0.2, ty=0.95), K(d, 2.95, 0, 6, tx=0.2, ty=0.95)],
                      cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    ms = P.celular(scr_chat(seg(u, 0.6, 0.8)), ry=-12, off=(0.65, max(0.0, -e['dy']), 0))
    ms += control_m(s=0.6, xs=-0.55, ys=-0.45, ry=25 + 10 * math.sin(t * 1.5))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'MÁNDASELO', 150, seg(u, 0.0, 0.3), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.25), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-3.3, 'whoosh_suave', 0.4), (-0.3, 'riser', 0.4), (U_GIRO, 'whoosh', 0.9), (U_GIRO + 0.2, 'burst', 0.5),
                     (U_GIRO + 0.4, 'burst', 0.5), (U_GIRO + 0.6, 'burst', 0.5), (U_GIRO + D_GIRO, 'sub', 1.0),
                     (U_GIRO + D_GIRO, 'shimmer', 0.6), (1.6, 'bass', 0.8)]),
           dict(desde=1, fn=s_motor, tr='zoom', c=(0.3, 0.62), sfx=[(0.5, 'scribble', 0.6), (1.4, 'bass', 0.7), (1.5, 'slap', 0.6)]),
           dict(desde=2, fn=s_centrado, tr='cubo', sfx=[(0.0, 'thud', 0.6), (0.9, 'click', 0.7), (1.1, 'scribble', 0.4)]),
           dict(desde=3, fn=s_liso, tr='deslizar', sfx=[(0.2, 'whoosh_suave', 0.5), (1.0, 'tick', 0.6), (1.5, 'chime_a', 0.4)]),
           dict(desde=4, fn=s_chueco, tr='giro', c=(0.5, 0.55), sfx=[(0.0, 'shimmer', 0.4), (0.4, 'scribble', 0.5)]),
           dict(desde=5, fn=s_jala, tr='whip', sfx=[(0.3, 'bass', 0.9), (0.35, 'burst', 0.4), (1.0, 'thud', 0.6), (1.6, 'thud', 0.5)]),
           dict(desde=6, fn=s_pesado, tr='rebanadas', sfx=[(0.6, 'whoosh', 0.5), (1.6, 'sub', 0.9), (1.6, 'bass', 0.8)]),
           dict(desde=7, fn=s_ligero, tr='deslizar_abajo', sfx=[(0.4, 'whoosh', 0.5), (1.0, 'tick2', 0.5), (1.2, 'tick2', 0.5),
                                                               (1.4, 'tick2', 0.5)]),
           dict(desde=8, fn=s_ps5, tr='cubo_izq', sfx=[(0.1, 'thud', 0.6), (1.0, 'shimmer', 0.5), (1.6, 'scribble', 0.6)]),
           dict(desde=9, fn=s_bocina, tr='iris', c=(0.45, 0.5), sfx=[(0.3, 'click', 0.5), (0.6, 'click', 0.5), (1.6, 'bass', 0.7)]),
           dict(desde=10, fn=s_lluvia, tr='remolino', sfx=[(0.3, 'tick', 0.4), (0.6, 'tick', 0.4), (2.4, 'shimmer', 0.5)]
                + [(2.6 + 0.17 * j, 'tick2', 0.3) for j in range(8)]),
           dict(desde=11, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.25, 'sub', 1.0), (0.25, 'bass', 0.8), (0.7, 'digital', 0.4)]),
           dict(desde=12, fn=s_palito, tr='golpe', sfx=[(0.12, 'bass', 0.9), (0.2, 'scribble', 0.6)]),
           dict(desde=13, fn=s_pista, tr='push', c=(0.33, 0.56), sfx=[(0.1, 'whoosh', 0.6), (0.6, 'click', 0.6), (1.6, 'scribble', 0.4)]),
           dict(desde=14, fn=s_gasta, tr='flash', sfx=[(0.6, 'click', 0.8), (1.3, 'click', 0.8), (1.5, 'burst', 0.3)]),
           dict(desde=15, fn=s_lectura, tr='mosaico', sfx=[(0.3, 'digital', 0.4), (1.0, 'tick', 0.5), (2.0, 'tick', 0.5)]),
           dict(desde=16, fn=s_drift, tr='cristal', palabra='DRIFT', sfx=[(0.5, 'whoosh_suave', 0.5), (1.2, 'tick2', 0.5)]),
           dict(desde=17, fn=s_juego, tr='glitch', sfx=[(0.4, 'scribble', 0.7), (0.8, 'bass', 0.8), (0.9, 'scribble', 0.4)]),
           dict(desde=18, fn=s_hall, tr='wipe', sfx=[(0.3, 'shimmer', 0.5), (0.6, 'chime_a', 0.4), (0.9, 'chime_b', 0.4)]),
           dict(desde=19, fn=s_comparar, tr='cubo', sfx=[(0.1, 'burst', 0.3), (0.5, 'chime_c', 0.5), (0.2, 'tick2', 0.4)]),
           dict(desde=20, fn=s_compa, tr='whip_izq', sfx=[(0.1, 'bass', 0.7), (0.7, 'click', 0.6), (0.8, 'chime_b', 0.4)]),
           dict(desde=21, loop=True, tr='zoom', c=(0.5, 0.5))]

if __name__ == '__main__':
    montaje.cli(globals())
