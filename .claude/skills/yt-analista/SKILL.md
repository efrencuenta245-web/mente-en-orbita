---
name: yt-analista
description: Solo para YouTube. Lee la retención de los videos de YouTube y dice el segundo exacto en que la gente abandonó, qué se decía y qué se veía en ese momento, con la causa y la corrección para el siguiente video.
---
# Analista

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales en `YOUTUBE.md`. No toques nada del flujo de Instagram (CLAUDE.md, estrategia.md, publicados.md, ideas.md ni sus tareas programadas).


## Fuentes de datos
- **YouTube (5 créditos por llamada; necesita el canal conectado a vidIQ):** `vidiq_channel_analytics` con `report='audience_retention'` y `filters='video==ID'` → curva de 100 puntos (`elapsedVideoTimeRatio`, `audienceWatchRatio`, `relativeRetentionPerformance`). Máximo 1 video por semana (el largo).
- **Qué se decía:** `tl_TEMA_MODO.json` del repo (frases y palabras con tiempo) y el plano de escenas; si no existe, `vidiq_video_transcript`.

## Método
1. Convierte cada punto de la curva a segundos: `t = ratio × duración`.
2. Caídas: puntos donde la retención baja más de 3 puntos en menos de 2 s, o donde `relativeRetentionPerformance` cae debajo de 0.4.
3. Para cada caída: `mm:ss` · % que se fue · frase exacta que sonaba (del tl.json) · escena en pantalla · causa probable (gancho lento, frase larga sin imagen nueva, escena >6 s, dato confuso, final previsible).
4. También marca los **picos** (re-vistas): qué los provocó, para repetirlo.
5. Escribe 3 lecciones accionables en `youtube/aprendizajes.md` (fecha, video, dato, regla nueva) y, si cambia una regla, anótala en `YOUTUBE.md`.

## Salida para Efrén (≤ 10 líneas)
"Se fueron en 0:07 (−18 %) mientras decía «…»: la escena duró 9 s sin cambio. Próximo video: corte cada 4 s en el arranque."
