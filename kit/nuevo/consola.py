"""Reel diario lun 16-nov-2026 10:00 — «Tu consola no guarda la ciudad… la dibuja.» (GTA 6 por dentro: culling, LOD,
streaming desde el SSD y el error del disco USB). Comunidad: gamers (mes del lanzamiento de GTA 6, 19-nov-2026).
Inicio tipo 8 (error en pantalla): la tele con la precarga de 212 GB se pone roja con falla digital; al decir «la dibuja»
la pantalla dibuja la ciudad en línea de luz. El final («porque su consola no guarda la ciudad… la dibuja») regresa a ella (loop).
Voz Isaac (eleven_v4) generada el 13-nov (inbox/narr_consola.mp3), 64.4 s. Datos y fuentes: guiones/2026-11-16_consola.txt.
Consola genérica (sin marca ni logo); todo lo que es ejemplo dice «EJEMPLO» o «RECREACIÓN».
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, line3, dot3, rec_frame,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'consola'
TXT = ['Tu consola no guarda la ciudad… la dibuja.',
       'GTA 6 sale el 19 de noviembre,',
       'y la precarga pide hasta 212 GB.',
       'Pero tu PS5 solo tiene 16 GB de memoria:',
       '13 veces menos.',
       'Así que la arma en vivo,',
       'y solo donde ve tu cámara.',
       'Mira: lo que tienes enfrente se dibuja…',
       'lo que está a tu espalda, no.',
       'Un edificio cerca va con todo su detalle;',
       'el mismo, a lo lejos, con muchos menos triángulos.',
       'Y aquí está el error: comprar un disco USB para que te quepa GTA.',
       'En PS5, lo puedes guardar ahí…',
       'pero no lo puedes jugar desde ahí.',
       'Tiene que estar en la consola,',
       'o en un SSD M.2 que se instala adentro.',
       'Porque los juegos de PS5 están hechos para su disco ultrarrápido:',
       'mientras manejas, tu consola lee la calle que sigue…',
       'antes de que llegues.',
       'Así que cada cuadro que ves es una ciudad nueva,',
       'dibujada decenas de veces por segundo.',
       'Mándaselo a tu compa que ya está bajando GTA 6,',
       'porque su consola no guarda la ciudad… la dibuja.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-16_consola_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_consola.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'inbox', 'words_consola.json')


AMARILLO = (255, 236, 160)
ROJO = (255, 60, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (120, 235, 150)
OSC = (8, 9, 12)


# ------------------------------------------------------------------ tiempos por palabra (u de cada palabra dentro de su frase)
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
            if L[k] is None and last is not None:
                L[k] = last + 0.25
            last = L[k] if L[k] is not None else last
        base = next(x for x in L if x is not None)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wu(i, k):
    L = _wt()[i]
    return L[min(k, len(L) - 1)]


# ------------------------------------------------------------------ utilidades
def cam(u, claves, cy=0.55):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p.get('tx', 0.0), p.get('ty', 0.8), p.get('tz', 0.0)), dist=p['dist'], yaw=p['yaw'],
               pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch, tx=0.0, ty=0.8, tz=0.0, roll=0.0):
    return (u, dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll))


def golpe_k(u, u0, dur=0.32):
    return (1 - seg(u, u0, u0 + dur)) ** 2 if u >= u0 else 0.0


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    return P.mover_img(img, amp * k * math.sin(t * 91.0) * math.cos(t * 37.0), amp * k * math.sin(t * 73.0 + 1.3))


def punch(img, u, u0, s1=1.25, dur=0.3, cx=0.5, cy=0.5):
    """Punch-in digital rápido (eout4) sobre el cuadro terminado."""
    k = P.eout4(seg(u, u0, u0 + dur))
    if k <= 0.001:
        return img
    return M.scale_about(img, 1 + (s1 - 1) * k, cx, cy)


def texto(img, fx, x, y, txt, size, col=WHITE, k=1.0, f='sansx', glow=0.35, anchor='mm'):
    if k <= 0.01:
        return
    lay = Image.new('L', img.size, 0)
    ImageDraw.Draw(lay).text((x, y), txt, font=M.font(f, size), fill=int(255 * clamp(k)), anchor=anchor)
    img.paste(Image.new('RGB', img.size, col), (0, 0), lay)
    if glow:
        fx.paste(Image.new('RGB', img.size, M.scale_c(col, glow)), (0, 0), lay.filter(ImageFilter.GaussianBlur(8)))


def flecha(img, fx, x0, y0, x1, y1, col, k=1.0, w=8):
    if k <= 0.01:
        return
    x1, y1 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    df.line([(x0, y0), (x1, y1)], fill=M.scale_c(col, 0.6), width=w * 3)
    a = math.atan2(y1 - y0, x1 - x0)
    L = 28 + w
    for s in (-1, 1):
        xa, ya = x1 - L * math.cos(a + s * 0.5), y1 - L * math.sin(a + s * 0.5)
        d.line([(x1, y1), (xa, ya)], fill=col, width=w)
        df.line([(x1, y1), (xa, ya)], fill=M.scale_c(col, 0.6), width=w * 3)


def tache(img, fx, x, y, r, k, t, col=ROJO, seed=3):
    N.doodle_arrow_free(img, fx, x - r, y - r, x + r, y + r, t, seg(k, 0.0, 0.5), col, seed=seed)
    N.doodle_arrow_free(img, fx, x + r, y - r, x - r, y + r, t, seg(k, 0.4, 0.9), col, seed=seed + 1)


def palomita(img, fx, x, y, r, k, col=VERDE):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    pts = [(x - r, y), (x - r * 0.3, y + r * 0.7), (x + r, y - r * 0.8)]
    L1 = clamp(k * 2)
    L2 = clamp(k * 2 - 1)
    p1 = (lerp(pts[0][0], pts[1][0], L1), lerp(pts[0][1], pts[1][1], L1))
    d.line([pts[0], p1], fill=col, width=12)
    df.line([pts[0], p1], fill=M.scale_c(col, 0.6), width=26)
    if L2 > 0:
        p2 = (lerp(pts[1][0], pts[2][0], L2), lerp(pts[1][1], pts[2][1], L2))
        d.line([pts[1], p2], fill=col, width=12)
        df.line([pts[1], p2], fill=M.scale_c(col, 0.6), width=26)


def rr(d, box, radius=0, **kw):
    """rounded_rectangle a prueba de cajas diminutas (al entrar con resorte)."""
    x0, y0, x1, y1 = box
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    r = max(0, min(radius, (x1 - x0) / 2 - 1, (y1 - y0) / 2 - 1))
    d.rounded_rectangle((x0, y0, x1, y1), radius=r, **kw)


def recreacion(img, fx, k=1.0, y=1440, txt='RECREACIÓN'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


# ------------------------------------------------------------------ pantallas 2D (decal de la tele)
SW_, SH_ = 960, 540


def _scr_fondo():
    im = Image.new('RGB', (SW_, SH_), OSC)
    d = ImageDraw.Draw(im)
    for j in range(0, SH_, 6):
        d.line([(0, j), (SW_, j)], fill=(12, 13, 17))
    return im, d


def scr_descarga(pct, err=0.0, t=0.0):
    im, d = _scr_fondo()
    f = M.font
    d.text((60, 50), 'PRECARGA', font=f('mono', 30), fill=(150, 160, 175))
    d.text((60, 120), 'GTA 6', font=f('sansx', 110), fill=(245, 245, 247))
    rr(d, (60, 330, 900, 380), radius=25, outline=(210, 214, 222), width=4)
    col = CYAN if err < 0.5 else ROJO
    rr(d, (68, 338, 68 + 824 * clamp(pct), 372), radius=18, fill=col)
    d.text((60, 410), f'{pct * 100:.0f} %', font=f('mono', 40), fill=(230, 232, 236))
    d.text((900, 410), f'{212 * pct:.0f} / 212 GB', font=f('mono', 40), fill=(230, 232, 236), anchor='ra')
    if err > 0.01:
        ov = Image.new('RGB', (SW_, SH_), (120, 8, 8))
        im = Image.blend(im, ov, 0.55 * clamp(err))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 150, SW_, 300), fill=(200, 20, 20))
        d.text((SW_ / 2, 200), '⚠ ERROR', font=f('sansx', 64), fill=(255, 255, 255), anchor='mm')
        d.text((SW_ / 2, 262), 'ESPACIO INSUFICIENTE', font=f('mono', 38), fill=(255, 230, 230), anchor='mm')
        # falla digital: franjas corridas (determinista por t)
        a = np.asarray(im).copy()
        rng = np.random.RandomState(int(t * 24) % 997)
        for _ in range(7):
            y0 = rng.randint(0, SH_ - 30)
            h = rng.randint(6, 30)
            a[y0:y0 + h] = np.roll(a[y0:y0 + h], rng.randint(-60, 60), axis=1)
        a[..., 0] = np.roll(a[..., 0], 6, axis=1)
        im = Image.fromarray(a)
    return im


def _skyline(rng_seed=4):
    rng = np.random.RandomState(rng_seed)
    L = []
    x = 20
    while x < SW_ - 40:
        w = rng.randint(50, 120)
        h = rng.randint(90, 330)
        L.append((x, w, h))
        x += w + rng.randint(6, 26)
    return L


SKY = _skyline()


def scr_ciudad(k, t=0.0, seed=4):
    """La ciudad dibujándose en línea de luz (k de 0 a 1)."""
    im, d = _scr_fondo()
    piso = SH_ - 70
    # piso en perspectiva
    for j in range(9):
        kk = clamp(k * 3 - j * 0.12)
        if kk > 0:
            y = piso + j * j * 1.2
            d.line([(SW_ / 2 - SW_ * kk, y), (SW_ / 2 + SW_ * kk, y)], fill=(60, 120, 150), width=2)
    sky = SKY if seed == 4 else _skyline(seed)
    n = len(sky)
    for i, (x, w, h) in enumerate(sky):
        kk = clamp(k * (n + 4) / 4 - i * 0.3 * 4 / 4 * 0.9 / 0.9 * (1.0 / 1.0) * 0.25 * 4 / 1)
        kk = clamp((k * 1.6 - i / n) * 3)
        if kk <= 0:
            continue
        hh = h * eout(kk)
        col = (120, 225, 255) if i % 3 else (235, 240, 245)
        d.line([(x, piso), (x, piso - hh)], fill=col, width=3)
        d.line([(x + w, piso), (x + w, piso - hh)], fill=col, width=3)
        if kk > 0.6:
            d.line([(x, piso - hh), (x + w, piso - hh)], fill=col, width=3)
            for wy in range(int(piso - hh + 16), int(piso - 10), 26):
                for wx in range(int(x + 10), int(x + w - 10), 22):
                    if (wx * 7 + wy * 3 + i) % 5 < 2:
                        d.rectangle((wx, wy, wx + 8, wy + 10), fill=M.scale_c(col, 0.55))
    return im


def scr_barras(k):
    im, d = _scr_fondo()
    f = M.font
    base = SH_ - 80
    for i, (v, lab, col) in enumerate(((212, 'PRECARGA', (235, 238, 242)), (16, 'MEMORIA', CYAN))):
        kb = eout(seg(k, 0.1 + 0.25 * i, 0.6 + 0.25 * i))
        x0 = 230 + i * 330
        h = 360 * v / 212 * kb
        rr(d, (x0, base - max(6, h), x0 + 170, base), radius=10, fill=col)
        d.text((x0 + 85, base - h - 34), f'{v * kb:.0f} GB', font=f('mono', 38), fill=(240, 240, 244), anchor='mm')
        d.text((x0 + 85, base + 40), lab, font=f('mono', 28), fill=(160, 168, 180), anchor='mm')
    return im


def _con_bisel(scr):
    w, h = scr.size
    b = int(w * 0.025)
    out = Image.new('RGB', (w + 2 * b, h + 2 * b), (14, 14, 16))
    out.paste(scr, (b, b))
    return out.convert('RGBA')


TVW, TVH, TVY = 1.6, 0.9, 0.38


def tv(scr, t=(0, 0, 0), s=1.0, ry=0.0):
    """Tele plana genérica (sin marca) con la pantalla `scr`."""
    marco = named(M3.box(TVW + 0.06, TVH + 0.06, 0.05, (30, 30, 34), shadow=0, base=True, gloss=0.6).tf(t=(0, TVY, 0)),
                  'tele', rim=0.9, gloss=0.6)
    M3.decal(marco, marco.FACE['front'], _con_bisel(scr))
    ms = [marco,
          named(M3.box(0.1, TVY, 0.05, (40, 40, 44), shadow=0, base=True, gloss=0.5).tf(t=(0, 0, -0.04)), 'pie', rim=0.5),
          named(M3.box(0.7, 0.025, 0.3, (40, 40, 44), shadow=0, base=True, gloss=0.5), 'pie', rim=0.5)]
    return P.tfk(ms, s=s, ry=ry, t=t)


def centro_tv(t=(0, 0, 0), s=1.0):
    return (t[0], t[1] + (TVY + (TVH + 0.06) / 2) * s, t[2] + 0.026 * s)


# ------------------------------------------------------------------ consola genérica (frente hacia +z; tarjeta por dentro)
MEMS = [(0.47, -0.2), (0.58, -0.2), (0.69, -0.2), (0.75, -0.05), (0.75, 0.1), (0.69, 0.25), (0.58, 0.25), (0.47, 0.25)]


def consola(luz=0.8, mem=0.0, ssd=0.0, m2=None, m2_glow=0.0):
    """mem/ssd (0-1): cuánto brillan los chips de memoria y de almacenamiento. m2: desplazamiento en z del SSD M.2
    (None = no hay; 0 = instalado)."""
    ms = [named(M3.rbox(0.2, 1.0, 0.74, 0.04, (24, 24, 28), n=3, shadow=0, gloss=0.6).tf(t=(0, 0.04, 0)), 'cuerpo', rim=0.7, gloss=0.6)]
    for sx in (-1, 1):
        ms.append(named(M3.box(0.03, 1.1, 0.82, (232, 234, 238), shadow=0, base=True, gloss=0.5).tf(t=(sx * 0.12, 0.0, 0)),
                        'panel', rim=0.8, gloss=0.5))
        l_ = named(M3.box(0.012, 0.9, 0.012, CYAN, shadow=0, base=True).tf(t=(sx * 0.1, 0.1, 0.375)), 'luz')
        l_.flat = True
        l_.glow = M.scale_c(CYAN, luz)
        ms.append(l_)
    ms.append(named(M3.cyl(0.17, 0.03, (30, 30, 34), n=20, shadow=0, gloss=0.4).tf(t=(0, -0.03, 0)), 'pie', rim=0.4))
    # por dentro
    ms.append(named(M3.box(0.015, 0.78, 0.62, (28, 78, 54), shadow=0, base=True, gloss=0.3).tf(t=(0.0, 0.15, 0)), 'in', rim=0.4))
    ms.append(named(M3.box(0.03, 0.15, 0.15, (90, 92, 100), shadow=0, base=True, gloss=0.8).tf(t=(0.02, 0.5, 0.03)), 'in', rim=0.7))
    for (y, z) in MEMS:
        c = named(M3.box(0.02, 0.07, 0.1, (18, 18, 20), shadow=0, base=True, gloss=0.6).tf(t=(0.018, y - 0.035, z)), 'mem', rim=0.6)
        if mem > 0.01:
            c.glow = M.scale_c(CYAN, 0.9 * mem)
        ms.append(c)
    for z in (-0.18, -0.05):
        c = named(M3.box(0.02, 0.09, 0.1, (20, 20, 24), shadow=0, base=True, gloss=0.6).tf(t=(0.018, 0.27, z)), 'ssd', rim=0.6)
        if ssd > 0.01:
            c.glow = M.scale_c(AMARILLO, 0.9 * ssd)
        ms.append(c)
    ms.append(named(M3.box(0.025, 0.05, 0.05, (200, 200, 205), shadow=0, base=True, gloss=0.8).tf(t=(0.02, 0.17, 0.2)), 'in', rim=0.6))
    if m2 is not None:
        ms += m2_mesh(t=(0.03, 0.18, 0.2 - 0.17 - m2), glow=m2_glow)
    return ms


def m2_mesh(t=(0, 0, 0), s=1.0, glow=0.0, ry=0.0, rz=0.0):
    """SSD M.2 (tarjeta verde delgada, 2 chips y contactos dorados). Largo en z, cara de chips hacia +x."""
    pcb = named(M3.box(0.008, 0.05, 0.3, (24, 92, 60), shadow=0, base=False, gloss=0.4), 'm2', rim=0.6)
    ms = [pcb]
    for z in (-0.06, 0.06):
        c = named(M3.box(0.01, 0.036, 0.08, (16, 16, 18), shadow=0, base=False, gloss=0.6).tf(t=(0.008, 0, z)), 'm2', rim=0.5)
        if glow > 0.01:
            c.glow = M.scale_c(CYAN, glow)
        ms.append(c)
    oro = named(M3.box(0.009, 0.046, 0.025, (220, 180, 80), shadow=0, base=False, gloss=0.9).tf(t=(0, 0, 0.15)), 'm2', rim=0.8, gloss=0.9)
    ms.append(oro)
    return P.tfk(ms, s=s, ry=ry, rz=rz, t=t)


def usb_mesh(t=(0, 0, 0), s=1.0, ry=0.0, rojo=0.0):
    """Disco externo USB genérico (caja con LED)."""
    col = M.mixc((58, 60, 66), (150, 30, 26), rojo)
    ms = [named(M3.rbox(0.36, 0.07, 0.52, 0.05, col, n=3, shadow=0, gloss=0.5), 'usb', rim=0.7, gloss=0.5)]
    led = named(M3.box(0.04, 0.012, 0.012, CYAN, shadow=0, base=True).tf(t=(0.1, 0.03, 0.262)), 'led')
    led.flat = True
    led.glow = M.scale_c(ROJO if rojo > 0.5 else CYAN, 0.9)
    ms.append(led)
    ms.append(named(M3.box(0.06, 0.03, 0.04, (150, 150, 158), shadow=0, base=True, gloss=0.8).tf(t=(0, 0.02, -0.27)), 'usb', rim=0.6))
    return P.tfk(ms, s=s, ry=ry, t=t)


def carro(t=(0, 0, 0), s=1.0, ry=0.0, giro=0.0):
    """Carro genérico low-poly (frente hacia +x)."""
    ms = [named(M3.rbox(0.92, 0.2, 0.44, 0.06, (190, 36, 40), n=3, shadow=0, gloss=0.75).tf(t=(0, 0.1, 0)), 'carro', rim=0.8, gloss=0.75),
          named(M3.rbox(0.48, 0.17, 0.38, 0.06, (26, 30, 40), n=3, shadow=0, gloss=0.9).tf(t=(-0.06, 0.3, 0)), 'vidrio', rim=0.9, gloss=0.9)]
    for x in (-0.3, 0.3):
        for z in (-0.21, 0.21):
            ms.append(named(M3.cyl(0.1, 0.07, (20, 20, 22), n=12, shadow=0, gloss=0.2).tf(rx=90, t=(x, 0.1, z - 0.035)), 'llanta', rim=0.3))
    for z in (-0.15, 0.15):
        f = named(M3.box(0.01, 0.04, 0.08, (255, 250, 230), shadow=0, base=True).tf(t=(0.465, 0.14, z)), 'faro')
        f.flat = True
        f.glow = (200, 200, 180)
        ms.append(f)
    return P.tfk(ms, s=s, ry=ry, t=t)


# ------------------------------------------------------------------ ciudad 3D en línea de luz
def _edif():
    rng = np.random.RandomState(7)
    L = []
    for i in range(-7, 8):
        for j in range(-9, 10):
            if i % 3 == 0 or j % 3 == 0:
                continue
            h = 0.45 + 2.2 * rng.rand() ** 1.6
            L.append((i * 0.9, j * 0.9, 0.62, 0.62, h))
    return L


EDIF = _edif()


def caja_wire(fr, x, z, w, d, h, col=CYAN, a=1.0, frac=1.0, glow=0.7, wl=1.8):
    """Edificio de alambre que «se dibuja»: base, aristas que suben y techo."""
    if a <= 0.01 or frac <= 0.01:
        return
    x0, x1, z0, z1 = x - w / 2, x + w / 2, z - d / 2, z + d / 2
    line3(fr, [(x0, 0.01, z0), (x1, 0.01, z0), (x1, 0.01, z1), (x0, 0.01, z1), (x0, 0.01, z0)], col=col, w=wl, a=a * 0.6,
          glow=glow * 0.5, frac=clamp(frac * 3))
    hh = h * eout(clamp(frac * 1.4))
    for (px, pz) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
        line3(fr, [(px, 0.01, pz), (px, hh, pz)], col=col, w=wl, a=a, glow=glow)
    if frac > 0.6:
        line3(fr, [(x0, hh, z0), (x1, hh, z0), (x1, hh, z1), (x0, hh, z1), (x0, hh, z0)], col=col, w=wl, a=a, glow=glow,
              frac=clamp((frac - 0.6) / 0.4))
        # pisos
        if frac > 0.85 and h > 0.9:
            for yy in np.arange(0.35, hh - 0.1, 0.35):
                line3(fr, [(x0, yy, z1), (x1, yy, z1)], col=col, w=wl * 0.6, a=a * 0.35, glow=0.2)


def edif_mesh(x, z, w, d, h, col=(30, 33, 40), glow=None):
    m = named(M3.box(w, h, d, col, shadow=0, base=True, gloss=0.3).tf(t=(x, 0, z)), 'edif', rim=0.6, gloss=0.3)
    if glow:
        m.glow = glow
    return m


def en_cono(x, z, cx, cz, ang, fov=55, R=5.5):
    dx, dz = x - cx, z - cz
    r = math.hypot(dx, dz)
    if r > R or r < 1e-6:
        return False
    a = math.degrees(math.atan2(dz, dx)) - ang
    a = (a + 180) % 360 - 180
    return abs(a) < fov / 2


def cerca(fr, x, z, R=7.5):
    tx, tz = fr.cam.target[0], fr.cam.target[2]
    return abs(x - tx) < R and abs(z - tz) < R


# ================================================================== escenas
# 0. gancho, inicio tipo 8 (error en pantalla): la precarga de 212 GB se pone roja con falla; «la dibuja» → la pantalla
#    dibuja la ciudad. En el loop (u negativo) la pantalla ya está dibujando la ciudad y regresa a la barra.
def _u_loop():
    T, DUR = montaje.CTX['T'], montaje.CTX['DUR']
    return T[22][0] - DUR - T[0][0]


def _pantalla_gancho(u, t):
    ul = _u_loop()
    if u < -0.62:
        return scr_ciudad(seg(u, ul - 0.2, ul + Wu(22, 7) + 0.9), t)
    if u < -0.42:
        return scr_descarga(0.97 + 0.03 * seg(u, -0.62, -0.42), 0.0, t)
    ud = Wu(0, 6) - 0.05
    if u < ud:
        return scr_descarga(1.0, 1.0, t)
    return scr_ciudad(seg(u, ud, ud + 1.1), t)


def s_gancho(t, fi, u, d):
    ud = Wu(0, 6) - 0.05
    ul = _u_loop()
    fr = Frame(cam(u, [K(ul - 0.3, 4.0, -32, 12, ty=0.78), K(ul + 0.4, 3.1, -14, 8, ty=0.78), K(-0.42, 3.0, -10, 8, ty=0.78),
                       K(-0.25, 2.85, -6, 7, ty=0.78), K(0.0, 2.55, 4, 6, ty=0.8), K(ud, 2.5, 8, 6, ty=0.8),
                       K(ud + 0.05, 2.9, 18, 9, ty=0.78), K(5, 3.0, 22, 9, ty=0.78)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.85, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'CIUDAD', u, t0=-3.4, cy=0.69, entrada='golpe')
    scr = _pantalla_gancho(u, t)
    err = u >= -0.42 and u < ud
    draw_objects(fr, tv(scr) + P.tfk(consola(luz=0.9), s=0.5, ry=28, t=(-0.62, 0, 0.55)))

    def ui(img, fx):
        k1 = seg(u, 0.0, 0.15) if u >= -0.1 else seg(u, ul + 0.05, ul + 0.2) * (1 - seg(u, -0.62, -0.42))
        k2 = seg(u, ud, ud + 0.15) if u >= -0.1 else seg(u, ul + Wu(22, 7), ul + Wu(22, 7) + 0.15) * (1 - seg(u, -0.62, -0.42))
        kicker(img, 'PRECARGA · GTA 6 · 212 GB', 118, k1, col=AZULC if not err else (255, 140, 130))
        P.titulo_golpe(img, fx, [('Tu consola no guarda', 'sans')], 170, k1, size=80)
        P.titulo_golpe(img, fx, [('la ciudad… la dibuja.', 'serif')], 270, k2, size=84)
        recreacion(img, fx, 1.0, y=1452)
        if err:
            ImageDraw.Draw(fx).rectangle((0, 0, M.W, M.H), fill=(12, 0, 0))
    fr.ui.append(ui)
    img = finish(fr, fi)
    img = sacudir(img, t, max(golpe_k(u, 0.15, 0.35), golpe_k(u, ud + 0.15, 0.4), golpe_k(u, -0.42, 0.3)), amp=24)
    return img


# 1. GTA 6 sale el 19 de noviembre (calendario de noviembre de 2026 que cae; el 19 se enciende y se encierra)
def _calendario(img, fx, u, t, ux):
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    x0, y0, cw, ch = 110, 560, 123, 112
    f = M.font
    d.text((540, 470), 'NOVIEMBRE 2026', font=f('mono', 40), fill=(220, 224, 232), anchor='mm')
    for j, ds in enumerate('DLMMJVS'):
        d.text((x0 + cw * j + cw / 2, y0 - 20), ds, font=f('mono', 28), fill=(140, 146, 158), anchor='mm')
    # 1-nov-2026 es domingo
    for dia in range(1, 31):
        idx = dia - 1
        r_, c_ = divmod(idx, 7)
        kk = P.resorte(seg(u, -0.2 + 0.018 * idx, 0.1 + 0.018 * idx))
        if kk <= 0.01:
            continue
        cx, cy = x0 + cw * c_ + cw / 2, y0 + 30 + ch * r_ + ch / 2
        w2, h2 = cw * 0.42 * kk, ch * 0.4 * kk
        es = dia == 19
        ke = seg(u, ux, ux + 0.25) if es else 0.0
        col = M.mixc((60, 64, 74), AMARILLO, ke)
        rr(d, (cx - w2, cy - h2, cx + w2, cy + h2), radius=12, outline=col, width=3,
                            fill=M.scale_c(AMARILLO, 0.25 * ke) if es else None)
        d.text((cx, cy), str(dia), font=f('mono', 36 if not es else int(36 + 18 * ke)), fill=M.mixc((200, 204, 212), WHITE, ke), anchor='mm')
        if es and ke > 0:
            rr(df, (cx - w2 - 8, cy - h2 - 8, cx + w2 + 8, cy + h2 + 8), radius=14, fill=M.scale_c(AMARILLO, 0.5 * ke))
            doodle_circle(img, fx, cx, cy, 90, 76, t, k=seg(u, ux + 0.2, ux + 0.6), col=CYAN, seed=4)


def s_fecha(t, fi, u, d):
    ux = Wu(1, 4) - 0.1                                    # «diecinueve»
    fr = Frame(cam(u, [K(-0.3, 6.5, -40, 30, ty=0.0), K(0.3, 5.4, -8, 22, ty=0.0), K(ux, 5.2, 4, 20, ty=0.0),
                       K(4, 5.1, 8, 20, ty=0.0)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)

    def ui(img, fx):
        kicker(img, 'LANZAMIENTO · PS5 Y XBOX SERIES', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 300, 'GTA 6', 130, WHITE, seg(u, -0.15, 0.05), f='sansx', glow=0.4)
        _calendario(img, fx, u, t, ux)
        P.numero_golpe(img, fx, '19', 1330, seg(u, ux, ux + 0.18), size=200, col=AMARILLO)
    fr.ui.append(ui)
    img = finish(fr, fi)
    img = punch(img, u, ux, 1.18, 0.3, 0.5, 0.55)
    return sacudir(img, t, golpe_k(u, ux + 0.18, 0.3), amp=16)


# 2. la precarga pide hasta 212 GB («212 GB» de cristal; cubos de datos que caen a la consola y el contador sube)
def s_212(t, fi, u, d):
    un = Wu(2, 5) - 0.1                                    # «doscientos doce»
    fr = Frame(cam(u, [K(-0.3, 4.2, 60, 16, ty=0.75), K(0.4, 3.8, 25, 10, ty=0.75), K(un, 3.5, 10, 8, ty=0.78),
                       K(4, 3.45, 6, 8, ty=0.78)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.6)
    M.cristal(fr.base, fr.fx, '212 GB', u, t0=un, cy=0.3, entrada='zoom')
    e = P.entrada(u, -0.25, 0.3, 'pop')
    ms = P.tfk(consola(luz=0.6 + 0.4 * seg(u, 0.0, 1.0)), s=max(0.05, e['escala']))
    # cubos de datos que caen
    for j in range(14):
        ph = (u * 1.4 + j / 14) % 1.0
        if u < 0.1:
            continue
        x = 0.35 * math.sin(j * 2.3)
        z = 0.3 * math.cos(j * 1.7)
        y = 2.2 - 1.6 * ph
        c = named(M3.box(0.07, 0.07, 0.07, CYAN, shadow=0, base=False).tf(ry=j * 30 + u * 90, t=(x, y, z)), 'dato')
        c.flat = True
        c.glow = M.scale_c(CYAN, 0.8 * (1 - ph))
        ms.append(c)
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'PRECARGA DE GTA 6', 150, seg(u, -0.1, 0.2), col=AZULC)
        kc = P.eout4(seg(u, 0.1, un + 0.2))
        texto(img, fx, 540, 1462, f'{212 * kc:.0f} / 212 GB', 38, WHITE, seg(u, 0.0, 0.15), f='mono', glow=0.3)
        x0, x1, y = 170, 910, 1405
        d = ImageDraw.Draw(img)
        rr(d, (x0, y - 16, x1, y + 16), radius=16, outline=(200, 204, 214), width=3)
        rr(d, (x0 + 6, y - 10, x0 + 6 + (x1 - x0 - 12) * kc, y + 10), radius=10, fill=CYAN)
        rr(ImageDraw.Draw(fx), (x0, y - 20, x0 + (x1 - x0) * kc, y + 20), radius=18, fill=M.scale_c(CYAN, 0.4))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.2, 0.3), amp=14)


# 3. tu PS5 solo tiene 16 GB de memoria (rayos X de la consola: 8 chips de memoria que se encienden uno por uno)
def s_memoria(t, fi, u, d):
    u16 = Wu(3, 6) - 0.1                                   # «dieciséis gigas»
    kx = seg(u, 0.05, 0.4)
    fr = Frame(cam(u, [K(-0.3, 3.0, 30, 10, ty=0.55), K(0.45, 1.6, 82, 6, ty=0.55, tz=0.03), K(u16, 1.25, 88, 4, ty=0.6, tz=0.03),
                       K(5, 1.22, 92, 4, ty=0.6, tz=0.03)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8)
    km = seg(u, u16 - 0.3, u16 + 0.5)
    draw_objects(fr, consola(luz=0.8, mem=km), xray=kx, keep=('in', 'mem', 'ssd'))
    pts = [fr.cam.p1((0.03, y, z)) for (y, z) in MEMS]

    def ui(img, fx):
        kicker(img, 'RAYOS X · MEMORIA DE LA CONSOLA', 150, seg(u, 0.2, 0.5), col=AZULC)
        for j, (x, y, _) in enumerate(pts):
            kj = seg(u, u16 - 0.3 + 0.06 * j, u16 + 0.0 + 0.06 * j)
            if kj > 0:
                ImageDraw.Draw(img).text((x, y), '2', font=M.font('mono', 26), fill=M.scale_c(WHITE, kj), anchor='mm')
        pill(img, fx, 540, 1330, '8 CHIPS × 2 GB = 16 GB', eout(seg(u, u16 + 0.4, u16 + 0.7)), size=34, border=CYAN)
        P.numero_golpe(img, fx, '16 GB', 330, seg(u, u16, u16 + 0.18), size=150, col=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u16 + 0.18, 0.3), amp=14)


# 4. trece veces menos (la tele muestra las dos barras; «×13» de cristal arriba). La cámara entra por la pantalla (zoom).
def s_x13(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 4.4, -20, 10, ty=0.85), K(0.3, 3.3, -4, 6, ty=0.82), K(3, 3.2, 0, 6, ty=0.82)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, '×13', u, t0=-0.1, cy=0.27, entrada='golpe')
    uz = d - 0.2 - 0.45                                    # 0.45 s antes del corte, la pantalla ya es la ciudad
    draw_objects(fr, tv(scr_barras(seg(u, -0.2, 0.9)) if u < uz else scr_ciudad(seg(u, uz, uz + 0.4), t)))

    def ui(img, fx):
        kicker(img, 'PRECARGA CONTRA MEMORIA', 1440, seg(u, 0.0, 0.3), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=16)


# 5. así que la arma en vivo (adentro de la pantalla: los edificios suben y se dibujan alrededor de la cámara)
def s_vivo(t, fi, u, d):
    zc = -1.8 - 1.2 * u
    fr = Frame(cam(u, [K(-0.3, 2.6, 0, 6, ty=0.7, tz=zc), K(0.35, 3.2, 22, 14, ty=0.8, tz=zc), K(3, 3.3, 28, 15, ty=0.8, tz=zc)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=0.8)
    for j, (x, z, w, dd, h) in enumerate(EDIF):
        if not cerca(fr, x, z, 6.5):
            continue
        r = math.hypot(x, z - zc)
        if r < 1.4:
            continue
        k = seg(u, -0.5 + r * 0.08, -0.1 + r * 0.08)
        caja_wire(fr, x, z, w, dd, h, col=CYAN if j % 4 else WHITE, a=0.9, frac=k)

    def ui(img, fx):
        texto(img, fx, 540, 300, 'EN VIVO', 120, WHITE, seg(u, 0.05, 0.2), f='sansx', glow=0.5)
        if int(t * 2) % 2 == 0:
            ImageDraw.Draw(img).ellipse((300, 285, 330, 315), fill=ROJO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. y solo donde ve tu cámara (vista de arriba: el cono de la cámara barre la ciudad; solo lo de adentro existe)
def s_cono(t, fi, u, d):
    ang = -90 + 35 * math.sin(u * 1.6)
    fr = Frame(cam(u, [K(-0.3, 5.5, 20, 35, ty=0.0), K(0.4, 8.5, 0, 72, ty=0.0, tz=-1.0), K(3, 8.6, -4, 74, ty=0.0, tz=-1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.6)
    cx, cz = 0.0, 1.6
    ms = carro(t=(cx, 0, cz), s=0.9, ry=-ang)
    ms2 = []
    for (x, z, w, dd, h) in EDIF:
        if not cerca(fr, x, z, 7):
            continue
        if en_cono(x, z, cx, cz, ang):
            ms2.append(edif_mesh(x, z, w, dd, h, col=(40, 46, 58), glow=M.scale_c(CYAN, 0.12)))
        else:
            line3(fr, [(x - w / 2, 0.01, z - dd / 2), (x + w / 2, 0.01, z - dd / 2), (x + w / 2, 0.01, z + dd / 2),
                       (x - w / 2, 0.01, z + dd / 2), (x - w / 2, 0.01, z - dd / 2)], col=GRIS, w=1.2, a=0.35, glow=0.0)
    # el cono
    for s_ in (-1, 1):
        a = math.radians(ang + s_ * 27.5)
        line3(fr, [(cx, 0.02, cz), (cx + 5.5 * math.cos(a), 0.02, cz + 5.5 * math.sin(a))], col=AMARILLO, w=3, a=0.9, glow=1.0)
    draw_objects(fr, ms2 + ms)

    def ui(img, fx):
        kicker(img, 'VISTA DE ARRIBA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, 'SOLO SE DIBUJA LO QUE VE LA CÁMARA', eout(seg(u, 0.4, 0.7)), size=28, border=AMARILLO, dot=False)
        recreacion(img, fx, 1.0, y=1420, txt='ESQUEMA')
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. lo que tienes enfrente se dibuja (cámara detrás del carro; los edificios de enfrente se dibujan y se llenan)
def _calle(fr, u, frente=True, k=1.0, xc=0.0, extra=()):
    sol, wires = [], []
    for (x, z, w, dd, h) in EDIF:
        if not cerca(fr, x, z, 7.5):
            continue
        adelante = x > xc + 0.3
        if adelante == frente:
            r = abs(x - xc)
            kk = seg(k, r * 0.05, r * 0.05 + 0.5)
            wires.append((x, z, w, dd, h, kk))
            if kk > 0.9:
                sol.append(edif_mesh(x, z, w * 0.98, dd * 0.98, h * 0.99, col=(34, 38, 48), glow=M.scale_c(CYAN, 0.06)))
    draw_objects(fr, sol + list(extra))
    for (x, z, w, dd, h, kk) in wires:
        caja_wire(fr, x, z, w, dd, h, col=CYAN, a=0.9, frac=kk)


def s_frente(t, fi, u, d):
    ud = Wu(7, 6) - 0.1                                    # «se dibuja»
    xc = -0.2 + 0.25 * u
    fr = Frame(cam(u, [K(-0.3, 3.8, -96, 24, tx=xc + 0.7, ty=0.5, tz=0.0), K(0.35, 3.5, -86, 18, tx=xc + 0.7, ty=0.55),
                       K(ud, 3.3, -80, 16, tx=xc + 0.7, ty=0.6), K(4, 3.25, -78, 16, tx=xc + 0.7, ty=0.6)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    _calle(fr, u, True, seg(u, -0.1, ud + 0.5), xc, extra=carro(t=(xc, 0, 0.0), giro=t * 8))

    def ui(img, fx):
        kicker(img, 'ENFRENTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, '✓ SE DIBUJA', eout(seg(u, ud, ud + 0.3)), size=34, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. lo que está a tu espalda, no (la cámara se voltea: atrás solo queda el piso; «ESPALDA» de cristal)
def s_espalda(t, fi, u, d):
    xc = -0.2 + 0.25 * (u + 2.6)
    fr = Frame(cam(u, [K(-0.3, 2.3, -70, 8, tx=xc, ty=0.55), K(0.4, 2.6, 92, 10, tx=xc, ty=0.55), K(3, 2.7, 100, 10, tx=xc, ty=0.55)],
                   cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'ESPALDA', u, t0=0.0, cy=0.4, entrada='sube')
    for (x, z, w, dd, h) in EDIF:
        if x < xc - 0.3 and cerca(fr, x, z, 6):
            line3(fr, [(x - w / 2, 0.01, z - dd / 2), (x + w / 2, 0.01, z - dd / 2), (x + w / 2, 0.01, z + dd / 2),
                       (x - w / 2, 0.01, z + dd / 2), (x - w / 2, 0.01, z - dd / 2)], col=GRIS, w=1.2, a=0.4, glow=0.0)
    draw_objects(fr, carro(t=(xc, 0, 0.0), giro=t * 8))

    def ui(img, fx):
        kicker(img, 'ATRÁS DE TI', 150, seg(u, -0.1, 0.2), col=(255, 140, 130))
        pill(img, fx, 540, 1330, '✗ NO EXISTE HASTA QUE VOLTEAS', eout(seg(u, 0.5, 0.8)), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. un edificio cerca va con todo su detalle (malla de triángulos densa + zoom digital con marco REC)
def edificio_tri(fr, cx, cz, w, h, n, col=CYAN, a=1.0, k=1.0):
    """Cara frontal de un edificio con su malla de triángulos (n divisiones)."""
    x0, x1 = cx - w / 2, cx + w / 2
    ny = max(1, int(n * h / w))
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        line3(fr, [(x, 0, cz), (x, h * k, cz)], col=col, w=1.4, a=a * 0.8, glow=0.4)
    for j in range(ny + 1):
        y = h * j / ny
        if y <= h * k:
            line3(fr, [(x0, y, cz), (x1, y, cz)], col=col, w=1.4, a=a * 0.8, glow=0.4)
    for i in range(n):
        for j in range(ny):
            ya, yb = h * j / ny, h * (j + 1) / ny
            if yb <= h * k:
                line3(fr, [(lerp(x0, x1, i / n), ya, cz), (lerp(x0, x1, (i + 1) / n), yb, cz)], col=col, w=1.0, a=a * 0.55, glow=0.2)


def s_cerca(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 3.4, 30, 6, ty=1.1), K(0.35, 2.6, 8, 4, ty=1.1), K(3, 2.5, 4, 4, ty=1.12)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    ms = [edif_mesh(0, -0.05, 1.2, 0.1, 2.2, col=(30, 34, 44))]
    draw_objects(fr, ms)
    edificio_tri(fr, 0, 0.005, 1.2, 2.2, 10, k=P.eout4(seg(u, -0.2, 0.6)))
    zl = 1.0 if u < 1.0 else (1.3 if u < 1.8 else 1.8)

    def ui(img, fx):
        kicker(img, 'EDIFICIO CERCA · DETALLE ALTO', 150, seg(u, -0.1, 0.2), col=AZULC)
        rec_frame(img, t, k=1.0, zoom_label=f'x{zl:.1f}')
        pill(img, fx, 540, 1330, 'MÁS TRIÁNGULOS = MÁS DETALLE', eout(seg(u, 0.5, 0.8)), size=28, border=CYAN, dot=False)
    fr.ui.append(ui)
    img = finish(fr, fi)
    return M.scale_about(img, zl, 0.5, 0.45) if zl > 1 else img


# 10. el mismo, a lo lejos, con muchos menos triángulos (se aleja y su malla se simplifica: LOD 0 → 1 → 2; «LEJOS»)
def s_lejos(t, fi, u, d):
    ul = Wu(10, 4) - 0.1                                   # «a lo lejos»
    zf = -0.05 - 9.0 * P.eout4(seg(u, ul, ul + 1.4))
    fr = Frame(cam(u, [K(-0.3, 2.6, 4, 4, ty=1.1), K(0.35, 3.0, -10, 5, ty=1.1), K(5, 3.0, -12, 5, ty=1.1)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'LEJOS', u, t0=ul, cy=0.62, entrada='golpe')
    lv = 0 if zf > -3 else (1 if zf > -6 else 2)
    n = (10, 4, 1)[lv]
    draw_objects(fr, [edif_mesh(0, zf - 0.05, 1.2, 0.1, 2.2, col=(30, 34, 44))])
    edificio_tri(fr, 0, zf + 0.005, 1.2, 2.2, n, col=(CYAN, AMARILLO, ROJO)[lv])
    tris = (440, 64, 4)[lv]

    def ui(img, fx):
        kicker(img, 'NIVEL DE DETALLE (LOD)', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 300, f'LOD {lv}', 110, (CYAN, AMARILLO, ROJO)[lv], 1.0, f='mono', glow=0.5)
        pill(img, fx, 540, 1330, f'≈ {tris} TRIÁNGULOS · EJEMPLO', eout(seg(u, 0.2, 0.5)), size=28, border=(CYAN, AMARILLO, ROJO)[lv], dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. SEGUNDO GANCHO: el error — comprar un disco USB para que te quepa GTA (el disco cae junto a la consola; «USB»)
def s_error(t, fi, u, d):
    uu = Wu(11, 8) - 0.1                                   # «disco USB»
    fr = Frame(cam(u, [K(-0.3, 3.6, -40, 18, ty=0.45), K(0.35, 3.0, -16, 14, ty=0.45), K(uu, 2.5, 10, 12, ty=0.35),
                       K(uu + 1.4, 2.7, 24, 14, ty=0.4), K(6, 2.75, 28, 14, ty=0.4)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'USB', u, t0=uu, cy=0.36, entrada='golpe')
    e = P.entrada(u, uu - 0.1, 0.4, 'cae')
    ms = P.tfk(consola(luz=0.8), s=0.7, t=(-0.4, 0.021, 0))
    ms += usb_mesh(t=(0.45, 0.02 + max(0.0, -e['dy']) * 0.6, 0.15), ry=-20, rojo=seg(u, uu + 1.2, uu + 1.6))
    draw_objects(fr, ms)
    if u > uu + 0.2:
        a, b = (-0.33, 0.25, 0.3), (0.45, 0.05, -0.1)
        line3(fr, [a, (0.0, 0.03, 0.3), b], col=(170, 170, 178), w=3, a=0.9, glow=0.0, frac=seg(u, uu + 0.2, uu + 0.6))
    pu = fr.cam.p1((0.45, 0.1, 0.15))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, -0.1, 0.1), col=(255, 140, 130))
        P.titulo_golpe(img, fx, [('El error:', 'sans')], 200, seg(u, 0.0, 0.15), size=90)
        P.titulo_golpe(img, fx, [('comprar un disco USB.', 'serif')], 310, seg(u, uu, uu + 0.15), size=80)
        if u > uu + 1.2:
            tache(img, fx, pu[0], pu[1], 110, seg(u, uu + 1.2, uu + 1.8), t)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.15, 0.3), golpe_k(u, uu + 0.3, 0.4)), amp=24)


# 12. en PS5 lo puedes guardar ahí (cubos de datos viajan por el cable al disco: ✓ GUARDAR)
def s_guardar(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.4, 60, 30, ty=0.25), K(0.35, 2.8, 30, 24, ty=0.25), K(3, 2.85, 24, 24, ty=0.25)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9)
    ms = P.tfk(consola(luz=0.8), s=0.8, t=(-0.45, 0.024, 0)) + usb_mesh(t=(0.45, 0.02, 0.15), ry=-20)
    path = [(-0.33, 0.25, 0.3), (0.0, 0.03, 0.3), (0.45, 0.05, -0.1)]
    line3(fr, path, col=(170, 170, 178), w=3, a=0.9, glow=0.0)
    for j in range(6):
        ph = (u * 1.3 + j / 6) % 1.0
        if u < 0.1:
            break
        if ph < 0.5:
            p = np.array(path[0]) + (np.array(path[1]) - np.array(path[0])) * (ph * 2)
        else:
            p = np.array(path[1]) + (np.array(path[2]) - np.array(path[1])) * ((ph - 0.5) * 2)
        c = named(M3.box(0.06, 0.06, 0.06, CYAN, shadow=0, base=False).tf(t=tuple(p + np.array([0, 0.05, 0]))), 'dato')
        c.flat = True
        c.glow = M.scale_c(CYAN, 0.9)
        ms.append(c)
    draw_objects(fr, ms)
    pu = fr.cam.p1((0.45, 0.2, 0.15))

    def ui(img, fx):
        pill(img, fx, pu[0], pu[1] - 140, 'GUARDAR AHÍ', eout(seg(u, 0.2, 0.5)), size=34, border=VERDE)
        palomita(img, fx, pu[0], pu[1] - 260, 50, seg(u, 0.4, 0.8))
        kicker(img, 'ALMACENAMIENTO USB · SOLO GUARDA', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. pero no lo puedes jugar desde ahí (botón de jugar en rojo, tachado; el cable se corta)
def s_jugar(t, fi, u, d):
    uj = Wu(13, 4) - 0.1                                   # «jugar»
    fr = Frame(cam(u, [K(-0.3, 2.9, 24, 24, ty=0.25), K(0.3, 2.3, -10, 14, ty=0.3), K(3, 2.25, -14, 14, ty=0.3)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9)
    ms = P.tfk(consola(luz=0.5), s=0.8, t=(-0.45, 0.024, 0)) + usb_mesh(t=(0.45, 0.02, 0.15), ry=-20, rojo=seg(u, uj, uj + 0.3))
    draw_objects(fr, ms)
    line3(fr, [(-0.33, 0.25, 0.3), (0.0, 0.03, 0.3)], col=ROJO, w=3, a=0.9, glow=0.6)
    line3(fr, [(0.08, 0.03, 0.26), (0.45, 0.05, -0.1)], col=ROJO, w=3, a=0.9, glow=0.6)
    pu = fr.cam.p1((0.45, 0.2, 0.15))

    def ui(img, fx):
        kicker(img, 'JUEGOS DE PS5 DESDE USB', 150, seg(u, -0.1, 0.2), col=(255, 140, 130))
        k = P.resorte(seg(u, uj - 0.2, uj + 0.1))
        if k > 0.01:
            cx, cy, r = 540, 520, 150 * k
            dd = ImageDraw.Draw(img)
            dd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ROJO, width=8)
            dd.polygon([(cx - r * 0.3, cy - r * 0.45), (cx - r * 0.3, cy + r * 0.45), (cx + r * 0.5, cy)], fill=WHITE)
            ImageDraw.Draw(fx).ellipse((cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10), outline=M.scale_c(ROJO, 0.6), width=20)
            tache(img, fx, cx, cy, 170, seg(u, uj + 0.2, uj + 0.7), t)
        pill(img, fx, pu[0], pu[1] - 120, '✗ JUGAR DESDE AHÍ', eout(seg(u, uj + 0.3, uj + 0.6)), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uj + 0.1, 0.3), amp=18)


# 14. tiene que estar en la consola (rayos X: el almacenamiento interno se enciende)
def s_adentro(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.6, -50, 12, ty=0.5), K(0.35, 1.7, 70, 6, ty=0.4, tz=0.0), K(3, 1.6, 76, 6, ty=0.4)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8)
    draw_objects(fr, consola(luz=0.8, ssd=seg(u, 0.2, 0.6)), xray=seg(u, -0.1, 0.25), keep=('in', 'mem', 'ssd'))
    ps = fr.cam.p1((0.03, 0.31, -0.11))

    def ui(img, fx):
        kicker(img, 'ADENTRO DE LA CONSOLA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, ps[0], ps[1] - 170, 'SSD INTERNO', eout(seg(u, 0.3, 0.6)), size=32, border=AMARILLO)
        doodle_circle(img, fx, ps[0], ps[1], 120, 80, t, k=seg(u, 0.4, 0.8), col=AMARILLO, seed=5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. o en un SSD M.2 que se instala adentro (la tarjeta entra deslizándose a su ranura y hace clic; «M.2»)
def s_m2(t, fi, u, d):
    um = Wu(15, 3) - 0.1                                   # «SSD»
    ki = P.eout4(seg(u, um + 0.2, um + 0.9))
    fr = Frame(cam(u, [K(-0.3, 0.75, 84, 4, ty=0.2, tz=0.12), K(0.4, 1.0, 64, 14, ty=0.22, tz=0.1), K(um + 0.9, 0.9, 74, 10, ty=0.2, tz=0.08),
                       K(5, 0.92, 78, 10, ty=0.2, tz=0.08)], cy=0.58))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'M.2', u, t0=um, cy=0.3, entrada='zoom')
    draw_objects(fr, consola(luz=0.7, m2=0.5 * (1 - ki), m2_glow=seg(u, um + 0.9, um + 1.3)), xray=1.0, keep=('in', 'mem', 'ssd', 'm2'))
    pm = fr.cam.p1((0.04, 0.2, 0.05))

    def ui(img, fx):
        kicker(img, 'RANURA DE EXPANSIÓN', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pm[0], pm[1] + 170, 'SSD M.2 · PCIe 4.0', eout(seg(u, um + 0.9, um + 1.2)), size=32, border=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.9, 0.25), amp=10)


# 16. hechos para su disco ultrarrápido (barras de velocidad: USB contra el SSD de la consola; destellos de velocidad)
def s_rapido(t, fi, u, d):
    uu = Wu(16, 9) - 0.1                                   # «ultrarrápido»
    fr = Frame(cam(u, [K(-0.3, 6.0, -30, 20, ty=0.0), K(0.35, 5.2, -6, 14, ty=0.0), K(uu, 4.6, 6, 12, ty=0.0), K(6, 4.5, 10, 12, ty=0.0)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)

    def ui(img, fx):
        kicker(img, 'VELOCIDAD DE LECTURA · GB POR SEGUNDO', 150, seg(u, -0.1, 0.2), col=AZULC)
        dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        base = 1250
        for i, (v, lab, col, u0) in enumerate(((1.25, 'USB 10 Gbps', GRIS, 0.2), (5.5, 'SSD DE LA PS5', CYAN, uu - 0.4))):
            kb = P.eout4(seg(u, u0, u0 + 0.6))
            x0 = 220 + i * 380
            h = 760 * v / 5.5 * kb
            rr(dd, (x0, base - max(6, h), x0 + 260, base), radius=14, fill=col)
            if i == 1:
                rr(df, (x0 - 10, base - h - 10, x0 + 270, base + 10), radius=18, fill=M.scale_c(CYAN, 0.35 * kb))
            dd.text((x0 + 130, base - h - 50), f'{v * kb:.2f}'.rstrip('0').rstrip('.') if kb > 0.98 else f'{v * kb:.1f}',
                    font=M.font('mono', 56), fill=WHITE, anchor='mm')
            dd.text((x0 + 130, base + 50), lab, font=M.font('mono', 30), fill=(170, 176, 188), anchor='mm')
        if u > uu:
            for j in range(10):
                y = 330 + j * 90
                L = 300 + 200 * math.sin(j * 3.1)
                x = ((u - uu) * 2400 + j * 377) % 1600 - 300
                dd.line([(x, y), (x + L, y)], fill=M.scale_c(WHITE, 0.35), width=3)
    fr.ui.append(ui)
    img = finish(fr, fi)
    return sacudir(punch(img, u, uu, 1.15, 0.3, 0.7, 0.45), t, golpe_k(u, uu + 0.3, 0.3), amp=12)


# 17. mientras manejas, tu consola lee la calle que sigue (las cuadras de enfrente se cargan antes de llegar)
def _cuadras(fr, xc, u, adelante=2.6, col=CYAN, extra=()):
    sol, wires = [], []
    for (x, z, w, dd, h) in EDIF:
        if abs(z) > 3.0 or not cerca(fr, x, z, 7.5):
            continue
        dx = x - xc
        if dx < -1.2:
            continue
        if dx < adelante:
            sol.append(edif_mesh(x, z, w * 0.98, dd * 0.98, h, col=(34, 38, 48), glow=M.scale_c(CYAN, 0.06)))
            wires.append((x, z, w, dd, h, 1.0, col, 0.6))
        elif dx < adelante + 1.0:
            wires.append((x, z, w, dd, h, 1 - (dx - adelante) / 1.0, AMARILLO, 0.95))
    draw_objects(fr, sol + list(extra))
    for (x, z, w, dd, h, k, c, a) in wires:
        caja_wire(fr, x, z, w, dd, h, col=c, a=a, frac=k)


def s_calle(t, fi, u, d):
    xc = 0.9 * u
    fr = Frame(cam(u, [K(-0.3, 4.8, -150, 40, tx=xc + 1.0, ty=0.3), K(0.35, 4.2, -120, 46, tx=xc + 1.2, ty=0.3),
                       K(4, 4.1, -116, 46, tx=xc + 1.2, ty=0.3)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    _cuadras(fr, xc, u, extra=carro(t=(xc, 0, 0.0), giro=t * 10))
    pa = fr.cam.p1((xc + 3.2, 0.2, 0.0))
    ps = fr.cam.p1((xc, 0.6, 0.0))

    def ui(img, fx):
        kicker(img, 'LA CONSOLA LEE EL MAPA DEL SSD', 150, seg(u, -0.1, 0.2), col=AZULC)
        flecha(img, fx, ps[0], ps[1] - 60, pa[0], pa[1] - 120, AMARILLO, k=eout(seg(u, 0.2, 0.6)), w=7)
        pill(img, fx, pa[0], pa[1] - 200, 'CARGANDO LA SIGUIENTE CALLE', eout(seg(u, 0.4, 0.7)), size=26, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. antes de que llegues (crash zoom a la cuadra que aparece justo antes del carro)
def s_antes(t, fi, u, d):
    xc = 0.9 * (u + 3.1)
    fr = Frame(cam(u, [K(-0.3, 4.8, -90, 42, tx=xc + 1.3, ty=0.3), K(0.25, 3.3, -90, 26, tx=xc + 1.5, ty=0.35),
                       K(3, 3.2, -88, 26, tx=xc + 1.5, ty=0.35)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    _cuadras(fr, xc, u, adelante=1.6 + 1.0 * P.eout4(seg(u, 0.2, 0.5)), extra=carro(t=(xc, 0, 0.0), giro=t * 10))

    def ui(img, fx):
        pill(img, fx, 540, 1330, '✓ LISTA ANTES DE QUE LLEGUES', eout(seg(u, 0.3, 0.55)), size=30, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.45, 0.3), amp=14)


# 19. cada cuadro que ves es una ciudad nueva (tira de cuadros que pasa volando; «CUADRO» de cristal)
def s_cuadros(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 5.0, 30, 10, ty=0.9), K(0.35, 4.4, 6, 6, ty=0.9), K(4, 4.3, 2, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0)
    M.cristal(fr.base, fr.fx, 'CUADRO', u, t0=-0.1, cy=0.33, entrada='zoom')
    ms = []
    for j in range(-3, 5):
        x = j * 1.95 - (u * 1.3) % 1.95
        ms += tv(scr_ciudad(1.0, t, seed=4 + j % 5), t=(x, 0.0, -0.6 + 0.0), s=1.05)[:1]
    draw_objects(fr, ms)

    def ui(img, fx):
        n = int(u * 30) + 1
        texto(img, fx, 540, 1300, f'CUADRO {max(1, n):04d}', 64, WHITE, seg(u, 0.1, 0.3), f='mono', glow=0.4)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. dibujada decenas de veces por segundo (cronómetro de 1 s y contador de cuadros; la ciudad parpadea al redibujarse)
def s_decenas(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.6, -30, 8, ty=0.85), K(0.3, 3.2, -6, 6, ty=0.85), K(3, 3.25, -2, 6, ty=0.85)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.4)
    kc = seg(u, 0.1, 1.1)
    draw_objects(fr, tv(scr_ciudad((u * 30 % 1.0) * 0.5 + 0.5, t, seed=4 + int(u * 30) % 5)))

    def ui(img, fx):
        dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        cx, cy, r = 540, 360, 130
        dd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(200, 204, 214), width=6)
        dd.pieslice((cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14), -90, -90 + 360 * kc, fill=M.scale_c(CYAN, 0.5))
        dd.text((cx, cy), f'{30 * kc:.0f}', font=M.font('mono', 90), fill=WHITE, anchor='mm')
        dd.text((cx, cy + r + 50), 'CUADROS EN 1 SEGUNDO', font=M.font('mono', 30), fill=(170, 176, 188), anchor='mm')
        recreacion(img, fx, 1.0, y=1440, txt='EJEMPLO: 30 CUADROS POR SEGUNDO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. mándaselo a tu compa que ya está bajando GTA 6 (la tele con la descarga avanzando; título que se estrella)
def s_compa(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 4.2, 40, 14, ty=0.8), K(0.35, 3.4, 12, 8, ty=0.8), K(4, 3.3, 8, 8, ty=0.8)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.85, bokeh=1.0, beam=0.5)
    pct = 0.55 + 0.35 * seg(u, 0.0, 2.8)
    draw_objects(fr, tv(scr_descarga(pct, 0.0, t)) + P.tfk(consola(luz=0.9), s=0.5, ry=-28, t=(0.6, 0, 0.55)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que ya está bajando GTA 6.', 'serif')], 190, seg(u, 0.05, 0.2), size=70)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45), sfx=[(-0.25, 'sub', 0.6), (-0.22, 'digital', 0.8), (0.15, 'bass', 0.8)]),
           dict(desde=1, fn=s_fecha, tr='glitch', sfx=[(0.0, 'tick2', 0.4), (1.25, 'bass', 0.8), (1.5, 'scribble', 0.5)]),
           dict(desde=2, fn=s_212, tr='mosaico', sfx=[(0.0, 'thud', 0.5)] + [(0.3 + 0.18 * j, 'tick2', 0.3) for j in range(8)]),
           dict(desde=3, fn=s_memoria, tr='cubo', sfx=[(0.1, 'shimmer', 0.5)] + [(2.0 + 0.06 * j, 'click', 0.35) for j in range(8)]),
           dict(desde=4, fn=s_x13, tr='golpe', c=(0.5, 0.55), sfx=[(0.1, 'chime_a', 0.4), (0.35, 'chime_b', 0.4)]),
           dict(desde=5, fn=s_vivo, tr='zoom', sfx=[(0.1, 'riser', 0.4)]),
           dict(desde=6, fn=s_cono, tr='giro', sfx=[(0.3, 'whoosh_suave', 0.5)]),
           dict(desde=7, fn=s_frente, tr='deslizar', sfx=[(1.2, 'shimmer', 0.5), (1.4, 'tick', 0.4)]),
           dict(desde=8, fn=s_espalda, tr='cubo_izq', sfx=[(0.6, 'burst', 0.4)]),
           dict(desde=9, fn=s_cerca, tr='iris', c=(0.5, 0.45), sfx=[(1.0, 'click', 0.7), (1.8, 'click', 0.7)]),
           dict(desde=10, fn=s_lejos, tr='whip', sfx=[(0.9, 'whoosh', 0.6), (1.5, 'tick', 0.4), (2.0, 'tick', 0.4)]),
           dict(desde=11, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(1.6, 'thud', 1.0), (3.0, 'scribble', 0.6)]),
           dict(desde=12, fn=s_guardar, tr='deslizar_abajo', sfx=[(0.5, 'chime_c', 0.5)]),
           dict(desde=13, fn=s_jugar, tr='glitch', sfx=[(0.8, 'bass', 0.7), (1.0, 'scribble', 0.6)]),
           dict(desde=14, fn=s_adentro, tr='flash', sfx=[(0.3, 'shimmer', 0.5), (0.5, 'scribble', 0.4)]),
           dict(desde=15, fn=s_m2, tr='push', c=(0.5, 0.6), sfx=[(1.0, 'whoosh', 0.5), (1.7, 'click', 1.0), (1.75, 'thud', 0.6)]),
           dict(desde=16, fn=s_rapido, tr='cristal', palabra='RÁPIDO', sfx=[(0.3, 'chime_a', 0.4), (2.6, 'chime_c', 0.5), (3.3, 'whoosh', 0.7)]),
           dict(desde=17, fn=s_calle, tr='whip_izq', sfx=[(0.6, 'riser', 0.3)]),
           dict(desde=18, fn=s_antes, tr='golpe', c=(0.5, 0.55), sfx=[(0.45, 'bass', 0.8)]),
           dict(desde=19, fn=s_cuadros, tr='rebanadas', sfx=[(0.2 + 0.4 * j, 'click', 0.4) for j in range(6)]),
           dict(desde=20, fn=s_decenas, tr='ritmo', sfx=[(0.1 + 0.1 * j, 'tick2', 0.25) for j in range(10)]),
           dict(desde=21, fn=s_compa, tr='remolino', sfx=[(0.2, 'bass', 0.7)]),
           dict(desde=22, loop=True, tr='wipe')]

if __name__ == '__main__':
    montaje.cli(globals())
