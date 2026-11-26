"""Read-only diagnostics: no camera or microphone opening and no remote requests."""
import importlib.metadata
import json
import shutil
import sys
import struct
import voice_output
import urllib.request
from pathlib import Path

PACKAGES=('opencv-python','Pillow','ultralytics','vosk','sounddevice','pyttsx3','faster-whisper','scipy','piper-tts')
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

VOICE_COMMANDS=(
    ('Vosk y voz Sistema', '-m pip install vosk sounddevice pyttsx3'),
    ('Whisper', '-m pip install --only-binary=:all: faster-whisper scipy'),
    ('Piper', '-m pip install --only-binary=:all: piper-tts'),
    ('Verificar dependencias', '-m pip check'),
)

def powershell_quote(value):
    return "'" + str(value).replace("'", "''") + "'"

def voice_install_commands(executable=None):
    """Return inert commands for explicit execution by the user, never run pip."""
    executable=Path(executable or sys.executable)
    if executable.name.casefold()=='pythonw.exe':
        executable=executable.with_name('python.exe')
    prefix='& '+powershell_quote(executable)+' -I '
    return [(label,prefix+args) for label,args in VOICE_COMMANDS]

def runtime_rows(base):
    base=Path(base)
    bits=struct.calcsize('P')*8
    tested=sys.version_info[:2]==(3,12) and bits==64
    whisper=base/'modelos'/'faster-whisper-small'
    present=all((whisper/n).is_file() for n in ('model.bin','config.json','tokenizer.json'))
    voices=voice_output.models(base)
    return [('Ejecutable Python',sys.executable),
            ('Arquitectura Python',str(bits)+' bits'),
            ('Entorno virtual','Sí' if sys.prefix!=sys.base_prefix else 'No'),
            ('Base de compatibilidad','Python 3.12 x64 (CI)' if tested else 'Fuera de la base 3.12 x64 comprobada'),
            ('Modelo Vosk completo','Carpeta presente' if (base/'modelos'/'vosk-model-es-0.42').is_dir() else 'No encontrado'),
            ('Modelo Whisper small','Archivos mínimos presentes' if present else 'Faltan archivos'),
            ('Modelos Piper','%d pares ONNX + JSON presentes'%len(voices))]

def collect(base,version):
    base=Path(base)
    result=[('JARVIS',version),('Python',sys.version.split()[0])]
    result.extend(runtime_rows(base))
    result.extend((name,package_version(name)) for name in PACKAGES)
    service,model=ollama_status()
    result.extend([('Ollama local',service),('gemma3:4b',model),
        ('Modelo YOLO','Presente' if (base/'yolo11n.pt').is_file() else 'No encontrado'),
        ('Modelo Vosk español','Presente' if (base/'modelos'/'vosk-model-small-es-0.42').is_dir() else 'No encontrado'),
        ('GitHub CLI','Detectado en PATH' if shutil.which('gh') else 'No detectado'),
        ('Memoria local','Existe' if (base/'jarvis_memory.sqlite3').is_file() else 'Sin base creada')])
    return result
