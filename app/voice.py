"""Optional offline voice: explicit 6-second microphone recording, no audio files."""
import json
import os
import queue
import time
from pathlib import Path
import speech_input

MODEL_DIR=Path(os.environ.get('JARVIS_DATA_DIR',str(Path(__file__).resolve().parent))) /'modelos'/'vosk-model-small-es-0.42'
_model=None
_model_path=None

def recognizer_input(sd,Model,KaldiRecognizer,settings,base):
    global _model,_model_path
    settings=speech_input.normalize(settings)
    path=speech_input.model_path(base,settings['model']) if base is not None else (MODEL_DIR if settings['model']=='Ligero' else MODEL_DIR.with_name(speech_input.MODELS['Completo']))
    if not path.is_dir():raise RuntimeError('Falta el modelo español '+settings['model']+'. Revisá Herramientas > Micrófono y reconocimiento.')
    index=speech_input.resolve_device(sd,settings['device'])
    device=sd.query_devices(index,kind='input') if index is not None else sd.query_devices(kind='input')
    rate=int(device['default_samplerate'])
    if _model is None or _model_path!=path:
        _model=Model(str(path));_model_path=path
    return KaldiRecognizer(_model,rate),rate,index,str(device['name'])

class SpeechTurn:
    """Accumulate recognized segments; optionally finish at the first nonempty endpoint."""
    def __init__(self, recognizer, end_on_phrase=False):
        self.recognizer=recognizer
        self.end_on_phrase=end_on_phrase
        self.parts=[]
        self.finished=False
    def feed(self,data):
        if self.finished: return True
        if self.recognizer.AcceptWaveform(data):
            text=json.loads(self.recognizer.Result()).get('text','').strip()
            if text:
                self.parts.append(text)
                self.finished=self.end_on_phrase
        return self.finished
    def finish(self,cancelled=False):
        if cancelled: return ''
        if not self.finished:
            text=json.loads(self.recognizer.FinalResult()).get('text','').strip()
            if text: self.parts.append(text)
            self.finished=True
        return ' '.join(self.parts)

def listen(stop, seconds=6, on_ready=None, *, end_on_phrase=False, settings=None, base=None):
    global _model
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
    if stop.is_set(): return ''
    rec,rate,index,device_name=recognizer_input(sd,Model,KaldiRecognizer,settings,base)
    if stop.is_set(): return ''
    chunks=queue.Queue(maxsize=64); turn=SpeechTurn(rec,end_on_phrase)
    def callback(indata,frames,timing,status):
        try: chunks.put_nowait(bytes(indata))
        except queue.Full: pass
    with sd.RawInputStream(device=index,samplerate=rate,blocksize=max(800,rate//10),dtype='int16',channels=1,callback=callback):
        if on_ready: on_ready()
        end=time.monotonic()+seconds
        while time.monotonic()<end and not stop.is_set():
            try: data=chunks.get(timeout=.15)
            except queue.Empty: continue
            if turn.feed(data): break
    return turn.finish(stop.is_set())

def speak(text):
    import pyttsx3
    engine=pyttsx3.init()
    try:
        for v in engine.getProperty('voices'):
            info=(str(v.id)+' '+str(v.name)+' '+str(v.languages)).lower()
            if any(x in info for x in ('spanish','español','es-es','es-mx','es-uy','es-ar','es_','es-')):
                engine.setProperty('voice',v.id); break
        engine.say(text); engine.runAndWait()
    finally: engine.stop()

# The wake phrase is detected by local speech transcription, not a specialized
# wake-word model. Recognition may vary with microphone and accent.
import re
import unicodedata

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c))

