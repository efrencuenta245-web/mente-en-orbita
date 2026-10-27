import math, os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import anim
from anim import (W, H, S, F, B, R, M, seg, ease, lerp, lc, sc3, P, clamp, glow_of,
                  BG_IMG, STARS, VIOLET, BLUE, CYAN, ORANGE, COPPER)

FPS = 24
FOC = 1200.0
TIMING = "/home/claude/timing.json"

# ---------- tiempos (se pueden reemplazar con timing.json cuando haya audio) ----------
DUR = 27.5
if os.path.exists(TIMING):
    tj = json.load(open(TIMING))
    DUR = tj["dur"]
    base = list(anim.PHR)
    newp = []
    for i, (a, b) in enumerate(tj["phrases"]):
        if i < len(base):
            newp.append((a, b, base[i][2], base[i][3]))
        else:
            newp.append((a, b, tj["extra_text"], {3}))
    anim.PHR = newp
    anim.PH = anim.build_phrases()
    for key, anc in tj.get("anchors", {}).items():
        ph = anim.PH[int(key)]
        words = ph["words"]
        wts = [len(w) + 2 for w in words]
        pts = [(int(w), t) for w, t in anc] + [(len(words), ph["b"])]
        for (wi, ti), (wj, tj2) in zip(pts[:-1], pts[1:]):
            tot = sum(wts[wi:wj])
            acc = ti
            for k in range(wi, wj):
                ph["starts"][k] = acc
                acc += (tj2 - ti) * wts[k] / tot
PHR = anim.PHR
NF = int(DUR * FPS)

T_CHG = PHR[2][0]      # bobina del cargador
T_CNT = PHR[3][0]      # contador
T_PH = PHR[5][0]       # bobina del celular
T_EL = PHR[6][0]       # electrones
T_FAR = PHR[7][0]      # Faraday
T_BAT = PHR[8][0]      # batería
T_HEAT = PHR[9][0]     # calor
T_END = PHR[9][1]      # fin de la narración
T_OUT = T_END + 0.3    # cierre

# ---------- cámara ----------
KEYS = [  # (t, D, phi, yaw, cy)
    (0.0, 1350, 24, -30, 1110),
    (T_CHG, 1250, 28, -16, 1110),
    (T_CNT + 0.4, 1000, 40, 0, 1130),
    (T_PH, 1050, 34, 14, 1110),
    (T_EL + 0.5, 900, 30, 24, 1010),
    (T_BAT, 1000, 28, 10, 1070),
    (T_END, 1300, 26, -10, 1110),
    (DUR, 1450, 24, -22, 1110),
]


def cam_at(t):
    for i in range(len(KEYS) - 1):
        a, b = KEYS[i], KEYS[i + 1]
        if a[0] <= t <= b[0]:
            e = ease((t - a[0]) / max(1e-6, b[0] - a[0]))
            D, phi, yaw, cy = [lerp(a[j], b[j], e) for j in (1, 2, 3, 4)]
            break
    else:
        D, phi, yaw, cy = KEYS[-1][1:]
    pr, yr = math.radians(phi), math.radians(yaw)
    return dict(D=D, cy=cy, cp=math.cos(pr), sp=math.sin(pr), ca=math.cos(yr), sa=math.sin(yr))


def proj(x, y, z, c):
    x1 = x * c['ca'] + z * c['sa']
    z1 = -x * c['sa'] + z * c['ca']
    y2 = y * c['cp'] + z1 * c['sp']
    z2 = z1 * c['cp'] - y * c['sp']
    dep = z2 + c['D']
    k = FOC / dep
    return (540 + x1 * k, c['cy'] - y2 * k, dep)


def P2(x, y, z, c):
    sx, sy, dep = proj(x, y, z, c)
    return (sx * S, sy * S)


# ---------- geometría ----------
RC = 270.0        # radio del cargador
CT = 40.0         # espesor del cargador
PA, PB, PRC = 150.0, 300.0, 48.0   # semiancho, semilargo y radio de esquina del celular
PT = 30.0         # espesor del celular


def spiral(r0, r1, turns, n, ox=0.0, oz=0.0):
    out = []
    for i in range(n + 1):
        u = i / n
        th = 2 * math.pi * turns * u
        r = r0 + (r1 - r0) * u
        out.append((r * math.cos(th) + ox, r * math.sin(th) + oz))
    return out


