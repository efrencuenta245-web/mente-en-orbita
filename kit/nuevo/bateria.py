"""Reel: «Tu pila no se acaba… se cansa.» (batería de litio). Jue 5-nov-2026, 8:00. Voz Isaac.
Datos: Battery University / Cadex (capacidad tras 1 año: 25 °C → 96 % al 40 % de carga, 80 % al 100 %; 40 °C → 85 % y 65 %)."""
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
                    chart_grow, line3, dot3, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

S = M.SS
TEMA = 'bateria'
TXT = ['Tu pila no se acaba… se cansa.',
       'Cada vez que la cargas, se desgasta un poquito.',
       'Adentro, millones de iones de litio viajan de un lado a otro.',
       'Cuando cargas, se meten entre capas de grafito; cuando la usas, regresan.',
       'Y en cada viaje, unos cuantos ya no regresan.',
       'Mira esta prueba: dos pilas guardadas un año, sin usarlas.',
       'Una al 40 %: conserva el 96 % de su capacidad.',
       'La otra, al 100 %: solo el 80 %.',
       'Pero lo que más la cansa es el calor.',
       'A 40 °C, la misma pila llena se queda en 65 %.',
       'Así que cargarlo al sol, en el coche o debajo de la almohada, le quita vida.',
       'Lo ideal: ni lleno al 100, ni vacío al 0, y lejos del calor.',
       'Mándaselo a quien deja el celular cargando debajo de la almohada,',
       'porque su pila no se acaba… se cansa.']

VOZ = ['Tu pila no se acaba... se cansa.', 'Cada vez que la cargas, se desgasta un poquito.',
       'Adentro, millones de iones de litio viajan de un lado a otro.',
       'Cuando cargas, se meten entre capas de grafito; cuando la usas, regresan.',
       'Y en cada viaje, unos cuantos ya no regresan.', 'Mira esta prueba: dos pilas guardadas un año, sin usarlas.',
       'Una al cuarenta por ciento: conserva el noventa y seis por ciento de su capacidad.',
       'La otra, al cien por ciento: solo el ochenta.', 'Pero lo que más la cansa es el calor.',
       'A cuarenta grados, la misma pila llena se queda en sesenta y cinco por ciento.',
       'Así que cargarlo al sol, en el coche o debajo de la almohada, le quita vida.',
       'Lo ideal: ni lleno al cien, ni vacío al cero, y lejos del calor.',
       'Mándaselo a quien deja el celular cargando debajo de la almohada,', 'porque su pila no se acaba... se cansa.']


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


# ------------------------------------------------------------------ pantalla de batería
def scr_bateria(pct, salud, ciclos, cargando=True, aviso=None):
    def dib(d, im):
        w = 420
        f = M.font
        d.text((w / 2, 120), 'Batería', font=f('sanss', 30), fill=(200, 200, 204), anchor='mm')
        d.text((w / 2, 230), f'{pct:.0f}%', font=f('sans', 96), fill=(245, 245, 247), anchor='mm')
        x0, y0, x1, y1 = 90, 330, 330, 470
        d.rounded_rectangle((x0, y0, x1, y1), radius=22, outline=(220, 220, 224), width=5)
        d.rounded_rectangle((x1, y0 + 45, x1 + 18, y1 - 45), radius=6, fill=(220, 220, 224))
        col = (110, 230, 140) if pct > 20 else (255, 90, 80)
        d.rounded_rectangle((x0 + 10, y0 + 10, x0 + 10 + (x1 - x0 - 20) * pct / 100, y1 - 10), radius=14, fill=col)
        if cargando:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            d.polygon([(cx + 10, cy - 50), (cx - 30, cy + 8), (cx - 2, cy + 8), (cx - 12, cy + 50), (cx + 30, cy - 8), (cx + 2, cy - 8)],
                      fill=(255, 255, 255))
        d.text((44, 560), 'Capacidad máxima', font=f('sanss', 26), fill=(170, 172, 180))
        d.text((w - 44, 560), f'{salud:.0f}%', font=f('sans', 30), fill=(245, 245, 247), anchor='ra')
        d.text((44, 620), 'Ciclos de carga', font=f('sanss', 26), fill=(170, 172, 180))
        d.text((w - 44, 620), f'{ciclos}', font=f('sans', 30), fill=(245, 245, 247), anchor='ra')
        if aviso:
            d.rounded_rectangle((40, 690, w - 40, 760), radius=20, outline=(255, 90, 80), width=3)
            d.text((w / 2, 725), aviso, font=f('sanss', 28), fill=(255, 110, 100), anchor='mm')
    return P.pantalla(dib)


