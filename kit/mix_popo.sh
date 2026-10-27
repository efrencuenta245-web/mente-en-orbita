#!/bin/bash
# Mezcla final: voz editada (loudnorm) + efectos con ducking por la voz
set -e
V=/home/claude/popo_sync_sin_audio.mp4
VOZ=/home/claude/narr_popo_editada.wav
FX=/home/claude/efectos_popo_sync.wav
OUT=/mnt/user-data/outputs/popocatepetl_con_narracion.mp4
ffmpeg -y -v error -i "$V" -i "$VOZ" -i "$FX" -filter_complex \
"[1:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11,asplit=2[voz][key];\
[2:a]aresample=48000,volume=0.6[fx];\
[fx][key]sidechaincompress=threshold=0.04:ratio=5:attack=15:release=350:makeup=1[fxd];\
[voz][fxd]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.95[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")" -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
ffmpeg -v info -i "$OUT" -af volumedetect -vn -f null - 2>&1 | grep -E "mean_volume|max_volume"
