"""Video de la Stark Varg sincronizado con la narración (voz Carmelo).
La voz original dura 59.6 s: se acortan pausas y se acelera 10% (atempo) para quedar en ~50 s."""
import sys, os, subprocess
import numpy as np
from PIL import Image
from scipy.io import wavfile
sys.path.insert(0, '/home/claude')
import varg, anim

SRC = "/home/claude/narr_varg.mp3"
VOZ = "/home/claude/narr_varg_editada.wav"
TEMPO = 1.10
PAD = 0.04
GAP_IN, GAP_OUT = 0.16, 0.28

# tramos de voz (silencedetect -38 dB, 0.18 s) en el audio original
SEG = [(0.096, 2.151), (2.466, 4.787), (5.244, 9.285), (9.855, 13.517), (13.996, 15.300), (15.926, 16.915), (17.323, 17.993),
       (18.463, 21.670), (22.054, 22.550), (22.800, 23.722), (24.322, 25.293), (25.694, 26.291), (26.637, 28.834), (29.169, 29.802),
       (30.181, 31.380), (32.002, 33.024), (33.360, 38.005), (38.615, 39.274), (39.645, 43.368), (43.674, 45.321), (45.714, 49.572),
       (49.763, 51.748), (52.347, 53.199), (53.639, 55.529), (55.733, 57.277), (57.743, 59.350)]
MAP = [[(0, 0)], [(0, 1)], [(0, 2)], [(0, 3), (7, 4)], [(0, 5), (2, 6), (3, 7), (9, 8), (11, 9)],
       [(0, 10), (2, 11), (3, 12), (8, 13), (10, 14)], [(0, 15), (2, 16)], [(0, 17), (2, 18), (12, 19)], [(0, 20), (10, 21)],
       [(0, 22), (3, 23), (6, 24)], [(0, 25)]]
SPOKEN = {"450": "cuatrocientoscincuenta", "7.2": "sietepuntodos", "2026": "dosmilveintiséis", "118": "cientodieciocho"}

# --- nueva línea de tiempo de la voz (pausas recortadas + tempo) ---
first_of_phrase = {m[0][1] for m in MAP}
NSEG = []
cur = 0.0
for i, (a, b) in enumerate(SEG):
    a0, b0 = max(0.0, a - PAD), b + PAD
    if i > 0:
        gap = GAP_OUT if i in first_of_phrase else GAP_IN
        orig_gap = (a - PAD) - (SEG[i - 1][1] + PAD)
        cur += max(0.0, min(gap, orig_gap))
    NSEG.append((cur + PAD, cur + (b0 - a0) - PAD, a0, b0, cur))
    cur += b0 - a0
VOICE_LEN = cur / TEMPO
SEGN = [(s / TEMPO, e / TEMPO) for (s, e, _, _, _) in NSEG]


def build_voice():
    tmp = "/home/claude/narr_varg_tmp.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", SRC, "-ac", "1", "-ar", "44100", tmp], check=True)
    sr, x = wavfile.read(tmp)
    x = x.astype(np.float32)
    out = np.zeros(int((cur + 0.2) * sr), np.float32)
    fd = int(0.006 * sr)
    for (s, e, a0, b0, pos) in NSEG:
        piece = x[int(a0 * sr):int(b0 * sr)].copy()
        piece[:fd] *= np.linspace(0, 1, fd)
        piece[-fd:] *= np.linspace(1, 0, fd)
        i0 = int(pos * sr)
        out[i0:i0 + len(piece)] += piece[:len(out) - i0]
    wavfile.write("/home/claude/narr_varg_cortada.wav", sr, np.clip(out, -32768, 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "/home/claude/narr_varg_cortada.wav", "-af", f"atempo={TEMPO}", VOZ], check=True)


PIECES = [[(w, SEGN[s][0], SEGN[s][1]) for (w, s) in m] for m in MAP]
OLD_PH = varg.anim.PH
OLD, NEW = [0.0], [0.0]
for i, (ph, pcs) in enumerate(zip(OLD_PH, PIECES)):
    OLD.append(varg.PHR[i][0])
    NEW.append(pcs[0][1])
    for (w0, ta, tb) in pcs[1:]:
        OLD.append(ph['starts'][w0])
        NEW.append(ta)
    OLD.append(varg.PHR[i][1])
    NEW.append(pcs[-1][2])
NEWDUR = round(PIECES[-1][-1][2] + 1.1, 2)
OLD.append(varg.DUR)
NEW.append(NEWDUR)
assert all(b > a for a, b in zip(OLD, OLD[1:])), "OLD no creciente"
assert all(b > a for a, b in zip(NEW, NEW[1:])), "NEW no creciente"
NF = int(NEWDUR * 24)


def bw(t):
    return float(np.interp(t, NEW, OLD))


def fw(t):
    return float(np.interp(t, OLD, NEW))


newp = []
for (a0, b0, txt, keys), pcs in zip(varg.PHR, PIECES):
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
        wts = [len(SPOKEN.get(w.strip('.,:¿?'), w)) + 2 for w in words[w0:w1]]
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
    return varg.render(bw(tn))


if __name__ == "__main__":
    mode = sys.argv[1]
    W, H, FPS = varg.W, varg.H, 24
    if mode == "voz":
        build_voice()
        print("voz editada:", VOZ, "duración esperada", round(VOICE_LEN, 2), "video", NEWDUR)
    elif mode == "anchors":
        for o, n_ in zip(OLD, NEW):
            print(f"{o:7.2f} -> {n_:7.2f}")
        for ct in varg.CUTS + (varg.T_OUT,):
            print("corte", ct, "->", round(fw(ct), 2))
    elif mode == "preview":
        os.makedirs("/home/claude/varg_prev2", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render_new(float(ts))).save(f"/home/claude/varg_prev2/t_{ts}.png")
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
