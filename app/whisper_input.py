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


class Utterance:
    """Energy-based candidate segmentation; not a dedicated acoustic wake model."""
    def __init__(self,rate,threshold=.012):
        from collections import deque
        self.rate=rate;self.threshold=threshold;self.pre=deque(maxlen=3)
        self.parts=[];self.samples=0;self.voiced=0;self.quiet=0;self.active=False
    def feed(self,chunk):
        if not chunk or len(chunk)%2:return False
        samples=np.frombuffer(chunk,dtype='<i2').astype(np.float32)/32768
        loud=float(np.sqrt(np.mean(samples*samples)))>=self.threshold
        n=len(samples)
        if not self.active:
            if not loud:self.pre.append(chunk);return False
            self.active=True;self.parts=list(self.pre);self.samples=sum(len(p)//2 for p in self.parts)
            self.pre.clear()
        remaining=max(0,self.rate*6-self.samples)
        if n>remaining:chunk=chunk[:remaining*2];n=remaining
        self.parts.append(chunk);self.samples+=n
        if loud:self.voiced+=n;self.quiet=0
        else:self.quiet+=n
        return self.samples>=self.rate*6 or self.quiet>=self.rate*.7
    def finish(self):
        return b''.join(self.parts) if self.voiced>=self.rate*.2 else b''

def capture_utterance(sd,index,rate,stop,*,idle_seconds=None,on_ready=None):
    chunks=queue.Queue(maxsize=64);overflow=False;segment=Utterance(rate)
    def callback(indata,frames,timing,status):
        nonlocal overflow
        if getattr(status,'input_overflow',False):overflow=True
        try:chunks.put_nowait(bytes(indata))
        except queue.Full:overflow=True
    with sd.RawInputStream(device=index,samplerate=rate,blocksize=max(800,rate//10),dtype='int16',channels=1,callback=callback):
        if on_ready:on_ready()
        deadline=None if idle_seconds is None else time.monotonic()+max(0,idle_seconds)
        while not stop.is_set():
            if overflow:raise RuntimeError('Se perdieron muestras del micrófono. Probá otra entrada.')
            if deadline is not None and time.monotonic()>=deadline:break
            try:chunk=chunks.get(timeout=.1)
            except queue.Empty:continue
            if segment.feed(chunk):break
    if stop.is_set():return b''
    if overflow:raise RuntimeError('Se perdieron muestras del micrófono. Probá otra entrada.')
    return segment.finish()

def listen_wake(base,settings,stop,on_state=None,*,allow_bare=False):
    """Opt-in Whisper activation. Close mic during inference; no overlapping windows."""
    import sounddevice as sd
    import faster_whisper
    from voice import WakeCommand
    if stop.is_set():return ''
    local_model(base)
    index=speech_input.resolve_device(sd,settings['device'])
    device=sd.query_devices(index,kind='input') if index is not None else sd.query_devices(kind='input')
    rate=int(device['default_samplerate'])
    if not 8000<=rate<=192000:raise ValueError('Frecuencia de micrófono no compatible.')
    gate=WakeCommand(allow_bare=allow_bare)
    prompt='Whisper experimental · esperando Hola, JARVIS'
    while not stop.is_set():
        now=time.monotonic();gate.expire(now)
        active=gate.until is not None
        idle=max(0,gate.until-now) if active else None
        if on_state:
            status='JARVIS activado · decí tu pregunta' if active else prompt
            on_ready=lambda:on_state(status+' · micrófono activo: '+str(device['name']))
        else:on_ready=None
        pcm=capture_utterance(sd,index,rate,stop,idle_seconds=idle,on_ready=on_ready)
        if stop.is_set():return ''
        if not pcm:
            gate.expire(time.monotonic());continue
        if on_state:on_state('Whisper local · transcribiendo; micrófono pausado')
        captured_at=time.monotonic()
        text=transcribe(base,pcm,rate,stop).lstrip('¿¡ ')
        if stop.is_set():return ''
        # Speech arrived before inference; do not consume the command window while decoding.
        command=gate.feed(text,captured_at if active else time.monotonic())
        if command:return command
        if on_state and text and gate.until is None:on_state('En espera · Whisper entendió: «'+text[:140]+'»')
    return ''
