"""Reel diario mié 25-nov-2026 10:00 (propuesto) — «Tu acumulador no se murió… se entumió.»
Con frío la reacción química del acumulador de plomo y ácido se hace lenta: a 0 °C pierde ~35 % de su fuerza y a −18 °C
~60 % (AAA), justo cuando el aceite espeso hace que el motor pida hasta el doble de corriente. Error (segundo gancho): al
pasar corriente, poner el último cable negro en la batería descargada (suelta hidrógeno y la última chispa lo puede
encender); va a un tornillo sin pintar del motor, lejos de la batería. Esperar unos minutos, 3 intentos, vida de 3 a 5 años
y manejar ~20 minutos después.
Comunidad: automovilistas. Inicio tipo 12 (cuenta regresiva): el termómetro baja de 25 a 0 °C sobre el acumulador, se
congela con destello y la marcha solo hace «clic»; «ENTUMIDO» de cristal detrás. El final regresa al inicio (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Sin fotos reales: acumulador, carros y motor son esquemas sin marca («ESQUEMA»/«EJEMPLO»).
Datos y fuentes: guiones/2026-11-25_acumulador.txt.
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import texto, esquema, golpe_k, sacudir, K, camara, _B
import velocimetro as V

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
TEMA = 'acumulador'
TXT = ['Tu acumulador no se murió… se entumió.',
       'Adentro hay placas de plomo en ácido:',
       'la corriente sale de una reacción química.',
       'Con frío, esa reacción se hace lenta,',
       'como la miel en el refri.',
       'A 0 °C pierde como 35 % de su fuerza;',
       'a −18 °C, 60 %.',
       'Y justo ahí, el aceite frío está espeso',
       'y el motor pide hasta el doble de corriente.',
       'Misma batería: a 25 °C arranca a la primera;',
       'a 0 °C, solo hace clic.',
       'Y aquí está el error:',
       'pasar corriente y poner el último cable negro en la batería muerta.',
       'Una batería descargada suelta hidrógeno,',
       'y esa última chispa lo puede encender.',
       'El orden es: rojo a la muerta,',
       'rojo a la buena y negro a la buena.',
       'Y el último negro, a un tornillo sin pintar del motor muerto,',
       'lejos de la batería.',
       'Deja prendido el carro bueno unos minutos antes de dar marcha.',
       'Si al tercer intento no prende, ya no da;',
       'un acumulador dura de 3 a 5 años.',
       'Ya que arrancó, manéjalo unos 20 minutos para que se recargue.',
       'Mándaselo a quien pasa corriente a lo ahí se va.',
       'Y que no lo dé por muerto… porque su acumulador no se murió: se entumió.']
VOZ = ['Tu acumulador no se murió... se entumió.',
       'Adentro hay placas de plomo en ácido:',
       'la corriente sale de una reacción química.',
       'Con frío, esa reacción se hace lenta,',
       'como la miel en el refri.',
       'A cero grados pierde como treinta y cinco por ciento de su fuerza;',
       'a dieciocho bajo cero, sesenta.',
       'Y justo ahí, el aceite frío está espeso',
       'y el motor pide hasta el doble de corriente.',
       'Misma batería: a veinticinco grados arranca a la primera;',
       'a cero, solo hace clic.',
       'Y aquí está el error:',
       'pasar corriente y poner el último cable negro en la batería muerta.',
       'Una batería descargada suelta hidrógeno,',
       'y esa última chispa lo puede encender.',
       'El orden es: rojo a la muerta,',
       'rojo a la buena y negro a la buena.',
       'Y el último negro, a un tornillo sin pintar del motor muerto,',
       'lejos de la batería.',
       'Deja prendido el carro bueno unos minutos antes de dar marcha.',
       'Si al tercer intento no prende, ya no da;',
       'un acumulador dura de tres a cinco años.',
       'Ya que arrancó, manéjalo unos veinte minutos para que se recargue.',
       'Mándaselo a quien pasa corriente a lo ahí se va.',
       'Y que no lo dé por muerto... porque su acumulador no se murió: se entumió.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_acumulador.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-25_acumulador_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
ROJO = (235, 50, 45)
AZULC = (150, 210, 230)
HIELO = (190, 230, 255)
GRIS = (150, 150, 160)
VERDE = (90, 220, 140)
MIEL = (235, 160, 40)
PLOMO = (150, 152, 160)
PB_POS = (128, 74, 44)
CAJA_ACU = (34, 36, 40)

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


# ------------------------------------------------------------------ el acumulador (frente hacia +z, bornes arriba)
_ETQ = {}


def etiqueta(estado='ok'):
    if estado not in _ETQ:
        im = Image.new('RGB', (520, 320), (20, 21, 24))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 520, 70), fill=(200, 40, 36) if estado == 'ok' else (70, 70, 76))
        d.text((260, 36), 'ACUMULADOR', font=M.font('mono', 38), fill=(250, 250, 250), anchor='mm')
        d.text((260, 170), '12 V', font=M.font('sansx', 120), fill=(245, 245, 247), anchor='mm')
        d.text((260, 270), 'PLOMO · ÁCIDO', font=M.font('mono', 30), fill=(170, 170, 178), anchor='mm')
        _ETQ[estado] = im.convert('RGBA')
    return _ETQ[estado]


Y_TOP = 0.87          # altura de la tapa
BORNE_P = (-0.45, Y_TOP + 0.1, 0.16)
BORNE_N = (0.45, Y_TOP + 0.1, 0.16)


def acumulador(frio=0.0, interior=True, viejo=0.0, estado='ok'):
    """Acumulador de 12 V semirrealista: caja negra, tapa, bornes de plomo (+ rojo, − negro), tapones y las placas
    por dentro (nombre 'in', para rayos X). frio 0–1 lo escarcha (tinte azul). viejo 0–1 sulfata los bornes."""
    ms = []
    cuerpo = M.mixc(CAJA_ACU, (70, 84, 100), frio * 0.6)
    b = M3.box(1.3, 0.8, 0.72, cuerpo, shadow=0, gloss=0.35)
    M3.decal(b, b.FACE['front'], etiqueta(estado))
    ms.append(named(b, 'caja', rim=0.7, gloss=0.35))
    ms.append(named(M3.box(1.34, 0.07, 0.76, M.mixc((52, 54, 60), (120, 140, 160), frio * 0.6), shadow=0, gloss=0.4).tf(t=(0, 0.8, 0)),
                    'tapa', rim=0.7, gloss=0.4))
    for x in (-0.25, 0.0, 0.25):                                   # tapones de ventilación
        ms.append(named(M3.cyl(0.05, 0.03, (70, 72, 78), n=12, shadow=0, gloss=0.4).tf(t=(x, Y_TOP, -0.18)), 'tapa', rim=0.5))
    for (x, y, z), col in ((BORNE_P, (205, 40, 36)), (BORNE_N, (40, 40, 44))):
        ms.append(named(M3.cyl(0.11, 0.025, col, n=20, shadow=0, gloss=0.5).tf(t=(x, Y_TOP, z)), 'collar', rim=0.6))
        pc = M.mixc(PLOMO, (215, 230, 205), viejo)
        ms.append(named(M3.cyl(0.065, 0.11, pc, n=18, shadow=0, gloss=0.75, r2=0.055).tf(t=(x, Y_TOP + 0.02, z)), 'borne', rim=0.8, gloss=0.75))
    ms.append(named(M3.box(0.7, 0.03, 0.05, (60, 62, 68), shadow=0, gloss=0.3).tf(t=(0, Y_TOP + 0.04, 0.0)), 'asa', rim=0.5))
    if interior:
        for c in range(6):                                          # 6 celdas de 2 V
            x = -0.54 + c * 0.216
            for j in range(5):
                col = PB_POS if j % 2 == 0 else PLOMO
                ms.append(named(M3.box(0.17, 0.58, 0.018, col, shadow=0, gloss=0.4).tf(t=(x, 0.08, -0.24 + j * 0.12)), 'in', rim=0.4, gloss=0.4))
            if c < 5:
                ms.append(named(M3.box(0.03, 0.62, 0.62, (70, 120, 150), shadow=0, gloss=0.2).tf(t=(x + 0.108, 0.06, 0)), 'in', rim=0.2))
        ms.append(named(M3.box(1.15, 0.03, 0.06, PLOMO, shadow=0, gloss=0.6).tf(t=(0, 0.69, 0.16)), 'in', rim=0.5))
    return ms


def escarcha(img, fx, fr, k, seed=3, n=26, caja=(-0.7, 0.0, 0.7, 0.95)):
    """Cristales de hielo (line-art) alrededor del acumulador; k 0–1."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    for j in range(n):
        x3 = rng.uniform(caja[0], caja[2])
        y3 = rng.uniform(caja[1], caja[3])
        x, y, z = fr.cam.p1((x3, y3, 0.38))
        if z < 0.2:
            continue
        r = rng.uniform(7, 16) * min(1.0, k * 1.6 - j / n * 0.6 + 0.4)
        if r <= 1:
            continue
        c = M.scale_c(HIELO, 0.85 * clamp(k * 1.5))
        for a in range(3):
            ang = a * math.pi / 3 + j
            d.line([(x - r * math.cos(ang), y - r * math.sin(ang)), (x + r * math.cos(ang), y + r * math.sin(ang))], fill=c, width=2)
        df.ellipse((x - r, y - r, x + r, y + r), fill=M.scale_c(HIELO, 0.25 * k))


