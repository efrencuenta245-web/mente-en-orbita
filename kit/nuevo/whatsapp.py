"""Reel diario: «Tu celular prende… pero WhatsApp se va.» Mié 11-nov-2026, 18:00 (CDMX). Voz Isaac.
Inicio tipo 8 (error en pantalla: el primer cuadro es el celular con el aviso rojo «Esta versión de iOS ya no es compatible»,
el chat gris y una falla digital; «ADIÓS» de cristal detrás). El final regresa: el chat funciona, falla y sale el aviso (loop).
Datos (Fox Sports MX, 4-nov-2026; Noticias SIN, 7-nov-2026): desde el 30-nov-2026 WhatsApp pide iOS 15.5 o más nuevo (deja iOS 15.1
a 15.4); en Android pide 6.0 desde el 8-sep-2026; iPhone 6s, 6s Plus, SE (1.ª gen.), 7 y 7 Plus pueden actualizar a iOS 15.8.x;
WhatsApp no cierra cuentas, solo deja de funcionar en esos sistemas; no guarda tu historial en sus servidores (respaldo en iCloud o
Google Drive). Usar apps no oficiales («WhatsApp Plus», «GB») puede suspender tu cuenta (Xataka; Infobae, 20-jun-2026).
Fuentes en guiones/2026-11-11_whatsapp.txt. Celulares, chats, calendario, escudo y nube: RECREACIÓN sin marcas ni logos."""
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
TEMA = 'whatsapp'
TXT = ['Tu celular prende… pero WhatsApp se va.',
       'El 30 de noviembre, WhatsApp deja de funcionar en iPhone con iOS 15.1 a 15.4.',
       'En Android ya pide la versión 6 o más nueva desde septiembre.',
       'Tu celular no está descompuesto: lo que envejece es su sistema.',
       'Sin actualizaciones ya no tapa sus huecos de seguridad, y WhatsApp lo deja de soportar.',
       'Mira dos iPhone 7 iguales: uno se quedó en 15.4 y el otro sí se actualizó.',
       'El primero pierde WhatsApp; el otro lo sigue usando como si nada.',
       'Y aquí está el error que más duele: cambiar de celular sin respaldo.',
       'WhatsApp no guarda tus chats en sus servidores: viven en tu celular.',
       'Si no los respaldas en iCloud o Google Drive, tus fotos y audios se pierden con él.',
       'Y no bajes un WhatsApp «modificado» de internet: te pueden suspender la cuenta.',
       'El truco: entra a Ajustes, General, Actualización de software, y actualiza si te deja.',
       'Mándaselo a tu mamá o a quien todavía tiene el iPhone viejo.',
       'Porque su celular prende… pero WhatsApp se va.']
VOZ = [x.strip() for x in open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'guiones', '2026-11-11_whatsapp_voz.txt'),
                               encoding='utf-8').read().strip().split('\n')]
assert len(VOZ) == len(TXT)

AMARILLO = (255, 236, 160)
VERDE = (110, 235, 150)
ROJO = (255, 50, 40)
GRIS = (150, 150, 160)
AZULC = (150, 210, 230)


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
    n = len(_pal(i))
    k = max(0, min(k, n - 1))
    W = _words()
    if len(W) == sum(len(_pal(j)) for j in range(len(VOZ))):
        n0 = sum(len(_pal(j)) for j in range(i))
        return W[n0 + k]['start'] - W[n0]['start']
    return (TE(i) - TT(i)) * k / n


def cam(u, claves, cy=0.5):
    p = P.cam_rapida(u, claves)
    return Cam(target=(p['tx'], p['ty'], p['tz']), dist=p['dist'], yaw=p['yaw'], pitch=p['pitch'], cy=cy, roll=p.get('roll', 0.0))


def K(u, dist, yaw, pitch=8, tx=0.0, ty=0.95, tz=0.0, roll=0.0):
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


def texto(img, fx, x, y, txt, size, col, k=1.0, glow=0.45, f='sansx', anchor='mm'):
    if k <= 0.01:
        return
    ImageDraw.Draw(img).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, k), anchor=anchor)
    ImageDraw.Draw(fx).text((x, y), txt, font=M.font(f, size), fill=M.scale_c(col, glow * k), anchor=anchor)


def check(img, fx, x, y, k, txt, col=VERDE, size=36):
    pill(img, fx, x, y, '✓ ' + txt, eout(k), size=size, border=col)


def tache(img, fx, x, y, k, txt, size=36):
    pill(img, fx, x, y, '✗ ' + txt, eout(k), size=size, border=ROJO, col=(255, 200, 196))


def flat(m, glow=None):
    m.flat = True
    if glow is not None:
        m.glow = glow
    return m


# ================================================================== pantallas del celular (420×900)
F = M.font
BURB = [('in', '¿Ya llegaste?'), ('out', 'Ya casi 😄'), ('in', 'Te mando la foto'), ('out', 'Va, aquí espero'),
        ('in', '¿Viste el aviso?'), ('out', '¿Cuál aviso?')]


def _chat(d, im, n=6, gris=0.0, sube=0.0):
    w, h = im.size
    d.rectangle((0, 64, w, 150), fill=(18, 20, 24))
    d.ellipse((24, 82, 76, 134), fill=(70, 74, 84))
    d.text((92, 92), 'Mamá', font=F('sans', 30), fill=(236, 236, 240))
    d.text((92, 128), 'en línea' if gris < 0.5 else 'sin conexión', font=F('sansm', 20), fill=(140, 200, 160) if gris < 0.5 else (150, 150, 156))
    y = 190 - sube
    for i, (lado, txt) in enumerate(BURB[:n]):
        tw = d.textlength(txt.replace('😄', ':)'), font=F('sansm', 26)) + 44
        if lado == 'in':
            x0, x1, col = 24, 24 + tw, M.mixc((52, 54, 62), (40, 40, 42), gris)
        else:
            x0, x1, col = w - 24 - tw, w - 24, M.mixc((30, 120, 150), (60, 60, 62), gris)
        d.rounded_rectangle((x0, y, x1, y + 62), radius=22, fill=col)
        d.text((x0 + 22, y + 31), txt.replace('😄', ':)'), font=F('sansm', 26), fill=M.mixc((240, 240, 244), (130, 130, 134), gris), anchor='lm')
        y += 84
    d.rounded_rectangle((20, h - 120, w - 90, h - 60), radius=30, fill=(30, 32, 38))
    d.text((44, h - 90), 'Mensaje', font=F('sansm', 24), fill=(120, 120, 128), anchor='lm')
    d.ellipse((w - 80, h - 122, w - 18, h - 60), fill=M.mixc((30, 140, 170), (60, 60, 62), gris))


