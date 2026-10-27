#!/bin/bash
cd /home/claude
NF=$(python3 -c "import gps_sync; print(gps_sync.NF)" 2>/dev/null | tail -1)
CH=150
seq 0 $CH $((NF-1)) | xargs -P 2 -I{} bash -c '
a={}; b=$((a+'$CH')); [ $b -gt '$NF' ] && b='$NF'
f=/home/claude/gps_parts2/p_$(printf %05d $a).mp4
if [ ! -e $f.done ]; then python3 gps_sync.py chunk $a $b $f > /dev/null && touch $f.done && echo "ok $a"; fi'
for f in $(ls /home/claude/gps_parts2/p_*.mp4 | sort); do echo "file '$f'"; done > /home/claude/gps_list2.txt
ffmpeg -y -v error -f concat -safe 0 -i /home/claude/gps_list2.txt -c copy /home/claude/gps_sync_sin_audio.mp4 && echo TERMINADO
