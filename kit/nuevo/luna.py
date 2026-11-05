"""Reel diario: «Tu Luna se está escapando.» Sáb 7-nov-2026, 19:00. Voz Isaac. Estilo rápido (ESTILO.md §11-12).
Inicio tipo 4 (barra de búsqueda: se escribe la pregunta, Enter y la cámara la atraviesa hacia la Luna). Primera transición: iris.
Datos: la Luna se aleja ~3.8 cm por año; el Apolo 11 dejó en 1969 un panel de 100 retrorreflectores; con pulsos de láser se mide
la distancia (~385 000 km) con error de ~3 cm o menos y regresa ~1 fotón cada pocos segundos (NASA GSFC, «Measuring the Moon's
Distance»; JPL, 2019). Ida y vuelta de la luz: 2 × 385 000 km / 299 792 km/s ≈ 2.6 s. Uñas: ~3.5 mm/mes ≈ 4 cm/año (Yaemsiri et
al., 2010). Hace 70 millones de años el día duraba ~23.5 h y el año tenía 372 días (de Winter et al., 2020, Paleoceanography and
Paleoclimatology). Mareas: el bulto adelantado jala a la Luna y frena la Tierra. Fotos reales: Luna (NASA/GSFC/ASU, LRO) y
retrorreflector del Apolo 11 (NASA, AS11-40-5952). Diagramas, dinosaurio y láser: RECREACIÓN / ESCALA EXAGERADA."""
import math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, glass_type, doodle_circle, line3, dot3,
                    rec_frame, chart_grow, photo_card, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'luna'
TXT = ['¿Sabes cuánto se alejó la Luna…',
       'desde que naciste?',
       'Tu Luna se está escapando.',
       'Cada año se aleja 3.8 centímetros.',
       'Más o menos lo que te crecen las uñas en un año.',
       'Si tienes 20 años, ya está 76 centímetros más lejos.',
       '¿Y cómo lo saben?',
       'Las misiones Apolo dejaron espejos allá arriba.',
       'Desde la Tierra les disparan un láser…',
       'y la luz tarda unos 2.5 segundos en ir y regresar.',
       'De todo ese láser, regresa apenas una partícula de luz cada pocos segundos.',
       'Y con eso miden la distancia con un error de menos de 3 centímetros.',
       'Pero lo más loco es quién la está empujando:',
       'tu mar.',
       'La Luna jala el agua y forma un bulto de marea.',
       'Pero la Tierra gira más rápido y adelanta ese bulto.',
       'Y el bulto jala a la Luna hacia adelante: la sube a una órbita más alta.',
       'A cambio, la Tierra frena.',
       'Hace 70 millones de años, con los dinosaurios, el día duraba 23.5 horas…',
       'y el año tenía 372 días.',
       'Mándaselo a alguien que dice que la Luna siempre está igual.',
       'Y ahora sí, dime:']
VOZ = list(TXT)
VOZ[0] = '[curious] ¿Sabes cuánto se alejó la Luna…'
VOZ[3] = 'Cada año se aleja tres punto ocho centímetros.'
VOZ[5] = 'Si tienes veinte años, ya está setenta y seis centímetros más lejos.'
VOZ[9] = 'y la luz tarda unos dos segundos y medio en ir y regresar.'
VOZ[11] = 'Y con eso miden la distancia con un error de menos de tres centímetros.'
VOZ[12] = '[excited] Pero lo más loco es quién la está empujando:'
VOZ[18] = 'Hace setenta millones de años, con los dinosaurios, el día duraba veintitrés horas y media…'
VOZ[19] = 'y el año tenía trescientos setenta y dos días.'

VERDE = (90, 255, 130)      # láser verde (532 nm)
AMARILLO = (255, 236, 160)
MAR = (90, 170, 255)
ROJO = (255, 64, 56)


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


def cam(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p['roll'])


def K(u, dist, yaw, pitch=8, tx=0.0, ty=2.1, tz=0.0, roll=0.0, vx=0.0):
    return (u, dict(tx=tx + vx, ty=ty, tz=tz, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def mov(u, claves):
    return P.cam_rapida(u, claves)


# ================================================================== la Luna real (foto LRO) como disco
_C = {}
_LUNA = Image.open(os.path.join(HERE, 'img', 'img_luna_lro.jpg')).convert('RGB')
_APOLO = Image.open(os.path.join(HERE, 'img', 'img_apolo11_lrrr.jpg')).convert('RGB')


def _disco():
    if 'disco' not in _C:
        a = np.asarray(_LUNA.convert('L'), np.float32)
        ys, xs = np.where(a > 18)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        # el disco es casi cuadrado; usamos el lado mayor centrado
        cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2
        im = _LUNA.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))
        _C['disco'] = im
    return _C['disco']


def luna_img(rpx, blur=0.0):
    rpx = max(4, int(rpx / 3) * 3)
    key = ('luna', rpx, round(blur, 0))
    if key not in _C:
        d = 2 * rpx
        im = _disco().resize((d, d), Image.LANCZOS)
        m = Image.new('L', (d * 4, d * 4), 0)
        ImageDraw.Draw(m).ellipse((2, 2, d * 4 - 3, d * 4 - 3), fill=255)
        m = m.resize((d, d), Image.LANCZOS)
        im = im.point(lambda v: min(255, int(v * 1.08)))
        if blur > 0.5:
            im = im.filter(ImageFilter.GaussianBlur(blur))
        rgba = im.convert('RGBA')
        rgba.putalpha(m)
        if len(_C) > 400:
            _C.clear()
        _C[key] = rgba
    return _C[key]


def luna2d(img, fx, cx, cy, r, a=1.0, blur=0.0, halo=0.5):
    if r < 3 or a <= 0.01:
        return
    im = luna_img(r, blur)
    x0, y0 = int(cx - im.width / 2), int(cy - im.height / 2)
    al = im.getchannel('A')
    if a < 1:
        al = al.point(lambda v: int(v * a))
    img.paste(im.convert('RGB'), (x0, y0), al)
    if halo:
        rr = im.width / 2
        ImageDraw.Draw(fx).ellipse((cx - rr - 6, cy - rr - 6, cx + rr + 6, cy + rr + 6), outline=M.scale_c((200, 210, 230), halo * a), width=8)


def luna3(fr, C, R, a=1.0, blur=0.0):
    """Disco de la Luna (foto real) en la posición 3D C con radio R (en la capa base, antes de la UI)."""
    s, z = fr.cam.proj([C, np.asarray(C, float) + fr.cam.r * R])
    if z[0] < 0.3:
        return None
    rp = abs(s[1][0] - s[0][0])
    luna2d(fr.base, fr.fx, s[0][0], s[0][1], rp, a, blur)
    return s[0][0] / S, s[0][1] / S, rp / S