def _aviso(d, im, k=1.0):
    if k <= 0.01:
        return
    w, h = im.size
    y0 = 300 - 40 * (1 - k)
    d.rounded_rectangle((26, y0, w - 26, y0 + 300), radius=26, fill=M.scale_c((60, 10, 12), 0.6 + 0.4 * k), outline=M.scale_c(ROJO, k), width=5)
    d.polygon([(w / 2 - 120, y0 + 76), (w / 2 - 96, y0 + 34), (w / 2 - 72, y0 + 76)], outline=M.scale_c((255, 120, 110), k), width=4)
    d.text((w / 2 - 96, y0 + 62), '!', font=F('sansx', 30), fill=M.scale_c((255, 120, 110), k), anchor='mm')
    d.text((w / 2 + 20, y0 + 56), 'ERROR', font=F('sansx', 44), fill=M.scale_c((255, 120, 110), k), anchor='mm')
    for j, ln in enumerate(['Esta versión de iOS', 'ya no es compatible.', 'Actualiza para seguir.']):
        d.text((w / 2, y0 + 130 + 46 * j), ln, font=F('sans', 30), fill=M.scale_c((250, 236, 236), k), anchor='mm')


def scr_chat(n=6, gris=0.0, aviso=0.0, sube=0.0):
    def dib(d, im):
        _chat(d, im, n, gris, sube)
        _aviso(d, im, aviso)
    return P.pantalla(dib)


def scr_version(ver, estado='viejo', k_bar=0.0):
    def dib(d, im):
        w, h = im.size
        d.text((w / 2, 110), 'Información', font=F('sans', 30), fill=(230, 230, 236), anchor='mm')
        d.text((w / 2, 300), 'iOS', font=F('sansm', 48), fill=(170, 170, 178), anchor='mm')
        col = (255, 110, 100) if estado == 'viejo' else (120, 235, 160)
        d.text((w / 2, 400), ver, font=F('sansx', 120), fill=col, anchor='mm')
        if k_bar > 0:
            d.rounded_rectangle((60, 560, w - 60, 590), radius=15, fill=(40, 42, 48))
            d.rounded_rectangle((60, 560, 60 + (w - 120) * k_bar, 590), radius=15, fill=(120, 235, 160))
            d.text((w / 2, 640), 'Actualizado' if k_bar >= 1 else 'Actualizando…', font=F('sansm', 28), fill=(200, 200, 206), anchor='mm')
    return P.pantalla(dib)


def scr_ajustes(paso, kbar=0.0):
    def dib(d, im):
        w, h = im.size
        tit = ['Ajustes', 'General', 'Actualización'][min(paso, 2)]
        d.text((34, 110), tit, font=F('sansx', 44), fill=(240, 240, 244), anchor='lm')
        if paso < 2:
            filas = ['Wi-Fi', 'Bluetooth', 'General', 'Pantalla', 'Batería'] if paso == 0 else \
                ['Información', 'Actualización de software', 'Almacenamiento', 'Fecha y hora']
            hi = 2 if paso == 0 else 1
            for i, txt in enumerate(filas):
                y = 200 + i * 92
                fill = (40, 70, 84) if i == hi else (26, 28, 34)
                d.rounded_rectangle((20, y, w - 20, y + 76), radius=16, fill=fill)
                d.text((44, y + 38), txt, font=F('sansm', 26), fill=(236, 236, 240), anchor='lm')
                d.text((w - 44, y + 38), '›', font=F('sans', 36), fill=(150, 150, 156), anchor='mm')
        else:
            d.text((w / 2, 300), 'iOS 15.8', font=F('sansx', 74), fill=(236, 236, 240), anchor='mm')
            d.rounded_rectangle((60, 420, w - 60, 452), radius=16, fill=(40, 42, 48))
            d.rounded_rectangle((60, 420, 60 + (w - 120) * kbar, 452), radius=16, fill=(120, 235, 160))
            d.text((w / 2, 510), 'Instalando…' if kbar < 1 else '✓ Actualizado', font=F('sans', 30),
                   fill=(200, 200, 206) if kbar < 1 else (120, 235, 160), anchor='mm')
    return P.pantalla(dib)


def scr_descarga(k, susp=0.0):
    def dib(d, im):
        w, h = im.size
        d.text((w / 2, 140), 'WhatsApp_PLUS.apk', font=F('mono', 26), fill=(230, 230, 236), anchor='mm')
        d.text((w / 2, 190), 'sitio-desconocido.xyz', font=F('mono', 20), fill=(255, 140, 120), anchor='mm')
        d.rounded_rectangle((50, 260, w - 50, 290), radius=15, fill=(40, 42, 48))
        d.rounded_rectangle((50, 260, 50 + (w - 100) * k, 290), radius=15, fill=(255, 190, 90))
        if susp > 0.01:
            d.rounded_rectangle((30, 380, w - 30, 680), radius=26, fill=M.scale_c((60, 10, 12), susp), outline=M.scale_c(ROJO, susp), width=5)
            d.rounded_rectangle((w / 2 - 34, 440, w / 2 + 34, 490), radius=8, fill=M.scale_c((255, 160, 150), susp))
            d.arc((w / 2 - 24, 404, w / 2 + 24, 460), 180, 360, fill=M.scale_c((255, 160, 150), susp), width=8)
            d.text((w / 2, 540), 'CUENTA', font=F('sansx', 52), fill=M.scale_c((255, 120, 110), susp), anchor='mm')
            d.text((w / 2, 610), 'SUSPENDIDA', font=F('sansx', 52), fill=M.scale_c((255, 120, 110), susp), anchor='mm')
    return P.pantalla(dib)


