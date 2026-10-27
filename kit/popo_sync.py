"""Video del Popocatépetl sincronizado con la narración (voz Carmelo), con autosync."""
import sys
sys.path.insert(0, '/home/claude')
import autosync as A

SPOKEN = {"72": "setentaydos", "42": "cuarentaydos", "18": "dieciocho", "100": "cien", "2023": "dosmilveintitres",
          "25": "veinticinco", "2": "dos", "UNAM": "unam"}
A.setup('popo', '/home/claude/narr_popo.mp3', tag='popo', SPOKEN=SPOKEN, GAP_IN=0.20, GAP_OUT=0.34)
fw, bw, NEWDUR, NF, VOICE_LEN = A.fw, A.bw, A.NEWDUR, A.NF, A.VOICE_LEN
W, H = A.V.W, A.V.H
render_new = A.render_new

if __name__ == '__main__':
    A.main(sys.argv)
