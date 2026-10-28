"""Librería genérica de escenas de Mente en órbita (sobre motor3d.py).
Cada video define su guion, sus tarjetas y su lista de escenas, y llama a escenas.main():

    import os; os.environ.setdefault('MOTOR_TEMA', 'espacio')
    import escenas as S
    from escenas import *            # motor3d + ayudas (head, ui_pill, photo, card...)
    CARD = {'c1': ('RAZÓN 1', 'SUBTÍTULO', 'bounce'), ...}   # estilos: bounce, line, rings, error, ruler
    def s_algo(fr, t, lt, dur): ...
    SHOTS = [(('c0', 0), s_algo), (('card', 'c1'), None), ...]
    if __name__ == '__main__': S.main(SHOTS, CARD)

Variables de entorno: GTA_FMT=h|v (horizontal 1920x1080 / vertical 1080x1920), MOTOR_TEMA, VIDEO_TL=ruta del tl_*.json
(lo genera timeline.py). Uso: python3 TEMA.py info | preview T salida.png | chunk A B salida.mp4"""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
import motor3d as E
from motor3d import *  # noqa: F401,F403
from motor3d import (Cam, box, rbox, cyl, sphere, extrude, decal, Frame, line3, ring3, dot3, headline, pill, label, counter,
                     draw_text, font, ease, eout, eback, lerp, mix, clamp, win, fmt_int, W, H, VERT, SS, INK, MUTED, TH)

TL = json.load(open(os.environ.get('VIDEO_TL', '/home/claude/tl.json')))
DUR = TL['dur']
FPS = 24
NF = int(round(DUR * FPS))
P = {(p['c'], p['i']): p for p in TL['phrases']}
IMG = os.environ.get('VIDEO_IMG', '/home/claude/img/')
_TX = {}
CARD = {}
SH = []


def PA(c, i):
    p = P.get((c, i))
    return p['a'] if p else None


def PB(c, i):
    p = P.get((c, i))
    return p['b'] if p else None


def WS(c, i, k):
    """Inicio de la palabra k (índice de pantalla) de la frase; k puede ser texto (primera coincidencia)."""
    p = P.get((c, i))
    if not p:
        return None
    if isinstance(k, str):
        for w, a, b in p['words']:
            if w.strip('.,:;…?!¿¡').lower().startswith(k.lower()):
                return a
        return p['a']
    k = max(0, min(k, len(p['words']) - 1))
    return p['words'][k][1]


def T(*opts, default=0.0):
    """Primer tiempo disponible de varias opciones (frases que pueden faltar en los reels)."""
    for o in opts:
        v = WS(*o) if len(o) == 3 else PA(*o)
        if v is not None:
            return v
    return default


def real_img(name, w, h, border=0):
    """Imagen oficial recortada a w x h (RGBA), con marco blanco opcional."""
    key = ('real', name, w, h, border)
    if key in _TX:
        return _TX[key]
    im = Image.open(IMG + name).convert('RGB')
    iw, ih = im.size
    r = w / h
    if iw / ih > r:
        nw = int(ih * r); im = im.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / r); im = im.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    im = im.resize((w - 2 * border, h - 2 * border), Image.LANCZOS)
    out = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    out.paste(im, (border, border))
    _TX[key] = out
    return out



def photo(name, w=1.6, x=0.0, y=0.0, z=0.0, ry=0.0, rx=0.0, rz=0.0, ar=16 / 9, a=1.0):
    """Tarjeta flotante con una imagen oficial (marco blanco, como foto impresa)."""
    h = w / ar
    m = box(w, h, 0.03, (250, 250, 250), shadow=0.25, base=False)
    decal(m, m.FACE['front'], real_img(name, 480, int(480 / ar), border=12))
    m.alpha = a
    return m.tf(rx=rx, ry=ry, rz=rz, t=(x, y, z))


def credit(fr, a=1.0):
    """Etiqueta honesta para imágenes oficiales."""
    ui_pill(fr, CREDIT, a, where='bl', dotc=(240, 88, 138))