# ------------------------------------------------------------------ escenas
K0 = [(-4.6, dict(target=(0, 0.95, 0), dist=5.6, yaw=70, pitch=16, cy=0.56)),
      (-0.9, dict(target=(0, 0.95, 0), dist=4.4, yaw=34, pitch=10, cy=0.56)),
      (0.0, dict(target=(0, 0.95, 0), dist=3.7, yaw=24, pitch=7, cy=0.56)),
      (6.5, dict(target=(0, 0.98, 0), dist=2.9, yaw=8, pitch=5, cy=0.56))]


def s_gancho(t, fi, u, d):
    fr = Frame(cam_path(u, K0))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    x, y = fr.cam.proj([(0, 0.02, 0)])[0][0]
    D.shadow_blob(fr, x, y, 330, 70, 0.8)
    glass_type(fr.base, fr.fx, 'LITIO', 540 * S, 1130 * S, 250 * S, k=ease(seg(u, -0.6, 0.4)), fill_a=0.07)
    t1 = TT(1) - TT(0)
    pct = 18 + 82 * eout(seg(u, 0.0, t1 - 0.2), 2) if u < t1 else 100
    n = int(clamp((u - t1 - 0.4) / 0.55, 0, 6)) if u > t1 else 0
    ph = P.celular(scr_bateria(pct, 100 - n, 412 + n, cargando=True), ry=0)
    draw_objects(fr, ph)

    def ui(img, fx):
        kicker(img, 'BATERÍA DE IONES DE LITIO', 132, seg(u, 0.55, 0.95))
        title(img, fx, [('Tu pila no se acaba…', 'sans'), ('se cansa.', 'serif')], 190, seg(u, 0.15, 0.75), size=80)
        if n > 0:
            kk = eout(seg(u, t1 + 0.4 + (n - 1) * 0.55, t1 + 0.6 + (n - 1) * 0.55))
            pill(img, fx, 780, 1300, f'CICLO {412 + n}  ·  −1 %', kk, size=30, border=(255, 120, 110))
    fr.ui.append(ui)
    return finish(fr, fi)


K1 = [(-0.6, dict(target=(0.0, 0.85, 0), dist=3.0, yaw=-12, pitch=6, cy=0.5)),
      (5.0, dict(target=(0.0, 0.75, 0), dist=2.5, yaw=6, pitch=8, cy=0.5))]
BAT_C = np.array([0.0, 0.65, 0.02])


