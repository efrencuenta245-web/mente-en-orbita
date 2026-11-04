---
name: yt-cazador
description: Solo para YouTube. Busca qué está funcionando en el nicho del canal de YouTube de Mente en órbita (ciencia, tecnología, espacio, curiosidades en español) y lo ordena por rendimiento relativo a su propio canal y por ingreso relativo estimado, por encima del tamaño del canal. Úsala para encontrar ideas de videos largos y Shorts de YouTube.
---
# Cazador

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales y el **reset del 3-nov-2026** en `YOUTUBE.md` (manda sobre esta skill). No toques nada del flujo del reel diario (CLAUDE.md, estrategia.md, publicados.md ni sus tareas programadas).


## Presupuesto
Máximo **1 llamada de 5 créditos por semana** a `vidiq_outliers` Antes, `vidiq_balance` (gratis): si quedan menos de 40 créditos, usa solo WebSearch (esos 40 se reservan para el estratega de Instagram).

## Pasos
1. `vidiq_outliers` con `language='es'`, `contentType='long'` (o `short` solo si el idioma lo permite), `keyword` con el nicho de la semana (p. ej. "ciencia y tecnología explicada, curiosidades, espacio, videojuegos por dentro"), `publishedWithin='thisMonth'`, `limit=30`, `sort='breakoutScore'`. Opcional `maxSubscribers=500000` para ver canales parecidos al nuestro.
2. **Puntaje del cazador** por video:
   - `rendimiento = breakoutScore` (vistas contra el promedio de su propio canal).
   - `ingreso_relativo = breakoutScore × RPM_categoría` con la tabla de abajo (largo = ×1, Short = ×0.05).
   - `cazador = 0.6 × rendimiento_normalizado + 0.4 × ingreso_relativo_normalizado` (normaliza de 0 a 1 en la lista).
   - El tamaño del canal no suma: un canal de 5 mil suscriptores con 20× vale más que uno de 5 millones con 2×.
3. Para el top 10 escribe: título, canal, breakout, puntaje, **por qué funcionó** (gancho, formato, tema) y **cómo lo haríamos nosotros** (tema visual, sello, ejemplo mexicano). Nunca copies el video: toma el patrón.
4. Guarda en `youtube/cazador.md` (reemplaza la sección de la semana; conserva el historial de 4 semanas) y pasa las 3 mejores ideas a `youtube/ideas.md` con su gancho.

## RPM relativo por categoría (guía, USD por 1 000 vistas de largo en México/LatAm)
| Categoría | RPM relativo |
|---|---|
| Finanzas, dinero, negocios | 3.0 |
| Tecnología, gadgets, IA | 2.0 |
| Ciencia, espacio, salud | 1.5 |
| Educación general, historia | 1.3 |
| Videojuegos | 1.0 |
| Entretenimiento, curiosidades | 0.8 |

## Sin créditos de vidIQ (hasta el 27-nov-2026 hay 0)
Si `vidiq_balance` da menos de 5, haz el mismo análisis con WebSearch (6–8 búsquedas: videos de ciencia y tecnología en español que están rompiendo esta semana, noticias de ciencia en México, preguntas que la gente busca). Puntúa con el mismo criterio usando lo que sepas del canal de origen; marca «sin vidIQ» en `youtube/cazador.md`.
