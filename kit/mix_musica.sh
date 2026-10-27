#!/bin/bash
# Mezcla final con música: voz (loudnorm) + efectos y música, ambos bajan cuando habla la voz.
# Uso: ./mix_musica.sh VIDEO_SIN_AUDIO VOZ_EDITADA EFECTOS MUSICA SALIDA
set -e
V=$1; VOZ=$2; FX=$3; MUS=$4; OUT=$5
ffmpeg -y -v error -i "$V" -i "$VOZ" -i "$FX" -i "$MUS" -filter_complex \
"[1:a]aresample=48000,aformat=channel_layouts=stereo,apad=pad_dur=6,loudnorm=I=-16:TP=-1.5:LRA=11,asplit=3[voz][k1][k2];\
[2:a]aresample=48000,volume=0.6[fx];\
[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.32[mu];\
[fx][k1]sidechaincompress=threshold=0.04:ratio=5:attack=15:release=350:makeup=1[fxd];\
[mu][k2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500:makeup=1[mud];\
[voz][fxd][mud]amix=inputs=3:normalize=0:duration=longest,alimiter=limit=0.95[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")" -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
ffmpeg -v info -i "$OUT" -af volumedetect -vn -f null - 2>&1 | grep -E "mean_volume|max_volume"