CHG_COIL = spiral(70, 215, 5.0, 150)
PH_COIL = spiral(55, 125, 4.0, 130, 0, 70)


def rrect(a, b, rc, nc=7):
    pts = []
    for (cx, cz, a0) in ((a - rc, b - rc, 0), (-(a - rc), b - rc, 90), (-(a - rc), -(b - rc), 180), (a - rc, -(b - rc), 270)):
        for i in range(nc + 1):
            an = math.radians(a0 + 90 * i / nc)
            pts.append((cx + rc * math.cos(an), cz + rc * math.sin(an)))
    return pts


PERIM = rrect(PA, PB, PRC)
CIRC = [(RC * math.cos(2 * math.pi * i / 56), RC * math.sin(2 * math.pi * i / 56)) for i in range(57)]

# arcos de campo en 3D
ARCS = []
for k in range(4):
    dk = 150 + k * 45
    hk = 210 + k * 85
    for ai in range(6):
        al = math.radians(ai * 60)
        pts = []
        for i in range(41):
            phi = math.pi * i / 40
            r = (dk / 2) * (1 - math.cos(phi))
            pts.append((r * math.cos(al), hk * math.sin(phi), r * math.sin(al)))
        ARCS.append((k, ai, pts))
        pts2 = [(-x, y, -z) for (x, y, z) in pts]
        ARCS.append((k, ai + 6, pts2))

BOLT = [(12, -95), (-38, 8), (-6, 8), (-18, 95), (38, -22), (6, -22)]


def rot_local(x, z, th):
    return (x * math.cos(th) - z * math.sin(th), x * math.sin(th) + z * math.cos(th))


