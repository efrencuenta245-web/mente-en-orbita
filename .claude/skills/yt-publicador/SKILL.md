---
name: yt-publicador
description: Solo para YouTube. Deja listo y programa cada video de YouTube - aloja archivos, manda video, miniatura y textos a Efrén, pide su aprobación, programa con Metricool solo en YouTube, revisa que se publique y lo registra en youtube/publicados.md.
---
# Publicador

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales y el **reset del 3-nov-2026** en `YOUTUBE.md` (manda sobre esta skill). No toques nada del flujo del reel diario (CLAUDE.md, estrategia.md, publicados.md ni sus tareas programadas).

1. **Archivos:** mp4 horizontal del largo (≤ 92 MB), los 2 Shorts verticales, la miniatura 1280×720 (`yt-empaquetador`) y el texto completo (`yt-seo` + `yt-capitulos`) en `youtube/guiones/AAAA-MM-DD_tema.md`.
2. **Alojar:** `bash kit/alojar.sh /home/claude/<archivo>` para cada mp4 y para la miniatura (jpg); la última línea trae la URL pública. Si el largo pesa más de 95 MB y no se pudo bajar, Efrén lo sube a mano (mándale el archivo y el texto).
3. **Aprobación (obligatoria):** PushNotification «Tu video de YouTube está listo: <tema>. ¿Lo programo el jueves a las 5 pm?», SendUserFile con el largo, los Shorts y la miniatura, y SendUserMessage con título, descripción, etiquetas y horarios propuestos (largo jueves 17:00; Shorts viernes y sábado 13:00, hora de CDMX). **Nunca programes sin un «sí» explícito de Efrén para esos videos.** Si pide cambios, hazlos y vuelve a preguntar.
4. **Programar con Metricool** (una llamada `createScheduledPost` por video): blogId `7735731`, publicationDate con timezone `America/Mexico_City` (si la fecha ya pasó, 15 min después del «sí»), autoPublish true, draft false, media [URL], text = descripción aprobada, providers `[{"network":"youtube"}]`, youtubeData `{"title":…,"type":"video" (largo) o "short","privacy":"public","madeForKids":false,"category":"SCIENCE_TECHNOLOGY","tags":[…]}`. En el largo agrega `videoThumbnailUrl` con la miniatura; si Metricool responde VIDEO_THUMBNAIL_NOT_APPLICABLE, repite sin ese campo y dile a Efrén que la ponga desde YouTube Studio. Confirma con `getScheduledPosts` y manda los plannerUrl.
5. **Revisión:** programa `send_later` 20 min después de cada publicación: si ya no está pendiente y Metricool (YTVP02, YTVP17, YTVP05) lo muestra, aviso «Ya está en YouTube: <tema>» con el enlace; si sigue pendiente o con error, aviso «No se pudo publicar en YouTube: <motivo>» con el plannerUrl y el archivo. Una lista vacía de pendientes no basta como prueba.
6. **Registro:** `youtube/publicados.md` (fecha, tipo quincenal o extra, formato largo/Short, tema, gancho, duración, escena principal, enlace) y guarda con `TAREA=youtube bash kit/guardar.sh "youtube: <tema>" youtube/publicados.md`.
7. **Nunca** toques `publicados.md` ni `estrategia.md` del reel diario.
