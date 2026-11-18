"""Guion del video largo quincenal de YouTube: ¿Qué pasaría si México tuviera tren bala? CDMX–Guadalajara (18-nov-2026).
Estilo nuevo (ESTILO.md, motor2). CAPS: (texto en pantalla con cifras, texto para la voz con letra).
Un mp3 por capítulo: narr_trenbala_cN.mp3 (y narr_trenbala_out.mp3 con los ganchos y cierres de los Shorts).
Las etiquetas de voz ([curious], [excited]) NO van aquí: se agregan solo en el texto que se manda a ElevenLabs (TAGS)."""

CAPS = [
    ("gancho", [
        ("Cuando un tren bala ya te dejó en Guadalajara…",
         "Cuando un tren bala ya te dejó en Guadalajara..."),
        ("…tu camión apenas va llegando a Querétaro.",
         "tu camión apenas va llegando a Querétaro."),
        ("Hoy, de la CDMX a Guadalajara haces unas 7 horas en camión.",
         "Hoy, de la Ciudad de México a Guadalajara haces unas siete horas en camión."),
        ("Un tren bala como el de Japón lo haría en unas 2 horas y media.",
         "Un tren bala como el de Japón lo haría en unas dos horas y media."),
        ("Y si tiembla, detecta el sismo antes del golpe fuerte… y empieza a frenar solo.",
         "Y si tiembla, detecta el sismo antes del golpe fuerte... y empieza a frenar solo."),
        ("¿Qué pasaría si México tuviera uno? Lo armamos en 6 partes.",
         "¿Qué pasaría si México tuviera uno? Lo armamos en seis partes."),
    ]),
    ("viaje", [
        ("Parte 1: el viaje.", "Parte uno: el viaje."),
        ("Si México tuviera tren bala, saldrías de la CDMX a Guadalajara: unos 540 km.",
         "Si México tuviera tren bala, saldrías de la Ciudad de México a Guadalajara: unos quinientos cuarenta kilómetros."),
        ("En auto, sin parar, haces 5 horas y 20 minutos… y pagas 10 casetas.",
         "En auto, sin parar, haces cinco horas y veinte minutos... y pagas diez casetas."),
        ("En camión, unas 7 horas.", "En camión, unas siete horas."),
        ("Ahora mira Japón: el Nozomi va de Tokio a Osaka, 515 km, en 2 horas y 21 minutos.",
         "Ahora mira Japón: el Nozomi va de Tokio a Osaka, quinientos quince kilómetros, en dos horas y veintiún minutos."),
        ("A ese ritmo, Guadalajara te quedaría a unas 2 horas y media.",
         "A ese ritmo, Guadalajara te quedaría a unas dos horas y media."),
        ("Desayunas en la CDMX… y almuerzas una torta ahogada en Guadalajara.",
         "Desayunas en la Ciudad de México... y almuerzas una torta ahogada en Guadalajara."),
        ("Mientras, tu camión apenas va llegando a Querétaro.",
         "Mientras, tu camión apenas va llegando a Querétaro."),
    ]),
    ("sismo", [
        ("Parte 2: cuando tiembla.", "Parte dos: cuando tiembla."),
        ("Un tren bala en México tendría que aguantar sismos, igual que en Japón.",
         "Un tren bala en México tendría que aguantar sismos, igual que en Japón."),
        ("Por eso Japón puso sismógrafos junto a la vía y en la costa.",
         "Por eso Japón puso sismógrafos junto a la vía, y en la costa."),
        ("Cuando empieza un sismo, primero sale una onda rápida y débil: la onda P.",
         "Cuando empieza un sismo, primero sale una onda rápida y débil: la onda Pe."),
        ("Después llega la fuerte: la onda S, la que tira cosas.",
         "Después llega la fuerte: la onda Ese, la que tira cosas."),
        ("El sistema detecta la onda P en un segundo y corta la corriente.",
         "El sistema detecta la onda Pe en un segundo, y corta la corriente."),
        ("Sin corriente, el tren frena solo.",
         "Sin corriente, el tren frena solo."),
        ("En 2011, con el sismo más fuerte en la historia de Japón, cortó la corriente de 12 a 15 segundos antes del golpe fuerte.",
         "En dos mil once, con el sismo más fuerte en la historia de Japón, cortó la corriente de doce a quince segundos antes del golpe fuerte."),
        ("En esa línea iban 19 trenes en marcha. Ninguno se descarriló.",
         "En esa línea iban diecinueve trenes en marcha. Ninguno se descarriló."),
        ("Pero ojo: frenar no es inmediato.", "Pero ojo: frenar no es inmediato."),
        ("A 360 km/h, un tren de pruebas de Japón necesitó unos 4 km para detenerse.",
         "A trescientos sesenta kilómetros por hora, un tren de pruebas de Japón necesitó unos cuatro kilómetros para detenerse."),
        ("Y eso, abriendo unas aletas en el techo, como orejas de gato.",
         "Y eso, abriendo unas aletas en el techo, como orejas de gato."),
        ("En la CDMX, tu alerta sísmica te da unos 60 segundos si el sismo viene de la costa.",
         "En la Ciudad de México, tu alerta sísmica te da unos sesenta segundos si el sismo viene de la costa."),
        ("Al tren bala le basta uno para empezar a frenar.",
         "Al tren bala le basta uno para empezar a frenar."),
        ("¿Y nunca se ha descarrilado? Sí. En 2004, un sismo sacó de la vía 8 de 10 vagones…",
         "¿Y nunca se ha descarrilado? Sí. En dos mil cuatro, un sismo sacó de la vía ocho de diez vagones..."),
        ("…con 154 personas a bordo. Nadie salió herido.",
         "con ciento cincuenta y cuatro personas a bordo. Nadie salió herido."),
        ("En 62 años, ningún pasajero ha muerto por un choque o un descarrilamiento del tren bala.",
         "En sesenta y dos años, ningún pasajero ha muerto por un choque o un descarrilamiento del tren bala."),
    ]),
    ("velocidad", [
        ("Parte 3: el secreto de los 300 km/h.", "Parte tres: el secreto de los trescientos kilómetros por hora."),
        ("Para cruzar México a esa velocidad, la vía es la mitad del truco.",
         "Para cruzar México a esa velocidad, la vía es la mitad del truco."),
        ("Primero, las curvas. En las líneas nuevas de Japón, el radio mínimo es de 4 km.",
         "Primero, las curvas. En las líneas nuevas de Japón, el radio mínimo es de cuatro kilómetros."),
        ("Si cerraras esa curva en un círculo, daría una vuelta de 25 km.",
         "Si cerraras esa curva en un círculo, daría una vuelta de veinticinco kilómetros."),
        ("Así, a 300 por hora, la curva no te avienta contra la ventana.",
         "Así, a trescientos por hora, la curva no te avienta contra la ventana."),
        ("Segundo: los rieles van soldados. Casi no hay juntas… y casi no hay traca-traca.",
         "Segundo: los rieles van soldados. Casi no hay juntas... y casi no hay traca traca."),
        ("Tercero: no cruza ni una calle. Cero cruces con autos, con gente o con vacas.",
         "Tercero: no cruza ni una calle. Cero cruces con autos, con gente, o con vacas."),
        ("Cuarto: no quema diésel. La energía baja de un cable a 25 mil volts.",
         "Cuarto: no quema diésel. La energía baja de un cable a veinticinco mil volts."),
        ("Hasta la nariz larga tiene su razón: corta el aire y evita un trueno al entrar a los túneles.",
         "Hasta la nariz larga tiene su razón: corta el aire, y evita un trueno al entrar a los túneles."),
    ]),
    ("maglev", [
        ("Parte 4: el tren que flota.", "Parte cuatro: el tren que flota."),
        ("Y si México quisiera ir más rápido, hay un tren que no toca las vías.",
         "Y si México quisiera ir más rápido, hay un tren que no toca las vías."),
        ("Se llama maglev: levitación magnética.", "Se llama maglev: levitación magnética."),
        ("Sus imanes lo levantan y lo mantienen a cerca de 1 cm del riel.",
         "Sus imanes lo levantan, y lo mantienen a cerca de un centímetro del riel."),
        ("Y la vía misma es el motor: un campo magnético que corre y lo va jalando.",
         "Y la vía misma es el motor: un campo magnético que corre, y lo va jalando."),
        ("El de Shanghái lleva más de 20 años en servicio y hoy va a 300 km/h.",
         "El de Shanghái lleva más de veinte años en servicio, y hoy va a trescientos kilómetros por hora."),
        ("Más rápido que un avión comercial al despegar, que va a unos 250 a 290.",
         "Más rápido que un avión comercial al despegar, que va a unos doscientos cincuenta a doscientos noventa."),
        ("En pruebas, China ya pasó de los 600 km/h. Pero ninguno así está en servicio.",
         "En pruebas, China ya pasó de los seiscientos kilómetros por hora. Pero ninguno así está en servicio."),
        ("El problema: no puede usar ni un metro de vía normal. Todo se construye desde cero.",
         "El problema: no puede usar ni un metro de vía normal. Todo se construye desde cero."),
    ]),
    ("costo", [
        ("Parte 5: ¿cuánto costaría?", "Parte cinco: ¿cuánto costaría?"),
        ("Un tren bala a Guadalajara no tiene precio: nadie lo ha presupuestado.",
         "Un tren bala a Guadalajara no tiene precio: nadie lo ha presupuestado."),
        ("Pero hay una pista: el tren México–Querétaro.", "Pero hay una pista: el tren México Querétaro."),
        ("Son 232 km, y Hacienda calcula una inversión de más de 206 mil millones de pesos.",
         "Son doscientos treinta y dos kilómetros, y Hacienda calcula una inversión de más de doscientos seis mil millones de pesos."),
        ("Casi 900 millones de pesos por cada kilómetro.", "Casi novecientos millones de pesos por cada kilómetro."),
        ("Y ese ni siquiera es tren bala.", "Y ese ni siquiera es tren bala."),
        ("Uno de alta velocidad pide curvas enormes, túneles y puentes.",
         "Uno de alta velocidad pide curvas enormes, túneles y puentes."),
        ("Al precio del México–Querétaro, solo los 540 km a Guadalajara rondarían 480 mil millones de pesos.",
         "Al precio del México Querétaro, solo los quinientos cuarenta kilómetros a Guadalajara rondarían cuatrocientos ochenta mil millones de pesos."),
        ("¿Y el boleto? Todavía no hay precio oficial.",
         "¿Y el boleto? Todavía no hay precio oficial."),
    ]),
    ("mexico", [
        ("Parte 6: lo que México sí está construyendo.", "Parte seis: lo que México sí está construyendo."),
        ("Un tren bala no viene pronto… pero sí trenes rápidos.",
         "Un tren bala no viene pronto... pero sí trenes rápidos."),
        ("El México–Querétaro ya va en 32 % de avance.", "El México Querétaro ya va en treinta y dos por ciento de avance."),
        ("Saldrá de Buenavista, irá a unos 160 km/h y llegará a Querétaro en 1 hora y 40 minutos.",
         "Saldrá de Buenavista, irá a unos ciento sesenta kilómetros por hora, y llegará a Querétaro en una hora y cuarenta minutos."),
        ("Casi una hora menos que tu camión. Debe arrancar en 2027.",
         "Casi una hora menos que tu camión. Debe arrancar en dos mil veintisiete."),
        ("Y sigue: Querétaro–Irapuato ya está en obra, y el tramo a Guadalajara pondría su primera piedra en diciembre.",
         "Y sigue: Querétaro Irapuato ya está en obra, y el tramo a Guadalajara pondría su primera piedra en diciembre."),
        ("Jalisco calcula unas 4 horas de la CDMX a Guadalajara, hacia 2030.",
         "Jalisco calcula unas cuatro horas de la Ciudad de México a Guadalajara, hacia dos mil treinta."),
        ("No es tren bala… pero serían 3 horas menos que el camión.",
         "No es tren bala... pero serían tres horas menos que el camión."),
    ]),
    ("cierre", [
        ("Curvas de kilómetros, rieles soldados y un tren que frena solo cuando tiembla: eso haría falta.",
         "Curvas de kilómetros, rieles soldados, y un tren que frena solo cuando tiembla: eso haría falta."),
        ("¿Tú te subirías a un tren bala aquí? Sí o no, en los comentarios.",
         "¿Tú te subirías a un tren bala aquí? Sí o no, en los comentarios."),
        ("Mándaselo a alguien que hace el viaje a Guadalajara en camión.",
         "Mándaselo a alguien que hace el viaje a Guadalajara en camión."),
        ("Porque cuando un tren bala ya te dejó en Guadalajara…",
         "Porque cuando un tren bala ya te dejó en Guadalajara..."),
    ]),
]

