"""Reel diario mar 24-nov-2026 18:00 (propuesto) — «Tu velocímetro… te miente.»
Por regla (Reglamento 39 de la ONU) el velocímetro nunca marca menos de lo que vas y puede marcar de más hasta 10 % + 4 km/h:
a 100 reales puede decir 114. El GPS del celular marca ~96 cuando la aguja dice 100. Error (segundo gancho): poner rines y
llantas más grandes sin recalibrar: el velocímetro cuenta vueltas de la llanta y supone su tamaño; con una llanta 3 % más
grande la aguja dice 100 y vas a 103, y el odómetro se queda corto. El GPS mide tu posición con satélites (en recta, el
más exacto).
Comunidad: automovilistas. Inicio tipo 8 (error en pantalla): la aguja en 100 y junto a ella el celular con el GPS en
«96» rojo que parpadea con falla digital, delante de «MIENTE» de cristal. El final («…tu velocímetro te miente») regresa (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
Sin fotos reales: tablero, celular, sedán sin marca, llantas y sensor son esquemas («ESQUEMA»/«EJEMPLO»).
Datos y fuentes: guiones/2026-11-24_velocimetro.txt.
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
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import texto, esquema, golpe_k, sacudir, K, camara, _B

M3 = M.M3
TEMA = 'velocimetro'
TXT = ['Tu velocímetro… te miente.',
       'Pon el GPS del celular junto a la aguja:',
       'el carro dice 100 y el GPS, 96.',
       'No está descompuesto:',
       'lo hicieron así a propósito.',
       'Una regla de la ONU, la número 39,',
       'dice que nunca puede marcar menos de lo que vas.',
       'Pero sí puede marcar de más:',
       'hasta el 10 %, más 4 km/h.',
       'A 100 de verdad, la aguja puede decir hasta 114',
       'y sigue siendo legal.',
       'Y aquí está el error:',
       'ponerle rines y llantas más grandes sin recalibrarlo.',
       'El velocímetro no ve el piso:',
       'cuenta las vueltas de la llanta y supone su tamaño.',
       'Si la llanta es más grande, cada vuelta avanza más…',
       'y tú vas más rápido de lo que dice la aguja.',
       'Con una llanta 3 % más grande,',
       'la aguja dice 100 y tú vas a 103.',
       'Y el odómetro se queda corto:',
       'cuenta menos kilómetros de los que ya hiciste.',
       '¿Y el GPS? Mide tu posición con satélites,',
       'y en una recta es el más exacto.',
       'Mándaselo a quien jura que su velocímetro es exacto.',
       'Y que cheque el GPS… porque tu velocímetro te miente.']
VOZ = ['Tu velocímetro... te miente.',
       'Pon el GPS del celular junto a la aguja:',
       'el carro dice cien y el GPS, noventa y seis.',
       'No está descompuesto:',
       'lo hicieron así a propósito.',
       'Una regla de la ONU, la número treinta y nueve,',
       'dice que nunca puede marcar menos de lo que vas.',
       'Pero sí puede marcar de más:',
       'hasta el diez por ciento, más cuatro kilómetros por hora.',
       'A cien de verdad, la aguja puede decir hasta ciento catorce',
       'y sigue siendo legal.',
       'Y aquí está el error:',
       'ponerle rines y llantas más grandes sin recalibrarlo.',
       'El velocímetro no ve el piso:',
       'cuenta las vueltas de la llanta y supone su tamaño.',
       'Si la llanta es más grande, cada vuelta avanza más...',
       'y tú vas más rápido de lo que dice la aguja.',
       'Con una llanta tres por ciento más grande,',
       'la aguja dice cien y tú vas a ciento tres.',
       'Y el odómetro se queda corto:',
       'cuenta menos kilómetros de los que ya hiciste.',
       '¿Y el GPS? Mide tu posición con satélites,',
       'y en una recta es el más exacto.',
       'Mándaselo a quien jura que su velocímetro es exacto.',
       'Y que cheque el GPS... porque tu velocímetro te miente.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_velocimetro.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-24_velocimetro_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
ROJO = (255, 60, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (90, 220, 140)
AZUL_GPS = (70, 150, 255)
LLANTA = (24, 24, 27)
CROMO = (190, 192, 198)

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


# ------------------------------------------------------------------ el velocímetro (line-art que brilla)
A0, A1 = 225.0, -45.0        # ángulo de 0 y de 200 km/h (grados, 0 = derecha, sentido antihorario)


def _ang(v):
    return math.radians(A0 + (A1 - A0) * clamp(v / 200.0))


def tablero(img, fx, cx, cy, R, v, k=1.0, rango=None, rojo=0.0, digital=True, etiqueta='KM/H', lectura=None):
    """Velocímetro de aguja (0–200 km/h). rango=(v0, v1, col): arco resaltado. rojo 0–1 tiñe la aguja."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    c = M.scale_c(WHITE, 0.85 * k)
    bb = (cx - R, cy - R, cx + R, cy + R)
    d.ellipse((cx - R - 26, cy - R - 26, cx + R + 26, cy + R + 26), fill=(10, 11, 14), outline=M.scale_c((90, 92, 100), k), width=4)
    d.arc(bb, -A0, -A1, fill=c, width=5)
    df.arc(bb, -A0, -A1, fill=M.scale_c(WHITE, 0.25 * k), width=12)
    if rango:
        v0, v1, col = rango
        a0, a1 = math.degrees(_ang(v0)), math.degrees(_ang(v1))
        d.arc((cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14), -a0, -a1, fill=M.scale_c(col, k), width=22)
        df.arc((cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14), -a0, -a1, fill=M.scale_c(col, 0.6 * k), width=36)
    for j in range(0, 201, 10):
        a = _ang(j)
        r0 = R - (34 if j % 20 == 0 else 18)
        d.line([(cx + r0 * math.cos(a), cy - r0 * math.sin(a)), (cx + R * math.cos(a), cy - R * math.sin(a))], fill=c, width=5 if j % 20 == 0 else 3)
        if j % 40 == 0:
            rt = R - 78
            d.text((cx + rt * math.cos(a), cy - rt * math.sin(a)), str(j), font=M.font('sans', int(R * 0.15)), fill=c, anchor='mm')
    a = _ang(v)
    col = M.mixc((255, 120, 60), ROJO, rojo)
    x1, y1 = cx + (R - 24) * math.cos(a), cy - (R - 24) * math.sin(a)
    d.line([(cx, cy), (x1, y1)], fill=M.scale_c(col, k), width=9)
    df.line([(cx, cy), (x1, y1)], fill=M.scale_c(col, 0.7 * k), width=24)
    d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=(30, 30, 34), outline=M.scale_c(WHITE, 0.6 * k), width=3)
    if digital:
        d.text((cx, cy + R * 0.42), f'{int(round(v))}' if lectura is None else lectura, font=M.font('mono', int(R * 0.3)), fill=c, anchor='mm')
        d.text((cx, cy + R * 0.66), etiqueta, font=M.font('mono', int(R * 0.1)), fill=M.scale_c(GRIS, k), anchor='mm')


