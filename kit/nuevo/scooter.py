"""Reel diario dom 22-nov-2026 10:00 (propuesto) — «Tu scooter no es juguete… ya es moto.»
Por dentro: el motor va escondido en el cubo de la rueda (motor de buje sin escobillas: bobinas fijas en el eje e imanes
que giran con la carcasa, sin cadena; Levy Electric). Un controlador prende las bobinas en orden y los imanes las
persiguen; un chip (el limitador) decide la velocidad máxima.
Regla de la CDMX (Semovi, vía POSTA 16-jul-2026): Vehículo Eléctrico Personal = no pasa de 25 km/h, motor de menos de
250 W y menos de 35 kg (sin placa ni licencia, con holograma). VEMEPE = pasa de 25 km/h o motor de hasta 1 000 W o de
35 a 350 kg: placa, tarjeta de circulación y licencia A1 o A2. Sin registro: multa (10–20 UMA) y corralón (Grupo Animal,
17-nov-2026: el plazo del 20-nov se amplió «hasta nuevo aviso»; por eso la voz no dice fechas).
Error (segundo gancho): quitarle el limitador. Física: de 25 a 35 km/h la energía (½mv²) sube (35/25)² = 1.96 veces y
con los mismos frenos la distancia de frenado también ≈ ×2 (d = v²/2a).
Comunidad: scooters y repartidores. Inicio tipo 6 (pantalla dividida que choca): arriba el scooter en la tienda
(«JUGUETE» de cristal), abajo el mismo con placa («MOTO» de cristal); las mitades chocan y el título cae en la costura.
El final («…su scooter no es juguete») regresa a la pantalla dividida (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
El scooter, el motor en corte, el chip, la placa y los documentos son esquemas sin marca (EJEMPLO / ESQUEMA).
Datos y fuentes: guiones/2026-11-22_scooter.txt.
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
TEMA = 'scooter'
TXT = ['Tu scooter no es juguete… ya es moto.',
       'En la Ciudad de México,',
       'el que pasa de 25 km/h ya necesita placa.',
       '¿Y quién lo empuja?',
       'En una bici, tu pierna jala la cadena.',
       'En el scooter no hay cadena:',
       'el motor va escondido dentro de la rueda.',
       'Las bobinas van fijas en el eje,',
       'y los imanes giran pegados a la llanta.',
       'Un controlador prende las bobinas una por una,',
       'y los imanes las persiguen sin parar.',
       'Y un chip decide hasta dónde te deja correr:',
       'eso es el limitador.',
       'Y aquí viene el error:',
       'quitarle el limitador para que corra más.',
       'De 25 a 35,',
       'la energía del golpe casi se duplica.',
       'Y para frenar necesitas casi el doble de distancia,',
       'con los mismos frenitos.',
       'Además, si pasa de 25 o su motor es de 250 watts o más,',
       'ya es otro vehículo.',
       'Lleva placa, tarjeta de circulación',
       'y licencia tipo A, como una moto.',
       'Sin papeles, te toca multa y hasta corralón.',
       'Mándaselo a tu compa que anda en scooter sin placa.',
       'Porque si ya le quitó el limitador… su scooter no es juguete.']
VOZ = ['Tu scooter no es juguete... ya es moto.',
       'En la Ciudad de México,',
       'el que pasa de veinticinco kilómetros por hora ya necesita placa.',
       '¿Y quién lo empuja?',
       'En una bici, tu pierna jala la cadena.',
       'En el scooter no hay cadena:',
       'el motor va escondido dentro de la rueda.',
       'Las bobinas van fijas en el eje,',
       'y los imanes giran pegados a la llanta.',
       'Un controlador prende las bobinas una por una,',
       'y los imanes las persiguen sin parar.',
       'Y un chip decide hasta dónde te deja correr:',
       'eso es el limitador.',
       'Y aquí viene el error:',
       'quitarle el limitador para que corra más.',
       'De veinticinco a treinta y cinco,',
       'la energía del golpe casi se duplica.',
       'Y para frenar necesitas casi el doble de distancia,',
       'con los mismos frenitos.',
       'Además, si pasa de veinticinco o su motor es de doscientos cincuenta watts o más,',
       'ya es otro vehículo.',
       'Lleva placa, tarjeta de circulación',
       'y licencia tipo A, como una moto.',
       'Sin papeles, te toca multa y hasta corralón.',
       'Mándaselo a tu compa que anda en scooter sin placa.',
       'Porque si ya le quitó el limitador... su scooter no es juguete.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_scooter.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-22_scooter_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
ROJO = (255, 60, 45)
VERDE = (60, 210, 120)
HULE = (28, 28, 31)
GRAFITO = (62, 64, 72)
NEGRO = (22, 22, 25)
CROMO = (205, 208, 215)
COBRE = (200, 122, 62)
IMAN_N = (225, 62, 52)
IMAN_S = (62, 112, 225)
LIMA = (190, 235, 70)

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


# ------------------------------------------------------------------ el scooter (frente hacia +x, apoyado en y = 0)
XR, XF, WR, WT = -0.62, 0.66, 0.2, 0.065
CY = WR + WT


def rueda(x, giro, motor=False, motor_glow=0.0):
    ms = [named(M3.torus(WR, WT, HULE, nu=44, nv=14, gloss=0.25).tf(rx=90, t=(x, CY, 0)), 'llanta', rim=0.45, gloss=0.25)]
    if motor:
        m = named(M3.cyl(WR * 0.82, 0.13, (80, 82, 90), n=32, shadow=0, gloss=0.6, y0=-0.065).tf(rx=90, t=(x, CY, 0)),
                  'motor', rim=0.7, gloss=0.6)
        if motor_glow > 0.01:
            m.glow = M.scale_c(CYAN, 0.55 * motor_glow)
        ms.append(m)
        for j in range(5):
            b = M3.box(0.026, 0.026, 0.02, (176, 178, 186), shadow=0, base=False, gloss=0.8).tf(t=(0, WR * 0.55, 0)).tf(rz=giro + 72 * j)
            ms.append(named(b.tf(t=(x, CY, 0.072)), 'tornillo', rim=0.8))
    else:
        ms.append(named(M3.cyl(WR * 0.7, 0.08, (150, 152, 160), n=28, shadow=0, gloss=0.7, y0=-0.04).tf(rx=90, t=(x, CY, 0)), 'rin', rim=0.7, gloss=0.7))
        for j in range(5):
            b = M3.box(0.03, WR * 0.55, 0.02, (204, 206, 214), shadow=0, base=False, gloss=0.8).tf(t=(0, WR * 0.3, 0)).tf(rz=giro + 72 * j)
            ms.append(named(b.tf(t=(x, CY, 0.045)), 'rayo', rim=0.8))
    return ms


def scooter(giro=0.0, placa=0.0, motor_glow=0.0, bat_glow=0.0, freno=0.0, pantalla=CYAN, precio=0.0):
    """Scooter eléctrico semirrealista sin marca: plataforma negra con lija, poste grafito, motor en la rueda de atrás,
    batería en la plataforma (se ve con rayos X: keep=('bateria', 'motor')), pantalla, calavera y placa opcional."""
    ms = rueda(XR, giro, motor=True, motor_glow=motor_glow) + rueda(XF, giro)
    _B(ms, 1.12, 0.075, 0.22, NEGRO, 0.02, 0.2, 0, name='deck', gloss=0.35)
    _B(ms, 1.04, 0.006, 0.19, (14, 14, 16), 0.02, 0.276, 0, name='lija', gloss=0.05)
    _B(ms, 0.82, 0.045, 0.14, (60, 200, 240), 0.02, 0.215, 0, name='bateria', gloss=0.3,
       glow=M.scale_c(CYAN, 0.7 * bat_glow) if bat_glow > 0.01 else None)
    ms.append(tubo((0.56, 0.27, 0), (XF, CY, 0), r=0.03, col=GRAFITO, name='horquilla'))
    ms.append(tubo((0.56, 0.25, 0), (0.47, 1.45, 0), r=0.038, col=GRAFITO, name='poste', gloss=0.6))
    ms.append(tubo((0.47, 1.45, -0.33), (0.47, 1.45, 0.33), r=0.026, col=GRAFITO, name='manubrio'))
    ms.append(tubo((0.47, 1.45, -0.34), (0.47, 1.45, -0.2), r=0.036, col=NEGRO, name='puno', gloss=0.2))
    ms.append(tubo((0.47, 1.45, 0.2), (0.47, 1.45, 0.34), r=0.036, col=NEGRO, name='puno', gloss=0.2))
    _B(ms, 0.11, 0.035, 0.14, (20, 22, 26), 0.47, 1.47, 0, name='pantalla', gloss=0.5, glow=M.scale_c(pantalla, 0.6))
    _B(ms, 0.4, 0.025, 0.16, GRAFITO, XR + 0.02, CY + WR + WT - 0.02, 0, name='salpicadera', gloss=0.5)
    _B(ms, 0.035, 0.05, 0.12, (200, 30, 30), XR - 0.19, 0.47, 0, name='calavera', gloss=0.6,
       glow=M.scale_c((255, 40, 30), 0.35 + 0.65 * freno))
    _B(ms, 0.05, 0.03, 0.06, (255, 180, 40), 0.57, 0.33, 0.12, name='reflejante', gloss=0.6, glow=M.scale_c((255, 170, 40), 0.3))
    if placa > 0.01:
        s = P.resorte(placa)
        p = M3.box(0.012, 0.15 * s, 0.25 * s, (240, 240, 234), shadow=0, gloss=0.4, base=False).tf(ry=-50, t=(XR - 0.22, 0.38, 0.02))
        ms.append(named(p, 'placa', rim=0.7, glow=M.scale_c(AMARILLO, 0.25)))
    if precio > 0.01:
        tag = M3.box(0.18 * precio, 0.12 * precio, 0.008, (250, 220, 60), shadow=0, gloss=0.3, base=False).tf(rz=12, t=(0.36, 1.18, 0.05))
        ms.append(named(tag, 'etiqueta', rim=0.5, glow=M.scale_c((250, 210, 50), 0.3)))
        ms.append(tubo((0.47, 1.32, 0.02), (0.38, 1.24, 0.05), r=0.004, col=WHITE, name='hilo'))
    return ms


def bici(pedal=0.0):
    """Bici de línea semirrealista (sin marca), frente hacia +x; pedal = ángulo de la biela en grados."""
    R = 0.42
    ms = []
    for x in (-0.68, 0.68):
        ms.append(named(M3.torus(R, 0.035, HULE, nu=52, nv=10, gloss=0.2).tf(rx=90, t=(x, R + 0.035, 0)), 'llanta', rim=0.45))
        ms.append(named(M3.torus(R * 0.93, 0.012, CROMO, nu=52, nv=6, gloss=0.8).tf(rx=90, t=(x, R + 0.035, 0)), 'rin', rim=0.8))
    bb, sx, hd = (0.0, 0.42, 0), (-0.16, 1.02, 0), (0.5, 1.02, 0)
    ra, fa = (-0.68, R + 0.035, 0), (0.68, R + 0.035, 0)
    ROJ = (196, 40, 40)
    for a, b in ((bb, sx), (sx, hd), (hd, bb), (bb, ra), (sx, ra)):
        ms.append(tubo(a, b, r=0.028, col=ROJ, name='cuadro', gloss=0.7))
    ms.append(tubo(hd, fa, r=0.024, col=CROMO, name='tenedor'))
    ms.append(tubo((0.5, 1.02, 0), (0.46, 1.22, 0), r=0.022, col=CROMO, name='poste'))
    ms.append(tubo((0.46, 1.22, -0.26), (0.46, 1.22, 0.26), r=0.02, col=CROMO, name='manubrio'))
    ms.append(tubo((-0.16, 1.02, 0), (-0.18, 1.14, 0), r=0.02, col=CROMO, name='tija'))
    _B(ms, 0.24, 0.05, 0.1, NEGRO, -0.18, 1.14, 0, name='asiento', gloss=0.2)
    ms.append(named(M3.torus(0.11, 0.012, CROMO, nu=30, nv=5, gloss=0.8).tf(rx=90, t=(0, 0.42, 0.04)), 'plato', rim=0.8))
    ms.append(named(M3.torus(0.05, 0.01, CROMO, nu=20, nv=5, gloss=0.8).tf(rx=90, t=(-0.68, R + 0.035, 0.04)), 'pinon', rim=0.8))
    for sgn in (1, -1):
        a = math.radians(pedal + (0 if sgn > 0 else 180))
        e = (0.17 * math.cos(a), 0.42 + 0.17 * math.sin(a), 0.07 * sgn)
        ms.append(tubo((0, 0.42, 0.07 * sgn), e, r=0.016, col=CROMO, name='biela'))
        _B(ms, 0.1, 0.025, 0.07, NEGRO, e[0], e[1] - 0.012, e[2] + 0.03 * sgn, name='pedal', gloss=0.3)
    return ms


def cadena(fr, t, k=1.0, vel=1.0, col=AMARILLO):
    """Cadena que corre del plato al piñón (puntos que avanzan) y brilla."""
    if k <= 0.01:
        return
    R = 0.42 + 0.035
    top = [(0.0, 0.42 + 0.11, 0.04), (-0.68, R + 0.05, 0.04)]
    bot = [(-0.68, R - 0.05, 0.04), (0.0, 0.42 - 0.11, 0.04)]
    line3(fr, top, col=col, w=4, a=0.8 * k, glow=0.9)
    line3(fr, bot, col=col, w=4, a=0.8 * k, glow=0.9)
    for j in range(10):
        s = ((t * 0.9 * vel) + j / 10) % 1.0
        p = np.array(top[0]) + (np.array(top[1]) - np.array(top[0])) * s
        dot3(fr, tuple(p), r=6, col=col, a=k, glow=1.3)


# ------------------------------------------------------------------ el motor de buje en corte (plano xy, centro y=1.1)
def motor_corte(ang, activas=(), k_bob=1.0, s=1.0, x=0.0, y=1.1, tire=True):
    ms = []
    if tire:
        ms.append(named(M3.torus(0.95, 0.14, HULE, nu=64, nv=14, gloss=0.25).tf(rx=90), 'llanta', rim=0.45))
    ms.append(named(M3.torus(0.78, 0.045, (124, 128, 136), nu=64, nv=8, gloss=0.7).tf(rx=90), 'carcasa', rim=0.7, gloss=0.7))
    for j in range(14):
        col = IMAN_N if j % 2 == 0 else IMAN_S
        b = M3.box(0.2, 0.085, 0.12, col, shadow=0, base=False, gloss=0.5).tf(t=(0, 0.69, 0)).tf(rz=ang + j * 360 / 14)
        ms.append(named(b, 'iman', rim=0.6, gloss=0.5))
    ms.append(named(M3.cyl(0.42, 0.1, (92, 94, 102), n=40, shadow=0, gloss=0.5, y0=-0.05).tf(rx=90), 'estator', rim=0.6))
    for j in range(12):
        b = M3.box(0.13, 0.2, 0.11, COBRE, shadow=0, base=False, gloss=0.7).tf(t=(0, 0.52, 0)).tf(rz=j * 30)
        b = named(b, 'bobina', rim=0.7, gloss=0.7)
        if j in activas:
            b.glow = M.scale_c(CYAN, 0.95 * k_bob)
        ms.append(b)
    ms.append(named(M3.cyl(0.075, 0.6, CROMO, n=20, shadow=0, gloss=0.9, y0=-0.3).tf(rx=90), 'eje', rim=0.8))
    return P.tfk(ms, s=s, t=(x, y, 0))


def activas_de(ang):
    """Bobinas que prende el controlador: las que van justo delante de los imanes (dos opuestas)."""
    j = int(math.floor(((ang % 360) / 30.0) + 1)) % 12
    return (j, (j + 6) % 12)


def chip(k=1.0, x=0.0, y=0.9, s=1.0):
    ms = []
    _B(ms, 0.9, 0.12, 0.9, (26, 26, 30), 0, 0, 0, name='chip', gloss=0.55)
    _B(ms, 0.5, 0.01, 0.5, (40, 40, 46), 0, 0.12, 0, name='tapa', gloss=0.9)
    for i in range(7):
        q = -0.36 + 0.12 * i
        for (px, pz, sx, sz) in ((q, 0.5, 0.05, 0.12), (q, -0.5, 0.05, 0.12), (0.5, q, 0.12, 0.05), (-0.5, q, 0.12, 0.05)):
            _B(ms, sx, 0.03, sz, CROMO, px, 0.02, pz, name='pin', gloss=0.9)
    return P.tfk(ms, s=s * P.resorte(k), t=(x, y, 0))


def velocimetro(img, fx, cx, cy, v, k=1.0, col=CYAN, w=420, maxtxt=None):
    """Pantalla del scooter (2D): número grande en monoespaciada y km/h."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    h = int(w * 0.56)
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=28, fill=(10, 11, 14), outline=M.scale_c(col, 0.8 * k), width=4)
    ImageDraw.Draw(fx).rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=28, outline=M.scale_c(col, 0.3 * k), width=12)
    texto(img, fx, cx, cy - h * 0.06, f'{v:.0f}', int(h * 0.62), col, k, f='mono', glow=0.5)
    texto(img, fx, cx, cy + h * 0.34, maxtxt or 'KM/H', int(h * 0.12), GRIS, k, f='mono', glow=0)


