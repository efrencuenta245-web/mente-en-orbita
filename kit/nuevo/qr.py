"""Reel diario: «Tu QR sirve aunque lo rompas.» Dom 8-nov-2026, 8:00. Voz Isaac. Estilo rápido (ESTILO.md §11-12).
Inicio tipo 3 (se arma solo: los pedazos del QR vuelan, se juntan y hacen clic; luego se le rompe una esquina y sigue leyendo).
Primera transición: rompe. El QR que sale en el video es REAL (versión 2, nivel H, dice «MENTE EN ORBITA»): qr_codigo.py lo
genera y cada daño que se muestra como «sí lee» se probó con un lector de QR (OpenCV) antes de renderizar (`python3 qr.py probar`).
Datos: QR creado en 1994 por Denso Wave (Japón) para rastrear autopartes; 4 niveles de corrección L 7 %, M 15 %, Q 25 %, H 30 %;
código Reed-Solomon (1960; el mismo de los CD y de sondas como la Voyager); 3 patrones de posición en las esquinas para ubicarlo y
saber su giro. Fuentes en guiones/2026-11-08_qr.txt."""
import math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
import norte as N
import qr_codigo as Q
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'qr'
TXT = ['Tu QR sirve aunque lo rompas.',
       'Rayado, manchado o con un pedazo menos… tu celular lo lee.',
       '¿Por qué? Trae su propio repuesto.',
       'Nació en 1994 en Japón, para aguantar la mugre de una fábrica de autopartes.',
       'Guarda tu información… y además un respaldo hecho con matemáticas.',
       'Con el nivel más alto, aguanta que le falte cerca del 30 %.',
       'Hasta le ponen un logo en medio y sigue funcionando.',
       'Pero hay tres cuadros que nunca debes tapar: los de las esquinas.',
       'Le dicen a tu cámara dónde está el código y hacia dónde está girado.',
       'Si los tapas, aunque lo demás esté perfecto, ya no lo encuentra.',
       'Por dentro, cada cuadrito es un uno o un cero.',
       'Se juntan en bloques de ocho, como letras.',
       'El respaldo usa la misma matemática que los CD y las naves espaciales.',
       'Si falta un pedazo, tu celular resuelve la ecuación y lo rellena.',
       'Por eso el QR de la taquería sigue jalando con todo y salsa.',
       'Y el de la tiendita, aunque esté todo rayado.',
       'Mándaselo a alguien que cree que un QR rayado ya no sirve.',
       'Y recuerda:']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-08_qr_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
CUT = 7          # frase quitada el 6-nov (pedido de Efrén: el «mándaselo a…» solo al final, nunca a la mitad)


def _ix(i):
    """Índice de frase viejo (el de las escenas) → índice nuevo (sin la frase CUT)."""
    return i - 1 if i > CUT else i

AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 70, 60)
SALSA = (170, 34, 20)

# ================================================================== el QR real
QM, QF = Q.matriz('MENTE EN ORBITA')
NQ = 25
QZ = 3                      # margen blanco (zona de silencio) en módulos
NT = NQ + 2 * QZ            # 31 unidades
PX = 14                     # px por módulo en la textura
TS = NT * PX


def _idx_map():
    """Qué codeword (0–43) guarda cada módulo de datos: < 16 datos, ≥ 16 respaldo (Reed-Solomon)."""
    I = [[-1] * NQ for _ in range(NQ)]
    i, right = 0, NQ - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(NQ):
            for j in range(2):
                x = right - j
                up = ((right + 1) & 2) == 0
                y = NQ - 1 - vert if up else vert
                if not QF[y][x] and i < 44 * 8:
                    I[y][x] = i >> 3
                    i += 1
        right -= 2
    return I


QI = _idx_map()
_TX = {}


def _rng(seed):
    return np.random.RandomState(seed)


