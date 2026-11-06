# Estilo nuevo de Mente en órbita (reset del 3-nov-2026)

Este archivo **manda sobre todo lo visual y sobre los ganchos**. Si CLAUDE.md, estrategia.md o una skill dicen otra cosa del formato viejo (estudio azul, paleta violeta, escáner de anillo, tema `orbita`), gana este archivo.

Referencias que dio Efrén:
- **Transiciones, animaciones y espacio:** el perfil de Instagram @alyxianews. Se copia el lenguaje, **nunca sus objetos ni sus temas tal cual**.
- **Cómo se ven los objetos:** el reel del gancho del metro (instagram.com/reel/Dege5ORIPxv).
- **Efectos de edición:** el reel de @annderrey «10 efectos de video que le pides a Claude» (instagram.com/reel/DfDq7v-JTnl). Se omiten los que dependen de una persona o un avatar.

Prueba aprobable: `kit/nuevo/demo_estilo.py` (12.9 s). Motor: `kit/nuevo/motor2.py`. Sonidos: `kit/nuevo/sfx_demo.py`.

## Decisiones fijas (3-nov-2026)
- **Fondo negro** en todo el video. El blanco solo como destello o sección sorpresa de 2-3 s a mitad del video.
- **Voz: Isaac** (ElevenLabs, voice_id `QmPfzE500cXXHM9uQKGc`, modelo `eleven_v4`; desde el 3-nov-2026): hombre joven, cálido y amigable, habla español con tono cercano. Se cambió Silverio por Isaac a petición de Efrén: Silverio es la voz mexicana más usada en ElevenLabs y hacía sonar al canal como «otra cuenta genérica». Isaac conserva lo mismo (joven, amigable, entretenido, da confianza y curiosidad) y es mucho menos usada que Silverio. Tono: amigo que te cuenta algo sorprendente, con energía pero sin gritar. Etiquetas útiles: `[curious]` en el gancho, `[excited]` en el dato fuerte, `[whispering]` para un secreto.
- **Nombre:** «Mente en órbita». **Foto de perfil:** `marca/perfil_mente_en_orbita.png` (órbita blanca con brillo y un punto cian sobre negro, sin texto).

---

## 1. Espacio y transiciones (lenguaje de @alyxianews)
- **Fondo negro** casi puro con un foco suave al centro, **viñeta**, **grano de película** (~4 %) y **partículas desenfocadas** (bokeh) que suben despacio.
- Elementos de apoyo en **line-art blanco que brilla**: esferas de alambre, líneas de campo, nodos luminosos, redes, pisos de puntos o de rayas en perspectiva, haces de luz que bajan como foco de escenario.
- **Bloom de 2 pasos** (radio chico intenso + radio grande difuso) en todo lo que emite luz.
- **Profundidad de campo:** lo principal nítido; fondo y partículas desenfocados. Al cambiar de escala, la cámara «enfoca» el siguiente detalle.
- **Cámara siempre en movimiento y con golpes rápidos** (ver §11): órbitas de 30–90° en ~0.6 s, crash zoom, punch-in y sacudida en los impactos. Nunca un cuadro quieto más de 1.5 s.
- **Ritmo:** un cambio visual cada **2 a 3 s** (en su reel más visto el plano dura 1.8–2.5 s en promedio).
- **Revelación tipo zoom fractal:** de lo que tienes en la mano → a lo que hay adentro → a la pieza más pequeña → a la escala del planeta (o al revés).
- **Paleta:** blanco y negro. **Color solo en el objeto real** (con sus colores verdaderos) y **un acento cian** para rayos X, cotas y la caja del subtítulo.

### Catálogo de transiciones (usar 5 o más distintas por video, nunca la misma dos veces seguidas, y que la primera transición cambie en cada video)
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
| **Falla digital** `glitch` (RGB separado + franjas) | 0.25 s | Mito, dato falso, «error», algo que se rompe | ráfaga + ticks |
| **Giro con zoom** `giro` (rota 70° y entra la otra girando) | 0.3 s | Dar la vuelta a una idea, «al revés», cambio de punto de vista | whoosh + golpe |
| **Iris** `iris` (círculo de luz que se abre desde un punto) | 0.3 s | Revelar algo que salió de un punto (gota, chip, foco, planeta) | brillo + campanita |
| **Deslizamiento** `deslizar` / `deslizar_abajo` con desenfoque | 0.25 s | Listas, «y además…», subir/bajar de piso | swish |
| **Golpe de cámara** `golpe` (crash zoom y corte seco con rebote) | 0.25 s | Dato que impacta, número grande, «¡y aquí está el truco!» | whoosh + bajo |