def scr_gps(v, rojo=0.0, t=0.0, glitch=0.0):
    """Pantalla del celular con una app de GPS genérica: mapa, punto azul y la velocidad grande."""
    def dib(d, im):
        f = M.font
        for j in range(9):                                   # calles del mapa
            y = 140 + j * 85 + (t * 60) % 85
            d.line([(0, y), (420, y - 60)], fill=(40, 44, 52), width=10)
        d.line([(210, 120), (210, 900)], fill=(60, 66, 80), width=34)
        d.ellipse((190, 430, 230, 470), fill=AZUL_GPS, outline=(255, 255, 255), width=4)
        d.rounded_rectangle((40, 560, 380, 800), radius=30, fill=(12, 13, 16))
        col = M.mixc((240, 240, 244), ROJO, rojo)
        dx = int(12 * glitch * math.sin(t * 90))
        if glitch > 0.05:
            d.text((210 + dx + 6, 660), f'{int(round(v))}', font=f('sansx', 150), fill=(0, 220, 255), anchor='mm')
            d.text((210 + dx - 6, 660), f'{int(round(v))}', font=f('sansx', 150), fill=(255, 30, 60), anchor='mm')
        d.text((210 + dx, 660), f'{int(round(v))}', font=f('sansx', 150), fill=col, anchor='mm')
        d.text((210, 760), 'km/h · GPS', font=f('mono', 30), fill=(150, 150, 160), anchor='mm')
    return P.pantalla(dib)


# ------------------------------------------------------------------ el carro y las llantas (frente hacia +x)
def carro(col=(150, 28, 34), r_ll=0.33, giro_llanta=0.0, ry=0.0):
    ms = []
    ms.append(named(M3.rbox(3.0, 0.5, 1.25, 0.22, col, n=5, shadow=0, gloss=0.8).tf(t=(0, 0.32 + (r_ll - 0.33), 0)), 'cuerpo', rim=0.8, gloss=0.8))
    ms.append(named(M3.rbox(1.55, 0.46, 1.1, 0.25, (30, 34, 42), n=5, shadow=0, gloss=0.95).tf(t=(-0.2, 0.8 + (r_ll - 0.33), 0)), 'vidrio', rim=0.9, gloss=0.95))
    ms.append(named(M3.rbox(1.3, 0.06, 1.0, 0.2, col, n=4, shadow=0, gloss=0.8).tf(t=(-0.22, 1.25 + (r_ll - 0.33), 0)), 'cuerpo', rim=0.8))
    for x in (1.0, -1.0):
        for z in (0.6, -0.68):
            ms += rueda(r_ll, (x, r_ll, z + 0.1), giro_llanta)
    dy = r_ll - 0.33
    for z in (-0.45, 0.45):
        _B(ms, 0.04, 0.12, 0.26, (255, 248, 230), 1.5, 0.55 + dy, z, glow=(160, 150, 120))
        _B(ms, 0.04, 0.1, 0.26, (200, 30, 30), -1.5, 0.58 + dy, z, glow=(120, 20, 20))
    return P.tfk(ms, ry=ry) if ry else ms


def rueda(r, c, giro=0.0, ancho=0.2, marca=True):
    ms = [named(M3.cyl(r, ancho, LLANTA, n=26, shadow=0, gloss=0.15, y0=-ancho / 2).tf(rx=90, t=c), 'llanta', rim=0.35),
          named(M3.cyl(r * 0.6, ancho + 0.01, CROMO, n=16, shadow=0, gloss=0.85, y0=-ancho / 2 - 0.005).tf(rx=90, t=c), 'rin', rim=0.7)]
    for j in range(5):                                        # rayos del rin: dejan ver que gira
        a = giro + j * 2 * math.pi / 5
        b = M3.box(r * 0.5, 0.05, 0.03, (120, 122, 130), shadow=0, base=False).tf(rz=math.degrees(a), t=(c[0] + r * 0.28 * math.cos(a), c[1] + r * 0.28 * math.sin(a), c[2] + ancho / 2 + 0.02))
        ms.append(named(b, 'rin', rim=0.6))
    if marca:
        b = M3.box(0.06, r * 0.32, 0.03, AMARILLO, shadow=0, base=False).tf(rz=math.degrees(giro), t=(c[0] + r * 0.82 * math.cos(giro + math.pi / 2), c[1] + r * 0.82 * math.sin(giro + math.pi / 2), c[2] + ancho / 2 + 0.02))
        ms.append(named(b, 'marca', glow=M.scale_c(AMARILLO, 0.4)))
    return ms


def flecha(img, fx, x0, y0, x1, y1, col, k=1.0, w=8):
    if k <= 0.01:
        return
    x1, y1 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    df.line([(x0, y0), (x1, y1)], fill=M.scale_c(col, 0.6), width=w * 3)
    a = math.atan2(y1 - y0, x1 - x0)
    L = 26 + w
    for s in (-1, 1):
        d.line([(x1, y1), (x1 - L * math.cos(a + s * 0.5), y1 - L * math.sin(a + s * 0.5))], fill=col, width=w)


def carretera(fr, t, vel=1.0, a=0.8, ancho=1.6):
    for z in (-ancho, ancho):
        line3(fr, [(-8, 0.01, z), (8, 0.01, z)], col=WHITE, w=2.4, a=a, glow=0.5)
    for j in range(12):
        x = -8 + ((j * 1.4 - t * 6 * vel) % 16.8)
        line3(fr, [(x, 0.01, 0), (x + 0.7, 0.01, 0)], col=AMARILLO, w=3, a=a, glow=0.6)


# ================================================================== escenas
UG = 0.3     # golpe del título en el gancho


