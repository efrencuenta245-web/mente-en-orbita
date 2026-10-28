# YouTube — Mente en órbita (separado de Instagram)

Canal: **@menteenorbita-t8b** · channelId `UCHk6ZxeFa204iyNser0ALJg` (conectado a vidIQ).
Este archivo y las skills `yt-*` son **solo para YouTube**. El flujo de Instagram (CLAUDE.md, estrategia.md, publicados.md, ideas.md y sus tareas de las 8:57 y 4:35 pm) **no se toca** desde aquí.

## Qué se hace
- **1 video largo por semana** (horizontal 1920×1080, 3–8 min, capítulos), producido el miércoles; Efrén lo sube el jueves.
- **2 Shorts por semana** sacados del largo (vertical, 50–70 s), viernes y sábado.
- Efrén sube todo desde su celular (vidIQ no sube videos a YouTube). Con su aprobación, vidIQ puede cambiar título, descripción, etiquetas u hora programada.

## Videos extra (pedidos por Efrén en el chat)
Igual que en Instagram: Efrén puede pedir en el chat un video largo o un Short **extra** para probar una idea suya o responder comentarios.
- **No alteran lo programado:** el video largo semanal y sus 2 Shorts se hacen igual, y `youtube/semana.md` no se reordena por un extra. Solo si el extra cubre el tema planeado de la semana, ese tema sale del plan y se usa la idea de reserva.
- **Mismo pipeline y misma calidad** (skills `yt-guionista` → `yt-publicador`), con aprobación de Efrén antes de cualquier cambio en YouTube.
- **Día de subida:** el que diga Efrén; si no dice, sugiere uno que no caiga el mismo día que el largo programado (jueves), para que no compitan.
- Se registra en `youtube/publicados.md` con tipo **extra**. Los videos que Efrén sube por su cuenta no se anotan, pero el analista y la auditoría los analizan igual.
- Nada de esto toca Instagram: un video extra de YouTube no se publica como reel salvo que Efrén lo pida en el chat (y entonces se sigue CLAUDE.md §3b).

## Archivos
| Archivo | Para qué |
|---|---|
| `youtube/semana.md` | Plan semanal (skill `yt-semana`) |
| `youtube/cazador.md` | Lo que funciona en el nicho (skill `yt-cazador`) |
| `youtube/ideas.md` | Ideas y preguntas del público |
| `youtube/aprendizajes.md` | Lecciones del analista |
| `youtube/publicados.md` | Registro de lo publicado en YouTube |
| `youtube/guiones/` | Guiones, miniaturas, textos |
| `youtube/auditorias/` | Auditoría mensual |

## Skills (en orden)
`yt-cazador` → `yt-semana` → `yt-guionista` → `yt-animador` → `yt-productor` → `yt-editor` → `yt-empaquetador` → `yt-seo` → `yt-capitulos` → `yt-shorts` → `yt-publicador`; después `yt-analista`, `yt-comentarios` y, cada mes, `yt-auditoria`.

## Animación
Motor `kit/motor3d.py` + `kit/escenas.py` con 10 temas visuales (`MOTOR_TEMA`). **`orbita` es la esencia del canal** y va al menos en 1 de cada 3 videos; en todos los temas se conservan escáner, HUD, contador, escala real, cierre `s_marca` y loop. Ver `.claude/skills/yt-animador/temas.md`.

## Créditos de vidIQ (compartidos con Instagram)
Instagram tiene prioridad: **YouTube nunca baja el saldo de 40 créditos** (son del estratega de Instagram). Revisa `vidiq_balance` antes de cada llamada que cueste.
| Uso de YouTube | Frecuencia | Créditos/mes |
|---|---|---|
| Cazador (outliers) | 1/semana | ~20 |
| SEO (keyword research) | 1/semana | ~20 |
| Analista (retención del largo) | 1/semana | ~20 |
| Comentarios | 1/semana | ~20 |
| Auditoría | 1/mes | ~10 |

## Monetización (YouTube)
Nivel 1: 500 suscriptores, 3 videos en 90 días y 3 M de vistas de Shorts en 90 días (o 3,000 h de reproducción de largos). Nivel 2 (anuncios): 1,000 suscriptores y 4,000 h de largos en 12 meses o 10 M de vistas de Shorts en 90 días (20 M desde el 1-feb-2027).
