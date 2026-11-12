"""Reel diario sáb 14-nov-2026 10:00 — «¿Tuviste vocho? El último del mundo… se armó en Puebla.»
Comunidad: autos clásicos / vocheros (decisión de Efrén del 10-nov: vehículos y comunidades mexicanas por dentro).
Inicio tipo 11 (pregunta directa): «¿TUVISTE / VOCHO?» gigante en letras de cristal se rompe en pedazos y deja ver
un vocho real (foto 3D) con «PUEBLA» de cristal detrás. El final regresa a la pregunta (loop).
Ciencia: motor bóxer enfriado por aire (turbina, aletas y aceite) y el error de seguir con el foco rojo prendido
(la misma banda mueve el generador y la turbina). Voz Isaac (eleven_v4), recortada y reordenada para que el error
caiga a los 28 s. Datos y fuentes: guiones/2026-11-14_vocho.txt. Fotos reales: vocho amarillo en Campeche
(Gideon, CC BY 2.0) y motor 1200 de 1953 (TTTNIS, CC0; etiqueta de la bobina difuminada).
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import foto3d as F3
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'vocho'
TXT = ['¿Tuviste vocho? El último del mundo… se armó en Puebla.',
       'Salió el 30 de julio de 2003:',
       'el número 21 529 464.',
       'Y su secreto va atrás:',
       'un motor sin radiador y sin una gota de agua.',
       'Mira por dentro: cuatro cilindros acostados,',
       'dos de cada lado, llenos de aletas.',
       'Una turbina sopla aire entre las aletas y se lleva el calor;',
       'el aceite ayuda a enfriar.',
       'Y el error que lo amarra en unos kilómetros:',
       'seguir manejando con el foco rojo prendido.',
       'Una sola banda mueve el generador… y también la turbina.',
       'Si se rompe, prende el foco rojo,',
       'la turbina se para y el motor se queda sin aire.',
       'En un par de kilómetros se calienta tanto',
       'que se queman las válvulas y el motor se amarra.',
       'Por eso el manual de Volkswagen dice: si prende ese foco, apaga el motor.',
       'Revisa la banda: si está floja o rajada, cámbiala antes de salir.',
       'Puebla lo armó 36 años:',
       'casi 1.7 millones de vochos.',
       'Mándaselo a quien tuvo un vocho,',
       'porque el último del mundo… se armó en Puebla.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-14_vocho_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_vocho.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-14_vocho_words.json')
FOTOS = '/home/claude/fotos_1114'
if not os.path.exists(os.path.join(FOTOS, 'vocho_motor.jpg')):
    FOTOS = os.path.join(_REPO, 'inbox')

AMARILLO = (255, 226, 90)
AMBAR = (255, 196, 70)
NARANJA = (255, 140, 50)
ROJO = (255, 60, 50)
AZULC = (150, 210, 230)
AGUA = (90, 170, 255)
GRIS = (150, 150, 160)
ALU = (178, 180, 186)
HIERRO = (92, 94, 100)
NEGRO = (28, 28, 32)
CROMO = (214, 216, 222)
ACEITE = (226, 160, 40)


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
        base = next((x for x in L if x is not None), 0.0)
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


def credito(img, txt, y=1872, k=1.0):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((540, y), txt, font=M.font('mono', 19), fill=M.scale_c((150, 150, 158), k), anchor='mm')


CRED_V = 'FOTO: GIDEON · CC BY 2.0 · WIKIMEDIA COMMONS'
CRED_M = 'FOTO: TTTNIS · CC0 · WIKIMEDIA COMMONS'

# ------------------------------------------------------------------ fotos reales
VOCHO = F3.preparar(os.path.join(FOTOS, 'vocho_campeche.jpg'), 'vocho_amarillo', recorte=(0.0, 0.22, 0.86, 0.72))


def vocho(img, fx, cx, piso, alto, yaw=0.0, t=0.0, alfa=1.0, xray=0.0, dy=0.0, esc=1.0, brillo=1.0, flip=False):
    luz = (-0.65 + 0.55 * math.sin(t * 0.9), -0.62)
    return F3.dibujar(img, VOCHO, cx, piso - alto * 0.5 + dy, alto, yaw=yaw, pitch=0.12, luz=luz, fx=fx, alfa=alfa,
                      reflejo=0.24, borde=0.6, piso_y=piso + dy, xray=xray, esc=esc, brillo=brillo)


_F = {}


def foto_motor():
    if 'm' not in _F:
        im = Image.open(os.path.join(FOTOS, 'vocho_motor.jpg')).convert('RGB')
        box = (860, 800, 1560, 1420)                                    # etiqueta de la bobina (marca): difuminada
        im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(26)), box[:2])
        im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        _F['m'] = im
    return _F['m']


def icono_vocho(w):
    key = ('ic', w)
    if key not in _F:
        m = Image.fromarray((VOCHO.m * 255).astype(np.uint8))
        h = max(2, int(w * VOCHO.h / VOCHO.w))
        _F[key] = m.resize((w, h), Image.LANCZOS)
    return _F[key]


# ------------------------------------------------------------------ el motor bóxer (eje del cigüeñal = z; atrás del auto = +z)
def _cyl_x(r, h, x0, y, z, lado, col, name='in', gloss=0.4, n=22):
    m = M3.cyl(r, h, col, n=n, shadow=0, gloss=gloss).tf(rz=-90 if lado > 0 else 90, t=(x0, y, z))
    return named(m, name, rim=0.6, gloss=gloss)


def _cyl_z(r, h, x, y, z0, col, name='pieza', gloss=0.6, n=24):
    m = M3.cyl(r, h, col, n=n, shadow=0, gloss=gloss).tf(rx=90, t=(x, y, z0 + h))
    return named(m, name, rim=0.7, gloss=gloss)


Y0 = 0.62            # altura del cigüeñal
GEN = (0.0, 1.42, 0.62)     # polea del generador (arriba)
CIG = (0.0, Y0 - 0.02, 0.62)  # polea del cigüeñal (abajo)


def motor(calor=0.0, giro=0.0, banda=True, shroud=True, aceite_k=0.0, sep=0.0):
    """Motor bóxer de 4 cilindros (2 por lado) con aletas, cabezas, carcasa de la turbina, generador y poleas.
    calor 0-1 pone los cilindros al rojo; sep separa los cilindros (vista explotada)."""
    ms = []
    ms.append(named(M3.rbox(0.56, 0.5, 0.86, 0.08, ALU, n=3, shadow=0, gloss=0.55).tf(t=(0, Y0 - 0.25, 0)), 'carter',
                    rim=0.7, gloss=0.55))
    glow = M.scale_c(M.mixc(NARANJA, ROJO, calor), 0.25 + 0.75 * calor) if calor > 0.02 else None
    for lado in (-1, 1):
        for z in (-0.22, 0.22):
            x0 = lado * (0.28 + sep)
            c = _cyl_x(0.15, 0.46, x0, Y0, z, lado, HIERRO)
            if glow:
                c.glow = glow
            ms.append(c)
            for j in range(7):
                xf = x0 + lado * (0.05 + j * 0.06)
                f = _cyl_x(0.2, 0.018, xf, Y0, z, lado, (150, 152, 160), gloss=0.5, n=20)
                if glow:
                    f.glow = M.scale_c(glow, 0.8)
                ms.append(f)
        hx = lado * (0.78 + sep)
        hd = named(M3.box(0.16, 0.4, 0.92, (168, 168, 174), shadow=0, gloss=0.5).tf(t=(hx, Y0 - 0.2, 0)), 'in', rim=0.6)
        if glow:
            hd.glow = M.scale_c(glow, 0.7)
        ms.append(hd)
    if shroud:
        ms.append(named(M3.rbox(1.25, 0.34, 0.82, 0.16, NEGRO, n=4, shadow=0, gloss=0.5).tf(t=(0, Y0 + 0.24, -0.02)),
                        'carcasa', rim=0.8, gloss=0.5))
        ms.append(named(M3.rbox(0.62, 0.3, 0.5, 0.2, NEGRO, n=4, shadow=0, gloss=0.5).tf(t=(0, Y0 + 0.56, 0.12)),
                        'carcasa', rim=0.8, gloss=0.5))
    # generador (cilindro a lo largo de z, encima de la turbina) y su polea; la turbina va en el mismo eje
    ms.append(_cyl_z(0.13, 0.62, GEN[0], GEN[1], -0.1, CROMO, 'generador', gloss=0.8))
    ms.append(_cyl_z(0.11, 0.05, GEN[0], GEN[1], GEN[2] - 0.05, (210, 212, 218), 'polea', gloss=0.9))
    ms.append(_cyl_z(0.17, 0.05, CIG[0], CIG[1], CIG[2] - 0.05, (210, 212, 218), 'polea', gloss=0.9))
    # turbina (aspas) dentro de la carcasa, en el eje del generador
    for j in range(10):
        a = giro + j * 2 * math.pi / 10
        ms.append(named(M3.box(0.03, 0.24, 0.06, (200, 200, 206), shadow=0, base=False, gloss=0.7)
                        .tf(rz=math.degrees(a), t=(0.12 * math.sin(a) * 0, GEN[1] - 0.02, -0.22))
                        .tf(t=(0, 0, 0)), 'turbina', rim=0.6))
    # enfriador de aceite (placas) junto a la turbina
    for j in range(6):
        col = M.mixc((120, 120, 128), ACEITE, aceite_k)
        p = named(M3.box(0.22, 0.02, 0.3, col, shadow=0, gloss=0.6).tf(t=(-0.42, Y0 + 0.44 + j * 0.045, -0.12)),
                  'enfriador', rim=0.6)
        if aceite_k > 0.05:
            p.glow = M.scale_c(ACEITE, 0.5 * aceite_k)
        ms.append(p)
    return ms


def correa(fr, t, k=1.0, vel=6.0, rota=0.0, col=(96, 96, 104)):
    """La banda entre la polea del generador y la del cigüeñal (con marcas que avanzan). rota: 0-1, se rompe."""
    g, c = np.array(GEN), np.array(CIG)
    rg, rc = 0.12, 0.18
    z = GEN[2] + 0.02
    pts = []
    for a in np.linspace(math.pi, 0, 14):
        pts.append((g[0] + rg * math.cos(a), g[1] + rg * math.sin(a), z))
    for a in np.linspace(0, -math.pi, 18):
        pts.append((c[0] + rc * math.cos(a), c[1] + rc * math.sin(a), z))
    pts.append(pts[0])
    if rota <= 0.01:
        line3(fr, pts, col=col, w=15, a=k, glow=0.0)
        line3(fr, pts, col=(220, 220, 230), w=3, a=0.8 * k, glow=0.6)
        n = len(pts) - 1
        for j in range(8):                                                   # marcas que corren
            q = ((j / 8 + t * vel * 0.05) % 1.0) * n
            i = int(q)
            p0, p1 = np.array(pts[i]), np.array(pts[min(i + 1, n)])
            dot3(fr, tuple(p0 + (p1 - p0) * (q - i)), r=3.2, col=AMARILLO, a=k, glow=0.8)
    else:
        # se rompe del lado derecho: los dos extremos caen y se abren
        right = pts[13:16]
        mid = len(pts) // 2
        A = pts[:14]
        B = pts[14:]
        dz = rota
        A2 = [(x - 0.35 * dz * (j / len(A)), y - 0.5 * dz * (j / len(A)) ** 2, zz) for j, (x, y, zz) in enumerate(A)]
        B2 = [(x + 0.3 * dz * (1 - j / len(B)), y - 0.9 * dz * (1 - j / len(B)) ** 2, zz) for j, (x, y, zz) in enumerate(B)]
        for L in (A2, B2):
            line3(fr, L, col=col, w=15, a=k, glow=0.0)
            line3(fr, L, col=(220, 220, 230), w=3, a=0.8 * k, glow=0.6)


def aire(fr, t, k=1.0, n=46, vel=1.3, col=(170, 230, 255)):
    """Partículas de aire que la turbina empuja por arriba y bajan entre las aletas de los cilindros."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(7)
    for j in range(n):
        ph = (t * vel + rng.rand()) % 1.0
        lado = 1 if j % 2 else -1
        z = (rng.rand() - 0.5) * 0.7
        x = lado * (0.1 + 0.85 * ph)
        y = GEN[1] - 0.15 - 0.95 * ph ** 0.8
        a = k * math.sin(math.pi * ph)
        dot3(fr, (x, y, z), r=3.4, col=col, a=a, glow=1.0)


