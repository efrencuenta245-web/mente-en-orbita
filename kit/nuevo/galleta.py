"""Reel diario vie 27-nov-2026 18:00 (propuesto) — «Tu refacción no es llanta… es galleta.»
La refacción temporal («galleta»): máximo 80 km/h (50 mph: AAA, Motor1, manual Kia 2027, Motorpasión México) y unos
80 km (AAA: 50 millas; Motorpasión: 80 a 112 km), lo justo para llegar a la llantera. Es como la mitad de ancha
(Motorpasión) y mucho más ligera (Motor1: se hizo para ahorrar espacio y peso); va inflada a unas 60 libras (manual
Kia: 60 psi / 420 kPa; Motor1: «some T-type spares… 60 psi»), casi el doble que una llanta normal. Pisa menos piso:
con lluvia agarra menos y puede patinar (Motorpasión; Motor1: cambia el manejo y el frenado). Error (segundo gancho):
traerla puesta semanas o meterle 120 en la autopista: se calienta, se gasta y puede fallar (Kia: «tire failure, loss of
vehicle control»); trae menos capas, costados más delgados y dibujo sencillo (Motorpasión; AAA Club Alliance); manejar
lejos con ella puede dañar otras piezas, hasta la transmisión (AAA). La trampa: olvidada en la cajuela pierde aire
(Motorpasión): revísale la presión. Comunidad: automovilistas. Inicio tipo 5 (número gigante): el «80» sube, se clava
con sacudida y se revela que es lo máximo de la galleta («GALLETA» de cristal detrás).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Datos y fuentes: guiones/2026-11-27_galleta.txt. Sin fotos reales (todo es esquema sin marca).
"""
import json, math, os, sys
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
import llanta as LL

M3 = M.M3
_NF = [0]


def finish(fr, fi=0, **kw):
    import gc
    out = M.finish(fr, fi, **kw)
    fr.ui.clear()
    _NF[0] += 1
    if _NF[0] % 40 == 0:
        gc.collect()
    return out


TEMA = 'galleta'
TXT = ['Tu refacción no es llanta… es galleta.',
       '80. Es lo más rápido que puedes ir con ella:',
       '80 km/h.',
       'Y no es para quedarse:',
       'aguanta unos 80 km, lo justo para llegar a la llantera.',
       'Ponla junto a tu llanta:',
       'es como la mitad de ancha, y mucho más ligera.',
       'Para cargar el carro con tan poquito hule,',
       'va inflada a unas 60 libras: casi el doble que tus llantas.',
       'Y como pisa menos piso,',
       'con lluvia agarra menos y puede patinar.',
       'Y aquí está el error:',
       'traerla puesta semanas…',
       'o meterle 120 en la autopista.',
       'Se calienta, se gasta rapidísimo',
       'y puede tronar justo cuando más la necesitas.',
       'Por dentro trae menos capas,',
       'costados más delgados y un dibujo sencillo.',
       'Y manejar lejos con ella castiga otras piezas del carro,',
       'hasta la transmisión.',
       'La otra trampa: pasa años olvidada en la cajuela…',
       'y pierde aire.',
       'Revísale el aire cuando revises las otras.',
       'Mándaselo a quien trae la galleta puesta desde hace un mes.',
       'Porque tu refacción no es llanta… es galleta.']
VOZ = ['Tu refacción no es llanta... es galleta.',
       'Ochenta. Es lo más rápido que puedes ir con ella:',
       'ochenta kilómetros por hora.',
       'Y no es para quedarse:',
       'aguanta unos ochenta kilómetros, lo justo para llegar a la llantera.',
       'Ponla junto a tu llanta:',
       'es como la mitad de ancha, y mucho más ligera.',
       'Para cargar el carro con tan poquito hule,',
       'va inflada a unas sesenta libras: casi el doble que tus llantas.',
       'Y como pisa menos piso,',
       'con lluvia agarra menos y puede patinar.',
       'Y aquí está el error:',
       'traerla puesta semanas...',
       'o meterle ciento veinte en la autopista.',
       'Se calienta, se gasta rapidísimo',
       'y puede tronar justo cuando más la necesitas.',
       'Por dentro trae menos capas,',
       'costados más delgados y un dibujo sencillo.',
       'Y manejar lejos con ella castiga otras piezas del carro,',
       'hasta la transmisión.',
       'La otra trampa: pasa años olvidada en la cajuela...',
       'y pierde aire.',
       'Revísale el aire cuando revises las otras.',
       'Mándaselo a quien trae la galleta puesta desde hace un mes.',
       'Porque tu refacción no es llanta... es galleta.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_galleta.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-27_galleta_words.json')

AMARILLO = (255, 236, 160)
AMBAR = (255, 176, 40)
NARANJA = (255, 130, 50)
ROJO = (240, 50, 42)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (90, 220, 140)
CARRO = (40, 92, 160)           # sedán azul sin marca
LETRAS = (255, 214, 60)         # letras amarillas de la galleta
CROMO = (205, 208, 215)
HULE = (30, 30, 33)

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
    ws_ = [montaje._norm(w) for w in VOZ[i].split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws_) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ objetos
def _angosta(ms, f):
    out = P.tfk(ms)
    for m in out:
        m.V = np.asarray(m.V, float) * np.array([1.0, 1.0, f])
    return out


def galleta_m(giro=0.0, sag=0.0, caliente=0.0, bulto=0.0, hombros=0.0, x=0.0, z=0.0, ry=0.0, s=0.86):
    """La galleta: la misma llanta semirrealista pero angosta (×0.5), más chica y con letras amarillas en el costado."""
    ms, cy = LL.llanta_m(sag=sag, giro=giro, caliente=caliente, bulto=bulto, hombros=hombros, s=s)
    ms = _angosta(ms, 0.5)
    for zz in (0.075, -0.075):
        ring = M3.torus(LL.RT * s * 1.08, 0.012, LETRAS, nu=48, nv=5).tf(rx=90, t=(0, cy, zz))
        ms.append(named(ring, 'letras', glow=M.scale_c(LETRAS, 0.35)))
    return P.tfk(ms, ry=ry, t=(x, 0, z)), cy


def llanta_n(giro=0.0, x=0.0, z=0.0, ry=0.0, **kw):
    ms, cy = LL.llanta_m(giro=giro, **kw)
    return P.tfk(ms, ry=ry, t=(x, 0, z)), cy


