"""Reel: «Tu refri no hace frío… saca el calor.» (refrigerador). Vie 6-nov-2026, 19:00. Voz Isaac.
Datos: el refrigerante absorbe calor al evaporarse en los tubos de adentro y lo suelta en el condensador de atrás
(por eso atrás está caliente); FDA/USDA: refri a 4 °C o menos y congelador a −18 °C."""
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
                    line3, dot3, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

S = M.SS
M3 = M.M3
TEMA = 'refri'
TXT = ['Tu refri no hace frío… saca el calor.',
       'El frío no se fabrica: lo que existe es el calor, y el refri lo cambia de lugar.',
       'Adentro corre un líquido llamado refrigerante.',
       'En los tubos de adentro se evapora, y al evaporarse le roba el calor a tu comida.',
       'Igual que el sudor te enfría la piel.',
       'Luego el compresor, ese que zumba, lo aprieta y lo calienta todavía más.',
       'Y por los tubos de atrás suelta todo ese calor en tu cocina.',
       'Por eso la parte de atrás del refri siempre está caliente.',
       'Pero aquí está el error: si dejas la puerta abierta para refrescarte, la cocina se calienta más.',
       'Porque el refri saca calor… y además le suma el de su motor.',
       'Y si lo pegas a la pared, ese calor no tiene por dónde salir, y gasta más luz.',
       'Adentro debe estar a 4 °C o menos; el congelador, a −18 °C.',
       'Mándaselo a quien abre el refri para echarse aire,',
       'porque su refri no hace frío… saca el calor.']
VOZ = TXT[:11] + ['Adentro debe estar a cuatro grados o menos; el congelador, a dieciocho bajo cero.'] + TXT[12:]
NARANJA = (255, 140, 60)
FRIO = (120, 200, 255)


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


def wt(i, k):
    n = len(TXT[i].split())
    return TT(i) + (TE(i) - TT(i)) * k / n


# ------------------------------------------------------------------ objetos
def refri(puerta=0.0, motor=0.0):
    col = (176, 180, 188)
    body = named(M3.rbox(1.0, 2.0, 0.9, 0.06, col, n=4, shadow=0, gloss=0.6), 'refri', rim=0.7, gloss=0.6)
    gap = named(M3.box(0.98, 0.02, 0.02, (30, 30, 34), shadow=0, base=True).tf(t=(0, 1.42, 0.455)), 'refri')
    asas = [named(M3.box(0.04, 0.42, 0.05, (60, 62, 68), shadow=0, base=True, gloss=0.7).tf(t=(0.4, y, 0.48)), 'refri')
            for y in (1.52, 0.86)]
    out = [body, gap] + asas
    comp = named(M3.cyl(0.14, 0.26, M.mixc((30, 30, 34), (255, 120, 60), motor), n=24, shadow=0, gloss=0.5, y0=0)
                 .tf(t=(0.25, 0.02, -0.6)), 'comp', rim=0.5)
    if motor > 0.05:
        comp.glow = M.scale_c((255, 120, 60), 0.6 * motor)
    out.append(comp)
    if puerta > 0.01:
        # hueco iluminado y la puerta de abajo girando sobre la bisagra izquierda
        hueco = named(M3.box(0.86, 1.25, 0.02, (210, 230, 245), shadow=0, base=True).tf(t=(0, 0.12, 0.452)), 'luz')
        hueco.glow = M.scale_c((200, 230, 255), 0.5 * puerta)
        hueco.flat = True
        out.append(hueco)
        for y in (0.45, 0.8, 1.1):
            out.append(named(M3.box(0.84, 0.015, 0.03, (150, 170, 190), shadow=0, base=True).tf(t=(0, y, 0.465)), 'luz'))
        door = M3.box(1.0, 1.36, 0.06, col, shadow=0, base=True, gloss=0.6).tf(t=(0.5, 0.04, 0.0))
        door = door.tf(ry=-100 * ease(puerta)).tf(t=(-0.5, 0, 0.48))
        out.append(named(door, 'refri', rim=0.7, gloss=0.6))
    return out


