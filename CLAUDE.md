# Mente en órbita — fábrica de videos (reset del 3-nov-2026)

Canal educativo de Efrén (México): Instagram `@mente_en_orbita1`, página de Facebook, TikTok `@mente.en.rbita` y YouTube `@menteenorbita-t8b`.
Videos verticales hechos 100 % con código, en español de México. Todo se publica con **Metricool** en las 4 redes a la vez.
Habla con Efrén en español, corto y claro: casi siempre está en el celular.

**Lo visual, los efectos, el sonido, las fotos reales y los ganchos están en [`ESTILO.md`](ESTILO.md). Ese archivo manda.** Ritmo y movimiento rápidos: §11; inicios distintos en cada video: §12 + registro `inicios.md`.

## 0. Arranque de cada sesión (siempre igual)
```bash
git clone --depth 1 https://github.com/efrencuenta245-web/mente-en-orbita /home/claude/mente-en-orbita   # timeout largo (10 min)
cp -r /home/claude/mente-en-orbita/kit/* /home/claude/
python3 -c "import numpy, PIL, scipy" || pip install --break-system-packages -q numpy pillow scipy
bash /home/claude/mente-en-orbita/kit/prueba_github.sh     # debe imprimir GITHUB_OK
```
Antes de clonar llama `add_repo` (owner `efrencuenta245-web`, repo `mente-en-orbita`, access `push`) y después `register_repo_root`, si esas herramientas existen.

## 1. Regla de oro de GitHub (para que no vuelva el error 403)
Las tareas programadas de Claude **solo pueden subir a ramas que empiezan con `claude/`**. Por eso:
- **Nunca** hagas `git push` a `main` ni a ramas `pub-*`.
- **Guardar archivos:** `TAREA=<nombre> bash kit/guardar.sh "mensaje" ruta1 ruta2 …` (desde la raíz del repo). Sube una rama `claude/guardar-…`; el workflow `sync` la pasa a `main` en ~15-60 s y el script espera a confirmarlo.
  - Código 0 = guardado. 4 = GitHub rechazó el permiso. 5 = la rama subió pero `sync` no la pasó (los datos siguen a salvo en esa rama).
- **Descargar algo bloqueado aquí** (voz de ElevenLabs, fotos de NASA/Wikimedia): `bash kit/descargar.sh "URL" nombre_unico.ext [destino]`. Hazlo en cuanto tengas la URL (las de ElevenLabs caducan en ~2 h).
- **Alojar el video para Metricool:** `bash kit/alojar.sh /ruta/video.mp4` → la última línea trae `URL https://raw.githubusercontent.com/…/<sha>/<archivo>.mp4`.
- Si `prueba_github.sh` falla: manda el aviso de error correspondiente (§5) con el texto que imprime, y sigue con todo lo que no necesite GitHub.

## 2. Formato
- 1080×1920, 24 fps, **61 a 75 s** (TikTok solo paga videos de más de 1 min).
- **Fondo negro** (destellos blancos de 2-3 s solo como sorpresa). **Voz: Isaac** (ElevenLabs, no Silverio: Efrén no quiere sonar genérico). Detalles en ESTILO.md.
- Motor: `kit/nuevo/motor2.py`. Montaje, tiempos, subtítulos, sonido, render y final: `kit/nuevo/montaje.py` (ejemplos: `bateria.py`, `induccion.py`, `teclado.py`, `refri.py`; piezas en `piezas.py`). Sonidos: `kit/nuevo/sfx_demo.py`. Música: `kit/musica.py`.
- **Datos verificados** con fuentes actuales (WebSearch). Fuentes del guion y de las fotos en `guiones/AAAA-MM-DD_tema.txt`.
- **Regla de YouTube:** nada «genérico, repetitivo o de plantilla»: escenas nuevas y arco propio en cada video.
- Se mantienen ejemplos mexicanos y las series «Lo que no ves», «Duelo», «¿Qué pasaría si…?», «Mito o realidad», «Respuestas».