def tarjeta2d(img, fx, cx, cy, w, tipo, k=1.0, ang=0.0):
    """Documentos de EJEMPLO (sin escudos ni logos): placa, tarjeta de circulación y licencia tipo A."""
    if k <= 0.01:
        return
    h = int(w * (0.5 if tipo == 'placa' else 0.63))
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    if tipo == 'placa':
        dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=(244, 244, 240, 255), outline=(40, 40, 44, 255), width=6)
        dl.text((w / 2, h * 0.2), 'CIUDAD DE MÉXICO', font=M.font('mono', int(w * 0.07)), fill=(60, 60, 66, 255), anchor='mm')
        dl.text((w / 2, h * 0.6), 'EJ-123', font=M.font('sansx', int(w * 0.24)), fill=(20, 20, 24, 255), anchor='mm')
    elif tipo == 'tarjeta':
        dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=(236, 240, 246, 255))
        dl.rectangle((0, 0, w, int(h * 0.22)), fill=(60, 110, 200, 255))
        dl.text((w / 2, h * 0.11), 'TARJETA DE CIRCULACIÓN', font=M.font('sansx', int(w * 0.058)), fill=(255, 255, 255, 255), anchor='mm')
        for j, (a, b) in enumerate((('TIPO', 'VEMEPE'), ('PLACA', 'EJ-123'), ('USO', 'PARTICULAR'))):
            y = h * (0.4 + 0.18 * j)
            dl.text((w * 0.07, y), a, font=M.font('mono', int(w * 0.05)), fill=(80, 80, 90, 255), anchor='lm')
            dl.text((w * 0.93, y), b, font=M.font('sansx', int(w * 0.06)), fill=(20, 20, 26, 255), anchor='rm')
    else:
        dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=(240, 236, 226, 255))
        dl.rectangle((0, 0, w, int(h * 0.22)), fill=(150, 40, 80, 255))
        dl.text((w / 2, h * 0.11), 'LICENCIA DE CONDUCIR', font=M.font('sansx', int(w * 0.06)), fill=(255, 255, 255, 255), anchor='mm')
        dl.rounded_rectangle((w * 0.07, h * 0.32, w * 0.33, h * 0.86), radius=10, fill=(200, 196, 186, 255))
        dl.text((w * 0.62, h * 0.5), 'TIPO', font=M.font('mono', int(w * 0.06)), fill=(80, 80, 90, 255), anchor='mm')
        dl.text((w * 0.62, h * 0.72), 'A1 / A2', font=M.font('sansx', int(w * 0.13)), fill=(20, 20, 26, 255), anchor='mm')
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    s = P.resorte(k)
    if s < 0.99 or s > 1.01:
        lay = lay.resize((max(2, int(lay.width * s)), max(2, int(lay.height * s))))
    img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)
    ImageDraw.Draw(fx).rounded_rectangle((cx - lay.width / 2, cy - lay.height / 2, cx + lay.width / 2, cy + lay.height / 2),
                                         radius=18, outline=M.scale_c(WHITE, 0.15 * k), width=10)