# 0. gancho, inicio tipo 8 (error en pantalla): aguja en 100 y el GPS en «96» rojo con falla digital; «MIENTE» de cristal
def s_gancho(t, fi, u, d):
    pose = P.cam_rapida(u, [K(-4.0, 3.2, -30, 6, tx=0.9, ty=1.2), K(-2.0, 3.0, -14, 4, tx=0.9, ty=1.2),
                            K(UG, 2.9, -8, 4, tx=0.9, ty=1.2), K(UG + 0.3, 3.3, 10, 6, tx=0.9, ty=1.2), K(3.0, 3.4, 14, 6, tx=0.9, ty=1.2)])
    fr = Frame(camara(u, [(0, pose)] , cy=0.56))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'MIENTE', u, t0=-2.6, cy=0.3, entrada='golpe')
    gl = 1.0 if (int(t * 6) % 3 == 0) else 0.3
    draw_objects(fr, P.celular(scr_gps(96, rojo=1.0, t=t, glitch=gl), ry=-18, off=(1.25, 0.05, 0.2)))

    def ui(img, fx):
        v = 100 + 1.2 * math.sin(t * 3)
        tablero(img, fx, 330, 1050, 250, v, k=1.0, lectura='100')
        texto(img, fx, 330, 1380, 'TABLERO', 30, GRIS, 1.0, f='mono', glow=0.0)
        if int(t * 4) % 2 == 0:
            texto(img, fx, 600, 1020, '≠', 120, ROJO, 1.0, f='sansx', glow=0.6)
        kicker(img, 'VELOCÍMETRO CONTRA GPS', 140, seg(u, UG, UG + 0.3), col=(255, 140, 130))
        P.titulo_golpe(img, fx, [('Tu velocímetro…', 'sans'), ('te miente.', 'serif')], 190, seg(u, UG, UG + 0.15), size=96)
        pill(img, fx, 780, 1460, 'EJEMPLO', 1.0, size=20, border=GRIS, dot=False)
    fr.ui.append(ui)
    img = finish(fr, fi)
    if int(t * 6) % 3 == 0:                                     # parpadeo de falla digital en todo el cuadro
        img = img.copy()
        img[:, :, 0] = np.roll(img[:, :, 0], 6, axis=1)
        img[:, :, 2] = np.roll(img[:, :, 2], -6, axis=1)
    return sacudir(img, t, golpe_k(u, UG + 0.15, 0.35), amp=22)


# 1. pon el GPS del celular junto a la aguja (el celular cae girando al lado del tablero)
def s_pon(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.2, 40, 20, tx=0.6, ty=1.0), K(0.35, 3.3, 0, 6, tx=0.6, ty=1.1), K(5, 3.25, -6, 6, tx=0.6, ty=1.1)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.15, 0.4, 'cae')
    ug = Wp(1, 'aguja') - 0.1
    draw_objects(fr, P.celular(scr_gps(97 + math.sin(t * 2), t=t), ry=-14 + 40 * (1 - P.eout4(seg(u, -0.15, 0.5))), off=(1.25, max(0.0, -e['dy']), 0.2)))

    def ui(img, fx):
        tablero(img, fx, 330, 1050, 250, 100 + math.sin(t * 3), k=1.0, lectura='100')
        kicker(img, 'LA PRUEBA · CELULAR AL LADO', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > ug:
            doodle_circle(img, fx, 330, 1050, 290, 290, t, k=seg(u, ug, ug + 0.4), col=WHITE, seed=2)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.3), amp=14)


# 2. el carro dice 100 y el GPS 96 (pantalla dividida: los dos números golpean)
def s_100_96(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -10, 10), K(0.3, 4.6, 0, 8), K(5, 4.5, 3, 8)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.3)
    u1, u2 = Wp(2, 'cien') - 0.05, Wp(2, 'noventa') - 0.05

    def ui(img, fx):
        d_ = ImageDraw.Draw(img)
        d_.line([(540, 380), (540, 1420)], fill=(80, 80, 88), width=3)
        texto(img, fx, 290, 470, 'TABLERO', 40, GRIS, seg(u, -0.1, 0.2), f='mono', glow=0.0)
        texto(img, fx, 790, 470, 'GPS', 40, AZUL_GPS, seg(u, -0.1, 0.2), f='mono', glow=0.3)
        tablero(img, fx, 290, 860, 200, 100 * P.eout4(seg(u, -0.2, u1 + 0.2)), k=1.0, digital=False)
        if u > u1:
            P.numero_golpe(img, fx, '100', 1200, seg(u, u1, u1 + 0.18), size=200, col=WHITE)
        if u > u2:
            texto(img, fx, 790, 1200, '96', 210, AZUL_GPS, seg(u, u2, u2 + 0.12), f='sansx', glow=0.6)
        kg = eout(seg(u, -0.2, 0.2))
        if kg > 0:
            r_ = 70 * P.resorte(kg)
            d_.ellipse((790 - r_, 860 - r_, 790 + r_, 860 + r_), outline=AZUL_GPS, width=10)
            d_.ellipse((790 - r_ * 0.45, 860 - r_ * 0.45, 790 + r_ * 0.45, 860 + r_ * 0.45), fill=AZUL_GPS)
            ImageDraw.Draw(fx).ellipse((790 - r_ * 1.6, 860 - r_ * 1.6, 790 + r_ * 1.6, 860 + r_ * 1.6), fill=M.scale_c(AZUL_GPS, 0.3))
        pill(img, fx, 540, 1440, 'EJEMPLO · DIFERENCIA TÍPICA 2 A 8 KM/H', eout(seg(u, u2 + 0.3, u2 + 0.6)), size=22, border=GRIS, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, u1 + 0.18, 0.25), golpe_k(u, u2 + 0.12, 0.25)), amp=16)


