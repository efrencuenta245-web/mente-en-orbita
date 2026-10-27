"""Suelo continuo de la ciudad (vista nocturna) por pixel: manzanas de 110 m como el centro detallado,
calles iluminadas (capa emisiva), lago, parques, aeropuerto, montañas oscuras, mip-maps, cielo y bruma."""
import math
import numpy as np
from PIL import Image, ImageDraw
from anim import W, H, S
from gps_earth import ray_dirs

GT = 4096
GEXT = 16384.0
TEX0 = 2 * GEXT / GT
PITCH = 110.0
INNER = 672.0


def _tx(v):
    return (v + GEXT) / (2 * GEXT) * GT


def urban_radius(theta):
    return 11800 + 1900 * np.sin(3 * theta + 1.0) + 1100 * np.sin(7 * theta + 0.3) + 600 * np.sin(13 * theta)


def _hash(a, b, c=0):
    h = (a * 73856093) ^ (b * 19349663) ^ (c * 83492791)
    return ((h & 0xFFFF) / 65535.0)


def build():
    yy, xx = np.mgrid[0:GT, 0:GT]
    X = (xx.astype(np.float32) + 0.5) / GT * 2 * GEXT - GEXT
    Z = (yy.astype(np.float32) + 0.5) / GT * 2 * GEXT - GEXT
    r = np.hypot(X, Z)
    th = np.arctan2(Z, X)
    urb_r = urban_radius(th)
    edge = np.clip((urb_r + 500 - r) / 1000, 0, 1)
    # cuadrícula de 110 m alineada con el centro (calles centradas en múltiplos de 110)
    mx = np.mod(X + 0.0, PITCH)
    mz = np.mod(Z + 0.0, PITCH)
    ix = np.floor(X / PITCH).astype(np.int64)
    iz = np.floor(Z / PITCH).astype(np.int64)
    st_x = (mx < 10) | (mx > 100)
    st_z = (mz < 10) | (mz > 100)
    street = st_x | st_z
    main = ((np.mod(np.round(X / PITCH), 5) == 0) & st_x) | ((np.mod(np.round(Z / PITCH), 5) == 0) & st_z)
    lotx = (mx > 55).astype(np.int64)
    lotz = (mz > 55).astype(np.int64)
    hsh = ((ix * 73856093) ^ (iz * 19349663) ^ ((lotx * 2 + lotz) * 83492791)) & 0xFFFF
    hv = hsh.astype(np.float32) / 65535.0
    roof = 30 + 30 * hv
    gap = (np.abs(mx - 55) < 2.5) | (np.abs(mz - 55) < 2.5)
    dens = np.exp(-r / 9000.0)
    arr = np.empty((GT, GT, 3), np.float32)
    arr[..., 0] = roof * 1.00
    arr[..., 1] = roof * 1.00
    arr[..., 2] = roof * 1.12
    arr[gap] = (22, 22, 28)
    arr[street] = (40, 35, 34)
    arr[main] = (62, 52, 42)
    terrain = np.stack([16 + 5 * np.sin(X * 0.0009) * np.sin(Z * 0.0011), 18 + 5 * np.sin(X * 0.0009) * np.sin(Z * 0.0011),
                        20 + 4 * np.sin(X * 0.0009) * np.sin(Z * 0.0011)], -1)
    arr = arr * edge[..., None] + terrain * (1 - edge[..., None])
    emis = np.zeros((GT, GT), np.float32)
    emis[street] = 0.17
    emis[main] = 0.55
    # anillo periférico y diagonales
    img_e = Image.new("L", (GT, GT), 0)
    de = ImageDraw.Draw(img_e)
    ring = []
    for i in range(361):
        a = 2 * math.pi * i / 360
        rr = 7200 + 650 * math.sin(3 * a + 0.5) + 300 * math.sin(5 * a)
        ring.append((_tx(rr * math.cos(a)), _tx(rr * math.sin(a))))
    de.line(ring, fill=255, width=4)
    for (a, b) in (((-14000, -9000), (9000, 14000)), ((-12000, 11000), (13000, -10000))):
        de.line([(_tx(a[0]), _tx(a[1])), (_tx(b[0]), _tx(b[1]))], fill=230, width=3)
    hw = np.asarray(img_e, np.float32) / 255.0
    emis = np.maximum(emis, hw * 0.8)
    arr = arr * (1 - hw[..., None]) + np.array([86, 70, 54], np.float32) * hw[..., None]
    emis = emis * edge * (0.45 + 0.55 * dens)

    def ell(cx, cz, rx, rz):
        return (((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2) < 1

    lake = ell(-6500, 4200, 1700, 950)
    arr[lake] = (10, 16, 30)
    emis[lake] = 0
    for (cx, cz, rx, rz) in ((2600, 3100, 700, 480), (-2400, -1800, 520, 800), (4200, -5200, 900, 600), (-8200, -3600, 800, 500), (900, -2100, 380, 300)):
        m = ell(cx, cz, rx, rz)
        arr[m] = (18, 34, 24)
        emis[m] *= 0.1
    ap = (np.abs(X - 5200) < 1500) & (np.abs(Z + 2600) < 700)
    arr[ap] = (34, 34, 40)
    emis[ap] = 0.02
    for dz in (-260, 260):
        rw = (np.abs(X - 5200) < 1350) & (np.abs(Z + 2600 - dz) < 30)
        arr[rw] = (84, 86, 94)
        emis[rw] = 0.25
    inner = (np.abs(X) < INNER) & (np.abs(Z) < INNER)
    emis[inner] = 0
    tex = np.clip(arr, 0, 255).astype(np.uint8)
    levels = [tex]
    elev = [np.clip(emis * 255, 0, 255).astype(np.uint8)]
    im = Image.fromarray(tex)
    ie = Image.fromarray(elev[0])
    sz = GT
    while sz > 32:
        sz //= 2
        im = im.resize((sz, sz), Image.BOX)
        ie = ie.resize((sz, sz), Image.BOX)
        levels.append(np.asarray(im))
        elev.append(np.asarray(ie))
    urban = (edge > 0.5)
    return levels, elev, urban


LEVELS, ELEV, URBAN = build()
EM_COL = np.array([255, 168, 78], np.float32) / 255.0


def is_urban(x, z):
    i = int(np.clip(_tx(z), 0, GT - 1))
    j = int(np.clip(_tx(x), 0, GT - 1))
    return bool(URBAN[i, j])


SKY_LO = np.array([62, 36, 80], np.float32)
SKY_HI = np.array([8, 8, 24], np.float32)
HAZE = np.array([46, 34, 60], np.float32)


def render_ground(c, haze_k=1.0, sky=True, em_k=1.0):
    """devuelve (color_base, emisivo) como arrays (H,W,3)"""
    dx, dy, dz = ray_dirs(c, 0, 0, W, H)
    ox, oy, oz = c['pos']
    out = np.empty((H, W, 3), np.float32)
    emo = np.zeros((H, W, 3), np.float32)
    down = dy < -1e-4
    t = np.where(down, -oy / np.where(down, dy, -1.0), 1e9)
    hit = down & (t < 2.0e5)
    if sky:
        e = np.clip(dy / 0.35, 0, 1)[..., None]
        out[...] = SKY_LO * (1 - e) + SKY_HI * e
    else:
        out[...] = SKY_HI
    if hit.any():
        tt = t[hit]
        X = ox + tt * dx[hit]
        Z = oz + tt * dz[hit]
        foot = tt * 0.00125 / np.maximum(np.abs(dy[hit]), 0.04)
        lev = np.clip(np.floor(np.log2(np.maximum(foot / TEX0, 1e-6)) + 0.5), 0, len(LEVELS) - 1).astype(np.int32)
        col = np.empty((tt.shape[0], 3), np.float32)
        em = np.empty(tt.shape[0], np.float32)
        for L in np.unique(lev):
            m = lev == L
            T = LEVELS[L]
            n = T.shape[0]
            u = np.clip(((X[m] + GEXT) / (2 * GEXT) * n).astype(np.int32), 0, n - 1)
            v = np.clip(((Z[m] + GEXT) / (2 * GEXT) * n).astype(np.int32), 0, n - 1)
            col[m] = T[v, u]
            em[m] = ELEV[L][v, u]
        outside = (np.abs(X) > GEXT) | (np.abs(Z) > GEXT)
        col[outside] = (14, 15, 18)
        em[outside] = 0
        h = np.clip((tt - 1.4 * max(oy, 1.0) - 5000) / 60000, 0, 0.85)[:, None] * haze_k
        col = col * (1 - h) + HAZE * h
        out[hit] = col
        emo[hit] = (em * (1 - h[:, 0] * 0.6) * em_k)[:, None] * EM_COL
    return out, emo
