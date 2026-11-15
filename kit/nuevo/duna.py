"""Reel diario lun 16-nov-2026 18:00 — «Tu llanta en la duna… va desinflada.» (física de la llanta en la arena:
huella más grande, misma fuerza repartida = flota; error: salir al pavimento con la llanta baja).
Comunidad: riders de side by side (la misma del razer viral del 9-nov). Médanos de Samalayuca (Chihuahua).
Inicio tipo 2 (cae y rebota): un side by side REAL (foto CC0 en 3D) cae sobre la duna, rebota con sacudida y el título se
estrella («DUNA» de cristal detrás). El final («porque su llanta en la duna… va desinflada») regresa a él (loop).
Voz Isaac (eleven_v4) generada el 13-nov (inbox/narr_duna.mp3), 60.0 s. Datos y fuentes: guiones/2026-11-16_duna.txt.
La llanta, la huella y las fuerzas son un modelo 3D marcado «ESQUEMA»; las presiones son de una guía (DrivingLine).
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, line3, dot3, rec_frame,
                    named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
TEMA = 'duna'
TXT = ['Tu llanta en la duna… va desinflada.',
       'No está ponchada:',
       'en Samalayuca, los riders le sacan aire a propósito.',
       'Mira la prueba: la misma llanta, inflada y desinflada.',
       'Inflada, queda redonda y dura:',
       'pisa con un cachito… y se entierra.',
       'Desinflada, se aplasta:',
       'su huella se hace más larga y más ancha.',
       'Mismo peso, repartido en más arena…',
       'y en vez de hundirse, flota.',
       'Como en la nieve: con zapato te hundes;',
       'con raqueta, caminas encima.',
       'Pero aquí está el error: salir de la duna y agarrar el pavimento así.',
       'En el pavimento, la llanta baja se dobla en cada vuelta,',
       'se calienta y puede tronar de golpe.',
       'Y hasta se puede zafar del rin y dejarte sin aire de un jalón.',
       'Por eso, con rines que la amarran,',
       'hay guías que la bajan a 6 u 8 libras en la duna…',
       'y antes de salir al camino, se vuelve a inflar a su presión normal.',
       'Mándaselo a tu compa que siempre se atasca en la duna,',
       'porque su llanta en la duna… va desinflada.']
_REPO = os.path.dirname(os.path.dirname(HERE))
VOZ = [x.strip() for x in open(os.path.join(_REPO, 'guiones', '2026-11-16_duna_voz.txt'), encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)
WORDS = '/home/claude/words_duna.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'inbox', 'words_duna.json')

import foto3d as F3

AMARILLO = (255, 236, 160)
ROJO = (255, 60, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
VERDE = (120, 235, 150)
ARENA = (226, 196, 146)
ARENA_O = (150, 122, 84)
NIEVE = (235, 242, 250)

# ------------------------------------------------------------------ foto real (Wikimedia Commons, CC0)
CRED = 'FOTO: HJUDALL · CC0 · WIKIMEDIA COMMONS'
VEH = F3.preparar(os.path.join(HERE, 'img', 'canam', 'canam_i_rzr23.jpg'), 'rzr23')


def veh(img, fx, cx, piso, alto, yaw=0.0, pitch=0.15, t=0.0, alfa=1.0, dy=0.0, reflejo=0.0, sombra=0.8):
    luz = (-0.65 + 0.55 * math.sin(t * 0.9), -0.62)
    return F3.dibujar(img, VEH, cx, piso - alto * 0.5 + dy, alto, yaw=yaw, pitch=pitch, luz=luz, fx=fx, alfa=alfa,
                      reflejo=reflejo, borde=0.55, piso_y=piso + dy, sombra=sombra)


def credito(img, k=1.0, y=1872):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((540, y), CRED, font=M.font('mono', 19), fill=M.scale_c((150, 150, 158), k), anchor='mm')


# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    d = json.load(open(WORDS))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(montaje._norm(w.get('text', '')), float(w['start'])) for w in d
          if w.get('type', 'word') == 'word' and montaje._norm(w.get('text', ''))]
    sw = []
    for i, f in enumerate(VOZ):
        for w in re.sub(r'\[[^\]]*\]', ' ', f).split():
            if montaje._norm(w):
                sw.append((i, montaje._norm(w)))
    sm = difflib.SequenceMatcher(None, [w for _, w in sw], [w for w, _ in tw], autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    per = {}
    for j, (i, w) in enumerate(sw):
        per.setdefault(i, []).append(tw[mp[j]][1] if j in mp else None)
    for i, L in per.items():
        last = None
        for k in range(len(L)):
            if L[k] is None and last is not None:
                L[k] = last + 0.25
            last = L[k] if L[k] is not None else last
        base = next(x for x in L if x is not None)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wu(i, k):
    L = _wt()[i]
    return L[min(k, len(L) - 1)]


# ------------------------------------------------------------------ utilidades
def cam(u, claves, cy=0.55):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p.get('tx', 0.0), p.get('ty', 0.4), p.get('tz', 0.0)), dist=p['dist'], yaw=p['yaw'],
               pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch, tx=0.0, ty=0.4, tz=0.0, roll=0.0):
    return (u, dict(dist=dist, yaw=yaw, pitch=pitch, tx=tx, ty=ty, tz=tz, roll=roll))


def golpe_k(u, u0, dur=0.32):
    return (1 - seg(u, u0, u0 + dur)) ** 2 if u >= u0 else 0.0


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    return P.mover_img(img, amp * k * math.sin(t * 91.0) * math.cos(t * 37.0), amp * k * math.sin(t * 73.0 + 1.3))


def punch(img, u, u0, s1=1.25, dur=0.3, cx=0.5, cy=0.5):
    k = P.eout4(seg(u, u0, u0 + dur))
    if k <= 0.001:
        return img
    return M.scale_about(img, 1 + (s1 - 1) * k, cx, cy)


def rr(d, box, radius=0, **kw):
    x0, y0, x1, y1 = box
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    r = max(0, min(radius, (x1 - x0) / 2 - 1, (y1 - y0) / 2 - 1))
    d.rounded_rectangle((x0, y0, x1, y1), radius=r, **kw)


def texto(img, fx, x, y, txt, size, col=WHITE, k=1.0, f='sansx', glow=0.35, anchor='mm'):
    if k <= 0.01:
        return
    lay = Image.new('L', img.size, 0)
    ImageDraw.Draw(lay).text((x, y), txt, font=M.font(f, size), fill=int(255 * clamp(k)), anchor=anchor)
    img.paste(Image.new('RGB', img.size, col), (0, 0), lay)
    if glow:
        fx.paste(Image.new('RGB', img.size, M.scale_c(col, glow)), (0, 0), lay.filter(ImageFilter.GaussianBlur(8)))


def flecha(img, fx, x0, y0, x1, y1, col, k=1.0, w=8):
    if k <= 0.01:
        return
    x1, y1 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    df.line([(x0, y0), (x1, y1)], fill=M.scale_c(col, 0.6), width=w * 3)
    a = math.atan2(y1 - y0, x1 - x0)
    L = 22 + w
    for s in (-1, 1):
        xa, ya = x1 - L * math.cos(a + s * 0.5), y1 - L * math.sin(a + s * 0.5)
        d.line([(x1, y1), (xa, ya)], fill=col, width=w)
        df.line([(x1, y1), (xa, ya)], fill=M.scale_c(col, 0.6), width=w * 3)


def tache(img, fx, x, y, r, k, t, col=ROJO, seed=3):
    N.doodle_arrow_free(img, fx, x - r, y - r, x + r, y + r, t, seg(k, 0.0, 0.5), col, seed=seed)
    N.doodle_arrow_free(img, fx, x + r, y - r, x - r, y + r, t, seg(k, 0.4, 0.9), col, seed=seed + 1)


def esquema(img, fx, k=1.0, y=1440, txt='ESQUEMA'):
    pill(img, fx, 540, y, txt, k, size=20, border=(150, 150, 160), dot=False)


# ------------------------------------------------------------------ la llanta 3D (eje z, rueda hacia +x)
RC, TA, TB = 0.36, 0.15, 0.21
ROUT = RC + TA


def llanta(defl=0.0, sink=0.0, giro=0.0, calor=0.0, x=0.0, z=0.0, amarre=0.0, sep=0.0, s=1.0, nu=44, nv=14, rin=True):
    """defl 0–1: desinflada (abajo se aplana y los costados se abomban). sink: se hunde (m). giro: rueda (rad).
    calor 0–1: se pone roja. sep: el rin se sale de la llanta (m, en +z). amarre 0–1: tornillos del rin de amarre."""
    dlt = 0.012 + 0.13 * defl
    yc = ROUT - dlt - sink
    V, F, C = [], [], []
    for i in range(nu):
        th = 2 * math.pi * i / nu + giro
        for j in range(nv):
            ph = 2 * math.pi * j / nv
            cp, sp = math.cos(ph), math.sin(ph)
            cp2 = math.copysign(abs(cp) ** 0.55, cp)
            sp2 = math.copysign(abs(sp) ** 0.7, sp)
            r = RC + TA * cp2
            px, py, pz = r * math.cos(th), r * math.sin(th), TB * sp2
            y = py + yc
            if y < 0.0:
                y = 0.0
            low = clamp((0.34 - y) / 0.3)
            pz *= 1 + 0.42 * defl * low
            px *= 1 + 0.18 * defl * low * (1 if abs(math.sin(th)) > 0.6 else 0.5)
            V.append((px + x, y, pz + z))
    calc = M.mixc((30, 30, 33), (235, 90, 40), calor)
    for i in range(nu):
        for j in range(nv):
            a, b = i * nv + j, ((i + 1) % nu) * nv + j
            c, d = ((i + 1) % nu) * nv + (j + 1) % nv, i * nv + (j + 1) % nv
            F.append((a, b, c, d))
            ph = 2 * math.pi * (j + 0.5) / nv
            if math.cos(ph) > 0.45:
                col = (40, 40, 44) if (i + j // 2) % 2 else (20, 20, 22)
                col = M.mixc(col, (200, 80, 40), calor * 0.6)
            else:
                col = calc
            C.append(col)
    m = named(M3.Mesh(V, F, C, shadow=0, gloss=0.15, double=True), 'llanta', rim=0.45, gloss=0.15)
    if calor > 0.05:
        m.glow = M.scale_c((255, 90, 40), 0.35 * calor)
    ms = [m]
    if rin:
        ms.append(named(M3.cyl(0.222, 0.34, (108, 110, 118), n=24, shadow=0, gloss=0.85).tf(rx=90, t=(x, yc, z + sep - 0.17)),
                        'rin', rim=0.8, gloss=0.85))
        ms.append(named(M3.cyl(0.08, 0.36, (50, 52, 58), n=12, shadow=0, gloss=0.7).tf(rx=90, t=(x, yc, z + sep - 0.165)),
                        'rin', rim=0.6))
        for j in range(5):
            a = giro + j * 2 * math.pi / 5
            ms.append(named(M3.box(0.22, 0.05, 0.02, (90, 92, 100), shadow=0, base=False, gloss=0.8)
                            .tf(rz=math.degrees(a), t=(x + 0.12 * math.cos(a), yc + 0.12 * math.sin(a), z + sep + 0.185)), 'rin', rim=0.6))
        if amarre > 0.01:
            n = 16
            for j in range(n):
                kj = clamp(amarre * n - j)
                if kj <= 0:
                    continue
                a = giro + j * 2 * math.pi / n
                b = named(M3.cyl(0.018, 0.04 * P.resorte(kj), (210, 180, 90), n=8, shadow=0, gloss=0.9)
                          .tf(rx=90, t=(x + 0.25 * math.cos(a), yc + 0.25 * math.sin(a), z + sep + 0.19)), 'perno', rim=0.9)
                ms.append(b)
            ring = named(M3.cyl(0.275, 0.02, (40, 40, 46), n=32, shadow=0, gloss=0.7).tf(rx=90, t=(x, yc, z + sep + 0.175)), 'aro', rim=0.7)
            ring.alpha = clamp(amarre * 3)
            ms.insert(1, ring)
    return P.tfk(ms, s=s) if s != 1.0 else ms


def huella_dim(defl):
    """Largo y ancho (m) de la huella: inflada ≈ 0.22 × 0.34; desinflada ≈ 0.7 × 0.46 (ESQUEMA)."""
    return 0.22 + 0.48 * defl, 0.34 + 0.12 * defl


def huella(fr, x, z, defl, col=AMARILLO, a=1.0, fill=True):
    L, Wd = huella_dim(defl)
    pts = [(x + L / 2 * math.cos(q), 0.012, z + Wd / 2 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 48)]
    if fill and a > 0.01:
        s, zz = fr.cam.proj(pts)
        if (zz > 0.2).all():
            fr.df.polygon([tuple(p) for p in s], fill=M.scale_c(col, 0.35 * a))
    line3(fr, pts, col=col, w=3, a=a, glow=1.0)


def arena(fr, t, a=1.0, z0=-4.0, z1=4.0, x0=-5, x1=5, col=ARENA, sink_x=None, n=16):
    """Duna en línea de luz: ondas de arena (crestas) en perspectiva."""
    for j in range(n):
        z = lerp(z0, z1, j / (n - 1))
        xs = np.linspace(x0, x1, 60)
        pts = [(x, 0.02 + 0.05 * math.sin(x * 1.7 + z * 2.3 + j), z) for x in xs]
        line3(fr, pts, col=col, w=1.5, a=a * (0.35 + 0.25 * (j % 2)), glow=0.25)


def monticulos(x, z, k, s=1.0):
    """Arena que se amontona alrededor de una llanta que se entierra."""
    out = []
    if k < 0.05:
        return out
    for dx, sx in ((-0.5, 1.0), (0.5, 1.0)):
        m = named(M3.sphere(0.32, ARENA_O, nu=16, nv=8, shadow=0, gloss=0.1).tf(s=(0.9 * sx * s, 0.5 * k * s + 0.01, 0.9 * s),
                                                                            t=(x + dx * s, 0, z)), 'arena', rim=0.4)
        out.append(m)
    return out


def manometro(img, fx, cx, cy, r, psi, k=1.0, zona=None, vmax=30):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    rr_ = r * P.resorte(k) if k < 1 else r
    d.ellipse((cx - rr_, cy - rr_, cx + rr_, cy + rr_), fill=(14, 15, 19), outline=(220, 224, 232), width=6)
    a0, a1 = 135, 405

    def ang(v):
        return math.radians(a0 + (a1 - a0) * clamp(v / vmax))
    if zona:
        za, zb = zona
        d.arc((cx - rr_ * 0.82, cy - rr_ * 0.82, cx + rr_ * 0.82, cy + rr_ * 0.82), math.degrees(ang(za)), math.degrees(ang(zb)),
              fill=VERDE, width=int(rr_ * 0.12))
        df.arc((cx - rr_ * 0.82, cy - rr_ * 0.82, cx + rr_ * 0.82, cy + rr_ * 0.82), math.degrees(ang(za)), math.degrees(ang(zb)),
               fill=M.scale_c(VERDE, 0.6), width=int(rr_ * 0.2))
    for v in range(0, vmax + 1, 2):
        a = ang(v)
        L = 0.16 if v % 10 == 0 else 0.08
        d.line([(cx + rr_ * 0.92 * math.cos(a), cy + rr_ * 0.92 * math.sin(a)),
                (cx + rr_ * (0.92 - L) * math.cos(a), cy + rr_ * (0.92 - L) * math.sin(a))], fill=(220, 224, 232), width=4)
        if v % 10 == 0:
            d.text((cx + rr_ * 0.6 * math.cos(a), cy + rr_ * 0.6 * math.sin(a)), str(v), font=M.font('mono', int(rr_ * 0.18)),
                   fill=(220, 224, 232), anchor='mm')
    a = ang(psi)
    d.line([(cx, cy), (cx + rr_ * 0.78 * math.cos(a), cy + rr_ * 0.78 * math.sin(a))], fill=ROJO, width=8)
    df.line([(cx, cy), (cx + rr_ * 0.78 * math.cos(a), cy + rr_ * 0.78 * math.sin(a))], fill=M.scale_c(ROJO, 0.6), width=16)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(220, 224, 232))
    d.text((cx, cy + rr_ * 0.45), 'LIBRAS (PSI)', font=M.font('mono', int(rr_ * 0.12)), fill=(160, 166, 178), anchor='mm')


def aire(img, fx, x, y, t, k=1.0, dirx=1.0, n=6, col=(220, 235, 245)):
    """Chorro de aire que sale (rayitas curvas que se alejan)."""
    if k <= 0.01:
        return
    d = ImageDraw.Draw(img)
    for j in range(n):
        ph = (t * 2.2 + j / n) % 1.0
        L = 40 + 90 * ph
        yy = y + (j - n / 2) * 14 * (0.5 + ph)
        xx = x + dirx * 160 * ph
        d.line([(xx, yy), (xx + dirx * L, yy - 6)], fill=M.scale_c(col, k * (1 - ph)), width=4)


# ================================================================== escenas
# 0. gancho, inicio tipo 2 (cae y rebota): el side by side real cae a la duna, rebota y se sacude; «DUNA» de cristal.
#    En el loop (u negativo) está parado en la duna con el título y al final brinca hacia arriba (sale del cuadro).
UC = 0.12          # aterriza


def _u_loop():
    T, DUR = montaje.CTX['T'], montaje.CTX['DUR']
    return T[20][0] - DUR - T[0][0]


def s_gancho(t, fi, u, d):
    ul = _u_loop()
    fr = Frame(cam(u, [K(ul - 0.3, 6.0, -20, 14, ty=0.6), K(ul + 0.5, 5.6, -8, 12, ty=0.6), K(-0.25, 6.4, 0, 16, ty=0.8),
                       K(UC, 5.2, 6, 10, ty=0.6), K(2.0, 5.0, 12, 10, ty=0.6), K(5, 5.0, 14, 10, ty=0.6)], cy=0.56))
    space(fr, t, floor=None, bokeh=1.0, beam=0.6)
    arena(fr, t, a=1.0)
    # altura (px) del vehículo sobre el piso: brinca al final del loop y cae al inicio
    if u < -0.6:
        dy = 0.0
    elif u < -0.25:
        dy = -760 * ease(seg(u, -0.6, -0.25))
    else:
        dy = -760 * (1 - P.rebote(seg(u, -0.25, UC + 0.35), n=2.0, amort=6))
    kk = golpe_k(u, UC, 0.5)

    def ui(img, fx):
        M.cristal(img, fx, 'DUNA', u, t0=-3.0, cy=0.36, entrada='golpe')
        piso = 1330
        veh(img, fx, 540, piso, 560, yaw=0.25 * math.sin(t * 0.7), pitch=0.15, t=t, dy=dy, sombra=0.8 * (1 + dy / 760))
        # arena que salta al aterrizar
        if UC <= u < UC + 0.8:
            kp = seg(u, UC, UC + 0.8)
            dd = ImageDraw.Draw(img)
            for j in range(26):
                a = math.pi * (0.1 + 0.8 * ((j * 0.37) % 1.0))
                v = 500 + 300 * ((j * 0.61) % 1.0)
                x = 540 + math.cos(a) * v * kp * (1 if j % 2 else -1)
                y = piso - math.sin(a) * v * kp * 0.9 + 900 * kp * kp
                rad = 5 + j % 4
                dd.ellipse((x - rad, y - rad, x + rad, y + rad), fill=M.scale_c(ARENA, 1 - kp))
        k1 = seg(u, 0.0, 0.15) if u >= -0.1 else seg(u, ul + 0.05, ul + 0.2) * (1 - seg(u, -0.6, -0.4))
        k2 = seg(u, Wu(0, 5), Wu(0, 5) + 0.15) if u >= -0.1 else seg(u, ul + Wu(20, 6), ul + Wu(20, 6) + 0.15) * (1 - seg(u, -0.6, -0.4))
        kicker(img, 'SIDE BY SIDE · MÉDANOS DE SAMALAYUCA', 128, k1, col=AZULC)
        P.titulo_golpe(img, fx, [('Tu llanta en la duna', 'sans')], 175, k1, size=86)
        P.titulo_golpe(img, fx, [('va desinflada.', 'serif')], 285, k2, size=96)
        credito(img)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(kk, golpe_k(u, Wu(0, 5) + 0.15, 0.3) * 0.6), amp=26)


# 1. no está ponchada (la llanta gira de frente; el clavo aparece y se tacha)
def s_ponchada(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.6, 60, 14, ty=0.45), K(0.3, 2.1, 24, 8, ty=0.45), K(3, 2.05, 18, 8, ty=0.45)], cy=0.52))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    e = P.entrada(u, -0.2, 0.3, 'gira')
    draw_objects(fr, llanta(defl=0.0, giro=-t * 2.0 + e['giro'], s=max(0.05, e['escala'])))
    pc = fr.cam.p1((0.0, ROUT * 2 + 0.05, 0.0))

    def ui(img, fx):
        kicker(img, '¿PONCHADA?', 150, seg(u, -0.1, 0.2), col=AZULC)
        # clavo
        k = P.resorte(seg(u, 0.1, 0.4))
        if k > 0.01:
            dd = ImageDraw.Draw(img)
            x, y = pc[0] + 230, pc[1] - 120
            dd.line([(x, y - 90 * k), (x, y + 90 * k)], fill=(200, 204, 214), width=12)
            dd.rectangle((x - 30 * k, y - 96 * k, x + 30 * k, y - 82 * k), fill=(200, 204, 214))
            tache(img, fx, x, y, 110, seg(u, 0.5, 1.0), t)
        pill(img, fx, 540, 1330, '✗ NO ESTÁ PONCHADA', eout(seg(u, 0.6, 0.9)), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. en Samalayuca los riders le sacan aire a propósito (duna de línea de luz, «SAMALAYUCA» de cristal, aire que sale
#    de la válvula y el manómetro que baja)
def s_samalayuca(t, fi, u, d):
    us = Wu(2, 5) - 0.1                                    # «sacan aire»
    fr = Frame(cam(u, [K(-0.3, 3.4, -40, 20, ty=0.4), K(0.35, 2.6, -14, 12, ty=0.4), K(us, 2.2, -4, 10, ty=0.42),
                       K(4, 2.15, 0, 10, ty=0.42)], cy=0.6))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    arena(fr, t, a=0.9)
    M.cristal(fr.base, fr.fx, 'SAMALAYUCA', u, t0=-0.15, cy=0.33, entrada='sube')
    kd = 0.6 * seg(u, us, us + 2.0)
    draw_objects(fr, llanta(defl=kd, giro=0.4))
    pv = fr.cam.p1((0.17, ROUT + 0.17, TB + 0.05))

    def ui(img, fx):
        kicker(img, 'MÉDANOS DE SAMALAYUCA · CHIHUAHUA', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > us:
            aire(img, fx, pv[0], pv[1], t, k=seg(u, us, us + 0.2))
            pill(img, fx, pv[0] + 40, pv[1] - 120, 'A PROPÓSITO', eout(seg(u, us + 0.3, us + 0.6)), size=30, border=AMARILLO, dot=False)
        manometro(img, fx, 860, 1280, 130, 20 - 12 * seg(u, us, us + 2.0), k=seg(u, us - 0.3, us))
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. la prueba: la misma llanta, inflada y desinflada (dos llantas lado a lado; la cámara orbita)
def s_prueba(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 4.0, 70, 18, ty=0.4), K(0.35, 3.4, 28, 12, ty=0.4), K(2.0, 3.3, 12, 10, ty=0.4),
                       K(5, 3.25, 8, 10, ty=0.4)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    e1 = P.entrada(u, -0.25, 0.3, 'cae')
    e2 = P.entrada(u, 0.0, 0.3, 'cae')
    ms = P.tfk(llanta(defl=0.0, giro=0.3), t=(-0.75, max(0.0, -e1['dy']) * 0.6, 0))
    ms += P.tfk(llanta(defl=0.85, giro=0.3), t=(0.75, max(0.0, -e2['dy']) * 0.6, 0))
    draw_objects(fr, ms)
    pa = fr.cam.p1((-0.75, -0.08, 0.3))
    pb = fr.cam.p1((0.75, -0.08, 0.3))

    def ui(img, fx):
        kicker(img, 'LA PRUEBA · MISMA LLANTA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pa[0], pa[1] + 80, 'INFLADA', eout(seg(u, 0.4, 0.7)), size=32, border=CYAN, dot=False)
        pill(img, fx, pb[0], pb[1] + 80, 'DESINFLADA', eout(seg(u, 0.9, 1.2)), size=32, border=AMARILLO, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.05, 0.25), golpe_k(u, 0.3, 0.25)), amp=12)


# 4. inflada queda redonda y dura (círculo perfecto que se dibuja encima, manómetro alto)
def s_inflada(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.0, 0, 6, ty=0.5), K(0.3, 2.3, -18, 8, ty=0.5), K(3, 2.35, -22, 8, ty=0.5)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    draw_objects(fr, llanta(defl=0.0, giro=-t * 1.2))
    pc = fr.cam.p1((0.0, ROUT, TB))

    def ui(img, fx):
        texto(img, fx, 540, 300, 'INFLADA', 120, CYAN, seg(u, -0.1, 0.1), f='sansx', glow=0.5)
        doodle_circle(img, fx, pc[0], pc[1], 330, 330, t, k=seg(u, 0.3, 0.8), col=CYAN, seed=2)
        pill(img, fx, 540, 1330, 'REDONDA Y DURA', eout(seg(u, 0.8, 1.1)), size=32, border=CYAN, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. pisa con un cachito… y se entierra (vista de lado: huella chiquita, se hunde y la arena se amontona; «ENTIERRA»)
def s_entierra(t, fi, u, d):
    ue = Wu(5, 5) - 0.1                                    # «se entierra»
    sk = 0.26 * P.eout4(seg(u, ue, ue + 0.7))
    fr = Frame(cam(u, [K(-0.3, 2.7, 40, 18, ty=0.3), K(0.35, 2.4, 16, 10, ty=0.3), K(ue, 2.1, 8, 8, ty=0.25),
                       K(4, 2.05, 6, 8, ty=0.25)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.9, beam=0.4)
    arena(fr, t, a=0.8, z0=-3, z1=3)
    M.cristal(fr.base, fr.fx, 'ENTIERRA', u, t0=ue, cy=0.3, entrada='golpe')
    draw_objects(fr, llanta(defl=0.0, sink=sk, giro=-u * 3.0 * (1 - seg(u, ue, ue + 0.8))) + monticulos(0, 0, sk / 0.26))
    huella(fr, 0, 0, 0.0, col=ROJO, a=seg(u, 0.2, 0.5) * (1 - seg(u, ue, ue + 0.3)))
    ph = fr.cam.p1((0.0, 0.0, 0.0))

    def ui(img, fx):
        kicker(img, 'INFLADA EN LA ARENA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, ph[0], ph[1] + 110, 'PISA CON UN CACHITO', eout(seg(u, 0.3, 0.6)) * (1 - seg(u, ue, ue + 0.2)), size=28,
             border=ROJO, dot=False)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ue + 0.2, 0.4), amp=18)


# 6. desinflada, se aplasta (sale el aire y la panza de abajo se aplana en vivo)
def s_aplasta(t, fi, u, d):
    ua = Wu(6, 2) - 0.1                                    # «se aplasta»
    kd = P.eout4(seg(u, ua - 0.3, ua + 0.6))
    fr = Frame(cam(u, [K(-0.3, 1.8, 40, 6, ty=0.35), K(0.35, 2.1, 12, 4, ty=0.35), K(3, 2.15, 8, 4, ty=0.35)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    draw_objects(fr, llanta(defl=kd, giro=0.2))
    pv = fr.cam.p1((0.17, ROUT + 0.17, TB + 0.05))
    pb = fr.cam.p1((0.0, 0.02, TB))

    def ui(img, fx):
        texto(img, fx, 540, 300, 'DESINFLADA', 110, AMARILLO, seg(u, -0.1, 0.1), f='sansx', glow=0.5)
        aire(img, fx, pv[0], pv[1], t, k=1 - seg(u, ua + 0.4, ua + 0.8))
        if kd > 0.3:
            for s_ in (-1, 1):
                flecha(img, fx, pb[0], pb[1] + 40, pb[0] + s_ * 260 * kd, pb[1] + 40, AMARILLO, k=eout(seg(u, ua, ua + 0.4)), w=6)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 7. su huella se hace más larga y más ancha (vista de arriba: dos huellas con cotas; «HUELLA» de cristal)
def s_huella(t, fi, u, d):
    ul = Wu(7, 6) - 0.1                                    # «más larga»
    uw = Wu(7, 9) - 0.1                                    # «más ancha»
    fr = Frame(cam(u, [K(-0.3, 3.2, -30, 40, ty=0.0), K(0.35, 3.4, 0, 78, ty=0.0), K(4, 3.45, 0, 80, ty=0.0)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    arena(fr, t, a=0.6, z0=-2.5, z1=2.5, x0=-2.5, x1=2.5)
    M.cristal(fr.base, fr.fx, 'HUELLA', u, t0=-0.1, cy=0.27, entrada='zoom')
    huella(fr, 0, -0.55, 0.0, col=CYAN, a=seg(u, 0.0, 0.3))
    kd = P.eout4(seg(u, ul - 0.3, uw + 0.3))
    huella(fr, 0, 0.45, kd, col=AMARILLO, a=seg(u, 0.1, 0.4))
    L, Wd = huella_dim(kd)
    p1, p2 = fr.cam.p1((-L / 2, 0, 0.45 + Wd / 2 + 0.12)), fr.cam.p1((L / 2, 0, 0.45 + Wd / 2 + 0.12))
    q1, q2 = fr.cam.p1((L / 2 + 0.12, 0, 0.45 - Wd / 2)), fr.cam.p1((L / 2 + 0.12, 0, 0.45 + Wd / 2))
    pi_ = fr.cam.p1((0, 0, -0.55))

    def ui(img, fx):
        kicker(img, 'VISTA DE ARRIBA · HUELLA EN LA ARENA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pi_[0], pi_[1] - 110, 'INFLADA', eout(seg(u, 0.1, 0.4)), size=26, border=CYAN, dot=False)
        ka = seg(u, ul, ul + 0.3)
        flecha(img, fx, (p1[0] + p2[0]) / 2, p1[1], p1[0], p1[1], AMARILLO, k=ka, w=6)
        flecha(img, fx, (p1[0] + p2[0]) / 2, p2[1], p2[0], p2[1], AMARILLO, k=ka, w=6)
        pill(img, fx, (p1[0] + p2[0]) / 2, p1[1] + 70, 'MÁS LARGA', eout(ka), size=28, border=AMARILLO, dot=False)
        kb = seg(u, uw, uw + 0.3)
        flecha(img, fx, q1[0], (q1[1] + q2[1]) / 2, q1[0], q1[1], AMARILLO, k=kb, w=6)
        flecha(img, fx, q2[0], (q1[1] + q2[1]) / 2, q2[0], q2[1], AMARILLO, k=kb, w=6)
        pill(img, fx, q1[0] + 40, (q1[1] + q2[1]) / 2, 'MÁS ANCHA', eout(kb), size=28, border=AMARILLO, dot=False, anchor='l')
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return finish(fr, fi)


# 8. mismo peso, repartido en más arena (flechas: una del peso y muchas chiquitas en la huella larga)
def s_peso(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.2, -60, 30, ty=0.35), K(0.35, 2.6, -24, 22, ty=0.35), K(4, 2.65, -18, 22, ty=0.35)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.9)
    arena(fr, t, a=0.7, z0=-3, z1=3)
    draw_objects(fr, llanta(defl=0.85, giro=0.2), xray=0.7, keep=('rin',))
    huella(fr, 0, 0, 0.85, col=AMARILLO, a=1.0)
    L, Wd = huella_dim(0.85)
    pts = []
    for i in range(7):
        for j in range(3):
            x = -L / 2 * 0.8 + L * 0.8 * i / 6
            z = -Wd / 2 * 0.6 + Wd * 0.6 * j / 2
            pts.append((fr.cam.p1((x, 0.16, z)), fr.cam.p1((x, 0.02, z))))
    pc = fr.cam.p1((0, ROUT + 0.3, 0))
    pf = fr.cam.p1((0, ROUT - 0.1, 0))

    def ui(img, fx):
        kicker(img, 'MISMO PESO · MÁS ARENA', 150, seg(u, -0.1, 0.2), col=AZULC)
        flecha(img, fx, pc[0], pc[1] - 200, pf[0], pf[1], WHITE, k=eout(seg(u, -0.1, 0.3)), w=12)
        pill(img, fx, pc[0], pc[1] - 250, 'PESO', eout(seg(u, 0.0, 0.3)), size=34, border=WHITE, dot=False)
        for n, (a, b) in enumerate(pts):
            flecha(img, fx, a[0], a[1], b[0], b[1], AMARILLO, k=eout(seg(u, 0.4 + 0.03 * n, 0.6 + 0.03 * n)), w=4)
        pill(img, fx, 540, 1330, 'MENOS PRESIÓN EN CADA CACHITO', eout(seg(u, 1.2, 1.5)), size=28, border=AMARILLO, dot=False)
        esquema(img, fx, 1.0, y=1420)
    fr.ui.append(ui)
    return finish(fr, fi)


# 9. y en vez de hundirse, flota (el side by side real va encima de las ondas de arena; «FLOTA» de cristal)
def s_flota(t, fi, u, d):
    uf = Wu(9, 5) - 0.1                                    # «flota»
    fr = Frame(cam(u, [K(-0.3, 5.0, -30, 30, ty=0.0), K(0.35, 5.6, -6, 14, ty=0.4), K(5, 5.6, -2, 14, ty=0.4)], cy=0.56))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    arena(fr, t + u * 2, a=1.0)

    def ui(img, fx):
        M.cristal(img, fx, 'FLOTA', u, t0=uf, cy=0.4, entrada='zoom')
        piso = 1300
        bob = 14 * math.sin(t * 6)
        veh(img, fx, 560 + 30 * math.sin(t), piso, 640, yaw=-0.5 + 0.3 * seg(u, 0, 2), pitch=0.2, t=t, dy=-30 * seg(u, uf, uf + 0.4) + bob,
            sombra=0.6)
        dd = ImageDraw.Draw(img)
        for j in range(30):
            ph = (t * 1.5 + j / 30) % 1.0
            x = 300 - 500 * ph + 30 * math.sin(j)
            y = piso - 40 - 160 * ph * (1 - ph) * 4 + (j % 5) * 6
            dd.ellipse((x - 4, y - 4, x + 4, y + 4), fill=M.scale_c(ARENA, 1 - ph))
        kicker(img, 'DESINFLADAS EN LA ARENA', 150, seg(u, -0.1, 0.2), col=AZULC)
        credito(img)
    fr.ui.append(ui)
    return finish(fr, fi)


# 10-11. nieve: con zapato te hundes; con raqueta caminas encima
def zapato(t_=(0, 0, 0), sink=0.0, ry=0.0):
    ms = [named(M3.rbox(0.22, 0.12, 0.52, 0.08, (70, 46, 30), n=3, shadow=0, gloss=0.3).tf(t=(0, -sink, 0)), 'zapato', rim=0.6),
          named(M3.rbox(0.2, 0.2, 0.22, 0.06, (80, 54, 36), n=3, shadow=0, gloss=0.3).tf(t=(0, 0.1 - sink, -0.13)), 'zapato', rim=0.6)]
    for m in ms:
        m.V[:, 1] = np.maximum(m.V[:, 1], 0.0)
    return P.tfk(ms, ry=ry, t=t_)


def nieve(fr, t, a=1.0):
    for j in range(14):
        z = lerp(-3, 3, j / 13)
        pts = [(x, 0.02 + 0.03 * math.sin(x * 2 + j), z) for x in np.linspace(-4, 4, 40)]
        line3(fr, pts, col=NIEVE, w=1.4, a=a * 0.45, glow=0.3)


def s_zapato(t, fi, u, d):
    uh = Wu(10, 7) - 0.1                                   # «te hundes»
    sk = 0.16 * P.eout4(seg(u, uh - 0.2, uh + 0.5))
    fr = Frame(cam(u, [K(-0.3, 2.2, 50, 26, ty=0.1), K(0.35, 1.8, 20, 18, ty=0.1), K(4, 1.75, 16, 18, ty=0.1)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.4, beam=0.4)
    nieve(fr, t)
    e = P.entrada(u, -0.25, 0.35, 'cae')
    ms = zapato((0, max(0.0, -e['dy']) * 0.3, 0), sink=sk)
    ms += [named(M3.sphere(0.2, (220, 228, 238), nu=14, nv=8, shadow=0, gloss=0.2).tf(s=(1.0, 0.4 * sk / 0.16 + 0.01, 1.6), t=(sx * 0.2, 0, 0)),
                 'nieve', rim=0.3) for sx in (-1, 1)]
    draw_objects(fr, ms)

    def ui(img, fx):
        texto(img, fx, 540, 300, 'CON ZAPATO', 100, WHITE, seg(u, -0.1, 0.1), f='sansx', glow=0.4)
        pill(img, fx, 540, 1330, '✗ TE HUNDES', eout(seg(u, uh, uh + 0.3)), size=32, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uh + 0.2, 0.3), amp=12)


def raqueta(fr, x=0.0, z=0.0, a=1.0):
    pts = [(x + 0.24 * math.cos(q), 0.03, z + 0.5 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 40)]
    line3(fr, pts, col=AMARILLO, w=4, a=a, glow=0.9)
    for j in range(-3, 4):
        zz = z + j * 0.12
        w = 0.24 * math.sqrt(max(0, 1 - (j * 0.12 / 0.5) ** 2))
        line3(fr, [(x - w, 0.03, zz), (x + w, 0.03, zz)], col=AMARILLO, w=1.6, a=a * 0.7, glow=0.4)
    for i in (-1, 0, 1):
        xx = x + i * 0.1
        line3(fr, [(xx, 0.03, z - 0.45), (xx, 0.03, z + 0.45)], col=AMARILLO, w=1.6, a=a * 0.7, glow=0.4)


def s_raqueta(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 1.8, -20, 18, ty=0.1), K(0.35, 2.0, -50, 26, ty=0.1), K(4, 2.05, -54, 26, ty=0.1)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.4, beam=0.4)
    nieve(fr, t)
    raqueta(fr, a=seg(u, -0.2, 0.2))
    e = P.entrada(u, -0.1, 0.3, 'cae')
    draw_objects(fr, zapato((0, 0.05 + max(0.0, -e['dy']) * 0.3, 0)))

    def ui(img, fx):
        texto(img, fx, 540, 300, 'CON RAQUETA', 100, AMARILLO, seg(u, -0.1, 0.1), f='sansx', glow=0.4)
        pill(img, fx, 540, 1330, '✓ CAMINAS ENCIMA', eout(seg(u, 0.4, 0.7)), size=32, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.25), amp=10)


# 12. SEGUNDO GANCHO: el error — salir de la duna al pavimento con la llanta así («PAVIMENTO» de cristal)
def asfalto(fr, t, xoff=0.0, a=1.0):
    piso = named(M3.box(14, 0.01, 4.2, (38, 38, 42), shadow=0, base=False, gloss=0.2), 'asfalto', rim=0.1)
    draw_objects(fr, [piso])
    for j in range(-8, 9):
        x = j * 1.2 - (xoff % 1.2)
        line3(fr, [(x, 0.012, 0.0), (x + 0.6, 0.012, 0.0)], col=AMARILLO, w=4, a=a, glow=0.4)
    for s_ in (-1, 1):
        line3(fr, [(-8, 0.012, s_ * 1.9), (8, 0.012, s_ * 1.9)], col=WHITE, w=3, a=a * 0.8, glow=0.3)


def s_error(t, fi, u, d):
    up = Wu(12, 11) - 0.1                                  # «pavimento»
    fr = Frame(cam(u, [K(-0.3, 3.4, -40, 22, ty=0.4), K(0.35, 2.9, -18, 14, ty=0.4), K(up, 2.5, 8, 10, ty=0.4),
                       K(up + 1.0, 2.6, 18, 12, ty=0.4), K(6, 2.65, 22, 12, ty=0.4)], cy=0.6))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    kp = seg(u, up - 0.3, up + 0.1)
    if kp < 1:
        arena(fr, t, a=1 - kp)
    if kp > 0:
        fr2 = fr
        asfalto(fr2, t, xoff=u * 1.5, a=kp)
    M.cristal(fr.base, fr.fx, 'PAVIMENTO', u, t0=up, cy=0.36, entrada='golpe')
    draw_objects(fr, llanta(defl=0.85, giro=-u * 4.0))

    def ui(img, fx):
        kicker(img, 'EL ERROR', 150, seg(u, -0.1, 0.1), col=(255, 140, 130))
        P.titulo_golpe(img, fx, [('El error:', 'sans')], 200, seg(u, 0.0, 0.15), size=90)
        P.titulo_golpe(img, fx, [('salir al pavimento así.', 'serif')], 310, seg(u, up, up + 0.15), size=80)
        esquema(img, fx, 1.0, y=1440)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, 0.15, 0.3), golpe_k(u, up + 0.15, 0.4)), amp=24)


# 13. en el pavimento la llanta baja se dobla en cada vuelta (acercamiento al costado con marco REC; la panza va y viene)
def s_dobla(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 2.4, 30, 8, ty=0.3), K(0.35, 1.5, 70, 4, ty=0.25), K(4, 1.45, 74, 4, ty=0.25)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    asfalto(fr, t, xoff=u * 1.8)
    flex = 0.75 + 0.15 * math.sin(u * 14)
    draw_objects(fr, llanta(defl=flex, giro=-u * 5.0))
    pb = fr.cam.p1((0.0, 0.12, TB + 0.08))
    zl = 1.0 if u < 1.2 else (1.3 if u < 2.2 else 1.8)

    def ui(img, fx):
        kicker(img, 'EL COSTADO SE DOBLA', 150, seg(u, -0.1, 0.2), col=AZULC)
        doodle_circle(img, fx, pb[0], pb[1], 190, 110, t, k=seg(u, 0.3, 0.7), col=ROJO, seed=6)
        n = int(max(0, u) * 14 / (2 * math.pi) * 4) + 1
        texto(img, fx, 540, 1330, f'VUELTA {n:03d}', 56, WHITE, seg(u, 0.2, 0.4), f='mono', glow=0.3)
        rec_frame(img, t, k=1.0, zoom_label=f'x{zl:.1f}')
    fr.ui.append(ui)
    img = finish(fr, fi)
    return M.scale_about(img, zl, 0.5, 0.58) if zl > 1 else img


# 14. se calienta y puede tronar de golpe (se pone roja, termómetro, ondas de calor y ¡pum!; «CALOR» de cristal)
def s_calienta(t, fi, u, d):
    ut = Wu(14, 4) - 0.1                                   # «tronar»
    kc = seg(u, -0.1, ut)
    fr = Frame(cam(u, [K(-0.3, 1.3, 80, 4, ty=0.3), K(0.35, 2.2, 30, 8, ty=0.4), K(ut, 2.0, 20, 8, ty=0.4),
                       K(ut + 0.05, 2.9, 10, 10, ty=0.4), K(5, 3.0, 8, 10, ty=0.4)], cy=0.56))
    space(fr, t, floor=None, bokeh=0.8)
    asfalto(fr, t, xoff=u * 1.8 * (1 - seg(u, ut, ut + 0.3)))
    M.cristal(fr.base, fr.fx, 'CALOR', u, t0=0.0, cy=0.31, entrada='zoom')
    boom = u >= ut
    if not boom:
        draw_objects(fr, llanta(defl=0.8 + 0.1 * math.sin(u * 14), giro=-u * 5.0, calor=kc))
        P.ondas_calor(fr, t, 0.0, ROUT * 2, ROUT * 2 + 0.6, 0.8, k=kc)
    else:
        kb = seg(u, ut, ut + 0.8)
        ms = llanta(defl=1.0, sink=-0.0, giro=0.0, calor=1 - kb)
        trozos = []
        rng = np.random.RandomState(5)
        for j in range(22):
            a = rng.rand() * 2 * math.pi
            v = 1.2 + rng.rand() * 1.4
            p = (math.cos(a) * v * kb, 0.3 + abs(math.sin(a)) * v * kb * 1.2 - 2.0 * kb * kb, (rng.rand() - 0.5) * v * kb + TB)
            c = named(M3.box(0.06, 0.03, 0.08, (28, 28, 30), shadow=0, base=False).tf(rx=kb * 400 * rng.rand(), ry=kb * 300, t=p), 'trozo')
            trozos.append(c)
        draw_objects(fr, ms[1:] + trozos)
    pt = fr.cam.p1((0.0, ROUT, TB))

    def ui(img, fx):
        if not boom:
            P.termometro(img, fx, 900, 1300, 300, 0.2 + 0.75 * kc, f'{int(30 + 55 * kc)} °C', k=seg(u, 0.0, 0.2))
            esquema(img, fx, 1.0, y=1440, txt='ESQUEMA · TEMPERATURA DE EJEMPLO')
        else:
            kb = seg(u, ut, ut + 0.3)
            dd = ImageDraw.Draw(img)
            for j in range(16):
                a = j * 2 * math.pi / 16
                r0, r1 = 120 + 300 * kb, 220 + 520 * kb
                dd.line([(pt[0] + r0 * math.cos(a), pt[1] + r0 * math.sin(a)), (pt[0] + r1 * math.cos(a), pt[1] + r1 * math.sin(a))],
                        fill=M.scale_c(WHITE, 1 - kb * 0.7), width=8)
            P.numero_golpe(img, fx, '¡PUM!', 300, seg(u, ut, ut + 0.15), size=170, col=ROJO)
    fr.ui.append(ui)
    img = finish(fr, fi, flash=1.0 - seg(u, ut, ut + 0.25) if boom else 0.0)
    return sacudir(img, t, golpe_k(u, ut, 0.5), amp=30)


# 15. y hasta se puede zafar del rin y dejarte sin aire de un jalón (vista explotada: el rin se sale y escapa el aire)
def s_zafa(t, fi, u, d):
    uz = Wu(15, 4) - 0.1                                   # «zafar»
    ks = P.eout4(seg(u, uz, uz + 0.5))
    fr = Frame(cam(u, [K(-0.3, 2.4, -60, 14, ty=0.4), K(0.35, 2.3, -30, 10, ty=0.4), K(uz, 2.6, 30, 12, ty=0.4),
                       K(6, 2.7, 38, 12, ty=0.4)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)
    draw_objects(fr, llanta(defl=0.7 + 0.3 * ks, sep=0.45 * ks, giro=0.3))
    pg = fr.cam.p1((0.0, ROUT, TB + 0.1))

    def ui(img, fx):
        kicker(img, 'LA LLANTA SE ZAFA DEL RIN', 150, seg(u, -0.1, 0.2), col=(255, 140, 130))
        if ks > 0.2:
            aire(img, fx, pg[0] + 40, pg[1] - 60, t, k=1 - seg(u, uz + 1.2, uz + 2.0), n=10)
            aire(img, fx, pg[0] - 40, pg[1] + 60, t + 0.3, k=1 - seg(u, uz + 1.2, uz + 2.0), dirx=-1, n=10)
        pill(img, fx, 540, 1330, 'SIN AIRE DE UN JALÓN', eout(seg(u, uz + 0.6, uz + 0.9)), size=30, border=ROJO, dot=False)
        esquema(img, fx, 1.0, y=1420)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uz + 0.1, 0.4), amp=22)


# 16. por eso, con rines que la amarran (rin de amarre: los pernos entran uno por uno)
def s_amarre(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 1.2, 10, 6, ty=0.45, tz=0.1), K(0.35, 1.6, 30, 8, ty=0.48, tz=0.1), K(4, 1.65, 34, 8, ty=0.48, tz=0.1)],
                   cy=0.52))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    draw_objects(fr, llanta(defl=0.7, amarre=seg(u, 0.0, 1.2), giro=0.0))
    pc = fr.cam.p1((0, ROUT - 0.1, TB + 0.25))

    def ui(img, fx):
        kicker(img, 'RIN DE AMARRE (BEADLOCK)', 150, seg(u, -0.1, 0.2), col=AZULC)
        doodle_circle(img, fx, pc[0], pc[1], 300, 300, t, k=seg(u, 1.0, 1.4), col=AMARILLO, seed=8)
        pill(img, fx, 540, 1330, 'PRENSA LA LLANTA AL RIN', eout(seg(u, 0.8, 1.1)), size=30, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 17. hay guías que la bajan a 6 u 8 libras en la duna (manómetro; «6-8 LB» de cristal)
def s_libras(t, fi, u, d):
    ul = Wu(17, 5) - 0.1                                   # «seis u ocho»
    fr = Frame(cam(u, [K(-0.3, 3.6, -30, 20, ty=0.4), K(0.35, 3.1, -8, 12, ty=0.4), K(4, 3.05, -4, 12, ty=0.4)], cy=0.62))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    arena(fr, t, a=0.7)
    M.cristal(fr.base, fr.fx, '6-8 LB', u, t0=ul, cy=0.6, entrada='golpe')
    psi = 20 - 13 * P.eout4(seg(u, 0.0, ul + 0.3))

    def ui(img, fx):
        kicker(img, 'UNA GUÍA DE MANEJO EN DUNAS', 150, seg(u, -0.1, 0.2), col=AZULC)
        manometro(img, fx, 540, 640, 300, psi, k=seg(u, -0.25, 0.05), zona=(6, 8) if u > ul else None)
        pill(img, fx, 540, 1460, 'SOLO CON RINES DE AMARRE · EN LA ARENA', eout(seg(u, ul + 0.4, ul + 0.7)), size=24, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ul + 0.2, 0.3), amp=14)


# 18. y antes de salir al camino, se vuelve a inflar (compresor: la llanta se redondea y el manómetro sube)
def s_inflar(t, fi, u, d):
    ui_ = Wu(18, 9) - 0.1                                  # «inflar»
    ki = P.eout4(seg(u, ui_ - 0.4, ui_ + 1.2))
    fr = Frame(cam(u, [K(-0.3, 2.0, 70, 10, ty=0.45), K(0.35, 2.5, 30, 8, ty=0.45), K(5, 2.55, 24, 8, ty=0.45)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    draw_objects(fr, llanta(defl=0.85 * (1 - ki), giro=0.3))
    pv = fr.cam.p1((0.17, ROUT + 0.17, TB + 0.05))
    line3(fr, [(0.17, ROUT + 0.17, TB + 0.05), (0.6, 1.2, 0.6), (1.4, 1.4, 0.2)], col=(200, 60, 50), w=5, a=seg(u, -0.1, 0.2), glow=0.2)

    def ui(img, fx):
        kicker(img, 'ANTES DE SALIR AL CAMINO', 150, seg(u, -0.1, 0.2), col=AZULC)
        manometro(img, fx, 830, 1220, 140, 7 + 15 * ki, k=seg(u, 0.0, 0.3))
        if 0.05 < ki < 0.98:
            aire(img, fx, pv[0] + 140, pv[1] - 30, t, k=1.0, dirx=-1, n=5, col=CYAN)
        pill(img, fx, 360, 1330, 'PRESIÓN DEL MANUAL', eout(seg(u, ui_ + 0.8, ui_ + 1.1)), size=28, border=VERDE, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19. mándaselo a tu compa que siempre se atasca en la duna (el side by side real enterrado hasta las llantas)
def s_compa(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 5.0, 30, 16, ty=0.3), K(0.35, 5.4, 6, 12, ty=0.3), K(5, 5.4, 2, 12, ty=0.3)], cy=0.56))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    arena(fr, t, a=0.9)
    e = P.entrada(u, -0.25, 0.3, 'desliza')

    def ui(img, fx):
        piso = 1320
        r = veh(img, fx, 540 + e['dy'] * 200, piso + 70, 540, yaw=0.4, pitch=0.15, t=t, sombra=0.0)
        # arena que tapa las llantas
        lay = Image.new('L', img.size, 0)
        dl = ImageDraw.Draw(lay)
        pts = [(0, 1920), (0, piso - 40)]
        for x in range(0, 1081, 30):
            pts.append((x, piso - 40 - 70 * math.exp(-((x - 540 - e['dy'] * 200) / 330) ** 2) + 10 * math.sin(x * 0.03)))
        pts += [(1080, 1920)]
        dl.polygon(pts, fill=235)
        lay = lay.filter(ImageFilter.GaussianBlur(3))
        img.paste(Image.new('RGB', img.size, (92, 74, 52)), (0, 0), lay)
        dd = ImageDraw.Draw(img)
        dd.line(pts[2:-1], fill=ARENA, width=3)
        P.titulo_golpe(img, fx, [('Mándaselo a tu compa', 'sans'), ('que siempre se atasca.', 'serif')], 210, seg(u, 0.05, 0.2), size=74)
        credito(img)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[(-0.25, 'whoosh', 0.5), (UC, 'sub', 1.0), (UC, 'thud', 1.0)]),
           dict(desde=1, fn=s_ponchada, tr='iris', c=(0.5, 0.55), sfx=[(0.2, 'click', 0.6), (0.6, 'scribble', 0.6)]),
           dict(desde=2, fn=s_samalayuca, tr='deslizar', sfx=[(0.4, 'shimmer', 0.4), (1.4, 'whoosh_suave', 0.6)]),
           dict(desde=3, fn=s_prueba, tr='cubo', sfx=[(0.05, 'thud', 0.7), (0.3, 'thud', 0.7)]),
           dict(desde=4, fn=s_inflada, tr='whip', sfx=[(0.3, 'scribble', 0.5), (0.9, 'tick', 0.5)]),
           dict(desde=5, fn=s_entierra, tr='golpe', c=(0.5, 0.5), sfx=[(1.6, 'sub', 0.8), (1.7, 'burst', 0.4)]),
           dict(desde=6, fn=s_aplasta, tr='remolino', sfx=[(0.1, 'whoosh_suave', 0.7), (0.9, 'thud', 0.5)]),
           dict(desde=7, fn=s_huella, tr='deslizar_abajo', sfx=[(1.0, 'chime_a', 0.4), (1.6, 'chime_b', 0.4)]),
           dict(desde=8, fn=s_peso, tr='rebanadas', c=(0.5, 0.62), sfx=[(0.1, 'bass', 0.6)] + [(0.45 + 0.07 * j, 'tick2', 0.25) for j in range(8)]),
           dict(desde=9, fn=s_flota, tr='zoom', sfx=[(0.3, 'riser', 0.3), (1.2, 'chime_c', 0.4)]),
           dict(desde=10, fn=s_zapato, tr='flash', sfx=[(0.1, 'thud', 0.6), (1.6, 'sub', 0.6)]),
           dict(desde=11, fn=s_raqueta, tr='cubo_izq', sfx=[(0.2, 'thud', 0.5), (0.5, 'chime_a', 0.4)]),
           dict(desde=12, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(2.3, 'bass', 0.8)]),
           dict(desde=13, fn=s_dobla, tr='deslizar_abajo', c=(0.5, 0.6), sfx=[(1.2, 'click', 0.7), (2.2, 'click', 0.7), (0.4, 'scribble', 0.5)]),
           dict(desde=14, fn=s_calienta, tr='push', sfx=[(0.1, 'riser', 0.6), (1.45, 'burst', 1.0), (1.45, 'sub', 1.0)]),
           dict(desde=15, fn=s_zafa, tr='glitch', sfx=[(0.9, 'whoosh', 0.8), (1.0, 'burst', 0.5)]),
           dict(desde=16, fn=s_amarre, tr='cristal', palabra='AMARRE', sfx=[(0.08 * j, 'click', 0.3) for j in range(16)]),
           dict(desde=17, fn=s_libras, tr='mosaico', sfx=[(0.2, 'tick', 0.4), (1.6, 'bass', 0.7)]),
           dict(desde=18, fn=s_inflar, tr='wipe', sfx=[(1.6, 'whoosh_suave', 0.6), (3.0, 'chime_c', 0.5)]),
           dict(desde=19, fn=s_compa, tr='whip_izq', sfx=[(0.2, 'bass', 0.7)]),
           dict(desde=20, loop=True, tr='ritmo')]

if __name__ == '__main__':
    montaje.cli(globals())
