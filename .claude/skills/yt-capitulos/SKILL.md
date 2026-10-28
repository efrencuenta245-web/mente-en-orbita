---
name: yt-capitulos
description: Solo para YouTube. Genera las marcas de tiempo y capítulos de los videos de YouTube (0:00 primero, mínimo 3 capítulos de 10 s o más, títulos cortos con palabra clave).
---
# Capítulos

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales en `YOUTUBE.md`. No toques nada del flujo de Instagram (CLAUDE.md, estrategia.md, publicados.md, ideas.md ni sus tareas programadas).


1. **Videos propios (gratis):** lee `tl_TEMA_full.json`. Cada capítulo empieza en la tarjeta o en la primera frase de cada sección (`c0`, `c1`…). Resta 1 s para que la transición no se corte. Redondea a segundos.
2. **Videos ya subidos sin línea de tiempo:** `vidiq_generate_video_chapters` (5 créditos, necesita subtítulos) y `vidiq_job_poll`.
3. Reglas de YouTube: el primero es `0:00`, al menos 3 capítulos, cada uno de 10 s o más, en orden.
4. Títulos: 2–6 palabras, con el número de la razón o el objeto ("Razón 4: el hackeo de 2022"); el primero resume el gancho ("13 años de espera").
5. Entrega el bloque listo para pegar y agrégalo a la descripción (skill `yt-seo`).
