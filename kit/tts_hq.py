"""Voz natural gratis con Chatterbox Multilingual (Resemble AI, licencia MIT) dentro de GitHub Actions.
Jobs: tts_hq/<nombre>.json -> inbox/<nombre>.mp3 + inbox/<nombre>.json
{"text_file": "tts/x.txt", "ref": "default" | "ald" | "ruta/a/referencia.wav|mp3|m4a|ogg",
 "exaggeration": 0.5, "cfg": 0.5, "temperature": 0.8, "gap": 0.32, "seed": 7}
"""
import json, os, glob, subprocess, sys, io, zipfile, tarfile, time
import numpy as np

os.makedirs('inbox', exist_ok=True)
CACHE = os.path.expanduser('~/.cache/mente_tts')
os.makedirs(CACHE, exist_ok=True)


def load_audio(path, sr=24000):
    out = f'/tmp/ref_{abs(hash(path))}.wav'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), out], check=True)
    import soundfile as sf
    x, _ = sf.read(out)
    return x.astype(np.float32)


def ref_ald():
    """Referencia de voz mexicana de dominio público (dataset Ald, licencia Unlicense)."""
    p = os.path.join(CACHE, 'ref_ald.wav')
    if os.path.exists(p):
        return p
    from huggingface_hub import list_repo_files, hf_hub_download
    repo = 'rmcpantoja/Ald_Mexican_Spanish_speech_dataset'
    files = list_repo_files(repo, repo_type='dataset')
    print('archivos del dataset:', files[:30], len(files), flush=True)
    clips = []
    aud = sorted(f for f in files if f.lower().endswith(('.wav', '.flac', '.mp3', '.ogg')))
    if aud:
        for f in aud[5:40]:
            clips.append(load_audio(hf_hub_download(repo, f, repo_type='dataset')))
            if sum(len(c) for c in clips) > 24000 * 14:
                break
    else:
        arch = [f for f in files if f.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz', '.parquet'))]
        print('archivos comprimidos:', arch[:10], flush=True)
        f = arch[0]
        lp = hf_hub_download(repo, f, repo_type='dataset')
        tmpd = '/tmp/ald'
        os.makedirs(tmpd, exist_ok=True)
        if f.endswith('.parquet'):
            import pandas as pd
            df = pd.read_parquet(lp)
            col = [c for c in df.columns if 'audio' in c.lower()][0]
            for i in range(5, 40):
                b = df[col].iloc[i]['bytes']
                fp = f'{tmpd}/c{i}.wav'
                open(fp, 'wb').write(b)
                clips.append(load_audio(fp))
                if sum(len(c) for c in clips) > 24000 * 14:
                    break
        else:
            if f.endswith('.zip'):
                zipfile.ZipFile(lp).extractall(tmpd)
            else:
                tarfile.open(lp).extractall(tmpd)
            wavs = sorted(glob.glob(tmpd + '/**/*.wav', recursive=True))
            for w in wavs[5:40]:
                clips.append(load_audio(w))
                if sum(len(c) for c in clips) > 24000 * 14:
                    break
    gap = np.zeros(int(0.25 * 24000), np.float32)
    x = np.concatenate([np.concatenate([c, gap]) for c in clips])[:24000 * 15]
    import soundfile as sf
    sf.write(p, x, 24000)
    return p


def main():
    jobs = [j for j in sorted(glob.glob('tts_hq/*.json')) if not os.path.exists('inbox/' + os.path.splitext(os.path.basename(j))[0] + '.mp3')]
    if not jobs:
        print('nada que hacer'); return
    import torch
    _orig = torch.load
    torch.load = lambda *a, **k: _orig(*a, **{**k, 'map_location': torch.device('cpu')})
    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    t0 = time.time()
    model = ChatterboxMultilingualTTS.from_pretrained(device='cpu')
    print('modelo cargado en', round(time.time() - t0), 's', flush=True)
    sr = model.sr
    for jf in jobs:
        name = os.path.splitext(os.path.basename(jf))[0]
        job = json.load(open(jf))
        try:
            text = job.get('text') or open(job['text_file'], encoding='utf-8').read()
            ref = job.get('ref', 'default')
            refp = None if ref == 'default' else (ref_ald() if ref == 'ald' else ref)
            if refp and not refp.endswith('.wav'):
                conv = f'/tmp/{name}_ref.wav'
                subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', refp, '-ac', '1', '-ar', '24000', conv], check=True)
                refp = conv
            torch.manual_seed(int(job.get('seed', 7)))
            parts, lines = [], []
            gap = np.zeros(int(float(job.get('gap', 0.32)) * sr), np.float32)
            t = 0.0
            for line in [l.strip() for l in text.split('\n') if l.strip()]:
                t1 = time.time()
                kw = dict(language_id='es', exaggeration=float(job.get('exaggeration', 0.5)), cfg_weight=float(job.get('cfg', 0.5)))
                if 'temperature' in job:
                    kw['temperature'] = float(job['temperature'])
                if refp:
                    kw['audio_prompt_path'] = refp
                w = model.generate(line, **kw).squeeze().cpu().numpy().astype(np.float32)
                lines.append({'text': line, 'start': round(t, 3), 'end': round(t + len(w) / sr, 3)})
                t += (len(w) + len(gap)) / sr
                parts += [w, gap]
                print(f'  {len(w) / sr:.1f}s en {time.time() - t1:.0f}s: {line[:50]}', flush=True)
            x = np.concatenate(parts)
            x = x / max(1e-6, float(np.abs(x).max())) * 0.9
            wav = f'/tmp/{name}.wav'
            ta.save(wav, torch.from_numpy(x).unsqueeze(0), sr)
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-ar', '44100', '-b:a', '160k', f'inbox/{name}.mp3'], check=True)
            json.dump({'ok': True, 'dur': len(x) / sr, 'lines': lines, **job}, open(f'inbox/{name}.json', 'w'), ensure_ascii=False)
            print('ok', name, round(len(x) / sr, 1), 's', flush=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            json.dump({'ok': False, 'error': repr(e), **job}, open(f'inbox/{name}.json', 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
