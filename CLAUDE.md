# Mente en órbita — fábrica de videos

Canal de Efrén (México) en Instagram `@mente_en_orbita1` (y YouTube, aún sin conectar a vidIQ).
Videos educativos verticales 100 % generados con código, en español neutro de México.
Habla con Efrén en español, corto y claro: casi siempre está en el celular.

## 0. Arranque de cada sesión
```bash
cp -r /home/claude/mente-en-orbita/kit/* /home/claude/   # todos los scripts asumen /home/claude
python3 -c "import numpy, PIL, scipy" || pip install --break-system-packages numpy pillow scipy
```
Antes de hacer `git push`, haz `git -C /home/claude/mente-en-orbita pull --rebase`.

## 1. Formato (obligatorio)
- 1080×1920, 24 fps. Con narración, entre **61 y 68 s** (TikTok solo paga videos de más de 1 min; nunca más de 70 s).
- **Estructura:**
  - Gancho (0–3 s): un objeto concreto más un dato que parece imposible.
  - Escáner de rayos X ("Así se ve por dentro").
  - Explicación con cambio de escena cada 4–6 s.
  - Cierre "Mente en órbita" más una pregunta Sí/No o "¿Qué quieres que explique después?".
- **Visual:**
  - Entornos reales con objetos 3D y colores reales; el neón solo en efectos.
  - Subtítulos palabra por palabra, pastillas HUD y etiquetas honestas ("Recreación", "Escala exagerada").
- **Sello de marca:**
  - El anillo escáner de rayos X con su sonido.
  - Comparaciones a "escala real", el zoom "del bolsillo al espacio" y los contadores en vivo.
  - Ejemplos mexicanos.
  - Series fijas: "Lo que no ves", "Duelo", "¿Qué pasaría si…?", "Mito o realidad", "Respuestas".
- **Anatomía:** estilo de ilustración médica 3D clara (ver `kit/vasec.py`).
- **Datos:** todos verificados con fuentes actuales (WebSearch). Las fuentes se guardan en `guiones/`.
- **Regla de YouTube (16-jul-2026):** nada de contenido "genérico, repetitivo o de plantilla". Cada video lleva escenas nuevas y un arco narrativo propio; no se reutiliza la misma escena con otro texto.

## 2. Qué funciona (Instagram, 27-oct-2026)
| Reel | Reproducciones | Saltos | % visto | Compartidos | Guardados |
|---|---|---|---|---|---|
| Varg (moto eléctrica vs gasolina) | 2296 | 29 % | 48 % | 4 | 4 |
| Láseres entre satélites | 1990 | 28 % | 53 % | 5 | 12 |
| Satélites que no chocan | 1872 | 33 % | 50 % | 1 | 10 |
| Relatividad / GPS del tiempo | 1712 | 36 % | 55 % | 2 | 5 |
| Cancelación de ruido | 1671 | 35 % | 35 % | 9 | 13 |
| Fibra óptica | 1583 | 31 % | 45 % | 41 | 15 |
| GPS | 250 | 33 % | 34 % | 1 | 1 |
| Carga inalámbrica | 48 | 63 % | 54 % | 1 | 0 |

**Conclusión:**
- Ganan los ganchos de objeto concreto con un dato imposible y acción inmediata.
- El espacio retiene más.
- La tecnología de todos los días se comparte más.
- La hora de publicación pesa menos que el gancho. Publicamos a las **19:00 (CDMX)** y se ajusta con los datos.

## 2b. Estrategia viral
Lee **`estrategia.md`** antes de elegir el tema. Ahí están los patrones que se están haciendo virales, las reglas nuevas (gancho en segunda persona, música de fondo, 61–68 s para TikTok, final en loop) y la cola de ideas ordenada. Produce la idea #1 salvo que los datos del día digan claramente otra cosa.

## 3. Pipeline diario
1. **Tema.**
   - Revisa `vidiq_instagram_owner_insights` (platformAccountId `39432107649769379`) y `vidiq_instagram_tiktok_outlier_search`, más `ideas.md`.
   - No repitas un tema de `publicados.md` de los últimos 14 días.
   - Si un reel reciente falló, cambia la variable que falló (gancho, tema o ritmo).
2. **Guion** (`guiones/AAAA-MM-DD_tema.txt`):
   - 11–14 frases y unos 900 caracteres como máximo.
   - Versión para la voz con los números escritos con letra; en los subtítulos (PHR), cifras.
3. **Escenas** (`/home/claude/TEMA.py`):
   - Usa como base `popo.py` (paisaje/ciencia) o `vasec.py` (anatomía); los ayudantes 3D están en `vasec.py`.
   - Define `PHR`, `CUTS`, `ENVS`, `T_OUT`, `DUR`, `NF`, `render(t)`, `W`, `H` y `anim`.
   - Revisa cuadros con `preview` y `csheet.py` antes de renderizar.
4. **Voz:**
   - `creative_generate_speech` con voice_id `5egO01tkUjEzu7xSSE8M` (Carmelo), modelo `eleven_v4`, **generations_count=1**.
   - Guarda el flow_id y los session_ids en `jobs/TEMA.json`.
   - Haz poll de `creative_get_flow_run_status` (espera ~20 s entre llamadas para no provocar un 429) hasta `all_completed`; la URL está en `generations[0].content_url` (firmada, caduca en 2 h).
   - Plan de Efrén: ElevenLabs Starter (30 000 créditos al mes, uso comercial). Una toma ≈ 875 créditos.