def tierra(fr, t, C, R, spin=None, mar=0.0):
    N.earth(fr, t, np.asarray(C, float), R, t * 0.35 if spin is None else spin)
    if mar > 0.01:
        th = np.linspace(0, 2 * math.pi, 80)
        P_ = [np.asarray(C) + np.array([R * 1.03 * math.cos(a), R * 1.03 * math.sin(a), 0]) for a in th]
        line3(fr, P_, col=MAR, w=3, a=mar, glow=1.0)


def flecha3(fr, a, b, col=WHITE, w=3, k=1.0, cabeza=0.12):
    a, b = np.asarray(a, float), np.asarray(b, float)
    e = a + (b - a) * clamp(k)
    line3(fr, [a, e], col=col, w=w, a=1.0, glow=0.8)
    if k > 0.95:
        d = (b - a) / (np.linalg.norm(b - a) + 1e-9)
        n = np.cross(d, fr.cam.f)
        n = n / (np.linalg.norm(n) + 1e-9)
        line3(fr, [e, e - d * cabeza + n * cabeza * 0.6], col=col, w=w, glow=0.8)
        line3(fr, [e, e - d * cabeza - n * cabeza * 0.6], col=col, w=w, glow=0.8)


# ================================================================== escenas
PREG = '¿cuánto se alejó la luna desde que nací?'


# 0. gancho, inicio tipo 4: barra de búsqueda, Enter y la cámara la atraviesa hacia la Luna
def s_gancho(t, fi, u, d):
    te = TE(1) - TT(0) - 0.35                     # Enter mientras dice «naciste?»
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=8 * math.sin(t * 0.3), pitch=4))
    space(fr, t, floor=None, bokeh=1.0)
    m = mov(u, [(-2.0, dict(r=300, y=1080, bl=8.0)), (-0.2, dict(r=330, y=1060, bl=7.0)),
                (te, dict(r=350, y=1050, bl=6.0)), (te + 0.05, dict(r=470, y=1000, bl=0.0)), (4.0, dict(r=490, y=995, bl=0.0))])
    kz = seg(u, te, te + 0.3)                     # la barra vuela hacia la cámara

    def ui(img, fx):
        luna2d(img, fx, 540, m['y'], m['r'], 1.0, blur=m['bl'], halo=0.6)
        if kz < 1:
            s = 1 + 5 * kz ** 2
            a = 1 - kz
            lay = Image.new('RGBA', (M.W, M.H), (0, 0, 0, 0))
            dl = ImageDraw.Draw(lay)
            bw, bh = 940 * s, 124 * s
            cx, cy = 540, 860
            dl.rounded_rectangle((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), radius=bh / 2,
                                 fill=(16, 18, 24, int(235 * a)), outline=(255, 255, 255, int(150 * a)), width=max(2, int(3 * s)))
            r_ = 22 * s
            lx, ly = cx - bw / 2 + 62 * s, cy - 4 * s
            dl.ellipse((lx - r_, ly - r_, lx + r_, ly + r_), outline=(230, 230, 236, int(255 * a)), width=max(2, int(5 * s)))
            dl.line([(lx + r_ * 0.7, ly + r_ * 0.7), (lx + r_ * 1.5, ly + r_ * 1.5)], fill=(230, 230, 236, int(255 * a)), width=max(2, int(6 * s)))
            n = int(clamp((u - 0.05) * 17, 0, len(PREG)))
            txt = PREG[:n]
            f = F('sanss', int(37 * s))
            tx0 = lx + 52 * s
            dl.text((tx0, cy), txt, font=f, fill=(245, 245, 248, int(255 * a)), anchor='lm')
            if (int(t * 3) % 2 == 0 or 0 < n < len(PREG)) and kz == 0:
                cxr = tx0 + dl.textlength(txt, font=f) + 4
                dl.line([(cxr, cy - 26), (cxr, cy + 26)], fill=CYAN + (255,), width=3)
            if kz > 0:
                lay = lay.filter(ImageFilter.GaussianBlur(6 * kz))
            img.paste(lay, (0, 0), lay)
            ImageDraw.Draw(fx).rounded_rectangle((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), radius=bh / 2,
                                                 outline=M.scale_c(CYAN, 0.35 * a), width=5)
        kicker(img, 'BUSCAR', 760, seg(u, -0.3, 0.0) * (1 - kz), col=(150, 210, 230))
        if u >= te + 0.1:
            pill(img, fx, 540, 1440, 'A ~385 000 KM DE TI', eout(seg(u, te + 0.15, te + 0.4)), size=34, border=(200, 200, 210))
        if u >= 0.05:
            P.titulo_golpe(img, fx, [('Tu Luna se está', 'sans'), ('escapando.', 'serif')], 190, seg(u, 0.05, 0.2), size=86)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if 0 <= u - te < 0.3:
        out = M.radial_blur(out, 0.12 * (1 - seg(u, te, te + 0.3)), 0.5, 0.45)
    return sacudir(out, t, golpe_k(u, 0.2, 0.3) + golpe_k(u, te + 0.1, 0.35), amp=20)


# 1. se está escapando: la Luna se aleja de la Tierra por una línea punteada
def s_escapa(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 6.2, 40, 14, ty=1.2, tx=0.6), K(0.3, 6.8, 12, 10, ty=1.4, tx=0.8), K(3.0, 7.0, 8, 10, ty=1.4, tx=0.8)]))
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, (-0.4, 0.0, 0), 0.95)
    x = 1.4 + 0.9 * P.eout4(seg(u, 0.1, 1.2))
    C = np.array([x, 3.1, -0.4])
    for j in range(16):
        a, b = j / 16, (j + 0.5) / 16
        p0 = np.array([-0.4, 0, 0]) + (C - np.array([-0.4, 0, 0])) * a
        p1 = np.array([-0.4, 0, 0]) + (C - np.array([-0.4, 0, 0])) * b
        line3(fr, [p0, p1], col=(170, 175, 190), w=1.6, a=0.6, glow=0.3)
    q = luna3(fr, C, 0.42)
    flecha3(fr, C + np.array([0.45, 0.3, 0]), C + np.array([0.85, 0.75, 0]), col=AMARILLO, k=seg(u, 0.4, 0.8))

    def ui(img, fx):
        kicker(img, 'TIERRA · LUNA · ESCALA EXAGERADA', 150, seg(u, 0.0, 0.3), col=(150, 152, 160))
        if q:
            pill(img, fx, q[0], q[1] - q[2] - 70, 'SE ALEJA', eout(seg(u, 0.5, 0.8)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. 3.8 cm por año (número que golpea + cota)
def s_38(t, fi, u, d):
    tn = wt(3, 4) - TT(3)
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.9)
    m = mov(u, [(-0.2, dict(r=620, x=-140)), (0.2, dict(r=520, x=-260)), (tn, dict(r=500, x=-280)), (tn + 0.05, dict(r=430, x=-330)), (4.0, dict(r=420, x=-340))])

    def ui(img, fx):
        luna2d(img, fx, 540 + m['x'], 1000, m['r'], 1.0)
        x0 = 540 + m['x'] + m['r'] + 14
        k = eout(seg(u, tn - 0.1, tn + 0.3))
        dd = ImageDraw.Draw(img)
        if k > 0:
            x1 = x0 + 230 * k
            for xx in (x0, x1):
                dd.line([(xx, 940), (xx, 1060)], fill=AMARILLO, width=4)
            dd.line([(x0, 1000), (x1, 1000)], fill=AMARILLO, width=4)
            ImageDraw.Draw(fx).line([(x0, 1000), (x1, 1000)], fill=(120, 110, 70), width=10)
        kicker(img, 'CADA AÑO', 300, seg(u, 0.0, 0.3), col=(150, 210, 230), size=32)
        P.numero_golpe(img, fx, '3.8 cm', 470, seg(u, tn - 0.15, tn), size=210, col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tn, 0.35), amp=22)


