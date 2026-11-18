"""Video largo de YouTube (horizontal 1920x1080): ¿Qué pasaría si México tuviera tren bala? (18-nov-2026).
Tiempos: tl_trenbala_full.json (kit/timeline.py) → `python3 trenbala_largo.py tiempos` crea tiempos_trenbala_largo.json
y narr_trenbala_largo_pad.wav. Luego: preview, hoja, render, final (como montaje.py; revisión relajada para el largo:
5+ transiciones distintas, 3+ creativas, ninguna dos veces seguidas y letras de cristal en 3+ escenas)."""
import os, sys, json, math, shutil
os.environ['MOTOR_FORMATO'] = 'h'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageFilter
import montaje
import trenbala_esc as E
from trenbala_esc import mk_capitulo, mk_corte, mk_curva
from motor2 import seg, word_caption, W, H, FPS
import motor2 as M

TEMA = 'trenbala_largo'
OUT = '/home/claude'
TL = f'{OUT}/tl_trenbala_full.json'
TXT = [p['text'] for p in json.load(open(TL))['phrases']] if os.path.exists(TL) else []

corteP = mk_corte(lambda u: seg(u, 0.2, 2.6), lambda u: 0.0, pal='ONDA P', pal_t0=0.6, kick_txt='CORTE DE LA TIERRA · ESQUEMA')
corteS = mk_corte(lambda u: 1.0, lambda u: seg(u, 0.1, 2.0), sac=lambda u: 0.8 * seg(u, 0.9, 1.3) * (1 - seg(u, 2.2, 2.8)),
                  kick_txt='ONDA S · LA FUERTE')

