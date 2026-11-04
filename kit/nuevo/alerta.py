"""Reel: «Tembló 7.4… y tu alerta no sonó.» (alerta sísmica SASMEX). Mié 4-nov-2026, 19:00. Voz Isaac.
Datos (fuentes en guiones/2026-11-04_alerta_sismica.txt): SASMEX no se activa por magnitud fija, estima la energía de los
primeros segundos y la distancia a cada ciudad; 17-jul-2026, 7.4 frente a Chiapas: «no ameritó aviso de alerta»; no hay
sensores en Chiapas, se detectó al llegar a Oaxaca; 96 sensores; >5.0 a menos de 170 km de la CDMX sí activa (N+);
alertas a celulares por difusión celular (no usan datos ni saldo); si se desactivan en el celular no llegan."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import (Frame, Cam, cam_path, space, draw_objects, finish, title, kicker, pill, glass_type, doodle_circle,
                    doodle_arrow, rec_frame, chart_grow, photo_card, scale_about, line3, dot3, named, seg, ease, eout,
                    clamp, lerp, CYAN, RED, WHITE)

S = M.SS
M3 = M.M3
TEMA = 'alerta'
TXT = ['Tembló 7.4… y tu alerta no sonó.',
       'No está descompuesta: la alerta sísmica no se fija en la magnitud.',
       'Calcula cuánto va a sacudir a cada ciudad, en los primeros segundos.',
       'Mira dos casos. 17 de julio: un 7.4 frente a Chiapas. No sonó.',
       'Pero uno de más de 5, a menos de 170 km de la capital, sí la activa.',
       'La diferencia: 96 sensores vigilan el Pacífico, de Jalisco a Oaxaca.',
       'En Chiapas no hay ni uno: ese sismo lo detectaron hasta que llegó a Oaxaca.',
       'Y su energía de los primeros segundos no alcanzó el nivel de alerta.',
       'Pero el error más común… está en tu bolsillo.',
       'Si apagaste las alertas de emergencia de tu celular, aunque suene la calle, a ti no te llega.',
       'En Android se llaman «Alertas de emergencia inalámbricas»; en iPhone, «Alertas gubernamentales».',
       'No gastan datos ni saldo: llegan por la antena.',
       'Y si el sismo nace cerca, no da tiempo: la alerta puede sonar cuando ya está temblando.',
       'Mándaselo a quien dice que la alerta está descompuesta,',
       'y revisa tu celular hoy, antes de que vuelva a temblar.']
VOZ = ['Tembló siete punto cuatro… y tu alerta no sonó.',
       TXT[1], TXT[2],
       'Mira dos casos. Diecisiete de julio: un siete punto cuatro frente a Chiapas. No sonó.',
       'Pero uno de más de cinco, a menos de ciento setenta kilómetros de la capital, sí la activa.',
       'La diferencia: noventa y seis sensores vigilan el Pacífico, de Jalisco a Oaxaca.',
       TXT[6], TXT[7], TXT[8], TXT[9],
       'En Android se llaman alertas de emergencia inalámbricas; en iPhone, alertas gubernamentales.',
       TXT[11], TXT[12], TXT[13], TXT[14]]
AMBAR = (255, 190, 70)
VERDE = (110, 240, 160)
AMAR = (255, 236, 160)


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


def wt(i, k):
    n = len(TXT[i].split())
    return TT(i) + (TE(i) - TT(i)) * k / n


def temblor(t, amp):
    """Desplazamientos de cámara de un sismo (yaw, pitch, roll)."""
    return (amp * (math.sin(t * 37) + 0.6 * math.sin(t * 23 + 1)), amp * 0.6 * math.sin(t * 41 + 2),
            amp * 0.8 * math.sin(t * 29 + 0.5))


def cam_temblor(u, keys, t, amp):
    c = cam_path(u, keys)
    if amp <= 0.001:
        return c
    dy, dp, dr = temblor(t, amp)
    kk = [k for k in keys if k[0] <= u] or [keys[0]]
    b = dict(kk[-1][1])
    # reconstruye la cámara interpolada con sacudida
    k2 = keys
    if u <= k2[0][0]:
        base = dict(k2[0][1])
    elif u >= k2[-1][0]:
        base = dict(k2[-1][1])
    else:
        for (ta, a), (tb, bb) in zip(k2[:-1], k2[1:]):
            if ta <= u <= tb:
                kx = ease((u - ta) / max(1e-6, tb - ta))
                base = {}
                for key in a:
                    va, vb = a[key], bb.get(key, a[key])
                    base[key] = tuple(lerp(x, y, kx) for x, y in zip(va, vb)) if isinstance(va, (tuple, list)) else lerp(va, vb, kx)
                break
    base['yaw'] = base.get('yaw', 0) + dy
    base['pitch'] = base.get('pitch', 10) + dp
    base['roll'] = base.get('roll', 0) + dr
    return Cam(**base)


# ------------------------------------------------------------------ objetos
def altavoz(sonando=0.0):
    """Poste de la alerta sísmica con 4 bocinas de trompeta (metal satinado gris) y caja de control."""
    met = (150, 154, 160)
    out = [named(M3.cyl(0.05, 2.6, (120, 124, 130), n=20, shadow=0, gloss=0.5, y0=0), 'poste', rim=0.6, gloss=0.5),
           named(M3.rbox(0.36, 0.5, 0.22, 0.03, (190, 192, 196), n=3, shadow=0, gloss=0.4).tf(t=(0, 1.05, 0.1)), 'caja', rim=0.5),
           named(M3.box(0.2, 0.06, 0.02, (60, 200, 120) if sonando > 0.5 else (60, 64, 70), shadow=0, base=True, gloss=0.6)
                 .tf(t=(0, 1.4, 0.215)), 'led', rim=0.2)]
    for ang in (0, 90, 180, 270):
        h = M3.cyl(0.06, 0.55, met, n=28, shadow=0, gloss=0.65, r2=0.24, y0=0.0, top=(18, 18, 20))
        h = named(h.tf(rz=-90).tf(rx=8).tf(ry=ang + 45, t=(0, 2.35, 0)), 'bocina', rim=0.7, gloss=0.65)
        out.append(h)
        dr = named(M3.cyl(0.11, 0.16, (70, 72, 78), n=20, shadow=0, gloss=0.5, y0=-0.16).tf(rz=-90).tf(ry=ang + 45, t=(0, 2.35, 0)),
                   'bocina', rim=0.5)
        out.append(dr)
    out.append(named(M3.sphere(0.07, (140, 144, 150), nu=20, nv=10, shadow=0, gloss=0.6).tf(t=(0, 2.62, 0)), 'poste', rim=0.5))
    return out


def ondas_sonido(fr, t, k, col=WHITE, centro=(0, 2.35, 0), dirs=(45, 135, 225, 315), n=3, vel=0.9):
    if k <= 0.01:
        return
    c = np.array(centro, float)
    for ang in dirs:
        a = math.radians(ang)
        dv = np.array([math.cos(a), 0, -math.sin(a)])
        side = np.array([-dv[2], 0, dv[0]])
        for j in range(n):
            s = (t * vel + j / n) % 1.0
            r = 0.55 + 1.3 * s
            pts = [c + dv * r * math.cos(b) + side * r * math.sin(b) + np.array([0, 0.25 * math.sin(b * 2) * 0, 0])
                   for b in np.linspace(-0.45, 0.45, 14)]
            line3(fr, pts, col=col, w=3, a=k * (1 - s), glow=1.0)


def estacion(xray=0.0):
    """Estación sismosensora: base de concreto, gabinete, mástil con panel solar y antena."""
    out = [named(M3.rbox(1.3, 0.14, 1.1, 0.04, (146, 144, 138), n=3, shadow=0, gloss=0.1), 'base', rim=0.4, gloss=0.1),
           named(M3.rbox(0.5, 0.7, 0.36, 0.03, (206, 208, 212), n=3, shadow=0, gloss=0.45).tf(t=(-0.15, 0.14, 0.05)), 'gab',
                 rim=0.6, gloss=0.45),
           named(M3.cyl(0.035, 1.9, (150, 152, 158), n=16, shadow=0, gloss=0.6, y0=0).tf(t=(0.4, 0.14, -0.25)), 'mast', rim=0.6),
           named(M3.box(0.75, 0.03, 0.5, (26, 38, 82), shadow=0, base=True, gloss=0.9).tf(rx=-35).tf(t=(0.4, 1.55, -0.2)), 'panel',
                 rim=0.5, gloss=0.9),
           named(M3.cyl(0.012, 0.6, (220, 220, 225), n=8, shadow=0, gloss=0.4, y0=0).tf(t=(0.4, 2.0, -0.25)), 'ant', rim=0.4)]
    sen = named(M3.box(0.22, 0.12, 0.2, (40, 120, 90), shadow=0, base=True, gloss=0.5).tf(t=(-0.15, 0.18, 0.05)), 'in', rim=0.4)
    sen2 = named(M3.cyl(0.05, 0.1, (214, 172, 82), n=16, shadow=0, gloss=0.9, y0=0).tf(t=(-0.15, 0.3, 0.05)), 'in', rim=0.3)
    if xray > 0.5:
        sen.glow = M.scale_c(VERDE, 0.4)
    return out + [sen, sen2]


def antena():
    col = (200, 202, 206)
    out = [named(M3.cyl(0.06, 3.0, (170, 172, 178), n=18, shadow=0, gloss=0.5, y0=0, r2=0.035), 'mast', rim=0.6)]
    for ang in (0, 120, 240):
        a = math.radians(ang)
        out.append(named(M3.box(0.14, 0.55, 0.05, col, shadow=0, base=True, gloss=0.4)
                         .tf(ry=ang, t=(0.12 * math.sin(a), 2.55, 0.12 * math.cos(a))), 'panel', rim=0.6))
    out.append(named(M3.cyl(0.13, 0.03, (190, 190, 196), n=20, shadow=0, gloss=0.5).tf(rx=90).tf(t=(0, 2.2, 0.12)), 'disco', rim=0.5))
    return out


# ------------------------------------------------------------------ mapa (esquema, escala aproximada)
KM = 0.2  # unidades por grado


def geo(lat, lon):
    return np.array([(lon + 99.0) * KM, 0.004, -(lat - 17.0) * KM])


COSTA = [(21.6, -105.3), (20.65, -105.25), (20.4, -105.7), (19.9, -105.4), (19.4, -105.0), (19.1, -104.4), (18.7, -103.7),
         (18.2, -102.9), (17.95, -102.2), (17.6, -101.55), (17.25, -101.0), (17.0, -100.3), (16.85, -99.9), (16.55, -99.0),
         (16.2, -98.1), (15.86, -97.07), (15.67, -96.5), (15.75, -96.1), (16.17, -95.2), (16.2, -94.6), (15.8, -93.9),
         (15.3, -93.2), (14.7, -92.4), (14.53, -92.22)]
COSTA_P = [geo(a, b) for a, b in COSTA]
CIUDADES = {'CDMX': (19.43, -99.13), 'OAXACA': (17.06, -96.72), 'ACAPULCO': (16.85, -99.9), 'PUEBLA': (19.04, -98.2),
            'GUADALAJARA': (20.67, -103.35), 'CHILPANCINGO': (17.55, -99.5), 'TUXTLA': (16.75, -93.12)}
EPI1 = (14.2, -92.95)   # frente a la costa de Chiapas (ubicación aproximada)
EPI2 = (18.45, -98.75)  # ejemplo: a menos de 170 km de la CDMX
EPI3 = (19.2, -99.0)    # ejemplo: sismo cercano


def _sensores():
    rng = np.random.RandomState(4)
    seg_ = [(a, b) for a, b in zip(COSTA[:-1], COSTA[1:]) if b[1] < -94.4]
    L = np.array([math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in seg_])
    cum = np.concatenate([[0], np.cumsum(L)])
    out = []
    for i in range(88):
        d = (i + rng.uniform(0.1, 0.9)) / 88 * cum[-1]
        j = min(len(seg_) - 1, int(np.searchsorted(cum, d) - 1))
        f = (d - cum[j]) / L[j]
        lat = seg_[j][0][0] + (seg_[j][1][0] - seg_[j][0][0]) * f + rng.uniform(0.06, 0.55)
        lon = seg_[j][0][1] + (seg_[j][1][1] - seg_[j][0][1]) * f + rng.uniform(-0.1, 0.1)
        out.append((lat, lon))
    for _ in range(8):  # algunos tierra adentro (Puebla, Oaxaca)
        out.append((rng.uniform(17.3, 18.9), rng.uniform(-98.6, -96.6)))
    order = np.argsort([-o[1] for o in out])[::-1]  # de oeste a este
    return [out[i] for i in order]


SENS = _sensores()
SENS_P = [geo(a, b) for a, b in SENS]


def circulo(c, r, n=64, y=0.006):
    return [c + np.array([r * math.cos(a), y, r * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, n)]


def mapa(fr, t, k=1.0, sensores=0, ciudades=('CDMX',), resalta=None, sens_on=None):
    if k <= 0.01:
        return
    line3(fr, COSTA_P, col=(200, 205, 215), w=2.4, a=0.85 * k, glow=0.5)
    # mar: líneas paralelas tenues a la costa
    for j in (1, 2, 3):
        off = np.array([0, 0, 0.06 * j])
        line3(fr, [p + off for p in COSTA_P], col=(90, 110, 130), w=1.0, a=0.35 * k / j, glow=0.1)
    n = int(sensores)
    for i, p in enumerate(SENS_P[:n]):
        on = sens_on(i) if sens_on else 0.0
        dot3(fr, p, r=3.0 + 2.5 * on, col=M.mixc(CYAN, WHITE, on), a=k, glow=0.9 + on)
    for nombre in ciudades:
        c = geo(*CIUDADES[nombre])
        dot3(fr, c, r=6, col=AMAR if nombre == resalta else WHITE, a=k, glow=1.2)


def anillos(fr, t, c, t0, k=1.0, col=WHITE, vel=0.5, n=3, rmax=2.5):
    if k <= 0.01 or t < t0:
        return
    for j in range(n):
        r = (t - t0) * vel - j * 0.25
        if 0.02 < r < rmax:
            line3(fr, circulo(c, r, 72), col=col, w=2.2, a=k * (1 - r / rmax), glow=0.9)


def etiqueta(img, fx, fr, p, txt, k, col=WHITE, dy=-44, size=26):
    if k <= 0.01:
        return
    x, y, z = fr.cam.p1(p)
    if z < 0.2:
        return
    d = ImageDraw.Draw(img)
    d.text((x, y + dy), txt, font=M.font('mono', size), fill=M.scale_c(col, k), anchor='mm')


# ------------------------------------------------------------------ pantallas del celular
def scr_alerta(brillo=1.0, on=True):
    def dib(d, im):
        if not on:
            d.text((210, 420), 'Sin alertas', font=M.font('sanss', 30), fill=(90, 92, 98), anchor='mm')
            return
        c = M.scale_c((255, 60, 50), 0.55 + 0.45 * brillo)
        d.rounded_rectangle((24, 120, 396, 520), radius=26, fill=(36, 10, 10), outline=c, width=4)
        d.text((52, 160), '⚠  ALERTA DE', font=M.font('sans', 36), fill=c)
        d.text((52, 206), 'EMERGENCIA', font=M.font('sans', 36), fill=c)
        d.text((52, 280), 'Alerta sísmica.', font=M.font('sanss', 30), fill=(240, 240, 240))
        d.text((52, 324), 'Busca una zona segura.', font=M.font('sanss', 26), fill=(210, 210, 214))
        d.text((52, 450), 'Ahora', font=M.font('mono', 22), fill=(160, 160, 166))
    return P.pantalla(dib)


def _toggle(d, x, y, on):
    on = clamp(on)
    col = M.mixc((70, 72, 78), CYAN, on)
    d.rounded_rectangle((x, y, x + 74, y + 40), radius=20, fill=col)
    cx = lerp(x + 20, x + 54, ease(on))
    d.ellipse((cx - 16, y + 4, cx + 16, y + 36), fill=(245, 245, 248))


def scr_ajustes(sistema='android', on=0.0):
    def dib(d, im):
        d.text((32, 96), 'Notificaciones', font=M.font('sans', 36), fill=(240, 240, 242))
        d.text((32, 146), 'ANDROID' if sistema == 'android' else 'IPHONE', font=M.font('mono', 20), fill=(130, 132, 140))
        y = 210
        filas = (['Pantalla de bloqueo', 'Ajustes avanzados'] if sistema == 'android' else ['Vista previa', 'Siri'])
        for f in filas:
            d.text((32, y), f, font=M.font('sanss', 26), fill=(170, 172, 178))
            y += 70
        d.line([(32, y - 14), (388, y - 14)], fill=(50, 52, 58), width=2)
        if sistema == 'android':
            d.text((32, y + 10), 'Alertas de emergencia', font=M.font('sanss', 27), fill=(245, 245, 248))
            d.text((32, y + 46), 'inalámbricas', font=M.font('sanss', 27), fill=(245, 245, 248))
        else:
            d.text((32, y + 10), 'ALERTAS GUBERNAMENTALES', font=M.font('mono', 18), fill=(150, 152, 160))
            d.text((32, y + 46), 'Alertas de emergencia', font=M.font('sanss', 27), fill=(245, 245, 248))
        _toggle(d, 318, y + 30, on)
        d.text((32, y + 130), 'Alerta sísmica', font=M.font('sanss', 24), fill=(150, 152, 160))
        _toggle(d, 318, y + 122, on)
    return P.pantalla(dib)


# ------------------------------------------------------------------ escenas
K0 = [(-4.6, dict(target=(0, 1.9, 0), dist=5.2, yaw=55, pitch=4, cy=0.5)),
      (-0.9, dict(target=(0, 2.0, 0), dist=4.0, yaw=28, pitch=-4, cy=0.5)),
      (0.0, dict(target=(0, 2.05, 0), dist=3.7, yaw=22, pitch=-6, cy=0.5)),
      (8.0, dict(target=(0, 2.1, 0), dist=3.2, yaw=6, pitch=-8, cy=0.5))]


def s_gancho(t, fi, u, d, titulo=True):
    amp = 0.9 * (0.6 + 0.4 * math.sin(t * 3)) if titulo else 0.4
    fr = Frame(cam_temblor(u, K0, t, amp))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    x, y = fr.cam.proj([(0, 0.02, 0)])[0][0]
    D.shadow_blob(fr, x, y, 300, 70, 0.8)
    glass_type(fr.base, fr.fx, '7.4' if titulo else 'SÍSMICA', 540 * S, 1150 * S, (330 if titulo else 190) * S,
               k=ease(seg(u, -0.6, 0.4)), fill_a=0.06)
    draw_objects(fr, altavoz())
    ondas_sonido(fr, t, 0.25, col=(120, 122, 130))
    tc = fr.cam.p1(np.array([0, 2.35, 0]))

    def ui(img, fx):
        if titulo:
            kicker(img, 'SASMEX · ALERTA SÍSMICA', 132, seg(u, 0.55, 0.95))
            title(img, fx, [('Tembló 7.4…', 'sans'), ('y tu alerta no sonó.', 'serif')], 190, seg(u, 0.15, 0.75), size=80)
            ta = wt(0, 4) - TT(0)
            doodle_circle(img, fx, tc[0], tc[1], 250, 150, t, k=eout(seg(u, ta - 0.3, ta + 0.2)), col=RED, w=6)
            pill(img, fx, 540, 1400, 'SILENCIO', eout(seg(u, ta, ta + 0.3)), size=34, border=RED)
        else:
            title(img, fx, [('Mándaselo a quien dice', 'sans'), ('que está descompuesta.', 'serif')], 190, seg(u, 0.0, 0.5), size=70)
            pill(img, fx, 540, 1400, 'NO ESTÁ DESCOMPUESTA', eout(seg(u, 0.6, 0.9)), size=32, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_mandalo(t, fi, u, d):
    return s_gancho(t, fi, u + 3.0, d, titulo=False)


def sismograma(img, fx, x0, y0, w, h, t, t0, k=1.0, primeros=0.0, umbral=None):
    """Sismograma 2D que se dibuja de izquierda a derecha; 'primeros' resalta los primeros segundos en cian."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    rng = np.random.RandomState(3)
    n = 220
    xs = np.linspace(0, 1, n)
    env = np.where(xs < 0.18, 0.12 + 0.3 * xs / 0.18, np.where(xs < 0.35, 0.25 + 0.75 * (xs - 0.18) / 0.17, np.exp(-(xs - 0.35) * 3.5)))
    ys = env * np.sin(xs * 160 + rng.rand(n) * 2) * (0.6 + 0.4 * rng.rand(n))
    m = int(n * clamp((t - t0) / 2.0))
    pts = [(x0 + w * xs[i], y0 + h / 2 - ys[i] * h * 0.45) for i in range(m)]
    if len(pts) > 1:
        d.line(pts, fill=M.scale_c(WHITE, 0.85 * k), width=3)
        df.line(pts, fill=M.scale_c(WHITE, 0.3 * k), width=6)
    if primeros > 0.01:
        a = int(0.2 * n)
        p2 = pts[:a]
        if len(p2) > 1:
            d.line(p2, fill=M.scale_c(CYAN, primeros), width=5)
            df.line(p2, fill=M.scale_c(CYAN, 0.7 * primeros), width=10)
        xb = x0 + w * 0.2
        d.line([(x0, y0 - 20), (x0, y0 - 34), (xb, y0 - 34), (xb, y0 - 20)], fill=M.scale_c(CYAN, primeros), width=3)
        d.text(((x0 + xb) / 2, y0 - 62), 'PRIMEROS SEGUNDOS', font=M.font('mono', 22), fill=M.scale_c(CYAN, primeros), anchor='mm')
    d.line([(x0, y0 + h / 2), (x0 + w, y0 + h / 2)], fill=M.scale_c((90, 92, 100), k), width=1)


