"""Utilidades 3D para el video del GPS: caras con recorte, cajas/cilindros rotados, proyección vectorizada y luces puntuales."""
import math
import numpy as np
from PIL import Image, ImageDraw
from anim import W, H, S, ease, lerp, sc3, clamp, seg
from nc import proj, P2, vis
from fo import clip_near

FOC = 1200.0


def norm(v):
    v = np.asarray(v, np.float64)
    return v / np.linalg.norm(v)


def shade_l(col, n, L, dim=1.0, amb=0.40, dif=0.85):
    d = max(0.0, n[0] * L[0] + n[1] * L[1] + n[2] * L[2])
    k = (amb + dif * d) * dim
    return (min(255, int(col[0] * k)), min(255, int(col[1] * k)), min(255, int(col[2] * k)))


def cam_from(D, phi, yaw, cy, f):
    pr, yr = math.radians(phi), math.radians(yaw)
    c = dict(D=D, cy=cy, cp=math.cos(pr), sp=math.sin(pr), ca=math.cos(yr), sa=math.sin(yr), f=tuple(f))
    c['pos'] = (f[0] + D * c['cp'] * c['sa'], f[1] + D * c['sp'], f[2] - D * c['cp'] * c['ca'])
    return c


def cam_keys(t, keys, logD=False):
    """keys: (t, D, phi, yaw, cy, fx, fy, fz)"""
    v = None
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a[0] <= t <= b[0]:
            e = ease((t - a[0]) / max(1e-6, b[0] - a[0]))
            v = [lerp(a[j], b[j], e) for j in range(1, 8)]
            if logD:
                v[0] = math.exp(lerp(math.log(a[1]), math.log(b[1]), e))
            break
    if v is None:
        v = list(keys[0][1:]) if t < keys[0][0] else list(keys[-1][1:])
    D, phi, yaw, cy, fx, fy, fz = v
    return cam_from(D, phi, yaw, cy, (fx, fy, fz))


def face(c, pts3, n, col, dim=1.0, L=None, amb=0.40, near=40.0, flat=False):
    k = len(pts3)
    ctr = tuple(sum(p[i] for p in pts3) / k for i in range(3))
    if n is not None and not vis(c, ctr, n):
        return None
    q = clip_near(pts3, c, near)
    if len(q) < 3:
        return None
    dep = proj(*ctr, c)[2]
    if flat or n is None:
        cc = tuple(max(0, min(255, int(v * dim))) for v in col)
    else:
        cc = shade_l(col, n, L if L is not None else LIGHT_DEF, dim, amb)
    return (dep, [P2(*p, c) for p in q], cc)


LIGHT_DEF = norm((-0.55, 0.75, -0.35))


def cbox(c, x0, x1, y0, y1, z0, z1, col, dim=1.0, L=None, amb=0.40, bottom=False, near=40.0):
    faces = [((0, 1, 0), [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]),
             ((0, 0, -1), [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]),
             ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
             ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
             ((1, 0, 0), [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)])]
    if bottom:
        faces.append(((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]))
    out = []
    for n, pts in faces:
        f = face(c, pts, n, col, dim, L, amb, near)
        if f:
            out.append(f)
    return out


def rot_x(a):
    ca, sa = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])


def rot_y(a):
    ca, sa = math.cos(a), math.sin(a)
    return np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])


def rot_z(a):
    ca, sa = math.cos(a), math.sin(a)
    return np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])


def xf(Rm, ctr, p):
    q = Rm @ np.asarray(p, np.float64)
    return (ctr[0] + q[0], ctr[1] + q[1], ctr[2] + q[2])


def obox(c, ctr, Rm, lo, hi, col, dim=1.0, L=None, amb=0.40, alpha=None, near=40.0):
    """caja orientada: lo/hi esquinas en coordenadas locales"""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    faces = [((0, 1, 0), [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]),
             ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),
             ((0, 0, -1), [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]),
             ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
             ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
             ((1, 0, 0), [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)])]
    out = []
    for n, pts in faces:
        nw = tuple(Rm @ np.asarray(n, np.float64))
        pw = [xf(Rm, ctr, p) for p in pts]
        f = face(c, pw, nw, col, dim, L, amb, near)
        if f:
            out.append(f if alpha is None else (f[0], f[1], (*f[2], alpha)))
    return out


