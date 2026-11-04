"""Reel: «Tu estufa calienta la olla… sin calentarse ella.» (estufa de inducción). Jue 5-nov-2026, 19:00. Voz Isaac.
Datos: bobina de cobre con corriente alterna de ~25–50 kHz (Wikipedia/EPRI); corrientes de Foucault en ollas
magnéticas; el vidrio cerámico conduce mal el calor (EPRI); eficiencia 84 % (DOE) contra ~40 % del gas."""
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
                    chart_grow, line3, dot3, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

S = M.SS
M3 = M.M3
TEMA = 'induccion'
TXT = ['Tu estufa calienta la olla… sin calentarse ella.',
       'Y no tiene fuego, ni una resistencia roja.',
       'Debajo del vidrio hay una bobina de cobre.',
       'Por ella pasa una corriente que cambia de dirección decenas de miles de veces por segundo.',
       'Eso crea un campo magnético que sube y baja sin parar.',
       'Cuando pones una olla de hierro, ese campo mueve corrientes dentro del metal.',
       'Se llaman corrientes de Foucault, y calientan la olla desde adentro.',
       'El vidrio casi no se calienta: solo le llega el calor que le pasa la olla.',
       'Pero aquí está el error: pon una olla de aluminio, o tu comal de barro… y no pasa nada.',
       'Para que funcione, la olla tiene que ser magnética.',
       'El truco: acércale un imán; si se pega, sirve.',
       'Y aprovecha como el 84 % de la energía; el gas, como el 40 %.',
       'Mándaselo a quien cree que es una parrilla eléctrica,',
       'porque su estufa calienta la olla… sin calentarse ella.']
VOZ = TXT[:11] + ['Y aprovecha como el ochenta y cuatro por ciento de la energía; el gas, como el cuarenta.'] + TXT[12:]
COBRE = (214, 140, 80)
NARANJA = (255, 150, 60)
GY = 0.31  # altura del vidrio


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


def wt(i, k):
    """Tiempo aproximado de la palabra k de la frase i."""
    n = len(TXT[i].split())
    return TT(i) + (TE(i) - TT(i)) * k / n


# ------------------------------------------------------------------ objetos
def estufa():
    base = named(M3.box(2.1, 0.25, 1.4, (46, 46, 50), shadow=0, base=True, gloss=0.3), 'estufa', rim=0.5)
    vidrio = named(M3.box(2.1, 0.06, 1.4, (10, 10, 13), shadow=0, base=True, gloss=0.95).tf(t=(0, 0.25, 0)), 'vidrio',
                   rim=0.7, gloss=0.95)
    return [base, vidrio]


def olla(tipo='acero', calor=0.0, y=GY, x=0.0):
    if tipo == 'comal':
        c = named(M3.cyl(0.52, 0.06, (150, 82, 52), n=40, shadow=0, gloss=0.15, y0=0), 'olla', rim=0.4)
        return P.tfk([c], t=(x, y, 0))
    col = (150, 154, 162) if tipo == 'aluminio' else (78, 80, 88)
    cuerpo = named(M3.cyl(0.42, 0.5, col, n=40, shadow=0, gloss=0.6, y0=0), 'olla', rim=0.7, gloss=0.6)
    asas = [named(M3.box(0.16, 0.05, 0.08, (40, 40, 44), shadow=0, base=True).tf(t=(sx * 0.5, 0.38, 0)), 'asa') for sx in (-1, 1)]
    out = [cuerpo] + asas
    if calor > 0.01:
        fondo = M3.cyl(0.425, 0.12, M.mixc(col, NARANJA, calor), n=40, shadow=0, gloss=0.3, y0=0)
        fondo = named(fondo, 'fondo', glow=M.scale_c(NARANJA, 0.9 * calor), rim=0.2)
        out.append(fondo)
    return P.tfk(out, t=(x, y, 0))


