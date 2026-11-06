"""Muestra (no es un reel) de lo nuevo del 6-nov-2026: letras de cristal GIGANTES detrás del objeto y las 6
transiciones creativas (cubo, rompe, rebanadas, cristal, mosaico, remolino). Sin voz: el subtítulo dice qué se ve.
Sirve de ejemplo para copiar la idea (nunca la composición) en los reels nuevos.

  python3 demo_cristal.py tiempos_falsos     → tiempos fijos de 2 s por frase (no hay voz)
  python3 demo_cristal.py hoja | render | sonido
  python3 demo_cristal.py muestra            → /home/claude/demo_cristal_final.mp4 (efectos + música, sin voz)
"""
import math, os, sys, json, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import demo_estilo as D
from motor2 import Frame, Cam, space, draw_objects, finish, kicker, line3, dot3, seg, ease, eout, clamp, CYAN

S = M.SS
TEMA = 'demo_cristal'
TXT = ['Letras de cristal gigantes, detrás del objeto.',
       'Transición: cubo 3D.',
       'Transición: la pantalla se rompe.',
       'Transición: rebanadas.',
       'Transición: atraviesas la letra de cristal.',
       'Transición: mosaico digital.',
       'Transición: remolino.',
       'Y el final regresa al inicio.']


def _sacudir(img, t, t0, amp=20):
    dx, dy = P.sacudida(t, t0=t0, amp=amp)
    return P.mover_img(img, dx, dy)


def scr_carga(pct):
    def dib(d, im):
        f = M.font
        d.text((210, 250), f'{pct:.0f}%', font=f('sans', 120), fill=(245, 245, 247), anchor='mm')
        d.rounded_rectangle((90, 380, 330, 500), radius=22, outline=(220, 220, 224), width=5)
        d.rounded_rectangle((100, 390, 100 + 220 * pct / 100, 490), radius=14, fill=(110, 230, 140))
    return P.pantalla(dib)


# 0. gancho: «CELULAR» de cristal se estrella y el celular cae y rebota delante. Pasa en el pre-roll (u < 0), que es
#    lo que se ve al final del video (loop): el primer cuadro ya tiene todo y el último regresa a él.
def s_gancho(t, fi, u, d):
    pose = P.cam_rapida(u, [(-2.6, dict(dist=5.0, yaw=-40, pitch=12)), (-1.9, dict(dist=3.6, yaw=-6, pitch=7)),
                            (0.3, dict(dist=3.3, yaw=16, pitch=5)), (2.5, dict(dist=3.1, yaw=22, pitch=5))])
    fr = Frame(Cam(target=(0, 0.95, 0), cy=0.56, **pose))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'CELULAR', u, t0=-2.3, cy=0.45)
    e = P.entrada(u, -1.9, 0.45, 'cae')
    draw_objects(fr, P.celular(scr_carga(min(100, 40 + 60 * seg(u, -1.6, 1.4))), off=(0, max(0.0, -e['dy']), 0)))

    def ui(img, fx):
        kicker(img, 'EFECTO 03 · LETRAS DE CRISTAL', 150, seg(u, -1.3, -1.0))
    fr.ui.append(ui)
    return _sacudir(finish(fr, fi), t, t - u - 1.5)


# 1. pila que gira con «LITIO» que sube letra por letra
def s_pila(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=3.4, yaw=50, pitch=14)), (0.9, dict(dist=2.7, yaw=-12, pitch=6)),
                            (2.5, dict(dist=2.6, yaw=-20, pitch=5))])
    fr = Frame(Cam(target=(0, 0.55, 0), cy=0.55, **pose))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.4)
    M.cristal(fr.base, fr.fx, 'LITIO', u, t0=-0.15, cy=0.44, entrada='sube')
    e = P.entrada(u, -0.25, 0.3, 'gira')
    draw_objects(fr, P.tfk(P.pila(0.35 + 0.5 * seg(u, 0.2, 1.6)), s=max(0.05, e['escala']), ry=math.degrees(e['giro'])))
    return finish(fr, fi)


