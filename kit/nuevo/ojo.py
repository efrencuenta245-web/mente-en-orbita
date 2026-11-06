"""Reel extra: «Tu ojo se apaga… y no lo notas.» (pedido por Efrén, vie 6-nov-2026, 15:00). Voz Isaac.
Inicio tipo 7 (macro extremo del iris que se aleja y revela el ojo, que se cierra de golpe). Primera transición: wipe.
Datos: Golan et al., eLife 2016 (parpadeo de 100–150 ms, al menos 1 000 por hora, 3–4 % del tiempo despierto con los
ojos cerrados; el cerebro suprime la señal, no la rellena); Volkmann, Riggs y Moore, Science 1980 (luz por el paladar:
la sensibilidad baja igual al parpadear), descrito en Willett, Maenner y Mayo, Front. Syst. Neurosci. 2023;
Portello, Chu y Rosenfield, Optom. Vis. Sci. 2014 (parpadeos incompletos 7.02 % en pantalla contra 4.33 % en papel);
regla 20-20-20 de la American Optometric Association. Ojo, cerebro, foco y gráficas: RECREACIÓN."""
import math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
import ojo_pieza as O
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, doodle_arrow,
                    line3, dot3, rec_frame, chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

S = M.SS
TEMA = 'ojo'
TXT = ['Tu ojo se apaga… y no lo notas.',                                  # 0
       'Cada vez que parpadeas,',                                          # 1
       'te quedas a ciegas una décima de segundo.',                        # 2
       'Y parpadeas unas mil veces cada hora.',                            # 3
       'Si la luz de tu cuarto se apagara así,',                           # 4
       'lo notarías al instante.',                                         # 5
       'Tu parpadeo dura lo mismo…',                                       # 6
       'y tu cerebro ni se entera.',                                       # 7
       'Haz la prueba: en el espejo nunca te ves parpadear.',              # 8
       'Grábate con el celular:',                                          # 9
       'ahí sí salen tus ojos cerrados.',                                  # 10
       'Súmalo: pasas como media hora al día',                             # 11
       'a ciegas… despierto.',                                             # 12
       'Mándaselo a quien jura que no se pierde nada.',                    # 13
       '¿Cómo lo esconde?',                                                # 14
       'Tu cerebro no rellena el hueco: lo borra.',                        # 15
       'Unos científicos metieron luz al ojo por el paladar,',             # 16
       'sin pasar por el párpado.',                                        # 17
       'Y aun así, al parpadear, la vista bajó:',                          # 18
       'el apagón lo hace tu cerebro.',                                    # 19
       'Pero frente a la pantalla,',                                       # 20
       '7 de cada 100 parpadeos se quedan a medias;',                      # 21
       'en papel, 4.',                                                     # 22
       'Por eso se te cansan los ojos:',                                   # 23
       'cada 20 minutos,',                                                 # 24
       'mira algo lejano 20 segundos.',                                    # 25
       'Mándaselo a alguien que vive pegado al celular…',                  # 26
       'porque en este video,',                                            # 27
       'tu ojo ya se apagó más de 15 veces.']                              # 28
VOZ = list(TXT)
VOZ[0] = '[curious] Tu ojo se apaga… y no lo notas.'
VOZ[11] = '[excited] Súmalo: pasas como media hora al día'
VOZ[21] = 'siete de cada cien parpadeos se quedan a medias;'
VOZ[22] = 'en papel, cuatro.'
VOZ[24] = 'cada veinte minutos,'
VOZ[25] = 'mira algo lejano veinte segundos.'
VOZ[28] = 'tu ojo ya se apagó más de quince veces.'

AMB = (255, 200, 120)
ROJO = (255, 64, 56)
AMARILLO = (255, 236, 160)
VERDE = (90, 220, 140)


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


def Z(u, claves):
    """Cámara 2D con golpes: claves [(u, dict(s=, x=, y=))] → (escala, dx, dy)."""
    p = P.cam_rapida(u, claves)
    return p.get('s', 1.0), p.get('x', 0.0), p.get('y', 0.0)


def zk(u, s=1.0, x=0.0, y=0.0):
    return (u, dict(s=s, x=x, y=y))


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def parpadeo(u, u0, cierra=0.07, quieto=0.05, abre=0.10):
    """Apertura del ojo durante un parpadeo que empieza en u0 (1 abierto → 0 cerrado → 1)."""
    if u < u0:
        return 1.0
    x = u - u0
    if x < cierra:
        return 1 - ease(x / cierra)
    x -= cierra
    if x < quieto:
        return 0.0
    x -= quieto
    if x < abre:
        return ease(x / abre)
    return 1.0


def ojo(img, cx, cy, ancho, apert=1.0, rojo=0.0, alfa=1.0, res=1000):
    O.pegar(img, O.ojo_img(apert, res, rojo), cx, cy, ancho, alfa)


def fondo(t, u, claves, floor='dots', floor_a=0.8, bokeh=0.9, beam=0.0, cy=0.55):
    fr = Frame(cam(u, claves, cy=cy))
    space(fr, t, floor=floor, floor_a=floor_a, bokeh=bokeh, beam=beam)
    return fr


# ================================================================== dibujos de line-art (2D, brillan)
def _brain_pts(seed=4):
    rng = np.random.RandomState(seed)
    th = np.linspace(0, 2 * math.pi, 220)
    r = 1 + 0.05 * np.sin(3 * th + 0.4) + 0.025 * np.sin(9 * th + 1.0)
    x = 1.25 * np.cos(th) * r
    y = 0.82 * np.sin(th) * r
    y = np.where(y > 0.25, 0.25 + (y - 0.25) * 0.55, y)          # base más plana
    out = list(zip(x, -y))
    giros = []
    for i in range(16):
        cx, cy = rng.uniform(-0.9, 0.9), rng.uniform(-0.55, 0.25)
        a = rng.uniform(0, math.pi)
        pts = []
        for k in range(26):
            s = k / 25 - 0.5
            px = cx + math.cos(a) * s * 0.9 + 0.06 * math.sin(k * 1.3 + i)
            py = cy + math.sin(a) * s * 0.5 + 0.07 * math.sin(k * 0.9 + i * 2)
            if (px / 1.2) ** 2 + (py / 0.75) ** 2 < 0.85:
                pts.append((px, py))
        if len(pts) > 4:
            giros.append(pts)
    cereb = [(0.75 + 0.32 * math.cos(a), 0.42 + 0.17 * math.sin(a)) for a in np.linspace(-0.3, math.pi + 0.3, 30)]
    tallo = [(0.35, 0.3), (0.42, 0.62), (0.46, 0.9)]
    return out, giros, cereb, tallo


_BR = _brain_pts()


