---
name: auditoria
description: Hace una auditoría completa del canal de YouTube (y de Instagram) - crecimiento, Shorts vs largos, retención, fuentes de tráfico, títulos y miniaturas, SEO, constancia, marca y perfil, con un plan de 30 días priorizado. Úsala una vez al mes o cuando Efrén pida revisar todo el canal.
---
# Auditoría

## Presupuesto (≈ 15–20 créditos al mes)
`vidiq_user_channels` (gratis) → `vidiq_channel_analytics` con `report='top_videos'`, `report='shorts_vs_longform_split'` y `report='traffic_sources'` (5 c/u) → `vidiq_instagram_owner_insights` (gratis). Si el canal no está conectado, llama `vidiq_connect_youtube_channel` y pásale el enlace a Efrén.

## Revisión (calificación 1–5 por área)
1. **Crecimiento:** suscriptores, vistas y engagedViews de 28 días contra el mes anterior; avance a metas de monetización (CLAUDE.md, estrategia.md).
2. **Formatos:** Shorts vs largos (vistas, suscriptores ganados por formato).
3. **Retención:** promedio de % visto; peores y mejores 3 videos (skill `analista`).
4. **Tráfico:** búsqueda, sugeridos, Shorts feed, externos (Instagram).
5. **Empaque:** títulos y miniaturas de los últimos 10 videos con las reglas de `empaquetador`.
6. **SEO:** descripciones con capítulos, fuentes y palabras clave (skill `seo`).
7. **Constancia:** días publicados vs plan (`publicados.md`, `semana.md`).
8. **Marca y perfil:** descripción del canal, enlaces, banner, perfil de Instagram con enlace a YouTube (`guiones/perfiles.md`), sello visual y variedad de temas visuales.
9. **Monetización:** requisitos que faltan y fecha estimada a este ritmo.

## Salida
`auditorias/AAAA-MM.md` con tabla de calificaciones, 5 hallazgos con dato, y **plan de 30 días** (máx. 7 acciones con responsable: Claude o Efrén). Resumen de 10 líneas a Efrén con notificación.