def iman(x, y, z=0.0):
    a = named(M3.box(0.12, 0.12, 0.2, (210, 52, 48), shadow=0, base=True, gloss=0.6).tf(t=(0, 0, 0.1)), 'iman', rim=0.6)
    b = named(M3.box(0.12, 0.12, 0.2, (52, 86, 200), shadow=0, base=True, gloss=0.6).tf(t=(0, 0, -0.1)), 'iman', rim=0.6)
    return P.tfk([a, b], ry=90, t=(x, y, z))


def bobina(fr, t, k=1.0, flujo=0.0):
    """Espiral de cobre bajo el vidrio; `flujo` mueve puntos de corriente que cambian de sentido."""
    if k <= 0.01:
        return
    th = np.linspace(0, 2 * math.pi * 7, 420)
    r = 0.06 + 0.36 * th / th[-1]
    pts = [np.array([rr * math.cos(a), 0.22, rr * math.sin(a)]) for rr, a in zip(r, th)]
    line3(fr, pts, col=COBRE, w=3.2, a=k, glow=0.9 * k, frac=k)
    if flujo > 0.01:
        sgn = 1 if math.sin(t * 2 * math.pi * 3.0) > 0 else -1
        for j in range(14):
            s = ((j / 14) + sgn * t * 0.9) % 1.0
            i = int(s * (len(pts) - 1))
            dot3(fr, pts[i], r=4.5, col=CYAN if sgn > 0 else (255, 214, 150), a=flujo, glow=1.2)


def campo(fr, t, k=1.0, alto=0.75, atraviesa=False):
    """Líneas de campo que suben y bajan (alterna)."""
    if k <= 0.01:
        return
    puls = 0.75 + 0.25 * math.sin(t * 2 * math.pi * 3.0)
    for j in range(10):
        ph = j * math.pi / 5
        for R in (0.18, 0.32):
            pts = []
            for s in np.linspace(0, math.pi, 40):
                rr = R + (R + 0.25) * (1 - math.cos(s)) / 2
                yy = 0.22 + alto * puls * math.sin(s) * (0.6 + R)
                pts.append(np.array([rr * math.cos(ph), yy, rr * math.sin(ph)]))
            line3(fr, pts, col=(200, 230, 255), w=1.4, a=0.55 * k, glow=0.7 * k)


def foucault(fr, t, k=1.0, y=GY + 0.05):
    if k <= 0.01:
        return
    for j, R in enumerate((0.12, 0.22, 0.32)):
        sgn = 1 if j % 2 == 0 else -1
        th0 = sgn * t * 6 + j
        pts = [np.array([R * math.cos(a), y, R * math.sin(a)]) for a in np.linspace(th0, th0 + 2 * math.pi * 0.85, 50)]
        line3(fr, pts, col=NARANJA, w=3.0, a=k, glow=1.3 * k)


def vapor(fr, t, k=1.0, y0=GY + 0.55):
    P.ondas_calor(fr, t, 0.0, y0, y0 + 0.8, 0.6, k=k, col=(235, 235, 240), n=4)


# ------------------------------------------------------------------ escenas
K0 = [(-4.6, dict(target=(0, 0.55, 0), dist=5.4, yaw=-70, pitch=30, cy=0.6)),
      (-0.9, dict(target=(0, 0.55, 0), dist=4.2, yaw=-36, pitch=24, cy=0.6)),
      (0.0, dict(target=(0, 0.55, 0), dist=3.7, yaw=-24, pitch=22, cy=0.6)),
      (7.0, dict(target=(0, 0.5, 0), dist=3.0, yaw=-6, pitch=26, cy=0.6))]