def render(t):
    c = cam_at(t)
    heat = seg(t, T_HEAT, T_HEAT + 1.5)
    chg = seg(t, T_CHG - 0.2, T_CHG + 0.8)
    phg = seg(t, T_PH - 0.2, T_PH + 0.8)
    h = 110 + (1 - ease(seg(t, 0.2, 2.8))) * 380 + (4 * math.sin(t * 2.0) if t > 3 else 0)
    th_p = math.radians((1 - ease(seg(t, 0.2, 3.0))) * 55)
    lw = max(2, int(4 * S))

    base = BG_IMG.copy()
    bd = ImageDraw.Draw(base)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    LB = Image.new("RGB", (W, H), (0, 0, 0))
    lb = ImageDraw.Draw(LB)
    L2 = Image.new("RGB", (W, H), (0, 0, 0))
    l2 = ImageDraw.Draw(L2)

    # estrellas
    for (x, y, ph, r) in STARS:
        a = 0.25 + 0.25 * math.sin(t * 1.4 + ph)
        px, py = P(x, y)
        rr = r * S * 0.7
        la.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3((200, 190, 255), a))

    # ---- cargador ----
    quads = []
    for i in range(56):
        x0, z0 = CIRC[i]
        x1, z1 = CIRC[i + 1]
        pts = [P2(x0, 0, z0, c), P2(x1, 0, z1, c), P2(x1, -CT, z1, c), P2(x0, -CT, z0, c)]
        dep = proj((x0 + x1) / 2, 0, (z0 + z1) / 2, c)[2]
        nx, nz = (x0 + x1) / 2 / RC, (z0 + z1) / 2 / RC
        shade = 0.45 + 0.55 * max(0.0, -0.5 * nx + 0.86 * nz * -1)
        quads.append((dep, pts, shade))
    quads.sort(key=lambda q: -q[0])
    for dep, pts, shade in quads:
        col = (int(16 + 20 * shade), int(18 + 20 * shade), int(34 + 30 * shade))
        bd.polygon(pts, fill=col)
    top = [P2(x, 0, z, c) for (x, z) in CIRC]
    bd.polygon(top, fill=(27, 29, 50), outline=(88, 76, 150))
    la.line(top, fill=sc3(VIOLET, 0.55 + 0.25 * chg), width=lw)
    inner = [P2(x * 0.93, 0, z * 0.93, c) for (x, z) in CIRC]
    la.line(inner, fill=sc3(VIOLET, 0.18), width=max(1, int(2 * S)))

    # bobina del cargador (cobre) + brillo
    cp = [P2(x, 0.5, z, c) for (x, z) in CHG_COIL]
    bd.line(cp, fill=COPPER, width=max(3, int(7 * S)), joint="curve")
    ring = lc(VIOLET, ORANGE, 0.75 * heat)
    pc = 0.6 + 0.4 * math.sin(2 * math.pi * 3.0 * t)
    la.line(cp, fill=sc3(ring, chg * pc), width=max(3, int(8 * S)), joint="curve")
    if chg > 0:
        for i in range(8):
            u = ((t * 0.35 + i / 8.0) % 1.0)
            x, z = CHG_COIL[int(u * 150)]
            px, py = P2(x, 3, z, c)
            rr = 7 * S
            la.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3((235, 225, 255), chg))

    # ---- campo magnético ----
    arcs_on = 0.5 * ease(seg(t, 2.8, 4.5)) + 0.5 * ease(seg(t, T_CHG, T_CHG + 1.2))
    for (k, ai, pts) in ARCS:
        col = lc(lc(VIOLET, BLUE, k / 3.0), ORANGE, 0.5 * heat)
        poly = [P2(x, y, z, c) for (x, y, z) in pts]
        for i in range(40):
            if pts[i][1] < 1.0 and pts[i + 1][1] < 1.0 and i not in (0, 39):
                continue
            u = (i + 0.5) / 40
            pulse = (0.5 + 0.5 * math.sin(2 * math.pi * (1.6 * t - u * 1.0 - k * 0.15))) ** 2
            a = arcs_on * (0.14 + 0.86 * pulse)
            la.line([poly[i], poly[i + 1]], fill=sc3(col, a), width=lw)
        if ai % 2 == 0:
            u = (t * 0.28 + k * 0.17 + ai * 0.13) % 1.0
            x, y, z = pts[int(u * 40)]
            px, py = P2(x, y, z, c)
            rr = 5 * S
            la.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, arcs_on))
    # anillos que suben
    for j in range(3):
        u = (t * 0.55 + j / 3.0) % 1.0
        y = u * 380
        rad = 200 + 40 * u
        a = arcs_on * math.sin(math.pi * u) * 0.9
        ringp = [P2(rad * math.cos(2 * math.pi * i / 48), y, rad * math.sin(2 * math.pi * i / 48), c) for i in range(49)]
        la.line(ringp, fill=sc3(lc(BLUE, ORANGE, 0.5 * heat), a), width=max(2, int(3 * S)))

    # ---- componer escena A ----
    arrA = np.asarray(base, dtype=np.float32) + np.asarray(LA, dtype=np.float32) + 1.5 * glow_of(LA, 4)
    imgA = Image.fromarray(np.clip(arrA, 0, 255).astype(np.uint8)).convert("RGBA")

    # ---- celular (translúcido) ----
    def world(x, z, y):
        xr, zr = rot_local(x, z, th_p)
        return (xr, y, zr)

    PH_ALPHA = int(lerp(175, 110, phg))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    sq = []
    n = len(PERIM)
    for i in range(n):
        x0, z0 = PERIM[i]
        x1, z1 = PERIM[(i + 1) % n]
        p0b, p1b = world(x0, z0, h), world(x1, z1, h)
        p0t, p1t = world(x0, z0, h + PT), world(x1, z1, h + PT)
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz) or 1
        nxx, nzz = rot_local(dz / ln, -dx / ln, th_p)
        shade = 0.4 + 0.6 * max(0.0, -0.5 * nxx - 0.86 * nzz)
        dep = proj(*world((x0 + x1) / 2, (z0 + z1) / 2, h + PT / 2), c)[2]
        sq.append((dep, [P2(*p0t, c), P2(*p1t, c), P2(*p1b, c), P2(*p0b, c)], shade))
    sq.sort(key=lambda q: -q[0])
    for dep, pts, shade in sq:
        col = (int(22 + 30 * shade), int(24 + 28 * shade), int(44 + 40 * shade), min(255, PH_ALPHA + 40))
        od.polygon(pts, fill=col)
    topf = [P2(*world(x, z, h + PT), c) for (x, z) in PERIM]
    od.polygon(topf, fill=(30, 32, 60, PH_ALPHA))
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")

    # ---- brillos del celular (capa B) ----
    lb.line(topf + [topf[0]], fill=sc3(VIOLET, 0.75), width=lw)
    botf = [P2(*world(x, z, h), c) for (x, z) in PERIM]
    lb.line(botf + [botf[0]], fill=sc3(VIOLET, 0.30), width=max(1, int(2 * S)))
    screen = rrect(PA - 16, PB - 20, PRC - 14, 5)
    scr = [P2(*world(x, z, h + PT + 0.5), c) for (x, z) in screen]
    lb.line(scr + [scr[0]], fill=sc3(BLUE, 0.35 + 0.25 * seg(t, T_BAT, T_BAT + 1)), width=max(1, int(2 * S)))
    # cámara del celular
    cxp, cyp = P2(*world(0, PB - 40, h + PT + 0.5), c)
    rr = 6 * S
    lb.ellipse((cxp - rr, cyp - rr, cxp + rr, cyp + rr), outline=sc3(VIOLET, 0.6), width=max(1, int(2 * S)))

    # bobina del celular
    pcoil = [P2(*world(x, z, h + 6), c) for (x, z) in PH_COIL]
    lb.line(pcoil, fill=sc3(COPPER, 0.85), width=max(3, int(6 * S)), joint="curve")
    pp = 0.6 + 0.4 * math.sin(2 * math.pi * 3.0 * t + 1.1)
    lb.line(pcoil, fill=sc3(ring, phg * pp), width=max(3, int(8 * S)), joint="curve")
    el = seg(t, T_EL, T_EL + 0.8)
    if el > 0:
        for i in range(14):
            u = ((i / 14.0) + t * 0.30) % 1.0
            x, z = PH_COIL[int(u * 130)]
            px, py = P2(*world(x, z, h + 9), c)
            rr = 6 * S
            lb.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, el))

    # rayo en la pantalla (carga)
    bol = seg(t, T_BAT, T_BAT + 0.8) * (1 - seg(t, T_OUT - 0.6, T_OUT))
    if bol > 0:
        pulse = 0.7 + 0.3 * math.sin(2 * math.pi * 1.2 * t)
        bp = [P2(*world(u, v - 90, h + PT + 0.6), c) for (u, v) in BOLT]
        lb.polygon(bp, fill=sc3(BLUE, 0.65 * bol * pulse))

    # ondas de calor
    hon = seg(t, T_HEAT + 0.1, T_HEAT + 1.1) * (1 - seg(t, T_END - 0.3, T_END + 0.3))
    if hon > 0:
        for (hx, hz) in ((-90, -140), (0, -60), (90, 20), (-60, 110), (60, 190), (-100, 40), (110, -90)):
            prev = None
            for j in range(26):
                u = j / 25.0
                y = h + PT + 4 + u * 170
                x = hx + 14 * math.sin(7 * u - t * 5 + hx * 0.05)
                xr, zr = rot_local(x, hz, th_p)
                p = P2(xr, y, zr, c)
                if prev is not None:
                    lb.line([prev, p], fill=sc3(ORANGE, hon * (1 - u) * 0.9), width=lw)
                prev = p

    arr = np.asarray(imgB, dtype=np.float32) + np.asarray(LB, dtype=np.float32) + 1.5 * glow_of(LB, 4)
    arr = arr * (1 - 0.92 * seg(t, T_OUT, T_OUT + 0.8))

    # ---------- overlays ----------
    anim.draw_caption(l2, t)

    def label(txt, target, text_pos, anchor, a):
        if a <= 0:
            return
        f = F(B, 30)
        tw = f.getlength(txt) / S
        tx, ty = text_pos
        l2.text(P(tx, ty), txt, font=f, fill=sc3((185, 185, 225), a), anchor=anchor)
        ex = (tx - tw - 14) if anchor == "rm" else (tx + tw + 14)
        l2.line([P(*target), P(ex, ty)], fill=sc3((140, 140, 200), a), width=max(1, int(2 * S)))
        rr = 6 * S
        px, py = P(*target)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), outline=sc3((200, 200, 240), a), width=max(1, int(2 * S)))

    a1 = seg(t, T_CHG, T_CHG + 0.6) * (1 - seg(t, T_PH - 0.2, T_PH + 0.4))
    if a1 > 0:
        tgt = proj(-215, 0, 0, c)[:2]
        label("BOBINA DEL CARGADOR", tgt, (60, min(1560, tgt[1] + 230)), "lm", a1)
    a2 = seg(t, T_PH, T_PH + 0.6) * (1 - seg(t, T_BAT - 0.4, T_BAT + 0.2))
    if a2 > 0:
        x, z = PH_COIL[70]
        xr, zr = rot_local(x, z, th_p)
        tgt = proj(xr, h + 6, zr, c)[:2]
        label("BOBINA DEL CELULAR", tgt, (1040, max(430, tgt[1] - 260)), "rm", a2)

    ca = seg(t, T_CNT, T_CNT + 0.6) * (1 - seg(t, T_PH, T_PH + 0.6))
    if ca > 0:
        val = int(100000 * ease(seg(t, T_CNT + 0.1, T_CNT + 3.1)))
        txt = f"{val:,}" + ("+" if val >= 100000 else "")
        l2.text(P(540, 470), txt, font=F(M, 100), fill=sc3((235, 225, 255), ca), anchor="mm")
        l2.text(P(540, 548), "VECES POR SEGUNDO", font=F(B, 32), fill=sc3((170, 160, 230), ca), anchor="mm")
        l2.rectangle((*P(170, 405), *P(910, 590)), outline=sc3((100, 90, 190), ca * 0.8), width=max(1, int(2 * S)))

    fa = seg(t, T_FAR, T_FAR + 0.6) * (1 - seg(t, T_BAT - 0.4, T_BAT + 0.2))
    if fa > 0:
        l2.rounded_rectangle((*P(300, 1600), *P(780, 1680)), radius=int(40 * S), outline=sc3(BLUE, fa), width=max(2, int(3 * S)))
        l2.text(P(540, 1640), "FARADAY · 1831", font=F(B, 38), fill=sc3((220, 235, 255), fa), anchor="mm")

    bon = seg(t, T_BAT, T_BAT + 0.8) * (1 - seg(t, T_END - 0.3, T_END + 0.3))
    if bon > 0:
        level = 0.78 * ease(seg(t, T_BAT + 0.1, T_END - 0.3))
        l2.rounded_rectangle((*P(430, 440), *P(650, 550)), radius=int(18 * S), outline=sc3(BLUE, bon), width=max(2, int(6 * S)))
        l2.rectangle((*P(650, 475), *P(668, 515)), fill=sc3(BLUE, bon))
        if level > 0.01:
            l2.rounded_rectangle((*P(442, 452), *P(442 + 196 * level / 0.78, 538)), radius=int(10 * S), fill=sc3(BLUE, 0.5 * bon))
        l2.text(P(540, 495), f"{int(level * 100)}%", font=F(B, 52), fill=sc3((255, 255, 255), bon), anchor="mm")
    if hon > 0:
        l2.text(P(540, 1560), "PARTE SE PIERDE COMO CALOR", font=F(B, 32), fill=sc3((255, 190, 130), hon), anchor="mm")

    ta = seg(t, T_OUT + 0.1, T_OUT + 1.0)
    if ta > 0:
        l2.text(P(540, 900), "Mente en órbita", font=F(B, 112), fill=sc3((240, 235, 255), ta), anchor="mm")
        ang = 2 * math.pi * (t - T_OUT) / 3.0
        ox, oy = 540 + 440 * math.cos(ang), 900 + 130 * math.sin(ang)
        l2.ellipse((*P(540 - 440, 900 - 130), *P(540 + 440, 900 + 130)), outline=sc3(VIOLET, 0.45 * ta), width=max(1, int(2 * S)))
        rr = 9 * S
        px, py = P(ox, oy)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, ta))
    sa = seg(t, T_OUT + 0.6, T_OUT + 1.4)
    if sa > 0 and len(PHR) <= 10:
        l2.text(P(540, 1040), "¿Qué quieres que explique después?", font=F(R, 42), fill=sc3((190, 190, 230), sa), anchor="mm")

    arr = arr + np.asarray(L2, dtype=np.float32) + 1.2 * glow_of(L2, 3)
    arr = arr * (seg(t, 0.0, 0.4) * (1 - seg(t, DUR - 0.5, DUR)))
    return np.clip(arr, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        os.makedirs("/home/claude/prev3", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render(float(ts))).save(f"/home/claude/prev3/t_{ts}.png")
        print("ok")
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(a, b):
            pr.stdin.write(render(f / FPS).tobytes())
        pr.stdin.close()
        pr.wait()
        print("ok", a, b, "de", NF)
