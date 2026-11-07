"""Reel diario: «Tu tarjeta no tiene pila… y paga.» Dom 8-nov-2026, 19:00. Voz Isaac. Estilo rápido (ESTILO.md §11-12).
Inicio tipo 10 (rayos X de golpe: la tarjeta normal y, con el primer golpe, se vuelve de cristal y se ve su antena y su chip).
Primera transición: cubo_izq. Datos: la tarjeta sin contacto no tiene batería; la terminal crea un campo de 13.56 MHz y la antena
en espiral de la tarjeta lo convierte en electricidad (inducción) que prende el chip; el alcance típico es de 4 cm o menos y nunca
pasa de 10 cm (Thales); con dos tarjetas juntas la terminal puede no cobrar o cobrarle a la que no querías («card clash», TfL);
cada terminal está registrada a un comercio y a un banco (Thales); cada pago lleva un criptograma que no se repite (EMV).
Tarjeta, terminal, cartera y camión: RECREACIÓN (sin marcas ni logos). Fuentes en guiones/2026-11-08_tarjeta.txt."""
import math, os, re, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'tarjeta'
TXT = ['Tu tarjeta no tiene pila… y paga.',
       '¿De dónde saca la energía? De la terminal.',
       'Crea un campo magnético que cambia más de 13 millones de veces por segundo.',
       'Escondida en el plástico, tu tarjeta tiene una antena en espiral.',
       'Al entrar al campo, la antena produce electricidad.',
       'Eso prende el chip… solo un instante.',
       'Pero el campo es chiquito: unos 4 centímetros.',
       'Pegada, cobra. A 10 centímetros… nada.',
       'Ahora, el error que casi todos cometemos: dos tarjetas sin contacto juntas en la cartera.',
       'La terminal detecta dos chips y no sabe cuál cobrar.',
       'Puede rechazar el pago… o cobrarle a la que no querías.',
       'Sácala sola y paga con una.',
       '¿Y si alguien te roza con una terminal en el camión?',
       'Tendría que pegártela, y cada terminal está registrada a un comercio y a un banco.',
       'Además, cada pago lleva un código que no se repite.',
       'Si alguien lo copia, ya no le sirve.',
       'Mándaselo a alguien que le tiene miedo a pagar sin contacto.',
       'Y recuerda:']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-08_tarjeta_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)

AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 70, 60)
COBRE = (240, 150, 70)
ORO = (214, 176, 92)


# ================================================================== utilidades
def _pal(i):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split()


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


_W = []


def _words():
    if not _W:
        f = f'/home/claude/words_{TEMA}.json'
        if os.path.exists(f):
            d = json.load(open(f))
            d = d.get('words', d) if isinstance(d, dict) else d
            _W.extend(w for w in d if w.get('type', 'word') == 'word' and not w['text'].startswith('['))
    return _W


def wt(i, k):
    """Tiempo (relativo al inicio de la frase i) en que empieza su palabra k: exacto con las palabras de Scribe."""
    n = len(_pal(i))
    k = max(0, min(k, n - 1))
    W = _words()
    if len(W) == sum(len(_pal(j)) for j in range(len(VOZ))):
        n0 = sum(len(_pal(j)) for j in range(i))
        return W[n0 + k]['start'] - W[n0]['start']
    return (TE(i) - TT(i)) * k / n


