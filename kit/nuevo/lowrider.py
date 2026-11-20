"""Reel diario dom 22-nov-2026 18:00 (propuesto) — «Tu lowrider no brinca… lo empuja el aceite.»
Hidráulica de lowrider: en cada esquina un cilindro hidráulico en lugar del resorte y el amortiguador de fábrica; una
bomba con motor eléctrico de 12 V mete aceite (fluido hidráulico) que no se comprime; switches con solenoides y «dumps»
para bajarlo (Engineer Fix 2026, Speedhunters). Un equipo básico (adelante, atrás y de lado) lleva 2 bombas y 4
baterías; cada batería en serie suma 12 V (Speedhunters); para brincar (hop) se le meten más bombas y baterías.
Historia: cultura lowrider nacida en comunidades mexicoamericanas (chicanas) del sur de California tras la Segunda
Guerra Mundial; en 1958 el Código Vehicular de California (sección 24008) prohibió que alguna parte del carro quedara
más abajo que la parte baja de los rines (Engineer Fix); a finales de los 50 llegaron los hidráulicos (bombas de avión
de desecho, Eternal Rollerz) para subirlo y bajarlo con un botón.
Error (segundo gancho): brincarlo sin reforzar el chasis: el bastidor se dobla o se cuartea; por eso se le sueldan
placas de acero de 3/16 o 1/4 de pulgada (≈ 5 a 6 mm) (Engineer Fix; Speedhunters: «frames are wrapped»).
Física: principio de Pascal (la presión se transmite igual a todo el líquido; F = P × A): el pistón chico empuja con
poca fuerza y el grande entrega más (jeringas unidas).
Comunidad: lowriders y clubes. Inicio tipo 2 (cae y rebota): el carro cae desde arriba, rebota en sus pistones, sacudida
y el título se estrella («ACEITE» de cristal detrás). En el loop el carro brinca cada vez más alto hasta salir por
arriba y vuelve a caer.
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
El carro (sin marca), el equipo, el bastidor y las jeringas son esquemas (ESQUEMA / EJEMPLO).
Datos y fuentes: guiones/2026-11-22_lowrider.txt.
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import tubo, _B, texto, esquema, golpe_k, sacudir, K, camara

M3 = M.M3
TEMA = 'lowrider'
TXT = ['Tu lowrider no brinca… lo empuja el aceite.',
       'Nació con la raza mexicana en California:',
       'en 1958, la ley prohibió ir más bajo que el rin.',
       'La respuesta fue subirlo y bajarlo con un botón.',
       'En cada llanta, en lugar del amortiguador,',
       'hay un cilindro hidráulico.',
       'Una bomba eléctrica le mete aceite,',
       'y el aceite no se deja apretar.',
       'Prueba con dos jeringas unidas:',
       'aprietas la chiquita y la grande empuja con más fuerza.',
       'Y aquí viene el error:',
       'brincarlo sin reforzar el chasis.',
       'Cada aterrizaje dobla el bastidor de fábrica,',
       'hasta que se cuartea.',
       'Por eso los de verdad le sueldan placas de acero de 5 o 6 milímetros.',
       '¿Y de dónde sale tanta fuerza?',
       'De baterías de 12 volts puestas en fila.',
       'Un equipo básico lleva 2 bombas y 4 baterías;',
       'para brincar, le meten más.',
       'Con el switch, el aceite entra de golpe al cilindro de adelante,',
       'la llanta empuja el piso y el carro sale volando.',
       'Es la ley de Pascal:',
       'la presión llega igual a todo el aceite,',
       'y en el pistón grande se vuelve fuerza.',
       'Mándaselo a tu compa del club lowrider.',
       'Y dile que no es magia… lo empuja el aceite.']
VOZ = ['Tu lowrider no brinca... lo empuja el aceite.',
       'Nació con la raza mexicana en California:',
       'en mil novecientos cincuenta y ocho, la ley prohibió ir más bajo que el rin.',
       'La respuesta fue subirlo y bajarlo con un botón.',
       'En cada llanta, en lugar del amortiguador,',
       'hay un cilindro hidráulico.',
       'Una bomba eléctrica le mete aceite,',
       'y el aceite no se deja apretar.',
       'Prueba con dos jeringas unidas:',
       'aprietas la chiquita y la grande empuja con más fuerza.',
       'Y aquí viene el error:',
       'brincarlo sin reforzar el chasis.',
       'Cada aterrizaje dobla el bastidor de fábrica,',
       'hasta que se cuartea.',
       'Por eso los de verdad le sueldan placas de acero de cinco o seis milímetros.',
       '¿Y de dónde sale tanta fuerza?',
       'De baterías de doce volts puestas en fila.',
       'Un equipo básico lleva dos bombas y cuatro baterías;',
       'para brincar, le meten más.',
       'Con el switch, el aceite entra de golpe al cilindro de adelante,',
       'la llanta empuja el piso y el carro sale volando.',
       'Es la ley de Pascal:',
       'la presión llega igual a todo el aceite,',
       'y en el pistón grande se vuelve fuerza.',
       'Mándaselo a tu compa del club lowrider.',
       'Y dile que no es magia... lo empuja el aceite.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_lowrider.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-22_lowrider_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
ROJO = (255, 60, 45)
VERDE = (60, 210, 120)
HULE = (26, 26, 29)
NEGRO = (22, 22, 25)
CROMO = (214, 216, 224)
DORADO = (245, 210, 110)
CANDY = (150, 18, 38)
ACEITE = (255, 170, 40)
VIDRIO = (24, 30, 38)

# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    if not os.path.exists(WORDS):
        T, _ = montaje.cargar(TEMA)
        for i, f in enumerate(VOZ):
            ws = [w for w in f.split() if montaje._norm(w)]
            a, b = T[i] if T else (0, 2)
            L = np.cumsum([0] + [len(w) + 1 for w in ws])[:-1] / max(1, sum(len(w) + 1 for w in ws))
            _WT[i] = [float(x) * (b - a) for x in L]
        return _WT
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
        base = next((x for x in L if x is not None), 0.0)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wp(i, palabra, n=0):
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ el lowrider (frente hacia +x, izquierda hacia +z)
LX, LZ = 0.98, 0.52
RT, rT = 0.26, 0.1
CYR = RT + rT
BASE = 0.24                       # altura del fondo de la carrocería (de paseo)


def rueda_rayos(x, z, giro=0.0, y=0.0):
    """Rin de rayos cromado (16 rayos) con cara blanca y birlo de orejas dorado."""
    out = 1 if z > 0 else -1
    c = (x, CYR + y, z)
    ms = [named(M3.torus(RT, rT, HULE, nu=40, nv=12, gloss=0.25).tf(rx=90, t=c), 'llanta', rim=0.45, gloss=0.25),
          named(M3.torus(RT * 0.98, 0.024, (242, 242, 238), nu=40, nv=6, gloss=0.4).tf(rx=90, t=(x, CYR + y, z + out * 0.075)), 'cara_blanca', rim=0.4),
          named(M3.cyl(RT * 0.72, 0.1, CROMO, n=30, shadow=0, gloss=0.95, y0=-0.05).tf(rx=90, t=c), 'rin', rim=0.9, gloss=0.95)]
    for j in range(16):
        b = M3.box(0.012, RT * 0.68, 0.012, (238, 239, 244), shadow=0, base=False, gloss=0.95).tf(t=(0, RT * 0.36, 0)).tf(rz=giro + j * 22.5)
        ms.append(named(b.tf(t=(x, CYR + y, z + out * 0.06)), 'rayo', rim=0.9))
    for j in range(3):
        b = M3.box(0.024, 0.12, 0.02, DORADO, shadow=0, base=False, gloss=0.95).tf(t=(0, 0.05, 0)).tf(rz=giro + 120 * j)
        ms.append(named(b.tf(t=(x, CYR + y, z + out * 0.1)), 'birlo', rim=0.9, glow=M.scale_c(DORADO, 0.15)))
    return ms


def _carroceria(color=CANDY, cajuela=0.0):
    """Carrocería en coordenadas locales (fondo en y = 0, centro en x = z = 0)."""
    b = []
    b.append(named(M3.rbox(3.3, 0.34, 1.12, 0.09, color, n=4, shadow=0, gloss=0.88), 'carroceria', rim=0.85, gloss=0.88))
    b.append(named(M3.rbox(1.5, 0.29, 0.98, 0.1, VIDRIO, n=4, shadow=0, gloss=0.95).tf(t=(-0.15, 0.3, 0)), 'vidrio', rim=0.9, gloss=0.95))
    b.append(named(M3.rbox(1.46, 0.06, 1.04, 0.03, color, n=3, shadow=0, gloss=0.88).tf(t=(-0.15, 0.58, 0)), 'techo', rim=0.85, gloss=0.88))
    b.append(tubo((1.68, 0.1, -0.52), (1.68, 0.1, 0.52), r=0.045, col=CROMO, name='defensa'))
    b.append(tubo((-1.68, 0.1, -0.52), (-1.68, 0.1, 0.52), r=0.045, col=CROMO, name='defensa'))
    for s in (-1, 1):
        b.append(tubo((-1.6, 0.21, s * 0.565), (1.6, 0.21, s * 0.565), r=0.012, col=CROMO, name='moldura'))
        _B(b, 0.04, 0.07, 0.16, (255, 245, 210), 1.65, 0.18, s * 0.36, name='faro', gloss=0.8, glow=(150, 140, 110))
        _B(b, 0.04, 0.09, 0.14, (200, 20, 20), -1.65, 0.18, s * 0.38, name='calavera', gloss=0.8, glow=(130, 20, 20))
    if cajuela > 0.01:
        tapa = M3.box(0.7, 0.03, 1.08, color, shadow=0, gloss=0.88, base=True).tf(t=(0.35, 0, 0)).tf(rz=-75 * cajuela).tf(t=(-1.6, 0.34, 0))
        b.append(named(tapa, 'tapa', rim=0.85, gloss=0.88))
    return b


def equipo(n_bat=4, n_bomba=2, k_bat=1.0, aceite=0.0, k_pop=1.0):
    """Bombas y baterías en la cajuela (coordenadas locales de la carrocería)."""
    e = []
    for j in range(n_bomba):
        z = -0.25 + 0.5 * j if n_bomba > 1 else 0.0
        e.append(named(M3.cyl(0.07, 0.36, CROMO, n=20, shadow=0, gloss=0.95, y0=-0.18).tf(rz=90, t=(-1.05, 0.14, z)), 'bomba', rim=0.9,
                       glow=M.scale_c(ACEITE, 0.5 * aceite) if aceite > 0.01 else None))
        _B(e, 0.18, 0.16, 0.16, (40, 42, 50), -1.32, 0.06, z, name='bomba', gloss=0.5)
    for j in range(n_bat):
        kk = P.resorte(clamp(k_pop * n_bat - j)) if k_pop < 1 else 1.0
        if kk <= 0.02:
            continue
        col_ = j // 4
        z = -0.42 + 0.28 * (j % 4)
        x = -1.5 + 0.0 * col_
        y = 0.04 + 0.22 * col_
        bat = M3.box(0.22 * kk, 0.18 * kk, 0.2 * kk, NEGRO, shadow=0, gloss=0.4, base=True).tf(t=(x, y, z))
        e.append(named(bat, 'bateria', rim=0.6, glow=M.scale_c(CYAN, 0.25 * k_bat)))
        _B(e, 0.04 * kk, 0.03 * kk, 0.04 * kk, (210, 40, 40), x + 0.06, y + 0.18 * kk, z - 0.05, name='bateria', gloss=0.6)
    return e


def carro(lift=(0, 0, 0, 0), giro=0.0, y=0.0, base=BASE, ruedas_y=(0, 0), color=CANDY, cajuela=0.0, interior=False,
          n_bat=4, n_bomba=2, aceite=(0, 0, 0, 0), k_pop=1.0, rz_extra=0.0):
    """Lowrider sin marca. lift = (DI, DD, TI, TD) subida de cada esquina por su cilindro; y = todo el carro en el aire
    (brinco); ruedas_y = (adelante, atrás) cuánto se despegan las llantas; aceite = brillo del aceite en cada cilindro."""
    fl, fr_, rl, rr = lift
    front, rear = (fl + fr_) / 2, (rl + rr) / 2
    left, right = (fl + rl) / 2, (fr_ + rr) / 2
    pitch = math.degrees(math.atan2(front - rear, 2 * LX)) + rz_extra
    roll = math.degrees(math.atan2(left - right, 2 * LZ))
    hmid = (front + rear) / 2
    b = _carroceria(color, cajuela)
    if interior:
        b += equipo(n_bat, n_bomba, aceite=max(aceite), k_pop=k_pop)
        b += bastidor()
    yb = base + hmid + y
    ms = P.tfk(P.tfk(b, rz=pitch, rx=-roll), t=(0, yb, 0))
    wy = {1: ruedas_y[0], -1: ruedas_y[1]}
    for sx in (1, -1):
        for sz in (1, -1):
            ms += rueda_rayos(sx * LX, sz * LZ, giro, y=wy[sx])
    for (sx, sz), ac in zip(((1, 1), (1, -1), (-1, 1), (-1, -1)), aceite):
        top = yb + (sx * LX) * math.tan(math.radians(pitch)) + (sz * (LZ - 0.12)) * math.tan(math.radians(roll)) + 0.06
        bot = CYR + wy[sx]
        c = tubo((sx * LX, bot, sz * (LZ - 0.12)), (sx * LX, max(bot + 0.05, top), sz * (LZ - 0.12)), r=0.075, col=CROMO, name='cilindro', gloss=0.95)
        if ac > 0.01:
            c.glow = M.scale_c(ACEITE, 0.8 * ac)
        ms.append(c)
    return ms


def bastidor(dobla=0.0, placas=0.0, estres=0.0, k=1.0):
    """Bastidor de escalera (coordenadas locales, bajo la carrocería). dobla 0–1 lo pandea al centro;
    estres lo pinta de rojo; placas 0–1 las placas de refuerzo soldadas a lo largo."""
    ms = []
    n = 14
    col = M.mixc((120, 124, 132), (255, 50, 40), estres)
    for s in (-1, 1):
        xs = np.linspace(-1.45, 1.45, n + 1)
        for a, b_ in zip(xs[:-1], xs[1:]):
            ya = 0.02 - dobla * 0.16 * math.sin(math.pi * (a + 1.45) / 2.9)
            yb = 0.02 - dobla * 0.16 * math.sin(math.pi * (b_ + 1.45) / 2.9)
            m = tubo((a, ya, s * 0.36), (b_, yb, s * 0.36), r=0.04, col=col, name='bastidor', gloss=0.6)
            if estres > 0.05:
                m.glow = M.scale_c((255, 40, 30), 0.5 * estres)
            ms.append(m)
            if placas > 0.01 and (a + 1.45) / 2.9 <= placas:
                p = M3.box(b_ - a, 0.1, 0.012, (196, 200, 210), shadow=0, gloss=0.8, base=False).tf(t=((a + b_) / 2, (ya + yb) / 2, s * 0.405))
                ms.append(named(p, 'placa', rim=0.8, gloss=0.8))
    for x in (-1.1, 0.0, 1.1):
        ms.append(tubo((x, 0.02, -0.36), (x, 0.02, 0.36), r=0.03, col=col, name='bastidor', gloss=0.6))
    return ms


def fila_baterias(n, k_pop=1.0, filas=1):
    """Baterías de 12 V grandes en fila (a lo largo de x), con sus bornes; k_pop 0–1 las va haciendo aparecer."""
    ms = []
    por = math.ceil(n / filas)
    for j in range(n):
        kk = P.resorte(clamp(k_pop * n - j)) if k_pop < 1 else 1.0
        if kk <= 0.02:
            continue
        f, c = j // por, j % por
        x = (c - (por - 1) / 2) * 0.62
        z = -f * 0.6
        bat = M3.rbox(0.48 * kk, 0.4 * kk, 0.36 * kk, 0.03, NEGRO, n=3, shadow=0, gloss=0.4).tf(t=(x, 0, z))
        ms.append(named(bat, 'bateria', rim=0.7, gloss=0.4))
        _B(ms, 0.07 * kk, 0.06 * kk, 0.07 * kk, (220, 40, 40), x + 0.14, 0.4 * kk, z, name='borne', gloss=0.7)
        _B(ms, 0.07 * kk, 0.06 * kk, 0.07 * kk, (60, 60, 66), x - 0.14, 0.4 * kk, z, name='borne', gloss=0.7)
        _B(ms, 0.3 * kk, 0.004, 0.2 * kk, (230, 230, 230), x, 0.4 * kk, z, name='etiqueta', gloss=0.2, glow=(40, 40, 40))
    return ms


def piso(fr, t, k=1.0, vel=0.0):
    """Pavimento con rayas amarillas que corren (si vel > 0)."""
    off = (t * vel) % 1.2
    for j in range(-6, 7):
        line3(fr, [(j * 1.2 - off, 0.005, 1.0), (j * 1.2 - off + 0.6, 0.005, 1.0)], col=AMARILLO, w=4, a=0.7 * k, glow=0.6)


def jeringas(img, fx, cx, cy, s, k=1.0, p=0.0, flechas=1.0, presion=0.0):
    """Dos jeringas unidas por una manguera con aceite (2D line-art que brilla). p 0–1: cuánto se aprieta la chica."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    wc, wg, H = 70 * s, 170 * s, 380 * s
    xc, xg = cx - 230 * s, cx + 200 * s
    top = cy - H / 2
    bajo = cy + H / 2
    dc = 200 * s * p
    dg = dc * (wc / wg) ** 2
    c = M.scale_c(WHITE, 0.9 * k)
    # aceite
    d.rectangle((xc - wc / 2, top + 40 * s + dc, xc + wc / 2, bajo), fill=M.scale_c(ACEITE, 0.85 * k))
    d.rectangle((xg - wg / 2, top + 120 * s - dg, xg + wg / 2, bajo), fill=M.scale_c(ACEITE, 0.85 * k))
    d.rectangle((xc, bajo - 10 * s, xg, bajo + 34 * s), fill=M.scale_c(ACEITE, 0.85 * k))
    df.rectangle((xc - wc / 2, top + 40 * s + dc, xg + wg / 2, bajo + 34 * s), fill=M.scale_c(ACEITE, 0.2 * k))
    for (x, w, y0) in ((xc, wc, top), (xg, wg, top + 60 * s)):
        d.line([(x - w / 2, y0), (x - w / 2, bajo), (x + w / 2, bajo), (x + w / 2, y0)], fill=c, width=int(6 * s))
    d.line([(xc, bajo + 40 * s), (xg, bajo + 40 * s)], fill=c, width=int(5 * s))
    d.line([(xc, bajo - 14 * s), (xg, bajo - 14 * s)], fill=c, width=int(3 * s))
    # émbolos
    for (x, w, yy) in ((xc, wc, top + 40 * s + dc), (xg, wg, top + 120 * s - dg)):
        d.rectangle((x - w / 2 + 4, yy - 16 * s, x + w / 2 - 4, yy), fill=(200, 200, 206))
        d.line([(x, yy - 16 * s), (x, yy - 160 * s)], fill=(200, 200, 206), width=int(10 * s))
        d.rectangle((x - w * 0.35, yy - 176 * s, x + w * 0.35, yy - 160 * s), fill=(200, 200, 206))
    if flechas > 0.01:
        N.doodle_arrow_free(img, fx, xc, top - 320 * s + dc, xc, top - 200 * s + dc, 0.0, flechas, AMARILLO, seed=3)
        dl = ImageDraw.Draw(img)
        a = flechas
        x0, y0 = xg, top + 120 * s - dg - 200 * s
        dl.line([(x0, y0), (x0, y0 - 220 * s * a)], fill=M.scale_c(ROJO, a), width=int(26 * s))
        dl.polygon([(x0 - 50 * s, y0 - 210 * s * a), (x0 + 50 * s, y0 - 210 * s * a), (x0, y0 - 290 * s * a)], fill=M.scale_c(ROJO, a))
        ImageDraw.Draw(fx).line([(x0, y0), (x0, y0 - 260 * s * a)], fill=M.scale_c(ROJO, 0.4 * a), width=int(40 * s))
    if presion > 0.01:
        for j in range(9):
            xx = lerp(xc, xg, j / 8)
            ya = bajo + 12 * s
            d.line([(xx, ya - 30 * s * presion), (xx, ya + 30 * s * presion)], fill=M.scale_c(CYAN, presion), width=4)
            d.line([(xx - 30 * s * presion, ya), (xx + 30 * s * presion, ya)], fill=M.scale_c(CYAN, presion), width=4)


