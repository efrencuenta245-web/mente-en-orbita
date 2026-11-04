"""Video completo: «Tu celular sabe dónde está el norte… sin internet» (61.5 s, voz Isaac).
Reutiliza el celular, la Tierra y los efectos de demo_estilo.py. Uso: python3 norte.py [preview T… | render salida.mp4]"""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motor2 as M
import demo_estilo as D
from motor2 import (W, H, FPS, Frame, Cam, cam_path, space, draw_objects, named, finish, title, kicker,
                    word_caption, pill, glass_type, doodle_circle, doodle_arrow, rec_frame, chart_grow, photo_card,
                    tr_zoom_through, tr_flash, tr_whip, tr_wipe_v, push_in, line3, dot3, seg, ease, eout, clamp, lerp,
                    WHITE, CYAN, RED, WARM)
M3 = M.M3
S = M.SS
PH_Y = D.PH_Y

DUR = 61.5
NF = int(round(DUR * FPS))
# inicio y fin de cada frase en la voz con pausas (narr_norte_pad.wav)
T = [(0.25, 3.43), (4.16, 5.98), (6.70, 10.93), (11.72, 15.57), (16.52, 21.65), (22.49, 26.62), (27.31, 33.32),
     (34.11, 38.69), (39.51, 42.21), (42.86, 48.29), (49.29, 54.81), (55.70, 57.51), (58.23, 60.92)]
TXT = ['Tu celular sabe dónde está el norte… sin internet.',
       'Y no, no usa el GPS.',
       'Adentro tiene un chip más chiquito que una lenteja: un magnetómetro.',
       'Ese chip siente un imán gigante que no ves: la Tierra.',
       'Muy abajo, el hierro líquido del núcleo se mueve y crea un campo magnético que nos envuelve.',
       'Es tan débil, que un imán de refri es como 100 veces más fuerte.',
       'Pero tu celular lo nota: lo mide en 3 direcciones al mismo tiempo, y así sabe hacia dónde apuntas.',
       'Ahora, el truco: acércale un imán… y la brújula se vuelve loca.',
       'Por eso las fundas y soportes con imán la descalibran,',
       'y por eso Google Maps te pide mover el celular como un 8: así el chip se vuelve a ajustar.',
       'La Tierra mide entre 25 y 65 µT, y tu celular lo siente en tu bolsillo.',
       'Mándaselo a alguien que siempre se pierde,',
       'porque su celular… sabe dónde está el norte.']


