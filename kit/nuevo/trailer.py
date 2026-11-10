"""Reel diario jue 12-nov-2026 10:00 — «Tu tráiler no truena… está frenando.» (freno de motor / «Jake brake»).
Comunidad: troqueros y traileros (decisión de Efrén del 10-nov: vehículos y comunidades mexicanas por dentro).
Inicio tipo 1 (caída desde el espacio): Tierra de alambre → crash zoom a las Cumbres de Maltrata → la cámara cae a la
carretera → el tráiler bajando con el tronido y el título que se estrella. El final regresa a la Tierra (loop).
Voz Isaac (eleven_v4), 70.7 s. Datos y fuentes: guiones/2026-11-12_trailer.txt.
Todo es recreación en 3D (no hay foto libre a la mano de un tráiler sin logos): se marca «RECREACIÓN».
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
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'trailer'
TXT = ['Tu tráiler no truena… está frenando.',
       'Ese tronido en las bajadas es el freno de motor.',
       'En inglés le dicen «Jake brake».',
       'Mira por dentro: el pistón sube y aprieta el aire como un resorte.',
       'Sin freno de motor, ese aire empuja el pistón de regreso y te devuelve la fuerza.',
       'Con freno de motor, la válvula del escape se abre justo arriba…',
       'y el aire sale de golpe.',
       'Ese aire que escapa es el tronido, y la fuerza ya no regresa: frena las llantas.',
       'Y el error que manda tráileres al barranco: bajar la cuesta solo con el pedal.',
       'Las balatas se calientan tanto que dejan de agarrar…',
       'y te quedas sin frenos.',
       'En las Cumbres de Maltrata la carretera baja más de 1 000 metros.',
       'Por eso tiene rampas de frenado.',
       'Con el freno de motor, tu motor se vuelve un compresor…',
       'y frena sin gastar ni una gota de diésel.',
       'Un motor de 15 litros puede frenar con unos 600 caballos de fuerza.',
       'Truena tanto que en algunos pueblos de Estados Unidos hay letreros que lo prohíben.',
       'Por eso el trailero baja en cambio corto y con el freno de motor puesto.',
       'Mándaselo a tu compa trailero,',
       'para que sepa que su tráiler no truena… está frenando.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-12_trailer_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_trailer.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-12_trailer_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 150, 60)
ROJO = (255, 50, 40)
ROJO_C = (176, 26, 24)
CROMO = (212, 214, 220)
NEGRO = (24, 24, 27)
CAJA = (224, 226, 230)
VIDRIO = (26, 34, 46)
METAL = (150, 154, 162)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)


# ------------------------------------------------------------------ tiempos por palabra (u de la palabra k de la frase i)
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    d = json.load(open(WORDS))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(montaje._norm(w.get('text', '')), float(w['start'])) for w in d
          if w.get('type', 'word') == 'word' and montaje._norm(w.get('text', ''))]
    sw = []
    for i, f in enumerate(VOZ):
        for w in re.sub(r'\[[^\]]*\]', ' ', f).split():
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
        base = next(x for x in L if x is not None)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wu(i, k):
    L = _wt()[i]
    return L[min(k, len(L) - 1)]


# ------------------------------------------------------------------ utilidades de cámara y movimiento
def cam(u, claves, cy=0.55):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p.get('tx', 0.0), p.get('ty', 0.8), p.get('tz', 0.0)), dist=p['dist'], yaw=p['yaw'],
               pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch, tx=0.0, ty=0.8, tz=0.0, roll=0.0):
    return (u, dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll))


def golpe_k(u, u0, dur=0.32):
    return (1 - seg(u, u0, u0 + dur)) ** 2 if u >= u0 else 0.0


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    return P.mover_img(img, amp * k * math.sin(t * 91.0) * math.cos(t * 37.0), amp * k * math.sin(t * 73.0 + 1.3))


def texto(img, fx, x, y, txt, size, col=WHITE, k=1.0, f='sansx', glow=0.35, anchor='mm'):
    if k <= 0.01:
        return
    lay = Image.new('L', img.size, 0)
    ImageDraw.Draw(lay).text((x, y), txt, font=M.font(f, size), fill=int(255 * clamp(k)), anchor=anchor)
    img.paste(Image.new('RGB', img.size, col), (0, 0), lay)
    if glow:
        fx.paste(Image.new('RGB', img.size, M.scale_c(col, glow)), (0, 0), lay.filter(ImageFilter.GaussianBlur(8)))


def recreacion(img, fx, k=1.0, y=1440):
    pill(img, fx, 540, y, 'RECREACIÓN', k, size=20, border=(150, 150, 160), dot=False)


# ------------------------------------------------------------------ el tráiler (malla semirrealista, frente hacia +x)
def _B(ms, sx, sy, sz, col, x, y, z, name='cuerpo', gloss=0.4, rim=0.55, glow=None):
    m = named(M3.box(sx, sy, sz, col, shadow=0, gloss=gloss).tf(t=(x, y, z)), name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    ms.append(m)
    return m


def _llanta(ms, x, zc, r=0.21, ancho=0.17, giro=0.0):
    ms.append(named(M3.cyl(r, ancho, NEGRO, n=18, shadow=0, gloss=0.15).tf(rx=90, t=(x, r, zc - ancho / 2)), 'llanta', rim=0.3))
    ms.append(named(M3.cyl(r * 0.55, ancho + 0.01, CROMO, n=12, shadow=0, gloss=0.9).tf(rx=90, t=(x, r, zc - ancho / 2 - 0.005)),
                    'rin', rim=0.7, gloss=0.9))
    # birlo que gira (se nota que la llanta da vueltas)
    bx, by = x + r * 0.33 * math.cos(giro), r + r * 0.33 * math.sin(giro)
    ms.append(named(M3.box(0.05, 0.05, ancho + 0.03, (90, 90, 96), shadow=0, base=False).tf(t=(bx, by, zc)), 'birlo'))


def trailer(giro=0.0, motor=False, faros=0.6, caja=True, freno_col=0.0):
    """Tractocamión rojo con caja seca. giro: ángulo de las llantas. motor=True: motor por dentro (nombre 'in')."""
    ms = []
    _B(ms, 5.6, 0.12, 0.56, (38, 38, 42), -0.6, 0.34, 0, gloss=0.2)                 # chasis
    _B(ms, 0.62, 1.28, 0.92, ROJO_C, 0.56, 0.47, 0, gloss=0.55)                     # dormitorio
    _B(ms, 0.64, 1.02, 0.92, ROJO_C, 1.18, 0.47, 0, gloss=0.55)                     # cabina
    _B(ms, 0.05, 0.36, 0.8, VIDRIO, 1.51, 1.02, 0, gloss=0.95, rim=0.9)            # parabrisas
    for z in (-0.47, 0.47):
        _B(ms, 0.3, 0.3, 0.02, VIDRIO, 1.2, 1.0, z, gloss=0.9)                       # ventanas
        _B(ms, 0.04, 0.22, 0.05, CROMO, 1.47, 1.02, z * 1.12, gloss=0.95)            # espejos
    _B(ms, 0.8, 0.5, 0.86, ROJO_C, 1.9, 0.47, 0, gloss=0.6)                         # cofre
    _B(ms, 0.05, 0.42, 0.62, CROMO, 2.31, 0.5, 0, gloss=0.95, rim=0.9)             # parrilla
    for j in range(5):
        _B(ms, 0.06, 0.02, 0.6, (70, 70, 76), 2.33, 0.56 + j * 0.07, 0, gloss=0.3)
    _B(ms, 0.12, 0.15, 1.0, CROMO, 2.34, 0.31, 0, gloss=0.95, rim=0.9)             # defensa
    for z in (-0.33, 0.33):
        _B(ms, 0.04, 0.09, 0.15, (255, 244, 214), 2.32, 0.7, z, glow=M.scale_c((255, 226, 160), faros))
    for z in (-0.5, 0.5):                                                           # chimeneas de escape
        ms.append(named(M3.cyl(0.042, 1.25, CROMO, n=14, shadow=0, gloss=0.95).tf(t=(0.86, 0.66, z)), 'escape', rim=0.85, gloss=0.95))
        ms.append(named(M3.cyl(0.13, 0.5, CROMO, n=16, shadow=0, gloss=0.9).tf(rz=90, t=(1.72, 0.27, z)), 'tanque', rim=0.8, gloss=0.9))
    if caja:
        _B(ms, 3.9, 1.3, 0.94, CAJA, -1.66, 0.5, 0, gloss=0.3, rim=0.6)            # caja seca
        for j in range(9):
            _B(ms, 0.03, 1.28, 0.955, (196, 198, 204), -3.5 + j * 0.46, 0.51, 0, gloss=0.2)
        for x in (-2.75, -3.2):
            for z in (-0.38, 0.38):
                _llanta(ms, x, z, giro=giro)
    for x in (1.98, 0.62, 0.18):
        for z in (-0.4, 0.4):
            _llanta(ms, x, z, giro=giro)
    if motor:                                                                       # motor diésel de 6 cilindros en línea
        _B(ms, 0.62, 0.3, 0.4, (110, 114, 122), 1.9, 0.48, 0, name='in', gloss=0.5)
        for j in range(6):
            _B(ms, 0.08, 0.1, 0.3, (170, 174, 182), 1.65 + j * 0.1, 0.78, 0, name='in', gloss=0.6)
        _B(ms, 0.7, 0.05, 0.12, (210, 120, 60), 1.9, 0.9, 0.08, name='in', gloss=0.4)  # múltiple de escape
    if freno_col > 0.01:
        for x in (0.62, 0.18):
            for z in (-0.49, 0.49):
                _B(ms, 0.18, 0.18, 0.02, M.mixc((80, 60, 50), (255, 90, 30), freno_col), x, 0.12, z,
                   name='freno', glow=M.scale_c((255, 110, 40), freno_col))
    return ms


def carretera(fr, t, vel=5.0, a=1.0, ancho=1.25, x0=-16, x1=16):
    for z in (-ancho, ancho):
        line3(fr, [(x0, 0.01, z), (x1, 0.01, z)], col=WHITE, w=2.4, a=0.75 * a, glow=0.6)
    off = (t * vel) % 1.6
    for i in range(int(x0 / 1.6) - 1, int(x1 / 1.6) + 1):
        xa = i * 1.6 - off
        line3(fr, [(xa, 0.012, 0), (xa + 0.75, 0.012, 0)], col=AMARILLO, w=3.2, a=0.85 * a, glow=0.8)


def montes(fr, a=0.7, z=-9.0, seed=3):
    rng = np.random.RandomState(seed)
    xs = np.linspace(-20, 20, 44)
    ys = 1.4 + 1.6 * np.abs(np.sin(xs * 0.23 + 1.1)) + rng.uniform(0, 0.5, len(xs))
    line3(fr, [(x, y, z) for x, y in zip(xs, ys)], col=(200, 205, 215), w=2.0, a=a, glow=0.5)


def tronido(img, fx, x, y, t, k=1.0, rate=7.0, escala=1.0):
    """Anillos del tronido saliendo de la chimenea (y bocanadas de humo gris)."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    for j in range(4):
        ph = ((t * rate / 4) + j / 4) % 1.0
        r = (18 + 150 * ph) * escala
        c = M.scale_c(WHITE, k * (1 - ph) * 0.9)
        d.ellipse((x - r, y - r * 0.75, x + r, y + r * 0.75), outline=c, width=4)
        df.ellipse((x - r, y - r * 0.75, x + r, y + r * 0.75), outline=M.scale_c(CYAN, k * (1 - ph) * 0.7), width=12)
    for j in range(5):
        ph = ((t * 1.3) + j / 5) % 1.0
        rr = (10 + 34 * ph) * escala
        yy = y - 30 * escala - 160 * ph * escala
        xx = x - 60 * ph * escala + 8 * math.sin(t * 5 + j)
        d.ellipse((xx - rr, yy - rr, xx + rr, yy + rr), fill=M.scale_c((150, 150, 158), k * (1 - ph) * 0.55))


