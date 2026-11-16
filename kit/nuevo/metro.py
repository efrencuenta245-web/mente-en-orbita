"""Reel diario mié 18-nov-2026 18:00 — «Tu metro anda… en llantas.» (Metro de la Ciudad de México por dentro: 10 de 12
líneas sobre neumáticos, tecnología de París, la rueda de acero escondida dentro de cada llanta, las ruedas guía y la
barra de 750 V; error: detener las puertas; la lluvia en los tramos elevados).
Comunidad: chilangos que se suben diario al metro. Inicio tipo 4 (barra de búsqueda): el cursor escribe
«¿por qué el metro tiene llantas?» delante de «LLANTAS» de cristal, Enter y la cámara atraviesa la pantalla hasta las
llantas del vagón naranja. El final («porque su metro anda… en llantas») regresa a la barra (loop).
Voz Isaac (eleven_v4) del 16-nov, 66.7 s. Datos y fuentes: guiones/2026-11-18_metro.txt.
Fotos reales: tren MP-68 (Gobierno de la Ciudad de México, CC BY 4.0) y tren NM-16 (Gobierno de la CDMX, CC BY 4.0),
recortadas sin personas, sin anuncios y sin logotipos.
El vagón, el carretón (bogie), las llantas y el mapa de líneas son esquemas marcados «ESQUEMA».
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
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'metro'
TXT = ['Tu metro anda… en llantas.',
       '10 de sus 12 líneas ruedan sobre neumáticos;',
       'solo la Línea A y la 12 van en acero.',
       'La idea vino de París: los primeros trenes llegaron de Francia en 1969.',
       'Mira la prueba: rueda de acero contra llanta de hule.',
       'El hule hace menos ruido y aguanta mejor las subidas.',
       'Ahora mira debajo de un vagón: cada eje lleva dos llantas.',
       'Y por dentro de cada llanta, escondida, hay una rueda de acero.',
       'Pero aquí está el error que nos retrasa a todos: detener las puertas.',
       'Si una puerta no cierra, el tren no sale…',
       'y los que vienen atrás se amontonan.',
       '¿Y la rueda escondida? Si una llanta se poncha,',
       'esa rueda de acero carga el peso del vagón.',
       'A los lados, unas llantitas guía tocan una barra que lleva 750 voltios.',
       'Su punto débil es la lluvia: con vías y llantas mojadas,',
       'en los tramos elevados baja de 70 a 35 km/h.',
       'Y así mueve más de 1 200 millones de viajes al año.',
       'Mándaselo a quien se sube diario al metro,',
       'porque su metro anda… en llantas.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-18_metro_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_metro.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-18_metro_words.json')
FOTOS = os.path.join(HERE, 'img', 'metro')

AMARILLO = (255, 236, 160)
NARANJA = (240, 110, 28)
AZULC = (150, 210, 230)
ACERO = (176, 180, 190)
HULE = (26, 26, 30)
GRIS = (150, 150, 160)
CONCRETO = (120, 118, 112)
VERDE = (120, 240, 160)
LINEAS = [('1', (232, 70, 138)), ('2', (0, 110, 200)), ('3', (175, 165, 40)), ('4', (110, 190, 200)), ('5', (255, 210, 0)),
          ('6', (210, 40, 45)), ('7', (240, 120, 30)), ('8', (0, 160, 95)), ('9', (130, 70, 35)), ('A', (140, 50, 150)),
          ('B', (160, 175, 165)), ('12', (195, 155, 70))]


# ------------------------------------------------------------------ tiempos por palabra
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


def Wp(i, palabra, n=0):
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ utilidades
def K(u, dist, yaw, pitch, tx=0.0, ty=0.8, tz=0.0, roll=0.0):
    return (u, dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll))


def camara(u, claves, cy=0.56):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


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


def esquema(img, fx, k=1.0, y=1440, txt='ESQUEMA'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


def tubo(p0, p1, r=0.03, col=ACERO, n=8, name='tubo', gloss=0.8):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = M.norm(p1 - p0)
    a = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    e1 = M.norm(np.cross(d, a))
    e2 = np.cross(d, e1)
    V, F = [], []
    for p in (p0, p1):
        for j in range(n):
            q = 2 * math.pi * j / n
            V.append(p + r * (math.cos(q) * e1 + math.sin(q) * e2))
    for j in range(n):
        F.append((j, (j + 1) % n, n + (j + 1) % n, n + j))
    return named(M3.Mesh(V, F, col, shadow=0, gloss=gloss, double=True), name, rim=0.8, gloss=gloss)


def _B(ms, sx, sy, sz, col, x, y, z, name='cuerpo', gloss=0.45, rim=0.6, glow=None, base=True):
    m = named(M3.box(sx, sy, sz, col, shadow=0, gloss=gloss, base=base).tf(t=(x, y, z)), name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    ms.append(m)
    return m


# ------------------------------------------------------------------ fotos reales (Wikimedia Commons, CC BY 4.0)
_F = {}


def foto(n):
    if n in _F:
        return _F[n]
    if n == 'mp68':
        im = Image.open(os.path.join(FOTOS, 'metro_i_mp68a.jpg')).convert('RGB').crop((250, 48, 546, 367))
    else:
        im = Image.open(os.path.join(FOTOS, 'metro_i_nm16a.jpg')).convert('RGB').crop((180, 150, 740, 640))
    _F[n] = im
    return im


# ------------------------------------------------------------------ la llanta del metro (eje z) con su rueda de acero
RC, TA, TB = 0.36, 0.15, 0.17
ROUT = RC + TA
R_ACERO = 0.43
Y_RIEL = 0.06


def llanta(defl=0.0, giro=0.0, x=0.0, z=0.0, nu=40, nv=12):
    """Llanta de hule (neumático portador). defl 0–1 desinflada; si se desinfla, la rueda de acero baja al riel."""
    dlt = 0.012 + 0.2 * defl
    yc = max(ROUT - dlt, R_ACERO + Y_RIEL)
    V, F, C = [], [], []
    for i in range(nu):
        th = 2 * math.pi * i / nu + giro
        for j in range(nv):
            ph = 2 * math.pi * j / nv
            cp, sp = math.cos(ph), math.sin(ph)
            cp2 = math.copysign(abs(cp) ** 0.55, cp)
            sp2 = math.copysign(abs(sp) ** 0.7, sp)
            r = RC + TA * cp2
            px, py, pz = r * math.cos(th), r * math.sin(th), TB * sp2
            y = max(0.0, py + yc)
            low = clamp((0.3 - y) / 0.3)
            pz *= 1 + 0.5 * defl * low
            V.append((px + x, y, pz + z))
    for i in range(nu):
        for j in range(nv):
            a, b = i * nv + j, ((i + 1) % nu) * nv + j
            c, d = ((i + 1) % nu) * nv + (j + 1) % nv, i * nv + (j + 1) % nv
            F.append((a, b, c, d))
            ph = 2 * math.pi * (j + 0.5) / nv
            C.append(((40, 40, 44) if (i + j // 2) % 2 else (20, 20, 22)) if math.cos(ph) > 0.45 else HULE)
    m = named(M3.Mesh(V, F, C, shadow=0, gloss=0.15, double=True), 'llanta', rim=0.45, gloss=0.15)
    rin = named(M3.cyl(0.22, 0.3, (108, 110, 118), n=22, shadow=0, gloss=0.85).tf(rx=90, t=(x, yc, z - 0.15)), 'rin', rim=0.8)
    return [m, rin], yc


def acero(x=0.0, z=0.0, yc=ROUT, giro=0.0, glow=0.0):
    """Rueda de seguridad de acero (con pestaña), por dentro de la llanta, en el mismo eje."""
    ms = [named(M3.cyl(R_ACERO, 0.09, ACERO, n=30, shadow=0, gloss=0.95).tf(rx=90, t=(x, yc, z - 0.045)), 'acero', rim=0.95,
                gloss=0.95),
          named(M3.cyl(R_ACERO + 0.04, 0.025, (150, 154, 162), n=30, shadow=0, gloss=0.9).tf(rx=90, t=(x, yc, z - 0.07)), 'acero',
                rim=0.9)]
    for j in range(4):
        a = giro + j * math.pi / 2
        ms.append(named(M3.box(0.06, 0.06, 0.1, (110, 114, 122), shadow=0, base=False, gloss=0.8).tf(
            t=(x + 0.28 * math.cos(a), yc + 0.28 * math.sin(a), z + 0.02)), 'acero', rim=0.8))
    if glow > 0.01:
        for m in ms:
            m.glow = M.scale_c(CYAN, 0.5 * glow)
    return ms


ZT, ZA, ZG = 0.8, 0.56, 1.2          # z de la llanta, de la rueda de acero y de la rueda guía


def juego(x=0.0, defl=(0.0, 0.0), giro=0.0, acero_glow=0.0, guia=True, gsp=0.0):
    """Un eje: 2 llantas, 2 ruedas de acero por dentro, el eje y (opcional) las ruedas guía horizontales."""
    ms = []
    yc0 = ROUT
    for s, df in zip((-1, 1), defl):
        ll, yc = llanta(df, giro, x=x, z=s * ZT)
        ms += ll
        ms += acero(x=x, z=s * ZA, yc=yc, giro=giro, glow=acero_glow)
        yc0 = min(yc0, yc)
    ms.append(tubo((x, yc0, -ZT), (x, yc0, ZT), r=0.06, col=(90, 94, 102), name='eje'))
    if guia:
        for s in (-1, 1):
            ms.append(named(M3.cyl(0.15, 0.1, HULE, n=18, shadow=0, gloss=0.2).tf(t=(x, 0.36, s * ZG)), 'guia', rim=0.5))
            ms.append(named(M3.cyl(0.07, 0.11, (150, 152, 160), n=12, shadow=0, gloss=0.8).tf(t=(x, 0.36, s * ZG)), 'guia', rim=0.7))
            ms.append(tubo((x, 0.41, s * ZG), (x, 0.7, s * (ZT + 0.05)), r=0.03, col=(90, 94, 102), name='soporte'))
    return ms


def carreton(x=0.0, giro=0.0, defl=0.0, acero_glow=0.0):
    """Carretón (bogie): 2 ejes y su bastidor."""
    ms = juego(x - 0.75, (0.0, 0.0), giro, acero_glow) + juego(x + 0.75, (defl, 0.0), giro, acero_glow)
    _B(ms, 2.2, 0.16, 1.3, (60, 64, 72), x, 0.72, 0, name='bastidor', gloss=0.5)
    return ms


def via(fr, x0=-8, x1=8, a=1.0, mov=0.0, barra_glow=0.0, t=0.0):
    """La vía: dos pistas de rodamiento (para el hule), dos rieles (para el acero) y dos barras guía (750 V)."""
    ms = []
    L = x1 - x0
    for s in (-1, 1):
        _B(ms, L, 0.06, 0.34, CONCRETO, (x0 + x1) / 2, -0.06, s * ZT, name='pista', gloss=0.2)
        _B(ms, L, Y_RIEL + 0.06, 0.07, (150, 152, 160), (x0 + x1) / 2, -0.06, s * ZA, name='riel', gloss=0.9)
        _B(ms, L, 0.18, 0.06, (120, 124, 134), (x0 + x1) / 2, 0.27, s * (ZG + 0.2), name='barra', gloss=0.8,
           glow=M.scale_c(AMARILLO, barra_glow) if barra_glow > 0.01 else None)
    for j in range(int(L / 0.6) + 1):                                         # durmientes en línea
        xx = x0 + ((j * 0.6 - mov) % L)
        line3(fr, [(xx, -0.07, -1.5), (xx, -0.07, 1.5)], col=WHITE, w=1.6, a=0.35 * a, glow=0.2)
    return ms


def vagon(x=0.0, xray=0.0, puertas=0.0, giro=0.0, defl=0.0, s=1.0, acero_glow=0.0):
    """Vagón naranja del metro (sin logos). Los carretones a escala 0.55. puertas: 0 abiertas, 1 cerradas."""
    ms = []
    ms.append(named(M3.rbox(6.0, 1.45, 2.3, 0.3, NARANJA, n=5, shadow=0, gloss=0.85).tf(t=(0, 1.05, 0)), 'cuerpo', rim=0.8, gloss=0.85))
    ms.append(named(M3.rbox(5.8, 0.14, 2.1, 0.3, (180, 182, 188), n=5, shadow=0, gloss=0.6).tf(t=(0, 2.5, 0)), 'cuerpo', rim=0.7))
    _B(ms, 5.6, 0.25, 2.0, (30, 30, 34), 0, 0.8, 0, name='bajo', gloss=0.3)
    for s in (-1, 1):
        for xw in (-2.25, -0.75, 0.75, 2.25):                                # ventanas
            _B(ms, 0.9, 0.55, 0.02, (28, 32, 40), xw, 1.65, s * 1.16, name='cuerpo', gloss=0.95, rim=0.9)
        for xd in (-1.5, 0.0, 1.5):                                           # puertas que se cierran
            g = 0.38 * (1 - clamp(puertas))
            for hh in (-1, 1):
                _B(ms, 0.36, 1.2, 0.03, (190, 192, 198), xd + hh * (0.18 + g / 2), 1.12, s * 1.17, name='puerta', gloss=0.8)
            if puertas < 0.99:
                _B(ms, g, 1.2, 0.01, (8, 8, 10), xd, 1.12, s * 1.165, name='hueco', gloss=0.1)
    for xc in (-2.2, 2.2):
        ms += P.tfk(carreton(0, giro, defl if xc > 0 else 0.0, acero_glow), s=0.55, t=(xc, 0.0, 0))
    out = P.tfk(ms, s=s, t=(x, 0, 0)) if (s != 1.0 or x) else ms
    return out


# ================================================================== escenas
# 0. gancho (inicio 4: barra de búsqueda). En el pre-roll (el loop del final) el cursor escribe la pregunta delante de
#    «LLANTAS» de cristal; en el primer cuadro ya está escrita. Enter en u=0 y la cámara atraviesa la pantalla.
PREG = '¿por qué el metro tiene llantas?'
U_ENTER = 0.0


def _barra(t, fi, u):
    fr = Frame(Cam(target=(0, 1.0, 0), dist=7.0, yaw=8 * math.sin(t * 0.3), pitch=4, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'LLANTAS', u, t0=-4.0, cy=0.62, entrada='golpe')
    n = int(len(PREG) * seg(u, -3.5, -1.2))

    def ui(img, fx):
        k = P.resorte(seg(u, -3.9, -3.6))
        if k <= 0.01:
            return
        w, h = int(900 * max(0.05, k)), 120
        x0, y0 = 540 - w // 2, 760
        dl = ImageDraw.Draw(img)
        bright = 1.0 + 0.6 * seg(u, U_ENTER - 0.12, U_ENTER) * (1 - seg(u, U_ENTER, U_ENTER + 0.2))
        dl.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=60, fill=(20, 22, 28), outline=M.scale_c(WHITE, min(1, 0.8 * bright)), width=4)
        ImageDraw.Draw(fx).rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=60, outline=M.scale_c(CYAN, 0.35 * bright), width=8)
        if k > 0.9:
            dl.ellipse((x0 + 40, y0 + 36, x0 + 80, y0 + 76), outline=(200, 200, 205), width=5)
            dl.line([(x0 + 76, y0 + 72), (x0 + 92, y0 + 88)], fill=(200, 200, 205), width=6)
            txt = PREG[:n]
            f = M.font('sanss', 44)
            dl.text((x0 + 120, y0 + h / 2), txt, font=f, fill=(235, 236, 240), anchor='lm')
            if (int(t * 2.5) % 2 == 0) or n < len(PREG):
                cx = x0 + 120 + dl.textlength(txt, font=f) + 6
                dl.line([(cx, y0 + 34), (cx, y0 + h - 34)], fill=CYAN, width=4)
            kicker(img, 'BUSCAR', y0 - 40, 1.0, col=GRIS)
        if u > U_ENTER - 0.15:
            pill(img, fx, 540, y0 + h + 80, 'ENTER ⏎', seg(u, U_ENTER - 0.15, U_ENTER), size=24, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def _llantas(t, fi, u):
    ull = Wp(0, 'llantas') - 0.1
    fr = Frame(camara(u, [K(0.0, 5.0, 24, 4, ty=0.9, tx=1.8), K(0.6, 6.4, 18, 5, ty=1.1, tx=1.4),
                          K(ull, 5.2, 34, 3, ty=0.8, tx=1.9), K(3.0, 5.0, 38, 3, ty=0.8, tx=1.9)], cy=0.68))
    space(fr, t, floor=None, bokeh=0.9, beam=0.3)
    M.cristal(fr.base, fr.fx, 'LLANTAS', u, t0=-4.0, cy=0.62, entrada='golpe')
    e = P.entrada(u, 0.0, 0.3, 'desliza')
    xv = 1.2 * e['dy']
    mov = (t * 3.0) * (1 - seg(u, 0.0, 0.3))
    ms = via(fr, -6, 8, mov=mov)
    ms += vagon(x=xv, giro=-t * 4 * (1 - seg(u, 0.0, 0.3)))
    draw_objects(fr, ms)
    pl = fr.cam.p1((2.2 + 0.41, 0.3, 1.25))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Tu metro anda…', 'sans'), ('en llantas.', 'serif')], 190, seg(u, ull, ull + 0.15), size=78)
        kicker(img, 'METRO · CIUDAD DE MÉXICO', 140, seg(u, 0.3, 0.6), col=AZULC)
        if u > ull:
            doodle_circle(img, fx, pl[0], pl[1], 120, 120, t, k=seg(u, ull + 0.1, ull + 0.4), col=AMARILLO, seed=3)
        esquema(img, fx, seg(u, 0.5, 0.8), y=1460)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.3, 0.3), golpe_k(u, ull + 0.15, 0.3)), amp=22)


def s_gancho(t, fi, u, d):
    if u < U_ENTER:
        return _barra(t, fi, u)
    if u < U_ENTER + 0.3:
        return M.tr_zoom_through(_barra(t, fi, u), _llantas(t, fi, u), seg(u, U_ENTER, U_ENTER + 0.3), 0.5, 0.42)
    return _llantas(t, fi, u)


# 1. 10 de sus 12 líneas ruedan sobre neumáticos (mapa esquemático: se prenden 10 con su llanta)
def _mapa(img, fx, u, t, k_on, k_acero, n_on):
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    for j, (nom, col) in enumerate(LINEAS):
        ke = P.resorte(seg(u, -0.25 + 0.03 * j, 0.0 + 0.03 * j))
        if ke <= 0.01:
            continue
        cx = 230 + (j % 3) * 310
        cy = 470 + (j // 3) * 180
        es_acero = nom in ('A', '12')
        on = (not es_acero and j < n_on) or (es_acero and k_acero > 0)
        cc = col if (on or k_on <= 0) else M.scale_c(col, 0.35)
        r = int(64 * max(0.05, ke))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=cc, width=8)
        texto(img, fx, cx, cy, nom, int(56 * max(0.1, ke)), cc, 1.0, glow=0.3 if on else 0.0)
        if on and not es_acero and k_on > 0:                                  # llantita negra con brillo
            d.ellipse((cx + 50, cy + 30, cx + 96, cy + 76), fill=(30, 30, 34), outline=(220, 220, 226), width=3)
            df.ellipse((cx + 44, cy + 24, cx + 102, cy + 82), outline=M.scale_c(col, 0.5), width=6)
        if es_acero and k_acero > 0:
            d.ellipse((cx + 50, cy + 30, cx + 96, cy + 76), fill=ACERO, outline=WHITE, width=3)
            df.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=M.scale_c(ACERO, 0.7 * k_acero), width=10)


def s_neumaticos(t, fi, u, d):
    un = Wp(1, 'neumaticos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.0, 0, 50, ty=0.0), K(d, 6.8, 6, 48, ty=0.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '10 DE 12', u, t0=un, cy=0.665, entrada='zoom')
    n_on = int(12 * seg(u, un - 0.4, un + 0.3))

    def ui(img, fx):
        kicker(img, 'LAS 12 LÍNEAS DEL METRO · ESQUEMA', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 285, 'sobre neumáticos', 70, WHITE, eout(seg(u, un, un + 0.25)), f='serif', glow=0.3)
        _mapa(img, fx, u, t, 1.0, 0.0, n_on)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.3, 0.3), amp=14)


# 2. solo la Línea A y la 12 van en acero (se prenden de gris acero y aparece la rueda de acero girando)
def s_acero(t, fi, u, d):
    ua = Wp(2, 'linea') - 0.1
    u12 = Wp(2, 'doce') - 0.1
    uac = Wp(2, 'acero') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, 50, 10, ty=0.5), K(0.5, 3.0, 20, 8, ty=0.5), K(d, 2.9, 14, 8, ty=0.5)], cy=0.78))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    ms = []
    _B(ms, 3.0, Y_RIEL + 0.06, 0.08, (150, 152, 160), 0, -0.06, 0, name='riel', gloss=0.9)
    yc = R_ACERO + Y_RIEL
    ms += P.tfk(acero(x=0, z=0, yc=yc, giro=-t * 3, glow=seg(u, uac, uac + 0.3)), t=(0, 0, 0.04))
    draw_objects(fr, ms)
    if u > uac:
        for j in range(8):
            ph = (t * 4 + j / 8) % 1.0
            dot3(fr, (-0.1 - 0.6 * ph, Y_RIEL + 0.02 + 0.25 * ph * (1 - ph) * 4 * ((j % 3) / 3 + 0.3), 0.05 * (j - 4)),
                 r=4, col=(255, 210, 140), a=(1 - ph) * seg(u, uac, uac + 0.2), glow=2.0)

    def ui(img, fx):
        kicker(img, 'RODADURA FÉRREA', 150, seg(u, -0.1, 0.2), col=AZULC)
        ka = eout(seg(u, ua, ua + 0.25))
        k12 = eout(seg(u, u12, u12 + 0.25))
        for kk, (nom, col), x in ((ka, LINEAS[9], 330), (k12, LINEAS[11], 750)):
            if kk <= 0.01:
                continue
            r = int(80 * P.resorte(kk))
            ImageDraw.Draw(img).ellipse((x - r, 360 - r, x + r, 360 + r), outline=col, width=10)
            texto(img, fx, x, 360, nom, int(76 * kk), col, 1.0, glow=0.5)
            pill(img, fx, x, 490, 'LÍNEA ' + nom, kk, size=26, border=col, dot=False)
        texto(img, fx, 540, 640, 'van en acero', 74, ACERO, eout(seg(u, uac, uac + 0.25)), f='serif', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uac, 0.3), amp=14)


# 3. la idea vino de París; los primeros trenes llegaron de Francia en 1969 (globo de alambre → foto real + 1969)
def _gp(lat, lon, spin, C, R):
    la, lo = math.radians(lat), math.radians(lon) + spin
    return C + R * np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)])


def s_paris(t, fi, u, d):
    upa = Wp(3, 'paris') - 0.1
    ufr = Wp(3, 'llegaron') - 0.1
    u69 = Wp(3, 'mil') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.4, 0, 8, ty=1.25), K(0.5, 5.2, 0, 10, ty=1.25), K(ufr, 5.6, 0, 8, ty=1.6),
                          K(d, 5.5, 0, 8, ty=1.6)], cy=0.42))
    space(fr, t, floor=None, bokeh=1.0)
    C, R = np.array([0, 1.25, 0]), 1.45
    spin = math.radians(-20) + 0.6 * ease(seg(u, upa, ufr))
    camdir = M.norm(fr.cam.pos - C)
    for lat in range(-60, 90, 30):
        P_ = np.array([_gp(lat, lo, spin, np.zeros(3), R) for lo in np.linspace(0, 360, 80)])
        D._seg_by_depth(fr, P_, C, camdir)
    for lo0 in range(0, 180, 30):
        P_ = np.array([_gp(la, lo0, spin, np.zeros(3), R) for la in np.linspace(-90, 270, 90)])
        D._seg_by_depth(fr, P_, C, camdir)
    par = _gp(48.86, 2.35, spin, C, R)
    mex = _gp(19.43, -99.13, spin, C, R)
    kr = ease(seg(u, ufr - 0.3, ufr + 0.8))
    arc = []
    for s_ in np.linspace(0, kr, 40):
        p = par + (mex - par) * s_
        p = C + M.norm(p - C) * (R + 0.6 * math.sin(math.pi * s_))
        arc.append(p)
    if len(arc) > 1 and kr > 0.01:
        line3(fr, arc, col=AMARILLO, w=4, a=1.0, glow=1.4)
    for p, kk in ((par, seg(u, upa, upa + 0.2)), (mex, seg(u, ufr + 0.6, ufr + 0.8))):
        dot3(fr, p, r=10, col=WHITE, a=kk, glow=2.0)
    pp = fr.cam.p1(tuple(par))
    pm = fr.cam.p1(tuple(mex))

    def ui(img, fx):
        kicker(img, 'DE DÓNDE VINO LA IDEA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pp[0] + 40, pp[1] - 50, 'PARÍS · METRO SOBRE LLANTAS', eout(seg(u, upa, upa + 0.25)), size=22, border=AMARILLO)
        pill(img, fx, pm[0] - 40, pm[1] + 50, 'CIUDAD DE MÉXICO', eout(seg(u, ufr + 0.6, ufr + 0.85)), size=22, border=NARANJA)
        if u > u69 - 0.5:
            photo_card(img, fx, foto('mp68'), 540, 1180, 640, t - u + u69 - 0.5, t,
                       caption='MP-68 · Gob. CDMX · CC BY 4.0', angle0=-7.0)
            pill(img, fx, 540, 470, 'ALSTHOM (FRANCIA) · MODELO MP-68', eout(seg(u, u69 - 0.2, u69 + 0.1)), size=22,
                 border=(200, 200, 210), dot=False)
        P.numero_golpe(img, fx, '1969', 300, seg(u, u69, u69 + 0.15), size=210, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, u69 - 0.2, 0.3), golpe_k(u, u69 + 0.15, 0.3)), amp=18)


# 4. la prueba: rueda de acero sobre riel contra llanta de hule sobre pista (lado a lado, girando)
def _par_ruedas(fr, t, u, k_ac=1.0, k_hu=1.0, pend=0.0, slip=0.0, xl=-1.0, xr=1.0):
    ms = []
    if k_ac > 0.01:
        ms.append(named(M3.box(2.2, Y_RIEL + 0.06, 0.08, (150, 152, 160), shadow=0, gloss=0.9).tf(t=(xl, -0.06, 0)), 'riel', rim=0.8))
        ms += P.tfk(acero(x=0, z=0, yc=R_ACERO + Y_RIEL, giro=-t * 3 * (1 + 3 * slip)), s=max(0.05, k_ac), t=(xl, 0, 0.04))
    if k_hu > 0.01:
        ms.append(named(M3.box(2.2, 0.06, 0.4, CONCRETO, shadow=0, gloss=0.2).tf(t=(xr, -0.06, 0)), 'pista', rim=0.5))
        ll, _ = llanta(0.0, -t * 3, x=0, z=0)
        ms += P.tfk(ll, s=max(0.05, k_hu), t=(xr, 0, 0))
    if pend:
        ms = P.tfk(ms, rz=pend)
    draw_objects(fr, ms)


def s_prueba(t, fi, u, d):
    ua = Wp(4, 'acero') - 0.1
    uh = Wp(4, 'hule') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.2, -30, 8, ty=0.5), K(0.4, 4.4, -8, 6, ty=0.5), K(uh, 4.3, 10, 6, ty=0.5),
                          K(d, 4.2, 14, 6, ty=0.5)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8, beam=0.4)
    ka = P.resorte(seg(u, ua - 0.2, ua + 0.1)) if u > ua - 0.2 else 0.0
    kh = P.resorte(seg(u, uh - 0.2, uh + 0.1)) if u > uh - 0.2 else 0.0
    _par_ruedas(fr, t, u, ka, kh)
    pl = fr.cam.p1((-1.0, -0.2, 0))
    pr = fr.cam.p1((1.0, -0.2, 0))

    def ui(img, fx):
        kicker(img, 'LA PRUEBA', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 300, 'VS', 110, WHITE, eout(seg(u, uh - 0.3, uh - 0.15)), glow=0.5)
        pill(img, fx, pl[0], pl[1] + 70, 'ACERO SOBRE RIEL', eout(ka), size=24, border=ACERO)
        pill(img, fx, pr[0], pr[1] + 70, 'HULE SOBRE PISTA', eout(kh), size=24, border=NARANJA)
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, ua + 0.1, 0.25), golpe_k(u, uh + 0.1, 0.25)), amp=12)


# 5. el hule hace menos ruido y aguanta mejor las subidas (ondas de ruido; luego la rampa: el acero patina)
def s_subidas(t, fi, u, d):
    ur = Wp(5, 'ruido') - 0.1
    us = Wp(5, 'subidas') - 0.1
    pend = 14 * P.eout4(seg(u, us - 0.3, us + 0.2))
    fr = Frame(camara(u, [K(-0.3, 4.4, 14, 6, ty=0.5), K(us - 0.3, 4.4, 10, 6, ty=0.5), K(us, 5.0, 0, 4, ty=0.7),
                          K(d, 4.9, -4, 4, ty=0.7)], cy=0.6))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    _par_ruedas(fr, t, u, 1.0, 1.0, pend=pend, slip=seg(u, us, us + 0.3))
    if u < us:                                                               # ondas de ruido (grandes en el acero)
        for xc, amp_, col in ((-1.0, 1.0, ACERO), (1.0, 0.3, NARANJA)):
            for j in range(3):
                ph = (t * 1.6 + j / 3) % 1.0
                r = 0.3 + amp_ * 1.3 * ph
                line3(fr, [(xc + r * math.cos(a), 0.45 + r * math.sin(a), 0.2) for a in np.linspace(0.3, math.pi - 0.3, 24)],
                      col=col, w=3, a=(1 - ph) * seg(u, ur - 0.3, ur), glow=1.0)
    pl = fr.cam.p1((-1.0, 1.4, 0))
    pr = fr.cam.p1((1.0, 1.4, 0))

    def ui(img, fx):
        if u < us:
            kicker(img, 'RUIDO', 150, seg(u, -0.1, 0.2), col=AZULC)
            pill(img, fx, pl[0], pl[1] - 60, 'MÁS RUIDO', eout(seg(u, ur, ur + 0.25)), size=26, border=ACERO)
            pill(img, fx, pr[0], pr[1] - 60, 'MENOS RUIDO', eout(seg(u, ur + 0.1, ur + 0.35)), size=26, border=NARANJA)
        else:
            kicker(img, 'EN SUBIDA', 150, seg(u, us, us + 0.2), col=AZULC)
            pill(img, fx, pl[0], pl[1] - 40, 'PATINA', eout(seg(u, us + 0.2, us + 0.45)), size=26, border=RED)
            pill(img, fx, pr[0], pr[1] + 10, 'AGARRA', eout(seg(u, us + 0.3, us + 0.55)), size=26, border=VERDE)
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. ahora mira debajo de un vagón: la cámara baja, el vagón se vuelve de cristal y aparece el eje con dos llantas
def s_debajo(t, fi, u, d):
    ud = Wp(6, 'debajo') - 0.1
    ue = Wp(6, 'eje') - 0.1
    fr = Frame(camara(u, [K(-0.3, 9.0, 40, 12, ty=1.2), K(0.4, 8.0, 30, 10, ty=1.2), K(ud + 0.3, 4.2, 50, -4, ty=0.4, tx=1.6),
                          K(ue, 3.0, 70, 2, ty=0.3, tx=2.2), K(d, 2.9, 74, 2, ty=0.3, tx=2.2)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    ms = via(fr, -6, 6)
    ms += vagon(giro=0.0, acero_glow=0.0)
    xr = seg(u, ud, ud + 0.5)
    draw_objects(fr, ms, xray=xr, keep=('llanta', 'rin', 'eje', 'acero', 'pista', 'riel', 'barra', 'guia', 'bastidor', 'soporte'))
    pe = fr.cam.p1((2.2 + 0.41, 0.28, 0))

    def ui(img, fx):
        kicker(img, 'DEBAJO DEL VAGÓN · RAYOS X', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > ue:
            pill(img, fx, pe[0], pe[1] - 130, 'UN EJE · DOS LLANTAS', eout(seg(u, ue, ue + 0.25)), size=28, border=NARANJA)
            doodle_arrow(img, fx, pe[0] - 260, pe[1] + 60, pe[0] + 260, pe[1] + 60, t, k=seg(u, ue + 0.1, ue + 0.4), col=AMARILLO, seed=4)
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. por dentro de cada llanta, escondida, hay una rueda de acero (la llanta se vuelve de cristal)
def s_escondida(t, fi, u, d):
    ues = Wp(7, 'escondida') - 0.1
    uac = Wp(7, 'acero') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.6, 30, 8, ty=0.45, tz=0.7), K(0.4, 2.2, 50, 6, ty=0.45, tz=0.7),
                          K(uac, 1.9, 75, 4, ty=0.45, tz=0.68), K(d, 1.85, 80, 4, ty=0.45, tz=0.68)], cy=0.6))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    ms = []
    for s in (1,):
        _B(ms, 2.0, 0.06, 0.34, CONCRETO, 0, -0.06, s * ZT, name='pista', gloss=0.2)
        _B(ms, 2.0, Y_RIEL + 0.06, 0.07, (150, 152, 160), 0, -0.06, s * ZA, name='riel', gloss=0.9)
    ll, yc = llanta(0.0, -t * 1.5, z=ZT)
    ms += ll + acero(z=ZA, yc=yc, giro=-t * 1.5, glow=seg(u, uac, uac + 0.3))
    ms.append(tubo((0, yc, 0.2), (0, yc, ZT), r=0.06, col=(90, 94, 102), name='eje'))
    draw_objects(fr, ms, xray=seg(u, ues, ues + 0.4), keep=('acero', 'eje', 'riel', 'pista'))
    pa = fr.cam.p1((0, yc + R_ACERO, ZA))

    def ui(img, fx):
        kicker(img, 'RUEDA DE SEGURIDAD', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > uac:
            pill(img, fx, pa[0], pa[1] - 80, 'ACERO', eout(seg(u, uac, uac + 0.25)), size=30, border=CYAN)
            doodle_circle(img, fx, pa[0], pa[1] + 120, 170, 170, t, k=seg(u, uac, uac + 0.3), col=CYAN, seed=6)
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. segundo gancho: el error que nos retrasa a todos — detener las puertas (una mochila atorada en la puerta)
def mochila(x, z):
    ms = [named(M3.rbox(0.42, 0.55, 0.3, 0.1, (40, 70, 140), n=4, shadow=0, gloss=0.3).tf(t=(x, 1.25, z)), 'mochila', rim=0.6),
          named(M3.rbox(0.3, 0.2, 0.08, 0.06, (30, 55, 110), n=3, shadow=0, gloss=0.3).tf(t=(x, 1.3, z + 0.18)), 'mochila', rim=0.5),
          tubo((x - 0.12, 1.8, z), (x + 0.12, 1.8, z), r=0.025, col=(20, 20, 24), name='asa')]
    return ms


def s_error(t, fi, u, d):
    uer = Wp(8, 'error') - 0.1
    upu = Wp(8, 'puertas') - 0.1
    rebote = 0.55 + 0.45 * abs(math.sin(max(0.0, u - 0.3) * 5.0)) if u > 0.3 else 1 - 0.45 * seg(u, 0.0, 0.3)
    fr = Frame(camara(u, [K(-0.3, 6.0, 20, 6, ty=1.4), K(0.4, 5.0, 8, 4, ty=1.4), K(upu - 0.3, 4.6, 4, 4, ty=1.4),
                          K(upu, 3.2, 0, 2, ty=1.5), K(d, 3.1, -2, 2, ty=1.5)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'PUERTAS', u, t0=upu, cy=0.24, entrada='golpe')
    ms = vagon(puertas=rebote * 0.86)
    ms += mochila(0.0, 1.2)
    draw_objects(fr, ms)
    rojo = 0.5 + 0.5 * math.sin(t * 12)

    def ui(img, fx):
        texto(img, fx, 540, 250, 'EL ERROR', 110, RED, eout(seg(u, 0.0, 0.12)), glow=0.8)
        kicker(img, 'QUE NOS RETRASA A TODOS', 370, seg(u, uer, uer + 0.3), col=(255, 160, 150))
        if u > 0.6:
            pill(img, fx, 540, 1400, 'PUERTA ABIERTA', 1.0, size=30, border=M.mixc((120, 40, 40), RED, rojo))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.0, 0.3), golpe_k(u, upu, 0.3), 0.2 * (u > 0.3) * abs(math.sin(u * 5.0)) ** 8),
                   amp=18)


# 9. si una puerta no cierra, el tren no sale (semáforo en rojo, velocímetro en 0 y el reloj corriendo)
def s_nosale(t, fi, u, d):
    us = Wp(9, 'sale') - 0.1
    fr = Frame(camara(u, [K(-0.3, 8.0, -40, 8, ty=1.3, tx=-0.5), K(0.4, 7.2, -55, 6, ty=1.3, tx=-0.5), K(d, 7.0, -58, 6, ty=1.3, tx=-0.5)],
                      cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.4)
    ms = via(fr, -6, 6)
    ms += vagon(puertas=0.6 + 0.2 * abs(math.sin(u * 5)))
    ms += mochila(0.0, 1.2)
    _B(ms, 0.1, 2.8, 0.1, (60, 62, 70), -3.8, 0, 1.6, name='poste')
    _B(ms, 0.36, 0.7, 0.2, (20, 20, 24), -3.8, 2.8, 1.6, name='semaforo')
    draw_objects(fr, ms)
    dot3(fr, (-3.8, 3.32, 1.72), r=14, col=(255, 50, 40), glow=2.5)
    dot3(fr, (-3.8, 3.0, 1.72), r=12, col=(40, 60, 40), glow=0.0)

    def ui(img, fx):
        kicker(img, 'ANDÉN', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 300, '0 km/h', 110, WHITE, eout(seg(u, 0.0, 0.2)), f='mono', glow=0.3)
        cx, cy, r = 540, 470, 60
        dl = ImageDraw.Draw(img)
        dl.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(220, 220, 226), width=5)
        a = -math.pi / 2 + 2 * math.pi * ((u * 0.8) % 1.0)
        dl.line([(cx, cy), (cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a))], fill=AMARILLO, width=6)
        texto(img, fx, 540, 1400, 'EL TREN NO SALE', 56, (255, 110, 90), eout(seg(u, us, us + 0.25)), glow=0.6)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. y los que vienen atrás se amontonan (vista de arriba: los trenes se van juntando detrás del detenido)
def s_amontonan(t, fi, u, d):
    ua = Wp(10, 'amontonan') - 0.1
    fr = Frame(camara(u, [K(-0.3, 14.0, 0, 70, tx=-4.0, ty=0.0), K(0.5, 12.0, 10, 62, tx=-5.0, ty=0.0), K(d, 11.8, 12, 60, tx=-5.0, ty=0.0)],
                      cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    line3(fr, [(-18, 0.0, 0), (6, 0.0, 0)], col=WHITE, w=3, a=0.8, glow=0.6)
    ms = []
    for j in range(5):
        x0 = -j * 6.5
        xs = -j * 2.45
        x = lerp(x0, xs, P.eout4(seg(u, 0.1 + 0.25 * j, 0.9 + 0.25 * j))) if j else 0.0
        col = (255, 70, 50) if j == 0 else NARANJA
        _B(ms, 2.2, 0.5, 0.6, col, x, 0, 0, name='tren', gloss=0.7, glow=M.scale_c(col, 0.4))
    draw_objects(fr, ms)
    p0 = fr.cam.p1((0, 0.6, 0))

    def ui(img, fx):
        kicker(img, 'LA LÍNEA VISTA DESDE ARRIBA · ESQUEMA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, p0[0], p0[1] - 70, 'DETENIDO', 1.0, size=24, border=RED)
        texto(img, fx, 540, 1350, 'se amontonan', 84, WHITE, eout(seg(u, ua, ua + 0.25)), f='serif', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.3, 0.3), amp=12)


# 11. ¿y la rueda escondida? si una llanta se poncha… (la llanta se desinfla con aire que escapa)
def s_poncha(t, fi, u, d):
    up = Wp(11, 'poncha') - 0.1
    defl = P.eout4(seg(u, up, up + 0.8))
    fr = Frame(camara(u, [K(-0.3, 2.8, 40, 6, ty=0.45, tz=0.75), K(0.4, 2.4, 60, 4, ty=0.4, tz=0.75), K(up, 2.0, 80, 2, ty=0.35, tz=0.75),
                          K(d, 1.95, 84, 2, ty=0.35, tz=0.75)], cy=0.6))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    ms = []
    _B(ms, 2.2, 0.06, 0.34, CONCRETO, 0, -0.06, ZT, name='pista', gloss=0.2)
    _B(ms, 2.2, Y_RIEL + 0.06, 0.07, (150, 152, 160), 0, -0.06, ZA, name='riel', gloss=0.9)
    ll, yc = llanta(defl, 0.0, z=ZT)
    ms += ll + acero(z=ZA, yc=yc, glow=0.4 * (1 - seg(u, 0.0, 0.5)))
    draw_objects(fr, ms, xray=0.5 * (1 - seg(u, 0.0, 0.6)), keep=('llanta', 'rin', 'pista', 'riel'))
    if u > up:
        for j in range(14):
            ph = (t * 2.2 + j / 14) % 1.0
            a = j * 0.9
            p = np.array([0.35 * math.cos(a) + 0.9 * ph * math.cos(a), 0.3 + 0.35 * math.sin(a) + 0.9 * ph * math.sin(a), ZT + 0.2])
            dot3(fr, p, r=3.5, col=AZULC, a=(1 - ph) * (1 - seg(u, up + 1.2, up + 1.8)), glow=1.0)
    pl = fr.cam.p1((0, 0.55, ZT))

    def ui(img, fx):
        texto(img, fx, 540, 270, '¿y la rueda escondida?', 62, WHITE, eout(seg(u, 0.0, 0.25)), f='serif', glow=0.3)
        texto(img, fx, pl[0], pl[1] - 330, '¡PSSS!', 80, AZULC, eout(seg(u, up, up + 0.15)) * (1 - seg(u, up + 1.0, up + 1.4)), glow=0.6)
        if u > up:
            doodle_circle(img, fx, pl[0], pl[1] + 60, 220, 200, t, k=seg(u, up, up + 0.3), col=RED, seed=8)
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return finish(fr, fi)


# 12. esa rueda de acero carga el peso del vagón (se apoya en el riel, chispas y flechas de peso; el tren sigue)
def s_carga(t, fi, u, d):
    uc = Wp(12, 'carga') - 0.1
    upe = Wp(12, 'peso') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.3, 70, 4, ty=0.4, tz=0.65), K(0.4, 2.8, 40, 8, ty=0.5, tz=0.65), K(upe, 3.4, 20, 12, ty=0.7, tz=0.6),
                          K(d, 3.3, 16, 12, ty=0.7, tz=0.6)], cy=0.62))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    ms = []
    _B(ms, 3.0, 0.06, 0.34, CONCRETO, 0, -0.06, ZT, name='pista', gloss=0.2)
    _B(ms, 3.0, Y_RIEL + 0.06, 0.07, (150, 152, 160), 0, -0.06, ZA, name='riel', gloss=0.9)
    ll, yc = llanta(1.0, -t * 2, z=ZT)
    ms += ll + acero(z=ZA, yc=yc, giro=-t * 2, glow=0.8)
    _B(ms, 1.6, 0.14, 0.9, (60, 64, 72), 0, yc + 0.12, 0.45, name='bastidor', gloss=0.5)
    draw_objects(fr, ms)
    for j in range(10):                                                      # chispas del acero en el riel
        ph = (t * 5 + j / 10) % 1.0
        dot3(fr, (0.05 - 0.7 * ph, Y_RIEL + 0.05 + 0.2 * math.sin(math.pi * ph) * ((j % 3) + 1) / 3, ZA + 0.05 * (j % 3 - 1)),
             r=3.5, col=(255, 210, 140), a=(1 - ph) * seg(u, 0.0, 0.2), glow=2.0)
    kpe = seg(u, upe, upe + 0.3)
    for xx in (-0.5, 0.0, 0.5):                                              # flechas del peso del vagón
        if kpe > 0:
            line3(fr, [(xx, 1.6, 0.5), (xx, 1.6 - 0.8 * kpe, 0.5)], col=AMARILLO, w=5, a=kpe, glow=1.2)
            line3(fr, [(xx - 0.08, 0.88 + 0.72 * (1 - kpe), 0.5), (xx, 0.8 + 0.8 * (1 - kpe), 0.5), (xx + 0.08, 0.88 + 0.72 * (1 - kpe), 0.5)],
                  col=AMARILLO, w=5, a=kpe, glow=1.2)
    pa = fr.cam.p1((0, Y_RIEL, ZA))

    def ui(img, fx):
        kicker(img, 'LLANTA PONCHADA', 150, seg(u, -0.1, 0.2), col=(255, 170, 160))
        pill(img, fx, pa[0], pa[1] + 80, 'EL ACERO SE APOYA EN EL RIEL', eout(seg(u, uc, uc + 0.25)), size=24, border=CYAN)
        texto(img, fx, 540, 300, 'carga el peso', 76, AMARILLO, eout(seg(u, upe, upe + 0.25)), f='serif', glow=0.4)
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.0, 0.35), amp=20)


# 13. a los lados, llantitas guía tocan una barra que lleva 750 voltios (carretón visto de arriba + arcos eléctricos)
def s_guia(t, fi, u, d):
    ug = Wp(13, 'guia') - 0.1
    ub = Wp(13, 'barra') - 0.1
    uv = Wp(13, 'setecientos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.6, 50, 40, ty=0.3), K(0.4, 4.6, 30, 34, ty=0.3), K(ug, 3.0, 70, 22, ty=0.35, tz=0.9),
                          K(uv, 4.4, 20, 30, ty=0.35, tz=0.4), K(d, 4.3, 16, 30, ty=0.35, tz=0.4)], cy=0.62))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, '750 V', u, t0=uv, cy=0.26, entrada='golpe')
    mov = t * 2.5
    ms = via(fr, -4, 4, mov=mov, barra_glow=0.6 * seg(u, uv, uv + 0.3))
    ms += carreton(0, -mov / ROUT)
    draw_objects(fr, ms)
    if u > uv:                                                               # arcos eléctricos a lo largo de la barra
        rng = np.random.RandomState(int(t * 24) % 1000)
        for s in (-1, 1):
            pts = [(x, 0.46 + 0.05 * rng.randn(), s * (ZG + 0.17)) for x in np.linspace(-3.5, 3.5, 30)]
            line3(fr, pts, col=(255, 240, 160), w=2.5, a=0.8 * seg(u, uv, uv + 0.2), glow=2.0)
    pgw = fr.cam.p1((0.75, 0.45, ZG))
    pb = fr.cam.p1((-1.6, 0.5, ZG + 0.2))

    def ui(img, fx):
        kicker(img, 'CARRETÓN · VISTA DE ARRIBA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pgw[0], pgw[1] - 110, 'RUEDA GUÍA', eout(seg(u, ug, ug + 0.25)), size=26, border=AMARILLO)
        pill(img, fx, pb[0], pb[1] + 90, 'BARRA GUÍA', eout(seg(u, ub, ub + 0.25)), size=26, border=AMARILLO)
        if u > uv:
            pill(img, fx, 540, 1390, '750 VOLTIOS · CORRIENTE DIRECTA', eout(seg(u, uv + 0.3, uv + 0.55)), size=24, border=(255, 240, 160))
        esquema(img, fx, 1.0, y=1460)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uv, 0.3), amp=14)


# 14. su punto débil es la lluvia: con vías y llantas mojadas (viaducto elevado bajo la lluvia)
def lluvia(fr, t, k, x0=-6, x1=6, n=70, y0=-0.5, y1=6.0):
    if k <= 0.01:
        return
    rng = np.random.RandomState(7)
    for j in range(n):
        x = x0 + (x1 - x0) * rng.rand()
        z = -2.5 + 5 * rng.rand()
        ph = (t * 1.6 + rng.rand()) % 1.0
        y = y1 - (y1 - y0) * ph
        line3(fr, [(x, y, z), (x - 0.04, y - 0.35, z)], col=AZULC, w=1.6, a=0.6 * k, glow=0.5)


def viaducto(fr, a=1.0):
    for x in (-5, -1.7, 1.7, 5):
        for z in (-0.5, 0.5):
            line3(fr, [(x, -3.0, z), (x, -0.15, z)], col=WHITE, w=2.4, a=0.7 * a, glow=0.5)
    for z in (-1.5, 1.5):
        line3(fr, [(-8, -0.15, z), (8, -0.15, z)], col=WHITE, w=2.4, a=0.7 * a, glow=0.5)


def s_lluvia(t, fi, u, d):
    ul = Wp(14, 'lluvia') - 0.1
    um = Wp(14, 'mojadas') - 0.1
    fr = Frame(camara(u, [K(-0.3, 12.0, 30, 10, ty=0.5), K(0.4, 10.0, 20, 6, ty=0.5), K(um - 0.3, 9.5, 16, 6, ty=0.5),
                          K(um, 3.0, 50, 2, ty=0.3, tx=2.2, tz=0.4), K(d, 2.9, 54, 2, ty=0.3, tx=2.2, tz=0.4)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.6)
    M.cristal(fr.base, fr.fx, 'LLUVIA', u, t0=ul, cy=0.25, entrada='sube')
    viaducto(fr)
    ms = via(fr, -7, 7, mov=t * 1.5)
    ms += vagon(giro=-t * 1.5 / ROUT * 0.55)
    draw_objects(fr, ms)
    lluvia(fr, t, seg(u, ul - 0.4, ul))
    if u > um:
        for j in range(10):                                                  # gotas que salpican de la llanta
            ph = (t * 3 + j / 10) % 1.0
            dot3(fr, (2.2 + 0.41 - 0.6 * ph, 0.05 + 0.3 * math.sin(math.pi * ph), 0.45 + 0.05 * (j % 3)), r=3, col=AZULC,
                 a=1 - ph, glow=1.0)

    def ui(img, fx):
        kicker(img, 'TRAMO ELEVADO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1400, 'VÍAS Y LLANTAS MOJADAS', eout(seg(u, um, um + 0.25)), size=26, border=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. en los tramos elevados baja de 70 a 35 km/h (velocímetro que cae; marcha de seguridad)
def s_70a35(t, fi, u, d):
    u70 = Wp(15, 'setenta') - 0.1
    u35 = Wp(15, 'treinta') - 0.1
    v = 70 if u < u35 else 70 - 35 * P.eout4(seg(u, u35, u35 + 0.8))
    fr = Frame(camara(u, [K(-0.3, 9.0, -30, 8, ty=0.5), K(0.4, 8.0, -14, 6, ty=0.5), K(d, 7.8, -10, 6, ty=0.5)], cy=0.66))
    space(fr, t, floor=None, bokeh=0.6)
    viaducto(fr)
    ms = via(fr, -7, 7, mov=t * v / 25)
    ms += vagon(giro=-t * v / 25 / ROUT * 0.55)
    draw_objects(fr, ms)
    lluvia(fr, t, 1.0)

    def ui(img, fx):
        kicker(img, 'MARCHA DE SEGURIDAD · STC', 150, seg(u, -0.1, 0.2), col=AZULC)
        cx, cy, r = 540, 520, 230
        dl = ImageDraw.Draw(img)
        dl.arc((cx - r, cy - r, cx + r, cy + r), 150, 390, fill=(220, 220, 226), width=8)
        for vv in range(0, 81, 10):
            a = math.radians(150 + 240 * vv / 80)
            dl.line([(cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a)), (cx + r * math.cos(a), cy + r * math.sin(a))],
                    fill=(200, 200, 205), width=4)
        a = math.radians(150 + 240 * v / 80)
        dl.line([(cx, cy), (cx + (r - 40) * math.cos(a), cy + (r - 40) * math.sin(a))], fill=(255, 90, 70), width=10)
        ImageDraw.Draw(fx).line([(cx, cy), (cx + (r - 40) * math.cos(a), cy + (r - 40) * math.sin(a))], fill=(160, 50, 40), width=18)
        texto(img, fx, cx, cy + 110, f'{v:.0f} km/h', 80, WHITE, 1.0, f='mono', glow=0.4)
        if u > u35:
            pill(img, fx, 540, 1400, 'DE 70 A 35 KM/H CON LLUVIA', eout(seg(u, u35 + 0.3, u35 + 0.55)), size=26, border=(255, 90, 70))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, u70, 0.25), golpe_k(u, u35 + 0.8, 0.35)), amp=16)


# 16. y así mueve más de 1 200 millones de viajes al año (contador; viajes como puntos que suben al tren)
def s_millones(t, fi, u, d):
    um = Wp(16, 'mil') - 0.1
    n = 1241582324 * P.eout4(seg(u, 0.0, um + 1.2))
    fr = Frame(camara(u, [K(-0.3, 9.0, 60, 14, ty=1.2), K(0.5, 8.0, 40, 10, ty=1.2), K(d, 7.8, 36, 10, ty=1.2)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.5)
    draw_objects(fr, vagon(puertas=0.0))
    for j in range(40):
        ph = (t * 0.7 + j / 40) % 1.0
        x = -1.5 + 1.5 * (j % 3)
        z = 3.6 - 2.3 * ph
        dot3(fr, (x + 0.3 * math.sin(j), 0.9, z), r=4, col=(255, 220, 170), a=0.9 * (1 - ph) * seg(u, 0.0, 0.3), glow=1.0)

    def ui(img, fx):
        kicker(img, 'VIAJES EN 2025 · STC', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 330, f'{int(n):,}'.replace(',', ' '), 92, WHITE, 1.0, f='mono', glow=0.4)
        texto(img, fx, 540, 450, 'viajes al año', 64, AMARILLO, eout(seg(u, um + 0.6, um + 0.9)), f='serif', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 1.2, 0.3), amp=14)


# 17. mándaselo a quien se sube diario al metro (el vagón en el andén, foto real del NM-16 que cae)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.0, 70, 6, ty=1.3), K(0.4, 7.0, 40, 4, ty=1.3), K(d, 6.9, 34, 4, ty=1.3)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.0)
    ms = via(fr, -6, 6)
    ms += vagon(puertas=1.0)
    draw_objects(fr, ms)

    def ui(img, fx):
        photo_card(img, fx, foto('nm16'), 540, 860, 540, t - u + 0.05, t, caption='NM-16 · Gob. CDMX · CC BY 4.0', angle0=6.0)
        P.titulo_golpe(img, fx, [('Mándaselo a quien', 'sans'), ('se sube diario al metro.', 'serif')], 190, seg(u, 0.0, 0.15), size=64)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45),
                sfx=[(-3.9, 'tick2', 0.6)] + [(-3.5 + 0.075 * j, 'click', 0.22) for j in range(31)] +
                    [(U_ENTER - 0.05, 'click', 1.0), (U_ENTER, 'whoosh', 0.9), (0.3, 'bass', 0.8), (1.65, 'sub', 0.8),
                     (1.8, 'scribble', 0.5)]),
           dict(desde=1, fn=s_neumaticos, tr='mosaico', sfx=[(0.1 + 0.05 * j, 'tick', 0.4) for j in range(12)] + [(2.2, 'bass', 0.7)]),
           dict(desde=2, fn=s_acero, tr='cubo_izq', sfx=[(0.4, 'chime_a', 0.5), (1.3, 'chime_b', 0.5), (2.0, 'bass', 0.8)]),
           dict(desde=3, fn=s_paris, tr='flash', sfx=[(0.75, 'chime_c', 0.4), (2.9, 'whoosh_suave', 0.6), (3.3, 'slap', 0.8),
                                                    (3.7, 'bass', 0.9)]),
           dict(desde=4, fn=s_prueba, tr='deslizar', sfx=[(1.4, 'thud', 0.8), (2.7, 'thud', 0.8), (2.5, 'whoosh', 0.5)]),
           dict(desde=5, fn=s_subidas, tr='whip', sfx=[(1.0, 'burst', 0.4), (2.2, 'whoosh_suave', 0.6), (2.6, 'tick2', 0.5)]),
           dict(desde=6, fn=s_debajo, tr='zoom', c=(0.5, 0.7), sfx=[(0.6, 'whoosh', 0.7), (0.9, 'shimmer', 0.5), (2.3, 'scribble', 0.5)]),
           dict(desde=7, fn=s_escondida, tr='cristal', palabra='ESCONDIDA', sfx=[(1.7, 'shimmer', 0.5), (3.4, 'chime_b', 0.6)]),
           dict(desde=8, fn=s_error, tr='rompe', c=(0.5, 0.4), sfx=[(0.0, 'bass', 0.9), (0.0, 'digital', 0.5)] +
                [(0.3 + 0.63 * j, 'thud', 0.6) for j in range(6)] + [(3.4, 'sub', 0.8)]),
           dict(desde=9, fn=s_nosale, tr='glitch', sfx=[(0.1, 'tick', 0.5), (1.1, 'tick', 0.5), (1.95, 'bass', 0.7)]),
           dict(desde=10, fn=s_amontonan, tr='deslizar_abajo', sfx=[(0.3 + 0.25 * j, 'thud', 0.5) for j in range(4)]),
           dict(desde=11, fn=s_poncha, tr='iris', c=(0.55, 0.55), sfx=[(2.4, 'burst', 0.9), (2.5, 'whoosh_suave', 0.6)]),
           dict(desde=12, fn=s_carga, tr='golpe', sfx=[(0.0, 'sub', 0.9), (0.9, 'click', 0.5), (1.4, 'bass', 0.7)]),
           dict(desde=13, fn=s_guia, tr='rebanadas', sfx=[(1.6, 'click', 0.6), (2.5, 'click', 0.6), (3.2, 'digital', 0.8),
                                                        (3.25, 'burst', 0.6)]),
           dict(desde=14, fn=s_lluvia, tr='remolino', sfx=[(0.6, 'whoosh_suave', 0.5), (1.1, 'shimmer', 0.4), (2.9, 'whoosh', 0.6)]),
           dict(desde=15, fn=s_70a35, tr='whip_izq', sfx=[(1.5, 'tick', 0.6), (2.4, 'riser', 0.3), (3.2, 'bass', 0.8)]),
           dict(desde=16, fn=s_millones, tr='giro', sfx=[(0.1, 'riser', 0.5), (2.4, 'bass', 0.8), (2.6, 'chime_c', 0.5)]),
           dict(desde=17, fn=s_compa, tr='ritmo', sfx=[(0.05, 'slap', 0.7), (0.15, 'bass', 0.7)]),
           dict(desde=18, loop=True, tr='push', c=(0.5, 0.45))]

if __name__ == '__main__':
    montaje.cli(globals())
