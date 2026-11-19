"""Reel diario sáb 21-nov-2026 18:00 (propuesto) — «Tu llanta no está ponchada… tiene frío.»
El aire de la llanta son billones de billones de moléculas que chocan contra ella: eso es la presión. Con frío se mueven
más lento, pegan más suave y la presión baja: ~1 psi por cada 10 °F (~5.6 °C) (AAA). Ejemplo: de 25 °C en la tarde a
3 °C en la madrugada = casi 4 psi menos. Error (segundo gancho): inflarla con el número del costado (es la presión
MÁXIMA de la llanta, no la recomendada: esa viene en la etiqueta de la puerta del conductor, AAA); se mide en frío
(sin manejar ~3 h, AAA). Baja: se gasta de las orillas, se calienta (AAA) y gasta más gasolina (~0.2 % por cada psi,
fueleconomy.gov). El testigo del tablero (TPMS) suele prender cuando ya le falta ~25 % (AAA).
Comunidad: automovilistas (temporada de frentes fríos). Inicio tipo 5 (número gigante): en el pre-roll el contador baja
de 0 a −4 y «−4 PSI» se clava con sacudida; luego se revela que es la llanta escarchada a las 7 am con «FRÍO» de
cristal detrás. El final («acuérdate… no está ponchada») regresa al contador (loop).
Voz: PLAN B (Chatterbox, workflow voz_hq) porque el conector de ElevenLabs pide volver a iniciar sesión.
La llanta, el manómetro, la etiqueta (cifras de EJEMPLO) y el carro son esquemas sin marca.
Datos y fuentes: guiones/2026-11-21_llanta.txt.
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import motor2 as M
import piezas as P
import norte as N
from motor2 import (Frame, Cam, space, draw_objects, finish, kicker, pill, doodle_circle, doodle_arrow, line3, dot3,
                    rec_frame, chart_grow, named, seg, ease, eout, clamp, lerp, CYAN, RED, WHITE)
from gasolina import tubo, _B, texto, esquema, golpe_k, sacudir, K, camara, pistola
from casco import dona

M3 = M.M3
TEMA = 'llanta'
TXT = ['Tu llanta no está ponchada… tiene frío.',
       'Mídela a las 7 de la mañana',
       'y a las 3 de la tarde: no marca lo mismo.',
       'Adentro, billones de billones de moléculas de aire',
       'chocan contra la llanta.',
       'Cada golpe empuja tantito,',
       'y todos juntos la sostienen: eso es la presión.',
       'Con frío se mueven más lento,',
       'pegan más suave… y la presión baja.',
       'Por cada 5.5 grados menos,',
       'pierde más o menos una libra.',
       'Si ayer hizo 25 grados y amaneció a 3,',
       'son casi 4 libras menos.',
       'Y aquí viene el error:',
       'inflarla con el número que trae la llanta.',
       'Ese número es lo máximo que aguanta,',
       'no lo que pide tu carro.',
       'La presión correcta viene en una etiqueta,',
       'en la puerta del conductor.',
       'Y se mide en frío, antes de manejar,',
       'porque al rodar se calienta y marca de más.',
       'Baja, se gasta de las orillas,',
       'se calienta y te cobra más gasolina.',
       'Y el foquito del tablero a veces prende',
       'hasta que le falta una cuarta parte.',
       'Mándaselo a quien infla las llantas al ojo.',
       'Y si mañana amanece baja, acuérdate… no está ponchada.']
VOZ = ['Tu llanta no está ponchada... tiene frío.',
       'Mídela a las siete de la mañana',
       'y a las tres de la tarde: no marca lo mismo.',
       'Adentro, billones de billones de moléculas de aire',
       'chocan contra la llanta.',
       'Cada golpe empuja tantito,',
       'y todos juntos la sostienen: eso es la presión.',
       'Con frío se mueven más lento,',
       'pegan más suave... y la presión baja.',
       'Por cada cinco grados y medio menos,',
       'pierde más o menos una libra.',
       'Si ayer hizo veinticinco grados y amaneció a tres,',
       'son casi cuatro libras menos.',
       'Y aquí viene el error:',
       'inflarla con el número que trae la llanta.',
       'Ese número es lo máximo que aguanta,',
       'no lo que pide tu carro.',
       'La presión correcta viene en una etiqueta,',
       'en la puerta del conductor.',
       'Y se mide en frío, antes de manejar,',
       'porque al rodar se calienta y marca de más.',
       'Baja, se gasta de las orillas,',
       'se calienta y te cobra más gasolina.',
       'Y el foquito del tablero a veces prende',
       'hasta que le falta una cuarta parte.',
       'Mándaselo a quien infla las llantas al ojo.',
       'Y si mañana amanece baja, acuérdate... no está ponchada.']
assert len(VOZ) == len(TXT)
_REPO = os.path.dirname(os.path.dirname(HERE))
WORDS = '/home/claude/words_llanta.json'
if not os.path.exists(WORDS):
    WORDS = os.path.join(_REPO, 'guiones', '2026-11-21_llanta_words.json')

AMARILLO = (255, 236, 160)
NARANJA = (255, 140, 50)
AZULC = (150, 210, 230)
GRIS = (150, 150, 160)
ROJO = (255, 60, 45)
VERDE = (60, 210, 120)
HULE = (30, 30, 33)
CROMO = (212, 214, 220)
FRIO = (120, 200, 255)
PLATA = (176, 180, 190)

# ------------------------------------------------------------------ tiempos por palabra
_WT = {}


def _wt():
    if _WT:
        return _WT
    import difflib
    if not os.path.exists(WORDS):                       # todavía sin voz (pruebas): reparte por letras
        T, _ = montaje.cargar(TEMA)
        for i, f in enumerate(VOZ):
            ws = [w for w in f.split() if montaje._norm(w)]
            a, b = T[i] if T else (0, 2)
            L = np.cumsum([0] + [len(w) + 1 for w in ws])[:-1] / max(1, sum(len(w) + 1 for w in ws))
            _WT[i] = [float(x) * (b - a) for x in L]
        return _WT
    d = json.load(open(WORDS))
    if isinstance(d, dict):
        d = d.get('words') or (d.get('transcripts') or [{}])[0].get('words', [])
    tw = [(montaje._norm(w.get('text', '')), float(w['start'])) for w in d
          if w.get('type', 'word') == 'word' and montaje._norm(w.get('text', ''))]
    sw = []
    for i, f in enumerate(VOZ):
        for w in re.sub(r'\[[^\]]*\]', ' ', f).split():
            if montaje._norm(w):
                sw.append((i, montaje._norm(w)))
    sm = difflib.SequenceMatcher(None, [w for _, w in sw], [w for w, _ in tw], autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    per = {}
    for j, (i, w) in enumerate(sw):
        per.setdefault(i, []).append(tw[mp[j]][1] if j in mp else None)
    for i, L in per.items():
        last = None
        for k in range(len(L)):
            if L[k] is None:
                L[k] = (last + 0.25) if last is not None else None
            last = L[k] if L[k] is not None else last
        base = next((x for x in L if x is not None), 0.0)
        _WT[i] = [(x if x is not None else base) - base for x in L]
    return _WT


def Wp(i, palabra, n=0):
    ws = [montaje._norm(w) for w in re.sub(r'\[[^\]]*\]', ' ', VOZ[i]).split() if montaje._norm(w)]
    p = montaje._norm(palabra)
    hits = [k for k, w in enumerate(ws) if w.startswith(p)]
    if not hits:
        return 0.0
    L = _wt()[i]
    return L[min(hits[min(n, len(hits) - 1)], len(L) - 1)]


# ------------------------------------------------------------------ la llanta (eje en z, apoyada en y = 0)
RT, rT = 0.62, 0.27            # radio al centro del hule y grosor


def llanta_m(sag=0.0, giro=0.0, frio=0.0, caliente=0.0, bulto=0.0, hombros=0.0, x=0.0, z=0.0, s=1.0):
    """Llanta semirrealista: hule con 3 canales de la banda, rin cromado de 5 rayos que gira.
    sag 0–1: baja (se aplasta abajo y se abomba de lado). bulto: sobreinflada (más gorda y roja). frio: escarcha azul.
    hombros: las orillas de la banda brillan en rojo (desgaste)."""
    r = rT * (1 + 0.12 * bulto)
    col = M.mixc(M.mixc(HULE, (40, 52, 66), frio), (120, 30, 24), 0.6 * bulto)
    tire = M3.torus(RT, r, col, nu=56, nv=18, gloss=0.25).tf(rx=90)
    V = tire.V.copy()
    cy = RT + r - 0.09 * sag
    V[:, 1] += cy
    low = V[:, 1] < 0.0
    V[low, 1] = 0.0
    side = np.clip((0.45 - V[:, 1]) / 0.45, 0, 1) * sag
    V[:, 2] *= 1 + 0.18 * side
    tire.V = V
    tire = named(tire, 'llanta', rim=0.45, gloss=0.25)
    if bulto > 0.05:
        tire.glow = M.scale_c((255, 60, 30), 0.35 * bulto)
    if caliente > 0.05:
        tire.glow = M.scale_c((255, 110, 40), 0.35 * caliente)
    ms = [tire]
    for dz in (-0.11, 0.0, 0.11):                                     # canales de la banda
        g = M3.torus(RT + r * 0.985, 0.014, (10, 10, 12), nu=56, nv=5).tf(rx=90, t=(0, cy, dz))
        ms.append(named(g, 'canal'))
    if hombros > 0.02:
        for dz in (-0.19, 0.19):
            g = M3.torus(RT + r * 0.86, 0.03, (255, 70, 40), nu=48, nv=6).tf(rx=90, t=(0, cy, dz))
            ms.append(named(g, 'hombro', glow=M.scale_c((255, 60, 30), 0.9 * hombros)))
    ms.append(named(M3.cyl(RT * 0.72, 0.36, (128, 132, 140), n=36, shadow=0, gloss=0.6, y0=-0.18).tf(rx=90, t=(0, cy, 0)), 'rin', rim=0.7, gloss=0.6))
    ms.append(named(M3.cyl(RT * 0.18, 0.4, (90, 92, 98), n=18, shadow=0, gloss=0.7, y0=-0.2).tf(rx=90, t=(0, cy, 0)), 'maza', rim=0.7))
    for j in range(5):
        b = M3.box(0.11, RT * 0.62, 0.05, (196, 198, 206), shadow=0, base=False, gloss=0.8).tf(t=(0, RT * 0.33, 0)).tf(rz=giro + 72 * j)
        ms.append(named(b.tf(t=(0, cy, 0.2)), 'rayo', rim=0.8, gloss=0.9))
    ms.append(named(M3.cyl(0.025, 0.12, (60, 60, 64), n=8, shadow=0).tf(rx=90).tf(t=(0, RT * 0.6, 0)).tf(rz=giro + 36).tf(t=(0, cy, 0.2)), 'valvula'))
    out = P.tfk(ms, s=s, t=(x, 0, z))
    return out, cy * s


def escarcha(fr, t, k=1.0, s=1.0, x=0.0, cy=None, n=40, seed=2):
    """Puntitos de escarcha que brillan sobre la banda."""
    if k <= 0.01:
        return
    rng = np.random.RandomState(seed)
    cy = cy if cy is not None else (RT + rT) * s
    for j in range(n):
        a = math.radians(30 + 120 * rng.rand())
        rr = (RT + rT * 0.95) * s
        p = (x + rr * math.cos(a), cy + rr * math.sin(a), (rng.rand() - 0.5) * 0.4 * s)
        tw = 0.5 + 0.5 * math.sin(t * 6 + j * 1.7)
        dot3(fr, p, r=3, col=(220, 240, 255), a=k * (0.4 + 0.6 * tw), glow=1.0)


def manometro(img, fx, cx, cy, R, psi, k=1.0, col=WHITE, txt=None):
    """Manómetro de llanta (2D): carátula de 0 a 50 PSI, aguja y número."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(14, 14, 18), outline=M.scale_c(WHITE, 0.85 * k), width=6)
    df.ellipse((cx - R, cy - R, cx + R, cy + R), outline=M.scale_c(CYAN, 0.25 * k), width=10)
    for v in range(0, 51, 5):
        a = math.radians(140 + 260 * v / 50)
        r0 = R - (30 if v % 10 == 0 else 18)
        d.line([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + (R - 8) * math.cos(a), cy + (R - 8) * math.sin(a))],
               fill=M.scale_c(WHITE, 0.7 * k), width=4 if v % 10 == 0 else 2)
        if v % 10 == 0 and R > 110:
            d.text((cx + (R - 58) * math.cos(a), cy + (R - 58) * math.sin(a)), str(v), font=M.font('mono', int(R * 0.15)),
                   fill=M.scale_c(GRIS, k), anchor='mm')
    a = math.radians(140 + 260 * clamp(psi / 50))
    d.line([(cx, cy), (cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a))], fill=ROJO, width=8)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(220, 220, 226))
    texto(img, fx, cx, cy + R * 0.48, txt or f'{psi:.0f} PSI', int(R * 0.24), col, k, f='mono', glow=0.35)


