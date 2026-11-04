---
name: yt-productor
description: Solo para YouTube. Produce audio y video final del largo y sus Shorts - voz Isaac por capítulo, tiempos por palabra con Scribe, descarga con descargar.sh, timeline.py, render con motor2, efectos, música, mezcla, peso máximo y control de calidad.
---
# Productor

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales y el **reset del 3-nov-2026** en `YOUTUBE.md` (manda sobre esta skill). No toques nada del flujo del reel diario (CLAUDE.md, estrategia.md, publicados.md ni sus tareas programadas).

1. **Voz Isaac:** una llamada `creative_generate_speech` por capítulo (voice_id `QmPfzE500cXXHM9uQKGc`, `eleven_v4`, `generations_count=1`), todas en el mismo `flow_id` (crea el flow primero con `creative_create_flow`). Guarda flow_id, node_id y session_ids en `jobs/TEMA.json`. Espera con `creative_get_flow_run_status` (20 s entre llamadas). Si da 429 o sin cuota: plan B de CLAUDE.md §6 y avísale a Efrén.
2. **Tiempos por palabra:** `creative_transcribe_audio` (`connect_from=[node_id]`) por capítulo; toma `words_download_url`.
3. **Descarga (en cuanto tengas las URLs; caducan en ~2 h):** `bash kit/descargar.sh "<content_url>" narr_TEMA_cN.mp3 /home/claude/narr_TEMA_cN.mp3` y `bash kit/descargar.sh "<words_url>" words_TEMA_cN.json /home/claude/words_TEMA_cN.json`.
4. **Revisión de voz:** skill `yt-editor` sobre los words.json. Si hay un error grave de pronunciación, regenera solo ese capítulo.
5. **Línea de tiempo:** `python3 timeline.py TEMA` → `narr_TEMA_MODO.wav` y `tl_TEMA_MODO.json` para `full`, `reelA`, `reelB` (bloque `EDITS` de `TEMA_guion.py`).
6. **Render** (skill `yt-animador`): `python3 kit/nuevo/TEMA_largo.py render /home/claude/TEMA_largo_sin_audio.mp4` y los Shorts en vertical.
7. **Efectos y música:** efectos sintetizados por cada cambio visual (plantilla `kit/nuevo/norte_sfx.py`); `python3 musica.py DUR musica_TEMA_MODO.wav SEMILLA BPM FIN_VOZ` con semilla y BPM nuevos (90–110).
8. **Mezcla:** `./mix_musica.sh VIDEO VOZ EFECTOS MUSICA SALIDA` (nunca quites el `apad`).
9. **Peso (para alojarlo en GitHub y publicarlo con Metricool):** el largo final debe pesar ≤ 92 MB. Antes de mezclar, recodifica el video con `-c:v libx264 -preset medium -b:v <92×8/duración − 0.2>M -maxrate <1.3×> -bufsize <2×> -pix_fmt yuv420p`. Los Shorts: `-crf 21 -maxrate 10M -bufsize 20M`.
10. **Control de calidad:** audio y video con la misma duración (`ffprobe`), últimos 3 s más fuertes que −35 dB (`volumedetect`), hoja de contacto del mp4 final y de las transiciones.