def scr_galeria(n=9):
    def dib(d, im):
        w, h = im.size
        d.text((34, 110), 'Fotos', font=F('sansx', 44), fill=(240, 240, 244), anchor='lm')
        for i in range(n):
            x, y = 24 + (i % 3) * 126, 170 + (i // 3) * 126
            c = [(220, 120, 70), (70, 120, 200), (90, 170, 110), (200, 90, 130), (230, 190, 90), (90, 90, 160), (160, 110, 80),
                 (60, 150, 170), (210, 150, 120)][i % 9]
            d.rounded_rectangle((x, y, x + 116, y + 116), radius=10, fill=c)
            d.ellipse((x + 70, y + 18, x + 98, y + 46), fill=M.mixc(c, (255, 255, 255), 0.5))
            d.polygon([(x, y + 116), (x + 50, y + 60), (x + 90, y + 116)], fill=M.mixc(c, (0, 0, 0), 0.4))
    return P.pantalla(dib)


def celu(scr, x=0.0, y=0.0, z=0.0, ry=0.0, rz=0.0, s=1.0, interior=False):
    ms = P.celular(scr, ry=ry, rz=rz, interior=interior)
    if s != 1.0:
        ms = P.tfk(ms, s=s, t=(0, P.PH_Y * (1 - s), 0))
    return P.tfk(ms, t=(x, y, z))


# ---------------------------------------------------------------- objetos
_C = {}


def _cal_img():
    if 'cal' not in _C:
        im = Image.new('RGB', (500, 560), (240, 238, 232))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 500, 140), fill=(200, 40, 36))
        d.text((250, 72), 'NOVIEMBRE', font=F('sansx', 62), fill=(255, 255, 255), anchor='mm')
        d.text((250, 350), '30', font=F('sansx', 290), fill=(30, 30, 34), anchor='mm')
        d.text((250, 520), 'LUNES · 2026', font=F('sans', 36), fill=(120, 120, 126), anchor='mm')
        _C['cal'] = im.convert('RGBA')
    return _C['cal']


def calendario(t=(0, 0, 0), ry=0.0, rx=0.0):
    m = named(M3.rbox(1.0, 0.12, 1.12, 0.04, (240, 238, 232), n=3, shadow=0, gloss=0.2, base=False).tf(rx=90), 'cal', rim=0.4)
    m2 = named(M3.box(1.0, 1.12, 0.12, (240, 238, 232), shadow=0, base=False, gloss=0.2), 'cal', rim=0.4)
    M3.decal(m2, m2.FACE['front'], _cal_img())
    return P.tfk([m2], rx=rx, ry=ry, t=t)


def escudo(fr, c, s, t, huecos=0.0, k=1.0):
    """Escudo de alambre que brilla; con `huecos` se le abren agujeros rojos que dejan pasar puntos."""
    C = np.array(c, float)
    pts = []
    for a in np.linspace(0, 1, 60):
        if a < 0.5:
            x = lerp(-0.6, 0.6, a * 2)
            y = 0.62 + 0.06 * math.sin(a * 2 * math.pi)
        else:
            q = (a - 0.5) * 2
            ang = math.pi * q
            x = 0.6 * math.cos(ang)
            y = 0.62 - 1.2 * math.sin(ang * 0.5) ** 0.8 * (0.5 + 0.5 * math.sin(ang * 0.5))
        pts.append(C + np.array([x, y, 0]) * s)
    line3(fr, pts + [pts[0]], col=CYAN, w=5, a=k, glow=1.0)
    inner = [C + (p - C) * 0.82 for p in pts]
    line3(fr, inner + [inner[0]], col=WHITE, w=2.5, a=0.6 * k, glow=0.5)
    hs = [(-0.25, 0.25), (0.22, 0.05), (-0.05, -0.25), (0.3, 0.4)]
    for i, (hx, hy) in enumerate(hs):
        kk = seg(huecos, i * 0.2, i * 0.2 + 0.3)
        if kk > 0:
            p = C + np.array([hx, hy, 0.02]) * s
            th = np.linspace(0, 2 * math.pi, 20)
            r = 0.09 * s * eout(kk)
            line3(fr, [p + np.array([r * math.cos(a) * (1 + 0.3 * math.sin(a * 3)), r * math.sin(a), 0]) for a in th], col=ROJO, w=4, a=1.0, glow=1.2)
            for j in range(4):
                ph = (t * 1.3 + j * 0.25 + i * 0.1) % 1.0
                dot3(fr, p + np.array([0.1 * math.sin(j * 2.1), 0.05 * math.cos(j), 0.2 + 1.4 * ph]) * s, r=4, col=ROJO, a=kk * (1 - ph), glow=1.2)


def nube(fr, c, s, k=1.0, col=WHITE):
    C = np.array(c, float)
    for (dx, dy, r) in ((-0.45, 0, 0.32), (0, 0.18, 0.42), (0.45, 0, 0.32), (0.2, -0.12, 0.3), (-0.22, -0.12, 0.3)):
        th = np.linspace(0, 2 * math.pi, 40)
        line3(fr, [C + np.array([dx + r * math.cos(a), dy + r * math.sin(a), 0]) * s for a in th], col=col, w=3, a=0.8 * k, glow=0.7)


def servidor(t=(0, 0, 0), s=1.0, vacio=1.0):
    ms = [named(M3.rbox(0.9, 1.6, 0.7, 0.04, (40, 42, 48), n=3, shadow=0, gloss=0.5), 'rack', rim=0.7, gloss=0.5)]
    for i in range(5):
        y = 0.2 + i * 0.28
        ms.append(named(M3.box(0.78, 0.2, 0.02, (24, 26, 30), shadow=0, base=True, gloss=0.6).tf(t=(0, y, 0.36)), 'bahia', rim=0.3))
        ms.append(flat(named(M3.box(0.04, 0.04, 0.01, (90, 255, 140), shadow=0, base=False).tf(t=(0.3, y + 0.1, 0.38)), 'led'),
                       glow=M.scale_c((90, 255, 140), 0.4 if vacio > 0.5 else 1.0)))
    return P.tfk(ms, s=s, t=t)


# ================================================================== escenas
# 0. gancho · inicio tipo 8: el celular con el aviso rojo de ERROR, chat gris, falla digital y «ADIÓS» de cristal detrás.
#    u < 0 (final en loop): el chat funciona, falla y sale el aviso (así el último cuadro es el primero).
U_F = -0.85                    # en el loop: el chat se cae aquí


