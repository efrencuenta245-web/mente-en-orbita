"""Foto 3D: el vehículo REAL de la foto, recortado y con profundidad, para moverlo en 3D sin recrearlo en malla.
(Pedido de Efrén, 9-nov-2026: «que los vehículos no se vean como una recreación en 3D, sino como se ven en las
imágenes pero en 3D».)

1) preparar(foto) → recorte con ISNet (ONNX) + profundidad con Depth Anything V2 (ONNX) + normales.
   Se guarda en /home/claude/f3d/NOMBRE.npz para no repetir (tarda ~20 s por foto en CPU).
2) dibujar(img, a, t, ...) pega el vehículo en el escenario negro con:
   · paralaje por profundidad (la cámara «orbita»: lo cercano se mueve más que lo lejano),
   · reluz con las normales (una luz que recorre la carrocería real), brillo especular y luz de borde,
   · reflejo en el piso y sombra de contacto, entrada con rebote y sacudida.
Modelos: /home/claude/modelos/{da2_vits.onnx, isnet.onnx} (GitHub releases de fabio-sim/Depth-Anything-ONNX y
danielgatis/rembg; se bajan directo con curl -L porque GitHub sí está permitido).
"""
import os, math
import numpy as np
import cv2
from PIL import Image, ImageFilter

MOD = '/home/claude/modelos'
CACHE = '/home/claude/f3d'
_S = {}


def _sess(n):
    if n not in _S:
        import onnxruntime as ort
        o = ort.SessionOptions()
        o.intra_op_num_threads = 2
        _S[n] = ort.InferenceSession(os.path.join(MOD, n), o, providers=['CPUExecutionProvider'])
    return _S[n]


def _mascara(rgb):
    h, w = rgb.shape[:2]
    x = cv2.resize(rgb, (1024, 1024), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    x = (x - 0.5) / 1.0
    s = _sess('isnet.onnx')
    m = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
    m = (m - m.min()) / max(1e-6, m.max() - m.min())
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)


def _prof(rgb):
    h, w = rgb.shape[:2]
    x = cv2.resize(rgb, (518, 518), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    s = _sess('da2_vits.onnx')
    d = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
    return cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)


def preparar(ruta, nombre, recorte=None, umbral=0.5, componentes=1, borrar=None, ancho_max=1600, forzar=False):
    """recorte=(x0,y0,x1,y1) en fracciones para quedarte con una parte de la foto antes de segmentar.
    borrar=[(x0,y0,x1,y1), …] en fracciones del recorte: zonas que no son el vehículo (personas, letreros)."""
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, nombre + '.npz')
    if os.path.exists(out) and not forzar:
        return cargar(nombre)
    im = Image.open(ruta).convert('RGB')
    if recorte:
        W0, H0 = im.size
        im = im.crop((int(recorte[0] * W0), int(recorte[1] * H0), int(recorte[2] * W0), int(recorte[3] * H0)))
    if im.width > ancho_max:
        im = im.resize((ancho_max, int(im.height * ancho_max / im.width)), Image.LANCZOS)
    rgb = np.asarray(im)
    m = _mascara(rgb)
    if borrar:
        h, w = m.shape
        for (a, b, c, d) in borrar:
            m[int(b * h):int(d * h), int(a * w):int(c * w)] = 0
    # quedarse con los componentes más grandes (el vehículo), limpiar y suavizar el borde
    bin_ = (m > umbral).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bin_, 8)
    if n > 1:
        orden = np.argsort(-st[1:, cv2.CC_STAT_AREA])[:componentes] + 1
        keep = np.isin(lab, orden)
        m = m * keep
    m = np.clip((m - 0.15) / 0.7, 0, 1).astype(np.float32)
    d = _prof(rgb).astype(np.float32)
    ys, xs = np.where(m > 0.5)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    pad = int(0.04 * max(y1 - y0, x1 - x0))
    y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
    y1, x1 = min(rgb.shape[0], y1 + pad), min(rgb.shape[1], x1 + pad)
    rgb, m, d = rgb[y0:y1, x0:x1], m[y0:y1, x0:x1], d[y0:y1, x0:x1]
    np.savez_compressed(out, rgb=rgb, m=m, d=d)
    return cargar(nombre)