def cap(img, fx, i, t, y=1560, size=56):
    """Subtítulo palabra por palabra de la frase i (0-12), repartido sobre su duración."""
    w = TXT[i].split()
    a, b = T[i]
    per = (b - a) * 0.92 / len(w)
    n = len(w)
    k = max(1, math.ceil(n / 6))
    sz = [n // k + (1 if j < n % k else 0) for j in range(k)]
    st = 0
    for j, m in enumerate(sz):
        t0 = a + st * per
        t1 = a + (st + m) * per if j < k - 1 else 1e9
        if t0 <= t < t1 or (j == 0 and t < t0):
            word_caption(img, fx, w[st:st + m], t0, t, y=y, size=size, per=per)
            return
        st += m


def rel(t, i):
    return t - T[i][0]


# ------------------------------------------------------------------ celular con pantalla a elección
def compass_img(head, warn=0.0, ok=0.0):
    w, h = 420, 900
    im = Image.new('RGB', (w, h), (6, 7, 10))
    d = ImageDraw.Draw(im)
    f = M.font
    d.text((34, 26), '9:41', font=f('sanss', 26), fill=(230, 230, 232))
    d.rounded_rectangle((w - 80, 32, w - 34, 52), radius=6, outline=(200, 200, 200), width=2)
    head = head % 360
    d.text((w / 2, 150), f'N {head:.0f}°', font=f('sans', 64), fill=(245, 245, 247), anchor='mm')
    d.text((w / 2, 210), 'CDMX · 19.43°N', font=f('mono', 20), fill=(140, 142, 150), anchor='mm')
    cx, cy, R = w / 2, 470, 165
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(70, 72, 80), width=3)
    for i in range(72):
        a = math.radians(i * 5 - head - 90)
        r0 = R - (22 if i % 6 == 0 else 12)
        c = (235, 235, 238) if i % 18 == 0 else (110, 112, 120)
        d.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + R * math.cos(a), cy + R * math.sin(a))], fill=c, width=3 if i % 6 == 0 else 2)
    for lab, deg in (('N', 0), ('E', 90), ('S', 180), ('O', 270)):
        a = math.radians(deg - head - 90)
        d.text((cx + (R - 52) * math.cos(a), cy + (R - 52) * math.sin(a)), lab, font=f('sans', 30),
               fill=(255, 80, 70) if lab == 'N' else (230, 230, 232), anchor='mm')
    d.polygon([(cx, cy - R - 24), (cx - 12, cy - R - 4), (cx + 12, cy - R - 4)], fill=(255, 80, 70))
    d.line([(cx - 30, cy), (cx + 30, cy)], fill=(90, 92, 100), width=2)
    d.line([(cx, cy - 30), (cx, cy + 30)], fill=(90, 92, 100), width=2)
    if warn > 0.01:
        c = M.scale_c((255, 90, 80), warn)
        d.rounded_rectangle((40, 690, w - 40, 760), radius=20, outline=c, width=3)
        d.text((w / 2, 725), 'Interferencia', font=f('sanss', 30), fill=c, anchor='mm')
    elif ok > 0.01:
        c = M.scale_c((120, 235, 160), ok)
        d.rounded_rectangle((40, 690, w - 40, 760), radius=20, outline=c, width=3)
        d.text((w / 2, 725), 'Calibrada', font=f('sanss', 30), fill=c, anchor='mm')
    else:
        d.text((w / 2, 720), 'Brújula', font=f('sanss', 30), fill=(200, 200, 204), anchor='mm')
    d.rounded_rectangle((w / 2 - 70, h - 34, w / 2 + 70, h - 26), radius=4, fill=(200, 200, 204))
    gl = Image.new('L', (w, h), 0)
    ImageDraw.Draw(gl).polygon([(w * 0.55, 0), (w * 0.85, 0), (w * 0.15, h), (-w * 0.15, h)], fill=20)
    im.paste((255, 255, 255), (0, 0), gl)
    return im


def phone_with(screen, ry=0.0, rz=0.0, off=(0, 0, 0)):
    """Mismo celular de demo_estilo, con pantalla dada, giro y desplazamiento."""
    old = D.compass_screen
    D.compass_screen = lambda _t: screen
    try:
        ph = D.phone(0.0, ry=0.0)
    finally:
        D.compass_screen = old
    out = []
    for m in ph:
        mm = m.tf(t=(0, -PH_Y, 0)).tf(rz=rz).tf(ry=ry, t=(off[0], PH_Y + off[1], off[2]))
        mm.name = m.name
        for a in ('rim', 'gloss', 'glow', 'double'):
            if hasattr(m, a):
                setattr(mm, a, getattr(m, a))
        out.append(mm)
    return out


def flash_in(out, t, t0, d=0.14, amt=110):
    if t0 <= t < t0 + d:
        out = (out.astype(np.float32) + amt * (1 - seg(t, t0, t0 + d))).clip(0, 255).astype(np.uint8)
    return out


# ------------------------------------------------------------------ 1. gancho
K1 = [(-4.6, dict(target=(0, 0.95, 0), dist=5.6, yaw=-78, pitch=16, fk=1.5, cy=0.56)),
      (-0.9, dict(target=(0, 0.95, 0), dist=4.4, yaw=-38, pitch=10, fk=1.5, cy=0.56)),
      (0.0, dict(target=(0, 0.95, 0), dist=3.7, yaw=-26, pitch=7, fk=1.5, cy=0.56)),
      (3.9, dict(target=(0, 0.98, 0), dist=2.8, yaw=-8, pitch=5, fk=1.5, cy=0.56))]


def s_hook(t, fi, end=False):
    fr = Frame(cam_path(t, K1))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    x, y, _ = fr.cam.proj([(0, 0.02, 0)])[0][0].tolist() + [0]
    D.shadow_blob(fr, x, y, 330, 70, 0.8)
    glass_type(fr.base, fr.fx, 'NORTE', 540 * S, 1130 * S, 250 * S, k=ease(seg(t, -0.6, 0.4)), fill_a=0.07)
    ph = D.phone(max(0.0, t) if not end else 0.0)
    draw_objects(fr, [m for m in ph if m.name != 'in'])
    k_t, k_k = seg(t, 0.15, 0.75), seg(t, 0.55, 0.95)
    gt = t + DUR if end else t

    def ui(img, fx):
        if not end:
            kicker(img, 'MAGNETÓMETRO · 3 EJES', 132, k_k)
            title(img, fx, [('Tu celular', 'sans'), ('sabe dónde está el norte.', 'serif')], 190, k_t, size=78)
            pill(img, fx, 540, 1440, 'SIN INTERNET', eout(seg(t, 2.5, 2.8)), size=34, border=(255, 236, 160))
            cap(img, fx, 0, gt)
        else:
            cap(img, fx, 12, gt)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 2. sin GPS
