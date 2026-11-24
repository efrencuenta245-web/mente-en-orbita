"""Reel diario jue 26-nov-2026 10:00 (propuesto) — «Tu carro eléctrico frena… y se carga.»
Frenado regenerativo: al soltar el acelerador el motor eléctrico se vuelve generador, frena las llantas y regresa energía a
la batería (mismo principio que la dinamo de la bici). Prueba: en una bajada el de gasolina frena con balatas (calor) y el
eléctrico carga. Por dentro: los imanes siguen girando frente a las bobinas y empujan la corriente al revés. En ciudad regresa
cerca de un tercio (fueleconomy.gov: 32 % en ciudad; 22 % combinado, DOE FOTW #1360). Error (segundo gancho): cargarlo al
100 % antes de bajar la sierra (batería llena = regenerativo limitado; manual Hyundai 2026: «temporarily limited… fully
charged»; con frío, igual) y el frenón de último segundo (lo que pasa del límite del motor lo hacen las balatas). Olinia 1:
eléctrico de ciudad mexicano, desde 150 mil pesos, más de 125 km, entregas en verano de 2027 (El Imparcial, 16-ago-2026).
Comunidad: automovilistas. Inicio tipo 10 (rayos X de golpe): el carro azul rueda normal con «CARGA» de cristal detrás; en el
primer golpe se vuelve de cristal, se ve la batería y el motor, y los puntos de energía corren de las llantas a la batería.
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Datos y fuentes: guiones/2026-11-26_electrico.txt. Sin fotos reales (todo es esquema sin marca).
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import texto, esquema, golpe_k, sacudir, K, camara, _B, tubo
import velocimetro as V
import scooter as SC
import acumulador as AC

M3 = M.M3
_NF = [0]


def finish(fr, fi=0, **kw):
    """motor2.finish + rompe el ciclo fr → ui → fr (si no, cada cuadro se queda en memoria y el render se cae)."""
    import gc
    out = M.finish(fr, fi, **kw)
    fr.ui.clear()
    _NF[0] += 1
    if _NF[0] % 40 == 0:
        gc.collect()
    return out


TEMA = 'electrico'
TXT = ['Tu carro eléctrico frena… y se carga.',
       'Sueltas el acelerador y el motor se vuelve generador:',
       'frena las llantas y manda energía de regreso a la batería.',
       'Se llama frenado regenerativo,',
       'y es el mismo truco de la dinamo de la bici que prende el foco.',
       'Mira la diferencia en una bajada:',
       'el carro de gasolina frena con las balatas, y esa energía se va en puro calor.',
       'El eléctrico baja la misma cuesta… y la batería sube.',
       'Por dentro, los imanes siguen girando frente a las bobinas,',
       'y ese giro empuja la corriente al revés.',
       'Y aquí está el error:',
       'cargarlo al 100 % justo antes de bajar la sierra.',
       'Con la batería llena ya no le cabe nada:',
       'el frenado regenerativo se limita y frenas casi puro con balatas.',
       'Con la batería muy fría pasa lo mismo: los manuales lo advierten.',
       'Y el frenón de último segundo también se desperdicia:',
       'el motor solo frena hasta cierto punto, lo demás lo hacen las balatas.',
       'Por eso, soltar el acelerador con tiempo es frenar cargando.',
       'En el tráfico de ciudad, con tanto alto y siga,',
       'regresa cerca de un tercio de la energía.',
       'Y en México ya viene el Olinia, un eléctrico de ciudad para 2027:',
       'justo en la ciudad es donde este truco rinde más.',
       'Mándaselo a quien dice que los eléctricos no sirven en México.',
       'Porque tu carro eléctrico frena… y se carga.']
VOZ = ['Tu carro eléctrico frena... y se carga.',
       'Sueltas el acelerador y el motor se vuelve generador:',
       'frena las llantas y manda energía de regreso a la batería.',
       'Se llama frenado regenerativo,',
       'y es el mismo truco de la dinamo de la bici que prende el foco.',
       'Mira la diferencia en una bajada:',
       'el carro de gasolina frena con las balatas, y esa energía se va en puro calor.',
       'El eléctrico baja la misma cuesta... y la batería sube.',
       'Por dentro, los imanes siguen girando frente a las bobinas,',
       'y ese giro empuja la corriente al revés.',
       'Y aquí está el error:',
       'cargarlo al cien por ciento justo antes de bajar la sierra.',
       'Con la batería llena ya no le cabe nada:',
       'el frenado regenerativo se limita y frenas casi puro con balatas.',
       'Con la batería muy fría pasa lo mismo: los manuales lo advierten.',
       'Y el frenón de último segundo también se desperdicia:',
       'el motor solo frena hasta cierto punto, lo demás lo hacen las balatas.',
       'Por eso, soltar el acelerador con tiempo es frenar cargando.',
       'En el tráfico de ciudad, con tanto alto y siga,',
       'regresa cerca de un tercio de la energía.',
       'Y en México ya viene el Olinia, un eléctrico de ciudad para dos mil veintisiete:',
       'justo en la ciudad es donde este truco rinde más.',
       'Mándaselo a quien dice que los eléctricos no sirven en México.',
       'Porque tu carro eléctrico frena... y se carga.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_electrico.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-26_electrico_words.json')

AMARILLO = (255, 236, 160)
AMBAR = (255, 170, 40)
NARANJA = (255, 130, 50)
ROJO = (240, 50, 42)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (90, 220, 140)
AZUL_EV = (38, 100, 186)
ROJO_G = (150, 28, 34)
VERDE_O = (44, 132, 104)
HIELO = (200, 235, 255)
CROMO = (205, 208, 215)

# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    if not os.path.exists(WORDS):
        for i, f in enumerate(VOZ):
            _WT[i] = [0.3 * k for k in range(len(f.split()))]
        return _WT
    import difflib
    d = json.load(open(WORDS))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(montaje._norm(w.get('text', '')), float(w['start'])) for w in d
          if w.get('type', 'word') == 'word' and montaje._norm(w.get('text', ''))]
    sw = []
    for i, f in enumerate(VOZ):
        for w in f.split():
            if montaje._norm(w):
                sw.append((i, montaje._norm(w)))
    sm = difflib.SequenceMatcher(None, [w for _, w in sw], [w for w, _ in tw], autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    per = {}
    for j, (i, w) in enumerate(sw):
        per.setdefault(i, []).append(tw[mp[j]][1] if j in mp else None)
    for i, L in per.items():
        last = None
        for k in range(len(L)):
            if L[k] is None:
                L[k] = (last + 0.25) if last is not None else None
            last = L[k] if L[k] is not None else last
        base = next((x for x in L if x is not None), 0.0)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wp(i, palabra, n=0):
    ws = [montaje._norm(w) for w in VOZ[i].split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ el carro eléctrico (frente hacia +x) y sus piezas
def ev(giro=0.0, nivel=0.6, bat=0.0, motor=0.0, col=AZUL_EV, freno=0.0, rojo=0.0):
    """Sedán eléctrico sin marca: batería plana en el piso (10 celdas que se prenden con el nivel) y el motor en el eje
    de atrás. Con rayos X: keep=('bateria', 'celda', 'motor')."""
    ms = V.carro(col=col, giro_llanta=giro)
    _B(ms, 2.1, 0.09, 0.92, (34, 38, 46), -0.05, 0.36, 0.05, name='bateria', gloss=0.4)
    n_on = int(round(clamp(nivel) * 10))
    for j in range(10):
        on = j < n_on
        c = M.mixc(CYAN, ROJO, rojo) if on else (52, 58, 68)
        _B(ms, 0.15, 0.035, 0.8, c, -0.95 + 0.2 * j, 0.45, 0.05, name='celda', gloss=0.3,
           glow=M.scale_c(c, 0.12 + 0.3 * bat) if on else None)
    m = named(M3.cyl(0.17, 0.44, (122, 126, 136), n=26, shadow=0, gloss=0.7, y0=-0.22).tf(rx=90, t=(-1.0, 0.33, 0.06)),
              'motor', rim=0.8, gloss=0.7)
    if motor > 0.01:
        m.glow = M.scale_c(CYAN, 0.7 * motor)
    ms.append(m)
    if freno > 0.01:
        for z in (-0.45, 0.45):
            _B(ms, 0.05, 0.11, 0.28, (255, 40, 30), -1.52, 0.58, z, name='calavera', glow=M.scale_c((255, 40, 30), freno))
    return ms


_RUTA = [(-1.0, 0.33, 0.72), (-1.0, 0.33, 0.06), (-0.78, 0.47, 0.05), (0.85, 0.47, 0.05)]


def flujo(fr, t, k=1.0, regen=True, n=9, vel=1.0, tf=None, col=None):
    """Puntos de energía: de la llanta al motor y del motor a la batería (regen, cian) o al revés (consumo, ámbar).
    tf: función que transforma cada punto (para cuando el carro está movido o inclinado)."""
    if k <= 0.01:
        return
    pts = [np.array(p, float) for p in _RUTA]
    if tf is not None:
        pts = [np.array(tf(p), float) for p in pts]
    col = col or (CYAN if regen else AMBAR)
    line3(fr, [tuple(p) for p in pts], col=col, w=3, a=0.45 * k, glow=0.7)
    Ls = [np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])]
    tot = sum(Ls)
    for j in range(n):
        s = (t * 0.9 * vel + j / n) % 1.0
        if not regen:
            s = 1 - s
        d = s * tot
        for a, b, L in zip(pts, pts[1:], Ls):
            if d <= L:
                p = a + (b - a) * (d / max(L, 1e-6))
                break
            d -= L
        dot3(fr, tuple(p), r=8, col=col, a=k, glow=1.5)


def en_cuesta(ms, x, ang=12.0, y0=0.0, z=0.0):
    """Coloca mallas en la cuesta (baja hacia +x): y = y0 − tan(ang)·x."""
    y = y0 - math.tan(math.radians(ang)) * x
    return P.tfk(ms, rz=-ang, t=(x, y, z))


def tf_cuesta(x, ang=12.0, y0=0.0, z=0.0):
    a = math.radians(-ang)
    y = y0 - math.tan(math.radians(ang)) * x

    def f(p):
        px, py, pz = p
        return (x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a), pz + z)
    return f


def cuesta(fr, ang=12.0, y0=0.0, zs=(-1.3, 1.3), a=0.8):
    for z in zs:
        line3(fr, [(-9, y0 + math.tan(math.radians(ang)) * 9, z), (9, y0 - math.tan(math.radians(ang)) * 9, z)],
              col=WHITE, w=2.4, a=a, glow=0.5)


def disco(calor=0.0, giro=0.0, s=1.0):
    """Disco de freno con su caliper (las balatas): se pone rojo-naranja y brilla con el calor."""
    ms = []
    c = M.mixc((150, 152, 160), (255, 110, 40), clamp(calor))
    d = named(M3.cyl(0.62, 0.07, c, n=40, shadow=0, gloss=0.85, y0=-0.035).tf(rx=90), 'disco', rim=0.8, gloss=0.85)
    if calor > 0.05:
        d.glow = M.scale_c((255, 90, 30), 0.85 * clamp(calor))
    ms.append(d)
    ms.append(named(M3.cyl(0.25, 0.1, (70, 72, 80), n=24, shadow=0, gloss=0.6, y0=-0.05).tf(rx=90), 'maza', rim=0.7))
    for j in range(5):
        a = math.radians(giro + j * 72)
        ms.append(named(M3.cyl(0.035, 0.12, CROMO, n=10, shadow=0, gloss=0.9, y0=-0.06).tf(rx=90, t=(0.16 * math.cos(a), 0.16 * math.sin(a), 0.02)), 'birlo', rim=0.8))
    for j in range(16):
        a = math.radians(giro + j * 22.5)
        ms.append(named(M3.box(0.03, 0.09, 0.075, M.mixc((96, 98, 106), (200, 70, 30), calor), shadow=0, base=False).tf(rz=giro + j * 22.5, t=(0.48 * math.cos(a), 0.48 * math.sin(a), 0)), 'ranura', rim=0.4))
    cal = named(M3.rbox(0.36, 0.5, 0.2, 0.05, (196, 34, 30), n=4, shadow=0, gloss=0.6).tf(rz=-35, t=(0.42, 0.28, 0.02)), 'caliper', rim=0.8, gloss=0.6)
    ms.append(cal)
    return P.tfk(ms, s=s)


def pedal(ang=0.0):
    """Pedal del acelerador colgado de su pivote (arriba); ang en grados (negativo = pisado)."""
    ms = [tubo((0, 1.3, 0), (0.0, 0.35, 0), r=0.045, col=(150, 154, 164), name='brazo')]
    _B(ms, 0.36, 0.55, 0.07, (78, 80, 88), 0.0, 0.05, 0.0, name='pedal', gloss=0.5, rim=0.9)
    for j in range(5):
        _B(ms, 0.3, 0.025, 0.08, (120, 122, 130), 0.0, 0.12 + j * 0.09, 0.0, name='hule', gloss=0.3)
    ms.append(named(M3.cyl(0.07, 0.2, CROMO, n=16, shadow=0, gloss=0.9, y0=-0.1).tf(rx=90, t=(0, 1.3, 0)), 'pivote', rim=0.9))
    return [m.tf(t=(0, -1.3, 0)).tf(rx=ang).tf(t=(0, 1.3, 0)) for m in ms]


def bici_dinamo(pedal_ang=0.0, foco=0.0):
    ms = SC.bici(pedal=pedal_ang)
    ms.append(named(M3.cyl(0.05, 0.14, CROMO, n=16, shadow=0, gloss=0.9).tf(rz=-35, t=(-0.36, 0.72, 0.07)), 'dinamo', rim=0.9))
    f = named(M3.sphere(0.07, (255, 240, 190), nu=20, nv=12, shadow=0, gloss=0.6).tf(t=(0.6, 1.06, 0)), 'foco', rim=0.6)
    if foco > 0.01:
        f.glow = M.scale_c((255, 220, 130), 1.4 * foco)
    ms.append(f)
    return ms


def montanas(fr, a=0.7, z=-5.0):
    pts = [(-9, -0.5, z), (-6, 2.2, z), (-4.2, 1.2, z), (-1.5, 3.8, z), (1.2, 1.6, z), (3.6, 3.0, z), (6, 0.8, z), (9, 2.0, z)]
    line3(fr, pts, col=WHITE, w=2.6, a=a, glow=0.6)


def edificios(fr, a=0.6, z=-4.0, seed=4):
    rng = np.random.RandomState(seed)
    x = -9.0
    while x < 9:
        w = rng.uniform(0.7, 1.6)
        h = rng.uniform(1.2, 4.2)
        line3(fr, [(x, 0, z), (x, h, z), (x + w, h, z), (x + w, 0, z)], col=WHITE, w=2.0, a=a, glow=0.5)
        for j in range(int(h / 0.6)):
            if rng.rand() < 0.5:
                dot3(fr, (x + w * rng.uniform(0.2, 0.8), 0.3 + j * 0.6, z), r=4, col=AMARILLO, a=0.6 * a, glow=0.8)
        x += w + rng.uniform(0.1, 0.5)


def semaforo(img, fx, x, y, rojo, k=1.0):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.rounded_rectangle((x - 46, y - 130, x + 46, y + 130), radius=22, fill=(16, 16, 18), outline=M.scale_c(WHITE, 0.6 * k), width=3)
    for j, (c, on) in enumerate((((255, 50, 40), rojo), ((255, 190, 40), 0.0), ((60, 230, 120), 1 - rojo))):
        yy = y - 80 + j * 80
        cc = M.scale_c(c, k * (0.18 + 0.82 * on))
        d.ellipse((x - 30, yy - 30, x + 30, yy + 30), fill=cc)
        if on > 0.3:
            df.ellipse((x - 48, yy - 48, x + 48, yy + 48), fill=M.scale_c(c, 0.6 * k * on))


def tarjeta_manual(img, k, y0=300):
    """Cita del manual del propietario (texto traducido)."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    y = y0 - 300 * (1 - P.eout4(k))
    d.rounded_rectangle((110, y, 970, y + 430), radius=20, fill=(240, 238, 232), outline=(200, 198, 190), width=3)
    texto(img, None, 160, y + 60, 'MANUAL DEL PROPIETARIO', 34, (60, 60, 66), 1.0, f='mono', glow=0, anchor='lm')
    texto(img, None, 160, y + 108, 'ELÉCTRICO 2026 · FRENADO REGENERATIVO', 24, (110, 110, 116), 1.0, f='mono', glow=0, anchor='lm')
    for j, ln in enumerate(['«Según la carga de la batería', '(llena) y su temperatura (alta', 'o baja), el sistema se puede', 'limitar.»']):
        texto(img, None, 160, y + 190 + j * 54, ln, 38, (30, 30, 36), 1.0, f='serif', glow=0, anchor='lm')