5. **Bajar la voz** (aquí ElevenLabs y storage.googleapis.com están bloqueados):
   - Escribe la URL en `jobs/narr_TEMA.mp3.url`, haz commit y push a `main`.
   - El workflow `fetch` la deja en `inbox/narr_TEMA.mp3` en 1–2 min.
   - Haz `git pull` y copia el archivo a `/home/claude/narr_TEMA.mp3`. Hazlo enseguida: las URL firmadas caducan.
6. **Sincronizar y mezclar:**
   - Crea `TEMA_sync.py` copiando `popo_sync.py` (usa `autosync.py`, que reparte la voz entre frases sin mapa manual).
   - `python3 TEMA_sync.py map` → revisa que cada frase empiece en su tramo.
   - `python3 TEMA_sync.py voz` → voz editada (si pasa de 70 s, sube `TEMPO` hasta 1.04 o baja las pausas).
   - `./render_varg.sh TEMA_sync`, luego `python3 sfx_TEMA.py` (el script detecta `TEMA_sync`).
   - Música: `python3 musica.py NEWDUR musica_TEMA.wav SEMILLA 96` (cambia la semilla y el BPM, 90–110, en cada video).
   - Mezcla: `./mix_musica.sh TEMA_sync_sin_audio.mp4 narr_TEMA_editada.wav efectos_TEMA_sync.wav musica_TEMA.wav /mnt/user-data/outputs/TEMA_con_narracion.mp4`.
   - Revisa la hoja de contacto (`check_popo.sh VIDEO`) y los niveles de audio.
7. **Alojar:**
   - Crea una rama huérfana `pub-AAAAMMDD-tema` que solo tenga el mp4 y haz push.
   - Pasa la URL `https://raw.githubusercontent.com/efrencuenta245-web/mente-en-orbita/<sha>/<archivo>.mp4` a `vidiq_video_upload` → `videoUrl` y `uploadId`.
   - El workflow `limpieza` borra las ramas `pub-*` después de 1 día. Desde la sesión no se pueden borrar ramas ni crear releases.
8. **Aprobación (obligatoria):**
   - Manda a Efrén el video (SendUserFile), el texto propuesto y la hora, con PushNotification.
   - Incluye también un título y una descripción cortos para que él lo suba a **TikTok** y **YouTube Shorts** desde el celular.
   - **Nunca publiques sin un "sí" explícito suyo para ese video exacto.**
   - Ajustes fijos: Reel normal (sin Trial) y sin etiqueta de IA (omitir `isAiGenerated`; lo eligió Efrén).
9. **Publicar a las 19:00 CDMX:**
   - Si aprueba antes, programa `send_later` para esa hora en la misma sesión. Si ya pasó la hora, publica en cuanto apruebe.
   - `vidiq_instagram_publish_reel` con platformAccountId `39432107649769379`, `videoUrl` y `caption`. Si la URL caducó, renuévala con `vidiq_video_upload uploadId=…`.
   - Continúa con `containerId`/`mcpJobId` hasta `PUBLISHED`.
10. **Registrar** en `publicados.md`: fecha, tipo (diario o extra), tema, gancho, duración y permalink. Haz commit y push.

**Texto del reel:** una pregunta-gancho, una línea de valor, la invitación ("Guárdalo y compártelo con alguien que…") y de 3 a 5 hashtags (#curiosidades #ciencia #mexico #menteenorbita + uno del tema).

## 3b. Videos extra (pedidos por Efrén)
Efrén a veces pide en el chat videos fuera de lo programado, por ejemplo para contestar un comentario o probar una idea suya.
- **No alteran lo programado.** El video diario de las 4:35 pm se hace igual, y la cola de `estrategia.md` no se reordena por un extra. Solo si el extra cubre la idea #1, esa idea sale de la cola.
- **Mismo pipeline y misma calidad** (pasos 1–8), con la misma aprobación obligatoria.
- **Hora:** se publica cuando Efrén lo apruebe. Si no da hora, sugiere una que quede al menos 3 h antes o después del reel diario de las 19:00 (por ejemplo 13:00 o 15:00), para que no compitan entre sí.
- Se registra en `publicados.md` con tipo **extra**. Los reels que Efrén sube por su cuenta no se anotan; todo reel de la cuenta que no esté en `publicados.md` es suyo.
- **Todos cuentan para las estadísticas** (diarios, extra y los suyos): el estratega los analiza igual y aprende de ellos.

## 4. Créditos y límites
- **ElevenLabs:** unos 900 créditos por video. Si responde 429 o falta cuota, avísale a Efrén.
  - Plan B automático: voz gratis Chatterbox (MIT) con el workflow `voz_hq`. Crea `tts_hq/narr_TEMA.json` con `{"text_file": "guiones/…_voz.txt", "ref": "ald", "exaggeration": 0.6, "cfg": 0.45}`, haz push y espera `inbox/narr_TEMA.mp3` (en CPU tarda 15–40 min).
  - Plan C: Efrén descarga el mp3 desde ElevenLabs y lo manda al chat.
- **vidIQ:** 150 créditos renovables al mes. `vidiq_video_upload` y `vidiq_instagram_publish_reel` cuestan 0. No uses `vidiq_compose` ni `vidiq_voiceover_generate` (gastan créditos).
- **Red:** solo GitHub y registros de paquetes. Para cualquier descarga externa usa el workflow `fetch`.
