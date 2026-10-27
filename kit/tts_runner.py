"""Genera narraciones con voces de código abierto dentro de GitHub Actions.
Lee tts/*.json  ->  escribe inbox/<nombre>.mp3  (y inbox/<nombre>.json con info).
Formato del job: {"engine": "piper"|"kokoro", "voice": "...", "text_file": "tts/x.txt" o "text": "...",
                  "speed": 1.0, "lang": "es" (kokoro), "gap": 0.35}
"""
import json, os, glob, subprocess, wave, sys, urllib.request
import numpy as np

CACHE = os.path.expanduser('~/.cache/mente_tts')
os.makedirs(CACHE, exist_ok=True)
os.makedirs('inbox', exist_ok=True)


def dl(url, name):
    p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        print('descargando', url, flush=True)
        urllib.request.urlretrieve(url, p)
    return p


PIPER = {
    'es_MX-claude-high': 'es/es_MX/claude/high',
    'es_MX-ald-medium': 'es/es_MX/ald/medium',
    'es_ES-davefx-medium': 'es/es_ES/davefx/medium',
}


def piper_tts(text, voice, speed, gap):
    from piper import PiperVoice
    base = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/' + PIPER[voice] + '/' + voice
    m = dl(base + '.onnx', voice + '.onnx')
    dl(base + '.onnx.json', voice + '.onnx.json')
    try:
        card = dl('https://huggingface.co/rhasspy/piper-voices/resolve/main/' + PIPER[voice] + '/MODEL_CARD', voice + '.card')
        print(open(card).read()[:600])
    except Exception as e:
        print('sin MODEL_CARD', e)
    v = PiperVoice.load(m)
    sr = v.config.sample_rate
    out = []
    for line in [l.strip() for l in text.split('\n') if l.strip()]:
        pcm = []
        try:  # piper-tts >= 1.3
            from piper import SynthesisConfig
            cfg = SynthesisConfig(length_scale=1.0 / speed)
            for ch in v.synthesize(line, syn_config=cfg):
                pcm.append(ch.audio_int16_array)
        except ImportError:
            import io
            bio = io.BytesIO()
            with wave.open(bio, 'wb') as wf:
                v.synthesize(line, wf, length_scale=1.0 / speed)
            bio.seek(44)
            pcm.append(np.frombuffer(bio.read(), np.int16))
        out.append(np.concatenate(pcm).astype(np.float32) / 32768)
        out.append(np.zeros(int(gap * sr), np.float32))
    return np.concatenate(out), sr


def kokoro_tts(text, voice, speed, gap, lang):
    from kokoro_onnx import Kokoro
    rel = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
    k = Kokoro(dl(rel + 'kokoro-v1.0.onnx', 'kokoro-v1.0.onnx'), dl(rel + 'voices-v1.0.bin', 'voices-v1.0.bin'))
    out, sr = [], 24000
    for line in [l.strip() for l in text.split('\n') if l.strip()]:
        s, sr = k.create(line, voice=voice, speed=speed, lang=lang)
        out.append(np.asarray(s, np.float32))
        out.append(np.zeros(int(gap * sr), np.float32))
    return np.concatenate(out), sr


def main():
    for jf in sorted(glob.glob('tts/*.json')):
        name = os.path.splitext(os.path.basename(jf))[0]
        if os.path.exists(f'inbox/{name}.mp3'):
            continue
        job = json.load(open(jf))
        text = job.get('text') or open(job['text_file'], encoding='utf-8').read()
        eng, voice = job['engine'], job['voice']
        speed, gap = float(job.get('speed', 1.0)), float(job.get('gap', 0.35))
        try:
            if eng == 'piper':
                x, sr = piper_tts(text, voice, speed, gap)
            elif eng == 'kokoro':
                x, sr = kokoro_tts(text, voice, speed, gap, job.get('lang', 'es'))
            else:
                raise ValueError('motor desconocido ' + eng)
            x = x / max(1e-6, float(np.abs(x).max())) * 0.9
            wav = f'/tmp/{name}.wav'
            with wave.open(wav, 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes((x * 32767).astype(np.int16).tobytes())
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-ar', '44100', '-b:a', '160k', f'inbox/{name}.mp3'], check=True)
            json.dump({'ok': True, 'dur': len(x) / sr, **job}, open(f'inbox/{name}.json', 'w'), ensure_ascii=False)
            print('ok', name, round(len(x) / sr, 2), 's', flush=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            json.dump({'ok': False, 'error': repr(e), **job}, open(f'inbox/{name}.json', 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