def contador(img, fx, x, y, val, k=1.0, col=CYAN, size=96, suf=' %'):
    texto(img, fx, x, y, f'{int(round(val))}{suf}', size, col, k, f='mono', glow=0.5)


# ================================================================== escenas
UG = 0.3
GIRO = lambda t, v=1.0: -t * 6.0 * v / 0.33


def _gancho(t, fi, u):
    fr = Frame(camara(u, [K(-4.0, 7.6, -38, 9, ty=0.62), K(UG, 7.0, -30, 8, ty=0.62), K(UG + 0.6, 5.8, -60, 12, ty=0.55),
                          K(3.2, 5.7, -64, 12, ty=0.55)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'CARGA', u, t0=-2.6, cy=0.34, entrada='golpe')
    vel = 1.0 - 0.6 * seg(u, UG, UG + 1.2)
    V.carretera(fr, t, vel=vel, a=0.6)
    kx = P.eout4(seg(u, UG - 0.06, UG + 0.12))
    ms = ev(giro=GIRO(t, vel), nivel=0.55 + 0.15 * seg(u, UG, 3.0), bat=kx, motor=kx)
    draw_objects(fr, ms, xray=0.88 * kx, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=kx, regen=True)

    def ui(img, fx):
        kicker(img, 'FRENADO REGENERATIVO', 140, seg(u, UG, UG + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu carro eléctrico frena…', 'sans'), ('y se carga.', 'serif')], 190, seg(u, UG, UG + 0.15), size=66)
        if kx > 0.05:
            x, y, _ = fr.cam.p1((0.2, 0.5, 0.05))
            pill(img, fx, x, y + 170, 'BATERÍA', eout(seg(u, UG + 0.3, UG + 0.55)), size=30, border=CYAN)
            xm, ym, _ = fr.cam.p1((-1.0, 0.33, 0.06))
            pill(img, fx, xm - 30, ym - 200, 'MOTOR', eout(seg(u, UG + 0.45, UG + 0.7)), size=30, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi, flash=0.55 * golpe_k(u, UG - 0.05, 0.25))


# 0. gancho, inicio 10 (rayos X de golpe): el carro rueda normal y en el primer golpe se vuelve de cristal
def s_gancho(t, fi, u, d):
    return sacudir(_gancho(t, fi, u), t, golpe_k(u, UG + 0.12, 0.35), amp=22)


# 1. sueltas el acelerador y el motor se vuelve generador (el pedal sube de golpe)
def s_suelta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.0, 60, 8, ty=0.6), K(0.3, 2.3, 30, 4, ty=0.6), K(5, 2.25, 26, 4, ty=0.6)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.6)
    us = Wp(1, 'acelerador') + 0.1
    ang = -24 + 24 * P.resorte(seg(u, us, us + 0.35))
    draw_objects(fr, pedal(ang))
    ug = Wp(1, 'generador') - 0.1

    def ui(img, fx):
        V.flecha(img, fx, 800, 1050, 800, 650, AMARILLO, k=seg(u, us, us + 0.3), w=10)
        texto(img, fx, 800, 600, 'SUELTAS', 44, AMARILLO, seg(u, us + 0.1, us + 0.3), f='mono', glow=0.4)
        pill(img, fx, 300, 1180, 'ACELERADOR', eout(seg(u, -0.1, 0.2)), size=32, border=AMARILLO)
        k = seg(u, ug, ug + 0.18)
        if k > 0:
            texto(img, fx, 540, 330, 'MOTOR', 70, WHITE, k, f='sansx', glow=0.3)
            texto(img, fx, 540, 420, '→ GENERADOR', 74, CYAN, seg(u, ug + 0.1, ug + 0.28), f='sansx', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ug + 0.1, 0.25), amp=12)


# 2. frena las llantas y manda energía de regreso a la batería (rayos X de lado; las celdas se prenden una a una)
def s_regreso(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, -40, 4, tx=-0.4, ty=0.5), K(0.3, 5.2, -12, 6, tx=-0.1, ty=0.5), K(5, 5.25, -8, 6, tx=-0.1, ty=0.5)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.4)
    vel = 1.0 - 0.5 * seg(u, 0, d)
    V.carretera(fr, t, vel=vel, a=0.5)
    ub = Wp(2, 'bateria') - 0.1
    niv = 0.5 + 0.2 * seg(u, Wp(2, 'energia'), ub + 0.4)
    draw_objects(fr, ev(giro=GIRO(t, vel), nivel=niv, bat=1.0, motor=1.0), xray=0.9, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=1.0, regen=True, vel=1.3)

    def ui(img, fx):
        xm, ym, _ = fr.cam.p1((-1.0, 0.33, 0.06))
        doodle_circle(img, fx, xm, ym, 110, 110, t, k=seg(u, 0.0, 0.3), col=CYAN, seed=2)
        pill(img, fx, xm, ym - 190, 'FRENA LA LLANTA', eout(seg(u, 0.1, 0.35)), size=28, border=CYAN)
        x, y, _ = fr.cam.p1((0.3, 0.5, 0.05))
        pill(img, fx, x, y + 190, 'ENERGÍA → BATERÍA', eout(seg(u, ub, ub + 0.25)), size=30, border=VERDE)
        contador(img, fx, 540, 420, 50 + 20 * seg(u, Wp(2, 'energia'), ub + 0.4), k=seg(u, 0.0, 0.2), col=VERDE)
        esquema(img, fx, seg(u, 0, 0.3), y=520, txt='EJEMPLO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. se llama frenado regenerativo (llega por la transición «cristal» con FRENADO; el motor en corte gira detrás)
def s_nombre(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 30, 4, ty=1.1), K(0.3, 4.0, 0, 0, ty=1.1), K(5, 3.95, -4, 0, ty=1.1)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.5)
    ang = t * 140
    draw_objects(fr, SC.motor_corte(ang, activas=SC.activas_de(ang), k_bob=0.8, s=0.9, y=1.1, tire=False))

    def ui(img, fx):
        kicker(img, 'SE LLAMA', 300, seg(u, -0.1, 0.1), col=AZULC)
        P.titulo_golpe(img, fx, [('Frenado', 'sans'), ('regenerativo.', 'serif')], 360, seg(u, 0.0, 0.15), size=96)
        k = seg(u, 0.3, 0.7)
        doodle_arrow(img, fx, 250, 1420, 830, 1420, t, k=k, col=CYAN, seed=4)
        doodle_arrow(img, fx, 830, 1500, 250, 1500, t, k=seg(u, 0.5, 0.9), col=AMBAR, seed=6)
        texto(img, fx, 540, 1370, 'SALE', 30, CYAN, k, f='mono', glow=0.3)
        texto(img, fx, 540, 1560, 'Y REGRESA', 30, AMBAR, seg(u, 0.5, 0.9), f='mono', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.25), amp=12)


