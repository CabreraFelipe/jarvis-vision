"""Read-only diagnostics: no camera or microphone opening and no remote requests."""
import importlib.metadata
import json
import shutil
import sys
import urllib.request
from pathlib import Path

PACKAGES=('opencv-python','Pillow','ultralytics','vosk','sounddevice','pyttsx3','piper-tts')
LIMIT=1024*1024

def package_version(name):
    try: return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: return 'No instalado'

def ollama_status(model='gemma3:4b'):
    try:
        class LocalOnly(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs): raise ValueError('Redirección no permitida')
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),LocalOnly())
        with opener.open('http://127.0.0.1:11434/api/tags',timeout=3) as r:
            raw=r.read(LIMIT+1)
        if len(raw)>LIMIT: raise ValueError('Respuesta excesiva')
        tags=json.loads(raw)['models']
        found=any(isinstance(x,dict) and model in (x.get('name'),x.get('model')) for x in tags)
        return 'Disponible', 'Instalado' if found else 'No encontrado'
    except (OSError,ValueError,KeyError,TypeError):
        return 'No disponible o respuesta inválida','No comprobado'

def collect(base,version):
    base=Path(base)
    result=[('JARVIS',version),('Python',sys.version.split()[0])]
    result.extend((name,package_version(name)) for name in PACKAGES)
    service,model=ollama_status()
    result.extend([('Ollama local',service),('gemma3:4b',model),
        ('Modelo YOLO','Presente' if (base/'yolo11n.pt').is_file() else 'No encontrado'),
        ('Modelo Vosk español','Presente' if (base/'modelos'/'vosk-model-small-es-0.42').is_dir() else 'No encontrado'),
        ('GitHub CLI','Detectado en PATH' if shutil.which('gh') else 'No detectado'),
        ('Memoria local','Existe' if (base/'jarvis_memory.sqlite3').is_file() else 'Sin base creada')])
    return result
