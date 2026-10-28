# Tareas programadas de YouTube (respaldo)
Si en claude.ai no se pueden agregar conectores a una tarea ya creada, crea una nueva con estos datos (conectores: vidIQ, ElevenLabs y Claude Code Remote) y borra la vieja.

| Tarea | Horario (CDMX) | Cron |
|---|---|---|
| YouTube: La Semana + Cazador | domingo 6:21 pm | `21 18 * * 0` |
| YouTube: video largo semanal | miércoles 9:07 am | `7 9 * * 3` |
| YouTube: analista y comentarios | martes 8:43 pm | `43 20 * * 2` |
| YouTube: auditoría mensual | día 1, 11:13 am | `13 11 1 * *` |

El texto (prompt) de cada una está guardado en la tarea; si hay que recrearla, pídele a Claude en el chat «dame el prompt de la tarea X».