def tex(rayas=0, mancha=0, hueco=None, logo=False, tapados=0, palido=0.0, region=0.0, marcar=0.0, faltan=None,
        relleno=None, color_fondo=(238, 236, 230)):
    """Textura del QR (RGB, TS×TS). rayas: n.º de rayones; mancha: n.º de gotas de salsa; hueco: caja de módulos rota;
    logo: logo al centro; tapados: n.º de esquinas tapadas con cinta; palido: 0–1 despintado por el sol;
    region: 0–1 pinta datos (blanco) y respaldo (cian); marcar: 0–1 resalta las 3 esquinas; faltan: lista de (x, y)
    de módulos borrados; relleno: lista de (x, y, k) módulos que vuelven a aparecer con brillo."""
    key = (rayas, mancha, hueco, logo, tapados, round(palido, 2), round(region, 2), round(marcar, 2),
           tuple(faltan) if faltan else None, tuple(relleno) if relleno else None, color_fondo)
    if key in _TX:
        return _TX[key]
    blanco = np.array(color_fondo, float)
    negro = np.array((18, 18, 22), float)
    if palido:
        negro = negro + (np.array((150, 146, 140)) - negro) * palido
        blanco = blanco + (np.array((226, 220, 205)) - blanco) * palido
    im = Image.new('RGB', (TS, TS), tuple(int(v) for v in blanco))
    d = ImageDraw.Draw(im)
    fal = set(faltan or [])
    for y in range(NQ):
        for x in range(NQ):
            if (x, y) in fal:
                continue
            col = None
            if QM[y][x]:
                col = negro
            if region > 0 and QI[y][x] >= 0:
                if QI[y][x] >= 16:
                    c2 = np.array((40, 150, 190)) if QM[y][x] else np.array((200, 240, 252))
                else:
                    c2 = np.array((10, 10, 14)) if QM[y][x] else np.array((255, 255, 255))
                col = (col if col is not None else blanco) * (1 - region) + c2 * region
            if col is not None:
                x0, y0 = (x + QZ) * PX, (y + QZ) * PX
                d.rectangle((x0, y0, x0 + PX - 1, y0 + PX - 1), fill=tuple(int(v) for v in col))
    for (x, y, k) in (relleno or []):
        x0, y0 = (x + QZ) * PX, (y + QZ) * PX
        c = tuple(int(v) for v in negro * (1 - k * 0.6) + np.array(CYAN) * k * 0.6)
        if QM[y][x]:
            d.rectangle((x0, y0, x0 + PX - 1, y0 + PX - 1), fill=c)
    if hueco:
        x0, y0, x1, y1 = hueco
        r = _rng(7)
        pts = []
        for i in range(9):
            pts.append(((x0 + (x1 - x0) * i / 8 + QZ) * PX, (y0 + QZ) * PX + r.uniform(-6, 6)))
        for i in range(9):
            pts.append(((x1 + QZ) * PX + r.uniform(-6, 6), (y0 + (y1 - y0) * i / 8 + QZ) * PX))
        for i in range(9):
            pts.append(((x1 - (x1 - x0) * i / 8 + QZ) * PX, (y1 + QZ) * PX + r.uniform(-6, 6)))
        for i in range(9):
            pts.append(((x0 + QZ) * PX + r.uniform(-6, 6), (y1 - (y1 - y0) * i / 8 + QZ) * PX))
        d.polygon(pts, fill=(6, 6, 8), outline=(200, 196, 186))
    if mancha:
        r = _rng(11)
        lay = Image.new('L', (TS, TS), 0)
        dl = ImageDraw.Draw(lay)
        for i in range(mancha):
            cx, cy = r.uniform(0.25, 0.8) * TS, r.uniform(0.3, 0.8) * TS
            rr = r.uniform(8, 17)
            dl.ellipse((cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8), fill=150)
            for j in range(5):
                a = r.uniform(0, 6.28)
                dd = rr * r.uniform(1.1, 2.0)
                q = r.uniform(2, 5)
                dl.ellipse((cx + dd * math.cos(a) - q, cy + dd * math.sin(a) - q, cx + dd * math.cos(a) + q, cy + dd * math.sin(a) + q), fill=140)
        im.paste((214, 60, 36), (0, 0), lay)
    if rayas:
        r = _rng(3)
        for i in range(rayas):
            x0, y0 = r.uniform(0.05, 0.95) * TS, r.uniform(0.05, 0.95) * TS
            a = r.uniform(-0.6, 0.6) + (0.9 if i % 2 else 0)
            L = r.uniform(0.25, 0.6) * TS
            d.line([(x0, y0), (x0 + L * math.cos(a), y0 + L * math.sin(a))], fill=(206, 204, 198), width=int(r.uniform(2, 4)))
    if logo:
        c = TS / 2
        rr = 3.6 * PX
        d.rounded_rectangle((c - rr, c - rr, c + rr, c + rr), radius=PX, fill=(8, 9, 12))
        d.ellipse((c - rr * 0.72, c - rr * 0.36, c + rr * 0.72, c + rr * 0.36), outline=(250, 250, 250), width=4)
        d.ellipse((c - 9, c - 9, c + 9, c + 9), fill=(250, 250, 250))
        d.ellipse((c + rr * 0.55 - 7, c - rr * 0.25 - 7, c + rr * 0.55 + 7, c - rr * 0.25 + 7), fill=CYAN)
    for k, (bx0, by0, bx1, by1) in enumerate(Q.buscadores()[:tapados]):
        r = _rng(20 + k)
        cx, cy = (bx0 + bx1) / 2 + QZ, (by0 + by1) / 2 + QZ
        s = 8.6 * PX / 2
        a = r.uniform(-0.18, 0.18)
        pts = [(cx * PX + s * (math.cos(a) * sx - math.sin(a) * sy), cy * PX + s * (math.sin(a) * sx + math.cos(a) * sy))
               for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        d.polygon(pts, fill=(250, 214, 70))
    if marcar > 0:
        for (bx0, by0, bx1, by1) in Q.buscadores():
            g = 0.6 * PX
            d.rectangle(((bx0 + QZ) * PX - g, (by0 + QZ) * PX - g, (bx1 + QZ) * PX + g, (by1 + QZ) * PX + g),
                        outline=tuple(int(v) for v in np.array(CYAN) * marcar + blanco * (1 - marcar)), width=6)
    if len(_TX) > 300:
        _TX.clear()
    _TX[key] = im
    return im


# daños que se muestran como «sí lee» (se prueban con `python3 qr.py probar`)
D_RAYADO = dict(rayas=9)
D_MANCHA = dict(rayas=9, mancha=4)
D_PEDAZO = dict(rayas=9, mancha=4, hueco=(17, 9, 23, 16))
D_ESQUINA = dict(hueco=(19, 19, 25, 25))
D_30 = dict(hueco=(9, 12, 18, 18))
D_LOGO = dict(logo=True)
D_DESP = dict(palido=0.55, rayas=5)
D_SALSA = dict(mancha=6)
D_TIENDA = dict(rayas=12)
D_FINAL = dict(rayas=10, mancha=2)
SI_LEE = [D_FINAL, D_RAYADO, D_MANCHA, D_PEDAZO, D_ESQUINA, D_30, D_LOGO, D_DESP, D_SALSA, D_TIENDA]
NO_LEE = [dict(tapados=3)]


def probar():
    import cv2
    det = cv2.QRCodeDetector()
    ok = True
    for dd, esperado in [(x, True) for x in SI_LEE] + [(x, False) for x in NO_LEE]:
        lee = False
        for s in (TS, 300):          # como lo ve una cámara: un poco desenfocado y con fondo alrededor
            a = np.asarray(tex(**dd).resize((s, s), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.8)))
            a = np.pad(a, ((40, 40), (40, 40), (0, 0)), constant_values=255)
            lee |= det.detectAndDecode(a)[0] == 'MENTE EN ORBITA'
        print('LEE ' if lee else 'NO  ', dd, '✓' if lee == esperado else '✗ CAMBIAR')
        ok &= lee == esperado
    print('TODO OK' if ok else 'HAY DAÑOS QUE NO CUMPLEN')


def placa(im, s=1.0, rx=0.0, ry=0.0, rz=0.0, t=(0, 0, 0), grosor=0.04, col=(232, 230, 224)):
    """QR impreso en una placa de plástico blanco, de pie (cara con el código hacia +z), centrada en t."""
    b = M3.box(1.24, 1.24, grosor, col, shadow=0, base=False, gloss=0.35)
    b = named(b, 'qr', rim=0.5, gloss=0.35)
    M3.decal(b, b.FACE['front'], im.convert('RGBA'))
    return P.tfk([b], s=s, rx=rx, ry=ry, rz=rz, t=t)


def pedazos(im, n=6, t=(0, 0, 0), s=1.0):
    """El QR partido en n×n losetas (cada una con su pedazo de textura) para la vista explotada."""
    out = []
    L = 1.24 / n
    w = TS / n
    for j in range(n):
        for i in range(n):
            b = M3.box(L * 0.995, L * 0.995, 0.04, (232, 230, 224), shadow=0, base=False, gloss=0.35)
            b = named(b, 'qr', rim=0.5, gloss=0.35)
            M3.decal(b, b.FACE['front'], im.crop((int(i * w), int(j * w), int((i + 1) * w), int((j + 1) * w))).convert('RGBA'))
            out.append(b.tf(t=(-0.62 + L * (i + 0.5), 0.62 - L * (j + 0.5), 0)))
    return P.tfk(out, s=s, t=t)


def mod_xy(mx, my, s=1.0, c=(0, 0, 0)):
    """Centro 3D de un módulo (mx, my) de una placa de escala s centrada en c (sin giro)."""
    u = 1.24 / NT
    return np.array([c[0] + s * (-0.62 + (mx + QZ + 0.5) * u), c[1] + s * (0.62 - (my + QZ + 0.5) * u), c[2] + 0.03 * s])


def pantalla_cam(qr_im=None, estado='busca', u=0.0, txt=''):
    """Pantalla del celular en modo cámara: el QR al centro, marco de escaneo y resultado."""
    def dib(d, im):
        d.rectangle((0, 70, 420, 820), fill=(22, 22, 26))
        if qr_im is not None:
            q = qr_im.resize((300, 300), Image.BILINEAR)
            im.paste(q, (60, 290))
        col = {'busca': (255, 255, 255), 'ok': VERDE, 'no': ROJO}[estado]
        for (x, y, sx, sy) in ((40, 270, 1, 1), (380, 270, -1, 1), (40, 610, 1, -1), (380, 610, -1, -1)):
            d.line([(x, y + sy * 46), (x, y), (x + sx * 46, y)], fill=col, width=7)
        if estado == 'busca':
            yy = 290 + 300 * (0.5 + 0.5 * math.sin(u * 6))
            d.line([(60, yy), (360, yy)], fill=(120, 225, 255), width=4)
        if estado == 'ok':
            d.rounded_rectangle((40, 660, 380, 760), radius=26, fill=(255, 255, 255))
            d.text((210, 710), txt or '✓ ABRIR', font=M.font('sans', 38), fill=(16, 120, 60), anchor='mm')
        if estado == 'no':
            d.rounded_rectangle((40, 660, 380, 760), radius=26, fill=(40, 12, 12))
            d.text((210, 710), txt or 'NO HAY CÓDIGO', font=M.font('sans', 32), fill=ROJO, anchor='mm')
        d.text((210, 150), 'CÁMARA', font=M.font('mono', 26), fill=(200, 200, 205), anchor='mm')
    return P.pantalla(dib)


# ================================================================== utilidades
def _paln(j):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[j]).split()


def _pal(i):
    return _paln(_ix(i))


def TT(i):
    return montaje.CTX['T'][_ix(i)][0]