def cable(fr, p0, p1, col, sag=0.35, a=1.0, frac=1.0, w=5.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    pts = []
    for s in np.linspace(0, 1, 24):
        p = p0 + (p1 - p0) * s
        p[1] -= sag * 4 * s * (1 - s)
        pts.append(p)
    line3(fr, pts, col=col, w=w, a=a, glow=0.5, frac=frac)


def pinza(p, col, abierta=0.0):
    """Pinza de cable pasacorriente (dos quijadas) en p."""
    x, y, z = p
    ms = []
    ms.append(named(M3.box(0.08, 0.16, 0.05, col, shadow=0, gloss=0.5).tf(rz=12 + 18 * abierta, t=(x - 0.02, y, z)), 'pinza', rim=0.7, gloss=0.5))
    ms.append(named(M3.box(0.08, 0.16, 0.05, col, shadow=0, gloss=0.5).tf(rz=-12 - 18 * abierta, t=(x + 0.02, y, z)), 'pinza', rim=0.7, gloss=0.5))
    ms.append(named(M3.box(0.05, 0.05, 0.06, (170, 172, 178), shadow=0, gloss=0.9).tf(t=(x, y - 0.03, z)), 'pinza', rim=0.8))
    return ms


def chispa(img, fx, x, y, t, k=1.0, escala=1.0, col=(255, 230, 150)):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    rng = np.random.RandomState(int(t * 24) % 97)
    for j in range(9):
        a = rng.uniform(0, 2 * math.pi)
        L = rng.uniform(30, 90) * escala * k
        pts = [(x, y)]
        for s in range(1, 4):
            pts.append((x + L * s / 3 * math.cos(a) + rng.uniform(-8, 8), y + L * s / 3 * math.sin(a) + rng.uniform(-8, 8)))
        d.line(pts, fill=M.scale_c(col, k), width=3)
        df.line(pts, fill=M.scale_c(col, 0.8 * k), width=9)
    df.ellipse((x - 40 * escala, y - 40 * escala, x + 40 * escala, y + 40 * escala), fill=M.scale_c(col, 0.7 * k))


def motor_bloque(frio=0.0):
    """Bloque de motor (esquema): monoblock gris con cabeza, tapa de punterías y un tornillo de tierra al frente."""
    ms = []
    g = M.mixc((110, 114, 122), (150, 170, 190), frio * 0.5)
    ms.append(named(M3.rbox(1.6, 0.8, 0.9, 0.08, g, n=4, shadow=0, gloss=0.5), 'motor', rim=0.7, gloss=0.5))
    ms.append(named(M3.rbox(1.5, 0.22, 0.7, 0.08, (70, 74, 82), n=4, shadow=0, gloss=0.6).tf(t=(0, 0.8, 0)), 'motor', rim=0.7))
    for j in range(4):
        ms.append(named(M3.cyl(0.07, 0.05, (40, 40, 44), n=12, shadow=0, gloss=0.4).tf(t=(-0.54 + j * 0.36, 1.02, 0.1)), 'motor'))
    ms.append(named(M3.cyl(0.06, 0.08, (190, 192, 198), n=6, shadow=0, gloss=0.95).tf(rx=90, t=(0.45, 0.45, 0.45)), 'tornillo', rim=0.9, gloss=0.95))
    return ms


TORNILLO = (0.45, 0.45, 0.53)


def frasco_miel(nivel=0.75):
    ms = []
    ms.append(named(M3.cyl(0.3, 0.7, (120, 70, 20), n=26, shadow=0, gloss=0.9), 'frasco', rim=0.95, gloss=0.9))
    ms.append(named(M3.cyl(0.27, 0.7 * nivel, MIEL, n=26, shadow=0, gloss=0.7).tf(t=(0, 0.01, 0)), 'miel', rim=0.4, glow=(60, 36, 6)))
    ms.append(named(M3.cyl(0.32, 0.1, (210, 212, 218), n=26, shadow=0, gloss=0.8).tf(t=(0, 0.7, 0)), 'tapa', rim=0.8))
    return ms


def marcha(giro=0.0):
    """Motor de arranque (esquema): cuerpo cilíndrico acostado (eje en x) y piñón con dientes que gira al frente."""
    ms = [named(M3.cyl(0.32, 1.1, (58, 60, 68), n=26, shadow=0, gloss=0.6, y0=-0.55).tf(rz=90, t=(0.1, 0.6, 0)), 'marcha', rim=0.8, gloss=0.6),
          named(M3.cyl(0.22, 0.3, (40, 42, 48), n=20, shadow=0, gloss=0.5, y0=-0.15).tf(rz=90, t=(0.8, 0.6, 0)), 'marcha', rim=0.7),
          named(M3.cyl(0.07, 0.4, (180, 182, 190), n=12, shadow=0, gloss=0.9, y0=-0.2).tf(rz=90, t=(-0.65, 0.6, 0)), 'eje', rim=0.8)]
    for j in range(12):
        a = giro + j * 2 * math.pi / 12
        ms.append(named(M3.box(0.12, 0.06, 0.06, (205, 207, 215), shadow=0, base=False, gloss=0.85)
                        .tf(rx=math.degrees(a), t=(-0.8, 0.6 + 0.16 * math.sin(a), 0.16 * math.cos(a))), 'engrane', rim=0.7))
    ms.append(named(M3.cyl(0.15, 0.12, (170, 172, 180), n=16, shadow=0, gloss=0.85, y0=-0.06).tf(rz=90, t=(-0.8, 0.6, 0)), 'engrane', rim=0.8))
    return ms


def carro_estado(col, faros=1.0, giro=0.0, frio=0.0):
    ms = V.carro(col=M.mixc(col, (150, 175, 200), frio * 0.5), giro_llanta=giro)
    for m in ms:
        g = getattr(m, 'glow', None)
        if g is not None and tuple(g) == (160, 150, 120):
            m.glow = M.scale_c((160, 150, 120), faros)
            m.C = [M.mixc((60, 60, 60), c, faros) for c in m.C]
    return ms


def humo(img, fx, x, y, t, k=1.0, escala=1.0):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    for j in range(5):
        ph = ((t * 1.5) + j / 5) % 1.0
        rr = (8 + 30 * ph) * escala
        xx, yy = x - 120 * ph * escala, y - 40 * ph * escala + 6 * math.sin(t * 5 + j)
        d.ellipse((xx - rr, yy - rr, xx + rr, yy + rr), fill=M.scale_c((150, 150, 158), k * (1 - ph) * 0.6))


def reloj(img, fx, cx, cy, R, frac, k=1.0, col=CYAN, txt=''):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c(WHITE, 0.8 * k), width=5)
    if frac > 0.001:
        d.pieslice((cx - R + 12, cy - R + 12, cx + R - 12, cy + R - 12), -90, -90 + 360 * clamp(frac), fill=M.scale_c(col, 0.45 * k))
        df.pieslice((cx - R + 12, cy - R + 12, cx + R - 12, cy + R - 12), -90, -90 + 360 * clamp(frac), fill=M.scale_c(col, 0.3 * k))
    a = -math.pi / 2 + 2 * math.pi * frac
    d.line([(cx, cy), (cx + (R - 24) * math.cos(a), cy + (R - 24) * math.sin(a))], fill=M.scale_c(WHITE, k), width=7)
    for j in range(12):
        b = j * math.pi / 6
        d.line([(cx + (R - 16) * math.cos(b), cy + (R - 16) * math.sin(b)), (cx + R * math.cos(b), cy + R * math.sin(b))], fill=M.scale_c(WHITE, 0.7 * k), width=3)
    if txt:
        texto(img, fx, cx, cy + R + 60, txt, 54, col, k, f='mono', glow=0.4)