### Transiciones CREATIVAS (6-nov-2026: Efrén notó que las transiciones ya no eran tan creativas) — 3 o más distintas en cada reel
| Transición | Duración | Cuándo | Sonido |
|---|---|---|---|
| **Cubo 3D** `cubo` / `cubo_izq` (la escena es una cara de un cubo que gira y la siguiente llega en la otra cara) | 0.35 s | «Del otro lado…», comparar, pasar al siguiente paso | whoosh grave + golpe |
| **Se rompe** `rompe` (grietas desde un punto y la pantalla estalla en pedazos de cristal que vuelan hacia ti) | 0.38 s | Mito que se rompe, «error», «no es lo que crees», segundo gancho | cristal que se rompe + golpe sub |
| **Rebanadas** `rebanadas` (franjas que salen disparadas a los lados en cascada) | 0.32 s | Listas, «y además…», cambio de capa | 4 swishes + bajo |
| **Atraviesa la letra** `cristal` (cae la palabra de cristal gigante, por sus letras se ve la escena siguiente y la cámara atraviesa una letra) | 0.5 s | Entrar a la palabra clave: «PANTALLA», «CALOR», «LITIO» (pon `palabra='…'` en la escena) | brillo cristalino + whoosh |
| **Mosaico digital** `mosaico` (bloques que se voltean en oleada a la escena nueva) | 0.28 s | Pantallas, datos, internet, «tu celular calcula…» | ticks digitales |
| **Remolino** `remolino` (la imagen se tuerce en espiral y la nueva sale destorciéndose) | 0.32 s | Mareo, giro, tiempo, «en un instante», agua, aire | whoosh + riser |

**Sin plantilla:** cada reel arma su propia secuencia. `montaje.py` no deja renderizar si la primera transición es la del reel anterior, si una racha de 3 transiciones seguidas es igual a la de alguno de los últimos 6 reels de `inicios.md` (pasaba: «golpe → deslizar → whip» salió igual en 3 reels seguidos), si una transición se usa más de 3 veces o si hay menos de 8 distintas (5 en reels de menos de 14 cambios). Además de las del catálogo, al menos 2 veces por reel la transición la hace **el objeto mismo** (la cámara entra por la pantalla, la gota se vuelve el planeta, el chip se abre y es la ciudad): eso no lo revisa el código, lo revisas tú en la hoja.

Funciones listas en `motor2.py`: `tr_zoom_through`, `tr_flash`, `push_in`, `tr_whip`, `tr_wipe_v`, `tr_glitch`, `tr_giro`, `tr_iris`, `tr_deslizar`, `tr_golpe`, `tr_cubo`, `tr_rebanadas`, `tr_rompe`, `tr_mosaico`, `tr_remolino`, `tr_cristal`, `radial_blur`, `dir_blur`, `scale_about`. En `montaje.py` se piden con `tr=` en cada escena: whip, whip_izq, zoom, flash, wipe, push, corte, ritmo, glitch, giro, iris, deslizar, deslizar_abajo, golpe, cubo, cubo_izq, rebanadas, rompe, mosaico, remolino, cristal. Muestra de todas las nuevas: `kit/nuevo/demo_cristal.py`.

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
| 03 | **Letras de cristal** (OBLIGATORIO, ver §4b) | Palabra clave GIGANTE que llena el ancho, detrás del objeto, de cristal (`cristal`) | brillo cristalino |
| 06 | **Muro de titulares / foto que cae** | Fotos reales o titulares que caen y se pegan con balanceo (`photo_card`) | golpe de papel |
| 07 | **Celular con vida** | Celular 3D girando con su pantalla animada (app, scroll) | whoosh de giro + clic |
| 08 | **Gráfico que crece** | Barras que suben una por una y línea punteada con nodos (`chart_grow`) | campanitas ascendentes |
| 09 | **Garabatos vivos** | Círculos y flechas a mano que «hierven» a 10 cps alrededor de la pieza (`doodle_circle`, `doodle_arrow`) | lápiz rayando |
| 10 | **Zoom digital** | Saltos x1.0 → x1.3 → x1.8 sobre el detalle con marco REC (`rec_frame`) | clics de cámara |