# 3. como lo que crecen tus uñas (duelo de barras sobre una regla)
def s_unas(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.9)
    m = mov(u, [(-0.2, dict(s=1.25, dy=120)), (0.25, dict(s=1.0, dy=0)), (3.0, dict(s=0.97, dy=-10))])

    def ui(img, fx):
        dd = ImageDraw.Draw(img)
        df = ImageDraw.Draw(fx)
        sc = m['s']
        px = 150 * sc                       # px por cm
        x0 = 540 - 2.5 * px
        yr = 1210 + m['dy']
        dd.rounded_rectangle((x0 - 30, yr, x0 + 5 * px + 30, yr + 120), radius=12, fill=(30, 31, 36), outline=(200, 200, 205), width=2)
        for i in range(51):
            xx = x0 + i * px / 10
            hh = 50 if i % 10 == 0 else (32 if i % 5 == 0 else 18)
            dd.line([(xx, yr), (xx, yr + hh)], fill=(220, 220, 226), width=2)
            if i % 10 == 0:
                dd.text((xx, yr + 84), str(i // 10), font=F('mono', 30), fill=(220, 220, 226), anchor='mm')
        dd.text((x0 + 5 * px + 10, yr + 84), 'cm', font=F('mono', 26), fill=(160, 160, 166), anchor='lm')
        bars = [('LUNA · 1 AÑO', 3.8, (200, 205, 220), 0.1), ('TUS UÑAS · 1 AÑO', 4.2, AMARILLO, 0.5)]
        for j, (lab, v, col, u0) in enumerate(bars):
            k = P.resorte(seg(u, u0, u0 + 0.5))
            y = yr - 300 + j * 140
            w = v * px * k
            dd.rounded_rectangle((x0, y, x0 + max(8, w), y + 70), radius=14, fill=M.scale_c(col, 0.85))
            df.rounded_rectangle((x0, y, x0 + max(8, w), y + 70), radius=14, fill=M.scale_c(col, 0.25))
            dd.text((x0, y - 34), lab, font=F('mono', 28), fill=col, anchor='lm')
            if k > 0.5:
                dd.text((x0 + w + 16, y + 35), f'{v:.1f}'.replace('4.2', '≈4'), font=F('sans', 44), fill=WHITE, anchor='lm')
        kicker(img, 'MÁS O MENOS IGUAL', 300, seg(u, 0.0, 0.3), col=(150, 210, 230), size=32)
        M.title(img, fx, [('Tu Luna se aleja', 'sans'), ('a paso de uña.', 'serif')], 380, seg(u, 0.9, 1.4), size=70)
    fr.ui.append(ui)
    return finish(fr, fi)


# 4. si tienes 20 años: 76 cm (contador de años, luego número que golpea)
def s_76(t, fi, u, d):
    t20 = wt(5, 2) - TT(5)
    t76 = wt(5, 7) - TT(5)
    fr = Frame(cam(u, [K(-0.2, 7.5, -30, 10, ty=1.4, tx=0.8), K(0.3, 6.8, -10, 8, ty=1.4, tx=0.8), K(t76 - 0.1, 6.6, -6, 8, ty=1.4, tx=0.8),
                       K(t76 + 0.05, 5.4, 18, 6, ty=1.9, tx=0.9), K(5.0, 5.3, 20, 6, ty=1.9, tx=0.9)]))
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, (-0.6, -0.2, 0), 0.9)
    anos = int(20 * clamp((u + 0.1) / max(0.3, t20 + 0.4)))
    x = 1.2 + 0.05 * anos
    C = np.array([x, 3.0, -0.3])
    C0 = np.array([1.2, 3.0, -0.3])
    luna3(fr, C0, 0.55, a=0.25)
    q = luna3(fr, C, 0.55)
    a0 = fr.cam.p1(C0 + np.array([0.58, 0, 0]))
    a1 = fr.cam.p1(C + np.array([0.58, 0, 0]))

    def ui(img, fx):
        kicker(img, 'EDAD', 140, seg(u, 0.0, 0.3), col=(150, 210, 230), size=30)
        f = F('sansx', 200)
        dd = ImageDraw.Draw(img)
        if u < t76:
            dd.text((540, 330), f'{anos} años', font=F('sansx', 150), fill=WHITE, anchor='mm')
            ImageDraw.Draw(fx).text((540, 330), f'{anos} años', font=F('sansx', 150), fill=(90, 90, 96), anchor='mm')
        else:
            P.numero_golpe(img, fx, '76 cm', 330, seg(u, t76, t76 + 0.15), size=200, col=AMARILLO)
            if a1[0] - a0[0] > 4:
                for xx in (a0[0], a1[0]):
                    dd.line([(xx, a0[1] - 40), (xx, a0[1] + 40)], fill=AMARILLO, width=4)
                dd.line([(a0[0], a0[1]), (a1[0], a1[1])], fill=AMARILLO, width=4)
        pill(img, fx, 540, 1430, 'ESCALA EXAGERADA', 1.0, size=24, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, t76 + 0.15, 0.35), amp=22)


