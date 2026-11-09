"""Reel diario: «Tu tele 4K… no la ves en 4K.» Mié 11-nov-2026, 10:00 (CDMX). Voz Isaac. Buen Fin (13 al 17-nov).
Inicio tipo 7 (macro extremo que se aleja: el primer cuadro son subpixeles rojo-verde-azul gigantes e irreconocibles; un zoom
hacia atrás revela la imagen, la tele y el sillón; «4K» de cristal detrás de la tele). El final regresa: la cámara se clava en la
pantalla hasta los subpixeles (loop).
Datos: 4K = 3840×2160 = 8 294 400 pixeles = 4 × Full HD (1920×1080). Ashraf et al., Nature Communications (2025, Universidad de
Cambridge): el ojo separa en promedio 94 pixeles por grado (gris, de frente). Cálculo propio con esa cifra: tele de 43" (0.95 m de
ancho) → Full HD da 53 pixeles por grado a 1.5 m (sí se nota el 4K) y 106 a 3 m (ya no). TDT de México (ATSC 1.0): HD = 720p o
1080i (IFT); el 4K de Netflix solo en Premium y ~15 Mbps (help.netflix.com/node/306). Fuentes en guiones/2026-11-11_tele.txt.
Tele, sillón, antena, tarjetas de planes, etiqueta y caja: RECREACIÓN sin marcas."""
import math, os, re, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import cargador as CG
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'tele'
TXT = ['Tu tele 4K… no la ves en 4K.',
       'Tiene más de 8 millones de puntitos de luz: 4 veces más que una Full HD.',
       'Pero tu ojo tiene un límite: en Cambridge midieron que separa unos 94 puntitos por grado.',
       'Mira una tele de 43 pulgadas a metro y medio: el 4K sí se nota.',
       'Ahora vete al sillón, a 3 metros: tu ojo ya no la distingue de una Full HD.',
       'Los puntitos son tan chiquitos que tu ojo los junta.',
       'Y aquí viene lo peor: mucho de lo que ves ni siquiera viene en 4K.',
       'La tele abierta en México llega, cuando mucho, en HD.',
       'Y en Netflix, el 4K solo viene en el plan Premium, con unos 15 megas de internet.',
       'Si no le llega en 4K, tu tele estira la imagen y adivina los puntitos que faltan.',
       'Por eso, en el Buen Fin, no pagues de más por una 8K para verla desde el sillón.',
       'Para que el 4K se note, necesitas más pantalla o sentarte más cerca.',
       'Mándaselo a quien va a comprar tele en el Buen Fin.',
       'Porque su tele 4K… no la ve en 4K.']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-11_tele_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)

AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 50, 40)
GRIS = (150, 150, 160)
AZULC = (150, 210, 230)
RGB3 = [(255, 40, 40), (40, 255, 80), (60, 110, 255)]


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
    """Segundos desde el inicio de la frase i hasta su palabra k (con Scribe)."""
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


def texto(img, fx, x, y, txt, size, col, k=1.0, glow=0.45, f='sansx', anchor='mm'):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, k), anchor=anchor)
    ImageDraw.Draw(fx).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, glow * k), anchor=anchor)


def check(img, fx, x, y, k, txt, col=VERDE):
    pill(img, fx, x, y, '✓ ' + txt, eout(k), size=36, border=col)


def tache(img, fx, x, y, k, txt):
    pill(img, fx, x, y, '✗ ' + txt, eout(k), size=36, border=ROJO, col=(255, 200, 196))


def flat(m, glow=None):
    m.flat = True
    if glow is not None:
        m.glow = glow
    return m


# ================================================================== la imagen de la tele (procedural: atardecer)
_C = {}


def escena(w, h):
    """Atardecer con sol, montañas y lago (lo que se ve en la tele). np.float32 h×w×3 en 0..1."""
    key = ('esc', w, h)
    if key in _C:
        return _C[key]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = (x + 0.5) / w, (y + 0.5) / h
    c1, c2, c3 = np.array([18, 26, 92.]), np.array([196, 58, 128.]), np.array([255, 160, 60.])
    k1 = np.clip(v / 0.45, 0, 1)[..., None]
    k2 = np.clip((v - 0.45) / 0.2, 0, 1)[..., None]
    sky = c1 * (1 - k1) + c2 * k1
    sky = sky * (1 - k2) + c3 * k2
    d = np.hypot((u - 0.64) * 16 / 9, v - 0.5)
    sky += np.array([255, 220, 150.]) * np.exp(-d / 0.07)[..., None] * 0.7
    sol = np.clip(1 - d / 0.085, 0, 1) ** 0.3
    sky = sky * (1 - sol[..., None]) + np.array([255, 246, 200.]) * sol[..., None]
    img = sky
    r1 = 0.6 + 0.05 * np.sin(u * 9) + 0.025 * np.sin(u * 23 + 1)
    m1 = (v > r1)[..., None]
    img = np.where(m1, np.array([70, 30, 80.]), img)
    r2 = 0.68 + 0.045 * np.sin(u * 6 + 2) + 0.02 * np.sin(u * 31)
    m2 = (v > r2)[..., None]
    img = np.where(m2, np.array([30, 14, 44.]), img)
    lago = (v > 0.8)[..., None]
    vv = np.clip(1.6 - v, 0, 1)
    refl = (c3 * 0.8 + np.array([255, 220, 150.]) * np.exp(-np.abs(u - 0.64) / 0.05)[..., None] * 0.6) * \
        (0.55 + 0.45 * np.sin(v * 140)[..., None] ** 2) * vv[..., None]
    img = np.where(lago, refl * 0.8 + np.array([20, 20, 60.]) * 0.4, img)
    out = np.clip(img / 255.0, 0, 1).astype(np.float32)
    _C[key] = out
    return out


CW, CH = 384, 216                     # «pixeles» de la tele que se ven en el macro
MACRO = (172.5, 115.6)                  # punto del macro: el borde del sol (colores que cambian de pixel a pixel)


def decal_tele(estado='normal'):
    key = ('decal', estado)
    if key in _C:
        return _C[key]
    e = escena(CW, CH)
    im = Image.fromarray((e * 255).astype(np.uint8)).resize((CW * 4, CH * 4), Image.NEAREST)
    a = np.asarray(im, np.float32)
    a[::4, :, :] *= 0.7
    a[:, ::4, :] *= 0.7
    if estado == 'gris':
        g = a.mean(2, keepdims=True)
        a = a * 0.25 + g * 0.45
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    bz = 20
    out = Image.new('RGB', (CW * 4 + 2 * bz, CH * 4 + 2 * bz), (14, 14, 16))
    out.paste(im, (bz, bz))
    _C[key] = out.convert('RGBA')
    return _C[key]


PW = 2.3                               # ancho de la imagen (sin marco)
PH = PW * 9 / 16
BZ = PW * 20 / (CW * 4)
YP = 0.18                              # altura del borde de abajo del panel sobre la base


