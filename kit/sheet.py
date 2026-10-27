import sys
from PIL import Image
files = sys.argv[2:]
out = sys.argv[1]
ims = [Image.open(f).resize((360, 640)) for f in files]
n = len(ims); cols = min(n, 4); rows = (n + cols - 1) // cols
sh = Image.new("RGB", (cols * 360 + (cols - 1) * 6, rows * 640 + (rows - 1) * 6), (255, 255, 255))
for i, im in enumerate(ims):
    sh.paste(im, ((i % cols) * 366, (i // cols) * 646))
sh.save(out)