def s_rayosx(t, fi, u, d):
    fr = Frame(cam_path(u, K1))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    ph = P.celular(scr_bateria(100, 80, 640, cargando=False), interior=True)
    draw_objects(fr, ph, xray=seg(u, 0.0, 0.55), keep=('in',))
    rng = np.random.RandomState(5)
    k = seg(u, 0.8, 1.4)
    if k > 0:
        for i in range(46):
            yy = BAT_C[1] - 0.34 + 0.68 * rng.rand()
            ph_ = rng.rand() * 6.28
            xx = 0.26 * math.sin(t * 2.2 + ph_)
            dot3(fr, np.array([xx, yy, 0.06]), r=3.2, col=CYAN, a=k, glow=1.0)
    cx, cy, _ = fr.cam.p1(BAT_C)

    def ui(img, fx):
        kicker(img, 'RAYOS X · LA PILA POR DENTRO', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        doodle_circle(img, fx, cx, cy, 250, 300, t, k=eout(seg(u, 0.5, 1.0)), col=(255, 236, 160), w=6)
        pill(img, fx, 540, 300, 'MILLONES DE IONES DE LITIO', eout(seg(u, 1.2, 1.5)), size=30)
    fr.ui.append(ui)
    return finish(fr, fi)


# capas: ánodo (grafito) a la izquierda, cátodo a la derecha
K2 = [(-0.4, dict(target=(0, 1.1, 0), dist=4.6, yaw=-16, pitch=8, cy=0.5)),
      (9.0, dict(target=(0, 1.1, 0), dist=4.0, yaw=14, pitch=12, cy=0.5))]
LANES = [0.62 + 0.24 * i for i in range(5)]


def s_capas(t, fi, u, d):
    fr = Frame(cam_path(u, K2))
    space(fr, t, floor=None, bokeh=0.9)
    kin = eout(seg(u, -0.1, 0.6))
    for yy in [0.5 + 0.24 * i for i in range(6)]:
        for (xa, xb, col) in ((-1.25, -0.25, (190, 196, 210)), (0.25, 1.25, (255, 190, 120))):
            line3(fr, [np.array([xa, yy, -0.3]), np.array([xb, yy, -0.3]), np.array([xb, yy, 0.3]), np.array([xa, yy, 0.3]),
                       np.array([xa, yy, -0.3])], col=col, w=1.8, a=0.85 * kin, glow=0.6, frac=kin)
            if col[0] < 200:
                for xi in np.linspace(xa + 0.08, xb - 0.08, 8):
                    dot3(fr, np.array([xi, yy, 0.0]), r=2.2, col=(200, 205, 220), a=0.6 * kin, glow=0.2)
    for yy in np.linspace(0.45, 1.75, 14):
        line3(fr, [np.array([0, yy, 0]), np.array([0, yy + 0.05, 0])], col=(150, 150, 160), w=1.4, a=0.6 * kin, glow=0)
    # fase de los iones: 0 = cátodo (derecha), 1 = ánodo (izquierda)
    t3, t3m, t4 = TT(3), (TT(3) + TE(3)) / 2, TT(4)
    if t < t3m:
        p = ease(seg(t, t3 + 0.2, t3m))
    elif t < t4:
        p = 1 - ease(seg(t, t3m + 0.1, t4))
    else:
        tm = (t4 + TE(4)) / 2
        p = ease(seg(t, t4, tm)) if t < tm else 1 - ease(seg(t, tm, TE(4)))
    rng = np.random.RandomState(9)
    stuck = set([3, 11, 18, 27])
    for i in range(32):
        lane = LANES[i % 4] + 0.12
        z = -0.25 + 0.5 * rng.rand()
        jitter = rng.rand() * 0.35
        xr, xl = 0.45 + jitter * 1.8, -1.15 + jitter * 1.8
        pp = p
        red = False
        if i in stuck and t > t4 + 0.3:
            pp, red = max(p, 1.0), True
        x = lerp(xr, xl, pp)
        dot3(fr, np.array([x, lane, z]), r=4.5 if red else 3.6, col=(255, 80, 70) if red else CYAN, a=1.0, glow=1.2)
    sc = fr.cam.p1(np.array([-0.75, LANES[1] + 0.12, 0]))

    def ui(img, fx):
        kicker(img, 'CAPAS DE GRAFITO  ·  SEPARADOR  ·  CÁTODO', 150, seg(u, 0.0, 0.3))
        carg = t < t3m or (t4 <= t < (t4 + TE(4)) / 2)
        pill(img, fx, 540, 300, 'CARGANDO  ←' if carg else 'USANDO  →', eout(seg(u, 0.2, 0.5)), size=32,
             border=CYAN if carg else (255, 214, 150))
        if t > t4 + 0.3:
            doodle_circle(img, fx, sc[0], sc[1], 230, 140, t, k=eout(seg(t, t4 + 0.4, t4 + 0.9)), col=(255, 236, 160), w=6)
            pill(img, fx, 540, 1360, 'SE QUEDAN ATRAPADOS', eout(seg(t, t4 + 0.6, t4 + 0.9)), size=30, border=(255, 90, 80))
    fr.ui.append(ui)
    return finish(fr, fi)


K3 = [(-0.4, dict(target=(0, 0.75, 0), dist=4.4, yaw=-20, pitch=10, cy=0.56)),
      (4.0, dict(target=(0, 0.75, 0), dist=3.8, yaw=8, pitch=8, cy=0.56))]


def s_dos(t, fi, u, d):
    fr = Frame(cam_path(u, K3))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=0.9, beam=0.35)
    for x in (-0.6, 0.6):
        xx, yy = fr.cam.proj([(x, 0.02, 0)])[0][0]
        D.shadow_blob(fr, xx, yy, 170, 40, 0.7)
    k = eout(seg(u, 0.3, 1.2))
    ms = P.pila(0.4 * k, x=-0.6, col_fill=CYAN) + P.pila(1.0 * k, x=0.6, col_fill=(236, 238, 242))
    draw_objects(fr, ms)
    a = fr.cam.p1(np.array([-0.6, 1.2, 0]))
    b = fr.cam.p1(np.array([0.6, 1.2, 0]))
    mes = int(clamp((u - 1.0) / 0.22, 0, 11))
    meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']

    def ui(img, fx):
        kicker(img, 'LA PRUEBA · 1 AÑO GUARDADAS A 25 °C', 150, seg(u, 0.0, 0.3))
        pill(img, fx, a[0], a[1] - 40, '40 %', eout(seg(u, 0.4, 0.7)), size=36, border=CYAN)
        pill(img, fx, b[0], b[1] - 40, '100 %', eout(seg(u, 0.6, 0.9)), size=36, border=(236, 238, 242))
        if u > 1.0:
            M.glass_type(img, fx, meses[mes], 540, 1440, 120, k=1.0, fill_a=0.08)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_grafica(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=14, cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    t7 = TT(7) - TT(6)

    def ui(img, fx):
        kicker(img, 'CAPACIDAD QUE CONSERVA · %', 150, seg(u, -0.1, 0.2))
        chart_grow(img, fx, (110, 300, 970, 1220), [96, 80], ['AL 40 %', 'AL 100 %'], TT(6) - 0.1, t,
                   title_txt='1 AÑO · 25 °C', tag='BATTERY UNIVERSITY', line=False)
        doodle_circle(img, fx, 723, 900, 190, 300, t, k=eout(seg(u, t7 + 0.3, t7 + 0.8)), col=(255, 236, 160), w=6)
        pill(img, fx, 723, 1300, '−20 %', eout(seg(u, t7 + 0.6, t7 + 0.9)), size=44, border=(255, 90, 80))
    fr.ui.append(ui)
    return finish(fr, fi)


K5 = [(-0.4, dict(target=(0, 0.8, 0), dist=3.6, yaw=-10, pitch=8, cy=0.55)),
      (6.0, dict(target=(0, 0.8, 0), dist=3.0, yaw=10, pitch=6, cy=0.55))]


def s_calor(t, fi, u, d):
    fr = Frame(cam_path(u, K5))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8, beam=0.3)
    t9 = TT(9) - TT(8)
    hot = eout(seg(u, 0.3, 1.6))
    lvl = 1.0 if u < t9 + 0.6 else lerp(1.0, 0.65, eout(seg(u, t9 + 0.6, t9 + 2.4)))
    glass_type(fr.base, fr.fx, '65%' if u > t9 + 2.4 else '', 540 * S, 1150 * S, 230 * S, k=eout(seg(u, t9 + 2.4, t9 + 2.9)), fill_a=0.06)
    draw_objects(fr, P.pila(lvl, x=0, col_fill=M.mixc((236, 238, 242), (255, 120, 80), hot), caliente=hot * 0.6))
    P.ondas_calor(fr, t, 0, 1.1, 1.9, 0.8, k=hot)
    temp = 25 + 15 * eout(seg(u, 0.4, t9 + 0.5))

    def ui(img, fx):
        kicker(img, 'EL ENEMIGO: EL CALOR', 150, seg(u, 0.0, 0.3), col=(255, 160, 130))
        P.termometro(img, fx, 160, 1250, 520, (temp - 10) / 35, f'{temp:.0f} °C', k=eout(seg(u, 0.2, 0.6)))
        pill(img, fx, 780, 300, f'CAPACIDAD {lvl * 100:.0f} %', eout(seg(u, t9 + 0.4, t9 + 0.7)), size=32, border=(255, 90, 80))
    fr.ui.append(ui)
    out = finish(fr, fi)
    a = 0.10 * hot
    o = out.astype(np.float32)
    o = o * (1 - a) + np.array([255, 70, 30], np.float32) * a * (o.mean(2, keepdims=True) / 255 + 0.2)
    return o.clip(0, 255).astype(np.uint8)