def cam(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch=8, tx=0.0, ty=0.0, tz=0.0, roll=0.0):
    return (u, dict(tx=tx, ty=ty, tz=tz, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def check(img, fx, x, y, k, txt, col=VERDE):
    pill(img, fx, x, y, '✓ ' + txt, eout(k), size=36, border=col)


def tache(img, fx, x, y, k, txt):
    pill(img, fx, x, y, '✗ ' + txt, eout(k), size=36, border=ROJO, col=(255, 200, 196))


# ================================================================== objetos
_IM = {}


def cara(tipo='azul', num='2026'):
    """Frente de la tarjeta (sin marcas): color, «DÉBITO» o «CRÉDITO» y número de ejemplo."""
    key = ('cara', tipo, num)
    if key in _IM:
        return _IM[key]
    w, h = 640, 400
    c0, c1, lab = {'azul': ((18, 40, 92), (40, 110, 170), 'DÉBITO'), 'negra': ((14, 14, 18), (60, 62, 70), 'CRÉDITO'),
                   'roja': ((110, 20, 26), (200, 60, 50), 'CRÉDITO')}[tipo]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    k = (x / w * 0.7 + y / h * 0.3)[..., None]
    a = np.array(c0, np.float32) * (1 - k) + np.array(c1, np.float32) * k
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for j in range(6):
        d.arc((-200 + j * 40, 120 - j * 10, 900 + j * 40, 700 - j * 10), 200, 330, fill=tuple(int(v * 1.25 + 12) for v in c1), width=2)
    d.text((40, 36), lab, font=M.font('mono', 30), fill=(230, 232, 236))
    d.text((40, 300), f'•••• •••• •••• {num}', font=M.font('mono', 36), fill=(236, 236, 240))
    d.text((40, 350), 'EJEMPLO', font=M.font('mono', 22), fill=(190, 194, 204))
    _IM[key] = im
    return im


def tarjeta(tipo='azul', num='2026', vertical=True, s=1.0, rx=0.0, ry=0.0, rz=0.0, t=(0, 0, 0)):
    """Tarjeta semirrealista (85.6 × 54 mm a escala 1.6 × 1.01). vertical=True: de pie viendo a +z; si no, acostada boca arriba."""
    body = named(M3.rbox(1.6, 0.03, 1.01, 0.07, (40, 44, 56), n=4, shadow=0, gloss=0.6, base=False), 'body', rim=0.7, gloss=0.6)
    top = named(M3.box(1.5, 0.004, 0.94, (30, 40, 70), shadow=0, base=True, gloss=0.7).tf(t=(0, 0.015, 0)), 'cara', gloss=0.7, rim=0.3)
    M3.decal(top, top.FACE['top'], cara(tipo, num).convert('RGBA'))
    chip = named(M3.box(0.22, 0.012, 0.17, ORO, shadow=0, base=True, gloss=0.95).tf(t=(-0.5, 0.019, 0.02)), 'chip', rim=0.4, gloss=0.95)
    ms = [body, top, chip]
    if vertical:
        ms = P.tfk(ms, rx=90)
    return P.tfk(ms, s=s, rx=rx, ry=ry, rz=rz, t=t)


def _antena_pts(vertical=True, s=1.0, rx=0.0, ry=0.0, rz=0.0, t=(0, 0, 0), vueltas=4):
    """Espiral de la antena (rectángulos concéntricos unidos), en las mismas coordenadas que tarjeta()."""
    pts = []
    for i in range(vueltas):
        ins = 0.07 + 0.035 * i
        x0, x1, z0, z1 = -0.8 + ins, 0.8 - ins, -0.505 + ins, 0.505 - ins
        pts += [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1), (x0, 0, z0 + 0.035)]
    pts += [(-0.5, 0, 0.02)]
    P_ = np.array(pts, float)
    R = M3.rotm(90 if vertical else 0, 0, 0)
    P_ = P_ @ R.T
    P_ = P_ * s
    P_ = P_ @ M3.rotm(rx, ry, rz).T
    return P_ + np.array(t, float)


def antena(fr, k, t, vertical=True, s=1.0, rx=0.0, ry=0.0, rz=0.0, pos=(0, 0, 0), frac=1.0, corriente=0.0):
    if k <= 0.01:
        return
    A = _antena_pts(vertical, s, rx, ry, rz, pos)
    line3(fr, A, col=COBRE, w=2.6, a=k, glow=0.9, frac=frac)
    if corriente > 0.01:
        L = np.cumsum(np.r_[0, np.linalg.norm(np.diff(A, axis=0), axis=1)])
        for j in range(14):
            q = ((t * 1.6 + j / 14) % 1.0) * L[-1]
            i = np.searchsorted(L, q) - 1
            i = max(0, min(i, len(A) - 2))
            f = (q - L[i]) / max(1e-6, L[i + 1] - L[i])
            dot3(fr, A[i] + (A[i + 1] - A[i]) * f, r=5, col=CYAN, a=corriente, glow=1.2)


def pantalla_term(estado='acerque', u=0.0):
    key = ('term', estado, int(u * 4) % 2 if estado == 'lee' else 0)
    if key in _IM:
        return _IM[key]
    w, h = 420, 380
    im = Image.new('RGB', (w, h), (10, 14, 18))
    d = ImageDraw.Draw(im)
    if estado == 'acerque':
        d.text((210, 110), '$ 45.00', font=M.font('sans', 70), fill=(240, 240, 244), anchor='mm')
        d.text((210, 240), 'ACERQUE', font=M.font('sans', 40), fill=(170, 220, 240), anchor='mm')
        d.text((210, 290), 'SU TARJETA', font=M.font('sans', 40), fill=(170, 220, 240), anchor='mm')
    elif estado == 'lee':
        d.text((210, 150), 'LEYENDO…', font=M.font('sans', 46), fill=(240, 240, 244), anchor='mm')
        for i in range(4):
            c = (120, 225, 255) if (i + key[2]) % 2 else (40, 70, 90)
            d.rounded_rectangle((90 + i * 64, 240, 140 + i * 64, 270), radius=8, fill=c)
    elif estado == 'ok':
        im.paste((20, 70, 40), (0, 0, w, h))
        d.text((210, 130), '✓', font=M.font('sans', 130), fill=VERDE, anchor='mm')
        d.text((210, 280), 'APROBADO', font=M.font('sans', 50), fill=(230, 255, 236), anchor='mm')
    elif estado == 'no':
        im.paste((80, 18, 18), (0, 0, w, h))
        d.line([(160, 80), (260, 180)], fill=ROJO, width=16)
        d.line([(260, 80), (160, 180)], fill=ROJO, width=16)
        d.text((210, 280), 'RECHAZADA', font=M.font('sans', 50), fill=(255, 220, 216), anchor='mm')
    elif estado == 'una':
        im.paste((70, 56, 12), (0, 0, w, h))
        d.text((210, 110), '¡2 TARJETAS!', font=M.font('sans', 46), fill=(255, 236, 160), anchor='mm')
        d.text((210, 220), 'PRESENTE', font=M.font('sans', 40), fill=(255, 250, 230), anchor='mm')
        d.text((210, 275), 'SOLO UNA', font=M.font('sans', 40), fill=(255, 250, 230), anchor='mm')
    elif estado == 'nada':
        d.text((210, 110), '$ 45.00', font=M.font('sans', 70), fill=(120, 120, 126), anchor='mm')
        d.text((210, 260), '…', font=M.font('sans', 80), fill=(120, 120, 126), anchor='mm')
    _IM[key] = im
    return im


def terminal(estado='acerque', u=0.0, s=1.0, ry=0.0, t=(0, 0, 0)):
    """Terminal de cobro acostada (pantalla hacia arriba, teclado hacia el frente +z)."""
    # el cuerpo va en dos mitades para que la pantalla no quede tapada por la tapa (orden de pintado por profundidad)
    atras = named(M3.rbox(1.0, 0.24, 0.86, 0.12, (34, 36, 42), n=4, shadow=0, gloss=0.45).tf(t=(0, 0, -0.42)), 'term', rim=0.7, gloss=0.45)
    frente = named(M3.rbox(1.0, 0.24, 0.86, 0.12, (34, 36, 42), n=4, shadow=0, gloss=0.45).tf(t=(0, 0, 0.42)), 'term', rim=0.7, gloss=0.45)
    scr = named(M3.box(0.8, 0.02, 0.72, (8, 10, 14), shadow=0, base=True, gloss=0.9).tf(t=(0, 0.235, -0.4)), 'scr', gloss=0.9, rim=0.2)
    M3.decal(scr, scr.FACE['top'], pantalla_term(estado, u).convert('RGBA'))
    ms = [atras, frente, scr]
    for j in range(4):
        for i in range(3):
            ms.append(named(M3.box(0.2, 0.03, 0.13, (70, 72, 80), shadow=0, base=True, gloss=0.5)
                            .tf(t=((i - 1) * 0.25, 0.24, 0.12 + j * 0.17)), 'tecla', rim=0.5))
    return P.tfk(ms, s=s, ry=ry, t=t)


SCR_C = np.array([0.0, 0.25, -0.38])        # centro de la pantalla de la terminal (sin escala)


def campo(fr, t, C, k=1.0, n=4, alto=1.1, ancho=0.9, col=CYAN, rapido=1.0):
    """Líneas de campo que salen de la terminal y oscilan (13.56 MHz, en cámara lenta)."""
    if k <= 0.01:
        return
    C = np.asarray(C, float)
    for j in range(n):
        f = (j + 1) / n
        a = k * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 14 * rapido - j * 1.3)))
        th = np.linspace(0, math.pi, 40)
        for zz in (-0.12, 0.12):
            pts = [C + np.array([-ancho * f * math.cos(a_), alto * f * math.sin(a_), zz]) for a_ in th]
            line3(fr, pts, col=col, w=2.0, a=a * 0.8, glow=1.0)


