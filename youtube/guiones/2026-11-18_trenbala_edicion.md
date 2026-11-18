# Edición de voz · tren bala (18-nov-2026)

Voz: **plan B** (Chatterbox, workflow `voz_hq`, referencia `ald`): el conector de ElevenLabs no respondió (timeouts, «Service Unavailable», «Bad Request»), así que no se pudo usar a Isaac.
Revisión (yt-editor) con los tiempos por línea del plan B (no hay palabras de Scribe):

| Tipo | Hallazgo | Acción |
|---|---|---|
| Silencio largo | Cada línea traía ~0.3–0.6 s de silencio al final | recortado por energía (−38 dB) antes de armar la línea de tiempo |
| Ritmo | ~13 caracteres/s (más lento que Isaac); el largo daba 6:33 | `atempo=1.1` en el largo y el Short A (sin cambio de tono); Short B a velocidad normal |
| Pausas entre frases | máx. 0.55 s (timeline.py) y 0.9 s entre capítulos | dejar |
| Diferencias con el guion | sin transcripción automática; se asume el texto del guion | revisar al escucharlo |

- full: 359.4 s (5:59), fin de voz 358.0 s
- reelA: 70.5 s (1:10), fin de voz 69.1 s
- reelB: 53.9 s (0:53), fin de voz 52.6 s
