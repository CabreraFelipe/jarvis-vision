"""Optional local neural TTS. No download, network service, or audio files."""
import json,os,re,subprocess,sys,tempfile
from pathlib import Path

DEFAULT={'engine':'Sistema','model':''}
ENGINES=('Sistema','Piper local')
MODEL_RE=re.compile(r'[A-Za-z0-9_-]{1,100}\.onnx\Z')
MAX_TEXT=4000
MAX_AUDIO=24*1024*1024

def normalize(raw):
    if not isinstance(raw,dict):return dict(DEFAULT)
    engine=raw.get('engine');model=raw.get('model')
    return {'engine':engine if engine in ENGINES else 'Sistema',
            'model':model if isinstance(model,str) and MODEL_RE.fullmatch(model) else ''}

def load(path):
    try:return normalize(json.loads(Path(path).read_text(encoding='utf-8')))
    except (OSError,ValueError):return dict(DEFAULT)

def save(path,settings):
    path=Path(path);fd,tmp=tempfile.mkstemp(prefix='.voice-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(normalize(settings),f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def model_folder(base):
    return Path(base)/'modelos'/'piper'

def models(base):
    folder=model_folder(base)
    try:
        return sorted(p.name for p in folder.iterdir() if MODEL_RE.fullmatch(p.name) and p.is_file()
                      and not p.is_symlink() and Path(str(p)+'.json').is_file()
                      and not Path(str(p)+'.json').is_symlink())
    except OSError:return []

def model_info(base,name):
    if name not in models(base):raise ValueError('Elegí un modelo Piper local con sus archivos ONNX y JSON.')
    model=model_folder(base)/name;config=Path(str(model)+'.json')
    if config.stat().st_size>1024*1024:raise ValueError('Configuración Piper demasiado grande.')
    try:rate=json.loads(config.read_text(encoding='utf-8'))['audio']['sample_rate']
    except (ValueError,KeyError,TypeError) as e:raise ValueError('Configuración Piper inválida.') from e
    if type(rate) is not int or not 8000<=rate<=48000:raise ValueError('Frecuencia Piper inválida.')
    return model.resolve(),config.resolve(),rate

def synthesize(base,model,text):
    model,config,rate=model_info(base,model)
    text=' '.join(text.split())
    if not text:return b'',rate
    if len(text)>MAX_TEXT:raise ValueError('Respuesta demasiado larga para la síntesis experimental.')
    # Isolated Python: no working-directory modules, shell, text in arguments, or model download.
    # Piper receives UTF-8 text via stdin and returns PCM via stdout.
    cmd=[sys.executable,'-I','-X','utf8','-m','piper','-m',str(model),'-c',str(config),'--output-raw']
    options={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    try:
        result=subprocess.run(cmd,input=(text+'\n').encode('utf-8'),stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL,timeout=90,check=False,**options)
    except (OSError,subprocess.TimeoutExpired) as e:raise RuntimeError('Piper no disponible o tiempo agotado.') from e
    if result.returncode!=0:raise RuntimeError('Piper no pudo sintetizar. Comprobá instalación y modelo local.')
    raw=result.stdout
    if not raw or len(raw)%2 or len(raw)>MAX_AUDIO:raise ValueError('Audio Piper inválido o excesivo.')
    return raw,rate

def speak(base,settings,text):
    settings=normalize(settings)
    if settings['engine']=='Sistema':
        import voice
        return voice.speak(text)
    raw,rate=synthesize(base,settings['model'],text)
    if not raw:return
    import sounddevice as sd
    with sd.RawOutputStream(samplerate=rate,channels=1,dtype='int16') as out:
        out.write(raw)
