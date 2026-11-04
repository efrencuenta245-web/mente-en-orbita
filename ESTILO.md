# Estilo nuevo de Mente en órbita (reset del 3-nov-2026)

Este archivo **manda sobre todo lo visual y sobre los ganchos**. Si CLAUDE.md, estrategia.md o una skill dicen otra cosa del formato viejo (estudio azul, paleta violeta, escáner de anillo, tema `orbita`), gana este archivo.

Referencias que dio Efrén:
- **Transiciones, animaciones y espacio:** el perfil de Instagram @alyxianews. Se copia el lenguaje, **nunca sus objetos ni sus temas tal cual**.
- **Cómo se ven los objetos:** el reel del gancho del metro (instagram.com/reel/Dege5ORIPxv).
- **Efectos de edición:** el reel de @annderrey «10 efectos de video que le pides a Claude» (instagram.com/reel/DfDq7v-JTnl). Se omiten los que dependen de una persona o un avatar.

Prueba aprobable: `kit/nuevo/demo_estilo.py` (12.9 s). Motor: `kit/nuevo/motor2.py`. Sonidos: `kit/nuevo/sfx_demo.py`.

---

## 1. Espacio y transiciones (lenguaje de @alyxianews)
- **Fondo negro** casi puro con un foco suave al centro, **viñeta**, **grano de película** (~4 %) y **partículas desenfocadas** (bokeh) que suben despacio.
- Elementos de apoyo en **line-art blanco que brilla**: esferas de alambre, líneas de campo, nodos luminosos, redes, pisos de puntos o de rayas en perspectiva, haces de luz que bajan como foco de escenario.
- **Bloom de 2 pasos** (radio chico intenso + radio grande difuso) en todo lo que emite luz.
- **Profundidad de campo:** lo principal nítido; fondo y partículas desenfocados. Al cambiar de escala, la cámara «enfoca» el siguiente detalle.
- **Cámara siempre en movimiento:** dolly hacia adentro/afuera y órbita leve (±15°). Nunca un cuadro quieto más de 2 s.
- **Ritmo:** un cambio visual cada **2 a 3 s** (en su reel más visto el plano dura 1.8–2.5 s en promedio).
- **Revelación tipo zoom fractal:** de lo que tienes en la mano → a lo que hay adentro → a la pieza más pequeña → a la escala del planeta (o al revés).
- **Paleta:** blanco y negro. **Color solo en el objeto real** (con sus colores verdaderos) y **un acento cian** para rayos X, cotas y la caja del subtítulo.

### Catálogo de transiciones (usar 4 o más distintas por video)
| Transición | Duración | Cuándo | Sonido |
|---|---|---|---|
| **Atraviesa la escena** (zoom-through + desenfoque radial) | 0.35 s | Entrar a algo: una pantalla, un hueco, una letra «O» | whoosh que acelera |
| **Destello de sobreexposición** (todo se quema a blanco) | 0.4 s | Cambio de tema o de escala grande | ráfaga de ruido blanco + glitch |
| **Acercamiento exponencial** con desenfoque | 0.5 s | Ir a un detalle (chip, célula, pieza) | whoosh + golpe grave |
| **Barrido rápido** con desenfoque de movimiento | 0.15–0.2 s | Comparar dos cosas, «mientras tanto…» | swish corto |
| **Cortinilla vertical** con línea de luz | 0.3 s | Antes/después, arriba/abajo | golpe sordo |
| **Vuelo de cámara** hacia arriba o hacia abajo | 0.6 s | Cambiar de piso, subir a la atmósfera | riser |
| **Cortes rítmicos** de 0.15 s con flash de bloom | 2–4 cortes | Montaje final o lista rápida | golpes de bajo sincopados |
| **Morph** (una forma se convierte en otra) | 0.4 s | Explicar que A «es» B | barrido suave |