def circuito():
    """Recorrido del refrigerante: evaporador (adentro arriba) → compresor → condensador (atrás) → de regreso."""
    pts = []
    for i, y in enumerate(np.linspace(1.85, 1.55, 5)):  # evaporador (serpentín adentro)
        xs = (-0.35, 0.35) if i % 2 == 0 else (0.35, -0.35)
        pts += [np.array([xs[0], y, -0.32]), np.array([xs[1], y, -0.32])]
    pts += [np.array([-0.35, 1.5, -0.42]), np.array([-0.35, 0.2, -0.42]), np.array([0.25, 0.14, -0.6])]  # baja al compresor
    for i, y in enumerate(np.linspace(0.35, 1.85, 9)):  # condensador (atrás, afuera)
        xs = (0.4, -0.4) if i % 2 == 0 else (-0.4, 0.4)
        pts += [np.array([xs[0], y, -0.52]), np.array([xs[1], y, -0.52])]
    pts += [np.array([0.4, 1.95, -0.45]), np.array([0.35, 1.85, -0.32])]  # capilar de regreso
    return pts


CIR = circuito()
_L = np.cumsum([0] + [np.linalg.norm(b - a) for a, b in zip(CIR[:-1], CIR[1:])])
I_COMP = 13  # índice del compresor en CIR


def _en(s):
    d = s * _L[-1]
    i = int(np.searchsorted(_L, d) - 1)
    i = max(0, min(i, len(CIR) - 2))
    f = (d - _L[i]) / max(1e-6, _L[i + 1] - _L[i])
    return CIR[i] + (CIR[i + 1] - CIR[i]) * f, i


def flujo(fr, t, k=1.0, n=34, vel=0.12):
    if k <= 0.01:
        return
    line3(fr, CIR, col=(150, 160, 175), w=1.6, a=0.5 * k, glow=0.25 * k)
    for j in range(n):
        p, i = _en((j / n + t * vel) % 1.0)
        if i < I_COMP - 3:
            col = FRIO
        elif i < I_COMP + 2:
            col = M.mixc(FRIO, NARANJA, (i - (I_COMP - 3)) / 5)
        else:
            col = M.mixc(NARANJA, (200, 200, 210), clamp((i - I_COMP - 2) / 18))
        dot3(fr, p, r=4.2, col=col, a=k, glow=1.2 * k)


def flechas_calor(fr, t, origen, destino, k=1.0, n=6, col=NARANJA):
    if k <= 0.01:
        return
    o, d_ = np.array(origen, float), np.array(destino, float)
    for j in range(n):
        s = (t * 0.6 + j / n) % 1.0
        p = o + (d_ - o) * s + np.array([0, 0.08 * math.sin(s * 9 + j), 0])
        dot3(fr, p, r=5, col=col, a=k * (1 - abs(s - 0.5) * 1.2), glow=1.2)


def comida():
    a = named(M3.box(0.18, 0.32, 0.14, (240, 240, 236), shadow=0, base=True, gloss=0.3).tf(t=(-0.2, 0.47, 0.05)), 'comida')
    b = named(M3.cyl(0.09, 0.2, (200, 70, 60), n=18, shadow=0, gloss=0.4, y0=0).tf(t=(0.15, 0.47, 0.1)), 'comida')
    c = named(M3.box(0.3, 0.12, 0.2, (240, 190, 90), shadow=0, base=True, gloss=0.3).tf(t=(0.05, 0.82, 0.0)), 'comida')
    return [a, b, c]


# ------------------------------------------------------------------ escenas
K0 = [(-4.6, dict(target=(0, 1.05, 0), dist=6.0, yaw=60, pitch=12, cy=0.55)),
      (-0.9, dict(target=(0, 1.05, 0), dist=4.9, yaw=34, pitch=8, cy=0.55)),
      (0.0, dict(target=(0, 1.05, 0), dist=4.4, yaw=26, pitch=6, cy=0.55)),
      (8.0, dict(target=(0, 1.0, 0), dist=3.8, yaw=10, pitch=5, cy=0.55))]


def s_gancho(t, fi, u, d, titulo=True):
    fr = Frame(cam_path(u, K0))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    x, y = fr.cam.proj([(0, 0.02, 0)])[0][0]
    D.shadow_blob(fr, x, y, 360, 90, 0.8)
    if titulo:
        glass_type(fr.base, fr.fx, 'FRÍO', 540 * S, 1180 * S, 260 * S, k=ease(seg(u, -0.6, 0.4)), fill_a=0.06)
    puerta = 0.0 if titulo else eout(seg(u, 3.0, 4.0))
    draw_objects(fr, refri(puerta=puerta))
    t1 = TT(1) - TT(0)
    flechas_calor(fr, t, (0, 1.0, 0.0), (0, 1.2, -1.3), k=seg(u, t1 + 1.5, t1 + 2.0) if titulo else 0.0)
    if not titulo:
        flechas_calor(fr, t, (0, 0.8, 0.5), (0, 0.4, 1.4), k=puerta, col=FRIO)
        flechas_calor(fr, t, (0, 1.0, -0.5), (0, 1.6, -1.4), k=puerta)

    def ui(img, fx):
        if titulo:
            kicker(img, 'TERMODINÁMICA DE TU COCINA', 132, seg(u, 0.55, 0.95))
            title(img, fx, [('Tu refri no hace frío…', 'sans'), ('saca el calor.', 'serif')], 190, seg(u, 0.15, 0.75), size=76)
            ta = wt(1, 3) - TT(0)
            P.pill_tachada(img, fx, 540, 1330, 'FABRICA FRÍO', seg(u, ta - 0.4, ta), seg(u, ta + 0.2, ta + 0.55), t, size=34)
            pill(img, fx, 540, 1430, 'MUEVE EL CALOR', eout(seg(u, t1 + 1.6, t1 + 1.9)), size=34, border=NARANJA)
        else:
            title(img, fx, [('Mándaselo a quien abre', 'sans'), ('el refri para echarse aire.', 'serif')], 190, seg(u, 0.0, 0.5), size=66)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_mandalo(t, fi, u, d):
    return s_gancho(t, fi, u + 3.0, d, titulo=False)