def TE(i):
    return montaje.CTX['T'][_ix(i)][1]


_W = []


def _words():
    if not _W:
        import json
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
    if len(W) == sum(len(_paln(j)) for j in range(len(VOZ))):
        n0 = sum(len(_paln(j)) for j in range(_ix(i)))
        return W[n0 + k]['start'] - W[n0]['start']
    return (TE(i) - TT(i)) * k / n


def cam(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch=6, tx=0.0, ty=0.0, tz=0.0, roll=0.0):
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


def piso(fr, t, estilo='dots', a=0.8, bokeh=1.0, beam=0.0):
    space(fr, t, floor=estilo, floor_a=a, bokeh=bokeh, beam=beam)


def sombra(fr, p, rx=230, ry=50, a=0.7):
    x, y, _ = fr.cam.p1(p)
    D.shadow_blob(fr, x * S, y * S, rx * S, ry * S, a)


def check(img, fx, x, y, k, txt='SE LEE', col=VERDE):
    pill(img, fx, x, y, '✓ ' + txt, eout(k), size=36, border=col)


def tache(img, fx, x, y, k, txt='NO LO LEE'):
    pill(img, fx, x, y, '✗ ' + txt, eout(k), size=36, border=ROJO, col=(255, 200, 196))


def cel(scr, x=0.0, y=0.0, z=0.0, ry=0.0, rz=0.0, s=1.0):
    return P.tfk(P.celular(scr), s=s, t=(x, y, z)) if not (ry or rz) else P.tfk(P.celular(scr, ry=ry, rz=rz), s=s, t=(x, y, z))


# ================================================================== escenas
# 0. gancho, inicio tipo 3: los pedazos del QR vuelan, se arman con clic, y se le rompe una esquina… y sigue leyendo
def s_gancho(t, fi, u, d):
    uc = 0.45                                         # clic: se arma
    ur = wt(0, 6) + 0.1                               # «rompas»: se cae la esquina
    fr = Frame(cam(u, [K(-1.6, 4.6, -70, 22, ty=0.9), K(uc, 3.4, -8, 6, ty=0.95), K(ur, 3.0, 14, 4, ty=0.9),
                       K(3.0, 2.9, 18, 4, ty=0.9)], cy=0.56))
    piso(fr, t, 'dots', 0.9, 1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'ROTO', u, t0=-0.9, cy=0.36, entrada='golpe')
    k = 1 - P.eout4(seg(u, -1.5, uc))
    C = (0, 0.95, 0)
    sombra(fr, (0, 0.02, 0.1), 300, 60, 0.6)
    pz = pedazos(tex(), 6, t=C)
    ex = P.despiece(pz, k, centro=C, fuerza=2.2, giro=1.4)
    # la esquina de abajo a la derecha (pieza 35) sale volando al romperse (ya no es parte del código: sigue leyendo)
    kr = P.eout4(seg(u, ur, ur + 0.6))
    if kr > 0:
        ex[35] = P.tfk([ex[35]], rz=-70 * kr, t=(0.9 * kr, -0.6 * kr - 0.4 * kr * kr, 0.5 * kr))[0]
    draw_objects(fr, ex)

    def ui(img, fx):
        kicker(img, 'CÓDIGO QR · NIVEL H', 150, seg(u, uc - 0.1, uc + 0.2), col=(150, 210, 230))
        P.titulo_golpe(img, fx, [('Tu QR sirve', 'sans'), ('aunque lo rompas.', 'serif')], 200, seg(u, uc, uc + 0.15), size=84)
        if u > ur + 0.3:
            check(img, fx, 540, 1430, seg(u, ur + 0.35, ur + 0.6), 'SIGUE LEYENDO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.15, 0.35) + 0.7 * golpe_k(u, ur, 0.3), amp=22)


# 1. rayado, manchado, con un pedazo menos… y el celular lo lee
def s_danos(t, fi, u, d):
    u1, u2, u3 = wt(1, 1) - 0.1, wt(1, 4), wt(1, 9) + 0.1
    dd = D_RAYADO if u < u1 else (D_MANCHA if u < u2 else D_PEDAZO)
    fr = Frame(cam(u, [K(-0.2, 3.3, 30, 8, ty=0.95, tx=0.25), K(u1, 2.7, -18, 6, ty=1.0, tx=0.1), K(u2, 3.0, 22, 10, ty=0.95, tx=0.3),
                       K(u3, 3.4, -6, 6, ty=0.95, tx=0.45), K(5.0, 3.4, -10, 6, ty=0.95, tx=0.45)], cy=0.52))
    piso(fr, t, 'lines', 0.7, 0.9)
    im = tex(**dd)
    e = P.entrada(u, -0.2, 0.25, 'pop')
    draw_objects(fr, placa(im, s=max(0.05, e['escala']), t=(0, 1.0, 0)))
    st = 'ok' if u > u3 + 0.4 else 'busca'
    ec = P.entrada(u, u3, 0.25, 'desliza')
    if u > u3:
        draw_objects(fr, cel(pantalla_cam(im, st, u, '✓ LEÍDO'), x=0.95 + ec['dy'] * 0.4, y=0.0, z=0.9, ry=-22, s=0.85))
    pq = fr.cam.p1((0, 1.0, 0.03))
    p_r, p_m, p_h = fr.cam.p1((0.3, 1.3, 0.03)), fr.cam.p1((0.0, 0.8, 0.03)), fr.cam.p1(mod_xy(20, 12, 1, (0, 1.0, 0)))

    def ui(img, fx):
        kicker(img, 'PRUEBA CON UN QR REAL', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        lab = 'RAYADO' if u < u1 else ('MANCHADO' if u < u2 else 'UN PEDAZO MENOS')
        pill(img, fx, 540, 300, lab, 1.0, size=40, border=AMARILLO, dot=False)
        p = p_r if u < u1 else (p_m if u < u2 else p_h)
        u0 = 0.0 if u < u1 else (u1 if u < u2 else u2)
        doodle_circle(img, fx, p[0], p[1], 150, 110, t, k=eout(seg(u, u0 + 0.05, u0 + 0.4)), col=AMARILLO, w=6, seed=int(u0 * 10))
        if st == 'ok':
            check(img, fx, 540, 1430, seg(u, u3 + 0.45, u3 + 0.7), 'TU CELULAR LO LEE')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u1, 0.25) + golpe_k(u, u2, 0.25) + golpe_k(u, u3 - 0.1, 0.25), amp=14)


