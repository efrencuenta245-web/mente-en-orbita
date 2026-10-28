# Tareas programadas de YouTube (respaldo)
Si en claude.ai no se pueden agregar conectores a una tarea ya creada, crea una nueva con estos datos (conectores: vidIQ, ElevenLabs y Claude Code Remote) y borra la vieja.

| Tarea | Horario (CDMX) | Cron | ID |
|---|---|---|---|
| YouTube: La Semana + Cazador | domingo 6:21 pm | `21 18 * * 0` | `trig_01NqsUnuaYdDHHL6WiDBJvWz` |
| YouTube: video largo semanal | miércoles 9:07 am | `7 9 * * 3` | `trig_01E9pD6yhzi2RXwGZaVjFfXD` |
| YouTube: analista y comentarios | martes 8:43 pm | `43 20 * * 2` | `trig_016tqwszuxuH5pzZLDwMLs4N` |
| YouTube: auditoría mensual | día 1, 11:13 am | `13 11 1 * *` | `trig_01CRQsgCg7brKmrU1Whn1rrx` |

El texto (prompt) de cada una está guardado en la tarea; si hay que recrearla, pídele a Claude en el chat «dame el prompt de la tarea X».

27-oct-2026: las 4 tareas se recrearon desde el chat principal con conectores (vidIQ, ElevenLabs, Claude Code Remote y Claude Docs) y quedaron activadas; las viejas sin conectores se borraron.
