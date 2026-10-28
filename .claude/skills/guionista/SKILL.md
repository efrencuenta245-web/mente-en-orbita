---
name: guionista
description: Escribe guiones de Mente en órbita. Dada una idea, propone 5 ganchos con las 21 fórmulas probadas, les pone puntaje, elige el mejor y redacta el guion completo (reel de 61-68 s o video largo de YouTube) con datos verificados y fuentes. Úsala siempre que haya que escribir, mejorar o revisar un guion o un gancho.
---
# Guionista

## Entrada
Una idea (de `semana.md`, de la cola de `estrategia.md` o del chat) y el formato: **reel** (61–68 s, vertical) o **largo** (3–8 min, horizontal, capítulos).

## Pasos
1. **Investiga antes de escribir.** Busca con WebSearch cada dato que vayas a usar (fuentes de este año si existen). Anota URL y fecha. Si un dato no se puede verificar, no va o se dice como estimación.
2. **5 ganchos.** Escribe 5 ganchos distintos, cada uno con una fórmula diferente de [formulas.md](formulas.md). Formato:
   `#n · Fórmula X (nombre) · "texto del gancho" · qué se ve en pantalla en el segundo 0`
3. **Puntaje (0–100)** con la rúbrica de [formulas.md](formulas.md#rúbrica). Muestra la tabla con los 6 criterios y el total. Elige el más alto; si hay empate, el que tenga acción visual más clara en el primer segundo.
4. **Guion completo** en `guiones/AAAA-MM-DD_tema.txt` y la versión de voz en `guiones/AAAA-MM-DD_tema_voz.txt`:
   - **Reel:** 11–14 frases, ~900 caracteres, arco: gancho (0–3 s) → escáner "Así se ve por dentro" → explicación con cambio cada 4–6 s → cierre "Mente en órbita" + pregunta Sí/No + invitación a compartir con alguien concreto + final en loop.
   - **Largo:** gancho de 20–30 s que promete N razones/partes → capítulos de 30–60 s, cada uno abre con una frase que funcione sola como gancho de Short → cierre con pregunta y loop al inicio. Deja escrito al final el bloque `EDITS` con 2 cortes de reel de 61–68 s (ver skill `shorts`).
   - Pantalla con cifras ("230 millones"), voz con letra ("doscientos treinta millones"). Abreviaturas en la voz deletreadas como se dicen ("Ge Te A"). Si usas abreviaturas en pantalla, decláralas en `SPOKEN` del guion.
   - Ejemplo mexicano en cada video (lugar, precio, distancia, costumbre).
5. **Archivo de código del guion:** `kit/TEMA_guion.py` con `CAPS = [(nombre, [(pantalla, voz), ...]), ...]`, `REEL_OUT` (cierre de reels) y, en largos, `EDITS`. Así lo lee `timeline.py`.
6. Al final del .txt, la sección **FUENTES** con cada dato → URL.

## Reglas
- Gancho en segunda persona con acción ("Agarra…", "Si naciste…", "Te…"), nada de introducciones.
- Nunca reutilices el arco o las frases de otro video (regla de YouTube del 16-jul-2026).
- Revisa `publicados.md`: no repitas tema de los últimos 14 días.
- Nada de datos inventados ni "dicen que". Lo no confirmado se dice: "según X", "se estima".