def doodle_x(img, fx, cx, cy, r, t, k, col=RED):
    if k <= 0.01:
        return
    doodle_arrow_free(img, fx, cx - r, cy - r, cx + r, cy + r, t, clamp(k * 2), col)
    doodle_arrow_free(img, fx, cx + r, cy - r, cx - r, cy + r, t, clamp(k * 2 - 1), col, seed=5)


def doodle_arrow_free(img, fx, x0, y0, x1, y1, t, k, col, seed=3):
    if k <= 0.01:
        return
    rng = np.random.RandomState(int(t * 10) + 100 * seed)
    n = 14
    pts = [(lerp(x0, x1, i / n) + rng.normal(0, 2), lerp(y0, y1, i / n) + rng.normal(0, 2)) for i in range(int(n * k) + 1)]
    if len(pts) > 1:
        ImageDraw.Draw(img).line(pts, fill=col, width=9, joint='curve')
        ImageDraw.Draw(fx).line(pts, fill=M.scale_c(col, 0.5), width=14)


def s_nogps(t, fi):
    u = rel(t, 1)
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0, 1.0, 0), dist=3.6, yaw=24, pitch=4, cy=0.55)),
                            (2.2, dict(target=(0, 1.0, 0), dist=3.2, yaw=6, pitch=6, cy=0.55))]))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9)
    head = 12 + 26 * math.sin(t * 1.3)
    draw_objects(fr, [m for m in phone_with(compass_img(head)) if m.name != 'in'])

    def ui(img, fx):
        kicker(img, 'SIN DATOS · SIN SATÉLITES', 150, seg(u, -0.2, 0.2))
        for j, (txt, x) in enumerate((('INTERNET', 270), ('GPS', 810))):
            k = eout(seg(u, 0.05 + 0.35 * j, 0.35 + 0.35 * j))
            pill(img, fx, x, 330, txt, k, size=40, border=(200, 200, 210), dot=False)
            doodle_x(img, fx, x, 330, 70, t, seg(u, 0.55 + 0.4 * j, 0.85 + 0.4 * j))
        cap(img, fx, 1, t)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 3. rayos X al chip
K3 = [(-0.6, dict(target=(0.0, 0.98, 0), dist=3.1, yaw=-14, pitch=6, fk=1.5, cy=0.52)),
      (3.6, dict(target=(0.06, 1.1, 0), dist=2.6, yaw=8, pitch=8, fk=1.5, cy=0.52))]


def s_xray(t, fi, zoom=True):
    u = rel(t, 2)
    fr = Frame(cam_path(u, K3))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    ph = D.phone(t)
    draw_objects(fr, ph, xray=seg(u, 0.0, 0.55), keep=('in',))
    cx, cy = D.chip_screen(fr.cam)

    def ui(img, fx):
        kicker(img, 'RAYOS X · ASÍ SE VE POR DENTRO', 150, seg(u, 0.1, 0.4), col=(150, 210, 230))
        doodle_circle(img, fx, cx, cy, 72, 64, t, k=eout(seg(u, 1.0, 1.45)), col=(255, 236, 160), w=6)
        k_p = eout(seg(u, 3.15, 3.45))
        if k_p > 0:
            d = ImageDraw.Draw(img)
            lx, ly = cx + 70, cy - 210
            d.line([(cx + 26, cy - 22), (lx, ly + 40), (lx + 40, ly + 40)], fill=M.scale_c(CYAN, k_p), width=3)
            pill(img, fx, lx + 40, ly + 40, 'Magnetómetro', k_p, size=30, anchor='l')
        cap(img, fx, 2, t)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if zoom:
        z = 1.0 if u < 2.0 else (1.3 if u < 2.6 else 1.8)
        if z > 1:
            out = M.scale_about(out, z, cx / W, cy / H)
            im = Image.fromarray(out)
            rec_frame(im, t, 1.0, f'x{z:.1f}')
            out = np.asarray(im)
    return out, (cx / W, cy / H)