def s_gancho(t, fi, u, d):
    pose = P.cam_rapida(u, [(-3.5, dict(dist=3.4, yaw=-34, pitch=8)), (-1.0, dict(dist=3.0, yaw=-16, pitch=6)),
                            (-0.5, dict(dist=2.55, yaw=8, pitch=4)), (0.55, dict(dist=2.85, yaw=-14, pitch=6)), (3.5, dict(dist=2.8, yaw=-18, pitch=6))])
    fr = Frame(Cam(target=(0, 0.92, 0), cy=0.6, **pose))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ADIÓS', u, t0=-3.6, cy=0.43, entrada='golpe')
    falla = u > U_F
    av = 1.0 if u > -0.5 else seg(u, U_F + 0.05, -0.5)
    gris = seg(u, U_F, U_F + 0.3) if falla else 0.0
    n = 6 if u > -2.6 else 4 + int(seg(u, -3.4, -2.6) * 2)
    draw_objects(fr, celu(scr_chat(n=n, gris=gris, aviso=av), ry=6 * math.sin(t * 1.3)))

    def ui(img, fx):
        if u > -0.6:
            kicker(img, 'AVISO EN TU PANTALLA', 140, 1.0 if u > -0.4 else seg(u, -0.6, -0.4), col=ROJO, size=30)
        if u > 0:
            P.titulo_golpe(img, fx, [('Tu celular prende…', 'sans'), ('pero WhatsApp se va.', 'serif')], 190, seg(u, 0.12, 0.27), size=74)
    fr.ui.append(ui)
    out = finish(fr, fi)
    # falla digital en el aviso (el problema primero)
    if (-0.75 < u < -0.05 and int(round(t * 24)) % 6 == 1) or (0.4 < u < 0.5) or (1.5 < u < 1.58):
        out = M.tr_glitch(out, out, 0.5, fi)
    return sacudir(out, t, golpe_k(u, -0.5, 0.3) + golpe_k(u, 0.27, 0.35), amp=22)


# 1. el 30 de noviembre (calendario que cae, «30 NOV» de cristal) → iOS 15.1 a 15.4 (barras de versiones: rojas y verdes)
VERS = ['15.0', '15.1', '15.2', '15.3', '15.4', '15.5', '15.6', '15.7', '15.8']