# 3. no está descompuesto (el carro llega derrapando; «DESCOMPUESTO» se tacha)
def s_descompuesto(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 60, 18, ty=0.7), K(0.35, 5.2, 28, 12, ty=0.7), K(5, 5.1, 22, 12, ty=0.7)]))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.25, 0.35, 'desliza')
    draw_objects(fr, P.tfk(carro(giro_llanta=-t * 6), ry=20 * (1 - P.eout4(seg(u, -0.25, 0.3))), t=(-e['dy'], 0, 0)))

    def ui(img, fx):
        P.pill_tachada(img, fx, 540, 420, 'DESCOMPUESTO', seg(u, 0.1, 0.3), seg(u, 0.5, 0.9), t, size=44, col=WHITE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. lo hicieron así a propósito (el carro sobre rodillos de prueba en la fábrica; «PROPÓSITO» de cristal)
def s_proposito(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, -50, 24, ty=0.6), K(0.35, 5.2, -20, 12, ty=0.7), K(5, 5.2, -14, 12, ty=0.7)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.6)
    M.cristal(fr.base, fr.fx, 'PROPÓSITO', u, t0=0.0, cy=0.3, entrada='sube')
    ms = carro(giro_llanta=-t * 10)
    for x in (1.0, -1.0):                                       # rodillos del banco de pruebas
        for dz in (-0.25, 0.25):
            ms.append(named(M3.cyl(0.14, 1.7, (90, 92, 100), n=16, shadow=0, gloss=0.8, y0=-0.85).tf(rx=90, t=(x + dz, -0.04, 0)), 'rodillo', rim=0.7))
    draw_objects(fr, P.tfk(ms, t=(0, 0.1, 0)))

    def ui(img, fx):
        kicker(img, 'CALIBRADO DE FÁBRICA', 1240, seg(u, 0.2, 0.5), col=AZULC)
        pill(img, fx, 540, 1320, 'MARCA UN POCO DE MÁS · A PROPÓSITO', eout(seg(u, 0.5, 0.8)), size=28, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def documento(img, fx, k, t, cx=540, cy=820, w=720):
    if k <= 0.01:
        return
    h = int(w * 1.12)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=12, fill=(244, 242, 236, 255))
    dl.text((w / 2, 90), 'REGLAMENTO N.º 39', font=M.font('sansx', 56), fill=(20, 20, 24, 255), anchor='mm')
    dl.text((w / 2, 150), 'VELOCÍMETROS · ONU (CEPE)', font=M.font('mono', 28), fill=(90, 90, 96, 255), anchor='mm')
    dl.line([(60, 200), (w - 60, 200)], fill=(180, 178, 170, 255), width=3)
    lines = ['5.3  La velocidad indicada', 'no debe ser menor que la', 'velocidad real del vehículo.', '',
             '0 ≤ (V1 − V2) ≤ 0.1 V2 + 4 km/h']
    for j, ln in enumerate(lines):
        dl.text((60, 250 + j * 70), ln, font=M.font('sanss' if j < 4 else 'mono', 40 if j < 4 else 36), fill=(30, 30, 34, 255))
    dl.text((w / 2, h - 50), 'TRADUCCIÓN · ILUSTRACIÓN', font=M.font('mono', 22), fill=(120, 120, 126, 255), anchor='mm')
    drop = eout(clamp(k * 1.5), 3)
    tt = max(0.0, k - 0.65)
    ang = -8 * (1 - drop) + 4.0 * math.exp(-5 * tt) * math.cos(12 * tt) * (1 if k > 0.65 else 0) - 2
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    y = cy - 700 * (1 - drop)
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 160), (0, 0), lay.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    img.paste(sh, (int(cx - lay.width / 2) + 16, int(y - lay.height / 2) + 24), sh)
    img.paste(lay, (int(cx - lay.width / 2), int(y - lay.height / 2)), lay)


# 5. una regla de la ONU, la número 39 (cae el documento; el «39» golpea)
def s_onu(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 30, 30), K(0.4, 5.4, 4, 22), K(5, 5.3, 0, 22)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.6)
    u39 = Wp(5, 'treinta') - 0.05

    def ui(img, fx):
        kicker(img, 'LA REGLA', 150, seg(u, -0.1, 0.2), col=AZULC)
        documento(img, fx, seg(u, -0.15, 0.5), t)
        if u > u39:
            P.numero_golpe(img, fx, '39', 1380, seg(u, u39, u39 + 0.18), size=200, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.5, 0.25), golpe_k(u, u39 + 0.18, 0.3)), amp=14)


def barras(img, fx, u, real, marca, k, y0=1250, col_m=WHITE, txt_m='MARCA'):
    d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    H = 620
    for j, (v, col, txt) in enumerate(((real, AZUL_GPS, 'VAS'), (marca, col_m, txt_m))):
        x = 360 + j * 360
        h = H * v / 120 * k
        d_.rounded_rectangle((x - 80, y0 - h, x + 80, y0), radius=14, fill=M.scale_c(col, 0.85))
        df.rounded_rectangle((x - 80, y0 - h, x + 80, y0), radius=14, fill=M.scale_c(col, 0.25))
        texto(img, fx, x, y0 - h - 50, f'{int(round(v * k))}', 64, col, k, f='mono', glow=0.3)
        texto(img, fx, x, y0 + 50, txt, 34, GRIS, k, f='mono', glow=0.0)


# 6. nunca puede marcar menos de lo que vas (barras: vas 100, marca 92 → ✗ prohibido)
def s_menos(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -30, 10), K(0.3, 4.6, -6, 8), K(5, 4.5, 0, 8)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.3)
    um = Wp(6, 'menos') - 0.1

    def ui(img, fx):
        kicker(img, 'LO QUE NO SE PERMITE', 150, seg(u, -0.1, 0.2), col=(255, 140, 130))
        barras(img, fx, u, 100, 92, eout(seg(u, -0.35, 0.3)), col_m=ROJO)
        if u > um:
            N.doodle_arrow_free(img, fx, 560, 520, 900, 1260, t, seg(u, um, um + 0.3), ROJO, seed=3)
            N.doodle_arrow_free(img, fx, 900, 520, 560, 1260, t, seg(u, um + 0.1, um + 0.4), ROJO, seed=4)
            pill(img, fx, 540, 1400, '✗ MARCAR MENOS: PROHIBIDO', eout(seg(u, um + 0.2, um + 0.5)), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. pero sí puede marcar de más (barras: vas 100, marca 106 → ✓)
def s_mas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 30, 10), K(0.3, 4.6, 6, 8), K(5, 4.5, 0, 8)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.3)

    def ui(img, fx):
        kicker(img, 'LO QUE SÍ SE PERMITE', 150, seg(u, -0.1, 0.2), col=VERDE)
        barras(img, fx, u, 100, 106, eout(seg(u, -0.35, 0.3)), col_m=VERDE)
        flecha(img, fx, 900, 900, 900, 640, VERDE, k=eout(seg(u, 0.4, 0.8)), w=9)
        pill(img, fx, 540, 1400, '✓ MARCAR DE MÁS', eout(seg(u, 0.5, 0.8)), size=32, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. hasta el 10 %, más 4 km/h (la fórmula golpea por partes)
def s_formula(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.4, 0, 30), K(0.3, 5.0, 0, 12), K(5, 4.9, 4, 12)]))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=1.0, beam=0.5)
    u10, u4 = Wp(8, 'diez') - 0.05, Wp(8, 'cuatro') - 0.05
    M.cristal(fr.base, fr.fx, '+10%', u, t0=u10, cy=0.32, entrada='golpe')

    def ui(img, fx):
        kicker(img, 'MARGEN MÁXIMO', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1100, '+10 %', 150, AMARILLO, seg(u, u10, u10 + 0.15), f='sansx', glow=0.5)
        texto(img, fx, 540, 1290, '+ 4 KM/H', 110, WHITE, seg(u, u4, u4 + 0.15), f='sansx', glow=0.4)
        texto(img, fx, 540, 1420, 'DE LA VELOCIDAD REAL', 32, GRIS, seg(u, u4 + 0.2, u4 + 0.4), f='mono', glow=0.0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, u10 + 0.15, 0.25), golpe_k(u, u4 + 0.15, 0.25)), amp=14)


