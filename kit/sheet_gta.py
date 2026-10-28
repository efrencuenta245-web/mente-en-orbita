import sys, os, time
os.environ.setdefault('GTA_FMT','h')
import gta6 as V
from PIL import Image
ts=[float(x) for x in sys.argv[2:]]
ims=[]
t0=time.time()
for t in ts:
    ims.append(V.render(t).resize((V.W//3, V.H//3)))
print('s/frame', (time.time()-t0)/len(ts))
cols=4 if V.W>V.H else 6
rows=(len(ims)+cols-1)//cols
sh=Image.new('RGB',(cols*V.W//3,rows*V.H//3),'white')
for i,im in enumerate(ims): sh.paste(im,((i%cols)*V.W//3,(i//cols)*V.H//3))
sh.save(sys.argv[1])