def barras(img, fx, filas, x0, y0, wmax, k=1.0, alto=86, gap=150):
    """filas = [(etiqueta, valor 0–1, color, texto_valor)]; barras horizontales que crecen."""
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    for j, (lab, v, col, tv) in enumerate(filas):
        y = y0 + j * gap
        texto(img, fx, x0, y - 44, lab, 34, GRIS, k, f='mono', glow=0.0, anchor='lm')
        d.rounded_rectangle((x0, y, x0 + wmax, y + alto), radius=14, outline=M.scale_c(WHITE, 0.35 * k), width=3)
        w = wmax * clamp(v)
        if w > 6:
            d.rounded_rectangle((x0, y, x0 + w, y + alto), radius=14, fill=M.scale_c(col, k))
            df.rounded_rectangle((x0, y, x0 + w, y + alto), radius=14, fill=M.scale_c(col, 0.35 * k))
        texto(img, fx, x0 + wmax + 20, y + alto / 2, tv, 52, col, k, f='sansx', glow=0.3, anchor='lm')


def iones(fr, t, x0, x1, y0, y1, z, vel=1.0, k=1.0, col=CYAN, n=22, seed=5):
    """Iones que viajan entre dos placas (puntos que brillan)."""
    rng = np.random.RandomState(seed)
    for j in range(n):
        ph = (rng.rand() + t * 0.35 * vel * (0.7 + 0.6 * rng.rand())) % 1.0
        x = x0 + (x1 - x0) * ph
        y = y0 + (y1 - y0) * rng.rand()
        dot3(fr, (x, y, z), r=5, col=col, a=0.9 * k, glow=1.0)


# ================================================================== escenas
UG = 0.3      # golpe del título (la cuenta llega a 0 °C)


def temp_gancho(u):
    return 25.0 * (1 - seg(u, -3.0, UG))


# 0. gancho, inicio 12 (cuenta regresiva): de 25 a 0 °C sobre el acumulador que se escarcha; clic; «ENTUMIDO» de cristal
def s_gancho(t, fi, u, d):
    fr = Frame(camara(u, [K(-4.0, 4.6, -42, 16, ty=0.45), K(UG, 4.1, -30, 12, ty=0.45), K(UG + 0.6, 3.45, 16, 9, ty=0.47),
                          K(3.2, 3.35, 22, 9, ty=0.47)], cy=0.53))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'ENTUMIDO', u, t0=-2.8, cy=0.33, entrada='golpe')
    tc = temp_gancho(u)
    frio = 1 - tc / 25.0
    x, y = fr.cam.proj([(0, 0.01, 0)])[0][0]
    D.shadow_blob(fr, x, y, 900, 140, 0.7)
    draw_objects(fr, acumulador(frio=frio, interior=False))

    def ui(img, fx):
        escarcha(img, fx, fr, frio, seed=3)
        col = M.mixc(NARANJA, HIELO, frio)
        congelado = u >= UG
        txt = f'{int(round(tc))} °C'
        if congelado and int(t * 8) % 2 == 0:
            col = WHITE
        texto(img, fx, 540, 1350, txt, 150 if not congelado else 170, col, 1.0, f='mono', glow=0.6)
        texto(img, fx, 540, 1455, 'TEMPERATURA · 7:00 AM', 26, GRIS, 1.0, f='mono', glow=0.0)
        if congelado:
            pill(img, fx, 860, 930, '«CLIC»', eout(seg(u, UG + 0.05, UG + 0.25)), size=34, border=ROJO, dot=False)
        kicker(img, 'ACUMULADOR · 12 V', 140, seg(u, UG, UG + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu acumulador no se murió…', 'sans'), ('se entumió.', 'serif')], 190, seg(u, UG, UG + 0.15), size=68)
    fr.ui.append(ui)
    img = finish(fr, fi, flash=0.55 * (1 - seg(u, UG, UG + 0.25)) if u >= UG else 0.0)
    return sacudir(img, t, golpe_k(u, UG + 0.15, 0.35), amp=24)


# 1. adentro hay placas de plomo en ácido (rayos X de golpe: la caja se vuelve de cristal)
def s_placas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.3, 10, 26, ty=0.45), K(0.35, 2.6, -24, 20, ty=0.45), K(5, 2.55, -30, 20, ty=0.45)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.4)
    kx = P.eout4(seg(u, -0.1, 0.35))
    draw_objects(fr, acumulador(frio=0.2), xray=max(0.02, kx), keep=('in',))
    u1, u2 = Wp(1, 'plomo') - 0.05, Wp(1, 'acido') - 0.05

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-0.33, 0.55, -0.1))
        pill(img, fx, x - 60, y - 340, 'PLACAS DE PLOMO', eout(seg(u, u1, u1 + 0.25)), size=32, border=AMARILLO)
        line_k = eout(seg(u, u1 + 0.1, u1 + 0.35))
        if line_k > 0:
            ImageDraw.Draw(img).line([(x - 60, y - 310), (x - 60 + 60 * line_k, y - 310 + 300 * line_k)], fill=AMARILLO, width=3)
        x2, y2, _ = fr.cam.p1((0.4, 0.3, 0.2))
        pill(img, fx, x2 + 40, y2 + 300, 'ÁCIDO', eout(seg(u, u2, u2 + 0.25)), size=32, border=CYAN)
        kicker(img, '6 CELDAS DE 2 V = 12 V', 150, seg(u, 0.2, 0.5), col=AZULC)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. la corriente sale de una reacción química (dos placas gigantes, iones entre ellas y el foco que prende)
def _placas_cerca(fr, t, u, vel, frio=0.0):
    pos = named(M3.box(1.1, 1.9, 0.08, M.mixc(PB_POS, (110, 130, 150), frio * 0.6), shadow=0, gloss=0.4).tf(t=(-0.85, 0.2, 0)), 'pos', rim=0.6)
    neg = named(M3.box(1.1, 1.9, 0.08, M.mixc(PLOMO, (170, 200, 225), frio * 0.6), shadow=0, gloss=0.5).tf(t=(0.85, 0.2, 0)), 'neg', rim=0.6)
    return [pos, neg]