def s_magnitud(t, fi, u, d):
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0, 0.9, 0), dist=5.2, yaw=-30, pitch=6, cy=0.62)),
                            (5.0, dict(target=(0, 0.9, 0), dist=4.4, yaw=-10, pitch=8, cy=0.62))]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    draw_objects(fr, P.tfk(altavoz(), s=0.6, t=(0, 0, 0)))
    tm = wt(1, 11) - TT(1)

    def ui(img, fx):
        kicker(img, 'NO ESTÁ DESCOMPUESTA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        sismograma(img, fx, 90, 330, 900, 300, t, TT(1) + 0.2, k=eout(seg(u, 0.0, 0.4)))
        v = 7.4 * eout(seg(u, 0.3, 1.6))
        ImageDraw.Draw(img).text((540, 760), f'M {v:.1f}', font=M.font('mono', 96), fill=M.scale_c(WHITE, eout(seg(u, 0.3, 0.6))), anchor='mm')
        P.pill_tachada(img, fx, 540, 1380, 'DECIDE POR LA MAGNITUD', seg(u, tm - 1.2, tm - 0.8), seg(u, tm - 0.2, tm + 0.2), t, size=32)
    fr.ui.append(ui)
    return finish(fr, fi)


KMAP = [(-0.4, dict(target=(-0.1, 0, -0.1), dist=2.6, yaw=0, pitch=72, cy=0.55, roll=60)),
        (6.0, dict(target=(-0.05, 0, -0.15), dist=2.2, yaw=6, pitch=70, cy=0.55, roll=55))]


def s_ciudades(t, fi, u, d):
    fr = Frame(cam_path(u, KMAP))
    space(fr, t, floor='dots', floor_a=0.35, bokeh=0.6)
    noms = ('CDMX', 'PUEBLA', 'OAXACA', 'ACAPULCO', 'GUADALAJARA', 'CHILPANCINGO')
    mapa(fr, t, k=eout(seg(u, 0.0, 0.5)), ciudades=noms)
    epi = geo(16.4, -98.6)
    anillos(fr, t, epi, TT(2) + 0.3, k=1.0, col=WHITE, vel=0.6)
    pos = {n: geo(*CIUDADES[n]) for n in noms}

    def ui(img, fx):
        kicker(img, 'CALCULA CIUDAD POR CIUDAD', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        for j, n in enumerate(noms):
            kj = eout(seg(u, 0.5 + 0.25 * j, 0.8 + 0.25 * j))
            etiqueta(img, fx, fr, pos[n], n, kj, size=22)
            x, y, z = fr.cam.p1(pos[n])
            dist = np.linalg.norm(pos[n] - epi)
            lvl = clamp(1.2 - dist * 0.9)
            hh = 90 * lvl * kj
            dd = ImageDraw.Draw(img)
            dd.rectangle((x + 16, y - hh, x + 30, y), fill=M.scale_c(M.mixc(CYAN, RED, lvl), kj))
        sismograma(img, fx, 140, 300, 800, 200, t, TT(2) + 0.1, k=eout(seg(u, 0.0, 0.3)),
                   primeros=eout(seg(t, wt(2, 9), wt(2, 10))))
    fr.ui.append(ui)
    return finish(fr, fi)


K3 = [(-0.4, dict(target=(0.6, 0, 0.05), dist=2.9, yaw=-6, pitch=72, cy=0.47, roll=40)),
      (7.0, dict(target=(0.65, 0, 0.1), dist=2.5, yaw=-12, pitch=70, cy=0.47, roll=36))]
_TARJ = {}


def tarjeta():
    if 'a' not in _TARJ:
        im = Image.new('RGB', (620, 300), (246, 245, 240))
        d = ImageDraw.Draw(im)
        d.text((30, 26), 'SASMEX · 17 JUL 2026 · 08:49:38', font=M.font('mono', 24), fill=(90, 90, 96))
        d.text((30, 90), '«…no ameritó aviso', font=M.font('serif', 46), fill=(20, 20, 24))
        d.text((30, 150), 'de alerta»', font=M.font('serif', 46), fill=(20, 20, 24))
        d.text((30, 236), 'Comunicado del sistema (cita)', font=M.font('mono', 20), fill=(120, 120, 126))
        _TARJ['a'] = im
    return _TARJ['a']


def s_caso1(t, fi, u, d):
    fr = Frame(cam_path(u, K3))
    space(fr, t, floor='dots', floor_a=0.3, bokeh=0.6)
    mapa(fr, t, k=1.0, ciudades=('CDMX', 'TUXTLA'), resalta='CDMX')
    e1 = geo(*EPI1)
    tc = wt(3, 6)
    anillos(fr, t, e1, tc, k=1.0, col=(255, 120, 100), vel=0.45, n=4, rmax=2.2)
    cd = geo(*CIUDADES['CDMX'])
    kl = eout(seg(t, tc + 0.6, tc + 1.4))
    if kl > 0.01:
        line3(fr, [e1 + (cd - e1) * s for s in np.linspace(0, kl, 30)], col=AMAR, w=2.5, a=0.9, glow=0.8)

    def ui(img, fx):
        kicker(img, 'CASO 1 · 17 DE JULIO DE 2026', 150, seg(u, 0.0, 0.3), col=(255, 160, 140))
        etiqueta(img, fx, fr, e1, 'EPICENTRO · 7.4', eout(seg(t, tc, tc + 0.3)), col=(255, 140, 120), dy=50)
        etiqueta(img, fx, fr, cd, 'CDMX', 1.0, col=AMAR)
        mid = fr.cam.p1((e1 + cd) / 2)
        if kl > 0.9:
            pill(img, fx, mid[0] - 40, mid[1] - 60, '+800 KM', eout(seg(t, tc + 1.3, tc + 1.6)), size=26, border=AMAR, dot=False)
        pill(img, fx, 540, 1330, 'NO SONÓ', eout(seg(t, wt(3, 11), wt(3, 12))), size=40, border=RED)
        photo_card(img, fx, tarjeta(), 540, 470, 560, wt(3, 10) - 0.1, t, angle0=-8)
    fr.ui.append(ui)
    return finish(fr, fi)


K4 = [(-0.4, dict(target=(0.0, 0, -0.35), dist=1.7, yaw=12, pitch=70, cy=0.55)),
      (6.0, dict(target=(0.0, 0, -0.35), dist=1.4, yaw=-4, pitch=74, cy=0.55))]


def s_caso2(t, fi, u, d):
    fr = Frame(cam_path(u, K4))
    space(fr, t, floor='dots', floor_a=0.3, bokeh=0.6)
    mapa(fr, t, k=1.0, ciudades=('CDMX', 'PUEBLA'), resalta='CDMX')
    cd = geo(*CIUDADES['CDMX'])
    kr = eout(seg(u, 0.2, 1.2))
    R = 1.53 * KM
    line3(fr, circulo(cd, R, 80)[:max(2, int(80 * kr))], col=CYAN, w=2.4, a=0.9, glow=0.9)
    e2 = geo(*EPI2)
    te = wt(4, 4)
    anillos(fr, t, e2, te, k=1.0, col=(255, 200, 120), vel=0.35, n=4, rmax=1.0)
    ks = eout(seg(t, wt(4, 13), wt(4, 14)))
    if ks > 0.01:
        ondas_sonido(fr, t, ks, col=VERDE, centro=tuple(cd + np.array([0, 0.02, 0])), vel=1.4, n=3)

    def ui(img, fx):
        kicker(img, 'CASO 2 · CERCA DE LA CAPITAL', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        etiqueta(img, fx, fr, cd, 'CDMX', 1.0, col=AMAR)
        etiqueta(img, fx, fr, e2, 'MÁS DE 5', eout(seg(t, te, te + 0.3)), col=(255, 200, 120), dy=50)
        rp = fr.cam.p1(cd + np.array([R, 0, 0]))
        pill(img, fx, rp[0] + 20, rp[1] - 70, '170 KM', eout(seg(u, 1.0, 1.3)), size=26, border=CYAN, dot=False)
        pill(img, fx, 540, 1330, 'SÍ SUENA', ks, size=40, border=VERDE)
        pill(img, fx, 540, 300, 'UMBRALES PARA LA CDMX (N+)', eout(seg(u, 0.4, 0.7)), size=22, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


K5 = [(-0.4, dict(target=(-0.5, 0, -0.05), dist=2.0, yaw=-10, pitch=70, cy=0.55, roll=62)),
      (6.0, dict(target=(-0.2, 0, 0.0), dist=2.3, yaw=0, pitch=72, cy=0.55, roll=60))]


def s_sensores(t, fi, u, d):
    fr = Frame(cam_path(u, K5))
    space(fr, t, floor='dots', floor_a=0.3, bokeh=0.6)
    t0, t1 = wt(5, 2), wt(5, 6)
    n = 96 * eout(seg(t, t0, t1), 2)
    mapa(fr, t, k=1.0, sensores=n, ciudades=('CDMX', 'GUADALAJARA', 'OAXACA'),
         sens_on=lambda i: 0.6 + 0.4 * math.sin(t * 6 + i))

    def ui(img, fx):
        kicker(img, 'RED DE SENSORES · ESQUEMA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        ImageDraw.Draw(img).text((800, 330), f'{int(round(n)):d}', font=M.font('mono', 130), fill=M.scale_c(WHITE, eout(seg(t, t0 - 0.2, t0))), anchor='mm')
        ImageDraw.Draw(img).text((800, 430), 'SENSORES', font=M.font('mono', 30), fill=M.scale_c(CYAN, eout(seg(t, t0, t0 + 0.3))), anchor='mm')
        etiqueta(img, fx, fr, geo(20.6, -104.6), 'JALISCO', eout(seg(t, wt(5, 9), wt(5, 10))), col=AMAR)
        etiqueta(img, fx, fr, geo(16.7, -96.0), 'OAXACA', eout(seg(t, wt(5, 11), wt(5, 12))), col=AMAR)
        pill(img, fx, 540, 1330, 'UBICACIÓN APROXIMADA', eout(seg(u, 0.6, 0.9)), size=22, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


K6 = [(-0.4, dict(target=(0.95, 0, 0.3), dist=2.2, yaw=-4, pitch=70, cy=0.5, roll=50)),
      (6.0, dict(target=(1.0, 0, 0.3), dist=1.9, yaw=-10, pitch=72, cy=0.5, roll=46))]


def s_chiapas(t, fi, u, d):
    fr = Frame(cam_path(u, K6))
    space(fr, t, floor='dots', floor_a=0.3, bokeh=0.6)
    e1 = geo(*EPI1)
    tq = wt(6, 6)
    vel = 0.5
    rr = max(0.0, (t - tq) * vel)

    def on(i):
        dd = np.linalg.norm(SENS_P[i] - e1)
        return 1.0 if (rr > dd and t > tq) else 0.0
    mapa(fr, t, k=1.0, sensores=96, ciudades=('TUXTLA', 'OAXACA'), sens_on=on)
    anillos(fr, t, e1, tq, k=1.0, col=(255, 120, 100), vel=vel, n=3, rmax=2.0)
    ch = geo(15.9, -92.9)
    zoom = 1.0 if u < 1.2 else (1.3 if u < 2.4 else 1.8)
    pc = fr.cam.p1(ch)

    def ui(img, fx):
        kicker(img, 'CHIAPAS', 150, seg(u, 0.0, 0.3), col=(255, 160, 140))
        doodle_circle(img, fx, pc[0], pc[1], 200, 130, t, k=eout(seg(u, 0.2, 0.7)), col=RED, w=6)
        pill(img, fx, pc[0], pc[1] - 190, '0 SENSORES', eout(seg(u, 0.5, 0.8)), size=36, border=RED)
        oa = fr.cam.p1(geo(16.4, -95.3))
        doodle_arrow(img, fx, pc[0] - 60, pc[1] + 160, oa[0] + 30, oa[1] + 60, t, k=eout(seg(t, wt(6, 12), wt(6, 14))), col=AMAR, w=5)
        pill(img, fx, 540, 1330, 'LO DETECTAN EN OAXACA', eout(seg(t, wt(6, 13), wt(6, 15))), size=30, border=AMAR)
    fr.ui.append(ui)
    img = finish(fr, fi)
    if zoom > 1.0:
        img = scale_about(img, zoom, pc[0] / 1080, pc[1] / 1920)
    im = Image.fromarray(img)
    rec_frame(im, t, 1.0, f'x{zoom:.1f}')
    return np.asarray(im)


K7 = [(-0.4, dict(target=(0, 0.7, 0), dist=4.0, yaw=35, pitch=12, cy=0.58)),
      (5.0, dict(target=(0, 0.7, 0), dist=3.5, yaw=55, pitch=16, cy=0.58))]


def s_energia(t, fi, u, d):
    fr = Frame(cam_temblor(u, K7, t, 0.25))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    xr = seg(u, 0.2, 0.7)
    draw_objects(fr, estacion(xray=xr), xray=xr * 0.8, keep=('in',))
    tc = TT(7) + 0.5
    ue = fr.cam.p1(np.array([-0.15, 0.24, 0.05]))

    def ui(img, fx):
        kicker(img, 'ESTACIÓN SISMOSENSORA', 132, seg(u, 0.0, 0.3), col=(150, 210, 230))
        pill(img, fx, ue[0], ue[1] + 120, 'ACELERÓMETRO', eout(seg(u, 0.6, 0.9)), size=26, border=VERDE)
        box = (90, 230, 990, 830)
        chart_grow(img, fx, box, [22, 36, 48], ['1 s', '2 s', '3 s'], tc, t, title_txt='ENERGÍA ESTIMADA', vmax=80, line=False,
                   tag='EJEMPLO')
        kt = eout(seg(t, tc + 1.2, tc + 1.6))
        if kt > 0.01:
            dd = ImageDraw.Draw(img)
            yl = 230 + 150 + (830 - 120 - 380) * (1 - 70 / 80)
            for x in range(170, 910, 26):
                dd.line([(x, yl), (x + 14, yl)], fill=M.scale_c(RED, kt), width=4)
            dd.text((900, yl - 30), 'NIVEL DE ALERTA', font=M.font('mono', 24), fill=M.scale_c(RED, kt), anchor='rm')
    fr.ui.append(ui)
    return finish(fr, fi)


KB = [(-0.4, dict(target=(0, 0.95, 0), dist=4.2, yaw=-50, pitch=10, cy=0.56)),
      (4.0, dict(target=(0, 0.95, 0), dist=2.9, yaw=-14, pitch=4, cy=0.56))]


def s_bolsillo(t, fi, u, d):
    fr = Frame(cam_path(u, KB))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.6)
    x, y = fr.cam.proj([(0, 0.02, 0)])[0][0]
    D.shadow_blob(fr, x, y, 300, 60, 0.8)
    glass_type(fr.base, fr.fx, 'ERROR', 540 * S, 1100 * S, 240 * S, k=ease(seg(u, 0.0, 0.6)), fill_a=0.06)
    rot = 40 * (1 - eout(seg(u, 0.0, 1.2)))
    draw_objects(fr, P.celular(scr_alerta(on=False), ry=rot))

    def ui(img, fx):
        kicker(img, 'EL ERROR MÁS COMÚN', 132, seg(u, 0.1, 0.4), col=(255, 160, 140))
        title(img, fx, [('El error más común…', 'sans'), ('está en tu bolsillo.', 'serif')], 190, seg(u, 0.2, 0.8), size=74)
    fr.ui.append(ui)
    img = finish(fr, fi)
    a = 0.1 * eout(seg(u, 0.8, 1.6))
    o = img.astype(np.float32)
    o = o * (1 - a) + np.array([255, 50, 40], np.float32) * a * (o.mean(2, keepdims=True) / 255 + 0.2)
    return o.clip(0, 255).astype(np.uint8)


K9 = [(-0.4, dict(target=(0.2, 1.3, 0), dist=6.0, yaw=20, pitch=4, cy=0.55)),
      (6.0, dict(target=(0.2, 1.2, 0), dist=5.2, yaw=4, pitch=4, cy=0.55))]


def s_apagada(t, fi, u, d):
    fr = Frame(cam_path(u, K9))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.8)
    alt = P.tfk(altavoz(sonando=1.0), s=1.0, t=(-1.2, 0, -1.4))
    ph = P.tfk(P.celular(scr_ajustes('android', 0.0), ry=-12), s=1.15, t=(0.9, 0, 0.6))
    draw_objects(fr, alt + ph)
    ks = eout(seg(t, wt(9, 10), wt(9, 11)))
    ondas_sonido(fr, t, ks, col=AMBAR, centro=(-1.2, 2.35, -1.4), vel=1.3)
    pp = fr.cam.p1(np.array([0.9, 1.3, 0.6]))

    def ui(img, fx):
        kicker(img, 'ALERTAS DESACTIVADAS', 150, seg(u, 0.0, 0.3), col=(255, 160, 140))
        pill(img, fx, 540, 300, 'LA CALLE SUENA', ks, size=30, border=AMBAR)
        doodle_circle(img, fx, pp[0], pp[1], 240, 330, t, k=eout(seg(t, wt(9, 15), wt(9, 17))), col=RED, w=6)
        pill(img, fx, 540, 1330, 'A TI NO TE LLEGA', eout(seg(t, wt(9, 15), wt(9, 16))), size=36, border=RED)
    fr.ui.append(ui)
    return finish(fr, fi)


KA = [(-0.4, dict(target=(0, 0.95, 0), dist=2.5, yaw=-14, pitch=3, cy=0.5)),
      (6.0, dict(target=(0, 0.95, 0), dist=2.25, yaw=10, pitch=3, cy=0.5))]


def s_ajustes(t, fi, u, d):
    fr = Frame(cam_path(u, KA))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9)
    ti = wt(10, 7)
    ios = t >= ti
    if not ios:
        on = eout(seg(t, wt(10, 5), wt(10, 6)))
    else:
        on = eout(seg(t, ti + 0.5, ti + 0.9))
    flip = 1 - eout(seg(t, ti - 0.15, ti + 0.15))
    ry = 0 if not ios else 0
    draw_objects(fr, P.celular(scr_ajustes('iphone' if ios else 'android', on), ry=ry))
    uz = u if not ios else t - ti
    zoom = 1.0 if uz < 1.0 else (1.3 if uz < 2.0 else 1.6)
    tg = fr.cam.p1(np.array([0.22, 0.95, 0.05]))

    def ui(img, fx):
        kicker(img, 'IPHONE · AJUSTES' if ios else 'ANDROID · AJUSTES', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if not ios:
            pill(img, fx, 540, 1330, 'ACTÍVALAS', eout(seg(t, wt(10, 5), wt(10, 6))), size=32, border=CYAN)
        else:
            pill(img, fx, 540, 1330, 'ALERTAS GUBERNAMENTALES', eout(seg(t, ti + 0.2, ti + 0.5)), size=30, border=CYAN)
    fr.ui.append(ui)
    img = finish(fr, fi)
    if zoom > 1.0:
        img = scale_about(img, zoom, 0.5, tg[1] / 1920)
    im = Image.fromarray(img)
    rec_frame(im, t, 1.0, f'x{zoom:.1f}')
    return np.asarray(im)


KT = [(-0.4, dict(target=(0.2, 1.4, 0), dist=6.4, yaw=-25, pitch=6, cy=0.55)),
      (5.0, dict(target=(0.2, 1.4, 0), dist=5.6, yaw=-5, pitch=8, cy=0.55))]


def s_antena(t, fi, u, d):
    fr = Frame(cam_path(u, KT))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    ant = P.tfk(antena(), t=(-1.0, 0, -1.0))
    ka = eout(seg(u, 0.6, 1.2))
    ph = P.tfk(P.celular(scr_alerta(0.5 + 0.5 * math.sin(t * 8), on=ka > 0.5), ry=-15), s=0.9, t=(1.0, 0, 0.6))
    draw_objects(fr, ant + ph)
    c = np.array([-1.0, 2.55, -1.0])
    for j in range(4):
        s = (t * 0.7 + j / 4) % 1.0
        r = 0.2 + 2.8 * s
        pts = [c + np.array([r * math.cos(a), -0.6 * s, r * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 60)]
        line3(fr, pts, col=CYAN, w=2.2, a=0.8 * (1 - s), glow=1.0)

    def ui(img, fx):
        kicker(img, 'DIFUSIÓN CELULAR', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        P.pill_tachada(img, fx, 330, 300, 'DATOS', seg(t, wt(11, 2), wt(11, 3)), seg(t, wt(11, 3), wt(11, 4)), t, size=32)
        P.pill_tachada(img, fx, 750, 300, 'SALDO', seg(t, wt(11, 4), wt(11, 5)), seg(t, wt(11, 5), wt(11, 6)), t, size=32)
        pill(img, fx, 540, 1330, 'LLEGA POR LA ANTENA', eout(seg(t, wt(11, 7), wt(11, 8))), size=32, border=CYAN)
    fr.ui.append(ui)
    return finish(fr, fi)


KN = [(-0.4, dict(target=(0.0, 0, -0.4), dist=1.4, yaw=6, pitch=70, cy=0.52)),
      (6.0, dict(target=(0.0, 0, -0.4), dist=1.1, yaw=-6, pitch=74, cy=0.52))]


def s_cerca(t, fi, u, d):
    amp = 0.6 * eout(seg(t, wt(12, 13), wt(12, 15)))
    fr = Frame(cam_temblor(u, KN, t, amp))
    space(fr, t, floor='dots', floor_a=0.3, bokeh=0.6)
    mapa(fr, t, k=1.0, ciudades=('CDMX', 'PUEBLA'), resalta='CDMX')
    e3 = geo(*EPI3)
    te = wt(12, 4)
    anillos(fr, t, e3, te, k=1.0, col=(255, 120, 100), vel=0.25, n=4, rmax=0.8)
    cd = geo(*CIUDADES['CDMX'])

    def ui(img, fx):
        kicker(img, 'SISMO CERCANO', 150, seg(u, 0.0, 0.3), col=(255, 160, 140))
        etiqueta(img, fx, fr, cd, 'CDMX', 1.0, col=AMAR)
        # línea de tiempo: sacudida vs. alerta
        dd = ImageDraw.Draw(img)
        x0, x1, y = 120, 960, 1290
        kk = eout(seg(u, 0.4, 0.8))
        if kk > 0.01:
            dd.line([(x0, y), (x1, y)], fill=M.scale_c(WHITE, 0.6 * kk), width=3)
            for i in range(9):
                xx = x0 + (x1 - x0) * i / 8
                dd.line([(xx, y - 8), (xx, y + 8)], fill=M.scale_c(WHITE, 0.5 * kk), width=2)
            ka = eout(seg(t, wt(12, 8), wt(12, 10)))
            xa = lerp(x1 - 120, x0 + 330, ka)
            xs = x0 + 300
            dd.rounded_rectangle((xs - 8, y - 70, xs + 8, y), radius=6, fill=M.scale_c(RED, kk))
            dd.text((xs, y - 96), 'SACUDIDA', font=M.font('mono', 24), fill=M.scale_c(RED, kk), anchor='mm')
            dd.rounded_rectangle((xa - 8, y, xa + 8, y + 70), radius=6, fill=M.scale_c(AMBAR, kk))
            dd.text((xa, y + 100), 'ALERTA', font=M.font('mono', 24), fill=M.scale_c(AMBAR, kk), anchor='mm')
        pill(img, fx, 540, 300, 'NO DA TIEMPO', eout(seg(t, wt(12, 6), wt(12, 8))), size=34, border=RED)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45), sfx=[]),
           dict(desde=1, fn=s_magnitud, tr='flash', sfx=[(0.2, 'scribble', 0.4), (0.4, 'tick', 0.6)]),
           dict(desde=2, fn=s_ciudades, tr='zoom', c=(0.5, 0.55), sfx=[(0.5, 'chime_a', 0.5), (1.0, 'chime_b', 0.5)]),
           dict(desde=3, fn=s_caso1, tr='wipe', sfx=[(0.2, 'tick', 0.6)]),
           dict(desde=4, fn=s_caso2, tr='whip', sfx=[(0.3, 'scribble', 0.5), (1.0, 'tick', 0.6)]),
           dict(desde=5, fn=s_sensores, tr='push', c=(0.5, 0.5), sfx=[(0.3, 'shimmer', 0.6)]),
           dict(desde=6, fn=s_chiapas, tr='flash', sfx=[(0.2, 'scribble', 0.8), (0.5, 'sub', 0.7), (1.2, 'click', 0.8), (2.4, 'click', 0.8)]),
           dict(desde=7, fn=s_energia, tr='zoom', c=(0.6, 0.5), sfx=[(0.6, 'tick', 0.6)]),
           dict(desde=8, fn=s_bolsillo, tr='flash', sfx=[(0.0, 'sub', 0.8), (0.2, 'shimmer', 0.7), (0.4, 'whoosh_suave', 0.5)]),
           dict(desde=9, fn=s_apagada, tr='whip_izq', sfx=[(0.3, 'tick', 0.5)]),
           dict(desde=10, fn=s_ajustes, tr='zoom', c=(0.5, 0.5), sfx=[(1.0, 'click', 0.8), (2.0, 'click', 0.8)]),
           dict(desde=11, fn=s_antena, tr='wipe', sfx=[(0.3, 'whoosh_suave', 0.5)]),
           dict(desde=12, fn=s_cerca, tr='push', c=(0.5, 0.5), sfx=[(0.2, 'tick', 0.5)]),
           dict(desde=13, fn=s_mandalo, tr='ritmo'),
           dict(desde=14, loop=True, tr='zoom')]


def _sfx_dinamicos():
    ta = wt(0, 4) - TT(0)
    ESCENAS[0]['sfx'] = [(0.15, 'whoosh', 0.3), (ta - 0.3, 'scribble', 0.7), (ta, 'thud', 0.8)]
    tm = wt(1, 11) - TT(1)
    ESCENAS[1]['sfx'] += [(tm - 1.2, 'tick', 0.6), (tm - 0.2, 'scribble', 0.7)]
    ESCENAS[2]['sfx'] += [(wt(2, 9) - TT(2), 'chime_c', 0.6), (0.3, 'riser', 0.3)]
    tc = wt(3, 6) - TT(3)
    ESCENAS[3]['sfx'] += [(tc, 'sub', 0.7), (tc + 1.3, 'tick', 0.6), (wt(3, 11) - TT(3), 'thud', 0.9),
                          (wt(3, 10) - TT(3) + 0.18, 'slap', 0.9)]
    ESCENAS[4]['sfx'] += [(wt(4, 4) - TT(4), 'sub', 0.5), (wt(4, 13) - TT(4), 'chime_c', 0.7), (wt(4, 13) - TT(4) + 0.15, 'chime_b', 0.5)]
    t0 = wt(5, 2) - TT(5)
    ESCENAS[5]['sfx'] += [(t0 + 0.15 * j, 'tick2', 0.35) for j in range(10)] + [(wt(5, 9) - TT(5), 'tick', 0.5),
                                                                               (wt(5, 11) - TT(5), 'tick', 0.5)]
    ESCENAS[6]['sfx'] += [(wt(6, 6) - TT(6), 'bass', 0.6), (wt(6, 12) - TT(6), 'scribble', 0.6), (wt(6, 13) - TT(6), 'tick', 0.6)]
    tc7 = 0.5
    ESCENAS[7]['sfx'] += [(tc7 + 0.25, 'chime_a', 0.6), (tc7 + 0.53, 'chime_b', 0.6), (tc7 + 0.81, 'chime_c', 0.6),
                          (tc7 + 1.2, 'thud', 0.8)]
    ESCENAS[9]['sfx'] += [(wt(9, 10) - TT(9), 'whoosh', 0.5), (wt(9, 15) - TT(9), 'scribble', 0.7), (wt(9, 15) - TT(9), 'thud', 0.7)]
    ti = wt(10, 7) - TT(10)
    ESCENAS[10]['sfx'] += [(wt(10, 5) - TT(10), 'tick', 0.7), (ti, 'whoosh', 0.5), (ti + 0.5, 'tick', 0.7), (ti + 1.0, 'click', 0.8),
                           (ti + 2.0, 'click', 0.8)]
    ESCENAS[11]['sfx'] += [(wt(11, 3) - TT(11), 'scribble', 0.6), (wt(11, 5) - TT(11), 'scribble', 0.6),
                           (wt(11, 7) - TT(11), 'tick', 0.6)]
    ESCENAS[12]['sfx'] += [(wt(12, 4) - TT(12), 'sub', 0.7), (wt(12, 6) - TT(12), 'thud', 0.7), (wt(12, 13) - TT(12), 'bass', 0.6)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