# 4. el mismo truco de la dinamo de la bici que prende el foco
def s_dinamo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, -60, 10, tx=0.0, ty=0.7), K(0.3, 3.1, -20, 6, ty=0.7), K(5, 3.05, -14, 6, ty=0.7)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    uf = Wp(4, 'foco') - 0.15
    kf = seg(u, Wp(4, 'dinamo'), uf + 0.2)
    e = P.entrada(u, -0.2, 0.3, 'gira')
    ms = bici_dinamo(pedal_ang=t * 260, foco=0.3 + 0.7 * kf * (0.85 + 0.15 * math.sin(t * 40)))
    draw_objects(fr, P.tfk(ms, ry=math.degrees(e['giro']) * 0.2))
    line3(fr, [(-0.36, 0.78, 0.08), (-0.1, 1.0, 0.04), (0.5, 1.04, 0.02), (0.6, 1.06, 0)], col=AMARILLO, w=2.6, a=0.7 * kf, glow=0.9)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-0.36, 0.72, 0.07))
        pill(img, fx, x - 60, y + 160, 'DINAMO', eout(seg(u, Wp(4, 'dinamo') - 0.1, Wp(4, 'dinamo') + 0.15)), size=30, border=AMARILLO)
        xf, yf, _ = fr.cam.p1((0.6, 1.06, 0))
        pill(img, fx, xf + 20, yf - 150, 'FOCO', eout(seg(u, uf, uf + 0.25)), size=30, border=AMARILLO)
        texto(img, fx, 540, 360, 'GIRA → LUZ', 64, AMARILLO, seg(u, uf, uf + 0.25), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. mira la diferencia en una bajada (los dos carros arriba de la misma cuesta)
def _dos_en_cuesta(fr, t, u, xg, xe, kcal=0.0, keve=0.0, nivel=0.6):
    cuesta(fr, ang=12, y0=0.0, zs=(-2.3, -0.3, 0.3, 2.3), a=0.7)
    draw_objects(fr, en_cuesta(ev(col=ROJO_G, giro=GIRO(t, 0.5), nivel=0.0, freno=kcal), xg, z=-1.3)
                 + en_cuesta(ev(giro=GIRO(t, 0.5), nivel=nivel, bat=keve, motor=keve), xe, z=1.3),
                 xray=0.0)


def s_bajada(t, fi, u, d):
    x = -1.0 + 0.5 * u
    yx = -math.tan(math.radians(12)) * x
    fr = Frame(camara(u, [K(-0.3, 12.0, 50, 30, tx=x, ty=yx + 0.5), K(0.3, 10.5, 24, 30, tx=x, ty=yx + 0.5), K(5, 10.45, 20, 30, tx=x, ty=yx + 0.5)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.3)
    _dos_en_cuesta(fr, t, u, x, x)

    def ui(img, fx):
        xg, yg, _ = fr.cam.p1((x, 1.6 - math.tan(math.radians(12)) * x, -1.3))
        xe, ye, _ = fr.cam.p1((x, 1.6 - math.tan(math.radians(12)) * x, 1.3))
        pill(img, fx, xg, yg - 60, 'GASOLINA', eout(seg(u, 0.1, 0.35)), size=30, border=ROJO)
        pill(img, fx, xe, ye - 60, 'ELÉCTRICO', eout(seg(u, 0.25, 0.5)), size=30, border=CYAN)
        P.titulo_golpe(img, fx, [('La misma bajada.', 'sans')], 300, seg(u, Wp(5, 'bajada') - 0.1, Wp(5, 'bajada') + 0.05), size=70)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(5, 'bajada') + 0.05, 0.25), amp=10)


# 6. el de gasolina frena con las balatas y la energía se va en calor («CALOR» de cristal detrás del disco)
def s_balatas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 40, 10, ty=0.05), K(0.3, 2.8, 14, 6, ty=0.05), K(5, 2.75, 10, 6, ty=0.05)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.4)
    uc = Wp(6, 'calor') - 0.2
    M.cristal(fr.base, fr.fx, 'CALOR', u, t0=uc, cy=0.3, entrada='sube')
    calor = seg(u, Wp(6, 'balatas') - 0.2, uc + 0.5)
    draw_objects(fr, disco(calor=calor, giro=-t * 260 * (1 - 0.7 * calor)))
    P.ondas_calor(fr, t, 0.0, 0.7, 1.9, 1.4, k=calor, col=NARANJA, n=6)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0.42, 0.28, 0.02))
        pill(img, fx, x + 40, y + 200, 'BALATAS', eout(seg(u, Wp(6, 'balatas') - 0.1, Wp(6, 'balatas') + 0.15)), size=30, border=ROJO)
        P.termometro(img, fx, 150, 1300, 380, 0.15 + 0.8 * calor, f'{int(40 + 360 * calor)} °C', k=seg(u, 0.0, 0.3), col=NARANJA)
        esquema(img, fx, seg(u, 0.2, 0.5), y=1440, txt='EJEMPLO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. el eléctrico baja la misma cuesta… y la batería sube (rayos X en la cuesta; el porcentaje sube)
def s_sube(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.6, -40, 8, tx=0.4, ty=0.4), K(0.3, 6.0, -14, 8, tx=0.4, ty=0.3), K(5, 5.95, -10, 8, tx=0.4, ty=0.3)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.3)
    x = -0.4 + 0.45 * u
    cuesta(fr, ang=12, zs=(-0.8, 0.9), a=0.7)
    us = Wp(7, 'sube') - 0.3
    kb = seg(u, us - 0.6, us + 0.4)
    draw_objects(fr, en_cuesta(ev(giro=GIRO(t, 0.6), nivel=0.6 + 0.2 * kb, bat=1.0, motor=1.0), x), xray=0.9, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=1.0, regen=True, vel=1.4, tf=tf_cuesta(x))

    def ui(img, fx):
        contador(img, fx, 540, 380, 60 + 20 * kb, k=1.0, col=VERDE, size=150)
        texto(img, fx, 540, 500, 'BATERÍA ↑', 44, VERDE, seg(u, us, us + 0.2), f='mono', glow=0.4)
        esquema(img, fx, 1.0, y=590, txt='EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.3, 0.25), amp=10)


# 8. por dentro, los imanes siguen girando frente a las bobinas (la cámara entra al motor; «IMANES» de cristal)
def s_imanes(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.2, -50, 20, ty=1.1), K(0.3, 3.6, -12, 6, ty=1.1), K(5, 3.55, -8, 6, ty=1.1)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'IMANES', u, t0=-0.1, cy=0.28, entrada='golpe')
    ang = t * 120
    e = P.entrada(u, -0.2, 0.3, 'pop')
    draw_objects(fr, P.tfk(SC.motor_corte(ang, activas=(), s=1.0, y=0.0, tire=False), s=max(0.05, e['escala']), t=(0, 1.1, 0)))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0.0, 1.1 + 0.69, 0))
        pill(img, fx, x + 200, y - 60, 'IMANES (GIRAN)', eout(seg(u, Wp(8, 'imanes') - 0.1, Wp(8, 'imanes') + 0.15)), size=30, border=ROJO)
        xb, yb, _ = fr.cam.p1((0.0, 1.1 - 0.52, 0))
        pill(img, fx, xb, yb + 40, 'BOBINAS (FIJAS)', eout(seg(u, Wp(8, 'bobinas') - 0.1, Wp(8, 'bobinas') + 0.15)), size=30, border=AMBAR)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. y ese giro empuja la corriente al revés (las bobinas brillan y los puntos salen hacia la batería)
