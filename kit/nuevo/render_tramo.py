"""Re-render de un tramo de cuadros de cualquier reel (para corregir una escena sin repetir todo el render).
Uso: python3 render_tramo.py TEMA cuadro_a cuadro_b salida.mp4"""
import sys, os, subprocess, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
tema, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
sys.argv = [tema + '.py', 'x']
mod = importlib.import_module(tema)
import montaje
from motor2 import W, H, FPS
montaje.CTX.update({k: getattr(mod, k) for k in ('TEMA', 'TXT', 'ESCENAS', 'VOZ') if hasattr(mod, k)})
T, D = montaje.cargar(tema)
montaje.CTX['T'], montaje.CTX['DUR'] = T, D
if hasattr(mod, '_sfx_dinamicos'):
    mod._sfx_dinamicos()
montaje.CTX['_SC'] = montaje._escenas()
p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                      '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-maxrate', '10M', '-bufsize', '20M',
                      '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for fi in range(a, b):
    p.stdin.write(montaje.frame_at(fi / FPS, fi).tobytes())
p.stdin.close(); p.wait()
print('OK', a, b, flush=True)
