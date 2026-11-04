---
name: yt-animador
description: Solo para YouTube. Diseña y programa las escenas del video largo (horizontal) y de sus Shorts (vertical) con el estilo nuevo de ESTILO.md (motor2, fondo negro, objetos semirrealistas, line-art que brilla) y las revisa con hojas de contacto.
---
# Animador

> **Solo YouTube** (@menteenorbita-t8b). Reglas generales y el **reset del 3-nov-2026** en `YOUTUBE.md` (manda sobre esta skill). No toques nada del flujo del reel diario (CLAUDE.md, estrategia.md, publicados.md ni sus tareas programadas).

## 1. Plano de escenas (antes de programar)
Tabla: frase (del `tl_TEMA_full.json`) → escena → objeto principal → movimiento de cámara → transición → efecto → sonido. Reglas:
- Cambio visual cada 4–6 s; nada estático más de 6 s sin un evento (aparece algo, pastilla, contador, garabato, zoom digital).
- Al menos 5 transiciones distintas de ESTILO.md (glitch, giro, iris, deslizar, golpe, zoom, destello, whip, barrido, empuje), ninguna dos veces seguidas, y 4 efectos de ESTILO.md §4. Nada con personas ni avatares.
- Movimiento rápido y creativo (ESTILO.md §11): objetos que entran en 0.12–0.3 s y cámara con golpes (`piezas.entrada`, `cam_rapida`, `sacudida`, `despiece`, `titulo_golpe`, `numero_golpe`; ejemplos en `kit/nuevo/ejemplo_inicios.py`).
- Inicio de cada video y de cada Short de un tipo distinto a los últimos 6 de `inicios.md` (catálogo en ESTILO.md §12); anótalo ahí.
- Rayos X «así se ve por dentro» una vez por video; una comparación de escala o gráfica que crece; ejemplo mexicano visible.
- 1 a 3 fotos reales con licencia libre (NASA y agencias de EE. UU., Wikimedia PD/CC0/CC BY; nunca personas ni logos), con crédito en pantalla. Bájalas con `bash kit/descargar.sh "URL" nombre.jpg`.
- Etiquetas honestas: «Recreación», «Escala exagerada», «Ejemplo», «Aprox.».
- Cada capítulo abre con una tarjeta corta: kicker `CAPÍTULO N`, título sans + serif y letras de cristal.
- Escenas nuevas en cada video: puedes reutilizar objetos y funciones, nunca la misma composición con otro texto.

## 2. Programar
- **Largo:** `kit/nuevo/TEMA_largo.py` con `os.environ['MOTOR_FORMATO']='h'` antes de importar `motor2` (1920×1080). Acomodo como `kit/nuevo/demo_horizontal.py`: objeto a un lado (`cx=0.68` o `0.32` en la cámara), título y kicker del otro (`cx=` en `title`/`kicker`), subtítulos `y=900, cx=960, maxw=1300` en bloques de máximo 8 palabras. Usa `finish(fr, fi, grain=0.025)` para que el archivo pese menos.
- **Shorts:** `kit/nuevo/TEMA_short.py` vertical, con la estructura de `kit/nuevo/norte.py` (frases, `cap()` en bloques de 6 palabras, `frame_at()` con transiciones, final en loop) y los tiempos de `tl_TEMA_reelA.json` / `reelB`.
- Reutiliza `kit/nuevo/demo_estilo.py` y `kit/nuevo/norte.py` (celular, Tierra, imán, gráficas, foto que cae, `phone_with`, `earth`, `compass_img`).
- Render con `multiprocessing.Pool(2)` a ffmpeg (como `norte.py render`): ~1 min por cada 10 s de video.

## 3. Revisar antes de renderizar
- `preview` de un cuadro por escena y una hoja de contacto. Corrige: objetos que tapan el texto, textos cortados, escenas vacías, subtítulos de más de 2 líneas.
- Revisa también los Shorts en vertical.