def carro_g(giro=0.0, galleta=True, col=CARRO, marca=0.0, cajuela=0.0):
    """Sedán sin marca (frente hacia +x) con la galleta puesta atrás a la derecha (+z)."""
    ms = []
    ms.append(named(M3.rbox(3.0, 0.5, 1.25, 0.22, col, n=5, shadow=0, gloss=0.8).tf(t=(0, 0.32, 0)), 'cuerpo', rim=0.8, gloss=0.8))
    ms.append(named(M3.rbox(1.55, 0.46, 1.1, 0.25, (30, 34, 42), n=5, shadow=0, gloss=0.95).tf(t=(-0.2, 0.8, 0)), 'vidrio', rim=0.9, gloss=0.95))
    ms.append(named(M3.rbox(1.3, 0.06, 1.0, 0.2, col, n=4, shadow=0, gloss=0.8).tf(t=(-0.22, 1.25, 0)), 'cuerpo', rim=0.8))
    if cajuela > 0.01:
        lid = M3.rbox(0.62, 0.05, 1.15, 0.03, col, n=3, shadow=0, gloss=0.8).tf(t=(-0.31, 0, 0)).tf(rz=-75 * cajuela).tf(t=(-0.98, 0.6, 0))
        ms.append(named(lid, 'cajuela', rim=0.8, gloss=0.8))
    for x in (1.0, -1.0):
        for zz in (0.6, -0.68):
            gal = galleta and x < 0 and zz > 0
            if gal:
                w = V.rueda(0.29, (0, 0, 0), giro * 0.33 / 0.29, ancho=0.11, marca=False)
                for m in w:
                    if getattr(m, 'name', '') == 'llanta':
                        m.glow = M.scale_c(LETRAS, 0.25 + 0.5 * marca)
                ms += P.tfk(w, t=(x, 0.29, zz + 0.16))
            else:
                ms += P.tfk(V.rueda(0.33, (0, 0, 0), giro), t=(x, 0.33, zz + 0.1))
    for zz in (-0.45, 0.45):
        _B(ms, 0.04, 0.12, 0.26, (255, 248, 230), 1.5, 0.55, zz, glow=(160, 150, 120))
        _B(ms, 0.04, 0.1, 0.26, (200, 30, 30), -1.5, 0.58, zz, glow=(120, 20, 20))
    return ms


GAL_POS = (-1.0, 0.29, 0.76)       # centro de la galleta en el carro


def manometro(img, fx, cx, cy, r, psi, k=1.0, vmax=80, txt='LIBRAS (PSI)', col=ROJO):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    rr_ = r * P.resorte(k) if k < 1 else r
    d.ellipse((cx - rr_, cy - rr_, cx + rr_, cy + rr_), fill=(14, 15, 19), outline=(220, 224, 232), width=6)
    a0, a1 = 135, 405

    def ang(v):
        return math.radians(a0 + (a1 - a0) * clamp(v / vmax))
    for v in range(0, vmax + 1, 5):
        a = ang(v)
        L = 0.16 if v % 20 == 0 else 0.08
        d.line([(cx + rr_ * 0.92 * math.cos(a), cy + rr_ * 0.92 * math.sin(a)),
                (cx + rr_ * (0.92 - L) * math.cos(a), cy + rr_ * (0.92 - L) * math.sin(a))], fill=(220, 224, 232), width=4)
        if v % 20 == 0:
            d.text((cx + rr_ * 0.6 * math.cos(a), cy + rr_ * 0.6 * math.sin(a)), str(v), font=M.font('mono', int(rr_ * 0.17)),
                   fill=(220, 224, 232), anchor='mm')
    a = ang(psi)
    d.line([(cx, cy), (cx + rr_ * 0.78 * math.cos(a), cy + rr_ * 0.78 * math.sin(a))], fill=col, width=8)
    df.line([(cx, cy), (cx + rr_ * 0.78 * math.cos(a), cy + rr_ * 0.78 * math.sin(a))], fill=M.scale_c(col, 0.6), width=16)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(220, 224, 232))
    d.text((cx, cy + rr_ * 0.45), txt, font=M.font('mono', int(rr_ * 0.11)), fill=(160, 166, 178), anchor='mm')
    d.text((cx, cy + rr_ * 0.7), f'{psi:.0f}', font=M.font('mono', int(rr_ * 0.22)), fill=(236, 238, 242), anchor='mm')


def lluvia(img, t, k=1.0, n=70, seed=3):
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    d = ImageDraw.Draw(img)
    for j in range(n):
        x0 = rng.uniform(0, 1080)
        ph = (t * 2.2 + rng.rand()) % 1.0
        y0 = -100 + ph * 2100
        d.line([(x0, y0), (x0 - 14, y0 + 60)], fill=M.scale_c(AZULC, 0.55 * k), width=2)


def tache(img, fx, x, y, r, k, col=ROJO, w=12):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    kk = eout(k)
    for s_ in (-1, 1):
        d.line([(x - r * kk, y - s_ * r * kk), (x + r * kk, y + s_ * r * kk)], fill=col, width=w)
        df.line([(x - r * kk, y - s_ * r * kk), (x + r * kk, y + s_ * r * kk)], fill=M.scale_c(col, 0.6), width=w * 3)


def engrane(n=14, r=0.5, giro=0.0, col=(170, 172, 180), calor=0.0, x=0.0, y=0.0, z=0.0):
    c = M.mixc(col, (255, 90, 40), calor)
    ms = [named(M3.cyl(r, 0.16, c, n=36, shadow=0, gloss=0.8, y0=-0.08).tf(rx=90), 'engrane', rim=0.8, gloss=0.8)]
    for j in range(n):
        a = giro + j * 360 / n
        b = M3.box(0.12, r * 0.22, 0.16, c, shadow=0, base=False, gloss=0.8).tf(t=(0, r + r * 0.08, 0)).tf(rz=a)
        ms.append(named(b, 'diente', rim=0.8))
    ms.append(named(M3.cyl(r * 0.2, 0.2, (80, 82, 90), n=16, shadow=0, gloss=0.6, y0=-0.1).tf(rx=90), 'eje', rim=0.6))
    if calor > 0.05:
        for m in ms[:-1]:
            m.glow = M.scale_c((255, 80, 30), 0.6 * calor)
    return P.tfk(ms, t=(x, y, z))


def carretera(fr, t, vel=1.0, a=0.8):
    for z in (-1.6, 1.6):
        line3(fr, [(-9, 0.01, z), (9, 0.01, z)], col=WHITE, w=2.4, a=a, glow=0.5)
    for j in range(14):
        x = -9 + ((j * 1.4 - t * 6 * vel) % 19.6)
        line3(fr, [(x, 0.01, 0), (x + 0.7, 0.01, 0)], col=AMARILLO, w=3, a=a, glow=0.6)


