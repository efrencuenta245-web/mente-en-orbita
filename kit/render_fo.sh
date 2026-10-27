#!/bin/bash
cd /home/claude
NF=1622
i=0
a=0
while [ $a -lt $NF ]; do
  b=$((a+150)); [ $b -gt $NF ] && b=$NF
  f=partsfo/p$(printf "%02d" $i).mp4
  if [ ! -s $f.done ]; then
    python3 fo.py chunk $a $b $f && touch $f.done
  fi
  a=$b; i=$((i+1))
done
echo ALLDONE