K1 = [(-0.4, dict(target=(0, 1.15, -0.1), dist=4.0, yaw=40, pitch=10, cy=0.52)),
      (8.0, dict(target=(0, 1.2, -0.1), dist=3.4, yaw=58, pitch=14, cy=0.52))]


def s_circuito(t, fi, u, d):
    fr = Frame(cam_path(u, K1))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    draw_objects(fr, refri() + comida(), xray=seg(u, 0.0, 0.55), keep=('comida', 'comp'))
    flujo(fr, t, k=eout(seg(u, 0.5, 1.4)))
    k3 = seg(t, TT(3) + 1.0, TT(3) + 1.6)
    flechas_calor(fr, t, (0, 0.6, 0.05), (0, 1.7, -0.32), k=k3, n=8)
    ec = fr.cam.p1(np.array([0, 1.7, -0.32]))

    def ui(img, fx):
        kicker(img, 'RAYOS X · EL REFRIGERANTE', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        pill(img, fx, 540, 300, 'REFRIGERANTE', eout(seg(u, 0.9, 1.2)), size=32, border=FRIO)
        if t >= TT(3):
            doodle_circle(img, fx, ec[0], ec[1], 200, 110, t, k=eout(seg(t, TT(3) + 0.3, TT(3) + 0.8)), col=(255, 236, 160), w=6)
            pill(img, fx, 540, 1330, 'SE EVAPORA Y SE ROBA EL CALOR', eout(seg(t, TT(3) + 1.0, TT(3) + 1.3)), size=28, border=NARANJA)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_gota(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.6, 0), dist=3.6, yaw=0, pitch=16, cy=0.55))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=0.9)
    k = eout(seg(u, 0.0, 0.5))
    ev = seg(u, 0.6, 2.4)
    R = 0.45 * (1 - 0.7 * ev)
    pts = [np.array([R * 0.85 * math.sin(a) * math.sin(a / 2), 0.02 + R + R * math.cos(a) * 1.15, 0])
           for a in np.linspace(0, 2 * math.pi, 80)]
    line3(fr, pts, col=FRIO, w=3.5, a=k, glow=1.0)
    P.ondas_calor(fr, t, 0, 0.2 + R * 2, 1.4, 0.5, k=ev, col=(220, 235, 255), n=4)
    flechas_calor(fr, t, (0, 0.0, 0.3), (0, 1.3, 0.0), k=ev, n=6)

    def ui(img, fx):
        kicker(img, 'COMO EL SUDOR', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        pill(img, fx, 540, 300, 'AL EVAPORARSE SE LLEVA EL CALOR', eout(seg(u, 0.8, 1.1)), size=28, border=NARANJA)
    fr.ui.append(ui)
    return finish(fr, fi)


K3 = [(-0.4, dict(target=(0.25, 0.25, -0.6), dist=1.9, yaw=150, pitch=14, cy=0.55)),
      (6.0, dict(target=(0.25, 0.25, -0.6), dist=1.6, yaw=170, pitch=12, cy=0.55))]


def s_compresor(t, fi, u, d):
    shake = 0.25 * math.sin(t * 60)
    keys = [(a, dict(b, yaw=b['yaw'] + shake)) for a, b in K3]
    fr = Frame(cam_path(u, keys))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    hot = eout(seg(u, 1.0, 3.0))
    draw_objects(fr, refri(motor=hot))
    flujo(fr, t, k=1.0, n=40, vel=0.16)
    cc = fr.cam.p1(np.array([0.25, 0.2, -0.6]))

    def ui(img, fx):
        kicker(img, 'EL COMPRESOR (EL QUE ZUMBA)', 150, seg(u, 0.0, 0.3))
        doodle_circle(img, fx, cc[0], cc[1], 210, 170, t, k=eout(seg(u, 0.4, 0.9)), col=(255, 236, 160), w=6)
        pill(img, fx, 540, 300, 'LO APRIETA Y LO CALIENTA', eout(seg(u, 1.4, 1.7)), size=30, border=NARANJA)
    fr.ui.append(ui)
    return finish(fr, fi)


K4 = [(-0.4, dict(target=(0, 1.1, -0.4), dist=4.2, yaw=200, pitch=8, cy=0.55)),
      (8.0, dict(target=(0, 1.1, -0.4), dist=3.6, yaw=165, pitch=10, cy=0.55))]


def s_atras(t, fi, u, d):
    fr = Frame(cam_path(u, K4))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    hot = eout(seg(u, 0.3, 1.8))
    draw_objects(fr, refri(motor=0.6))
    line3(fr, CIR[14:-2], col=M.mixc((90, 90, 96), NARANJA, hot), w=4, a=1.0, glow=1.2 * hot)
    P.ondas_calor(fr, t, 0, 1.95, 2.8, 0.9, k=hot, col=NARANJA, n=6)
    flechas_calor(fr, t, (0, 1.0, -0.55), (0, 1.4, -1.6), k=hot, n=8)

    def ui(img, fx):
        kicker(img, 'ATRÁS DEL REFRI', 150, seg(u, 0.0, 0.3), col=(255, 160, 130))
        pill(img, fx, 540, 300, 'SUELTA EL CALOR EN TU COCINA', eout(seg(u, 0.8, 1.1)), size=30, border=NARANJA)
        if t >= TT(7):
            P.termometro(img, fx, 150, 1300, 420, 0.8, 'CALIENTE', k=eout(seg(t, TT(7) + 0.3, TT(7) + 0.7)))
    fr.ui.append(ui)
    out = finish(fr, fi)
    a = 0.08 * hot
    o = out.astype(np.float32)
    o = o * (1 - a) + np.array([255, 70, 30], np.float32) * a * (o.mean(2, keepdims=True) / 255 + 0.2)
    return o.clip(0, 255).astype(np.uint8)


K5 = [(-0.4, dict(target=(0, 1.0, 0), dist=5.4, yaw=55, pitch=12, cy=0.55)),
      (8.0, dict(target=(0, 1.0, 0), dist=4.6, yaw=75, pitch=14, cy=0.55))]


def s_puerta(t, fi, u, d):
    fr = Frame(cam_path(u, K5))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    pu = eout(seg(t, wt(8, 7), wt(8, 9)))
    mot = eout(seg(t, TT(9) + 1.5, TT(9) + 2.5))
    draw_objects(fr, refri(puerta=pu, motor=mot))
    flechas_calor(fr, t, (0, 0.9, 0.5), (0.2, 0.5, 1.6), k=pu, col=FRIO)
    flechas_calor(fr, t, (0, 1.0, -0.55), (0, 1.5, -1.8), k=pu, n=8)
    flechas_calor(fr, t, (0.25, 0.25, -0.6), (0.4, 1.0, -1.8), k=mot, n=6, col=(255, 90, 60))
    k_coc = eout(seg(t, wt(8, 13), wt(8, 15)))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, 0.0, 0.3), col=(255, 150, 140))
        pill(img, fx, 540, 300, 'PUERTA ABIERTA', eout(seg(t, wt(8, 7), wt(8, 8))), size=32, border=FRIO)
        pill(img, fx, 540, 1300, 'LA COCINA SE CALIENTA MÁS', k_coc, size=30, border=RED)
        if t >= TT(9):
            pill(img, fx, 540, 1400, '+ EL CALOR DEL MOTOR', eout(seg(t, TT(9) + 1.5, TT(9) + 1.8)), size=30, border=(255, 90, 60))
    fr.ui.append(ui)
    return finish(fr, fi)