GIRO = lambda t, v=1.0: -t * 6.0 * v / 0.33

# ================================================================== escenas
UC = -0.1          # el 80 se clava


def s_gancho(t, fi, u, d):
    ut = Wp(0, 'galleta') - 0.15
    fr = Frame(camara(u, [K(-3.0, 6.0, -20, 8, ty=0.8), K(UC, 5.4, -14, 8, ty=0.8), K(0.4, 3.8, 26, 10, ty=0.75),
                          K(ut, 3.5, 32, 10, ty=0.75), K(5.0, 3.4, 36, 10, ty=0.75)], cy=0.68))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'GALLETA', u, t0=-2.6, cy=0.44, entrada='golpe')
    e = P.entrada(u, UC, 0.25, 'pop')
    ms, cy = galleta_m(giro=12 * math.sin(t * 1.3))
    draw_objects(fr, P.tfk(ms, s=max(0.05, e['escala'])))
    n = 80 * P.eout4(seg(u, -2.4, UC))
    kn = 1 - seg(u, ut - 0.05, ut + 0.1)

    def ui(img, fx):
        if kn > 0.01:
            P.numero_golpe(img, fx, f'{n:.0f}', 360, kn, size=300, col=M.mixc(WHITE, AMBAR, seg(u, UC, UC + 0.2)))
        kicker(img, 'LLANTA DE REFACCIÓN TEMPORAL', 140, 1.0, col=AMARILLO)
        P.titulo_golpe(img, fx, [('Tu refacción no es llanta…', 'sans'), ('es galleta.', 'serif')], 200, seg(u, ut, ut + 0.15), size=68)
        x, y, _ = fr.cam.p1((0, cy * 1.95, 0))
        pill(img, fx, x, y - 30, 'MÁX. 80 KM/H', eout(seg(u, UC + 0.2, UC + 0.45)), size=28, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, UC, 0.4), golpe_k(u, ut + 0.15, 0.3)), amp=26)


# 1. ochenta: es lo más rápido que puedes ir con ella (el velocímetro: después de 80 todo es rojo)
def s_80(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, -40, 8, ty=0.6), K(0.3, 3.8, -12, 6, ty=0.6), K(5, 3.75, -8, 6, ty=0.6)], cy=0.8))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    ms, cy = galleta_m(giro=math.degrees(GIRO(t, 0.4)), s=0.7)
    draw_objects(fr, ms)
    kv = P.eout4(seg(u, -0.1, 0.5))

    def ui(img, fx):
        V.tablero(img, fx, 540, 640, 300, 80 * kv, k=seg(u, -0.2, 0.1), rango=(80, 200, ROJO))
        texto(img, fx, 540, 1080, 'NO MÁS DE 80', 40, AMARILLO, seg(u, Wp(1, 'rapido') - 0.2, Wp(1, 'rapido')), f='mono', glow=0.4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. 80 km/h (número que golpea junto al costado de la galleta)
def s_kmh(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.6, 70, 6, ty=0.75), K(0.3, 2.2, 84, 4, ty=0.75), K(5, 2.18, 86, 4, ty=0.75)], cy=0.66))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    ms, cy = galleta_m(giro=10 * math.sin(t))
    draw_objects(fr, ms)

    def ui(img, fx):
        P.numero_golpe(img, fx, '80 km/h', 380, seg(u, -0.1, 0.12), size=190, col=AMARILLO)
        pill(img, fx, 540, 560, 'VELOCIDAD MÁXIMA · MANUAL Y AAA', eout(seg(u, 0.2, 0.45)), size=24, border=GRIS, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.12, 0.3), amp=18)


# 3. y no es para quedarse (el carro con la galleta puesta: sello TEMPORAL)
def s_quedarse(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.6, 10, 14, tx=-0.2, ty=0.5), K(0.3, 6.6, 36, 12, tx=-0.3, ty=0.5), K(5, 6.5, 40, 12, tx=-0.3, ty=0.5)], cy=0.64))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    draw_objects(fr, carro_g(marca=1.0))

    def ui(img, fx):
        x, y, _ = fr.cam.p1(GAL_POS)
        doodle_circle(img, fx, x, y, 110, 110, t, k=seg(u, 0.0, 0.3), col=AMARILLO, seed=2)
        ks = seg(u, Wp(3, 'quedarse') - 0.15, Wp(3, 'quedarse'))
        if ks > 0:
            lay = Image.new('L', (520, 150), 0)
            dd = ImageDraw.Draw(lay)
            dd.rounded_rectangle((6, 6, 514, 144), radius=18, outline=255, width=10)
            dd.text((260, 76), 'TEMPORAL', font=M.font('sansx', 84), fill=255, anchor='mm')
            s_ = 1.8 - 0.8 * P.eout4(ks)
            lay = lay.rotate(-12, expand=True, resample=Image.BILINEAR)
            lay = lay.resize((int(lay.size[0] * s_), int(lay.size[1] * s_)), Image.BILINEAR)
            img.paste(Image.new('RGB', lay.size, ROJO), (540 - lay.size[0] // 2, 430 - lay.size[1] // 2), lay.point(lambda v: int(v * min(1, ks * 2))))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(3, 'quedarse'), 0.3), amp=14)


# 4. aguanta unos 80 km, lo justo para llegar a la llantera («LLANTERA» de cristal; ruta con contador)
def s_llantera(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.0, -10, 24, tx=0.0, ty=0.5), K(0.3, 7.0, -24, 20, tx=0.0, ty=0.5), K(5, 6.95, -26, 20, tx=0.0, ty=0.5)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, 'LLANTERA', u, t0=Wp(4, 'llantera') - 0.3, cy=0.27, entrada='sube')
    kr = seg(u, 0.0, Wp(4, 'llantera'))
    x = -3.0 + 5.0 * kr
    line3(fr, [(-3.6, 0.01, 0), (2.6, 0.01, 0)], col=AMARILLO, w=4, a=0.8, glow=0.6, frac=1.0)
    ms = P.tfk(carro_g(giro=GIRO(t, 0.5), marca=0.6), s=0.5, t=(x, 0, 0))
    ms.append(named(M3.cyl(0.04, 1.4, (150, 152, 160), n=10, shadow=0).tf(t=(2.9, 0, -0.5)), 'poste', rim=0.7))
    ms.append(named(M3.box(1.0, 0.45, 0.06, (230, 230, 236), shadow=0, base=False).tf(t=(2.9, 1.5, -0.5)), 'letrero', rim=0.8, glow=(60, 60, 64)))
    draw_objects(fr, ms)

    def ui(img, fx):
        xs, ys, _ = fr.cam.p1((2.9, 1.5, -0.45))
        texto(img, fx, xs, ys, 'LLANTERA', 30, (20, 20, 24), 1.0, f='sansx', glow=0.0)
        km = 80 * kr
        texto(img, fx, 540, 1180, f'{km:.0f} km', 96, AMARILLO, seg(u, -0.1, 0.2), f='mono', glow=0.5)
        pill(img, fx, 540, 1290, 'AAA: UNAS 50 MILLAS ≈ 80 KM', eout(seg(u, Wp(4, 'ochenta') - 0.2, Wp(4, 'ochenta'))), size=24, border=GRIS, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. ponla junto a tu llanta (las dos caen lado a lado)
def _par(t, u, claves, cy=0.62, giro=0.0):
    fr = Frame(camara(u, claves, cy=cy))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    e1 = P.entrada(u, -0.25, 0.3, 'cae')
    e2 = P.entrada(u, -0.12, 0.3, 'cae')
    a, _ = llanta_n(giro=giro, z=0.75)
    b, _ = galleta_m(giro=giro, z=-0.75)
    return fr, P.tfk(a, t=(0, -e1['dy'] * 0.5, 0)) + P.tfk(b, t=(0, -e2['dy'] * 0.5, 0))


def s_junto(t, fi, u, d):
    fr, ms = _par(t, u, [K(-0.3, 6.0, 40, 12, ty=0.8), K(0.3, 5.0, 60, 10, ty=0.8), K(5, 4.95, 62, 10, ty=0.8)])
    draw_objects(fr, ms)

    def ui(img, fx):
        xa, ya, _ = fr.cam.p1((0, 1.95, 0.75))
        xb, yb, _ = fr.cam.p1((0, 1.7, -0.75))
        pill(img, fx, xa, ya - 40, 'TU LLANTA', eout(seg(u, Wp(5, 'llanta') - 0.2, Wp(5, 'llanta'))), size=28, border=WHITE)
        pill(img, fx, xb, yb - 40, 'GALLETA', eout(seg(u, 0.1, 0.35)), size=28, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.05, 0.25), golpe_k(u, 0.18, 0.25)), amp=14)


