"""Escenas del tren bala (largo horizontal y Shorts verticales). Cada función devuelve fn(t, fi, u, d) para montaje.py.
Acomodo automático según MOTOR_FORMATO (ver trenbala_lib)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import trenbala_lib as L
from trenbala_lib import (M, P, HZ, W, H, S, Frame, space, draw_objects, finish, line3, dot3, seg, ease, eout, clamp,
                          lerp, pill, WHITE, CYAN, RED, INK, MUTED, texto, titulo, kick, num, velocimetro, reloj, barra,
                          tarjeta_dato, etiqueta, credito, pose, camara, golpe_k, sacudir, geo, CIU, AZUL, BLANCO,
                          AMARILLO, VERDE, ROJO, NARANJA, rec_frame)

DX, DY = (520, 560) if HZ else (540, 1250)
DY2 = 770 if HZ else 1440
GR = 0.025 if HZ else 0.04
FOT = '/home/claude/fotos_tb'
_F = {}


def foto(n):
    if n not in _F:
        im = Image.open(os.path.join(FOT, f'img_tb_{n}.jpg')).convert('RGB')
        if n == 'maglev':      # tapa el logotipo del frente (regla: sin logos)
            d = ImageDraw.Draw(im)
            d.rectangle((1140, 868, 1262, 920), fill=(236, 238, 240))
            im = im.crop((150, 160, 1500, 1034))
        elif n == 'n700s':
            im = im.crop((60, 150, 1880, 700))
        elif n == 'e5':
            im = im.crop((0, 180, 1500, 1150))
        _F[n] = im
    return _F[n]


def fin(fr, fi, flash=0.0, dof=0.0):
    return finish(fr, fi, grain=GR, flash=flash, dof=dof)


def zoom2d(img, u, claves, cx=0.5, cy=0.5):
    p = P.cam_rapida(u, [(a, dict(z=z)) for a, z in claves])
    return M.scale_about(img, p['z'], cx, cy)


def fondo(t, fi, u, ui, claves=None, floor=None, beam=0.0, bokeh=1.0, pal=None, pal_t0=-0.3, pal_cy=0.42,
          pal_ent='golpe', z=None, zc=(0.5, 0.5), flash=0.0):
    """Escena 2D sobre el espacio negro (con palabra de cristal opcional y zoom de golpe)."""
    fr = Frame(camara(u, claves or [(0, pose(6, -20, 18))]))
    space(fr, t, floor=floor, floor_a=0.5, bokeh=bokeh, beam=beam, beam_x=0.5)
    if pal:
        M.cristal(fr.base, fr.fx, pal, u, t0=pal_t0, cy=pal_cy, entrada=pal_ent)
    fr.ui.append(ui)
    img = fin(fr, fi, flash=flash)
    if z:
        img = zoom2d(img, u, z, *zc)
    return img


# =================================================================== MAPA
def _mapa_cam(u, claves):
    return camara(u, claves, cx=0.70 if HZ else 0.5, cy=0.50 if HZ else 0.47, fk=1.5)


def mk_mapa(claves, rutas=(), marcas=(), ciudades=(), pal=None, pal_t0=-0.3, pal_cy=0.30, extra_ui=None, dibuja=None,
            intro=False, punteadas=(), estaciones=()):
    """rutas: [(nombres, frac(u), col)], marcas: [(nombres, frac(u), txt, col)], ciudades: [(nombre, u0, lado)]."""
    def fn(t, fi, u, d):
        if intro and u < 0.55:
            return _tierra(t, fi, u)
        fr = Frame(_mapa_cam(u, claves))
        space(fr, t, floor=None, bokeh=0.8)
        if pal:
            M.cristal(fr.base, fr.fx, pal, u, t0=pal_t0, cy=pal_cy, entrada='golpe')
        L.mapa(fr, dibuja=dibuja(u) if dibuja else 1.0)
        for nombres, ffn, col in rutas:
            L.ruta(fr, nombres, ffn(u), col=col)
        for nombres, ffn, col in punteadas:
            L.ruta(fr, nombres, ffn(u), col=col, punteada=True, t=t)
        cam = fr.cam

        def ui(img, fx):
            for nombre, u0, lado in ciudades:
                L.ciudad_ui(img, fx, cam, nombre, seg(u, u0, u0 + 0.25), lado=lado)
            for nombre, u0 in estaciones:
                L.ciudad_ui(img, fx, cam, nombre, seg(u, u0, u0 + 0.2), lado=-1, size=22, col=(200, 230, 255))
            for nombres, ffn, txt, col in marcas:
                Pp = L.ruta_pts(nombres)
                L.marcador(img, fx, cam, L.en_ruta(Pp, ffn(u)), txt, seg(u, 0.0, 0.2) if u > -0.5 else 1.0, col=col)
            if extra_ui:
                extra_ui(img, fx, u, t)
        fr.ui.append(ui)
        img = fin(fr, fi)
        if intro and u < 0.9:
            img = M.radial_blur(img, 0.25 * (1 - seg(u, 0.62, 0.9)), 0.5, 0.5)
        return img
    return fn


def _tierra(t, fi, u):
    """Caída desde el espacio: Tierra de alambre y crash zoom hacia México."""
    import norte as N
    k = M.ein(seg(u, -0.5, 0.62), 2)
    C = np.array([0, 1.2, 0])
    fr = Frame(M.Cam(target=(0, 1.2, 0), dist=lerp(4.4, 1.6, k), yaw=lerp(30, 8, k), pitch=lerp(6, 22, k),
                     cx=0.5, cy=0.5))
    space(fr, t, floor=None, bokeh=1.2)
    N.earth(fr, t, C, 1.0, 1.9 + u * 0.15)
    # México brilla en la cara de enfrente
    lat, lon = math.radians(21), math.radians(-100)
    pm = C + np.array([math.cos(lat) * math.sin(lon + 1.9), math.sin(lat), math.cos(lat) * math.cos(lon + 1.9)])
    dot3(fr, pm, r=9, col=CYAN, a=1.0, glow=1.2)
    img = fin(fr, fi)
    return M.radial_blur(img, 0.3 * seg(u, 0.2, 0.62), 0.5, 0.5)


def reloj_ui(img, fx, x, y, horas, k, label, col=WHITE, r=None):
    reloj(img, fx, x, y, r or (78 if HZ else 90), horas, k, label, col)


# =================================================================== TREN 3D (escenario genérico)
def mk_tren(claves, ui=None, **kw):
    def fn(t, fi, u, d):
        def _ui(img, fx):
            if ui:
                ui(img, fx, u, t)
        return L.escena_tren(t, fi, u, claves, ui=_ui, **kw)
    return fn


def mk_tren_k(claves, kwf, ui=None, sac=None):
    """Como mk_tren pero los parámetros dependen de u: kwf(u) -> dict. sac: tiempo (u) de sacudida."""
    def fn(t, fi, u, d):
        def _ui(img, fx):
            if ui:
                ui(img, fx, u, t)
        img = L.escena_tren(t, fi, u, claves, ui=_ui, **kwf(u))
        if sac is not None:
            img = sacudir(img, t, golpe_k(u, sac))
        return img
    return fn


# =================================================================== TARJETA DE CAPÍTULO
def mk_capitulo(n, l1, l2, pal, objeto='bala', pal_ent='golpe', yaw=-30):
    """Tarjeta: kicker PARTE N, título, palabra de cristal gigante y el objeto del capítulo entrando de golpe."""
    def fn(t, fi, u, d):
        def ui(img, fx):
            kick(img, f'PARTE {n} DE 6', u, 0.05)
            titulo(img, fx, l1, l2, u, 0.12)
        if objeto == 'maglev':
            fr = Frame(camara(u, [(0, pose(11.5, -28, 6, tx=-1.2, ty=0.5)), (0.5, pose(10.0, -18, 9, tx=-0.6, ty=0.6))]))
            space(fr, t, floor='lines', floor_a=0.35, bokeh=1.0, beam=0.4, beam_x=L.OBJ_CX)
            M.cristal(fr.base, fr.fx, pal, u, t0=-0.25, cy=0.50 if HZ else 0.40, entrada=pal_ent)
            e = P.entrada(u, 0.0, 0.3, 'desliza')
            ms = L.maglev(x=2.0 + e['dy'] * 2, flota=seg(u, 0.25, 0.8)) + L.viga()
            draw_objects(fr, ms)
            fr.ui.append(ui)
            return fin(fr, fi)
        kw = dict(quien='bala' if objeto == 'bala' else ('mx' if objeto == 'mx' else None))
        e = P.entrada(u, 0.0, 0.28, 'desliza')
        return L.escena_tren(t, fi, u, [(0, pose(9.0, yaw, 7, tx=-1.5, ty=0.7)), (0.6, pose(7.8, yaw + 12, 9, tx=-1.0, ty=0.8))],
                             ui=ui, palabra=pal, pal_cy=0.50 if HZ else 0.40, pal_entrada=pal_ent, vel=0.8, xpos=e['dy'] * 2.5, **kw)
    return fn


# =================================================================== GANCHO
def s_bus_sign(t, fi, u, d):
    """Tu camión apenas va llegando a Querétaro: camión en carretera y letrero verde que pasa."""
    fr = Frame(camara(u, [(0, pose(10.0, 44, 9, tx=-0.8, ty=0.9)), (0.4, pose(8.6, 30, 7, tx=-0.9, ty=0.9))]))
    space(fr, t, floor='lines', floor_a=0.45, bokeh=1.0, beam=0.3, beam_x=L.OBJ_CX)
    mov = t * 3.0
    for zs in (-0.75, 0.75):
        line3(fr, [(-14, 0.01, zs), (14, 0.01, zs)], col=(230, 230, 230), w=2.0, a=0.6, glow=0.2)
    for j in range(16):
        xx = -14 + ((j * 1.8 - mov) % 28)
        line3(fr, [(xx, 0.01, 0), (xx + 0.8, 0.01, 0)], col=AMARILLO, w=2.4, a=0.8, glow=0.4)
    e = P.entrada(u, -0.1, 0.25, 'desliza')
    draw_objects(fr, L.camion(x=1.6 + e['dy']))
    sx = 4.5 - ((u * 2.2) % 14)
    cam = fr.cam

    def ui(img, fx):
        x, y, z = cam.p1((sx, 2.6, -1.4))
        if z > 0.3:
            s = 1.5 / z * (5.0 if HZ else 4.0)
            w_, h_ = 260 * s, 110 * s
            d = ImageDraw.Draw(img)
            d.rounded_rectangle((x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), radius=12 * s, fill=(18, 110, 60),
                                outline=(240, 240, 240), width=max(2, int(4 * s)))
            texto(img, fx, x, y - h_ * 0.12, 'Querétaro', int(46 * s), WHITE, 1.0, f='sans', glow=0.1)
            texto(img, fx, x, y + h_ * 0.28, '↑  5 km', int(30 * s), WHITE, 1.0, f='sans', glow=0)
        reloj_ui(img, fx, DX if HZ else 540, (DY - 30) if HZ else 1240, 2.75 + 0.2 * seg(u, 0, 3), seg(u, 0.15, 0.4), 'CAMIÓN · 2 h 45')
        etiqueta(img, fx, 'RECREACIÓN', u)
    fr.ui.append(ui)
    return fin(fr, fi)


def s_siete_horas(t, fi, u, d):
    """De la CDMX a Guadalajara: 7 horas en camión (contador de horas y la ruta)."""
    claves = [(0, pose(4.2, 0, 64, tx=0.32, ty=0, tz=1.24)), (0.5, pose(3.3, -8, 58, tx=0.32, ty=0, tz=1.24))]
    fn = mk_mapa(claves, rutas=[(['CDMX', 'Querétaro', 'Irapuato', 'León', 'Guadalajara'], lambda u: seg(u, 0.1, 1.8), (240, 240, 240))],
                 marcas=[(['CDMX', 'Querétaro', 'Irapuato', 'León', 'Guadalajara'], lambda u: 0.42 * seg(u, 0.1, 3.0), 'CAMIÓN', NARANJA)],
                 ciudades=[('CDMX', 0.0, 1), ('Guadalajara', 0.2, -1)],
                 extra_ui=lambda img, fx, u, t: tarjeta_dato(img, fx, DX if HZ else 540, (DY - 120) if HZ else 1330,
                                                             f'{contador(u, 0.2, 1.4, 0, 7):.0f} h', 'EN CAMIÓN', seg(u, 0.2, 0.5), NARANJA))
    return fn(t, fi, u, d)


def contador(u, a, b, v0, v1):
    return L.contador(u, a, b, v0, v1)


def s_dos_y_media(t, fi, u, d):
    """Un tren bala como el de Japón: unas 2 horas y media (el tren entra de golpe)."""
    def ui(img, fx, u, t):
        kick(img, 'A RITMO DEL NOZOMI DE JAPÓN', u, 0.2)
        etiqueta(img, fx, 'ESTIMACIÓN', u, 0.5)
    e = lambda u: dict(xpos=P.entrada(u, 0.0, 0.3, 'desliza')['dy'] * 3.5, vel=1.4, palabra='2 H 30', pal_cy=0.40,
                       pal_t0=0.3, pal_entrada='zoom', cat=0.4)
    return mk_tren_k([(0, pose(8.5, -42, 6, tx=-1.5, ty=0.8)), (0.35, pose(7.5, -30, 8, tx=-1.0, ty=0.8))], e, ui=ui, sac=0.3)(t, fi, u, d)


def s_preview_sismo(t, fi, u, d):
    """Si tiembla, detecta el sismo y frena solo (adelanto del capítulo 2)."""
    def ui(img, fx):
        box = (60, 70, 900, 330) if HZ else (60, 1080, 1020, 1400)
        L.sismograma(img, fx, box, u, kP=seg(u, 0.3, 0.8), kS=seg(u, 1.4, 2.2), frac=seg(u, 0.0, 2.6))
        if u > 0.9:
            pill(img, fx, 480 if HZ else 540, 390 if HZ else 1000, 'CORTA LA CORRIENTE', seg(u, 0.9, 1.2), size=26, border=ROJO)
    fr_cfg = lambda u: dict(vel=max(0.15, 1.2 - 0.7 * seg(u, 1.0, 3.0)), chisp=seg(u, 1.0, 1.3), cat=1 - seg(u, 0.9, 1.05),
                            palabra='SISMO', pal_t0=-0.3, pal_cy=0.62 if HZ else 0.30, pal_entrada='zoom')
    fn = mk_tren_k([(0, pose(6.5, 32, 10, tx=-0.4, ty=0.8)), (0.9, pose(5.6, 42, 6, tx=-1.2, ty=0.7))], fr_cfg, sac=0.95)

    def fn2(t, fi, u, d):
        img = fn(t, fi, u, d)
        im = Image.fromarray(img)
        fx = Image.new('RGB', im.size)
        ui(im, fx)
        a = np.asarray(im, np.float32) + np.asarray(fx.filter(ImageFilter.GaussianBlur(4)), np.float32) * 0.5
        out = a.clip(0, 255).astype(np.uint8)
        return sacudir(out, t, 0.6 * seg(u, 1.6, 2.0) * (1 - seg(u, 2.4, 3.0)), 14)
    return fn2(t, fi, u, d)


def s_ensambla(t, fi, u, d):
    """¿Qué pasaría si México tuviera uno? El tren se arma solo y salen las 6 partes."""
    fr = Frame(camara(u, [(0, pose(12.5, -36, 14, tx=-1.6, ty=0.8)), (0.7, pose(11.0, -24, 10, tx=-1.4, ty=0.8))],
                      cy=0.70 if HZ else 0.55))
    space(fr, t, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.4, beam_x=L.OBJ_CX)
    ms = L.tren_bala(x=1.6, carros=2)
    k = 1 - P.eout4(seg(u, 0.0, 1.0))
    ms = P.despiece(ms, k, centro=(-2.0, 0.8, 0), fuerza=2.4, giro=0.6)
    L.via(fr, a=0.6)
    draw_objects(fr, ms)
    partes = ['1 · VIAJE', '2 · SISMOS', '3 · VÍA', '4 · FLOTA', '5 · COSTO', '6 · MÉXICO']

    def ui(img, fx):
        titulo(img, fx, '¿Qué pasaría si México', 'tuviera tren bala?', u, 0.15)
        for i, p in enumerate(partes):
            if HZ:
                x, y = 330 + (i % 3) * 330, 300 + (i // 3) * 90
            else:
                x, y = 270 + (i % 2) * 540, 1150 + (i // 2) * 105
            pill(img, fx, x, y, p, seg(u, 0.9 + 0.22 * i, 1.15 + 0.22 * i), size=26)
    fr.ui.append(ui)
    img = fin(fr, fi)
    return sacudir(img, t, golpe_k(u, 1.0), 14)


# =================================================================== PARTE 1: EL VIAJE
RUTA5 = ['CDMX', 'Querétaro', 'Irapuato', 'León', 'Guadalajara']
CAM_RUTA = [(0, pose(4.6, 10, 66, tx=0.32, ty=0, tz=1.24)), (0.45, pose(3.6, -6, 56, tx=0.32, ty=0, tz=1.24))]


def s_intro(t, fi, u, d):
    """Escena 0 (inicio 1, caída desde el espacio): Tierra → México → el tren bala ya está en Guadalajara."""
    def ui(img, fx, u, t):
        titulo(img, fx, 'El tren bala ya llegó.', 'Tu camión va en Querétaro.', u, 0.75)
    fn = mk_mapa([(0.62, pose(9.0, 0, 80, tx=0.6, ty=0, tz=1.0)), (1.0, pose(4.4, -4, 60, tx=0.32, ty=0, tz=1.24))],
                 rutas=[(RUTA5, lambda u: 1.0, CYAN)],
                 marcas=[(RUTA5, lambda u: 1.0, 'TREN BALA', CYAN), (RUTA5, lambda u: 0.27, 'CAMIÓN', NARANJA)],
                 ciudades=[('CDMX', 0.7, 1), ('Querétaro', 0.8, 1), ('Guadalajara', 0.75, -1)],
                 pal='TREN BALA', pal_t0=-0.6, pal_cy=0.70 if HZ else 0.70, extra_ui=ui, intro=True)
    img = fn(t, fi, u, d)
    return sacudir(img, t, golpe_k(u, 0.62), 16)


def s_540(t, fi, u, d):
    fn = mk_mapa(CAM_RUTA, rutas=[(RUTA5, lambda u: seg(u, 0.2, 2.2), CYAN)],
                 ciudades=[('CDMX', 0.0, 1), ('Querétaro', 0.6, 1), ('León', 1.3, 1), ('Guadalajara', 1.9, -1)],
                 extra_ui=lambda img, fx, u, t: tarjeta_dato(img, fx, DX, DY - 100 if HZ else 1330,
                                                             f'{contador(u, 0.2, 2.2, 0, 540):.0f} km', 'CDMX → GUADALAJARA', seg(u, 0.1, 0.4)))
    return fn(t, fi, u, d)


def s_casetas(t, fi, u, d):
    """En auto, 5 h 20 min y 10 casetas: el auto pasa casetas que se van contando."""
    fr = Frame(camara(u, [(0, pose(9.0, -60, 22, tx=0.0, ty=0.5)), (0.5, pose(8.0, -48, 16, tx=0.2, ty=0.5))]))
    space(fr, t, floor='lines', floor_a=0.35, bokeh=1.0)
    mov = u * 5.0
    for zs in (-0.7, 0.7):
        line3(fr, [(-16, 0.01, zs), (16, 0.01, zs)], col=(220, 220, 220), w=2.0, a=0.5)
    n_c = 0
    for j in range(10):
        xx = 6 + j * 2.6 - mov
        if xx < 1.2:
            n_c += 1
        if -16 < xx < 16:
            for zs in (-1.0, 1.0):
                line3(fr, [(xx, 0, zs), (xx, 1.5, zs)], col=AMARILLO, w=2.2, a=0.8, glow=0.5)
            line3(fr, [(xx, 1.5, -1.1), (xx, 1.5, 1.1)], col=AMARILLO, w=3.0, a=0.9, glow=0.7)
    car = [named_box(1.6, 0.45, 0.8, (200, 40, 40), 1.0, 0.18, 0), named_box(0.9, 0.36, 0.72, (30, 34, 44), 0.9, 0.62, 0)]
    for xw in (0.5, 1.5):
        for zz in (-0.4, 0.4):
            car.append(M.named(L.M3.cyl(0.16, 0.1, (20, 20, 24), n=14, shadow=0).tf(rx=90, t=(xw, 0.16, zz)), 'rueda'))
    draw_objects(fr, car)

    def ui(img, fx):
        tarjeta_dato(img, fx, DX - (170 if HZ else 230), DY - 120 if HZ else 1280, '5 h 20', 'EN AUTO, SIN PARAR', seg(u, 0.1, 0.4))
        tarjeta_dato(img, fx, DX + (170 if HZ else 230), DY - 120 if HZ else 1280, f'{min(10, n_c)}', 'CASETAS', seg(u, 0.5, 0.8), AMARILLO)
    fr.ui.append(ui)
    return fin(fr, fi)


def named_box(sx, sy, sz, col, x, y, z, name='cuerpo', gloss=0.6):
    return M.named(L.M3.box(sx, sy, sz, col, shadow=0, gloss=gloss).tf(t=(x, y, z)), name, gloss=gloss, rim=0.7)


def s_camion7(t, fi, u, d):
    """En camión, unas 7 horas: camión de lado con el reloj corriendo."""
    fr = Frame(camara(u, [(0, pose(8.5, -10, 6, tx=-0.6, ty=0.9)), (0.35, pose(7.6, 4, 8, tx=-0.8, ty=0.9))]))
    space(fr, t, floor='dots', floor_a=0.45, bokeh=1.0, beam=0.35, beam_x=L.OBJ_CX)
    for j in range(14):
        xx = -14 + ((j * 2.0 - t * 4) % 28)
        line3(fr, [(xx, 0.01, 0.9), (xx + 1.0, 0.01, 0.9)], col=AMARILLO, w=2.4, a=0.8, glow=0.4)
    e = P.entrada(u, 0.0, 0.25, 'desliza')
    draw_objects(fr, L.camion(x=1.8 - e['dy'] * 2))

    def ui(img, fx):
        reloj_ui(img, fx, DX, DY - 60 if HZ else 1250, 7 * seg(u, 0.1, 1.6), seg(u, 0.05, 0.3), 'EN CAMIÓN · ~7 h', NARANJA)
    fr.ui.append(ui)
    return fin(fr, fi)


def s_nozomi(t, fi, u, d):
    """Japón: el Nozomi hace Tokio–Osaka, 515 km, en 2 h 21 min (foto real + diagrama)."""
    def ui(img, fx):
        if HZ:
            M.photo_card(img, fx, foto('n700s'), 1360, 380, 880, t - u + 0.05, t, caption='N700S · TOKAIDO · CC0 MaedaAkihiko', angle0=-8)
            x0, x1, y = 110, 820, 300
        else:
            M.photo_card(img, fx, foto('n700s'), 540, 1180, 900, t - u + 0.05, t, caption='N700S · TOKAIDO · CC0 MaedaAkihiko', angle0=-8)
            x0, x1, y = 120, 960, 420
        k = seg(u, 0.4, 1.4)
        d = ImageDraw.Draw(img)
        d.line([(x0, y), (lerp(x0, x1, k), y)], fill=CYAN, width=6)
        ImageDraw.Draw(fx).line([(x0, y), (lerp(x0, x1, k), y)], fill=M.scale_c(CYAN, 0.6), width=14)
        for xx, nm, kk in ((x0, 'TOKIO', seg(u, 0.2, 0.4)), (x1, 'OSAKA', seg(u, 1.3, 1.5))):
            if kk > 0:
                d.ellipse((xx - 14, y - 14, xx + 14, y + 14), fill=M.scale_c(WHITE, kk))
                texto(img, fx, xx, y - 52, nm, 34, WHITE, kk, f='mono', glow=0.3)
        texto(img, fx, (x0 + x1) / 2, y + 60, '515 km', 46, CYAN, seg(u, 0.8, 1.1), f='mono', glow=0.4)
        tarjeta_dato(img, fx, (x0 + x1) / 2, y + 250 if HZ else y + 220, '2 h 21', 'NOZOMI · EL MÁS RÁPIDO', seg(u, 1.4, 1.7))
    return fondo(t, fi, u, ui, z=[(0, 1.0), (1.4, 1.06)])


def s_estimacion(t, fi, u, d):
    """A ese ritmo, Guadalajara te quedaría a unas 2 h 30: el tren corre por la ruta."""
    fn = mk_mapa([(0, pose(3.2, -20, 50, tx=0.6, ty=0, tz=1.3)), (0.5, pose(4.0, 0, 60, tx=0.32, ty=0, tz=1.24))],
                 rutas=[(RUTA5, lambda u: P.eout4(seg(u, 0.1, 2.4)), CYAN)],
                 marcas=[(RUTA5, lambda u: P.eout4(seg(u, 0.1, 2.4)), 'TREN BALA', CYAN)],
                 ciudades=[('CDMX', 0.0, 1), ('Guadalajara', 0.3, -1)],
                 extra_ui=lambda img, fx, u, t: (reloj_ui(img, fx, DX, DY - 90 if HZ else 1260, 2.5 * P.eout4(seg(u, 0.1, 2.4)),
                                                          seg(u, 0.0, 0.3), '≈ 2 h 30', CYAN), etiqueta(img, fx, 'ESTIMACIÓN', u)))
    return fn(t, fi, u, d)


def s_torta(t, fi, u, d):
    """Desayunas en la CDMX y almuerzas una torta ahogada en Guadalajara: reloj de 8:00 a 10:30."""
    def ui(img, fx):
        h = 8 + 2.5 * P.eout4(seg(u, 0.6, 2.2))
        cx = (L.OBJ_CX * W) if HZ else 540
        cy = 470 if HZ else 860
        reloj(img, fx, cx, cy, 190 if HZ else 230, h, seg(u, 0.0, 0.3))
        texto(img, fx, cx, cy + (260 if HZ else 310), f'{int(h):02d}:{int((h % 1) * 60):02d}', 64, CYAN, seg(u, 0.1, 0.3), f='mono')
        pill(img, fx, DX if HZ else 300, 420 if HZ else 1330, 'DESAYUNO · CDMX', seg(u, 0.1, 0.35), size=28, border=WHITE)
        pill(img, fx, DX if HZ else 780, 560 if HZ else 1430, 'TORTA AHOGADA · GDL', seg(u, 1.6, 1.9), size=28, border=ROJO)
        etiqueta(img, fx, 'EJEMPLO', u)
    return fondo(t, fi, u, ui, z=[(0, 1.08), (0.4, 1.0)])


def s_mientras(t, fi, u, d):
    """Mientras, tu camión apenas va llegando a Querétaro (el mapa con los dos)."""
    fn = mk_mapa([(0, pose(3.0, 10, 50, tx=0.9, ty=0, tz=1.35)), (0.5, pose(4.4, -6, 62, tx=0.32, ty=0, tz=1.24))],
                 rutas=[(RUTA5, lambda u: 1.0, CYAN), (['CDMX', 'Querétaro'], lambda u: 1.0, NARANJA)],
                 marcas=[(RUTA5, lambda u: 1.0, 'TREN BALA · 2 h 30', CYAN), (RUTA5, lambda u: 0.27 * seg(u, 0, 0.6), 'CAMIÓN · 2 h 45', NARANJA)],
                 ciudades=[('Querétaro', 0.1, 1), ('Guadalajara', 0.0, -1)], pal='QUERÉTARO', pal_t0=0.2, pal_cy=0.72 if HZ else 0.72)
    return fn(t, fi, u, d)


# =================================================================== PARTE 2: CUANDO TIEMBLA
def s_cinturon(t, fi, u, d):
    """Japón y México: los dos en el Cinturón de Fuego (globo de alambre con el anillo rojo)."""
    import norte as N
    fr = Frame(M.Cam(target=(0, 1.2, 0), dist=lerp(3.6, 3.0, P.eout4(seg(u, 0, 0.5))), yaw=0, pitch=8 + 4 * u,
                     cx=L.OBJ_CX, cy=0.5))
    space(fr, t, floor=None, bokeh=1.0)
    C = np.array([0, 1.2, 0])
    spin = 3.0 + 0.12 * u
    N.earth(fr, t, C, 1.0, spin)
    import demo_estilo as D
    k = seg(u, 0.3, 1.6)
    pts = []
    for la, lo in [(60, 150), (50, 157), (40, 143), (35, 140), (25, 125), (13, 123), (0, 127), (-10, 150), (-20, 170),
                   (-35, 178), (-45, -175), (-55, -70), (-40, -73), (-20, -71), (-5, -81), (8, -84), (14, -92),
                   (17, -101), (23, -107), (34, -119), (45, -125), (55, -135), (60, -150), (55, -165), (52, 175), (58, 162)]:
        a, b = math.radians(la), math.radians(lo)
        pts.append(np.array([math.cos(a) * math.cos(b), math.sin(a), math.cos(a) * math.sin(b)]))
    P2 = D._rot(np.array(pts), spin)
    camdir = M.norm(fr.cam.pos - C)
    n = max(2, int(len(P2) * k))
    for p0, p1 in zip(P2[:n - 1], P2[1:n]):
        if (p0 @ camdir) > -0.1:
            line3(fr, [C + p0 * 1.01, C + p1 * 1.01], col=ROJO, w=3.0, a=0.9, glow=1.0)

    def ui(img, fx):
        kick(img, 'CINTURÓN DE FUEGO DEL PACÍFICO', u, 0.3)
        tarjeta_dato(img, fx, DX, DY - 60 if HZ else 1330, 'MÉXICO + JAPÓN', 'TIEMBLA EN LOS DOS', seg(u, 0.8, 1.1), ROJO,
                     size=64 if HZ else 72)
    fr.ui.append(ui)
    return fin(fr, fi)


def s_sensores(t, fi, u, d):
    """Japón puso sismógrafos junto a la vía y en la costa (cajas que laten a lo largo de la vía)."""
    def extra(u):
        ms = []
        for j, xx in enumerate((-9, -5, -1, 3, 7)):
            b = named_box(0.35, 0.5, 0.35, (60, 70, 86), xx, 0, -1.2, name='sensor')
            b.glow = M.scale_c(CYAN, 0.5 + 0.5 * math.sin(t * 6 + j)) if u > 0.2 + 0.15 * j else None
            ms.append(b)
        return ms

    def ui(img, fx, u, t):
        kick(img, 'SISMÓGRAFOS · VÍA Y COSTA', u, 0.1)
        pill(img, fx, DX, DY - 40 if HZ else 1300, 'DETECTAN EL SISMO', seg(u, 0.8, 1.1), size=30)
    return L.escena_tren(t, fi, u, [(0, pose(11, -64, 16, tx=-1.5, ty=0.6)), (0.5, pose(10, -50, 20, tx=-0.8, ty=0.5))],
                         ui=lambda img, fx: ui(img, fx, u, t), extra=extra, vel=0.6, palabra=None)


def mk_corte(kp, ks, corr=lambda u: 1.0, pal=None, pal_t0=0.2, kick_txt='', extra=None, sac=None, z=None):
    """Corte sísmico + sismograma. kp/ks/corr: funciones de u."""
    def fn(t, fi, u, d):
        def ui(img, fx):
            if HZ:
                box, sbox = (80, 300, 1840, 860), (1180, 70, 1840, 270)
            else:
                box, sbox = (40, 820, 1040, 1480), (60, 420, 1020, 700)
            L.corte_sismico(img, fx, box, u, kP=kp(u), kS=ks(u), corriente=corr(u))
            L.sismograma(img, fx, sbox, u, kP=kp(u), kS=ks(u), frac=seg(u, 0, 2.5))
            if kick_txt:
                kick(img, kick_txt, u, 0.1, cx=TX0, y=110 if HZ else 300)
            if extra:
                extra(img, fx, u, t)
        img = fondo(t, fi, u, ui, pal=pal, pal_t0=pal_t0, pal_cy=0.62 if HZ else 0.62, z=z or [(0, 1.0), (0.6, 1.04)])
        if sac is not None:
            img = sacudir(img, t, sac(u), 18)
        return img
    return fn


TX0 = 470 if HZ else 540


def _ui_corriente(img, fx, u, t):
    pill(img, fx, DX if HZ else 540, 200 if HZ else 760, '1 s · CORTA LA CORRIENTE', seg(u, 0.5, 0.8), size=30, border=AMARILLO)


def s_corte_luz(t, fi, u, d):
    """El sistema detecta la onda P en 1 s y corta la corriente (la catenaria se apaga con chispazo)."""
    kw = lambda u: dict(vel=1.0, cat=1.0 - seg(u, 0.7, 0.85), palabra=None)
    fn = mk_tren_k([(0, pose(7.0, -70, 16, tx=-1.5, ty=1.3)), (0.6, pose(6.2, -55, 10, tx=-1.8, ty=1.4))], kw,
                   ui=lambda img, fx, u, t: (_ui_corriente(img, fx, u, t),
                                             tarjeta_dato(img, fx, DX, DY + 40 if HZ else 1300, 'OFF', 'CATENARIA', seg(u, 0.8, 1.0), ROJO)),
                   sac=0.75)

    def g(t, fi, u, d):
        img = fn(t, fi, u, d)
        if 0.7 <= u < 0.9:
            img = (img.astype(np.float32) + 120 * (1 - seg(u, 0.7, 0.9))).clip(0, 255).astype(np.uint8)
        return img
    return g(t, fi, u, d)


def s_frena_solo(t, fi, u, d):
    kw = lambda u: dict(vel=max(0.05, 1.3 - 1.25 * seg(u, 0.1, 2.6)), chisp=seg(u, 0.1, 0.3) * (1 - seg(u, 2.2, 2.6)), cat=0.0)

    def ui(img, fx, u, t):
        velocimetro(img, fx, DX, DY - 120 if HZ else 1270, 150 if HZ else 170, 300 * (1 - P.eout4(seg(u, 0.1, 2.8)) * 0.85), 360,
                    seg(u, 0.0, 0.3))
        pill(img, fx, DX, (DY + 130) if HZ else 1520, 'FRENO AUTOMÁTICO', seg(u, 0.4, 0.7), size=26, border=ROJO)
    return mk_tren_k([(0, pose(6.0, 38, 6, tx=-1.5, ty=0.6)), (0.4, pose(5.2, 52, 4, tx=-2.2, ty=0.5))], kw, ui=ui)(t, fi, u, d)


def s_2011(t, fi, u, d):
    """2011: cortó la corriente de 12 a 15 s antes del golpe fuerte (línea de tiempo)."""
    def ui(img, fx):
        x0, x1 = (120, 1800) if HZ else (90, 990)
        y = 600 if HZ else 1060
        kick(img, '11 · MARZO · 2011 · MAGNITUD 9.0', u, 0.05, cx=W / 2, y=40 if HZ else 300)
        k = seg(u, 0.2, 1.6)
        dd = ImageDraw.Draw(img)
        dd.line([(x0, y), (lerp(x0, x1, k), y)], fill=(200, 200, 210), width=4)
        xa = lerp(x0, x1, 0.18)
        xb = lerp(x0, x1, 0.82)
        if k > 0.18:
            dd.line([(xa, y - 40), (xa, y + 40)], fill=AMARILLO, width=6)
            texto(img, fx, xa, y - 80, 'CORTE', 34, AMARILLO, seg(u, 0.4, 0.6), f='mono')
        if k > 0.82:
            dd.line([(xb, y - 40), (xb, y + 40)], fill=ROJO, width=6)
            texto(img, fx, xb, y - 80, 'GOLPE FUERTE', 34, ROJO, seg(u, 1.4, 1.6), f='mono')
        kk = seg(u, 1.5, 1.9)
        if kk > 0:
            ImageDraw.Draw(fx).line([(xa, y), (xb, y)], fill=M.scale_c(CYAN, 0.6 * kk), width=14)
            num(img, fx, '12–15 s', (xa + xb) / 2, y + (140 if HZ else 170), 110 if HZ else 130, kk, CYAN)
    return fondo(t, fi, u, ui, pal='2011', pal_t0=-0.2, pal_cy=0.25 if HZ else 0.33, pal_ent='sube', z=[(0, 1.0), (1.5, 1.07)])


def s_19trenes(t, fi, u, d):
    """19 trenes en marcha: ninguno se descarriló (19 fichas que frenan y se ponen verdes)."""
    def ui(img, fx):
        cols, rows = (7, 3) if HZ else (4, 5)
        x0, y0 = (300, 260) if HZ else (180, 520)
        sx, sy = (220, 170) if HZ else (240, 180)
        for i in range(19):
            c, r = i % cols, i // cols
            x, y = x0 + c * sx, y0 + r * sy
            k = seg(u, 0.1 + 0.05 * i, 0.3 + 0.05 * i)
            ok = seg(u, 1.6 + 0.04 * i, 1.8 + 0.04 * i)
            col = M.mixc(WHITE, VERDE, ok)
            if k > 0:
                dd = ImageDraw.Draw(img)
                w_ = max(80.0, 150 * P.resorte(k))
                dd.rounded_rectangle((x - w_ / 2, y - 22, x + w_ / 2 - 30, y + 22), radius=12, outline=col, width=4)
                dd.polygon([(x + w_ / 2 - 30, y - 22), (x + w_ / 2 + 10, y + 22), (x + w_ / 2 - 30, y + 22)], outline=col)
                if ok > 0.5:
                    texto(img, fx, x + 10, y + 52, '✓', 34, VERDE, ok, f='sans', glow=0.5)
        num(img, fx, f'{int(contador(u, 0.1, 1.1, 0, 19))}', W - 260 if HZ else 540, 640 if HZ else 1330, 200, seg(u, 0.1, 0.3))
        texto(img, fx, W - 260 if HZ else 540, 790 if HZ else 1470, 'NINGUNO SE DESCARRILÓ', 30, VERDE, seg(u, 1.7, 2.0), f='mono', glow=0.4)
    return fondo(t, fi, u, ui, z=[(0, 1.05), (0.5, 1.0)])


def s_ojo(t, fi, u, d):
    """Pero ojo: frenar no es inmediato (segundo gancho): el tren sigue de largo con chispas y aviso rojo."""
    kw = lambda u: dict(vel=1.2, chisp=1.0, cat=0.0, palabra='¡OJO!', pal_t0=0.0, pal_cy=0.40 if HZ else 0.30, pal_entrada='golpe')

    def ui(img, fx, u, t):
        pill(img, fx, DX, DY + 60 if HZ else 1330, 'FRENAR NO ES INMEDIATO', seg(u, 0.3, 0.6), size=30, border=ROJO)
    return mk_tren_k([(0, pose(4.2, 70, 4, tx=0.6, ty=0.7)), (0.35, pose(6.5, 60, 8, tx=-0.5, ty=0.8))], kw, ui=ui, sac=0.02)(t, fi, u, d)


def s_4km(t, fi, u, d):
    """A 360 km/h, un tren de pruebas necesitó unos 4 km para detenerse (regla con cota y velocímetro)."""
    def ui(img, fx):
        x0, x1 = (110, 1810) if HZ else (70, 1010)
        y = 650 if HZ else 1050
        k = P.eout4(seg(u, 0.3, 2.6))
        dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        dd.line([(x0, y), (x1, y)], fill=(120, 122, 130), width=3)
        for j in range(5):
            xx = lerp(x0, x1, j / 4)
            dd.line([(xx, y - 18), (xx, y + 18)], fill=(200, 200, 210), width=3)
            texto(img, fx, xx, y + 46, f'{j} km', 26, MUTED, 1.0, f='mono', glow=0)
        xt = lerp(x0, x1, k)
        dd.line([(x0, y - 4), (xt, y - 4)], fill=ROJO, width=8)
        df.line([(x0, y - 4), (xt, y - 4)], fill=M.scale_c(ROJO, 0.6), width=18)
        dd.rounded_rectangle((xt - 90, y - 70, xt + 30, y - 30), radius=14, fill=BLANCO)
        dd.polygon([(xt + 30, y - 70), (xt + 80, y - 30), (xt + 30, y - 30)], fill=BLANCO)
        dd.line([(xt - 90, y - 52), (xt + 50, y - 52)], fill=AZUL, width=6)
        velocimetro(img, fx, DX if HZ else 540, 330 if HZ else 650, 150 if HZ else 170, 360 * (1 - k), 400, seg(u, 0.0, 0.3), warn=200)
    return fondo(t, fi, u, ui, z=[(0, 1.0), (2.0, 1.05)])


def s_orejas(t, fi, u, d):
    """Abriendo unas aletas en el techo, como orejas de gato."""
    kw = lambda u: dict(vel=1.0 - 0.6 * seg(u, 0.3, 2.5), aletas=P.resorte(seg(u, 0.3, 0.8)), cat=0.0)

    def ui(img, fx, u, t):
        pill(img, fx, DX, DY - 60 if HZ else 1300, 'ALETAS DE AIRE', seg(u, 0.5, 0.8), size=30, border=ROJO)
        etiqueta(img, fx, 'TREN DE PRUEBAS · RECREACIÓN', u)
    return mk_tren_k([(0, pose(6.0, -40, 30, tx=-2.0, ty=1.2)), (0.35, pose(5.0, -24, 22, tx=-2.4, ty=1.2))], kw, ui=ui)(t, fi, u, d)


def pantalla_alerta(seg_rest, k_on):
    def dib(d, im):
        w, h = im.size
        if k_on > 0.01:
            d.rectangle((0, 70, w, h - 40), fill=(int(140 * k_on), 12, 12))
        d.text((w / 2, 240), 'ALERTA', font=M.font('sansx', 66), fill=(255, 255, 255), anchor='mm')
        d.text((w / 2, 320), 'SÍSMICA', font=M.font('sansx', 66), fill=(255, 255, 255), anchor='mm')
        d.text((w / 2, 520), f'{seg_rest:02d}', font=M.font('mono', 180), fill=(255, 230, 120), anchor='mm')
        d.text((w / 2, 650), 'SEGUNDOS', font=M.font('mono', 34), fill=(255, 255, 255), anchor='mm')
        d.text((w / 2, 760), 'EJEMPLO', font=M.font('mono', 26), fill=(255, 200, 200), anchor='mm')
    return P.pantalla(dib)


def s_alerta60(t, fi, u, d):
    """Tu alerta sísmica te da unos 60 s si el sismo viene de la costa (celular con vida)."""
    fr = Frame(camara(u, [(0, pose(3.0, -28, 4, tx=0.0, ty=P.PH_Y + 0.15)), (0.5, pose(2.6, -10, 2, tx=0.0, ty=P.PH_Y + 0.15))],
                      cy=None if HZ else 0.45))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.5, beam_x=L.OBJ_CX)
    M.cristal(fr.base, fr.fx, '60 S', u, t0=0.4, cy=0.42 if HZ else 0.26, entrada='sube')
    rest = max(0, 60 - int(max(0.0, u - 0.3) * 6))
    e = P.entrada(u, 0.0, 0.25, 'gira')
    ph = P.celular(pantalla_alerta(rest, 0.6 + 0.4 * math.sin(t * 8) ** 2), ry=math.degrees(e['giro']) * 0.3 - 12, rz=0)
    draw_objects(fr, ph)

    def ui(img, fx):
        kick(img, 'SASMEX · SISMO EN LA COSTA', u, 0.1)
        pill(img, fx, DX if HZ else 540, 760 if HZ else 1460, 'AVISO EN LA CDMX', seg(u, 0.6, 0.9), size=26, border=AMARILLO)
    fr.ui.append(ui)
    img = fin(fr, fi)
    return sacudir(img, t, 0.35 * (0.5 + 0.5 * math.sin(t * 3)), 6)


def s_uno(t, fi, u, d):
    """Al tren bala le basta uno: 60 s contra 1 s."""
    def ui(img, fx):
        if HZ:
            tarjeta_dato(img, fx, 560, 470, '60 s', 'TU ALERTA', seg(u, 0.0, 0.25), AMARILLO, size=150)
            tarjeta_dato(img, fx, 1360, 470, '1 s', 'EL TREN BALA', seg(u, 0.5, 0.8), CYAN, size=230)
        else:
            tarjeta_dato(img, fx, 540, 560, '60 s', 'TU ALERTA', seg(u, 0.0, 0.25), AMARILLO, size=170)
            tarjeta_dato(img, fx, 540, 1080, '1 s', 'EL TREN BALA', seg(u, 0.5, 0.8), CYAN, size=260)
    img = fondo(t, fi, u, ui, z=[(0, 1.0), (0.5, 1.08)])
    return sacudir(img, t, golpe_k(u, 0.65), 18)


def s_descarrila(t, fi, u, d):
    """2004: un sismo sacó de la vía 8 de 10 vagones (10 vagones de lado; 8 se ladean en rojo)."""
    def ui(img, fx):
        n = 10
        x0, x1 = (100, 1820) if HZ else (60, 1020)
        y = 520 if HZ else 980
        wv = (x1 - x0) / n
        dd = ImageDraw.Draw(img)
        dd.line([(x0, y + 34), (x1, y + 34)], fill=(160, 160, 170), width=4)
        for i in range(n):
            k = seg(u, 0.1 + 0.04 * i, 0.3 + 0.04 * i)
            if k <= 0:
                continue
            off = i in (1, 2, 3, 4, 5, 6, 7, 8)
            kk = seg(u, 1.0 + 0.06 * i, 1.4 + 0.06 * i) if off else 0
            ang = 14 * kk * (1 if i % 2 else -1)
            lay = Image.new('RGBA', (int(wv - 8), 60), (0, 0, 0, 0))
            dl = ImageDraw.Draw(lay)
            col = M.mixc(BLANCO, ROJO, kk)
            dl.rounded_rectangle((0, 0, lay.width - 1, 46), radius=12, fill=col + (255,))
            dl.line([(6, 30), (lay.width - 6, 30)], fill=AZUL + (255,), width=5)
            lay = lay.rotate(ang, expand=True, resample=Image.BICUBIC)
            img.paste(lay, (int(x0 + i * wv + 4), int(y - 20 + 26 * kk)), lay)
        num(img, fx, '8 de 10', DX if HZ else 540, 280 if HZ else 660, 120 if HZ else 140, seg(u, 1.3, 1.6), ROJO)
        kick(img, '23 · OCTUBRE · 2004 · NIIGATA', u, 0.1, cx=W / 2, y=110 if HZ else 420)
    img = fondo(t, fi, u, ui, z=[(0, 1.0), (1.2, 1.06)])
    return sacudir(img, t, seg(u, 0.9, 1.1) * (1 - seg(u, 1.6, 2.0)), 16)


def s_154(t, fi, u, d):
    """Con 154 personas a bordo. Nadie salió herido (154 puntos que se ponen verdes)."""
    def ui(img, fx):
        cols = 22 if HZ else 14
        x0, y0 = (220, 240) if HZ else (110, 520)
        sp = 54 if HZ else 62
        dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        for i in range(154):
            k = seg(u, 0.05 + 0.006 * i, 0.15 + 0.006 * i)
            if k <= 0:
                continue
            ok = seg(u, 1.6 + 0.003 * i, 1.8 + 0.003 * i)
            x, y = x0 + (i % cols) * sp, y0 + (i // cols) * sp
            col = M.mixc(WHITE, VERDE, ok)
            r = 11 * P.resorte(k)
            dd.ellipse((x - r, y - r, x + r, y + r), fill=col)
            if ok > 0.5:
                df.ellipse((x - 2 * r, y - 2 * r, x + 2 * r, y + 2 * r), fill=M.scale_c(VERDE, 0.3))
        num(img, fx, f'{int(contador(u, 0.05, 1.0, 0, 154))}', W / 2, 700 if HZ else 1260, 150 if HZ else 170, seg(u, 0.05, 0.2))
        texto(img, fx, W / 2, 820 if HZ else 1410, '0 HERIDOS', 44, VERDE, seg(u, 1.7, 2.0), f='mono', glow=0.5)
    return fondo(t, fi, u, ui, z=[(0, 1.06), (0.6, 1.0)])


def s_62(t, fi, u, d):
    """En 62 años, ningún pasajero ha muerto por choque o descarrilamiento del tren bala."""
    def ui(img, fx, u, t):
        tarjeta_dato(img, fx, DX, DY - 140 if HZ else 1220, '62 años', 'DESDE EL 1-OCT-1964', seg(u, 0.1, 0.4))
        tarjeta_dato(img, fx, DX, DY + 110 if HZ else 1450, '0', 'PASAJEROS MUERTOS POR CHOQUE O DESCARRILAMIENTO', seg(u, 1.4, 1.7), VERDE, size=90)
    kw = lambda u: dict(vel=1.0, cat=0.6)
    return mk_tren_k([(0, pose(9.0, -150, 10, tx=-3.0, ty=0.8)), (0.6, pose(8.0, -140, 8, tx=-3.4, ty=0.8))], kw, ui=ui)(t, fi, u, d)


# =================================================================== PARTE 3: EL SECRETO DE LOS 300
def s_via_truco(t, fi, u, d):
    """La vía es la mitad del truco: la cámara baja a la vía mientras pasa el tren."""
    def ui(img, fx, u, t):
        pill(img, fx, DX, DY - 80 if HZ else 1280, 'LA VÍA = 50 % DEL TRUCO', seg(u, 0.6, 0.9), size=30)
    kw = lambda u: dict(vel=1.6, cat=0.5, xpos=-4.0 + 9.0 * seg(u, 0.0, 3.5))
    return mk_tren_k([(0, pose(5.5, -10, 2, tx=2.5, ty=0.3)), (0.6, pose(6.5, -30, 12, tx=0.5, ty=0.4))], kw, ui=ui)(t, fi, u, d)


def mk_curva(circulo=False):
    """Vista desde arriba: curva de 4 km de radio (y la vuelta completa de 25 km)."""
    def fn(t, fi, u, d):
        def ui(img, fx):
            cx, cy = (L.OBJ_CX * W, 560) if HZ else (540, 1020)
            R = 330 if HZ else 380
            dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
            a_end = 90 if not circulo else 90 + 360 * P.eout4(seg(u, 0.2, 2.4))
            box = (cx - R, cy - R, cx + R, cy + R)
            dd.arc(box, 0, min(a_end, 90 + 360), fill=CYAN, width=8)
            df.arc(box, 0, min(a_end, 90 + 360), fill=M.scale_c(CYAN, 0.6), width=18)
            if not circulo:
                k = seg(u, 0.5, 1.2)
                xe, ye = cx + R * k, cy
                dd.line([(cx, cy), (xe, ye)], fill=AMARILLO, width=4)
                dd.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=AMARILLO)
                texto(img, fx, cx + R / 2, cy - 36, 'RADIO 4 km', 34, AMARILLO, seg(u, 1.0, 1.3), f='mono')
                ft = seg(u, 0.0, 3.0)
                ang = math.radians(90 * ft)
                tx_, ty_ = cx + R * math.cos(ang), cy + R * math.sin(ang)
                dd.ellipse((tx_ - 16, ty_ - 16, tx_ + 16, ty_ + 16), fill=BLANCO)
                df.ellipse((tx_ - 30, ty_ - 30, tx_ + 30, ty_ + 30), fill=M.scale_c(CYAN, 0.5))
                tarjeta_dato(img, fx, DX if HZ else 540, 330 if HZ else 520, '4 km', 'RADIO MÍNIMO · LÍNEAS NUEVAS', seg(u, 1.2, 1.5), AMARILLO)
            else:
                tarjeta_dato(img, fx, DX if HZ else 540, 330 if HZ else 520,
                             f'{contador(u, 0.2, 2.4, 6.3, 25.1):.0f} km', 'UNA VUELTA COMPLETA', seg(u, 0.1, 0.4), CYAN)
                etiqueta(img, fx, '2 × π × 4 km', u, 0.8)
        return fondo(t, fi, u, ui, claves=[(0, pose(7, 0, 70))], floor='dots', z=[(0, 1.05), (0.5, 1.0)] if not circulo else [(0, 1.0), (1.5, 0.94)])
    return fn


def s_vaso(t, fi, u, d):
    """A 300 por hora, la curva no te avienta: el agua del vaso casi no se mueve."""
    fr = Frame(camara(u, [(0, pose(2.6, -20, 14, tx=0, ty=0.9)), (0.45, pose(2.2, -6, 10, tx=0, ty=0.9))]))
    space(fr, t, floor='lines', floor_a=0.35, bokeh=1.3, beam=0.5, beam_x=L.OBJ_CX)
    M.cristal(fr.base, fr.fx, 'SUAVE', u, t0=-0.2, cy=0.40 if HZ else 0.30, entrada='zoom')
    tilt = 1.5 * math.sin(t * 2.0)
    mesa = named_box(1.6, 0.06, 0.9, (60, 62, 70), 0, 0.6, 0, gloss=0.5)
    vaso = M.named(L.M3.cyl(0.18, 0.5, (190, 220, 235), n=28, shadow=0, gloss=0.95, r2=0.21).tf(t=(0, 0.66, 0)), 'vaso', rim=1.0, gloss=0.95)
    agua = M.named(L.M3.cyl(0.165, 0.32, (90, 170, 230), n=28, shadow=0, gloss=0.8, r2=0.185).tf(rz=tilt, t=(0, 0.67, 0)), 'agua')
    agua.glow = (20, 50, 70)
    draw_objects(fr, [mesa, agua, vaso])

    def ui(img, fx):
        pill(img, fx, DX, DY + 160 if HZ else 1380, 'LA CURVA NO TE AVIENTA', seg(u, 0.4, 0.7), size=30)
        etiqueta(img, fx, 'RECREACIÓN', u)
    fr.ui.append(ui)
    return fin(fr, fi)


def s_soldados(t, fi, u, d):
    """Los rieles van soldados: los tramos se juntan con chispa y desaparece el traca-traca (zoom digital)."""
    fr = Frame(camara(u, [(0, pose(5.5, -60, 28, tx=0, ty=0.0)), (0.5, pose(4.6, -40, 20, tx=0, ty=0.0))]))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0)
    k = P.eout4(seg(u, 0.2, 1.0))
    ms = []
    for j in range(-3, 4):
        gap = 0.25 * (1 - k)
        for zs in (-0.36, 0.36):
            ms.append(named_box(1.9, 0.12, 0.08, (170, 174, 184), j * (2.0 + gap), 0, zs, name='riel', gloss=0.9))
    draw_objects(fr, ms)
    L.via(fr, a=0.5, postes=False)
    if 0.8 < u < 1.4:
        for j in range(-3, 3):
            for zs in (-0.36, 0.36):
                dot3(fr, (j * 2.0 + 1.0, 0.1, zs), r=8, col=(255, 200, 120), a=1 - seg(u, 1.0, 1.4), glow=1.5)

    def ui(img, fx):
        zl = 'x1.0' if u < 1.2 else ('x1.15' if u < 2.0 else 'x1.3')
        rec_frame(img, t, seg(u, 0.0, 0.2), zoom_label=zl)
        P.pill_tachada(img, fx, DX if HZ else 540, DY - 60 if HZ else 1300, 'TRACA-TRACA', seg(u, 0.3, 0.5), seg(u, 1.2, 1.5), t)
        kick(img, 'RIEL SOLDADO CONTINUO', u, 0.1)
    fr.ui.append(ui)
    img = fin(fr, fi)
    zz = 1.0 if u < 1.2 else (1.15 if u < 2.0 else 1.3)
    return M.scale_about(img, zz, L.OBJ_CX, 0.55)


def s_cruces(t, fi, u, d):
    """No cruza ni una calle: vía elevada sin cruces (autos, gente y vacas abajo, tachados en la vía)."""
    def extra(u):
        ms = []
        for j in range(-3, 4):
            ms.append(named_box(0.5, 1.8, 0.5, (110, 108, 104), j * 4.0, -1.8, 0, name='pilar', gloss=0.1))
        ms.append(named_box(30, 0.3, 1.6, (120, 118, 112), 0, -0.32, 0, name='losa', gloss=0.1))
        e = P.entrada(u, 0.5, 0.25, 'desliza')
        ms.append(named_box(0.9, 0.35, 0.5, (40, 120, 220), 1.5 + e['dy'], -1.8, 2.0, name='auto'))
        return ms

    def ui(img, fx, u, t):
        y0 = 260 if HZ else 1120
        for i, (txt, col) in enumerate((('AUTOS', ROJO), ('GENTE', ROJO), ('VACAS', ROJO))):
            P.pill_tachada(img, fx, (DX - 260 + 260 * i) if HZ else (200 + 340 * i), y0, txt, seg(u, 0.3 + 0.3 * i, 0.5 + 0.3 * i),
                           seg(u, 0.6 + 0.3 * i, 0.9 + 0.3 * i), t, size=28)
        tarjeta_dato(img, fx, DX if HZ else 540, (y0 + 200) if HZ else 1330, '0', 'CRUCES', seg(u, 1.6, 1.9), VERDE)
    kw = lambda u: dict(vel=1.4, cat=0.5)
    return mk_tren_k([(0, pose(10, -30, -4, tx=-1.0, ty=-0.3)), (0.5, pose(9, -40, 4, tx=-1.0, ty=0.0))], lambda u: dict(kw(u), extra=extra), ui=ui)(t, fi, u, d)


def s_25kv(t, fi, u, d):
    """No quema diésel: la energía baja de un cable a 25 mil volts (corriente que baja por el pantógrafo)."""
    def ui(img, fx, u, t):
        tarjeta_dato(img, fx, DX, DY - 100 if HZ else 1270, f'{contador(u, 0.2, 1.4, 0, 25000):,.0f} V'.replace(',', ' '), 'CORRIENTE ALTERNA',
                     seg(u, 0.1, 0.4), AMARILLO)
        P.pill_tachada(img, fx, DX, DY + 120 if HZ else 1480, 'DIÉSEL', seg(u, 0.0, 0.2), seg(u, 0.3, 0.6), t, size=28)
    kw = lambda u: dict(vel=1.0, cat=0.6 + 0.4 * abs(math.sin(t * 5)))
    return mk_tren_k([(0, pose(6.5, -12, 10, tx=-4.0, ty=1.5)), (0.5, pose(5.5, -24, 6, tx=-4.3, ty=1.6))], kw, ui=ui)(t, fi, u, d)


def s_tunel(t, fi, u, d):
    """La nariz larga corta el aire y evita un trueno al entrar a los túneles."""
    def extra(u):
        return []

    def ui(img, fx, u, t):
        pill(img, fx, DX, DY - 80 if HZ else 1290, 'SIN «TRUENO» EN EL TÚNEL', seg(u, 1.2, 1.5), size=28, border=CYAN)
        kick(img, 'NARIZ LARGA = MENOS PRESIÓN', u, 0.2)
    kw = lambda u: dict(vel=1.4, cat=0.5, tunel=seg(u, 0.0, 0.3), xpos=-2.0 + 3.5 * seg(u, 0.0, 3.0))

    def fn(t, fi, u, d):
        img = mk_tren_k([(0, pose(7.5, 50, 8, tx=2.5, ty=0.9)), (0.6, pose(6.5, 34, 6, tx=2.0, ty=0.9))], kw, ui=ui)(t, fi, u, d)
        return img
    return fn(t, fi, u, d)


def s_foto_e5(t, fi, u, d):
    def ui(img, fx):
        M.photo_card(img, fx, foto('e5'), L.OBJ_CX * W if HZ else 540, 470 if HZ else 980, 760 if HZ else 860, t - u + 0.05, t,
                     caption='E5 · CC0 Toshinori baba', angle0=7)
        if HZ:
            velocimetro(img, fx, 330, 470, 170, contador(u, 0.3, 1.6, 0, 320), 360, seg(u, 0.1, 0.4))
        else:
            velocimetro(img, fx, 540, 500, 170, contador(u, 0.3, 1.6, 0, 320), 360, seg(u, 0.1, 0.4))
    return fondo(t, fi, u, ui, z=[(0, 1.0), (0.8, 1.05)])


# =================================================================== PARTE 4: EL TREN QUE FLOTA
def mk_mag(claves, flota=lambda u: 1.0, xray=lambda u: 0.0, campo=lambda u: 0.0, ui=None, pal=None, pal_t0=-0.3, pal_cy=0.40,
           pal_ent='golpe', vel=lambda u: 0.6, xpos=lambda u: 0.0, rieles_normales=0.0, construye=None):
    if not HZ:   # en vertical el maglev necesita más distancia para caber
        claves = [(a, dict(p, dist=p['dist'] * 1.6)) for a, p in claves]

    def fn(t, fi, u, d):
        fr = Frame(camara(u, claves, cy=None if HZ else 0.47))
        space(fr, t, floor='lines', floor_a=0.3, bokeh=1.0, beam=0.35, beam_x=L.OBJ_CX)
        if pal:
            M.cristal(fr.base, fr.fx, pal, u, t0=pal_t0, cy=pal_cy, entrada=pal_ent)
        x1 = 14 if construye is None else -14 + 28 * construye(u)
        ms = L.maglev(x=2.0 + xpos(u), flota=flota(u)) + L.viga(-14, max(-13.5, x1))
        draw_objects(fr, ms, xray=xray(u), keep=('iman', 'riel', 'viga', 'pilar'))
        kc = campo(u)
        if kc > 0.01:
            for j in range(16):
                xx = -12 + ((j * 1.6 + t * 6) % 24)
                for zs in (-0.25, 0.25):
                    line3(fr, [(xx, 0.07, zs), (xx + 0.5, 0.07, zs)], col=CYAN, w=4, a=kc, glow=1.2)
        if vel(u) > 0.2:
            L.rachas(fr, t, a=vel(u), vel=14 * vel(u))
        if ui:
            fr.ui.append(lambda img, fx: ui(img, fx, u, t, fr.cam))
        return fin(fr, fi)
    return fn


def s_mag_sube(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        pill(img, fx, DX, DY - 60 if HZ else 1300, 'NO TOCA LAS VÍAS', seg(u, 0.6, 0.9), size=30)
        etiqueta(img, fx, 'ESCALA EXAGERADA', u)
    return mk_mag([(0, pose(7.0, 30, 2, tx=-1.0, ty=0.4)), (0.5, pose(6.0, 18, 4, tx=-1.2, ty=0.4))],
                  flota=lambda u: P.resorte(seg(u, 0.3, 1.0)), ui=ui, vel=lambda u: 0.2)(t, fi, u, d)


def s_mag_nombre(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        kick(img, 'MAGNETIC LEVITATION', u, 0.2)
    return mk_mag([(0, pose(9.0, -24, 10, tx=-1.5, ty=0.5)), (0.5, pose(8.0, -34, 8, tx=-1.2, ty=0.5))], ui=ui, pal='MAGLEV',
                  pal_t0=0.0, pal_cy=0.38 if HZ else 0.30, pal_ent='sube', vel=lambda u: 0.8)(t, fi, u, d)


def s_mag_1cm(t, fi, u, d):
    """Así se ve por dentro: corte del maglev abrazando la viga; los imanes jalan hacia arriba y lo dejan a ~1 cm."""
    def ui(img, fx):
        cx, cy = (L.OBJ_CX * W, 520) if HZ else (540, 1000)
        s_ = 1.0 if HZ else 1.15
        k = seg(u, 0.0, 0.4)
        lift = 26 * P.resorte(seg(u, 0.5, 1.1)) * s_
        dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        # viga en T (concreto) y riel
        dd.rectangle((cx - 90 * s_, cy, cx + 90 * s_, cy + 300 * s_), fill=M.scale_c((110, 108, 104), k))
        dd.rectangle((cx - 200 * s_, cy - 40 * s_, cx + 200 * s_, cy), fill=M.scale_c((140, 138, 132), k))
        dd.rectangle((cx - 210 * s_, cy - 52 * s_, cx + 210 * s_, cy - 40 * s_), fill=M.scale_c((180, 184, 194), k))
        # tren (corte) que abraza la viga
        top = cy - 52 * s_ - 30 * s_ - lift
        body = [(cx - 300 * s_, top), (cx + 300 * s_, top), (cx + 300 * s_, top - 300 * s_), (cx - 300 * s_, top - 300 * s_)]
        dd.rounded_rectangle((cx - 300 * s_, top - 320 * s_, cx + 300 * s_, top), radius=60 * s_, outline=M.scale_c(CYAN, k), width=5)
        df.rounded_rectangle((cx - 300 * s_, top - 320 * s_, cx + 300 * s_, top), radius=60 * s_, outline=M.scale_c(CYAN, 0.5 * k), width=10)
        for sg in (-1, 1):
            xo = cx + sg * 250 * s_
            xi = cx + sg * 215 * s_
            dd.line([(xo, top), (xo, cy + 40 * s_ - lift), (cx + sg * 130 * s_, cy + 40 * s_ - lift)], fill=M.scale_c(CYAN, k), width=5)
            # imán debajo del ala de la viga
            mx0, mx1 = sorted((cx + sg * 130 * s_, xi + sg * 20 * s_))
            my = cy + 8 * s_ - lift * 0.0 + (26 * s_ - lift)
            col = M.mixc((60, 70, 90), CYAN, seg(u, 0.4, 0.7))
            dd.rectangle((mx0, cy + 12 * s_ + 26 * s_ - lift, mx1, cy + 34 * s_ + 26 * s_ - lift), fill=col)
            df.rectangle((mx0, cy + 12 * s_ + 26 * s_ - lift, mx1, cy + 34 * s_ + 26 * s_ - lift), fill=M.scale_c(CYAN, 0.6 * seg(u, 0.4, 0.7)))
            if u > 0.6:
                ax = (mx0 + mx1) / 2
                dd.line([(ax, cy + 70 * s_), (ax, cy + 30 * s_)], fill=AMARILLO, width=4)
                dd.polygon([(ax - 10, cy + 34 * s_), (ax + 10, cy + 34 * s_), (ax, cy + 18 * s_)], fill=AMARILLO)
        # cota del hueco
        kk = seg(u, 1.0, 1.3)
        if kk > 0:
            xg = cx + 320 * s_
            y0, y1 = cy - 52 * s_, top
            dd.line([(xg, y0), (xg, y1)], fill=AMARILLO, width=4)
            dd.line([(xg - 14, y0), (xg + 14, y0)], fill=AMARILLO, width=4)
            dd.line([(xg - 14, y1), (xg + 14, y1)], fill=AMARILLO, width=4)
            texto(img, fx, xg + 24, (y0 + y1) / 2, '≈ 1 cm', 48, AMARILLO, kk, f='mono', anchor='lm')
        pill(img, fx, DX if HZ else 540, 330 if HZ else 1480, 'LOS IMANES JALAN HACIA ARRIBA', seg(u, 0.7, 1.0), size=26, border=CYAN)
        kick(img, 'ASÍ SE VE POR DENTRO · CORTE', u, 0.05)
        etiqueta(img, fx, 'ESQUEMA · ESCALA EXAGERADA', u)
    return fondo(t, fi, u, ui, z=[(0, 1.0), (1.0, 1.08)], zc=(L.OBJ_CX if HZ else 0.5, 0.48),
                 pal=None if HZ else 'IMANES', pal_t0=0.2, pal_cy=0.26, pal_ent='sube')


def s_mag_motor(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        pill(img, fx, DX, DY - 80 if HZ else 1290, 'LA VÍA ES EL MOTOR', seg(u, 0.3, 0.6), size=30, border=CYAN)
    return mk_mag([(0, pose(6.5, -50, 24, tx=-2.0, ty=0.2)), (0.6, pose(5.5, -30, 18, tx=-1.5, ty=0.2))],
                  campo=lambda u: seg(u, 0.4, 0.8), xpos=lambda u: 1.5 * seg(u, 0.5, 3.5), ui=ui, vel=lambda u: 0.7)(t, fi, u, d)


def s_shanghai(t, fi, u, d):
    def ui(img, fx):
        M.photo_card(img, fx, foto('maglev'), L.OBJ_CX * W if HZ else 540, 450 if HZ else 1000, 820 if HZ else 900, t - u + 0.05, t,
                     caption='SHANGHÁI · DOMINIO PÚBLICO', angle0=-7)
        if HZ:
            velocimetro(img, fx, 330, 470, 170, contador(u, 0.6, 1.8, 0, 300), 450, seg(u, 0.4, 0.7))
            texto(img, fx, 330, 150, '+20 AÑOS', 54, WHITE, seg(u, 0.2, 0.5), f='mono')
        else:
            velocimetro(img, fx, 540, 470, 170, contador(u, 0.6, 1.8, 0, 300), 450, seg(u, 0.4, 0.7))
            texto(img, fx, 540, 1450, '+20 AÑOS EN SERVICIO', 44, WHITE, seg(u, 0.2, 0.5), f='mono')
    return fondo(t, fi, u, ui, z=[(0, 1.0), (1.0, 1.05)])


def s_avion(t, fi, u, d):
    """Más rápido que un avión al despegar: avión de línea de luz que despega junto al maglev + barras."""
    def ui(img, fx):
        box = (100, 120, 980, 860) if HZ else (80, 900, 1000, 1480)
        M.chart_grow(img, fx, box, [270, 300], ['AVIÓN', 'MAGLEV'], t - u + 0.2, t, unit='km/h', title_txt='KM/H AL DESPEGAR',
                     vmax=330, line=False)
        etiqueta(img, fx, 'AVIÓN: 250–290 km/h', u, 0.8)

    def fn(t, fi, u, d):
        fr = Frame(camara(u, [(0, pose(7.0, 30, 6, tx=0.6, ty=0.8)), (0.5, pose(6.0, 18, 6, tx=0.8, ty=0.8))],
                          cx=0.80 if HZ else 0.5, cy=0.60 if HZ else 0.40))
        space(fr, t, floor='lines', floor_a=0.3, bokeh=1.0)
        draw_objects(fr, L.maglev(x=2.0, flota=1.0) + L.viga())
        L.rachas(fr, t, a=0.8)
        fr.ui.append(ui)
        return fin(fr, fi)
    return fn(t, fi, u, d)


def s_600(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        velocimetro(img, fx, DX, DY - 140 if HZ else 1260, 170 if HZ else 190, contador(u, 0.1, 1.4, 300, 600), 700, seg(u, 0.0, 0.3), warn=450)
        pill(img, fx, DX, DY + 110 if HZ else 1520, 'SOLO EN PRUEBAS', seg(u, 1.6, 1.9), size=28, border=ROJO)
    return mk_mag([(0, pose(5.0, 70, 6, tx=1.0, ty=0.6)), (0.4, pose(6.0, 50, 4, tx=0.0, ty=0.6))], ui=ui,
                  vel=lambda u: 1.6, campo=lambda u: 0.6, pal='600', pal_t0=0.9, pal_cy=0.30 if HZ else 0.30,
                  pal_ent='zoom')(t, fi, u, d)


def s_desde_cero(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        P.pill_tachada(img, fx, DX, DY - 120 if HZ else 1240, 'VÍA NORMAL', seg(u, 0.1, 0.3), seg(u, 0.5, 0.8), t, size=30)
        pill(img, fx, DX, DY + 40 if HZ else 1380, 'TODO DESDE CERO', seg(u, 1.4, 1.7), size=30, border=CYAN)
    return mk_mag([(0, pose(12, -40, 20, tx=0.0, ty=0.0)), (0.5, pose(10, -30, 16, tx=0.0, ty=0.0))], ui=ui,
                  construye=lambda u: 0.35 + 0.65 * seg(u, 0.6, 3.0), flota=lambda u: 0.6, vel=lambda u: 0.0,
                  xpos=lambda u: -6.0)(t, fi, u, d)


# =================================================================== PARTE 5: ¿CUÁNTO COSTARÍA?
def s_precio(t, fi, u, d):
    """No tiene precio: etiqueta de precio con «?» que se balancea junto al tren."""
    def extra(u):
        return []

    def ui(img, fx, u, t):
        x, y = (DX, 420) if HZ else (540, 1250)
        ang = 12 * math.sin(t * 3.2) * math.exp(-0.4 * u) + 4
        lay = Image.new('RGBA', (360, 200), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        k = P.resorte(seg(u, 0.1, 0.5))
        dl.rounded_rectangle((40, 10, 350, 190), radius=26, fill=(250, 236, 180, int(255 * clamp(k))))
        dl.ellipse((64, 82, 92, 110), fill=(0, 0, 0, 0))
        dl.text((215, 100), '$ ?', font=M.font('sansx', 110), fill=(40, 30, 20, int(255 * clamp(k))), anchor='mm')
        lay = lay.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.paste(lay, (int(x - lay.width / 2), int(y - lay.height / 2)), lay)
        texto(img, fx, x, y + 170, 'SIN PRESUPUESTO OFICIAL', 28, MUTED, seg(u, 0.8, 1.1), f='mono', glow=0)
    return mk_tren_k([(0, pose(8.0, -150, 12, tx=-3.0, ty=0.8)), (0.5, pose(7.0, -160, 8, tx=-3.0, ty=0.8))],
                     lambda u: dict(vel=0.3, cat=0.3), ui=ui)(t, fi, u, d)


def s_pista(t, fi, u, d):
    fn = mk_mapa([(0, pose(3.0, 0, 70, tx=0.9, ty=0, tz=1.35)), (0.5, pose(2.4, -10, 58, tx=0.85, ty=0, tz=1.35))],
                 rutas=[(['CDMX', 'Querétaro'], lambda u: seg(u, 0.3, 1.4), AMARILLO)],
                 ciudades=[('CDMX', 0.0, 1), ('Querétaro', 0.8, 1)],
                 extra_ui=lambda img, fx, u, t: pill(img, fx, DX if HZ else 540, (DY - 120) if HZ else 1300, 'LA PISTA: MÉXICO–QUERÉTARO',
                                                     seg(u, 0.4, 0.7), size=30, border=AMARILLO))
    return fn(t, fi, u, d)


def s_206(t, fi, u, d):
    def ui(img, fx):
        if HZ:
            tarjeta_dato(img, fx, 560, 330, '232 km', 'MÉXICO–QUERÉTARO', seg(u, 0.0, 0.3))
            tarjeta_dato(img, fx, 1300, 330, f'${contador(u, 1.2, 2.6, 0, 206):.0f} mil millones', 'INVERSIÓN · HACIENDA', seg(u, 1.0, 1.3),
                         AMARILLO, size=90)
        else:
            tarjeta_dato(img, fx, 540, 620, '232 km', 'MÉXICO–QUERÉTARO', seg(u, 0.0, 0.3))
            tarjeta_dato(img, fx, 540, 1060, f'${contador(u, 1.2, 2.6, 0, 206):.0f}', 'MIL MILLONES DE PESOS · HACIENDA', seg(u, 1.0, 1.3),
                         AMARILLO, size=190)
    return fondo(t, fi, u, ui, z=[(0, 1.0), (1.2, 1.06)], pal='$', pal_t0=0.9, pal_cy=0.62 if HZ else 0.40, pal_ent='zoom')


def s_por_km(t, fi, u, d):
    """Casi 900 millones de pesos por cada kilómetro: 1 km de vía y una pila de billetes que crece."""
    fr = Frame(camara(u, [(0, pose(7.0, -40, 18, tx=0.0, ty=0.8)), (0.5, pose(6.0, -28, 14, tx=0.0, ty=1.0))]))
    space(fr, t, floor='dots', floor_a=0.45, bokeh=1.0, beam=0.5, beam_x=L.OBJ_CX)
    L.via(fr, -2.0, 2.0, a=0.9, postes=False)
    n = int(18 * P.eout4(seg(u, 0.2, 1.8)))
    ms = []
    for j in range(n):
        b = named_box(1.4, 0.12, 0.7, (120, 180, 130) if j % 2 else (100, 160, 112), 0.03 * math.sin(j * 1.7), 0.15 + j * 0.13, 0,
                      name='billete', gloss=0.2)
        ms.append(b)
    draw_objects(fr, ms)

    def ui(img, fx):
        tarjeta_dato(img, fx, DX if HZ else 540, DY - 100 if HZ else 1330, '≈ $890 millones', 'POR CADA KILÓMETRO', seg(u, 0.6, 0.9),
                     AMARILLO, size=84 if HZ else 90)
        etiqueta(img, fx, '206 785 ÷ 232 · CÁLCULO', u, 0.8)
    fr.ui.append(ui)
    return fin(fr, fi)


def s_ni_bala(t, fi, u, d):
    def ui(img, fx):
        if HZ:
            velocimetro(img, fx, 600, 470, 200, contador(u, 0.0, 0.8, 0, 160), 360, seg(u, 0.0, 0.3), label='MÉXICO–QUERÉTARO')
            velocimetro(img, fx, 1320, 470, 200, contador(u, 0.4, 1.2, 0, 300), 360, seg(u, 0.4, 0.7), label='TREN BALA', col=CYAN)
        else:
            velocimetro(img, fx, 540, 640, 210, contador(u, 0.0, 0.8, 0, 160), 360, seg(u, 0.0, 0.3), label='MÉXICO–QUERÉTARO')
            velocimetro(img, fx, 540, 1180, 210, contador(u, 0.4, 1.2, 0, 300), 360, seg(u, 0.4, 0.7), label='TREN BALA', col=CYAN)
    return fondo(t, fi, u, ui, z=[(0, 1.06), (0.4, 1.0)])


def s_terreno(t, fi, u, d):
    """Curvas enormes, túneles y puentes: perfil de cerros con la vía recta que los atraviesa."""
    def ui(img, fx):
        x0, x1 = (80, 1840) if HZ else (40, 1040)
        yb = 760 if HZ else 1300
        n = 120
        xs = np.linspace(x0, x1, n)
        hs = 160 * np.maximum(0, np.sin(np.linspace(0, 3.2 * math.pi, n)) ** 2) + 60 * np.sin(np.linspace(0, 9, n)) + 120
        k = seg(u, 0.0, 0.8)
        pts = [(x, yb - h * k) for x, h in zip(xs, hs)]
        dd, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        dd.line(pts, fill=(200, 205, 215), width=4)
        df.line(pts, fill=(80, 80, 90), width=8)
        yv = yb - 150
        kv = seg(u, 0.8, 2.2)
        xv = lerp(x0, x1, kv)
        dd.line([(x0, yv), (xv, yv)], fill=CYAN, width=6)
        df.line([(x0, yv), (xv, yv)], fill=M.scale_c(CYAN, 0.6), width=16)
        for x, h in zip(xs[::6], hs[::6]):
            if x < xv:
                if yb - h < yv:     # túnel
                    dd.line([(x, yv - 14), (x, yv + 14)], fill=AMARILLO, width=3)
                else:               # puente
                    dd.line([(x, yv), (x, yb - h)], fill=(160, 160, 170), width=3)
        pill(img, fx, (x0 + x1) * 0.3, yv - 260 if HZ else yv - 300, 'TÚNELES', seg(u, 1.2, 1.5), size=28, border=AMARILLO)
        pill(img, fx, (x0 + x1) * 0.7, yv - 260 if HZ else yv - 300, 'PUENTES', seg(u, 1.6, 1.9), size=28, border=WHITE)
        etiqueta(img, fx, 'ESQUEMA', u)
    return fondo(t, fi, u, ui, z=[(0, 1.0), (1.0, 1.05)])


def s_480(t, fi, u, d):
    def ui(img, fx):
        box = (90, 100, 1000, 860) if HZ else (70, 560, 1010, 1440)
        M.chart_grow(img, fx, box, [206, 480], ['MX–QRO', 'CDMX–GDL'], t - u + 0.1, t, unit='', title_txt='MIL MILLONES DE PESOS',
                     vmax=520, line=False, tag='CÁLCULO APROX.')
        if HZ:
            tarjeta_dato(img, fx, 1460, 420, '≈ $480', 'MIL MILLONES · A GUADALAJARA', seg(u, 1.0, 1.3), AMARILLO, size=130)
    return fondo(t, fi, u, ui, z=[(0, 1.0), (1.2, 1.04)])


def s_boleto(t, fi, u, d):
    def ui(img, fx):
        x, y = (L.OBJ_CX * W, 470) if HZ else (540, 980)
        k = P.resorte(seg(u, 0.05, 0.5))
        lay = Image.new('RGBA', (640, 300), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle((10, 10, 630, 290), radius=24, fill=(240, 240, 236, 255))
        dl.line([(450, 20), (450, 280)], fill=(160, 160, 160, 255), width=3)
        dl.text((40, 50), 'BOLETO', font=M.font('mono', 36), fill=(40, 40, 46, 255))
        dl.text((40, 120), 'CDMX → GDL', font=M.font('sansx', 56), fill=(20, 20, 24, 255))
        dl.text((540, 150), '$ ?', font=M.font('sansx', 80), fill=(200, 40, 40, 255), anchor='mm')
        lay = lay.rotate(-6 + 4 * math.sin(t * 2), expand=True, resample=Image.BICUBIC)
        s = max(0.05, k)
        lay = lay.resize((max(1, int(lay.width * s)), max(1, int(lay.height * s))))
        img.paste(lay, (int(x - lay.width / 2), int(y - lay.height / 2)), lay)
        if HZ:
            texto(img, fx, 420, 470, 'SIN PRECIO', 70, WHITE, seg(u, 0.6, 0.9), f='sansx')
            texto(img, fx, 420, 550, 'OFICIAL TODAVÍA', 34, MUTED, seg(u, 0.7, 1.0), f='mono', glow=0)
        else:
            texto(img, fx, 540, 1320, 'SIN PRECIO OFICIAL', 56, WHITE, seg(u, 0.6, 0.9), f='sansx')
    return fondo(t, fi, u, ui, z=[(0, 1.0), (0.6, 1.06)])


# =================================================================== PARTE 6: LO QUE MÉXICO SÍ ESTÁ CONSTRUYENDO
def s_tren_mx(t, fi, u, d):
    def ui(img, fx, u, t):
        pill(img, fx, DX, DY - 60 if HZ else 1300, 'TRENES RÁPIDOS · NO BALA', seg(u, 0.5, 0.8), size=28)
        etiqueta(img, fx, 'RECREACIÓN · GENÉRICO', u)
    kw = lambda u: dict(quien='mx', vel=0.9, cat=0.4, xpos=P.entrada(u, 0.0, 0.3, 'desliza')['dy'] * 2.5)
    return mk_tren_k([(0, pose(8.0, -36, 8, tx=-1.2, ty=0.8)), (0.5, pose(7.0, -24, 6, tx=-1.0, ty=0.8))], kw, ui=ui)(t, fi, u, d)


def s_32(t, fi, u, d):
    def ui(img, fx):
        if HZ:
            barra(img, fx, 160, 600, 1600, 0.32 * P.eout4(seg(u, 0.3, 1.6)), seg(u, 0.1, 0.4), 'AVANCE DE OBRA · 31-OCT-2026', h=46)
            num(img, fx, f'{contador(u, 0.3, 1.6, 0, 32):.0f} %', 960, 420, 190, seg(u, 0.3, 0.5), CYAN)
            kick(img, 'TREN MÉXICO–QUERÉTARO', u, 0.05, cx=960, y=180)
        else:
            barra(img, fx, 90, 1180, 900, 0.32 * P.eout4(seg(u, 0.3, 1.6)), seg(u, 0.1, 0.4), 'AVANCE · 31-OCT-2026', h=46)
            num(img, fx, f'{contador(u, 0.3, 1.6, 0, 32):.0f} %', 540, 960, 220, seg(u, 0.3, 0.5), CYAN)
            kick(img, 'TREN MÉXICO–QUERÉTARO', u, 0.05, cx=540, y=700)
    return fondo(t, fi, u, ui, z=[(0, 1.0), (1.4, 1.05)])


def s_estaciones(t, fi, u, d):
    est = ['Huehuetoca', 'Tula', 'San Juan del Río']

    def eui(img, fx, u, t):
        tarjeta_dato(img, fx, DX, DY - 220 if HZ else 1260, '160 km/h', 'VELOCIDAD DE OPERACIÓN', seg(u, 1.0, 1.3), WHITE, size=80)
        tarjeta_dato(img, fx, DX, DY + 20 if HZ else 1460, '1 h 40', 'BUENAVISTA → QUERÉTARO', seg(u, 2.0, 2.3), CYAN, size=80)
    fn = mk_mapa([(0, pose(2.2, 20, 70, tx=1.0, ty=0, tz=1.15)), (0.6, pose(2.0, 0, 62, tx=0.9, ty=0, tz=1.2))],
                 rutas=[(['CDMX', 'Huehuetoca', 'Tula', 'San Juan del Río', 'Querétaro'], lambda u: seg(u, 0.2, 2.0), CYAN)],
                 ciudades=[('CDMX', 0.0, 1), ('Querétaro', 1.8, 1)], estaciones=[(n, 0.5 + 0.4 * i) for i, n in enumerate(est)],
                 extra_ui=eui)
    return fn(t, fi, u, d)


def s_hora_menos(t, fi, u, d):
    def ui(img, fx):
        box = (90, 100, 1000, 860) if HZ else (70, 560, 1010, 1440)
        M.chart_grow(img, fx, box, [165, 100], ['CAMIÓN', 'TREN'], t - u + 0.1, t, unit='min', title_txt='MINUTOS A QUERÉTARO', vmax=190,
                     line=False)
        if HZ:
            tarjeta_dato(img, fx, 1460, 330, '≈ −1 h', 'CONTRA EL CAMIÓN', seg(u, 0.9, 1.2), VERDE, size=110)
            tarjeta_dato(img, fx, 1460, 620, '2027', 'ARRANQUE PREVISTO', seg(u, 1.8, 2.1), WHITE, size=110)
        else:
            pill(img, fx, 540, 1560, 'ARRANQUE PREVISTO: 2027', seg(u, 1.8, 2.1), size=30)
    return fondo(t, fi, u, ui)


def s_sigue(t, fi, u, d):
    fn = mk_mapa([(0, pose(3.6, -10, 66, tx=0.6, ty=0, tz=1.25)), (0.5, pose(4.4, -4, 60, tx=0.32, ty=0, tz=1.24))],
                 rutas=[(['CDMX', 'Querétaro'], lambda u: 1.0, CYAN), (['Querétaro', 'Irapuato'], lambda u: seg(u, 0.2, 0.9), AMARILLO)],
                 punteadas=[(['Irapuato', 'León', 'Guadalajara'], lambda u: seg(u, 1.0, 2.4), (200, 200, 210))],
                 ciudades=[('Querétaro', 0.0, 1), ('Irapuato', 0.6, 1), ('Guadalajara', 1.6, -1)],
                 extra_ui=lambda img, fx, u, t: (pill(img, fx, DX if HZ else 300, 200 if HZ else 1300, 'EN OBRA', seg(u, 0.5, 0.8), size=26, border=AMARILLO),
                                                  pill(img, fx, DX if HZ else 760, 300 if HZ else 1300, '1.ª PIEDRA: DIC', seg(u, 1.8, 2.1), size=26, border=WHITE)))
    return fn(t, fi, u, d)


def s_4h(t, fi, u, d):
    def eui(img, fx, u, t):
        reloj_ui(img, fx, DX, DY - 100 if HZ else 1250, 4 * P.eout4(seg(u, 0.2, 1.6)), seg(u, 0.0, 0.3), '≈ 4 h · CDMX → GDL', WHITE)
        pill(img, fx, DX, DY + 150 if HZ else 1500, 'HACIA 2030 · GOBIERNO DE JALISCO', seg(u, 1.4, 1.7), size=24)
    fn = mk_mapa(CAM_RUTA, rutas=[(RUTA5, lambda u: P.eout4(seg(u, 0.2, 1.6)), WHITE)],
                 marcas=[(RUTA5, lambda u: P.eout4(seg(u, 0.2, 1.6)), 'TREN', WHITE)],
                 ciudades=[('CDMX', 0.0, 1), ('Guadalajara', 0.2, -1)], extra_ui=eui)
    return fn(t, fi, u, d)


def s_tres_menos(t, fi, u, d):
    def ui(img, fx):
        box = (90, 100, 1060, 860) if HZ else (70, 560, 1010, 1440)
        M.chart_grow(img, fx, box, [7, 4, 2.5], ['CAMIÓN', 'TREN MX', 'BALA'], t - u + 0.1, t, unit='h', title_txt='HORAS CDMX → GDL',
                     vmax=8, line=True)
        if HZ:
            tarjeta_dato(img, fx, 1480, 420, '−3 h', 'TREN CONTRA CAMIÓN', seg(u, 1.4, 1.7), VERDE, size=150)
        etiqueta(img, fx, 'BALA: ESTIMACIÓN', u, 1.0)
    return fondo(t, fi, u, ui)


# =================================================================== CIERRE
def s_resumen(t, fi, u, d):
    """Curvas de km, rieles soldados y un tren que frena solo: el tren pasa con todo encendido."""
    def ui(img, fx, u, t):
        for i, (txt, col) in enumerate((('CURVAS DE 4 km', CYAN), ('RIELES SOLDADOS', WHITE), ('FRENA SOLO SI TIEMBLA', ROJO))):
            pill(img, fx, DX if HZ else 540, (150 + 100 * i) if HZ else (1120 + 100 * i), txt, seg(u, 0.4 + 0.9 * i, 0.7 + 0.9 * i), size=28, border=col)
    kw = lambda u: dict(vel=1.6, cat=0.8)
    return mk_tren_k([(0, pose(10.0, -60, 14, tx=-2.0, ty=0.8)), (1.2, pose(7.0, -30, 6, tx=-1.0, ty=0.8)),
                      (2.4, pose(8.0, -14, 8, tx=-1.2, ty=0.8))], kw, ui=ui)(t, fi, u, d)


def s_si_no(t, fi, u, d):
    def ui(img, fx, u, t):
        titulo(img, fx, '¿Tú te subirías', 'a un tren bala aquí?', u, 0.05)
        pill(img, fx, (DX - 150) if HZ else 360, DY + 40 if HZ else 1330, 'SÍ', seg(u, 0.9, 1.2), size=44, border=VERDE)
        pill(img, fx, (DX + 150) if HZ else 720, DY + 40 if HZ else 1330, 'NO', seg(u, 1.1, 1.4), size=44, border=ROJO)
    kw = lambda u: dict(vel=1.0, cat=0.5)
    return mk_tren_k([(0, pose(7.0, 30, 10, tx=-0.5, ty=0.8)), (0.5, pose(8.0, 20, 6, tx=-1.0, ty=0.8))], kw, ui=ui)(t, fi, u, d)


def s_mandalo(t, fi, u, d):
    def eui(img, fx, u, t):
        pill(img, fx, DX if HZ else 540, DY - 60 if HZ else 1300, 'PARA QUIEN VIAJA EN CAMIÓN', seg(u, 0.4, 0.7), size=28, border=NARANJA)
    fn = mk_mapa([(0, pose(5.0, 20, 62, tx=0.4, ty=0, tz=1.2)), (0.5, pose(4.4, 0, 60, tx=0.32, ty=0, tz=1.24))],
                 rutas=[(RUTA5, lambda u: 1.0, CYAN)],
                 marcas=[(RUTA5, lambda u: 0.27 * seg(u, 0.0, 3.0), 'CAMIÓN', NARANJA), (RUTA5, lambda u: P.eout4(seg(u, 0.2, 2.8)), 'TREN BALA', CYAN)],
                 ciudades=[('CDMX', 0.0, 1), ('Guadalajara', 0.0, -1)], extra_ui=eui)
    return fn(t, fi, u, d)


# =================================================================== SHORTS: inicios propios
def s_hookA(t, fi, u, d):
    """Short A, inicio 12 (cuenta regresiva): el celular cuenta 60…1 rapidísimo y se congela en «1» con destello."""
    fr = Frame(camara(u, [(-1.0, pose(3.0, -30, 4, tx=0.0, ty=P.PH_Y + 0.15)), (0.0, pose(2.6, -12, 2, tx=0.0, ty=P.PH_Y + 0.15))],
                      cy=0.45 if not HZ else None))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.5, beam_x=L.OBJ_CX)
    M.cristal(fr.base, fr.fx, 'ALERTA', u, t0=-0.6, cy=0.26 if not HZ else 0.40, entrada='golpe')
    k = seg(u, -0.6, 1.4)
    rest = max(1, int(round(60 - 59 * P.eout4(k))))
    ph = P.celular(pantalla_alerta(rest, 0.6 + 0.4 * math.sin(t * 9) ** 2), ry=-12 + 6 * math.sin(u * 2), rz=0)
    draw_objects(fr, ph)

    def ui(img, fx):
        titulo(img, fx, 'Tu alerta: segundos.', 'Al tren bala le basta uno.', u, 1.2, y=150 if not HZ else None)
    fr.ui.append(ui)
    img = fin(fr, fi, flash=0.7 * (1 - seg(u, 1.4, 1.7)) if u >= 1.4 else 0.0)
    return sacudir(img, t, golpe_k(u, 1.4), 22)


def s_hookB(t, fi, u, d):
    """Short B, inicio 7 (macro extremo): empieza pegado al imán que brilla y la cámara se aleja hasta el tren flotando."""
    k = P.eout4(seg(u, -0.2, 1.3))
    fr = Frame(M.Cam(target=(lerp(0.6, -0.6, k), lerp(-0.12, 0.4, k), lerp(0.42, 0.0, k)), dist=lerp(0.55, 8.5 if HZ else 13.0, k),
                     yaw=lerp(-80, 28, k), pitch=lerp(-4, 6, k), cx=0.5, cy=0.5 if not HZ else 0.58))
    space(fr, t, floor='lines', floor_a=0.3 * k, bokeh=1.0, beam=0.35, beam_x=0.5)
    M.cristal(fr.base, fr.fx, 'FLOTA', u, t0=-0.5, cy=0.30 if not HZ else 0.42, entrada='zoom')
    ms = L.maglev(x=2.0, flota=1.0) + L.viga()
    draw_objects(fr, ms)
    for j in range(16):
        xx = -12 + ((j * 1.6 + t * 6) % 24)
        for zs in (-0.25, 0.25):
            line3(fr, [(xx, 0.07, zs), (xx + 0.5, 0.07, zs)], col=CYAN, w=4, a=0.6, glow=1.2)
    L.rachas(fr, t, a=0.8 * k, vel=14)

    def ui(img, fx):
        titulo(img, fx, 'No toca las vías.', 'Flota.', u, 1.1, y=150 if not HZ else None)
    fr.ui.append(ui)
    img = fin(fr, fi)
    return M.radial_blur(img, 0.2 * (1 - seg(u, 0.0, 1.0)), 0.5, 0.5) if u < 1.0 else img


def s_mandaA(t, fi, u, d):
    def ui(img, fx):
        pill(img, fx, 540 if not HZ else DX, 1250 if not HZ else DY, 'PARA QUIEN CORRE CON LA ALERTA', seg(u, 0.3, 0.6), size=28,
             border=AMARILLO)
    fr = Frame(camara(u, [(0, pose(2.6, 20, 6, tx=0.0, ty=P.PH_Y + 0.15)), (0.5, pose(3.0, 8, 4, tx=0.0, ty=P.PH_Y + 0.15))],
                      cy=0.45 if not HZ else None))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0, beam=0.5)
    ph = P.celular(pantalla_alerta(60, 0.8), ry=10 + 8 * math.sin(u * 3), rz=0)
    draw_objects(fr, ph)
    fr.ui.append(ui)
    return fin(fr, fi)


def s_mandaB(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        pill(img, fx, 540 if not HZ else DX, 1250 if not HZ else DY, 'PARA QUIEN DICE QUE LOS TRENES SON LENTOS', seg(u, 0.3, 0.6),
             size=26, border=CYAN)
    return mk_mag([(0, pose(9.0, 40, 6, tx=-1.0, ty=0.5)), (0.5, pose(8.0, 30, 6, tx=-1.0, ty=0.5))], ui=ui, vel=lambda u: 1.4,
                  campo=lambda u: 0.6)(t, fi, u, d)


# =================================================================== SHORTS: escenas para las frases partidas
def s_ninguno(t, fi, u, d):
    def ui(img, fx, u, t):
        tarjeta_dato(img, fx, DX, DY - 60 if HZ else 1250, '0', 'DESCARRILADOS EN SERVICIO', seg(u, 0.2, 0.5), VERDE, size=160)
    kw = lambda u: dict(vel=max(0.0, 0.4 - 0.4 * seg(u, 0.0, 1.0)), cat=0.0)
    return mk_tren_k([(0, pose(7.0, 140, 10, tx=-2.0, ty=0.8)), (0.4, pose(6.0, 155, 6, tx=-2.4, ty=0.8))], kw, ui=ui)(t, fi, u, d)


def s_nunca(t, fi, u, d):
    def ui(img, fx):
        kick(img, 'NIIGATA · 23 · OCTUBRE · 2004', u, 0.1, cx=W / 2, y=1250 if not HZ else 700)
        pill(img, fx, W / 2, 1360 if not HZ else 800, '¿NUNCA SE HA DESCARRILADO?', seg(u, 0.0, 0.3), size=30, border=ROJO)
    img = fondo(t, fi, u, ui, pal='2004', pal_t0=-0.2, pal_cy=0.40, pal_ent='golpe', z=[(0, 1.12), (0.4, 1.0)], floor='dots',
                claves=[(0, pose(7, 0, 20))])
    return sacudir(img, t, golpe_k(u, 0.0), 14)


def s_mag_jala(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        pill(img, fx, 540 if not HZ else DX, 1300 if not HZ else DY, 'EL CAMPO CORRE Y LO JALA', seg(u, 0.2, 0.5), size=28, border=CYAN)
    return mk_mag([(0, pose(4.5, -88, 4, tx=-1.0, ty=0.1)), (0.5, pose(5.0, -70, 8, tx=-1.0, ty=0.1))], campo=lambda u: 1.0,
                  xpos=lambda u: 2.0 * seg(u, 0.0, 3.0), ui=ui, vel=lambda u: 1.0)(t, fi, u, d)


def s_vel300(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        velocimetro(img, fx, 540 if not HZ else DX, 1230 if not HZ else DY - 100, 200, contador(u, 0.0, 1.2, 0, 300), 450,
                    seg(u, 0.0, 0.3))
        texto(img, fx, 540 if not HZ else DX, 1520 if not HZ else DY + 150, 'HOY · EN SERVICIO', 30, MUTED, seg(u, 0.4, 0.7), f='mono', glow=0)
    return mk_mag([(0, pose(8.0, -20, 4, tx=-1.0, ty=0.6)), (0.5, pose(7.0, -32, 6, tx=-1.0, ty=0.6))], ui=ui,
                  vel=lambda u: 1.2)(t, fi, u, d)


def s_mag_pasa(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        pill(img, fx, 540 if not HZ else DX, 1300 if not HZ else DY, 'MÁS QUE UN AVIÓN AL DESPEGAR', seg(u, 0.3, 0.6), size=28,
             border=WHITE)
    return mk_mag([(0, pose(5.0, 80, 2, tx=3.0, ty=0.6)), (0.5, pose(5.5, 60, 4, tx=1.0, ty=0.6))], ui=ui, vel=lambda u: 1.8,
                  xpos=lambda u: -6 + 10 * seg(u, 0.0, 2.2))(t, fi, u, d)


def s_pruebas(t, fi, u, d):
    def ui(img, fx, u, t, cam):
        P.pill_tachada(img, fx, 540 if not HZ else DX, 1240 if not HZ else DY - 60, 'EN SERVICIO', seg(u, 0.0, 0.2), seg(u, 0.4, 0.7), t,
                       size=34)
        pill(img, fx, 540 if not HZ else DX, 1380 if not HZ else DY + 80, 'SOLO PRUEBAS', seg(u, 0.6, 0.9), size=34, border=ROJO)
    return mk_mag([(0, pose(7.0, 150, 8, tx=-3.0, ty=0.6)), (0.5, pose(6.0, 165, 6, tx=-3.0, ty=0.6))], ui=ui,
                  vel=lambda u: 0.3)(t, fi, u, d)


def s_via_normal(t, fi, u, d):
    """No puede usar ni un metro de vía normal: rieles de tren de siempre que se tachan en rojo."""
    fr = Frame(camara(u, [(0, pose(6.0, -60, 26, tx=0.0, ty=0.0)), (0.5, pose(5.0, -45, 20, tx=0.0, ty=0.0))]))
    space(fr, t, floor='dots', floor_a=0.4, bokeh=1.0)
    k = seg(u, 0.5, 0.9)
    L.via(fr, -8, 8, a=1.0, postes=False)
    if k > 0:
        line3(fr, [(-2.0, 0.05, -1.4), (lerp(-2.0, 2.0, k), 0.05, lerp(-1.4, 1.4, k))], col=ROJO, w=8, a=1.0, glow=1.2)
        line3(fr, [(2.0, 0.05, -1.4), (lerp(2.0, -2.0, k), 0.05, lerp(-1.4, 1.4, k))], col=ROJO, w=8, a=1.0, glow=1.2)

    def ui(img, fx):
        pill(img, fx, 540 if not HZ else DX, 1300 if not HZ else DY, 'VÍA NORMAL: NO SIRVE', seg(u, 0.6, 0.9), size=30, border=ROJO)
    fr.ui.append(ui)
    return fin(fr, fi)
