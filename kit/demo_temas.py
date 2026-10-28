"""Muestra de los 9 temas visuales con la misma escena (para elegir tema)."""
import os, sys
import escenas as S
from escenas import *

def s_demo(fr, t, lt, dur):
    fr.cam = Cam(target=(0, 0.8, 0), dist=vfit(6.6), yaw=-18, pitch=14)
    fr.meshes.append(sphere(0.6, (240, 88, 138), gloss=0.6).tf(t=(-1.4, 0.6, 0)))
    fr.meshes.append(box(1.0, 1.4, 1.0, (66, 124, 214)).tf(ry=20, t=(0.2, 0, -0.2)))
    fr.meshes.append(cyl(0.45, 0.9, (230, 178, 58), n=28).tf(t=(1.6, 0, 0.3)))
    fr.under.append(lambda d, cam: ring3(d, cam, (0, 0, 0), 2.4, INK, 1.6, 0.7))
    head(fr, ['Tema:', E.TEMA + '.'], (240, 88, 138), t, t - lt - 1, kicker='Mente en órbita')
    ui_pill(fr, 'Recreación', 1.0, dotc=(240, 88, 138))

if __name__ == '__main__':
    S.main([(('c0', 0), s_demo)], {})
