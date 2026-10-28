---
name: animador
description: Diseña y programa las escenas 3D de cada video de Mente en órbita. Primero identifica el tema y elige el tema visual (estudio, espacio, médico, plano, neón, noir, naturaleza, micro, mapa), después arma escenas nuevas con motor3d.py/escenas.py, tarjetas de transición y revisión con hojas de contacto. Úsala cada vez que haya que animar un guion (reel o video largo).
---
# Animador

## 1. Elegir el tema visual (obligatorio, nunca el mismo por costumbre)
Lee el guion y elige con la tabla de [temas.md](temas.md). Escribe en `jobs/TEMA.json` el campo `"tema_visual"` y una línea de por qué.
- Si el mismo tema visual salió en los 2 videos anteriores (`publicados.md` → columna Tema visual), usa la segunda opción salvo que el tema lo exija (p. ej. anatomía → médico).
- Un video largo puede cambiar de tema por capítulo (p. ej. noir en la historia del hackeo y estudio en el resto): exporta `MOTOR_TEMA` distinto por render de capítulo solo si la transición entre ellos es una tarjeta.

## 2. Plano de escenas
Antes de programar, escribe una tabla: frase → escena → objeto 3D principal → movimiento de cámara → efecto (escáner, contador, escala real, etiqueta). Reglas:
- Cambio de escena cada 4–6 s; nada de escenas estáticas más de 6 s sin un evento (aparece algo, cambia el título, contador).
- El escáner de rayos X "Así se ve por dentro" aparece una vez por video (sello).
- Una comparación de escala real o "del bolsillo al espacio" y al menos un contador en vivo.
- Ejemplo mexicano visible en pantalla.
- Etiquetas honestas: "Recreación", "Escala exagerada", "Mapa aproximado", "Imagen oficial: …" cuando uses imágenes reales.
- Escenas nuevas en cada video (regla de YouTube): puedes reutilizar objetos/ayudantes, nunca la misma composición con otro texto.

## 3. Programar
- Archivo `kit/TEMA.py` (copiar a /home/claude). Importa `escenas` (que trae `motor3d`): ver el encabezado de `kit/escenas.py` y el ejemplo completo `kit/gta6.py` (video largo) y `kit/demo_temas.py` (mínimo).
- Define `CARD` (tarjetas entre capítulos; estilos `bounce`, `line`, `rings`, `error`, `ruler`, en blanco y negro con transición a gris) y `SHOTS = [(('c0', 0), s_gancho), (('card', 'c1'), None), ...]`.
- Variables: `MOTOR_TEMA`, `GTA_FMT=h|v` (largo horizontal / reels verticales), `VIDEO_TL=/home/claude/tl_TEMA_MODO.json`.
- Encuadre vertical: usa `vfit(d, wide=True)` en escenas anchas.
- Imágenes reales (portadas, capturas oficiales de prensa): bájalas con el workflow `fetch` a `inbox/`, cópialas a `/home/claude/img/` y úsalas con `photo()` o como textura (`real_img()`); nunca uses material filtrado o pirata.

## 4. Revisar antes de renderizar
- `python3 TEMA.py info` (lista de escenas y tiempos) y `python3 TEMA.py sheet salida.jpg t1 t2 …` con un cuadro por escena.
- Mira la hoja y corrige: objetos que tapan el título o los subtítulos, textos cortados en vertical, escenas vacías, colores sin contraste con el tema.
- Revisa también la versión vertical de los reels (`GTA_FMT=v`).