# 2. ¿por qué? trae su propio repuesto (el QR y su copia de respaldo en line-art cian)
def s_repuesto(t, fi, u, d):
    ur = wt(2, 2)
    fr = Frame(cam(u, [K(-0.2, 3.8, -40, 12, ty=1.0), K(0.35, 3.3, 8, 6, ty=1.0), K(ur, 3.6, 26, 8, ty=1.0, tx=0.25),
                       K(4.0, 3.6, 30, 8, ty=1.0, tx=0.25)], cy=0.55))
    piso(fr, t, 'dots', 0.8, 1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'REPUESTO', u, t0=ur - 0.15, cy=0.31, entrada='sube')
    e = P.entrada(u, -0.2, 0.3, 'gira')
    draw_objects(fr, placa(tex(), s=max(0.05, e['escala']), ry=math.degrees(e['giro']), t=(0, 1.0, 0)))
    k = P.eout4(seg(u, ur, ur + 0.45))
    C = np.array([0.0, 1.0, -0.05]) + np.array([0.75, 0.15, -0.6]) * k
    if k > 0.01:
        hw = 0.62
        cs = [C + np.array(v) for v in ((-hw, hw, 0), (hw, hw, 0), (hw, -hw, 0), (-hw, -hw, 0), (-hw, hw, 0))]
        line3(fr, cs, col=CYAN, w=3, a=k, glow=1.0)
        for (bx0, by0, bx1, by1) in Q.buscadores():
            p0 = C + np.array([-0.62 + (bx0 + QZ) * 1.24 / NT, 0.62 - (by0 + QZ) * 1.24 / NT, 0])
            p1 = C + np.array([-0.62 + (bx1 + QZ) * 1.24 / NT, 0.62 - (by1 + QZ) * 1.24 / NT, 0])
            line3(fr, [p0, (p1[0], p0[1], 0), p1, (p0[0], p1[1], 0), p0], col=CYAN, w=2, a=k, glow=0.8)
        for j in range(30):
            r = _rng(j)
            p = C + np.array([r.uniform(-0.45, 0.45), r.uniform(-0.45, 0.45), 0])
            dot3(fr, p, r=3, col=CYAN, a=k * (0.5 + 0.5 * math.sin(t * 6 + j)), glow=0.8)
    pc = fr.cam.p1(C + np.array([0, -0.75, 0]))

    def ui(img, fx):
        kicker(img, 'CORRECCIÓN DE ERRORES', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        if k > 0.5:
            pill(img, fx, pc[0], pc[1] + 40, 'RESPALDO', eout(seg(u, ur + 0.3, ur + 0.6)), size=34, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. nació en 1994 en Japón, en una fábrica de autopartes (número que golpea → banda con piezas y QR con grasa)
def s_fabrica(t, fi, u, d):
    un = wt(3, 2) - 0.15
    uf = wt(3, 9) - 0.2                    # «para aguantar…»: cambia a la fábrica
    if u < uf:
        fr = Frame(cam(u, [K(-0.2, 7.0, 0, 6, ty=1.0), K(0.2, 5.6, -10, 8, ty=1.0), K(5.0, 5.5, -12, 8, ty=1.0)]))
        piso(fr, t, None, 0, 1.0)
        N.earth(fr, t, np.array([0.0, 0.3, 0.0]), 1.35 * (1 + 0.15 * P.eout4(seg(u, un, un + 0.6))), 2.4 + 0.3 * seg(u, 0, 3))
        pj = fr.cam.p1((0.9, 0.95, 0.9))

        def ui(img, fx):
            P.numero_golpe(img, fx, '1994', 420, seg(u, un - 0.12, un), size=250, col=WHITE)
            kicker(img, 'JAPÓN · DENSO WAVE', 640, seg(u, un + 0.2, un + 0.5), col=(150, 210, 230), size=32)
            if u > un + 0.5:
                pill(img, fx, pj[0], pj[1], 'JAPÓN', eout(seg(u, un + 0.5, un + 0.8)), size=30, border=AMARILLO)
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, un, 0.35), amp=22)
    v = u - uf
    fr = Frame(cam(v, [K(-0.1, 4.6, 40, 20, ty=0.5), K(0.3, 4.0, 16, 16, ty=0.5), K(4.0, 3.9, 12, 16, ty=0.5)], cy=0.55))
    piso(fr, t, 'lines', 0.9, 0.8, beam=0.5)
    mesh = []
    banda = named(M3.box(6.0, 0.08, 1.0, (40, 42, 46), shadow=0, base=True, gloss=0.3), 'banda', rim=0.4)
    mesh.append(banda.tf(t=(0, 0.0, 0)))
    for i in range(10):
        x = -3 + ((i * 0.6 + v * 0.9) % 6.0)
        mesh.append(named(M3.cyl(0.05, 0.9, (120, 122, 128), n=12, shadow=0, gloss=0.6).tf(rx=90, t=(x, -0.05, 0.45)), 'rod'))
    for j in range(3):
        x = -1.6 + j * 1.3 + v * 0.9 - 0.4
        pieza = named(M3.rbox(0.62, 0.36, 0.5, 0.06, (150, 152, 160), n=3, shadow=0, gloss=0.8), 'pieza', rim=0.7, gloss=0.8)
        mesh.append(pieza.tf(t=(x, 0.08, 0)))
        mesh += placa(tex(mancha=2 + j, rayas=3, color_fondo=(236, 234, 228)), s=0.26, rx=-12, t=(x, 0.3, 0.26))
    draw_objects(fr, mesh)
    pc = fr.cam.p1((0.0, 0.7, 0.3))

    def ui(img, fx):
        kicker(img, 'FÁBRICA DE AUTOPARTES · RECREACIÓN', 150, seg(v, 0.0, 0.3), col=(150, 152, 160))
        M.title(img, fx, [('Hecho para', 'sans'), ('la mugre.', 'serif')], 230, seg(v, 0.15, 0.5), size=82)
        doodle_arrow(img, fx, pc[0] - 220, pc[1] + 260, pc[0] - 40, pc[1] + 40, t, k=eout(seg(v, 0.5, 0.9)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. guarda tu información… y un respaldo (datos en blanco, respaldo en cian) + gráfico 16 contra 28
def s_respaldo(t, fi, u, d):
    ur = wt(4, 3)
    ug = wt(4, 6) - 0.1
    fr = Frame(cam(u, [K(-0.2, 3.0, 0, 4, ty=1.05), K(0.3, 2.6, -22, 6, ty=1.05), K(ug, 3.3, 12, 6, ty=1.0, tx=-0.35),
                       K(5.0, 3.3, 14, 6, ty=1.0, tx=-0.35)], cy=0.5))
    piso(fr, t, 'dots', 0.6, 0.8)
    draw_objects(fr, placa(tex(region=round(ease(seg(u, ur - 0.2, ur + 0.3)), 2)), t=(0, 1.0, 0)))

    def ui(img, fx):
        kicker(img, 'ESTE QR · VERSIÓN 2 · NIVEL H', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if u < ug:
            pill(img, fx, 330, 300, 'TU INFORMACIÓN', eout(seg(u, 0.15, 0.4)), size=32, border=WHITE)
            pill(img, fx, 760, 300, 'RESPALDO', eout(seg(u, ur, ur + 0.3)), size=32, border=CYAN)
        else:
            chart_grow(img, fx, (560, 300, 1030, 1180), [16, 28], ['DATOS', 'RESPALDO'], t - u + ug, t, unit='',
                       title_txt='BLOQUES', vmax=32, line=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. con el nivel H aguanta que le falte cerca del 30 % (escalera L-M-Q-H, mordida que se come el código, número)
def s_30(t, fi, u, d):
    un = wt(5, 9) - 0.2
    fr = Frame(cam(u, [K(-0.2, 3.6, 34, 10, ty=1.0, tx=0.4), K(0.25, 3.1, 8, 6, ty=1.0, tx=0.4), K(un, 3.5, -16, 6, ty=1.0, tx=0.2),
                       K(5.0, 3.5, -18, 6, ty=1.0, tx=0.2)], cy=0.55))
    piso(fr, t, 'lines', 0.7, 1.0)
    kb = seg(u, un - 0.9, un)
    hueco = None
    if kb > 0:
        x1 = int(round(9 + 9 * ease(kb)))
        hueco = (9, 12, max(10, x1), 18)
    draw_objects(fr, placa(tex(hueco=hueco), t=(0.4, 1.0, 0)))
    niveles = [('L', '7 %'), ('M', '15 %'), ('Q', '25 %'), ('H', '30 %')]

    def ui(img, fx):
        kicker(img, 'NIVELES DE CORRECCIÓN', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        for i, (n, p) in enumerate(niveles):
            k = seg(u, 0.1 + 0.18 * i, 0.3 + 0.18 * i)
            col = AMARILLO if n == 'H' else (190, 192, 200)
            pill(img, fx, 150, 470 + i * 120, f'{n} · {p}', eout(k), size=34, border=col, dot=False)
        P.numero_golpe(img, fx, '30 %', 300, seg(u, un - 0.12, un), size=220, col=AMARILLO)
        if u > un + 0.4:
            check(img, fx, 600, 1430, seg(u, un + 0.4, un + 0.65), 'Y SIGUE LEYENDO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un, 0.35), amp=22)


# 6. hasta le ponen un logo en medio (el logo cae, rebota, y el celular lo lee)
def s_logo(t, fi, u, d):
    ul = wt(6, 4) - 0.25
    fr = Frame(cam(u, [K(-0.2, 3.9, -30, 18, ty=0.9), K(0.3, 3.4, -6, 10, ty=0.9), K(ul + 0.2, 3.0, 10, 6, ty=0.95),
                       K(4.0, 3.0, 12, 6, ty=0.95)], cy=0.55))
    piso(fr, t, 'dots', 0.8, 1.0, beam=0.5)
    puesto = u > ul + 0.3
    draw_objects(fr, placa(tex(**(D_LOGO if puesto else {})), t=(0, 1.0, 0)))
    if not puesto:
        e = P.entrada(u, ul, 0.3, 'cae')
        lg = named(M3.rbox(0.36, 0.36, 0.05, 0.05, (10, 11, 14), n=3, shadow=0, gloss=0.6, base=False), 'logo', rim=0.8)
        if u > ul:
            draw_objects(fr, P.tfk([lg], rx=90, t=(0, 1.0 - e['dy'] * 0.4, 0.06)))
    if u > ul + 0.5:
        draw_objects(fr, cel(pantalla_cam(tex(**D_LOGO), 'ok' if u > ul + 0.9 else 'busca', u, '✓ ABRIR'), x=-0.95, z=0.8, ry=24, s=0.8))
    pc = fr.cam.p1((0, 1.0, 0.03))

    def ui(img, fx):
        kicker(img, 'UN LOGO ENCIMA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        doodle_circle(img, fx, pc[0], pc[1], 120, 120, t, k=eout(seg(u, ul + 0.35, ul + 0.7)), col=AMARILLO, w=6)
        if u > ul + 0.9:
            check(img, fx, 540, 1430, seg(u, ul + 0.95, ul + 1.2), 'FUNCIONA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ul + 0.3, 0.35), amp=18)


# 7. mándaselo a quien tiene el QR de su negocio todo despintado (puerta de local en line-art + QR pálido)
def s_desp(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 5.0, 40, 10, ty=1.3), K(0.3, 4.2, 12, 6, ty=1.3), K(3.0, 4.0, 8, 6, ty=1.3)], cy=0.56))
    piso(fr, t, 'lines', 0.6, 0.9, beam=0.6)
    for x in (-1.2, 1.2):
        line3(fr, [(x, 0, -0.2), (x, 2.8, -0.2)], col=WHITE, w=3, a=0.8, glow=0.6)
    line3(fr, [(-1.2, 2.8, -0.2), (1.2, 2.8, -0.2)], col=WHITE, w=3, a=0.8, glow=0.6)
    line3(fr, [(-1.6, 3.2, -0.25), (1.6, 3.2, -0.25)], col=AMARILLO, w=4, a=0.9, glow=1.0)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    draw_objects(fr, placa(tex(**D_DESP), s=0.85, t=(0, 1.45 - e['dy'] * 0.3, 0)))
    if u > 0.8:
        draw_objects(fr, cel(pantalla_cam(tex(**D_DESP), 'ok' if u > 1.4 else 'busca', u, '✓ PAGAR'), x=0.9, y=-0.1, z=1.0, ry=-20, s=0.8))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien tiene', 'sans'), ('su QR todo despintado.', 'serif')], 170, seg(u, 0.0, 0.35), size=62)
        kicker(img, 'ABIERTO', 545, seg(u, 0.2, 0.5), col=AMARILLO, size=30)
        if u > 1.4:
            check(img, fx, 540, 1430, seg(u, 1.45, 1.7), 'HASTA ASÍ LEE')
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. segundo gancho: pero hay tres cuadros que nunca debes tapar (las 3 esquinas se encienden una por una)
def s_tres(t, fi, u, d):
    u3 = wt(8, 3)
    ue = wt(8, 9)
    fr = Frame(cam(u, [K(-0.2, 2.6, 0, 4, ty=1.0, roll=-8), K(0.25, 3.2, -10, 6, ty=1.0), K(ue, 2.9, 12, 4, ty=1.0),
                       K(5.0, 2.9, 14, 4, ty=1.0)], cy=0.53))
    piso(fr, t, 'dots', 0.6, 1.0)
    M.cristal(fr.base, fr.fx, 'ESQUINAS', u, t0=ue - 0.2, cy=0.24, entrada='zoom')
    mk = round(ease(seg(u, u3 - 0.1, u3 + 0.3)), 2)
    draw_objects(fr, placa(tex(marcar=mk), t=(0, 1.0, 0)))
    cs = []
    for (bx0, by0, bx1, by1) in Q.buscadores():
        p = mod_xy((bx0 + bx1) / 2 - 0.5, (by0 + by1) / 2 - 0.5, 1, (0, 1.0, 0))
        cs.append(fr.cam.p1(p))

    def ui(img, fx):
        kicker(img, '¡OJO!', 150, seg(u, 0.0, 0.2), col=ROJO, size=34)
        P.titulo_golpe(img, fx, [('Nunca tapes', 'sans'), ('estos tres.', 'serif')], 1300, seg(u, ue, ue + 0.15), size=76)
        for i, c in enumerate(cs):
            k = seg(u, u3 + 0.25 * i, u3 + 0.25 * i + 0.3)
            doodle_circle(img, fx, c[0], c[1], 95, 95, t, k=eout(k), col=CYAN, w=6, seed=i)
            if k > 0.5:
                ImageDraw.Draw(img).text((c[0], c[1]), str(i + 1), font=M.font('sansx', 64), fill=AMARILLO, anchor='mm')
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, ue + 0.15, 0.35) + golpe_k(u, 0.0, 0.3), amp=22)


# 9. le dicen a tu cámara dónde está y hacia dónde está girado (zoom digital con REC y el triángulo de las 3 esquinas)
def s_gira(t, fi, u, d):
    ug = wt(9, 9)
    rz = -150 * P.eout4(seg(u, ug - 0.3, ug + 0.6)) + 20 * math.sin(t * 1.3)
    fr = Frame(Cam(target=(0, 1.0, 0), dist=3.1, yaw=0, pitch=2, cy=0.5))
    piso(fr, t, None, 0, 0.8)
    pl = placa(tex(marcar=1.0), rz=rz, t=(0, 1.0, 0))
    draw_objects(fr, pl)
    a = math.radians(rz)
    cs = []
    for (bx0, by0, bx1, by1) in Q.buscadores():
        p = mod_xy((bx0 + bx1) / 2 - 0.5, (by0 + by1) / 2 - 0.5, 1, (0, 0, 0))
        x, y = p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a)
        cs.append(fr.cam.p1((x, 1.0 + y, 0.05)))
    z = 1.0 if u < 0.9 else (1.3 if u < ug - 0.3 else 1.55)

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        k = eout(seg(u, 0.2, 0.6))
        if k > 0:
            for (pa, pb) in ((cs[0], cs[1]), (cs[0], cs[2])):
                xb, yb = pa[0] + (pb[0] - pa[0]) * k, pa[1] + (pb[1] - pa[1]) * k
                dd.line([(pa[0], pa[1]), (xb, yb)], fill=AMARILLO, width=6)
                ImageDraw.Draw(fx).line([(pa[0], pa[1]), (xb, yb)], fill=(120, 110, 60), width=14)
        for c in cs:
            dd.ellipse((c[0] - 12, c[1] - 12, c[0] + 12, c[1] + 12), fill=CYAN)
        pill(img, fx, 540, 290, 'AQUÍ ESTÁ · ASÍ ESTÁ GIRADO', eout(seg(u, 0.6, 0.9)), size=30, border=CYAN, dot=False)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if z > 1.01:
        out = M.scale_about(out, z, 0.5, 0.5)
    im = Image.fromarray(out)
    rec_frame(im, t, 1.0, zoom_label=f'x{z:.1f}')
    return np.asarray(im)


# 10. si los tapas, ya no lo encuentra (cintas que se pegan una por una y el celular busca… y nada)
def s_tapas(t, fi, u, d):
    ut = [0.05, 0.3, 0.55]
    n = sum(1 for x in ut if u > x)
    un = wt(10, 9) - 0.2
    fr = Frame(cam(u, [K(-0.2, 3.5, 30, 8, ty=1.0, tx=0.3), K(0.25, 3.2, 6, 6, ty=1.0, tx=0.3), K(un, 3.6, -14, 6, ty=1.0, tx=0.5),
                       K(5.0, 3.6, -16, 6, ty=1.0, tx=0.5)], cy=0.52))
    piso(fr, t, 'lines', 0.7, 1.0)
    im = tex(tapados=n)
    draw_objects(fr, placa(im, t=(0, 1.0, 0)))
    if u > 1.0:
        e = P.entrada(u, 1.0, 0.25, 'desliza')
        draw_objects(fr, cel(pantalla_cam(im, 'no' if u > un else 'busca', u), x=1.0 + e['dy'] * 0.3, z=0.9, ry=-22, s=0.85))

    def ui(img, fx):
        kicker(img, 'CINTA EN LAS ESQUINAS', 150, seg(u, 0.0, 0.3), col=(255, 140, 120))
        if u > un:
            tache(img, fx, 540, 1430, seg(u, un, un + 0.25), 'NO LO ENCUENTRA')
    fr.ui.append(ui)
    k = sum(golpe_k(u, x, 0.2) for x in ut) + golpe_k(u, un, 0.3)
    return sacudir(finish(fr, fi), t, k, amp=16)


# 11. por dentro, cada cuadrito es un uno o un cero (macro de módulos en 3D con sus dígitos)
def s_bits(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 1.6, -30, 30, ty=0.0), K(0.3, 2.3, -8, 40, ty=0.0), K(4.0, 2.4, -2, 42, ty=0.0)], cy=0.5))
    piso(fr, t, None, 0, 0.9)
    mesh = []
    x0, y0 = 9, 9
    for j in range(7):
        for i in range(7):
            v = QM[y0 + j][x0 + i]
            e = P.entrada(u, 0.05 * (i + j) * 0.5, 0.2, 'pop')
            h = (0.18 if v else 0.04) * max(0.05, e['escala'])
            col = (24, 24, 28) if v else (238, 236, 230)
            b = named(M3.box(0.2, h, 0.2, col, shadow=0, base=True, gloss=0.4), 'm', rim=0.5)
            mesh.append(b.tf(t=((i - 3) * 0.21, 0, (j - 3) * 0.21)))
    draw_objects(fr, mesh)
    pts = [(fr.cam.p1(((i - 3) * 0.21, 0.25, (j - 3) * 0.21)), QM[y0 + j][x0 + i]) for j in range(7) for i in range(7)]

    def ui(img, fx):
        kicker(img, '1 = OSCURO · 0 = CLARO', 150, seg(u, 0.2, 0.5), col=(150, 210, 230))
        dd = ImageDraw.Draw(img)
        f = M.font('mono', 40)
        for n, ((x, y, _), v) in enumerate(pts):
            k = seg(u, 0.3 + 0.012 * n, 0.5 + 0.012 * n)
            if k > 0:
                dd.text((x, y), str(v), font=f, fill=M.scale_c(CYAN if v else WHITE, k), anchor='mm')
    fr.ui.append(ui)
    return finish(fr, fi)