def s_gancho(t, fi, u, d, titulo=True):
    fr = Frame(cam_path(u, K0))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    x, y = fr.cam.proj([(0, 0.02, 0)])[0][0]
    D.shadow_blob(fr, x, y, 420, 110, 0.8)
    if titulo:
        glass_type(fr.base, fr.fx, 'CALOR', 540 * S, 640 * S, 230 * S, k=ease(seg(u, -0.6, 0.4)), fill_a=0.06)
    draw_objects(fr, estufa() + olla(calor=0.0))
    vapor(fr, t, k=0.9)
    t1 = TT(1) - TT(0)

    def ui(img, fx):
        if titulo:
            kicker(img, 'ESTUFA DE INDUCCIÓN', 132, seg(u, 0.55, 0.95))
            title(img, fx, [('Tu estufa calienta la olla…', 'sans'), ('sin calentarse ella.', 'serif')], 190, seg(u, 0.15, 0.75), size=70)
            for j, (txt, k0) in enumerate((('FUEGO', 3), ('RESISTENCIA ROJA', 6))):
                ta = wt(1, k0) - TT(0)
                P.pill_tachada(img, fx, 540, 1250 + j * 96, txt, seg(u, ta - 0.3, ta), seg(u, ta + 0.2, ta + 0.55), t, size=32)
        else:
            title(img, fx, [('Mándaselo a quien cree', 'sans'), ('que es una parrilla.', 'serif')], 190, seg(u, 0.0, 0.5), size=72)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_mandalo(t, fi, u, d):
    return s_gancho(t, fi, u + 3.0, d, titulo=False)


K1 = [(-0.4, dict(target=(0, 0.35, 0), dist=3.0, yaw=-20, pitch=38, cy=0.55)),
      (9.0, dict(target=(0, 0.4, 0), dist=2.6, yaw=12, pitch=30, cy=0.55))]


