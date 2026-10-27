#!/bin/bash
# render por trozos con 2 procesos en paralelo (reanudable)
cd /home/claude
NF=$(python3 -c "import gps; print(gps.NF)" 2>/dev/null | tail -1)
CH=150
seq 0 $CH $((NF-1)) | xargs -P 2 -I{} bash -c '
a={}; b=$((a+'$CH')); [ $b -gt '$NF' ] && b='$NF'
f=gps_parts/p_$(printf %05d $a).mp4
if [ ! -e $f.done ]; then python3 gps.py chunk $a $b $f > /dev/null && touch $f.done && echo "ok $a"; fi'
ls gps_parts/*.mp4 | sort | sed "s/^/file '/; s/$/'/" > gps_parts/list.txt
ffmpeg -y -v error -f concat -safe 0 -i gps_parts/list.txt -c copy gps_sin_audio.mp4 && echo TERMINADO
