"""Reel diario: «Tu dedo se arruga… a propósito.» Mar 10-nov-2026, 18:00. Voz Isaac. Estilo rápido.
Inicio tipo 9 (giro 360° con destellos: la yema arrugada da una vuelta completa con 3 cortes rítmicos y queda de frente al
título, con «PROPÓSITO» de cristal gigante detrás). Datos: las arrugas en el agua son una reacción del sistema nervioso
autónomo: vasoconstricción de los vasos de la yema por activación simpática (Nature News 2013; Grinbaum et al., Sci Rep
2022, que cita a Wilder-Smith y Chow 2003); aparecen entre 5 y 30 min en agua tibia en personas sanas (Sci Rep 2022); la
piel con el nervio cortado no se arruga (O'Riain 1973) y se sabe desde los años 1930 (Nature 2013); «prueba de arrugas»
de los médicos para revisar el nervio digital (Sci Rep 2022); Kareklas, Nettle y Smulders (Biology Letters, 2013,
Universidad de Newcastle, Inglaterra): con dedos arrugados pasaron más rápido canicas mojadas; con secas, sin diferencia;
analogía del dibujo de las llantas (Nature 2013). Dedo, canicas, llanta y regadera: RECREACIÓN (sin personas).
Fuentes en guiones/2026-11-10_dedo.txt."""
import math, os, re, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)

M3 = M.M3
S = M.SS
TEMA = 'dedo'
TXT = ['Tu dedo se arruga… a propósito.',
       'Parece piel inflada de agua, pero es una orden de tu sistema nervioso.',
       'Desde unos 5 minutos en agua tibia, tus nervios aprietan los vasitos de sangre de la yema.',
       'La yema se desinfla un poquito y la piel de encima se dobla en surcos.',
       '¿Para qué? En 2013, en Inglaterra, pusieron a gente a pasar canicas mojadas.',
       'Con los dedos arrugados fueron más rápidos; con canicas secas, no hubo diferencia.',
       'Y aquí viene lo más raro: hay dedos que ya no se arrugan.',
       'Si el nervio de un dedo se corta en un accidente, ese dedo se queda liso en el agua.',
       'Se sabe desde los años 30, y los médicos lo usan como prueba de nervios.',
       'Dedo con nervio sano: surcos. Nervio cortado: liso, como si nada.',
       'Y esos surcos funcionan como el dibujo de una llanta: abren canales para que se vaya el agua.',
       'O sea, cada arruga es tu cuerpo preparándote para agarrar mejor.',
       'Mándaselo a quien se tarda horas en la regadera.',
       'Porque cuando sale, su dedo se arruga… a propósito.']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-10_dedo_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)

PIEL = (222, 168, 134)
PIEL_ARR = (206, 150, 122)
SURCO = (120, 72, 56)
UNA = (246, 214, 206)
SANGRE = (230, 45, 55)
NERVIO = (255, 214, 90)
AGUA_C = (90, 170, 230)
AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 60, 50)
CANICAS = [(70, 160, 235), (240, 120, 60), (90, 210, 140), (230, 80, 120), (250, 210, 80)]


# ================================================================== utilidades
def _pal(i):
    return re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split()


def TT(i):
    return montaje.CTX['T'][i][0]


def TE(i):
    return montaje.CTX['T'][i][1]


_W = []


def _words():
    if not _W:
        f = f'/home/claude/words_{TEMA}.json'
        if os.path.exists(f):
            d = json.load(open(f))
            d = d.get('words', d) if isinstance(d, dict) else d
            _W.extend(w for w in d if w.get('type', 'word') == 'word' and not w['text'].startswith('['))
    return _W


def wt(i, k):
    """Segundos desde el inicio de la frase i hasta su palabra k."""
    n = len(_pal(i))
    k = max(0, min(k, n - 1))
    W_ = _words()
    if len(W_) == sum(len(_pal(j)) for j in range(len(VOZ))):
        n0 = sum(len(_pal(j)) for j in range(i))
        return W_[n0 + k]['start'] - W_[n0]['start']
    return (TE(i) - TT(i)) * k / n


def cam(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch=8, tx=0.0, ty=0.0, tz=0.0, roll=0.0):
    return (u, dict(tx=tx, ty=ty, tz=tz, dist=dist, yaw=yaw, pitch=pitch, roll=roll))


def golpe_k(u, u0, dur=0.35):
    if u < u0 or u > u0 + dur:
        return 0.0
    return (1 - (u - u0) / dur) ** 2


def sacudir(img, t, k, amp=20):
    if k <= 0.01:
        return img
    dx, dy = P.sacudida(t, k=k, amp=amp)
    return P.mover_img(img, dx, dy)


def check(img, fx, x, y, k, txt, col=VERDE):
    pill(img, fx, x, y, '✓ ' + txt, eout(k), size=36, border=col)


def tache(img, fx, x, y, k, txt):
    pill(img, fx, x, y, '✗ ' + txt, eout(k), size=36, border=ROJO, col=(255, 200, 196))


def texto(img, fx, x, y, txt, size, col, k=1.0, glow=0.45, f='sansx', anchor='mm'):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, k), anchor=anchor)
    ImageDraw.Draw(fx).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, glow * k), anchor=anchor)


def dibujar(fr, ms):
    """draw_objects + tapa en la capa que brilla lo que queda detrás de los objetos (para que nada brille a través)."""
    draw_objects(fr, ms)
    caras = M._faces(fr.cam, ms)
    for z, mi, fi_, n, vd, Sx in caras:
        if getattr(ms[mi], 'glow', None) is None:
            fr.df.polygon([tuple(p) for p in Sx], fill=(0, 0, 0))
    for z, mi, fi_, n, vd, Sx in caras:
        g = getattr(ms[mi], 'glow', None)
        if g is not None:
            fr.df.polygon([tuple(p) for p in Sx], fill=g)


def xf(p, s=1.0, ry=0.0, t=(0, 0, 0), base=True):
    """Transforma un punto igual que dedo() (escala, giro en y con el giro base BY, traslación)."""
    return (np.asarray(p, float) * s) @ M3.rotm(0, ry + (BY if base else 0.0), 0).T + np.asarray(t, float)


# ================================================================== objetos (RECREACIÓN, sin personas)
YT = 1.54           # centro de la punta del dedo (yema)
BY = -38.0          # giro base: la yema mira al frente-izquierda y la uña asoma a la derecha (se lee como dedo)
RT = 0.18           # radio de la falange de la punta


def _media_esfera(m, y0):
    """Deja solo la mitad de arriba de una esfera (la de abajo queda dentro del cilindro y ensuciaba el orden de dibujo)."""
    keep = [i for i, f in enumerate(m.F) if m.V[list(f)][:, 1].mean() >= y0 - 0.005]
    m.F = [m.F[i] for i in keep]
    m.C = [m.C[i] for i in keep]
    return m