# 12. se juntan en bloques de ocho, como letras (8 cuadritos se deslizan y forman la «M»)
BYTE = '01001101'


def s_byte(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.4, 30, 14, ty=0.4), K(0.3, 3.0, 0, 10, ty=0.4), K(3.0, 2.9, -6, 10, ty=0.4)], cy=0.5))
    piso(fr, t, 'dots', 0.8, 1.0, beam=0.4)
    mesh = []
    for i, b in enumerate(BYTE):
        e = P.entrada(u, 0.05 * i, 0.22, 'desliza')
        col = (24, 24, 28) if b == '1' else (238, 236, 230)
        m = named(M3.box(0.24, 0.24, 0.24, col, shadow=0, base=True, gloss=0.4), 'm', rim=0.6)
        mesh.append(m.tf(t=((i - 3.5) * 0.27 + e['dy'] * 0.6, 0.3, 0)))
    draw_objects(fr, mesh)
    pp = [fr.cam.p1(((i - 3.5) * 0.27, 0.75, 0.0)) for i in range(8)]
    um = 1.0

    def ui(img, fx):
        kicker(img, '8 CUADRITOS = 1 BLOQUE · EJEMPLO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        dd = ImageDraw.Draw(img)
        for i, p in enumerate(pp):
            if u > 0.05 * i + 0.15:
                dd.text((p[0], p[1]), BYTE[i], font=M.font('mono', 54), fill=CYAN if BYTE[i] == '1' else WHITE, anchor='mm')
        if u > um:
            P.numero_golpe(img, fx, 'M', 480, seg(u, um, um + 0.15), size=300, col=AMARILLO)
            pill(img, fx, 540, 1430, 'LETRA «M»', eout(seg(u, um + 0.2, um + 0.45)), size=34, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.15, 0.3), amp=18)


