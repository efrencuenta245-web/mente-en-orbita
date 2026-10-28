---
name: shorts
description: Analiza un video largo (propio o de YouTube) para encontrar los fragmentos que funcionan solos como YouTube Shorts y Reels de 61-68 s, arma la lista de edición y los renderiza en vertical. Úsala después de cada video largo o cuando Efrén pida sacar clips.
---
# Shorts

## Video propio (gratis)
1. Lee `tl_TEMA_full.json` y el guion. Busca tramos que:
   - Abran con una frase que funcione sola como gancho (fórmulas 2, 3, 13, 16 de la skill `guionista`); la frase "Razón N." no sirve como inicio.
   - Tengan un clímax (número, revelación, contador) antes del segundo 50.
   - Sumen 50–57 s de voz + 11 s del cierre `REEL_OUT` = 61–68 s.
2. Califica cada candidato: gancho (0–40), clímax (0–30), se entiende sin el resto (0–20), cercanía (0–10). Elige los 2 mejores (y un 3.º de reserva).
3. Escribe el bloque `EDITS` en `kit/TEMA_guion.py`:
   `'reelA': [('gap', 0.15), ('c4', 1, 8), ('gap', 0.45), ('c5', 2, 3), ('gap', 0.6), ('out', 0, 1), ('gap', 1.6)]`
   Puedes saltar frases (dos tramos del mismo capítulo) si la idea sigue clara.
4. `python3 timeline.py TEMA reelA reelB` → revisa duración; renderiza con `GTA_FMT=v` (skill `productor`).
5. Para cada reel: texto de Instagram, título y descripción corta de TikTok/Shorts (skill `seo`) y hora (13:00 o 15:00, 3 h lejos del diario).

## Video ajeno o ya subido a YouTube
`vidiq_video_transcript` (5 créditos) y el mismo análisis; para cortar se necesita el archivo original (no descargamos videos de otros). `vidiq_generate_clips` cuesta 9 créditos por minuto: úsalo solo si Efrén lo pide.