# 6. es como la mitad de ancha, y mucho más ligera («MITAD» de cristal; cotas de ancho, vista de frente)
def s_mitad(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.4, 60, 10, ty=0.8), K(0.3, 4.6, 88, 6, ty=0.8), K(5, 4.55, 90, 6, ty=0.8)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'MITAD', u, t0=Wp(6, 'mitad') - 0.3, cy=0.27, entrada='zoom')
    a, _ = llanta_n(z=0.75)
    b, _ = galleta_m(z=-0.75)
    draw_objects(fr, a + b)

    def ui(img, fx):
        kc = seg(u, Wp(6, 'ancha') - 0.2, Wp(6, 'ancha') + 0.2)
        dd = ImageDraw.Draw(img)
        for zc, w, lab in ((0.75, 0.27, '1'), (-0.75, 0.135, '½')):
            xa, ya, _ = fr.cam.p1((0, 1.95, zc - w))
            xb, yb, _ = fr.cam.p1((0, 1.95, zc + w))
            if kc > 0:
                dd.line([(xa, ya - 40), (xa + (xb - xa) * kc, yb - 40)], fill=AMARILLO, width=5)
                for xx in (xa, xb):
                    dd.line([(xx, ya - 58), (xx, ya - 22)], fill=M.scale_c(AMARILLO, kc), width=5)
                texto(img, fx, (xa + xb) / 2, ya - 100, lab, 54, AMARILLO, kc, f='mono', glow=0.4)
        pill(img, fx, 540, 1400, 'Y MUCHO MÁS LIGERA', eout(seg(u, Wp(6, 'ligera') - 0.2, Wp(6, 'ligera'))), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. para cargar el carro con tan poquito hule (flechas del peso sobre la galleta)
def s_hule(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 70, 12, tx=-0.6, ty=0.4, tz=0.4), K(0.3, 3.8, 40, 10, tx=-0.8, ty=0.4, tz=0.5),
                          K(5, 3.75, 36, 10, tx=-0.8, ty=0.4, tz=0.5)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    draw_objects(fr, carro_g(marca=1.0))

    def ui(img, fx):
        x, y, _ = fr.cam.p1(GAL_POS)
        for j, dx in enumerate((-90, 0, 90)):
            kk = seg(u, Wp(7, 'cargar') - 0.2 + 0.08 * j, Wp(7, 'cargar') + 0.1 + 0.08 * j)
            V.flecha(img, fx, x + dx, y - 470, x + dx, y - 250, ROJO, k=kk, w=12)
        texto(img, fx, x, y - 520, 'PESO DEL CARRO', 34, ROJO, seg(u, Wp(7, 'cargar') - 0.2, Wp(7, 'cargar')), f='mono', glow=0.4)
        pill(img, fx, x, y + 170, 'POQUITO HULE', eout(seg(u, Wp(7, 'hule') - 0.2, Wp(7, 'hule'))), size=28, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. va inflada a unas 60 libras: casi el doble que tus llantas («60 PSI» de cristal; dos manómetros)
def s_60(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.2, -40, 8, ty=0.8), K(0.3, 4.6, -20, 6, ty=0.8), K(5, 4.55, -16, 6, ty=0.8)], cy=0.42))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, '60 PSI', u, t0=Wp(8, 'sesenta') - 0.3, cy=0.25, entrada='golpe')
    ms, _ = galleta_m(giro=8 * math.sin(t))
    draw_objects(fr, ms)

    def ui(img, fx):
        k1 = seg(u, Wp(8, 'sesenta') - 0.1, Wp(8, 'sesenta') + 0.5)
        k2 = seg(u, Wp(8, 'doble') - 0.3, Wp(8, 'doble') + 0.3)
        manometro(img, fx, 280, 1230, 150, 60 * P.eout4(k1), k=seg(u, -0.1, 0.2), txt='GALLETA', col=AMARILLO)
        manometro(img, fx, 800, 1230, 150, 32 * P.eout4(k2), k=seg(u, Wp(8, 'doble') - 0.4, Wp(8, 'doble') - 0.1), txt='TU LLANTA*', col=WHITE)
        pill(img, fx, 540, 1420, '*EJEMPLO · LA DE TU CARRO VIENE EN LA PUERTA', seg(u, Wp(8, 'doble'), Wp(8, 'doble') + 0.3), size=20, border=GRIS, dot=False)
        texto(img, fx, 540, 1230, '≈ ×2', 52, AMARILLO, k2, f='mono', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. y como pisa menos piso (las huellas en el piso: la de la galleta es más chica)
def huella(fr, x, z, w, l, col, a=1.0):
    pts = [(x - l, 0.012, z - w), (x + l, 0.012, z - w), (x + l, 0.012, z + w), (x - l, 0.012, z + w), (x - l, 0.012, z - w)]
    line3(fr, pts, col=col, w=4, a=a, glow=0.8)
    for j in range(5):
        zz = z - w + 2 * w * (j + 0.5) / 5
        line3(fr, [(x - l, 0.012, zz), (x + l, 0.012, zz)], col=col, w=2, a=0.5 * a, glow=0.4)


def s_piso(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.6, 40, 50, ty=0.4), K(0.3, 4.8, 70, 62, ty=0.3), K(5, 4.75, 72, 62, ty=0.3)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.3)
    kl = 1 - P.eout4(seg(u, Wp(9, 'pisa') - 0.3, Wp(9, 'pisa') + 0.3))
    a, _ = llanta_n(z=0.75)
    b, _ = galleta_m(z=-0.75)
    ms = P.tfk(a, t=(0, 1.6 * (1 - kl) * 0 + 0.0, 0)) + b
    draw_objects(fr, P.tfk(ms, t=(0, 0, 0)), xray=0.75 * (1 - kl))
    ka = 1 - kl
    huella(fr, 0, 0.75, 0.27, 0.32, CYAN, a=ka)
    huella(fr, 0, -0.75, 0.135, 0.26, AMARILLO, a=ka)

    def ui(img, fx):
        pill(img, fx, 540, 1330, 'MENOS HULE EN EL PISO', eout(seg(u, Wp(9, 'piso') - 0.2, Wp(9, 'piso'))), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. con lluvia agarra menos y puede patinar (llueve, la galleta resbala y salpica)
def s_lluvia(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.2, -30, 10, ty=0.7), K(0.3, 3.6, -50, 8, ty=0.7), K(5, 3.55, -52, 8, ty=0.7)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    xs = 0.25 * math.sin(u * 5) * seg(u, Wp(10, 'patinar') - 0.3, Wp(10, 'patinar'))
    ms, _ = galleta_m(giro=math.degrees(GIRO(t, 0.3)), x=xs)
    draw_objects(fr, ms)
    rng = np.random.RandomState(4)
    for j in range(14):
        ph = (t * 2.5 + j / 14) % 1.0
        p = (xs - 0.3 - ph * 0.9 + rng.uniform(-0.1, 0.1), 0.05 + 0.5 * ph - 0.6 * ph * ph, rng.uniform(-0.3, 0.3))
        dot3(fr, p, r=4, col=AZULC, a=0.8 * (1 - ph), glow=0.8)

    def ui(img, fx):
        lluvia(img, t, k=seg(u, Wp(10, 'lluvia') - 0.3, Wp(10, 'lluvia')))
        pill(img, fx, 540, 1330, 'PUEDE PATINAR', eout(seg(u, Wp(10, 'patinar') - 0.2, Wp(10, 'patinar'))), size=34, border=AZULC, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. y aquí está el error (la galleta en rojo)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.4, 40, 16, ty=0.8), K(0.3, 4.6, 20, 12, ty=0.8), K(5, 4.55, 16, 12, ty=0.8)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    ms, _ = galleta_m(caliente=0.6)
    draw_objects(fr, ms)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 300, seg(u, 0.05, 0.2), size=92)
        texto(img, fx, 540, 1330, '⚠', 140, ROJO, seg(u, 0.2, 0.35), f='sansx', glow=0.8)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.35), amp=20)