Funciones listas en `motor2.py`: `tr_zoom_through`, `tr_flash`, `push_in`, `tr_whip`, `tr_wipe_v`, `radial_blur`, `dir_blur`, `scale_about`.

## 2. Cómo se ven los objetos (referencia del metro)
- **Semirrealistas, no caricatura:** materiales reales (metal satinado, latón brillante, plástico mate, madera con veta, concreto rugoso, vidrio).
- **Luz:** principal suave desde arriba-izquierda, relleno tenue y **luz de borde** que separa el objeto del fondo negro; brillo especular en lo metálico y oscurecido en contactos y ranuras.
- **Colores reales** del objeto (cinta amarilla, remaches dorados, mangos rojos). Lo demás en blanco y negro.
- **Rayos X de cristal:** el cuerpo se vuelve casi transparente con **bordes cian que brillan** y se ve el interior en color. Sustituye al anillo escáner viejo.
- **Vistas técnicas:** isométrica, lateral ortográfica y corte transversal; cotas amarillas o cian, planos semitransparentes y el «0» o la medida flotando.
- **Escenario del error:** muestra qué pasa si se hace mal (la pieza se pone roja y falla). Funciona como segundo gancho.
- Mallas con suficientes caras (esferas de 28+ segmentos, cantos redondeados) y detalles reales (pines, tornillos, texturas).
- Funciones: `draw_objects(fr, mallas, xray=k, keep=('in',))`, `shade()`, `named()`.

## 3. Texto en pantalla
- **Título del gancho en 2 líneas:** primera en **sans negrita** (Inter Bold) y segunda en **serif itálica** (Lora Italic). Corto y con contraste: «No tapan el ruido. / *Lo borran.*». Entra con desenfoque y subida (`title()`).
- **Etiqueta técnica pequeña** en monoespaciada con letras separadas, arriba del título: «MAGNETÓMETRO · 3 EJES» (`kicker()`).
- **Subtítulos palabra por palabra** en el tercio inferior: palabra activa en blanco dentro de una **caja de selección cian con anclas** (estilo interfaz); las dichas en gris (`word_caption()`).
- **Pastillas** con borde y punto para nombrar piezas, con línea guía al objeto (`pill()`).
- Números con **contador que sube** en monoespaciada.
- Etiquetas honestas cuando aplique: «EJEMPLO», «Recreación», «Escala exagerada».

## 4. Efectos obligatorios (video de @annderrey, sin persona)
En **cada video** van al menos 4 de estos, cada uno con su sonido:
| # | Efecto | Cómo se usa aquí | Sonido |
|---|---|---|---|
| 02 | **Atraviesa la escena** | La cámara entra por la pantalla, una «O» o un hueco del objeto | whoosh |
| 03 | **Letras de cristal** | Palabra clave gigante detrás del objeto, casi transparente, con bisel que brilla (`glass_type`) | brillo cristalino |
| 06 | **Muro de titulares / foto que cae** | Fotos reales o titulares que caen y se pegan con balanceo (`photo_card`) | golpe de papel |
| 07 | **Celular con vida** | Celular 3D girando con su pantalla animada (app, scroll) | whoosh de giro + clic |
| 08 | **Gráfico que crece** | Barras que suben una por una y línea punteada con nodos (`chart_grow`) | campanitas ascendentes |
| 09 | **Garabatos vivos** | Círculos y flechas a mano que «hierven» a 10 cps alrededor de la pieza (`doodle_circle`, `doodle_arrow`) | lápiz rayando |
| 10 | **Zoom digital** | Saltos x1.0 → x1.3 → x1.8 sobre el detalle con marco REC (`rec_frame`) | clics de cámara |

**Omitidos** porque dependen de una persona o avatar: 01 Rompe el marco (cabeza que sale del cuadro), 04 Órbita alrededor de la cabeza, 05 Interfaces flotantes alrededor del presentador. No se usan caras, avatares ni presentadores.