# 9. a 100 de verdad, la aguja puede decir hasta 114 (el arco de 100 a 114 se ilumina; «114» de cristal)
def s_114(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, -20, 6), K(0.35, 3.6, 4, 4), K(5, 3.5, 8, 4)]))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    u114 = Wp(9, 'ciento') - 0.1
    M.cristal(fr.base, fr.fx, '114', u, t0=u114, cy=0.22, entrada='zoom')
    v = 100 + 14 * P.eout4(seg(u, u114, u114 + 0.6))

    def ui(img, fx):
        tablero(img, fx, 540, 1020, 360, v, k=1.0, rango=(100, 114, AMARILLO))
        texto(img, fx, 540, 1480, 'VAS A 100 DE VERDAD', 36, AZUL_GPS, seg(u, 0.0, 0.3), f='mono', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u114 + 0.6, 0.3), amp=14)


# 10. y sigue siendo legal (un sello «LEGAL» se estampa)
def s_legal(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, 10, 6), K(0.3, 3.8, -6, 4), K(5, 3.8, -10, 4)]))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    ks = seg(u, 0.25, 0.4)

    def ui(img, fx):
        tablero(img, fx, 540, 1000, 330, 114, k=0.55, rango=(100, 114, AMARILLO))
        if ks > 0:
            s = 2.2 - 1.2 * P.eout4(ks)
            lay = Image.new('L', (700, 300), 0)
            dl = ImageDraw.Draw(lay)
            dl.rounded_rectangle((10, 10, 690, 290), radius=40, outline=255, width=18)
            dl.text((350, 150), 'LEGAL', font=M.font('sansx', 170), fill=255, anchor='mm')
            lay = lay.rotate(-12, expand=True).resize((int(760 * s), int(420 * s)))
            a = lay.point(lambda q: int(q * min(1, ks * 3)))
            img.paste(Image.new('RGB', lay.size, VERDE), (540 - lay.size[0] // 2, 1000 - lay.size[1] // 2), a)
            fx.paste(Image.new('RGB', lay.size, M.scale_c(VERDE, 0.5)), (540 - lay.size[0] // 2, 1000 - lay.size[1] // 2), a.filter(ImageFilter.GaussianBlur(8)))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.4, 0.35), amp=22)


# 11. SEGUNDO GANCHO: y aquí está el error (rines gigantes; «RINES» de cristal)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 50, 16, ty=0.8), K(0.25, 5.0, 24, 8, ty=0.8), K(5, 4.9, 20, 8, ty=0.8)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'RINES', u, t0=-0.15, cy=0.3, entrada='golpe')
    draw_objects(fr, carro(col=(40, 42, 50), r_ll=0.46, giro_llanta=-t * 4))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, -0.1, 0.1), col=(255, 140, 130))
        P.titulo_golpe(img, fx, [('Y aquí está', 'sans'), ('el error.', 'serif')], 200, seg(u, 0.05, 0.2), size=96)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.4), amp=24)


# 12. rines y llantas más grandes sin recalibrarlo (las llantas crecen; el velocímetro con «SIN RECALIBRAR»)
def s_grandes(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 30, 6, ty=0.7), K(0.3, 4.6, 6, 4, ty=0.7), K(5, 4.5, 2, 4, ty=0.7)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    ug = Wp(12, 'grandes') - 0.2
    r = 0.33 + 0.13 * P.resorte(seg(u, ug, ug + 0.5))
    draw_objects(fr, carro(col=(40, 42, 50), r_ll=r, giro_llanta=-t * 4))
    ur = Wp(12, 'recalibrarlo') - 0.1

    def ui(img, fx):
        p = fr.cam.p1((1.0, r, 0.7))
        pill(img, fx, p[0] + 80, p[1] - 260, 'LLANTA MÁS GRANDE', eout(seg(u, ug + 0.2, ug + 0.5)), size=28, border=AMARILLO)
        P.pill_tachada(img, fx, 540, 1330, 'RECALIBRAR', seg(u, ur, ur + 0.2), seg(u, ur + 0.3, ur + 0.6), t, size=40, col=WHITE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. el velocímetro no ve el piso (debajo del carro: el sensor de la rueda con su anillo dentado)
def s_sensor(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.0, -20, 10, tx=1.0, ty=0.36, tz=0.7), K(0.35, 1.5, -40, 4, tx=1.0, ty=0.36, tz=0.7),
                          K(5, 1.45, -46, 4, tx=1.0, ty=0.36, tz=0.7)]))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.8)
    g = -t * 5
    ms = rueda(0.33, (1.0, 0.33, 0.7), g)
    for j in range(24):                                     # anillo dentado (tono) detrás del rin
        a = g + j * 2 * math.pi / 24
        b = M3.box(0.04, 0.05, 0.04, (170, 172, 180), shadow=0, base=False).tf(rz=math.degrees(a), t=(1.0 + 0.17 * math.cos(a), 0.33 + 0.17 * math.sin(a), 0.42))
        ms.append(named(b, 'tono', rim=0.7, gloss=0.8))
    ms.append(named(M3.rbox(0.08, 0.2, 0.08, 0.02, (60, 62, 70), n=2, shadow=0, gloss=0.5).tf(t=(1.0, 0.52, 0.42)), 'sensor', rim=0.6, glow=(30, 80, 110)))
    draw_objects(fr, ms, xray=0.55, keep=('tono', 'sensor', 'marca'))
    pulso = (math.sin(t * 40) > 0.3)

    def ui(img, fx):
        kicker(img, 'SENSOR DE LA RUEDA', 150, seg(u, -0.1, 0.2), col=AZULC)
        x, y, _ = fr.cam.p1((1.0, 0.72, 0.42))
        d_ = ImageDraw.Draw(img)
        if pulso:
            d_.ellipse((x - 16, y - 16, x + 16, y + 16), fill=CYAN)
            ImageDraw.Draw(fx).ellipse((x - 40, y - 40, x + 40, y + 40), fill=M.scale_c(CYAN, 0.6))
        pill(img, fx, x, y - 120, 'CUENTA DIENTES QUE PASAN', eout(seg(u, 0.4, 0.7)), size=26, border=CYAN)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. cuenta las vueltas de la llanta y supone su tamaño (la llanta rueda, contador de vueltas, cota «SUPONE»)