# ------------------------------------------------------------------ silueta del tablero: velocímetro con el foco rojo
def tablero(img, fx, cx, cy, r, t, foco=0.0, km=None, aguja=0.35, k=1.0):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(12, 12, 14), outline=M.scale_c((220, 220, 226), k), width=6)
    for j in range(13):
        a = math.radians(140 + j * 260 / 12)
        r0 = r * (0.78 if j % 2 else 0.72)
        d.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a))],
               fill=M.scale_c(WHITE, 0.8 * k), width=4)
    a = math.radians(140 + 260 * aguja)
    d.line([(cx, cy), (cx + r * 0.7 * math.cos(a), cy + r * 0.7 * math.sin(a))], fill=M.scale_c(NARANJA, k), width=8)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(60, 60, 66))
    texto(img, fx, cx, cy - r * 0.42, 'km/h', int(r * 0.12), GRIS, k, f='mono', glow=0)
    # foco rojo (generador y enfriamiento)
    fy = cy + r * 0.42
    fr_ = int(r * 0.13)
    on = foco * (0.75 + 0.25 * math.sin(t * 18))
    d.ellipse((cx - fr_, fy - fr_, cx + fr_, fy + fr_), fill=M.mixc((50, 16, 16), ROJO, on), outline=(90, 90, 96), width=3)
    if on > 0.05:
        for j, rr in enumerate((fr_ * 2.2, fr_ * 4.0)):
            df.ellipse((cx - rr, fy - rr, cx + rr, fy + rr), fill=M.scale_c(ROJO, on * 0.5 / (j + 1)))
    if km is not None:
        d.rounded_rectangle((cx - r * 0.42, cy + r * 0.1, cx + r * 0.42, cy + r * 0.26), radius=6, fill=(20, 20, 24),
                            outline=(110, 110, 120), width=2)
        texto(img, fx, cx, cy + r * 0.18, km, int(r * 0.12), WHITE, k, f='mono', glow=0.2)


