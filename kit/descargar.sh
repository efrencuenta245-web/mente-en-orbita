#!/bin/bash
# Descarga una URL bloqueada aquí (ElevenLabs, storage.googleapis.com, NASA, Wikimedia…) usando GitHub Actions.
# Uso: bash kit/descargar.sh "URL" nombre_unico.ext [destino]
#   Escribe jobs/NOMBRE.url, lo guarda con guardar.sh (rama claude/… → sync) y sync descarga a inbox/NOMBRE.
#   Copia el archivo a DESTINO (por defecto /home/claude/NOMBRE). Sale con 0 si quedó descargado.
#   Las URL firmadas de ElevenLabs caducan en ~2 h: llama a este script en cuanto tengas la URL.
set -u
REPO=${REPO:-/home/claude/mente-en-orbita}
URL=$1; N=$2; DEST=${3:-/home/claude/$N}
cd "$REPO" || exit 3
echo "$URL" > "jobs/$N.url"
TAREA=${TAREA:-descarga} bash kit/guardar.sh "jobs: descargar $N" "jobs/$N.url"; rc=$?
[ $rc = 0 ] || { echo "ERROR_DESCARGA: no pude pedir la descarga (código $rc)"; exit $rc; }
for i in $(seq 1 30); do
  git fetch -q --depth=5 origin main 2>/dev/null
  if git cat-file -e "origin/main:inbox/$N" 2>/dev/null; then
    git show "origin/main:inbox/$N" > "$DEST" && echo "DESCARGADO $DEST ($(stat -c %s "$DEST") bytes)" && exit 0
  fi
  if git cat-file -e "origin/main:inbox/$N.error" 2>/dev/null; then
    echo "ERROR_DESCARGA: $(git show "origin/main:inbox/$N.error")"; exit 6
  fi
  sleep 10
done
echo "ERROR_DESCARGA: el archivo no apareció en inbox/ en 5 min"; exit 6