# 12. traerla puesta semanas… (el calendario tacha días rapidísimo)
def s_semanas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.6, -30, 12, tx=-0.5, ty=0.4), K(0.3, 5.8, -50, 10, tx=-0.6, ty=0.4), K(5, 5.75, -52, 10, tx=-0.6, ty=0.4)], cy=0.78))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    draw_objects(fr, carro_g(giro=GIRO(t, 0.4), marca=1.0))
    kd = seg(u, 0.0, d - 0.2)

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        x0, y0, cw, ch = 150, 300, 112, 92
        ka = seg(u, -0.1, 0.15)
        dd.rounded_rectangle((x0 - 20, y0 - 90, x0 + 7 * cw + 20, y0 + 5 * ch + 20), radius=22, outline=M.scale_c(WHITE, 0.7 * ka), width=4)
        texto(img, fx, x0 + 3.5 * cw, y0 - 45, 'CON LA GALLETA', 34, AMARILLO, ka, f='mono', glow=0.3)
        n = int(35 * kd)
        for j in range(35):
            cx, cy = x0 + (j % 7) * cw + cw / 2, y0 + (j // 7) * ch + ch / 2
            dd.text((cx, cy), str(j + 1), font=M.font('mono', 30), fill=M.scale_c(GRIS, ka), anchor='mm')
            if j < n:
                tache(img, fx, cx, cy, 26, 1.0, w=6)
        texto(img, fx, 540, y0 + 5 * ch + 90, f'DÍA {max(1, n)}', 70, ROJO, seg(u, 0.1, 0.3), f='mono', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. o meterle 120 en la autopista («120» de cristal; la aguja se va al rojo)
def s_120(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.6, 50, 14, ty=0.4), K(0.3, 6.6, 70, 10, ty=0.4), K(5, 6.55, 72, 10, ty=0.4)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, '120', u, t0=Wp(13, 'ciento') - 0.3, cy=0.3, entrada='golpe')
    v = 60 + 60 * P.eout4(seg(u, Wp(13, 'ciento') - 0.3, Wp(13, 'veinte') + 0.2))
    carretera(fr, t, vel=v / 60)
    draw_objects(fr, carro_g(giro=GIRO(t, v / 60), marca=1.0))

    def ui(img, fx):
        V.tablero(img, fx, 540, 1250, 190, v, k=seg(u, -0.1, 0.15), rango=(80, 200, ROJO), rojo=seg(v, 80, 120))
        pill(img, fx, 540, 1500, 'AUTOPISTA', eout(seg(u, Wp(13, 'autopista') - 0.2, Wp(13, 'autopista'))), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.25 * seg(v, 100, 120), amp=10)


# 14. se calienta, se gasta rapidísimo (la galleta al rojo con ondas de calor y orillas gastadas)
def s_calienta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.2, -60, 10, ty=0.75), K(0.3, 4.6, -30, 8, ty=0.75), K(5, 4.55, -26, 8, ty=0.75)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    kc = seg(u, Wp(14, 'calienta') - 0.3, Wp(14, 'calienta') + 0.4)
    kg = seg(u, Wp(14, 'gasta') - 0.2, Wp(14, 'gasta') + 0.4)
    ms, _ = galleta_m(giro=math.degrees(GIRO(t, 1.5)), caliente=kc, hombros=kg)
    draw_objects(fr, ms)
    P.ondas_calor(fr, t, 0.0, 1.4, 2.4, 0.8, k=kc, col=NARANJA, n=5)

    def ui(img, fx):
        P.termometro(img, fx, 950, 520, 460, 0.25 + 0.7 * kc, 'CALOR', k=seg(u, -0.1, 0.2))
        pill(img, fx, 540, 1330, 'SE GASTA RAPIDÍSIMO', eout(seg(u, Wp(14, 'gasta') - 0.2, Wp(14, 'gasta'))), size=32, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. y puede tronar justo cuando más la necesitas (se infla, revienta y vuelan pedazos)
def s_truena(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, 20, 10, ty=0.75), K(0.3, 3.8, 0, 8, ty=0.75), K(5, 3.75, -4, 8, ty=0.75)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    ut = Wp(15, 'tronar') - 0.05
    if u < ut:
        ms, _ = galleta_m(caliente=1.0, bulto=seg(u, -0.2, ut))
        draw_objects(fr, ms)
    else:
        k = u - ut
        rng = np.random.RandomState(7)
        ms = [named(M3.cyl(LL.RT * 0.86 * 0.72, 0.18, (128, 132, 140), n=30, shadow=0, gloss=0.6, y0=-0.09).tf(rx=90, t=(0, 0.55, 0)), 'rin', rim=0.7)]
        for j in range(26):
            a = rng.uniform(0, 2 * math.pi)
            v = rng.uniform(1.5, 3.5)
            p = (math.cos(a) * (0.75 + v * k), 0.76 + math.sin(a) * (0.75 + v * k) - 2.5 * k * k, rng.uniform(-0.6, 0.6) * v * k)
            ms.append(named(M3.box(0.14, 0.09, 0.12, HULE, shadow=0, base=False).tf(rx=900 * k * rng.rand(), ry=700 * k, t=p), 'pedazo', rim=0.5))
        draw_objects(fr, ms)

    def ui(img, fx):
        kt = seg(u, ut, ut + 0.12)
        texto(img, fx, 540, 420, '¡PUM!', 150, WHITE, kt, f='sansx', glow=0.7)
        pill(img, fx, 540, 1330, 'JUSTO CUANDO MÁS LA NECESITAS', eout(seg(u, Wp(15, 'necesitas') - 0.2, Wp(15, 'necesitas'))), size=28, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=0.6 * golpe_k(u, ut, 0.15)), t, golpe_k(u, ut, 0.5), amp=30)


