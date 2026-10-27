import sys, subprocess
import anim
a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
cmd = ["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{anim.W}x{anim.H}","-r",str(anim.FPS),"-i","-",
       "-vf","scale=1080:1920:flags=lanczos","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",out]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for f in range(a, b):
    pr.stdin.write(anim.render(f/anim.FPS).tobytes())
pr.stdin.close(); pr.wait()
print("ok", a, b)
