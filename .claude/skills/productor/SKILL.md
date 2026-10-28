---
name: productor
description: Produce el audio y el video final de Mente en órbita - voz Carmelo en ElevenLabs por capítulo, tiempos por palabra con Scribe, descarga con el workflow fetch, línea de tiempo (timeline.py), render 3D en paralelo, efectos, música y mezcla con revisión de audio. Úsala cuando el guion y las escenas ya existen y hay que convertirlos en un mp4.
---
# Productor

Sigue CLAUDE.md §3 pasos 4–7. Resumen del flujo automático:

1. **Voz:** una llamada `creative_generate_speech` por capítulo (voice_id `5egO01tkUjEzu7xSSE8M`, `eleven_v4`, `generations_count=1`), todas en el mismo `flow_id`. Guarda flow_id, node_id y session_ids en `jobs/TEMA.json`. Poll cada ~20 s.
2. **Tiempos por palabra (gratis):** `creative_transcribe_audio` (`eleven_scribe_v1`, `connect_from=[node_id]`) por capítulo. Del resultado toma `words_download_url`.
3. **Descarga:** escribe en `main` los archivos `jobs/narr_TEMA_cN.mp3.url` (content_url de la voz) y `jobs/words_TEMA_cN.json.url` (words_download_url), commit y push; espera `inbox/` (1–2 min) y copia a `/home/claude/`. Las URLs caducan en 2 h: hazlo enseguida.
4. **Revisión de voz:** corre la skill `editor` sobre los words.json (silencios, palabras cambiadas, muletillas). Si hay un error de pronunciación grave, regenera solo ese capítulo.
5. **Línea de tiempo:** `python3 timeline.py TEMA` → `narr_TEMA_MODO.wav` y `tl_TEMA_MODO.json` por cada modo de `EDITS` (full, reelA, reelB…). Comprueba que los reels duren 61–68 s.
6. **Render:** `./render_gta.sh` sirve de plantilla (4 procesos, bloques de 120 cuadros). Para cada modo: `MOTOR_TEMA=… GTA_FMT=h|v VIDEO_TL=tl_TEMA_MODO.json`.
7. **Efectos y música:** efectos por corte de escena y eventos (plantilla `kit/sfx_gta.py`); `python3 musica.py DUR musica_TEMA_MODO.wav SEMILLA BPM FIN_VOZ` con semilla y BPM nuevos (90–110).
8. **Mezcla:** `./mix_musica.sh VIDEO VOZ EFECTOS MUSICA SALIDA` (nunca quites el `apad`).
9. **Control de calidad:** audio y video con la misma duración (`ffprobe`), últimos 3 s más fuertes que −35 dB, hoja de contacto del mp4 final y de las transiciones.
