"""Reel diario sáb 21-nov-2026 10:00 (propuesto) — «Tu tráiler gringo… nació en Mexicali.»
Kenworth Mexicana (PACCAR) arma tractocamiones en Mexicali desde 1959 (más de 400 000; cerca del 20 % va a EE. UU.).
Por dentro: el diésel no tiene bujías de chispa: aprieta solo aire (14:1 a 22:1), lo calienta a más de 526 °C y el
diésel inyectado se enciende solo. Error (segundo gancho): apagarlo de volada después de una subida con carga: el turbo
(más de 100 000 rpm) se queda sin aceite y el aceite se cocina en los baleros; dejarlo de 1 a 3 minutos en marcha mínima.
Comunidad: traileros. Inicio tipo 11 (pregunta directa): «¿TU TRÁILER / ES GRINGO?» gigante en letras de cristal se
rompe en pedazos y deja ver el tractocamión con «MEXICALI» de cristal detrás. El final («acuérdate de Mexicali»)
regresa a la pregunta (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Fotos reales (dominio público, NASA): Mexicali desde la Estación Espacial (ISS071-E-131092, 2024) y un turbo en corte
(NASA Glenn, C-2003-1451). Datos y fuentes: guiones/2026-11-21_mexicali.txt. El tráiler, el cilindro, la bujía y el
turbo animados son esquemas sin marca (sin logos).
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
import demo_estilo as D
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import tubo, _B, texto, esquema, golpe_k, sacudir, K, camara
import trailer as TR
from italika import MX, gm

M3 = M.M3
TEMA = 'mexicali'
TXT = ['Tu tráiler gringo… nació en Mexicali.',
       'Kenworth arma tractocamiones en Mexicali',
       'desde 1959.',
       'Ya salieron más de 400 000,',
       'y algunos se van a Estados Unidos.',
       'Y su motor guarda un secreto:',
       'no tiene bujías de chispa.',
       'Uno de gasolina aprieta la mezcla',
       'y la prende con una chispa.',
       'El diésel solo aprieta aire, unas 20 veces,',
       'y lo calienta a más de 500 grados.',
       'Ahí le inyectan el diésel…',
       'y se enciende solito.',
       'Pero hay un error que mata al turbo…',
       'y casi todos lo cometen.',
       'Llegas de una subida con carga',
       'y lo apagas de volada.',
       'El turbo venía girando',
       'a más de 100 000 vueltas por minuto, hirviendo.',
       'Al apagar, el aceite deja de correr',
       'y se cocina en los baleros.',
       'Déjalo en marcha mínima de 1 a 3 minutos,',
       'y el aceite lo enfría.',
       'Ese ratito sale mucho más barato que un turbo nuevo.',
       'Mándaselo a tu compa trailero que apaga en cuanto llega.',
       'Y la próxima vez que oigas ese motor… acuérdate de Mexicali.']
VOZ = ['Tu tráiler gringo... nació en Mexicali.',
       'Kenworth arma tractocamiones en Mexicali',
       'desde mil novecientos cincuenta y nueve.',
       'Ya salieron más de cuatrocientos mil,',
       'y algunos se van a Estados Unidos.',
       'Y su motor guarda un secreto:',
       'no tiene bujías de chispa.',
       'Uno de gasolina aprieta la mezcla',
       'y la prende con una chispa.',
       'El diésel solo aprieta aire, unas veinte veces,',
       'y lo calienta a más de quinientos grados.',
       'Ahí le inyectan el diésel...',
       'y se enciende solito.',
       'Pero hay un error que mata al turbo...',
       'y casi todos lo cometen.',
       'Llegas de una subida con carga',
       'y lo apagas de volada.',
       'El turbo venía girando',
       'a más de cien mil vueltas por minuto, hirviendo.',
       'Al apagar, el aceite deja de correr',
       'y se cocina en los baleros.',
       'Déjalo en marcha mínima de uno a tres minutos,',
       'y el aceite lo enfría.',
       'Ese ratito sale mucho más barato que un turbo nuevo.',
       'Mándaselo a tu compa trailero que apaga en cuanto llega.',
       'Y la próxima vez que oigas ese motor... acuérdate de Mexicali.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_mexicali.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-21_mexicali_words.json')
IMG = os.path.join(HERE, 'img', 'mexicali')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
ROJO = (255, 60, 45)
AZUL_T = (28, 66, 150)          # el tractocamión de este reel es azul (el del freno de motor era rojo)
CROMO = (212, 214, 220)
ALUM = (196, 198, 204)
FIERRO = (88, 86, 90)
ACEITE = (236, 168, 52)
VERDE = (60, 210, 120)
CRED_ISS = 'FOTO: NASA · ESTACIÓN ESPACIAL · 2024'
CRED_TURBO = 'FOTO: NASA GLENN · TURBO EN CORTE'

# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    if not os.path.exists(WORDS):                       # todavía sin voz (pruebas): reparte por letras
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


_F = {}


def foto(nombre, caja=None):
    if nombre not in _F:
        p = os.path.join(IMG, nombre)
        if not os.path.exists(p):
            _F[nombre] = None
        else:
            im = Image.open(p).convert('RGB')
            if caja:
                w, h = im.size
                im = im.crop((int(w * caja[0]), int(h * caja[1]), int(w * caja[2]), int(h * caja[3])))
            _F[nombre] = im
    return _F[nombre]


def credito(img, txt, y=1470):
    texto(img, None, 540, y, txt, 20, (170, 170, 178), 1.0, f='mono', glow=0)


# ------------------------------------------------------------------ objetos
def recolor(ms, de, a):
    for m in ms:
        m.C = [a if c == de else c for c in m.C]
    return ms


def camion(giro=0.0, motor=False, faros=0.6, caja=True):
    return recolor(TR.trailer(giro=giro, motor=motor, faros=faros, caja=caja), TR.ROJO_C, AZUL_T)


def escena(t, u, claves, cy=0.58, roll=0.0, vel=4.0, motor=False, caja=True, floor_a=0.7, mont=True, beam=0.3):
    p = P.cam_rapida(u, claves)
    fr = Frame(Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy,
                   roll=p.get('roll', 0.0) + roll))
    space(fr, t, floor='lines', floor_a=floor_a, bokeh=0.9, beam=beam)
    if mont:
        TR.montes(fr)
    TR.carretera(fr, t, vel=vel)
    return fr, camion(giro=-t * vel / 0.21, motor=motor, caja=caja)


def bujia(chispa=0.0, t=0.0):
    """Bujía de chispa (sin marca): terminal, aislante de cerámica con costillas, hexágono, cuerda y electrodo."""
    ms = [named(M3.cyl(0.05, 0.22, CROMO, n=14, shadow=0, gloss=0.9).tf(t=(0, 1.62, 0)), 'terminal', rim=0.8),
          named(M3.cyl(0.13, 0.62, (238, 236, 230), n=26, shadow=0, gloss=0.75, r2=0.1).tf(t=(0, 1.0, 0)), 'ceramica', rim=0.7)]
    for j in range(4):
        ms.append(named(M3.cyl(0.145, 0.03, (246, 244, 238), n=26, shadow=0, gloss=0.7).tf(t=(0, 1.16 + 0.1 * j, 0)), 'costilla'))
    ms += [named(M3.cyl(0.24, 0.2, CROMO, n=6, shadow=0, gloss=0.95).tf(t=(0, 0.8, 0)), 'hex', rim=0.9, gloss=0.95),
           named(M3.cyl(0.16, 0.36, (168, 170, 176), n=22, shadow=0, gloss=0.6).tf(t=(0, 0.44, 0)), 'cuerda', rim=0.6)]
    for j in range(8):
        ms.append(named(M3.torus(0.162, 0.012, (120, 122, 128), nu=22, nv=5).tf(t=(0, 0.47 + 0.04 * j, 0)), 'hilo'))
    ms += [named(M3.cyl(0.03, 0.1, (210, 200, 180), n=10, shadow=0, gloss=0.6).tf(t=(0, 0.34, 0)), 'electrodo'),
           named(M3.box(0.05, 0.16, 0.05, (150, 150, 156), shadow=0, gloss=0.6).tf(t=(0.12, 0.28, 0)), 'masa'),
           named(M3.box(0.14, 0.04, 0.05, (150, 150, 156), shadow=0, gloss=0.6).tf(t=(0.06, 0.26, 0)), 'masa')]
    return ms


def chispazo(fr, t, p, k=1.0, seed=0, escala=1.0, col=(200, 230, 255)):
    """Rayito eléctrico que tiembla (line-art) y su destello."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(int(t * 24) + seed)
    p = np.asarray(p, float)
    for j in range(3):
        pts = [p + np.array([0, 0.0, 0])]
        for s in range(5):
            pts.append(p + np.array([(rng.rand() - 0.5) * 0.14 * escala, -0.05 * escala * (s + 1), (rng.rand() - 0.5) * 0.05]))
        line3(fr, pts, col=col, w=2.6, a=k, glow=1.6)
    dot3(fr, p + np.array([0, -0.13 * escala, 0]), r=int(10 + 8 * k), col=WHITE, a=k, glow=2.4)