# ------------------------------------------------------------------ ayudas de escena
def orbit(lt, base_yaw, rate=4.0, **kw):
    kw = dict(kw)
    kw['yaw'] = base_yaw + lt * rate
    return Cam(**kw)


def vfit(d, wide=False):
    """En vertical la cámara se aleja para que quepa el ancho (más en escenas anchas)."""
    if not VERT:
        return d * 0.96
    return d * (1.3 if wide else 1.0)


def appear(t, t0, d=0.45):
    return eback((t - t0) / d) if t0 is not None else 0.0


def ui_label3(fr, p, txt, sub=None, a=1.0, side=1, length=90, up=40):
    def f(img, d, p=p):
        x, y, z = fr.cam.p1(p)
        if z > 0.2:
            label(img, d, x, y, txt, sub, a, side, length, up)
    fr.ui.append(f)


def ui_text3(fr, p, txt, size=30, a=1.0, col=INK, fk='b', dy=0):
    def f(img, d, p=p):
        x, y, z = fr.cam.p1(p)
        if z > 0.2:
            draw_text(d, (x, y + dy), txt, font(fk, size * (1.3 if VERT else 1.0)), col, 'mm', a=a)
    fr.ui.append(f)


def ui_pill(fr, txt, a=1.0, where='br', dotc=None):
    def f(img, d):
        if where == 'br':
            x, y = (W - 40, H - 150) if not VERT else (W - 40, H * 0.66)
            pill(img, d, x, y, txt, a, anchor='r', dotc=dotc)
        else:
            x, y = (40, H - 150) if not VERT else (40, H * 0.66)
            pill(img, d, x, y, txt, a, anchor='l', dotc=dotc)
    fr.ui.append(f)


def head(fr, lines, accent, t, t0, kicker=None):
    k = clamp((t - t0) / 0.55) if t0 is not None else 0
    fr.ui.append(lambda img, d: headline(img, d, lines, accent, ease(k), kicker))


def big_counter(fr, txt, a=1.0, sub=None, pos=None, size=None, col=INK):
    def f(img, d):
        x, y = pos or ((W * 0.5, H * 0.30) if not VERT else (W * 0.5, H * 0.30))
        counter(img, d, x, y, txt, size, a, col, sub)
    fr.ui.append(f)


