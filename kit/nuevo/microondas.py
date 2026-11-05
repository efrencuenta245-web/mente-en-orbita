"""Reel extra: «Tu microondas apaga tu Wi-Fi.» Jue 5-nov-2026, 14:30 (pedido por Efrén). Voz Isaac.
Estilo rápido (ESTILO.md §11-12). Inicio tipo 8 (error en pantalla: la videollamada se cae primero).
Datos: horno a 2 450 MHz, onda de ~12 cm, hoyitos de la rejilla de ~1 mm (la onda es ~120 veces más grande),
fuga limitada a 5 mW/cm² a ~5 cm (HyperPhysics, Georgia State Univ.); Wi-Fi de 2.4 GHz en 2 400–2 483.5 MHz con
potencia máxima de 1 W (FCC 47 CFR 15.247, resumen de rfwel); la red de 5 GHz no se ve afectada (ScienceABC).
Horno de ~1 000 W: potencia típica de etiqueta. Espectro, ondas y cocina: RECREACIÓN / ESCALA EXAGERADA."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, line3, dot3,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'microondas'
TXT = ['Calientas tu café en el micro…',
       'y tu Wi-Fi se cae.',
       'No es la compañía de internet.',
       'Es tu microondas.',
       'Tu micro trabaja a 2 450 MHz…',
       'justo en medio de la banda de tu Wi-Fi.',
       'Mira dos casos:',
       'en la red normal, la videollamada se congela.',
       'En la red de 5 GHz… ni se entera.',
       '¿Y por qué le gana?',
       'Porque tu micro usa unos 1 000 W…',
       'y tu módem manda menos de 1 W.',
       'Es como gritar junto a alguien que te habla en secreto.',
       'Claro, la puerta lo encierra:',
       'tiene una rejilla con hoyitos de 1 mm.',
       'Y la onda mide 12 cm,',
       '120 veces más: rebota y se queda adentro.',
       'La luz sí pasa… por eso ves tu comida.',
       'Pero basta que se escape una pizca, la que permite la norma,',
       'para tapar la señal de tu Wi-Fi.',
       'Y el error que casi todos cometemos:',
       'poner el módem en la cocina, junto al micro.',
       'Aléjalo… o conéctate a la red de 5 GHz.',
       'Mándaselo a quien le echa la culpa a la compañía de internet.',
       'Porque ahora ya sabes qué pasa cada vez que…']
VOZ = list(TXT)
VOZ[4] = 'Tu micro trabaja a dos mil cuatrocientos cincuenta megahercios…'
VOZ[8] = 'En la red de cinco gigahercios… ni se entera.'
VOZ[10] = 'Porque tu micro usa unos mil watts…'
VOZ[11] = 'y tu módem manda menos de uno.'
VOZ[14] = 'tiene una rejilla con hoyitos de un milímetro.'
VOZ[15] = 'Y la onda mide doce centímetros,'
VOZ[16] = 'ciento veinte veces más: rebota y se queda adentro.'
VOZ[22] = 'Aléjalo… o conéctate a la red de cinco gigahercios.'

NAR = (255, 150, 60)      # la onda del micro
VERDE = (90, 220, 140)
AMBAR = (255, 196, 90)
ROJO = (255, 64, 56)
CAFE = (92, 54, 30)


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


def wt(i, k):
    n = len(VOZ[i].split())
    return TT(i) + (TE(i) - TT(i)) * k / n


def F(k, s):
    return M.font(k, s)


def cam(u, claves, cy=0.55):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p['roll'])


def K(u, dist, yaw, pitch=8, tx=0.0, ty=0.45, tz=0.0, roll=0.0):
    return (u, dict(tx=tx, ty=ty, tz=tz, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def golpe_k(u, u0, dur=0.35):
    """1 justo en el impacto y baja a 0 en `dur` (para la sacudida)."""
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


# ================================================================== objetos
_CACHE = {}
MW_W, MW_H, MW_D = 1.3, 0.78, 0.9
DOOR_W, DOOR_H = 0.92, 0.66
DOOR_X0 = -MW_W / 2 + 0.03            # bisagra (orilla izquierda de la puerta)
FRONT_Z = MW_D / 2


def _malla_overlay(w, h, paso=9, r=2.6):
    key = ('malla', w, h)
    if key not in _CACHE:
        m = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(m)
        for yy in range(0, h + paso, paso):
            off = (paso / 2) if (yy // paso) % 2 else 0
            for xx in range(0, w + paso, paso):
                d.ellipse((xx + off - r, yy - r, xx + off + r, yy + r), fill=255)
        _CACHE[key] = m
    return _CACHE[key]


def puerta_img(luz, ang, malla=1.0):
    """Cara de la puerta: marco oscuro, ventana con la rejilla de puntos y, si está prendido, la luz y la taza."""
    key = ('puerta', round(luz, 1), int(ang * 3) % 24, round(malla, 1))
    if key in _CACHE:
        return _CACHE[key]
    w, h = 600, 430
    im = Image.new('RGB', (w, h), (44, 45, 50))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 46, 44, w - 46, h - 44
    l = clamp(luz)
    d.rectangle((x0, y0, x1, y1), fill=(int(14 + 120 * l), int(14 + 96 * l), int(16 + 44 * l)))
    # plato que gira (elipse) y la taza
    cx, cy = (x0 + x1) / 2, y1 - 70
    d.ellipse((cx - 190, cy - 34, cx + 190, cy + 34), fill=(int(40 + 140 * l), int(40 + 120 * l), int(44 + 70 * l)))
    sx = 60 * math.sin(ang)
    d.rectangle((cx - 52 + sx, cy - 150, cx + 52 + sx, cy - 10), fill=(int(70 + 170 * l), int(70 + 165 * l), int(70 + 150 * l)))
    d.ellipse((cx - 52 + sx, cy - 30, cx + 52 + sx, cy + 6), fill=(int(70 + 170 * l), int(70 + 165 * l), int(70 + 150 * l)))
    d.arc((cx + 36 + sx, cy - 130, cx + 96 + sx, cy - 50), -90, 90, fill=(int(70 + 160 * l), int(70 + 150 * l), int(70 + 140 * l)), width=12)
    if malla > 0:
        ov = _malla_overlay(x1 - x0, y1 - y0)
        im.paste((8, 8, 10), (x0, y0), ov.point(lambda v: int(v * 0.86 * malla)))
    d.rectangle((x0, y0, x1, y1), outline=(20, 20, 22), width=6)
    d.rounded_rectangle((w - 34, 120, w - 16, h - 120), radius=8, fill=(70, 72, 78))  # jaladera
    _CACHE[key] = im.convert('RGBA')
    return _CACHE[key]


def panel_img(txt, on):
    key = ('panel', txt, round(on, 1))
    if key in _CACHE:
        return _CACHE[key]
    w, h = 200, 430
    im = Image.new('RGB', (w, h), (30, 31, 35))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((18, 26, w - 18, 96), radius=10, fill=(6, 10, 10))
    c = M.mixc((40, 70, 60), (110, 255, 190), on)
    d.text((w / 2, 61), txt, font=F('mono', 40), fill=c, anchor='mm')
    for r in range(4):
        for q in range(3):
            xx, yy = 30 + q * 50, 130 + r * 52
            d.rounded_rectangle((xx, yy, xx + 40, yy + 38), radius=8, fill=(58, 60, 66))
    d.rounded_rectangle((26, 350, w - 26, 400), radius=12, fill=(70, 140, 90) if on > 0.5 else (60, 62, 68))
    d.text((w / 2, 375), 'INICIO', font=F('sans', 22), fill=(230, 235, 232), anchor='mm')
    _CACHE[key] = im.convert('RGBA')
    return _CACHE[key]


def microondas(t, luz=0.0, puerta=0.0, interior=False, reloj='1:30', malla=1.0, mag=0.0, x=0.0, z=0.0, s=1.0, ry=0.0):
    """Horno de microondas semirrealista. luz: interior prendido (0–1). puerta: 0 cerrada → 1 abierta.
    interior=True agrega el magnetrón, la guía de onda, el plato y la taza (para rayos X)."""
    col = (186, 189, 196)
    body = named(M3.rbox(MW_W, MW_H, MW_D, 0.05, col, n=4, shadow=0, gloss=0.6), 'micro', rim=0.7, gloss=0.6)
    out = [body]
    pan = M3.box(0.3, DOOR_H, 0.02, (30, 31, 35), shadow=0, base=True, gloss=0.5).tf(t=(MW_W / 2 - 0.19, 0.06, FRONT_Z + 0.01))
    M3.decal(pan, pan.FACE['front'], panel_img(reloj, luz))
    out.append(named(pan, 'panel', rim=0.4))
    door = M3.box(DOOR_W, DOOR_H, 0.04, (44, 45, 50), shadow=0, base=True, gloss=0.6).tf(t=(DOOR_W / 2, 0.06, 0.02))
    M3.decal(door, door.FACE['front'], puerta_img(luz, t * 2.2, malla))
    door = door.tf(ry=-105 * ease(clamp(puerta))).tf(t=(DOOR_X0, 0, FRONT_Z))
    out.append(named(door, 'puerta', rim=0.6, gloss=0.6))
    if puerta > 0.02:
        hueco = M3.box(DOOR_W - 0.06, DOOR_H - 0.06, 0.01, M.mixc((40, 40, 44), (250, 232, 190), luz), shadow=0, base=True)
        hueco = named(hueco.tf(t=(DOOR_X0 + DOOR_W / 2, 0.09, FRONT_Z + 0.004)), 'hueco')
        hueco.flat = True
        if luz > 0.05:
            hueco.glow = M.scale_c((255, 220, 150), 0.35 * luz)
        out.insert(1, hueco)
    if interior:
        cav = M3.box(DOOR_W - 0.08, DOOR_H - 0.06, 0.02, M.mixc((60, 60, 64), (230, 220, 190), luz), shadow=0, base=True)
        cav = named(cav.tf(t=(DOOR_X0 + DOOR_W / 2, 0.09, -MW_D / 2 + 0.06)), 'in')
        cav.flat = True
        if luz > 0.05:
            cav.glow = M.scale_c((255, 220, 150), 0.25 * luz)
        out.append(cav)
        cx = DOOR_X0 + DOOR_W / 2
        plato = named(M3.cyl(0.3, 0.02, (200, 214, 222), n=32, shadow=0, gloss=0.8, y0=0.07), 'in', rim=0.8)
        taza = named(M3.cyl(0.1, 0.2, (238, 238, 232), n=24, shadow=0, gloss=0.5, y0=0.09), 'in', rim=0.5)
        cafe = named(M3.cyl(0.092, 0.004, CAFE, n=24, shadow=0, gloss=0.6, y0=0.285), 'in', rim=0.2)
        a = t * 70
        out += P.tfk([plato], t=(cx, 0, 0)) + P.tfk([taza, cafe], ry=a, t=(cx + 0.06 * math.sin(math.radians(a)), 0, 0.06 * math.cos(math.radians(a))))
    if interior:
        magn = named(M3.cyl(0.085, 0.16, M.mixc((150, 120, 90), (255, 150, 60), mag), n=24, shadow=0, gloss=0.6, y0=0.48), 'in', rim=0.6)
        magn = magn.tf(t=(MW_W / 2 - 0.19, 0, -0.1))
        if mag > 0.05:
            magn.glow = M.scale_c(NAR, 0.7 * mag)
        guia = named(M3.box(0.42, 0.08, 0.16, (150, 152, 160), shadow=0, base=True, gloss=0.5).tf(t=(MW_W / 2 - 0.36, 0.62, -0.1)), 'in', rim=0.5)
        out += [magn, guia]
    if s != 1.0 or x or z or ry:
        out = P.tfk(out, s=s, ry=ry, t=(x, 0, z))
    return out


def modem(t, x=0.0, z=0.0, s=1.0, ry=0.0, rojo=0.0, leds=1.0):
    col = M.mixc((36, 37, 42), (120, 30, 26), rojo)
    out = [named(M3.rbox(0.62, 0.1, 0.4, 0.05, col, n=4, shadow=0, gloss=0.55), 'modem', rim=0.7, gloss=0.55)]
    for i, xx in enumerate((-0.22, 0.0, 0.22)):
        a = named(M3.cyl(0.018, 0.5, (30, 30, 34), n=10, shadow=0, gloss=0.5, y0=0.0), 'modem', rim=0.6)
        out += P.tfk([a], rz=(-14, 0, 14)[i], t=(xx, 0.1, -0.15))
    for i in range(4):
        on = leds * (0.55 + 0.45 * (math.sin(t * (9 + 3 * i) + i * 1.7) > -0.2))
        led = named(M3.box(0.035, 0.018, 0.01, (40, 60, 50), shadow=0, base=True).tf(t=(-0.18 + 0.12 * i, 0.045, 0.2)), 'led')
        led.flat = True
        c = M.mixc(VERDE, ROJO, rojo)
        led.C = [M.scale_c(c, 0.4 + 0.6 * on)] * len(led.C)
        led.glow = M.scale_c(c, 0.9 * on)
        out.append(led)
    return P.tfk(out, s=s, ry=ry, t=(x, 0, z))


def tel(scr, x=0.0, z=0.0, s=1.0, ry=0.0):
    ph = P.celular(scr, ry=ry)
    return P.tfk(ph, s=s, t=(x, 0, z))


# ------------------------------------------------------------------ pantallas del celular
def wifi_icon(d, cx, cy, s, col, nivel=3, tachado=False):
    for i in range(3):
        r = s * (0.35 + 0.32 * i)
        c = col if i < nivel else (70, 72, 80)
        d.arc((cx - r, cy - r, cx + r, cy + r), 225, 315, fill=c, width=max(3, int(s * 0.11)))
    d.ellipse((cx - s * 0.09, cy - s * 0.09, cx + s * 0.09, cy + s * 0.09), fill=col if nivel > 0 else (70, 72, 80))
    if tachado:
        d.line([(cx - s * 0.8, cy - s * 0.95), (cx + s * 0.8, cy + s * 0.2)], fill=ROJO, width=max(4, int(s * 0.13)))


def scr_llamada(t, estado='ok', red='MiCasa', mal=0.0):
    """Videollamada (sin caras: círculo con inicial). estado: ok, congelada, error."""
    def dib(d, im):
        d.rectangle((0, 70, 420, 900), fill=(18, 22, 30))
        d.text((210, 130), 'Videollamada', font=F('sanss', 26), fill=(160, 166, 176), anchor='mm')
        wifi_icon(d, 360, 52, 30, (230, 230, 232), nivel=3 if estado == 'ok' else (1 if estado == 'congelada' else 0),
                  tachado=estado == 'error')
        d.ellipse((110, 230, 310, 430), fill=(60, 110, 160))
        d.text((210, 330), 'M', font=F('sans', 110), fill=(235, 240, 248), anchor='mm')
        d.text((210, 490), 'Mamá', font=F('sans', 44), fill=(240, 240, 244), anchor='mm')
        tt = 134 + (int(t) if estado == 'ok' else 0)
        d.text((210, 545), f'{tt // 60:02d}:{tt % 60:02d}', font=F('mono', 28), fill=(150, 156, 166), anchor='mm')
        d.text((210, 600), red, font=F('mono', 22), fill=(110, 200, 230), anchor='mm')
        d.ellipse((170, 760, 250, 840), fill=(225, 60, 56))
        d.line([(190, 800), (230, 800)], fill=(255, 255, 255), width=8)
        if estado != 'ok':
            arr = np.asarray(im).copy()
            rng = np.random.RandomState(int(t * 24))
            amt = 0.5 + 0.5 * mal
            for _ in range(int(16 * amt)):
                y0 = rng.randint(80, 860)
                h = rng.randint(6, 46)
                arr[y0:y0 + h] = np.roll(arr[y0:y0 + h], rng.randint(-110, 110), 1)
            arr = (arr.astype(np.float32) * 0.55).astype(np.uint8)
            im.paste(Image.fromarray(arr))
            if estado == 'congelada':
                a0 = (t * 360) % 360
                d.arc((160, 280, 260, 380), a0, a0 + 270, fill=(235, 235, 240), width=10)
                d.text((210, 690), 'Reconectando…', font=F('sans', 34), fill=(240, 240, 244), anchor='mm')
            else:
                d.rectangle((0, 640, 420, 740), fill=(200, 36, 32))
                d.text((210, 690), 'SIN CONEXIÓN', font=F('sans', 40), fill=(255, 255, 255), anchor='mm')
    return P.pantalla(dib)


def scr_redes(sel):
    def dib(d, im):
        d.rectangle((0, 70, 420, 900), fill=(14, 16, 22))
        d.text((30, 120), 'Wi-Fi', font=F('sans', 44), fill=(240, 240, 244))
        filas = [('MiCasa', '2.4 GHz', 1 - sel), ('MiCasa-5G', '5 GHz', sel), ('Vecino_2.4', '2.4 GHz', 0.0)]
        for i, (n, b, k) in enumerate(filas):
            y = 230 + i * 130
            if k > 0.05:
                d.rounded_rectangle((14, y - 20, 406, y + 92), radius=18, fill=(24, 30, 40), outline=M.scale_c(CYAN, k), width=3)
            wifi_icon(d, 64, y + 50, 34, (230, 232, 236), nivel=3)
            d.text((110, y + 6), n, font=F('sans', 32), fill=(240, 240, 244))
            d.text((110, y + 50), b, font=F('mono', 22), fill=(130, 200, 230) if b == '5 GHz' else (140, 142, 150))
            if k > 0.5:
                d.line([(350, y + 38), (366, y + 56), (392, y + 22)], fill=VERDE, width=7)
    return P.pantalla(dib)


# ------------------------------------------------------------------ ondas
def aros(fr, c, t, t0, col, vel=0.9, n=5, rmax=2.2, sep=0.28, w=2.6, a=1.0, plano='xy'):
    """Frentes de onda (círculos de alambre que crecen) desde el punto c."""
    for i in range(n):
        r = ((t - t0) * vel - i * sep) % (n * sep) if t >= t0 else -1
        if 0.02 < r < rmax:
            pts = []
            for j in range(49):
                q = 2 * math.pi * j / 48
                if plano == 'xy':
                    pts.append((c[0] + r * math.cos(q), c[1] + r * math.sin(q), c[2]))
                else:
                    pts.append((c[0] + r * math.cos(q), c[1], c[2] + r * math.sin(q)))
            line3(fr, pts, col=col, w=w, a=a * (1 - r / rmax), glow=0.8)


def seno(fr, x0, x1, y, z, lam, amp, t, col, fase=0.0, frac=1.0, w=3.0, a=1.0, glow=0.9):
    xs = np.linspace(x0, x1, 160)
    pts = [(x, y + amp * math.sin(2 * math.pi * (x - x0) / lam - t * 6 + fase), z) for x in xs]
    line3(fr, pts, col=col, w=w, a=a, glow=glow, frac=frac)


def ruido(img, box, k, t, col=NAR):
    """Estática naranja (lo que «tapa» la señal)."""
    if k <= 0.01:
        return
    x0, y0, x1, y1 = box
    rng = np.random.RandomState(int(t * 24))
    d = ImageDraw.Draw(img)
    for _ in range(int(220 * k)):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(1.5, 4.5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=M.scale_c(col, rng.uniform(0.4, 1.0) * k))


def sombra(fr, x, z, rx, ry=None, a=0.75):
    sx, sy = fr.cam.proj([(x, 0.01, z)])[0][0]
    D.shadow_blob(fr, sx, sy, rx, ry or rx * 0.25, a)


# ================================================================== escenas
# 0. gancho, inicio tipo 8 (error en pantalla): el micro prende y la videollamada se cae
def s_gancho(t, fi, u, d):
    u0 = -TT(0)                            # cuadro 0 del video (el loop nunca llega aquí)
    tm = wt(0, 5) - TT(0)                  # «micro…»
    tc = TT(1) - TT(0)                     # «y tu Wi-Fi se cae»
    tg = wt(1, 3) - TT(0)                  # «se cae»
    fr = Frame(cam(u, [K(-4.2, 4.4, -34, 12, tx=0.0, ty=0.45, tz=-0.1), K(-0.9, 3.3, -14, 8, tx=0.0, ty=0.45, tz=-0.1),
                       K(u0, 2.6, -4, 6, tx=0.05, ty=0.45, tz=-0.05), K(tm - 0.25, 2.5, -8, 6, tx=0.05, ty=0.45, tz=-0.05),
                       K(tm + 0.05, 2.0, -22, 8, tx=-0.3, ty=0.42, tz=-0.3), K(tg - 0.1, 1.95, -26, 8, tx=-0.3, ty=0.42, tz=-0.3),
                       K(tg + 0.05, 1.45, 8, 3, tx=0.45, ty=0.45, tz=0.4), K(tg + 3.0, 1.35, 12, 3, tx=0.45, ty=0.45, tz=0.4)]))
    space(fr, t, floor='lines', floor_a=0.85, bokeh=1.0, beam=0.5, beam_x=0.4)
    on = u >= u0
    sombra(fr, -0.35, -0.6, 330, 70)
    if not on:
        estado = 'ok'
    elif u < tc:
        estado = 'congelada' if (u < u0 + 0.6 or u > tm) else 'ok'
    else:
        estado = 'error'
    ph = tel(scr_llamada(t, estado, mal=seg(u, tc, tg)), x=0.45, z=0.4, s=0.42, ry=-16)
    mw = microondas(t, luz=(0.85 + 0.15 * math.sin(t * 40)) if on else 0.0,
                    reloj='1:30' if not on else f'1:{max(0, 29 - int(u + 0.3)):02d}', x=-0.35, z=-0.6)
    draw_objects(fr, mw + ph)
    if on:
        aros(fr, (-0.5, 0.42, -0.1), t, 0.0, NAR, vel=1.1, n=5, rmax=1.9, sep=0.3, a=0.8)

    def ui(img, fx):
        if on and u < tc + 0.05 and (int(t * 8) % 2 == 0 or u < u0 + 0.4):
            kicker(img, 'ERROR · CONEXIÓN INESTABLE', 150, 1.0, col=ROJO, size=28)
        if u >= tg:
            kicker(img, '2.4 GHz · INTERFERENCIA', 140, seg(u, tg + 0.2, tg + 0.5), col=(255, 170, 120))
            P.titulo_golpe(img, fx, [('Tu microondas', 'sans'), ('apaga tu Wi-Fi.', 'serif')], 200, seg(u, tg, tg + 0.15), size=84)
    fr.ui.append(ui)
    out = finish(fr, fi)
    k = golpe_k(u, u0, 0.35) * 0.8 + golpe_k(u, tg + 0.15, 0.4)
    return sacudir(out, t, k, amp=24)


# 1. no es la compañía de internet (el módem, inocente)
def s_compania(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.0, 50, 22, ty=0.3), K(0.3, 2.4, -12, 14, ty=0.3), K(3.0, 2.25, -18, 13, ty=0.3)]))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9, beam=0.4)
    e = P.entrada(u, -0.1, 0.3, 'cae')
    sombra(fr, 0, 0, 340, 80)
    draw_objects(fr, P.tfk(modem(t, s=1.55), t=(0, max(0.0, -e['dy']) * 0.4, 0)))
    tt = wt(2, 4) - TT(2)

    def ui(img, fx):
        kicker(img, 'TU MÓDEM', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        P.pill_tachada(img, fx, 540, 330, 'CULPA DE LA COMPAÑÍA', seg(u, 0.05, 0.3), seg(u, tt, tt + 0.3), t, size=40)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=16)


# 2. es tu microondas
def s_es_micro(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.8, 70, 14), K(0.25, 3.3, 18, 7), K(2.0, 3.1, 24, 7)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.55)
    glass_type(fr.base, fr.fx, 'MICRO', 540 * S, 700 * S, 250 * S, k=eout(seg(u, -0.2, 0.3)), fill_a=0.06)
    sombra(fr, 0, 0, 420, 90)
    draw_objects(fr, microondas(t, luz=0.9, reloj='1:27'))
    c = fr.cam.p1(np.array([-0.16, 0.4, FRONT_Z]))

    def ui(img, fx):
        doodle_circle(img, fx, c[0], c[1], 380, 260, t, k=eout(seg(u, 0.2, 0.6)), col=(255, 236, 160), w=6)
        pill(img, fx, 540, 1330, 'EL CULPABLE', eout(seg(u, 0.35, 0.6)), size=40, border=ROJO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. 2 450 MHz: rayos X, el magnetrón y la onda
def s_2450(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 2.6, 30, 18, tx=0.2, ty=0.45), K(0.35, 2.4, 40, 16, tx=0.25, ty=0.45),
                       K(3.5, 2.2, 46, 15, tx=0.25, ty=0.45)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.7)
    mag = eout(seg(u, 0.3, 1.0))
    draw_objects(fr, microondas(t, luz=0.6, interior=True, mag=mag), xray=1.0, keep=('in',))
    seno(fr, MW_W / 2 - 0.36, -0.55, 0.62, -0.1, 0.24, 0.05 * mag, t, NAR, frac=mag, w=3.4)
    tn = wt(4, 5) - TT(4)
    v = int(2450 * P.eout4(seg(u, tn - 0.6, tn + 0.4)))
    mc = fr.cam.p1(np.array([MW_W / 2 - 0.19, 0.56, -0.1]))

    def ui(img, fx):
        kicker(img, 'RAYOS X · EL MAGNETRÓN', 130, seg(u, 0.0, 0.3), col=(150, 210, 230))
        pill(img, fx, mc[0], mc[1] - 120, 'MAGNETRÓN', eout(seg(u, 0.4, 0.7)), size=28, border=NAR)
        if u > tn - 0.6:
            txt = f'{v:,}'.replace(',', ' ') + ' MHz'
            d_ = ImageDraw.Draw(img)
            d_.text((540, 300), txt, font=F('mono', 104), fill=M.scale_c(NAR, 1.0), anchor='mm')
            ImageDraw.Draw(fx).text((540, 300), txt, font=F('mono', 104), fill=M.scale_c(NAR, 0.5), anchor='mm')
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. justo en medio de la banda del Wi-Fi (espectro)
def espectro(img, fx, t, u, k_banda, k_pico, k_can, y0=640, y1=1240):
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    x0, x1 = 90, 990
    f0, f1 = 2380, 2500
    X = lambda f: x0 + (x1 - x0) * (f - f0) / (f1 - f0)
    d.line([(x0, y1), (x1, y1)], fill=(150, 152, 160), width=3)
    for f in (2400, 2450, 2483.5):
        d.line([(X(f), y1), (X(f), y1 + 16)], fill=(150, 152, 160), width=3)
        lab = f'{f:g}'.replace('.', ',')
        d.text((X(f), y1 + 44), lab, font=F('mono', 28), fill=(170, 172, 180), anchor='mm')
    d.text((540, y1 + 92), 'MHz', font=F('mono', 24), fill=(130, 132, 140), anchor='mm')
    if k_banda > 0.01:
        xa, xb = X(2400), X(2400 + 83.5 * P.eout4(k_banda))
        d.rectangle((xa, y0, xb, y1), fill=(12, 34, 44))
        d.rectangle((xa, y0, xb, y1), outline=M.scale_c(CYAN, 0.9), width=3)
        df.rectangle((xa, y0, xb, y1), outline=M.scale_c(CYAN, 0.5), width=6)
        d.text((X(2441.75), y0 - 40), 'BANDA DE TU WI-FI', font=F('mono', 30), fill=M.scale_c(CYAN, k_banda), anchor='mm')
    for i in range(3):  # canales 1, 6 y 11
        kc = seg(k_can, i * 0.25, i * 0.25 + 0.4)
        if kc <= 0.01:
            continue
        fc = (2412, 2437, 2462)[i]
        pts = [(X(fc + df_), y1 - (y1 - y0 - 120) * 0.62 * kc * math.cos(df_ / 11 * math.pi / 2) ** 2) for df_ in np.linspace(-11, 11, 40)]
        d.line(pts, fill=M.scale_c(CYAN, 0.9), width=4)
        df.line(pts, fill=M.scale_c(CYAN, 0.4), width=8)
    if k_pico > 0.01:
        hp = (y1 - y0 - 150) * P.resorte(k_pico)
        xs = X(2450)
        pts = [(xs + dx, y1 - hp * math.exp(-(dx / 26) ** 2) * (0.9 + 0.1 * math.sin(t * 30 + dx))) for dx in np.linspace(-90, 90, 60)]
        d.line(pts, fill=NAR, width=6)
        df.line(pts, fill=M.scale_c(NAR, 0.7), width=12)
        d.text((xs, y1 - hp - 40), 'TU MICRO', font=F('sans', 38), fill=NAR, anchor='mm')


def s_banda(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 5.0, 0, 30, ty=0.0), K(3.0, 4.4, 6, 26, ty=0.0)]))
    space(fr, t, floor='lines', floor_a=0.5, bokeh=0.6)
    tb = wt(5, 6) - TT(5)

    def ui(img, fx):
        kicker(img, 'ESPECTRO · RECREACIÓN', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        espectro(img, fx, t, u, seg(u, -0.45, -0.1), seg(u, 0.1, 0.45), seg(u, tb - 0.3, tb + 0.7))
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. mira dos casos (pantalla dividida)
def tarjeta(img, fx, x, y, k, l1, l2, l3, col):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    w, h = 440, 330
    x0 = x - w / 2
    d.rounded_rectangle((x0, y, x0 + w, y + h), radius=26, fill=(14, 15, 19), outline=col, width=4)
    d.text((x, y + 60), l1, font=F('mono', 26), fill=(150, 210, 230), anchor='mm')
    d.text((x, y + 150), l2, font=F('sans', 60), fill=(245, 245, 247), anchor='mm')
    d.text((x, y + 250), l3, font=F('sans', 38), fill=col, anchor='mm')
    ImageDraw.Draw(fx).rounded_rectangle((x0, y, x0 + w, y + h), radius=26, outline=M.scale_c(col, 0.6), width=6)


def s_dos(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.0, -30, 12), K(0.3, 3.4, 20, 8), K(3.0, 3.2, 26, 8)]))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.3)
    k1 = P.eout4(seg(u, -0.25, 0.0))
    k2 = P.eout4(seg(u, 0.0, 0.25))

    def ui(img, fx):
        kicker(img, 'DOS CASOS', 420, seg(u, -0.1, 0.2), col=(150, 210, 230))
        tarjeta(img, fx, 290 - 700 * (1 - k1), 560, k1, 'CASO 1', '2.4 GHz', 'RED NORMAL', AMBAR)
        tarjeta(img, fx, 790 + 700 * (1 - k2), 960, k2, 'CASO 2', '5 GHz', 'RED «5G»', CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. en la red normal se congela (ondas que chocan)
def s_congela(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.6, -40, 14, tx=0.1, ty=0.4), K(0.3, 3.9, -6, 9, tx=0.1, ty=0.4),
                       K(2.0, 3.9, -6, 9, tx=0.1, ty=0.4), K(2.3, 1.25, 4, 3, tx=0.95, ty=0.48, tz=0.4),
                       K(4.0, 1.18, 8, 3, tx=0.95, ty=0.48, tz=0.4)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    for xx, zz, rx in ((-0.7, -0.3, 330), (0.95, -0.6, 160), (0.95, 0.4, 110)):
        sombra(fr, xx, zz, rx, rx * 0.22)
    tq = wt(7, 6) - TT(7)
    draw_objects(fr, microondas(t, luz=0.9, reloj='1:12', x=-0.7, z=-0.3) + modem(t, x=0.95, z=-0.6, s=0.8)
                 + tel(scr_llamada(t, 'congelada' if u > tq else 'ok', mal=seg(u, tq, tq + 0.6)), x=0.95, z=0.4, s=0.4, ry=-20))
    aros(fr, (-0.7, 0.42, 0.1), t, TT(7) - 0.3, NAR, vel=1.0, n=6, rmax=2.4, sep=0.3, a=0.9)
    aros(fr, (0.95, 0.35, -0.55), t, TT(7) - 0.3, CYAN, vel=0.7, n=4, rmax=1.4, sep=0.32, a=0.6, w=2.0)

    def ui(img, fx):
        pill(img, fx, 540, 230, 'RED 2.4 GHz', eout(seg(u, 0.0, 0.25)), size=34, border=AMBAR)
        if u > tq:
            kicker(img, 'SE CONGELA', 330, seg(u, tq, tq + 0.2), col=ROJO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tq, 0.3) * 0.7, amp=14)


# 7. en la red de 5 GHz ni se entera
def s_5ghz(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.2, 40, 12, tx=0.1, ty=0.4), K(0.3, 3.9, 12, 9, tx=0.1, ty=0.4), K(3.5, 3.7, 18, 9, tx=0.1, ty=0.4)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    for xx, zz, rx in ((-0.7, -0.3, 330), (0.95, -0.6, 160), (0.95, 0.4, 110)):
        sombra(fr, xx, zz, rx, rx * 0.22)
    draw_objects(fr, microondas(t, luz=0.9, reloj='1:09', x=-0.7, z=-0.3) + modem(t, x=0.95, z=-0.6, s=0.8)
                 + tel(scr_llamada(t, 'ok', red='MiCasa-5G'), x=0.95, z=0.4, s=0.4, ry=-20))
    aros(fr, (-0.7, 0.42, 0.1), t, TT(8) - 0.5, NAR, vel=1.0, n=6, rmax=2.4, sep=0.3, a=0.5)
    aros(fr, (0.95, 0.35, -0.55), t, TT(8) - 0.5, CYAN, vel=1.0, n=8, rmax=1.4, sep=0.14, a=0.9, w=2.2)
    tok = wt(8, 6) - TT(8)
    pc = fr.cam.p1(np.array([0.95, 0.42, 0.4]))

    def ui(img, fx):
        pill(img, fx, 540, 230, 'RED 5 GHz', eout(seg(u, 0.0, 0.25)), size=34, border=CYAN)
        if u > tok:
            dd = ImageDraw.Draw(img)
            k = P.resorte(seg(u, tok, tok + 0.3))
            r = 46 * k
            dd.ellipse((pc[0] - r, pc[1] - 270 - r, pc[0] + r, pc[1] - 270 + r), outline=VERDE, width=6)
            dd.line([(pc[0] - 20 * k, pc[1] - 270), (pc[0] - 4 * k, pc[1] - 252), (pc[0] + 24 * k, pc[1] - 290)], fill=VERDE, width=7)
            kicker(img, 'NI SE ENTERA', 330, seg(u, tok, tok + 0.2), col=VERDE)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. ¿y por qué le gana? (duelo)
def s_porque(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.6, -70, 6, ty=0.3), K(0.25, 3.2, 0, 3, ty=0.3), K(2.0, 3.0, 6, 3, ty=0.3)]))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.6)
    sombra(fr, -0.45, 0, 230, 55)
    sombra(fr, 0.6, 0, 150, 40)
    draw_objects(fr, microondas(t, luz=0.9, reloj='1:05', x=-0.45, s=0.6) + modem(t, x=0.6, s=0.85))

    def ui(img, fx):
        glass_type(img, fx, 'VS', 540, 760, 260, k=eout(seg(u, 0.05, 0.3)), fill_a=0.08)
        pill(img, fx, 300, 1300, 'MICROONDAS', eout(seg(u, 0.1, 0.3)), size=30, border=NAR)
        pill(img, fx, 790, 1300, 'MÓDEM', eout(seg(u, 0.2, 0.4)), size=30, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9 y 10. 1 000 W contra menos de 1 W
def barras(img, fx, t, k1, k2, kx):
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    base = 1300
    if k1 > 0.01:
        h = 900 * P.resorte(k1)
        d.rounded_rectangle((200, base - h, 440, base), radius=18, fill=(60, 34, 18), outline=NAR, width=5)
        df.rounded_rectangle((200, base - h, 440, base), radius=18, outline=M.scale_c(NAR, 0.6), width=10)
        d.text((320, base + 50), 'MICROONDAS', font=F('mono', 28), fill=(200, 202, 210), anchor='mm')
    if k2 > 0.01:
        h = max(4, 0.9 * P.resorte(k2))
        d.rounded_rectangle((640, base - h - 4, 880, base), radius=4, fill=CYAN)
        df.rounded_rectangle((640, base - h - 4, 880, base), radius=4, fill=M.scale_c(CYAN, 0.6))
        d.text((760, base + 50), 'MÓDEM', font=F('mono', 28), fill=(200, 202, 210), anchor='mm')
        d.text((760, base - 60), '< 1 W', font=F('sans', 64), fill=CYAN, anchor='mm')
    if kx > 0.01:
        d.text((540, 300), '×1 000', font=F('sansx', 120), fill=M.scale_c(WHITE, kx), anchor='mm')
        df.text((540, 300), '×1 000', font=F('sansx', 120), fill=M.scale_c(NAR, 0.5 * kx), anchor='mm')


def s_1000(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 5.0, -20, 28, ty=0.0), K(0.3, 4.4, 4, 22, ty=0.0), K(3.0, 4.2, 8, 22, ty=0.0)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    tw = wt(10, 5) - TT(10)

    def ui(img, fx):
        kicker(img, 'POTENCIA', 150, seg(u, 0.0, 0.3), col=(255, 170, 120))
        barras(img, fx, t, seg(u, 0.0, 0.5), 0.0, 0.0)
        P.numero_golpe(img, fx, '1 000 W', 700, seg(u, tw - 0.2, tw), size=170, col=NAR)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tw, 0.35), amp=22)


def s_1w(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.2, 8, 22, ty=0.0), K(0.3, 4.6, -6, 24, ty=0.0), K(3.0, 4.7, -10, 24, ty=0.0)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    tw = wt(11, 5) - TT(11)

    def ui(img, fx):
        kicker(img, 'POTENCIA', 150, 1.0, col=(255, 170, 120))
        barras(img, fx, t, 1.0, seg(u, 0.2, 0.5), seg(u, tw, tw + 0.3))
        M.doodle_arrow(img, fx, 470, 420, 700, 1150, t, k=eout(seg(u, tw + 0.1, tw + 0.5)), col=(255, 236, 160), w=6)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. como gritar junto a alguien que te habla en secreto (megáfono vs. susurro)
def megafono():
    cono = named(M3.cyl(0.08, 0.6, (230, 120, 50), n=28, shadow=0, gloss=0.5, r2=0.32, y0=0.0), 'mega', rim=0.6, gloss=0.5)
    mango = named(M3.box(0.08, 0.26, 0.1, (40, 40, 44), shadow=0, base=True).tf(t=(0, -0.26, 0.15)), 'mega')
    out = P.tfk([cono], rz=-90) + P.tfk([mango], rz=0, t=(0.1, 0, 0))
    return P.tfk(out, t=(-1.15, 0.55, 0))


def s_grito(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.8, 40, 8, ty=0.5), K(0.3, 3.4, 8, 5, ty=0.5), K(3.0, 3.2, 14, 5, ty=0.5)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9)
    draw_objects(fr, megafono())
    for i in range(5):  # ondas grandes del grito
        r = 0.15 + ((t - TT(12)) * 1.2 - i * 0.35) % 1.75
        pts = [(-0.55 + r * math.cos(q), 0.55 + r * math.sin(q), 0.0) for q in np.linspace(-0.75, 0.75, 30)]
        line3(fr, pts, col=NAR, w=5, a=0.9 * (1 - r / 1.9), glow=1.0)
    ts = wt(12, 6) - TT(12)
    seno(fr, 0.45, 1.0, 0.3, 0.3, 0.06, 0.012, t, CYAN, w=1.8, a=seg(u, ts, ts + 0.3) * 0.8)

    def ui(img, fx):
        kicker(img, 'ASÍ SE SIENTE TU WI-FI', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        pill(img, fx, 330, 1320, 'GRITO = MICRO', eout(seg(u, 0.2, 0.5)), size=30, border=NAR)
        pill(img, fx, 780, 1320, 'SECRETO = WI-FI', eout(seg(u, ts, ts + 0.3)), size=30, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


# 12. la puerta lo encierra
def s_puerta(t, fi, u, d):
    tcl = wt(13, 3) - TT(13)
    fr = Frame(cam(u, [K(-0.2, 3.3, 55, 12), K(0.3, 3.0, 40, 9), K(tcl + 0.1, 3.0, 40, 9), K(tcl + 0.3, 2.6, 12, 6), K(3.0, 2.5, 16, 6)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8, beam=0.5)
    sombra(fr, 0, 0, 420, 90)
    pu = 1 - P.eout4(seg(u, tcl - 0.4, tcl))
    draw_objects(fr, microondas(t, luz=0.9, puerta=pu, reloj='0:58'))

    def ui(img, fx):
        kicker(img, 'LA PUERTA ES UNA JAULA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        pill(img, fx, 540, 1330, 'ENCIERRA LAS ONDAS', eout(seg(u, tcl, tcl + 0.3)), size=34, border=CYAN)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tcl, 0.3), amp=14)


# 13. rejilla con hoyitos de 1 mm (zoom digital)
def s_rejilla(t, fi, u, d):
    t1 = wt(14, 3) - TT(14)
    z = 1.0 + 0.6 * P.eout4(seg(u, 0.35, 0.55)) + 0.8 * P.eout4(seg(u, t1, t1 + 0.2))
    fr = Frame(Cam(target=(-0.16, 0.42, FRONT_Z), dist=2.3 / z, yaw=0, pitch=2, cy=0.5))
    space(fr, t, floor=None, bokeh=0.6)
    draw_objects(fr, microondas(t, luz=0.9, reloj='0:55'))
    tm = wt(14, 6) - TT(14)
    a = fr.cam.p1(np.array([-0.16, 0.42, FRONT_Z + 0.04]))

    def ui(img, fx):
        M.rec_frame(img, t, k=1.0, zoom_label=f'x{z:.1f}')
        if u > tm:
            dd = ImageDraw.Draw(img)
            k = eout(seg(u, tm, tm + 0.3))
            dd.line([(a[0] - 120, a[1] - 160), (a[0] + 120, a[1] - 160)], fill=M.scale_c(AMBAR, k), width=5)
            for xx in (a[0] - 120, a[0] + 120):
                dd.line([(xx, a[1] - 185), (xx, a[1] - 135)], fill=M.scale_c(AMBAR, k), width=5)
            pill(img, fx, a[0], a[1] - 240, '1 mm', k, size=44, border=AMBAR, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. la onda mide 12 cm
def s_onda(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.2, -30, 6, ty=0.5), K(0.3, 2.8, 0, 2, ty=0.5), K(3.0, 2.7, 4, 2, ty=0.5)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    k = P.eout4(seg(u, -0.45, 0.2))
    seno(fr, -1.2, 1.2, 0.55, 0, 0.8, 0.22, t * 0.3, NAR, frac=k, w=5)
    tc = wt(15, 4) - TT(15)
    p0, p1 = fr.cam.p1(np.array([-0.4, 0.95, 0])), fr.cam.p1(np.array([0.4, 0.95, 0]))
    # rejilla diminuta a escala (puntos)
    for i in range(8):
        dot3(fr, (0.9 + 0.012 * i, 0.2, 0), r=1.6, col=(200, 200, 210), a=seg(u, 0.4, 0.7))

    def ui(img, fx):
        kicker(img, 'LONGITUD DE ONDA', 150, seg(u, 0.0, 0.3), col=(255, 170, 120))
        if u > tc:
            kk = eout(seg(u, tc, tc + 0.3))
            dd = ImageDraw.Draw(img)
            dd.line([(p0[0], p0[1]), (p0[0] + (p1[0] - p0[0]) * kk, p1[1])], fill=AMBAR, width=5)
            for p in (p0, p1):
                dd.line([(p[0], p[1] - 22), (p[0], p[1] + 22)], fill=M.scale_c(AMBAR, kk), width=5)
            pill(img, fx, (p0[0] + p1[0]) / 2, p0[1] - 80, '12 cm', kk, size=48, border=AMBAR, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. 120 veces más: rebota y se queda adentro (corte lateral)
def s_rebota(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.0, 80, 10, ty=0.4), K(0.3, 2.7, 90, 6, ty=0.4), K(4.0, 2.6, 92, 6, ty=0.4)]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    draw_objects(fr, microondas(t, luz=0.8, interior=True, mag=1.0), xray=1.0, keep=('in',))
    # paquetes de onda que rebotan entre el fondo y la puerta
    for j in range(7):
        s_ = ((t - TT(16)) * 0.9 + j / 7) % 1.0
        zz = -0.38 + 0.8 * (1 - abs(2 * s_ - 1))
        yy = 0.15 + 0.07 * j
        pts = [(DOOR_X0 + 0.15 + 0.03 * math.sin(q * 6 + t * 10), yy + 0.03 * math.sin(q * 9), zz + 0.0) for q in np.linspace(0, 1, 2)]
        dot3(fr, (DOOR_X0 + 0.46, yy, zz), r=6, col=NAR, a=0.9, glow=1.4)
    tr_ = wt(16, 4) - TT(16)

    def ui(img, fx):
        kicker(img, 'CORTE · RECREACIÓN', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        P.numero_golpe(img, fx, '×120', 330, seg(u, 0.0, 0.18), size=170, col=AMBAR)
        pill(img, fx, 540, 1330, 'REBOTA EN LA REJILLA', eout(seg(u, tr_, tr_ + 0.3)), size=32, border=NAR)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.18, 0.3), amp=18)


# 16. la luz sí pasa
def s_luz(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 2.4, -20, 4, tx=-0.16, ty=0.42), K(0.3, 2.0, 0, 2, tx=-0.16, ty=0.42), K(3.0, 1.9, 4, 2, tx=-0.16, ty=0.42)]))
    space(fr, t, floor=None, bokeh=0.8, beam=0.4, beam_x=0.4)
    draw_objects(fr, microondas(t, luz=1.0, reloj='0:41'))
    k = eout(seg(u, 0.1, 0.6))
    for i in range(9):  # rayos de luz amarilla que salen por los hoyitos
        x = -0.5 + 0.085 * i
        y = 0.2 + 0.05 * (i % 3)
        line3(fr, [(x, y + 0.2, FRONT_Z + 0.05), (x + 0.05, y + 0.25, FRONT_Z + 0.05 + 1.2 * k)], col=(255, 236, 160), w=2.2, a=0.7 * k, glow=0.9)

    def ui(img, fx):
        kicker(img, 'LA LUZ SÍ PASA', 150, seg(u, 0.0, 0.3), col=(255, 236, 160))
        pill(img, fx, 540, 1330, 'LUZ: 0.0005 mm · ONDA: 120 mm', eout(seg(u, 0.4, 0.7)), size=28, border=(255, 236, 160), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. basta una pizca (la fuga que permite la norma)
def s_pizca(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.4, 30, 10, tx=0.3, tz=0.3), K(0.3, 3.0, 20, 7, tx=0.3, tz=0.3), K(3.5, 2.9, 24, 7, tx=0.3, tz=0.3)]))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    sombra(fr, -0.3, -0.3, 330, 70)
    draw_objects(fr, microondas(t, luz=0.9, reloj='0:33', x=-0.3, z=-0.3))
    for j in range(16):
        s_ = ((t * 0.7 + j / 16) % 1.0)
        a0 = j * 2.4
        p = (-0.3 + DOOR_X0 + 0.46 + 0.5 * math.cos(a0) * (0.3 + s_), 0.4 + 0.3 * math.sin(a0) * (0.3 + s_), -0.3 + FRONT_Z + 0.05 + 1.3 * s_)
        dot3(fr, p, r=3.5, col=NAR, a=0.8 * (1 - s_) * seg(u, 0.2, 0.6), glow=1.2)
    tn = wt(18, 9) - TT(18)

    def ui(img, fx):
        kicker(img, 'UNA FUGA MÍNIMA', 150, seg(u, 0.0, 0.3), col=(255, 170, 120))
        pill(img, fx, 540, 1250, 'LÍMITE: 5 mW/cm² A 5 cm', eout(seg(u, tn, tn + 0.3)), size=32, border=AMBAR, dot=False)
        pill(img, fx, 540, 1350, 'NORMA DE SEGURIDAD', eout(seg(u, tn + 0.15, tn + 0.45)), size=26, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. para tapar la señal de tu Wi-Fi (el icono se llena de estática)
def s_tapa(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 3.4, -24, 8, ty=0.5), K(0.3, 3.0, 0, 4, ty=0.5), K(3.0, 2.9, 6, 4, ty=0.5)]))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)
    kn = seg(u, 0.4, 1.6)

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        nivel = 3 - int(3 * kn)
        wifi_icon(dd, 540, 900, 330, CYAN, nivel=nivel, tachado=kn >= 1)
        wifi_icon(ImageDraw.Draw(fx), 540, 900, 330, M.scale_c(CYAN, 0.4), nivel=nivel)
        ruido(img, (140, 520, 940, 1180), kn, t)
        kicker(img, 'TU SEÑAL', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if kn >= 1:
            kicker(img, 'TAPADA', 1260, 1.0, col=ROJO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19 y 20. el error: el módem en la cocina, junto al micro
def cocina(t, rojo=0.0, modem_x=0.95):
    mesa = named(M3.box(3.2, 0.06, 1.2, (120, 96, 72), shadow=0, base=True, gloss=0.25).tf(t=(0.2, -0.06, 0)), 'mesa', rim=0.4)
    pared = named(M3.box(3.6, 1.8, 0.06, (54, 56, 62), shadow=0, base=True, gloss=0.15).tf(t=(0.2, -0.06, -0.66)), 'pared', rim=0.3)
    return [pared, mesa] + microondas(t, luz=0.9, reloj='0:21', x=-0.4, z=-0.1, s=0.85) + modem(t, x=modem_x, z=-0.15, s=0.85, rojo=rojo)


def s_error(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.6, -50, 30, tx=0.2, ty=0.3), K(0.3, 4.0, -18, 24, tx=0.2, ty=0.3), K(3.0, 3.8, -12, 22, tx=0.2, ty=0.3)]))
    space(fr, t, floor=None, bokeh=0.7)
    draw_objects(fr, cocina(t, rojo=0.6 + 0.4 * math.sin(t * 8)))
    aros(fr, (-0.4, 0.36, 0.3), t, TT(20), NAR, vel=1.0, n=5, rmax=1.8, sep=0.3, a=0.7)

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, 0.0, 0.2), col=ROJO)
        P.titulo_golpe(img, fx, [('El error de', 'sans'), ('casi todos.', 'serif')], 210, seg(u, 0.1, 0.25), size=76)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.35), amp=18)


def s_junto(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 2.6, 30, 14, tx=0.5, ty=0.3), K(0.3, 2.3, 10, 10, tx=0.5, ty=0.3), K(3.0, 2.2, 14, 10, tx=0.5, ty=0.3)]))
    space(fr, t, floor=None, bokeh=0.7)
    draw_objects(fr, cocina(t, rojo=0.7 + 0.3 * math.sin(t * 8)))
    aros(fr, (-0.4, 0.36, 0.3), t, TT(20), NAR, vel=1.0, n=5, rmax=1.8, sep=0.3, a=0.7)
    c = fr.cam.p1(np.array([0.95, 0.15, -0.15]))
    tj = wt(21, 6) - TT(21)

    def ui(img, fx):
        doodle_circle(img, fx, c[0], c[1], 200, 130, t, k=eout(seg(u, 0.2, 0.6)), col=ROJO, w=7)
        pill(img, fx, 540, 300, 'MÓDEM EN LA COCINA', eout(seg(u, 0.1, 0.35)), size=34, border=ROJO)
        pill(img, fx, 540, 1330, 'JUNTO AL MICRO = ERROR', eout(seg(u, tj, tj + 0.3)), size=34, border=ROJO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21. aléjalo… o conéctate a la red de 5 GHz
def s_aleja(t, fi, u, d):
    t5 = wt(22, 2) - TT(22)
    if u < t5:
        fr = Frame(cam(u, [K(-0.2, 4.2, -10, 22, tx=0.6, ty=0.3), K(0.3, 4.6, -4, 20, tx=0.9, ty=0.3), K(3.0, 4.6, 0, 20, tx=0.9, ty=0.3)]))
        space(fr, t, floor=None, bokeh=0.7)
        mx = 0.95 + 1.3 * P.eout4(seg(u, 0.15, 0.6))
        draw_objects(fr, cocina(t, rojo=1 - seg(u, 0.3, 0.7), modem_x=mx))

        def ui(img, fx):
            pill(img, fx, 540, 300, 'ALÉJALO', eout(seg(u, 0.1, 0.35)), size=40, border=VERDE)
        fr.ui.append(ui)
        return finish(fr, fi)
    uu = u - t5
    fr = Frame(cam(uu, [K(-0.1, 2.4, -40, 6, ty=0.95), K(0.25, 2.0, 6, 3, ty=0.95), K(3.0, 1.9, 10, 3, ty=0.95)]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.4)
    draw_objects(fr, P.celular(scr_redes(eout(seg(uu, 0.6, 1.0))), ry=-6))

    def ui2(img, fx):
        pill(img, fx, 540, 230, 'O USA LA RED 5 GHz', eout(seg(uu, 0.0, 0.3)), size=36, border=CYAN)
    fr.ui.append(ui2)
    return finish(fr, fi)


# 22. mándaselo
def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 4.0, 30, 10, tx=-0.1, ty=0.5), K(0.3, 3.6, 10, 8, tx=-0.1, ty=0.5), K(3.0, 3.4, 16, 8, tx=-0.1, ty=0.5)]))
    space(fr, t, floor='lines', floor_a=0.85, bokeh=1.0, beam=0.5, beam_x=0.35)
    sombra(fr, -0.6, -0.4, 330, 70)
    draw_objects(fr, microondas(t, luz=0.0, reloj='0:00', x=-0.6, z=-0.4)
                 + tel(scr_llamada(t, 'ok', red='MiCasa-5G'), x=0.55, z=0.35, s=0.42, ry=-14))

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien culpa', 'sans'), ('a la compañía de internet.', 'serif')], 190, seg(u, 0.0, 0.45), size=64)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.62, 0.5), sfx=[]),
           dict(desde=2, fn=s_compania, tr='golpe', sfx=[]),
           dict(desde=3, fn=s_es_micro, tr='giro', sfx=[(0.2, 'scribble', 0.7), (0.4, 'slap', 0.6)]),
           dict(desde=4, fn=s_2450, tr='zoom', c=(0.45, 0.6), sfx=[(0.0, 'shimmer', 0.6), (0.4, 'tick', 0.6)]),
           dict(desde=5, fn=s_banda, tr='deslizar', sfx=[(0.0, 'chime_a', 0.5), (0.5, 'tick', 0.5), (0.75, 'tick', 0.5), (1.0, 'tick', 0.5)]),
           dict(desde=6, fn=s_dos, tr='whip', sfx=[(-0.25, 'whoosh', 0.5), (0.0, 'whoosh', 0.5)]),
           dict(desde=7, fn=s_congela, tr='glitch', sfx=[(0.1, 'tick', 0.5)]),
           dict(desde=8, fn=s_5ghz, tr='wipe', sfx=[(0.0, 'tick', 0.5)]),
           dict(desde=9, fn=s_porque, tr='golpe', c=(0.5, 0.45), sfx=[(0.1, 'slap', 0.7)]),
           dict(desde=10, fn=s_1000, tr='flash', sfx=[(0.0, 'riser', 0.4)]),
           dict(desde=11, fn=s_1w, tr='deslizar_abajo', sfx=[(0.2, 'tick2', 0.6)]),
           dict(desde=12, fn=s_grito, tr='whip_izq', sfx=[(0.0, 'burst', 0.4)]),
           dict(desde=13, fn=s_puerta, tr='iris', sfx=[]),
           dict(desde=14, fn=s_rejilla, tr='zoom', c=(0.4, 0.45), sfx=[(0.35, 'click', 0.8)]),
           dict(desde=15, fn=s_onda, tr='deslizar', sfx=[(0.0, 'whoosh_suave', 0.5)]),
           dict(desde=16, fn=s_rebota, tr='golpe', sfx=[(0.18, 'bass', 0.8)]),
           dict(desde=17, fn=s_luz, tr='push', c=(0.42, 0.45), sfx=[(0.1, 'shimmer', 0.6)]),
           dict(desde=18, fn=s_pizca, tr='wipe', sfx=[(0.2, 'whoosh_suave', 0.4)]),
           dict(desde=19, fn=s_tapa, tr='glitch', sfx=[(0.4, 'burst', 0.35), (1.0, 'burst', 0.35)]),
           dict(desde=20, fn=s_error, tr='giro', sfx=[(0.25, 'bass', 0.9)]),
           dict(desde=21, fn=s_junto, tr='deslizar_abajo', sfx=[(0.2, 'scribble', 0.8)]),
           dict(desde=22, fn=s_aleja, tr='whip', sfx=[(0.15, 'whoosh', 0.6)]),
           dict(desde=23, fn=s_mandalo, tr='ritmo', sfx=[]),
           dict(desde=24, loop=True, tr='zoom')]


def _sfx_dinamicos():
    tm = wt(0, 5) - TT(0)
    tg = wt(1, 3) - TT(0)
    ESCENAS[0]['sfx'] = [(0.0, 'burst', 0.5), (0.05, 'tick2', 0.6), (tm, 'sub', 0.5), (tg - 0.05, 'burst', 0.6),
                         (tg + 0.15, 'bass', 1.0), (tg + 0.5, 'tick', 0.5)]
    ESCENAS[1]['sfx'] = [(0.2, 'thud', 0.8), (wt(2, 4) - TT(2), 'scribble', 0.7)]
    tn = wt(4, 5) - TT(4)
    ESCENAS[3]['sfx'] += [(tn - 0.6, 'riser', 0.4), (tn + 0.4, 'chime_c', 0.6)]
    tb = wt(5, 5) - TT(5)
    ESCENAS[4]['sfx'] += [(tb, 'sub', 0.6)]
    tq = wt(7, 6) - TT(7)
    ESCENAS[6]['sfx'] += [(tq, 'burst', 0.5), (tq + 0.05, 'tick2', 0.6)]
    ESCENAS[7]['sfx'] += [(wt(8, 6) - TT(8), 'chime_b', 0.7)]
    ESCENAS[9]['sfx'] += [(wt(10, 5) - TT(10), 'bass', 1.0)]
    ESCENAS[10]['sfx'] += [(wt(11, 5) - TT(11), 'chime_c', 0.6), (wt(11, 5) - TT(11) + 0.1, 'scribble', 0.6)]
    ESCENAS[11]['sfx'] += [(wt(12, 6) - TT(12), 'tick', 0.4)]
    tcl = wt(13, 3) - TT(13)
    ESCENAS[12]['sfx'] = [(tcl - 0.4, 'whoosh', 0.5), (tcl, 'thud', 0.9), (tcl + 0.02, 'click', 0.7)]
    t1 = wt(14, 3) - TT(14)
    ESCENAS[13]['sfx'] += [(t1, 'click', 0.8), (wt(14, 6) - TT(14), 'tick', 0.6)]
    ESCENAS[14]['sfx'] += [(wt(15, 4) - TT(15), 'tick', 0.6)]
    ESCENAS[15]['sfx'] += [(wt(16, 4) - TT(16), 'tick', 0.5)]
    ESCENAS[17]['sfx'] += [(wt(18, 9) - TT(18), 'tick', 0.6), (wt(18, 9) - TT(18) + 0.15, 'tick2', 0.5)]
    ESCENAS[20]['sfx'] += [(wt(21, 6) - TT(21), 'slap', 0.7)]
    t5 = wt(22, 2) - TT(22)
    ESCENAS[21]['sfx'] += [(t5, 'whoosh', 0.6), (t5 + 0.6, 'chime_b', 0.7)]
    ESCENAS[22]['sfx'] = [(0.0, 'shimmer', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
