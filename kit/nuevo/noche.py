"""Reel diario: «Tu foto de noche no es una foto.» Sáb 7-nov-2026, 8:00. Voz Isaac. Estilo rápido (ESTILO.md §11-12).
Inicio tipo 12 (cuenta regresiva 3-2-1 del modo noche que se congela en la foto). Primera transición: giro.
Datos: Night Sight de Google junta hasta 15 cuadros de 1/15 s (o menos) en mano, o 6 de 1 s en tripié; alinea y promedia
para bajar el ruido; mide el movimiento y descarta los pedazos que no puede alinear (Google Research, 14-nov-2018).
Ruido ~1/√n: con 15 fotos baja ~3.9 veces (estadística). Foto real: Monterrey de noche desde la ISS (NASA, ISS-35, dominio público).
Ruido de las fotos, tripié, perro y pared: RECREACIÓN."""
import math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'noche'
TXT = ['Toma una foto de noche…',
       'y no te muevas.',
       'Porque tu foto de noche no es una foto.',
       'Son muchas.',
       'El modo noche de Google, por ejemplo, junta hasta 15 fotos…',
       'en cuanto aprietas el botón.',
       'Cada una sale oscura y llena de puntitos.',
       'Eso es ruido.',
       'Cada píxel del sensor cuenta partículas de luz…',
       'y de noche le llegan tan poquitas que se equivoca.',
       'Pero se equivoca al azar: en cada foto, en otro lugar.',
       'Tu celular alinea las 15 y saca el promedio.',
       'La luz se suma… y el ruido se cancela.',
       'Con 15 fotos, el ruido baja casi 4 veces.',
       'Y aquí está el error que todos cometemos:',
       'si tú o tu perro se mueven, las fotos ya no encajan.',
       'El celular tira los pedazos que no puede alinear…',
       'y te deja algo borroso, o con fantasmas.',
       'En un tripié, en cambio, aguanta 6 fotos de 1 segundo cada una.',
       'Truco: recárgate en una pared…',
       'y no te muevas hasta que termine el contador.',
       'Mándaselo a quien siempre sale borroso en las fotos de la fiesta.',
       'Y la próxima vez que salgas de noche…']
VOZ = list(TXT)
VOZ[0] = '[curious] Toma una foto de noche…'
VOZ[4] = 'El modo noche de Google, por ejemplo, junta hasta quince fotos…'
VOZ[11] = 'Tu celular alinea las quince y saca el promedio.'
VOZ[13] = 'Con quince fotos, el ruido baja casi cuatro veces.'
VOZ[14] = '[excited] Y aquí está el error que todos cometemos:'
VOZ[18] = 'En un tripié, en cambio, aguanta seis fotos de un segundo cada una.'

AMB = (255, 196, 90)       # ámbar de las luces de la ciudad
ROJO = (255, 64, 56)
VERDE = (90, 220, 140)
AMARILLO = (255, 236, 160)


def _palabras(i):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split()


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


def wt(i, k):
    n = len(_palabras(i))
    return TT(i) + (TE(i) - TT(i)) * k / n


def F(k, s):
    return M.font(k, s)


def cam(u, claves, cy=0.55):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p['roll'])


def K(u, dist, yaw, pitch=8, tx=0.0, ty=0.95, tz=0.0, roll=0.0):
    return (u, dict(tx=tx, ty=ty, tz=tz, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def sombra(fr, x, z, rx, ry=None, a=0.75):
    sx, sy = fr.cam.proj([(x, 0.01, z)])[0][0]
    D.shadow_blob(fr, sx, sy, rx, ry or rx * 0.25, a)


# ================================================================== la foto real y su ruido
_C = {}
_BASE = Image.open(os.path.join(HERE, 'img', 'img_monterrey_noche.jpg')).convert('RGB')


def _recorte(w, h, cx=0.55):
    bw, bh = _BASE.size
    cw = bh * w / h
    x0 = clamp(cx * bw - cw / 2, 0, bw - cw)
    return np.asarray(_BASE.resize((w, h), Image.LANCZOS, box=(x0, 0, x0 + cw, bh)), np.float32) / 255.0


def _ruidosa(arr, seed, osc=0.22, sig=0.15, grano=2):
    rng = np.random.RandomState(seed)
    h, w = arr.shape[:2]
    hh, ww = h // grano + 1, w // grano + 1
    n = rng.normal(0, sig, (hh, ww, 3)) * 0.7 + rng.normal(0, sig, (hh, ww, 1))
    n = np.repeat(np.repeat(n, grano, 0), grano, 1)[:h, :w]
    hot = (rng.rand(hh, ww) > 0.995)[..., None] * 0.7
    hot = np.repeat(np.repeat(hot, grano, 0), grano, 1)[:h, :w]
    out = arr * osc + np.abs(n) * 0.55 + n * 0.25 + hot
    return np.clip(out, 0, 1)


def _rgba(arr, a=255):
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    if a < 255:
        im.putalpha(a)
    return im


def slab(i):
    """Foto de 300x400 (3:4): i = 0..14 ruidosas, 'limpia' sin ruido."""
    if ('slab', i) not in _C:
        base = _C.setdefault('slab_base', _recorte(300, 400))
        _C[('slab', i)] = _rgba(np.clip(base * 1.15, 0, 1) if i == 'limpia' else _ruidosa(base, 100 + i))
    return _C[('slab', i)]


def visor(i):
    """Visor de la cámara 420x690: i ruidosa o 'limpia'."""
    if ('vf', i) not in _C:
        base = _C.setdefault('vf_base', _recorte(420, 690))
        arr = np.clip(base * 1.15, 0, 1) if i == 'limpia' else _ruidosa(base, 300 + i)
        _C[('vf', i)] = Image.fromarray((arr * 255).astype(np.uint8))
    return _C[('vf', i)]


def completa(i):
    """Cuadro completo 1080x1920 (ruidoso o limpio) para el zoom digital."""
    if ('full', i) not in _C:
        base = _C.setdefault('full_base', _recorte(1080, 1920, 0.56))
        _C[('full', i)] = np.clip(base * 1.1, 0, 1) if i == 'limpia' else _ruidosa(base, 500 + i, osc=0.32, grano=4, sig=0.16)
    return _C[('full', i)]


def mezcla(k):
    """Foto que va de ruidosa (0) a limpia (1)."""
    a = np.asarray(slab(0), np.float32)
    b = np.asarray(slab('limpia'), np.float32)
    return Image.fromarray((a * (1 - k) + b * k).astype(np.uint8), 'RGBA')


# ================================================================== planos de foto en 3D
def plano(fr, img, C, w, h, rx=0.0, ry=0.0, rz=0.0, alpha=1.0, borde=(235, 235, 240), glow=0.0, bcol=None):
    R = M3.rotm(rx, ry, rz)
    loc = np.array([[-w / 2, h / 2, 0], [w / 2, h / 2, 0], [w / 2, -h / 2, 0], [-w / 2, -h / 2, 0]])
    Pw = loc @ R.T + np.array(C, float)
    s, z = fr.cam.proj(Pw)
    if (z < 0.25).any():
        return None
    quad = [tuple(p) for p in s]
    M3.paste_quad(fr.base, quad, img, alpha)
    c = bcol or borde
    if c:
        fr.db.line(quad + [quad[0]], fill=M.scale_c(c, 0.9 * alpha), width=max(1, int(2.2 * S)))
    if glow:
        fr.df.line(quad + [quad[0]], fill=M.scale_c(bcol or WHITE, glow * alpha), width=max(1, int(4 * S)))
    return quad


def planos(fr, items):
    """items: [(img, C, w, h, kw)] dibujados de atrás hacia adelante."""
    zs = []
    for it in items:
        _, z = fr.cam.proj([it[1]])
        zs.append(z[0])
    out = {}
    for j in sorted(range(len(items)), key=lambda j: -zs[j]):
        img, C, w, h, kw = items[j]
        out[j] = plano(fr, img, C, w, h, **kw)
    return out


# ================================================================== pantallas del celular
def scr_camara(t, foto, cuenta=None, prog=0.0, flash=0.0, modo='NOCHE', ok=False, aviso=None, sacude=0.0):
    def dib(d, im):
        d.rectangle((0, 64, 420, 900), fill=(6, 7, 10))
        vf = foto
        if sacude > 0.01:
            a = np.asarray(vf, np.float32)
            dx = int(14 * sacude * math.sin(t * 40))
            b = np.roll(a, dx, 1)
            c = np.roll(a, -dx, 0)
            vf = Image.fromarray(((a + b + c) / 3).astype(np.uint8))
        im.paste(vf, (0, 90))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((140, 104, 280, 146), radius=21, fill=(20, 22, 30), outline=(255, 214, 120), width=2)
        d.ellipse((158, 113, 178, 133), fill=(255, 224, 150))
        d.ellipse((165, 109, 185, 129), fill=(20, 22, 30))
        d.text((222, 125), modo, font=F('sanss', 22), fill=(255, 224, 150), anchor='mm')
        if cuenta is not None:
            d.text((210, 430), str(cuenta), font=F('sansx', 210), fill=(255, 255, 255), anchor='mm')
            d.text((210, 560), 'No te muevas', font=F('sanss', 26), fill=(235, 235, 240), anchor='mm')
        if aviso:
            d.rounded_rectangle((40, 640, 380, 700), radius=14, fill=(190, 34, 30))
            d.text((210, 670), aviso, font=F('sans', 26), fill=(255, 255, 255), anchor='mm')
        cx, cy = 210, 828
        d.ellipse((cx - 44, cy - 44, cx + 44, cy + 44), outline=(240, 240, 244), width=5)
        d.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), fill=(250, 250, 252) if not ok else VERDE)
        if prog > 0:
            d.arc((cx - 52, cy - 52, cx + 52, cy + 52), -90, -90 + 360 * clamp(prog), fill=(255, 214, 120), width=7)
        if ok:
            d.line([(cx - 16, cy), (cx - 4, cy + 13), (cx + 18, cy - 12)], fill=(255, 255, 255), width=7)
        d.rounded_rectangle((330, 806, 376, 852), radius=10, fill=(40, 42, 50))
        if flash > 0.01:
            fl = Image.new('RGB', (420, 900), (255, 255, 255))
            im.paste(fl, (0, 0), Image.new('L', (420, 900), int(255 * clamp(flash))))
    return P.pantalla(dib)


