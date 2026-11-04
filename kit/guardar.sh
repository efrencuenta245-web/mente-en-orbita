#!/bin/bash
# Guarda archivos del repo en GitHub SIN subir a main directamente.
# Las tareas programadas solo pueden subir a ramas claude/…; este script sube una rama claude/guardar-…
# y espera a que el workflow «sync» la pase a main. Sale con 0 solo cuando los archivos ya están en main.
# Uso: TAREA=estratega bash kit/guardar.sh "mensaje del commit" ruta1 [ruta2 …]
#      (rutas relativas a la raíz del repo; se toman de /home/claude/mente-en-orbita)
# Al terminar bien, la copia local queda apuntando a origin/main (sin tocar tus archivos), así no hay choques.
# Códigos: 0 guardado · 3 no pude leer GitHub · 4 GitHub rechazó la subida (permiso) · 5 sync no lo pasó a main
set -u
REPO=${REPO:-/home/claude/mente-en-orbita}
TAREA=${TAREA:-manual}
MSG=$1; shift
cd "$REPO" || { echo "ERROR: no existe $REPO"; exit 3; }
for f in "$@"; do [ -e "$f" ] || { echo "ERROR: no existe $f"; exit 3; }; done

fetch_main() { for i in 1 2 3; do git fetch -q --depth=20 origin main 2>/tmp/gerr && return 0; sleep $((i * 5)); done; cat /tmp/gerr; return 1; }
fetch_main || { echo "ERROR_LEER: no pude leer main de GitHub"; exit 3; }

W=$(mktemp -d)/w
git worktree add -q --detach "$W" origin/main || { echo "ERROR: worktree"; exit 3; }
for f in "$@"; do mkdir -p "$W/$(dirname "$f")"; cp -a "$f" "$W/$f"; (cd "$W" && git add -- "$f"); done
cd "$W"
if git diff --cached --quiet; then echo "Sin cambios: ya estaba igual en main"; cd "$REPO"; git worktree remove --force "$W"; git reset -q origin/main 2>/dev/null; exit 0; fi
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -qm "$MSG"
B="claude/guardar-$(date -u +%Y%m%d-%H%M%S)-$TAREA"
ok=0; out=""
for i in 1 2 3; do
  out=$(git push -q origin "HEAD:refs/heads/$B" 2>&1) && { ok=1; break; }
  case "$out" in
    *429*|*"too many"*) sleep 6 ;;
    *403*|*denied*|*"not in this session"*|*"Permission"*) break ;;
    *413*) git fetch -q --depth=20 origin main; sleep 3 ;;
    *) sleep $((i * 4)) ;;
  esac
done
cd "$REPO"
if [ $ok != 1 ]; then
  git worktree remove --force "$W"
  echo "ERROR_PUSH: GitHub rechazó la subida de $B"
  echo "$out" | tail -5
  exit 4
fi
# Esperar a que sync lo pase a main (normalmente 30-90 s; máximo ~5 min)
for i in $(seq 1 30); do
  sleep 10
  fetch_main >/dev/null 2>&1 || continue
  same=1
  for f in "$@"; do (cd "$W" && git diff --quiet origin/main HEAD -- "$f") || same=0; done
  if [ $same = 1 ]; then git worktree remove --force "$W"; git reset -q origin/main 2>/dev/null; echo "GUARDADO en main (rama $B)"; exit 0; fi
done
git worktree remove --force "$W"
echo "ERROR_SYNC: la rama $B sí se subió, pero el workflow sync no la pasó a main en 5 min. Los cambios siguen a salvo en esa rama."
exit 5