## 3. Pipeline diario: 2 reels al día con 4 de reserva (desde el 5-nov-2026)
**Horario fijo:** cada día salen 2 reels en las 4 redes, a las **8:00** y a las **19:00** (`America/Mexico_City`). Siempre hay **4 de reserva** programados en Metricool (mañana y pasado mañana, 8:00 y 19:00).
**La tarea de las 4:35 pm hace 2 reels** y los programa, con el «sí» de Efrén, en los **2 primeros huecos libres**: normalmente pasado mañana a las 8:00 y a las 19:00. Si un día falló, la siguiente tarea llena primero los huecos que quedaron. Un hueco está ocupado si Metricool tiene un post pendiente a esa hora (±30 min); los extras van en otras horas y no cuentan.

Para cada uno de los 2 reels:
1. **Tema:** las ideas #1 y #2 de la cola de `estrategia.md` (sin repetir temas de `publicados.md` de los últimos 14 días ni de «Ya programados»). Como salen 2 días después, deben ser temas que no caduquen; si una idea depende de una fecha, respeta la fecha.
2. **Guion** (`guiones/AAAA-MM-DD_tema.txt`) con la fórmula de ESTILO.md §7-8: gancho de 3-7 palabras con «tú/tu» y contradicción, prueba en dos casos, zoom de lo grande a lo pequeño, segundo gancho a los 25-30 s (el error), cierre «mándaselo a…» y loop (el «mándaselo» SOLO al final, nunca a la mitad: la gente cree que ya terminó y se va; pedido de Efrén, 6-nov). 12-15 frases, ~950 caracteres. Datos verificados con WebSearch y fuentes en el guion.
3. **Voz:** `creative_generate_speech` con voice_id `QmPfzE500cXXHM9uQKGc` (**Isaac**), modelo `eleven_v4`, **generations_count=1**, texto con números en letra; etiquetas `[curious]` en el gancho y `[excited]` en el segundo gancho. Lanza las 2 voces juntas.
4. **Tiempos por palabra:** cuando termine cada voz, `creative_transcribe_audio` (`eleven_scribe_v1`, mismo `flow_id`, `connect_from=[node_id de la voz]`). Del resultado toma `words_download_url`.
5. **Bajar:** `bash kit/descargar.sh "<content_url>" narr_TEMA.mp3 /home/claude/narr_TEMA.mp3` y `bash kit/descargar.sh "<words_download_url>" words_TEMA.json /home/claude/words_TEMA.json` (caducan en ~2 h).
6. **Escenas con `kit/nuevo/montaje.py`** (lee su encabezado). Un archivo `kit/nuevo/TEMA.py` con `TEMA`, `TXT` (frases de pantalla con cifras), `VOZ` (las mismas frases como se dicen) y `ESCENAS`. Ejemplos completos del 4-nov: `bateria.py`, `induccion.py`, `teclado.py` y `refri.py`; piezas reutilizables en `kit/nuevo/piezas.py` (celular con pantalla propia, pila, almohada, termómetro, pastilla tachada, ondas de calor). Objetos y escenas nuevos en cada video (regla de YouTube): reutiliza piezas, nunca la misma composición.
   - **Letras de cristal gigantes y transiciones creativas (pedido de Efrén, 6-nov):** `M.cristal(fr.base, fr.fx, 'PALABRA', u, t0=…)` antes de `draw_objects` en 3+ escenas (una en los primeros 6 s) y 3+ transiciones creativas (cubo, rompe, rebanadas, cristal, mosaico, remolino) sin repetir rachas de reels anteriores (ESTILO.md §1 y §4b; muestra: `demo_cristal.py`). `hoja` imprime ERROR si falta algo y `render` no arranca hasta corregirlo.
   - **Movimiento e inicio (pedido de Efrén, 4-nov):** transiciones de 0.25–0.38 s, 8+ distintas y ninguna dos veces seguidas; objetos que entran con movimiento en 0.12–0.3 s y cámara con golpes rápidos (`piezas.entrada`, `cam_rapida`, `sacudida`, `despiece`, `titulo_golpe`, `numero_golpe`; ver `ejemplo_inicios.py`). **Inicio de un tipo distinto** a los últimos 6 de `inicios.md` (catálogo en ESTILO.md §12) y primera transición distinta a la del video anterior; el final sigue en loop. Cuando `hoja` salga sin ERROR: `python3 TEMA.py registrar "AAAA-MM-DD HH:MM" "tema" "N nombre del inicio"` (agrega la fila en `inicios.md`; no la escribas a mano) y guárdalo con `guardar.sh`.
   - `python3 TEMA.py tiempos /home/claude/narr_TEMA.mp3 /home/claude/words_TEMA.json` (alarga las pausas solo hasta 61.3 s o más)
   - `python3 TEMA.py hoja` → corrige cada ERROR que imprima y mira `/home/claude/hoja_TEMA.png` (las letras de cristal se leen, nada vacío ni cortado) antes de renderizar.
   - `python3 TEMA.py render` (~10 min por reel; los 2 renders uno después del otro).
   - `python3 TEMA.py final "Línea 1" "línea 2" CATEGORÍA SEMILLA BPM` → efectos, música (semilla y BPM 90–110 nuevos), mezcla, portada (ESTILO.md §10) y portada como cuadro 0: `/home/claude/TEMA_final_p.mp4` y `/home/claude/portada_TEMA.jpg`. Revisa lo que imprime: video y audio con la misma duración, últimos 3 s más fuertes que −35 dB y menos de 95 MB.
