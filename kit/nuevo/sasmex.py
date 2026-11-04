"""Reel: «Tembló 7.4… y tu alerta no sonó.» (cómo decide el SASMEX). Mié 4-nov-2026, 19:00. Voz Isaac.
Versión con el estilo rápido (ESTILO.md §11-12). Inicio tipo 5 (número gigante). Usa la voz de la tarea diaria
(inbox/narr_alerta.mp3 + words_alerta.json).
Datos: criterios del SASMEX para la CDMX: magnitud mayor a 5 a no más de 170 km (Bloomberg Línea, SDP Noticias,
N+ 5-jun-2026); sismo 7.4 frente a Chiapas, 17-jul-2026, sin alerta (Crónica, 17-jul-2026; ejecentral);
96 sensores en la costa del Pacífico de Jalisco a Oaxaca y ninguno en Chiapas (guion de la tarea diaria, ejecentral);
nombres de los ajustes del celular (Infobae, 2-ene-2026). Posiciones de sensores y epicentros: RECREACIÓN."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, line3, dot3,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
M3 = M.M3
S = M.SS

TEMA = 'sasmex'
TXT = ['Tembló 7.4… y tu alerta no sonó.',
       'No está descompuesta:',
       'la alerta sísmica no se fija en la magnitud.',
       'Calcula cuánto va a sacudir a cada ciudad, en los primeros segundos.',
       'Mira dos casos.',
       '17 de julio: un 7.4 frente a Chiapas.',
       'No sonó.',
       'Pero uno de más de 5, a menos de 170 km de la capital, sí la activa.',
       'La diferencia: 96 sensores vigilan el Pacífico, de Jalisco a Oaxaca.',
       'En Chiapas no hay ni uno:',
       'ese sismo lo detectaron hasta que llegó a Oaxaca.',
       'Y su energía de los primeros segundos no alcanzó el nivel de alerta.',
       'Pero el error más común… está en tu bolsillo.',
       'Si apagaste las alertas de emergencia de tu celular,',
       'aunque suene la calle, a ti no te llega.',
       'En Android se llaman «alertas de emergencia inalámbricas»;',
       'en iPhone, «alertas gubernamentales».',
       'No gastan datos ni saldo: llegan por la antena.',
       'Y si el sismo nace cerca, no da tiempo:',
       'la alerta puede sonar cuando ya está temblando.',
       'Mándaselo a quien dice que la alerta está descompuesta,',
       'y revisa tu celular hoy, antes de que vuelva a temblar.']
VOZ = list(TXT)
VOZ[0] = 'Tembló siete punto cuatro… y tu alerta no sonó.'
VOZ[5] = 'Diecisiete de julio: un siete punto cuatro frente a Chiapas.'
VOZ[7] = 'Pero uno de más de cinco, a menos de ciento setenta kilómetros de la capital, sí la activa.'
VOZ[8] = 'La diferencia: noventa y seis sensores vigilan el Pacífico, de Jalisco a Oaxaca.'
ROJO = (255, 64, 56)
AMBAR = (255, 196, 90)


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


def wt(i, k):
    n = len(TXT[i].split())
    return TT(i) + (TE(i) - TT(i)) * k / n


def F(k, s):
    return M.font(k, s)


# ------------------------------------------------------------------ mapa de México (line-art en el piso)
MX = [(-117.1, 32.5), (-114.7, 32.7), (-111.0, 31.3), (-108.2, 31.3), (-108.2, 31.8), (-106.5, 31.8), (-104.5, 29.6),
      (-103.0, 29.0), (-102.4, 29.8), (-101.4, 29.8), (-100.3, 28.3), (-99.5, 27.5), (-97.4, 25.9), (-97.7, 24.0),
      (-97.8, 22.3), (-97.2, 20.6), (-96.1, 19.2), (-94.8, 18.5), (-94.4, 18.15), (-92.6, 18.6), (-91.8, 18.65),
      (-90.7, 19.4), (-90.4, 21.0), (-89.0, 21.35), (-87.6, 21.5), (-86.8, 21.2), (-87.4, 20.2), (-87.5, 19.5),
      (-88.0, 18.6), (-88.3, 18.4), (-89.15, 17.9), (-90.98, 17.8), (-90.98, 17.25), (-91.4, 17.25), (-90.4, 16.1),
      (-92.2, 15.25), (-92.2, 14.55), (-93.4, 15.7), (-94.6, 16.2), (-95.2, 16.17), (-96.5, 15.65), (-98.5, 16.3),
      (-99.9, 16.85), (-101.5, 17.6), (-102.2, 17.95), (-103.7, 18.7), (-104.3, 19.1), (-105.3, 19.9), (-105.6, 20.4),
      (-105.3, 21.5), (-105.6, 22.3), (-106.4, 23.2), (-107.4, 24.3), (-108.0, 25.0), (-109.2, 26.4), (-110.0, 27.0),
      (-110.9, 27.9), (-111.95, 28.8), (-112.7, 29.9), (-113.5, 31.3), (-114.8, 31.8),
      (-114.6, 30.3), (-113.6, 29.2), (-112.9, 28.3), (-112.2, 27.2), (-111.4, 26.0), (-110.7, 24.8), (-110.3, 24.2),
      (-109.6, 23.6), (-109.4, 23.2), (-109.9, 22.9), (-110.3, 23.4), (-111.0, 24.1), (-112.0, 24.7), (-112.2, 25.5),
      (-113.2, 26.4), (-113.9, 26.9), (-115.1, 27.85), (-114.2, 28.0), (-114.6, 28.8), (-115.6, 29.7), (-116.0, 30.5),
      (-116.6, 31.85), (-117.1, 32.5)]
COSTA = [(-105.6, 20.4), (-105.3, 19.9), (-104.3, 19.1), (-103.7, 18.7), (-102.2, 17.95), (-101.5, 17.6),
         (-99.9, 16.85), (-98.5, 16.3), (-96.5, 15.65), (-95.2, 16.17)]
CHIAPAS = [(-94.6, 16.2), (-93.4, 15.7), (-92.2, 14.55)]
CDMX = (-99.13, 19.43)
OAX = (-96.73, 17.06)
EPI_CH = (-93.7, 14.95)       # «frente a Chiapas» (recreación)
EPI_GRO = (-99.4, 16.5)
EPI_170 = (-99.5, 18.35)      # ~125 km de la CDMX (recreación)
CIUDADES = [(CDMX, 'CDMX'), ((-98.2, 19.04), 'PUEBLA'), (OAX, 'OAXACA'), ((-99.5, 17.55), 'CHILPANCINGO'),
            ((-101.19, 19.70), 'MORELIA'), ((-103.35, 20.67), 'GUADALAJARA'), ((-99.88, 16.86), 'ACAPULCO')]
KS = 0.13


def geo(lon, lat, y=0.0):
    return (lon + 101.5) * KS, y, -(lat - 23.0) * KS


def _sensores():
    rng = np.random.RandomState(4)
    seg_len = [math.dist(a, b) for a, b in zip(COSTA, COSTA[1:])]
    tot = sum(seg_len)
    out = []
    for i in range(96):
        s = (i + 0.5) / 96 * tot
        j = 0
        while s > seg_len[j]:
            s -= seg_len[j]
            j += 1
        a, b = COSTA[j], COSTA[j + 1]
        f = s / seg_len[j]
        lon, lat = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        nx, ny = -(b[1] - a[1]), (b[0] - a[0])
        n = math.hypot(nx, ny) or 1
        off = 0.15 + 0.85 * rng.rand() ** 1.5
        out.append((lon - nx / n * off, lat - ny / n * off))
    return out


SENS = _sensores()


def mapa(fr, k=1.0, a=0.85, col=WHITE):
    line3(fr, [geo(*p) for p in MX], col=col, w=2.2, a=a, glow=0.5, frac=k)


def aro(fr, c, r, col=CYAN, a=1.0, w=2.4, frac=1.0, n=72):
    x, _, z = geo(*c)
    pts = [(x + r * math.cos(2 * math.pi * i / n), 0.004, z + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
    line3(fr, pts, col=col, w=w, a=a, glow=0.7, frac=frac)


def ondas(fr, c, t0, t, col=CYAN, vel=0.55, n=4, rmax=1.6):
    for i in range(n):
        r = (t - t0 - i * 0.35) * vel
        if 0 < r < rmax:
            aro(fr, c, r, col=col, a=0.9 * (1 - r / rmax))


def cam_m(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], 0.0, p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy)


def KM(u, c, dist, yaw, pitch):
    x, _, z = geo(*c)
    return (u, dict(tx=x, tz=z, dist=dist, yaw=yaw, pitch=pitch))


def cam_t(u, claves, cy=0.55):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p.get('tx', 0.0), p.get('ty', 0.95), 0.0), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'],
               cy=cy, roll=p.get('roll', 0.0))


def KT(u, dist, yaw, pitch=6, tx=0.0, ty=0.95, roll=0.0):
    return (u, dict(tx=tx, ty=ty, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


# ------------------------------------------------------------------ pantallas del celular
def campana(d, cx, cy, s, col):
    d.polygon([(cx - 0.55 * s, cy + 0.42 * s), (cx - 0.42 * s, cy - 0.05 * s), (cx - 0.3 * s, cy - 0.42 * s),
               (cx, cy - 0.55 * s), (cx + 0.3 * s, cy - 0.42 * s), (cx + 0.42 * s, cy - 0.05 * s),
               (cx + 0.55 * s, cy + 0.42 * s)], fill=col)
    d.ellipse((cx - 0.13 * s, cy + 0.42 * s, cx + 0.13 * s, cy + 0.66 * s), fill=col)


def scr_silencio(t, glitch=0.0):
    def dib(d, im):
        d.text((210, 150), 'Alerta sísmica', font=F('sans', 34), fill=(150, 152, 160), anchor='mm')
        d.ellipse((110, 260, 310, 460), outline=(70, 72, 80), width=4)
        campana(d, 210, 360, 120, (120, 122, 130))
        d.line([(140, 430), (280, 290)], fill=ROJO, width=12)
        d.text((210, 540), 'Sin alertas', font=F('sans', 40), fill=(230, 230, 234), anchor='mm')
        d.text((210, 600), 'No se recibió ningún aviso', font=F('sanss', 24), fill=(140, 142, 150), anchor='mm')
        if glitch > 0:
            rng = np.random.RandomState(int(t * 24))
            arr = np.asarray(im).copy()
            for _ in range(int(14 * glitch)):
                y0 = rng.randint(80, 860)
                h = rng.randint(6, 40)
                arr[y0:y0 + h] = np.roll(arr[y0:y0 + h], rng.randint(-90, 90), 1)
            im.paste(Image.fromarray(arr))
    return P.pantalla(dib)


def scr_ok():
    def dib(d, im):
        d.text((210, 150), 'Alerta sísmica', font=F('sans', 34), fill=(150, 152, 160), anchor='mm')
        d.ellipse((110, 260, 310, 460), outline=CYAN, width=6)
        d.line([(160, 365), (200, 405), (270, 315)], fill=CYAN, width=14, joint='curve')
        d.text((210, 540), 'Funciona bien', font=F('sans', 40), fill=(230, 230, 234), anchor='mm')
        d.text((210, 600), 'Solo decide cuándo sonar', font=F('sanss', 24), fill=(140, 142, 150), anchor='mm')
    return P.pantalla(dib)


def scr_alerta(t):
    def dib(d, im):
        p = 0.5 + 0.5 * math.sin(t * 14)
        d.rectangle((0, 70, 420, 900), fill=(int(150 + 90 * p), 18, 16))
        campana(d, 210, 300, 170, (255, 255, 255))
        d.text((210, 520), 'ALERTA', font=F('sans', 64), fill=(255, 255, 255), anchor='mm')
        d.text((210, 590), 'SÍSMICA', font=F('sans', 64), fill=(255, 255, 255), anchor='mm')
        d.text((210, 690), 'Sismo en curso', font=F('sanss', 28), fill=(255, 220, 216), anchor='mm')
    return P.pantalla(dib)


def scr_ajuste(titulo, fila, on, claro=False):
    """Pantalla de ajustes con un interruptor. on: 0 (apagado) … 1 (encendido)."""
    bg = (242, 242, 246) if claro else (6, 7, 10)
    tx = (20, 20, 24) if claro else (235, 235, 240)
    sub = (110, 110, 118) if claro else (140, 142, 150)

    def dib(d, im):
        d.rectangle((0, 70, 420, 900), fill=bg)
        d.text((30, 120), titulo, font=F('sans', 38), fill=tx)
        y = 230
        for i, (txt, hl) in enumerate(fila):
            if hl:
                d.rounded_rectangle((14, y - 18, 406, y + 110), radius=18,
                                    fill=(255, 255, 255) if claro else (24, 26, 32), outline=CYAN, width=3)
            lines = txt.split('\n')
            for j, ln in enumerate(lines):
                d.text((34, y + j * 34), ln, font=F('sans' if hl else 'sanss', 28), fill=tx if hl else sub)
            if hl:
                k = clamp(on)
                col = M.mixc((120, 120, 128), (60, 200, 120), k)
                d.rounded_rectangle((300, y + 66, 386, y + 106), radius=20, fill=col)
                xk = 320 + 46 * k
                d.ellipse((xk - 16, y + 70, xk + 16, y + 102), fill=(255, 255, 255))
            y += 150
    return P.pantalla(dib)


def tel(scr, ry=0.0, rz=0.0, off=(0, 0, 0)):
    return P.celular(scr, ry=ry, rz=rz, off=off)


# ------------------------------------------------------------------ 0. gancho: número gigante (inicio tipo 5)
def s_gancho(t, fi, u, d):
    tc = wt(0, 4) - TT(0)                       # «y tu alerta…»: crash zoom al celular
    fr = Frame(cam_t(u, [KT(-3.6, 2.4, 40, 5), KT(-2.2, 3.0, -28, 6), KT(-0.9, 3.0, -34, 6), KT(-0.3, 7.5, 0, 4),
                         KT(tc - 0.35, 7.0, -6, 4), KT(tc, 2.9, 18, 5), KT(tc + 3.0, 2.6, 26, 5)]))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=1.0, beam=0.55)
    draw_objects(fr, tel(scr_silencio(t), ry=-8))

    def ui(img, fx):
        if u < tc + 0.1:
            P.numero_golpe(img, fx, '7.4', 820, seg(u, 0.0, 0.18), size=300)
            kicker(img, 'MAGNITUD', 1040, seg(u, 0.3, 0.6), col=(150, 210, 230))
        else:
            k = P.eout4(seg(u, tc, tc + 0.3))
            P.numero_golpe(img, fx, '7.4', 820 - 600 * k, 1.0, size=300 - 170 * k)
        P.titulo_golpe(img, fx, [('y tu alerta no sonó.', 'serif')], 330, seg(u, tc + 0.35, tc + 0.5), size=74)
    fr.ui.append(ui)
    out = finish(fr, fi)
    k = (1 - seg(u, 0.0, 2.2)) * (u >= 0) + 0.7 * max(0.0, 1 - abs(u - tc - 0.5) / 0.3)
    return sacudir(out, t, k, amp=26)


# ------------------------------------------------------------------ 1. no está descompuesta
def s_descompuesta(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 2.6, -40, 8), KT(0.25, 1.9, 6, 3), KT(2.0, 1.75, 12, 3)]))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.8, beam=0.4)
    tok = TE(1) - TT(1) - 0.1
    scr = scr_silencio(t, glitch=1 - seg(u, 0.1, tok)) if u < tok else scr_ok()
    draw_objects(fr, tel(scr, ry=4))

    def ui(img, fx):
        P.pill_tachada(img, fx, 540, 300, '¿DESCOMPUESTA?', seg(u, 0.0, 0.2), seg(u, tok - 0.2, tok + 0.1), t, size=40)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 2. no se fija en la magnitud (sismograma 3D)
def sismo_y(x, t, amp, x0=-1.6):
    q = max(0.0, x - x0)
    env = math.exp(-((q - 1.1) / 0.55) ** 2) + 0.25 * math.exp(-((q - 0.35) / 0.2) ** 2)
    return amp * env * math.sin(q * 38 + t * 2) * (0.6 + 0.4 * math.sin(q * 11))


def s_magnitud(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 3.6, 50, 10, ty=1.0), KT(0.35, 3.0, -18, 6, ty=1.0), KT(3.0, 2.8, -28, 6, ty=1.0)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.8)
    glass_type(fr.base, fr.fx, 'M', 540 * S, 900 * S, 600 * S, k=eout(seg(u, -0.2, 0.3)), fill_a=0.05)
    xs = np.linspace(-1.6, 1.6, 260)
    pts = [(x, 1.0 + sismo_y(x, t, 0.5), 0) for x in xs]
    line3(fr, pts, col=WHITE, w=2.6, a=1.0, glow=0.8, frac=P.eout4(seg(u, -0.1, 0.8)))
    line3(fr, [(-1.6, 1.0, 0), (1.6, 1.0, 0)], col=(90, 92, 100), w=1.2, a=0.8, glow=0.0)
    tm = wt(2, 8) - TT(2)

    def ui(img, fx):
        kicker(img, 'SISMOGRAMA · RECREACIÓN', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        P.pill_tachada(img, fx, 540, 1330, 'SOLO LA MAGNITUD', seg(u, tm - 0.4, tm - 0.15), seg(u, tm, tm + 0.35), t, size=38)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 3. calcula ciudad por ciudad (mapa)
NIV = {'CDMX': 0.55, 'PUEBLA': 0.4, 'OAXACA': 0.3, 'CHILPANCINGO': 0.9, 'MORELIA': 0.35, 'GUADALAJARA': 0.15,
       'ACAPULCO': 1.0}


def s_calcula(t, fi, u, d):
    fr = Frame(cam_m(u, [KM(-0.2, (-100.5, 21.5), 5.4, 0, 78), KM(0.3, (-99.5, 18.6), 3.0, 14, 52),
                         KM(2.2, (-99.5, 18.6), 3.0, 14, 52), KM(2.6, (-99.8, 18.2), 2.4, -20, 40),
                         KM(6.0, (-99.8, 18.2), 2.3, -26, 40)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8)
    mapa(fr, k=P.eout4(seg(u, -0.2, 0.5)))
    ondas(fr, EPI_GRO, TT(3) - 0.1, t, col=ROJO, vel=0.6)
    dot3(fr, geo(*EPI_GRO), r=9, col=ROJO, a=1.0)
    tc = wt(3, 6) - TT(3)
    for i, (c, nom) in enumerate(CIUDADES):
        k = P.resorte(seg(u, tc + 0.12 * i, tc + 0.12 * i + 0.35))
        h = 0.55 * NIV[nom] * max(0.0, k)
        x, _, z = geo(*c)
        col = M.mixc(CYAN, ROJO, NIV[nom])
        line3(fr, [(x, 0, z), (x, h, z)], col=col, w=6, a=1.0, glow=0.9)
        dot3(fr, (x, 0, z), r=6, col=WHITE)
    pos = [(fr.cam.p1(np.array(geo(*c, y=0.55 * NIV[nom] + 0.06))), nom) for c, nom in CIUDADES]

    def ui(img, fx):
        kicker(img, 'SASMEX · CIUDAD POR CIUDAD', 150, seg(u, 0.2, 0.5), col=(150, 210, 230))
        for i, ((x, y, z), nom) in enumerate(pos):
            k = seg(u, tc + 0.12 * i + 0.1, tc + 0.12 * i + 0.3)
            if z > 0.2 and k > 0.01:
                pill(img, fx, x, y - 26, nom, k, size=22, border=M.mixc(CYAN, ROJO, NIV[nom]), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 4. mira dos casos (tarjetas)
def tarjeta(img, fx, x, y, k, l1, l2, l3, col):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    w, h = 440, 330
    x0 = x - w / 2
    d.rounded_rectangle((x0, y, x0 + w, y + h), radius=26, fill=(14, 15, 19), outline=col, width=4)
    d.text((x, y + 60), l1, font=F('mono', 26), fill=(150, 210, 230), anchor='mm')
    d.text((x, y + 150), l2, font=F('sans', 58), fill=(245, 245, 247), anchor='mm')
    d.text((x, y + 250), l3, font=F('sans', 40), fill=col, anchor='mm')
    ImageDraw.Draw(fx).rounded_rectangle((x0, y, x0 + w, y + h), radius=26, outline=M.scale_c(col, 0.6), width=6)


def s_dos(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 4.0, -30, 12), KT(0.3, 3.4, 20, 8), KT(3.0, 3.2, 28, 8)]))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.3)
    k1 = P.eout4(seg(u, -0.3, -0.05))
    k2 = P.eout4(seg(u, -0.05, 0.2))

    def ui(img, fx):
        kicker(img, 'DOS CASOS', 380, seg(u, -0.1, 0.2), col=(150, 210, 230))
        tarjeta(img, fx, 290 - 700 * (1 - k1), 560, k1, 'CASO 1', 'M 7.4', 'NO SONÓ', ROJO)
        tarjeta(img, fx, 790 + 700 * (1 - k2), 960, k2, 'CASO 2', 'M 5+', 'SÍ SONÓ', CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 5. 17 de julio, frente a Chiapas
def s_chiapas(t, fi, u, d):
    fr = Frame(cam_m(u, [KM(-0.2, (-101.5, 23.0), 5.6, 0, 70), KM(0.35, (-94.0, 16.0), 2.0, 24, 48),
                         KM(3.0, (-94.0, 16.0), 1.85, 34, 44)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    mapa(fr)
    line3(fr, [geo(*p) for p in CHIAPAS], col=AMBAR, w=4, a=1.0, glow=0.8)
    ondas(fr, EPI_CH, TT(5) + 0.3, t, col=ROJO, vel=0.45, rmax=0.9)
    dot3(fr, geo(*EPI_CH), r=10, col=ROJO)
    pe = fr.cam.p1(np.array(geo(*EPI_CH)))
    pc = fr.cam.p1(np.array(geo(-92.9, 16.4)))

    def ui(img, fx):
        kicker(img, 'RECREACIÓN', 150, seg(u, 0.2, 0.5), col=(150, 210, 230))
        pill(img, fx, 540, 300, '17 JUL 2026 · M 7.4', P.resorte(seg(u, 0.0, 0.3)), size=40, border=ROJO)
        if pc[2] > 0.2:
            pill(img, fx, pc[0], pc[1] - 40, 'CHIAPAS', seg(u, wt(5, 7) - TT(5), wt(5, 7) - TT(5) + 0.2), size=28, border=AMBAR, dot=False)
        if pe[2] > 0.2:
            doodle_circle(img, fx, pe[0], pe[1], 70, 50, t, k=eout(seg(u, 0.6, 1.0)), col=(255, 236, 160), w=5)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 6. no sonó
def s_nosono(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 1.4, -10, 2, roll=-8), KT(0.2, 1.9, 0, 3, roll=0), KT(2.0, 1.85, 4, 3)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.6, beam=0.3)
    draw_objects(fr, tel(scr_silencio(t), ry=0, rz=3 * math.sin(t * 30) * (1 - seg(u, 0, 1.2))))
    pc = fr.cam.p1(np.array((0, 0.95, 0.05)))

    def ui(img, fx):
        M.doodle_circle  # (referencia)
        import norte as N
        N.doodle_x(img, fx, pc[0], pc[1] - 40, 260, t, eout(seg(u, 0.05, 0.4)), col=ROJO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 1 - seg(u, 0.0, 1.0), amp=18)


# ------------------------------------------------------------------ 7. M 5+ a menos de 170 km sí la activa
def s_170(t, fi, u, d):
    fr = Frame(cam_m(u, [KM(-0.2, CDMX, 2.4, -40, 70), KM(0.3, (-99.3, 18.9), 1.35, 10, 52),
                         KM(2.6, (-99.3, 18.9), 1.35, 10, 52), KM(3.0, (-99.3, 18.9), 1.15, 38, 44),
                         KM(6.0, (-99.3, 18.9), 1.1, 44, 44)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    mapa(fr, a=0.7)
    r170 = 170 / 111.0 * KS
    tk = wt(7, 10) - TT(7)
    aro(fr, CDMX, r170, col=CYAN, a=1.0, w=3, frac=P.eout4(seg(u, tk - 0.6, tk)))
    x, _, z = geo(*CDMX)
    line3(fr, [(x, 0.004, z), (x + r170, 0.004, z)], col=CYAN, w=2, a=seg(u, tk - 0.2, tk + 0.1))
    ke = P.resorte(seg(u, wt(7, 5) - TT(7) - 0.2, wt(7, 5) - TT(7) + 0.1))
    if ke > 0.01:
        dot3(fr, geo(*EPI_170), r=9 * max(0.2, ke), col=AMBAR)
        ondas(fr, EPI_170, TT(7) + wt(7, 5) - TT(7), t, col=AMBAR, vel=0.25, rmax=0.35)
    ta = wt(7, 14) - TT(7)
    act = seg(u, ta - 0.3, ta)
    dot3(fr, geo(*CDMX), r=8 + 6 * act * (0.5 + 0.5 * math.sin(t * 16)), col=M.mixc(WHITE, ROJO, act))
    if act > 0:
        ondas(fr, CDMX, TT(7) + ta - 0.3, t, col=ROJO, vel=0.3, rmax=0.5)
    pr = fr.cam.p1(np.array((x + r170 / 2, 0, z)))
    pe = fr.cam.p1(np.array(geo(*EPI_170)))
    pcx = fr.cam.p1(np.array(geo(*CDMX)))

    def ui(img, fx):
        kicker(img, 'CRITERIO DEL SASMEX PARA LA CDMX', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        if pr[2] > 0.2:
            pill(img, fx, pr[0], pr[1] - 34, '170 km', seg(u, tk - 0.1, tk + 0.15), size=30, border=CYAN, dot=False)
        if pe[2] > 0.2:
            pill(img, fx, pe[0], pe[1] + 80, 'M 5+', seg(u, wt(7, 5) - TT(7), wt(7, 5) - TT(7) + 0.2), size=30, border=AMBAR, dot=False)
        if pcx[2] > 0.2:
            pill(img, fx, pcx[0], pcx[1] - 80, 'CDMX', seg(u, 0.2, 0.4), size=28, border=WHITE, dot=False)
        P.titulo_golpe(img, fx, [('Sí la activa.', 'serif')], 1250, seg(u, ta - 0.1, ta + 0.05), size=78, col=WHITE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0, amp=10)


# ------------------------------------------------------------------ 8. 96 sensores de Jalisco a Oaxaca
def s_sensores(t, fi, u, d):
    fr = Frame(cam_m(u, [KM(-0.2, (-104.0, 19.4), 2.3, -50, 55), KM(0.35, (-103.5, 19.0), 1.8, -30, 48),
                         KM(1.5, (-101.0, 17.8), 1.9, -10, 48), KM(3.0, (-98.0, 16.8), 2.0, 12, 48),
                         KM(4.4, (-96.8, 16.5), 2.6, 22, 55), KM(6.0, (-97.0, 17.0), 2.7, 26, 56)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    mapa(fr, a=0.7)
    tn = wt(8, 3) - TT(8)
    dur = max(1.2, wt(8, 10) - TT(8) - tn)
    n = 0
    for i, c in enumerate(SENS):
        k = P.resorte(seg(u, tn + dur * i / 96, tn + dur * i / 96 + 0.18))
        if k > 0.01:
            n += 1
            dot3(fr, geo(*c, y=0.01), r=4.5 * max(0.3, k), col=CYAN, glow=1.0)
    pj = fr.cam.p1(np.array(geo(-104.6, 20.7)))
    po = fr.cam.p1(np.array(geo(-96.5, 17.6)))

    def ui(img, fx):
        kicker(img, 'SENSORES DEL SASMEX · RECREACIÓN', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        P.numero_golpe(img, fx, str(n), 330, seg(u, tn - 0.1, tn + 0.1), size=170, col=CYAN)
        kicker(img, 'SENSORES', 450, seg(u, tn, tn + 0.3), col=(150, 210, 230))
        if pj[2] > 0.2:
            pill(img, fx, pj[0], pj[1], 'JALISCO', seg(u, wt(8, 9) - TT(8), wt(8, 9) - TT(8) + 0.2), size=26, dot=False)
        if po[2] > 0.2:
            pill(img, fx, po[0], po[1], 'OAXACA', seg(u, wt(8, 11) - TT(8), wt(8, 11) - TT(8) + 0.2), size=26, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 9. en Chiapas no hay ni uno
def s_vacio(t, fi, u, d):
    fr = Frame(cam_m(u, [KM(-0.2, (-95.5, 16.4), 2.4, 20, 60), KM(0.25, (-93.6, 15.6), 1.3, 40, 40),
                         KM(3.0, (-93.6, 15.6), 1.2, 48, 38)], cy=0.56))
    space(fr, t, floor=None, bokeh=0.8)
    mapa(fr, a=0.7)
    for c in SENS[-20:]:
        dot3(fr, geo(*c, y=0.01), r=4.5, col=CYAN)
    pts = [geo(*p) for p in CHIAPAS]
    blink = 0.6 + 0.4 * math.sin(t * 10)
    for a, b in zip(pts, pts[1:]):
        for j in range(10):
            f0, f1 = j / 10, j / 10 + 0.05
            line3(fr, [tuple(np.array(a) + (np.array(b) - np.array(a)) * f0),
                       tuple(np.array(a) + (np.array(b) - np.array(a)) * f1)], col=ROJO, w=4, a=blink, glow=0.8)

    def ui(img, fx):
        P.numero_golpe(img, fx, '0', 560, seg(u, 0.0, 0.16), size=360, col=ROJO)
        kicker(img, 'SENSORES EN CHIAPAS', 790, seg(u, 0.15, 0.4), col=(255, 170, 160))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(0.0, 1 - abs(u - 0.16) / 0.3), amp=22)


# ------------------------------------------------------------------ 10. lo detectaron hasta Oaxaca
def s_viaje(t, fi, u, d):
    fr = Frame(cam_m(u, [KM(-0.2, (-94.0, 15.6), 1.6, 50, 50), KM(0.3, (-94.6, 15.9), 2.0, 70, 40),
                         KM(3.5, (-95.2, 16.0), 1.9, 80, 38)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.8)
    mapa(fr, a=0.7)
    t0 = TT(10) - 0.1
    r = max(0.0, (t - t0) * 0.16)
    x0, _, z0 = geo(*EPI_CH)
    dot3(fr, (x0, 0, z0), r=9, col=ROJO)
    for i in range(3):
        rr = r - i * 0.05
        if rr > 0:
            aro(fr, EPI_CH, rr, col=ROJO, a=0.9 - 0.25 * i)
    hit = None
    for c in SENS[-24:]:
        x, _, z = geo(*c)
        dd = math.hypot(x - x0, z - z0)
        on = r >= dd
        if on and (hit is None or dd < hit[0]):
            hit = (dd, c)
        dot3(fr, (x, 0.01, z), r=7 if on else 4.5, col=AMBAR if on else CYAN, glow=1.2 if on else 0.8)
    secs = max(0.0, (t - t0)) * 8
    ph = fr.cam.p1(np.array(geo(*hit[1]))) if hit else None

    def ui(img, fx):
        kicker(img, 'LAS ONDAS VIAJAN HASTA EL PRIMER SENSOR', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        pill(img, fx, 540, 300, f'+{secs:4.1f} s SIN AVISO', seg(u, 0.1, 0.3), size=40, border=ROJO)
        if ph and ph[2] > 0.2:
            doodle_circle(img, fx, ph[0], ph[1], 60, 44, t, k=1.0, col=AMBAR, w=5)
            pill(img, fx, ph[0], ph[1] - 70, 'DETECTADO EN OAXACA', 1.0, size=26, border=AMBAR, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 11. la energía no alcanzó el nivel
def s_energia(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 3.6, -50, 18, ty=0.9), KT(0.3, 3.0, 20, 8, ty=0.9), KT(2.4, 3.0, 20, 8, ty=0.9),
                         KT(2.8, 2.6, -14, 4, ty=0.9), KT(5.0, 2.5, -20, 4, ty=0.9)]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.4)
    tn = wt(11, 9) - TT(11)
    lv = 0.72 * P.eout4(seg(u, 0.1, tn)) + 0.03 * math.sin(t * 9) * seg(u, tn, tn + 0.2)
    hmax = 1.6
    barra = named(M3.rbox(0.42, max(0.02, hmax * lv), 0.42, 0.03, M.mixc(CYAN, AMBAR, lv), n=4, shadow=0, gloss=0.4), 'barra', rim=0.5)
    draw_objects(fr, [barra])
    b = 0.27
    for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        line3(fr, [(sx * b, 0, sz * b), (sx * b, hmax, sz * b)], col=WHITE, w=1.6, a=0.7, glow=0.4)
    for yy in (0.0, hmax):
        line3(fr, [(-b, yy, -b), (b, yy, -b), (b, yy, b), (-b, yy, b), (-b, yy, -b)], col=WHITE, w=1.6, a=0.7, glow=0.4)
    y = hmax * 0.95
    sq = [(-0.4, y, -0.4), (0.4, y, -0.4), (0.4, y, 0.4), (-0.4, y, 0.4), (-0.4, y, -0.4)]
    line3(fr, sq, col=ROJO, w=3.5, a=0.9 + 0.1 * math.sin(t * 12), glow=1.0)
    pl = fr.cam.p1(np.array((0.45, y, 0.4)))
    pb = fr.cam.p1(np.array((0.0, hmax * lv + 0.08, 0.3)))

    def ui(img, fx):
        kicker(img, 'ENERGÍA EN LOS PRIMEROS SEGUNDOS', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        if pl[2] > 0.2:
            pill(img, fx, pl[0] + 150, pl[1], 'NIVEL DE ALERTA', seg(u, tn - 0.4, tn - 0.1), size=28, border=ROJO, dot=False)
        if pb[2] > 0.2:
            pill(img, fx, pb[0], pb[1] - 30, f'{int(lv * 100 / 0.95)} %', seg(u, 0.2, 0.4), size=30, border=CYAN, dot=False)
        P.titulo_golpe(img, fx, [('No alcanzó.', 'serif')], 1250, seg(u, tn + 0.1, tn + 0.25), size=74)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 12. segundo gancho: el error en tu bolsillo
def s_error(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 3.2, 0, 6), KT(0.4, 2.7, 14, 5), KT(4.0, 2.5, 20, 5)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.6)
    giro = 360 * (1 - P.eout4(seg(u, -0.2, 0.6)))
    draw_objects(fr, tel(scr_silencio(t), ry=giro), xray=0.8 * (1 - seg(u, 0.4, 0.9)), keep=('in',))
    tb = wt(12, 7) - TT(12)
    pc = fr.cam.p1(np.array((0, 0.95, 0)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('El error más común…', 'sans')], 200, seg(u, 0.0, 0.15), size=72)
        P.titulo_golpe(img, fx, [('está en tu bolsillo.', 'serif')], 300, seg(u, tb - 0.2, tb - 0.05), size=72)
        doodle_circle(img, fx, pc[0], pc[1], 300, 470, t, k=eout(seg(u, tb, tb + 0.4)), col=(255, 236, 160), w=6)
    fr.ui.append(ui)
    k = max(0.0, 1 - abs(u - 0.15) / 0.3) + max(0.0, 1 - abs(u - tb + 0.05) / 0.3)
    return sacudir(finish(fr, fi), t, k, amp=20)


# ------------------------------------------------------------------ 13. si apagaste las alertas
FILAS = [('Alertas de emergencia\ninalámbricas', True), ('Alertas de prueba', False), ('Historial de alertas', False)]


def s_apagado(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 2.6, 40, 8), KT(0.3, 1.55, 8, 2, ty=1.1), KT(3.0, 1.45, 4, 2, ty=1.1)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.7)
    ta = wt(13, 2) - TT(13)
    on = 1 - P.eout4(seg(u, ta, ta + 0.25))
    draw_objects(fr, tel(scr_ajuste('Ajustes', FILAS, on)))
    pc = fr.cam.p1(np.array((0.17, 1.38, 0.05)))

    def ui(img, fx):
        kicker(img, 'AJUSTES DE TU CELULAR · EJEMPLO', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        if u > ta:
            pill(img, fx, 540, 300, 'APAGADO', P.resorte(seg(u, ta + 0.1, ta + 0.4)), size=44, border=ROJO)
            doodle_circle(img, fx, pc[0], pc[1], 120, 70, t, k=eout(seg(u, ta + 0.2, ta + 0.6)), col=ROJO, w=6)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 14. suena la calle, a ti no
def altavoz():
    poste = named(M3.cyl(0.05, 2.6, (150, 152, 158), n=20, shadow=0, gloss=0.5), 'poste', rim=0.6)
    out = [poste.tf(t=(-1.2, 0, -1.4))]
    for ry in (0, 120, 240):
        bocina = named(M3.cyl(0.08, 0.36, (215, 215, 220), n=20, shadow=0, gloss=0.5, r2=0.2), 'bocina', rim=0.6)
        out.append(bocina.tf(rz=90).tf(ry=ry, t=(-1.2, 2.4, -1.4)))
    return out


def s_calle(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 4.6, -30, 14, ty=1.4, tx=-0.6), KT(0.35, 3.6, 14, 6, ty=1.2, tx=-0.4),
                         KT(1.4, 3.6, 14, 6, ty=1.2, tx=-0.4), KT(1.7, 2.4, 22, 4, tx=0.2), KT(4.0, 2.3, 26, 4, tx=0.2)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    draw_objects(fr, altavoz() + tel(scr_silencio(t), ry=-14, off=(0.55, 0, 0.4)))
    ps = fr.cam.p1(np.array((-1.2, 2.4, -1.4)))
    pt = fr.cam.p1(np.array((0.55, 1.6, 0.4)))
    tt = wt(14, 5) - TT(14)

    def ui(img, fx):
        if ps[2] > 0.2:
            dr = ImageDraw.Draw(img)
            dfx = ImageDraw.Draw(fx)
            for i in range(4):
                r = ((t * 260 + i * 90) % 360) + 40
                a = int(255 * (1 - (r - 40) / 360))
                bb = (ps[0] - r, ps[1] - r, ps[0] + r, ps[1] + r)
                dr.arc(bb, 200, 340, fill=(a, a, a), width=4)
                dfx.arc(bb, 200, 340, fill=(a // 2, a // 2, a // 2), width=8)
            pill(img, fx, ps[0], ps[1] - 120, 'LA CALLE: SUENA', seg(u, 0.0, 0.25), size=30, border=CYAN, dot=False)
        if pt[2] > 0.2:
            pill(img, fx, pt[0], pt[1] - 40, 'TU CELULAR: NADA', seg(u, tt, tt + 0.25), size=30, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 15-16. cómo se llama el ajuste
def s_android(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 2.6, -60, 10), KT(0.25, 1.7, -16, 3, ty=1.05), KT(3.5, 1.6, -10, 3, ty=1.05)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.7, beam=0.3)
    on = P.eout4(seg(u, 0.8, 1.05))
    draw_objects(fr, tel(scr_ajuste('Alertas', FILAS, on), ry=-10))

    def ui(img, fx):
        pill(img, fx, 540, 270, 'ANDROID', P.resorte(seg(u, -0.1, 0.25)), size=46, border=(140, 220, 140))
        kicker(img, 'AJUSTES › NOTIFICACIONES · PUEDE CAMBIAR SEGÚN LA MARCA', 360, seg(u, 0.2, 0.5), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


FILAS_IOS = [('Alertas\ngubernamentales', True), ('Alertas AMBER', False), ('Alertas de seguridad', False)]


def s_iphone(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 2.6, 60, 10), KT(0.25, 1.7, 16, 3, ty=1.05), KT(3.5, 1.6, 10, 3, ty=1.05)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.7, beam=0.3)
    on = P.eout4(seg(u, 0.7, 0.95))
    draw_objects(fr, tel(scr_ajuste('Notificaciones', FILAS_IOS, on, claro=True), ry=10))

    def ui(img, fx):
        pill(img, fx, 540, 270, 'IPHONE', P.resorte(seg(u, -0.1, 0.25)), size=46, border=WHITE)
        kicker(img, 'AJUSTES › NOTIFICACIONES', 360, seg(u, 0.2, 0.5), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 17. llegan por la antena
def torre(fr, x, z, h, a=1.0):
    b, tp = 0.35, 0.06
    esq = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for sx, sz in esq:
        line3(fr, [(x + sx * b, 0, z + sz * b), (x + sx * tp, h, z + sz * tp)], col=WHITE, w=2.2, a=a, glow=0.5)
    for i in range(1, 9):
        y = h * i / 9
        w = b + (tp - b) * i / 9
        line3(fr, [(x + sx * w, y, z + sz * w) for sx, sz in esq + esq[:1]], col=WHITE, w=1.6, a=a * 0.8, glow=0.4)
    dot3(fr, (x, h + 0.08, z), r=7, col=ROJO, a=0.6 + 0.4 * math.sin(fr_t[0] * 6))


fr_t = [0.0]


def s_antena(t, fi, u, d):
    fr_t[0] = t
    fr = Frame(cam_t(u, [KT(-0.2, 5.0, 40, 30, ty=1.6, tx=-0.3), KT(0.3, 4.4, -10, 10, ty=1.5, tx=-0.25),
                         KT(4.0, 4.2, -18, 10, ty=1.5, tx=-0.25)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    torre(fr, -1.0, -1.0, 3.0 * P.eout4(seg(u, -0.2, 0.4)))
    draw_objects(fr, tel(scr_alerta(t), ry=-20, off=(0.45, 0, 0.5)))
    pa = fr.cam.p1(np.array((-1.0, 3.0, -1.0)))
    tl = wt(17, 6) - TT(17)

    def ui(img, fx):
        if pa[2] > 0.2:
            dr = ImageDraw.Draw(img)
            dfx = ImageDraw.Draw(fx)
            for i in range(5):
                r = ((t * 300 + i * 80) % 400) + 30
                a = int(200 * (1 - (r - 30) / 400))
                bb = (pa[0] - r, pa[1] - r, pa[0] + r, pa[1] + r)
                dr.arc(bb, 300, 60, fill=(a // 2, a, a), width=4)
                dfx.arc(bb, 300, 60, fill=(a // 4, a // 2, a // 2), width=8)
        P.pill_tachada(img, fx, 330, 300, 'DATOS', seg(u, 0.0, 0.2), seg(u, 0.4, 0.7), t, size=38)
        P.pill_tachada(img, fx, 750, 300, 'SALDO', seg(u, 0.25, 0.45), seg(u, 0.75, 1.05), t, size=38)
        pill(img, fx, 540, 1320, 'LLEGA POR LA ANTENA', P.resorte(seg(u, tl, tl + 0.3)), size=36, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 18. si nace cerca, no da tiempo
def s_cerca(t, fi, u, d):
    c = (-98.9, 19.1)
    fr = Frame(cam_m(u, [KM(-0.2, CDMX, 3.5, -30, 70), KM(0.3, CDMX, 1.1, 20, 45), KM(3.0, CDMX, 1.0, 30, 42)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    mapa(fr, a=0.6)
    dot3(fr, geo(*CDMX), r=9, col=WHITE)
    t0 = TT(18) + 0.1
    dot3(fr, geo(*c), r=9, col=ROJO)
    rs = max(0.0, (t - t0) * 0.12)
    ra = max(0.0, (t - t0 - 0.1) * 0.16)
    if rs > 0:
        aro(fr, c, rs, col=ROJO, a=1.0, w=4)
    if ra > 0:
        aro(fr, c, ra, col=CYAN, a=0.9, w=2)
    pc = fr.cam.p1(np.array(geo(*CDMX)))
    tn = wt(18, 7) - TT(18)

    def ui(img, fx):
        kicker(img, 'EPICENTRO CERCA · RECREACIÓN', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        if pc[2] > 0.2:
            pill(img, fx, pc[0], pc[1] - 50, 'TU CIUDAD', seg(u, 0.1, 0.3), size=28, border=WHITE, dot=False)
        P.numero_golpe(img, fx, '0 s', 1180, seg(u, tn - 0.1, tn + 0.08), size=200, col=ROJO)
        kicker(img, 'DE AVISO', 1330, seg(u, tn, tn + 0.3), col=(255, 170, 160))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(0.0, 1 - abs(u - tn - 0.08) / 0.35), amp=22)


# ------------------------------------------------------------------ 19. suena cuando ya está temblando
def s_temblando(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 2.2, 30, 4, roll=6), KT(0.3, 2.0, -12, 4, roll=-5), KT(1.4, 2.0, -12, 4, roll=-5),
                         KT(1.7, 1.7, 10, 3, roll=4), KT(4.0, 1.65, 14, 3, roll=4)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    draw_objects(fr, tel(scr_alerta(t), rz=4 * math.sin(t * 34)))

    def ui(img, fx):
        kicker(img, 'LA ALERTA LLEGA… CON EL SISMO', 150, seg(u, 0.1, 0.4), col=(255, 170, 160))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.9, amp=16)


# ------------------------------------------------------------------ 20. mándaselo
def s_mandalo(t, fi, u, d):
    fr = Frame(cam_t(u, [KT(-0.2, 3.4, -40, 10), KT(0.3, 2.8, -12, 5), KT(4.0, 2.6, -4, 5)]))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    draw_objects(fr, tel(scr_alerta(t), ry=10 * math.sin(t * 1.5)))

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien dice', 'sans'), ('que la alerta está descompuesta.', 'serif')],
                       190, seg(u, 0.0, 0.18), size=62)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(0.0, 1 - abs(u - 0.18) / 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[]),
           dict(desde=1, fn=s_descompuesta, tr='glitch', sfx=[]),
           dict(desde=2, fn=s_magnitud, tr='golpe', sfx=[(0.0, 'scribble', 0.5)]),
           dict(desde=3, fn=s_calcula, tr='iris', sfx=[(0.0, 'shimmer', 0.6)]),
           dict(desde=4, fn=s_dos, tr='deslizar', sfx=[(-0.1, 'whoosh', 0.5), (0.15, 'whoosh', 0.5)]),
           dict(desde=5, fn=s_chiapas, tr='whip', sfx=[(0.3, 'sub', 0.6), (0.0, 'tick', 0.6)]),
           dict(desde=6, fn=s_nosono, tr='golpe', c=(0.5, 0.5), sfx=[(0.05, 'scribble', 0.8)]),
           dict(desde=7, fn=s_170, tr='iris', sfx=[]),
           dict(desde=8, fn=s_sensores, tr='deslizar_abajo', sfx=[]),
           dict(desde=9, fn=s_vacio, tr='push', c=(0.6, 0.6), sfx=[(0.0, 'bass', 0.9)]),
           dict(desde=10, fn=s_viaje, tr='whip_izq', sfx=[(0.0, 'riser', 0.5)]),
           dict(desde=11, fn=s_energia, tr='wipe', sfx=[(0.1, 'riser', 0.5)]),
           dict(desde=12, fn=s_error, tr='giro', sfx=[(0.0, 'slap', 0.8)]),
           dict(desde=13, fn=s_apagado, tr='deslizar', sfx=[]),
           dict(desde=14, fn=s_calle, tr='whip', sfx=[(0.0, 'shimmer', 0.5)]),
           dict(desde=15, fn=s_android, tr='push', sfx=[]),
           dict(desde=16, fn=s_iphone, tr='deslizar_abajo', sfx=[]),
           dict(desde=17, fn=s_antena, tr='iris', sfx=[(0.4, 'scribble', 0.6), (0.75, 'scribble', 0.6)]),
           dict(desde=18, fn=s_cerca, tr='golpe', sfx=[(0.1, 'sub', 0.7)]),
           dict(desde=19, fn=s_temblando, tr='glitch', sfx=[(0.0, 'riser', 0.4)]),
           dict(desde=20, fn=s_mandalo, tr='ritmo', sfx=[(0.18, 'slap', 0.8)]),
           dict(desde=21, loop=True, tr='zoom')]


def _sfx_dinamicos():
    tc = wt(0, 4) - TT(0)
    ESCENAS[0]['sfx'] = [(0.0, 'thud', 1.0), (0.02, 'burst', 0.7), (tc - 0.2, 'whoosh', 0.9), (tc + 0.45, 'slap', 0.8)]
    ESCENAS[1]['sfx'] = [(0.0, 'tick2', 0.5), (TE(1) - TT(1) - 0.1, 'chime_c', 0.6)]
    tm = wt(2, 8) - TT(2)
    ESCENAS[2]['sfx'] += [(tm, 'scribble', 0.7)]
    tcx = wt(3, 6) - TT(3)
    ESCENAS[3]['sfx'] += [(tcx + 0.12 * i, 'tick2', 0.35) for i in range(7)]
    tk = wt(7, 10) - TT(7)
    ta = wt(7, 14) - TT(7)
    ESCENAS[7]['sfx'] = [(tk - 0.6, 'whoosh_suave', 0.5), (tk, 'tick', 0.6), (ta, 'bass', 0.8), (ta + 0.05, 'chime_b', 0.6)]
    tn = wt(8, 3) - TT(8)
    dur = max(1.2, wt(8, 10) - TT(8) - tn)
    ESCENAS[8]['sfx'] = [(tn + dur * i / 12, 'tick2', 0.25) for i in range(12)] + [(tn, 'chime_a', 0.6)]
    tn = wt(11, 9) - TT(11)
    ESCENAS[11]['sfx'] += [(tn + 0.15, 'thud', 0.8)]
    tb = wt(12, 7) - TT(12)
    ESCENAS[12]['sfx'] += [(tb - 0.1, 'bass', 0.9), (tb + 0.05, 'scribble', 0.6)]
    ta = wt(13, 2) - TT(13)
    ESCENAS[13]['sfx'] = [(ta, 'click', 0.9), (ta + 0.1, 'thud', 0.6)]
    ESCENAS[15]['sfx'] = [(0.8, 'click', 0.9), (0.0, 'tick', 0.5)]
    ESCENAS[16]['sfx'] = [(0.7, 'click', 0.9), (0.0, 'tick', 0.5)]
    tl = wt(17, 6) - TT(17)
    ESCENAS[17]['sfx'] += [(tl, 'chime_b', 0.6)]
    tn = wt(18, 7) - TT(18)
    ESCENAS[18]['sfx'] += [(tn, 'bass', 0.9), (tn + 0.02, 'burst', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