def switchbox(img, fx, cx, cy, s, k=1.0, on=0.0, cual=0):
    """Caja de switches de lowrider (EJEMPLO): 3 palancas; la `cual` se sube con `on`."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    w, h = 420 * s, 230 * s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=int(30 * s), fill=(30, 30, 34), outline=M.scale_c(CROMO, k), width=int(6 * s))
    for j in range(3):
        x = cx - 120 * s + 120 * s * j
        d.ellipse((x - 30 * s, cy - 30 * s, x + 30 * s, cy + 30 * s), fill=(120, 122, 130))
        a = math.radians(-60 if (j == cual and on > 0.5) else 60)
        L = 90 * s
        d.line([(x, cy), (x + L * math.sin(a) * 0.3, cy - L * math.cos(a))], fill=CROMO, width=int(16 * s))
        led = (j == cual and on > 0.5)
        d.ellipse((x - 12 * s, cy + 60 * s, x + 12 * s, cy + 84 * s), fill=VERDE if led else (40, 60, 40))
        if led:
            df.ellipse((x - 40 * s, cy + 32 * s, x + 40 * s, cy + 112 * s), fill=M.scale_c(VERDE, 0.6))
    df.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=int(30 * s), outline=M.scale_c(CYAN, 0.25 * k), width=int(14 * s))


def cilindros_ab(img, fx, cx, cy, s, k=1.0, p=0.0, t=0.0):
    """Dos cilindros con pistón: con aire (se aprieta) y con aceite (no se mueve)."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    w, H = 220 * s, 520 * s
    for j, (x, liq) in enumerate(((cx - 220 * s, False), (cx + 220 * s, True))):
        top, bajo = cy - H / 2, cy + H / 2
        ypis = top + 60 * s + (260 * s * p if not liq else 10 * s * p)
        if liq:
            d.rectangle((x - w / 2, ypis, x + w / 2, bajo), fill=M.scale_c(ACEITE, 0.85 * k))
            df.rectangle((x - w / 2, ypis, x + w / 2, bajo), fill=M.scale_c(ACEITE, 0.2 * k))
        else:
            rng = np.random.RandomState(4)
            for q in range(26):
                xx = x - w / 2 + 20 * s + rng.rand() * (w - 40 * s)
                yy = ypis + 20 * s + ((rng.rand() + t * 0.6 * (1 + rng.rand())) % 1.0) * (bajo - ypis - 30 * s)
                d.ellipse((xx - 7 * s, yy - 7 * s, xx + 7 * s, yy + 7 * s), fill=AZULC)
                df.ellipse((xx - 12 * s, yy - 12 * s, xx + 12 * s, yy + 12 * s), fill=M.scale_c(AZULC, 0.4))
        d.line([(x - w / 2, top), (x - w / 2, bajo), (x + w / 2, bajo), (x + w / 2, top)], fill=M.scale_c(WHITE, 0.9 * k), width=int(6 * s))
        d.rectangle((x - w / 2 + 5, ypis - 22 * s, x + w / 2 - 5, ypis), fill=(206, 206, 212))
        d.line([(x, ypis - 22 * s), (x, ypis - 190 * s)], fill=(206, 206, 212), width=int(14 * s))
        texto(img, fx, x, bajo + 60 * s, 'ACEITE' if liq else 'AIRE', int(40 * s), ACEITE if liq else AZULC, k, f='mono', glow=0.3)


