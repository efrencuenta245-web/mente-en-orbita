"""Video de autos de rally sincronizado con la narración (voz Carmelo), con autosync."""
import sys
sys.path.insert(0, '/home/claude')
import autosync as A

SPOKEN = {"170": "cientosetenta", "km/h": "kilometrosporhora", "50": "cincuenta", "5": "cinco", "2,700": "dosmilsetecientos",
          "20": "veinte", "%": "porciento"}
A.setup('rally', '/home/claude/narr_rally.mp3', tag='rally', SPOKEN=SPOKEN, TEMPO=0.96, GAP_IN=0.26, GAP_OUT=0.85)
fw, bw, NEWDUR, NF, VOICE_LEN = A.fw, A.bw, A.NEWDUR, A.NF, A.VOICE_LEN
W, H = A.V.W, A.V.H
render_new = A.render_new

if __name__ == '__main__':
    A.main(sys.argv)
