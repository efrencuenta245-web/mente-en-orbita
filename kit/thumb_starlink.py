"""Miniatura 1280x720 del video largo de Starlink (tema orbita)."""
import os
os.environ['GTA_FMT'] = 'h'
os.environ.setdefault('MOTOR_TEMA', 'orbita')
os.environ.setdefault('VIDEO_TL', '/home/claude/tl_starlink_full.json')
import math
import starlink as V
import motor3d as E
from motor3d import Cam, Frame, font, draw_text
from PIL import Image, ImageDraw

fr = Frame()
fr.floor = 0.0
fr.cam = Cam(target=(0.0, 0.0, 0), dist=7.0, yaw=-8, pitch=16, cx=0.70, cy=0.55)
fr.meshes.append(V.earth(1.9, lon0=-100, lat_tilt=22, nu=90, nv=48))
fr.under.append(lambda d, cam: V.atmo(d, cam, (0, 0, 0), 1.92))
pts = V.shell_points(260, 2.35, (0, 0, 0), 3.0, seed=5, speed=0.1, planes=22)
V.draw_shell(fr, pts, (0, 0, 0), 1.9, V.ICE, 3.2)
fr.meshes += V.sat_at((1.2, 2.2, 1.6), s=0.55, ry=25, rx=35)
V.beam(fr, (1.2, 2.2, 1.6), (0.15, 0.7, 1.75), V.CYAN, 4.0)
img = E.render_frame(fr)
d = ImageDraw.Draw(img)
draw_text(d, (90, 330), '11 MIL', font('xb', 250), (240, 244, 255), 'lm')
draw_text(d, (100, 520), 'sobre ti', font('xb', 130), (240, 244, 255), 'lm')
d.text((100 + font('xb', 130).getlength('sobre ti') + 4, 520), '.', font=font('xb', 130), fill=V.CYAN, anchor='lm')
x0, y0 = 100, 640
txt = 'AHORA MISMO'
f = font('mono', 50)
w = f.getlength(txt) + 70
d.rounded_rectangle((x0, y0, x0 + w, y0 + 96), radius=48, fill=(8, 14, 30), outline=V.CYAN, width=4)
d.text((x0 + 35, y0 + 48), txt, font=f, fill=(255, 255, 255), anchor='lm')
draw_text(d, (104, 150), '•  SATÉLITES · RECREACIÓN', font('sb', 40), (130, 150, 190), 'lm', spacing=4)
img = img.resize((1280, 720), Image.LANCZOS)
img.save('/home/claude/miniatura_starlink.jpg', quality=94)
img.resize((320, 180), Image.LANCZOS).save('/tmp/mini320.jpg')
print('ok')