def pregunta_frame(t, fi, u):
    """Capa A del inicio: «¿TUVISTE / VOCHO?» gigante en letras de cristal (también es el cuadro del loop)."""
    s = 1.0 + 0.04 * clamp((u + 1.5) / 3.0)
    fr = Frame(camara(u, [K(-2.0, 6.0, 20, 6, ty=0.5), K(0.0, 5.5, 12, 6, ty=0.5), K(2.0, 5.2, 8, 6, ty=0.5)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.55, bokeh=1.0, beam=0.45)
    M.cristal(fr.base, fr.fx, '¿TUVISTE', u, t0=-3.3, cy=0.36, entrada='golpe')
    M.cristal(fr.base, fr.fx, 'VOCHO?', u, t0=-3.1, cy=0.58, entrada='zoom')

    def ui(img, fx):
        kicker(img, 'AUTOS CLÁSICOS · LO QUE NO VES', 150, 1.0, col=AZULC)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return M.scale_about(out, s) if hasattr(M, 'scale_about') else out


# ================================================================== escenas
U_R = 1.22            # se rompe la pregunta (justo en «El último…»)


def _vocho_gancho(t, fi, u):
    up = Wp(0, 'puebla') - 0.08
    fr = Frame(camara(u, [K(U_R - 0.1, 7.5, -30, 10, ty=0.4), K(U_R + 0.2, 5.6, 8, 6, ty=0.4), K(5, 5.3, 14, 6, ty=0.4)],
                      cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.6)
    M.cristal(fr.base, fr.fx, 'PUEBLA', u, t0=U_R - 0.05, cy=0.43, entrada='golpe')
    e = P.entrada(u, U_R, 0.3, 'cae')
    yaw = -0.7 + 1.0 * P.eout4(seg(u, U_R, U_R + 0.6)) + 0.1 * math.sin(t * 0.8)

    def ui(img, fx):
        vocho(img, fx, 540, 1180, 400, yaw=yaw, t=t, dy=e['dy'] * 120)
        kicker(img, 'VOLKSWAGEN SEDÁN · EL ÚLTIMO DEL MUNDO', 150, seg(u, U_R, U_R + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('El último del mundo…', 'sans'), ('se armó en Puebla.', 'serif')], 230,
                       seg(u, up, up + 0.15), size=70)
        credito(img, CRED_V, k=seg(u, U_R, U_R + 0.3))
    fr.ui.append(ui)
    return finish(fr, fi)


def s_gancho(t, fi, u, d):
    if u < U_R - 0.12:
        return pregunta_frame(t, fi, u)
    k = seg(u, U_R - 0.12, U_R + 0.26)
    B = _vocho_gancho(t, fi, u)
    if k < 1:
        A = pregunta_frame(t, fi, u)
        out = M.tr_rompe(A, B, k, 0.5, 0.45)
    else:
        out = B
    up = Wp(0, 'puebla') - 0.08
    return sacudir(out, t, max(golpe_k(u, U_R + 0.3, 0.35), golpe_k(u, up + 0.15, 0.3)), amp=24)


# 1. salió el 30 de julio de 2003: sale de la planta de Puebla (portón de línea) y el fechador se voltea
def s_fecha(t, fi, u, d):
    u30 = Wp(1, 'treinta') - 0.05
    u03 = Wp(1, 'dos') - 0.05
    fr = Frame(camara(u, [K(-0.2, 7.0, 35, 8, tx=-0.6, ty=0.8), K(0.5, 5.6, 10, 5, tx=0.0, ty=0.8),
                          K(d, 5.3, 4, 5, tx=0.2, ty=0.8)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8, beam=0.5, beam_x=0.6)
    M.cristal(fr.base, fr.fx, '2003', u, t0=u03, cy=0.3, entrada='zoom')
    # el portón de la línea (marco de luz)
    q = [(-2.2, 0, -0.6), (-2.2, 2.2, -0.6), (-0.6, 2.2, -0.6), (-0.6, 0, -0.6)]
    line3(fr, q, col=WHITE, w=3, a=0.8, glow=0.8)
    for j in range(5):
        line3(fr, [(-2.2 + 0.32 * j + 0.16, 2.2, -0.6), (-2.2 + 0.32 * j + 0.16, 2.0, -0.6)], col=AMARILLO, w=3, a=0.8)
    salida = P.eout4(seg(u, -0.2, 0.5))

    def ui(img, fx):
        kicker(img, 'PLANTA DE PUEBLA · LÍNEA DEL SEDÁN', 150, 1.0, col=AZULC)
        vocho(img, fx, 160 + 420 * salida, 1230, 330, yaw=-0.4 + 0.5 * salida, t=t)
        # fechador de paletas
        d_ = ImageDraw.Draw(img)
        vals = [('30', u30), ('JUL', u30 + 0.35), ('2003', u03 + 0.2)]
        x = 160
        for j, (txt, uu) in enumerate(vals):
            w = 150 if j < 2 else 260
            kk = seg(u, uu - 0.12, uu + 0.05)
            d_.rounded_rectangle((x, 560, x + w, 700), radius=14, fill=(16, 16, 20), outline=(120, 120, 130), width=3)
            d_.line([(x + 4, 630), (x + w - 4, 630)], fill=(50, 50, 56), width=3)
            if kk > 0:
                sy = 0.2 + 0.8 * P.resorte(kk)
                lay = Image.new('L', (w, 140), 0)
                ImageDraw.Draw(lay).text((w / 2, 70), txt, font=M.font('mono', 84 if j < 2 else 92), fill=255, anchor='mm')
                lay = lay.resize((w, max(2, int(140 * sy))))
                img.paste(Image.new('RGB', lay.size, AMARILLO if j == 2 else WHITE), (x, int(630 - lay.size[1] / 2)), lay)
            x += w + 20
        pill(img, fx, 540, 780, 'ÚLTIMA EDICIÓN', eout(seg(u, u03 + 0.3, u03 + 0.55)), size=28, border=AMARILLO)
        credito(img, CRED_V)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u03 + 0.25, 0.3), amp=14)


# 2. el número 21 529 464: muro de siluetas de vochos y un contador que se clava
def s_numero(t, fi, u, d):
    ufin = Wp(2, 'cuatro', 1) - 0.1
    fr = Frame(camara(u, [K(-0.2, 9.0, 0, 30, ty=0.0), K(d, 8.0, 0, 34, ty=0.0)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.9)
    z = 1.0 + 1.6 * P.eout4(seg(u, ufin, ufin + 0.5))

    def ui(img, fx):
        ic = icono_vocho(int(84 * z))
        cols, rows = 9, 22
        dx_, dy_ = 98 * z, 52 * z
        x0 = 540 - (cols - 1) / 2 * dx_
        y0 = 980 - (rows - 1) / 2 * dy_
        n = 0
        for r in range(rows):
            for c in range(cols):
                x, y = x0 + c * dx_, y0 + r * dy_
                if not (-120 < x < 1200 and -80 < y < 2000):
                    continue
                last = (r == rows // 2 and c == cols // 2)
                kk = seg(u, -0.2 + 0.012 * ((r * 7 + c * 13) % 40), 0.0 + 0.012 * ((r * 7 + c * 13) % 40))
                if kk <= 0:
                    continue
                col = AMARILLO if (last and u > ufin) else (70, 72, 80)
                img.paste(Image.new('RGB', ic.size, col), (int(x - ic.width / 2), int(y - ic.height / 2)), ic)
                if last and u > ufin:
                    fx.paste(Image.new('RGB', ic.size, M.scale_c(AMARILLO, 0.6)), (int(x - ic.width / 2), int(y - ic.height / 2)),
                             ic.filter(ImageFilter.GaussianBlur(6)))
                n += 1
        d_ = ImageDraw.Draw(img)
        d_.rectangle((0, 300, 1080, 470), fill=(0, 0, 0))
        v = int(21529464 * P.eout4(seg(u, -0.1, ufin + 0.1)))
        txt = f'{v:,}'.replace(',', ' ')
        texto(img, fx, 540, 390, txt, 112, WHITE, 1.0, f='mono', glow=0.5)
        kicker(img, 'VOCHOS FABRICADOS EN EL MUNDO', 270, 1.0, col=AZULC)
        if u > ufin:
            pill(img, fx, 540, 1060 + 30 * z, 'EL ÚLTIMO', eout(seg(u, ufin + 0.2, ufin + 0.45)), size=32, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ufin + 0.1, 0.35), amp=18)


# 3. su secreto va atrás: crash zoom a la parte de atrás (el motor), con garabato
def s_atras(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 6.0, -10, 6, ty=0.5), K(0.3, 4.6, -30, 8, tx=-0.8, ty=0.5), K(d, 4.4, -34, 8, tx=-0.9, ty=0.5)],
                      cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.4, beam_x=0.3)
    z = P.eout4(seg(u, -0.1, 0.35))

    def ui(img, fx):
        alto = 380 + 520 * z
        cx = 540 + 560 * z
        vocho(img, fx, cx, 1250 + 160 * z, alto, yaw=-0.2 - 0.6 * z, t=t)
        doodle_circle(img, fx, 330, 1020, 230, 170, t, k=seg(u, 0.4, 0.75), col=AMARILLO, w=7, seed=2)
        pill(img, fx, 330, 760, 'AQUÍ VA EL MOTOR', eout(seg(u, 0.5, 0.75)), size=30, border=AMARILLO)
        kicker(img, 'EL SECRETO', 150, 1.0, col=AZULC)
        credito(img, CRED_V)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. prueba en dos casos: motor con radiador y agua (arriba) contra el del vocho, solo aire (abajo, foto real)
def _radiador(fr, t, k=1.0):
    for j in range(9):
        x = -1.0 + j * 0.25
        line3(fr, [(x, 0.3, 0), (x, 1.6, 0)], col=(200, 200, 210), w=2, a=0.7 * k, glow=0.3)
    line3(fr, [(-1.1, 0.3, 0), (1.1, 0.3, 0), (1.1, 1.6, 0), (-1.1, 1.6, 0), (-1.1, 0.3, 0)], col=WHITE, w=3, a=k, glow=0.6)
    # manguera con agua que corre
    pts = [(1.1, 1.4, 0), (1.7, 1.4, 0.2), (2.2, 1.0, 0.3), (2.2, 0.5, 0.3), (1.7, 0.4, 0.2), (1.1, 0.5, 0)]
    line3(fr, pts, col=(60, 70, 90), w=10, a=k, glow=0.0)
    for j in range(10):
        q = ((t * 0.9 + j / 10) % 1.0) * (len(pts) - 1)
        i = int(q)
        p0, p1 = np.array(pts[i]), np.array(pts[min(i + 1, len(pts) - 1)])
        dot3(fr, tuple(p0 + (p1 - p0) * (q - i)), r=6, col=AGUA, a=k, glow=1.2)


def s_sinagua(t, fi, u, d):
    urad = Wp(4, 'radiador') - 0.1
    uag = Wp(4, 'agua') - 0.1
    fr = Frame(camara(u, [K(-0.2, 5.6, 25, 5, tx=0.55, ty=0.95), K(0.4, 4.9, 6, 4, tx=0.55, ty=0.95), K(d, 4.8, 2, 4, tx=0.55, ty=0.95)],
                      cy=0.25))
    space(fr, t, floor=None, bokeh=0.7)
    M.cristal(fr.base, fr.fx, 'SIN AGUA', u, t0=uag - 0.1, cy=0.53, entrada='sube')
    _radiador(fr, t, k=eout(seg(u, -0.2, 0.1)))

    def ui(img, fx):
        d_ = ImageDraw.Draw(img)
        d_.line([(0, 960), (1080, 960)], fill=(200, 200, 205), width=3)
        kicker(img, 'UN MOTOR NORMAL: RADIADOR + AGUA', 120, 1.0, col=AGUA)
        P.pill_tachada(img, fx, 540, 820, 'RADIADOR', 1.0, seg(u, urad, urad + 0.3), t, size=30, col=AGUA)
        photo_card(img, fx, foto_motor(), 540, 1390, 760, t - u - 0.05, t, caption=CRED_M, angle0=-6.0)
        kicker(img, 'EL DEL VOCHO: SOLO AIRE', 1000, eout(seg(u, -0.1, 0.2)), col=AMARILLO)
        P.pill_tachada(img, fx, 540, 1700, 'AGUA', eout(seg(uag, 0, 1) if u > uag else 0.0), seg(u, uag + 0.2, uag + 0.5), t,
                       size=30, col=AGUA)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.08, 0.3), amp=12)


# 5 y 6. por dentro: el motor bóxer se arma solo (rayos X) y luego crash zoom a las aletas con zoom digital
def s_dentro(t, fi, u, d):
    uc = Wp(5, 'cuatro') - 0.1
    k = 1 - P.eout4(seg(u, -0.2, 0.55))
    fr = Frame(camara(u, [K(-0.2, 4.6, 70, 30, ty=0.75), K(0.5, 3.6, 25, 22, ty=0.75), K(d, 3.4, 18, 20, ty=0.75)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8, beam=0.5)
    ms = motor(giro=t * 6)
    draw_objects(fr, P.despiece(ms, k, centro=(0, Y0, 0), fuerza=1.3, giro=0.6), xray=0.85, keep=('in', 'carter'))
    pts = [fr.cam.p1((s * 0.55, Y0, z)) for s in (-1, 1) for z in (-0.22, 0.22)]

    def ui(img, fx):
        kicker(img, 'RAYOS X · MOTOR BÓXER 1.6', 150, 1.0, col=AZULC)
        for j, p in enumerate(pts):
            pill(img, fx, p[0], p[1] - 70, str(j + 1), eout(seg(u, uc + 0.12 * j, uc + 0.12 * j + 0.2)), size=34, border=CYAN)
        texto(img, fx, 540, 300, 'acostados', 92, WHITE, eout(seg(u, Wp(5, 'acostados'), Wp(5, 'acostados') + 0.2)), f='serif')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.4, 0.3), amp=14)


def s_aletas(t, fi, u, d):
    ul = Wp(6, 'llenos') - 0.1
    fr = Frame(camara(u, [K(-0.2, 3.2, -20, 10, tx=0.0, ty=0.7), K(0.35, 2.8, -55, 8, tx=0.0, ty=0.7),
                          K(ul, 2.2, -62, 14, tx=0.5, ty=Y0, tz=0.0), K(d, 2.1, -66, 14, tx=0.5, ty=Y0, tz=0.0)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9, beam=0.3)
    draw_objects(fr, motor(giro=t * 6), xray=0.6, keep=('in', 'carter'))
    zl = 'x1.0' if u < ul else ('x1.3' if u < ul + 0.4 else 'x1.8')

    def ui(img, fx):
        kicker(img, '2 Y 2 · CILINDROS OPUESTOS', 150, 1.0, col=AZULC)
        if u < ul:
            pill(img, fx, 270, 1240, '2 AQUÍ', eout(seg(u, 0.0, 0.25)), size=30, border=CYAN)
            pill(img, fx, 810, 1240, '2 ALLÁ', eout(seg(u, 0.4, 0.65)), size=30, border=CYAN)
        else:
            rec_frame(img, t, 1.0, zl)
            pill(img, fx, 540, 1330, 'ALETAS', eout(seg(u, ul + 0.1, ul + 0.35)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. la turbina sopla aire entre las aletas y se lleva el calor
def s_turbina(t, fi, u, d):
    ucal = Wp(7, 'calor') - 0.1
    fr = Frame(camara(u, [K(-0.2, 3.6, 40, 40, ty=0.9), K(0.4, 3.2, 15, 32, ty=0.9), K(d, 3.0, 8, 30, ty=0.9)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, 'AIRE', u, t0=-0.15, cy=0.3, entrada='golpe')
    calor = 0.8 * (1 - seg(u, 0.3, ucal + 0.6))
    draw_objects(fr, motor(calor=calor, giro=t * 14), xray=0.75, keep=('in', 'turbina'))
    aire(fr, t, k=eout(seg(u, -0.2, 0.3)))
    pt = fr.cam.p1((0, GEN[1], -0.22))

    def ui(img, fx):
        kicker(img, 'ENFRIADO POR AIRE', 150, 1.0, col=AZULC)
        pill(img, fx, pt[0], pt[1] - 110, 'TURBINA', eout(seg(u, 0.0, 0.25)), size=30, border=CYAN)
        P.termometro(img, fx, 860, 900, 360, 0.25 + calor * 0.7, 'CALOR', k=1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. el aceite ayuda a enfriar: el enfriador se llena de aceite
def s_aceite(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 2.6, 60, 20, tx=-0.4, ty=1.0, tz=-0.1), K(0.35, 1.7, 40, 14, tx=-0.42, ty=1.1, tz=-0.12),
                          K(d, 1.6, 34, 12, tx=-0.42, ty=1.1, tz=-0.12)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.9, beam=0.3)
    ka = seg(u, 0.1, 0.8)
    draw_objects(fr, motor(giro=t * 14, aceite_k=ka), xray=0.7, keep=('in', 'enfriador'))
    pts = [(-0.55, Y0 + 0.44, -0.3), (-0.55, Y0 + 0.75, -0.3), (-0.3, Y0 + 0.75, 0.05), (-0.3, Y0 + 0.44, 0.05),
           (-0.55, Y0 + 0.44, -0.3)]
    for j in range(12):
        q = ((t * 0.7 + j / 12) % 1.0) * (len(pts) - 1)
        i = int(q)
        p0, p1 = np.array(pts[i]), np.array(pts[i + 1])
        dot3(fr, tuple(p0 + (p1 - p0) * (q - i)), r=5, col=ACEITE, a=ka, glow=1.2)
    pe = fr.cam.p1((-0.42, Y0 + 0.75, -0.12))

    def ui(img, fx):
        kicker(img, 'ENFRIADOR DE ACEITE', 150, 1.0, col=AZULC)
        pill(img, fx, pe[0], pe[1] - 120, '2.5 L DE ACEITE', eout(seg(u, 0.3, 0.55)), size=30, border=ACEITE)
        texto(img, fx, 540, 300, 'también enfría', 84, WHITE, eout(seg(u, 0.4, 0.6)), f='serif')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.32, 0.25), amp=10)


# 9. el error (segundo gancho): el tablero con el foco rojo, en rojo
def s_error(t, fi, u, d):
    ukm = Wp(9, 'kilometros') - 0.1
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 8, ty=0.8), K(d, 5.6, 0, 8, ty=0.8)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.6)

    def ui(img, fx):
        d_ = ImageDraw.Draw(fx)
        d_.rectangle((0, 0, 1080, 1920), fill=M.scale_c((90, 0, 0), 0.25 + 0.15 * math.sin(t * 12)))
        kicker(img, '⚠ EL ERROR', 150, 1.0, col=ROJO)
        P.titulo_golpe(img, fx, [('El error que lo amarra', 'sans'), ('en unos kilómetros.', 'serif')], 230,
                       seg(u, 0.0, 0.15), size=68, col=WHITE)
        sc = P.resorte(seg(u, 0.1, 0.45))
        tablero(img, fx, 540, 1010, int(300 * max(0.05, sc)), t, foco=seg(u, 0.6, 0.7), km=None, aguja=0.42, k=1.0)
        if u > ukm:
            P.numero_golpe(img, fx, '+ 3 km', 1450, seg(u, ukm, ukm + 0.15), size=120, col=ROJO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.15, 0.3), golpe_k(u, ukm + 0.15, 0.3)), amp=22)


# 10. seguir manejando con el foco rojo prendido: carretera que corre, el vocho y el foco gigante
def s_foco(t, fi, u, d):
    ufo = Wp(10, 'foco') - 0.1
    fr = Frame(camara(u, [K(-0.2, 5.0, 60, 12, ty=0.6), K(0.4, 4.4, 30, 8, ty=0.6), K(d, 4.2, 24, 8, ty=0.6)], cy=0.6))
    space(fr, t, floor=None, bokeh=0.6)
    M.cristal(fr.base, fr.fx, 'FOCO ROJO', u, t0=ufo, cy=0.3, entrada='golpe')
    for x in (-1.6, 1.6):
        line3(fr, [(x, 0, -12), (x, 0, 6)], col=WHITE, w=3, a=0.8, glow=0.6)
    for j in range(8):
        z = -12 + ((j * 2.4 + t * 14) % 19.2)
        line3(fr, [(0, 0, z), (0, 0, z + 1.0)], col=AMARILLO, w=4, a=0.9, glow=0.8)

    def ui(img, fx):
        kicker(img, 'Y SIGUE MANEJANDO…', 150, 1.0, col=ROJO)
        vocho(img, fx, 540 + 8 * math.sin(t * 30), 1260, 300, yaw=0.15, t=t)
        km = 0.3 + 2.4 * seg(u, 0.0, d)
        tablero(img, fx, 830, 760, 170, t, foco=1.0 if u > ufo else 0.6, km=f'{km:4.1f} km', aguja=0.5 + 0.03 * math.sin(t * 9))
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. una sola banda mueve el generador… y también la turbina (foto real con zoom digital)
def s_banda(t, fi, u, d):
    ug = Wp(11, 'generador') - 0.1
    ut = Wp(11, 'turbina') - 0.1
    fr = Frame(camara(u, [K(-0.2, 5.0, 0, 8, ty=0.8), K(d, 4.8, 0, 8, ty=0.8)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.6)
    M.cristal(fr.base, fr.fx, 'BANDA', u, t0=-0.1, cy=0.2, entrada='sube')
    im = foto_motor()
    W0, H0 = im.size
    # zoom digital por pasos: toda la foto → generador → turbina
    if u < ug:
        z, cx, cy, zl = 1.0, 0.5, 0.55, 'x1.0'
    elif u < ut:
        z, cx, cy, zl = 1.6, 0.54, 0.62, 'x1.6'
    else:
        z, cx, cy, zl = 1.3, 0.5, 0.42, 'x1.3'
    cw, ch = W0 / z, H0 / z
    x0 = clamp(cx * W0 - cw / 2, 0, W0 - cw)
    y0 = clamp(cy * H0 - ch / 2, 0, H0 - ch)
    crop = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((1000, int(1000 * H0 / W0)), Image.LANCZOS)

    def ui(img, fx):
        img.paste(crop, (40, 640))
        d_ = ImageDraw.Draw(img)
        d_.rectangle((40, 640, 1040, 640 + crop.height), outline=(200, 200, 210), width=3)
        rec_frame(img, t, 1.0, zl)
        kicker(img, 'UNA SOLA BANDA', 470, 1.0, col=AMARILLO)
        if ug <= u < ut:
            doodle_circle(img, fx, 600, 640 + crop.height * 0.48, 170, 170, t, k=seg(u, ug, ug + 0.25), col=AMARILLO, w=7, seed=4)
            pill(img, fx, 600, 640 + crop.height * 0.48 - 220, 'GENERADOR', eout(seg(u, ug, ug + 0.2)), size=30, border=AMARILLO)
        if u >= ut:
            doodle_circle(img, fx, 540, 640 + crop.height * 0.45, 330, 230, t, k=seg(u, ut, ut + 0.25), col=CYAN, w=7, seed=5)
            pill(img, fx, 540, 640 + crop.height + 70, '…Y LA TURBINA', eout(seg(u, ut, ut + 0.2)), size=32, border=CYAN)
        credito(img, CRED_M, y=640 + crop.height + 150)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, ug, 0.2), golpe_k(u, ut, 0.2)), amp=10)


