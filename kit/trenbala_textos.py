"""Textos de YouTube del tren bala (yt-seo + yt-capitulos + yt-shorts): capítulos desde tl_trenbala_full.json.
Escribe youtube/guiones/2026-11-18_trenbala_youtube.md y /home/claude/textos_trenbala.json."""
import json

TL = '/home/claude/tl_trenbala_full.json'
REPO = '/home/claude/mente-en-orbita'
d = json.load(open(TL))
ph = d['phrases']
NOM = {'c0': 'Tren bala contra camión', 'c1': 'Parte 1: el viaje a Guadalajara', 'c2': 'Parte 2: cuando tiembla',
       'c3': 'Parte 3: el secreto de los 300 km/h', 'c4': 'Parte 4: el tren que flota (maglev)',
       'c5': 'Parte 5: ¿cuánto costaría?', 'c6': 'Parte 6: el tren México–Querétaro', 'c7': '¿Te subirías?'}
caps = []
for c in ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7']:
    a = min(p['a'] for p in ph if p['c'] == c)
    s = 0 if c == 'c0' else max(0, int(a - 1.0))
    caps.append((s, NOM[c]))
fmt = lambda s: f'{s // 60}:{s % 60:02d}'
dur = d['dur']
cap_txt = '\n'.join(f'{fmt(s)} {n}' for s, n in caps)

TITULO = '¿Qué pasaría si México tuviera un tren bala?'
ALT = ['Tren bala en México: frena solo si tiembla', 'Tren bala en México: ¿qué haría falta de verdad?']
DESC = f"""¿Te imaginas ir de la CDMX a Guadalajara en tren bala? Mientras tu camión apenas llega a Querétaro, uno como el de Japón ya te habría dejado en Guadalajara.
Armamos el tren bala mexicano pieza por pieza: el viaje, qué pasa cuando tiembla, por qué puede ir a 300 km/h, el tren que flota, cuánto costaría y lo que México sí está construyendo.

Capítulos:
{cap_txt}

¿Tú te subirías a un tren bala aquí? Sí o no, en los comentarios.

Fuentes:
• JR Central (Nozomi Tokio–Shin-Osaka, 2 h 21 min): global.jr-central.co.jp/en/company/about_shinkansen
• JR East, Annual Report 2011 (corte de corriente 12–15 s antes del golpe fuerte) y 2005 (Toki 325)
• Nakamura, 14 WCEE 2008 (UrEDAS) · JSCE 2013 (19 trenes en marcha el 11-mar-2011)
• JR East, FASTECH 360 (frenado de ~4 km desde 360 km/h)
• Guinness World Records (cero muertes por choque o descarrilamiento desde 1964)
• Taniguchi, 1992 (radio mínimo de curva, 25 kV)
• Shanghai maglev (300 km/h desde 2021) · Transrapid (~10 mm) · Yicai Global (maglev de 600 km/h en pruebas)
• Eje Central (SASMEX, ~60 s para sismos de la costa)
• Publimetro (costo del México–Querétaro según Hacienda, 6-abr-2026; tren a Guadalajara, 12-nov-2026)
• Excélsior (32 % de avance, 31-oct-2026) · N+ (160 km/h y 1 h 40 min; arranque en 2027) · Crónica Jalisco (primera piedra Irapuato–Guadalajara, dic-2026)
• ETN y SICT (tiempos por carretera)

Notas: las animaciones son recreaciones y esquemas (escala exagerada donde se indica). Las 2 h 30 a Guadalajara y los 480 mil millones son estimaciones propias a partir de los datos citados.
Fotos: N700S en Kikugawa (CC0, MaedaAkihiko), E5 en Omiya (CC0, Toshinori baba) y maglev de Shanghái (dominio público, Alex Needham), Wikimedia Commons.

Síguenos en Instagram: @mente_en_orbita1

#trenbala #mexico #ciencia #curiosidades #menteenorbita"""

TAGS = ['tren bala', 'tren bala méxico', 'qué pasaría si méxico tuviera tren bala', 'tren méxico guadalajara',
        'tren méxico querétaro', 'shinkansen', 'tren bala japón', 'tren bala sismo', 'maglev', 'tren que flota',
        'alerta sísmica', 'tren de alta velocidad', 'trenes de pasajeros méxico', 'mente en órbita']

SHORTS = {
    'A': dict(titulo='Al tren bala le basta 1 segundo si tiembla #Shorts',
              texto='Tu alerta sísmica te da segundos… a un tren bala le basta uno para empezar a frenar. '
                    'Video completo en el canal: ¿Qué pasaría si México tuviera un tren bala?\n'
                    'Fuentes: JR East, Nakamura (UrEDAS), Guinness, Eje Central (SASMEX).\n#trenbala #sismo #ciencia #mexico #Shorts'),
    'B': dict(titulo='Este tren no toca las vías: flota #Shorts',
              texto='El maglev de Shanghái flota a cerca de 1 cm de su riel y va a 300 km/h: más que un avión al despegar. '
                    'Video completo en el canal: ¿Qué pasaría si México tuviera un tren bala?\n'
                    'Fuentes: Shanghai maglev (Wikipedia), Transrapid, Aerospaceweb, Yicai Global. Foto: dominio público (Alex Needham).\n'
                    '#maglev #trenbala #ciencia #curiosidades #Shorts'),
}

md = f"""# YouTube · ¿Qué pasaría si México tuviera un tren bala? (18-nov-2026)

## Largo ({fmt(int(dur))})
**Título:** {TITULO}
Alternativas: {ALT[0]} · {ALT[1]}
**Miniatura:** «2 h 30» de cristal + «CDMX → GDL» (no repite el título)
**Etiquetas:** {', '.join(TAGS)}

### Descripción
{DESC}

## Short A (viernes 13:00)
**Título:** {SHORTS['A']['titulo']}
{SHORTS['A']['texto']}

## Short B (sábado 13:00)
**Título:** {SHORTS['B']['titulo']}
{SHORTS['B']['texto']}

## SEO (sin vidIQ: 0 créditos hasta el 27-nov)
Palabra clave principal: «tren bala» (+ «México» en los primeros 40 caracteres). Secundarias: tren México–Querétaro, tren México–Guadalajara, Shinkansen, maglev, alerta sísmica.
"""
open(f'{REPO}/youtube/guiones/2026-11-18_trenbala_youtube.md', 'w').write(md)
json.dump(dict(titulo=TITULO, desc=DESC, tags=TAGS, shorts=SHORTS, capitulos=cap_txt, dur=dur),
          open('/home/claude/textos_trenbala.json', 'w'), ensure_ascii=False, indent=1)
print(cap_txt)
print('dur', dur, 'desc chars', len(DESC))