def cerebro(img, fx, cx, cy, s, t, k=1.0, brillo=1.0, giro=0.0, col=WHITE, pulsos=True):
    """Cerebro de alambre visto de lado (s = medio ancho en px). giro (rad) lo voltea (escala en x)."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    sx = s * math.cos(giro)
    a = clamp(k) * brillo
    out, giros, cereb, tallo = _BR
    T = lambda p: (cx + p[0] * sx, cy + p[1] * s)
    c = M.scale_c(col, 0.95 * a)
    cg = M.scale_c(col, 0.5 * a)
    w = max(2, int(s / 110))
    n = max(2, int(len(out) * clamp(k * 1.3)))
    d.line([T(p) for p in out[:n]], fill=c, width=w + 1, joint='curve')
    df.line([T(p) for p in out[:n]], fill=cg, width=w + 6, joint='curve')
    for j, g in enumerate(giros):
        if k * 1.4 > j / len(giros):
            d.line([T(p) for p in g], fill=M.scale_c(col, 0.6 * a), width=w, joint='curve')
            df.line([T(p) for p in g], fill=M.scale_c(col, 0.25 * a), width=w + 4, joint='curve')
    d.line([T(p) for p in cereb], fill=M.scale_c(col, 0.7 * a), width=w, joint='curve')
    d.line([T(p) for p in tallo], fill=M.scale_c(col, 0.7 * a), width=w + 2, joint='curve')
    if pulsos and a > 0.2:
        for j, g in enumerate(giros[:10]):
            q = (t * 0.9 + j * 0.37) % 1.0
            x, y = T(g[int(q * (len(g) - 1))])
            r = s / 36
            d.ellipse((x - r, y - r, x + r, y + r), fill=M.scale_c(CYAN, a))
            df.ellipse((x - 3 * r, y - 3 * r, x + 3 * r, y + 3 * r), fill=M.scale_c(CYAN, 0.5 * a))


def foco(img, fx, cx, cy, s, on=1.0, k=1.0, cable=True):
    """Foco de line-art colgando: (cx, cy) = centro del bulbo; on 0..1 = luz."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    cw = M.scale_c(WHITE, 0.9 * k)
    if cable:
        d.line([(cx, 0), (cx, cy - s * 1.25)], fill=M.scale_c(WHITE, 0.5 * k), width=4)
    d.rectangle((cx - s * 0.32, cy - s * 1.25, cx + s * 0.32, cy - s * 0.78), outline=cw, width=4)
    for i in range(3):
        yy = cy - s * 1.15 + i * s * 0.12
        d.line([(cx - s * 0.32, yy), (cx + s * 0.32, yy + s * 0.05)], fill=cw, width=3)
    d.ellipse((cx - s * 0.75, cy - s * 0.85, cx + s * 0.75, cy + s * 0.65), outline=cw, width=5)
    if on > 0.01:
        gl = M.scale_c(AMB, on * k)
        d.ellipse((cx - s * 0.68, cy - s * 0.78, cx + s * 0.68, cy + s * 0.58), fill=M.scale_c(AMB, 0.55 * on * k))
        d.line([(cx - s * 0.2, cy - s * 0.78), (cx - s * 0.12, cy - s * 0.1), (cx, cy - s * 0.3), (cx + s * 0.12, cy - s * 0.1),
                (cx + s * 0.2, cy - s * 0.78)], fill=M.scale_c((255, 250, 230), on * k), width=6)
        for rr, aa in ((0.9, 0.55), (1.4, 0.18)):
            df.ellipse((cx - s * rr, cy - s * rr * 0.95, cx + s * rr, cy + s * rr * 0.85), fill=M.scale_c(gl, aa))
    else:
        d.line([(cx - s * 0.2, cy - s * 0.78), (cx - s * 0.12, cy - s * 0.1), (cx, cy - s * 0.3), (cx + s * 0.12, cy - s * 0.1),
                (cx + s * 0.2, cy - s * 0.78)], fill=M.scale_c(WHITE, 0.35 * k), width=3)