def turbo(giro=0.0, calor=0.0, corte=0.0):
    """Turbo (esquema): caracol del compresor (aluminio), caracol de la turbina (fierro que se pone al rojo),
    eje con sus baleros y dos ruedas de álabes que giran (nombre 'in': se ven con rayos X)."""
    hot = M.mixc(FIERRO, (255, 96, 36), calor)
    ms = [named(M3.torus(0.52, 0.24, ALUM, nu=34, nv=12, gloss=0.7).tf(rz=90, t=(-0.62, 1.0, 0)), 'caracol', rim=0.8),
          named(M3.cyl(0.3, 0.3, ALUM, n=24, shadow=0, gloss=0.7).tf(rz=90, t=(-0.5, 1.0, 0)), 'caracol', rim=0.7),
          named(M3.cyl(0.2, 0.42, ALUM, n=20, shadow=0, gloss=0.8, r2=0.24).tf(rz=90, t=(-1.0, 1.0, 0)), 'boca', rim=0.8),
          named(M3.torus(0.5, 0.23, hot, nu=34, nv=12, gloss=0.4).tf(rz=90, t=(0.62, 1.0, 0)), 'turbina', rim=0.6),
          named(M3.cyl(0.22, 0.62, (120, 122, 130), n=20, shadow=0, gloss=0.6).tf(rz=90, t=(0.3, 1.0, 0)), 'centro', rim=0.6)]
    if calor > 0.05:
        ms[3].glow = M.scale_c((255, 80, 20), 0.75 * calor)
    # salidas de los caracoles (lo que hace que se vea como turbo y no como pesa)
    ms.append(named(tubo((-0.62, 1.5, 0.0), (-0.62, 1.5, 0.75), r=0.15, col=ALUM, n=16, name='caracol'), 'caracol', rim=0.8))
    ms.append(named(M3.cyl(0.2, 0.06, ALUM, n=20, shadow=0, gloss=0.7).tf(rx=90, t=(-0.62, 1.5, 0.78)), 'brida', rim=0.8))
    ms.append(named(tubo((0.62, 0.5, 0.0), (0.62, 0.5, -0.7), r=0.15, col=hot, n=16, name='turbina'), 'turbina', rim=0.6))
    ms.append(named(M3.box(0.42, 0.42, 0.06, M.mixc((70, 70, 74), (255, 96, 36), calor), shadow=0, gloss=0.4).tf(t=(0.62, 0.29, -0.72)), 'brida'))
    ms.append(named(M3.cyl(0.04, 1.5, (220, 222, 228), n=12, shadow=0, gloss=0.9).tf(rz=90, t=(0.75, 1.0, 0)), 'in', rim=0.9))
    for x0, col in ((-0.62, (226, 228, 234)), (0.62, M.mixc((170, 172, 178), (255, 140, 60), calor))):
        for j in range(10):
            a = giro + j * 36
            b = M3.box(0.22, 0.36, 0.025, col, shadow=0, base=False, gloss=0.8).tf(ry=24).tf(t=(0, 0.2, 0)).tf(rx=a)
            ms.append(named(b.tf(t=(x0, 1.0, 0)), 'in', rim=0.8, gloss=0.8))
    for x0 in (0.12, 0.48):                                   # baleros (bujes) en el centro
        ms.append(named(M3.torus(0.075, 0.03, (255, 210, 120), nu=18, nv=6).tf(rz=90, t=(x0, 1.0, 0)), 'in', rim=0.8))
    return ms


def flujo_aceite(fr, t, k=1.0, vel=1.0, col=ACEITE, cocido=0.0):
    """Puntos de aceite que bajan por el centro del turbo y pasan por los baleros (se detienen si vel = 0)."""
    if k <= 0.01:
        return
    ruta = [np.array(p) for p in ((0.3, 1.75, 0.15), (0.3, 1.3, 0.15), (0.12, 1.05, 0.15), (0.48, 1.05, 0.15),
                                  (0.3, 0.75, 0.15), (0.3, 0.3, 0.15))]
    c = M.mixc(col, (40, 26, 18), cocido)
    for j in range(16):
        ph = ((t * 0.7 * vel) + j / 16) % 1.0 if vel > 0 else (j / 16)
        s = ph * (len(ruta) - 1)
        q = int(s)
        p = ruta[q] + (ruta[min(q + 1, len(ruta) - 1)] - ruta[q]) * (s - q)
        dot3(fr, p, r=6, col=c, a=k, glow=1.0 * (1 - cocido) + 0.1)


def reloj(img, fx, cx, cy, R, frac, k=1.0, col=CYAN, txt=''):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c(WHITE, 0.8 * k), width=6)
    for j in range(12):
        a = math.radians(j * 30 - 90)
        d.line([(cx + (R - 26) * math.cos(a), cy + (R - 26) * math.sin(a)), (cx + (R - 8) * math.cos(a), cy + (R - 8) * math.sin(a))],
               fill=M.scale_c(WHITE, 0.6 * k), width=4)
    if frac > 0.001:
        d.arc((cx - R + 16, cy - R + 16, cx + R - 16, cy + R - 16), -90, -90 + 360 * frac, fill=M.scale_c(col, k), width=18)
        df.arc((cx - R + 16, cy - R + 16, cx + R - 16, cy + R - 16), -90, -90 + 360 * frac, fill=M.scale_c(col, 0.6 * k), width=34)
    a = math.radians(-90 + 360 * frac)
    d.line([(cx, cy), (cx + (R - 40) * math.cos(a), cy + (R - 40) * math.sin(a))], fill=M.scale_c(WHITE, k), width=7)
    if txt:
        texto(img, fx, cx, cy + R * 0.42, txt, int(R * 0.28), WHITE, k, f='mono', glow=0.3)


def tacometro(img, fx, cx, cy, R, nivel, k=1.0, txt='RPM'):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.arc((cx - R, cy - R, cx + R, cy + R), 150, 390, fill=M.scale_c(WHITE, 0.8 * k), width=6)
    df.arc((cx - R, cy - R, cx + R, cy + R), 330, 390, fill=M.scale_c(ROJO, 0.6 * k), width=16)
    a = math.radians(150 + 240 * clamp(nivel))
    d.line([(cx, cy), (cx + R * 0.86 * math.cos(a), cy + R * 0.86 * math.sin(a))], fill=ROJO, width=8)
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(220, 220, 226))
    texto(img, fx, cx, cy + R * 0.5, txt, 28, GRIS, k, f='mono', glow=0)