# ================================================================== escenas
# 0. gancho (inicio 2: cae y rebota). En el loop (u < −0.7) el carro brinca de adelante cada vez más alto; de −0.7 a
#    −0.25 sale disparado hacia arriba; desde −0.25 cae, rebota en sus pistones (sacudida) y el título se estrella.
U_CAE = -0.25
ALTO = 1.7


def altura_gancho(u):
    if u < -0.7:
        ph = ((u + 10) % 0.9) / 0.9
        amp = 0.12 + 0.3 * seg(u, -3.5, -0.7)
        return 0.0, amp * max(0.0, math.sin(math.pi * ph)) ** 1.5
    if u < U_CAE:
        return ALTO * P.eout4(seg(u, -0.7, U_CAE)), 0.0
    return ALTO * (1 - P.rebote(seg(u, U_CAE, 0.35))), 0.0


def s_gancho(t, fi, u, d):
    ue = Wp(0, 'empuja') - 0.12
    y, front = altura_gancho(u)
    land = U_CAE + 0.12
    fr = Frame(camara(u, [K(-3.5, 8.0, 30, 8, ty=0.9), K(-0.7, 7.5, 28, 8, ty=1.2), K(land, 6.8, 28, 7, ty=0.9), K(ue, 6.2, 28, 6, ty=0.85), K(5.0, 6.1, 28, 6, ty=0.85)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.7)
    M.cristal(fr.base, fr.fx, 'ACEITE', u, t0=-3.0, cy=0.42, entrada='golpe')
    sq = 0.06 * golpe_k(u, land, 0.3)
    ms = carro(lift=(front, front, 0, 0), y=y, ruedas_y=(y + max(0.0, front - 0.25), y), base=BASE - sq,
               aceite=(front * 3, front * 3, 0, 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'LOWRIDER · HIDRÁULICA', 150, seg(u, 0.25, 0.45), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu lowrider no brinca…', 'sans'), ('lo empuja el aceite.', 'serif')], 230, seg(u, 0.05, 0.2), size=72)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, land, 0.4), golpe_k(u, 0.2, 0.25)), amp=30)


# 1. Nació con la raza mexicana en California («RAZA» de cristal; el carro pasea bajito y despacio)
def s_raza(t, fi, u, d):
    ur = Wp(1, 'raza') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.5, -50, 6, ty=0.6), K(0.35, 6.5, -28, 5, ty=0.6), K(d, 6.4, -28, 5, ty=0.6)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.6, beam_x=0.7)
    M.cristal(fr.base, fr.fx, 'RAZA', u, t0=ur - 0.05, cy=0.4, entrada='sube')
    e = P.entrada(u, -0.25, 0.3, 'desliza')
    draw_objects(fr, P.tfk(carro(giro=-t * 60, base=0.12), t=(e['dy'], 0, 0)))
    piso(fr, t, vel=0.8)

    def ui(img, fx):
        kicker(img, 'SUR DE CALIFORNIA · DESPUÉS DE LA GUERRA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, 'FAMILIAS MEXICANAS · CULTURA CHICANA', eout(seg(u, ur + 0.2, ur + 0.5)), size=28, border=AMARILLO, dot=False)
        pill(img, fx, 540, 1410, '«LOW AND SLOW»: BAJITO Y DESPACIO', eout(seg(u, ur + 0.6, ur + 0.9)), size=24, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. en 1958 la ley prohibió ir más bajo que el rin (el carro aplastado; línea roja a la altura del rin)
def s_1958(t, fi, u, d):
    ul = Wp(2, 'ley') - 0.1
    ur = Wp(2, 'rin') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.4, 0, 2, tx=0.9, ty=0.3), K(0.35, 3.6, 4, 2, tx=1.0, ty=0.25), K(d, 3.5, 6, 2, tx=1.0, ty=0.25)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9)
    M.cristal(fr.base, fr.fx, '1958', u, t0=-0.3, cy=0.36, entrada='golpe')
    draw_objects(fr, carro(base=0.08))
    yr = CYR - RT * 0.72
    line3(fr, [(-2.0, yr, 0.75), (3.0, yr, 0.75)], col=ROJO, w=5, a=seg(u, ur - 0.2, ur), glow=1.2)

    def ui(img, fx):
        kicker(img, 'CÓDIGO VEHICULAR DE CALIFORNIA · 24008', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1150, 'PROHIBIDO: MÁS BAJO QUE EL RIN', eout(seg(u, ur, ur + 0.3)), size=34, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.0, 0.3), golpe_k(u, ur + 0.1, 0.3)), amp=18)