# 2. calor: la pila se calienta, termómetro y «CALOR» que crece con rebote
def s_calor(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=2.4, yaw=8, pitch=6)), (0.7, dict(dist=3.1, yaw=-24, pitch=10)),
                            (2.5, dict(dist=3.2, yaw=-28, pitch=10))])
    fr = Frame(Cam(target=(0, 0.55, 0), cy=0.55, **pose))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=0.8)
    M.cristal(fr.base, fr.fx, 'CALOR', u, t0=0.05, cy=0.42, entrada='zoom')
    draw_objects(fr, P.pila(0.8, caliente=seg(u, 0.1, 1.2), col_fill=(255, 140, 80)))
    P.ondas_calor(fr, t, 0.0, 1.1, 1.8, 0.6, k=seg(u, 0.3, 0.7))

    def ui(img, fx):
        P.termometro(img, fx, 170, 1350, 360, 0.3 + 0.6 * eout(seg(u, 0.2, 1.4)), '45 °C', k=seg(u, 0.1, 0.3))
    fr.ui.append(ui)
    return finish(fr, fi)


# 3. la Tierra de alambre con «SEÑAL»
def s_tierra(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=6.5, yaw=0, pitch=8)), (0.6, dict(dist=4.4, yaw=20, pitch=14)),
                            (2.5, dict(dist=4.2, yaw=26, pitch=14))])
    fr = Frame(Cam(target=(0, 1.25, 0), cy=0.48, **pose))
    space(fr, t, floor=None, bokeh=1.2)
    M.cristal(fr.base, fr.fx, 'SEÑAL', u, t0=0.0, cy=0.47)
    C = np.array([0, 1.25, 0])
    spin = t * 0.5
    camdir = M.norm(fr.cam.pos - C)
    for lat in range(-60, 90, 30):
        th = np.linspace(0, 2 * math.pi, 80)
        r = math.cos(math.radians(lat))
        Pp = np.stack([r * np.cos(th), np.full_like(th, math.sin(math.radians(lat))), r * np.sin(th)], 1)
        D._seg_by_depth(fr, D._rot(Pp, spin), C, camdir)
    for lon in range(0, 180, 30):
        th = np.linspace(0, 2 * math.pi, 80)
        a = math.radians(lon)
        Pp = np.stack([np.cos(th) * math.cos(a), np.sin(th), np.cos(th) * math.sin(a)], 1)
        D._seg_by_depth(fr, D._rot(Pp, spin), C, camdir)
    for j in range(6):
        a = j * math.pi / 3 + t * 0.8
        p = C + np.array([1.7 * math.cos(a), 0.35 * math.sin(a * 2), 1.7 * math.sin(a)])
        dot3(fr, p, r=5, col=CYAN, a=seg(u, 0.2 + j * 0.08, 0.4 + j * 0.08), glow=1.0)
    return finish(fr, fi)


# 4. rayos X del celular (después de atravesar «PANTALLA»)
def s_rayos(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=2.6, yaw=-6, pitch=6)), (0.8, dict(dist=3.0, yaw=28, pitch=8)),
                            (2.5, dict(dist=3.0, yaw=34, pitch=8))])
    fr = Frame(Cam(target=(0, 0.95, 0), cy=0.53, **pose))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.7)
    draw_objects(fr, P.celular(scr_carga(100), interior=True), xray=seg(u, 0.1, 0.5), keep=('in',))

    def ui(img, fx):
        kicker(img, 'RAYOS X DE CRISTAL', 150, seg(u, 0.2, 0.5), col=(150, 210, 230))
    fr.ui.append(ui)
    return finish(fr, fi)


