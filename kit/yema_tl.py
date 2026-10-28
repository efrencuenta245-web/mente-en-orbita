"""Tiempos del reel de la yema: autosync (silencios) -> voz editada + tl_yema.json para escenas.py."""
import sys, json, os
sys.path.insert(0, '/home/claude')
import autosync as A
A.setup('yema_phr', '/home/claude/narr_yema.mp3', tag='yema', GAP_IN=float(os.environ.get('GI','0.16')), GAP_OUT=float(os.environ.get('GO','0.30')), TEMPO=float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)
if sys.argv[1] == 'map':
    A.main(['', 'map'])
else:
    A.build_voice()
    ph = []
    for i, p in enumerate(A.anim.PH):
        st = p['starts'] + [p['b']]
        ph.append({'c': 'c0', 'i': i, 'a': p['a'], 'b': p['b'],
                   'words': [[w, st[k], st[k + 1]] for k, w in enumerate(p['words'])]})
    json.dump({'dur': A.NEWDUR, 'voice_end': A.PIECES[-1][-1][2], 'phrases': ph}, open('/home/claude/tl_yema.json', 'w'), ensure_ascii=False)
    print('dur', A.NEWDUR, 'voz', A.VOICE_LEN)
