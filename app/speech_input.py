"""Local speech input preferences. No audio or transcript storage."""
import json,os,tempfile
from pathlib import Path
MODELS={'Ligero':'vosk-model-small-es-0.42','Completo':'vosk-model-es-0.42'}
DEFAULT={'model':'Ligero','device':None}
MANUAL_MODELS=tuple(MODELS)+('Whisper small',)
def normalize(raw):
    raw=raw if isinstance(raw,dict) else {}
    model=raw.get('model');device=raw.get('device')
    if not isinstance(device,dict) or type(device.get('index')) is not int or device['index']<0 or not isinstance(device.get('name'),str) or not isinstance(device.get('host'),str):
        device=None
    else:device={k:device[k] for k in ('index','name','host')}
    result={'model':model if isinstance(model,str) and model in MANUAL_MODELS else 'Ligero','device':device}
    if result['model']=='Whisper small' and raw.get('wake')=='Whisper experimental':result['wake']='Whisper experimental'
    return result
def load(path):
    try:return normalize(json.loads(Path(path).read_text(encoding='utf-8')))
    except (OSError,ValueError):return dict(DEFAULT)
def save(path,value):
    path=Path(path);fd,tmp=tempfile.mkstemp(prefix='.speech-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(normalize(value),f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def inputs(sd):
    hosts=sd.query_hostapis()
    return [{'index':i,'name':str(d['name']),'host':str(hosts[d['hostapi']]['name'])}
            for i,d in enumerate(sd.query_devices()) if d['max_input_channels']>0]
def resolve_device(sd,saved):
    if saved is None:return None
    choices=inputs(sd)
    if saved in choices:return saved['index']
    matches=[d for d in choices if (d['name'],d['host'])==(saved['name'],saved['host'])]
    if len(matches)==1:return matches[0]['index']
    raise RuntimeError('Micrófono guardado no disponible o ambiguo. Elegí nuevamente la entrada en Herramientas.')
def model_path(base,model):
    return Path(base)/'modelos'/('faster-whisper-small' if model=='Whisper small' else MODELS[model])
