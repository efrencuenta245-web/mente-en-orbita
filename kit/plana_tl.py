"""Tiempos del reel de la Tierra plana: autosync (silencios) -> voz editada + tl_plana.json para escenas.py."""
import sys, json
sys.path.insert(0, '/home/claude')
import autosync as A
A.setup('plana_phr', '/home/claude/narr_plana.mp3', tag='plana', GAP_IN=0.16, GAP_OUT=0.30, TEMPO=float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)
if sys.argv[1] == 'map':
    A.main(['', 'map'])
else:
    A.build_voice()
    ph = []
    for i, p in enumerate(A.anim.PH):
        st = p['starts'] + [p['b']]
        ph.append({'c': 'c0', 'i': i, 'a': p['a'], 'b': p['b'],
                   'words': [[w, st[k], st[k + 1]] for k, w in enumerate(p['words'])]})
    json.dump({'dur': A.NEWDUR, 'voice_end': A.PIECES[-1][-1][2], 'phrases': ph}, open('/home/claude/tl_plana.json', 'w'), ensure_ascii=False)
    print('dur', A.NEWDUR, 'voz', A.VOICE_LEN)