def _una():
    """Uña curva pegada al dorso de la punta (un pedazo de cilindro un poco más grande que el dedo)."""
    m = M3.cyl(RT + 0.005, 0.34, UNA, n=36, shadow=0, gloss=0.6, y0=1.24)
    keep = [i for i, f in enumerate(m.F) if len(f) == 4 and m.V[list(f)][:, 2].mean() < -0.12]
    m.F = [m.F[i] for i in keep]
    m.C = [m.C[i] for i in keep]
    m.double = True
    return named(m, 'una', rim=0.6, gloss=0.85)


def _pliegues():
    """Pliegues del dorso en los nudillos (arcos oscuros solo atrás): ayudan a que se lea como dedo."""
    out = []
    for yc, r in ((0.63, 0.207), (1.15, 0.193)):
        for dy in (-0.035, 0.0, 0.035):
            m = M3.torus(r, 0.007, (150, 98, 80), nu=36, nv=4, gloss=0.1).tf(t=(0, yc + dy, 0))
            keep = [i for i, f in enumerate(m.F) if m.V[list(f)][:, 2].mean() < -0.08]
            m.F = [m.F[i] for i in keep]
            m.C = [m.C[i] for i in keep] if isinstance(m.C, list) else m.C
            m.flat = True
            out.append(named(m, 'pliegue'))
    return out


def dedo(t=(0, 0, 0), s=1.0, ry=0.0, arr=0.0, col=None):
    """Dedo índice de pie (la yema mira a +z, la uña a −z): 3 falanges, nudillos, punta redondeada y uña."""
    c = col or M.mixc(PIEL, PIEL_ARR, arr)
    kw = dict(shadow=0, gloss=0.28)
    ms = [named(M3.cyl(0.205, 0.62, c, n=28, **kw), 'dedo', rim=0.55, gloss=0.28),
          named(M3.sphere(0.205, c, nu=28, nv=12, **kw).tf(s=(1, 0.5, 1), t=(0, 0.63, 0)), 'dedo', rim=0.55, gloss=0.28),
          named(M3.cyl(0.19, 0.5, c, n=28, y0=0.64, **kw), 'dedo', rim=0.55, gloss=0.28),
          named(M3.sphere(0.19, c, nu=28, nv=12, **kw).tf(s=(1, 0.45, 1), t=(0, 1.15, 0)), 'dedo', rim=0.55, gloss=0.28),
          named(M3.cyl(RT, 0.38, c, n=28, y0=1.16, **kw), 'dedo', rim=0.55, gloss=0.28),
          named(_media_esfera(M3.sphere(RT, c, nu=28, nv=14, **kw).tf(s=(1, 1.15, 1), t=(0, YT, 0)), YT), 'dedo', rim=0.55,
                gloss=0.28),
          _una()] + _pliegues()
    return P.tfk(ms, s=s, ry=ry + BY, t=t)


def arrugas(fr, t, k, pos=(0, 0, 0), s=1.0, ry=0.0, n=9):
    """Surcos de la yema (line-art en la piel): curvas a lo largo del dedo que se ondulan con k."""
    if k <= 0.01:
        return
    camp = fr.cam.pos
    for i in range(n):
        th0 = math.radians(-72 + 144 * i / (n - 1))
        pts, vis = [], []
        for y in np.linspace(1.18, YT + RT * 1.1, 22):
            r = RT if y <= YT else RT * math.sqrt(max(0.0, 1 - ((y - YT) / (RT * 1.15)) ** 2))
            th = th0 + k * 0.09 * math.sin(y * 38 + i * 1.3)
            p_loc = np.array([r * 1.01 * math.sin(th), y, r * 1.01 * math.cos(th)])
            p = xf(p_loc, s, ry, pos)
            nrm = xf(np.array([math.sin(th), 0, math.cos(th)]), 1.0, ry, (0, 0, 0))
            pts.append(p)
            vis.append(float(nrm @ (camp - p)) > 0.02)
        run = []
        for p, v in zip(pts, vis):
            if v:
                run.append(p)
            elif len(run) > 1:
                line3(fr, run, col=SURCO, w=3.2 * s, a=0.95 * k, glow=0.0)
                run = []
            else:
                run = []
        if len(run) > 1:
            line3(fr, run, col=SURCO, w=3.2 * s, a=0.95 * k, glow=0.0)
            line3(fr, [q + np.array([0.012 * s, 0.006 * s, 0.004]) for q in run], col=(255, 225, 205), w=1.6 * s, a=0.55 * k, glow=0.15)


def gotas(fr, t, pos=(0, 0, 0), s=1.0, k=1.0, n=3):
    """Gotas que escurren de la punta y caen."""
    if k <= 0.01:
        return
    for j in range(n):
        ph = (t * 0.9 + j / n) % 1.0
        p = xf((0.02 * math.sin(j * 2.1), YT + 0.05 - 1.6 * ph ** 2, 0.2), s, 0, pos)
        dot3(fr, p, r=5 * s, col=(170, 220, 255), a=k * (1 - ph), glow=1.0)


def agua_debajo(img, y, k=1.0, t=0.0, tibia=False):
    """Superficie del agua en pantalla (línea cian ondulada) y tinte azul debajo (2D, sobre el cuadro terminado)."""
    if k <= 0.01:
        return img
    a = np.asarray(img, np.float32)
    yy = int(clamp(y, 0, M.H))
    tint = np.array(AGUA_C if not tibia else (110, 170, 210), np.float32)
    a[yy:] = a[yy:] * (1 - 0.32 * k) + tint * 0.22 * k
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for j in range(2):
        pts = [(x, y + 8 * math.sin(x / 60 + t * 4 + j * 2) + 10 * j) for x in range(0, M.W + 20, 20)]
        d.line(pts, fill=M.scale_c(CYAN, k * (0.95 - 0.4 * j)), width=5 - 2 * j)
    return np.asarray(im)


def vasos(fr, t, k_cierra, pos=(0, 0, 0), s=1.0, ry=0.0, a=1.0):
    """Vasitos de sangre de la yema (rojos que brillan) que se aprietan con k_cierra."""
    if a <= 0.01:
        return
    w = (7 - 4.8 * k_cierra) * s
    col = M.mixc(SANGRE, (150, 30, 40), k_cierra)
    for j, (x0, z0) in enumerate(((-0.08, 0.06), (0.0, 0.1), (0.08, 0.05), (-0.04, -0.02), (0.05, -0.03))):
        pts = [xf((x0 + 0.03 * math.sin(y * 16 + j), y, z0 + 0.02 * math.cos(y * 12 + j)), s, ry, pos) for y in np.linspace(1.0, YT + 0.1, 16)]
        line3(fr, pts, col=col, w=w, a=a, glow=1.0 * (1 - 0.5 * k_cierra))
    for j in range(5):  # flujo de sangre (puntitos que corren por los vasos)
        ph = (t * (1.4 - 1.0 * k_cierra) + j / 5) % 1.0
        dot3(fr, xf((-0.04 + 0.04 * (j % 3), 1.0 + 0.6 * ph, 0.06), s, ry, pos), r=4 * s, col=(255, 140, 140), a=a * (1 - k_cierra * 0.7),
             glow=1.0)


