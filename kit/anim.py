import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 720, 1280
S = W / 1080.0
FPS = 24
DUR = 27.5
NF = int(DUR * FPS)

VIOLET = (150, 95, 255)
BLUE = (70, 175, 255)
CYAN = (170, 230, 255)
ORANGE = (255, 140, 50)
COPPER = (225, 140, 95)

B = ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
R = ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
M = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
_fc = {}


def F(paths, size):
    key = (paths[0], size)
    if key not in _fc:
        for p in paths:
            if os.path.exists(p):
                _fc[key] = ImageFont.truetype(p, max(8, int(size * S)))
                break
    return _fc[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, x):
    return a + (b - a) * x


def lc(c1, c2, x):
    return tuple(lerp(c1[i], c2[i], x) for i in range(3))


def sc3(c, a):
    return tuple(int(max(0, min(255, v * a))) for v in c)


def P(x, y):
    return (x * S, y * S)


# ---------------- fondo ----------------
yy, xx = np.mgrid[0:H, 0:W]
d = np.sqrt(((xx - W * 0.5) / (W * 0.9)) ** 2 + ((yy - H * 0.60) / (H * 0.5)) ** 2)
vig = np.clip(1 - d, 0, 1) ** 2
BG = np.zeros((H, W, 3), np.float32)
BG += np.array([7, 7, 13], np.float32)
BG += vig[..., None] * np.array([38, 16, 66], np.float32)
BG_IMG = Image.fromarray(BG.astype(np.uint8))

rng = np.random.RandomState(7)
STARS = [(rng.uniform(20, 1060), rng.uniform(20, 1900), rng.uniform(0, 6.28), rng.uniform(2, 4.5)) for _ in range(75)]

# ---------------- arcos de campo ----------------
CX, Y0 = 540, 1335
N = 56
ARCS = []
for k in range(5):
    dk = 160 + k * 80
    hk = 220 + k * 110
    for side in (-1, 1):
        pts = []
        for i in range(N + 1):
            phi = math.pi * i / N
            pts.append((CX + side * (dk / 2) * (1 - math.cos(phi)), Y0 - hk * math.sin(phi)))
        ARCS.append((k, side, pts))

OFFS = (-270, -220, -170, -120, 120, 170, 220, 270)

# ---------------- subtítulos ----------------
PHR = [
    (0.3, 2.8, "Tu celular se carga sin cables...", {5}),
    (2.9, 5.8, "¿Cómo cruza la energía por el aire?", {3, 6}),
    (6.0, 8.6, "Dentro del cargador hay una bobina de cobre,", {5}),
    (8.7, 10.9, "que crea un campo magnético que cambia", {4}),
    (11.0, 12.9, "más de cien mil veces por segundo.", {3}),
    (13.0, 14.9, "Tu celular tiene otra bobina.", {4}),
    (15.0, 17.6, "El campo la atraviesa y mueve los electrones.", {7}),
    (17.7, 19.6, "Se llama inducción electromagnética.", {2}),
    (19.8, 21.4, "La batería empieza a cargarse,", {1}),
    (21.5, 24.3, "pero parte de la energía se escapa como calor.", {8}),
]
CAP = 64
Y_CAP = 270


def build_phrases():
    out = []
    fb, fr = F(B, CAP), F(R, CAP)
    maxw = 900 * S
    sp = fb.getlength(" ")
    lh = CAP * 1.3 * S
    for (a, b, text, keys) in PHR:
        words = text.split(" ")
        widths = [max(fb.getlength(w), fr.getlength(w)) for w in words]
        lines, cur, cw = [], [], 0
        for i, w in enumerate(words):
            add = widths[i] + (sp if cur else 0)
            if cur and cw + add > maxw:
                lines.append(cur)
                cur, cw = [i], widths[i]
            else:
                cur.append(i)
                cw += add
        lines.append(cur)
        pos = {}
        y0 = Y_CAP * S - (len(lines) - 1) * lh / 2
        for li, line in enumerate(lines):
            tw = sum(widths[i] for i in line) + sp * (len(line) - 1)
            x = (W - tw) / 2
            for i in line:
                pos[i] = (x, widths[i], y0 + li * lh)
                x += widths[i] + sp
        wts = [len(w) + 2 for w in words]
        tot = sum(wts)
        starts, acc = [], a
        for wt in wts:
            starts.append(acc)
            acc += (b - a) * wt / tot
        out.append(dict(a=a, b=b, words=words, pos=pos, starts=starts, keys=keys))
    return out