K6 = [(-0.4, dict(target=(0, 1.0, -0.3), dist=5.0, yaw=95, pitch=14, cy=0.55)),
      (6.0, dict(target=(0, 1.0, -0.3), dist=4.4, yaw=110, pitch=16, cy=0.55))]


def s_pared(t, fi, u, d):
    fr = Frame(cam_path(u, K6))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    zp = lerp(-1.6, -0.66, eout(seg(u, 0.2, 1.4)))
    pared = named(M3.box(2.6, 2.6, 0.12, (70, 72, 80), shadow=0, base=True, gloss=0.2).tf(t=(0, 0, zp - 0.06)), 'pared', rim=0.4)
    draw_objects(fr, [pared] + refri(motor=0.7))
    trap = seg(u, 1.2, 2.0)
    for j in range(8):
        s = (t * 1.4 + j / 8) % 1.0
        x = -0.4 + 0.8 * (j / 7)
        z = -0.5 + (zp + 0.06 + 0.5) * (0.5 + 0.5 * math.sin(s * 2 * math.pi))
        dot3(fr, np.array([x, 0.6 + 1.2 * s, z]), r=5, col=(255, 90, 60), a=trap, glow=1.3)

    def ui(img, fx):
        kicker(img, 'PEGADO A LA PARED', 150, seg(u, 0.0, 0.3), col=(255, 150, 140))
        pill(img, fx, 540, 300, 'EL CALOR NO TIENE POR DÓNDE SALIR', eout(seg(u, 1.4, 1.7)), size=28, border=RED)
        pill(img, fx, 540, 1350, 'GASTA MÁS LUZ', eout(seg(t, wt(10, 14), wt(10, 15))), size=40, border=(255, 236, 160))
    fr.ui.append(ui)
    return finish(fr, fi)