def s_vueltas(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.2, 30, 8, ty=0.6), K(0.35, 3.6, 0, 4, ty=0.6), K(5, 3.55, -4, 4, ty=0.6)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.3)
    r = 0.55
    vueltas = max(0.0, u) * 0.6
    x = -1.6 + 2 * math.pi * r * vueltas * 0.5
    draw_objects(fr, rueda(r, (x, r, 0), -vueltas * 2 * math.pi, ancho=0.3))
    us = Wp(14, 'supone') - 0.1

    def ui(img, fx):
        texto(img, fx, 540, 420, f'VUELTAS: {int(vueltas)}', 70, WHITE, seg(u, 0.0, 0.2), f='mono', glow=0.3)
        if u > us:
            a = fr.cam.p1((x, 0.0, 0.3))
            b = fr.cam.p1((x, 2 * r, 0.3))
            k = eout(seg(u, us, us + 0.3))
            flecha(img, fx, b[0] + 230, (a[1] + b[1]) / 2, b[0] + 230, b[1], AMARILLO, k=k, w=6)
            flecha(img, fx, b[0] + 230, (a[1] + b[1]) / 2, b[0] + 230, a[1], AMARILLO, k=k, w=6)
            pill(img, fx, b[0] + 230, (a[1] + b[1]) / 2, 'SUPONE: DE FÁBRICA', k, size=26, border=AMARILLO, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. si la llanta es más grande, cada vuelta avanza más (caso 1 contra caso 2: una vuelta de cada una, desenrollada)
def s_avanza(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -24, 14, ty=0.9), K(0.35, 4.4, 0, 6, ty=0.9), K(5, 4.35, 3, 6, ty=0.9)]))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)
    k = P.eout4(seg(u, 0.2, 1.8))
    ms = []
    lineas = []
    for j, (r, y, col) in enumerate(((0.36, 1.5, WHITE), (0.46, 0.0, AMARILLO))):
        x0 = -1.6
        x = x0 + 2 * math.pi * r * k
        ms += rueda(r, (x, y + r, 0), -k * 2 * math.pi, ancho=0.24)
        lineas.append(((x0, y, 0.15), (x, y, 0.15), col, r))
    draw_objects(fr, ms)
    for a, b, col, r in lineas:
        line3(fr, [a, b], col=col, w=6, a=0.95, glow=1.0)
        line3(fr, [(a[0], a[1] - 0.05, 0.15), (a[0], a[1] + 0.05, 0.15)], col=col, w=3, a=0.9)

    def ui(img, fx):
        kicker(img, 'UNA VUELTA DE CADA UNA', 150, seg(u, -0.1, 0.2), col=AZULC)
        for a, b, col, r in lineas:
            p = fr.cam.p1(b)
            texto(img, fx, p[0], p[1] + 50, 'DE FÁBRICA' if col == WHITE else 'MÁS GRANDE', 26, col, seg(u, 0.2, 0.4), f='mono', glow=0.2)
        if k > 0.98:
            pill(img, fx, 540, 1400, 'MÁS GRANDE = AVANZA MÁS', eout(seg(u, 1.9, 2.2)), size=30, border=AMARILLO, dot=False)
        esquema(img, fx, 1.0, y=1470)
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. y tú vas más rápido de lo que dice la aguja (el carro en la carretera con líneas de velocidad; aguja que se queda corta)
def s_rapido(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.5, 70, 14, ty=0.7), K(0.3, 5.0, 35, 10, ty=0.7), K(5, 4.9, 30, 10, ty=0.7)]))
    space(fr, t, floor=None, bokeh=1.0, beam=0.2)
    carretera(fr, t, vel=1.6)
    draw_objects(fr, carro(col=(40, 42, 50), r_ll=0.42, giro_llanta=-t * 14))
    for j in range(8):
        y = 0.3 + j * 0.12
        x = -1.8 - ((t * 5 + j * 0.7) % 2.5)
        line3(fr, [(x, y, 0.2 * math.sin(j)), (x - 0.8, y, 0.2 * math.sin(j))], col=WHITE, w=2, a=0.6, glow=0.5)

    def ui(img, fx):
        tablero(img, fx, 540, 1250, 190, 100, k=1.0, digital=True)
        texto(img, fx, 540, 1500, 'VAS MÁS RÁPIDO', 40, ROJO, seg(u, 0.4, 0.6), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. con una llanta 3 % más grande («+3%» de cristal; transición cristal)
def s_3(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.2, -30, 6, ty=0.5), K(0.35, 2.8, -8, 4, ty=0.5), K(5, 2.75, -4, 4, ty=0.5)]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.4)
    r = 0.45 * (1 + 0.03 * seg(u, 0.3, 0.9) * 4)
    draw_objects(fr, rueda(r, (0, r, 0), -t * 2, ancho=0.3))

    def ui(img, fx):
        a = fr.cam.p1((0, 0, 0.3))
        b = fr.cam.p1((0, 2 * r, 0.3))
        flecha(img, fx, b[0] + 330, (a[1] + b[1]) / 2, b[0] + 330, b[1], AMARILLO, k=1.0, w=6)
        flecha(img, fx, b[0] + 330, (a[1] + b[1]) / 2, b[0] + 330, a[1], AMARILLO, k=1.0, w=6)
        texto(img, fx, b[0] + 330, (a[1] + b[1]) / 2, '+3 %', 70, AMARILLO, 1.0, f='sansx', glow=0.5)
        esquema(img, fx, 1.0, y=1440, txt='ESQUEMA · CRECIMIENTO EXAGERADO')
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. la aguja dice 100 y tú vas a 103 (tablero contra GPS; «103» rojo golpea)
def s_103(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, 20, 8, tx=0.9, ty=1.2), K(0.3, 3.6, -6, 4, tx=0.9, ty=1.2), K(5, 3.55, -10, 4, tx=0.9, ty=1.2)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.4)
    u103 = Wp(18, 'ciento') - 0.05
    v = 96 + 7 * P.eout4(seg(u, u103, u103 + 0.3))
    draw_objects(fr, P.celular(scr_gps(v, rojo=seg(u, u103, u103 + 0.2), t=t), ry=-18, off=(1.25, 0.05, 0.2)))

    def ui(img, fx):
        tablero(img, fx, 330, 1050, 250, 100 + 0.6 * math.sin(t * 3), k=1.0, lectura='100')
        texto(img, fx, 330, 1380, 'DICE 100', 34, WHITE, seg(u, 0.0, 0.2), f='mono', glow=0.2)
        texto(img, fx, 780, 1460, 'VAS A 103', 40, ROJO, seg(u, u103, u103 + 0.2), f='sansx', glow=0.5)
        pill(img, fx, 780, 1530, 'EJEMPLO', 1.0, size=20, border=GRIS, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u103 + 0.3, 0.3), amp=16)


