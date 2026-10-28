#!/bin/bash
# Uso: ./render_sl.sh MODO FMT -> /home/claude/starlink_MODO_sin_audio.mp4
cd /home/claude
MODE=$1; FMT=$2
export MOTOR_TEMA=orbita GTA_FMT=$FMT VIDEO_TL=/home/claude/tl_starlink_$MODE.json
OUTD=/home/claude/sl_parts_$MODE
mkdir -p $OUTD
NF=$(python3 starlink.py info | head -1 | awk '{print $4}')
CH=120
seq 0 $CH $((NF-1)) | xargs -P 2 -I{} bash -c '
a={}; b=$((a+'$CH')); [ $b -gt '$NF' ] && b='$NF'
f='$OUTD'/p_$(printf %05d $a).mp4
if [ ! -e $f.done ]; then python3 starlink.py chunk $a $b $f && touch $f.done; fi'
for f in $(ls $OUTD/p_*.mp4 | sort); do echo "file '$f'"; done > $OUTD/list.txt
ffmpeg -y -v error -f concat -safe 0 -i $OUTD/list.txt -c copy /home/claude/starlink_${MODE}_sin_audio.mp4 && echo TERMINADO $MODE