def candado(img, fx, cx, cy, s, k=1.0, abierto=0.0, col=AMARILLO):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    c = M.scale_c(col, k)
    up = 40 * s * abierto
    d.arc((cx - 46 * s, cy - 110 * s - up, cx + 46 * s, cy - 10 * s - up), 180, 360, fill=c, width=int(14 * s))
    d.line([(cx + 46 * s, cy - 60 * s - up), (cx + 46 * s, cy - 20 * s - up * (1 - abierto))], fill=c, width=int(14 * s))
    if abierto < 0.5:
        d.line([(cx - 46 * s, cy - 60 * s), (cx - 46 * s, cy - 20 * s)], fill=c, width=int(14 * s))
    d.rounded_rectangle((cx - 70 * s, cy - 30 * s, cx + 70 * s, cy + 80 * s), radius=int(14 * s), fill=c)
    d.ellipse((cx - 12 * s, cy + 10 * s, cx + 12 * s, cy + 34 * s), fill=(20, 20, 20))
    df.rounded_rectangle((cx - 90 * s, cy - 50 * s, cx + 90 * s, cy + 100 * s), radius=int(20 * s), fill=M.scale_c(col, 0.3 * k))


def pin_mapa(k):
    """Pin rojo del mapa que cae y rebota (esfera + cono)."""
    e = P.rebote(k)
    y = 3.0 * (1 - e)
    ms = [named(M3.sphere(0.24, (220, 40, 40), nu=28, nv=16, shadow=0, gloss=0.8).tf(t=(0, 0.82 + y, 0)), 'pin', rim=0.8, gloss=0.8),
          named(M3.cyl(0.17, 0.62, (200, 34, 34), n=24, shadow=0, gloss=0.7, r2=0.0).tf(rx=180, t=(0, 0.74 + y, 0)), 'pin', rim=0.7),
          named(M3.sphere(0.08, WHITE, nu=16, nv=10, shadow=0, gloss=0.9).tf(t=(0, 0.86 + y, 0.2)), 'pin', rim=0.5, glow=(70, 70, 70))]
    return ms