def s_reves(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 30, 8, tx=1.0, ty=1.1), K(0.3, 3.9, 8, 4, tx=1.0, ty=1.1), K(5, 3.95, 4, 4, tx=1.0, ty=1.1)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    ang = t * 120
    ur = Wp(9, 'reves') - 0.2
    kr = seg(u, 0.2, ur)
    draw_objects(fr, SC.motor_corte(ang, activas=tuple(range(12)), k_bob=0.3 + 0.7 * kr, s=0.9, x=0.0, y=1.1, tire=False)
                 + P.pila(0.5 + 0.3 * kr, x=2.1, y=0.45, z=0.0, ancho=0.55, alto=1.1))
    pts = [(0.45, 1.1, 0.1), (1.2, 1.1, 0.1), (1.6, 1.62, 0.1), (2.1, 1.62, 0.1)]
    line3(fr, pts, col=CYAN, w=3, a=0.6 * kr, glow=0.8)
    for j in range(7):
        s = (t * 1.1 + j / 7) % 1.0
        q = np.array(pts[0]) + (np.array(pts[1]) - np.array(pts[0])) * min(1, s * 2) if s < 0.5 else \
            np.array(pts[1]) + (np.array(pts[3]) - np.array(pts[1])) * (s - 0.5) * 2
        dot3(fr, tuple(q), r=8, col=CYAN, a=kr, glow=1.5)

    def ui(img, fx):
        k = seg(u, ur, ur + 0.2)
        texto(img, fx, 540, 340, 'CORRIENTE', 70, WHITE, seg(u, 0.1, 0.3), f='sansx', glow=0.3)
        texto(img, fx, 540, 440, 'AL REVÉS', 80, CYAN, k, f='sansx', glow=0.6)
        V.flecha(img, fx, 760, 1300, 300, 1300, CYAN, k=k, w=10)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ur + 0.1, 0.25), amp=12)