ESCENAS = [
    dict(desde=0, fn=E.s_intro, c=(0.6, 0.45)),
    dict(desde=1, fn=E.s_bus_sign, tr='whip'),
    dict(desde=2, fn=E.s_siete_horas, tr='deslizar'),
    dict(desde=3, fn=E.s_dos_y_media, tr='zoom', c=(0.6, 0.5), sfx=[(0.3, 'bass', 0.8)]),
    dict(desde=4, fn=E.s_preview_sismo, tr='glitch', sfx=[(0.95, 'burst', 0.6), (1.6, 'sub', 0.7)]),
    dict(desde=5, fn=E.s_ensambla, tr='rebanadas', sfx=[(1.0, 'click', 0.9), (1.2, 'tick', 0.5), (1.4, 'tick', 0.5)]),
    # Parte 1
    dict(desde=6, fn=mk_capitulo(1, 'Parte 1:', 'el viaje.', 'VIAJE', yaw=-30), tr='cristal', palabra='VIAJE'),
    dict(desde=7, fn=E.s_540, tr='push', c=(0.6, 0.5), sfx=[(0.2, 'riser', 0.4)]),
    dict(desde=8, fn=E.s_casetas, tr='deslizar_abajo', sfx=[(0.6, 'tick', 0.6), (1.1, 'tick', 0.6), (1.6, 'tick', 0.6)]),
    dict(desde=9, fn=E.s_camion7, tr='whip_izq'),
    dict(desde=10, fn=E.s_nozomi, tr='giro', sfx=[(0.05, 'slap', 0.8), (1.4, 'chime_b', 0.5)]),
    dict(desde=11, fn=E.s_estimacion, tr='mosaico', sfx=[(0.1, 'whoosh', 0.6)]),
    dict(desde=12, fn=E.s_torta, tr='iris', c=(0.67, 0.45), sfx=[(1.6, 'chime_c', 0.5)]),
    dict(desde=13, fn=E.s_mientras, tr='cubo', sfx=[(0.2, 'shimmer', 0.6)]),
    # Parte 2
    dict(desde=14, fn=mk_capitulo(2, 'Parte 2:', 'cuando tiembla.', 'SISMOS', yaw=-150), tr='rompe', c=(0.5, 0.5),
         sfx=[(0.2, 'sub', 0.8)]),
    dict(desde=15, fn=E.s_cinturon, tr='remolino', c=(0.67, 0.5)),
    dict(desde=16, fn=E.s_sensores, tr='deslizar', sfx=[(0.3, 'tick2', 0.5), (0.5, 'tick2', 0.5), (0.7, 'tick2', 0.5)]),
    dict(desde=17, fn=corteP, tr='zoom', c=(0.2, 0.7), sfx=[(0.3, 'tick', 0.6)]),
    dict(desde=18, fn=corteS, tr='golpe', c=(0.2, 0.7), sfx=[(0.9, 'sub', 1.0), (1.0, 'burst', 0.5)]),
    dict(desde=19, fn=E.s_corte_luz, tr='glitch', sfx=[(0.72, 'burst', 0.9), (0.75, 'bass', 0.8)]),
    dict(desde=20, fn=E.s_frena_solo, tr='whip', sfx=[(0.1, 'scribble', 0.4)]),
    dict(desde=21, fn=E.s_2011, tr='flash', sfx=[(0.4, 'tick', 0.6), (1.4, 'bass', 0.7), (1.6, 'chime_b', 0.5)]),
    dict(desde=22, fn=E.s_19trenes, tr='rebanadas', sfx=[(1.6, 'chime_a', 0.4), (1.8, 'chime_b', 0.4), (2.0, 'chime_c', 0.4)]),
    dict(desde=23, fn=E.s_ojo, tr='giro', sfx=[(0.0, 'sub', 0.9)]),
    dict(desde=24, fn=E.s_4km, tr='deslizar_abajo', sfx=[(0.3, 'whoosh_suave', 0.5)]),
    dict(desde=25, fn=E.s_orejas, tr='iris', sfx=[(0.3, 'click', 0.8), (0.4, 'whoosh', 0.5)]),
    dict(desde=26, fn=E.s_alerta60, tr='mosaico', sfx=[(0.2, 'digital', 0.6)]),
    dict(desde=27, fn=E.s_uno, tr='golpe', sfx=[(0.65, 'bass', 0.9)]),
    dict(desde=28, fn=E.s_descarrila, tr='glitch', sfx=[(1.0, 'sub', 0.8), (1.1, 'thud', 0.6)]),
    dict(desde=29, fn=E.s_154, tr='cubo_izq', sfx=[(1.6, 'chime_c', 0.5)]),
    dict(desde=30, fn=E.s_62, tr='zoom', c=(0.6, 0.5), sfx=[(1.4, 'bass', 0.7)]),
    # Parte 3
    dict(desde=31, fn=mk_capitulo(3, 'Parte 3: el secreto', 'de los 300 km/h.', '300', yaw=-60, pal_ent='zoom'), tr='cristal', palabra='300'),
    dict(desde=32, fn=E.s_via_truco, tr='push', c=(0.7, 0.6)),
    dict(desde=33, fn=mk_curva(False), tr='deslizar', sfx=[(0.5, 'scribble', 0.4)]),
    dict(desde=34, fn=mk_curva(True), tr='remolino', c=(0.67, 0.52), sfx=[(0.2, 'riser', 0.4)]),
    dict(desde=35, fn=E.s_vaso, tr='giro'),
    dict(desde=36, fn=E.s_soldados, tr='golpe', sfx=[(0.8, 'burst', 0.5), (1.2, 'click', 0.8), (2.0, 'click', 0.8)]),
    dict(desde=37, fn=E.s_cruces, tr='rebanadas', sfx=[(0.6, 'scribble', 0.4), (0.9, 'scribble', 0.4), (1.2, 'scribble', 0.4)]),
    dict(desde=38, fn=E.s_25kv, tr='flash', sfx=[(0.2, 'riser', 0.4)]),
    dict(desde=39, fn=E.s_tunel, tr='zoom', c=(0.75, 0.55), sfx=[(1.0, 'whoosh', 0.7)]),
    # Parte 4
    dict(desde=40, fn=mk_capitulo(4, 'Parte 4:', 'el tren que flota.', 'FLOTA', objeto='maglev', pal_ent='sube'), tr='iris', c=(0.67, 0.55)),
    dict(desde=41, fn=E.s_mag_sube, tr='whip', sfx=[(0.3, 'riser', 0.5)]),
    dict(desde=42, fn=E.s_mag_nombre, tr='cubo'),
    dict(desde=43, fn=E.s_mag_1cm, tr='zoom', c=(0.6, 0.6), sfx=[(0.1, 'shimmer', 0.6), (0.9, 'tick', 0.6)]),
    dict(desde=44, fn=E.s_mag_motor, tr='deslizar_abajo', sfx=[(0.4, 'digital', 0.5)]),
    dict(desde=45, fn=E.s_shanghai, tr='mosaico', sfx=[(0.05, 'slap', 0.8)]),
    dict(desde=46, fn=E.s_avion, tr='whip_izq', sfx=[(0.3, 'chime_a', 0.4), (0.6, 'chime_b', 0.4)]),
    dict(desde=47, fn=E.s_600, tr='golpe', sfx=[(0.1, 'riser', 0.5)]),
    dict(desde=48, fn=E.s_desde_cero, tr='rompe', c=(0.5, 0.5)),
    # Parte 5
    dict(desde=49, fn=mk_capitulo(5, 'Parte 5:', '¿cuánto costaría?', 'COSTO', yaw=-120), tr='cubo_izq'),
    dict(desde=50, fn=E.s_precio, tr='giro'),
    dict(desde=51, fn=E.s_pista, tr='iris', c=(0.75, 0.5)),
    dict(desde=52, fn=E.s_206, tr='deslizar', sfx=[(1.2, 'tick', 0.5), (2.6, 'bass', 0.6)]),
    dict(desde=53, fn=E.s_por_km, tr='zoom', c=(0.67, 0.6), sfx=[(0.3, 'scribble', 0.3)]),
    dict(desde=54, fn=E.s_ni_bala, tr='glitch'),
    dict(desde=55, fn=E.s_terreno, tr='remolino'),
    dict(desde=56, fn=E.s_480, tr='rebanadas', sfx=[(0.4, 'chime_a', 0.4), (0.7, 'chime_c', 0.4)]),
    dict(desde=57, fn=E.s_boleto, tr='flash'),
    # Parte 6
    dict(desde=58, fn=mk_capitulo(6, 'Parte 6: lo que México', 'sí está construyendo.', 'MÉXICO', objeto='mx', yaw=-40), tr='cristal',
         palabra='MÉXICO'),
    dict(desde=59, fn=E.s_tren_mx, tr='deslizar_abajo'),
    dict(desde=60, fn=E.s_32, tr='golpe', sfx=[(0.3, 'riser', 0.4), (1.6, 'chime_b', 0.5)]),
    dict(desde=61, fn=E.s_estaciones, tr='whip', sfx=[(0.5, 'tick', 0.5), (0.9, 'tick', 0.5), (1.3, 'tick', 0.5)]),
    dict(desde=62, fn=E.s_hora_menos, tr='cubo'),
    dict(desde=63, fn=E.s_sigue, tr='push', c=(0.6, 0.5)),
    dict(desde=64, fn=E.s_4h, tr='iris', c=(0.6, 0.5)),
    dict(desde=65, fn=E.s_tres_menos, tr='deslizar', sfx=[(1.4, 'bass', 0.6)]),
    # Cierre
    dict(desde=66, fn=E.s_resumen, tr='ritmo', sfx=[(0.4, 'tick', 0.5), (1.3, 'tick', 0.5), (2.2, 'tick', 0.5)]),
    dict(desde=67, fn=E.s_si_no, tr='giro', sfx=[(0.9, 'click', 0.7), (1.1, 'click', 0.7)]),
    dict(desde=68, fn=E.s_mandalo, tr='mosaico'),
    dict(desde=69, loop=True, tr='zoom', c=(0.6, 0.5)),
]


