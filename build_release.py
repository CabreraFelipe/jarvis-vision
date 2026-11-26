"""Build protocol-1 release artifacts from an explicit allowlist, no user data."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FILES='jarvis_vision.py assistant_core.py test_core.py camera.py voice.py conversation.py vision.py requirements.txt requirements-voice.txt INICIAR.bat INSTALAR.bat INSTALAR_VOZ.bat LEEME.txt PRUEBAS.txt VOZ.txt test_jarvis.py test_ui.py test_v04.py test_voice_ui.py test_wake041.py'.split()
def build(repo,out):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo): raise ValueError('Invalid repository')
    v=(ROOT/'VERSION').read_text().strip()
    if not re.fullmatch(r'(0|[1-9]\d{0,4})\.(0|[1-9]\d{0,4})\.(0|[1-9]\d{0,4})',v): raise ValueError('Invalid version')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    files={n:(ROOT/'app'/n).read_bytes() for n in FILES}
    if f"VERSION='{v}'".encode() not in files['jarvis_vision.py']:raise ValueError('Version mismatch')
    for n,data in files.items():
        if n.endswith('.py'):compile(data,n,'exec')
    manifest={'product':'jarvis-vision','protocol':1,'version':v,'files':{n:hashlib.sha256(data).hexdigest() for n,data in files.items()}}
    name=f'JARVIS_Vision_V{v}.zip'; package=out/name
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        def write(name,data):
            info=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3; info.external_attr=0o100644 << 16
            z.writestr(info,data)
        write('release.json',json.dumps(manifest,indent=2))
        for n,data in files.items():write('app/'+n,data)
    feed={'product':'jarvis-vision','protocol':1,'version':v,'url':f'https://github.com/{repo}/releases/download/v{v}/{name}','sha256':hashlib.sha256(package.read_bytes()).hexdigest()}
    (out/'feed.json').write_text(json.dumps(feed,indent=2)+'\n',encoding='utf-8')
    return package,feed
if __name__=='__main__':print(build(sys.argv[1],sys.argv[2]))
