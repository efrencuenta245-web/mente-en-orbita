import sys, os, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude')
import fo, anim

OLD = [0.0, 0.4, 4.6, 4.7, 8.8, 9.6, 12.9, 13.7, 16.3, 16.5, 22.0, 22.8, 26.8, 26.9, 32.9, 33.6, 36.2, 37.2, 41.5, 42.3, 46.3, 46.4, 52.1, 52.9, 59.4, 60.2, 64.0, 64.6, 66.6, 67.6]
NEW = [0.0, 0.10, 3.33, 3.975, 7.461, 8.467, 12.340, 13.088, 15.686, 16.299, 23.032, 23.746, 27.321, 27.35, 32.116, 32.721, 35.293, 36.263, 39.902, 40.582, 44.781, 45.300, 49.698, 50.441, 56.243, 56.954, 60.706, 61.588, 63.018, 64.0]
NEWDUR = 64.0
NF = int(NEWDUR * 24)


def bw(t): return float(np.interp(t, NEW, OLD))
def fw(t): return float(np.interp(t, OLD, NEW))


PIECES = [
    [(0, 0.10, 3.33)],
    [(0, 3.975, 5.442), (6, 5.649, 7.461)],
    [(0, 8.467, 10.773), (6, 11.301, 12.340)],
    [(0, 13.088, 15.686)],
    [(0, 16.299, 18.447), (6, 18.868, 20.322), (8, 20.682, 23.032)],
    [(0, 23.746, 25.293), (6, 25.875, 27.321)],
    [(0, 27.321, 28.917), (6, 29.306, 32.116)],
    [(0, 32.721, 35.293)],
    [(0, 36.263, 39.902)],
    [(0, 40.582, 44.781)],
    [(0, 45.300, 47.428), (9, 47.870, 49.698)],
    [(0, 50.441, 51.490), (5, 51.676, 54.285), (13, 54.817, 56.243)],
    [(0, 56.954, 58.926), (7, 59.404, 60.706)],
    [(0, 61.588, 63.018)],
]
newp = []
for (a0, b0, txt, keys), pcs in zip(fo.PHR, PIECES):
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
    return fo.render(bw(tn))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        os.makedirs("/home/claude/prevfo2", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render_new(float(ts))).save(f"/home/claude/prevfo2/t_{ts}.png")
        print("ok")
    else:
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{fo.W}x{fo.H}", "-r", "24", "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(a, b):
            pr.stdin.write(render_new(f / 24.0).tobytes())
        pr.stdin.close()
        pr.wait()
        print("ok", a, b, "de", NF)
