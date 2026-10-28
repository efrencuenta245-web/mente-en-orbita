---
name: editor
description: Revisa una transcripción con tiempos (voz de ElevenLabs Scribe o una grabación de Efrén) y marca con minuto y segundo exactos los silencios largos, muletillas, palabras repetidas, tomas repetidas y diferencias contra el guion, con la acción de corte recomendada. Úsala después de generar la voz o cuando Efrén mande audio o video grabado.
---
# Editor

## Entrada
- Voz generada: `words_TEMA_cN.json` (Scribe) + el texto de voz del guion.
- Grabación de Efrén: súbela a ElevenLabs (`creative_create_asset_upload` → PUT → `creative_finalize_asset_upload`) y transcríbela con `creative_transcribe_audio` (`eleven_scribe_v1`, gratis) para tener palabras con tiempo.

## Qué marcar (formato `mm:ss.s`)
| Tipo | Regla |
|---|---|
| Silencio largo | Hueco > 0.6 s entre palabras dentro de una frase, o > 0.9 s entre frases |
| Muletilla | eh, este, o sea, bueno, ajá, mmm, "¿no?", "pues" al inicio |
| Repetición | Misma palabra o frase dicha 2 veces seguidas (tartamudeo o retoma) |
| Toma repetida | Una frase completa que aparece 2 veces: conserva la última completa |
| Diferencia con guion | Palabra distinta, faltante o sobrante comparando con el texto de voz (alineación palabra por palabra) |
| Ritmo | Frase a más de 18 caracteres/s (muy rápida) o menos de 11 (lenta) |

## Salida
Tabla en el chat y en `guiones/AAAA-MM-DD_tema_edicion.md`:
`mm:ss.s – mm:ss.s · tipo · texto · acción (cortar / acortar a 0.3 s / regenerar capítulo / dejar)`.
Al final: duración actual, duración tras cortes y si queda dentro de 61–68 s (reels).
Para la voz generada, `timeline.py` ya recorta pausas (`GAP_MAX`); el editor solo decide si hace falta regenerar un capítulo.
