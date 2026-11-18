"""Miniatura 1280x720 del largo del tren bala (estilo nuevo): tren bala grande a la derecha, «2 h 30» de cristal
y «CDMX → GDL» a la izquierda. Uso: python3 trenbala_miniatura.py SALIDA.jpg"""
import os, sys
os.environ['MOTOR_FORMATO'] = 'h'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import trenbala_lib as L
from trenbala_lib import M, P, Frame, space, draw_objects, finish, pose, camara, texto, CYAN, WHITE, NARANJA


def miniatura(out):
    u = 2.0
    fr = Frame(camara(u, [(0, pose(6.4, -34, 7, tx=-0.6, ty=0.75))], cx=0.62, cy=0.60))
    space(fr, 3.0, floor='dots', floor_a=0.5, bokeh=1.0, beam=0.55, beam_x=0.62)
    M.cristal(fr.base, fr.fx, '2 h 30', 3.0, t0=0.0, cy=0.30, ancho=0.62, alto=0.42, cx=0.36, entrada='golpe', brillo=1.25)
    L.via(fr, mov=0.3, cat=0.7)
    L.rachas(fr, 1.3, a=1.0, vel=16)
    draw_objects(fr, L.tren_bala(x=1.6, carros=2))

    def ui(img, fx):
        d = ImageDraw.Draw(img)
        # pastilla grande con la ruta
        x0, y0 = 70, 700
        d.rounded_rectangle((x0, y0, x0 + 700, y0 + 150), radius=75, fill=(10, 12, 16), outline=CYAN, width=6)
        ImageDraw.Draw(fx).rounded_rectangle((x0, y0, x0 + 700, y0 + 150), radius=75, outline=M.scale_c(CYAN, 0.6), width=12)
        texto(img, fx, x0 + 350, y0 + 75, 'CDMX → GDL', 88, WHITE, 1.0, f='sansx', glow=0.3)
    fr.ui.append(ui)
    img = finish(fr, 7, grain=0.02)
    Image.fromarray(img).resize((1280, 720), Image.LANCZOS).save(out, quality=92)
    Image.fromarray(img).resize((320, 180), Image.LANCZOS).save(out.replace('.jpg', '_320.png'))
    print(out)


if __name__ == '__main__':
    miniatura(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/miniatura_trenbala.jpg')
