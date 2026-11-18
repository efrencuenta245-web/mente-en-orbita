"""Shorts verticales del tren bala (18-nov-2026), sacados del largo. SHORT=A (sismo) o SHORT=B (maglev).
Tiempos: tl_trenbala_reelA.json / reelB (kit/timeline.py). Las frases largas (> 4 s) se parten en 2 escenas por palabras.
Uso: SHORT=A python3 trenbala_short.py tiempos | preview T… | hoja | render | registrar … | final "L1" "l2" CAT SEMILLA BPM"""
import os, sys, json, shutil, re
os.environ['MOTOR_FORMATO'] = 'v'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import montaje
import trenbala_esc as E
from trenbala_esc import mk_corte
from motor2 import seg

SH = os.environ.get('SHORT', 'A')
TEMA = f'trenbala_short{SH.lower()}'
OUT = '/home/claude'
TL = f'{OUT}/tl_trenbala_reel{SH}.json'
MAXD = 4.0


def partir():
    """Frases del Short (con partes) -> lista [(clave, texto, a, b)] donde clave = (c, i, parte)."""
    d = json.load(open(TL))
    out = []
    for p in d['phrases']:
        ws = p['words']
        dur = p['b'] - p['a']
        if dur > MAXD and len(ws) >= 6:
            mid = (p['a'] + p['b']) / 2
            best, bj = 1e9, None
            for j in range(2, len(ws) - 2):
                cost = abs(ws[j][1] - mid) - (0.8 if re.search(r'[,.:;…]$', ws[j - 1][0]) else 0)
                if cost < best:
                    best, bj = cost, j
            out.append(((p['c'], p['i'], 0), ' '.join(w[0] for w in ws[:bj]), p['a'], ws[bj - 1][2]))
            out.append(((p['c'], p['i'], 1), ' '.join(w[0] for w in ws[bj:]), ws[bj][1], p['b']))
        else:
            out.append(((p['c'], p['i'], 0), p['text'], p['a'], p['b']))
    return out, d['dur']


corteP = mk_corte(lambda u: seg(u, 0.2, 2.4), lambda u: 0.0, pal='ONDA P', pal_t0=0.4, kick_txt='ESQUEMA')
corteS = mk_corte(lambda u: 1.0, lambda u: seg(u, 0.1, 1.8), sac=lambda u: 0.8 * seg(u, 0.8, 1.2) * (1 - seg(u, 2.0, 2.6)),
                  kick_txt='ONDA S · LA FUERTE')