# 5. ¿y cómo lo saben? (crash zoom a la Luna, al Mar de la Tranquilidad)
def s_como(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.8)
    z = 1 + 2.4 * P.eout4(seg(u, 0.1, 1.0))
    # Mar de la Tranquilidad en el disco (aprox.: 0.62, 0.42 del disco)
    r = 470 * z
    cx = 540 - (0.62 - 0.5) * 2 * r
    cy = 960 - (0.42 - 0.5) * 2 * r

    def ui(img, fx):
        luna2d(img, fx, cx, cy, r, 1.0, halo=0.3)
        glass_type(img, fx, '¿?', 540, 960, 420, k=eout(seg(u, -0.1, 0.25)) * (1 - seg(u, 0.9, 1.2)), fill_a=0.08)
        kicker(img, 'MAR DE LA TRANQUILIDAD', 300, seg(u, 0.7, 0.9), col=(150, 210, 230), size=30)
        doodle_circle(img, fx, 540, 960, 150, 120, t, k=eout(seg(u, 0.8, 1.1)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    return finish(fr, fi)


# 6. el Apolo dejó espejos (foto real que cae + garabato)
def s_espejos(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=0.9)
    m = mov(u, [(-0.2, dict(z=1.25)), (0.3, dict(z=1.0)), (1.2, dict(z=1.0)), (1.35, dict(z=1.18)), (3.0, dict(z=1.2))])

    def ui(img, fx):
        kicker(img, 'APOLO 11 · 1969 · FOTO REAL', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        photo_card(img, fx, _APOLO, 540, 790, 740, t - u - 0.15, t, caption='NASA · APOLO 11 · RETRORREFLECTOR', angle0=-8)
        doodle_circle(img, fx, 540 + 10, 790 - 58, 135, 96, t, k=eout(seg(u, 0.6, 1.0)), col=AMARILLO, w=6)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if abs(m['z'] - 1) > 0.01:
        out = M.scale_about(out, m['z'], 0.5, 0.4)
    im = Image.fromarray(out)
    fx2 = Image.new('RGB', (M.W, M.H))
    pill(im, fx2, 540, 1400, '100 ESPEJOS DE ESQUINA', eout(seg(u, 0.9, 1.2)), size=34, border=AMARILLO)
    out = np.clip(np.asarray(im, np.float32) + np.asarray(fx2, np.float32) * 0.5, 0, 255).astype(np.uint8)
    return sacudir(out, t, golpe_k(u, 0.13, 0.3), amp=16)


# Tierra abajo, Luna arriba (vertical), para el láser
TC, TR = np.array([0.0, -0.1, 0.0]), 1.05
LC, LR = np.array([0.0, 4.4, 0.0]), 0.42
EST = TC + np.array([-0.35, TR * 0.94, 0.12])          # estación en la Tierra (recreación)
ESP = LC + np.array([0.12, -LR * 0.9, 0.12])           # espejos en la Luna


def _vertical(u, claves):
    return Frame(cam(u, claves, cy=0.5))


# 7. desde la Tierra les disparan un láser
def s_laser(t, fi, u, d):
    fr = _vertical(u, [K(-0.2, 7.6, 40, 6, ty=2.0, vx=1.2), K(0.3, 9.0, 14, 4, ty=2.1, vx=1.2), K(3.0, 9.0, 10, 4, ty=2.1, vx=1.2)])
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, TC, TR)
    luna3(fr, LC, LR)
    k = P.eout4(seg(u, 0.5, 1.1))
    line3(fr, [EST, EST + (ESP - EST) * k], col=VERDE, w=5, a=1.0, glow=1.4)
    dot3(fr, EST, r=10, col=VERDE, a=1.0, glow=1.5)
    e = fr.cam.p1(EST)

    def ui(img, fx):
        kicker(img, 'LÁSER · RECREACIÓN', 150, seg(u, 0.0, 0.3), col=VERDE)
        pill(img, fx, e[0] + 40, e[1] + 110, 'OBSERVATORIO', eout(seg(u, 0.2, 0.5)), size=28, border=VERDE, anchor='l')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.5, 0.3), amp=12)


# 8. la luz tarda unos 2.5 s en ir y regresar (pulso que va y vuelve + cronómetro)
def s_ida(t, fi, u, d):
    t0 = 0.1
    tv = 2.6
    fr = _vertical(u, [K(-0.2, 8.5, -20, 4, ty=2.0, vx=1.2), K(0.3, 9.0, -8, 4, ty=2.1, vx=1.2), K(4.0, 8.9, -4, 4, ty=2.1, vx=1.2)])
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, TC, TR)
    luna3(fr, LC, LR)
    line3(fr, [EST, ESP], col=VERDE, w=2, a=0.35, glow=0.4)
    s = clamp((u - t0) / tv)
    p = ESP + (EST - ESP) * (2 * s - 1) if s > 0.5 else EST + (ESP - EST) * (2 * s)
    if 0 < s < 1:
        dot3(fr, p, r=14, col=VERDE, a=1.0, glow=2.0)
    reloj = min(2.56, max(0.0, (u - t0) / tv * 2.56))

    def ui(img, fx):
        kicker(img, 'IDA Y VUELTA', 150, seg(u, 0.0, 0.3), col=VERDE)
        txt = f'{reloj:.2f} s'
        dd = ImageDraw.Draw(img)
        dd.text((790, 900), txt, font=F('mono', 96), fill=WHITE, anchor='mm')
        ImageDraw.Draw(fx).text((790, 900), txt, font=F('mono', 96), fill=(70, 120, 80), anchor='mm')
        if s >= 1:
            pill(img, fx, 790, 1030, '≈ 2.5 SEGUNDOS', eout(seg(u, t0 + tv, t0 + tv + 0.3)), size=36, border=VERDE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, t0 + tv, 0.35), amp=16)


# 9. de todo el láser regresa una partícula de luz cada pocos segundos (segundo gancho)
def s_una(t, fi, u, d):
    t1 = wt(10, 7) - TT(10)                    # «una partícula»
    fr = _vertical(u, [K(-0.2, 8.2, 30, 6, ty=2.0, vx=1.2), K(0.3, 9.0, 14, 4, ty=2.1, vx=1.2), K(t1 - 0.05, 8.9, 12, 4, ty=2.1, vx=1.2),
                       K(t1 + 0.05, 4.2, 6, 4, ty=1.0, vx=0.6), K(5.5, 4.0, 4, 4, ty=0.9, vx=0.6)])
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, TC, TR)
    luna3(fr, LC, LR)
    rng = np.random.RandomState(12)
    for j in range(40):                          # millones de fotones que suben y se abren (recreación)
        ph = (t * 0.9 + j / 40) % 1.0
        ang = rng.uniform(-1, 1)
        p = EST + (ESP - EST) * ph + np.array([ang * 0.9 * ph ** 2, 0, rng.uniform(-0.2, 0.2) * ph])
        dot3(fr, p, r=3, col=VERDE, a=0.7 * (1 - ph * 0.5), glow=0.8)
    if u > t1 - 1.0:                              # uno solo regresa
        s = clamp((u - (t1 - 1.0)) / 1.6)
        p = ESP + (EST - ESP) * P.eout4(s) if s < 1 else EST
        dot3(fr, p, r=12, col=(220, 255, 220), a=1.0, glow=2.2)
        q = fr.cam.p1(p)
    else:
        q = None

    def ui(img, fx):
        kicker(img, 'SALEN MUCHÍSIMAS · REGRESA…', 150, seg(u, 0.0, 0.3), col=VERDE)
        if u >= t1:
            k1 = eout(seg(u, t1, t1 + 0.15))
            f1 = F('sansx', int(300 * (2.2 - 1.2 * k1)))
            ImageDraw.Draw(img).text((800, 860), '1', font=f1, fill=M.scale_c((220, 255, 220), min(1, k1 * 2)), anchor='mm')
            ImageDraw.Draw(fx).text((800, 860), '1', font=f1, fill=M.scale_c((110, 160, 110), min(1, k1 * 2)), anchor='mm')
            if q:
                doodle_circle(img, fx, q[0], q[1], 70, 70, t, k=eout(seg(u, t1 + 0.2, t1 + 0.5)), col=AMARILLO, w=6)
            pill(img, fx, 790, 1080, 'PARTÍCULA DE LUZ', eout(seg(u, t1 + 0.3, t1 + 0.6)), size=32, border=VERDE)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, t1 + 0.15, 0.4), amp=24)


