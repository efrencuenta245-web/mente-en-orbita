import os
os.environ['GTA_FMT'] = 'h'
import math
import gta6 as V
import gta_eng as E
from gta_eng import Cam, Frame, font, draw_text
from PIL import Image, ImageDraw

fr = Frame()
fr.cam = Cam(target=(0.9, 1.0, 0), dist=6.2, yaw=-14, pitch=10, cx=0.62, cy=0.58)
fr.meshes.append(V.case_at('V', -0.2, 0, -0.6, ry=22, s=0.9))
fr.meshes.append(V.case_at('VI', 1.6, 0, 0.2, ry=-16, s=1.25))
fr.meshes += V.hourglass(0.55, 1.2, 0.5, k=0.8)
def under(d, cam):
    for j in range(3):
        E.ring3(d, cam, (1.6, 0.01, 0.2), 1.3 + j * 0.45, (30, 30, 34), 2.2 - j * 0.5, 1 - j * 0.3)
fr.under.append(under)
img = E.render_frame(fr)
d = ImageDraw.Draw(img)
# texto grande a la izquierda
draw_text(d, (90, 300), '13 AÑOS', font('xb', 230), (20, 20, 22), 'lm')
draw_text(d, (96, 470), 'de espera.', font('xb', 120), (20, 20, 22), 'lm')
d.text((96 + font('xb', 120).getlength('de espera'), 470), '.', font=font('xb', 120), fill=V.PINK, anchor='lm')
# pastilla
x0, y0 = 96, 600
txt = '¿POR QUÉ TARDÓ TANTO?'
f = font('mono', 52)
w = f.getlength(txt) + 70
d.rounded_rectangle((x0, y0, x0 + w, y0 + 96), radius=48, fill=(20, 20, 22))
d.text((x0 + 35, y0 + 48), txt, font=f, fill=(255, 255, 255), anchor='lm')
draw_text(d, (100, 120), '•  GTA 6 · 5 RAZONES', font('sb', 40), (120, 120, 124), 'lm', spacing=4)
img = img.resize((1280, 720), Image.LANCZOS)
img.save('/home/claude/miniatura_gta6.jpg', quality=94)
print('ok')
