"""Render de un tramo de cuadros con 2 procesos (para videos largos que no caben en una sola corrida).
Uso: python3 render_pool_tb.py MODULO cuadro_a cuadro_b salida.mp4   (MODULO = trenbala_largo o trenbala_short con SHORT=A/B)"""
import sys, os, subprocess, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
tema, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
sys.argv = [tema + '.py', 'x']
mod = importlib.import_module(tema)
import montaje
from motor2 import W, H, FPS
montaje.CTX.update(dict(TEMA=mod.TEMA, TXT=mod.TXT, ESCENAS=mod.ESCENAS, VOZ=mod.TXT, CAP=getattr(mod, 'CAP', {})))
T, D = montaje.cargar(mod.TEMA)
montaje.CTX['T'], montaje.CTX['DUR'] = T, D
montaje.CTX['_SC'] = montaje._escenas()
b = min(b, int(round(D * FPS)))


def work(fi):
    return fi, montaje.frame_at(fi / FPS, fi).tobytes()


if __name__ == '__main__':
    from multiprocessing import Pool
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-f', 'mpegts', out],
                         stdin=subprocess.PIPE)
    with Pool(2) as pool:
        for fi, buf in pool.imap(work, range(a, b), chunksize=2):
            p.stdin.write(buf)
            if fi % 240 == 0:
                print('cuadro', fi, '/', b, flush=True)
    p.stdin.close()
    p.wait()
    print('OK', a, b, flush=True)