# 16. por dentro trae menos capas (corte: capas de tu llanta contra las de la galleta; entra con `cristal` CAPAS)
def capas(img, fx, x0, y0, w, n, cols, k, lab, col):
    dd = ImageDraw.Draw(img)
    h = 46
    for j in range(n):
        kk = seg(k, j / n * 0.7, j / n * 0.7 + 0.3)
        if kk <= 0:
            continue
        y = y0 - j * (h + 8)
        dd.rounded_rectangle((x0, y - h * kk, x0 + w, y), radius=10, fill=cols[j % len(cols)])
    texto(img, fx, x0 + w / 2, y0 + 60, lab, 32, col, seg(k, 0, 0.3), f='mono', glow=0.3)


def s_capas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.8, 30, 20, ty=0.8), K(0.3, 4.2, 10, 16, ty=0.8), K(5, 4.15, 6, 16, ty=0.8)], cy=0.42))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.4)
    a, _ = llanta_n(z=0.75, giro=10 * t)
    b, _ = galleta_m(z=-0.75, giro=10 * t)
    draw_objects(fr, a + b, xray=0.6)
    k = seg(u, Wp(16, 'capas') - 0.4, Wp(16, 'capas') + 0.5)

    def ui(img, fx):
        cols = [(60, 62, 70), (180, 182, 190), (120, 90, 60), (180, 182, 190), (70, 72, 80)]
        capas(img, fx, 150, 1350, 340, 5, cols, k, 'TU LLANTA', WHITE)
        capas(img, fx, 600, 1350, 340, 3, cols, k, 'GALLETA', AMARILLO)
        esquema(img, fx, k, y=1470)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. costados más delgados y un dibujo sencillo (la galleta de cerca con pastillas)