**Omitidos** porque dependen de una persona o avatar: 01 Rompe el marco (cabeza que sale del cuadro), 04 Órbita alrededor de la cabeza, 05 Interfaces flotantes alrededor del presentador. No se usan caras, avatares ni presentadores.

### 4b. Letras de cristal GIGANTES en cada reel (pedido de Efrén, 6-nov-2026)
Efrén notó que ya no salían: en los reels del 4 al 6-nov eran de 230–330 px, casi transparentes y tapadas por el objeto, y en los últimos ni aparecían. Desde ahora:
- **Función:** `M.cristal(fr.base, fr.fx, 'PALABRA', u, t0=…, cy=…)` **antes de `draw_objects`**, para que quede detrás del objeto. Llena el 94 % del ancho (máximo 42 % del alto), refracta el fondo, tiene bisel redondeado con luz arriba-izquierda, filo que brilla, tinte cian de prisma y un destello que la recorre al entrar y cada 3.2 s. Se empuja despacio (nunca está quieta).
- **Entradas:** `entrada='golpe'` (cae desde grande y desenfocada), `'sube'` (letra por letra desde abajo) o `'zoom'` (crece con rebote). Cámbiala entre escenas.
- **Cuántas:** en **3 o más escenas** de cada reel (2 si tiene menos de 10 escenas) y **una en los primeros 6 s** (en el gancho, con `t0 ≤ −0.3` para que ya esté en el primer cuadro y en el loop). La transición `cristal` cuenta como una.
- **Qué palabra:** UNA palabra clave corta y en mayúsculas (o una cifra: «100%», «7.4», «−18 °C»), la que el espectador debe recordar de esa frase. Nunca la misma palabra dos veces en un reel.
- **Que se lea:** el objeto tapa como máximo la mitad de la palabra; si la tapa más, súbela o bájala con `cy` (0.3–0.55). El objeto va delante: así se ve la profundidad.
- `montaje.py` lo revisa solo: si falta, `hoja` imprime ERROR y `render` no arranca. Al mezclar, cada palabra de cristal suena con su brillo cristalino.
- `glass_type` queda solo para etiquetas chicas; **no cuenta** como el efecto 03.

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

**Fórmula del guion (de los reels de referencia que se hicieron virales):**
1. 0–2 s: contradicción sobre algo que tienes («No tapan el ruido. *Lo borran.*» · «¿Por qué el gancho del metro está suelto? No, no está roto»).
2. 2–8 s: prometes la respuesta y das el primer dato en pantalla.
3. La prueba: dos casos lado a lado (empujar vs. jalar, con vs. sin), mostrados, no contados.
4. Zoom: del objeto → a su interior → a la pieza más pequeña (o al revés, a escala planeta).
5. 20–30 s: el error («si haces esto, lo arruinas») = segundo gancho.
6. Cierre: «Mándaselo a…» y la última imagen igual a la primera (loop).

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
| 0–2 s | Gancho: objeto real + título de 2 líneas + etiqueta técnica | **Letras de cristal gigantes** detrás del objeto, celular con vida, golpe grave |
| 2–12 s | Contexto: por qué te importa, con foto real si existe | Atraviesa la escena, foto que cae |
| 12–25 s | Por dentro: rayos X de cristal, pieza nombrada | Destello, pastillas, garabato, zoom digital |
| 25–30 s | **Segundo gancho** (error, dato que se dispara, escala) | `rompe` o `cristal`, acercamiento exponencial, contador, letras de cristal con la cifra |
| 30–55 s | Explicación por capas (zoom fractal) | Gráfico que crece, barridos, cortinillas |
| 55–65 s | Cierre: invitación a compartir con alguien concreto + pregunta | Cortes rítmicos |
| Final | Última imagen = primera imagen (loop) | Riser que regresa al inicio |