# ================================================================== perro de line-art (recreación)
PERRO = [(0.10, 0.46), (0.30, 0.50), (0.55, 0.50), (0.66, 0.52), (0.72, 0.62), (0.76, 0.74), (0.79, 0.86), (0.84, 0.77),
         (0.90, 0.72), (0.98, 0.66), (0.97, 0.60), (0.86, 0.58), (0.78, 0.50), (0.76, 0.36), (0.78, 0.04), (0.71, 0.04),
         (0.68, 0.30), (0.36, 0.30), (0.30, 0.04), (0.23, 0.04), (0.20, 0.28), (0.12, 0.34), (0.10, 0.46)]
COLA = [(0.11, 0.46), (0.04, 0.57), (0.0, 0.69)]


def perro(img, fx, x, y, s, t, a=1.0, col=WHITE, corre=True):
    """Perro de alambre que brilla; (x, y) = esquina inferior izquierda en px; s = ancho en px."""
    if a <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    ph = t * 14 if corre else 0.0
    pts = []
    for i, (px, py) in enumerate(PERRO):
        dy = 0.0
        if corre and py < 0.1:
            dy = 0.05 * max(0.0, math.sin(ph + (0 if px > 0.5 else math.pi) + (0.6 if i % 2 else 0)))
        pts.append((x + px * s, y - (py + dy) * s))
    c = M.scale_c(col, a)
    d.line(pts, fill=c, width=max(2, int(s / 80)), joint='curve')
    df.line(pts, fill=M.scale_c(col, 0.6 * a), width=max(4, int(s / 45)), joint='curve')
    cola = [(x + px * s + (0.03 * s * math.sin(t * 20) if j else 0), y - py * s) for j, (px, py) in enumerate(COLA)]
    d.line(cola, fill=c, width=max(2, int(s / 80)), joint='curve')
    ex, ey = x + 0.86 * s, y - 0.68 * s
    r = s / 90
    d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=c)


