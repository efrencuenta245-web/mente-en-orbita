---
name: yt-auditoria
description: Solo para YouTube. Auditoría mensual completa del canal de YouTube - crecimiento, Shorts vs largos, retención, tráfico, títulos y miniaturas, SEO, constancia, marca y monetización, con plan de 30 días.
---
# Auditoría

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales y el **reset del 3-nov-2026** en `YOUTUBE.md` (manda sobre esta skill). No toques nada del flujo del reel diario (CLAUDE.md, estrategia.md, publicados.md ni sus tareas programadas).


## Presupuesto (≈ 15–20 créditos al mes)
`vidiq_user_channels` (gratis) → `vidiq_channel_analytics` con `report='top_videos'`, `report='shorts_vs_longform_split'` y `report='traffic_sources'` (5 c/u). Si el canal no está conectado, llama `vidiq_connect_youtube_channel` y pásale el enlace a Efrén.

## Revisión (calificación 1–5 por área)
1. **Crecimiento:** suscriptores, vistas y engagedViews de 28 días contra el mes anterior; avance a la monetización de YouTube (`YOUTUBE.md`).
2. **Formatos:** Shorts vs largos (vistas, suscriptores ganados por formato).
3. **Retención:** promedio de % visto; peores y mejores 3 videos (skill `yt-analista`).
4. **Tráfico:** búsqueda, sugeridos, Shorts feed, externos (Instagram).
5. **Empaque:** títulos y miniaturas de los últimos 10 videos con las reglas de `yt-empaquetador`.
6. **SEO:** descripciones con capítulos, fuentes y palabras clave (skill `yt-seo`).
7. **Constancia:** días publicados vs plan (`youtube/publicados.md`, `youtube/semana.md`).
8. **Marca y perfil:** descripción del canal, enlaces, banner, sello visual y variedad de temas visuales (`guiones/perfiles.md`).
9. **Monetización:** requisitos que faltan y fecha estimada a este ritmo.

## Salida
`youtube/auditorias/AAAA-MM.md` con tabla de calificaciones, 5 hallazgos con dato, y **plan de 30 días** (máx. 7 acciones con responsable: Claude o Efrén). Resumen de 10 líneas a Efrén con notificación.

## Sin créditos de vidIQ (hasta el 27-nov-2026 hay 0)
Usa Metricool (YouTube: YTVP02, YTVP17, YTVP05, YTVP06, YTVP08, YTVP12, YTVP09, YTVP11 y los suscriptores con getAnalyticsAvailableMetrics) y `youtube/stats.csv`. Las áreas sin datos (tráfico) se marcan «sin dato» en vez de inventarlas.