# ------------------------------------------------------------------ 4-5. la Tierra y su núcleo
def earth(fr, t, C, R, spin, field=0.0, core=0.0, lines_a=1.0):
    camdir = M.norm(fr.cam.pos - C)
    if core > 0.01:
        (px, py), _ = fr.cam.proj([C])[0][0], 0
        (qx, qy) = fr.cam.proj([C + fr.cam.r * R])[0][0]
        rp = abs(qx - px)
        lay = Image.new('RGB', fr.base.size, (0, 0, 0))
        dl = ImageDraw.Draw(lay)
        ro = rp * 0.55
        for j in range(18, 0, -1):
            rr = ro * j / 18
            c = M.mixc((255, 120, 30), (120, 30, 10), j / 18)
            dl.ellipse((px - rr, py - rr, px + rr, py + rr), fill=M.scale_c(c, core))
        rng = np.random.RandomState(7)
        for j in range(14):  # corrientes del hierro líquido
            a0 = rng.rand() * 6.28 + t * (0.9 + 0.4 * rng.rand()) * (1 if j % 2 else -1)
            rr = ro * (0.45 + 0.5 * rng.rand())
            pts = [(px + rr * math.cos(a0 + s * 0.08), py + rr * 0.9 * math.sin(a0 + s * 0.08)) for s in range(14)]
            dl.line(pts, fill=M.scale_c((255, 200, 120), core * 0.8), width=int(4 * S))
        ri = rp * 0.19
        dl.ellipse((px - ri, py - ri, px + ri, py + ri), fill=M.scale_c((255, 236, 190), core))
        lay = lay.filter(ImageFilter.GaussianBlur(2))
        fr.base.paste(Image.blend(fr.base, lay, 1.0), (0, 0), Image.fromarray((np.asarray(lay.convert('L')) > 3).astype(np.uint8) * 255))
        fr.fx.paste(lay.point(lambda v: int(v * 0.7)), (0, 0), Image.fromarray((np.asarray(lay.convert('L')) > 3).astype(np.uint8) * 255))
    for lat in range(-60, 90, 30):
        th = np.linspace(0, 2 * math.pi, 90)
        r = R * math.cos(math.radians(lat))
        P = np.stack([r * np.cos(th), np.full_like(th, R * math.sin(math.radians(lat))), r * np.sin(th)], 1)
        D._seg_by_depth(fr, D._rot(P, spin), C, camdir)
    for lon in range(0, 180, 20):
        th = np.linspace(0, 2 * math.pi, 90)
        a = math.radians(lon)
        P = np.stack([R * np.cos(th) * math.cos(a), R * np.sin(th), R * np.cos(th) * math.sin(a)], 1)
        D._seg_by_depth(fr, D._rot(P, spin), C, camdir)
    rng = np.random.RandomState(3)
    N = rng.normal(size=(36, 3))
    N = N / np.linalg.norm(N, axis=1, keepdims=True) * R
    for p in D._rot(N, spin):
        front = (p @ camdir) > 0
        dot3(fr, C + p, r=3.2 if front else 2, a=0.95 if front else 0.25, glow=0.9 if front else 0)
    if field > 0.01:
        for L in (1.6, 2.2, 3.0):
            th0 = math.asin(math.sqrt(1 / L))
            th = np.linspace(th0, math.pi - th0, 80)
            for j in range(8):
                ph = j * math.pi / 4
                r = L * R * np.sin(th) ** 2
                P = np.stack([r * np.sin(th) * math.cos(ph), r * np.cos(th), r * np.sin(th) * math.sin(ph)], 1)
                line3(fr, C + D._rot(P, spin * 0.6), col=(200, 230, 255), w=1.6, a=0.75, glow=0.8, frac=field)