def s_temps(t, fi, u, d):
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0, 1.0, 0), dist=4.6, yaw=-24, pitch=8, cx=0.62, cy=0.55)),
                            (6.0, dict(target=(0, 1.0, 0), dist=4.2, yaw=-12, pitch=8, cx=0.62, cy=0.55))]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9)
    draw_objects(fr, refri())
    tc = wt(11, 6)

    def ui(img, fx):
        kicker(img, 'LA TEMPERATURA CORRECTA', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        P.termometro(img, fx, 150, 1180, 380, 0.35, '4 °C', k=eout(seg(u, 0.3, 0.7)), col=FRIO)
        P.termometro(img, fx, 150, 640, 280, 0.08, '−18 °C', k=eout(seg(t, tc, tc + 0.4)), col=(170, 140, 255))
        pill(img, fx, 700, 1500, 'FDA · USDA', eout(seg(u, 1.0, 1.3)), size=24, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55), sfx=[]),
           dict(desde=2, fn=s_circuito, tr='zoom', sfx=[(0.0, 'shimmer', 0.8), (0.9, 'tick', 0.6)]),
           dict(desde=4, fn=s_gota, tr='flash', sfx=[(0.6, 'whoosh_suave', 0.4), (0.8, 'tick', 0.5)]),
           dict(desde=5, fn=s_compresor, tr='whip', sfx=[(0.4, 'scribble', 0.7), (1.0, 'sub', 0.6), (1.4, 'tick', 0.6)]),
           dict(desde=6, fn=s_atras, tr='whip_izq', sfx=[(0.3, 'riser', 0.4), (0.8, 'tick', 0.6)]),
           dict(desde=8, fn=s_puerta, tr='flash', sfx=[]),
           dict(desde=10, fn=s_pared, tr='wipe', sfx=[(0.4, 'whoosh', 0.5), (1.4, 'thud', 0.8), (1.5, 'tick', 0.6)]),
           dict(desde=11, fn=s_temps, tr='zoom', sfx=[(0.3, 'chime_b', 0.7), (1.0, 'tick', 0.5)]),
           dict(desde=12, fn=s_mandalo, tr='ritmo'),
           dict(desde=13, loop=True, tr='zoom')]


def _sfx_dinamicos():
    ta = wt(1, 3) - TT(0)
    t1 = TT(1) - TT(0)
    ESCENAS[0]['sfx'] = [(0.15, 'whoosh', 0.3), (ta - 0.4, 'tick', 0.6), (ta + 0.2, 'scribble', 0.7), (t1 + 1.6, 'chime_b', 0.6)]
    ESCENAS[1]['sfx'] += [(TT(3) - TT(2) + 0.3, 'scribble', 0.7), (TT(3) - TT(2) + 1.0, 'tick', 0.6)]
    ESCENAS[4]['sfx'] += [(TT(7) - TT(6) + 0.3, 'tick', 0.6)]
    ESCENAS[5]['sfx'] = [(wt(8, 7) - TT(8), 'whoosh', 0.6), (wt(8, 13) - TT(8), 'tick', 0.6), (TT(9) + 1.5 - TT(8), 'bass', 0.6)]
    ESCENAS[6]['sfx'] += [(wt(10, 14) - TT(10), 'chime_c', 0.6)]
    ESCENAS[7]['sfx'] += [(wt(11, 6) - TT(11), 'chime_a', 0.6)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