def s_costados(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.0, 100, 14, ty=0.8), K(0.3, 2.5, 60, 10, ty=0.8), K(5, 2.45, 56, 10, ty=0.8)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.5)
    ms, _ = galleta_m(giro=12 * t)
    draw_objects(fr, ms)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0, 0.3, 0.06))
        pill(img, fx, 540, 1330, 'COSTADO DELGADO', eout(seg(u, Wp(17, 'costados') - 0.2, Wp(17, 'costados'))), size=28, border=AMARILLO)
        x2, y2, _ = fr.cam.p1((0, 1.52, 0))
        pill(img, fx, x2 + 60, y2 - 120, 'DIBUJO SENCILLO', eout(seg(u, Wp(17, 'dibujo') - 0.2, Wp(17, 'dibujo'))), size=28, border=AMARILLO)
        doodle_circle(img, fx, x2, y2 + 40, 200, 70, t, k=seg(u, Wp(17, 'dibujo') - 0.1, Wp(17, 'dibujo') + 0.3), col=AMARILLO, seed=4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. y manejar lejos con ella castiga otras piezas del carro (rayos X: la transmisión brilla; odómetro corre)
def s_piezas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.4, 20, 26, ty=0.4), K(0.3, 5.6, -20, 22, ty=0.4), K(5, 5.55, -24, 22, ty=0.4)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    ms = carro_g(giro=GIRO(t, 0.6), marca=1.0)
    kp = seg(u, Wp(18, 'piezas') - 0.2, Wp(18, 'piezas') + 0.3)
    ms += P.tfk(engrane(n=12, r=0.18, giro=-t * 200, calor=kp), t=(0.6, 0.4, 0.0))
    _B(ms, 0.2, 0.22, 0.3, M.mixc((90, 92, 100), (255, 90, 40), kp), -1.0, 0.33, 0.06, name='diferencial', gloss=0.6,
       glow=M.scale_c((255, 80, 30), 0.6 * kp) if kp > 0.05 else None)
    draw_objects(fr, ms, xray=0.85, keep=('engrane', 'diente', 'diferencial', 'llanta'))

    def ui(img, fx):
        km = 40 + 260 * seg(u, 0.0, d)
        texto(img, fx, 540, 330, f'{km:06.0f} KM', 70, AMARILLO, seg(u, -0.1, 0.2), f='mono', glow=0.4)
        x, y, _ = fr.cam.p1((-1.0, 0.33, 0.06))
        pill(img, fx, x, y + 150, 'DIFERENCIAL', eout(kp), size=26, border=ROJO)
        x2, y2, _ = fr.cam.p1((0.6, 0.4, 0.0))
        pill(img, fx, x2, y2 - 160, 'TRANSMISIÓN', eout(seg(u, Wp(18, 'piezas'), Wp(18, 'piezas') + 0.3)), size=26, border=ROJO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. hasta la transmisión (la cámara entra: engranes que se calientan)
def s_transmision(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.4, 20, 10, ty=0.0), K(0.3, 2.8, -8, 8, ty=0.0), K(5, 2.75, -12, 8, ty=0.0)], cy=0.52))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    kc = seg(u, Wp(19, 'transmision') - 0.3, Wp(19, 'transmision') + 0.4)
    g = -t * 120
    draw_objects(fr, engrane(n=16, r=0.62, giro=g, calor=kc, x=-0.45, y=0.2) + engrane(n=10, r=0.4, giro=-g * 1.6 + 18, calor=kc, x=0.62, y=-0.35))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Transmisión', 'serif')], 330, seg(u, Wp(19, 'transmision'), Wp(19, 'transmision') + 0.15), size=96, col=NARANJA)
        pill(img, fx, 540, 1400, 'AAA: PUEDE DAÑAR OTRAS PIEZAS', seg(u, 0.3, 0.6), size=22, border=GRIS, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wp(19, 'transmision') + 0.15, 0.3), amp=14)