def tv(t=(0, 0, 0), s=1.0, ry=0.0, estado='normal', led=0.0):
    """Tele plana de pie sin marcas. Centro de la imagen en (0, YP + PH/2 + BZ, 0.031) antes de mover."""
    wtot, htot = PW + 2 * BZ, PH + 2 * BZ
    marco = named(M3.box(wtot, htot, 0.06, (34, 34, 38), shadow=0, base=True, gloss=0.6).tf(t=(0, YP, 0)), 'tele', rim=0.9, gloss=0.6)
    M3.decal(marco, marco.FACE['front'], decal_tele(estado))
    ms = [marco,
          named(M3.box(0.12, YP, 0.05, (40, 40, 44), shadow=0, base=True, gloss=0.5).tf(t=(0, 0, -0.035)), 'pie', rim=0.5),
          named(M3.box(0.8, 0.025, 0.32, (40, 40, 44), shadow=0, base=True, gloss=0.5), 'base', rim=0.5)]
    if led > 0.01:
        ms.append(flat(named(M3.box(0.03, 0.02, 0.01, ROJO, shadow=0, base=False).tf(t=(wtot / 2 - 0.1, YP + 0.02, 0.035)), 'led'),
                       glow=M.scale_c(ROJO, led)))
    return P.tfk(ms, s=s, ry=ry, t=t)


def centro_tv(t=(0, 0, 0), s=1.0):
    return np.array([t[0], t[1] + (YP + BZ + PH / 2) * s, t[2] + 0.031 * s])


def mueble(t=(0, 0, 0)):
    return P.tfk([named(M3.box(3.2, 0.5, 0.7, (96, 70, 50), shadow=0, base=True, gloss=0.25), 'mueble', rim=0.4)], t=t)


def sofa(t=(0, 0, 0), s=1.0, ry=180.0):
    return CG.sofa(t=t, s=s, ry=ry)


# ---------------------------------------------------------------- macro de subpixeles (2D)
def pix2d(Pz, cx, cy, t, aw=1.0):
    """Cuadro 1080×1920 con la imagen de la tele vista con zoom: cada pixel mide Pz px y se ven sus 3 subpixeles."""
    e = escena(CW, CH)
    xs = (np.arange(1080) - 540 + 0.5) / Pz + cx
    ys = (np.arange(1920) - 960 + 0.5) / Pz + cy
    ix, iy = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fxp, fyp = xs - ix, ys - iy
    vx = ((ix >= 0) & (ix < CW)).astype(np.float32)
    vy = ((iy >= 0) & (iy < CH)).astype(np.float32)
    col = e[iy.clip(0, CH - 1)[:, None], ix.clip(0, CW - 1)[None, :]]
    ksub = clamp((Pz - 4.0) / 14.0)
    if ksub > 0.01:
        sub = np.floor(fxp * 3).astype(int).clip(0, 2)
        sf = fxp * 3 - sub
        mx = np.clip(np.minimum(sf - 0.13, 0.87 - sf) * Pz * 0.6, 0, 1).astype(np.float32)
        my = np.clip(np.minimum(fyp - 0.05, 0.95 - fyp) * Pz * 0.4, 0, 1).astype(np.float32)
        ch = np.zeros((1080, 3), np.float32)
        ch[np.arange(1080), sub] = 1.0
        brillo = 0.93 + 0.07 * np.sin(t * 17 + ix * 1.7)[None, :, None]
        st = col * ch[None] * mx[None, :, None] * my[:, None, None] * 1.75 * brillo
        img = st * ksub + col * (1 - ksub)
    else:
        img = col
    img = img * (vx[None, :, None] * vy[:, None, None]) * aw
    a8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(a8)
    small = im.resize((270, 480), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5 if Pz > 20 else 3)).resize((1080, 1920), Image.BILINEAR)
    o = a8.astype(np.float32) + np.asarray(small, np.float32) * (0.9 if Pz > 20 else 0.35)
    o = o * M._vig()
    return np.clip(o, 0, 255).astype(np.uint8)


def acabar_2d(o, fi, ui=None):
    im = Image.fromarray(o)
    fx = Image.new('RGB', im.size, (0, 0, 0))
    if ui:
        ui(im, fx)
    a = np.asarray(im, np.float32) + np.asarray(fx.filter(ImageFilter.GaussianBlur(6)), np.float32) * 0.8
    a = a / 255.0 + M._grain(fi) * 0.04
    return (np.clip(a, 0, 1) * 255).astype(np.uint8)


# ---------------------------------------------------------------- piezas de línea que brillan
def ojo3d(fr, c, r=0.32, mira=(0, 0, -1), k=1.0, t=0.0, pupila=1.0):
    """Ojo de alambre que brilla (esfera + iris cian + pupila), mirando hacia `mira`."""
    if k <= 0.01:
        return
    C = np.array(c, float)
    ax = M.norm(mira)
    up = np.array([0, 1.0, 0]) if abs(ax[1]) < 0.9 else np.array([1.0, 0, 0])
    e1 = M.norm(np.cross(ax, up))
    e2 = np.cross(ax, e1)
    th = np.linspace(0, 2 * math.pi, 56)
    for lat in (-55, -25, 0, 25, 55):
        a = math.radians(lat)
        rr, off = r * math.cos(a), r * math.sin(a)
        line3(fr, [C + e2 * off + (e1 * math.cos(q) + ax * math.sin(q)) * rr for q in th], col=WHITE, w=1.5, a=0.4 * k, glow=0.35)
    for lon in range(0, 180, 36):
        b = math.radians(lon + t * 25)
        d1 = e1 * math.cos(b) + ax * math.sin(b)
        line3(fr, [C + (e2 * math.cos(q) + d1 * math.sin(q)) * r for q in th], col=WHITE, w=1.5, a=0.3 * k, glow=0.3)
    for rr, col, w in ((0.5 * r, CYAN, 4.0), (0.22 * r * pupila, WHITE, 3.0)):
        z = math.sqrt(max(0.0, r * r - rr * rr))
        line3(fr, [C + ax * z + (e1 * math.cos(q) + e2 * math.sin(q)) * rr for q in th], col=col, w=w, a=k, glow=1.0)
    dot3(fr, C + ax * r, r=7, col=(230, 245, 255), a=k, glow=1.0)


def cota(fr, a, b, txt, img_ui, k=1.0, col=AMARILLO, h=0.0):
    """Línea de medida en 3D con topes; devuelve la posición 2D del centro para poner la etiqueta."""
    if k <= 0.01:
        return None
    a, b = np.asarray(a, float), np.asarray(b, float)
    bb = a + (b - a) * eout(k)
    line3(fr, [a, bb], col=col, w=3, a=1.0, glow=0.8)
    for p in (a, bb):
        line3(fr, [p + np.array([0, -0.08, 0]), p + np.array([0, 0.08, 0])], col=col, w=3, a=1.0, glow=0.8)
    return fr.cam.p1((a + bb) / 2 + np.array([0, h, 0]))


def tile(x, y, z, w, h, col, g=0.32, name='tile'):
    m = M3.box(w, h, 0.02, col, shadow=0, base=False).tf(t=(x, y, z))
    m = named(m, name)
    return flat(m, glow=M.scale_c(col, g))


