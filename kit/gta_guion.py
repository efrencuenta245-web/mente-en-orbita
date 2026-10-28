"""Guion del video largo de YouTube: ¿Por qué GTA 6 tardó tanto? (28-oct-2026).
Cada capítulo es una lista de frases (texto en pantalla con cifras, texto para la voz con letra).
Cada capítulo se narra en un archivo de voz aparte (narr_gta_cN.mp3) para poder recortar reels."""

CAPS = [
    ("gancho", [
        ("Si naciste el día que salió GTA 5, hoy ya estás en secundaria.",
         "Si naciste el día que salió Ge Te A cinco, hoy ya estás en secundaria."),
        ("13 años de espera.", "Trece años de espera."),
        ("Entre GTA 3 y Vice City pasó un año.", "Entre Ge Te A tres y Vice City pasó un año."),
        ("Entre San Andreas y GTA 4, casi 4.", "Entre San Andreas y Ge Te A cuatro, casi cuatro."),
        ("Entre GTA 5 y GTA 6… 13.", "Entre Ge Te A cinco y Ge Te A seis... trece."),
        ("Es la espera más larga de toda la saga.", "Es la espera más larga de toda la saga."),
        ("¿Qué pasó dentro de Rockstar? Hoy lo abrimos por dentro, en 5 razones.",
         "¿Qué pasó dentro de Rockstar? Hoy lo abrimos por dentro, en cinco razones."),
    ]),
    ("razon1", [
        ("Razón 1.", "Razón uno."),
        ("GTA 5 nunca dejó de vender.", "Ge Te A cinco nunca dejó de vender."),
        ("Salió en 2013 para PS3.", "Salió en dos mil trece para PlayStation tres."),
        ("Luego volvió en PS4, en PC y en PS5.", "Luego volvió en PlayStation cuatro, en computadora, y en PlayStation cinco."),
        ("3 generaciones de consolas con el mismo juego.", "Tres generaciones de consolas... con el mismo juego."),
        ("Ya pasó los 230 millones de copias.", "Ya pasó los doscientos treinta millones de copias."),
        ("Si cada copia fuera una caja, la torre subiría unos 2,700 km.",
         "Si cada copia fuera una caja, la torre subiría unos dos mil setecientos kilómetros."),
        ("Casi 7 veces más alto que la Estación Espacial.",
         "Casi siete veces más alto que la Estación Espacial."),
        ("Mientras el 5 pagara las cuentas, el 6 podía esperar.",
         "Mientras el cinco pagara las cuentas... el seis podía esperar."),
    ]),
    ("razon2", [
        ("Razón 2.", "Razón dos."),
        ("Antes del 6, Rockstar tenía otro gigante en la mesa.",
         "Antes del seis, Rockstar tenía otro gigante en la mesa."),
        ("Red Dead Redemption 2, que salió en 2018.", "Red Dead Redemption dos, que salió en dos mil dieciocho."),
        ("Fue un proyecto de unos 7 años, con estudios en varios países.",
         "Fue un proyecto de unos siete años, con estudios en varios países."),
        ("Su jefe de guion contó que su equipo llegó a semanas de 100 horas.",
         "Su jefe de guion contó que su equipo llegó a semanas de cien horas."),
        ("Una semana normal en México es de 48.", "Una semana normal en México es de cuarenta y ocho."),
        ("Mientras el vaquero no saliera, GTA 6 no tenía al estudio completo.",
         "Mientras el vaquero no saliera, Ge Te A seis no tenía al estudio completo."),
    ]),
    ("razon3", [
        ("Razón 3.", "Razón tres."),
        ("Rockstar se cambió por dentro a mitad del camino.",
         "Rockstar se cambió por dentro, a mitad del camino."),
        ("En 2020 se fue Dan Houser, cofundador, y la voz detrás de las historias de GTA.",
         "En dos mil veinte se fue Dan Houser, cofundador, y la voz detrás de las historias de Ge Te A."),
        ("Ese mismo año, la pandemia mandó a medio mundo a trabajar desde casa.",
         "Ese mismo año, la pandemia mandó a medio mundo a trabajar desde casa."),
        ("Según Bloomberg, Rockstar cambió sus reglas: las horas extra se pagan con días libres.",
         "Según Bloomberg, Rockstar cambió sus reglas: las horas extra se pagan con días libres."),
        ("Pasó contratistas a planta y sumó productores para cuidar el calendario.",
         "Pasó contratistas a planta, y sumó productores para cuidar el calendario."),
        ("Menos jornadas de 100 horas: más sano… pero más lento.",
         "Menos jornadas de cien horas: más sano... pero más lento."),
    ]),
    ("razon4", [
        ("Razón 4.", "Razón cuatro."),
        ("Un chico de 17 años hackeó a Rockstar… desde la tele de un hotel.",
         "Un chico de diecisiete años hackeó a Rockstar... desde la tele de un hotel."),
        ("Fue en septiembre de 2022. Estaba bajo vigilancia y sin computadora.",
         "Fue en septiembre de dos mil veintidós. Estaba bajo vigilancia, y sin computadora."),
        ("Usó la tele del cuarto, un Fire Stick y un celular.",
         "Usó la tele del cuarto, un Fire Stick, y un celular."),
        ("Publicó unos 90 videos del juego sin terminar.", "Publicó unos noventa videos del juego sin terminar."),
        ("El mundo vio Vice City y gráficos a medio hacer.", "El mundo vio Vice City... y gráficos a medio hacer."),
        ("Rockstar tuvo que confirmar que eran reales.", "Rockstar tuvo que confirmar que eran reales."),
        ("Calculó el daño en unos 5 millones de dólares, y miles de horas de trabajo.",
         "Calculó el daño en unos cinco millones de dólares, y miles de horas de trabajo."),
        ("Y en 2023, hasta el primer tráiler se filtró: lo tuvieron que publicar antes de tiempo.",
         "Y en dos mil veintitrés, hasta el primer tráiler se filtró: lo tuvieron que publicar antes de tiempo."),
    ]),
    ("razon5", [
        ("Razón 5.", "Razón cinco."),
        ("Lo que tú esperas de él.", "Lo que tú esperas de él."),
        ("El primer tráiler, en diciembre de 2023, tuvo 90 millones de vistas en 24 horas.",
         "El primer tráiler, en diciembre de dos mil veintitrés, tuvo noventa millones de vistas en veinticuatro horas."),
        ("Récord para un video que no es de música.", "Récord para un video que no es de música."),
        ("El juego pasa en Leonida, un estado inspirado en Florida, a un vuelo corto de Cancún.",
         "El juego pasa en Leonida, un estado inspirado en Florida... a un vuelo corto de Cancún."),
        ("Según Bloomberg, el plan original era todavía más grande.",
         "Según Bloomberg, el plan original era todavía más grande."),
        ("Por eso las fechas se movieron: otoño de 2025, luego 26 de mayo de 2026…",
         "Por eso las fechas se movieron: otoño de dos mil veinticinco, luego veintiséis de mayo de dos mil veintiséis..."),
        ("…y ahora el 19 de noviembre de 2026.", "y ahora, el diecinueve de noviembre de dos mil veintiséis."),
        ("La razón oficial: más tiempo para pulirlo al nivel que esperan los jugadores.",
         "La razón oficial: más tiempo para pulirlo al nivel que esperan los jugadores."),
    ]),
    ("cierre", [
        ("Un juego que no dejaba de vender, un vaquero, un estudio nuevo, un hackeo y una ambición gigante.",
         "Un juego que no dejaba de vender, un vaquero, un estudio nuevo, un hackeo, y una ambición gigante."),
        ("El 19 de noviembre sabremos si valió la pena.", "El diecinueve de noviembre sabremos si valió la pena."),
        ("Esto fue Mente en órbita.", "Esto fue Mente en órbita."),
        ("¿Tú crees que valió la pena la espera? Sí o no, en los comentarios.",
         "¿Tú crees que valió la pena la espera? Sí o no, en los comentarios."),
        ("Y si naciste el día que salió GTA 5…", "Y si naciste el día que salió Ge Te A cinco..."),
    ]),
]

# Cierre corto para los reels (se narra aparte)
REEL_OUT = [
    ("Mente en órbita. Las 5 razones completas, en nuestro YouTube.",
     "Mente en órbita. Las cinco razones completas, en nuestro YouTube."),
    ("Mándaselo a tu amigo que sigue esperando GTA 6. ¿Valió la pena? Sí o no.",
     "Mándaselo a tu amigo que sigue esperando Ge Te A seis. ¿Valió la pena? Sí o no."),
]

if __name__ == '__main__':
    tot = 0
    for name, ph in CAPS + [("reel_out", REEL_OUT)]:
        v = " ".join(p[1] for p in ph)
        tot += len(v)
        print(name, len(v), "chars ~", round(len(v) / 14.5, 1), "s")
    print("total", tot)