# 13. el respaldo usa la misma matemática que los CD y las naves espaciales (CD que gira → sonda de alambre)
def s_cd(t, fi, u, d):
    un = wt(13, 10) - 0.1                      # «y las naves espaciales»
    if u < un:
        fr = Frame(cam(u, [K(-0.2, 3.0, 20, 40, ty=0.3), K(0.3, 2.7, -10, 32, ty=0.3), K(5.0, 2.6, -14, 30, ty=0.3)], cy=0.55))
        piso(fr, t, None, 0, 1.0, beam=0.5)
        e = P.entrada(u, -0.2, 0.3, 'gira')
        disco = named(M3.cyl(0.95, 0.02, (200, 204, 212), n=48, shadow=0, gloss=0.95), 'cd', rim=0.9, gloss=0.95)
        hoyo = named(M3.cyl(0.15, 0.024, (8, 8, 10), n=24, shadow=0, gloss=0.2), 'hoyo')
        ry = math.degrees(t * 3.0) + math.degrees(e['giro'])
        draw_objects(fr, P.tfk([disco, hoyo], s=max(0.05, e['escala']), rx=-12, ry=ry, t=(0, 0.3, 0)))
        for j in range(5):
            r = 0.4 + j * 0.11
            th = np.linspace(0, 2 * math.pi, 60)
            col = [(255, 120, 180), (255, 220, 120), (120, 255, 200), (120, 200, 255), (200, 140, 255)][j]
            line3(fr, [(r * math.cos(a), 0.33, r * math.sin(a)) for a in th], col=col, w=1.2, a=0.35, glow=0.6)

        def ui(img, fx):
            kicker(img, 'REED-SOLOMON · 1960', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
            M.title(img, fx, [('La misma matemática', 'sans'), ('que tus discos.', 'serif')], 230, seg(u, 0.25, 0.6), size=70)
        fr.ui.append(ui)
        return finish(fr, fi)
    v = u - un
    fr = Frame(cam(v, [K(-0.1, 6.0, -50, 14, ty=1.0), K(0.3, 4.6, -18, 10, ty=1.0), K(4.0, 4.4, -12, 10, ty=1.0)], cy=0.5))
    piso(fr, t, None, 0, 1.3)
    C = np.array([0.0, 1.0, 0.0])
    th = np.linspace(0, 2 * math.pi, 40)
    for r, yy in ((0.9, 0.0), (0.6, 0.18), (0.3, 0.3)):
        line3(fr, [C + np.array([r * math.cos(a), yy, r * math.sin(a)]) for a in th], col=WHITE, w=2.4, a=0.9, glow=0.7)
    for a in np.linspace(0, 2 * math.pi, 8, endpoint=False):
        line3(fr, [C + np.array([0.9 * math.cos(a), 0, 0.9 * math.sin(a)]), C + np.array([0, 0.62, 0])], col=WHITE, w=1.6, a=0.7, glow=0.5)
    line3(fr, [C + np.array([0, -0.05, 0]), C + np.array([0, -0.6, 0])], col=WHITE, w=3, a=0.9, glow=0.6)
    bx = [C + np.array(p) for p in ((-0.3, -0.6, -0.3), (0.3, -0.6, -0.3), (0.3, -0.6, 0.3), (-0.3, -0.6, 0.3), (-0.3, -0.6, -0.3))]
    line3(fr, bx, col=WHITE, w=2.4, a=0.9, glow=0.6)
    line3(fr, [C + np.array([0.3, -0.6, 0]), C + np.array([2.2, -0.9, 0])], col=WHITE, w=1.6, a=0.7, glow=0.4)
    for j in range(6):
        p = C + np.array([0, 0.62, 0]) + np.array([-0.4 - j * 0.45, 0.25 + j * 0.2, 0.3]) * ((v * 1.4 + j / 6) % 1.0) * 2
        dot3(fr, p, r=5, col=CYAN, a=0.9, glow=1.0)

    def ui(img, fx):
        kicker(img, 'SONDAS COMO LA VOYAGER · RECREACIÓN', 150, seg(v, 0.0, 0.3), col=(150, 210, 230))
        M.title(img, fx, [('Y la de las', 'sans'), ('naves espaciales.', 'serif')], 230, seg(v, 0.1, 0.45), size=70)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.0, 0.3), amp=14)


