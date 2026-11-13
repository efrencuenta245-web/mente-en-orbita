"""Reel sáb 14-nov-2026 10:00 — «Tu moto truena más… pero no corre más.» (escape sin mofle: ruido, truenos, oído y multa).
Pedido por Efrén el 12-nov («haz el de tu moto truena más»); ocupa el hueco del vocho (el vocho se corre).
Comunidad: moteros (decisión de Efrén del 10-nov: vehículos y comunidades mexicanas por dentro).
Inicio tipo 9 (giro 360° con destellos): la moto REAL (foto 3D) da una vuelta completa; en cada canto un destello y un
trueno con flamazo por el escape; queda de frente al título con «TRUENA» de cristal detrás. El final regresa al giro (loop).
Voz Isaac (eleven_v4), 69.9 s. Datos y fuentes: guiones/2026-11-14_moto.txt.
Fotos reales (Wikimedia Commons): moto de 125 cc con escape cromado (Pascal-André, CC0; marcas difuminadas y color
corregido) y Honda CG125 roja (Urbancowboy89, CC BY-SA 3.0; logos difuminados). La moto de malla de las escenas de
mecánica, el mofle por dentro y los truenos son RECREACIÓN.
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import foto3d as F3
import italika as IT
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'moto'
TXT = ['Tu moto truena más… pero no corre más.',
       'Le quitaste el mofle para que se oyera brava, ¿verdad?',
       'Pero el escape de fábrica no es un tubo cualquiera: está hecho para tu motor.',
       'Saca el humo de cada explosión para que no se quede atrapado adentro.',
       'Mira la prueba: la misma moto, con mofle y sin mofle.',
       'Sin mofle truena muchísimo más… pero, según ingenieros de Kawasaki, casi no gana fuerza.',
       'Y hasta puede calentar más tu motor.',
       'Y esos truenos que tanto te gustan… son gasolina que explota en el tubo, no en el motor.',
       'Adentro del cilindro, la explosión empuja el pistón; en el escape, solo hace ruido y gasta gasolina.',
       'Por dentro, el mofle tiene cámaras donde el sonido rebota y se apaga.',
       'Por eso la norma mexicana limita una moto nueva a 86 decibeles, u 89 si es grande.',
       'Y tu oído: con cada 3 decibeles de más, aguanta la mitad del tiempo; a 100, solo 15 minutos al día.',
       'En la Ciudad de México, el escape modificado para hacer ruido es multa de más de 2 000 pesos.',
       'Mándaselo a tu compa que le quitó el mofle a su moto,',
       'porque su moto truena más… pero no corre más.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-14_moto_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_moto.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-14_moto_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
FUEGO = (255, 170, 60)
AZULC = (150, 210, 230)
VERDE = (120, 240, 160)
AZUL_M = (36, 62, 140)
CROMO = (214, 216, 222)
GRIS = (150, 150, 160)
HUMO = (175, 178, 186)
GASOL = (255, 214, 90)

# ------------------------------------------------------------------ fotos reales en 3D (Wikimedia Commons)
FOTOS = os.path.join(HERE, 'img', 'moto')
CRED = {'cromo': 'FOTO: PASCAL-ANDRÉ · CC0 · WIKIMEDIA COMMONS',
        'roja': 'FOTO: URBANCOWBOY89 · CC BY-SA 3.0 · WIKIMEDIA COMMONS'}
VEH = {'cromo': F3.preparar(f'{FOTOS}/moto_i_cromo.jpg', 'moto_cromo', recorte=(0.05, 0.18, 0.92, 0.78)),
       'roja': F3.preparar(f'{FOTOS}/moto_i_roja.jpg', 'moto_roja', recorte=(0.05, 0.2, 0.98, 0.95))}
PUNTA = {'cromo': (0.035, 0.735)}          # salida del escape en la foto recortada (fracción del ancho y del alto)


def veh(img, fx, n, cx, piso, alto, yaw=0.0, pitch=0.15, t=0.0, alfa=1.0, xray=0.0, borde=0.55):
    a = VEH[n]
    luz = (-0.65 + 0.55 * math.sin(t * 0.9), -0.62)
    return F3.dibujar(img, a, cx, piso - alto * 0.5, alto, yaw=yaw, pitch=pitch, luz=luz, fx=fx, alfa=alfa,
                      reflejo=0.22, borde=borde, piso_y=piso, xray=xray)


def veh_giro(img, fx, n, cx, piso, alto, ang, t=0.0):
    """La foto 3D girando sobre su eje vertical (vuelta de tornamesa): se angosta con cos(ang) y se voltea de espaldas.
    Devuelve la salida del escape en pantalla (x, y) o None."""
    a = VEH[n]
    c = math.cos(math.radians(ang))
    yaw = clamp(math.sin(math.radians(ang)) * 1.0, -1, 1)
    rgb, al, bo = F3.render_activo(a, yaw=yaw, pitch=0.15, esc=1.0, luz=(-0.6 + 0.8 * math.sin(math.radians(ang)), -0.6))
    s = alto / a.h
    W2, H2 = max(2, int(a.w * s * max(0.04, abs(c)))), max(2, int(a.h * s))
    rgb = cv2.resize(rgb, (W2, H2), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (W2, H2), interpolation=cv2.INTER_AREA)
    if c < 0:
        rgb, al = rgb[:, ::-1], al[:, ::-1]
        rgb = rgb * 0.72
    x0, y0 = int(cx - W2 / 2), int(piso - H2)
    can = np.asarray(img, np.float32).copy()
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(img.size[0], x0 + W2), min(img.size[1], y0 + H2)
    if X1 > X0 and Y1 > Y0:
        sub_a = al[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
        sub = rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        can[Y0:Y1, X0:X1] = can[Y0:Y1, X0:X1] * (1 - sub_a) + sub * sub_a
        img.paste(Image.fromarray(np.clip(can, 0, 255).astype(np.uint8)))
    pf, pv = PUNTA.get(n, (0.03, 0.73))
    fxp = pf if c >= 0 else 1 - pf
    return (x0 + fxp * W2, y0 + pv * H2, -1 if c >= 0 else 1)


def punta_foto(r, n='cromo'):
    x0, y0, w, h = r
    pf, pv = PUNTA[n]
    return x0 + pf * w, y0 + pv * h


def credito(img, txt, y=1872, k=1.0):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((540, y), txt, font=M.font('mono', 19), fill=M.scale_c((150, 150, 158), k), anchor='mm')


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
K = IT.K
camara = IT.camara
golpe_k = IT.golpe_k
sacudir = IT.sacudir
texto = IT.texto


def llamarada(img, fx, x, y, k, t, dirx=-1, escala=1.0, seed=0):
    """Trueno del escape: flamazo naranja con núcleo azul-blanco y chispas, apuntando hacia dirx."""
    if k <= 0.02:
        return
    rng = np.random.RandomState(seed + int(t * 24) % 7)
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    L = 230 * escala * (0.55 + 0.45 * k)
    capas = [((255, 80, 20), 1.0, 1.0, 0.55), ((255, 160, 40), 0.72, 0.8, 0.8), ((255, 236, 170), 0.42, 0.55, 1.0),
             ((170, 210, 255), 0.18, 0.25, 1.0)]
    for col, ww, ll, aa in capas:
        h = 70 * escala * ww * (0.7 + 0.3 * k)
        lx = L * ll * (0.85 + 0.3 * rng.rand())
        pts = [(x, y - h * 0.35)]
        n = 9
        for i in range(1, n + 1):
            s = i / n
            jit = (rng.rand() - 0.5) * h * 0.5
            pts.append((x + dirx * lx * s, y - h * (1 - s) * 0.9 + jit))
        for i in range(n, 0, -1):
            s = i / n
            jit = (rng.rand() - 0.5) * h * 0.5
            pts.append((x + dirx * lx * s * 0.92, y + h * (1 - s) * 0.9 + jit))
        pts.append((x, y + h * 0.35))
        cc = M.scale_c(col, k * aa)
        df.polygon(pts, fill=cc)
        if aa >= 0.8:
            d.polygon(pts, fill=M.scale_c(col, k * 0.8))
    for i in range(14):
        ph = rng.rand()
        sx = x + dirx * L * (0.4 + 0.9 * ph)
        sy = y + (rng.rand() - 0.5) * 160 * escala
        r = 3 + 3 * rng.rand()
        df.ellipse((sx - r, sy - r, sx + r, sy + r), fill=M.scale_c((255, 200, 120), k))


def humo_puff(fr, p, r, k, t, seed=0, col=HUMO):
    rng = np.random.RandomState(seed)
    for j in range(9):
        off = np.array([(rng.rand() - 0.5) * r, (rng.rand() - 0.5) * r * 0.8, (rng.rand() - 0.5) * r])
        dot3(fr, tuple(np.asarray(p) + off), r=5 + 7 * rng.rand(), col=col, a=0.75 * k, glow=0.5)


# ------------------------------------------------------------------ moto de malla (recreación) con mofle desmontable
TUBO_A = np.array([0.45, 0.25, 0.16])          # el escape de IT.moto baja del motor y va hacia atrás
TUBO_B = np.array([-0.75, 0.42, 0.18])
MOF_A = np.array([-0.18, 0.34, 0.18])          # el mofle (cilindro grueso) va sobre el tramo de atrás
MOF_B = np.array([-0.86, 0.43, 0.18])


def mofle_mesh(off=(0, 0, 0), giro=0.0, col=CROMO):
    off = np.asarray(off, float)
    a, b = MOF_A + off, MOF_B + off
    if giro:
        c = (a + b) / 2
        R = np.array([[math.cos(giro), -math.sin(giro), 0], [math.sin(giro), math.cos(giro), 0], [0, 0, 1]])
        a, b = c + R @ (a - c), c + R @ (b - c)
    return [IT.tubo(a, b, r=0.09, col=col, n=16, name='mofle'),
            IT.tubo(b, b + (b - a) * 0.04, r=0.05, col=(40, 40, 46), n=12, name='mofle')]


def moto_m(giro=0.0, faro=0.6, mofle=True, mofle_off=(0, 0, 0), mofle_giro=0.0, col=AZUL_M, motor_glow=0.0):
    ms = IT.moto(giro=giro, faro=faro, col=col, motor_glow=motor_glow)
    if mofle:
        ms += mofle_mesh(mofle_off, mofle_giro)
    return ms


def punta(mofle=True):
    return MOF_B if mofle else TUBO_B


def ruta_escape(n=40):
    """Puntos del escape: del cilindro a la salida (sin mofle)."""
    A = np.array([0.28, 0.6, 0.12])
    P1 = [A + (TUBO_A - A) * s for s in np.linspace(0, 1, 10)]
    P2 = [TUBO_A + (TUBO_B - TUBO_A) * s for s in np.linspace(0, 1, n)]
    return P1 + P2[1:]


def pos_ruta(s, R=None):
    R = R or ruta_escape()
    s = clamp(s)
    f = s * (len(R) - 1)
    i = min(int(f), len(R) - 2)
    return R[i] + (R[i + 1] - R[i]) * (f - i)


def ondas_sonido(fr, p, t, k, col=WHITE, n=4, rmax=1.6, vel=1.4, w=2.4):
    for j in range(n):
        ph = (t * vel + j / n) % 1.0
        r = 0.15 + rmax * ph
        q = np.linspace(-1.1, 1.1, 30)
        line3(fr, [np.asarray(p) + np.array([-r * math.cos(a), r * math.sin(a), 0.02]) for a in q], col=col, w=w,
              a=k * (1 - ph), glow=0.8)


# ================================================================== escenas
# 0. gancho (inicio 9: giro 360° con destellos) — la moto real da la vuelta; en cada canto, destello + trueno
U_GIRO0 = -0.22


def s_gancho(t, fi, u, d):
    ut = Wp(0, 'truena') + 0.02
    up = Wp(0, 'pero') - 0.05
    uc = Wp(0, 'corre') - 0.05
    ang = 360.0 * ease(seg(u, U_GIRO0, ut))
    c = math.cos(math.radians(ang))
    canto = 1 - clamp(abs(c) / 0.28) if 0 < ang < 360 else 0.0               # flash en los cantos (90° y 270°)
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='lines', floor_a=0.75, bokeh=1.0, beam=0.55)
    kl = golpe_k(u, ut, 0.95)                                                # trueno al aterrizar
    k90 = max(0.0, 1 - abs(ang - 90) / 35) if ang < 180 else 0.0
    k270 = max(0.0, 1 - abs(ang - 270) / 35) if ang > 180 else 0.0

    def ui(img, fx):
        M.cristal(img, fx, 'TRUENA', u, t0=ut - 0.05, cy=0.37, entrada='golpe')
        piso, alto = 1250, 470
        if u < ut:
            tip = veh_giro(img, fx, 'cromo', 540, piso, alto, ang, t)
            for kk, sd in ((k90, 1), (k270, 2)):
                if kk > 0 and tip:
                    llamarada(img, fx, tip[0], tip[1], kk, t, dirx=tip[2], escala=0.8, seed=sd)
        else:
            pose = P.cam_rapida(u - ut, [(0.0, dict(yaw=-0.9, al=500)), (0.5, dict(yaw=-0.35, al=475)),
                                         (3.0, dict(yaw=-0.15, al=475))])
            r = veh(img, fx, 'cromo', 560, piso, pose['al'] * 1.0, yaw=pose['yaw'], pitch=0.15, t=t)
            if r:
                x, y = punta_foto(r)
                llamarada(img, fx, x, y, kl, t, dirx=-1, escala=1.35, seed=3)
                llamarada(img, fx, x, y, golpe_k(u, uc, 0.45) * 0.8, t, dirx=-1, escala=0.8, seed=5)
        kicker(img, 'MOTOS · LO QUE NO VES', 120, seg(u, ut, ut + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu moto truena más…', 'sans')], 175, seg(u, ut, ut + 0.15), size=78)
        P.titulo_golpe(img, fx, [('pero no corre más.', 'serif')], 270, seg(u, up, up + 0.15), size=78)
        pill(img, fx, 540, 1400, 'MÁS RUIDO  ≠  MÁS FUERZA', eout(seg(u, uc, uc + 0.25)), size=30, border=FUEGO)
        pill(img, fx, 540, 1480, 'FOTO REAL', seg(u, ut + 0.3, ut + 0.6), size=20, border=(150, 150, 160), dot=False)
        credito(img, CRED['cromo'], k=seg(u, ut, ut + 0.3))
    fr.ui.append(ui)
    out = finish(fr, fi, flash=max(canto * 0.95, 0.85 * golpe_k(u, ut, 0.18)))
    return sacudir(out, t, max(golpe_k(u, ut, 0.4), 0.6 * golpe_k(u, uc, 0.3), 0.5 * k90 ** 3, 0.5 * k270 ** 3), amp=26)


# 1. le quitaste el mofle: el mofle se desarma y sale volando; queda el tubo pelón y truena
def s_quitaste(t, fi, u, d):
    uq = Wp(1, 'quitaste') - 0.1
    ub = Wp(1, 'brava') - 0.05
    k = P.eout4(seg(u, uq, uq + 0.45))
    fr = Frame(camara(u, [K(-0.3, 4.4, 30, 8, tx=-0.1, ty=0.55, tz=0.1), K(0.3, 3.6, -18, 6, tx=-0.3, ty=0.5, tz=0.1),
                          K(uq + 0.4, 3.9, -30, 10, tx=-0.5, ty=0.6, tz=0.5), K(d, 3.8, -34, 10, tx=-0.5, ty=0.6, tz=0.5)],
                   cy=0.58))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.35)
    off = (-0.4 * k, 1.2 * k - 0.6 * k * k, 2.6 * k)
    draw_objects(fr, moto_m(giro=-t * 0.5, faro=0.5, mofle=True, mofle_off=off, mofle_giro=k * 4.0))
    tip = fr.cam.p1(tuple(TUBO_B))
    kb = golpe_k(u, ub, 0.5)

    def ui(img, fx):
        kicker(img, 'LO QUE MUCHOS LE HACEN', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1480, 'RECREACIÓN', seg(u, 0.2, 0.5), size=20, border=(150, 150, 160), dot=False)
        texto(img, fx, 540, 280, '¿Sin mofle?', 104, WHITE, eout(seg(u, uq, uq + 0.2)), f='serif', glow=0.3)
        doodle_circle(img, fx, tip[0], tip[1], 90, 70, t, k=seg(u, uq + 0.45, uq + 0.75), col=RED, seed=2, w=7)
        pill(img, fx, tip[0], tip[1] + 130, 'ESCAPE DIRECTO', eout(seg(u, uq + 0.6, uq + 0.85)), size=26, border=RED)
        llamarada(img, fx, tip[0], tip[1], kb, t, dirx=-1, escala=0.9, seed=7)
        if u > ub:
            texto(img, fx, 540, 1250, '¡BRRAP!', 120, FUEGO, eout(seg(u, ub, ub + 0.15)) * (1 - seg(u, ub + 0.8, ub + 1.2)),
                  f='sansx', glow=0.7)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, uq + 0.1, 0.3), kb), amp=20)


# 2. el escape de fábrica no es un tubo cualquiera: rayos X y la ruta del escape medida para tu motor
def s_fabrica(t, fi, u, d):
    ut = Wp(2, 'tubo') - 0.1
    uh = Wp(2, 'hecho') - 0.1
    kx = seg(u, 0.1, 0.45)
    fr = Frame(camara(u, [K(-0.3, 4.6, 20, 10, tx=0.0, ty=0.6), K(0.4, 3.9, 8, 8, tx=-0.1, ty=0.55),
                          K(ut, 3.3, 2, 6, tx=-0.15, ty=0.45), K(d, 3.2, 0, 6, tx=-0.15, ty=0.45)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, 'FÁBRICA', u, t0=-0.15, cy=0.2, entrada='sube')
    draw_objects(fr, moto_m(giro=-t * 0.6, faro=0.4), xray=kx, keep=('mofle',))
    R = ruta_escape()
    kr = seg(u, ut - 0.2, ut + 0.9)
    if kr > 0:
        line3(fr, R, col=FUEGO, w=6, a=1.0, glow=1.4, frac=kr)
    pa, pb = fr.cam.p1(tuple(TUBO_A)), fr.cam.p1(tuple(MOF_B))
    pm = fr.cam.p1(tuple((MOF_A + MOF_B) / 2))
    pc = fr.cam.p1((0.28, 0.6, 0.12))

    def ui(img, fx):
        kicker(img, 'ESCAPE DE FÁBRICA · RAYOS X', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pc[0] + 40, pc[1] - 110, 'MOTOR', eout(seg(u, ut, ut + 0.25)), size=22, border=FUEGO)
        pill(img, fx, (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2 + 120, 'LARGO Y GROSOR MEDIDOS', eout(seg(u, ut + 0.6, ut + 0.85)),
             size=22, border=FUEGO, dot=False)
        pill(img, fx, pm[0], pm[1] - 100, 'MOFLE', eout(seg(u, ut + 0.9, ut + 1.15)), size=22, border=CYAN)
        P.titulo_golpe(img, fx, [('Hecho para tu motor', 'serif')], 1330, seg(u, uh, uh + 0.15), size=72)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uh + 0.15, 0.3), amp=14)


# 3. saca el humo de cada explosión: pulsos de humo viajan por el tubo y salen (no se quedan atrapados)
def s_humo(t, fi, u, d):
    ua = Wp(3, 'atrapado') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, 24, 8, tx=0.0, ty=0.5, tz=0.2), K(0.3, 3.1, 12, 5, tx=-0.1, ty=0.48, tz=0.2),
                          K(ua, 2.9, 4, 4, tx=-0.35, ty=0.45, tz=0.2), K(d, 2.9, 2, 4, tx=-0.4, ty=0.45, tz=0.2)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8)
    draw_objects(fr, moto_m(giro=-t * 0.8, faro=0.4, motor_glow=0.25), xray=0.85, keep=('mofle',))
    R = ruta_escape()
    line3(fr, R, col=WHITE, w=2.6, a=0.6, glow=0.5)
    rate = 3.0
    pc = (0.18, 0.75, 0.12)
    ex = (t * rate) % 1.0
    dot3(fr, pc, r=8 + 30 * (1 - ex) ** 6, col=(255, 210, 140), a=(1 - ex) ** 4, glow=2.0)        # la explosión del cilindro
    for j in range(6):
        s = ((t * rate - j) / 3.2) % 1.0
        p = pos_ruta(s, R) if s < 0.97 else MOF_B + np.array([-(s - 0.97) * 8, 0.05, 0])
        humo_puff(fr, p, 0.12 + 0.2 * s, 0.9, t, seed=j)
    for j in range(5):                                                       # el humo que sale por atrás
        ph = (t * 1.2 + j / 5) % 1.0
        humo_puff(fr, MOF_B + np.array([-0.2 - 1.4 * ph, 0.1 + 0.4 * ph, 0]), 0.25 + 0.5 * ph, (1 - ph) * 0.6, t, seed=10 + j)
    pt = fr.cam.p1(tuple(MOF_B))

    def ui(img, fx):
        kicker(img, 'CADA EXPLOSIÓN = UN PULSO DE HUMO', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 290, 'el humo sale', 92, WHITE, eout(seg(u, 0.1, 0.3)), f='serif', glow=0.3)
        pill(img, fx, pt[0] + 60, pt[1] - 120, 'NO SE QUEDA ATRAPADO', eout(seg(u, ua, ua + 0.25)), size=24, border=VERDE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. la prueba: la misma moto en el dinamómetro, con mofle (izq.) y sin mofle (der.)
def rodillos(fr, x, t, vel=1.0):
    ms = [named(M3.cyl(0.13, 0.5, (70, 72, 80), n=18, shadow=0, gloss=0.7).tf(rx=90, t=(x - 0.17, 0.13, -0.25)), 'rodillo', rim=0.7),
          named(M3.cyl(0.13, 0.5, (70, 72, 80), n=18, shadow=0, gloss=0.7).tf(rx=90, t=(x + 0.17, 0.13, -0.25)), 'rodillo', rim=0.7)]
    return ms


CARRIL = {True: -1.7, False: 1.5}            # z de cada moto: con mofle atrás, sin mofle adelante


def _par_dyno(fr, t, u, d):
    ms = []
    for mof in (True, False):
        z = CARRIL[mof]
        ms += P.tfk(moto_m(giro=-t * 9, faro=0.8, mofle=mof), s=1.0, t=(0.0, 0.0, z))
        ms += P.tfk(rodillos(fr, -0.72, t), t=(0, 0, z + 0.25))
        line3(fr, [(-1.6, 0.005, z - 0.5), (1.6, 0.005, z - 0.5)], col=CYAN if mof else RED, w=2, a=0.5, glow=0.4)
    draw_objects(fr, ms)
    tips = [fr.cam.p1((MOF_B[0], MOF_B[1], MOF_B[2] + CARRIL[True])),
            fr.cam.p1((TUBO_B[0], TUBO_B[1], TUBO_B[2] + CARRIL[False]))]
    return tips


def s_prueba(t, fi, u, d):
    um = Wp(4, 'misma') - 0.1
    uc = Wp(4, 'con') - 0.1
    us = Wp(4, 'sin') - 0.1
    fr = Frame(camara(u, [K(-0.3, 8.0, 24, 50, tx=0.0, ty=0.4, tz=-0.1), K(0.4, 6.8, 10, 42, tx=0.0, ty=0.4, tz=-0.1),
                          K(uc, 6.6, 6, 42, tx=0.0, ty=0.4, tz=-0.1), K(d, 6.5, 4, 42, tx=0.0, ty=0.4, tz=-0.1)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, 'PRUEBA', u, t0=-0.2, cy=0.22, entrada='zoom')
    tips = _par_dyno(fr, t, u, d)
    pa = fr.cam.p1((0.0, 1.35, CARRIL[True]))
    pb = fr.cam.p1((0.0, 1.35, CARRIL[False]))

    def ui(img, fx):
        kicker(img, 'DINAMÓMETRO · LA MISMA MOTO', 150, seg(u, um, um + 0.3), col=AZULC)
        pill(img, fx, pa[0], pa[1] - 40, 'CON MOFLE', eout(seg(u, uc, uc + 0.2)), size=30, border=CYAN)
        pill(img, fx, pb[0], pb[1] - 40, 'SIN MOFLE', eout(seg(u, us, us + 0.2)), size=30, border=RED)
        llamarada(img, fx, tips[1][0], tips[1][1], 0.8 * golpe_k(u, us + 0.25, 0.5), t, dirx=-1, escala=0.6, seed=4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.25, 0.3), amp=12)


# 5. el resultado: RUIDO se dispara sin mofle; FUERZA casi igual (Kawasaki: aumento casi nulo)
def barra(img, fx, x, y, w, h, nivel, col, k, txt=''):
    if k <= 0.01:
        return
    dd = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    dd.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, outline=M.scale_c(WHITE, 0.5 * k), width=3)
    ww = max(h, (w - 8) * clamp(nivel))
    dd.rounded_rectangle((x + 4, y + 4, x + 4 + ww, y + h - 4), radius=(h - 8) // 2, fill=M.scale_c(col, k))
    df.rounded_rectangle((x + 4, y + 4, x + 4 + ww, y + h - 4), radius=(h - 8) // 2, fill=M.scale_c(col, 0.45 * k))
    if txt:
        dd.text((x - 18, y + h / 2), txt, font=M.font('sans', 30), fill=M.scale_c(WHITE, k), anchor='rm')


def s_ruido(t, fi, u, d):
    um = Wp(5, 'muchisimo') - 0.1
    uk = Wp(5, 'kawasaki') - 0.1
    uf = Wp(5, 'fuerza') - 0.1
    fr = Frame(camara(u, [K(-0.3, 8.6, -14, 46, tx=0.0, ty=0.4, tz=-0.1), K(0.4, 8.0, -6, 42, tx=0.0, ty=0.4, tz=-0.1),
                          K(d, 7.9, -4, 42, tx=0.0, ty=0.4, tz=-0.1)], cy=0.33))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'RUIDO', u, t0=um - 0.1, cy=0.14, entrada='golpe')
    tips = _par_dyno(fr, t, u, d)
    kr = seg(u, um, um + 0.5)
    ondas_sonido(fr, (TUBO_B[0], TUBO_B[1], TUBO_B[2] + CARRIL[False]), t, kr, col=FUEGO, n=5, rmax=2.2, vel=1.8, w=3)
    ondas_sonido(fr, (MOF_B[0], MOF_B[1], MOF_B[2] + CARRIL[True]), t, 0.6 * kr, col=CYAN, n=3, rmax=0.45, vel=1.2, w=2)

    def ui(img, fx):
        kicker(img, 'RESULTADO DEL DINAMÓMETRO', 1020, seg(u, -0.1, 0.2), col=AZULC)
        k1 = seg(u, -0.1, 0.25)
        texto(img, fx, 330, 1160, 'CON', 30, CYAN, k1, f='sans', glow=0.2)
        texto(img, fx, 330, 1250, 'SIN', 30, RED, k1, f='sans', glow=0.2)
        texto(img, fx, 330, 1430, 'CON', 30, CYAN, seg(u, uk, uk + 0.2), f='sans', glow=0.2)
        texto(img, fx, 330, 1520, 'SIN', 30, RED, seg(u, uk, uk + 0.2), f='sans', glow=0.2)
        texto(img, fx, 540, 1095, 'RUIDO', 40, WHITE, k1, f='sansx', glow=0.3)
        barra(img, fx, 380, 1140, 560, 40, 0.3, CYAN, k1)
        barra(img, fx, 380, 1230, 560, 40, 0.3 + 0.7 * P.eout4(seg(u, um, um + 0.5)), RED, k1)
        texto(img, fx, 540, 1365, 'FUERZA', 40, WHITE, seg(u, uk, uk + 0.2), f='sansx', glow=0.3)
        kf = P.eout4(seg(u, uk + 0.1, uk + 0.7))
        barra(img, fx, 380, 1410, 560, 40, 0.62 * kf, CYAN, seg(u, uk, uk + 0.2))
        barra(img, fx, 380, 1500, 560, 40, 0.63 * kf, RED, seg(u, uk, uk + 0.2))
        pill(img, fx, 540, 1610, 'INGENIEROS DE KAWASAKI: GANANCIA «CASI NULA»', eout(seg(u, uf, uf + 0.25)), size=22,
             border=AMARILLO, dot=False)
        pill(img, fx, 540, 1680, 'RECREACIÓN · AUTOPAPO, BRASIL', eout(seg(u, uf + 0.2, uf + 0.45)), size=18,
             border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.1, 0.35), amp=16)


# 6. y hasta puede calentar más tu motor: el motor se pone al rojo y el termómetro sube
def s_calor(t, fi, u, d):
    uc = Wp(6, 'calentar') - 0.1
    kc = P.eout4(seg(u, uc, uc + 0.8))
    fr = Frame(camara(u, [K(-0.3, 3.8, 34, 10, tx=0.05, ty=0.55), K(0.3, 3.2, 18, 8, tx=0.05, ty=0.55),
                          K(d, 3.1, 14, 8, tx=0.05, ty=0.55)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    draw_objects(fr, moto_m(giro=-t * 4, faro=0.4, mofle=False, motor_glow=0.15 + 0.85 * kc))
    P.ondas_calor(fr, t, 0.1, 0.8, 1.8, 0.7, k=kc)

    def ui(img, fx):
        kicker(img, 'SIN MOFLE · MÁS CALOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 290, 'más caliente', 96, (255, 120, 80), eout(seg(u, uc, uc + 0.2)), f='serif', glow=0.5)
        P.termometro(img, fx, 900, 1450, 420, 0.3 + 0.65 * kc, '', k=seg(u, -0.1, 0.2))
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. SEGUNDO GANCHO: los truenos son gasolina que explota en el tubo, no en el motor
#    hasta «gasolina» se ve la moto REAL tronando; luego rayos X (recreación) con la gasolina dentro del tubo
def _truenos_foto(t, fi, u, d, bangs):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    pose = P.cam_rapida(u, [(-0.3, dict(al=600, x=760, yaw=-0.8)), (0.0, dict(al=720, x=820, yaw=-0.4)),
                            (bangs[2], dict(al=820, x=880, yaw=-0.2)), (3.0, dict(al=840, x=890, yaw=-0.1))])

    def ui(img, fx):
        kicker(img, 'LOS TRUENOS', 150, seg(u, -0.1, 0.2), col=FUEGO)
        texto(img, fx, 540, 300, 'que tanto te gustan…', 76, WHITE, eout(seg(u, bangs[2] - 0.6, bangs[2] - 0.4)), f='serif', glow=0.3)
        r = veh(img, fx, 'cromo', pose['x'], 1250, pose['al'], yaw=pose['yaw'], pitch=0.15, t=t)
        if r:
            x, y = punta_foto(r)
            for j, b in enumerate(bangs):
                llamarada(img, fx, x, y, golpe_k(u, b, 0.5), t, dirx=-1, escala=1.4, seed=20 + j)
        credito(img, CRED['cromo'])
    fr.ui.append(ui)
    return fr


def s_truenos(t, fi, u, d):
    ug = Wp(7, 'gustan') - 0.1
    uga = Wp(7, 'gasolina') - 0.1
    ue = Wp(7, 'explota') - 0.05
    un = Wp(7, 'no') - 0.05
    bangs = [0.05, Wp(7, 'truenos') - 0.05, ug, ue + 0.3]
    if u < uga - 0.08:
        fr = _truenos_foto(t, fi, u, d, bangs)
        sh = max(golpe_k(u, b, 0.35) for b in bangs)
        return sacudir(finish(fr, fi, flash=0.35 * golpe_k(u, bangs[1], 0.15)), t, sh, amp=24)
    fr = Frame(camara(u, [K(uga - 0.1, 3.2, -8, 6, tx=-0.25, ty=0.45, tz=0.2), K(uga + 0.4, 2.9, 0, 5, tx=-0.2, ty=0.45, tz=0.2),
                          K(d, 2.8, 4, 5, tx=-0.2, ty=0.45, tz=0.2)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9, beam=0.3)
    M.cristal(fr.base, fr.fx, 'GASOLINA', u, t0=uga, cy=0.2, entrada='zoom')
    draw_objects(fr, moto_m(giro=-t * 1.5, faro=0.4, mofle=False), xray=0.8, keep=('escape',))
    R = ruta_escape()
    rng = np.random.RandomState(5)
    for j in range(12):                                                      # gotitas de gasolina dentro del tubo
        s_ = (0.35 + 0.6 * rng.rand() + t * 0.18) % 1.0
        p = pos_ruta(s_, R) + np.array([0, (rng.rand() - 0.5) * 0.04, 0])
        dot3(fr, tuple(p), r=7, col=GASOL, a=1.0, glow=1.3)
    if u > ue:
        for j in range(4):
            p = pos_ruta(0.55 + 0.1 * j, R)
            kk = golpe_k(u, ue + 0.08 * j, 0.5)
            dot3(fr, tuple(p), r=10 + 60 * kk, col=(255, 190, 90), a=kk, glow=2.2)
    tip = fr.cam.p1(tuple(TUBO_B))
    pm = fr.cam.p1((0.1, 0.4, 0.12))

    def ui(img, fx):
        kicker(img, 'LOS TRUENOS · RAYOS X (RECREACIÓN)', 150, 1.0, col=FUEGO)
        llamarada(img, fx, tip[0], tip[1], golpe_k(u, bangs[3], 0.5), t, dirx=-1, escala=1.1, seed=24)
        pill(img, fx, 540, 1300, 'GASOLINA SIN QUEMAR', eout(seg(u, uga, uga + 0.25)), size=30, border=GASOL)
        if u > un - 0.4:
            pill(img, fx, 540, 1400, 'EXPLOTA EN EL TUBO', eout(seg(u, un - 0.4, un - 0.15)), size=30, border=FUEGO)
        if u > un:
            P.pill_tachada(img, fx, 540, 1500, 'EN EL MOTOR', eout(seg(u, un, un + 0.2)), seg(u, un + 0.2, un + 0.5), t,
                           size=28, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=0.8 * (1 - seg(u, uga - 0.08, uga + 0.12))), t, golpe_k(u, bangs[3], 0.35), amp=20)


# 8. adentro del cilindro empuja el pistón; en el escape solo hace ruido y gasta gasolina (pantalla dividida)
def _mitad_cil(t, u, d, ue):
    th = 300 + 160 * clamp(u / 1.0) + (u - 1.0) * 220 if u > 1.0 else 300 + 160 * clamp(u / 1.0)
    fr = Frame(Cam(target=(0, 2.3, 0), dist=9.5, yaw=12, pitch=6, cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    IT.cilindro(fr, t, th % 720, k=1.0)
    return fr


def _mitad_tubo(t, u, d, ur):
    fr = Frame(Cam(target=(0, 0, 0), dist=5.0, yaw=0, pitch=4, cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    for zz in (-0.3, 0.3):
        line3(fr, [(-2.6, zz, 0), (2.6, zz, 0)], col=WHITE, w=4, a=0.95, glow=0.8)
    kk = max(golpe_k(u, ur, 0.6), 0.6 * golpe_k(u, 0.9, 0.5))
    dot3(fr, (0.2, 0, 0), r=14 + 120 * kk, col=(255, 190, 90), a=kk, glow=2.6)
    rng = np.random.RandomState(9)
    for j in range(10):
        dot3(fr, (-2.0 + 4 * ((rng.rand() + t * 0.3) % 1.0), (rng.rand() - 0.5) * 0.3, 0), r=5, col=GASOL, a=0.9, glow=1.0)
    return fr


def s_cilindro(t, fi, u, d):
    ue = Wp(8, 'empuja') - 0.1
    ur = Wp(8, 'ruido') - 0.1
    ug = Wp(8, 'gasta') - 0.1
    A = _mitad_cil(t, u, d, ue)
    B = _mitad_tubo(t, u, d, ur)

    def uiA(img, fx):
        kicker(img, 'ADENTRO DEL CILINDRO', 560, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1390, '✓ EMPUJA EL PISTÓN = FUERZA', eout(seg(u, ue, ue + 0.25)), size=28, border=VERDE)
    A.ui.append(uiA)

    def uiB(img, fx):
        kicker(img, 'EN EL ESCAPE', 560, seg(u, ur - 0.6, ur - 0.3), col=FUEGO)
        pill(img, fx, 540, 700, '✗ SOLO RUIDO', eout(seg(u, ur, ur + 0.2)), size=30, border=RED)
        pill(img, fx, 540, 790, 'Y GASTA GASOLINA', eout(seg(u, ug, ug + 0.2)), size=26, border=GASOL)
    B.ui.append(uiB)
    a, b = finish(A, fi), finish(B, fi)
    out = np.zeros_like(a)
    out[0:960] = a[480:1440]
    out[960:1920] = b[480:1440]
    img = Image.fromarray(out)
    ImageDraw.Draw(img).line([(0, 960), (1080, 960)], fill=(200, 200, 205), width=3)
    return sacudir(np.asarray(img), t, golpe_k(u, ur, 0.35), amp=16)


# 9. por dentro, el mofle tiene cámaras: la onda de sonido entra por arriba, rebota en las paredes y sale chiquita
def s_mofle(t, fi, u, d):
    uc = Wp(9, 'camaras') - 0.1
    ur = Wp(9, 'rebota') - 0.1
    ua = Wp(9, 'apaga') - 0.1
    fr = Frame(camara(u, [K(-0.3, 8.4, 30, 14, tx=0.0, ty=0.0), K(0.4, 7.4, 16, 8, tx=0.0, ty=0.0), K(d, 7.2, 12, 6, tx=0.0, ty=0.0)],
                   cy=0.52))
    space(fr, t, floor=None, bokeh=0.8)
    Lh, R = 2.0, 0.85
    q = np.linspace(0, 2 * math.pi, 40)
    for y in (-Lh, Lh):
        line3(fr, [(R * math.cos(a), y, R * math.sin(a)) for a in q], col=WHITE, w=2.6, a=0.9, glow=0.7)
    for sx in (-1, 1):
        line3(fr, [(sx * R, -Lh, 0), (sx * R, Lh, 0)], col=WHITE, w=3.2, a=0.95, glow=0.8)
        line3(fr, [(0, -Lh, sx * R), (0, Lh, sx * R)], col=WHITE, w=1.6, a=0.3, glow=0.3)
    kc = seg(u, uc - 0.3, uc + 0.5)
    paredes = (1.0, 0.0, -1.0)
    for j, y in enumerate(paredes):                                          # las cámaras: paredes con un hueco alternado
        kk = clamp(kc * 3 - j)
        hueco = 0.42 if j % 2 == 0 else -0.42
        if hueco > 0:
            line3(fr, [(-R, y, 0), (hueco - 0.2, y, 0)], col=CYAN, w=5, a=kk, glow=1.1)
        else:
            line3(fr, [(hueco + 0.2, y, 0), (R, y, 0)], col=CYAN, w=5, a=kk, glow=1.1)
    line3(fr, [(0, Lh, 0), (0, Lh + 1.2, 0)], col=(170, 172, 180), w=10, a=0.95, glow=0.3)    # entra el tubo
    line3(fr, [(0, -Lh, 0), (0, -Lh - 0.9, 0)], col=(170, 172, 180), w=10, a=0.95, glow=0.3)  # sale
    kw = seg(u, 0.1, ur + 1.2)
    pts = []
    n = 320
    for i in range(n):                                                        # la onda que baja rebotando y se apaga
        s_ = i / (n - 1)
        if s_ > kw:
            break
        yy = Lh + 1.2 - s_ * (2 * Lh + 2.1)
        dentro = -Lh < yy < Lh
        amp = (0.5 if not dentro and yy > 0 else 0.08) if not dentro else 0.5 * math.exp(-2.4 * (Lh - yy) / (2 * Lh))
        xx = amp * math.sin(s_ * 80 - t * 14)
        if dentro:
            xx += 0.45 * math.sin(s_ * 9.0) * math.exp(-1.2 * (Lh - yy) / (2 * Lh))          # zigzag entre cámaras
        pts.append((clamp(xx, -R + 0.06, R - 0.06), yy, 0.03))
    if len(pts) > 2:
        line3(fr, pts, col=FUEGO, w=4.5, a=1.0, glow=1.4)
    pi, po = fr.cam.p1((0.0, Lh + 0.8, 0)), fr.cam.p1((0.0, -Lh - 0.6, 0))
    pw = fr.cam.p1((R, 0.0, 0))

    def ui(img, fx):
        kicker(img, 'EL MOFLE POR DENTRO · RECREACIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 270, 'cámaras', 110, WHITE, eout(seg(u, uc, uc + 0.2)), f='serif', glow=0.3)
        pill(img, fx, pi[0] + 230, pi[1], 'ENTRA FUERTE', eout(seg(u, 0.2, 0.45)), size=24, border=FUEGO)
        pill(img, fx, pw[0] + 150, pw[1], 'REBOTA', eout(seg(u, ur, ur + 0.25)), size=24, border=CYAN)
        pill(img, fx, po[0] + 220, po[1], 'SALE BAJITO', eout(seg(u, ua, ua + 0.25)), size=24, border=VERDE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. la norma: 86 dB (89 si es grande), medidos acelerando a 7.5 m (NOM-082-SEMARNAT-1994)
def s_norma(t, fi, u, d):
    u86 = Wp(10, 'ochenta') - 0.1
    u89 = Wp(10, 'ochenta', 1) - 0.1
    ug = Wp(10, 'grande') - 0.1
    fr = Frame(camara(u, [K(-0.3, 8.0, 0, 36, tx=0.0, ty=0.3, tz=0.6), K(0.4, 7.0, 0, 30, tx=0.0, ty=0.3, tz=1.0),
                          K(d, 6.9, 0, 30, tx=0.0, ty=0.3, tz=1.0)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.7)
    M.cristal(fr.base, fr.fx, '86 dB', u, t0=u86, cy=0.2, entrada='golpe')
    xm = -2.4 + 4.8 * ease(seg(u, -0.3, d))
    draw_objects(fr, P.tfk(moto_m(giro=-t * 10, faro=0.9), s=1.0, t=(xm, 0, 0)))
    line3(fr, [(-4, 0.01, 0.6), (4, 0.01, 0.6)], col=WHITE, w=2, a=0.5, glow=0.3)
    mic = (0.0, 0.0, 3.0)
    line3(fr, [(0, 0.01, 0.0), (0, 0.01, 3.0)], col=AMARILLO, w=3, a=0.9, glow=0.8)
    line3(fr, [mic, (0, 1.2, 3.0)], col=WHITE, w=3, a=0.9, glow=0.6)
    dot3(fr, (0, 1.25, 3.0), r=12, col=WHITE, glow=1.2)
    pmid = fr.cam.p1((0.0, 0.0, 1.5))
    pm = fr.cam.p1((0, 1.3, 3.0))
    ondas_sonido(fr, (xm - 0.8, 0.4, 0.18), t, 0.8, col=FUEGO, n=3, rmax=1.4, vel=1.5, w=2.4)

    def ui(img, fx):
        kicker(img, 'NOM-082-SEMARNAT-1994 · MOTOS NUEVAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pmid[0] + 110, pmid[1], '7.5 m', eout(seg(u, 0.2, 0.45)), size=24, border=AMARILLO, dot=False)
        pill(img, fx, pm[0], pm[1] - 70, 'MICRÓFONO', eout(seg(u, 0.3, 0.55)), size=20, border=(200, 200, 210), dot=False)
        pill(img, fx, 540, 1380, '86 dB · HASTA 449 cc', eout(seg(u, u86 + 0.2, u86 + 0.45)), size=30, border=CYAN)
        pill(img, fx, 540, 1470, '89 dB · DE 450 cc EN ADELANTE', eout(seg(u, u89, u89 + 0.25)), size=30, border=FUEGO)
        pill(img, fx, 540, 1560, 'MEDIDO ACELERANDO, A 7.5 m', eout(seg(u, ug, ug + 0.25)), size=22, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, u86 + 0.15, 0.3), golpe_k(u, u89 + 0.1, 0.25) * 0.6), amp=14)


# 11. tu oído: cada 3 dB de más, la mitad del tiempo; a 100 dB, 15 minutos (NIOSH)
ESCALA = [(85, '8 h'), (88, '4 h'), (91, '2 h'), (94, '1 h'), (97, '30 min'), (100, '15 min')]


def oreja(img, fx, cx, cy, s, k, t):
    if k <= 0.01:
        return
    dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    c = M.scale_c(WHITE, 0.9 * k)
    dd.arc((cx - 90 * s, cy - 140 * s, cx + 90 * s, cy + 120 * s), 180, 90, fill=c, width=int(7 * s))
    dd.arc((cx - 45 * s, cy - 80 * s, cx + 45 * s, cy + 40 * s), 180, 60, fill=c, width=int(6 * s))
    dd.line([(cx + 90 * s * math.cos(math.radians(90)), cy + 120 * s * 0.0)], fill=c)
    for j in range(3):
        ph = (t * 1.4 + j / 3) % 1.0
        r = (60 + 160 * ph) * s
        df.arc((cx - 260 * s - r, cy - r, cx - 260 * s + r, cy + r), -40, 40, fill=M.scale_c(FUEGO, k * (1 - ph)), width=int(5 * s))


def s_oido(t, fi, u, d):
    u3 = Wp(11, 'tres') - 0.1
    um = Wp(11, 'mitad') - 0.1
    uc = Wp(11, 'cien') - 0.1
    uq = Wp(11, 'quince') - 0.1
    fr = Frame(Cam(target=(0, 0, 0), dist=6, yaw=0, pitch=0, cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '15 MIN', u, t0=uq, cy=0.13, entrada='zoom')

    def ui(img, fx):
        kicker(img, 'TU OÍDO · LÍMITE RECOMENDADO (NIOSH, EE. UU.)', 340, seg(u, -0.1, 0.2), col=AZULC)
        oreja(img, fx, 820, 560, 0.9, seg(u, -0.1, 0.25), t)
        texto(img, fx, 390, 560, 'tu oído', 96, WHITE, eout(seg(u, -0.05, 0.2)), f='serif', glow=0.3)
        dd = ImageDraw.Draw(img)
        x0, y0, hb, gap = 300, 800, 70, 22
        for j, (db, tt) in enumerate(ESCALA):
            kj = seg(u, u3 + 0.25 * j, u3 + 0.25 * j + 0.25) if j else seg(u, -0.1, 0.2)
            if j == len(ESCALA) - 1:
                kj = seg(u, uc - 0.2, uc + 0.1)
            if kj <= 0:
                continue
            y = y0 + j * (hb + gap)
            w = 640 / (2 ** j)
            col = RED if db >= 100 else (FUEGO if db > 85 else VERDE)
            barra(img, fx, x0, y, max(60, int(w * P.eout4(kj) + 50)), hb, 1.0, col, kj)
            dd.text((x0 - 20, y + hb / 2), f'{db} dB', font=M.font('sans', 34), fill=M.scale_c(WHITE, kj), anchor='rm')
            dd.text((x0 + max(60, int(w + 50)) + 20, y + hb / 2), tt, font=M.font('sansx', 36), fill=M.scale_c(col, kj),
                    anchor='lm')
        pill(img, fx, 540, 1430, '+3 dB = LA MITAD DEL TIEMPO', eout(seg(u, um, um + 0.25)), size=28, border=FUEGO)
        if u > uq:
            doodle_circle(img, fx, 560, y0 + 5 * (hb + gap) + hb / 2, 330, 70, t, k=seg(u, uq, uq + 0.3), col=RED, seed=6, w=7)
        pill(img, fx, 540, 1700, 'AL DÍA · REFERENCIA DE TRABAJO', eout(seg(u, uq + 0.3, uq + 0.55)), size=18,
             border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uq + 0.1, 0.3), amp=12)


# 12. la multa en la CDMX: boleta que cae con sello rojo (Reglamento de Tránsito, art. 43, fracc. V)
def s_multa(t, fi, u, d):
    ue = Wp(12, 'escape') - 0.1
    um = Wp(12, 'multa') - 0.1
    ud = Wp(12, 'dos') - 0.1
    fr = Frame(Cam(target=(0, 0, 0), dist=6, yaw=0, pitch=0, cy=0.5))
    space(fr, t, floor=None, bokeh=0.9, beam=0.4)
    M.cristal(fr.base, fr.fx, 'MULTA', u, t0=um, cy=0.13, entrada='golpe')

    def ui(img, fx):
        kicker(img, 'REGLAMENTO DE TRÁNSITO · CIUDAD DE MÉXICO', 440, seg(u, -0.1, 0.2), col=AZULC)
        e = P.rebote(seg(u, -0.1, 0.5))
        y = int(-700 + (900 + 700) * e)
        ang = (1 - e) * 12
        card = Image.new('RGBA', (760, 820), (0, 0, 0, 0))
        dc = ImageDraw.Draw(card)
        dc.rounded_rectangle((0, 0, 759, 819), radius=24, fill=(236, 232, 222, 255))
        dc.rectangle((0, 0, 759, 110), fill=(30, 34, 44, 255))
        dc.text((380, 56), 'BOLETA DE INFRACCIÓN', font=M.font('sansx', 40), fill=(240, 240, 240), anchor='mm')
        lines = [('ARTÍCULO 43 · FRACCIÓN V', 34), ('Modificar el escape para', 36), ('provocar ruido excesivo', 36),
                 ('', 20), ('20, 25 o 30 UMA', 40)]
        yy = 170
        for txt, sz in lines:
            dc.text((380, yy), txt, font=M.font('sans', sz), fill=(40, 40, 46), anchor='mm')
            yy += sz + 34
        dc.text((380, 640), '$2 346 a $3 519', font=M.font('sansx', 70), fill=(30, 30, 36), anchor='mm')
        dc.text((380, 735), 'RECREACIÓN · MOTORPASIÓN MÉXICO, 2026', font=M.font('mono', 20), fill=(120, 120, 128), anchor='mm')
        card = card.rotate(ang, resample=Image.BICUBIC, expand=True)
        img.paste(card, (540 - card.width // 2, y - card.height // 2), card)
        ks = seg(u, um, um + 0.15)
        if ks > 0:
            st = Image.new('RGBA', (520, 170), (0, 0, 0, 0))
            ds = ImageDraw.Draw(st)
            ds.rounded_rectangle((6, 6, 513, 163), radius=20, outline=(220, 30, 40, 255), width=12)
            ds.text((260, 86), 'MULTA', font=M.font('sansx', 110), fill=(220, 30, 40, 255), anchor='mm')
            s = (2.0 - P.eout4(ks)) * 0.68
            st = st.resize((int(520 * s), int(170 * s))).rotate(-9, resample=Image.BICUBIC, expand=True)
            img.paste(st, (600 - st.width // 2, 1030 - st.height // 2), st)
        pill(img, fx, 540, 1460, 'MÁS DE $2 000', eout(seg(u, ud, ud + 0.2)), size=40, border=RED)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.4, 0.3), golpe_k(u, um + 0.15, 0.35)), amp=18)


# 13. mándaselo a tu compa que le quitó el mofle (las dos motos reales, de noche)
def s_compa(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.9, 0), dist=6.0, yaw=0, pitch=10, cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.2)

    def ui(img, fx):
        e = P.eout4(seg(u, -0.2, 0.25))
        veh(img, fx, 'roja', 540 + 260 * (1 - e) + 170, 1180, 360, yaw=0.3, t=t, alfa=0.85)
        r = veh(img, fx, 'cromo', 540 - 260 * (1 - e) - 120, 1420, 400, yaw=-0.3, t=t)
        if r:
            x, y = punta_foto(r)
            llamarada(img, fx, x, y, golpe_k(u, 0.2, 0.45), t, dirx=-1, escala=0.7, seed=31)
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que le quitó el mofle.', 'serif')], 230,
                       seg(u, 0.0, 0.15), size=70)
        credito(img, CRED['cromo'], y=1840)
        credito(img, CRED['roja'], y=1872)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(U_GIRO0 + 0.05, 'whoosh', 0.8), (-0.02, 'burst', 0.7), (0.25, 'burst', 0.7), (0.58, 'sub', 1.0),
                     (0.58, 'burst', 1.0), (0.6, 'bass', 0.9), (2.4, 'burst', 0.8), (2.4, 'slap', 0.6)]),
           dict(desde=1, fn=s_quitaste, tr='cubo', sfx=[(0.1, 'click', 0.8), (0.2, 'whoosh', 0.8), (1.7, 'burst', 1.0),
                                                     (1.7, 'sub', 0.8)]),
           dict(desde=2, fn=s_fabrica, tr='zoom', sfx=[(0.15, 'shimmer', 0.6), (2.0, 'riser', 0.5), (3.3, 'chime_b', 0.6),
                                                     (3.45, 'bass', 0.7)]),
           dict(desde=3, fn=s_humo, tr='wipe', sfx=[(0.3 + 0.33 * j, 'thud', 0.35) for j in range(9)]),
           dict(desde=4, fn=s_prueba, tr='mosaico', sfx=[(1.1, 'click', 0.7), (2.0, 'chime_a', 0.5), (2.9, 'burst', 0.9)]),
           dict(desde=5, fn=s_ruido, tr='deslizar_abajo', sfx=[(0.9, 'riser', 0.6), (1.4, 'burst', 0.9), (1.45, 'sub', 0.8),
                                                             (3.0, 'tick', 0.6), (3.4, 'chime_c', 0.5)]),
           dict(desde=6, fn=s_calor, tr='flash', sfx=[(0.5, 'riser', 0.5)]),
           dict(desde=7, fn=s_truenos, tr='rompe', c=(0.3, 0.55),
                sfx=[(0.05, 'burst', 1.0), (0.05, 'sub', 0.9), (0.4, 'burst', 0.9), (1.6, 'burst', 1.0), (1.6, 'bass', 0.8),
                     (2.6, 'shimmer', 0.6), (3.5, 'burst', 1.0), (3.5, 'sub', 0.9)]),
           dict(desde=8, fn=s_cilindro, tr='giro', sfx=[(1.1, 'thud', 0.8), (3.4, 'burst', 1.0), (3.45, 'sub', 0.7),
                                                     (4.8, 'tick', 0.6)]),
           dict(desde=9, fn=s_mofle, tr='remolino', sfx=[(1.3, 'click', 0.7), (2.7, 'whoosh_suave', 0.5), (4.0, 'chime_a', 0.5)]),
           dict(desde=10, fn=s_norma, tr='golpe', sfx=[(2.6, 'sub', 0.8), (2.65, 'bass', 0.8), (4.5, 'tick', 0.6)]),
           dict(desde=11, fn=s_oido, tr='rebanadas', sfx=[(1.5 + 0.25 * j, 'tick', 0.5) for j in range(5)] +
                [(5.1, 'bass', 0.9), (6.0, 'scribble', 0.6)]),
           dict(desde=12, fn=s_multa, tr='glitch', sfx=[(0.4, 'slap', 0.9), (3.4, 'bass', 1.0), (3.4, 'thud', 0.8),
                                                      (4.3, 'chime_b', 0.5)]),
           dict(desde=13, fn=s_compa, tr='iris', sfx=[(0.2, 'burst', 0.8), (0.15, 'bass', 0.7)]),
           dict(desde=14, loop=True, tr='push')]

if __name__ == '__main__':
    montaje.cli(globals())