def ocyl(c, ctr, Rm, base, axis, r, h, col, n=16, dim=1.0, L=None, caps=True, alpha=None, near=40.0):
    """cilindro orientado; base = centro local de la base, axis = 0/1/2 (eje local)"""
    a = axis
    u, v = (a + 1) % 3, (a + 2) % 3
    out = []

    def pt(s, th):
        p = list(base)
        p[a] += s * h
        p[u] += r * math.cos(th)
        p[v] += r * math.sin(th)
        return xf(Rm, ctr, p)

    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        tm = (t0 + t1) / 2
        nl = [0.0, 0.0, 0.0]
        nl[u], nl[v] = math.cos(tm), math.sin(tm)
        nw = tuple(Rm @ np.array(nl))
        f = face(c, [pt(0, t0), pt(0, t1), pt(1, t1), pt(1, t0)], nw, col, dim, L, 0.40, near)
        if f:
            out.append(f if alpha is None else (f[0], f[1], (*f[2], alpha)))
    if caps:
        for s in (0, 1):
            nl = [0.0, 0.0, 0.0]
            nl[a] = 1.0 if s else -1.0
            nw = tuple(Rm @ np.array(nl))
            f = face(c, [pt(s, 2 * math.pi * i / n) for i in range(n)], nw, col, dim, L, 0.40, near)
            if f:
                f = (f[0] - 0.5, f[1], f[2])
                out.append(f if alpha is None else (f[0], f[1], (*f[2], alpha)))
    return out


def draw_sorted(d, polys):
    polys.sort(key=lambda q: -q[0])
    for dep, pts, col in polys:
        d.polygon(pts, fill=col)


def proj_np(X, Y, Z, c):
    x = X - c['f'][0]
    y = Y - c['f'][1]
    z = Z - c['f'][2]
    x1 = x * c['ca'] + z * c['sa']
    z1 = -x * c['sa'] + z * c['ca']
    y2 = y * c['cp'] + z1 * c['sp']
    z2 = z1 * c['cp'] - y * c['sp']
    dep = z2 + c['D']
    k = FOC / np.maximum(dep, 1e-6)
    return (540 + x1 * k) * S, (c['cy'] - y2 * k) * S, dep


def splat(buf, c, X, Y, Z, col, inten=1.0, near=40.0, size=1, fade_far=None):
    """luces puntuales sumadas en buf (H,W,3 float32)"""
    sx, sy, dep = proj_np(X, Y, Z, c)
    ok = (dep > near) & (sx >= 1) & (sx < W - 2) & (sy >= 1) & (sy < H - 2)
    if not ok.any():
        return
    xs, ys = sx[ok].astype(np.int32), sy[ok].astype(np.int32)
    w = np.full(xs.shape, inten, np.float32) if np.isscalar(inten) else np.asarray(inten, np.float32)[ok]
    if fade_far is not None:
        w = w * np.clip(fade_far / dep[ok], 0.15, 1.0).astype(np.float32)
    colv = np.asarray(col, np.float32)
    for dx_ in range(size):
        for dy_ in range(size):
            for ch in range(3):
                np.add.at(buf[..., ch], (ys + dy_, xs + dx_), w * colv[ch])


def seg_clip_uv(p0, p1, lo=-1.0, hi=1.0):
    """recorta segmento 2D al cuadrado [lo,hi]^2 (Liang-Barsky)"""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - lo), (dx, hi - x0), (-dy, y0 - lo), (dy, hi - y0)):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return None
    return (x0 + t0 * dx, y0 + t0 * dy), (x0 + t1 * dx, y0 + t1 * dy)


def ring_pts(ctr, n_axis, r, k=48):
    n_axis = norm(n_axis)
    a = np.array([0.0, 1.0, 0.0]) if abs(n_axis[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = norm(np.cross(n_axis, a))
    e2 = np.cross(n_axis, e1)
    return [tuple(np.asarray(ctr) + r * (math.cos(2 * math.pi * i / k) * e1 + math.sin(2 * math.pi * i / k) * e2)) for i in range(k + 1)]


def polyline3(d, c, pts, col, w=1, near=40.0):
    """polilínea 3D con recorte en el plano cercano"""
    prev = None
    run = []
    for p in pts:
        dep = proj(*p, c)[2]
        if dep > near:
            run.append(P2(*p, c))
        else:
            if len(run) > 1:
                d.line(run, fill=col, width=w)
            run = []
    if len(run) > 1:
        d.line(run, fill=col, width=w)


def glow_dot(la, x, y, r, col, a):
    if a <= 0.01:
        return
    la.ellipse((x - r, y - r, x + r, y + r), fill=sc3(col, a))