# 10. en el tráfico de ciudad, con tanto alto y siga (semáforo: en rojo frena y carga, en verde gasta)
def s_ciudad(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 9.0, -50, 22, tx=0.0, ty=0.6), K(0.3, 7.8, -20, 14, ty=0.9), K(5, 7.75, -16, 14, ty=0.9)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.2)
    edificios(fr, a=0.55, z=-4.0)
    ph = (u * 0.8) % 1.0
    rojo = 1.0 if ph < 0.5 else 0.0
    vel = 0.2 if rojo else 1.0
    V.carretera(fr, t, vel=vel, a=0.6)
    draw_objects(fr, ev(giro=GIRO(t, vel), nivel=0.6, bat=1.0, motor=1.0, freno=rojo), xray=0.8, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=1.0, regen=bool(rojo), vel=1.3)

    def ui(img, fx):
        semaforo(img, fx, 900, 520, rojo, k=seg(u, -0.1, 0.15))
        texto(img, fx, 420, 420, 'ALTO → CARGA' if rojo else 'SIGA → GASTA', 54, CYAN if rojo else AMBAR, seg(u, 0.0, 0.2), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. regresa cerca de un tercio de la energía («32 %» de cristal y las barras del DOE)
def s_tercio(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.6, 40, 10, ty=0.6), K(0.3, 6.2, 18, 8, ty=0.6), K(5, 6.15, 14, 8, ty=0.6)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, '32 %', u, t0=Wp(19, 'tercio') - 0.3, cy=0.3, entrada='zoom')
    draw_objects(fr, ev(giro=GIRO(t, 0.4), nivel=0.7, bat=1.0, motor=1.0), xray=0.85, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=1.0, regen=True)

    def ui(img, fx):
        k = seg(u, Wp(19, 'tercio') - 0.1, Wp(19, 'tercio') + 0.6)
        AC.barras(img, fx, [('EN CIUDAD', 0.32 * k * 2.2, CYAN, '32 %'), ('CIUDAD + CARRETERA', 0.22 * k * 2.2, AZULC, '22 %')],
                  120, 1230, 640, k=seg(u, 0.0, 0.3), alto=60, gap=130)
        pill(img, fx, 540, 1458, 'FUELECONOMY.GOV · DEPTO. DE ENERGÍA EE. UU.', seg(u, 0.3, 0.6), size=20, border=GRIS, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(19, 'tercio') - 0.1, 0.3), amp=14)