# 10. miden la distancia con error de menos de 3 cm (cota + zoom digital)
def s_error3(t, fi, u, d):
    t3 = wt(11, 11) - TT(11)
    fr = _vertical(u, [K(-0.2, 7.0, -30, 6, ty=2.0, vx=1.2), K(0.3, 9.0, -6, 4, ty=2.1, vx=1.2), K(5.0, 8.9, -2, 4, ty=2.1, vx=1.2)])
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, TC, TR)
    luna3(fr, LC, LR)
    xa = 1.55
    pa, pb = np.array([xa, TC[1], 0]), np.array([xa, LC[1], 0])
    k = P.eout4(seg(u, 0.1, 0.8))
    line3(fr, [pa, pa + (pb - pa) * k], col=AMARILLO, w=3, a=1.0, glow=0.8)
    for pp in (pa, pb):
        line3(fr, [pp - np.array([0.18, 0, 0]), pp + np.array([0.18, 0, 0])], col=AMARILLO, w=3, a=k, glow=0.8)
    km = int(385000 * clamp(seg(u, 0.1, 1.2)))
    mid = fr.cam.p1((pa + pb) / 2)
    top = fr.cam.p1(pb)

    def ui(img, fx):
        kicker(img, 'DISTANCIA PROMEDIO', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        dd = ImageDraw.Draw(img)
        txt = f'{km:,} km'.replace(',', ' ')
        dd.text((mid[0] + 30, mid[1]), txt, font=F('mono', 50), fill=AMARILLO, anchor='lm')
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u >= t3 - 0.3:
        z = 1.45 if u < t3 + 0.35 else 2.0
        out = M.scale_about(out, z, top[0] / M.W, top[1] / M.H)
        im = Image.fromarray(out)
        rec_frame(im, t, 1.0, f'x{z:.1f}')
        fx = Image.new('RGB', (M.W, M.H))
        P.numero_golpe(im, fx, '± 3 cm', 1250, seg(u, t3, t3 + 0.15), size=170, col=AMARILLO)
        out = np.clip(np.asarray(im, np.float32) + np.asarray(fx, np.float32) * 0.6, 0, 255).astype(np.uint8)
    return sacudir(out, t, golpe_k(u, t3 + 0.15, 0.3), amp=16)


# 11. ¿quién la empuja? … tu mar (segundo gancho dicho)
def s_mar(t, fi, u, d):
    tm = TT(13) - TT(12) - 0.05
    if u < tm:
        fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
        space(fr, t, floor=None, bokeh=0.9)
        m = mov(u, [(-0.2, dict(r=260, a=-30)), (0.3, dict(r=380, a=0)), (tm, dict(r=400, a=4))])

        def ui(img, fx):
            luna2d(img, fx, 540 + m['a'] * 3, 1000, m['r'], 1.0)
            for j in range(3):
                ang = -2.6 + j * 0.25 + 0.05 * math.sin(t * 9 + j)
                x0 = 540 + math.cos(ang) * (m['r'] + 200)
                y0 = 1000 + math.sin(ang) * (m['r'] + 200)
                M.doodle_arrow(img, fx, x0, y0, 540 + math.cos(ang) * (m['r'] + 30), 1000 + math.sin(ang) * (m['r'] + 30), t,
                               k=eout(seg(u, 0.3 + 0.15 * j, 0.6 + 0.15 * j)), col=AMARILLO, w=6, seed=j)
            P.titulo_golpe(img, fx, [('¿Quién la empuja?', 'sans')], 260, seg(u, 0.1, 0.25), size=80)
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.3), amp=16)
    uu = u - tm
    fr = Frame(cam(uu, [K(0.0, 2.6, 0, 10, ty=0.4), K(0.3, 4.6, -24, 14, ty=0.4), K(3.0, 4.5, -28, 14, ty=0.4)]))
    space(fr, t, floor=None, bokeh=1.0)
    tierra(fr, t, (0, 0.4, 0), 1.25, mar=1.0)
    # olas de alambre
    for j in range(3):
        xs = np.linspace(-1.6, 1.6, 90)
        pts = [(x, -1.15 - j * 0.16 + 0.07 * math.sin(x * 5 - t * 6 + j), 0.6) for x in xs]
        line3(fr, pts, col=MAR, w=2.5, a=0.9 - 0.2 * j, glow=1.0)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Tu mar.', 'serif')], 230, seg(uu, 0.0, 0.15), size=130, col=(170, 210, 255))
    fr.ui.append(ui)
    out = finish(fr, fi, flash=0.5 * (1 - seg(uu, 0, 0.2)))
    return sacudir(out, t, golpe_k(uu, 0.15, 0.45), amp=26)


# diagrama de mareas visto desde arriba (plano XZ)
def _diagrama(fr, t, ang_bulto=0.0, k_bulto=1.0, rot=1.0, luna_r=2.9, luna_ang=90.0, flecha_luna=0.0, orb=None):
    C = np.array([0.0, 0.0, 0.0])
    R = 0.9
    spin = t * 1.6 * rot
    for lon in range(0, 180, 30):              # Tierra de alambre vista desde el polo
        a = math.radians(lon) + spin
        line3(fr, [C + np.array([R * math.cos(a), 0, R * math.sin(a)]), C - np.array([R * math.cos(a), 0, R * math.sin(a)])],
              col=(200, 205, 215), w=1.2, a=0.6, glow=0.3)
    th = np.linspace(0, 2 * math.pi, 90)
    line3(fr, [C + np.array([R * math.cos(a), 0, R * math.sin(a)]) for a in th], col=WHITE, w=2.2, a=0.9, glow=0.6)
    # bulto de marea (elipse de agua)
    b = math.radians(luna_ang + ang_bulto)
    ea, eb = R * (1.0 + 0.32 * k_bulto), R * 1.06
    pts = []
    for a in th:
        x, z = ea * math.cos(a), eb * math.sin(a)
        pts.append(C + np.array([x * math.cos(b) - z * math.sin(b), 0.01, x * math.sin(b) + z * math.cos(b)]))
    line3(fr, pts, col=MAR, w=4, a=1.0, glow=1.2)
    la = math.radians(luna_ang)
    L = C + np.array([luna_r * math.cos(la), 0, luna_r * math.sin(la)])
    if orb:
        for rr, aa in orb:
            line3(fr, [C + np.array([rr * math.cos(a), 0, rr * math.sin(a)]) for a in th], col=(170, 175, 190), w=1.4, a=aa, glow=0.3)
    return C, R, L, b