def reloj_txt(img, fx, x, y, hora, k=1.0, col=WHITE, icono='luna'):
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    if icono == 'sol':
        d.ellipse((x - 150, y - 34, x - 82, y + 34), fill=M.scale_c((255, 200, 90), k))
        df.ellipse((x - 175, y - 60, x - 57, y + 60), fill=M.scale_c((255, 170, 60), 0.5 * k))
    else:
        d.ellipse((x - 150, y - 34, x - 82, y + 34), fill=M.scale_c((210, 225, 255), k))
        d.ellipse((x - 132, y - 44, x - 70, y + 20), fill=(0, 0, 0))
    texto(img, fx, x + 50, y, hora, 64, col, k, f='mono', glow=0.35)


def corte(fr, t, calor=0.5, k=1.0, n=46, cy=1.0, w=1.5, h=1.1, choques=True, seed=5):
    """Corte de la llanta: pared de hule (line-art que brilla) y moléculas de aire que rebotan adentro.
    calor 0 = frío (azules y lentas) … 1 = caliente (naranjas y rápidas)."""
    if k <= 0.01:
        return
    col_m = M.mixc(FRIO, (255, 150, 70), calor)
    vel = 0.35 + 0.9 * calor
    a, b = w / 2, h / 2
    th = np.linspace(0, 2 * math.pi, 72)
    pared = [(a * 1.05 * math.copysign(abs(math.cos(q)) ** 0.6, math.cos(q)), cy + b * 1.05 * math.copysign(abs(math.sin(q)) ** 0.6, math.sin(q)), 0)
             for q in th]
    line3(fr, pared, col=(225, 228, 236), w=5, a=0.9 * k, glow=0.8)
    line3(fr, [(-a * 0.75, cy - b * 1.25, 0), (a * 0.75, cy - b * 1.25, 0)], col=CROMO, w=6, a=0.8 * k, glow=0.5)   # el rin
    rng = np.random.RandomState(seed)
    tri = lambda s, L: L * (1 - 2 * abs((s % 2) - 1))
    for j in range(n):
        p0x, p0y, vx, vy = rng.rand() * 2, rng.rand() * 2, rng.uniform(0.6, 1.4), rng.uniform(0.6, 1.4)
        sx = p0x + vx * t * vel * 1.3
        sy = p0y + vy * t * vel * 1.3
        x = tri(sx, a * 0.92)
        y = cy + tri(sy, b * 0.88)
        dot3(fr, (x, y, 0.02), r=5, col=col_m, a=k, glow=0.9 + 0.6 * calor)
        if choques:
            fx_ = abs(x) / (a * 0.92)
            if fx_ > 0.94:
                dot3(fr, (math.copysign(a * 1.0, x), y, 0.03), r=int(6 + 10 * calor), col=WHITE, a=k * (fx_ - 0.94) * 16 * (0.4 + 0.6 * calor), glow=1.6)
            fy_ = abs(y - cy) / (b * 0.88)
            if fy_ > 0.94:
                dot3(fr, (x, cy + math.copysign(b * 1.0, y - cy), 0.03), r=int(6 + 10 * calor), col=WHITE, a=k * (fy_ - 0.94) * 16 * (0.4 + 0.6 * calor), glow=1.6)


