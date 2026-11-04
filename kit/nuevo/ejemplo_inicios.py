"""Ejemplos de inicios rápidos y distintos (ESTILO.md §11-12). No es un reel: son 3 escenas de muestra para copiar
la idea (nunca la composición) en cada video nuevo. Todas funcionan con u negativo (el final en loop las repite).

  python3 ejemplo_inicios.py   → /home/claude/ejemplo_inicios.png (3 filas × 6 cuadros)

  A) tipo 2  «cae y rebota»: la pila cae, rebota, la cámara se sacude y el título se estrella.
  B) tipo 3  «se arma solo»: vista explotada que se junta mientras la cámara orbita 70° de golpe.
  C) tipo 5  «número gigante»: la cifra golpea, sacudida, y un crash zoom revela el objeto.
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import motor2 as M
import piezas as P
from motor2 import Frame, Cam, space, draw_objects, finish, kicker, seg, clamp
import demo_estilo as D

S = M.SS


def _sacudir(img, t, t0, amp=22):
    dx, dy = P.sacudida(t, t0=t0, amp=amp)
    return P.mover_img(img, dx, dy)


# ---------------------------------------------------------------- A) cae y rebota + título que se estrella
def s_cae(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=4.2, yaw=-25, pitch=10)),
                            (0.55, dict(dist=3.2, yaw=12, pitch=6)),      # golpe de cámara al aterrizar
                            (2.5, dict(dist=2.9, yaw=20, pitch=5))])
    fr = Frame(Cam(target=(0, 0.6, 0), cy=0.56, **pose))
    space(fr, t, floor='lines', floor_a=0.9, bokeh=1.0, beam=0.6)
    e = P.entrada(u, 0.0, 0.5, 'cae')                                   # cae desde arriba con rebote
    x, y = fr.cam.proj([(0, 0.02, 0)])[0][0]
    D.shadow_blob(fr, x, y, 260 * (0.6 + 0.4 * (1 + e['dy'] / 3)), 60, 0.8)
    draw_objects(fr, P.pila(0.35 + 0.1 * math.sin(t * 3), y=max(0.0, -e['dy'])))

    def ui(img, fx):
        kicker(img, 'BATERÍA DE LITIO', 150, seg(u, 0.5, 0.8))
        P.titulo_golpe(img, fx, [('Tu batería no se gasta', 'sans'), ('al usarla.', 'serif')], 200, seg(u, 0.35, 0.5), size=72)
    fr.ui.append(ui)
    return _sacudir(finish(fr, fi), t, t - u + 0.5)                     # sacudida justo cuando el título cae


# ---------------------------------------------------------------- B) se arma solo (vista explotada al revés)
def s_arma(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=3.8, yaw=-60, pitch=22)),
                            (0.9, dict(dist=3.0, yaw=10, pitch=8)),       # órbita de 70° en ~0.3 s
                            (2.5, dict(dist=2.7, yaw=18, pitch=6))])
    fr = Frame(Cam(target=(0, 0.95, 0), cy=0.55, **pose))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    k = 1 - P.eout4(seg(u, 0.0, 0.9))                                  # 1 = separado → 0 = armado (clic)
    piezas = P.celular(P.pantalla(lambda dd, im: None), interior=True)
    draw_objects(fr, P.despiece(piezas, k, centro=(0, 0.95, 0), fuerza=1.4, giro=0.8), xray=0.6 * k, keep=('in',))

    def ui(img, fx):
        kicker(img, 'POR DENTRO', 150, seg(u, 0.9, 1.2))
        P.titulo_golpe(img, fx, [('Tu celular tiene', 'sans'), ('más de 1 000 piezas.', 'serif')], 200, seg(u, 0.9, 1.05), size=72)
    fr.ui.append(ui)
    return _sacudir(finish(fr, fi), t, t - u + 0.9, amp=14)


# ---------------------------------------------------------------- C) número gigante + crash zoom
def s_numero(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=9.0, yaw=0, pitch=4)),
                            (0.8, dict(dist=3.0, yaw=-18, pitch=8)),      # crash zoom al objeto
                            (2.5, dict(dist=2.7, yaw=-10, pitch=6))])
    fr = Frame(Cam(target=(0, 0.6, 0), cy=0.6, **pose))
    space(fr, t, floor='dots', floor_a=0.8 * seg(u, 0.6, 0.9), bokeh=1.0, beam=0.4)
    if u > 0.6:
        e = P.entrada(u, 0.6, 0.25, 'pop')
        draw_objects(fr, P.tfk(P.pila(0.8), s=max(0.05, e['escala'])))

    def ui(img, fx):
        P.numero_golpe(img, fx, '500', 760 if u < 0.8 else 760 - 520 * P.eout4(seg(u, 0.8, 1.1)), seg(u, 0.0, 0.18),
                       size=330 if u < 0.8 else 330 - 170 * P.eout4(seg(u, 0.8, 1.1)))
        kicker(img, 'CICLOS DE CARGA', 330, seg(u, 1.0, 1.3))
    fr.ui.append(ui)
    return _sacudir(finish(fr, fi), t, t - u + 0.18, amp=26)


if __name__ == '__main__':
    filas = []
    for fn in (s_cae, s_arma, s_numero):
        fila = []
        for u in (-0.3, 0.12, 0.3, 0.5, 0.9, 1.6):
            t = 10 + u
            fila.append(Image.fromarray(fn(t, int(t * 24), u, 3.0)).resize((216, 384)))
        filas.append(fila)
    hoja = Image.new('RGB', (216 * 6, 384 * 3))
    for r, fila in enumerate(filas):
        for k, im in enumerate(fila):
            hoja.paste(im, (216 * k, 384 * r))
    hoja.save('/home/claude/ejemplo_inicios.png')
    print('ok /home/claude/ejemplo_inicios.png')
