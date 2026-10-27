import sys
from PIL import Image
out, d = sys.argv[1], sys.argv[2]
ts = sys.argv[3:]
ims = [Image.open(f'{d}/t_{t}.png').resize((270, 480)) for t in ts]
cols = 6
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (270 * cols, 480 * rows))
for i, im in enumerate(ims):
    sh.paste(im, ((i % cols) * 270, (i // cols) * 480))
sh.save(out)