# 12. si se rompe, prende el foco rojo: la banda revienta (3D) y el foco salta
def s_revienta(t, fi, u, d):
    uf = Wp(12, 'foco') - 0.1
    ur = Wp(12, 'rompe') - 0.05
    fr = Frame(camara(u, [K(-0.2, 3.6, 20, 10, tx=0.0, ty=1.0, tz=0.3), K(ur, 2.9, -8, 8, tx=0.0, ty=1.0, tz=0.3),
                          K(d, 3.0, -12, 8, tx=0.0, ty=1.0, tz=0.3)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8, beam=0.3)
    draw_objects(fr, motor(giro=t * 14 if u < ur else t * 14 * 0.2), xray=0.0)
    correa(fr, t, rota=P.eout4(seg(u, ur, ur + 0.4)))
    if u > ur:
        for j in range(10):
            ph = seg(u, ur, ur + 0.5)
            a = j * 0.63
            dot3(fr, (0.17 + 0.6 * ph * math.cos(a), Y0 + 0.4 + 0.6 * ph * math.sin(a), 0.7), r=4, col=AMARILLO,
                 a=1 - ph, glow=1.5)

    def ui(img, fx):
        kicker(img, 'SI LA BANDA SE ROMPE…', 150, 1.0, col=ROJO)
        if u > uf:
            sc = P.resorte(seg(u, uf, uf + 0.3))
            tablero(img, fx, 540, 1430, int(190 * max(0.05, sc)), t, foco=1.0, aguja=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, ur, 0.35), golpe_k(u, uf + 0.1, 0.3)), amp=26)