def escena_camion(t, u, claves, cy=0.58, roll=-6.0, vel=5.0, motor=False, xray=0.0, caja=True, freno_col=0.0,
                  floor_a=0.7, mont=True, beam=0.3, dx=0.0):
    """Escenario base: el tráiler bajando una cuesta (la cámara va inclinada) con la carretera que corre."""
    p = P.cam_rapida(u, claves)
    fr = Frame(Cam(target=(p['tx'] + dx, p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy,
                   roll=p.get('roll', 0.0) + roll))
    space(fr, t, floor='lines', floor_a=floor_a, bokeh=0.9, beam=beam)
    if mont:
        montes(fr)
    carretera(fr, t, vel=vel)
    return fr, trailer(giro=-t * vel / 0.21, motor=motor, caja=caja, freno_col=freno_col)


def chimenea_px(fr, z=0.5):
    x, y, _ = fr.cam.p1((0.86, 1.95, z))
    return x, y


# ------------------------------------------------------------------ el cilindro por dentro (corte)
_AIRE = np.random.RandomState(11).rand(54, 3)


def cilindro(fr, t, yp, valv=0.0, salida=0.0, resorte=0.0, aire=1.0, col_aire=None, adm=0.0):
    """Corte de un cilindro: paredes de line-art, pistón de metal, válvulas, aire (puntos) y escape.
    yp 0..1 = altura del pistón (1 = arriba del todo). valv 0..1 = cuánto abre la válvula del escape."""
    R, Y1 = 0.52, 1.7
    top = 0.35 + 1.05 * yp                      # cara de arriba del pistón
    comp = clamp((1.4 - (Y1 - top)) / 1.05)     # 0 = aire suelto, 1 = muy apretado
    th = np.linspace(0, 2 * math.pi, 48)
    for yy, a in ((Y1, 0.9), (0.0, 0.6), (0.85, 0.25)):
        line3(fr, [(R * math.cos(q), yy, R * math.sin(q)) for q in th], col=WHITE, w=2.0, a=a, glow=0.5)
    for q in (0.0, math.pi):
        line3(fr, [(R * math.cos(q), 0.0, R * math.sin(q)), (R * math.cos(q), Y1, R * math.sin(q))], col=WHITE, w=2.4, a=0.9, glow=0.6)
    # cabeza (line-art) y puerto de escape que sale a la derecha
    for x0, x1 in ((-0.62, 0.62),):
        line3(fr, [(x0, Y1, 0), (x0, Y1 + 0.38, 0), (x1, Y1 + 0.38, 0), (x1, Y1, 0)], col=WHITE, w=2.2, a=0.8, glow=0.5)
    port = [(0.22, Y1 + 0.02, 0), (0.3, Y1 + 0.3, 0), (0.55, Y1 + 0.55, 0), (1.0, Y1 + 0.62, 0), (1.6, Y1 + 0.62, 0)]
    for dz in (-0.1, 0.1):
        line3(fr, [(x + (0.06 if dz > 0 else -0.06) * (1 if i < 2 else 0), y + dz * (1 if i >= 2 else 0.3), 0) for i, (x, y, _) in enumerate(port)],
              col=NARANJA, w=2.4, a=0.85, glow=0.7)
    ms = []
    pm = named(M3.cyl(R * 0.95, 0.42, METAL, n=26, shadow=0, gloss=0.7).tf(t=(0, top - 0.42, 0)), 'piston', rim=0.7, gloss=0.7)
    ms.append(pm)
    for j in range(3):
        ms.append(named(M3.cyl(R * 0.955, 0.025, (60, 62, 68), n=26, shadow=0, gloss=0.3).tf(t=(0, top - 0.1 - 0.07 * j, 0)), 'anillo'))
    ms.append(named(M3.box(0.12, max(0.05, top - 0.42 + 0.6), 0.1, (120, 124, 132), shadow=0, gloss=0.5).tf(t=(0, -0.6, 0)), 'biela'))
    # válvulas (hongo): escape a la derecha (baja al abrir), admisión a la izquierda
    for x, lift, col in ((0.24, 0.22 * valv, (230, 150, 90)), (-0.24, 0.18 * adm, (190, 194, 202))):
        ms.append(named(M3.cyl(0.035, 0.55, (200, 202, 208), n=10, shadow=0, gloss=0.8).tf(t=(x, Y1 - 0.03 - lift, 0)), 'vastago'))
        ms.append(named(M3.cyl(0.16, 0.05, col, n=20, shadow=0, gloss=0.8).tf(t=(x, Y1 - 0.06 - lift, 0)), 'valvula', rim=0.8))
    draw_objects(fr, ms)
    # cigüeñal (line-art)
    line3(fr, [(0.32 * math.cos(q), -0.75 + 0.32 * math.sin(q), 0.0) for q in th], col=WHITE, w=1.8, a=0.45, glow=0.4)
    # resorte de aire (garabato en zigzag que se aprieta)
    if resorte > 0.01:
        n = 9
        pts = [(-0.05 + (0.2 if i % 2 else -0.2), top + (Y1 - top) * i / n, 0.3) for i in range(n + 1)]
        line3(fr, pts, col=AMARILLO, w=3.0, a=resorte, glow=0.9)
    # aire: puntos que se juntan (y se ponen blancos) al apretarse; con salida se van por el escape
    ca = col_aire or M.mixc(CYAN, (255, 255, 255), comp)
    nsal = int(len(_AIRE) * clamp(salida))
    for j, (a, b, c) in enumerate(_AIRE):
        if j < nsal:
            s = clamp(salida * 1.8 - j / len(_AIRE))
            if s >= 1:
                continue
            q = int(s * (len(port) - 1))
            fr_ = s * (len(port) - 1) - q
            pa, pb = np.array(port[q]), np.array(port[min(q + 1, len(port) - 1)])
            p = pa + (pb - pa) * fr_ + np.array([0, (c - 0.5) * 0.12, (a - 0.5) * 0.12])
            dot3(fr, p, r=5, col=WHITE, a=aire * (1 - s * 0.6), glow=1.2)
            continue
        rr = R * 0.85 * math.sqrt(a)
        q = 2 * math.pi * b + t * 0.6
        y = top + 0.03 + (Y1 - top - 0.06) * c
        dot3(fr, (rr * math.cos(q), y, rr * math.sin(q)), r=3.5 + 2.0 * comp, col=ca, a=aire * (0.55 + 0.45 * comp), glow=0.8 + 0.9 * comp)
    return comp


# ------------------------------------------------------------------ el tambor del freno (balatas)
def tambor(fr, t, calor=0.0, giro=0.0, abre=0.0):
    ms = []
    hot = M.mixc((92, 92, 98), (255, 110, 40), calor)
    ms.append(named(M3.cyl(0.95, 0.42, hot, n=36, shadow=0, gloss=0.6).tf(rx=90, t=(0, 1.0, -0.21)), 'tambor', rim=0.7,
                    glow=M.scale_c((255, 90, 30), calor * 0.6) if calor > 0.05 else None, double=True))
    ms[-1].double = True
    return ms


def balatas(fr, t, calor=0.0, giro=0.0, apriete=1.0):
    """Tambor en corte (line-art que brilla con el calor) y las 2 balatas que aprietan desde adentro."""
    C = np.array([0.0, 1.0, 0.0])
    th = np.linspace(0, 2 * math.pi, 72)
    colt = M.mixc((235, 238, 245), (255, 120, 50), calor)
    for r, a in ((1.0, 0.95), (0.9, 0.6)):
        for z in (-0.18, 0.18):
            line3(fr, [C + np.array([r * math.cos(q + giro), r * math.sin(q + giro), z]) for q in th], col=colt, w=2.6, a=a,
                  glow=0.6 + 1.2 * calor)
    for j in range(8):                                   # birlos que giran
        q = giro + j * math.pi / 4
        dot3(fr, C + np.array([0.3 * math.cos(q), 0.3 * math.sin(q), 0.2]), r=6, col=CROMO, a=0.9, glow=0.4)
    ms = []
    for s in (1, -1):                                    # balatas: arcos (extrusión) con su forro
        pts = []
        for q in np.linspace(math.radians(25), math.radians(155), 14):
            pts.append((0.86 * math.cos(q) * s, 0.86 * math.sin(q) * s))
        for q in np.linspace(math.radians(155), math.radians(25), 14):
            pts.append((0.7 * math.cos(q) * s, 0.7 * math.sin(q) * s))
        off = (0.02 + 0.05 * (1 - apriete)) * s
        m = M3.extrude([(x, y) for x, y in pts], 0.3, M.mixc((96, 70, 52), (255, 96, 30), calor), shadow=0, gloss=0.2)
        m = m.tf(rx=-90, t=(0, 1.0 - off, -0.15))
        m = named(m, 'balata', rim=0.5, glow=M.scale_c((255, 80, 20), 0.8 * calor) if calor > 0.1 else None)
        ms.append(m)
    draw_objects(fr, ms)
    return C


# ------------------------------------------------------------------ Tierra de alambre (inicio tipo 1)
def geo(lat, lon, spin, C, R):
    la, lo = math.radians(lat), math.radians(lon)
    p = np.array([[R * math.cos(la) * math.cos(lo), R * math.sin(la), R * math.cos(la) * math.sin(lo)]])
    return np.asarray(C, float) + D._rot(p, spin)[0]


UC = 0.6     # corte interno: de la Tierra a la carretera
UL = 1.05    # la cámara «aterriza» en el tráiler: golpe + título


def _gancho_tierra(t, fi, u):
    k = P.eout4(seg(u, UC - 0.32, UC))
    C = np.array([0.0, 1.0, 0.0])
    spin = 2.92 + 0.1 * (u - UC)
    fr = Frame(Cam(target=tuple(C), dist=6.4 - 0.4 * seg(u, -0.3, UC - 0.32) - 3.0 * k, yaw=5 * math.sin(t * 0.4), pitch=10, cy=0.5))
    space(fr, t, floor=None, bokeh=1.0)
    M.cristal(fr.base, fr.fx, 'TRUENA', u, t0=-2.3, cy=0.5, entrada='golpe')
    N.earth(fr, t, C, 1.55, spin)
    mx = geo(18.8, -97.3, spin, C, 1.55)
    dot3(fr, mx, r=9, col=AMARILLO, a=0.6 + 0.4 * math.sin(t * 9), glow=1.5)
    for j in range(3):                                   # ondas del tronido que salen de las Cumbres
        ph = (t * 1.6 + j / 3) % 1.0
        q = np.linspace(0, 2 * math.pi, 40)
        line3(fr, [mx + np.array([0.08 + 0.5 * ph * math.cos(a), 0.4 * ph * math.sin(a), 0.2]) for a in q],
              col=AMARILLO, w=2.2, a=(1 - ph) * 0.8, glow=1.0)

    def ui(img, fx):
        x, y, _ = fr.cam.p1(tuple(mx))
        pill(img, fx, x, y - 70, 'CUMBRES DE MALTRATA', eout(seg(u, -0.6, -0.3)) * (1 - k), size=26, border=AMARILLO)
        kicker(img, 'PUEBLA → VERACRUZ · BAJADA', 150, (1 - k), col=AZULC)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if k > 0.05:
        px, py, _ = fr.cam.p1(tuple(mx))
        out = M.scale_about(out, 1 + 2.8 * k * k, px / 1080, py / 1920)
        out = M.radial_blur(out, 0.16 * k, px / 1080, py / 1920)
    return out


# ================================================================== escenas
# 0. gancho (inicio 1: caída desde el espacio) → la cámara cae del cielo a la carretera y aterriza junto al tráiler
def s_gancho(t, fi, u, d):
    if u < UC:
        return _gancho_tierra(t, fi, u)
    fr, ms = escena_camion(t, u, [K(UC, 13.0, 30, 70, tx=0.0, ty=0.5), K(UL, 8.2, 38, 10, tx=-0.2, ty=1.0),
                                  K(2.4, 7.4, 30, 8, tx=0.2, ty=1.0), K(4.0, 7.0, 24, 8, tx=0.2, ty=1.0)], cy=0.6, roll=-7)
    M.cristal(fr.base, fr.fx, 'TRUENA', u, t0=-2.3, cy=0.37, entrada='golpe')
    draw_objects(fr, ms)
    cx, cy = chimenea_px(fr)

    def ui(img, fx):
        tronido(img, fx, cx, cy, t, k=seg(u, UL - 0.05, UL + 0.1), escala=0.9)
        kicker(img, 'FRENO DE MOTOR · TRAILEROS', 150, seg(u, UL, UL + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu tráiler no truena…', 'sans'), ('está frenando.', 'serif')], 200, seg(u, UL, UL + 0.15), size=76)
        recreacion(img, fx, seg(u, UL + 0.3, UL + 0.6))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, UL + 0.15, 0.4), amp=26)


# 1. el tronido en la bajada = el freno de motor (pastilla que señala la chimenea)
def s_tronido(t, fi, u, d):
    uf = Wu(1, 6) - 0.1                                     # «freno de motor»
    fr, ms = escena_camion(t, u, [K(-0.3, 4.2, 70, 6, tx=0.9, ty=1.4), K(0.5, 4.6, 52, 4, tx=0.8, ty=1.5),
                                  K(uf, 3.4, 30, 12, tx=0.9, ty=1.7), K(3.5, 3.3, 26, 12, tx=0.9, ty=1.7)], cy=0.55, roll=-6)
    draw_objects(fr, ms)
    cx, cy = chimenea_px(fr)

    def ui(img, fx):
        tronido(img, fx, cx, cy, t, k=1.0, escala=1.3)
        pill(img, fx, cx - 40, cy - 230, 'FRENO DE MOTOR', eout(seg(u, uf, uf + 0.25)), size=34, border=AMARILLO)
        if u > uf:
            doodle_circle(img, fx, cx, cy + 40, 120, 160, t, k=seg(u, uf + 0.1, uf + 0.5), col=AMARILLO, seed=2)
        kicker(img, 'EL TRONIDO DE LAS BAJADAS', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uf, 0.3), amp=12)


