#!/bin/bash
# hoja de contacto del video final + niveles de audio
f=$1
mkdir -p gps_chk && rm -f gps_chk/*.png
for t in 1 4 7 10 14 19 24 28 32 34 37 42 47 53 57 61; do
  ffmpeg -v error -ss $t -i $f -frames:v 1 -vf scale=360:640 gps_chk/c_$(printf %02d $t).png
done
python3 sheet.py gps_chk/sheet_a.png $(ls gps_chk/c_*.png | head -8)
python3 sheet.py gps_chk/sheet_b.png $(ls gps_chk/c_*.png | tail -7)
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of default=nw=1 $f
ffmpeg -i $f -af volumedetect -vn -f null - 2>&1 | grep -E "mean_volume|max_volume"
