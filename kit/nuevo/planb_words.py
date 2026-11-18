"""Plan B de voz (Chatterbox, workflow voz_hq): arma la voz final y un words.json con el formato de Scribe.
El workflow solo da tiempos por LÍNEA ({text, start, end}); aquí se recorta cada línea por energía y sus palabras se
reparten por letras (las comas, los dos puntos y los «...» pesan como una pausa corta). Opcional: atempo (sin cambio
de tono) para acercar la duración a 61–75 s.

  python3 planb_words.py /ruta/narr_TEMA.mp3 /ruta/narr_TEMA.json /home/claude/narr_TEMA.mp3 /home/claude/words_TEMA.json [atempo]
"""
import json, re, subprocess, sys
import numpy as np

SR = 16000


def audio(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def recorta(x, a, b):
    """Inicio y fin reales de la voz dentro de [a, b] (energía por cuadros de 20 ms)."""
    i0, i1 = int(a * SR), int(b * SR)
    s = x[i0:i1]
    n = 320
    if len(s) < n * 3:
        return a, b
    fr = s[:len(s) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-6)
    thr = max(db.max() - 38, -50)
    on = np.where(db > thr)[0]
    if not len(on):
        return a, b
    return a + on[0] * n / SR, a + (on[-1] + 1) * n / SR


def main(mp3_in, js_in, mp3_out, words_out, atempo=1.0):
    atempo = float(atempo)
    if abs(atempo - 1) > 1e-3:
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', mp3_in, '-af', f'atempo={atempo}', '-ar', '44100', '-b:a', '192k',
                        mp3_out], check=True)
    else:
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', mp3_in, '-c', 'copy', mp3_out], check=True)
    d = json.load(open(js_in))
    x = audio(mp3_in)
    words = []
    for L in d['lines']:
        a, b = recorta(x, L['start'], L['end'])
        toks = L['text'].split()
        wts = []
        for w in toks:
            p = 0
            if re.search(r'(\.\.\.|…)$', w):
                p = 5
            elif re.search(r'[:;]$', w):
                p = 3
            elif re.search(r'[,.]$', w):
                p = 2
            wts.append((len(re.sub(r'[^\wáéíóúñü]', '', w.lower())) + 1, p))
        tot = sum(c + p for c, p in wts)
        t = a
        for w, (c, p) in zip(toks, wts):
            dur = (b - a) * c / tot
            words.append({'text': re.sub(r'(\.\.\.|…)', '', w), 'start': round(t / atempo, 3),
                          'end': round((t + dur) / atempo, 3), 'type': 'word'})
            t += dur + (b - a) * p / tot
    json.dump({'words': words, 'fuente': 'plan B Chatterbox, reparto por letras', 'atempo': atempo},
              open(words_out, 'w'), ensure_ascii=False)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3_out],
                               capture_output=True, text=True).stdout)
    print(f'ok {mp3_out} {dur:.1f} s · {len(words)} palabras · voz {words[0]["start"]:.2f}–{words[-1]["end"]:.2f} s')


if __name__ == '__main__':
    main(*sys.argv[1:])