def s_bobina(t, fi, u, d):
    fr = Frame(cam_path(u, K1))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    xr = seg(u, 0.0, 0.5)
    draw_objects(fr, estufa(), xray=xr, keep=('estufa',))
    bobina(fr, t, k=eout(seg(u, 0.3, 1.4)), flujo=seg(t, TT(3), TT(3) + 0.4))
    campo(fr, t, k=seg(t, TT(4), TT(4) + 0.6))

    def ui(img, fx):
        kicker(img, 'DEBAJO DEL VIDRIO', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        pill(img, fx, 540, 300, 'BOBINA DE COBRE', eout(seg(u, 0.6, 0.9)), size=32, border=COBRE)
        k3 = eout(seg(t, TT(3) + 1.5, TT(3) + 1.8))
        if k3 > 0 and t < TT(4):
            pill(img, fx, 540, 1330, 'DECENAS DE MILES DE VECES / SEG', k3, size=30, border=CYAN)
        if t >= TT(4):
            pill(img, fx, 540, 1330, 'CAMPO MAGNÉTICO QUE VA Y VIENE', eout(seg(t, TT(4) + 0.4, TT(4) + 0.7)), size=30)
    fr.ui.append(ui)
    return finish(fr, fi)


K2 = [(-0.4, dict(target=(0, 0.5, 0), dist=3.3, yaw=16, pitch=24, cy=0.56)),
      (9.0, dict(target=(0, 0.5, 0), dist=2.8, yaw=-10, pitch=18, cy=0.56))]


def s_foucault(t, fi, u, d, termica=False):
    fr = Frame(cam_path(u, K2))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    caida = eout(seg(u, 0.0, 0.5), 3)
    calor = eout(seg(t, TT(6), TT(6) + 2.5)) if not termica else 1.0
    draw_objects(fr, estufa() + olla(calor=calor, y=GY + 0.6 * (1 - caida)))
    if not termica:
        bobina(fr, t, k=1.0, flujo=0.6)
        campo(fr, t, k=0.8)
        foucault(fr, t, k=seg(u, 1.4, 2.2))
    else:
        vapor(fr, t, k=0.9)
    pc = fr.cam.p1(np.array([0, GY + 0.3, 0]))
    gc = fr.cam.p1(np.array([0.78, GY + 0.04, 0.3]))

    def ui(img, fx):
        if not termica:
            kicker(img, 'OLLA DE HIERRO', 150, seg(u, 0.0, 0.3))
            k6 = eout(seg(t, TT(6) + 0.2, TT(6) + 0.5))
            pill(img, fx, 540, 300, 'CORRIENTES DE FOUCAULT', k6, size=32, border=NARANJA)
        else:
            kicker(img, 'VISTA TÉRMICA', 150, seg(u, 0.0, 0.3), col=(255, 190, 130))
            pill(img, fx, pc[0], pc[1] - 330, 'OLLA: CALIENTE', eout(seg(u, 0.3, 0.6)), size=30, border=NARANJA)
            pill(img, fx, gc[0] - 60, gc[1] + 150, 'VIDRIO: CASI FRÍO', eout(seg(u, 1.2, 1.5)), size=30, border=CYAN)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if termica:  # falsa cámara térmica: luminancia → paleta azul-rojo-amarillo, la olla en caliente
        o = out.astype(np.float32) / 255
        lum = o.mean(2)
        cold = np.stack([0.1 + 0.2 * lum, 0.25 + 0.5 * lum, 0.6 + 0.4 * lum], 2)
        ys, xs = np.mgrid[0:M.H, 0:M.W]
        hot_m = np.clip(1 - np.hypot((xs - pc[0]) / 330, (ys - pc[1]) / 300), 0, 1) ** 0.7
        hot = np.stack([0.9 + 0.1 * lum, 0.25 + 0.7 * lum, 0.05 + 0.3 * lum], 2)
        mix = cold * (1 - hot_m[..., None]) + hot * hot_m[..., None]
        k = eout(seg(u, -0.2, 0.3))
        out = ((o * (1 - k) + mix * lum[..., None] ** 0.3 * k) * 255).clip(0, 255).astype(np.uint8)
    return out


def s_termica(t, fi, u, d):
    return s_foucault(t, fi, u, d, termica=True)


K4 = [(-0.4, dict(target=(0, 0.5, 0), dist=3.4, yaw=-12, pitch=22, cy=0.56)),
      (6.0, dict(target=(0, 0.5, 0), dist=3.0, yaw=10, pitch=20, cy=0.56))]


def s_error(t, fi, u, d):
    fr = Frame(cam_path(u, K4))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    t_comal = wt(8, 11)
    tipo = 'aluminio' if t < t_comal - 0.15 else 'comal'
    caida = eout(seg(t, (TT(8) + 0.9) if tipo == 'aluminio' else t_comal - 0.15, (TT(8) + 1.3) if tipo == 'aluminio' else t_comal + 0.25), 3)
    draw_objects(fr, estufa())
    campo(fr, t, k=0.6)
    draw_objects(fr, olla(tipo, y=GY + 0.6 * (1 - caida)))
    pc = fr.cam.p1(np.array([0, GY + 0.25, 0]))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, 0.0, 0.3), col=(255, 150, 140))
        pill(img, fx, 540, 300, 'OLLA DE ALUMINIO' if tipo == 'aluminio' else 'COMAL DE BARRO', eout(seg(u, 0.8, 1.1)), size=32,
             border=(200, 200, 210))
        kx = seg(t, wt(8, 15), wt(8, 15) + 0.4)
        if kx > 0:
            N_ = P.N
            N_.doodle_x(img, fx, pc[0], pc[1], 150, t, kx)
            pill(img, fx, 540, 1330, 'NO CALIENTA', eout(kx), size=40, border=RED)
    fr.ui.append(ui)
    return finish(fr, fi)


K5 = [(-0.4, dict(target=(0.2, 0.55, 0), dist=3.2, yaw=-26, pitch=16, cy=0.56)),
      (7.0, dict(target=(0.3, 0.55, 0), dist=2.7, yaw=-8, pitch=14, cy=0.56))]


