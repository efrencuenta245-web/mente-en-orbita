"""Versión del video del GPS sincronizada con la narración (voz Carmelo, 70.7 s).
Mapa de tiempos por tramos: tiempo nuevo (voz) -> tiempo viejo (animación)."""
import sys, os, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude')
import gps, anim

# tramos de voz detectados con silencedetect (-38 dB, 0.18 s)
SEG = [(0.114, 2.329), (2.684, 4.016), (4.795, 8.162), (8.763, 11.681), (11.948, 14.137), (14.670, 16.581), (16.786, 19.577),
       (20.026, 22.058), (22.310, 23.137), (23.420, 24.505), (25.102, 26.729), (27.126, 28.081), (28.586, 30.747), (30.979, 33.336),
       (33.751, 34.634), (34.886, 37.641), (38.064, 39.169), (39.470, 41.095), (41.712, 42.05), (42.511, 45.140), (45.485, 49.085),
       (49.497, 50.973), (51.333, 52.012), (52.215, 55.448), (55.810, 59.889), (60.325, 61.168), (61.376, 63.709), (64.193, 66.137),
       (66.549, 68.444), (68.935, 70.477)]
# por frase: (primera palabra del tramo, índice del tramo)
MAP = [[(0, 0), (6, 1)], [(0, 2)], [(0, 3), (7, 4)], [(0, 5), (5, 6)], [(0, 7), (6, 8), (8, 9)], [(0, 10), (6, 11)],
       [(0, 12), (9, 13)], [(0, 14), (3, 15)], [(0, 16), (3, 17), (8, 18)], [(0, 19), (8, 20)], [(0, 21), (4, 22), (6, 23)],
       [(0, 24)], [(0, 25), (2, 26)], [(0, 27), (6, 28)], [(0, 29)]]
PIECES = [[(w, SEG[s][0], SEG[s][1]) for (w, s) in m] for m in MAP]

OLD_PH = gps.anim.PH
OLD, NEW = [0.0], [0.0]
for i, (ph, pcs) in enumerate(zip(OLD_PH, PIECES)):
    a_old, b_old = gps.PHR[i][0], gps.PHR[i][1]
    OLD.append(a_old)
    NEW.append(pcs[0][1])
    for (w0, ta, tb) in pcs[1:]:
        OLD.append(ph['starts'][w0])
        NEW.append(ta)
    OLD.append(b_old)
    NEW.append(pcs[-1][2])
NEWDUR = 71.6
OLD.append(gps.DUR)
NEW.append(NEWDUR)
assert all(b > a for a, b in zip(OLD, OLD[1:])), "OLD no creciente"
assert all(b > a for a, b in zip(NEW, NEW[1:])), "NEW no creciente"
NF = int(NEWDUR * 24)


def bw(t):
    return float(np.interp(t, NEW, OLD))


def fw(t):
    return float(np.interp(t, OLD, NEW))


# subtítulos con los tiempos reales de la voz
newp = []
for (a0, b0, txt, keys), pcs in zip(gps.PHR, PIECES):
    newp.append((pcs[0][1], pcs[-1][2] + 0.15, txt, keys))
anim.PHR = newp
anim.PH = anim.build_phrases()
for i in range(len(anim.PH) - 1):
    anim.PH[i]['b'] = min(anim.PH[i]['b'], anim.PH[i + 1]['a'] - 0.31)
for ph, pcs in zip(anim.PH, PIECES):
    words = ph['words']
    n = len(words)
    starts = [0.0] * n
    for k, (w0, ta, tb) in enumerate(pcs):
        w1 = pcs[k + 1][0] if k + 1 < len(pcs) else n
        wts = [len(w) + 2 for w in words[w0:w1]]
        tot = sum(wts)
        acc = ta
        for i, wt in zip(range(w0, w1), wts):
            starts[i] = acc
            acc += (tb - ta) * wt / tot
    ph['starts'] = starts

_orig = anim.draw_caption
CUR = [0.0]
anim.draw_caption = lambda l2, t: _orig(l2, CUR[0])


def render_new(tn):
    CUR[0] = tn
    return gps.render(bw(tn))


if __name__ == "__main__":
    mode = sys.argv[1]
    W, H, FPS = gps.W, gps.H, 24
    if mode == "preview":
        os.makedirs("/home/claude/gps_prev2", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render_new(float(ts))).save(f"/home/claude/gps_prev2/t_{ts}.png")
        print("ok")
    elif mode == "anchors":
        for o, n_ in zip(OLD, NEW):
            print(f"{o:7.2f} -> {n_:7.2f}")
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fr in range(a, b):
            pr.stdin.write(render_new(fr / FPS).tobytes())
        pr.stdin.close()
        pr.wait()
        print("ok", a, b, "de", NF)