def nervio(fr, t, pos=(0, 0, 0), s=1.0, ry=0.0, k=1.0, corte=None, pulsos=1.0, y0=-0.4):
    """Nervio del dedo (amarillo que brilla) con pulsos que suben. corte = altura donde está cortado."""
    if k <= 0.01:
        return
    def pt(y):
        return xf((0.1 + 0.015 * math.sin(y * 7), y, 0.09), s, ry, pos)
    ys = np.linspace(y0, YT + 0.08, 40)
    if corte is None:
        line3(fr, [pt(y) for y in ys], col=NERVIO, w=4.5 * s, a=k, glow=1.0)
    else:
        line3(fr, [pt(y) for y in ys if y < corte - 0.06], col=NERVIO, w=4.5 * s, a=k, glow=1.0)
        line3(fr, [pt(y) for y in ys if y > corte + 0.06], col=M.scale_c(NERVIO, 0.45), w=4.5 * s, a=k, glow=0.2)
    for j in range(4):
        ph = (t * 1.3 + j / 4) % 1.0
        y = y0 + (YT + 0.08 - y0) * ph
        if corte is not None and y > corte - 0.06:
            continue
        dot3(fr, pt(y), r=6 * s, col=(255, 250, 200), a=k * pulsos, glow=1.4)


def canica(p, r=0.1, col=CANICAS[0]):
    return [named(M3.sphere(r, col, nu=16, nv=10, shadow=0, gloss=0.95).tf(t=p), 'canica', rim=0.9, gloss=0.95)]


def charola(x, y, z=0.0, w=0.7):
    return [named(M3.rbox(w, 0.12, 0.5, 0.06, (40, 42, 48), n=3, shadow=0, gloss=0.4).tf(t=(x, y, z)), 'charola', rim=0.6)]


def llanta(t=(0, 0, 0), s=1.0, giro=0.0):
    """Llanta de pie (eje en x) que rueda: hule negro con rin plateado."""
    ms = [named(M3.torus(0.62, 0.26, (34, 34, 38), nu=40, nv=14, gloss=0.25).tf(rz=90, rx=giro), 'llanta', rim=0.5, gloss=0.25),
          named(M3.cyl(0.42, 0.3, (170, 174, 182), n=28, shadow=0, gloss=0.8, y0=-0.15).tf(rz=90, rx=giro), 'rin', rim=0.7, gloss=0.8)]
    return P.tfk(ms, s=s, t=t)


def surcos_llanta(fr, t, giro, pos=(0, 0, 0), s=1.0, k=1.0):
    """Dibujo de la llanta (line-art) que gira con ella."""
    if k <= 0.01:
        return
    cx, cy, cz = pos
    camp = fr.cam.pos
    for j in range(28):
        a = math.radians(giro) + j * 2 * math.pi / 28
        R = 0.62 + 0.26
        p_c = np.array([cx, cy + R * math.sin(a) * s, cz + R * math.cos(a) * s])
        nrm = np.array([0, math.sin(a), math.cos(a)])
        if float(nrm @ (camp - p_c)) <= 0:
            continue
        pts = [np.array([cx + x * s, cy + R * math.sin(a + 0.08 * (x / 0.22)) * s, cz + R * math.cos(a + 0.08 * (x / 0.22)) * s])
               for x in np.linspace(-0.22, 0.22, 6)]
        line3(fr, pts, col=(110, 110, 120), w=3 * s, a=k, glow=0.1)


def regadera(t=(0, 0, 0), s=1.0):
    ms = [named(M3.cyl(0.32, 0.08, (190, 194, 200), n=30, shadow=0, gloss=0.9), 'regadera', rim=0.8, gloss=0.9),
          named(M3.cyl(0.06, 0.6, (190, 194, 200), n=12, shadow=0, gloss=0.9, y0=0.08), 'tubo', rim=0.8, gloss=0.9)]
    return P.tfk(ms, s=s, t=t)


def chorros(fr, t, pos=(0, 0, 0), s=1.0, k=1.0, h=2.2):
    if k <= 0.01:
        return
    cx, cy, cz = pos
    for j in range(14):
        a = j * 2.4
        r = 0.25 * math.sqrt((j % 7) / 7 + 0.1)
        x, z = cx + r * math.cos(a) * s, cz + r * math.sin(a) * s
        for q in range(3):
            ph = (t * 2.2 + j * 0.13 + q / 3) % 1.0
            y = cy - h * ph * s
            line3(fr, [(x, y, z), (x, y - 0.18 * s, z)], col=(170, 215, 255), w=2.5 * s, a=0.8 * k, glow=0.8)


def _pant_chat(k_env, t):
    def dib(d, im):
        w, h = im.size
        d.rectangle((0, 70, w, 150), fill=(18, 20, 26))
        d.ellipse((24, 88, 72, 136), fill=(120, 80, 150))
        d.text((88, 96), 'Hermano', font=M.font('sanss', 30), fill=(240, 240, 242))
        d.text((88, 128), 'en la regadera…', font=M.font('sansm', 18), fill=(150, 200, 160))
        y0 = 200
        d.rounded_rectangle((120, y0, w - 24, y0 + 330), radius=22, fill=(26, 60, 50))
        d.rounded_rectangle((136, y0 + 16, w - 40, y0 + 250), radius=14, fill=(8, 8, 10))
        cx, cy = (136 + w - 40) / 2, y0 + 140
        d.rounded_rectangle((cx - 22, cy - 70, cx + 22, cy + 90), radius=22, fill=PIEL)
        for i in range(5):
            yy = cy - 50 + 14 * i
            d.arc((cx - 18, yy - 6, cx + 18, yy + 6), 0, 180, fill=SURCO, width=3)
        d.polygon([(cx + 46, y0 + 110), (cx + 46, y0 + 150), (cx + 78, y0 + 130)], fill=(240, 240, 240))
        d.text((140, y0 + 266), 'Tu dedo se arruga… a propósito', font=M.font('sanss', 20), fill=(235, 240, 236))
        d.text((w - 40, y0 + 302), '18:00 ✓✓', font=M.font('sansm', 18), fill=(130, 200, 255), anchor='ra')
        if k_env > 0.01:
            y1 = y0 + 360
            d.rounded_rectangle((60, y1, w - 24, y1 + 90), radius=20, fill=(26, 60, 50))
            d.text((80, y1 + 24), '¡Ya sal, llevas 1 hora!', font=M.font('sanss', 28), fill=(240, 242, 240))
        d.rounded_rectangle((24, h - 120, w - 110, h - 62), radius=28, fill=(30, 32, 38))
        d.ellipse((w - 96, h - 124, w - 30, h - 58), fill=(40, 170, 110))
        d.polygon([(w - 76, h - 108), (w - 76, h - 74), (w - 46, h - 91)], fill=(255, 255, 255))
    return P.pantalla(dib)


