"""Optional offline faster-whisper, explicit short microphone turns only."""
import queue,time
from pathlib import Path
import numpy as np
import speech_input

RATE=16000
MAX_SECONDS=12
_model=None
_model_path=None

def local_model(base):
    path=Path(base)/'modelos'/'faster-whisper-small'
    # Require local tokenizer to avoid fetching a fallback.
    if not path.is_dir() or not all((path/n).is_file() for n in ('model.bin','config.json','tokenizer.json')):
        raise RuntimeError('Falta el modelo local faster-whisper-small completo. Consultá VOZ.txt.')
    return path.resolve()

def transcribe(base,pcm,rate,stop):
    global _model,_model_path
    if stop.is_set():return ''
    if type(rate) is not int or rate<8000 or rate>192000 or len(pcm)%2 or len(pcm)>rate*MAX_SECONDS*2:
        raise ValueError('Audio fuera de los límites de la prueba.')
    if not pcm:return ''
    audio=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768
    if np.max(np.abs(audio))<.005:return ''
    if rate!=RATE:
        from scipy.signal import resample_poly
        from math import gcd
        g=gcd(rate,RATE);audio=resample_poly(audio,RATE//g,rate//g).astype(np.float32)
    path=local_model(base)
    if _model is None or _model_path!=path:
        from faster_whisper import WhisperModel
        _model=WhisperModel(str(path),device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
        _model_path=path
    if stop.is_set():return ''
    segments,_=_model.transcribe(audio,language='es',task='transcribe',beam_size=3,
                                 vad_filter=True,condition_on_previous_text=False)
    parts=[]
    for segment in segments:
        if stop.is_set():return ''
        parts.append(segment.text.strip())
    return '' if stop.is_set() else ' '.join(p for p in parts if p)

def listen(base,settings,stop,seconds=6,on_ready=None,on_processing=None):
    import sounddevice as sd
    if stop.is_set():return ''
    local_model(base)
    import faster_whisper
    if type(seconds) is not int or not 1<=seconds<=MAX_SECONDS:raise ValueError('Duración de escucha inválida.')
    index=speech_input.resolve_device(sd,settings['device'])
    device=sd.query_devices(index,kind='input') if index is not None else sd.query_devices(kind='input')
    rate=int(device['default_samplerate'])
    if not 8000<=rate<=192000:raise ValueError('Frecuencia de micrófono no compatible.')
    chunks=queue.Queue(maxsize=64);overflow=False
    def callback(indata,frames,timing,status):
        nonlocal overflow
        if getattr(status,'input_overflow',False):overflow=True
        try:chunks.put_nowait(bytes(indata))
        except queue.Full:overflow=True
    data=[];size=0;limit=rate*seconds*2
    with sd.RawInputStream(device=index,samplerate=rate,blocksize=max(800,rate//10),dtype='int16',channels=1,callback=callback):
        if on_ready:on_ready()
        deadline=time.monotonic()+seconds
        while not stop.is_set() and size<limit and time.monotonic()<deadline:
            try:chunk=chunks.get(timeout=.1)
            except queue.Empty:continue
            take=chunk[:limit-size];data.append(take);size+=len(take)
    if stop.is_set():return ''
    if overflow:raise RuntimeError('Se perdieron muestras del micrófono. Probá otra entrada.')
    if on_processing:on_processing()
    return transcribe(base,b''.join(data),rate,stop)
