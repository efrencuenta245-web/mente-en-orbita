# Tareas programadas de YouTube (recreadas el 3-nov-2026 con el estilo nuevo)
Todas corren en la nube con los conectores Metricool, ElevenLabs, vidIQ, Claude Code Remote y Claude Docs, y avisan al celular.

| Tarea | Horario (CDMX) | Cron | ID |
|---|---|---|---|
| YouTube: plan de la semana (cazador + semana) | domingo 5:13 pm | `13 17 * * 0` | `trig_012LMZQYRcF3Z3CJbGMG2tF7` |
| YouTube: video largo quincenal (+ 2 Shorts) | miércoles 9:07 am | `7 9 * * 3` | `trig_017pqCFJvd52rPHPZyJvyusA` |
| YouTube: analista y comentarios | martes 8:43 pm | `43 20 * * 2` | `trig_01WGk2VYdm4zMBCtzArkWR2f` |
| YouTube: auditoría mensual | día 1, 11:13 am | `13 11 1 * *` | `trig_01PhheQKS1AJv294PEHR95py` |

- El plan de la semana va a las 5:13 pm para no chocar con el reporte semanal de las 4 redes (domingo 6:21 pm).
- El largo se salta la semana si ya hubo uno «quincenal» en los últimos 13 días (el miércoles 4-nov se salta: el último fue Starlink, 28-oct).
- Publicación con Metricool solo en YouTube y solo con el «sí» de Efrén: largo jueves 5 pm; Shorts viernes y sábado 1 pm.
- El texto (prompt) de cada una está guardado en la tarea; si hay que recrearla, pídele a Claude en el chat «dame el prompt de la tarea X».