# 12. y aquí está el error (todo se pone rojo con falla)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 60, 14, ty=0.6), K(0.3, 5.4, 30, 8, ty=0.6), K(5, 5.45, 26, 8, ty=0.6)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    draw_objects(fr, ev(nivel=1.0, bat=1.0, motor=0.0, rojo=1.0), xray=0.85, xray_col=RED, keep=('bateria', 'celda'))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 300, seg(u, 0.05, 0.2), size=92, col=WHITE)
        texto(img, fx, 540, 1250, '⚠', 160, ROJO, seg(u, 0.2, 0.35), f='sansx', glow=0.8)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.35), amp=20)


# 13. cargarlo al 100 % justo antes de bajar la sierra (arriba de la sierra con la batería llena)
def s_cien(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 9.0, -20, 6, tx=-2.0, ty=1.6), K(0.3, 8.0, -36, 10, tx=-2.0, ty=1.6), K(5, 7.95, -40, 10, tx=-2.0, ty=1.6)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.3, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, '100 %', u, t0=Wp(11, 'cien') - 0.25, cy=0.3, entrada='golpe')
    montanas(fr, a=0.7)
    cuesta(fr, ang=14, y0=1.0, zs=(-0.8, 0.9), a=0.6)
    draw_objects(fr, en_cuesta(ev(nivel=1.0, bat=1.0), -2.2, ang=14, y0=1.0), xray=0.8, keep=('bateria', 'celda', 'motor'))

    def ui(img, fx):
        contador(img, fx, 540, 1250, 100 * seg(u, 0.0, Wp(11, 'cien') + 0.2), k=seg(u, 0, 0.15), col=VERDE, size=110)
        pill(img, fx, 540, 1380, 'ARRIBA DE LA SIERRA', eout(seg(u, Wp(11, 'sierra') - 0.2, Wp(11, 'sierra'))), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(11, 'cien'), 0.3), amp=16)


# 14. con la batería llena ya no le cabe nada (los puntos chocan contra la pila llena y rebotan)
def s_llena(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, -40, 8, ty=0.7), K(0.3, 3.8, -10, 4, ty=0.7), K(5, 3.75, -6, 4, ty=0.7)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.6)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    draw_objects(fr, P.pila(1.0, x=0.4, y=max(0.0, -e['dy']) * 0.5, ancho=0.9, alto=1.6, col_fill=VERDE))
    kx = seg(u, Wp(12, 'cabe') - 0.2, Wp(12, 'cabe') + 0.1)
    for j in range(8):
        s = (t * 1.2 + j / 8) % 1.0
        x = -2.6 + 2.4 * min(s * 1.6, 1.0)
        if s > 0.625:
            x = -0.2 - 1.2 * (s - 0.625) / 0.375
        dot3(fr, (x, 1.0 + 0.25 * math.sin(j * 1.7), 0.1), r=9, col=CYAN if s < 0.625 else ROJO, a=1.0, glow=1.4)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-0.15, 1.0, 0.1))
        if kx > 0:
            d = ImageDraw.Draw(img)
            r = 70 * eout(kx)
            d.line([(x - r, y - r), (x + r, y + r)], fill=ROJO, width=14)
            d.line([(x - r, y + r), (x + r, y - r)], fill=ROJO, width=14)
        pill(img, fx, 540, 360, 'LLENA: NO LE CABE NADA', eout(seg(u, 0.1, 0.35)), size=36, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(12, 'cabe'), 0.25), amp=12)


# 15. el frenado regenerativo se limita y frenas casi puro con balatas (barras que se voltean; el disco se calienta)
def s_limita(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, -40, 10, tx=0.0, ty=0.4), K(0.3, 3.0, -14, 6, tx=0.0, ty=0.4), K(5, 2.95, -10, 6, ty=0.4)], cy=0.36))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.4)
    kb = seg(u, Wp(13, 'balatas') - 0.5, Wp(13, 'balatas') + 0.2)
    draw_objects(fr, disco(calor=0.2 + 0.75 * kb, giro=-t * 200))
    P.ondas_calor(fr, t, 0.0, 0.7, 1.7, 1.3, k=kb, col=NARANJA, n=5)

    def ui(img, fx):
        kl = seg(u, Wp(13, 'limita') - 0.2, Wp(13, 'limita') + 0.3)
        AC.barras(img, fx, [('REGENERATIVO', 0.8 - 0.7 * kl, CYAN, 'LIMITADO' if kl > 0.5 else 'NORMAL'),
                            ('BALATAS', 0.2 + 0.7 * kb, ROJO, 'CASI TODO' if kb > 0.5 else 'POCO')],
                  120, 1150, 520, k=seg(u, 0.0, 0.25), alto=64, gap=140)
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. con la batería muy fría pasa lo mismo: los manuales lo advierten (pila con escarcha y la cita del manual)
def s_fria(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 30, 10, tx=0.0, ty=0.8), K(0.3, 4.2, 10, 6, ty=0.8), K(5, 4.15, 6, 6, ty=0.8)], cy=0.7))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    kf = seg(u, 0.0, Wp(14, 'fria') + 0.3)
    draw_objects(fr, P.pila(0.7, x=0.0, ancho=0.9, alto=1.5, col_fill=M.mixc(CYAN, HIELO, kf)))
    um = Wp(14, 'manuales') - 0.2

    def ui(img, fx):
        AC.escarcha(img, fx, fr, kf, seed=4, n=30, caja=(-0.5, 0.0, 0.5, 1.5))
        P.termometro(img, fx, 160, 1250, 300, 0.6 - 0.5 * kf, f'{int(20 - 30 * kf)} °C', k=seg(u, 0.0, 0.3), col=AZULC)
        tarjeta_manual(img, seg(u, um, um + 0.35), y0=280)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.35, 0.25), amp=12)