def s_reaccion(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.2, 40, 10, ty=1.2), K(0.3, 4.4, 8, 6, ty=1.2), K(5, 4.3, 2, 6, ty=1.2)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.2, beam=0.3)
    M.cristal(fr.base, fr.fx, 'QUÍMICA', u, t0=-0.1, cy=0.27, entrada='sube')
    draw_objects(fr, _placas_cerca(fr, t, u, 1.0))
    iones(fr, t, -0.3, 0.3, 0.4, 1.9, 0.1, vel=2.2, col=CYAN)
    iones(fr, t + 0.5, 0.3, -0.3, 0.4, 1.9, 0.15, vel=2.2, col=AMARILLO, seed=9)
    # cable de arriba hacia un foco
    kf = seg(u, 0.5, 0.9)
    line3(fr, [(-0.85, 2.15, 0), (-0.85, 2.7, 0), (0.85, 2.7, 0), (0.85, 2.15, 0)], col=WHITE, w=3, a=0.9, glow=0.5)
    for j in range(6):
        ph = (t * 0.8 + j / 6) % 1.0
        dot3(fr, (-0.85 + 1.7 * ph, 2.7, 0), r=4, col=AMARILLO, a=kf, glow=1.0)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0, 2.95, 0))
        r = 36
        ImageDraw.Draw(img).ellipse((x - r, y - r, x + r, y + r), outline=WHITE, width=4)
        ImageDraw.Draw(fx).ellipse((x - r * 2.6 * kf, y - r * 2.6 * kf, x + r * 2.6 * kf, y + r * 2.6 * kf), fill=M.scale_c(AMARILLO, 0.7 * kf))
        ImageDraw.Draw(img).ellipse((x - r + 8, y - r + 8, x + r - 8, y + r - 8), fill=M.scale_c(AMARILLO, kf))
        xp, yp, _ = fr.cam.p1((-0.85, 0.0, 0.1))
        xn, yn, _ = fr.cam.p1((0.85, 0.0, 0.1))
        texto(img, fx, xp, yp + 70, '+', 90, (255, 120, 100), 1.0, glow=0.4)
        texto(img, fx, xn, yn + 70, '−', 90, AZULC, 1.0, glow=0.4)
        pill(img, fx, 540, 1400, 'PLOMO + ÁCIDO → CORRIENTE', eout(seg(u, 0.3, 0.6)), size=30, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. con frío, esa reacción se hace lenta (los mismos iones se frenan; escarcha y termómetro que baja)
def s_lenta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, -30, 14, ty=1.2), K(0.35, 4.6, -6, 10, ty=1.2), K(5, 4.65, -2, 10, ty=1.2)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.0, beam=0.2)
    fk = P.eout4(seg(u, 0.0, 0.8))
    draw_objects(fr, _placas_cerca(fr, t, u, 1.0, frio=fk))
    vel = 2.2 - 1.9 * fk
    tt = 10 + u * vel                               # tiempo «lento»
    iones(fr, tt, -0.3, 0.3, 0.4, 1.9, 0.1, vel=1.0, col=M.mixc(CYAN, HIELO, fk))
    iones(fr, tt + 0.5, 0.3, -0.3, 0.4, 1.9, 0.15, vel=1.0, col=M.mixc(AMARILLO, HIELO, fk), seed=9)

    def ui(img, fx):
        escarcha(img, fx, fr, fk, seed=8, n=34, caja=(-1.4, 0.2, 1.4, 2.1))
        P.termometro(img, fx, 140, 1240, 420, 0.8 - 0.65 * fk, f'{int(round(25 - 25 * fk))}°', k=1.0, col=M.mixc(NARANJA, HIELO, fk))
        pill(img, fx, 640, 1400, 'REACCIÓN LENTA', eout(seg(u, 0.4, 0.7)), size=34, border=HIELO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. como la miel en el refri (frasco que cae en el refri de line-art; la miel cuelga y casi no baja)
def s_miel(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 30, 18, ty=0.8), K(0.3, 3.1, 4, 10, ty=0.8), K(5, 3.0, -2, 10, ty=0.8)], cy=0.57))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.3)
    # el refri: caja de alambre que brilla
    W_, H_, Dp = 1.2, 1.9, 0.9
    for (a, b) in [((-W_, 0, -Dp), (W_, 0, -Dp)), ((W_, 0, -Dp), (W_, H_, -Dp)), ((W_, H_, -Dp), (-W_, H_, -Dp)), ((-W_, H_, -Dp), (-W_, 0, -Dp)),
                   ((-W_, 0, Dp), (-W_, H_, Dp)), ((W_, 0, Dp), (W_, H_, Dp)), ((-W_, H_, Dp), (W_, H_, Dp)),
                   ((-W_, 0, -Dp), (-W_, 0, Dp)), ((W_, 0, -Dp), (W_, 0, Dp)), ((-W_, H_, -Dp), (-W_, H_, Dp)), ((W_, H_, -Dp), (W_, H_, Dp))]:
        line3(fr, [a, b], col=HIELO, w=2.2, a=0.7, glow=0.5)
    line3(fr, [(-W_, 1.0, -Dp), (W_, 1.0, -Dp), (W_, 1.0, Dp), (-W_, 1.0, Dp), (-W_, 1.0, -Dp)], col=HIELO, w=2, a=0.5, glow=0.4)
    e = P.entrada(u, -0.15, 0.35, 'cae')
    draw_objects(fr, P.tfk(frasco_miel(), s=0.9, t=(-0.1, 1.02 + max(0.0, -e['dy']) * 0.5, 0)))
    # la cuchara y el hilo de miel que casi no baja
    yb = 1.02 + 0.72
    gota = 0.15 + 0.12 * ease(seg(u, 0.3, 3.0))
    line3(fr, [(0.25, yb + 0.55, 0.1), (0.05, yb + 0.35, 0.1)], col=(210, 212, 218), w=6, a=0.95, glow=0.3)
    line3(fr, [(0.05, yb + 0.35, 0.1), (0.05, yb + 0.35 - gota, 0.1)], col=MIEL, w=7, a=1.0, glow=0.8)
    dot3(fr, (0.05, yb + 0.35 - gota, 0.1), r=10, col=MIEL, a=1.0, glow=1.0)

    def ui(img, fx):
        kicker(img, 'EN FRÍO TODO SE HACE LENTO', 150, seg(u, 0.1, 0.4), col=AZULC)
        pill(img, fx, 780, 1350, '4 °C', eout(seg(u, 0.2, 0.45)), size=40, border=HIELO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


# 5. a 0 °C pierde como 35 % de su fuerza (barras: 25 °C contra 0 °C; «−35 %» golpea)
def s_35(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -30, 30), K(0.3, 4.4, 0, 22), K(5, 4.3, 4, 22)]))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.3)
    u1 = Wp(5, 'treinta') - 0.1
    v0 = 1.0 - 0.35 * P.eout4(seg(u, u1, u1 + 0.5))

    def ui(img, fx):
        kicker(img, 'FUERZA DEL ACUMULADOR', 380, 1.0, col=AZULC)
        barras(img, fx, [('25 °C', 1.0, NARANJA, '100 %'), ('0 °C', v0, HIELO, f'{int(round(v0 * 100))} %')], 120, 640, 640)
        if u > u1:
            P.numero_golpe(img, fx, '−35 %', 1150, seg(u, u1 + 0.2, u1 + 0.38), size=210, col=HIELO)
        texto(img, fx, 540, 1430, 'FUENTE: AAA', 24, GRIS, 1.0, f='mono', glow=0.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u1 + 0.38, 0.3), amp=16)