## 5. Sonido
- **Cada cambio visual lleva un sonido** (corte, texto que aparece, zoom, etiqueta, barra). Ninguna transición muda.
- Mapa base: golpe grave + riser al abrir · whoosh en cada «atraviesa» · ráfaga de ruido en cada destello · tick suave por palabra clave · golpe de papel cuando cae una foto · lápiz en los garabatos · clics en el zoom digital · campanitas en las gráficas · golpes de bajo en los cortes rítmicos · riser al final que regresa al inicio (loop).
- Todos los sonidos se sintetizan por código (`sfx_demo.py`): cero derechos de terceros.
- **Música de fondo** electrónica suave (`musica.py`, semilla y BPM nuevos en cada video) que baja cuando habla la voz (`mix_musica.sh`).
- **Nunca más de 1.5 s de silencio**, y el audio dura hasta el último cuadro.

## 6. Imágenes reales de internet
Cuando el video hable de algo que existe (un lugar, un objeto, un planeta, un fenómeno), se busca una foto real y se mete con el efecto de foto que cae o como tarjeta.
- **Fuentes permitidas:** NASA y otras agencias de gobierno de EE. UU. (dominio público), Wikimedia Commons con licencia **dominio público, CC0 o CC BY**. Evitar CC BY-NC, CC BY-ND y CC BY-SA (no sirven para videos monetizados o obligan a cambiar la licencia del video).
- **Nunca:** fotos de personas identificables, logos o insignias de marcas o agencias, ni imágenes de bancos de pago, Google Imágenes o redes sociales.
- **Crédito** en la tarjeta («NASA · APOLLO 17 · 1972») y en la descripción del post. La fuente y la licencia se anotan en `guiones/AAAA-MM-DD_tema.txt`.
- **Descarga:** como aquí no hay internet directo, escribe la URL en `jobs/img_NOMBRE.jpg.url`, haz push y el workflow `fetch` la deja en `inbox/` en 1–2 min.

## 7. Ganchos, nichos y retención (investigación sin vidIQ, 3-nov-2026)
**Lo que más ve la gente en este formato.** En @alyxianews ganan los temas de **la tecnología que tienes en la mano explicada por dentro**: «Así piensa ChatGPT» (956 K), entrenamiento de IA (468 K), la batería en tu mochila (420 K), SpaceX (320 K) y «Tu pantalla no te siente» (235 K). Los temas de empresa sin conexión con tu vida (ASML, 31 K) rinden mucho menos. En nuestros datos, el espacio retiene más (50–54 % visto) y la tecnología de todos los días se comparte más (fibra óptica: 25.6 compartidos por cada 1 000). La educación es el sector con más interacción en TikTok.

**Nichos que se priorizan:**
1. Tecnología e IA de todos los días por dentro (celular, ChatGPT, baterías, Wi-Fi, pantallas, apps).
2. Objetos de la casa + física (estufa, microondas, metro, refrigerador).
3. Espacio y satélites con conexión a tu vida (GPS, Starlink, el clima).
4. Noticia de tecnología o ciencia del momento explicada en 1 minuto, siempre conectada con tu vida (tipo «La otra cara de SpaceX», 320 K).

**Por qué funciona el gancho.** Abre un **hueco de curiosidad** (teoría de Loewenstein): muestra que hay algo que no sabes sobre algo que sí conoces, y el cerebro quiere cerrarlo. Los ganchos de la referencia son 2 líneas cortas que **contradicen lo que crees**: «No tapan el ruido. *Lo borran.*», «Tu pantalla *no te siente.*», «Boca abajo. *y no se cae*», «Así piensa *ChatGPT.*».

**Fórmula del gancho (0–2 s):** objeto que tienes + giro inesperado, en 3 a 7 palabras, con **«tú/tu»**, la imagen más llamativa del video en el primer cuadro y el sonido de golpe. Nada de logo, saludo ni título de canal al inicio.