# ------------------------------------------------------------------ subtítulos en horizontal (bloques de 8 palabras)
def _cap_h(img, t, T, txts, y=905, size=50):
    fx = Image.new('RGB', (W, H), (0, 0, 0))
    for i, (a, b) in enumerate(T):
        nxt = T[i + 1][0] if i + 1 < len(T) else 1e9
        if not (a - 0.05 <= t < nxt - 0.12):
            continue
        w = txts[i].split()
        per = (b - a) * 0.92 / len(w)
        n = len(w)
        k = max(1, math.ceil(n / 8))
        sz = [n // k + (1 if j < n % k else 0) for j in range(k)]
        st = 0
        for j, m in enumerate(sz):
            t0 = a + st * per
            t1 = a + (st + m) * per if j < k - 1 else 1e9
            if t0 <= t < t1:
                word_caption(img, fx, w[st:st + m], t0, t, y=y, size=size, per=per, cx=960, maxw=1300)
                break
            st += m
    small = fx.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    a = np.asarray(img, np.float32) + np.asarray(small, np.float32) * 0.6
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


montaje._cap = _cap_h


def tiempos():
    d = json.load(open(TL))
    T = [(round(p['a'], 3), round(p['b'], 3)) for p in d['phrases']]
    json.dump({'T': T, 'DUR': round(d['dur'], 2)}, open(f'{OUT}/tiempos_{TEMA}.json', 'w'))
    shutil.copy(f'{OUT}/narr_trenbala_full.wav', f'{OUT}/narr_{TEMA}_pad.wav')
    print('DUR', d['dur'], 'frases', len(T))


def revisar():
    trs = [e.get('tr', 'corte') for e in ESCENAS[1:]]
    err = []
    rep = [trs[i] for i in range(1, len(trs)) if trs[i] == trs[i - 1]]
    if rep:
        err.append('repetidas seguidas: ' + ', '.join(rep))
    crea = {montaje.CREATIVAS[x] for x in trs if x in montaje.CREATIVAS}
    if len(set(trs)) < 8 or len(crea) < 3:
        err.append(f'variedad: {len(set(trs))} distintas, {len(crea)} creativas')
    prev = [r for r in montaje._inicios()]
    if prev and trs[0] == prev[0]['primera']:
        err.append(f'primera transición igual a la del video anterior ({trs[0]})')
    e2, hits = montaje._revisar_cristal()
    err += e2
    err += montaje._revisar_mandaselo()
    print('Transiciones:', len(trs), 'cambios;', len(set(trs)), 'distintas;', 'creativas:', sorted(crea))
    for x in err:
        print('ERROR', x)
    return err


def hoja(out, n=None):
    SC = montaje.CTX['_SC']
    ts = [round((e['a'] + e['b']) / 2, 2) for e in SC[:-1]]
    if n:
        ts = ts[n[0]:n[1]]
    ims = [Image.fromarray(montaje.frame_at(t, int(t * FPS))).resize((384, 216)) for t in ts]
    cols = 6
    rows = math.ceil(len(ims) / cols)
    sh = Image.new('RGB', (384 * cols, 216 * rows))
    for i, im in enumerate(ims):
        sh.paste(im, ((i % cols) * 384, (i // cols) * 216))
    sh.save(out)
    print('hoja', out, len(ims))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'tiempos':
        tiempos()
        sys.exit()
    montaje.CTX.update(dict(TEMA=TEMA, TXT=TXT, ESCENAS=ESCENAS, VOZ=TXT, CAP={}))
    T, DUR = montaje.cargar(TEMA)
    montaje.CTX['T'], montaje.CTX['DUR'] = T, DUR
    montaje.CTX['_SC'] = montaje._escenas()
    if cmd == 'preview':
        for ts in sys.argv[2:]:
            t = float(ts)
            Image.fromarray(montaje.frame_at(t, int(t * FPS))).save(f'{OUT}/prev_{TEMA}_{ts}.png')
    elif cmd == 'revisar':
        revisar()
    elif cmd == 'hoja':
        revisar()
        a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        b = int(sys.argv[3]) if len(sys.argv) > 3 else 999
        hoja(f'{OUT}/hoja_{TEMA}_{a}.png', (a, b))
    elif cmd == 'render':
        if revisar():
            raise SystemExit('No se renderiza: corrige los ERROR.')
        out = sys.argv[2] if len(sys.argv) > 2 else f'{OUT}/{TEMA}_sin_audio.mp4'
        a = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
        b = float(sys.argv[4]) if len(sys.argv) > 4 else DUR
        montaje.render(out) if (a == 0.0 and b >= DUR) else None
    elif cmd == 'sonido':
        montaje.sonido(f'{OUT}/efectos_{TEMA}.wav')
    elif cmd == 'final':
        import subprocess
        semilla, bpm = sys.argv[2], sys.argv[3]
        KIT = os.path.dirname(HERE)
        v = f'{OUT}/{TEMA}_sin_audio.mp4'
        fx, mu = f'{OUT}/efectos_{TEMA}.wav', f'{OUT}/musica_{TEMA}.wav'
        montaje.sonido(fx)
        subprocess.run(['python3', os.path.join(KIT, 'musica.py'), str(DUR), mu, semilla, bpm, str(T[-1][1])], check=True)
        # video a la tasa que deja el archivo en ≤ 92 MB (YOUTUBE.md): bitrate = 92·8/dur − 0.2 Mbps
        br = 92 * 8 / DUR - 0.25
        vb = f'{OUT}/{TEMA}_vb.mp4'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', v, '-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{br:.2f}M',
                        '-maxrate', f'{br * 1.3:.2f}M', '-bufsize', f'{br * 2:.2f}M', '-pix_fmt', 'yuv420p', '-an', vb], check=True)
        fin = f'{OUT}/{TEMA}_final.mp4'
        subprocess.run(['bash', os.path.join(KIT, 'mix_musica.sh'), vb, f'{OUT}/narr_{TEMA}_pad.wav', fx, mu, fin], check=True, cwd=KIT)
        import re
        pr = lambda f, k: subprocess.run(['ffprobe', '-v', 'error', '-select_streams', k, '-show_entries', 'stream=duration',
                                          '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip()
        r = subprocess.run(['ffmpeg', '-sseof', '-3', '-i', fin, '-af', 'volumedetect', '-vn', '-f', 'null', '-'],
                           capture_output=True, text=True).stderr
        print('FINAL', fin, 'video', pr(fin, 'v:0'), 'audio', pr(fin, 'a:0'), 'últimos 3 s', re.findall(r'mean_volume: ([-\d.]+)', r),
              'peso', round(os.path.getsize(fin) / 1e6, 1), 'MB')