def foquito(img, fx, cx, cy, s, k=1.0, on=1.0):
    """Testigo de presión baja del tablero: llanta en corte (herradura) con «!» en ámbar."""
    if k <= 0.01:
        return
    col = M.mixc((70, 60, 40), (255, 190, 40), on)
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    w = 8 * s
    d.arc((cx - 60 * s, cy - 70 * s, cx + 60 * s, cy + 50 * s), 20, 160, fill=M.scale_c(col, k), width=int(w))
    d.arc((cx - 60 * s, cy - 50 * s, cx + 60 * s, cy + 70 * s), 200, 340, fill=M.scale_c(col, k), width=int(w))
    d.line([(cx - 64 * s, cy - 10 * s), (cx - 64 * s, cy + 22 * s)], fill=M.scale_c(col, k), width=int(w))
    d.line([(cx + 64 * s, cy - 10 * s), (cx + 64 * s, cy + 22 * s)], fill=M.scale_c(col, k), width=int(w))
    for xx in range(-50, 51, 20):
        d.line([(cx + xx * s, cy + 58 * s), (cx + xx * s, cy + 72 * s)], fill=M.scale_c(col, k), width=int(w * 0.6))
    d.line([(cx, cy - 34 * s), (cx, cy + 6 * s)], fill=M.scale_c(col, k), width=int(w * 1.3))
    d.ellipse((cx - 6 * s, cy + 16 * s, cx + 6 * s, cy + 28 * s), fill=M.scale_c(col, k))
    if on > 0.05:
        df.ellipse((cx - 110 * s, cy - 110 * s, cx + 110 * s, cy + 110 * s), fill=M.scale_c((255, 170, 30), 0.35 * on * k))


def carro_perfil(img, fx, x0, y0, w, k=1.0, puerta=0.0, t=0.0):
    """Sedán de perfil en line-art que brilla (sin marca). puerta 0–1 resalta la puerta del conductor."""
    if k <= 0.01:
        return
    d, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
    P_ = [(0.0, 0.62), (0.04, 0.45), (0.2, 0.4), (0.33, 0.18), (0.62, 0.16), (0.78, 0.38), (0.97, 0.43), (1.0, 0.62)]
    pts = [(x0 + w * a, y0 + w * b) for a, b in P_]
    d.line(pts, fill=M.scale_c(WHITE, 0.9 * k), width=5, joint='curve')
    df.line(pts, fill=M.scale_c(CYAN, 0.35 * k), width=12)
    for cx_ in (0.2, 0.8):
        r = w * 0.09
        cx, cy = x0 + w * cx_, y0 + w * 0.62
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=M.scale_c(WHITE, 0.9 * k), width=6)
        d.ellipse((cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5), outline=M.scale_c(GRIS, k), width=3)
    d.line([(x0 + w * 0.02, y0 + w * 0.62), (x0 + w * 0.11, y0 + w * 0.62)], fill=M.scale_c(WHITE, 0.9 * k), width=5)
    d.line([(x0 + w * 0.29, y0 + w * 0.62), (x0 + w * 0.71, y0 + w * 0.62)], fill=M.scale_c(WHITE, 0.9 * k), width=5)
    d.line([(x0 + w * 0.89, y0 + w * 0.62), (x0 + w * 0.98, y0 + w * 0.62)], fill=M.scale_c(WHITE, 0.9 * k), width=5)
    door = [(x0 + w * 0.36, y0 + w * 0.2), (x0 + w * 0.5, y0 + w * 0.19), (x0 + w * 0.5, y0 + w * 0.6), (x0 + w * 0.34, y0 + w * 0.6),
            (x0 + w * 0.33, y0 + w * 0.4), (x0 + w * 0.36, y0 + w * 0.2)]
    c = M.mixc(GRIS, AMARILLO, puerta)
    d.line(door, fill=M.scale_c(c, k), width=4 + int(3 * puerta))
    if puerta > 0.05:
        df.line(door, fill=M.scale_c(AMARILLO, 0.5 * puerta * k), width=16)


def etiqueta(img, fx, cx, cy, w, k=1.0, ang=0.0):
    """Etiqueta de presión de la puerta (EJEMPLO, sin marca)."""
    if k <= 0.01:
        return
    h = int(w * 0.62)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((0, 0, w - 1, h - 1), radius=14, fill=(246, 244, 236, 255))
    dl.rectangle((0, 0, w, int(h * 0.22)), fill=(220, 210, 60, 255))
    dl.text((w / 2, h * 0.11), 'PRESIÓN DE INFLADO EN FRÍO', font=M.font('sansx', int(w * 0.06)), fill=(20, 20, 22, 255), anchor='mm')
    for j, (a, b) in enumerate((('DELANTERAS', '32 PSI'), ('TRASERAS', '32 PSI'), ('REFACCIÓN', '60 PSI'))):
        y = h * (0.38 + 0.2 * j)
        dl.text((w * 0.08, y), a, font=M.font('mono', int(w * 0.055)), fill=(40, 40, 44, 255), anchor='lm')
        dl.text((w * 0.92, y), b, font=M.font('sansx', int(w * 0.075)), fill=(20, 20, 22, 255), anchor='rm')
    lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    s = P.resorte(k)
    if s < 0.99:
        lay = lay.resize((max(2, int(lay.width * s)), max(2, int(lay.height * s))))
    img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)


# ================================================================== escenas
# 0. gancho (inicio 5: número gigante). En el pre-roll (lo que se ve al final, loop) el contador baja de 0 a −4 y en
#    U_CLAVA «−4 PSI» se clava con sacudida. Luego un crash zoom revela de qué es: la llanta escarchada a las 7 am, con
#    «FRÍO» de cristal detrás y el manómetro en 28.
U_CLAVA = -0.45


