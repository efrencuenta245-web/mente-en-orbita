"""Prueba del estilo nuevo (12.9 s, sin voz): ¿cómo sabe tu celular dónde está el norte?
Muestra: espacio y transiciones tipo @alyxianews, objeto semirrealista tipo video del metro,
efectos del video 2 (letras de cristal, atraviesa la escena, celular con vida, garabatos vivos,
zoom digital, gráfico que crece, foto real que cae), imagen real de internet (NASA, dominio público)
y efectos de sonido. Uso: python3 demo_estilo.py [preview T | render]"""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motor2 as M
from motor2 import (W, H, FPS, Frame, Cam, cam_path, space, draw_objects, named, finish, title, kicker,
                    word_caption, pill, glass_type, doodle_circle, rec_frame, chart_grow, photo_card,
                    tr_zoom_through, tr_flash, push_in, line3, dot3, seg, ease, eout, clamp, lerp, WHITE, CYAN)
M3 = M.M3

DUR = 12.9
NF = int(round(DUR * FPS))
PHOTO = Image.open(os.path.join(HERE, '..', '..', 'inbox', 'img_bluemarble.jpg')).convert('RGB')

# ------------------------------------------------------------------ el celular (semirrealista)
PH_Y = 0.95


def compass_screen(t):
    w, h = 420, 900
    im = Image.new('RGB', (w, h), (6, 7, 10))
    d = ImageDraw.Draw(im)
    f = M.font
    d.text((34, 26), '9:41', font=f('sanss', 26), fill=(230, 230, 232))
    d.rounded_rectangle((w - 80, 32, w - 34, 52), radius=6, outline=(200, 200, 200), width=2)
    head = (12 + 26 * math.sin(t * 1.3)) % 360
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
    d.text((w / 2, 720), 'Brújula', font=f('sanss', 30), fill=(200, 200, 204), anchor='mm')
    d.rounded_rectangle((w / 2 - 70, h - 34, w / 2 + 70, h - 26), radius=4, fill=(200, 200, 204))
    # reflejo diagonal del cristal
    gl = Image.new('L', (w, h), 0)
    ImageDraw.Draw(gl).polygon([(w * 0.55, 0), (w * 0.85, 0), (w * 0.15, h), (-w * 0.15, h)], fill=20)
    im.paste((255, 255, 255), (0, 0), gl)
    return im


def phone(t, ry=0.0, with_screen=True):
    body = M3.rbox(0.75, 0.08, 1.56, 0.11, (64, 66, 72), n=6, shadow=0, gloss=0.55)
    body = named(body, 'body', rim=0.75, gloss=0.55)
    scr = M3.box(0.69, 0.006, 1.48, (8, 9, 12), shadow=0, base=True, gloss=0.9).tf(t=(0, 0.08, 0))
    scr = named(scr, 'screen', gloss=0.9, rim=0.2)
    if with_screen:
        M3.decal(scr, scr.FACE['top'], compass_screen(t).convert('RGBA'))
    parts = [body, scr]
    btn = named(M3.box(0.02, 0.03, 0.18, (90, 92, 98), shadow=0, base=True, gloss=0.6).tf(t=(0.385, 0.025, -0.3)), 'btn')
    parts.append(btn)
    # interior (se ve con rayos X)
    inn = []
    inn.append(named(M3.box(0.6, 0.03, 0.78, (46, 48, 54), shadow=0, base=True, gloss=0.35).tf(t=(0, 0.02, 0.3)), 'in', rim=0.3))
    inn.append(named(M3.box(0.64, 0.012, 0.52, (16, 46, 38), shadow=0, base=True, gloss=0.4).tf(t=(0, 0.02, -0.42)), 'in', rim=0.3))
    inn.append(named(M3.box(0.1, 0.022, 0.1, (22, 22, 24), shadow=0, base=True, gloss=0.7).tf(t=(0.16, 0.032, -0.5)), 'in', rim=0.4))
    for i in range(4):
        for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            off = -0.03 + 0.02 * i
            px = 0.16 + (sx * 0.058 if sx else off)
            pz = -0.5 + (sz * 0.058 if sz else off)
            inn.append(named(M3.box(0.012 if sx else 0.008, 0.008, 0.008 if sx else 0.012, (214, 172, 82), shadow=0, base=True, gloss=0.95)
                             .tf(t=(px, 0.032, pz)), 'in', rim=0.2))
    inn.append(named(M3.box(0.16, 0.022, 0.13, (40, 40, 44), shadow=0, base=True, gloss=0.6).tf(t=(-0.12, 0.032, -0.36)), 'in'))
    inn.append(named(M3.cyl(0.075, 0.03, (30, 30, 34), n=24, shadow=0, gloss=0.8).tf(t=(-0.18, 0.03, -0.62)), 'in'))
    inn.append(named(M3.cyl(0.04, 0.032, (12, 14, 30), n=20, shadow=0, gloss=1.0).tf(t=(-0.18, 0.03, -0.62)), 'in'))
    for m in inn:
        m.double = False
    out = []
    for m in parts + inn:
        mm = m.tf(rx=90).tf(ry=ry, t=(0, PH_Y, 0))
        mm.name = m.name
        for a in ('rim', 'gloss', 'glow'):
            if hasattr(m, a):
                setattr(mm, a, getattr(m, a))
        out.append(mm)
    return out


