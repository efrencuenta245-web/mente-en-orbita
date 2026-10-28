---
name: publicador
description: Publica y registra los videos de Mente en órbita - aloja el mp4, pide la aprobación de Efrén, programa la hora, publica el reel en Instagram con vidIQ, prepara los textos para TikTok, Shorts y YouTube, registra en publicados.md y manda los avisos. Úsala cuando un video está terminado.
---
# Publicador

Sigue CLAUDE.md §3 pasos 7–10 y §3c al pie de la letra:
1. Rama huérfana `pub-AAAAMMDD-tema` con el mp4 → `vidiq_video_upload` (URL raw de GitHub) → guarda `uploadId` en `jobs/TEMA.json`.
2. **Aprobación obligatoria:** manda video (SendUserFile), texto de Instagram, título y descripción de TikTok/Shorts y la hora propuesta, con PushNotification. Nunca publiques sin un "sí" de Efrén para ese video exacto (un pedido explícito de programar cuenta como aprobación de la hora; aun así manda el video antes).
3. Horas: diario 19:00 CDMX; extras y reels de videos largos 13:00 o 15:00. Programa con `send_later`.
4. Publica con `vidiq_instagram_publish_reel` (Reel normal, sin `isAiGenerated`), sigue `containerId` hasta `PUBLISHED`; si falla, avisa y no reintentes.
5. **YouTube:** Efrén sube el largo y los Shorts desde su celular (vidIQ no sube videos). Entrégale el mp4, la miniatura y el texto de la skill `seo`. Si el canal está conectado, ofrece aplicar título/descripción/etiquetas con `vidiq_update_video` cuando él confirme.
6. Registra en `publicados.md` (fecha, tipo, tema, gancho, duración, **tema visual**, enlace), commit y push, y manda el aviso "Ya se publicó tu reel".
