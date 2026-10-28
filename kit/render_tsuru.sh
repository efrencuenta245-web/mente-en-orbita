#!/bin/bash
cd /home/claude
MOD=${1:-tsuru}
OUTD=/home/claude/${MOD}_parts
mkdir -p $OUTD
NF=1540
CH=150
seq 0 $CH $((NF-1)) | xargs -P 4 -I{} bash -c '
a={}; b=$((a+'$CH')); [ $b -gt '$NF' ] && b='$NF'
f='$OUTD'/p_$(printf %05d $a).mp4
if [ ! -e $f.done ]; then python3 '$MOD'.py chunk $a $b $f > /dev/null && touch $f.done && echo "ok $a"; fi'
for f in $(ls $OUTD/p_*.mp4 | sort); do echo "file '$f'"; done > $OUTD/list.txt
ffmpeg -y -v error -f concat -safe 0 -i $OUTD/list.txt -c copy /home/claude/${MOD}_sin_audio.mp4 && echo TERMINADO
