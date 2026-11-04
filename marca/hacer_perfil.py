"""Foto de perfil de Mente en órbita (estilo nuevo): esfera de alambre blanca que brilla, órbita inclinada
y un punto cian (el «satélite») sobre negro. Sin texto: a 110 px el texto no se lee. Uso: python3 marca/hacer_perfil.py"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

S = 2160                     # se dibuja al doble y se reduce a 1080
C = S / 2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'perfil_mente_en_orbita.png')
CYAN = (120, 225, 255)


def rot(P, ax, ay):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ca, sa = math.cos(ax), math.sin(ax)
    y, z = y * ca - z * sa, y * sa + z * ca
    cb, sb = math.cos(ay), math.sin(ay)
    x, z = x * cb + z * sb, -x * sb + z * cb
    return np.stack([x, y, z], 1)


def proj(P, R=560):
    return [(C + R * p[0], C - R * p[1]) for p in P]


base = Image.new('RGB', (S, S), (0, 0, 0))
fx = Image.new('RGB', (S, S), (0, 0, 0))
db, df = ImageDraw.Draw(base), ImageDraw.Draw(fx)
yy, xx = np.mgrid[0:S, 0:S]
r = np.hypot(xx - C, yy - C * 0.96) / (S * 0.5)
spot = (np.clip(1 - r, 0, 1) ** 2 * 26).astype(np.float32)
base = Image.fromarray(np.stack([spot, spot * 0.98, spot * 1.04], 2).clip(0, 255).astype(np.uint8))
db = ImageDraw.Draw(base)

AX, AY = math.radians(18), math.radians(-24)


def sphere_lines(front):
    for lat in range(-60, 90, 30):
        th = np.linspace(0, 2 * math.pi, 160)
        rr = math.cos(math.radians(lat))
        P = np.stack([rr * np.cos(th), np.full_like(th, math.sin(math.radians(lat))), rr * np.sin(th)], 1)
        yield rot(P, AX, AY)
    for lon in range(0, 180, 30):
        th = np.linspace(0, 2 * math.pi, 160)
        a = math.radians(lon)
        P = np.stack([np.cos(th) * math.cos(a), np.sin(th), np.cos(th) * math.sin(a)], 1)
        yield rot(P, AX, AY)


def draw_poly(P, front, w, col, a, glow):
    keep = (P[:, 2] > -0.02) if front else (P[:, 2] <= -0.02)
    seg = []
    for p, k in zip(P, keep):
        if k:
            seg.append(p)
        elif seg:
            if len(seg) > 1:
                pts = proj(np.array(seg))
                db.line(pts, fill=tuple(int(c * a) for c in col), width=w, joint='curve')
                if glow:
                    df.line(pts, fill=tuple(int(c * a * glow) for c in col), width=w * 2, joint='curve')
            seg = []
    if len(seg) > 1:
        pts = proj(np.array(seg))
        db.line(pts, fill=tuple(int(c * a) for c in col), width=w, joint='curve')
        if glow:
            df.line(pts, fill=tuple(int(c * a * glow) for c in col), width=w * 2, joint='curve')


# órbita: elipse inclinada alrededor de la esfera
th = np.linspace(0, 2 * math.pi, 400)
ORB = np.stack([1.55 * np.cos(th), 0.0 * th, 1.62 * np.sin(th)], 1)
ORB = rot(rot(ORB, math.radians(72), 0), 0, math.radians(-28))
ORB = rot(ORB, math.radians(-12), 0)
# 1) parte trasera de la órbita (tenue, detrás de la esfera)
draw_poly(ORB, False, 7, (255, 255, 255), 0.35, 0.0)
# 2) esfera: hemisferio trasero tenue, disco que tapa, hemisferio delantero brillante
for P in sphere_lines(False):
    draw_poly(P, False, 4, (255, 255, 255), 0.18, 0)
db.ellipse((C - 556, C - 556, C + 556, C + 556), fill=(4, 4, 6))
for P in sphere_lines(True):
    draw_poly(P, True, 6, (255, 255, 255), 0.92, 0.55)
db.ellipse((C - 560, C - 560, C + 560, C + 560), outline=(245, 245, 248), width=9)
df.ellipse((C - 560, C - 560, C + 560, C + 560), outline=(150, 150, 150), width=22)
rng = np.random.RandomState(4)
N = rng.normal(size=(26, 3)); N /= np.linalg.norm(N, axis=1, keepdims=True)
for p in rot(N, AX, AY):
    if p[2] > 0.1:
        x, y = proj([p])[0]
        db.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(255, 255, 255))
        df.ellipse((x - 26, y - 26, x + 26, y + 26), fill=(170, 170, 170))
# 3) parte delantera de la órbita (brillante, sobre la esfera)
draw_poly(ORB, True, 10, (255, 255, 255), 1.0, 0.8)
# 4) satélite cian sobre la órbita, al frente
i = int(np.argmax(ORB[:, 2] + 0.6 * ORB[:, 0]))
x, y = proj([ORB[i]])[0]
db.ellipse((x - 34, y - 34, x + 34, y + 34), fill=CYAN)
df.ellipse((x - 90, y - 90, x + 90, y + 90), fill=CYAN)

# acabado: bloom de 2 pasos, viñeta y grano
b = np.asarray(base, np.float32) / 255
e = np.asarray(fx, np.float32) / 255
img = b + e * 0.45
q = np.asarray(Image.fromarray((np.clip(e + np.clip(b - 0.6, 0, None), 0, 1) * 255).astype(np.uint8)).resize((S // 4, S // 4), Image.BILINEAR), np.float32) / 255
bl = gaussian_filter(q, (3, 3, 0)) * 0.7 + gaussian_filter(q, (16, 16, 0)) * 0.9
bl = np.asarray(Image.fromarray((np.clip(bl, 0, 1) * 255).astype(np.uint8)).resize((S, S), Image.BILINEAR), np.float32) / 255
img = img + bl
v = 1 - 0.5 * np.clip(r - 0.55, 0, 1) ** 1.3
img = img * v[..., None]
img = img / (1 + 0.1 * img)
img = img + (np.random.RandomState(9).rand(S, S, 1).astype(np.float32) - 0.5) * 0.035
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((1080, 1080), Image.LANCZOS).save(OUT)
print('listo', OUT)