def odometro(img, fx, cx, cy, km, k=1.0, col=WHITE, digitos=6):
    """Odómetro de tambores: los dígitos ruedan (el último se ve a medio cambiar)."""
    if k <= 0.01:
        return
    d_ = ImageDraw.Draw(img)
    w, h = 104, 160
    x0 = cx - w * digitos / 2
    d_.rounded_rectangle((x0 - 16, cy - h / 2 - 16, x0 + w * digitos + 16, cy + h / 2 + 16), radius=18, fill=(14, 14, 18), outline=M.scale_c(GRIS, k), width=4)
    f = M.font('mono', 120)
    for j in range(digitos):
        p = 10 ** (digitos - 1 - j)
        val = km / p
        dig = int(val) % 10
        frac = (val - int(val)) if j == digitos - 1 else max(0.0, (val % 1) * 10 - 9) if False else 0.0
        x = x0 + j * w + w / 2
        lay = Image.new('L', (w, h), 0)
        dl = ImageDraw.Draw(lay)
        dl.text((w / 2, h / 2 - frac * h), str(dig), font=f, fill=255, anchor='mm')
        dl.text((w / 2, h / 2 + h - frac * h), str((dig + 1) % 10), font=f, fill=255, anchor='mm')
        img.paste(Image.new('RGB', (w, h), M.scale_c(col, k)), (int(x - w / 2), int(cy - h / 2)), lay)
        d_.line([(x + w / 2, cy - h / 2), (x + w / 2, cy + h / 2)], fill=(50, 50, 56), width=2)