# ================================================================== escenas
# 0. gancho, inicio tipo 9: la yema arrugada da una vuelta de 360° en 0.55 s con 3 cortes de destello y queda de frente;
#    el título cae con golpe. En el loop (u < 0) el dedo se mece de frente, ya arrugado y escurriendo.
UG = 0.55


def s_gancho(t, fi, u, d):
    giro = 360 * P.eout4(seg(u, 0.0, UG)) if u >= 0 else 8 * math.sin(u * 1.7)
    fr = Frame(cam(u, [K(-4.0, 2.6, -14, 6, ty=1.2), K(-1.0, 2.15, 0, 4, ty=1.25), K(UG, 2.15, 0, 4, ty=1.25),
                       K(UG + 0.05, 1.8, 6, 6, ty=1.3), K(3.4, 1.75, 8, 6, ty=1.3)], cy=0.6))
    space(fr, t, floor=None, bokeh=1.2, beam=0.55)
    M.cristal(fr.base, fr.fx, 'PROPÓSITO', u, t0=-3.6, cy=0.36, alto=0.26, entrada='golpe')
    dibujar(fr, dedo(ry=giro, arr=1.0))
    arrugas(fr, t, 1.0, ry=giro)
    gotas(fr, t, k=1.0)

    def ui(img, fx):
        kicker(img, 'YEMA DEL DEDO · 30 MIN EN AGUA TIBIA', 112, 1.0, col=(150, 210, 230))
        P.titulo_golpe(img, fx, [('Tu dedo se arruga…', 'sans'), ('a propósito.', 'serif')], 170, seg(u, UG, UG + 0.15), size=78)
    fr.ui.append(ui)
    out = finish(fr, fi)
    for uc in (0.1, 0.24, 0.38):                     # 3 cortes rítmicos con destello
        if uc <= u < uc + 0.07:
            out = (out.astype(np.float32) + 120).clip(0, 255).astype(np.uint8)
    if u >= UG:
        out = (out.astype(np.float32) + 100 * golpe_k(u, UG + 0.12, 0.16)).clip(0, 255).astype(np.uint8)
    return sacudir(out, t, golpe_k(u, UG + 0.12, 0.4), amp=24)


# 1. ¿piel inflada? (flechitas de agua que entran: ✗) → es una orden del sistema nervioso (rayos X y pulsos en el nervio).
def s_orden(t, fi, u, d):
    up, uo = wt(1, 5) - 0.12, wt(1, 8) - 0.15
    if u < uo:
        fr = Frame(cam(u, [K(-0.3, 2.6, 40, 8, ty=1.3), K(0.25, 2.0, 18, 6, ty=1.35), K(up, 2.0, 18, 6, ty=1.35),
                           K(up + 0.05, 1.7, -10, 6, ty=1.4), K(3.0, 1.65, -12, 6, ty=1.4)], cy=0.55))
        space(fr, t, floor=None, bokeh=1.0)
        dibujar(fr, dedo(arr=0.6))
        arrugas(fr, t, 0.6)
        for j in range(6):  # el «agua que entra» (la idea equivocada)
            a = -1.0 + j * 0.4
            ph = (t * 1.5 + j * 0.2) % 1.0
            p1 = np.array([0.55 * math.sin(a), YT - 0.1 + 0.15 * math.cos(j), 0.55 * math.cos(a)])
            p0 = p1 * (1 + 0.5 * (1 - ph))
            line3(fr, [p0, p0 + (p1 - p0) * 0.6], col=AGUA_C, w=4, a=0.8 * (1 - seg(u, up, up + 0.3)), glow=0.8)

        def ui(img, fx):
            pill(img, fx, 540, 330, '¿PIEL INFLADA DE AGUA?', eout(seg(u, 0.0, 0.25)), size=36, border=AGUA_C)
            tache(img, fx, 540, 1380, seg(u, up, up + 0.25), 'NO ES AGUA')
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.1, 0.3), amp=14)
    v = u - uo
    fr = Frame(cam(v, [K(-0.1, 3.4, -30, 8, ty=0.8), K(0.3, 3.0, -6, 6, ty=0.8), K(3.0, 2.95, -2, 6, ty=0.8)], cy=0.56))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'NERVIOS', v, t0=0.0, cy=0.33, alto=0.3, entrada='sube')
    draw_objects(fr, dedo(arr=0.6), xray=seg(v, 0.0, 0.3))
    nervio(fr, t, k=seg(v, 0.1, 0.4))

    def ui(img, fx):
        pill(img, fx, 540, 1390, 'ORDEN DEL SISTEMA NERVIOSO', eout(seg(v, 0.3, 0.55)), size=32, border=NERVIO)
    fr.ui.append(ui)
    return finish(fr, fi)