K6 = [(-0.4, dict(target=(0, 0.25, 0), dist=3.6, yaw=-28, pitch=34, cy=0.58)),
      (6.0, dict(target=(0, 0.25, 0), dist=3.1, yaw=-8, pitch=40, cy=0.58))]


def s_almohada(t, fi, u, d, titulo=False):
    fr = Frame(cam_path(u, K6))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9)
    hot = eout(seg(u, 0.5, 2.0))
    ms = P.almohada() + P.celular(scr_bateria(100, 80, 640, aviso='Temperatura alta'), acostado=True, off=(0.05, 0.34, 0.05), ry=12)
    draw_objects(fr, ms)
    P.ondas_calor(fr, t, 0.05, 0.45, 1.2, 0.9, k=hot)
    nw = len(TXT[10].split())
    tw = (TE(10) - TT(10)) / nw

    def ui(img, fx):
        if not titulo:
            kicker(img, 'LO QUE MÁS LA CANSA', 150, seg(u, 0.0, 0.3), col=(255, 160, 130))
            for j, (txt, w0) in enumerate((('AL SOL', 4), ('EN EL COCHE', 7), ('BAJO LA ALMOHADA', 11))):
                ta = w0 * tw
                P.pill_tachada(img, fx, 540, 290 + j * 96, txt, seg(u, ta - 0.3, ta), seg(u, ta + 0.25, ta + 0.6), t, size=32)
        else:
            title(img, fx, [('Mándaselo a quien', 'sans'), ('carga bajo la almohada.', 'serif')], 190, seg(u, 0.0, 0.5), size=72)
    fr.ui.append(ui)
    out = finish(fr, fi)
    a = 0.08 * hot
    o = out.astype(np.float32)
    o = o * (1 - a) + np.array([255, 70, 30], np.float32) * a * (o.mean(2, keepdims=True) / 255 + 0.2)
    return o.clip(0, 255).astype(np.uint8)