def reloj(img, fx, cx, cy, r, frac, k=1.0, col=WHITE, marcas=12):
    """Reloj de line-art con un sector que se llena (frac 0..1)."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(WHITE, 0.85 * k), width=5)
    for i in range(marcas):
        a = i / marcas * 2 * math.pi
        d.line([(cx + math.sin(a) * r * 0.86, cy - math.cos(a) * r * 0.86), (cx + math.sin(a) * r * 0.97, cy - math.cos(a) * r * 0.97)],
               fill=M.scale_c(WHITE, 0.7 * k), width=4)
    if frac > 0.002:
        d.pieslice((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), -90, -90 + 360 * clamp(frac), fill=M.scale_c(col, 0.55 * k))
        df.pieslice((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), -90, -90 + 360 * clamp(frac), fill=M.scale_c(col, 0.35 * k))
        a = -math.pi / 2 + 2 * math.pi * clamp(frac)
        d.line([(cx, cy), (cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78)], fill=M.scale_c(WHITE, k), width=6)
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=M.scale_c(WHITE, k))


def numero(img, fx, txt, x, y, size, k=1.0, col=WHITE, font='mono', anchor='mm', glow=0.45):
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    d.text((x, y), txt, font=F(font, size), fill=M.scale_c(col, clamp(k)), anchor=anchor)
    if glow:
        ImageDraw.Draw(fx).text((x, y), txt, font=F(font, size), fill=M.scale_c(col, glow * clamp(k)), anchor=anchor)


def pantalla_chat(burbujas, t, k_env=0.0):
    """Pantalla de chat genérica (sin marcas). burbujas: [(lado, texto, k)] lado 'i'/'d'; 'video' = miniatura del reel."""
    def dib(d, im):
        d.rectangle((0, 64, 420, 900), fill=(12, 14, 20))
        d.rectangle((0, 64, 420, 140), fill=(22, 25, 34))
        d.ellipse((24, 80, 72, 128), fill=(70, 74, 90))
        d.text((88, 92), 'Primo Beto', font=F('sanss', 24), fill=(235, 236, 240))
        d.text((88, 120), 'en línea', font=F('sansm', 16), fill=(150, 154, 168))
        y = 170
        for lado, txt, kk in burbujas:
            if kk <= 0.01:
                continue
            if txt == 'video':
                w, h = 230, 300
                x0 = 420 - 24 - w
                d.rounded_rectangle((x0, y, x0 + w, y + h), radius=18, fill=(30, 110, 140))
                mini = O.ojo_img(1.0, 400).resize((w - 20, int((w - 20) * 0.64)))
                im.paste(mini, (x0 + 10, y + 50), mini)
                d.text((x0 + 16, y + 14), 'Mente en órbita', font=F('sanss', 17), fill=(220, 240, 250))
                d.text((x0 + 16, y + 210), 'Tu ojo se apaga…', font=F('sans', 20), fill=(255, 255, 255))
                d.text((x0 + 16, y + 240), '30 min al día a ciegas', font=F('sansm', 16), fill=(210, 230, 240))
                d.polygon([(x0 + w / 2 - 14, y + 120), (x0 + w / 2 - 14, y + 160), (x0 + w / 2 + 18, y + 140)], fill=(255, 255, 255))
                y += h + 24
                continue
            f = F('sansm', 22)
            tw = min(300, d.textlength(txt, font=f))
            w, h = tw + 40, 62
            x0 = 24 if lado == 'i' else 420 - 24 - w
            col = (40, 44, 56) if lado == 'i' else (30, 110, 140)
            d.rounded_rectangle((x0, y, x0 + w, y + h), radius=20, fill=col)
            d.text((x0 + 20, y + 18), txt, font=f, fill=(240, 242, 246))
            y += h + 18
        d.rounded_rectangle((20, 820, 330, 870), radius=25, fill=(30, 33, 44))
        d.text((40, 834), 'Mensaje', font=F('sansm', 20), fill=(130, 134, 148))
        cxx, cyy = 372, 845
        rr = 28 * (1 + 0.25 * math.sin(math.pi * clamp(k_env)))
        d.ellipse((cxx - rr, cyy - rr, cxx + rr, cyy + rr), fill=(40, 170, 200) if k_env > 0 else (60, 64, 78))
        d.polygon([(cxx - 10, cyy - 12), (cxx - 10, cyy + 12), (cxx + 14, cyy)], fill=(255, 255, 255))
    return P.pantalla(dib)


def pantalla_camara(t, apert, rec=True):
    """App de cámara frontal grabando tu ojo (sin marcas)."""
    def dib(d, im):
        d.rectangle((0, 64, 420, 900), fill=(4, 4, 6))
        e = O.ojo_img(apert, 600)
        ew = 520
        e2 = e.resize((ew, int(ew * 0.64)))
        im.paste(e2, (-50, 300), e2)
        if rec:
            if int(t * 2) % 2 == 0:
                d.ellipse((24, 92, 44, 112), fill=(230, 50, 45))
            d.text((54, 90), 'REC  00:%02d' % (int(t) % 60), font=F('mono', 20), fill=(240, 240, 240))
        d.text((210, 760), 'VIDEO', font=F('sanss', 20), fill=(255, 214, 120), anchor='mm')
        cx, cy = 210, 828
        d.ellipse((cx - 44, cy - 44, cx + 44, cy + 44), outline=(240, 240, 244), width=5)
        d.rounded_rectangle((cx - 20, cy - 20, cx + 20, cy + 20), radius=6, fill=(230, 50, 45))
    return P.pantalla(dib)


# ================================================================== escenas
# 0. gancho, inicio tipo 7: macro extremo del iris → se aleja → el ojo se apaga de golpe. Con u < -0.3 (solo en el loop
#    final) hace lo contrario: el ojo entero, un parpadeo y la cámara se mete al iris.
def s_gancho(t, fi, u, d):
    fr = fondo(t, u, [K(-4, 4.0, -20, 10), K(0.0, 3.4, 10, 8), K(0.8, 3.0, -6, 6), K(4, 2.9, -10, 6)], floor='dots', floor_a=0.6, bokeh=0.8)
    ua = 0.80                                     # «apaga»: el párpado cae
    if u >= -0.3:
        z = 1 + 7.0 * (1 - P.eout4(seg(u, -0.05, ua - 0.05)))
        ap = 1.0 if u < ua else (1 - ease(seg(u, ua, ua + 0.12)) if u < 1.3 else ease(seg(u, 1.3, 1.45)))
    else:                                          # loop: del ojo entero al iris
        z = 1 + 7.0 * ease(seg(u, -1.6, -0.3))
        ap = parpadeo(u, -2.6) * parpadeo(u, -1.95)
    oscuro = (1 - ap) if u >= -0.3 else 0.0

    def ui(img, fx):
        cy = 900 + 60 * (z - 1) / 7
        ojo(img, 540, cy, 1000 * z, ap, res=2000)
        if oscuro > 0.01:
            img.paste((0, 0, 0), (0, 0), Image.new('L', img.size, int(200 * oscuro)))
        if u >= -0.3:
            kicker(img, 'TU OJO · AHORA MISMO', 150, seg(u, 0.4, 0.6), col=(150, 210, 230))
            P.titulo_golpe(img, fx, [('Tu ojo se apaga…', 'sans')], 210, seg(u, ua - 0.02, ua + 0.13), size=88)
            M.title(img, fx, [('y no lo notas.', 'serif')], 330, seg(u, 1.45, 1.8), size=84)
        if u < -0.6:
            n = int(clamp((u + 3.6) / 2.4) * 15)
            numero(img, fx, f'×{max(1, n)}', 540, 1330, 120, seg(u, -3.6, -3.3) * (1 - seg(u, -1.0, -0.7)), col=AMARILLO)
    fr.ui.append(ui)
    out = finish(fr, fi, bloom=0.8)
    return sacudir(out, t, golpe_k(u, ua + 0.12, 0.35), amp=24)


# 1. «cada vez que parpadeas»: el párpado baja (flecha) y la cámara da un golpe
def s_parpadea(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.6, 30, 12), K(0.3, 3.0, -8, 6), K(3, 2.9, -12, 6)], floor='lines', floor_a=0.7)
    ub = wt(1, 3) - TT(1)
    s, dx, dy = Z(u, [zk(-0.2, 1.25, -40), zk(0.25, 1.0), zk(ub, 1.12, 0, 30), zk(3, 1.15, 0, 30)])
    ap = parpadeo(u, ub, 0.12, 0.12, 0.2)

    def ui(img, fx):
        ojo(img, 540 + dx, 900 + dy, 1050 * s, ap)
        kicker(img, 'PÁRPADO SUPERIOR', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        doodle_arrow(img, fx, 900, 560, 900, 840, t, seg(u, 0.1, 0.45), col=AMARILLO, seed=3)
        pill(img, fx, 830, 500, 'BAJA EN 0.07 s', seg(u, 0.2, 0.45), size=30, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. «te quedas a ciegas una décima de segundo»: negro total y cronómetro 0.1 s
def s_decima(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.0, 0, 6), K(0.3, 3.4, 20, 10), K(3, 3.3, 24, 10)], floor='dots', floor_a=0.5, bokeh=0.6)
    ud = wt(2, 4) - TT(2)

    def ui(img, fx):
        frac = clamp(seg(u, ud, ud + 0.8)) * 0.1 / 1.0
        reloj(img, fx, 540, 860, 260, frac * 10 * 0.1, k=seg(u, -0.2, 0.1), col=CYAN, marcas=10)
        P.numero_golpe(img, fx, '0.1 s', 1300, seg(u, ud, ud + 0.15), size=210, col=WHITE)
        kicker(img, 'A CIEGAS', 150, seg(u, 0.0, 0.3), col=(255, 150, 140))
        if 0.15 < u < 0.45:
            img.paste((0, 0, 0), (0, 0), Image.new('L', img.size, 235))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ud + 0.15), amp=20)


# 3. «unas mil veces cada hora»: cuadrícula de ojos que parpadean + contador
def s_mil(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 4.4, -30, 14), K(0.3, 3.6, 8, 8), K(3, 3.5, 12, 8)], floor='lines', floor_a=0.6)
    s, dx, dy = Z(u, [zk(-0.2, 1.3), zk(0.3, 1.0), zk(3, 0.96)])

    def ui(img, fx):
        cols, rows = 5, 7
        for i in range(cols * rows):
            r, c = divmod(i, cols)
            kk = seg(u, -0.2 + 0.02 * i, 0.1 + 0.02 * i)
            if kk <= 0:
                continue
            fase = (i * 0.37) % 1.0
            ap = parpadeo((u + fase * 3) % 0.9, 0.0) if (i * 7) % 3 else parpadeo((u + fase) % 1.3, 0.0)
            x = 540 + dx + (c - 2) * 200 * s
            y = 820 + dy + (r - 3) * 135 * s
            ojo(img, x, y, 190 * s * P.resorte(kk), ap, res=400)
        n = int(1000 * P.eout4(seg(u, 0.1, 1.8)))
        numero(img, fx, f'{n:,}'.replace(',', ' '), 540, 1360, 150, seg(u, 0.0, 0.2), col=AMARILLO, font='sansx')
        kicker(img, 'PARPADEOS POR HORA', 1460, seg(u, 0.2, 0.4), col=(255, 224, 150))
        kicker(img, 'ELIFE · 2016', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. «si la luz de tu cuarto se apagara así»: foco colgando con su haz
def s_foco(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.8, -40, 16), K(0.3, 3.2, -6, 8), K(3, 3.1, -2, 8)], floor='lines', floor_a=0.8, beam=0.8)
    s, dx, dy = Z(u, [zk(-0.2, 0.8, 0, -200), zk(0.3, 1.0), zk(3, 1.05, 0, 20)])
    e = P.entrada(u, -0.2, 0.3, 'cae')

    def ui(img, fx):
        foco(img, fx, 540 + dx, 760 + dy + e['dy'] * 120, 150 * s, on=1.0)
        kicker(img, 'TU CUARTO', 150, seg(u, 0.0, 0.3), col=(255, 214, 140))
    fr.ui.append(ui)
    return finish(fr, fi, bloom=1.1)


# 5. «lo notarías al instante»: se apaga 0.1 s y ¡lo notas!
def s_foco_off(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.1, -2, 8), K(0.25, 2.6, 18, 6), K(3, 2.5, 22, 6)], floor='lines', floor_a=0.8)
    uo = 0.05
    on = 0.0 if uo <= u < uo + 0.1 else 1.0

    def ui(img, fx):
        foco(img, fx, 540, 780, 170, on=on)
        if not on:
            img.paste((0, 0, 0), (0, 0), Image.new('L', img.size, 200))
        P.titulo_golpe(img, fx, [('¡Lo notas!', 'sans')], 1180, seg(u, 0.25, 0.4), size=96, col=AMARILLO)
        doodle_circle(img, fx, 540, 760, 260, 300, t, seg(u, 0.35, 0.8), col=AMARILLO)
        kicker(img, 'APAGÓN DE 0.1 s', 150, seg(u, 0.1, 0.3), col=(255, 214, 140))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, bloom=1.1 if on else 0.3), t, golpe_k(u, 0.4), amp=22)


# 6. «tu parpadeo dura lo mismo»: pantalla dividida foco / ojo con la misma barra de 0.1 s
def s_igual(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.4, 30, 10), K(0.3, 3.0, 0, 6), K(3, 2.9, -4, 6)], floor='dots', floor_a=0.6)
    k1 = P.eout4(seg(u, -0.2, 0.15))

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        foco(img, fx, 540 - (1 - k1) * 700, 560, 110, on=0.0 if (u % 1.2) < 0.1 else 1.0, cable=False)
        ojo(img, 540 + (1 - k1) * 700, 1110, 760, parpadeo(u % 1.2, 0.0, 0.03, 0.04, 0.03))
        dd.line([(120, 840), (960, 840)], fill=(90, 92, 100), width=2)
        for yy, lab in ((760, 'LUZ APAGADA'), (1340, 'OJO CERRADO')):
            kk = seg(u, 0.2, 0.5)
            dd.rounded_rectangle((300, yy, 300 + 480 * kk, yy + 22), radius=11, fill=M.scale_c(CYAN, 0.9))
            ImageDraw.Draw(fx).rounded_rectangle((300, yy, 300 + 480 * kk, yy + 22), radius=11, fill=M.scale_c(CYAN, 0.4))
            numero(img, fx, '0.1 s', 860, yy + 11, 40, kk, font='mono', anchor='lm')
            kicker(img, lab, yy - 44, kk, col=(150, 210, 230))
        P.numero_golpe(img, fx, '=', 845, seg(u, 0.5, 0.65), size=200, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.65), amp=16)


# 7. «y tu cerebro ni se entera»: cerebro tranquilo con la señal continua
def s_cerebro(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.8, -30, 12), K(0.3, 3.2, 6, 8), K(3, 3.1, 10, 8)], floor='dots', floor_a=0.7, beam=0.4)
    e = P.entrada(u, -0.2, 0.3, 'pop')

    def ui(img, fx):
        cerebro(img, fx, 540, 820, 380 * max(0.05, e['escala']), t, k=seg(u, -0.2, 0.4), giro=0.25 * math.sin(t * 1.2))
        dd = ImageDraw.Draw(img)
        pts = [(140 + i * 8, 1250 + 18 * math.sin(i * 0.5 + t * 6)) for i in range(101)]
        dd.line(pts[:max(2, int(101 * seg(u, 0.1, 0.8)))], fill=VERDE, width=5)
        ImageDraw.Draw(fx).line(pts[:max(2, int(101 * seg(u, 0.1, 0.8)))], fill=M.scale_c(VERDE, 0.5), width=10)
        pill(img, fx, 540, 1360, 'NI SE ENTERA', seg(u, 0.6, 0.9), size=34, border=VERDE)
        kicker(img, 'TU CEREBRO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. «en el espejo nunca te ves parpadear»: espejo ovalado con marco de latón
def _espejo(img, fx, cx, cy, rx, ry, k):
    d = ImageDraw.Draw(img)
    for i in range(14):
        a = i / 13
        col = M.mixc((120, 90, 40), (240, 205, 120), 0.5 + 0.5 * math.sin(a * 3 + 1))
        d.ellipse((cx - rx - 40 + i * 2, cy - ry - 40 + i * 2, cx + rx + 40 - i * 2, cy + ry + 40 - i * 2), outline=M.scale_c(col, k), width=3)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(14, 16, 20))
    ImageDraw.Draw(fx).ellipse((cx - rx - 44, cy - ry - 44, cx + rx + 44, cy + ry + 44), outline=M.scale_c(AMB, 0.25 * k), width=10)


def s_espejo(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.6, 24, 10), K(0.3, 3.1, -6, 6), K(1.6, 2.7, 10, 4), K(4, 2.6, 12, 4)], floor='lines', floor_a=0.7, beam=0.6)
    s, dx, dy = Z(u, [zk(-0.2, 0.85), zk(0.3, 1.0), zk(1.6, 1.15, 0, -30), zk(4, 1.18, 0, -30)])
    e = P.entrada(u, -0.2, 0.25, 'desliza')

    def ui(img, fx):
        cx, cy = 540 + dx + e['dy'] * 150, 820 + dy
        rx, ry = 330 * s, 450 * s
        _espejo(img, fx, cx, cy, rx, ry, 1.0)
        msk = Image.new('L', img.size, 0)
        ImageDraw.Draw(msk).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
        capa = img.copy()
        ojo(capa, cx, cy, 700 * s, 1.0)
        brillo = Image.new('RGB', img.size, (255, 255, 255))
        gl = Image.new('L', img.size, 0)
        ImageDraw.Draw(gl).polygon([(cx - rx * 0.6, cy - ry), (cx - rx * 0.2, cy - ry), (cx - rx * 0.9, cy + ry), (cx - rx * 1.3, cy + ry)], fill=22)
        capa.paste(brillo, (0, 0), gl)
        img.paste(capa, (0, 0), msk)
        kicker(img, 'EN EL ESPEJO', 150, seg(u, 0.0, 0.3), col=(255, 214, 140))
        pill(img, fx, 540, 1390, 'PARPADEOS QUE VES: 0', seg(u, 1.4, 1.7), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. «grábate con el celular»: celular con la cámara frontal grabando
def s_cel(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.4, -50, 14, ty=1.0), K(0.3, 2.5, -14, 6, ty=1.0), K(3, 2.4, -18, 6, ty=1.0)], floor='dots', floor_a=0.8, beam=0.5, cy=0.58)
    ap = parpadeo(u, 0.6, 0.08, 0.1, 0.12)
    e = P.entrada(u, -0.2, 0.3, 'gira')
    draw_objects(fr, P.celular(pantalla_camara(t, ap), ry=math.degrees(e['giro']) * 0.25))

    def ui(img, fx):
        kicker(img, 'CÁMARA FRONTAL · VIDEO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


# 10. «ahí sí salen tus ojos cerrados»: zoom digital al cuadro donde estás con los ojos cerrados
def s_rec(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.0, 0, 6), K(3, 3.0, 4, 6)], floor=None, floor_a=0.0, bokeh=0.3)
    z = 1.0 if u < 0.5 else (1.35 if u < 1.1 else 1.8)
    lab = 'x1.0' if u < 0.5 else ('x1.3' if u < 1.1 else 'x1.8')
    ap = 1.0 if u < 0.25 else 0.0

    def ui(img, fx):
        ojo(img, 540, 860, 1000 * z, ap)
        rec_frame(img, t, 1.0, lab)
        pill(img, fx, 540, 1320, 'OJOS CERRADOS', seg(u, 0.3, 0.55), size=36, border=ROJO)
        kicker(img, 'CUADRO 00:%02d:%02d' % (int(t) % 60, int((t % 1) * 24)), 300, seg(u, 0.0, 0.2), col=(200, 200, 205))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.5, 0.2) + golpe_k(u, 1.1, 0.2), amp=10)


# 11. SEGUNDO GANCHO «súmalo: como media hora al día»: 30 MIN que golpea y el reloj se llena
def s_suma(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 4.0, 40, 14), K(0.3, 3.2, -10, 6), K(3, 3.1, -14, 6)], floor='lines', floor_a=0.8, beam=0.6)
    u30 = wt(11, 4) - TT(11)

    def ui(img, fx):
        reloj(img, fx, 540, 760, 300, 0.5 * P.eout4(seg(u, u30, u30 + 0.6)), k=seg(u, -0.2, 0.1), col=AMARILLO)
        P.numero_golpe(img, fx, '30 MIN', 1230, seg(u, u30, u30 + 0.15), size=170, col=AMARILLO)
        pill(img, fx, 540, 1390, '3–4 % DE TU DÍA DESPIERTO', seg(u, u30 + 0.6, u30 + 0.9), size=32, border=AMARILLO)
        kicker(img, 'SÚMALO', 150, seg(u, 0.0, 0.2), col=(255, 224, 150))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u30 + 0.15, 0.4), amp=26)


# 12. «a ciegas… despierto»: la barra de tu día con cientos de rayitas negras que se juntan en un bloque
def s_despierto(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.2, -20, 8), K(0.3, 2.8, 8, 6), K(3, 2.7, 10, 6)], floor='dots', floor_a=0.6)
    kj = P.eout4(seg(u, 0.7, 1.4))

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        x0, x1, y0, y1 = 110, 970, 820, 940
        dd.rounded_rectangle((x0, y0, x1, y1), radius=20, fill=(250, 214, 120))
        ImageDraw.Draw(fx).rounded_rectangle((x0, y0, x1, y1), radius=20, fill=(120, 100, 50))
        rng = np.random.RandomState(9)
        xs = np.sort(rng.uniform(x0 + 6, x1 - 6, 160))
        bloque = (x1 - x0) * 0.035
        for i, x in enumerate(xs):
            if seg(u, -0.1 + i * 0.004, i * 0.004) <= 0:
                continue
            xt = x1 - bloque + (i / len(xs)) * bloque
            xx = lerp(x, xt, kj)
            dd.rectangle((xx - 1.6, y0 + 4, xx + 1.6, y1 - 4), fill=(8, 8, 10))
        if kj > 0.95:
            dd.rectangle((x1 - bloque - 2, y0, x1, y1), fill=(8, 8, 10))
            doodle_circle(img, fx, x1 - bloque / 2, (y0 + y1) / 2, 70, 110, t, seg(u, 1.4, 1.7), col=WHITE)
        numero(img, fx, '7:00', x0, y1 + 50, 34, seg(u, 0.0, 0.3), font='mono', anchor='lm', glow=0)
        numero(img, fx, '23:00', x1, y1 + 50, 34, seg(u, 0.0, 0.3), font='mono', anchor='rm', glow=0)
        kicker(img, 'TU DÍA · 16 h DESPIERTO', 150, seg(u, 0.0, 0.3), col=(255, 224, 150))
        ojo(img, 540, 520, 620, parpadeo(u % 0.8, 0.2, 0.04, 0.05, 0.05))
        P.titulo_golpe(img, fx, [('…despierto.', 'serif')], 1180, seg(u, wt(12, 2) - TT(12), wt(12, 2) - TT(12) + 0.15), size=90)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. «mándaselo a quien jura que no se pierde nada»: chat genérico, se manda el reel
def s_manda1(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.2, 40, 12, ty=1.0), K(0.3, 2.5, 10, 6, ty=1.0), K(3, 2.4, 14, 6, ty=1.0)], floor='lines', floor_a=0.8, beam=0.5, cy=0.58)
    ue = 1.0
    b = [('i', 'Yo no me pierdo nada', seg(u, -0.2, 0.0)), ('d', 'video', seg(u, ue, ue + 0.1))]
    draw_objects(fr, P.celular(pantalla_chat(b, t, seg(u, ue - 0.15, ue + 0.15))))

    def ui(img, fx):
        kicker(img, 'MÁNDASELO', 150, seg(u, 0.0, 0.3), col=(150, 230, 210))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ue, 0.3), amp=12)


# 14. «¿cómo lo esconde?»: signos de cristal y el cerebro que entra girando
def s_como(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.6, -40, 10), K(0.3, 3.0, 0, 6), K(3, 2.9, 4, 6)], floor='dots', floor_a=0.6, beam=0.4)
    e = P.entrada(u, -0.2, 0.3, 'gira')

    def ui(img, fx):
        glass_type(img, fx, '¿?', 540, 820, 620, k=seg(u, -0.2, 0.2))
        cerebro(img, fx, 540, 820, 300 * max(0.05, e['escala']), t, k=1.0, giro=e['giro'])
        kicker(img, '¿CÓMO LO ESCONDE?', 150, seg(u, 0.0, 0.2), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


# 15. «no rellena el hueco: lo borra»: tira de cuadros con un cuadro negro que se borra
def s_borra(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.4, 20, 8), K(0.3, 2.9, -6, 6), K(3, 2.8, -8, 6)], floor='lines', floor_a=0.6)
    ur = wt(15, 3) - TT(15)
    ub = wt(15, 6) - TT(15)
    kb = P.eout4(seg(u, ub, ub + 0.4))

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        n, w, h, gap = 5, 180, 240, 20
        xs = [540 + (i - 2) * (w + gap) for i in range(n)]
        for i, x in enumerate(xs):
            if i == 2:
                if kb > 0.98:
                    continue
                xx = x
                sc = 1 - kb
                dd.rectangle((xx - w / 2 * sc, 820 - h / 2, xx + w / 2 * sc, 820 + h / 2), fill=(4, 4, 6), outline=ROJO, width=4)
                continue
            shift = (w + gap) / 2 * kb * (1 if i < 2 else -1)
            x2 = x + shift
            dd.rectangle((x2 - w / 2, 820 - h / 2, x2 + w / 2, 820 + h / 2), fill=(40, 46, 60), outline=(220, 220, 228), width=3)
            ojo(img, x2, 820, w * 0.9, 1.0, res=400)
            for j in range(4):
                dd.rectangle((x2 - w / 2 + 10 + j * 44, 820 - h / 2 - 34, x2 - w / 2 + 34 + j * 44, 820 - h / 2 - 14), fill=(200, 200, 205))
                dd.rectangle((x2 - w / 2 + 10 + j * 44, 820 + h / 2 + 14, x2 - w / 2 + 34 + j * 44, 820 + h / 2 + 34), fill=(200, 200, 205))
        P.pill_tachada(img, fx, 540, 1130, 'LO RELLENA', seg(u, ur - 0.3, ur), seg(u, ur + 0.1, ur + 0.4), t, size=40)
        P.titulo_golpe(img, fx, [('Lo borra.', 'serif')], 1230, seg(u, ub, ub + 0.15), size=110, col=CYAN)
        kicker(img, 'LO QUE VE TU CEREBRO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.15), amp=18)


# 16-17. diagrama del experimento: corte del ojo, fibra de luz que entra por el paladar
def _diagrama(img, fx, t, u, cx, cy, R, k_fibra, cierre, k=1.0):
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    c = M.scale_c(CYAN, 0.9 * k)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=c, width=5)
    df.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c(CYAN, 0.4 * k), width=10)
    d.arc((cx - R * 0.93, cy - R * 0.93, cx + R * 0.93, cy + R * 0.93), 120, 240, fill=M.scale_c((255, 120, 110), k), width=12)
    d.text((cx - R * 1.02, cy + R * 0.55), 'RETINA', font=F('mono', 26), fill=M.scale_c((255, 150, 140), k), anchor='rm')
    d.ellipse((cx + R * 0.55, cy - R * 0.3, cx + R * 0.8, cy + R * 0.3), outline=M.scale_c(WHITE, 0.8 * k), width=4)
    d.arc((cx + R * 0.7, cy - R * 0.55, cx + R * 1.25, cy + R * 0.55), -60, 60, fill=M.scale_c(WHITE, 0.6 * k), width=4)
    # párpado: cortinilla que baja frente al ojo
    if cierre > 0.01:
        y1 = cy - R * 1.05 + 2.1 * R * cierre
        d.rectangle((cx + R * 1.0, cy - R * 1.05, cx + R * 1.18, y1), fill=M.scale_c((188, 138, 112), k))
        d.text((cx + R * 1.3, cy - R * 1.0), 'PÁRPADO', font=F('mono', 26), fill=M.scale_c(WHITE, 0.8 * k), anchor='lm')
    # paladar y fibra
    py = cy + R * 1.65
    d.line([(cx - R * 1.4, py), (cx + R * 1.3, py)], fill=M.scale_c(WHITE, 0.6 * k), width=4)
    d.text((cx - R * 1.4, py + 20), 'PALADAR', font=F('mono', 26), fill=M.scale_c(WHITE, 0.7 * k), anchor='la')
    if k_fibra > 0.01:
        pts = [(cx - R * 0.2, py + R * 0.9), (cx - R * 0.35, py), (cx - R * 0.75, cy + R * 0.2)]
        tot = int(30 * clamp(k_fibra))
        seg_pts = []
        for i in range(tot + 1):
            q = i / 30
            if q < 0.5:
                a, b, qq = pts[0], pts[1], q / 0.5
            else:
                a, b, qq = pts[1], pts[2], (q - 0.5) / 0.5
            seg_pts.append((lerp(a[0], b[0], qq), lerp(a[1], b[1], qq)))
        if len(seg_pts) > 1:
            d.line(seg_pts, fill=M.scale_c(AMB, k), width=10)
            df.line(seg_pts, fill=M.scale_c(AMB, 0.8 * k), width=26)
        if k_fibra >= 1:
            x, y = pts[2]
            r = 40 + 8 * math.sin(t * 12)
            df.ellipse((x - r, y - r, x + r, y + r), fill=M.scale_c(AMB, 0.9 * k))


def s_paladar(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.8, -30, 10), K(0.3, 3.1, 0, 6), K(3, 3.0, 6, 6)], floor='dots', floor_a=0.5)
    up = wt(16, 7) - TT(16)
    s, dx, dy = Z(u, [zk(-0.2, 0.8), zk(0.3, 1.0), zk(up, 1.0), zk(up + 0.6, 1.0, 0, -60), zk(4, 1.0, 0, -60)])

    def ui(img, fx):
        _diagrama(img, fx, t, u, 520 + dx, 700 + dy, 250 * s, seg(u, up - 0.3, up + 0.6), 0.0, k=seg(u, -0.2, 0.2))
        kicker(img, 'EXPERIMENTO · SCIENCE 1980', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        pill(img, fx, 540, 1390, 'FIBRA DE LUZ EN LA BOCA', seg(u, up, up + 0.3), size=32, border=AMB)
        kicker(img, 'RECREACIÓN', 1480, seg(u, 0.2, 0.5), col=(130, 132, 140))
    fr.ui.append(ui)
    return finish(fr, fi)


def s_parpado(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.0, 6, 6), K(0.3, 2.6, 20, 4), K(3, 2.5, 24, 4)], floor='dots', floor_a=0.5)
    kc = P.eout4(seg(u, 0.1, 0.5))
    s, dx, dy = Z(u, [zk(-0.2, 1.0, 0, -60), zk(0.3, 1.25, -60, -120), zk(3, 1.28, -60, -120)])

    def ui(img, fx):
        _diagrama(img, fx, t, u, 520 + dx, 700 + dy, 250 * s, 1.0, kc)
        pill(img, fx, 540, 1390, 'LA LUZ LLEGA IGUAL', seg(u, 0.5, 0.8), size=34, border=AMB)
        kicker(img, 'SIN PASAR POR EL PÁRPADO', 150, seg(u, 0.0, 0.3), col=(255, 214, 140))
    fr.ui.append(ui)
    return finish(fr, fi)


# 18. «y aun así, al parpadear, la vista bajó»: gráfica de sensibilidad con un hoyo en cada parpadeo
def s_curva(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.4, -24, 10), K(0.3, 2.9, 4, 6), K(3, 2.8, 8, 6)], floor='lines', floor_a=0.6)
    ub = wt(18, 5) - TT(18)

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        dfx = ImageDraw.Draw(fx)
        k0 = eout(seg(u, -0.2, 0.2))
        x0, x1, y0, y1 = 110, 970, 560, 1160
        over = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ImageDraw.Draw(over).rounded_rectangle((x0 - 30, y0 - 90, x1 + 30, y1 + 90), radius=30, fill=(12, 13, 17, int(220 * k0)),
                                               outline=(255, 255, 255, int(60 * k0)), width=2)
        img.paste(over, (0, 0), over)
        dd.text((x0, y0 - 60), 'SENSIBILIDAD DE LA VISTA', font=F('mono', 26), fill=M.scale_c((150, 152, 160), k0))
        dd.text((x0, y1 + 30), 'TIEMPO →', font=F('mono', 24), fill=M.scale_c((150, 152, 160), k0))
        bx = x0 + (x1 - x0) * 0.55
        dd.rectangle((bx - 40, y0, bx + 40, y1), fill=M.scale_c((60, 30, 30), k0))
        dd.text((bx, y0 + 20), 'PARPADEO', font=F('mono', 22), fill=M.scale_c(ROJO, k0), anchor='mt')
        n = 120
        pts = []
        for i in range(n):
            q = i / (n - 1)
            x = x0 + (x1 - x0) * q
            dip = math.exp(-((x - bx) / 55) ** 2) * 0.62
            y = y0 + 150 + (y1 - y0 - 200) * dip + 6 * math.sin(i * 0.7)
            pts.append((x, y))
        m = max(2, int(n * seg(u, 0.1, ub + 0.4)))
        dd.line(pts[:m], fill=M.scale_c(AMB, k0), width=6)
        dfx.line(pts[:m], fill=M.scale_c(AMB, 0.5 * k0), width=14)
        pill(img, fx, 540, 1390, 'LUZ ENCENDIDA TODO EL TIEMPO', seg(u, 0.0, 0.3), size=30, border=AMB)
        if m > n * 0.6:
            doodle_circle(img, fx, bx, y1 - 140, 110, 120, t, seg(u, ub + 0.3, ub + 0.6), col=ROJO)
        kicker(img, 'LA VISTA BAJÓ', 150, seg(u, ub, ub + 0.2), col=(255, 150, 140))
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. «el apagón lo hace tu cerebro»: el cerebro baja su propio interruptor
def s_apagon(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.6, 30, 10), K(0.3, 3.0, -4, 6), K(3, 2.9, -8, 6)], floor='dots', floor_a=0.6, beam=0.5)
    us = wt(19, 2) - TT(19)
    off = u >= us

    def ui(img, fx):
        brillo = 1.0 if not off else 0.35 + 0.65 * (1 - seg(u, us, us + 0.1)) * 0 + 0.25
        cerebro(img, fx, 540, 760, 340, t, k=1.0, brillo=brillo, col=WHITE if not off else (180, 190, 210), pulsos=not off)
        dd = ImageDraw.Draw(img)
        x, y = 540, 1220
        dd.rounded_rectangle((x - 70, y - 110, x + 70, y + 110), radius=20, outline=(230, 230, 236), width=5)
        yy = y - 50 if not off else y + 50
        dd.rounded_rectangle((x - 40, yy - 40, x + 40, yy + 40), radius=12, fill=AMARILLO if not off else (90, 92, 100))
        dd.text((x + 100, y - 60), 'ON', font=F('mono', 34), fill=(200, 200, 205))
        dd.text((x + 100, y + 40), 'OFF', font=F('mono', 34), fill=ROJO if off else (120, 120, 126))
        kicker(img, 'EL APAGÓN LO HACE TU CEREBRO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi, bloom=1.0 if not off else 0.6), t, golpe_k(u, us), amp=18)


# 20. EL ERROR «pero frente a la pantalla»: celular brillando frente al ojo, todo rojo
def s_pantalla(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.2, -30, 8, ty=1.0), K(0.25, 2.7, 4, 4, ty=1.0), K(3, 2.6, 8, 4, ty=1.0)], floor='lines', floor_a=0.6, cy=0.62)

    def scr(dd, im):
        dd.rectangle((0, 64, 420, 900), fill=(28, 34, 48))
        for i in range(9):
            y = 120 + i * 82 - (t * 160) % 82
            dd.rounded_rectangle((24, y, 396, y + 66), radius=12, fill=(48, 56, 76))
    draw_objects(fr, P.celular(P.pantalla(scr)))

    def ui(img, fx):
        ojo(img, 540, 330, 760, 0.85, rojo=0.4)
        P.titulo_golpe(img, fx, [('EL ERROR', 'sans')], 1330, seg(u, 0.1, 0.25), size=110, col=ROJO)
        kicker(img, 'FRENTE A LA PANTALLA', 1460, seg(u, 0.2, 0.4), col=(255, 150, 140))
        rojo = Image.new('RGB', img.size, (120, 0, 0))
        img.paste(rojo, (0, 0), Image.new('L', img.size, int(40 * seg(u, 0.0, 0.2))))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25), amp=20)


# 21. «7 de cada 100 parpadeos se quedan a medias»: el párpado se atora a la mitad
def s_medias(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.4, 20, 8), K(0.3, 2.9, -6, 6), K(4, 2.8, -10, 6)], floor='dots', floor_a=0.6)
    um = wt(21, 7) - TT(21)
    ap = 1.0 - 0.55 * ease(seg(u, um - 0.2, um)) if u < um + 0.5 else 1 - 0.55 * (1 - ease(seg(u, um + 0.5, um + 0.7)))

    def ui(img, fx):
        ojo(img, 540, 760, 1000, ap)
        if u > um - 0.1:
            doodle_circle(img, fx, 540, 700, 470, 200, t, seg(u, um - 0.1, um + 0.3), col=ROJO)
            pill(img, fx, 540, 470, 'A MEDIAS', seg(u, um, um + 0.2), size=40, border=ROJO)
        k1 = seg(u, -0.1, 0.1)
        numero(img, fx, '7', 380, 1240, 220, k1, col=ROJO, font='sansx')
        numero(img, fx, 'de cada 100', 640, 1260, 60, k1, col=WHITE, font='sans', glow=0.2)
        kicker(img, 'PARPADEOS INCOMPLETOS · PANTALLA', 150, seg(u, 0.0, 0.3), col=(255, 150, 140))
    fr.ui.append(ui)
    return finish(fr, fi)


# 22. «en papel, 4»: gráfica que crece papel 4 contra pantalla 7
def s_papel(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.2, -20, 8), K(0.3, 2.8, 6, 6), K(3, 2.7, 10, 6)], floor='lines', floor_a=0.6)

    def ui(img, fx):
        chart_grow(img, fx, (110, 470, 970, 1250), [4.33, 7.02], ['PAPEL', 'PANTALLA'], TT(22) - 0.35, t,
                   title_txt='PARPADEOS A MEDIAS (%)', vmax=8.5, line=False, tag='OPTOM VIS SCI 2014')
        kicker(img, 'DE CADA 100 PARPADEOS', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


# 23. «por eso se te cansan los ojos»: ojo rojo y entrecerrado
def s_cansado(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.6, 30, 10), K(0.3, 3.0, 6, 6), K(3, 2.9, 2, 6)], floor='dots', floor_a=0.5)
    s, dx, dy = Z(u, [zk(-0.2, 1.4), zk(0.25, 1.1), zk(3, 1.15)])

    def ui(img, fx):
        ojo(img, 540 + dx, 820 + dy, 1000 * s, 0.7 + 0.05 * math.sin(t * 3), rojo=1.0)
        pill(img, fx, 540, 1330, 'SECOS Y CANSADOS', seg(u, 0.3, 0.6), size=38, border=ROJO)
        kicker(img, 'OJO CANSADO', 150, seg(u, 0.0, 0.3), col=(255, 150, 140))
    fr.ui.append(ui)
    return finish(fr, fi)


# 24. «cada 20 minutos»: cronómetro 20:00 que golpea
def s_20min(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.6, -30, 12), K(0.25, 3.0, 0, 6), K(3, 2.9, 4, 6)], floor='lines', floor_a=0.7, beam=0.5)
    k = P.eout4(seg(u, -0.1, 0.6))

    def ui(img, fx):
        mins = int(20 * k)
        reloj(img, fx, 540, 800, 280, k * 20 / 60, k=seg(u, -0.2, 0.0), col=CYAN)
        P.numero_golpe(img, fx, f'{mins:02d}:00', 1250, seg(u, 0.45, 0.6), size=170, col=WHITE)
        kicker(img, 'REGLA 20-20-20', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.6), amp=16)


# 25. «mira algo lejano 20 segundos»: la cámara vuela hacia unas montañas lejanas
def s_lejos(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 2.2, 0, 4, tz=2.0), K(0.4, 6.5, 0, 6, tz=-2.0), K(3, 7.0, 0, 6, tz=-2.5)], floor='lines', floor_a=1.0, bokeh=0.6)
    for j, (z, h, col) in enumerate(((-9, 2.4, 0.5), (-12, 3.4, 0.35))):
        pts = []
        for i in range(60):
            x = -9 + 18 * i / 59
            q = (x * (0.32 + 0.1 * j) + j * 0.7) % 2.0
            y = h * (1 - abs(q - 1)) ** 1.3 * (0.65 + 0.35 * math.sin(x * 0.9 + j * 3)) + 0.08 * math.sin(x * 7.0)
            pts.append((x, max(0.0, y), z))
        line3(fr, pts, col=WHITE, w=2.5, a=col * 2, glow=0.7)
    us = wt(25, 3) - TT(25)

    def ui(img, fx):
        n = int(20 * clamp(seg(u, us, us + 1.4)))
        numero(img, fx, f'{n:02d} s', 540, 1230, 150, seg(u, us - 0.1, us + 0.1), col=AMARILLO, font='sansx')
        pill(img, fx, 540, 1380, 'A 6 METROS O MÁS', seg(u, 0.4, 0.7), size=32, border=AMARILLO)
        kicker(img, 'ALGO LEJANO', 150, seg(u, 0.0, 0.3), col=(255, 224, 150))
    fr.ui.append(ui)
    return finish(fr, fi)


# 26. «mándaselo a alguien que vive pegado al celular»: el celular da una vuelta y se manda
def s_manda2(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.0, -60, 12, ty=1.0), K(0.4, 2.5, 8, 6, ty=1.0), K(3, 2.4, 12, 6, ty=1.0)], floor='dots', floor_a=0.8, beam=0.6, cy=0.58)
    ue = wt(26, 3) - TT(26)
    b = [('i', 'No suelto el cel en todo el día', seg(u, -0.2, 0.0)), ('d', 'video', seg(u, ue, ue + 0.1))]
    giro = 360 * (1 - P.eout4(seg(u, -0.2, 0.5)))
    draw_objects(fr, P.celular(pantalla_chat(b, t, seg(u, ue - 0.15, ue + 0.15)), ry=giro))

    def ui(img, fx):
        kicker(img, 'MÁNDASELO', 150, seg(u, 0.0, 0.3), col=(150, 230, 210))
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ue, 0.3), amp=12)


# 27. «porque en este video»: 15 ojos que van apareciendo y parpadean
def s_quince(t, fi, u, d):
    fr = fondo(t, u, [K(-0.2, 3.4, 24, 10), K(0.3, 3.0, -4, 6), K(3, 2.9, -8, 6)], floor='lines', floor_a=0.6)

    def ui(img, fx):
        for i in range(15):
            r, c = divmod(i, 3)
            ki = seg(u, -0.2 + i * 0.07, -0.1 + i * 0.07)
            if ki <= 0:
                continue
            x = 540 + (c - 1) * 300
            y = 470 + r * 190
            ojo(img, x, y, 280 * P.resorte(ki), parpadeo(u, -0.1 + i * 0.07, 0.04, 0.04, 0.06), res=400)
        kicker(img, 'EN ESTE VIDEO', 150, seg(u, 0.0, 0.3), col=(255, 224, 150))
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.47), sfx=[]),
           dict(desde=1, fn=s_parpadea, tr='wipe', sfx=[]),
           dict(desde=2, fn=s_decima, tr='golpe', sfx=[]),
           dict(desde=3, fn=s_mil, tr='deslizar', sfx=[]),
           dict(desde=4, fn=s_foco, tr='whip', sfx=[]),
           dict(desde=5, fn=s_foco_off, tr='corte', sfx=[]),
           dict(desde=6, fn=s_igual, tr='giro', sfx=[]),
           dict(desde=7, fn=s_cerebro, tr='iris', c=(0.5, 0.43), sfx=[]),
           dict(desde=8, fn=s_espejo, tr='deslizar_abajo', sfx=[]),
           dict(desde=9, fn=s_cel, tr='whip_izq', sfx=[]),
           dict(desde=10, fn=s_rec, tr='zoom', c=(0.5, 0.45), sfx=[]),
           dict(desde=11, fn=s_suma, tr='flash', sfx=[]),
           dict(desde=12, fn=s_despierto, tr='golpe', sfx=[]),
           dict(desde=13, fn=s_manda1, tr='deslizar', sfx=[]),
           dict(desde=14, fn=s_como, tr='giro', sfx=[]),
           dict(desde=15, fn=s_borra, tr='wipe', sfx=[]),
           dict(desde=16, fn=s_paladar, tr='push', c=(0.5, 0.45), sfx=[]),
           dict(desde=17, fn=s_parpado, tr='deslizar_abajo', sfx=[]),
           dict(desde=18, fn=s_curva, tr='whip', sfx=[]),
           dict(desde=19, fn=s_apagon, tr='golpe', sfx=[]),
           dict(desde=20, fn=s_pantalla, tr='glitch', sfx=[]),
           dict(desde=21, fn=s_medias, tr='iris', c=(0.5, 0.4), sfx=[]),
           dict(desde=22, fn=s_papel, tr='deslizar', sfx=[]),
           dict(desde=23, fn=s_cansado, tr='flash', sfx=[]),
           dict(desde=24, fn=s_20min, tr='golpe', sfx=[]),
           dict(desde=25, fn=s_lejos, tr='zoom', c=(0.5, 0.42), sfx=[]),
           dict(desde=26, fn=s_manda2, tr='giro', sfx=[]),
           dict(desde=27, fn=s_quince, tr='ritmo', sfx=[]),
           dict(desde=28, loop=True, tr='whip')]


def _sfx_dinamicos():
    E = ESCENAS
    ua = 0.80
    E[0]['sfx'] = [(-0.1, 'whoosh_suave', 0.6), (ua, 'click', 0.8), (ua + 0.12, 'sub', 1.0), (ua + 0.12, 'bass', 0.9),
                   (1.3, 'tick', 0.5), (1.45, 'shimmer', 0.5)]
    ub = wt(1, 3) - TT(1)
    E[1]['sfx'] = [(0.1, 'scribble', 0.6), (0.2, 'tick', 0.5), (ub, 'click', 0.8)]
    ud = wt(2, 4) - TT(2)
    E[2]['sfx'] = [(0.15, 'thud', 0.8), (ud, 'bass', 0.9), (ud + 0.1, 'tick2', 0.6)] + [(ud + 0.08 * i, 'tick', 0.3) for i in range(1, 6)]
    E[3]['sfx'] = [(0.02 * i, 'tick2', 0.2) for i in range(0, 35, 3)] + [(0.1 + 0.12 * i, 'tick', 0.3) for i in range(12)] + [(1.8, 'chime_c', 0.5)]
    E[4]['sfx'] = [(0.1, 'thud', 0.7), (0.15, 'shimmer', 0.5)]
    E[5]['sfx'] = [(0.05, 'burst', 0.6), (0.15, 'click', 0.9), (0.4, 'bass', 1.0), (0.4, 'scribble', 0.6)]
    E[6]['sfx'] = [(0.0, 'whoosh', 0.5), (0.25, 'chime_a', 0.5), (0.35, 'chime_b', 0.5), (0.65, 'bass', 0.9)]
    E[7]['sfx'] = [(0.0, 'shimmer', 0.6), (0.3, 'scribble', 0.3), (0.7, 'chime_c', 0.5)]
    E[8]['sfx'] = [(0.0, 'whoosh', 0.5), (1.6, 'whoosh', 0.4), (1.5, 'tick', 0.5)]
    E[9]['sfx'] = [(0.0, 'whoosh', 0.6), (0.3, 'click', 0.8), (0.6, 'tick', 0.5)]
    E[10]['sfx'] = [(0.25, 'click', 1.0), (0.5, 'click', 0.9), (1.1, 'click', 0.9), (0.35, 'tick', 0.5)]
    u30 = wt(11, 4) - TT(11)
    E[11]['sfx'] = [(-0.1, 'riser', 0.6), (u30, 'sub', 1.0), (u30, 'bass', 1.0), (u30 + 0.15, 'burst', 0.5)] + \
        [(u30 + 0.1 * i, 'tick', 0.3) for i in range(6)] + [(u30 + 0.7, 'chime_c', 0.5)]
    E[12]['sfx'] = [(0.0 + 0.05 * i, 'tick2', 0.15) for i in range(12)] + [(0.7, 'whoosh', 0.6), (1.4, 'thud', 0.8), (1.45, 'scribble', 0.5)]
    E[13]['sfx'] = [(0.0, 'tick', 0.5), (1.0, 'click', 0.9), (1.05, 'chime_b', 0.6)]
    E[14]['sfx'] = [(0.0, 'shimmer', 0.6), (0.2, 'whoosh', 0.5)]
    ur, ub2 = wt(15, 3) - TT(15), wt(15, 6) - TT(15)
    E[15]['sfx'] = [(ur, 'scribble', 0.6), (ub2, 'whoosh', 0.6), (ub2 + 0.15, 'bass', 0.9)]
    up = wt(16, 7) - TT(16)
    E[16]['sfx'] = [(0.1, 'tick', 0.5), (up - 0.3, 'riser', 0.5), (up + 0.5, 'shimmer', 0.6), (up, 'tick2', 0.5)]
    E[17]['sfx'] = [(0.1, 'whoosh', 0.5), (0.5, 'thud', 0.7), (0.6, 'chime_a', 0.5)]
    ub3 = wt(18, 5) - TT(18)
    E[18]['sfx'] = [(0.2, 'tick', 0.4), (ub3, 'thud', 0.7), (ub3 + 0.3, 'scribble', 0.6)]
    us = wt(19, 2) - TT(19)
    E[19]['sfx'] = [(0.0, 'shimmer', 0.4), (us, 'click', 1.0), (us + 0.02, 'sub', 0.9)]
    E[20]['sfx'] = [(0.1, 'burst', 0.6), (0.25, 'bass', 1.0)]
    um = wt(21, 7) - TT(21)
    E[21]['sfx'] = [(0.0, 'bass', 0.7), (um - 0.1, 'scribble', 0.7), (um, 'thud', 0.8)]
    E[22]['sfx'] = [(-0.1, 'whoosh', 0.4), (0.15, 'chime_a', 0.6), (0.45, 'chime_c', 0.7)]
    E[23]['sfx'] = [(0.3, 'tick', 0.5), (0.35, 'thud', 0.5)]
    E[24]['sfx'] = [(0.06 * i, 'tick', 0.3) for i in range(10)] + [(0.6, 'bass', 1.0), (0.62, 'tick2', 0.6)]
    us2 = wt(25, 3) - TT(25)
    E[25]['sfx'] = [(0.0, 'whoosh_suave', 0.6), (0.4, 'thud', 0.5)] + [(us2 + 0.07 * i, 'tick', 0.25) for i in range(20)]
    ue = wt(26, 3) - TT(26)
    E[26]['sfx'] = [(-0.1, 'whoosh', 0.6), (0.4, 'thud', 0.6), (ue, 'click', 0.9), (ue + 0.05, 'chime_b', 0.6)]
    E[27]['sfx'] = [(-0.1 + 0.07 * i, 'tick2', 0.35) for i in range(15)]
    E[28]['sfx'] = [(0.0, 'shimmer', 0.4), (0.3, 'tick', 0.4), (0.9, 'whoosh_suave', 0.5)]


_frame_orig = montaje.frame_at


def _frame_portada(t, fi, caps=True):
    """La portada (y cuadro 0) sale del ojo abierto (u = 0.6), no del macro del iris."""
    if not caps and t == 0.1 and fi == 2:
        t, fi = 0.85, 20
    return _frame_orig(t, fi, caps)


montaje.frame_at = _frame_portada

if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_ and len(T_) == len(TXT) and sys.argv[1] != 'tiempos':
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