# 6. a −18 °C, 60 % (la tercera barra cae a 40 %; «−60 %» de cristal detrás)
def s_60(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, 30, 26), K(0.3, 4.6, 6, 20), K(5, 4.7, 2, 20)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, '−60 %', u, t0=-0.05, cy=0.27, entrada='zoom')
    v = 1.0 - 0.6 * P.eout4(seg(u, 0.1, 0.7))

    def ui(img, fx):
        barras(img, fx, [('25 °C', 1.0, NARANJA, '100 %'), ('0 °C', 0.65, HIELO, '65 %'),
                         ('−18 °C', v, (120, 170, 255), f'{int(round(v * 100))} %')], 120, 860, 640, gap=170)
        escarcha(img, fx, fr, seg(u, 0.4, 1.2), seed=12, n=18, caja=(-2.0, 0.0, 2.0, 1.0))
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. y justo ahí, el aceite frío está espeso (motor con la varilla del aceite; la gota cuelga espesa)
def s_aceite(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, -60, 20, ty=0.7), K(0.35, 3.6, -20, 14, ty=0.75), K(5, 3.5, -14, 14, ty=0.75)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.45)
    e = P.entrada(u, -0.2, 0.3, 'pop')
    draw_objects(fr, P.tfk(motor_bloque(frio=0.6), s=max(0.05, e['escala'])))
    ks = P.eout4(seg(u, 0.1, 0.6))
    ys = 1.05 + 0.9 * ks
    line3(fr, [(-0.6, 1.05, 0.3), (-0.6, ys, 0.3)], col=(220, 200, 120), w=4, a=1.0, glow=0.4)
    line3(fr, [(-0.6, ys, 0.3), (-0.6, ys + 0.12, 0.3)], col=(220, 200, 120), w=10, a=1.0, glow=0.4)
    gota = 0.05 + 0.18 * ease(seg(u, 0.6, 3.0))
    line3(fr, [(-0.6, 1.25, 0.3), (-0.6, 1.25 - gota, 0.3)], col=(200, 140, 30), w=12, a=1.0, glow=0.9)
    dot3(fr, (-0.6, 1.25 - gota, 0.3), r=14, col=(200, 140, 30), a=1.0, glow=1.0)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-0.6, 1.25 - gota, 0.3))
        pill(img, fx, x + 200, y + 40, 'ACEITE ESPESO', eout(seg(u, 0.5, 0.8)), size=32, border=(230, 170, 60))
        doodle_circle(img, fx, x, y, 70, 90, t, k=seg(u, 0.9, 1.3), col=WHITE, seed=4)
        kicker(img, 'MOTOR EN FRÍO', 150, seg(u, 0.1, 0.4), col=AZULC)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. y el motor pide hasta el doble de corriente (la marcha gira forzada; «×2» golpea)
def s_doble(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 50, 14, ty=0.6), K(0.3, 4.0, 24, 10, ty=0.6), K(5, 3.95, 20, 10, ty=0.6)], cy=0.47))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.4)
    draw_objects(fr, marcha(giro=t * 3.0 + 0.4 * math.sin(t * 20)))
    u1 = Wp(8, 'doble') - 0.1

    def ui(img, fx):
        kicker(img, 'MOTOR DE ARRANQUE (MARCHA)', 150, seg(u, 0.0, 0.3), col=AZULC)
        barras(img, fx, [('CON CALOR', 0.45, NARANJA, '×1'), ('CON FRÍO', 0.45 + 0.45 * P.eout4(seg(u, u1, u1 + 0.4)), ROJO, '×2')], 120, 1230, 640, alto=56, gap=115)
        if u > u1:
            P.numero_golpe(img, fx, '×2', 420, seg(u, u1, u1 + 0.18), size=240, col=ROJO)
        esquema(img, fx, 1.0, y=1440, txt='HASTA EL DOBLE DE CORRIENTE · AAA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u1 + 0.18, 0.3), amp=18)


# 9. misma batería: a 25 °C arranca a la primera (el carro prende: faros y humo)
def s_25(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 40, 10, ty=0.6), K(0.3, 5.0, 24, 8, ty=0.6), K(5, 4.9, 20, 8, ty=0.6)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.15, 0.3, 'desliza')
    vib = 0.01 * math.sin(t * 60) if u > 0.5 else 0.0
    draw_objects(fr, P.tfk(carro_estado((160, 36, 40), faros=seg(u, 0.4, 0.6)), t=(-e['dy'], vib, 0)))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-1.55, 0.35, 0.3))
        humo(img, fx, x, y, t, k=seg(u, 0.5, 0.8))
        texto(img, fx, 540, 420, '25 °C', 150, NARANJA, 1.0, f='mono', glow=0.5)
        pill(img, fx, 540, 1350, '✓ A LA PRIMERA', eout(seg(u, 0.6, 0.85)), size=40, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. a 0 °C, solo hace clic (el mismo carro escarchado: la llave gira, «CLIC» y los faros se apagan)
def s_clic(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.2, -20, 14, ty=0.6), K(0.3, 4.8, 18, 8, ty=0.6), K(5, 4.85, 22, 8, ty=0.6)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.3)
    uc = Wp(10, 'clic') - 0.05
    parp = 0.5 + 0.5 * math.sin(t * 30) if uc - 0.2 < u < uc + 0.25 else (0.0 if u > uc else 0.15)
    draw_objects(fr, carro_estado((160, 36, 40), faros=parp, frio=1.0))

    def ui(img, fx):
        escarcha(img, fx, fr, 1.0, seed=21, n=30, caja=(-1.6, 0.1, 1.6, 1.3))
        texto(img, fx, 540, 420, '0 °C', 150, HIELO, 1.0, f='mono', glow=0.5)
        if u > uc:
            P.numero_golpe(img, fx, '«CLIC»', 1300, seg(u, uc, uc + 0.16), size=150, col=ROJO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.16, 0.3), amp=20)


# --------- pasar corriente: dos acumuladores en la mesa (descargado a la izquierda, bueno a la derecha)
XA, XB = -0.62, 0.62
SB = 0.5          # escala de las dos baterías


def dos_baterias(fr, frio=0.6):
    draw_objects(fr, P.tfk(acumulador(frio=frio, interior=False, estado='muerta'), s=SB, t=(XA, 0, 0)) +
                 P.tfk(acumulador(interior=False), s=SB, t=(XB, 0, 0)))


def borne(x, signo):
    b = BORNE_P if signo > 0 else BORNE_N
    return (x + b[0] * SB, b[1] * SB + 0.04, b[2] * SB)


def etiquetas_baterias(img, fx, fr, k=1.0):
    for x, txt, col in ((XA, 'DESCARGADA', HIELO), (XB, 'BUENA', VERDE)):
        xx, yy, _ = fr.cam.p1((x, 0.0, 0.3))
        pill(img, fx, xx, yy + 60, txt, k, size=26, border=col, dot=False)


# 11. y aquí está el error (alarma roja sobre las dos baterías)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.6, 0, 50, ty=0.4), K(0.3, 3.2, -12, 30, ty=0.4), K(5, 3.25, -16, 30, ty=0.4)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.3)
    dos_baterias(fr)
    rojo = 0.5 + 0.5 * math.sin(t * 14)

    def ui(img, fx):
        etiquetas_baterias(img, fx, fr)
        ImageDraw.Draw(fx).rectangle((0, 0, 1080, 1920), outline=M.scale_c(ROJO, 0.6 * rojo), width=40)
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 260, seg(u, 0.0, 0.15), size=110, col=(255, 110, 100))
        kicker(img, 'AL PASAR CORRIENTE', 200, seg(u, 0.15, 0.4), col=(255, 140, 130))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.35), amp=22)