def s_almohada_t(t, fi, u, d):
    return s_almohada(t, fi, u, d, titulo=True)


def s_ideal(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=12, cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9)
    k = eout(seg(u, 0.0, 0.5))

    def ui(img, fx):
        kicker(img, 'LO IDEAL', 150, seg(u, 0.0, 0.3), col=(140, 240, 170))
        if k <= 0.01:
            return
        d_ = ImageDraw.Draw(img)
        df = ImageDraw.Draw(fx)
        x0, x1, y0, y1 = 130, 950, 700, 820
        d_.rounded_rectangle((x0, y0, x1, y1), radius=60, outline=M.scale_c(WHITE, 0.85 * k), width=5)
        w = x1 - x0
        for a_, b_, col in ((0, 0.12, (255, 80, 70)), (0.12, 0.88, (110, 230, 140)), (0.88, 1.0, (255, 80, 70))):
            xa, xb = x0 + 12 + (w - 24) * a_, x0 + 12 + (w - 24) * min(b_, k)
            if xb > xa:
                d_.rectangle((xa, y0 + 14, xb, y1 - 14), fill=M.scale_c(col, 0.85))
        df.rounded_rectangle((x0, y0, x1, y1), radius=60, outline=(60, 120, 80), width=12)
        for v, xx in (('0 %', x0), ('100 %', x1)):
            d_.text((xx, y1 + 50), v, font=M.font('mono', 36), fill=M.scale_c(WHITE, k), anchor='mm')
        m = 0.5 + 0.22 * math.sin(t * 1.6)
        mx = x0 + 12 + (w - 24) * m
        d_.polygon([(mx, y0 - 20), (mx - 22, y0 - 60), (mx + 22, y0 - 60)], fill=WHITE)
        title(img, fx, [('Ni lleno al 100,', 'sans'), ('ni vacío al 0.', 'serif')], 330, seg(u, 0.2, 0.8), size=78)
        pill(img, fx, 540, 1080, 'Y LEJOS DEL CALOR', eout(seg(u, 2.2, 2.5)), size=34, border=(255, 160, 130))
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55), sfx=[]),
           dict(desde=2, fn=s_rayosx, tr='zoom', c=(0.5, 0.62), sfx=[(0.0, 'shimmer', 0.9), (0.5, 'scribble', 0.8), (1.2, 'tick', 0.6)]),
           dict(desde=3, fn=s_capas, tr='push', sfx=[(0.2, 'whoosh_suave', 0.4), (0.25, 'tick', 0.5)]),
           dict(desde=5, fn=s_dos, tr='flash', sfx=[(0.4, 'chime_a', 0.6), (0.6, 'chime_b', 0.6)]),
           dict(desde=6, fn=s_grafica, tr='wipe', sfx=[(0.15, 'chime_a', 0.9), (0.43, 'chime_c', 0.9)]),
           dict(desde=8, fn=s_calor, tr='whip', sfx=[(0.3, 'riser', 0.5), (0.4, 'whoosh_suave', 0.4)]),
           dict(desde=10, fn=s_almohada, tr='flash'),
           dict(desde=11, fn=s_ideal, tr='whip_izq', sfx=[(0.2, 'chime_b', 0.6), (2.2, 'tick', 0.6)]),
           dict(desde=12, fn=s_almohada_t, tr='ritmo'),
           dict(desde=13, loop=True, tr='zoom')]