def card(fr, t, lt, dur, c):
    title, sub, style = CARD[c][:3]
    fr.mono = True
    fr.floor = 1.0
    fr.floor_g = 0.28
    ball = lambda y, s=1.0: sphere(0.32 * s, (18, 18, 20) if not E.DARK else (230, 230, 236), nu=28, nv=18, gloss=0.9, shadow=0.55).tf(t=(0, y, 0))
    if style == 'bounce':
        fr.cam = Cam(target=(0, 0.4, 0), dist=vfit(6.5) - lt * 0.35, yaw=-10 + lt * 6, pitch=16 + lt * 2)
        tb = lt * 1.6
        y = abs(math.cos(min(tb, 3.6) * 1.5)) * 2.4 * math.exp(-min(tb, 3.6) * 0.75) + 0.32
        fr.meshes.append(ball(y))
        hits = [k * math.pi / 1.5 / 1.6 + math.pi / 3 / 1.6 for k in range(3)]
        def under(d, cam, lt=lt):
            for h in hits:
                if lt > h:
                    for j in range(3):
                        r = (lt - h) * 1.6 + j * 0.25
                        a = clamp(1 - (lt - h) / 1.8) * (1 - j * 0.25)
                        if a > 0:
                            ring3(d, cam, (0, 0.0, 0), r, INK, 1.6, a)
            ring3(d, cam, (0, 0, 0), 2.8, INK, 1.2, 0.5)
        fr.under.append(under)
    elif style == 'line':
        fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(7.0), yaw=30 - lt * 5, pitch=28)
        k = ease(lt / 1.3)
        a, b = np.array([-2.4, 0.0, 1.2]), np.array([2.2, 0.0, -1.4])
        p = a + (b - a) * k
        fr.meshes.append(ball(0.32, 0.7).tf(t=(p[0], 0, p[2])))
        def under(d, cam, k=k, p=p):
            line3(d, cam, [a, p], INK, 2.2)
            for j in range(12):
                q = a + (b - a) * j / 11
                line3(d, cam, [q + (0, 0, -0.06), q + (0, 0, 0.06)], INK, 1.4, a=0.7)
            ring3(d, cam, tuple(b), 0.25, INK, 2.0)
            ring3(d, cam, tuple(b), 0.4, INK, 1.4, 0.6)
        fr.under.append(under)
    elif style == 'rings':
        fr.cam = Cam(target=(0, 0.0, 0), dist=vfit(6.0), yaw=lt * 8, pitch=58 - lt * 6)
        fr.meshes.append(ball(0.25, 0.6))
        def under(d, cam, lt=lt):
            for j in range(4):
                r = 0.6 + j * 0.55 + 0.15 * math.sin(lt * 2 + j)
                ring3(d, cam, (0, 0, 0), r, INK, 2.2 - j * 0.3, clamp(lt * 2 - j * 0.3))
        fr.under.append(under)
    elif style == 'error':
        fr.cam = Cam(target=(0, 0.2, 0), dist=vfit(7.0), yaw=-25 + lt * 4, pitch=24)
        k = ease(lt / 1.0)
        a, b = np.array([-2.2, 0.0, 1.0]), np.array([2.0, 0.0, -1.2])
        p = a + (b - a) * k
        fr.meshes.append(ball(0.0, 0.5).tf(t=tuple(a + (0, 0.16, 0))))
        def under(d, cam, p=p, lt=lt):
            line3(d, cam, [a, p], INK, 2.4)
            ring3(d, cam, tuple(b), 0.22, INK, 2.0)
            ring3(d, cam, tuple(b), 0.36, INK, 1.6)
        fr.under.append(under)
        if lt > 1.0:
            mid = (a + b) / 2 + np.array([0, 0.35, 0])
            ui_text3(fr, tuple(mid), 'error', 30, a=0.5 + 0.5 * (int(lt * 5) % 2), fk='mono')
    else:  # ruler
        fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(7.5), yaw=0, pitch=6)
        fr.meshes.append(ball(0.0, 0.7).tf(t=(0, 0.2, 0)))
        def under(d, cam):
            line3(d, cam, [(0, 0.2, 0), (0, 1.85, 0)], INK, 2.4)
            for j in range(9):
                y = 0.25 + j * 0.2
                ww = 0.12 if j % 4 == 0 else 0.06
                line3(d, cam, [(-ww, y, 0), (ww, y, 0)], INK, 1.6)
        fr.under.append(under)
        meta = CARD[c][3] if len(CARD[c]) > 3 else (100, '')
        v = meta[0] * eout(lt / 2.2)
        ui_text3(fr, (0, 2.15, 0), f'{v:,.1f}'.replace('.0', '') if v < 1000 else fmt_int(v), 44, fk='b')
        if meta[1]:
            ui_text3(fr, (0.95, 2.15, 0), meta[1], 26, a=0.4, fk='m')
    # texto de la tarjeta
    def f(img, d, lt=lt):
        k = ease(lt / 0.5)
        ys = H * (0.15 if not VERT else 0.22)
        draw_text(d, (W / 2, ys), title, font('mono', 76 if not VERT else 96), INK, 'mm', a=k, spacing=6)
        n = int(len(sub) * clamp((lt - 0.3) / 0.9))
        draw_text(d, (W / 2, ys + (64 if not VERT else 86)), sub[:n], font('monor', 28 if not VERT else 38), MUTED, 'mm', a=k, spacing=3)
    fr.ui.append(f)


LEAD = 0.2