# 14. si falta un pedazo, tu celular resuelve la ecuación y lo rellena (el hueco se llena módulo por módulo)
HUECO = [(x, y) for y in range(10, 16) for x in range(10, 16) if not QF[y][x]]


def s_rellena(t, fi, u, d):
    ur = wt(14, 6) - 0.1
    k = seg(u, ur, ur + 1.2)
    n = int(len(HUECO) * k)
    falt = HUECO[n:]
    rel = tuple((x, y, round(max(0.0, 1 - (k * len(HUECO) - i) / 6), 1)) for i, (x, y) in enumerate(HUECO[:n]))
    fr = Frame(cam(u, [K(-0.2, 2.4, -20, 6, ty=1.0), K(0.3, 2.9, 4, 4, ty=1.0), K(ur, 2.5, 14, 4, ty=1.0), K(5.0, 2.45, 16, 4, ty=1.0)], cy=0.5))
    piso(fr, t, None, 0, 0.9)
    draw_objects(fr, placa(tex(faltan=falt, relleno=rel), t=(0, 1.0, 0)))
    pc = fr.cam.p1(mod_xy(12.5, 12.5, 1, (0, 1.0, 0)))

    def ui(img, fx):
        kicker(img, 'TU CELULAR HACE LA CUENTA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        f = M.font('mono', 40)
        dd = ImageDraw.Draw(img)
        for j, s in enumerate(['x⁴ + 3x² + 1', 'α¹⁴ · α²⁸', '= ?']):
            kk = seg(u, 0.3 + 0.2 * j, 0.5 + 0.2 * j) * (1 - seg(u, ur + 1.0, ur + 1.3))
            if kk > 0:
                dd.text((540 + (j - 1) * 120, 330 + j * 70), s, font=f, fill=M.scale_c(CYAN, kk), anchor='mm')
        doodle_circle(img, fx, pc[0], pc[1], 150, 150, t, k=eout(seg(u, 0.1, 0.45)) * (1 - seg(u, ur + 0.8, ur + 1.0)), col=AMARILLO, w=6)
        if k >= 1:
            check(img, fx, 540, 1430, seg(u, ur + 1.25, ur + 1.5), 'RELLENADO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ur + 1.2, 0.3), amp=14)


# 15. el QR de la taquería con todo y salsa (mesa de madera, botella de salsa y el QR salpicado)
def s_taqueria(t, fi, u, d):
    us = wt(15, 10) - 0.2
    fr = Frame(cam(u, [K(-0.2, 4.4, 50, 26, ty=0.6), K(0.3, 3.6, 18, 16, ty=0.6), K(us, 3.2, -10, 12, ty=0.7), K(5.0, 3.15, -12, 12, ty=0.7)], cy=0.55))
    piso(fr, t, None, 0, 0.8, beam=0.6)
    mesa = named(M3.box(3.4, 0.12, 2.0, (122, 80, 46), shadow=0, base=True, gloss=0.25), 'mesa', rim=0.4)
    mesh = [mesa.tf(t=(0, -0.12, 0))]
    bot = named(M3.cyl(0.13, 0.62, (196, 30, 22), n=20, shadow=0, gloss=0.7), 'salsa', rim=0.6)
    tapa = named(M3.cyl(0.07, 0.16, (240, 240, 236), n=16, shadow=0, gloss=0.5), 'tapa')
    e = P.entrada(u, 0.1, 0.25, 'cae')
    mesh += P.tfk([bot, tapa.tf(t=(0, 0.62, 0))], t=(-0.95, -e['dy'] * 0.3, 0.2))
    base = named(M3.box(0.7, 0.08, 0.35, (220, 222, 226), shadow=0, base=True, gloss=0.8), 'base', rim=0.8)
    mesh.append(base)
    im = tex(**(D_SALSA if u > us else {}))
    mesh += placa(im, s=0.62, rx=-8, t=(0, 0.45, 0))
    draw_objects(fr, mesh)

    def ui(img, fx):
        kicker(img, 'TAQUERÍA · EJEMPLO', 150, seg(u, 0.0, 0.3), col=AMARILLO)
        M.title(img, fx, [('Con todo', 'sans'), ('y salsa.', 'serif')], 240, seg(u, us, us + 0.3), size=88, col=(255, 200, 190))
        if u > us + 0.5:
            check(img, fx, 540, 1430, seg(u, us + 0.5, us + 0.75), 'EL MENÚ ABRE')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us, 0.3), amp=16)