# 12. pasar corriente y poner el último cable negro en la batería muerta (la pinza baja al borne negativo: ✗)
def s_cable(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 20, 40, ty=0.45), K(0.35, 2.8, -8, 28, ty=0.5), K(1.9, 2.8, -8, 28, ty=0.5), K(2.3, 2.3, -34, 30, ty=0.5, tx=-0.4), K(6, 2.25, -38, 30, ty=0.5, tx=-0.4)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.3)
    dos_baterias(fr)
    cable(fr, borne(XA, 1), borne(XB, 1), (230, 50, 45), sag=0.3)
    cable(fr, borne(XB, -1), (0.2, 0.9, 0.25), (60, 60, 66), sag=0.25)
    un = Wp(12, 'ultimo') - 0.1
    k = P.eout4(seg(u, un, un + 1.0))
    p_end = np.array((0.2, 0.9, 0.25)) + (np.array(borne(XA, -1)) + np.array((0, 0.08, 0)) - np.array((0.2, 0.9, 0.25))) * k
    cable(fr, (0.2, 0.9, 0.25), p_end, (60, 60, 66), sag=0.05)
    draw_objects(fr, pinza(borne(XA, 1), (210, 40, 36)) + pinza(borne(XB, 1), (210, 40, 36)) + pinza(borne(XB, -1), (40, 40, 44)) +
                 pinza(tuple(p_end), (40, 40, 44), abierta=1 - k))

    def ui(img, fx):
        etiquetas_baterias(img, fx, fr)
        x, y, _ = fr.cam.p1(borne(XA, -1))
        if k > 0.9:
            doodle_circle(img, fx, x, y, 80, 80, t, k=seg(u, un + 1.0, un + 1.3), col=ROJO, seed=6)
            texto(img, fx, x, y - 150, '✗', 130, ROJO, seg(u, un + 1.0, un + 1.15), f='sansx', glow=0.7)
        kicker(img, 'EL ÚLTIMO CABLE NEGRO', 150, seg(u, un - 0.2, un + 0.1), col=(255, 140, 130))
        esquema(img, fx, 1.0, y=1440, txt='ASÍ NO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. una batería descargada suelta hidrógeno (burbujas H–H que suben de los tapones; «HIDRÓGENO» de cristal)
def s_hidrogeno(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.3, 30, 30, ty=0.9), K(0.35, 2.9, 6, 18, ty=1.0), K(5, 2.95, 2, 18, ty=1.0)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.35)
    M.cristal(fr.base, fr.fx, 'HIDRÓGENO', u, t0=0.0, cy=0.28, entrada='zoom')
    draw_objects(fr, acumulador(frio=0.5, interior=False, estado='muerta'))
    rng = np.random.RandomState(4)
    for j in range(14):
        x0 = rng.choice([-0.25, 0.0, 0.25]) + rng.uniform(-0.05, 0.05)
        ph = (rng.rand() + t * 0.45) % 1.0
        y = Y_TOP + 0.05 + 1.5 * ph
        x = x0 + 0.08 * math.sin(t * 2 + j)
        a = seg(u, -0.1, 0.3) * (1 - ph)
        dot3(fr, (x - 0.05, y, -0.18), r=9, col=(200, 240, 255), a=a, glow=1.0)
        dot3(fr, (x + 0.05, y, -0.18), r=9, col=(200, 240, 255), a=a, glow=1.0)
        line3(fr, [(x - 0.05, y, -0.18), (x + 0.05, y, -0.18)], col=(200, 240, 255), w=3, a=a, glow=0.6)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0.0, Y_TOP + 0.9, -0.18))
        pill(img, fx, x + 250, y, 'H₂ · GAS QUE EXPLOTA', eout(seg(u, 0.5, 0.8)), size=30, border=(200, 240, 255))
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. y esa última chispa lo puede encender (la pinza toca el borne: chispa y flamazo naranja)
def s_chispa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.8, -30, 24, ty=0.8, tx=0.3), K(0.25, 2.3, -8, 16, ty=0.85, tx=0.3), K(5, 2.25, -4, 16, ty=0.85, tx=0.3)], cy=0.47))
    space(fr, t, floor=None, bokeh=1.0, beam=0.2)
    draw_objects(fr, acumulador(frio=0.4, interior=False, estado='muerta') + pinza((BORNE_N[0], BORNE_N[1] + 0.08, BORNE_N[2]), (40, 40, 44)))
    cable(fr, (BORNE_N[0], BORNE_N[1] + 0.12, BORNE_N[2]), (1.6, 1.4, 0.5), (60, 60, 66), sag=0.1, w=7)
    us = Wp(14, 'chispa') - 0.05

    def ui(img, fx):
        x, y, _ = fr.cam.p1((BORNE_N[0], BORNE_N[1] + 0.02, BORNE_N[2]))
        if u > us:
            chispa(img, fx, x, y, t, k=1 - seg(u, us + 0.3, us + 1.2) * 0.6, escala=1.6)
            kb = seg(u, us + 0.15, us + 0.5)
            if kb > 0:
                r = 380 * P.eout4(kb)
                ImageDraw.Draw(fx).ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=M.scale_c((255, 130, 40), 0.8 * (1 - kb * 0.7)))
        pill(img, fx, 540, 1360, 'CHISPA + HIDRÓGENO = PELIGRO', eout(seg(u, us + 0.5, us + 0.8)), size=30, border=ROJO, dot=False)
        esquema(img, fx, 1.0, y=1440, txt='RECREACIÓN')
    fr.ui.append(ui)
    img = finish(fr, fi, flash=0.5 * (1 - seg(u, us + 0.15, us + 0.5)) if u > us + 0.15 else 0.0)
    return sacudir(img, t, golpe_k(u, us + 0.15, 0.4), amp=26)


# 15–16. el orden: pasos que se numeran y cables que se conectan
def _num(img, fx, fr, n_, p, col, k):
    if k <= 0:
        return
    x, y, _ = fr.cam.p1(p)
    texto(img, fx, x, y - 160, n_, int(80 + 60 * (1 - P.eout4(k))), col, k, f='sansx', glow=0.6)


