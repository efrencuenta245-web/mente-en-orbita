---
name: comentarios
description: Gestiona la comunidad de Mente en órbita - lee y clasifica comentarios de YouTube (preguntas, pedidos de tema, críticas, elogios, spam), redacta respuestas con el tono del canal, publica solo con aprobación y convierte las mejores preguntas en ideas para la serie "Respuestas". Úsala 1-2 veces por semana o cuando Efrén pregunte por comentarios.
---
# Comentarios

## Presupuesto
`vidiq_video_comments` con `channelId` del canal y `order='time'` (5 créditos, 1 página por semana). Responder: `vidiq_reply_to_comment` (1 crédito) **solo con aprobación** del texto exacto. Instagram: vidIQ no lee comentarios de Instagram; Efrén puede pegarlos en el chat y se tratan igual.

## Pasos
1. Trae los comentarios nuevos y quita los que ya contestó el canal (`byChannelOwner`).
2. Clasifica: pregunta · pedido de tema · corrección/crítica · elogio · spam/odio.
3. Respuestas (máx. 2 líneas, tú, español de México, sin emojis de más):
   - Pregunta → respuesta corta y verificada + "¿te hago un video de esto?".
   - Corrección → agradece y, si tiene razón, reconoce el error y anota la corrección en el guion.
   - Pedido de tema → "Anotado 🚀" y súmalo a `ideas.md` con el usuario.
   - Spam/odio → no responder; sugerir ocultarlo.
4. Manda a Efrén la lista con las respuestas propuestas numeradas y espera "sí" (todas o por número) antes de publicar. Nunca respondas dos veces si el resultado fue dudoso.
5. Las 1–2 mejores preguntas van a `ideas.md` como "Respuestas: @usuario …" (fórmula 20 de la skill `guionista`).
