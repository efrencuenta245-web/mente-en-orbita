"""Video de la vasectomía sincronizado con la narración (voz Carmelo).
La voz original dura 69.1 s: solo se acortan pausas largas (sin acelerar)."""
import sys, os, subprocess
import numpy as np
from PIL import Image
from scipy.io import wavfile
sys.path.insert(0, '/home/claude')
import vasec as varg, anim

SRC = "/home/claude/narr_vas.mp3"
VOZ = "/home/claude/narr_vas_editada.wav"
TEMPO = 1.0
PAD = 0.04
GAP_IN, GAP_OUT = 0.22, 0.36

# tramos de voz (silencedetect -38 dB, 0.18 s) en el audio original
SEG = [(0.045, 2.612), (3.084, 4.019), (4.303, 6.157), (6.770, 8.446), (9.337, 13.208), (13.757, 15.568), (15.901, 18.013),
       (18.560, 22.219), (22.850, 25.181), (25.633, 28.651), (29.469, 31.564), (31.991, 34.522), (35.060, 36.378), (36.596, 37.819),
       (38.394, 39.856), (40.481, 42.751), (43.056, 44.606), (45.127, 48.665), (49.369, 49.719), (50.004, 51.628), (51.976, 54.995),
       (55.492, 58.184), (58.551, 61.731), (62.306, 63.805), (64.132, 66.659), (67.352, 68.960)]
MAP = [[(0, 0), (7, 1), (10, 2)], [(0, 3)], [(0, 4)], [(0, 5), (5, 6)], [(0, 7)], [(0, 8), (7, 9)], [(0, 10), (6, 11)],
       [(0, 12), (3, 13), (7, 14)], [(0, 15), (6, 16)], [(0, 17)], [(0, 18), (1, 19), (5, 20)], [(0, 21), (5, 22)], [(0, 23), (3, 24)],
       [(0, 25)]]
SPOKEN = {"30": "treinta", "5%": "cincoporciento", "15": "quince", "99%": "noventaynueveporciento", "IMSS": "ims"}

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
    tmp = "/home/claude/narr_vas_tmp.wav"
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
    wavfile.write("/home/claude/narr_vas_cortada.wav", sr, np.clip(out, -32768, 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "/home/claude/narr_vas_cortada.wav", "-af", f"atempo={TEMPO}", VOZ], check=True)


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
        os.makedirs("/home/claude/vas_prev2", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render_new(float(ts))).save(f"/home/claude/vas_prev2/t_{ts}.png")
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