def calles(fr, t, k=1.0):
    """Cuadrícula de calles de la ciudad en line-art que brilla (EJEMPLO) y pulso cian desde el pin."""
    for i in range(-5, 6):
        line3(fr, [(-4, 0.005, i * 0.7), (4, 0.005, i * 0.7)], col=(200, 205, 215), w=2, a=0.45 * k, glow=0.3)
        line3(fr, [(i * 0.7, 0.005, -4), (i * 0.7, 0.005, 4)], col=(200, 205, 215), w=2, a=0.45 * k, glow=0.3)
    line3(fr, [(-4, 0.01, -2.0), (4, 0.01, 1.2)], col=AMARILLO, w=4, a=0.7 * k, glow=0.8)
    r = 0.3 + (t * 1.4) % 1.0 * 2.2
    th = np.linspace(0, 2 * math.pi, 60)
    line3(fr, [(r * math.cos(q), 0.02, r * math.sin(q)) for q in th], col=CYAN, w=3, a=k * (1 - (r - 0.3) / 2.2), glow=1.0)


# ================================================================== escenas
# 0. gancho (inicio 6: pantalla dividida que choca). Arriba el scooter en la tienda con su etiqueta («JUGUETE» de
#    cristal); abajo el mismo, rodando, con placa («MOTO» de cristal). En el loop (u < −0.9) están juntas; se separan y
#    en U_CHOQUE chocan con destello y sacudida; el título cae en la costura.
U_CHOQUE = 0.05


def _mitad(t, u, arriba):
    if arriba:
        fr = Frame(camara(u, [K(-3.5, 3.9, 34, 10, ty=0.75), K(U_CHOQUE, 3.5, 22, 8, ty=0.75), K(3.0, 3.4, 16, 8, ty=0.75)], cy=0.5))
    else:
        fr = Frame(camara(u, [K(-3.5, 3.9, -34, 10, ty=0.75), K(U_CHOQUE, 3.5, -22, 8, ty=0.75), K(3.0, 3.4, -16, 8, ty=0.75)], cy=0.5))
    space(fr, t, floor='dots' if arriba else 'lines', floor_a=0.8, bokeh=0.8, beam=0.5 if arriba else 0.2)
    M.cristal(fr.base, fr.fx, 'JUGUETE' if arriba else 'MOTO', u, t0=-3.0, cy=0.45, entrada='golpe')
    if arriba:
        draw_objects(fr, P.tfk(scooter(precio=1.0), ry=8 * math.sin(t * 0.7)))
    else:
        draw_objects(fr, scooter(giro=-t * 260, placa=1.0, motor_glow=0.4, freno=0.2))
        off = (t * 3.0) % 1.0
        for j in range(-4, 5):
            line3(fr, [(j - off, 0.005, 0.5), (j - off + 0.45, 0.005, 0.5)], col=AMARILLO, w=4, a=0.7, glow=0.6)
    return fr


def s_gancho(t, fi, u, d):
    ub = Wp(0, 'moto') - 0.12
    if u < -0.25:
        gap = 230 * seg(u, -0.9, -0.25)
    else:
        gap = 230 * (1 - P.eout4(seg(u, -0.25, U_CHOQUE)))
    A = _mitad(t, u, True)
    B = _mitad(t, u, False)

    def ui_a(img, fx):
        pill(img, fx, 540, 1230, 'EN LA TIENDA · «JUGUETE»', 1.0, size=28, border=AMARILLO)

    def ui_b(img, fx):
        pill(img, fx, 540, 660, 'EN LA CALLE · CON PLACA', 1.0, size=28, border=ROJO)
    A.ui.append(ui_a)
    B.ui.append(ui_b)
    ia = finish(A, fi)
    ib = finish(B, fi)
    out = np.zeros_like(ia)
    g = int(gap)
    out[0:960 - g] = ia[480 + g:1440][:960 - g]
    out[960 + g:1920] = ib[480:1440 - g][:960 - g]
    img = Image.fromarray(out)
    fx = Image.new('RGB', img.size, (0, 0, 0))
    dl = ImageDraw.Draw(img)
    kc = 1 - seg(u, U_CHOQUE + 0.05, U_CHOQUE + 0.5) if u >= U_CHOQUE else 0.5
    dl.line([(0, 960 - g), (1080, 960 - g)], fill=M.scale_c(WHITE, 0.6 + 0.4 * kc), width=4)
    dl.line([(0, 960 + g), (1080, 960 + g)], fill=M.scale_c(WHITE, 0.6 + 0.4 * kc), width=4)
    P.titulo_golpe(img, fx, [('Tu scooter no es juguete…', 'sans'), ('ya es moto.', 'serif')], 860, seg(u, 0.15, 0.3), size=70)
    kicker(img, 'SCOOTER ELÉCTRICO · CDMX', 120, seg(u, 0.3, 0.5), col=AZULC)
    a = np.asarray(img, np.float32) + np.asarray(fx.filter(ImageFilter.GaussianBlur(6)), np.float32) * 0.8
    if U_CHOQUE <= u < U_CHOQUE + 0.14:
        a += 120 * (1 - seg(u, U_CHOQUE, U_CHOQUE + 0.14))
    out = a.clip(0, 255).astype(np.uint8)
    return sacudir(out, t, max(golpe_k(u, U_CHOQUE, 0.4), golpe_k(u, 0.3, 0.25), golpe_k(u, ub, 0.25)), amp=28)


