#!/bin/bash
# Aloja un video en una rama huérfana claude/pub-… (solo ese archivo) y da su URL pública para Metricool.
# Uso: bash kit/alojar.sh /ruta/video.mp4
# Imprime en la última línea: URL https://raw.githubusercontent.com/efrencuenta245-web/mente-en-orbita/<sha>/<archivo>
# La rama se borra sola a los 2 días (workflow limpieza), cuando Metricool ya copió el video.
set -u
REPO=${REPO:-/home/claude/mente-en-orbita}
F=$1
[ -f "$F" ] || { echo "ERROR: no existe $F"; exit 3; }
NAME=$(basename "$F")
REMOTE=$(git -C "$REPO" remote get-url origin)
W=$(mktemp -d)
cd "$W" && git init -q && git checkout -q --orphan pub
cp "$F" "$W/$NAME" && git add "$NAME"
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -qm "video $NAME"
B="claude/pub-$(date -u +%Y%m%d-%H%M%S)-${NAME%.*}"
B=${B:0:90}
git remote add origin "$REMOTE"
ok=0; out=""
for i in 1 2 3; do
  out=$(git push -q origin "HEAD:refs/heads/$B" 2>&1) && { ok=1; break; }
  case "$out" in *429*|*"too many"*) sleep 6 ;; *403*|*denied*|*"not in this session"*) break ;; *) sleep $((i * 4)) ;; esac
done
[ $ok = 1 ] || { echo "ERROR_ALOJAR: $out" | tail -5; exit 4; }
SHA=$(git rev-parse HEAD)
OWNER_REPO=efrencuenta245-web/mente-en-orbita
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://api.github.com/repos/$OWNER_REPO/contents/$NAME?ref=$SHA")
echo "rama $B · comprobación API: $code"
echo "URL https://raw.githubusercontent.com/$OWNER_REPO/$SHA/$NAME"