def build_shots(SHOTS):
    out = []
    for key, fn in SHOTS:
        if key[0] == 'card':
            c = key[1]
            a = PA(c, 0)
            if a is None:
                continue
            start = a - 1.25
            out.append({'key': key, 'fn': (lambda fr, t, lt, dur, c=c: card(fr, t, lt, dur, c)), 't0': start, 'card': True})
        else:
            a = PA(*key)
            if a is None:
                continue
            out.append({'key': key, 'fn': fn, 't0': max(0.0, a - LEAD), 'card': False})
    out.sort(key=lambda s: s['t0'])
    out[0]['t0'] = 0.0
    for s, n in zip(out[:-1], out[1:]):
        s['t1'] = n['t0']
    out[-1]['t1'] = DUR + 0.01
    return out


XF = 0.28


def shot_at(t):
    for i, s in enumerate(SH):
        if s['t0'] <= t < s['t1']:
            return i
    return len(SH) - 1


def render_shot(i, t):
    s = SH[i]
    fr = Frame()
    lt = t - s['t0']
    s['fn'](fr, t, lt, s['t1'] - s['t0'])
    # gris hacia/desde las tarjetas en blanco y negro
    if not s['card']:
        if i + 1 < len(SH) and SH[i + 1]['card']:
            fr.gray = max(fr.gray, clamp(1 - (s['t1'] - t) / 0.6))
        if i > 0 and SH[i - 1]['card']:
            fr.gray = max(fr.gray, clamp(1 - lt / 0.6))
    return E.render_frame(fr)


_FADE = {}


def sub_band(img):
    if 'b' not in _FADE:
        h = int(H * (0.16 if not VERT else 0.2))
        a = (np.linspace(0, 1, h) ** 1.4 * 215).astype(np.uint8)
        m = Image.fromarray(np.repeat(a[:, None], W, 1), 'L')
        _FADE['b'] = (m, Image.new('RGB', (W, h), TH['bot']), h)
    m, c, h = _FADE['b']
    y = H - h if not VERT else int(H * 0.86) - h
    img.paste(c, (0, y), m)
    if VERT:
        img.paste(Image.new('RGB', (W, H - int(H * 0.86)), TH['bot']), (0, int(H * 0.86)),
                  Image.new('L', (W, H - int(H * 0.86)), 215))


def subtitles(img, t):
    sub_band(img)
    d = ImageDraw.Draw(img)
    cur = None
    for p in TL['phrases']:
        if p['a'] - 0.1 <= t <= p['b'] + 0.35:
            cur = p
    if cur is None:
        return
    fs = 36 if not VERT else 50
    f = font('sb', fs)
    maxw = W * (0.74 if not VERT else 0.86)
    words = cur['words']
    lines, line, lw = [], [], 0
    sp = f.getlength(' ')
    for w in words:
        ww = f.getlength(w[0])
        if line and lw + sp + ww > maxw:
            lines.append(line); line, lw = [], 0
        line.append(w); lw += (sp if lw else 0) + ww
    if line:
        lines.append(line)
    if len(lines) > 2:  # mostrar el par de líneas que contiene la palabra actual
        cur_i = 0
        for li, ln in enumerate(lines):
            if ln[0][1] <= t:
                cur_i = li
        s = min(cur_i, len(lines) - 2)
        s -= s % 2
        lines = lines[s:s + 2]
    y0 = (H - 92) if not VERT else H * 0.79
    lh = fs * 1.3
    y0 -= (len(lines) - 1) * lh
    a = clamp((t - (cur['a'] - 0.1)) / 0.15) * clamp((cur['b'] + 0.35 - t) / 0.15)
    for li, ln in enumerate(lines):
        tw = sum(f.getlength(w[0]) for w in ln) + sp * (len(ln) - 1)
        x = W / 2 - tw / 2
        for w, wa, wb in ln:
            on = t >= wa - 0.03
            col = INK if on else mix(TH['bot'], MUTED, 0.75)
            if on and t < wb + 0.05 and 'sub_hi' in TH:  # palabra que suena ahora
                col = TH['sub_hi']
            draw_text(d, (x, y0 + li * lh), w, f, col, 'lm', a=a)
            x += f.getlength(w) + sp