def s_orden1(t, fi, u, d):
    u1 = Wp(15, 'rojo') - 0.05
    fr = Frame(camara(u, [K(-0.3, 3.8, 30, 42, ty=0.5), K(0.3, 3.0, 10, 30, ty=0.5), K(5, 2.95, 6, 30, ty=0.5)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.3)
    dos_baterias(fr, frio=0.3)
    k1 = P.eout4(seg(u, u1 - 0.3, u1 + 0.15))
    suelto = np.array((-0.1, 1.15, 0.7))
    pa = np.array(borne(XA, 1)) + np.array((0, 0.08, 0))
    p = suelto + (pa - suelto) * k1
    cable(fr, (0.3, 0.6, 0.9), tuple(p), (230, 50, 45), sag=0.1)
    draw_objects(fr, pinza(tuple(p), (210, 40, 36), abierta=1 - k1))

    def ui(img, fx):
        etiquetas_baterias(img, fx, fr)
        kicker(img, 'EL ORDEN · PASO 1', 150, 1.0, col=AZULC)
        _num(img, fx, fr, '1', borne(XA, 1), (255, 110, 100), seg(u, u1, u1 + 0.16))
        pill(img, fx, 540, 1360, 'ROJO → + DE LA DESCARGADA', eout(seg(u, u1 + 0.2, u1 + 0.5)), size=28, border=(255, 110, 100), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u1 + 0.16, 0.25), amp=12)


def s_orden2(t, fi, u, d):
    u2, u3 = Wp(16, 'rojo') - 0.05, Wp(16, 'negro') - 0.05
    fr = Frame(camara(u, [K(-0.3, 2.7, -30, 30, ty=0.5), K(0.3, 3.1, -10, 32, ty=0.5), K(5, 3.15, -6, 32, ty=0.5)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.3)
    dos_baterias(fr, frio=0.3)
    pa, pb, pn = (np.array(borne(x, s)) + np.array((0, 0.08, 0)) for x, s in ((XA, 1), (XB, 1), (XB, -1)))
    k2 = P.eout4(seg(u, u2 - 0.4, u2 + 0.1))
    p2 = pa + (pb - pa) * k2
    cable(fr, tuple(pa), tuple(p2), (230, 50, 45), sag=0.3 * k2)
    ms = pinza(tuple(pa), (210, 40, 36)) + pinza(tuple(p2), (210, 40, 36), abierta=1 - k2)
    k3 = P.eout4(seg(u, u3 - 0.4, u3 + 0.1))
    suelto = np.array((1.9, 1.2, 0.7))
    p3 = suelto + (pn - suelto) * k3
    cable(fr, (2.2, 0.6, 0.9), tuple(p3), (60, 60, 66), sag=0.08)
    ms += pinza(tuple(p3), (40, 40, 44), abierta=1 - k3)
    draw_objects(fr, ms)

    def ui(img, fx):
        etiquetas_baterias(img, fx, fr)
        kicker(img, 'PASOS 2 Y 3', 150, 1.0, col=AZULC)
        _num(img, fx, fr, '1', borne(XA, 1), (255, 110, 100), 1.0)
        _num(img, fx, fr, '2', borne(XB, 1), (255, 110, 100), seg(u, u2, u2 + 0.16))
        _num(img, fx, fr, '3', borne(XB, -1), WHITE, seg(u, u3, u3 + 0.16))
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. y el último negro, a un tornillo sin pintar del motor muerto (la pinza muerde el tornillo)
def s_tornillo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 50, 20, ty=0.55), K(0.35, 3.3, 22, 12, ty=0.55, tx=0.3), K(5, 3.25, 18, 12, ty=0.55, tx=0.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.45)
    k = P.eout4(seg(u, 0.3, 1.1))
    p0 = np.array((1.6, 1.4, 0.9))
    p = p0 + (np.array((TORNILLO[0], TORNILLO[1] + 0.04, TORNILLO[2] + 0.06)) - p0) * k
    cable(fr, tuple(p0), tuple(p), (60, 60, 66), sag=0.05, w=7)
    draw_objects(fr, motor_bloque(frio=0.3) + pinza(tuple(p), (40, 40, 44), abierta=1 - k))

    def ui(img, fx):
        x, y, _ = fr.cam.p1(TORNILLO)
        doodle_circle(img, fx, x, y, 90, 90, t, k=seg(u, 1.0, 1.4), col=VERDE, seed=9)
        pill(img, fx, x - 120, y + 180, 'METAL SIN PINTAR', eout(seg(u, 0.9, 1.2)), size=32, border=VERDE)
        texto(img, fx, x, y - 170, '4', 130, WHITE, seg(u, 1.0, 1.16), f='sansx', glow=0.6)
        kicker(img, 'MOTOR DEL CARRO DESCARGADO', 150, seg(u, 0.0, 0.3), col=AZULC)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 1.1, 0.25), amp=12)


# 18. lejos de la batería (vista desde arriba: cota cian entre el tornillo y la batería; chispa chiquita y segura)
def s_lejos(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.6, -20, 60, ty=0.4, tx=0.35), K(0.3, 5.4, 0, 48, ty=0.4, tx=0.35), K(5, 5.35, 4, 48, ty=0.4, tx=0.35)], cy=0.52))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.3)
    draw_objects(fr, P.tfk(acumulador(frio=0.3, interior=False, estado='muerta'), s=0.7, t=(-0.75, 0, 0)) + P.tfk(motor_bloque(), t=(1.3, 0, -0.2)))
    pa = np.array((-0.75 + BORNE_N[0] * 0.7, 0.75, 0.6))
    pb = np.array((1.3 + TORNILLO[0], 0.75, 0.6))
    kc = P.eout4(seg(u, 0.2, 0.7))
    line3(fr, [pa, pa + (pb - pa) * kc], col=CYAN, w=3, a=1.0, glow=0.8)
    dot3(fr, tuple(pa), r=8, col=CYAN)
    if kc > 0.95:
        dot3(fr, tuple(pb), r=8, col=CYAN)

    def ui(img, fx):
        xm, ym, _ = fr.cam.p1(tuple((pa + pb) / 2))
        pill(img, fx, xm, ym - 70, 'LEJOS', eout(seg(u, 0.6, 0.9)), size=40, border=CYAN)
        x, y, _ = fr.cam.p1((1.3 + TORNILLO[0], TORNILLO[1], TORNILLO[2] - 0.2))
        chispa(img, fx, x, y, t, k=seg(u, 0.9, 1.0) * (1 - seg(u, 1.3, 1.7)), escala=0.5)
        pill(img, fx, 540, 1360, '✓ LA CHISPA QUEDA LEJOS DEL GAS', eout(seg(u, 1.0, 1.3)), size=30, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. deja prendido el carro bueno unos minutos antes de dar marcha (carro bueno con humo y el reloj que corre)
def s_minutos(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.4, -40, 12, ty=0.7), K(0.3, 6.0, -20, 10, ty=0.9), K(2.2, 6.0, -20, 10, ty=0.9), K(2.6, 5.0, -52, 8, ty=0.8), K(5, 4.95, -56, 8, ty=0.8)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    vib = 0.01 * math.sin(t * 60)
    draw_objects(fr, P.tfk(carro_estado((60, 90, 150), faros=1.0), t=(0, vib, 0)))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-1.55, 0.35, 0.3))
        humo(img, fx, x, y, t, k=1.0)
        reloj(img, fx, 540, 520, 170, ease(seg(u, 0.1, d - 0.4)) * 0.8, k=eout(seg(u, -0.2, 0.1)), txt='3 A 5 MIN')
        pill(img, fx, 540, 1350, 'CARRO BUENO · PRENDIDO', 1.0, size=28, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. si al tercer intento no prende, ya no da (tres llaves que giran: ✗ ✗ ✗)
def s_tercer(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.5, 20, 20, ty=0.45), K(0.3, 2.9, -6, 14, ty=0.45), K(5, 2.85, -10, 14, ty=0.45)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.35)
    draw_objects(fr, P.tfk(acumulador(frio=0.8, interior=False, estado='muerta'), s=0.85))
    ut = Wp(20, 'tercer') - 0.1
    us = [max(-0.1, ut - 0.8), max(0.2, ut - 0.4), ut]

    def ui(img, fx):
        escarcha(img, fx, fr, 0.8, seed=31, caja=(-0.6, 0.0, 0.6, 0.8))
        for j, uu in enumerate(us):
            x = 240 + j * 300
            k = seg(u, uu, uu + 0.15)
            texto(img, fx, x, 360, f'{j + 1}.º', 60, WHITE, eout(seg(u, uu - 0.15, uu)), f='mono', glow=0.2)
            if k > 0:
                texto(img, fx, x, 500, '✗', int(110 + 80 * (1 - P.eout4(k))), ROJO, k, f='sansx', glow=0.6)
        pill(img, fx, 540, 1350, 'YA NO DA: TOCA CAMBIARLO', eout(seg(u, ut + 0.6, ut + 0.9)), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut + 0.15, 0.3), amp=16)


