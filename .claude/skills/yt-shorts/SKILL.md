---
name: yt-shorts
description: Solo para YouTube. Analiza un video largo de YouTube para encontrar los fragmentos que funcionan solos como YouTube Shorts, arma la lista de edición y los renderiza en vertical (Efrén los sube a Shorts y, si quiere, a TikTok).
---
# Shorts

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales en `YOUTUBE.md`. No toques nada del flujo de Instagram (CLAUDE.md, estrategia.md, publicados.md, ideas.md ni sus tareas programadas).


## Video propio (gratis)
1. Lee `tl_TEMA_full.json` y el guion. Busca tramos que:
   - Abran con una frase que funcione sola como gancho (fórmulas 2, 3, 13, 16 de la skill `yt-guionista`); la frase "Razón N." no sirve como inicio.
   - Tengan un clímax (número, revelación, contador) antes del segundo 50.
   - Sumen 50–57 s de voz + 11 s del cierre `REEL_OUT` = 61–68 s.
2. Califica cada candidato: gancho (0–40), clímax (0–30), se entiende sin el resto (0–20), cercanía (0–10). Elige los 2 mejores (y un 3.º de reserva).
3. Escribe el bloque `EDITS` en `kit/TEMA_guion.py`:
   `'reelA': [('gap', 0.15), ('c4', 1, 8), ('gap', 0.45), ('c5', 2, 3), ('gap', 0.6), ('out', 0, 1), ('gap', 1.6)]`
   Puedes saltar frases (dos tramos del mismo capítulo) si la idea sigue clara.
4. `python3 timeline.py TEMA reelA reelB` → revisa duración; renderiza con `GTA_FMT=v` (skill `yt-productor`).
5. Para cada Short: título y descripción de YouTube Shorts (y de TikTok si Efrén quiere subirlo ahí) con «Video completo en el canal». Se suben a YouTube; **no se publican en Instagram** desde aquí.

## Video ajeno o ya subido a YouTube
`vidiq_video_transcript` (5 créditos) y el mismo análisis; para cortar se necesita el archivo original (no descargamos videos de otros). `vidiq_generate_clips` cuesta 9 créditos por minuto: úsalo solo si Efrén lo pide.
