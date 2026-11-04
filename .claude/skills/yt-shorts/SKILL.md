---
name: yt-shorts
description: Solo para YouTube. Analiza un video largo de YouTube para encontrar los 2 fragmentos que funcionan solos como YouTube Shorts, arma la lista de edición y los renderiza en vertical con el estilo nuevo.
---
# Shorts

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales y el **reset del 3-nov-2026** en `YOUTUBE.md` (manda sobre esta skill). No toques nada del flujo del reel diario (CLAUDE.md, estrategia.md, publicados.md ni sus tareas programadas).

## Video propio
1. Lee `tl_TEMA_full.json` y el guion. Busca tramos que:
   - Abran con una frase que funcione sola como gancho (fórmula de ESTILO.md §7: «tú/tu» + contradicción); «Razón N.» no sirve como inicio.
   - Tengan un clímax (número, revelación, contador) antes del segundo 45.
   - Sumen 50–65 s de voz y cierren con una frase que regrese al gancho (loop) o con «la historia completa está en el canal».
2. Califica cada candidato: gancho (0–40), clímax (0–30), se entiende sin el resto (0–20), cercanía (0–10). Elige los 2 mejores (y un 3.º de reserva).
3. Escribe el bloque `EDITS` en `kit/TEMA_guion.py`, por ejemplo:
   `'reelA': [('gap', 0.15), ('c4', 1, 8), ('gap', 0.45), ('c5', 2, 3), ('gap', 0.6)]`
4. `python3 timeline.py TEMA reelA reelB` → revisa la duración y renderiza en vertical (skill `yt-animador`, `kit/nuevo/TEMA_short.py`).
5. Portada de cada Short con `kit/nuevo/portada.py` (mismo diseño que los reels, ESTILO.md §10) y `--primer-cuadro`.
6. Para cada Short: título ≤ 60 caracteres con #Shorts y descripción corta con «Video completo en el canal». Se publican **solo en YouTube Shorts** con Metricool (skill `yt-publicador`), salvo que Efrén pida otra red.

## Video ajeno o ya subido
`vidiq_video_transcript` (5 créditos, si alcanza) y el mismo análisis; para cortar se necesita el archivo original (no descargamos videos de otros).