def mini_trailer(d, x, y, w, col):
    h = w * 0.36
    d.rectangle((x, y - h, x + w * 0.66, y), fill=col)                                       # caja
    d.rectangle((x + w * 0.69, y - h * 0.8, x + w * 0.84, y), fill=col)                      # cabina
    d.rectangle((x + w * 0.84, y - h * 0.45, x + w, y), fill=col)                            # cofre
    for xx in (0.1, 0.22, 0.75, 0.93):
        d.ellipse((x + w * xx - w * 0.045, y - w * 0.045, x + w * xx + w * 0.045, y + w * 0.045), fill=(10, 10, 12))


def recreacion(img, fx, k=1.0, y=1440, txt='RECREACIÓN'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


# ================================================================== escenas
# 0. gancho (inicio 11: pregunta directa). En el pre-roll (y en el loop) se ve «¿TU TRÁILER / ES GRINGO?» gigante de
#    cristal; en «nació» la pregunta se rompe en pedazos y deja ver el tractocamión azul con «MEXICALI» de cristal detrás.
def U_R():
    return Wp(0, 'naci') - 0.12


def pregunta_frame(t, fi, u):
    fr = Frame(camara(u, [K(-2.4, 6.4, -22, 8, ty=0.6), K(0.0, 5.6, -10, 6, ty=0.6), K(2.0, 5.3, -6, 6, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.55, bokeh=1.0, beam=0.45)
    M.cristal(fr.base, fr.fx, '¿TU TRÁILER', u, t0=-3.4, cy=0.36, entrada='golpe')
    M.cristal(fr.base, fr.fx, 'ES GRINGO?', u, t0=-3.2, cy=0.58, entrada='zoom')

    def ui(img, fx):
        kicker(img, 'TRAILEROS · LO QUE NO VES', 150, 1.0, col=AZULC)
    fr.ui.append(ui)
    return M.scale_about(finish(fr, fi), 1.0 + 0.05 * clamp((u + 2.0) / 3.0))


def _camion_gancho(t, fi, u):
    ur = U_R()
    fr, ms = escena(t, u, [K(ur - 0.1, 9.4, 62, 8, tx=0.3, ty=1.0), K(ur + 0.35, 7.2, 32, 6, tx=0.4, ty=1.0),
                           K(6, 6.8, 26, 6, tx=0.4, ty=1.0)], cy=0.62, vel=3.0)
    M.cristal(fr.base, fr.fx, 'MEXICALI', u, t0=ur - 0.02, cy=0.4, entrada='golpe')
    e = P.entrada(u, ur, 0.3, 'cae')
    draw_objects(fr, P.tfk(ms, t=(0, max(0.0, -e['dy']) * 0.6, 0)))

    def ui(img, fx):
        kicker(img, 'HECHO EN MÉXICO · BAJA CALIFORNIA', 150, seg(u, ur + 0.2, ur + 0.45), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu tráiler gringo…', 'sans'), ('nació en Mexicali.', 'serif')], 210, seg(u, ur + 0.05, ur + 0.2), size=76)
        recreacion(img, fx, seg(u, ur + 0.5, ur + 0.8))
    fr.ui.append(ui)
    return finish(fr, fi)


def s_gancho(t, fi, u, d):
    ur = U_R()
    if u < ur - 0.12:
        return pregunta_frame(t, fi, u)
    k = seg(u, ur - 0.12, ur + 0.26)
    B = _camion_gancho(t, fi, u)
    out = M.tr_rompe(pregunta_frame(t, fi, u), B, k, 0.5, 0.45) if k < 1 else B
    return sacudir(out, t, golpe_k(u, ur + 0.25, 0.4), amp=26)


# 1. Kenworth arma tractocamiones en Mexicali: el mapa de México se dibuja y la cámara cae sobre Mexicali
MXL = (-115.45, 32.62)


def s_mapa(t, fi, u, d):
    um = Wp(1, 'mexicali') - 0.1
    p = gm(*MXL)
    fr = Frame(camara(u, [K(-0.3, 8.6, 0, 70, tx=-0.6, ty=0.0, tz=-0.2), K(0.5, 7.4, 6, 64, tx=-2.0, ty=0.0, tz=-1.4),
                          K(um, 3.2, 10, 58, tx=p[0], ty=0.0, tz=p[2]), K(6, 2.9, 14, 56, tx=p[0], ty=0.0, tz=p[2])], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8)
    line3(fr, [gm(lo, la) for lo, la in MX], col=WHITE, w=4.0, a=1.0, glow=1.1, frac=min(1.0, 0.25 + P.eout4(seg(u, -0.3, 0.5))))
    for la in range(16, 34, 3):                                          # retícula tenue
        line3(fr, [gm(-118, la), gm(-86, la)], col=WHITE, w=1, a=0.12, glow=0)
    for lo in range(-117, -86, 3):
        line3(fr, [gm(lo, 14), gm(lo, 33)], col=WHITE, w=1, a=0.12, glow=0)
    line3(fr, [gm(-117.1, 32.53), gm(-114.7, 32.72), gm(-111.0, 31.33), gm(-106.5, 31.8)], col=AMARILLO, w=3, a=0.5, glow=0.6)
    pul = 0.5 + 0.5 * math.sin(t * 8)
    dot3(fr, p, r=10, col=AMARILLO, a=1.0, glow=1.6 + pul)
    for j in range(3):
        ph = (t * 1.2 + j / 3) % 1.0
        q = np.linspace(0, 2 * math.pi, 36)
        line3(fr, [p + np.array([0.6 * ph * math.cos(a), 0, 0.6 * ph * math.sin(a)]) for a in q], col=AMARILLO, w=2, a=(1 - ph) * 0.8, glow=0.9)
    px, py, _ = fr.cam.p1(tuple(p))

    def ui(img, fx):
        kicker(img, 'KENWORTH MEXICANA · PACCAR', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, px, py - 90, 'MEXICALI, B. C.', eout(seg(u, um, um + 0.25)), size=32, border=AMARILLO)
        pill(img, fx, 540, 1380, 'TRACTOCAMIONES KENWORTH Y PETERBILT', eout(seg(u, um + 0.4, um + 0.7)), size=24,
             border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.1, 0.3), amp=12)


# 2. desde 1959: la planta (portón de luz), chispas de soldadura y la cabina que avanza por la línea
def s_planta(t, fi, u, d):
    u59 = Wp(2, 'mil') - 0.05
    fr = Frame(camara(u, [K(-0.3, 5.0, 50, 8, tx=0.5, ty=1.0), K(0.5, 6.0, 20, 6, tx=0.2, ty=1.0), K(d, 5.8, 14, 6, tx=0.2, ty=1.0)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8, beam=0.6, beam_x=0.55)
    M.cristal(fr.base, fr.fx, '1959', u, t0=u59, cy=0.33, entrada='zoom')
    for x0 in (-3.4, -0.6, 2.2):                                       # portones de la nave
        line3(fr, [(x0, 0, -1.2), (x0, 2.6, -1.2), (x0 + 2.2, 2.6, -1.2), (x0 + 2.2, 0, -1.2)], col=WHITE, w=2.6, a=0.7, glow=0.6)
        for j in range(6):
            line3(fr, [(x0 + 0.18 + 0.37 * j, 2.6, -1.2), (x0 + 0.18 + 0.37 * j, 2.4, -1.2)], col=AMARILLO, w=3, a=0.6)
    for zz in (-0.8, 0.8):                                               # riel de la línea
        line3(fr, [(-6, 0.02, zz), (6, 0.02, zz)], col=AMARILLO, w=3, a=0.7, glow=0.7)
    x = -2.2 + 1.6 * P.eout4(seg(u, -0.2, 0.6)) + 0.12 * u
    ms = P.tfk(camion(caja=False, faros=0.3), s=0.75, t=(x, 0, 0))
    draw_objects(fr, ms)
    rng = np.random.RandomState(int(t * 24))
    sp = np.array([x + 1.0, 0.95, 0.55])
    for j in range(18):                                                  # chispas de soldadura
        a = rng.rand() * math.pi
        r = rng.rand() * 0.6
        dot3(fr, sp + np.array([r * math.cos(a), r * math.sin(a) * 0.8, rng.rand() * 0.2]), r=3, col=(255, 200, 120), a=0.9, glow=1.3)
    dot3(fr, sp, r=14, col=WHITE, a=0.6 + 0.4 * rng.rand(), glow=2.2)

    def ui(img, fx):
        kicker(img, 'PLANTA DE MEXICALI', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1300, 'MÁS DE 3 000 TRABAJADORES', eout(seg(u, u59 + 0.5, u59 + 0.8)), size=28, border=AMARILLO, dot=False)
        recreacion(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. ya salieron más de 400 000: filas de tráileres chiquitos que se llenan y el contador que se clava
def s_cuenta(t, fi, u, d):
    ufin = Wp(3, 'mil') + 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, 0, 20, ty=1.0), K(0.6, 5.0, -8, 14, ty=1.0), K(d, 4.8, -10, 14, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    llen = P.eout4(seg(u, -0.15, ufin))
    n = int(1 + 400000 * llen)

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        cols, rows = 7, 12
        tot = int(cols * rows * llen)
        for j in range(tot):
            r, c = divmod(j, cols)
            x = 70 + c * 138 + (r % 2) * 20
            y = 560 + r * 66
            mini_trailer(dd, x, y, 112, AZULC if j % 9 else AMARILLO)
        kicker(img, 'TRACTOCAMIONES HECHOS EN MEXICALI', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.numero_golpe(img, fx, f'{n:,}'.replace(',', ' '), 380, 1.0 if u > ufin else 0.99, size=170, col=WHITE)
        pill(img, fx, 540, 1400, 'UNIDAD 400 000: JULIO DE 2025', eout(seg(u, ufin + 0.2, ufin + 0.5)), size=26, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ufin, 0.35), amp=18)


# 4. y algunos se van a Estados Unidos: la foto REAL de Mexicali desde la Estación Espacial cae; la línea de la frontera
#    se marca punteada y unas flechas cruzan hacia Calexico (EE. UU.). En la foto el norte queda arriba a la izquierda.
def s_frontera(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, -20, 30, ty=0.0), K(0.5, 5.5, 0, 34, ty=0.0), K(d, 5.4, 4, 34, ty=0.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    im = foto('mxl_i_iss.jpg')
    out = finish(fr, fi)
    img = Image.fromarray(out)
    fx = Image.new('RGB', img.size, (0, 0, 0))
    if im is not None:
        e = P.entrada(u, -0.25, 0.3, 'cae')
        z = 1.0 + 0.12 * P.eout4(seg(u, 0.3, 0.9)) + 0.02 * u
        W0 = 1040
        H0 = int(W0 * im.size[1] / im.size[0])
        ph = im.resize((int(W0 * z), int(H0 * z)), Image.BILINEAR)
        ph = ph.crop(((ph.size[0] - W0) // 2, (ph.size[1] - H0) // 2, (ph.size[0] - W0) // 2 + W0, (ph.size[1] - H0) // 2 + H0))
        x0, y0 = 20, int(600 + e['dy'] * 160)
        img.paste(ph, (x0, y0))
        dd = ImageDraw.Draw(img)
        dd.rectangle((x0, y0, x0 + W0, y0 + H0), outline=(230, 230, 236), width=4)

        def fp(fx_, fy_):                                     # punto de la foto (fracción) → pantalla, con el zoom
            return x0 + W0 / 2 + (fx_ - 0.5) * W0 * z, y0 + H0 / 2 + (fy_ - 0.5) * H0 * z
        kb = seg(u, 0.35, 0.8)
        a0, a1 = fp(0.13, 0.84), fp(0.58, 0.0)
        for j in range(16):                                   # la frontera, punteada
            q0, q1 = j / 16, min(kb, (j + 0.55) / 16)
            if q1 > q0:
                dd.line([(a0[0] + (a1[0] - a0[0]) * q0, a0[1] + (a1[1] - a0[1]) * q0),
                         (a0[0] + (a1[0] - a0[0]) * q1, a0[1] + (a1[1] - a0[1]) * q1)], fill=AMARILLO, width=8)
        for j in range(3):
            ka = seg(u, 0.7 + 0.15 * j, 1.1 + 0.15 * j)
            s0, s1 = fp(0.42 + 0.05 * j, 0.62 - 0.06 * j), fp(0.2 + 0.05 * j, 0.32 - 0.06 * j)
            if ka > 0:
                doodle_arrow(img, fx, s0[0], s0[1], s1[0], s1[1], t, k=ka, col=CYAN, seed=j)
        c1, c2 = fp(0.52, 0.5), fp(0.12, 0.25)
        pill(img, fx, c1[0], c1[1], 'MEXICALI', eout(seg(u, 0.3, 0.55)), size=30, border=AMARILLO)
        pill(img, fx, c2[0] + 90, c2[1], 'CALEXICO, EE. UU.', eout(seg(u, 0.5, 0.75)), size=26, border=CYAN)
    kicker(img, 'FOTO REAL · LA FRONTERA DESDE EL ESPACIO', 150, seg(u, -0.1, 0.2), col=AZULC)
    pill(img, fx, 540, 470, 'CERCA DEL 20 % SE VA A ESTADOS UNIDOS', eout(seg(u, 0.6, 0.9)), size=26, border=AMARILLO, dot=False)
    credito(img, CRED_ISS, y=1340)
    a = np.asarray(img, np.float32) + np.asarray(fx.filter(ImageFilter.GaussianBlur(6)), np.float32) * 0.8
    return a.clip(0, 255).astype(np.uint8)


# 5. y su motor guarda un secreto: crash zoom al cofre y rayos X del motor diésel
def s_secreto(t, fi, u, d):
    us = Wp(5, 'secreto') - 0.1
    fr, ms = escena(t, u, [K(-0.3, 6.5, -40, 8, tx=0.6, ty=0.9), K(0.4, 5.0, -20, 10, tx=1.2, ty=0.8),
                           K(us, 2.4, 36, 22, tx=1.9, ty=0.7), K(5, 2.3, 40, 22, tx=1.9, ty=0.7)], cy=0.55, vel=2.5, motor=True, mont=False)
    draw_objects(fr, ms, xray=seg(u, us - 0.1, us + 0.25), keep=('in',))

    def ui(img, fx):
        kicker(img, 'RAYOS X · MOTOR DIÉSEL DE 6 CILINDROS', 150, seg(u, us, us + 0.3), col=AZULC)
        pill(img, fx, 540, 1330, '¿QUÉ LE FALTA?', eout(seg(u, us + 0.3, us + 0.6)), size=34, border=CYAN, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.05, 0.3), amp=12)


# 6. no tiene bujías de chispa: la bujía llega girando, da su chispa y se tacha
def s_bujia(t, fi, u, d):
    un = Wp(6, 'no') - 0.05
    ux = Wp(6, 'chispa') + 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, 60, 14, ty=1.0), K(0.5, 3.0, 16, 8, ty=0.95), K(d, 2.9, 8, 8, ty=0.95)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9, beam=0.5)
    M.cristal(fr.base, fr.fx, 'CHISPA', u, t0=ux - 0.35, cy=0.42, entrada='golpe')
    e = P.entrada(u, -0.25, 0.3, 'gira')
    draw_objects(fr, P.tfk(bujia(), s=max(0.05, e['escala']), ry=math.degrees(e['giro']) + 20 * math.sin(t * 0.8)))
    chispazo(fr, t, (0.04, 0.33, 0.06), k=(0.6 + 0.4 * math.sin(t * 30)) * seg(u, 0.2, 0.4) * (1 - seg(u, ux, ux + 0.2)))
    bx, by, _ = fr.cam.p1((0, 1.0, 0))

    def ui(img, fx):
        kicker(img, 'BUJÍA DE CHISPA', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > ux:
            N.doodle_arrow_free(img, fx, bx - 260, by - 380, bx + 260, by + 380, t, seg(u, ux, ux + 0.3), ROJO, seed=5)
            N.doodle_arrow_free(img, fx, bx + 260, by - 380, bx - 260, by + 380, t, seg(u, ux + 0.15, ux + 0.45), ROJO, seed=6)
        pill(img, fx, 540, 1380, 'EL DIÉSEL NO LA USA', eout(seg(u, ux + 0.3, ux + 0.6)), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ux, 0.3), amp=16)


# 7-8. CASO 1, gasolina: el pistón aprieta la mezcla (puntos naranjas) y la bujía la prende
def _cil_gas(t, fr, yp, chispa=0.0, fuego=0.0):
    col = M.mixc((255, 190, 120), (255, 120, 40), fuego)
    comp = TR.cilindro(fr, t, yp, col_aire=col, aire=1.0)
    draw_objects(fr, P.tfk(bujia(), s=0.32, t=(0, 1.62, 0)))
    chispazo(fr, t, (0.0, 1.73, 0.05), k=chispa, escala=0.8)
    if fuego > 0.01:
        dot3(fr, (0, 1.5, 0), r=int(18 + 30 * fuego), col=(255, 160, 70), a=fuego, glow=2.0)
    return comp


def s_gas1(t, fi, u, d):
    ua = Wp(7, 'aprieta') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, -40, 12, ty=1.1), K(0.4, 4.0, -18, 9, ty=1.1), K(ua + 0.3, 3.6, 10, 7, ty=1.2),
                          K(d, 3.5, 14, 7, ty=1.2)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    yp = 0.15 + 0.6 * P.eout4(seg(u, ua - 0.1, ua + 1.0))
    comp = _cil_gas(t, fr, yp)

    def ui(img, fx):
        texto(img, fx, 540, 250, 'CASO 1 · GASOLINA', 60, NARANJA, eout(seg(u, -0.1, 0.15)), f='sansx', glow=0.35)
        kicker(img, 'UN CILINDRO EN CORTE', 340, seg(u, 0.1, 0.4), col=AZULC)
        pill(img, fx, 830, 760, 'AIRE + GASOLINA', eout(seg(u, 0.3, 0.6)), size=26, border=NARANJA)
        texto(img, fx, 540, 1320, f'APRIETA {int(100 * comp)} %', 50, AMARILLO, seg(u, ua, ua + 0.2), f='mono', glow=0.3)
        esquema(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_gas2(t, fi, u, d):
    uc = Wp(8, 'chispa') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, 14, 7, ty=1.3), K(0.3, 2.6, 6, 6, ty=1.5), K(uc, 2.2, -4, 5, ty=1.55), K(d, 2.6, -12, 6, ty=1.4)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    fuego = seg(u, uc + 0.05, uc + 0.3) * (1 - 0.5 * seg(u, uc + 0.6, uc + 1.4))
    yp = 0.75 - 0.6 * P.eout4(seg(u, uc + 0.1, uc + 0.7))
    _cil_gas(t, fr, yp, chispa=seg(u, uc - 0.15, uc) * (1 - seg(u, uc + 0.3, uc + 0.5)), fuego=fuego)
    vx, vy, _ = fr.cam.p1((0, 1.7, 0))

    def ui(img, fx):
        texto(img, fx, 540, 250, 'CASO 1 · GASOLINA', 60, NARANJA, 1.0, f='sansx', glow=0.35)
        if u > uc - 0.2:
            doodle_circle(img, fx, vx, vy, 120, 90, t, k=seg(u, uc - 0.2, uc + 0.2), col=AMARILLO, seed=3)
            pill(img, fx, vx + 250, vy - 40, 'CHISPA', eout(seg(u, uc, uc + 0.2)), size=30, border=AMARILLO)
        rec_frame(img, t, k=seg(u, uc - 0.2, uc), zoom_label='x1.8')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.3), amp=18)


# 9-10. CASO 2, diésel: solo aire (cian) apretado ~20 veces, y se calienta a más de 500 °C
def s_diesel1(t, fi, u, d):
    u20 = Wp(9, 'veinte') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, 40, 12, ty=1.1), K(0.4, 4.0, 18, 9, ty=1.1), K(u20, 3.4, -12, 7, ty=1.3),
                          K(d, 3.3, -16, 7, ty=1.3)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '×20', u, t0=u20, cy=0.3, entrada='zoom')
    yp = 0.15 + 0.82 * P.eout4(seg(u, 0.0, u20 + 0.3))
    TR.cilindro(fr, t, yp, aire=1.0)
    ix, iy, _ = fr.cam.p1((0, 1.85, 0))

    def ui(img, fx):
        texto(img, fx, 540, 250, 'CASO 2 · DIÉSEL', 60, CYAN, eout(seg(u, -0.1, 0.15)), f='sansx', glow=0.35)
        kicker(img, 'SOLO AIRE · SIN BUJÍA', 340, seg(u, 0.1, 0.4), col=AZULC)
        n = 1 + int(19 * P.eout4(seg(u, 0.0, u20 + 0.3)))
        texto(img, fx, 540, 1320, f'{n} VECES MÁS APRETADO', 46, AMARILLO, seg(u, 0.2, 0.4), f='mono', glow=0.3)
        pill(img, fx, 540, 1410, 'COMPRESIÓN TÍPICA: DE 14 A 22 A 1', eout(seg(u, u20 + 0.4, u20 + 0.7)), size=22,
             border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u20 + 0.1, 0.3), amp=14)


def s_calor(t, fi, u, d):
    uq = Wp(10, 'quinientos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.2, -16, 7, ty=1.4), K(0.4, 2.7, 10, 5, ty=1.45), K(uq, 2.4, 22, 6, ty=1.5), K(d, 2.35, 26, 6, ty=1.5)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '500 °C', u, t0=uq, cy=0.28, entrada='golpe')
    cal = P.eout4(seg(u, 0.0, uq + 0.4))
    TR.cilindro(fr, t, 0.97, col_aire=M.mixc(CYAN, (255, 120, 40), cal), aire=1.0)
    P.ondas_calor(fr, t, 0.0, 1.75, 2.5, 0.9, k=cal)

    def ui(img, fx):
        P.termometro(img, fx, 150, 1330, 380, 0.15 + 0.8 * cal, f'{int(25 + 501 * cal)} °C', k=seg(u, -0.1, 0.1))
        kicker(img, 'EL AIRE APRETADO SE CALIENTA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 700, 1420, 'MÁS DE 526 °C', eout(seg(u, uq + 0.3, uq + 0.6)), size=28, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uq + 0.05, 0.3), amp=12)


# 11-12. le inyectan el diésel (rocío ámbar) y se enciende solito (bola de fuego, el pistón baja de golpe)
def inyector(fr, t, k_rocio=0.0):
    ms = [named(M3.cyl(0.07, 0.6, (200, 202, 210), n=14, shadow=0, gloss=0.9).tf(t=(0, 1.72, 0)), 'inyector', rim=0.9),
          named(M3.cyl(0.11, 0.18, (120, 124, 132), n=14, shadow=0, gloss=0.7).tf(t=(0, 2.1, 0)), 'inyector', rim=0.7),
          named(M3.cyl(0.04, 0.08, (60, 62, 68), n=10, shadow=0, gloss=0.6, r2=0.02).tf(t=(0, 1.66, 0)), 'punta')]
    draw_objects(fr, ms)
    if k_rocio > 0.01:
        rng = np.random.RandomState(3)
        for j in range(70):
            a = rng.rand() * 2 * math.pi
            s = (rng.rand() + t * 2.4) % 1.0 * k_rocio
            r = 0.55 * s * rng.rand()
            dot3(fr, (r * math.cos(a), 1.65 - 0.4 * s, r * math.sin(a)), r=3, col=(240, 190, 80), a=0.9 * k_rocio, glow=1.1)


def s_inyecta(t, fi, u, d):
    ui_ = Wp(11, 'inyectan') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.5, 30, 6, ty=1.5), K(0.4, 3.0, -10, 10, ty=1.5), K(d, 2.9, -16, 10, ty=1.5)], cy=0.52))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    TR.cilindro(fr, t, 0.97, col_aire=(255, 130, 50), aire=0.9)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    rocio = seg(u, ui_, ui_ + 0.4)
    inyector(fr, t, rocio)
    ix, iy, _ = fr.cam.p1((0, 1.9, 0))

    def ui(img, fx):
        kicker(img, 'INYECTOR · DIÉSEL A PRESIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, ix + 230, iy - 30, 'INYECTOR', eout(seg(u, 0.1, 0.4)), size=30, border=AMARILLO)
        pill(img, fx, 540, 1350, 'GOTITAS EN AIRE A MÁS DE 500 °C', eout(seg(u, ui_ + 0.3, ui_ + 0.6)), size=26, border=NARANJA, dot=False)
        esquema(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_enciende(t, fi, u, d):
    us = Wp(12, 'enciende') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.9, -16, 10, ty=1.4), K(us, 2.6, -6, 8, ty=1.3), K(us + 0.4, 4.2, 20, 12, ty=1.0), K(d, 4.0, 24, 12, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    f = seg(u, us, us + 0.15) * (1 - 0.6 * seg(u, us + 0.5, us + 1.6))
    yp = 0.97 - 0.85 * P.eout4(seg(u, us + 0.05, us + 0.45))
    TR.cilindro(fr, t, yp, col_aire=M.mixc((255, 150, 60), (255, 230, 160), f), aire=1.0)
    inyector(fr, t, 0.0)
    if f > 0.01:
        dot3(fr, (0, 1.45, 0), r=int(22 + 38 * f), col=(255, 170, 80), a=f, glow=2.2)
        for j in range(3):                                   # flechas: la explosión empuja el pistón
            line3(fr, [(-0.25 + 0.25 * j, 1.5, 0.6), (-0.25 + 0.25 * j, 1.5 - 0.8 * f, 0.6)], col=AMARILLO, w=5, a=f, glow=1.2)

    def ui(img, fx):
        kicker(img, 'SE ENCIENDE SOLO · SIN CHISPA', 150, seg(u, us, us + 0.2), col=AZULC)
        P.titulo_golpe(img, fx, [('Sin chispa.', 'sans'), ('Solo calor.', 'serif')], 230, seg(u, us + 0.1, us + 0.25), size=86)
    fr.ui.append(ui)
    out = finish(fr, fi, flash=0.5 * seg(u, us, us + 0.08) * (1 - seg(u, us + 0.08, us + 0.3)))
    return sacudir(out, t, golpe_k(u, us + 0.05, 0.45), amp=30)


# 13. SEGUNDO GANCHO: el error que mata al turbo (el turbo al rojo, «TURBO» de cristal, aviso)
def s_error(t, fi, u, d):
    ut = Wp(13, 'turbo') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.2, 60, 16, ty=1.0), K(0.35, 3.4, 24, 10, ty=1.0), K(ut, 3.0, -10, 8, ty=1.0), K(d, 2.9, -16, 8, ty=1.0)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'TURBO', u, t0=0.0, cy=0.38, entrada='golpe')
    e = P.entrada(u, -0.25, 0.3, 'pop')
    rojo = seg(u, ut, ut + 0.5)
    draw_objects(fr, P.tfk(turbo(giro=-t * 900, calor=rojo), s=max(0.05, e['escala']) * 0.9, ry=-35, t=(0, 0.1, 0)), xray=0.0)

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, -0.1, 0.1), col=(255, 120, 110))
        P.titulo_golpe(img, fx, [('El error que', 'sans'), ('mata al turbo.', 'serif')], 230, seg(u, ut, ut + 0.15), size=82)
        pill(img, fx, 540, 1380, '⚠ CASI TODOS LO COMETEN', eout(seg(u, ut + 0.5, ut + 0.8)), size=28, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut + 0.15, 0.35), amp=22)