## 9. Lista de revisión antes de mandar a Efrén
- [ ] Gancho de 3 a 7 palabras con «tú/tu», sin intro, imagen más fuerte en el primer cuadro.
- [ ] `hoja` sin ningún ERROR: 8+ transiciones distintas con 3+ creativas, sin plantilla repetida de reels anteriores, y letras de cristal gigantes en 3+ escenas (una en los primeros 6 s).
- [ ] 4+ efectos de la sección 4 (el 03, letras de cristal, siempre) y 2+ transiciones hechas con el objeto mismo.
- [ ] **Inicio de un tipo distinto** a los últimos 6 de `inicios.md` (§12) y anotado ahí; la escena 0 funciona con u negativo (loop).
- [ ] Cada escena tiene contenido visible desde su primer cuadro y al menos un movimiento rápido de cámara u objeto (§11).
- [ ] Ningún efecto con persona o avatar.
- [ ] Cada cambio visual tiene sonido; sin silencios de más de 1.5 s; el audio llega al final.
- [ ] Fotos reales solo de fuentes permitidas, con crédito.
- [ ] Datos verificados con fuente actual; las cifras de ejemplo dicen «EJEMPLO».
- [ ] Segundo gancho entre 25 y 30 s; final en loop.
- [ ] Hoja de contacto revisada (texto legible, nada cortado fuera de los zooms digitales).

## 10. Portada (miniatura) de cada video — perfil limpio y ordenado
- **Mismo diseño siempre** (`kit/nuevo/portada.py`): cuadro del gancho oscurecido, categoría en mono cian arriba (y=300), título en 2 líneas (sans blanca + serif itálica) en el mismo lugar, y la firma «● MENTE EN ÓRBITA» abajo (y=1600). Nada de flechas, emojis ni colores extra: la cuadrícula se ve ordenada porque todas las portadas son iguales salvo el objeto y el título.
- Todo lo importante va dentro del recorte 3:4 de la cuadrícula de Instagram y TikTok (y de 240 a 1680 en 1080×1920).
- Título: el gancho en 2 partes de máximo ~22 caracteres cada una (p. ej. «Tu celular sabe» / «dónde está el norte»).
- Categorías fijas: TECNOLOGÍA, ESPACIO, CUERPO, PLANETA, MÉXICO, o el nombre de la serie (LO QUE NO VES, DUELO, ¿QUÉ PASARÍA SI…?, MITO O REALIDAD, RESPUESTAS).
- Se manda a Metricool como `videoThumbnailUrl` (Instagram, Facebook, YouTube y TikTok si la cuenta es de empresa) y además va como cuadro 0 del video, por si alguna red la ignora.
- Videos largos de YouTube: miniatura 1280×720 con el mismo lenguaje (skill `yt-empaquetador`).

## 11. Ritmo y movimiento: más rápido y más creativo (pedido de Efrén, 4-nov-2026)
Efrén quiere transiciones y movimientos de objetos y de cámara **más creativos y más rápidos**. Reglas para cada escena:
- **Nada aparece «solo»:** cada objeto entra con movimiento en **0.12–0.3 s**: cae y rebota, hace «pop» con resorte, llega girando o entra deslizándose (`piezas.entrada(u, u0, dur, modo)` con modo `cae`, `pop`, `gira`, `desliza`). Prohibido el desvanecido lento de más de 0.4 s.
- **Contenido desde el primer cuadro:** como las transiciones duran 0.25 s, la escena nueva debe tener algo visible desde u = 0 (si no, la transición deja ver negro). Lo que va entrando, que entre rápido.
- **Cámara con golpes, no paneos lentos:** cada escena tiene al menos **un movimiento rápido** (órbita de 30–90° en ~0.6 s, crash zoom, punch-in de x1 a x1.6, paso lateral) y luego se queda casi quieta con deriva suave. `piezas.cam_rapida(u, claves)` hace exactamente eso (salta en el primer 35 % del tramo con ease-out cuártico y descansa).
- **Impactos con sacudida:** cuando algo cae, choca o aparece un número grande, sacude la cámara 0.3 s (`piezas.sacudida(t, t0=…)` + `piezas.mover_img`) con su golpe grave.
- **Curvas con personalidad:** `piezas.rebote`, `piezas.resorte` (se pasa un poco y regresa) y `piezas.eout4` (arranca muy rápido y frena) en lugar de rampas lineales.
- **Vista explotada** para explicar piezas: `piezas.despiece(mallas, k, centro, fuerza, giro)` separa las partes y las vuelve a armar.
- **Transiciones:** 0.25–0.38 s (las de §1; `cristal` dura 0.5 s). Elige la transición por lo que dice la frase (mito → `rompe` o `glitch`, número que impacta → `golpe`, lista → `rebanadas` o `deslizar`, sale de un punto → `iris`, cambio de punto de vista → `cubo` o `giro`, pantallas y datos → `mosaico`, palabra clave → `cristal`), nunca por costumbre ni copiando el orden de otro reel.
- Cada escena dura **1.8–3 s**; si una frase es larga, pártela en 2 escenas con un movimiento de cámara distinto.