def s_earth(t, fi):
    u = rel(t, 3)
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0, 1.25, 0), dist=4.8, yaw=14, pitch=8, cy=0.47)),
                            (4.2, dict(target=(0, 1.25, 0), dist=4.0, yaw=-6, pitch=12, cy=0.47))]))
    space(fr, t, floor=None, bokeh=1.2)
    earth(fr, t, np.array([0, 1.25, 0]), 1.0, t * 0.35)

    def ui(img, fx):
        kicker(img, 'UN IMÁN DEL TAMAÑO DE UN PLANETA', 150, seg(u, 0.1, 0.4))
        photo_card(img, fx, D.PHOTO, 790, 1180, 330, T[3][0] + 3.25, t, caption='NASA · APOLLO 17 · 1972', angle0=-14)
        cap(img, fx, 3, t)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_core(t, fi):
    u = rel(t, 4)
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0, 1.25, 0), dist=3.4, yaw=-6, pitch=10, cy=0.47)),
                            (5.4, dict(target=(0, 1.25, 0), dist=5.4, yaw=20, pitch=14, cy=0.47))]))
    space(fr, t, floor=None, bokeh=1.0)
    earth(fr, t, np.array([0, 1.25, 0]), 1.0, t * 0.35, field=seg(u, 2.4, 4.6), core=eout(seg(u, 0.2, 1.2)))

    def ui(img, fx):
        kicker(img, 'NÚCLEO EXTERNO · HIERRO LÍQUIDO', 150, seg(u, 0.4, 0.8), col=(255, 190, 130))
        pill(img, fx, 540, 300, 'CAMPO MAGNÉTICO', eout(seg(u, 3.0, 3.3)), size=32)
        cap(img, fx, 4, t)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 6. qué tan débil
def s_compare(t, fi):
    u = rel(t, 5)
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=14, cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    t0 = T[5][0]

    def ui(img, fx):
        kicker(img, 'CAMPO MAGNÉTICO · µT (APROX.)', 150, seg(u, -0.1, 0.2))
        chart_grow(img, fx, (90, 300, 990, 1230), [50, 5000], ['TIERRA', 'IMÁN DE REFRI'], t0 - 0.1, t,
                   title_txt='TIERRA vs IMÁN', tag='APROX.', line=False)
        doodle_circle(img, fx, 355, 1080, 160, 70, t, k=eout(seg(u, 0.5, 0.95)), col=(255, 236, 160), w=6)
        title(img, fx, [('100 veces', 'sans'), ('más fuerte.', 'serif')], 1300, seg(u, 2.4, 3.0), size=70)
        cap(img, fx, 5, t, y=1600)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 7. tres ejes
def s_axes(t, fi):
    u = rel(t, 6)
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0, 1.0, 0), dist=4.2, yaw=-40, pitch=16, cy=0.54)),
                            (6.2, dict(target=(0, 1.0, 0), dist=3.6, yaw=-28, pitch=20, cy=0.54))]))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.9)
    ry = 38 * ease(seg(u, 4.2, 5.6))
    head = 12 + ry + 6 * math.sin(t * 1.3)
    draw_objects(fr, [m for m in phone_with(compass_img(head), ry=ry) if m.name != 'in'])
    C = np.array([0, 1.0, 0.12])
    rr = math.radians(ry)
    axes = [((math.cos(rr), 0, -math.sin(rr)), 'X', (255, 120, 110)),
            ((0, 1, 0), 'Y', (140, 240, 170)),
            ((math.sin(rr), 0, math.cos(rr)), 'Z', CYAN)]
    tips = []
    for j, (v, lab, col) in enumerate(axes):
        k = eout(seg(u, 1.6 + 0.3 * j, 2.1 + 0.3 * j))
        if k > 0.01:
            P = [C, C + np.array(v) * 1.05 * k]
            line3(fr, P, col=col, w=5, a=1.0, glow=1.0)
            dot3(fr, P[1], r=8, col=col, a=1.0, glow=1.0)
        tips.append((fr.cam.p1(C + np.array(v) * 1.2), lab, col, k))
    vals = (21.4 + 3 * math.sin(t * 2.1 + ry * 0.05), 4.9 + 0.8 * math.sin(t * 3.3), 38.2 + 2 * math.sin(t * 1.7))

    def ui(img, fx):
        kicker(img, 'LO MIDE EN 3 DIRECCIONES', 150, seg(u, 1.4, 1.7))
        d = ImageDraw.Draw(img)
        for (x, y, _), lab, col, k in tips:
            if k > 0.5:
                d.text((x, y), lab, font=M.font('sans', 52), fill=col, anchor='mm')
        kp = eout(seg(u, 2.6, 3.0))
        if kp > 0.01:
            for j, (lab, v, col) in enumerate(zip('XYZ', vals, [a[2] for a in axes])):
                pill(img, fx, 540, 300 + j * 78, f'{lab}  {v:5.1f} µT', kp, size=30, border=col, dot=True)
        cap(img, fx, 6, t)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 8-9. el imán
