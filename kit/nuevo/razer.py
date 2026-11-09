"""Reel EXTRA (pedido de Efrén, 9-nov-2026): «Tu "razer" no es un RZR» — la historia de Can-Am contada por sus side by side.
Efrén: en México es muy popular irse de ruta en «razers», pero la gente no sabe que RZR es un modelo de Polaris y a todo
vehículo parecido le dice «razer». Quiere la historia de Can-Am hablando más de los Maverick y los Commander.
Vehículos = FOTOS REALES en 3D (recorte + profundidad + órbita con paralaje, kit/nuevo/foto3d.py), nada recreado.
Inicio tipo 11 (pregunta directa en texto grande que se rompe y deja ver el objeto). Voz Isaac, 68 s.

Datos (fuentes en guiones/2026-11-09_razer.txt): RZR = modelo de Polaris (EE. UU.), salió en 2007 como modelo 2008 y
creó el segmento del side by side deportivo (Wikipedia «Polaris RZR», Powersports Business 2007); Can-Am nace en Canadá
(Bombardier) y produce motos de motocross desde 1973, última en 1987; 2006: las cuatrimotos de BRP pasan a llamarse Can-Am;
junio 2010: Commander, primer side by side de Can-Am, 85 hp, el de más potencia del mercado (Powersports Business,
utvguide); 2013: Maverick 1000R (101 hp) para competir contra el RZR XP (Wikipedia «Can-Am Off-Road»); sept. 2014: primer
side by side con turbo de fábrica (Wikipedia, SuperATV); Maverick X3 2017: 154 hp; X3 Turbo RR: 200 hp (BRP); Maverick R
2024: 240 hp (BRP, 20-ago-2023); Juárez: Maverick, Commander, Defender y Outlander, 2 millones desde 2007 (BRP, ene-2026).
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
import canam as CA
from motor2 import (Frame, Cam, space, finish, kicker, pill, doodle_circle, doodle_arrow, chart_grow, seg, ease, eout,
                    clamp, lerp, CYAN, RED, WHITE)
from canam import veh, en, credito, escenario, piso, texto_grande, golpe_k, sacudir, mov, AMARILLO

TEMA = 'razer'
TXT = ['¿Te vas de ruta en razer? Casi seguro… no es un razer.',
       'El razer, que se escribe RZR, es un modelo de Polaris, una marca de Estados Unidos.',
       'Salió en 2007 y pegó tanto que a todo lo que se le parece le decimos razer.',
       'Como cuando a cualquier pañuelo le dices Kleenex.',
       'Su nombre real es side by side: vas sentado al lado de tu copiloto.',
       'Y muchos de los que ves en la ruta son de otra marca: Can-Am.',
       'Nació en Canadá en 1973… haciendo motos de motocross.',
       'Pero en 1987 hizo su última moto… y el nombre desapareció.',
       'Volvió en 2006 con cuatrimotos, y en 2010 sacó su primer side by side: el Commander.',
       'Con 85 caballos, era el más potente de todos.',
       'En 2013 llegó el Maverick, hecho para pelearle de frente al razer.',
       'Y al año siguiente sacó el primer side by side con turbo de fábrica.',
       'Hoy el Maverick R tiene 240 caballos… y muchos Can-Am se arman en Ciudad Juárez.',
       'Mándaselo a tu amigo que le dice razer a todo,',
       'porque igual el suyo… es un Can-Am.']
VOZ = list(TXT)
VOZ[0] = '[curious] ' + TXT[0]
VOZ[1] = 'El razer, que se escribe erre, zeta, erre, es un modelo de Polaris, una marca de Estados Unidos.'
VOZ[2] = 'Salió en dos mil siete y pegó tanto que a todo lo que se le parece le decimos razer.'
VOZ[6] = 'Nació en Canadá en mil novecientos setenta y tres… haciendo motos de motocross.'
VOZ[7] = '[excited] Pero en mil novecientos ochenta y siete hizo su última moto… y el nombre desapareció.'
VOZ[8] = 'Volvió en dos mil seis con cuatrimotos, y en dos mil diez sacó su primer side by side: el Commander.'
VOZ[9] = 'Con ochenta y cinco caballos, era el más potente de todos.'
VOZ[10] = 'En dos mil trece llegó el Maverick, hecho para pelearle de frente al razer.'
VOZ[12] = 'Hoy el Maverick R tiene doscientos cuarenta caballos… y muchos Can-Am se arman en Ciudad Juárez.'
WORDS_JSON = '/home/claude/words_razer.json'

# ---------------------------------------------------------------- fotos nuevas (Wikimedia Commons, CC0 / CC BY / PD)
FOTOS = os.path.join(HERE, 'img', 'canam')
CA.CREDITO.update({'rzr23': 'FOTO: HJUDALL · CC0', 'rzr24': 'FOTO: HJUDALL · CC0',
                   'comp': 'FOTO: MINISTERIO DE DEFENSA DEL PERÚ · CC BY 2.0',
                   'ohv3': 'FOTO: BLM OREGON & WASHINGTON · DOMINIO PÚBLICO'})
for _n, _kw in [('rzr23', {}), ('rzr24', {}),
                ('comp', dict(recorte=(0.0, 0.31, 0.50, 1.0), borrar=[(0.64, 0.10, 0.88, 0.40), (0.90, 0.0, 1.0, 0.43)]))]:
    CA.VEH[_n] = F3.preparar(f'{FOTOS}/canam_i_{_n}.jpg', _n, **_kw)
CA.ESC['ohv3'] = F3.preparar_escena(f'{FOTOS}/canam_i_ohv3.jpg', 'ohv3')
ESC = CA.ESC
CRED = CA.CREDITO


# ================================================================== tiempos
def _palabras(i):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split()


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


_WS = []


def W(i, k):
    if not _WS and os.path.exists(WORDS_JSON):
        d = json.load(open(WORDS_JSON))['words']
        _WS.extend([w for w in d if w.get('type', 'word') == 'word' and not w['text'].startswith('[')])
    idx = sum(len(_palabras(j)) for j in range(i)) + k
    if not _WS or idx >= len(_WS):
        return TT(i) + (TE(i) - TT(i)) * k / len(_palabras(i))
    return _WS[idx]['start'] + (TT(0) - _WS[0]['start'])


def Wu(i, k):
    return W(i, k) - TT(i)


def F(k, s):
    return M.font(k, s)


def etiqueta(img, fx, x, y, txt, k, col=AMARILLO, ang=-6, size=34):
    """Calcomanía que se pega con golpe (para «¿RAZER?»)."""
    if k <= 0.01:
        return
    s = 1 + 0.8 * (1 - P.eout4(k))
    f = F('sansx', int(size * s))
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    bx = d0.textbbox((0, 0), txt, font=f)
    w, h = bx[2] - bx[0] + 40, bx[3] - bx[1] + 28
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=10, fill=col + (255,))
    dl.text((20 - bx[0], 14 - bx[1]), txt, font=f, fill=(20, 20, 24, 255))
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    if k < 1:
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * min(1, k * 3))))
    img.paste(lay, (int(x - lay.width / 2), int(y - lay.height / 2)), lay)


def lineas_velocidad(img, fx, t, k, y0=700, y1=1300, n=14, col=WHITE):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    rng = np.random.RandomState(5)
    for j in range(n):
        y = y0 + (y1 - y0) * rng.rand()
        L = 120 + 260 * rng.rand()
        x = ((t * (1400 + 900 * rng.rand()) + rng.rand() * 2000) % 2200) - 600
        d.line([(1080 - x, y), (1080 - x - L, y)], fill=M.scale_c(col, 0.55 * k), width=3)
        df.line([(1080 - x, y), (1080 - x - L, y)], fill=M.scale_c(col, 0.25 * k), width=8)


def turbina(img, fx, cx, cy, r, ang, k, col=CYAN):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    c = M.scale_c(col, k)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=5)
    df.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(col, 0.4 * k), width=16)
    for j in range(9):
        a = ang + j * 2 * math.pi / 9
        pts = [(cx + r * 0.18 * math.cos(a + s * 0.9), cy + r * 0.18 * math.sin(a + s * 0.9)) for s in (0,)]
        pts += [(cx + r * (0.2 + 0.72 * s) * math.cos(a + 0.9 * s), cy + r * (0.2 + 0.72 * s) * math.sin(a + 0.9 * s)) for s in np.linspace(0.1, 1, 7)]
        d.line(pts, fill=c, width=4, joint='curve')
    d.ellipse((cx - r * 0.18, cy - r * 0.18, cx + r * 0.18, cy + r * 0.18), fill=c)


# ================================================================== escenas
# 0. gancho (inicio 11): «¿TE VAS DE RUTA EN RAZER?» gigante se rompe y deja ver un Maverick real → «no es un RZR»
#    En el loop (u negativo): el Maverick con «ES UN CAN-AM» y la pregunta vuelve a caer encima.
def _gancho_vista(t, fi, u, pregunta):
    uQ = Wu(0, 6)
    m = mov(u, [(-4.0, dict(yaw=0.6, al=620)), (uQ, dict(yaw=0.6, al=620)), (uQ + 0.05, dict(yaw=-0.35, al=700)),
                (Wu(0, 11), dict(yaw=-0.35, al=700)), (Wu(0, 11) + 0.05, dict(yaw=0.25, al=740)), (6.0, dict(yaw=0.45, al=750))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.45)
    py = piso(fr) + 210

    def ui(img, fx):
        if not pregunta:
            M.cristal(img, fx, 'RAZER', u, t0=uQ - 0.05, cy=0.37, entrada='golpe')
        veh(img, fx, 'mavf', 540, py, m['al'], yaw=m['yaw'], pitch=0.15, t=t, alfa=0.28 if pregunta else 1.0,
            reflejo=0.0 if pregunta else 0.22)
        if pregunta:
            kq = 1.0 if u >= -0.25 else P.eout4(seg(u, -0.45, -0.25))
            s = 1 + 1.2 * (1 - kq)
            for j, (tx, f) in enumerate([('¿TE VAS', 'sansx'), ('DE RUTA EN', 'sansx'), ('RAZER?', 'sansx')]):
                texto_grande(img, fx, tx, 540, 680 + (j - 1) * 175 * s, int(150 * s), col=AMARILLO if j == 2 else WHITE,
                             a=kq, glow=0.35)
            kicker(img, 'PREGUNTA', 300, kq, col=(150, 210, 230))
        elif u >= -0.45:
            P.titulo_golpe(img, fx, [('Casi seguro', 'sans'), ('no es un RZR.', 'serif')], 200, seg(u, uQ + 0.05, uQ + 0.2), size=90)
            P.pill_tachada(img, fx, 540, 1430, 'RAZER', eout(seg(u, Wu(0, 8), Wu(0, 8) + 0.2)), seg(u, Wu(0, 11), Wu(0, 11) + 0.3), t, size=40)
            credito(img, CRED['mavf'], k=seg(u, uQ, uQ + 0.3))
        else:                                                   # final del loop: el suyo es un Can-Am
            M.title(img, fx, [('Igual el suyo', 'sans'), ('es un Can-Am.', 'serif')], 210, seg(u, -3.0, -2.7), size=86)
            pill(img, fx, 540, 1430, 'CAN-AM MAVERICK', eout(seg(u, -1.6, -1.3)), size=40, border=CYAN)
            credito(img, CRED['mavf'])
    fr.ui.append(ui)
    return finish(fr, fi)


def s_gancho(t, fi, u, d):
    uQ = Wu(0, 6)
    if -0.45 <= u < uQ - 0.12:
        return _gancho_vista(t, fi, u, True)
    if u < -0.45 or u >= uQ + 0.26:
        out = _gancho_vista(t, fi, u, False)
        return sacudir(out, t, golpe_k(u, uQ + 0.2, 0.3), amp=18)
    A = _gancho_vista(t, fi, u, True)
    B = _gancho_vista(t, fi, u, False)
    return M.tr_rompe(A, B, seg(u, uQ - 0.12, uQ + 0.26), 0.5, 0.42)


# 1. El razer se escribe RZR: es un modelo de Polaris (RZR real en 3D)
def s_rzr(t, fi, u, d):
    us = Wu(1, 5)
    m = mov(u, [(-0.3, dict(yaw=-0.9, al=600)), (0.2, dict(yaw=-0.3, al=600)), (us, dict(yaw=-0.3, al=600)),
                (us + 0.05, dict(yaw=0.4, al=650)), (Wu(1, 12), dict(yaw=0.4, al=650)), (Wu(1, 12) + 0.05, dict(yaw=-0.1, al=690)),
                (7, dict(yaw=-0.25, al=700))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.45)
    py = piso(fr) + 200

    def ui(img, fx):
        M.cristal(img, fx, 'RZR', u, t0=us - 0.1, cy=0.37, entrada='sube', ancho=0.8)
        e = P.entrada(u, -0.3, 0.32, 'cae')
        veh(img, fx, 'rzr23', 540, py, m['al'], yaw=m['yaw'], pitch=0.15, t=t, dy=e['dy'] * 230, alfa=e['alfa'])
        kicker(img, 'SE ESCRIBE R · Z · R', 150, seg(u, -0.2, 0.1), col=(150, 210, 230))
        M.title(img, fx, [('El razer', 'sans'), ('es de Polaris.', 'serif')], 220, seg(u, -0.15, 0.2), size=86)
        pill(img, fx, 540, 1430, 'POLARIS · ESTADOS UNIDOS', eout(seg(u, Wu(1, 12) - 0.1, Wu(1, 12) + 0.2)), size=36, border=AMARILLO)
        credito(img, CRED['rzr23'], k=seg(u, 0.0, 0.3))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.02, 0.35), amp=20)


# 2. Salió en 2007 y pegó tanto que a todo le decimos razer (calcomanías «¿RAZER?» sobre Can-Am reales)
def s_2007(t, fi, u, d):
    ut = Wu(2, 10)                                             # «a todo lo que se le parece»
    m = mov(u, [(-0.2, dict(yaw=0.7)), (0.3, dict(yaw=0.0)), (ut, dict(yaw=0.0)), (ut + 0.05, dict(yaw=-0.6)), (6, dict(yaw=-0.7))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.4)
    py = piso(fr) + 230
    kr = P.eout4(seg(u, ut - 0.15, ut + 0.15))                # el RZR se va y entran los demás

    def ui(img, fx):
        P.numero_golpe(img, fx, '2007', 330, seg(u, Wu(2, 2) - 0.15, Wu(2, 2)), size=200, col=WHITE)
        if kr < 1:
            veh(img, fx, 'rzr24', 540 - 1100 * kr, py, 620, yaw=m['yaw'], pitch=0.15, t=t, alfa=1 - kr * 0.5)
            credito(img, CRED['rzr24'], k=1 - kr)
        if kr > 0:
            ur = Wu(2, 18)
            for j, (n, x, al, dy) in enumerate([('mavs', 225, 310, -150), ('defr', 860, 320, -150), ('comp', 540, 420, 110)]):
                e = P.entrada(u, ut - 0.05 + 0.12 * j, 0.25, 'pop')
                r = veh(img, fx, n, x, py + dy, al, yaw=m['yaw'], pitch=0.15, t=t + j, escala=max(0.05, e['escala']), alfa=e['alfa'],
                        reflejo=0.12)
                if r:
                    etiqueta(img, fx, x, r[1] + 30, '¿RAZER?', seg(u, ur - 0.3 + 0.12 * j, ur - 0.1 + 0.12 * j), ang=-8 + 8 * j)
            kicker(img, 'A TODO LE DECIMOS…', 470, seg(u, ut, ut + 0.3), col=(150, 210, 230))
            credito(img, 'FOTOS: KARLEHORN (CC BY 3.0) · AHUNT (CC0) · MIN. DEFENSA DEL PERÚ (CC BY 2.0)', k=seg(u, ut + 0.2, ut + 0.5))
    fr.ui.append(ui)
    ur = Wu(2, 18)
    return sacudir(finish(fr, fi), t, golpe_k(u, Wu(2, 2), 0.3) + golpe_k(u, ur - 0.1, 0.25) + golpe_k(u, ur + 0.14, 0.25), amp=14)


# 3. Como a cualquier pañuelo le dices Kleenex (caja de pañuelos en line-art + las dos «ecuaciones»)
def s_kleenex(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0)
    uk = Wu(3, 7)

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        df = ImageDraw.Draw(fx)
        k = P.resorte(seg(u, -0.25, 0.1))
        cx, cy = 540, 760
        w, h = 360 * k, 200 * k
        if k > 0.05:
            dd.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=18, outline=WHITE, width=5)
            df.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=18, outline=(90, 90, 96), width=14)
            dd.ellipse((cx - w * 0.25, cy - h / 2 - 12, cx + w * 0.25, cy - h / 2 + 12), outline=WHITE, width=4)
            ks = seg(u, 0.1, 0.5)                               # el pañuelo sale de la caja
            if ks > 0:
                yy = cy - h / 2 - 150 * ks
                pts = [(cx - 50, cy - h / 2), (cx - 70 + 15 * math.sin(t * 5), yy + 70), (cx - 40, yy + 10), (cx, yy + 30 + 10 * math.sin(t * 6)), (cx + 40, yy), (cx + 75 + 15 * math.sin(t * 5 + 1), yy + 60), (cx + 50, cy - h / 2)]
                dd.line(pts, fill=WHITE, width=5, joint='curve')
                df.line(pts, fill=(120, 120, 126), width=14, joint='curve')
        kicker(img, 'UNA MARCA QUE SE VOLVIÓ NOMBRE', 170, seg(u, -0.2, 0.1), col=(150, 210, 230))
        k1 = P.eout4(seg(u, 0.15, 0.45))
        texto_grande(img, fx, 'pañuelo', 540 - 600 * (1 - k1), 1010, 70, col=(200, 200, 210), a=k1, f='serif', glow=0.1)
        texto_grande(img, fx, '→ «KLEENEX»', 540 + 600 * (1 - k1), 1100, 80, col=WHITE, a=k1, glow=0.3)
        k2 = P.eout4(seg(u, uk - 0.2, uk + 0.1))
        texto_grande(img, fx, 'side by side', 540 - 600 * (1 - k2), 1260, 70, col=(200, 200, 210), a=k2, f='serif', glow=0.1)
        texto_grande(img, fx, '→ «RAZER»', 540 + 600 * (1 - k2), 1350, 80, col=AMARILLO, a=k2, glow=0.4)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return sacudir(out, t, golpe_k(u, uk + 0.1, 0.3), amp=14)


# 4. Su nombre real es side by side: vas al lado de tu copiloto (vista desde arriba en line-art vs cuatrimoto)
def _seat(d, df, x, y, w, h, k, col):
    if k <= 0.01:
        return
    s = P.resorte(k)
    d.rounded_rectangle((x - w * s / 2, y - h * s / 2, x + w * s / 2, y + h * s / 2), radius=22, outline=col, width=5)
    df.rounded_rectangle((x - w * s / 2, y - h * s / 2, x + w * s / 2, y + h * s / 2), radius=22, outline=M.scale_c(col, 0.4), width=14)


def s_lado(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0)
    uv, uc = Wu(4, 8), Wu(4, 13)

    def ui(img, fx):
        M.cristal(img, fx, 'SIDE BY SIDE', u, t0=-0.3, cy=0.24, entrada='golpe', alto=0.2)
        dd = ImageDraw.Draw(img)
        df = ImageDraw.Draw(fx)
        kb = clamp(seg(u, -0.2, 0.5))
        cx, cy, W2, H2 = 540, 900, 440, 640                     # vista desde arriba: carrocería, ruedas, jaula
        pts = [(cx - W2 / 2, cy - H2 / 2 + 80), (cx - W2 / 2 + 60, cy - H2 / 2), (cx + W2 / 2 - 60, cy - H2 / 2), (cx + W2 / 2, cy - H2 / 2 + 80),
               (cx + W2 / 2, cy + H2 / 2 - 40), (cx + W2 / 2 - 40, cy + H2 / 2), (cx - W2 / 2 + 40, cy + H2 / 2), (cx - W2 / 2, cy + H2 / 2 - 40),
               (cx - W2 / 2, cy - H2 / 2 + 80)]
        n = max(2, int(len(pts) * kb))
        dd.line(pts[:n], fill=WHITE, width=5, joint='curve')
        df.line(pts[:n], fill=(100, 100, 106), width=14, joint='curve')
        for j, (wx, wy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
            kw = P.resorte(seg(u, 0.2 + 0.07 * j, 0.45 + 0.07 * j))
            if kw > 0:
                x, y = cx + wx * (W2 / 2 + 30), cy + wy * (H2 / 2 - 110)
                dd.rounded_rectangle((x - 34 * kw, y - 80 * kw, x + 34 * kw, y + 80 * kw), radius=12, fill=(40, 40, 46), outline=WHITE, width=4)
        _seat(dd, df, cx - 100, cy + 40, 180, 170, seg(u, uv - 0.1, uv + 0.25), CYAN)
        _seat(dd, df, cx + 100, cy + 40, 180, 170, seg(u, uc - 0.4, uc - 0.05), AMARILLO)
        if u > uv:
            texto_grande(img, fx, 'TÚ', cx - 100, cy + 40, 48, col=CYAN, a=seg(u, uv, uv + 0.2), glow=0.5)
        if u > uc - 0.3:
            texto_grande(img, fx, 'COPILOTO', cx + 100, cy + 40, 30, col=AMARILLO, a=seg(u, uc - 0.3, uc - 0.1), glow=0.5)
            ka = seg(u, uc - 0.2, uc + 0.2)
            doodle_arrow(img, fx, cx - 20, cy + 150, cx + 20, cy + 150, t, k=ka)
        kicker(img, 'VISTA DESDE ARRIBA', 1290, seg(u, 0.3, 0.6), col=(150, 152, 160))
        pill(img, fx, 540, 1380, 'LADO A LADO = SIDE BY SIDE', eout(seg(u, uc - 0.1, uc + 0.2)), size=34, border=CYAN)
    fr.ui.append(ui)
    out = finish(fr, fi)
    s = 1 + 0.07 * P.eout4(seg(u, uv, uv + 0.25))
    return M.scale_about(out, s, 0.5, 0.48)


# 5. Muchos de los que ves en la ruta son de otra marca: Can-Am (la ruta real en 3D → Maverick real)
def s_ruta(t, fi, u, d):
    uo, uc = Wu(5, 11), Wu(5, 13)
    m = mov(u, [(-0.2, dict(yaw=-0.8)), (uo, dict(yaw=-0.8)), (uo + 0.05, dict(yaw=0.3)), (uc, dict(yaw=0.3)), (uc + 0.05, dict(yaw=-0.3)), (5, dict(yaw=-0.4))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.4, floor_a=0.6)
    py = piso(fr) + 230
    kv = seg(u, uo - 0.3, uo)

    def ui(img, fx):
        F3.dibujar_escena(img, ESC['ohv3'], (60, 560 - 120 * kv, 1020, 1280 - 120 * kv), yaw=-1 + 2 * seg(u, -0.2, uo), pitch=0.3,
                          esc=1.14, marco=14, angulo=-2 - 4 * kv, alfa=1 - 0.6 * kv)
        if u < uo:
            kicker(img, 'LA RUTA', 470, seg(u, -0.2, 0.1), col=(150, 210, 230))
            credito(img, CRED['ohv3'], y=1330)
        if u >= uc - 0.15:
            M.cristal(img, fx, 'CAN-AM', u, t0=uc - 0.15, cy=0.33, entrada='golpe')
        if kv > 0:
            e = P.entrada(u, uo - 0.3, 0.3, 'cae')
            veh(img, fx, 'mavs', 540, py, 640, yaw=m['yaw'], pitch=0.15, t=t, dy=e['dy'] * 240, alfa=e['alfa'])
            credito(img, CRED['mavs'], k=seg(u, uo, uo + 0.3))
        M.title(img, fx, [('Muchos son', 'sans'), ('de otra marca.', 'serif')], 210, seg(u, uo - 0.2, uo + 0.1), size=84)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uo, 0.35) + golpe_k(u, uc, 0.3), amp=18)


# 6. Nació en Canadá en 1973… haciendo motos de motocross (foto real de NARA en 3D)
def s_1973(t, fi, u, d):
    un = Wu(6, 4)
    m = mov(u, [(-0.3, dict(yaw=-1.0)), (0.3, dict(yaw=-0.3)), (un, dict(yaw=-0.3)), (un + 0.05, dict(yaw=0.7)), (5, dict(yaw=0.9))])
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)

    def ui(img, fx):
        F3.dibujar_escena(img, ESC['nara2'], (70, 640, 1010, 1330), yaw=m['yaw'], pitch=0.3, esc=1.14, marco=14, angulo=-2)
        P.numero_golpe(img, fx, '1973', 330, seg(u, un - 0.15, un), size=210, col=AMARILLO)
        kicker(img, 'CANADÁ · ASÍ ERA EL MOTOCROSS EN LOS 70', 170, seg(u, -0.2, 0.1), col=(150, 210, 230), size=24)
        pill(img, fx, 540, 1460, 'CAN-AM EMPEZÓ CON MOTOS', eout(seg(u, Wu(6, 10) - 0.1, Wu(6, 10) + 0.2)), size=34, border=AMARILLO)
        credito(img, CRED['nara2'], y=1380)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un, 0.35), amp=18)


# 7. SEGUNDO GANCHO: en 1987 hizo su última moto… y el nombre desapareció
def s_1987(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.8)
    u87, uu, ud = Wu(7, 2), Wu(7, 9), Wu(7, 14)

    def ui(img, fx):
        kf = seg(u, u87 + 0.2, uu + 0.4)
        if kf < 1:
            yy = 1050 + 1300 * kf ** 2
            F3.dibujar_escena(img, ESC['nara2'], (90, yy - 330, 990, yy + 330), yaw=0.4, pitch=0.3, esc=1.14, marco=14,
                              angulo=-2 + 30 * kf ** 1.5, tinte=((255, 255, 255), seg(u, -0.2, u87 + 0.2)))
        if u >= u87 - 0.1:
            M.cristal(img, fx, '1987', u, t0=u87 - 0.1, cy=0.33, entrada='golpe')
        pill(img, fx, 540, 900, 'ÚLTIMA MOTO', eout(seg(u, uu - 0.1, uu + 0.2)), size=40, border=RED)
        kd = seg(u, ud, ud + 0.9)                              # el nombre se desintegra
        if u > uu:
            a = 1 - kd
            for j, ch in enumerate('CAN-AM'):
                dx = (j - 2.5) * 130
                rng = np.random.RandomState(j)
                ox, oy = rng.uniform(-200, 200) * kd, -300 * kd * (0.5 + rng.rand())
                texto_grande(img, fx, ch, 540 + dx + ox, 1200 + oy, 150, col=WHITE, a=a * seg(u, uu, uu + 0.3), glow=0.3)
        kicker(img, 'Y ENTONCES…', 170, seg(u, -0.2, 0.1), col=(255, 140, 130))
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u87 - 0.05 <= u < u87 + 0.2 or ud <= u < ud + 0.15:
        out = M.tr_glitch(out, out, 0.5, fi)
    return sacudir(out, t, golpe_k(u, u87, 0.4) + golpe_k(u, ud, 0.3), amp=22)


# 8. Volvió en 2006 con cuatrimotos (Outlander real) → 2010: su primer side by side, el Commander (real)
def _cuatri(t, fi, u):
    m = mov(u, [(-0.3, dict(yaw=0.9)), (0.2, dict(yaw=0.2)), (5, dict(yaw=-0.2))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.4)
    py = piso(fr) + 200

    def ui(img, fx):
        e = P.entrada(u, -0.3, 0.25, 'desliza')
        veh(img, fx, 'outh', 540 + e['dy'] * 160, py, 680, yaw=m['yaw'], pitch=0.15, t=t, alfa=e['alfa'])
        kicker(img, '2006 · REVIVE EL NOMBRE', 150, seg(u, -0.2, 0.1), col=(150, 210, 230))
        M.title(img, fx, [('Volvió', 'sans'), ('en cuatrimotos.', 'serif')], 220, seg(u, -0.15, 0.2), size=84)
        credito(img, CRED['outh'])
    fr.ui.append(ui)
    return finish(fr, fi)


def _commander(t, fi, u, u0):
    v = u - u0
    m = mov(v, [(-0.1, dict(yaw=-0.9, al=560)), (0.25, dict(yaw=-0.3, al=600)), (Wu(8, 19) - u0, dict(yaw=-0.3, al=600)),
                (Wu(8, 19) - u0 + 0.05, dict(yaw=0.4, al=660)), (6, dict(yaw=0.5, al=670))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.5)
    py = piso(fr) + 210

    def ui(img, fx):
        M.cristal(img, fx, 'COMMANDER', v, t0=Wu(8, 19) - u0 - 0.1, cy=0.37, entrada='sube')
        e = P.entrada(v, -0.05, 0.28, 'cae')
        veh(img, fx, 'comp', 540, py, m['al'], yaw=m['yaw'], pitch=0.15, t=t, dy=e['dy'] * 220, alfa=e['alfa'])
        kicker(img, '2010 · CAN-AM COMMANDER', 150, seg(v, 0.0, 0.3), col=(150, 210, 230))
        M.title(img, fx, [('Su primer', 'sans'), ('side by side.', 'serif')], 220, seg(v, 0.05, 0.35), size=84)
        credito(img, CRED['comp'], k=seg(v, 0.2, 0.5))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.22, 0.3), amp=18)


def s_commander(t, fi, u, d):
    u0 = Wu(8, 8)                                              # «y en dos mil diez»
    if u < u0 - 0.17:
        return _cuatri(t, fi, u)
    if u >= u0 + 0.15:
        return _commander(t, fi, u, u0)
    return M.tr_whip(_cuatri(t, fi, u), _commander(t, fi, u, u0), seg(u, u0 - 0.17, u0 + 0.15), 1)


# 9. Con 85 caballos, era el más potente de todos (el Commander real con líneas de velocidad + número)
def s_85(t, fi, u, d):
    un = Wu(9, 1)
    m = mov(u, [(-0.2, dict(yaw=0.7, al=640)), (0.2, dict(yaw=0.2, al=640)), (un, dict(yaw=0.2, al=640)),
                (un + 0.05, dict(yaw=-0.5, al=720)), (5, dict(yaw=-0.6, al=730))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.4)
    py = piso(fr) + 230

    def ui(img, fx):
        lineas_velocidad(img, fx, t, seg(u, un, un + 0.3))
        veh(img, fx, 'comp', 540, py, m['al'], yaw=m['yaw'], pitch=0.15, t=t)
        P.numero_golpe(img, fx, '85 HP', 330, seg(u, un - 0.15, un), size=200, col=AMARILLO)
        pill(img, fx, 540, 1440, 'EL MÁS POTENTE EN 2010', eout(seg(u, Wu(9, 7) - 0.1, Wu(9, 7) + 0.2)), size=36, border=AMARILLO)
        credito(img, CRED['comp'])
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un, 0.35), amp=20)


# 10. DUELO: en 2013 llegó el Maverick, hecho para pelearle de frente al razer (los dos reales)
def s_duelo(t, fi, u, d):
    um, ur = Wu(10, 6), Wu(10, 13)
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.9)
    yw = 0.5 * math.sin(t * 0.8)

    def ui(img, fx):
        e1 = P.entrada(u, -0.3, 0.25, 'desliza')
        uh = Wu(10, 7)
        e2 = P.entrada(u, uh - 0.25, 0.25, 'desliza')
        veh(img, fx, 'mavf', 540 - e1['dy'] * 200, 930, 440, yaw=yw, pitch=0.15, t=t, alfa=e1['alfa'], reflejo=0.12)
        ImageDraw.Draw(img).line([(80, 975), (1000, 975)], fill=M.scale_c(CYAN, 0.5), width=2)
        if u >= uh - 0.25:
            veh(img, fx, 'rzr23', 540 + e2['dy'] * 200, 1440, 420, yaw=-yw, pitch=0.15, t=t + 1, alfa=e2['alfa'], reflejo=0.12)
            pill(img, fx, 860, 1110, 'POLARIS RZR', eout(seg(u, uh, uh + 0.25)), size=30, border=AMARILLO)
        pill(img, fx, 540, 445, 'CAN-AM MAVERICK · 2013', eout(seg(u, um - 0.1, um + 0.2)), size=30, border=CYAN)
        kv = P.resorte(seg(u, ur - 0.2, ur + 0.15))
        if kv > 0:
            texto_grande(img, fx, 'VS', 540, 975, int(150 * max(0.05, kv)), col=WHITE, glow=0.8)
        kicker(img, 'DUELO', 110, seg(u, -0.2, 0.1), col=(150, 210, 230))
        M.title(img, fx, [('Hecho para', 'sans'), ('pelearle al razer.', 'serif')], 160, seg(u, Wu(10, 7) - 0.1, Wu(10, 7) + 0.25), size=72)
        credito(img, 'FOTOS: KARLEHORN (CC BY 3.0) · HJUDALL (CC0)', k=seg(u, 0.1, 0.4))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ur + 0.1, 0.35), amp=18)


# 11. Al año siguiente: el primer side by side con turbo de fábrica (Maverick real que se vuelve de cristal + turbina)
def s_turbo(t, fi, u, d):
    ut = Wu(11, 11)
    m = mov(u, [(-0.2, dict(yaw=-0.8)), (0.3, dict(yaw=-0.2)), (ut, dict(yaw=-0.2)), (ut + 0.05, dict(yaw=0.5)), (5, dict(yaw=0.6))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.45)
    py = piso(fr) + 220
    kx = seg(u, ut - 0.3, ut + 0.1)

    def ui(img, fx):
        M.cristal(img, fx, 'TURBO', u, t0=ut - 0.1, cy=0.35, entrada='zoom')
        a = CA.VEH['mavs']
        r = F3.dibujar(img, a, 540, py - 330, 660, yaw=m['yaw'], pitch=0.15, luz=(-0.65 + 0.55 * math.sin(t * 0.9), -0.62), fx=fx,
                       reflejo=0.2, piso_y=py, xray=0.85 * kx)
        if r and kx > 0:
            x, y = en(r, 0.40, 0.42)
            turbina(img, fx, x, y, 70, t * 18, kx)
            pill(img, fx, x, y - 130, 'TURBO', eout(seg(u, ut, ut + 0.25)), size=30, border=CYAN)
        kicker(img, '2014 · AL AÑO SIGUIENTE', 150, seg(u, -0.2, 0.1), col=(150, 210, 230))
        M.title(img, fx, [('El primero', 'sans'), ('con turbo de fábrica.', 'serif')], 220, seg(u, Wu(11, 6) - 0.1, Wu(11, 6) + 0.25), size=74)
        credito(img, CRED['mavs'])
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ut + 0.1, 0.3), amp=16)


# 12. Hoy: 240 caballos (gráfico que crece con datos reales) → se arman en Ciudad Juárez (Tierra con pin)
def _grafica(t, fi, u):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0)

    def ui(img, fx):
        kicker(img, 'CABALLOS DE FUERZA · CAN-AM', 170, seg(u, -0.2, 0.1), col=(150, 210, 230))
        M.title(img, fx, [('De 85', 'sans'), ('a 240 caballos.', 'serif')], 240, seg(u, -0.15, 0.2), size=84)
        chart_grow(img, fx, (90, 560, 990, 1330), [85, 101, 154, 200, 240], ['2010', '2013', '2017', '2022', '2024'], -0.2, u,
                   unit='HP', title_txt='', vmax=260, line=True, tag='BRP')
        pill(img, fx, 540, 1420, 'MAVERICK R · 240 HP', eout(seg(u, Wu(12, 6) - 0.1, Wu(12, 6) + 0.2)), size=36, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_240(t, fi, u, d):
    u0 = Wu(12, 13)                                            # «en Ciudad Juárez»
    if u < u0 - 0.18:
        return _grafica(t, fi, u)
    v = u - u0 + 0.6
    if u >= u0 + 0.14:
        return CA._jrz_tierra(t, fi, v)[0]
    A = _grafica(t, fi, u)
    B, (cx, cy) = CA._jrz_tierra(t, fi, v)
    return M.tr_zoom_through(A, B, seg(u, u0 - 0.18, u0 + 0.14), 0.5, 0.5)


# 13. Mándaselo a tu amigo que le dice razer a todo (RZR, Maverick y Commander reales con calcomanía)
def s_mandalo(t, fi, u, d):
    m = mov(u, [(-0.2, dict(yaw=0.7)), (0.3, dict(yaw=0.0)), (1.2, dict(yaw=0.0)), (1.25, dict(yaw=-0.6)), (4, dict(yaw=-0.7))])
    fr = escenario(t, yaw_deg=9 * m['yaw'], beam=0.4)
    py = piso(fr) + 230
    ur = Wu(13, 7)

    def ui(img, fx):
        for j, (n, x, al, dy) in enumerate([('rzr23', 270, 330, -30), ('comp', 820, 360, -20), ('mavf', 540, 450, 70)]):
            e = P.entrada(u, -0.3 + 0.1 * j, 0.28, 'cae')
            r = veh(img, fx, n, x, py + dy, al, yaw=m['yaw'], pitch=0.15, t=t + j, dy=e['dy'] * 200, alfa=e['alfa'], reflejo=0.12)
            if r:
                etiqueta(img, fx, x, r[1] + 20, '¿RAZER?', seg(u, ur - 0.2 + 0.1 * j, ur + 0.1 * j), ang=8 - 8 * j)
        M.title(img, fx, [('Mándaselo a tu amigo', 'sans'), ('que le dice razer a todo.', 'serif')], 210, seg(u, -0.2, 0.15), size=66)
        credito(img, 'FOTOS: HJUDALL (CC0) · MIN. DEFENSA DEL PERÚ (CC BY 2.0) · KARLEHORN (CC BY 3.0)', k=seg(u, 0.2, 0.5))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.0, 0.3) + golpe_k(u, ur, 0.25), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45), sfx=[]),
           dict(desde=1, fn=s_rzr, tr='cubo', sfx=[]),
           dict(desde=2, fn=s_2007, tr='golpe', sfx=[]),
           dict(desde=3, fn=s_kleenex, tr='mosaico', sfx=[]),
           dict(desde=4, fn=s_lado, tr='deslizar', sfx=[]),
           dict(desde=5, fn=s_ruta, tr='zoom', sfx=[]),
           dict(desde=6, fn=s_1973, tr='iris', sfx=[]),
           dict(desde=7, fn=s_1987, tr='rompe', c=(0.5, 0.45), sfx=[]),
           dict(desde=8, fn=s_commander, tr='flash', sfx=[]),
           dict(desde=9, fn=s_85, tr='golpe', sfx=[]),
           dict(desde=10, fn=s_duelo, tr='rebanadas', sfx=[]),
           dict(desde=11, fn=s_turbo, tr='remolino', sfx=[]),
           dict(desde=12, fn=s_240, tr='whip', sfx=[]),
           dict(desde=13, fn=s_mandalo, tr='ritmo', sfx=[]),
           dict(desde=14, loop=True, tr='giro')]


def _sfx_dinamicos():
    E = ESCENAS
    uQ = Wu(0, 6)
    E[0]['sfx'] = [(0.0, 'bass', 0.6), (uQ - 0.12, 'vidrio', 1.0), (uQ - 0.1, 'sub', 0.9), (uQ + 0.2, 'bass', 0.9), (uQ + 0.25, 'cristal', 0.6),
                   (Wu(0, 8), 'tick', 0.6), (Wu(0, 11), 'scribble', 0.6)]
    E[1]['sfx'] = [(0.02, 'sub', 0.9), (0.03, 'slap', 0.5), (Wu(1, 5), 'tick', 0.6), (Wu(1, 6), 'tick', 0.6), (Wu(1, 7), 'tick', 0.6),
                   (Wu(1, 12), 'whoosh', 0.5), (Wu(1, 12) + 0.1, 'tick', 0.5)]
    ut, ur = Wu(2, 10), Wu(2, 18)
    E[2]['sfx'] = [(Wu(2, 2) - 0.15, 'whoosh', 0.5), (Wu(2, 2), 'bass', 1.0), (ut - 0.15, 'whoosh', 0.8)] + \
                  [(ut - 0.05 + 0.12 * j, 'thud', 0.5) for j in range(3)] + [(ur - 0.3 + 0.12 * j + 0.1, 'slap', 0.8) for j in range(3)]
    uk = Wu(3, 7)
    E[3]['sfx'] = [(-0.2, 'thud', 0.5), (0.1, 'whoosh_suave', 0.5), (0.2, 'whoosh', 0.5), (uk - 0.2, 'whoosh', 0.6), (uk + 0.1, 'bass', 0.9)]
    uv, uc = Wu(4, 8), Wu(4, 13)
    E[4]['sfx'] = [(0.0, 'scribble', 0.5)] + [(0.3 + 0.07 * j, 'tick2', 0.3) for j in range(4)] + \
                  [(uv, 'chime_a', 0.6), (uc - 0.3, 'chime_b', 0.6), (uc - 0.1, 'scribble', 0.4), (uc + 0.05, 'tick', 0.6)]
    uo, uc = Wu(5, 11), Wu(5, 13)
    E[5]['sfx'] = [(-0.1, 'whoosh_suave', 0.6), (uo - 0.25, 'whoosh', 0.6), (uo, 'sub', 1.0), (uo + 0.02, 'slap', 0.5), (uc, 'bass', 0.8)]
    un = Wu(6, 4)
    E[6]['sfx'] = [(0.0, 'shimmer', 0.4), (un - 0.15, 'whoosh', 0.5), (un, 'bass', 1.0), (Wu(6, 10), 'tick', 0.6)]
    u87, uu, ud = Wu(7, 2), Wu(7, 9), Wu(7, 14)
    E[7]['sfx'] = [(u87 - 0.05, 'burst', 0.6), (u87, 'sub', 1.0), (u87 + 0.05, 'digital', 0.6), (u87 + 0.3, 'thud', 0.6), (uu, 'bass', 0.8),
                   (ud, 'digital', 0.7), (ud + 0.05, 'whoosh_suave', 0.6)]
    u0 = Wu(8, 8)
    E[8]['sfx'] = [(-0.25, 'whoosh', 0.6), (u0 - 0.2, 'whoosh', 0.9), (u0 + 0.2, 'sub', 0.9), (u0 + 0.22, 'slap', 0.5),
                   (Wu(8, 19) - 0.1, 'cristal', 0.6), (Wu(8, 19), 'whoosh', 0.5)]
    un = Wu(9, 1)
    E[9]['sfx'] = [(un - 0.15, 'whoosh', 0.6), (un, 'bass', 1.0), (un + 0.05, 'riser', 0.4), (Wu(9, 7), 'tick', 0.6)]
    um, ur = Wu(10, 6), Wu(10, 13)
    E[10]['sfx'] = [(-0.3, 'whoosh', 0.6), (um, 'tick', 0.6), (ur - 0.5, 'whoosh', 0.7), (ur, 'bass', 1.0), (ur + 0.05, 'burst', 0.4)]
    ut = Wu(11, 11)
    E[11]['sfx'] = [(-0.1, 'whoosh_suave', 0.5), (ut - 0.3, 'riser', 0.6), (ut, 'shimmer', 0.6), (ut + 0.1, 'bass', 0.9), (ut + 0.2, 'whoosh', 0.5)]
    u0 = Wu(12, 13)
    E[12]['sfx'] = [(-0.2 + 0.1 * j, 'chime_a' if j < 2 else ('chime_b' if j < 4 else 'chime_c'), 0.5) for j in range(5)] + \
                   [(Wu(12, 6), 'bass', 0.8), (u0 - 0.2, 'whoosh', 0.9), (u0 + 0.1, 'thud', 0.6), (u0 + 0.5, 'tick', 0.6)]
    ur = Wu(13, 7)
    E[13]['sfx'] = [(0.0, 'sub', 0.8)] + [(ur - 0.2 + 0.1 * j + 0.15, 'slap', 0.7) for j in range(3)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