# Ganchos y cierres propios de los 2 Shorts (un solo mp3: narr_trenbala_out.mp3)
REEL_OUT = [
    ("Tu alerta sísmica te da segundos… a un tren bala le basta uno.",          # 0 gancho Short A
     "Tu alerta sísmica te da segundos... a un tren bala le basta uno."),
    ("Mándaselo a alguien que siempre corre cuando suena la alerta.",           # 1 cierre A
     "Mándaselo a alguien que siempre corre cuando suena la alerta."),
    ("Porque tu alerta sísmica te da segundos…",                              # 2 loop A
     "Porque tu alerta sísmica te da segundos..."),
    ("Este tren no toca las vías: flota… y va más rápido que un avión al despegar.",  # 3 gancho Short B
     "Este tren no toca las vías: flota... y va más rápido que un avión al despegar."),
    ("Mándaselo a alguien que cree que los trenes son lentos.",               # 4 cierre B
     "Mándaselo a alguien que cree que los trenes son lentos."),
    ("Porque este tren no toca las vías…",                                    # 5 loop B
     "Porque este tren no toca las vías..."),
]

# Etiquetas de emoción para ElevenLabs (capítulo, frase) → etiqueta. Solo en el texto que se manda a la voz.
TAGS = {('c0', 0): '[curious]', ('c2', 7): '[excited]', ('c2', 9): '[curious]', ('out', 0): '[curious]',
        ('out', 3): '[excited]'}

