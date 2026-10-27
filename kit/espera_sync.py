"""Video de la espera tras la vasectomía sincronizado con la narración (voz Carmelo), con autosync."""
import sys
sys.path.insert(0, '/home/claude')
import autosync as A

SPOKEN = {"3": "tres", "20": "veinte", "8": "ocho"}
A.setup('espera', '/home/claude/narr_espera_full.wav', tag='espera', SPOKEN=SPOKEN, GAP_IN=0.30, GAP_OUT=0.55)
fw, bw, NEWDUR, NF, VOICE_LEN = A.fw, A.bw, A.NEWDUR, A.NF, A.VOICE_LEN
W, H = A.V.W, A.V.H
render_new = A.render_new

if __name__ == '__main__':
    A.main(sys.argv)