CHIP = np.array([0.16, PH_Y + 0.5, 0.04])


def shadow_blob(fr, cx, cy, rx, ry, a=0.7):
    lay = Image.new('L', (M.GW // 4, M.GH // 4), 0)
    s = 4
    ImageDraw.Draw(lay).ellipse(((cx - rx) / s, (cy - ry) / s, (cx + rx) / s, (cy + ry) / s), fill=int(200 * a))
    from PIL import ImageFilter
    lay = lay.filter(ImageFilter.GaussianBlur(8)).resize((M.GW, M.GH), Image.BILINEAR)
    fr.base.paste((0, 0, 0), (0, 0), lay)


# ------------------------------------------------------------------ escenas
K1 = [(-0.9, dict(target=(0, 0.95, 0), dist=4.4, yaw=-38, pitch=10, fk=1.5, cy=0.56)),
      (0.0, dict(target=(0, 0.95, 0), dist=3.7, yaw=-26, pitch=7, fk=1.5, cy=0.56)),
      (2.6, dict(target=(0, 0.98, 0), dist=3.0, yaw=-10, pitch=5, fk=1.5, cy=0.56))]


def s_hook(t, fi):
    fr = Frame(cam_path(t, K1))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    x, y, _ = fr.cam.proj([(0, 0.02, 0)])[0][0].tolist() + [0]
    shadow_blob(fr, x, y, 330, 70, 0.8)
    S = M.SS
    glass_type(fr.base, fr.fx, 'NORTE', 540 * S, 1130 * S, 250 * S, k=ease(seg(t, -0.6, 0.4)), fill_a=0.07)
    ph = phone(max(0.0, t))
    draw_objects(fr, [m for m in ph if m.name != 'in'])
    k_t = seg(t, 0.15, 0.75)
    k_k = seg(t, 0.55, 0.95)

    def ui(img, fx):
        kicker(img, 'MAGNETÓMETRO · 3 EJES', 132, k_k)
        title(img, fx, [('Tu celular', 'sans'), ('sabe dónde está el norte.', 'serif')], 190, k_t, size=78)
    fr.ui.append(ui)
    return finish(fr, fi)


K2 = [(2.5, dict(target=(0, 1.25, 0), dist=4.6, yaw=10, pitch=8, fk=1.5, cy=0.47)),
      (5.6, dict(target=(0, 1.25, 0), dist=4.0, yaw=-6, pitch=12, fk=1.5, cy=0.47))]
TILT = math.radians(11)


def _rot(P, spin):
    c, s = math.cos(spin), math.sin(spin)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    x, z = x * c + z * s, -x * s + z * c
    ct, st = math.cos(TILT), math.sin(TILT)
    x, y = x * ct - y * st, x * st + y * ct
    return np.stack([x, y, z], 1)


def s_earth(t, fi):
    fr = Frame(cam_path(t, K2))
    space(fr, t, floor=None, bokeh=1.2)
    C = np.array([0, 1.25, 0])
    R = 1.0
    spin = t * 0.35
    camdir = M.norm(fr.cam.pos - C)
    for lat in range(-60, 90, 30):
        th = np.linspace(0, 2 * math.pi, 90)
        r = R * math.cos(math.radians(lat))
        P = np.stack([r * np.cos(th), np.full_like(th, R * math.sin(math.radians(lat))), r * np.sin(th)], 1)
        _seg_by_depth(fr, _rot(P, spin), C, camdir)
    for lon in range(0, 180, 20):
        th = np.linspace(0, 2 * math.pi, 90)
        a = math.radians(lon)
        P = np.stack([R * np.cos(th) * math.cos(a), R * np.sin(th), R * np.cos(th) * math.sin(a)], 1)
        _seg_by_depth(fr, _rot(P, spin), C, camdir)
    rng = np.random.RandomState(3)
    N = rng.normal(size=(36, 3))
    N = N / np.linalg.norm(N, axis=1, keepdims=True) * R
    for p in _rot(N, spin):
        front = (p @ camdir) > 0
        dot3(fr, C + p, r=3.2 if front else 2, a=0.95 if front else 0.25, glow=0.9 if front else 0)
    # líneas del campo magnético (dipolo inclinado ~11°)
    kf = seg(t, 3.15, 4.4)
    for L in (1.75, 2.5):
        th0 = math.asin(math.sqrt(1 / L))
        th = np.linspace(th0, math.pi - th0, 80)
        for j in range(8):
            ph = j * math.pi / 4
            r = L * R * np.sin(th) ** 2
            P = np.stack([r * np.sin(th) * math.cos(ph), r * np.cos(th), r * np.sin(th) * math.sin(ph)], 1)
            P = _rot(P, spin * 0.6)
            line3(fr, C + P, col=(200, 230, 255), w=1.6, a=0.75, glow=0.8, frac=kf)

    def ui(img, fx):
        kicker(img, 'LA TIERRA · DIPOLO MAGNÉTICO', 150, seg(t, 3.0, 3.3))
        photo_card(img, fx, PHOTO, 790, 1180, 330, 3.6, t, caption='NASA · APOLLO 17 · 1972', angle0=-14)
        word_caption(img, fx, 'La Tierra es un imán gigante.'.split(), 3.15, t, y=1560, size=60)
    fr.ui.append(ui)
    return finish(fr, fi)


def _seg_by_depth(fr, P, C, camdir):
    front = (P @ camdir) > -0.05
    cur, curf = [], None
    for p, f in zip(P, front):
        if curf is None or f == curf:
            cur.append(C + p)
        else:
            if len(cur) > 1:
                line3(fr, cur, w=1.5 if curf else 1.0, a=0.85 if curf else 0.18, glow=0.55 if curf else 0)
            cur = [cur[-1], C + p]
        curf = f
    if len(cur) > 1:
        line3(fr, cur, w=1.5 if curf else 1.0, a=0.85 if curf else 0.18, glow=0.55 if curf else 0)


K3 = [(5.5, dict(target=(0.0, 0.98, 0), dist=3.1, yaw=-14, pitch=6, fk=1.5, cy=0.52)),
      (9.0, dict(target=(0.06, 1.1, 0), dist=2.6, yaw=8, pitch=8, fk=1.5, cy=0.52))]


def chip_screen(cam):
    x, y, _ = cam.p1(CHIP)
    return x, y


def s_xray(t, fi, zoom=True):
    fr = Frame(cam_path(t, K3))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    ph = phone(t)
    xr = seg(t, 6.0, 6.55)
    draw_objects(fr, ph, xray=xr, keep=('in',))
    cx, cy = chip_screen(fr.cam)

    def ui(img, fx):
        kicker(img, 'RAYOS X · ASÍ SE VE POR DENTRO', 150, seg(t, 6.1, 6.4), col=(150, 210, 230))
        k_p = eout(seg(t, 6.6, 6.9))
        if k_p > 0:
            d = ImageDraw.Draw(img)
            lx, ly = cx + 70, cy - 210
            d.line([(cx + 26, cy - 22), (lx, ly + 40), (lx + 40, ly + 40)], fill=M.scale_c(CYAN, k_p), width=3)
            pill(img, fx, lx + 40, ly + 40, 'Magnetómetro', k_p, size=30, anchor='l')
        doodle_circle(img, fx, cx, cy, 72, 64, t, k=eout(seg(t, 7.0, 7.45)), col=(255, 236, 160), w=6)
        word_caption(img, fx, 'Mide el campo en 3 ejes.'.split(), 7.0, t, y=1560, size=60)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if zoom:
        z = 1.0 if t < 7.5 else (1.3 if t < 8.0 else 1.8)
        if z > 1:
            out = M.scale_about(out, z, cx / W, cy / H)
            im = Image.fromarray(out)
            rec_frame(im, t, 1.0, f'x{z:.1f}')
            out = np.asarray(im)
    return out, (cx / W, cy / H)


def s_chart(t, fi):
    fr = Frame(Cam(target=(0, 0.6, 0), dist=6, yaw=0, pitch=14, cy=0.62))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)

    def ui(img, fx):
        kicker(img, 'LECTURA DEL MAGNETÓMETRO · µT', 150, seg(t, 9.35, 9.6))
        chart_grow(img, fx, (90, 330, 990, 1260), [21, 5, 38, 44], ['X', 'Y', 'Z', 'TOTAL'], 9.35, t,
                   title_txt='3 EJES + TOTAL', tag='EJEMPLO')
        title(img, fx, [('La Tierra mide', 'sans'), ('entre 25 y 65 µT.', 'serif')], 1390, seg(t, 10.7, 11.3), size=74)
    fr.ui.append(ui)
    return finish(fr, fi)


# ------------------------------------------------------------------ montaje
def frame_at(t, fi):
    if t < 2.6:
        return s_hook(t, fi)
    if t < 2.95:  # atraviesa la escena: entra por la brújula de la pantalla
        k = seg(t, 2.6, 2.95)
        A = s_hook(t, fi)
        B = s_earth(t, fi)
        return tr_zoom_through(A, B, k, 0.5, 0.52)
    if t < 5.55:
        return s_earth(t, fi)
    if t < 5.95:  # destello de sobreexposición
        k = seg(t, 5.55, 5.95)
        return tr_flash(s_earth(t, fi), s_xray(t, fi)[0], k)
    if t < 8.9:
        return s_xray(t, fi)[0]
    if t < 9.3:  # acercamiento exponencial al chip y corte
        img, (cx, cy) = s_xray(t, fi, zoom=False)
        k = seg(t, 8.9, 9.3)
        return push_in(img, k, cx, cy, zmax=3.2)
    if t < 11.9:
        out = s_chart(t, fi)
        if t < 9.42:  # destello del corte
            out = (out.astype(np.float32) + 120 * (1 - seg(t, 9.3, 9.42))).clip(0, 255).astype(np.uint8)
        return out
    if t < 12.05:  # cortes rítmicos
        img, (cx, cy) = s_xray(8.6, fi, zoom=False)
        img = M.scale_about(img, 1.8, cx, cy)
        return (img.astype(np.float32) + 90 * (1 - seg(t, 11.9, 12.05))).clip(0, 255).astype(np.uint8)
    # regreso al inicio (loop): termina en el primer cuadro
    tt = t - DUR
    out = s_hook(tt, fi)
    if t < 12.15:
        out = (out.astype(np.float32) + 90 * (1 - seg(t, 12.05, 12.15))).clip(0, 255).astype(np.uint8)
    return out


def _work(fi):
    return fi, frame_at(fi / FPS, fi).tobytes()


def render(out):
    from multiprocessing import Pool
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    with Pool(2) as pool:
        for fi, buf in pool.imap(_work, range(NF), chunksize=2):
            p.stdin.write(buf)
            if fi % 24 == 0:
                print('cuadro', fi, '/', NF, flush=True)
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        for ts in sys.argv[2:]:
            t = float(ts)
            Image.fromarray(frame_at(t, int(t * FPS))).save(f'/home/claude/prev_{ts}.png')
    else:
        render(sys.argv[2] if len(sys.argv) > 2 else '/home/claude/demo_sin_audio.mp4')