# Lista de edición: video completo y 2 Shorts (skill yt-shorts)
EDITS = {
    'full': [('gap', 0.25), ('c0', 0, 5), ('gap', 1.4), ('c1', 0, 8), ('gap', 1.4), ('c2', 0, 17), ('gap', 1.4),
             ('c3', 0, 9), ('gap', 1.4), ('c4', 0, 10), ('gap', 1.4), ('c5', 0, 8), ('gap', 1.4), ('c6', 0, 8),
             ('gap', 1.2), ('c7', 0, 4), ('gap', 2.0)],
    # Short A: el tren bala frena antes de que llegue el sismo
    'reelA': [('gap', 0.15), ('out', 0, 0), ('gap', 0.35), ('c2', 3, 8), ('gap', 0.35), ('c2', 9, 10),
              ('gap', 0.35), ('c2', 15, 17), ('gap', 0.45), ('out', 1, 2), ('gap', 1.2)],
    # Short B: el tren que flota (maglev)
    'reelB': [('gap', 0.15), ('out', 3, 3), ('gap', 0.35), ('c4', 2, 10), ('gap', 0.45), ('out', 4, 5), ('gap', 1.2)],
}

SPOKEN = {'km': 1, 'km/h': 3, 'CDMX': 3, 'P': 1, 'S': 1, '32': 3, '%': 2, '2011,': 3, 'traca-traca': 2,
          'México–Querétaro': 2, 'México–Querétaro.': 2, 'México–Querétaro,': 2, 'Querétaro–Irapuato': 2,
          '…tu': 1, '1': 1}


def texto_voz(c, i):
    """Texto que se manda a ElevenLabs (con la etiqueta de emoción si la hay)."""
    lst = REEL_OUT if c == 'out' else CAPS[int(c[1:])][1]
    v = lst[i][1]
    return (TAGS[(c, i)] + ' ' + v) if (c, i) in TAGS else v


if __name__ == '__main__':
    tot = 0
    for k, (name, ph) in enumerate(CAPS + [("out", REEL_OUT)]):
        v = " ".join(p[1] for p in ph)
        tot += len(v) if name != 'out' else 0
        print(f'c{k}' if name != 'out' else 'out', name, len(v), "chars ~", round(len(v) / 14.5, 1), "s")
    print("total largo", tot, "chars ~", round(tot / 14.5 / 60, 2), "min")