def magnet_meshes(x):
    a = named(M3.box(0.22, 0.22, 0.42, (210, 52, 48), shadow=0, base=True, gloss=0.6).tf(t=(0, 0, 0.21)), 'mag', rim=0.6)
    b = named(M3.box(0.22, 0.22, 0.42, (52, 86, 200), shadow=0, base=True, gloss=0.6).tf(t=(0, 0, -0.21)), 'mag', rim=0.6)
    out = []
    for m in (a, b):
        mm = m.tf(ry=90).tf(t=(x, 0.95, 0.25))
        mm.name = m.name
        for at in ('rim', 'gloss'):
            if hasattr(m, at):
                setattr(mm, at, getattr(m, at))
        out.append(mm)
    return out


def s_magnet(t, fi, part=8):
    i = part - 1
    u = rel(t, i)
    if part == 8:
        keys = [(-0.4, dict(target=(0.3, 1.0, 0), dist=4.0, yaw=-10, pitch=6, cy=0.55)),
                (4.6, dict(target=(0.35, 1.0, 0), dist=3.5, yaw=-18, pitch=8, cy=0.55))]
        mx = lerp(2.4, 0.78, eout(seg(u, 1.0, 2.6)))
        crazy = seg(u, 2.7, 3.0)
    else:
        keys = [(-0.4, dict(target=(0.2, 1.0, 0), dist=3.0, yaw=-150, pitch=8, cy=0.55)),
                (2.8, dict(target=(0.2, 1.0, 0), dist=2.6, yaw=-165, pitch=10, cy=0.55))]
        mx = 0.78
        crazy = 1.0
    cam = cam_path(u, keys)
    if crazy > 0 and part == 8:
        cam = Cam(target=cam.target, dist=np.linalg.norm(cam.pos - cam.target), yaw=-18 + 1.2 * math.sin(t * 40) * crazy,
                  pitch=8 + 0.8 * math.sin(t * 33), cy=0.55, roll=1.5 * math.sin(t * 27) * crazy)
    fr = Frame(cam)
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    base = 12 + 26 * math.sin(t * 1.3)
    head = base + crazy * (140 * math.sin(t * 7.3) + 90 * math.sin(t * 13.1))
    warn = crazy if part == 8 else 1.0
    draw_objects(fr, [m for m in phone_with(compass_img(head, warn=warn)) if m.name != 'in'] + magnet_meshes(mx))
    # líneas del imán
    kf = seg(u, 1.6, 2.6) if part == 8 else 1.0
    if kf > 0:
        for j in range(5):
            h = 0.08 + 0.09 * j
            P = [np.array([mx + 0.21 * math.cos(s), 0.95 + h * math.sin(s) * 1.6, 0.25]) for s in np.linspace(0, math.pi, 30)]
            line3(fr, P, col=(255, 150, 140) if part == 9 else (200, 230, 255), w=1.4, a=0.6, glow=0.8, frac=kf)
    if part == 9:  # anillo de imanes de fundas y soportes (atrás del celular)
        ring = [np.array([0.22 * math.cos(a), PH_Y + 0.15 + 0.22 * math.sin(a), -0.02]) for a in np.linspace(0, 2 * math.pi, 60)]
        kr = eout(seg(u, 0.3, 0.9))
        line3(fr, ring, col=(255, 90, 80), w=5, a=1.0, glow=1.2, frac=kr)
        for a in np.linspace(0, 2 * math.pi, 16, endpoint=False):
            if kr > 0.9:
                dot3(fr, np.array([0.22 * math.cos(a), PH_Y + 0.15 + 0.22 * math.sin(a), -0.02]), r=6, col=(255, 120, 100), glow=1.0)
    ringc = fr.cam.p1(np.array([0, PH_Y + 0.15, -0.02]))

    def ui(img, fx):
        if part == 8:
            kicker(img, 'EL TRUCO', 150, seg(u, -0.1, 0.2), col=(255, 236, 160))
            pill(img, fx, 540, 300, 'IMÁN', eout(seg(u, 1.1, 1.4)), size=34, border=(255, 120, 110))
        else:
            kicker(img, 'OJO CON ESTO', 150, seg(u, -0.1, 0.2), col=(255, 150, 140))
            pill(img, fx, 540, 300, 'FUNDAS Y SOPORTES CON IMÁN', eout(seg(u, 0.4, 0.7)), size=32, border=(255, 90, 80))
            doodle_circle(img, fx, ringc[0], ringc[1], 150, 150, t, k=eout(seg(u, 1.0, 1.5)), col=(255, 236, 160), w=6)
        cap(img, fx, i, t)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if part == 9 or crazy > 0.5:  # tinte rojo de error
        a = 0.16 if part == 9 else 0.10 * (0.6 + 0.4 * math.sin(t * 18))
        o = out.astype(np.float32)
        o = o * (1 - a) + np.array([255, 40, 30], np.float32) * a * (o.mean(2, keepdims=True) / 255 + 0.25)
        out = o.clip(0, 255).astype(np.uint8)
    return out


