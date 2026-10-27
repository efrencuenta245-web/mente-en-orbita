"""Video de láseres entre satélites sincronizado con la narración (voz Carmelo, 68.8 s, velocidad natural)."""
import sys, os, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude')
import lasers, anim

VOZ = "/home/claude/narr_las.mp3"
SEG = [(0.045, 4.131), (4.601, 9.443), (10.075, 14.585), (15.387, 16.165), (16.772, 19.047), (19.583, 20.204), (20.445, 23.105),
       (23.526, 25.926), (26.559, 29.104), (29.310, 30.085), (30.774, 31.333), (31.519, 33.406), (33.755, 34.815), (35.044, 36.759),
       (37.630, 38.215), (38.775, 41.407), (41.612, 44.872), (45.523, 49.855), (50.741, 51.502), (52.087, 56.916), (57.489, 58.577),
       (58.768, 60.577), (61.470, 62.305), (62.553, 63.455), (64.043, 66.469), (67.075, 68.700)]
MAP = [[(0, 0)], [(0, 1)], [(0, 2)], [(0, 3), (3, 4)], [(0, 5), (2, 6), (12, 7)], [(0, 8), (8, 9)],
       [(0, 10), (2, 11), (7, 12), (10, 13)], [(0, 14), (2, 15), (9, 16)], [(0, 17)], [(0, 18), (3, 19)], [(0, 20), (3, 21)],
       [(0, 22), (2, 23), (4, 24)], [(0, 25)]]
SPOKEN = {"200": "doscientos", "50%": "cincuentaporciento"}
PIECES = [[(w, SEG[s][0], SEG[s][1]) for (w, s) in m] for m in MAP]

OLD_PH = lasers.anim.PH
OLD, NEW = [0.0], [0.0]
for i, (ph, pcs) in enumerate(zip(OLD_PH, PIECES)):
    OLD.append(lasers.PHR[i][0])
    NEW.append(pcs[0][1])
    for (w0, ta, tb) in pcs[1:]:
        OLD.append(ph['starts'][w0])
        NEW.append(ta)
    OLD.append(lasers.PHR[i][1])
    NEW.append(pcs[-1][2])
NEWDUR = round(PIECES[-1][-1][2] + 1.15, 2)
OLD.append(lasers.DUR)
NEW.append(NEWDUR)
assert all(b > a for a, b in zip(OLD, OLD[1:])), "OLD no creciente"
assert all(b > a for a, b in zip(NEW, NEW[1:])), "NEW no creciente"
NF = int(NEWDUR * 24)


def bw(t):
    return float(np.interp(t, NEW, OLD))


def fw(t):
    return float(np.interp(t, OLD, NEW))


newp = []
for (a0, b0, txt, keys), pcs in zip(lasers.PHR, PIECES):
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
        wts = [len(SPOKEN.get(w.strip('.,:¿?¡!'), w)) + 2 for w in words[w0:w1]]
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
    return lasers.render(bw(tn))


if __name__ == "__main__":
    mode = sys.argv[1]
    W, H, FPS = lasers.W, lasers.H, 24
    if mode == "anchors":
        for ct in lasers.CUTS + (lasers.T_OUT,):
            print("corte", ct, "->", round(fw(ct), 2))
        print("NEWDUR", NEWDUR)
    elif mode == "preview":
        os.makedirs("/home/claude/las_prev2", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render_new(float(ts))).save(f"/home/claude/las_prev2/t_{ts}.png")
        print("ok")
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
