"""Prueba del estilo nuevo en HORIZONTAL (1920x1080) para el video largo de YouTube.
Muestra cómo acomodar: objeto 3D a un lado, título del otro, subtítulo abajo (y=880) y kicker arriba.
Uso: MOTOR_FORMATO=h python3 demo_horizontal.py T [T…]   (guarda /home/claude/hprev_T.png)"""
import os, sys
os.environ['MOTOR_FORMATO'] = 'h'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import motor2 as M
import demo_estilo as D
from motor2 import Frame, cam_path, space, draw_objects, finish, title, kicker, word_caption, pill, glass_type, seg, ease, eout

assert M.HORIZONTAL and M.W == 1920
S = M.SS
# cámara con el objeto a la derecha (cx=0.68) para dejar la izquierda al texto
K = [(0.0, dict(target=(0, 0.95, 0), dist=4.0, yaw=-30, pitch=8, fk=1.5, cx=0.68, cy=0.55)),
     (4.0, dict(target=(0, 0.98, 0), dist=3.3, yaw=-12, pitch=5, fk=1.5, cx=0.68, cy=0.55))]


def frame(t, fi=0):
    fr = Frame(cam_path(t, K))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5, beam_x=0.68)
    glass_type(fr.base, fr.fx, 'NORTE', 1306 * S, 640 * S, 230 * S, k=ease(seg(t, 0.0, 0.6)), fill_a=0.06)
    draw_objects(fr, [m for m in D.phone(t) if m.name != 'in'])

    def ui(img, fx):
        kicker(img, 'CAPÍTULO 1 · EL CHIP', 300, seg(t, 0.2, 0.5), cx=560)
        title(img, fx, [('Tu celular', 'sans'), ('sabe dónde está el norte.', 'serif')], 350, seg(t, 0.3, 0.9), size=72, cx=560)
        pill(img, fx, 560, 580, 'SIN INTERNET', eout(seg(t, 1.2, 1.5)), size=32)
        word_caption(img, fx, 'Y no, no usa el GPS.'.split(), 1.6, t, y=900, size=50, per=0.3, cx=960, maxw=1300)
    fr.ui.append(ui)
    out = finish(fr, fi)
    return out


if __name__ == '__main__':
    for ts in sys.argv[1:]:
        t = float(ts)
        Image.fromarray(frame(t, int(t * 24))).save(f'/home/claude/hprev_{ts}.png')