# 19. y el odómetro se queda corto (tambores que ruedan)
def s_odometro(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, 40, 10), K(0.3, 3.8, 10, 6), K(5, 3.75, 6, 6)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)

    def ui(img, fx):
        kicker(img, 'ODÓMETRO', 600, seg(u, -0.1, 0.2), col=AZULC)
        odometro(img, fx, 540, 860, 45230 + max(0, u) * 3.1, k=1.0)
        texto(img, fx, 540, 1040, 'KM', 40, GRIS, 1.0, f='mono', glow=0.0)
        pill(img, fx, 540, 1180, 'SE QUEDA CORTO', eout(seg(u, 0.5, 0.8)), size=34, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 20. cuenta menos kilómetros de los que ya hiciste (dos contadores: real 100 contra odómetro 97; «KM» de cristal)
def s_menos_km(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, -40, 10), K(0.3, 3.8, -8, 6), K(5, 3.75, -4, 6)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.4)
    k = P.eout4(seg(u, 0.0, 1.6))

    def ui(img, fx):
        texto(img, fx, 540, 520, 'HICISTE', 36, AZUL_GPS, 1.0, f='mono', glow=0.2)
        odometro(img, fx, 540, 640, 100 * k, k=1.0, col=AZUL_GPS, digitos=3)
        texto(img, fx, 540, 900, 'CUENTA', 36, WHITE, 1.0, f='mono', glow=0.0)
        odometro(img, fx, 540, 1020, 97 * k, k=1.0, col=WHITE, digitos=3)
        pill(img, fx, 540, 1250, '−3 KM DE CADA 100', eout(seg(u, 1.4, 1.7)), size=34, border=ROJO, dot=False)
        pill(img, fx, 540, 1330, 'EJEMPLO CON LLANTA +3 %', eout(seg(u, 1.5, 1.8)), size=22, border=GRIS, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. ¿y el GPS? mide tu posición con satélites (la Tierra de alambre con satélites; «GPS» de cristal)
def s_gps(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.5, 0, 8, ty=1.25), K(0.4, 6.4, 24, 14, ty=1.25), K(5, 6.3, 30, 14, ty=1.25)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.2)
    M.cristal(fr.base, fr.fx, 'GPS', u, t0=-0.1, cy=0.24, entrada='zoom')
    C = np.array([0, 1.25, 0])
    spin = t * 0.4
    camdir = M.norm(fr.cam.pos - C)
    for lat in range(-60, 90, 30):
        th = np.linspace(0, 2 * math.pi, 80)
        r = math.cos(math.radians(lat))
        Pp = np.stack([r * np.cos(th), np.full_like(th, math.sin(math.radians(lat))), r * np.sin(th)], 1)
        D._seg_by_depth(fr, D._rot(Pp, spin), C, camdir)
    for lon in range(0, 180, 30):
        th = np.linspace(0, 2 * math.pi, 80)
        a = math.radians(lon)
        Pp = np.stack([np.cos(th) * math.cos(a), np.sin(th), np.cos(th) * math.sin(a)], 1)
        D._seg_by_depth(fr, D._rot(Pp, spin), C, camdir)
    yo = C + np.array([0.3, 0.55, 0.78])
    for j in range(4):
        a = j * math.pi / 2 + t * 0.5
        p = C + np.array([2.0 * math.cos(a), 0.9 + 0.3 * math.sin(a * 2), 2.0 * math.sin(a)])
        dot3(fr, p, r=7, col=WHITE, a=seg(u, 0.1 + j * 0.1, 0.3 + j * 0.1), glow=1.0)
        line3(fr, [p, yo], col=CYAN, w=1.6, a=0.6 * seg(u, 0.5 + j * 0.1, 0.8 + j * 0.1), glow=0.8)
    dot3(fr, yo, r=8, col=AZUL_GPS, a=seg(u, 0.2, 0.4), glow=1.2)

    def ui(img, fx):
        x, y, _ = fr.cam.p1(tuple(yo))
        pill(img, fx, x, y + 80, 'TÚ', eout(seg(u, 0.4, 0.7)), size=30, border=AZUL_GPS)
        kicker(img, 'SATÉLITES', 1500, seg(u, 0.3, 0.6), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 22. y en una recta es el más exacto (carretera recta con los puntos del GPS alineados)
def s_recta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.5, 80, 34, ty=0.4), K(0.35, 5.6, 50, 26, ty=0.4), K(5, 5.5, 46, 26, ty=0.4)]))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)
    carretera(fr, t, vel=0.8, a=0.9)
    x = -2.0 + 0.8 * max(0.0, u)
    draw_objects(fr, P.tfk(carro(giro_llanta=-t * 8), s=0.6, t=(x, 0, 0)))
    for j in range(10):
        xx = -6 + j * 0.8
        if xx < x:
            dot3(fr, (xx, 0.02, 0), r=6, col=AZUL_GPS, a=0.9, glow=1.0)

    def ui(img, fx):
        pill(img, fx, 540, 1250, '✓ EN RECTA: EL MÁS EXACTO', eout(seg(u, 0.4, 0.7)), size=32, border=VERDE, dot=False)
        texto(img, fx, 540, 1330, 'EN CURVAS, TÚNELES O ENTRE EDIFICIOS FALLA', 24, GRIS, seg(u, 0.8, 1.1), f='mono', glow=0.0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. mándaselo a quien jura que su velocímetro es exacto (tablero grande y título)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -30, 10), K(0.3, 4.6, 0, 6), K(5, 4.5, 4, 6)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'desliza')
    draw_objects(fr, P.tfk(carro(giro_llanta=-t * 6), s=0.75, t=(-e['dy'], -0.05, 0)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien jura', 'sans'), ('que su velocímetro es exacto.', 'serif')], 230, seg(u, 0.05, 0.2), size=66)
        tablero(img, fx, 540, 1380, 150, 100 + 2 * math.sin(t * 3), k=eout(seg(u, 0.2, 0.5)))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5),
                sfx=[(-2.6, 'cristal', 0.5), (-2.0, 'digital', 0.5), (-0.8, 'digital', 0.4), (UG, 'sub', 0.9), (UG + 0.15, 'bass', 0.8)]),
           dict(desde=1, fn=s_pon, tr='giro', sfx=[(0.25, 'thud', 0.8), (0.6, 'scribble', 0.4)]),
           dict(desde=2, fn=s_100_96, tr='golpe', sfx=[(0.0, 'tick', 0.4)]),
           dict(desde=3, fn=s_descompuesto, tr='glitch', sfx=[(0.1, 'whoosh', 0.6), (0.6, 'scribble', 0.6)]),
           dict(desde=4, fn=s_proposito, tr='cubo', sfx=[(0.2, 'shimmer', 0.4), (0.6, 'tick', 0.4)]),
           dict(desde=5, fn=s_onu, tr='deslizar', sfx=[(0.5, 'slap', 0.9)]),
           dict(desde=6, fn=s_menos, tr='wipe', sfx=[(0.3, 'chime_a', 0.4)]),
           dict(desde=7, fn=s_mas, tr='whip', sfx=[(0.4, 'whoosh_suave', 0.5), (0.6, 'chime_c', 0.5)]),
           dict(desde=8, fn=s_formula, tr='mosaico', sfx=[]),
           dict(desde=9, fn=s_114, tr='zoom', c=(0.5, 0.53), sfx=[]),
           dict(desde=10, fn=s_legal, tr='iris', c=(0.5, 0.52), sfx=[(0.4, 'thud', 1.0), (0.42, 'bass', 0.7)]),
           dict(desde=11, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[(0.2, 'sub', 0.9), (0.25, 'bass', 0.7)]),
           dict(desde=12, fn=s_grandes, tr='deslizar_abajo', c=(0.66, 0.58), sfx=[(0.5, 'whoosh_suave', 0.5), (1.4, 'scribble', 0.6)]),
           dict(desde=13, fn=s_sensor, tr='zoom', sfx=[(0.2 + 0.25 * j, 'tick2', 0.3) for j in range(8)]),
           dict(desde=14, fn=s_vueltas, tr='remolino', sfx=[(0.5, 'click', 0.5), (1.2, 'tick', 0.4)]),
           dict(desde=15, fn=s_avanza, tr='cubo_izq', sfx=[(0.2, 'whoosh_suave', 0.6), (1.9, 'chime_b', 0.5)]),
           dict(desde=16, fn=s_rapido, tr='whip', sfx=[(0.1, 'whoosh', 0.7), (0.4, 'riser', 0.3)]),
           dict(desde=17, fn=s_3, tr='cristal', palabra='+3%', sfx=[(0.4, 'tick', 0.5)]),
           dict(desde=18, fn=s_103, tr='golpe', sfx=[]),
           dict(desde=19, fn=s_odometro, tr='rebanadas', sfx=[(0.2 + 0.3 * j, 'click', 0.3) for j in range(6)]),
           dict(desde=20, fn=s_menos_km, tr='flash', sfx=[(1.5, 'chime_a', 0.5)]),
           dict(desde=21, fn=s_gps, tr='zoom', c=(0.62, 0.5), sfx=[(0.2 + 0.1 * j, 'tick2', 0.3) for j in range(4)]),
           dict(desde=22, fn=s_recta, tr='deslizar_abajo', sfx=[(0.4, 'chime_c', 0.5)]),
           dict(desde=23, fn=s_compa, tr='ritmo', sfx=[(0.05, 'slap', 0.7), (0.2, 'bass', 0.7)]),
           dict(desde=24, loop=True, tr='glitch')]


def tiempos_falsos():
    T = [(round(0.25 + 2.8 * i, 2), round(0.25 + 2.8 * i + 2.4, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.55, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    print('ok', T[-1])


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    else:
        montaje.cli(globals())