# 2. «Jake brake» (entra atravesando la palabra de cristal): la cabina de frente con su chimenea
def s_jake(t, fi, u, d):
    fr, ms = escena_camion(t, u, [K(-0.3, 6.0, -10, 6, tx=1.2, ty=1.0), K(0.6, 4.4, -32, 4, tx=1.2, ty=1.1),
                                  K(2.4, 4.2, -38, 4, tx=1.2, ty=1.1)], cy=0.6, roll=-4, vel=4.0)
    draw_objects(fr, ms)
    cx, cy = chimenea_px(fr, z=-0.5)

    def ui(img, fx):
        tronido(img, fx, cx, cy, t, k=1.0, escala=1.0)
        kicker(img, 'EN INGLÉS', 150, seg(u, 0.0, 0.3), col=AZULC)
        texto(img, fx, 540, 300, '«Jake brake»', 104, WHITE, eout(seg(u, 0.05, 0.3)), f='serif', glow=0.3)
        pill(img, fx, 540, 420, 'POR JACOBS, LA MARCA QUE LO HIZO PRIMERO', eout(seg(u, 0.5, 0.8)), size=24,
             border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. por dentro: rayos X del cofre → el cilindro en corte; el pistón sube y aprieta el aire como un resorte
def s_piston(t, fi, u, d):
    ux = 0.9                                               # aquí cambia del cofre al cilindro
    if u < ux:
        fr, ms = escena_camion(t, u, [K(-0.3, 3.4, 20, 18, tx=1.9, ty=0.7), K(0.4, 2.4, 36, 22, tx=1.9, ty=0.7),
                                      K(ux, 2.2, 40, 22, tx=1.9, ty=0.7)], cy=0.52, roll=-3, motor=True, mont=False)
        draw_objects(fr, ms, xray=seg(u, -0.2, 0.3), keep=('in',))

        def ui(img, fx):
            kicker(img, 'RAYOS X · MOTOR DIÉSEL', 150, seg(u, -0.1, 0.2), col=AZULC)
        fr.ui.append(ui)
        out = finish(fr, fi)
        kz = seg(u, ux - 0.35, ux)
        if kz > 0:
            out = M.radial_blur(M.scale_about(out, 1 + 2.2 * kz * kz, 0.5, 0.5), 0.15 * kz)
        return out
    uh = Wu(3, 7) - 0.1                                    # «aprieta»
    fr = Frame(cam(u, [K(ux, 4.6, 40, 14, ty=0.9), K(ux + 0.5, 4.0, 18, 10, ty=0.95), K(uh, 3.7, -14, 8, ty=1.05),
                       K(6, 3.6, -20, 8, ty=1.05)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    yp = P.eout4(seg(u, uh - 0.3, uh + 1.4)) * 0.95
    comp = cilindro(fr, t, yp, resorte=seg(u, uh + 0.5, uh + 0.9))

    def ui(img, fx):
        kicker(img, 'UN CILINDRO · CORTE', 150, seg(u, ux, ux + 0.3), col=AZULC)
        pill(img, fx, 800, 640, 'AIRE', eout(seg(u, ux + 0.3, ux + 0.6)), size=30, border=CYAN)
        pill(img, fx, 260, 1260, 'PISTÓN', eout(seg(u, ux + 0.5, ux + 0.8)), size=30, border=(200, 200, 210))
        texto(img, fx, 540, 330, f'APRETADO {int(100 * comp)}%', 56, AMARILLO, seg(u, uh, uh + 0.3), f='mono', glow=0.3)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. caso 1 (SIN freno de motor): el aire apretado empuja el pistón de regreso y te devuelve la fuerza
def s_sin(t, fi, u, d):
    ub = Wu(4, 9) - 0.1                                    # «de regreso»
    fr = Frame(cam(u, [K(-0.3, 3.9, -40, 10, ty=1.0), K(0.4, 3.6, -22, 8, ty=1.0), K(ub, 3.2, 8, 6, ty=0.95),
                       K(6, 3.1, 12, 6, ty=0.95)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    yp = 0.95 - 0.9 * P.eout4(seg(u, ub, ub + 0.8))
    cilindro(fr, t, yp, resorte=1.0 - 0.5 * seg(u, ub, ub + 0.8))
    for j in range(3):                                     # flechas: el aire empuja hacia abajo
        x = -0.25 + 0.25 * j
        k = seg(u, ub + 0.05 * j, ub + 0.3 + 0.05 * j)
        if k > 0:
            line3(fr, [(x, 1.6, 0.6), (x, 1.6 - 0.9 * k, 0.6)], col=AMARILLO, w=4, a=k, glow=1.0)

    def ui(img, fx):
        texto(img, fx, 540, 250, 'SIN FRENO DE MOTOR', 54, WHITE, eout(seg(u, -0.1, 0.15)), f='sansx', glow=0.3)
        kicker(img, 'CASO 1 · LA VÁLVULA SE QUEDA CERRADA', 340, seg(u, 0.1, 0.4), col=AZULC)
        pill(img, fx, 540, 1400, '↓ TE DEVUELVE LA FUERZA', eout(seg(u, ub + 0.6, ub + 0.9)), size=32, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. caso 2 (CON freno de motor): justo arriba, la válvula del escape se abre (garabato + zoom digital REC)
def s_con(t, fi, u, d):
    uv = Wu(5, 6) - 0.1                                    # «se abre»
    fr = Frame(cam(u, [K(-0.3, 3.9, 40, 10, ty=1.0), K(0.4, 3.5, 20, 8, ty=1.05), K(uv, 2.4, 10, 6, ty=1.6),
                       K(6, 2.3, 6, 6, ty=1.6)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    cilindro(fr, t, 0.95, valv=P.eout4(seg(u, uv, uv + 0.25)), resorte=0.6)
    vx, vy, _ = fr.cam.p1((0.24, 1.6, 0))

    def ui(img, fx):
        texto(img, fx, 540, 250, 'CON FRENO DE MOTOR', 54, AMARILLO, eout(seg(u, -0.1, 0.15)), f='sansx', glow=0.3)
        kicker(img, 'CASO 2 · EL PISTÓN LLEGA ARRIBA', 340, seg(u, 0.1, 0.4), col=AZULC)
        if u > uv - 0.2:
            doodle_circle(img, fx, vx, vy, 110, 80, t, k=seg(u, uv - 0.2, uv + 0.2), col=AMARILLO, seed=4)
            pill(img, fx, vx + 60, vy + 150, 'VÁLVULA DEL ESCAPE', eout(seg(u, uv, uv + 0.25)), size=28, border=NARANJA)
        rec_frame(img, t, k=seg(u, uv, uv + 0.2), zoom_label='x1.8')
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. y el aire sale de golpe (iris desde la válvula; «AIRE» de cristal detrás; sacudida)
def s_sale(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 3.0, -20, 10, ty=1.6), K(0.3, 3.6, -36, 14, ty=1.5), K(3, 3.7, -40, 14, ty=1.5)], cy=0.52))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'AIRE', u, t0=0.0, cy=0.33, entrada='zoom')
    cilindro(fr, t, 0.95, valv=1.0, salida=P.eout4(seg(u, 0.0, 1.0)))

    def ui(img, fx):
        kicker(img, 'SALE DE GOLPE POR EL ESCAPE', 1300, seg(u, 0.1, 0.4), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.05, 0.4), amp=22)


# 7. ese aire es el tronido y la fuerza ya no regresa: frena las llantas (zoom out del escape a las llantas)
def s_llantas(t, fi, u, d):
    ul = Wu(7, 12) - 0.1                                   # «frena las llantas»
    vel = 5.0 - 2.5 * seg(u, ul, ul + 1.0)
    fr, ms = escena_camion(t, u, [K(-0.3, 2.6, 20, 30, tx=0.86, ty=2.0), K(0.5, 5.0, 40, 14, tx=0.6, ty=1.2),
                                  K(ul, 3.1, 18, 8, tx=0.4, ty=0.45), K(4, 3.0, 24, 8, tx=0.4, ty=0.45)], cy=0.55, roll=-5, vel=vel)
    draw_objects(fr, ms)
    cx, cy = chimenea_px(fr)
    wx, wy, _ = fr.cam.p1((0.4, 0.22, 0.6))

    def ui(img, fx):
        tronido(img, fx, cx, cy, t, k=1 - seg(u, ul - 0.3, ul), escala=1.2)
        pill(img, fx, 540, 330, 'ESE AIRE = EL TRONIDO', eout(seg(u, 0.2, 0.5)), size=34, border=CYAN, dot=False)
        if u > ul - 0.1:
            for j in range(2):
                doodle_arrow(img, fx, wx + 220 - j * 40, wy - 180 + j * 30, wx + 80, wy - 40, t, k=seg(u, ul, ul + 0.4), col=AMARILLO, seed=j)
            pill(img, fx, wx + 40, wy - 260, 'FRENA LAS LLANTAS', eout(seg(u, ul + 0.1, ul + 0.4)), size=32, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. SEGUNDO GANCHO: el error — bajar la cuesta solo con el pedal (pedal que se hunde, aviso rojo)
def s_error(t, fi, u, d):
    up = Wu(8, 9) - 0.1                                    # «bajar la cuesta»
    fr = Frame(cam(u, [K(-0.3, 3.2, 50, 16, ty=0.5), K(0.4, 2.7, 24, 12, ty=0.5), K(up, 2.4, -16, 18, ty=0.45),
                       K(5, 2.3, -22, 18, ty=0.45)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'PEDAL', u, t0=0.0, cy=0.36, entrada='golpe')
    press = P.eout4(seg(u, up, up + 0.4)) * (0.8 + 0.2 * math.sin(t * 6) ** 2)
    ms = [named(M3.box(1.4, 0.06, 1.0, (40, 40, 44), shadow=0, gloss=0.2).tf(t=(0, 0, 0)), 'piso')]
    arm = M3.box(0.08, 0.9, 0.08, (70, 72, 78), shadow=0, gloss=0.4)
    plate = M3.box(0.5, 0.06, 0.32, (34, 34, 38), shadow=0, gloss=0.3).tf(t=(0, 0.9, 0))
    for j in range(5):
        ms.append(named(M3.box(0.48, 0.015, 0.03, (90, 90, 96), shadow=0).tf(t=(0, 0.965, -0.12 + 0.06 * j)).tf(rx=-62 + 40 * press, t=(0, 0.15, 0.3)), 'goma'))
    ms += [named(arm.tf(rx=-62 + 40 * press, t=(0, 0.15, 0.3)), 'brazo', rim=0.7, gloss=0.5),
           named(plate.tf(rx=-62 + 40 * press, t=(0, 0.15, 0.3)), 'pedal', rim=0.8, gloss=0.4)]
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, -0.1, 0.1), col=(255, 120, 110))
        P.titulo_golpe(img, fx, [('Bajar la cuesta', 'sans'), ('solo con el pedal.', 'serif')], 200, seg(u, up, up + 0.15), size=78, col=WHITE)
        pill(img, fx, 540, 1380, '⚠ ERROR QUE MANDA TRÁILERES AL BARRANCO', eout(seg(u, 0.1, 0.35)), size=24, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.15, 0.35), amp=20)


# 9. las balatas se calientan tanto que dejan de agarrar (tambor en corte que se pone al rojo + termómetro)
def s_balatas(t, fi, u, d):
    uc = Wu(9, 3) - 0.1                                    # «se calientan»
    calor = P.eout4(seg(u, uc - 0.2, uc + 1.6))
    fr = Frame(cam(u, [K(-0.3, 4.2, -30, 8, ty=1.0), K(0.5, 3.6, -8, 4, ty=1.0), K(uc + 0.6, 3.2, 18, 4, ty=1.0),
                       K(5, 3.1, 22, 4, ty=1.0)], cy=0.53))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'BALATAS', u, t0=-0.1, cy=0.3, entrada='sube')
    C = balatas(fr, t, calor=calor, giro=-t * 4.0)
    P.ondas_calor(fr, t, 0.0, 2.05, 2.9, 1.4, k=calor)

    def ui(img, fx):
        P.termometro(img, fx, 150, 1330, 380, 0.15 + 0.8 * calor, 'CALIENTE' if calor > 0.5 else '', k=seg(u, uc - 0.2, uc))
        pill(img, fx, 800, 1310, 'BALATA', eout(seg(u, 0.2, 0.5)), size=30, border=NARANJA)
        kicker(img, 'TAMBOR DEL FRENO · CORTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1430, 'MÁS CALIENTE = MENOS AGARRE', eout(seg(u, uc + 1.0, uc + 1.3)), size=28, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. y te quedas sin frenos (falla digital, indicador en rojo y el tráiler que se acelera)
def s_sinfrenos(t, fi, u, d):
    vel = 6.0 + 6.0 * seg(u, 0.0, 1.6)
    fr, ms = escena_camion(t, u, [K(-0.3, 7.0, -50, 10, tx=0.0, ty=1.0), K(0.35, 6.2, -24, 6, tx=0.0, ty=1.0),
                                  K(2.5, 5.6, -16, 6, tx=0.0, ty=1.0)], cy=0.6, roll=-9, vel=vel, freno_col=1.0)
    draw_objects(fr, ms)

    def ui(img, fx):
        txt = 'SIN FRENOS'
        k = eout(seg(u, 0.0, 0.2))
        dx = int(10 * math.sin(t * 60)) if (int(t * 12) % 3 == 0) else 0
        texto(img, fx, 540 + dx, 330, txt, 120, ROJO, k, f='sansx', glow=0.6)
        for j in range(6):                                    # líneas de velocidad
            yy = 700 + j * 90
            ph = (t * 3 + j * 0.37) % 1.0
            ImageDraw.Draw(img).line([(1080 * (1 - ph), yy), (1080 * (1 - ph) + 260, yy)], fill=M.scale_c(WHITE, 0.35), width=3)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if int(t * 8) % 4 == 0:
        out = M.tr_glitch(out, out, 0.5, fi)
    return sacudir(out, t, 0.35, amp=8)


# 11. Cumbres de Maltrata: la carretera baja más de 1 000 metros (perfil de la bajada en line-art con su cota)
def s_cumbres(t, fi, u, d):
    um = Wu(11, 8) - 0.1                                   # «más de mil metros»
    fr = Frame(cam(u, [K(-0.3, 8.2, -40, 18, ty=1.5), K(0.4, 7.2, -14, 12, ty=1.5), K(um, 6.9, 10, 10, ty=1.4),
                       K(5, 6.8, 14, 10, ty=1.4)], cy=0.52))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    M.cristal(fr.base, fr.fx, '1 000 m', u, t0=um, cy=0.27, entrada='golpe')
    xs = np.linspace(-2.6, 2.6, 64)
    ys = 0.2 + 2.8 / (1 + np.exp(1.7 * xs)) + 0.1 * np.sin(xs * 5)
    kk = P.eout4(seg(u, -0.2, 0.8))
    n = max(2, int(len(xs) * kk))
    for j in range(0, n, 2):                                   # relleno de la montaña (rayas que brillan poco)
        line3(fr, [(xs[j], 0.0, 0), (xs[j], ys[j], 0)], col=(150, 155, 165), w=1.4, a=0.35, glow=0.2)
    line3(fr, [(x, y, 0) for x, y in zip(xs[:n], ys[:n])], col=WHITE, w=4.5, a=1.0, glow=1.0)
    for z, a in ((-0.7, 0.45), (-1.4, 0.25)):
        line3(fr, [(x * 1.1, y * 0.85 + 0.3, z) for x, y in zip(xs[:n], ys[:n])], col=(160, 165, 175), w=2.0, a=a, glow=0.3)
    s_ = (0.12 + 0.75 * seg(u, 0.2, 4.0))
    i = int(s_ * (len(xs) - 1))
    p = np.array([xs[i], ys[i] + 0.05, 0.0])
    dot3(fr, p, r=13, col=ROJO, a=1.0, glow=1.6)
    ka = P.eout4(seg(u, um - 0.2, um + 0.4))
    x0 = 1.55
    if ka > 0:
        line3(fr, [(x0, ys[0], 0.2), (x0, ys[0] - (ys[0] - ys[-1]) * ka, 0.2)], col=AMARILLO, w=5, a=1.0, glow=1.0)
        for y in (ys[0], ys[-1]):
            line3(fr, [(x0 - 0.25, y, 0.2), (x0 + 0.25, y, 0.2)], col=AMARILLO, w=5, a=ka, glow=1.0)
        line3(fr, [(xs[0], ys[0], 0.2), (x0, ys[0], 0.2)], col=AMARILLO, w=2, a=0.5 * ka, glow=0.5)
    py_ = fr.cam.p1((x0, (ys[0] + ys[-1]) / 2, 0.2))
    pt_ = fr.cam.p1(tuple(p))

    def ui(img, fx):
        kicker(img, 'CUMBRES DE MALTRATA · CAMINO A ORIZABA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, py_[0] - 30, py_[1], 'MÁS DE 1 000 m ↓', eout(seg(u, um + 0.1, um + 0.4)), size=32, border=AMARILLO, anchor='r')
        pill(img, fx, pt_[0], pt_[1] - 60, 'TRÁILER', eout(seg(u, 0.4, 0.7)), size=24, border=ROJO)
        pill(img, fx, 540, 1400, 'ESQUEMA', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.3, 0.3), amp=12)


# 12. por eso tiene rampas de frenado (el tráiler se mete a la rampa de grava y se clava)
def s_rampa(t, fi, u, d):
    s = P.eout4(seg(u, 0.0, 1.6))                          # recorre y frena en la grava
    x = -6.0 + 9.0 * s
    z = 0.0 if x < -1.5 else -2.5 * clamp((x + 1.5) / 2.0)
    fr = Frame(cam(u, [K(-0.3, 7.0, 60, 26, tx=x, ty=0.5, tz=z), K(0.4, 6.4, 36, 22, tx=x, ty=0.5, tz=z),
                       K(2.4, 6.0, 24, 20, tx=x, ty=0.5, tz=z), K(5, 5.9, 20, 20, tx=x, ty=0.5, tz=z)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8)
    carretera(fr, t, vel=0.0, x0=-10, x1=10)
    rng = np.random.RandomState(4)
    # la rampa sale a un lado y sube: grava de puntos
    for j in range(240):
        a, b = rng.rand(), rng.rand()
        x = -1.0 + 6.0 * a
        z = -2.0 - 1.0 * b
        y = 0.08 * max(0, x + 1.0)
        dot3(fr, (x, y, z), r=2.5, col=(210, 190, 160), a=0.75, glow=0.3)
    for zz in (-2.0, -3.0):
        line3(fr, [(-1.0, 0, zz), (5.0, 0.48, zz)], col=AMARILLO, w=2.4, a=0.8, glow=0.7)
    y = 0.08 * max(0, x + 1.0)
    ms = P.tfk(trailer(giro=-x / 0.21, caja=True), s=0.55, ry=-30 * clamp((x + 1.5) / 2.0), t=(x, y - 0.06 * clamp((x + 0.5)), z))
    draw_objects(fr, ms)
    hit = 0.9

    def ui(img, fx):
        kicker(img, 'RAMPA DE FRENADO DE EMERGENCIA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, 'GRAVA SUELTA + SUBIDA', eout(seg(u, hit, hit + 0.3)), size=30, border=AMARILLO, dot=False)
        recreacion(img, fx, 1.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, hit, 0.4), amp=16)


# 13. con el freno de motor, tu motor se vuelve un compresor (6 cilindros que bombean y sueltan aire)
def s_compresor(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 6.4, 50, 26, ty=1.0), K(0.4, 5.2, 24, 18, ty=1.0), K(2.4, 4.9, 10, 16, ty=1.0),
                       K(5, 4.8, 6, 16, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    M.cristal(fr.base, fr.fx, 'COMPRESOR', u, t0=0.05, cy=0.32, entrada='sube')
    ms = []
    th = np.linspace(0, 2 * math.pi, 30)
    for j in range(6):
        x = -1.5 + 0.6 * j
        ph = (t * 2.2 + j * (2 / 6)) % 1.0
        yp = 0.5 + 0.5 * math.cos(2 * math.pi * ph)
        top = 0.25 + 0.9 * yp
        for yy in (0.0, 1.4):
            line3(fr, [(x + 0.24 * math.cos(q), yy, 0.24 * math.sin(q)) for q in th], col=WHITE, w=1.6, a=0.7, glow=0.4)
        line3(fr, [(x - 0.24, 0, 0), (x - 0.24, 1.4, 0)], col=WHITE, w=1.6, a=0.6, glow=0.4)
        line3(fr, [(x + 0.24, 0, 0), (x + 0.24, 1.4, 0)], col=WHITE, w=1.6, a=0.6, glow=0.4)
        ms.append(named(M3.cyl(0.22, 0.25, METAL, n=16, shadow=0, gloss=0.7).tf(t=(x, top - 0.25, 0)), 'piston', rim=0.7))
        if yp > 0.88:                                     # arriba: suelta el aire (bocanada cian)
            for k in range(5):
                dot3(fr, (x + 0.05 * k, 1.5 + 0.15 * k, 0), r=4, col=CYAN, a=1.0 - 0.15 * k, glow=1.3)
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'MOTOR DE 6 CILINDROS · FRENO DE MOTOR PUESTO', 1290, seg(u, 0.2, 0.5), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. y frena sin gastar ni una gota de diésel (la gota cae, se detiene en el aire y se tacha: 0)
def s_diesel(t, fi, u, d):
    ug = Wu(14, 5) - 0.1                                   # «ni una gota»
    fr = Frame(cam(u, [K(-0.3, 3.0, -30, 10, ty=1.0), K(0.4, 2.6, -8, 6, ty=1.0), K(3, 2.5, 6, 6, ty=1.0)], cy=0.52))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9, beam=0.5)
    e = P.entrada(u, -0.2, 0.4, 'cae')
    y = 1.0 + max(0.0, -e['dy']) * 0.4 + 0.04 * math.sin(t * 3)
    gota = named(M3.sphere(0.32, (232, 176, 60), nu=24, nv=14, shadow=0, gloss=0.9).tf(s=(1, 1.25, 1), t=(0, y, 0)), 'gota', rim=0.8, gloss=0.9)
    punta = named(M3.cyl(0.3, 0.42, (232, 176, 60), n=24, shadow=0, gloss=0.9, r2=0.01).tf(t=(0, y + 0.18, 0)), 'gota', rim=0.8, gloss=0.9)
    draw_objects(fr, [gota, punta])
    gx, gy, _ = fr.cam.p1((0, y + 0.1, 0))

    def ui(img, fx):
        kicker(img, 'DIÉSEL QUE GASTA AL FRENAR', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.numero_golpe(img, fx, '0', 380, seg(u, ug, ug + 0.18), size=260, col=WHITE)
        if u > ug + 0.2:
            N.doodle_arrow_free(img, fx, gx - 230, gy - 230, gx + 230, gy + 230, t, seg(u, ug + 0.2, ug + 0.5), ROJO, seed=5)
            N.doodle_arrow_free(img, fx, gx + 230, gy - 230, gx - 230, gy + 230, t, seg(u, ug + 0.35, ug + 0.65), ROJO, seed=6)
        pill(img, fx, 540, 1360, 'NO SE INYECTA COMBUSTIBLE', eout(seg(u, ug + 0.6, ug + 0.9)), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ug + 0.18, 0.3), amp=18)


# 15. un motor de 15 litros: unos 600 caballos frenando («600 HP» de cristal detrás del motor)
def s_caballos(t, fi, u, d):
    us = Wu(15, 8) - 0.1                                   # «seiscientos»
    fr, ms = escena_camion(t, u, [K(-0.3, 3.6, -50, 20, tx=1.9, ty=0.7), K(0.4, 3.0, -30, 14, tx=1.9, ty=0.8),
                                  K(us, 2.6, -6, 10, tx=1.9, ty=0.8), K(5, 2.5, -2, 10, tx=1.9, ty=0.8)],
                           cy=0.6, roll=-3, motor=True, mont=False, vel=3.0)
    M.cristal(fr.base, fr.fx, '600 HP', u, t0=us, cy=0.3, entrada='zoom')
    draw_objects(fr, ms, xray=1.0, keep=('in',))

    def ui(img, fx):
        kicker(img, 'MOTOR DE 15 LITROS · FRENANDO', 150, seg(u, -0.1, 0.2), col=AZULC)
        n = int(600 * P.eout4(seg(u, us, us + 0.8)))
        texto(img, fx, 540, 1250, f'≈ {n} caballos', 64, AMARILLO, seg(u, us, us + 0.2), f='mono', glow=0.4)
        pill(img, fx, 540, 1350, 'A ALTAS REVOLUCIONES', eout(seg(u, us + 0.6, us + 0.9)), size=24, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.3, 0.3), amp=14)


def letrero(img, fx, cx, cy, w, k, t, ang0=-14.0):
    """Letrero de carretera (blanco, letras negras) que cae y se balancea. Ilustración, no foto."""
    if k <= 0.01:
        return
    h = int(w * 0.62)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=(244, 244, 240, 255))
    dl.rounded_rectangle((10, 10, w - 11, h - 11), radius=12, outline=(20, 20, 22, 255), width=7)
    for j, (tx, sz) in enumerate((('ENGINE', 0.17), ('BRAKES', 0.17), ('PROHIBITED', 0.12))):
        dl.text((w / 2, h * (0.25 + 0.25 * j)), tx, font=M.font('sansx', int(w * sz)), fill=(20, 20, 22, 255), anchor='mm')
    drop = eout(clamp(k * 1.4), 3)
    tt = max(0.0, k - 0.6)
    ang = ang0 * (1 - drop) + 6.0 * math.exp(-5 * tt) * math.cos(12 * tt) * (1 if k > 0.6 else 0)
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    y = cy - 600 * (1 - drop)
    img.paste(lay, (int(cx - lay.width / 2), int(y - lay.height / 2)), lay)
    # poste
    ImageDraw.Draw(img).rectangle((cx - 9, y + h / 2 - 10, cx + 9, y + h / 2 + 420), fill=(150, 152, 158))


# 16. truena tanto que en algunos pueblos de EE. UU. hay letreros que lo prohíben (cae el letrero)
def s_letrero(t, fi, u, d):
    ul = Wu(16, 9) - 0.15                                  # «hay letreros»
    fr, ms = escena_camion(t, u, [K(-0.3, 8.5, 60, 6, tx=-0.4, ty=1.0), K(0.4, 8.0, 36, 4, tx=-0.4, ty=1.0),
                                  K(3, 7.8, 30, 4, tx=-0.4, ty=1.0)], cy=0.66, roll=-3, vel=4.0)
    draw_objects(fr, ms)
    cx, cy = chimenea_px(fr)

    def ui(img, fx):
        tronido(img, fx, cx, cy, t, k=1.0, escala=0.9)
        kicker(img, 'EN ALGUNOS PUEBLOS DE ESTADOS UNIDOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        k = seg(u, ul, ul + 0.6)
        letrero(img, fx, 540, 560, 560, k, t)
        if k > 0.6:
            doodle_circle(img, fx, 540, 560, 330, 230, t, k=seg(u, ul + 0.4, ul + 0.8), col=ROJO, seed=8)
        pill(img, fx, 540, 900, 'ILUSTRACIÓN', seg(u, ul + 0.4, ul + 0.6), size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ul + 0.42, 0.3), amp=14)


# 17. el trailero baja en cambio corto y con el freno de motor puesto (palanca en H y tacómetro)
def s_cambio(t, fi, u, d):
    uc = Wu(17, 5) - 0.1                                   # «cambio corto»
    um = Wu(17, 9) - 0.1                                   # «freno de motor»
    fr, ms = escena_camion(t, u, [K(-0.3, 9.5, -70, 14, tx=-0.4, ty=0.8), K(0.4, 8.6, -40, 10, tx=-0.4, ty=0.8),
                                  K(4, 8.2, -32, 10, tx=-0.4, ty=0.8)], cy=0.78, roll=-6, vel=3.2)
    draw_objects(fr, ms)
    cx, cy = chimenea_px(fr, z=-0.5)

    def ui(img, fx):
        d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        k0 = eout(seg(u, -0.1, 0.2))
        ox, oy, s = 330, 640, 120
        for gx in (-1, 0, 1):                                # rejilla en H
            d.line([(ox + gx * s, oy - s), (ox + gx * s, oy + s)], fill=M.scale_c(WHITE, 0.8 * k0), width=6)
            df.line([(ox + gx * s, oy - s), (ox + gx * s, oy + s)], fill=M.scale_c(CYAN, 0.4 * k0), width=14)
        d.line([(ox - s, oy), (ox + s, oy)], fill=M.scale_c(WHITE, 0.8 * k0), width=6)
        kc = P.resorte(seg(u, uc, uc + 0.5))
        px, py = lerp(ox + s, ox - s, kc), lerp(oy - s, oy + s, kc)
        d.ellipse((px - 34, py - 34, px + 34, py + 34), fill=(20, 20, 24), outline=AMARILLO, width=6)
        df.ellipse((px - 44, py - 44, px + 44, py + 44), fill=M.scale_c(AMARILLO, 0.35))
        d.text((ox, oy + s + 60), 'CAMBIO CORTO', font=M.font('mono', 30), fill=M.scale_c(AMARILLO, eout(seg(u, uc, uc + 0.3))), anchor='mm')
        # tacómetro
        tx, ty, r = 770, 650, 150
        d.arc((tx - r, ty - r, tx + r, ty + r), 150, 390, fill=M.scale_c(WHITE, 0.8 * k0), width=6)
        df.arc((tx - r, ty - r, tx + r, ty + r), 300, 390, fill=M.scale_c(ROJO, 0.6 * k0), width=16)
        a = math.radians(170 + 170 * (0.3 + 0.45 * P.eout4(seg(u, uc, uc + 0.7))))
        d.line([(tx, ty), (tx + r * 0.85 * math.cos(a), ty + r * 0.85 * math.sin(a))], fill=ROJO, width=7)
        d.text((tx, ty + 70), 'RPM', font=M.font('mono', 28), fill=M.scale_c(GRIS, k0), anchor='mm')
        kicker(img, 'ASÍ BAJA UN TRAILERO', 150, k0, col=AZULC)
        pill(img, fx, 540, 900, '+ FRENO DE MOTOR PUESTO', eout(seg(u, um, um + 0.3)), size=32, border=AMARILLO, dot=False)
        tronido(img, fx, cx, cy, t, k=seg(u, um, um + 0.2), escala=0.8)
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. Mándaselo a tu compa trailero (el tráiler pasa junto a la cámara de noche con los faros)
def s_compa(t, fi, u, d):
    fr, ms = escena_camion(t, u, [K(-0.3, 4.6, 100, 4, tx=1.5, ty=0.9), K(0.4, 4.0, 62, 2, tx=1.4, ty=0.9),
                                  K(3, 3.8, 54, 2, tx=1.4, ty=0.9)], cy=0.6, roll=-4, vel=5.0, beam=0.0)
    ms = trailer(giro=-t * 5 / 0.21, faros=1.6)
    draw_objects(fr, ms)
    fx_, fy_, _ = fr.cam.p1((2.36, 0.7, 0.33))

    def ui(img, fx):
        df = ImageDraw.Draw(fx)
        for j, r in enumerate((60, 120, 200)):
            df.ellipse((fx_ - r, fy_ - r * 0.6, fx_ + r, fy_ + r * 0.6), fill=M.scale_c((255, 220, 150), 0.35 / (j + 1)))
        P.titulo_golpe(img, fx, [('Mándaselo a tu', 'sans'), ('compa trailero.', 'serif')], 230, seg(u, 0.0, 0.15), size=80)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


# 19. para que sepa que su tráiler no truena… está frenando (el tráiler viene de frente; el loop regresa a la Tierra)
def s_final(t, fi, u, d):
    fr, ms = escena_camion(t, u, [K(-0.3, 9.0, 20, 8, tx=0.0, ty=1.0), K(0.4, 7.8, 8, 6, tx=0.0, ty=1.0),
                                  K(d, 7.2, 4, 6, tx=0.0, ty=1.0)], cy=0.62, roll=-7, vel=5.0)
    M.cristal(fr.base, fr.fx, 'FRENANDO', u, t0=Wu(19, 8) - 0.1, cy=0.36, entrada='golpe')
    draw_objects(fr, ms)
    cx, cy = chimenea_px(fr)

    def ui(img, fx):
        tronido(img, fx, cx, cy, t, k=1.0, escala=0.9)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45), sfx=[(UL + 0.12 + 0.11 * j, 'thud', 0.55) for j in range(7)]),
           dict(desde=1, fn=s_tronido, tr='golpe', sfx=[(0.1 + 0.12 * j, 'thud', 0.45) for j in range(6)]),
           dict(desde=2, fn=s_jake, tr='cristal', palabra='JAKE', sfx=[(0.5, 'tick', 0.6)]),
           dict(desde=3, fn=s_piston, tr='zoom', c=(0.62, 0.62), sfx=[(0.6, 'whoosh', 0.7), (1.0, 'click', 0.6)]),
           dict(desde=4, fn=s_sin, tr='wipe', sfx=[(1.5, 'bass', 0.5)]),
           dict(desde=5, fn=s_con, tr='cubo', sfx=[(1.6, 'click', 0.8), (1.6, 'tick2', 0.6)]),
           dict(desde=6, fn=s_sale, tr='iris', c=(0.56, 0.42), sfx=[(0.05, 'burst', 0.9), (0.05, 'sub', 0.6)]),
           dict(desde=7, fn=s_llantas, tr='deslizar', sfx=[(0.1 + 0.12 * j, 'thud', 0.4) for j in range(5)]),
           dict(desde=8, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(1.7, 'bass', 0.9)]),
           dict(desde=9, fn=s_balatas, tr='flash', sfx=[(0.6, 'riser', 0.4)]),
           dict(desde=10, fn=s_sinfrenos, tr='glitch', sfx=[(0.2, 'digital', 0.6)]),
           dict(desde=11, fn=s_cumbres, tr='whip_izq', sfx=[(1.5, 'chime_a', 0.5), (2.6, 'bass', 0.7)]),
           dict(desde=12, fn=s_rampa, tr='push', c=(0.5, 0.5), sfx=[(0.9, 'thud', 0.9), (0.95, 'burst', 0.4)]),
           dict(desde=13, fn=s_compresor, tr='cubo_izq', sfx=[(0.3 + 0.18 * j, 'tick', 0.4) for j in range(8)]),
           dict(desde=14, fn=s_diesel, tr='iris', c=(0.5, 0.48), sfx=[(1.2, 'bass', 0.8), (1.5, 'scribble', 0.6)]),
           dict(desde=15, fn=s_caballos, tr='golpe', c=(0.5, 0.55), sfx=[(1.9, 'chime_b', 0.5)]),
           dict(desde=16, fn=s_letrero, tr='rebanadas', sfx=[(2.6, 'slap', 0.9), (2.9, 'scribble', 0.6)]),
           dict(desde=17, fn=s_cambio, tr='giro', sfx=[(1.4, 'click', 0.9), (2.6, 'thud', 0.5)]),
           dict(desde=18, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7)]),
           dict(desde=19, loop=True, tr='remolino')]

if __name__ == '__main__':
    montaje.cli(globals())
