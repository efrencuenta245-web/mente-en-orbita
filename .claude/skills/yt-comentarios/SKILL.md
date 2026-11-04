---
name: yt-comentarios
description: Solo para YouTube. Gestiona los comentarios del canal de YouTube - los clasifica, redacta respuestas con el tono del canal, publica solo con aprobación y convierte las mejores preguntas en ideas.
---
# Comentarios

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales y el **reset del 3-nov-2026** en `YOUTUBE.md` (manda sobre esta skill). No toques nada del flujo del reel diario (CLAUDE.md, estrategia.md, publicados.md ni sus tareas programadas).


## Presupuesto
`vidiq_video_comments` con `channelId` del canal y `order='time'` (5 créditos, 1 página por semana). Responder: `vidiq_reply_to_comment` (1 crédito) **solo con aprobación** del texto exacto. Instagram: vidIQ no lee comentarios de Instagram; Efrén puede pegarlos en el chat y se tratan igual.

## Pasos
1. Trae los comentarios nuevos y quita los que ya contestó el canal (`byChannelOwner`).
2. Clasifica: pregunta · pedido de tema · corrección/crítica · elogio · spam/odio.
3. Respuestas (máx. 2 líneas, tú, español de México, sin emojis de más):
   - Pregunta → respuesta corta y verificada + "¿te hago un video de esto?".
   - Corrección → agradece y, si tiene razón, reconoce el error y anota la corrección en el guion.
   - Pedido de tema → "Anotado 🚀" y súmalo a `youtube/ideas.md` con el usuario.
   - Spam/odio → no responder; sugerir ocultarlo.
4. Manda a Efrén la lista con las respuestas propuestas numeradas y espera "sí" (todas o por número) antes de publicar. Nunca respondas dos veces si el resultado fue dudoso.
5. Las 1–2 mejores preguntas van a `youtube/ideas.md` como "Respuestas: @usuario …" (fórmula 20 de la skill `yt-guionista`).

## Sin créditos de vidIQ (hasta el 27-nov-2026 hay 0)
No se pueden leer los comentarios: no gastes nada, dile a Efrén en una línea que puede pegarlos en el chat si quiere respuestas, y sigue con lo demás.
