---
name: seo
description: Optimiza el posicionamiento de cada video - investigación de palabras clave en español (México), título con la palabra clave, descripción con capítulos y fuentes, etiquetas, hashtags y textos para Instagram, TikTok y Shorts; aplica cambios en YouTube solo con aprobación. Úsala al publicar o al mejorar videos ya subidos.
---
# SEO

## Presupuesto
1 llamada a `vidiq_keyword_research` (5 créditos) por video largo; en reels usa WebSearch y el historial de `seo.md`.

## Pasos
1. `vidiq_keyword_research` con `mode='research'`, `keyword` del tema en español y `country='MX'`. Elige 1 palabra clave principal (volumen alto, competencia ≤ 60) y 4–6 secundarias. Guarda la tabla en `seo.md` para reusar en reels del mismo tema.
2. **Título** (con la skill `empaquetador`): palabra clave en los primeros 40 caracteres.
3. **Descripción largo:** 2 líneas de gancho con la palabra clave → resumen → capítulos (skill `capitulos`) → pregunta para comentar → fuentes → etiquetas honestas (recreación, imágenes oficiales) → enlace a Instagram → 3–5 hashtags.
4. **Etiquetas:** 8–15, de la más exacta a la más amplia, sin repetir el título palabra por palabra.
5. **Reels/Shorts/TikTok:** título ≤ 50 caracteres con 1–2 hashtags; Instagram con pregunta-gancho, línea de valor, "Guárdalo y compártelo con alguien que…" y 3–5 hashtags (#curiosidades #ciencia #mexico #menteenorbita + 1 del tema). En los reels que vienen de un video largo: "Video completo: link en mi perfil".
6. Guarda todo en `guiones/AAAA-MM-DD_tema_youtube.md`.
7. **Aplicar en YouTube:** `vidiq_update_video` (5 créditos) solo después de que Efrén apruebe el texto exacto y si el canal está conectado (`vidiq_user_channels`).