def s_gancho(t, fi, u, d):
    ut = Wp(0, 'tiene') - 0.12
    fr = Frame(camara(u, [K(-3.0, 9.0, -10, 6, ty=0.9), K(U_CLAVA, 8.0, -6, 6, ty=0.9), K(0.25, 3.9, 24, 8, ty=0.85),
                          K(ut, 3.6, 34, 8, ty=0.85), K(5.0, 3.5, 38, 8, ty=0.85)], cy=0.7))
    space(fr, t, floor='dots', floor_a=0.8, bokeh=1.0, beam=0.45)
    M.cristal(fr.base, fr.fx, 'FRÍO', u, t0=-2.6, cy=0.43, entrada='golpe')
    ms, cy = llanta_m(frio=1.0, giro=8 * math.sin(t))
    draw_objects(fr, ms)
    escarcha(fr, t, 1.0)
    n = -4 * P.eout4(seg(u, -2.4, U_CLAVA))
    kn = 1 - seg(u, ut - 0.05, ut + 0.1)

    def ui(img, fx):
        if kn > 0.01:
            P.numero_golpe(img, fx, f'{n:.0f} PSI'.replace('-', '−') if n < -0.5 else '0 PSI', 330, kn, size=220,
                           col=M.mixc(WHITE, FRIO, seg(u, U_CLAVA, U_CLAVA + 0.2)))
        kicker(img, 'TU LLANTA · 7:00 AM · FRENTE FRÍO', 150, 1.0, col=AZULC)
        P.titulo_golpe(img, fx, [('Tu llanta no está ponchada…', 'sans'), ('tiene frío.', 'serif')], 210, seg(u, ut, ut + 0.15), size=70)
        manometro(img, fx, 175, 1300, 120, 32 - 4 * P.eout4(seg(u, U_CLAVA, U_CLAVA + 0.4)), k=seg(u, U_CLAVA - 0.2, U_CLAVA), col=FRIO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, max(golpe_k(u, U_CLAVA, 0.4), golpe_k(u, ut + 0.15, 0.3)), amp=26)


# 1-2. dos casos: a las 7 am (luna, azul, 28) y a las 3 pm (sol, cálida, 32)
def _caso_hora(t, fi, u, d, manana):
    yaw0 = -50 if manana else 50
    fr = Frame(camara(u, [K(-0.3, 4.2, yaw0, 10, ty=0.85), K(0.4, 3.4, yaw0 * 0.3, 8, ty=0.85), K(d, 3.3, yaw0 * 0.2, 8, ty=0.85)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.6, beam_x=0.35 if manana else 0.65)
    e = P.entrada(u, -0.25, 0.3, 'desliza')
    ms, cy = llanta_m(frio=1.0 if manana else 0.0, caliente=0.0 if manana else 0.25, giro=-30 * u)
    draw_objects(fr, P.tfk(ms, t=(e['dy'] * (1 if manana else -1), 0, 0)))
    if manana:
        escarcha(fr, t, 1.0)
    return fr


def s_siete(t, fi, u, d):
    fr = _caso_hora(t, fi, u, d, True)
    u7 = Wp(1, 'siete') - 0.1

    def ui(img, fx):
        kicker(img, 'CASO 1 · EN LA MADRUGADA', 150, seg(u, -0.1, 0.2), col=AZULC)
        reloj_txt(img, fx, 560, 300, '7:00 AM', seg(u, u7, u7 + 0.2), col=FRIO, icono='luna')
        manometro(img, fx, 540, 1250, 150, 28 * P.eout4(seg(u, u7 + 0.2, u7 + 0.8)), k=seg(u, 0.1, 0.3), col=FRIO)
        esquema(img, fx, 1.0, txt='EJEMPLO')
    fr.ui.append(ui)
    return finish(fr, fi)


def s_tres(t, fi, u, d):
    fr = _caso_hora(t, fi, u, d, False)
    u3 = Wp(2, 'tres') - 0.1
    un = Wp(2, 'no') - 0.1

    def ui(img, fx):
        kicker(img, 'CASO 2 · EN LA TARDE', 150, seg(u, -0.1, 0.2), col=AZULC)
        reloj_txt(img, fx, 560, 300, '3:00 PM', seg(u, u3, u3 + 0.2), col=(255, 200, 120), icono='sol')
        manometro(img, fx, 540, 1250, 150, 28 + 4 * P.eout4(seg(u, u3 + 0.2, u3 + 0.8)), k=1.0, col=(255, 200, 120))
        pill(img, fx, 540, 470, 'NO MARCA LO MISMO: 28 CONTRA 32', eout(seg(u, un, un + 0.3)), size=28, border=AMARILLO, dot=False)
        esquema(img, fx, 1.0, txt='EJEMPLO')
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, un + 0.05, 0.3), amp=12)