# 3. La respuesta fue subirlo y bajarlo con un botón (switch; el carro sube y baja)
def s_boton(t, fi, u, d):
    us = Wp(3, 'subirlo') - 0.1
    ub = Wp(3, 'bajarlo') - 0.1
    h = 0.35 * P.eout4(seg(u, us, us + 0.3)) * (1 - P.eout4(seg(u, ub, ub + 0.3)))
    up = Wp(3, 'boton') - 0.1
    h = max(h, 0.3 * P.eout4(seg(u, up, up + 0.25)))
    fr = Frame(camara(u, [K(-0.3, 7.0, 40, 8, ty=0.7), K(0.35, 6.2, 28, 6, ty=0.7), K(d, 6.1, 28, 6, ty=0.7)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.6)
    draw_objects(fr, carro(lift=(h, h, h, h), aceite=(h * 3,) * 4, base=0.1))

    def ui(img, fx):
        kicker(img, 'LA RESPUESTA · HIDRÁULICOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        switchbox(img, fx, 540, 420, 1.0, k=seg(u, -0.25, 0.0), on=1.0 if (us < u < ub or u > up) else 0.0, cual=1)
        pill(img, fx, 540, 600, 'SUBE · BAJA', eout(seg(u, us, us + 0.3)), size=30, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, us + 0.25, 0.25), golpe_k(u, ub + 0.25, 0.25)), amp=12)


# 4. En cada llanta, en lugar del amortiguador (rayos X: AMORTIGUADOR tachado)
def s_amortiguador(t, fi, u, d):
    ua = Wp(4, 'amortiguador') - 0.1
    x = seg(u, -0.1, 0.25)
    fr = Frame(camara(u, [K(-0.3, 5.3, 60, 14, ty=0.6), K(0.35, 4.1, 36, 10, tx=0.6, ty=0.5), K(d, 4.0, 32, 10, tx=0.7, ty=0.5)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    draw_objects(fr, carro(lift=(0.15, 0.15, 0.15, 0.15), base=0.12), xray=0.85 * x, keep=('cilindro',))
    cx, cy_, _ = fr.cam.p1((LX, 0.62, LZ - 0.12))

    def ui(img, fx):
        kicker(img, 'RAYOS X · CADA ESQUINA', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.pill_tachada(img, fx, 540, 1330, 'RESORTE Y AMORTIGUADOR', seg(u, 0.0, 0.25), seg(u, ua + 0.2, ua + 0.6), t, size=32)
        doodle_circle(img, fx, cx, cy_, 120, 200, t, k=seg(u, ua, ua + 0.4), col=AMARILLO, seed=2)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. hay un cilindro hidráulico (la cámara entra a la esquina: «CILINDRO» de cristal; pistón cromado que sube)
def s_cilindro(t, fi, u, d):
    uc = Wp(5, 'cilindro') - 0.1
    h = 0.25 + 0.15 * math.sin(t * 3)
    fr = Frame(camara(u, [K(-0.3, 2.6, 20, 8, tx=LX, ty=0.55, tz=0.4), K(0.35, 2.2, 40, 6, tx=LX, ty=0.55, tz=0.4), K(d, 2.15, 44, 6, tx=LX, ty=0.55, tz=0.4)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'CILINDRO', u, t0=uc - 0.05, cy=0.3, entrada='golpe')
    draw_objects(fr, carro(lift=(h, h, 0.1, 0.1), aceite=(0.7, 0.7, 0, 0), base=0.12), xray=0.85, keep=('cilindro',))

    def ui(img, fx):
        rec_frame(img, t, k=1.0, zoom_label='x1.8')
        kicker(img, 'CILINDRO HIDRÁULICO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1390, 'UNO EN CADA LLANTA', eout(seg(u, uc + 0.3, uc + 0.6)), size=30, border=ACEITE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.15, 0.3), amp=12)


# 6. Una bomba eléctrica le mete aceite (cajuela en rayos X: bombas y mangueras con aceite que corre)
def s_bomba(t, fi, u, d):
    ub = Wp(6, 'bomba') - 0.1
    ua = Wp(6, 'aceite') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, -50, 24, tx=-0.6, ty=0.5), K(0.35, 3.6, -30, 26, tx=-0.7, ty=0.5), K(d, 3.5, -26, 26, tx=-0.7, ty=0.5)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8)
    ac = seg(u, ua, ua + 0.3)
    draw_objects(fr, carro(interior=True, aceite=(ac, ac, ac, ac), base=0.12), xray=0.85, keep=('bomba', 'bateria', 'cilindro'))
    for s in (-1, 1):
        pts = [(-1.05, BASE - 0.12 + 0.14, s * 0.25), (0.0, BASE - 0.12 + 0.05, s * 0.3), (LX, BASE - 0.12 + 0.05, s * (LZ - 0.12))]
        line3(fr, pts, col=ACEITE, w=4, a=0.4 + 0.6 * ac, glow=0.6 + ac)
        for j in range(6):
            q = (t * 1.2 + j / 6) % 1.0
            dot3(fr, (lerp(-1.05, LX, q), BASE - 0.05, s * lerp(0.25, LZ - 0.12, q)), r=7, col=ACEITE, a=ac, glow=1.4)
    bx, by, _ = fr.cam.p1((-1.15, 0.5, 0))

    def ui(img, fx):
        kicker(img, 'EN LA CAJUELA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, bx, by - 200, 'BOMBA ELÉCTRICA', eout(seg(u, ub, ub + 0.3)), size=30, border=CYAN)
        pill(img, fx, 540, 1390, 'ACEITE A LOS CILINDROS', eout(seg(u, ua, ua + 0.3)), size=28, border=ACEITE, dot=False)
        esquema(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. y el aceite no se deja apretar (aire contra aceite)
def s_apretar(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 20, 10, ty=1.0), K(0.35, 4.6, 6, 8, ty=1.0), K(d, 4.5, 2, 8, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    p = P.eout4(seg(u, 0.2, 0.9))

    def ui(img, fx):
        kicker(img, 'LA PRUEBA · AIRE CONTRA ACEITE', 150, seg(u, -0.1, 0.2), col=AZULC)
        cilindros_ab(img, fx, 540, 880, 1.25, k=seg(u, -0.25, 0.0), p=p, t=t)
        pill(img, fx, 540, 1350, 'EL ACEITE NO SE COMPRIME', eout(seg(u, 0.8, 1.1)), size=30, border=ACEITE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.9, 0.25), amp=10)


# 8. Prueba con dos jeringas unidas
def s_jeringas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -20, 10, ty=1.0), K(0.35, 4.6, -6, 8, ty=1.0), K(d, 4.5, -2, 8, ty=1.0)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.5)

    def ui(img, fx):
        kicker(img, 'HAZLO EN TU CASA', 150, seg(u, -0.1, 0.2), col=AZULC)
        jeringas(img, fx, 540, 900, 1.3, k=seg(u, -0.25, 0.0), p=0.0, flechas=0.0)
        pill(img, fx, 540, 1380, 'DOS JERINGAS + UNA MANGUERITA', eout(seg(u, 0.3, 0.6)), size=28, border=CYAN, dot=False)
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. aprietas la chiquita y la grande empuja con más fuerza («FUERZA» de cristal)
def s_fuerza(t, fi, u, d):
    uc = Wp(9, 'chiquita') - 0.1
    uf = Wp(9, 'fuerza') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, 10, 8, ty=1.0), K(0.35, 4.2, 2, 6, ty=1.0), K(d, 4.1, 0, 6, ty=1.0)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9)
    M.cristal(fr.base, fr.fx, 'FUERZA', u, t0=uf - 0.05, cy=0.24, entrada='zoom')
    p = P.eout4(seg(u, uc, uc + 0.8))

    def ui(img, fx):
        jeringas(img, fx, 540, 980, 1.3, k=1.0, p=p, flechas=seg(u, uf - 0.2, uf + 0.2))
        texto(img, fx, 300, 1420, 'POQUITA', 40, AMARILLO, seg(u, uc, uc + 0.3), f='mono', glow=0.3)
        texto(img, fx, 800, 1420, 'MUCHA', 40, ROJO, seg(u, uf, uf + 0.3), f='mono', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uf + 0.15, 0.3), amp=16)


# 10. SEGUNDO GANCHO: el error («ERROR» de cristal; el carro llega girando)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.8, -60, 14, ty=0.75), K(0.35, 6.2, -28, 8, ty=0.75), K(d, 6.1, -28, 8, ty=0.75)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ERROR', u, t0=0.0, cy=0.4, entrada='golpe')
    e = P.entrada(u, -0.2, 0.3, 'gira')
    draw_objects(fr, P.tfk(carro(base=0.12), s=max(0.05, e['escala']), ry=math.degrees(e['giro'])))

    def ui(img, fx):
        kicker(img, 'Y AQUÍ VIENE…', 150, seg(u, -0.1, 0.1), col=(255, 120, 110))
        P.titulo_golpe(img, fx, [('El error', 'sans'), ('que dobla el carro.', 'serif')], 230, seg(u, 0.1, 0.25), size=84)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.35), amp=22)


# 11. brincarlo sin reforzar el chasis (el carro brinca; rayos X: el bastidor de fábrica se pone rojo)
def s_brinca(t, fi, u, d):
    uc = Wp(11, 'chasis') - 0.1
    ph = ((u + 0.2) % 1.0)
    y = 0.6 * max(0.0, math.sin(math.pi * ph)) if u > -0.2 else 0.0
    x = seg(u, uc - 0.1, uc + 0.2)
    fr = Frame(camara(u, [K(-0.3, 7.5, 40, 8, ty=0.9), K(0.35, 6.5, 28, 6, ty=0.9), K(d, 6.4, 28, 6, ty=0.9)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.5)
    ms = carro(lift=(0.3 + y, 0.3 + y, 0, 0), y=0.0, ruedas_y=(max(0.0, y - 0.25), 0), aceite=(1, 1, 0, 0), base=0.12)
    ms += P.tfk(bastidor(estres=x * (0.5 + 0.5 * y / 0.6)), t=(0, 0.12, 0))
    draw_objects(fr, ms, xray=0.8 * x, keep=('bastidor', 'cilindro'))

    def ui(img, fx):
        kicker(img, 'SIN REFORZAR', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        pill(img, fx, 540, 1350, 'BASTIDOR DE FÁBRICA', eout(seg(u, uc, uc + 0.3)), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    land = (1.0 - 0.2) % 1.0
    return sacudir(finish(fr, fi), t, golpe_k(u, land, 0.3), amp=16)


# 12. Cada aterrizaje dobla el bastidor de fábrica (solo el bastidor; se pandea en cada golpe)
def s_dobla(t, fi, u, d):
    ud = Wp(12, 'dobla') - 0.1
    hits = [ud, ud + 0.7, ud + 1.4]
    db = sum(0.3 * P.eout4(seg(u, h, h + 0.15)) for h in hits)
    fr = Frame(camara(u, [K(-0.3, 5.0, 60, 34, ty=0.6), K(0.35, 4.4, 44, 28, ty=0.6), K(d, 4.3, 40, 28, ty=0.6)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    ms = P.tfk(bastidor(dobla=db, estres=min(1.0, db * 1.4)), t=(0, 0.6, 0))
    draw_objects(fr, ms)
    k_hit = max(golpe_k(u, h + 0.15, 0.3) for h in hits)

    def ui(img, fx):
        kicker(img, 'EL BASTIDOR · VISTA SOLA', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1300, f'ATERRIZAJE {sum(1 for h in hits if u > h)}', 44, ROJO, seg(u, ud, ud + 0.2), f='mono', glow=0.3)
        esquema(img, fx, 1.0, txt='ESCALA EXAGERADA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, k_hit, amp=20)


# 13. hasta que se cuartea (zoom digital a la grieta; «CUARTEA» de cristal)
def s_cuartea(t, fi, u, d):
    uc = Wp(13, 'cuartea') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.8, 30, 20, ty=0.5, tz=0.3), K(0.35, 1.8, 20, 14, ty=0.5, tz=0.3), K(d, 1.75, 18, 14, ty=0.5, tz=0.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    M.cristal(fr.base, fr.fx, 'CUARTEA', u, t0=uc - 0.05, cy=0.28, entrada='golpe')
    draw_objects(fr, P.tfk(bastidor(dobla=0.9, estres=1.0), t=(0, 0.6, 0)))
    gx, gy, _ = fr.cam.p1((0.0, 0.46, 0.36))

    def ui(img, fx):
        rec_frame(img, t, k=1.0, zoom_label='x2.0')
        if u > uc:
            kk = seg(u, uc, uc + 0.3)
            dl = ImageDraw.Draw(img)
            pts = [(gx - 10, gy - 70), (gx + 14, gy - 30), (gx - 8, gy + 4), (gx + 18, gy + 40), (gx - 4, gy + 80)]
            n = max(2, int(len(pts) * kk))
            dl.line(pts[:n], fill=WHITE, width=6)
            ImageDraw.Draw(fx).line(pts[:n], fill=(255, 120, 80), width=18)
            doodle_circle(img, fx, gx, gy, 150, 150, t, k=kk, col=ROJO, seed=7)
        kicker(img, 'METAL CANSADO', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.35), amp=20)


# 14. le sueldan placas de acero de 5 o 6 milímetros (chispas de soldadura que avanzan; cota)
def s_placas(t, fi, u, d):
    ucm = Wp(14, 'cinco') - 0.1
    pl = P.eout4(seg(u, 0.0, max(0.8, ucm + 0.6)))
    fr = Frame(camara(u, [K(-0.3, 4.8, 56, 30, ty=0.6), K(0.35, 4.0, 40, 24, ty=0.6), K(d, 3.9, 36, 24, ty=0.6)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8, beam=0.5)
    draw_objects(fr, P.tfk(bastidor(placas=pl), t=(0, 0.6, 0)))
    xw = -1.45 + 2.9 * pl
    rng = np.random.RandomState(int(t * 24) % 1000)
    if pl < 0.99:
        for j in range(18):
            a = rng.rand() * 2 * math.pi
            r = rng.rand() * 0.3
            dot3(fr, (xw + r * math.cos(a), 0.62 + abs(r * math.sin(a)), 0.42), r=4, col=(255, 210, 120), a=1.0, glow=1.6)
        dot3(fr, (xw, 0.62, 0.42), r=22, col=(255, 240, 200), a=1.0, glow=2.4)
    cx, cy_, _ = fr.cam.p1((0.6, 0.62, 0.42))

    def ui(img, fx):
        kicker(img, 'LOS DE VERDAD · REFUERZO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, 'PLACAS DE ACERO SOLDADAS', eout(seg(u, 0.2, 0.5)), size=30, border=AMARILLO, dot=False)
        texto(img, fx, 540, 1430, '5–6 mm  (3/16″ – 1/4″)', 48, AMARILLO, seg(u, ucm, ucm + 0.25), f='mono', glow=0.4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. ¿Y de dónde sale tanta fuerza? (la cajuela se abre; «?» de garabato)
def s_dedonde(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.2, -60, 14, ty=0.6), K(0.35, 5.2, -36, 18, tx=-0.6, ty=0.5), K(d, 5.1, -32, 18, tx=-0.6, ty=0.5)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.5)
    draw_objects(fr, carro(cajuela=P.eout4(seg(u, 0.0, 0.5)), base=0.12))

    def ui(img, fx):
        kicker(img, 'ABRE LA CAJUELA', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 470, '?', 260, AMARILLO, eout(seg(u, 0.2, 0.45)), f='sansx', glow=0.6)
        doodle_circle(img, fx, 540, 490, 150, 170, t, k=seg(u, 0.35, 0.7), col=AMARILLO, seed=3)
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. De baterías de 12 volts puestas en fila (la transición cae como «12 VOLTS» de cristal; las baterías se forman)
def s_baterias(t, fi, u, d):
    uf = Wp(16, 'fila') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, 30, 22, ty=0.3), K(0.35, 3.3, 14, 18, ty=0.3), K(d, 3.2, 10, 18, ty=0.3)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9)
    kp = seg(u, -0.2, uf + 0.4)
    n = 4
    draw_objects(fr, fila_baterias(n, kp))
    nb = max(0, min(n, int(kp * n + 0.999)))
    for j in range(nb - 1):
        x0 = (j - 1.5) * 0.62 + 0.14
        x1 = (j + 1 - 1.5) * 0.62 - 0.14
        line3(fr, [(x0, 0.46, 0), ((x0 + x1) / 2, 0.6, 0), (x1, 0.46, 0)], col=CYAN, w=5, a=1.0, glow=1.4)

    def ui(img, fx):
        kicker(img, 'EN SERIE · CADA UNA SUMA 12 V', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1330, f'{12 * max(1, nb)} V', 150, CYAN, 1.0, f='mono', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uf + 0.4, 0.3), amp=12)


# 17. Un equipo básico lleva 2 bombas y 4 baterías (cajuela en rayos X con sus nombres)
def s_equipo(t, fi, u, d):
    ub = Wp(17, 'bombas') - 0.1
    ut = Wp(17, 'baterias') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.4, -70, 34, tx=-1.1, ty=0.4), K(0.35, 3.4, -40, 40, tx=-1.2, ty=0.4), K(d, 3.3, -36, 40, tx=-1.2, ty=0.4)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8)
    draw_objects(fr, carro(interior=True, base=0.12), xray=0.9, keep=('bomba', 'bateria'))

    def ui(img, fx):
        kicker(img, 'EQUIPO BÁSICO · ADELANTE, ATRÁS Y DE LADO', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 300, 1320, '2 BOMBAS', 56, CYAN, seg(u, ub, ub + 0.2), f='sansx', glow=0.4)
        texto(img, fx, 780, 1320, '4 BATERÍAS', 56, CYAN, seg(u, ut, ut + 0.2), f='sansx', glow=0.4)
        esquema(img, fx, 1.0, y=1420)
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. para brincar, le meten más (se llena la cajuela: 8 baterías)
def s_mas(t, fi, u, d):
    um = Wp(18, 'mas') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, -40, 30, ty=0.2, tz=-0.3), K(0.35, 4.0, -20, 30, ty=0.2, tz=-0.3), K(d, 3.9, -16, 30, ty=0.2, tz=-0.3)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8)
    kp = 0.5 + 0.5 * seg(u, um - 0.1, um + 0.6)
    draw_objects(fr, fila_baterias(8, kp, filas=2))
    nb = max(4, int(kp * 8 + 0.999))

    def ui(img, fx):
        kicker(img, 'PARA BRINCAR · MÁS BOMBAS Y MÁS BATERÍAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1330, f'{12 * nb} V', 150, ROJO if nb > 4 else CYAN, 1.0, f='mono', glow=0.5)
        esquema(img, fx, 1.0, y=1440, txt='EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.6, 0.3), amp=14)


# 19. Con el switch, el aceite entra de golpe al cilindro de adelante
def s_switch(t, fi, u, d):
    us = Wp(19, 'switch') - 0.1
    ug = Wp(19, 'golpe') - 0.1
    ac = seg(u, ug - 0.1, ug + 0.1)
    fr = Frame(camara(u, [K(-0.3, 5.3, 50, 12, tx=0.4, ty=0.6), K(0.35, 4.4, 30, 10, tx=0.6, ty=0.6), K(d, 4.3, 26, 10, tx=0.6, ty=0.6)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    draw_objects(fr, carro(aceite=(ac, ac, 0, 0), base=0.12, lift=(0.1 * ac, 0.1 * ac, 0, 0)), xray=0.8, keep=('cilindro',))
    for s in (-1, 1):
        for j in range(8):
            q = clamp((u - ug + 0.2) * 3 + j / 8)
            if 0 < q < 1:
                dot3(fr, (lerp(-1.05, LX, q), 0.2, s * lerp(0.25, LZ - 0.12, q)), r=9, col=ACEITE, a=1.0, glow=1.8)

    def ui(img, fx):
        kicker(img, 'CLIC · DE GOLPE', 150, seg(u, -0.1, 0.2), col=AZULC)
        switchbox(img, fx, 540, 440, 1.0, k=1.0, on=1.0 if u > us + 0.2 else 0.0, cual=0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ug + 0.1, 0.3), amp=16)


# 20. la llanta empuja el piso y el carro sale volando (brinco grande con sacudida)
def s_vuela(t, fi, u, d):
    ue = Wp(20, 'empuja') - 0.1
    uv = Wp(20, 'volando') - 0.15
    ext = 0.45 * P.eout4(seg(u, ue, ue + 0.2))
    air = 1.1 * math.sin(math.pi * seg(u, uv, uv + 0.9))
    fr = Frame(camara(u, [K(-0.3, 6.6, -40, 6, ty=0.8), K(0.35, 5.8, -32, 4, ty=0.8), K(uv, 6.8, -30, 2, ty=1.3), K(d, 6.7, -30, 2, ty=1.3)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=1.0, beam=0.6)
    fl = ext + air
    draw_objects(fr, carro(lift=(fl, fl, 0, 0), ruedas_y=(max(0.0, air * 0.8), 0), aceite=(1, 1, 0, 0), base=0.12))
    gx, gy, _ = fr.cam.p1((LX, 0.0, LZ))

    def ui(img, fx):
        kicker(img, 'LA LLANTA EMPUJA EL PISO', 150, seg(u, -0.1, 0.2), col=AZULC)
        if ue < u < uv + 0.4:
            doodle_arrow(img, fx, gx, gy + 60, gx, gy + 220, t, k=seg(u, ue, ue + 0.2), col=AMARILLO, seed=5)
        P.titulo_golpe(img, fx, [('¡Vuela!', 'serif')], 330, seg(u, uv + 0.1, uv + 0.25), size=110, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, ue + 0.2, 0.3), golpe_k(u, uv + 0.9, 0.35)), amp=24)


# 21. Es la ley de Pascal («PASCAL» de cristal; jeringas con cruces de presión)
def s_pascal(t, fi, u, d):
    up = Wp(21, 'pascal') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, 30, 10, ty=1.0), K(0.35, 4.6, 10, 8, ty=1.0), K(d, 4.5, 6, 8, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9, beam=0.5)
    M.cristal(fr.base, fr.fx, 'PASCAL', u, t0=up - 0.05, cy=0.3, entrada='sube')

    def ui(img, fx):
        kicker(img, 'BLAISE PASCAL · SIGLO XVII', 150, seg(u, -0.1, 0.2), col=AZULC)
        jeringas(img, fx, 540, 1080, 1.0, k=seg(u, -0.25, 0.0), p=0.4, flechas=0.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.15, 0.3), amp=14)


# 22. la presión llega igual a todo el aceite (cruces cian de presión iguales en todo el líquido)
def s_igual(t, fi, u, d):
    ui_ = Wp(22, 'igual') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, -20, 8, ty=1.0), K(0.35, 4.2, -6, 6, ty=1.0), K(d, 4.1, -2, 6, ty=1.0)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9)

    def ui(img, fx):
        kicker(img, 'MISMA PRESIÓN EN TODOS LADOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        jeringas(img, fx, 540, 900, 1.3, k=1.0, p=0.4, flechas=0.0, presion=seg(u, ui_ - 0.2, ui_ + 0.2))
        texto(img, fx, 540, 1380, 'P = IGUAL', 80, CYAN, seg(u, ui_, ui_ + 0.25), f='mono', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. y en el pistón grande se vuelve fuerza (F = P × A; flecha roja gigante)
def s_grande(t, fi, u, d):
    ug = Wp(23, 'grande') - 0.1
    uf = Wp(23, 'fuerza') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.4, 20, 8, ty=1.0), K(0.35, 4.0, 6, 6, ty=1.0), K(d, 3.9, 2, 6, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)

    def ui(img, fx):
        kicker(img, 'MÁS ÁREA = MÁS FUERZA', 150, seg(u, -0.1, 0.2), col=AZULC)
        jeringas(img, fx, 540, 1050, 1.2, k=1.0, p=0.4 + 0.4 * seg(u, ug, ug + 0.5), flechas=seg(u, uf - 0.1, uf + 0.2))
        texto(img, fx, 540, 360, 'F = P × A', 110, WHITE, seg(u, ug - 0.2, ug), f='mono', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uf + 0.15, 0.3), amp=16)


# 24. Mándaselo a tu compa del club lowrider (el carro baila en tres llantas)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.2, 56, 10, ty=0.7), K(0.4, 6.4, 44, 6, ty=0.7), K(d, 6.3, 40, 6, ty=0.7)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.6)
    a = 0.35 + 0.1 * math.sin(t * 4)
    draw_objects(fr, carro(lift=(a, 0.05, 0.05, 0.05), aceite=(1, 0, 0, 0), base=0.12))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('del club lowrider.', 'serif')], 230, seg(u, 0.0, 0.15), size=70)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.6), sfx=[(U_CAE + 0.12, 'sub', 1.0), (U_CAE + 0.12, 'bass', 0.9), (0.2, 'thud', 0.6)]),
           dict(desde=1, fn=s_raza, tr='whip', sfx=[(0.3, 'whoosh_suave', 0.5)]),
           dict(desde=2, fn=s_1958, tr='golpe', sfx=[(0.0, 'bass', 0.8), (1.2, 'tick2', 0.5)]),
           dict(desde=3, fn=s_boton, tr='iris', c=(0.5, 0.22), sfx=[(0.4, 'click', 0.9), (1.2, 'click', 0.9)]),
           dict(desde=4, fn=s_amortiguador, tr='flash', sfx=[(0.6, 'scribble', 0.6)]),
           dict(desde=5, fn=s_cilindro, tr='zoom', sfx=[(0.3, 'shimmer', 0.6)]),
           dict(desde=6, fn=s_bomba, tr='deslizar', sfx=[(0.2, 'whoosh_suave', 0.5), (0.6, 'riser', 0.4)]),
           dict(desde=7, fn=s_apretar, tr='cubo', sfx=[(0.9, 'thud', 0.7)]),
           dict(desde=8, fn=s_jeringas, tr='rebanadas', sfx=[(0.3, 'tick2', 0.5)]),
           dict(desde=9, fn=s_fuerza, tr='push', c=(0.3, 0.5), sfx=[(0.5, 'whoosh', 0.5), (1.4, 'bass', 0.7)]),
           dict(desde=10, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(0.25, 'bass', 0.9)]),
           dict(desde=11, fn=s_brinca, tr='giro', sfx=[(0.8, 'thud', 0.8), (1.8, 'thud', 0.8)]),
           dict(desde=12, fn=s_dobla, tr='wipe', sfx=[(0.6, 'thud', 0.9), (1.3, 'thud', 0.9)]),
           dict(desde=13, fn=s_cuartea, tr='glitch', sfx=[(0.3, 'vidrio', 0.6)]),
           dict(desde=14, fn=s_placas, tr='cubo_izq', sfx=[(0.1 + 0.15 * j, 'tick', 0.35) for j in range(12)]),
           dict(desde=15, fn=s_dedonde, tr='whip_izq', sfx=[(0.3, 'scribble', 0.6)]),
           dict(desde=16, fn=s_baterias, tr='cristal', palabra='12 VOLTS', sfx=[(0.2 + 0.25 * j, 'click', 0.6) for j in range(4)]),
           dict(desde=17, fn=s_equipo, tr='mosaico', sfx=[(0.4, 'tick2', 0.5), (1.2, 'tick2', 0.5)]),
           dict(desde=18, fn=s_mas, tr='deslizar_abajo', sfx=[(0.3 + 0.12 * j, 'click', 0.5) for j in range(4)]),
           dict(desde=19, fn=s_switch, tr='remolino', c=(0.5, 0.65), sfx=[(0.5, 'click', 1.0), (0.9, 'whoosh', 0.6)]),
           dict(desde=20, fn=s_vuela, tr='golpe', sfx=[(0.3, 'riser', 0.5), (1.6, 'sub', 0.9)]),
           dict(desde=21, fn=s_pascal, tr='mosaico', sfx=[(0.3, 'chime_b', 0.4)]),
           dict(desde=22, fn=s_igual, tr='rebanadas', sfx=[(0.6, 'chime_a', 0.4)]),
           dict(desde=23, fn=s_grande, tr='push', c=(0.6, 0.5), sfx=[(0.8, 'bass', 0.8)]),
           dict(desde=24, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7)]),
           dict(desde=25, loop=True, tr='cubo')]

if __name__ == '__main__':
    montaje.cli(globals())
