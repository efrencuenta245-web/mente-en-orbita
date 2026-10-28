#!/bin/bash
# Uso: ./render_gta.sh MODO FMT   -> /home/claude/gta_MODO_sin_audio.mp4
cd /home/claude
MODE=$1; FMT=$2
OUTD=/home/claude/gta_parts_$MODE
mkdir -p $OUTD
NF=$(GTA_FMT=$FMT GTA_MODE=$MODE python3 gta6.py info | head -1 | awk '{print $4}')
CH=120
seq 0 $CH $((NF-1)) | xargs -P 4 -I{} bash -c '
a={}; b=$((a+'$CH')); [ $b -gt '$NF' ] && b='$NF'
f='$OUTD'/p_$(printf %05d $a).mp4
if [ ! -e $f.done ]; then GTA_FMT='$FMT' GTA_MODE='$MODE' python3 gta6.py chunk $a $b $f && touch $f.done; fi'
for f in $(ls $OUTD/p_*.mp4 | sort); do echo "file '$f'"; done > $OUTD/list.txt
ffmpeg -y -v error -f concat -safe 0 -i $OUTD/list.txt -c copy /home/claude/gta_${MODE}_sin_audio.mp4 && echo TERMINADO $MODE
