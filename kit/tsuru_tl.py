"""Tiempos del reel de del Tsuru: autosync (silencios) -> voz editada + tl_tsuru.json para escenas.py."""
import sys, json
sys.path.insert(0, '/home/claude')
import autosync as A
A.setup('tsuru_phr', '/home/claude/narr_tsuru.mp3', tag="tsuru", SPOKEN={'0': 'cero', '2,400,000': 'dos millones cuatrocientos mil', '33': 'treinta y tres', '25': 'veinticinco', '2.4': 'dos punto cuatro', '1.7': 'uno punto siete', 'ABS': 'a be ese', '2007': 'dos mil siete', '2012': 'dos mil doce', '4,000': 'cuatro mil', '2017': 'dos mil diecisiete', '60': 'sesenta'}, GAP_IN=0.16, GAP_OUT=0.30, TEMPO=float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)
if sys.argv[1] == 'map':
    A.main(['', 'map'])
else:
    A.build_voice()
    ph = []
    for i, p in enumerate(A.anim.PH):
        st = p['starts'] + [p['b']]
        ph.append({'c': 'c0', 'i': i, 'a': p['a'], 'b': p['b'],
                   'words': [[w, st[k], st[k + 1]] for k, w in enumerate(p['words'])]})
    json.dump({'dur': A.NEWDUR, 'voice_end': A.PIECES[-1][-1][2], 'phrases': ph}, open('/home/claude/tl_tsuru.json', 'w'), ensure_ascii=False)
    print('dur', A.NEWDUR, 'voz', A.VOICE_LEN)