def s_fecha(t, fi, u, d):
    uv = wt(1, 11) - 0.15                        # «iOS quince punto uno…»
    if u < uv:
        fr = Frame(cam(u, [K(-0.3, 3.6, 40, 16, ty=1.0), K(0.3, 3.2, 12, 8, ty=1.0), K(uv, 3.0, -8, 6, ty=1.0)], cy=0.56))
        space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.6)
        M.cristal(fr.base, fr.fx, '30 NOV', u, t0=0.05, cy=0.3, alto=0.24, entrada='zoom')
        e = P.entrada(u, -0.15, 0.4, 'cae')
        draw_objects(fr, calendario(t=(0, 1.0 - e['dy'] * 0.6, 0), rx=-8, ry=-10 + 4 * math.sin(t)))

        def ui(img, fx):
            kicker(img, 'WHATSAPP · ÚLTIMO DÍA EN IOS VIEJO', 140, seg(u, -0.1, 0.2), col=AZULC)
        fr.ui.append(ui)
        return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.35), amp=22)
    v = u - uv
    fr = Frame(cam(v, [K(-0.2, 5.6, -40, 24, ty=0.6), K(0.3, 5.0, -10, 16, ty=0.6), K(3.0, 4.9, -6, 16, ty=0.6)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    ms = []
    for i, ver in enumerate(VERS):
        kk = seg(v, 0.04 * i, 0.04 * i + 0.25)
        if kk <= 0:
            continue
        mala = 1 <= i <= 4
        h = (0.4 + 0.12 * i) * P.resorte(kk)
        col = ROJO if mala else ((90, 90, 100) if i == 0 else VERDE)
        x = -1.2 + i * 0.3
        ms.append(flat(named(M3.box(0.22, max(0.01, h), 0.22, col, shadow=0, base=True), 'barra'), glow=M.scale_c(col, 0.35)))
        ms[-1] = P.tfk([ms[-1]], t=(x, 0, 0))[0]
    draw_objects(fr, ms)
    labs = [fr.cam.p1((-1.2 + i * 0.3, -0.02, 0.25)) for i in range(len(VERS))]
    top = fr.cam.p1((-1.2 + 2.5 * 0.3, 1.2, 0))

    def ui(img, fx):
        kicker(img, 'VERSIONES DE IOS', 140, seg(v, -0.1, 0.2), col=AZULC)
        for i, (x, y, _) in enumerate(labs):
            texto(img, fx, x, y + 40, VERS[i], 26, ROJO if 1 <= i <= 4 else (VERDE if i > 4 else GRIS), seg(v, 0.04 * i, 0.04 * i + 0.25), glow=0.3, f='mono')
        if v > 0.5:
            tache(img, fx, top[0], top[1] - 90, seg(v, 0.5, 0.75), '15.1 A 15.4 · SIN WHATSAPP', size=30)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(v, 0.5, 0.3), amp=12)


# 2. en Android ya pide la versión 6 o más nueva (dos celulares: 5.1 tachado y 6.0 palomeado)
def scr_android(ver, ok):
    def dib(d, im):
        w, h = im.size
        d.text((w / 2, 120), 'Versión del sistema', font=F('sans', 28), fill=(220, 220, 226), anchor='mm')
        d.text((w / 2, 380), ver, font=F('sansx', 150), fill=(120, 235, 160) if ok else (255, 110, 100), anchor='mm')
        d.text((w / 2, 540), '✓ compatible' if ok else '✗ ya no', font=F('sans', 36), fill=(120, 235, 160) if ok else (255, 110, 100), anchor='mm')
    return P.pantalla(dib)


def s_android(t, fi, u, d):
    u6 = wt(2, 6) - 0.12                         # «seis»
    fr = Frame(cam(u, [K(-0.3, 4.4, 30, 10, ty=0.95), K(0.3, 3.9, 0, 6, ty=0.95), K(u6, 3.6, -14, 6, ty=0.95), K(4.0, 3.55, -18, 6, ty=0.95)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    e1 = P.entrada(u, -0.2, 0.28, 'gira')
    e2 = P.entrada(u, u6 - 0.1, 0.28, 'pop')
    ms = celu(scr_android('5.1', False), x=-0.62, ry=12 + math.degrees(e1['giro']), s=max(0.05, e1['escala']))
    if u > u6 - 0.12:
        ms += celu(scr_android('6.0', True), x=0.62, ry=-12, s=max(0.05, e2['escala']))
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'ANDROID · DESDE EL 8 DE SEPTIEMBRE', 140, seg(u, -0.1, 0.2), col=AZULC)
        if u > u6 + 0.3:
            check(img, fx, 540, 1420, seg(u, u6 + 0.3, u6 + 0.55), 'ANDROID 6 O MÁS NUEVO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, u6 + 0.18, 0.3), amp=14)


# 3. no está descompuesto (rayos X: las piezas están bien) → lo que envejece es su sistema («SISTEMA» de cristal)
def s_sistema(t, fi, u, d):
    us = wt(3, 7) - 0.15                         # «envejece es su sistema»
    fr = Frame(cam(u, [K(-0.3, 1.8, 10, 4), K(0.3, 2.6, 34, 10), K(us, 3.2, -24, 8), K(4.0, 3.15, -28, 8)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9)
    if u >= us:
        M.cristal(fr.base, fr.fx, 'SISTEMA', u, t0=us + 0.05, cy=0.33, alto=0.2, entrada='sube')
    xr = seg(u, -0.2, 0.2) * (1 - seg(u, us, us + 0.35))
    año = 2016 + int(10 * P.eout4(seg(u, us + 0.1, us + 1.0)))
    draw_objects(fr, celu(scr_version('15.4', 'viejo'), interior=True, ry=-8 + 6 * math.sin(t)), xray=xr, keep=('in',))
    pc = fr.cam.p1((0.16, P.PH_Y + 0.5, 0.04))

    def ui(img, fx):
        kicker(img, 'RAYOS X · POR DENTRO', 140, seg(u, -0.1, 0.2), col=AZULC)
        if u < us + 0.2:
            check(img, fx, pc[0] + 60, pc[1] - 140, seg(u, 0.2, 0.45), 'PIEZAS BIEN', size=30)
        if u > us:
            texto(img, fx, 540, 1250, f'{año}', 96, AMARILLO, seg(u, us + 0.05, us + 0.25), f='mono')
            pill(img, fx, 540, 1400, 'SU SISTEMA SE QUEDÓ ATRÁS', eout(seg(u, us + 0.4, us + 0.65)), size=32, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, us + 0.35, 0.3), amp=14)


# 4. sin actualizaciones ya no tapa sus huecos de seguridad (escudo con agujeros) → WhatsApp lo deja de soportar
def s_huecos(t, fi, u, d):
    uh = wt(4, 6) - 0.15                         # «huecos de seguridad»
    uw = wt(4, 9) - 0.12                         # «y WhatsApp lo deja de soportar»
    fr = Frame(cam(u, [K(-0.3, 3.0, -30, 6, ty=1.0), K(0.3, 3.8, -6, 4, ty=1.0), K(uw, 3.6, 10, 6, ty=1.0), K(5.0, 3.55, 12, 6, ty=1.0)], cy=0.52))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=1.0)
    draw_objects(fr, celu(scr_chat(n=4, gris=seg(u, uw, uw + 0.3), aviso=seg(u, uw + 0.1, uw + 0.4)), z=-0.3, s=0.75, ry=-6))
    escudo(fr, (0, 1.05, 0.25), 1.15, t, huecos=seg(u, uh - 0.2, uh + 0.8), k=seg(u, -0.2, 0.1))

    def ui(img, fx):
        kicker(img, 'SIN ACTUALIZACIONES', 140, seg(u, -0.1, 0.2), col=ROJO)
        if u > uh:
            pill(img, fx, 540, 300, 'HUECOS DE SEGURIDAD', eout(seg(u, uh, uh + 0.3)), size=32, border=ROJO, dot=False)
        if u > uw:
            tache(img, fx, 540, 1420, seg(u, uw + 0.2, uw + 0.45), 'SIN SOPORTE')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uh + 0.2, 0.25) + golpe_k(u, uw + 0.3, 0.25), amp=12)


# 5. dos iPhone 7 iguales: uno en 15.4 y el otro actualizado (zoom digital REC a las versiones)
def s_dos(t, fi, u, d):
    u1 = wt(5, 5) - 0.12                         # «uno se quedó en quince punto cuatro»
    u2 = wt(5, 12) - 0.12                        # «y el otro sí se actualizó»
    fr = Frame(cam(u, [K(-0.3, 5.2, 0, 26, ty=0.95), K(0.3, 3.9, 0, 6, ty=0.95), K(u1, 3.5, 14, 6, ty=0.95, tx=-0.3),
                       K(u2, 3.5, -14, 6, ty=0.95, tx=0.3), K(6.0, 3.45, -16, 6, ty=0.95, tx=0.3)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    e1 = P.entrada(u, -0.2, 0.25, 'cae')
    e2 = P.entrada(u, -0.05, 0.25, 'cae')
    kb = seg(u, u2, u2 + 0.9)
    ms = celu(scr_version('15.4', 'viejo'), x=-0.6, y=-e1['dy'] * 0.5, ry=10) + \
        celu(scr_version('15.8' if kb > 0.5 else '15.4', 'nuevo' if kb > 0.5 else 'viejo', k_bar=kb), x=0.6, y=-e2['dy'] * 0.5, ry=-10)
    draw_objects(fr, ms)
    pa, pb = fr.cam.p1((-0.6, 1.95, 0)), fr.cam.p1((0.6, 1.95, 0))
    pv = fr.cam.p1((-0.6, P.PH_Y + 0.25, 0.05)) if u < u2 else fr.cam.p1((0.6, P.PH_Y + 0.25, 0.05))

    def ui(img, fx):
        kicker(img, 'DOS IPHONE 7 IGUALES · EJEMPLO', 140, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, pa[0], pa[1] - 30, 'IPHONE 7', eout(seg(u, 0.1, 0.35)), size=26, border=GRIS, dot=False)
        pill(img, fx, pb[0], pb[1] - 30, 'IPHONE 7', eout(seg(u, 0.2, 0.45)), size=26, border=GRIS, dot=False)
        if u > u1:
            doodle_circle(img, fx, pv[0], pv[1], 150, 90, t, k=eout(seg(u, u1 if u < u2 else u2 + 0.6, (u1 if u < u2 else u2 + 0.6) + 0.35)),
                          col=ROJO if u < u2 else VERDE, w=6)
    fr.ui.append(ui)
    out = finish(fr, fi)
    if u1 + 0.1 < u < u2:
        z = 1.0 + 0.5 * P.eout4(seg(u, u1 + 0.1, u1 + 0.35))
        out = M.scale_about(out, z, pv[0] / 1080, pv[1] / 1920)
        im = Image.fromarray(out)
        rec_frame(im, t, 1.0, zoom_label=f'x{z:.1f}')
        out = np.asarray(im)
    return sacudir(out, t, golpe_k(u, 0.05, 0.3) + golpe_k(u, u2 + 0.9, 0.25), amp=14)


# 6. el primero pierde WhatsApp (chat gris con ✗) y el otro lo sigue usando (mensajes que siguen llegando)
def s_pierde(t, fi, u, d):
    uo = wt(6, 4) - 0.12                         # «el otro lo sigue usando»
    fr = Frame(cam(u, [K(-0.3, 3.0, -40, 10, ty=0.95, tx=-0.6), K(0.3, 3.3, -24, 6, ty=0.95, tx=-0.4), K(uo, 3.3, 24, 6, ty=0.95, tx=0.4),
                       K(4.0, 3.25, 28, 6, ty=0.95, tx=0.4)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0)
    n2 = 3 + min(3, int(max(0.0, u - uo) / 0.35))
    ms = celu(scr_chat(n=6, gris=seg(u, 0.0, 0.3), aviso=seg(u, 0.15, 0.4)), x=-0.6, ry=14) + \
        celu(scr_chat(n=n2, sube=0), x=0.6, ry=-14)
    draw_objects(fr, ms)
    pa, pb = fr.cam.p1((-0.6, 0.0, 0)), fr.cam.p1((0.6, 0.0, 0))

    def ui(img, fx):
        kicker(img, 'EL 30 DE NOVIEMBRE', 140, seg(u, -0.1, 0.2), col=AZULC)
        tache(img, fx, pa[0], pa[1] + 40, seg(u, 0.3, 0.55), '15.4', size=30)
        if u > uo:
            check(img, fx, pb[0], pb[1] + 40, seg(u, uo, uo + 0.25), '15.8', size=30)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.3) + golpe_k(u, uo + 0.1, 0.2), amp=12)


# 7. segundo gancho: el error que más duele (celular viejo → nuevo, los chats se desbaratan) + «RESPALDO» de cristal
def s_error(t, fi, u, d):
    uc = wt(7, 8) - 0.12                         # «cambiar de celular»
    ur = wt(7, 11) - 0.15                        # «sin respaldo»
    fr = Frame(cam(u, [K(-0.3, 2.6, 30, 6), K(0.25, 3.4, 4, 4), K(uc, 3.6, -16, 6), K(5.0, 3.55, -20, 6)], cy=0.58))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    if u >= ur:
        M.cristal(fr.base, fr.fx, 'RESPALDO', u, t0=ur, cy=0.3, alto=0.18, entrada='golpe', brillo=1.2)
    kc = P.eout4(seg(u, uc, uc + 0.45))
    vacio = u > ur + 0.2
    ms = celu(scr_chat(n=6), x=lerp(0.0, -0.75, kc), y=-0.15 * kc, ry=lerp(0, 25, kc), rz=lerp(0, 12, kc))
    if u > uc:
        e = P.entrada(u, uc + 0.1, 0.3, 'desliza')
        ms += celu(scr_chat(n=0 if vacio else 2), x=0.75 + e['dy'] * 0.3, ry=-18)
    draw_objects(fr, ms)
    if u > ur:                                  # las burbujas se desbaratan en puntos que se van
        for j in range(26):
            ph = seg(u, ur + 0.02 * j, ur + 0.02 * j + 0.9)
            if 0 < ph < 1:
                p0 = np.array([-0.75 + 0.3 * math.sin(j * 1.7), 1.0 + 0.5 * math.cos(j * 2.3), 0.1])
                p = p0 + np.array([0.6 * math.sin(j), 1.4 * ph, 0.8 * ph])
                dot3(fr, p, r=5, col=(150, 210, 230), a=1 - ph, glow=1.0)

    def ui(img, fx):
        kicker(img, '¡EL ERROR QUE MÁS DUELE!', 140, seg(u, -0.1, 0.1), col=ROJO, size=32)
        if u > ur + 0.2:
            tache(img, fx, 540, 1420, seg(u, ur + 0.3, ur + 0.55), 'CHATS PERDIDOS')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, -0.05, 0.4) + golpe_k(u, ur + 0.1, 0.3), amp=24)


# 8. WhatsApp no guarda tus chats en sus servidores (servidor vacío con ✗) → viven en tu celular (rayos X: chats en la memoria)
def s_servidor(t, fi, u, d):
    uv = wt(8, 8) - 0.12                         # «viven en tu celular»
    fr = Frame(cam(u, [K(-0.3, 4.6, -26, 14, ty=1.1, tx=0.05), K(0.3, 5.2, -6, 10, ty=1.1, tx=0.05), K(uv, 3.8, 14, 6, ty=1.0, tx=0.55),
                       K(4.0, 3.75, 18, 6, ty=1.0, tx=0.55)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.3)
    e = P.entrada(u, -0.2, 0.3, 'pop')
    nube(fr, (-0.55, 2.2, -0.4), 0.7 * max(0.05, e['escala']), k=1.0)
    draw_objects(fr, servidor(t=(-0.55, 0.0, -0.4), s=0.8 * max(0.05, e['escala'])) +
                 celu(scr_chat(n=6), x=0.65, ry=-16, interior=True), xray=seg(u, uv, uv + 0.3), keep=('in', 'rack', 'bahia', 'led'))
    if u > uv:
        for j in range(8):
            ph = (t * 0.8 + j / 8) % 1.0
            dot3(fr, np.array([0.65 + 0.18 * math.sin(j * 2.2), 0.6 + 0.9 * ph, 0.05]), r=5, col=CYAN, a=seg(u, uv, uv + 0.3), glow=1.2)
    ps, pc = fr.cam.p1((-0.55, 1.45, -0.4)), fr.cam.p1((0.65, 1.9, 0))

    def ui(img, fx):
        kicker(img, 'DÓNDE VIVEN TUS CHATS', 140, seg(u, -0.1, 0.2), col=AZULC)
        tache(img, fx, ps[0], ps[1] - 40, seg(u, 0.4, 0.65), 'SERVIDORES', size=28)
        if u > uv:
            check(img, fx, pc[0], pc[1] - 30, seg(u, uv + 0.1, uv + 0.35), 'TU CELULAR', col=CYAN, size=30)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.4, 0.25) + golpe_k(u, uv + 0.3, 0.25), amp=12)


# 9. si no los respaldas en iCloud o Google Drive, tus fotos y audios se pierden (la galería se cae a pedazos)
def s_fotos(t, fi, u, d):
    uf = wt(9, 9) - 0.12                         # «tus fotos y audios»
    up = wt(9, 13) - 0.12                        # «se pierden con él»
    fr = Frame(cam(u, [K(-0.3, 3.4, 40, 10), K(0.3, 3.0, 12, 6), K(up, 3.4, -10, 14), K(5.0, 3.35, -14, 14)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0)
    nube(fr, (0.0, 2.35, -0.3), 0.7, k=seg(u, -0.2, 0.2), col=CYAN)
    draw_objects(fr, celu(scr_galeria(9), ry=10 * math.sin(t * 0.8)))
    kp = seg(u, up, up + 1.2)
    if u > uf:                                  # fotos y audios que salen del celular… y caen al vacío
        for j in range(9):
            a = j / 9 * 2 * math.pi
            kk = seg(u, uf + 0.05 * j, uf + 0.05 * j + 0.3)
            p = np.array([0.95 * math.cos(a) * eout(kk), P.PH_Y + 0.8 * math.sin(a) * eout(kk) - 2.5 * kp ** 2, 0.3])
            c = [(220, 120, 70), (70, 120, 200), (90, 170, 110), (200, 90, 130), (230, 190, 90), (90, 90, 160)][j % 6]
            if j % 3 == 2:
                for q in range(5):
                    hh = 0.05 + 0.08 * abs(math.sin(t * 9 + q + j))
                    line3(fr, [p + np.array([-0.12 + 0.06 * q, -hh, 0]), p + np.array([-0.12 + 0.06 * q, hh, 0])], col=CYAN, w=4, a=kk, glow=1.0)
            else:
                dot3(fr, p, r=16, col=c, a=kk, glow=0.6)

    def ui(img, fx):
        kicker(img, 'SIN RESPALDO EN ICLOUD O GOOGLE DRIVE', 140, seg(u, -0.1, 0.2), col=AZULC, size=24)
        if u > up:
            tache(img, fx, 540, 1420, seg(u, up + 0.2, up + 0.45), 'FOTOS Y AUDIOS PERDIDOS')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, up + 0.3, 0.3), amp=14)


# 10. no bajes un WhatsApp «modificado»: la descarga se completa y sale «CUENTA SUSPENDIDA» («SUSPENDIDA» de cristal)
def s_modificado(t, fi, u, d):
    us = wt(10, 10) - 0.15                       # «suspender la cuenta»
    fr = Frame(cam(u, [K(-0.3, 2.4, -30, 6), K(0.3, 2.9, -6, 4), K(us, 2.7, 14, 6), K(5.0, 2.65, 18, 6)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=1.0, beam=0.5)
    if u >= us:
        M.cristal(fr.base, fr.fx, 'SUSPENDIDA', u, t0=us + 0.05, cy=0.31, alto=0.16, entrada='golpe', brillo=1.2)
    kd = seg(u, 0.1, us)
    draw_objects(fr, celu(scr_descarga(kd, susp=seg(u, us, us + 0.3)), ry=-8 + 4 * math.sin(t)))

    def ui(img, fx):
        kicker(img, 'WHATSAPP «MODIFICADO» · NO OFICIAL', 140, seg(u, -0.1, 0.2), col=ROJO, size=26)
        if u > us:
            tache(img, fx, 540, 1420, seg(u, us + 0.35, us + 0.6), 'NO LO BAJES')
    fr.ui.append(ui)
    out = finish(fr, fi)
    if us <= u < us + 0.15:
        out = M.tr_glitch(out, out, 0.5, fi)
    return sacudir(out, t, golpe_k(u, us + 0.1, 0.35), amp=22)


# 11. el truco: Ajustes → General → Actualización de software → actualiza (celular con vida, toques con círculo)
def s_truco(t, fi, u, d):
    ug = wt(11, 5) - 0.12                        # «General»
    ua = wt(11, 6) - 0.12                        # «Actualización de software»
    ui_ = wt(11, 10) - 0.12                      # «actualiza»
    paso = 0 if u < ug + 0.15 else (1 if u < ua + 0.4 else 2)
    kbar = P.eout4(seg(u, ui_, ui_ + 1.0))
    fr = Frame(cam(u, [K(-0.3, 2.6, 30, 8), K(0.3, 2.3, 8, 4), K(ua, 2.2, -8, 4), K(ui_, 2.5, 12, 6), K(6.0, 2.45, 16, 6)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.5)
    draw_objects(fr, celu(scr_ajustes(paso, kbar), ry=4 * math.sin(t * 0.9)))
    # toque: posición de la fila resaltada en la pantalla (coordenadas de la pantalla 420×900 → 3D)
    def pnt(px, py):
        x = (px / 420 - 0.5) * 0.69
        y = P.PH_Y + (0.5 - py / 900) * 1.48
        return fr.cam.p1((x, y, 0.09))
    toques = [(ug, pnt(210, 200 + 2 * 92 + 38)), (ua, pnt(210, 200 + 1 * 92 + 38))]

    def ui(img, fx):
        kicker(img, 'EL TRUCO', 140, seg(u, -0.1, 0.2), col=VERDE, size=34)
        for (u0, (x, y, _)) in toques:
            k = seg(u, u0, u0 + 0.35)
            if 0 < k < 1:
                r = 20 + 50 * k
                ImageDraw.Draw(img).ellipse((x - r, y - r, x + r, y + r), outline=M.scale_c(CYAN, 1 - k), width=5)
                ImageDraw.Draw(fx).ellipse((x - r, y - r, x + r, y + r), outline=M.scale_c(CYAN, 0.6 * (1 - k)), width=12)
        ruta = ['AJUSTES', 'GENERAL', 'ACTUALIZACIÓN DE SOFTWARE'][:paso + 1]
        M.kicker(img, '  ›  '.join(ruta), 200, 1.0, col=AMARILLO, size=24)
        if kbar >= 1:
            check(img, fx, 540, 1420, seg(u, ui_ + 1.0, ui_ + 1.25), 'iOS 15.8 · WHATSAPP SIGUE')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ug, 0.15) + golpe_k(u, ua, 0.15) + golpe_k(u, ui_ + 1.0, 0.25), amp=10)


# 12. mándaselo a tu mamá o a quien todavía tiene el iPhone viejo (el celular gira y el mensaje sale volando)
def s_manda(t, fi, u, d):
    fr = Frame(cam(u, [K(-0.3, 3.4, -40, 10, ty=0.8), K(0.3, 2.9, -10, 6, ty=0.8), K(4.0, 2.85, -6, 6, ty=0.8)], cy=0.66))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    e = P.entrada(u, 0.0, 0.3, 'gira')
    draw_objects(fr, celu(scr_chat(n=6), ry=math.degrees(e['giro']), s=max(0.05, e['escala'])))
    k = seg(u, 0.6, 1.4)
    if 0 < k < 1:
        p = np.array([0.2 + 1.2 * k, 1.2 + 1.0 * k, 0.3])
        dot3(fr, p, r=12, col=CYAN, a=1 - k, glow=1.4)

    def ui(img, fx):
        M.title(img, fx, [('Mándaselo a tu mamá o a quien', 'sans'), ('todavía tiene el iPhone viejo.', 'serif')], 170, seg(u, -0.1, 0.25), size=58)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.3), amp=12)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5), sfx=[]),
           dict(desde=1, fn=s_fecha, tr='deslizar_abajo', sfx=[]),
           dict(desde=2, fn=s_android, tr='cubo', sfx=[]),
           dict(desde=3, fn=s_sistema, tr='zoom', c=(0.5, 0.5), sfx=[]),
           dict(desde=4, fn=s_huecos, tr='glitch', sfx=[]),
           dict(desde=5, fn=s_dos, tr='wipe', sfx=[]),
           dict(desde=6, fn=s_pierde, tr='whip', sfx=[]),
           dict(desde=7, fn=s_error, tr='rompe', c=(0.5, 0.45), sfx=[]),
           dict(desde=8, fn=s_servidor, tr='remolino', sfx=[]),
           dict(desde=9, fn=s_fotos, tr='rebanadas', sfx=[]),
           dict(desde=10, fn=s_modificado, tr='mosaico', sfx=[]),
           dict(desde=11, fn=s_truco, tr='iris', c=(0.5, 0.42), sfx=[]),
           dict(desde=12, fn=s_manda, tr='giro', sfx=[]),
           dict(desde=13, loop=True, tr='flash')]


def _sfx_dinamicos():
    E = ESCENAS
    E[0]['sfx'] = [(-0.25, 'burst', 0.5), (-0.2, 'digital', 0.6), (0.12, 'whoosh', 0.6), (0.27, 'sub', 1.0), (0.27, 'bass', 0.8),
                   (0.45, 'tick', 0.5), (1.5, 'digital', 0.4)]
    uv = wt(1, 11) - 0.15
    E[1]['sfx'] = [(-0.15, 'whoosh', 0.6), (0.25, 'thud', 0.9), (0.25, 'slap', 0.5), (uv, 'whoosh', 0.7)] + \
                  [(uv + 0.04 * i + 0.2, 'tick2', 0.25) for i in range(9)] + [(uv + 0.5, 'bass', 0.8)]
    u6 = wt(2, 6) - 0.12
    E[2]['sfx'] = [(-0.2, 'whoosh', 0.6), (0.1, 'click', 0.5), (u6 - 0.1, 'whoosh', 0.6), (u6 + 0.18, 'thud', 0.7), (u6 + 0.35, 'chime_c', 0.5)]
    us = wt(3, 7) - 0.15
    E[3]['sfx'] = [(-0.2, 'shimmer', 0.6), (0.25, 'chime_a', 0.4)] + [(us + 0.1 + 0.09 * i, 'tick2', 0.22) for i in range(10)] + \
                  [(us + 0.35, 'bass', 0.8)]
    uh, uw = wt(4, 6) - 0.15, wt(4, 9) - 0.12
    E[4]['sfx'] = [(-0.1, 'riser', 0.3), (uh - 0.1, 'burst', 0.4), (uh + 0.2, 'bass', 0.7), (uh + 0.4, 'tick', 0.4), (uw + 0.1, 'digital', 0.5),
                   (uw + 0.3, 'thud', 0.6)]
    u1, u2 = wt(5, 5) - 0.12, wt(5, 12) - 0.12
    E[5]['sfx'] = [(0.05, 'thud', 0.8), (0.2, 'thud', 0.6), (u1 + 0.1, 'click', 0.9), (u1 + 0.35, 'click', 0.7), (u1, 'scribble', 0.5),
                   (u2, 'riser', 0.4), (u2 + 0.9, 'chime_c', 0.6)]
    uo = wt(6, 4) - 0.12
    E[6]['sfx'] = [(0.15, 'digital', 0.5), (0.3, 'bass', 0.7)] + [(uo + 0.35 * i, 'tick', 0.5) for i in range(4)] + [(uo, 'chime_b', 0.5)]
    uc, ur = wt(7, 8) - 0.12, wt(7, 11) - 0.15
    E[7]['sfx'] = [(-0.05, 'sub', 1.0), (uc, 'whoosh', 0.8), (uc + 0.4, 'thud', 0.6), (ur + 0.1, 'bass', 0.9), (ur + 0.2, 'whoosh_suave', 0.6)]
    uv8 = wt(8, 8) - 0.12
    E[8]['sfx'] = [(-0.2, 'whoosh', 0.5), (0.4, 'digital', 0.4), (0.45, 'click', 0.6), (uv8, 'shimmer', 0.6), (uv8 + 0.3, 'chime_c', 0.5)]
    uf, up = wt(9, 9) - 0.12, wt(9, 13) - 0.12
    E[9]['sfx'] = [(0.0, 'tick', 0.4)] + [(uf + 0.05 * j, 'tick2', 0.25) for j in range(9)] + [(up, 'whoosh_suave', 0.7), (up + 0.3, 'bass', 0.8)]
    us10 = wt(10, 10) - 0.15
    E[10]['sfx'] = [(0.1 + 0.15 * i, 'tick2', 0.25) for i in range(int(max(1, us10 - 0.1) / 0.15))] + \
                   [(us10, 'burst', 0.6), (us10 + 0.1, 'sub', 0.9), (us10 + 0.35, 'click', 0.6)]
    ug, ua, ui_ = wt(11, 5) - 0.12, wt(11, 6) - 0.12, wt(11, 10) - 0.12
    E[11]['sfx'] = [(0.0, 'chime_a', 0.4), (ug, 'click', 0.9), (ua, 'click', 0.9)] + \
                   [(ui_ + 0.1 * i, 'tick2', 0.2) for i in range(10)] + [(ui_ + 1.0, 'chime_c', 0.7), (ui_ + 1.0, 'bass', 0.6)]
    E[12]['sfx'] = [(0.0, 'whoosh', 0.6), (0.3, 'thud', 0.6), (0.6, 'whoosh', 0.7), (0.65, 'chime_b', 0.5)]


if __name__ == '__main__':
    T_, DUR_ = montaje.cargar(TEMA)
    if T_:
        montaje.CTX['T'] = T_
        _sfx_dinamicos()
    montaje.cli(globals())