PH = build_phrases()


def glow_of(L, rad=4):
    small = L.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(rad))
    return np.asarray(small.resize((W, H), Image.BILINEAR), dtype=np.float32)


def draw_caption(ld, t):
    fb, fr = F(B, CAP), F(R, CAP)
    for ph in PH:
        if ph['a'] <= t < ph['b'] + 0.3:
            cur = max(i for i, s in enumerate(ph['starts']) if s <= t)
            for i in range(cur + 1):
                x, w, y = ph['pos'][i]
                word = ph['words'][i]
                f, col = (fb, (255, 255, 255)) if i == cur else (fr, (125, 125, 150))
                tw = f.getlength(word)
                ld.text((x + (w - tw) / 2, y), word, font=f, fill=col, anchor="lm")
            if cur in ph['keys']:
                x, w, y = ph['pos'][cur]
                pad = 10 * S
                hh = 0.62 * CAP * S
                box = (x - pad, y - hh, x + w + pad, y + hh)
                bc = (90, 140, 255)
                ld.rectangle(box, outline=bc, width=2)
                s = 7 * S
                for cxp, cyp in ((box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])):
                    ld.rectangle((cxp - s / 2, cyp - s / 2, cxp + s / 2, cyp + s / 2), fill=(15, 15, 40), outline=bc, width=2)


