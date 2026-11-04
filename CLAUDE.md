# Mente en órbita — fábrica de videos (reset del 3-nov-2026)

Canal educativo de Efrén (México): Instagram `@mente_en_orbita1`, página de Facebook, TikTok `@mente.en.rbita` y YouTube `@menteenorbita-t8b`.
Videos verticales hechos 100 % con código, en español de México. Todo se publica con **Metricool** en las 4 redes a la vez.
Habla con Efrén en español, corto y claro: casi siempre está en el celular.

**Lo visual, los efectos, el sonido, las fotos reales y los ganchos están en [`ESTILO.md`](ESTILO.md). Ese archivo manda.**

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
- **Fondo negro** (destellos blancos de 2-3 s solo como sorpresa). **Voz: Silverio** (ElevenLabs). Detalles en ESTILO.md.
- Motor: `kit/nuevo/motor2.py`. Plantilla de escenas, montaje y render: `kit/nuevo/demo_estilo.py`. Sonidos: `kit/nuevo/sfx_demo.py`. Música: `kit/musica.py`.
- **Datos verificados** con fuentes actuales (WebSearch). Fuentes del guion y de las fotos en `guiones/AAAA-MM-DD_tema.txt`.
- **Regla de YouTube:** nada «genérico, repetitivo o de plantilla»: escenas nuevas y arco propio en cada video.
- Se mantienen ejemplos mexicanos y las series «Lo que no ves», «Duelo», «¿Qué pasaría si…?», «Mito o realidad», «Respuestas».

## 3. Pipeline del video diario
1. **Tema:** la idea #1 de la cola de `estrategia.md` (la actualiza la tarea de monitoreo cada mañana). No repitas un tema de `publicados.md` de los últimos 14 días.
2. **Guion** (`guiones/AAAA-MM-DD_tema.txt`) con la fórmula de ESTILO.md §7-8: gancho de 3-7 palabras con «tú/tu» y contradicción, prueba en dos casos, zoom de lo grande a lo pequeño, segundo gancho a los 25-30 s (el error), cierre «mándaselo a…» y loop. 12-15 frases, ~950 caracteres. Versión para voz con números en letra; subtítulos con cifras.
3. **Escenas** (`kit/nuevo/TEMA.py`, copiando `demo_estilo.py`): `preview` de cuadros y hoja de contacto antes del render completo (`python3 TEMA.py render salida.mp4`, ~1 min por cada 10 s).
4. **Voz:** `creative_generate_speech` con voice_id `lLu7VwiNjffLb7HZ3LFW` (**Silverio**), modelo `eleven_v4`, **generations_count=1**. Puedes usar etiquetas como `[curious]` o `[excited]` en el gancho. Guarda flow_id y session_ids en `jobs/TEMA.json`. Espera con `creative_get_flow_run_status` (20 s entre llamadas) y toma `generations[0].content_url`.
5. **Bajar la voz:** `bash kit/descargar.sh "<content_url>" narr_TEMA.mp3 /home/claude/narr_TEMA.mp3`.
6. **Sincronizar y mezclar:** reparte las frases sobre la voz con `kit/autosync.py`; render; efectos (`sfx_demo.py` como base: cada cambio visual con su sonido); música `python3 musica.py DUR musica_TEMA.wav SEMILLA BPM FIN_VOZ` (semilla y BPM 90–110 nuevos); mezcla con `./mix_musica.sh VIDEO_SIN_AUDIO VOZ EFECTOS MUSICA SALIDA`.
   - **Revisa el final:** audio y video con la misma duración (`ffprobe`) y los últimos 3 s más fuertes que −35 dB (`volumedetect`). Nunca quites el `apad` de las mezclas.