## 12. Inicios: uno distinto en cada video
El inicio decide si la gente se queda. **Cada video abre con un tipo de inicio diferente**: nunca uno de los usados en los **últimos 6 videos** (registro en `inicios.md`, con fecha, tema, tipo y primera transición). El final sigue igual: la última imagen y la última frase regresan al primer cuadro sin aviso (loop), así que **la escena 0 debe verse bien con u negativo** (el final la reproduce antes de tiempo).

Catálogo de inicios (combina con el gancho de 3-7 palabras; el título de 2 líneas entra con golpe, no fijo desde el cuadro 0):
1. **Caída desde el espacio:** la Tierra de alambre → crash zoom a México → a una casa → al objeto, en 1.5 s, con el título al aterrizar.
2. **El objeto cae y rebota** desde arriba del cuadro, sacudida y título que se estrella con golpe grave.
3. **Se arma solo:** vista explotada que se junta en 1 s (`despiece` de 1 a 0) y hace clic.
4. **Barra de búsqueda:** el cursor escribe la pregunta del gancho letra por letra, Enter y la cámara atraviesa la pantalla.
5. **Número gigante:** una cifra enorme golpea la pantalla (contador que se detiene de golpe) y luego se revela de qué es.
6. **Pantalla dividida antes/después:** dos mitades que chocan o se deslizan (con / sin, mito / realidad).
7. **Macro extremo que se aleja:** empieza en una textura irreconocible (pieza, fibra, gota) y un zoom hacia atrás revela el objeto.
8. **Error en pantalla:** glitch, aviso rojo «ERROR» o la pieza fallando (el problema primero, la explicación después).
9. **Giro 360° con destellos:** el objeto da una vuelta completa rapidísima con 3 cortes rítmicos y queda de frente al título.
10. **Rayos X de golpe:** el objeto normal y en el primer golpe de sonido se vuelve de cristal y se ve por dentro.
11. **Pregunta directa en primera persona:** texto grande «¿Tú también…?» que se rompe en pedazos y deja ver el objeto.
12. **Cuenta regresiva o reloj:** 3-2-1 o una manecilla que corre y se congela en el dato.
13. **Objeto al centro con título** (el clásico de los primeros reels): máximo 1 de cada 7 videos.

También cambia la **primera transición** (la de la escena 0 a la 1): no la misma que en el video anterior.

## Fuentes de la investigación
- Análisis de los 3 reels de referencia y de los 12 reels más recientes de @alyxianews (3-nov-2026).
- Hooks y primeros 3 s: kineclip.com/blog/how-to-write-viral-hooks-short-form-2026 · hansencommerce.com/insights-tiktok-hook-3-seconds · perceedigital.com/insights/video-hooks-that-convert
- Benchmarks de retención: grow-it.se/en/resources/short-form-video-retention-benchmarks · upgrow.com/blog/instagram-reels-statistics-2026-views-watch-time-reach-engagement · influencermarketinghub.com/instagram-reels-stats
- Curiosidad (Loewenstein, 1994): billdenton.substack.com/p/the-information-gap
- Ritmo y sonido: fluxnote.io/guides/faceless-shorts-retention-tips-2026 · livecounts.io/blog/youtube/how-mrbeast-uses-pattern-interrupts-every-4-seconds · socialync.io/blog/retention-techniques-keep-viewers-watching-2026
- Loops: virvid.ai/blog/looping-structure-shorts-retention-2026
- Nichos: improvado.io/blog/social-media-benchmarking · facelesschannel.com/guides/best-faceless-youtube-niches
- Licencias: commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia · nasa.gov/multimedia/guidelines