# 12. la Luna jala el agua y forma un bulto de marea
def s_bulto(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 7.4, 0, 70, ty=0.0, tz=-1.2), K(0.3, 7.0, 0, 62, ty=0.0, tz=-1.2), K(3.5, 6.9, 4, 60, ty=0.0, tz=-1.2)]))
    space(fr, t, floor=None, bokeh=0.8)
    kb = P.resorte(seg(u, 0.4, 1.1))
    C, R, L, b = _diagrama(fr, t, 0.0, kb, rot=0.3, luna_ang=-90)
    luna3(fr, L, 0.36)
    for j in (-1, 0, 1):
        flecha3(fr, L + np.array([0.15 * j, 0, 0.5]), C + np.array([0.15 * j, 0, -R * 1.45]), col=AMARILLO, k=seg(u, 0.1, 0.5))
    pb = fr.cam.p1(C + np.array([0, 0, -R * 1.35]))

    def ui(img, fx):
        kicker(img, 'VISTA DESDE ARRIBA · RECREACIÓN', 150, seg(u, 0.0, 0.3), col=(150, 152, 160))
        pill(img, fx, 540, 1380, 'BULTO DE MAREA', eout(seg(u, 1.0, 1.3)), size=36, border=MAR)
        doodle_circle(img, fx, pb[0], pb[1] + 20, 140, 70, t, k=eout(seg(u, 1.1, 1.5)), col=MAR, w=5)
    fr.ui.append(ui)
    return finish(fr, fi)


# 13. la Tierra gira más rápido y adelanta el bulto
def s_adelanta(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.2, 6.6, 30, 55, ty=0.0, tz=-1.2), K(0.3, 6.9, 10, 64, ty=0.0, tz=-1.2), K(3.5, 6.8, 6, 64, ty=0.0, tz=-1.2)]))
    space(fr, t, floor=None, bokeh=0.8)
    ka = P.eout4(seg(u, 0.6, 1.4))
    C, R, L, b = _diagrama(fr, t, 28 * ka, 1.0, rot=1.0, luna_ang=-90)
    luna3(fr, L, 0.36)
    th = np.linspace(math.radians(200), math.radians(320), 30)
    arc = [C + np.array([1.55 * math.cos(a), 0.02, 1.55 * math.sin(a)]) for a in th]
    line3(fr, arc, col=WHITE, w=3, a=seg(u, 0.1, 0.4), glow=0.8)
    flecha3(fr, arc[-2], arc[-1] + (arc[-1] - arc[-2]) * 3, col=WHITE, k=1.0 if u > 0.4 else 0.0, cabeza=0.18)
    pb = fr.cam.p1(C + np.array([1.25 * math.cos(b), 0, 1.25 * math.sin(b)]))

    def ui(img, fx):
        kicker(img, 'LA TIERRA GIRA EN 24 H · LA LUNA TARDA ~27 DÍAS', 150, seg(u, 0.0, 0.3), col=(150, 152, 160), size=22)
        pill(img, fx, pb[0], pb[1] - 90, 'ADELANTADO', eout(seg(u, 1.2, 1.5)), size=32, border=MAR)
    fr.ui.append(ui)
    return finish(fr, fi)


# 14. el bulto jala a la Luna hacia adelante y la sube a una órbita más alta
def s_sube(t, fi, u, d):
    ts = wt(16, 9) - TT(16)                       # «la sube»
    if u < ts:
        fr = Frame(cam(u, [K(-0.2, 7.2, -14, 66, ty=0.0, tz=-1.2), K(0.3, 6.9, -4, 64, ty=0.0, tz=-1.2), K(ts, 6.8, -2, 64, ty=0.0, tz=-1.2)]))
    else:
        fr = Frame(cam(u - ts, [K(0.0, 8.4, 20, 40, ty=0.0, tz=-0.8), K(0.3, 9.4, 30, 34, ty=0.0, tz=-0.8), K(3.0, 9.5, 34, 33, ty=0.0, tz=-0.8)]))
    space(fr, t, floor=None, bokeh=0.8)
    kr = P.eout4(seg(u, ts, ts + 1.2))
    lr = 2.9 + 0.8 * kr
    lang = -90 + 14 * seg(u, 0.2, ts) + 20 * kr
    C, R, L, b = _diagrama(fr, t, 28, 1.0, rot=1.0, luna_r=lr, luna_ang=lang, orb=[(2.9, 0.5), (lr, 0.9 * kr)])
    luna3(fr, L, 0.36)
    tang = np.array([-math.sin(math.radians(lang)), 0, math.cos(math.radians(lang))])
    flecha3(fr, L + tang * 0.45, L + tang * 1.35, col=AMARILLO, k=seg(u, 0.4, 0.8))
    bp = C + np.array([1.2 * math.cos(b), 0, 1.2 * math.sin(b)])
    line3(fr, [bp, L], col=MAR, w=2, a=0.6 * seg(u, 0.2, 0.5), glow=0.6)
    pl = fr.cam.p1(L)

    def ui(img, fx):
        kicker(img, 'EL BULTO JALA A LA LUNA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        if u >= ts:
            pill(img, fx, pl[0], pl[1] - 120, 'ÓRBITA MÁS ALTA', eout(seg(u, ts + 0.2, ts + 0.5)), size=34, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ts, 0.3), amp=14)