# 16. y el de la tiendita, aunque esté todo rayado (mostrador, QR muy rayado y el pago listo)
def s_tienda(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.0, -40, 16, ty=0.9), K(0.25, 2.8, -12, 10, ty=0.95), K(3.0, 2.7, -8, 10, ty=0.95)], cy=0.52))
    piso(fr, t, 'lines', 0.6, 1.0)
    mesh = [named(M3.box(3.0, 0.9, 0.9, (60, 64, 72), shadow=0, base=True, gloss=0.4), 'mostrador', rim=0.5).tf(t=(0, -0.6, -0.3))]
    im = tex(**D_TIENDA)
    mesh += placa(im, s=0.72, t=(0, 0.75, 0.2))
    draw_objects(fr, mesh)
    if u > 0.6:
        e = P.entrada(u, 0.6, 0.25, 'desliza')
        draw_objects(fr, cel(pantalla_cam(im, 'ok' if u > 1.1 else 'busca', u, '✓ PAGO LISTO'), x=0.85 + e['dy'] * 0.3, y=-0.2, z=0.9, ry=-18, s=0.75))

    def ui(img, fx):
        kicker(img, 'TIENDITA · EJEMPLO', 150, seg(u, 0.0, 0.3), col=AMARILLO)
        if u > 1.1:
            check(img, fx, 540, 1430, seg(u, 1.15, 1.4), 'PAGADO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. mándaselo a alguien que cree que un QR rayado ya no sirve (el QR se agrieta y aun así lee)
def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.8, 50, 10, ty=1.0), K(0.3, 3.4, 16, 6, ty=1.0), K(4.0, 3.3, 10, 6, ty=1.0)], cy=0.58))
    piso(fr, t, 'dots', 0.9, 1.0, beam=0.55)
    sombra(fr, (0, 0.02, 0.1), 260, 50, 0.6)
    draw_objects(fr, placa(tex(**D_FINAL), t=(0, 1.0, 0)))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien cree que', 'sans'), ('un QR rayado ya no sirve.', 'serif')], 170, seg(u, 0.0, 0.35), size=60)
        check(img, fx, 540, 1430, seg(u, 0.8, 1.05), 'SÍ SIRVE')
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[]),
           dict(desde=1, fn=s_danos, tr='rompe', c=(0.6, 0.5), sfx=[]),
           dict(desde=2, fn=s_repuesto, tr='iris', c=(0.5, 0.5), sfx=[]),
           dict(desde=3, fn=s_fabrica, tr='cubo', sfx=[]),
           dict(desde=4, fn=s_respaldo, tr='mosaico', sfx=[]),
           dict(desde=5, fn=s_30, tr='golpe', sfx=[]),
           dict(desde=6, fn=s_logo, tr='deslizar', sfx=[]),
           dict(desde=7, fn=s_desp, tr='whip_izq', sfx=[]),
           dict(desde=8, fn=s_tres, tr='glitch', sfx=[]),
           dict(desde=9, fn=s_gira, tr='zoom', c=(0.3, 0.33), sfx=[]),
           dict(desde=10, fn=s_tapas, tr='rebanadas', sfx=[]),
           dict(desde=11, fn=s_bits, tr='cristal', palabra='CUADRITO', sfx=[]),
           dict(desde=12, fn=s_byte, tr='deslizar_abajo', sfx=[]),
           dict(desde=13, fn=s_cd, tr='giro', sfx=[]),
           dict(desde=14, fn=s_rellena, tr='remolino', sfx=[]),
           dict(desde=15, fn=s_taqueria, tr='whip', sfx=[]),
           dict(desde=16, fn=s_tienda, tr='push', c=(0.5, 0.45), sfx=[]),
           dict(desde=17, fn=s_mandalo, tr='ritmo', sfx=[]),
           dict(desde=18, loop=True, tr='flash')]

ESCENAS = [dict(e, desde=_ix(e['desde']), _o=e['desde']) for e in ESCENAS if e['desde'] != CUT]


class _PorViejo(dict):
    def __missing__(self, k):
        return {}


def _sfx_dinamicos():
    E = _PorViejo({e['_o']: e for e in ESCENAS})
    uc, ur = 0.45, wt(0, 6) + 0.1
    E[0]['sfx'] = [(-0.6, 'whoosh', 0.6), (uc - 0.05, 'click', 1.0), (uc + 0.15, 'bass', 1.0), (ur, 'vidrio', 0.7), (ur + 0.35, 'chime_c', 0.6)]
    u1, u2, u3 = wt(1, 1) - 0.1, wt(1, 4), wt(1, 9) + 0.1
    E[1]['sfx'] = [(0.0, 'scribble', 0.5), (u1, 'slap', 0.7), (u1 + 0.05, 'scribble', 0.5), (u2, 'thud', 0.8), (u2 + 0.05, 'scribble', 0.5),
                   (u3, 'whoosh', 0.5), (u3 + 0.45, 'chime_b', 0.7)]
    ur2 = wt(2, 2)
    E[2]['sfx'] = [(-0.2, 'whoosh', 0.5), (ur2, 'shimmer', 0.6), (ur2 + 0.3, 'tick', 0.6)]
    un, uf = wt(3, 2) - 0.15, wt(3, 9) - 0.2
    E[3]['sfx'] = [(un - 0.1, 'whoosh', 0.5), (un, 'bass', 1.0), (un + 0.5, 'tick', 0.6), (uf, 'whoosh_suave', 0.7), (uf + 0.5, 'scribble', 0.5)]
    ur4, ug = wt(4, 3), wt(4, 6) - 0.1
    E[4]['sfx'] = [(0.15, 'tick', 0.5), (ur4 - 0.2, 'digital', 0.6), (ur4, 'tick2', 0.6), (ug, 'whoosh', 0.4), (ug + 0.25, 'chime_a', 0.6), (ug + 0.53, 'chime_c', 0.7)]
    un5 = wt(5, 9) - 0.2
    E[5]['sfx'] = [(0.1 + 0.18 * i, 'tick', 0.5) for i in range(4)] + [(un5 - 0.9, 'digital', 0.4), (un5, 'bass', 1.0), (un5 + 0.4, 'chime_b', 0.6)]
    ul = wt(6, 4) - 0.25
    E[6]['sfx'] = [(ul, 'whoosh', 0.5), (ul + 0.3, 'thud', 1.0), (ul + 0.35, 'scribble', 0.5), (ul + 0.9, 'chime_c', 0.7)]
    E[7]['sfx'] = [(-0.2, 'thud', 0.7), (0.0, 'shimmer', 0.4), (1.4, 'chime_b', 0.6)]
    u38, ue = wt(8, 3), wt(8, 9)
    E[8]['sfx'] = [(0.0, 'sub', 0.8)] + [(u38 + 0.25 * i, 'tick2', 0.7) for i in range(3)] + [(ue, 'whoosh', 0.4), (ue + 0.15, 'bass', 1.0)]
    ug9 = wt(9, 9)
    E[9]['sfx'] = [(0.2, 'scribble', 0.4), (0.9, 'click', 0.8), (ug9 - 0.3, 'whoosh', 0.7), (ug9 - 0.3, 'click', 0.8)]
    un10 = wt(10, 9) - 0.2
    E[10]['sfx'] = [(x, 'slap', 0.9) for x in (0.05, 0.3, 0.55)] + [(1.0, 'whoosh', 0.4), (un10, 'burst', 0.5), (un10 + 0.05, 'sub', 0.8)]
    E[11]['sfx'] = [(0.05 + 0.05 * i, 'tick2', 0.25) for i in range(8)] + [(0.3 + 0.1 * i, 'tick', 0.2) for i in range(10)]
    E[12]['sfx'] = [(0.05 * i + 0.1, 'tick', 0.4) for i in range(8)] + [(1.0, 'whoosh', 0.4), (1.15, 'bass', 1.0)]
    un13 = wt(13, 10) - 0.1
    E[13]['sfx'] = [(-0.2, 'whoosh_suave', 0.6), (0.25, 'shimmer', 0.4), (un13, 'whoosh', 0.7), (un13 + 0.1, 'sub', 0.7)]
    ur14 = wt(14, 6) - 0.1
    E[14]['sfx'] = [(0.1, 'scribble', 0.5)] + [(0.3 + 0.2 * j, 'tick2', 0.5) for j in range(3)] + \
                   [(ur14 + 0.1 * i, 'tick', 0.3) for i in range(12)] + [(ur14 + 1.2, 'chime_c', 0.7), (ur14 + 1.25, 'bass', 0.6)]
    us = wt(15, 10) - 0.2
    E[15]['sfx'] = [(0.1, 'thud', 0.6), (us, 'slap', 1.0), (us + 0.05, 'burst', 0.3), (us + 0.5, 'chime_b', 0.6)]
    E[16]['sfx'] = [(0.0, 'scribble', 0.5), (0.6, 'whoosh', 0.4), (1.1, 'chime_c', 0.7)]
    E[17]['sfx'] = [(0.0, 'shimmer', 0.5), (0.8, 'chime_b', 0.6)]


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'probar':
        probar()
        raise SystemExit
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
