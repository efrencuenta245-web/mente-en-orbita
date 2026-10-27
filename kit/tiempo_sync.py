"""Video de relatividad sincronizado con la narración (voz Carmelo).
La voz original dura 72.0 s: solo se acortan pausas largas (sin acelerar) para quedar en menos de 70 s."""
import sys, os, subprocess
import numpy as np
from PIL import Image
from scipy.io import wavfile
sys.path.insert(0, '/home/claude')
import tiempo as varg, anim

SRC = "/home/claude/narr_tie.mp3"
VOZ = "/home/claude/narr_tie_editada.wav"
TEMPO = 1.0
PAD = 0.04
GAP_IN, GAP_OUT = 0.20, 0.32

# tramos de voz (silencedetect -38 dB, 0.18 s) en el audio original
SEG = [(0.055, 3.199), (3.713, 5.294), (5.740, 7.070), (7.731, 10.943), (11.420, 12.211), (12.524, 13.283), (14.281, 15.647),
       (16.155, 19.923), (20.523, 24.734), (25.222, 28.286), (29.189, 29.795), (30.041, 30.831), (31.360, 34.614), (35.175, 37.190),
       (37.624, 40.045), (40.565, 41.620), (41.968, 44.699), (45.387, 48.698), (48.892, 49.969), (50.562, 52.666), (52.931, 55.131),
       (55.321, 59.007), (59.960, 61.048), (61.618, 65.013), (65.509, 67.421), (67.898, 69.655), (70.297, 71.813)]
MAP = [[(0, 0)], [(0, 1), (5, 2)], [(0, 3), (9, 4), (11, 5)], [(0, 6), (3, 7)], [(0, 8), (11, 9)], [(0, 10), (1, 11), (3, 12)],
       [(0, 13), (7, 14)], [(0, 15), (3, 16)], [(0, 17), (12, 18)], [(0, 19), (6, 20), (13, 21)], [(0, 22), (5, 23)], [(0, 24), (6, 25)],
       [(0, 26)]]
SPOKEN = {"500": "quinientos", "5": "cinco"}

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
    tmp = "/home/claude/narr_tie_tmp.wav"
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
    wavfile.write("/home/claude/narr_tie_cortada.wav", sr, np.clip(out, -32768, 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "/home/claude/narr_tie_cortada.wav", "-af", f"atempo={TEMPO}", VOZ], check=True)


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
        os.makedirs("/home/claude/tie_prev2", exist_ok=True)
        for ts in sys.argv[2:]:
            Image.fromarray(render_new(float(ts))).save(f"/home/claude/tie_prev2/t_{ts}.png")
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