def chrome(img, t):
    d = ImageDraw.Draw(img)
    fz = 16 if not VERT else 24
    draw_text(d, (34, 34) if not VERT else (40, 120), '@mente_en_orbita1', font('sb', fz), MUTED, 'lm')


def render(t):
    i = shot_at(t)
    img = render_shot(i, t)
    s = SH[i]
    if i > 0 and t - s['t0'] < XF and not s['card'] and not SH[i - 1]['card']:
        prev = render_shot(i - 1, t)
        img = Image.blend(prev, img, ease((t - s['t0']) / XF))
    elif i > 0 and t - s['t0'] < XF:
        prev = render_shot(i - 1, t)
        img = Image.blend(prev, img, ease((t - s['t0']) / XF))
    subtitles(img, t)
    chrome(img, t)
    return img


def chunk(a, b, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    for fi in range(a, b):
        p.stdin.write(render(fi / FPS).tobytes())
    p.stdin.close()
    p.wait()




CREDIT = 'Imagen oficial'


def s_marca(fr, t, lt, dur, sub=None):
    """Sello de cierre de Mente en órbita (va en todos los temas): esfera con órbita y luna + nombre del canal."""
    fr.cam = Cam(target=(0, 1.2, 0), dist=vfit(6.4), yaw=lt * 6, pitch=14)
    dark = E.DARK
    fr.meshes.append(sphere(0.55, (24, 24, 28) if not dark else (60, 110, 200), nu=32, nv=20, gloss=0.9).tf(t=(0, 1.2, 0)))
    a = lt * 1.6
    fr.meshes.append(sphere(0.1, (240, 88, 138) if not dark else (170, 230, 255), nu=12, nv=8, shadow=0, gloss=0.5).tf(
        t=(1.25 * math.cos(a), 1.2 + 0.35 * math.sin(a), 1.25 * math.sin(a))))
    ring_col = INK if not TH.get('hud') else (70, 175, 255)
    fr.under.append(lambda d, cam: line3(d, cam, [(1.25 * math.cos(u), 1.2 + 0.35 * math.sin(u), 1.25 * math.sin(u))
                                                  for u in np.linspace(0, 2 * math.pi, 90)], ring_col, 1.8))

    def f(img, d, lt=lt):
        k = ease(lt / 0.5)
        y = H * (0.80 if not VERT else 0.27)
        draw_text(d, (W / 2, y), 'MENTE EN ÓRBITA', font('mono', 64 if not VERT else 74), INK, 'mm', a=k, spacing=5)
        if sub:
            pill(img, d, W / 2, y + (70 if not VERT else 90), sub, k, dotc=(240, 88, 138))
    fr.ui.append(f)


def main(shots, cards, argv=None):
    """Arma la lista de escenas y atiende la línea de comandos."""
    global SH
    CARD.update(cards)
    SH[:] = build_shots(shots)
    argv = argv or sys.argv
    cmd = argv[1] if len(argv) > 1 else 'info'
    if cmd == 'preview':
        render(float(argv[2])).save(argv[3])
    elif cmd == 'chunk':
        chunk(int(argv[2]), int(argv[3]), argv[4])
    elif cmd == 'sheet':  # hoja de contacto: sheet salida.jpg t1 t2 ...
        ts = [float(x) for x in argv[3:]]
        ims = [render(t).resize((W // 3, H // 3)) for t in ts]
        cols = 4 if W > H else 6
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new('RGB', (cols * W // 3, rows * H // 3), 'white')
        for i, im in enumerate(ims):
            sh.paste(im, ((i % cols) * W // 3, (i // cols) * H // 3))
        sh.save(argv[2])
    else:
        print('DUR', DUR, 'NF', NF)
        for s in SH:
            print(f"{s['t0']:7.2f} {s['t1']:7.2f} {s['key']}")
