"""Render por tramos (procesos nuevos por tramo para no acumular memoria). Uso: render_seg.py a b out.mp4"""
import sys, os, subprocess
sys.path.insert(0, '/home/claude/mente-en-orbita/kit/nuevo')
os.chdir('/home/claude/mente-en-orbita/kit/nuevo')
a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
sys.argv = ['alerta.py', 'x']
import alerta, montaje
from motor2 import W, H, FPS
montaje.CTX.update({k: getattr(alerta, k) for k in ('TEMA', 'TXT', 'ESCENAS', 'VOZ')})
T, D = montaje.cargar('alerta')
montaje.CTX['T'], montaje.CTX['DUR'] = T, D
montaje.CTX['_SC'] = montaje._escenas()
p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                      '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-maxrate', '10M', '-bufsize', '20M',
                      '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
for fi in range(a, b):
    p.stdin.write(montaje.frame_at(fi / FPS, fi).tobytes())
p.stdin.close(); p.wait()
print('OK', a, b, flush=True)