**Cómo pasar del 50 % hasta el final.** Como referencia, el 20 % de mejores videos cortos retiene 60–70 % a los 3 s y 45–55 % a la mitad; en Reels de 30–60 s lo normal para educación es 40–50 % de visto completo. Para superarlo:
1. **Bucle abierto** en el gancho que se cierra hasta el final; mientras, se abren y cierran preguntas pequeñas.
2. **Cambio visual cada 2–3 s** con sonido.
3. **Segundo gancho a los 25–30 s:** el error, el dato que se dispara, el cambio de escala.
4. **Que no se sienta el final:** no cerrar con «gracias por ver»; la última frase y la última imagen enganchan con la primera (**loop**). Las repeticiones cuentan y suben el % visto.
5. Duración: **61–75 s** (TikTok solo paga más de 1 min; los videos de @alyxianews duran 69–104 s).

## 8. Estructura de cada video (61–75 s)
| Tiempo | Qué pasa | Efectos y transición |
|---|---|---|
| 0–2 s | Gancho: objeto real + título de 2 líneas + etiqueta técnica | Letras de cristal, celular con vida, golpe grave |
| 2–12 s | Contexto: por qué te importa, con foto real si existe | Atraviesa la escena, foto que cae |
| 12–25 s | Por dentro: rayos X de cristal, pieza nombrada | Destello, pastillas, garabato, zoom digital |
| 25–30 s | **Segundo gancho** (error, dato que se dispara, escala) | Acercamiento exponencial, contador |
| 30–55 s | Explicación por capas (zoom fractal) | Gráfico que crece, barridos, cortinillas |
| 55–65 s | Cierre: invitación a compartir con alguien concreto + pregunta | Cortes rítmicos |
| Final | Última imagen = primera imagen (loop) | Riser que regresa al inicio |

## 9. Lista de revisión antes de mandar a Efrén
- [ ] Gancho de 3 a 7 palabras con «tú/tu», sin intro, imagen más fuerte en el primer cuadro.
- [ ] 4+ transiciones distintas del catálogo y 4+ efectos de la sección 4.
- [ ] Ningún efecto con persona o avatar.
- [ ] Cada cambio visual tiene sonido; sin silencios de más de 1.5 s; el audio llega al final.
- [ ] Fotos reales solo de fuentes permitidas, con crédito.
- [ ] Datos verificados con fuente actual; las cifras de ejemplo dicen «EJEMPLO».
- [ ] Segundo gancho entre 25 y 30 s; final en loop.
- [ ] Hoja de contacto revisada (texto legible, nada cortado fuera de los zooms digitales).

## Fuentes de la investigación
- Análisis de los 3 reels de referencia y de los 12 reels más recientes de @alyxianews (3-nov-2026).
- Hooks y primeros 3 s: kineclip.com/blog/how-to-write-viral-hooks-short-form-2026 · hansencommerce.com/insights-tiktok-hook-3-seconds · perceedigital.com/insights/video-hooks-that-convert
- Benchmarks de retención: grow-it.se/en/resources/short-form-video-retention-benchmarks · upgrow.com/blog/instagram-reels-statistics-2026-views-watch-time-reach-engagement · influencermarketinghub.com/instagram-reels-stats
- Curiosidad (Loewenstein, 1994): billdenton.substack.com/p/the-information-gap
- Ritmo y sonido: fluxnote.io/guides/faceless-shorts-retention-tips-2026 · livecounts.io/blog/youtube/how-mrbeast-uses-pattern-interrupts-every-4-seconds · socialync.io/blog/retention-techniques-keep-viewers-watching-2026
- Loops: virvid.ai/blog/looping-structure-shorts-retention-2026
- Nichos: improvado.io/blog/social-media-benchmarking · facelesschannel.com/guides/best-faceless-youtube-niches
- Licencias: commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia · nasa.gov/multimedia/guidelines