# 1. En la Ciudad de México: el pin cae en la cuadrícula de calles
def s_cdmx(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.5, 30, 40, ty=0.5), K(0.35, 4.6, 12, 30, ty=0.6), K(d, 4.4, 8, 30, ty=0.6)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.9, beam=0.4)
    calles(fr, t, k=1.0)
    draw_objects(fr, pin_mapa(seg(u, -0.25, 0.25)))
    px, py, _ = fr.cam.p1((0, 1.4, 0))

    def ui(img, fx):
        kicker(img, 'SEMOVI · REGLA DE LA CIUDAD', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, px, py - 120, 'CIUDAD DE MÉXICO', eout(seg(u, 0.25, 0.5)), size=34, border=ROJO)
        esquema(img, fx, 1.0, txt='EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.3), amp=16)


# 2. el que pasa de 25 km/h ya necesita placa («25 KM/H» de cristal; el número pasa a 26 y salta la placa)
def s_placa(t, fi, u, d):
    u25 = Wp(2, 'veinticinco') - 0.1
    up = Wp(2, 'placa') - 0.15
    fr = Frame(camara(u, [K(-0.3, 3.2, -40, 8, ty=0.7), K(0.35, 3.6, -24, 8, ty=0.7), K(up, 3.0, -48, 10, ty=0.6), K(d, 2.9, -52, 10, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, '25 KM/H', u, t0=u25 - 0.05, cy=0.36, entrada='golpe')
    draw_objects(fr, scooter(giro=-t * 300, placa=seg(u, up, up + 0.3), motor_glow=0.5))
    v = 25 * P.eout4(seg(u, -0.2, u25 + 0.3)) + (1 if u > up - 0.25 else 0)

    def ui(img, fx):
        velocimetro(img, fx, 800, 1320, v, k=seg(u, -0.2, 0.0), col=ROJO if v > 25.5 else CYAN, w=360)
        kicker(img, 'MÁS DE 25 KM/H', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 300, 1320, '+ PLACA', eout(seg(u, up + 0.1, up + 0.35)), size=40, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, u25 + 0.1, 0.3), golpe_k(u, up + 0.2, 0.3)), amp=18)


# 3. ¿Y quién lo empuja? (órbita rápida alrededor del scooter que rueda; «?» de garabato)
def s_quien(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.2, 60, 12, ty=0.7), K(0.3, 2.7, -10, 6, ty=0.7), K(d, 2.6, -16, 6, ty=0.7)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9)
    draw_objects(fr, scooter(giro=-t * 300))
    off = (t * 3.0) % 1.0
    for j in range(-4, 5):
        line3(fr, [(j - off, 0.005, 0.5), (j - off + 0.45, 0.005, 0.5)], col=AMARILLO, w=4, a=0.7, glow=0.6)

    def ui(img, fx):
        kicker(img, 'SIN PEDALES · SIN GASOLINA', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 830, 520, '?', 260, AMARILLO, eout(seg(u, 0.1, 0.35)), f='sansx', glow=0.6)
        doodle_circle(img, fx, 830, 540, 150, 170, t, k=seg(u, 0.25, 0.6), col=AMARILLO, seed=3)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. En una bici, tu pierna jala la cadena (la cadena brilla y corre)
def s_bici(t, fi, u, d):
    uc = Wp(4, 'cadena') - 0.15
    fr = Frame(camara(u, [K(-0.3, 4.0, 30, 10, ty=0.75), K(0.35, 3.3, 8, 6, ty=0.7), K(d, 3.2, 4, 6, ty=0.7)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.5)
    e = P.entrada(u, -0.25, 0.3, 'desliza')
    draw_objects(fr, P.tfk(bici(pedal=-t * 220), t=(e['dy'], 0, 0)))
    cadena(fr, t, k=seg(u, uc - 0.1, uc + 0.2), vel=1.2)

    def ui(img, fx):
        kicker(img, 'CASO 1 · LA BICI', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, 'TU PIERNA → PEDAL → CADENA → RUEDA', eout(seg(u, uc, uc + 0.3)), size=26, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. En el scooter no hay cadena (CADENA tachada)
def s_sincadena(t, fi, u, d):
    un = Wp(5, 'cadena') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, -30, 10, ty=0.7), K(0.35, 2.8, -8, 6, ty=0.7), K(d, 2.7, -4, 6, ty=0.7)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.5)
    e = P.entrada(u, -0.25, 0.3, 'desliza')
    draw_objects(fr, P.tfk(scooter(giro=-t * 200), t=(-e['dy'], 0, 0)))

    def ui(img, fx):
        kicker(img, 'CASO 2 · EL SCOOTER', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.pill_tachada(img, fx, 540, 1330, 'CADENA', seg(u, 0.0, 0.25), seg(u, un, un + 0.35), t, size=40)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.3, 0.3), amp=12)


# 6. el motor va escondido dentro de la rueda (crash zoom a la rueda de atrás; rayos X: brilla el motor)
def s_escondido(t, fi, u, d):
    ur = Wp(6, 'rueda') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.2, 10, 8, ty=0.7), K(0.3, 2.0, 6, 4, tx=-0.4, ty=0.45), K(ur, 1.3, 2, 2, tx=-0.6, ty=0.3), K(d, 1.25, 0, 2, tx=-0.62, ty=0.28)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    x = seg(u, 0.3, 0.6)
    draw_objects(fr, scooter(giro=-t * 120, motor_glow=x, bat_glow=0.5 * x), xray=0.85 * x, keep=('motor', 'tornillo', 'bateria'))
    mx, my, _ = fr.cam.p1((XR, CY, 0.1))

    def ui(img, fx):
        kicker(img, 'RAYOS X · RUEDA DE ATRÁS', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > ur:
            doodle_circle(img, fx, mx, my, 300, 300, t, k=seg(u, ur, ur + 0.4), col=CYAN, seed=5)
            pill(img, fx, mx, my - 380, 'MOTOR DE BUJE', eout(seg(u, ur + 0.1, ur + 0.4)), size=32, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. Las bobinas van fijas en el eje (la cámara entra por la rueda: motor en corte, bobinas de cobre)
def s_bobinas(t, fi, u, d):
    ub = Wp(7, 'bobinas') - 0.1
    ue = Wp(7, 'eje') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.4, 0, 0, ty=1.1), K(0.3, 3.6, 18, 6, ty=1.1), K(d, 3.5, 22, 6, ty=1.1)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    ang = 20 * t
    act = tuple(range(12)) if ub < u < ub + 0.8 else ()
    draw_objects(fr, motor_corte(ang, act, k_bob=0.6 * (1 - seg(u, ub + 0.4, ub + 0.8))))
    ex, ey, _ = fr.cam.p1((0, 1.1, 0.3))
    bx, by, _ = fr.cam.p1((0, 1.62, 0.06))

    def ui(img, fx):
        kicker(img, 'ADENTRO DEL MOTOR · CORTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, bx, by - 70, 'BOBINAS DE COBRE', eout(seg(u, ub, ub + 0.3)), size=28, border=NARANJA)
        if u > ue:
            pill(img, fx, ex + 220, ey + 240, 'FIJAS EN EL EJE', eout(seg(u, ue, ue + 0.3)), size=30, border=AMARILLO)
            doodle_arrow(img, fx, ex + 200, ey + 200, ex + 30, ey + 30, t, k=seg(u, ue, ue + 0.3), col=AMARILLO, seed=2)
        esquema(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. y los imanes giran pegados a la llanta («IMANES» de cristal detrás; el anillo de imanes gira)
def s_imanes(t, fi, u, d):
    ui_ = Wp(8, 'imanes') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.2, -30, 8, ty=1.1), K(0.35, 3.5, -10, 4, ty=1.1), K(d, 3.4, -6, 4, ty=1.1)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'IMANES', u, t0=ui_ - 0.1, cy=0.5, entrada='sube')
    ang = 25 * t + 160 * P.eout4(seg(u, ui_, ui_ + 1.2))
    draw_objects(fr, motor_corte(ang))
    gx, gy, _ = fr.cam.p1((0.0, 1.1 + 0.72, 0.1))

    def ui(img, fx):
        kicker(img, 'GIRAN CON LA LLANTA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 330, 1420, 'N', 1.0, size=34, border=IMAN_N, dot=False)
        pill(img, fx, 470, 1420, 'S', 1.0, size=34, border=IMAN_S, dot=False)
        pill(img, fx, 720, 1420, 'IMANES', eout(seg(u, ui_, ui_ + 0.3)), size=30, border=CYAN)
        N.doodle_arrow_free(img, fx, gx - 240, gy - 60, gx + 240, gy - 60, t, seg(u, ui_ + 0.2, ui_ + 0.6), AMARILLO, seed=4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. Un controlador prende las bobinas una por una (caja con cables; las bobinas se prenden en orden)
def s_control(t, fi, u, d):
    uu = Wp(9, 'una') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, 40, 10, ty=1.0), K(0.35, 4.0, 14, 8, ty=1.0), K(d, 3.9, 10, 8, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    j = int((u * 5.0) % 12)
    act = (j, (j + 6) % 12) if u > -0.1 else ()
    ms = motor_corte(0.0, act, k_bob=1.0, s=0.75, x=0.35, y=1.0)
    caja = []
    _B(caja, 0.5, 0.32, 0.3, (34, 36, 42), -1.15, 0.2, 0, name='controlador', gloss=0.5)
    _B(caja, 0.3, 0.02, 0.2, (20, 70, 40), -1.15, 0.52, 0, name='placa_pcb', gloss=0.4, glow=M.scale_c(VERDE, 0.3))
    e = P.entrada(u, -0.25, 0.25, 'pop')
    draw_objects(fr, ms + P.tfk(caja, s=max(0.05, e['escala'])))
    for jj, col in enumerate((ROJO, AMARILLO, CYAN)):
        pts = [(-0.9, 0.36 + 0.06 * jj, 0.05), (-0.5, 0.5 + 0.06 * jj, 0.1), (0.35, 1.0, 0.1)]
        line3(fr, pts, col=col, w=3, a=0.8, glow=0.6)
        s = (t * 2.2 + jj * 0.33) % 1.0
        dot3(fr, (lerp(-0.9, 0.35, s), lerp(0.36, 1.0, s), 0.1), r=7, col=CYAN, a=1.0, glow=1.4)
    cx, cy_, _ = fr.cam.p1((-1.15, 0.45, 0.2))

    def ui(img, fx):
        kicker(img, 'EL CONTROLADOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, cx, cy_ - 160, 'CONTROLADOR', eout(seg(u, 0.0, 0.3)), size=28, border=VERDE)
        texto(img, fx, 760, 1450, f'BOBINA {j + 1:02d}', 40, CYAN, seg(u, uu, uu + 0.2), f='mono', glow=0.4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. y los imanes las persiguen sin parar (zoom digital al hueco entre imán y bobina; gira más rápido)
def s_persiguen(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.0, 0, 0, ty=1.1), K(0.3, 1.6, 0, 0, tx=0.0, ty=1.65), K(d, 1.55, 4, 0, tx=0.0, ty=1.67)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.7)
    ang = 120 * u
    draw_objects(fr, motor_corte(ang, activas_de(ang - 90), k_bob=1.0))
    ax, ay, _ = fr.cam.p1((0.0, 1.1 + 0.6, 0.1))

    def ui(img, fx):
        rec_frame(img, t, k=seg(u, 0.0, 0.2), zoom_label='x1.8')
        kicker(img, 'SE ATRAEN · SE EMPUJAN · SIN PARAR', 150, seg(u, -0.1, 0.2), col=AZULC)
        doodle_arrow(img, fx, ax + 260, ay - 300, ax + 40, ay - 60, t, k=seg(u, 0.4, 0.7), col=AMARILLO, seed=6)
        pill(img, fx, 540, 1400, 'SIN CADENA · SIN ENGRANES', eout(seg(u, 0.8, 1.1)), size=28, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. Y un chip decide hasta dónde te deja correr («CHIP» de cristal; el chip sale de la pantalla del manubrio)
def s_chip(t, fi, u, d):
    uc = Wp(11, 'chip') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, 30, 30, ty=0.9), K(0.35, 2.9, 12, 34, ty=0.9), K(d, 2.8, 8, 34, ty=0.9)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9, beam=0.5)
    M.cristal(fr.base, fr.fx, 'CHIP', u, t0=uc - 0.05, cy=0.33, entrada='zoom')
    draw_objects(fr, P.tfk(chip(k=seg(u, -0.25, 0.2)), ry=10 * math.sin(t)))
    for jj in range(8):                                     # pistas del circuito que brillan
        a = jj * 45
        r0, r1 = 0.75, 1.6
        line3(fr, [(r0 * math.cos(math.radians(a)), 0.9, r0 * math.sin(math.radians(a))),
                   (r1 * math.cos(math.radians(a)), 0.9, r1 * math.sin(math.radians(a)))], col=VERDE, w=3, a=0.7, glow=0.8,
              frac=seg(u, 0.1 + 0.05 * jj, 0.5 + 0.05 * jj))
    tx, ty, _ = fr.cam.p1((0, 1.03, 0))

    def ui(img, fx):
        kicker(img, 'EL CEREBRO DEL SCOOTER', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, tx, ty, 'MÁX 25', 54, CYAN, seg(u, 0.3, 0.5), f='mono', glow=0.5)
        esquema(img, fx, 1.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.15, 0.3), amp=14)


# 12. eso es el limitador (candado amarillo sobre el chip; la pantalla no pasa de 25)
def s_limitador(t, fi, u, d):
    ul = Wp(12, 'limitador') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.2, -30, 30, ty=0.9), K(0.35, 3.0, -10, 26, ty=0.9), K(d, 2.9, -6, 26, ty=0.9)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9)
    draw_objects(fr, chip(k=1.0, s=0.8))

    def ui(img, fx):
        kicker(img, 'LIMITADOR DE VELOCIDAD', 150, seg(u, -0.1, 0.2), col=AZULC)
        candado(img, fx, 540, 560, 1.4, k=seg(u, ul - 0.1, ul + 0.1))
        velocimetro(img, fx, 540, 1330, 25 - 0.4 * abs(math.sin(t * 6)), k=1.0, col=CYAN, w=380, maxtxt='MÁX 25 KM/H')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ul + 0.1, 0.3), amp=14)