def rejilla(fr, c, nx, ny, paso, t, a=1.0, r=3.2, frente=(0, 0, 1), onda=0.0):
    """Pared de subpixeles RGB que brillan (proyección en lote, rápido)."""
    C = np.array(c, float)
    ax = M.norm(frente)
    e1 = M.norm(np.cross(np.array([0, 1.0, 0]), ax))
    e2 = np.cross(ax, e1)
    pts, cols = [], []
    e = escena(nx, ny)
    for j in range(ny):
        for i in range(nx):
            base = C + e1 * (i - nx / 2) * paso - e2 * (j - ny / 2) * paso
            for s in range(3):
                pts.append(base + e1 * (s - 1) * paso * 0.28)
                cols.append(float(e[j, i, s]))
    S, Z = fr.cam.proj(np.array(pts))
    F = fr.cam.F
    for (x, y), z, v, s in zip(S, Z, cols, range(len(cols))):
        if z < 0.2:
            continue
        c3 = RGB3[s % 3]
        kk = min(1.4, a * (0.3 + 0.9 * v) * (1 + onda * math.sin(t * 8 - z * 3)))
        q = F * paso / max(0.3, z)
        fr.db.rectangle((x - q * 0.1, y - q * 0.42, x + q * 0.1, y + q * 0.42), fill=M.scale_c(c3, kk))
        fr.df.rectangle((x - q * 0.14, y - q * 0.46, x + q * 0.14, y + q * 0.46), fill=M.scale_c(c3, kk * 0.5))