class Activo:
    pass


def cargar(nombre):
    z = np.load(os.path.join(CACHE, nombre + '.npz'))
    a = Activo()
    a.nombre = nombre
    a.rgb = z['rgb'].astype(np.float32)
    a.m = z['m'].astype(np.float32)
    d = z['d'].astype(np.float32)
    dentro = a.m > 0.5
    lo, hi = np.percentile(d[dentro], 2), np.percentile(d[dentro], 98)
    dn = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1)          # 1 = cerca de la cámara
    # fuera del vehículo: copiar la profundidad del borde (así el borde no se estira al mover la cámara)
    # fuera del vehículo: extender la profundidad del borde con convolución normalizada (sin rayas)
    mm = dentro.astype(np.float32)
    sg = 0.03 * max(dn.shape)
    num = cv2.GaussianBlur(dn * mm, (0, 0), sg)
    den = cv2.GaussianBlur(mm, (0, 0), sg)
    fill = num / np.maximum(den, 1e-4)
    dn = dn * mm + fill * (1 - mm)
    dn = cv2.GaussianBlur(dn, (0, 0), 2.0)
    a.d = dn
    a.dw = cv2.GaussianBlur(dn, (0, 0), 0.012 * max(dn.shape))   # profundidad suave para mover sin romper
    # normales desde la profundidad suavizada (para la reluz)
    ds = cv2.GaussianBlur(dn, (0, 0), 6.0) * (0.35 * max(dn.shape))
    gx = cv2.Sobel(ds, cv2.CV_32F, 1, 0, ksize=5) / 32.0
    gy = cv2.Sobel(ds, cv2.CV_32F, 0, 1, ksize=5) / 32.0
    n = np.dstack([-gx, gy, np.ones_like(gx)])
    a.n = n / np.linalg.norm(n, axis=2, keepdims=True)
    a.h, a.w = a.m.shape
    # luz de borde: anillo interior de la máscara
    er = cv2.erode((a.m > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8), iterations=2)
    a.borde = np.clip(a.m - er.astype(np.float32), 0, 1)
    a.borde = cv2.GaussianBlur(a.borde, (0, 0), 2.5)
    a.lum = float(np.percentile((a.rgb.mean(2))[dentro], 60))
    return a