# 13. SEGUNDO GANCHO: el error («ERROR» de cristal, el scooter llega girando y se pone rojo)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, -60, 14, ty=0.75), K(0.35, 2.9, -24, 8, ty=0.75), K(d, 2.8, -18, 8, ty=0.75)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ERROR', u, t0=0.0, cy=0.4, entrada='golpe')
    e = P.entrada(u, -0.2, 0.3, 'gira')
    ms = scooter(pantalla=ROJO, freno=1.0)
    draw_objects(fr, P.tfk(ms, s=max(0.05, e['escala']), ry=math.degrees(e['giro'])))

    def ui(img, fx):
        kicker(img, 'Y AQUÍ VIENE…', 150, seg(u, -0.1, 0.1), col=(255, 120, 110))
        P.titulo_golpe(img, fx, [('El error', 'sans'), ('de casi todos.', 'serif')], 230, seg(u, 0.1, 0.25), size=86)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.35), amp=22)


# 14. quitarle el limitador para que corra más (el candado se abre y la pantalla salta a 35 en rojo)
def s_quitar(t, fi, u, d):
    uq = Wp(14, 'quitarle') - 0.1
    um = Wp(14, 'mas') - 0.15
    ab = P.eout4(seg(u, uq + 0.2, uq + 0.5))
    fr = Frame(camara(u, [K(-0.3, 3.0, 20, 24, ty=0.9), K(0.35, 2.6, 6, 22, ty=0.9), K(d, 2.5, 2, 22, ty=0.9)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9)
    draw_objects(fr, chip(k=1.0, s=0.8))
    v = 25 + 10 * P.eout4(seg(u, um - 0.1, um + 0.5))

    def ui(img, fx):
        kicker(img, 'DESBLOQUEADO · «PARA QUE CORRA MÁS»', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        candado(img, fx, 540 + 260 * ab, 560 - 200 * ab, 1.4 * (1 - 0.3 * ab), k=1 - seg(u, uq + 0.6, uq + 0.9), abierto=ab, col=ROJO if ab > 0.5 else AMARILLO)
        velocimetro(img, fx, 540, 1330, v, k=1.0, col=ROJO if v > 25.5 else CYAN, w=380)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, uq + 0.3, 0.3), golpe_k(u, um + 0.4, 0.3)), amp=16)


# 15. De 25 a 35 (números gigantes que golpean)
def s_de25(t, fi, u, d):
    u35 = Wp(15, 'treinta') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, 30, 10, ty=0.75), K(0.35, 3.3, 10, 8, ty=0.75), K(d, 3.2, 6, 8, ty=0.75)], cy=0.7))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.4)
    draw_objects(fr, scooter(giro=-t * 400, pantalla=ROJO if u > u35 else CYAN, motor_glow=0.6))
    off = (t * (3.0 if u < u35 else 5.0)) % 1.0
    for j in range(-4, 5):
        line3(fr, [(j - off, 0.005, 0.5), (j - off + 0.45, 0.005, 0.5)], col=AMARILLO, w=4, a=0.7, glow=0.6)

    def ui(img, fx):
        P.numero_golpe(img, fx, '25', 520, seg(u, -0.25, -0.1) * (1 - seg(u, u35 - 0.05, u35 + 0.05)), size=330, col=CYAN)
        P.numero_golpe(img, fx, '35', 520, seg(u, u35, u35 + 0.18), size=360, col=ROJO)
        texto(img, fx, 540, 760, 'KM/H', 44, GRIS, 1.0, f='mono', glow=0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, -0.1, 0.3), golpe_k(u, u35 + 0.18, 0.35)), amp=20)


