"""Reel diario mié 25-nov-2026 18:00 (propuesto) — «Tu tráiler no es el tráiler… es el que lo jala.»
Corregir la palabra (la palanca del razer): «trailer» en inglés es la caja; lo que manejas es el tractocamión («el tracto»).
NOM-012-SCT-2-2017: semirremolque = «vehículo sin eje delantero… de manera que sea jalado y parte de su peso sea soportado»
por el tractocamión. Se engancha en la quinta rueda (plato con grasa) donde se traba el perno rey. Como la carretilla: el
tracto carga parte del peso y por eso sus llantas de tracción agarran. En la vuelta las llantas de la caja cortan la curva
por dentro. Error (segundo gancho): meterte por la derecha cuando el tráiler da vuelta (abre a la izquierda, el hueco parece
libre, la caja se cierra sobre ti y ahí casi no te ve; FMCSA: si no ves al chofer en su espejo, él no te ve). Largos máximos
(NOM-012): tracto con caja 23 m, full 31 m (≈ edificio de 10 pisos acostado).
Comunidad: traileros y automovilistas. Inicio tipo 11 (pregunta directa): «¿LE DICES TRÁILER?» gigante sobre el tractocamión
completo; se rompe en pedazos, la caja se suelta y se va para atrás («CAJA» de cristal detrás) y el título se estrella.
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Foto real: «Kingpin.jpg» (perno rey bajo una caja), Sterkebak, Wikimedia Commons, CC BY 3.0. Lo demás son esquemas sin marca.
Datos y fuentes: guiones/2026-11-25_caja.txt.
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
from gasolina import texto, esquema, golpe_k, sacudir, K, camara
import trailer as TR
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
TEMA = 'caja'
TXT = ['Tu tráiler no es el tráiler… es el que lo jala.',
       'Tráiler, en inglés, es la caja;',
       'lo que manejas es el tractocamión: el tracto.',
       'La norma mexicana le dice semirremolque:',
       'no tiene eje adelante y se recarga en el tracto.',
       'Se engancha en la quinta rueda:',
       'un plato con grasa donde se traba el perno rey de la caja.',
       'Ahí se apoya y gira, como una carretilla:',
       'el tracto carga parte del peso y por eso sus llantas agarran.',
       'Pero en la vuelta, las llantas de la caja no siguen al tracto:',
       'cortan la curva por dentro.',
       'Y aquí está el error:',
       'meterte por la derecha cuando el tráiler da vuelta.',
       'El trailero abre hacia la izquierda para librar la esquina,',
       'y ese hueco parece libre.',
       'Si te metes, la caja se cierra sobre ti,',
       'y ahí casi no te ve.',
       'Regla de oro: si no ves su cara en el espejo,',
       'él tampoco te ve a ti.',
       'Con la direccional prendida, nunca te metas entre el tráiler y la banqueta.',
       'Y entre más larga la caja, más corta la curva:',
       'un tracto con caja mide hasta 23 metros.',
       'Y un full, con dos cajas, hasta 31:',
       'como un edificio de 10 pisos acostado.',
       'Mándaselo a quien se mete por la derecha cuando el tráiler da vuelta.',
       'Y que se acuerde: su tráiler no es el tráiler… es el que lo jala.']
VOZ = ['Tu tráiler no es el tráiler... es el que lo jala.',
       'Tráiler, en inglés, es la caja;',
       'lo que manejas es el tractocamión: el tracto.',
       'La norma mexicana le dice semirremolque:',
       'no tiene eje adelante y se recarga en el tracto.',
       'Se engancha en la quinta rueda:',
       'un plato con grasa donde se traba el perno rey de la caja.',
       'Ahí se apoya y gira, como una carretilla:',
       'el tracto carga parte del peso y por eso sus llantas agarran.',
       'Pero en la vuelta, las llantas de la caja no siguen al tracto:',
       'cortan la curva por dentro.',
       'Y aquí está el error:',
       'meterte por la derecha cuando el tráiler da vuelta.',
       'El trailero abre hacia la izquierda para librar la esquina,',
       'y ese hueco parece libre.',
       'Si te metes, la caja se cierra sobre ti,',
       'y ahí casi no te ve.',
       'Regla de oro: si no ves su cara en el espejo,',
       'él tampoco te ve a ti.',
       'Con la direccional prendida, nunca te metas entre el tráiler y la banqueta.',
       'Y entre más larga la caja, más corta la curva:',
       'un tracto con caja mide hasta veintitrés metros.',
       'Y un full, con dos cajas, hasta treinta y uno:',
       'como un edificio de diez pisos acostado.',
       'Mándaselo a quien se mete por la derecha cuando el tráiler da vuelta.',
       'Y que se acuerde: su tráiler no es el tráiler... es el que lo jala.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_caja.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-25_caja_words.json')
IMG = os.path.join(HERE, 'img', 'caja')

AMARILLO = (255, 236, 160)
NARANJA = (255, 150, 60)
AMBAR = (255, 170, 40)
ROJO = (240, 50, 42)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (90, 220, 140)
VERDE_T = (22, 92, 66)          # tracto verde oscuro
CAJA_C = (226, 228, 232)
NEGRO = (24, 24, 27)
CROMO = (212, 214, 220)
VIDRIO = (26, 34, 46)
GRASA = (60, 56, 44)

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


_F = {}


def foto(nombre):
    if nombre not in _F:
        p = os.path.join(IMG, nombre)
        _F[nombre] = Image.open(p).convert('RGB') if os.path.exists(p) else None
    return _F[nombre]


# ------------------------------------------------------------------ el tracto y la caja (frente hacia +x; la quinta rueda en x = 0)
QX = 0.40          # x de la quinta rueda en el modelo original de trailer.py
B_ = TR._B
LL = TR._llanta


def tracto(col=VERDE_T, giro=0.0, faros=0.7, direccional=0.0, quinta=True):
    ms = []
    B_(ms, 2.55, 0.12, 0.56, (38, 38, 42), 1.02 - QX, 0.34, 0, gloss=0.2)            # chasis corto
    B_(ms, 0.62, 1.28, 0.92, col, 0.56 - QX + 0.25, 0.47, 0, gloss=0.55)              # dormitorio
    B_(ms, 0.64, 1.02, 0.92, col, 1.18 - QX + 0.2, 0.47, 0, gloss=0.55)               # cabina
    B_(ms, 0.05, 0.36, 0.8, VIDRIO, 1.51 - QX + 0.2, 1.02, 0, gloss=0.95, rim=0.9)   # parabrisas
    for z in (-0.47, 0.47):
        B_(ms, 0.3, 0.3, 0.02, VIDRIO, 1.2 - QX + 0.2, 1.0, z, gloss=0.9)
        B_(ms, 0.04, 0.26, 0.06, CROMO, 1.47 - QX + 0.2, 1.0, z * 1.14, gloss=0.95)
    B_(ms, 0.8, 0.5, 0.86, col, 1.9 - QX + 0.2, 0.47, 0, gloss=0.6)                   # cofre
    B_(ms, 0.05, 0.42, 0.62, CROMO, 2.31 - QX + 0.2, 0.5, 0, gloss=0.95, rim=0.9)    # parrilla
    for j in range(5):
        B_(ms, 0.06, 0.02, 0.6, (70, 70, 76), 2.33 - QX + 0.2, 0.56 + j * 0.07, 0, gloss=0.3)
    B_(ms, 0.12, 0.15, 1.0, CROMO, 2.34 - QX + 0.2, 0.31, 0, gloss=0.95, rim=0.9)
    for z in (-0.33, 0.33):
        B_(ms, 0.04, 0.09, 0.15, (255, 244, 214), 2.32 - QX + 0.2, 0.7, z, glow=M.scale_c((255, 226, 160), faros))
    for z in (-0.5, 0.5):
        ms.append(named(M3.cyl(0.042, 1.25, CROMO, n=14, shadow=0, gloss=0.95).tf(t=(0.86 - QX + 0.12, 0.66, z)), 'escape', rim=0.85))
        ms.append(named(M3.cyl(0.13, 0.5, CROMO, n=16, shadow=0, gloss=0.9).tf(rz=90, t=(1.72 - QX + 0.2, 0.27, z)), 'tanque', rim=0.8))
    if direccional > 0.01:                                                         # direccional derecha (lado +z)
        B_(ms, 0.06, 0.08, 0.04, AMBAR, -0.2, 0.4, 0.3, glow=M.scale_c(AMBAR, direccional))
        B_(ms, 0.05, 0.08, 0.04, AMBAR, 2.34 - QX + 0.2, 0.45, 0.47, glow=M.scale_c(AMBAR, direccional))
    if quinta:                                                                     # quinta rueda: plato con grasa
        ms.append(named(M3.cyl(0.3, 0.05, GRASA, n=28, shadow=0, gloss=0.95).tf(t=(0, 0.41, 0)), 'quinta', rim=0.8, gloss=0.95))
        B_(ms, 0.34, 0.012, 0.08, (14, 14, 16), -0.15, 0.462, 0, name='quinta', gloss=0.2)
    for x in (1.98 + 0.2, 0.62, 0.18):
        for z in (-0.4, 0.4):
            LL(ms, x - QX, z, giro=giro)
    return ms


def caja(largo=4.0, col=CAJA_C, giro=0.0, patas=True, perno=True, ejes=True):
    """Caja seca (semirremolque) con el perno rey en x = 0; sin eje delantero: adelante solo las patas."""
    ms = []
    cx = -largo / 2 + 0.3
    B_(ms, largo, 1.3, 0.94, col, cx, 0.5, 0, gloss=0.3, rim=0.6)
    n = int(largo / 0.46)
    for j in range(n):
        B_(ms, 0.03, 1.28, 0.955, (196, 198, 204), 0.3 - largo + 0.2 + j * (largo - 0.4) / max(1, n - 1), 0.51, 0, gloss=0.2)
    B_(ms, largo - 0.2, 0.1, 0.5, (40, 40, 44), cx, 0.42, 0, gloss=0.2)            # largueros
    if ejes:
        for x in (0.3 - largo + 0.7, 0.3 - largo + 1.15):
            for z in (-0.38, 0.38):
                LL(ms, x, z, giro=giro)
    if patas:
        for z in (-0.36, 0.36):
            B_(ms, 0.06, 0.48, 0.06, (120, 124, 130), -0.75, 0.02, z, name='patas', gloss=0.5)
            B_(ms, 0.16, 0.03, 0.16, (90, 92, 98), -0.75, 0.0, z, name='patas')
    if perno:
        ms.append(named(M3.cyl(0.045, 0.1, (190, 192, 198), n=14, shadow=0, gloss=0.9).tf(t=(0, 0.4, 0)), 'perno', rim=0.9, gloss=0.9))
    return ms


def pose(ms, q, ang):
    """Coloca mallas: q = (x, z) de la quinta rueda, ang = rumbo en grados (0 = +x, positivo = hacia −z)."""
    return P.tfk(ms, ry=ang, t=(q[0], 0, q[1]))


def adelante(ang):
    a = math.radians(ang)
    return np.array([math.cos(a), -math.sin(a)])


# ------------------------------------------------------------------ la vuelta a la derecha (cinemática simple de la caja)
L_CAJA = 3.0       # del perno rey al eje de la caja (largo 4.0: ejes en −2.7 a −3.15)
R_V = 3.0


def _trayectoria(swing=14.0, L=L_CAJA, ds=0.01):
    """Rumbo del tracto φ(s) (grados): recto, abre a la izquierda (+swing) y luego da vuelta a la derecha hasta −90.
    La caja sigue: dθ/ds = sin(φ − θ) / L. Devuelve arrays de s, q (x, z), φ, θ."""
    S1, S2 = 5.0, 6.4
    arco = math.radians(90 + swing) * R_V
    S = S2 + arco + 6.0
    ss = np.arange(0, S, ds)
    q = np.zeros((len(ss), 2))
    ph = np.zeros(len(ss))
    th = np.zeros(len(ss))
    p = np.array([-7.0, 0.0])
    t_ = 0.0
    for i, s in enumerate(ss):
        if s < S1:
            f = 0.0
        elif s < S2:
            f = swing * ease((s - S1) / (S2 - S1))
        elif s < S2 + arco:
            f = swing - math.degrees((s - S2) / R_V)
        else:
            f = -90.0
        ph[i] = f
        q[i] = p
        th[i] = t_
        p = p + adelante(f) * ds
        t_ = t_ + math.degrees(math.sin(math.radians(f - t_)) / L * ds)
    return ss, q, ph, th


TRAY = _trayectoria()
TRAY_C = _trayectoria(L=1.9)        # caja corta (para «entre más larga, más corta la curva»)


def en(tray, s):
    ss, q, ph, th = tray
    i = int(clamp(s / (ss[1] - ss[0]), 0, len(ss) - 1))
    return q[i], ph[i], th[i], i


def rueda_caja(q, th, L=L_CAJA, lado=0.45):
    """Llanta trasera derecha de la caja (lado +z cuando va hacia +x)."""
    return q - adelante(th) * L + _derecha(th) * lado


def _derecha(ang):
    a = math.radians(ang)
    return np.array([math.sin(a), math.cos(a)])          # (cos, −sin) girado −90° en planta → derecha


def rueda_tracto(q, ph, lado=0.45):
    return q + adelante(ph) * (1.98 + 0.2 - QX) + _derecha(ph) * lado


def _esquina():
    """La esquina de la banqueta: carril a la derecha en z = 1.17 y la orilla de la otra calle justo donde la llanta de
    atrás de la caja la libra (la caja corta la curva por dentro)."""
    ss, q, ph, th = TRAY
    zk = 0.62 + 0.55
    W = [rueda_caja(q[i], th[i]) for i in range(0, len(ss), 3)]
    xk = min(w[0] for w in W if w[1] > zk) - 0.12
    return xk, zk


XK, ZK = _esquina()


def calle(fr, a=0.8, banqueta=True):
    """Calle con la esquina a la derecha (line-art): la banqueta forma la esquina (XK, ZK)."""
    r = 0.6
    if banqueta:
        pts = [(-14, 0.01, ZK)] + [(XK - r + r * math.sin(math.radians(g)), 0.01, ZK + r - r * math.cos(math.radians(g))) for g in range(0, 91, 10)] + [(XK, 0.01, 14)]
        line3(fr, pts, col=WHITE, w=3.0, a=a, glow=0.6)
    line3(fr, [(-14, 0.01, -1.7), (XK + 3.6, 0.01, -1.7)], col=WHITE, w=2.4, a=0.6 * a, glow=0.4)
    line3(fr, [(XK + 3.6, 0.01, -1.7), (XK + 3.6, 0.01, 14)], col=WHITE, w=2.4, a=0.6 * a, glow=0.4)
    for j in range(12):
        x0 = -14 + j * 1.2
        if x0 + 0.6 < XK:
            line3(fr, [(x0, 0.012, -0.55 + 0.0), (x0 + 0.6, 0.012, -0.55)], col=AMARILLO, w=2.6, a=0.6 * a, glow=0.6)


def huella(fr, tray, i, fn, col, w=4.0, a=1.0, paso=8):
    ss, q, ph, th = tray
    pts = []
    for j in range(0, max(1, i), paso):
        x, z = fn(q[j], ph[j], th[j])
        pts.append((x, 0.02, z))
    if len(pts) >= 2:
        line3(fr, pts, col=col, w=w, a=a, glow=0.9)


def rig(tray, s, giro=0.0, direccional=0.0, col=VERDE_T, largo=4.0):
    q, ph, th, i = en(tray, s)
    return pose(tracto(col=col, giro=giro, direccional=direccional), q, ph) + pose(caja(largo=largo, giro=giro, patas=False), q, th), i


def flecha(img, fx, x0, y0, x1, y1, col, k=1.0, w=8):
    V.flecha(img, fx, x0, y0, x1, y1, col, k=k, w=w)


def carro_mini(col=(60, 110, 190), giro=0.0, ang=0.0, p=(0, 0), s=0.4):
    return P.tfk(V.carro(col=col, giro_llanta=giro), s=s, ry=ang, t=(p[0], 0, p[1]))


# ================================================================== escenas
UG = 0.3


def _gancho_frame(t, fi, u, pregunta):
    fr = Frame(camara(u, [K(-4.0, 10.0, -36, 14, tx=-1.0, ty=0.8), K(UG, 9.6, -30, 12, tx=-1.0, ty=0.8),
                          K(UG + 0.6, 8.8, -50, 10, tx=-1.4, ty=0.8), K(3.2, 8.6, -54, 10, tx=-1.4, ty=0.8)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    if not pregunta:
        M.cristal(fr.base, fr.fx, 'CAJA', u, t0=-2.6, cy=0.36, entrada='golpe')
    TR.carretera(fr, t, vel=0.0 if u < UG else 0.0, a=0.6)
    ks = P.eout4(seg(u, UG + 0.1, UG + 0.8))                   # la caja se suelta y se va para atrás
    ms = tracto(giro=0.0) + P.tfk(caja(giro=0.0), t=(-0.9 * ks, 0.12 * math.sin(math.pi * ks), 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        if pregunta:
            a = Image.new('L', img.size, 0)
            ImageDraw.Draw(a).rectangle((0, 0, 1080, 1920), fill=110)
            img.paste((0, 0, 0), (0, 0), a)
            texto(img, fx, 540, 700, '¿LE DICES', 150, WHITE, 1.0, f='sansx', glow=0.4)
            texto(img, fx, 540, 880, 'TRÁILER?', 190, AMARILLO, 1.0, f='sansx', glow=0.6)
        else:
            xc, yc, _ = fr.cam.p1((-1.7 - 0.9 * ks, 1.9, 0))
            xt, yt, _ = fr.cam.p1((0.9, 1.9, 0))
            pill(img, fx, xc, yc - 30, 'TRÁILER = LA CAJA', eout(seg(u, UG + 0.5, UG + 0.75)), size=30, border=AMARILLO)
            pill(img, fx, xt + 40, yt - 110, 'EL TRACTO', eout(seg(u, UG + 0.7, UG + 0.95)), size=30, border=VERDE)
            kicker(img, 'TRACTOCAMIÓN + SEMIRREMOLQUE', 140, seg(u, UG, UG + 0.3), col=AZULC)
            P.titulo_golpe(img, fx, [('Tu tráiler no es el tráiler…', 'sans'), ('es el que lo jala.', 'serif')], 190, seg(u, UG, UG + 0.15), size=64)
    fr.ui.append(ui)
    return finish(fr, fi)


# 0. gancho, inicio 11 (pregunta directa): «¿LE DICES TRÁILER?» sobre el tractocamión se rompe; la caja se suelta
def s_gancho(t, fi, u, d):
    k = seg(u, UG - 0.12, UG + 0.26)
    if u < UG - 0.12:
        img = _gancho_frame(t, fi, u, True)
    elif k < 1:
        img = M.tr_rompe(_gancho_frame(t, fi, u, True), _gancho_frame(t, fi, u, False), k, 0.5, 0.42)
    else:
        img = _gancho_frame(t, fi, u, False)
    return sacudir(img, t, golpe_k(u, UG + 0.15, 0.35), amp=22)


# 1. tráiler, en inglés, es la caja (la caja sola gira; ficha de diccionario)
def s_caja(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.6, 60, 18, tx=-1.7, ty=0.9), K(0.3, 6.0, 30, 12, tx=-1.7, ty=0.9), K(5, 5.9, 24, 12, tx=-1.7, ty=0.9)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.15, 0.3, 'desliza')
    draw_objects(fr, P.tfk(caja(), t=(-e['dy'] * 0.5, 0, 0)))

    def ui(img, fx):
        d_ = ImageDraw.Draw(img)
        k = eout(seg(u, 0.2, 0.5))
        if k > 0:
            y0 = 360 - 40 * (1 - k)
            d_.rounded_rectangle((150, y0, 930, y0 + 300), radius=26, fill=(14, 15, 18), outline=M.scale_c(AMARILLO, k), width=4)
            texto(img, fx, 200, y0 + 70, 'trailer', 70, M.scale_c(WHITE, k), 1.0, f='serif', glow=0.0, anchor='lm')
            texto(img, fx, 560, y0 + 75, '(inglés)', 34, GRIS, k, f='mono', glow=0.0, anchor='lm')
            texto(img, fx, 200, y0 + 190, '= remolque: la caja', 56, AMARILLO, k, f='sansx', glow=0.4, anchor='lm')
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. lo que manejas es el tractocamión: el tracto (el tracto solo da vuelta y frena de golpe)
def s_tracto(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, -70, 14, tx=0.8, ty=0.8), K(0.35, 4.0, -24, 10, tx=0.8, ty=0.8), K(5, 3.95, -18, 10, tx=0.8, ty=0.8)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'TRACTO', u, t0=Wp(2, 'tracto', 1) - 0.25, cy=0.33, entrada='sube')
    e = P.entrada(u, -0.2, 0.35, 'gira')
    draw_objects(fr, P.tfk(tracto(), ry=math.degrees(e['giro']) * 0.25, t=(0.8, 0, 0)))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((1.3, 1.6, 0))
        pill(img, fx, x, y - 60, 'TRACTOCAMIÓN', eout(seg(u, Wp(2, 'tractocamion') - 0.05, Wp(2, 'tractocamion') + 0.2)), size=34, border=VERDE)
        esquema(img, fx, 1.0, y=1440, txt='ESQUEMA SIN MARCA')
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. la norma mexicana le dice semirremolque (la ficha de la NOM-012 cae y se subraya la palabra)
def s_norma(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 20, 30, tx=-1.0, ty=0.6), K(0.3, 6.8, 4, 22, tx=-1.0, ty=0.6), K(5, 6.9, 0, 22, tx=-1.0, ty=0.6)], cy=0.7))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.3)
    draw_objects(fr, tracto() + caja())
    us = Wp(3, 'semirremolque') - 0.05

    def ui(img, fx):
        d_ = ImageDraw.Draw(img)
        k = P.eout4(seg(u, -0.2, 0.15))
        y0 = 330 - 300 * (1 - k)
        d_.rounded_rectangle((110, y0, 970, y0 + 520), radius=20, fill=(240, 238, 232), outline=(200, 198, 190), width=3)
        texto(img, None, 160, y0 + 60, 'NOM-012-SCT-2-2017', 36, (60, 60, 66), 1.0, f='mono', glow=0, anchor='lm')
        texto(img, None, 160, y0 + 110, 'DOF · 26-dic-2017 · 4.28', 26, (110, 110, 116), 1.0, f='mono', glow=0, anchor='lm')
        texto(img, None, 160, y0 + 210, 'Semirremolque:', 62, (20, 20, 24), 1.0, f='sansx', glow=0, anchor='lm')
        for j, ln in enumerate(['«Vehículo sin eje delantero,', 'destinado a ser acoplado a un', 'tractocamión… y parte de su peso', 'sea soportado por éste.»']):
            texto(img, None, 160, y0 + 290 + j * 52, ln, 34, (40, 40, 46), 1.0, f='serif', glow=0, anchor='lm')
        ku = seg(u, us, us + 0.4)
        if ku > 0:
            d_.line([(160, y0 + 250), (160 + 470 * ku, y0 + 250)], fill=ROJO, width=7)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.25), amp=12)


# 4. no tiene eje adelante y se recarga en el tracto (la caja sola sobre sus patas: círculo donde «faltan» llantas; baja al tracto)
def s_sineje(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.6, -8, 8, tx=-0.4, ty=0.8), K(0.3, 7.8, 4, 6, tx=-0.4, ty=0.8), K(5, 7.7, 6, 6, tx=-0.4, ty=0.8)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    ur = Wp(4, 'recarga') - 0.1
    k = P.eout4(seg(u, ur, ur + 0.6))
    ms = P.tfk(tracto(), t=(2.6 - 2.6 * k, 0, 0)) + P.tfk(caja(patas=k < 0.95), t=(0, 0.05 * (1 - k), 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-0.2, 0.2, 0.47))
        if u < ur + 0.2:
            doodle_circle(img, fx, x, y, 110, 80, t, k=seg(u, 0.2, 0.6), col=ROJO, seed=3)
            pill(img, fx, x, y - 170, 'SIN EJE ADELANTE', eout(seg(u, 0.3, 0.6)), size=30, border=ROJO)
        xp, yp, _ = fr.cam.p1((0, 0.46, 0))
        flecha(img, fx, xp, yp - 260, xp, yp - 40, AMARILLO, k=seg(u, ur + 0.3, ur + 0.6), w=8)
        pill(img, fx, 540, 1360, 'SE RECARGA EN EL TRACTO', eout(seg(u, ur + 0.5, ur + 0.8)), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ur + 0.6, 0.25), amp=12)


# 5. se engancha en la quinta rueda (crash zoom al plato con grasa; «QUINTA» de cristal)
def s_quinta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.4, -150, 40, tx=0.0, ty=0.5), K(0.3, 3.0, -118, 50, tx=-0.2, ty=0.45), K(5, 2.95, -112, 50, tx=-0.2, ty=0.45)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'QUINTA', u, t0=0.0, cy=0.3, entrada='golpe')
    draw_objects(fr, tracto())

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0, 0.46, 0))
        doodle_circle(img, fx, x, y, 210, 120, t, k=seg(u, 0.4, 0.8), col=AMARILLO, seed=5)
        pill(img, fx, x, y + 200, 'QUINTA RUEDA', eout(seg(u, 0.3, 0.6)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. un plato con grasa donde se traba el perno rey (el perno baja a la ranura y las quijadas cierran: clic; foto real)
def s_perno(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 40, 26, tx=-0.1, ty=0.5), K(0.3, 3.8, 18, 30, tx=-0.1, ty=0.5), K(5, 3.75, 14, 30, tx=-0.1, ty=0.5)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    ut = Wp(6, 'traba') - 0.1
    k = P.eout4(seg(u, ut - 0.5, ut))
    ms = tracto() + P.tfk(caja(patas=False), t=(-0.0 - 0.6 * (1 - k), 0.25 * (1 - k), 0))
    draw_objects(fr, ms, xray=0.25 + 0.75 * P.eout4(seg(u, -0.2, 0.3)), keep=('quinta', 'perno'))
    up = Wp(6, 'donde') - 0.1
    ph = foto('caja_kingpin.jpg')

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0, 0.44, 0))
        if u > ut:
            texto(img, fx, x + 150, y - 40, 'CLIC', 60, AMARILLO, seg(u, ut, ut + 0.1), f='sansx', glow=0.6)
        pill(img, fx, x - 220, y + 150, 'GRASA', eout(seg(u, 0.2, 0.45)), size=28, border=(200, 180, 120))
        if ph is not None:
            M.photo_card(img, fx, ph, 540, 560, 520, up + 0.1, u, caption='PERNO REY · FOTO: STERKEBAK · CC BY 3.0', angle0=-8)
        else:
            pill(img, fx, 540, 560, 'PERNO REY', eout(seg(u, up, up + 0.3)), size=40, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut, 0.25), amp=14)


# 7. ahí se apoya y gira, como una carretilla (la carretilla: la mitad la carga la llanta y la otra tus manos)
def carretilla(carga=1.0):
    ms = []
    ms.append(named(M3.box(1.0, 0.35, 0.7, (200, 60, 40), shadow=0, gloss=0.5).tf(rz=-8, t=(0, 0.55, 0)), 'bote', rim=0.7, gloss=0.5))
    ms.append(named(M3.box(0.9, 0.2, 0.6, (120, 100, 70), shadow=0, gloss=0.1).tf(rz=-8, t=(0, 0.82, 0)), 'carga', rim=0.3))
    for z in (-0.3, 0.3):
        ms.append(named(M3.box(1.7, 0.05, 0.05, (90, 92, 98), shadow=0, gloss=0.7).tf(rz=-8, t=(-0.25, 0.5, z)), 'mango', rim=0.7))
    ms.append(named(M3.cyl(0.25, 0.12, NEGRO, n=22, shadow=0, gloss=0.2, y0=-0.06).tf(rx=90, t=(0.65, 0.25, 0)), 'llanta', rim=0.4))
    return ms


def s_carretilla(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.2, 50, 14, ty=0.6, tx=-0.2), K(0.3, 4.4, 10, 8, ty=0.6, tx=-0.2), K(5, 4.35, 6, 8, ty=0.6, tx=-0.2)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    uc = Wp(7, 'como') - 0.1
    e = P.entrada(u, uc - 0.1, 0.3, 'cae')
    if u > uc - 0.1:
        draw_objects(fr, P.tfk(carretilla(), t=(0, max(0.0, -e['dy']) * 0.4, 0)))
    else:
        q, ph, th, _ = en(TRAY, 6.0 + 0.7 * u)
        draw_objects(fr, P.tfk(pose(tracto(), (0, 0), 0) + pose(caja(patas=False), (0, 0), 18 * math.sin(t * 2.5)), s=0.55, t=(0.5, 0, 0)))

    def ui(img, fx):
        if u > uc:
            xl, yl, _ = fr.cam.p1((0.65, 0.0, 0))
            xm, ym, _ = fr.cam.p1((-1.0, 0.4, 0))
            flecha(img, fx, xl, yl - 300, xl, yl - 20, AMARILLO, k=seg(u, uc + 0.3, uc + 0.6))
            flecha(img, fx, xm, ym - 300, xm, ym - 20, AMARILLO, k=seg(u, uc + 0.4, uc + 0.7))
            texto(img, fx, min(860, xl), yl - 350, 'LLANTA: MITAD', 34, AMARILLO, seg(u, uc + 0.5, uc + 0.8), f='mono', glow=0.3)
            texto(img, fx, max(220, xm), ym - 350, 'TÚ: MITAD', 34, AMARILLO, seg(u, uc + 0.6, uc + 0.9), f='mono', glow=0.3)
        else:
            pill(img, fx, 540, 1360, 'SE APOYA Y GIRA', eout(seg(u, 0.0, 0.3)), size=34, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.2, 0.25), amp=12)


# 8. el tracto carga parte del peso y por eso sus llantas agarran (flecha de peso sobre la quinta; llantas que brillan)
def s_peso(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.6, -20, 8, tx=-0.6, ty=0.9), K(0.3, 6.6, 8, 6, tx=-0.6, ty=0.9), K(5, 6.5, 12, 6, tx=-0.6, ty=0.9)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    TR.carretera(fr, t, vel=2.0, a=0.6)
    ms = tracto(giro=-t * 2.0 / 0.21) + caja(giro=-t * 2.0 / 0.21, patas=False)
    ua = Wp(8, 'agarran') - 0.1
    kg = seg(u, ua, ua + 0.3)
    for m in ms:
        if m.name == 'llanta' and m.V[:, 0].mean() < 0.4 and m.V[:, 0].mean() > -0.5:
            m.glow = M.scale_c(AMARILLO, 0.5 * kg)
    draw_objects(fr, ms)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((0, 0.5, 0))
        flecha(img, fx, x, y - 420, x, y - 30, AMARILLO, k=seg(u, 0.1, 0.5), w=12)
        texto(img, fx, x, y - 470, 'PESO', 50, AMARILLO, seg(u, 0.3, 0.6), f='mono', glow=0.4)
        xr, yr, _ = fr.cam.p1((0.0, 0.0, 0.5))
        pill(img, fx, xr + 60, yr + 140, '✓ AGARRAN', eout(seg(u, ua, ua + 0.3)), size=32, border=VERDE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9–10. la vuelta vista desde arriba: la huella del tracto (blanca) y la de la caja (roja) que corta por dentro
def _vuelta(t, fi, u, claves, s0, vel, huellas=True, rojo_k=0.0, cristal=None, cy=0.55):
    fr = Frame(camara(u, claves, cy=cy))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.2)
    if cristal:
        M.cristal(fr.base, fr.fx, cristal[0], u, t0=cristal[1], cy=0.24, entrada='zoom')
    calle(fr)
    s = s0 + vel * max(0.0, u)
    ms, i = rig(TRAY, s, giro=-s / 0.21)
    if huellas:
        huella(fr, TRAY, i, lambda q, ph, th: rueda_tracto(q, ph), WHITE, w=4, a=0.9)
        huella(fr, TRAY, i, lambda q, ph, th: rueda_caja(q, th), M.mixc(WHITE, ROJO, rojo_k), w=5 + 3 * rojo_k, a=1.0)
    draw_objects(fr, ms)
    return fr, s, i


def s_vuelta(t, fi, u, d):
    fr, s, i = _vuelta(t, fi, u, [K(-0.3, 9.0, -10, 50, tx=-1.4, ty=0.0, tz=0.6), K(0.35, 10.0, 0, 66, tx=-0.6, ty=0.0, tz=1.0),
                                  K(5, 10.1, 2, 66, tx=-0.6, ty=0.0, tz=1.0)], 5.0, 1.5, rojo_k=seg(u, 1.2, 1.8))

    def ui(img, fx):
        pill(img, fx, 300, 1380, '— TRACTO', 1.0, size=26, border=WHITE, dot=False)
        pill(img, fx, 760, 1380, '— CAJA', 1.0, size=26, border=ROJO, dot=False)
        esquema(img, fx, 1.0, y=1450, txt='VISTA DESDE ARRIBA · ESQUEMA')
    fr.ui.append(ui)
    return finish(fr, fi)


def s_corta(t, fi, u, d):
    fr, s, i = _vuelta(t, fi, u, [K(-0.3, 8.6, 20, 70, tx=XK + 0.5, ty=0.0, tz=ZK - 0.5), K(0.3, 6.6, 10, 74, tx=XK + 0.8, ty=0.0, tz=ZK - 0.3),
                                  K(5, 6.5, 8, 74, tx=XK + 0.8, ty=0.0, tz=ZK - 0.3)], 5.0 + 1.5 * 2.6, 1.3, rojo_k=1.0,
                       cristal=('DENTRO', 0.0))

    def ui(img, fx):
        q, ph, th, _ = en(TRAY, s)
        p = rueda_caja(q, th)
        x, y, _ = fr.cam.p1((p[0], 0.02, p[1]))
        doodle_circle(img, fx, x, y, 120, 120, t, k=seg(u, 0.3, 0.7), col=ROJO, seed=8)
        pill(img, fx, 540, 1380, 'LA CAJA CORTA LA CURVA', eout(seg(u, 0.3, 0.6)), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. y aquí está el error (el tráiler dando vuelta en rojo, alarma)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, -60, 20, tx=-1.0, ty=0.8), K(0.3, 8.0, -40, 16, tx=-1.0, ty=0.8), K(5, 8.1, -38, 16, tx=-1.0, ty=0.8)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.3)
    draw_objects(fr, tracto(direccional=1.0 if int(t * 3) % 2 == 0 else 0.0) + P.tfk(caja(patas=False), ry=12, t=(0, 0, 0)))
    rojo = 0.5 + 0.5 * math.sin(t * 14)

    def ui(img, fx):
        ImageDraw.Draw(fx).rectangle((0, 0, 1080, 1920), outline=M.scale_c(ROJO, 0.6 * rojo), width=40)
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 300, seg(u, 0.0, 0.15), size=110, col=(255, 110, 100))
        kicker(img, 'EN LA VUELTA A LA DERECHA', 240, seg(u, 0.15, 0.4), col=(255, 140, 130))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.35), amp=22)


# 12. meterte por la derecha cuando el tráiler da vuelta (vista de atrás: el carrito azul se mete por la derecha)
def s_derecha(t, fi, u, d):
    s = 4.6 + 0.9 * max(0.0, u)
    q, ph, th, i = en(TRAY, s)
    fr = Frame(camara(u, [K(-0.3, 6.0, -40, 26, tx=q[0] - 1.6, ty=0.5, tz=0.6), K(0.35, 6.4, -62, 20, tx=q[0] - 1.2, ty=0.5, tz=0.6),
                          K(5, 6.45, -64, 20, tx=q[0] - 1.2, ty=0.5, tz=0.6)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.3)
    calle(fr)
    ms, _ = rig(TRAY, s, giro=-s / 0.21, direccional=1.0 if int(t * 3) % 2 == 0 else 0.0)
    xc = q[0] - 4.0 + 2.2 * P.eout4(seg(u, 0.2, 1.6))
    draw_objects(fr, ms + carro_mini(p=(xc, ZK - 0.32), giro=-t * 8))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((xc, 0.6, ZK - 0.32))
        pill(img, fx, x, y - 90, 'TÚ', eout(seg(u, 0.2, 0.5)), size=32, border=CYAN)
        xd, yd, _ = fr.cam.p1((q[0] + 1.9, 0.45, q[1] + 0.47))
        texto(img, fx, 540, 380, '➜ DERECHA', 60, AMBAR, seg(u, 0.4, 0.6), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13–15. desde arriba: abre a la izquierda, el hueco parece libre y la caja se cierra sobre el carro
def _arriba(t, fi, u, s, car_x, claves, rojo=0.0, hueco=0.0, cristal=None):
    fr = Frame(camara(u, claves, cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.2)
    if cristal:
        M.cristal(fr.base, fr.fx, cristal[0], u, t0=cristal[1], cy=0.24, entrada=cristal[2])
    calle(fr)
    ms, i = rig(TRAY, s, giro=-s / 0.21, direccional=1.0 if int(t * 3) % 2 == 0 else 0.0)
    huella(fr, TRAY, i, lambda q, ph, th: rueda_caja(q, th), ROJO, w=4, a=0.8)
    if hueco > 0.01:
        q, ph, th, _ = en(TRAY, s)
        a = rueda_caja(q, th, lado=0.5)
        b = rueda_tracto(q, ph, lado=0.5)
        pts = [(a[0], 0.02, a[1]), (b[0], 0.02, b[1]), (b[0], 0.02, ZK - 0.05), (a[0], 0.02, ZK - 0.05), (a[0], 0.02, a[1])]
        line3(fr, pts, col=CYAN, w=3, a=hueco, glow=0.9)
    col = M.mixc((60, 110, 190), (230, 40, 40), rojo)
    draw_objects(fr, ms + carro_mini(col=col, p=(car_x, ZK - 0.33), giro=-t * 6))
    return fr


def s_abre(t, fi, u, d):
    s = 4.4 + 1.1 * max(0.0, u)
    fr = _arriba(t, fi, u, s, -6.0 + 0.6 * max(0.0, u), [K(-0.3, 11.0, -20, 58, tx=-3.0, ty=0.0, tz=0.8), K(0.3, 9.2, 0, 72, tx=-2.4, ty=0.0, tz=0.6),
                                                     K(5, 9.1, 2, 72, tx=-2.4, ty=0.0, tz=0.6)])
    q, ph, th, _ = en(TRAY, s)

    def ui(img, fx):
        x, y, _ = fr.cam.p1((q[0] + 1.6, 0.5, q[1]))
        flecha(img, fx, x, y + 40, x, y - 200, AMARILLO, k=seg(u, 0.3, 0.7), w=10)
        texto(img, fx, x, y - 250, 'ABRE', 50, AMARILLO, seg(u, 0.5, 0.8), f='mono', glow=0.4)
        esquema(img, fx, 1.0, y=1450, txt='VISTA DESDE ARRIBA · ESQUEMA')
    fr.ui.append(ui)
    return finish(fr, fi)


def s_hueco(t, fi, u, d):
    s = 4.4 + 1.1 * (d + 0.3) + 0.5 * max(0.0, u)
    fr = _arriba(t, fi, u, s, -5.0 + 0.8 * max(0.0, u), [K(-0.3, 7.6, 30, 66, tx=-1.8, ty=0.0, tz=1.0), K(0.3, 6.8, 10, 76, tx=-1.8, ty=0.0, tz=1.0),
                                                     K(5, 6.75, 8, 76, tx=-1.8, ty=0.0, tz=1.0)], hueco=seg(u, 0.1, 0.4),
                 cristal=('¿LIBRE?', 0.05, 'golpe'))

    def ui(img, fx):
        pill(img, fx, 540, 1380, 'PARECE LIBRE…', eout(seg(u, 0.3, 0.6)), size=34, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_cierra(t, fi, u, d):
    s = 7.2 + 1.6 * max(0.0, u)
    car_x = XK - 1.4
    q, ph, th, _ = en(TRAY, s)
    p = rueda_caja(q, th)
    choque = p[1] > ZK - 0.62 and abs(p[0] - car_x) < 1.2
    uc = Wp(15, 'cierra') - 0.05
    fr = _arriba(t, fi, u, s, car_x, [K(-0.3, 6.0, 40, 64, tx=XK - 1.0, ty=0.0, tz=ZK - 0.6), K(0.3, 5.2, 20, 76, tx=XK - 1.0, ty=0.0, tz=ZK - 0.6),
                                     K(5, 5.15, 18, 76, tx=XK - 1.0, ty=0.0, tz=ZK - 0.6)], rojo=seg(u, uc, uc + 0.3))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((car_x, 0.3, ZK - 0.33))
        if u > uc:
            doodle_circle(img, fx, x, y, 140, 110, t, k=seg(u, uc, uc + 0.3), col=ROJO, seed=12)
            texto(img, fx, x, y - 190, '¡SE CIERRA!', 54, ROJO, seg(u, uc, uc + 0.15), f='sansx', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.4), amp=24)


# 16. y ahí casi no te ve (zona ciega roja al lado derecho del tráiler; «CIEGO» de cristal)
def s_nove(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 8.0, 10, 50, tx=-1.2, ty=0.0, tz=0.6), K(0.3, 7.0, 0, 64, tx=-1.2, ty=0.0, tz=0.6), K(5, 6.95, -2, 64, tx=-1.2, ty=0.0, tz=0.6)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.2)
    M.cristal(fr.base, fr.fx, 'CIEGO', u, t0=-0.05, cy=0.24, entrada='sube')
    ms = tracto() + caja(patas=False) + carro_mini(p=(-1.6, 1.05))
    draw_objects(fr, ms)
    kz = seg(u, 0.2, 0.6)
    zona = [(1.3, 0.02, 0.5), (-3.8, 0.02, 0.5), (-3.8, 0.02, 1.8), (1.3, 0.02, 1.8), (1.3, 0.02, 0.5)]

    def ui(img, fx):
        pts = [fr.cam.p1(p)[:2] for p in zona]
        a = 0.5 + 0.3 * math.sin(t * 8)
        ImageDraw.Draw(fx).polygon(pts[:-1], fill=M.scale_c(ROJO, 0.35 * kz * a))
        ImageDraw.Draw(img).line(pts, fill=M.scale_c(ROJO, kz), width=4)
        x, y, _ = fr.cam.p1((-1.2, 0.02, 1.6))
        pill(img, fx, x, y + 70, 'ZONA CIEGA', eout(seg(u, 0.4, 0.7)), size=30, border=ROJO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17–18. el espejo: si no ves su cara en el espejo, él tampoco te ve a ti (sin personas: el ojo de line-art)
_ESP = {}


def reflejo(con_carro=False):
    if con_carro not in _ESP:
        im = Image.new('RGBA', (300, 520), (18, 22, 30, 255))
        d = ImageDraw.Draw(im)
        for j in range(6):
            d.line([(40 + j * 30, 520), (150, 160)], fill=(80, 90, 104), width=3)
        d.rectangle((0, 0, 300, 150), fill=(30, 40, 56))
        if con_carro:
            d.rounded_rectangle((110, 300, 220, 380), radius=12, fill=(60, 110, 190))
        _ESP[con_carro] = im
    return _ESP[con_carro]


def espejo(con_carro=False):
    ms = []
    caja_e = M3.box(0.32, 0.56, 0.1, (40, 42, 48), shadow=0, gloss=0.6)
    ms.append(named(caja_e.tf(t=(0, 0.72, 0)), 'carcasa', rim=0.8, gloss=0.6))
    vidrio = M3.box(0.28, 0.5, 0.02, (60, 70, 86), shadow=0, gloss=0.95)
    M3.decal(vidrio, vidrio.FACE['front'], reflejo(con_carro))
    ms.append(named(vidrio.tf(t=(0, 0.75, 0.055)), 'vidrio', rim=0.9, gloss=0.95))
    ms.append(named(M3.box(0.6, 0.04, 0.04, CROMO, shadow=0, gloss=0.95).tf(t=(-0.4, 1.0, -0.02)), 'brazo', rim=0.9))
    ms.append(named(M3.box(0.6, 0.04, 0.04, CROMO, shadow=0, gloss=0.95).tf(t=(-0.4, 0.75, -0.02)), 'brazo', rim=0.9))
    return ms


def ojo(img, fx, x, y, k=1.0, tachado=0.0, col=WHITE):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    w, h = 150 * k, 70 * k
    d.arc((x - w, y - h * 1.6, x + w, y + h * 1.6), 210, 330, fill=col, width=7)
    d.arc((x - w, y - h * 1.6, x + w, y + h * 1.6), 30, 150, fill=col, width=7)
    d.ellipse((x - 36 * k, y - 36 * k, x + 36 * k, y + 36 * k), outline=col, width=7)
    df.ellipse((x - 50 * k, y - 50 * k, x + 50 * k, y + 50 * k), fill=M.scale_c(col, 0.3))
    if tachado > 0.01:
        L = 190 * tachado
        d.line([(x - 150, y + 110), (x - 150 + L * 1.58, y + 110 - L * 1.16)], fill=ROJO, width=12)
        df.line([(x - 150, y + 110), (x - 150 + L * 1.58, y + 110 - L * 1.16)], fill=M.scale_c(ROJO, 0.6), width=26)


def s_espejo(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.6, 50, 10, ty=0.75), K(0.3, 1.9, 14, 6, ty=0.75), K(5, 1.85, 10, 6, ty=0.75)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'pop')
    draw_objects(fr, P.tfk(espejo(), s=max(0.05, e['escala']) * 1.6, t=(0, -0.4, 0)))

    def ui(img, fx):
        kicker(img, 'REGLA DE ORO', 150, 1.0, col=AMARILLO)
        texto(img, fx, 540, 300, '¿VES AL CHOFER EN SU ESPEJO?', 44, WHITE, seg(u, 0.2, 0.5), f='sansx', glow=0.3)
        ojo(img, fx, 540, 470, k=eout(seg(u, 0.3, 0.6)))
        esquema(img, fx, 1.0, y=1440, txt='FMCSA (EE. UU.)')
    fr.ui.append(ui)
    return finish(fr, fi)


def s_teve(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 1.9, -30, 6, ty=0.75), K(0.3, 2.3, -10, 6, ty=0.75), K(5, 2.35, -8, 6, ty=0.75)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    draw_objects(fr, P.tfk(espejo(con_carro=False), s=1.6, t=(0, -0.4, 0)))
    ut = Wp(18, 'tampoco') - 0.1

    def ui(img, fx):
        ojo(img, fx, 540, 470, k=1.0, tachado=P.eout4(seg(u, ut, ut + 0.3)))
        P.titulo_golpe(img, fx, [('Él tampoco te ve.', 'sans')], 250, seg(u, ut + 0.1, ut + 0.25), size=70, col=(255, 120, 110))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut + 0.25, 0.3), amp=14)


# 19. con la direccional prendida, nunca te metas entre el tráiler y la banqueta (la direccional parpadea; ✗ en el hueco)
def s_direccional(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.4, 80, 22, tx=-0.6, ty=0.5, tz=0.8), K(0.3, 5.4, 52, 18, tx=-0.6, ty=0.5, tz=0.8),
                          K(5, 5.35, 48, 18, tx=-0.6, ty=0.5, tz=0.8)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.3)
    on = 1.0 if int(t * 3) % 2 == 0 else 0.0
    draw_objects(fr, tracto(direccional=on) + P.tfk(caja(patas=False), ry=10))
    line3(fr, [(-4, 0.02, 1.4), (3, 0.02, 1.4)], col=WHITE, w=4, a=0.9, glow=0.6)   # banqueta
    un = Wp(19, 'nunca') - 0.1

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-0.6, 0.3, 1.0))
        if u > un:
            texto(img, fx, x, y, '✗', int(160 + 100 * (1 - P.eout4(seg(u, un, un + 0.15)))), ROJO, seg(u, un, un + 0.15), f='sansx', glow=0.7)
        pill(img, fx, x, y + 170, 'NUNCA AQUÍ', eout(seg(u, un + 0.1, un + 0.4)), size=34, border=ROJO)
        xb, yb, _ = fr.cam.p1((1.5, 0.02, 1.4))
        pill(img, fx, xb, yb + 60, 'BANQUETA', 1.0, size=24, border=GRIS, dot=False)
        kicker(img, 'DIRECCIONAL PRENDIDA', 150, 1.0, col=AMBAR)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.15, 0.3), amp=16)


# 20. y entre más larga la caja, más corta la curva (dos huellas: caja corta contra caja larga)
def s_larga(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 9.6, -20, 60, tx=XK + 0.6, ty=0.0, tz=1.6), K(0.3, 9.0, 0, 74, tx=XK + 0.6, ty=0.0, tz=1.6),
                          K(5, 8.95, 2, 74, tx=XK + 0.6, ty=0.0, tz=1.6)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.2)
    M.cristal(fr.base, fr.fx, 'LARGA', u, t0=0.0, cy=0.22, entrada='golpe')
    calle(fr)
    kk = ease(seg(u, 0.1, d - 0.3))
    S = len(TRAY[0]) - 1
    i = int(S * (0.35 + 0.6 * kk))
    huella(fr, TRAY_C, i, lambda q, ph, th: rueda_caja(q, th, L=1.9), VERDE, w=5, a=1.0)
    huella(fr, TRAY, i, lambda q, ph, th: rueda_caja(q, th), ROJO, w=5, a=1.0)
    huella(fr, TRAY, i, lambda q, ph, th: rueda_tracto(q, ph), WHITE, w=3, a=0.7)

    def ui(img, fx):
        pill(img, fx, 300, 1380, '— CAJA CORTA', 1.0, size=26, border=VERDE, dot=False)
        pill(img, fx, 770, 1380, '— CAJA LARGA', 1.0, size=26, border=ROJO, dot=False)
        esquema(img, fx, 1.0, y=1450, txt='HUELLA DE LAS LLANTAS DE ATRÁS · ESQUEMA')
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. un tracto con caja mide hasta 23 metros (vista de lado con cota; «23 m» golpea)
def cota(fr, x0, x1, y, z, k, col=CYAN):
    if k <= 0.01:
        return
    xm = x0 + (x1 - x0) * k
    line3(fr, [(x0, y, z), (xm, y, z)], col=col, w=3, a=1.0, glow=0.8)
    line3(fr, [(x0, y - 0.15, z), (x0, y + 0.15, z)], col=col, w=3, a=1.0, glow=0.8)
    if k > 0.98:
        line3(fr, [(x1, y - 0.15, z), (x1, y + 0.15, z)], col=col, w=3, a=1.0, glow=0.8)


def s_23(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 9.0, 30, 10, tx=-0.9, ty=0.9), K(0.3, 8.2, 2, 4, tx=-0.9, ty=0.9), K(5, 8.15, 0, 4, tx=-0.9, ty=0.9)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    e = P.entrada(u, -0.2, 0.3, 'desliza')
    draw_objects(fr, P.tfk(tracto() + caja(patas=False), t=(-e['dy'], 0, 0)))
    u2 = Wp(21, 'veintitres') - 0.1
    cota(fr, -3.7, 2.15, 2.2, 0.5, P.eout4(seg(u, u2 - 0.4, u2)))

    def ui(img, fx):
        if u > u2:
            P.numero_golpe(img, fx, '23 m', 560, seg(u, u2, u2 + 0.18), size=220, col=CYAN)
        texto(img, fx, 540, 1420, 'LARGO MÁXIMO · NOM-012-SCT-2-2017', 24, GRIS, 1.0, f='mono', glow=0.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u2 + 0.18, 0.3), amp=16)


# 22. y un full, con dos cajas, hasta 31 (el full se arma: dolly y segunda caja; «31 M» de cristal)
def dolly(giro=0.0):
    ms = []
    B_(ms, 1.0, 0.1, 0.5, (40, 40, 44), -0.2, 0.34, 0, gloss=0.2)
    B_(ms, 0.9, 0.04, 0.06, (90, 92, 98), 0.55, 0.3, 0, gloss=0.5)                  # lanza
    ms.append(named(M3.cyl(0.26, 0.05, GRASA, n=24, shadow=0, gloss=0.95).tf(t=(0, 0.41, 0)), 'quinta', rim=0.8))
    for x in (-0.15, -0.6):
        for z in (-0.38, 0.38):
            LL(ms, x, z, giro=giro)
    return ms


def full(k=1.0):
    ms = tracto() + caja(largo=3.0, patas=False)
    off = -3.0 - 0.55 - 0.6 * (1 - k)
    ms += P.tfk(dolly(), t=(off + 0.2, 0, 0))
    ms += P.tfk(caja(largo=3.0, patas=False), t=(off + 0.2 - 0.0, 0, 0)) if k > 0.0 else []
    return ms


def s_31(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 10.0, -26, 8, tx=-2.0, ty=0.9), K(0.3, 11.0, -2, 4, tx=-2.0, ty=0.9), K(5, 11.05, 0, 4, tx=-2.0, ty=0.9)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, '31 M', u, t0=Wp(22, 'treinta') - 0.2, cy=0.27, entrada='zoom')
    kf = P.eout4(seg(u, -0.1, 0.4))
    draw_objects(fr, full(kf))
    cota(fr, -6.25, 2.15, 2.2, 0.5, P.eout4(seg(u, 0.3, 0.9)))

    def ui(img, fx):
        x, y, _ = fr.cam.p1((-4.0, 1.9, 0))
        pill(img, fx, x, y - 50, '2.ª CAJA', eout(seg(u, 0.2, 0.5)), size=26, border=AMARILLO)
        xd, yd, _ = fr.cam.p1((-3.3, 0.2, 0.5))
        pill(img, fx, xd, yd + 70, 'DOLLY', eout(seg(u, 0.4, 0.7)), size=24, border=GRIS)
        texto(img, fx, 540, 1420, 'FULL (DOBLEMENTE ARTICULADO) · NOM-012', 24, GRIS, 1.0, f='mono', glow=0.0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. como un edificio de 10 pisos acostado (el full se para y se vuelve un edificio de 10 pisos)
def s_edificio(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 11.0, 0, 6, tx=-2.0, ty=1.0), K(0.4, 12.5, 14, 6, tx=0.0, ty=4.0), K(5, 12.6, 16, 6, tx=0.0, ty=4.0)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    kr = P.eout4(seg(u, 0.0, 0.6))
    ms = P.tfk(full(1.0), t=(4.1, 0, 0))                     # el frente en x≈6.25 → gira sobre la orilla de atrás
    ms = P.tfk(ms, rz=90 * kr, t=(-2.15 + 0.0, 0, 0))
    draw_objects(fr, ms)
    kb = seg(u, 0.5, 0.9)
    H = 8.4
    for j in range(11):
        y = H * j / 10
        line3(fr, [(-1.0, y, -0.6), (-1.0, y, 0.6)], col=WHITE, w=2, a=0.0, glow=0.0)
    xb = 1.4

    def ui(img, fx):
        for j in range(11):
            y3 = H * j / 10
            x0, y0, _ = fr.cam.p1((xb, y3, 0))
            x1, y1, _ = fr.cam.p1((xb + 2.2, y3, 0))
            ImageDraw.Draw(img).line([(x0, y0), (x1, y1)], fill=M.scale_c(WHITE, 0.8 * kb), width=3)
            ImageDraw.Draw(fx).line([(x0, y0), (x1, y1)], fill=M.scale_c(CYAN, 0.4 * kb), width=8)
            if j < 10:
                texto(img, fx, x1 + 50, (y0 + y1) / 2 - 22, str(j + 1), 30, CYAN, kb, f='mono', glow=0.3)
        xa, ya, _ = fr.cam.p1((xb, 0, 0))
        xc, yc, _ = fr.cam.p1((xb, H, 0))
        ImageDraw.Draw(img).line([(xa, ya), (xc, yc)], fill=M.scale_c(WHITE, 0.8 * kb), width=3)
        xd, yd, _ = fr.cam.p1((xb + 2.2, 0, 0))
        xe, ye, _ = fr.cam.p1((xb + 2.2, H, 0))
        ImageDraw.Draw(img).line([(xd, yd), (xe, ye)], fill=M.scale_c(WHITE, 0.8 * kb), width=3)
        pill(img, fx, 540, 1380, '10 PISOS ≈ 31 M', eout(seg(u, 0.8, 1.1)), size=34, border=CYAN, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.6, 0.3), amp=14)


# 24. mándaselo a quien se mete por la derecha cuando el tráiler da vuelta
def s_compa(t, fi, u, d):
    s = 6.0 + 1.2 * max(0.0, u)
    fr = _arriba(t, fi, u, s, XK - 2.2, [K(-0.3, 9.0, -10, 60, tx=-1.6, ty=0.0, tz=1.0), K(0.3, 8.0, 6, 70, tx=-1.6, ty=0.0, tz=1.0),
                                       K(5, 7.95, 8, 70, tx=-1.6, ty=0.0, tz=1.0)])

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien se mete', 'sans'), ('por la derecha en la vuelta.', 'serif')], 230, seg(u, 0.05, 0.2), size=62)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-2.6, 'whoosh_suave', 0.4), (UG - 0.12, 'vidrio', 1.0), (UG, 'sub', 0.9), (UG + 0.15, 'bass', 0.8), (UG + 0.4, 'whoosh', 0.6)]),
           dict(desde=1, fn=s_caja, tr='cubo', sfx=[(0.2, 'slap', 0.7)]),
           dict(desde=2, fn=s_tracto, tr='whip_izq', sfx=[(0.0, 'whoosh', 0.6)]),
           dict(desde=3, fn=s_norma, tr='deslizar_abajo', sfx=[(0.15, 'slap', 0.9)]),
           dict(desde=4, fn=s_sineje, tr='giro', sfx=[(0.3, 'scribble', 0.5)]),
           dict(desde=5, fn=s_quinta, tr='zoom', c=(0.5, 0.6), sfx=[(0.4, 'scribble', 0.5)]),
           dict(desde=6, fn=s_perno, tr='whip', c=(0.5, 0.62), sfx=[]),
           dict(desde=7, fn=s_carretilla, tr='remolino', sfx=[]),
           dict(desde=8, fn=s_peso, tr='wipe', sfx=[(0.1, 'whoosh_suave', 0.5)]),
           dict(desde=9, fn=s_vuelta, tr='flash', sfx=[(1.2, 'tick', 0.4)]),
           dict(desde=10, fn=s_corta, tr='cristal', palabra='CURVA', sfx=[(0.3, 'scribble', 0.6)]),
           dict(desde=11, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.15, 'sub', 0.9), (0.2, 'bass', 0.7)]),
           dict(desde=12, fn=s_derecha, tr='deslizar', sfx=[(0.2, 'whoosh', 0.6)]),
           dict(desde=13, fn=s_abre, tr='push', c=(0.5, 0.5), sfx=[(0.3, 'whoosh_suave', 0.5)]),
           dict(desde=14, fn=s_hueco, tr='mosaico', sfx=[(0.2, 'shimmer', 0.4)]),
           dict(desde=15, fn=s_cierra, tr='golpe', sfx=[]),
           dict(desde=16, fn=s_nove, tr='glitch', sfx=[(0.3, 'tick', 0.4)]),
           dict(desde=17, fn=s_espejo, tr='cubo_izq', sfx=[(0.3, 'chime_a', 0.4)]),
           dict(desde=18, fn=s_teve, tr='whip', sfx=[]),
           dict(desde=19, fn=s_direccional, tr='rebanadas', sfx=[(0.1 + 0.66 * j, 'tick2', 0.4) for j in range(4)]),
           dict(desde=20, fn=s_larga, tr='zoom', c=(0.5, 0.5), sfx=[(0.5, 'whoosh_suave', 0.4)]),
           dict(desde=21, fn=s_23, tr='deslizar_abajo', sfx=[]),
           dict(desde=22, fn=s_31, tr='iris', c=(0.3, 0.55), sfx=[(0.3, 'click', 0.6)]),
           dict(desde=23, fn=s_edificio, tr='remolino', sfx=[(0.0, 'riser', 0.4), (0.6, 'thud', 1.0)]),
           dict(desde=24, fn=s_compa, tr='golpe', sfx=[(0.05, 'slap', 0.7)]),
           dict(desde=25, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    add = {2: [(Wp(2, 'tracto', 1) - 0.25, 'cristal', 0.6)], 3: [(Wp(3, 'semirremolque'), 'scribble', 0.6)],
           4: [(Wp(4, 'recarga') + 0.5, 'thud', 1.0)], 6: [(Wp(6, 'traba') - 0.1, 'click', 1.0), (Wp(6, 'donde') + 0.1, 'slap', 0.8)],
           7: [(Wp(7, 'como'), 'thud', 0.8)], 8: [(Wp(8, 'agarran') - 0.1, 'chime_b', 0.5)],
           15: [(Wp(15, 'cierra') - 0.05, 'burst', 0.9), (Wp(15, 'cierra') + 0.05, 'sub', 0.9)],
           18: [(Wp(18, 'tampoco') - 0.1, 'scribble', 0.6), (Wp(18, 'tampoco') + 0.15, 'bass', 0.7)],
           19: [(Wp(19, 'nunca') - 0.1, 'bass', 0.9)], 21: [(Wp(21, 'veintitres') - 0.1, 'bass', 0.9)],
           22: [(Wp(22, 'treinta') - 0.2, 'cristal', 0.6)]}
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
