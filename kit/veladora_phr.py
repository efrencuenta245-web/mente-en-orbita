"""Frases del reel de la veladora para autosync (solo tiempos; las escenas están en veladora.py)."""
import anim
TXT = [l.strip() for l in open('/home/claude/mente-en-orbita/guiones/2026-10-30_veladora_voz.txt', encoding='utf-8') if l.strip()]
_t, PHR = 0.3, []
for s in TXT:
    d = len(s) * 0.068
    PHR.append((_t, _t + d, s, set()))
    _t += d + 0.5
DUR = _t + 2.0
CUTS, ENVS, T_OUT = (), ('x',), DUR
anim.PHR = PHR
anim.PH = anim.build_phrases()
W, H = anim.W, anim.H
def render(t):
    return None