# 17. y el frenón de último segundo también se desperdicia (el carro llega rápido y clava el freno)
def s_frenon(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.0, 150, 8, tx=0.5, ty=0.6), K(0.3, 6.2, 120, 6, tx=0.5, ty=0.6), K(5, 6.15, 116, 6, tx=0.5, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.3)
    uf = Wp(15, 'frenon') - 0.1
    kf = P.eout4(seg(u, uf, uf + 0.35))
    x = -3.0 + 3.2 * P.eout4(seg(u, -0.2, uf + 0.35))
    cab = 4.0 * math.sin(math.pi * seg(u, uf, uf + 0.6)) * (1 - seg(u, uf + 0.3, uf + 0.6))
    V.carretera(fr, t, vel=1.6 * (1 - kf), a=0.6)
    draw_objects(fr, P.tfk(ev(giro=GIRO(t, 1.6 * (1 - kf)), nivel=0.6, freno=kf), rz=-cab, t=(x, 0, 0)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('¡FRENÓN!', 'sans')], 330, seg(u, uf, uf + 0.12), size=110, col=ROJO)
        pill(img, fx, 540, 1380, 'TAMBIÉN SE DESPERDICIA', eout(seg(u, Wp(15, 'desperdicia') - 0.2, Wp(15, 'desperdicia'))), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uf + 0.15, 0.35), amp=24)


# 18. el motor solo frena hasta cierto punto, lo demás lo hacen las balatas (barra apilada con el límite del motor)
def s_tope(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.6, -60, 18, tx=0.0, ty=0.4), K(0.3, 7.0, -34, 14, ty=0.4), K(5, 6.95, -30, 14, ty=0.4)], cy=0.78))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.3)
    draw_objects(fr, ev(nivel=0.6, bat=0.6, motor=1.0, freno=1.0), xray=0.6, keep=('motor',))

    def ui(img, fx):
        d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        k0 = seg(u, -0.1, 0.2)
        x0, x1, yb, ht = 380, 700, 1150, 800
        d.rectangle((x0, yb - ht, x1, yb), outline=M.scale_c(WHITE, 0.4 * k0), width=3)
        km = seg(u, 0.1, Wp(16, 'punto'))
        hm = ht * 0.38 * km
        d.rectangle((x0 + 6, yb - hm, x1 - 6, yb), fill=M.scale_c(CYAN, k0))
        df.rectangle((x0, yb - hm, x1, yb), fill=M.scale_c(CYAN, 0.35 * k0))
        ylim = yb - ht * 0.38
        for xx in range(x0 - 60, x1 + 60, 34):
            d.line([(xx, ylim), (xx + 18, ylim)], fill=M.scale_c(AMARILLO, k0), width=5)
        texto(img, fx, x1 + 40, ylim, 'LÍMITE', 30, AMARILLO, km, f='mono', glow=0.3, anchor='lm')
        texto(img, fx, x1 + 40, ylim + 44, 'DEL MOTOR', 30, AMARILLO, km, f='mono', glow=0.3, anchor='lm')
        kb = seg(u, Wp(16, 'balatas') - 0.5, Wp(16, 'balatas') + 0.2)
        hb = ht * 0.62 * kb
        if hb > 2:
            d.rectangle((x0 + 6, ylim - hb, x1 - 6, ylim), fill=M.scale_c(ROJO, k0))
            df.rectangle((x0, ylim - hb, x1, ylim), fill=M.scale_c(ROJO, 0.35 * k0))
        texto(img, fx, (x0 + x1) / 2, yb - hm / 2, 'MOTOR', 40, (10, 20, 30), km, f='sansx', glow=0.0)
        texto(img, fx, (x0 + x1) / 2, ylim - hb / 2, 'BALATAS', 44, WHITE, kb, f='sansx', glow=0.2)
        texto(img, fx, (x0 + x1) / 2, yb - ht - 40, 'FRENÓN', 40, WHITE, k0, f='mono', glow=0.2)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. por eso, soltar el acelerador con tiempo es frenar cargando («TIEMPO» de cristal; el carro rueda suave al alto)
def s_tiempo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.0, 40, 10, tx=0.6, ty=0.6), K(0.3, 6.2, 14, 8, tx=0.6, ty=0.6), K(5, 6.15, 10, 8, tx=0.6, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, 'TIEMPO', u, t0=Wp(17, 'tiempo') - 0.3, cy=0.3, entrada='sube')
    kv = seg(u, 0.0, d)
    vel = 1.0 - 0.8 * kv
    V.carretera(fr, t, vel=vel, a=0.6)
    draw_objects(fr, ev(giro=GIRO(t, vel), nivel=0.55 + 0.25 * kv, bat=1.0, motor=1.0), xray=0.85, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=1.0, regen=True, vel=1.2)

    def ui(img, fx):
        semaforo(img, fx, 920, 1200, 1.0, k=seg(u, 0.0, 0.2))
        pill(img, fx, 540, 1380, 'FRENAR CARGANDO', eout(seg(u, Wp(17, 'cargando') - 0.2, Wp(17, 'cargando'))), size=36, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. y en México ya viene el Olinia, un eléctrico de ciudad para 2027 (esquema sin marca con su ficha)
def s_olinia(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 60, 12, ty=0.6), K(0.3, 5.0, 30, 8, ty=0.6), K(5, 4.95, 26, 8, ty=0.6)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.6)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    draw_objects(fr, P.tfk(V.carro(col=VERDE_O, r_ll=0.28), s=0.8, ry=t * 20, t=(0, max(0.0, -e['dy']) * 0.4, 0)))

    def ui(img, fx):
        kicker(img, 'HECHO EN MÉXICO · LLEGA EN 2027', 300, seg(u, Wp(20, 'olinia') - 0.2, Wp(20, 'olinia')), col=VERDE)
        P.titulo_golpe(img, fx, [('Olinia', 'serif')], 350, seg(u, Wp(20, 'olinia') - 0.1, Wp(20, 'olinia') + 0.05), size=110)
        for j, (txt, w) in enumerate((('DESDE 150 MIL PESOS', 'ciudad'), ('+125 KM POR CARGA', 'ciudad'), ('DE CIUDAD', 'ciudad'))):
            pill(img, fx, 540, 1180 + j * 90, txt, eout(seg(u, Wp(20, w) - 0.4 + 0.2 * j, Wp(20, w) - 0.15 + 0.2 * j)), size=30, border=VERDE, dot=False)
        esquema(img, fx, seg(u, 0.2, 0.5), y=1460, txt='ESQUEMA · NO ES EL OLINIA REAL')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(20, 'olinia') + 0.05, 0.25), amp=12)


# 21. justo en la ciudad es donde este truco rinde más (la ciudad de línea y el carro cargando en cada alto)
def s_rinde(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 10.0, 20, 26, tx=0.0, ty=1.0), K(0.3, 8.6, 6, 18, ty=1.0), K(5, 8.55, 4, 18, ty=1.0)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.2)
    edificios(fr, a=0.65, z=-3.5, seed=7)
    edificios(fr, a=0.35, z=-6.0, seed=9)
    V.carretera(fr, t, vel=0.6, a=0.6)
    draw_objects(fr, ev(giro=GIRO(t, 0.6), nivel=0.75, bat=1.0, motor=1.0), xray=0.85, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=1.0, regen=True)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('En la ciudad', 'sans'), ('rinde más.', 'serif')], 300, seg(u, Wp(21, 'ciudad') - 0.1, Wp(21, 'ciudad') + 0.05), size=80)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(21, 'ciudad') + 0.05, 0.25), amp=12)