def recorte(res, x0, y0, n):
    """Pedazo cuadrado de la imagen de la tele (alrededor del sol) a resolución res×(res·9/16): n pixeles de lado."""
    e = escena(res, res * 9 // 16)
    ix, iy = int(x0 * res), int(y0 * res * 9 // 16)
    return e[iy:iy + n, ix:ix + n]


def panel(img, fx, x, y, tam, res_px, etiqueta, k=1.0, col=WHITE, borde=CYAN):
    """Cuadro 2D con un pedazo de la imagen: res_px pixeles por lado (pocos = se ven los cuadritos)."""
    if k <= 0.01:
        return
    e = recorte(384 * res_px // 12, 0.6, 0.53, res_px)
    im = Image.fromarray((e * 255).astype(np.uint8)).resize((int(tam), int(tam)), Image.NEAREST)
    s = 0.6 + 0.4 * eout(k)
    tt = max(2, int(tam * s))
    im = im.resize((tt, tt), Image.NEAREST)
    img.paste(im, (int(x - tt / 2), int(y - tt / 2)))
    d = ImageDraw.Draw(img)
    d.rectangle((x - tt / 2 - 3, y - tt / 2 - 3, x + tt / 2 + 3, y + tt / 2 + 3), outline=M.scale_c(borde, k), width=4)
    ImageDraw.Draw(fx).rectangle((x - tt / 2 - 3, y - tt / 2 - 3, x + tt / 2 + 3, y + tt / 2 + 3), outline=M.scale_c(borde, 0.5 * k), width=10)
    M.kicker(img, etiqueta, int(y + tt / 2 + 34), k, col=col, size=28, cx=x)


# ================================================================== escenas
# 0. gancho · inicio tipo 7: macro de subpixeles → la imagen → la tele → la sala desde el sillón («4K» de cristal detrás)
#    u < 0 (final en loop): la sala y la cámara se clava en la pantalla hasta los subpixeles.
U_IN, U_2D, U_3D = -1.05, -0.62, -0.45        # loop: vuela a la pantalla · entra al macro · macro quieto
U_SAL, U_PB = 0.0, 0.5                          # sale del macro (2D) · se aleja en 3D
P_MAX = 300.0
P_FULL = 1080.0 / CW


def _cam_sala(u):
    """Cámara 0 = de frente a la pantalla (la imagen llena el ancho) · 1 = desde atrás del sillón."""
    c = centro_tv((0, 0.5, 0))
    if u >= U_PB:
        k = P.eout4(seg(u, U_PB, U_PB + 0.55))
        drift = 2.5 * math.sin(u * 0.9) * seg(u, U_PB + 0.5, U_PB + 1.2)
    else:
        k = 1 - M.ein(seg(u, U_IN, U_2D), 3)
        drift = 0
    tgt = (lerp(c[0], 0.0, k), lerp(c[1], 1.05, k), lerp(c[2], 0.4, k))
    return Cam(target=tgt, dist=lerp(1.5 * PW, 7.4, k), yaw=lerp(0, -20, k) + drift, pitch=lerp(0, 9, k), cy=lerp(0.5, 0.6, k))


def _sala3d(t, fi, u):
    fr = Frame(_cam_sala(u))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.35)
    M.cristal(fr.base, fr.fx, '4K', u, t0=-3.6, cy=0.36, entrada='golpe')
    draw_objects(fr, mueble() + tv(t=(0, 0.5, 0), led=0.0) + sofa(t=(0.0, 0, 4.4)))

    def ui(img, fx):
        if u > 0:
            kicker(img, 'TELE 4K · 43 PULGADAS', 150, seg(u, 0.7, 1.0), col=AZULC)
            P.titulo_golpe(img, fx, [('Tu tele 4K…', 'sans'), ('no la ves en 4K.', 'serif')], 200, seg(u, 0.92, 1.07), size=80)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if U_PB <= u < U_PB + 0.3:
        out = M.radial_blur(out, 0.12 * (1 - seg(u, U_PB, U_PB + 0.3)), 0.5, 0.5)
    if U_IN + 0.15 <= u < U_2D:
        out = M.radial_blur(out, 0.14 * seg(u, U_IN + 0.15, U_2D), 0.5, 0.5)
    return out


def s_gancho(t, fi, u, d):
    if U_2D <= u < U_PB:                        # 2D: subpixeles
        if u < U_3D:
            kz = M.ein(seg(u, U_2D, U_3D), 2)
        elif u < U_SAL:
            kz = 1.0
        else:
            kz = 1 - P.eout4(seg(u, U_SAL, U_PB))
        Pz = math.exp(lerp(math.log(P_FULL), math.log(P_MAX), kz))
        cx = lerp(CW / 2, MACRO[0], kz ** 0.35)
        cy = lerp(CH / 2, MACRO[1], kz ** 0.35)
        o = pix2d(Pz, cx, cy, t)

        def ui(img, fx):
            if u >= U_3D - 0.05 and u < U_SAL + 0.25:
                M.kicker(img, 'PIXEL · ROJO · VERDE · AZUL', 1380, 1.0, col=AZULC, size=28)
        out = acabar_2d(o, fi, ui)
        return sacudir(out, t, golpe_k(u, U_3D, 0.25), amp=16)
    out = _sala3d(t, fi, u)
    return sacudir(out, t, golpe_k(u, 1.07, 0.35), amp=24)


# 1. más de 8 millones de puntitos (pared de subpixeles con contador) → 4 veces más que una Full HD (1 cuadro contra 4)
def s_8m(t, fi, u, d):
    u4 = wt(1, 9) - 0.12                         # «cuatro veces»
    if u < u4:
        fr = Frame(cam(u, [K(-0.3, 2.2, -38, 14, ty=1.0), K(0.3, 3.0, -8, 6, ty=1.0), K(u4, 3.3, 12, 4, ty=1.0)], cy=0.55))
        space(fr, t, floor=None, bokeh=0.8)
        rejilla(fr, (0, 1.0, 0), 26, 15, 0.16, t, a=1.0, onda=0.15)
        n = int(8294400 * P.eout4(seg(u, 0.0, wt(1, 4) + 0.2)))

        def ui(img, fx):
            kicker(img, 'PUNTITOS DE LUZ · 3 840 × 2 160', 150, seg(u, -0.1, 0.2), col=AZULC)
            P.numero_golpe(img, fx, f'{n:,}'.replace(',', ' '), 470, seg(u, 0.0, 0.18), size=150, col=WHITE)
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, wt(1, 4) + 0.2, 0.3), amp=14)
    v = u - u4
    fr = Frame(cam(v, [K(-0.2, 3.6, 40, 16, ty=0.9), K(0.3, 3.4, 10, 8, ty=0.9), K(3.0, 3.3, 4, 8, ty=0.9)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)
    e1 = P.entrada(v, 0.0, 0.25, 'pop')
    e2 = P.entrada(v, 0.18, 0.25, 'pop')
    sun = (240, 130, 50)
    ms = [tile(-0.85, 0.9, 0, 1.0 * max(0.05, e1['escala']), 1.0 * max(0.05, e1['escala']), sun)]
    tonos = [(250, 170, 70), (236, 110, 50), (214, 80, 70), (255, 214, 120)]
    for j in range(4):
        sx = 0.85 + (0.255 if j % 2 else -0.255)
        sy = 0.9 + (0.255 if j < 2 else -0.255)
        q = 0.48 * max(0.05, e2['escala'])
        ms.append(tile(sx, sy, 0, q, q, tonos[j]))
    draw_objects(fr, ms)
    pa, pb = fr.cam.p1((-0.85, 1.55, 0)), fr.cam.p1((0.85, 1.55, 0))

    def ui(img, fx):
        kicker(img, 'EL MISMO PEDACITO DE PANTALLA', 150, seg(v, -0.1, 0.2), col=AZULC)
        pill(img, fx, pa[0], pa[1] - 30, 'FULL HD · 1', eout(seg(v, 0.1, 0.35)), size=30, border=GRIS, dot=False)
        pill(img, fx, pb[0], pb[1] - 30, '4K · 4', eout(seg(v, 0.3, 0.55)), size=30, border=CYAN, dot=False)
        P.numero_golpe(img, fx, '×4', 1280, seg(v, 0.5, 0.68), size=220, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.68, 0.3), amp=18)


# 2. tu ojo tiene un límite (ojo de alambre que hace pop) → 94 puntitos por grado (cono de 1° con una fila de puntos)
def s_ojo(t, fi, u, d):
    u94 = wt(2, 11) - 0.15                       # «unos noventa y cuatro»
    fr = Frame(cam(u, [K(-0.3, 2.0, 50, 10, ty=1.0, tx=-0.9), K(0.3, 2.5, 22, 6, ty=1.0, tx=-0.9),
                       K(u94, 5.6, -8, 10, ty=1.0, tx=0.3), K(6.0, 5.55, -12, 10, ty=1.0, tx=0.3)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    if u >= u94:
        M.cristal(fr.base, fr.fx, '94', u, t0=u94 + 0.1, cy=0.33, entrada='zoom')
    e = P.entrada(u, -0.25, 0.3, 'pop')
    C0 = np.array([-1.0, 1.0, 0.0])
    ojo3d(fr, C0, r=0.5 * max(0.05, e['escala']), mira=(1, 0, 0), t=t)
    kc = seg(u, u94 - 0.3, u94 + 0.3)
    if kc > 0:
        tip = C0 + np.array([0.5, 0, 0])
        far = np.array([1.6, 1.0, 0.0])
        a1, a2 = far + np.array([0, 0.52, 0]), far + np.array([0, -0.52, 0])
        line3(fr, [tip, tip + (a1 - tip) * eout(kc)], col=CYAN, w=2.5, a=0.9, glow=0.8)
        line3(fr, [tip, tip + (a2 - tip) * eout(kc)], col=CYAN, w=2.5, a=0.9, glow=0.8)
        n = int(94 * P.eout4(seg(u, u94, u94 + 0.9)))
        for i in range(n):
            yy = 0.5 - i * (1.04 / 93)
            dot3(fr, far + np.array([0, yy, 0]), r=3.4, col=RGB3[i % 3], a=1.0, glow=1.2)
    pg = fr.cam.p1(C0 + np.array([0.9, 0, 0]))

    def ui(img, fx):
        kicker(img, 'TU OJO TIENE UN LÍMITE', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > wt(2, 6) - 0.1:
            kicker(img, 'UNIVERSIDAD DE CAMBRIDGE · 2025', 205, seg(u, wt(2, 6) - 0.1, wt(2, 6) + 0.2), col=GRIS, size=24)
        if u > u94 + 0.2:
            pill(img, fx, 540, 1400, '94 PUNTITOS POR GRADO', eout(seg(u, u94 + 0.2, u94 + 0.5)), size=34, border=CYAN, dot=False)
            texto(img, fx, pg[0], pg[1] - 70, '1°', 54, AMARILLO, seg(u, u94, u94 + 0.3))
            M.kicker(img, 'ESCALA EXAGERADA', 1470, seg(u, u94 + 0.4, u94 + 0.7), col=GRIS, size=22)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u94 + 0.42, 0.3), amp=14)


# 3 y 4. la prueba en dos casos: la misma tele de 43" a 1.5 m (se nota) y a 3 m (ya no)
TV43 = 0.95 / PW                              # escala real: 43" mide 0.95 m de ancho


def _sala_medida(fr, t, dist_ojo, k_ojo, sofa_k=0.0):
    draw_objects(fr, tv(t=(0, 0.55, 0), s=TV43) + P.tfk([named(M3.box(1.0, 0.55, 0.38, (78, 56, 40), shadow=0, base=True, gloss=0.25),
                                                                  'mueble', rim=0.4)]) +
                 (sofa(t=(0, 0, dist_ojo + 0.55), s=0.6) if sofa_k > 0.01 else []))
    ojo3d(fr, (0, 1.12, dist_ojo), r=0.16, mira=(0, 0, -1), k=k_ojo, t=t)


def s_cerca(t, fi, u, d):
    un = wt(3, 12) - 0.12                        # «el cuatro K sí se nota»
    fr = Frame(cam(u, [K(-0.3, 5.6, 78, 34, ty=0.7, tz=0.75), K(0.3, 4.8, 60, 28, ty=0.7, tz=0.75),
                       K(un, 3.0, 30, 14, ty=1.0, tz=0.4), K(5.0, 2.9, 26, 14, ty=1.0, tz=0.4)], cy=0.4))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    e = P.entrada(u, -0.1, 0.28, 'desliza')
    zo = 1.5 + e['dy'] * 0.4
    _sala_medida(fr, t, zo, 1.0)
    pc = cota(fr, (0.62, 0.02, 0.04), (0.62, 0.02, zo), '1.5 m', None, k=seg(u, 0.15, 0.5), h=0.1)
    ctv = fr.cam.p1(centro_tv((0, 0.55, 0), TV43))

    def ui(img, fx):
        kicker(img, 'CASO 1 · TELE DE 43" A 1.5 m', 150, seg(u, -0.1, 0.2), col=AZULC)
        if pc:
            pill(img, fx, pc[0], pc[1] - 40, '1.5 m', eout(seg(u, 0.3, 0.55)), size=34, border=AMARILLO, dot=False)
        if u > un:
            k = seg(u, un, un + 0.3)
            panel(img, fx, 300, 1120, 300, 12, 'FULL HD', k, borde=GRIS)
            panel(img, fx, 780, 1120, 300, 24, '4K', k, borde=CYAN)
            check(img, fx, 540, 1420, seg(u, un + 0.3, un + 0.55), 'SÍ SE NOTA')
            doodle_circle(img, fx, 780, 1120, 190, 190, t, k=eout(seg(u, un + 0.5, un + 0.9)), col=AMARILLO, w=5)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u > un - 0.05:
        z = 1.0 + 0.25 * P.eout4(seg(u, un - 0.05, un + 0.2))
        out = M.scale_about(out, z, ctv[0] / 1080, ctv[1] / 1920)
        im = Image.fromarray(out)
        rec_frame(im, t, 1.0, zoom_label=f'x{z:.2f}')
        out = np.asarray(im)
    return sacudir(out, t, golpe_k(u, un + 0.2, 0.25), amp=12)


def s_lejos(t, fi, u, d):
    u3 = wt(4, 5) - 0.15                         # «tres metros»
    ud = wt(4, 9) - 0.12                         # «ya no la distingue»
    zo = 1.5 + 1.5 * P.eout4(seg(u, 0.0, 0.55))
    fr = Frame(cam(u, [K(-0.3, 3.0, -30, 20, ty=0.9, tz=1.2), K(0.3, 5.6, -58, 26, ty=0.9, tz=1.6),
                       K(ud, 5.2, -40, 18, ty=1.0, tz=1.5), K(5.0, 5.1, -36, 18, ty=1.0, tz=1.5)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.3)
    if u >= u3:
        M.cristal(fr.base, fr.fx, '3 METROS', u, t0=u3, cy=0.3, alto=0.2, entrada='sube')
    _sala_medida(fr, t, zo, 1.0, sofa_k=1.0)
    pc = cota(fr, (-0.62, 0.02, 0.04), (-0.62, 0.02, zo), '3 m', None, k=seg(u, 0.0, 0.55), h=0.1)

    def ui(img, fx):
        kicker(img, 'CASO 2 · LA MISMA TELE A 3 m', 150, seg(u, -0.1, 0.2), col=AZULC)
        if pc:
            pill(img, fx, pc[0], pc[1] - 40, '3 m', eout(seg(u, 0.3, 0.55)), size=34, border=AMARILLO, dot=False)
        if u > ud:
            k = seg(u, ud, ud + 0.3)
            tam = 300 - 230 * P.eout4(seg(u, ud + 0.2, ud + 0.8))
            panel(img, fx, 380, 1150, tam, 12, 'FULL HD', k, borde=GRIS)
            panel(img, fx, 700, 1150, tam, 24, '4K', k, borde=CYAN)
            texto(img, fx, 540, 1150, '=', 90, WHITE, seg(u, ud + 0.7, ud + 0.9))
            pill(img, fx, 540, 1420, 'SE VEN IGUAL', eout(seg(u, ud + 0.8, ud + 1.05)), size=36, border=GRIS, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u3 + 0.3, 0.3), amp=14)


# 5. los puntitos son tan chiquitos que tu ojo los junta (4 subpixeles que vuelan al ojo y se funden en uno)
def s_junta(t, fi, u, d):
    uj = wt(5, 8) - 0.1                          # «los junta»
    fr = Frame(cam(u, [K(-0.3, 2.4, 60, 12, ty=1.0), K(0.3, 3.0, 20, 6, ty=1.0), K(uj, 2.7, -8, 6, ty=1.0), K(4.0, 2.65, -12, 6, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0)
    k = ease(seg(u, 0.25, uj + 0.25))
    ojo = np.array([1.1, 1.0, 0.0])
    ojo3d(fr, ojo, r=0.5, mira=(-1, 0, 0), t=t)
    tonos = [(250, 170, 70), (236, 110, 50), (214, 80, 70), (255, 214, 120)]
    ms = []
    for j in range(4):
        sx = (0.34 if j % 2 else -0.34) * (1 - k)
        sy = (0.34 if j < 2 else -0.34) * (1 - k)
        x = lerp(-0.9, 0.35, k)
        q = lerp(0.62, 0.12, k)
        col = M.mixc(tonos[j], (240, 140, 70), k)
        ms.append(tile(x + sx, 1.0 + sy, 0, q, q, col, g=0.45))
    draw_objects(fr, ms)
    for i in range(3):
        a = np.array([lerp(-0.9, 0.35, k), 1.0 + 0.3 * (i - 1) * (1 - k), 0])
        line3(fr, [a, ojo + np.array([-0.5, 0, 0])], col=WHITE, w=1.5, a=0.5 * seg(u, 0.0, 0.3), glow=0.6)

    def ui(img, fx):
        kicker(img, 'TAN CHIQUITOS…', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > uj:
            pill(img, fx, 540, 1400, 'TU OJO LOS JUNTA EN UNO', eout(seg(u, uj, uj + 0.3)), size=34, border=CYAN, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uj + 0.25, 0.3), amp=14)


# 6. segundo gancho: lo peor → mucho de lo que ves ni siquiera viene en 4K (la etiqueta «4K» de la pantalla se tacha)
def s_peor(t, fi, u, d):
    un = wt(6, 10) - 0.12                        # «ni siquiera viene en cuatro K»
    fr = Frame(cam(u, [K(-0.3, 2.4, 28, 4, ty=1.35), K(0.25, 3.3, -6, 2, ty=1.35), K(un, 3.0, 10, 4, ty=1.35), K(5.0, 2.95, 14, 4, ty=1.35)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.4)
    gris = u > un + 0.1
    draw_objects(fr, mueble() + tv(t=(0, 0.5, 0), estado='gris' if gris else 'normal'))
    ct = fr.cam.p1(centro_tv((0, 0.5, 0)))

    def ui(img, fx):
        kicker(img, '¡LO PEOR!', 150, seg(u, -0.1, 0.1), col=ROJO, size=36)
        k4 = eout(seg(u, 0.2, 0.45))
        if k4 > 0.01:
            pill(img, fx, ct[0], ct[1] - 40, '4K', k4, size=70, border=CYAN, dot=False)
        if u > un:
            doodle_arrow(img, fx, ct[0] - 120, ct[1] - 10, ct[0] + 120, ct[1] - 70, t, k=eout(seg(u, un, un + 0.3)), col=ROJO, w=9)
            tache(img, fx, 540, 1400, seg(u, un + 0.3, un + 0.55), 'NI SIQUIERA VIENE EN 4K')
    fr.ui.append(ui)
    out = finish(fr, fi)
    if un <= u < un + 0.18:
        out = M.tr_glitch(out, out, 0.5, fi)
    return sacudir(out, t, golpe_k(u, -0.05, 0.4) + golpe_k(u, un + 0.1, 0.3), amp=24)


# 7. la tele abierta en México llega, cuando mucho, en HD (antena de techo con ondas que llegan a la tele + «HD» de cristal)
def antena(fr, base, t, k=1.0):
    B = np.array(base, float)
    line3(fr, [B, B + np.array([0, 1.6, 0])], col=WHITE, w=6, a=k, glow=0.7)
    line3(fr, [B + np.array([-1.1, 1.6, 0]), B + np.array([1.1, 1.6, 0])], col=WHITE, w=6, a=k, glow=0.7)
    for i in range(9):
        x = -1.0 + i * 0.25
        h = 0.62 - abs(i - 4) * 0.07
        line3(fr, [B + np.array([x, 1.6, -h]), B + np.array([x, 1.6, h])], col=WHITE, w=4.5, a=k, glow=0.7)
    dot3(fr, B + np.array([0, 1.6, 0]), r=9, col=CYAN, a=k, glow=1.2)


def s_abierta(t, fi, u, d):
    uh = wt(7, 8) - 0.15                         # «en alta definición»
    fr = Frame(cam(u, [K(-0.3, 5.0, -50, 20, ty=1.4, tx=-0.2), K(0.3, 6.0, -22, 12, ty=1.4, tx=-0.2), K(uh, 5.8, 6, 10, ty=1.4, tx=-0.2),
                       K(5.0, 5.7, 10, 10, ty=1.4, tx=-0.2)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    if u >= uh - 0.1:
        M.cristal(fr.base, fr.fx, 'HD', u, t0=uh - 0.05, cy=0.32, entrada='golpe')
    e = P.entrada(u, -0.2, 0.3, 'cae')
    antena(fr, (-1.3, 1.1 - e['dy'] * 0.4, -0.5), t)
    draw_objects(fr, tv(t=(0.55, 0, 0.2), s=0.75, ry=-12))
    for j in range(5):                          # ondas que viajan de la antena a la tele
        ph = (t * 0.9 + j / 5) % 1.0
        c = np.array([lerp(-1.3, 0.5, ph), 2.7 - 1.5 * ph, lerp(-0.5, 0.2, ph)])
        th = np.linspace(-0.9, 0.9, 20)
        r = 0.25 + 0.15 * ph
        line3(fr, [c + np.array([r * math.sin(a) * 0.4, r * math.cos(a), r * math.sin(a)]) for a in th], col=CYAN, w=4,
              a=0.9 * (1 - ph) * seg(u, 0.0, 0.3), glow=1.0)
    pt = fr.cam.p1((0.55, 1.6, 0.2))

    def ui(img, fx):
        kicker(img, 'TV ABIERTA EN MÉXICO · ATSC 1.0', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > uh:
            pill(img, fx, pt[0], pt[1] - 40, '720p · 1080i', eout(seg(u, uh, uh + 0.3)), size=32, border=CYAN, dot=False)
            tache(img, fx, 540, 1400, seg(u, uh + 0.35, uh + 0.6), 'NO LLEGA EN 4K')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uh + 0.3, 0.3), amp=16)


# 8. en Netflix el 4K solo viene en Premium (3 tarjetas que caen) → con unos 15 megas de internet (medidor)
def _tarjeta_img(titulo, res, hi):
    def dib(d, im):
        w, h = im.size
        d.rectangle((0, 0, w, h), fill=(16, 18, 24) if not hi else (10, 30, 40))
        d.text((w / 2, 70), titulo, font=M.font('sans', 46), fill=(240, 240, 244), anchor='mm')
        d.text((w / 2, 170), res, font=M.font('sansx', 110), fill=(120, 225, 255) if hi else (160, 160, 170), anchor='mm')
        if hi:
            e = escena(4, 4)
            th = Image.fromarray((e * 255).astype(np.uint8)).resize((140, 140), Image.NEAREST)
            im.paste(th, (int(w / 2 - 70), 250))
        d.rectangle((2, 2, w - 3, h - 3), outline=(120, 225, 255) if hi else (90, 90, 100), width=5)
    key = ('tarj', titulo, res, hi)
    if key not in _C:
        im = Image.new('RGB', (420, 420), (0, 0, 0))
        dib(ImageDraw.Draw(im), im)
        _C[key] = im.convert('RGBA')
    return _C[key]


def tarjeta(titulo, res, hi, t=(0, 0, 0), ry=0.0):
    m = named(M3.box(1.0, 1.0, 0.03, (16, 18, 24), shadow=0, base=False, gloss=0.4), 'tarjeta', rim=0.6)
    M3.decal(m, m.FACE['front'], _tarjeta_img(titulo, res, hi))
    if hi:
        m.glow = (8, 30, 40)
    return P.tfk([m], ry=ry, t=t)


def s_netflix(t, fi, u, d):
    up = wt(8, 11) - 0.12                        # «Premium»
    u15 = wt(8, 13) - 0.15                       # «quince megas»
    fr = Frame(cam(u, [K(-0.3, 4.0, 30, 16, ty=1.0), K(0.3, 4.4, 6, 8, ty=1.0), K(up, 3.6, -4, 6, ty=1.0, tx=1.1),
                       K(u15, 4.6, -18, 10, ty=1.2), K(6.0, 4.5, -22, 10, ty=1.2)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.3)
    ms = []
    defs = [('ESTÁNDAR CON ANUNCIOS', '1080p', False), ('ESTÁNDAR', '1080p', False), ('PREMIUM', '4K', True)]
    for i, (a, b, hi) in enumerate(defs):
        e = P.entrada(u, -0.2 + 0.16 * i, 0.28, 'cae')
        if u > -0.25 + 0.16 * i:
            ms += tarjeta(a, b, hi, t=(-1.15 + 1.15 * i, 1.0 - e['dy'] * 0.5 + (0.15 if hi and u > up else 0), 0.25 if hi else 0),
                          ry=6 * (i - 1))
    draw_objects(fr, ms)
    pp = fr.cam.p1((1.15, 1.75, 0.25))
    vel = 15 * P.eout4(seg(u, u15 - 0.2, u15 + 0.5))

    def ui(img, fx):
        kicker(img, 'NETFLIX · PLANES', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > up:
            doodle_circle(img, fx, pp[0], pp[1] + 120, 200, 200, t, k=eout(seg(u, up, up + 0.4)), col=AMARILLO, w=6)
        if u > u15 - 0.3:
            k = seg(u, u15 - 0.3, u15)
            cx, cy, r = 540, 1300, 150
            dd = ImageDraw.Draw(img)
            dd.arc((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=M.scale_c((200, 200, 210), k), width=8)
            a = math.radians(180 + 180 * vel / 25)
            dd.line([(cx, cy), (cx + (r - 20) * math.cos(a), cy + (r - 20) * math.sin(a))], fill=M.scale_c(CYAN, k), width=8)
            ImageDraw.Draw(fx).line([(cx, cy), (cx + (r - 20) * math.cos(a), cy + (r - 20) * math.sin(a))], fill=M.scale_c(CYAN, 0.6 * k), width=18)
            texto(img, fx, cx, cy + 60, f'{vel:.0f} Mbps', 64, WHITE, k)
            M.kicker(img, 'VELOCIDAD RECOMENDADA PARA 4K', cy + 120, k, col=GRIS, size=24)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.1, 0.25) + golpe_k(u, u15 + 0.5, 0.25), amp=12)


# 9. tu tele estira la imagen y adivina los puntitos que faltan (la miniatura 4×4 de la tarjeta se vuelve una rejilla de 8×8)
def s_estira(t, fi, u, d):
    ue = wt(9, 7) - 0.12                         # «tu tele estira la imagen»
    ua = wt(9, 13) - 0.12                        # «adivina los puntitos»
    fr = Frame(cam(u, [K(-0.3, 2.2, 0, 4, ty=1.0), K(0.3, 3.0, 24, 10, ty=1.0), K(ua, 3.4, -20, 8, ty=1.0), K(5.0, 3.35, -24, 8, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0)
    ks = P.eout4(seg(u, ue, ue + 0.4))
    lado = lerp(0.8, 1.9, ks)
    e4, e8 = escena(4, 4), escena(8, 8)
    ms = []
    for j in range(8):
        for i in range(8):
            q = lado / 8
            x = -lado / 2 + (i + 0.5) * q
            y = 1.0 + lado / 2 - (j + 0.5) * q
            orig = (i % 2 == 0 and j % 2 == 0)
            if orig:
                col = tuple(int(v * 255) for v in e4[j // 2, i // 2])
                ms.append(tile(x, y, 0, q * 0.92, q * 0.92, col, g=0.5))
            else:
                kk = seg(u, ua + 0.03 * (i + j), ua + 0.03 * (i + j) + 0.2)
                if u > ue + 0.3:
                    col = tuple(int(v * 255) for v in e8[j, i]) if kk > 0.5 else (40, 40, 48)
                    ms.append(tile(x, y, 0, q * 0.92 * (0.6 + 0.4 * eout(kk)) if kk > 0 else q * 0.5, q * 0.92 * (0.6 + 0.4 * eout(kk)) if kk > 0 else q * 0.5,
                                   col, g=0.5 if kk > 0.5 else 0.1))
    draw_objects(fr, ms)
    qs = []
    if ue + 0.3 < u < ua + 0.4:
        for j in range(8):
            for i in range(8):
                if not (i % 2 == 0 and j % 2 == 0):
                    q = lado / 8
                    qs.append(fr.cam.p1((-lado / 2 + (i + 0.5) * q, 1.0 + lado / 2 - (j + 0.5) * q, 0.02)))

    def ui(img, fx):
        kicker(img, 'REESCALADO', 150, seg(u, -0.1, 0.2), col=AZULC)
        for (x, y, _) in qs:
            texto(img, fx, x, y, '?', 34, AMARILLO, seg(u, ue + 0.3, ue + 0.5), glow=0.3, f='sans')
        if u > ua:
            pill(img, fx, 540, 1400, 'PUNTITOS INVENTADOS', eout(seg(u, ua + 0.3, ua + 0.55)), size=34, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ue + 0.4, 0.25), amp=12)


# 10. Buen Fin: no pagues de más por una 8K para verla desde el sillón (etiqueta de precio tachada → la sala desde lejos)
def s_8k(t, fi, u, d):
    un = wt(10, 6) - 0.12                        # «no pagues de más»
    us = wt(10, 14) - 0.12                       # «para verla desde el sillón»
    if u < us:
        fr = Frame(cam(u, [K(-0.3, 3.2, 30, 6, ty=1.3), K(0.3, 3.8, 8, 4, ty=1.3), K(un, 3.5, -10, 4, ty=1.3), K(us, 3.45, -14, 4, ty=1.3)], cy=0.52))
        space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
        draw_objects(fr, mueble() + tv(t=(0, 0.5, 0)))
        ct = fr.cam.p1(centro_tv((0, 0.5, 0)) + np.array([PW * 0.42, PH * 0.5, 0]))

        def ui(img, fx):
            kicker(img, 'BUEN FIN · 13 AL 17 DE NOVIEMBRE', 150, seg(u, -0.1, 0.2), col=AMARILLO)
            k = eout(seg(u, 0.05, 0.3))
            if k > 0.01:
                sw = 4 * math.sin(t * 3)
                x, y = ct[0] - 40, ct[1] + 40 + sw
                dd = ImageDraw.Draw(img)
                dd.line([(ct[0], ct[1] - 60), (x, y - 70)], fill=(220, 220, 220), width=3)
                dd.rounded_rectangle((x - 130, y - 70, x + 130, y + 90), radius=18, fill=M.scale_c((250, 236, 170), k))
                dd.text((x, y - 15), '8K', font=M.font('sansx', 70), fill=(30, 30, 30), anchor='mm')
                dd.text((x, y + 50), '$ $ $', font=M.font('sans', 40), fill=(170, 40, 30), anchor='mm')
            if u > un:
                doodle_arrow(img, fx, ct[0] - 200, ct[1] + 120, ct[0] + 120, ct[1] - 40, t, k=eout(seg(u, un, un + 0.3)), col=ROJO, w=10)
                tache(img, fx, 540, 1400, seg(u, un + 0.2, un + 0.45), 'NO PAGUES DE MÁS')
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.3, 0.3), amp=16)
    v = u - us
    k = P.eout4(seg(v, 0.0, 0.5))
    fr = Frame(Cam(target=(0, 1.1, 1.0), dist=lerp(3.4, 8.2, k), yaw=lerp(-14, 160, 0) + lerp(0, -18, k), pitch=lerp(4, 12, k), cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    draw_objects(fr, mueble() + tv(t=(0, 0.5, 0)) + sofa(t=(0.0, 0, 4.4)))
    out = finish(fr, fi)
    if k < 0.95:
        out = M.radial_blur(out, 0.14 * (1 - k), 0.5, 0.45)
    im = Image.fromarray(out)
    fx = Image.new('RGB', im.size, (0, 0, 0))
    pill(im, fx, 540, 1400, 'DESDE EL SILLÓN NO SE NOTA', eout(seg(v, 0.35, 0.6)), size=34, border=GRIS, dot=False)
    return sacudir(np.asarray(im), t, golpe_k(v, 0.45, 0.3), amp=14)


# 11. para que el 4K se note: más pantalla (la tele crece con resorte) o sentarte más cerca (el sillón se desliza)
def s_grande(t, fi, u, d):
    up = wt(11, 8) - 0.12                        # «más pantalla»
    uc = wt(11, 11) - 0.12                       # «sentarte más cerca»
    fr = Frame(cam(u, [K(-0.3, 7.4, 70, 30, ty=0.9, tz=2.0), K(0.3, 8.0, 52, 26, ty=0.9, tz=2.0), K(uc, 7.6, 36, 24, ty=0.9, tz=1.8),
                       K(5.0, 7.5, 32, 24, ty=0.9, tz=1.8)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.3)
    sg = 0.62 + 0.5 * P.resorte(seg(u, up, up + 0.45))
    zs = 4.4 - 1.6 * P.eout4(seg(u, uc, uc + 0.4))
    draw_objects(fr, mueble() + tv(t=(0, 0.5, 0), s=sg) + sofa(t=(0.0, 0, zs)))
    pa = fr.cam.p1(centro_tv((0, 0.5, 0), sg) + np.array([0, PH * sg * 0.62, 0]))
    pb = fr.cam.p1((0, 1.2, zs))

    def ui(img, fx):
        kicker(img, 'PARA QUE EL 4K SE NOTE', 150, seg(u, -0.1, 0.2), col=VERDE)
        if u > up:
            check(img, fx, pa[0], max(260, pa[1] - 50), seg(u, up + 0.2, up + 0.45), 'MÁS PANTALLA')
        if u > uc:
            check(img, fx, pb[0], pb[1] - 120, seg(u, uc + 0.2, uc + 0.45), 'MÁS CERCA')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.45, 0.25) + golpe_k(u, uc + 0.4, 0.25), amp=14)


# 12. mándaselo a quien va a comprar tele en el Buen Fin (la caja de la tele cae y rebota)
def _caja_img():
    key = 'caja'
    if key not in _C:
        im = Image.new('RGB', (600, 360), (176, 132, 84))
        d = ImageDraw.Draw(im)
        d.rectangle((40, 40, 560, 320), outline=(120, 86, 50), width=6)
        d.text((300, 150), '4K', font=M.font('sansx', 150), fill=(40, 30, 24), anchor='mm')
        d.text((300, 270), '43"', font=M.font('sans', 60), fill=(60, 44, 30), anchor='mm')
        _C[key] = im.convert('RGBA')
    return _C[key]


def s_manda(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 4.6, 40, 14, ty=0.6), K(0.3, 4.0, 12, 10, ty=0.6), K(4.0, 3.9, 8, 10, ty=0.6)], cy=0.52))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    e = P.entrada(u, 0.0, 0.32, 'cae')
    caja = named(M3.box(2.0, 1.2, 0.4, (176, 132, 84), shadow=0, base=True, gloss=0.1), 'caja', rim=0.4)
    M3.decal(caja, caja.FACE['front'], _caja_img())
    draw_objects(fr, P.tfk([caja], ry=-14, t=(0, -e['dy'] * 0.6, 0)))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien va a', 'sans'), ('comprar tele en el Buen Fin.', 'serif')], 190, seg(u, -0.1, 0.25), size=60)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.3), amp=18)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55), sfx=[]),
           dict(desde=1, fn=s_8m, tr='golpe', sfx=[]),
           dict(desde=2, fn=s_ojo, tr='iris', c=(0.3, 0.5), sfx=[]),
           dict(desde=3, fn=s_cerca, tr='cubo', sfx=[]),
           dict(desde=4, fn=s_lejos, tr='whip_izq', sfx=[]),
           dict(desde=5, fn=s_junta, tr='remolino', c=(0.5, 0.5), sfx=[]),
           dict(desde=6, fn=s_peor, tr='rompe', c=(0.62, 0.5), sfx=[]),
           dict(desde=7, fn=s_abierta, tr='deslizar', sfx=[]),
           dict(desde=8, fn=s_netflix, tr='mosaico', c=(0.72, 0.42), sfx=[]),
           dict(desde=9, fn=s_estira, tr='zoom', c=(0.5, 0.5), sfx=[]),
           dict(desde=10, fn=s_8k, tr='cristal', palabra='8K', sfx=[]),
           dict(desde=11, fn=s_grande, tr='giro', sfx=[]),
           dict(desde=12, fn=s_manda, tr='rebanadas', sfx=[]),
           dict(desde=13, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    E = ESCENAS
    E[0]['sfx'] = [(-0.25, 'digital', 0.5), (U_SAL, 'whoosh', 0.9), (U_PB, 'whoosh_suave', 0.6), (0.92, 'whoosh', 0.6),
                   (1.07, 'sub', 1.0), (1.07, 'bass', 0.8), (0.75, 'tick', 0.5)]
    u4 = wt(1, 9) - 0.12
    E[1]['sfx'] = [(0.0 + 0.08 * i, 'tick2', 0.22) for i in range(int((wt(1, 4) + 0.2) / 0.08))] + \
                  [(wt(1, 4) + 0.2, 'bass', 0.9), (u4, 'whoosh', 0.7), (u4 + 0.05, 'click', 0.6), (u4 + 0.25, 'click', 0.6),
                   (u4 + 0.68, 'bass', 1.0), (u4 + 0.68, 'slap', 0.5)]
    u94 = wt(2, 11) - 0.15
    E[2]['sfx'] = [(-0.2, 'shimmer', 0.6), (wt(2, 6), 'tick', 0.5), (u94 - 0.3, 'whoosh', 0.7)] + \
                  [(u94 + 0.09 * i, 'tick2', 0.2) for i in range(10)] + [(u94 + 0.42, 'bass', 0.9)]
    un = wt(3, 12) - 0.12
    E[3]['sfx'] = [(0.0, 'whoosh', 0.6), (0.3, 'tick', 0.5), (un - 0.05, 'click', 0.9), (un + 0.2, 'click', 0.9), (un + 0.35, 'chime_c', 0.5),
                   (un + 0.5, 'scribble', 0.5)]
    u3, ud = wt(4, 5) - 0.15, wt(4, 9) - 0.12
    E[4]['sfx'] = [(0.0, 'whoosh', 0.8), (0.55, 'thud', 0.6), (u3 + 0.3, 'bass', 0.8), (ud, 'tick', 0.5), (ud + 0.7, 'chime_a', 0.5),
                   (ud + 0.8, 'click', 0.6)]
    uj = wt(5, 8) - 0.1
    E[5]['sfx'] = [(0.1, 'whoosh_suave', 0.6), (uj + 0.25, 'bass', 0.8), (uj + 0.25, 'chime_b', 0.5)]
    un6 = wt(6, 10) - 0.12
    E[6]['sfx'] = [(-0.05, 'sub', 1.0), (0.2, 'click', 0.6), (un6, 'burst', 0.6), (un6 + 0.05, 'scribble', 0.5), (un6 + 0.1, 'bass', 0.9)]
    uh = wt(7, 8) - 0.15
    E[7]['sfx'] = [(-0.2, 'whoosh', 0.6), (0.1, 'thud', 0.7), (0.4, 'riser', 0.3), (uh + 0.3, 'bass', 0.8), (uh + 0.35, 'click', 0.6)]
    up, u15 = wt(8, 11) - 0.12, wt(8, 13) - 0.15
    E[8]['sfx'] = [(-0.2 + 0.16 * i + 0.28, 'thud', 0.6) for i in range(3)] + [(up, 'scribble', 0.5), (up + 0.1, 'chime_c', 0.6)] + \
                  [(u15 - 0.2 + 0.07 * i, 'tick2', 0.22) for i in range(10)] + [(u15 + 0.5, 'bass', 0.8)]
    ue, ua = wt(9, 7) - 0.12, wt(9, 13) - 0.12
    E[9]['sfx'] = [(ue, 'whoosh', 0.7), (ue + 0.4, 'thud', 0.6), (ue + 0.3, 'tick', 0.5)] + \
                  [(ua + 0.06 * i, 'tick2', 0.25) for i in range(8)] + [(ua + 0.3, 'chime_b', 0.5)]
    un10, us10 = wt(10, 6) - 0.12, wt(10, 14) - 0.12
    E[10]['sfx'] = [(0.05, 'slap', 0.6), (un10, 'scribble', 0.6), (un10 + 0.3, 'bass', 0.8), (us10, 'whoosh', 0.8), (us10 + 0.45, 'thud', 0.6)]
    up11, uc11 = wt(11, 8) - 0.12, wt(11, 11) - 0.12
    E[11]['sfx'] = [(0.0, 'tick', 0.5), (up11, 'riser', 0.4), (up11 + 0.45, 'bass', 0.8), (up11 + 0.25, 'chime_a', 0.5),
                    (uc11, 'whoosh', 0.7), (uc11 + 0.4, 'thud', 0.7), (uc11 + 0.3, 'chime_c', 0.5)]
    E[12]['sfx'] = [(0.0, 'whoosh', 0.6), (0.3, 'thud', 0.9), (0.3, 'slap', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
