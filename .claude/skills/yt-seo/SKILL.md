---
name: yt-seo
description: Solo para YouTube. Optimiza el posicionamiento de los videos de YouTube - palabras clave en español (México), título, descripción con capítulos y fuentes, etiquetas y hashtags; aplica cambios en YouTube solo con aprobación.
---
# SEO

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales en `YOUTUBE.md`. No toques nada del flujo de Instagram (CLAUDE.md, estrategia.md, publicados.md, ideas.md ni sus tareas programadas).


## Presupuesto
1 llamada a `vidiq_keyword_research` (5 créditos) por video largo; en Shorts usa WebSearch y el historial de `youtube/seo.md`.

## Pasos
1. `vidiq_keyword_research` con `mode='research'`, `keyword` del tema en español y `country='MX'`. Elige 1 palabra clave principal (volumen alto, competencia ≤ 60) y 4–6 secundarias. Guarda la tabla en `youtube/seo.md` para reusar en Shorts del mismo tema.
2. **Título** (con la skill `yt-empaquetador`): palabra clave en los primeros 40 caracteres.
3. **Descripción largo:** 2 líneas de gancho con la palabra clave → resumen → capítulos (skill `yt-capitulos`) → pregunta para comentar → fuentes → etiquetas honestas (recreación, imágenes oficiales) → enlace a Instagram → 3–5 hashtags.
4. **Etiquetas:** 8–15, de la más exacta a la más amplia, sin repetir el título palabra por palabra.
5. **Shorts (y TikTok si Efrén lo sube):** título ≤ 50 caracteres con 1–2 hashtags; descripción corta con «Video completo en el canal».
6. Guarda todo en `guiones/AAAA-MM-DD_tema_youtube.md`.
7. **Aplicar en YouTube:** `vidiq_update_video` (5 créditos) solo después de que Efrén apruebe el texto exacto y si el canal está conectado (`vidiq_user_channels`).