def render(t):
    base = BG_IMG.copy()
    bd = ImageDraw.Draw(base)
    L1 = Image.new("RGB", (W, H), (0, 0, 0))
    l1 = ImageDraw.Draw(L1)
    L2 = Image.new("RGB", (W, H), (0, 0, 0))
    l2 = ImageDraw.Draw(L2)

    heat = seg(t, 21.5, 23.0)
    ypos = 1050 - (1 - ease(seg(t, 0.2, 2.6))) * 350
    chg = seg(t, 5.8, 6.8)
    phg = seg(t, 12.8, 13.8)
    lw = max(2, int(4 * S))

    # estrellas
    for (x, y, ph, r) in STARS:
        a = 0.25 + 0.25 * math.sin(t * 1.4 + ph)
        px, py = P(x, y)
        rr = r * S * 0.7
        l1.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3((200, 190, 255), a))

    # cargador
    bd.rounded_rectangle((*P(190, 1290), *P(890, 1385)), radius=int(38 * S), fill=(19, 21, 35), outline=(66, 58, 112), width=2)
    l1.line([P(235, 1291), P(845, 1291)], fill=sc3(VIOLET, 0.55 + 0.25 * chg), width=lw)

    # teléfono
    bd.rounded_rectangle((*P(260, ypos), *P(820, ypos + 64)), radius=int(24 * S), fill=(25, 27, 43), outline=(92, 86, 142), width=2)
    l1.line([P(295, ypos + 2), P(785, ypos + 2)], fill=sc3(VIOLET, 0.30), width=max(1, int(3 * S)))

    # arcos de campo
    arcs_on = 0.5 * ease(seg(t, 2.8, 4.5)) + 0.5 * ease(seg(t, 6.0, 7.2))
    for (k, side, pts) in ARCS:
        base_col = lc(lc(VIOLET, BLUE, k / 4.0), ORANGE, 0.5 * heat)
        for i in range(N):
            if pts[i][1] > 1286 or pts[i + 1][1] > 1286:
                continue
            u = (i + 0.5) / N
            pulse = (0.5 + 0.5 * math.sin(2 * math.pi * (1.6 * t - u * 1.0 - k * 0.15))) ** 2
            a = arcs_on * (0.16 + 0.84 * pulse)
            l1.line([P(*pts[i]), P(*pts[i + 1])], fill=sc3(base_col, a), width=lw)
        for j in range(2):
            u = (t * 0.28 + k * 0.17 + j * 0.5) % 1.0
            x, y = pts[int(u * N)]
            if y < 1286:
                rr = 5 * S
                px, py = P(x, y)
                l1.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, arcs_on))

    # bobinas
    pc = 0.65 + 0.35 * math.sin(2 * math.pi * 3.0 * t)
    pp = 0.65 + 0.35 * math.sin(2 * math.pi * 3.0 * t + 1.1)
    ring = lc(VIOLET, ORANGE, 0.75 * heat)
    for ox in OFFS:
        x = CX + ox
        r1 = 15 * S
        px, py = P(x, 1335)
        bd.ellipse((px - r1, py - r1, px + r1, py + r1), fill=COPPER)
        r2 = 19 * S
        l1.ellipse((px - r2, py - r2, px + r2, py + r2), outline=sc3(ring, chg * pc), width=lw)
        r3 = 11 * S
        px, py = P(x, ypos + 44)
        bd.ellipse((px - r3, py - r3, px + r3, py + r3), fill=COPPER)
        r4 = 15 * S
        l1.ellipse((px - r4, py - r4, px + r4, py + r4), outline=sc3(ring, phg * pp), width=lw)

    # cable interno del teléfono y electrones
    if phg > 0:
        l1.line([P(CX - 270, ypos + 18), P(CX + 270, ypos + 18)], fill=sc3(VIOLET, 0.35 * phg), width=max(1, int(3 * S)))
    el = seg(t, 14.8, 15.6)
    if el > 0:
        for i in range(10):
            x = CX + (i - 4.5) * 52 + 24 * math.sin(2 * math.pi * 1.5 * t)
            rr = 6 * S
            px, py = P(x, ypos + 18)
            l1.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, el))

    # ondas de calor
    hon = seg(t, 21.6, 22.6) * (1 - seg(t, 24.0, 24.6))
    if hon > 0:
        for x0 in (CX - 160, CX - 80, CX, CX + 80, CX + 160):
            prev = None
            for j in range(31):
                u = j / 30.0
                y = ypos - 10 - u * 150
                x = x0 + 16 * math.sin(7 * u - t * 5 + x0 * 0.05)
                if prev is not None:
                    l1.line([P(*prev), P(x, y)], fill=sc3(ORANGE, hon * (1 - u) * 0.9), width=lw)
                prev = (x, y)

    # batería
    bon = seg(t, 19.8, 20.6) * (1 - seg(t, 24.0, 24.6))
    level = 0.78 * ease(seg(t, 19.9, 24.0))
    if bon > 0:
        l1.rounded_rectangle((*P(430, 720), *P(650, 830)), radius=int(18 * S), outline=sc3(BLUE, bon), width=max(2, int(6 * S)))
        l1.rectangle((*P(650, 755), *P(668, 795)), fill=sc3(BLUE, bon))
        if level > 0.01:
            l1.rounded_rectangle((*P(442, 732), *P(442 + 196 * level / 0.78 * 0.78, 818)), radius=int(10 * S), fill=sc3(BLUE, 0.55 * bon))

    # combinar capa 1
    arr = np.asarray(base, dtype=np.float32)
    arr = arr + np.asarray(L1, dtype=np.float32) + 1.5 * glow_of(L1, 4)
    dimf = 1 - 0.92 * seg(t, 24.6, 25.4)
    arr = arr * dimf

    # ---------- overlays (capa 2) ----------
    draw_caption(l2, t)

    def label(txt, x, y, anchor, a, tx=None, ty0=None, ty1=None):
        if a <= 0:
            return
        l2.text(P(x, y), txt, font=F(B, 30), fill=sc3((185, 185, 225), a), anchor=anchor)
        if tx is not None:
            l2.line([P(tx, ty0), P(tx, ty1)], fill=sc3((140, 140, 200), a), width=max(1, int(2 * S)))

    a1 = seg(t, 6.0, 6.6) * (1 - seg(t, 12.8, 13.4))
    label("BOBINA DEL CARGADOR", 230, 1485, "lm", a1, 270, 1462, 1354)
    a2 = seg(t, 13.0, 13.6) * (1 - seg(t, 19.2, 19.8))
    label("BOBINA DEL CELULAR", 840, 985, "rm", a2, 760, 1002, 1082)

    # contador
    ca = seg(t, 8.7, 9.3) * (1 - seg(t, 13.0, 13.6))
    if ca > 0:
        val = int(100000 * ease(seg(t, 8.8, 11.8)))
        txt = f"{val:,}" + ("+" if val >= 100000 else "")
        l2.text(P(CX, 520), txt, font=F(M, 112), fill=sc3((235, 225, 255), ca), anchor="mm")
        l2.text(P(CX, 610), "VECES POR SEGUNDO", font=F(B, 34), fill=sc3((170, 160, 230), ca), anchor="mm")
        l2.rectangle((*P(150, 445), *P(930, 655)), outline=sc3((100, 90, 190), ca * 0.8), width=max(1, int(2 * S)))

    # chip Faraday
    fa = seg(t, 17.7, 18.3) * (1 - seg(t, 19.3, 19.8))
    if fa > 0:
        l2.rounded_rectangle((*P(300, 1560), *P(780, 1640)), radius=int(40 * S), outline=sc3(BLUE, fa), width=max(2, int(3 * S)))
        l2.text(P(CX, 1600), "FARADAY · 1831", font=F(B, 38), fill=sc3((220, 235, 255), fa), anchor="mm")

    # porcentaje de batería
    if bon > 0:
        l2.text(P(540, 775), f"{int(level * 100)}%", font=F(B, 52), fill=sc3((255, 255, 255), bon), anchor="mm")

    # etiqueta de calor
    if hon > 0:
        l2.text(P(CX, 862), "PARTE SE PIERDE COMO CALOR", font=F(B, 30), fill=sc3((255, 190, 130), hon), anchor="mm")

    # cierre
    ta = seg(t, 24.9, 25.8)
    if ta > 0:
        l2.text(P(CX, 900), "Mente en órbita", font=F(B, 112), fill=sc3((240, 235, 255), ta), anchor="mm")
        ang = 2 * math.pi * (t - 24.9) / 3.0
        ox, oy = CX + 440 * math.cos(ang), 900 + 130 * math.sin(ang)
        l2.ellipse((*P(CX - 440, 900 - 130), *P(CX + 440, 900 + 130)), outline=sc3(VIOLET, 0.45 * ta), width=max(1, int(2 * S)))
        rr = 9 * S
        px, py = P(ox, oy)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, ta))
    sa = seg(t, 25.4, 26.2)
    if sa > 0:
        l2.text(P(CX, 1040), "¿Qué quieres que explique después?", font=F(R, 42), fill=sc3((190, 190, 230), sa), anchor="mm")

    arr = arr + np.asarray(L2, dtype=np.float32) + 1.2 * glow_of(L2, 3)
    fade = seg(t, 0.0, 0.4) * (1 - seg(t, DUR - 0.5, DUR))
    arr = arr * fade
    return np.clip(arr, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        os.makedirs("/home/claude/prev", exist_ok=True)
        for ts in sys.argv[2:]:
            t = float(ts)
            Image.fromarray(render(t)).save(f"/home/claude/prev/t_{ts}.png")
        print("ok")
    else:
        out = sys.argv[2]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(NF):
            pr.stdin.write(render(f / FPS).tobytes())
            if f % 48 == 0:
                print(f, NF, flush=True)
        pr.stdin.close()
        pr.wait()
        print("done", flush=True)
