#!/bin/bash
cd /home/claude
MOD=${1:-varg}
OUTD=/home/claude/${MOD}_parts
mkdir -p $OUTD
NF=$(python3 -c "import $MOD; print($MOD.NF)" 2>/dev/null | tail -1)
CH=150
seq 0 $CH $((NF-1)) | xargs -P 2 -I{} bash -c '
a={}; b=$((a+'$CH')); [ $b -gt '$NF' ] && b='$NF'
f='$OUTD'/p_$(printf %05d $a).mp4
if [ ! -e $f.done ]; then python3 '$MOD'.py chunk $a $b $f > /dev/null && touch $f.done && echo "ok $a"; fi'
for f in $(ls $OUTD/p_*.mp4 | sort); do echo "file '$f'"; done > $OUTD/list.txt
ffmpeg -y -v error -f concat -safe 0 -i $OUTD/list.txt -c copy /home/claude/${MOD}_sin_audio.mp4 && echo TERMINADO