# 22. mándaselo a quien dice que los eléctricos no sirven en México
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.4, -20, 10, ty=0.6), K(0.3, 5.8, -40, 10, ty=0.6), K(5, 5.75, -44, 10, ty=0.6)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    V.carretera(fr, t, vel=0.8, a=0.6)
    draw_objects(fr, ev(giro=GIRO(t, 0.8), nivel=0.7, bat=1.0, motor=1.0), xray=0.6, keep=('bateria', 'celda', 'motor'))
    flujo(fr, t, k=0.8, regen=True)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien dice', 'sans'), ('que los eléctricos no sirven.', 'serif')], 250, seg(u, 0.05, 0.2), size=58)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55),
                sfx=[(-2.6, 'whoosh_suave', 0.4), (UG - 0.06, 'digital', 0.8), (UG, 'sub', 0.9), (UG + 0.12, 'bass', 0.8), (UG + 0.4, 'shimmer', 0.5)]),
           dict(desde=1, fn=s_suelta, tr='whip_izq', sfx=[(0.0, 'whoosh', 0.6)]),
           dict(desde=2, fn=s_regreso, tr='zoom', c=(0.5, 0.55), sfx=[(0.1, 'scribble', 0.5)]),
           dict(desde=3, fn=s_nombre, tr='cristal', palabra='FRENADO', sfx=[(0.15, 'bass', 0.7), (0.3, 'scribble', 0.5)]),
           dict(desde=4, fn=s_dinamo, tr='iris', c=(0.35, 0.62), sfx=[(0.0, 'whoosh_suave', 0.4)]),
           dict(desde=5, fn=s_bajada, tr='cubo', sfx=[]),
           dict(desde=6, fn=s_balatas, tr='deslizar_abajo', sfx=[(0.0, 'whoosh', 0.5)]),
           dict(desde=7, fn=s_sube, tr='wipe', sfx=[]),
           dict(desde=8, fn=s_imanes, tr='zoom', c=(0.4, 0.58), sfx=[(-0.1, 'cristal', 0.6), (0.2, 'whoosh_suave', 0.4)]),
           dict(desde=9, fn=s_reves, tr='giro', sfx=[(0.3, 'shimmer', 0.4)]),
           dict(desde=10, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.15, 'sub', 0.9), (0.2, 'bass', 0.7)]),
           dict(desde=11, fn=s_cien, tr='flash', sfx=[]),
           dict(desde=12, fn=s_llena, tr='mosaico', sfx=[(0.1, 'thud', 0.8)]),
           dict(desde=13, fn=s_limita, tr='glitch', sfx=[(0.2, 'digital', 0.5)]),
           dict(desde=14, fn=s_fria, tr='deslizar', sfx=[(0.1, 'shimmer', 0.4)]),
           dict(desde=15, fn=s_frenon, tr='golpe', sfx=[]),
           dict(desde=16, fn=s_tope, tr='rebanadas', sfx=[(0.1, 'tick2', 0.4)]),
           dict(desde=17, fn=s_tiempo, tr='remolino', sfx=[(0.0, 'riser', 0.3)]),
           dict(desde=18, fn=s_ciudad, tr='whip_izq', sfx=[(0.1, 'tick', 0.5), (0.7, 'tick2', 0.5), (1.35, 'tick', 0.5), (1.95, 'tick2', 0.5)]),
           dict(desde=19, fn=s_tercio, tr='golpe', sfx=[(0.3, 'chime_a', 0.4), (0.6, 'chime_b', 0.4)]),
           dict(desde=20, fn=s_olinia, tr='cubo_izq', sfx=[]),
           dict(desde=21, fn=s_rinde, tr='push', c=(0.5, 0.5), sfx=[(0.2, 'whoosh_suave', 0.4)]),
           dict(desde=22, fn=s_compa, tr='deslizar_abajo', sfx=[(0.05, 'slap', 0.7)]),
           dict(desde=23, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    add = {1: [(Wp(1, 'acelerador') + 0.1, 'click', 0.9), (Wp(1, 'generador'), 'bass', 0.8)],
           2: [(Wp(2, 'bateria') - 0.1, 'chime_b', 0.5)],
           4: [(Wp(4, 'foco') - 0.15, 'chime_c', 0.5)],
           5: [(Wp(5, 'bajada') + 0.05, 'thud', 0.9)],
           6: [(Wp(6, 'balatas') - 0.1, 'burst', 0.5), (Wp(6, 'calor') - 0.2, 'cristal', 0.6)],
           7: [(Wp(7, 'sube') - 0.3, 'chime_a', 0.5), (Wp(7, 'sube'), 'chime_c', 0.5)],
           9: [(Wp(9, 'reves') - 0.1, 'bass', 0.8)],
           19: [(Wp(19, 'tercio') - 0.3, 'cristal', 0.6), (Wp(19, 'tercio') - 0.1, 'bass', 0.8)],
           11: [(Wp(11, 'cien') - 0.25, 'cristal', 0.6), (Wp(11, 'cien'), 'sub', 0.8)],
           12: [(Wp(12, 'cabe') - 0.1, 'burst', 0.6), (Wp(12, 'cabe'), 'bass', 0.7)],
           13: [(Wp(13, 'limita') - 0.2, 'digital', 0.5), (Wp(13, 'balatas') - 0.3, 'burst', 0.4)],
           14: [(Wp(14, 'manuales') - 0.2, 'slap', 0.8)],
           15: [(Wp(15, 'frenon') - 0.1, 'burst', 0.8), (Wp(15, 'frenon') + 0.15, 'sub', 1.0)],
           16: [(Wp(16, 'punto') - 0.1, 'thud', 0.8), (Wp(16, 'balatas') - 0.3, 'bass', 0.7)],
           17: [(Wp(17, 'tiempo') - 0.3, 'cristal', 0.6), (Wp(17, 'cargando') - 0.2, 'chime_b', 0.5)],
           20: [(Wp(20, 'olinia') + 0.05, 'bass', 0.8), (Wp(20, 'ciudad') - 0.4, 'tick', 0.5)],
           21: [(Wp(21, 'ciudad') + 0.05, 'thud', 0.7)]}
    for e in ESCENAS:
        if e.get('desde') in add and not e.get('loop'):
            e['sfx'] = list(e.get('sfx', [])) + add[e['desde']]


_sfx_dinamicos()


def tiempos_falsos():
    T = [(round(0.25 + 2.9 * i, 2), round(0.25 + 2.9 * i + 2.5, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.55, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    print('ok', T[-1])


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    else:
        montaje.cli(globals())
