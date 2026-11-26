"""Offline evaluation of the existing Vosk wake parser on explicitly selected WAV files.
No microphone, uploads, transcript logging, or persisted output. Requires local Vosk model.
Run from repository root: python tools/wake_benchmark.py --model PATH --positive PATH --negative PATH
"""
import argparse
import json
import sys
import wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from voice import WakeCommand

def evaluate_clip(path, recognizer_factory, allow_bare=False):
    gate=WakeCommand(allow_bare=allow_bare)
    with wave.open(str(path),'rb') as audio:
        rate=audio.getframerate()
        if audio.getnchannels()!=1 or audio.getsampwidth()!=2 or audio.getcomptype()!='NONE' or not 8000<=rate<=48000:
            raise ValueError('WAV requerido: PCM mono 16 bits, 8–48 kHz.')
        if audio.getnframes()>rate*600:
            raise ValueError('Máximo 10 minutos por clip.')
        rec=recognizer_factory(rate)
        count=0
        def feed(raw):
            text=json.loads(raw).get('text','')
            command=gate.feed(text,count/rate)
            return bool(command or gate.until is not None)
        while True:
            data=audio.readframes(max(1,rate//10))
            if not data: break
            count+=len(data)//2
            if rec.AcceptWaveform(data) and feed(rec.Result()): return True
        return feed(rec.FinalResult())

def report(positive,negative,detect):
    if not positive or not negative: raise ValueError('Se requieren clips positivos y negativos.')
    hits=sum(bool(detect(p)) for p in positive)
    false_hits=sum(bool(detect(p)) for p in negative)
    return {'positive_clips':len(positive),'detected':hits,'missed':len(positive)-hits,
            'negative_clips':len(negative),'false_activation_clips':false_hits,
            'recall':hits/len(positive),'false_positive_clip_rate':false_hits/len(negative)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',required=True,type=Path)
    p.add_argument('--positive',nargs='+',required=True,type=Path)
    p.add_argument('--negative',nargs='+',required=True,type=Path)
    p.add_argument('--allow-bare',action='store_true')
    a=p.parse_args()
    if not a.model.is_dir(): p.error('Modelo Vosk local no encontrado.')
    positive=[x.resolve() for x in a.positive]; negative=[x.resolve() for x in a.negative]
    if len(set(positive+negative))!=len(positive+negative): p.error('No repetir clips entre grupos ni dentro de ellos.')
    from vosk import Model,KaldiRecognizer,SetLogLevel
    SetLogLevel(-1); model=Model(str(a.model))
    try:
        result=report(positive,negative,lambda path:evaluate_clip(path,lambda rate:KaldiRecognizer(model,rate),a.allow_bare))
    except (OSError,ValueError,wave.Error):
        p.error('No se pudo procesar un WAV local; revisar formato y acceso.')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
