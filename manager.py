"""JARVIS secure manager candidate. Protocol 1 packages with verified GitHub provenance."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, zipfile
from contextlib import contextmanager
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlparse

PROTOCOL=1
TRUSTED_REPO='CabreraFelipe/jarvis-vision'
TRUSTED_FEED=f'https://github.com/{TRUSTED_REPO}/releases/latest/download/feed.json'
TRUSTED_WORKFLOW=f'{TRUSTED_REPO}/.github/workflows/release.yml@refs/heads/main'
MIN_GH_VERSION=(2,102,0)
MAX_ZIP=50*1024*1024
MAX_FILE=20*1024*1024
MAX_MANIFEST=128*1024
APP_EXIT=42
VERSION_RE=re.compile(r'(0|[1-9]\d{0,4})\.(0|[1-9]\d{0,4})\.(0|[1-9]\d{0,4})\Z')
NAME_RE=re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,100}\.(py|txt|bat|json)\Z')
SHA_RE=re.compile(r'[0-9a-f]{64}\Z')
REQUIRED={'jarvis_vision.py','camera.py','voice.py','conversation.py','vision.py','requirements.txt','requirements-voice.txt'}
RESERVED={'camera_config.json','update_state.json','feed.json'}

def version(v):
    if not isinstance(v,str) or not VERSION_RE.fullmatch(v): raise ValueError('Versión inválida')
    return tuple(map(int,v.split('.')))

def atomic_json(path,data):
    fd,tmp=tempfile.mkstemp(prefix='.state-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def digest(data): return hashlib.sha256(data).hexdigest()

def verify_artifact(path):
    """Use a separately installed trusted GitHub CLI. Failure never permits installation."""
    cwd=Path.cwd().resolve()
    dirs=[p for p in os.environ.get('PATH','').split(os.pathsep)
          if p and Path(p).is_absolute() and Path(p).resolve()!=cwd]
    gh=shutil.which('gh',path=os.pathsep.join(dirs))
    if not gh: raise ValueError('Verificación no disponible: instalá GitHub CLI oficial y autenticá tu cuenta si es necesario.')
    env=os.environ.copy()
    env.update(GH_HOST='github.com', GH_PROMPT_DISABLED='1', GH_NO_UPDATE_NOTIFIER='1')
    binary=str(Path(gh).resolve())
    try:
        info=subprocess.run([binary,'--version'],env=env,capture_output=True,timeout=10,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:
        raise ValueError('No se pudo verificar la versión de GitHub CLI.') from e
    match=re.match(rb'gh version (\d+)\.(\d+)\.(\d+)(?:\s|$)',info.stdout)
    if info.returncode!=0 or not match or tuple(map(int,match.groups()))<MIN_GH_VERSION:
        raise ValueError('GitHub CLI 2.102.0 o superior es obligatorio.')
    cmd=[binary,'attestation','verify',str(Path(path).resolve()),
         '--repo',TRUSTED_REPO,'--signer-workflow',TRUSTED_WORKFLOW,
         '--source-ref','refs/heads/main','--deny-self-hosted-runners','--hostname','github.com']
    try:
        result=subprocess.run(cmd,env=env,capture_output=True,timeout=90,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:
        raise ValueError('No se pudo completar la verificación criptográfica.') from e
    if result.returncode!=0:
        raise ValueError('Atestación no válida o no disponible. No se instaló la actualización.')

def verify_bytes(data,name):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/name; p.write_bytes(data); verify_artifact(p)

def validate_feed(m):
    v=m['version']; version(v)
    if m.get('product')!='jarvis-vision' or m.get('protocol')!=PROTOCOL: raise ValueError('Canal incompatible')
    expected=f'https://github.com/{TRUSTED_REPO}/releases/download/v{v}/JARVIS_Vision_V{v}.zip'
    if m.get('url')!=expected: raise ValueError('Origen del paquete no autorizado')
    h=m['sha256']
    if not isinstance(h,str) or not SHA_RE.fullmatch(h): raise ValueError('SHA-256 inválido en canal')
    return m

def manifest(raw):
    m=json.loads(raw); version(m['version'])
    if m.get('product')!='jarvis-vision' or m.get('protocol')!=PROTOCOL: raise ValueError('Producto o protocolo incompatible')
    files=m['files']
    if not isinstance(files,dict) or not REQUIRED.issubset(files) or len(files)>100: raise ValueError('Archivos requeridos ausentes')
    folded=set()
    for n,h in files.items():
        if not NAME_RE.fullmatch(n) or n.lower() in RESERVED or n.lower() in folded or not isinstance(h,str) or not SHA_RE.fullmatch(h): raise ValueError('Nombre o hash inválido: '+n)
        folded.add(n.lower())
    return m

@contextmanager
def instance_lock(store):
    store.mkdir(parents=True,exist_ok=True)
    with (store/'manager.lock').open('a+b') as f:
        f.seek(0,2)
        if f.tell()==0: f.write(b'0'); f.flush()
        f.seek(0)
        try:
            if os.name=='nt':
                import msvcrt; msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl; fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as e: raise RuntimeError('Ya hay una instancia administrada de JARVIS abierta. Cerrala primero.') from e
        try: yield
        finally:
            f.seek(0)
            if os.name=='nt': msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(f,fcntl.LOCK_UN)

class Manager:
    def __init__(self,root):
        self.root=Path(root).resolve(); self.store=self.root/'.jarvis'; self.versions=self.store/'versions'; self.versions.mkdir(parents=True,exist_ok=True); self.statefile=self.store/'state.json'; self.feedfile=self.store/'feed.json'
    def state(self):
        if not self.statefile.exists(): return {'active':None,'previous':None}
        s=read_json(self.statefile)
        for k in ('active','previous'):
            if s.get(k) is not None: version(s[k])
        highest=s.get('highest',s.get('active'))
        if highest is not None: version(highest)
        candidates=[v for v in (highest,s.get('active'),s.get('previous')) if v is not None]
        s['highest']=max(candidates,key=version) if candidates else None
        return s
    def verified(self,v):
        version(v); path=self.versions/v; m=manifest((path/'release.json').read_bytes())
        if m['version']!=v: raise ValueError('Versión inconsistente')
        for n,h in m['files'].items():
            p=path/n
            if p.is_symlink() or not p.is_file() or digest(p.read_bytes())!=h: raise ValueError('Archivo alterado: '+n)
        return path
    def install(self,package,expected_version=None,expected_sha=None):
        package=Path(package)
        if package.stat().st_size>MAX_ZIP: raise ValueError('ZIP demasiado grande')
        if expected_sha and digest(package.read_bytes())!=expected_sha: raise ValueError('SHA-256 del ZIP no coincide')
        old=self.state(); stage=None
        try:
            with zipfile.ZipFile(package) as z:
                entries=z.infolist(); names=[i.filename for i in entries]
                if len(names)>150 or len(names)!=len(set(n.casefold() for n in names)): raise ValueError('Entradas duplicadas o excesivas')
                if 'release.json' not in names or z.getinfo('release.json').file_size>MAX_MANIFEST: raise ValueError('Manifiesto ausente o demasiado grande')
                raw=z.read('release.json'); m=manifest(raw); v=m['version']
                if expected_version and v!=expected_version: raise ValueError('Versión distinta a la anunciada')
                if old.get('highest',old['active']) and version(v)<=version(old.get('highest',old['active'])): raise ValueError('No es una versión más reciente; usá restaurar para volver atrás')
                allowed={'release.json','manager.py','INSTALAR_ACTUALIZADOR.py','INSTALAR_ACTUALIZADOR.bat','LEEME.txt','app/'}|{'app/'+n for n in m['files']}
                if not set(names).issubset(allowed): raise ValueError('Entradas no autorizadas en ZIP')
                if sum(i.file_size for i in entries)>MAX_ZIP or any(i.file_size>MAX_FILE for i in entries): raise ValueError('Tamaño descomprimido excesivo')
                stage=Path(tempfile.mkdtemp(prefix='.stage-',dir=self.versions))
                for n,h in m['files'].items():
                    i=z.getinfo('app/'+n)
                    if i.is_dir() or ((i.external_attr>>16)&0o170000)==0o120000: raise ValueError('Entrada no regular')
                    data=z.read(i)
                    if digest(data)!=h: raise ValueError('Hash inválido: '+n)
                    if n.endswith('.py'): compile(data,n,'exec')
                    (stage/n).write_bytes(data)
                (stage/'release.json').write_bytes(raw)
                dest=self.versions/v
                if dest.exists():
                    self.verified(v)
                    if (dest/'release.json').read_bytes()!=raw: raise ValueError('Versión existente con contenido diferente')
                else: os.replace(stage,dest); stage=None
                atomic_json(self.statefile,{'active':v,'previous':old['active'],'highest':v})
                return v
        finally:
            if stage is not None: shutil.rmtree(stage,ignore_errors=True)
    def rollback(self):
        s=self.state(); prior=s['previous']
        if not prior: raise ValueError('Todavía no hay una versión administrada anterior')
        self.verified(prior)
        atomic_json(self.statefile,{'active':prior,'previous':s['active'],'highest':s['highest']}); return prior
    def launch(self,args=()):
        path=self.verified(self.state()['active']); env=os.environ.copy(); env.update(JARVIS_DATA_DIR=str(self.root),JARVIS_MANAGED='1')
        return subprocess.call([sys.executable,str(path/'jarvis_vision.py'),*args],cwd=self.root,env=env)
    def feed(self): return read_json(self.feedfile).get('url','') if self.feedfile.exists() else ''
    def set_feed(self,url):
        if url and url!=TRUSTED_FEED: raise ValueError('Solo se permite el canal oficial de JARVIS.')
        atomic_json(self.feedfile,{'url':url})
    def check(self):
        url=self.feed()
        if not url: return None
        if url!=TRUSTED_FEED: raise ValueError('Canal no autorizado; configurá el canal oficial.')
        raw=fetch(url,MAX_MANIFEST); verify_bytes(raw,'feed.json')
        m=validate_feed(json.loads(raw)); v=m['version']
        s=self.state(); highest=s.get('highest',s.get('active'))
        return m if not highest or version(v)>version(highest) else None
    def download(self,m):
        validate_feed(m)
        data=fetch(m['url'],MAX_ZIP)
        if digest(data)!=m['sha256']: raise ValueError('SHA-256 del ZIP no coincide')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'release.zip'; p.write_bytes(data)
            verify_artifact(p)
            return self.install(p,m['version'],m['sha256'])
    def install_local(self,package):
        # Copy into a private temporary directory before verification, avoiding a swap of the selected file.
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'release.zip'
            with Path(package).open('rb') as f:
                data=f.read(MAX_ZIP+1)
            if len(data)>MAX_ZIP: raise ValueError('ZIP demasiado grande')
            p.write_bytes(data); verify_artifact(p)
            return self.install(p)

def https(url):
    u=urlparse(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password: raise ValueError('El canal requiere URL HTTPS sin credenciales')
    return url
class HTTPSOnly(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        https(newurl); return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url,limit):
    with build_opener(HTTPSOnly()).open(Request(https(url),headers={'User-Agent':'JARVIS-Vision-Updater/1'}),timeout=8) as r:
        https(r.geturl()); data=r.read(limit+1)
        if len(data)>limit: raise ValueError('Descarga demasiado grande')
        return data

def migrate_manager(root,source):
    """Explicit bootstrap after external provenance verification; preserve existing state."""
    root=Path(root).resolve(); store=root/'.jarvis'; target=store/'manager.py'
    if not store.is_dir() or store.is_symlink() or not target.is_file() or target.is_symlink() or not (store/'state.json').is_file():
        raise ValueError('Seleccioná una instalación administrada existente de JARVIS.')
    with instance_lock(store):
        manager=Manager(root); active=manager.state()['active']; manager.verified(active)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'manager.py'
            with Path(source).open('rb') as f: data=f.read(MAX_FILE+1)
            if len(data)>MAX_FILE: raise ValueError('Gestor demasiado grande')
            p.write_bytes(data); verify_artifact(p); compile(data,str(p),'exec')
            old=target.read_bytes()
            if old==data: return False
            backup=store/('manager-backup-'+digest(old)+'.py')
            if backup.exists():
                if backup.is_symlink() or backup.read_bytes()!=old: raise ValueError('Respaldo inconsistente')
            else:
                with backup.open('xb') as f:
                    f.write(old); f.flush(); os.fsync(f.fileno())
            fd,tmp=tempfile.mkstemp(prefix='.manager-',dir=store)
            try:
                with os.fdopen(fd,'wb') as f:
                    f.write(data); f.flush(); os.fsync(f.fileno())
                os.replace(tmp,target)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
            return True

def ui(m, startup=False):
    import tkinter as tk
    from tkinter import ttk,messagebox,filedialog,simpledialog
    root=tk.Tk(); root.title('JARVIS · Actualizaciones'); root.geometry('600x300'); root.resizable(False,False); result={'launch':False}
    status=tk.StringVar(); busy=False
    def refresh():
        s=m.state(); status.set(f"Versión activa: {s['active']}\nVersión anterior: {s['previous'] or 'ninguna administrada'}\nCanal: {'configurado' if m.feed() else 'sin configurar (ZIP local disponible)'}")
    def run(fn):
        nonlocal busy
        if busy:return
        busy=True; root.config(cursor='watch'); root.update_idletasks()
        try: fn(); refresh()
        except Exception as e: messagebox.showerror('Actualizaciones',str(e),parent=root)
        finally: busy=False; root.config(cursor='')
    def install():
        p=filedialog.askopenfilename(parent=root,filetypes=[('Paquete JARVIS','*.zip')]);
        if p and messagebox.askyesno('Instalar','¿Confiás en el origen de este paquete? Solo se actualizará el programa.',parent=root): messagebox.showinfo('Actualizado','Versión instalada: '+m.install_local(p),parent=root)
    def check():
        if not m.feed(): messagebox.showinfo('Canal','Todavía no hay un canal publicado. Configuralo o instalá un ZIP.',parent=root); return
        new=m.check()
        if new is None: messagebox.showinfo('Canal','No hay una versión más reciente.',parent=root); return
        if messagebox.askyesno('Actualización',f"Disponible V{new['version']}. ¿Descargar e instalar desde el canal configurado?",parent=root): messagebox.showinfo('Actualizado','Versión instalada: '+m.download(new),parent=root)
    def configure():
        url=simpledialog.askstring('Canal HTTPS','Canal oficial de JARVIS. Vacío para desactivar.',initialvalue=m.feed() or TRUSTED_FEED,parent=root)
        if url is not None: m.set_feed(url.strip())
    def restore():
        if messagebox.askyesno('Restaurar','¿Volver a la versión anterior? Los datos compartidos no se revierten.',parent=root): messagebox.showinfo('Restaurado','Versión activa: '+m.rollback(),parent=root)
    def launch():
        if not busy: result['launch']=True; root.destroy()
    ttk.Label(root,text='JARVIS Vision · Gestor de versiones',font=('Segoe UI',16,'bold')).pack(pady=12); ttk.Label(root,textvariable=status,justify='left').pack(pady=8)
    row=ttk.Frame(root); row.pack(pady=6)
    for label,fn in [('Instalar ZIP',install),('Buscar actualización',check),('Configurar canal',configure),('Restaurar',restore)]: ttk.Button(row,text=label,command=lambda f=fn:run(f)).pack(side='left',padx=3)
    ttk.Button(root,text='Abrir JARVIS',command=launch).pack(pady=12)
    root.protocol('WM_DELETE_WINDOW',lambda:root.destroy() if not busy else None); refresh()
    if startup:
        def auto():
            nonlocal busy
            busy=True; root.config(cursor='watch'); root.update_idletasks()
            try:
                new=m.check()
                if new and messagebox.askyesno('Actualización disponible',f"V{new['version']}: ¿descargar e instalar?",parent=root): m.download(new)
            except Exception as e: messagebox.showwarning('Canal no disponible',str(e),parent=root)
            finally: busy=False; root.config(cursor='')
            launch()
        root.after(50,auto)
    root.mainloop(); return result['launch']

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--migrate':
        try:
            changed=migrate_manager(sys.argv[2],__file__)
            print('Gestor actualizado. Respaldo conservado.' if changed else 'El gestor ya está actualizado.')
            return 0
        except Exception as e:
            print('Migración no completada:',e,file=sys.stderr); return 1
    import tkinter as tk
    from tkinter import messagebox
    m=Manager(Path(__file__).resolve().parent.parent)
    args=sys.argv[1:]; manage='--manage' in args; args=[x for x in args if x!='--manage']
    try:
      with instance_lock(m.store):
        if manage or m.feed():
            if not ui(m,startup=not manage): return 0
        while True:
            rc=m.launch(args)
            if rc==APP_EXIT:
                if ui(m): continue
                return 0
            if rc!=0:
                root=tk.Tk(); root.withdraw(); messagebox.showwarning('JARVIS',f'La aplicación terminó con código {rc}. Podés abrir el gestor con ACTUALIZACIONES.bat para restaurar.',parent=root); root.destroy()
            return rc
    except Exception as e:
        root=tk.Tk(); root.withdraw(); messagebox.showerror('JARVIS',str(e),parent=root); root.destroy(); return 1
if __name__=='__main__': raise SystemExit(main())
