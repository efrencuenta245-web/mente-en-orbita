# YouTube — Mente en órbita (video largo y sus Shorts)

Canal: **@menteenorbita-t8b** · channelId `UCHk6ZxeFa204iyNser0ALJg`.
Este archivo y las skills `yt-*` son para el **video largo de YouTube y los Shorts que salen de él**. El reel diario (que ya se publica en IG, FB, TikTok y YouTube Shorts) es de CLAUDE.md: desde aquí **no se tocan** `estrategia.md`, `publicados.md` ni sus tareas.

## Reset del 3-nov-2026 (esto manda sobre cualquier skill `yt-*` que diga otra cosa)
- **Estilo:** el mismo del reel, ESTILO.md: fondo negro, motor `kit/nuevo/motor2.py`, objetos semirrealistas, line-art que brilla, transiciones y efectos de ESTILO.md §4, fotos reales con licencia libre. Los temas visuales viejos (`orbita`, `estudio`…), `motor3d.py`/`escenas.py` como estilo, `render_gta.sh` y `thumb_gta.py` quedan **solo como archivo**.
  - **Largo horizontal 1920×1080:** `MOTOR_FORMATO=h` antes de importar motor2. Acomodo de ejemplo: `kit/nuevo/demo_horizontal.py` (objeto 3D a un lado con `cx=0.68` o `0.32` en la cámara; título y kicker del otro lado con `cx=`; subtítulos `y=900, cx=960, maxw=1300`, máximo 8 palabras por bloque).
  - **Shorts verticales 1080×1920:** igual que el reel, `kit/nuevo/norte.py` es la plantilla (subtítulos en bloques de máximo 6 palabras).
  - Reutiliza funciones de `kit/nuevo/demo_estilo.py` y `kit/nuevo/norte.py` (celular, Tierra, imán, gráficas, foto que cae…), pero cada video lleva escenas y arco nuevos (regla de YouTube).
- **Tiempos:** `kit/timeline.py` sigue sirviendo para la voz por capítulo: da `narr_TEMA_MODO.wav` y `tl_TEMA_MODO.json` (`phrases[]` con `a`, `b`, `text` y `words`). Las escenas leen esos tiempos.
- **Voz: Isaac** (ElevenLabs `QmPfzE500cXXHM9uQKGc`, `eleven_v4`), la misma del reel, una llamada por capítulo.
- **Publicación con Metricool** (brandId `7735731`), solo a YouTube y solo con el «sí» de Efrén (skill `yt-publicador`). Ya no hace falta que Efrén suba nada a mano, salvo que el archivo no se pueda alojar (más de 95 MB).
- **vidIQ:** 0 créditos hasta el 27-nov-2026; luego 150 al mes. Antes de cada llamada que cueste, `vidiq_balance`: si no alcanza, usa el plan sin vidIQ que dice cada skill (Metricool + WebSearch). El reel diario ya no usa vidIQ, así que YouTube puede usar todos los créditos (máximo ~100 al mes).

## Qué se hace
- **1 video largo cada 15 días** (horizontal, 3–6 min, capítulos). Lo produce la tarea del miércoles; se salta la semana si ya hubo uno «quincenal» en los últimos 13 días. Se programa con Metricool para el **jueves a las 17:00** (lejos del reel de las 19:00).
- **2 Shorts** sacados de cada largo (vertical, 50–70 s), programados el **viernes y el sábado a las 13:00**, solo en YouTube Shorts (Efrén puede pedir que también salgan en otras redes).
- **Peso:** GitHub no acepta archivos de más de 100 MB, así que el largo se codifica para pesar **≤ 92 MB** (bitrate de video = 92×8/duración − 0.2 Mbps; con grano 0.025 en horizontal comprime mejor).
- **ElevenLabs:** Efrén tiene más de 100 000 créditos (3-nov-2026): alcanzan para el reel diario (~900 cada uno) y el largo (~3 000 por uno de 3–4 min), siempre con la voz de Isaac. Solo si ElevenLabs responde 429 o sin cuota se usa el plan B de CLAUDE.md §6 y se le avisa a Efrén.

## Videos extra (pedidos por Efrén en el chat)
- No alteran lo programado: el largo quincenal y sus 2 Shorts se hacen igual, y `youtube/semana.md` no se reordena por un extra. Solo si el extra cubre el tema planeado de la semana, ese tema sale del plan y se usa la idea de reserva.
- Mismo pipeline, misma calidad y misma aprobación. Si Efrén no dice el día, sugiere uno que no caiga en jueves.
- Se registra en `youtube/publicados.md` con tipo **extra**.

## Archivos
| Archivo | Para qué |
|---|---|
| `youtube/semana.md` | Plan semanal (skill `yt-semana`) |
| `youtube/cazador.md` | Lo que funciona en el nicho (skill `yt-cazador`) |
| `youtube/ideas.md` | Ideas y preguntas del público |
| `youtube/aprendizajes.md` | Lecciones del analista |
| `youtube/publicados.md` | Registro de lo publicado en YouTube (tipos: quincenal, extra) |
| `youtube/stats.csv` | Suscriptores y vistas (fecha,suscriptores,vistas_28d) |
| `youtube/guiones/` | Guiones, miniaturas, textos |
| `youtube/auditorias/` | Auditoría mensual |
| `youtube/tareas.md` | Las 4 tareas programadas de YouTube |

## Skills (en orden)
`yt-cazador` → `yt-semana` → `yt-guionista` → `yt-animador` → `yt-productor` (con `yt-editor`) → `yt-shorts` → `yt-empaquetador` → `yt-seo` → `yt-capitulos` → `yt-publicador`; después `yt-analista`, `yt-comentarios` y, cada mes, `yt-auditoria`.
Para guardar en GitHub usa siempre `TAREA=youtube bash kit/guardar.sh "mensaje" archivos…` (CLAUDE.md §1): nunca `git push` a mano.

## Créditos de vidIQ (desde el 27-nov-2026)
| Uso | Frecuencia | Créditos/mes |
|---|---|---|
| Cazador (outliers) | 1/semana | ~20 |
| SEO (keyword research) | 1 por largo | ~10 |
| Analista (retención del largo) | 1/semana | ~20 |
| Comentarios (leer) | 1/semana | ~20 |
| Auditoría | 1/mes | ~15 |

## Monetización (YouTube)
Nivel 1: 500 suscriptores, 3 videos en 90 días y 3 M de vistas de Shorts en 90 días (o 3 000 h de reproducción de largos). Nivel 2 (anuncios): 1 000 suscriptores y 4 000 h de largos en 12 meses o 10 M de vistas de Shorts en 90 días (20 M desde el 1-feb-2027).