# 13. la turbina se para y el motor se queda sin aire
def s_sinaire(t, fi, u, d):
    up = Wp(13, 'para') - 0.1
    us = Wp(13, 'sin') - 0.1
    vel = 14 * (1 - P.eout4(seg(u, -0.2, up + 0.3)))
    giro = 14 * (u + 0.2) - 14 * 0.5 * (u + 0.2) ** 2 / max(0.2, up + 0.5) if u < up + 0.3 else 3.0
    fr = Frame(camara(u, [K(-0.2, 3.4, 20, 34, ty=0.9), K(us, 3.0, -15, 26, ty=0.9), K(d, 2.9, -20, 26, ty=0.9)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    draw_objects(fr, motor(calor=0.35 * seg(u, us, d), giro=giro), xray=0.75, keep=('in', 'turbina'))
    aire(fr, t, k=1 - seg(u, 0.0, up + 0.3))

    def ui(img, fx):
        kicker(img, 'TURBINA PARADA', 150, 1.0, col=ROJO)
        texto(img, fx, 540, 300, 'sin aire', 104, WHITE, eout(seg(u, us, us + 0.2)), f='serif')
        P.pill_tachada(img, fx, 540, 1380, 'AIRE', 1.0, seg(u, us, us + 0.3), t, size=34, col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. en un par de kilómetros se calienta tanto (al rojo, ondas de calor y termómetro)
def s_calienta(t, fi, u, d):
    uk = Wp(14, 'kilometros') - 0.1
    uc = Wp(14, 'calienta') - 0.1
    c = seg(u, -0.2, uc + 0.6)
    fr = Frame(camara(u, [K(-0.2, 3.8, -40, 18, ty=0.75), K(uc, 3.0, -10, 12, ty=0.75), K(d, 2.8, -4, 12, ty=0.75)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8, beam=0.2)
    draw_objects(fr, motor(calor=0.4 + 0.6 * c, giro=2.0), xray=0.0)
    P.ondas_calor(fr, t, 0.0, Y0 + 0.4, Y0 + 1.6, 1.4, k=c)

    def ui(img, fx):
        kicker(img, 'SIN ENFRIAMIENTO', 150, 1.0, col=NARANJA)
        P.numero_golpe(img, fx, '2 km', 330, seg(u, uk, uk + 0.15), size=150, col=NARANJA)
        P.termometro(img, fx, 860, 1000, 420, 0.3 + 0.68 * c, 'CALOR', k=1.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uk + 0.15, 0.3) + 0.25 * c, amp=8)


# 15. se queman las válvulas y el motor se amarra (corte de la cabeza; chispas; se detiene de golpe)
def s_amarra(t, fi, u, d):
    uv = Wp(15, 'valvulas') - 0.1
    ua = Wp(15, 'amarra') - 0.05
    fr = Frame(camara(u, [K(-0.2, 4.4, 20, 20, tx=0.2, ty=Y0 + 0.2, tz=0.0), K(uv, 2.3, 70, 10, tx=0.7, ty=Y0, tz=0.0),
                          K(ua, 3.4, -30, 14, ty=0.8), K(d, 3.3, -26, 14, ty=0.8)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.8)
    draw_objects(fr, motor(calor=1.0, giro=2.0), xray=0.55 if u < ua else 0.0, keep=('in',))
    # válvula al rojo en la cabeza derecha
    pv = (0.86, Y0 + 0.02, 0.22)
    kv = seg(u, uv, uv + 0.3)
    dot3(fr, pv, r=14 + 30 * kv, col=(255, 120, 60), a=0.5 + 0.5 * kv, glow=2.0)
    if u > uv:
        for j in range(14):
            ph = ((t * 2.2 + j / 14) % 1.0)
            dot3(fr, (pv[0] + 0.5 * ph * math.cos(j), pv[1] + 0.6 * ph, pv[2] + 0.3 * math.sin(j * 2)), r=3, col=(255, 210, 120),
                 a=(1 - ph) * kv, glow=2.0)
    ppv = fr.cam.p1(pv)

    def ui(img, fx):
        kicker(img, 'VÁLVULAS QUEMADAS', 150, 1.0, col=ROJO)
        if uv < u < ua:
            pill(img, fx, ppv[0], ppv[1] - 120, 'VÁLVULA', eout(seg(u, uv, uv + 0.2)), size=30, border=ROJO)
        if u > ua:
            P.titulo_golpe(img, fx, [('…y el motor', 'sans'), ('se amarra.', 'serif')], 280, seg(u, ua, ua + 0.15), size=78, col=ROJO)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if ua <= u < ua + 0.2:
        out = M.tr_glitch(out, out, 0.5, fi) if hasattr(M, 'tr_glitch') else out
    return sacudir(out, t, golpe_k(u, ua, 0.45), amp=30)


# 16. el manual de Volkswagen dice: si prende ese foco, apaga el motor (libro que se abre y la llave a OFF)
def s_manual(t, fi, u, d):
    uap = Wp(16, 'apaga') - 0.1
    fr = Frame(camara(u, [K(-0.2, 6.0, 20, 10, ty=0.8), K(d, 5.6, 10, 10, ty=0.8)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8, beam=0.5)
    ab = P.eout4(seg(u, -0.2, 0.35))
    zk = P.eout4(seg(u, uap - 0.3, uap + 0.1))

    def ui(img, fx):
        kicker(img, 'MANUAL DEL PROPIETARIO', 150, 1.0, col=AZULC)
        s_ = 1.0 + 0.25 * zk
        cx, cy = 540, 980 - 120 * zk
        pw, ph = 380 * s_ * (0.15 + 0.85 * ab), 560 * s_
        d_ = ImageDraw.Draw(img)
        for sgn in (-1, 1):                                   # las dos páginas se abren desde el lomo
            x0, x1 = (cx - pw, cx) if sgn < 0 else (cx, cx + pw)
            d_.rounded_rectangle((x0, cy - ph / 2, x1, cy + ph / 2), radius=10, fill=(222, 216, 200), outline=(120, 110, 96), width=3)
            for j in range(9):
                yy = cy - ph / 2 + 60 * s_ + j * 46 * s_
                if sgn > 0 and 3 <= j <= 6:
                    continue
                ww = pw * (0.55 + 0.3 * ((j * 37 + sgn) % 5) / 5)
                xa = x0 + 30 * s_
                d_.line([(xa, yy), (xa + ww - 60 * s_, yy)], fill=(150, 144, 130), width=max(2, int(7 * s_)))
        d_.line([(cx, cy - ph / 2), (cx, cy + ph / 2)], fill=(90, 84, 72), width=4)
        k = eout(seg(u, 0.3, 0.6)) * ab
        if k > 0.01:
            bx0, by0 = cx + 22 * s_, cy - 40 * s_
            bx1, by1 = cx + pw - 22 * s_, cy + 170 * s_
            d_.rounded_rectangle((bx0, by0, bx1, by1), radius=12, fill=(250, 236, 230), outline=M.scale_c(ROJO, k), width=5)
            r = int(26 * s_)
            fy = by0 + 50 * s_
            d_.ellipse((bx0 + 20 * s_, fy - r, bx0 + 20 * s_ + 2 * r, fy + r), fill=ROJO)
            ImageDraw.Draw(fx).ellipse((bx0 + 20 * s_ - r, fy - 2 * r, bx0 + 20 * s_ + 3 * r, fy + 2 * r), fill=M.scale_c(ROJO, 0.5))
            texto(img, fx, bx0 + 80 * s_, fy, 'Si prende:', int(30 * s_), (40, 30, 30), k, f='sans', glow=0, anchor='lm')
            texto(img, fx, (bx0 + bx1) / 2, by0 + 130 * s_, '¡apaga el motor!', int(36 * s_), (200, 30, 30),
                  eout(seg(u, uap, uap + 0.2)), f='serif', glow=0, anchor='mm')
            if u > uap:
                doodle_circle(img, fx, (bx0 + bx1) / 2, by0 + 130 * s_, 200 * s_, 50 * s_, t, k=seg(u, uap + 0.1, uap + 0.4),
                              col=AMARILLO, w=6, seed=8)
        if u > uap - 0.1:                                     # la llave gira a OFF
            kk = P.eout4(seg(u, uap + 0.15, uap + 0.5))
            kx, ky = 540, 1520
            d_.ellipse((kx - 110, ky - 110, kx + 110, ky + 110), fill=(18, 18, 22), outline=(180, 180, 190), width=5)
            a = math.radians(-60 - 60 * kk)
            d_.line([(kx - 80 * math.cos(a), ky - 80 * math.sin(a)), (kx + 80 * math.cos(a), ky + 80 * math.sin(a))],
                    fill=CROMO, width=26)
            texto(img, fx, kx + 160, ky - 100, 'ON', 34, GRIS, 1.0, f='mono', glow=0)
            texto(img, fx, kx - 170, ky - 100, 'OFF', 34, AMARILLO, 0.3 + 0.7 * kk, f='mono', glow=0.4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uap + 0.5, 0.3), amp=14)


# 17. revisa la banda: bien, floja o rajada (tres bandas con su diagnóstico)
def _banda2d(img, fx, cx, cy, t, tipo, k):
    if k <= 0.01:
        return
    d_ = ImageDraw.Draw(img)
    r1, r2 = 50, 80
    y1, y2 = cy - 180, cy + 120
    d_.ellipse((cx - r1, y1 - r1, cx + r1, y1 + r1), outline=CROMO, width=8)
    d_.ellipse((cx - r2, y2 - r2, cx + r2, y2 + r2), outline=CROMO, width=8)
    sag = 46 if tipo == 'floja' else 0
    col = (80, 80, 86)
    pts_l = [(cx - r1 - 4, y1), (cx - (r1 + r2) / 2 - 6 - sag, (y1 + y2) / 2), (cx - r2 - 4, y2)]
    pts_r = [(cx + r1 + 4, y1), (cx + (r1 + r2) / 2 + 6 + sag * 0.3, (y1 + y2) / 2), (cx + r2 + 4, y2)]
    for L in (pts_l, pts_r):
        d_.line(L, fill=col, width=16, joint='curve')
        d_.line(L, fill=(170, 170, 180), width=3)
    if tipo == 'rajada':
        for j in range(4):
            yy = y1 + 60 + j * 40
            d_.line([(cx + 58, yy), (cx + 82, yy + 10)], fill=ROJO, width=5)
    col_t = {'bien': (120, 240, 160), 'floja': AMARILLO, 'rajada': ROJO}[tipo]
    texto(img, fx, cx, cy + 280, tipo.upper(), 40, col_t, k, f='mono', glow=0.5)


def s_revisa(t, fi, u, d):
    uf = Wp(17, 'floja') - 0.1
    ur = Wp(17, 'rajada') - 0.1
    uc = Wp(17, 'cambiala') - 0.1
    fr = Frame(camara(u, [K(-0.2, 6.0, 0, 8, ty=0.8), K(d, 5.8, 0, 8, ty=0.8)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'ANTES DE SALIR', 150, 1.0, col=AZULC)
        texto(img, fx, 540, 300, 'Revisa la banda', 86, WHITE, eout(seg(u, -0.1, 0.15)), f='serif')
        _banda2d(img, fx, 200, 1000, t, 'bien', P.resorte(seg(u, -0.2, 0.15)))
        _banda2d(img, fx, 540, 1000, t, 'floja', P.resorte(seg(u, uf - 0.1, uf + 0.2)))
        _banda2d(img, fx, 880, 1000, t, 'rajada', P.resorte(seg(u, ur - 0.1, ur + 0.2)))
        if u > uf:
            doodle_circle(img, fx, 540, 960, 150, 260, t, k=seg(u, uf, uf + 0.3), col=AMARILLO, w=6, seed=9)
        if u > ur:
            doodle_circle(img, fx, 880, 960, 150, 260, t, k=seg(u, ur, ur + 0.3), col=ROJO, w=6, seed=10)
        pill(img, fx, 540, 1480, 'CÁMBIALA', eout(seg(u, uc, uc + 0.25)), size=36, border=(120, 240, 160))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.3), amp=12)


# 18 y 19. Puebla lo armó 36 años (1967 → 2003) y casi 1.7 millones de vochos (mapa y gráfica)
MX = [(-117.1, 32.5), (-114.7, 32.7), (-111.0, 31.3), (-108.2, 31.3), (-106.5, 31.8), (-104.5, 29.6), (-102.5, 29.8),
      (-100.3, 28.2), (-99.5, 27.5), (-97.2, 25.9), (-97.7, 22.0), (-97.2, 20.0), (-95.0, 18.6), (-92.0, 18.6),
      (-90.4, 21.2), (-87.0, 21.5), (-87.5, 18.5), (-89.1, 17.8), (-90.4, 17.8), (-91.4, 16.1), (-92.2, 14.6),
      (-94.0, 16.1), (-96.5, 15.7), (-99.8, 16.7), (-102.2, 17.9), (-105.2, 20.4), (-105.7, 22.5), (-108.0, 25.0),
      (-109.4, 26.0), (-111.0, 27.8), (-112.8, 30.0), (-113.6, 31.3), (-114.8, 31.5), (-114.0, 29.5), (-112.0, 27.0),
      (-110.0, 24.0), (-109.5, 23.0), (-110.2, 23.4), (-112.1, 24.8), (-112.1, 26.3), (-114.2, 27.8), (-115.0, 29.5),
      (-117.1, 32.5)]


def gm(lon, lat, y=0.0):
    return np.array([(lon + 100.0) * 0.28, y, -(lat - 23.0) * 0.28])


PUE = (-98.2, 19.04)


def s_puebla(t, fi, u, d):
    u36 = Wp(18, 'treinta') - 0.1
    fr = Frame(camara(u, [K(-0.2, 11.0, 0, 62, tx=0.4, ty=0.0, tz=0.6), K(0.4, 8.0, 12, 56, tx=0.5, ty=0.0, tz=0.9),
                          K(d, 7.6, 14, 56, tx=0.5, ty=0.0, tz=0.9)], cy=0.42))
    space(fr, t, floor=None, bokeh=0.8)
    line3(fr, [gm(lo, la) for lo, la in MX], col=WHITE, w=2.4, a=0.85, glow=0.7)
    p = gm(*PUE, 0.02)
    dot3(fr, p, r=12, col=AMARILLO, glow=1.8)
    for j in range(3):
        ph = (t * 1.2 + j / 3) % 1.0
        q = np.linspace(0, 2 * math.pi, 30)
        line3(fr, [p + np.array([0.7 * ph * math.cos(a), 0, 0.7 * ph * math.sin(a)]) for a in q], col=AMARILLO, w=2,
              a=1 - ph, glow=1.0)
    pp = fr.cam.p1(tuple(p))
    kt = P.eout4(seg(u, u36 - 0.1, u36 + 0.7))

    def ui(img, fx):
        kicker(img, 'VOLKSWAGEN DE MÉXICO · PUEBLA', 150, 1.0, col=AZULC)
        pill(img, fx, pp[0], pp[1] - 70, 'PUEBLA', eout(seg(u, -0.1, 0.15)), size=28, border=AMARILLO)
        d_ = ImageDraw.Draw(img)
        x0, x1, y = 140, 940, 1300
        d_.line([(x0, y), (x0 + (x1 - x0) * kt, y)], fill=AMARILLO, width=8)
        for x, txt, kk in ((x0, '1967', 1.0), (x1, '2003', seg(kt, 0.95, 1.0))):
            d_.ellipse((x - 14, y - 14, x + 14, y + 14), fill=M.scale_c(AMARILLO, max(0.2, kk)))
            texto(img, fx, x, y + 70, txt, 56, WHITE, max(0.2, kk), f='mono', glow=0.3)
        P.numero_golpe(img, fx, '36 años', 1520, seg(u, u36, u36 + 0.15), size=130, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u36 + 0.15, 0.3), amp=14)


def s_millones(t, fi, u, d):
    um = Wp(19, 'millon') - 0.1
    fr = Frame(camara(u, [K(-0.2, 7.0, 0, 20, ty=0.6), K(d, 6.6, 0, 20, ty=0.6)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.9)

    def ui(img, fx):
        kicker(img, 'HECHOS EN MÉXICO', 150, 1.0, col=AZULC)
        v = int(1691542 * P.eout4(seg(u, -0.1, um + 0.5)))
        texto(img, fx, 540, 330, f'{v:,}'.replace(',', ' '), 110, AMARILLO, 1.0, f='mono', glow=0.5)
        ic = icono_vocho(150)
        n = int(30 * seg(u, -0.15, um + 0.4))
        for j in range(n):
            r, c = divmod(j, 5)
            x, y = 200 + c * 170, 620 + r * 120
            kk = P.resorte(seg(u, -0.15 + j * 0.025, 0.05 + j * 0.025))
            if kk <= 0.01:
                continue
            icn = ic.resize((max(2, int(ic.width * kk)), max(2, int(ic.height * kk))))
            img.paste(Image.new('RGB', icn.size, (230, 200, 80) if j % 7 else (240, 240, 245)),
                      (int(x - icn.width / 2), int(y - icn.height / 2)), icn)
        pill(img, fx, 540, 1430, 'CASI 1.7 MILLONES', eout(seg(u, um, um + 0.25)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. mándaselo a quien tuvo un vocho (el vocho real con sus faros, de noche)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.2, 5.0, 50, 5, ty=0.5), K(0.4, 4.4, 20, 4, ty=0.5), K(d, 4.3, 14, 4, ty=0.5)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'desliza')

    def ui(img, fx):
        vocho(img, fx, 540 + e['dy'] * 160, 1250, 380, yaw=0.5 - 0.4 * P.eout4(seg(u, -0.2, 0.6)), t=t)
        P.titulo_golpe(img, fx, [('Mándaselo a quien', 'sans'), ('tuvo un vocho.', 'serif')], 300, seg(u, 0.0, 0.15), size=76)
        credito(img, CRED_V)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55),
                sfx=[(-0.3, 'shimmer', 0.6), (U_R, 'sub', 1.0), (U_R + 0.3, 'bass', 0.9), (2.9, 'bass', 0.7)]),
           dict(desde=1, fn=s_fecha, tr='deslizar', sfx=[(0.0, 'whoosh_suave', 0.6), (0.3, 'click', 0.7), (0.65, 'click', 0.7),
                                                         (1.5, 'click', 0.8), (1.6, 'sub', 0.7)]),
           dict(desde=2, fn=s_numero, tr='golpe', c=(0.5, 0.5), sfx=[(0.1 + 0.25 * j, 'tick', 0.4) for j in range(12)] + [(3.5, 'bass', 0.9)]),
           dict(desde=3, fn=s_atras, tr='giro', c=(0.3, 0.55), sfx=[(0.0, 'whoosh', 0.8), (0.45, 'scribble', 0.6)]),
           dict(desde=4, fn=s_sinagua, tr='cubo', c=(0.5, 0.72), sfx=[(0.08, 'slap', 0.8), (1.0, 'scribble', 0.6), (2.6, 'scribble', 0.6)]),
           dict(desde=5, fn=s_dentro, tr='zoom', sfx=[(0.0, 'whoosh', 0.7), (0.4, 'click', 0.8), (1.4, 'tick', 0.5), (1.55, 'tick', 0.5),
                                                      (1.7, 'tick', 0.5), (1.85, 'tick', 0.5)]),
           dict(desde=6, fn=s_aletas, tr='rebanadas', sfx=[(0.0, 'whoosh_suave', 0.6), (1.2, 'click', 0.8), (1.6, 'click', 0.8)]),
           dict(desde=7, fn=s_turbina, tr='remolino', sfx=[(0.0, 'riser', 0.5), (0.2, 'shimmer', 0.5)]),
           dict(desde=8, fn=s_aceite, tr='wipe', sfx=[(0.3, 'chime_a', 0.6)]),
           dict(desde=9, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(0.0, 'bass', 1.0), (0.15, 'sub', 0.9), (0.6, 'digital', 0.5),
                                                                    (1.7, 'bass', 0.8)]),
           dict(desde=10, fn=s_foco, tr='glitch', sfx=[(0.0, 'whoosh', 0.6), (1.2, 'shimmer', 0.5)]),
           dict(desde=11, fn=s_banda, tr='push', c=(0.5, 0.55), sfx=[(0.6, 'click', 0.7), (1.6, 'click', 0.7), (2.3, 'scribble', 0.6)]),
           dict(desde=12, fn=s_revienta, tr='golpe', c=(0.5, 0.5), sfx=[(0.3, 'burst', 0.9), (0.3, 'sub', 1.0), (1.1, 'digital', 0.6)]),
           dict(desde=13, fn=s_sinaire, tr='deslizar_abajo', sfx=[(0.0, 'whoosh_suave', 0.5), (1.6, 'thud', 0.7)]),
           dict(desde=14, fn=s_calienta, tr='flash', sfx=[(0.3, 'riser', 0.6), (1.0, 'bass', 0.8)]),
           dict(desde=15, fn=s_amarra, tr='glitch', sfx=[(0.6, 'burst', 0.6), (2.0, 'sub', 1.0), (2.0, 'bass', 1.0)]),
           dict(desde=16, fn=s_manual, tr='cubo_izq', sfx=[(0.0, 'slap', 0.7), (3.4, 'click', 0.9), (3.7, 'thud', 0.8)]),
           dict(desde=17, fn=s_revisa, tr='rebanadas', sfx=[(1.4, 'scribble', 0.6), (2.0, 'scribble', 0.6), (2.8, 'chime_b', 0.6)]),
           dict(desde=18, fn=s_puebla, tr='cristal', palabra='36 AÑOS', sfx=[(0.6, 'bass', 0.8), (0.3, 'riser', 0.4)]),
           dict(desde=19, fn=s_millones, tr='mosaico', sfx=[(0.05 + 0.08 * j, 'tick', 0.35) for j in range(14)] + [(1.6, 'chime_c', 0.6)]),
           dict(desde=20, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.8)]),
           dict(desde=21, loop=True, tr='whip')]

if __name__ == '__main__':
    montaje.cli(globals())