# 16. la energía del golpe casi se duplica (gráfico 100 → 196 y «×2» de cristal)
def s_energia(t, fi, u, d):
    ud = Wp(16, 'duplica') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, 0, 20, ty=1.0), K(0.5, 4.6, -6, 16, ty=1.0), K(d, 4.5, -8, 16, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    M.cristal(fr.base, fr.fx, '×2', u, t0=ud, cy=0.3, entrada='zoom')

    def ui(img, fx):
        chart_grow(img, fx, (110, 640, 970, 1320), [100, 196], ['25 KM/H', '35 KM/H'], -0.1, u, unit='',
                   title_txt='ENERGÍA DEL GOLPE (25 = 100)', vmax=220, line=True, tag='½·m·v²')
        kicker(img, 'MÁS RÁPIDO = MUCHO MÁS GOLPE', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1420, '(35 ÷ 25)² = 1.96', 46, AMARILLO, seg(u, ud + 0.2, ud + 0.5), f='mono', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ud + 0.2, 0.3), amp=14)


# 17. Y para frenar necesitas casi el doble de distancia (dos carriles: a 25 y a 35)
def s_frenar(t, fi, u, d):
    ud = Wp(17, 'doble') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, 40, 34, tx=0.0, ty=0.3), K(0.35, 5.2, 12, 28, tx=0.0, ty=0.3), K(d, 5.1, 8, 28, tx=0.0, ty=0.3)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.7)
    X0 = -1.9
    D1, D2 = 1.4, 2.75
    ms = []
    for z, dd, v in ((-0.75, D1, 25), (0.75, D2, 35)):
        k = P.eout4(seg(u, 0.0, 0.6 + 0.9 * dd / D2))
        ms += P.tfk(scooter(freno=1.0, pantalla=CYAN if v == 25 else ROJO), s=0.6, t=(X0 + dd * k, 0, z))
        line3(fr, [(X0 - 0.6, 0.005, z - 0.45), (X0 + 4.0, 0.005, z - 0.45)], col=(200, 205, 215), w=2, a=0.5, glow=0.2)
        line3(fr, [(X0 + 0.6, 0.01, z - 0.3), (X0 + 0.6, 0.01, z + 0.3)], col=WHITE, w=4, a=0.8, glow=0.6)
        if k > 0.98:
            line3(fr, [(X0 + dd + 0.6, 0.01, z - 0.3), (X0 + dd + 0.6, 0.01, z + 0.3)], col=ROJO if v == 35 else CYAN, w=5, a=1.0, glow=1.0)
    draw_objects(fr, ms)
    p1 = fr.cam.p1((X0 + 0.9, 1.1, -0.75))
    p2 = fr.cam.p1((X0 + 0.9, 1.1, 0.75))

    def ui(img, fx):
        kicker(img, 'DISTANCIA PARA FRENAR · MISMOS FRENOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, p1[0], p1[1] - 90, '25 KM/H', 1.0, size=26, border=CYAN, dot=False)
        pill(img, fx, p2[0], p2[1] - 90, '35 KM/H', 1.0, size=26, border=ROJO, dot=False)
        texto(img, fx, 540, 1350, '≈ ×2', 120, ROJO, seg(u, ud, ud + 0.2), f='sansx', glow=0.5)
        esquema(img, fx, 1.0, txt='EJEMPLO · d = v² ÷ 2a')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ud + 0.1, 0.3), amp=14)