def _warp(a, yaw, pitch, esc):
    """Mapa inverso: giro de cámara alrededor del vehículo (perspectiva de hasta ~9° con yaw=±1) + paralaje por
    profundidad (lo cercano se mueve más que lo lejano). 3 pasos de punto fijo para usar la profundidad del origen."""
    h, w = a.h, a.w
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cxp, cyp = w / 2, h * 0.55
    th = math.radians(9.0 * yaw)
    f = 2.4 * max(w, h)
    xo = (xx - cxp) / esc
    yo = (yy - cyp) / esc
    X = f * xo / (f * math.cos(th) - xo * math.sin(th))          # plano girado (inversa)
    Y = yo * (f + X * math.sin(th)) / f
    amp_x = yaw * w * 0.045
    amp_y = pitch * h * 0.035
    sx = cxp + X
    sy = cyp + Y
    for _ in range(3):
        d = cv2.remap(a.dw, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        off = d - 0.5
        sx = cxp + X - amp_x * off
        sy = cyp + Y - amp_y * off
    return sx, sy


def render_activo(a, yaw=0.0, pitch=0.0, esc=1.0, luz=(-0.5, -0.6), luz_k=0.55, spec=0.5, brillo=1.0):
    """Devuelve (rgb float 0-255, alfa 0-1, borde) del vehículo ya movido y con luz nueva, tamaño del activo."""
    sx, sy = _warp(a, yaw, pitch, esc)
    rgb = cv2.remap(a.rgb, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al = cv2.remap(a.m, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    n = cv2.remap(a.n, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    bo = cv2.remap(a.borde, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    L = np.array([luz[0], -luz[1], 0.75], np.float32)
    L /= np.linalg.norm(L)
    lam = np.clip((n * L).sum(2), 0, 1)
    sh = 1 + luz_k * (lam - 0.62)                     # reluz: aclara lo que mira a la luz, oscurece lo demás
    V = np.array([0, 0, 1.0], np.float32)
    Hh = (L + V) / np.linalg.norm(L + V)
    sp = np.clip((n * Hh).sum(2), 0, 1) ** 28 * spec   # brillo especular sobre la pintura real
    base = rgb * sh[..., None] * brillo
    base = base + 255 * sp[..., None] * (0.55 + 0.45 * np.clip(rgb.mean(2, keepdims=True) / 255, 0, 1))
    return np.clip(base, 0, 255), np.clip(al, 0, 1), bo


def dibujar(img, a, cx, cy, alto, yaw=0.0, pitch=0.0, esc=1.0, luz=(-0.5, -0.6), luz_k=0.55, spec=0.45,
            reflejo=0.28, sombra=0.8, borde=0.6, borde_col=(255, 255, 255), fx=None, alfa=1.0, piso_y=None,
            brillo=1.0, xray=0.0, xray_col=(120, 225, 255)):
    """Pega el vehículo (activo `a`) en img (PIL RGB) centrado en (cx, cy) con `alto` px de alto.
    yaw/pitch: órbita por paralaje (−1…1). esc: zoom dentro del recorte. luz: dirección de la luz (x, y) en pantalla.
    xray: 0–1, el vehículo se vuelve de cristal con bordes cian (rayos X de cristal del canal)."""
    if alfa <= 0.01:
        return
    rgb, al, bo = render_activo(a, yaw, pitch, esc, luz, luz_k, spec, brillo)
    s = alto / a.h
    W2, H2 = max(2, int(a.w * s)), max(2, int(a.h * s))
    rgb = cv2.resize(rgb, (W2, H2), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    al = cv2.resize(al, (W2, H2), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR) * alfa
    bo = cv2.resize(bo, (W2, H2), interpolation=cv2.INTER_LINEAR) * alfa
    if xray > 0:
        g = rgb.mean(2, keepdims=True)
        edge = cv2.Canny(np.clip(g[..., 0], 0, 255).astype(np.uint8), 40, 110).astype(np.float32) / 255
        edge = cv2.GaussianBlur(edge, (0, 0), 1.0)[..., None]
        glass = g * 0.25 + np.array(xray_col, np.float32) * (edge * 1.4 + 0.08)
        rgb = rgb * (1 - xray) + glass * xray
    x0, y0 = int(cx - W2 / 2), int(cy - H2 / 2)
    Wi, Hi = img.size
    canvas = np.asarray(img, np.float32).copy()
    # piso: sombra de contacto y reflejo
    py = int(piso_y if piso_y is not None else y0 + H2 * 0.97)
    if sombra > 0:
        sh = np.zeros((Hi, Wi), np.float32)
        cv2.ellipse(sh, (int(cx), py), (int(W2 * 0.46), max(4, int(H2 * 0.05))), 0, 0, 360, 1.0, -1)
        sh = cv2.GaussianBlur(sh, (0, 0), max(3, H2 * 0.03))
        canvas *= (1 - sh * sombra * 0.85 * alfa)[..., None]
    if reflejo > 0:
        fl = rgb[::-1]
        fa = al[::-1] * np.linspace(1, 0, H2, dtype=np.float32)[:, None] ** 2.2 * reflejo
        ry0 = py + (py - (y0 + H2)) - 0
        _pegar(canvas, fl, fa, x0, ry0)
    _pegar(canvas, rgb, al, x0, y0)
    if borde > 0:
        rim = np.zeros((H2, W2, 3), np.float32) + np.array(borde_col, np.float32)
        _pegar_add(canvas, rim, bo * borde * 0.55, x0, y0)
        if fx is not None:
            fxa = np.asarray(fx, np.float32).copy()
            _pegar_add(fxa, rim, cv2.GaussianBlur(bo, (0, 0), 3) * borde * 0.5, x0, y0)
            if xray > 0:
                pass
            fx.paste(Image.fromarray(fxa.clip(0, 255).astype(np.uint8)))
    img.paste(Image.fromarray(canvas.clip(0, 255).astype(np.uint8)))
    return (x0, y0, W2, H2)


def _clip(canvas, x0, y0, w, h):
    Hc, Wc = canvas.shape[:2]
    ax0, ay0 = max(0, x0), max(0, y0)
    ax1, ay1 = min(Wc, x0 + w), min(Hc, y0 + h)
    if ax1 <= ax0 or ay1 <= ay0:
        return None
    return ax0, ay0, ax1, ay1, ax0 - x0, ay0 - y0


def _pegar(canvas, src, a, x0, y0):
    c = _clip(canvas, x0, y0, src.shape[1], src.shape[0])
    if not c:
        return
    ax0, ay0, ax1, ay1, sx, sy = c
    s = src[sy:sy + ay1 - ay0, sx:sx + ax1 - ax0]
    al = a[sy:sy + ay1 - ay0, sx:sx + ax1 - ax0][..., None]
    reg = canvas[ay0:ay1, ax0:ax1]
    canvas[ay0:ay1, ax0:ax1] = reg * (1 - al) + s * al


def _pegar_add(canvas, src, a, x0, y0):
    c = _clip(canvas, x0, y0, src.shape[1], src.shape[0])
    if not c:
        return
    ax0, ay0, ax1, ay1, sx, sy = c
    s = src[sy:sy + ay1 - ay0, sx:sx + ax1 - ax0]
    al = a[sy:sy + ay1 - ay0, sx:sx + ax1 - ax0][..., None]
    canvas[ay0:ay1, ax0:ax1] += s * al


# ================================================================== foto completa en 3D (paralaje de toda la escena)
def preparar_escena(ruta, nombre, ancho_max=1400, forzar=False):
    """Foto entera (sin recortar) con profundidad: para «meterse» en una foto histórica con paralaje."""
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, nombre + '.npz')
    if not (os.path.exists(out) and not forzar):
        im = Image.open(ruta).convert('RGB')
        if im.width > ancho_max:
            im = im.resize((ancho_max, int(im.height * ancho_max / im.width)), Image.LANCZOS)
        rgb = np.asarray(im)
        d = _prof(rgb).astype(np.float32)
        np.savez_compressed(out, rgb=rgb, m=np.ones(rgb.shape[:2], np.float32), d=d)
    a = cargar(nombre)
    a.dw = cv2.GaussianBlur(a.d, (0, 0), 0.02 * max(a.d.shape))
    return a


def dibujar_escena(img, a, box, yaw=0.0, pitch=0.0, esc=1.12, luz=(-0.4, -0.6), marco=16, angulo=0.0, alfa=1.0,
                   sombra=True, tinte=None):
    """Pinta la foto entera con paralaje dentro de box=(x0, y0, x1, y1) (recorte tipo «cover»).
    marco: borde blanco de foto impresa (0 = sin marco). angulo: giro de la tarjeta en grados."""
    if alfa <= 0.01:
        return
    rgb, _, _ = render_activo(a, yaw, pitch, esc, luz, luz_k=0.22, spec=0.0)
    x0, y0, x1, y1 = [int(v) for v in box]
    bw, bh = x1 - x0, y1 - y0
    s = max(bw / a.w, bh / a.h)
    rw, rh = int(a.w * s) + 1, int(a.h * s) + 1
    r = cv2.resize(rgb, (rw, rh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    ox, oy = (rw - bw) // 2, (rh - bh) // 2
    r = r[oy:oy + bh, ox:ox + bw]
    if tinte is not None:
        g = r.mean(2, keepdims=True)
        r = r * (1 - tinte[1]) + g * np.array(tinte[0], np.float32) / 255 * tinte[1]
    ph = Image.fromarray(np.clip(r, 0, 255).astype(np.uint8))
    if marco:
        card = Image.new('RGB', (bw + 2 * marco, bh + 2 * marco), (245, 244, 240))
        card.paste(ph, (marco, marco))
    else:
        card = ph
    card = card.convert('RGBA')
    if angulo:
        card = card.rotate(angulo, resample=Image.BICUBIC, expand=True)
    if alfa < 1:
        card.putalpha(card.getchannel('A').point(lambda v: int(v * alfa)))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    px, py = int(cx - card.width / 2), int(cy - card.height / 2)
    if sombra:
        sh = Image.new('RGBA', card.size, (0, 0, 0, 0))
        sh.paste((0, 0, 0, int(150 * alfa)), (0, 0), card.getchannel('A'))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        img.paste(sh, (px + 14, py + 22), sh)
    img.paste(card, (px, py), card)