# ------------------------------------------------------------------ 10. el ocho
def s_eight(t, fi):
    u = rel(t, 9)
    fr = Frame(Cam(target=(0, 1.2, 0), dist=7.0, yaw=0, pitch=4, cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)
    glass_type(fr.base, fr.fx, '8', 540 * S, 960 * S, 1000 * S, k=ease(seg(u, 1.6, 2.4)), fill_a=0.05)
    w = 2 * math.pi / 2.2

    def pos(uu):
        ph = max(0.0, uu - 1.4) * w
        return np.array([0.75 * math.sin(2 * ph), 1.2 + 0.95 * math.sin(ph), 0.0]), ph
    p, ph = pos(u)
    moving = u > 1.4
    ok = eout(seg(u, 4.0, 4.4))
    head = 12 + 26 * math.sin(t * 1.3) + (60 * math.sin(t * 9) * (1 - ok) if moving else 0)
    tr = [pos(uu)[0] for uu in np.linspace(max(1.4, u - 2.2), u, 60)] if moving else []
    if len(tr) > 1:
        line3(fr, tr, col=CYAN, w=4, a=0.9, glow=1.2)
    draw_objects(fr, [m for m in phone_with(compass_img(head, ok=ok), ry=25 * math.sin(ph) if moving else 0,
                                            rz=-18 * math.cos(ph) if moving else 0,
                                            off=(p[0], p[1] - PH_Y, 0)) if m.name != 'in'])

    def ui(img, fx):
        kicker(img, 'CALIBRACIÓN · MUEVE EN FORMA DE 8', 150, seg(u, 0.0, 0.3))
        pill(img, fx, 540, 300, 'CALIBRADO', ok, size=34, border=(120, 235, 160))
        cap(img, fx, 9, t, y=1600)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 11. el dato
def s_chart(t, fi):
    u = rel(t, 10)
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=14, cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'LECTURA DEL MAGNETÓMETRO · µT', 150, seg(u, -0.1, 0.2))
        chart_grow(img, fx, (90, 300, 990, 1200), [21, 5, 38, 44], ['X', 'Y', 'Z', 'TOTAL'], T[10][0] - 0.1, t,
                   title_txt='3 EJES + TOTAL', tag='EJEMPLO')
        title(img, fx, [('La Tierra mide', 'sans'), ('entre 25 y 65 µT.', 'serif')], 1270, seg(u, 0.6, 1.2), size=68)
        cap(img, fx, 10, t, y=1610, size=52)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ 12. mándaselo
def s_send(t, fi):
    u = rel(t, 11)
    fr = Frame(cam_path(u, [(-0.4, dict(target=(0, 1.25, 0), dist=6.4, yaw=30, pitch=14, cy=0.5)),
                            (2.6, dict(target=(0, 1.25, 0), dist=5.6, yaw=10, pitch=10, cy=0.5))]))
    space(fr, t, floor=None, bokeh=1.3)
    earth(fr, t, np.array([0, 1.25, 0]), 0.8, t * 0.35, field=1.0)

    def ui(img, fx):
        title(img, fx, [('Mándaselo a alguien', 'sans'), ('que siempre se pierde.', 'serif')], 190, seg(u, 0.0, 0.5), size=74)
        cap(img, fx, 11, t)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ montaje
