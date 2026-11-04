#!/bin/bash
# Prueba rápida (10-20 s) de que esta sesión puede guardar en GitHub. Úsala al arrancar cada tarea.
# Sube una rama vacía claude/ping-… y la borra. Sale con 0 si funciona; si no, imprime el error y qué hacer.
set -u
REPO=${REPO:-/home/claude/mente-en-orbita}
cd "$REPO" || { echo "ERROR: no existe $REPO (¿se clonó el repo?)"; exit 3; }
B="claude/ping-$(date -u +%Y%m%d-%H%M%S)-$RANDOM"
out=$(git push -q origin "HEAD:refs/heads/$B" 2>&1)
if [ $? = 0 ]; then
  git push -q origin --delete "$B" >/dev/null 2>&1 || true
  echo "GITHUB_OK"; exit 0
fi
echo "GITHUB_FALLA"
echo "$out" | tail -5
cat <<'EOF'
Qué hacer: en claude.ai/code/routines abre esta tarea → editar → Repositories → agrega
efrencuenta245-web/mente-en-orbita y guarda. Revisa también que la app de Claude siga instalada en GitHub
(github.com/settings/installations) con acceso a ese repositorio.
EOF
exit 4