# 20. la otra trampa: pasa años olvidada en la cajuela… (la cajuela se abre; polvo)
def s_cajuela(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.2, -150, 26, tx=-0.9, ty=0.6), K(0.3, 4.4, -120, 34, tx=-1.0, ty=0.6), K(5, 4.35, -118, 34, tx=-1.0, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    kc = P.resorte(seg(u, Wp(20, 'trampa') - 0.2, Wp(20, 'trampa') + 0.3))
    ms = carro_g(galleta=False, cajuela=kc)
    g, _ = galleta_m(s=0.42)
    ms += P.tfk(g, rx=90, t=(-1.0, 0.62, 0.0))
    draw_objects(fr, ms)
    rng = np.random.RandomState(9)
    for j in range(22):
        ph = (t * 0.25 + j / 22) % 1.0
        dot3(fr, (-1.0 + rng.uniform(-0.6, 0.6), 0.7 + ph * 0.8, rng.uniform(-0.5, 0.5)), r=2.5, col=(200, 190, 170), a=0.7 * (1 - ph) * kc, glow=0.8)

    def ui(img, fx):
        pill(img, fx, 540, 1330, 'AÑOS SIN REVISAR', eout(seg(u, Wp(20, 'anos') - 0.2, Wp(20, 'anos'))), size=32, border=AMARILLO, dot=False)
        kicker(img, 'LA OTRA TRAMPA', 300, seg(u, 0.0, 0.3), col=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. y pierde aire («AIRE» de cristal; la aguja baja y la galleta se aplasta)
def s_aire(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.2, 40, 10, ty=0.7), K(0.3, 3.6, 20, 8, ty=0.7), K(5, 3.55, 16, 8, ty=0.7)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'AIRE', u, t0=Wp(21, 'aire') - 0.3, cy=0.28, entrada='sube')
    ka = seg(u, Wp(21, 'pierde') - 0.2, d)
    ms, _ = galleta_m(sag=0.9 * ka)
    draw_objects(fr, ms)

    def ui(img, fx):
        manometro(img, fx, 830, 1150, 140, 60 - 32 * P.eout4(ka), k=seg(u, -0.1, 0.2), txt='GALLETA', col=AMARILLO)
        x, y, _ = fr.cam.p1((0.3, 1.0, 0.1))
        for j in range(5):
            ph = (t * 1.5 + j / 5) % 1.0
            texto(img, fx, x + 60 + ph * 160, y - ph * 90, '~', 50, M.scale_c(AZULC, (1 - ph) * ka), 1.0, f='mono', glow=0.3)
    fr.ui.append(ui)
    return finish(fr, fi)


# 22. revísale el aire cuando revises las otras (las 5 llantas con su palomita)
def s_revisa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 10.5, 30, 20, ty=0.6), K(0.3, 9.6, 10, 16, ty=0.6), K(5, 9.55, 6, 16, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    ms = []
    xs = (-2.6, -1.3, 0.0, 1.3, 2.6)
    for j, x in enumerate(xs):
        e = P.entrada(u, -0.2 + 0.06 * j, 0.25, 'cae')
        if j < 4:
            a, _ = llanta_n(x=x, s=0.62)
        else:
            a, _ = galleta_m(x=x, s=0.54)
        ms += P.tfk(a, t=(0, -e['dy'] * 0.4, 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        for j, x in enumerate(xs):
            xx, yy, _ = fr.cam.p1((x, 1.4, 0))
            kk = seg(u, Wp(22, 'revisale') + 0.15 * j, Wp(22, 'revisale') + 0.15 * j + 0.2)
            texto(img, fx, xx, yy - 40, '✓', 90, VERDE, kk, f='sansx', glow=0.6)
        x4, y4, _ = fr.cam.p1((2.6, 0.0, 0))
        pill(img, fx, min(x4, 900), y4 + 70, 'LA GALLETA TAMBIÉN', eout(seg(u, Wp(22, 'otras') - 0.2, Wp(22, 'otras'))), size=24, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. mándaselo a quien trae la galleta puesta desde hace un mes
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.2, 40, 16, tx=-0.3, ty=0.5), K(0.3, 6.4, 60, 12, tx=-0.4, ty=0.5), K(5, 6.35, 62, 12, tx=-0.4, ty=0.5)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    draw_objects(fr, carro_g(marca=1.0))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien trae', 'sans'), ('la galleta desde hace un mes.', 'serif')], 250, seg(u, 0.05, 0.2), size=56)
        x, y, _ = fr.cam.p1(GAL_POS)
        doodle_circle(img, fx, x, y, 110, 110, t, k=seg(u, 0.3, 0.6), col=AMARILLO, seed=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.6),
                sfx=[(-2.4 + 0.12 * j, 'tick', 0.45) for j in range(19)] + [(UC, 'sub', 1.0), (UC, 'bass', 0.9)]),
           dict(desde=1, fn=s_80, tr='golpe', c=(0.5, 0.35), sfx=[(0.0, 'riser', 0.3)]),
           dict(desde=2, fn=s_kmh, tr='zoom', c=(0.5, 0.33), sfx=[(0.12, 'bass', 0.8)]),
           dict(desde=3, fn=s_quedarse, tr='deslizar', sfx=[]),
           dict(desde=4, fn=s_llantera, tr='mosaico', sfx=[]),
           dict(desde=5, fn=s_junto, tr='cubo', sfx=[(0.05, 'thud', 0.8), (0.18, 'thud', 0.7)]),
           dict(desde=6, fn=s_mitad, tr='giro', sfx=[]),
           dict(desde=7, fn=s_hule, tr='push', c=(0.5, 0.6), sfx=[]),
           dict(desde=8, fn=s_60, tr='iris', c=(0.5, 0.6), sfx=[]),
           dict(desde=9, fn=s_piso, tr='wipe', sfx=[]),
           dict(desde=10, fn=s_lluvia, tr='remolino', sfx=[(0.0, 'whoosh_suave', 0.5)]),
           dict(desde=11, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.15, 'sub', 0.9), (0.2, 'bass', 0.7)]),
           dict(desde=12, fn=s_semanas, tr='rebanadas', sfx=[]),
           dict(desde=13, fn=s_120, tr='whip', sfx=[]),
           dict(desde=14, fn=s_calienta, tr='flash', sfx=[]),
           dict(desde=15, fn=s_truena, tr='golpe', sfx=[]),
           dict(desde=16, fn=s_capas, tr='cristal', palabra='CAPAS', sfx=[]),
           dict(desde=17, fn=s_costados, tr='cubo_izq', sfx=[]),
           dict(desde=18, fn=s_piezas, tr='deslizar_abajo', sfx=[]),
           dict(desde=19, fn=s_transmision, tr='zoom', c=(0.55, 0.6), sfx=[]),
           dict(desde=20, fn=s_cajuela, tr='whip_izq', sfx=[]),
           dict(desde=21, fn=s_aire, tr='deslizar', sfx=[]),
           dict(desde=22, fn=s_revisa, tr='giro', sfx=[]),
           dict(desde=23, fn=s_compa, tr='mosaico', sfx=[(0.05, 'slap', 0.7)]),
           dict(desde=24, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    add = {1: [(Wp(1, 'rapido') - 0.2, 'tick', 0.5)],
           3: [(Wp(3, 'quedarse'), 'slap', 0.9), (Wp(3, 'quedarse') + 0.02, 'bass', 0.6)],
           4: [(Wp(4, 'llantera') - 0.3, 'cristal', 0.6), (Wp(4, 'llantera'), 'chime_a', 0.4)],
           5: [(Wp(5, 'llanta') - 0.2, 'tick', 0.5)],
           6: [(Wp(6, 'mitad') - 0.3, 'cristal', 0.6), (Wp(6, 'ancha') - 0.2, 'scribble', 0.4), (Wp(6, 'ligera') - 0.2, 'tick2', 0.5)],
           7: [(Wp(7, 'cargar') - 0.2, 'thud', 0.8), (Wp(7, 'hule') - 0.2, 'tick', 0.5)],
           8: [(Wp(8, 'sesenta') - 0.3, 'cristal', 0.6), (Wp(8, 'sesenta'), 'chime_b', 0.4), (Wp(8, 'doble') - 0.2, 'chime_c', 0.4)],
           9: [(Wp(9, 'pisa') - 0.3, 'whoosh_suave', 0.4), (Wp(9, 'piso') - 0.2, 'tick', 0.5)],
           10: [(Wp(10, 'lluvia') - 0.3, 'whoosh_suave', 0.4), (Wp(10, 'patinar') - 0.2, 'whoosh', 0.5)],
           12: [(0.1 + 0.07 * j, 'tick', 0.3) for j in range(20)],
           13: [(Wp(13, 'ciento') - 0.3, 'cristal', 0.6), (Wp(13, 'ciento') - 0.3, 'riser', 0.4), (Wp(13, 'veinte'), 'bass', 0.7)],
           14: [(Wp(14, 'calienta') - 0.3, 'burst', 0.4), (Wp(14, 'gasta') - 0.2, 'scribble', 0.4)],
           15: [(Wp(15, 'tronar') - 0.05, 'burst', 1.0), (Wp(15, 'tronar') - 0.05, 'sub', 1.0), (Wp(15, 'tronar'), 'bass', 0.9)],
           16: [(Wp(16, 'capas') - 0.3, 'chime_a', 0.4)],
           17: [(Wp(17, 'costados') - 0.2, 'tick', 0.5), (Wp(17, 'dibujo') - 0.1, 'scribble', 0.5)],
           18: [(Wp(18, 'piezas') - 0.2, 'burst', 0.4), (0.1, 'digital', 0.3)],
           19: [(Wp(19, 'transmision'), 'bass', 0.7)],
           20: [(Wp(20, 'trampa') - 0.2, 'thud', 0.7), (Wp(20, 'anos') - 0.2, 'tick2', 0.5)],
           21: [(Wp(21, 'aire') - 0.3, 'cristal', 0.6), (Wp(21, 'pierde') - 0.2, 'whoosh_suave', 0.5)],
           22: [(Wp(22, 'revisale') + 0.15 * j, 'chime_b', 0.3) for j in range(5)]}
    for e in ESCENAS:
        if e.get('desde') in add and not e.get('loop'):
            e['sfx'] = list(e.get('sfx', [])) + add[e['desde']]


_sfx_dinamicos()


def tiempos_falsos():
    T = [(round(0.25 + 2.6 * i, 2), round(0.25 + 2.6 * i + 2.2, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.55, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    print('ok', T[-1])


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    else:
        montaje.cli(globals())