# 15. a cambio, la Tierra frena
def s_frena(t, fi, u, d):
    tf = wt(17, 4) - TT(17)
    fr = Frame(cam(u, [K(-0.2, 3.6, 40, 10, ty=0.0), K(0.3, 4.4, 10, 8, ty=0.0), K(tf, 4.3, 8, 8, ty=0.0),
                       K(tf + 0.05, 3.6, -6, 6, ty=0.0), K(3.0, 3.5, -8, 6, ty=0.0)]))
    space(fr, t, floor=None, bokeh=1.0)
    # giro que frena: el ángulo crece rápido y luego casi se detiene
    sp = 6.0 * min(u, tf) + 1.2 * max(0.0, u - tf) + 9.0
    N.earth(fr, t, np.array([0, 0, 0]), 1.25, sp)
    ttop = fr.cam.p1(np.array([0, 1.25, 0]))

    def ui(img, fx):
        kicker(img, 'LA TIERRA PIERDE GIRO', 150, seg(u, 0.0, 0.3), col=(255, 140, 120))
        if u >= tf:
            P.titulo_golpe(img, fx, [('La Tierra', 'sans'), ('frena.', 'serif')], 240, seg(u, tf, tf + 0.15), size=90, col=(255, 150, 140))
        pill(img, fx, 540, 1420, 'EL DÍA SE ALARGA', eout(seg(u, tf + 0.3, tf + 0.6)), size=34, border=ROJO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tf + 0.15, 0.4), amp=22)


# 16. hace 70 millones de años el día duraba 23.5 horas (dinosaurio de alambre + reloj)
SAURO = [(0.0, 0.30), (0.12, 0.33), (0.25, 0.38), (0.38, 0.45), (0.50, 0.47), (0.58, 0.45), (0.66, 0.50), (0.74, 0.62), (0.80, 0.74),
         (0.85, 0.80), (0.92, 0.81), (0.96, 0.78), (0.91, 0.75), (0.85, 0.72), (0.80, 0.62), (0.74, 0.48), (0.70, 0.38), (0.68, 0.30),
         (0.68, 0.02), (0.62, 0.02), (0.61, 0.26), (0.44, 0.26), (0.43, 0.02), (0.37, 0.02), (0.36, 0.28), (0.25, 0.32), (0.12, 0.31), (0.0, 0.30)]


def sauro(img, fx, x, y, s, t, a=1.0, col=WHITE):
    if a <= 0.01:
        return
    pts = []
    for (px, py) in SAURO:
        dy = 0.012 * math.sin(t * 6 + px * 4) if py < 0.05 else 0.0
        pts.append((x + px * s, y - (py + dy) * s))
    ImageDraw.Draw(img).line(pts, fill=M.scale_c(col, a), width=max(2, int(s / 110)), joint='curve')
    ImageDraw.Draw(fx).line(pts, fill=M.scale_c(col, 0.6 * a), width=max(4, int(s / 55)), joint='curve')
    ex, ey = x + 0.91 * s, y - 0.79 * s
    ImageDraw.Draw(img).ellipse((ex - 4, ey - 4, ex + 4, ey + 4), fill=M.scale_c(col, a))


def reloj(img, fx, cx, cy, r, horas, t, k=1.0):
    if k <= 0.01:
        return
    dd = ImageDraw.Draw(img)
    df = ImageDraw.Draw(fx)
    c = M.scale_c(WHITE, k)
    dd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=5)
    df.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(WHITE, 0.4 * k), width=10)
    for i in range(24):
        a = -math.pi / 2 + 2 * math.pi * i / 24
        r0 = r * (0.82 if i % 6 == 0 else 0.9)
        dd.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r * 0.97 * math.cos(a), cy + r * 0.97 * math.sin(a))], fill=c, width=4)
    # arco del día de 23.5 h y lo que falta para 24 en rojo
    a1 = -90 + 360 * horas / 24
    dd.arc((cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy + r * 0.7), -90, a1, fill=AMARILLO, width=16)
    if horas < 24:
        dd.arc((cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy + r * 0.7), a1, 270, fill=ROJO, width=16)
    a = math.radians(a1)
    dd.line([(cx, cy), (cx + r * 0.62 * math.cos(a), cy + r * 0.62 * math.sin(a))], fill=c, width=7)


def s_dinos(t, fi, u, d):
    td = wt(18, 7) - TT(18)                         # «dinosaurios»
    th = wt(18, 11) - TT(18)                        # «veintitrés»
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6.5, yaw=10 * math.sin(t * 0.4), pitch=10))
    space(fr, t, floor='lines', floor_a=0.8 * seg(u, 0.0, 0.3), bokeh=0.9)
    m = mov(u, [(-0.2, dict(z=1.3)), (0.3, dict(z=1.0)), (th - 0.1, dict(z=1.0)), (th + 0.05, dict(z=1.15)), (6.0, dict(z=1.16))])
    anos = int(70 * clamp(seg(u, -0.1, td - 0.3)))
    if u < td - 0.2:
        N.earth(fr, t, np.array([0.0, 1.6, -1.0]), 1.3 * (1 - 0.3 * seg(u, td - 0.8, td - 0.2)), -t * 9.0)

    def ui(img, fx):
        if u < th:
            txt = f'hace {anos} millones de años'
            ImageDraw.Draw(img).text((540, 330), txt, font=F('sans', 58), fill=WHITE, anchor='mm')
            kicker(img, 'VIAJE AL PASADO', 230, seg(u, 0.0, 0.3), col=(150, 210, 230), size=30)
            ue = td - 0.5
            x = 1200 - 960 * P.eout4(seg(u, ue, ue + 0.3)) - 60 * seg(u, ue + 0.3, th)
            if u >= ue:
                sauro(img, fx, x, 1420, 600, t, a=1.0)
        else:
            reloj(img, fx, 540, 960, 300, 23.5, t, k=eout(seg(u, th - 0.05, th + 0.2)))
            P.numero_golpe(img, fx, '23.5 h', 420, seg(u, th, th + 0.15), size=190, col=AMARILLO)
            pill(img, fx, 540, 1400, 'HOY: 24 H', eout(seg(u, th + 0.4, th + 0.7)), size=34, border=(200, 200, 210))
    fr.ui.append(ui)
    out = finish(fr, fi)
    if abs(m['z'] - 1) > 0.01:
        out = M.scale_about(out, m['z'], 0.5, 0.5)
    return sacudir(out, t, golpe_k(u, th + 0.15, 0.4), amp=22)


# 17. y el año tenía 372 días (gráfico que crece)
def s_372(t, fi, u, d):
    tn = wt(19, 5) - TT(19)
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=14, cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'DÍAS EN UN AÑO', 150, seg(u, -0.1, 0.2))
        chart_grow(img, fx, (140, 330, 940, 1220), [365, 372], ['HOY', 'DINOS'], t - u - 0.1, t, unit='', title_txt='DÍAS', vmax=420,
                   tag='DE WINTER, 2020', line=False)
        pill(img, fx, 540, 1350, '+7 DÍAS', eout(seg(u, tn, tn + 0.3)), size=44, border=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, tn, 0.3), amp=14)