def _sfx_dinamicos():
    """Eventos que dependen de los tiempos reales (ciclos del gancho, tachones, etc.)."""
    T = montaje.CTX.get('T')
    if not T:
        return
    t1 = T[1][0] - T[0][0]
    ESCENAS[0]['sfx'] = [(0.15, 'whoosh', 0.3)] + [(t1 + 0.4 + i * 0.55, 'tick2', 0.6) for i in range(6)]
    t4 = T[4][0] - T[3][0]
    ESCENAS[2]['sfx'] += [(t4 + 0.4, 'scribble', 0.8), (t4 + 0.6, 'bass', 0.6)]
    t7 = T[7][0] - T[6][0]
    ESCENAS[4]['sfx'] += [(t7 + 0.3, 'scribble', 0.8), (t7 + 0.6, 'tick', 0.7)]
    t9 = T[9][0] - T[8][0]
    ESCENAS[5]['sfx'] += [(t9 + 0.4, 'tick', 0.6), (t9 + 2.4, 'thud', 0.7)]
    nw = len(TXT[10].split())
    tw = (T[10][1] - T[10][0]) / nw
    ESCENAS[6]['sfx'] = sum([[(w0 * tw - 0.3, 'tick', 0.6), (w0 * tw + 0.25, 'scribble', 0.7)] for w0 in (4, 7, 11)], [])


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