# 3-6. adentro (la cámara atraviesa el costado): moléculas de aire que chocan; cada golpe empuja; juntas la sostienen
def s_adentro(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 2.0, 0, 4, ty=1.0), K(0.35, 3.0, 14, 4, ty=1.0), K(d, 3.1, 18, 4, ty=1.0)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.9)
    M.cristal(fr.base, fr.fx, 'AIRE', u, t0=-0.1, cy=0.3, entrada='zoom')
    corte(fr, t, calor=0.6, k=seg(u, -0.2, 0.1), n=int(10 + 40 * P.eout4(seg(u, 0.0, 1.4))))

    def ui(img, fx):
        kicker(img, 'ADENTRO DE LA LLANTA · CORTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, 'BILLONES DE BILLONES DE MOLÉCULAS', eout(seg(u, 0.5, 0.8)), size=28, border=CYAN, dot=False)
        esquema(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_chocan(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.1, -30, 8, ty=1.0), K(0.35, 2.7, -8, 4, ty=1.0), K(d, 2.6, -4, 4, ty=1.0)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.9)
    corte(fr, t, calor=0.75, n=50)

    def ui(img, fx):
        kicker(img, '¡PUM! CONTRA LA PARED DE HULE', 150, seg(u, -0.1, 0.2), col=AZULC)
        doodle_circle(img, fx, 540, 960, 430, 330, t, k=seg(u, 0.3, 0.7), col=AMARILLO, seed=2)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_empuja(t, fi, u, d):
    ug = Wp(5, 'golpe') - 0.1
    fr = Frame(camara(u, [K(-0.3, 2.2, 10, 4, tx=0.6, ty=1.0), K(0.3, 1.5, 4, 2, tx=0.75, ty=1.0), K(d, 1.45, 0, 2, tx=0.75, ty=1.0)], cy=0.5))
    space(fr, t, floor=None, bokeh=0.8)
    corte(fr, t, calor=0.6, n=30, choques=False)
    ph = (u * 1.2) % 1.0                                   # una molécula que va y viene contra la pared
    x = 0.2 + 0.55 * (1 - abs(2 * ph - 1))
    dot3(fr, (x, 1.05, 0.05), r=16, col=(255, 200, 120), a=1.0, glow=2.0)
    hit = max(0.0, 1 - abs(x - 0.75) / 0.05)
    if hit > 0:
        dot3(fr, (0.79, 1.05, 0.05), r=int(14 + 30 * hit), col=WHITE, a=hit, glow=2.4)
    ax, ay, _ = fr.cam.p1((0.82, 1.05, 0))

    def ui(img, fx):
        rec_frame(img, t, k=1.0, zoom_label='x1.8')
        kicker(img, 'UNA MOLÉCULA', 150, seg(u, -0.1, 0.2), col=AZULC)
        if u > ug:
            doodle_arrow(img, fx, ax + 20, ay, ax + 260, ay, t, k=seg(u, ug, ug + 0.3), col=AMARILLO, seed=1)
            pill(img, fx, ax + 120, ay - 140, 'EMPUJA TANTITO', eout(seg(u, ug + 0.1, ug + 0.4)), size=28, border=AMARILLO)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_sostiene(t, fi, u, d):
    up = Wp(6, 'presion') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.4, 40, 12, ty=1.0), K(0.4, 3.9, 14, 8, ty=1.0), K(d, 3.8, 8, 8, ty=1.0)], cy=0.56))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.4)
    M.cristal(fr.base, fr.fx, 'PRESIÓN', u, t0=up - 0.2, cy=0.23, entrada='sube')
    e = P.entrada(u, -0.2, 0.35, 'cae')
    ms, cy = llanta_m(giro=0.0)
    carro = [named(M3.rbox(1.7, 0.36, 1.0, 0.12, PLATA, n=4, shadow=0, gloss=0.8).tf(t=(0.4, 1.55 + max(0.0, -e['dy']) * 0.4, 0)), 'carro', rim=0.8, gloss=0.8)]
    _B(carro, 0.12, 0.7, 0.12, (90, 92, 98), 0, 0.9, 0, name='suspension', gloss=0.6)
    draw_objects(fr, ms + carro)
    for j in range(12):                                   # todas las moléculas empujan hacia afuera
        a = 2 * math.pi * j / 12
        kk = seg(u, 0.2 + 0.04 * j, 0.5 + 0.04 * j)
        p0 = np.array([0, cy, 0.3])
        line3(fr, [p0 + np.array([0.5 * math.cos(a), 0.5 * math.sin(a), 0]), p0 + np.array([(0.5 + 0.35 * kk) * math.cos(a), (0.5 + 0.35 * kk) * math.sin(a), 0])],
              col=CYAN, w=4, a=kk, glow=1.2)

    def ui(img, fx):
        kicker(img, 'TODAS JUNTAS SOSTIENEN TU CARRO', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=12)


# 7-8. con frío se mueven más lento, pegan más suave y la presión baja (la llanta se aplasta)
def s_lento(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 3.6, 30, 6, ty=1.0), K(0.4, 3.0, 6, 4, ty=1.0), K(d, 2.9, 2, 4, ty=1.0)], cy=0.52))
    space(fr, t, floor=None, bokeh=0.9)
    fri = P.eout4(seg(u, 0.0, 1.0))
    # tiempo "lento": las moléculas avanzan menos (integramos la velocidad para que no salten)
    tt = t - 0.6 * fri * (u + 0.3)
    corte(fr, tt, calor=0.7 * (1 - fri), n=46)
    rng = np.random.RandomState(9)
    for j in range(16):                                   # copos que caen
        ph = (t * 0.25 + rng.rand()) % 1.0
        dot3(fr, (rng.uniform(-1.6, 1.6), 2.4 - 2.6 * ph, rng.uniform(-0.5, 0.8)), r=4, col=(230, 240, 255), a=0.7 * fri, glow=0.8)

    def ui(img, fx):
        P.termometro(img, fx, 150, 1330, 380, 0.75 - 0.6 * fri, f'{int(25 - 22 * fri)} °C', k=seg(u, -0.1, 0.1), col=M.mixc(NARANJA, FRIO, fri))
        kicker(img, 'CON FRÍO · MÁS LENTAS', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_baja(t, fi, u, d):
    ub = Wp(8, 'baja') - 0.1
    sag = P.eout4(seg(u, ub - 0.2, ub + 0.5))
    fr = Frame(camara(u, [K(-0.3, 4.4, -40, 8, ty=0.8), K(0.4, 3.6, -14, 6, ty=0.8), K(ub, 3.0, 4, 4, ty=0.6), K(d, 2.9, 8, 4, ty=0.6)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.4)
    ms, cy = llanta_m(sag=sag, frio=1.0)
    draw_objects(fr, ms)
    escarcha(fr, t, 0.7, cy=cy)

    def ui(img, fx):
        kicker(img, 'PEGAN MÁS SUAVE', 150, seg(u, -0.1, 0.2), col=AZULC)
        manometro(img, fx, 840, 420, 130, 32 - 4 * sag, k=1.0, col=FRIO)
        pill(img, fx, 540, 1350, '↓ LA PRESIÓN BAJA', eout(seg(u, ub, ub + 0.3)), size=34, border=ROJO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ub + 0.3, 0.3), amp=12)


# 9-12. la regla: −5.6 °C = −1 PSI; de 25 a 3 °C (gráfica que crece) = casi −4 PSI
def s_cinco(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, 40, 10, ty=1.0), K(0.4, 3.6, 10, 8, ty=1.0), K(d, 3.5, 4, 8, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.7, bokeh=0.9)
    M.cristal(fr.base, fr.fx, '−5.6 °C', u, t0=-0.3, cy=0.42, entrada='golpe')

    def ui(img, fx):
        P.termometro(img, fx, 300, 1380, 420, 0.7 - 0.18 * P.eout4(seg(u, 0.2, 0.8)), '−5.6 °C', k=seg(u, -0.3, -0.15), col=FRIO)
        kicker(img, 'LA REGLA · 10 °F ≈ 5.6 °C', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 740, 1180, 'POR CADA', eout(seg(u, 0.1, 0.4)), size=30, border=FRIO, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.3, 0.3), amp=12)


def s_libra(t, fi, u, d):
    ul = Wp(10, 'libra') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, -30, 8, ty=0.85), K(0.4, 3.1, -8, 6, ty=0.85), K(d, 3.0, -2, 6, ty=0.85)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.9)
    ms, cy = llanta_m(frio=0.6, sag=0.25)
    draw_objects(fr, ms)

    def ui(img, fx):
        P.numero_golpe(img, fx, '−1 PSI', 420, seg(u, ul, ul + 0.18), size=230, col=AMARILLO)
        kicker(img, '≈ UNA LIBRA POR PULGADA CUADRADA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1350, 'FUENTE: AAA', eout(seg(u, ul + 0.4, ul + 0.7)), size=22, border=(200, 200, 210), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ul + 0.18, 0.35), amp=18)


def s_grafica(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 5.0, 0, 20, ty=1.0), K(0.5, 4.6, -6, 16, ty=1.0), K(d, 4.5, -8, 16, ty=1.0)], cy=0.5))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9)

    def ui(img, fx):
        chart_grow(img, fx, (70, 480, 1010, 1240), [25, 18, 9, 3], ['3 PM', '9 PM', '3 AM', '7 AM'], -0.1, u, unit='°C',
                   title_txt='TEMPERATURA (°C) · EJEMPLO', vmax=30, line=True, tag='FRENTE FRÍO')
        kicker(img, 'DE LA TARDE A LA MADRUGADA', 150, seg(u, -0.1, 0.2), col=AZULC)
        texto(img, fx, 540, 1330, '25 °C → 3 °C = 22 °C MENOS', 46, FRIO, seg(u, 1.0, 1.3), f='mono', glow=0.3)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_cuatro(t, fi, u, d):
    uc = Wp(12, 'cuatro') - 0.1
    sag = P.eout4(seg(u, uc - 0.1, uc + 0.5)) * 0.55
    fr = Frame(camara(u, [K(-0.3, 3.8, 50, 10, ty=0.8), K(0.4, 3.2, 20, 6, ty=0.8), K(d, 3.1, 14, 6, ty=0.8)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.4)
    M.cristal(fr.base, fr.fx, '−4 PSI', u, t0=uc, cy=0.33, entrada='zoom')
    ms, cy = llanta_m(sag=sag, frio=1.0)
    draw_objects(fr, ms)
    escarcha(fr, t, 0.8, cy=cy)

    def ui(img, fx):
        kicker(img, 'CASI 4 LIBRAS MENOS · EN UNA NOCHE', 150, seg(u, -0.1, 0.2), col=AZULC)
        manometro(img, fx, 870, 1330, 120, 32 - 4 * sag / 0.55, k=1.0, col=FRIO)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.35), amp=18)