# 2. el dedo entra al agua tibia (≈5 min) → rayos X de la yema: los vasitos de sangre se aprietan (zoom digital REC).
def s_vasos(t, fi, u, d):
    ua = wt(2, 8) - 0.15
    if u < ua:
        dip = P.eout4(seg(u, 0.0, 0.5))
        fr = Frame(cam(u, [K(-0.3, 3.0, -20, 10, ty=1.15), K(0.2, 2.6, 6, 8, ty=1.15), K(3.0, 2.55, 10, 8, ty=1.15)], cy=0.5))
        space(fr, t, floor=None, bokeh=1.0)
        pos = (0, 0.25 - 0.85 * dip, 0)
        dibujar(fr, dedo(t=pos, arr=0.2))
        ysurf = fr.cam.p1((0, 1.3, 0))[1]
        out = agua_debajo(finish(fr, fi), ysurf, k=1.0, t=t, tibia=True)
        im = Image.fromarray(out)
        fx = Image.new('RGB', im.size)
        mins = 5 * P.eout4(seg(u, 0.3, wt(2, 3)))
        cx, cy, R = 820, 420, 105
        dd = ImageDraw.Draw(im)
        dd.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(230, 232, 238), width=6)
        dd.arc((cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14), -90, -90 + 72 * mins, fill=AMARILLO, width=12)
        texto(im, fx, cx, cy, f'{mins:.0f} min', 44, WHITE, f='mono')
        pill(im, fx, 330, 420, 'AGUA TIBIA', eout(seg(u, wt(2, 5) - 0.1, wt(2, 5) + 0.15)), size=32, border=(255, 170, 120))
        for j in range(4):  # vapor tibio
            x0 = 240 + 200 * j
            pts = [(x0 + 12 * math.sin(t * 3 + q * 0.05 + j), ysurf - 30 - q * 1.6) for q in range(0, 160, 8)]
            dd.line(pts, fill=(200, 205, 215), width=3)
        return sacudir(np.asarray(im), t, golpe_k(u, 0.45, 0.25), amp=10)
    v = u - ua
    kc = P.eout4(seg(v, 0.25, 1.4))
    zoom = 1.0 if v < 0.9 else 2.0
    fr = Frame(cam(v, [K(-0.1, 1.5, 20, 6, ty=1.35), K(0.3, 1.2, 0, 4, ty=1.4), K(0.9, 1.2, 0, 4, ty=1.4), K(0.95, 0.85, -6, 4, ty=1.45),
                       K(4.0, 0.82, -8, 4, ty=1.45)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    draw_objects(fr, dedo(), xray=1.0)
    vasos(fr, t, kc)
    nervio(fr, t, k=0.7)

    def ui(img, fx):
        rec_frame(img, t, 1.0, zoom_label=f'x{zoom:.1f}')
        pill(img, fx, 540, 1390, 'LOS VASITOS SE APRIETAN', eout(seg(v, 0.3, 0.55)), size=34, border=SANGRE)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if 0.9 <= v < 1.0:
        out = (out.astype(np.float32) + 70).clip(0, 255).astype(np.uint8)
    return out


# 3. corte de la yema (line-art): el cojín se desinfla y la piel de encima se dobla en surcos («SURCOS» de cristal);
#    luego la cámara sale a la yema que ya tiene surcos.
def s_surcos(t, fi, u, d):
    ud, us = wt(3, 3) - 0.1, wt(3, 12) - 0.12
    uo = wt(3, 14) + 0.25
    if u < uo:
        kd = P.eout4(seg(u, ud, ud + 1.2))
        fr = Frame(cam(u, [K(-0.3, 4.4, 30, 18, ty=0.6), K(0.3, 3.7, 10, 14, ty=0.6), K(us, 3.7, 10, 14, ty=0.6),
                           K(us + 0.1, 3.2, -14, 16, ty=0.6), K(4.0, 3.1, -16, 16, ty=0.6)], cy=0.56))
        space(fr, t, floor=None, bokeh=1.0)
        M.cristal(fr.base, fr.fx, 'SURCOS', u, t0=us, cy=0.3, alto=0.28, entrada='zoom')
        L = 1.6
        for zi, z in enumerate((0.0, -0.4, -0.8)):
            xs = np.linspace(-L, L, 90)
            # el cojín baja (se desinfla) y la piel conserva su largo → se dobla en surcos
            top = [(x, 0.95 * (1 - (x / L) ** 2) ** 0.6 * (1 - 0.3 * kd) + 0.09 * kd * math.sin(x * 11 + zi * 0.3), z) for x in xs]
            base = [(x, 0.0, z) for x in xs]
            if zi == 0:
                sc, _ = fr.cam.proj(top + base[::-1])
                fr.db.polygon([tuple(p) for p in sc], fill=(92, 58, 48))
                for j, x0 in enumerate((-0.9, -0.3, 0.3, 0.9)):
                    rr = 0.13 * (1 - 0.6 * kd)
                    th = np.linspace(0, 2 * math.pi, 24)
                    line3(fr, [(x0 + rr * math.cos(a), 0.4 + rr * math.sin(a), 0.01) for a in th], col=SANGRE, w=5, a=1.0,
                          glow=1.0 - 0.5 * kd)
            line3(fr, top, col=(255, 214, 190) if zi == 0 else WHITE, w=6 if zi == 0 else 2, a=1.0 if zi == 0 else 0.35, glow=0.8)
            line3(fr, base, col=WHITE, w=2, a=0.3, glow=0.3)

        def ui(img, fx):
            kicker(img, 'CORTE DE LA YEMA · RECREACIÓN', 150, seg(u, -0.1, 0.2), col=(150, 210, 230))
            pill(img, fx, 290, 1380, 'SE DESINFLA', eout(seg(u, ud, ud + 0.25)), size=32, border=SANGRE)
            pill(img, fx, 790, 1380, 'SE DOBLA', eout(seg(u, wt(3, 12) - 0.1, wt(3, 12) + 0.15)), size=32, border=AMARILLO)
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.1, 0.3), amp=12)
    v = u - uo
    fr = Frame(cam(v, [K(-0.1, 0.9, 0, 6, ty=1.45), K(0.35, 1.5, 22, 8, ty=1.35), K(3.0, 1.45, 26, 8, ty=1.35)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.0)
    ka = seg(v, 0.0, 0.5)
    dibujar(fr, dedo(arr=ka))
    arrugas(fr, t, ka)
    return finish(fr, fi)


# 4. ¿para qué? 2013, Inglaterra: charolas y canicas mojadas que pasan de una a otra (RECREACIÓN).
def _carril(fr, t, y, vel, k=1.0, mojada=True, x0=-0.95, x1=0.95):
    ms = charola(x0, y) + charola(x1, y)
    for j in range(3):
        ms += canica((x0 - 0.15 + 0.15 * j, y + 0.21, 0.0), col=CANICAS[j])
        ms += canica((x1 - 0.15 + 0.15 * j, y + 0.21, 0.0), col=CANICAS[(j + 2) % 5])
    ph = (t * vel) % 1.0
    p = (lerp(x0, x1, ph), y + 0.21 + 0.6 * math.sin(math.pi * ph), 0.0)
    ms += canica(p, col=CANICAS[int(t * vel) % 5])
    if mojada:
        for j in range(3):
            dot3(fr, (p[0] - 0.06 * j * (1 if vel > 0 else -1), p[1] - 0.05 - 0.07 * j, 0.03), r=3, col=(170, 220, 255), a=0.8 * k, glow=0.8)
    return ms


def s_canicas(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 4.6, -30, 12, ty=0.8), K(0.3, 4.0, -8, 10, ty=0.8), K(wt(4, 8), 4.0, -8, 10, ty=0.8),
                       K(wt(4, 8) + 0.1, 3.5, 12, 12, ty=0.8), K(6.0, 3.4, 14, 12, ty=0.8)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    e = P.entrada(u, 0.0, 0.3, 'pop')
    ms = _carril(fr, t, 0.9, 0.9) + _carril(fr, t, 0.0, 0.9)
    draw_objects(fr, P.tfk(ms, s=max(0.05, e['escala']), t=(0, 0.45 * (1 - e['escala']), 0)))

    def ui(img, fx):
        kicker(img, 'ESTUDIO · 2013 · INGLATERRA', 150, seg(u, wt(4, 2) - 0.1, wt(4, 2) + 0.2), col=(150, 210, 230))
        P.numero_golpe(img, fx, '2013', 330, seg(u, wt(4, 3) - 0.1, wt(4, 3) + 0.08), size=150)
        pill(img, fx, 540, 1390, 'CANICAS MOJADAS · RECREACIÓN', eout(seg(u, wt(4, 13) - 0.1, wt(4, 13) + 0.15)), size=30, border=AGUA_C)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, wt(4, 3), 0.3), amp=14)


# 5. dos carriles: dedos arrugados (rápido) contra lisos; luego secas: igual.
def s_rapido(t, fi, u, d):
    us = wt(5, 7) - 0.12
    seca = u >= us
    fr = Frame(cam(u, [K(-0.3, 4.4, 20, 10, ty=0.8), K(0.3, 3.9, 6, 8, ty=0.8), K(us, 3.9, 6, 8, ty=0.8),
                       K(us + 0.1, 4.1, -12, 12, ty=0.8), K(6.0, 4.0, -14, 12, ty=0.8)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=1.0)
    v_lisos, v_arr = (0.55, 1.15) if not seca else (0.75, 0.75)
    ms = _carril(fr, t, 0.9, v_lisos, mojada=not seca) + _carril(fr, t, 0.0, v_arr, mojada=not seca)
    draw_objects(fr, ms)
    p_top, p_bot = fr.cam.p1((0, 0.9, 0)), fr.cam.p1((0, 0.0, 0))

    def ui(img, fx):
        pill(img, fx, 540, p_top[1] - 330, 'DEDOS LISOS', 1.0, size=30, border=(200, 200, 210), dot=False)
        pill(img, fx, 540, p_bot[1] + 120, 'DEDOS ARRUGADOS', 1.0, size=30, border=AMARILLO, dot=False)
        if not seca:
            check(img, fx, 540, 1390, seg(u, wt(5, 5) - 0.1, wt(5, 5) + 0.15), 'MÁS RÁPIDO CON ARRUGAS', col=AMARILLO)
        else:
            texto(img, fx, 900, (p_top[1] + p_bot[1]) / 2 - 60, '=', 130, AMARILLO, k=seg(u - us, 0.2, 0.4))
            pill(img, fx, 540, 1390, 'SECAS: NINGUNA DIFERENCIA', eout(seg(u - us, 0.3, 0.55)), size=32, border=(200, 200, 210))
            pill(img, fx, 540, 300, 'CANICAS SECAS', eout(seg(u - us, 0.0, 0.2)), size=34, border=(230, 200, 150))
    fr.ui.append(ui)
    out = finish(fr, fi)
    if us <= u < us + 0.1:
        out = (out.astype(np.float32) + 90).clip(0, 255).astype(np.uint8)
    return out


# 6. segundo gancho: tres dedos en el agua; dos se arrugan y el de en medio se queda liso («LISO» de cristal).
def s_raro(t, fi, u, d):
    uh = wt(6, 6) - 0.12
    fr = Frame(cam(u, [K(-0.3, 3.6, 0, 6, ty=1.2), K(0.25, 3.1, 0, 6, ty=1.2), K(uh, 3.1, 0, 6, ty=1.2), K(uh + 0.1, 2.4, -6, 4, ty=1.3),
                       K(5.0, 2.35, -8, 4, ty=1.3)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'LISO', u, t0=wt(6, 10) - 0.15, cy=0.3, alto=0.3, entrada='golpe')
    ka = seg(u, 0.3, 1.6)
    xs = (-0.62, 0.0, 0.62)
    ms = []
    for x in xs:
        ms += dedo(t=(x, 0, 0), s=0.85, arr=ka if x != 0 else 0.0)
    dibujar(fr, ms)
    for x in xs:
        if x != 0:
            arrugas(fr, t, ka, pos=(x, 0, 0), s=0.85)
    pm = fr.cam.p1((0, 1.42 * 0.85, 0.15))
    ysurf = fr.cam.p1((0, 0.6, 0))[1]

    def ui(img, fx):
        doodle_circle(img, fx, pm[0], pm[1], 95, 150, t, k=eout(seg(u, uh, uh + 0.4)), col=ROJO, w=6)
        texto(img, fx, pm[0], pm[1] - 230, '?', 110, ROJO, k=seg(u, uh + 0.2, uh + 0.35))
    fr.ui.append(ui)
    out = agua_debajo(finish(fr, fi), ysurf, k=1.0, t=t)
    return sacudir(out, t, golpe_k(u, uh + 0.1, 0.35), amp=18)


# 7. el nervio del dedo se corta (corte rojo + falla) y ese dedo se queda liso en el agua.
def s_corte(t, fi, u, d):
    uc, ul = wt(7, 7) - 0.12, wt(7, 14) - 0.15
    cortado = u >= uc
    fr = Frame(cam(u, [K(-0.3, 3.4, 30, 8, ty=0.9), K(0.25, 2.9, 10, 6, ty=0.9), K(uc, 2.9, 10, 6, ty=0.9), K(uc + 0.08, 2.3, -4, 5, ty=0.8),
                       K(ul, 2.3, -4, 5, ty=0.8), K(ul + 0.1, 2.6, -18, 6, ty=1.0), K(6.0, 2.55, -20, 6, ty=1.0)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.0)
    if u < ul:
        draw_objects(fr, dedo(), xray=1.0)
        nervio(fr, t, k=1.0, corte=0.5 if cortado else None)
        pc = fr.cam.p1((0.1, 0.5, 0.09))
        ysurf = None
    else:
        dip = P.eout4(seg(u, ul, ul + 0.4))
        dibujar(fr, dedo(t=(0, 0.6 - 0.45 * dip, 0)))
        pc = None
        ysurf = fr.cam.p1((0, 1.4, 0))[1]

    def ui(img, fx):
        if pc is not None and cortado:
            ImageDraw.Draw(img).line([(pc[0] - 70, pc[1] - 40), (pc[0] + 70, pc[1] + 40)], fill=ROJO, width=8)
            ImageDraw.Draw(fx).line([(pc[0] - 70, pc[1] - 40), (pc[0] + 70, pc[1] + 40)], fill=(150, 30, 20), width=18)
            pill(img, fx, pc[0] + 210, pc[1], 'NERVIO CORTADO', eout(seg(u, uc + 0.1, uc + 0.35)), size=30, border=ROJO,
                 col=(255, 200, 196))
        if pc is None:
            pill(img, fx, 540, 330, 'SE QUEDA LISO', eout(seg(u, ul + 0.2, ul + 0.45)), size=40, border=(220, 225, 235))
    fr.ui.append(ui)
    out = finish(fr, fi)
    if ysurf is not None:
        out = agua_debajo(out, ysurf, k=1.0, t=t)
    if uc <= u < uc + 0.25:
        out = M.tr_glitch(out, out, 0.5, fi)
    return sacudir(out, t, golpe_k(u, uc, 0.4), amp=22)


# 8. desde los años 30 → la prueba de arrugas de los médicos (tablero con el resultado).
def s_prueba(t, fi, u, d):
    um = wt(8, 7) - 0.15
    fr = Frame(cam(u, [K(-0.3, 3.4, -24, 10, ty=0.9), K(0.25, 3.0, -6, 8, ty=0.9), K(um, 3.0, -6, 8, ty=0.9),
                       K(um + 0.1, 2.6, 14, 8, ty=1.0), K(5.0, 2.55, 18, 8, ty=1.0)], cy=0.6))
    space(fr, t, floor=None, bokeh=1.0, beam=0.3)
    M.cristal(fr.base, fr.fx, 'PRUEBA', u, t0=wt(8, 12) - 0.15, cy=0.42, alto=0.26, entrada='zoom')
    ka = seg(u, um, um + 1.5)
    dibujar(fr, dedo(t=(-0.4, 0, 0), s=0.8, arr=ka) + dedo(t=(0.4, 0, 0), s=0.8))
    arrugas(fr, t, ka, pos=(-0.4, 0, 0), s=0.8)
    ysurf = fr.cam.p1((0, 0.55, 0))[1]

    def ui(img, fx):
        P.numero_golpe(img, fx, 'AÑOS 30', 330, seg(u, wt(8, 4) - 0.12, wt(8, 4) + 0.05), size=170)
        kicker(img, 'PRUEBA DE ARRUGAS · AGUA TIBIA', 470, seg(u, um, um + 0.3), col=(150, 210, 230))
    fr.ui.append(ui)
    out = agua_debajo(finish(fr, fi), ysurf, k=1.0, t=t, tibia=True)
    return sacudir(out, t, golpe_k(u, wt(8, 4) + 0.05, 0.3), amp=16)


# 9. lado a lado: nervio sano (surcos ✓) contra nervio cortado (liso ✗), con rayos X del nervio debajo.
def s_lado(t, fi, u, d):
    uc = wt(9, 5) - 0.12
    fr = Frame(cam(u, [K(-0.3, 3.0, -16, 6, ty=1.0), K(0.25, 2.6, 0, 5, ty=1.0), K(uc, 2.6, 0, 5, ty=1.0),
                       K(uc + 0.1, 2.5, 10, 5, ty=1.05), K(5.0, 2.45, 12, 5, ty=1.05)], cy=0.55))
    space(fr, t, floor=None, bokeh=1.0)
    L, R_ = (-0.45, 0, 0), (0.45, 0, 0)
    dibujar(fr, dedo(t=L, s=0.85, arr=1.0) + dedo(t=R_, s=0.85))
    arrugas(fr, t, 1.0, pos=L, s=0.85)
    nervio(fr, t, pos=L, s=0.85, k=0.8, y0=-0.2)
    nervio(fr, t, pos=R_, s=0.85, k=0.8, corte=0.45, y0=-0.2)
    pl, pr = fr.cam.p1((-0.45, 1.3, 0.15)), fr.cam.p1((0.45, 1.3, 0.15))

    def ui(img, fx):
        check(img, fx, pl[0] - 20, 330, seg(u, wt(9, 3) - 0.1, wt(9, 3) + 0.15), 'NERVIO SANO')
        tache(img, fx, pr[0] + 20, 450, seg(u, uc, uc + 0.25), 'NERVIO CORTADO')
        doodle_circle(img, fx, pl[0], pl[1], 85, 130, t, k=eout(seg(u, wt(9, 4) - 0.1, wt(9, 4) + 0.3)), col=AMARILLO, w=5)
        doodle_circle(img, fx, pr[0], pr[1], 85, 130, t, k=eout(seg(u, wt(9, 7) - 0.1, wt(9, 7) + 0.3)), col=ROJO, w=5, seed=4)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.25), amp=10)


# 10. la llanta: rueda sobre piso mojado y su dibujo saca el agua; los surcos de la yema hacen lo mismo («LLANTA»).
def s_llanta(t, fi, u, d):
    uc = wt(10, 10) - 0.12
    if u < uc:
        giro = -u * 260
        fr = Frame(cam(u, [K(-0.3, 4.2, 60, 10, ty=0.8), K(0.3, 3.4, 35, 8, ty=0.8), K(3.0, 3.3, 30, 8, ty=0.8)], cy=0.56))
        space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
        M.cristal(fr.base, fr.fx, 'LLANTA', u, t0=wt(10, 9) - 0.15, cy=0.3, alto=0.3, entrada='sube')
        dibujar(fr, llanta(t=(0, 0.88, 0), giro=giro))
        surcos_llanta(fr, t, giro, pos=(0, 0.88, 0))
        for j in range(10):  # agua que sale disparada por los canales
            ph = (t * 2 + j / 10) % 1.0
            sd = 1 if j % 2 else -1
            p = (sd * (0.25 + 0.9 * ph), 0.05 + 0.25 * math.sin(math.pi * ph), 0.3 + 0.4 * ph)
            dot3(fr, p, r=4, col=(170, 220, 255), a=1 - ph, glow=1.0)
        line3(fr, [(-2.0, 0.0, 0.9), (2.0, 0.0, 0.9)], col=AGUA_C, w=3, a=0.6, glow=0.8)
        return finish(fr, fi)
    v = u - uc
    fr = Frame(cam(v, [K(-0.1, 1.2, 0, 50, ty=1.5), K(0.3, 1.05, 10, 30, ty=1.5), K(3.0, 1.0, 14, 30, ty=1.5)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)
    dibujar(fr, dedo(arr=1.0))
    arrugas(fr, t, 1.0)
    for j in range(7):  # el agua se va por los surcos
        th = math.radians(-60 + 20 * j)
        ph = (t * 1.6 + j * 0.17) % 1.0
        y = YT + 0.12 - 0.5 * ph
        r = RT * 1.06 if y <= YT else RT * 1.06 * math.sqrt(max(0, 1 - ((y - YT) / (RT * 1.15)) ** 2))
        dot3(fr, xf((r * math.sin(th), y, r * math.cos(th))), r=4, col=(150, 210, 255), a=1 - ph, glow=1.0)

    def ui(img, fx):
        pill(img, fx, 540, 1390, 'CANALES PARA EL AGUA', eout(seg(v, 0.1, 0.35)), size=34, border=AGUA_C)
    fr.ui.append(ui)
    return finish(fr, fi)


# 11. agarre: la yema arrugada presiona una canica mojada y el agua escapa por los surcos («AGARRE»).
def s_agarre(t, fi, u, d):
    ua = wt(11, 9) - 0.15
    fr = Frame(cam(u, [K(-0.3, 2.4, 80, 6, ty=1.35), K(0.25, 1.9, 58, 4, ty=1.35), K(ua, 1.9, 58, 4, ty=1.35),
                       K(ua + 0.1, 1.55, 40, 4, ty=1.4), K(5.0, 1.5, 36, 4, ty=1.4)], cy=0.5))
    space(fr, t, floor=None, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'AGARRE', u, t0=ua, cy=0.3, alto=0.28, entrada='golpe')
    press = P.eout4(seg(u, 0.1, 0.5))
    zc = 0.8 - 0.42 * press
    dibujar(fr, dedo(arr=1.0) + canica(tuple(xf((0, 1.3 + 0.02 * math.sin(t * 3), zc))), r=0.2, col=CANICAS[0]))
    arrugas(fr, t, 1.0)
    for j in range(10):
        a = j * math.pi / 5
        ph = (t * 1.5 + j * 0.12) % 1.0
        dot3(fr, xf((0.22 * math.cos(a) * (1 + 0.8 * ph), 1.3 + 0.22 * math.sin(a) * (1 + 0.8 * ph), 0.2)), r=3.5, col=(170, 220, 255),
             a=(1 - ph) * press, glow=1.0)

    def ui(img, fx):
        check(img, fx, 540, 1390, seg(u, ua + 0.2, ua + 0.45), 'MÁS AGARRE EN MOJADO', col=AMARILLO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.05, 0.3), amp=14)


# 12. mándaselo: la regadera que no se cierra y el celular con el chat del hermano.
def s_mandalo(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 3.9, -40, 10, ty=1.0), K(0.3, 3.1, -10, 6, ty=1.0), K(4.0, 3.0, -6, 6, ty=1.0)], cy=0.6))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.4)
    e = P.entrada(u, -0.15, 0.3, 'gira')
    scr = _pant_chat(seg(u, 1.2, 1.3), t)
    dibujar(fr, regadera(t=(-0.85, 2.15, -0.4), s=0.8) +
            P.tfk(P.celular(scr), s=max(0.05, e['escala']), ry=math.degrees(e['giro']), t=(0.15, 0.95 * (1 - e['escala']), 0)))
    chorros(fr, t, pos=(-0.85, 2.13, -0.4), s=0.8, h=2.4)

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a quien se tarda', 'sans'), ('horas en la regadera.', 'serif')], 170, seg(u, 0.0, 0.3), size=62)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.25), amp=10)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.45), sfx=[]),
           dict(desde=1, fn=s_orden, tr='glitch', sfx=[]),
           dict(desde=2, fn=s_vasos, tr='push', sfx=[]),
           dict(desde=3, fn=s_surcos, tr='zoom', c=(0.5, 0.48), sfx=[]),
           dict(desde=4, fn=s_canicas, tr='cristal', palabra='CANICAS', sfx=[]),
           dict(desde=5, fn=s_rapido, tr='cubo', sfx=[]),
           dict(desde=6, fn=s_raro, tr='rompe', c=(0.5, 0.5), sfx=[]),
           dict(desde=7, fn=s_corte, tr='golpe', sfx=[]),
           dict(desde=8, fn=s_prueba, tr='flash', sfx=[]),
           dict(desde=9, fn=s_lado, tr='whip_izq', sfx=[]),
           dict(desde=10, fn=s_llanta, tr='giro', c=(0.5, 0.5), sfx=[]),
           dict(desde=11, fn=s_agarre, tr='deslizar', sfx=[]),
           dict(desde=12, fn=s_mandalo, tr='mosaico', sfx=[]),
           dict(desde=13, loop=True, tr='ritmo')]


def _sfx_dinamicos():
    E = ESCENAS
    E[0]['sfx'] = [(-1.0, 'whoosh_suave', 0.5), (0.0, 'whoosh', 0.8)] + [(uc, 'bass', 0.7) for uc in (0.1, 0.24, 0.38)] + \
                  [(UG + 0.12, 'sub', 1.0), (UG + 0.12, 'slap', 0.8), (UG + 0.25, 'tick', 0.5)]
    up, uo = wt(1, 5) - 0.12, wt(1, 8) - 0.15
    E[1]['sfx'] = [(0.0, 'tick', 0.5), (up, 'scribble', 0.5), (up + 0.1, 'thud', 0.7), (uo, 'shimmer', 0.6), (uo + 0.1, 'whoosh', 0.6)] + \
                  [(uo + 0.4 + 0.25 * i, 'tick2', 0.3) for i in range(4)]
    ua = wt(2, 8) - 0.15
    E[2]['sfx'] = [(0.0, 'whoosh', 0.5), (0.45, 'thud', 0.7)] + [(0.4 + 0.2 * i, 'tick', 0.3) for i in range(6)] + \
                  [(wt(2, 5), 'chime_a', 0.4), (ua, 'shimmer', 0.6), (ua + 0.9, 'click', 0.9), (ua + 0.95, 'whoosh', 0.5)]
    ud, us = wt(3, 3) - 0.1, wt(3, 12) - 0.12
    E[3]['sfx'] = [(0.0, 'tick', 0.5), (ud, 'whoosh_suave', 0.6), (ud + 0.1, 'tick2', 0.5), (us, 'bass', 0.8), (us + 0.1, 'scribble', 0.4),
                   (wt(3, 14) + 0.25, 'whoosh', 0.7)]
    E[4]['sfx'] = [(0.0, 'thud', 0.6), (wt(4, 3) - 0.1, 'bass', 0.9), (wt(4, 3), 'slap', 0.6), (wt(4, 7), 'tick', 0.5),
                   (wt(4, 13), 'chime_b', 0.5)] + [(0.6 + 1.1 * i, 'click', 0.4) for i in range(4)]
    us5 = wt(5, 7) - 0.12
    E[5]['sfx'] = [(0.0, 'tick', 0.4), (wt(5, 5), 'chime_c', 0.5), (us5, 'burst', 0.5), (us5 + 0.3, 'tick2', 0.5), (us5 + 0.5, 'chime_a', 0.4)] + \
                  [(0.4 + 0.85 * i, 'click', 0.35) for i in range(5)]
    uh = wt(6, 6) - 0.12
    E[6]['sfx'] = [(0.3, 'whoosh_suave', 0.4), (uh, 'scribble', 0.5), (uh + 0.1, 'sub', 0.9), (uh + 0.25, 'tick', 0.6),
                   (wt(6, 10) - 0.15, 'bass', 0.7)]
    uc7, ul = wt(7, 7) - 0.12, wt(7, 14) - 0.15
    E[7]['sfx'] = [(0.0, 'tick', 0.4), (uc7, 'burst', 0.7), (uc7, 'sub', 1.0), (uc7 + 0.1, 'tick2', 0.5), (ul, 'whoosh', 0.7),
                   (ul + 0.35, 'thud', 0.7), (ul + 0.3, 'chime_b', 0.4)]
    um = wt(8, 7) - 0.15
    E[8]['sfx'] = [(wt(8, 4) - 0.1, 'whoosh', 0.6), (wt(8, 4) + 0.05, 'bass', 1.0), (um, 'whoosh', 0.6), (um + 0.2, 'tick', 0.5),
                   (wt(8, 12), 'tick2', 0.5)]
    uc9 = wt(9, 5) - 0.12
    E[9]['sfx'] = [(wt(9, 3) - 0.1, 'chime_c', 0.5), (wt(9, 4), 'scribble', 0.5), (uc9, 'thud', 0.7), (uc9 + 0.1, 'tick', 0.5),
                   (wt(9, 7), 'scribble', 0.5)]
    uc10 = wt(10, 10) - 0.12
    E[10]['sfx'] = [(0.0, 'whoosh_suave', 0.6)] + [(0.3 + 0.4 * i, 'tick2', 0.25) for i in range(6)] + \
                   [(uc10, 'whoosh', 0.8), (uc10 + 0.3, 'chime_a', 0.4)]
    ua11 = wt(11, 9) - 0.15
    E[11]['sfx'] = [(0.1, 'thud', 0.6), (0.4, 'tick', 0.4), (ua11, 'bass', 0.9), (ua11 + 0.3, 'chime_c', 0.5)]
    E[12]['sfx'] = [(0.0, 'whoosh', 0.6), (0.15, 'thud', 0.6), (1.2, 'click', 0.8), (1.25, 'chime_b', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