# Explicit phonetic variants, not unrestricted fuzzy matching.
# Bare-name activation is optional and accepts only a narrower set.
NAME=r'(?:jarvis|yarvis|llarvis|charvis|jarbis|yarbis|yervis|jervis|harvis|arvis|llarbis|charbis|y arvis|(?:jar|yar|llar|char|har|jer|yer)[\s-]+(?:vis|bis)|asistente)'
BOUNDARY=r'(?=$|[\s,.:;!?¿¡])'
WAKE=re.compile(r'^\s*hola[\s,.:;!?¿¡]+'+NAME+BOUNDARY,re.I)
SPLIT=re.compile(r'^\s*'+NAME+BOUNDARY,re.I)
BARE=re.compile(r'^(?:jarvis|yarvis|llarvis|jarbis|yarbis|jar[\s-]+vis|yar[\s-]+vis)$',re.I)
FIRST=r'(?:jar|yar|llar|char|har|jer|yer)'
PARTIAL_HELLO=re.compile(r'^hola[\s,.:;!?¿¡]+'+FIRST+r'$',re.I)
PARTIAL_NAME=re.compile(r'^'+FIRST+r'$',re.I)
SUFFIX=re.compile(r'^(?:vis|bis)'+BOUNDARY,re.I)
PUNCT=' ,.!?¿¡:;'
class WakeCommand:
    def __init__(self,timeout=8,*,allow_bare=False):
        self.timeout=timeout; self.allow_bare=allow_bare
        self.until=None; self.hola_until=None; self.partial_until=None
    def feed(self,text,now):
        text=unicodedata.normalize('NFC',text.strip()); self.expire(now)
        normalized=normalize(text)
        trimmed=normalized.strip(PUNCT)
        match=WAKE.search(normalized)
        if not match and self.hola_until is not None:
            match=SPLIT.search(normalized)
        if not match and self.partial_until is not None:
            match=SUFFIX.search(normalized)
        was_hello=self.hola_until is not None
        self.hola_until=None; self.partial_until=None
        if match:
            command=text[match.end():].strip(PUNCT)
            if command: self.until=None; return command
            self.until=now+self.timeout; return None
        if self.allow_bare and BARE.fullmatch(trimmed):
            self.until=now+self.timeout; return None
        if self.until is not None and text:
            self.until=None; return text
        if PARTIAL_HELLO.fullmatch(trimmed) or (was_hello and PARTIAL_NAME.fullmatch(trimmed)):
            self.partial_until=now+2
        elif trimmed=='hola':
            self.hola_until=now+2
        return None
    def expire(self,now):
        if self.hola_until is not None and now>=self.hola_until: self.hola_until=None
        if self.partial_until is not None and now>=self.partial_until: self.partial_until=None
        if self.until is not None and now>=self.until: self.until=None; return True
        return False

def listen_wake(stop,on_state=None,*,allow_bare=False,settings=None,base=None):
    global _model
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
    if stop.is_set(): return ''
    rec,rate,index,device_name=recognizer_input(sd,Model,KaldiRecognizer,settings,base)
    if stop.is_set(): return ''
    chunks=queue.Queue(maxsize=32); gate=WakeCommand(allow_bare=allow_bare)
    def callback(indata,frames,timing,status):
        try: chunks.put_nowait(bytes(indata))
        except queue.Full: pass
    with sd.RawInputStream(device=index,samplerate=rate,blocksize=max(800,rate//10),dtype='int16',channels=1,callback=callback):
        prompt='En espera de «Hola, JARVIS» o «Hola, asistente»'+(' o «JARVIS» solo' if allow_bare else '')
        if on_state: on_state(prompt+' · micrófono activo: '+device_name)
        while not stop.is_set():
            now=time.monotonic()
            if gate.expire(now) and on_state: on_state('Tiempo agotado · '+prompt)
            try: data=chunks.get(timeout=.15)
            except queue.Empty: continue
            if rec.AcceptWaveform(data):
                text=json.loads(rec.Result()).get('text',''); was=gate.until
                command=gate.feed(text,time.monotonic())
                if command: return '' if stop.is_set() else command
                if on_state and text:
                    if gate.until is not None and gate.until!=was: on_state('JARVIS activado · decí tu pregunta (8 s)')
                    else: on_state('En espera · Vosk entendió: «'+text[:140]+'»')
    return ''
