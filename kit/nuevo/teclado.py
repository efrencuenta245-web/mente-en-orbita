"""Reel: «Tu teclado ya sabe tu siguiente palabra.» (texto predictivo). Vie 6-nov-2026, 8:00. Voz Isaac.
Datos: Gboard predice la siguiente palabra con un modelo de lenguaje; en 2018 el modelo pesaba 1.4 MB (Hard et al.,
«Federated learning for mobile keyboard prediction», arXiv 1811.03604) y se entrena con aprendizaje federado: el celular
entrena con lo que escribes y solo manda ajustes del modelo (Xu et al., Google, 2023). Probabilidades de la gráfica: EJEMPLO."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, cam_path, space, draw_objects, finish, title, kicker, pill, glass_type, doodle_circle,
                    chart_grow, rec_frame, line3, dot3, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
import demo_estilo as D

S = M.SS
TEMA = 'teclado'
TXT = ['Tu teclado ya sabe tu siguiente palabra.',
       'Y no, no te está leyendo la mente.',
       'Escribe «buenos», y te sugiere «días». Escribe «feliz», y te sale «cumpleaños».',
       'Adentro hay un modelo de lenguaje: un programa que aprendió de millones de frases.',
       'Para cada palabra, calcula una probabilidad.',
       'Después de «buenos», «días» gana por mucho, y «noches» va segunda.',
       'Y te enseña las tres más probables, arriba del teclado.',
       'En 2018, ese modelo del teclado de Google pesaba apenas 1.4 megas: cabe en tu celular.',
       'Pero aquí viene lo curioso: también aprende de cómo escribes tú.',
       'Tu celular entrena el modelo ahí mismo, y a Google solo le manda los ajustes, no tus mensajes.',
       'Se llama aprendizaje federado.',
       'Por eso tus apodos y tus palabras de siempre aparecen primero.',
       'Mándaselo a quien cree que su celular lo espía,',
       'porque su teclado ya sabe… su siguiente palabra.']
VOZ = TXT[:7] + ['En dos mil dieciocho, ese modelo del teclado de Google pesaba apenas uno punto cuatro megas: cabe en tu celular.'] + TXT[8:]


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


def wt(i, k):
    n = len(TXT[i].split())
    return TT(i) + (TE(i) - TT(i)) * k / n


# ------------------------------------------------------------------ pantalla de chat con teclado
def scr_teclado(texto, sug=('', '', ''), hl=-1, mensajes=(), cursor=True, brillo=0.0):
    def dib(d, im):
        w = 420
        f = M.font
        d.text((w / 2, 110), 'Chat', font=f('sanss', 28), fill=(220, 220, 224), anchor='mm')
        d.line([(30, 150), (w - 30, 150)], fill=(40, 42, 50), width=2)
        y = 180
        for m, mio in mensajes:
            tw = d.textlength(m, font=f('sanss', 24))
            x0 = w - 40 - tw - 30 if mio else 40
            d.rounded_rectangle((x0, y, x0 + tw + 30, y + 50), radius=20, fill=(40, 110, 220) if mio else (40, 42, 50))
            d.text((x0 + 15, y + 25), m, font=f('sanss', 24), fill=(245, 245, 247), anchor='lm')
            y += 66
        d.rounded_rectangle((24, 440, w - 24, 500), radius=28, outline=(80, 82, 92), width=2, fill=(16, 17, 22))
        d.text((48, 470), texto, font=f('sanss', 28), fill=(245, 245, 247), anchor='lm')
        if cursor:
            cx = 48 + d.textlength(texto, font=f('sanss', 28)) + 4
            d.line([(cx, 452), (cx, 488)], fill=(120, 225, 255), width=3)
        for i, s in enumerate(sug):
            x0 = 14 + i * 132
            on = i == hl
            if on:
                d.rounded_rectangle((x0, 512, x0 + 126, 566), radius=14, fill=M.mixc((40, 42, 50), (120, 225, 255), 0.35 + 0.4 * brillo))
            d.text((x0 + 63, 539), s, font=f('sans' if on else 'sanss', 26), fill=(255, 255, 255) if on else (190, 192, 200), anchor='mm')
            if i < 2:
                d.line([(x0 + 129, 522), (x0 + 129, 556)], fill=(60, 62, 70), width=2)
        rows = ['qwertyuiop', 'asdfghjklñ', 'zxcvbnm']
        for r, row in enumerate(rows):
            n = len(row)
            kw = 38
            x = (w - n * kw) / 2
            for ch in row:
                d.rounded_rectangle((x + 2, 590 + r * 70, x + kw - 2, 650 + r * 70), radius=8, fill=(44, 46, 54))
                d.text((x + kw / 2, 620 + r * 70), ch, font=f('sanss', 24), fill=(230, 230, 234), anchor='mm')
                x += kw
        d.rounded_rectangle((100, 800, w - 100, 850), radius=10, fill=(44, 46, 54))
    return P.pantalla(dib)


def tipeo(full, t0, t, cps=11):
    n = int(clamp((t - t0) * cps, 0, len(full)))
    return full[:n]


KF = [(-4.6, dict(target=(0, 0.95, 0), dist=5.0, yaw=60, pitch=14, cy=0.55)),
      (-0.9, dict(target=(0, 0.95, 0), dist=3.6, yaw=26, pitch=8, cy=0.55)),
      (0.0, dict(target=(0, 0.95, 0), dist=3.1, yaw=18, pitch=6, cy=0.55)),
      (6.0, dict(target=(0, 0.95, 0), dist=2.6, yaw=6, pitch=4, cy=0.55))]


def s_gancho(t, fi, u, d, titulo=True):
    fr = Frame(cam_path(u, KF))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    x, y = fr.cam.proj([(0, 0.02, 0)])[0][0]
    D.shadow_blob(fr, x, y, 330, 70, 0.8)
    if titulo:
        glass_type(fr.base, fr.fx, 'Aa', 540 * S, 1140 * S, 300 * S, k=ease(seg(u, -0.6, 0.4)), fill_a=0.06)
    txt = tipeo('Nos vemos ', 0.2, max(0.0, u), 9)
    sug = ('mañana', 'al rato', 'luego') if len(txt) >= 10 else ('', '', '')
    hl = 0 if u > 1.6 else -1
    draw_objects(fr, P.celular(scr_teclado(txt + ('mañana' if u > 2.0 else ''), sug, hl, brillo=0.5 + 0.5 * math.sin(t * 6))))

    def ui(img, fx):
        if titulo:
            kicker(img, 'TEXTO PREDICTIVO', 132, seg(u, 0.55, 0.95))
            title(img, fx, [('Tu teclado ya sabe', 'sans'), ('tu siguiente palabra.', 'serif')], 190, seg(u, 0.15, 0.75), size=76)
            ta = wt(1, 6) - TT(0)
            P.pill_tachada(img, fx, 540, 1330, 'LEE TU MENTE', seg(u, ta - 0.4, ta), seg(u, ta + 0.2, ta + 0.55), t, size=34)
        else:
            title(img, fx, [('Mándaselo a quien cree', 'sans'), ('que su celular lo espía.', 'serif')], 190, seg(u, 0.0, 0.5), size=72)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_mandalo(t, fi, u, d):
    return s_gancho(t, fi, u + 3.0, d, titulo=False)


KC = [(-0.4, dict(target=(0, 0.92, 0), dist=2.35, yaw=-12, pitch=3, cy=0.5)),
      (6.0, dict(target=(0, 0.92, 0), dist=2.15, yaw=8, pitch=3, cy=0.5))]


def s_ejemplos(t, fi, u, d):
    fr = Frame(cam_path(u, KC))
    space(fr, t, floor=None, bokeh=0.9)
    tf_ = wt(2, 7)
    if t < tf_:
        txt = tipeo('Buenos ', TT(2) + 0.1, t, 10)
        sug, hl = (('días', 'noches', 'tardes'), 0) if len(txt) >= 7 else (('', '', ''), -1)
    else:
        txt = tipeo('Feliz ', tf_, t, 10)
        sug, hl = (('cumpleaños', 'día', 'año'), 0) if len(txt) >= 6 else (('', '', ''), -1)
    draw_objects(fr, P.celular(scr_teclado(txt, sug, hl, brillo=0.5 + 0.5 * math.sin(t * 6))))

    def ui(img, fx):
        kicker(img, 'ESCRIBE UNA PALABRA…', 150, seg(u, 0.0, 0.3))
    fr.ui.append(ui)
    return finish(fr, fi)


# red neuronal de líneas que brillan
KN = [(-0.4, dict(target=(0, 1.1, 0), dist=4.6, yaw=-24, pitch=6, cy=0.5)),
      (9.0, dict(target=(0, 1.1, 0), dist=4.0, yaw=22, pitch=10, cy=0.5))]
CAPAS = [(-1.2, 5), (-0.4, 7), (0.4, 7), (1.2, 3)]
PALABRAS = ['hola', 'gracias', 'buenos', 'días', 'feliz', 'noche', 'casa', 'nos vemos', 'tacos', 'mañana', 'jefa', 'carnal']


def _nodos():
    out = []
    for x, n in CAPAS:
        col = []
        for j in range(n):
            yy = 1.1 + (j - (n - 1) / 2) * 0.28
            col.append(np.array([x, yy, 0.0]))
        out.append(col)
    return out


def s_red(t, fi, u, d):
    fr = Frame(cam_path(u, KN))
    space(fr, t, floor=None, bokeh=1.0)
    nod = _nodos()
    k = eout(seg(u, 0.0, 1.0))
    rng = np.random.RandomState(4)
    for a, b in zip(nod[:-1], nod[1:]):
        for pa in a:
            for pb in b:
                if rng.rand() < 0.55:
                    line3(fr, [pa, pb], col=(170, 190, 220), w=1.0, a=0.35 * k, glow=0.25 * k)
    for li, col in enumerate(nod):
        for pj, p in enumerate(col):
            puls = 0.5 + 0.5 * math.sin(t * 5 - li * 1.3 + pj)
            dot3(fr, p, r=7, col=CYAN if li < 3 else WHITE, a=k, glow=0.6 + 0.6 * puls)
    for j in range(6):  # pulsos que viajan por la red
        s = ((t * 0.7 + j / 6) % 1.0)
        li = int(s * 3)
        f = s * 3 - li
        pa = nod[li][(j * 3) % len(nod[li])]
        pb = nod[li + 1][(j * 2) % len(nod[li + 1])]
        dot3(fr, pa + (pb - pa) * f, r=5, col=(255, 236, 160), a=k, glow=1.3)
    outs = [fr.cam.p1(p) for p in nod[-1]]
    ins = [fr.cam.p1(p + np.array([-0.55, 0, 0])) for p in nod[0]]
    t4 = TT(4)

    def ui(img, fx):
        kicker(img, 'MODELO DE LENGUAJE', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        dd = ImageDraw.Draw(img)
        for i, (x, y, _) in enumerate(ins):
            w_ = PALABRAS[(i + int(t * 1.5)) % len(PALABRAS)]
            a = 0.85 * k
            dd.text((x, y), w_, font=M.font('mono', 26), fill=M.scale_c(WHITE, a), anchor='rm')
        if t > t4:
            for i, (x, y, _) in enumerate(outs):
                v = [0.62, 0.21, 0.09][i]
                kk = eout(seg(t, t4 + 0.4 + 0.2 * i, t4 + 0.7 + 0.2 * i))
                pill(img, fx, x + 40, y, f'{v:.2f}', kk, size=28, anchor='l', border=WHITE if i == 0 else (150, 150, 160), dot=False)
        pill(img, fx, 540, 300, 'APRENDIÓ DE MILLONES DE FRASES', eout(seg(u, 1.2, 1.5)), size=28)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_grafica(t, fi, u, d):
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=14, cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'DESPUÉS DE «BUENOS»…', 150, seg(u, -0.1, 0.2))
        chart_grow(img, fx, (90, 300, 990, 1220), [3, 9, 21, 62], ['AMIGOS', 'TARDES', 'NOCHES', 'DÍAS'], TT(5) - 0.1, t,
                   unit='%', title_txt='PROBABILIDAD · %', tag='EJEMPLO', line=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_barra(t, fi, u, d):
    fr = Frame(cam_path(u, KC))
    space(fr, t, floor=None, bokeh=0.9)
    draw_objects(fr, P.celular(scr_teclado('Buenos ', ('días', 'noches', 'tardes'), 0, brillo=0.5 + 0.5 * math.sin(t * 6))))
    out = finish(fr, fi)
    z = 1.0 if u < 1.2 else (1.4 if u < 1.9 else 1.9)
    cx, cy = 0.5, 0.56
    if z > 1:
        out = M.scale_about(out, z, cx, cy)
        im = Image.fromarray(out)
        rec_frame(im, t, 1.0, f'x{z:.1f}')
        out = np.asarray(im)
    return out


def s_mega(t, fi, u, d):
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0.0, 0.9, 0), dist=3.0, yaw=-14, pitch=6, cy=0.52)),
                            (6.0, dict(target=(0.08, 1.1, 0), dist=2.6, yaw=8, pitch=8, cy=0.52))]))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    ph = P.celular(scr_teclado('Buenos ', ('días', 'noches', 'tardes'), 0), interior=True)
    draw_objects(fr, ph, xray=seg(u, 0.0, 0.55), keep=('in',))
    cx, cy, _ = fr.cam.p1(D.CHIP)

    def ui(img, fx):
        kicker(img, 'EN 2018 · TECLADO DE GOOGLE', 150, seg(u, 0.0, 0.3), col=(150, 210, 230))
        doodle_circle(img, fx, cx, cy, 80, 70, t, k=eout(seg(u, 1.0, 1.4)), col=(255, 236, 160), w=6)
        M.glass_type(img, fx, '1.4 MB', 540, 1350, 170, k=eout(seg(u, 2.6, 3.2)), fill_a=0.1)
        pill(img, fx, cx + 40, cy - 190, 'EL MODELO CABE AQUÍ', eout(seg(u, 1.4, 1.7)), size=28, anchor='l')
    fr.ui.append(ui)
    return finish(fr, fi)


def s_tuyo(t, fi, u, d, final=False):
    fr = Frame(cam_path(u, KC))
    space(fr, t, floor=None, bokeh=0.9)
    if not final:
        msgs = (('Qué onda, carnal', True), ('Ya llegué', True))
        txt = tipeo('Nos vemos al rato, ', 0.6, u, 10)
        sug = ('carnal', 'jefa', 'compa') if len(txt) >= 19 else ('', '', '')
    else:
        msgs = (('Gracias, jefa', True), ('Va, carnal', True))
        txt = tipeo('Ya voy, ', 0.2, u, 10)
        sug = ('jefa', 'carnal', 'compa') if len(txt) >= 8 else ('', '', '')
    draw_objects(fr, P.celular(scr_teclado(txt, sug, 0 if sug[0] else -1, mensajes=msgs, brillo=0.5 + 0.5 * math.sin(t * 6))))

    def ui(img, fx):
        if not final:
            kicker(img, 'APRENDE DE CÓMO ESCRIBES TÚ', 150, seg(u, 0.0, 0.3), col=(255, 236, 160))
        else:
            kicker(img, 'TUS PALABRAS DE SIEMPRE, PRIMERO', 150, seg(u, 0.0, 0.3), col=(255, 236, 160))
    fr.ui.append(ui)
    return finish(fr, fi)


def s_final(t, fi, u, d):
    return s_tuyo(t, fi, u, d, final=True)


KS = [(-0.4, dict(target=(0, 1.1, 0), dist=7.2, yaw=-16, pitch=20, cy=0.55)),
      (9.0, dict(target=(0, 1.1, 0), dist=6.4, yaw=14, pitch=16, cy=0.55))]


def s_federado(t, fi, u, d):
    fr = Frame(cam_path(u, KS))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9)
    phones = []
    pos = [(-1.25, 0.55), (-0.62, 1.0), (0.0, 1.2), (0.62, 1.0), (1.25, 0.55)]
    for i, (x, z) in enumerate(pos):
        phones += P.tfk(P.celular(scr_teclado('', ('', '', '')), ry=-x * 18), s=0.55, t=(x, 0, z))
    draw_objects(fr, phones)
    C = np.array([0, 2.35, -0.4])
    k = eout(seg(u, 0.2, 0.9))
    for R in (0.35, 0.55):
        pts = [C + np.array([R * math.cos(a), 0.12 * math.sin(a), R * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 60)]
        line3(fr, pts, col=WHITE, w=2.0, a=0.8 * k, glow=0.8 * k)
    dot3(fr, C, r=16, col=CYAN, a=k, glow=1.5)
    t_aj = wt(9, 13)
    for i, (x, z) in enumerate(pos):
        top = np.array([x, 0.95 * 0.55 + 0.45, z])
        if t > t_aj - 0.6:
            s = ((t - (t_aj - 0.6)) * 0.6 + i * 0.17) % 1.0
            p = top + (C - top) * s
            dot3(fr, p, r=6, col=CYAN, a=1.0, glow=1.3)
        line3(fr, [top, C], col=(120, 160, 200), w=1.0, a=0.25 * k, glow=0.2)
    tops = [fr.cam.p1(np.array([x, 1.1, z])) for x, z in pos]
    cc = fr.cam.p1(C)

    def ui(img, fx):
        kicker(img, 'TU CELULAR ENTRENA EL MODELO', 150, seg(u, 0.0, 0.3))
        pill(img, fx, cc[0], cc[1] - 120, 'SOLO AJUSTES', eout(seg(t, t_aj, t_aj + 0.3)), size=30, border=CYAN)
        km = seg(t, wt(9, 16), wt(9, 16) + 0.3)
        for i, (x, y, _) in enumerate(tops[1:4]):
            if km > 0:
                pill(img, fx, x, y - 60, 'mensajes', eout(km), size=22, border=(200, 200, 210), dot=False)
                if km >= 1:
                    P.N.doodle_arrow_free(img, fx, x - 60, y - 52, x + 60, y - 68, t, seg(t, wt(9, 16) + 0.3, wt(9, 16) + 0.6), RED, seed=i)
        if t >= TT(10):
            title(img, fx, [('Aprendizaje', 'sans'), ('federado.', 'serif')], 1250, seg(t, TT(10), TT(10) + 0.5), size=78)
    fr.ui.append(ui)
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.55), sfx=[]),
           dict(desde=2, fn=s_ejemplos, tr='zoom', sfx=[]),
           dict(desde=3, fn=s_red, tr='flash', sfx=[(0.0, 'shimmer', 0.7), (1.2, 'tick', 0.6)]),
           dict(desde=5, fn=s_grafica, tr='wipe', sfx=[(0.15, 'chime_a', 0.8), (0.43, 'chime_a', 0.6), (0.71, 'chime_b', 0.8), (0.99, 'chime_c', 0.9)]),
           dict(desde=6, fn=s_barra, tr='whip', sfx=[(1.2, 'click', 1.0), (1.9, 'click', 1.0)]),
           dict(desde=7, fn=s_mega, tr='push', sfx=[(0.0, 'shimmer', 0.8), (1.0, 'scribble', 0.8), (2.6, 'thud', 0.7)]),
           dict(desde=8, fn=s_tuyo, tr='whip_izq', sfx=[]),
           dict(desde=9, fn=s_federado, tr='zoom', sfx=[(0.2, 'whoosh_suave', 0.4)]),
           dict(desde=11, fn=s_final, tr='flash', sfx=[]),
           dict(desde=12, fn=s_mandalo, tr='ritmo'),
           dict(desde=13, loop=True, tr='zoom')]


def _sfx_dinamicos():
    ta = wt(1, 6) - TT(0)
    ESCENAS[0]['sfx'] = [(0.15, 'whoosh', 0.3)] + [(0.2 + i / 9, 'tick2', 0.25) for i in range(10)] + \
                        [(2.0, 'chime_b', 0.5), (ta - 0.4, 'tick', 0.6), (ta + 0.2, 'scribble', 0.7)]
    tf_ = wt(2, 7)
    ESCENAS[1]['sfx'] = [(0.1 + i / 10, 'tick2', 0.25) for i in range(7)] + [(0.8, 'chime_b', 0.6)] + \
                        [(tf_ - TT(2) + i / 10, 'tick2', 0.25) for i in range(6)] + [(tf_ - TT(2) + 0.7, 'chime_c', 0.6)]
    ESCENAS[2]['sfx'] += [(TT(4) - TT(3) + 0.4 + 0.2 * i, 'tick', 0.5) for i in range(3)]
    ESCENAS[6]['sfx'] = [(0.6 + i / 10, 'tick2', 0.22) for i in range(19)] + [(2.6, 'chime_b', 0.6)]
    ESCENAS[7]['sfx'] += [(wt(9, 13) - TT(9), 'chime_a', 0.6), (wt(9, 16) - TT(9), 'tick', 0.6), (wt(9, 16) - TT(9) + 0.3, 'scribble', 0.7),
                          (TT(10) - TT(9), 'bass', 0.6)]
    ESCENAS[8]['sfx'] = [(0.2 + i / 10, 'tick2', 0.22) for i in range(8)] + [(1.1, 'chime_b', 0.6)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