# ================================================================== escenas
# 0. gancho, inicio tipo 12: cuenta regresiva 3-2-1 del modo noche y la foto se congela
def s_gancho(t, fi, u, d):
    tm = wt(1, 3) - TT(0)                         # «muevas»: se toma la foto
    b2, b1 = 0.55, 1.35                           # golpes del 2 y del 1
    fr = Frame(cam(u, [K(-2.6, 4.6, -62, 16, ty=1.0), K(-0.35, 2.7, -18, 6, ty=1.0), K(b2, 2.4, -6, 4, ty=1.0),
                       K(b1, 2.1, 6, 3, ty=1.0), K(tm, 2.7, 16, 6, ty=1.0), K(4.0, 2.65, 18, 6, ty=1.0)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    n = 3 if u < b2 else (2 if u < b1 else 1)
    sombra(fr, 0, 0, 320, 70)
    capt = u >= tm
    foto = visor('limpia') if capt else visor(int(t * 12) % 6)
    prog = clamp((u + 0.3) / (tm + 0.3)) if u >= -0.3 else 0.0
    flash = 1 - seg(u, tm, tm + 0.25) if capt else 0.0
    draw_objects(fr, P.celular(scr_camara(t, foto, prog=prog if not capt else 0.0, flash=flash, ok=capt)))
    cy_ = fr.cam.p1(np.array([0, 0.98, 0.05]))[1]

    def ui(img, fx):
        kicker(img, 'MODO NOCHE · NO TE MUEVAS', 140, seg(u, -0.3, 0.0), col=(255, 214, 140))
        if -0.3 <= u < tm:
            k = seg(u, -0.3, -0.12) if n == 3 else seg(u, (b2 if n == 2 else b1) - 0.15, b2 if n == 2 else b1)
            P.numero_golpe(img, fx, str(n), cy_, k, size=340, col=(255, 236, 190))
        if u >= 0.05:
            P.titulo_golpe(img, fx, [('Tu foto de noche', 'sans'), ('no es una foto.', 'serif')], 190, seg(u, 0.05, 0.2), size=80)
    fr.ui.append(ui)
    out = finish(fr, fi, flash=0.55 * flash)
    k = golpe_k(u, -0.12, 0.3) + golpe_k(u, 0.2, 0.3) + golpe_k(u, b2, 0.3) + golpe_k(u, b1, 0.3) + golpe_k(u, tm, 0.4)
    return sacudir(out, t, k, amp=22)


# 1. no es una foto: la foto flota, letras de cristal y «1 FOTO» tachado
def s_no_es(t, fi, u, d):
    tx = wt(2, 6) - TT(2)
    fr = Frame(cam(u, [K(-0.2, 3.2, 46, 12, ty=1.0), K(0.35, 2.9, -10, 6, ty=1.0), K(tx, 2.6, -16, 6, ty=1.0), K(3.0, 2.5, -20, 6, ty=1.0)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.5)
    glass_type(fr.base, fr.fx, 'FOTO', 540 * S, 980 * S, 330 * S, k=eout(seg(u, -0.2, 0.25)), fill_a=0.06)
    e = P.entrada(u, -0.2, 0.25, 'pop')
    s = max(0.05, e['escala'])
    plano(fr, slab(0), (0, 1.0, 0.1), 1.2 * s, 1.6 * s, ry=6 * math.sin(t * 1.3), glow=0.4)

    def ui(img, fx):
        kicker(img, 'LO QUE VES EN TU GALERÍA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        P.pill_tachada(img, fx, 540, 1380, '1 FOTO', seg(u, 0.1, 0.35), seg(u, tx, tx + 0.3), t, size=46)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. son muchas: la foto se abre en 15
def _abanico(k, n=15, sep=0.13, ang=0.0):
    out = []
    for i in range(n):
        j = i - (n - 1) / 2
        out.append((j * 0.10 * k, 1.0 + 0.02 * math.sin(i * 1.7) * k, -j * sep * k, j * ang * k))
    return out


def s_muchas(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 2.4, 0, 4, ty=1.0), K(0.3, 5.6, 32, 10, ty=1.0), K(2.0, 5.4, 38, 10, ty=1.0)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9)
    k = P.resorte(seg(u, -0.1, 0.35))
    items = []
    for i, (x, y, z, a) in enumerate(_abanico(k)):
        items.append((slab(i), (x, y, z), 0.8, 1.07, dict(ry=a, glow=0.25)))
    planos(fr, items)

    def ui(img, fx):
        P.numero_golpe(img, fx, '×15', 330, seg(u, 0.15, 0.3), size=200, col=(255, 224, 150))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.35), amp=20)


# 3. el modo noche de Google junta hasta 15 fotos (contador que sube y caen una por una)
def s_quince(t, fi, u, d):
    t15 = wt(4, 9) - TT(4)                           # «quince»
    fr = Frame(cam(u, [K(-0.2, 4.6, 70, 12, ty=1.0), K(0.3, 4.4, 62, 12, ty=1.0), K(t15 - 0.1, 4.2, 58, 11, ty=1.0),
                       K(t15 + 0.05, 3.6, 18, 6, ty=1.0), K(5.0, 3.5, 12, 6, ty=1.0)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.45)
    n = int(clamp((u + 0.1) / max(0.2, t15) * 15, 1, 15))
    items = []
    for i in range(n):
        u0 = -0.1 + t15 * i / 15
        e = P.entrada(u, u0, 0.18, 'cae')
        z = (i - 7) * 0.12
        items.append((slab(i), (0.0, 1.0 + max(0.0, -e['dy']) * 0.4, -z), 1.0, 1.33, dict(glow=0.2)))
    planos(fr, items)

    def ui(img, fx):
        kicker(img, 'MODO NOCHE DE GOOGLE · EJEMPLO', 140, seg(u, 0.0, 0.3), col=(150, 210, 230))
        f = F('sansx', 230)
        d_ = ImageDraw.Draw(img)
        txt = f'{n}'
        d_.text((540, 330), txt, font=f, fill=(255, 224, 150), anchor='mm')
        ImageDraw.Draw(fx).text((540, 330), txt, font=f, fill=(120, 100, 60), anchor='mm')
        pill(img, fx, 540, 1350, 'FOTOS DE 1/15 s', eout(seg(u, t15, t15 + 0.3)), size=34, border=(255, 214, 120))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, t15, 0.35), amp=18)


# 4. en cuanto aprietas el botón: punch-in al disparador y ráfaga 1/15 … 15/15
def s_boton(t, fi, u, d):
    tp = 0.35
    fr = Frame(cam(u, [K(-0.2, 2.9, -30, 10, ty=0.95), K(0.25, 1.35, -6, 4, ty=0.45, tx=0.0), K(2.0, 1.3, -2, 4, ty=0.45)]))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9)
    sombra(fr, 0, 0, 300, 70)
    k = clamp((u - tp) / 1.1)
    m = int(k * 15)
    fl = 0.22 if (u > tp and int((u - tp) * 14) % 2 == 0 and k < 1) else 0.0
    draw_objects(fr, P.celular(scr_camara(t, visor(m % 6), prog=k, flash=fl)))
    c = fr.cam.p1(np.array([0, 0.95 - 0.78 * 0.92 * 0.5 - 0.02, 0.06]))

    def ui(img, fx):
        doodle_circle(img, fx, c[0], c[1] + 40, 170, 170, t, k=eout(seg(u, 0.1, 0.4)), col=AMARILLO, w=6)
        if u > tp:
            P.numero_golpe(img, fx, f'{max(1, m)}/15', 330, 1.0, size=150, col=WHITE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tp, 0.3), amp=14)


# 5. cada una sale oscura y llena de puntitos: zoom digital x1 → x1.3 → x1.8
def s_puntitos(t, fi, u, d):
    t1, t2 = wt(6, 3) - TT(6), wt(6, 6) - TT(6)
    z = 1.0 if u < t1 else (1.35 if u < t2 else 1.9)
    z0 = 1.08 - 0.08 * P.eout4(seg(u, -0.2, 0.25))
    a = completa(0)
    img = Image.fromarray((a * 255).astype(np.uint8))
    out = M.scale_about(img, z * z0, 0.6, 0.48)
    im = Image.fromarray(out)
    rec_frame(im, t, 1.0, f'x{z:.1f}')
    kicker(im, '1 DE 15 · 1/15 s', 260, 1.0, col=(255, 214, 140))
    out = np.asarray(im)
    return sacudir(out, t, golpe_k(u, t1, 0.2) + golpe_k(u, t2, 0.2), amp=10)


# 6. eso es ruido: letras de cristal y garabatos sobre los puntitos
def s_ruido(t, fi, u, d):
    a = completa(1 + int(t * 10) % 3)
    zz = 2.3 - 0.25 * P.eout4(seg(u, -0.1, 0.4))
    img = Image.fromarray(M.scale_about(Image.fromarray((a * 255).astype(np.uint8)), zz, 0.62, 0.5))
    fx = Image.new('RGB', (M.W, M.H), (0, 0, 0))
    glass_type(img, fx, 'RUIDO', 540, 960, 250, k=eout(seg(u, 0.0, 0.3)), fill_a=0.14, edge=0.8)
    for j, (x, y, r) in enumerate(((250, 520, 70), (820, 640, 60), (330, 1300, 80))):
        doodle_circle(img, fx, x, y, r, r * 0.9, t, k=eout(seg(u, 0.25 + 0.15 * j, 0.5 + 0.15 * j)), col=AMARILLO, w=6, seed=j)
    o = np.asarray(img, np.float32) + np.asarray(fx, np.float32) * 0.7
    return o.clip(0, 255).astype(np.uint8)


# 7. cada píxel del sensor cuenta partículas de luz (rayos X → sensor)
def _sensor(fr, t, n=8, paso=0.2, k=1.0, foco=None):
    cols = [(150, 40, 36), (40, 130, 60), (40, 60, 150)]
    ms = []
    for i in range(n):
        for j in range(n):
            c = cols[1] if (i + j) % 2 else (cols[0] if i % 2 == 0 else cols[2])
            if foco and (i, j) == foco:
                c = M.mixc(c, (255, 236, 160), 0.5 + 0.5 * math.sin(t * 8))
            b = named(M3.box(paso * 0.86, 0.05, paso * 0.86, c, shadow=0, base=True, gloss=0.7), 'px', rim=0.5, gloss=0.7)
            ms.append(b.tf(t=((i - (n - 1) / 2) * paso, 0.0, (j - (n - 1) / 2) * paso)))
    draw_objects(fr, ms)


def s_pixel(t, fi, u, d):
    tc = 1.25
    if u < tc:
        fr = Frame(cam(u, [K(-0.2, 3.6, 140, 8, ty=1.0), K(0.3, 3.1, 168, 6, ty=1.0), K(0.75, 3.0, 172, 6, ty=1.05),
                           K(tc - 0.05, 1.1, 180, 3, ty=1.57, tx=-0.18)]))
        space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8)
        draw_objects(fr, P.celular(scr_camara(t, visor(0)), interior=True), xray=seg(u, -0.1, 0.4), keep=('in',))
        c = fr.cam.p1(np.array([-0.18, 0.95 + 0.62, -0.03]))

        def ui(img, fx):
            kicker(img, 'RAYOS X · CÁMARA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
            doodle_circle(img, fx, c[0], c[1], 90, 90, t, k=eout(seg(u, 0.35, 0.7)), col=AMARILLO, w=6)
        fr.ui.append(ui)
        out = finish(fr, fi)
        return out
    uu = u - tc
    fr = Frame(cam(uu, [K(0.0, 1.0, 20, 70, ty=0.0), K(0.3, 2.3, 30, 48, ty=0.0), K(2.5, 2.2, 36, 46, ty=0.0)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.9)
    _sensor(fr, t, foco=(4, 3))
    p = fr.cam.p1(np.array([(4 - 3.5) * 0.2, 0.05, (3 - 3.5) * 0.2]))
    rng = np.random.RandomState(int(t * 8))
    for q in range(6):
        x, z = rng.uniform(-0.8, 0.8, 2)
        y = 1.2 - ((t * 2 + q * 0.37) % 1.2)
        dot3(fr, (x, y, z), r=4, col=AMARILLO, a=0.9, glow=1.2)

    def ui(img, fx):
        kicker(img, 'SENSOR DE LA CÁMARA', 150, 1.0, col=(150, 210, 230))
        pill(img, fx, p[0], p[1] - 160, 'UN PÍXEL', eout(seg(uu, 0.2, 0.45)), size=32, border=AMARILLO)
        ImageDraw.Draw(img).line([(p[0], p[1] - 125), (p[0], p[1] - 10)], fill=AMARILLO, width=3)
    fr.ui.append(ui)
    return P.N.flash_in(finish(fr, fi), t, t - uu, 0.14, 120)


# 8. de noche le llegan tan poquitas que se equivoca (cubetas con fotones)
def s_poquitas(t, fi, u, d):
    te = wt(9, 9) - TT(9)
    fr = Frame(cam(u, [K(-0.2, 5.0, -30, 30, ty=0.6), K(0.3, 4.4, -12, 22, ty=0.6), K(te, 4.2, -6, 20, ty=0.6),
                       K(te + 0.05, 3.6, 10, 16, ty=0.6), K(4.0, 3.55, 12, 16, ty=0.6)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    ms = []
    pos = [(-0.75, 0.0), (0.0, 0.0), (0.75, 0.0)]
    cuentas = []
    for i, (x, z) in enumerate(pos):
        e = P.entrada(u, -0.2 + 0.08 * i, 0.22, 'pop')
        s = max(0.05, e['escala'])
        w = named(M3.rbox(0.5 * s, 0.7 * s, 0.5 * s, 0.05, (52, 54, 62), n=4, shadow=0, gloss=0.4), 'cubeta', rim=0.8)
        ms.append(w.tf(t=(x, 0, z)))
        rng = np.random.RandomState(40 + i)
        tiempos = sorted(rng.uniform(-0.2, 3.2, 3 + i * 2 % 5))
        cuentas.append(sum(1 for tt in tiempos if u > tt + 0.5))
    draw_objects(fr, ms)
    for i, (x, z) in enumerate(pos):
        rng = np.random.RandomState(40 + i)
        tiempos = sorted(rng.uniform(-0.2, 3.2, 3 + i * 2 % 5))
        for tt in tiempos:
            if tt < u < tt + 0.5:
                y = 2.0 - 1.7 * (u - tt) / 0.5
                dot3(fr, (x + 0.05 * math.sin(tt * 9), y, z), r=6, col=AMARILLO, a=1.0, glow=1.4)
    tops = [fr.cam.p1(np.array([x, 0.95, z])) for x, z in pos]

    def ui(img, fx):
        kicker(img, 'DE NOCHE · POCA LUZ', 150, seg(u, 0.0, 0.3), col=(255, 214, 140))
        for (x, y, _), c in zip(tops, cuentas):
            ImageDraw.Draw(img).text((x, y - 60), str(c), font=F('mono', 90), fill=AMARILLO, anchor='mm')
            ImageDraw.Draw(fx).text((x, y - 60), str(c), font=F('mono', 90), fill=(120, 110, 70), anchor='mm')
        pill(img, fx, 540, 1330, 'DEBERÍA DECIR 3', eout(seg(u, te - 0.6, te - 0.3)), size=32, border=(200, 200, 210), dot=False)
        P.titulo_golpe(img, fx, [('Se equivoca.', 'serif')], 280, seg(u, te, te + 0.15), size=90, col=(255, 120, 110))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, te + 0.15, 0.35), amp=16)


# 9. se equivoca al azar: 3 fotos con el error en otro lugar
def s_azar(t, fi, u, d):
    tl = wt(10, 7) - TT(10)
    fr = Frame(cam(u, [K(-0.2, 4.4, -24, 6, ty=1.0, tx=-0.6), K(0.3, 4.2, -8, 4, ty=1.0, tx=0.0), K(tl, 4.0, 4, 4, ty=1.0),
                       K(tl + 0.05, 3.6, 14, 4, ty=1.0, tx=0.2), K(4.0, 3.5, 16, 4, ty=1.0, tx=0.2)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.4)
    xs = (-0.88, 0.0, 0.88)
    items = []
    for i, x in enumerate(xs):
        e = P.entrada(u, -0.2 + 0.1 * i, 0.22, 'desliza')
        items.append((slab(3 + i), (x + e['dy'] * 0.3, 1.0, 0.0), 0.8, 1.07, dict(ry=(-8, 0, 8)[i], glow=0.25)))
    planos(fr, items)
    marcas = [(-0.88 - 0.2, 1.3), (0.14, 0.7), (0.88 + 0.22, 1.12)]
    pm = [fr.cam.p1(np.array([x, y, 0.02])) for x, y in marcas]
    lab = [fr.cam.p1(np.array([x, 0.4, 0.0])) for x in xs]

    def ui(img, fx):
        kicker(img, 'EL ERROR CAMBIA DE LUGAR', 150, seg(u, 0.0, 0.3), col=(255, 214, 140))
        for i, ((x, y, _), (lx, ly, _)) in enumerate(zip(pm, lab)):
            doodle_circle(img, fx, x, y, 50, 50, t, k=eout(seg(u, tl + 0.2 * i, tl + 0.25 + 0.2 * i)), col=ROJO, w=6, seed=i)
            ImageDraw.Draw(img).text((lx, ly + 20), f'FOTO {i + 1}', font=F('mono', 30), fill=(210, 212, 220), anchor='mm')
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. alinea las 15 y saca el promedio (se juntan de golpe y queda limpia)
def s_alinea(t, fi, u, d):
    ta = wt(11, 3) - TT(11)
    tp = wt(11, 8) - TT(11)
    fr = Frame(cam(u, [K(-0.2, 4.6, -40, 14, ty=1.0), K(ta, 4.2, -30, 12, ty=1.0), K(ta + 0.05, 3.3, -12, 6, ty=1.0),
                       K(tp, 3.2, -10, 6, ty=1.0), K(tp + 0.05, 2.5, 0, 3, ty=1.0), K(4.0, 2.45, 2, 3, ty=1.0)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    k = 1 - P.eout4(seg(u, ta - 0.1, ta + 0.35))
    rng = np.random.RandomState(9)
    if u < tp:
        items = []
        for i in range(15):
            ox, oy, oz = rng.uniform(-1.1, 1.1), rng.uniform(-0.6, 0.6), rng.uniform(-1.2, 0.8)
            items.append((slab(i), (ox * k, 1.0 + oy * k, oz * k - i * 0.01), 1.0, 1.33,
                          dict(rz=rng.uniform(-30, 30) * k, ry=rng.uniform(-40, 40) * k, glow=0.2, alpha=0.85 if k < 0.05 else 1.0)))
        planos(fr, items)
    else:
        km = seg(u, tp, tp + 0.35)
        plano(fr, mezcla(km), (0, 1.0, 0), 1.2, 1.6, glow=0.6, bcol=(255, 224, 150))

    def ui(img, fx):
        kicker(img, 'ALINEA + PROMEDIA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if u >= tp:
            P.titulo_golpe(img, fx, [('15 fotos →', 'sans'), ('una sola.', 'serif')], 230, seg(u, tp, tp + 0.15), size=80)
    fr.ui.append(ui)
    fl = 0.7 * (1 - seg(u, tp, tp + 0.3)) if u >= tp else 0.0
    out = finish(fr, fi, flash=fl)
    return sacudir(out, t, golpe_k(u, ta + 0.3, 0.3) + golpe_k(u, tp, 0.4), amp=22)


# 11. la luz se suma y el ruido se cancela (foto real que cae, mitad ruidosa / mitad limpia)
def s_suma(t, fi, u, d):
    ts, tc = wt(12, 3) - TT(12), wt(12, 7) - TT(12)
    fr = Frame(cam(u, [K(-0.2, 3.0, 16, 30, ty=0.6), K(0.3, 3.4, -6, 22, ty=0.6), K(3.0, 3.3, -10, 22, ty=0.6)]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9)
    xw = clamp(0.15 + 0.85 * seg(u, 0.2, tc + 0.3))
    a = np.asarray(slab(0), np.float32)
    b = np.asarray(slab('limpia'), np.float32)
    cut = int(300 * xw)
    m = a.copy()
    m[:, :cut] = b[:, :cut]
    m[:, max(0, cut - 3):cut + 3, :3] = 255
    foto = Image.fromarray(m.astype(np.uint8), 'RGBA').convert('RGB')

    def ui(img, fx):
        photo_card(img, fx, foto, 540, 900, 600, t - u - 0.1, t, caption='NASA · ISS · MONTERREY DE NOCHE', angle0=-10)
        pill(img, fx, 300, 1420, 'LUZ: SE SUMA', eout(seg(u, ts, ts + 0.3)), size=32, border=(255, 214, 120))
        pill(img, fx, 780, 1420, 'RUIDO: SE CANCELA', eout(seg(u, tc, tc + 0.3)), size=32, border=CYAN)
        kicker(img, 'FOTO REAL · PROMEDIO (RECREACIÓN)', 150, 1.0, col=(150, 152, 160))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


# 12. con 15 fotos el ruido baja casi 4 veces (gráfico que crece)
def s_grafica(t, fi, u, d):
    t4 = wt(13, 7) - TT(13)
    fr = Frame(cam(u, [K(-0.2, 6.0, -18, 18, ty=0.6), K(0.3, 6.2, 0, 14, ty=0.6), K(4.0, 6.0, 6, 14, ty=0.6)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'RUIDO SEGÚN CUÁNTAS FOTOS JUNTA', 150, seg(u, -0.1, 0.2))
        chart_grow(img, fx, (90, 300, 990, 1220), [100, 50, 33, 26], ['1', '4', '9', '15'], t - u - 0.1, t,
                   unit='%', title_txt='RUIDO · % · FOTOS ABAJO', tag='APROX.', line=True)
        P.numero_golpe(img, fx, '÷4', 1370, seg(u, t4 - 0.15, t4), size=160, col=(255, 224, 150))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, t4, 0.35), amp=18)


# 13. el error que todos cometemos (el visor tiembla, aviso rojo)
def s_error(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 1.9, 24, 4, ty=1.0, roll=-8), K(0.25, 2.7, -10, 6, ty=1.0, roll=6), K(3.0, 2.8, -14, 6, ty=1.0, roll=4)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)
    sombra(fr, 0, 0, 300, 70)
    tb = 0.12 * math.sin(t * 23)
    ph = P.celular(scr_camara(t, visor(int(t * 12) % 6), aviso='¡SE MOVIÓ!' if int(t * 6) % 2 == 0 else None, sacude=1.0),
                   rz=8 * math.sin(t * 17), off=(tb, 0.05 * math.sin(t * 29), 0))
    draw_objects(fr, ph)

    def ui(img, fx):
        if int(t * 8) % 2 == 0 or u < 0.3:
            kicker(img, 'ERROR · MOVIMIENTO', 140, 1.0, col=ROJO, size=30)
        P.titulo_golpe(img, fx, [('El error que', 'sans'), ('todos cometemos.', 'serif')], 200, seg(u, 0.05, 0.2), size=74, col=WHITE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.35 + golpe_k(u, 0.2, 0.4), amp=16)


# 14. si tú o tu perro se mueven, las fotos no encajan
def s_perro(t, fi, u, d):
    tn = wt(15, 9) - TT(15)
    fr = Frame(cam(u, [K(-0.2, 3.9, 30, 8, ty=1.0), K(0.3, 3.7, 8, 6, ty=1.0), K(tn, 3.6, 4, 6, ty=1.0),
                       K(tn + 0.05, 3.0, -20, 6, ty=1.0), K(4.0, 2.9, -24, 6, ty=1.0)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9)
    mal = seg(u, 0.3, tn)
    items = []
    for i in range(3):
        items.append((slab(6 + i), (0.18 * i * mal - 0.18, 1.0 + 0.09 * i * mal, -0.05 * i), 1.1, 1.47,
                      dict(rz=5 * i * mal, alpha=0.8, glow=0.4, bcol=M.mixc(WHITE, ROJO, mal))))
    q = planos(fr, items)

    def ui(img, fx):
        x = -300 + 1500 * seg(u, 0.0, 2.6)
        perro(img, fx, x, 1450, 360, t, a=1.0)
        if u >= tn:
            pill(img, fx, 540, 330, 'NO ENCAJAN', eout(seg(u, tn, tn + 0.25)), size=44, border=ROJO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tn, 0.35), amp=14)


# 15. tira los pedazos que no puede alinear (mosaico; los rojos salen volando)
def s_pedazos(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.6, -40, 10, ty=1.0), K(0.3, 3.1, -14, 6, ty=1.0), K(3.0, 3.0, -18, 6, ty=1.0)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.4)
    im = slab(10)
    nx, ny = 4, 5
    w, h = 1.2, 1.6
    tw, th = 300 // nx, 400 // ny
    malos = {(1, 1), (2, 3), (3, 0), (0, 4), (2, 1)}
    items = []
    for i in range(nx):
        for j in range(ny):
            tile = im.crop((i * tw, j * th, (i + 1) * tw, (j + 1) * th))
            cx = -w / 2 + (i + 0.5) * w / nx
            cy = 1.0 + h / 2 - (j + 0.5) * h / ny
            kw = dict(glow=0.15)
            C = (cx, cy, 0.0)
            if (i, j) in malos:
                kf = seg(u, 0.5 + 0.15 * ((i + j) % 3), 1.4 + 0.15 * ((i + j) % 3))
                C = (cx + (0.6 if i > 1 else -0.6) * kf, cy - 2.2 * kf ** 2 + 0.4 * kf, 0.5 * kf)
                kw = dict(rz=200 * kf * (1 if i % 2 else -1), ry=90 * kf, bcol=ROJO, glow=0.6, alpha=1 - 0.6 * kf)
            items.append((tile, C, w / nx * 0.97, h / ny * 0.97, kw))
    planos(fr, items)

    def ui(img, fx):
        kicker(img, 'LO QUE NO ALINEA, LO TIRA', 150, seg(u, 0.0, 0.3), col=(255, 140, 120))
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. borroso o con fantasmas
def s_fantasmas(t, fi, u, d):
    tf = wt(17, 7) - TT(17)
    fr = Frame(cam(u, [K(-0.2, 2.6, 20, 6, ty=1.0), K(0.3, 3.0, -6, 6, ty=1.0), K(3.0, 2.9, -10, 6, ty=1.0)]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9)
    base = np.asarray(slab('limpia'), np.float32)
    bl = np.asarray(Image.fromarray(base.astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(4 * eout(seg(u, 0.0, 0.6)))), np.float32)
    plano(fr, Image.fromarray(bl.astype(np.uint8), 'RGBA'), (0, 1.0, 0), 1.25, 1.66, glow=0.3)
    q = fr.cam.p1(np.array([-0.5, 0.45, 0.0]))

    def ui(img, fx):
        kicker(img, 'RECREACIÓN', 150, 1.0, col=(150, 152, 160))
        n = 4
        for g in range(n):
            a = (1.0 if g == 0 else 0.45 - 0.1 * g) * (1.0 if g == 0 else eout(seg(u, tf - 0.4, tf)))
            perro(img, fx, q[0] - 70 * g * eout(seg(u, tf - 0.4, tf)), q[1] + 120, 330, t * 0.3, a=a, col=(220, 230, 255), corre=False)
        pill(img, fx, 780, 520, 'FANTASMAS', eout(seg(u, tf, tf + 0.25)), size=40, border=ROJO)
        M.doodle_arrow(img, fx, 760, 570, q[0] + 220, q[1] - 40, t, k=eout(seg(u, tf + 0.1, tf + 0.5)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. en un tripié aguanta 6 fotos de 1 segundo (tripié de alambre)
def tripie(fr, t, k=1.0, top=1.0):
    ap = np.array([0, top, 0])
    for a in (90, 210, 330):
        r = math.radians(a)
        pie = np.array([0.55 * math.cos(r), 0.0, 0.55 * math.sin(r)])
        line3(fr, [ap, ap + (pie - ap) * k], col=(220, 222, 230), w=6, a=1.0, glow=0.6)
    line3(fr, [ap, ap + np.array([0, 0.08, 0])], col=(220, 222, 230), w=10, a=1.0, glow=0.6)


def s_tripie(t, fi, u, d):
    t6 = wt(18, 6) - TT(18)
    if u < t6:
        fr = Frame(cam(u, [K(-0.2, 5.6, 60, 18, ty=1.25), K(0.3, 5.0, 30, 12, ty=1.25), K(t6, 4.8, 24, 12, ty=1.25)]))
    else:
        fr = Frame(cam(u - t6, [K(0.0, 4.0, -10, 6, ty=1.5), K(0.25, 5.2, -26, 8, ty=1.45), K(3.0, 5.1, -30, 8, ty=1.45)]))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9, beam=0.5)
    k = P.eout4(seg(u, -0.2, 0.2))
    tripie(fr, t, k)
    if u >= t6:
        items = []
        for i in range(6):
            e = P.entrada(u, t6 + 0.06 * i, 0.2, 'pop')
            s = max(0.05, e['escala'])
            a_ = math.radians(-60 + 24 * i)
            items.append((slab(i), (1.05 * math.sin(a_), 1.95 + 0.55 * math.cos(a_), -0.5), 0.42 * s, 0.56 * s, dict(glow=0.3)))
        planos(fr, items)
    e = P.entrada(u, -0.05, 0.25, 'cae')
    draw_objects(fr, P.celular(scr_camara(t, visor('limpia'), prog=clamp(u / 4.4)), off=(0, 0.91 + max(0.0, -e['dy']) * 0.3, 0)))

    def ui(img, fx):
        kicker(img, 'EN TRIPIÉ', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if u >= t6:
            P.numero_golpe(img, fx, '6 × 1 s', 330, seg(u, t6, t6 + 0.15), size=170, col=(255, 224, 150))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, t6 + 0.15, 0.35) + golpe_k(u, 0.2, 0.25) * 0.6, amp=18)


# 18. truco: recárgate en una pared
def ladrillos():
    if 'lad' not in _C:
        w, h = 600, 660
        im = Image.new('RGB', (w, h), (40, 36, 34))
        d = ImageDraw.Draw(im)
        rng = np.random.RandomState(3)
        bh, bw = 44, 120
        for r in range(h // bh + 1):
            off = (bw // 2) if r % 2 else 0
            for c in range(-1, w // bw + 2):
                x0, y0 = c * bw + off, r * bh
                g = rng.randint(-14, 14)
                d.rectangle((x0 + 3, y0 + 3, x0 + bw - 3, y0 + bh - 3), fill=(150 + g, 78 + g // 2, 58 + g // 2))
        _C['lad'] = im.convert('RGBA')
    return _C['lad']


def s_pared(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.2, 70, 10, ty=1.0, tz=-0.2), K(0.3, 3.4, 38, 8, ty=1.0, tz=-0.2), K(3.0, 3.3, 34, 8, ty=1.0, tz=-0.2)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.5, beam_x=0.6)
    pared = M3.box(2.8, 2.6, 0.2, (150, 80, 60), shadow=0, base=True, gloss=0.1)
    M3.decal(pared, pared.FACE['front'], ladrillos())
    pared = named(pared.tf(t=(-0.4, 0, -0.7)), 'pared', rim=0.4)
    e = P.entrada(u, -0.15, 0.25, 'desliza')
    draw_objects(fr, [pared] + P.celular(scr_camara(t, visor('limpia')), ry=-8, off=(0.45 + e['dy'] * 0.3, 0.05, -0.52)))
    c = fr.cam.p1(np.array([0.45, 1.0, -0.55]))

    def ui(img, fx):
        kicker(img, 'TRUCO', 150, seg(u, 0.0, 0.2), col=AMARILLO, size=34)
        pill(img, fx, 540, 300, 'APOYA EL CELULAR', eout(seg(u, 0.3, 0.55)), size=36, border=AMARILLO)
        M.doodle_arrow(img, fx, 560, 360, c[0] - 40, c[1] - 250, t, k=eout(seg(u, 0.5, 0.9)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.1, 0.3), amp=14)


# 19. no te muevas hasta que termine el contador (vista desde arriba)
def s_contador(t, fi, u, d):
    tf = TE(20) - TT(20) - 0.1
    fr = Frame(cam(u, [K(-0.2, 2.3, 0, 40, ty=1.0), K(0.3, 2.5, -14, 12, ty=1.0), K(tf - 0.4, 2.3, -10, 8, ty=1.0),
                       K(tf, 2.9, 10, 8, ty=1.0), K(4.0, 2.8, 12, 8, ty=1.0)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    sombra(fr, 0, 0, 300, 70)
    pr = clamp(u / tf)
    n = 3 - int(pr * 3)
    ok = u >= tf
    draw_objects(fr, P.celular(scr_camara(t, visor('limpia') if ok else visor(2), cuenta=None if ok else max(1, n), prog=0 if ok else pr, ok=ok)))

    def ui(img, fx):
        kicker(img, 'QUIETO 3 SEGUNDOS', 150, seg(u, 0.0, 0.3), col=(255, 214, 140))
        if ok:
            pill(img, fx, 540, 1380, 'FOTO LIMPIA', eout(seg(u, tf, tf + 0.25)), size=40, border=VERDE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, flash=0.4 * (1 - seg(u, tf, tf + 0.25)) if ok else 0.0), t, golpe_k(u, tf, 0.3), amp=14)


# 20. mándaselo a quien sale borroso en la fiesta
def scr_fiesta(t):
    def dib(d, im):
        d.rectangle((0, 64, 420, 900), fill=(14, 10, 22))
        rng = np.random.RandomState(5)
        cols = [(255, 80, 120), (255, 200, 60), (80, 200, 255), (140, 255, 140), (255, 140, 40)]
        for r in range(3):
            y = 130 + r * 26
            for i in range(9):
                x = i * 48 + (r % 2) * 24
                d.polygon([(x, y), (x + 40, y), (x + 34, y + 30), (x + 6, y + 30)], fill=cols[(i + r) % 5])
        for _ in range(60):
            x, y = rng.uniform(0, 420), rng.uniform(220, 860)
            r_ = rng.uniform(3, 8)
            d.ellipse((x - r_, y - r_, x + r_, y + r_), fill=cols[rng.randint(5)])
        tmp = im.filter(ImageFilter.GaussianBlur(5))
        im.paste(tmp)
        d2 = ImageDraw.Draw(im)
        d2.text((210, 820), 'fiesta_borrosa.jpg', font=F('mono', 22), fill=(200, 200, 206), anchor='mm')
    return P.pantalla(dib)


def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.3, 36, 10, ty=0.95), K(0.3, 3.0, 12, 6, ty=0.95), K(3.5, 2.9, 16, 6, ty=0.95)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.85, bokeh=1.0, beam=0.5)
    sombra(fr, 0, 0, 300, 70)
    e = P.entrada(u, -0.15, 0.25, 'gira')
    draw_objects(fr, P.celular(scr_fiesta(t), ry=math.degrees(e['giro']) * 0.5))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien siempre', 'sans'), ('sale borroso en la fiesta.', 'serif')], 170, seg(u, 0.0, 0.4), size=62)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[]),
           dict(desde=2, fn=s_no_es, tr='giro', sfx=[(0.0, 'shimmer', 0.6)]),
           dict(desde=3, fn=s_muchas, tr='golpe', sfx=[]),
           dict(desde=4, fn=s_quince, tr='deslizar', sfx=[]),
           dict(desde=5, fn=s_boton, tr='whip', sfx=[]),
           dict(desde=6, fn=s_puntitos, tr='push', c=(0.5, 0.5), sfx=[]),
           dict(desde=7, fn=s_ruido, tr='glitch', sfx=[(0.0, 'shimmer', 0.6)]),
           dict(desde=8, fn=s_pixel, tr='zoom', c=(0.5, 0.45), sfx=[]),
           dict(desde=9, fn=s_poquitas, tr='deslizar_abajo', sfx=[]),
           dict(desde=10, fn=s_azar, tr='wipe', sfx=[]),
           dict(desde=11, fn=s_alinea, tr='iris', sfx=[]),
           dict(desde=12, fn=s_suma, tr='flash', sfx=[]),
           dict(desde=13, fn=s_grafica, tr='deslizar', sfx=[]),
           dict(desde=14, fn=s_error, tr='golpe', sfx=[]),
           dict(desde=15, fn=s_perro, tr='whip_izq', sfx=[]),
           dict(desde=16, fn=s_pedazos, tr='giro', sfx=[]),
           dict(desde=17, fn=s_fantasmas, tr='glitch', sfx=[]),
           dict(desde=18, fn=s_tripie, tr='wipe', sfx=[]),
           dict(desde=19, fn=s_pared, tr='push', c=(0.45, 0.5), sfx=[]),
           dict(desde=20, fn=s_contador, tr='iris', sfx=[]),
           dict(desde=21, fn=s_mandalo, tr='ritmo', sfx=[]),
           dict(desde=22, loop=True, tr='whip')]


def _sfx_dinamicos():
    tm = wt(1, 3) - TT(0)
    E = ESCENAS
    E[0]['sfx'] = [(-0.12, 'bass', 1.0), (0.45, 'bass', 0.9), (1.15, 'bass', 0.9), (0.0, 'tick', 0.5), (0.45, 'tick', 0.5),
                   (1.15, 'tick', 0.5), (tm, 'click', 1.0), (tm + 0.02, 'burst', 0.5), (tm + 0.15, 'sub', 0.9)]
    E[1]['sfx'] += [(wt(2, 6) - TT(2), 'scribble', 0.7), (0.1, 'tick', 0.5)]
    E[2]['sfx'] = [(0.0, 'whoosh', 0.6)] + [(0.0 + 0.02 * i, 'tick2', 0.25) for i in range(8)] + [(0.3, 'bass', 0.8)]
    t15 = wt(4, 9) - TT(4)
    E[3]['sfx'] = [(-0.1 + t15 * i / 15, 'tick2', 0.35) for i in range(15)] + [(t15, 'bass', 0.9), (t15 + 0.05, 'chime_c', 0.5)]
    E[4]['sfx'] = [(0.0, 'whoosh', 0.4), (0.35, 'click', 1.0)] + [(0.35 + i * 1.1 / 15, 'tick', 0.35) for i in range(15)]
    E[5]['sfx'] = [(0.0, 'click', 0.8), (wt(6, 3) - TT(6), 'click', 1.0), (wt(6, 6) - TT(6), 'click', 1.0)]
    E[6]['sfx'] += [(0.25, 'scribble', 0.7), (0.55, 'scribble', 0.5)]
    E[7]['sfx'] = [(0.0, 'shimmer', 0.6), (0.35, 'scribble', 0.6), (1.25, 'burst', 0.5), (1.3, 'thud', 0.7), (1.5, 'tick', 0.6)]
    te = wt(9, 9) - TT(9)
    E[8]['sfx'] = [(x, 'tick2', 0.4) for x in (0.4, 0.9, 1.6, 2.2, 2.8)] + [(te, 'bass', 0.9)]
    tl = wt(10, 7) - TT(10)
    E[9]['sfx'] = [(-0.2, 'whoosh', 0.4), (tl, 'scribble', 0.6), (tl + 0.2, 'tick', 0.4), (tl + 0.4, 'tick', 0.4)]
    ta, tp = wt(11, 3) - TT(11), wt(11, 8) - TT(11)
    E[10]['sfx'] = [(ta - 0.1, 'whoosh', 0.7), (ta + 0.3, 'thud', 0.9), (tp - 0.4, 'riser', 0.5), (tp, 'burst', 0.6), (tp + 0.02, 'sub', 1.0),
                    (tp + 0.1, 'chime_c', 0.6)]
    E[11]['sfx'] = [(0.1, 'slap', 0.8), (wt(12, 3) - TT(12), 'chime_a', 0.6), (wt(12, 7) - TT(12), 'chime_b', 0.6)]
    t4 = wt(13, 7) - TT(13)
    E[12]['sfx'] = [(0.15, 'chime_a', 0.6), (0.43, 'chime_a', 0.5), (0.71, 'chime_b', 0.6), (0.99, 'chime_c', 0.7), (t4, 'bass', 1.0)]
    E[13]['sfx'] = [(0.0, 'burst', 0.6), (0.05, 'tick2', 0.6), (0.2, 'bass', 1.0), (0.6, 'burst', 0.3), (1.2, 'burst', 0.3)]
    tn = wt(15, 9) - TT(15)
    E[14]['sfx'] = [(0.1, 'whoosh_suave', 0.5), (tn, 'slap', 0.8), (tn + 0.05, 'tick', 0.5)]
    E[15]['sfx'] = [(0.5, 'whoosh', 0.5), (0.65, 'whoosh', 0.4), (0.8, 'whoosh', 0.4), (1.3, 'thud', 0.5)]
    tf = wt(17, 7) - TT(17)
    E[16]['sfx'] = [(tf - 0.4, 'whoosh_suave', 0.5), (tf, 'tick', 0.6), (tf + 0.1, 'scribble', 0.6)]
    t6 = wt(18, 6) - TT(18)
    E[17]['sfx'] = [(0.2, 'thud', 0.7), (t6, 'whoosh', 0.5)] + [(t6 + 0.06 * i, 'tick2', 0.4) for i in range(6)] + [(t6 + 0.15, 'bass', 1.0)]
    E[18]['sfx'] = [(0.1, 'thud', 0.8), (0.3, 'tick', 0.6), (0.5, 'scribble', 0.6)]
    tf2 = TE(20) - TT(20) - 0.1
    E[19]['sfx'] = [(tf2 * i / 3, 'tick', 0.6) for i in range(3)] + [(tf2, 'click', 1.0), (tf2 + 0.05, 'chime_c', 0.7)]
    E[20]['sfx'] = [(0.0, 'shimmer', 0.5), (0.1, 'whoosh', 0.4)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