# 13. SEGUNDO GANCHO: el error (pantalla que se rompe; aviso rojo)
def s_error(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.6, -60, 14, ty=0.85), K(0.35, 3.4, -24, 8, ty=0.85), K(d, 3.2, -18, 8, ty=0.85)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ERROR', u, t0=0.0, cy=0.4, entrada='golpe')
    e = P.entrada(u, -0.2, 0.3, 'gira')
    ms, cy = llanta_m(giro=0.0)
    draw_objects(fr, P.tfk(ms, s=max(0.05, e['escala'])))

    def ui(img, fx):
        kicker(img, 'Y AQUÍ VIENE…', 150, seg(u, -0.1, 0.1), col=(255, 120, 110))
        P.titulo_golpe(img, fx, [('El error', 'sans'), ('de casi todos.', 'serif')], 230, seg(u, 0.1, 0.25), size=86)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.25, 0.35), amp=22)


# 14-16. inflarla con el número del costado (zoom digital al «MAX. 44 PSI»): ese es el máximo, no lo que pide tu carro
def s_costado(t, fi, u, d):
    un = Wp(14, 'numero') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.4, 10, 6, ty=0.85), K(0.4, 2.2, 0, 4, tx=-0.35, ty=1.25), K(d, 2.1, 0, 4, tx=-0.35, ty=1.25)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    ms, cy = llanta_m(giro=0.0)
    draw_objects(fr, ms)
    sx, sy, _ = fr.cam.p1((-0.45, cy + 0.42, 0.3))

    def ui(img, fx):
        lay = Image.new('L', (520, 80), 0)
        ImageDraw.Draw(lay).text((260, 40), 'MAX. PRESS 44 PSI', font=M.font('sansx', 46), fill=235, anchor='mm')
        lay = lay.rotate(28, resample=Image.BICUBIC, expand=True)
        img.paste(Image.new('RGB', lay.size, (205, 205, 210)), (int(sx - lay.width / 2), int(sy - lay.height / 2)), lay)
        rec_frame(img, t, k=seg(u, 0.2, 0.4), zoom_label='x1.8')
        if u > un:
            doodle_circle(img, fx, sx, sy, 300, 130, t, k=seg(u, un, un + 0.4), col=AMARILLO, seed=4)
        kicker(img, 'EL NÚMERO DEL COSTADO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1380, 'EJEMPLO', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_maximo(t, fi, u, d):
    um = Wp(15, 'maximo') - 0.1
    b = P.eout4(seg(u, 0.0, um + 0.4))
    fr = Frame(camara(u, [K(-0.3, 3.0, -30, 6, ty=0.9), K(0.4, 3.6, -10, 8, ty=0.9), K(d, 3.7, -6, 8, ty=0.9)], cy=0.62))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8, beam=0.4)
    M.cristal(fr.base, fr.fx, 'MÁXIMO', u, t0=um, cy=0.32, entrada='golpe')
    ms, cy = llanta_m(bulto=b)
    draw_objects(fr, P.tfk(ms, t=(0.01 * b * math.sin(t * 50), 0, 0)))

    def ui(img, fx):
        manometro(img, fx, 860, 1330, 120, 32 + 12 * b, k=1.0, col=ROJO if b > 0.6 else WHITE)
        kicker(img, 'LO MÁXIMO QUE AGUANTA LA LLANTA', 150, seg(u, -0.1, 0.2), col=AZULC)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, 0.3 * b, amp=6)


def s_noes(t, fi, u, d):
    ux = Wp(16, 'carro') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, 20, 10, ty=1.0), K(0.4, 3.6, 4, 8, ty=1.0), K(d, 3.5, 0, 8, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8)

    def ui(img, fx):
        texto(img, fx, 540, 700, '44 PSI', 200, ROJO, eout(seg(u, -0.3, -0.1)), f='sansx', glow=0.5)
        if u > 0.2:
            N.doodle_arrow_free(img, fx, 220, 560, 860, 840, t, seg(u, 0.2, 0.5), ROJO, seed=5)
        kicker(img, 'NO ES LA DE TU CARRO', 150, seg(u, -0.1, 0.2), col=(255, 120, 110))
        carro_perfil(img, fx, 190, 980, 700, k=seg(u, ux - 0.2, ux + 0.1))
        texto(img, fx, 540, 1150, '¿Y ENTONCES?', 56, WHITE, seg(u, ux + 0.2, ux + 0.4), f='sansx', glow=0.3)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.2, 0.3), amp=14)


# 17-18. la presión correcta viene en una etiqueta, en la puerta del conductor
def s_etiqueta(t, fi, u, d):
    ue = Wp(17, 'etiqueta') - 0.15
    fr = Frame(camara(u, [K(-0.3, 4.0, -20, 12, ty=1.0), K(0.4, 3.6, -6, 8, ty=1.0), K(d, 3.5, -2, 8, ty=1.0)], cy=0.55))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.9, beam=0.6)
    M.cristal(fr.base, fr.fx, 'ETIQUETA', u, t0=ue - 0.1, cy=0.3, entrada='sube')

    def ui(img, fx):
        etiqueta(img, fx, 540, 1060, 760, k=seg(u, -0.15, 0.2), ang=-4 + 3 * math.sin(t * 2))
        doodle_circle(img, fx, 700, 1150, 220, 150, t, k=seg(u, ue, ue + 0.4), col=AMARILLO, seed=6)
        kicker(img, 'LA PRESIÓN CORRECTA', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1430, 'EJEMPLO', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ue + 0.3, 0.3), amp=12)


