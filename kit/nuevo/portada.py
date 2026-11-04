"""Portada (miniatura) de cada video, con el mismo diseño siempre para que el perfil se vea limpio y ordenado.
Formato 1080x1920; todo lo importante va dentro del recorte 3:4 de la cuadrícula de Instagram y TikTok
(y de 240 a 1680). Uso:
  python3 portada.py FONDO.png SALIDA.jpg "Línea 1 (sans)" "línea 2 (itálica)" [CATEGORÍA]
  FONDO: un cuadro del video sin subtítulos (p. ej. `python3 TEMA.py preview 0.1`).
  CATEGORÍA: TECNOLOGÍA, ESPACIO, CUERPO, PLANETA, MÉXICO… o el nombre de la serie (LO QUE NO VES, DUELO…).
Para que la portada también sea el primer cuadro del video (respaldo si una red ignora la miniatura):
  python3 portada.py --primer-cuadro VIDEO.mp4 PORTADA.jpg SALIDA.mp4"""
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['MOTOR_FORMATO'] = 'v'
import motor2 as M

W, H = 1080, 1920
SAFE_TOP, SAFE_BOT = 240, 1680
CYAN = M.CYAN


def _fit(d, txt, kind, max_w, start):
    s = start
    while s > 40 and d.textlength(txt, font=M.font(kind, s)) > max_w:
        s -= 2
    return M.font(kind, s), s


def make(fondo, out, l1, l2, cat='MENTE EN ÓRBITA'):
    bg = Image.open(fondo).convert('RGB').resize((W, H), Image.LANCZOS)
    a = np.asarray(bg, np.float32) * 0.78
    # degradado oscuro arriba para que el título siempre se lea igual
    g = np.clip(1 - (np.arange(H, dtype=np.float32) - 200) / 800, 0, 1)[:, None, None] * 0.7
    a = a * (1 - g)
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # categoría (kicker) con espaciado
    f = M.font('mono', 30)
    cat = cat.upper()
    ws = [d.textlength(ch, font=f) for ch in cat]
    x = (W - (sum(ws) + 8 * (len(cat) - 1))) / 2
    for ch, w in zip(cat, ws):
        d.text((x, 300), ch, font=f, fill=(150, 210, 230))
        x += w + 8
    # título: sans arriba, serif itálica abajo (mismo lugar y tamaño máximo en todas)
    glow = Image.new('L', (W, H), 0)
    dg = ImageDraw.Draw(glow)
    f1, s1 = _fit(d, l1, 'sans', 960, 112)
    f2, s2 = _fit(d, l2, 'serif', 980, 116)
    y = 372
    for txt, fnt, s in ((l1, f1, s1), (l2, f2, s2)):
        w = d.textlength(txt, font=fnt)
        d.text(((W - w) / 2, y), txt, font=fnt, fill=(255, 255, 255))
        dg.text(((W - w) / 2, y), txt, font=fnt, fill=150)
        y += int(s * 1.18)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img = Image.fromarray(np.clip(np.asarray(img, np.float32) + np.asarray(glow, np.float32)[:, :, None] * 0.45, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # firma de la marca, siempre igual, dentro del recorte 3:4
    fb = M.font('mono', 26)
    t = 'MENTE EN ÓRBITA'
    tw = d.textlength(t, font=fb)
    x0 = (W - tw - 30) / 2
    d.ellipse((x0, 1606, x0 + 16, 1622), fill=CYAN)
    d.text((x0 + 30, 1600), t, font=fb, fill=(200, 202, 208))
    img.save(out, quality=92)
    return out


def primer_cuadro(video, portada, out):
    """Pone la portada en el cuadro 0 (1/24 s): si una red ignora la miniatura, toma el primer cuadro."""
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', video, '-i', portada, '-filter_complex',
                    "[1:v]scale=1080:1920,setsar=1[p];[0:v][p]overlay=0:0:enable='eq(n,0)'[v]",
                    '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
                    '-maxrate', '10M', '-bufsize', '20M', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
                    '-movflags', '+faststart', out], check=True)
    return out


if __name__ == '__main__':
    if sys.argv[1] == '--primer-cuadro':
        primer_cuadro(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        make(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else 'MENTE EN ÓRBITA')