def cota(img, fx, x0, y0, x1, y1, txt, k, col=AMARILLO, lado=1):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    yb = y0 + (y1 - y0) * eout(k)
    d.line([(x0, y0), (x1, yb)], fill=col, width=5)
    for (x, y) in ((x0, y0), (x1, yb)):
        d.line([(x - 24, y), (x + 24, y)], fill=col, width=5)
    ImageDraw.Draw(fx).line([(x0, y0), (x1, yb)], fill=M.scale_c(col, 0.5), width=12)
    if k > 0.6:
        d.text((x0 + 40 * lado, (y0 + yb) / 2), txt, font=M.font('sans', 64), fill=col, anchor='lm' if lado > 0 else 'rm')


# ================================================================== escenas
# 0. gancho, inicio tipo 10: la tarjeta normal y, con el golpe, rayos X: antena en espiral y chip
def s_gancho(t, fi, u, d):
    ux = 0.15                                   # golpe: se vuelve de cristal
    up = wt(0, 5) - 0.05                        # «y paga»: bip de la terminal
    fr = Frame(cam(u, [K(-1.5, 4.0, -55, 18, ty=1.1), K(ux, 3.2, -14, 8, ty=1.1), K(up, 3.5, 10, 14, ty=0.95), K(3.0, 3.4, 14, 14, ty=0.95)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'PILA', u, t0=-0.8, cy=0.33, entrada='golpe')
    ry = 25 * math.sin(t * 0.8) - 30 * (1 - P.eout4(seg(u, -1.4, ux)))
    xr = ease(seg(u, ux, ux + 0.12))
    pos = (0, 1.15, 0)
    if u > up - 0.3:
        e = P.entrada(u, up - 0.3, 0.25, 'desliza')
        draw_objects(fr, terminal('ok' if u > up + 0.15 else 'acerque', u, s=0.7, t=(e['dy'] * 0.4, 0, 0.3)))
    draw_objects(fr, tarjeta('azul', ry=ry, t=pos), xray=xr, keep=('chip',))
    antena(fr, xr, t, ry=ry, pos=pos, corriente=xr * seg(u, up - 0.2, up))

    def ui(img, fx):
        kicker(img, 'RAYOS X · TARJETA SIN CONTACTO', 150, seg(u, ux, ux + 0.3), col=(150, 210, 230))
        P.titulo_golpe(img, fx, [('Tu tarjeta no tiene pila…', 'sans'), ('y paga.', 'serif')], 200, seg(u, ux, ux + 0.15), size=72)
        if u > up + 0.15:
            check(img, fx, 540, 1430, seg(u, up + 0.15, up + 0.4), 'PAGADO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ux, 0.35) + 0.6 * golpe_k(u, up + 0.15, 0.3), amp=22)


# 1. ¿de dónde saca la energía? de la terminal (la tarjeta flota con «?» y la terminal cae desde arriba)
def s_energia(t, fi, u, d):
    ut = wt(1, 5) - 0.1
    fr = Frame(cam(u, [K(-0.2, 3.6, 40, 12, ty=0.9), K(0.3, 3.2, 10, 10, ty=0.9), K(ut, 4.2, -14, 24, ty=0.7), K(4.0, 4.1, -16, 24, ty=0.7)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0)
    e = P.entrada(u, ut, 0.3, 'cae')
    if u > ut:
        draw_objects(fr, terminal('acerque', u, s=0.85, t=(0, -e['dy'] * 0.5, 0.2)))
    draw_objects(fr, tarjeta('azul', ry=-20 + 10 * math.sin(t), t=(0, 1.5 + 0.06 * math.sin(t * 2.4), -0.3)))
    pq = fr.cam.p1((0.0, 1.5, -0.3))

    def ui(img, fx):
        kicker(img, 'NO TIENE BATERÍA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        glass_type(img, fx, '?', pq[0] + 300, pq[1] - 150, 260, k=eout(seg(u, 0.1, 0.4)) * (1 - seg(u, ut, ut + 0.2)))
        if u > ut + 0.3:
            P.titulo_golpe(img, fx, [('De la', 'sans'), ('terminal.', 'serif')], 240, seg(u, ut + 0.3, ut + 0.45), size=90)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut + 0.3, 0.35), amp=22)


# 2. crea un campo magnético que cambia más de 13 millones de veces por segundo (campo que late + contador)
def s_campo(t, fi, u, d):
    un = wt(2, 7) - 0.15                         # «trece»
    fr = Frame(cam(u, [K(-0.2, 3.6, -40, 22, ty=0.8), K(0.3, 3.3, -8, 18, ty=0.8), K(un, 4.0, 22, 14, ty=1.0), K(5.0, 4.0, 24, 14, ty=1.0)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'CAMPO', u, t0=0.0, cy=0.3, entrada='zoom')
    draw_objects(fr, terminal('acerque', u, s=0.85))
    campo(fr, t, SCR_C * 0.85, k=seg(u, 0.05, 0.4), n=5, alto=1.5, ancho=1.1, rapido=1.0 + 2.0 * seg(u, un, un + 0.5))
    cnt = int(13_560_000 * P.eout4(seg(u, un - 0.6, un + 0.1)))

    def ui(img, fx):
        kicker(img, 'CAMPO MAGNÉTICO · 13.56 MHz', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if u > un - 0.6:
            txt = f'{cnt:,}'.replace(',', ' ')
            ImageDraw.Draw(img).text((540, 1250), txt, font=M.font('sansx', 110), fill=AMARILLO, anchor='mm')
            ImageDraw.Draw(fx).text((540, 1250), txt, font=M.font('sansx', 110), fill=(110, 100, 60), anchor='mm')
            kicker(img, 'VECES POR SEGUNDO', 1340, seg(u, un, un + 0.3), col=AMARILLO, size=30)
        pill(img, fx, 540, 1430, 'CÁMARA LENTA · RECREACIÓN', 1.0, size=22, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.1, 0.35), amp=18)


# 3. escondida en el plástico: la antena en espiral (zoom digital con REC, la antena se dibuja vuelta por vuelta)
def s_antena(t, fi, u, d):
    ua = wt(3, 8) - 0.1                          # «antena»
    fr = Frame(cam(u, [K(-0.2, 2.8, 0, 2, ty=1.0), K(0.3, 2.5, -6, 4, ty=1.0), K(5.0, 2.45, -8, 4, ty=1.0)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    pos = (0, 1.0, 0)
    draw_objects(fr, tarjeta('negra', '7741', t=pos), xray=1.0, keep=('chip',))
    antena(fr, 1.0, t, pos=pos, frac=0.05 + 0.95 * ease(seg(u, ua - 0.4, ua + 0.8)))
    pa = fr.cam.p1((0.62, 1.38, 0))
    z = 1.0 if u < ua else (1.35 if u < ua + 1.0 else 1.7)
    cz = (0.62, 0.36) if u > ua + 1.0 else (0.5, 0.5)

    def ui(img, fx):
        kicker(img, 'ADENTRO DEL PLÁSTICO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if u > ua:
            pill(img, fx, pa[0] - 90, pa[1] - 120, 'ANTENA', eout(seg(u, ua, ua + 0.3)), size=34, border=COBRE)
            doodle_arrow(img, fx, pa[0] - 160, pa[1] - 80, pa[0] - 10, pa[1] - 6, t, k=eout(seg(u, ua + 0.1, ua + 0.5)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if z > 1.01:
        out = M.scale_about(out, z, *cz)
    im = Image.fromarray(out)
    rec_frame(im, t, 1.0, zoom_label=f'x{z:.1f}')
    return np.asarray(im)


# 4. al entrar al campo, la antena produce electricidad (la tarjeta baja sobre la terminal y la corriente corre)
def s_luz(t, fi, u, d):
    ue = wt(4, 1) - 0.1
    fr = Frame(cam(u, [K(-0.2, 4.2, 50, 26, ty=0.6), K(0.3, 3.6, 20, 22, ty=0.6), K(ue + 0.5, 3.0, -10, 26, ty=0.6), K(4.0, 2.95, -12, 26, ty=0.6)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0)
    h = 1.35 - 0.75 * P.eout4(seg(u, ue - 0.2, ue + 0.4))
    TC = (0, h, -0.32)
    draw_objects(fr, terminal('lee' if u > ue + 0.4 else 'acerque', u, s=0.85))
    campo(fr, t, SCR_C * 0.85, k=0.9, n=4, alto=1.0, ancho=1.0)
    k_in = seg(u, ue + 0.2, ue + 0.6)
    draw_objects(fr, tarjeta('azul', vertical=False, s=0.75, t=TC), xray=1.0, keep=('chip',))
    antena(fr, 1.0, t, vertical=False, s=0.75, pos=(TC[0], TC[1] + 0.005, TC[2]), corriente=k_in)
    pc = fr.cam.p1((0.45, h + 0.05, -0.1))

    def ui(img, fx):
        kicker(img, 'INDUCCIÓN', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if k_in > 0.1:
            pill(img, fx, pc[0] + 60, pc[1] - 130, 'ELECTRICIDAD', eout(k_in), size=34, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. eso prende el chip… solo un instante (macro del chip dorado que se enciende y se apaga)
def s_chip(t, fi, u, d):
    ui0 = wt(5, 5) - 0.1                         # «instante»
    fr = Frame(cam(u, [K(-0.2, 1.3, -30, 30, tx=-0.5, ty=1.0), K(0.3, 1.05, -10, 18, tx=-0.5, ty=1.0), K(4.0, 1.0, -6, 16, tx=-0.5, ty=1.0)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.9)
    pos = (0, 1.0, 0)
    on = seg(u, 0.25, 0.35) * (1 - seg(u, ui0 + 0.3, ui0 + 0.45))
    draw_objects(fr, tarjeta('azul', t=pos), xray=1.0, keep=('chip',))
    antena(fr, 0.8, t, pos=pos, corriente=on)
    C = np.array([-0.5, 1.0 - 0.02, 0.03])
    for i in range(3):
        for j in range(2):
            p = C + np.array([-0.06 + 0.06 * i, -0.04 + 0.08 * j, 0.0])
            dot3(fr, p, r=6, col=AMARILLO, a=on, glow=1.6)
    pc = fr.cam.p1(C)

    def ui(img, fx):
        kicker(img, 'CHIP', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if on > 0.05:
            ImageDraw.Draw(fx).ellipse((pc[0] - 220, pc[1] - 220, pc[0] + 220, pc[1] + 220), fill=M.scale_c(AMARILLO, 0.25 * on))
        pill(img, fx, 540, 1430, 'ENCENDIDO' if on > 0.5 else 'APAGADO', 1.0, size=34, border=AMARILLO if on > 0.5 else (150, 150, 160))
        if u > ui0:
            P.titulo_golpe(img, fx, [('Solo un', 'sans'), ('instante.', 'serif')], 260, seg(u, ui0, ui0 + 0.15), size=86)
    fr.ui.append(ui)
    out = finish(fr, fi, flash=0.25 * golpe_k(u, 0.25, 0.25))
    return sacudir(out, t, golpe_k(u, ui0 + 0.15, 0.3), amp=16)


# 6. pero el campo es chiquito: unos 4 centímetros (vista de lado con cota + gráfico 4 contra 10)
def s_4cm(t, fi, u, d):
    u4 = wt(6, 6) - 0.15
    fr = Frame(cam(u, [K(-0.2, 3.6, 70, 6, ty=0.6, tx=-0.4), K(0.3, 3.2, 88, 4, ty=0.6, tx=-0.4), K(4.0, 3.15, 90, 4, ty=0.6, tx=-0.4)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0)
    draw_objects(fr, terminal('acerque', u, s=0.85))
    campo(fr, t, SCR_C * 0.85, k=1.0, n=3, alto=0.45, ancho=0.5)
    y0, y1 = fr.cam.p1((0, 0.22, -0.32)), fr.cam.p1((0, 0.62, -0.32))

    def ui(img, fx):
        kicker(img, 'ALCANCE', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        cota(img, fx, y0[0] + 260, y0[1], y1[0] + 260, y1[1], '4 cm', seg(u, u4 - 0.2, u4 + 0.1))
        chart_grow(img, fx, (140, 260, 940, 900), [4, 10], ['TÍPICO', 'MÁXIMO'], t - u + 0.2, t, unit='cm', title_txt='CENTÍMETROS',
                   vmax=12, line=False, tag='THALES')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u4 + 0.1, 0.3), amp=16)


# 7. pegada, cobra. A 10 centímetros… nada (duelo: arriba pegada y aprobada, abajo lejos y nada)
def s_duelo(t, fi, u, d):
    u10 = wt(7, 2) - 0.1
    lejos = u > u10
    fr = Frame(cam(u, [K(-0.2, 3.4, 30, 44, ty=0.4), K(0.3, 3.1, 12, 42, ty=0.4), K(u10, 3.9, -18, 30, ty=0.7), K(5.0, 3.9, -20, 30, ty=0.7)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    h = 0.32 if not lejos else 0.32 + 0.9 * P.eout4(seg(u, u10, u10 + 0.35))
    est = ('ok' if u > 0.5 else 'lee') if not lejos else 'nada'
    draw_objects(fr, terminal(est, u, s=0.85))
    campo(fr, t, SCR_C * 0.85, k=1.0, n=3, alto=0.45, ancho=0.5, col=CYAN)
    draw_objects(fr, tarjeta('azul', vertical=False, s=0.7, t=(0.42, h, -0.12)))
    p0, p1 = fr.cam.p1((1.0, 0.24, -0.12)), fr.cam.p1((1.0, h, -0.12))

    def ui(img, fx):
        if not lejos:
            pill(img, fx, 540, 300, 'PEGADA', 1.0, size=40, border=VERDE, dot=False)
            if u > 0.5:
                check(img, fx, 540, 1430, seg(u, 0.5, 0.75), 'COBRA')
        else:
            pill(img, fx, 540, 300, 'A 10 CM', 1.0, size=40, border=ROJO, dot=False)
            cota(img, fx, p0[0] + 40, p0[1], p1[0] + 40, p1[1], '10 cm', seg(u, u10 + 0.2, u10 + 0.5), col=ROJO)
            if u > u10 + 0.7:
                tache(img, fx, 540, 1430, seg(u, u10 + 0.7, u10 + 0.95), 'NADA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.5, 0.25) + golpe_k(u, u10 + 0.7, 0.3), amp=14)


# 8. mándaselo a quien todavía mete la tarjeta (la tarjeta entra en la ranura de la terminal)
def s_mete(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.8, -40, 18, ty=0.5, tz=0.3), K(0.3, 3.3, -10, 16, ty=0.5, tz=0.3), K(3.0, 3.2, -6, 16, ty=0.5, tz=0.3)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    ms = terminal('lee', u, s=0.85, ry=180)
    k = P.eout4(seg(u, 0.3, 0.9))
    ms += tarjeta('roja', '0412', rx=0, t=(0, 0.6 + 0.01, 1.65 - 0.55 * k), s=0.6)
    draw_objects(fr, ms)

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien', 'sans'), ('todavía la mete.', 'serif')], 190, seg(u, 0.0, 0.35), size=80)
        pill(img, fx, 540, 1430, 'Y TECLEA SU NIP', eout(seg(u, 0.9, 1.2)), size=34, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.9, 0.25), amp=12)


# 9. segundo gancho: el error que casi todos cometemos → dos tarjetas juntas en la cartera
def s_error(t, fi, u, d):
    uc = wt(8, 6) - 0.1                          # «dos tarjetas…»: aparece la cartera
    if u < uc:
        fr = Frame(cam(u, [K(-0.2, 2.6, 0, 4, ty=1.0, roll=10), K(0.25, 3.2, -8, 6, ty=1.0), K(4.0, 3.1, -10, 6, ty=1.0)], cy=0.55))
        space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
        M.cristal(fr.base, fr.fx, 'ERROR', u, t0=-0.1, cy=0.42, entrada='golpe', brillo=1.2)
        draw_objects(fr, tarjeta('azul', ry=-14, rz=8, t=(0, 0.95, 0.2)), xray=0.0)

        def ui(img, fx):
            kicker(img, '¡OJO!', 150, seg(u, 0.0, 0.2), col=ROJO, size=34)
            P.titulo_golpe(img, fx, [('El error', 'sans'), ('de casi todos.', 'serif')], 1240, seg(u, 0.15, 0.3), size=82, col=(255, 160, 150))
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.35), amp=24)
    v = u - uc
    fr = Frame(cam(v, [K(-0.1, 4.0, 40, 30, ty=0.4), K(0.3, 3.4, 14, 26, ty=0.4), K(4.0, 3.3, 10, 26, ty=0.4)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    cart = named(M3.rbox(2.0, 0.2, 1.25, 0.12, (96, 58, 34), n=4, shadow=0, gloss=0.2), 'cartera', rim=0.5, gloss=0.2)
    e = P.entrada(v, 0.0, 0.25, 'cae')
    ms = [cart.tf(t=(0, -e['dy'] * 0.2, 0))]
    k = P.eout4(seg(v, 0.2, 0.6))
    ms += tarjeta('azul', '2026', vertical=False, s=0.8, ry=-6 * k, t=(-0.15 * k, 0.21, -0.25 - 0.35 * k))
    ms += tarjeta('negra', '7741', vertical=False, s=0.8, ry=8 * k, t=(0.2 * k, 0.24, -0.2 - 0.25 * k))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'DOS SIN CONTACTO JUNTAS', 150, seg(v, 0.0, 0.3), col=(255, 140, 120))
        pill(img, fx, 540, 1430, 'EN LA MISMA CARTERA', eout(seg(v, 0.5, 0.8)), size=34, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.25, 0.3), amp=16)


# 10. la terminal detecta dos chips y no sabe cuál cobrar (dos chips señalados con «?» y aviso «presente solo una»)
def s_dos(t, fi, u, d):
    uq = wt(9, 6) - 0.1
    fr = Frame(cam(u, [K(-0.2, 3.6, -30, 46, ty=0.4), K(0.3, 3.2, -6, 44, ty=0.4), K(uq, 2.9, 16, 48, ty=0.4), K(4.0, 2.85, 18, 48, ty=0.4)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    draw_objects(fr, terminal('una' if u > uq else 'lee', u, s=0.85))
    campo(fr, t, SCR_C * 0.85, k=1.0, n=3, alto=0.5, ancho=0.6, col=(255, 200, 120))
    TC = (0.0, 0.5, -0.32)
    ms = tarjeta('azul', '2026', vertical=False, s=0.7, ry=-8, t=(0.32, 0.5, -0.06))
    ms += tarjeta('negra', '7741', vertical=False, s=0.7, ry=10, t=(0.5, 0.55, 0.02))
    draw_objects(fr, ms, xray=1.0, keep=('chip',))
    c1 = fr.cam.p1((0.32 - 0.35, 0.51, -0.06))
    c2 = fr.cam.p1((0.5 - 0.35, 0.56, 0.02))

    def ui(img, fx):
        kicker(img, 'LA TERMINAL VE 2 CHIPS', 150, seg(u, 0.0, 0.3), col=(255, 200, 120))
        for i, c in enumerate((c1, c2)):
            k = seg(u, 0.3 + 0.3 * i, 0.6 + 0.3 * i)
            doodle_circle(img, fx, c[0], c[1], 70, 55, t, k=eout(k), col=AMARILLO, w=6, seed=i)
            if k > 0.5:
                ImageDraw.Draw(img).text((c[0] + (-110 if i == 0 else 110), c[1] - 90), '?', font=M.font('sansx', 90), fill=AMARILLO, anchor='mm')
        if u > uq:
            pill(img, fx, 540, 1430, '¿CUÁL COBRO?', eout(seg(u, uq, uq + 0.25)), size=38, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uq, 0.3), amp=14)


# 11. puede rechazar el pago… o cobrarle a la que no querías
def s_rechaza(t, fi, u, d):
    uo = wt(10, 4) - 0.1                         # «o cobrarle…»
    fr = Frame(cam(u, [K(-0.2, 3.3, 30, 48, ty=0.3), K(0.3, 3.0, 6, 46, ty=0.3), K(uo, 3.4, -20, 24, ty=0.7), K(4.0, 3.4, -22, 24, ty=0.7)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0)
    if u < uo:
        draw_objects(fr, terminal('no', u, s=0.85))

        def ui(img, fx):
            tache(img, fx, 540, 1430, seg(u, 0.1, 0.35), 'PAGO RECHAZADO')
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.3), amp=18)
    v = u - uo
    draw_objects(fr, terminal('ok', u, s=0.85))
    ms = tarjeta('azul', '2026', vertical=True, s=0.65, ry=-10, t=(-0.75, 1.2, 0.1))
    ms += tarjeta('negra', '7741', vertical=True, s=0.65, ry=10, t=(0.75, 1.2 + 0.15 * golpe_k(v, 0.4, 0.4), 0.1))
    draw_objects(fr, ms)
    pa, pb = fr.cam.p1((-0.75, 1.62, 0.1)), fr.cam.p1((0.75, 1.62, 0.1))

    def ui(img, fx):
        pill(img, fx, pa[0], pa[1] - 50, 'LA QUE QUERÍAS', eout(seg(v, 0.05, 0.3)), size=28, border=(150, 150, 160), dot=False)
        pill(img, fx, pb[0], pb[1] - 50, '$ COBRADA', eout(seg(v, 0.35, 0.6)), size=34, border=ROJO)
        doodle_circle(img, fx, pb[0], pb[1] + 110, 230, 170, t, k=eout(seg(v, 0.45, 0.85)), col=ROJO, w=6)
        kicker(img, 'TfL · «CARD CLASH»', 150, seg(v, 0.0, 0.3), col=(150, 152, 160))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.4, 0.3), amp=16)


# 12. sácala sola y paga con una (una tarjeta sale de la cartera, baja y aprobado)
def s_sola(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.6, -40, 40, ty=0.4), K(0.3, 3.3, -14, 38, ty=0.4), K(3.0, 3.2, -10, 38, ty=0.4)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    ut = 0.75
    draw_objects(fr, terminal('ok' if u > ut + 0.2 else 'acerque', u, s=0.85, t=(0.6, 0, 0)))
    cart = named(M3.rbox(1.6, 0.18, 1.0, 0.1, (96, 58, 34), n=4, shadow=0, gloss=0.2), 'cartera', rim=0.5).tf(t=(-1.2, 0, 0.3))
    k = P.eout4(seg(u, 0.0, ut))
    x = lerp(-1.2, 0.6, k)
    y = lerp(0.25, 0.32, k) + 0.5 * math.sin(math.pi * k)
    draw_objects(fr, [cart] + tarjeta('azul', vertical=False, s=0.7, t=(x + 0.35 * k, y, lerp(0.3, -0.1, k))))
    if u > ut:
        campo(fr, t, SCR_C * 0.85 + np.array([0.6, 0, 0]), k=0.8, n=3, alto=0.4, ancho=0.5)

    def ui(img, fx):
        M.title(img, fx, [('Una sola.', 'sans'), ('Y paga.', 'serif')], 230, seg(u, 0.05, 0.35), size=92)
        if u > ut + 0.2:
            check(img, fx, 540, 1430, seg(u, ut + 0.2, ut + 0.45), 'APROBADO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut, 0.3), amp=14)


# 13. ¿y si alguien te roza con una terminal en el camión? (camión de alambre + terminal que se acerca a la mochila)
def s_camion(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 7.5, 50, 10, ty=1.3), K(0.3, 6.0, 24, 8, ty=1.3), K(3.0, 5.8, 18, 8, ty=1.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    k = seg(u, 0.0, 0.5)
    W_, H_ = 2.6, 1.3
    bus = [(-W_, 0.35, 0), (W_, 0.35, 0), (W_, 0.35 + 2 * H_, 0), (-W_ + 0.3, 0.35 + 2 * H_, 0), (-W_, 0.35 + 2 * H_ - 0.3, 0), (-W_, 0.35, 0)]
    line3(fr, bus, col=WHITE, w=3, a=1.0, glow=0.7, frac=0.1 + 0.9 * k)
    for i in range(5):
        x0 = -W_ + 0.4 + i * 0.95
        line3(fr, [(x0, 1.6, 0), (x0 + 0.75, 1.6, 0), (x0 + 0.75, 2.6, 0), (x0, 2.6, 0), (x0, 1.6, 0)], col=WHITE, w=2, a=0.7 * k, glow=0.5)
    th = np.linspace(0, 2 * math.pi, 30)
    for xw in (-1.6, 1.7):
        line3(fr, [(xw + 0.35 * math.cos(a), 0.35 + 0.35 * math.sin(a), 0.02) for a in th], col=WHITE, w=3, a=k, glow=0.6)
    e = P.entrada(u, 0.6, 0.3, 'desliza')
    draw_objects(fr, terminal('acerque', u, s=0.45, t=(0.9 + e['dy'] * 0.3, 1.0, 0.8)))
    mo = named(M3.rbox(0.8, 1.0, 0.4, 0.12, (40, 60, 80), n=3, shadow=0, gloss=0.3), 'mochila', rim=0.6)
    draw_objects(fr, [mo.tf(t=(-0.2, 0.9, 0.7))])

    def ui(img, fx):
        kicker(img, 'MITO O REALIDAD', 150, seg(u, 0.0, 0.3), col=AMARILLO, size=34)
        glass_type(img, fx, '¿?', 540, 400, 200, k=eout(seg(u, 0.4, 0.7)))
        pill(img, fx, 540, 1430, 'RECREACIÓN', 1.0, size=22, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. tendría que pegártela (cota de 4 cm) y cada terminal está registrada a un comercio y a un banco (red)
def s_registro(t, fi, u, d):
    ur = wt(13, 4) - 0.15                        # «cada terminal…»
    if u < ur:
        fr = Frame(cam(u, [K(-0.2, 3.8, 40, 14, ty=0.8, tz=0.4), K(0.3, 3.4, 58, 10, ty=0.8, tz=0.4), K(4.0, 3.35, 62, 10, ty=0.8, tz=0.4)], cy=0.55))
        space(fr, t, floor=None, bokeh=1.0)
        k = P.eout4(seg(u, 0.0, 0.6))
        mo = named(M3.rbox(0.8, 1.2, 0.4, 0.12, (70, 100, 130), n=3, shadow=0, gloss=0.3), 'mochila', rim=0.8)
        draw_objects(fr, [mo.tf(t=(0, 0.4, -0.35))])
        pm = fr.cam.p1((0, 1.7, -0.35))
        term = terminal('acerque', u, s=0.45)
        draw_objects(fr, P.tfk(term, rx=-90, t=(0, 1.0, lerp(1.6, 0.25, k))))
        p0, p1 = fr.cam.p1((0, 1.0, -0.12)), fr.cam.p1((0, 1.0, 0.25 - 0.06))

        def ui(img, fx):
            kicker(img, 'TENDRÍA QUE PEGÁRTELA', 150, seg(u, 0.0, 0.3), col=AMARILLO)
            pill(img, fx, pm[0], pm[1] - 40, 'TU MOCHILA', eout(seg(u, 0.1, 0.4)), size=30, border=(150, 190, 230), dot=False)
            if k > 0.95:
                d_ = ImageDraw.Draw(img)
                d_.line([(p0[0], p0[1] - 260), (p1[0], p1[1] - 260)], fill=AMARILLO, width=5)
                d_.text(((p0[0] + p1[0]) / 2, p0[1] - 320), '≤ 4 cm', font=M.font('sans', 60), fill=AMARILLO, anchor='mm')
        fr.ui.append(ui)
        return finish(fr, fi)
    v = u - ur
    fr = Frame(Cam(target=(0, 0.6, 0), dist=5.0, yaw=8 * math.sin(t * 0.5), pitch=10, cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0)
    e = P.entrada(v, 0.0, 0.25, 'pop')
    draw_objects(fr, terminal('acerque', u, s=0.5 * max(0.05, e['escala']), t=(0, 0.0, 0.6)))
    pt = fr.cam.p1((0, 0.4, 0.6))
    nodos = [(260, 620, 'COMERCIO', 0.35), (820, 620, 'BANCO', 0.9)]

    def ui(img, fx):
        kicker(img, 'CADA TERMINAL TIENE DUEÑO', 150, seg(v, 0.0, 0.3), col=(150, 210, 230))
        dd = ImageDraw.Draw(img)
        df = ImageDraw.Draw(fx)
        for (x, y, lab, v0) in nodos:
            k = eout(seg(v, v0, v0 + 0.35))
            if k <= 0.01:
                continue
            xb, yb = pt[0] + (x - pt[0]) * k, pt[1] + (y + 110 - pt[1]) * k
            dd.line([(pt[0], pt[1]), (xb, yb)], fill=CYAN, width=4)
            df.line([(pt[0], pt[1]), (xb, yb)], fill=(50, 90, 100), width=10)
            c = M.scale_c(WHITE, k)
            if lab == 'COMERCIO':
                dd.rectangle((x - 110, y - 40, x + 110, y + 100), outline=c, width=5)
                for i in range(5):
                    dd.polygon([(x - 130 + i * 52, y - 40), (x - 78 + i * 52, y - 40), (x - 104 + i * 52, y - 90)], outline=c)
                dd.rectangle((x - 30, y + 20, x + 30, y + 100), outline=c, width=4)
            else:
                dd.polygon([(x - 130, y - 30), (x + 130, y - 30), (x, y - 110)], outline=c, width=5)
                for i in range(4):
                    dd.rectangle((x - 100 + i * 60, y - 20, x - 80 + i * 60, y + 80), outline=c, width=4)
                dd.line([(x - 130, y + 95), (x + 130, y + 95)], fill=c, width=6)
            df.rectangle((x - 140, y - 120, x + 140, y + 110), outline=M.scale_c(WHITE, 0.25 * k), width=10)
            pill(img, fx, x, y + 180, lab, k, size=32, border=CYAN)
        pill(img, fx, 540, 1430, 'SI TE COBRA, SE SABE QUIÉN FUE', eout(seg(v, 1.4, 1.7)), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. cada pago lleva un código que no se repite (tres pagos, tres códigos distintos)
CODIGOS = ['9F26 · A7F3 1C84 D2E0 5B19', '9F26 · 04BE 77D2 9A13 C6F1', '9F26 · E5C2 3B07 F41A 8D6E']


def s_codigo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.4, 30, 46, ty=0.4), K(0.3, 3.0, 4, 44, ty=0.4), K(4.0, 2.95, 0, 44, ty=0.4)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0)
    taps = [0.2, 1.1, 2.0]
    n = sum(1 for x in taps if u > x)
    ph = min((u - x) for x in taps if u > x) if n else 1.0
    h = 0.32 + 0.8 * clamp(abs(ph - 0.45) / 0.45) if n else 1.1
    draw_objects(fr, terminal('ok' if (n and ph < 0.5) else 'acerque', u, s=0.85))
    draw_objects(fr, tarjeta('azul', vertical=False, s=0.7, t=(0.42, h, -0.12)))

    def ui(img, fx):
        kicker(img, 'CÓDIGO DE UN SOLO USO · EJEMPLO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        dd = ImageDraw.Draw(img)
        for i in range(n):
            y = 300 + i * 90
            col = AMARILLO if i == n - 1 else (150, 152, 160)
            dd.text((540, y), f'PAGO {i + 1}  {CODIGOS[i][7:]}', font=M.font('mono', 40), fill=col, anchor='mm')
        if n == 3:
            pill(img, fx, 540, 1430, 'NINGUNO SE REPITE', eout(seg(u, 2.2, 2.45)), size=34, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    k = sum(golpe_k(u, x + 0.45, 0.2) for x in taps)
    return sacudir(finish(fr, fi), t, k, amp=10)


# 16. si alguien lo copia, ya no le sirve (código copiado con sello COPIA → rechazado)
def s_copia(t, fi, u, d):
    ur = wt(15, 4) - 0.1
    fr = Frame(cam(u, [K(-0.2, 3.0, -20, 48, ty=0.3), K(0.3, 3.2, 4, 46, ty=0.3), K(ur, 2.8, 14, 52, ty=0.3), K(4.0, 2.75, 16, 52, ty=0.3)], cy=0.62))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0)
    draw_objects(fr, terminal('no' if u > ur + 0.2 else 'lee', u, s=0.85))

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        k = eout(seg(u, 0.0, 0.25))
        dd.text((540, 330), CODIGOS[2][7:], font=M.font('mono', 52), fill=M.scale_c((150, 152, 160), k), anchor='mm')
        if u > 0.4:
            P.titulo_golpe(img, fx, [('COPIA', 'sans')], 380, seg(u, 0.4, 0.55), size=110, col=ROJO)
        if u > ur + 0.2:
            tache(img, fx, 540, 1430, seg(u, ur + 0.2, ur + 0.45), 'YA NO SIRVE')
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, 0.55, 0.3) + golpe_k(u, ur + 0.2, 0.3), amp=20)


# 17. mándaselo a alguien que le tiene miedo a pagar sin contacto (la tarjeta de cristal paga una vez más)
def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.0, 50, 14, ty=0.8), K(0.3, 3.5, 16, 12, ty=0.8), K(4.0, 3.4, 10, 12, ty=0.8)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    up = 1.0
    draw_objects(fr, terminal('ok' if u > up else 'acerque', u, s=0.75, t=(0, 0, 0.4)))
    h = 1.3 - 0.4 * P.eout4(seg(u, 0.3, up))
    draw_objects(fr, tarjeta('azul', ry=10 * math.sin(t), t=(0, h, -0.1), s=0.85), xray=0.6, keep=('chip',))
    antena(fr, 0.8, t, s=0.85, ry=10 * math.sin(t), pos=(0, h, -0.1), corriente=seg(u, up - 0.3, up))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien le da', 'sans'), ('miedo pagar sin contacto.', 'serif')], 170, seg(u, 0.0, 0.35), size=60)
        if u > up:
            check(img, fx, 540, 1430, seg(u, up, up + 0.25), 'SEGURO')
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[]),
           dict(desde=1, fn=s_energia, tr='cubo_izq', sfx=[]),
           dict(desde=2, fn=s_campo, tr='iris', c=(0.5, 0.62), sfx=[]),
           dict(desde=3, fn=s_antena, tr='zoom', sfx=[]),
           dict(desde=4, fn=s_luz, tr='flash', sfx=[]),
           dict(desde=5, fn=s_chip, tr='push', c=(0.3, 0.5), sfx=[]),
           dict(desde=6, fn=s_4cm, tr='wipe', sfx=[]),
           dict(desde=7, fn=s_duelo, tr='rebanadas', sfx=[]),
           dict(desde=8, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[]),
           dict(desde=9, fn=s_dos, tr='mosaico', sfx=[]),
           dict(desde=10, fn=s_rechaza, tr='glitch', sfx=[]),
           dict(desde=11, fn=s_sola, tr='deslizar_abajo', sfx=[]),
           dict(desde=12, fn=s_camion, tr='giro', sfx=[]),
           dict(desde=13, fn=s_registro, tr='whip_izq', sfx=[]),
           dict(desde=14, fn=s_codigo, tr='cristal', palabra='CÓDIGO', sfx=[]),
           dict(desde=15, fn=s_copia, tr='golpe', sfx=[]),
           dict(desde=16, fn=s_mandalo, tr='ritmo', sfx=[]),
           dict(desde=17, loop=True, tr='remolino')]


def _sfx_dinamicos():
    E = ESCENAS
    up = wt(0, 5) - 0.05
    E[0]['sfx'] = [(-1.2, 'whoosh_suave', 0.5), (0.15, 'sub', 1.0), (0.17, 'shimmer', 0.7), (up - 0.3, 'whoosh', 0.5),
                   (up + 0.15, 'chime_c', 0.9), (up + 0.17, 'click', 0.6)]
    ut = wt(1, 5) - 0.1
    E[1]['sfx'] = [(0.1, 'shimmer', 0.4), (ut, 'whoosh', 0.6), (ut + 0.3, 'thud', 1.0), (ut + 0.32, 'bass', 0.8)]
    un = wt(2, 7) - 0.15
    E[2]['sfx'] = [(0.05, 'riser', 0.4)] + [(un - 0.6 + 0.08 * i, 'tick2', 0.25) for i in range(9)] + [(un + 0.1, 'bass', 1.0)]
    ua = wt(3, 8) - 0.1
    E[3]['sfx'] = [(0.0, 'click', 0.7), (ua - 0.4, 'scribble', 0.5), (ua, 'click', 0.8), (ua + 1.0, 'click', 0.8), (ua + 0.1, 'tick', 0.6)]
    ue = wt(4, 1) - 0.1
    E[4]['sfx'] = [(ue - 0.2, 'whoosh', 0.6), (ue + 0.2, 'shimmer', 0.7), (ue + 0.5, 'tick2', 0.5)]
    ui0 = wt(5, 5) - 0.1
    E[5]['sfx'] = [(0.25, 'burst', 0.4), (0.27, 'chime_b', 0.7), (ui0, 'whoosh', 0.4), (ui0 + 0.15, 'bass', 0.9), (ui0 + 0.35, 'tick', 0.5)]
    u4 = wt(6, 6) - 0.15
    E[6]['sfx'] = [(0.2 + 0.25, 'chime_a', 0.6), (0.2 + 0.53, 'chime_c', 0.6), (u4, 'whoosh', 0.4), (u4 + 0.1, 'bass', 0.8)]
    u10 = wt(7, 2) - 0.1
    E[7]['sfx'] = [(0.5, 'chime_c', 0.8), (u10, 'whoosh', 0.6), (u10 + 0.7, 'thud', 0.9), (u10 + 0.72, 'burst', 0.3)]
    uc = wt(8, 6) - 0.1
    E[8]['sfx'] = [(0.0, 'sub', 0.9), (0.3, 'bass', 1.0), (uc, 'whoosh', 0.5), (uc + 0.25, 'thud', 0.8), (uc + 0.5, 'slap', 0.6)]
    uq = wt(9, 6) - 0.1
    E[9]['sfx'] = [(0.3, 'scribble', 0.5), (0.6, 'scribble', 0.5), (0.35, 'tick2', 0.5), (0.65, 'tick2', 0.5), (uq, 'digital', 0.6), (uq + 0.05, 'bass', 0.6)]
    uo = wt(10, 4) - 0.1
    E[10]['sfx'] = [(0.1, 'burst', 0.5), (0.12, 'sub', 0.9), (uo, 'whoosh', 0.5), (uo + 0.4, 'slap', 0.8), (uo + 0.45, 'scribble', 0.5)]
    E[11]['sfx'] = [(0.0, 'whoosh', 0.6), (0.75, 'thud', 0.7), (0.95, 'chime_c', 0.8)]
    E[12]['sfx'] = [(0.0, 'scribble', 0.4), (0.4, 'shimmer', 0.5), (0.6, 'whoosh', 0.6)]
    ur = wt(13, 4) - 0.15
    E[13]['sfx'] = [(0.0, 'whoosh', 0.6), (0.6, 'tick', 0.7), (ur, 'whoosh_suave', 0.5), (ur + 0.35, 'chime_a', 0.6), (ur + 0.9, 'chime_b', 0.6),
                    (ur + 1.4, 'tick', 0.6)]
    E[14]['sfx'] = sum([[(x + 0.45, 'chime_c', 0.6), (x + 0.5, 'tick2', 0.5)] for x in (0.2, 1.1, 2.0)], []) + [(2.2, 'bass', 0.6)]
    ur16 = wt(15, 4) - 0.1
    E[15]['sfx'] = [(0.0, 'tick', 0.5), (0.55, 'slap', 1.0), (0.55, 'bass', 0.6), (ur16 + 0.2, 'burst', 0.5), (ur16 + 0.22, 'sub', 0.8)]
    E[16]['sfx'] = [(0.0, 'shimmer', 0.5), (0.3, 'whoosh_suave', 0.5), (1.0, 'chime_c', 0.8)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