7. **Alojar:** `bash kit/alojar.sh /home/claude/TEMA_final.mp4` → URL pública.
8. **Aprobación obligatoria:** aviso «Tu reel de hoy está listo…» (§5), el video con SendUserFile y con SendUserMessage: tema, texto para IG/FB (pregunta-gancho, línea de valor, «mándaselo a…», 3-5 hashtags), título de TikTok, título de YouTube Shorts (máx. 100 caracteres con #Shorts) y la pregunta «¿Lo publico hoy a las 7 pm en Instagram, Facebook, TikTok y YouTube?». **Nunca publiques sin un «sí» explícito de Efrén para ese video exacto.**
9. **Publicar con Metricool** `createScheduledPost`: blogId `7735731`, hoy 19:00 `America/Mexico_City` (si ya pasó, 15 min a partir del «sí»). info: autoPublish true, draft false, media [URL], text aprobado, providers instagram/facebook/tiktok/youtube, instagramData `{"type":"REEL","showReelOnFeed":true}` (sin isAiGenerated: lo eligió Efrén), facebookData `{"type":"REEL","title":…}`, tiktokData `{"title":…,"privacyOption":"PUBLIC_TO_EVERYONE"}`, youtubeData `{"title":…,"type":"short","privacy":"public","madeForKids":false,"category":"SCIENCE_TECHNOLOGY"}`. Si da error, no repitas igual: corrige solo si el error dice qué falta. Confirma con `getScheduledPosts` y manda el plannerUrl.
10. **Revisión 20 min después de publicar** (`send_later` en la misma sesión): `getScheduledPosts` debe mostrar que ya no está pendiente; aviso «Ya se publicó…» o «No se pudo publicar…» (§5). Registra en `publicados.md` (fecha, tipo diario/extra, tema, gancho, duración, redes, enlaces) y guarda con `guardar.sh`.

**Texto del reel:** pregunta-gancho, línea de valor, «Mándaselo a alguien que…» y 3-5 hashtags (#curiosidades #ciencia #mexico #menteenorbita + uno del tema).

## 3b. Videos extra (pedidos por Efrén)
No alteran el video diario ni reordenan la cola. Mismo pipeline, misma aprobación. Si no da hora, sugiere una al menos 3 h antes o después de las 19:00. Se registran como **extra**. Todos cuentan para las estadísticas.

## 4. Monitoreo de las 4 redes
- Fuente principal: **Metricool** (brandId `7735731`, timezone `America/Mexico_City`). vidIQ ya no se usa en las tareas (no tiene créditos y no hace falta).
- Seguidores: Instagram `IGEV01`, TikTok `TKEV07` (conector evolution de cada red); Facebook y YouTube con getAnalyticsAvailableMetrics.
- **Si Instagram o TikTok vienen en 0 o vacíos (incluso los seguidores)**, no es falta de videos: Metricool perdió el permiso de estadísticas de esa red. En la «acción para Efrén» pídele: Metricool → Conexiones → desconectar esa red, quitar el acceso de Metricool en la app de esa red y volver a conectarla con el mismo método, aceptando todos los permisos.
- Datos acumulados: `stats/redes.csv` (fecha,red,tema,url,vistas,retencion,tiempo_medio,compartidos,guardados,likes,clasificacion) y `stats/seguidores.csv` (fecha,red,seguidores).
- Metas: TikTok Recompensas (10 000 seguidores y 100 000 vistas en 30 días, videos de más de 1 min) y YouTube (1 000 suscriptores + 10 M de vistas de Shorts públicas en 90 días; sube a 20 M para quien entre desde el 1-feb-2027). Solo cuentan las vistas de videos **públicos**.

## 5. Avisos a Efrén (PushNotification de menos de 200 caracteres + SendUserMessage con detalles)
Video:
1. «Tu reel de hoy está listo: <tema>. ¿Lo publico a las 7 pm en IG, FB, TikTok y YouTube?»
2. «No pude terminar el reel de hoy: <motivo>» + qué necesitas de él.
3. «Ya se publicó tu reel en 4 redes: <tema>» + enlaces.
4. «No se pudo publicar el reel de las 7 pm: <motivo>» + qué hacer y el video para que él lo suba.
Monitoreo:
5. «Estrategia de hoy lista: <idea #1>» · «No pude hacer la estrategia de hoy: <motivo>»
6. «Tu reporte semanal de las 4 redes está listo: <dato principal>» · «No pude hacer el reporte semanal: <motivo>»
Si un guardado en GitHub falla después de los reintentos, no detengas la tarea: termina lo demás, manda el aviso de error de esa tarea con el texto exacto y pon en el mensaje lo que no se guardó.

## 6. Créditos y límites
- **ElevenLabs** (plan Starter, 30 000 créditos al mes): unos 1 000 créditos por video. Si responde 429 o sin cuota: plan B, voz gratis Chatterbox con el workflow `voz_hq` (crea `tts_hq/narr_TEMA.json` con `{"text_file": "guiones/…_voz.txt", "ref": "ald", "exaggeration": 0.6, "cfg": 0.45}`, guárdalo con `guardar.sh` y espera `inbox/narr_TEMA.mp3`, 15–40 min); plan C, avisar a Efrén.
- **Red:** aquí solo hay GitHub y registros de paquetes; todo lo demás se baja con `descargar.sh`.
- **YouTube largo y skills `yt-*`:** en pausa desde el reset (usan el estilo viejo). El monitoreo de YouTube lo hace la tarea de las 4 redes.
