"""Reel diario lun 23-nov-2026 10:00 (propuesto) — «Tu carro no es… de donde crees.»
El NIV (VIN, «número de serie»): 17 letras y números en el marco de la puerta del conductor y en el tablero, junto al
parabrisas. El 1.er carácter dice en qué país se armó (3 = México; 1, 4 o 5 = EE. UU.; J = Japón); el 10.º es el
año modelo y el 9.º es un dígito verificador: una cuenta con los otros 16 que delata un número inventado o cambiado.
Nunca lleva I, O ni Q (para no confundirlas con 1 y 0). Error (segundo gancho): comprar un carro usado sin revisar que
el número del tablero, el de la puerta y el de la factura sean idénticos, y sin consultarlo gratis en el REPUVE.
Comunidad: automovilistas y compradores de usados. Inicio tipo 4 (barra de búsqueda): en el celular el cursor escribe
«¿de dónde es mi carro?» delante de «ORIGEN» de cristal; Enter y la cámara atraviesa la pantalla hasta el carro.
El final («…porque tu carro no es de donde crees») regresa a la barra de búsqueda (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
El NIV que se ve es un EJEMPLO inventado (con su dígito verificador bien calculado); el carro es un sedán sin marca.
Datos y fuentes: guiones/2026-11-23_vin.txt.
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
                    rec_frame, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import _B, texto, esquema, golpe_k, sacudir, K, camara, auto
from scooter import candado

M3 = M.M3
TEMA = 'vin'
TXT = ['Tu carro no es… de donde crees.',
       'Abre la puerta del conductor:',
       'en el marco hay una etiqueta con 17 letras y números.',
       'Es el NIV,',
       'y casi siempre también está en el tablero, junto al parabrisas.',
       'El primer carácter',
       'dice en qué país se armó tu carro.',
       'Si empieza con 3, nació en México;',
       'con 1, 4 o 5, en Estados Unidos; con J, en Japón.',
       'Dos carros de la misma marca pueden venir de países distintos:',
       'solo cambia ese primer carácter.',
       'El 10.º es el año modelo,',
       'y el 9.º es un candado:',
       'una cuenta matemática con los otros 16.',
       'Y aquí está el error:',
       'comprar un carro usado sin revisar ese número.',
       'Si alguien lo inventa o lo cambia,',
       'la cuenta del 9.º casi nunca cuadra.',
       'Antes de pagar, el número del tablero, el de la puerta',
       'y el de la factura tienen que ser idénticos.',
       'Y en la página del REPUVE lo consultas gratis:',
       'te dice si tiene reporte de robo.',
       'Ah, y nunca vas a ver una I, una O ni una Q:',
       'así nadie las confunde con 1 y 0.',
       'Mándaselo a tu compa que va a comprar carro usado.',
       'Y que antes cheque de dónde es… porque tu carro no es de donde crees.']
VOZ = ['Tu carro no es... de donde crees.',
       'Abre la puerta del conductor:',
       'en el marco hay una etiqueta con diecisiete letras y números.',
       'Es el NIV,',
       'y casi siempre también está en el tablero, junto al parabrisas.',
       'El primer carácter',
       'dice en qué país se armó tu carro.',
       'Si empieza con tres, nació en México;',
       'con uno, cuatro o cinco, en Estados Unidos; con jota, en Japón.',
       'Dos carros de la misma marca pueden venir de países distintos:',
       'solo cambia ese primer carácter.',
       'El décimo es el año modelo,',
       'y el noveno es un candado:',
       'una cuenta matemática con los otros dieciséis.',
       'Y aquí está el error:',
       'comprar un carro usado sin revisar ese número.',
       'Si alguien lo inventa o lo cambia,',
       'la cuenta del noveno casi nunca cuadra.',
       'Antes de pagar, el número del tablero, el de la puerta',
       'y el de la factura tienen que ser idénticos.',
       'Y en la página del REPUVE lo consultas gratis:',
       'te dice si tiene reporte de robo.',
       'Ah, y nunca vas a ver una I, una O ni una Q:',
       'así nadie las confunde con uno y cero.',
       'Mándaselo a tu compa que va a comprar carro usado.',
       'Y que antes cheque de dónde es... porque tu carro no es de donde crees.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_vin.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-23_vin_words.json')

AMARILLO = (255, 236, 160)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
ROJO = (255, 60, 45)
VERDE = (60, 210, 120)
VINO = (132, 22, 34)              # el sedán de este reel es rojo vino (sin marca)
PLATA = (150, 156, 166)
PAPEL = (246, 244, 236)

# ------------------------------------------------------------------ el NIV de ejemplo (dígito verificador real)
_TR = dict(zip('ABCDEFGHJKLMNPRSTUVWXYZ', [1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 7, 9, 2, 3, 4, 5, 6, 7, 8, 9]))
PESOS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def valor(c):
    return int(c) if c.isdigit() else _TR.get(c, 0)


def suma(v):
    return sum(valor(c) * w for c, w in zip(v, PESOS))


def digito(v):
    r = suma(v) % 11
    return 'X' if r == 10 else str(r)


def armar(v):
    return v[:8] + digito(v) + v[9:]


VIN_MX = armar('3XYAB12C0SM004217')       # 3XYAB12C2SM004217 (EJEMPLO inventado)
VIN_JP = armar('JXYAB12C0SJ004217')       # JXYAB12C6SJ004217
VIN_MAL = VIN_MX[:14] + '8' + VIN_MX[15:]  # alguien cambió un número: la cuenta ya no da 2

# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    if not os.path.exists(WORDS):                       # todavía sin voz (pruebas): reparte por letras
        T, _ = montaje.cargar(TEMA)
        for i, f in enumerate(VOZ):
            ws = [w for w in f.split() if montaje._norm(w)]
            a, b = T[i] if T else (0, 2)
            L = np.cumsum([0] + [len(w) + 1 for w in ws])[:-1] / max(1, sum(len(w) + 1 for w in ws))
            _WT[i] = [float(x) * (b - a) for x in L]
        return _WT
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
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ objetos
def carro(col=VINO, puerta=0.0, sticker=1.0, giro=0.0):
    """Sedán sin marca (gasolina.auto) con la puerta del conductor que se abre sobre su bisagra delantera y la
    etiqueta del NIV en el marco (se ve cuando la puerta se abre)."""
    ms = auto(col=col)
    ms = [m for m in ms if getattr(m, 'name', '') != 'tapa']
    if sticker > 0:
        st = named(M3.box(0.2, 0.13, 0.012, PAPEL, shadow=0, gloss=0.3).tf(t=(-0.45, 0.52, 0.628)), 'sticker', rim=0.3)
        st.glow = M.scale_c(AMARILLO, 0.25 * sticker)
        ms.append(st)
    a = 62 * P.eout4(clamp(puerta))
    dp = named(M3.box(0.86, 0.46, 0.045, col, shadow=0, gloss=0.8).tf(t=(-0.43, 0.35, 0)), 'puerta', rim=0.8, gloss=0.8)
    man = named(M3.box(0.14, 0.03, 0.03, (200, 202, 208), shadow=0, gloss=0.9).tf(t=(-0.7, 0.7, 0.035)), 'manija', rim=0.9)
    marco = named(M3.box(0.86, 0.03, 0.06, (40, 42, 48), shadow=0, gloss=0.4).tf(t=(-0.43, 0.8, 0)), 'marco')
    ms += [x.tf(ry=a).tf(t=(0.31, 0, 0.64)) for x in (dp, man, marco)]
    return P.tfk(ms, ry=giro) if giro else ms


def vin_tira(img, fx, cx, cy, vin, size, k=1.0, marcas=None, glitch=0.0, t=0.0, apagar=0.0, sep=1.0):
    """Los 17 caracteres en cajitas (monoespaciada). marcas = {índice: color} resalta cajas; apagar baja los demás."""
    cw = size * 0.78 * sep
    x0 = cx - cw * 17 / 2
    if k <= 0.01:
        return [(x0 + cw * (i + 0.5), cy) for i in range(17)]
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    f = M.font('mono', size)
    marcas = marcas or {}
    rng = np.random.RandomState(int(t * 20))
    pos = []
    for i, ch in enumerate(vin):
        ki = clamp(k * 17 - i)
        x = x0 + cw * (i + 0.5)
        pos.append((x, cy))
        if ki <= 0.01:
            continue
        col = marcas.get(i)
        base = WHITE if col is None else col
        if col is None and apagar > 0:
            base = M.mixc(WHITE, (90, 90, 98), apagar)
        if glitch > 0 and rng.rand() < 0.35 * glitch:
            ch = '0123456789ABCDEFGHJKLMNPRSTUVWXYZ'[rng.randint(33)]
            base = ROJO
        if col is not None:
            box = (x - cw * 0.46, cy - size * 0.72, x + cw * 0.46, cy + size * 0.72)
            d.rounded_rectangle(box, radius=8, outline=M.scale_c(col, ki), width=4)
            df.rounded_rectangle(box, radius=8, outline=M.scale_c(col, 0.6 * ki), width=10)
        d.text((x, cy), ch, font=f, fill=M.scale_c(base, ki), anchor='mm')
        if col is not None:
            df.text((x, cy), ch, font=f, fill=M.scale_c(col, 0.5 * ki), anchor='mm')
    return pos


def etiqueta_vin(img, fx, cx, cy, w, k=1.0, ang=0.0, vin=VIN_MX, marca1=0.0):
    """Etiqueta del marco de la puerta (EJEMPLO, sin marca): código de barras y el NIV."""
    if k <= 0.01:
        return
    h = int(w * 0.5)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=12, fill=(*PAPEL, 255))
    dl.text((w * 0.06, h * 0.14), 'FABRICADO POR: ……………', font=M.font('mono', int(w * 0.035)), fill=(60, 60, 64, 255), anchor='lm')
    dl.text((w * 0.94, h * 0.14), 'EJEMPLO', font=M.font('sansx', int(w * 0.04)), fill=(200, 40, 40, 255), anchor='rm')
    rng = np.random.RandomState(4)
    x = w * 0.06
    while x < w * 0.94:                                                  # código de barras
        bw = rng.choice([2, 3, 5]) * w / 900
        dl.rectangle((x, h * 0.28, x + bw, h * 0.58), fill=(20, 20, 22, 255))
        x += bw + rng.choice([2, 4]) * w / 900
    f = M.font('mono', int(w * 0.075))
    cw = w * 0.88 / 17
    for i, ch in enumerate(vin):
        xx = w * 0.06 + cw * (i + 0.5)
        col = (20, 20, 22, 255)
        if i == 0 and marca1 > 0:
            dl.rounded_rectangle((xx - cw * 0.5, h * 0.66, xx + cw * 0.5, h * 0.9), radius=6, fill=(255, 210, 60, int(255 * marca1)))
        dl.text((xx, h * 0.78), ch, font=f, fill=col, anchor='mm')
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    s = P.resorte(k)
    if s < 0.99:
        lay = lay.resize((max(2, int(lay.width * s)), max(2, int(lay.height * s))))
    img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)
    ImageDraw.Draw(fx).rounded_rectangle((cx - lay.width / 2 - 6, cy - lay.height / 2 - 6, cx + lay.width / 2 + 6, cy + lay.height / 2 + 6),
                                         radius=16, outline=M.scale_c(AMARILLO, 0.35 * k), width=10)


def scr_busqueda(n_letras, enter=0.0, t=0.0):
    preg = '¿de dónde es mi carro?'

    def dib(d, im):
        f = M.font
        d.text((210, 150), 'Buscar', font=f('sansx', 46), fill=(240, 240, 244), anchor='mm')
        c = M.mixc((200, 200, 205), CYAN, enter)
        d.rounded_rectangle((26, 220, 394, 300), radius=40, fill=(24, 26, 32), outline=c, width=4)
        d.ellipse((46, 244, 76, 274), outline=(200, 200, 205), width=4)
        d.line([(72, 270), (84, 282)], fill=(200, 200, 205), width=5)
        txt = preg[:n_letras]
        fo = f('sanss', 25)
        d.text((96, 260), txt, font=fo, fill=(235, 236, 240), anchor='lm')
        if int(t * 3) % 2 == 0 or n_letras < len(preg):
            x = 96 + d.textlength(txt, font=fo) + 4
            d.line([(x, 242), (x, 278)], fill=CYAN, width=3)
        for j in range(4):                                               # sugerencias grises
            y = 360 + 70 * j
            d.rounded_rectangle((30, y, 390, y + 46), radius=10, fill=(16, 17, 21))
            d.text((50, y + 23), ('¿qué significa el número de serie?', '¿cómo saber si un auto es robado?',
                                  'NIV de mi auto', 'país de fabricación por VIN')[j], font=f('sansm', 19),
                   fill=(130, 132, 140), anchor='lm')
        if enter > 0:
            d.rounded_rectangle((120, 680, 300, 750), radius=20, fill=M.scale_c(CYAN, 0.6 * enter))
            d.text((210, 715), 'ENTER', font=f('sansx', 30), fill=(10, 10, 12), anchor='mm')
    return P.pantalla(dib)


def scr_repuve(n_letras, resultado=0.0, robo=False):
    def dib(d, im):
        f = M.font
        d.rectangle((0, 70, 420, 170), fill=(22, 24, 30))
        d.text((210, 104), 'CONSULTA CIUDADANA', font=f('sansx', 28), fill=(240, 240, 244), anchor='mm')
        d.text((210, 142), 'REGISTRO PÚBLICO VEHICULAR', font=f('mono', 15), fill=(150, 152, 160), anchor='mm')
        d.text((34, 220), 'NIV / VIN', font=f('mono', 18), fill=(170, 172, 180), anchor='lm')
        d.rounded_rectangle((26, 240, 394, 300), radius=10, fill=(14, 15, 18), outline=(200, 200, 205), width=3)
        d.text((40, 270), VIN_MX[:n_letras], font=f('mono', 24), fill=(235, 236, 240), anchor='lm')
        d.rounded_rectangle((110, 330, 310, 390), radius=14, fill=(60, 160, 230))
        d.text((210, 360), 'CONSULTAR', font=f('sansx', 26), fill=(255, 255, 255), anchor='mm')
        if resultado > 0:
            col = ROJO if robo else VERDE
            a = clamp(resultado)
            d.rounded_rectangle((26, 440, 394, 640), radius=18, outline=M.scale_c(col, a), width=5)
            d.text((210, 500), '✓' if not robo else '!', font=f('sansx', 70), fill=M.scale_c(col, a), anchor='mm')
            d.text((210, 580), 'CON REPORTE DE ROBO' if robo else 'SIN REPORTE DE ROBO', font=f('sansx', 26),
                   fill=M.scale_c(col, a), anchor='mm')
            d.text((210, 690), 'EJEMPLO', font=f('mono', 20), fill=(150, 152, 160), anchor='mm')
    return P.pantalla(dib)


def globo(fr, t, C, R, spin, marcas=(), k=1.0):
    """Tierra de alambre (line-art) con marcas de país [(lon, lat, color, intensidad)] que brillan."""
    camdir = M.norm(fr.cam.pos - C)
    TILT = math.radians(-18)

    def rot(Pp):
        c, s = math.cos(spin), math.sin(spin)
        x, y, z = Pp[:, 0], Pp[:, 1], Pp[:, 2]
        x, z = x * c + z * s, -x * s + z * c
        ct, st = math.cos(TILT), math.sin(TILT)
        y, z = y * ct - z * st, y * st + z * ct
        return np.stack([x, y, z], 1)
    for lat in range(-60, 90, 30):
        th = np.linspace(0, 2 * math.pi, 72)
        r = math.cos(math.radians(lat))
        Pp = np.stack([r * np.cos(th), np.full_like(th, math.sin(math.radians(lat))), r * np.sin(th)], 1) * R
        D._seg_by_depth(fr, rot(Pp), C, camdir)
    for lon in range(0, 180, 30):
        th = np.linspace(0, 2 * math.pi, 72)
        a = math.radians(lon)
        Pp = np.stack([np.cos(th) * math.cos(a), np.sin(th), np.cos(th) * math.sin(a)], 1) * R
        D._seg_by_depth(fr, rot(Pp), C, camdir)
    out = []
    for lon, lat, col, kk in marcas:
        la, lo = math.radians(lat), math.radians(lon)
        p = rot(np.array([[math.cos(la) * math.cos(lo), math.sin(la), -math.cos(la) * math.sin(lo)]]) * R)[0]
        vis = (p / R) @ camdir > 0.05
        if vis and kk > 0.01:
            dot3(fr, C + p, r=int(8 + 6 * kk), col=col, a=kk * k, glow=1.6 * kk)
        out.append((fr.cam.p1(tuple(C + p)), vis))
    return out


def recreacion(img, fx, k=1.0, y=1440, txt='EJEMPLO'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


def flash_txt(img, fx, txt, y, k, size=90, col=WHITE):
    if k > 0.01:
        P.titulo_golpe(img, fx, [(txt, 'sans')], y, k, size=size, col=col)


# ================================================================== escenas
# 0. gancho (inicio 4: barra de búsqueda). Pre-roll (y loop): el celular cae girando delante de «ORIGEN» de cristal y
#    el cursor escribe «¿de dónde es mi carro?»; en U_ENTER se aprieta Enter y la cámara atraviesa la pantalla hasta el
#    sedán vino, que llega derrapando con el título.
U_ENTER = 0.05
N_PREG = len('¿de dónde es mi carro?')


def _busca(t, fi, u):
    fr = Frame(camara(u, [K(-4.2, 4.6, -40, 10, ty=0.95), K(-3.6, 2.9, -8, 4, ty=0.95), K(-1.2, 2.5, 6, 3, ty=0.95),
                          K(U_ENTER, 2.2, 0, 2, ty=0.95)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ORIGEN', u, t0=-4.4, cy=0.66, entrada='golpe')
    n = int(N_PREG * seg(u, -3.3, -0.9))
    e = P.entrada(u, -4.0, 0.3, 'gira')
    ent = seg(u, U_ENTER - 0.2, U_ENTER)
    draw_objects(fr, P.celular(scr_busqueda(n, enter=ent, t=t), ry=math.degrees(e['giro']) * 0.25 - 6 * math.sin(t * 0.7),
                               off=(0, 0, 0)) if e['escala'] > 0.05 else [])

    def ui(img, fx):
        kicker(img, 'NIV · NÚMERO DE IDENTIFICACIÓN VEHICULAR', 150, seg(u, -3.9, -3.6), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


def _revela(t, fi, u):
    uc = Wp(0, 'crees') - 0.15
    fr = Frame(camara(u, [K(U_ENTER, 4.4, 40, 6, ty=0.7), K(U_ENTER + 0.5, 6.4, 24, 9, ty=0.65), K(uc, 6.0, 14, 8, ty=0.65),
                          K(3.0, 5.8, 10, 8, ty=0.65)], cy=0.64))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.55)
    M.cristal(fr.base, fr.fx, 'ORIGEN', u, t0=-4.4, cy=0.4, entrada='golpe')
    e = P.entrada(u, U_ENTER, 0.3, 'desliza')
    draw_objects(fr, P.tfk(carro(giro=25 * (1 - P.eout4(seg(u, U_ENTER, U_ENTER + 0.45)))), t=(-1.2 * e['dy'], 0, 0)))

    def ui(img, fx):
        kicker(img, 'AUTOMOVILISTAS · LO QUE NO VES', 150, seg(u, U_ENTER + 0.1, U_ENTER + 0.3), col=AZULC)
        P.titulo_golpe(img, fx, [('Tu carro no es…', 'sans'), ('de donde crees.', 'serif')], 230, seg(u, uc - 0.6, uc - 0.45), size=84)
        recreacion(img, fx, seg(u, uc, uc + 0.3), y=1400, txt='SEDÁN SIN MARCA · EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc - 0.45, 0.35), amp=22)


def s_gancho(t, fi, u, d):
    if u < U_ENTER:
        return _busca(t, fi, u)
    if u < U_ENTER + 0.3:
        return M.tr_zoom_through(_busca(t, fi, u), _revela(t, fi, u), seg(u, U_ENTER, U_ENTER + 0.3), 0.5, 0.45)
    return _revela(t, fi, u)


# 1. abre la puerta del conductor: órbita rápida al costado y la puerta se abre sobre su bisagra
def s_puerta(t, fi, u, d):
    ua = Wp(1, 'puerta') - 0.2
    fr = Frame(camara(u, [K(-0.3, 6.4, 70, 10, ty=0.65), K(0.35, 5.0, 30, 7, ty=0.6, tx=-0.1), K(ua + 0.3, 3.6, 22, 6, ty=0.6, tx=-0.3),
                          K(d, 3.5, 18, 6, ty=0.6, tx=-0.3)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.4)
    draw_objects(fr, carro(puerta=seg(u, ua, ua + 0.45), sticker=seg(u, ua + 0.3, ua + 0.6)))
    px, py, _ = fr.cam.p1((-0.45, 0.58, 0.63))

    def ui(img, fx):
        kicker(img, 'PUERTA DEL CONDUCTOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > ua + 0.35:
            doodle_circle(img, fx, px, py, 90, 60, t, k=seg(u, ua + 0.35, ua + 0.7), col=AMARILLO, seed=3)
            pill(img, fx, px, py - 150, 'MARCO DE LA PUERTA', eout(seg(u, ua + 0.5, ua + 0.8)), size=26, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. la etiqueta del marco sale volando hacia ti y aparecen los 17 caracteres, contados uno por uno
def s_etiqueta(t, fi, u, d):
    u17 = Wp(2, 'diecisiete') - 0.1
    fr = Frame(camara(u, [K(-0.3, 1.6, 10, 4, ty=0.58, tx=-0.45, tz=0.6), K(0.4, 1.3, 4, 2, ty=0.58, tx=-0.45, tz=0.6),
                          K(d, 1.25, 2, 2, ty=0.58, tx=-0.45, tz=0.6)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    draw_objects(fr, carro(puerta=1.0, sticker=1.0))
    k = P.eout4(seg(u, -0.2, 0.25))

    def ui(img, fx):
        a = np.asarray(img, np.float32) * (1 - 0.6 * k)
        img.paste(Image.fromarray(a.astype(np.uint8)))
        etiqueta_vin(img, fx, 540, 760, int(980 * (0.4 + 0.6 * k)), k=1.0, ang=-4 * (1 - k) + 1.5 * math.sin(t * 1.3))
        n = int(17 * seg(u, u17 - 0.1, u17 + 0.9))
        if n > 0:
            vin_tira(img, fx, 540, 1130, VIN_MX[:n] + ' ' * (17 - n), 50, k=1.0)
            texto(img, fx, 540, 1230, f'{n:2d} / 17', 44, AMARILLO, 1.0, f='mono', glow=0.4)
        kicker(img, 'ETIQUETA DEL NIV · EJEMPLO', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. «Es el NIV»: llega con la transición de cristal (la palabra NIV); los 17 en cajitas y sus 4 partes
def s_niv(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.6, -30, 10, ty=0.6), K(0.3, 5.8, -14, 8, ty=0.6), K(d, 5.6, -10, 8, ty=0.6)], cy=0.72))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9, beam=0.3)
    draw_objects(fr, P.tfk(carro(), s=0.8, t=(0, 0, 0)))

    def ui(img, fx):
        kicker(img, 'NIV = VIN = «NÚMERO DE SERIE»', 150, seg(u, -0.1, 0.2), col=AZULC)
        pos = vin_tira(img, fx, 540, 520, VIN_MX, 52, k=seg(u, -0.15, 0.3))
        partes = [(0, 3, 'FABRICANTE', CYAN), (3, 8, 'MODELO', GRIS), (8, 9, '✓', AMARILLO), (9, 10, 'AÑO', VERDE), (10, 17, 'SERIE', GRIS)]
        dd = ImageDraw.Draw(img)
        for j, (a, b, nom, col) in enumerate(partes):
            kk = seg(u, 0.3 + 0.12 * j, 0.5 + 0.12 * j)
            if kk <= 0:
                continue
            x0, x1 = pos[a][0] - 18, pos[b - 1][0] + 18
            dd.line([(x0, 580), (x0, 600), (x1, 600), (x1, 580)], fill=M.scale_c(col, kk), width=4)
            texto(img, fx, (x0 + x1) / 2, 640 + 40 * (j % 2), nom, 24, col, kk, f='mono', glow=0.3)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. también en el tablero, junto al parabrisas: zoom digital (REC) a la plaquita detrás del vidrio
def s_tablero(t, fi, u, d):
    ut = Wp(4, 'tablero') - 0.1
    up = Wp(4, 'parabrisas') - 0.1
    z = 1.0 if u < ut else (1.3 if u < up else 1.8)
    fr = Frame(camara(u, [K(-0.3, 4.0, 110, 30, ty=0.9, tx=0.6), K(0.3, 3.2, 120, 34, ty=0.9, tx=0.75),
                          K(ut, 2.4, 124, 36, ty=0.9, tx=0.75), K(up, 1.7, 126, 38, ty=0.88, tx=0.78), K(d, 1.6, 127, 38, ty=0.88, tx=0.78)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.7)
    draw_objects(fr, carro())
    px, py, _ = fr.cam.p1((0.58, 0.86, -0.42))

    def ui(img, fx):
        kicker(img, 'ZOOM · ESQUINA DEL PARABRISAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        w = int(150 * z)
        dd, dfx = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        dd.rounded_rectangle((px - w, py - w * 0.2, px + w, py + w * 0.2), radius=6, fill=(196, 198, 204), outline=(240, 240, 244), width=3)
        dd.text((px, py), VIN_MX, font=M.font('mono', max(10, int(w * 0.17))), fill=(20, 20, 24), anchor='mm')
        dfx.rounded_rectangle((px - w - 10, py - w * 0.2 - 10, px + w + 10, py + w * 0.2 + 10), radius=10,
                              outline=M.scale_c(CYAN, 0.4), width=8)
        rec_frame(img, t, k=1.0, zoom_label=f'x{z:.1f}')
        pill(img, fx, 540, 1350, 'SE LEE DESDE AFUERA, A TRAVÉS DEL VIDRIO', eout(seg(u, up, up + 0.3)), size=24, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. el primer carácter: todo se apaga menos el «3», que crece al centro
def s_primero(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.0, 0, 6, ty=1.0), K(0.4, 5.4, 10, 6, ty=1.0), K(d, 5.3, 12, 6, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.6)
    kc = P.eout4(seg(u, 0.1, 0.6))

    def ui(img, fx):
        kicker(img, 'CARÁCTER 1 DE 17', 150, seg(u, -0.1, 0.2), col=AZULC)
        pos = vin_tira(img, fx, 540, 1180 - 120 * kc, VIN_MX, 50, k=1.0, marcas={0: AMARILLO}, apagar=kc)
        x0, y0 = pos[0]
        x = lerp(x0, 540, kc)
        y = lerp(y0, 700, kc)
        s = int(lerp(60, 420, kc))
        texto(img, fx, x, y, '3', s, AMARILLO, 1.0, f='mono', glow=0.6)
        doodle_circle(img, fx, x, y, s * 0.55, s * 0.62, t, k=seg(u, 0.6, 0.9), col=WHITE, seed=5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.6, 0.3), amp=14)


# 6. dice en qué país se armó: el «3» se abre en un punto de luz (iris) y gira la Tierra de alambre
def s_pais(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 6.5, 0, 6, ty=1.2), K(0.4, 5.0, 20, 10, ty=1.2), K(d, 4.8, 24, 10, ty=1.2)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.1)
    C = np.array([0, 1.2, 0])
    M.cristal(fr.base, fr.fx, 'PAÍS', u, t0=0.05, cy=0.5, entrada='sube')
    spin = math.radians(-60 + 30 * u)
    glob = globo(fr, t, C, 1.4, spin, marcas=[(-102, 23, AMARILLO, seg(u, 0.8, 1.1)), (-98, 39, CYAN, seg(u, 1.0, 1.3)),
                                              (138, 36, CYAN, seg(u, 1.2, 1.5))])

    def ui(img, fx):
        kicker(img, 'DÓNDE SE ARMÓ · NO DÓNDE SE DISEÑÓ', 150, seg(u, -0.1, 0.2), col=AZULC)
        (x, y, _), vis = glob[0]
        if vis:
            pill(img, fx, x, y - 70, '3', eout(seg(u, 0.8, 1.1)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. si empieza con 3, nació en México: el mapa de México se dibuja y «MÉXICO» de cristal cae detrás
MX = None


def _mapa():
    global MX
    if MX is None:
        from italika import MX as _MX, gm as _gm
        MX = (_MX, _gm)
    return MX


def s_mexico(t, fi, u, d):
    um = Wp(7, 'mexico') - 0.1
    mx, gm = _mapa()
    fr = Frame(camara(u, [K(-0.3, 22.0, 0, 82, tx=-0.6, ty=0.0, tz=0.2), K(0.4, 19.0, 6, 78, tx=-0.6, ty=0.0, tz=0.3),
                          K(d, 18.6, 8, 77, tx=-0.6, ty=0.0, tz=0.3)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'MÉXICO', u, t0=um - 0.1, cy=0.3, entrada='golpe')
    line3(fr, [gm(lo, la) for lo, la in mx], col=WHITE, w=4.0, a=1.0, glow=1.1, frac=min(1.0, 0.2 + P.eout4(seg(u, -0.3, um))))
    for j, (lo, la) in enumerate(((-100.4, 20.6), (-101.7, 21.9), (-99.2, 19.3), (-106.4, 31.7), (-100.3, 25.7))):
        dot3(fr, gm(lo, la), r=8, col=AMARILLO, a=seg(u, um + 0.1 * j, um + 0.1 * j + 0.2), glow=1.4)
    px, py, _ = fr.cam.p1(tuple(gm(-101.5, 22.0)))

    def ui(img, fx):
        kicker(img, 'EMPIEZA CON 3 → SE ARMÓ EN MÉXICO', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 210, 1300, '3', 200, AMARILLO, P.resorte(seg(u, 0.0, 0.3)), f='mono', glow=0.6)
        doodle_arrow(img, fx, 290, 1230, px - 30, py + 60, t, k=seg(u, 0.3, 0.7), col=AMARILLO, seed=2)
        pill(img, fx, 680, 1300, 'PLANTAS ARMADORAS', eout(seg(u, um + 0.4, um + 0.7)), size=26, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, um + 0.2, 0.3), amp=16)


# 8. con 1, 4 o 5, Estados Unidos; con J, Japón: lista que cae en rebanadas sobre la Tierra que gira
def s_lista(t, fi, u, d):
    uu = Wp(8, 'estados') - 0.1
    uj = Wp(8, 'japon') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.6, -20, 8, ty=1.0), K(0.4, 5.0, 0, 6, ty=1.0), K(d, 4.9, 4, 6, ty=1.0)], cy=0.62))
    space(fr, t, floor=None, bokeh=0.9)
    spin = math.radians(-40 + 70 * P.eout4(seg(u, uu, uj + 0.3)))
    globo(fr, t, np.array([0, 1.0, 0]), 1.25, spin, marcas=[(-98, 39, CYAN, seg(u, uu - 0.2, uu)), (138, 36, CYAN, seg(u, uj - 0.2, uj)),
                                                         (-102, 23, AMARILLO, 1.0)])

    def ui(img, fx):
        kicker(img, 'EL PRIMER CARÁCTER · EJEMPLOS', 150, seg(u, -0.1, 0.2), col=AZULC)
        filas = [('3', 'MÉXICO', AMARILLO, -0.2), ('1 · 4 · 5', 'ESTADOS UNIDOS', CYAN, uu - 0.25), ('J', 'JAPÓN', CYAN, uj - 0.25)]
        for j, (cod, pais, col, u0) in enumerate(filas):
            kk = P.eout4(seg(u, u0, u0 + 0.25))
            if kk <= 0:
                continue
            y = 300 + 115 * j
            x = 540 + (1 - kk) * 700 * (1 if j % 2 else -1)
            dd = ImageDraw.Draw(img)
            dd.rounded_rectangle((x - 430, y - 46, x + 430, y + 46), radius=18, fill=(14, 15, 19), outline=M.scale_c(col, kk), width=3)
            texto(img, fx, x - 250, y, cod, 58, col, kk, f='mono', glow=0.5)
            texto(img, fx, x + 150, y, pais, 42, WHITE, kk, f='sansx', glow=0.2)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. prueba en dos casos: dos sedanes iguales lado a lado; arriba de cada uno su NIV
def s_dos(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 9.0, 100, 16, ty=0.6), K(0.4, 7.6, 66, 11, ty=0.6), K(d, 7.4, 60, 11, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8, beam=0.4)
    e1 = P.entrada(u, -0.2, 0.3, 'cae')
    e2 = P.entrada(u, 0.15, 0.3, 'cae')
    ms = (P.tfk(carro(col=PLATA), s=0.8, t=(0, max(0.0, -e1['dy']), -1.15)) +
          P.tfk(carro(col=PLATA), s=0.8, t=(0, max(0.0, -e2['dy']), 1.15)))
    draw_objects(fr, ms)
    a = fr.cam.p1((0.3, 1.25, -1.15))
    b = fr.cam.p1((0.3, 1.25, 1.15))
    izq, der = (a, b) if a[0] < b[0] else (b, a)

    def ui(img, fx):
        kicker(img, 'PRUEBA · MISMA MARCA, MISMO MODELO', 150, seg(u, -0.1, 0.2), col=AZULC)
        for (x, y, _), vin, pais, col, u0 in ((izq, VIN_MX, 'MÉXICO', AMARILLO, 0.2), (der, VIN_JP, 'JAPÓN', CYAN, 0.55)):
            k = seg(u, u0, u0 + 0.3)
            xx = min(max(x, 290), 790)
            vin_tira(img, fx, xx, y - 120, vin, 24, k=k, marcas={0: col})
            texto(img, fx, xx, y - 260, vin[0], 120, col, P.resorte(k), f='mono', glow=0.6)
            pill(img, fx, xx, y - 175, pais, eout(k), size=26, border=col)
        recreacion(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.1, 0.25), golpe_k(u, 0.45, 0.25)), amp=12)


# 10. solo cambia ese primer carácter: los dos NIV encimados; 16 se quedan iguales y el primero parpadea 3 ↔ J
def s_cambia(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 20, 8, ty=0.8), K(0.4, 4.6, 0, 6, ty=0.8), K(d, 4.5, -4, 6, ty=0.8)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    alt = int(t * 3) % 2

    def ui(img, fx):
        kicker(img, 'ANTES / DESPUÉS', 150, seg(u, -0.1, 0.2), col=AZULC)
        k = seg(u, -0.2, 0.2)
        v1 = VIN_MX if alt == 0 else 'J' + VIN_MX[1:]
        pos = vin_tira(img, fx, 540, 700, v1, 52, k=k, marcas={0: AMARILLO if alt == 0 else CYAN})
        x0, y0 = pos[0]
        doodle_circle(img, fx, x0, y0, 46, 64, t, k=seg(u, 0.3, 0.6), col=WHITE, seed=8)
        texto(img, fx, 540, 860, '3 = MÉXICO     J = JAPÓN', 44, WHITE, seg(u, 0.4, 0.6), f='mono', glow=0.3)
        texto(img, fx, 540, 1000, 'LOS OTROS 16 PUEDEN PARECERSE', 30, GRIS, seg(u, 0.7, 0.9), f='mono', glow=0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. el 10.º es el año modelo: la «S» y un calendario que corre hasta 2025
def s_anio(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, -10, 6, ty=0.9), K(0.4, 4.6, 6, 6, ty=0.9), K(d, 4.5, 8, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=1.0, beam=0.5)
    k = P.eout4(seg(u, 0.2, 0.9))
    anio = int(2016 + 9 * k)

    def ui(img, fx):
        kicker(img, 'CARÁCTER 10 · AÑO MODELO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pos = vin_tira(img, fx, 540, 480, VIN_MX, 50, k=1.0, marcas={9: VERDE}, apagar=0.7)
        x, y = pos[9]
        doodle_arrow(img, fx, x, y + 60, 540, 760, t, k=seg(u, 0.1, 0.4), col=VERDE, seed=4)
        texto(img, fx, 540, 900, 'S', 260, VERDE, P.resorte(seg(u, 0.1, 0.4)), f='mono', glow=0.6)
        texto(img, fx, 540, 1150, f'= {anio}', 120, WHITE, seg(u, 0.2, 0.4), f='mono', glow=0.4)
        texto(img, fx, 540, 1260, 'R = 2024 · S = 2025 · T = 2026', 30, GRIS, seg(u, 0.9, 1.1), f='mono', glow=0)
    fr.ui.append(ui)
    return finish(fr, fi)


# 12. y el 9.º es un candado: el candado cae sobre el carácter 9 y se cierra; «CANDADO» de cristal
def s_candado(t, fi, u, d):
    uc = Wp(12, 'candado') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, 20, 6, ty=0.9), K(0.4, 4.0, -6, 6, ty=0.9), K(d, 3.9, -10, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    M.cristal(fr.base, fr.fx, 'CANDADO', u, t0=uc - 0.2, cy=0.62, entrada='zoom')

    def ui(img, fx):
        kicker(img, 'CARÁCTER 9 · DÍGITO VERIFICADOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        pos = vin_tira(img, fx, 540, 470, VIN_MX, 50, k=1.0, marcas={8: AMARILLO}, apagar=0.7)
        x, y = pos[8]
        e = P.entrada(u, uc - 0.1, 0.3, 'cae')
        candado(img, fx, 540, 820 + e['dy'] * 160, 2.4, k=seg(u, uc - 0.1, uc), abierto=1 - seg(u, uc + 0.25, uc + 0.4))
        texto(img, fx, 540, 885 + e['dy'] * 160, VIN_MX[8], 90, (20, 20, 20), seg(u, uc + 0.3, uc + 0.4), f='mono', glow=0)
        doodle_arrow(img, fx, x, y + 50, 540, 640, t, k=seg(u, 0.1, 0.4), col=AMARILLO, seed=6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.35, 0.3), amp=18)


# 13. una cuenta matemática con los otros 16: cada carácter → número × peso; la suma corre y sale el 2
def s_cuenta(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 0, 6, ty=0.9), K(0.4, 4.8, 8, 6, ty=0.9), K(d, 4.7, 10, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=0.8)
    k = seg(u, 0.1, max(0.6, d - 0.9))
    n = int(17 * k)
    parc = sum(valor(c) * w for c, w in list(zip(VIN_MX, PESOS))[:n])

    def ui(img, fx):
        kicker(img, 'LA CUENTA DEL DÍGITO 9', 150, seg(u, -0.1, 0.2), col=AZULC)
        marcas = {i: CYAN for i in range(n) if i != 8}
        marcas[8] = AMARILLO
        pos = vin_tira(img, fx, 540, 420, VIN_MX, 50, k=1.0, marcas=marcas)
        for i in range(n):
            if i == 8:
                continue
            x, y = pos[i]
            texto(img, fx, x, 500, str(valor(VIN_MX[i])), 26, WHITE, 1.0, f='mono', glow=0)
            texto(img, fx, x, 540, f'×{PESOS[i]}', 20, GRIS, 1.0, f='mono', glow=0)
        texto(img, fx, 540, 760, f'SUMA = {parc}', 92, WHITE, seg(u, 0.1, 0.3), f='mono', glow=0.4)
        kf = seg(u, d - 0.8, d - 0.55)
        texto(img, fx, 540, 900, f'{suma(VIN_MX)} ÷ 11 → SOBRA {suma(VIN_MX) % 11}', 56, AMARILLO, kf, f='mono', glow=0.5)
        texto(img, fx, 540, 1080, VIN_MX[8], 200, AMARILLO, P.resorte(seg(u, d - 0.55, d - 0.3)), f='mono', glow=0.7)
        texto(img, fx, 540, 1240, '¡CUADRA!', 54, VERDE, seg(u, d - 0.4, d - 0.25), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. y aquí está el error (segundo gancho): llega rompiendo la pantalla; carro con «SE VENDE» y todo en rojo
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, 60, 12, ty=0.6), K(0.3, 5.8, 30, 9, ty=0.6), K(d, 5.6, 26, 9, ty=0.6)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ERROR', u, t0=-0.05, cy=0.36, entrada='golpe')
    draw_objects(fr, carro(col=PLATA))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, -0.1, 0.1), col=(255, 120, 110))
        P.titulo_golpe(img, fx, [('El error que', 'sans'), ('sale carísimo.', 'serif')], 250, seg(u, 0.05, 0.2), size=82, col=WHITE)
        dd = ImageDraw.Draw(img)
        kk = P.resorte(seg(u, 0.3, 0.6))
        if kk > 0.05:
            w, h = int(360 * kk), int(150 * kk)
            dd.rectangle((700 - w // 2, 1150 - h // 2, 700 + w // 2, 1150 + h // 2), fill=(250, 230, 60))
            dd.text((700, 1150), 'SE VENDE', font=M.font('sansx', max(8, int(56 * kk))), fill=(20, 20, 20), anchor='mm')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.35), amp=24)


# 15. comprar un carro usado sin revisar ese número: billetes que se van y el NIV con signos de interrogación
def s_usado(t, fi, u, d):
    us = Wp(15, 'sin') - 0.1
    fr = Frame(camara(u, [K(-0.3, 7.4, -40, 10, ty=0.7), K(0.4, 6.4, -16, 9, ty=0.7), K(d, 6.2, -12, 9, ty=0.7)], cy=0.68))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.3)
    M.cristal(fr.base, fr.fx, 'USADO', u, t0=-0.1, cy=0.42, entrada='sube')
    e = P.entrada(u, -0.2, 0.3, 'cae')
    draw_objects(fr, P.tfk(carro(col=PLATA), s=0.9, t=(0, max(0.0, -e['dy']), 0)))

    def ui(img, fx):
        kicker(img, 'COMPRA DE USADO', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        dd = ImageDraw.Draw(img)
        for j in range(6):
            ph = seg(u, 0.2 + 0.12 * j, 1.2 + 0.12 * j)
            if 0 < ph < 1:
                x = 540 + (j - 2.5) * 120 + 300 * ph * (1 if j % 2 else -1)
                y = 1250 - 700 * ph
                dd.rounded_rectangle((x - 70, y - 34, x + 70, y + 34), radius=6, fill=(110, 170, 120), outline=(220, 240, 220), width=3)
                dd.text((x, y), '$', font=M.font('sansx', 40), fill=(30, 60, 30), anchor='mm')
        vin_tira(img, fx, 540, 470, '?' * 17, 46, k=seg(u, us, us + 0.4), marcas={8: ROJO}, glitch=0.0)
        texto(img, fx, 540, 560, 'SIN REVISAR', 40, ROJO, seg(u, us + 0.3, us + 0.5), f='sansx', glow=0.5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 16. si alguien lo inventa o lo cambia: los caracteres se descomponen (falla digital) y uno cambia a 8
def s_cambian(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.4, 10, 6, ty=0.9), K(0.4, 4.0, -8, 6, ty=0.9), K(d, 3.9, -10, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.9)
    g = seg(u, 0.1, 0.4) * (1 - seg(u, d - 0.9, d - 0.6))

    def ui(img, fx):
        kicker(img, 'NÚMERO ALTERADO · EJEMPLO', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        v = VIN_MX if u < d - 0.8 else VIN_MAL
        vin_tira(img, fx, 540, 760, v, 54, k=1.0, marcas={14: ROJO} if u > d - 0.8 else {}, glitch=g, t=t)
        texto(img, fx, 540, 900, 'LIMADO · REGRABADO · INVENTADO', 32, GRIS, seg(u, 0.3, 0.5), f='mono', glow=0)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, 0.4 * g, amp=10)


# 17. la cuenta del 9.º casi nunca cuadra: la suma da otro número y el candado se pone rojo
def s_nocuadra(t, fi, u, d):
    un = Wp(17, 'nunca') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.6, -10, 6, ty=0.9), K(0.4, 4.2, 8, 6, ty=0.9), K(d, 4.1, 10, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=0.9)
    s_mal = suma(VIN_MAL)

    def ui(img, fx):
        kicker(img, 'LA CUENTA DEL DÍGITO 9', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        vin_tira(img, fx, 540, 420, VIN_MAL, 50, k=1.0, marcas={14: ROJO, 8: AMARILLO})
        texto(img, fx, 540, 620, f'SUMA = {s_mal}', 84, WHITE, seg(u, 0.0, 0.2), f='mono', glow=0.4)
        texto(img, fx, 540, 740, f'{s_mal} ÷ 11 → SOBRA {s_mal % 11}', 54, ROJO, seg(u, 0.3, 0.5), f='mono', glow=0.5)
        texto(img, fx, 540, 900, f'{s_mal % 11}  ≠  {VIN_MAL[8]}', 150, ROJO, P.resorte(seg(u, un, un + 0.3)), f='mono', glow=0.7)
        candado(img, fx, 540, 1200, 1.6, k=seg(u, un + 0.2, un + 0.4), abierto=1.0, col=ROJO)
        texto(img, fx, 540, 1380, 'NO CUADRA', 64, ROJO, seg(u, un + 0.3, un + 0.5), f='sansx', glow=0.6)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.3, 0.3), amp=18)


# 18. antes de pagar: tablero, puerta (y factura en la siguiente): tarjetas que caen en fila
def _tarjeta(img, fx, x, y, titulo, vin, k, col=WHITE, ok=0.0, roto=False):
    if k <= 0.01:
        return
    dd = ImageDraw.Draw(img)
    w, h = 920, 150
    yy = y - (1 - P.rebote(k)) * 400
    dd.rounded_rectangle((x - w / 2, yy - h / 2, x + w / 2, yy + h / 2), radius=18, fill=(16, 17, 22), outline=M.scale_c(col, 0.9), width=3)
    texto(img, fx, x - w / 2 + 30, yy - 38, titulo, 26, GRIS, 1.0, f='mono', glow=0, anchor='lm')
    vin_tira(img, fx, x, yy + 22, vin, 40, k=1.0)
    if ok > 0.01:
        texto(img, fx, x + w / 2 - 40, yy - 38, '✓', 44, VERDE, ok, f='sansx', glow=0.6)


def s_pagar(t, fi, u, d):
    ut = Wp(18, 'tablero') - 0.15
    up = Wp(18, 'puerta') - 0.15
    fr = Frame(camara(u, [K(-0.3, 5.0, 30, 8, ty=0.9), K(0.4, 4.6, 6, 6, ty=0.9), K(d, 4.5, 2, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.9, beam=0.4)

    def ui(img, fx):
        kicker(img, 'COMPARA 3 LUGARES', 150, seg(u, -0.1, 0.2), col=AZULC)
        P.titulo_golpe(img, fx, [('Antes de pagar…', 'sans')], 300, seg(u, -0.25, -0.1), size=84)
        _tarjeta(img, fx, 540, 520, 'TABLERO (PARABRISAS)', VIN_MX, seg(u, ut, ut + 0.35))
        _tarjeta(img, fx, 540, 760, 'MARCO DE LA PUERTA', VIN_MX, seg(u, up, up + 0.35))
        texto(img, fx, 540, 1000, 'FACTURA: …', 40, GRIS, seg(u, up + 0.5, up + 0.7), f='mono', glow=0)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, ut + 0.3, 0.25), golpe_k(u, up + 0.3, 0.25)), amp=12)


# 19. y el de la factura tienen que ser idénticos: la tercera tarjeta cae, se alinean y palomita; «IDÉNTICOS»
def s_identicos(t, fi, u, d):
    uf = Wp(19, 'factura') - 0.15
    ui_ = Wp(19, 'identicos') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, -20, 8, ty=0.9), K(0.4, 4.6, -4, 6, ty=0.9), K(d, 4.5, 0, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.9, beam=0.4)
    M.cristal(fr.base, fr.fx, 'IDÉNTICOS', u, t0=ui_ - 0.15, cy=0.8, entrada='golpe')

    def ui(img, fx):
        kicker(img, 'LOS TRES IGUALES, CARÁCTER POR CARÁCTER', 150, seg(u, -0.1, 0.2), col=AZULC)
        ok = seg(u, ui_, ui_ + 0.3)
        _tarjeta(img, fx, 540, 420, 'TABLERO (PARABRISAS)', VIN_MX, 1.0, ok=ok)
        _tarjeta(img, fx, 540, 620, 'MARCO DE LA PUERTA', VIN_MX, 1.0, ok=ok)
        _tarjeta(img, fx, 540, 820, 'FACTURA', VIN_MX, seg(u, uf, uf + 0.35), ok=ok)
        if ok > 0:
            dd = ImageDraw.Draw(img)
            for i in range(17):
                x = 540 - 40 * 0.78 * 17 / 2 + 40 * 0.78 * (i + 0.5)
                dd.line([(x, 470), (x, 820)], fill=M.scale_c(VERDE, 0.5 * ok), width=2)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uf + 0.3, 0.3), amp=14)


# 20. en la página del REPUVE lo consultas gratis: el celular con la consulta (se escribe el NIV)
def s_repuve(t, fi, u, d):
    ug = Wp(20, 'gratis') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.0, 30, 6, ty=0.95), K(0.4, 2.45, 10, 4, ty=0.95), K(d, 2.35, 6, 4, ty=0.95)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'GRATIS', u, t0=ug - 0.1, cy=0.78, entrada='zoom')
    n = int(17 * seg(u, 0.2, ug + 0.2))
    e = P.entrada(u, -0.25, 0.3, 'pop')
    draw_objects(fr, P.tfk(P.celular(scr_repuve(n), ry=-8 + 4 * math.sin(t * 0.8)), s=max(0.05, e['escala'])))

    def ui(img, fx):
        kicker(img, 'REPUVE · CONSULTA CIUDADANA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1460, 'CON EL NIV, LA PLACA O EL FOLIO', eout(seg(u, ug + 0.3, ug + 0.6)), size=24, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. te dice si tiene reporte de robo: dos casos, sin reporte (verde) y con reporte (rojo)
def s_robo(t, fi, u, d):
    ur = Wp(21, 'robo') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.8, -24, 6, ty=0.95), K(0.4, 3.3, 0, 4, ty=0.95), K(d, 3.2, 4, 4, ty=0.95)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    ms = P.tfk(P.celular(scr_repuve(17, resultado=seg(u, 0.2, 0.5), robo=False), ry=14), t=(-0.62, 0, 0))
    ms += P.tfk(P.celular(scr_repuve(17, resultado=seg(u, ur, ur + 0.3), robo=True), ry=-14), t=(0.62, 0, 0))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'RESULTADO · EJEMPLO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 300, 1450, 'TRATO SEGURO', eout(seg(u, 0.4, 0.7)), size=26, border=VERDE, dot=False)
        pill(img, fx, 780, 1450, 'NO LO COMPRES', eout(seg(u, ur + 0.3, ur + 0.6)), size=26, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ur + 0.2, 0.3), amp=16)


# 22. nunca vas a ver una I, una O ni una Q: las tres letras gigantes que caen y se tachan
def s_ioq(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 40, 8, ty=0.9), K(0.4, 4.6, 10, 6, ty=0.9), K(d, 4.5, 6, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0, beam=0.5)
    us = [Wp(22, 'i', 1) - 0.1, Wp(22, 'o', 0) - 0.1, Wp(22, 'q') - 0.1]

    def ui(img, fx):
        kicker(img, 'LETRAS PROHIBIDAS EN EL NIV', 150, seg(u, -0.1, 0.2), col=AZULC)
        vin_tira(img, fx, 540, 330, VIN_MX, 44, k=seg(u, -0.25, 0.1))
        for j, (ch, u0) in enumerate(zip('IOQ', us)):
            k = seg(u, u0, u0 + 0.25)
            x = 220 + 320 * j
            y = 800 - (1 - P.rebote(k)) * 500
            texto(img, fx, x, y, ch, 300, WHITE, k, f='mono', glow=0.4)
            if u > u0 + 0.4:
                doodle_arrow(img, fx, x - 120, y - 140, x + 120, y + 140, t, k=seg(u, u0 + 0.4, u0 + 0.6), col=ROJO, seed=j)
                doodle_arrow(img, fx, x + 120, y - 140, x - 120, y + 140, t, k=seg(u, u0 + 0.5, u0 + 0.7), col=ROJO, seed=j + 3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, us[0] + 0.25, 0.2), golpe_k(u, us[1] + 0.25, 0.2), golpe_k(u, us[2] + 0.25, 0.2)), amp=12)


# 23. así nadie las confunde con 1 y 0: la I se vuelve 1 y la O se vuelve 0 (morph) en un NIV escrito a mano
def s_confunde(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, -20, 6, ty=0.9), K(0.4, 4.2, 0, 6, ty=0.9), K(d, 4.1, 4, 6, ty=0.9)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0)
    km = P.eout4(seg(u, 0.4, 0.9))

    def ui(img, fx):
        kicker(img, 'POR QUÉ', 150, seg(u, -0.1, 0.2), col=AZULC)
        for j, (a, b) in enumerate((('I', '1'), ('O', '0'))):
            x = 340 + 400 * j
            texto(img, fx, x, 760, a, 280, M.mixc(WHITE, (90, 90, 98), km), 1.0 - 0.6 * km, f='mono', glow=0.2)
            texto(img, fx, x + 120 * km, 760, b, 280, AMARILLO, km, f='mono', glow=0.5)
            texto(img, fx, x, 1000, f'{a} ≈ {b}', 50, GRIS, seg(u, 0.2, 0.4), f='mono', glow=0)
        texto(img, fx, 540, 1150, 'UN SOLO SIGNIFICADO POR CARÁCTER', 34, CYAN, seg(u, 1.0, 1.2), f='mono', glow=0.3)
    fr.ui.append(ui)
    return finish(fr, fi)


# 24. mándaselo a tu compa que va a comprar carro usado: el sedán vino derrapa al centro con el NIV arriba
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 7.6, 80, 10, ty=0.6), K(0.4, 6.2, 34, 9, ty=0.6), K(d, 6.0, 28, 9, ty=0.6)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.6)
    e = P.entrada(u, -0.2, 0.3, 'cae')
    draw_objects(fr, P.tfk(carro(), t=(0, max(0.0, -e['dy']), 0)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que va a comprar usado.', 'serif')], 230, seg(u, 0.0, 0.15), size=72)
        vin_tira(img, fx, 540, 520, VIN_MX, 40, k=seg(u, 0.3, 0.8), marcas={0: AMARILLO, 8: AMARILLO, 9: VERDE})
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


# ------------------------------------------------------------------ escenas dobles (frases muy cortas: dos ideas, un corte interno)
_T0, _ = montaje.cargar(TEMA)


def _off(ia, ib):
    return (_T0[ib][0] - _T0[ia][0]) if _T0 else 0.0


def _cut(ia, ib, palabra=None, lead=0.15):
    return _off(ia, ib) + (Wp(ib, palabra) if palabra else 0.0) - lead


def combo(fa, fb, ia, ib, palabra=None, lead=0.15, tr=None, dur=0.25):
    """Una escena que muestra fa y, con un corte interno rápido (tr), sigue con fb (fb recibe su propio u)."""
    def fn(t, fi, u, d):
        off = _off(ia, ib)
        cut = _cut(ia, ib, palabra, lead)
        if u < cut:
            return fa(t, fi, u, cut + 0.2)
        ub, db = u - off, d - off
        if u < cut + dur:
            k = seg(u, cut, cut + dur)
            A, B = fa(t, fi, u, cut + 0.2), fb(t, fi, ub, db)
            return tr(A, B, k) if tr else M.tr_whip(A, B, k, -1)
        return fb(t, fi, ub, db)
    return fn


C34 = _cut(3, 4, 'tablero', 0.45)
C56 = _cut(5, 6, 'pais', 0.35)
C1415 = _cut(14, 15, None, -0.25)
s_niv_tablero = combo(s_niv, s_tablero, 3, 4, 'tablero', 0.45)
s_primero_pais = combo(s_primero, s_pais, 5, 6, 'pais', 0.35, tr=lambda A, B, k: M.tr_iris(A, B, k, 0.5, 0.42))
s_error_usado = combo(s_error, s_usado, 14, 15, None, -0.25, tr=lambda A, B, k: M.tr_golpe(A, B, k, 0.5, 0.5))

ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45),
                sfx=[(-4.0, 'whoosh', 0.6), (-4.4, 'cristal', 0.6)] + [(-3.3 + 0.11 * j, 'click', 0.22) for j in range(22)] +
                    [(U_ENTER - 0.05, 'click', 1.0), (U_ENTER, 'whoosh', 0.9), (0.4, 'bass', 0.6)]),
           dict(desde=1, fn=s_puerta, tr='giro', c=(0.5, 0.55), sfx=[(0.5, 'click', 0.8), (0.6, 'whoosh_suave', 0.5), (0.9, 'scribble', 0.5)]),
           dict(desde=2, fn=s_etiqueta, tr='zoom', c=(0.62, 0.55), sfx=[(0.1, 'slap', 0.7)] + [(1.0 + 0.06 * j, 'tick', 0.3) for j in range(17)]),
           dict(desde=3, fn=s_niv_tablero, tr='cristal', palabra='NIV',
                sfx=[(0.3 + 0.12 * j, 'tick2', 0.4) for j in range(5)] + [(C34 - 0.1, 'whoosh', 0.9)] +
                    [(C34 + 0.6 + 0.6 * j, 'click', 0.7) for j in range(3)]),
           dict(desde=5, fn=s_primero_pais, tr='push', c=(0.5, 0.6),
                sfx=[(0.1, 'whoosh', 0.5), (0.6, 'bass', 0.8), (0.65, 'scribble', 0.5), (C56 - 0.1, 'shimmer', 0.6), (C56, 'chime_c', 0.4),
                     (C56 + 0.9, 'chime_a', 0.5), (C56 + 1.1, 'chime_b', 0.5)]),
           dict(desde=7, fn=s_mexico, tr='golpe', sfx=[(0.1, 'scribble', 0.5), (0.4, 'scribble', 0.4)]),
           dict(desde=8, fn=s_lista, tr='rebanadas', sfx=[(-0.2, 'slap', 0.5), (0.9, 'slap', 0.5), (2.0, 'slap', 0.5)]),
           dict(desde=9, fn=s_dos, tr='cubo', sfx=[(0.1, 'thud', 0.8), (0.45, 'thud', 0.8), (0.3, 'tick', 0.5), (0.65, 'tick', 0.5)]),
           dict(desde=10, fn=s_cambia, tr='wipe', sfx=[(0.3, 'scribble', 0.5)] + [(0.33 * j, 'tick2', 0.3) for j in range(6)]),
           dict(desde=11, fn=s_anio, tr='deslizar', sfx=[(0.1, 'scribble', 0.4)] + [(0.2 + 0.08 * j, 'tick', 0.3) for j in range(9)]),
           dict(desde=12, fn=s_candado, tr='zoom', c=(0.5, 0.3), sfx=[(1.0, 'click', 1.0), (1.05, 'bass', 0.7)]),
           dict(desde=13, fn=s_cuenta, tr='mosaico', sfx=[(0.1 + 0.1 * j, 'tick', 0.3) for j in range(16)] + [(2.0, 'chime_c', 0.6)]),
           dict(desde=14, fn=s_error_usado, tr='rompe', c=(0.5, 0.45),
                sfx=[(0.2, 'sub', 0.9), (0.4, 'slap', 0.6), (C1415 - 0.1, 'whoosh', 0.8), (C1415, 'bass', 0.9)] +
                    [(C1415 + 0.3 + 0.12 * j, 'whoosh', 0.15) for j in range(6)]),
           dict(desde=16, fn=s_cambian, tr='glitch', sfx=[(0.2, 'digital', 0.7), (1.0, 'digital', 0.5)]),
           dict(desde=17, fn=s_nocuadra, tr='flash', sfx=[(0.3, 'tick', 0.5), (1.0, 'sub', 0.9), (1.2, 'click', 0.6)]),
           dict(desde=18, fn=s_pagar, tr='rebanadas', sfx=[(-0.2, 'bass', 0.6), (0.6, 'thud', 0.7), (1.5, 'thud', 0.7)]),
           dict(desde=19, fn=s_identicos, tr='cubo_izq', sfx=[(0.6, 'thud', 0.7), (1.6, 'chime_b', 0.6), (1.7, 'chime_c', 0.5)]),
           dict(desde=20, fn=s_repuve, tr='zoom', c=(0.5, 0.5), sfx=[(0.2 + 0.08 * j, 'click', 0.2) for j in range(17)]),
           dict(desde=21, fn=s_robo, tr='deslizar', sfx=[(0.3, 'chime_b', 0.6), (1.4, 'burst', 0.6), (1.45, 'bass', 0.7)]),
           dict(desde=22, fn=s_ioq, tr='remolino', sfx=[(0.6, 'thud', 0.6), (1.1, 'thud', 0.6), (1.6, 'thud', 0.6), (2.0, 'scribble', 0.6)]),
           dict(desde=23, fn=s_confunde, tr='giro', sfx=[(0.4, 'whoosh_suave', 0.6), (1.0, 'chime_a', 0.5)]),
           dict(desde=24, fn=s_compa, tr='ritmo', sfx=[(0.05, 'slap', 0.7), (0.15, 'bass', 0.7)]),
           dict(desde=25, loop=True, tr='deslizar_abajo')]

if __name__ == '__main__':
    montaje.cli(globals())