# 18. con los mismos frenitos (zoom digital a la salpicadera-freno de atrás que se calienta)
def s_frenitos(t, fi, u, d):
    uf = Wp(18, 'frenitos') - 0.1
    cal = P.eout4(seg(u, uf - 0.1, uf + 0.6))
    fr = Frame(camara(u, [K(-0.3, 2.6, -30, 10, tx=-0.5, ty=0.45), K(0.3, 1.5, -14, 8, tx=-0.6, ty=0.45), K(d, 1.45, -10, 8, tx=-0.62, ty=0.45)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    ms = scooter(giro=-t * 100 * (1 - cal), freno=1.0)
    for m in ms:
        if m.name == 'salpicadera':
            m.glow = M.scale_c((255, 90, 30), 0.7 * cal)
    draw_objects(fr, ms)
    P.ondas_calor(fr, t, XR, 0.6, 1.1, 0.4, k=cal)

    def ui(img, fx):
        rec_frame(img, t, k=1.0, zoom_label='x1.6')
        kicker(img, 'EL FRENO DE PISAR · ATRÁS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1380, 'LOS MISMOS FRENITOS · LAS MISMAS LLANTITAS', eout(seg(u, uf, uf + 0.3)), size=24, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. si pasa de 25 o su motor es de 250 watts o más (dos condiciones con «O» en medio)
def s_reglas(t, fi, u, d):
    uw = Wp(19, 'doscientos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, -40, 10, ty=0.75), K(0.35, 3.3, -16, 8, ty=0.75), K(d, 3.2, -12, 8, ty=0.75)], cy=0.66))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9, beam=0.5)
    draw_objects(fr, scooter(giro=-t * 200, motor_glow=seg(u, uw, uw + 0.3)))

    def ui(img, fx):
        kicker(img, 'SEMOVI · BASTA CON UNA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 330, 'MÁS DE 25 KM/H', eout(seg(u, 0.1, 0.4)), size=40, border=ROJO, dot=False)
        texto(img, fx, 540, 440, 'O', 60, WHITE, seg(u, uw - 0.4, uw - 0.2), f='serif', glow=0.3)
        pill(img, fx, 540, 550, 'MOTOR DE 250 W O MÁS', eout(seg(u, uw, uw + 0.3)), size=40, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uw + 0.2, 0.3), amp=12)


# 20. ya es otro vehículo (rayos X de golpe: el scooter se vuelve «VEMEPE»)
def s_otro(t, fi, u, d):
    uv = Wp(20, 'vehiculo') - 0.1
    x = seg(u, uv - 0.1, uv + 0.1)
    fr = Frame(camara(u, [K(-0.3, 3.5, 50, 12, ty=0.75), K(0.35, 2.9, 20, 8, ty=0.75), K(d, 2.8, 16, 8, ty=0.75)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.5)
    draw_objects(fr, scooter(placa=x, motor_glow=x, bat_glow=x), xray=0.9 * x, keep=('motor', 'tornillo', 'bateria', 'placa'))

    def ui(img, fx):
        kicker(img, 'YA NO ES «VEHÍCULO PERSONAL»', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.titulo_golpe(img, fx, [('VEMEPE', 'sans'), ('vehículo motorizado', 'serif')], 300, x, size=84)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uv + 0.1, 0.3), amp=18)


# 21. Lleva placa, tarjeta de circulación («PLACA» de cristal; los documentos caen y se pegan)
def s_papeles(t, fi, u, d):
    up = Wp(21, 'placa') - 0.12
    ut = Wp(21, 'tarjeta') - 0.12
    fr = Frame(camara(u, [K(-0.3, 4.6, 30, 16, ty=0.75), K(0.35, 4.2, 10, 14, ty=0.75), K(d, 4.1, 6, 14, ty=0.75)], cy=0.7))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    M.cristal(fr.base, fr.fx, 'PLACA', u, t0=up - 0.05, cy=0.3, entrada='golpe')
    draw_objects(fr, P.tfk(scooter(placa=1.0), s=0.8))

    def ui(img, fx):
        kicker(img, 'COMO UNA MOTO', 150, seg(u, -0.1, 0.2), col=AZULC)
        tarjeta2d(img, fx, 300, 1180, 420, 'placa', k=seg(u, up, up + 0.3), ang=-8 + 2 * math.sin(t * 2))
        tarjeta2d(img, fx, 770, 1260, 460, 'tarjeta', k=seg(u, ut, ut + 0.3), ang=6 + 2 * math.sin(t * 2 + 1))
        esquema(img, fx, 1.0, y=1500, txt='EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, up + 0.25, 0.25), golpe_k(u, ut + 0.25, 0.25)), amp=14)


# 22. y licencia tipo A, como una moto (la licencia gira y cae; A1 / A2)
def s_licencia(t, fi, u, d):
    ul = Wp(22, 'licencia') - 0.12
    um = Wp(22, 'moto') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, -30, 12, ty=0.8), K(0.35, 3.6, -10, 10, ty=0.8), K(d, 3.5, -6, 10, ty=0.8)], cy=0.68))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.4)

    def ui(img, fx):
        kicker(img, 'LICENCIA PARA MOTO', 150, seg(u, -0.1, 0.2), col=AZULC)
        tarjeta2d(img, fx, 540, 760, 640, 'licencia', k=seg(u, ul - 0.1, ul + 0.25), ang=-5 + 3 * math.sin(t * 2))
        pill(img, fx, 540, 1150, 'A1: MOTOS Y VEMEPE · A2: AUTO Y MOTO', eout(seg(u, um, um + 0.3)), size=26, border=AMARILLO, dot=False)
        esquema(img, fx, 1.0, y=1430, txt='EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ul + 0.2, 0.3), amp=14)


# 23. Sin papeles, te toca multa y hasta corralón (sello «MULTA»; la grúa levanta el scooter; «CORRALÓN» de cristal)
def s_corralon(t, fi, u, d):
    um = Wp(23, 'multa') - 0.1
    uc = Wp(23, 'corralon') - 0.15
    lift = P.eout4(seg(u, uc, uc + 0.8))
    fr = Frame(camara(u, [K(-0.3, 4.4, 30, 8, ty=1.0), K(0.35, 4.0, 10, 6, ty=1.0), K(d, 3.9, 6, 6, ty=1.0)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.6)
    M.cristal(fr.base, fr.fx, 'CORRALÓN', u, t0=uc, cy=0.6, entrada='sube')
    sw = 6 * math.sin(t * 4) * lift
    ms = P.tfk(scooter(), rz=sw, t=(0, 1.4 * lift, 0))
    draw_objects(fr, ms)
    line3(fr, [(0.47, 1.47 + 1.4 * lift, 0), (0.1, 4.5, 0)], col=CROMO, w=4, a=0.9, glow=0.4)
    line3(fr, [(-0.6, 0.55 + 1.4 * lift, 0), (0.1, 4.5, 0)], col=CROMO, w=4, a=0.9, glow=0.4)

    def ui(img, fx):
        kicker(img, 'SIN REGISTRO', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        if u > um:
            lay_k = seg(u, um, um + 0.15)
            P.titulo_golpe(img, fx, [('MULTA', 'sans')], 300, lay_k, size=120, col=ROJO, glow=0.5)
        pill(img, fx, 540, 1450, 'DE 10 A 20 UMA, SEGÚN SEMOVI', eout(seg(u, um + 0.3, um + 0.6)), size=24, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, um + 0.15, 0.3), golpe_k(u, uc + 0.1, 0.3)), amp=18)


# 24. Mándaselo a tu compa que anda en scooter sin placa (el scooter rueda y el título se estrella)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, -60, 10, ty=0.75), K(0.4, 3.0, -26, 6, ty=0.75), K(d, 2.9, -20, 6, ty=0.75)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    draw_objects(fr, scooter(giro=-t * 300, motor_glow=0.4))
    off = (t * 3.0) % 1.0
    for j in range(-4, 5):
        line3(fr, [(j - off, 0.005, 0.5), (j - off + 0.45, 0.005, 0.5)], col=AMARILLO, w=4, a=0.7, glow=0.6)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que anda en scooter sin placa.', 'serif')], 230, seg(u, 0.0, 0.15), size=64)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[(U_CHOQUE, 'sub', 1.0), (U_CHOQUE, 'bass', 0.9), (0.3, 'thud', 0.6)]),
           dict(desde=1, fn=s_cdmx, tr='deslizar_abajo', sfx=[(0.25, 'thud', 0.9), (0.4, 'chime_a', 0.4)]),
           dict(desde=2, fn=s_placa, tr='golpe', c=(0.3, 0.68), sfx=[(0.0, 'tick', 0.4), (0.4, 'tick', 0.4), (0.8, 'bass', 0.7)]),
           dict(desde=3, fn=s_quien, tr='giro', sfx=[(0.2, 'scribble', 0.6)]),
           dict(desde=4, fn=s_bici, tr='cubo', sfx=[(0.6, 'tick2', 0.4), (1.0, 'tick2', 0.4)]),
           dict(desde=5, fn=s_sincadena, tr='cubo_izq', c=(0.3, 0.75), sfx=[(0.5, 'scribble', 0.7)]),
           dict(desde=6, fn=s_escondido, tr='push', c=(0.5, 0.55), sfx=[(0.3, 'shimmer', 0.6), (0.9, 'scribble', 0.5)]),
           dict(desde=7, fn=s_bobinas, tr='zoom', sfx=[(0.5, 'tick2', 0.5), (1.0, 'click', 0.5)]),
           dict(desde=8, fn=s_imanes, tr='remolino', sfx=[(0.3, 'whoosh_suave', 0.6)]),
           dict(desde=9, fn=s_control, tr='mosaico', sfx=[(0.2 * j, 'tick', 0.3) for j in range(12)]),
           dict(desde=10, fn=s_persiguen, tr='whip', sfx=[(0.1, 'click', 0.6), (0.4, 'click', 0.6), (0.8, 'scribble', 0.4)]),
           dict(desde=11, fn=s_chip, tr='iris', c=(0.5, 0.55), sfx=[(0.3, 'digital', 0.6)]),
           dict(desde=12, fn=s_limitador, tr='deslizar', sfx=[(0.4, 'click', 0.8)]),
           dict(desde=13, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(0.25, 'bass', 0.9)]),
           dict(desde=14, fn=s_quitar, tr='glitch', sfx=[(0.5, 'click', 0.8), (1.0, 'riser', 0.5)]),
           dict(desde=15, fn=s_de25, tr='whip_izq', sfx=[(-0.1, 'bass', 0.8)]),
           dict(desde=16, fn=s_energia, tr='rebanadas', sfx=[(0.15 + 0.28 * j, 'chime_a' if j == 0 else 'chime_c', 0.5) for j in range(2)]),
           dict(desde=17, fn=s_frenar, tr='wipe', sfx=[(0.2, 'whoosh', 0.5), (1.2, 'thud', 0.6)]),
           dict(desde=18, fn=s_frenitos, tr='zoom', c=(0.35, 0.6), sfx=[(0.3, 'click', 0.6), (0.6, 'click', 0.6)]),
           dict(desde=19, fn=s_reglas, tr='deslizar_abajo', sfx=[(0.2, 'tick2', 0.5), (1.5, 'tick2', 0.5)]),
           dict(desde=20, fn=s_otro, tr='flash', sfx=[(0.3, 'shimmer', 0.6)]),
           dict(desde=21, fn=s_papeles, tr='cubo', sfx=[(0.3, 'slap', 0.8), (0.9, 'slap', 0.8)]),
           dict(desde=22, fn=s_licencia, tr='giro', sfx=[(0.2, 'slap', 0.8)]),
           dict(desde=23, fn=s_corralon, tr='push', c=(0.5, 0.5), sfx=[(0.6, 'riser', 0.5)]),
           dict(desde=24, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7)]),
           dict(desde=25, loop=True, tr='iris')]

if __name__ == '__main__':
    montaje.cli(globals())