# 21. un acumulador dura de 3 a 5 años (bornes sulfatados y el contador de años)
def s_anios(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.5, -40, 26, ty=0.6), K(0.3, 2.9, -14, 18, ty=0.6), K(5, 2.95, -10, 18, ty=0.6)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    kv = ease(seg(u, 0.2, 1.4))
    draw_objects(fr, acumulador(interior=False, viejo=kv, estado='ok' if kv < 0.5 else 'muerta'))
    rng = np.random.RandomState(2)
    for b in (BORNE_P, BORNE_N):
        for j in range(10):
            dot3(fr, (b[0] + rng.uniform(-0.09, 0.09), b[1] - 0.05 + rng.uniform(0, 0.08), b[2] + rng.uniform(-0.09, 0.09)),
                 r=4 + 4 * rng.rand(), col=(215, 235, 205), a=kv, glow=0.3)

    def ui(img, fx):
        n = 3 + 2 * P.eout4(seg(u, 0.0, 1.0))
        P.numero_golpe(img, fx, f'{int(n)} AÑOS' if u < 1.0 else '3 A 5 AÑOS', 470, seg(u, -0.2, 0.0) if u < 1.0 else seg(u, 1.0, 1.16), size=150, col=AMARILLO)
        pill(img, fx, 540, 1350, 'VIDA PROMEDIO · AAA', eout(seg(u, 0.4, 0.7)), size=28, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 22. ya que arrancó, manéjalo unos 20 minutos para que se recargue (carretera y la pila que se llena)
def s_recarga(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 70, 22, ty=0.6), K(0.3, 5.2, 40, 16, ty=0.6), K(5, 5.1, 36, 16, ty=0.6)], cy=0.6))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)
    V.carretera(fr, t, vel=1.2, a=0.9)
    draw_objects(fr, carro_estado((160, 36, 40), faros=1.0, giro=-t * 10))
    kc = ease(seg(u, 0.2, d - 0.3))

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        x0, y0, w, h = 340, 360, 400, 170
        d_.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=20, outline=WHITE, width=6)
        d_.rectangle((x0 + w, y0 + 50, x0 + w + 24, y0 + h - 50), fill=WHITE)
        ww = (w - 24) * (0.15 + 0.85 * kc)
        col = M.mixc(ROJO, VERDE, kc)
        d_.rounded_rectangle((x0 + 12, y0 + 12, x0 + 12 + ww, y0 + h - 12), radius=12, fill=col)
        df.rounded_rectangle((x0 + 12, y0 + 12, x0 + 12 + ww, y0 + h - 12), radius=12, fill=M.scale_c(col, 0.4))
        texto(img, fx, 540, 640, f'{int(round(20 * kc))} MIN', 90, WHITE, 1.0, f='mono', glow=0.4)
        pill(img, fx, 540, 1350, 'SE RECARGA MANEJANDO', eout(seg(u, 0.3, 0.6)), size=30, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. mándaselo a quien pasa corriente a lo ahí se va (los cables cruzados y el título)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.8, -24, 36, ty=0.45), K(0.3, 3.1, 0, 28, ty=0.45), K(5, 3.05, 4, 28, ty=0.45)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    dos_baterias(fr, frio=0.4)
    cable(fr, borne(XA, 1), borne(XB, -1), (230, 50, 45), sag=0.35)
    cable(fr, borne(XA, -1), borne(XB, 1), (60, 60, 66), sag=0.45)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien', 'sans'), ('pasa corriente a lo ahí se va.', 'serif')], 230, seg(u, 0.05, 0.2), size=66)
        x, y, _ = fr.cam.p1((0, 0.9, 0.1))
        texto(img, fx, x, y, '?', 140, ROJO, seg(u, 0.4, 0.55), f='sansx', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55),
                sfx=[(-2.8, 'cristal', 0.5), (-2.0, 'tick', 0.4), (-1.0, 'tick', 0.4), (-0.25, 'tick', 0.5), (UG, 'click', 1.0),
                     (UG, 'sub', 0.9), (UG + 0.15, 'bass', 0.8)]),
           dict(desde=1, fn=s_placas, tr='zoom', sfx=[(0.1, 'shimmer', 0.5), (0.6, 'tick', 0.4)]),
           dict(desde=2, fn=s_reaccion, tr='iris', c=(0.5, 0.5), sfx=[(0.5, 'chime_a', 0.4)]),
           dict(desde=3, fn=s_lenta, tr='remolino', sfx=[(0.3, 'whoosh_suave', 0.5)]),
           dict(desde=4, fn=s_miel, tr='deslizar', sfx=[(0.2, 'thud', 0.8)]),
           dict(desde=5, fn=s_35, tr='golpe', sfx=[]),
           dict(desde=6, fn=s_60, tr='mosaico', sfx=[(0.3, 'chime_b', 0.4)]),
           dict(desde=7, fn=s_aceite, tr='cubo', sfx=[(0.1, 'whoosh', 0.5), (0.9, 'scribble', 0.5)]),
           dict(desde=8, fn=s_doble, tr='push', c=(0.5, 0.5), sfx=[]),
           dict(desde=9, fn=s_25, tr='whip', sfx=[(0.5, 'bass', 0.6), (0.65, 'chime_c', 0.4)]),
           dict(desde=10, fn=s_clic, tr='glitch', sfx=[]),
           dict(desde=11, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.15, 'sub', 0.9), (0.2, 'bass', 0.7)]),
           dict(desde=12, fn=s_cable, tr='deslizar_abajo', sfx=[]),
           dict(desde=13, fn=s_hidrogeno, tr='iris', c=(0.5, 0.42), sfx=[(0.2 + 0.2 * j, 'tick2', 0.3) for j in range(6)]),
           dict(desde=14, fn=s_chispa, tr='flash', sfx=[]),
           dict(desde=15, fn=s_orden1, tr='rebanadas', sfx=[]),
           dict(desde=16, fn=s_orden2, tr='giro', sfx=[]),
           dict(desde=17, fn=s_tornillo, tr='zoom', c=(0.62, 0.55), sfx=[(1.1, 'click', 0.8), (1.0, 'scribble', 0.4)]),
           dict(desde=18, fn=s_lejos, tr='wipe', sfx=[(0.3, 'whoosh_suave', 0.4), (1.0, 'chime_a', 0.4)]),
           dict(desde=19, fn=s_minutos, tr='cubo_izq', sfx=[(0.3 + 0.4 * j, 'tick', 0.3) for j in range(5)]),
           dict(desde=20, fn=s_tercer, tr='glitch', c=(0.5, 0.5), sfx=[]),
           dict(desde=21, fn=s_anios, tr='cristal', palabra='AÑOS', sfx=[(1.0, 'bass', 0.6)]),
           dict(desde=22, fn=s_recarga, tr='deslizar', sfx=[(1.0, 'chime_c', 0.4)]),
           dict(desde=23, fn=s_compa, tr='golpe', sfx=[(0.05, 'slap', 0.7)]),
           dict(desde=24, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    """Sonidos que dependen de los tiempos por palabra (se agregan al cargar)."""
    add = {5: [(Wp(5, 'treinta') + 0.1, 'bass', 0.9)], 8: [(Wp(8, 'doble') - 0.1, 'sub', 0.8)],
           10: [(Wp(10, 'clic') - 0.05, 'click', 1.0), (Wp(10, 'clic'), 'bass', 0.7)],
           12: [(Wp(12, 'ultimo') + 0.9, 'click', 0.9), (Wp(12, 'ultimo') + 1.0, 'scribble', 0.5)],
           14: [(Wp(14, 'chispa') - 0.05, 'burst', 1.0), (Wp(14, 'chispa') + 0.15, 'sub', 0.9)],
           15: [(Wp(15, 'rojo'), 'click', 0.8)], 16: [(Wp(16, 'rojo'), 'click', 0.8), (Wp(16, 'negro'), 'click', 0.8)],
           20: [(max(-0.1, Wp(20, 'tercer') - 0.9), 'click', 0.7), (max(0.2, Wp(20, 'tercer') - 0.5), 'click', 0.7),
                (Wp(20, 'tercer') - 0.1, 'click', 0.8), (Wp(20, 'tercer') + 0.05, 'bass', 0.7)]}
    for e in ESCENAS:
        if e.get('desde') in add and not e.get('loop'):
            e['sfx'] = list(e.get('sfx', [])) + add[e['desde']]


_sfx_dinamicos()


def tiempos_falsos():
    T = [(round(0.25 + 2.7 * i, 2), round(0.25 + 2.7 * i + 2.3, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.55, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    print('ok', T[-1])


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    else:
        montaje.cli(globals())
