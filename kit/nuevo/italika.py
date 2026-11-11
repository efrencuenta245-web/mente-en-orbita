"""Reel diario vie 13-nov-2026 18:00 — «Tu Italika no es… italiana.» (marca mexicana + motor de 4 tiempos + aceite).
Comunidad: motociclistas (decisión de Efrén del 10-nov: vehículos y comunidades mexicanas por dentro).
Inicio tipo 6 (pantalla dividida que choca): arriba la moto con las franjas verde-blanco-rojo de Italia y «¿ITALIANA?»,
abajo la misma moto con las de México; las dos mitades se estrellan, la de arriba se tacha y la de abajo se prende.
El final regresa a las mitades separadas (loop). Voz Isaac (eleven_v4), 68.9 s. Datos y fuentes:
guiones/2026-11-13_italika.txt. Fotos reales: motoneta Italika en Tulum (Nan Palmero, CC BY 2.0; logo difuminado)
y un motor de un cilindro y 4 tiempos en corte (CheminduCret, CC0; recortado sin letreros ni personas).
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
TEMA = 'italika'
TXT = ['Tu Italika no es… italiana.',
       'Es mexicana: nació en 2004 y es de Grupo Salinas, el de las tiendas Elektra.',
       'Se arma en Toluca, donde sale una moto nueva cada minuto.',
       'Y casi 7 de cada 10 motos que se venden en México son suyas.',
       'Mira por dentro: un cilindro y cuatro tiempos.',
       'Entra aire con gasolina, el pistón lo aprieta, la chispa lo explota y sale por el escape.',
       'A 8 500 vueltas por minuto, eso pasa unas 70 veces por segundo.',
       'Y el error que acaba con ese motor: no cambiarle el aceite a tiempo.',
       'El aceite es una capa delgadita entre el pistón y el cilindro.',
       'Viejo, se ensucia y se adelgaza: el metal roza contra metal, se calienta… y el motor se amarra.',
       'Italika pide cambiarlo en cada servicio: cada 3 000 a 6 000 km, según tu modelo.',
       'Eso sí: la mayoría de sus piezas llega de China… pero se arman aquí, con manos mexicanas.',
       'Y desde 2025 también en Jalisco: entre las dos plantas, más de un millón y medio de motos al año.',
       'Mándaselo a tu compa que dice que su Italika es italiana,',
       'porque su Italika no es… italiana.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-13_italika_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_italika.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-13_italika_words.json')
FOTOS = os.path.join(_REPO, 'inbox')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
VERDE_B = (0, 150, 70)
ROJO_B = (210, 30, 40)
ROJO_M = (196, 28, 32)
NEGRO = (22, 22, 26)
CROMO = (210, 212, 218)
ACEITE = (226, 160, 40)
GRIS = (150, 150, 160)


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
    """u de la palabra de la frase i que empieza con `palabra` (la n-ésima si se repite)."""
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


def tubo(p0, p1, r=0.03, col=CROMO, n=7, name='tubo'):
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
    return named(M3.Mesh(V, F, col, shadow=0, gloss=0.8, double=True), name, rim=0.8, gloss=0.8)


def _B(ms, sx, sy, sz, col, x, y, z, name='cuerpo', gloss=0.45, rim=0.6, glow=None, base=True):
    m = named(M3.box(sx, sy, sz, col, shadow=0, gloss=gloss, base=base).tf(t=(x, y, z)), name, rim=rim, gloss=gloss)
    if glow is not None:
        m.glow = glow
    ms.append(m)
    return m


# ------------------------------------------------------------------ la moto (de calle, 150 cc, sin marca; frente hacia +x)
def moto(giro=0.0, faro=0.6, col=ROJO_M, motor_glow=0.0):
    ms = []
    r = 0.34
    for x in (0.78, -0.72):
        ms.append(named(M3.cyl(r, 0.12, NEGRO, n=22, shadow=0, gloss=0.15).tf(rx=90, t=(x, r, -0.06)), 'llanta', rim=0.35))
        ms.append(named(M3.cyl(r * 0.62, 0.13, (60, 62, 68), n=14, shadow=0, gloss=0.8).tf(rx=90, t=(x, r, -0.065)),
                        'rin', rim=0.7))
        for j in range(3):
            a = giro + j * 2.1
            _B(ms, 0.05, 0.05, 0.15, CROMO, x + r * 0.45 * math.cos(a), r + r * 0.45 * math.sin(a), 0.0, name='rayo',
               base=False, gloss=0.9)
    ms.append(tubo((0.78, r, 0), (0.52, 1.02, 0), r=0.03, col=CROMO, name='horquilla'))        # horquilla
    ms.append(tubo((-0.72, r, 0.05), (-0.05, 0.55, 0.05), r=0.03, col=(60, 60, 66), name='basculante'))
    ms.append(tubo((-0.72, r, -0.05), (-0.05, 0.55, -0.05), r=0.03, col=(60, 60, 66), name='basculante'))
    ms.append(tubo((-0.45, 0.42, 0.1), (-0.3, 0.86, 0.1), r=0.04, col=ROJO_B, name='amortiguador'))
    ms.append(named(M3.rbox(0.6, 0.3, 0.34, 0.1, col, n=4, shadow=0, gloss=0.75).tf(t=(0.15, 0.8, 0)), 'cuerpo',
                    rim=0.7, gloss=0.75))                                                       # tanque
    ms.append(named(M3.rbox(0.36, 0.06, 0.16, 0.03, col, n=3, shadow=0, gloss=0.7).tf(t=(0.86, 0.66, 0)), 'cuerpo',
                    rim=0.6, gloss=0.7))                                                        # salpicadera
    ms.append(named(M3.rbox(0.66, 0.11, 0.28, 0.05, (30, 30, 34), n=3, shadow=0, gloss=0.2).tf(t=(-0.4, 0.9, 0)),
                    'cuerpo', rim=0.5, gloss=0.2))                                              # asiento
    _B(ms, 0.4, 0.14, 0.2, col, -0.78, 0.86, 0, gloss=0.7)                                       # colín
    _B(ms, 0.22, 0.26, 0.24, (40, 40, 44), 0.58, 0.95, 0, gloss=0.4)                             # faro (carcasa)
    _B(ms, 0.03, 0.12, 0.14, (255, 248, 230), 0.7, 1.0, 0, glow=M.scale_c((255, 240, 200), faro))
    ms.append(tubo((0.5, 1.22, -0.36), (0.5, 1.22, 0.36), r=0.022, col=CROMO, name='manubrio'))
    ms.append(tubo((0.52, 1.02, 0), (0.5, 1.22, 0), r=0.03, col=CROMO, name='horquilla'))
    # motor de un cilindro (rayos X: 'in')
    _B(ms, 0.42, 0.28, 0.26, (150, 154, 162), 0.05, 0.36, 0, name='in', gloss=0.6,
       glow=M.scale_c((255, 120, 50), motor_glow) if motor_glow > 0.01 else None)
    for j in range(5):
        _B(ms, 0.24, 0.025, 0.3, (170, 174, 182), 0.18, 0.64 + j * 0.045, 0, name='in', gloss=0.6)  # aletas del cilindro
    ms.append(tubo((0.28, 0.6, 0.12), (0.45, 0.25, 0.16), r=0.035, col=CROMO, name='escape'))
    ms.append(tubo((0.45, 0.25, 0.16), (-0.75, 0.42, 0.18), r=0.045, col=CROMO, name='escape'))
    return ms


# ------------------------------------------------------------------ fotos reales
_F = {}


def foto(nombre):
    if nombre in _F:
        return _F[nombre]
    if nombre == 'scooter':
        im = Image.open(os.path.join(FOTOS, 'italika_i_scooter1920.jpg')).convert('RGB')
        for box in ((1050, 830, 1290, 940), (1140, 975, 1260, 1060)):            # el logo, difuminado
            reg = im.crop(box).filter(ImageFilter.GaussianBlur(14))
            im.paste(reg, box[:2])
        im = im.crop((150, 300, 1650, 1250))
    else:
        im = Image.open(os.path.join(FOTOS, 'italika_i_corte1920.jpg')).convert('RGB')
        im = im.crop((230, 20, 1130, 900))                                       # solo el cilindro cortado
    _F[nombre] = im
    return im


# ------------------------------------------------------------------ el cilindro por dentro (corte)
R_CIL, Y_CAB = 0.62, 3.2


def ciclo(theta):
    """theta en grados (0-720). Devuelve (y del pistón, fase 0-3, apertura admisión, apertura escape)."""
    th = math.radians(theta)
    r, L = 0.62, 1.7
    yp = 0.6 + r * math.cos(th) + math.sqrt(L * L - (r * math.sin(th)) ** 2)   # 0 grados = arriba
    fase = int((theta % 720) // 180)
    a = theta % 720
    adm = math.sin(math.radians(a)) if a < 180 else 0.0
    esc = math.sin(math.radians(a - 540)) if a >= 540 else 0.0
    return yp, fase, max(0.0, adm), max(0.0, esc)


FASES = [('1 · ADMISIÓN', AZULC), ('2 · COMPRESIÓN', CYAN), ('3 · EXPLOSIÓN', NARANJA), ('4 · ESCAPE', GRIS)]


def cilindro(fr, t, theta, k=1.0, blur=0, aceite=None, roce=0.0):
    """Corte del cilindro: paredes de línea que brilla, pistón y biela de metal, válvulas, bujía y gases."""
    yp, fase, adm, esc = ciclo(theta)
    top = yp + 0.32
    q = np.linspace(0, 2 * math.pi, 40)
    for y in (1.6, Y_CAB + 0.75):
        line3(fr, [(R_CIL * math.cos(a), y, R_CIL * math.sin(a)) for a in q], col=WHITE, w=2.4, a=0.7 * k, glow=0.6)
    for x in (-R_CIL, R_CIL):
        line3(fr, [(x, 1.6, 0), (x, Y_CAB + 0.75, 0)], col=WHITE, w=3.0, a=0.95 * k, glow=0.8)
    # aletas de enfriamiento (por fuera)
    for j in range(7):
        y = 1.9 + j * 0.24
        for s in (-1, 1):
            line3(fr, [(s * R_CIL, y, 0), (s * (R_CIL + 0.32), y, 0)], col=(170, 174, 182), w=2.2, a=0.5 * k, glow=0.2)
    # cigüeñal y biela (línea)
    th = math.radians(theta)
    cz = (0.62 * math.sin(th), 0.6 + 0.62 * math.cos(th))
    line3(fr, [(0.62 * math.cos(a), 0.6 + 0.62 * math.sin(a), 0) for a in q], col=AMARILLO, w=2.4, a=0.7 * k, glow=0.7)
    line3(fr, [(cz[0], cz[1], 0.05), (0, yp, 0.05)], col=CROMO, w=6, a=0.95 * k, glow=0.3)
    # gases
    col_g = [AZULC, CYAN, NARANJA, GRIS][fase]
    rng = np.random.RandomState(4)
    n = 40
    for j in range(n):
        y = top + 0.05 + rng.rand() * (Y_CAB + 0.7 - top)
        x = (rng.rand() - 0.5) * 2 * (R_CIL - 0.08)
        x += 0.03 * math.sin(t * 17 + j)
        dot3(fr, (x, y, (rng.rand() - 0.5) * 0.4), r=3.6, col=col_g, a=0.85 * k, glow=1.0 if fase == 2 else 0.6)
    if fase == 2:                                                            # la chispa: flash naranja
        kk = clamp(1 - ((theta % 720) - 360) / 70)
        dot3(fr, (0, Y_CAB + 0.62, 0), r=12 + 40 * kk, col=(255, 230, 160), a=kk, glow=2.5)
    ms = [named(M3.cyl(R_CIL - 0.03, 0.32, (186, 190, 198), n=28, shadow=0, gloss=0.85).tf(t=(0, yp, 0)), 'piston',
                rim=0.85, gloss=0.85),
          named(M3.cyl(0.05, 0.4, (230, 232, 236), n=10, shadow=0, gloss=0.9).tf(t=(0, Y_CAB + 0.75, 0)), 'bujia', rim=0.9)]
    for s, ab, col in ((-1, adm, (90, 160, 230)), (1, esc, (200, 120, 70))):
        yv = Y_CAB + 0.7 - 0.22 * ab
        ms.append(named(M3.cyl(0.17, 0.05, col, n=16, shadow=0, gloss=0.8).tf(t=(s * 0.3, yv, 0)), 'valvula', rim=0.8))
        ms.append(named(M3.cyl(0.03, 0.7, CROMO, n=8, shadow=0, gloss=0.9).tf(t=(s * 0.3, yv + 0.05, 0)), 'valvula'))
    if aceite is not None:                                                   # la capa de aceite entre pistón y pared
        for s in (-1, 1):
            line3(fr, [(s * (R_CIL - 0.015), yp - 0.05, 0.02), (s * (R_CIL - 0.015), yp + 0.4, 0.02)], col=aceite,
                  w=5, a=0.95 * k, glow=0.9)
    draw_objects(fr, ms)
    if roce > 0.01:                                                          # chispas de metal contra metal
        for j in range(10):
            ph = (t * 3 + j / 10) % 1.0
            s = 1 if j % 2 else -1
            x0, y0 = s * R_CIL, yp + 0.15
            dot3(fr, (x0 - s * 0.4 * ph, y0 + 0.6 * ph * math.sin(j), 0.2), r=4, col=(255, 200, 120), a=roce * (1 - ph),
                 glow=2.0)
    return yp, fase


# ================================================================== escenas
# 0. gancho (inicio 6: pantalla dividida que choca) — arriba «¿ITALIANA?» (verde-blanco-rojo de Italia), abajo México
U_CHOQUE = 0.1


def _mitad(t, u, arriba):
    """Una mitad del inicio (se dibuja en un cuadro completo y se recorta su franja central de 960 px)."""
    yaw0 = 32 if arriba else -32
    fr = Frame(camara(u, [K(-3.5, 6.2, yaw0 + 30, 6, tx=0.0, ty=0.7), K(-0.3, 5.8, yaw0, 6, tx=0.0, ty=0.7),
                          K(U_CHOQUE + 0.1, 5.0, yaw0 * 0.6, 5, tx=0.0, ty=0.7), K(4, 4.9, yaw0 * 0.5, 5, tx=0.0, ty=0.7)],
                   cy=0.62 if arriba else 0.44))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5, beam_x=0.5)
    if arriba:
        M.cristal(fr.base, fr.fx, 'ITALIANA', u, t0=-2.3, cy=0.5, entrada='golpe')
    for j, col in enumerate((VERDE_B, (235, 235, 235), ROJO_B)):           # verde, blanco y rojo (¡las dos banderas!)
        x = -1.5 + j * 1.5
        line3(fr, [(x, 0.02, -2.8), (x, 0.02, -0.8)], col=col, w=18, a=0.55, glow=1.0)
    draw_objects(fr, moto(giro=-t * 2, faro=1.0))
    return fr


def s_gancho(t, fi, u, d):
    off = 0.35 * (1 - P.eout4(seg(u, -0.32, U_CHOQUE)))      # separadas (también en el loop) y chocan en U_CHOQUE
    ux = Wp(0, 'italiana') - 0.05
    A = _mitad(t, u, True)
    B = _mitad(t, u, False)

    def uiA(img, fx):
        if u > ux:                                           # se tacha la mitad italiana
            doodle_arrow(img, fx, 250, 880, 830, 1180, t, k=seg(u, ux, ux + 0.2), col=RED, seed=3, w=9)
            doodle_arrow(img, fx, 830, 880, 250, 1180, t, k=seg(u, ux + 0.1, ux + 0.3), col=RED, seed=4, w=9)
    A.ui.append(uiA)

    def uiB(img, fx):
        texto(img, fx, 540, 610, 'MÉXICO', 64, (120, 240, 160), 0.35 + 0.65 * eout(seg(u, ux + 0.2, ux + 0.4)), glow=0.6)
        pill(img, fx, 540, 700, 'MARCA MEXICANA', eout(seg(u, ux + 0.4, ux + 0.6)), size=24, border=(120, 240, 160))
    B.ui.append(uiB)
    a = finish(A, fi)
    b = finish(B, fi)
    out = np.zeros_like(a)
    dy = int(off * 960)
    top = a[480 + dy:1440, :]                                # mitad de arriba (entra desde arriba)
    out[0:top.shape[0], :] = top
    bot = b[480:1440 - dy, :]                                # mitad de abajo (entra desde abajo)
    out[960 + dy:960 + dy + bot.shape[0], :] = bot
    img = Image.fromarray(out)
    fx = Image.new('RGB', img.size, (0, 0, 0))
    dl = ImageDraw.Draw(img)
    if off < 0.02:
        kk = 1 - seg(u, U_CHOQUE, U_CHOQUE + 0.5)
        dl.line([(0, 960), (1080, 960)], fill=M.scale_c(WHITE, 0.35 + 0.65 * kk), width=4)
    else:
        dl.line([(0, 960 - dy), (1080, 960 - dy)], fill=(200, 200, 205), width=3)
        dl.line([(0, 960 + dy), (1080, 960 + dy)], fill=(200, 200, 205), width=3)
    kicker(img, 'MOTOS · LO QUE NO VES', 120, seg(u, U_CHOQUE, U_CHOQUE + 0.3), col=AZULC)
    P.titulo_golpe(img, fx, [('Tu Italika no es…', 'sans'), ('italiana.', 'serif')], 165, seg(u, U_CHOQUE + 0.05, U_CHOQUE + 0.2),
                   size=72)
    pill(img, fx, 540, 1480, 'RECREACIÓN', seg(u, 0.4, 0.7), size=20, border=(150, 150, 160), dot=False)
    a2 = np.asarray(img, np.float32) + np.asarray(fx.filter(ImageFilter.GaussianBlur(6)), np.float32) * 0.8
    return sacudir(a2.clip(0, 255).astype(np.uint8), t, golpe_k(u, U_CHOQUE, 0.4), amp=26)


# 1. es mexicana: la foto real cae (logo difuminado), 2004, Grupo Salinas, tiendas Elektra
def s_mexicana(t, fi, u, d):
    u04 = Wp(1, 'dos') - 0.1
    ugs = Wp(1, 'grupo') - 0.1
    uel = Wp(1, 'tiendas') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, -40, 10, ty=0.8), K(0.4, 4.4, -20, 6, ty=0.8), K(d, 4.2, -14, 6, ty=0.8)], cy=0.7))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, 'MEXICANA', u, t0=-0.15, cy=0.2, entrada='sube')

    def ui(img, fx):
        photo_card(img, fx, foto('scooter'), 540, 760, 860, t - u + 0.1, t, caption='Foto: Nan Palmero · CC BY 2.0',
                   angle0=-7.0)
        P.numero_golpe(img, fx, '2004', 1180, seg(u, u04, u04 + 0.15), size=170, col=AMARILLO)
        pill(img, fx, 540, 1300, 'GRUPO SALINAS', eout(seg(u, ugs, ugs + 0.25)), size=30, border=CYAN)
        pill(img, fx, 540, 1390, 'SE VENDE EN TIENDAS ELEKTRA', eout(seg(u, uel, uel + 0.25)), size=24,
             border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.38, 0.3), golpe_k(u, u04 + 0.15, 0.3)), amp=18)


# 2. se arma en Toluca: la línea de ensamble avanza y sale una moto cada minuto
def s_toluca(t, fi, u, d):
    umin = Wp(2, 'minuto') - 0.1
    fr = Frame(camara(u, [K(-0.3, 8.0, 40, 20, tx=0.0, ty=0.6), K(0.4, 7.2, 28, 14, tx=-0.4, ty=0.6),
                          K(umin - 0.3, 7.0, 24, 14, tx=-0.4, ty=0.6), K(umin, 5.4, 8, 8, tx=1.6, ty=0.6),
                          K(d, 5.2, 4, 8, tx=1.8, ty=0.6)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8, beam=0.4)
    for z in (-0.45, 0.45):                                                  # la banda
        line3(fr, [(-6, 0.02, z), (6, 0.02, z)], col=WHITE, w=2.6, a=0.8, glow=0.6)
    vel = 0.9
    off = (u * vel) % 2.4
    for j in range(-3, 4):
        x = j * 2.4 + off
        line3(fr, [(x - 1.2, 0.02, -0.45), (x - 1.2, 0.02, 0.45)], col=AMARILLO, w=2.0, a=0.6, glow=0.6)
        armado = clamp((x + 4.0) / 6.0)
        ms = P.despiece(moto(faro=0.3 + 0.7 * armado), 1 - armado, centro=(0, 0.6, 0), fuerza=0.9)
        draw_objects(fr, P.tfk(ms, s=0.7, t=(x, 0, 0)))
    pr = fr.cam.p1((2.6, 1.4, 0))

    def ui(img, fx):
        kicker(img, 'ENSAMBLIKA · TOLUCA, ESTADO DE MÉXICO', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 300, 'Toluca', 104, WHITE, eout(seg(u, 0.0, 0.2)), f='serif', glow=0.3)
        ka = seg(u, umin - 0.2, umin + 0.2)
        if ka > 0:
            d_ = ImageDraw.Draw(img)
            cx, cy, r = 540, 520, 70
            d_.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(WHITE, ka), width=5)
            a = -math.pi / 2 + 2 * math.pi * ((u - umin) % 1.0)
            d_.line([(cx, cy), (cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a))], fill=M.scale_c(AMARILLO, ka), width=6)
            pill(img, fx, 540, 640, '1 MOTO NUEVA CADA 60 SEGUNDOS', eout(ka), size=26, border=AMARILLO, dot=False)
        pill(img, fx, pr[0], pr[1] - 60, '¡LISTA!', eout(seg(u, umin + 0.2, umin + 0.4)), size=24, border=(120, 240, 160))
        pill(img, fx, 540, 1400, 'DESDE 2008', eout(seg(u, 0.5, 0.8)), size=22, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. casi 7 de cada 10 motos que se venden en México son suyas (10 motos; se prenden 7)
_ICON = {}


def icono_moto(col):
    key = col
    if key in _ICON:
        return _ICON[key]
    im = Image.new('L', (150, 100), 0)
    d = ImageDraw.Draw(im)
    d.ellipse((6, 52, 50, 96), outline=255, width=7)
    d.ellipse((100, 52, 144, 96), outline=255, width=7)
    d.polygon([(28, 74), (60, 40), (100, 40), (122, 74), (90, 74), (75, 56), (55, 74)], fill=255)
    d.line([(100, 40), (112, 18), (128, 16)], fill=255, width=7)
    _ICON[key] = im
    return im


def s_7de10(t, fi, u, d):
    u7 = Wp(3, 'siete') - 0.1
    umx = Wp(3, 'mexico') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.0, 0, 10, ty=1.0), K(d, 6.8, 0, 10, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, '7 DE 10', u, t0=u7, cy=0.25, entrada='zoom')

    def ui(img, fx):
        kicker(img, 'MOTOS NUEVAS QUE SE VENDEN EN MÉXICO', 150, seg(u, -0.1, 0.2), col=AZULC)
        ic = icono_moto(0)
        for j in range(10):
            cx_, cy_ = 230 + (j % 5) * 155, 760 + (j // 5) * 170
            ke = P.resorte(seg(u, -0.25 + 0.04 * j, 0.0 + 0.04 * j))
            if ke <= 0.01:
                continue
            on = j < 7 and u > u7 + 0.05 * j
            col = NARANJA if on else (90, 92, 100)
            s_ = max(0.05, ke)
            icn = ic.resize((int(150 * s_), int(100 * s_)))
            img.paste(Image.new('RGB', icn.size, col), (int(cx_ - icn.width / 2), int(cy_ - icn.height / 2)), icn)
            if on:
                fx.paste(Image.new('RGB', icn.size, M.scale_c(NARANJA, 0.5)), (int(cx_ - icn.width / 2), int(cy_ - icn.height / 2)),
                         icn.filter(ImageFilter.GaussianBlur(6)))
        pill(img, fx, 540, 1150, 'ENTRE 6 Y 7 DE CADA 10 · EXPANSIÓN, 2026', eout(seg(u, umx, umx + 0.3)), size=22,
             border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u7 + 0.3, 0.3), amp=14)


# 4. por dentro: la foto real del motor en corte cae; la moto en rayos X y su único cilindro
def s_dentro(t, fi, u, d):
    uc = Wp(4, 'cilindro') - 0.1
    u4 = Wp(4, 'cuatro') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, 30, 8, tx=0.1, ty=0.6), K(0.3, 3.4, 18, 6, tx=0.1, ty=0.5),
                          K(uc, 2.4, 6, 4, tx=0.12, ty=0.55), K(d, 2.3, 4, 4, tx=0.12, ty=0.55)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, '4 TIEMPOS', u, t0=u4, cy=0.3, entrada='golpe')
    draw_objects(fr, moto(giro=0, faro=0.6, motor_glow=0.6 * seg(u, uc, uc + 0.3)), xray=clamp(seg(u, 0.0, 0.35)),
                 keep=('in',))
    pm = fr.cam.p1((0.15, 0.7, 0.0))

    def ui(img, fx):
        kicker(img, 'RAYOS X · MOTOR DE 150 cc', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u < uc + 0.2:
            photo_card(img, fx, foto('corte'), 760, 470, 430, t - u + 0.05, t, caption='Motor de 1 cilindro en corte · CC0',
                       angle0=8.0)
        pill(img, fx, pm[0], pm[1] - 120, '1 CILINDRO', eout(seg(u, uc, uc + 0.25)), size=30, border=NARANJA)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, 0.4, 0.25), amp=12)


# 5. los cuatro tiempos, sincronizados con la voz: admisión, compresión, explosión y escape
def s_tiempos(t, fi, u, d):
    w = [Wp(5, 'entra'), Wp(5, 'piston'), Wp(5, 'chispa'), Wp(5, 'sale'), d]
    th = 0.0
    for j in range(4):
        if u >= w[j]:
            th = 180 * j + 179 * ease(seg(u, w[j], min(w[j] + 0.9, w[j + 1] - 0.05)))
    th = max(0.0, th) if u >= w[0] else 180 * (u - w[0]) * 0.0
    fr = Frame(camara(u, [K(-0.3, 7.6, 32, 10, ty=2.3), K(0.4, 6.6, 14, 6, ty=2.3), K(w[2] - 0.2, 6.4, -10, 6, ty=2.5),
                          K(w[3] - 0.2, 6.5, 12, 4, ty=2.3), K(d, 6.4, 16, 4, ty=2.3)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    yp, fase = cilindro(fr, t, th)
    pe = fr.cam.p1((-0.3, Y_CAB + 0.9, 0))
    ps = fr.cam.p1((0.3, Y_CAB + 0.9, 0))

    def ui(img, fx):
        kicker(img, 'UN CILINDRO · CUATRO TIEMPOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        nom, col = FASES[fase]
        texto(img, fx, 540, 290, nom, 64, col, 1.0, glow=0.6)
        for j, (n_, c_) in enumerate(FASES):
            x = 210 + j * 220
            k_ = 1.0 if j == fase else 0.35
            ImageDraw.Draw(img).rounded_rectangle((x - 95, 380, x + 95, 392), radius=6, fill=M.scale_c(c_, k_))
        if fase == 0:
            doodle_arrow(img, fx, pe[0] - 160, pe[1] - 120, pe[0] - 10, pe[1] - 10, t, k=1.0, col=AZULC, seed=2)
            pill(img, fx, pe[0] - 170, pe[1] - 170, 'AIRE + GASOLINA', 1.0, size=22, border=AZULC)
        if fase == 3:
            doodle_arrow(img, fx, ps[0] + 10, ps[1] - 10, ps[0] + 170, ps[1] - 130, t, k=1.0, col=GRIS, seed=5)
            pill(img, fx, ps[0] + 160, ps[1] - 180, 'AL ESCAPE', 1.0, size=22, border=GRIS)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, w[2] + 0.05, 0.35), amp=22)


# 6. a 8 500 rpm: unas 70 explosiones por segundo (el motor acelera hasta verse borroso)
def s_rpm(t, fi, u, d):
    u70 = Wp(6, 'setenta') - 0.1
    vel = 400 + 2600 * P.eout4(seg(u, 0.0, 1.6))                              # grados por segundo (cámara lenta)
    fr = Frame(camara(u, [K(-0.3, 6.0, -30, 8, ty=2.3), K(0.5, 7.0, 10, 4, ty=2.3), K(u70 - 0.2, 6.8, 18, 4, ty=2.3),
                          K(d, 6.7, 20, 4, ty=2.3)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8, beam=0.2)
    M.cristal(fr.base, fr.fx, '70', u, t0=u70, cy=0.3, entrada='zoom', ancho=0.6)
    cilindro(fr, t, (u * vel) % 720 + 360 * (vel > 2000) * (int(u * 7) % 2))

    def ui(img, fx):
        kicker(img, 'A TODO GAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        rpm = int(8500 * P.eout4(seg(u, 0.0, 1.6)))
        texto(img, fx, 540, 300, f'{rpm:,}'.replace(',', ' ') + ' rpm', 96, WHITE, 1.0, f='mono', glow=0.5)
        texto(img, fx, 540, 1330, '≈ 70 EXPLOSIONES POR SEGUNDO', 40, NARANJA, eout(seg(u, u70 + 0.1, u70 + 0.3)), f='mono',
              glow=0.6)
        pill(img, fx, 540, 1410, 'CÁMARA LENTA', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u70 + 0.1, 0.3) + 0.15 * seg(u, 1.0, 1.6), amp=14)


# 7. segundo gancho: el error que acaba con ese motor — no cambiarle el aceite (alerta roja, gota que se ennegrece)
def s_error(t, fi, u, d):
    ua = Wp(7, 'aceite') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, 20, 8, ty=1.0), K(0.5, 4.2, -10, 6, ty=1.0), K(d, 4.0, -16, 6, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ACEITE', u, t0=ua, cy=0.34, entrada='golpe')
    sucio = seg(u, ua + 0.3, d)
    col = M.mixc(ACEITE, (40, 30, 20), sucio)
    gota = named(M3.sphere(0.55, col, nu=28, nv=18, shadow=0, gloss=0.9), 'gota', rim=0.9, gloss=0.9)
    gota.V = gota.V * np.array([1.0, 1.0, 1.0])
    V = gota.V.copy()
    arriba = np.clip(V[:, 1] / 0.55, 0, 1)                                    # forma de gota (punta arriba)
    V[:, 0] *= 1 - 0.92 * arriba ** 1.3
    V[:, 2] *= 1 - 0.92 * arriba ** 1.3
    V[:, 1] = np.where(V[:, 1] > 0, V[:, 1] * 1.8, V[:, 1])
    gota.V = V
    e = P.entrada(u, -0.2, 0.3, 'cae')
    draw_objects(fr, P.tfk([gota], t=(0, 0.75 - e['dy'] * 0.5, 0)))

    def ui(img, fx):
        texto(img, fx, 540, 260, 'EL ERROR', 110, RED, eout(seg(u, 0.0, 0.12)), glow=0.8)
        kicker(img, 'QUE ACABA CON TU MOTOR', 380, seg(u, 0.2, 0.5), col=(255, 160, 150))
        pill(img, fx, 540, 1380, 'NO CAMBIAR EL ACEITE A TIEMPO', eout(seg(u, ua + 0.2, ua + 0.5)), size=28, border=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.0, 0.3), golpe_k(u, ua + 0.1, 0.3)), amp=20)


# 8. el aceite es una capa delgadita entre el pistón y el cilindro (zoom digital al hueco)
def s_capa(t, fi, u, d):
    ucap = Wp(8, 'capa') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.4, 10, 6, ty=2.3), K(0.3, 5.6, 4, 4, ty=2.2), K(d, 5.5, 2, 4, ty=2.2)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    yp, _ = cilindro(fr, t, 200 + 90 * u, aceite=ACEITE)
    px, py, _ = fr.cam.p1((R_CIL, yp + 0.15, 0))

    def ui(img, fx):
        kicker(img, 'ENTRE EL PISTÓN Y EL CILINDRO', 150, seg(u, -0.1, 0.2), col=AZULC)
        rec_frame(img, t, seg(u, ucap - 0.1, ucap), zoom_label='x2.4' if u > ucap + 0.8 else 'x1.6')
        if u > ucap + 0.3:
            pill(img, fx, 540, 1350, 'CAPA DE ACEITE · MÁS DELGADA QUE UN CABELLO', eout(seg(u, ucap + 0.3, ucap + 0.6)),
                 size=22, border=ACEITE)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u > ucap:
        z = 1.6 if u < ucap + 0.8 else 2.4
        out = M.scale_about(out, z, px / 1080, py / 1920)
    return out


# 9. viejo: se ensucia y se adelgaza, roza metal con metal, se calienta… y el motor se amarra
def s_amarra(t, fi, u, d):
    uroz = Wp(9, 'metal') - 0.1
    ucal = Wp(9, 'calienta') - 0.1
    uam = Wp(9, 'amarra') - 0.1
    sucio = seg(u, 0.0, uroz)
    col = M.mixc(ACEITE, (50, 38, 26), sucio)
    vel = 220 * (1 - seg(u, uam - 0.4, uam + 0.1))
    th = 200 + vel * min(u, uam + 0.1)
    fr = Frame(camara(u, [K(-0.3, 4.8, -14, 6, ty=2.6), K(uroz - 0.3, 4.4, -8, 5, ty=2.6), K(uroz, 3.6, 18, 4, ty=2.8),
                          K(uam, 5.6, 0, 4, ty=2.4), K(d, 5.4, -4, 4, ty=2.4)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'SE AMARRA', u, t0=uam, cy=0.25, entrada='golpe')
    yp, _ = cilindro(fr, t, th, aceite=col if u < uroz else None, roce=seg(u, uroz, uroz + 0.3) * (1 - seg(u, uam + 0.6, uam + 1.2)))
    if u > ucal:
        P.ondas_calor(fr, t, 0.0, Y_CAB + 0.9, Y_CAB + 2.0, 1.6, k=seg(u, ucal, ucal + 0.4))

    def ui(img, fx):
        kicker(img, 'ACEITE VIEJO', 150, seg(u, -0.1, 0.2), col=(255, 180, 120))
        if u < uroz:
            pill(img, fx, 540, 1350, 'SUCIO Y AGUADO', eout(seg(u, 0.4, 0.7)), size=26, border=(160, 120, 80))
        elif u < uam:
            texto(img, fx, 540, 1330, 'METAL CONTRA METAL', 52, (255, 200, 120), eout(seg(u, uroz, uroz + 0.2)), glow=0.6)
        P.termometro(img, fx, 920, 1250, 360, 0.3 + 0.65 * seg(u, ucal, uam), '', k=seg(u, ucal - 0.2, ucal + 0.1),
                     col=(255, 80, 60))
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u > uam:                                                              # se amarra: se tiñe de rojo y se congela
        kk = seg(u, uam, uam + 0.15)
        o = out.astype(np.float32)
        o[..., 0] = o[..., 0] * (1 + 0.5 * kk) + 30 * kk
        o[..., 1] *= 1 - 0.35 * kk
        o[..., 2] *= 1 - 0.35 * kk
        out = o.clip(0, 255).astype(np.uint8)
    return sacudir(out, t, golpe_k(u, uam, 0.5), amp=30)


# 10. Italika pide cambiarlo en cada servicio: cada 3 000 a 6 000 km según tu modelo (odómetro y carretera)
def s_servicio(t, fi, u, d):
    u3 = Wp(10, 'tres') - 0.1
    u6 = Wp(10, 'seis') - 0.1
    km = 6000 * ease(seg(u, 0.2, u6 + 0.4))
    x = km / 1000.0
    fr = Frame(camara(u, [K(-0.3, 6.0, 40, 8, tx=0.0, ty=0.7), K(0.4, 5.4, 70, 6, tx=0.0, ty=0.7),
                          K(d, 5.2, 76, 6, tx=0.0, ty=0.7)], cy=0.6))
    fr.cam.target = fr.cam.target + np.array([x, 0, 0])
    fr.cam.pos = fr.cam.pos + np.array([x, 0, 0])
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.0)
    for z in (-0.5, 0.5):
        line3(fr, [(x - 8, 0.01, z), (x + 8, 0.01, z)], col=WHITE, w=2.4, a=0.8, glow=0.6)
    for m in (3, 6):                                                         # postes de servicio en el km 3 000 y 6 000
        line3(fr, [(m, 0, -0.8), (m, 1.6, -0.8)], col=ACEITE, w=4, a=0.9, glow=1.0)
        dot3(fr, (m, 1.7, -0.8), r=12, col=ACEITE, glow=1.5)
    draw_objects(fr, P.tfk(moto(giro=-x / 0.34, faro=1.0), s=0.8, t=(x, 0, 0)))
    p3 = fr.cam.p1((3, 1.9, -0.8))
    p6 = fr.cam.p1((6, 1.9, -0.8))

    def ui(img, fx):
        kicker(img, 'EN CADA SERVICIO · SEGÚN TU MANUAL', 150, seg(u, -0.1, 0.2), col=AZULC)
        d_ = ImageDraw.Draw(img)
        d_.rounded_rectangle((300, 240, 780, 360), radius=20, fill=(14, 15, 19), outline=(120, 120, 130), width=3)
        texto(img, fx, 540, 300, f'{int(km):06d} km', 72, WHITE, 1.0, f='mono', glow=0.3)
        if u > u3:
            pill(img, fx, p3[0], p3[1] - 40, 'CAMBIO DE ACEITE · 3 000 km', eout(seg(u, u3, u3 + 0.25)), size=22, border=ACEITE)
        if u > u6:
            pill(img, fx, p6[0], p6[1] - 40, '6 000 km (MODELOS NUEVOS)', eout(seg(u, u6, u6 + 0.25)), size=22, border=ACEITE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. sus piezas llegan de China (Shanghái → Lázaro Cárdenas → Toluca) y se arman aquí (la moto se arma sola)
MX = [(-117.1, 32.5), (-114.7, 32.7), (-111.0, 31.3), (-108.2, 31.3), (-106.5, 31.8), (-104.5, 29.6), (-102.5, 29.8),
      (-100.3, 28.2), (-99.5, 27.5), (-97.2, 25.9), (-97.7, 22.0), (-97.2, 20.0), (-95.0, 18.6), (-92.0, 18.6),
      (-90.4, 21.2), (-87.0, 21.5), (-87.5, 18.5), (-89.1, 17.8), (-90.4, 17.8), (-91.4, 16.1), (-92.2, 14.6),
      (-94.0, 16.1), (-96.5, 15.7), (-99.8, 16.7), (-102.2, 17.9), (-105.2, 20.4), (-105.7, 22.5), (-108.0, 25.0),
      (-109.4, 26.0), (-111.0, 27.8), (-112.8, 30.0), (-113.6, 31.3), (-114.8, 31.5), (-114.0, 29.5), (-112.0, 27.0),
      (-110.0, 24.0), (-109.5, 23.0), (-110.2, 23.4), (-112.1, 24.8), (-112.1, 26.3), (-114.2, 27.8), (-115.0, 29.5),
      (-117.1, 32.5)]


def gm(lon, lat, y=0.0):
    return np.array([(lon + 100.0) * 0.28, y, -(lat - 23.0) * 0.28])


def mapa_mx(fr, k=1.0):
    line3(fr, [gm(lo, la) for lo, la in MX], col=WHITE, w=2.4, a=0.85 * k, glow=0.7, frac=min(1.0, k * 1.1))


def s_china(t, fi, u, d):
    uaq = Wp(11, 'aqui') - 0.15
    ruta = ease(seg(u, 0.2, uaq - 0.2))
    fr = Frame(camara(u, [K(-0.3, 12.0, 0, 60, tx=-3.0, ty=0.0, tz=0.0), K(0.5, 11.0, 0, 62, tx=-2.5, ty=0.0),
                          K(uaq - 0.6, 10.5, 4, 62, tx=-2.0, ty=0.0),
                          K(uaq, 4.4, 26, 10, tx=0.0, ty=0.6, tz=0.0), K(d, 4.2, 20, 8, tx=0.0, ty=0.6)], cy=0.55))
    space(fr, t, floor='lines' if u > uaq else None, floor_a=0.6, bokeh=0.8)
    if u < uaq + 0.2:
        mapa_mx(fr, k=1.0 - seg(u, uaq, uaq + 0.2))
        lc = gm(-102.2, 17.95)
        tol = gm(-99.65, 19.29)
        sha = gm(-100.0 - 60.0, 19.0)                                        # Shanghái queda muy lejos (fuera del cuadro)
        P_ = [sha + (lc - sha) * s for s in np.linspace(0, 1, 30)] + [lc + (tol - lc) * s for s in np.linspace(0, 1, 8)]
        n = max(2, int(len(P_) * ruta))
        line3(fr, P_[:n], col=NARANJA, w=4, a=1.0, glow=1.2)
        dot3(fr, P_[n - 1], r=10, col=WHITE, glow=2.0)
        for p in (lc, tol):
            dot3(fr, p, r=7, col=AMARILLO, glow=1.2)
        plc = fr.cam.p1(tuple(lc))
        ptl = fr.cam.p1(tuple(tol))
    else:
        plc = ptl = (0, 0, 0)
    if u > uaq - 0.1:
        k = 1 - P.eout4(seg(u, uaq, uaq + 0.6))
        draw_objects(fr, P.despiece(moto(faro=1.0), k, centro=(0, 0.6, 0), fuerza=1.4, giro=0.6))

    def ui(img, fx):
        if u < uaq:
            kicker(img, 'DE SHANGHÁI, CHINA → LÁZARO CÁRDENAS → TOLUCA', 150, seg(u, -0.1, 0.2), col=AZULC)
            pill(img, fx, plc[0] - 40, plc[1] + 60, 'LÁZARO CÁRDENAS, MICH.', eout(seg(ruta, 0.7, 0.8)), size=20, border=AMARILLO,
                 dot=False)
            pill(img, fx, ptl[0] + 40, ptl[1] - 60, 'TOLUCA', eout(seg(ruta, 0.95, 1.0)), size=22, border=AMARILLO, dot=False)
            pill(img, fx, 540, 330, 'LA MAYORÍA DE LAS PIEZAS', eout(seg(u, 0.4, 0.7)), size=26, border=NARANJA, dot=False)
        else:
            kicker(img, 'SE ARMAN AQUÍ', 150, seg(u, uaq, uaq + 0.3), col=(120, 240, 160))
            texto(img, fx, 540, 300, 'con manos mexicanas', 70, WHITE, eout(seg(u, uaq + 0.5, uaq + 0.8)), f='serif', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uaq + 0.6, 0.3), amp=16)


# 12. desde 2025 también en Jalisco: entre las dos plantas, más de 1.5 millones de motos al año (gráfica que crece)
def s_jalisco(t, fi, u, d):
    uj = Wp(12, 'jalisco') - 0.1
    um = Wp(12, 'millon') - 0.1
    fr = Frame(camara(u, [K(-0.3, 9.0, 0, 58, tx=-0.4, ty=0.0, tz=-0.6), K(0.5, 8.0, 10, 56, tx=-0.6, ty=0.0, tz=-0.8),
                          K(d, 7.8, 12, 56, tx=-0.6, ty=0.0, tz=-0.8)], cy=0.45))
    space(fr, t, floor=None, bokeh=0.8)
    mapa_mx(fr, 1.0)
    tol = gm(-99.65, 19.29, 0.02)
    jal = gm(-103.25, 20.52, 0.02)
    dot3(fr, tol, r=11, col=NARANJA, glow=1.6)
    kj = seg(u, uj - 0.1, uj + 0.2)
    if kj > 0:
        dot3(fr, jal, r=11 * P.resorte(kj), col=NARANJA, glow=1.6)
        for j in range(3):
            ph = (t * 1.4 + j / 3) % 1.0
            q = np.linspace(0, 2 * math.pi, 30)
            line3(fr, [jal + np.array([0.5 * ph * math.cos(a), 0, 0.5 * ph * math.sin(a)]) for a in q], col=NARANJA, w=2,
                  a=(1 - ph) * kj, glow=1.0)
    pt = fr.cam.p1(tuple(tol))
    pj = fr.cam.p1(tuple(jal))

    def ui(img, fx):
        kicker(img, 'ENSAMBLIKA · 2 PLANTAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pt[0] + 60, pt[1] + 50, 'TOLUCA · 2008', 1.0, size=20, border=NARANJA, dot=False)
        pill(img, fx, pj[0] - 40, pj[1] - 55, 'EL SALTO, JALISCO · 2025', eout(kj), size=20, border=NARANJA, dot=False)
        if u > um - 0.3:
            chart_grow(img, fx, (170, 980, 910, 1500), [1.2, 0.5, 1.7], ['TOLUCA', 'JALISCO', 'JUNTAS'], t - u + um - 0.3, t,
                       unit='', title_txt='CAPACIDAD (MILLONES DE MOTOS AL AÑO)', vmax=2.0, line=False)
            texto(img, fx, 540, 300, '+1 500 000 al año', 80, WHITE, eout(seg(u, um, um + 0.25)), glow=0.4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. mándaselo a tu compa que dice que su Italika es italiana (de noche, faro prendido)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, 70, 4, ty=0.7), K(0.4, 3.8, 40, 3, ty=0.7), K(d, 3.7, 34, 3, ty=0.7)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.0)
    draw_objects(fr, moto(giro=-u * 6, faro=1.8))
    pf = fr.cam.p1((0.72, 1.0, 0))

    def ui(img, fx):
        df = ImageDraw.Draw(fx)
        for j, r in enumerate((60, 130, 220)):
            df.ellipse((pf[0] - r, pf[1] - r * 0.6, pf[0] + r, pf[1] + r * 0.6), fill=M.scale_c((255, 240, 200), 0.32 / (j + 1)))
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que dice que es italiana.', 'serif')], 230,
                       seg(u, 0.0, 0.15), size=70)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-0.3, 'whoosh', 0.8), (U_CHOQUE, 'sub', 1.0), (U_CHOQUE, 'bass', 0.9), (1.5, 'scribble', 0.7),
                     (1.9, 'chime_b', 0.5)]),
           dict(desde=1, fn=s_mexicana, tr='rompe', c=(0.5, 0.3), sfx=[(0.38, 'slap', 0.9), (1.5, 'bass', 0.8), (3.0, 'tick', 0.6)]),
           dict(desde=2, fn=s_toluca, tr='deslizar_abajo', sfx=[(0.1 + 0.4 * j, 'click', 0.5) for j in range(6)] + [(2.6, 'chime_a', 0.5)]),
           dict(desde=3, fn=s_7de10, tr='mosaico', sfx=[(0.3 + 0.05 * j, 'tick', 0.45) for j in range(7)] + [(0.6, 'bass', 0.7)]),
           dict(desde=4, fn=s_dentro, tr='zoom', c=(0.5, 0.5), sfx=[(0.05, 'slap', 0.8), (0.3, 'shimmer', 0.5), (1.1, 'click', 0.7)]),
           dict(desde=5, fn=s_tiempos, tr='cubo', sfx=[(0.1, 'whoosh_suave', 0.6), (1.6, 'thud', 0.7), (2.9, 'sub', 1.0),
                                                       (2.95, 'burst', 0.8), (4.2, 'whoosh', 0.7)]),
           dict(desde=6, fn=s_rpm, tr='remolino', sfx=[(0.1, 'riser', 0.6)] + [(1.0 + 0.12 * j, 'thud', 0.35) for j in range(14)]),
           dict(desde=7, fn=s_error, tr='glitch', sfx=[(0.0, 'bass', 0.9), (0.0, 'digital', 0.5), (2.7, 'sub', 0.7)]),
           dict(desde=8, fn=s_capa, tr='push', c=(0.5, 0.45), sfx=[(0.8, 'click', 0.8), (1.6, 'click', 0.8)]),
           dict(desde=9, fn=s_amarra, tr='flash', sfx=[(2.3, 'scribble', 0.6), (4.2, 'riser', 0.5), (6.0, 'sub', 1.0),
                                                      (6.0, 'bass', 1.0)]),
           dict(desde=10, fn=s_servicio, tr='wipe', sfx=[(2.4, 'chime_a', 0.6), (3.3, 'chime_b', 0.6)]),
           dict(desde=11, fn=s_china, tr='giro', sfx=[(0.2, 'whoosh_suave', 0.6), (3.0, 'click', 0.8), (3.6, 'thud', 0.8)]),
           dict(desde=12, fn=s_jalisco, tr='iris', c=(0.45, 0.45), sfx=[(1.6, 'chime_c', 0.5), (3.4, 'bass', 0.6)]),
           dict(desde=13, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7)]),
           dict(desde=14, loop=True, tr='whip')]

if __name__ == '__main__':
    montaje.cli(globals())