def frame_at(t, fi):
    c = [a - 0.2 for a, _ in T]  # cortes: un poco antes de cada frase
    if t < c[1] - 0.2:
        return s_hook(t, fi)
    if t < c[1] + 0.15:   # whip
        return tr_whip(s_hook(t, fi), s_nogps(t, fi), seg(t, c[1] - 0.2, c[1] + 0.15), 1)
    if t < c[2] - 0.2:
        return s_nogps(t, fi)
    if t < c[2] + 0.15:   # atraviesa la pantalla
        return tr_zoom_through(s_nogps(t, fi), s_xray(t, fi)[0], seg(t, c[2] - 0.2, c[2] + 0.15), 0.5, 0.52)
    if t < c[3] - 0.35:
        return s_xray(t, fi)[0]
    if t < c[3]:          # acercamiento exponencial al chip
        img, (cx, cy) = s_xray(t, fi, zoom=False)
        return push_in(img, seg(t, c[3] - 0.35, c[3]), cx, cy, zmax=3.2)
    if t < c[4] - 0.2:
        return flash_in(s_earth(t, fi), t, c[3], 0.2, 160)
    if t < c[4] + 0.2:    # entra a la Tierra
        return tr_zoom_through(s_earth(t, fi), s_core(t, fi), seg(t, c[4] - 0.2, c[4] + 0.2), 0.5, 0.45)
    if t < c[5] - 0.2:
        return s_core(t, fi)
    if t < c[5] + 0.15:   # barrido vertical
        return tr_wipe_v(s_core(t, fi), s_compare(t, fi), seg(t, c[5] - 0.2, c[5] + 0.15))
    if t < c[6] - 0.2:
        return s_compare(t, fi)
    if t < c[6] + 0.15:
        return tr_zoom_through(s_compare(t, fi), s_axes(t, fi), seg(t, c[6] - 0.2, c[6] + 0.15), 0.5, 0.5)
    if t < c[7] - 0.2:
        return s_axes(t, fi)
    if t < c[7] + 0.15:
        return tr_whip(s_axes(t, fi), s_magnet(t, fi, 8), seg(t, c[7] - 0.2, c[7] + 0.15), -1)
    if t < c[8] - 0.15:
        return s_magnet(t, fi, 8)
    if t < c[8] + 0.15:
        return tr_whip(s_magnet(t, fi, 8), s_magnet(t, fi, 9), seg(t, c[8] - 0.15, c[8] + 0.15), 1)
    if t < c[9] - 0.2:
        return s_magnet(t, fi, 9)
    if t < c[9] + 0.2:    # destello
        return tr_flash(s_magnet(t, fi, 9), s_eight(t, fi), seg(t, c[9] - 0.2, c[9] + 0.2))
    if t < c[10] - 0.2:
        return s_eight(t, fi)
    if t < c[10] + 0.15:
        return tr_wipe_v(s_eight(t, fi), s_chart(t, fi), seg(t, c[10] - 0.2, c[10] + 0.15))
    if t < c[11] - 0.36:
        return s_chart(t, fi)
    if t < c[11] - 0.24:  # cortes rítmicos
        return flash_in(s_xray(T[2][0] + 3.0, fi)[0], t, c[11] - 0.36, 0.12, 90)
    if t < c[11] - 0.12:
        return flash_in(s_magnet(T[7][0] + 3.2, fi, 8), t, c[11] - 0.24, 0.12, 90)
    if t < c[12] - 0.2:
        return flash_in(s_send(t, fi), t, c[11] - 0.12, 0.15, 100)
    if t < c[12] + 0.15:
        return tr_zoom_through(s_send(t, fi), s_hook(t - DUR, fi, end=True), seg(t, c[12] - 0.2, c[12] + 0.15), 0.5, 0.5)
    return s_hook(t - DUR, fi, end=True)  # termina en el primer cuadro (loop)


def _work(fi):
    return fi, frame_at(fi / FPS, fi).tobytes()


def render(out):
    from multiprocessing import Pool
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    with Pool(2) as pool:
        for fi, buf in pool.imap(_work, range(NF), chunksize=2):
            p.stdin.write(buf)
            if fi % 120 == 0:
                print('cuadro', fi, '/', NF, flush=True)
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        for ts in sys.argv[2:]:
            t = float(ts)
            Image.fromarray(frame_at(t, int(t * FPS))).save(f'/home/claude/nprev_{ts}.png')
    else:
        render(sys.argv[2] if len(sys.argv) > 2 else '/home/claude/norte_sin_audio.mp4')