def s_iman(t, fi, u, d):
    fr = Frame(cam_path(u, K5))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8, beam=0.3)
    t_i = wt(10, 3)
    pega = seg(t, t_i + 0.2, t_i + 1.0)
    mx = lerp(1.6, 0.51, ease(pega) ** 1.6)
    draw_objects(fr, estufa() + olla(calor=0.0) + iman(mx, GY + 0.25, 0.0))
    if pega >= 1.0:
        P.ondas_calor(fr, t, 0.55, GY + 0.45, GY + 0.75, 0.15, k=0.0)
    mc = fr.cam.p1(np.array([0.55, GY + 0.32, 0]))

    def ui(img, fx):
        kicker(img, 'LA OLLA TIENE QUE SER MAGNÉTICA', 150, seg(u, 0.0, 0.3))
        if t >= TT(10):
            pill(img, fx, 540, 300, 'EL TRUCO: UN IMÁN', eout(seg(t, TT(10), TT(10) + 0.3)), size=32, border=(255, 236, 160))
        if pega >= 1.0:
            doodle_circle(img, fx, mc[0], mc[1], 110, 90, t, k=eout(seg(t, t_i + 1.0, t_i + 1.4)), col=(140, 240, 170), w=6)
            pill(img, fx, 540, 1330, 'SI SE PEGA, SIRVE', eout(seg(t, t_i + 1.1, t_i + 1.4)), size=38, border=(120, 235, 160))
    fr.ui.append(ui)
    return finish(fr, fi)


def s_grafica(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=14, cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'ENERGÍA QUE LLEGA A LA OLLA · %', 150, seg(u, -0.1, 0.2))
        chart_grow(img, fx, (110, 300, 970, 1220), [40, 84], ['GAS', 'INDUCCIÓN'], TT(11) - 0.1, t,
                   title_txt='EFICIENCIA', tag='DOE · APROX.', line=False)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.62), sfx=[]),
           dict(desde=2, fn=s_bobina, tr='zoom', sfx=[(0.0, 'shimmer', 0.8), (0.6, 'tick', 0.6)]),
           dict(desde=5, fn=s_foucault, tr='whip', sfx=[(0.45, 'thud', 0.8)]),
           dict(desde=7, fn=s_termica, tr='flash', sfx=[(0.3, 'tick', 0.6), (1.2, 'tick2', 0.6)]),
           dict(desde=8, fn=s_error, tr='wipe', sfx=[(0.8, 'tick', 0.6)]),
           dict(desde=9, fn=s_iman, tr='whip_izq', sfx=[]),
           dict(desde=11, fn=s_grafica, tr='corte', sfx=[(0.15, 'chime_a', 0.9), (0.43, 'chime_c', 0.9)]),
           dict(desde=12, fn=s_mandalo, tr='ritmo'),
           dict(desde=13, loop=True, tr='zoom')]


def _sfx_dinamicos():
    ESCENAS[0]['sfx'] = [(0.15, 'whoosh', 0.3)] + sum([[(wt(1, k) - TT(0) - 0.3, 'tick', 0.6), (wt(1, k) - TT(0) + 0.2, 'scribble', 0.7)]
                                                       for k in (3, 6)], [])
    ESCENAS[1]['sfx'] += [(TT(3) - TT(2), 'whoosh_suave', 0.4), (TT(3) + 1.5 - TT(2), 'tick2', 0.6), (TT(4) - TT(2), 'whoosh_suave', 0.4)]
    ESCENAS[2]['sfx'] += [(TT(6) - TT(5) + 0.2, 'tick', 0.6), (TT(6) - TT(5) + 0.3, 'riser', 0.4)]
    ESCENAS[4]['sfx'] += [(wt(8, 11) - TT(8) - 0.15, 'thud', 0.7), (wt(8, 15) - TT(8), 'scribble', 0.8), (wt(8, 15) - TT(8) + 0.1, 'bass', 0.7)]
    ti = wt(10, 3) - TT(9)
    ESCENAS[5]['sfx'] = [(TT(10) - TT(9), 'tick', 0.6), (ti + 0.2, 'whoosh', 0.5), (ti + 1.0, 'slap', 0.9), (ti + 1.1, 'chime_b', 0.7)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