def s_puerta(t, fi, u, d):
    up = Wp(18, 'puerta') - 0.1
    fr = Frame(camara(u, [K(-0.3, 5.0, 30, 10, ty=1.0), K(0.4, 4.6, 6, 8, ty=1.0), K(d, 4.5, 2, 8, ty=1.0)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.6, bokeh=0.9)
    z = 1.0 + 0.5 * P.eout4(seg(u, up + 0.3, up + 0.9))

    def ui(img, fx):
        w = int(900 * z)
        x0 = 540 - w * 0.43
        carro_perfil(img, fx, x0, 760 - w * 0.25, w, k=1.0, puerta=seg(u, up, up + 0.3), t=t)
        px, py = x0 + w * 0.36, 760 - w * 0.25 + w * 0.45
        if u > up:
            etiqueta(img, fx, px, py, int(150 * z), k=seg(u, up + 0.1, up + 0.4))
            doodle_arrow(img, fx, px + 300, py - 260, px + 70, py - 40, t, k=seg(u, up + 0.2, up + 0.5), col=AMARILLO, seed=3)
        kicker(img, 'EN EL MARCO DE LA PUERTA DEL CONDUCTOR', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1400, 'O EN EL MANUAL', eout(seg(u, up + 0.6, up + 0.9)), size=28, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 19-20. se mide en frío (antes de manejar); al rodar se calienta y marca de más
def s_enfrio(t, fi, u, d):
    ua = Wp(19, 'antes') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.9, 60, 10, ty=0.85), K(0.4, 3.5, 26, 8, ty=0.85), K(d, 3.4, 20, 8, ty=0.85)], cy=0.69))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9, beam=0.5)
    M.cristal(fr.base, fr.fx, 'ANTES', u, t0=ua, cy=0.3, entrada='golpe')
    ms, cy = llanta_m(frio=0.6)
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'SE MIDE EN FRÍO', 150, seg(u, -0.1, 0.2), col=AZULC)
        manometro(img, fx, 830, 1320, 130, 32 * P.eout4(seg(u, 0.1, 0.7)), k=seg(u, -0.1, 0.1), col=VERDE)
        pill(img, fx, 330, 1320, 'SIN MANEJAR ~3 H', eout(seg(u, ua + 0.3, ua + 0.6)), size=26, border=VERDE, dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ua + 0.05, 0.3), amp=12)


def s_rueda(t, fi, u, d):
    uc = Wp(20, 'calienta') - 0.1
    cal = P.eout4(seg(u, uc - 0.2, uc + 0.8))
    fr = Frame(camara(u, [K(-0.3, 4.6, -50, 8, ty=0.85), K(0.4, 3.8, -24, 6, ty=0.85), K(d, 3.7, -18, 6, ty=0.85)], cy=0.6))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.9)
    off = (t * 4.0) % 1.2
    for j in range(-6, 7):                                # el piso corre (la llanta rueda)
        line3(fr, [(j * 1.2 - off, 0.01, 0.9), (j * 1.2 - off + 0.6, 0.01, 0.9)], col=AMARILLO, w=4, a=0.8, glow=0.7)
    ms, cy = llanta_m(giro=-t * 4.0 / (RT + rT) * 57.3, caliente=cal)
    draw_objects(fr, ms)
    P.ondas_calor(fr, t, 0.0, 1.8, 2.6, 1.0, k=cal)

    def ui(img, fx):
        kicker(img, 'AL RODAR SE CALIENTA', 150, seg(u, -0.1, 0.2), col=AZULC)
        manometro(img, fx, 830, 1320, 130, 32 + 3 * cal, k=1.0, col=M.mixc(VERDE, NARANJA, cal))
        pill(img, fx, 330, 1320, 'MARCA DE MÁS', eout(seg(u, uc + 0.4, uc + 0.7)), size=30, border=NARANJA, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


# 21-22. baja: se gasta de las orillas, se calienta y gasta más gasolina
def s_orillas(t, fi, u, d):
    uo = Wp(21, 'orillas') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.0, 80, 30, ty=0.6), K(0.4, 2.6, 70, 22, ty=0.55), K(d, 2.5, 66, 22, ty=0.55)], cy=0.55))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=0.8)
    ms, cy = llanta_m(sag=0.7, hombros=seg(u, uo, uo + 0.4), giro=-t * 40)
    draw_objects(fr, ms)

    def ui(img, fx):
        kicker(img, 'LLANTA BAJA · VISTA DE FRENTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1350, 'SE GASTAN LAS ORILLAS', eout(seg(u, uo + 0.2, uo + 0.5)), size=32, border=ROJO, dot=False)
        esquema(img, fx, 1.0)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_gasolina(t, fi, u, d):
    ug = Wp(22, 'gasolina') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, 40, 10, ty=1.0), K(0.4, 3.2, 16, 8, ty=1.0), K(d, 3.1, 10, 8, ty=1.0)], cy=0.56))
    space(fr, t, floor='dots', floor_a=0.6, bokeh=0.8, beam=0.5)
    e = P.entrada(u, ug - 0.25, 0.3, 'cae')
    if u > ug - 0.25:
        draw_objects(fr, P.tfk(pistola(gota=(u * 1.4) % 1.0), s=0.9, t=(-0.1, max(0.0, -e['dy']) * 0.5 + 0.1, 0)))
    else:
        ms, cy = llanta_m(sag=0.7, caliente=seg(u, -0.2, 0.4))
        draw_objects(fr, P.tfk(ms, s=0.9))
        P.ondas_calor(fr, t, 0.0, 1.6, 2.4, 1.0, k=seg(u, -0.2, 0.4))

    def ui(img, fx):
        kicker(img, 'SE CALIENTA Y GASTA MÁS', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1330, '≈ 0.2 % MÁS GASOLINA POR CADA LIBRA BAJA', eout(seg(u, ug + 0.2, ug + 0.5)), size=24, border=AMARILLO, dot=False)
        pill(img, fx, 540, 1410, 'FUENTE: FUELECONOMY.GOV (EE. UU.)', eout(seg(u, ug + 0.4, ug + 0.7)), size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, ug + 0.05, 0.3), amp=14)


# 23-24. el foquito del tablero a veces prende hasta que le falta una cuarta parte (25 %)
def s_foquito(t, fi, u, d):
    uf = Wp(23, 'prende') - 0.1
    fr = Frame(camara(u, [K(-0.3, 4.0, -20, 10, ty=1.0), K(0.4, 3.6, -4, 8, ty=1.0), K(d, 3.5, 0, 8, ty=1.0)], cy=0.55))
    space(fr, t, floor=None, bokeh=0.8)

    def ui(img, fx):
        d_ = ImageDraw.Draw(img)
        d_.rounded_rectangle((90, 620, 990, 1240), radius=60, fill=(10, 10, 14), outline=(90, 90, 100), width=4)
        d_.arc((140, 700, 520, 1080), 140, 400, fill=(160, 160, 170), width=6)
        d_.arc((560, 700, 940, 1080), 140, 400, fill=(160, 160, 170), width=6)
        texto(img, fx, 330, 980, 'km/h', 30, GRIS, 1.0, f='mono', glow=0)
        texto(img, fx, 750, 980, 'RPM', 30, GRIS, 1.0, f='mono', glow=0)
        on = seg(u, uf, uf + 0.1) * (0.75 + 0.25 * math.sin(t * 9))
        foquito(img, fx, 540, 1150, 0.7, k=1.0, on=on)
        kicker(img, 'EL TESTIGO DE PRESIÓN DEL TABLERO', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 470, 'NO SIEMPRE AVISA A TIEMPO', eout(seg(u, uf + 0.3, uf + 0.6)), size=28, border=AMARILLO, dot=False)
    fr.ui.append(ui)
    return finish(fr, fi)