# (c, i, parte, escena)
SPEC = {
    'A': [
        ('out', 0, 0, dict(fn=E.s_hookA, c=(0.5, 0.45), sfx=[(1.4, 'bass', 1.0), (1.4, 'burst', 0.6)])),
        ('out', 0, 1, dict(fn=E.s_uno, tr='golpe', sfx=[(0.65, 'bass', 0.9)])),
        ('c2', 3, 0, dict(fn=corteP, tr='cristal', palabra='ONDA P')),
        ('c2', 3, 1, dict(fn=E.s_sensores, tr='deslizar')),
        ('c2', 4, 0, dict(fn=corteS, tr='rompe', c=(0.5, 0.55), sfx=[(0.8, 'sub', 1.0)])),
        ('c2', 5, 0, dict(fn=E.s_preview_sismo, tr='whip')),
        ('c2', 5, 1, dict(fn=E.s_corte_luz, tr='glitch', sfx=[(0.72, 'burst', 0.9)])),
        ('c2', 6, 0, dict(fn=E.s_frena_solo, tr='cubo')),
        ('c2', 7, 0, dict(fn=E.s_cinturon, tr='remolino', c=(0.5, 0.5))),
        ('c2', 7, 1, dict(fn=E.s_2011, tr='flash', sfx=[(1.4, 'bass', 0.7)])),
        ('c2', 8, 0, dict(fn=E.s_19trenes, tr='rebanadas', sfx=[(1.6, 'chime_a', 0.4), (1.8, 'chime_c', 0.4)])),
        ('c2', 8, 1, dict(fn=E.s_ninguno, tr='iris', sfx=[(0.2, 'chime_c', 0.5)])),
        ('c2', 9, 0, dict(fn=E.s_ojo, tr='giro', sfx=[(0.0, 'sub', 0.9)])),
        ('c2', 10, 0, dict(fn=E.s_4km, tr='deslizar_abajo')),
        ('c2', 10, 1, dict(fn=E.s_orejas, tr='mosaico')),
        ('c2', 14, 0, dict(fn=E.s_nunca, tr='glitch', sfx=[(0.0, 'sub', 0.8)])),
        ('c2', 14, 1, dict(fn=E.s_descarrila, tr='push', sfx=[(1.0, 'sub', 0.8)])),
        ('c2', 15, 0, dict(fn=E.s_154, tr='cubo_izq', sfx=[(1.6, 'chime_c', 0.5)])),
        ('c2', 16, 0, dict(fn=E.s_62, tr='zoom', c=(0.5, 0.5))),
        ('c2', 16, 1, dict(fn=E.s_frena_solo, tr='whip_izq')),
        ('out', 1, 0, dict(fn=E.s_mandaA, tr='deslizar')),
        ('out', 2, 0, dict(loop=True, tr='zoom', c=(0.5, 0.45))),
    ],
    'B': [
        ('out', 3, 0, dict(fn=E.s_hookB, c=(0.5, 0.5), sfx=[(0.0, 'riser', 0.6), (1.1, 'bass', 0.8)])),
        ('out', 3, 1, dict(fn=E.s_mag_sube, tr='whip')),
        ('c4', 2, 0, dict(fn=E.s_mag_nombre, tr='cubo')),
        ('c4', 3, 0, dict(fn=E.s_mag_1cm, tr='zoom', c=(0.5, 0.5), sfx=[(0.1, 'shimmer', 0.6), (1.0, 'tick', 0.6)])),
        ('c4', 3, 1, dict(fn=E.s_mag_sube, tr='deslizar_abajo')),
        ('c4', 4, 0, dict(fn=E.s_mag_motor, tr='mosaico', sfx=[(0.4, 'digital', 0.5)])),
        ('c4', 4, 1, dict(fn=E.s_mag_jala, tr='giro')),
        ('c4', 5, 0, dict(fn=E.s_shanghai, tr='rebanadas', sfx=[(0.05, 'slap', 0.8)])),
        ('c4', 5, 1, dict(fn=E.s_vel300, tr='glitch', sfx=[(0.2, 'riser', 0.4)])),
        ('c4', 6, 0, dict(fn=E.s_mag_pasa, tr='iris', c=(0.5, 0.5), sfx=[(0.2, 'whoosh', 0.8)])),
        ('c4', 6, 1, dict(fn=E.s_avion, tr='deslizar', sfx=[(0.3, 'chime_a', 0.4), (0.6, 'chime_b', 0.4)])),
        ('c4', 7, 0, dict(fn=E.s_600, tr='golpe', sfx=[(0.1, 'riser', 0.5)])),
        ('c4', 7, 1, dict(fn=E.s_pruebas, tr='remolino', sfx=[(0.4, 'scribble', 0.5)])),
        ('c4', 8, 0, dict(fn=E.s_via_normal, tr='rompe', c=(0.5, 0.5), sfx=[(0.5, 'scribble', 0.5)])),
        ('c4', 8, 1, dict(fn=E.s_desde_cero, tr='cubo_izq')),
        ('out', 4, 0, dict(fn=E.s_mandaB, tr='whip_izq')),
        ('out', 5, 0, dict(loop=True, tr='zoom', c=(0.5, 0.5))),
    ],
}

TXT, ESCENAS, T, DUR = [], [], [], None
if os.path.exists(TL):
    frs, DUR = partir()
    idx = {k: n for n, (k, _, _, _) in enumerate(frs)}
    TXT = [f[1] for f in frs]
    T = [(round(f[2], 3), round(f[3], 3)) for f in frs]
    for c, i, parte, esc in SPEC[SH]:
        if (c, i, parte) in idx:
            ESCENAS.append(dict(esc, desde=idx[(c, i, parte)]))
    # frases que no tienen escena propia se quedan en la anterior (no se pierde nada)
VOZ = TXT

if __name__ == '__main__':
    if sys.argv[1] == 'tiempos':
        json.dump({'T': T, 'DUR': round(DUR, 2)}, open(f'{OUT}/tiempos_{TEMA}.json', 'w'))
        shutil.copy(f'{OUT}/narr_trenbala_reel{SH}.wav', f'{OUT}/narr_{TEMA}_pad.wav')
        print('DUR', DUR, 'frases', len(T), 'escenas', len(ESCENAS))
        for k, (a, b) in enumerate(T):
            print(f'{k:2d} {a:6.2f}–{b:6.2f} {TXT[k]}')
        sys.exit()
    montaje.cli(globals())