# 5. el celular acostado en la almohada con «100%» de cristal
def s_almohada(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=4.0, yaw=-40, pitch=30)), (0.7, dict(dist=3.2, yaw=10, pitch=24)),
                            (2.5, dict(dist=3.1, yaw=16, pitch=24))])
    fr = Frame(Cam(target=(0, 0.3, 0), cy=0.58, **pose))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.5)
    M.cristal(fr.base, fr.fx, '100%', u, t0=0.0, cy=0.36)
    e = P.entrada(u, 0.0, 0.35, 'cae')
    draw_objects(fr, P.almohada() + P.celular(scr_carga(100), acostado=True, off=(0, 0.34 + max(0.0, -e['dy']), 0)))
    return finish(fr, fi)


# 6. el celular de nuevo, girando, antes del loop
def s_vuelta(t, fi, u, d):
    pose = P.cam_rapida(u, [(0.0, dict(dist=3.0, yaw=70, pitch=12)), (0.5, dict(dist=3.4, yaw=-10, pitch=6)),
                            (2.5, dict(dist=3.5, yaw=-16, pitch=6))])
    fr = Frame(Cam(target=(0, 0.95, 0), cy=0.56, **pose))
    space(fr, t, floor='dots', floor_a=0.9, bokeh=1.0, beam=0.55)
    M.cristal(fr.base, fr.fx, 'LOOP', u, t0=0.0, cy=0.45, entrada='sube')
    draw_objects(fr, P.celular(scr_carga(100), ry=-25 * (1 - P.eout4(seg(u, 0.0, 0.6)))))
    return finish(fr, fi)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.5)),
           dict(desde=1, fn=s_pila, tr='cubo'),
           dict(desde=2, fn=s_calor, tr='rompe', c=(0.5, 0.42)),
           dict(desde=3, fn=s_tierra, tr='rebanadas'),
           dict(desde=4, fn=s_rayos, tr='cristal', palabra='PANTALLA'),
           dict(desde=5, fn=s_almohada, tr='mosaico'),
           dict(desde=6, fn=s_vuelta, tr='remolino'),
           dict(desde=7, loop=True, tr='giro')]


def tiempos_falsos():
    T = [(round(0.25 + 2.0 * i, 2), round(0.25 + 2.0 * i + 1.6, 2)) for i in range(len(TXT))]
    json.dump({'T': T, 'DUR': round(T[-1][1] + 0.4, 2)}, open(f'/home/claude/tiempos_{TEMA}.json', 'w'))
    from scipy.io import wavfile
    dur = T[-1][1] + 0.4
    wavfile.write(f'/home/claude/narr_{TEMA}_pad.wav', 48000, np.zeros(int(dur * 48000), np.int16))
    print('ok', T)


def muestra():
    """Efectos + música (sin voz) sobre el render: /home/claude/demo_cristal_final.mp4."""
    montaje.CTX.update(TEMA=TEMA, TXT=TXT, ESCENAS=ESCENAS)
    montaje.init(globals())
    out = '/home/claude'
    montaje.sonido(f'{out}/efectos_{TEMA}.wav')
    dur = montaje.CTX['DUR']
    subprocess.run(['python3', os.path.join(montaje.KIT, 'musica.py'), str(dur), f'{out}/musica_{TEMA}.wav', '61', '104', '0'],
                   check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', f'{out}/{TEMA}_sin_audio.mp4', '-i', f'{out}/efectos_{TEMA}.wav',
                    '-i', f'{out}/musica_{TEMA}.wav', '-filter_complex',
                    '[1:a]aresample=48000,volume=0.9[fx];[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.45[mu];'
                    '[fx][mu]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]',
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', f'{out}/{TEMA}_final.mp4'], check=True)
    print('ok', f'{out}/{TEMA}_final.mp4')


if __name__ == '__main__':
    if sys.argv[1] == 'tiempos_falsos':
        tiempos_falsos()
    elif sys.argv[1] == 'muestra':
        muestra()
    else:
        montaje.cli(globals())
