#!/bin/bash
cd /home/claude
NF=1536
i=0
a=0
while [ $a -lt $NF ]; do
  b=$((a+150)); [ $b -gt $NF ] && b=$NF
  f=partsfo2/p$(printf "%02d" $i).mp4
  if [ ! -e $f.done ]; then
    python3 fo2.py chunk $a $b $f && touch $f.done
  fi
  a=$b; i=$((i+1))
done
echo ALLDONE
