---
name: yt-publicador
description: Solo para YouTube. Deja listo cada video de YouTube para publicar - archivos, miniatura y textos para Efrén, aprobación, metadatos con vidIQ si él lo aprueba, registro en youtube/publicados.md y avisos. No publica nada en Instagram.
---
# Publicador

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales en `YOUTUBE.md`. No toques nada del flujo de Instagram (CLAUDE.md, estrategia.md, publicados.md, ideas.md ni sus tareas programadas).


1. **Archivos:** mp4 horizontal del largo, los Shorts verticales, la miniatura (`yt-empaquetador`) y el texto completo (`yt-seo` + `yt-capitulos`) en `youtube/AAAA-MM-DD_tema.md`.
2. **Aprobación:** manda todo a Efrén con PushNotification («Tu video de YouTube está listo: <tema>») y SendUserFile. Propón día y hora (largo jueves; Shorts viernes y sábado).
3. **Subida:** Efrén sube el video y los Shorts desde su celular (vidIQ no sube videos a YouTube). Para que los descargue fácil, aloja los mp4 en ramas `pub-yt-*`.
4. **Metadatos:** cuando Efrén confirme que ya subió el video y apruebe el texto exacto, aplica título, descripción, etiquetas u hora programada (`privacyStatus='private'` + `publishAt`) con `vidiq_update_video` (5 créditos, canal `UCHk6ZxeFa204iyNser0ALJg`).
5. **Registro:** `youtube/publicados.md` (fecha, formato largo/Short, tema, gancho, duración, tema visual, enlace), commit y push, y aviso «Ya está en YouTube: <tema>».
6. **Nunca** publiques en Instagram desde estas skills ni toques `publicados.md`: eso es del flujo de Instagram.