# 14. y casi todos lo cometen: fila de tráileres en el parador que se apagan uno tras otro (clic, clic, clic)
def s_todos(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 9.0, 70, 20, tx=0.0, ty=0.6), K(0.4, 8.0, 40, 16, tx=0.0, ty=0.6), K(d, 7.6, 34, 16, tx=0.0, ty=0.6)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.2)
    ms = []
    pos = []
    for j in range(4):
        apag = u > 0.25 + 0.3 * j
        z = -2.4 + 1.6 * j
        ms += P.tfk(camion(caja=False, faros=0.0 if apag else 1.4), s=0.6, t=(0.0, 0, z))
        pos.append(((1.4, 0.4, z), apag))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'EN EL PARADOR · LLEGAN Y LOS APAGAN', 150, seg(u, -0.1, 0.2), col=AZULC)
        for j, (pp, apag) in enumerate(pos):
            x, y, _ = fr.cam.p1(pp)
            if apag:
                texto(img, fx, x, y - 150, 'OFF', 34, ROJO, seg(u, 0.25 + 0.3 * j, 0.35 + 0.3 * j), f='mono', glow=0.5)
        recreacion(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. llegas de una subida con carga (la cámara se inclina hacia arriba; tacómetro alto)
def s_subida(t, fi, u, d):
    fr, ms = escena(t, u, [K(-0.3, 8.5, -60, 6, tx=0.0, ty=1.0), K(0.4, 7.4, -30, 4, tx=0.0, ty=1.0), K(d, 7.0, -24, 4, tx=0.0, ty=1.0)],
                    cy=0.6, roll=8, vel=3.0)
    draw_objects(fr, ms)
    cx, cy = TR.chimenea_px(fr)

    def ui(img, fx):
        TR.tronido(img, fx, cx, cy, t, k=1.0, escala=0.9)
        kicker(img, 'SUBIDA LARGA · CAJA CARGADA', 150, seg(u, -0.1, 0.2), col=AZULC)
        tacometro(img, fx, 870, 420, 130, 0.78 + 0.04 * math.sin(t * 9), k=seg(u, 0.1, 0.3))
        recreacion(img, fx, 1.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.25, amp=5)


# 16. y lo apagas de volada: la llave gira a OFF, el tacómetro cae a 0 y todo se apaga de golpe
def s_apaga(t, fi, u, d):
    uo = Wp(16, 'apagas') - 0.05
    off = seg(u, uo, uo + 0.12)
    fr = Frame(camara(u, [K(-0.3, 3.0, -20, 10, ty=1.0), K(uo, 2.6, -8, 8, ty=1.0), K(uo + 0.3, 2.2, -4, 6, ty=1.0), K(d, 2.2, -2, 6, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6 * (1 - 0.6 * off), bokeh=0.8 * (1 - 0.6 * off))

    def ui(img, fx):
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        cx, cy, R = 540, 820, 230
        d_.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(18, 18, 22), outline=M.scale_c(WHITE, 0.8), width=6)
        for txt, a in (('OFF', -150), ('ACC', -110), ('ON', -60), ('START', -20)):
            r = math.radians(a)
            texto(img, fx, cx + (R + 70) * math.cos(r), cy + (R + 70) * math.sin(r), txt, 30,
                  ROJO if (txt == 'OFF' and off > 0.5) else GRIS, 1.0, f='mono', glow=0.3)
        ang = math.radians(-60 - 90 * P.eout4(off))
        L = R * 0.85
        d_.rounded_rectangle((cx - 40, cy - 40, cx + 40, cy + 40), radius=12, fill=(60, 62, 68))
        p0 = (cx - L * math.cos(ang) * 0.3, cy - L * math.sin(ang) * 0.3)
        p1 = (cx + L * math.cos(ang), cy + L * math.sin(ang))
        d_.line([p0, p1], fill=CROMO, width=46)
        df.line([p0, p1], fill=M.scale_c(CYAN, 0.25), width=70)
        tacometro(img, fx, 540, 1250, 150, 0.35 * (1 - P.eout4(seg(u, uo, uo + 0.4))), k=1.0)
        kicker(img, 'LLEGAS Y… APAGAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1460, 'EL TURBO SIGUE AL ROJO', eout(seg(u, uo + 0.4, uo + 0.7)), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uo + 0.1, 0.35), amp=22)


# 17-18. el turbo por dentro: rayos X, las ruedas de álabes giran y el contador sube a 100 000 rpm; se pone al rojo
def s_turbo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 70, 20, ty=1.0), K(0.4, 3.5, 30, 12, ty=1.0), K(d, 3.3, 22, 10, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    draw_objects(fr, turbo(giro=-t * 700, calor=0.35), xray=seg(u, 0.1, 0.5), keep=('in',))
    im = foto('mxl_i_turbo.jpg', (0.12, 0.02, 0.92, 0.74))

    def ui(img, fx):
        kicker(img, 'TURBO · RAYOS X', 150, seg(u, -0.1, 0.2), col=AZULC)
        if im is not None:
            photo_card(img, fx, im, 760, 1240, 380, 0.35, u, caption='TURBO EN CORTE (REAL)', angle0=8.0)
            credito(img, CRED_TURBO, y=1475)
        pill(img, fx, 300, 1180, 'GASES DEL ESCAPE → ← AIRE', eout(seg(u, 0.5, 0.8)), size=22, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_rpm(t, fi, u, d):
    uc = Wp(18, 'mil') + 0.1
    uh = Wp(18, 'hirviendo') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.6, 50, 8, tx=0.62, ty=1.0), K(0.3, 2.0, 80, 4, tx=0.62, ty=1.0), K(uh, 2.8, 40, 12, tx=0.3, ty=1.0),
                          K(d, 2.7, 36, 12, tx=0.3, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.9)
    M.cristal(fr.base, fr.fx, '100 000', u, t0=uc - 0.4, cy=0.3, entrada='zoom')
    cal = P.eout4(seg(u, uh - 0.2, uh + 0.5))
    draw_objects(fr, turbo(giro=-t * 1400, calor=0.35 + 0.65 * cal), xray=0.75, keep=('in',))
    P.ondas_calor(fr, t, 0.62, 1.6, 2.4, 0.8, k=cal)
    n = int(100000 * P.eout4(seg(u, 0.0, uc)))

    def ui(img, fx):
        kicker(img, 'VUELTAS POR MINUTO DEL TURBO', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1300, f'{n:,} RPM'.replace(',', ' '), 70, AMARILLO, seg(u, 0.0, 0.2), f='mono', glow=0.4)
        pill(img, fx, 540, 1400, 'HIRVIENDO', eout(seg(u, uh, uh + 0.25)), size=34, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc, 0.3), amp=14)


# 19-20. al apagar, el aceite deja de correr y se cocina en los baleros (zoom digital REC)
def s_aceite(t, fi, u, d):
    ud = Wp(19, 'deja') - 0.1
    vel = 1.0 - seg(u, ud, ud + 0.5)
    fr = Frame(camara(u, [K(-0.3, 3.4, -30, 10, tx=0.3, ty=1.05), K(0.4, 2.8, -6, 6, tx=0.3, ty=1.05), K(d, 2.7, -2, 6, tx=0.3, ty=1.05)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)
    draw_objects(fr, turbo(giro=-t * 900 * (0.4 + 0.6 * vel), calor=0.9), xray=0.85, keep=('in',))
    flujo_aceite(fr, t if vel > 0.02 else ud + 0.5, k=1.0, vel=vel)
    line3(fr, [(0.3, 2.3, 0.15), (0.3, 1.75, 0.15)], col=ACEITE, w=5, a=0.4 + 0.6 * vel, glow=0.8 * vel)

    def ui(img, fx):
        kicker(img, 'EL ACEITE LO ENFRÍA Y LO LUBRICA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 780, 520, 'ACEITE DEL MOTOR', eout(seg(u, 0.1, 0.4)), size=28, border=ACEITE)
        texto(img, fx, 540, 1330, 'MOTOR APAGADO = BOMBA DE ACEITE APAGADA', 34, ROJO, seg(u, ud, ud + 0.3), f='mono', glow=0.3)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_cocina(t, fi, u, d):
    uc = Wp(20, 'cocina') - 0.1
    coc = P.eout4(seg(u, uc, uc + 1.0))
    fr = Frame(camara(u, [K(-0.3, 2.6, 10, 6, tx=0.3, ty=1.0), K(0.3, 2.0, 20, 4, tx=0.3, ty=1.0), K(d, 1.9, 24, 4, tx=0.3, ty=1.0)], cy=0.64))
    space(fr, t, floor=None, bokeh=0.7)
    M.cristal(fr.base, fr.fx, 'BALEROS', u, t0=-0.1, cy=0.27, entrada='sube')
    draw_objects(fr, turbo(giro=0.0, calor=1.0), xray=0.9, keep=('in',))
    flujo_aceite(fr, 0.0, k=1.0, vel=0.0, cocido=coc)
    rng = np.random.RandomState(int(t * 12))
    for j in range(10):                                   # humito del aceite que se quema
        ph = (t * 0.9 + j / 10) % 1.0
        dot3(fr, (0.12 + 0.36 * (j % 2) + 0.05 * math.sin(t * 3 + j), 1.1 + 0.8 * ph, 0.2), r=int(6 + 14 * ph), col=(120, 112, 108),
             a=coc * (1 - ph) * 0.7, glow=0.2)
    bx, by, _ = fr.cam.p1((0.3, 1.0, 0.0))

    def ui(img, fx):
        kicker(img, 'ZOOM · LOS BALEROS DEL EJE', 150, seg(u, -0.1, 0.2), col=AZULC)
        rec_frame(img, t, k=1.0, zoom_label='x1.8' if u < uc else 'x3.0')
        if u > uc:
            doodle_circle(img, fx, bx, by, 260, 140, t, k=seg(u, uc, uc + 0.4), col=ROJO, seed=7)
        pill(img, fx, 540, 1380, 'EL ACEITE SE HACE CARBÓN', eout(seg(u, uc + 0.4, uc + 0.7)), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21-22. déjalo en marcha mínima de 1 a 3 minutos (cronómetro) y el aceite lo enfría (del rojo al metal)
def s_espera(t, fi, u, d):
    u3 = Wp(21, 'tres') - 0.1
    fr, ms = escena(t, u, [K(-0.3, 10.5, 40, 10, tx=0.0, ty=1.0), K(0.4, 9.6, 22, 8, tx=0.0, ty=1.0), K(d, 9.4, 18, 8, tx=0.0, ty=1.0)],
                    cy=0.8, vel=0.0, mont=False, beam=0.5)
    M.cristal(fr.base, fr.fx, '3 MIN', u, t0=u3, cy=0.25, entrada='golpe')
    draw_objects(fr, P.tfk(ms, t=(0, 0.01 * math.sin(t * 60), 0)))
    cx, cy = TR.chimenea_px(fr)

    def ui(img, fx):
        TR.tronido(img, fx, cx, cy, t, k=0.35, rate=3.0, escala=0.6)
        frac = P.eout4(seg(u, 0.0, u3 + 0.5)) * 0.75
        reloj(img, fx, 540, 900, 190, frac, k=seg(u, -0.1, 0.1), col=VERDE, txt=f'{1 + 2 * frac / 0.75:.0f} MIN')
        kicker(img, 'MARCHA MÍNIMA · DE 1 A 3 MINUTOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1410, 'DESPUÉS DE SUBIDA O CON CARGA', eout(seg(u, u3 + 0.4, u3 + 0.7)), size=26, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u3 + 0.05, 0.3), amp=14)


def s_enfria(t, fi, u, d):
    ue = Wp(22, 'enfria') - 0.1
    fria = P.eout4(seg(u, ue - 0.2, ue + 1.0))
    fr = Frame(camara(u, [K(-0.3, 3.0, 60, 10, tx=0.2, ty=1.0), K(0.4, 3.3, 20, 8, tx=0.2, ty=1.0), K(d, 3.2, 14, 8, tx=0.2, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    draw_objects(fr, turbo(giro=-t * 120, calor=1.0 - fria), xray=0.7, keep=('in',))
    flujo_aceite(fr, t, k=1.0, vel=1.0)
    P.ondas_calor(fr, t, 0.62, 1.6, 2.3, 0.8, k=1 - fria)

    def ui(img, fx):
        P.termometro(img, fx, 150, 1330, 380, 0.95 - 0.7 * fria, f'{int(600 - 450 * fria)} °C', k=1.0, col=M.mixc(ROJO, CYAN, fria))
        kicker(img, 'EL ACEITE SIGUE CORRIENDO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 680, 1430, 'SE ENFRÍA SIN QUEMARSE', eout(seg(u, ue + 0.3, ue + 0.6)), size=28, border=VERDE, dot=False)
        esquema(img, fx, 1.0, y=1500)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. ese ratito sale más barato que un turbo nuevo: dos casos lado a lado (3 minutos contra turbo nuevo $$$)
def s_barato(t, fi, u, d):
    ub = Wp(23, 'barato') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, -40, 14, tx=0.0, ty=1.0), K(0.4, 4.6, -12, 10, tx=0.0, ty=1.0), K(d, 4.5, -8, 10, tx=0.0, ty=1.0)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.4)
    e = P.entrada(u, ub - 0.2, 0.3, 'cae')
    draw_objects(fr, P.tfk(turbo(giro=-t * 60), s=0.7, t=(0.9, max(0.0, -e['dy']) * 0.5 + 0.2, 0)))
    tx, ty, _ = fr.cam.p1((0.9, 1.9, 0))

    def ui(img, fx):
        reloj(img, fx, 290, 860, 150, 0.75, k=seg(u, -0.1, 0.15), col=VERDE, txt='3 MIN')
        texto(img, fx, 290, 1080, 'ESPERAR', 40, VERDE, seg(u, 0.0, 0.2), f='mono', glow=0.3)
        texto(img, fx, 290, 1140, '$0', 70, VERDE, seg(u, 0.1, 0.3), f='sansx', glow=0.4)
        texto(img, fx, tx, ty - 40, 'TURBO NUEVO', 40, ROJO, seg(u, ub, ub + 0.2), f='mono', glow=0.3)
        texto(img, fx, tx, ty + 20, '$$$$', 80, ROJO, seg(u, ub + 0.1, ub + 0.3), f='sansx', glow=0.5)
        kicker(img, 'DOS CASOS', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.1, 0.3), amp=16)


# 24. mándaselo a tu compa trailero: foto real de Mexicali desde el espacio que cae y el tráiler de noche
def s_compa(t, fi, u, d):
    fr, ms = escena(t, u, [K(-0.3, 5.0, 100, 4, tx=1.5, ty=0.9), K(0.4, 4.2, 64, 2, tx=1.4, ty=0.9), K(d, 4.0, 56, 2, tx=1.4, ty=0.9)],
                    cy=0.66, vel=4.0, beam=0.0)
    ms = camion(giro=-t * 4 / 0.21, faros=1.6)
    draw_objects(fr, ms)
    fx_, fy_, _ = fr.cam.p1((2.36, 0.7, 0.33))
    im = foto('mxl_i_iss.jpg', (0.1, 0.1, 0.9, 0.9))

    def ui(img, fx):
        df = ImageDraw.Draw(fx)
        for j, r in enumerate((60, 120, 200)):
            df.ellipse((fx_ - r, fy_ - r * 0.6, fx_ + r, fy_ + r * 0.6), fill=M.scale_c((255, 220, 150), 0.35 / (j + 1)))
        P.titulo_golpe(img, fx, [('Mándaselo a tu', 'sans'), ('compa trailero.', 'serif')], 210, seg(u, 0.0, 0.15), size=80)
        if im is not None:
            photo_card(img, fx, im, 540, 760, 560, 0.25, u, caption='MEXICALI DESDE EL ESPACIO', angle0=-8.0)
            credito(img, CRED_ISS, y=1080)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45), sfx=[(-0.3, 'whoosh', 0.6)]),
           dict(desde=1, fn=s_mapa, tr='cubo', c=(0.5, 0.52), sfx=[(0.2, 'scribble', 0.5), (1.4, 'tick', 0.6)]),
           dict(desde=2, fn=s_planta, tr='zoom', sfx=[(0.2 + 0.1 * j, 'tick2', 0.3) for j in range(6)]),
           dict(desde=3, fn=s_cuenta, tr='rebanadas', sfx=[(0.1 * j, 'tick', 0.35) for j in range(12)]),
           dict(desde=4, fn=s_frontera, tr='deslizar', sfx=[(0.0, 'slap', 0.8), (0.7, 'scribble', 0.6)]),
           dict(desde=5, fn=s_secreto, tr='giro', c=(0.5, 0.55), sfx=[(0.5, 'shimmer', 0.6)]),
           dict(desde=6, fn=s_bujia, tr='glitch', sfx=[(0.3 + 0.1 * j, 'tick2', 0.4) for j in range(5)] + [(1.3, 'scribble', 0.7)]),
           dict(desde=7, fn=s_gas1, tr='wipe', sfx=[(0.6, 'whoosh_suave', 0.5)]),
           dict(desde=8, fn=s_gas2, tr='push', c=(0.5, 0.42), sfx=[(0.5, 'click', 0.7), (0.6, 'burst', 0.6)]),
           dict(desde=9, fn=s_diesel1, tr='cubo_izq', sfx=[(1.2, 'bass', 0.6)]),
           dict(desde=10, fn=s_calor, tr='remolino', sfx=[(0.4, 'riser', 0.4)]),
           dict(desde=11, fn=s_inyecta, tr='iris', c=(0.5, 0.3), sfx=[(0.6, 'whoosh', 0.4)]),
           dict(desde=12, fn=s_enciende, tr='golpe', sfx=[(0.5, 'sub', 1.0), (0.5, 'burst', 0.8)]),
           dict(desde=13, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(1.0, 'bass', 0.9)]),
           dict(desde=14, fn=s_todos, tr='whip', sfx=[(0.25 + 0.3 * j, 'click', 0.7) for j in range(4)]),
           dict(desde=15, fn=s_subida, tr='deslizar_abajo', sfx=[(0.2 + 0.12 * j, 'thud', 0.35) for j in range(6)]),
           dict(desde=16, fn=s_apaga, tr='flash', sfx=[(0.3, 'click', 1.0), (0.35, 'sub', 0.8)]),
           dict(desde=17, fn=s_turbo, tr='zoom', c=(0.5, 0.5), sfx=[(0.3, 'shimmer', 0.6), (0.4, 'slap', 0.6)]),
           dict(desde=18, fn=s_rpm, tr='mosaico', sfx=[(0.6, 'riser', 0.5)]),
           dict(desde=19, fn=s_aceite, tr='cubo', c=(0.58, 0.5), sfx=[(0.9, 'thud', 0.6)]),
           dict(desde=20, fn=s_cocina, tr='push', c=(0.55, 0.5), sfx=[(0.1, 'click', 0.6), (0.6, 'click', 0.6), (0.9, 'scribble', 0.5)]),
           dict(desde=21, fn=s_espera, tr='whip_izq', sfx=[(0.8, 'chime_a', 0.5)]),
           dict(desde=22, fn=s_enfria, tr='iris', c=(0.5, 0.45), sfx=[(0.6, 'chime_b', 0.5)]),
           dict(desde=23, fn=s_barato, tr='rebanadas', sfx=[(0.8, 'slap', 0.7)]),
           dict(desde=24, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7), (0.5, 'slap', 0.7)]),
           dict(desde=25, loop=True, tr='giro')]

if __name__ == '__main__':
    montaje.cli(globals())