def s_cuarta(t, fi, u, d):
    uc = Wp(24, 'cuarta') - 0.1
    fr = Frame(camara(u, [K(-0.3, 3.6, 30, 8, ty=0.85), K(0.4, 3.2, 10, 6, ty=0.85), K(d, 3.1, 4, 6, ty=0.85)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.7, bokeh=0.8)
    M.cristal(fr.base, fr.fx, '25 %', u, t0=uc, cy=0.3, entrada='zoom')
    sag = 0.9 * P.eout4(seg(u, 0.0, uc + 0.4))
    ms, cy = llanta_m(sag=sag)
    draw_objects(fr, ms)

    def ui(img, fx):
        dona(img, fx, 840, 1330, 110, 0.25 * P.eout4(seg(u, uc, uc + 0.5)), k=1.0, col=ROJO, txt='−25%', size=44)
        manometro(img, fx, 240, 1330, 110, 32 - 8 * sag / 0.9, k=1.0, col=ROJO)
        kicker(img, 'CUANDO YA LE FALTA UNA CUARTA PARTE', 150, seg(u, -0.1, 0.2), col=AZULC)
        pill(img, fx, 540, 1470, 'FUENTE: AAA', 1.0, size=20, border=(150, 150, 160), dot=False)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, uc + 0.1, 0.3), amp=16)


# 25. mándaselo a quien infla las llantas al ojo (ojo de garabato que mide la llanta con un «?»)
def s_compa(t, fi, u, d):
    fr = Frame(camara(u, [K(-0.3, 4.0, -60, 10, ty=0.85), K(0.4, 3.4, -26, 6, ty=0.85), K(d, 3.3, -20, 6, ty=0.85)], cy=0.66))
    space(fr, t, floor='lines', floor_a=0.8, bokeh=1.0, beam=0.5)
    ms, cy = llanta_m(sag=0.4, frio=0.8)
    draw_objects(fr, ms)
    escarcha(fr, t, 0.8, cy=cy)

    def ui(img, fx):
        P.titulo_golpe(img, fx, [('Mándaselo a quien', 'sans'), ('infla las llantas al ojo.', 'serif')], 210, seg(u, 0.0, 0.15), size=70)
        d_, df = ImageDraw.Draw(img), ImageDraw.Draw(fx)
        k = eout(seg(u, 0.3, 0.6))
        if k > 0:
            cx, cy_ = 540, 620
            d_.ellipse((cx - 130 * k, cy_ - 60 * k, cx + 130 * k, cy_ + 60 * k), outline=WHITE, width=6)
            d_.ellipse((cx - 40 * k, cy_ - 40 * k, cx + 40 * k, cy_ + 40 * k), fill=AZULC)
            d_.ellipse((cx - 16 * k, cy_ - 16 * k, cx + 16 * k, cy_ + 16 * k), fill=(0, 0, 0))
            df.ellipse((cx - 150 * k, cy_ - 80 * k, cx + 150 * k, cy_ + 80 * k), outline=M.scale_c(CYAN, 0.5), width=14)
            texto(img, fx, cx + 200, cy_ - 30, '?', 120, AMARILLO, k, f='sansx', glow=0.5)
    fr.ui.append(ui)
    return sacudir(finish(fr, fi), t, golpe_k(u, 0.15, 0.3), amp=14)


ESCENAS = [dict(desde=0, fn=s_gancho, c=(0.5, 0.6), sfx=[(-2.4 + 0.12 * j, 'tick', 0.45) for j in range(16)] + [(U_CLAVA, 'sub', 1.0), (U_CLAVA, 'bass', 0.9)]),
           dict(desde=1, fn=s_siete, tr='iris', c=(0.5, 0.6), sfx=[(0.5, 'tick2', 0.5), (0.9, 'click', 0.6)]),
           dict(desde=2, fn=s_tres, tr='cubo_izq', c=(0.45, 0.62), sfx=[(0.5, 'chime_a', 0.5), (1.6, 'bass', 0.6)]),
           dict(desde=3, fn=s_adentro, tr='zoom', sfx=[(0.3 + 0.08 * j, 'tick2', 0.25) for j in range(10)]),
           dict(desde=4, fn=s_chocan, tr='mosaico', sfx=[(0.1 + 0.11 * j, 'tick', 0.4) for j in range(10)] + [(0.3, 'scribble', 0.5)]),
           dict(desde=5, fn=s_empuja, tr='push', c=(0.62, 0.5), sfx=[(0.4, 'click', 0.6), (1.2, 'click', 0.6)]),
           dict(desde=6, fn=s_sostiene, tr='deslizar', sfx=[(0.15, 'thud', 0.8), (0.4, 'chime_b', 0.4)]),
           dict(desde=7, fn=s_lento, tr='remolino', sfx=[(0.3, 'whoosh_suave', 0.6)]),
           dict(desde=8, fn=s_baja, tr='wipe', sfx=[(0.8, 'thud', 0.8)]),
           dict(desde=9, fn=s_cinco, tr='glitch', sfx=[(0.3, 'bass', 0.6)]),
           dict(desde=10, fn=s_libra, tr='golpe', sfx=[(0.5, 'sub', 0.8)]),
           dict(desde=11, fn=s_grafica, tr='rebanadas', sfx=[(0.15 + 0.28 * j, 'chime_a' if j < 2 else 'chime_b', 0.5) for j in range(4)]),
           dict(desde=12, fn=s_cuatro, tr='whip', sfx=[(0.4, 'bass', 0.8)]),
           dict(desde=13, fn=s_error, tr='rompe', c=(0.5, 0.5), sfx=[(0.25, 'bass', 0.9)]),
           dict(desde=14, fn=s_costado, tr='giro', sfx=[(0.3, 'click', 0.6), (0.6, 'click', 0.6), (1.0, 'scribble', 0.6)]),
           dict(desde=15, fn=s_maximo, tr='zoom', c=(0.5, 0.5), sfx=[(0.2, 'riser', 0.5)]),
           dict(desde=16, fn=s_noes, tr='flash', sfx=[(0.2, 'scribble', 0.7)]),
           dict(desde=17, fn=s_etiqueta, tr='deslizar_abajo', sfx=[(0.5, 'slap', 0.8)]),
           dict(desde=18, fn=s_puerta, tr='cubo', sfx=[(0.6, 'scribble', 0.5)]),
           dict(desde=19, fn=s_enfrio, tr='iris', c=(0.36, 0.48), sfx=[(0.3, 'tick2', 0.5)]),
           dict(desde=20, fn=s_rueda, tr='whip_izq', sfx=[(0.3, 'whoosh', 0.5), (0.8, 'riser', 0.4)]),
           dict(desde=21, fn=s_orillas, tr='giro', sfx=[(0.6, 'bass', 0.5)]),
           dict(desde=22, fn=s_gasolina, tr='rebanadas', sfx=[(0.6, 'thud', 0.6), (1.0, 'chime_c', 0.4)]),
           dict(desde=23, fn=s_foquito, tr='mosaico', sfx=[(0.5, 'click', 0.8), (0.6, 'tick2', 0.6)]),
           dict(desde=24, fn=s_cuarta, tr='push', c=(0.5, 0.6), sfx=[(0.6, 'bass', 0.6)]),
           dict(desde=25, fn=s_compa, tr='ritmo', sfx=[(0.15, 'bass', 0.7)]),
           dict(desde=26, loop=True, tr='remolino')]

if __name__ == '__main__':
    montaje.cli(globals())
