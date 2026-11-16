"""Reel diario mié 18-nov-2026 10:00 — «Tu gasolina Premium… no tiene más fuerza.» (el octanaje mide aguante a la
compresión, no energía; cascabeleo; prueba Magna contra Premium; error: pagar Premium en un carro que pide Magna y, al
revés, Magna en un turbo que pide Premium: el sensor atrasa la chispa y le quita fuerza).
Comunidad: automovilistas (cualquiera que carga gasolina). Inicio tipo 5 (número gigante): el contador sube y el «91»
rojo se clava en la pantalla con sacudida, delante de «PREMIUM» de cristal, y luego se revela de qué es (la pistola
de la bomba). El final («porque su gasolina Premium… no tiene más fuerza») regresa a él (loop).
Voz Isaac (eleven_v4) del 16-nov, 62.2 s. Datos y fuentes: guiones/2026-11-18_gasolina.txt.
Foto real: motor de un cilindro en corte (CheminduCret, CC0; ya usada en el reel de la Italika, recortada sin letreros).
El cilindro, el motor turbo, el sensor y los grados de la chispa son esquemas marcados «ESQUEMA»/«EJEMPLO».
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'gasolina'
TXT = ['Tu gasolina Premium… no tiene más fuerza.',
       'Ese número de octanos no mide energía: mide aguante.',
       'Mira el pistón: aprieta el aire con gasolina,',
       'y la bujía lo prende justo a tiempo.',
       'Si la gasolina no aguanta tanto apretón,',
       'explota sola antes de tiempo.',
       'Ese es el cascabeleo: el golpeteo metálico del motor.',
       'Ahora la prueba: un motor normal con Magna,',
       'y el mismo motor con Premium.',
       'Empatan: casi la misma energía por litro y la misma fuerza.',
       'Pero aquí está el error: pagar Premium en un carro que pide Magna.',
       'En noviembre, el litro de Premium cuesta casi 5 pesos más.',
       'En un tanque de 40 litros, son casi 200 pesos… por nada.',
       'Y al revés también falla: un motor turbo que pide Premium,',
       'con Magna, cascabelea.',
       'Su computadora lo oye con un sensor, atrasa la chispa para protegerlo… y le quita fuerza.',
       '¿Cuál le toca al tuyo? Viene en el manual o en la tapa del tanque.',
       'Mándaselo a quien le pone Premium para que corra más,',
       'porque su gasolina Premium… no tiene más fuerza.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-18_gasolina_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_gasolina.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-18_gasolina_words.json')
FOTOS = os.path.join(_REPO, 'inbox')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
VERDE = (40, 205, 110)
ROJO_P = (232, 46, 42)
NEGRO = (24, 24, 28)
CROMO = (210, 212, 218)
GRIS = (150, 150, 160)
DINERO = (120, 220, 140)


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


def esquema(img, fx, k=1.0, y=1440, txt='ESQUEMA'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


def tubo(p0, p1, r=0.03, col=CROMO, n=8, name='tubo', gloss=0.8):
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


# ------------------------------------------------------------------ objetos
def pistola(col=ROJO_P, gota=0.0):
    """Pistola de la bomba de gasolina (sin marca): cuerpo de color, mango negro, pico cromado y manguera."""
    ms = [named(M3.rbox(0.66, 0.28, 0.22, 0.09, col, n=4, shadow=0, gloss=0.75).tf(t=(0.0, 0.95, 0)), 'cuerpo',
                rim=0.75, gloss=0.75),
          named(M3.rbox(0.17, 0.52, 0.17, 0.06, NEGRO, n=3, shadow=0, gloss=0.25).tf(rz=-22, t=(-0.18, 0.5, 0)), 'mango',
                rim=0.5, gloss=0.25),
          tubo((-0.12, 0.6, 0), (0.24, 0.72, 0), r=0.026, col=CROMO, name='guarda'),
          tubo((0.28, 1.08, 0), (1.0, 0.8, 0), r=0.052, col=CROMO, name='pico', gloss=0.95),
          tubo((0.96, 0.815, 0), (1.04, 0.785, 0), r=0.068, col=(150, 152, 158), name='pico'),
          tubo((-0.3, 1.12, 0), (-0.78, 1.42, 0), r=0.075, col=(28, 28, 32), name='manguera', gloss=0.3),
          tubo((-0.78, 1.42, 0), (-1.5, 1.6, 0), r=0.075, col=(28, 28, 32), name='manguera', gloss=0.3)]
    _B(ms, 0.06, 0.2, 0.07, (70, 70, 76), 0.04, 0.73, 0, gloss=0.6)
    if gota > 0.01:
        g = gota_m(col, 0.09)
        ms += P.tfk(g, t=(1.07, 0.66 - 0.6 * gota, 0))
    return ms


def gota_m(col, r=0.5):
    g = named(M3.sphere(r, col, nu=26, nv=16, shadow=0, gloss=0.9), 'gota', rim=0.9, gloss=0.9)
    V = g.V.copy()
    arriba = np.clip(V[:, 1] / r, 0, 1)
    V[:, 0] *= 1 - 0.92 * arriba ** 1.3
    V[:, 2] *= 1 - 0.92 * arriba ** 1.3
    V[:, 1] = np.where(V[:, 1] > 0, V[:, 1] * 1.8, V[:, 1])
    g.V = V
    return [g]


def auto(col=(70, 76, 90), tapa=0.0, giro=0.0):
    """Sedán sin marca (frente hacia +x) con la tapa del tanque en el costado trasero derecho (+z)."""
    ms = []
    ms.append(named(M3.rbox(3.0, 0.5, 1.25, 0.22, col, n=5, shadow=0, gloss=0.8).tf(t=(0, 0.32, 0)), 'cuerpo', rim=0.8, gloss=0.8))
    ms.append(named(M3.rbox(1.55, 0.46, 1.1, 0.25, (30, 34, 42), n=5, shadow=0, gloss=0.95).tf(t=(-0.2, 0.8, 0)), 'vidrio',
                    rim=0.9, gloss=0.95))
    ms.append(named(M3.rbox(1.3, 0.06, 1.0, 0.2, col, n=4, shadow=0, gloss=0.8).tf(t=(-0.22, 1.25, 0)), 'cuerpo', rim=0.8))
    for x in (1.0, -1.0):
        for z in (0.6, -0.68):
            ms.append(named(M3.cyl(0.33, 0.2, (22, 22, 24), n=22, shadow=0, gloss=0.15).tf(rx=90, t=(x, 0.33, z + 0.1)), 'llanta',
                            rim=0.35))
            ms.append(named(M3.cyl(0.2, 0.21, (170, 172, 178), n=14, shadow=0, gloss=0.85).tf(rx=90, t=(x, 0.33, z + 0.105)),
                            'rin', rim=0.7))
    for z in (-0.45, 0.45):                                                    # faros y calaveras
        _B(ms, 0.04, 0.12, 0.26, (255, 248, 230), 1.5, 0.55, z, glow=(160, 150, 120))
        _B(ms, 0.04, 0.1, 0.26, (200, 30, 30), -1.5, 0.58, z, glow=(120, 20, 20))
    # tapa del tanque: gira sobre su borde trasero (bisagra en x = -0.92)
    a = math.radians(-100 * clamp(tapa))
    hx, hz = -0.92, 0.635
    tp = named(M3.box(0.26, 0.24, 0.025, (90, 96, 110), shadow=0, gloss=0.8, base=False), 'tapa', rim=0.8)
    tp = tp.tf(t=(0.13, 0, 0)).tf(ry=math.degrees(-a) * -1).tf(t=(hx, 0.66, hz))
    ms.append(tp)
    if tapa > 0.05:
        _B(ms, 0.1, 0.1, 0.02, (12, 12, 14), -0.79, 0.61, 0.632, name='hueco', base=True)
    return P.tfk(ms, ry=giro) if giro else ms


# ------------------------------------------------------------------ el cilindro por dentro (corte, esquema)
R_CIL, Y_CAB = 0.62, 3.2
Y_TECHO = Y_CAB + 0.75


def yp_de(theta):
    th = math.radians(theta)
    r, L = 0.62, 1.7
    return 0.6 + r * math.cos(th) + math.sqrt(L * L - (r * math.sin(th)) ** 2)


def cilindro(fr, t, theta, gas=AZULC, chispa=0.0, frente=0.0, detona=0.0, ondas=0.0, x0=0.0, s=1.0, k=1.0,
             temblor=0.0, rojo=0.0, seed=4):
    """Corte del cilindro de un motor de gasolina: paredes de línea que brilla, pistón y biela, válvulas, bujía.
    frente: la flama que sale de la bujía (0-1). detona: explosión que nace sola en un punto caliente (0-1).
    ondas: ondas de presión que rebotan (cascabeleo)."""
    def q(x, y, z=0.0):
        return (x0 + s * x, s * y, s * z)
    yp = yp_de(theta) + 0.03 * temblor * math.sin(t * 160)
    top = yp + 0.32
    qq = np.linspace(0, 2 * math.pi, 40)
    wcol = M.mixc(WHITE, (255, 90, 70), rojo)
    for y in (1.5, Y_TECHO):
        line3(fr, [q(R_CIL * math.cos(a), y, R_CIL * math.sin(a)) for a in qq], col=wcol, w=2.4, a=0.7 * k, glow=0.6)
    for x in (-R_CIL, R_CIL):
        line3(fr, [q(x, 1.5, 0), q(x, Y_TECHO, 0)], col=wcol, w=3.0, a=0.95 * k, glow=0.8)
    for x in (-R_CIL - 0.3, R_CIL + 0.3):                                     # camisa de agua (contorno)
        line3(fr, [q(x, 1.7, 0), q(x, Y_TECHO + 0.15, 0)], col=(110, 150, 190), w=1.6, a=0.45 * k, glow=0.3)
    line3(fr, [q(-R_CIL - 0.3, Y_TECHO + 0.15, 0), q(R_CIL + 0.3, Y_TECHO + 0.15, 0)], col=(110, 150, 190), w=1.6, a=0.45 * k)
    th = math.radians(theta)
    cz = (0.62 * math.sin(th), 0.6 + 0.62 * math.cos(th))
    line3(fr, [q(0.62 * math.cos(a), 0.6 + 0.62 * math.sin(a), 0) for a in qq], col=AMARILLO, w=2.4, a=0.7 * k, glow=0.7)
    line3(fr, [q(cz[0], cz[1], 0.05), q(0, yp, 0.05)], col=CROMO, w=6 * s, a=0.95 * k, glow=0.3)
    # la mezcla de aire con gasolina
    rng = np.random.RandomState(seed)
    for j in range(42):
        y = top + 0.05 + rng.rand() * (Y_TECHO - 0.05 - top)
        x = (rng.rand() - 0.5) * 2 * (R_CIL - 0.08)
        x += 0.03 * math.sin(t * 17 + j)
        c = gas
        dd = math.hypot(x, Y_TECHO - 0.05 - y)
        if frente > 0 and dd < frente * 1.6:
            c = NARANJA
        if detona > 0:
            dh = math.hypot(x + 0.42, y - (top + 0.25))
            if dh < detona * 1.7:
                c = (255, 70, 40)
        dot3(fr, q(x, y, (rng.rand() - 0.5) * 0.4), r=3.6 * s ** 0.5, col=c, a=0.85 * k,
             glow=1.2 if c in (NARANJA, (255, 70, 40)) else 0.6)
    if chispa > 0.01:                                                       # la chispa de la bujía
        dot3(fr, q(0, Y_TECHO - 0.05, 0), r=(10 + 34 * chispa) * s, col=(255, 240, 190), a=chispa, glow=2.5)
    if frente > 0.01:                                                       # frente de flama (semicírculo que baja)
        r = min(1.6, frente * 1.6)
        arc = [q(clamp(r * math.cos(a), -R_CIL + 0.02, R_CIL - 0.02), max(top, Y_TECHO - 0.05 - r * math.sin(a)), 0.1)
               for a in np.linspace(0, math.pi, 30)]
        line3(fr, arc, col=(255, 190, 90), w=4 * s, a=0.9 * k * (1 - seg(frente, 0.85, 1.0)), glow=1.6)
    if detona > 0.01:                                                       # explosión que nace sola
        hx, hy = -0.42, top + 0.25
        dot3(fr, q(hx, hy, 0.1), r=(8 + 30 * detona) * s, col=(255, 90, 50), a=1 - 0.5 * detona, glow=2.4)
        r = detona * 1.1
        arc = [q(clamp(hx + r * math.cos(a), -R_CIL + 0.02, R_CIL - 0.02), clamp(hy + r * math.sin(a), top, Y_TECHO), 0.1)
               for a in np.linspace(0, 2 * math.pi, 36)]
        line3(fr, arc, col=(255, 80, 50), w=4 * s, a=0.9 * k, glow=1.8)
    if ondas > 0.01:                                                        # ondas de presión que rebotan
        for j in range(4):
            ph = (t * 3.2 + j * 0.25) % 1.0
            r = 0.1 + ph * 1.3
            cx_ = -0.42 if j % 2 == 0 else 0.42
            arc = [q(clamp(cx_ + r * math.cos(a), -R_CIL + 0.02, R_CIL - 0.02), clamp(top + 0.3 + r * math.sin(a), top, Y_TECHO), 0.12)
                   for a in np.linspace(0, 2 * math.pi, 40)]
            line3(fr, arc, col=(255, 210, 120), w=2.6 * s, a=ondas * (1 - ph) * k, glow=1.4)
    ms = [named(M3.cyl(R_CIL - 0.03, 0.32, M.mixc((186, 190, 198), (255, 120, 90), 0.5 * rojo), n=28, shadow=0, gloss=0.85).tf(
        t=(0, yp, 0)), 'piston', rim=0.85, gloss=0.85),
        named(M3.cyl(0.05, 0.4, (230, 232, 236), n=10, shadow=0, gloss=0.9).tf(t=(0, Y_TECHO - 0.05, 0)), 'bujia', rim=0.9),
        named(M3.cyl(0.1, 0.16, (240, 240, 244), n=12, shadow=0, gloss=0.6).tf(t=(0, Y_TECHO + 0.22, 0)), 'bujia', rim=0.9)]
    for sx_, col in ((-1, (90, 160, 230)), (1, (200, 120, 70))):
        ms.append(named(M3.cyl(0.17, 0.05, col, n=16, shadow=0, gloss=0.8).tf(t=(sx_ * 0.32, Y_TECHO - 0.05, 0)), 'valvula', rim=0.8))
        ms.append(named(M3.cyl(0.03, 0.6, CROMO, n=8, shadow=0, gloss=0.9).tf(t=(sx_ * 0.32, Y_TECHO, 0)), 'valvula'))
    draw_objects(fr, P.tfk(ms, s=s, t=(x0, 0, 0)))
    return yp


def theta_compresion(u, u0, dur):
    """Ángulo del cigüeñal que sube el pistón de abajo (180) hasta arriba (360) entre u0 y u0+dur."""
    return 180 + 180 * ease(seg(u, u0, u0 + dur))


# ------------------------------------------------------------------ foto real
_F = {}


def foto():
    if 'c' not in _F:
        im = Image.open(os.path.join(FOTOS, 'italika_i_corte1920.jpg')).convert('RGB')
        _F['c'] = im.crop((230, 20, 1130, 900))
    return _F['c']


# ================================================================== escenas
# 0. gancho (inicio 5: número gigante). En el pre-roll (lo que se ve al final, loop) cae «PREMIUM» de cristal y el
#    contador sube de 0 a 91; en −0.5 se clava con sacudida. Luego se revela de qué es: la pistola roja de la bomba.
U_CLAVA = -0.5


def s_gancho(t, fi, u, d):
    uf = Wp(0, 'fuerza') - 0.1
    fr = Frame(camara(u, [K(-4.2, 7.5, 0, 4, ty=1.0), K(U_CLAVA, 6.6, -8, 4, ty=1.0), K(0.15, 3.6, 22, 8, ty=1.0, tx=0.1),
                          K(uf, 3.3, 30, 8, ty=1.0, tx=0.1), K(4.0, 3.2, 34, 8, ty=1.0, tx=0.1)], cy=0.64))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'PREMIUM', u, t0=-4.0, cy=0.62, entrada='golpe')
    e = P.entrada(u, -3.9, 0.3, 'cae')
    if u > -3.9:
        draw_objects(fr, P.tfk(pistola(ROJO_P, gota=seg(u, 0.9, 1.6) if u < 1.6 else seg(u, 2.2, 2.9)),
                               ry=-20 + 10 * math.sin(t * 0.8), t=(0, -e['dy'] * 0.5, 0)))
    pp = fr.cam.p1((0.2, 1.2, 0))

    def ui(img, fx):
        n = int(91 * seg(u, -3.6, U_CLAVA) ** 1.6) if u < U_CLAVA else 91
        ka = seg(u, -3.7, -3.55)
        if u < 0.05:
            P.numero_golpe(img, fx, str(n), 640, 1.0 if u >= U_CLAVA else 0.75 * ka, size=520, col=ROJO_P, glow=0.7)
        else:                                                                 # sube y se encoge: revela de qué es
            kk = P.eout4(seg(u, 0.05, 0.35))
            P.numero_golpe(img, fx, '91', 640 - 150 * kk, 1.0, size=int(520 - 300 * kk), col=ROJO_P, glow=0.7)
            kicker(img, 'OCTANOS · GASOLINA PREMIUM', 640, seg(u, 0.2, 0.45), col=(255, 170, 160))
        if u >= U_CLAVA - 0.05:
            kicker(img, 'NÚMERO DE OCTANOS', 950, seg(u, U_CLAVA, U_CLAVA + 0.15) * (1 - seg(u, 0.0, 0.1)),
                   col=GRIS)
        P.titulo_golpe(img, fx, [('Tu gasolina Premium…', 'sans'), ('no tiene más fuerza.', 'serif')], 180, seg(u, 0.1, 0.25),
                       size=70)
        if u > uf:
            P.pill_tachada(img, fx, pp[0], pp[1] - 190, 'MÁS FUERZA', seg(u, uf, uf + 0.2), seg(u, uf + 0.25, uf + 0.55), t,
                           size=30)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, U_CLAVA, 0.4), golpe_k(u, 0.25, 0.3)), amp=28)


# 1. el número de octanos no mide energía: mide aguante (dos gotas: Magna 87 y Premium 91; la prensa las aprieta)
def s_octanos(t, fi, u, d):
    ue = Wp(1, 'energia') - 0.1
    ua = Wp(1, 'aguante') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.2, 30, 10, ty=0.9), K(0.4, 4.6, 8, 6, ty=0.9), K(ua - 0.2, 4.6, 4, 6, ty=0.9),
                          K(ua, 3.9, -10, 4, ty=0.8), K(d, 3.8, -14, 4, ty=0.8)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.4)
    M.cristal(fr.base, fr.fx, 'AGUANTE', u, t0=ua, cy=0.3, entrada='zoom')
    pr = P.eout4(seg(u, ua + 0.1, ua + 0.9))                                  # la prensa baja
    ms = []
    for x, col, lim in ((-0.9, VERDE, 0.55), (0.9, ROJO_P, 1.0)):
        e = P.entrada(u, -0.25 + (0.08 if x > 0 else 0), 0.3, 'pop')
        apl = min(pr, lim)
        g = P.tfk(gota_m(col, 0.42), s=(max(0.05, e['escala']) * (1 + 0.25 * apl), max(0.05, e['escala']) * (1 - 0.45 * apl),
                                         max(0.05, e['escala']) * (1 + 0.25 * apl)), t=(x, 0.42 * (1 - 0.45 * apl), 0))
        ms += g
        yplaca = 1.7 - 0.62 * pr if x > 0 else 1.7 - 0.62 * min(pr, lim + 0.08)
        if u > ua:
            _B(ms, 0.9, 0.08, 0.7, (120, 124, 134), x, yplaca, 0, name='prensa', gloss=0.7)
            ms.append(tubo((x, yplaca + 0.08, 0), (x, 2.6, 0), r=0.04, col=CROMO, name='prensa'))
    draw_objects(fr, ms)
    boom = seg(u, ua + 0.55, ua + 0.75) if pr > 0.5 else 0.0
    if u > ua + 0.55:
        dot3(fr, (-0.9, 0.35, 0.3), r=20 + 90 * seg(u, ua + 0.55, ua + 0.9), col=(255, 120, 60), a=1 - seg(u, ua + 0.7, ua + 1.3), glow=2.5)
    pv = fr.cam.p1((-0.9, -0.15, 0))
    pr_ = fr.cam.p1((0.9, -0.15, 0))

    def ui(img, fx):
        kicker(img, 'MAGNA 87  ·  PREMIUM 91', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pv[0], pv[1] + 40, 'MAGNA · 87', eout(seg(u, -0.1, 0.15)), size=26, border=VERDE)
        pill(img, fx, pr_[0], pr_[1] + 40, 'PREMIUM · 91', eout(seg(u, -0.05, 0.2)), size=26, border=ROJO_P)
        if u < ua + 0.1:
            ke = eout(seg(u, ue, ue + 0.25))
            for xx in (pv[0], pr_[0]):
                ImageDraw.Draw(img).rounded_rectangle((xx - 120, 330, xx + 120, 362), radius=14, outline=M.scale_c(WHITE, ke), width=3)
                ImageDraw.Draw(img).rounded_rectangle((xx - 114, 336, xx - 114 + 228 * 0.93 * ke, 356), radius=10,
                                                      fill=M.scale_c(AMARILLO, ke))
            texto(img, fx, 540, 420, 'ENERGÍA ≈ IGUAL', 44, AMARILLO, ke, glow=0.5)
        else:
            texto(img, fx, 540, 300, 'aguante al apretón', 62, WHITE, eout(seg(u, ua + 0.1, ua + 0.35)), f='serif', glow=0.3)
            if boom > 0:
                texto(img, fx, pv[0], pv[1] - 420, '¡PUM!', 64, (255, 140, 80), boom, glow=0.7)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.6, 0.3), amp=16)


# 2. mira el pistón: cae la foto real del motor en corte y la cámara entra al cilindro; el pistón aprieta la mezcla
def s_piston(t, fi, u, d):
    ua = Wp(2, 'aprieta') - 0.1
    th = theta_compresion(u, ua, max(0.8, d - ua - 0.1))
    fr = Frame(camara(u, [K(-0.3, 5.6, 40, 10, ty=2.4), K(0.35, 7.4, 16, 6, ty=2.4), K(ua, 7.0, 6, 4, ty=2.5),
                          K(d, 6.8, 2, 4, ty=2.6)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    cilindro(fr, t, th, gas=AZULC)
    pg = fr.cam.p1((-0.3, 3.4, 0))
    pp = fr.cam.p1((R_CIL, yp_de(th) + 0.16, 0))

    def ui(img, fx):
        kicker(img, 'EL PISTÓN · ESQUEMA', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u < ua + 0.4:
            photo_card(img, fx, foto(), 780, 470, 420, t - u - 0.1, t, caption='Motor en corte · CC0', angle0=8.0)
        pill(img, fx, pg[0] - 160, pg[1] - 120, 'AIRE + GASOLINA', eout(seg(u, ua - 0.2, ua + 0.1)), size=24, border=AZULC)
        doodle_arrow(img, fx, pp[0] + 170, pp[1] + 150, pp[0] + 20, pp[1] + 10, t, k=seg(u, ua, ua + 0.3), col=WHITE, seed=3)
        pill(img, fx, pp[0] + 180, pp[1] + 200, 'APRIETA', eout(seg(u, ua + 0.1, ua + 0.35)), size=26, border=WHITE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. y la bujía lo prende justo a tiempo: chispa arriba y la flama baja pareja empujando el pistón
def s_chispa(t, fi, u, d):
    ub = Wp(3, 'bujia') - 0.1
    uj = Wp(3, 'justo') - 0.15
    th = 360 + 140 * ease(seg(u, uj + 0.1, d))
    fr = Frame(camara(u, [K(-0.3, 4.2, -6, 4, ty=3.3), K(0.3, 4.6, -18, 6, ty=3.2), K(uj, 6.4, -10, 4, ty=2.8),
                          K(d, 6.6, -6, 4, ty=2.7)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8, beam=0.2)
    ch = seg(u, uj - 0.05, uj + 0.05) * (1 - seg(u, uj + 0.12, uj + 0.4))
    cilindro(fr, t, th, gas=AZULC, chispa=ch, frente=seg(u, uj, uj + 0.9))
    pb = fr.cam.p1((0, Y_TECHO + 0.3, 0))

    def ui(img, fx):
        kicker(img, 'LA BUJÍA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pb[0] + 170, pb[1] - 60, 'BUJÍA', eout(seg(u, ub, ub + 0.25)), size=28, border=AMARILLO)
        doodle_circle(img, fx, pb[0], pb[1], 70, 70, t, k=seg(u, ub, ub + 0.3), col=AMARILLO, seed=2)
        texto(img, fx, 540, 330, 'justo a tiempo', 70, (255, 200, 120), eout(seg(u, uj + 0.1, uj + 0.35)), f='serif', glow=0.5)
        if u > uj + 0.5:
            pill(img, fx, 540, 1380, 'LA FLAMA EMPUJA AL PISTÓN', eout(seg(u, uj + 0.5, uj + 0.8)), size=24, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uj + 0.05, 0.3), amp=14)


# 4. si la gasolina no aguanta tanto apretón: el pistón aprieta más y se calienta (manómetro que sube)
def s_apreton(t, fi, u, d):
    ua = Wp(4, 'apreton') - 0.1
    th = theta_compresion(u, -0.2, d + 0.2) * 0.985
    fr = Frame(camara(u, [K(-0.3, 6.0, 30, 8, ty=2.8), K(0.3, 5.0, 46, 10, ty=2.9), K(ua, 4.2, 30, 8, ty=3.0),
                          K(d, 4.0, 26, 8, ty=3.0)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8, beam=0.2)
    cal = seg(u, ua - 0.3, d)
    cilindro(fr, t, th, gas=M.mixc(AZULC, (255, 160, 90), cal), rojo=0.3 * cal)

    def ui(img, fx):
        kicker(img, 'COMPRESIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.termometro(img, fx, 930, 1300, 380, 0.25 + 0.7 * cal, '', k=seg(u, 0.0, 0.2), col=(255, 120, 70))
        texto(img, fx, 540, 300, 'más apretón = más calor', 50, WHITE, eout(seg(u, ua, ua + 0.3)), glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.25 * cal, amp=8)


# 5. explota sola antes de tiempo: nace la explosión en un punto caliente con el pistón todavía subiendo
def s_sola(t, fi, u, d):
    us = Wp(5, 'sola') - 0.1
    ua = Wp(5, 'antes') - 0.1
    th = 300 + 50 * seg(u, 0.0, d)
    fr = Frame(camara(u, [K(-0.3, 4.6, -24, 6, ty=3.0), K(us, 3.6, -10, 4, ty=3.2), K(d, 3.5, -6, 4, ty=3.2)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    cilindro(fr, t, th, gas=(255, 170, 110), detona=seg(u, us, us + 0.5), rojo=0.6 * seg(u, us, us + 0.3))

    def ui(img, fx):
        texto(img, fx, 540, 260, '¡EXPLOTA SOLA!', 84, (255, 90, 60), eout(seg(u, us, us + 0.12)), glow=0.8)
        kt = eout(seg(u, ua, ua + 0.25))
        if kt > 0.01:                                                          # línea de tiempo: la chispa llega tarde
            dl = ImageDraw.Draw(img)
            dl.line([(180, 1330), (900, 1330)], fill=M.scale_c(WHITE, kt), width=4)
            for x, lab, col in ((470, 'EXPLOSIÓN', (255, 90, 60)), (760, 'CHISPA', AMARILLO)):
                dl.ellipse((x - 14, 1316, x + 14, 1344), fill=M.scale_c(col, kt))
                texto(img, fx, x, 1385, lab, 26, col, kt, f='mono', glow=0.4)
            texto(img, fx, 540, 1255, 'ANTES DE TIEMPO', 40, (255, 90, 60), kt, f='mono', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us, 0.45), amp=26)


# 6. el cascabeleo: ondas de presión que rebotan, el pistón tiembla y la gráfica de presión vibra (zoom digital)
def s_cascabeleo(t, fi, u, d):
    ug = Wp(6, 'golpeteo') - 0.1
    th = 350 + 6 * math.sin(t * 9)
    fr = Frame(camara(u, [K(-0.3, 6.6, 20, 6, ty=2.8), K(0.3, 5.8, 8, 4, ty=2.8), K(ug, 4.0, -6, 4, ty=3.2),
                          K(d, 3.9, -8, 4, ty=3.2)], cy=0.56))
    space(fr, t, floor=None, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'CASCABELEO', u, t0=-0.15, cy=0.24, entrada='sube')
    cilindro(fr, t, th, gas=(255, 170, 110), detona=0.6, ondas=1.0, temblor=1.0, rojo=0.5)
    pp = fr.cam.p1((0, yp_de(th) + 0.2, 0))

    def ui(img, fx):
        kicker(img, 'DETONACIÓN · «CASCABELEO»', 150, seg(u, -0.1, 0.2), col=(255, 180, 140))
        kg = eout(seg(u, 0.3, 0.6))
        if kg > 0.01:                                                          # traza de presión con «timbre»
            dl = ImageDraw.Draw(img)
            x0, y0, w = 160, 1330, 760
            pts = []
            for i in range(160):
                s_ = i / 159
                if s_ > kg:
                    break
                pk = math.exp(-((s_ - 0.45) / 0.09) ** 2)
                ring = math.exp(-max(0, s_ - 0.45) * 9) * math.sin(s_ * 120) * (s_ > 0.45)
                pts.append((x0 + w * s_, y0 - 110 * pk - 45 * ring))
            if len(pts) > 1:
                dl.line(pts, fill=(255, 190, 110), width=4)
            texto(img, fx, 540, 1400, 'PRESIÓN QUE «TIMBRA»', 26, GRIS, kg, f='mono', glow=0.2)
        if u > ug:
            doodle_circle(img, fx, pp[0], pp[1], 200, 90, t, k=seg(u, ug, ug + 0.3), col=(255, 120, 80), seed=5)
            rec_frame(img, t, seg(u, ug - 0.1, ug), zoom_label='x1.8')
        esquema(img, fx, 1.0, y=1470)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, 0.35 + 0.25 * math.sin(t * 40) ** 2, amp=7)


# 7-8. la prueba: el mismo motor con Magna (verde) y con Premium (rojo), lado a lado, encendiendo a tiempo
def _par(t, u, d, cual, claves):
    fr = Frame(camara(u, claves, cy=0.56))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    ciclo = (u * 300) % 360
    th = 180 + ciclo
    for x0, gas, on in ((-1.0, VERDE, True), (1.0, ROJO_P, cual == 2)):
        if not on:
            continue
        e = P.entrada(u, -0.25 if x0 < 0 else 0.0, 0.3, 'pop')
        sc = 0.62 * max(0.05, e['escala'])
        fase = ciclo / 360
        cilindro(fr, t, th, gas=gas, x0=x0, s=sc, chispa=seg(fase, 0.97, 1.0) + (1 - seg(fase, 0.0, 0.08)) * (fase < 0.1),
                 frente=seg(fase, 0.0, 0.35) * (fase < 0.4), seed=4 if x0 < 0 else 9)
    return fr


def s_magna(t, fi, u, d):
    um = Wp(7, 'magna') - 0.1
    fr = _par(t, u, d, 1, [K(-0.3, 7.5, -30, 8, tx=-1.0, ty=1.7), K(0.3, 5.6, -8, 6, tx=-1.0, ty=1.6),
                           K(d, 5.4, -4, 6, tx=-1.0, ty=1.6)])
    pm = fr.cam.p1((-1.0, 0.7, 0))

    def ui(img, fx):
        kicker(img, 'LA PRUEBA · MISMO MOTOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 290, 'motor normal', 66, WHITE, eout(seg(u, 0.4, 0.65)), f='serif', glow=0.3)
        pill(img, fx, pm[0], pm[1] + 60, 'MAGNA · 87', eout(seg(u, um, um + 0.25)), size=30, border=VERDE)
        esquema(img, fx, 1.0, y=1470)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_premium(t, fi, u, d):
    up = Wp(8, 'premium') - 0.1
    fr = _par(t, u, d, 2, [K(-0.3, 6.0, 20, 6, tx=1.0, ty=1.6), K(0.3, 8.6, 6, 6, tx=0.0, ty=1.6),
                           K(d, 8.4, 2, 6, tx=0.0, ty=1.6)])
    pm = fr.cam.p1((-1.0, 0.7, 0))
    pr = fr.cam.p1((1.0, 0.7, 0))

    def ui(img, fx):
        kicker(img, 'LA PRUEBA · MISMO MOTOR', 150, 1.0, col=AZULC)
        pill(img, fx, pm[0], pm[1] + 60, 'MAGNA · 87', 1.0, size=26, border=VERDE)
        pill(img, fx, pr[0], pr[1] + 60, 'PREMIUM · 91', eout(seg(u, up, up + 0.25)), size=26, border=ROJO_P)
        texto(img, fx, 540, 300, 'VS', 110, WHITE, eout(seg(u, 0.1, 0.25)), glow=0.5)
        esquema(img, fx, 1.0, y=1470)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.25), amp=12)


# 9. empatan: casi la misma energía por litro y la misma fuerza (gráfica que crece + «EMPATE» de cristal)
def s_empate(t, fi, u, d):
    ue = Wp(9, 'energia') - 0.1
    uf = Wp(9, 'fuerza') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, 0, 6, ty=1.0), K(0.4, 5.2, 12, 6, ty=1.0), K(uf, 4.6, -12, 6, ty=1.0),
                          K(d, 4.5, -16, 6, ty=1.0)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'EMPATE', u, t0=-0.2, cy=0.28, entrada='golpe')

    def ui(img, fx):
        chart_grow(img, fx, (150, 640, 930, 1210), [100, 100], ['MAGNA', 'PREMIUM'], t - u + ue - 0.3, t, unit='',
                   title_txt='ENERGÍA POR LITRO · MAGNA = 100', vmax=115, line=False)
        kf = eout(seg(u, uf, uf + 0.3))
        if kf > 0.01:
            texto(img, fx, 540, 1300, 'MISMA FUERZA', 64, WHITE, kf, glow=0.45)
            pill(img, fx, 540, 1395, 'EN UN MOTOR QUE PIDE MAGNA · PRUEBAS DE AAA (EE. UU.)', kf, size=20, border=(200, 200, 210),
                 dot=False)
        kicker(img, 'RESULTADO', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.0, 0.3), amp=14)


# 10. segundo gancho: el error — pagar Premium en un carro que pide Magna (la pistola roja entra; la tapa dice MAGNA)
def s_error(t, fi, u, d):
    up = Wp(10, 'pagar') - 0.1
    um = Wp(10, 'magna') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.4, 60, 12, tx=-0.6, ty=0.7), K(0.4, 5.6, 40, 10, tx=-0.6, ty=0.7),
                          K(um - 0.2, 4.6, 30, 8, tx=-0.9, ty=0.7), K(um, 3.6, 18, 6, tx=-0.75, ty=0.75, tz=0.45),
                          K(d, 3.5, 14, 6, tx=-0.75, ty=0.75, tz=0.45)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5)
    ms = auto(tapa=seg(u, 0.2, 0.5))
    kp = P.eout4(seg(u, up, up + 0.5))
    ms += P.tfk(pistola(ROJO_P), s=0.55, ry=90, t=(-0.8, 0.22, 1.75 - 0.52 * kp))
    draw_objects(fr, ms)
    pt = fr.cam.p1((-0.79, 0.85, 0.65))

    def ui(img, fx):
        texto(img, fx, 540, 250, 'EL ERROR', 110, RED, eout(seg(u, 0.0, 0.12)), glow=0.8)
        kicker(img, 'QUE TE CUESTA DINERO', 370, seg(u, 0.2, 0.45), col=(255, 160, 150))
        pill(img, fx, pt[0], pt[1] - 90, 'ESTE CARRO PIDE MAGNA · 87', eout(seg(u, um, um + 0.25)), size=26, border=VERDE)
        if u > up + 0.3:
            pill(img, fx, 540, 1380, 'LE PONEN PREMIUM', eout(seg(u, up + 0.3, up + 0.55)), size=28, border=ROJO_P)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.0, 0.35), golpe_k(u, um, 0.3)), amp=22)


# 11. en noviembre, el litro de Premium cuesta casi 5 pesos más (letrero de precios de la gasolinera)
def s_precio(t, fi, u, d):
    u5 = Wp(11, 'cinco') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.0, -30, 4, ty=2.0), K(0.3, 5.6, -10, 2, ty=2.0), K(u5, 4.4, 4, 2, ty=2.0),
                          K(d, 4.3, 6, 2, ty=2.0)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8)
    e = P.entrada(u, -0.25, 0.3, 'cae')
    ms = []
    _B(ms, 1.9, 2.9, 0.3, (26, 28, 34), 0, 0.45 - e['dy'] * 0.5, 0, name='letrero', gloss=0.5)
    _B(ms, 0.3, 0.45, 0.25, (60, 62, 70), 0, 0.0, 0, name='poste', gloss=0.4)
    draw_objects(fr, ms)
    p1 = fr.cam.p1((0, 2.65 - e['dy'] * 0.5, 0.16))
    p2 = fr.cam.p1((0, 1.7 - e['dy'] * 0.5, 0.16))
    sc = clamp((p2[1] - p1[1]) / 330)

    def ui(img, fx):
        kicker(img, 'PROMEDIO NACIONAL · CNE Y PROFECO · 15-NOV-2026', 150, seg(u, -0.1, 0.2), col=AZULC)
        for (px, py), nom, val, col in ((p1[:2], 'MAGNA', '23.70', VERDE), (p2[:2], 'PREMIUM', '28.59', ROJO_P)):
            k = seg(u, -0.1, 0.15)
            texto(img, fx, px, py - 60 * sc, nom, int(40 * max(0.5, sc)), col, k, f='mono', glow=0.6)
            texto(img, fx, px, py + 30 * sc, '$' + val, int(110 * max(0.5, sc)), WHITE, k, f='mono', glow=0.4)
        P.numero_golpe(img, fx, '+$4.89', 1390, seg(u, u5, u5 + 0.15), size=170, col=ROJO_P)
        texto(img, fx, 540, 1520, 'POR LITRO', 34, GRIS, eout(seg(u, u5 + 0.2, u5 + 0.4)), f='mono', glow=0.2)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.05, 0.25), golpe_k(u, u5 + 0.15, 0.35)), amp=20)


# 12. en un tanque de 40 litros son casi 200 pesos… por nada (el tanque se llena y los billetes salen volando)
def s_tanque(t, fi, u, d):
    u2 = Wp(12, 'doscientos') - 0.1
    un = Wp(12, 'nada') - 0.15
    lit = 40 * ease(seg(u, 0.0, u2))
    fr = Frame(camara(u, [K(-0.3, 5.4, 34, 14, ty=0.9), K(0.4, 4.8, 18, 10, ty=0.9), K(u2, 4.0, -12, 8, ty=1.0),
                          K(d, 3.9, -16, 8, ty=1.0)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, '$196', u, t0=u2, cy=0.37, entrada='zoom')
    a, b, c = 1.0, 0.75, 0.6                                                     # el tanque de línea
    cs = [(-a, 0, -c), (a, 0, -c), (a, 0, c), (-a, 0, c)]
    for y in (0.0, 2 * b):
        line3(fr, [(x, y, z) for x, _, z in cs + cs[:1]], col=WHITE, w=2.6, a=0.85, glow=0.7)
    for x, _, z in cs:
        line3(fr, [(x, 0, z), (x, 2 * b, z)], col=WHITE, w=2.6, a=0.85, glow=0.7)
    h = 2 * b * lit / 40.0
    ms = []
    if h > 0.01:
        liq = named(M3.box(2 * a - 0.04, h, 2 * c - 0.04, ROJO_P, shadow=0, gloss=0.9), 'liquido', rim=0.9, gloss=0.9)
        ms.append(liq)
    draw_objects(fr, ms)
    for j in range(8):                                                         # los billetes que se van «por nada»
        if u < un:
            break
        ph = seg(u, un + 0.05 * j, un + 0.9 + 0.05 * j)
        p = np.array([0.6 * math.sin(j * 2.1), 1.6 + 2.0 * ph, 0.5 * math.cos(j * 1.7)])
        if ph < 1:
            line3(fr, [p + np.array([-0.18, 0, 0]), p + np.array([0.18, 0.04 * math.sin(t * 9 + j), 0])], col=DINERO, w=14,
                  a=1 - ph, glow=0.8)

    def ui(img, fx):
        kicker(img, 'UN TANQUE DE 40 LITROS', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 250, f'{lit:4.1f} L', 92, WHITE, 1.0, f='mono', glow=0.3)
        texto(img, fx, 540, 345, f'+${4.89 * lit:,.0f} de más'.replace(',', ' '), 60, ROJO_P, seg(u, 0.1, 0.3), f='mono', glow=0.5)
        texto(img, fx, 540, 1380, 'por nada', 80, WHITE, eout(seg(u, un, un + 0.25)), f='serif', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u2, 0.3), amp=16)


# 13. y al revés también falla: un motor turbo que pide Premium (el turbo gira y mete más aire)
def turbo_m(giro):
    ms = [named(M3.torus(0.55, 0.22, (170, 172, 180), nu=32, nv=10, gloss=0.8).tf(rx=90, t=(0, 1.0, 0)), 'caracol', rim=0.8, gloss=0.8),
          named(M3.cyl(0.32, 0.5, (150, 152, 160), n=24, shadow=0, gloss=0.8).tf(rx=90, t=(0, 1.0, 0.25)), 'caracol', rim=0.8),
          tubo((0.55, 1.0, 0), (1.6, 1.0, 0), r=0.16, col=(150, 152, 160), name='tubo')]
    for j in range(8):                                                       # las aspas que giran
        a = giro + j * math.pi / 4
        ms.append(named(M3.box(0.04, 0.3, 0.18, (230, 232, 238), shadow=0, gloss=0.9, base=False).tf(
            rz=math.degrees(a), t=(0.17 * math.cos(a + math.pi / 2), 1.0 + 0.17 * math.sin(a + math.pi / 2), 0.3)), 'aspa', rim=0.9))
    return ms


def s_turbo(t, fi, u, d):
    ut = Wp(13, 'turbo') - 0.1
    up = Wp(13, 'premium') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, 60, 10, ty=1.0, tx=0.4), K(0.4, 4.2, 30, 6, ty=1.0, tx=0.4),
                          K(ut, 3.4, 6, 4, ty=1.0, tx=0.3), K(d, 3.3, 2, 4, ty=1.0, tx=0.3)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.4)
    draw_objects(fr, turbo_m(t * (6 + 30 * seg(u, ut, ut + 0.6))))
    for j in range(6):                                                       # el aire que entra apretado
        ph = (t * 1.8 + j / 6) % 1.0
        y = 1.0 + 0.35 * math.sin(j * 2.3)
        line3(fr, [(0.6 + 1.0 * ph, y, 0.1), (0.75 + 1.0 * ph, y, 0.1)], col=AZULC, w=3, a=(1 - ph) * seg(u, ut, ut + 0.3), glow=1.2)
    pt = fr.cam.p1((0, 1.7, 0))

    def ui(img, fx):
        texto(img, fx, 540, 270, 'al revés', 90, WHITE, eout(seg(u, 0.0, 0.2)), f='serif', glow=0.4)
        pill(img, fx, pt[0], pt[1] - 40, 'TURBO · METE MÁS AIRE', eout(seg(u, ut, ut + 0.25)), size=26, border=AZULC)
        pill(img, fx, 540, 1380, 'PIDE PREMIUM', eout(seg(u, up, up + 0.25)), size=30, border=ROJO_P)
        esquema(img, fx, 1.0, y=1470)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. con Magna, cascabelea (el cilindro del turbo con gas verde detona y tiembla)
def s_cascabelea(t, fi, u, d):
    uc = Wp(14, 'cascabelea') - 0.1
    th = 330 + 20 * seg(u, 0.0, d)
    fr = Frame(camara(u, [K(-0.3, 4.4, 40, 6, ty=3.0), K(0.3, 5.2, 14, 4, ty=2.9), K(d, 5.1, 10, 4, ty=2.9)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    det = seg(u, uc - 0.2, uc + 0.3)
    cilindro(fr, t, th, gas=VERDE, detona=det, ondas=det, temblor=det, rojo=0.5 * det)

    def ui(img, fx):
        pill(img, fx, 540, 230, 'CON MAGNA', eout(seg(u, 0.0, 0.2)), size=32, border=VERDE)
        texto(img, fx, 540, 340, '¡CASCABELEA!', 88, (255, 110, 70), eout(seg(u, uc, uc + 0.12)), glow=0.8)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, det * (0.45 + 0.3 * math.sin(t * 50) ** 2), amp=12)


# 15. su computadora lo oye con un sensor, atrasa la chispa para protegerlo… y le quita fuerza
def s_sensor(t, fi, u, d):
    us = Wp(15, 'sensor') - 0.1
    ua = Wp(15, 'atrasa') - 0.1
    uq = Wp(15, 'quita') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.6, -40, 14, ty=0.9), K(0.4, 4.6, -20, 10, ty=0.9), K(us, 3.4, -6, 8, ty=0.8, tx=-0.3),
                          K(ua, 4.8, 18, 10, ty=1.0), K(uq, 4.6, 26, 10, ty=1.0), K(d, 4.5, 28, 10, ty=1.0)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, 'SENSOR', u, t0=us, cy=0.27, entrada='golpe')
    ms = []
    _B(ms, 1.6, 1.0, 1.0, (120, 124, 132), -0.4, 0.0, 0, name='bloque', gloss=0.5)     # el bloque del motor
    for j in range(4):
        _B(ms, 0.3, 0.12, 0.6, (90, 94, 102), -0.95 + j * 0.37, 1.0, 0, name='bloque', gloss=0.5)
    ms.append(named(M3.cyl(0.11, 0.14, (60, 64, 72), n=14, shadow=0, gloss=0.7).tf(rx=90, t=(-0.4, 0.5, 0.5)), 'sensor', rim=0.9,
                    glow=M.scale_c(CYAN, 0.6 * seg(u, us, us + 0.3))))
    _B(ms, 0.7, 0.18, 0.5, (40, 44, 52), 1.25, 0.0, 0.2, name='ecu', gloss=0.6)           # la computadora
    _B(ms, 0.26, 0.04, 0.26, (30, 30, 34), 1.25, 0.18, 0.2, name='chip', gloss=0.8, glow=M.scale_c(CYAN, 0.5 + 0.5 * math.sin(t * 8) ** 2))
    draw_objects(fr, ms)
    line3(fr, [(-0.4, 0.5, 0.64), (0.3, 0.5, 0.8), (0.9, 0.2, 0.5), (1.2, 0.2, 0.2)], col=CYAN, w=2.6, a=seg(u, us, us + 0.3), glow=1.2,
          frac=seg(u, us, us + 0.5))
    pse = fr.cam.p1((-0.4, 0.5, 0.6))
    pe = fr.cam.p1((1.25, 0.3, 0.2))

    def ui(img, fx):
        kicker(img, 'SENSOR DE DETONACIÓN · COMPUTADORA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pse[0] - 60, pse[1] + 90, 'LO «OYE»', eout(seg(u, us, us + 0.25)), size=24, border=CYAN)
        pill(img, fx, pe[0] + 20, pe[1] + 80, 'COMPUTADORA', eout(seg(u, 0.1, 0.35)), size=24, border=(200, 200, 210), dot=False)
        ka = eout(seg(u, ua, ua + 0.3))
        if ka > 0.01:                                                          # el avance de la chispa se atrasa (ejemplo)
            cx, cy, r = 250, 1200, 110
            dl = ImageDraw.Draw(img)
            dl.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=M.scale_c(WHITE, ka), width=5)
            gr = 20 - 10 * P.eout4(seg(u, ua + 0.3, ua + 0.9))
            a = math.radians(270 - (gr - 10) * 5)
            dl.line([(cx, cy), (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a))], fill=M.scale_c(AMARILLO, ka), width=7)
            texto(img, fx, cx, cy + 50, f'{gr:.0f}°', 48, AMARILLO, ka, f='mono', glow=0.5)
            texto(img, fx, cx, cy - 165, 'CHISPA', 28, GRIS, ka, f='mono', glow=0.2)
            pill(img, fx, cx, cy + 120, 'LA ATRASA', ka, size=22, border=AMARILLO, dot=False)
        kq = eout(seg(u, uq, uq + 0.3))
        if kq > 0.01:
            dl = ImageDraw.Draw(img)
            x0, y0 = 600, 1150
            dl.rounded_rectangle((x0, y0, x0 + 300, y0 + 44), radius=18, outline=M.scale_c(WHITE, kq), width=3)
            lv = 0.95 - 0.35 * seg(u, uq + 0.1, uq + 0.6)
            dl.rounded_rectangle((x0 + 6, y0 + 6, x0 + 6 + 288 * lv, y0 + 38), radius=14, fill=M.scale_c((255, 110, 80), kq))
            texto(img, fx, x0 + 150, y0 + 90, '− FUERZA', 46, (255, 110, 80), kq, glow=0.5)
        esquema(img, fx, 1.0, y=1440, txt='ESQUEMA · GRADOS DE EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us, 0.3), amp=14)


# 16. ¿cuál le toca al tuyo? viene en el manual o en la tapa del tanque (la tapa se abre y deja ver la etiqueta)
def s_tapa(t, fi, u, d):
    um = Wp(16, 'manual') - 0.1
    ut = Wp(16, 'tapa') - 0.1
    fr = Frame(camara(u, [K(-0.3, 6.0, -50, 12, ty=0.8), K(0.4, 5.2, 50, 12, ty=0.8), K(ut - 0.3, 4.8, 40, 10, ty=0.8, tx=-0.6),
                          K(ut, 3.1, 14, 5, ty=0.72, tx=-0.8, tz=0.5), K(d, 3.0, 12, 5, ty=0.72, tx=-0.8, tz=0.5)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'MANUAL', u, t0=um, cy=0.22, entrada='sube')
    draw_objects(fr, auto(tapa=seg(u, ut, ut + 0.35)))
    ph = fr.cam.p1((-0.79, 0.66, 0.65))

    def ui(img, fx):
        texto(img, fx, 540, 270, '¿cuál le toca al tuyo?', 64, WHITE, eout(seg(u, 0.0, 0.25)), f='serif', glow=0.35)
        km = eout(seg(u, um, um + 0.3)) * (1 - seg(u, ut, ut + 0.2))
        if km > 0.01:                                                          # el manual (libro de línea)
            dl = ImageDraw.Draw(img)
            x0, y0 = 360, 1180
            dl.rounded_rectangle((x0, y0, x0 + 360, y0 + 240), radius=12, outline=M.scale_c(WHITE, km), width=4)
            dl.line([(x0 + 180, y0), (x0 + 180, y0 + 240)], fill=M.scale_c(WHITE, km), width=3)
            for j in range(4):
                dl.line([(x0 + 30, y0 + 50 + j * 40), (x0 + 150, y0 + 50 + j * 40)], fill=M.scale_c(GRIS, km), width=3)
            texto(img, fx, x0 + 270, y0 + 120, '87', 70, VERDE, km, f='mono', glow=0.5)
        kt = eout(seg(u, ut + 0.3, ut + 0.6))
        if kt > 0.01:
            dl = ImageDraw.Draw(img)
            dl.rounded_rectangle((ph[0] - 46, ph[1] - 30, ph[0] + 46, ph[1] + 30), radius=8, fill=(12, 14, 16),
                                 outline=M.scale_c(VERDE, kt), width=4)
            texto(img, fx, ph[0], ph[1], '87', 40, VERDE, kt, f='mono', glow=0.6)
            pill(img, fx, ph[0], ph[1] - 150, 'OCTANAJE MÍNIMO · 87', kt, size=28, border=VERDE)
            esquema(img, fx, kt, y=1440, txt='ETIQUETA DE EJEMPLO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. mándaselo a quien le pone Premium para que corra más (el carro con la pistola roja y líneas de velocidad)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.6, 70, 8, ty=0.7), K(0.4, 5.6, 35, 6, ty=0.7), K(d, 5.5, 30, 6, ty=0.7)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.0)
    for j in range(10):                                                      # líneas de velocidad (que no sirven)
        ph = (t * 2.2 + j / 10) % 1.0
        z = -0.6 + 1.2 * (j % 5) / 4
        y = 0.3 + 0.9 * ((j * 7) % 5) / 5
        line3(fr, [(-2.0 - 3 * ph, y, z), (-2.8 - 3 * ph, y, z)], col=WHITE, w=2.4, a=0.7 * (1 - ph), glow=0.8)
    draw_objects(fr, auto(tapa=1.0) + P.tfk(pistola(ROJO_P), s=0.55, ry=90, t=(-0.8, 0.22, 1.23)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien', 'sans'), ('le pone Premium «para que corra».', 'serif')], 230,
                       seg(u, 0.0, 0.15), size=62)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45),
                sfx=[(-1.6, 'riser', 0.5)] + [(-3.6 + 0.15 * j, 'tick', 0.3) for j in range(21)] +
                    [(U_CLAVA, 'sub', 1.0), (U_CLAVA, 'bass', 0.9), (0.25, 'bass', 0.7), (1.3, 'scribble', 0.6)]),
           dict(desde=1, fn=s_octanos, tr='golpe', sfx=[(1.6, 'chime_a', 0.5), (3.1, 'thud', 0.7), (3.7, 'burst', 0.8)]),
           dict(desde=2, fn=s_piston, tr='zoom', c=(0.5, 0.62), sfx=[(0.0, 'slap', 0.8), (1.0, 'whoosh_suave', 0.6), (1.9, 'click', 0.5)]),
           dict(desde=3, fn=s_chispa, tr='iris', c=(0.5, 0.3), sfx=[(1.0, 'tick2', 0.8), (1.05, 'burst', 0.7), (1.1, 'sub', 0.7)]),
           dict(desde=4, fn=s_apreton, tr='whip', sfx=[(0.2, 'riser', 0.5), (1.4, 'tick', 0.5)]),
           dict(desde=5, fn=s_sola, tr='glitch', sfx=[(0.3, 'sub', 1.0), (0.3, 'burst', 0.8), (1.2, 'tick', 0.6)]),
           dict(desde=6, fn=s_cascabeleo, tr='flash', sfx=[(0.1 + 0.11 * j, 'tick2', 0.45) for j in range(26)] +
                [(1.5, 'click', 0.7), (1.6, 'scribble', 0.5)]),
           dict(desde=7, fn=s_magna, tr='cubo', sfx=[(0.1, 'whoosh_suave', 0.5)] + [(0.3 + 1.2 * j, 'thud', 0.35) for j in range(2)]),
           dict(desde=8, fn=s_premium, tr='wipe', sfx=[(0.25, 'bass', 0.7), (0.6, 'chime_b', 0.4)]),
           dict(desde=9, fn=s_empate, tr='mosaico', sfx=[(0.0, 'bass', 0.6), (1.1, 'chime_a', 0.5), (1.4, 'chime_b', 0.5),
                                                       (2.6, 'chime_c', 0.5)]),
           dict(desde=10, fn=s_error, tr='rompe', c=(0.5, 0.35), sfx=[(0.0, 'bass', 0.9), (0.0, 'digital', 0.5), (2.0, 'click', 0.6),
                                                                   (2.6, 'sub', 0.7)]),
           dict(desde=11, fn=s_precio, tr='deslizar', sfx=[(0.05, 'thud', 0.7), (2.4, 'sub', 0.9), (2.4, 'bass', 0.8)]),
           dict(desde=12, fn=s_tanque, tr='push', c=(0.5, 0.72), sfx=[(0.1, 'whoosh_suave', 0.6), (1.7, 'bass', 0.9),
                                                                   (3.6, 'slap', 0.6), (3.7, 'whoosh', 0.6)]),
           dict(desde=13, fn=s_turbo, tr='remolino', sfx=[(0.1, 'whoosh', 0.6), (2.1, 'riser', 0.6), (2.9, 'chime_a', 0.4)]),
           dict(desde=14, fn=s_cascabelea, tr='zoom', c=(0.5, 0.45), sfx=[(0.6 + 0.1 * j, 'tick2', 0.5) for j in range(10)] + [(0.7, 'sub', 0.8)]),
           dict(desde=15, fn=s_sensor, tr='rebanadas', sfx=[(1.0, 'cristal', 0.0), (1.0, 'digital', 0.5), (2.4, 'click', 0.6),
                                                          (3.3, 'tick', 0.6), (4.3, 'thud', 0.8)]),
           dict(desde=16, fn=s_tapa, tr='giro', sfx=[(1.8, 'shimmer', 0.4), (2.6, 'click', 0.8), (2.9, 'chime_b', 0.5)]),
           dict(desde=17, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7), (0.3, 'whoosh', 0.6)]),
           dict(desde=18, loop=True, tr='whip_izq')]

if __name__ == '__main__':
    montaje.cli(globals())