# 18. mándaselo a quien dice que la Luna siempre está igual
def s_mandalo(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0, 0), dist=5, yaw=0, pitch=4))
    space(fr, t, floor=None, bokeh=1.0)
    m = mov(u, [(-0.2, dict(r=600, y=1150)), (0.3, dict(r=420, y=1080)), (3.5, dict(r=410, y=1075))])

    def ui(img, fx):
        luna2d(img, fx, 540, m['y'], m['r'], 1.0, halo=0.6)
        M.title(img, fx, [('Mándaselo a quien dice', 'sans'), ('que la Luna siempre está igual.', 'serif')], 190, seg(u, 0.0, 0.4), size=58)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[]),
           dict(desde=2, fn=s_escapa, tr='iris', c=(0.6, 0.35), sfx=[]),
           dict(desde=3, fn=s_38, tr='golpe', sfx=[]),
           dict(desde=4, fn=s_unas, tr='deslizar', sfx=[]),
           dict(desde=5, fn=s_76, tr='whip', sfx=[]),
           dict(desde=6, fn=s_como, tr='giro', sfx=[]),
           dict(desde=7, fn=s_espejos, tr='zoom', sfx=[]),
           dict(desde=8, fn=s_laser, tr='flash', sfx=[]),
           dict(desde=9, fn=s_ida, tr='whip_izq', sfx=[]),
           dict(desde=10, fn=s_una, tr='golpe', sfx=[]),
           dict(desde=11, fn=s_error3, tr='wipe', sfx=[]),
           dict(desde=12, fn=s_mar, tr='giro', sfx=[]),
           dict(desde=14, fn=s_bulto, tr='deslizar_abajo', sfx=[]),
           dict(desde=15, fn=s_adelanta, tr='push', c=(0.5, 0.5), sfx=[]),
           dict(desde=16, fn=s_sube, tr='iris', sfx=[]),
           dict(desde=17, fn=s_frena, tr='whip', sfx=[]),
           dict(desde=18, fn=s_dinos, tr='flash', sfx=[]),
           dict(desde=19, fn=s_372, tr='deslizar', sfx=[]),
           dict(desde=20, fn=s_mandalo, tr='ritmo', sfx=[]),
           dict(desde=21, loop=True, tr='zoom')]


def _sfx_dinamicos():
    E = ESCENAS
    te = TE(1) - TT(0) - 0.35
    E[0]['sfx'] = [(0.2, 'bass', 0.9)] + [(0.05 + i / 17, 'tick2', 0.22) for i in range(0, len(PREG), 2)] + \
                  [(te - 0.05, 'click', 1.0), (te, 'whoosh', 0.8), (te + 0.1, 'sub', 0.9), (te + 0.2, 'shimmer', 0.5)]
    E[1]['sfx'] = [(0.1, 'whoosh_suave', 0.6), (0.5, 'tick', 0.5)]
    tn = wt(3, 4) - TT(3)
    E[2]['sfx'] = [(tn - 0.1, 'whoosh', 0.5), (tn, 'bass', 1.0), (tn + 0.05, 'tick', 0.5)]
    E[3]['sfx'] = [(0.1, 'chime_a', 0.6), (0.5, 'chime_b', 0.6), (0.9, 'shimmer', 0.4)]
    t20, t76 = wt(5, 2) - TT(5), wt(5, 7) - TT(5)
    E[4]['sfx'] = [(0.1 + i * 0.1, 'tick2', 0.25) for i in range(int((t20 + 0.3) / 0.1))] + [(t76, 'whoosh', 0.5), (t76 + 0.15, 'bass', 1.0)]
    E[5]['sfx'] = [(0.1, 'whoosh', 0.7), (0.0, 'shimmer', 0.5), (0.8, 'scribble', 0.6)]
    E[6]['sfx'] = [(0.13, 'slap', 0.9), (0.6, 'scribble', 0.6), (0.9, 'tick', 0.5)]
    E[7]['sfx'] = [(0.45, 'riser', 0.4), (0.5, 'shimmer', 0.6), (0.55, 'tick', 0.6)]
    E[8]['sfx'] = [(0.1, 'whoosh_suave', 0.4), (1.4, 'chime_b', 0.5), (2.7, 'chime_c', 0.7), (2.7, 'bass', 0.7)] + \
                  [(0.1 + i * 0.25, 'tick', 0.25) for i in range(11)]
    t1 = wt(10, 7) - TT(10)
    E[9]['sfx'] = [(0.1, 'whoosh_suave', 0.5), (t1 - 0.4, 'riser', 0.5), (t1, 'burst', 0.4), (t1 + 0.15, 'sub', 1.0), (t1 + 0.2, 'scribble', 0.6),
                   (t1 + 0.35, 'chime_c', 0.6)]
    t3 = wt(11, 11) - TT(11)
    E[10]['sfx'] = [(0.1 + i * 0.1, 'tick2', 0.22) for i in range(11)] + [(t3 - 0.3, 'click', 0.9), (t3 + 0.35, 'click', 0.9), (t3 + 0.15, 'bass', 0.9)]
    tm = TT(13) - TT(12) - 0.05
    E[11]['sfx'] = [(0.25, 'bass', 0.8), (0.3, 'scribble', 0.6), (tm, 'burst', 0.6), (tm + 0.05, 'sub', 1.0), (tm + 0.1, 'whoosh_suave', 0.6)]
    E[12]['sfx'] = [(0.1, 'whoosh', 0.4), (0.4, 'shimmer', 0.5), (1.0, 'chime_a', 0.5), (1.1, 'scribble', 0.5)]
    E[13]['sfx'] = [(0.1, 'whoosh_suave', 0.6), (0.6, 'whoosh', 0.4), (1.2, 'chime_b', 0.5)]
    ts = wt(16, 9) - TT(16)
    E[14]['sfx'] = [(0.4, 'whoosh', 0.4), (ts, 'riser', 0.4), (ts + 0.2, 'chime_c', 0.6)]
    tf = wt(17, 4) - TT(17)
    E[15]['sfx'] = [(0.0, 'whoosh_suave', 0.5), (tf, 'thud', 0.8), (tf + 0.15, 'bass', 1.0), (tf + 0.3, 'tick', 0.5)]
    td, th = wt(18, 7) - TT(18), wt(18, 12) - TT(18)
    E[16]['sfx'] = [(0.0, 'riser', 0.4)] + [(0.1 + i * 0.12, 'tick2', 0.22) for i in range(int((td - 0.4) / 0.12))] + \
                   [(td - 0.6, 'thud', 0.6), (td - 0.1, 'thud', 0.6), (td + 0.4, 'thud', 0.6), (th, 'whoosh', 0.5), (th + 0.15, 'bass', 1.0)]
    tn2 = wt(19, 5) - TT(19)
    E[17]['sfx'] = [(0.15, 'chime_a', 0.6), (0.43, 'chime_c', 0.7), (tn2, 'tick', 0.6), (tn2 + 0.05, 'bass', 0.6)]
    E[18]['sfx'] = [(0.0, 'shimmer', 0.5), (0.1, 'whoosh', 0.4)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