7. **Alojar:** `bash kit/alojar.sh /home/claude/TEMA_final_p.mp4` y `bash kit/alojar.sh /home/claude/portada_TEMA.jpg` → URL públicas. Guarda guion, `TEMA.py` y jobs con `guardar.sh`.
8. **Aprobación obligatoria (los 2 juntos):** aviso «Tus 2 reels del <día> están listos…» (§5), los 2 videos y sus portadas con SendUserFile y con SendUserMessage: para cada uno, día y hora, tema, texto para IG/FB (pregunta-gancho, línea de valor, «mándaselo a…», 3-5 hashtags), título de TikTok y título de YouTube Shorts (máx. 100 caracteres con #Shorts); y la pregunta «¿Los programo así? Responde sí a los dos, o dime cuál cambio». **Nunca programes sin un «sí» explícito de Efrén para esos videos.**
9. **Programar con Metricool** `createScheduledPost` (uno por reel), en su hueco: blogId `7735731`, date y publicationDate con timezone `America/Mexico_City`. info: autoPublish true, draft false, media [URL del video], `videoThumbnailUrl` [URL de la portada], text aprobado, providers instagram/facebook/tiktok/youtube, instagramData `{"type":"REEL","showReelOnFeed":true}` (sin isAiGenerated: lo eligió Efrén), facebookData `{"type":"REEL","title":…}`, tiktokData `{"title":…,"privacyOption":"PUBLIC_TO_EVERYONE"}`, youtubeData `{"title":…,"type":"short","privacy":"public","madeForKids":false,"category":"SCIENCE_TECHNOLOGY"}`. Si responde VIDEO_THUMBNAIL_NOT_APPLICABLE, repite una vez sin `videoThumbnailUrl` (el cuadro 0 ya es la portada). Si da otro error, no repitas igual: corrige solo si el error dice qué falta. Confirma con `getScheduledPosts` y manda los plannerUrl. Anota los 2 en «Ya programados» de `estrategia.md` y sácalos de la cola.
10. **¿Se publicó?** `getScheduledPosts` trae también los ya publicados: cada red debe decir `PUBLISHED` con su `publicUrl` (una lista vacía NO prueba nada: puede ser que lo borraron). La tarea de las 6:43 revisa el de las 19:00 del día anterior y la de las 4:35 pm revisa el de las 8:00 de ese día. Si salió: regístralo en `publicados.md` (fecha y hora, tipo diario, tema, gancho, duración, redes y enlaces) y quítalo de «Ya programados». Si no: aviso «No se pudo publicar el reel de las <hora>: <motivo>» con el plannerUrl y el enlace del video.

**Texto del reel:** pregunta-gancho, línea de valor, «Mándaselo a alguien que…» y 3-5 hashtags (#curiosidades #ciencia #mexico #menteenorbita + uno del tema).

## 3b. Videos extra (pedidos por Efrén)
No alteran los reels diarios, ni la reserva, ni la cola. Mismo pipeline y misma aprobación. Si no da hora, sugiere una entre las 11:00 y las 16:00 (lejos de las 8:00 y las 19:00). Se registran como **extra** y cuentan para las estadísticas.

## 4. Monitoreo de las 4 redes
- Fuente principal: **Metricool** (brandId `7735731`, timezone `America/Mexico_City`). vidIQ ya no se usa en las tareas (no tiene créditos y no hace falta).
- Seguidores: Instagram `IGEV01`, TikTok `TKEV07` (conector evolution de cada red); Facebook y YouTube con getAnalyticsAvailableMetrics.
- **Si Instagram o TikTok vienen en 0 o vacíos (incluso los seguidores)**, no es falta de videos: Metricool perdió el permiso de estadísticas de esa red. En la «acción para Efrén» pídele: Metricool → Conexiones → desconectar esa red, quitar el acceso de Metricool en la app de esa red y volver a conectarla con el mismo método, aceptando todos los permisos.
- Datos acumulados: `stats/redes.csv` (fecha,red,tema,url,vistas,retencion,tiempo_medio,compartidos,guardados,likes,clasificacion) y `stats/seguidores.csv` (fecha,red,seguidores).
- Metas: TikTok Recompensas (10 000 seguidores y 100 000 vistas en 30 días, videos de más de 1 min) y YouTube (1 000 suscriptores + 10 M de vistas de Shorts públicas en 90 días; sube a 20 M para quien entre desde el 1-feb-2027). Solo cuentan las vistas de videos **públicos**.

## 5. Avisos a Efrén (PushNotification de menos de 200 caracteres + SendUserMessage con detalles)
Video:
1. «Tus 2 reels del <día> están listos: <tema 1> y <tema 2>. ¿Los programo a las 8 am y 7 pm?»
2. «No pude terminar los reels de hoy: <motivo>» + qué necesitas de él (si solo salió uno, mándalo y dilo).
3. Lo que ya se publicó va dentro del reporte de las 6:43 y del aviso de las 4:35 (sin aviso aparte).
4. «No se pudo publicar el reel de las <hora>: <motivo>» + qué hacer y el enlace del video para que él lo suba.
Monitoreo:
5. «Estrategia de hoy lista: <idea #1>» · «No pude hacer la estrategia de hoy: <motivo>»
6. «Tu reporte semanal de las 4 redes está listo: <dato principal>» · «No pude hacer el reporte semanal: <motivo>»
Si un guardado en GitHub falla después de los reintentos, no detengas la tarea: termina lo demás, manda el aviso de error de esa tarea con el texto exacto y pon en el mensaje lo que no se guardó.

## 6. Créditos y límites
- **ElevenLabs:** Efrén tiene más de 100 000 créditos (dato suyo, 3-nov-2026). Gasto: ~900 créditos por reel (2 al día ≈ 55 000 al mes) y ~3 000 por largo de YouTube. La transcripción con Scribe para los tiempos no cuesta créditos. Si responde 429 o sin cuota: plan B, voz gratis Chatterbox con el workflow `voz_hq` (crea `tts_hq/narr_TEMA.json` con `{"text_file": "guiones/…_voz.txt", "ref": "ald", "exaggeration": 0.6, "cfg": 0.45}`, guárdalo con `guardar.sh` y espera `inbox/narr_TEMA.mp3`, 15–40 min); plan C, avisar a Efrén.
- **Red:** aquí solo hay GitHub y registros de paquetes; todo lo demás se baja con `descargar.sh`.
- **YouTube largo y skills `yt-*`:** activos con el estilo nuevo (ver `YOUTUBE.md`): largo cada 15 días + 2 Shorts, publicados con Metricool solo en YouTube con aprobación. El monitoreo de YouTube lo hace la tarea de las 4 redes.
